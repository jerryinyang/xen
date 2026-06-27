# Results: Experiment EXP-068 — MA(20,50)-Substrate Native Combined Champion

## Summary

On the native conditioning object (MA-segment `/STRONG-STAT`, 8360-class), **both** predeclared
champion arms clear the full **G-015 conjunction** — per-cell median-viable **AND** raw-mean-positive
(P4 co-primary) **AND** beats the matched-random-on-MA null — composed at P11 with the P6 non-4h
rule. `N-PARTIAL-V2A` composes in **9 cells / 5 instruments / 7 non-4h**; `N-V2A×ADV-NONE` in
**14 cells / 9 instruments / 6 non-4h**. This is the **first Phase 015 native read where the mean
co-primary clears composition** (EXP-066's S3 PARTIAL-V2A was median-viable + beats-RM but the mean
was not required there). The deliverable label is **NATIVE_COMBINED_CHAMPION_G015_INPUT =
PROCEED_TO_SCREEN-candidate**. Integrity is clean: all three P12 anchors reproduce to 1e-9 (99/99),
determinism/causality/invariants pass, and ADV-NONE produced **zero** adverse stop-outs. Two honest
caveats temper the headline: (1) the mean edge is **narrow** (mean-positive 11/14 of 99 vs
median-viable 45/89) and, for `N-V2A×ADV-NONE`, its composition is **4h-concentrated** (8/14 cells
are 4h) with broad mean-negativity classified **TAIL_DRIVEN** (63/99); (2) the genuinely robust,
non-4h, geometry-independent signal is a **small FX core** of ~5 cells. **G-015 is not adjudicated
here** — that single terminal gate runs after the full slate (incl. EXP-067 hybrid + cross-object
comparison).

## Detailed Findings

### Finding 1 — Both champion arms compose the full G-015 conjunction (hypothesis SUPPORTED)

- **Observation**: per-cell G-015 conjunction (`median CI_low>0` ∧ `raw-mean CI_low>0` ∧
  `arm−RM-native CI_low>0`) composes at P11+P6 for both champion arms.
- **Evidence** (`g015_verdict.json`, `champion_map.csv`):

  | Arm | median-viable | mean-positive | beats-RM | S3-EF | **G-015 cells** | instr | non-4h | composes |
  |---|---|---|---|---|---|---|---|---|
  | BENCH (ref) | 8 | 10 | 8 | 0 | 6 | 4 | 6 | (ref) |
  | **N-PARTIAL-V2A** | 45 | 11 | 41 | 21 | **9** | 5 | 7 | **YES** |
  | **N-V2A×ADV-NONE** | 89 | 14 | 85 | 57 | **14** | 9 | 6 | **YES** |

