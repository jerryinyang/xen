# Audit Report: Experiment EXP-095 (Re-Audit — D0-amendment-001 rerun)

Portfolio Construction & Online-Adaptive Risk Model (RSI-2 Fade, 8 confirmed cells) · `CF-MR-001`/`HYP-003` · Phase 022

> **Audit lineage.** Cycle 1: FAIL on Critical C1 (concurrent-risk cap on un-anchored weights → `1/vol²`).
> Cycle 2 (post-C1-fix): PASS, but **under-weighted a verdict-material measurement defect** — 4h positions were
> booked **flat-at-exit** instead of the **intra-1h mark-to-market D0 §D2.1 requires**, inflating Sharpe/MaxDD
> *differentially* across 1h/4h. Operator ratified **D0-amendment-001** (A1 intra-1h MTM; A2 like-for-like
> benefit + cross-cell-median baseline; A3 co-binding Calmar/CVaR/Ulcer; A4 MDE-curve bite-check), predeclared
> **before** this re-read. This is the re-audit of the amendment rerun (`results/` `2026-06-24T22:53:13Z`).

## Summary

- **Verdict**: **PASS** — the amendment is correctly implemented; the favorable-direction result is a **faithful
  measurement correction, not goalpost-moving**; no verdict-material finding. Clear for Stage 6.
- **Critical Issues**: 0
- **Warnings**: 2 (W1 in-sample Sharpe magnitude; W2 circuit-breaker turns NEUTRAL — A ≈ B, both faithful, non-blocking)
- **Info Notes**: 3

**Headline.** Restoring the D0-mandated intra-1h MTM **raised** the portfolio Sharpe (A 9.87→**11.69** / lo
8.59→**10.24**; B 9.34→**11.57** / lo **10.19**) and **lowered** portfolio MaxDD (0.077→**0.034**). This is
**counter-intuitive but verified-faithful**: per-cell MTM columns carry genuine adverse excursions (ATR-unit
MaxDD 6–20, ~10% negative steps, e.g. XAUUSD min mark −16.97), so MTM is *injecting* intra-position risk, not
smoothing it away; the portfolio improvement is **real moment-to-moment diversification** across 8 low-correlation
cells (mean |cross-cell corr| 0.10) that the lumpy flat-at-exit booking was **hiding**. The benefit criterion
(A2) now clears **decisively and robustly** across every baseline; the new MDE bite-check (A4) **resolves**
(m\* 1.75/2.00, realized LB 10.24 ≫ m\*) — fixing the recurring fixed-Sharpe=1.0 unattainability. **Two findings
reverse and are reported honestly: ERC no longer loses to naive-IV (now comparable, A marginally ahead); the
circuit-breaker turns NEUTRAL (A ≈ B within noise — no material de-risking, a wash not a degradation).** The absolute Sharpe (~11–12) is an even higher
in-sample number and **remains a scrutiny flag, not a deployment estimate** (W1).

## C1 / amendment fix verification

| Check | Method | Result |
|---|---|---|
| A1 MTM conservation | Σ(per-cell marks) vs Σ(realized net), per cell + grid total | **EXACT** — diff ≤ 2.8e-14 per cell; grid `pnl_mat == trade_mat == +2199.79` (path redistributed, realized total preserved) |
| A1 marks causal | perturb minute prices strictly AFTER a 4h boundary → earlier marks | **all earlier marks unchanged**; conservation still holds ⇒ no future price enters an earlier mark |
| A1 excursions captured | per-cell MTM column drawdowns | real (ATR-unit MaxDD 6–20; ~10% negative steps; large negative marks) — not variance-smoothing |
| Provenance unchanged by MTM | `provenance_reconciliation.csv` hash | **`33a10cdf…` identical to the superseded run** ⇒ realized nets untouched; 8/8 reconcile abs-diff 0.0 |
| A4 m\* derivation | recompute smallest plant with fire-rate ≥ 0.80 from `fire_rate_by_plant` | A **1.75** / B **2.00** — match `bite_check.json` exactly |
| C1 vol-anchor (carried) | Sharpe across vol targets {7,10,15}% | spread **1.8e-15** (invariant); realized vol 0.112 (closer to 10% than the 0.131 pre-MTM — the MTM cov is more representative) |

**Predeclaration check (anti-goalpost-moving):** the A1–A4 rules are dated and frozen in
`D0-amendment-001.md` (RATIFIED 2026-06-24), authored **before** this rerun was read; the rerun only *applied*
them. The amendment restores the **already-frozen** D0 §D2.1 MTM (not a new favorable rule), and the benefit
criterion was made **stricter and more honest** (lower-bound-vs-lower-bound + a deployment-realistic median-cell
baseline; ex-post-best demoted to disclosure), not looser. The favorable direction is not engineered.

