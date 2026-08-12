# EXP-100 Execution Apparatus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the frozen two-venue EXP-100 matrix safely resumable and run its approved 30-day operational preflight.

**Architecture:** The one-cell Nautilus runner derives its catalog fence from the frozen venue pin. A separate serial scheduler expands deterministic cell specifications, launches each cell in a fresh process, validates its emission, and journals terminal states. Resource and resume checks fail closed without cleanup.

**Tech Stack:** Python 3.13, NautilusTrader `BacktestNode`, `subprocess`, JSON/JSONL, pytest, Ruff.

## Global Constraints

- TRAIN only; never query TEST or global holdout.
- One `BacktestNode` per fresh process.
- Zero-cost model and future-destroy control remain mandatory.
- Frozen 936-cell matrix; no methodology or object-lifetime change.
- Serial execution only; no retries or deletion of partial artifacts.
- Preflight is one declared 30-day BTCUSDT cell and does not auto-launch full mode.

---

### Task 1: Venue-Specific Fence Attestation

**Files:**
- Modify: `python/src/xen/nautilus/catalog_fence.py`
- Modify: `python/experiments/EXP-100/code/run_experiment.py`
- Test: `python/tests/test_estimand_validation_v2.py`
- Test: `python/tests/test_exp100_runner.py`

**Interfaces:**
- Produces: `EXP100_VENUES: Mapping[str, VenueExecutionPin]`
- Produces: `execution_pin(venue: str) -> VenueExecutionPin`
- Changes: `fence_attestation_payload(manifest)` records the manifest's actual repository-relative path.

- [ ] **Step 1: Write failing fence and venue-pin tests**

```python
def test_attestation_uses_supplied_manifest_path(tmp_path: Path) -> None:
    manifest = load_fence_manifest(CTRADER_MANIFEST)
    payload = fence_attestation_payload(manifest)
    assert payload["manifest_path"].endswith(
        "archive/chapter-05-voldir-capture-geometry/experiments/INFR-021/artifacts/fence-manifest.json"
    )
    assert payload["manifest_sha256"] == CTRADER_SHA256

def test_ctrader_execution_pin_is_independent() -> None:
    pin = execution_pin("CTRADER")
    assert pin.catalog_path == Path("data/catalog_ctrader")
    assert pin.fence_sha256 == CTRADER_SHA256
```

- [ ] **Step 2: Verify RED**

Run: `cd python && .venv/bin/python -m pytest -q tests/test_estimand_validation_v2.py tests/test_exp100_runner.py`

Expected: supplied manifest path remains the Bybit path and `execution_pin` is absent.

- [ ] **Step 3: Implement the minimum fix**

Add immutable venue pins beside the runner constants. Resolve both paths from the repository
root, load the selected manifest, verify its expected hash, assert the requested dates lie
within its TRAIN band, and pass that manifest to `fence_attestation_payload`.

Update `fence_attestation_payload` to derive a repository-relative POSIX path from
`manifest.path`; refuse paths outside the repository.

- [ ] **Step 4: Verify GREEN**

Run the same focused command; expected PASS.

- [ ] **Step 5: Run a short real cTrader cell and its integrity gate**

Use `EURUSD.CTrader`, 15m, BREAKOUT_BAR, 1H, PREVIOUS_1H over three TRAIN days in a unique
temporary directory. Run `xen.estimand_validation --expect EURUSD`; expected
`blocking_pass=true` and the INFR-021 manifest hash.

### Task 2: Deterministic Matrix and Resume Guards

**Files:**
- Create: `python/experiments/EXP-100/code/run_matrix.py`
- Create: `python/tests/test_exp100_matrix_runner.py`

**Interfaces:**
- Produces: `MatrixCell` frozen dataclass with identity, venue pin, dates, `cell_id`, run path, gate path.
- Produces: `build_cells(mode: str) -> tuple[MatrixCell, ...]`.
- Produces: `resume_decision(cell: MatrixCell) -> Literal["RUN", "SKIP"]` or raises on unsafe state.

- [ ] **Step 1: Write failing matrix tests**

```python
def test_full_grid_has_936_unique_cells() -> None:
    cells = build_cells("full")
    assert len(cells) == 936
    assert len({cell.cell_id for cell in cells}) == 936
    assert all(c.confirmation_reference == ("1D" if c.observation_minutes == 60 else "1H") for c in cells)

def test_preflight_is_exactly_declared_cell() -> None:
    (cell,) = build_cells("preflight")
    assert cell.archive_symbol == "BTCUSDT"
    assert cell.start.isoformat() == "2023-11-18T00:00:00+00:00"
    assert cell.end.isoformat() == "2023-12-17T23:59:00+00:00"
```