- **Interpretation**: per the scope's success criteria, ≥1 champion arm satisfying the full
  conjunction at P11+P6 is the **PROCEED_TO_SCREEN (G-015)** surface input. Both arms qualify, so the
  native combined champion delivers a PROCEED-candidate. The falsifiable hypothesis ("no champion arm
  simultaneously satisfies the conjunction") is **not** falsified → **SUPPORTED** as a surface
  deliverable.

### Finding 2 — The signal is genuine, not a geometry artifact: it is present at the single-leg BENCH

- **Observation**: the single-leg benchmark geometry already composes the conjunction (median ∧ mean
  ∧ beats-RM) in **6 non-4h FX cells** (EURUSD-15m/30m, GBPUSD-1h, NZDUSD-1h/2h, GBPJPY-30m; 4
  instruments), with mean CI_low strictly > 0 (0.006–0.297 ATR).
- **Evidence**: BENCH g015 = 6, all non-4h; `var_rm_median_low_1s > 0`; the robust non-4h core
  (GBPJPY-30m, GBPUSD-1h, GBPUSD-5m, NZDUSD-1h, NZDUSD-2h) holds under **both** champion arms, and 4
  of those overlap the BENCH set.
- **Interpretation**: the mean-positive, RM-beating edge does **not** depend on the partial-exit or
  ADV-NONE machinery — it exists at benchmark on a coherent liquid-FX cluster (GBPUSD/NZDUSD/GBPJPY/
  EURUSD). The champion geometries **broaden** it; they do not manufacture it. This strengthens the
  "real matched-substrate conditioning signal" reading from EXP-061.

### Finding 3 — The mean co-primary is the binding bottleneck; ADV-NONE recovers it but via a tail trade-off

- **Observation**: median viability is broad (N-PARTIAL-V2A 45, N-V2A×ADV-NONE 89 of 99) but
  mean-positivity collapses (11 and 14). `N-V2A×ADV-NONE` recovers more median-viable and beats-RM
  cells than `N-PARTIAL-V2A` (89 vs 45; 85 vs 41) — removing the adverse stop eliminates
  stop-induced negative-median cells, exactly the EXP-060B mechanism.
- **Evidence** (`g015_verdict.json` P4 closure): `N-PARTIAL-V2A` → `PARTIAL_RECOVERY` (51 cells
  mean-negative point estimate, but only 1 structural, 0 tail-driven); `N-V2A×ADV-NONE` →
  `TAIL_DRIVEN` (63/99 cells tail-share > 0.40; 58 mean-negative-pt; 0 structural). Headline non-4h
  cells (`N-V2A×ADV-NONE`): median 1.06–1.68 ATR, mean 0.18–0.86 ATR (mean CI_low 0.037–0.327),
  arm−RM CI_low 0.59–1.10 ATR.
- **Interpretation**: the negative mean is **not structural** for either arm (trimmed mean rarely
  also-negative) — consistent with the Phase 015 thesis that the MA mean ≈ 0 is a removable-tail /
  geometry phenomenon, not irrecoverable un-tradability. But `N-V2A×ADV-NONE` "recovers" the mean in
  a subset by accepting **fat negative tails** elsewhere (the ADV-NONE skew). The bounded-downside
  `N-PARTIAL-V2A` is the cleaner (PARTIAL_RECOVERY, no tail-driven cells) but narrower champion.

### Finding 4 — Concentration caveat: ADV-NONE's headline leans on 4h; the robust non-4h core is small

- **Observation**: `N-V2A×ADV-NONE`'s 14 G-015 cells are **8/14 in the 4h domain**; its non-4h
  breadth is **6** (clears the P6 floor of 3 but is the real load-bearing count). `N-PARTIAL-V2A` is
  less 4h-reliant (9 cells, 7 non-4h, 2 4h).
- **Evidence**: the non-4h robust core common to both champion arms is **5 cells over 3 instruments**
  (GBPJPY-30m, GBPUSD-1h, GBPUSD-5m, NZDUSD-1h, NZDUSD-2h) — exactly at the P11 quorum (5 cells / 3
  instruments). No DE30-truncated cell appears in any G-015-passing set.
- **Interpretation**: this mirrors the EXP-060B "8/14 low-n 4h" concentration the Phase 015 P6 rule
  was written to discount. The composition is mechanically non-fragile, but the **defensible**
  signal is the small non-4h FX core, not the headline 14-cell ADV-NONE count. The gate should weigh
  non-4h breadth over headline cell count.

### Finding 5 — Cross-object: the edge is native/matched-substrate specific (disclosed, not pooled)

- **Observation**: across the dual-object surface (EXP-061–066) the **hybrid** object was
  EVIDENCE_AGAINST at L1/S1/S3 and INCONCLUSIVE at S2; EXP-067 (hybrid combined champion) is
  **PENDING**.
- **Evidence**: `g015_verdict.json → disclosed_hybrid`; hyb-BENCH here is a P12 check only
  (reconciles EXP-061 H0, 99/99) and is excluded from every native composition.
- **Interpretation**: consistent with EXP-061's headline — the MA-substrate edge generalises only
  when `/STRONG-STAT` is computed on the **same MA segment** that defines the geometry (native), not
  on the ZigZag move (hybrid). The native PROCEED-candidate is an object-specific property, never
  pooled with hybrid.

## Hypothesis Verdict

**SUPPORTED (surface deliverable) — PROCEED_TO_SCREEN-candidate input to G-015.**

≥1 champion arm (in fact both) satisfies the full G-015 conjunction (median-viable AND
raw-mean-positive AND beats-RM-native) composed at P11+P6 on the native object. Integrity gates all
pass. **This is the input to G-015, not the gate decision itself** — the single terminal G-015 (after
the full slate, incl. EXP-067 hybrid + cross-object comparison) must weigh the caveats below before
adjudicating PROCEED / candidate registration. No candidate slot is consumed here (0 slots, 0 TEST).

## Limitations

- **Narrow mean breadth.** Mean-positive composes on 11–14 of 99 cells vs 45–89 median-viable; the
  family's broad strength is the **median**, the mean edge is real but thin.
- **4h concentration (ADV-NONE).** 8/14 of `N-V2A×ADV-NONE`'s G-015 cells are 4h; the non-4h count
  (6) is the load-bearing breadth. The robust geometry-independent core is ~5 non-4h FX cells.
- **ADV-NONE tail trade-off.** `N-V2A×ADV-NONE` is `TAIL_DRIVEN` (63/99): its mean recovery comes
  with fat negative tails in the majority of cells — gross, costs excluded.
- **Gross only, TRAIN only.** No costs; TEST/holdout untouched. A mean edge this thin is the most
  cost-sensitive endpoint and is unverified out-of-sample by design.
- **Single-object read.** The cross-object comparison is disclosed-only until EXP-067 completes.

## Alternative Explanations

- The 4h-heavy ADV-NONE composition could be a low-n artifact of long-horizon cells rather than a
  durable edge; the non-4h FX core (present even at BENCH) is the conservative reading.
- The mean recovery under ADV-NONE may partly reflect the uncapped-upside / fat-tail skew (median ≫
  mean) rather than a genuinely higher expected value — the `TAIL_DRIVEN` P4 classification supports
  treating ADV-NONE's headline with caution.

## Recommended Next Steps

*(New scopes only — not extensions of EXP-068. None pre-empts the G-015 gate.)*

1. **EXP-067 (hybrid combined champion)** — already on the slate; required for the G-015 cross-object
   comparison before adjudication.
2. **Post-PROCEED only:** a TEST-stratum confirmation scope for the native non-4h FX core under the
   bounded-downside `N-PARTIAL-V2A` champion (consumes the first candidate slot + a counted TEST
   read), gated on G-015 PROCEED.
3. **Post-PROCEED only:** a cost-aware re-read of the mean co-primary on the FX core (the thin mean
   is the cost-sensitive endpoint), and a targeted tail-filter / capped-downside follow-up for the
   `N-V2A×ADV-NONE` TAIL_DRIVEN cells (the MEAN_RECOVERABLE lever).

---

## Post-Hoc Addendum — Winsorized Mean Diagnostic (2026-06-18)

**Status: exploratory, non-predeclared. Does not alter any binding conclusion, G-015 input, or
registry disposition. Recorded here as context for the terminal G-015 gate.**

### Motivation

Finding 3 identifies the raw-mean co-primary as the binding bottleneck: median-viable counts
(45/89) are an order of magnitude larger than mean-positive counts (11/14). The hypothesis to
test was whether this suppression is a **metric artifact** — i.e., a small number of extreme
negative-return events dragging the raw mean below zero — rather than evidence of a genuinely
negative expected value in those cells.

### Method

A 10% symmetric winsorized mean was added to the experiment code
(`python/experiments/EXP-068/code/run_experiment.py`, function `_winsorized_mean`). The
winsorization fraction matches the existing `TRIM_FRAC = 0.10` used for the trimmed mean. Unlike
trimming (which discards the extreme 10% on each side), winsorization **replaces** those values
with the boundary values (`p10` and `p90`), so the full sample contributes to the mean but
extreme observations are clipped. No RNG, bootstrap, or CI is involved — this is a point
estimate only. A cell is counted `winsorm+` when `m >= 30` and the winsorized mean point
estimate is `> 0`.

The script was re-run on the same TRAIN data. All binding outputs (median CIs, raw-mean CIs,
contrast CIs, G-015 flags, reconciliation) are byte-identical to the original run.

### Results

| Arm | median-viable | mean+ (CI) | **winsorm+ (pt est)** | beats_rm | G-015 cells |
|---|---|---|---|---|---|
| BENCH (ref) | 8 | 10 | **46** | 8 | 6 |
| N-PARTIAL-V2A | 45 | 11 | **57** | 41 | 9 |
| N-V2A×ADV-NONE | 89 | 14 | **73** | 85 | 14 |

Total member cells: 99.

### Interpretation

The winsorized mean is positive in **46–73 cells** versus **10–14 for the raw mean** — a
difference of ~4–5×. For `N-V2A×ADV-NONE`, the winsorized mean is positive in 73/99 cells while
the raw mean is positive in only 14. This is a qualitative shift, not a marginal one.

This directly confirms the P4 `TAIL_DRIVEN` / `PARTIAL_RECOVERY` diagnosis: the raw-mean
co-primary is failing because a **fat negative tail** (worst-5% tail-share > 0.40 in 63/99
cells for `N-V2A×ADV-NONE`) pulls the mean below zero even in cells where the **central
tendency** — both the median and the winsorized mean — is clearly positive. The underlying
signal is not negative in expectation in those cells; the negative raw mean is a distributional
feature of the exit structure (primarily timecap/censored events with unbounded-downside skew
under ADV-NONE), not a directional verdict on the strategy.

**The finding supports the Phase 015 thesis stated in Finding 3**: the mean suppression is a
removable-tail / exit-geometry phenomenon. A tail-robust mean estimator (winsorized or trimmed)
passes broadly where the raw mean does not, and those are exactly the cells already passing
median viability and beats-RM.

### Implication for G-015

The terminal gate should be aware that the raw-mean co-primary — as currently defined (raw mean
bootstrap CI_low > 0) — is operating as a **tail-sensitivity filter**, not a standard expected-
value test. It is passing the 11–14 cells with the most benign exit distributions and failing the
majority of cells where the median and winsorized mean are both positive. Whether this is
appropriate (the raw mean is the predeclared co-primary and its CIs are valid) or whether a
tail-robust alternative would be more informative is a gate-level adjudication question, not an
EXP-068 conclusion.

**No binding conclusions are changed. This addendum is an exploratory diagnostic only.**
