# The detection floor in SPDR-024 — why every read came back unresolvable

- **Date:** 2026-08-07
- **Checkpoint:** 018 — trade-opportunity capture geometry
- **Subject:** the MDE / resolution apparatus in `SPDR-024`, as it stood in the artifacts under
  `python/experiments/SPDR-024/results/` and as reported in `python/experiments/SPDR-024/analysis.md`
- **Trigger:** operator observation that SPDR-024 disqualifies reads as underpowered on every ground
  at once, and that the size of the shortfall is implausibly large.
- **Band:** TRAIN only. No TEST, no holdout, no run re-executed for this document.

**Boundary.** This is a document about the **apparatus**, not about the candidate. It takes no
experiment verdict, no family disposition, no arm ranking, no tradability claim. It does not convert
any SPDR-024 `NOT_RESOLVABLE` into a positive or a negative read; the defects below make the run's
resolution labels unreliable **in both directions**. Every figure is gross (SPDR-024 charges no
spread, `analysis.md` §0).

**Everything below is re-derived from the emitted parquet/JSON, not from `analysis.md` prose.** The
reproduction script is in §10.

---

## 0. The finding in one paragraph

SPDR-024's detection floor is not too high because the data is thin. It is too high because the
floor and the effect are measured against **different, incompatible scales**, and five separate
inflations compound on top of that mismatch. The largest single term is structural: for a pure SIZE
device the σ̂-normalised estimand is arithmetically pinned to the baseline's **per-trade Sharpe
ratio** (0.032–0.059 in these four cells), while the floor is `2.8/√n`. Reaching a floor below the
ceiling requires 2,270–7,501 independent blocks in the *best* case per cell, and only one of four
cells has that. Three of four cells were incapable of resolving anything **before the run started**,
by arithmetic that was computable at design time and was not computed.

---

## 1. Provenance and the exact objects under review

| Object | Path |
|---|---|
| Scale-channel estimates | `python/experiments/SPDR-024/results/analysis/<cell>/scale_channel_estimates.parquet` |
| Selection-channel estimates | `python/experiments/SPDR-024/results/analysis/<cell>/selection_channel_estimates.parquet` |
| Preflight power block | `python/experiments/SPDR-024/results/preflight/<cell>.json` → `P1_pooled` |
| Analyser | `python/src/xen/adaptive_management/spdr024_analysis.py` |
| Binding design | `python/experiments/SPDR-024/design.md` §10 (power), §11 (bands) |

Cells: `crypto_H1`, `crypto_H4`, `ctrader_H1`, `ctrader_H4`.

Two constants govern everything:

```python
MDE_Z = 2.8                                 # spdr024_analysis.py:31
STEP3_OBSERVED_EFFECT_SIGMA_MAX = 0.150     # :36
STEP3_OBSERVED_EFFECT_SIGMA_MIN = 0.022     # :37
```

and one formula:

```python
"mde_sigma": MDE_Z / np.sqrt(effective_blocks)    # spdr024_analysis.py:392
```

---

## 2. Defect 1 — the estimand cannot produce effects as large as the yardstick

### 2.1 The identity

`analysis.md` §3.1 already records that for a SIZE arm the paired difference is exactly
`(risk_size − 1) × baseline_outcome`, verified to a maximum absolute difference of 0.0. Carry that
one step further, to the quantity that is actually banded.

For a gate firing at rate `p` with multiplier `m`, on baseline outcomes `y`:

```
delta_i   = (m − 1) · y_i · 1[gate_i]
mean      = p (m − 1) E[y | gate]
sd        = |m − 1| · sqrt( p·E[y²|gate] − p²·E[y|gate]² )   ≈  |m − 1| · √p · σ_y
```

so

```
estimate_σ̂  =  mean / sd   ≈   √p · ( E[y] / σ_y )   =   √(gate_rate) × baseline per-trade Sharpe
```

**The multiplier cancels.** The σ̂-normalised sizing effect is not a property of how hard the device
cuts exposure. It is the baseline's own Sharpe ratio per trade, attenuated by the square root of the
gate rate. Nothing a SIZE device does can move it past that ceiling.

### 2.2 The ceiling, measured

Baseline levels from `baseline_characterisation.parquet` (reproduced in `analysis.md` §2):

| Cell | baseline gross mean (bps) | σ (bps) | **per-trade Sharpe = ceiling at p=1** | predicted median ceiling at realised `gate_rate` | observed max \|estimate_σ̂\| |
|---|---:|---:|---:|---:|---:|
| crypto H1 | +5.21 | 152.3 | **0.0342** | 0.0226 | 0.0490 |
| crypto H4 | −8.80 | 272.2 | **0.0323** | 0.0225 | 0.0648 |
| cTrader H1 | +1.10 | 27.0 | **0.0407** | 0.0315 | 0.0692 |
| cTrader H4 | −2.48 | 42.2 | **0.0588** | 0.0478 | 0.0871 |

(observed = POOLED, PRIMARY lens, `regime == ALL`, governing treatment)

Prediction and observation agree to within a factor of ~1.8 across all four cells, which is what the
approximation's dropped `E[y|gate] ≠ E[y]` term is worth. **The identity holds.**

