# Audit Report: Experiment EXP-009 — CF-MR-003/HYP-001 native re-screen (does price return to the anchor?)

## Summary

- **Verdict**: **PASS** — the recorded **ADMIT-TO-EXPLORE** (per-stratum) is supported, leak-clean, and
  robustness-checked, with one disclosed power caveat (recent-third).
- **Critical Issues**: **0**
- **Warnings**: 1 (recent-third temporal stability unconfirmed — power)
- **Info**: 4

EXP-009 is the native re-screen built after EXP-008's evaluation-vehicle mismatch (L-13). Target-based
estimands (anchor-hit / fraction-recovered / time-to-anchor), event-specific half-life horizon, screen-fail
dislocation-matched null. It records **36 leak-clean per-stratum reversion-to-anchor passes** (S5_SPREAD 20,
S3_DETREND 14, S4_OU 2) plus pervasive positive **hints** on S1/S2 (precision-limited). Analysis-only,
TRAIN-only, 0 counted reads, holdout sealed.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `reversion_targets.py` | Correctness | PASS | `measure_entry` (hit/frac/time) unit-tested on synthetic short/long/no-reach/reverse; `anchor_price_level` recovers price-space (`close−dev`) and log-space (`close·e^{−dev}`) anchors; `event_horizon`/`dislocation_bin` verified. |
| `reversion_targets.py` | Provenance | PASS | Docstring contract: `a_level_lag`/`dev_lag` are `[i-1]`; forward window `[i,i+H-1]` is the only future read (outcome). No forming-bar OHLC in a decision. |
| `run_experiment.py` | Correctness | PASS | Screen-fail control, `|z|`-bin×regime matching, horizon-matched pairing, per-endpoint floors, disposition logic re-derived below. |
| `run_experiment.py` | Holdout | PASS | Reuses EXP-008 `load_train_1m` (first 49% per file); TEST + holdout never loaded. |
| `availability_gate.py` | Additive | PASS | `STAT_MEAN` added (hit-rate); `git diff` additive only, frozen constants + existing stats byte-unchanged. |

---

## Verdict Forensics

### Per-stratum re-derivation & masking check

Binding = per stratum (instrument, series, pair), L-03. **No pooled headline is used as the verdict.** The
result is a **per-stratum tally**: 36 instrument-cells pass (any_pass on E1 hit @0.03 or E2 frac @0.05,
label-permutation collapses). Distribution: **S5_SPREAD 20** (FX-major-concentrated: EURUSD, USDJPY,
NZDUSD, USDCHF, GBPUSD across pairs), **S3_DETREND 14**, **S4_OU 2**. The axis-majority rule (design §7)
was **relaxed to per-stratum reporting** on operator direction (a family need not work everywhere; L-03) —
recorded as a governance change, not a silent one.

Disposition tally (precision-aware, Amendment B2): **POWERED_PASS 49 · POWERED_FAIL 26 · UNPOWERED_HINT
253 · UNPOWERED_NULL 104**. The 253:104 hint:null split (~71% of underpowered cells lean past the floor)
is itself weak corroboration of a broad positive signal, **not** a verdict (unresolved).

### Mechanism

The screen (VR∧HL at `|z|≥2`) selects exec bars whose deviation is mean-reverting; those bars reach the
higher-domain anchor (the "mean") **more often and faster** than dislocation+regime-matched screen-FAIL
bars. Concretely: on S5_SPREAD the cross-instrument spread reverts to its rolling-β basket anchor; on
S3_DETREND the log-price reverts to its rolling-OLS trendline. Effect sizes: hit-Δ medians +2.2pp
(S5) … +8.8pp (S4); fraction-recovered +3.3% … +19%.

### Gate/precision-shape check

The **sole binding gate is statistical precision (Gate 5, MDE ≤ floor)** — verified by a full 6-gate
cascade count: Gates 1–4 (cond<100 / fail<2 / D>0-dropout / matched-pairing) fire ~0 across all series;
Gate 5 fires 48/48 (S1), 48/48 (S2), 43 (S3), 27 (S4), 18 (S5). The operator's "screen-fail null
starvation" hypothesis was **empirically tested and refuted** (median fail-pool 2439/2152/1687 for
S1/S2/S4; D>0 drop 0%; all buckets populate). S1/S2 UNPOWERED = binary-hit precision at their event counts
(fewer `|z|≥2` extremes from trend-inflated median-MAD z on price-space deviations), **not** a null
artifact and **not** no-signal (their hit-Δ medians are +5.2pp / +8.2pp, 73–81% UNPOWERED_HINT).

---

## Causal Provenance & Leak

### Provenance trace

