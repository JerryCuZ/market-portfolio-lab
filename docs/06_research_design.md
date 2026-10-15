# Lesson 06: fixed research design

Recorded before running the lesson's performance comparison on 2026-10-15 (America/New_York). This is an educational specification, not independent preregistration or an untouched test sample. Prior lessons have already examined this historical period.

- Question: does a simple trend filter change the drawdown/return/cost tradeoff of the existing ERC portfolio?
- Universe and snapshot: SPY, IEF, GLD; original verified snapshot `20261007T234808781424Z`. No market refresh or parameter search in this lesson.
- Baseline: 126 prior-return ERC, monthly first-observed-session opening execution.
- Signal: prior adjusted close strictly greater than the arithmetic mean of the previous 200 observed adjusted closes, including that close. Equality is off. Decide at the previous observed close. Monthly evaluation only.
- Mapping: multiply each full-universe ERC target by its own binary signal. Do not refit ERC on survivors or renormalize. Unallocated capital targets zero-interest cash; all cash is allowed. No shorts, leverage, cap overlay, or rebalance threshold.
- Comparison start: first monthly ERC date with at least 253 preceding price rows (same warm-up convention as lesson 05's 252-return comparison); both portfolios start with USD 100,000 on that date.
- Accounting: existing ledger conventions, 5 bps each side, fractional shares, idealized opening execution, distributions immediately credited on ex-date. Zero cash yield is a simplifying assumption, not a Treasury-bill return proxy.
- Outputs: full-period metrics, net value/drawdown/actual cash charts, dated signal audit, signal flips, annual returns, chronological historical segments before/after 2020-01-01, and 0/5/20 bps execution-cost sensitivity. Segment returns inherit the continuous account and include the first segment day's return from the prior close; segment drawdowns reset at the boundary.
- Interpretation: no alpha claim, no matched-risk comparison, no causal claim that lower drawdown proves timing skill. Chronological segments are descriptive robustness diagnostics, not genuine out-of-sample evidence. Report adverse years and lag/whipsaw failure modes, not only favorable outcomes.
- Next validation: exposure-matched controls, cash-yield sensitivity, timestamped frozen-rule forward observations, and explicit validation protocol before tuning/ML. These remain future work.

Reading: [Faber's moving-average allocation paper](https://mebfaber.com/2009/02/19/a-quantitative-approach-to-tactical-asset-allocation-updated/) and [Moskowitz, Ooi and Pedersen: Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum). This ETF long-or-cash overlay is an educational adaptation, not a reproduction of either paper's full implementation or results. A 200-daily-close average is not identical to a 10-month-end-close average.
