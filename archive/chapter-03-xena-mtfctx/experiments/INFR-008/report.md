# INFR-008 — XENA fold-kernel restructure + grid binning + GIL release — NEUTRAL amendment

**Status:** COMPLETE (2026-07-12) — all three approved items landed as one amendment;
all proof obligations PASS (bitwise). Operator-approved from the INFR-007 follow-up
speed review (items #1, #2, #4; #3 skipped, #5 deferred).
**Class:** NEUTRAL — numerically identical by proof, not claim. Frozen registry v3
untouched; no threshold, estimand, or emitted-data change. INFR-007 parity regime
(bitwise only, never allclose) retained unchanged — no tolerance relaxation was needed.

## What changed

### 1. `grid_increments` scatter kill (`xen/xena/search.py`)

`np.add.at` (unbuffered ufunc scatter over ~400–536k events) replaced by
`np.bincount(bins, weights)` — both accumulate sequentially in event order (same C-loop
order) ⇒ bit-identical. Profiling then showed the REAL dominant cost was
`searchsorted(grid, ev_t)` (23 ms of the 25 ms, branchy binary search 400k events →
135k-bar grid). Since `ev_t` is monotone (heap-pop order), the search is inverted:
`searchsorted(ev_t, grid, side="right")` + `diff` + `repeat` produces the identical
`bins` values with ~3× fewer probes over a contiguous array. Consumers
(`search.py`, `certify.py`, `final_gate.py`) unchanged — same function, same bits.

### 2. Kernel k-way merge restructure (`rust/xena_fold/src/lib.rs`)

The monolithic BinaryHeap (all ~63k entries pushed upfront + ~508k individual mark
pushes) is replaced by a deterministic merge of already-sorted streams:

- entries sorted once by their heap key `(t, PH_ENTRY, rank, k)`, consumed via one array
  cursor;
- each admitted trade's marks are ascending in `(t, seq)` and its exit key
  `(exit_t, PH_EXIT, rank, k)` sorts after its own last mark ⇒ ONE `Cursor` per OPEN
  trade walks marks-then-exit in key order;
- a small BinaryHeap holds only the open-trade cursors; each step compares the heap top
  against the next entry key.

Same total order over the same unique keys ⇒ identical pop sequence ⇒ identical float
accumulation order ⇒ bitwise-identical by construction. The Python `seq` push counter is
replayed exactly (marks get `seq+1..seq+m` at admission in schedule order; the counter
also bumps for the exit push, whose key remains `trade_k`). Per-mark money is computed
once at admission (schedule order — `gross` accumulation order unchanged) into a flat
buffer the cursors read back.

### 3. GIL release (`Python::detach`)

The fold now runs as a pure `fold_impl` over borrowed slices under `py.detach` — no
numeric change; enables thread-parallel evaluations (certification folds, permutation
batteries) in one process.

## Proof obligations (INFR-007 regime, unchanged)

| # | Obligation | Result |
|---|---|---|
| 1 | Synthetic adversarial parity (6 cases, bitwise Python vs Rust) | **PASS** |
| 2 | Pinned 500-case corpus, sha256 vs `tests/data/xena_fold_parity_hashes.json` (pins NOT regenerated) | **PASS** |
| 3 | `grid_increments` bitwise vs the old `add.at` path (full-universe + 45-subset, real XENA-001 events) | **PASS** (`.tobytes()` equal) |
| 4 | Thread-parallel results ≡ sequential results (8 subsets, 4 threads) | **PASS** (bitwise) |
| 5 | rid-0 budget-16000 replay vs local …527 baseline | **PASS** — see below |
| 6 | Full xena test suite (71 tests) | **PASS** |

## Replay credential (2026-07-12, local M-series)

rid 0, budget 16000: `best_F_hat` 4.027236467717527 (== INFR-007 local baseline, the
1-ULP-vs-EC2 libm caveat stands), `best_subset`/`n_iterations`/`n_kicks`/
`acceptance_rate`/`gate_rejection_rate` all equal to `search_restart_00.json`.
Wall: 12.2 min (INFR-007: 29.2 min; pre-Rust Python-equivalent: ~4.5 h).

## Measured payoff (local M-series, XENA-001 universe)

| Path | INFR-007 | INFR-008 |
|---|---|---|
| eval, 45-candidate subset | ~65 ms kernel | **~21 ms** total |
| eval, full 90-candidate universe | ~1.06 s | ~0.93 s (residual is Python-side ledger build — the skipped item #3) |
| `grid_increments` | ~25–33 ms | **~11 ms** (bitwise) |
| rid-0 replay (15,569 evals) | 29.2 min | **12.2 min** |
| thread scaling (4 threads, 8 evals) | n/a (GIL-bound) | **3.0×** |

## Deferred / skipped (operator triage)

- **#3 lean eval mode** (skip): the ~30k-row polars ledger build per eval is now the
  dominant cost on LARGE subsets; touches the `OracleResult` contract. Revisit only if
  full-universe evals become a hot path.
- **#5 full LAHC in Rust** (defer): drags bootstrap + proposal RNG streams into the
  parity surface and would reverse the operator-locked kernel-only scope. Revisit only
  if wall-clock still blocks the permutation battery.

## Consequences for open runs

Bit-identical by proof ⇒ XENA-001/002/003 continue unchanged; no in-flight result
invalidated. The XENA-002/003 pre-gate permutation-null battery now costs ~⅓ of the
INFR-007 estimate and can additionally thread-parallelize within one process.
