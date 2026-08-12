# EXP-100 SQL and Active-Raid Scan Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce TPO-bin SQL call overhead and eliminate one per-minute active-raid cursor pass while preserving exact EXP-100 research outputs.

**Architecture:** Stage 1 replaces the per-bin Python `execute` loop with generator-fed `executemany`, then passes an exact three-day safety gate. Stage 2 merges profile/swing/return processing into one streaming raid pass, passes a second exact safety gate and fresh QA, and only then receives cumulative profiling.

**Tech Stack:** Python 3.13, stdlib `sqlite3`, pytest, NautilusTrader 1.230.0, PyArrow, cProfile, Xen estimand validation v2.

## Global Constraints

- Preserve all research-bearing outputs and ordered events exactly.
- `bar_marks.state_bytes` is the sole approved operational Parquet exception.
- Keep TRAIN-only pinned fence and `cost_model: NO_COST_CHARGED`.
- Keep cursor/generator bounded memory; no active-state or bin-range lists.
- No raid/profile lifetime, reference-scan, schema, pragma, or methodology change.
- Do not profile Stage 1; profile only after Stage 2 safety and fresh QA.
- Do not launch the full matrix.
- Implementation files overlap pre-existing EXP-100 work; do not commit them.

---

### Task 1: Stream TPO-bin upserts through one Python database call

**Files:**
- Modify: `python/tests/test_exp100_state_store.py`
- Modify: `python/src/xen/exp100/state_store.py`

**Interfaces:**
- Consumes: `increment_profile_bin_range(raid_id: str, generation: int, low_bin_index: int, high_bin_index: int) -> None`.
- Produces: the same method and SQL effects, using one `executemany` call for bin upserts.

- [ ] **Step 1: Add a real-connection counting proxy and failing test**

The proxy delegates every operation to the real SQLite connection and counts only the API boundary being optimized:

```python
class CountingConnection:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.execute_calls = 0
        self.executemany_calls = 0

    def execute(self, *args: object, **kwargs: object) -> sqlite3.Cursor:
        self.execute_calls += 1
        return self.connection.execute(*args, **kwargs)

    def executemany(self, *args: object, **kwargs: object) -> sqlite3.Cursor:
        self.executemany_calls += 1
        return self.connection.executemany(*args, **kwargs)

    def __getattr__(self, name: str) -> object:
        return getattr(self.connection, name)
```

Test literal behavior and call shape:

```python
def test_profile_range_uses_one_streaming_bulk_call(tmp_path: Path) -> None:
    store = Exp100StateStore(tmp_path / "state.sqlite")
    try:
        generation = store.start_profile_generation("R1", 1, 0.1)
        counting = CountingConnection(store._connection)
        store._connection = counting

        store.increment_profile_bin_range("R1", generation, -2, 3)

        assert counting.executemany_calls == 1
        assert counting.execute_calls == 2  # BEGIN plus profile_state update
        assert list(store.iter_profile_bins("R1", generation)) == [
            (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1)
        ]
        assert store.get_profile_state("R1", generation) == {
            "profile_start_ts_ns": 1,
            "bin_width": 0.1,
            "bracket_count": 1,
            "expected_tpo_total": 6,
        }
    finally:
        store.close()
```

- [ ] **Step 2: Run the test and verify RED**

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_state_store.py::test_profile_range_uses_one_streaming_bulk_call
```

Expected: FAIL because `executemany_calls == 0` and `execute_calls` includes one call per bin.

- [ ] **Step 3: Replace only the per-bin loop**

Inside the existing transaction:

```python
self._connection.executemany(
    """
    INSERT INTO profile_bins(raid_id, generation, bin_index, count)
    VALUES(?, ?, ?, 1)
    ON CONFLICT(raid_id, generation, bin_index) DO UPDATE SET
        count = profile_bins.count + 1
    """,
    (
        (raid_id, generation, bin_index)
        for bin_index in range(low_bin_index, high_bin_index + 1)
    ),
)
```

Keep the conservation update unchanged.

- [ ] **Step 4: Run store/TPO tests and verify GREEN**

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_state_store.py tests/test_exp100_tpo.py
```

Expected: all pass.

### Task 2: Stage-1 semantic-preservation gate without profiling

**Files:**
- Create temporarily: `/tmp/exp100-stage2-tpo-20260812/three-day/`
- Create temporarily: `/tmp/exp100-stage2-tpo-20260812/estimand_validation.json`

**Interfaces:**
- Consumes: Stage-1 code and retained approved smoke.
- Produces: exact-equivalence and integrity evidence; no profile data.

- [ ] **Step 1: Run the 73-test focused suite**

Use the eight EXP-100 test files from the prior gate. Expected: all pass.

- [ ] **Step 2: Run the frozen three-day TRAIN smoke with destroy control**

Use BTCUSDT, 15m, BREAKOUT_BAR, 1H reference, PREVIOUS_1H, 2023-12-01 through 2023-12-03, and the retained runner arguments. Do not wrap the command in cProfile or `/usr/bin/time`.

- [ ] **Step 3: Compare exact outputs**

Assert exact PyArrow equality for `levels`, `raids`, `tpo_profiles`, and `raids_destroyed`; exact `bar_marks` equality after dropping `state_bytes`; and byte-identical `event_log.jsonl`.