Add tests proving low disk, stale `.work`/`.publish`, existing run without a passing gate,
and invalid gate all refuse; only a passing gate returns `SKIP`.

- [ ] **Step 2: Verify RED**

Run: `cd python && .venv/bin/python -m pytest -q tests/test_exp100_matrix_runner.py`

Expected: module does not exist.

- [ ] **Step 3: Implement matrix and fail-closed resume logic**

Use frozen tuples copied from the design. Cell IDs contain venue, symbol, timeframe,
confirmation method/reference, and level config with filesystem-safe lowercase tokens.
Validate gate JSON by requiring `blocking_pass is True`.

- [ ] **Step 4: Verify GREEN**

Run the focused matrix tests; expected PASS.

### Task 3: Serial Subprocess Orchestration

**Files:**
- Modify: `python/experiments/EXP-100/code/run_matrix.py`
- Modify: `python/tests/test_exp100_matrix_runner.py`

**Interfaces:**
- Produces: `cell_command(cell, ...) -> list[str]`.
- Produces: `gate_command(cell, ...) -> list[str]`.
- Produces: `run_matrix(...) -> int` and CLI `main()`.

- [ ] **Step 1: Write failing command and journal tests**

Assert the command includes the selected catalog, full cell identity, venue TRAIN dates,
RSS limit, chunk size, and `--destroy-control`. Assert gate command includes the exact
symbol and output path. With a fake subprocess runner, assert `STARTED` then `VALIDATED`
JSONL entries and stop-on-failure behavior.

- [ ] **Step 2: Verify RED**

Run the focused matrix test; expected missing orchestration functions.

- [ ] **Step 3: Implement serial execution**

Before each launch: apply resume checks, reject stale staging paths, require configured
free bytes. Run the child with a timeout. Journal `STARTED`, then `PUBLISHED`, then
`VALIDATED`; journal `FAILED`, `TIMEOUT`, `INVALID`, or `LOW_DISK` before stopping where
applicable. Flush and `fsync` each journal append.

- [ ] **Step 4: Verify GREEN and static checks**

Run:

```bash
cd python
.venv/bin/python -m pytest -q tests/test_exp100_matrix_runner.py tests/test_exp100_runner.py tests/test_estimand_validation_v2.py
.venv/bin/ruff check experiments/EXP-100/code/run_experiment.py experiments/EXP-100/code/run_matrix.py tests/test_exp100_matrix_runner.py tests/test_exp100_runner.py src/xen/nautilus/catalog_fence.py
```

Expected: PASS and Ruff clean.

### Task 4: Independent QA and Production Preflight

**Files:**
- Append: `python/experiments/EXP-100/qa-review.md`
- Create at runtime: `python/experiments/EXP-100/results/execution/preflight-journal.jsonl`
- Create at runtime: `python/experiments/EXP-100/results/execution/preflight/*.json`
- Create at runtime: `data/nautilus_runs/EXP-100/preflight/*/`
- Update: `docs/superpowers/plans/2026-08-12-exp-100-progress-handoff.md`

- [ ] **Step 1: Run focused and full verification**

```bash
cd python
.venv/bin/python -m pytest -q
.venv/bin/ruff check src/xen/exp100 src/xen/nautilus/catalog_fence.py experiments/EXP-100/code tests/test_exp100_*.py tests/test_estimand_validation_v2.py
```

Expected: all tests pass; only the documented existing NumPy warning may appear.

- [ ] **Step 2: Obtain fresh-context QA**

Reviewer traces both venue fences, the 936-cell expansion, one-process-per-cell, destroy
control, TRAIN bounds, fail-closed resume/resource behavior, and the cTrader safety gate.
Append QA run 8; required verdict: APPROVE.

- [ ] **Step 3: Run preflight**

```bash
cd python
.venv/bin/python experiments/EXP-100/code/run_matrix.py --mode preflight
```

Expected: one atomically published emission and one passing integrity JSON. Stop on timeout,
memory abort, low disk, or invalid gate.

- [ ] **Step 4: Record feasibility without launching full mode**

Read run metadata and artifact sizes, calculate transparent serial and disk projections for
936 cells, update the handoff, and report whether full execution is operationally feasible.
Do not launch `--mode full` automatically.
