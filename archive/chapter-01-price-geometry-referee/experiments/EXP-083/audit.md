# Audit: EXP-083 — TRAIN-Only Candidate Screen Behind the Separability Gate (CF-CAPGEO-001 Phase 018 / HYP-004a)

**Auditor stage:** Stage 5 (consolidated pipeline)
**Date:** 2026-06-22
**Verdict produced by run:** `SCREEN_DELIVERED` — `n_valid_candidates = 28`, `valid_set_sha256 = 0796530c…`, `determinism_ok = true`, `holdout_untouched = true`, `test_stratum_touched = false`, `counted_test_reads = 0`.

**Audit verdict (first pass):** **REVISE — one Critical (verdict-material) finding forces a fix + re-execution before Stage 6.**
The binary screen verdict (`SCREEN_DELIVERED`, "≥1 valid candidate") is **sound and robust** — it cannot flip. But the **hash-pinned valid-candidate set is the experiment's binding deliverable** (EXP-084 imports it verbatim and asserts its sha256 before spending a lifetime TEST read), and a demonstrated control-seed inconsistency changes a member of the binding 7-survivor subset and therefore changes `n_valid` and the pinned hash. That is verdict-material to the hand-off and must be fixed and re-pinned, not documented-and-proceeded.

> **RE-AUDIT verdict (post-fix re-execution, 2026-06-22, run `fa4035f3…`): PASS.** C1 and W1 were fixed (operator-directed: dedupe harami → single stratum; per-candidate `m_cell`) and the experiment re-run. The Critical control-seed inconsistency is gone, the mechanism is unchanged, and the new hash-pinned set is trustworthy. **No remaining Critical/verdict-material finding — the experiment may advance to Stage 6.** Full re-audit detail in the *Re-Audit* section at the end of this file. Sections below describe the **superseded first-pass run** (28 survivors, sha `0796530c…`) and are retained for provenance.

---

## Artifacts Reviewed

- `scope.md`, `analysis-plan.md`
- `code/run_experiment.py` (orchestration)
- `python/src/xen/capgeo_screen.py` (new harness — resolvers, bootstrap, S1/S2)
- frozen imports: `capgeo_exits.derive_barriers` (sha256-pinned), `capgeo_substrates`, `capgeo_geometry`, `domain_bars`
- `results/screen_results.parquet` (2760 rows), `valid_candidate_set.json` (28 members), `run_metadata.json`
- `governance/pre-execution-review.md` (5 Stage-4-routed materiality items)

---

## Confirmations (passed)

| Check | Result | Evidence |
|---|---|---|
| Pinned `derive_barriers` sha256 == EXP-082 | **PASS** | `_assert_provenance` hashes `capgeo_exits.py`, asserts `== e82.derive_barriers_module_sha256` **and** `startswith("34d03f45")`; metadata records `34d03f45bc036a5e…`. |
| EXP-080/081/082 provenance fingerprints | **PASS** | Verdicts + `holdout_untouched`/`counted_test_reads==0`/cell counts asserted before any read (`run_experiment.py:562-580`). HALT on mismatch. |
| Holdout / TEST discipline | **PASS** | `load_first70` (VAL-005) loads first-70% analysis slice only; screen slices `[0, int(analysis_rows*0.7))` (TRAIN ≈ first-49% of file); analysis-TEST and final-30% holdout never sliced. `holdout_untouched=true`, `test_stratum_touched=false`. |
| Look-ahead / causality | **PASS** | All resolvers scan only `entry+1..min(cap, n_bars-1)`; adverse-first (P15) intrabar tie-break; TRAIN-edge-truncated windows → `CENSORED` (excluded with record, never marked at the edge). Derived barriers from the causal pinned function. |
| Real-price discipline | **PASS** | Every return is real domain OHLC (`_real_ohlc` high/low/close) in ATR units (Wilder ATR(14)); no HA/Renko brick price enters any metric. |
| EXP-042 same-denominator invariant | **PASS** | `n_usable` (entry population) is identical across all 15 candidates within every cell (verified: AUDUSD-1h-harami all `n_usable=988`). Exits vary only `n_resolved` via legitimate censoring/VP-invalidity, never the entry denominator. |
| Harami entry **identity** | **PASS (structural)** | Both harami substrates map to the *same* `harami` EntrySet object (`make_entrysets`); verified empirically — every candidate's `gross_exp` and `n_resolved` are byte-identical across the two harami substrates (max diff = 0.0). *(But see C1: their matched-random controls are **not** identical.)* |
| Determinism replay | **PASS (in-process)** | Second full pass over the member grid; `_fingerprint` (9-dp rounded, sorted) compared → `determinism_ok=true`. Seeds fixed (`SEED_RANDOM=20260621`, `SEED_BOOT=20260622`), all `default_rng` seeded by `[seed, cell, s_i, c_i]`. |
| Complexity budget | **PASS** | 4 stat-method families / 5 plots / 1 new `src` module — within the ≤4 / ≤5 / ≤2 budget. |
| Code conventions | **PASS** | Imports→paths→constants→types→helpers→candidate surface→gate→orchestration→plotting→`main()`; no import-time I/O; `tqdm` outer loop; bounded plot inputs from the single screen table. |

