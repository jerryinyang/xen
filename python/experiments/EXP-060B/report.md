# EXP-060B Report — MA(20,50) Substrate Dominance: Genuine Lead or Skew Artifact?

**Status:** `SUBSTRATE_LEAD_FOUND` · **Audit:** PASS (0 Critical / 2 Warning / 3 Info) · **Date:** 2026-06-17
**Phase:** 014-B (diagnostic addendum to EXP-060, HYP-013b) · **Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN)
**Slot/ledger:** 0 candidate slots, 0 TEST reads, TRAIN-only, gross, holdouts sealed.

## Research question

EXP-060 closed its combined-system read as `CHARACTERISED_NOT_VIABLE_ELIGIBLE`, recording the MA(20,50)
baseline's ~3–4× median advantage over the ZigZag champion as a *"substrate property."* That reading rested on
two untested confounds: (1) EXP-060 emitted MA's **median** only — never its **mean** or exit composition — yet
the ZigZag champion's own gross mean is ≈0 on 5/6 domains (capped V2A upside + uncapped `/ADV-NONE` downside);
(2) MA's advantage was never tested against a **matched-random control on the MA substrate**, so "the harami
adds value on MA" was untested. EXP-060B asks: **is the MA median dominance a genuine signal-attributable edge,
or the same capped-up/uncapped-down left-skew + entry-redundant artifact as the ZigZag champion?**

## Scope & method

Re-instruments EXP-060's per-cell pipeline on the **identical** conditioned `/STRONG-STAT` HA-harami population
(99-cell TRAIN grid; reconciliation exact 99/99). Ten predeclared objects: 8 signal arms — ZigZag {Z0 BENCH,
Z1 50PCT-NONE, Z2 V2A-1TO1, Z3 V2A-NONE} and MA(20,50) {M0,M1,M2,M3} — plus two matched-random nulls RZ3
(ZigZag) and RM3 (MA, the one new computation). Binding endpoint unchanged: **median** per-event
position-weighted gross ATR-normalised return (P14, P15 fills); **mean** disclosed and used as the
characterisation lens. Three diagnostics: **D1** median vs mean (skew); **D2** `M3 − RM3` independent contrast
(binding discriminator); **D3** exit-reason composition. Four methods (median CI, mean CI, independent
signal-vs-null contrast, baseline contrast), 5 plots, 0 new `xen/` modules. Real-price metrics throughout
(MA(20,50) on real close; HA only for detection). Detail: [`scope.md`](scope.md),
[`analysis-plan.md`](analysis-plan.md).

## Key results

### D2 — The harami expresses a REAL median edge on MA (binding discriminator)

| Quantity | Value | P11 |
|---|---|---|
| M3 median-viable | 89 / 99 cells (17 instr) | ✓ |
| M3 beats RM3 (independent median contrast CI_low>0) | **85 / 99** | ✓ |
| M3 mean-viable | **14 / 99** | ✓ (9 instr) |
| **M3 lead cells** (median-viable ∧ beats RM3 ∧ mean-viable) | **14 / 99 (9 instr)** | **✓ → SUBSTRATE_LEAD_FOUND** |

- RM3 (matched-random on MA) median across cells = **0.380** (min 0.268 / max 0.530) — i.e. it reproduces the
  ~0.38-ATR geometry drift-capture baseline EXP-060 measured. The control is **fair, not degenerate**.
- M3 median = **1.158** (0.075 / 1.821); the `M3 − RM3` median contrast CI_low has median **0.551** (only 4/89
  ≤ 0). The harami+strong signal adds ~0.78 ATR of median over random **on MA**.
- **This reverses ZigZag.** On ZigZag the same signal beat its matched-random in only **3/99** (EXP-060); on MA
  it beats it in **85/99**. The substrate genuinely determines whether the harami expresses an edge.

### D1 — But it is a MEDIAN-only edge: the mean is ≈0, ADV-NONE-driven (skew confirmed)

- M3 gross **mean** median across cells = **−0.065** (RM3 −0.054). M3's mean clears zero with one-sided
  confidence in only **14/99** cells — the binding constraint on the lead. The 75 median-viable-but-not-lead
  cells are blocked by the mean.
- Skew is driven by the uncapped downside. Median (median−mean) gap by adverse model:

  | Substrate | ADV-NONE gap | 1:1 gap |
  |---|---|---|
  | ZigZag | 0.163 | 0.114 |
  | **MA** | **1.201** | 0.495 |

  On MA the ADV-NONE gap is **1.20 ATR** — the capped V2A upside with a time-cap-realized uncapped downside
  produces a fat left tail that zeroes the mean even where the median is strong.

### D3 — M3 wins by magnitude, not hit-rate

Pooled exit-weight (favourable legs vs time cap): Z3 TIMECAP 0.64 / FAV 0.36; **M3 TIMECAP 0.41 / FAV 0.59**;
RM3 TIMECAP 0.18 / FAV 0.82. M3 is less TIMECAP-bound than Z3 (MA converts more to FAV), but RM3 hits FAV
**more** than M3 — non-conditioned random entries have smaller `M_sofar` → nearer targets → higher hit-rate. So
M3's median edge is **larger realized magnitude per resolution** under strong-conditioning (further targets),
not a higher favourable hit-rate — and that same further-target-with-no-stop geometry is what generates the
left tail in D1.

