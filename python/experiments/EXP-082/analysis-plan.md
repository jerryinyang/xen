# Analysis Plan: Experiment EXP-082 — Mechanical Exit Derivation from the Frozen D3 Rule

**Phase:** 018 (CF-CAPGEO-001) · **HYP:** HYP-003 (derive) · **Slots:** 0 · **Counted TEST reads:** 0 ·
**Statistical tests:** 0 · **Mode:** deterministic transformation of EXP-081 TRAIN outputs.

## Objective

Apply the **frozen D3 mechanical exit-derivation rule** (D0 §D3, ratified G0 2026-06-21) to EXP-081's
per-cell TRAIN statistics to emit, for every member substrate-cell, a triple-barrier exit
`(T_fav, S_adv, H_cap)` for each of three registered `/EXIT-DERIVED` candidates — `D1-MEDIAN-CAPTURE`,
`D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT` — and to **lock and sha256-pin** the derivation function that
EXP-083 will import for its per-fold causal re-fit. The verdict is **DERIVATION_DELIVERED**: there is
**no method to select, no statistic to test, and no edge to claim**. The plan's entire substance is to
fix, unambiguously and parameter-free, (a) the operational form of each barrier, (b) the validity gates
that decide candidate formation, (c) the provenance and determinism discipline, and (d) the
disclosure-only readouts — so the derivation is a single, auditable, reproducible mapping with no hidden
degree of freedom. This is the literal embodiment of "**freeze the rule, not the story**."

There is **no statistical methodology** in the usual sense; the "Methodology" steps below are
**deterministic computation steps**, each with its exact formula, its faithfulness check against D0 §D3,
and its expected output. Hard boundary (binding): **no exit simulation, no P&L/expectancy, no G-018a
gross screen, no separability gate (S1/S2), no WF folds, no `ASS` adjudication** — all are EXP-083.

---

## Inputs (frozen; read-only)

| Input | Path | Use |
| --- | --- | --- |
| EXP-081 per-cell summary (184 rows) | `python/experiments/EXP-081/results/substrate_cell_summary.parquet` | the D3 input statistics |
| EXP-081 run metadata | `python/experiments/EXP-081/results/run_metadata.json` | provenance fingerprint assertion |

Consumed columns (per cell): `instrument, domain, substrate, n_usable, mfe_med, mfe_q40, ttp_med,
ttp_q75, mae_q90, m_anti, dip_stat, dip_p, tailmass, q05, tail_boundary, mad_zero`. (The `ass_*` columns
are **not** consumed — `ASS` is non-binding discovery and plays no role in derivation.)

**Decisive data fact (verified pre-plan, read-only):** `m_anti` is non-NaN in **exactly 1 of 184 cells**
— US500-1h `SUB-AVWAP` (`m_anti = 1.794` ATR, `dip_p = 0.0323 < 0.05`, `MAE_q90 = 8.999` ATR). In the
other 183 cells the MAE distribution is unimodal to the Hartigan dip (`m_anti = NaN`) and the adverse leg
takes the `MAE_q90` fallback — **exactly as the D9 bite-check anticipated** ("the D3 adverse leg
predominantly uses the `MAE_q90` fallback at realistic cell sizes; `m_anti` engages only in large-n
cells"). This fact drives the D2 operationalization below.

---

## Methodology (deterministic computation steps)

### Step 1 — EXP-081 provenance-fingerprint assertion (gate before any derivation)

- **Computation:** load `EXP-081/results/run_metadata.json`; assert
  `verdict == "CHARACTERISATION_DELIVERED"`, `n_substrate_cells == 184`, `n_underpowered_cells == 0`,
  `holdout_untouched == true`, `counted_test_reads == 0`. Load `substrate_cell_summary.parquet`; assert
  `height == 184`, the 4 substrates × 46 member cells are all present (the US500-4h, JP225-4h
  `COVERAGE_EXCLUDED` cells are absent), and no member cell is below the `EVENT_FLOOR = 30`
  (`n_usable.min() >= 30`). Record the EXP-081 module hashes (`capgeo_geometry`, `capgeo_substrates`,
  `domain_bars`) verbatim into EXP-082 `run_metadata.json`.
- **Why:** EXP-082 is *defined* as a transformation of the **audited** EXP-081 result; the fingerprint
  guarantees the derived candidates trace to that exact result, not a stale or mutated copy.
- **Failure → HALT** (process-level Evidence AGAINST): any assertion failure stops the experiment.
- **Expected output:** an `inputs_ok: true` block in the validity report.

### Step 2 — The frozen barrier formulas (per candidate; D0 §D3 verbatim)

Define one **pure, deterministic, importable** function
`derive_barriers(stats) -> {candidate: (T_fav, S_adv, H_cap)}` (the binding artifact; Step 6). For a cell
with statistics `s`, the three candidates are:

| Candidate | `T_fav` | `S_adv` | `H_cap` |
| --- | --- | --- | --- |
| `D1-MEDIAN-CAPTURE` | `s.mfe_med` | `s.m_anti` if `isfinite(s.m_anti)` else `s.mae_q90` | `s.ttp_q75` |
| `D2-TAIL-ROBUST` | `s.mfe_med` | `min(s.m_anti, s.mae_q90)` if `isfinite(s.m_anti)` else `s.mae_q90` | `s.ttp_q75` |
| `D3-CAPTURE-EFFICIENT` | `s.mfe_q40` | `s.m_anti` if `isfinite(s.m_anti)` else `s.mae_q90` | `s.ttp_med` |

- **`H_cap` integerization (frozen):** `H_cap = max(1, int(round(<ttp quantile>)))` — domain bars are
  integer; `ttp_q75`/`ttp_med` are emitted as floats (e.g. `51.0`, `26.0`) and are already near-integer.
  Round-half-to-even (`numpy` default), then floor at 1 bar.
- **Units:** `T_fav`, `S_adv` in **ATR** (EXP-081 normalization, Wilder ATR(14)); `H_cap` in **domain
  bars**. Carried through unchanged — EXP-082 introduces no re-scaling.

**Faithfulness of the D2 operationalization (the one genuinely ambiguous item — frozen here):**

D0 §D3 writes D1's adverse leg as "`m_anti` else `MAE_q90`" and D2's as "`m_anti` *(tightened to the
dip; unimodal → `MAE_q90`)*". The parenthetical encodes D2's distinct thesis — *cut the catastrophic
minority tail with the tighter stop*. The only parameter-free, column-computable reading of "tightened to
the dip" that (i) introduces **no new constant** (D0 "no magic numbers"), (ii) reduces to `MAE_q90` when
unimodal exactly as D0 states, and (iii) is genuinely *tighter-or-equal* to D1, is:

