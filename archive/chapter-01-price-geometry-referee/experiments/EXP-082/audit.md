# Audit Report: Experiment EXP-082 — Mechanical Exit Derivation from the Frozen D3 Rule

**Phase:** 018 (CF-CAPGEO-001) · **HYP:** HYP-003 (derive) · **Auditor:** experiment-auditor ·
**Date:** 2026-06-22 · **Run verdict under audit:** `DERIVATION_DELIVERED` (552/552 valid triples).

## Summary

- **Verdict:** **PASS** (0 Critical / 1 Warning / 3 Info)
- The frozen D0 §D3 rule is implemented faithfully and applied deterministically; an **independent
  re-derivation of all 552 triples from the raw EXP-081 summary reproduces every
  `(T_fav, S_adv, H_cap)` and `s_adv_source` to full float precision (0/552 mismatches).**
- The binding artifact (`xen.capgeo_exits.derive_barriers`) is pure/deterministic and the
  `run_metadata.json` sha256 matches the on-disk module, so EXP-083's hash-pin assertion will hold.
- The one substantive finding is **not** verdict-material for EXP-082 but is the mechanism the
  interpreter and EXP-083 must carry: the derived adverse stop is, by construction on this data, a
  generic wide `MAE_q90` quantile that sits *at the edge of* (not inside) the catastrophe it was
  designed to cut — the D3 rule's tail-engaging instrument (`m_anti`) is dormant in 551/552 rows
  (Warning W1; gate-shape finding).

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Per-row apply of the pure function; validity/identity/determinism orchestration matches the plan. |
| `code/run_experiment.py` | Edge cases | PASS | `_disposition` gates n<floor, `T_fav≤0`, `S_adv≤0`, `H_cap<1` (`run_experiment.py:140-150`); none triggered (all comfortably interior). |
| `src/xen/capgeo_exits.py` | Correctness (rule) | PASS | D1/D2/D3 legs match D0 §D3 verbatim; verified by independent re-derivation. |
| `src/xen/capgeo_exits.py` | Purity/determinism | PASS | No I/O, no globals, no RNG; `derive_barriers(s)==derive_barriers(s)`; frozen dataclasses. |
| both | Type safety | PASS | Type hints + docstrings on all public functions/dataclasses. |
| both | NaN handling | PASS | `m_anti` NaN (183/184) branched explicitly via `math.isfinite` (`capgeo_exits.py:_is_finite`, used in `_s_adv_d1_d3`/`_s_adv_d2`); never propagates into a barrier. |
| `code/run_experiment.py` | Holdout exclusion | PASS (strongest) | **No market data opened.** Only inputs: `EXP-081/results/substrate_cell_summary.parquet` + `run_metadata.json` (`run_experiment.py:89-90`). No `data/timebars/`, no `scan_parquet`, no domain build, no substrate regen (grep-confirmed). |
| `code/run_experiment.py` | Column hygiene | PASS | Consumes only the 14 approved D3-input columns via `.select(D3_INPUT_COLS)` (`run_experiment.py:74-77,90`); **no `ass_*` column read.** |
| `code/run_experiment.py` | Real-/synthetic-price | PASS (N/A) | No return/P&L/excursion/hit-rate computed; barriers carried in EXP-081 ATR units. The "expectancy"/"return" tokens at lines 13/14/150 are disclaimer text, not computation. |
| `code/run_experiment.py` | Separation of concerns | PASS | Pure compute in module; I/O, gates, plots, metadata in orchestration. |
| `code/run_experiment.py` | No magic numbers | PASS | Only `EVENT_FLOOR=30` (D9); barriers/`K_tail` inherited from EXP-081. |
| `code/run_experiment.py` | Organization/sections/import side-effects | PASS | VAL-001 sectioning; dirs created only in `main()` (`run_experiment.py:339-340`); `matplotlib.use("Agg")` before pyplot. |
| `code/run_experiment.py` | Progress/logging | PASS (N/A tqdm) | 184-row transform is sub-second; concise `logging`; no per-row noise. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 3 plots built from the single derived table; no reloads. |
| `code/run_experiment.py` | Verdict representation (per-stratum) | PASS | 552-row per-(cell,candidate) `disposition`/`valid` emitted; the process verdict `DERIVATION_DELIVERED` is a completeness/determinism flag, not a collapsed cross-stratum edge PASS/FAIL (no edge claim exists). EXP-076 C1 doctrine respected. |

## Numerical Validation

### Spot Checks (independent re-derivation — auditor's own implementation, not importing the module)

