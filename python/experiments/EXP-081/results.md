# Results: Experiment EXP-081

**Per-substrate realized return-structure characterization (4 frozen substrates × 46 member cells; 5-year data; TRAIN-only, gross).**
Phase 018 · CF-CAPGEO-001 · HYP-002 · 0 candidate slots · 0 counted TEST reads · audit PASS (0C/1W/3I).

## Summary

**Verdict: CHARACTERISATION_DELIVERED.** All **184** member substrate-cells (4 substrates × 46
EXP-080-READY instrument×domain cells) produced the frozen D3-input statistics, the minority-mass /
left-tail read, the `m_anti` bimodality diagnostic, and the non-binding `ASS` discovery disclosure,
deterministically. 0 underpowered cells (`n_usable` 46–5535, median 1083), 0 nondeterministic, harami
entry-population identity exact, EXP-080 reconciliation 184/184, holdout untouched, 0 counted TEST reads.
The D3 inputs are ready to drive EXP-082's mechanical exit-derivation rule.

The substantive finding is **mechanistic** (not an edge claim — this is a gross characterization): on the
exit-agnostic adaptive-cap geometry, **the frozen entries barely separate from a random matched-control on
gross capture availability**; the only structure is the **outcome shape** — the harami substrate
reproduces the CF-HA-HARAMI-001 *median-positive / mean-killed-by-catastrophic-tail* signature on the
disjoint 5-year data, while AVWAP is weaker but more symmetric. This squarely sets up EXP-082/083: a
data-derived exit's value must come from the **adverse/tail leg**, and EXP-083's separability gate is the
crux.

## Detailed Findings

### Finding 1 — D3 inputs delivered and EXP-082-ready (per cell)

Every member cell yields the frozen D3 table the EXP-082 rule consumes (D0 §D3):

| EXP-082 barrier | D3 input(s) | EXP-081 status |
|---|---|---|
| `T_fav` (favourable target) | `MFE_med` (D1/D2), `MFE_q40` (D3-cand) | Estimable in all 184 cells; per-substrate medians ~3.2–3.4 ATR. |
| `S_adv` (adverse stop) | `m_anti` **else** `MAE_q90` | `m_anti` NaN in 183/184 → `MAE_q90` fallback (per design), estimable all cells (~9–9.7 ATR). |
| `H_cap` (time cap) | `TTP_q75` (D1/D2), `TTP_med` (D3-cand) | Estimable all cells; `TTP_q75` clusters ~37–52 bars (median ~44; one 4h outlier 73). |

Supporting shape reads (`tailmass`, `q05`, `dip_p`, `m_anti`) and the non-binding `ASS`
expectancy/median/tail are attached per cell. **No cell fell below the 30-event floor**, so EXP-082 can
form a derived candidate for every member cell (no `UNDERPOWERED_DISCLOSED` exclusions).

### Finding 2 — Per-stratum framing: the headline medians are disclosures, not an edge (LESSON-001)

Per-substrate pooled medians (AVWAP `MFE_med` 3.39 / harami 3.25 / random 3.36; `ASS` expectancy AVWAP
+0.157 / harami +0.000 / random +0.062) are **disclosure-only**. The binding picture is **per cell**,
adjudicated against the within-cell `SUB-RANDOM` control. No pooled edge is claimed; substrates are never
pooled.

### Finding 3 — Gross capture availability ≈ random (the AVWAP-situation echo)

Per-cell paired difference (real − within-cell random), 46 cells:

| Metric | AVWAP median Δ (cells real>rand) | harami median Δ (cells real>rand) |
|---|---|---|
| `MFE_med` (favourable availability) | +0.061 (28/46) | **−0.140 (17/46)** |
| `MAE_q90` (adverse extent) | −0.554 (18/46) | −0.719 (9/46) |
| outcome median | +0.040 (23/46) | +0.016 (25/46) |

Favourable-move *availability* sits at the random baseline — harami's median favourable excursion is
actually **below** random, AVWAP's is coin-flip; the outcome-median edge over random is ≈ chance
(23–25/46). **Move availability is not the differentiator** — the same conclusion CF-AVWAP-001 reached
(EXP-047: "move availability was never the binding constraint; capture geometry is"), now reproduced on
the 5-year data for both inherited entries. This is the central justification for the family's
exit-first thesis: the lever is the exit, not the entry, and not raw move size.

### Finding 4 — The only structure is the outcome shape — CF-HA-HARAMI-001 signature reproduced

Per-cell outcome location, summarized across 46 cells:

| Substrate | median-of-cell **means** | median-of-cell **medians** | cells median>0 | cells mean>0 | cells median>mean |
|---|---|---|---|---|---|
| SUB-AVWAP | +0.157 | +0.150 | 26/46 | 30/46 | — (≈symmetric) |
| **SUB-HARAMI-PARTIAL-V2A** | **+0.000** | **+0.135** | **30/46** | **23/46** | **33/46** |
| SUB-RANDOM | +0.062 | +0.085 | 28/46 | 26/46 | — |

