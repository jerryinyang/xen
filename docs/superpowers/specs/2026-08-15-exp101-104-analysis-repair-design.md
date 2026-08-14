# EXP-101–104 Analysis Repair Design

- **Date:** 2026-08-15
- **Status:** operator-approved design
- **Scope:** repair every unresolved finding in the latest fresh-context QA run for
  EXP-101, EXP-102, EXP-103, and EXP-104; consolidate the duplicated implementation;
  verify without reading TEST or HOLDOUT and without another QA run.

## 1. Outcome

The four analysis implementations become executable, bounded, fail-closed analysis
programs over the retained EXP-100 TRAIN emission. Shared mechanics have one canonical
implementation; each experiment retains a small explicit adapter for its own populations,
comparators, outputs, and design-specific integrity rules.

Completion requires:

1. every Critical and High issue in the latest appended QA section is covered by a
   regression test and implementation change;
2. `--live` performs the registered analysis and writes a complete result artifact;
3. every hard integrity failure prevents affected value output;
4. the registered 2/5/10 cluster sensitivities and 2,000 future-destroy draws are
   computationally bounded and do not deep-copy millions of Python dictionaries;
5. fixture results are produced through the production path and carry the canonical
   zero-cost disclosure verbatim;
6. the final diff is organized by ownership, contains no stale generated artifacts, and
   preserves the amended designs and append-only QA history.

The latest QA run in each `qa-review.md` is the repair authority. Earlier findings marked
resolved by that run are historical record and are not reopened.

## 2. Chosen architecture

### 2.1 Canonical shared package

Create `python/src/xen/liqswp_analysis/` with narrow modules:

| Module | Responsibility |
| --- | --- |
| `contract.py` | Canonical zero-cost disclosure, result schemas, explicit VOID/error reasons, registered constants. |
| `source.py` | Gate-first source sealing, projected TRAIN-only reads, per-cell metadata/hash/config/count reconciliation, row identity, timestamp causality, and profile joins. |
| `statistics.py` | Exact estimators, whole-cluster circular bootstrap, 2/5/10 sensitivity, finite-draw handling, explicit thin-population results. |
| `destroy.py` | Exact design grouping, deterministic zero-fixed-point derangements, array-based destroyed estimates, same-population outer uncertainty, non-vacuity, collapse disclosures, and fail-closed integrity status. |
| `runtime.py` | Shared fixture/live orchestration, bounded chunking, progress reporting, atomic result writing, and integrity-before-value ordering. |

These modules contain only mechanics reused by all four experiments. They do not encode
experiment-specific arm definitions or machine value labels.

### 2.2 Thin experiment adapters

Keep `python/experiments/EXP-10X/analysis_code/analysis.py` as the auditable entry point.
Each adapter declares directly:

- named populations and exclusions;
- the fixed comparator and contrast orientation;
- exact control grouping required by its design;
- requested outcome channels and census/disclosure tables;
- experiment-specific integrity checks and golden fixture;
- output row construction.

No generic configuration language or dynamic plugin registry is introduced. The adapters
call typed shared functions and remain readable against their respective `design.md`.

### 2.3 Why this boundary

Fixing four copies independently would preserve the defect multiplier. A single fully
parameterized family runner would conceal important differences among configuration,
raid-count, TPO-gap, and volatility-regime estimands. Shared mechanics plus explicit thin
adapters removes accidental duplication while keeping design fidelity reviewable.

## 3. Integrity flow

Every live run follows this fixed sequence:

1. validate the family estimand gate and all 264 per-cell execution gates;
2. reconcile gate config hashes, catalog/fence identity, metadata, event hashes, row counts,
   object IDs, symbols, timeframes, confirmation method/reference, and source configuration;
3. project and scan only required TRAIN columns; reject any timestamp beyond the pinned
   TRAIN boundary;
4. enforce row-level causal order for raid, return, sweep/confirmation, endpoint, ATR source,
   profile, and regime timestamps as applicable;
5. build the experiment's exact declared population and disclose every excluded, missing,
   censored, failed, or undefined row by named reason;
6. execute future-destroy on the identical population and estimator used by the raw read;
7. fail closed on singleton/undestroyable groups, fixed points, no changed verdict-bearing
   values, non-finite statistics, or surviving future information;
8. only for valid observations, compute value estimates, uncertainty, sensitivity, counts,
   and neutral report layers;
9. atomically write the registered results artifact with source identity and canonical
   disclosure.

An integrity failure yields an explicit affected-observation `VOID` record and no value row
for that observation. It never becomes a negative economic result and never remains a nested
informational string.

## 4. Statistical and performance design

- Cluster resampling uses the design-declared whole-`level_id` circular bootstrap.
- Block lengths 2, 5, and 10 are computed, with `L_eff`, cluster counts, seed ranges,
  intervals, and explicit reasons for unavailable intervals.
- Non-finite resamples are counted and excluded from percentile calculation; an interval is
  VOID when no finite draw remains. NaNs never silently poison or suppress a row.
- Future-destroy grouping is exact per experiment. Channel eligibility is handled as an
  explicit reconciled population, not by adding undeclared grouping keys.
