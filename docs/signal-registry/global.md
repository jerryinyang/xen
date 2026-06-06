# GLOBAL TECHNIQUE REGISTRY
[this would be populated incrementally in the future; for now, I'm writing down models/techniques I intend to test later]

## ENTRY



## EXIT
### Heiken Ashi Exhaustion Patterns
These patterns aim to exploit "exhaustion tells" from the Heiken Ashi. Each of these fall of different places of the spectrum of "Lagless -> Sensitivity to Noise -> Early Exit (pros+cons)" to "Lagged -> Robustness to Noise -> Late Exits (pros+cons)"

#### Pattern #1: Harami Pattern ()
- HA_Bar_0: Latest Heiken Ashi Bar
- Signal: `MAX(Bar_Close_1, Bar_Open_1) > MAX(Bar_Close_0, Bar_Open_0) && MIN(Bar_Close_1, Bar_Open_1) < MIN(Bar_Close_0, Bar_Open_0)`
- Variants: 
  - Bar Direction: 
    - alternating colors: signal same direction as `Bar_0`
    - any direction; as long as harami size pattern is met

#### Pattern #2: Trailing Exit Price
- Price: Heikin Ashi `Bar_High` or `MAX(Bar_Close, Bar_Open)` for short exits; Heikin Ashi `Bar_Low` or `MIN(Bar_Close, Bar_Open)` for long exits
- Modality Variants:
  - Stop Order: triggered on price fill
  - Market Order: triggered on bar close (or new bar open) beyond the trailing price.
- Note: fill price is always the traditional candlestick, not heikin ashi

### Last X HH/LL 
- Price: Highest/Lowest Price from the last X bars (traditional cnadlesticks). 
- `1 <= X <= ...`. For example, where `X == 1`, only the previous candle's hgi/low is considered
- Modality Variants: [same as "Pattern #2, HA Exhaustion Patterns"] 




## POSITION MANAGEMENT

### Pyramiding Positions
- Allow additional entries (by signal discovery) in the same directions as the positions is already opened.
- PARAM: max_open_positions


## RISK MANAGEMENT



## NOTES
Many of the claims, assumptions, options, parameters, suggetions e.t.c in this document would require individual experiments to emperically support or disprove them. As earlier mentioned, the strategy theory counts more like an idea than a complete model specification, though most of these specs should not be changed, only clarified.