# Xen Experiments — Master Index (Chapter 03)

Live status + family navigation for the current chapter. Chapter 02 is archived at
`archive/chapter-02-mr-volharv-htfdi/experiments-docs/`; Chapter 01 at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first). Live ledgers: `docs/signal-registry/`.

## Current Checkpoint Status

**Active: [Checkpoint 011 — MTF Context Filters via XENA](checkpoints/2026-07-10-011-mtf-context-xena/design.md)**
(opened 2026-07-10). Family group [CF-MTFCTX-001](../signal-registry/candidate-families/cf-mtfctx-001.md)
REGISTERED. Runs XENA-001 (CTRL-01 RANDOM), XENA-002 (CTRL-02 MOMENTUM), XENA-003 (CTRL-03
REVERSION, native limit orders); 2,736 candidates each, 12 instruments (indices 10 + XAUUSD +
BTCUSD). First live XENA universes; carried the C# batch runner + permutation-null battery
deliverables.

**All three universes COMPLETED 2026-07-13** (search + certification + permutation battery;
**0/2 gate slots spent on every universe — no counted TEST read, holdout never loaded**):

| Run | Operator verdict | Headline |
|---|---|---|
| [XENA-001](../../python/experiments/XENA-001/report.md) | **MACHINERY-ALARM** | RANDOM control certified 4/12 finalists (33%) vs a 0.75% battery null rate. PROVEN: `F_floor` (0.4302) is an absolute threshold on an *extensive* statistic calibrated at 24 cands/400 budget — at live scale (2,736 cands) 12/12 finalists clear it 8–13×, leaving a plateau screen that passes 50.8% of pure noise. Emission layer clean; the defect is in the adjudication layer. |
| [XENA-002](../../python/experiments/XENA-002/report.md) | **NO DETECTABLE STRUCTURE** | Naive momentum sits +0.26 above the random control on the battery comparison (delta −1.41 vs −1.67), inside restart dispersion 2.90. Negative evidence for the CF-MTFCTX-001 arc. |
| [XENA-003](../../python/experiments/XENA-003/report.md) | **NOT SUPPORTED (magnitude)** | Reversion via native limit fills: real +1.958 bps/leg gross, breakeven RT spread 0.71 bps, 0/12 finalists survive 1.5 bps (band was 20–40 bps). 91.2% of the edge is the limit print, not the registered mechanism. V00 4.0× over-represented ⇒ thesis contradicted. |

**Blocking framework finding:** a post-XENA audit of the adjudication layer
(`.ignore/temp/new-referee/post-xena-infr-audit.md`, 2026-07-13) identifies five root causes
(extensive-vs-intensive F statistic; costless cadence-maximizing objective; permutation battery
confounded on non-grid-priced entries; plateau screen rewards ubiquity; governance sequencing) and
warrants a dedicated **INFR redesign**. Recorded recommendation: **no XENA universe should reach a
counted gate until the scale defect is resolved.** Family status + lesson ratification are the
operator's calls at the checkpoint-011 retrospective (not yet written).

## Current Infrastructure Tasks

| Item | Status | Detail |
|------|--------|--------|
| INFR-009 | **COMPLETE 2026-07-14 — P5 route RESTORED** | Exit (c) two-stage CONFIRM DUAL_CERTIFY (α̂ 5.0% boundary). P4 freeze+VAL gross clean. P5 net inject flat **1.0 bps** → re-VAL **PASS**; active pin `pc_frozen_registry.json` v2 `db87dc1a…`. 001/002 not certified; 003 gross-ok / not deployable. INFR-006 v3 extensive-F superseded. |
| INFR-006 | **SUPERSEDED-BY INFR-009** (artifacts retained) | Frozen v3 absolute extensive-F binders (X=0.70/F_floor=0.4302/gate=0.0558, sha256 `537d691a…`) retired from the binding path by INFR-009. Spec history: `docs/references/xena-lane.md`. Do not delete. |
| INFR-008 | **COMPLETE 2026-07-12** | NEUTRAL amendment (INFR-007 follow-up, items #1/#2/#4): `grid_increments` add.at→bincount + monotone-events inverted searchsorted (bitwise-equal); kernel restructured to k-way merge cursors (one heap entry per open trade — same total key order ⇒ bitwise by construction); fold runs under `Python::detach` (GIL-free, 3× on 4 threads, results identical). All INFR-007 pins re-proven unchanged; rid-0 replay identical. 45-subset eval ~21 ms. Skipped #3 (lean eval), deferred #5 (full LAHC in Rust). Record: `python/experiments/INFR-008/report.md`. |
| INFR-007 | **COMPLETE 2026-07-12** | NEUTRAL amendment: XENA oracle event fold ported to Rust (`python/rust/xena_fold/`, PyO3). Bit-identical by proof: 500-case pinned parity corpus (bitwise sha256, `python/tests/test_xena_fold_parity.py`) + XENA-001 rid-0 replay (identical walk, 15,569 evals, 29 min local vs 640 min EC2). Default backend `rust`; registry v3 untouched. Finding: 1-ULP macOS↔Linux libm (`np.log`) divergence hits both backends → one universe adjudicates on one platform. Permutation-null battery now ~5 h local, $0. Record: `python/experiments/INFR-007/report.md`. |

## Family Indexes

| Family | EXP range | Status |
|--------|-----------|--------|
| [CF-MTFCTX-001](families/cf-mtfctx-001/INDEX.md) — MTF context filters on naive controls ([registry card](../signal-registry/candidate-families/cf-mtfctx-001.md)) | XENA-001..003 (XENA lane) — all COMPLETED 2026-07-13 | REGISTERED 2026-07-10 (family status moves only at the checkpoint-011 retrospective) |

## Checkpoint Retrospectives

(none yet this chapter)
