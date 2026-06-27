# Audit Report: Experiment EXP-081

**Per-substrate realized return-structure characterization (4 frozen substrates × 46 member cells; 5-year data; TRAIN-only, gross).**
Phase 018 · CF-CAPGEO-001 · HYP-002 · auditor: experiment-auditor (Stage 5).

## Summary

**Audit verdict: PASS (0 Critical / 1 Warning / 3 Info).** The implementation is correct, deterministic,
holdout-clean, and the D3-input statistics reproduce from raw bars to full float precision. The
experiment verdict **CHARACTERISATION_DELIVERED** is faithful: all 184 member substrate-cells produced
the frozen D3 inputs, the minority-mass/tail read, the `m_anti` diagnostic, and the non-binding `ASS`
disclosure, with 0 underpowered, 0 nondeterministic, harami entry identity exact, and EXP-080
reconciliation 184/184.

The one finding that *matters for EXP-082/083* is **mechanistic, not a defect** (Warning W1, fully
documented in Verdict Forensics): on this gross, exit-agnostic geometry the real substrates barely
separate from the random matched-control — the structure lives in the **outcome shape** (a
median-positive / mean-killed-by-catastrophic-tail signature), which is exactly why only `tailmass`/`q05`
(not `m_anti`) surface it and why EXP-082's value must come from the adverse/tail leg.

---

## Code Review

| Area | Result | Evidence |
|---|---|---|
| Plan compliance | PASS | `run_experiment.py` implements analysis-plan steps 1–8; no extra analyses. |
| Holdout exclusion | PASS | `load_first70` collects only `int(total*0.7)` rows (VAL-005 `run_experiment.py:277-289`, 0 holdout rows asserted); EXP-081 then `train_frame = li.frame.slice(0, int(analysis_rows*0.7))` (`run_experiment.py:528-529`). Holdout never loaded; analysis-TEST never sliced. `holdout_untouched=true`. |
| Look-ahead | PASS | Adaptive cap uses only moves confirmed strictly before the entry (`expectancy.adaptive_time_caps_by_epoch`, `j_last = searchsorted(..., side="left")-1`); path window `[i+1, min(i+cap, last)]` (`capgeo_geometry.py:128-129`); alignment by epoch/`CloseTime`, never bar index. |
| Real-price discipline | PASS | Every MFE/MAE/TTP/outcome/ATR on real domain OHLC (`_real_ohlc`, `wilder_atr`); HA used only inside the harami **entry** detector. No HA/Renko brick price in any outcome. |
| Window-clip (TRAIN edge) | PASS | `hi = min(i+cap, last)` with `last = n_bars-1`; verified `hi <= last` on hand-derived events; 5 SUB-RANDOM events landing at the last bar correctly excluded as `clipped_empty`. |
| MFE/MAE floor | PASS | `max(0.0, ...)` (`capgeo_geometry.py:130-131`), matching the EXP-055 convention; all per-event MFE/MAE ≥ 0 verified across the saved 300,651-row per-event table. |
| Type hints / docstrings | PASS | Public functions in `capgeo_geometry.py` and the script's pure helpers typed and documented. |
| NaN / edge handling | PASS | `m_anti` → NaN when unimodal/unresolved; `tailmass` zero-tail → 0.0 with denominator; warmup/ATR-undef/clipped disclosed & excluded; `_ass_discovery` guards `n<4`. |
| Determinism | PASS | Second-pass summary fingerprint identical in-run (`nondeterministic_cells=[]`); auditor re-ran XAUUSD-4h (cell_index 32) in a fresh process → identical fingerprint. Seeds + module sha256 in `run_metadata.json`. |
| Organization / sectioning | PASS | VAL-001-style sections; output dirs created only in `main()`; `tqdm` over the 48-cell loop; `logging`, concise. |
| Vectorization discipline | PASS | Explicit causal per-event loop (bounded by the cap); only intra-window max/argmax vectorized — no future-row use. |

---

## Numerical Validation

**Spot checks (independent recompute).**

1. **D3 estimators from per-event data** (EURUSD-15m AVWAP, GBPJPY-1h harami, BTCUSD-4h random):
   `MFE_med`, `MFE_q40`, `TTP_med`, `TTP_q75`, `MAE_q90`, `tailmass`, `q05` all reproduce to `<1e-9`
   against `numpy.quantile(method="linear")` and `#{outcome < median−3·MAD}/n` — **OK** for every field.
2. **Path geometry from raw bars** (GBPJPY-1h harami, first 3 kept events): hand-computed MFE/MAE/TTP/
   outcome from `build_domain_bars` real OHLC reproduce the saved `per_event_geometry.parquet` to full
   precision (e.g. evt0 MFE=0.0291, MAE=15.9967, TTP=1, OUT=−15.6013 — exact). Window indices `hi ≤ last`
   confirmed.
3. **Accounting identity** `n_entries − n_warmup − n_usable == n_clipped_empty` holds for **all 184**
   cells. Warmup attribution coherent: harami 0 (its entry filter already drops bench-warmup), AVWAP 350,
   SUB-RANDOM 1183 (+5 clipped) early/no-regime entries.

