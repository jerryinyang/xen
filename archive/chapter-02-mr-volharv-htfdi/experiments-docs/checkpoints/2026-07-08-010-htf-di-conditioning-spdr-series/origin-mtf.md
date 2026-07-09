# MULTITIMEFRAME EXPLORATION

**core thesis:** higher timeframe context gives credibility to lower timeframe decisions

**hypotheses**
- htf context/filter improves signal quality on ltf


**design**
* parameters:
  * htf-ltf domain pair: 1d/1h, 4h/1h, 1h/5min 
  * htf trend direction context/filter (toggle: on/off) — adx di +/-
  * htf trend strength context/filter (toggle: on/off) — adx 
  * htf volatilitity context/filter (toggle: on/off) — atr(14)
  
* control models: 
  * CTRL-01 (RANDOM)
    * random entry: 
        - split the [-1,1] range by `lambda`, such that the probability ratio of [SELL:NEUTRAL:BUY] is [1:lambda:1]
        - e.g. when `lambda=2`, ratio becomes `1:2:1`, therefore randomly generated number `<= -0.5` is a sell signal and `>= 0.5` is a buy signal
        - default: `lambda=2`
    * no filters, except an active holding period; if holding period is active, ignore new signals
    * fixed hold-period: 
        - exploration plane: |1x|2x|3x|4x htf period span equivalent in the ltf
        - e.g. 2x span for a 4h/1h domain pair is 4 bars
  * CTRL-02 (NAIVE MOMENTUM)
    * entry: 
        - long: bar close above the highest high of the last 3 bars
        - short: bar close below the lowest low of the last 3 bars
    * no filters, except an active holding period; if holding period is active, ignore new signals
    * fixed hold-period: 
        - +exploration plane: |1x|2x|3x|4x htf period span equivalent in the ltf
        - e.g. 2x span for a 4h/1h domain pair is 4 bars
  * CTRL-03 (NAIVE REVERSION)
    * entry: 
        - long: buy limit entry on the lowest low of the last 3 bars
        - short: sell limit entry on the highest high of the last 3 bars
        - limit order fills estimated/simulated with the 1-minute bars (our most granular local domain)
    * no filters, except an active holding period; if holding period is active, ignore new signals
      * if new signal comes before the price is filled, reset to the new liomit price; essentially a trailing limit price
    * fixed hold-period: 
        - +exploration plane: |1x|2x|3x|4x htf period span equivalent in the ltf
        - e.g. 2x span for a 4h/1h domain pair is 4 bars

* hypothesis models:
  * CTRL-01 | CTRL-02 | CTRL-03
    * with [ADX < 25 | ADX >= 25 & ADX < 75 | ADX >= 75] regimes (3 variants)
      * in each variant, filter results by the variant condition
    * with `LONG += +DI > -DI` and `SHORT = +DI < -DI`
      * in each variant, add the direction filter to each side of the signal
      * long: control long signal + filter long signal
      * short: control short signal + filter short signal
    * with [LOW|MEDIUM|HIGH] regimes (3 variants)
      * in each variant, filter results by the variant condition
      * use a robust estimation of vol regimes with ATR
    * with `ATR[LOW|MEDIUM|HIGH] + ADX[ADX < 25 | ADX >= 25]` (5 variants)
      * combinations of the two filters
    * with `ATR[LOW|MEDIUM|HIGH] + ADX[ADX < 25 | ADX >= 25] + DI_FILTER` (5 variants)
      * combinations of the two filters



**plans**
* SPDR-### experiments: I intend to introduce "speed-run" experiments. the purpose for this is to gate a "Worth Exploring Candidate" verdict on ideas (something like what EXP-021/022 were, but stripping some of the formal steps)
  * these would not go through the entire research-pipeline candidate family registration and checkpoiint design process, before the first run.
  * each experiment is majorly exploratory: each would compound more than 1 hypotheses/questions coherently, and would be run on the existing local dataset (not in cTrader yet)
  * the purpose is to execute early tests for availability with minimal constraints and qualification requirements (not the full referee framework)