Across the *whole* run — every arm, every regime stratum, both universes, both domains, POOLED,
governing treatment — the estimand's realised range is:

| Cell | max \|est\| | p90 | median | governing floor (median) |
|---|---:|---:|---:|---:|
| crypto H1 | 0.0676 | 0.0505 | 0.0242 | 0.0527 |
| crypto H4 | 0.0794 | 0.0711 | 0.0416 | 0.1099 |
| cTrader H1 | 0.1149 | 0.0734 | 0.0520 | 0.1169 |
| cTrader H4 | 0.1571 | 0.0848 | 0.0487 | 0.2129 |

**In three of four cells the median floor is above the maximum effect the estimand produced
anywhere in the cell.** The top of the declared reference range, 0.150 σ̂, is exceeded exactly twice
in ~460 pooled rows, both in the thinnest cells where it is a noise excursion.

### 2.3 The data requirement, stated as it should have been at design time

Setting `2.8/√n = ceiling` and solving:

| Cell | ceiling (σ̂) | governing floor | floor ÷ ceiling | governing eff. blocks | blocks needed | **shortfall** |
|---|---:|---:|---:|---:|---:|---:|
| crypto H1 | 0.0342 | 0.0394 | 1.15× | 5,058 | 6,710 | **1.3×** |
| crypto H4 | 0.0323 | 0.0807 | 2.50× | 1,203 | 7,501 | **6.2×** |
| cTrader H1 | 0.0407 | 0.0842 | 2.07× | 1,107 | 4,734 | **4.3×** |
| cTrader H4 | 0.0588 | 0.1639 | 2.79× | 292 | 2,270 | **7.8×** |

This is the answer to *"why is the scale difference so exorbitant?"* It is not exorbitant. It is
`(floor ÷ ceiling)²`, and the floor-to-ceiling ratio is 1.15–2.79 because the two quantities were
never set on the same scale. A 2.8× ratio in σ̂ is a 7.8× ratio in required sample, and that is what
reads as implausible when you meet it in the report rather than in the design.

Note the block deficit understates the trade deficit: `effective_blocks / n_trades` runs 0.60–0.65
in these cells, so the shortfall in *filled trades* is larger again.

---

## 3. Defect 2 — the yardstick is built from estimates that were themselves declared unresolved

`design.md:538`, in the design's own words:

> DIRECTION-vs-MAGNITUDE: reported as two separate reads. Step-3's sizing result was
> direction-certain (236/236 resolving rows one side, 6/6 cells) and **magnitude-unresolved
> (0.022-0.150 sigma-hat)** SIMULTANEOUSLY.

`0.022–0.150 σ̂` is the spread of Step-3's own **point estimates**, which Step-3 declared it could not
resolve. Those numbers sat inside Step-3's own intervals. SPDR-024 promotes them at `design.md:507`
to *"the family's observed effect range"* and builds the entire resolution ladder on them:

```text
UNPOWERED           : MDE_sigma > 0.150
PARTIALLY_RESOLVING : 0.022 < MDE_sigma <= 0.150
FULLY_RESOLVING     : MDE_sigma <= 0.022
```

Two consequences, both realised in the run:

**(a) Circularity.** The bar is a set of magnitudes nobody has established are real. SPDR-024 is
required to resolve a magnitude whose existence is the open question.

**(b) The bottom endpoint is a minimum over noise draws, so it drifts toward zero.** `0.022` is the
smallest of a set of unresolved estimates. Add cells and it shrinks. `FULLY_RESOLVING` therefore
gets *harder to reach the more the family measures*. Concretely:

```
FULLY_RESOLVING needs  MDE_sigma <= 0.022  ->  n >= (2.8/0.022)² = 16,198 independent blocks
largest cell in this run                    ->  5,058
shortfall                                   ->  3.2x
```

**No cell in SPDR-024 could ever have been `FULLY_RESOLVING`.** Since `WASH` — the only band in the
whole taxonomy that expresses a genuine null — is gated on `FULLY_RESOLVING`, **the run was
structurally incapable of producing a null.** Every sub-floor result had exactly two reachable
destinations: `UNPOWERED` or `NOT_RESOLVABLE_AT_THIS_FLOOR`. That is the mechanism behind the
operator's observation that it "fails on all grounds": there were no other grounds available.

---

## 4. Defect 3 — a power constant used as a test threshold, beside a bootstrap SE it ignores

### 4.1 `2.8` is a sample-size target, not a significance bar

`MDE_Z = 2.8 ≈ z₀.₉₇₅ + z₀.₈₀`. That constant answers *"how many observations do I need for 80%
power at 5%?"* The band rule instead used it as a pass mark on the realised estimate:

```python
clears_floor = abs(estimate) >= mde          # the withdrawn band_label
```

which demands `|est| ≥ 2.8 · SE`, against `1.96 · SE` for the 95% interval printed on the same row —
a **1.43× stricter bar than the run's own interval**, applied silently.

Counted over POOLED × PRIMARY × governing rows:

