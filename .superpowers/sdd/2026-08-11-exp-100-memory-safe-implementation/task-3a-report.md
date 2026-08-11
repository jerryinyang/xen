# EXP-100 memory-safe apparatus — Task 3a report

## Status

Task 3a implements only the online, disk-backed TPO profile. It does not add
the event processor, strategy, runner, future-destroy control, full experiment,
or a golden trace.

## Commit

The staged Task 3a implementation and focused test were committed as
`c31f371` (`feat: add exp100 tpo profile`).

## Changed files

- `python/src/xen/exp100/tpo.py`
  - Adds `TPOProfileStore` with validated constants and ATR units.
  - Freezes `0.10 * atr_unit` at profile start, applies every closed bar to its
    direct inclusive integer-bin range, and preserves that width on reset.
  - Finalizes through SQLite cursor passes and bounded point queries: lowest-bin
    POC tie breaking, upper-first value-area ties, exact contiguous value-area
    mask, low-density gap span, strict tight-gap rule, and explicit undefined
    outputs for missing/empty profiles.
- `python/src/xen/exp100/state_store.py`
  - Adds the minimal profile-state table and cursor-safe primitives required by
    TPO: current scalar profile state, direct inclusive range increments with
    durable bracket/conservation totals, point bin lookup, current-generation
    lookup, and density-ordered bin iteration.
  - No active-level, active-raid, or history behavior changed.
- `python/tests/test_exp100_tpo.py`
  - Covers TPO conservation, the strict tight-gap comparison, reset without
    historical rebuild, deterministic POC/value-area ties, invalid grid inputs,
    and explicit empty-profile output.

## Memory and causality review

- Profile bin counts and generation metadata are stored in SQLite; Python keeps
  only scalar profile state during each method call.
- Bar updates iterate their inclusive bin range directly and do not construct a
  range list.
- Finalization does not call `fetchall()`, `to_list()`, `to_dicts()`, or load
  profile bins into a Python list. It uses ordered cursors for summary and
  density passes, plus one-bin SQLite lookups while expanding the value area.
- Reset deletes the prior generation's bins through the Task 2 generation
  primitive before a caller can add any bar to the new generation. It carries
  forward the original frozen bin width and never rebuilds old bars.

## TDD and verification

The focused TPO tests were written before `tpo.py` existed. The initial run
failed at collection with the expected `ModuleNotFoundError` for
`xen.exp100.tpo`.

Final commands:

```text
cd python
.venv/bin/python -m pytest -q tests/test_exp100_tpo.py
.venv/bin/python -m compileall -q src/xen/exp100/tpo.py
```

Final output:

```text
.....                                                                    [100%]
5 passed in 0.20s
```

The compile check and `git diff --check` completed with no output and exit 0.

## Concerns

- The added state-store profile primitives commit each public mutation. This
  favors durable, bounded state; a later throughput task may add bounded
  batching without retaining profile history in Python.
- The task brief's explicit gap target is 30% of total profile TPO mass. Older
  EXP-100 design material describes a 30%-of-value-area target instead; the
  implementation follows the task brief for this scoped task.

## Fix round 1

Addressed every Critical/Important finding in
`task-3a-review.md`:

- Gap selection now uses `gap_mass * va_count`, the governing approved
  definition. Finalization emits `gap_mask` as a deterministic `|`-delimited
  sequence of selected bin indexes in density order, preserving separated
  bins, alongside the conservative outer `gap_span`.
- `start_profile_generation()` and `reset_profile_generation()` perform scalar
  state insertion, old-bin retirement, and `profile_meta` publication inside
  one `BEGIN IMMEDIATE` transaction. Rollback leaves the prior generation
  usable. Duplicate `TPOProfileStore.start()` calls are rejected.
- Bin indexes use `Decimal(str(price))` and `Decimal(str(bin_width))` with
  `ROUND_FLOOR`, including negative prices and exact positive boundaries.
- One-bin and otherwise non-computable gap/tightness profiles emit
  `profile_status: UNDEFINED` with `undefined_reason: GAP_UNDEFINED` and do
  not emit a silent non-tight result.

Regression coverage added:

- VA-vs-total gap targets with separated selected bins;
- atomic reset rollback through an injected SQLite failure;
- duplicate starts;
- exact and negative Decimal boundaries; and
- one-bin undefined gap/tightness state.

Verification for the fix round:

```text
cd python
.venv/bin/python -m pytest -q tests/test_exp100_tpo.py tests/test_exp100_state_store.py
.venv/bin/python -m compileall -q src/xen/exp100/tpo.py
.venv/bin/ruff check src/xen/exp100/tpo.py src/xen/exp100/state_store.py tests/test_exp100_tpo.py tests/test_exp100_state_store.py
```

Results: `15 passed`; compile and Ruff passed. `git diff --check` and the
cursor/no-list scan also passed. The fix-round commit hash is recorded after
commit.

## Fix round 2

Addressed both Important findings from `task-3a-rereview.md`:

- `new_profile_generation()` no longer mutates profile metadata or bins. It
  raises a clear `ValueError` directing callers to the atomic
  `start_profile_generation()` and `reset_profile_generation()` APIs. The
  existing direct state test now uses those lifecycle APIs, and a regression
  test protects the rejection.
- Exact selected gap indexes are persisted incrementally in the new
  `profile_gap_bins(raid_id, generation, bin_index)` SQLite table. A cursor
  iterator exposes the exact ascending indexes, while `finalize()` returns a
  fixed-field reference containing the store path, profile key, selected count,
  SHA-256 digest, and conservative outer bin indexes. No Python mask string or
  selected-index list is materialized during finalization.

Verification for this fix round:

```text
cd python
.venv/bin/python -m pytest -q tests/test_exp100_tpo.py tests/test_exp100_state_store.py tests/test_exp100_features.py
.venv/bin/python -m compileall -q src/xen/exp100/tpo.py
.venv/bin/ruff check src/xen/exp100/tpo.py src/xen/exp100/state_store.py tests/test_exp100_tpo.py tests/test_exp100_state_store.py tests/test_exp100_features.py
```

Results: `21 passed`; compile and Ruff passed. `git diff --check` and the
cursor/no-list scan passed. The gap regression verifies separated indexes via
the SQLite cursor and validates the fixed-size digest reference.
