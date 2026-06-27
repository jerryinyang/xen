# Results: Experiment EXP-092

**Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT; 1h + 4h survivors) → hash-pinned candidate set + Holm rule**
Phase 021 · `CF-MR-001` · `HYP-002` · TRAIN-only · 0 counted TEST reads · 0 slots · holdout sealed · audit PASS (0C/0W/4I).

## Summary

The per-instrument cost-bearing sequence over EXIT-RCT's inherited survivor cells delivered a **non-empty,
hash-pinned candidate set**: **all 11 carried cells reach `SEQUENCE_PASS`** (net per-event expectancy one-sided
lower bound `net ci_low_1s > 0` at α=0.05, power-confirmed), so the experiment verdict is **`SEQUENCE_DELIVERED`**
and Phase 021 advances to the one-shot EXP-093 TEST (not G-021 NOT_TRADABLE). The candidate set is pinned at
sha256 `f6427e83…` with the phase Holm rule sized to whatever subset EXP-093 carries. The binding pass is a
faithful re-derivation — every cell's `net_ci_low` reproduces its EXP-091/094 value within ≤6.2e-4 (independent
bootstrap seeds), on byte-identical resolved-event populations. The **important structure is not the 11/11 count
but the quality split the margin pre-read exposes**: a **robust core of 8 cells** (all six 4h members + USTEC-1h +
US2000-1h) that clear the EXP-093 margin **and** are mean-AND-median positive, versus a **mean-carried / fragile
1h tier of 3** (EURUSD-1h, NZDUSD-1h median-negative; GBPUSD-1h below its margin and median-negative).

## Detailed Findings

### Finding 1 — All 11 carried cells `SEQUENCE_PASS` (the candidate set is non-empty)

- **Observation**: every carried EXIT-RCT cell has `net_ci_low > 0`; with all 11 being powered members (finite
  MDE), all 11 satisfy the binding D6/4b rule.
- **Evidence** (`sequence_per_cell.csv`, `candidate_set.csv`): `net_ci_low` ranges +0.0044 (GBPUSD-1h) to
  +0.135 (EURUSD-4h). Ranked: EURUSD-4h 0.135, USDCHF-4h 0.122, AUDJPY-4h 0.119, XAUUSD-4h 0.115, USTEC-1h
  0.108, US2000-1h 0.104, GBPJPY-4h 0.086, EURJPY-4h 0.050, EURUSD-1h 0.047, NZDUSD-1h 0.039, GBPUSD-1h 0.0044.
  Plot: `plots/net_ci_low_vs_thresholds.png`, `plots/sequence_map.png`.
- **Interpretation**: expected and mechanical — the carried cells *were* the upstream net-clearers (EXP-091 1h
  quorum + EXP-094 4h members), so re-deriving the same bound reproduces `SEQUENCE_PASS`. This is the
  candidate-freeze step, **not** new evidence of an edge; it certifies the set and pins it for TEST.

### Finding 2 — 4h dominates the ranking; cost geometry, not signal strength

- **Observation**: the four highest `net_ci_low` cells and 6 of the top 8 are 4h; gross expectancy is
  near domain-invariant (~0.26–0.30 ATR) across both domains.
- **Evidence**: 4h `net_mean` 0.075–0.158 vs 1h `net_mean` 0.018–0.121; `gross_mean` ~0.27 ATR everywhere;
  `terminal_fav` ~0.99 (RCT hits its reversion-completion target ~99% of events). 4h `holding_days_mean` ~0.21
  vs 1h ~0.05.
- **Interpretation**: the same ATR-normalized cost mechanism EXP-091/094 established — fixed-bps round-trip ÷
  the (larger) 4h entry-ATR is a smaller ATR fraction, so 4h nets more and bounds tighter. The 1h cells survive
  on thinner net margins. Availability was never the constraint (gross is broad); **net tradability is decided
  by cost geometry**, exactly the phase's honest prior.

### Finding 3 — The robust core vs the mean-carried/fragile 1h tier (the EXP-093 selection signal)

- **Observation**: 11/11 pass the mean gate, but only **8** are both margin-clearing and mean-AND-median
  positive.
- **Evidence** (`margin_preread.csv`): **robust core (8)** = AUDJPY-4h, EURJPY-4h, EURUSD-4h, GBPJPY-4h,
  USDCHF-4h, XAUUSD-4h, USTEC-1h, US2000-1h (`clears_margin=true ∧ mean_and_median_pos=true`). **Fragile 1h
  tier (3)**: EURUSD-1h (`net_median −0.010`), NZDUSD-1h (`−0.005`) — clear margin but mean-carried; GBPUSD-1h
  (`net_ci_low 0.0044 < 0.0125 margin`, `net_median −0.052`) — the single weakest. Plot:
  `plots/mean_vs_median.png`, `plots/robustness_ranking.png`.
