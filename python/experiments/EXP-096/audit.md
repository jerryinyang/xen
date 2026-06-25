# Audit Report: Experiment EXP-096

**Noise Infusion — Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 confirmed cells)** ·
`CF-MR-001`/`HYP-003` · Phase 022 (batch 3) · analysis-set only, **no holdout verdict** ·
audited 2026-06-25.

## Summary

- **Verdict: PASS** (numbers re-derived from raw artifacts + mechanism established; the binding v2 verdict is
  trustworthy and faithfully implemented).
- **Critical Issues:** 0
- **Warnings:** 0
- **Info Notes:** 5

The implementation is a faithful **pure entry-leg perturbation**: the exit resolution is reused verbatim and only
the entry execution price changes. Every integrity gate (provenance, MTM conservation, determinism, causality,
keep-mask invariance, holdout fence, read accounting) passes, and I re-derived the binding numbers analytically
from the per-cell artifacts. No finding moves any verdict-bearing number, so no rerun is required.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `intrabar_fill.py::resolve_entry_fills` | Correctness | PASS | v1=first 1m open after signal close (`searchsorted side="right"`); v2=v1+`dir·0.05·atr` (adverse); v3=worst touched (max-high long / min-low short) over bounded ≤k=3 window. Unit-tested (dev) + re-derived below. |
| `intrabar_fill.py::resolve_entry_fills` | Causality/fence | PASS | Only 1m bars in `(signal_close, train_edge]`; `available` mask + edge clip; pre-signal perturbation inert (`causal_entry_fill_pass=true`). |
| `run_experiment.py::resolve_cell_noise` | Pure entry-leg | PASS | Exit (`res.fill_price`/`kind`/`exit_domain_idx`/`keep`) resolved once, reused across variants; only `entry_fill` swapped via `net_return_atr`. Cost notional pinned to signal close. |
| `run_experiment.py` | Holdout exclusion | PASS | Reuses `E95.load_analysis_1m` → lazy `slice(0, int(total·0.7))`; `train_edge_epoch` = analysis edge; `holdout_untouched=true`. |
| `run_experiment.py` | Loader ordering | PASS | Lazy scan → `sort("CloseTime")` → first-70% slice → collect (inherited from EXP-095). |
| `run_experiment.py` | Timestamp alignment | PASS | All alignment by `CloseTime` epoch / `searchsorted`; never bar index. |
| `run_experiment.py` | Real-price discipline | PASS | Entry/exit fills are real touched 1m prices; ATR-unit returns off real OHLC; no HA/Renko. |
| `run_experiment.py` | NaN/zero-baseline | PASS | `net_return_atr` NaN on bad ATR; `_per_event_expectancy` guards n<2; Sharpe/Calmar guard zero denom → NaN. |
| `run_experiment.py` | Determinism | PASS | `determinism_pass=true` (A&B byte-identical); entry-fill walk is RNG-free pure numpy; bootstrap seeded off master `20260624`. |
| `run_experiment.py` | Separation/organization | PASS | Sectioned; output dirs in orchestration only; no import-time side effects. |
| `run_experiment.py` | Progress/logging | PASS | `tqdm` on cells/variants; concise logging; helpers return data. |
| `run_experiment.py` | Plot reuse | PASS | Plots consume collected series; no reloads. |
| `run_experiment.py` | Verdict representation | PASS | Portfolio is the legitimate estimand (a real combined stream, **not** a collapsed `.all()`); per-cell degradation + per-cell baselines emitted as disclosure (LESSON-001). |

---

## Numerical Validation

### Spot checks (re-derived from artifacts)

1. **v2 slippage applied exactly once (cost not double-counted) — verdict-material check, PASS.**
   For every cell, `v2_net_mean − v1_net_mean = −0.05000` exactly (e.g. EURUSD-4h 0.14847→0.09847; USTEC-1h
   0.10451→0.05451; US2000-1h 0.10982→0.05982). Since net = `dir·(exit−entry)/atr − cost` and v2 shifts entry by
   `+dir·0.05·atr`, the per-event return shifts by exactly `−0.05` ATR with the cost term **unchanged**. An exact
   −0.05 (not −0.05 ± a cost re-application) proves the slippage is a pure entry-price perturbation and the flat
   round-trip cost is **not double-counted**. ✓
