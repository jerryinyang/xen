# Experiment Index — Chapter 02

| ID | Title | Status | Key Finding | Date |
|----|-------|--------|-------------|------|
| EXP-001 | E1 cost-control arm (referee renew, D-referee) | COMPLETED | ACCOUNTING_MATERIAL — per-held-bar cost over-charges turnover ~L×; amortizing recovers ΔMDE 1.0–11.5 bps/stratum (median 1.5), scaling with cost & L. L-12 Mode-1 partly accounting, not just gate shape. analysis-only, 0 reads, holdout sealed. | 2026-06-28 |
| EXP-002 | E2 synthetic-positive battery + dogfood (referee renew, D-referee) | COMPLETED | Frozen gate SHAPE-BLIND: structurally blind to SPARSE/event edges (L1 readiness veto, edge-independent), degraded on STATE (L5 on pooled mean), robust to DENSE+TAIL. FPR=0/32 + dogfood 0/64; confirms L-12 §1/§2, localizes blindness to L1+L5 → scopes E3. analysis-only, 0 reads, holdout sealed. | 2026-06-29 |
| EXP-003 | E3a economic-leg adaptive gate — 3-arm DET-dominance (referee renew, D-referee) | COMPLETED | **DET-DOMINANT 32/32** (re-audit PASS, post-Amendment A1): adaptive recovers STATE (ΔMDE median 7.5, max 23.5 bps) + sparse (28/32; design "UNPOWERED" REFUTED, D0-compliant, L1 proven rigid) at dogfood FPR 0/32 ≤ frozen, no DENSE/TAIL loss, leak-clean. A1 studentized the sub-pop L5 (q\*-quantile/std > Q_STUD_MIN=Φ⁻¹(q\*), candidate-blind) — cured the high-σ FPR leak at the gate (orig raw-bps run's "15/17" was the brittle diagnostic that drove A1). Pulls E3b's return-series unit forward → E5 freeze. analysis-only, 0 reads, holdout sealed. | 2026-06-29 |

> Chapter 01 (EXP-001..098, VAL-001..005, INFR-001..003) is archived at
> `archive/chapter-01-price-geometry-referee/experiments/`. Hard-won knowledge is distilled in
> `docs/knowledge-base/` — read it before designing a new experiment.
