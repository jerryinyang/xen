# EXP-100 Safe SQLite Batching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace EXP-100's per-mutation SQLite commits with one atomic transaction per source minute while preserving exact research outputs.

**Architecture:** `Exp100StateStore` will own a re-entrant transaction context. Existing standalone store calls keep automatic commit behavior; compound profile operations join an active source-bar transaction. `Exp100Processor` will place the unchanged source-minute processing sequence inside that boundary.

**Tech Stack:** Python 3.13, stdlib `sqlite3`/`contextlib`, pytest, NautilusTrader 1.230.0, PyArrow, Xen emission contract v1.

## Global Constraints

- Preserve level, raid, confirmation, TPO, control, fence, timestamp, event-order, and estimand semantics exactly.
- TRAIN only; do not access TEST or holdout.
- Keep `cost_model: NO_COST_CHARGED`; no accounting or cost path changes.
- Keep cursor-based bounded memory; never materialise all active state.
- No partitioning, pruning, timeout, schema, or object-lifetime change.
- Any emission-value or ordered-event difference fails the optimization.
- The worktree contains pre-existing EXP-100 edits. Do not commit implementation files unless the operator separately requests it.

---

### Task 1: State-store transaction ownership

**Files:**
- Modify: `python/tests/test_exp100_state_store.py`
- Modify: `python/src/xen/exp100/state_store.py`

**Interfaces:**
- Consumes: existing `Exp100StateStore` mutation methods.
- Produces: `Exp100StateStore.source_bar_transaction() -> ContextManager[None]`; nested compound profile methods join the outer transaction; standalone methods retain auto-commit.

- [ ] **Step 1: Write failing transaction-boundary tests**

Add real-SQLite tests with a second connection and literal expectations:

```python
def test_source_bar_transaction_commits_mutations_together(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite"
    with Exp100StateStore(path) as store, sqlite3.connect(path) as observer:
        with store.source_bar_transaction():
            store.insert_level({"level_id": "L1", "price": 100.0, "active": 1})
            store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
            assert observer.execute("SELECT COUNT(*) FROM levels").fetchone()[0] == 0
            assert observer.execute("SELECT COUNT(*) FROM raids").fetchone()[0] == 0
        assert observer.execute("SELECT COUNT(*) FROM levels").fetchone()[0] == 1
        assert observer.execute("SELECT COUNT(*) FROM raids").fetchone()[0] == 1


def test_source_bar_transaction_rolls_back_nested_profile_mutations(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite"
    with Exp100StateStore(path) as store:
        with pytest.raises(RuntimeError, match="injected"):
            with store.source_bar_transaction():
                store.insert_raid({"raid_id": "R1", "level_id": "L1", "active": 1})
                generation = store.start_profile_generation("R1", 1, 0.1)
                store.increment_profile_bin_range("R1", generation, 0, 2)
                raise RuntimeError("injected")
        assert list(store.iter_active_raids()) == []
        assert store.current_profile_generation("R1") is None
        assert list(store.iter_profile_bins("R1", 1)) == []


def test_standalone_mutation_remains_immediately_committed(tmp_path: Path) -> None:
    path = tmp_path / "state.sqlite"
    with Exp100StateStore(path) as store, sqlite3.connect(path) as observer:
        store.insert_level({"level_id": "L1", "price": 100.0, "active": 1})
        assert observer.execute("SELECT COUNT(*) FROM levels").fetchone()[0] == 1
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
cd python
.venv/bin/python -m pytest -q \
  tests/test_exp100_state_store.py::test_source_bar_transaction_commits_mutations_together \
  tests/test_exp100_state_store.py::test_source_bar_transaction_rolls_back_nested_profile_mutations \
  tests/test_exp100_state_store.py::test_standalone_mutation_remains_immediately_committed
```

Expected: the first two tests fail because `source_bar_transaction` does not exist; the standalone characterization passes.

- [ ] **Step 3: Implement the minimum re-entrant transaction mechanism**

Add transaction depth initialized to zero, a public source-bar context, a private compound-operation context, and a standalone commit helper:

```python
from contextlib import contextmanager
from collections.abc import Iterator

@contextmanager
def source_bar_transaction(self) -> Iterator[None]:
    with self._transaction(immediate=True):
        yield

@contextmanager
def _transaction(self, *, immediate: bool) -> Iterator[None]:
    outer = self._transaction_depth == 0
    if outer:
        self._connection.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
    self._transaction_depth += 1
    try:
        yield
    except Exception:
        self._transaction_depth -= 1
        if outer:
            self._connection.rollback()
        raise
    else:
        self._transaction_depth -= 1
        if outer:
            self._connection.commit()

def _commit_if_standalone(self) -> None:
    if self._transaction_depth == 0:
        self._connection.commit()
```

Replace direct commits in simple mutation methods with `_commit_if_standalone()`. Replace the manual `BEGIN`/commit/rollback blocks in profile compound operations with `with self._transaction(...)`. Do not change their SQL statements or ordering.

- [ ] **Step 4: Run state-store and TPO tests and verify GREEN**