## Conclusion

**`SUBSTRATE_LEAD_FOUND`** — mechanically met and audit-validated. The two confounds resolve oppositely:

- **Redundancy confound → refuted on MA.** The conditioned harami is *not* redundant on the MA substrate; it
  lifts the median from the geometry baseline (~0.38) to ~1.16 and beats its own matched-random control in
  85/99 cells. This is the genuine discovery — and it directly qualifies EXP-060's "substrate property" reading:
  the MA advantage is *partly* a real signal effect, not solely a geometry/drift artifact.
- **Skew confound → confirmed.** That edge is **not tradeable** as configured: M3's gross mean is ≈0/negative
  across most of the grid (ADV-NONE uncapped-downside skew, gap 1.20 ATR on MA). The mean-positive subset is
  exactly the 14 lead cells.

Net: **a real but narrow MA-substrate median edge that is not yet a mean-positive (tradeable) edge.** The
binding obstacle to viability has shifted from "does the signal work" (it does, on MA) to "does the no-stop
geometry leave a positive mean" (it does not, except marginally).

## Audit caveats

- **W1 — Lead narrow / 4h-concentrated:** P11 met via 14 cells/9 instruments, but **8/14 are 4h** (n=108–194),
  the highest-noise domain; high-count lead cells have mean CI_low barely >0 (0.037–0.088). Not a broad, stable
  edge.
- **W2 — Median overstates tradeable expectancy:** the lead is a median phenomenon; the average M3 trade makes
  ≈0 gross, before costs.
- **I2 — Plan/code note (code correct):** [`analysis-plan.md`](analysis-plan.md) §2 mislabeled the M3−RM3
  contrast as *paired*; the code correctly uses **independent** `contrast_ci` (matched-random are different
  events, no common subset to pair).
- **I3 — Attribution breadth:** M3 vs RM3 attributes the lift to the **combined** harami+`/STRONG-STAT` signal,
  not separately to harami pattern / strong conditioning / MA-direction interaction (EXP-060 convention).
- Gross only; costs would erode the marginal mean further.

Integrity: reconciliation exact 99/99 (Z3↔EXP-060-A3, M3↔EXP-060-maseg, exit weights); determinism ✓,
causality ✓ (0 violations), invariants ✓ (ADV-NONE fires 0 ADV exits; matched-count holds; weights sum 1.0);
holdout fence respected. Full audit: [`audit.md`](audit.md).

## Signal-registry disposition (registry-relevant)

- `multiplicity-registry.md`: `CF-HA-HARAMI-001/HYP-013b — EXP-060B` advanced **PLANNED → CHARACTERISED —
  SUBSTRATE_LEAD_FOUND**; the EXP-060 G2 routing note updated to record that EXP-060B returned
  SUBSTRATE_LEAD_FOUND (do **not** close CF-HA-HARAMI-001 without a scoped MA-substrate follow-up).
- Family `CF-HA-HARAMI-001` stays **REGISTERED, OPEN**. **0 candidate slots, 0 TEST reads** — no candidate is
  registered here (registration occurs only at G2 PROCEED on a future MA-substrate scope). `test-read-ledger.md`
  unchanged (no TEST stratum touched).
- The G2 desk adjudicates the single 014-B outcome; EXP-060B does not close the phase.

## G2 routing consequence

EXP-060B reframes the G2 decision: the binding constraint is the **skew/mean**, not the signal's existence. A
follow-up that re-runs the MA signal under the current V2A×ADV-NONE geometry will inherit the mean≈0 problem.

## Follow-ups (new scopes only)

1. **MA-substrate geometry vs the skew (priority):** re-screen the MA-conditioned harami under **stop-bearing**
   adverse models (registered 1:1, `/ADV-EXTREME-rr1`) and capped favourable schemes, with the **mean** as a
   co-primary endpoint — D1 shows the 1:1 gap (0.49) is <half the ADV-NONE gap (1.20) on MA, so a bounded
   downside may recover the mean at some median cost.
2. **Signal-component attribution on MA** (harami-only / strong-only vs RM3) — only if G2 routes to a SUBSTRATE
   follow-up.
3. **Cost-bearing screen** of any mean-positive MA geometry (future tradability phase).

## Artifacts

[`scope.md`](scope.md) · [`analysis-plan.md`](analysis-plan.md) · [`code/run_experiment.py`](code/run_experiment.py)
· [`results/`](results/) · [`results.md`](results.md) · [`audit.md`](audit.md) ·
[`governance/pre-execution-review.md`](governance/pre-execution-review.md)
Plots: [`plots/d1_median_vs_mean.png`](plots/d1_median_vs_mean.png),
[`plots/d1_skew_gap_by_adverse_model.png`](plots/d1_skew_gap_by_adverse_model.png),
[`plots/d2_m3_rm3_forest.png`](plots/d2_m3_rm3_forest.png),
[`plots/d3_exit_reason_composition.png`](plots/d3_exit_reason_composition.png),
[`plots/ma_substrate_viability_map.png`](plots/ma_substrate_viability_map.png).
Checkpoint addendum:
[`014-B-EXP-060B-ma-substrate-dominance-addendum.md`](../../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-B-EXP-060B-ma-substrate-dominance-addendum.md).
