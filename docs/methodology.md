# Methodology and limitations

## Data

Yahoo Finance via yfinance; SPY, IEF and GLD. The teaching snapshot is `20261007T234808781424Z`, downloaded 2026-10-07 UTC, covering 2010-01-04 through 2026-10-06 (4,215 prices per asset). Downloaded CSV files are checksummed. Raw data is not published; selected derived figures, metrics and notebook outputs document the experiments.

Risk estimation uses provider-adjusted close-to-close returns. The cash/share ledger uses Open/Close and separate distribution events. Do not add distributions to adjusted-price returns again. Data may be revised after the historical observation date; this is not a point-in-time database. Internal checks are not an independent data-source or official exchange-calendar validation.

## Portfolio accounting

- Initial capital USD 100,000; fractional shares; long-only; no leverage or external flows.
- Initial purchase at first simulated open. Monthly targets execute at the first observed open of a new month.
- Dynamic targets use only prior-close observations. Current opening prices determine quantities, an idealized sizing/fill assumption rather than an executable opening-auction algorithm.
- Cost: 5 bps of absolute traded notional on each side, inclusive modeled friction; not a broker quote. Holdings are sized after accounting for these costs.
- Distributions belong to prior-close holders and are immediately credited on the ex-date. Actual payment dates and settlement are not modeled.
- Cash earns zero interest. No personal taxes, borrowing, order queue, market impact or settlement delays.
- Splits/capital-gain distributions are rejected rather than silently mishandled.
- Reconciliation independently rebuilds cash and share balances from transaction/distribution records.

## Comparisons

Lesson 02 starts on 2010-01-04. Its hold portfolios leave distributions in cash; monthly portfolios reinvest them during rebalancing. This comparison does not isolate rebalancing alone.

Lessons 03–04 start on 2010-08-02, after sufficient history and at a monthly execution boundary. All portfolios share a common start, end and accounting convention. Risk estimators use 126 daily returns, sample covariance (ddof=1), annualized by 252. Window length was fixed for instruction rather than optimized for return.

Inverse volatility sets weights proportional to 1 / asset volatility. ERC solves positive risk-budget weights using the full covariance matrix. The cyclic coordinate solver requires a positive-definite, sufficiently conditioned covariance, fails on nonconvergence, and verifies risk shares to absolute tolerance 1e-9. No position caps or portfolio volatility target are imposed.

## Metrics and interpretation

CAGR uses the calendar span; volatility is daily account return standard deviation times sqrt(252). Initial capital enters the return/drawdown baseline so initial fees are not hidden. The first day's account return is open-to-close; later returns are close-to-close. Daily closing values cannot reveal intraday drawdowns.

Risk contribution is an Euler decomposition of estimated portfolio volatility. It is not a probability, realized P&L attribution or maximum-drawdown decomposition. Negative contributions represent offsets in the estimated covariance model; other contributions can exceed 100%.

Existing history has been inspected. Sequential historical calculations and no-lookahead tests do not establish an untouched out-of-sample result. Portfolios have different exposures and total risk; return differences are not automatically alpha. Further work must test estimation stability, constraints, costs and frozen rules on new observations.
