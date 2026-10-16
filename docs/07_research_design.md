# Lesson 07: exposure controls

Specified 2026-10-16 before this lesson's comparisons. Historical outcomes and lesson 06's average cash are already known; this is not independent preregistration or untouched out-of-sample research.

Question: how much of the trend overlay's historical tradeoff is also obtainable through lower exposure, and how does asset-specific filtering differ from scaling the entire base portfolio?

Keep snapshot, dates, 126-return ERC, 200-price SMA, monthly execution, USD 100,000, 5 bps, zero cash yield and accounting unchanged from lesson 06. No optimization or new prices.

Five schedules:
- `erc_126`: full ERC reference.
- `trend_200`: unchanged asset-specific long/cash filter.
- `fixed_70`: 0.70 times each ERC target; cash target 30%. Illustrative round number informed by the previous lesson, not optimized or independently selected before observing history.
- `dynamic_total`: e_t times each ERC target, where e_t is the sum of trend targets at that decision. Same monthly total target exposure as trend, original ERC proportions retained. Signal information is available at prior close, but actual daily exposures and portfolio risks need not match.
- `matched_mean_POSTHOC`: constant multiplier equal to the arithmetic mean of all monthly trend target exposures. Matches mean monthly targets, not daily realized exposure, volatility or losses. Uses future observations; diagnostic only, never a tradable historical claim.

Evaluate full-period account metrics, actual daily and monthly target exposure, annual returns, target and realized cash charts, and paired differences at 0 and 5 bps. Report partial years. Differences are strategy contrasts, not additive causal attribution or validated alpha. No claim that uniform scaling eliminates selection effects or that comparing it to a static control proves timing skill.

Next: credible cash-yield assumptions and forward-validation design, with a reference chosen using only prior information. No parameter search, financing, shorts, futures or live trades here.