| Cell | rows | CI excludes 0 | also clears MDE | **demoted to `DIRECTION_RESOLVED_MAGNITUDE_UNRESOLVED`** |
|---|---:|---:|---:|---:|
| crypto H1 | 29 | 9 | 6 | 3 |
| crypto H4 | 29 | 5 | 0 | **5** |
| cTrader H1 | 29 | 3 | 0 | **3** |
| cTrader H4 | 29 | 0 | 0 | 0 |
| **total** | 116 | **17** | **6** | **11** |

**11 of 17 results that clear the run's own 95% interval were demoted by that constant alone.** The
`DIRECTION_RESOLVED_MAGNITUDE_UNRESOLVED` band is not, as `analysis.md` §3.2 and the design's
DIRECTION-vs-MAGNITUDE clause imply, a subtle epistemic distinction the apparatus discovered. It is
mostly the numerical gap between 1.96 and 2.8.

### 4.2 The floor ignores the standard error the module measures

`clustered_interval` runs a 2,000-draw symbol-clustered block bootstrap and returns real interval
bounds. The floor on the same row is then computed parametrically as `2.8/√effective_blocks`
(`:392`), i.e. it *asserts* `SE = 1/√blocks` rather than using the SE it just measured.

Implied bootstrap SE (`(ci_high − ci_low)/3.92`) against the parametric SE (`mde_sigma/2.8`), over
all POOLED rows with a finite interval (87 per cell):

| Cell | ratio min | **median** | max | parametric floor (median) | floor if built on bootstrap SE |
|---|---:|---:|---:|---:|---:|
| crypto H1 | 1.03 | **1.25** | 1.70 | 0.0457 | 0.0589 |
| crypto H4 | 0.89 | **1.17** | 1.54 | 0.0955 | 0.1087 |
| cTrader H1 | 0.77 | **1.20** | 1.80 | 0.0978 | 0.1070 |
| cTrader H4 | 0.71 | **1.03** | 1.41 | 0.1888 | 0.1841 |

The two disagree by up to 1.8× within a single cell, in both directions. **One row is banded by two
different uncertainty scales at once**: a floor that credits every block as exactly `1/√n`
independent, against an interval that does not. Note the direction — the parametric floor is
*optimistic* by ~20% in three cells, so the defect is not simply excess conservatism; it is
incoherence.

### 4.3 The conservatism stack, for completeness

Legitimate, but it lands on top of §2–§4.2. crypto H1, the best cell:

| stratum | V-A unchunked | V-B time block | V-C regime episode (governs) |
|---|---:|---:|---:|
| ALL | 8,469 blk / **0.0304** | 5,796 / 0.0368 | 5,058 / **0.0394** |
| HIGH | 4,639 / 0.0411 | 3,421 / 0.0479 | 2,820 / **0.0527** |
| LOW | 3,736 / 0.0458 | 2,942 / 0.0516 | 2,308 / **0.0583** |

Most-conservative-treatment selection: **×1.30**. Regime split: a further **×1.34**. Combined
**×1.73** from the raw V-A ALL floor. Against a ceiling of 0.0342, the HIGH-stratum floor of 0.0527
is 1.54× the largest effect the estimand can generate in that cell.

---

## 5. Defect 4 — two channels, two σ̂ units, one ladder

The two channels normalise by different objects:

- **Scale channel** — σ̂ is the standard deviation of the **paired difference**
  (`SymbolSeries.sigma`, `:392` path).
- **Selection channel** — σ̂ is the standard deviation of the **outcome level**, pooled across
  admitted and declined (`_pooled_sigma`, `:958`).

These are not the same size:

| Cell | scale-channel σ̂ (paired delta) | selection-channel σ̂ (outcome level) | **ratio** |
|---|---:|---:|---:|
| crypto H1 | 64.4 bps | 147.5 bps | **2.3×** |
| cTrader H1 | 6.7 bps | 27.1 bps | **4.0×** |
| crypto H4 | 75.0 bps | 273.7 bps | **3.7×** |
| cTrader H4 | 20.9 bps | 46.9 bps | **2.2×** |

Both were then banded through the same `0.022–0.150` ladder, and `_selection_band`'s docstring
recorded this as a virtue — *"so this channel and the scale channel share one standard"*. They share
a **number**, not a standard. In raw basis points the selection channel is held to a bar 2.2–4.0×
stricter than the scale channel, purely because its denominator is a level rather than a difference.

This is a material part of why **all 96 selection contrasts failed and no scale arm did**. It is the
same class of defect as **L-50 / P-21** (importing an absolute bar across universes silently loosened
a threshold 5.6×) — which `design.md:468` explicitly invokes as the reason MDE is declared in σ̂ units
in the first place. Declaring in σ̂ does not help when σ̂ denotes two different objects.

---

## 6. Defect 5 — the pre-execution gate and the post-execution ladder used different standards

`design.md:493` (M2) requires cells that cannot reach `est/MDE > 1` to be marked **DESCRIPTIVE before
execution**. It ran. It passed all four:

