# G2 Gate Review — Phase 011 Portfolio Authorization

**Date:** 2026-06-11
**Gate:** G2 — portfolio authorization (strict, predeclared), design §8.3;
composition threshold P5 (`D0-predeclarations.md`): membership ≥ 5 cells
spanning ≥ 3 distinct instruments.
**Adjudicated by:** desk review (research-pipeline governance), on operator
instruction 2026-06-11 ("Phase 011 completed — G2 review and retrospective").
**Inputs:** EXP-045 (`python/experiments/EXP-045/`: report.md, results.md,
results/membership.csv, results/exit_selection.csv, audit.md PASS,
post-experiment governance APPROVE).

---

## Verdict

```text
G2 STATUS: FAIL — membership set empty (0 cells vs P5 floor of ≥5 over ≥3 instruments)
TRACK C AUTHORIZATION: NOT GRANTED
PHASE OUTCOME: FOUNDATION_NON-TUNABLE (design §8.3 / §9)
TEST READS SPENT: 0 of ≤6 — Tracks C and D never open
```

The adjudication is mechanical. P5 requires ≥ 5 member cells over ≥ 3
instruments; EXP-045's `membership.csv` contains zero rows. Per design §8.3,
"if membership is empty or below threshold, the phase closes
FOUNDATION_NON-TUNABLE with no TEST read spent." No judgement call exists at
this gate.

## Basis

EXP-045 (TRAINING_DELIVERED, audit PASS — one cell reproduced from raw data
to full float precision; all 74 family-classifications and all 37 verdicts
re-derived with 0 mismatches) trained both G0-frozen exit families on the
37-cell COVERED grid authorized at G1 close:

- **35/37 cells NON_TUNABLE** under the design-§6 rule (of 74 family-cells:
  42 `endpoint_argmax`, 30 `flat_plane`); endpoint dominance is side-mixed
  (FH 12 low / 8 high; MAD 11/11) — the signature of a wandering best point
  on a noisy surface, not a too-narrow grid.
- **2/37 cells tunable but FLOOR_FAIL** with *negative* stability plateaus:
  EURUSD-1h FH(3) S(θ\*) = −3.45 bps; US500-2h MAD(1.0) S(θ\*) = −0.37 bps.
  The P4 floor (S(θ\*) ≥ +1×SE) requires a positive plateau; neither sign nor
  magnitude is close.
- **The failure is economic, not methodological.** Median net expectancy is
  −5 to −7 bps at every grid point of both families under the frozen
  CONSERVATIVE cost model (P2); 20/37 cells are net-negative at all 16 grid
  points; a gross proxy (best net + RT) is positive in 31/37. The few-bps
  gross bounce edge survives per-instrument training; the frozen costs
  consume it. Exit selection cannot manufacture net edge that gross does not
  contain.

No conservatism relaxation could flip the gate: the P4 floor requires a
positive plateau, the two tunable plateaus are negative, and TRAIN-selected
scores are winner's-curse upward-biased — making the empty membership more
credible, not less.

## Consequences

| Item | State |
| --- | --- |
| Track C (`EXP-018` portfolio-fitness read) | **NEVER OPENS.** The P1 threshold predeclaration is unspent; it stands as a frozen record only. |
| Track D (top-5 confirmations) | **NEVER OPENS** (membership empty; no ranking exists). |
| TEST-read ledger | **Unchanged** — 0 counted reads, 0 disclosures added this phase. All strata stand as backfilled at D0 (EURUSD-4h remains AT CAP). |
| EXP-029-analog parity (pre-TEST-read requirement, G1 review) | **Moot this phase** — no TEST read occurred; the requirement re-binds if any future phase reads a 2h or new-universe TEST stratum. |
| EXP-044 conditional follow-ups (second-horizon FPR check; precision-only re-run) | Second-horizon check **moot** (no Track D exits selected). Precision-only re-run remains an operator option for a future phase if the 37-cell coverage map proves limiting. |
| Phase 011 | **CLOSES — FOUNDATION_NON-TUNABLE.** Per design §9: the AVWAP baseline-entry substrate with per-instrument-trained exits is not tunable at frozen CONSERVATIVE costs; `/ENTRY` exploration or substrate change becomes the path. |
| Phase 008 frozen package (EURUSD-4h, FH H\*=12, all_legs) | Unaffected — remains the family's standing TEST-capped record. |

## Routing (design §9, FOUNDATION_NON-TUNABLE row)

The exit-side lever is now measured and exhausted on this substrate. The
untried levers that could raise gross per-event edge above the cost floor are
the deliberately-frozen entry-side branches (`/ENTRY`, `/ALPHA`,
`/MA-DOMAIN`) or a substrate-level revision; a cheaper execution layer is the
only other side of the inequality. Direction-setting belongs to the Phase 011
retrospective and the next phase design, not to this gate.