## Code Review (new amendment paths)

| File / function | Check | Verdict | Notes |
|---|---|---|---|
| `xen/portfolio.py::CellStream` | mark fields | PASS | `mark_epoch`/`mark_return` default `None` (back-compat); null path unaffected. |
| `xen/portfolio.py::grid_mark_matrix` | MTM booking | PASS | books per-1h increments via `np.add.at`; guards `mark_epoch is None`. |
| `run_experiment.py::mtm_marks` | telescoping + pin | PASS | intermediate price = `minute_open` of the last bar with `mce ≤ boundary` (causal real price); final mark pinned to realized `net` (`incr[-1] += net - incr.sum()`); **hard conservation assert ≤1e-9**; same-bar (`x≤e`) lumps net at entry step. |
| `xen/portfolio.py::build_portfolio/_rebalance_weight` | dual matrix | PASS | **covariance + returns from `pnl_mat`; trade-counts (`_trailing_trade_counts`) + breaker (`breaker_multipliers`) from `trade_mat`** — verified the breaker still consumes the per-resolved-trade stream, not the MTM marks. `trade_mat=None` defaults to the P&L matrix (null path = prior behavior). |
| `run_experiment.py::build_grid` | grid anchor | PASS | `grid_start = min ENTRY` (marks accrue from entry); `pnl_mat=grid_mark_matrix`, `trade_mat=grid_return_matrix`. (`grid_start` epoch −3600 vs pre-MTM, `n_steps` +1 — consistent.) |
| `xen/portfolio.py::moving_block_boot_components/sharpe_lower_bound_shift` | analytic MDE | PASS | a planted constant `c` shifts each resample mean by `c`, std unchanged ⇒ `LB(series+c)` analytic; verified **identical** to a direct re-bootstrapped `moving_block_sharpe_lower_bound(series+c)` (≤1e-9). |
| `run_experiment.py::calibrate_statistic` | A4 MDE + null | PASS | null = `block_permute_zero_mean` on the **per-trade grid** (a permuted synthetic block has no price path to MTM — correct, and matches the EXP-044 form; **not** built around a signal-derived target); m\* = smallest plant with fire ≥ floor; `statistic_ready = FPR≤0.05 ∧ m\* finite`; band-≥-m\* deferred to G-022a (not hard-coded). |
| `xen/portfolio.py::moving_block_calmar_lower_bound/cvar/ulcer_index` | A3 metrics | PASS | Calmar LB resamples weekly + computes per-resample Calmar; CVaR5 = mean worst-5% (positive magnitude); Ulcer = √mean(dd²); NaN (not inf) guards present. Per-cell baselines vol-scaled to the anchor (verified `ann_vol=0.10000`) so tail/drawdown are like-for-like. |
| `run_experiment.py` | holdout / determinism / dirs | PASS | analysis slice `[0,0.7)`, `holdout_untouched=true`; determinism byte-identical (A&B); `make_plots`/`write_outputs` create dirs in orchestration. |

## Numerical Validation

### Spot checks (independently re-derived)
- **Sharpe** from saved `portfolio_returns_{A,B}.csv` (weekly cadence 168, ppy 52.18): A **11.6911**, B **11.5717** — match metadata.
- **MDE m\***: from `fire_rate_by_plant`, first plant ≥ 0.80 → A **1.75** (0.779 at 1.50 → 0.967 at 1.75), B **2.00** (0.666 at 1.75 → 0.818 at 2.00). FPR A 0.000 (Wilson-hi 0.0038), B 0.002 (0.0073) ≤ 0.05.
- **Median-cell baseline**: median of the 8 per-cell Sharpe LBs {2.006,3.430,3.496,4.937,5.042,6.098,6.500,7.526} = (4.937+5.042)/2 = **4.9895** — matches `median_cell_sharpe_lo` 4.9893.
- **Benefit margins**: A 10.239−4.989 = **+5.25** (band 11.691−10.239 = 1.452) → ADDS_VALUE; A vs best-cell LB 10.239−7.526 = **+2.71**; vs best-cell point 10.239 > 8.725; vs naive-IV LB 10.239 > 10.066. **Robust across all four baselines.**