> **D2 `S_adv` = `min(m_anti, MAE_q90)` when the dip resolves, else `MAE_q90`.**

This selects the **tighter of the dip stop and the q90 stop** whenever a dip exists — the literal "tighten
to the dip." It is a **distinct function** from D1 (D1 *prefers* `m_anti` even were it wider than
`MAE_q90`; D2 *caps* at the tighter of the two). The two diverge **iff** a cell has `m_anti > MAE_q90`
(then D1 keeps the wide antimode, D2 takes the tighter `MAE_q90`).

**Anticipated EXP-082 outcome (disclosure, not a result):** on the EXP-081 full-TRAIN snapshot the lone
resolved cell has `m_anti = 1.794 < MAE_q90 = 8.999`, so `min(m_anti, MAE_q90) = m_anti` there, and
`m_anti = NaN` in the other 183 → **D1 and D2 emit numerically identical triples for all 184 cells** on
this snapshot. This is the honest output of the frozen rule meeting power-limited `m_anti` (D9 foresaw
it), **not** a defect and **not** grounds to invent a differentiating constant. The two remain **distinct
frozen functions**: EXP-083 re-fits per fold-TRAIN, where a fold subsample could resolve `m_anti > MAE_q90`
and make D2 strictly tighter than D1 — so both are carried, and the numerical coincidence on the
full-TRAIN snapshot is **disclosed** (Step 8), flagged for EXP-083's candidate-grid / Holm accounting.
Any move to make D1 and D2 differ *on this snapshot* would require a new constant or finer dip geometry
EXP-081 does not emit, and is therefore **out of scope** (would need an operator D0-amendment, not an
analyst choice).

- **Why this method (and the simpler alternative considered):** the *simplest* reading — "D2 `S_adv` ≡
  D1 `S_adv` = `m_anti` else `MAE_q90`" — is rejected because it makes D2 a definitional duplicate of D1
  (no distinct function for EXP-083 to re-fit), erasing the "tightened" semantics the operator
  registered. The `min(m_anti, MAE_q90)` form is the minimal faithful distinct rule; it coincides
  numerically here but not by definition.
- **Expected output:** 552 rows (184 × 3) of `(T_fav, S_adv, H_cap)` plus an `s_adv_source ∈
  {m_anti, mae_q90}` tag per row.

### Step 3 — Validity / estimability / degeneracy gates (decide candidate formation)

Per cell, before emitting a candidate, assert from `s`:

1. **Event floor:** `n_usable >= 30` → else cell is `UNDERPOWERED_DISCLOSED`, forms **no** candidate
   (none expected — EXP-081 `n_usable` ∈ [46, 5535]).
2. **Favourable leg non-degenerate:** `mfe_med > 0` (D1/D2) and `mfe_q40 > 0` (D3) → else
   `DEGENERATE_DISCLOSED`, that candidate not formed (none expected — `mfe_med` ~3.2 ATR).