---

## Verdict Forensics

### 1. Per-stratum re-derivation & masking check (the headline is heterogeneous)

The `n_valid = 28` / `SCREEN_DELIVERED` headline **masks severe concentration and a deferred binding gate**. Re-derived from `screen_results.parquet`:

| Binding stratum (substrate × instrument × domain) | survivors | n_resolved | S2 status | S1 margin (x_fav_excess_lo − m_cell) |
|---|---|---|---|---|
| SUB-AVWAP × NZDUSD × 4h | 10 | 77 | **all S2_DEFERRED (n<120)** | 0.44–0.76 (huge) |
| SUB-AVWAP × USDCAD × 4h | 11 | 44–78 | **all S2_DEFERRED (n<120)** | 0.42–1.55 (huge) |
| SUB-HARAMI-PARTIAL-V2A × AUDUSD × 1h | 4 | 988 | **S2 PASS** | 0.022–0.055 (thin) |
| SUB-HARAMI-V2A-ADVNONE × AUDUSD × 1h | 3 | 988 | **S2 PASS** | 0.041–0.051 (thin) |

**Masking findings (all faithfully recorded in the artifacts, but the headline must not be read flat):**

- **Only 7 of 28 survivors cleared *both* binding gates.** 21/28 (75%) are `s2_deferred=true` — the binding shape-guard S2 was **never evaluated** for them (sub-floor n). The phrase "survives both TRAIN gates" in the scope's `SCREEN_DELIVERED` definition is satisfied for 7 strata; the other 21 are carried on **G-018a ∧ S1 with S2 deferred**. The interpreter and EXP-084 must treat the 21 as *S2-unadjudicated*, not S2-passed.
- **All 28 survivors come from 3 underlying entry populations** (NZDUSD-4h-AVWAP, USDCAD-4h-AVWAP, AUDUSD-1h-harami), and the harami population is **double-counted** as two substrates (identical entries+returns; see C1). The apparent "breadth" of 28 is candidate-count × strata, not population breadth. Honest breadth: **2 low-n AVWAP-4h cells (S2-deferred) + 1 well-powered harami-1h cell.**
- **98.6% of the surface (2719/2760) dies at the cheap G-018a gross screen** before separability is even reached. The binding separability gate was the deciding leg for only **10 strata** (8 fail@S2, 2 fail@S1). The expensive S1∧S2 machinery almost never bound — the gross matched-random-excess screen did the work.

### 2. Mechanism statement (why these survived — NOT the EXP-082 trap)

**The survivors are genuine favourable-attribution, not the "harvest the median, leave the catastrophe" tail-truncation artifact EXP-082 feared.** Decomposition over all 28 survivors:

- `x_fav > 0` for **all 28** (min 0.81, mean 1.27 ATR) — the favourable-target + time-cap leg independently beats matched-random (S1 PASS by construction here).
- `x_tail ≤ 0` for **all 28** (range −0.199 … 0.0) — the adverse stop **subtracts** expectancy rather than manufacturing it. **Zero** survivors have `x_fav ≤ 0` and **zero** are tail-dominated (`|x_tail| > |x_fav|`).

So the edge is attributable to favourable capture, and the catastrophe-stop costs (not creates) expectancy. The driver is the **entry** (harami-1h and AVWAP-4h favourable capture beating random), with the exit's adverse leg a small drag.

**Gate-shape caveat on the 7 S2-passers (important for the interpreter):** the RR arms (RR-1.5/2/3, 6 of the 7) clear S2 *via mechanical stop truncation*: their post-exit `tailmass = 0.0` and `q05_post = q05_control = −7.279329` exactly — the fixed adverse stop `S_adv = MAE_q90 ≈ 7.28 ATR` clips the left tail of **both** candidate and control to a point mass at the stop level, so the tailmass leg sees "no continuous tail" and the relative-q05 leg ties at the stop. S2 is a *shape* guard (separated continuous catastrophe mode), not a *magnitude* guard: a −7.28-ATR-per-stop tail passes S2 by truncation. Whether a 7-ATR stop loss is economically acceptable is a **cost/magnitude** question the GROSS screen explicitly defers to EXP-084's cost-calibrated referee suite. The 7th S2-passer (AVWAP-FH, a no-stop fixed-horizon exit) passes S2 on a genuine continuous-tail measurement (`tailmass=0.022`, `q05_post=−6.30 > q05_control=−6.76`).

