"""Download immutable Yahoo Finance snapshots; analyze provider-adjusted closes."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
TICKERS = ('SPY', 'IEF', 'GLD')


def download(start='2010-01-01', end=None):
    # Exclude the current NY date even after close: deliberately use completed prior days.
    end = end or datetime.now(ZoneInfo('America/New_York')).date().isoformat()
    now = datetime.now(ZoneInfo('UTC'))
    frames = {}
    yf.set_tz_cache_location(str(ROOT / '.cache/yfinance'))
    yf.config.debug.hide_exceptions = False
    for symbol in TICKERS:
        frame = yf.Ticker(symbol).history(
            start=start, end=end, interval='1d', auto_adjust=False,
            back_adjust=False, actions=True, repair=False,
        )
        if frame.empty:
            raise ValueError(f'{symbol}: provider returned no data')
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        frame.index.name = 'Date'
        if not frame.index.is_unique or not frame.index.is_monotonic_increasing:
            raise ValueError(f'{symbol}: duplicate or unordered dates')
        required = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        if frame[required].isna().any().any():
            raise ValueError(f'{symbol}: missing required values; inspect before continuing')
        if not np.isfinite(frame[required].to_numpy()).all():
            raise ValueError(f'{symbol}: nonfinite values')
        if (frame[['Open','High','Low','Close','Adj Close']] <= 0).any().any():
            raise ValueError(f'{symbol}: nonpositive price')
        if (frame['Volume'] < 0).any():
            raise ValueError(f'{symbol}: negative volume')
        if ((frame['High'] < frame[['Open','Close','Low']].max(axis=1)) |
            (frame['Low'] > frame[['Open','Close','High']].min(axis=1))).any():
            raise ValueError(f'{symbol}: inconsistent OHLC')
        if frame.index.min() < pd.Timestamp(start) or frame.index.max() >= pd.Timestamp(end):
            raise ValueError(f'{symbol}: response outside requested date range')
        frames[symbol] = frame
    snapshot = now.strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'data/raw' / snapshot
    folder.mkdir(parents=True, exist_ok=False)
    checksums = {}
    for symbol, frame in frames.items():
        path = folder / f'{symbol}.csv'
        frame.to_csv(path, float_format='%.12g')
        checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = dict(
        snapshot=snapshot, source='Yahoo Finance via yfinance',
        yfinance_version=yf.__version__, retrieved_at_utc=now.isoformat(),
        start_inclusive=start, end_exclusive=end, tickers=list(TICKERS),
        auto_adjust=False, back_adjust=False, repair=False, actions=True,
        return_basis='Yahoo Adj Close; dividend/split adjusted approximation, not execution prices',
        sha256=checksums,
    )
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (ROOT/'data/raw/latest.json').write_text(json.dumps({'snapshot':snapshot}), encoding='utf-8')
    print(json.dumps(manifest, indent=2))
    for symbol, frame in frames.items():
        print(symbol, len(frame), frame.index.min().date(), frame.index.max().date())
    return snapshot


def load_snapshot(snapshot=None):
    if snapshot is None:
        if not (ROOT/'data/raw/latest.json').exists():
            raise FileNotFoundError('No local snapshot. Run python src/market_data.py first; see docs/reproducibility.md')
        snapshot = json.loads((ROOT/'data/raw/latest.json').read_text())['snapshot']
    folder = ROOT/'data/raw'/snapshot
    if not (folder/'manifest.json').exists():
        raise FileNotFoundError(f'Snapshot {snapshot} is not available locally. Download data, then run python scripts/run_lessons.py --snapshot latest')
    manifest = json.loads((folder/'manifest.json').read_text())
    frames = {}
    for symbol in manifest['tickers']:
        p = folder/f'{symbol}.csv'
        if hashlib.sha256(p.read_bytes()).hexdigest() != manifest['sha256'][p.name]:
            raise ValueError(f'Snapshot checksum mismatch: {symbol}')
        frames[symbol] = pd.read_csv(p, index_col='Date', parse_dates=True)
    return frames, manifest


def analyze(frames):
    panel = pd.concat({k:v['Adj Close'] for k,v in frames.items()}, axis=1).sort_index()
    panel.columns.name = 'Asset'
    # No forward filling. Notebook shows any dates omitted from joint comparison.
    prices = panel.dropna(how='any')
    if len(prices) < 3:
        raise ValueError('Insufficient common history')
    returns = prices.pct_change(fill_method=None).iloc[1:]
    nav = prices / prices.iloc[0]
    drawdown = nav/nav.cummax()-1
    years = (prices.index[-1]-prices.index[0]).days/365.25
    stats = pd.DataFrame({
        'Total return':nav.iloc[-1]-1,
        'CAGR':nav.iloc[-1]**(1/years)-1,
        'Annual volatility':returns.std(ddof=1)*np.sqrt(252),
        'Max drawdown':drawdown.min(),
    })
    return panel, prices, returns, nav, drawdown, stats


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', default='2010-01-01')
    parser.add_argument('--end', help='Exclusive cutoff; defaults to current New York date')
    args = parser.parse_args()
    download(args.start, args.end)
