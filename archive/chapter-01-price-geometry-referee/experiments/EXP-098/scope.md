# EXP-098 — Cross-Broker & Aggregation-Method Robustness Replication of the RSI-2 Fade Deployment Portfolio (PPS data)

**Phase:** 022 (CF-MR-001 batch 3 — Portfolio Construction, Noise Infusion & Global-Holdout Release) ·
**Family / HYP:** `CF-MR-001` / `HYP-003` (deployment robustness companion) · **Date:** 2026-06-25
**Stage:** 1 (Scope) · **Type:** **non-binding robustness / replication disclosure.** Reruns the
G-022a-frozen deployment portfolio **verbatim** on an **independent broker's** 1-minute data (`data/timebars/pps/`),
under two bar-aggregation methods. **0 candidate slots · 0 counted analysis-TEST reads · the INFR-003 final-30%
global holdout is NOT touched** (it was spent once at EXP-097 and is sealed). EXP-098 **cannot upgrade, revoke, or
otherwise revise** the EXP-097 `DEPLOYABLE_CONFIRMED` verdict — it is a robustness cross-check, recorded as a
registry governance disclosure.
**Governing:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md)
· opened by [`D0-amendment-002`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-002.md)
· inherits the frozen spec from [`G-022a-gate-criteria.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022a-gate-criteria.md)
+ EXP-097 [`scope.md`](../EXP-097/scope.md).

> **Nothing about the strategy, portfolio, risk model, statistic, or band is a new design choice.** EXP-098 reuses
> the EXP-097/096/095/090 construction byte-for-byte. The **only** two things that change are: (a) the **data
> source** (a different broker's 1-minute bars for the same 8 instruments and the same 2021-06 → 2026-06 span);
> and (b) in one arm, the **bar-aggregation timestamping rule**. No parameter, threshold, cell set, exit, cost, or
> rule is re-derived, re-tuned, or re-selected.

---

## 1. Research question (single, binding-for-the-disclosure, falsifiable)

**Run verbatim on a completely independent broker's data (PPS), does the G-022a-frozen, noise-aware (binding v2
entry fill) causal ERC deployment portfolio retain its confirmed risk-adjusted edge — and is that edge robust to
the bar-aggregation timestamping method — i.e. does the primary Portfolio B clear the EXP-097 band (annualized
Sharpe LB > 2.00 with co-binding Calmar LB > 0) under BOTH (Arm 1) the canonical bucket-boundary aggregation and
(Arm 2) the alternate last-source-close aggregation?**

This is a **robustness companion** to the `HYP-003` deployment leg. It tests two overfitting hypotheses that the
single-broker EXP-097 read could not separate:

1. **Broker overfit** — is the confirmed edge specific to the cTrader/INFR-003 broker's quotes, spreads, and
   session structure, or does it replicate on an unrelated broker's feed for the same instruments and span?
2. **Aggregation overfit** — is the confirmed edge an artifact of our specific clock-aligned, bucket-boundary
   timestamping of N-minute bars, or does it survive a different (last-source-close) timestamping of the same
   buckets?

A purely independent dataset is, by construction, out-of-sample relative to every prior CF-MR-001 read. Because
the model is **fully frozen** (no selection or tuning happens here), reading the full PPS timeline carries no
overfitting risk for *this* experiment — so the binding metric is computed on the **full evaluable PPS series**
(operator decision 2026-06-25), not a held-back slice.

**Honest prior.** EXP-097 confirmed at B Sharpe LB 4.762 (band 2.00). A different broker introduces feed-level
differences (spread/quote/session) that the frozen ATR-normalized cost model does not re-fit, so some decay is
expected and legitimate; the band is the same absolute bar. A **ROBUST** outcome on both arms strengthens the
deployment claim; a **DEGRADED** outcome on either arm is recorded permanently as a disclosed robustness limit
and **does not** alter EXP-097's spent, non-upgradable verdict.

## 2. Signal-registry precondition (verified / established at scope time)

- **Family `DEPLOYABLE` (G-022 CONFIRMED); lever frozen.** `CF-MR-001` is `ADMITTED (BINDING)` (G-020) /
  `TRADABLE` (G-021) / `DEPLOYABLE_CONFIRMED` (G-022, EXP-097). `HYP-003` deployment leg closed. EXP-098 is a
  **post-deployment robustness companion** consuming **0 candidate slots** (no new signal candidate — same
  admitted lever, replicated on independent data).
- **Multiplicity registry.** EXP-098 and its **one new countable item — the alternate aggregation method
  (`AGG-LASTCLOSE`)** — are registered in `docs/signal-registry/multiplicity-registry.md` (Phase 022 batch) by
  `D0-amendment-002` in the same change as this scope, at frozen values, as a **non-binding robustness
  disclosure** (file-drawer control; never deleted or reused regardless of outcome). The PPS dataset is registered
  as a robustness data source. No slot consumed.
- **TEST-read ledger.** PPS is an **independent dataset**, outside the INFR-003 48-stratum analysis-TEST ledger
  and outside the INFR-003 global holdout entirely. Reading it is **not** a counted analysis-TEST read and **not**
  a global-holdout shot. The 11 carried INFR-003 strata stay **1/2**; the 37 others stay **0/2**; the INFR-003
  global holdout stays spent-once (EXP-097) and **is not loaded here**. The PPS read is recorded as a **robustness
  governance disclosure** in `test-read-ledger.md` + `multiplicity-registry.md` in the same change that records the
  result. (PPS is hereby "touched" as a robustness dataset; any *future binding* use of PPS would need its own
  governance — out of scope here.)

## 3. Deployable set (frozen at G-022a §3.1) — carry-8, verbatim

The **8 G-021-confirmed cells**: EURUSD-4h, XAUUSD-4h, USDCHF-4h, AUDJPY-4h, EURJPY-4h, GBPJPY-4h, USTEC-1h,
US2000-1h. The PPS directory contains exactly these 8 instruments. **EURJPY-4h remains flagged `NOISE_DEGRADED`**
(EXP-096) but net-positive → carried under portfolio-only membership. **No set change is permitted** (no re-pruning
on PPS evidence — that would be selection on the robustness data).

## 4. Data views, instruments, slice, exclusions, and the two arms

- **Dataset:** `data/timebars/pps/timebars_<symbol>_20210602_*_2026062*.parquet` — an **independent broker's**
  1-minute OHLC bars, 8-column standard time-bar schema, same 8 instruments, span 2021-06-02 → 2026-06-21 (file
  end), identical to the INFR-003 collection window. Real OHLC only; per-cell returns in ATR(14) units; portfolio
  curve vol-target-scaled. **The INFR-003 dataset is NOT read in this experiment** (no mixing of broker eras).
- **Instruments / cells:** the 8 cells in §3. No instrument or domain outside the set.
- **THE EVALUATION SLICE — the full PPS timeline (operator decision):** the per-cell exit/fill streams resolve
  over the **entire PPS file** per instrument; the binding portfolio metric is computed over the **full evaluable
  grid** — i.e. the full series after the unavoidable trailing-estimator burn-in (the LW trailing-90-day
  covariance lookback `LOOKBACK_STEPS`, ATR/RSI indicator warmup, the trailing-50-trade breaker state). The
  burn-in region carries degenerate/incomplete weights and is excluded from the binding metric only because the
  estimators are not yet defined there — **not** as a holdout. `n_weeks` of the evaluable region is reported.
- **Two arms (the only axis of variation besides the dataset):**
  - **Arm 1 — `PPS-CANON` (canonical aggregation):** domain bars built with the **deployed**
    `xen.domain_bars.build_domain_bars` (i.e. `aggregate_ohlc(min_coverage=0.90)` + analysis-boundary fence),
    which labels each N-minute bar at the **bucket right boundary** (the current production method). This is the
    pure cross-broker replication of EXP-097's exact construction.
  - **Arm 2 — `PPS-ALTAGG` (alternate aggregation):** identical bucketing, coverage (0.90), and OHLC reduction
    (first Open / max High / min Low / last Close / summed Volume), but each bar is **timestamped at the actual
    last source 1-minute bar's `CloseTime`** within the bucket rather than the bucket boundary. (Under this label
    the analysis-boundary fence is trivially satisfied — last source close ≤ source max — so the trailing-window
    drop behaves differently; this is part of what the arm tests.) Everything downstream of domain-bar
    construction (RSI-2 entry, EXIT-RCT, adverse 2.0×ATR + MR-tempo cap, v2 entry fill, cost, ERC, MTM, breaker,
    statistic) is byte-identical to Arm 1.
- **No look-ahead / causal everything:** every weight / covariance / vol / concurrent-risk cap / breaker state at
  grid timestamp *u* uses only per-cell returns resolved strictly before *u*; the v2 entry fill at signal *t* uses
  only 1-minute bars at/after *t*'s domain-bar `CloseTime`, clipped at the file end. Cross-domain alignment by
  **timestamp** (`CloseTime`), never bar index.
- **Exclusions:** the INFR-003 final-30% global holdout (sealed, not loaded — different dataset anyway); the
  v1/v3 fill variants and the covariance-window bracket (EXP-096 ladder — not recomputed); all deferred levers.

## 5. Frozen parameters (G-022a §3.2 — NOTHING tuned)

Inherited byte-for-byte from EXP-097/096/095: entry `RSI(2)` 2/10/90; exit **EXIT-RCT**; adverse `2.0×ATR(14)` +
EXP-089 MR-tempo cap; cost `D0-amendment-003` conservative round-trip (`F=0`); **binding v2 entry fill** (next-1m-
open + 0.05×ATR adverse slippage); ERC weights from a causal trailing-90-day Ledoit-Wolf covariance, **weekly**
rebalance, **10%** annualized-vol anchor, **1.5×** concurrent-risk cap; **intra-1h MTM**; master seed `20260624`;
`N_BOOT=10_000`, `α=0.10` (one-sided 95% lower bound). Both **Portfolio A** (static ERC) and **Portfolio B** (ERC +
circuit-breaker) built identically per arm. Confirmation bands **inherited verbatim**: band_A = 1.75, band_B =
2.00 (= the A4 MDE m\*). **No re-fit, no re-tune, no re-selection.**

## 6. What EXP-098 computes (the robustness disclosure)

```
For each arm in {PPS-CANON, PPS-ALTAGG}:
  Load each instrument's FULL PPS 1-minute file (independent broker).
  Build domain bars per the arm's aggregation rule (Arm 1 = bucket boundary; Arm 2 = last source close).
  Resolve per-cell EXIT-RCT net per-event streams under the binding v2 entry fill over the full PPS series
    (exit path/keep mask per the frozen substrate logic; entry_fill = v2; net = dir·(exit_fill − entry_fill)/atr − cost).
  Build the causal ERC portfolio (A static, B circuit-breaker) on the 1h grid with intra-1h MTM, weights past-only.
  On the FULL EVALUABLE portfolio return series (after estimator burn-in), for P in {A, B}:
    Sharpe_LB(P) = annualized-Sharpe moving-block one-sided lower bound (weekly block, N_BOOT=10_000, α=0.10)
    Calmar_LB(P) = Calmar moving-block one-sided lower bound (same block/N_BOOT)
    CONFIRM(P)   iff Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0   (band_A=1.75, band_B=2.00)

Robustness label (primary = Portfolio B, per arm; mechanical, frozen — NON-BINDING on EXP-097):
  ROBUST_arm        iff CONFIRM(B) on that arm
  DEGRADED_arm      iff Sharpe_pt(B) <= band_B OR Sharpe_LB(B) <= 0
  INCONCLUSIVE_arm  iff not CONFIRM(B) and not DEGRADED (power-limited / spans the band)

Overall disclosure:
  CROSS_BROKER_ROBUST          iff ROBUST on Arm 1 (PPS-CANON)
  AGGREGATION_ROBUST           iff (ROBUST on Arm 1) AND (ROBUST on Arm 2)   [edge survives both timestamping rules]
  else DEGRADED/INCONCLUSIVE   with the arm(s) and leg(s) that failed named explicitly.
```

## 7. Measurable criteria (reuse the EXP-097 band; NON-BINDING disclosure)

- **CROSS_BROKER_ROBUST:** Arm 1 (PPS-CANON) primary **Portfolio B** confirms — PPS Sharpe LB > 2.00 **AND**
  Calmar LB > 0. (A's confirm status co-reported, no OR.)
- **AGGREGATION_ROBUST:** **both** arms' Portfolio B confirm (the edge does not depend on the timestamping rule).
- **DEGRADED:** on an arm, B's Sharpe **point** ≤ 2.00 or B's Sharpe LB ≤ 0 — the edge does not replicate on that
  broker/aggregation. Recorded permanently; **does not touch EXP-097.**
- **INCONCLUSIVE:** on an arm, B is neither CONFIRM nor DEGRADED (point > 2.00 but LB ≤ 2.00, or the Calmar leg
  fails while Sharpe holds) — power-limited / spans the band.
- **Per-cell disclosure (LESSON-001):** every cell's PPS net outcome (mean/median/ci_low) reported per arm
  alongside the portfolio; a masking check confirms no single cell carries (or hides) the label. Non-binding.
- **Cross-dataset companion (descriptive, non-binding):** report the PPS-vs-INFR-003 retention — PPS Sharpe LB and
  per-cell net vs the **published** EXP-097 holdout values (no INFR-003 data re-read; the EXP-097 numbers are read
  from its committed results) — to quantify *how much* of the edge is broker/aggregation-portable.
- **Integrity (required regardless):** determinism byte-identical second pass per arm (entry-fill walk + ERC solve
  + MTM + bootstrap) for A and B; **MTM conservation** Σ(marks) = realized net per cell (≤1e-9 ATR); causal-weight
  + causal-fill assertions (no future per-cell return / 1m bar enters any weight / fill); real-price metrics only;
  `infr003_holdout_loaded=false` (asserted — the INFR-003 holdout is never read), `counted_test_reads=0`,
  `candidate_slots=0`, `exp097_verdict_unchanged=true`; the PPS robustness read recorded in `test-read-ledger.md`
  + `multiplicity-registry.md` in the same change.

## 8. Metric denominators / zero-baseline (frozen)

- **Per-cell return stream:** the binding-v2 EXIT-RCT net per-event return (ATR units), timestamped at the event
  exit `CloseTime`; denominator = resolved PPS events (the v2 keep mask).
- **Binding portfolio series:** net P&L aggregated by timestamp on the 1h grid (4h marked-to-market at each 1h
  close), scaled to the 10% vol target, restricted to the **full evaluable region** (post burn-in). Annualization
  factor fixed by the grid (recorded). Sharpe/Calmar denominators are the evaluable-series statistics.
- **No zero-baseline ratio.** The binding figure is the portfolio metric's **absolute lower bound vs the inherited
  band** (Sharpe LB vs band_B = 2.00; Calmar LB vs 0), per arm. A grid window with < 2 resolved trades on the
  trailing grid is `INDETERMINATE` for that mark (0 weight, recorded). Guard Sharpe/Calmar against zero vol / zero
  MaxDD → `NaN` with a flag, never `inf`.
- **Co-reported (non-binding):** MaxDD, CVaR5, Ulcer, ann return/vol, turnover, per-cell PPS net
  (mean/median/ci_low), A's CONFIRM status, the equity curves, the PPS→INFR-003 retention companion.

## 9. Complexity budget (design §5)

| Item | Budget | EXP-098 plan |
|---|---|---|
| Binding statistical tests | 1 robustness statistic (the primary-B portfolio Sharpe LB + co-binding Calmar LB vs the inherited band) **× 2 arms**; per-cell + retention descriptive. | Within budget — one frozen statistic, evaluated per arm; everything else descriptive. |
| Visualisations | ≤ 5 | (1) PPS equity curves A/B per arm (+ per-cell); (2) Sharpe/Calmar LB vs band, both arms (with EXP-097 holdout reference markers); (3) per-cell PPS net per arm vs the EXP-097 holdout values (retention); (4) A/B drawdown per arm; (5) Arm 1 vs Arm 2 metric comparison (aggregation sensitivity). |
| New code modules | 0 new `xen` modules. | Reuse `xen.portfolio`, `xen.intrabar_fill`, `xen.domain_bars`/`xen.bar_aggregator`, the EXP-090/095/096/097 substrate, `xen.ass` verbatim. New code is confined to `code/run_experiment.py` (orchestration): (a) a **PPS file-discovery override** (point loading at `data/timebars/pps/`, full-file load); (b) a small **alternate-aggregation helper** for Arm 2 (the last-source-close label variant of `build_domain_bars`); (c) the two-arm driver + the robustness-label adjudication. No `xen/` module is mutated. |

## 10. Discipline (binding)

- **Frozen-spec discipline.** The deployable set, construction, primary (B), bands (A 1.75 / B 2.00), and the
  confirmation rule are exactly as frozen at G-022a; **none is re-edited after the PPS outcome is seen.** No
  goalpost-moving; no re-pruning the cell set on PPS evidence.
- **Independent-data discipline.** Only PPS is read; the INFR-003 dataset and its sealed global holdout are not
  loaded. No mixing of broker eras within an analysis.
- **Causal everything.** Weights/covariance/vol/cap/breaker past-only at each grid timestamp; v2 entry fill uses
  only 1m bars at/after the signal close; cross-domain alignment by timestamp.
- **Real-price outcomes only.** Real domain & 1-minute OHLC; entry/exit fills are real touched prices; no HA/Renko.
- **Per-cell disclosure (LESSON-001).** Per-cell PPS outcomes reported per arm alongside the binding primary-B
  portfolio estimand; A co-reported.
- **Non-binding on EXP-097.** Whatever EXP-098 finds, the EXP-097 `DEPLOYABLE_CONFIRMED` verdict and the spent
  global-holdout shot are unchanged and non-upgradable. EXP-098 adds a robustness disclosure only.
- **Deviation handling.** A frozen-spec confound found mid-stream → dated amendment + hard-delete + full rerun
  (programme norm), not a silent follow-up.

## 11. Out of scope (explicit)

- Any re-derivation, re-tuning, or re-selection of the deployable set, construction, primary, band, or rule.
- Any change to the EXP-097 verdict, or any "upgrade" of the deployment claim from PPS evidence (PPS is a
  robustness cross-check, not a sanctioned holdout).
- Loading the INFR-003 dataset or its global holdout.
- The v1/v3 fill variants and the covariance-window bracket (EXP-096 ladder).
- The deferred levers (vol-regime, contrarian, 25/75, 15m, regime×variant cross-cuts, faster-cost,
  instrument/domain expansion) — each a separate dated `D0-amendment-*` + slot decision.
- Any *future binding* use of the PPS dataset (would need its own governance).
