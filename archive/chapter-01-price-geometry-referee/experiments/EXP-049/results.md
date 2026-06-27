# Results: Experiment EXP-049

Phase 014-A · `CF-HA-HARAMI-001` / HYP-002 · 3-Barrier Capture Readiness & Gross Capture Rate

## Summary

The 3-barrier capture system is **construction-valid** across all 99 EXP-048-READY member cells (0 invariant failures, 0 non-deterministic cells, CAPTURE_READINESS_DELIVERED). However, the primary G1 (distance-based) favourable-before-adverse capture rate `r` stays below the P12 viability bar of 0.55 in **every** cell — 99/99 are `BELOW_R`. The composition readout yields **0 VIABLE cells** on either geometry, so the family-level P11 rule (≥5 cells over ≥3 instruments) is not met. The capture geometry under benchmark defaults is characterised as **not viable** on this substrate.

## Detailed Findings

### Finding 1: Barrier-construction readiness — PASS (99/99 cells)

- **Observation**: Every READY/READY_FLAGGED cell produces a causal, deterministic barrier system.
- **Evidence**: 0 causality violations (`inv_causality`=0 in all cells; all trailing-window moves confirmed strictly before each event). 0 determinism failures (frame-identical second-pass replay). 0 NaN barrier fields. 0 window-fence violations. 0 G1 `fav_dist ≤ 0` cells.
- **Interpretation**: HYP-002 leg (a) — "barriers computable and causally sound" — is fully supported. The `xen.capture_barriers` module and the per-cell orchestrator are correct.

### Finding 2: G1 capture rate — all 99 cells BELOW_R (r < 0.55)

- **Observation**: Per-cell G1 `r = P(fav before adv | resolved)` ranges from 0.4545 (NZDUSD-4h) to 0.5343 (AUDUSD-4h). All 99 cells have `r < 0.55`.
- **Evidence**: `capture_rate_map.csv` — status column is `BELOW_R` on every member cell. Typical 5m r ≈ 0.474–0.495; 1h r ≈ 0.458–0.510; 4h r ≈ 0.454–0.534. Resolved counts range from 128 (DE30-4h) to 22,172 (BTCUSD-5m). See `plots/g1_capture_rate_heatmap.png` and `plots/g1_viability_status_heatmap.png`.
- **Interpretation**: Under symmetric 1:1 barriers at 50% of the prior move, favourable-before-adverse is statistically indistinguishable from a 0.50 coin flip — no cell shows a material reversal-direction bias. The G1 composition readout is `composition_met = false` (0 VIABLE cells), which is consistent with design §10 `CHARACTERISED_NOT_VIABLE` on the capture leg.

### Finding 3: G2 capture rate — systematically lower, composition also not viable

- **Observation**: G2 (retracement-level) r ranges from 0.3257 (EURUSD-30m) to 0.4389 (EURUSD-4h). 52–60% of events are degenerate (entry already at/through the midpoint) and excluded from G2.
- **Evidence**: `capture_rate_secondary.csv`. G2 degeneracy fraction 0.52–0.60 across all cells. All G2 cells also `BELOW_R` (0 VIABLE). The composition is also not viable on G2.
- **Interpretation**: The retracement-level geometry is less favourable than distance-based because it conditions on the entry price being outside the midpoint — which fails for the majority of events. G2 provides no routing signal beyond G1 and the predeclared G1-primary designation is reinforced.

### Finding 4: Time-cap censoring is material but uniform

- **Observation**: `g1_timecap_frac` ranges from 0.218 (DE30-4h) to 0.335 (USDCHF-2h). Data-truncation censoring is < 0.5% everywhere.
- **Evidence**: `censoring_disclosure.csv`. `n_event_median` is 6 (the floor) in 96/99 cells; only GBPUSD-4h, USDCHF-4h, AUDUSD-4h reach 7.0. See `plots/g1_unresolved_fraction_heatmap.png`.
- **Interpretation**: The adaptive P4 time-cap defaults to its floor of 6 bars in most cells. The 24-33% unresolved fraction is driven primarily by the floor, not by per-cell adaptive variation. This is a known limitation of the benchmark `/THIRD-TIME` parameters; sensitivity is deferred to 014-B.

### Finding 5: Power is adequate — no cells NOT_VIABLE_BY_POWER

- **Observation**: `resolved ≥ 30` in all 99 member cells. Minimum resolved = 128 (DE30-4h). See `plots/g1_resolved_count_heatmap.png`.
- **Interpretation**: The 30-event P12 floor is comfortably cleared in every cell. The absence of VIABLE cells is not a power artefact — it is a genuine null reading on capture geometry.

## Hypothesis Verdict

**CAPTURE_READINESS_DELIVERED** — HYP-002 leg (a) supported (barrier construction causally correct and deterministic on 99/99 cells). HYP-002 leg (b) — the G1 capture-rate readout — shows **no cell meets P12 viability** under the benchmark defaults. The experiment does not self-adjudicate the §10 routing (PROCEED_TO_SCREEN vs CHARACTERISED_NOT_VIABLE); the readout is consistent with `CHARACTERISED_NOT_VIABLE` on the capture leg.

## Limitations

- The 50% favourable target (P2) and 1:1 adverse (P3) are single benchmark defaults. Other barrier ratios, third-barrier parameters, or favourable geometries may produce different capture rates. These are 014-B questions.
- The adaptive P4 time-cap binds at its floor (6 bars) in 96/99 cells, so variability in the cap is minimal. The `/THIRD-TIME` branch would assess k/window/floor sensitivity.
- The G1 distance-based and G2 retracement-level geometries are the only two tested. Volume-profile or statistical-magnitude targets (`/VPTARGET`, `/MAGTARGET`) are scoped for 014-B.
- All results are gross (no costs). Costs do not enter capture-geometry measurement, but any future net tradability screen would add them.

## Alternative Explanations

- The null r ≈ 0.50 is consistent with a random-walk substrate: with symmetric equidistant barriers on either side of entry, price has equal probability of hitting either target first. The failure to find r > 0.55 in any cell may be a genuine property of the ZigZag-confirmation entry point — it is not biased toward reversal continuation under these barrier parameters.
- G2's systematically lower r suggests that conditioning on the entry being *inside* the midpoint selects events where reversal momentum is already partially spent.

## Recommended Next Steps

1. **G1 desk adjudication** (design §10) — combine EXP-048 readiness (leg a), EXP-049 capture readout (leg b), and the future 014-B leg (c) to decide PROCEED_TO_SCREEN vs CHARACTERISED_NOT_VIABLE. The present readout is consistent with the latter.
2. **If proceeding to 014-B**: test alternative favourable-target definitions (`/VPTARGET`, `/MAGTARGET`), adverse-target variants (`/ADV-EXTREME`, `/ADV-NONE`), and third-barrier sensitivity (`/THIRD-TIME`, `/THIRD-EVENT`) on the same substrate.
3. **If CHARACTERISED_NOT_VIABLE**: the family is measured as capture-geometry-constrained on this substrate. A new candidate family or a substrate revision (different barrier-anchor or entry rule) would require a new phase scope.
