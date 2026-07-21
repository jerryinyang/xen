# HYP-I2 runner performance refactor (2026-07-20, after QA run 4)

Not a design amendment: nothing in §3 changed — no estimand, no control
construction, no threshold, no admission rule. The runner computed the same
numbers ~13x slower than it needed to. Recorded here so QA run 5 can audit the
claim rather than take it.

## What changed in `hyp_i2_anchor_race.py`

1. **Column projection.** `session_breaks` reads `OpenTime, High, Low, Close`
   and nothing else; the staging frame carried 11 columns through every
   `join_asof` and `group_by`. The race now loads `RACE_COLUMNS` only.
   Measured 38.1 ms -> 22.7 ms per call on BTCUSDT/DESIGN, with the two output
   frames compared by `DataFrame.equals` -> `True`.

2. **Anchor-table cache** (`_anchors_for`). `anchor_table` is symbol-independent
   and was rebuilt inside every `_sessions_for` call (~79,000 rebuilds of the
   same ~600-row table). Keyed on the **spec**, not on `anchor_id`: two
   candidate anchors' control ensembles reuse the same pseudo ids
   (`PSEUDO-1x-00`) at different offsets, so an id-keyed cache would hand one
   anchor's controls to another. That is a correctness trap, and the key choice
   is the thing to check here.

3. **Tripwire computed once.** `_arm_day_contrast` previously called `run_cell`
   (building the real arm and all 30 control arms) and then rebuilt the same
   frames inline for the day series — every arm's work done twice. It also
   rebuilt the control arm for each `ib_shift`, although the control arm does
   not depend on `ib_shift` (same clocks, same L, same bars, no shift applied).
   Now: one `run_jobs` call producing shift 0/1/2 real arms plus one control
   arm, reused. 26,040 `session_breaks` calls -> 4,620.

4. **Symbol-parallel execution** (`run_jobs`). Symbols are independent — a cell
   pools them only after every session row exists — so per-symbol work is
   distributed over worker processes. Workers run the same `symbol_frames` on
   the same fenced bars; results reassemble in sorted-symbol order (the order
   the serial loop produced); every cell statistic is an order-free aggregate
   (median / min / max / count / first-by-sort), so worker count cannot move a
   number. `POLARS_MAX_THREADS=1` inside workers prevents N processes each
   spawning a full thread pool. `--workers 1` runs the original single-process
   path.

`run_cell` is retained as the serial wrapper and still drives the
per-instrument spot-check unchanged. `xen.sigbar` was **not** touched.

## Equivalence evidence

- 12-symbol smoke (`--limit 60`), `--workers 1` vs `--workers 10`: whole
  artifact equal ignoring `generated_utc`.
- Full-scale DESIGN artifact vs the pre-refactor full-scale artifact produced by
  the old runner (archived, path below): `cells`, `ranked`, `spot_check`,
  `controls`, `universe`, `universe_scale`, `multiplicity`, `frozen_inputs`,
  `break_rule_at_phase1` all equal; tripwire `cell`, `contrast_raw`,
  `contrast_shifted`, `collapse_fraction`, `day_contrast_correlation`,
  `survives`, `shifted_ci`, `CALIBRATION_ONLY_shift_arm` all equal. The I-34
  positive control has no counterpart in the old artifact (it did not exist).
- Reference artifact + comparison script (session scratchpad, not repo):
  `<scratchpad>/pre_i34_archive/hyp_i2_anchor_race_DESIGN.json`,
  `<scratchpad>/verify_equivalence.py`.
- Independent re-derivation: re-run any band with `--workers 1` and diff.

## Runtime

Full DESIGN race 140 symbols: ~52 min -> ~3.5 min (race cells 2:47, tripwire
0:12). A ~2.5 min floor remains in the parent: the block bootstrap, sensitivity
sweep and MDE curve run on the 609-day series and do not scale with symbols.

---

# HYP-I3 runner performance refactor (2026-07-21, after QA run 8 APPROVE)

Not a design amendment: nothing in §4 changed — no estimand, no destroy form, no
threshold, no admission rule. Same numbers, less wall-clock.

## What changed in `hyp_i3_a6_race.py`

1. **Path-swap row access.** `swap_outcome_paths` used `ev[i]` / `donors[i]`
   (a new one-row DataFrame per event). That dominated the tripwire. Rows are
   now materialised once via `to_dicts()`; the derangement, filters, truncate,
   and `label_outcomes` call are unchanged. Seed and perm are the same.

2. **Single-pass window drop on splice rebuild.** Replacing N sequential
   `filter` copies of the symbol frame with one OR-expression over all replaced
   windows. Sessions are still disjoint; uniqueness is still asserted.

3. **Symbol-parallel event assembly** (`assemble_events`). Load → residualise →
   session → poke/label per symbol is independent. Workers reassemble in
   **sorted-symbol order** (the serial order). `POLARS_MAX_THREADS=1` inside
   workers. `--workers 1` is the single-process path. The race loop (disc × δ)
   and the derangement RNG stream stay single-process and sequential — they
   consume `SEED_DERANGE` in the same order as before, so control derangements
   are bit-stable vs the serial path.

4. **Per-δ symbol index.** `events.partition_by("symbol")` once per poke depth
   instead of `events.filter(symbol == …)` inside every disc cell.

`xen.sigbar` was **not** touched for speed (I-56 join helper stays as the
correctness fix).

## What was deliberately NOT changed

- **Parallel disc evaluation.** Sharing one RNG across discs means evaluation
  order is load-bearing for the soft-control derangements. Parallelising discs
  would require per-cell seeds and would change control numbers. Not done.
- **Vectorised path-swap labels.** Still one `label_outcomes` per spliced event
  — same labels, same splice. Batching would risk I-56/I-61 regressions for
  little gain once row access is fixed.
- **Dropping double `attach_sessions`.** `session_breaks` attaches internally;
  the race also attaches for poke construction. Fixing that means changing
  `sessions.py` (shared with HYP-I2). Left alone.

## Equivalence evidence

- Unit suite `test_sigbar_infr018.py` (path-swap + freeze adjudicators) green
  after the refactor.
- `--workers 1` vs `--workers N` must agree on cells / ranked / tripwire when
  compared ignoring `generated_utc` and the recorded `universe_scale.workers`
  field (re-run smoke if in doubt).

## Runtime (profile, 30-symbol slice → 140-symbol estimate)

Pre-refactor sketch: event build ~15–20s, race ~30s, path-swap ~30s.
Post row-access fix the path-swap term drops sharply; workers cut event build.
Full DESIGN target: **well under 2 minutes** on the same host as the I2 race.
