# SPDR-021/022/023 — analysis capacity problem

Recorded 2026-07-31. **Status: OPEN — operator decision required.** This document states a
capacity problem in the analysis stage. It carries no economic content, no result, and no verdict.

## One-paragraph statement

All six TRAIN cells are executed and hold `blocking_pass=true`. The analyser that turns them into
the 13 declared artifacts per cell has been made 30× faster with byte-identical output, and one
full cTrader cell now analyses in 12.8 minutes. But peak memory scales with the cell, and the two
30M-episode breach crypto cells project to roughly 80 GB on a 16 GB machine. Four of six cells are
not proven to fit. Nothing about the runs is in question; the constraint is the machine the
analysis runs on.

## What is measured, not projected

| item | measured value |
| --- | --- |
| SPDR-021 cTrader cell, full analysis | 766s, peak RSS 5.12 GB, 13 artifacts, rc 0 |
| 12-origin fixture, before optimisation | 892.7s, peak 347 MB |
| 12-origin fixture, after optimisation | 29.5s, peak 352 MB, **13/13 artifacts byte-identical** |
| suite after optimisation | `492 passed, 4 skipped` |
| Ruff after optimisation | clean |
| first (pre-optimisation) attempt on SPDR-021 cTrader | 5.5 GB and climbing, unfinished at 10 min |

The anchor for everything below is one real cell: 2.9M schedule rows → 766s and 5.12 GB.

## The projection

Scaling that anchor by schedule rows:

| cell | schedule rows | ×anchor | projected time | projected peak | fits 16 GB? |
| --- | --- | --- | --- | --- | --- |
| SPDR-021 cTrader | 2.9M | 1× | 12.8 min (measured) | 5.1 GB (measured) | yes |
| SPDR-022 cTrader | 13.0M | 4.5× | ~57 min | ~15–20 GB | marginal |
| SPDR-023 cTrader | 13.0M | 4.5× | ~57 min | ~15–20 GB | marginal |
| SPDR-021 crypto | 14.8M | 5.1× | ~65 min | ~20 GB | marginal |
| SPDR-022 crypto | 67.0M | 23× | ~4.9 h | ~80 GB | no |
| SPDR-023 crypto | 67.0M | 23× | ~4.9 h | ~80 GB | no |

Total sequential runtime ≈ 9 h, which is tolerable unattended. The peaks are the problem.

Treat the peak column as an upper-bound estimate: some of the 5.12 GB anchor is fixed overhead
rather than data-proportional, so the true peaks are likely lower. They are not likely lower by
the factor the two breach crypto cells need.

## Where the memory goes

`analyse_run` holds two wide working frames live through every stage: `native_results` and
`policy_results`, each the schedule (33 columns native, 55 policy) joined to entry/exit aggregates
and widened by 11 path-diagnostic columns. On a breach crypto cell that is 30.0M and 37.0M rows
held simultaneously, and every later stage reads from both.

The already-landed fixes removed the avoidable terms: boxed-float Python lists in the path
diagnostics, the whole 78.6M-row ledger staying resident past the point of use, multimillion-element
Python string sets in the reporting check, and per-draw DataFrame materialisation. What remains is
the two frames themselves.

## Options

**A. Column projection.** Keep only the ~20 columns the downstream stages actually read, right
after `_attach_results`. Bit-identical, small, verifiable by the same fixture-hash method already
used. Worth perhaps 2–3×, which brings the three marginal cells home. Does **not** rescue the two
breach crypto cells: 23× still lands near 30 GB. Recommended regardless, as it is cheap and
strictly reduces risk on the cells that are borderline.

**B. Per-symbol streaming.** Analyse one symbol at a time and concatenate. Every group key already
includes `symbol`, so the estimates should be preserved. Two caveats make this more than an
optimisation: row *order* becomes symbol-major instead of global first-appearance, so byte-identity
requires an explicit restoring sort; and any stage that aggregates across symbols must be
identified and handled rather than assumed absent. This changes the analyser's execution model and
needs its own test and operator sign-off.

**C. Run the two breach crypto cells on a larger machine.** ~128 GB instance, ~4.9 h per cell,
single-threaded so extra cores buy nothing beyond two. Transfer cost measured: the analyser reads
only 6 file kinds per cell, so the two cells are **60 files, 7.7 GB**; all six cells' inputs are
114 files, 10.1 GB; whole run directories are 798 files, 37.5 GB. Compression is pointless — every
input parquet is already ZSTD internally, measured saving 2.3% on the largest file. Do **not**
re-encode the parquets to shrink them: `row_accounting.json` and `determinism.json` pin a sha256
per source artifact, and re-encoding would break the replay-hash verification that proves these are
the emissions that passed integrity. Ship the bytes unchanged and verify sha256 on arrival.

If a cell is analysed off-machine, its second reproduction pass must run there too, and the
artifact hashes should be compared against a local cell's to show the instance produces the same
bytes. Egress of research data is an operator decision.

## Rejected

**Rust for the bootstrap inner loop.** Considered seriously and dropped. The reasoning that made
it attractive was that `np.mean` over a concatenated array uses pairwise summation, so only an
implementation preserving the identical operation order can stay bit-identical — which Rust can and
the sums-and-counts algebra cannot. But it addresses CPU, and after the four landed fixes CPU is no
longer binding: 9 h sequential is acceptable, and a 3–10× would not move the peak by a byte. The
INFR-007 precedent shows bit-identity is achievable in Rust, at the cost of a pinned parity corpus
and a dedicated task. Not worth it for a constraint that is not binding.

**Collapsing the bootstrap to per-block sums and counts.** Large speed win, but changes float
rounding, so it breaks byte-identical reproduction and shifts printed CI digits.

**Narrowing the grid, the arms or the dates to fit.** Out of bounds. The plan's stop conditions
make resource pressure a stop-and-report condition, not a licence to reduce scope.

## Recommendation

Do A now and re-measure. Then decide the two breach crypto cells between B and C. A is
bit-identical and cheap; B and C are the only two paths that finish those two cells, and choosing
between them is an operator call about whether to change the analyser's execution model or move
data off-machine.

## What is not affected

- The six runs, their integrity results and their row accounting stand unchanged.
- No TEST read, no holdout contact, no XENA action, no family-status change, no verdict.
- Nothing staged or committed.
- Task 11 (streaming order/position artifacts during the run) remains open and separate; it
  concerns engine memory during execution, not analysis memory.