2. **v1 ≈ ideal (latency-only is near-neutral), reconciled to the entry-fill audit.** `ideal_net − v1_net` equals
   the per-cell `v1_mean_adverse_gap_atr` to the digit (EURUSD-4h 0.14875−0.14847 = 0.00027 = audit gap; XAUUSD
   +0.00089 with sign). Next-1m-open is an essentially unbiased fill vs the signal close. ✓
3. **v2 entry gap = 0.05 ATR exactly** in `entry_fill_audit.csv` for all 8 cells (`v2_mean_adverse_gap_atr`
   0.0491–0.0503, = v1 gap + 0.05). Adverse sign verified (positive = worse). ✓
4. **Ideal variant reproduces EXP-095 to the point estimate.** Ideal portfolio A Sharpe **11.691** =
   EXP-095's reported 11.69 (the LB 10.28 vs EXP-095's 10.24 differs only by the `noise_ideal` bootstrap-seed
   namespace — see Info-1; binding read is v2). Confirms the EXP-095 construction is reused verbatim. ✓
5. **Provenance gate PASS** (`provenance_reconciliation.csv`): all 8 cells `abs_diff_mean=abs_diff_median=0.0`,
   `count_match=true`, `resolved_frac` identical vs EXP-093 `test_per_cell.csv`. The substrate regeneration is
   byte-faithful **before** noise is applied. ✓
6. **MTM conservation PASS** (`mtm_conservation.csv`): Σ(intra-1h marks) = realized net(v2) per cell, abs_diff
   ≤ 1.42e-14 (6 cells exactly 0.0). The amendment-001 A1 conservation invariant holds against the **v2**
   realized total. ✓
7. **Keep-mask invariance PASS:** `n_entry_unavailable_on_keep=0` for all 8 cells (`entry_fill_audit.csv`) and
   provenance `count_match=true` (n_resolved identical to EXP-093). The noise perturbs the entry price, never the
   event population. ✓

### Range / statistical sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| v2 A Sharpe LB | 5.147 | YES | Binding read; ≥ inherited m* 1.75 (edge +3.40). |
| v2 per-cell Sharpe LB | [0.130, 3.652], median 2.554 | YES | All 8 positive; median = the deployment baseline. |
| v2 A MaxDD / Ulcer | 0.062 / 0.012 | YES | ~2× the idealized 0.034 — slippage adds drawdown, plausible. |
| v3 A MaxDD / Ulcer | 0.409 / 0.188 | YES | Catastrophe under the stress ceiling; gate captures it (Sharpe LB −1.65, Calmar LB −0.27). |
| n_weeks | 185 | YES | Matches EXP-095 analysis-set length. |
| n_indeterminate (A,B) | 3 | YES | Same warmup structure as EXP-095. |

---

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

**Binding estimand = the v2 portfolio** (D0 design; per-cell disclosed alongside per LESSON-001). The portfolio
"ADDS_VALUE" headline is re-derived per cell from `portfolio_metrics.csv` (v2, vol-anchored single cells):

| Cell | v2 single-cell Sharpe LB | v2 net `ci_low_1s` (ATR) | vs EXP-093 margin | Disposition |
|---|---|---|---|---|
| EURUSD-4h | 3.652 | 0.0792 | > 0.025 | strong |
| XAUUSD-4h | 1.811 | 0.0610 | > 0.025 | strong |
| USDCHF-4h | 2.633 | 0.0611 | > 0.025 | strong |
| AUDJPY-4h | 2.476 | 0.0550 | > 0.025 | strong |
| EURJPY-4h | 0.130 | 0.0079 | **< 0.025** | **NOISE_DEGRADED (flagged)** |
| GBPJPY-4h | 1.173 | 0.0278 | > 0.025 (barely) | marginal |
| USTEC-1h | 2.874 | 0.0435 | > 0.0125 | strong |
| US2000-1h | 3.461 | 0.0488 | > 0.0125 | strong |

