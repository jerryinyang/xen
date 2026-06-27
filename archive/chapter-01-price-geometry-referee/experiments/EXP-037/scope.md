# Experiment: EXP-037 — `/EXIT-FH` Fixed-Horizon-Exit Capture-Efficiency Variant (4h, one-shot TEST)

**Registry ID:** `CF-AVWAP-001/EXIT-FH` (Tier-B registered variant; **1 candidate
slot**, activated 2026-06-10 on G1-B2 qualification).
**Phase:** 008 (`docs/experiments-docs/checkpoints/2026-06-10-008-avwap-clinical-tradability/design.md`, §5/B2, §8.3, §8.4).
**Gate provenance:** G1-B2 qualified 4h only (EXP-033 TRAIN FH grid max +45.79 bps > 0;
`G1-gate-review.md`). 5m/1h NOT eligible (grid maxima ≤ 0) — out of scope here.
**Depends on:** EXP-033 (TRAIN FH(H) curve, pyramid-policy menu, H\* fragility
disclosure), EXP-030 (frozen cost model), EXP-034/D0 (financing layer), EXP-027
(frozen inference tail), EXP-022/020 (event population + triggers).
**Revision R1 (2026-06-10, pre-execution, before any TEST read — design §11):**
binding multiplicity moved to the phase-level Holm family (R1.1); binding bound
margin from a pre-TEST synthetic-null calibration (R1.2); binding stratum boundary
unified to the 1-minute-row timestamp (R1.3); the H\* tie-break recorded as a
design amendment and labeled second-generation data-dependent (R1.4); tie-break
computed on the spill-contained TRAIN subset (R1.5); pre-freeze feasibility and
freeze-recovery semantics added (R1.6).

## Hypothesis

