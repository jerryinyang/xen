# Chapter 05–06 Research Status

## Current checkpoint status

**CHECKPOINT-018 CLOSED 2026-08-07 — `CAPTURE GEOMETRY CHARACTERISED / NO EXTRACTABLE EDGE AT
THE MEASURED JOINT`. `CF-VOLDIR-001` RETIRED — CHARACTERISED, NOT TRADABLE (operator-signed).**
Retrospective:
[checkpoint-018 retrospective](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/retrospective.md).

The chapter closes with this checkpoint. `SPDR-018` + `SPDR-018B` powered the complete 017
residue on two independent universes; `SPDR-021/022/023` characterised adaptive capture geometry
(six TRAIN cells, run stamp `20260803T140238Z`, integrity-clean, 13/13 reproduction hashes);
`SPDR-024` measured the one surviving lever on estimands that could actually see it (four cells,
17 HARD each, H4 run for the first time in the programme).

**The finding.** The joint `(p, W, L)` sits **at net break-even** and nothing clears it — 0 of
1,413 powered crypto cells, 0 of 315 powered cTrader cells — with **91–96% of the distance being
cost, not rate**. `W/L` is **not a free lever**: it is ~97% the arithmetic mirror of `p`
(R² 0.9667 crypto / **0.9746** cTrader), movable 36–67× with `p` inverse and the mean unchanged.
Vol-gated hold, stop distance, trail and post-stop recovery are refuted at power. Vol-aware SIZE
has a consistent direction (236/236 rows, 6/6 cells) but a magnitude below its own detection floor
after the dedicated `SPDR-024` measurement. Vol state never clears zero as a baseline selectivity
contrast, on mean or Sharpe, in any cell.

**Standing exclusion carried forward:** spread is never charged programme-wide (2026-07-23) —
reported net is overstated and every money, expectancy and tradability claim stays refused by
AMENDMENT-C2. TRAIN only; **0 counted TEST reads; 0 multiplicity slots; holdouts sealed
throughout.**

**Booked as terminal `NOT_RESOLVABLE` — parked, never refuted:** **C2 shock-MOMO** (`SPDR-018B`
neither replicated nor refuted it; the comparator is not a neutral yardstick; P1 skipped by
operator, no 018C) and **C3** (terminally unpowerable in its registered form — the median cell
needs ~201 years of 25-symbol history). **C9, D3, D4 are OPEN and never run.** **P6** — Asia
magnitude × shock, ~+10 bps vs ~0 EU — is an unregistered lead.

**Closed diagnostic threads:** **P3** — CI fragility swept, seed spans ~4.8% of CI width, so no
read rests on a Monte-Carlo artifact; **P2** — median/trimmed CIs recovered on 451 arm-B cells,
and they reject zero where the mean does not.

Binding premise: *Unconditional direction is dead. Conditional direction is unpowered, not refuted.
Volatility is a multiplier on a direction term, never a substitute for it.*

Organising identity: `E[net] = p·W − (1−p)·L − cost`, `p_be_net = (L+cost)/(W+L)`,
`edge = p − p_be_net`. **The target is not `p > 0.5` but `p` above its own break-even**,
satisfiable at `p < 0.5` when `W > L`. `W/L` is the natural handle for the capture branch;
κ is a diagnostic only. Direction is **measured, not targeted**.

Route as executed: `SPDR-018` / `SPDR-018B` (**powering sweep over the complete 017 residue** —
four arms, original statement, no omissions, only authorised drop SPDR-017) → mid-checkpoint
reflection (evidence inventory, signed 2026-07-30) → `SPDR-021/022/023` adaptive-management
characterisation → confirmation extraction (signed 2026-08-05) → `SPDR-024` successor
characterisation → operator interpretation → **family retired**. `XENA-VOLDIR-001` was reserved
and **never opened** — no graduated base existed at any point.

Checkpoint-018 SoT: `.ignore/what-next/alts/opportunity.md`  
Governance: [Chapter 06 governance](../references/chapter-06-governance.md)  
Checkpoint:
[018 trade-opportunity capture geometry](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/design.md)

**Standing caveat:** spread is never charged programme-wide (2026-07-23); no checkpoint-018 money read is licensed, by rule rather than by pending work.  
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
  018 registered `SPDR-018` (`HYP-D5`). Two later capture-axis registrations were withdrawn and
  permanently voided on 2026-07-30 for design defects. Their replacements are
  `SPDR-021/HYP-D8`, `SPDR-022/HYP-D9` and `SPDR-023/HYP-D10`. **SPDR-018 + SPDR-018B closed
  2026-07-26:**
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
  (`HYP-D5` SUPPORTED / PARTIALLY SUPPORTED; **no gating verdict from either**). The evidence
  inventory and [replacement design](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md)
  are **approved**. SPDR-021/022/023 execution and analysis are **AMENDED RERUN COMPLETE; ANALYSIS COMPLETE; AWAITING OPERATOR INTERPRETATION** (2026-08-04).
  Spread **never charged** for any money read.
- [Checkpoint 018 corrections log](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/corrections-log.md)
  — 2026-07-26; independent adversarial audit of the 018/018B documentation. **RELIABLE WITH
  CORRECTIONS**; both verdicts survive. Two critical fixes: the C2 ruling's third leg was false and
  now supports *not replicated*; `log R` is negative at the centre, not uniformly.
- [Checkpoint 018 reflection inputs](checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid.md)
  — 2026-07-26; the consolidated two-universe `(p, W, L, W/L, edge)` picture, the per-item 017 residue
  ledger and surviving open threads. **Approved as an evidence inventory 2026-07-30; it remains
  evidence-only and takes no end-state.**

## Prior checkpoints

- [Checkpoint 017 design](checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md) —
  **CLOSED** 2026-07-25 (structural package delivered / extraction unresolved-at-power).
- [Checkpoint 016 design](checkpoints/2026-07-22-016-volatility-direction-conversion/design.md) —
  OPEN (retrospective pending); SPDR-011 closed at L1.

## Checkpoint retrospectives

- [Checkpoint 017 retrospective](checkpoints/2026-07-23-017-structural-vol-direction-programme/retrospective.md)
  — 2026-07-25; 0 TEST reads, 0 slots, family unchanged; SPDR-016 superseded unrun; residue routed to checkpoint-018.
- Checkpoint 016 retrospective — still pending (independent of Chapter 06).