3. **Adverse leg well-defined and positive:** the resolved `S_adv > 0` (the rule guarantees
   definedness — `m_anti` finite *or* `MAE_q90` fallback; D9 undefined-rate 0.000) → else
   `DEGENERATE_DISCLOSED`.
4. **Time cap valid:** `H_cap >= 1` after integerization → guaranteed by the `max(1, …)` floor.

A cell passing all gates is `valid = true` and emits all three candidates; `disposition ∈ {OK,
UNDERPOWERED_DISCLOSED, DEGENERATE_DISCLOSED}` is recorded per (cell, candidate). **No cell is ever
silently dropped.**

- **Expected output:** `valid` flag + `disposition` per (cell, candidate); summary counts in the
  validity report (expected: 184/184 valid, 0 underpowered, 0 degenerate).

### Step 4 — Harami-substrate triple-identity assertion

`SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` share one entry population (EXP-080/081), so their
EXP-081 input rows are identical per (instrument, domain) and therefore their derived triples must be
**bit-identical**. Assert this for all 46 instrument×domain pairs across all three candidates.

- **Failure → HALT** (indicates an input or join defect, not a result).
- **Expected output:** `harami_identity_ok: true` (46 pairs × 3 candidates reconciled).

### Step 5 — Determinism replay

Run `derive_barriers` twice over the 184 rows; assert the two `derived_candidates` tables are
**byte-identical** (stable column order, stable row order by `(instrument, domain, substrate,
candidate)`, fixed float formatting). No RNG is used anywhere (pure transformation).

- **Expected output:** `determinism_replay: "byte-identical"` fingerprint (e.g. sha256 of the
  canonicalized table) recorded in `run_metadata.json`.

### Step 6 — Freeze and hash-pin the derivation function (the binding artifact)

Implement `derive_barriers` as a small pure function in **one** new module `python/src/xen/capgeo_exits.py`
(≤1 new module, per budget), importable by both EXP-082 and EXP-083. Record its **sha256** (source-bytes
hash of the function/module, the same hashing convention EXP-081 used in `module_hashes`) in EXP-082
`run_metadata.json`. EXP-083 must import this exact module and assert the same hash before its per-fold
re-fit, so "the rule" is provably identical across derive and test (D4.1 legitimacy condition).

- **Why:** the static full-TRAIN triples are the *registered candidate values*; the **function** is the
  *binding rule*. Hash-pinning is what makes "many candidates, one honest counted read" (EXP-083) a single
  frozen look rather than a moving target.

### Step 7 — Structural-guard read (DISCLOSURE ONLY — non-adjudicative)

Per cell/candidate, compute and record, **without any threshold, gate, or selection**:

- `T_fav` vs `S_adv` (favourable target vs adverse stop, ATR) and their ratio `T_fav / S_adv`.
- The relation of `S_adv` to the EXP-081 catastrophe read: `S_adv` vs `|q05|` and vs `|tail_boundary|`,
  and the cell's `tailmass`.

This makes the D3 "engage the catastrophic-minority boundary" intent (D0 §D3) **visible** for EXP-083's
separability argument and for the human reviewer — but **nothing here decides anything**. It is reported
as columns/plots, explicitly labelled disclosure. (E.g. the expectation that `S_adv` (~9 ATR `MAE_q90`)
sits *outside* `|q05|` (~9 ATR) so the stop rarely pre-empts the catastrophe — a fact EXP-083 must
confront, surfaced here, not judged here.)

- **Boundary discipline:** this step computes **no realized return, no hit-rate, no expectancy**. It only
  compares already-derived barriers to already-emitted EXP-081 descriptive statistics.

### Step 8 — D1≡D2 coincidence disclosure

Explicitly count and report the number of (cell) rows where D1 and D2 emit identical triples (expected
184/184 on this snapshot), and the number where they diverge (expected 0), with the mechanism
(`m_anti < MAE_q90` wherever resolved; `m_anti = NaN` elsewhere). Flag this prominently for EXP-083 so the
{candidate × stratum} Holm grid and slot accounting can treat D1/D2 correctly (distinct functions,
coincident snapshot values).

---

## Visualisations (≤3; descriptive disclosure of the derived definitions — not results)

1. **Barrier-triple panel by substrate × domain** — small-multiple heatmaps/tables of `T_fav`, `S_adv`,
   `H_cap` across the 46 cells, faceted by the (up to) 4 substrates, one candidate shown (D1; D2/D3 in
   the results table). Answers: *what exits did the frozen rule produce, and how do they vary across
   regime?*