- Derangement mappings are integer arrays. They are generated once per declared group/seed,
  verified to have zero fixed points, and reused across numeric columns.
- Source data remains columnar. Reads use projected Polars scans and bounded partition
  collection; rows are not materialized as a repository-wide list of dictionaries.
- Bootstrap and destroy calculations operate on numeric arrays and cluster index vectors.
  Work is chunked so the 2,000-draw control and 10,000-bootstrap settings have bounded memory.
- Reused mappings and sufficient statistics must be bit/equality checked against a simple
  reference implementation on small fixtures before the optimized path is accepted.
- Progress is reported at experiment/stratum/channel granularity, never per row or draw.

No sample count, interval, PSR, or control statistic becomes a machine value verdict.

## 5. Experiment-specific completion

### EXP-101

- configuration-family arms versus their exact fixed baselines;
- exact cross-configuration destroy grouping and five-bit nullness class;
- same-population raw/destroyed estimator and SE;
- raw price, bps, ATR, duration, and strong-move summaries;
- separate arm/comparator status, missingness, exclusion, control interval, and collapse rows.

### EXP-102

- derived count bands `0`, `1`, and `2+` without mutating source rows;
- exact count and configuration populations, censor tables, raw price/bps and registered
  continuous/binary outputs;
- singleton destroy groups are blocking VOID;
- fixtures exercise the production integrity implementation, not a private shortcut.

### EXP-103

- authoritative left join and reconciliation of raid/profile records;
- exact selected-bin mask, VA/TPO conservation, strict tight-gap boundary, undefined reasons,
  and all-defined/tight/non-tight populations;
- the amended golden profile trace is replayed from explicit inputs;
- false-versus-false comparisons are refused explicitly rather than emitted as arms.

### EXP-104

- authoritative raid/profile/regime joins and timestamp provenance;
- frequency census plus all registered outcome, regime, duration, and secondary layers;
- exact control grouping from the amended design;
- profile-join evidence is retained in the result artifact.

## 6. Result contract

Each experiment writes one deterministic JSON result beneath its own `results/` directory.
The artifact contains:

- experiment and source identities;
- gate, fence, hash, config, count, and causality attestations;
- named population funnel and exclusions;
- future-destroy mappings/counts, fixed-point count, changed-field/non-vacuity evidence,
  raw/destroyed estimates, uncertainty, interval, collapse ratio, and blocking status;
- every registered estimate at L=2/5/10 with counts and explicit unavailable reasons;
- experiment-specific secondary/census/profile/regime outputs;
- neutral `observed / ideal / interpretation` report-layer fields with no machine value tag;
- the canonical `ZERO-COST-DISCLOSURE` fields and wording verbatim.

Writes use a temporary sibling file followed by atomic replacement. A failed run leaves no
partially valid final artifact.

## 7. Test-first repair matrix

Before production edits, add failing synthetic tests for:

1. live mode writes a complete artifact and calls the registered analysis;
2. integrity runs before value rows and blocks affected observations;
3. raw, destroyed, and uncertainty populations are identical;
4. singleton/undestroyable groups are VOID and cannot be certified;
5. exact per-experiment grouping does not gain undeclared fields;
6. every derangement has zero fixed points and moves a verdict-bearing value;
7. fixtures invoke the production bootstrap/destroy path;
8. thin resamples produce finite intervals or explicit VOID reasons, never silent NaN;
9. L=2/5/10 outputs and all experiment-specific registered fields are present;
10. source hash/config/cell/count/object/causal checks fail closed;
11. EXP-103 malformed masks, conservation failures, and false-vs-false arms are refused;
12. EXP-104 regime/profile joins and frequency census are retained;
13. the canonical zero-cost disclosure is exact;
14. optimized array calculations equal the simple reference implementation;
15. input projection/chunking prevents whole-emission dictionary materialization.

Every regression follows red → green → refactor. Fixture generation occurs only after the
production path is green.

## 8. Workspace cleanup

- Preserve all operator-authored design amendments.
- Preserve every prior QA section; no QA history is rewritten or removed.
- Replace the four copied shared implementations with the canonical package and thin adapters.
- Keep the existing shared test file only if it remains cohesive; split it by contract,
  integrity, experiment adapters, and performance when that makes failures clearer.
- Regenerate only governed fixture artifacts whose producing code changes.
- Remove only files/imports/helpers made obsolete by this consolidation; do not clean unrelated
  repository code.
- Review the final staged diff by ownership: designs/QA history, canonical source, adapters,
  tests, and generated fixture artifacts. No temporary files, caches, backups, or stale fixture
  outputs remain.
- Do not commit or delete unrelated dirty-worktree changes.

## 9. Verification and stop condition

Verification includes focused red/green tests, the complete relevant Python test suite, Ruff,
format checking, compilation, `check_no_local_accounting` for all four experiment boundaries,
fixture regeneration and deterministic hash rerun, source/gate synthetic probes, and a bounded
performance probe of the optimized control path.

No live EXP-101–104 analysis, TEST read, HOLDOUT read, Nautilus execution, or confirmatory QA run
is part of this repair. The work stops when every latest-QA Critical/High item maps to a passing
regression or explicit artifact check, the final diff is organized, and no unrelated change was
absorbed.