- [ ] **Step 4: Run estimand validation**

```bash
cd python
.venv/bin/python -m xen.estimand_validation \
  /tmp/exp100-stage2-tpo-20260812/three-day \
  --expect BTCUSDT \
  --out /tmp/exp100-stage2-tpo-20260812/estimand_validation.json
```

Expected: `BLOCKING_PASS: True`, pinned fence, zero cost.

### Task 3: Process each active raid once per source minute

**Files:**
- Modify: `python/tests/test_exp100_processor.py`
- Modify: `python/src/xen/exp100/processor.py`

**Interfaces:**
- Consumes: current `iter_active_raids()` cursor and source-bar update sequence.
- Produces: `_update_active_raids_from_source(bar: BarRecord) -> None`, replacing two state-processing cursor passes with one; `Exp100StateStore.count_active_raids() -> int` supplies post-minute telemetry without JSON decoding.

- [ ] **Step 1: Write the failing cursor-count test**

Wrap the real iterator, create one active non-returned raid on the first bar, then count iterator openings on the second:

```python
def test_processor_scans_active_raids_once_per_source_minute(tmp_path: Path) -> None:
    processor, _ = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    processor.on_one_minute_bar(BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1))
    original = processor.state.iter_active_raids
    calls = 0

    def counted() -> Iterator[dict[str, Any]]:
        nonlocal calls
        calls += 1
        yield from original()

    processor.state.iter_active_raids = counted
    processor.on_one_minute_bar(
        BarRecord(MINUTE_NS, 100.9, 101.2, 100.6, 101.0, 1.0, 1)
    )

    assert calls == 1
    raid = next(original())
    assert raid["raid_id"] == "L1:raid:1"
    assert raid["return_ts_ns"] is None
```

- [ ] **Step 2: Run the test and verify RED**

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_processor.py::test_processor_scans_active_raids_once_per_source_minute
```

Expected: FAIL with `calls == 2`.

The current telemetry count also uses `iter_active_raids`, so the observed RED
count is three. Add a separate failing state-store test before production code:

```python
def test_count_active_raids_reports_only_active_rows(tmp_path: Path) -> None:
    with Exp100StateStore(tmp_path / "state.sqlite") as store:
        store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
        store.insert_raid({"raid_id": "R2", "level_id": "L1", "active": 0})
        assert store.count_active_raids() == 1
```

- [ ] **Step 3: Merge profile/swing/return processing into one cursor loop**

Rename `_update_active_profiles_from_source` to `_update_active_raids_from_source`. For each yielded raid, keep the existing profile and swing operations, then perform the current return test against the updated raid dictionary. Remove only the active-raid loop from `_process_source_raid_state`; retain its level loop unchanged. Add `count_active_raids` using `SELECT COUNT(*) FROM raids WHERE active = 1`, and route `_count_active_raids` through it.

- [ ] **Step 4: Run processor tests and verify GREEN**

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_processor.py
```

Expected: all pass.

### Task 4: Final cumulative safety gate and fresh QA

**Files:**
- Create temporarily: `/tmp/exp100-stage3-scan-20260812/three-day/`
- Create temporarily: `/tmp/exp100-stage3-scan-20260812/estimand_validation.json`
- Append only: `python/experiments/EXP-100/qa-review.md`

**Interfaces:**
- Consumes: cumulative Stage-1 and Stage-2 implementation.
- Produces: final exact-equivalence evidence, passing integrity gate, and independent QA verdict.

- [ ] **Step 1: Run focused and full test suites plus Ruff**

Expected: zero failures; unrelated existing warnings may remain disclosed.

- [ ] **Step 2: Run the frozen three-day TRAIN smoke and exact comparison**

Use the same cell and equality contract as Task 2 against the retained approved smoke.

- [ ] **Step 3: Run estimand validation**

Expected: `blocking_pass=true`, pinned fence, zero cost.

- [ ] **Step 4: Dispatch fresh-context QA**

Provide the approved design, cumulative diff, both safety-smoke paths, retained baseline, and final gate. The reviewer appends a new QA run and cannot edit implementation/design. Any REVISE/REJECT stops profiling.

### Task 5: Profile cumulative effect only after final safety approval

**Files:**
- Create temporarily: `/tmp/exp100-stage3-scan-20260812/one-day.prof`
- Create temporarily: `/tmp/exp100-stage3-scan-20260812/two-day.prof`

**Interfaces:**
- Consumes: QA-approved cumulative implementation.
- Produces: comparable one-/two-day cProfile evidence and final performance summary.

- [ ] **Step 1: Profile the frozen one-day cell**

Use the prior one-day arguments and cProfile output path above.

- [ ] **Step 2: Profile the frozen two-day cell**

Use the prior two-day arguments and cProfile output path above.

- [ ] **Step 3: Extract comparable counters**

Record total profiled time; `execute`/`executemany` calls and time; profile-bin increment time; active-raid cursor/decode time; second-pass removal; commit count/time; final live levels/raids/state bytes; and peak RSS.

- [ ] **Step 4: Run final verification**

Re-run the full suite, Ruff, exact research-output comparison, event-log byte equality, and final integrity artifact checks before reporting completion.