The harami entry carries a **median-positive edge (+0.135 ATR) whose mean is ≈ 0** — in 33/46 cells the
median exceeds the mean (left-tail drag), driven by a ~5% catastrophic-loser minority (`tailmass` 0.0526 >
random 0.0437, 31/46 cells; `q05` ≈ −9 ATR). This is the **exact failure shape that closed
CF-HA-HARAMI-001** (EXP-071 raw-mean leg failed; EXP-074 identified the entry bimodality), now shown to
**persist on the disjoint 5-year dataset**. AVWAP, by contrast, is roughly symmetric (mean +0.157 ≈ median
+0.150) — a weaker but not tail-killed shape. `SUB-RANDOM` is the modest positive baseline (median +0.085)
that the real substrates only marginally exceed.

### Finding 5 — `m_anti` resolves in 1/184 cells (heavy tail, not a separated mode)

The MAE distributions are predominantly **unimodal** to the Hartigan dip (dip_p median 0.976; 184 finite,
136 unique p-values; the lone resolver is US500-1h AVWAP, dip_p 0.032, `m_anti` 1.79). The catastrophe is
a **heavy continuous left tail**, not a cleanly separated second mode — so `m_anti` is correctly NaN almost
everywhere and EXP-082's adverse leg uses the `MAE_q90` fallback in 183/184 cells, **exactly as D9
anticipated** (`m_anti` power-limited; fallback dominates). The dip test is genuinely exercised; this is
the data's shape, not a defect.

### Finding 6 — `ASS` discovery disclosure (non-binding, G-017 DISCOVERY_ONLY)

`ASS` expectancy/median/tail are reported per cell as **disclosure only** — no decision rests on them.
They corroborate Finding 4 (harami `ASS` expectancy +0.000 vs median +0.135; AVWAP symmetric +0.157/+0.150).
D6 Guard (i) (defer expectancy→median at effective-n ≤ 60 on bimodal/asymmetric strata) is wired and fired
0 times — all member cells have n ≫ 60, so the bracket/guard regime is comfortably satisfied.

## Hypothesis Verdict

**CHARACTERISATION_DELIVERED.** The HYP-002 question — *do the frozen entries' realized return structures
expose what exit fits?* — is answered with a complete, deterministic, EXP-082-ready D3-input set, and a
clear mechanistic read: the exit-relevant structure is concentrated in the **outcome tail/shape**, not in
gross favourable availability. This is a descriptive characterization; **no edge, tradability, or pass/fail
claim is made or implied** (0 slots, gross, TRAIN-only).

## Limitations

- **Gross, no costs.** No spread/slippage/financing; absolute ATR-normalized geometry only. Net behavior is
  out of scope (EXP-083).
- **TRAIN-only, no edge verdict.** First-70%-of-analysis TRAIN sub-split; the analysis-TEST stratum and the
  final-30% holdout are untouched. Nothing here is a tradability or confirmation read.
- **`m_anti` power-limited by design.** It resolves only where a separated adverse mode exists (1/184); the
  catastrophe-detection job is carried by `tailmass`/`q05` on the outcome distribution, as intended.
- **Harami substrates are one object.** `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` carry the
  identical entry population (geometry exact); they differ only by their later benchmark *exits* (EXP-083).
  Treat their EXP-081 geometry as a single substrate.
- **Per-cell paired contrasts are descriptive.** The real-vs-random differences in Findings 3–4 are gross,
  un-bootstrapped read-outs for characterization; the binding matched-control inference is EXP-083's
  separability gate (S1), not run here.

## Alternative Explanations

- *Could the near-random gross geometry be a cap mis-sizing?* The adaptive cap is the validated EXP-068
  MA-tempo cap applied uniformly (incl. to random), so any cap effect is shared by the random control —
  the *difference* from random is cap-robust. `TTP_q75` ≪ cap (peaks land well inside the window), so the
  cap is not truncating the favourable move.
- *Could the harami mean≈0 be a few outlier cells?* No — it is substrate-wide (33/46 cells median>mean),
  not a handful of instruments (audit per-stratum masking check).

## Recommended Next Steps (new scopes — not extensions of EXP-081)

1. **EXP-082 (HYP-003, derive):** apply the frozen D3 mechanical rule to these inputs. Given Findings 3–5,
   the derived candidates' differentiation from random will hinge on the **adverse leg** (`S_adv` =
   `MAE_q90` fallback truncating the catastrophe tail); the favourable target (`MFE_med`/`MFE_q40`) is
   ≈ random and unlikely to be the source of any edge.
2. **EXP-083 (HYP-004, test + benchmark):** the **separability gate (S1∧S2) is the crux** — does cutting
   the catastrophe tail (the obstacle) also remove the median-positive edge? If yes, this is the same
   unfilterable-mechanism trap that closed CF-HA-HARAMI-001; if no, a tail-truncating data-derived exit is
   a genuine candidate. Per-stratum adjudication; counted TEST reads spent only there.

These are pointers for the next checkpoint items; EXP-081 makes no claim on their outcomes.