- **Pooled/portfolio headline:** A v2 Sharpe LB **5.147** vs cross-cell-**median** single-cell LB **2.554**
  (margin +2.59 > sampling band 1.35). **Masking heterogeneity? NO.** All 8 per-cell v2 Sharpe LBs are **positive**;
  the portfolio LB (5.147) exceeds **even the best single cell's LB (3.652)** by +1.49 and the median by +2.59.
  The benefit is **broad-based diversification**, not one cell carrying a basket of losers — there is **no
  negative/broken cell hidden** in the v2 aggregate. The cross-cell-median baseline (2.554) is the literal median
  and honestly represents the eight cells. The portfolio is therefore the legitimate binding estimand here.
- **One cell flagged (disclosure):** EURJPY-4h v2 `ci_low` 0.0079 < its 0.025 margin → `NOISE_DEGRADED`. It is
  still **net-positive** (not broken) and, per the operator's portfolio-only membership rule, is **retained**;
  G-022a adjudicates the holdout-frozen set. GBPJPY-4h is the next-weakest (0.0278, just clears). Correctly
  surfaced as disclosure, not buried.

### Mechanism

- **Why v2 SURVIVES (ADDS_VALUE).** The binding v2 fill subtracts a near-**uniform ~0.05 ATR/event** from every
  cell (the slippage; re-derived as an exact −0.05 per-event mean shift). This roughly **halves both** the
  portfolio Sharpe LB (idealized 10.28 → v2 5.15) **and** the cross-cell-median baseline (≈5.0 → 2.55), so the
  **relative** diversification margin is preserved. It is **not** variance hiding and **not** a denominator change
  (keep mask byte-identical; n unchanged) — it is the EXP-095 low-correlation diversification mechanism operating
  on uniformly cost-shifted streams. ERC ≈ naive-IV again (5.147 vs 5.089), so the lift is generic diversification,
  not an ERC-specific property.
- **Why v3 BREAKS for A but B survives (the shape finding).** v3 (worst-of-3-1m-bars) imposes a far larger entry
  penalty on the **fast 1h cells** (v3 adverse gap ≈ 0.15 ATR for USTEC/US2000 vs ≈ 0.05–0.075 ATR for the 4h
  cells) — because a 3-minute price swing is a larger fraction of a 1h cell's ATR(14) than of a 4h cell's. That
  drives USTEC-1h/US2000-1h (and EURJPY-4h) v3 net **negative**, so the static-ERC Portfolio A suffers a **40.9%
  MaxDD** (Sharpe LB −1.65). Portfolio B's circuit-breaker de-allocates exactly those cells once their trailing-50
  mean flips negative (USTEC de-allocated 26.1% / US2000 21.7% of steps), holding B at **6.0% MaxDD** (Sharpe LB
  +1.83). **This is the binding-stratum-relevant mechanism for the A-vs-B decision** (see gate-shape).

### Gate-shape check

- **Binding gate:** portfolio Sharpe LB **+ co-binding Calmar LB** (location + drawdown), with CVaR₅/Ulcer
  co-reported. **Is the gate blind to the effect's shape? NO.** Under v3 it captures the catastrophe on **both**
  legs (A Sharpe LB −1.65 **and** Calmar LB −0.27 both flip negative), so the drawdown-shape co-binding metric is
  doing real work — a Sharpe-only gate would still have caught it here, but the Calmar leg confirms it.
