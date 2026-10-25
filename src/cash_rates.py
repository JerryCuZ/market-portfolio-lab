"""Immutable FRED DFF snapshots and explicitly lagged cash-rate scenarios."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import io
import json
from urllib.request import urlopen
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=DFF'


def parse_rates(raw):
    f = pd.read_csv(io.BytesIO(raw))
    if list(f.columns) != ['observation_date', 'DFF']:
        raise ValueError('Unexpected FRED DFF schema')
    dates = pd.to_datetime(f.observation_date, errors='raise')
    rates = pd.Series(pd.to_numeric(f.DFF, errors='raise').to_numpy()/100,
                      index=pd.DatetimeIndex(dates), name='annual_rate')
    if (rates.empty or not rates.index.is_unique or not rates.index.is_monotonic_increasing
            or not np.isfinite(rates).all() or ((rates < 0) | (rates > 1)).any()):
        raise ValueError('Need ordered, complete, finite nonnegative DFF rates')
    return rates


def save_rates(raw, source):
    rates = parse_rates(raw)
    sha = hashlib.sha256(raw).hexdigest()
    snapshot = 'dff_'+sha[:16]
    folder = ROOT/'data/raw/cash_rates'/snapshot
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=False)
        (folder/'DFF.csv').write_bytes(raw)
        manifest = dict(snapshot=snapshot, source=source, series='DFF', units='percent in source; decimals after parsing',
            retrieved_at_utc=datetime.now(timezone.utc).isoformat(), sha256=sha,
            first_date=str(rates.index[0].date()), last_date=str(rates.index[-1].date()),
            rows=len(rates), vintage='retrieval-time revised history, not point-in-time archive')
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    else:
        if hashlib.sha256((folder/'DFF.csv').read_bytes()).hexdigest() != sha:
            raise ValueError('Existing snapshot checksum mismatch')
    (folder.parent/'latest.json').write_text(json.dumps({'snapshot':snapshot}),encoding='utf-8')
    return snapshot


def load_rates(snapshot='latest'):
    root=ROOT/'data/raw/cash_rates'
    if snapshot=='latest':
        if not (root/'latest.json').exists():
            raise FileNotFoundError('Download rates first: python src/cash_rates.py --start 2010-01-01 --end 2026-10-06')
        snapshot=json.loads((root/'latest.json').read_text())['snapshot']
    if Path(snapshot).name != snapshot:
        raise ValueError('Snapshot must be a directory ID')
    folder=root/snapshot
    if not (folder/'manifest.json').exists():
        raise FileNotFoundError('Missing cash-rate snapshot; download rates and set MARKET_LAB_RATE_SNAPSHOT=latest')
    manifest=json.loads((folder/'manifest.json').read_text())
    raw=(folder/'DFF.csv').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['sha256']:
        raise ValueError('Rate snapshot checksum mismatch')
    return parse_rates(raw),manifest


def rate_schedule(rates, dates, spread_bps=0., lag_days=7, max_extra_age=3):
    """Hold a lagged rate over each account close-to-next-session interval.

    Select newest observation <= interval start minus lag_days. This artificial
    lag is a teaching convention, not observed publication metadata. Rates are
    simple annual decimals. No backward fill or stale unbounded forward fill.
    """
    dates=pd.DatetimeIndex(dates)
    if (len(dates)<2 or not dates.is_unique or not dates.is_monotonic_increasing
            or rates.empty or not rates.index.is_unique or not rates.index.is_monotonic_increasing
            or not np.isfinite(rates).all() or ((rates<0)|(rates>1)).any()
            or not isinstance(lag_days,int) or lag_days<1
            or not np.isfinite(spread_bps) or spread_bps<0 or max_extra_age<0):
        raise ValueError('Invalid rates, calendar, lag or spread')
    rows=[]
    for i,date in enumerate(dates):
        start=dates[i-1] if i else date
        cutoff=start-pd.Timedelta(days=lag_days)
        pos=rates.index.searchsorted(cutoff,side='right')-1
        if pos<0 or (cutoff-rates.index[pos]).days>max_extra_age:
            raise ValueError('Missing or stale rate at interval start; never backfill from future')
        observation=rates.index[pos]
        rows.append(dict(date=date,period_start=start,observation_date=observation,
            assumed_available_date=observation+pd.Timedelta(days=lag_days),
            reference_rate=float(rates.iloc[pos]),
            annual_rate=max(float(rates.iloc[pos])-spread_bps/10000,0.),
            days=(date-start).days))
    return pd.DataFrame(rows).set_index('date')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',default='2010-01-01');p.add_argument('--end',default='2026-10-06')
    p.add_argument('--input',help='Previously downloaded official DFF CSV')
    a=p.parse_args();url=SOURCE+'&cosd='+a.start+'&coed='+a.end
    raw=Path(a.input).read_bytes() if a.input else urlopen(url,timeout=60).read()
    rates=parse_rates(raw)
    if rates.index[0]>pd.Timestamp(a.start) or rates.index[-1]<pd.Timestamp(a.end):
        raise ValueError('Requested coverage incomplete')
    print(save_rates(raw,url))