Re-applied the D0 §D3 rule directly from `substrate_cell_summary.parquet` for all 184 cells × 3
candidates and compared to `derived_candidates.parquet`:

- **checked = 552, mismatches = 0** (full float equality on `T_fav`, `S_adv`, `H_cap`, `s_adv_source`).
- **Lone `m_anti`-resolved cell — US500-1h SUB-AVWAP** (raw: `m_anti=1.794475`, `mae_q90=8.999404`,
  `mfe_med=3.913885`, `mfe_q40=3.022126`, `ttp_med=26`, `ttp_q75=51`):
  - D1 → `T_fav=3.913885`, `S_adv=1.794475` (`m_anti`), `H_cap=51` ✓
  - D2 → `T_fav=3.913885`, `S_adv=1.794475` (`m_anti`, since `min(1.79, 9.00)=1.79`) ✓
  - D3 → `T_fav=3.022126`, `S_adv=1.794475` (`m_anti`), `H_cap=26` ✓
  - Matches emitted output exactly. This is the only cell where the adverse leg engages the dip.
- **Unimodal cells** (e.g. EURUSD-15m SUB-HARAMI-PARTIAL-V2A: `mfe_med=2.913`, `mae_q90=8.971`,
  `m_anti=NaN`): all three candidates take `S_adv=MAE_q90=8.971` (`mae_q90` source), confirmed.