### 3. Gate-shape check (can the binding gate see the effect's shape?)

- For the **21 deferred** survivors: **no** — S2 was structurally not run (n<120), so the binding shape-guard is blind here by design. They are eligible on location/attribution evidence only.
- For the **6 RR S2-passers**: S2 passes by stop-truncation-to-point-mass (above) — it confirms *no separated catastrophe mode* but is silent on the *magnitude* of the truncated tail. The gate sees the shape it was built for and reports it benign; it cannot and does not adjudicate the −7.28 ATR loss size (correctly deferred to the cost layer).
- No retro-editing of the gate is recommended. Record both shape-caveats for the interpreter and EXP-084.

---

## Findings

### CRITICAL (verdict-material — fix + re-execute before Stage 6)

**C1 — Entry-identical harami substrates receive *different* matched-random controls; control-draw noise alone flips a binding-7 survivor and changes `n_valid` + the pinned hash.**

- **Where:** `run_experiment.py:425-431` (`_matched_control`) and `:411` (`m_cell` rng) — the control rng is seeded `np.random.default_rng([SEED_RANDOM, cell_index, s_i, 7])`, i.e. by **substrate index `s_i`**.
- **Demonstrated:** `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` (AUDUSD-1h) have byte-identical entries → identical candidate returns (`gross_exp` diff = 0.0, `n_resolved` diff = 0 across all 15 candidates). Yet their matched-random controls differ (`matched_exp_excess_lo` differs by up to 0.318; `q05_control` differs, e.g. AVWAP-FH −6.757 vs −7.235). This control-draw difference **flips `AVWAP-FH` from `valid=true` (PARTIAL-V2A) to `valid=false` (V2A-ADVNONE)** — the only candidate whose flag disagrees between the two byte-identical substrates.
- **Why it is verdict-material:** `AVWAP-FH`-on-harami is one of the **7 binding (S2-passing)** survivors. With a consistent (shared) control, AVWAP-FH would be both-or-neither → `n_valid` would be 27 or 29, not 28, and the canonicalized set sha256 (`0796530c…`) would change. `valid_candidate_set.json` is hash-pinned and **imported verbatim by EXP-084, which asserts that exact sha256 before spending a lifetime TEST read.** Shipping a binding hand-off whose membership turns on null-draw noise (for an entry population the scope itself declares identical) is not acceptable given the programme's 2-lifetime-reads-per-stratum scarcity and falsification-first discipline.
- **Required fix (route to `experiment-developer`):** the entry-identical harami pair must share **one** matched-random control (seed the control by the entry population / a substrate-group key, not by `s_i`), so eligibility is identical for byte-identical `{entry × exit}`. Equivalently, dedupe the harami pair to a single stratum in the screen and disclose the one-population reporting. Then **re-run** (Stage manual-execution gate) and **re-pin** `valid_candidate_set.json`.
- **Note:** the binary verdict `SCREEN_DELIVERED` is **not** at risk (6 well-powered RR survivors + 21 AVWAP survivors remain regardless). Only the set composition / `n_valid` / sha256 move — but those are the deliverable.

### WARNING (shown not to flip the binary verdict; flagged for the fix-rerun and/or EXP-084)

**W1 — `m_cell` reuse across a cell's candidates is anti-conservative for the larger-target arms, and `m_cell` is the *thin* binding leg for all 7 S2-passers (Stage-4 item 4).**

- **Where:** `run_experiment.py:409-414` — `m_cell` is calibrated **once per substrate-cell** from the canonical no-stop control reference (`ctrl_map["V2A-ADVNONE"]`, the `mfe_med`-target distribution) and reused for every candidate.
- **Materiality:** for the 7 binding harami-1h survivors, the S1 margin `x_fav_excess_lo − m_cell` is only **0.022–0.055 ATR** — `m_cell` is the decisive leg there. The RR arms' `X_fav` uses a *larger* favourable target (`R·MAE_q90`) → larger variance → the correctly-scaled synthetic-null margin should be **larger** than the `mfe_med`-calibrated `m_cell` actually used. Direction of bias is therefore **anti-conservative**: the reused `m_cell` is too small for RR-2/RR-3, so it can admit RR arms slightly too easily. A per-candidate-scale `m_cell` could plausibly drop the thinnest (RR-1.5, margin 0.022).
- **Why not Critical on its own:** (a) the binary verdict is unaffected; (b) the bias is anti-conservative at a *screen*, and any over-admitted RR arm is re-adjudicated by EXP-084's frozen referee suite under Holm correction — it cannot create a false programme conclusion, only a wasted (Holm-penalised) test. It was explicitly disclosed and Stage-4-ratified.
- **Action:** a re-run is already required (C1); the developer should **either** recompute `m_cell` per-candidate-scale in that same re-run, **or** keep the reuse and have `results.md`/EXP-084 carry the anti-conservative direction + the 0.022 thinnest-margin explicitly so EXP-084's referee suite is the binding arbiter for the 7-subset. Not independently blocking.

