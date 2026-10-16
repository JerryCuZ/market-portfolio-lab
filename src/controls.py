"""Explicit exposure controls for allocation experiments."""
import numpy as np
import pandas as pd


def scale_schedule(base, assets, exposure):
    """Scale fully invested base weights by scalar or exactly aligned series.

    Leaves the remainder in cash. A dated series must already be available at
    each decision; alignment checks cannot establish information provenance.
    This helper does not infer exposure from future observations.
    """
    assets = list(assets)
    if (not assets or len(set(assets)) != len(assets) or base.empty
            or not base.index.is_unique or not base.index.is_monotonic_increasing
            or not set(assets+['decision_date']).issubset(base.columns)):
        raise ValueError('Need unique assets and an ordered dated base schedule')
    w = base[assets].to_numpy(dtype=float)
    decisions = pd.to_datetime(base.decision_date)
    if (not np.isfinite(w).all() or (w < 0).any()
            or not np.allclose(w.sum(axis=1), 1, rtol=0, atol=1e-12)
            or decisions.isna().any()
            or (decisions.to_numpy() >= base.index.to_numpy()).any()):
        raise ValueError('Base must be fully invested, long-only and decided before execution')
    if np.isscalar(exposure):
        e = pd.Series(float(exposure), index=base.index)
    elif isinstance(exposure, pd.Series) and exposure.index.equals(base.index):
        e = exposure.astype(float)
    else:
        raise ValueError('Exposure must be a scalar or exactly aligned series')
    if not np.isfinite(e).all() or ((e < -1e-12) | (e > 1+1e-12)).any():
        raise ValueError('Exposure must lie in [0, 1]')
    e = e.clip(0, 1)  # Remove summation roundoff only, not economic leverage.
    result = base.copy()
    result[assets] = result[assets].mul(e, axis=0)
    return result.drop(columns=['iterations', 'max_risk_share_error'], errors='ignore')