### Statistical sanity
| Statistic | Value | Sensible? | Notes |
|---|---|---|---|
| Realized vol A/B | 0.112 / 0.113 | YES | ≈1.1× the 10% target (improved from 1.3× pre-MTM — the MTM covariance better represents portfolio variance). |
| Portfolio MaxDD vs cells | 0.034 (A) < all 8 cells (0.031–0.100) | YES | genuine diversification (mean |corr| 0.10); only AUDJPY-4h (0.031) is comparable. |
| Per-cell Sharpe | 3.05–8.73 (median pt 6.3) | YES, in-sample | dropped slightly vs pre-MTM (MTM adds intra-position variance per cell); US2000-1h still best cell. |
| FPR A/B | 0.000 / 0.002 | YES | rule fires almost never under zero-edge. |

## Verdict Forensics (run autonomously)

### Mechanism of the Sharpe rise (the key skeptical question)
The rise is **temporal-spreading + genuine diversification**, not variance understatement or look-ahead:
- **Spreading.** Flat-at-exit lumped each trade's whole P&L into one exit-step spike → high weekly variance. MTM
  distributes the P&L over the hold (the marks telescope to the same realized total), so weekly returns are less
  lumpy. Within a week the weekly sum is conserved; only positions straddling a week boundary redistribute — a
  second-order, real effect.
- **Diversification.** With 8 cells at mean |corr| 0.10 marked continuously, the aggregate moment-to-moment path
  averages down → portfolio MaxDD (0.034) below every constituent. This is the **standard reason MTM matters for
  a portfolio** and is exactly the diversification the lumpy booking hid.
- **Not an artifact.** Per-cell MTM columns retain real adverse excursions (MaxDD 6–20 ATR units); marks are
  strictly causal (perturbation test); the conservation pin books the realized net at the **exit** step (known at
  exit — causal). The causal-weight assertion (weights) passes *and* the marks themselves are causal by direct test.

### Per-stratum re-derivation & masking check
All 8 per-cell baselines disclosed (`run_metadata.json::metrics.per_cell`), vol-scaled for like-for-like:

| Cell | Sharpe LB | Calmar LB | MaxDD | vs portfolio A (lo 10.24) |
|---|---|---|---|---|
| EURUSD-4h | 6.10 | 15.74 | 0.043 | below |
| XAUUSD-4h | 3.43 | 3.04 | 0.089 | below |
| USDCHF-4h | 5.04 | 7.28 | 0.053 | below |
| AUDJPY-4h | 4.94 | 9.22 | 0.031 | below |
| EURJPY-4h | 2.01 | 1.56 | 0.100 | below (weakest) |
| GBPJPY-4h | 3.50 | 5.60 | 0.043 | below |
| USTEC-1h | 6.50 | 16.57 | 0.040 | below |
| US2000-1h | **7.53** | 24.87 | 0.035 | below (best cell) |

- **Masking?** **No.** The portfolio LB (10.24) sits **above all 8 constituents** because diversification of 8
  imperfectly-correlated continuously-marked cells genuinely lifts the risk-adjusted return above any single one —
  re-confirmed by the low cross-cell correlation and the portfolio MaxDD < every cell. The benefit is robust to
  the baseline choice (median-cell, best-cell point, best-cell LB, naive-IV LB) — it does not hinge on the median
  baseline. The weakest cell (EURJPY-4h, LB 2.01) and the high-MaxDD cells (XAUUSD/EURJPY) are disclosed, not hidden.

### Two reversals vs the superseded (flat-at-exit) run — reported honestly
- **(a) ERC vs naive-IV:** now **comparable** — A 11.69 (lo 10.24) vs naive-IV 11.55 (lo 10.07); ERC marginally
  ahead on both point and LB. The prior "ERC does NOT beat naive-IV (refuted)" **no longer holds**; honest read is
  "ERC ≈ naive-IV, marginally ahead in-sample." (Neither is a strong ERC win.)
- **(b) Circuit-breaker:** **NEUTRAL — A ≈ B within noise.** MaxDD 0.0344 vs 0.0375 (0.31 pp on an ~11%-vol book),
  Sharpe LB 10.24 vs 10.19; the two drawdown statistics disagree (B marginally *better* on Ulcer 0.00369 vs
  0.00398, marginally worse on MaxDD). The prior headline "B reduces MaxDD 22.4%" was a flat-at-exit artifact;
  under MTM the breaker delivers **no material benefit** — a wash, **not** a degradation. The interpreter must drop
  the positive de-risking claim (and not overstate it as a negative): A ≈ B.