2. **`S_adv` source split** — a 46-cell map / bar showing `s_adv_source ∈ {m_anti, mae_q90}` across the
   member set (expected: 1 `m_anti`, 183 `mae_q90`). Answers: *how often did the dip-based stop engage vs
   the fallback?* (the D9-anticipated dormancy, made visible).
3. **`T_fav` vs `S_adv` scatter (structural-guard disclosure)** — per cell, favourable target vs adverse
   stop (ATR), coloured by substrate, with the EXP-081 `|q05|` catastrophe magnitude overlaid (e.g. as a
   reference line or point size). Answers: *does the derived stop sit inside or outside the catastrophe
   the family must cut?* — the separability question EXP-083 will adjudicate, surfaced descriptively.

All three plots are built from the single derived-candidates table (no reloads, no recomputation).

## Interpretation Guide (predeclared, before the derivation is run)

- **DERIVATION_DELIVERED** iff: all 184 member cells pass the validity gates and emit all three
  candidates with `(T_fav>0, S_adv>0, H_cap>=1)`; the adverse leg is defined in every cell; the
  per-candidate `m_anti`/`MAE_q90` accounting is reported; the harami-identity and determinism replays
  pass; and the `derive_barriers` function is hash-pinned. (Expected: 552/552 triples valid; `s_adv_source`
  = 1 `m_anti` / 551 `mae_q90` across the 3×184 grid; D1≡D2 on 184/184 cells.)
- **Cell-level INCONCLUSIVE** (recorded, not a failure): any cell flagged `UNDERPOWERED_DISCLOSED` or
  `DEGENERATE_DISCLOSED` forms no candidate for the affected candidate(s). Expected count 0; a non-zero
  count is a *disclosed derivation outcome*, not a process failure.
- **Evidence AGAINST → HALT** (process/implementation defect, not a data shape): provenance-fingerprint
  mismatch (Step 1); a frozen-rule transcription error (an emitted triple ≠ the Step-2 formula on an
  independent spot re-derivation of ≥3 cells incl. the lone `m_anti` cell); non-determinism (Step 5);
  harami-identity failure (Step 4); or any holdout-fence / real-price / synthetic-price violation
  (none possible — no market data is read, but assert `holdout_untouched` is carried through).
- **No edge / pass / viability / tradability verdict exists** in EXP-082 (0 slots, no evaluation). The
  D1≡D2 numerical coincidence is **disclosed**, not adjudicated; whether the derived stops actually cut
  the catastrophe without removing the median edge is **EXP-083's separability question**.

## Implementation Safety Constraints (for experiment-developer)

- **Pure transformation, no market data:** read only the two EXP-081 result files; do **not** open
  `data/timebars/`, build domain bars, regenerate substrates, or recompute any per-event geometry. No
  TEST/holdout row is reachable.
- **No RNG:** the derivation is deterministic; do not introduce seeds, sampling, or hashing of
  floating-point with platform-dependent formatting. Canonicalize the output table (fixed column +
  row order, fixed float repr) before fingerprinting.
- **NaN discipline:** `m_anti` is NaN in 183/184 cells — branch on `np.isfinite(m_anti)` explicitly;
  never let NaN propagate into a barrier. `min(m_anti, MAE_q90)` is only evaluated when `m_anti` is
  finite.
- **Integerization:** `H_cap = max(1, int(round(ttp_quantile)))` with `numpy` round-half-to-even; record
  the pre-round float alongside for audit.
- **Frozen function placement:** `derive_barriers` lives in `python/src/xen/capgeo_exits.py`, takes a
  per-cell stats record (or a Polars/pandas row mapping) and returns the three triples; it must have **no
  side effects, no I/O, no global state** so EXP-083 can call it per fold-TRAIN. The experiment script
  orchestrates I/O, validity gates, plots, and metadata; the module is pure compute only.
- **No vectorization that obscures the rule:** 184 rows is tiny; a clear per-row application of the pure
  function is preferred over a clever vectorized form, so the rule reads exactly like D0 §D3.
- **Section the script** (VAL-001 style): imports → path setup → constants (`EVENT_FLOOR=30`, input paths)
  → provenance assertion → derivation (calls `xen.capgeo_exits.derive_barriers`) → validity/identity/
  determinism checks → disclosure reads → plotting → `main()`. Output dirs created only in orchestration.
- **Outputs:** `results/derived_candidates.parquet` (+ `.csv`), `results/derivation_validity.json`,
  `results/run_metadata.json`; `plots/` (≤3). Concise logging; no helper-level prints.

## Complexity Check

- **Statistical tests: 0 / 0** (no inference; `m_anti`/dip were EXP-081's, consumed as inputs).
- **Visualisations: 3 / ≤3** (all descriptive disclosure of derived definitions).
- **New modules: 1 / ≤1** (`xen.capgeo_exits` — the frozen, hash-pinned `derive_barriers`; the binding
  artifact EXP-083 imports).