| Cell | preflight floor | label | basis | **realised floor** |
|---|---:|---|---|---:|
| crypto H1 | 0.0317 | `CARRIES_MAGNITUDE_QUESTION` | 26,849 orders created | 0.0394 |
| crypto H4 | 0.0638 | `CARRIES_MAGNITUDE_QUESTION` | 6,348 | 0.0807 |
| cTrader H1 | 0.0646 | `CARRIES_MAGNITUDE_QUESTION` | 5,738 | 0.0842 |
| cTrader H4 | **0.1261** | `CARRIES_MAGNITUDE_QUESTION` | 1,647 — **491 actually filled** | **0.1639** |

Two independent failures:

**(a) The gate counted orders created, not fills.** Fill rate is 7.4–9.0%, and `P1_pooled`'s own
`count_basis` field says so:

> *"STOP ORDERS CREATED. Fills are a subset, so every MDE below is OPTIMISTIC against the realised
> sample; the realised MDE is recomputed post-execution from filled trades."*

It flagged itself (`power_label_basis: ORDERS_NOT_FILLS_TREAT_AS_UPPER_BOUND`) and passed the cell
anyway. An acknowledged upper bound used as a gate value is not a gate.

**(b) The gate tested against the top of the range (0.150); the ladder tests against the bottom
(0.022).** This is the exact defect AMENDMENT-5 corrected in `band_label` (`design.md:650`) — and it
was corrected in the band rule only, never in the preflight gate. So the screen that exists to stop
blind cells before execution passed a cell (`cTrader H4`, realised 0.1639) that the corrected ladder
then declared blind after execution. **The apparatus contradicts itself across the execution
boundary, and the contradiction is why the run spent budget on a cell it had already established it
could not read.**

---

## 7. Why the failure is universal rather than selective

Each defect on its own would leave some reads standing. Composed, they close every exit:

```
ceiling of the estimand      ~0.032 - 0.059 sigma-hat      (Defect 1, arithmetic)
floor demanded               2.8 / sqrt(blocks)            (Defect 3, a power target)
   x1.30 most-conservative treatment
   x1.34 regime split
yardstick                    0.022 - 0.150 sigma-hat       (Defect 2, unresolved estimates)
   -> FULLY_RESOLVING unreachable  -> WASH unreachable  -> no null is expressible
selection channel            same numbers, denominator 2-4x larger  (Defect 4)
pre-run gate                 tested a different endpoint, on inflated counts (Defect 5)
```

With `WASH` unreachable, the label set reduces to {`UNPOWERED`, `NOT_RESOLVABLE_AT_THIS_FLOOR`,
`DIRECTION_RESOLVED…`, `MAGNITUDE_RESOLVED…`, `SUPPORTED`, `CONTRADICTED`}, and the last four require
clearing a floor that sits above the estimand's ceiling in three of four cells. The run's own
headline — *"Most of this run cannot resolve most of what it measured"* (`analysis.md` §0) — is
therefore a statement about the apparatus, and it was true before any data was loaded.

---

## 8. Code state as of 2026-08-07 05:12

`spdr024_analysis.py` was edited during the investigation session. Current state, verified:

**Withdrawn** — `band_label`, `resolution_class`, `_selection_band`, `_resolution_fields`,
`MIN_TRADES_FOR_POWER`, and the emitted `band` / `governing_band` / `component_specific_band` /
`resolution_class` / `floor_over_*` columns. The withdrawal note at `:411–426` grounds this in
`adaptive-management-design.md` §1/§9 — power must not decide how a row is *described*. That removes
**Defect 2's labelling arm and Defect 3.1's demotion mechanism**, and is the correct call
independently of anything in this document.

**Surviving unchanged, and not addressed by that edit:**

| Defect | Status | Anchor |
|---|---|---|
| 1 — estimand ceiling = per-trade Sharpe, never computed | **open** | mechanism; nothing in code |
| 2 — `0.022 / 0.150` yardstick | constants now **dead but still declared** | `:36–37` |
| 3.2 — floor asserts `SE = 1/√blocks`, ignores the bootstrap SE beside it | **open** | `:392`, `:611`, `:1103` |
| 4 — two σ̂ denominators, one numeric scale | **open** | `SymbolSeries.sigma` vs `_pooled_sigma` `:958` |
| 5 — preflight gate on orders, tested at the wrong endpoint | **open** | `results/preflight/*.json` |

`mde_sigma`, `mde_bps` and `contrast_over_mde` are still emitted on every row, still computed from
`MDE_Z / √blocks`. A reader told to "compare the estimate with its own MDE" is still comparing
against an incoherent floor. **Removing the labels removes the automatic misreading, not the
defect.**

---

## 9. What this does and does not license

**Does:**

- SPDR-024's resolution labels — `UNPOWERED`, `NOT_RESOLVABLE_AT_THIS_FLOOR`, and the
  direction/magnitude split — are unreliable **in both directions** and should not be carried
  forward as either evidence or as a power finding.
- `analysis.md` §4's claim that the selection channel result is *"a first-class result about the
  apparatus"* is correct in spirit and wrong in attribution: it is a result about **this analyser's
  floor construction**, not about the substrate's capacity to answer the selection question.
