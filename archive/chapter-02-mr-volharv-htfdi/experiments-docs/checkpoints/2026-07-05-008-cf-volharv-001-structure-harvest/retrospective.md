# Checkpoint 008 Retrospective — CF-VOLHARV-001 Structure Harvest (2026-07-05)

**Family disposition: CF-VOLHARV-001 RETIRED** (operator decision 2026-07-05). Both core
hypotheses are closed negative — HYP-001 ARTIFACT_CONFIRMED (the founding anomaly is a draw),
HYP-002 NOT SUPPORTED (neither rebalance nor grid structure harvests the measured oscillation
at scale). The speculative HYP-003 (CF-VOLEXP tail long-vol) was never scoped and does not,
on its own, sustain an open family. The family retires having spent **0 slots, 0 counted TEST
reads, holdout sealed** throughout.

## Phase outcome vs objectives

| Objective | Outcome |
|---|---|
| Adjudicate HYP-002 via EXP-020 | **COMPLETE — NOT SUPPORTED (operator verdict 2026-07-05)**; `python/experiments/EXP-020/report.md` |
| Family disposition | **RETIRE** (this document) |

## Basis for the HYP-002 verdict

1. **ARM R (rebalancing premium)** — all 4 MR cells tiny-positive but **UNPOWERED** (MDE >
   effect). Design §8 over-stated the classical `w(1−w)σ²` premium ~100×; the true scale is
   ~0.04–0.07%/yr — economically negligible even if fully real. Only US2000 (mid, disclosure)
   CI-positive. Costs never binding for ARM R.
2. **ARM G (grid harvest)** — MR-block twin-spread scoreboard 1/4. USDCAD +132 bps/mo
   CI[+43,+257] survives commission / weekend-×4 stress / top-3 removal / both halves, **but
   fails** two SUPPORTED requirements: the inverted-twin sign-flip (momentum twin +3,491 —
   same sign) and the ≤60% cleanliness bar (2022 = 67% of funding). NZDUSD −56, GBPUSD wash,
   AUDUSD −104 (momentum twin beats the MR grid). The MR block does not act as a block; the
   sign-flip prediction fails everywhere; MR-vs-RW does not separate.
3. **Structure failure, not substrate absence** — realized round-trip mean = +g in every cell
   (mechanism real), but fills materialise at only 5–28% of the A1-implied cadence; 3/4 MR
   cells cap-lock at 8 legs; NZDUSD trades nothing after 2022-04 (cap-lock + stale monthly
   anchor); the ≤8 fence-open legs erase 100–155% of realized harvest (VAL-006 survivorship).
   The "always-on oscillation harvester" is in fact a mostly-frozen, levered inventory carrier.
4. Integrity clean: 68/68 estimand blocking_pass; ARM R provenance + ARM G m1 fill-causality
   clean; +2 bps/rebalance plant detected before the real read; tripwire-1 (+1-bar delay)
   graceful everywhere (object ratios 1.01–1.06 — no fill-seam edge). Verdict robust under the
   hardened `block_bootstrap_ci` re-run (INFR-004/L-20; 2 verdict-immaterial temporal-half flips).

## Why RETIRE (kill-criterion adjudication)

Predeclared criterion (family card): retire if the harvest structures do not clear the cost
floor on the MR block. HYP-002 is the actual family bet, and it failed — not on cost, but on
**capture geometry**: the specific monthly-anchored capped structures cannot keep inventory
clearing within-episode on instruments that mean-revert locally but trend across a month, so
the harvest object degenerates into a cap-locked inventory carrier. Under UNPOWERED discipline
this does **not** license the universal claim "no oscillation harvest exists" — but the two
booked hypotheses are exhausted, the survivors (USDCAD, US2000-disclosure) are single-stratum,
attribution-flagged, and cost-unpinned, and the programme's standing prior (every prior harvest
/ MR construction hit the cost/capture wall) is reinforced, not challenged. No open lever
justifies holding a slot.

## What is closed / what remains open

- **Closed (permanent):** the EXP-018 NZDUSD rt anomaly (a draw, HYP-001); the fixed-hold
  unconditioned object (E[gross]=0 analytic + empirical); the **monthly-anchored capped grid
  and banded 50/50 rebalance as harvest structures on this universe** (HYP-002).
- **Not re-opened by this evidence:** whether a *different* structure that clears inventory
  within-episode (dynamic/rolling anchor, no hard cap, or episode-matched spacing) could
  harvest the real FX-block oscillation. This would be a **new candidate family with its own
  D0, on an unseen band** — not a re-parameterisation of CF-VOLHARV-001 (P-01/P-02). Recorded
  as a lead in the knowledge base, not carried as an open hypothesis here.
- HYP-003 (CF-VOLEXP tail long-vol) returns to DEFERRED / unregistered.

## Lessons (candidates → KB)

- **Cadence-vs-inventory tension is a first-class design risk for always-on grid/ladder
  harvesters.** A fixed anchor + hard inventory cap silently converts an "always-on harvester"
  into a mostly-frozen inventory carrier; measure realized fill cadence against the design's
  implied crossing rate, and report realized-vs-censored decomposition, *before* reading any
  harvest (EXP-020: 5–28% of implied; NZDUSD went inert). Extends [[event-mass-must-match-field-cadence]]
  and the VAL-006 censoring discipline to structure-borne P&L.
- **Level-based grid P&L is a drift carrier on trending instruments;** only the direction-
  inverted twin spread is drift-robust and admissible as the harvest read (BTCUSD level read
  +78k both directions; only the spread is meaningful).
- Design-time effect-size arithmetic must be sanity-checked against realized scale: the §8
  `w(1−w)σ²` premium was ~100× optimistic, which is why ARM R was predeclared plausibly powered
  yet came back uniformly UNPOWERED.
- Infra: unbounded per-symbol container parallelism (16-way) crashes the cTrader console at
  startup; `run-experiment.sh parallel` now bounded (`CTRADER_MAX_PARALLEL`=4 + 10s stagger).
  Killed containers leave truncated parquets → full-file integrity scan before gating.

## Cost-pin blocker — closed by operator directive (2026-07-05)

The live-session FTMO spread re-snapshot is **no longer carried**. Operator directive: the
weekend-ceiling snapshot (`code/derive_exp020_params.py`) is a sufficient cost estimate, with a
2–5× multiplier applied for evaluation stress when needed. The verdict already held at gross,
gross-minus-commission, and weekend-ceiling stress, so no re-analysis is implied; the
"net-at-live-spread BLOCKED" caveat is resolved for record-keeping — a deployable read (were one
ever pursued on a survivor) would use the ceiling × stress, not a fresh pin.

## Registry actions (sanctioned by this retrospective)

- `candidate-families/cf-volharv-001.md`: status → **RETIRED (2026-07-05)**; HYP-002 evidence
  row already appended.
- `multiplicity-registry.md`: CF-VOLHARV-001 family → RETIRED; HYP-002 row → COMPLETE / NOT
  SUPPORTED (retained, never deleted).
- Master index Family Indexes row + live status → RETIRED.

**Signed:** operator (verdict + RETIRE instruction, 2026-07-05); recorded by the pipeline.
