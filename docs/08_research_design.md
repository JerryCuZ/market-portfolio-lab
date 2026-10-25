# Lesson 08: cash yield sensitivity

Defined 2026-10-25 before performance comparison. Preserve original ETF snapshot, 2011-02-01–2026-10-06 interval, risk/signal schedules and 5 bps execution costs. Four policies: full ERC, trend, fixed70 and dynamic total. Exclude the prior lesson's future-informed diagnostic from tradable-rule comparisons.

New data: FRED DFF (effective federal funds rate), downloaded as immutable hash-verified CSV. It is an interbank reference, not an investable cash instrument or promised broker rate. Current-vintage history may be revised. Source: https://fred.stlouisfed.org/series/DFF ; publication context: https://www.newyorkfed.org/markets/reference-rates/effr .

Scenarios fixed before running: zero; lagged reference; max(lagged reference−100 bps,0). The spread is illustrative, not empirically estimated broker pricing. Use at least seven calendar days' lag at each accrual interval start. This artificial delay is a deliberately conservative teaching rule, not measured publication metadata or proof of point-in-time availability. No backward fill; rate more than three days older than the lag cutoff is rejected.

Accrual: previous closing cash × simple annual decimal rate × calendar days/360. Freeze rate during each close-to-next-observed-session interval; no daily compounding inside weekends, compound after each credit. Credit at next observed session before distributions/trades; first day accrues nothing. Today's sales and distributions cannot earn prior-interval interest. No withholding tax, tiering, sweep eligibility, settlement delay or monthly payment modeling. Interest can fund that day's scheduled rebalance. Existing threshold decisions still use previous cash, before today's credited interest.

Report all scenarios, CAGR shifts, drawdowns, fees and explicit interest totals. Ending NAV gain need not equal summed interest: reinvestment changes future holdings and fees. Cash-only check isolates the modeled accrual path. Zero scenario must reproduce prior lesson metrics.

No ranking claim is guaranteed; do not change spreads or signals to make a winner. Cash remuneration and actual tradeable cash proxies remain different models. No live forward record is initiated by this lesson; see validation_protocol.md for the next gate.
