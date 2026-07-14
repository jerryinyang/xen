# Checkpoint 012 — XENA Referee Redesign (Chapter 03, Phase 2) — Retrospective

**Phase number:** 012 (Chapter 03, Phase 2) · infrastructure checkpoint (no candidate family)
**Opened:** 2026-07-13 (post-XENA adjudication audit) · **Closed:** 2026-07-14
**Status:** COMPLETED — INFR-009 delivered; XENA default route **RESTORED** under the exit-(c)
two-stage binder. Finalized 2026-07-14 at chapter-03 close (operator Phase-0 approval,
INFR-010 design §6).
**Slots / reads:** 0 gate slots; no counted TEST read; SEG_PROXY only for blind VAL; holdout
TEST band (2024-03-28→2024-12-11) and global holdout **never read**.

**Primary artifact:** `python/experiments/INFR-009/` (design.md §P3..§P5, report.md).
**Grounds:** checkpoint-011 MACHINERY-ALARM + adjudication audit
(`.ignore/temp/new-referee/post-xena-infr-audit.md`, five root causes).

---

## 1. Objective

Replace the INFR-006 v3 extensive-F/plateau XENA adjudicator (proven inoperative at live
scale, L-25) with a binder whose end-to-end FPR is certified at α=5% under the CAL discipline
(design/confirm bank split, predeclared n, point-α̂ gate, no optional stopping), then freeze,
blind-VAL on the three XENA fixtures, and restore or terminally withhold the default route.

## 2. Arc (what was tried, in order)

| Round | Form | Outcome |
|---|---|---|
| P3/P3b/P3c | percentile → refined LCB estimators | STOP — e2e α̂ up to 15%; knob-turning exhausted |
| P3d | leg-bootstrap studentized LCB | STOP — confirm e2e 8.5%/6.5%; **selection residual ~3pp** forced a binder-FORM change, not another estimator |
| P-BF | permutation-through-search (mean per-leg bps) | **DESIGN STOP** — bite PASS (96–99.7% plant collapse) but K-rule non-convergent on low (rel99=0.559 at K=99) + host hard-crash mid high-cadence; confirm never touched |
| **P-C** | **exit (c): two-stage sample-split** (stage-1 top-1 selection → 0.20-span embargo → stage-2 leg-studentized LCB, per-cadence) | **CONFIRM DUAL_CERTIFY** — e2e α̂ 5.0%/5.0% (10/200 both, boundary pass, Wilson upper 9.0%); **selection_inflation ≈0** (+0.5pp/+1.0pp vs P3d's ~3pp) — leak killed by construction |
| P4 | freeze + blind VAL (SEG_PROXY) | GROSS axis clean (001/002 rejected, 003 gross-certified +1.077, matches predeclared); **net axis invalid** — stream `cost_bps` under-charged on engine-costless emissions; route WITHHELD |
| P5 | net inject flat **1.0 bps** RT + re-VAL | **`VAL_PASS`** — 003 top-1 net −0.085, no fixture deployable; **route RESTORED**, registry v2 `db87dc1a…` (parent P4 `44e1aa3c…`) |

## 3. What the checkpoint proved

- **The binder-form pivot was the fix, not more knobs.** Three estimator rounds (P3..P3d)
  could not close the ~3pp selection residual; preventing the leak **by construction**
  (sample-split + embargo) closed it to ≈0 in one round. Canonized in methodology
  (iterated-calibration discipline).
- **XENA-003 cost-fatality reproduced blind.** The frozen binder, never having seen the
  fixtures, re-derived the known picture: 001 null rejected, 002 sub-zero rejected, 003 real
  gross (+1.077 LCB) that dies across the 0.7–1.5 bps breakeven→ruin band. Deployability at
  1.0 bps: none.
- **Cost must bind the objective (L-26 closure).** The engine-costless net path was the last
  L-22-shaped hole; P5's injected 1.0 bps floor makes NET a real verdict leg inside the
  frozen registry.
- **Honest margins recorded:** α̂ sits exactly on the 5.0% gate line at both cadences
  (predeclared point rule honored; thin margin, Wilson upper 9.0%); high-cadence bite was
  borderline (1/8). Neither re-run nor α-shopping is permitted on the frozen pin.

## 4. Standing state at close

- **Active pin:** `pc_frozen_registry.json` v2 sha256 `db87dc1a…` — frozen (c) procedure +
  1.0 bps net inject. Do not re-run (c) confirm; do not read holdout.
- **INFR-006 v3** extensive-F binders: SUPERSEDED-BY INFR-009 (artifacts retained, not binding).
- **Open items carried forward:** per-symbol spread pins still un-pinned (operator data needed
  before any live-scale deployability claim); L-27 next-open discriminating control required
  before any native-fill universe; plateau-ubiquity (root cause #4) an open design note.
- **Chapter boundary note (2026-07-14):** the INFR-010 migration (NautilusTrader engine, Bybit
  perp OHLCV data) declares this frozen registry **VOID on the new stack** — the (c) binder
  *form* and CAL discipline carry forward; the calibration constants are engine+data-specific
  and require a fresh CAL cycle before any crypto universe (INFR-010 §8 R4).

## 5. Slots / reads / holdout attestation

Gate slots 0; counted TEST reads 0; test-read ledger unchanged; global holdout never loaded;
`new_data_attestation` not invoked.

---

*Finalized 2026-07-14 by research-pipeline orchestrator at chapter-03 close (Phase 0,
INFR-010 design §6; operator-approved). Lessons L-25/L-26/L-27 were ratified at the
checkpoint-011 retrospective and live in `docs/knowledge-base/lessons-and-amendments.md`.*
