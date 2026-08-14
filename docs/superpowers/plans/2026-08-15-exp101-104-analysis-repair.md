# EXP-101–104 Analysis Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make EXP-101–104 analysis executable, fail-closed, complete, computationally bounded,
and organized around one canonical shared mechanics package with four explicit adapters.

**Architecture:** `xen.liqswp_analysis` owns only shared result contracts, source sealing,
statistics, future-destroy integrity, and orchestration. Each experiment's `analysis.py` owns
its design-specific population, comparator, grouping, golden fixture, and output rows. All
behavior changes start as failing synthetic tests; no live data analysis is run.

**Tech Stack:** Python 3.12, NumPy, Polars, pytest, Ruff, `xen.estimand_validation` boundaries.

## Global Constraints

- Never load TEST or HOLDOUT; never execute Nautilus or a live EXP-101–104 analysis.
- Preserve amended `design.md` files and append-only `qa-review.md` history.
- The latest QA section per experiment is the unresolved-finding authority.
- Integrity executes before value; failed integrity yields affected-observation `VOID` and no
  value row.
- Zero cost uses the canonical disclosure verbatim; no MDE, power gate, PSR gate, or machine
  economic label.
- Whole-`level_id` circular cluster bootstrap; report block lengths 2, 5, and 10.
- Future-destroy uses exact design grouping, zero-fixed-point derangements, identical raw/
  destroyed/SE populations, and `INTEGRITY_Z=2.8` only as a validity bite.
- Keep every row/count/reason visible; pooled output is disclosure-only.
- Do not absorb unrelated dirty-worktree changes.

---

### Task 1: Canonical result and statistical contracts

**Files:**
- Create: `python/src/xen/liqswp_analysis/__init__.py`
- Create: `python/src/xen/liqswp_analysis/contract.py`
- Create: `python/src/xen/liqswp_analysis/statistics.py`
- Create: `python/tests/liqswp_analysis/test_contract.py`
- Create: `python/tests/liqswp_analysis/test_statistics.py`

**Interfaces:**
- Produces: `ZERO_COST_DISCLOSURE: dict[str, str]`, `IntegrityStatus`, `AnalysisResult`,
  `estimate_contrast(...)`, `circular_cluster_indices(...)`,
  `clustered_contrast_bootstrap(...)`, and `block_sensitivity(...)`.
- `clustered_contrast_bootstrap` returns counts, `L_eff`, five seed intervals/ranges,
  `finite_draws`, `nonfinite_draws`, and an explicit `reason`; it never returns a silently
  poisoned interval.

- [ ] **Step 1: Write failing contract tests**

  Add literal assertions that the disclosure has all canonical fields and exact canonical
  text, integrity status cannot contain value labels, and JSON serialization preserves an
  explicit VOID reason.

- [ ] **Step 2: Run contract tests and verify RED**

  Run:
  `PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/liqswp_analysis/test_contract.py`

  Expected: collection/import failure because `xen.liqswp_analysis.contract` does not exist.

- [ ] **Step 3: Implement the minimal typed contract**

  Define frozen dataclasses and one canonical disclosure constant. `AnalysisResult.to_dict()`
  must emit `integrity`, `value_rows`, `population`, `source`, and `zero_cost_disclosure`.

- [ ] **Step 4: Run contract tests and verify GREEN**

  Run the Step 2 command; expected all tests pass.

- [ ] **Step 5: Write failing statistics tests**

  Use hand-derived two-arm cluster fixtures to prove contrast orientation, whole-cluster
  circular sampling, L=2/5/10 presence, explicit `ONE_CLUSTER`, and finite-draw filtering.
  Include a thin joint resample whose one seed produces NaN: the expected behavior is a finite
  interval from remaining draws plus the exact rejected count, or VOID if none remain.

- [ ] **Step 6: Run statistics tests and verify RED**

  Run:
  `PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/liqswp_analysis/test_statistics.py`

  Expected: import failures for the unimplemented functions.

- [ ] **Step 7: Implement minimal shared statistics**

  Use numeric arrays and cluster-index arrays. Keep the estimator population explicit through
  `PopulationView(label, arm, comparator, row_indices, cluster_ids, values)` so raw and control
  calculations can assert the same `population_id`.

- [ ] **Step 8: Run Task 1 tests and commit**

  Run both Task 1 files, Ruff on the new package/tests, and `git diff --check`. Commit only Task
  1 files with `feat: add liquidity-sweep analysis contracts`.

