I want to characterise one simple concept: "Liquidity sweeps".

# Definitions
For the purpose of the experiment,
1. A "liquidity level" or "pivot level" or "swing point" is simply any significant swing high or low. For different scenarios, this could mean:
    * A: previous 1D/1W/4h/1h high and low. 1H/4H are completed contiguous clock bars. 1D/1W are the previous completed New York 17:00 trading day and the previous completed Monday–Friday trading week (DST-aware). They are not 1,440/10,080-minute bars and not UTC calendar dates.
    * B: most recent session (asia/europe/america) session highest and lowest prices
    * C: rolling highest-high[period] or lowest-low[period], where `period` signifies the number of historical bars to consider
2. A "swing move" is the price action between pivot levels.
3. A "sweep" is a completed raid of a liquidity level followed by a later strong move in the opposite direction. The experiment does not try to predict sweeps while they are happening. It first records the observable price behaviour, then classifies the eventual outcome retrospectively.
    * An "excursion" is price moving beyond an active liquidity level. It is tracked online, bar by bar, on the cell's observation timeframe (the same 15m / 30m / 1h bar that defines the level catalogue for that cell).
    * A raid starts on a completed observation bar that goes strictly beyond the level. Return to the level is recorded when it happens (same bar or later) but is not required to open the raid and does not close it. Confirmation or fail on the reference clock settles the raid (AMENDMENT-13). The older two-bar / same-bar-close reading is retired.
    * A completed raid is worth recording even if it does not produce a strong swing. It is only later classified according to the move that follows it.
    * A level can have multiple completed raids or retests. Each raid is recorded separately, while the level retains its total raid count and the metadata and outcomes of previous raids.
    * The later swing is attributed to the level, not to one specific raid. If multiple levels are raided before a confirmation event, the most recently raided level receives the attribution (primary). Earlier eligible returned raids are settled on that same confirmation/breakout event: expected-side as non-primary confirmed, opposing-side as failed breakout. They retain their own maximum excursions through settlement and do not stay live until a later opposing event or right-censor solely because a newer raid is primary. (Operator amendment 2026-08-12 — close-all-eligible.)
    * The level direction is implied by its type: a high is raided above and the expected reversal is downward; a low is raided below and the expected reversal is upward.
    * A breakout is a competing outcome of an excursion. Once the move is confirmed as a breakout, that excursion is recorded as a failed sweep. Breakouts are not the main object of this hypothesis group, but they must be retained to avoid analysing only successful sweeps.
    * The main question is whether raided liquidity levels lead to strong swing moves, including when multiple raids happen before the eventual move.
    * Every active raid remains tracked until a direction event settles it, or the TRAIN boundary right-censors it. Same-bar pierce-and-return stays live. Outcomes:
        - a same-direction event on the expected reversal side confirms eligible returned raids; the latest primary stays live while the later swing continues; earlier eligible raids close as non-primary confirmed at that event
        - an opposite-direction event on the excursion side confirms a breakout and failed sweep for every eligible returned unconfirmed raid
    * The later swing is considered complete when the opposite direction event occurs after a sweep has been confirmed. These events should be defined using higher-degree liquidity levels, rather than arbitrary distance thresholds.
    * Confirmation uses a completed reference bar's close beyond the previous
      reference bar's high/low (breakout-bar), or a close beyond a configured
      higher-degree level. Current pairing (operator 2026-08-13): 1H for 15m/30m
      cells; both 1H and 4H for 1h cells, as separate strata. Daily confirmation
      is retired because 1h→1D left returned raids unsettled on TRAIN.
    * Rolling highest-highs/lowest-lows with a larger period may be considered later, but introduce another period choice and assume that the resulting level is sufficiently far away.
4. For every active level and timestamp, the online state should record:
    * whether price is beyond the level
    * current excursion magnitude and duration
    * whether price has returned to the level
    * number of completed raids on the level
    * metadata for each completed raid
    * the eventual outcome of each raid, once known
