# Omission: EXP-028 cTrader Per-Bar Streaming Parity

**Date**: 2026-06-09
**Checkpoint**: 2026-06-08-006-avwap-evaluation-correction (ACTIVE)
**Status**: OMISSION_RECORDED

## What EXP-028 Was Supposed To Do

EXP-028 was to re-screen the **faithful** selective AVWAP strategy under the
corrected event-level evaluation method (EXP-027). The phase design (§4) set a
binding faithfulness requirement: *"the only change vs. EXP-023 is the evaluation
method, not the trade logic."* Because **EXP-023's trade logic was executed as a
cTrader `Mode=StrategyHost` run** of the C# `AvwapBounceModel.cs` robot (emitting
`positions.parquet` / `events.parquet`), and because INFR-001/VAL-002 established
the cTrader per-bar streaming path as the programme's strategy-execution-validation
standard, "change only the evaluation method" implies the faithful re-screen should
have been produced **from that same execution path**, only swapping the per-bar
frozen suite for the EXP-027 event-level inference. Concretely:

1. Reuse EXP-023's C# `StrategyHost` code (`AvwapBounceModel.cs`) — corrected to
   open and track pyramid positions so pyramid bounces enter the position output.
2. Run the corrected C# strategy on cTrader via `tools/ctrader-cli/` (the same
   per-bar streaming infrastructure validated in VAL-002 and used in EXP-023).
3. Evaluate the emitted cTrader `positions.parquet` through the EXP-027 event-level
   inference pipeline.
4. Confirm parity and consistency between the **realtime cTrader per-bar streaming**
   output and the **Python-only re-analysis** results.

## What EXP-028 Actually Did

EXP-028 was implemented as a **pure Python re-analysis** that loads pre-computed
upstream artifacts (EXP-020 events, EXP-022 lifetime observations) and runs the
event-level inference on them. It does **not**:

- Reference or invoke the C# `AvwapBounceModel.cs`;
- Run any cTrader backtest via `tools/ctrader-cli/`;
- Ingest cTrader-emitted `positions.parquet` from a `StrategyHost` run;
- Verify that the C# strategy's per-bar streaming output produces the same
  events, lifetime returns, and event-level verdict as the Python re-analysis.

The Python re-analysis re-derives the strategy's events and returns from EXP-020/022
artifacts rather than from the actual C# per-bar streaming execution. This skips
the cTrader-in-the-loop validation that was the original purpose of the
direct-translation-and-backtest design.

**How this was reached (not a hidden defect):** EXP-028's approved `scope.md`
*explicitly and transparently* defined the experiment as a Python re-analysis that
loads EXP-020/EXP-022 artifacts — it never claimed a cTrader run. The Stage 4
pre-execution review correctly caught and fixed a different, higher-priority issue
(the recurrence of the Phase-005 framing-divergence error in the matched-control
construction) but did **not** flag that going Python-only departs from the EXP-023
execution lineage the faithfulness clause assumes. So EXP-028 is internally
consistent and correctly executed *against its own scope*; the gap is that neither
the scope nor governance carried the design's implicit "same execution path"
requirement forward. EXP-029 closes the gap; a governance note (below) records the
process lesson so future faithful re-screens state their execution path explicitly.

## Why This Matters

Without a cTrader per-bar streaming run:

- The `EVAL_SUPPORTED` verdict (all 3 domains `EVIDENCE_FOR`) rests entirely on
  Python re-analysis of upstream synthetic-event artifacts. The C# code path — the
  actual robot that would run in production — has **never executed the pyramid-
  inclusive faithful strategy at all**: the current `AvwapBounceModel.cs` *suppresses*
  pyramids (`pyramid_skipped`, single concurrent position; `AvwapBounceModel.cs`
  position branch), so the exact strategy EXP-028 found EVAL_SUPPORTED exists only
  as a Python re-aggregation of EXP-020/022 events, not as runnable code.
- Pipeline parity (VAL-002 established for MA crossover) is unconfirmed for the
  AVWAP baseline strategy. The Python re-analysis could differ from the C# per-bar
  output due to subtle differences in state-machine behavior, rounding, or
  completion-rule scanning (as seen in VAL-002 where 1h/4h differed ≤1.83 bps).
- The Phase 006 objective — "fix the yardstick, then re-screen the faithful
  strategy" — is only half-satisfied: the yardstick is fixed, but the re-screen
  bypasses the faithful strategy's actual execution environment.

## Resolution

A new experiment **EXP-029** is added to this checkpoint to close the omission:

| Experiment | Purpose |
|------------|---------|
| EXP-029 | Correct `AvwapBounceModel.cs` to open/track pyramid positions, run it on cTrader via per-bar streaming, evaluate through the EXP-027 event-level inference, and confirm parity with EXP-028's Python-only findings. |

EXP-029 is a **parity confirmation**, not a re-litigation: EXP-028's edge
measurement on the canonical EXP-020 event substrate remains a valid result. EXP-029
adds the missing production-path evidence. Per the EXP-029 parity criteria, a
CONSISTENT result upgrades EXP-028 to cTrader-confirmed; an INCONSISTENT result
downgrades the Python-only verdict to `EVAL_UNCONFIRMED` pending root-cause.

See `python/experiments/EXP-029/scope.md` for the full design.

**Strengthening (2026-06-09, post adversarial review).** A pre-execution review found
the original EXP-029 design would *run* the corrected C# but not *grade* it: the
binding estimand re-scans exits in Python, so a CONSISTENT result would certify only
the cTrader entry/signal emission, not the new concurrent-completion code. EXP-029 was
strengthened (before execution) so the C# now serialises its executed completion and
the harness grades it per event against the Python scan on the same feed
(**exit-parity**, binding), adds a feed-exact **5m signal-layer reconciliation** vs the
EXP-020 substrate, a **magnitude-equivalence** gate (so a divergence can downgrade, not
just fail to upgrade), the **pyramid split** in the count gate, and a hard-asserted
frozen-method hash. This closes the omission in spirit (the production completion code
is validated), not only in letter (the code runs).

## Process note (governance lesson)

EXP-028 satisfied its approved scope but silently dropped the EXP-023 execution
path. To prevent recurrence: **any "faithful re-screen" experiment must state its
execution path explicitly in scope** (cTrader per-bar streaming vs. Python
re-analysis of upstream artifacts), and Stage 4 pre-execution governance must check
that path against the lineage the faithfulness clause references. This is recorded
here rather than as a silent fix.
