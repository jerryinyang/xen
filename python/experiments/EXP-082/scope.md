# Experiment: EXP-082 — Mechanical Exit Derivation from the Frozen D3 Rule (3 Derived Candidates × 184 Member Substrate-Cells, 5-Year Data)

**Phase:** 018 (CF-CAPGEO-001 data-derived exit / capture geometry; checkpoint
`2026-06-20-018-capgeo-exit-geometry`, **G0 PASS 2026-06-21**) · **HYP:** HYP-003 ·
**Registry:** `CF-CAPGEO-001` Phase 018 batch (multiplicity-registry) — derived candidates
`D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT` already registered at D0 under
`/EXIT-DERIVED` (no new countable item) · **Candidate slots:** 0 (derivation; no screen) ·
**TEST reads:** 0 counted (no market-data read at all — pure transformation of EXP-081 TRAIN outputs).

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`docs/signal-registry/test-read-ledger.md`, re-materialized 2026-06-21 on VAL-005 PASS) shows **all
16 instruments × {15m,1h,4h} = 48 strata at 0/2 counted reads, open** (EURUSD fully eligible, clean
slate — D8). **EXP-082 reads no market data**: it consumes only EXP-081's already-computed per-cell
TRAIN statistics (`EXP-081/results/substrate_cell_summary.parquet`, a TRAIN-only disclosure read) and
applies the frozen D3 mechanical mapping. No TEST stratum is sliced, no analysis-set row is re-read, the
final-30% global holdout is never touched, and **no stratum-specific inference** is performed. The
ledger is **unchanged**; no per-stratum tally moves (EXP-074/075/081 precedent — derivation off
TRAIN-only inputs).

**Gating precondition:** **EXP-081 CHARACTERISATION_DELIVERED 2026-06-22 (audit PASS 0C/1W/3I)** —
184/184 member substrate-cells delivered the frozen D3 inputs (`MFE_med`, `MFE_q40`, `TTP_med`,
`TTP_q75`, `MAE_q90`, `m_anti`, `tailmass`, `q05`); **0 cells below the 30-event floor** (`n_usable`
46–5535); `m_anti` NaN in 183/184 cells (lone resolver US500-1h AVWAP) → the D3 adverse leg uses the
`MAE_q90` fallback almost everywhere, **exactly as the D9 bite-check anticipated**.

**Analog:** EXP-075 (TRAIN-design-and-lock of a frozen rule; deterministic, carried nowhere until its
test) / EXP-033 (mechanical selection rule frozen on TRAIN, applied downstream). **Deliverable boundary
(operator decision 2026-06-22):** **derive + lock only** — EXP-082 emits the per-cell barrier triples,
confirms quantile estimability (D9), and **hash-pins the frozen derivation function**; it applies **no
exit, runs no P&L simulation, and runs no G-018a / separability / WF** (all of which are EXP-083). The
barrier triples are computed **once on the full EXP-081 TRAIN sub-split** as the registered candidate
definition; the **binding artifact is the frozen function** — EXP-083 calls the *same* hash-pinned
function per WF fold-TRAIN for the causal re-fit (D3/D5/D4.1), with no human selection between folds.

**Context:** Third experiment of Phase 018, the **derive** step of the characterize → derive → test
slate (design §2/§3, D0 §D2/§D3). The reverse-direction posture of this family is: *let each substrate's
own realized return structure (EXP-081) dictate the exit geometry, via a rule frozen before the
structure was seen.* EXP-082 is the act of applying that frozen rule. **It introduces no new
measurement and no new degree of freedom** — the entire content is the predeclared D3 mapping from
per-cell statistics to a triple-barrier `(T_fav, S_adv, H_cap)`, plus the validity/estimability check
and the hash-pin that make EXP-083's "many candidates, one honest counted read" legitimate (D4.1).

---

## Hypothesis / Exploratory Question

Mechanical derivation (no market-edge claim, no candidate screen, no edge/pass/fail verdict): applying
the **frozen D3 triple-barrier derivation rule** (D0 §D3) to the EXP-081 TRAIN per-cell statistics
yields, for every member substrate-cell, a **well-defined, estimable** barrier triple
`(T_fav, S_adv, H_cap)` for each of the three derived candidates `D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`,
`D3-CAPTURE-EFFICIENT`, with the adverse leg always defined (D9: undefined-rate 0.000) and no candidate
formed for any cell below the ≥30-event floor (none expected — EXP-081 had 0 underpowered cells).