| Quantity | Inputs & timestamps | ≤ t-1? | Where |
|---|---|---|---|
| Selector (VR∧HL, `\|z\|`) | trailing `W_s`/`W_z` deviation ending `i-1` | YES | `cross_domain_mr`, `extreme_screen` |
| Anchor target `a_target` | `a_level[i-1]` (entry-fixed) | YES | `reversion_targets.anchor_price_level` + lag |
| Horizon `H_i` | `hl[i]` fitted on `dev[..i-1]` | YES | `event_horizon` |
| Outcome (hit/frac/time) | real `low/high[i..i+H_i-1]` | outcome (forward) | `measure_entry` |
| Control | screen-FAIL bars, same `\|z\|`-bin×regime, paired `H_i` | YES (label `≤ i-1`) | `build_cell` |

No `rct[di]`-style own-close-as-limit. Decision at bar open on `≤ t-1`; forward window is outcome only. The
anchor-hit is an intrabar touch of a fixed level = a faithful proxy for the family's **form-2 limit-at-mean**
outcome (dump `0-phase002-thoughts.md`); it is a **non-tradable availability diagnostic**, not open-to-open
P&L. Entry-side live-limit fill is **not** modeled (simplification, deferred to the price-primary
concretization) — disclosed.

### Leak tripwire

- **Binding: pass/fail label-permutation — collapses.** All 36 passing cells have `|Δ_labelperm| < 0.03`
  (mean ≈ −0.002). The edge is the VR∧HL split, not a random split of the same extreme bars.
- **Time-reversal: reported, non-binding (Amendment B1).** It does **not** collapse (+~6pp), which is the
  *expected* signature of genuine stationary mean-reversion (target-touch is time-symmetric on an
  oscillatory deviation), **not** a leak. Causality is guaranteed by construction (`≤ t-1` decisions), so
  the label-permutation is the operative selection-artifact control. Justified on a mechanism argument,
  pre-binding-run.

### Shared-module & price-primary

`reversion_targets` matches its provenance contract. ANALYSIS-ONLY (no positions/orders/P&L). Not a
vectorized price-strategy backtest. Concretization (limit-at-anchor) is deferred to an in-engine
price-primary experiment (L-01 discipline preserved).

---

## Robustness (design §8 + operator-requested)

Per-stratum passes stable across horizon `m∈{2,3,4}`, `H_CAP∈{48,96}`, `|z|`-bin edges, and
event-vs-cell-median horizon: **S5_SPREAD 18–20** (essentially flat — robust); **S3_DETREND 8–16** (stays
positive; more horizon-sensitive). Floor sweep monotone (0.02→0 for S3; baseline 14/20; loose 24/13). The
earlier "S3 m=4→0 fragility" was a narrow-probe artifact (hit-only, single floor), corrected here.

**Warning (non-Critical): recent-third → 0 passes for both series.** Temporal/out-of-regime stability is
**unconfirmed** — but this is a **power** artifact (⅓ TRAIN → n below the floor's resolution), not a signal
refutation (point estimates remain positive; cells fall to UNPOWERED_HINT/NULL, not POWERED_FAIL).
Materiality: does **not** move the in-sample verdict; it bounds the *strength* of the ADMIT (an
"explore," not a confirmed deployable edge). Recorded for the interpreter; a constant-n thirds test is the
clean follow-up.

---

## Scope Compliance

- Analysis plan (EXP-009 design + Amendments B1/B2) followed. ANALYSIS-ONLY, TRAIN-only, 0 counted reads,
  holdout sealed, referee untouched (L-12).
- Amendments recorded: **B1** (time-reversal demoted to diagnostic — mechanism), **B2** (endpoint-specific
  floors + precision-aware disposition + E1-or-E2 eligibility + per-stratum relaxation of axis-majority).
  All pre-binding-run or governance-directed; none results-tuned toward the ADMIT.
- Complexity: 3 stat-test types (block-boot CI, cross-axis Holm, leak tripwire) + robustness; new module
  `reversion_targets` + additive `STAT_MEAN` + script; within budget.

---

## Issues

### Warning
1. **recent-third temporal stability unconfirmed (power).** File: robustness. Both series → 0 passes at
   ⅓-TRAIN. Materiality: non-verdict-moving (in-sample ADMIT stands); bounds the claim to "explore," not
   "deployable." Fix: constant-event-count thirds test (future).

### Info
1. Entry-side live-limit fill not modeled (bar-open reference) — deferred to concretization.
2. UNPOWERED_HINT cells (253) are unresolved point estimates — suggestive, not confirmed; a positive lean
   could partly be the screen-fail control running slightly worse.
3. S1/S2 precision-limited (fewer extremes from trend-inflated median-MAD z) — a less-trend-contaminated z
   is a future anchor variant, not required for the ADMIT.
4. Floor-sensitivity is inherent to any effect-floor test; passes hold at the predeclared floors.

## Materiality & Re-Audit

- **0 Critical.** No verdict-material finding forces a rerun. The one Warning bounds the ADMIT's strength
  (explore-not-deploy) without moving the in-sample per-stratum verdict.
- **Audit verdict: PASS.** → Stage 5 (Document). Registry disposition: CF-MR-003 `REGISTERED →
  SCREENED-ADMIT (per-stratum, native vehicle)`; concretization deferred to a price-primary experiment.