Run:

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_state_store.py tests/test_exp100_tpo.py
```

Expected: all pass, including the pre-existing injected-reset rollback test.

### Task 2: One transaction per processor source minute

**Files:**
- Modify: `python/tests/test_exp100_processor.py`
- Modify: `python/src/xen/exp100/processor.py`

**Interfaces:**
- Consumes: `Exp100StateStore.source_bar_transaction()` from Task 1.
- Produces: unchanged `Exp100Processor.on_one_minute_bar(bar) -> None` behavior with one outer SQLite transaction.

- [ ] **Step 1: Write a failing one-transaction processor test**

Use SQLite's real trace callback because transaction count is the measured performance contract:

```python
def test_processor_uses_one_transaction_for_a_source_minute(tmp_path: Path) -> None:
    processor, _ = make_processor(tmp_path)
    processor.seed_level("L1", price=100.0, side="HIGH")
    statements: list[str] = []
    processor.state._connection.set_trace_callback(statements.append)

    processor.on_one_minute_bar(
        BarRecord(0, 100.8, 101.0, 100.5, 100.8, 1.0, 1)
    )

    transaction_statements = [
        statement for statement in statements
        if statement in {"BEGIN IMMEDIATE", "BEGIN", "COMMIT", "ROLLBACK"}
    ]
    assert transaction_statements == ["BEGIN IMMEDIATE", "COMMIT"]
    assert next(processor.state.iter_active_raids())["raid_id"] == "L1:raid:1"
```

The test catches reintroduction of per-mutation commits while asserting a real raid mutation survived the transaction.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
cd python
.venv/bin/python -m pytest -q \
  tests/test_exp100_processor.py::test_processor_uses_one_transaction_for_a_source_minute
```

Expected: FAIL because the current processor produces multiple transaction boundaries.

- [ ] **Step 3: Wrap the existing minute sequence without reordering it**

Change `on_one_minute_bar` so its current body executes inside:

```python
with self.state.source_bar_transaction():
    # existing profile update, raid state, observation/reference,
    # and catalogue state mutations

# existing memory observation runs immediately after the commit so state_bytes
# retains its current post-commit meaning
```

Do not alter the statements inside the block.

- [ ] **Step 4: Run processor tests and verify GREEN**

Run:

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_processor.py
```

Expected: all pass with exact existing event and row assertions.

### Task 3: Regression verification and exact smoke equivalence

**Files:**
- Read: `data/nautilus_runs/exp100_smoke/BTCUSDT_15m_BREAKOUT_PREVIOUS_1H_2023-12-01_2023-12-04/`
- Create temporarily: `/tmp/exp100-batching-smoke-20260812/`
- Update only if needed by the gate: `python/experiments/EXP-100/results/estimand_validation_smoke.json`

**Interfaces:**
- Consumes: optimized EXP-100 runner and retained approved smoke.
- Produces: test results, exact-equivalence report in command output, passing estimand gate, and new profile timings.

- [ ] **Step 1: Run the focused suite**

```bash
cd python
.venv/bin/python -m pytest -q \
  tests/test_exp100_levels.py \
  tests/test_exp100_control.py \
  tests/test_exp100_processor.py \
  tests/test_exp100_runner.py \
  tests/test_exp100_state_store.py \
  tests/test_exp100_features.py \
  tests/test_exp100_tpo.py \
  tests/test_nautilus_streaming.py
```

Expected: all tests pass.

- [ ] **Step 2: Run the frozen three-day TRAIN smoke in a fresh process**

Use the exact retained cell configuration, a unique temporary run directory, and `--destroy-control`. Expected: publication succeeds without TEST/holdout contact.

- [ ] **Step 3: Compare research-bearing outputs exactly**

For `bar_marks`, `levels`, `raids`, `tpo_profiles`, and `raids_destroyed`, use PyArrow to sort columns into canonical order and assert table equality including null placement and row order. Assert `event_log.jsonl` bytes are identical. Compare metadata after excluding only `generated_utc`, runtime/memory observations, catalog/run-directory textual identity, and hashes derived solely from permitted metadata differences. Expected: no research-bearing difference.

- [ ] **Step 4: Run the integrity gate**

```bash
cd python
.venv/bin/python -m xen.estimand_validation \
  /tmp/exp100-batching-smoke-20260812/three-day \
  --expect BTCUSDT \
  --out experiments/EXP-100/results/estimand_validation_smoke.json
```

Expected: `BLOCKING_PASS: True`, pinned fence, and zero-cost compliance true.

- [ ] **Step 5: Re-profile one-day and two-day cells**

Run the same `cProfile` commands used in diagnosis. Record wall time, commit count/time, SQL execution time, active-profile time, final live raids, and peak RSS. Expected: materially fewer commits and lower wall time with unchanged final state counts.

### Task 4: Fresh-context QA handoff

**Files:**
- Append only: `python/experiments/EXP-100/qa-review.md`

**Interfaces:**
- Consumes: implementation diff, tests, smoke equivalence, estimand gate, profile evidence.
- Produces: an independent QA verdict for the changed execution path.

- [ ] **Step 1: Dispatch fresh QA**

Use the `qa-compliance` skill in a dedicated fresh-context subagent. Provide the approved batching spec, implementation diff, verification commands/results, and retained/new smoke paths. The reviewer must append a new run; prior QA history is immutable.

- [ ] **Step 2: Stop on any integrity or fidelity finding**

If QA returns REVISE/REJECT or equivalence fails, do not run the full matrix. Correct only an approved implementation defect through a new failing test, then repeat Tasks 3 and 4.

- [ ] **Step 3: Report readiness and the new bottleneck**

If QA approves, report the measured speedup and the newly dominant profile path. Do not implement a second optimization until its evidence is reviewed as a separate design decision.