The experiment verdict is **DERIVATION_DELIVERED** — the per-cell triples, the validity report, the
frozen-function hash-pin, and the determinism replay are produced for every member cell, whatever the
numeric values. There is **no edge, tradability, viability, or pass/fail claim** (that is EXP-083).

## Question

For each of the 184 member substrate-cells (4 substrates × 46 instrument×domain member cells), applying
the frozen D3 rule to the EXP-081 statistics:

1. **`D1-MEDIAN-CAPTURE`** — `T_fav = MFE_med`, `S_adv = m_anti else MAE_q90`, `H_cap = TTP_q75`
   (central favourable capture).
2. **`D2-TAIL-ROBUST`** — `T_fav = MFE_med`, `S_adv = m_anti` *tightened to the dip* (unimodal →
   `MAE_q90`), `H_cap = TTP_q75` (does cutting the catastrophic-minority tail tighten the stop?).
   The exact operationalization of "tightened to the dip" vs `D1`'s `m_anti` is fixed in the Stage-2
   analysis plan from the frozen D3 wording; it differs from `D1` **only** where `m_anti` resolves
   (1/184 cells), and equals `D1`'s `MAE_q90` fallback elsewhere.
3. **`D3-CAPTURE-EFFICIENT`** — `T_fav = MFE_q40`, `S_adv = m_anti else MAE_q90`, `H_cap = TTP_med`
   (does an earlier / higher-hit-probability favourable target with a shorter time cap capture more?).
4. **Validity / estimability (D9):** confirm every input quantile
   (`MFE_med`/`MFE_q40`/`TTP_q75`/`TTP_med`/`MAE_q90`) is finite/non-degenerate on each cell, the
   adverse leg (`m_anti else MAE_q90`) is well-defined for every cell, and `H_cap ≥ 1` bar,
   `T_fav > 0`, `S_adv > 0`. Disclose the `m_anti`-resolved vs `MAE_q90`-fallback split per candidate
   (expected 1 vs 183).
5. **Structural-guard disclosure (non-binding):** record, per cell, `T_fav` vs `S_adv` (favourable
   target vs adverse stop, ATR) and the relation of `S_adv` to the EXP-081 catastrophe read
   (`q05`/`tailmass`), so the D3 "engage the catastrophic-minority boundary" intent (D0 §D3) is visible
   for EXP-083's separability argument — **as disclosure only**; no selection or adjudication here.

## Scope Boundaries

- **Input data view:** **EXP-081 outputs only** — `EXP-081/results/substrate_cell_summary.parquet`
  (the per-substrate-cell frozen D3-input table; 184 rows) plus `EXP-081/results/run_metadata.json`
  (seeds, module hashes, frozen constants, EXP-080 reconciliation) for provenance assertion. **No
  `data/timebars/` read, no domain-bar build, no substrate re-generation, no per-event re-computation.**
  EXP-082 is a deterministic transformation of EXP-081's locked TRAIN statistics.
- **Provenance assertion (binding):** before deriving, assert the consumed EXP-081 summary matches its
  `run_metadata.json` fingerprint — `verdict == "CHARACTERISATION_DELIVERED"`, `n_substrate_cells == 184`,
  `n_underpowered_cells == 0`, `holdout_untouched == true`, `counted_test_reads == 0`, and the
  `capgeo_geometry`/`capgeo_substrates`/`domain_bars` module hashes recorded in EXP-081 — so EXP-082 is
  provably derived from the audited EXP-081 result, not a stale or altered copy.
- **Candidates (three, frozen at D0 §D2/§D3; none tuned):** `D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`,
  `D3-CAPTURE-EFFICIENT`, under the registered `/EXIT-DERIVED` branch. No fourth candidate, no variant,
  no parameter grid — the rule **is** the candidate set.
