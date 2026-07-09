# Checkpoint 008 — CF-VOLHARV-001 Structure Harvest (2026-07-05)

**Phase container** for the HYP-002 adjudication. Predecessor: checkpoint-007
(EXP-019 verdict: SUPPORTED/ARTIFACT_CONFIRMED — the founding anomaly is a single-seed draw;
HYP-002 gate lifted by the signed retrospective). Family card:
`docs/signal-registry/candidate-families/cf-volharv-001.md`.

## Phase objectives

1. **Adjudicate HYP-002** via EXP-020: does a rebalance/grid structure convert the measured
   FX-block oscillation (VR 0.76–0.92 at H=6–48) into positive net expectation at capped
   inventory? Two arms: R (banded 50/50 rebalance vs unrebalanced twin), G (symmetric
   monthly-anchored grid vs direction-inverted twin). MR block primary, RW block negative
   controls; params candidate-blind from EXP-019 (`derive_exp020_params.py`, byte-reproducible).
2. **Family disposition at retrospective**: promote-to-next-hypothesis, iterate, or retire —
   operator-signed only.

## Carried blocker — live-session FTMO spread re-snapshot

The 2026-07-05 03:24 snapshot (`.ignore/temp/photos/`) is CLOSED-MARKET / weekend-widened
(e.g. EURUSD 2.19 bps vs ~0.2 live typical); **EURJPY missing entirely**. Usable ONLY as the
predeclared STRESS ceiling. Binding net reads require an operator live-session re-snapshot
(Monday). `xen.evaluation` raises on unpinned live spread — no silent NaN.

## Planned work

| Item | What | Gate |
|---|---|---|
| Param derivation | `derive_exp020_params.py` (reads EXP-019 artifacts only) → per-instrument b, g + implied-cadence table, appended as EXP-020 design A1; cells <4 implied crossings/month predeclared UNPOWERED-risk | before implementation; early exit if weekend-ceiling stress kills all MR-block cells on paper |
| EXP-020 build | 2 C# models (RebalanceHarvestModel, GridHarvestModel) + twin/invert flags; 64 confs + 4 delay-twin confs (NZDUSD/USDCAD both arms); EXP-019 `AnalysisEndUtc` fences | experiment-developer; golden traces are QA's |
| QA | fresh-context qa-compliance: declarations, param byte-diff (tripwire 2), golden traces T1–T3, exit-set diff | APPROVE before execution gate |
| Execution | 68 runs | OPERATOR gate (also needs live spread pin for binding reads) |
| Analysis → verdict | estimand gate per root → data-analyst → operator verdict → documenter | per INFR-001 |

## Constraints in force

- TRAIN only; TEST band never emitted; holdout sealed; 0 slots, 0 counted reads.
- Integrity gates hard (tripwires 1–3, estimand reconciliation, holdout); all quality reads
  informative — operator judges.
- Family status changes ONLY at this checkpoint's retrospective, operator-signed.
- No scope expansion after QA APPROVE.

## Exit condition

Retrospective written when EXP-020 has an operator verdict (or the paper-stress early exit is
taken) and the family disposition is decided. Possible outcomes: (a) MR-block harvest clears
pinned live costs → next-hypothesis scoping; (b) wash/contradicted → retire per family kill
criteria; (c) artifact alarm (RW-block CI-positive or tripwire trip) → fill forensics
supersedes.
