# Chapter 05–06 Research Status

## Current checkpoint status

**CHECKPOINT-018 OPEN (2026-07-25) — Trade Opportunity Modelling / Capture Geometry.
SoT signed. `SPDR-018` + `SPDR-018B` COMPLETE AND CLOSED 2026-07-26 (`HYP-D5` SUPPORTED /
PARTIALLY SUPPORTED; no gating verdict from either). NEXT = the mid-checkpoint reflection
(inputs assembled, operator decision unsigned). `SPDR-019` / `SPDR-020` designs are complete;
`SPDR-020` QA run-5 fixes were applied 2026-07-29 and await fresh QA approval. Execution remains
unauthorised. TRAIN only; holdouts sealed.**

**Closed threads since:** **P4** — C3 is *terminally unpowerable* in its registered form (median cell
needs ~201 years of 25-symbol history); **P3** — CI fragility swept, seed spans ~4.8% of CI width, so
no read rests on a Monte-Carlo artifact; **P2** — median/trimmed CIs recovered on 451 arm-B cells, and
they reject zero where the mean does not. **P1 skipped by operator** (no 018C), so **C2 must be booked
at the retrospective as unresolved-and-parked — terminal `NOT_RESOLVABLE`, never a refutation.**

Binding premise: *Unconditional direction is dead. Conditional direction is unpowered, not refuted.
Volatility is a multiplier on a direction term, never a substitute for it.*

Organising identity: `E[net] = p·W − (1−p)·L − cost`, `p_be_net = (L+cost)/(W+L)`,
`edge = p − p_be_net`. **The target is not `p > 0.5` but `p` above its own break-even**,
satisfiable at `p < 0.5` when `W > L`. `W/L` is the natural handle for the capture branch;
κ is a diagnostic only. Direction is **measured, not targeted**.

Route: `SPDR-018` (**powering sweep over the complete 017 residue** — four arms, original statement,
no omissions, only authorised drop SPDR-017) → mid-checkpoint reflection →
`SPDR-019` (breakout baseline + opportunity-modulated capture) / `SPDR-020` (E-TOUCH/E-CLOSE
direction-aware capture) → conditional `XENA-VOLDIR-001`.

Checkpoint-018 SoT: `.ignore/what-next/alts/opportunity.md`  
Governance: [Chapter 06 governance](../references/chapter-06-governance.md)  
Checkpoint:
[018 trade-opportunity capture geometry](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/design.md)

**Blocking:** per-symbol spread pin is a prerequisite for any checkpoint-018 money read.  
**Deferred (operator):** pure direction-agnostic strategies (both-side / straddle / grid) — parked,
not refuted.

## Prior checkpoint (CLOSED)

**CHECKPOINT-017 CLOSED 2026-07-25 — `STRUCTURAL PACKAGE DELIVERED / EXTRACTION
UNRESOLVED-AT-POWER`.** SPDR-012/013 complete; Reflection C signed (O3 + Decision A); SPDR-014
screen complete (INCONCLUSIVE / UNPOWERED, `residual_status=NONE`, 0/927 powered); SPDR-015 screen
complete (WORTH_EXPLORING per-arm); SPDR-017 CLOSED NOT_WORTH; **SPDR-016 CLOSED — SUPERSEDED,
NEVER RUN** (DERIVED layer measured inert by SPDR-017; its target carried into SPDR-018). 0 counted
TEST reads; 0 multiplicity slots; family status unchanged; XENA never opened.

Governing RAW: `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`  
O3 sequence SoT: `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`  
Checkpoint:
[017 structural vol-direction](checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md)  
Reflection:
[reflection-mid.md](checkpoints/2026-07-23-017-structural-vol-direction-programme/reflection-mid.md)  
Retrospective:
[retrospective.md](checkpoints/2026-07-23-017-structural-vol-direction-programme/retrospective.md)

## Earlier checkpoint (not closed)

