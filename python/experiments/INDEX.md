# Chapter 05–06 Experiment Index

## Infrastructure (ad-hoc)

| ID | Status | Purpose |
|---|---|---|
| INFR-021 | **COMPLETE** 2026-07-25 — EURUSD/XAUUSD/USTEC → `data/catalog_ctrader/`; fence pin independent of Bybit | Ingest chapter-03 cTrader 1m timebars into Nautilus catalog |

## Chapter 06 — active

Checkpoint-017 open. Family `CF-VOLDIR-001` `REGISTERED`. SPDR-012/013 **complete**. Reflection C
**signed** (O3 + Decision A). SPDR-014 **screen complete** (disposition NONE; 016 opened by override);
SPDR-017 **closed**; SPDR-015 **screen complete — WORTH_EXPLORING** (per-arm, operator-signed
2026-07-24: ordinal swing-size gate + vol level-state labels/multi-bar gate route on; k=1 next-bar
NOT_WORTH).

Sequence brief: `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`

| ID | Family | Status | Purpose |
|---|---|---|---|
| SPDR-012 **(SPDR)** | CF-VOLDIR-001 | **COMPLETE** — vol level H1/H4 reliable; no within-day skill | Volatility characterisation |
| SPDR-013 **(SPDR)** | CF-VOLDIR-001 | **COMPLETE** — signed direction not adequate; ZZ mag IC 0.34–0.46 | Direction expectancy bps |
| SPDR-014 **(SPDR)** | CF-VOLDIR-001 | **SCREEN COMPLETE** (operator disposition 2026-07-24) — analyst INCONCLUSIVE / UNPOWERED_NOT_NULL (B-5); `residual_status=NONE`, 0 powered cells; integrity PASS; band non-selective (p_event≈1), continuation ≈ coin-flip; coherent SUGGESTIVE leads (shock-MOMO CI excl 0, E-TOUCH/E-CLOSE asymmetry, L→H vol-flip MOMO); **SPDR-016 OPENED by operator override** (`016_start_basis=OPERATOR_OVERRIDE`); 0 TEST reads | O3 primary product science |
| SPDR-015 **(SPDR)** | CF-VOLDIR-001 | **SCREEN COMPLETE — WORTH_EXPLORING (per-arm; operator-signed 2026-07-24)** — Group 2 conditioners. **2b ordinal swing-size gate** T-GT-CUR **WORTH_EXPLORING** (21/21 coins × 3 models; hit ~+20pt over base, IC≈0.37, CI-backed) — MED5 weaker WORTH_EXPLORING, MED10 INCONCLUSIVE. **2a R-MARKOV multi-bar level gate k=4/12 WORTH_EXPLORING** (16/16 coins H1; ΔBrier −0.025 k4 / −0.114 k12 = ~15%/33% less error than persistence, CI excl 0) + **HIGH/LOW vol-state labels WORTH_EXPLORING** (next-\|oo\| gap +35 bps HMM / +16 bps R-MARKOV). **2a k=1 next-bar NOT_WORTH** (thin; H4 k1 + R-HMM-RV forecast); R-SHOCK comparator only. Integrity PASS (hard_pass; golden G1–G4); control = true L-28 derangement both arms (collapse≈0; bite 98%/73%); QA run1 REVISE→run2 APPROVE. Fold into 014/016 by amendment only; no family status change; no XENA; 0 TEST reads | Conditioner science |
| SPDR-016 **(SPDR)** | CF-VOLDIR-001 | **DESIGN COMPLETE — OPEN by operator override** (2026-07-24; `016_start_allowed=true`, basis `OPERATOR_OVERRIDE`) — on 014's coherent SUGGESTIVE leads, NOT a powered residual (`residual_status=NONE`); residual object + policy deferred to 016 design | Refine named 014 residual |
| SPDR-017 **(SPDR)** | CF-VOLDIR-001 | **CLOSED — NOT_WORTH** (operator-signed 2026-07-24) — Group 3b independent mispricing; residual_status=NONE; integrity PASS; no model skill (IC≈0), DERIVED layer inert, M-ZONE ≤ Z-VOL; per-stratum UNPOWERED (B-5) | Predicted-price mispricing + 014 method |
| XENA-VOLDIR-001 | CF-VOLDIR-001 | **RESERVED** | Portfolio/search on graduated bases |

See checkpoint-017, `reflection-mid.md`, and `docs/references/chapter-06-governance.md`.

## Chapter 05 — closed path (no further authorised work)

| ID | Family | Status | Purpose |
|---|---|---|---|
| SPDR-011 | CF-VOLCONV-001 | **CLOSED** — L1 **NOT SUPPORTED**; see `report.md` | Partial-cost characterisation only |
| EXP-099 | CF-VOLCONV-001 | **RESERVED / NOT AUTHORISED** | Frozen-rule Nautilus reproduction |

Checkpoint-016 retrospective (CF-VOLCONV-001) still pending and independent of Chapter 06.