- **Interpretation**: the family's known median-fragile / mean-fragile signature (EXP-089/091) persists on the
  1h cells; the 4h members are uniformly robust (mean-AND-median positive), as EXP-094 found. For a one-shot
  TEST the defensible carry is the robust core; GBPUSD-1h would fail the EXP-093 margin condition and should not
  be carried.

### Finding 4 — Integrity: determinism, hash-pin, holdout, reads

- **Observation**: determinism PASS; candidate set hash-pinned and reproducible; no TEST/holdout contact.
- **Evidence** (`run_metadata.json`): replay of USTEC-1h + EURUSD-4h byte-identical; `candidate_set_sha256`
  reproduces from the canonical serialization (audit confirmed); `holdout_untouched=true`,
  `counted_test_reads=0`, `candidate_slots=0`; cost table Phase-021-local (`D0-amendment-003`), shared
  `COST_CONSTANTS` not mutated.
- **Interpretation**: the candidate set is a reproducible, frozen artifact suitable as the EXP-093 hand-off.

## Hypothesis Verdict

**`SEQUENCE_DELIVERED` (candidate set non-empty; necessary-but-not-sufficient for TEST).**

Per the pre-defined interpretation guide: **≥1 carried cell reaches `SEQUENCE_PASS`** → non-empty hash-pinned
candidate set + sized Holm rule emitted → Phase 021 proceeds to EXP-093. Realized: **11/11** `SEQUENCE_PASS`,
pinned at `f6427e83…`. No cell was `SEQUENCE_EMPTY`/`INDETERMINATE`; the boundary cell (GBPUSD-1h) stayed
`net_ci_low>0` under EXP-092's independent seeds (so it passes the sequence) but is flagged below its EXP-093
margin. This experiment **does not** decide G-021 — that is the EXP-093 TEST.

## Limitations

- **TRAIN-only, no TEST.** The candidate set is a TRAIN eligibility set; it makes no out-of-sample claim. The
  binding tradability read is EXP-093 (one counted read per carried stratum, cap 2/stratum, all 11 strata
  currently 0/2).
- **Mean-carried fragility on 1h.** Three of the five 1h cells are median-negative; the mean-gate admits them
  but the median shows the per-event outcome is right-skewed. Only the robust core is defensible for TEST.
- **GBPUSD-1h is below its margin** — pinned for completeness but should not be carried to TEST (would fail the
  4c margin condition).
- **No new evidence of edge.** By construction the carried cells already net-cleared upstream; EXP-092 certifies
  and freezes, it does not independently re-test availability.

## Alternative Explanations

- **Is the 11/11 pass just upstream selection echoed back?** Yes — and that is the intended function. EXP-092 is
  not an independent edge test; it re-derives the binding bound to freeze the set. The cross-check against the
  *independent* EXP-091/094 runs (≤6.2e-4 agreement, same signs, byte-identical counts) confirms the
  re-derivation is faithful, not a coincidental pass.
- **Could the 4h dominance be a power artifact (fewer events)?** No — 4h has fewer events (855–1088 vs ~3850 on
  1h) yet *tighter* lower bounds, because the net effect size per event is larger (smaller ATR-normalized cost),
  not because of noise. The mean-AND-median positivity on all six 4h cells rules out a thin-tail artifact.

## Recommended Next Steps

1. **EXP-093 (the planned one-shot TEST):** carry the **smallest-defensible robust core** from this pinned set —
   the mean-AND-median-positive, margin-clearing cells (USTEC-1h, US2000-1h, and the six 4h members) — selecting
   ≤1–2 cells per surviving exit/domain at EXP-093's D0, sized to the phase Holm rule. **Exclude GBPUSD-1h**
   (below margin) and treat EURUSD-1h/NZDUSD-1h (median-negative) as lower priority than the 4h core. Each
   carried `(instrument, domain)` stratum spends 1 counted TEST read (0→1; EURUSD-1h and EURUSD-4h are distinct
   strata). This is a new scope/D0, not an extension of EXP-092.
2. **(Disclosed, deferred — not now):** the faster-turnover cost sensitivity, the inert vol-regime partition,
   the contrarian arm, and 15m capture remain registered-but-deferred; each needs its own dated `D0-amendment-*`
   and slot decision.