---

### Task 2: Fail-closed future-destroy engine

**Files:**
- Create: `python/src/xen/liqswp_analysis/destroy.py`
- Create: `python/tests/liqswp_analysis/test_destroy.py`
- Modify: `python/src/xen/liqswp_analysis/contract.py`
- Modify: `python/src/xen/liqswp_analysis/statistics.py`

**Interfaces:**
- Produces: `DestroySpec(group_columns, null_columns, channels)`,
  `derange_indices(n, rng)`, `build_destroy_mappings(frame, spec, seeds)`, and
  `future_destroy_attestation(population, mappings, ...) -> IntegrityStatus`.
- `IntegrityStatus.blocking_pass` is false for singleton/undestroyable groups, fixed points,
  no changed eligible values, population mismatch, non-finite statistics, or survival.

- [ ] **Step 1: Write failing integrity regressions**

  Add one test per realistic mutation: accepting a singleton, retaining a fixed point, adding
  an undeclared grouping key, changing raw/SE population IDs, changing no eligible value,
  swallowing VOID counts, or returning value rows after a failed attestation.

- [ ] **Step 2: Run and verify RED**

  Run:
  `PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/liqswp_analysis/test_destroy.py`

  Expected: missing API failures.

- [ ] **Step 3: Implement reference destroy behavior**

  Implement a simple array/index reference path first. Group only by `DestroySpec`; generate
  true derangements; record group sizes, mapping counts, fixed points, moved eligible values,
  and named VOID reasons. Assert identical `population_id` for raw, destroyed, and outer SE.

- [ ] **Step 4: Verify GREEN, then add optimized parity test**

  Run Step 2. Add a literal small fixture comparing reference and batched mappings/estimates
  exactly for five seeds and all registered channels; verify it fails before optimization.

- [ ] **Step 5: Implement bounded array batching**

  Precompute mappings once per group/seed, reuse across columns, and evaluate draws in bounded
  chunks. Do not copy row dictionaries. Preserve exact reference results on the parity corpus.

- [ ] **Step 6: Run Task 2 tests and commit**

  Run Task 1–2 tests, Ruff, and `git diff --check`. Commit Task 2 files with
  `feat: enforce future-destroy integrity`.

---

### Task 3: Gate-first TRAIN source sealing

**Files:**
- Create: `python/src/xen/liqswp_analysis/source.py`
- Create: `python/tests/liqswp_analysis/test_source.py`

**Interfaces:**
- Produces: `SourceSpec`, `SourceAttestation`, `validate_source_contract(...)`,
  `scan_train_columns(...)`, `validate_causal_order(...)`, and `join_profiles_left(...)`.
- Source validation accepts supplied synthetic paths/frames, enabling real behavior tests
  without reading retained market data.

- [ ] **Step 1: Write failing source-seal tests**

  Build a temporary 2-cell synthetic emission containing complete gate, metadata, event hash,
  raid, mark, and profile artifacts. Derive literal expected attestations. Mutate one fact per
  test: missing per-cell gate, config-hash mismatch, row config mismatch, duplicate object ID,
  count mismatch, timestamp after TRAIN, causal inversion, unmatched profile, and unexpected
  source configuration.

- [ ] **Step 2: Run and verify RED**

  Run:
  `PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/liqswp_analysis/test_source.py`

  Expected: import/API failures.

- [ ] **Step 3: Implement minimal gate-first validation and projected scans**

  Validate all gate/metadata/hash facts before scanning Parquet. Use `pl.scan_parquet().select()`
  with explicit columns and partition filters. Keep census and unmatched-join evidence in the
  returned attestation. Fail closed on any mismatch.

- [ ] **Step 4: Add a no-whole-emission-materialization regression**

  Exercise a synthetic multi-file scan and assert only requested columns/partition rows reach
  collection; the public source API must not return `list[dict]`.

- [ ] **Step 5: Run Task 3 tests and commit**

  Run Task 1–3 tests, Ruff, compilation, and `git diff --check`. Commit Task 3 files with
  `feat: seal liquidity-sweep TRAIN sources`.

---

### Task 4: Shared runtime and executable adapters