**Range checks.** MFE_med ~3.2–3.4 ATR, TTP_med 25–27 bars, MAE_q90 ~9–9.7 ATR, tailmass 0.04–0.05 —
all plausible for ATR-normalized lifetime excursions over an adaptive cap. `n_usable` 46–5535
(median 1083); 0 cells below the 30-event floor.

**EXP-080 fidelity.** All 184 TRAIN `n_entries ≤ EXP-080 full counts`; SUB-RANDOM `n_entries ==` harami
`n_entries` per cell (matched draw, key `[SEED_RANDOM, cell_index, harami_count]` over the full 48-cell
grid); harami PARTIAL-V2A ≡ V2A-ADVNONE on all 9 D3 columns (`harami_entry_identity_geometry=true`).
AVWAP direction recovery alignment verified: re-generated trigger order `==` `EntrySet` entry-epoch order
(stable sort), lengths match (1570/1570), long-fraction 0.49 (balanced, no sign flip).

---

## Verdict Forensics (run autonomously)

This is a characterization — the "verdict" is **completeness + integrity**, both confirmed. But per the
mandate (and operator direction), the audit must explain **why the numbers came out as they did**, not
merely that they reproduce. The mechanism below is the substance the interpreter (Stage 6) and EXP-082/083
need.

### Per-stratum re-derivation & masking check

The headline per-substrate medians (AVWAP MFE_med 3.39 / harami 3.25 / random 3.36; ASS expectancy AVWAP
+0.157 / harami +0.000 / random +0.062) are **pooled disclosures**. Re-deriving **per cell, paired against
the within-cell SUB-RANDOM control** (46 cells), the pooled medians do **not** mask heterogeneity — they
*understate* a consistent, material structural finding:

**(a) On gross capture geometry the entries barely separate from random.**

| Metric (real − random, per cell) | AVWAP median Δ | cells real>rand | harami median Δ | cells real>rand |
|---|---|---|---|---|
| `MFE_med` (favourable availability) | +0.061 | 28/46 | **−0.140** | 17/46 |
| `MAE_q90` (adverse extent) | −0.554 | 18/46 | −0.719 | 9/46 |
| `TTP_med` (capture time) | −2.0 | 13/46 | 0.0 | 22/46 |
| outcome median | +0.040 | 23/46 | +0.016 | 25/46 |

Favourable-move *availability* is essentially the random baseline (harami's median MFE is **below**
random; AVWAP a hair above at coin-flip breadth 28/46). The outcome-median edge over random is tiny
(23–25/46 ≈ chance). This **reproduces the AVWAP-situation / EXP-047 finding on the 5-year data: move
availability is not the differentiator** — the entries do not sit on systematically larger gross moves
than random timing in the same regime.

**(b) The structure that exists lives in the OUTCOME SHAPE, and it is the CF-HA-HARAMI-001 signature.**

| Substrate | median-of-cell **means** | median-of-cell **medians** | cells median>0 | cells mean>0 |
|---|---|---|---|---|
| SUB-AVWAP | +0.157 | +0.150 | 26/46 | 30/46 |
| **SUB-HARAMI-PARTIAL-V2A** | **+0.000** | **+0.135** | **30/46** | **23/46** |
| SUB-RANDOM | +0.062 | +0.085 | 28/46 | 26/46 |

Harami: **median +0.135 but mean ≈ 0**; **33/46 cells have median > mean** (left-tail drag), median gap
+0.133. This is the *exact* CF-HA-HARAMI-001 trap reproduced on the disjoint 5-year data — a
median-positive edge whose mean is consumed by a catastrophic minority of losers (the audited evt0:
long, MAE=16 ATR, realized −15.6 ATR). AVWAP is, by contrast, roughly symmetric (mean +0.157 ≈ median
+0.150) — its weak edge lives in the mean too. No single domain/instrument drives the harami split; it is
substrate-wide (33/46), so the pooled "mean ≈ 0" is **not** masking a few outliers — it is the structure.

### Mechanism

- **Why MFE_med/MAE_q90/TTP ≈ random:** the four substrates are measured over the *same cell-level
  MA-segment adaptive cap* with *no exit*; gross lifetime excursions over a fixed regime-tempo window are
  dominated by the instrument×domain volatility, which the random control shares by construction. Entry
  *timing* shifts the excursion distribution only marginally. Hence the near-random gross geometry — and
  hence the family thesis: the lever is the **exit**, not the entry, and not raw move availability.
- **Why harami mean ≈ 0 while median > 0:** a small fraction of entries (~5–6% tail mass) suffer
  catastrophic adverse realizations (heavy left tail in the outcome distribution) that exactly offset the
  median-positive bulk. This is the bimodality EXP-074 identified and the reason EXP-071's raw-mean leg
  failed — now shown to persist on 5-year data.
