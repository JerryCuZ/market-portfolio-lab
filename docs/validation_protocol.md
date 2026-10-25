# Validation protocol — next gate, not completed evidence

Status: documented 2026-10-25; no prospective trading record or broker connection has been started. Existing 2011–2026 history is explored data, including any split at 2020. A future start date is set only when data capture and decision logging are operational, never backdated to call already-observed history unseen.

Before starting forward simulation:
1. Freeze strategy version, asset universe, signal/risk windows, target mapping, execution convention, cash treatment, costs and primary baseline. Save code/data hashes and a timestamped configuration.
2. Specify the intended improvement before looking at new outcomes: net return, drawdown tradeoff and turnover together, with exposure/cash statistics. Fix a review window and acceptance criteria then; do not choose them to fit later results. No automatic minimum-duration claim of statistical validity.
3. Store each original data snapshot and each decision before the subsequent execution observation; log missing data, corrections, delayed decisions and rule deviations. Use original availability timestamps where possible; current downloaded adjustments are not a historical vintage archive.
4. Keep the full ERC and fixed-exposure reference alongside the candidate, under identical cash/cost treatment. Exclude POSTHOC controls from deployable performance claims.
5. At predeclared review points, report the complete period, failure episodes and all versions tried. A rule change creates a new version and a new forward segment; never overwrite old decisions. No cherry-picked start dates or silent relabeling as out-of-sample.

Next practical work: choose and validate the cash implementation, then establish manual snapshot/decision logging. Scheduling, broker orders, borrowing and leverage are not authorized by this document. Advanced mechanics follow the staged roadmap after accounting and validation prerequisites.