- `analysis.md` §1's table (*"floor ÷ weakest observed effect: 1.8×–7.5×"*) uses a denominator
  (0.022) that no cell could reach and that is itself a noise minimum. The honest denominator is the
  estimand's own ceiling, giving 1.15×–2.79× — smaller ratios, but ones that mean something.

**Does not:**

- This says nothing about whether volatility-state sizing works. Defect 1 in particular is
  symmetric: the apparatus could not have detected the effect *or* ruled it out.
- No SPDR-024 number is retracted. The estimates, intervals, counts, the exposure/selectivity
  decomposition, the gate-permutation control and the identity attestations are unaffected — only
  the floor they were judged against.
- No re-run is implied by this document. §10 is a proposal, not a decision.

---

## 10. Remedies, ordered by how much of the gap each closes

**R1 — derive the reference magnitude from the mechanism, not from prior unresolved estimates.**
For a SIZE device the ceiling is `√(gate_rate) × baseline per-trade Sharpe`, computable from a
baseline-only pass before any arm runs. Declare it per cell. If the floor exceeds it, the cell is
DESCRIPTIVE and does not run. This alone would have caught three of four cells at design time.
Retire `STEP3_OBSERVED_EFFECT_SIGMA_MIN/MAX`.

**R2 — build the floor from the measured SE.** `mde = MDE_Z × SE_bootstrap`, using the interval the
module already computes. Delete the `2.8/√blocks` assertion at `:392` / `:611`. Keeps one uncertainty
scale per row.

**R3 — separate the power target from the reporting threshold.** Keep `2.8` for sizing the *next*
run. Report `estimate / SE` and the interval for *this* one. Never compare a realised estimate to an
80%-power constant.

**R4 — one denominator per comparison, declared.** Either give each channel its own mechanism-derived
reference scale, or express both channels in raw bps against a single stated σ. Do not let the word
σ̂ carry two objects.

**R5 — fix the preflight gate.** Count fills (or apply the realised fill rate to orders), and test
against the same endpoint the post-run report will use. A gate whose own artifact calls its input an
optimistic upper bound must not return a pass.

R2/R3/R5 are mechanical. R1/R4 are design changes and belong in the next design, not in a patch to
this one.

---

## 11. Reproduction

Run from `python/` with the project venv. Reads only emitted artifacts.

```python
import polars as pl, numpy as np, json

CELLS = ['crypto_H1', 'crypto_H4', 'ctrader_H1', 'ctrader_H4']
# baseline gross mean / sigma, from baseline_characterisation.parquet (analysis.md §2)
BASE = {'crypto_H1': (5.20583, 152.3), 'crypto_H4': (-8.80, 272.2),
        'ctrader_H1': (1.09881, 27.0), 'ctrader_H4': (-2.48, 42.2)}
root = 'experiments/SPDR-024/results/analysis'

# §2.2 ceiling identity
for cell, (m, s) in BASE.items():
    d = pl.read_parquet(f'{root}/{cell}/scale_channel_estimates.parquet')
    p = d.filter((pl.col('scope') == 'POOLED')
                 & (pl.col('lens') == 'PRIMARY_capital_normalised')
                 & (pl.col('regime') == 'ALL') & pl.col('governs')).drop_nulls('gate_rate')
    sharpe = abs(m) / s
    print(cell, 'sharpe', round(sharpe, 4),
          'pred_med', round(float((p['gate_rate'].sqrt() * sharpe).median()), 4),
          'obs_max', round(float(p['estimate_sigma'].abs().max()), 4),
          'floor', round(float(p['mde_sigma'].median()), 4))

# §4.2 bootstrap SE vs parametric SE
for cell in CELLS:
    d = pl.read_parquet(f'{root}/{cell}/scale_channel_estimates.parquet').filter(
        (pl.col('scope') == 'POOLED') & pl.col('ci_low_sigma').is_finite()
        & pl.col('mde_sigma').is_finite())
    r = ((d['ci_high_sigma'] - d['ci_low_sigma']) / 3.92) / (d['mde_sigma'] / 2.8)
    print(cell, 'SE ratio min/med/max',
          round(float(r.min()), 2), round(float(r.median()), 2), round(float(r.max()), 2))

# §4.1 demotions by the 2.8 constant
for cell in CELLS:
    d = pl.read_parquet(f'{root}/{cell}/scale_channel_estimates.parquet').filter(
        (pl.col('scope') == 'POOLED') & (pl.col('lens') == 'PRIMARY_capital_normalised')
        & pl.col('governs') & pl.col('ci_low_sigma').is_finite())
    excl = (pl.col('ci_low_sigma') > 0) | (pl.col('ci_high_sigma') < 0)
    clears = pl.col('estimate_sigma').abs() >= pl.col('mde_sigma')
    print(cell, 'rows', d.height, 'ci_excl_0', d.filter(excl).height,
          'clears', d.filter(excl & clears).height,
          'demoted', d.filter(excl & ~clears).height)

# §5 cross-channel sigma-hat denominators
for cell in CELLS:
    sc = pl.read_parquet(f'{root}/{cell}/scale_channel_estimates.parquet').filter(
        (pl.col('scope') == 'POOLED') & (pl.col('lens') == 'PRIMARY_capital_normalised')
        & (pl.col('regime') == 'ALL') & pl.col('governs'))
    imp = (sc['mean_delta_raw'] / sc['estimate_sigma']).abs()
    imp = imp.filter((imp > 1) & (imp < 1000))          # drop near-zero-estimate blowups
    se = pl.read_parquet(f'{root}/{cell}/selection_channel_estimates.parquet').filter(
        pl.col('scope') == 'POOLED')['pooled_sigma_bps'].median()
    print(cell, 'scale sigma', round(float(imp.median()), 1),
          'selection sigma', round(float(se), 1), 'ratio', round(se / float(imp.median()), 1))

# §6 preflight
for cell in CELLS:
    j = json.load(open(f'experiments/SPDR-024/results/preflight/{cell}.json'))['P1_pooled']
    print(cell, j['n_orders_created'], round(j['most_conservative_mde_sigma'], 4), j['power_label'])
```

