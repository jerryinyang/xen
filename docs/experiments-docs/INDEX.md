# Xen Experiments — Master Index (Chapter 03)

Live status + family navigation for the current chapter. Chapter 02 is archived at
`archive/chapter-02-mr-volharv-htfdi/experiments-docs/`; Chapter 01 at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first). Live ledgers: `docs/signal-registry/`.

## Current Checkpoint Status

**Active: [Checkpoint 011 — MTF Context Filters via XENA](checkpoints/2026-07-10-011-mtf-context-xena/design.md)**
(opened 2026-07-10). Family group [CF-MTFCTX-001](../signal-registry/candidate-families/cf-mtfctx-001.md)
REGISTERED. Runs XENA-001 (CTRL-01 RANDOM, next), XENA-002 (CTRL-02 MOMENTUM), XENA-003
(CTRL-03 REVERSION); 2,736 candidates each, 12 instruments (indices 10 + XAUUSD + BTCUSD).
First live XENA universes; carries C# batch runner + permutation-null battery deliverables.

## Current Infrastructure Tasks

| Item | Status | Detail |
|------|--------|--------|
| INFR-006 | **COMPLETE — FROZEN v3 2026-07-10** | XENA portfolio framework = default route (L-12 fix). Gross selection + A-4 dual gate (gross binding / net informational). Battery v3 (realistic correlated null): 0/300 end-to-end false → FPR ≤1%@95%; power 30 bps→70%, 40→94%. Frozen X=0.70/F_floor=0.4302/gate=0.0558, sha256 `537d691a…e672a6`, operator-signed. Spec: `docs/references/xena-lane.md`. At first live universe: C# batch runner, permutation-null battery. |
| INFR-008 | **COMPLETE 2026-07-12** | NEUTRAL amendment (INFR-007 follow-up, items #1/#2/#4): `grid_increments` add.at→bincount + monotone-events inverted searchsorted (bitwise-equal); kernel restructured to k-way merge cursors (one heap entry per open trade — same total key order ⇒ bitwise by construction); fold runs under `Python::detach` (GIL-free, 3× on 4 threads, results identical). All INFR-007 pins re-proven unchanged; rid-0 replay identical. 45-subset eval ~21 ms. Skipped #3 (lean eval), deferred #5 (full LAHC in Rust). Record: `python/experiments/INFR-008/report.md`. |
| INFR-007 | **COMPLETE 2026-07-12** | NEUTRAL amendment: XENA oracle event fold ported to Rust (`python/rust/xena_fold/`, PyO3). Bit-identical by proof: 500-case pinned parity corpus (bitwise sha256, `python/tests/test_xena_fold_parity.py`) + XENA-001 rid-0 replay (identical walk, 15,569 evals, 29 min local vs 640 min EC2). Default backend `rust`; registry v3 untouched. Finding: 1-ULP macOS↔Linux libm (`np.log`) divergence hits both backends → one universe adjudicates on one platform. Permutation-null battery now ~5 h local, $0. Record: `python/experiments/INFR-007/report.md`. |

## Family Indexes

| Family | EXP range | Status |
|--------|-----------|--------|
| [CF-MTFCTX-001](../signal-registry/candidate-families/cf-mtfctx-001.md) — MTF context filters on naive controls | XENA-001..003 (XENA lane) | REGISTERED 2026-07-10 |

## Checkpoint Retrospectives

(none yet this chapter)