- **Grid (member set):** 3 derived candidates × **184 member substrate-cells** = **552 barrier triples**
  (4 substrates × 46 EXP-080-READY instrument×domain cells; US500-4h, JP225-4h `COVERAGE_EXCLUDED`; no
  DE30). The harami substrates (`SUB-HARAMI-PARTIAL-V2A`, `SUB-HARAMI-V2A-ADVNONE`) share one entry
  population (EXP-080/081), so their derived triples coincide per cell by construction — asserted and
  disclosed, not pooled.
- **Time range:** the derivation inherits EXP-081's read region — **first 70% of the analysis set only**
  (`[0, train_cutoff)`, the nested TRAIN sub-split). EXP-082 reads no rows itself; the analysis-TEST
  stratum and the final-30% global holdout are **never** loaded, inspected, counted, or used. The
  per-fold causal re-fit on deeper analysis-set folds is **EXP-083's** WF machinery, not run here.
- **Global holdout:** excluded from all analysis (mandatory). Never a fold; not read here or by the
  inputs (EXP-081 `holdout_untouched == true`, asserted).
- **Look-ahead bias prevention:** the derivation is a pure function of TRAIN-only summary statistics;
  no future data exists in the input. The frozen function is **causal by construction** — it maps a
  cell's TRAIN statistics to a barrier triple with no cross-fold or forward dependency, so EXP-083 can
  call it per fold-TRAIN without leakage.
- **Real-price discipline (binding):** every input statistic was computed by EXP-081 on **real** domain
  OHLC (ATR-normalized); EXP-082 carries those ATR-unit barriers forward unchanged. No HA / Renko /
  synthetic price enters anywhere. Barriers are expressed in **ATR units** (the EXP-081 normalization);
  `H_cap` is in **domain bars**.
- **Exclusions:** **no exit applied, no trade simulated, no P&L / expectancy / capture computed** (that
  is EXP-083); **no G-018a gross TRAIN screen, no separability gate (S1/S2), no frozen referee suite, no
  binding or discovery `ASS` adjudication** (EXP-083 / D4); **no per-fold WF re-fit emulation** (EXP-083
  / D5); no grid search, sweep, or tuning of any barrier (the barriers *are* the measured quantiles —
  D3); no post-hoc selection among candidates or cells (the rule is total over the member set); no
  cross-cell / cross-substrate / cross-candidate pooling as a binding statistic (per-stratum default,
  LESSON-001; any aggregate is disclosure only); no new market-data contact; nothing tuned or chosen
  against any EXP-081 *narrative* beyond the predeclared mechanical D3 mapping (**freeze the rule, not
  the story** — D0 §D3).

## The Derivation (per member substrate-cell)

For every member substrate-cell, read its EXP-081 row and emit three barrier triples by the frozen
D3 mapping (D0 §D3, verbatim):

| Candidate (countable item) | `T_fav` | `S_adv` | `H_cap` |
| --- | --- | --- | --- |
| `D1-MEDIAN-CAPTURE` | `MFE_med` | `m_anti` else `MAE_q90` | `TTP_q75` |
| `D2-TAIL-ROBUST` | `MFE_med` | `m_anti` (tightened to the dip; unimodal → `MAE_q90`) | `TTP_q75` |
| `D3-CAPTURE-EFFICIENT` | `MFE_q40` | `m_anti` else `MAE_q90` | `TTP_med` |

- **Adverse leg is left-tail-parameterized, not a symmetric mirror** (D0 §D3) — every candidate's stop
  engages the catastrophic-minority boundary `m_anti` where it resolves, falling back to `MAE_q90`. This
  is the structural guard against the CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" trap;
  EXP-082 only *constructs* the guard, EXP-083 *tests* whether it works (separability).
- **EXP-042 guard (binding):** `(T_fav, S_adv, H_cap)` are **exit** barriers on the held position of
  frozen-entry events. **None filters, selects, or alters the entry event population** — every candidate
  applies to the identical EXP-080/081 frozen-substrate event set; no denominator changes. EXP-082 emits
  definitions only and so cannot change any population; the invariant is asserted at EXP-083.
