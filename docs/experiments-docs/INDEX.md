# Chapter 05–06 Research Status

## Current checkpoint status

**CHECKPOINT-017 OPEN — SPDR-012/013 COMPLETE; REFLECTION C SIGNED (O3 + Decision A);
SPDR-014 SCREEN COMPLETE (INCONCLUSIVE / UNPOWERED; `residual_status=NONE`; SPDR-016 OPENED by
operator override); SPDR-017 SCREEN COMPLETE (residual_status=NONE); SPDR-015 SCREEN COMPLETE —
WORTH_EXPLORING (operator-signed 2026-07-24: ordinal swing-size gate + vol level-state labels &
multi-bar gate route on; k=1 next-bar NOT_WORTH; conditioners fold into 014/016 by amendment).**

Route: vol (`SPDR-012`) → direction (`SPDR-013`) → mid reflection →
**O3 sequence** `SPDR-014` (zone/event — **screen done, pin NONE; INCONCLUSIVE/UNPOWERED**) → `SPDR-015` (conditioners — **screen done; WORTH_EXPLORING**) →
`SPDR-016` (refine 014 residual — **OPEN by operator override**) → `SPDR-017` (independent #3 mispricing — **screen done, pin NONE**) →
conditional `XENA-VOLDIR-001`. TRAIN only; holdout sealed.

Governing RAW: `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`  
O3 sequence SoT: `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`  
Governance: [Chapter 06 governance](../references/chapter-06-governance.md)  
Checkpoint:
[017 structural vol-direction](checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md)  
Reflection:
[reflection-mid.md](checkpoints/2026-07-23-017-structural-vol-direction-programme/reflection-mid.md)

## Prior checkpoint (not closed)

**CHECKPOINT-016** — `CF-VOLCONV-001` still `REGISTERED`; SPDR-011 L1 **CLOSED NOT SUPPORTED**.
EXP-099 not authorised. Family retrospective still pending (independent of Ch.06).

## Current infrastructure tasks

| Task | Status | Exit condition |
|---|---|---|
| Chapter 05 cost/data preflight | **PASSED / NO-SPREAD AMENDMENT QA APPROVED** | Partial-cost / no-spread caveat remains binding for Ch.05–06 money figures |
| INFR-021 cTrader catalog (EURUSD, XAUUSD, USTEC) | **COMPLETE** 2026-07-25 | `data/catalog_ctrader/`; fence `python/experiments/INFR-021/artifacts/fence-manifest.json`; Bybit catalog untouched |

## Family indexes

- [`CF-VOLDIR-001`](../signal-registry/candidate-families/cf-voldir-001.md) — `REGISTERED`;
  checkpoint-017; SPDR-014 zone/event screen complete (`residual_status=NONE`; INCONCLUSIVE/UNPOWERED;
  016 opened by override); SPDR-015 conditioner screen complete (WORTH_EXPLORING — ordinal swing-size
  gate + vol level-state labels/multi-bar gate); SPDR-017 independent mispricing screen complete
  (`residual_status=NONE`); no XENA.
- [`CF-VOLCONV-001`](../signal-registry/candidate-families/cf-volconv-001.md) — `REGISTERED`;
  checkpoint-016; SPDR-011 L1 closed NOT SUPPORTED; retrospective pending.

## Current checkpoint

- [Checkpoint 017 design](checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md) —
  OPEN; C signed; 014 + 017 screens complete (both pin NONE); 016 open by override; 015 screen complete
  (WORTH_EXPLORING; conditioners fold into 014/016 by amendment).

## Prior checkpoint

- [Checkpoint 016 design](checkpoints/2026-07-22-016-volatility-direction-conversion/design.md) —
  OPEN (retrospective pending); SPDR-011 closed at L1.

## Checkpoint retrospectives

None in Chapter 05–06.
