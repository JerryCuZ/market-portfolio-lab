# Roadmap

## Implemented

- [x] Real-data snapshot acquisition, validation and checksum verification.
- [x] Returns, distributions, volatility, drawdowns and changing correlations.
- [x] Fixed-weight hold/monthly baselines and an auditable cash/share ledger.
- [x] Inverse-volatility targets and risk-contribution analysis.
- [x] Correlation-aware equal risk contribution and solver checks.
- [x] Dated target schedule interface shared by allocation models.
- [x] Thirty offline tests and eight executed learning reports.

## Experiments completed and next research questions

- [x] Proportional target caps and their departure from equal risk contributions.
- [x] Window sensitivity across 63/126/252 prior returns on a common interval.
- [ ] Covariance shrinkage and alternative estimation methods.
- [x] Monthly prior-close rebalance threshold experiment, including cost and drift measurements.
- [x] First fixed 200-day SMA long/cash overlay experiment, annual and historical-segment diagnostics, 0/5/20 bps sensitivity.
- [x] Initial fixed-70%, dynamic-total and explicitly post-hoc mean-target exposure comparisons (lesson 07).
- [ ] Establish signal value with prior-information controls and prospective evidence; lesson 07 does not prove timing alpha.
- [x] Cash-yield sensitivity with historical FRED DFF and a documented frozen-rule validation protocol (lesson 08).
- [ ] Implement prospective data/decision archives and formally start frozen-rule forward simulation; the protocol alone is not forward evidence.
- [ ] How accurate are forward risk forecasts, separately from portfolio performance?

Stage I (lessons 01–05) built allocation/accounting foundations. Stage II starts at lesson 06 with signal research; a completed experiment does not establish strategy effectiveness.

## Later, when prerequisites are met

### Beyond long-only, unlevered ETFs — requested progression

These are planned simulation capabilities, not implemented features. Introduce them progressively after exposure controls, cash-yield treatment and a credible signal-validation protocol are established; do not add complexity simply to improve a backtest.

1. **Exposure measurement:** distinguish market value, notional exposure, gross/net exposure and factor sensitivity. Produce exposure reports that reconcile to positions and explain why low net exposure need not mean low risk.
2. **Financing and leverage:** add borrowing balances, financing rates, leverage limits, margin requirements and forced-reduction scenarios. Validate interest, NAV and stress behavior on hand-calculated fixtures before comparing leveraged strategies.
3. **Short selling:** model negative holdings, borrow availability/fees, dividend payments owed, collateral and recall/cover scenarios. Test P&L and cash independently before constructing a long/short experiment.
4. **Futures as an instrument extension:** add contract multipliers, margin, daily settlement, expiry and rolls using appropriate real contract data. Separate collateral from economic exposure; a continuous price series alone is not a tradable account.
5. **Options only after these foundations:** introduce nonlinear exposure, Greeks, expiry/exercise and liquidity with suitable data. Treat this as a separate instrument module, not negative ETF weights.

Each step should include a beginner explanation, explicit data/assumption limits, reconciled accounting tests and a small comparison against the existing baseline. Timing depends on learning readiness and data quality, not a fixed lesson number. No broker action or actual financing is implied.

### Other extensions

- [ ] Linear/tree models followed by more complex ML only against credible simple baselines.
- [ ] AI-assisted research or text features with provenance, availability timestamps and evaluation.
- [ ] User-supplied positions and cash, decision reports and explainable proposed trades.
- [ ] Frozen-rule forward simulation, anomaly handling and persistent decision archives.
- [ ] Paper-broker adapter, actual distribution payment dates, settlement and execution calibration.
- [ ] Additional assets/strategies with instrument-specific data and accounting.

No deadline or promise of profitability is implied. Real trading requires a separately reviewed implementation; a new model must not bypass account, timing or execution constraints. High-frequency and derivatives strategies require new data and mechanics, not simply a model swap.