**W2 — `/EXIT-VP` (VP-POC) is scored on a geometry-selected subsample (selection-on-outcome).**

- **Where:** `run_experiment.py:235-252` (`_vp_fav_distance`) → events whose cell-level POC sits on the adverse side get `dist ≤ 0` → NaN target → excluded by the resolver. Verified: AUDUSD-1h-harami VP-POC `n_resolved = 590` vs `988` for every other candidate (−40%); the surviving USDCAD-4h VP-POC has `n_resolved = 44`.
- **Materiality:** `n_usable` (entry denominator) is preserved (EXP-042 honored), but VP-POC's *effective* sample is the self-selected subset where the POC is favourable-side, which can inflate its apparent edge. Impact is confined to VP-POC strata — **1 survivor (USDCAD-4h, `s2_deferred`)**, which does not touch the 7 binding S2-passers and flows to EXP-084 re-adjudication. Disclosed + Stage-4-ratified as a cell-level TickVolume proxy.
- **Action:** flag to the interpreter; EXP-084/parity work should use a per-event reference-move profile or drop VP from the binding set. Not verdict-flipping.

### INFO (context; does not affect trust)

- **I1 — "paired" wording vs independent two-sample diff.** The plan (§Step 3) says "paired" matched-random contrast, but the code correctly uses `two_sample_diff_lo` (independent block-resampled samples), because candidate (substrate) and matched-random entries are **different** event sets and cannot be paired event-by-event. Independent diff CIs are *wider* (more conservative) than paired — the conservative, correct choice. Plan wording is a misnomer only.
- **I2 — Determinism is in-process.** `determinism_ok` re-runs the same code in the same process with fixed seeds; it proves seed-stability, not cross-machine reproducibility. Acceptable for this screen; the hash-pin is the durable artifact.
- **I3 — `q05_post == q05_control` exact ties for RR arms** are explained (stop clips both at `−MAE_q90`); not a bug. Documented under Mechanism above.
- **I4 — `/SIZE-VOLADJ` correctly omitted** as a degenerate duplicate in the ATR-normalized frame (returns already vol-normalized) — confirmed a correct observation (Stage-4 item 3), not a dropped test that could have changed the survivor set.

---

## Materiality Summary

| Finding | Moves a verdict-bearing number? | Class | Disposition |
|---|---|---|---|
| C1 harami control seed | **Yes** — flips AVWAP-FH-on-harami → changes `n_valid` (28) and pinned sha256 | **Critical** | Fix (`experiment-developer`) + re-run + re-pin |
| W1 `m_cell` reuse | Could thin/flip the 7 S2-passers at 0.022 margin; **not** the binary verdict; downstream Holm-absorbed | Warning | Address in the C1 re-run **or** carry explicitly to EXP-084 |
| W2 VP-POC selection | 1 deferred VP survivor only; not the binding 7; not the binary verdict | Warning | Disclose to interpreter / EXP-084 |
| I1–I4 | No | Info | Document |

**Binary verdict `SCREEN_DELIVERED` is sound** (favourable-attribution mechanism confirmed; ≥6 well-powered S2-passing survivors robust to C1/W1). **The hash-pinned hand-off set is not yet trustworthy as the EXP-084 input** because C1 makes its membership/sha256 depend on control-draw noise. Fix C1, re-run, re-pin, then advance to Stage 6 — and ensure `results.md` foregrounds the 7-vs-21 (S2-passed vs S2-deferred) split, the 3-population concentration, and the stop-truncation gate-shape caveat rather than the flat "28 survivors" count.

---

# Re-Audit (post-fix re-execution, 2026-06-22)

**Run:** `valid_set_sha256 = fa4035f3…` (supersedes first-pass `0796530c…`), `generated_at 2026-06-22T10:15Z`, full budgets (`N_BOOT=10000, NULL_REPS=200, N_BOOT_NULL=1000`).
**Re-audit verdict: PASS — no remaining Critical/verdict-material finding. Advance to Stage 6.**