**Files:**
- Create: `python/src/xen/liqswp_analysis/runtime.py`
- Create: `python/tests/liqswp_analysis/test_runtime.py`
- Modify: `python/experiments/EXP-101/analysis_code/analysis.py`
- Modify: `python/experiments/EXP-102/analysis_code/analysis.py`
- Modify: `python/experiments/EXP-103/analysis_code/analysis.py`
- Modify: `python/experiments/EXP-104/analysis_code/analysis.py`

**Interfaces:**
- Produces: `ExperimentAdapter` protocol with `source_spec()`, `destroy_spec()`,
  `fixture_frame()`, `build_populations(frame)`, `analyze_valid(population)`, and
  `extra_integrity(frame)`; `run_fixture(adapter, output)` and
  `run_live(adapter, source_root, gate, output)`.
- Four scripts remain CLI entry points with `--fixture`, `--live`, `--source-root`, `--gate`,
  and `--output`. Live defaults point only at registered TRAIN artifacts but are never invoked
  during implementation verification.

- [ ] **Step 1: Write failing runtime tests**

  Use a real minimal adapter and temporary synthetic source. Assert integrity executes first,
  failed integrity writes only VOID/no value rows, valid live mode writes a complete artifact,
  writes are atomic, and a simulated exception leaves no final partial artifact.

- [ ] **Step 2: Run and verify RED**

  Run:
  `PYTHONPATH=python/src python/.venv/bin/python -m pytest -q python/tests/liqswp_analysis/test_runtime.py`

  Expected: missing runtime failures.

- [ ] **Step 3: Implement runtime**

  Add deterministic JSON serialization and a temporary-sibling/`Path.replace` writer.
  `run_live` orders source validation → experiment integrity → future destroy → value analysis.

- [ ] **Step 4: Replace copied mechanics with thin adapters**

  Preserve each existing public helper only where tests or design review need it; otherwise
  remove copied bootstrap, destroy, disclosure, gate, and orchestration functions after their
  callers move to `xen.liqswp_analysis`. Each `main()` must invoke the shared fixture/live path,
  not print a row count.

- [ ] **Step 5: Run runtime and existing contract tests**

  Run Task 1–4 tests plus `python/tests/test_exp10x_analysis_contract.py`. Repair tests that
  asserted duplicated private structure; retain behavior-level contract coverage.

- [ ] **Step 6: Commit Task 4**

  Run Ruff, compilation, and `git diff --check`. Commit shared runtime and four adapters with
  `refactor: organize EXP-101-104 analysis runtime`.

---

### Task 5: Complete experiment-specific outputs and integrity

**Files:**
- Create: `python/tests/liqswp_analysis/test_exp101_adapter.py`
- Create: `python/tests/liqswp_analysis/test_exp102_adapter.py`
- Create: `python/tests/liqswp_analysis/test_exp103_adapter.py`
- Create: `python/tests/liqswp_analysis/test_exp104_adapter.py`
- Modify: the four `analysis_code/analysis.py` adapters

**Interfaces:**
- Produces complete deterministic fixture/live result rows documented in the approved design
  §5–6; no adapter returns a machine economic verdict.

- [ ] **Step 1: Write EXP-101 failing tests**

  Assert exact family baselines, five-bit null class, raw/destroyed population identity,
  price/bps/ATR/duration/strong-move rows, separate arm/comparator census, L=2/5/10, destroy
  interval and collapse output.

- [ ] **Step 2: Implement EXP-101 minimal adapter behavior and verify GREEN**

  Run only `test_exp101_adapter.py`, then Task 1–4 tests.

- [ ] **Step 3: Write EXP-102 failing tests**

  Assert `0/1/2+` derivation without source mutation, exact counts/config populations, censor
  tables, registered continuous/binary/raw outputs, singleton VOID, and production-path fixture.

- [ ] **Step 4: Implement EXP-102 minimal adapter behavior and verify GREEN**

  Run only `test_exp102_adapter.py`, then Task 1–4 tests.

- [ ] **Step 5: Write EXP-103 failing tests**

  Assert authoritative left join, profile census, selected-mask and VA/TPO conservation,
  strict 50% tight-gap boundary, explicit undefined reasons, all-defined/tight/non-tight rows,
  amended golden replay, and refusal of false-versus-false arms.

- [ ] **Step 6: Implement EXP-103 minimal adapter behavior and verify GREEN**

  Run only `test_exp103_adapter.py`, then Task 1–4 tests.

