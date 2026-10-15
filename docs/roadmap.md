# Roadmap

## Implemented

- [x] Real-data snapshot acquisition, validation and checksum verification.
- [x] Returns, distributions, volatility, drawdowns and changing correlations.
- [x] Fixed-weight hold/monthly baselines and an auditable cash/share ledger.
- [x] Inverse-volatility targets and risk-contribution analysis.
- [x] Correlation-aware equal risk contribution and solver checks.
- [x] Dated target schedule interface shared by allocation models.
- [x] Twenty-three offline tests and six executed learning reports.

## Experiments completed and next research questions

- [x] Proportional target caps and their departure from equal risk contributions.
- [x] Window sensitivity across 63/126/252 prior returns on a common interval.
- [ ] Covariance shrinkage and alternative estimation methods.
- [x] Monthly prior-close rebalance threshold experiment, including cost and drift measurements.
- [x] First fixed 200-day SMA long/cash overlay experiment, annual and historical-segment diagnostics, 0/5/20 bps sensitivity.
- [ ] Distinguish timing value from reduced exposure using credible controls.
- [ ] Cash-yield sensitivity and a frozen-rule forward-validation protocol.
- [ ] How accurate are forward risk forecasts, separately from portfolio performance?

Stage I (lessons 01–05) built allocation/accounting foundations. Stage II starts at lesson 06 with signal research; a completed experiment does not establish strategy effectiveness.

## Later, when prerequisites are met

- [ ] Linear/tree models followed by more complex ML only against credible simple baselines.
- [ ] AI-assisted research or text features with provenance, availability timestamps and evaluation.
- [ ] User-supplied positions and cash, decision reports and explainable proposed trades.
- [ ] Frozen-rule forward simulation, anomaly handling and persistent decision archives.
- [ ] Paper-broker adapter, actual distribution payment dates, settlement and execution calibration.
- [ ] Additional assets/strategies with instrument-specific data and accounting.

No deadline or promise of profitability is implied. Real trading requires a separately reviewed implementation; a new model must not bypass account, timing or execution constraints. High-frequency and derivatives strategies require new data and mechanics, not simply a model swap.
