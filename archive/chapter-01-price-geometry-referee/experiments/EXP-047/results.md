# Results: Experiment EXP-047

## Summary

The diagnostic executed cleanly (51/51 cells READY, reconciliation 125/125
exact, audit PASS) and returned **0/51 SHIFTED_VIABLE** — the mechanical G1b
input is **ANCHOR_MOVE_FLAT**. The decisive empirical fact, established by
the audit and binding on interpretation, is that the ratified `/ANCHOR`
definition (ATR(14)-prominence, k=1.0) **collapses to the baseline
running-extreme anchor by qualification**: anchors coincide in 94.6–98.5% of
regimes (fallback only 0–2%; 13/51 cells have literally identical event
populations, 29/51 have exactly zero median-MFE delta). The verdict
therefore closes the *ratified* `/ANCHOR` branch but is conditional on
k=1.0 — it is not evidence that anchor placement is irrelevant in general.
A second, unanticipated descriptive finding: P5 leg 2 (median MFE ≥ 2×floor)
passes in **51/51 cells on both anchors** — the available peak move was
never the scarce quantity; the shift leg (0/51) is the only failing leg.

## Detailed Findings

### Finding 1 — The ratified `/ANCHOR` rule barely moves any anchor

- **Observation**: anchor coincidence with baseline 97.8%/98.3%/98.5% mean
  (min 94.6%) on 1h/2h/4h; fallback rate 0.7–1.5%; event populations
  literally identical in 13/51 cells (`results/audit_anchor_coincidence.csv`,
  audit-verified).
- **Evidence**: by the time MA(20,50) confirms a regime change, price has
  moved far off the segment extreme, so the extreme almost always has a
  completed ≥1×ATR(14) counter-move; it qualifies, and being the most
  price-extreme candidate it is selected — the same point the baseline uses.
  The collapse is via *qualification*, which the predeclared `fallback_rate`
  disclosure cannot see (audit W1).
- **Interpretation**: k=1.0 makes "significant pivot" a near-vacuous filter
  at these timeframes. The diagnostic compared the substrate with itself in
  ~19 of 20 regimes; the NOT_SHIFTED outcome was close to structurally
  forced (audit W2).

### Finding 2 — No material MFE shift anywhere (leg 1: 0/51)

- **Observation**: Δ median MFE ranges −2.7 to +0.9 bps across the grid
  (29 exact zeros); best leg-1 margin −1.67 bps (EURUSD-1h, ΔMFE +0.30 vs
  SE_diff 1.97). No `leg1_borderline` flags — the zero count is not
  seed-brittle. Sensitivity thresholds (≥4 cells/≥2 instruments, ≥3/≥2)
  also unmet.
- **Interpretation**: among the ~2–5% of regimes where the anchor did move,
  the induced event-population changes are far inside noise. Mechanically
  ANCHOR_MOVE_FLAT under P5/P6.

### Finding 3 — The available peak move clears 2×floor everywhere (leg 2: 51/51)

- **Observation**: median lifetime MFE is 2.6×/3.1×/4.6× the *2×floor*
  threshold (i.e. ≈5–9× the floor itself) at the per-domain median; e.g.
  anchor-arm median MFE 24.0/35.9/64.5 bps on 1h/2h/4h vs binding floors
  ≈4.9/5.3/7.2 bps. Censored fractions ≤3.1%.
- **Interpretation (descriptive, necessary-not-sufficient)**: the phase's
  motivating framing — "the available captured move is too small" — needs
  sharpening. The available **peak** excursion over the event lifetime is
  ample relative to cost on the *existing* anchor; what Phases 010–011
  showed is that no deterministic exit converts more than a thin slice of
  it net of cost. The binding constraint is **capture geometry** (peak →
  realizable exit), not move availability. MFE is an unreachable upper
  bound for any exit, so this does not contradict the exit-side negatives;
  it locates the gap.

### Finding 4 — Matched-control context: event moves resemble in-regime moves

- **Observation**: control median MFE ≈ event median MFE (1h: 24.9 vs 24.0
  bps — controls slightly higher; 2h: 31.6 vs 35.9; 4h: 59.1 vs 64.5).
- **Interpretation**: the available lifetime move from a bounce trigger is
  similar to that from a generic same-regime bar — consistent with the
  established picture that the bounce entry's edge is relative/timing, not
  privileged access to larger moves. Descriptive only (same-sub-segment
  circularity disclosed in the plan).

## Hypothesis Verdict

**REFUTED** (mechanically: 0 SHIFTED_VIABLE cells vs the ≥5-cells/≥3-
instruments threshold → G1b input **ANCHOR_MOVE_FLAT**; adjudication is
checkpoint desk work).

The hypothesis that the ATR-prominence pivot anchor materially enlarges the
available move-size distribution is refuted **for the ratified definition**:
at k=1.0 the rule reproduces the baseline anchor in ~95–99% of regimes, and
the residual differences are within noise everywhere.

## Limitations

- The result is **conditional on k=1.0 and the ratified confirmation
  convention**. A k large enough to bind (or a different pivot/confirmation
  rule) was not tested and cannot be tested in this phase
  (no-re-parameterisation rule); it would be a new predeclared scope.
- Leg 1's SE-based guard is a noise guard, not a materiality margin; with
  near-identical populations it was the only discriminating leg.
- The matched-control read shares the events' regime sub-segments
  (disclosed circularity) and is descriptive only.
- MFE is a non-tradable upper bound; Finding 3 says nothing about net
  capturability by itself.

## Alternative Explanations

- None competitive for the headline: the zero-shift outcome is fully
  explained by anchor coincidence, which was verified mechanically (manual
  pivot recomputation, identical event frames), not inferred statistically.

## Recommended Next Steps

1. **Routing (per the operator pre-commitment, design §1.5/§9)**: with
   ANCHOR_MOVE_FLAT, the in-family lever closes and the programme routes to
   a **new candidate family** under its own design/D0. Finding 3 should
   inform that design: the failure mode to escape is capture geometry, not
   move availability.
2. **Optional new scope (only if the operator prefers one more in-family
   read before the pivot)**: a predeclared `/ANCHOR` variant whose
   prominence threshold demonstrably binds (e.g. k calibrated *on synthetic
   fixtures only* to produce a target anchor-displacement rate) — a new
   EXP/D0, explicitly motivated by the collapse finding, not a
   re-parameterisation of this one.
3. Record in the phase retrospective that collapse-toward-baseline
   disclosures must measure **anchor coincidence**, not just fallback rate
   (audit W1 lesson).
