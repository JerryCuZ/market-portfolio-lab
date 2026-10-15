"""Auditable signal overlays on dated target schedules; no return forecasts."""
import numpy as np
import pandas as pd


def trend_filter_schedule(prices, base_schedule, lookback=200):
    """Keep base weight only if prior adjusted close > its trailing SMA.

    SMA includes the decision close and exactly lookback price observations.
    Equality is off. Removed weights become cash, with no renormalization.
    Execution calendar comes from base_schedule; every decision must be the
    prior observed price session. Input prices may be retrospectively revised.
    """
    if (not isinstance(lookback, int) or lookback < 2 or prices.empty
            or not prices.index.is_unique or not prices.columns.is_unique
            or not prices.index.is_monotonic_increasing
            or not np.isfinite(prices.to_numpy(dtype=float)).all()
            or (prices <= 0).any().any()):
        raise ValueError('Need ordered, unique, finite positive prices and lookback >= 2')
    assets = list(prices.columns)
    s = base_schedule.copy()
    if (s.empty or not s.index.is_unique or not s.index.is_monotonic_increasing
            or not s.index.isin(prices.index).all()
            or not set(assets+['decision_date']).issubset(s.columns)):
        raise ValueError('Need an aligned, ordered target schedule with decision dates')
    weights = s[assets].to_numpy(dtype=float)
    if (not np.isfinite(weights).all() or (weights < 0).any()
            or (weights.sum(axis=1) > 1+1e-12).any()):
        raise ValueError('Base weights must be long-only with no leverage')
    audit = []
    for date in s.index:
        i = prices.index.get_loc(date)
        if i < lookback:
            raise ValueError('Insufficient prior price observations for trend window')
        decision = pd.Timestamp(s.loc[date, 'decision_date'])
        if decision != prices.index[i-1]:
            raise ValueError('Signal decision must be the prior observed session')
        window = prices.iloc[i-lookback:i]
        close, sma = window.iloc[-1], window.mean()
        enabled = close > sma
        original = s.loc[date, assets].astype(float)
        target = original * enabled.astype(float)
        s.loc[date, assets] = target
        for asset in assets:
            audit.append(dict(execution_date=date, decision_date=decision, asset=asset,
                window_start=window.index[0], observations=lookback,
                adjusted_close=float(close[asset]), sma=float(sma[asset]),
                signal=int(enabled[asset]), base_weight=float(original[asset]),
                target_weight=float(target[asset]),
                cash_target=float(1-target.sum())))
    # ERC convergence diagnostics do not describe the filtered portfolio.
    s = s.drop(columns=['iterations', 'max_risk_share_error'], errors='ignore')
    return s, pd.DataFrame(audit)
