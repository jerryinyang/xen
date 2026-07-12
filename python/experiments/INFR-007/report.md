# INFR-007 — XENA oracle fold-kernel port (Rust) — NEUTRAL amendment

**Status:** COMPLETE (2026-07-12) — all proof obligations PASS; default backend flipped
to `"rust"`. One finding: cross-PLATFORM 1-ULP libm divergence (see §Replay), affects
both backends equally. Operator-approved from proposal
`.ignore/temp/new-referee/xena-infr-update.md` (drafted from XENA-001 runtime evidence).
**Class:** NEUTRAL — numerically identical by proof, not claim. Frozen registry v3
untouched; no threshold, estimand, or emitted-data change.

## Problem

One `xen.xena.oracle.evaluate` ≈ 1.0 s local / 2.4 s c7i (pure-Python event loop,
~571k heap pops + 32.7k mark-schedule builds per 60-candidate eval). 12-restart LAHC
≈ 128 CPU-h; pre-registered permutation-null battery (N=10 re-searches) practically
unaffordable (waived for XENA-001, operator 2026-07-12, no gate intent). XENA-002/003
have plausible gate spends where the battery is pre-gate-mandatory.

**Profile precondition (2026-07-12, local M-series):** cProfile confirms the fold
dominates — 1.7 s profiled eval entirely inside `evaluate` (0.65 s loop body, 0.32 s
heappop, 0.39 s `_trade_mark_schedule`); `grid_increments`+`bootstrap_F` = 44 ms.

## What changed (scope: kernel only — operator-confirmed 2026-07-12)

- New PyO3 crate `python/rust/xena_fold/` (Rust, f64-only, no mul_add/FMA, no
  reassociation, i64 ns timestamps). Implements ONLY the sequential event fold: heap of
  `(t, phase, rank, seq)` replicating heapq's tuple order (candidate-id string compare
  replaced by sorted-id rank — order-isomorphic; same global `seq` push counter), same
  float-op order incl. `equity`/`gross` accumulation order, same admission arithmetic,
  kernel-side L-18 reconciliation.
- `OracleConfig.backend = "python" | "rust"` (single dispatch point in `evaluate()`;
  nothing upstream changes). Default flipped to `"rust"` on credential PASS (2026-07-12).
  Build: `uv pip install ./rust/xena_fold` (from `python/`); missing kernel raises with
  that instruction; `backend="python"` remains the bit-identical fallback.
- Python keeps: parquet loading, per-trade mark schedules (`_trade_mark_schedule`
  unchanged, called from a per-(stream, segment) prepared-array cache — subset-independent),
  segment clipping + censoring, all sorting (numpy stays the tie-break authority),
  `grid_increments`, `bootstrap_F` (bootstrap RNG never enters the kernel), all of
  search/certify/final gate.
- LAHC search, certification, final gate: **zero code change** — they consume
  `evaluate()` unchanged.

## Proof obligations (proposal safety protocol)

| # | Obligation | Artifact | Status |
|---|---|---|---|
| 1 | Backend flag, default python | `xen/xena/oracle.py` | DONE |
| 2 | Golden parity gate, bitwise, CI-blocking | `python/tests/test_xena_fold_parity.py` — 6 synthetic adversarial cases (censored legs, same-timestamp collisions, single-bar trades, empty/singleton subsets, rejection cascade, segment-end censoring) + 500-case pinned corpus (`tests/data/xena_fold_parity_hashes.json`, sha256 digests from the Python-backend authority: 488 seeded random (subset, segment, cost-flag) cases over 4 segment variants + the 12 XENA-001 restart best-subsets) | **PASS** (all bitwise) |
| 3 | End-to-end replay credential | rid 0, budget 16000, Rust backend vs `XENA-001/results/search_restart_00.json` | **PASS with platform caveat** (below) |
| 4 | Governance | this record; registry v3 untouched; L-18 invariant retained kernel-side AND Python-side | DONE |
| 5 | Pin corpus + hashes in-repo | regenerate only via `tests/gen_xena_fold_parity_corpus.py` after operator-approved semantic change; toolchain upgrades must re-prove against pins | DONE |

## Replay credential result (2026-07-12)

Rust backend, rid 0, budget 16000, local M-series: **29.2 min wall** (reference Python
run: 639.8 min EC2). Identical across all 16,000 iterations: `best_subset` (45 ids),
`n_evaluations` 15569, `distinct_subsets` 15569, `acceptance_rate` 0.1124375,
`gate_rejection_rate` 0.113625, `n_kicks` 12. Sole difference: `best_F_hat`
4.027236467717527 vs reference 4.027236467717526 — **1 ULP**.

**Attribution (kernel exonerated):** the PYTHON backend, run locally on the same
restart inputs, also yields 4.027236467717527 and is bitwise-equal to the Rust backend
(identical `equity` bytes). The 1-ULP divergence is macOS-vs-Linux libm (`np.log` in
`bootstrap_F`), hits both backends identically, and did not alter a single walk
decision. **Standing rule:** bit-identity claims hold per platform — run all restarts,
certification, and any permutation battery of one universe on ONE platform; never mix
EC2 and local outputs inside one adjudication.

## Measured payoff (local M-series, 60-candidate subsets)

- Eval: 1.02 s → ~70 ms (64 ms kernel + ~6 ms dispatch) — ~15× per eval. The
  previously negligible bootstrap layer (44 ms) is now co-dominant; per-iteration total
  ~115 ms.
- rid-0 replay (15,569 evals): ~4.5 h Python-equivalent → ~30 min local.
- 12-restart search: ~11 h EC2 wall (~$8) → ~30 min local wall (restart-parallel).
- Permutation-null battery (N=10 full re-searches): days + ~$80–100 → ~5 h local, $0.

## Consequences for open runs

XENA-001/002/003 are open (little post-execution documentation). On PASS of obligations
2+3, the default backend flips to `"rust"` and the three runs continue on the faster
oracle — reruns reproduce Python results bit-identically by construction, so no
in-flight result is invalidated.
