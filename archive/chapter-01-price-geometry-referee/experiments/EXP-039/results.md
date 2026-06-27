# Results: Experiment EXP-039 — TRAIN-Only Exit Screen (DIAG-006)

## Summary

EXP-039 screened 5 candidate exit families (E1–E5, 10 evaluated cells across 1h and 4h) against the AVWAP bounce-entry substrate under frozen CONSERVATIVE costs + Phase 008 financing. No candidate qualifies under the mechanical §8.1 rule. The screen outcome is **FLAT**. On the 4h domain the bar is R-FH(12) at +37.3 bps pooled net — the best candidate (E2, +31.9 bps) trails by −5.4 bps, and no candidate exceeds it. On the 1h domain all candidates produce negative pooled nets (−6.1 to −0.9 bps). Capture-efficiency beyond FH is exhausted on this substrate per Phase 010 design §9.

## Detailed Findings

### 4h Screen — High Bar, No Winner

- **Reference context**: R-FH(12) pooled net = +37.3 bps (n=86 intersection, bootstrap SE 17.9 bps). R-BTC pooled net = +7.2 bps. R-FH(12) is the binding bar for criterion (ii).
- **Best candidate**: E2 (HA trailing reference) at +31.9 bps pooled net, gap −5.4 bps vs R-FH(12). Passes per-instrument positivity (criterion i) and split-half stability (criterion iii) but fails criterion (ii) — the gap is negative.
- **Other candidates**: E3(3) delivers the highest raw pooled net (+39.9 bps) but the selected grid point E3(8) yields only +26.9 bps and fails per-instrument positivity (XAUUSD −1.7 bps). E5(8) passes criterion (i) at +11.3 bps pooled net but gaps R-FH(12) by −26.0 bps. E1, E4, and the remaining E5 points are all below R-FH(12).
- **Containment**: All 4h events resolve within the TRAIN boundary (0 unresolved per candidate, n=86 intersection for all).
- **Power**: 86 events per cell, bootstrap SEs range 7.2–30.0 bps. Two cells flagged fragile (|gap| < SE): 4h/E2 (gap SE 10.6 bps) and 4h/E3(8) (gap SE 18.2 bps). The E2 gap of −5.4 bps is approximately 0.5 SE.

### 1h Screen — All Negative

- **Reference context**: R-BTC pooled net = −2.5 bps (n=443 intersection). All candidates negative.
- **Best candidate**: E2 at −1.5 bps — marginally above R-BTC (gap +0.9 bps) but net negative, so fails criterion (i) (per-instrument positivity) and criterion (ii) (need pooled net > reference, which is itself negative — though the rule requires beating the better reference, and with R-BTC being the only reference on 1h, the gap is positive but the pooled net itself is below zero).
- **No candidate** passes per-instrument positivity. The closest is E3(8) at −0.9 bps pooled net, but BTCUSD descriptive is +22.3 bps while EURUSD is −4.7 bps and USTEC −6.0 bps.
- **Containment**: 639 events resolved per candidate; 1–2 unresolved for E3(5)/E3(8) (boundary edge cases). Intersection n=442–443.
- **Power**: Bootstrap SEs 1.5–5.5 bps. Two cells fragile: 1h/E2 (gap SE 1.75 bps, gap +0.9 bps) and 1h/E3(8) (gap SE 5.1 bps, gap +1.5 bps).

### Reference Context

- R-FH(12) on 4h TRAIN reproduces the EXP-033/EXP-037 freeze values (max diff 2.1e-14 bps, per-event R-BTC match exact with max diff 0.0 bps).
- R-FH(12) pooled net +37.3 bps remains the strongest known exit on this substrate.
- EURUSD carries a TEST-cap disclosure (design §7.3); EURUSD contribution shares across 4h candidates range −0.05 to 0.52 (negative for E1, where EURUSD net is −2.3 bps). Pooled nets ex-EURUSD are generally higher (e.g. E2 from +31.9 to +37.1 bps), confirming EURUSD dilutes the positive signal from USTEC and XAUUSD on 4h.

### Power and Fragility

- 4 of 10 evaluated cells are power-fragile (|gap| < bootstrap SE). This is consistent with the scope's predeclared warning: ~90 events per 4h cell with per-event dispersion 60–70 bps cannot stably select reference gaps below roughly one bootstrap SE.
- The split-half filter correctly identifies instability in 1h candidates (all 1h cells fail stability criterion iii — split_half_stable=0.0 for all 1h candidates, indicating sign changes between halves).
- On 4h, E4 fails split-half stability (h1 +20.3 bps, h2 −1.0 bps) despite having adequate event counts — the adverse-band stop is structurally unstable on this substrate.

## Screen Verdict

**FLAT** — no (exit, domain) cell satisfies the §8.1 mechanical qualification rule. The qualifying set is empty. The EXP-041 one-shot TEST slot is unused.

## Limitations

1. **TRAIN-only selection, winner's curse exposed**: All measurements are descriptive TRAIN statistics. Even if a candidate had qualified, TRAIN selection is fully exposed to winner's curse — the one-shot TEST (EXP-041) exists to discipline this. With FLAT, no TEST occurs.
2. **Power-limited 4h cells**: ~86 intersection events per 4h cell (3 instruments pooled) yields bootstrap SEs of 7–30 bps. Reference gaps below the SE are not stably selectable. The best candidate's gap (−5.4 bps) is roughly 0.5 SE.
3. **EURUSD TEST-cap**: 4h E2's pooled net is +31.9 bps including EURUSD (TEST-capped per design §7.3, 27/86 events); ex-EURUSD it rises to +37.1 bps. Qualification strength (had it occurred) would depend on TEST replication across uncapped instruments.
4. **1h structural weakness**: The 1h domain generates events that, on this substrate, are net-negative even under R-BTC. The 1h screen could not function as a qualification pathway regardless of exit design.
5. **BTCUSD descriptive only**: BTCUSD is excluded from binding statistics per the EXP-030/D0 break-even map. Its large negative nets on 4h (−45 to −93 bps for E3 candidates, −33.8 for R-FH) are disclosed descriptively and would dominate any equal-weight pooled.

## Implications

The FLAT outcome triggers the Phase 010 design §9 **EXIT_FLAT** consequence: capture-efficiency beyond R-FH(12) on the AVWAP bounce-entry substrate is exhausted in TRAIN across the structurally distinct exit families tested (HA-based, trailing reference, Last-X, adverse band, target-conditional time-stop). No candidate exit from this screen proceeds to the one-shot TEST (EXP-041 slot unused). The Track A exit exploration line is closed.

## Recommended Next Steps

1. **Stage-C family review per design §9**: The EXIT_FLAT conclusion should be reviewed in the context of the broader Stage-C (exit-exploration) program to confirm no unexamined exit families or registration opportunities remain.
2. **No further exit variation on this substrate**: EXP-039 tests the full predeclared candidate set. Additional exit rules on the unchanged AVWAP entry substrate would face the same R-FH(12) bar on 4h and structural negativity on 1h. New exit exploration should consider entry-substrate changes (Stage-D) or market-regime conditioning rather than further exit-only variation.