## Fix verification

| Finding | Fix applied (operator-directed) | Verified |
|---|---|---|
| **C1 (Critical)** harami control-seed inconsistency | Harami pair deduped to ONE canonical screened stratum `SUB-HARAMI-V2A` (4→3 substrates; `_SUMMARY_SUBSTRATE` maps to the entry-identical PARTIAL-V2A EXP-081 row). | **Resolved.** `screen_results.parquet` carries exactly `{SUB-AVWAP, SUB-HARAMI-V2A, SUB-RANDOM}`; `n_rows = 2070 = 3×46×15`. `AVWAP-FH` on harami now appears **once**, consistently `valid` — the two-identical-substrate flip cannot recur (one entry population → one null). |
| **W1 (Warning)** per-cell `m_cell` reuse | `m_cell` recomputed **per candidate** from each arm's own no-stop control reference (scaled to its favourable-target distance); per-candidate seed `[SEED_BOOT, cell, s_i, c_i, 999]`. | **Resolved.** `m_cell` now varies by arm at AUDUSD-1h: RR-1.5 `0.035`, RR-3 `0.053` (correctly **larger** for the bigger target), AVWAP-FH `0.021`, RR-2 `−0.025`. The previously-feared anti-conservative bias **did not flip any survivor** — RR-3 survives correct calibration (S1 margin `0.036`). |

## Re-run verdict forensics

- **Per-stratum / masking (now clean, still concentrated).** `n_valid = 26` = **4 S2-PASS** (all `SUB-HARAMI-V2A × AUDUSD × 1h`, n=988, well-powered) + **22 S2-DEFERRED** (`SUB-AVWAP` 4h: NZDUSD ×10, USDCAD ×11, USTEC ×1, all n<120). The double-counting is gone; the binding-S2 evidence sits in **one** well-powered cell, and the 22 deferred are all low-n AVWAP-4h. The headline must still be read as "4 fully-gated + 22 S2-unadjudicated," not a flat 26.
- **Mechanism (unchanged, confirmed).** All 26 survivors have `x_fav > 0` (min 0.808, mean 1.328 ATR) and `x_tail ∈ [−0.199, 0]`; **0 survivors are tail-truncation artifacts** and **0 are tail-dominated**. The edge is genuine favourable-capture attribution; the adverse stop subtracts (never manufactures) expectancy. The EXP-082 "harvest-median-leave-catastrophe" trap did **not** materialise for the survivors.
- **Gate-shape caveat (unchanged).** The 3 RR S2-passers clear S2 by stop-truncation-to-point-mass (`tailmass_post = 0`, `q05_post = q05_control = −MAE_q90`); S2 confirms *no separated continuous catastrophe mode* but is silent on the truncated tail's **magnitude** (−7.28 ATR/stop), correctly deferred to EXP-084's cost-calibrated referee suite. AVWAP-FH passes S2 on a genuine continuous-tail measurement (`tailmass 0.022`).
- **Cheap-screen dominance (unchanged).** 2033/2070 (98.2%) die at G-018a; separability bound for only 8 strata (7 fail@S2, 1 fail@S1).
- **Discipline checks (re-confirmed).** `determinism_ok = true`; `holdout_untouched = true`, `test_stratum_touched = false`, `counted_test_reads = 0`, `candidate_slots = 0`; `derive_barriers` sha256 = `34d03f45…` (== EXP-082 pin); EXP-042 same-denominator invariant holds (`n_usable` identical across candidates within each cell; only legitimate censoring/VP-invalidity varies `n_resolved`); real-price/ATR discipline intact; new valid set hash-pinned (`fa4035f3…`) with the Holm rule + provenance.

## Carry-forward to Stage 6 / EXP-084 (non-blocking)

- **W2 (VP-POC selection-on-geometry)** persists by design (cell-level TickVolume POC proxy excludes adverse-side-POC events → geometry-selected subsample). In this run VP-POC survives only at USDCAD-4h (deferred); it does not touch the 4 binding S2-passers. Disclose to the interpreter; resolve in EXP-084/parity work.
- `results.md` (Stage 6) must foreground the **4-vs-22** (S2-passed vs S2-deferred) split, the single-well-powered-cell concentration (AUDUSD-1h harami), and the stop-truncation gate-shape caveat — not the flat "26 survivors" count.
- Registry/documentation (Stage 7) must record the **harami slate consolidation** (the two registered harami substrates screened as one stratum here; multiplicity-registry Phase 018 harami count updated accordingly) and the new pinned `valid_set_sha256 = fa4035f3…`.