- **Real shape effect, not an artifact:** the breaker is **dormant at v2** (no cell's trailing-50 mean goes
  negative — all v2 per-cell means are positive ≈0.03–0.10 ATR → A ≈ B, "neutral") and **active at v3** (the 1h
  cells' trailing mean flips negative → de-allocation). So "breaker neutral at v2 / protective at v3" is a genuine
  **edge-decay-threshold** effect, correctly distinguished from "breaker adds nothing." **Interpreter note
  (Stage 6):** this nuances EXP-095's "circuit-breaker NEUTRAL" — B costs nothing at the binding v2 and provides
  large tail insurance at the v3 stress ceiling, which is material to the G-022a A-vs-B decision.

---

## Scope Compliance

- **Analysis plan followed: YES.** All 9 steps implemented; binding variant v2; m* inherited (not recomputed);
  portfolio-only membership (flags only); per-cell disclosure; v1/v2/v3 ladder + ideal overlay.
- **Deviations:** none material. (The `ideal` variant is the plan's required provenance reference + equity overlay,
  not scope creep.)
- **Complexity budget:** 2 binding tests (v2 survival + ladder) / ≤2; 5 plots / 5; 0 new modules + 1 small
  `intrabar_fill` entry-side function / ≤1. **Within budget.**
- **Holdout exclusion verified: YES** (`holdout_untouched=true`; analysis ends 2024-12, well before the holdout;
  only first-70% sliced).
- **Read accounting:** `counted_test_reads=0`, `candidate_slots=0`; entry-leg re-resolution = disclosure
  (EXP-085 precedent; ratified at Stage 4). 11 carried strata stay 1/2; 37 stay 0/2.

---

## Issues

### Critical
None.

### Warning
None.

### Info

1. **Ideal-variant Sharpe LB differs from EXP-095 by bootstrap-seed namespace.** Ideal A LB 10.281 here vs
   EXP-095's 10.24 (point estimate 11.691 matches exactly). The `seed_for(EXPERIMENT_ID, "noise_ideal", …)` key
   differs from EXP-095's `"real"` key, so the moving-block resample draw differs. Non-material: the ideal variant
   is an overlay/cross-check; the binding read is v2; the point estimate confirms verbatim construction reuse.
2. **v3 is a deliberately harsh stress ceiling, not a realistic fill.** v3 takes the absolute most-adverse touched
   price across 3 minutes — an upper bound on execution cost, correctly labelled disclosure-only. The interpreter
   should read "v3 A BREAKS" as a stress probe (and the source of the B-insurance finding), **not** as a
   deployment failure. The binding realistic-conservative fill is v2 (which survives).
3. **NOISE_DEGRADED flag compares a full-analysis-set `ci_low` to a TEST-stratum-calibrated margin.** The per-cell
   degradation `ci_low` is on the full analysis-set stream (n=1459 etc.) while the EXP-093 margin was an MDE on
   the TEST stratum. The flag is a mildly conservative disclosure heuristic (operator chose portfolio-only
   membership), not a binding gate; it cannot move the verdict. Plan-specified.
4. **Causal-entry-fill assertion is a single-event probe.** It perturbs all 719 pre-signal 1m bars and asserts
   event 0's fills unchanged. Non-vacuous (719 bars perturbed) but tests one event; causality is otherwise
   structural (`searchsorted side="right"` on the signal close + edge clip). Adequate.
5. **`determinism_replay` re-runs the portfolio build, not the upstream entry-fill walk.** The entry-fill
   resolution is RNG-free pure numpy (deterministic by construction), so re-checking the ERC/bootstrap build is
   the only place RNG enters. Adequate coverage.

---

## Materiality & Re-Audit Requirements

- **No Critical or Warning findings → no fix + rerun required.** All five Info findings are shown above to be
  unable to move any verdict-bearing number: (1) is a non-binding overlay seed; (2) v3 is disclosure-only with
  the binding read on v2; (3) the flag is non-binding disclosure under portfolio-only membership; (4)/(5) are
  causality/determinism coverage notes on mechanisms that are structurally or RNG-free deterministic.
- **Binding-number re-derivation:** the v2 ADDS_VALUE verdict was re-derived from raw artifacts — the per-event
  slippage shift (exact −0.05), the per-cell v2 Sharpe LBs (all positive, median 2.554), the portfolio LB
  exceeding every cell, the provenance abs-diff 0, and MTM conservation ≤1.4e-14. The verdict is trustworthy and
  faithfully implemented.
- **Verdict forensics complete:** per-stratum masking check (no heterogeneity masked), mechanism (uniform
  cost-shift preserves the relative diversification margin; v3 1h-cell sensitivity drives the A-break/B-survive
  split), and gate-shape check (the Sharpe+Calmar co-binding gate sees both the v2 survival and the v3
  catastrophe; the breaker's v2-neutral/v3-protective behavior is a real edge-decay-threshold effect, flagged for
  the interpreter and the G-022a A-vs-B decision).

**Audit verdict: PASS.** Cleared to Stage 6 (Interpretation).