5. For every completed raid, the experiment should retain enough information to measure:
    * maximum excursion beyond the level
    * excursion duration
    * reversal or swing magnitude
    * reversal or swing duration
    * whether the later swing exceeded the initial excursion
    * number of previous raids on the level
    * whether a value gap occurred
    * whether the level was eventually confirmed as a sweep or invalidated by a breakout
6. Value Gap definition
    * Area of interest: from the maximum excursion price of the sweep to the price of same-direction confirmation event of the positive reversal from the sweep.
    * Method:
        - compute the market profile (TPO) of that price and time range
        - compute the value area (VA) of the TPO: the area containing 70% of the total price
        - compute the value gap of the VA: the area with the least 30% of the VA, between the value area high and low
        - a gap is tight when that selected span is strictly below 50% of the full VA width
    * This has to be designed and maintained in an online data streaming format to avoid recursive backtracking and rebuilding of market/price profile


## Constraints, Caveats, Clarifications
- for the purpose of the experiment, a catalog/set of liquidity levels is considered at each timestamp for every level definition/type/config. this is purely for full exploration and characterisation
- depending on the definition, the price levels can have different degrees of significance. e.g. for definition C, the `period` parameter directly encodes significance; for A, significance grows with timeframe (1W levels > 1D levels)
- to avoid referring to every significant pivot level in history, restrict the window to only the most recent completed session of whatever domain is under consideration. Only those levels make up the catalog at any timestamp. e.g.
    - the previous 1D/1W/4h/1h highs and lows are significant levels for the current session only (1D = last NY-17:00 trading day; 1W = last Mon–Fri book closed Friday 17:00 NY)
    - for intraday sessions, the highest and lowest prices of each completed trading session from the previous day only
    - rolling highest-highs/lowest-lows are safe to get up to the most recent completed bar of the current timeframe, as they are strictly decided online with no lookahead. therefore, this is the only type of level that can contain information from the current session
- the experiment should not discard a raid because it does not immediately produce a strong move. its later outcome is part of the analysis
- multiple raids on one level should not be collapsed into one event. they should be linked to the same level so that repeated interaction can be analysed

# Hypothesis
- level significance directly maps to likelihood of a strong reversal or swing move
- repeated raids change the likelihood or strength of the eventual swing move
- levels that produce strong moves may typically require more than one raid
- a sweep that leaves a tight value gap is more significant and tradable
  - A "tight" value gap is a value gap with a span less than 30% of the full VA width/magnitude
- volatility regime affects the frequency, magnitude, duration, and quality of raids and subsequent swing moves
- [deferred/gated by operator] only levels that cause breakouts are significant


# Strata
- Timeframe
- Asset class
- Specific liquidity-level type and config
- Level significance
- Number of previous raids on the level
- Volatility regime

# Labels
These would be emitted for every timestamp of the data for future analysis.
* Volatility regime; useful to
  - characterise liquidity sweeps: what regimes are likely to produce more/better sweeps ("better" depends on what is being measured); typical regime label during the excursion, raid, and later swing phase; typical magnitude and duration of raids per volatility regime
* Level and raid state; useful to
  - identify active levels, current excursions, completed raids, retests, raid counts, and breakout status
* Later outcome; useful to
  - associate each completed raid with the eventual swing magnitude, duration, endpoint event, value gap, and whether the move was strong or invalidated


# Open Questions, Unorganised Ideas
- the design for tracking levels, excursions, raids, and their later swing outcomes has to be in an online/streaming/event-based data availability format (per bar), not vectorised or retrospective
- both confirmation definitions are retained as separate methods; the reference
  clock is 1H for 15m/30m and both 1H and 4H for 1h (daily confirmation retired)
- whether any additional state or emissions are needed beyond the level, excursion, raid, confirmation, breakout, and later swing data. leave this for the quant designer during execution

Plan all these into single checkpoint, with experiments for each hypothesis group. I'm providing little contextual explanations to the concepts and hypotheses to avoid any bias in the analysis; just clear empirical analytics.
