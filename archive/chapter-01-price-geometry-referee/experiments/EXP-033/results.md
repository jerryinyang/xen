# Results: Experiment EXP-033

## Summary

**MEASUREMENT_COMPLETE**. Both diagnostic deliverables delivered.

The attribution crossover resolves EXP-031's horizon-dependent flip: on 5m, entry share crosses 0.5 at H=3 (STABLE_CROSSOVER); on 1h, at H=4. On 4h, attribution is UNPOWERED (~90 TRAIN events). The BTC exit is a short-horizon loss-cutter and a long-horizon trend-truncator — confirmed on both powered domains.

The FH(H) net curve shows 5m and 1h are not B2-eligible (grid maxima ≤ 0 under frozen costs + financing). Only 4h is eligible with H*=8 and pyramid policy = all_legs, but the split-half stability disclosure flags the H* selection as fragile (`h_star_stable = false` on ~47+39 events).

## Detailed Findings

### Finding 1: Attribution Crossover Resolved

- **Observation**: 5m crosses s_entry = 0.5 at H=3; 1h crosses at H=4. Entry share stabilizes above 0.5 for all larger H on both domains.
- **Evidence**: `results/crossover.csv`: 5m STABLE_CROSSOVER H=3, 1h STABLE_CROSSOVER H=4. `results/attribution_sweep.csv` (full grid per domain). Plot: `plots/s_entry_sweep.png`.
- **Interpretation**: The EXP-031 H=1 EXIT_DOMINANT / H=6 ENTRY_DOMINANT flip is not a contradiction — it's a horizon-regime structure. The BTC exit adds value only at short horizons (cuts early losers), then becomes a drag at longer horizons (truncates trends). The entry timing is the dominant carrier of the edge for holds ≥ 3–4 domain bars.

### Finding 2: FH(H) Net Negative on Powered Domains

- **Observation**: On 5m, the objective-set FH(H) net curve peaks at −3.72 bps (H=24); on 1h, at −0.99 bps (H=6). Neither grid maximum exceeds 0, triggering `B2_ELIGIBLE = false` per the mechanical one-SE rule.
- **Evidence**: `results/fh_net_curve.csv`; `results/b2_selection.json` (5m and 1h: `b2_eligible = false`, reason: "grid maximum ≤ 0"). Plot: `plots/fh_net_curves.png`.
- **Interpretation**: The fixed-horizon exit cannot rescue absolute net on either powered domain. The expense of replacing the BTC exit with FH is small (net changes by +0.6/+0.8 bps on 5m/1h per the design expectation), but the base absolute net is already negative — even the ideal exit does not reach breakeven. B2 (/EXIT-FH) should not proceed on 5m or 1h.

### Finding 3: 4h B2-Eligible but Selection-Fragile

- **Observation**: 4h is B2-eligible with H*=8 (smallest H within one SE of the grid max of +45.79 bps at H=24). Net at H* = +31.30 bps. Pyramid policy = all_legs (the best and selected policy).
- **Evidence**: `results/b2_selection.json`: 4h `b2_eligible = true`, `h_star = 8`, `pyramid_policy = all_legs`. Stability disclosure: `eligibility_stable = true`, `h_star_stable = false`, `policy_stable = true`.
- **Interpretation**: 4h has genuine positive net expectancy on TRAIN at all horizons (grid max > 0 under costs + financing). The one-SE rule selects H=8 as the shortest competitive hold. However, the split-half stability disclosure shows the argmax shifts between H=12 and H=24 across halves, making H*=8 unstable — the selection is fragile on 4h's ~90 contained TRAIN events. The EXP-037 scope and governance must weigh this fragility before spending a Tier-B slot.

### Finding 4: Pyramid Policy: All Legs Preferred

- **Observation**: At 4h H*=8, all_legs produces net 31.30 bps, first_leg_only 27.82 bps, pyramid_legs_only 28.63 bps. The all_legs policy is both the best and selected (within one SE of itself).
- **Evidence**: `results/b2_selection.json` policy section; plot `plots/pyramid_policy.png`.
- **Interpretation**: On 4h, pyramid legs carry no penalty at H*=8 — all three policies are within ~3.5 bps. The simplicity-preference order selects all_legs. Stability disclosure shows both halves agree (policy_stable = true).

## Hypothesis Verdict

**MEASUREMENT_COMPLETE** (diagnostic — no candidate hypothesis).

Both predeclared deliverables produced: attribution crossover characterized (stable crossover on 5m/1h) and FH(H) net curve plus mechanical B2 selections emitted (5m/1h: ineligible; 4h: eligible H*=8 all_legs with fragility flag).

## Limitations

- 4h attribution is UNPOWERED (~90 TRAIN events across 4 instruments). Crossover cannot be characterized on 4h.
- The FH net curve excludes BTCUSD from the objective set (D0 §4 data-dependent choice); full per-instrument curves are disclosed.
- The stability disclosure is descriptive (point estimates only, no test family) — it flags fragility but does not quantify its probability.
- All TRAIN reads; no TEST or holdout validation of the selected H*/policy.

## Alternative Explanations

- The crossover at H=3 (5m) / H=4 (1h) may shift on TEST or holdout. The OUT_OF_SAMPLE direction is more likely a rightward shift (longer horizon needed for entry dominance on unseen regimes), but this cannot be tested here — TRAIN-only by scope.

## Recommended Next Steps

- For EXP-037 (/EXIT-FH) scope time, weigh the 4h H* fragility flag. If the Tier-B slot is spent on 4h, consider a predeclared H* sensitivity window (e.g., H ∈ {4, 6, 8, 12}) rather than a single frozen H*.
