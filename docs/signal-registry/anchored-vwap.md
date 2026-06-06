# ANCHORED VWAP: VWAP Anchored on Market Regime Ranges

## MODEL DISCUSSION
- Core Theory: The model is based on the VWAP line, calculated with price data (source: typical price; HLC3) from the last anchor point which is defined by market trend regimes, weigthed by volume.
- Anchor points are dynamic and event-based; not fixed ranges or durations, as seen in traditional anchored VWAPs. When a trend change is confirmed [REQUIRES_DEFINITION], the anchor point resets to the last significant pivot [REQUIRES_DEFINITION], and the VWAP calculation resets cummulatively from there.
- Pivot Point Management:
  -  For efficiency in a streaming algorithm, the system has to track the most recent "viable" pivot point (both high and low), and should maintain a temporary cache of the necessary data from that point, until the pivot is "confirmed" by a confirmed trend change (at which point the temporary store is transferred to (or used as) the main storage structure for the VWAP calculation), or a new viable pivot is found.
  -  For simplicity, pivots should be the highest/lowest prices observed between trend regime changes.
  -  The temporary cahce is very important and should be different from the main storage structure for the VWAP calculation. The data could also be stored as a single incremented value (important bit is that it's separate). The separation is important because without this, at confirmation of a new trend, the algorithm would need to backtrack to the last viable pivot and recalculate up till the confirmation point; the temporary cache solves this.
- Trend Change Detection Methods:
  - Baseline Method: Moving Average Crossover (price-MA or MA-MA). The MA period depends on the timeframe domain (larger periods on smaller timeframes).
  - Linebreak Direction: the linebreak chart data serves as a good summarisation for trend. Change in direction of the latest linebreak bar (locked in realtime to the current traditional bar) is a valid regime change signal. [PARAM] the linebreak level
  - Market Bias Indicator Trend Value: `python/src/xen/indicators/market_bias.py`. Trend value here. [PARAM] market bias period
  - Pivot High/Low with ATR: Track the pivot high/low; the highest high/lowest low. When price deviates from that pivot point by a difference of `ATR * ATR_Mult`, trend change is confirmed. [PARAM] ATR_Mult
- The non-linearly volume weighted average price line is the core signal-generating source and hypotheses basis. 
- Bands: The bands calculated above and below the line to form a range, or a 3-line band. The distance is calculated based on the "Median Absolute Deviation" value of the source (typical price) data collected from the anchor point
- The VWAP and Bands values are constantly recalculated and updated with every new confirmed bar



## SIGNAL
This strategy theory is not fully formed; the actual signal for the strategy is undecided. All that is set in stone for evaluation is HYP-001; if this validated, a tradign system can be built around the proven observations. 
However, here's a complete working model (HYP-002) we can begin with, and subsequently, use as a benchmark for strategies built around this idea (if the hypothesis HYP-001 is supported).

### Definitions:
- the "bounce" (the signal trigger): this event defines the start of an interaction between price and the VWAP line, particularly the interaction we are interested in. For this model, a valid bounce/trigger would be defined as:
    > close price crossing the VWAP in the direction of the overall trend regime (see the "Sequence" section for details)
- "significant move": when qualifying a reaction off the VWAP, the move has to be explicitly quantified in one of many ways that define the lifetime of a move/bounce (targets or trend change):
  - targets: two targets (positive and negative) have to be deterministically (for reproducibility, especially during live trading) defined. The "positive" target defines the price at which the move is considered a successfull favourable excursion after the "trigger" (defined below). The "negative" target is the price at which a bounce is concluded to be unsuccessful. Based on targets alone, a move resulting from a bounce remains valid until one of the targets is reached. The upper and lower bands define the positive and negative targets for a Long trade respectively (switched for short trades).
  - trend change: additionally, a move can be considered completed when the trend regime changes to a different value from the move/signal's direction. If a move ends by a trend change event, evaluating the success/failure of the move/bounce is based on the net price change from the trigger point to the point of trend regime change
- performance metrics: to evaluate the efficacy of the moves, or significance of the bounce, we can evaluate:
  - successful bounce rate: how many bounces reached the positive target; win rate
  - bounce expectancy: expected return from a direction-signed bounce; this carries more useful information than
  - risk-adjusted return metric (e.g Sharpe ratio) of the returns series of the model compared to the raw/traditional (log) returns of the price series
  - valid bounce count/prevalence: characterise bounce/signal prevalence/availability

### Sequence:
- Trend change detection method returns a new "Bullish" regime. 
- The previously (or currently) tracked "viable/potential" anchor point (e.g the current pivot low) becomes the anchor point. 
- Source data (typical price) stored incrementally from that anchor point to the current regime change confirmation point is used to compute the
  - VWAP price
  - the MAD, and thus the upper and lower band price
- If subsequently, market price goes below the VWAP, we wait until it closes back above the VWAP; that's a valid bound trigger. 
  - Price "going below/above the VWAP" must be confirmed after bar confirmation — price action during live (unconfirmed) bars do not count.
  - If price never comes back up above the VWAP, the bounce never happened. If a trend change occurs subsequently, no bounce is recorded
- Once a bounce event is triggered, wait for the completion of the move (by target or trend change or both; operator's call, [PARAM])
- Once move completion is confirmed, record the move
  - performance should be tracked both individually and cummulatively, per instrument, timeframe domain, and trend/signal direction.



### Notes:
- Signals can only be considered after the point of confirmation of trend change (the sequence section clarified this). The period/data range between the viable pivot (confirmed by the trend change), and the actual trend change time/bar — that range cannot be evaluated for signals for the newly confirmed trend range or VWAP, because up until the confirmation, that period is under the previous trend regime, and only signals related to that trend regime count.
- Multi-bounce handling within a single regime: Each bounce should be recorded individually. Additionally, bounces that occur during another active bounce could be given an extra "pyramid bounce" tag, and can be evaluated specially too. For definition, a "pyramid bounce" occurs in this example:
> * Bullish regime confirmed
> * Price crosses below VWAP
> * Price closes back above VWAP → Bounce #1
> * Move completes
> * Later price goes below VWAP again
> * Later closes back above VWAP again

- Treatment of unfinished observations at end-of-sample: Ignore uncompleted observations.
- Regime-neutral periods: For simplicity, trend regimes are binary (Bullish or Bearish) for this model, and for the entire strategy theory.
- Cross-timeframe relationship: For this first stage, this would not be implemented. More advanced refinements like cross-timeframe analyses for more granular and precise entries, other exit and position management techniques, would be explored and tested.


## PARAMETERS (or [PARAM] inline)
[discussed inline]



## MODEL HYPOTHESES [HYPOTHESIS]
HYP-001: The VWAP line (or range/bands) serves significant support/resistance levels. Therefore, price is more likely to react off these levels, and make significant moves. [REQUIRES_DEFINITON]: "significant moves", "price reaction" requires precise testable definition.
HYP-002: Signal model viability



## CAVEATS [CAVEAT]
- Only `Tick Volume` data available currently, not actual `Trading Volume`. Therefore, VWAP would be an approximation.
- To prevent over-senstivity or overreaction to tick volume, i.e robustness to tick volume spikes, we would employ weight tick volume nonlinearly. Instead of using raw tick volume as the VWAP weight, use `w=TV^{\alpha},\quad 0.5\leq\alpha\leq0.9`, and then calculate VWAP with these adjusted weights. [PARAM] alpha is therefore tunable.
> Typical values
>  * \alpha = 1.0: Standard tick-volume VWAP.
>  * \alpha \approx 0.75: Good balance for most FX applications.
>  * \alpha = 0.5: Strong compression (square-root weighting).