- **Frozen function (the binding artifact):** the mapping above is implemented once as a pure,
  deterministic function `derive_barriers(cell_stats, candidate) -> (T_fav, S_adv, H_cap)` and
  **sha256-pinned** in `run_metadata.json`. EXP-083 imports and calls the identical function per
  fold-TRAIN; the static full-TRAIN triples emitted here are the registered candidate values +
  estimability evidence, not a separate rule.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **No ratio / percentage / expectancy metric is computed** (no evaluation), so there is no denominator
  or zero-baseline exposure on the outcome side. The only "denominators" are the EXP-081 per-cell event
  counts already disclosed there; EXP-082 carries the `n_usable` through and applies the ≥30-event floor
  as a **gate on candidate formation**, never as a divisor.
- **Estimability accounting:** report per candidate the count of cells with a well-defined triple
  (expected 184/184), the `m_anti`-resolved vs `MAE_q90`-fallback split (expected 1 vs 183), and any
  cell below the ≥30-floor (expected 0) — each as a count over the 184-cell member denominator, shown
  explicitly, never as `0/0`.
- **Degenerate-quantile guard:** a cell whose `MFE_q40 == MFE_med == 0` (no favourable excursion) or
  `MAE_q90 == 0` (no adverse excursion) would yield a degenerate barrier; flag as
  `DEGENERATE_DISCLOSED` and form no candidate for that cell (none expected — EXP-081 `MFE_med` ~3.2 ATR,
  `MAE_q90` ~9 ATR). `H_cap` is floored at 1 bar.

## Frozen Constants (predeclared at D0/G0; recorded here pre-derivation)

- **Derivation rule:** the D0 §D3 mapping, verbatim (table above). No constant in the rule is free —
  the barriers *are* the EXP-081 measured quantiles.
- **Event floor:** **≥ 30** events per cell to form a derived candidate (D9 §D3).
- **Catastrophe boundary (carried from EXP-081, not recomputed):** `K_tail = 3.0` (the `m_anti` /
  `tailmass` boundary was already fixed at the D9 bite-check and applied in EXP-081); EXP-082 consumes
  `m_anti`, `MAE_q90`, `tailmass`, `q05` as given.
- **Units:** barriers in **ATR units** (EXP-081 normalization, Wilder ATR(14)); `H_cap` in **domain
  bars**.
- **Seeds:** none required (deterministic transformation, no RNG); a second full pass is byte-identical
  (D10). Any incidental ordering is fixed and recorded in `run_metadata.json`.

## Success / Failure / Inconclusive Criteria

- **DERIVATION_DELIVERED (experiment verdict):** for all 184 member substrate-cells, all three derived
  candidates receive a well-defined barrier triple `(T_fav > 0, S_adv > 0, H_cap ≥ 1)` by the frozen D3
  rule, with the adverse leg defined in every cell; the per-candidate estimability/fallback accounting
  is reported; the frozen derivation function is sha256-pinned; and a second pass reproduces every triple
  byte-identically.
- **Cell-level INCONCLUSIVE:** a cell below the ≥30-event floor (or with a degenerate input quantile) is
  `UNDERPOWERED_DISCLOSED` / `DEGENERATE_DISCLOSED` and **forms no derived candidate** for that cell
  (recorded, never silently dropped). None expected.
- **Evidence AGAINST (process-level — HALT):** non-determinism (second-pass triples not identical); an
  EXP-081 provenance-fingerprint mismatch (consumed summary not the audited CHARACTERISATION_DELIVERED
  result); a frozen-rule transcription error (emitted triple not equal to the D0 §D3 mapping on a spot
  re-derivation); any holdout-fence / real-price-discipline violation; or the harami-identity assertion
  failing (the two harami substrates' triples must coincide per cell). Any of these halts and routes to a
  fix — they indicate an implementation/provenance defect, not a result.
- There is **no edge / pass / viability / tradability verdict** (0 slots, no evaluation). Only the
  derived definitions and their validity are produced.

## Complexity Budget

- **Max statistical tests: 0** — EXP-082 runs no inference. The `m_anti` dip and `ASS` bootstrap were
  EXP-081's; EXP-082 consumes their outputs. (The "tightened to the dip" `D2` rule uses EXP-081's
  already-computed `m_anti`/`dip_p`; it fits no new model.)