- **Why only 1/184 cells resolves a dip (`m_anti` finite):** the Hartigan dip needs a resolvable
  *antimode* — a density valley between two separated modes. The catastrophe here is a **heavy continuous
  left tail**, not a cleanly separated second mode, so the MAE distribution is unimodal to the dip
  (dip_p median **0.976**; 184 finite p-values, 136 unique, range 0.032–1.0; the lone resolver is
  US500-1h AVWAP at dip_p=0.032, m_anti=1.79). **This is not a bug** — the dip path is exercised and
  varied — it is the genuine D9-anticipated property ("`m_anti` power-limited; the D3 adverse leg
  predominantly uses the `MAE_q90` fallback"). **Consequence for EXP-082:** the derived adverse leg
  `m_anti else MAE_q90` will use `MAE_q90` in 183/184 cells, as designed.

### Gate-shape check

The shape read **can** see the minority-catastrophe shape — but it is carried by `tailmass`/`q05` (on the
**outcome** distribution), **not** by `m_anti` (on the **MAE** distribution):

- `tailmass` (outcome, catastrophe boundary median−3·MAD): harami 0.0526 > random 0.0437, **31/46 cells
  harami > random** — the catastrophe-minority is visible and is larger for the conditioned entry than for
  random timing.
- `m_anti` (MAE): answers a *different* question — where to place an adverse **stop** given the
  adverse-excursion distribution — and correctly reports "no separated mode → use the quantile." Putting
  the dip on MAE and the tail-mass on outcome is **intentional and coherent**: each distribution answers
  its own EXP-082 question (stop placement vs catastrophe detection).
- The job `ASS` is structurally blind to (the subtle median-positive minority-catastrophe shape, EXP-078)
  is therefore carried here by the **descriptive `tailmass`/`q05` + mean-median gap**, exactly as the
  Phase-018 design intended (the separability gate, not `ASS`, is the binding shape-guard downstream). The
  read surfaces the shape; it does not adjudicate it.

**No gate is retro-edited.** The mechanism is recorded for Stage 6 and for EXP-082/083: a data-derived
exit's value must come from truncating the catastrophic left tail (the adverse/`S_adv` leg), since gross
favourable availability ≈ random; and EXP-083's separability gate is the crux — if cutting the tail also
removes the median edge, it is the same CF-HA-HARAMI-001 trap.

---

## Scope Compliance

| Check | Result |
|---|---|
| Member set = 46 EXP-080-READY cells (US500-4h, JP225-4h excluded) | PASS (184 = 4×46) |
| TRAIN-only; 0 slots; 0 counted TEST reads; ledger unchanged | PASS |
| Complexity budget (2 tests / 5 plots / 2 modules) | PASS (Hartigan dip + ASS bootstrap; 5 plots present; `capgeo_geometry` + in-module shape helper) |
| Frozen modules unedited | PASS (`capgeo_substrates`/`domain_bars`/`expectancy`/`ass`/`zigzag` hashes recorded; only `capgeo_geometry` added) |
| ASS non-binding (G-017) | PASS (no decision rests on `ASS`; `ass_discovery.json` carries the explicit non-binding note; D6 Guard (i) wired, 0 defers since all cells n≫60) |

---

## Issues

### Critical
None.

### Warning

- **W1 — Entries barely separate from random on gross geometry; the edge (such as it is) is a
  median-positive / mean-killed-by-tail outcome shape (mechanistic, not a defect).** *Materiality:* this
  does **not** move any D3-input value, denominator, sample, or the per-cell characterization — every
  number is correct and reproduces. It is verdict-material for the **downstream** family decision, so it
  is raised here for Stage 6 and EXP-082/083, not as a code fix. Evidence: Verdict Forensics
  (a)/(b) above (per-cell paired vs SUB-RANDOM; harami median +0.135 vs mean +0.000, 33/46 median>mean).
  *Action:* interpreter must report that gross capture availability ≈ random and that the only structure
  is the outcome-shape; EXP-082's derived exit must target the catastrophe tail; EXP-083 separability is
  the binding test. No rerun required.

### Info

- **I1 — `m_anti` resolves in only 1/184 cells (MAE distributions predominantly unimodal).** Expected
  per D9; the dip is genuinely exercised (184 finite, varied p-values). EXP-082's adverse leg will use the
  `MAE_q90` fallback in 183/184 cells, as designed. No action.
- **I2 — `generate_avwap_events` is re-run on the domain bars to recover per-event `direction`** (the
  frozen `avwap_entries` discards it; the frozen module may not be edited). Deterministic, bounded; does
  not change any sample/denominator/metric. Verified alignment (trigger order == entry order). No action.
- **I3 — SUB-RANDOM direction = prevailing in-progress MA-segment direction at the random entry bar**
  (random *timing*, same-regime *direction*); 1183/90467 random entries fall in MA-warmup (no valid
  in-progress move) and are correctly excluded. This is the intended "only timing is randomized"
  attribution null; documented in the analysis plan. No action.

---

## Materiality & Re-Audit Requirements

No Critical findings; **no fix or re-execution required**. Every finding is shown not to move a
verdict-bearing D3 number: W1 is a mechanistic interpretation of correct numbers (raised for Stage 6 /
EXP-082-083), and I1–I3 are expected, bounded, or documented design choices. The per-cell D3 inputs,
shape reads, and `ASS` disclosure are trustworthy for EXP-082's mechanical derivation.

**Audit verdict: PASS.** Cleared to Stage 6 (interpretation).
