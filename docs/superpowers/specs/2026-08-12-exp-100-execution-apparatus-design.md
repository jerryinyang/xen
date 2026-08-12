# EXP-100 Execution Apparatus Design

**Status:** operator approved 2026-08-12  
**Scope:** execution integrity and orchestration only; no experiment-method change

## Problem

EXP-100 has an approved 936-cell TRAIN grid but only a one-cell runner. Two execution
blocks remain:

1. the runner always loads and attests the Bybit INFR-011 fence, so cTrader emissions
   would carry the wrong manifest;
2. no resumable, resource-aware orchestrator exists, while an optimistic full-grid
   projection is 96 serial days and about 365 GB against 89 GB currently free.

## Decision

Implement the smallest apparatus that can safely measure and later run the frozen grid:

- venue-specific, repository-pinned catalog and fence definitions;
- one subprocess per cell using the existing one-cell CLI;
- deterministic grid expansion with stable cell IDs;
- append-only execution journal and skip-only resume for already validated cells;
- free-disk check before launch and a per-cell wall-time limit;
- integrity validation after each published cell;
- a dedicated 30-day BTCUSDT preflight mode; full-grid mode remains explicit.

The first execution after QA is the preflight only. Its purpose is operational sizing,
not research analysis or a value read.

## Frozen matrix

| Dimension | Values |
|---|---|
| Bybit instruments | BTCUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, ORDIUSDT, 1000BONKUSDT, TIAUSDT, DOGEUSDT, XRPUSDT, LINKUSDT |
| cTrader instruments | EURUSD, XAUUSD, USTEC |
| Observation minutes | 15, 30, 60 |
| Confirmation method | BREAKOUT_BAR, LEVEL_CLOSE |
| Confirmation reference | 1H for 15/30m; 1D for 60m |
| Level configuration | PREVIOUS_1H, PREVIOUS_4H, PREVIOUS_1D, PREVIOUS_1W, PREVIOUS_ASIA, PREVIOUS_EUROPE, PREVIOUS_AMERICA, ROLLING_16, ROLLING_32, ROLLING_64, ROLLING_128, ROLLING_256 |

Total: `10×3×2×12 + 3×3×2×12 = 936` cells.

## Venue pins

| Venue | Catalog | Fence | TRAIN bounds |
|---|---|---|---|
| BYBIT | `data/catalog` | INFR-011 manifest, SHA `35d3375e…00448` | 2021-06-29T06:53:00Z through 2023-12-18T00:00:00Z |
| CTRADER | `data/catalog_ctrader` | archived INFR-021 manifest, SHA `4cdc7b01…6de0` | 2021-06-02T00:01:00Z through 2023-11-22T00:00:00Z |

The one-cell runner derives the manifest from `cell.venue`; callers cannot pair a venue
with an arbitrary fence. The attestation records the actual repository-relative manifest
path and its hash. Both paths remain independently verifiable by
`xen.estimand_validation`.

## Scheduler contract

New file: `python/experiments/EXP-100/code/run_matrix.py`.

Modes:

- `preflight`: exactly one cell — BTCUSDT, 15m, BREAKOUT_BAR, 1H,
  PREVIOUS_1H, 2023-11-18T00:00:00Z through 2023-12-17T23:59:00Z.
- `full`: the frozen 936-cell grid across each venue's full TRAIN band.

Each cell runs as a fresh child process. On success, the scheduler invokes
`python -m xen.estimand_validation <run_dir> --expect <symbol> --out <gate_path>`.
Only `blocking_pass=true` records `VALIDATED`. Published-but-invalid emissions record
`INVALID` and stop the scheduler. Child failure, timeout, low disk, stale staging paths,
or an existing unvalidated run also stops without deleting data.

Resume behavior is conservative:

- a final run directory plus a passing gate is skipped;
- absent output is launched;
- any other state is refused for operator inspection;
- journal entries are append-only JSONL with cell ID, status, timestamps, elapsed time,
  run path, gate path, and process return code where available.

Default safety limits:

- serial execution (`jobs=1` only);
- RSS remains the existing 1.5 GiB per-cell limit;
- at least 20 GiB free before every launch;
- 2-hour wall-time limit per cell;
- full mode requires explicit `--mode full` and is not automatically entered after
  preflight.

## Preflight output

Root: `data/nautilus_runs/EXP-100/`.

- emission: `preflight/<stable-cell-id>/`;
- gate: `python/experiments/EXP-100/results/execution/preflight/<stable-cell-id>.json`;
- journal: `python/experiments/EXP-100/results/execution/preflight-journal.jsonl`.

After validation, record wall time, peak RSS, artifact bytes, event/raid counts, and
free disk. Project the frozen full grid transparently as an operational estimate. Do not
turn the estimate into a research gate or alter the grid to improve it.

## Testing

1. A supplied non-default manifest produces its actual repository-relative attestation
   path and hash.
2. A cTrader cell resolves only to the cTrader catalog/fence and Bybit only to Bybit.
3. Grid expansion is exactly 936 unique stable IDs with correct reference mapping.
4. Preflight expansion is exactly the declared cell and dates.
5. Scheduler refuses low disk and existing unvalidated/staged outputs.
6. Scheduler skips only a run with a passing gate.
7. Subprocess command includes destroy control, venue-specific catalog, and TRAIN bounds.
8. Focused EXP-100 tests, full suite, Ruff, fresh-context QA, real cTrader safety smoke,
   then the 30-day Bybit preflight and integrity gate.

## Explicit exclusions

- No concurrency, automatic retries, cleanup, repartitioning, sampling, shorter research
  horizon, level/raid lifetime change, schema change, TEST/holdout access, analysis, or
  experiment/family verdict.
- No automatic full-grid launch after preflight.
- No deletion of failed or partial artifacts.

## Deviations

None. This apparatus makes the approved two-venue scope executable without changing it.