On the **4h domain**, replacing the band-target/trend-change (BTC) exit with a
fixed-horizon exit at a single TRAIN-frozen horizon H\* (pyramid policy TRAIN-frozen)
yields positive **net** per-event expectancy (absolute estimand, frozen CONSERVATIVE
costs + financing) that survives a **one-shot TEST-stratum** confirmation with
**Holm across the phase-level G2 family** (design §8.4/R1.1: the 3 cells here plus
EXP-038's single cell — all realized binding TEST p-values of Phase 008).

## Question

Does the disclosed 4h capture-efficiency headroom (BTC-exit matched-control drag
−27 bps, EXP-031) convert into a net-positive, TEST-stratum-confirmed exit variant —
or is the H\* selection too fragile (EXP-033 `h_star_stable = false`) to carry a TEST
read?

## TRAIN/TEST discipline (LOCKED — design §3, §7.3)

Nested split inside the **analysis set** (first 70% of full data; global holdout =
final 30%, never touched):

- **TRAIN** = first 70% of the analysis set. All selection (H\*, pyramid policy)
  happens here, by the mechanical predeclared rules below, and is **frozen before any
  TEST read**.
- **TEST** = last 30% of the analysis set. Evaluated **exactly once**, at the single
  frozen H\* and frozen pyramid policy. Honest caveat (design §3): aggregate
  full-analysis 4h results are known from EXP-028/030/031, but this per-instrument
  TEST-stratum FH-variant read is fresh.
- **Stratum membership (predeclared, causal; R1.3 unified convention):** the
  boundary is the **CloseTime of the last TRAIN 1-minute analysis row**
  (`train_rows = int(analysis_rows × 0.7)`, the shared loader's `train_end_ts`),
  per instrument. An event is **TEST iff its entry-confirmation (trigger) close
  time > boundary**; ties → TRAIN — identical to EXP-038, so the phase has exactly
  one operationalization of "TEST = last 30%". Known at entry, no look-ahead. An
  event's full FH(H\*) lifetime may extend past the stratum boundary; that is
  allowed for the binding TEST estimand (the membership key is the entry bar). The
  membership divergence vs the EXP-033 bar-index convention is disclosed per cell
  (transparency only; the bar-index rule survives solely inside guard 1's EXP-033
  reproduction anchor).

## H\* selection — TRAIN tie-break (PREDECLARED, mechanical, frozen before TEST)

Operator decision 2026-06-10: a TRAIN-only robustness tie-break over a bounded
neighborhood, resolving to **one** binding H\* on TEST (no multi-horizon TEST looks).
**Authorization and provenance (R1.4):** this rule **replaced** the design's
original §5/B2 mechanism (A2's one-SE pick, H\*=8) **after** EXP-033 disclosed
`h_star_stable = false`, the full N(H) curve, and the split-half argmaxes — it is
recorded as a design amendment (design §11/R1.4) and labeled **second-generation
data-dependent** in the multiplicity registry. It remains mechanical and
TRAIN-only.

1. **Candidate set:** H ∈ {4, 6, 8, 12} domain bars (neighborhood of EXP-033's
   one-SE pick H\*=8; bounded to keep holds short → less financing).
2. **Selection population (R1.5 — spill containment):** the tie-break is computed
   on the **contained TRAIN subset** — TRAIN events whose FH window at the grid
   maximum H = 12 exits at or before the boundary timestamp (constant population
   across candidate H, mirroring EXP-033/F08). Boundary-spill events are
   **excluded from selection** and their count disclosed, so no TEST-window price
   enters the freeze. Binding TEST population and TRAIN/TEST membership are
   unchanged. For each candidate H, compute on this subset under frozen costs +
   financing, pyramid policy = all_legs: full net `N(H)` and both chronological
   split-half nets `N₁(H)`, `N₂(H)`.
3. **Stability filter (directly targets the EXP-033 fragility):** retain H only if
   `N(H) > 0` AND `N₁(H) > 0` AND `N₂(H) > 0` (positive in full TRAIN and both halves).
4. **Selection:** among retained H, `H* = argmax_H min(N₁(H), N₂(H))` (worst-half /
   max-min robust criterion); ties broken toward the **smaller H** (less financing).
5. **Empty-set rule:** if no H passes step 3, EXP-037 produces **no binding TEST read**
   — recorded as `B2_NO_ROBUST_HSTAR`, the Tier-B slot is consumed but the holdout is
   not advanced through B2 (G2 must then route through EXP-038). This is a possible,
   honest outcome given the disclosed fragility.

The `s_entry(H)` attribution map never enters H\* selection. The full {4,6,8,12}
TRAIN net table (full + both halves) is disclosed regardless of the pick.

## Pyramid policy — TRAIN-frozen (PREDECLARED)

Policy ∈ {all_legs, first_leg_only, pyramid_legs_only}, selected per the EXP-033
one-SE rule on contained-TRAIN net at the chosen H\* (simplicity-preference order
all_legs → first_leg_only → pyramid_legs_only on ties). EXP-033 disclosed
`policy_stable = true` with all_legs selected at H\*=8; recomputed at the tie-break
H\* and frozen before TEST. (Subsumes the "no-pyramid" idea — blanket drop is
contradicted on 4h, D0 §2.)
**Pre-freeze feasibility (R1.6):** a policy is a selection candidate only if it
keeps **every TEST cell non-empty**, checked from entry attributes only
(`is_pyramid_bounce` composition of the TEST stratum — no TEST outcome is read).
This removes the post-freeze hard-stop ambiguity of an empty TEST cell.

## Pre-TEST null calibration and binding margin (R1.2, PREDECLARED)

The frozen EXP-027 bootstrap has never been Type-I-calibrated at ~11–13-event
single cells. Before the freeze, run a **synthetic-null calibration** per declared
cell (no TEST-outcome contact): cluster sizes and direction labels = the TEST
stratum's entry attributes under the frozen policy; null returns from a zero-mean
Gaussian cluster model with between/within variance components estimated from the
contained-TRAIN nets at H\* (method of moments, per analysis plan); R = 2000 null
replicates, each scored by the frozen 1000-resample bootstrap. Persist (before the
freeze) the measured null FPR of the uncorrected rule and the **binding margin**
`m_cell = max(0, Q95 of null ci_low_1s)`. The binding bound rule is
**`ci_low_1s > m_cell`** (identical to `> 0` when the cell is not
anti-conservative). Margins are frozen inside `frozen_selection.json`; no
post-result iteration.

## Recovery semantics (R1.6, PREDECLARED)

If execution halts **after** `frozen_selection.json` is written but **before**
`test_verdicts.csv` exists, a rerun is **not** a second TEST read. The rerun must
reproduce the existing freeze record exactly (content-hash assert; hard stop on
mismatch). Any run that finds an existing `test_verdicts.csv` must refuse to
recompute TEST inference (structural no-second-read guard).

## Scope Boundaries

- **Data Views:** EXP-022 `results/lifetime_observations.csv` (`role = event`,
  `reportable_event = true` — the EXP-028/030 PRIMARY population, pyramids included);
  EXP-020 `results/avwap_events.csv` triggers; rebuilt 4h domain series
  (EXP-031-identical rebuild) for FH(H) exit-bar prices and stratum timestamps.
- **Instruments (declared 4h TEST family):** EURUSD, USTEC, XAUUSD. **BTCUSD excluded**
  (break-even map, D0 §3 — its 16 bps RT exceeds every gross figure). Holm across the
  **3** tested 4h cells.
- **Parameters (all FROZEN before measurement):**
  - RT costs, CONSERVATIVE: EURUSD 3.0 / USTEC 5.0 / XAUUSD 6.0 bps (EXP-030,
    unchanged). BTCUSD not tested.
  - Financing, adverse-side, per calendar day: EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 bps
    (D0/EXP-034 values, unchanged), charged `rate_i × elapsed_calendar_days(trigger,
    FH-exit)` with fractional days. **No post-result iteration of any cost component.**
  - Inference: frozen EXP-027 regime-cluster bootstrap (1000 resamples) + one-sided
    bootstrap p, pinned hash `e50873d12a9f68d9` (same tail as EXP-034).
- **FH(H\*) outcome:** per event, real-OHLC return from entry-confirmation close to the
  close H\* domain bars later (or last available bar if truncated at series end —
  predeclared, EXP-033-identical FH construction), minus RT_cons_i minus financing.
- **Time range:** analysis set only, nested TRAIN/TEST as above. Global holdout never
  loaded.
- **Real-price outcome discipline:** all returns real-OHLC; no synthetic prices.
- **Look-ahead prevention:** H\* and policy frozen from TRAIN only; stratum membership
  keyed on the causal trigger bar; FH exit uses only post-entry real bars.
- **Exclusions:** no 5m/1h (G1-B2 ineligible); no conditioning strata (EXP-036/035);
  no second horizon on TEST; no cost-model change; no holdout; no re-selection after
  any TEST read.

## Estimand and procedure (LOCKED)

- **Per-cell estimand:** event-weighted mean of `net_e = FH_bps_e(H*) − RT_cons_i −
  financing_e` over the cell's TEST-stratum events (pyramids per frozen policy).
- **Binding TEST rule (G2-strict, design §8.4 as amended R1.1/R1.2):** per tested
  4h cell, **net one-sided 95% lower bootstrap bound > m_cell** (the calibrated
  margin) AND **Holm-adjusted one-sided bootstrap p ≤ 0.05 across the phase-level
  G2 family** (the realized binding TEST p-values of Phase 008: these 3 cells +
  EXP-038's cell). This experiment emits **raw** p's and a clearly labeled
  **provisional route-level flag** (`route_pass_provisional`, within-route Holm-3 +
  margin); the **binding adjudication happens once in the checkpoint's
  `G2-gate-review.md`** after EXP-038 also completes. No `g2_satisfied` flag is
  emitted here.
- **Descriptive labels** (non-binding) from the two-sided 95% CI: EVIDENCE_FOR /
  EVIDENCE_AGAINST / INCONCLUSIVE_SPANS_ZERO.
- **Zero-baseline:** baseline is exactly 0 bps net; no percentage-of-baseline metric.
- **Integrity guards (must pass before any TEST verdict):** (1) TRAIN H\* tie-break
  machinery reproduces EXP-033 FH inputs at the overlapping horizons to ≤ 0.01 bps
  (on EXP-033's own contained population and bar-index cutoff — reproduction anchor
  only); (2) TRAIN+TEST event counts reconcile to the EXP-030 4h population
  partition (no dropped/duplicated events; TRAIN∪TEST = full-analysis cell), with
  the timestamp-vs-bar-index membership divergence disclosed; (3) frozen-tail hash
  pin verified; (4) same-seed determinism replay; (5) **no TEST quantity is computed
  until H\*, policy, calibration margins, and the stratum manifest are written to
  disk** (freeze-before-TEST assertion); (6) **no-second-read guard:** TEST
  inference refuses to run if a verdict artifact already exists (R1.6 recovery
  semantics).

## Predeclared power statement (mandatory)

The 4h population is small and the TEST stratum is ~30% of it. From the EXP-030 4h
dispersions:

| 4h cell | full-analysis n | approx TEST n (~30%) | expectation (honest) |
| --- | --- | --- | --- |
| EURUSD-4h | 39 | ~12 | Likely power-limited; a clean one-sided pass is the optimistic case. |
| USTEC-4h | 36 | ~11 | Expected INCONCLUSIVE on power. |
| XAUUSD-4h | 42 | ~13 | Expected INCONCLUSIVE on power. |

A TEST INCONCLUSIVE on all three cells is an **expected, honest** outcome, not an
experiment failure — it would route the phase to CHARACTERISED_NOT_CONFIRMED via B2
while EXP-038 carries the independent A1-cell route. The realistic prize, if any, is
the FH-exit recovery of the 4h BTC-exit drag (−27 bps, EXP-031); a null on this small
sample does not refute the mechanism.

## Success / Failure Criteria

- **Evidence FOR (phase-binding, adjudicated in `G2-gate-review.md`):** ≥1 declared
  4h cell is `EXIT_FH_TEST_PASS` (one-sided CI_low > m_cell AND phase-family Holm
  p ≤ 0.05) → satisfies strict G2 → EXP-032 holdout-release checkpoint becomes
  admissible for a predeclared package (operator selects one). This experiment
  alone records `route_pass_provisional` per cell, pending the phase adjudication.
- **Evidence AGAINST:** all tested cells net CI_high < 0 on TEST.
- **Inconclusive:** TEST CIs span zero (power-limited; expected per the statement).
- **`B2_NO_ROBUST_HSTAR`:** TRAIN tie-break stability filter empties → no TEST read;
  the phase-level G2 family shrinks to EXP-038's single read (a TRAIN-determined
  event, fixed before any TEST contact).

## Complexity Budget

- Statistical test families: 1 (regime-cluster bootstrap CI + one-sided p, applied per
  cell; phase-family Holm). The R1.2 null calibration is verification machinery of
  the same frozen family (synthetic data only), not a new test family.
- Visualisations: 3 (TRAIN {4,6,8,12} net table incl. split-halves; TEST per-cell net
  vs zero with provisional flags; FH(H\*) vs BTC-exit per-cell comparison).
- New code modules: 1 (orchestration reusing EXP-033 FH construction + EXP-034
  cost/financing overlay; no new reusable `xen` module unless an FH helper is shared
  with EXP-033 — prefer reuse).

## Data Requirements

Same event provenance as EXP-034. FH(H\*) exit prices from the rebuilt 4h series at
`entry_idx + H*` (truncation rule EXP-033-identical). Stratum partition computed once
from trigger timestamps and written to disk with the frozen H\*/policy before any TEST
outcome is read.

### Standard Loading Pattern

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)          # global holdout never read
bars = scan.slice(0, analysis_cutoff).collect()
train_cutoff = int(analysis_cutoff * 0.7)        # TRAIN = first 70% of analysis
# TEST stratum = analysis rows [train_cutoff, analysis_cutoff); read once, after freeze
```

## Suggested Direction

Thin deterministic overlay: reuse EXP-033's TRAIN FH machinery to build the
{4,6,8,12} split-half table, apply the mechanical tie-break, persist H\*/policy, then
run the EXP-034 cost/financing bootstrap once on the 4h TEST stratum with Holm. The
freeze-before-TEST assertion (guard 5) is the load-bearing control — it is what makes
the TEST read one-shot and honest.