- [ ] **Step 7: Write EXP-104 failing tests**

  Assert authoritative regime/profile join, causal regime timestamp, frequency census,
  registered outcome/duration/secondary/regime rows, exact control grouping, and retained join
  evidence.

- [ ] **Step 8: Implement EXP-104 minimal adapter behavior and verify GREEN**

  Run only `test_exp104_adapter.py`, then Task 1–4 tests.

- [ ] **Step 9: Run all adapter tests and commit**

  Run all `python/tests/liqswp_analysis/` tests and `test_exp10x_analysis_contract.py`, Ruff,
  compilation, and `git diff --check`. Commit with
  `feat: complete EXP-101-104 analysis outputs`.

---

### Task 6: Fixtures, QA coverage ledger, and workspace verification

**Files:**
- Modify: `python/experiments/EXP-101/results/fixture_integrity.json`
- Modify: `python/experiments/EXP-102/results/fixture_integrity.json`
- Modify: `python/experiments/EXP-103/results/fixture_integrity.json`
- Modify: `python/experiments/EXP-104/results/fixture_integrity.json`
- Create: `python/experiments/EXP-101/results/qa-fix-coverage.json`
- Create: `python/experiments/EXP-102/results/qa-fix-coverage.json`
- Create: `python/experiments/EXP-103/results/qa-fix-coverage.json`
- Create: `python/experiments/EXP-104/results/qa-fix-coverage.json`
- Modify: `python/tests/test_exp10x_analysis_contract.py`
- Modify only if status is stale: `python/experiments/INDEX.md`

**Interfaces:**
- `qa-fix-coverage.json` maps every issue number in the latest QA run to test node IDs and the
  implementing file; it contains no new QA verdict.

- [ ] **Step 1: Run fixture CLIs through production runtime**

  For each experiment run its `analysis.py --fixture --output <fixture path>` with
  `PYTHONPATH=python/src`. Run twice and compare SHA-256 hashes for determinism.

- [ ] **Step 2: Write and validate QA coverage ledgers**

  Map EXP-101 issues 1–8, EXP-102 issues 1–8, EXP-103 issues 1–7, and EXP-104 issues 1–7 to
  exact tests/files. Add a test that fails if an issue lacks a mapping or references a missing
  test node/file.

- [ ] **Step 3: Run bounded performance proof**

  Execute the reference/optimized parity benchmark on a synthetic registered-shape subset.
  Record rows, groups, seeds, peak allocation estimate, elapsed time, and exact parity in test
  output or a deterministic fixture section. It must prove no dictionary deep-copy path and no
  nested 10,000×2,000 destroy loop.

- [ ] **Step 4: Run complete verification**

  Run:

  ```bash
  PYTHONPATH=python/src python/.venv/bin/python -m pytest -q \
    python/tests/liqswp_analysis \
    python/tests/test_exp10x_analysis_contract.py \
    python/tests/test_exp100_analysis_probes.py \
    python/tests/test_estimand_validation.py \
    python/tests/test_estimand_validation_v2.py
  python/.venv/bin/python -m ruff check python/src/xen/liqswp_analysis \
    python/experiments/EXP-10{1,2,3,4}/analysis_code python/tests/liqswp_analysis \
    python/tests/test_exp10x_analysis_contract.py
  python/.venv/bin/python -m ruff format --check python/src/xen/liqswp_analysis \
    python/experiments/EXP-10{1,2,3,4}/analysis_code python/tests/liqswp_analysis \
    python/tests/test_exp10x_analysis_contract.py
  PYTHONPATH=python/src python/.venv/bin/python -m compileall -q \
    python/src/xen/liqswp_analysis python/experiments/EXP-10{1,2,3,4}/analysis_code
  ```

  Run `check_no_local_accounting` against every EXP-101–104 experiment directory and confirm
  all return `ok=true`. Run `git diff --check`.

- [ ] **Step 5: Audit the workspace**

  Inspect `git status --short`, file ownership, generated artifacts, caches/backups, and staged
  content. Ensure the amended designs and QA history are retained, no unrelated files changed,
  and no stale fixture/temp files remain.

- [ ] **Step 6: Commit the completed repair**

  Stage only EXP-101–104 designs/QA/adapters/results, canonical package, relevant tests/index,
  and this plan. Review `git diff --cached --stat` and `git diff --cached --check`; commit with
  `fix: complete EXP-101-104 analysis readiness`.

