"""Long-only fractional-share teaching ledger, with explicit cash distributions.

Execution: first observed open, then first observed open of each new month.
Distributions: prior-close shares, credited immediately on ex-date (simplification).
Splits/capital gains are rejected rather than silently mishandled. No financing.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    daily: pd.DataFrame
    trades: pd.DataFrame
    distributions: pd.DataFrame
    initial_cash: float
    cost_bps: float

    def metrics(self):
        nav = self.daily['nav']
        # Include initial capital so initial execution costs are not hidden.
        values = np.r_[self.initial_cash, nav.to_numpy()]
        returns = pd.Series(values[1:] / values[:-1] - 1)
        years = (nav.index[-1] - nav.index[0]).days / 365.25
        dd = values / np.maximum.accumulate(values) - 1
        return pd.Series({
            'final_nav': nav.iloc[-1],
            'total_return': nav.iloc[-1] / self.initial_cash - 1,
            'cagr': (nav.iloc[-1] / self.initial_cash) ** (1 / years) - 1,
            'annual_volatility': returns.std(ddof=1) * np.sqrt(252),
            'max_drawdown': dd.min(),
            'fees_paid': self.trades['fee'].sum(),
            'gross_traded': self.trades['notional'].abs().sum(),
            'trade_days': self.trades['date'].nunique(),
            'distributions_received': self.distributions['amount'].sum(),
            'ending_cash': self.daily['cash'].iloc[-1],
        })


def simulate(frames, weights, initial_cash=100_000., cost_bps=5., monthly=True,
             target_schedule=None, rebalance_threshold=None):
    """Fixed target policy; monthly=False holds initial shares, distributions in cash.

    Rates are per side, proportional to gross traded notional, combining assumed
    fees and execution friction. Actual fills at Open are an idealized model.
    Weights may sum to [0, 1]; all-zero weights explicitly target all cash.
    The remainder targets zero-interest cash.
    Optional schedule: execution dates as index, asset weight columns and
    decision_date strictly before execution. Schedule overrides monthly timing.
    Optional threshold: at scheduled opportunities, trade only if the largest
    asset-or-cash weight gap at the prior close exceeds the threshold. Initial
    investment is mandatory. Threshold requires prior-session decisions.
    """
    symbols = list(weights)
    if rebalance_threshold is not None:
        if (target_schedule is None or not np.isfinite(rebalance_threshold)
                or not 0 <= rebalance_threshold <= 1):
            raise ValueError('Threshold needs a schedule and a value in [0, 1]')
    target = np.array([weights[s] for s in symbols], dtype=float)
    if (not symbols or not np.isfinite(target).all() or (target < 0).any()
            or target.sum() > 1 + 1e-12):
        raise ValueError('Weights must be finite, nonnegative and sum to [0, 1]')
    if not np.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError('Initial capital must be positive')
    if not np.isfinite(cost_bps) or not 0 <= cost_bps < 10_000:
        raise ValueError('Cost must be in [0, 10000) bps')
    dates = frames[symbols[0]].index
    if (len(dates) < 2 or not dates.is_unique or not dates.is_monotonic_increasing
            or (dates[-1] - dates[0]).days <= 0):
        raise ValueError('Need unique, increasing daily history')
    for s in symbols:
        f = frames[s]
        if not f.index.equals(dates):
            raise ValueError('Calendars must match exactly; missing dates need review')
        vals = f[['Open', 'Close', 'Dividends']].to_numpy()
        if (not np.isfinite(vals).all() or (vals[:, :2] <= 0).any()
                or (vals[:, 2] < 0).any()):
            raise ValueError('Invalid prices/distributions')
        for column in ('Stock Splits', 'Capital Gains'):
            if column in f and (f[column].fillna(0) != 0).any():
                raise ValueError(f'{s}: {column} require additional accounting support')

    if target_schedule is not None:
        schedule = target_schedule.copy()
        if (schedule.empty or not schedule.index.is_unique
                or not schedule.index.is_monotonic_increasing
                or not schedule.index.isin(dates).all() or schedule.index[0] != dates[0]):
            raise ValueError('Schedule must start at first price date and use unique ordered price dates')
        if not set(symbols + ['decision_date']).issubset(schedule.columns):
            raise ValueError('Schedule needs every asset and decision_date')
        vals = schedule[symbols].to_numpy(dtype=float)
        if (not np.isfinite(vals).all() or (vals < 0).any()
                or (vals.sum(axis=1) > 1 + 1e-12).any()):
            raise ValueError('Invalid scheduled weights')
        decisions = pd.to_datetime(schedule['decision_date'])
        if decisions.isna().any() or (decisions.to_numpy() >= schedule.index.to_numpy()).any():
            raise ValueError('Decisions must be dated strictly before execution')
        schedule['decision_date'] = decisions
        if rebalance_threshold is not None:
            for date in schedule.index[1:]:
                if schedule.loc[date, 'decision_date'] != dates[dates.get_loc(date)-1]:
                    raise ValueError('Threshold decisions must use the prior session close')

    opens = np.column_stack([frames[s]['Open'] for s in symbols])
    closes = np.column_stack([frames[s]['Close'] for s in symbols])
    dividends = np.column_stack([frames[s]['Dividends'] for s in symbols])
    shares = np.zeros(len(symbols))
    cash = float(initial_cash)
    rate = cost_bps / 10_000
    trade_rows, distribution_rows, daily_rows = [], [], []
    accumulated_fees = accumulated_distributions = 0.
    for i, date in enumerate(dates):
        # Save decision-time holdings before today's distributions and opening gap.
        prior_cash = cash
        # Entitlement belongs to shares held before this day's opening trades.
        distribution = shares * dividends[i]
        for j, s in enumerate(symbols):
            if distribution[j] != 0:
                distribution_rows.append(dict(date=date, asset=s, eligible_shares=shares[j],
                                              per_share=dividends[i, j], amount=distribution[j]))
        cash += distribution.sum()
        accumulated_distributions += distribution.sum()
        opening_values = shares * opens[i]
        before = cash + opening_values.sum()
        pre_weights = opening_values / before
        rebalance = i == 0 or (monthly and date.to_period('M') != dates[i-1].to_period('M'))
        decision_date = dates[i-1] if i else pd.NaT
        if target_schedule is not None:
            rebalance = date in schedule.index
            if rebalance:
                target = schedule.loc[date, symbols].to_numpy(dtype=float)
                decision_date = schedule.loc[date, 'decision_date']
        opportunity = rebalance
        decision_gap = np.nan
        if rebalance and i > 0 and rebalance_threshold is not None:
            prior_values = shares * closes[i-1]
            prior_nav = prior_cash + prior_values.sum()
            actual = np.r_[prior_values / prior_nav, prior_cash / prior_nav]
            desired = np.r_[target, 1-target.sum()]
            decision_gap = float(np.max(np.abs(actual-desired)))
            rebalance = decision_gap > rebalance_threshold
        day_fee = 0.
        if rebalance:
            # Solve V_after + rate * sum(abs(target * V_after - current)) = V_before.
            lo, hi = 0., before
            for _ in range(70):
                mid = (lo + hi) / 2
                if mid + rate * np.abs(target * mid - opening_values).sum() > before:
                    hi = mid
                else:
                    lo = mid
            after = (lo + hi) / 2
            delta = (target * after - opening_values) / opens[i]
            notionals = delta * opens[i]
            fees = np.abs(notionals) * rate
            day_fee = fees.sum()
            # Batch netting models sales funding buys; broker sequencing is future work.
            cash -= notionals.sum() + day_fee
            shares += delta
            for j, s in enumerate(symbols):
                if abs(delta[j]) > 1e-10:
                    trade_rows.append(dict(date=date,
                        decision_date=decision_date,
                        asset=s, reason='initial' if i == 0 else ('scheduled' if target_schedule is not None else 'monthly'),
                        shares=delta[j], price=opens[i, j], notional=notionals[j], fee=fees[j]))
            accumulated_fees += day_fee
            if not np.isclose(cash + (shares * opens[i]).sum(), before - day_fee, atol=1e-7):
                raise AssertionError('Trade accounting failed')
        if cash < -1e-7 or (shares < -1e-9).any():
            raise AssertionError('Long-only / cash constraint failed')
        cash = max(cash, 0.)  # Remove floating point dust only.
        values = shares * closes[i]
        nav = cash + values.sum()
        row = dict(date=date, nav=nav, cash=cash, distribution=distribution.sum(),
                   fees=day_fee, cumulative_fees=accumulated_fees,
                   cumulative_distributions=accumulated_distributions, rebalance=rebalance,
                   rebalance_opportunity=opportunity, decision_weight_gap=decision_gap)
        for j, s in enumerate(symbols):
            row.update({f'{s}_shares': shares[j], f'{s}_value': values[j],
                        f'{s}_weight': values[j]/nav, f'{s}_pretrade_weight': pre_weights[j]})
        daily_rows.append(row)
    return BacktestResult(
        pd.DataFrame(daily_rows).set_index('date'),
        pd.DataFrame(trade_rows, columns=['date','decision_date','asset','reason','shares','price','notional','fee']),
        pd.DataFrame(distribution_rows, columns=['date','asset','eligible_shares','per_share','amount']),
        initial_cash, cost_bps)


def reconcile(result):
    """Independently reconstruct daily cash and shares from event records."""
    daily = result.daily
    dates = daily.index
    t = result.trades
    d = result.distributions
    outgoing = (t['notional'] + t['fee']).groupby(t['date']).sum().reindex(dates, fill_value=0)
    incoming = d.groupby('date')['amount'].sum().reindex(dates, fill_value=0)
    reconstructed_cash = result.initial_cash + (incoming - outgoing).cumsum()
    errors = {'cash_error': float((daily['cash']-reconstructed_cash).abs().max())}
    for col in daily.filter(regex='_shares$'):
        s = col.removesuffix('_shares')
        holdings = t.loc[t.asset == s].groupby('date')['shares'].sum().reindex(dates, fill_value=0).cumsum()
        errors[f'{s}_shares_error'] = float((daily[col] - holdings).abs().max())
    errors['nav_error'] = float((daily['nav'] - daily['cash'] - daily.filter(regex='_value$').sum(axis=1)).abs().max())
    if max(errors.values()) > 1e-6:
        raise AssertionError(errors)
    return errors