**CHECKPOINT-016** — `CF-VOLCONV-001` still `REGISTERED`; SPDR-011 L1 **CLOSED NOT SUPPORTED**.
EXP-099 not authorised. Family retrospective still pending (independent of Ch.06).

## Current infrastructure tasks

| Task | Status | Exit condition |
|---|---|---|
| Chapter 05 cost/data preflight | **PASSED / NO-SPREAD AMENDMENT QA APPROVED** | Partial-cost / no-spread caveat remains binding for Ch.05–06 money figures |
| INFR-021 cTrader catalog (EURUSD, XAUUSD, USTEC) | **COMPLETE** 2026-07-25 | `data/catalog_ctrader/`; fence `python/experiments/INFR-021/artifacts/fence-manifest.json`; Bybit catalog untouched |

## Family indexes

- [`CF-VOLDIR-001`](../signal-registry/candidate-families/cf-voldir-001.md) — `REGISTERED`;
  checkpoint-017 **CLOSED**, checkpoint-018 **OPEN**. 017 banked: reliable H1/H4 range vol level,
  forecastable next-swing magnitude, ordinal swing-size gate, multi-bar vol-state gate; measured
  dead: unconditional direction, error-dynamics features, predicted-price mispricing zones.
  018 registers `SPDR-018/019/020` (`HYP-D5/D6/D7`). **SPDR-018 + SPDR-018B closed 2026-07-26:**
  the 017 residue is now largely **powered** (1,413 signed cells against SPDR-014's 0 of 927) and the
  `(p, W, L)` layer is measured for the first time — the joint sits **at break-even**, **nothing clears
  `p_be_net`** on either universe, and `W/L` is ~97% the arithmetic **mirror of `p`** rather than a free
  lever (replicated on cTrader at R² 0.9746). Still `UNPOWERED`, not refuted: **C2 shock-MOMO** and
  **C3**. No XENA; family status unchanged.
- [`CF-VOLCONV-001`](../signal-registry/candidate-families/cf-volconv-001.md) — `REGISTERED`;
  checkpoint-016; SPDR-011 L1 closed NOT SUPPORTED; retrospective pending.

## Current checkpoint

- [Checkpoint 018 design](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/design.md) —
  **OPEN** 2026-07-25; SoT signed. **SPDR-018 and SPDR-018B both COMPLETE AND CLOSED 2026-07-26**
  (`HYP-D5` SUPPORTED / PARTIALLY SUPPORTED; **no gating verdict from either**). **Next item = the
  mid-checkpoint reflection**, which sets how SPDR-019/020 are parameterised, not whether they run.
  SPDR-019/020 registered; designs complete, execution unauthorised. Spread pin still **BLOCKING**
  for any money read.
- [Checkpoint 018 corrections log](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/corrections-log.md)
  — 2026-07-26; independent adversarial audit of the 018/018B documentation. **RELIABLE WITH
  CORRECTIONS**; both verdicts survive. Two critical fixes: the C2 ruling's third leg was false and
  now supports *not replicated*; `log R` is negative at the centre, not uniformly.
- [Checkpoint 018 reflection inputs](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-inputs.md)
  — 2026-07-26; the consolidated two-universe `(p, W, L, W/L, edge)` picture, the per-item 017 residue
  ledger, surviving open threads, and the written end-state options. **Operator decision unsigned.**

## Prior checkpoints

- [Checkpoint 017 design](checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md) —
  **CLOSED** 2026-07-25 (structural package delivered / extraction unresolved-at-power).
- [Checkpoint 016 design](checkpoints/2026-07-22-016-volatility-direction-conversion/design.md) —
  OPEN (retrospective pending); SPDR-011 closed at L1.

## Checkpoint retrospectives

- [Checkpoint 017 retrospective](checkpoints/2026-07-23-017-structural-vol-direction-programme/retrospective.md)
  — 2026-07-25; 0 TEST reads, 0 slots, family unchanged; SPDR-016 superseded unrun; residue routed to checkpoint-018.
- Checkpoint 016 retrospective — still pending (independent of Chapter 06).
