# EXP-097 — Global-Holdout Release: One-Shot OOS-Final Confirmation of the RSI-2 Fade Deployment Portfolio

**Phase:** 022 (CF-MR-001 batch 3 — Portfolio Construction, Noise Infusion & Global-Holdout Release) ·
**Family / HYP:** `CF-MR-001` / `HYP-003` · **Date:** 2026-06-25
**Stage:** 1 (Scope) · **Type:** **the single sanctioned global-holdout release** — the binding deployment OOS-final
read (à la EXP-032). Spends **1 global-holdout shot** (one holdout-governance event); **0 candidate slots, 0
counted analysis-TEST reads.** This is the programme's first new-dataset global-holdout shot.
**Governing:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md)
§6 · D0 [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
§D1/§D4/§D7/§D9 · **G-022a freeze** [`G-022a-gate-criteria.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022a-gate-criteria.md)
+ [`G-022a-gate-review.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022a-gate-review.md)
· terminal rubric [`G-022-gate-criteria.md`](../../../docs/experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022-gate-criteria.md).

> **Nothing in this scope is a new design choice.** EXP-097 reads **exactly** what G-022a froze — the deployable
> set, the construction, the confirmation statistic + band, the A-vs-B structure, and the read accounting. The only
> new thing EXP-097 does is **load the final-30% global holdout for the first time** and apply the frozen rule. No
> parameter, threshold, set, or rule may be re-derived, re-tuned, or re-selected here.

---

## 1. Research question (single, binding, falsifiable)

**Deployed as the G-022a-frozen, noise-aware (binding v2 entry fill) causal ERC portfolio with intra-1h
mark-to-market, does the confirmed RSI-2 fade confirm a positive risk-adjusted edge on the fully-fresh final-30%
global holdout — i.e. does the primary Portfolio B's holdout annualized-Sharpe lower bound exceed its predeclared
band (2.00) with the co-binding Calmar lower bound > 0?**

This is the binding deployment leg of `HYP-003`. It is the single sanctioned, irreversible, **non-repeatable /
non-upgradable** out-of-sample-final read (EXP-032 precedent). Per G-022a (operator decision 2026-06-25), **both
Portfolio A and Portfolio B are computed from one holdout materialization and counted as one read**; the **terminal
G-022 verdict keys off the primary, Portfolio B** (A is co-adjudicated and disclosed but cannot rescue the family
verdict via an OR). The honest prior, carried from the programme: the analysis-TEST already showed uniform
TRAIN→TEST shrinkage (G-021 Δ net_ci_low −0.005…−0.107) and EXP-096 showed the binding v2 fill roughly halves the
Sharpe lower bound; the holdout is a further-forward, fully-fresh slice that may decay further. A
DEPLOYABLE_CONFIRMED outcome makes the fade the programme's first deployment-grade price strategy; a DECAYED or
INCONCLUSIVE outcome is recorded permanently and the shot is spent.

## 2. Signal-registry precondition (verified at scope time)

- **Family `ADMITTED` / lever TRADABLE; G-022a FREEZE adjudicated.** `CF-MR-001` is `ADMITTED (BINDING)` (G-020) /
  **TRADABLE** (G-021); `HYP-003` active; **G-022a adjudicated FREEZE 2026-06-25** (all four D0 §D9 preconditions
  met). EXP-097 consumes **0 new candidate slots** (deployment wrapper on the admitted lever).
- **Multiplicity registry:** EXP-097 is the registered terminal experiment of the Phase 022 batch
  (`multiplicity-registry.md`, EXP-097 row — gated behind G-022a, now cleared). No new countable item.
- **TEST-read ledger — the global-holdout shot is spent here.** The final-30% global holdout is **outside** the
  analysis-TEST 48-stratum ledger (sealed since VAL-005, 0 rows read). EXP-097 is the **first and only** load of
  the new-dataset global holdout for this lever — recorded as a **holdout-governance event** in
  `test-read-ledger.md` **and** the multiplicity registry **in the same change** that records the result (à la
  EXP-032). The 11 carried analysis-TEST strata stay **1/2**; the other 37 stay 0/2 (the holdout read does not
  touch the analysis-TEST ledger). Per the operator decision 2026-06-25, **reading both A and B is ONE read.**
  **Non-repeatable, non-upgradable.**

## 3. Deployable set (frozen at G-022a §3.1) — carry-8

The **8 G-021-confirmed cells**: EURUSD-4h, XAUUSD-4h, USDCHF-4h, AUDJPY-4h, EURJPY-4h, GBPJPY-4h, USTEC-1h,
US2000-1h. **EURJPY-4h is flagged `NOISE_DEGRADED`** (EXP-096 v2 net ci_low 0.0079 < 0.025) **but net-positive →
carried** under portfolio-only membership. *(Ratifiable line — frozen default is carry-8; the operator may trim to
7 before the manual execution gate. No other set change is permitted.)*

## 4. Data views, instruments, slice, exclusions

- **Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars` (1h=60-min,
  4h=240-min). Real OHLC only; per-cell returns in ATR(14) units; portfolio curve vol-target-scaled.
- **Instruments / cells:** the 8 cells in §3. No instrument or domain outside the set.
- **THE BINDING SLICE — the final-30% global holdout, loaded for the first time:** per file,
  `holdout = [int(total_rows·0.7), total_rows)` (each file's own 2021-06 → collection-date timeline). This is the
  sanctioned shot. The binding confirmation statistic is computed on the **holdout-region** portfolio return series
  only (n ≈ the holdout weeks ≈ the m\*-calibration n).
- **Causal warmup (already-spent; not a new read):** the analysis set `[0, int(total_rows·0.7))` is loaded as
  **past-only warmup** for the trailing estimators (ATR/RSI indicator warmup; the trailing-90-day covariance/vol;
  the trailing-50-trade circuit-breaker mean) and the per-cell return history the weights need at the holdout's
  left edge. This is the EXP-093 pattern (TRAIN loaded as causal warmup; binding inference on the held-back
  stratum only). Loading the analysis set again is **not** a new holdout read.
- **No look-ahead:** every weight / covariance / vol / concurrent-risk cap / circuit-breaker state at a holdout
  timestamp *u* uses only per-cell returns resolved **strictly before** *u* (analysis tail + earlier holdout);
  the v2 entry fill at signal *t* uses only 1-minute bars at/after *t*'s domain-bar `CloseTime`, clipped at the
  file's end. Cross-domain alignment by **timestamp** (`CloseTime`), never bar index.
- **No further reserve:** the holdout is the end of each file; nothing beyond it is read.

## 5. Frozen parameters (G-022a §3.2 — NOTHING tuned)

Inherited byte-for-byte: entry `RSI(2)` 2/10/90; exit **EXIT-RCT**; adverse `2.0×ATR(14)` + EXP-089 MR-tempo cap;
cost `D0-amendment-003` conservative round-trip (`F=0`); **binding v2 entry fill** (next-1m-open + 0.05×ATR
adverse slippage); ERC weights from a causal trailing-90-day Ledoit-Wolf covariance, **weekly** rebalance, **10%**
annualized-vol anchor, **1.5×** concurrent-risk cap; **intra-1h MTM** (amendment-001 A1); master seed `20260624`.
Both **Portfolio A** (static ERC) and **Portfolio B** (ERC + circuit-breaker) built identically. The v1/v3 fill
variants and the covariance-window bracket are **not** computed here (they were the EXP-096 sensitivity ladder; the
holdout uses only the binding v2). **No re-fit, no re-tune, no re-selection.**

## 6. What EXP-097 computes (binding holdout verdict)

```
Load the final-30% global holdout per file (the sanctioned shot) + the analysis set as causal warmup.
Resolve per-cell EXIT-RCT net per-event streams under the binding v2 entry fill over warmup + holdout
  (exit path/keep mask per the frozen substrate; entry_fill = v2; net = dir·(exit_fill − entry_fill)/atr − cost).
Build the causal ERC portfolio (A static, B circuit-breaker) on the 1h grid with intra-1h MTM, weights past-only.

Binding read (primary = Portfolio B; A co-adjudicated on the SAME materialization, disclosed):
  on the HOLDOUT-REGION portfolio return series, for P in {A, B}:
    Sharpe_LB(P) = annualized-Sharpe moving-block one-sided lower bound (block=weekly cadence, N_BOOT=10_000,
                   alpha=0.10, seed 20260624)
    Calmar_LB(P) = Calmar moving-block one-sided lower bound (same block/N_BOOT)
    CONFIRM(P)   iff Sharpe_LB(P) > band_P AND Calmar_LB(P) > 0    (band_A=1.75, band_B=2.00)

Terminal G-022 adjudication (keys off primary B; mechanical, frozen):
  DEPLOYABLE_CONFIRMED  iff CONFIRM(B)
  DECAYED/NOT_CONFIRMED iff Sharpe_pt(B) <= band_B OR Sharpe_LB(B) <= 0
  INCONCLUSIVE          iff not CONFIRM(B) and not DECAYED (power-limited / spans the band, EXP-032 precedent)

Co-reported (non-binding): A's CONFIRM status; per-cell holdout net outcomes (mean/median/ci_low) for all 8 cells;
  MaxDD/CVaR5/Ulcer/ann ret-vol/turnover (A and B); the holdout equity curves; the analysis→holdout shrinkage.
```

## 7. Measurable criteria (frozen at G-022a §3.4 / G-022 rubric — NOT re-defined here)

- **DEPLOYABLE_CONFIRMED:** the primary **Portfolio B** confirms — holdout Sharpe LB > 2.00 **AND** holdout Calmar
  LB > 0. (A's confirm status co-reported; an A-confirm with a B-fail does **not** make the family confirmed.)
- **DECAYED / NOT_CONFIRMED:** B's holdout Sharpe **point** ≤ 2.00 (the central estimate itself fails the bar) **or**
  B's Sharpe LB ≤ 0.
- **INCONCLUSIVE:** B is neither CONFIRM nor DECAYED — Sharpe point > 2.00 but Sharpe LB ≤ 2.00, or the Calmar leg
  fails while Sharpe holds (power-limited / spans the band; the shot is still spent, EXP-032 precedent).
- **Per-cell disclosure (LESSON-001):** every cell's holdout net outcome is reported alongside the binding
  portfolio; a masking check confirms no single cell carries the verdict and no broken cell is hidden in the
  aggregate. Non-binding.
- **Integrity (required regardless):** determinism byte-identical second pass (entry-fill walk + ERC solve + MTM +
  bootstrap) for A and B; **MTM conservation** Σ(holdout marks) = realized holdout net per cell (≤1e-9 ATR);
  causal-weight assertion (no future per-cell return enters any weight) + causal-fill assertion (no future 1m bar
  enters any entry fill); real-price metrics only; `holdout_untouched=false` (asserted true only for this
  experiment — the shot is spent), `counted_test_reads=0` (analysis-TEST ledger untouched), `candidate_slots=0`;
  the holdout-governance event recorded in `test-read-ledger.md` + `multiplicity-registry.md` in the same change.

## 8. Metric denominators / zero-baseline (frozen)

- **Per-cell return stream:** the binding-v2 EXIT-RCT net per-event return (ATR units), timestamped at the event
  exit `CloseTime`; denominator = resolved holdout events (the v2 keep mask; the noise perturbs the entry price,
  not the event population).
- **Binding portfolio series:** net P&L aggregated by timestamp on the 1h grid (4h marked-to-market at each 1h
  close), scaled to the 10% vol target, restricted to the **holdout region** for the binding metric. Annualization
  factor fixed by the grid (recorded). The Sharpe/Calmar denominators are the holdout-region series statistics.
- **No zero-baseline ratio.** The binding figure is the portfolio metric's **absolute lower bound vs the
  predeclared band** (Sharpe LB vs band_B = 2.00; Calmar LB vs 0). A holdout window with < 2 resolved trades on
  the trailing grid is `INDETERMINATE` for that mark (0 weight, recorded). Guard Sharpe/Calmar against zero vol /
  zero MaxDD → `NaN` with a flag, never `inf`.
- **Co-reported (non-binding):** MaxDD, CVaR5, Ulcer, ann return/vol, turnover, per-cell holdout net
  (mean/median/ci_low), A's CONFIRM status, the holdout equity curves, the analysis→holdout shrinkage.

## 9. Complexity budget (design §5)

| Item | Budget | EXP-097 plan |
|---|---|---|
| Binding statistical tests | 1 (the binding holdout confirmation) + descriptive companions | 1 — the primary-B holdout Sharpe LB + co-binding Calmar LB vs the frozen band; A co-adjudicated (disclosed); per-cell + shrinkage descriptive. |
| Visualisations | ≤ 5 | (1) holdout equity curves A/B (+ per-cell); (2) holdout Sharpe/Calmar LB vs band (A & B, with m\*/band lines); (3) per-cell holdout net (mean/median/ci_low) vs the EXP-096 v2 analysis values (shrinkage); (4) A/B holdout drawdown (underwater); (5) circuit-breaker de-allocation timeline on the holdout. |
| New code modules | 0 | Reuse `xen.portfolio`, `xen.intrabar_fill` (incl. `resolve_entry_fills`), the EXP-090/096 substrate, `xen.ass` verbatim. The only new code is the **holdout-slice loader + holdout-region metric extraction** in `code/run_experiment.py` (orchestration), mirroring the EXP-096 build with the slice extended through the holdout and the binding metric restricted to the holdout region. |

## 10. Discipline (binding)

- **One shot, ever.** The final-30% global holdout is loaded once, here; recorded as the single sanctioned
  holdout-governance event; non-repeatable, non-upgradable (EXP-032 precedent). No holdout bar was loaded at any
  prior stage.
- **Frozen-rule discipline.** The deployable set, construction, primary (B), bands (A 1.75 / B 2.00), and the
  confirmation rule are exactly as frozen at G-022a; **none is re-edited after the holdout outcome is seen**,
  whatever it is. No goalpost-moving.
- **Causal everything.** Weights/covariance/vol/cap/breaker past-only at each holdout timestamp; v2 entry fill
  uses only 1m bars at/after the signal close; cross-domain alignment by timestamp.
- **Real-price outcomes only.** Real domain & 1-minute OHLC; entry/exit fills are real touched prices; no
  HA/Renko.
- **Per-cell disclosure (LESSON-001).** Per-cell holdout outcomes reported alongside the binding primary-B
  portfolio estimand; A co-reported.
- **Deviation handling.** A frozen-design confound found mid-stream → dated `D0-amendment-*` + hard-delete + full
  rerun (programme norm), **before** spending/again-reading the shot — but the shot is one-time, so any rerun must
  preserve holdout-read-once discipline (a confound discovered after the read is recorded as a permanent caveat,
  not a re-read).

## 11. Out of scope (explicit)

- Any re-derivation, re-tuning, or re-selection of the deployable set, construction, primary, band, or rule (all
  frozen at G-022a).
- The v1/v3 fill variants and the covariance-window bracket (EXP-096 disclosure ladder — not computed on the
  holdout).
- The deferred levers (vol-regime, contrarian, 25/75, 15m, regime×variant cross-cuts, parameter tuning,
  instrument/domain expansion, faster-cost) — each a separate dated `D0-amendment-*` + slot decision, post-G-022.
- Any second holdout read or any upgrade of this read's verdict (one-shot, non-upgradable).
