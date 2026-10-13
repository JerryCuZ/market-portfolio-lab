"""Small historical risk estimators; predictions are not future risk guarantees."""
import numpy as np
import pandas as pd


def cap_weights(weights, cap=0.5):
    """Cap-and-proportionally-redistribute positive fully invested targets.

    This is an explicit allocation overlay, NOT a constrained ERC optimizer.
    The cap applies to targets; market drift can exceed it between trades.
    """
    w = pd.Series(weights, dtype=float)
    if (w.empty or not w.index.is_unique or not np.isfinite(w).all()
            or (w <= 0).any() or not np.isclose(w.sum(), 1, atol=1e-12, rtol=0)
            or not np.isfinite(cap) or not 0 < cap <= 1 or len(w)*cap < 1-1e-12):
        raise ValueError('Need positive normalized weights and a feasible cap')
    result = pd.Series(0., index=w.index)
    free = pd.Series(True, index=w.index)
    while free.any():
        allocation = w[free] / w[free].sum() * (1-result.sum())
        hit = allocation > cap
        if not hit.any():
            result.loc[allocation.index] = allocation
            break
        locked = allocation.index[hit]
        result.loc[locked] = cap
        free.loc[locked] = False
    return result


def risk_contributions(weights, covariance):
    """Euler contributions to volatility; contributions can be negative.

    Covariance is annualized, indexed and columned in matching asset order.
    Shares sum to one; absolute volatility contributions sum to portfolio vol.
    """
    if not covariance.index.equals(covariance.columns):
        raise ValueError('Covariance asset labels must align')
    w = pd.Series(weights, dtype=float).reindex(covariance.index)
    c = covariance.to_numpy(dtype=float)
    if not np.isfinite(w).all() or not np.isfinite(c).all() or not np.allclose(c,c.T):
        raise ValueError('Invalid weights or covariance')
    if np.linalg.eigvalsh(c).min() < -1e-10:
        raise ValueError('Covariance must be positive semidefinite')
    marginal_variance = c @ w.to_numpy()
    variance = float(w.to_numpy() @ marginal_variance)
    if variance <= 0:
        raise ValueError('Positive portfolio variance required')
    vol = np.sqrt(variance)
    result = pd.DataFrame({'capital_weight':w, 'asset_volatility':np.sqrt(np.diag(c)),
        'volatility_contribution':w.to_numpy()*marginal_variance/vol,
        'risk_share':w.to_numpy()*marginal_variance/variance})
    return result, vol


def inverse_vol_schedule(prices, lookback=126):
    """Monthly inverse-vol targets from prior-close adjusted returns only.

    Uses exactly lookback daily returns, never execution-date returns.
    Returns target schedule and long-form risk audit at each decision.
    """
    if (not isinstance(lookback, int) or lookback < 2 or not prices.index.is_unique
            or not prices.index.is_monotonic_increasing or prices.isna().any().any()
            or not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any().any()):
        raise ValueError('Need ordered complete positive prices and lookback >= 2')
    returns = prices.pct_change(fill_method=None)
    rows, audit = [], []
    for i in range(lookback+1, len(prices)):
        date = prices.index[i]
        if date.to_period('M') == prices.index[i-1].to_period('M'):
            continue
        window = returns.iloc[i-lookback:i]
        covariance = window.cov() * 252
        vol = np.sqrt(np.diag(covariance))
        if (vol <= 1e-12).any():
            raise ValueError('Zero estimated volatility needs explicit policy')
        inv = 1/vol
        w = pd.Series(inv/inv.sum(), index=prices.columns)
        row = dict(execution_date=date, decision_date=prices.index[i-1],
                   window_start=window.index[0], observations=len(window), **w.to_dict())
        rows.append(row)
        for name, weights in [('inverse_vol',w),
                              ('equal_3',pd.Series(1/len(w),index=w.index)),
                              ('60_40',pd.Series({'SPY':.6,'IEF':.4}).reindex(w.index,fill_value=0))]:
            if name == '60_40' and not {'SPY','IEF'}.issubset(w.index):
                continue
            rc, portfolio_vol = risk_contributions(weights, covariance)
            for asset, values in rc.iterrows():
                audit.append(dict(execution_date=date,decision_date=prices.index[i-1],
                    policy=name,asset=asset,portfolio_volatility=portfolio_vol,**values.to_dict()))
    if not rows:
        raise ValueError('Not enough history for a monthly decision after warm-up')
    return pd.DataFrame(rows).set_index('execution_date'), pd.DataFrame(audit)


def equal_risk_weights(covariance, tolerance=1e-9, max_iterations=10000):
    """Long-only ERC via cyclic coordinate descent on .5*x'C*x-sum(b*log(x)).

    Positive-definite covariance required; no silent covariance repair or
    fallback. Normalizing x gives fully invested weights. Verify risk shares
    rather than trusting an optimizer status flag.
    """
    if (not covariance.index.equals(covariance.columns) or covariance.empty
            or not covariance.index.is_unique):
        raise ValueError('Need aligned unique covariance labels')
    c = covariance.to_numpy(dtype=float)
    if not np.isfinite(c).all() or not np.allclose(c,c.T,rtol=1e-10,atol=1e-12):
        raise ValueError('Need finite symmetric covariance')
    if not 0 < tolerance < 1 or max_iterations < 1:
        raise ValueError('Invalid solver settings')
    scale = np.max(np.diag(c))
    if scale <= 0:
        raise ValueError('Positive covariance required')
    c = c / scale
    if np.linalg.eigvalsh(c).min() <= 1e-12:
        raise ValueError('Singular or ill-conditioned covariance needs explicit policy')
    n = len(c)
    budget = np.full(n,1/n)
    x = 1/np.sqrt(np.diag(c))
    for iteration in range(1,max_iterations+1):
        for i in range(n):
            cross = c[i] @ x - c[i,i]*x[i]
            root = np.sqrt(cross*cross+4*c[i,i]*budget[i])
            x[i] = (2*budget[i]/(root+cross) if cross >= 0
                    else (root-cross)/(2*c[i,i]))
        w = x/x.sum()
        contribution = w*(c@w)
        error = np.max(np.abs(contribution/contribution.sum()-budget))
        if error < tolerance:
            weights = pd.Series(w,index=covariance.index)
            rc,_ = risk_contributions(weights,covariance)
            if not np.allclose(rc.risk_share,budget,atol=tolerance,rtol=0):
                raise RuntimeError('Independent ERC check failed')
            return weights, {'iterations':iteration,'max_risk_share_error':float(error)}
    raise RuntimeError('ERC solver did not converge; no target produced')


def equal_risk_schedule(prices, lookback=126):
    """Same calendar and data windows as inverse-vol; only allocation changes."""
    schedule,_ = inverse_vol_schedule(prices,lookback)
    returns = prices.pct_change(fill_method=None)
    rows=[]
    for date in schedule.index:
        i=prices.index.get_loc(date)
        cov=returns.iloc[i-lookback:i].cov()*252
        weights,diagnostics=equal_risk_weights(cov)
        schedule.loc[date,prices.columns]=weights
        for key,value in diagnostics.items(): schedule.loc[date,key]=value
        rc,vol=risk_contributions(weights,cov)
        for asset,values in rc.iterrows():
            rows.append(dict(execution_date=date,decision_date=prices.index[i-1],
                             policy='equal_risk',asset=asset,portfolio_volatility=vol,
                             **values.to_dict()))
    return schedule,pd.DataFrame(rows)
