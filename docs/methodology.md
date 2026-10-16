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

## Lesson 05: stability and execution constraints

Use 63/126/252 prior adjusted returns, with all scenarios starting afresh at the first shared execution date after the longest warm-up. Keep USD 100,000 and 5 bps per side unchanged. The 126-day ERC baseline is compared separately against each overlay; cap and threshold are not combined.

The 50% cap locks excessive weights and proportionally redistributes to remaining assets, repeating if necessary. It preserves full investment but is not a constrained risk-budget optimizer. Original ERC solver diagnostics are removed from the modified schedule. Recomputed risk shares audit the departure. Caps govern targets, not continuous actual holdings.

The 3-percentage-point threshold checks the maximum absolute difference between prior-close actual and new target weights, including cash, at monthly opportunities. Only a strictly greater gap triggers a full rebalance; initial investment always occurs. Decision dates must match the previous observed session after initial entry. Today's opening gap and distributions do not enter the prior-close trigger. Fills still use idealized next-open sizing, not actual broker orders. Daily ledgers record opportunities, triggers and decision gaps.

Target instability is the mean sum of absolute month-to-month asset target changes, excluding the initial undefined change. Holding drift is the maximum asset-or-cash absolute target gap at each daily close. Gross turnover is total absolute daily traded notional divided by prior-close NAV (initial capital on day one), summed and divided by calendar years; includes entry and is explicitly two-sided. It is not the one-way half-turnover convention. These teaching parameters are not tuned or out-of-sample validated.

## Lesson 06: signal layer and all-cash targets

The fixed design is documented in [06_research_design.md](06_research_design.md). At each baseline monthly execution date, compute the arithmetic mean of exactly 200 adjusted closes ending at the previous observed session. Strictly above that mean enables the asset; equality or below disables it. Multiply each full-universe ERC target by its binary signal. No renormalization, survivor-universe ERC refit, shorting, leverage, cap or threshold overlay. The residual is zero-interest cash. The ledger now explicitly accepts all-zero asset targets and tests liquidation, dividend entitlement and reentry with costs.

Signal timing is checked against the preceding observed session, and future-price perturbations leave prior signals unchanged. This does not resolve retrospective adjusted-data revisions. A 200-day SMA is not a 10-month-end SMA. Price-based signals are historical state rules, not calibrated return probabilities.

Annual returns compound daily ledger returns, including entry fees; first/last years are partial. Chronological segments split at 2020-01-01, inherit the continuous account, include the first day's return from prior-close NAV and reset drawdown peaks at the segment boundary. Their CAGR uses elapsed time from the previous boundary valuation (or first execution day at initial entry, consistent with the ledger). No fitting or parameter selection uses this split, but both periods were already observed: do not call it pristine out-of-sample validation. Risk exposures are not matched; higher cash can mechanically reduce drawdown. Cost sensitivity changes only the per-side bps assumption with identical target schedules.

## Lesson 07: exposure controls and inference limits

See [fixed design](07_research_design.md). `fixed_70` scales each fully invested ERC target by 0.70; the round number was chosen after seeing prior historical results, not independently validated. `dynamic_total` scales ERC by the same decision's sum of trend weights, keeping ERC proportions and matching monthly target total exposure only. `matched_mean_POSTHOC` scales ERC by the full-sample mean of monthly trend total targets: future-informed diagnostic, not a tradable historical rule. Mean daily actual exposure and realized volatility can differ for every control.

The scaling helper preserves dates, requires prior decisions and exact series alignment, and removes inapplicable ERC solver diagnostics. It cannot certify provenance of user-supplied exposure factors. Full ledgers, costs, annual results (partial first/last years), and 0/5 bps pairs are retained. Policy contrasts do not provide additive causal attribution, matched-risk alpha or statistical significance. Cash remains zero-yield; exposure-sensitive cash-return assumptions are the next research step.