---

## Appendix — line anchors

| What | Where |
|---|---|
| `MDE_Z = 2.8` | `python/src/xen/adaptive_management/spdr024_analysis.py:31` |
| `STEP3_OBSERVED_EFFECT_SIGMA_MAX / MIN` | `:36`, `:37` |
| `mde_sigma = MDE_Z / sqrt(effective_blocks)` | `:392` (pooled), `:611` (per-symbol) |
| `governing_treatment` — highest floor wins | `:429` |
| Label withdrawal note | `:411–426` |
| `_two_sample_mde` (selection channel floor) | `:1081–1103` |
| `_selection_band` withdrawal note | `:1106–1114` |
| `_pooled_sigma` (selection σ̂ denominator) | `:958` |
| Power block, MDE declared in σ̂, L-50/P-21 rationale | `python/experiments/SPDR-024/design.md:468–479` |
| M2 pre-execution DESCRIPTIVE gate | `design.md:493` |
| Resolution ladder | `design.md:507–517` |
| Step-3 range described as magnitude-**unresolved** | `design.md:538` |
| AMENDMENT-5 top-of-range correction (band rule only) | `design.md:650–651` |
| P-1: §10 figures are SPDR-021-derived design-time estimates | `design.md:691` |

---

## 12. Independent validation (2026-08-07) — claims checked against artefacts and code

**Scope.** A second pass re-ran the reproduction logic in §11 against the live parquet/JSON under
`python/experiments/SPDR-024/results/` and the live sources `spdr024_analysis.py`,
`screen_code/preflight.py`, and `design.md`. No engine cell was re-executed for this section.
This section does **not** re-open the candidate hypothesis; it grades the defect document only.

### 12.1 Quantitative claims — reproduced

| Claim (defect doc) | Result | Note |
|---|---|---|
| Ceiling identity table (§2.2): Sharpe, predicted median, obs max, median floor | **Match** | All four cells to the printed digits |
| Max / p90 / median \|est\| vs median floor, all regimes, POOLED PRIMARY governing | **Match** | 29 rows/cell; three cells have median floor > cell max \|est\| |
| Blocks needed / shortfall table (§2.3) | **Match** | 1.3× / 6.2× / 4.3× / 7.8× |
| CI-excludes-0 vs clears-MDE demotions (§4.1): 17 / 6 / 11 | **Match** | Per-cell 9·6·3 / 5·0·5 / 3·0·3 / 0·0·0 |
| Bootstrap SE / parametric SE ratios (§4.2) | **Match** | medians 1.25 / 1.17 / 1.20 / 1.03 |
| Cross-channel σ̂ denominators (§5) | **Match** | ratios 2.3 / 3.7 / 4.0 / 2.2 |
| Preflight P1_pooled floors, order counts, `CARRIES_MAGNITUDE_QUESTION` (§6) | **Match** | All four cells; count basis = orders, self-flagged optimistic |
| Code anchors: `MDE_Z`, `mde_sigma = 2.8/√blocks`, label withdrawal, `_pooled_sigma`, `_two_sample_mde` | **Match** | Live line numbers may drift; symbols and formulae hold |

### 12.2 Verdict per defect