- **Max visualisations: ≤ 3** — (i) per-candidate barrier-triple heatmap/table by substrate × domain
  (`T_fav`, `S_adv`, `H_cap`); (ii) `S_adv` source split (`m_anti`-resolved vs `MAE_q90`-fallback)
  across the member set; (iii) `T_fav` vs `S_adv` (favourable-vs-adverse, ATR) scatter by substrate with
  the EXP-081 `q05`/catastrophe context overlaid (the structural-guard disclosure). All from the single
  derivation pass's bounded inputs (no reloads). Plots are descriptive disclosure of the derived
  definitions, not results.
- **Max new code modules: ≤ 1** under `python/src/xen/` — the frozen, hash-pinned derivation function
  (e.g. `xen.capgeo_exits.derive_barriers`), the **binding shared artifact** EXP-083 will import for the
  per-fold causal re-fit. **Reuse** EXP-081's `xen.capgeo_geometry` column conventions; no edits to any
  frozen generator/detector/geometry module. If the mapping is trivial enough to live cleanly in the
  experiment script *and* be importable by EXP-083, a module is still preferred so the hash-pin governs
  both experiments.

## Data Requirements

Read `EXP-081/results/substrate_cell_summary.parquet` (184 rows) and `EXP-081/results/run_metadata.json`;
assert the EXP-081 provenance fingerprint (verdict / counts / holdout flag / module hashes). For each of
the 184 cells, apply the frozen `derive_barriers` function to produce the three triples; run the
estimability / well-definedness / degeneracy checks and the per-candidate accounting; assert the
harami-substrate triple identity; emit the derived-candidate table, a validity report, the sha256
hash-pin of the derivation function, and `run_metadata.json` (input fingerprint, function hash,
frozen-constant versions, determinism replay result); render the ≤3 bounded disclosure plots from the
collected table. `tqdm` over the 184-cell loop is optional (the transform is fast); memory is trivially
bounded (one small table in, one small table out). Outputs:

- `results/derived_candidates.parquet` (and `.csv`) — 552 rows (184 cells × {D1,D2,D3}) with
  `instrument, domain, substrate, candidate, T_fav, S_adv, H_cap, s_adv_source ∈ {m_anti, mae_q90},
  n_usable, valid, disposition`.
- `results/derivation_validity.json` — per-candidate estimability/fallback/floor accounting + the
  determinism replay fingerprint.
- `results/run_metadata.json` — EXP-081 input fingerprint, `derive_barriers` sha256, frozen constants,
  module hashes, `holdout_untouched: true`, `counted_test_reads: 0`, `candidate_slots: 0`.

Expected runtime: seconds (pure transformation; no market-data load).

### Standard Loading Pattern (EXP-081 TRAIN-only outputs; no market data)

```python
import json, polars as pl
from pathlib import Path

EXP081 = Path("python/experiments/EXP-081/results")
meta = json.loads((EXP081 / "run_metadata.json").read_text())
assert meta["verdict"] == "CHARACTERISATION_DELIVERED"
assert meta["n_substrate_cells"] == 184 and meta["n_underpowered_cells"] == 0
assert meta["holdout_untouched"] and meta["counted_test_reads"] == 0

cells = pl.read_parquet(EXP081 / "substrate_cell_summary.parquet")   # 184 rows, TRAIN-only stats
# triples = derive_barriers(cells)   # frozen D3 mapping; no market data, no TEST/holdout row touched
```

## Suggested Direction (non-binding)

Implement the D0 §D3 mapping as one small pure function in `python/src/xen/` so the *same* hash-pinned
function is the binding artifact for both EXP-082 (full-TRAIN application) and EXP-083 (per-fold causal
re-fit). Drive a single pass over the 184 EXP-081 rows, emit the three triples per cell, and spend the
rest of the experiment on **provenance and validity discipline** — the EXP-081 fingerprint assertion,
the well-definedness/degeneracy guards, the `m_anti`-vs-`MAE_q90` accounting, the harami-identity
assertion, and the byte-identical determinism replay. Keep the structural-guard read (`T_fav` vs
`S_adv` vs `q05`) explicitly **disclosure-only** so the derive/test boundary the D0 draws stays clean:
EXP-082 builds and locks the exits; EXP-083 alone decides whether they capture anything.