- **`H_cap` integerization:** verified `max(1, round-half-even(q))`: `51.0→51`, `26.0→26`, `0.4→1`,
  `2.5→2`, `3.5→4`, `1.5→2` (banker's rounding confirmed — `_h_cap_bars`).

### Range Checks

| Metric | Expected | Actual (across 552) | Pass? |
|--------|----------|---------------------|-------|
| `T_fav` (ATR) | > 0 | D1/D2 [2.420, …] med 3.310; D3 [1.811, …] med 2.558 | YES |
| `S_adv` (ATR) | > 0 | [1.794, …] med 9.209 | YES |
| `H_cap` (bars) | ≥ 1 | D1/D2 [34, 73]; D3 [17, 41] | YES |
| `disposition` | all OK | 552 OK / 0 UNDERPOWERED / 0 DEGENERATE | YES |
| `s_adv_source` | {m_anti, mae_q90} | 3 m_anti (US500-1h-AVWAP ×3) / 549 mae_q90 | YES |

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

The headline is per-cell-total by construction (no pooling/aggregation/equal-weighting), but I
independently re-derived per stratum to confirm no cell silently disagrees with the pooled counts:

| Headline | Independent per-stratum recount | Agrees? | Masking? |
|---|---|---|---|
| 552/552 valid | recounted dispositions: 552 `OK`, 0 else | YES | None — every (cell,candidate) individually `OK`. |
| `s_adv` 1 `m_anti` / 183 `mae_q90` per candidate | recounted across 184 cells/candidate: exactly the US500-1h-AVWAP cell uses `m_anti`; all 183 others `mae_q90` | YES | None — the single resolver is identified by name, not an aggregate. |
| D1≡D2 184/184 | recounted `(T_fav,S_adv,H_cap)` equality D1-vs-D2 per cell: **0 divergent** | YES | **Disclosed, not masked** — see Mechanism + W1: D1=D2 because the one resolved `m_anti` (1.79) is `< MAE_q90` (9.00), so `min()` returns `m_anti`=D1's value; everywhere else both use `MAE_q90`. |
| harami identity | `SUB-HARAMI-PARTIAL-V2A` vs `SUB-HARAMI-V2A-ADVNONE`: 46×3 triples bit-identical (`harami_identity_ok=true`) | YES | None — the two share one entry population by construction. |

**The pooled counts are genuine per-stratum facts, not aggregates hiding heterogeneity.** The only
heterogeneity that exists (US500-1h-AVWAP being the lone dip-resolver) is surfaced explicitly, not
buried.

### Mechanism — *why* `DERIVATION_DELIVERED`, and what the derived exits actually are

1. **Why all 552 valid (not a close call):** every EXP-081 input quantile is comfortably interior —
   `T_fav` ≥ 1.81 ATR, `S_adv` ≥ 1.79 ATR, `H_cap` ≥ 17 bars; no cell approaches the degeneracy or
   ≥30-event floor (EXP-081 had `n_usable` ∈ [46, 5535], 0 underpowered). The frozen rule maps
   well-conditioned inputs to well-defined triples; the process verdict is robust, not marginal.

2. **Why D2's tail-robustness lever is dormant (D1≡D2):** D2 ("tighten the stop to the dip") was the
   one candidate designed to *differ* by cutting the catastrophic-minority tail with a tighter stop.
   Its distinguishing operation `min(m_anti, MAE_q90)` only diverges from D1 when a cell has
   `m_anti > MAE_q90`. `m_anti` resolves in **1/184** cells, and there it is **1.79 < 9.00**, so
   `min` returns `m_anti` — identical to D1. Net: **the family registers 3 candidates but emits only 2
   distinct exit definitions on this snapshot** (D1=D2; D3 differs only by its q40 target + median time
   cap). The "tail-robust" thesis is **untested by construction here** — not because the rule is wrong,
   but because the data has no separated mode for the dip stop to engage.

3. **Why the catastrophe-engaging guard is inert (the deepest "why"):** D0 §D3 left-tail-parameterized
   the adverse leg on `m_anti` *specifically* as the structural guard against the CF-HA-HARAMI-001
   "harvest-the-median-leave-the-catastrophe" trap. But EXP-081 found the catastrophe is a **heavy
   continuous left tail, not a separated second mode** (`dip_p` median 0.976; only 0.5% of cells dip
   below 0.05). So the adverse leg falls back to a **generic `MAE_q90` stop in 551/552 rows**, and that
   stop (~9.2 ATR) sits almost exactly **at** the catastrophe magnitude `|q05|` (~9 ATR): median
   `S_adv − |q05|` = **−0.008 ATR**, with the stop landing *outside* the catastrophe in ~50% of cells.
   Combined with `T_fav/S_adv` ≈ **0.35** (modest target, wide stop), the derived exit is, geometrically,
   **the same wide-stop shape that lets the median print while the catastrophe completes** — the prior
   family's failure geometry reproduced inside the derived exit. Per substrate the picture is uniform
   (median `S_adv−|q05|`: AVWAP +0.06, harami −0.0001, random −0.08), so this is a structural property of
   the rule-meets-data, not a one-substrate artifact.

**Consequence for the pipeline (carry-forward, not an EXP-082 verdict):** EXP-083's **separability gate
(S2)** is pre-loaded as the crux exactly as the Phase-018 design anticipated — the derived stops as
parameterized are unlikely to truncate the catastrophe, so the live question becomes whether *any* exit
geometry can cut the tail without removing the median edge. EXP-082 has faithfully *built* the guard the
rule specified; it has not, and was not asked to, demonstrate the guard *works*.

### Gate-shape check

- **Binding "gate" in EXP-082:** none in the edge sense — the only gate is the validity/estimability
  gate, which is a location/positivity check appropriate to its job (is each quantile a usable
  barrier?). It is the right instrument for the question it answers.
- **Shape mismatch worth recording (for the interpreter / EXP-083):** the **derivation rule's own
  adverse instrument** (`m_anti`, a *separated-mode* dip detector) is the wrong instrument for the
  *shape EXP-081 found* (a continuous heavy tail). This is the same family of blind spot G-017 flagged
  for `ASS` — a mode/dip detector cannot see an unseparated tail. The rule degrades gracefully (falls
  back to `MAE_q90`), so this does **not** corrupt any EXP-082 number, but it means the "tail-robust"
  differentiation the rule was built to express is inactive on this data. Recorded for Stage 6 / EXP-083;
  **gate not retro-edited** (the rule is frozen at D0; this is an honest, D9-anticipated outcome).

## Scope Compliance

- Analysis plan followed: **YES** (Steps 1–8 all implemented; D2 operationalized as the plan's frozen
  `min(m_anti, MAE_q90)`).
- Deviations: **none.**
- Complexity budget: **0/0 tests, 3/≤3 plots, 1/≤1 module** — compliant.
- Holdout exclusion verified: **YES** (no market data read at all; EXP-081 `holdout_untouched` asserted
  and carried; `counted_test_reads=0`, `candidate_slots=0`).
- Hard boundary respected: **YES** — no exit simulation, no P&L/expectancy, no G-018a screen, no
  separability gate, no WF fold, no `ASS` adjudication. The structural-guard read (Step 7) computes only
  comparisons of derived barriers to EXP-081 statistics — **no realized return/hit-rate/expectancy**
  (confirmed by inspection of `derive_table`, `run_experiment.py:131-160`).

## Faithfulness / Determinism / Hash-pin

- **Purity/determinism:** `derive_barriers` re-run byte-identical; `determinism_replay_byte_identical=true`;
  determinism fingerprint recorded (`run_metadata.json`).
- **D2 distinct-from-D1 (faithfulness):** synthetic `m_anti=6 > MAE_q90=4` → D1 keeps `S_adv=6.0`
  (`m_anti`), D2 tightens to `S_adv=4.0` (`mae_q90`), D3 keeps `6.0`. The functions are genuinely
  distinct; they merely coincide on this snapshot. ✓
- **Hash-pin:** on-disk `sha256(capgeo_exits.py)` == `run_metadata.derive_barriers_module_sha256`
  (`34d03f45…`); on-disk `sha256(substrate_cell_summary.parquet)` == pinned `exp081_input.summary_sha256`.
  EXP-083's hash-pin assertion will hold against the current module. ✓
- **Provenance assertion:** all 8 EXP-081 fingerprint checks pass
  (`verdict=CHARACTERISATION_DELIVERED`, 184 cells, 0 underpowered, holdout untouched, 0 counted reads,
  height 184, n_usable≥30, substrate set) — `derivation_validity.json:provenance.checks`.

## Issues

### Critical

None.

### Warning

1. **The derived adverse stop does not engage the catastrophe it was designed to cut (gate-shape /
   mechanism).**
   - File: `python/src/xen/capgeo_exits.py:_s_adv_d1_d3 / _s_adv_d2`; evidence in
     `results/derived_candidates.parquet` (`s_adv_source`, `s_adv_minus_absq05`) and
     `EXP-081/results/substrate_cell_summary.parquet` (`dip_p`, `q05`).
   - Description: `m_anti` resolves in 1/184 cells (`dip_p` median 0.976), so the left-tail-parameterized
     adverse leg falls back to `MAE_q90` in 551/552 rows; that stop (~9.2 ATR) sits at the catastrophe
     edge (median `S_adv−|q05| = −0.008`), and D2's tail-tightening lever is dormant (D1≡D2 184/184).
   - **Materiality reasoning (why Warning, not Critical):** this **cannot move any EXP-082
     verdict-bearing number** — the rule was applied faithfully (0/552 re-derivation mismatches), all
     552 triples are valid, the verdict is `DERIVATION_DELIVERED` regardless of whether the stop is
     wide or tight, and EXP-082 makes **no edge/separability/tradability claim**. The finding is about
     what the *next* experiment will find, not whether this one is correct. It is therefore
     document-and-proceed, but it is the single most important thing for Stage 6 and EXP-083 to carry:
     the separability gate (S2) is the crux and is pre-loaded toward "the tail truncation does little."
   - Fix: none for EXP-082 (the rule is frozen and faithfully applied). For the family, this is the
     operator/EXP-083 question — whether a tail-cutting exit is even available given a continuous (not
     separated) catastrophe. An optional future re-parameterization of the adverse leg to a
     *quantile-of-the-tail* rather than a *dip-mode* detector would be a new D0-amendment, not an
     EXP-082 fix.

### Info

1. **3 candidates → 2 distinct exit definitions on this snapshot.** D1≡D2 (184/184); D3 differs only by
   the q40 target + median time cap. EXP-083's {candidate × stratum} Holm grid should account D1 and D2
   as numerically identical here (they remain distinct functions for the per-fold re-fit, where a
   subsample could resolve `m_anti > MAE_q90`). Already disclosed in `derivation_validity.json`.
2. **`H_cap` integerization is deterministic banker's rounding + floor at 1.** All `ttp` quantiles are
   near-integer (e.g. 51.0, 26.0) so rounding is rarely active; the floor never triggered (min q75
   H_cap=34, min med H_cap=17). No ambiguity in the emitted caps.
3. **Plots are descriptive disclosure of definitions, not results.** Plot 3 (`T_fav` vs `S_adv` with
   `|q05|` sizing) visually encodes the W1 mechanism; correct and non-adjudicative.

## Materiality & Re-Audit Requirements

- **No blocking findings.** The single Warning is shown not to move any verdict-bearing number (the rule
  is faithfully applied; the verdict, barriers, validity flags, source labels, and accounting all
  reproduce exactly). No fix or re-run is required for EXP-082.
- **Re-audit:** not required. The Warning and all three Info notes are carry-forward context for Stage 6
  (interpretation) and EXP-083 (separability), explicitly recorded above.

**Audit verdict: PASS (0C / 1W / 3I).** The derivation is faithful, deterministic, holdout-clean, and
hash-pinned; the binding artifact is ready for EXP-083 to import. The mechanism is understood and
documented: EXP-082 correctly *builds* the D3-specified catastrophe guard, and the audit shows that on
this data the guard's tail-engaging instrument is dormant — making EXP-083's separability gate the crux,
exactly as the Phase 018 design predicted.