| # | Defect | Verdict | Soft edges (do not reverse the verdict) |
|---|---|---|---|
| **1** | Estimand ceiling ≈ √(gate) × baseline per-trade Sharpe; floor and effect on incompatible scales | **PROVEN — structural** | Soft ceiling, not a hard law. Observed max is often 1.5–2.8× the simple `√gate × Sharpe` prediction (selectivity, `E[y\|gate] ≠ E[y]`, continuous size can exceed 1, per-symbol normalise-then-pool). The **order of magnitude** and the floor-above-ceiling arithmetic in 3/4 cells still stand. Continuous SCALE arms are not pure gate×halve devices. |
| **2** | Yardstick 0.022–0.150 is Step-3’s own unresolved point-estimate range; WASH/null unreachable under the old ladder | **PROVEN — for the labelled apparatus; partially mitigated** | Band / resolution-class columns are **withdrawn** in the live analyser (AMENDMENT-6). Constants remain as “reader context.” Informal reads that still compare estimate to MDE against that range remain exposed. “Structurally incapable of a null” applied to the **old** WASH gate, not to the post-withdrawal emission. |
| **3.1** | `2.8` used as a pass mark on realised estimates (stricter than the row’s own 95% interval) | **PROVEN** | Empirically 11/17 CI-excluding rows fail MDE. Because parametric SE ≠ bootstrap SE, the gap is not *only* 2.8 vs 1.96 — but the demotion count is real either way. |
| **3.2** | Floor asserts `SE = 1/√blocks` and ignores the bootstrap SE on the same row | **PROVEN** | Code path `:392` / per-symbol path; SE-ratio table reproduced. Defect is **incoherence**, not pure excess conservatism (parametric floor is optimistic by ~20% in three cells). |
| **4** | Scale and selection normalise by different objects, then share one numeric ladder | **PROVEN** | Denominator ratios 2.2–4.0×. Contributes materially to “0/96 selection vs some scale clears”; not the only reason selection sits below its floor (two-sample split, block counts). |
| **5** | Preflight gate on orders + top-of-range endpoint; post-run ladder used a different standard | **PROVEN** | Artefacts match. cTrader H4: preflight 0.126 pass on 1,647 orders → realised floor 0.164 on 491 fills. After label withdrawal, `preflight.py` still imports `STEP3_OBSERVED_EFFECT_SIGMA` / `MIN_TRADES_FOR_POWER` that the cleaned analyser module no longer exports — script/module inconsistency; preflight **JSON** remains valid history of the broken gate. |

### 12.3 What the validation does and does not license (alignment with §9)

**Does (confirmed):**

- Resolution labels and “\|est\| ≥ MDE ⇒ resolved / else unreadable” as used in the SPDR-024 cycle are
  **unreliable in both directions** and must not be carried forward as power findings or as evidence.
- Selection’s universal “below floor” is substantially a statement about **this floor construction**,
  not a clean powered null on admission quality.
- Point estimates, bootstrap intervals, exposure/selectivity decomposition, gate-permutation control,
  baseline characterisation, and the paired-difference identity are **not** invalidated by these
  defects.

**Does not (confirmed):**

- Does **not** prove or refute volatility-state sizing or selection on this substrate.
- Does **not** retract SPDR-024 gross estimates.
- Does **not** make a prose “rewalk” of the old artefacts an adequate remedy: the floor is still
  emitted on every row; any read that treats MDE as the detection standard re-imports the defect.

### 12.4 Implication for how SPDR-024 may be read until fixed

| Object | Trust for operator interpretation |
|---|---|
| Baseline levels, fill rates, hold geometry | **Us** |
| Scale/selection **point estimates** and **bootstrap CIs** | **Use** |
| Exposure vs selectivity terms; gate-permutation | **Use** (mechanism-native) |
| Future-shift tripwire HARD pass / non-collapse fractions | **Use as integrity, not as edge proof** |
| `mde_sigma` / `mde_bps` / `contrast_over_mde` as resolve/unresolve | **Do not use** until R1–R5 are implemented and re-emitted |
| Preflight `CARRIES_MAGNITUDE_QUESTION` | **Do not use** |
| Informal “only crypto H1 can see anything” as a substrate power finding | **Withdraw** — partly apparatus |

A patch-job re-interpretation of the existing emission (CI-only narrative on the old parquet) is
explicitly **rejected** as the disposition of this defect set. See §13.

---

## 13. OPERATOR DECISION — clean fix, artefact purge, full re-emission (binding)

**Date:** 2026-08-07  
**Authority:** operator  
**Disposition of this defect set:** not a documentation footnote and not a rewalk of the current
`analysis.md`. The MDE / resolution apparatus is treated as **broken end-to-end**. The only
accepted remedy is a design-level correction, a matching implementation, a full purge of generated
artefacts that embed the broken floor, and a full re-run + re-analysis that re-emits every dependent
record.

### 13.1 Decision (operative)

1. **Reject** any “rewalk” or operator narrative that re-labels the existing SPDR-024 analysis
   artefacts in place (CI-only commentary, hand demotion tables, partial re-banding). That path
   leaves `mde_*` columns and preflight power labels in the tree and invites the next session to
   re-import the defect.
2. **Require a complete fix from design through implementation**, implementing remedies **R1–R5**
   in §10 as a single coherent amendment — not a silent code patch under the old §10/§11 text.
3. **Require a clean removal** of all generated SPDR-024 artefacts that depend on the broken floor
   or on the preflight gate that used it (scope in §13.3).
4. **Require a full re-run** of the SPDR-024 screen/engine path for all four cells, then a full
   re-analysis and a replacement `analysis.md` / `screen.md` (and any summary JSON) produced only
   from the new emission.
5. **Until that cycle completes**, SPDR-024 is **not** in a state where MDE-based resolution claims
   may be used for family disposition, XENA gating, or “powered null” language on either channel.

### 13.2 Design amendments that must land before code (binding content)