### Gate-shape check
- **Binding gate:** weekly-Sharpe MBB one-sided lower bound (+ co-binding Calmar LB). **Effect shape:**
  right-skewed location edge. The gate sees it (LB ≫ 0); Calmar LB co-reads the drawdown shape. Not blind.
- **A4 MDE gate (fixed):** the recurring fixed-Sharpe=1.0-vs-n unattainability (W1 prior; EXP-094-class) is
  resolved — the gate now reports its **detectable** effect m\* (1.75/2.00) and the realized edge (10.24) clears it
  comfortably. The band-≥-m\* rule is correctly **deferred to G-022a** (not retro-edited here).

## Scope Compliance
- Amendment A1–A4 implemented as predeclared; no scope drift; entry/exit/cost/cells/seeds frozen.
- Complexity budget: 1 binding test + calibration; 5 plots; 1 module (`xen.portfolio`) — within budget (A3 adds
  metrics to the existing endpoint, not new tests).
- Holdout exclusion: **YES** (`holdout_untouched=true`; 0 counted reads; 0 slots; provenance hash unchanged).
- Registry/ledger: portfolio-aggregate disclosure; no tally moves (11 carried strata stay 1/2).

## Issues

### Critical
*(none)*

### Warning

1. **Absolute Sharpe (~11–12) is an in-sample, favorable-selected magnitude — not deployment-realistic.**
   - Evidence: `metrics.A/B.ann_sharpe` 11.69/11.57; 8 G-021-confirmed cells; continuous MTM curve is smooth.
   - Materiality: the amendment did **not** (and was not meant to) fix the absolute-magnitude implausibility — it
     fixed *comparability* (1h vs 4h) and the *gate*. The **binding** read is the scale-invariant Sharpe/Calmar
     **lower-bound-vs-baseline margin**, which is a relative diversification statistic; the absolute level is a
     known in-sample property, not a code defect. **Record for the interpreter:** read 11–12 as "strong in-sample,
     non-deployment"; the binding deployment verdict is **EXP-097** on the sealed holdout (same MTM construction).
     Cannot move a verdict-bearing number ⇒ non-blocking.

2. **Circuit-breaker de-risking claim becomes NEUTRAL under MTM (faithful result change, not a defect).**
   - Evidence: A ≈ B within noise — Sharpe LB 10.24 vs 10.19; MaxDD 0.0344 vs 0.0375 (0.31 pp); the two drawdown
     statistics disagree (B marginally *better* on Ulcer 0.00369 vs 0.00398, marginally worse on MaxDD); Calmar
     gap (71.7 vs 66.3) merely amplifies the tiny MaxDD difference.
   - Materiality: these are the *correct* numbers on the corrected booking — no fix required; the **interpreter
     must update the A-vs-B headline** to "neutral / no material benefit" (NOT a degradation — B is not worse on
     any binding number outside noise). The breaker still de-allocates the fragile 1h cells (timeline intact).
     Non-blocking (no fix/rerun; it is the faithful measurement).

### Info

1. **Intermediate marks use `minute_open` (no minute *close* price in the context).** The most recent 1-minute
   bar's open at/before each 1h boundary is a real causal price; conservation pins the realized total exactly, so
   the choice only affects intra-position *distribution* of a boundary-straddling position's P&L (sub-minute,
   second-order). Cannot move the per-cell/portfolio weekly Sharpe materially. Non-material.
2. **`n_indeterminate` 2→3** (grid now anchored at min-entry → one extra early warmup rebalance with <8 active
   cells). Expected; carries 0 weight; non-material.
3. **`portfolio_metrics.csv` ragged** (A/B rows carry `turnover`/`n_indeterminate`; per-cell rows do not).
   Cosmetic; values correct and fully in `run_metadata.json`.

## Materiality & Re-Audit Requirements
- No Critical finding. The favorable-direction result is verified faithful (conservation exact, marks causal,
  excursions real, diversification genuine, predeclared rules) ⇒ **no fix/rerun required; clear for Stage 6.**
- W1/W2 are faithful, non-blocking; both routed to the **interpreter** (Stage 6): carry the in-sample-magnitude
  caveat, and **replace** the superseded run's "ERC < naive-IV refuted" and "circuit-breaker de-risks" headlines
  with the corrected reads (ERC ≈ naive-IV; breaker roughly neutral). The interpreter must also carry the A4 m\*
  forward to G-022a (band must be set ≥ m\*).
- Info 1–3 cannot move any verdict-bearing number.

**Routing:** none — proceed to Stage 6 (interpretation) on the corrected run.