Carry into `python/experiments/SPDR-024/design.md` as a numbered amendment (direction: **TIGHTER**
on honesty of power; **NEUTRAL** on admission/threshold of the strategy itself):

| Remedy | Design change required |
|---|---|
| **R1** | Retire `STEP3_OBSERVED_EFFECT_SIGMA_MIN/MAX` (0.022 / 0.150) as a resolution or preflight yardstick. Declare per cell a **mechanism-derived SIZE ceiling**: `√(gate_rate) × \|baseline mean / baseline σ\|` (or the design’s frozen equivalent), computable from a baseline-only pass. If the planned floor exceeds that ceiling under the governing treatment, the cell is **DESCRIPTIVE for SIZE magnitude** before arms run. Step-3’s 0.022–0.150 range may remain historical context only, never a gate. |
| **R2** | Detection floor on each row must use the **same uncertainty object as the interval**: `mde = MDE_Z × SE_bootstrap` (or the explicit SE implied by the governing clustered interval). Delete the free-standing `2.8 / √effective_blocks` assertion as the row’s floor. |
| **R3** | `MDE_Z = 2.8` is a **sample-size planning constant for the next design**, not a pass mark on a realised estimate. Reporting uses estimate, CI, population counts, effective counts, and (if retained) est/SE. No band, no “clears floor” label, no demotion class. |
| **R4** | Scale and selection must not share one σ̂ ladder built on different denominators. Either each channel has its own declared mechanism scale, or both are reported in raw bps with one stated dispersion — **declared in the design**, not only in code comments. |
| **R5** | Preflight M2 gate: count **fills** (or apply a measured fill rate to orders with the result labelled as still provisional), and test against the **same endpoint** the post-run report will use (mechanism ceiling / descriptive rule from R1). A gate whose own artefact calls its input an optimistic upper bound must not return a magnitude-carrying pass. |

Power remains **context only** under `adaptive-management-design.md` §1/§9: no result labels return.

### 13.3 Implementation and purge scope

**Code (non-exhaustive; implementer owns the full touch list):**

- `python/src/xen/adaptive_management/spdr024_analysis.py` — floor construction, any dead Step-3
  constants, selection MDE path, docstring contracts.
- `python/experiments/SPDR-024/screen_code/preflight.py` — fill-based counts, endpoint alignment,
  remove imports of withdrawn symbols.
- Tests under `python/tests/` that lock the new floor contract and forbid reintroduction of
  power labels.
- `python/experiments/SPDR-024/design.md` amendment ledger + §10/§11 text.
- `python/experiments/SPDR-024/implementation-notes.md` — record the defect doc path and this
  decision.

**Artefacts to remove before re-run (generated only; do not delete design/source):**

```text
python/experiments/SPDR-024/results/          # entire tree (preflight, runs, selfcheck,
                                              # analysis, logs, performance, estimand_*, etc.)
python/experiments/SPDR-024/analysis.md       # regenerated after re-analysis only
python/experiments/SPDR-024/screen.md         # regenerated after re-screen only
python/experiments/SPDR-024/plots/            # if present and generated
```

Retain: `design.md`, `implementation-notes.md`, `screen_code/`, `analysis_code/`, and this defect
document. After purge, no consumer should be able to open a stale `mde_sigma` from the prior cycle.

### 13.4 Re-run and re-analysis sequence (mandatory order)

```text
1. Land design amendment (R1–R5) and get operator sign-off if the ledger requires it.
2. Land implementation + unit tests; no result labels.
3. Purge §13.3 paths.
4. Preflight all four cells under the new gate (fills / mechanism ceiling).
5. Full engine screen for all four cells (self-check, estimand validation, tripwires).
6. Full analysis emission for all four cells.
7. Replace analysis.md / screen.md from the new artefacts only.
8. Record in implementation-notes.md: old emission superseded; cite this document §12–§13.
```

No partial cell keep, no “reuse old scale parquet with new labels,” no analysis-only refresh on
old engine output if the floor or preflight inputs changed the admission of cells.

### 13.5 Success criteria for the new cycle (not a hypothesis verdict)

The new cycle is accepted as a **fixed apparatus** when all of the following hold:

1. Every estimate row’s floor (if emitted) is derived from the **same SE family** as its CI (R2).
2. No preflight pass is based on order counts alone or on 0.022/0.150 as a gate (R1, R5).
3. No emitted column classifies a row by power (R3; AMENDMENT-6 preserved).
4. Scale and selection do not share an undeclared dual-σ̂ ladder (R4).
5. `analysis.md` does not use “\|est\| ≥ MDE” as a resolve/unresolve rule; MDE/power is context.
6. Golden / unit tests cover the new floor contract and the ban on label columns.

Hypothesis support/refute remains out of scope for this decision, as for the rest of this document.

### 13.6 Explicit non-goals

- No family disposition, no XENA gate, no arm ranking from this decision alone.
- No claim that fixing the floor will create a positive sizing result (Defect 1 is symmetric).
- No TEST/holdout access; TRAIN-only remains binding for SPDR-024 unless a separate operator
  decision opens it.

**End of operator decision.**

**Execution ledger (not started until operator says go):**  
`docs/superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md`
