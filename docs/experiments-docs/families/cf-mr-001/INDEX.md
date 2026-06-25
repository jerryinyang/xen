# CF-MR-001 — Mean-Reversion Entry (RSI-2) — Detail Index

**Status:** `ADMITTED (BINDING) — G-020 adjudicated 2026-06-23; first candidate slot consumed` (EXP-089
`SCREEN_DELIVERED`, 2026-06-23, amended `D0-amendment-001`; G-020 ADMITTED). First candidate family opened
after the Phase 019 terminal branch, by **explicit operator override** of the G-019 price→non-price routing.
The availability screen consumed **0 counted TEST reads, holdout sealed**; **G-020 ADMITTED** (`S_fam=28 > S*=7`,
perm-p≈0.0002, FWER-robust, MC-stable) → **CF-MR-001 has now consumed its first candidate slot**, the
programme's first non-random price entry. The admitted lever is the **bare RSI-2 fade (CORE)** (the vol-regime
partition is inert; variants counter-productive); effect is **intraday (15m/1h)**, ~3-bar horizon.

**Batch 2 — Phase 021 OPEN** (G0 RATIFIED 2026-06-23, D0 FROZEN): the
**availability→tradability** step for the bare fade — exit / capture geometry / cost, intraday-first. See
[`../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md).
**EXP-090 (readiness/calibration) COMPLETE 2026-06-24 — `READINESS_CALIBRATION_DELIVERED`, 20 MEMBER / 12
COVERAGE_EXCLUDED (AMENDED `D0-amendment-002`; audit PASS)**. **EXP-091 (exit/capture-geometry screen) COMPLETE
2026-06-24 — `SCREEN_DELIVERED`, non-empty: EXIT-RCT passes the D6 quorum (5 cells / 5 instruments, all 1h); the
other 5 arms net-clear 0 cells.** The screen is non-empty ⇒ Phase 021 **advances to EXP-092** (cost-bearing
sequence) → EXP-093 (one-shot TEST), rather than closing at G-021 NOT_TRADABLE. **EXP-094 (4h falsification
re-screen) COMPLETE 2026-06-24 — `ADMIT_4H`: the 4h domain (opened via `D0-amendment-004`, binding null
corrected by `D0-amendment-005`, after the archived TEMP-091 hunch) is ADMITTED as a domain expansion (0 new
slots).** 6 MEMBER / 7 COVERAGE_EXCLUDED — TEMP-091's "RCT 12/12 on 4h" over-claimed (6 unpowered, incl.
USTEC/US2000-4h); on the 6 powered cells real EXIT-RCT beats the matched-distance + realized-capture oscillation
nulls **6/6** via a ~65%→~99% completion-rate lift → signal, not oscillation; bite-check GREEN (after a
corrected first-run RED); audit PASS (re-audit). EXP-092 now carries the 6 powered 4h cells alongside the 1h
survivors. **EXP-092 (per-instrument cost-bearing sequence) COMPLETE 2026-06-24 — `SEQUENCE_DELIVERED`: all 11
carried EXIT-RCT cells (5×1h + 6×4h) `SEQUENCE_PASS` (net `ci_low_1s` +0.0044…+0.135 ATR > 0, power-confirmed) →
hash-pinned candidate set (sha256 `f6427e83…`) + sized phase Holm rule for EXP-093; audit PASS (0C/0W/4I), 0
reads / 0 slots, holdout sealed.** The 11/11 masks a disclosed two-tier split — **robust core (8): all six 4h
members + USTEC-1h + US2000-1h** (margin-clearing AND mean-AND-median positive); mean-carried 1h (EURUSD-1h,
NZDUSD-1h, median<0); fragile GBPUSD-1h (below its 0.0125 margin, median −0.052 → pinned but NOT for TEST). →
EXP-093 carried **all 11** SEQUENCE_PASS cells (operator-ratified `D0-amendment-006`, superseding the §8.3
smallest-defensible sizing; Holm-11). **EXP-093 (one-shot TEST) COMPLETE 2026-06-24 — `TEST_CONFIRMED`: 8/11
cells CONFIRM** (`Holm-adj p=0.0011 ∧ net ci_low_1s > margin`) across 7 instruments and both domains — the
**programme's first net-positive out-of-sample price entry**, routing **G-021 TRADABLE**. Robust core = the six
4h cells (mean-AND-median positive) + USTEC-1h/US2000-1h (mean-carried); GBPUSD-1h & EURUSD-1h are well-powered
net-negative (EVIDENCE_AGAINST, OOS reversal), NZDUSD-1h near-zero (INCONCLUSIVE). **11 counted TEST reads spent
(each carried stratum 0→1; cap 2/stratum); final-30% global holdout never loaded; 0 slots.** Audit PASS (0C/1W
non-material/3I). **G-021 ADJUDICATED TRADABLE 2026-06-24 — Phase 021 CLOSED** ([`G-021-gate-review.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-review.md),
[`retrospective.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/retrospective.md)). A sanctioned
global-holdout release for the 4h core is a separate, later gate.
**Primary exit hypothesis = a native intrabar reversion-target pair** — **EXIT-RCT**
(operator-proposed; closed-form RSI₂→50 reversion-completion price `P*=Close+(AL−AG)`, proactive limit, 1m
intrabar fill) and **EXIT-ERT** (Claude-designed; price-returns-to-equilibrium-mean target) — measured against
conventional reactive contrast arms (RSI-revert-on-close, fixed-bar, ATR-barrier, partial/trail), adverse side
held fixed. The vol-regime / variant / contrarian / 25-75 / tuning / expansion branches remain deferred (each
needs its own dated `D0-amendment-*` + slot decision).

**Family spec:** [`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md)
· **Phase 020 checkpoint:** [`../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md)
(design · D0 · G-020 criteria · bite-check plan).

---

## What this family tests

The programme's first **mean-reversion (fade)** entry — every prior family was continuation/pullback. Plus a
**global, strategy-agnostic volatility-regime partition** treated as part of the signal definition (cell =
`asset+domain+regime`) — the hypothesis that *a filter can become the signal*. Opened over G-019's
price-exhausted verdict by operator override; the honest prior is **availability ≈ random**, so the screen is
a cheap falsification attempt (0 reads / 0 slots) reusing the Phase-019 admission gate.

## Frozen batch-1 surface (Phase 020 D0)

- **Entry:** `RSI(2)` Wilder, long `RSI₂<10` / short `RSI₂>90` (2 / 10 / 90 frozen).
- **Global filter `/VOLREGIME`:** `ATR(14)` causal rolling-50 percentile, 33/66 → Low/Med/High;
  per-(instrument,domain) thresholds; **partition on the bare core only**.
- **Variants (pooled):** TREND `EMA(20)`, RSI-FILTER `RSI(5)≷50`.
- **Six sub-screens → joint-max gate:** `CORE`, `CORE-VOL-LOW/MED/HIGH`, `CORE+TREND`, `CORE+FILTER`.
- **Endpoint (AMENDED `D0-amendment-001`, 2026-06-23):** entry-signed favourable `MFE_med`, ATR-normalised, over
  a **causal MR-tempo cap** (RSI-2 reversion-episode tempo, ~3-bar horizon; replaces the original trend-length
  MA-segment cap). **All 6 sub-screens are single-test leg-1** `Δ̂_rand` vs a matched `SUB-RANDOM` —
  **regime-matched** (same-regime bars) for the three `/VOLREGIME` sub-screens, all-bars for CORE/variants.
  TRAIN-only, 46 EXP-080-READY cells × {15m,1h,4h}.
- **RETIRED by `D0-amendment-001`:** the leg-2 beats-CORE conjunction + regime-membership-shuffle null (audit
  C-1: an ATR-normalization confound the leg-2 gate was blind to) and the trend-length cap (audit C-2). The
  regime-dependence question is now read directly from *which regimes' leg-1 passes* (answer: all three,
  uniformly — the regime adds nothing).
- **Deferred (registered, uncounted):** CONTRARIAN arm, 25/75 scheme, regime×variant cross-cuts, parameter
  tuning, expansion.

## Experiment cards

| EXP | HYP | Title | Status | Key finding |
| --- | --- | --- | --- | --- |
| EXP-089 | `CF-MR-001/HYP-001` | RSI-MR Availability Screen (bare core + vol-regime partition + 2 variants; 6 sub-screens; TRAIN-only; AMENDED) | **SCREEN_DELIVERED → G-020 ADMITTED (BINDING) 2026-06-23** | `S_fam=28 > S*=7`, perm-p≈0.0002, FWER-robust, MC-stable; driver = **CORE** (bare fade, z=17.3); vol-regime **inert** (LOW/MED/HIGH ≈22/25/20, flat Δ̂); variants kill it (0,1); intraday (15m 16/16, 1h 11/16, 4h 1/14); ~3-bar horizon. First run voided (deviation, audit C-1/C-2); amended (`D0-amendment-001`) — confounds confirmed removed. |
| EXP-090 | `CF-MR-001/HYP-002` | Exit-Substrate Readiness & Per-Cell Inference Calibration (32 cells = 16×{15m,1h}; TRAIN-only; AMENDED `D0-amendment-002`) | **READINESS_CALIBRATION_DELIVERED 2026-06-24** | **20 MEMBER / 12 COVERAGE_EXCLUDED** (10×15m + 10×1h members → EXP-091, margins RCT 0.0125 / ERT 0.025 ATR). All 12 excluded for the *same power reason* — no finite MDE on either native arm (not FPR/engine/coverage). 1m fill engine + FPR control clean (every member arm ≤0.050 both nulls). Two HALT-class confounds found+fixed+rerun (`D0-amendment-002`: 1m fill window/gap-fill; Null B path→returns). Median leg dropped (D5 non-binding). Audit PASS. |
| EXP-091 | `CF-MR-001/HYP-002` | Exit / Capture-Geometry Screen (20 member cells × 6 frozen exit arms; TRAIN-only; gross + EXP-085 cost; `D0-amendment-003` cost table) | **SCREEN_DELIVERED — non-empty (1 arm passes) 2026-06-24** | **EXIT-RCT (native reversion-completion target) is the only arm to pass the D6 quorum: 5 cells / 5 instruments (EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h, all 1h); ERT + 4 contrasts net-clear 0 cells → die at the screen.** Pure ATR-normalized cost geometry: gross ≈ domain-invariant (~0.28 ATR; RCT terminal_fav ~0.99; both natives gross-clear 20/20) but fixed-bps RT ÷ entry ATR costs ~0.6 ATR on 15m vs ~0.24–0.30 on 1h → 15m all net-negative (cost ≈ 2× gross), RCT 0/10 on 15m & 5/10 on 1h. *Availability ≠ capturable edge* realized. Native A/B: RCT > RSI-revert-on-close 20/20 (Δ median +0.261 ATR, Wilcoxon p≈1.9e-6, descriptive); ERT fails. Caveats (audit forensics): pass is 1h-only, boundary-fragile (GBPUSD-1h net_ci_low +0.0043), mean/tail-carried on 3/5 (median<0; only USTEC-1h & US2000-1h mean-and-median-positive). Faster-cost (RT/2): 14 cells → cost-dominated. Determinism PASS; holdout sealed; 0 slots, 0 TEST reads. Audit PASS (0C/3W/3I). Non-empty ⇒ advances to EXP-092. |
| EXP-094 | `CF-MR-001/HYP-002` | 4h Readiness + Falsification Re-Screen (4h-only; `D0-amendment-004` opens 4h + `D0-amendment-005` corrects binding null; TRAIN-only) | **`ADMIT_4H` 2026-06-24 — 4h ADMITTED (domain expansion, 0 new slots)** | **6 MEMBER / 7 COVERAGE_EXCLUDED** — TEMP-091's "RCT 12/12 on 4h" over-claimed (6 unpowered incl. USTEC/US2000-4h; JP225 build-fail). On the 6 powered cells (AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h): real EXIT-RCT beats the **binding matched favourable-target-distance oscillation null 6/6** (`delta_lo` 0.19–0.27) **and** the **realized-capture sensitivity null 6/6** → entry signal, not oscillation harvesting. Mechanism: reversion-completion hit rate **~65% (random) → ~99% (real)**, identical exit/stop/fill/cost; null nets −0.09…−0.18, real +0.07…+0.16. Net screen 6/6; 1h positive control 5/5; **bite-check GREEN** (per-cell power leg corrected after a first-run RED miscalibration). All 6 members **mean-AND-median net-positive** (robust core). Determinism PASS; holdout sealed; 0 slots, 0 TEST reads (4h strata 0/2). Audit PASS (re-audit; 1 CRITICAL fixed-and-rerun, 1 Warning closed). → EXP-092 carries the 6 powered 4h cells. |
| EXP-092 | `CF-MR-001/HYP-002` | Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT on 11 carried cells = 5×1h EXP-091 + 6×4h EXP-094; TRAIN-only; A1-style) | **`SEQUENCE_DELIVERED` 2026-06-24 — candidate set hash-pinned** | **All 11 carried EXIT-RCT cells `SEQUENCE_PASS`** (net `ci_low_1s` +0.0044…+0.135 ATR > 0 at α=0.05, power-confirmed) → **hash-pinned candidate set (sha256 `f6427e83…`) + sized phase Holm rule** for EXP-093; non-empty ⇒ Phase 021 advances to the one-shot TEST. Re-derivation matches independent EXP-091/094 within ≤6.2e-4 (independent seeds; byte-identical resolved counts). **Masking check (disclosed two-tier split): robust core (8) = all six 4h members + USTEC-1h + US2000-1h** (margin-clearing AND mean-AND-median positive); mean-carried 1h (EURUSD-1h, NZDUSD-1h, median<0); **GBPUSD-1h** below its 0.0125 margin (median −0.052) → pinned but should NOT carry to TEST. 4h dominates the ranking (smaller ATR-normalized cost). Gate-shape OK (binding mean + co-reported median, D5). Determinism PASS; holdout sealed; 0 slots, 0 counted TEST reads (11 carried strata 0/2). Audit PASS (0C/0W/4I). |
| EXP-095 | `CF-MR-001/HYP-003` | Portfolio Construction & Online-Adaptive Risk Model (8 G-021-confirmed cells; causal ERC **A** vs circuit-breaker **B** vs deployment-realistic baseline + naive-IV; analysis-set, noise-free; NO holdout verdict; **D0-amendment-001 rerun**) | **COMPLETED 2026-06-25 — portfolio benefit SUPPORTED; ERC ≈ naive-IV; circuit-breaker NEUTRAL (no material de-risking); gate statistic READY (re-audit PASS).** D0-amendment-001 restored intra-1h MTM (D0 §D2.1; prior flat-at-exit was a verdict-material defect), like-for-like benefit + median-cell baseline, co-binding Calmar/CVaR/Ulcer, MDE-curve bite. A Sharpe **11.69 (lo 10.24)** / B 11.57 (lo 10.19) / naive-IV 11.55 (lo 10.07) / best cell US2000-1h 8.73 (lo 7.53). **Benefit SUPPORTED** (corrects prior "NOT MET"): A/B Sharpe LB clears every baseline (median-cell 4.99 +5.25; best-cell point 8.73; best-cell LB 7.53 +2.71; naive-IV LB 10.07) + Calmar LB (+53) → genuine moment-to-moment diversification of 8 low-corr cells (mean |corr| 0.10), portfolio MaxDD 0.034 below every constituent (the benefit flat-at-exit hid). **Reversals:** ERC **≈ naive-IV** (prior refute overturned); **circuit-breaker NEUTRAL** — A ≈ B within noise (MaxDD 3.44% vs 3.75%; B better on Ulcer), no material de-risking (prior −22.4% was a flat-at-exit artifact), a wash not a degradation. **Gate READY** (was NOT READY): MDE m*=1.75/2.00, FPR 0.000/0.002, realized LB 10.24 ≫ m* → `statistic_ready=true`; G-022a band ≥ m*. **Scale caveat:** Sharpe ~11-12 in-sample favorable-selected, binding read EXP-097. Verified faithful (conservation exact, marks causal, A1-A4 predeclared); 0 reads/0 slots, 11 carried strata stay 1/2. *Prior (superseded, flat-at-exit) record retained.* | A Sharpe **9.87 (MBB lo 8.59)** / B **9.34 (lo 8.15)** / naive-IV **10.11 (lo 8.81)** / best cell US2000-1h **8.68**. **Diversification — faithful negative:** A/B point Sharpes beat every cell, but their **lower bounds (8.59/8.15) fall just below** best-cell point (8.68) → pre-registered "portfolio benefit" NOT MET; only naive-IV's lower bound clears it, and **ERC does NOT beat naive-IV** (10.11>9.87>9.34, sub-thesis refuted). **Headline positive — circuit-breaker B de-risks:** de-allocates the fragile 1h cells (USTEC 12.0% / US2000 5.4% of grid steps) → **MaxDD −22.4%** (0.0769→0.0596), **Calmar 20.3→26.3**, −0.52 Sharpe, ann-return unchanged → SUPPORTED descriptively. **NEW portfolio gate statistic NOT READY:** FPR controlled (A 0.000/B 0.001 ≤0.05) but **bite-check RED** (planted-fire 0.10/0.15 vs 0.80 floor; `statistic_ready_for_g022a=false`) — structural power artifact at n=79 weeks (generic Sharpe=1.0 plant), **not "no edge"** → G-022a gate-scale decision. **C1 fix re-audited PASS** (cap on un-anchored weights → 1/vol² → vol-anchor first; vol ~1%→13%, gross-lev CV 0.99→0.25, cap dormant, Sharpe scale-invariant 1.8e-15). Determinism/causality/holdout clean; provenance abs-diff 0.0; **0 slots, 0 counted TEST reads** (11 carried strata stay 1/2). Analysis-set only — binding read is EXP-097. Audit PASS (re-audit). |
| EXP-093 | `CF-MR-001/HYP-002` | **One-Shot TEST Confirmation** (EXIT-RCT on all 11 EXP-092 SEQUENCE_PASS cells; analysis-TEST stratum; Holm-11; `D0-amendment-006`) | **`TEST_CONFIRMED` 2026-06-24 — HYP-002 tradability SUPPORTED → routes G-021 TRADABLE** | **8/11 cells CONFIRM** (`Holm-adj p=0.0011 ∧ net ci_low_1s > margin`) across **7 instruments, both domains** — the **programme's first net-positive out-of-sample price entry.** **Robust core = six 4h cells mean-AND-median positive** (net_ci_low 0.039–0.094 vs 0.025: EURUSD +0.094 / XAUUSD +0.072 / USDCHF +0.062 / AUDJPY +0.057 / EURJPY +0.044 / GBPJPY +0.039) + **two mean-carried 1h** (US2000-1h +0.073, USTEC-1h +0.046; USTEC TEST median −0.026). Non-confirm: **GBPUSD-1h (ci_low −0.103, n=1653) & EURUSD-1h (−0.032) well-powered net-negative — EVIDENCE_AGAINST (OOS reversal)**; NZDUSD-1h near-zero (INCONCLUSIVE). Mechanism: RCT target hit ~99%; 4h nets clear via cost geometry (smaller ATR-cost fraction), not stronger signal; uniform TRAIN→TEST shrinkage (Δ ci_low −0.005…−0.107) — robust core absorbed it, thin 1h tier did not. **11 counted TEST reads spent (each carried stratum 0→1; cap 2/stratum); final-30% global holdout never loaded; 0 slots.** Determinism PASS; numbers reproduced from raw data. Audit PASS (0C/1W non-material re-label/3I). |

### EXP-089 — detailed card (`CF-MR-001/HYP-001`)

- **Hypothesis tests:** does the RSI-2 fade — bare, vol-regime-partitioned, or trend/momentum-filtered — beat
  the multiplicity-adjusted joint-max permuted-axis availability gate (`S_fam > S* ∧ axis perm-p ≤ 0.05`) on any
  of 6 sub-screens? (One binding test: the D2b gate.)
- **Scope:** TRAIN-only, gross, real-OHLC; 46 EXP-080-READY cells × {15m,1h,4h}; entry-signed favourable
  `MFE_med` (ATR units) over a causal MR-tempo cap; leg-1 single-test all 6 sub-screens; regime-matched control
  for `/VOLREGIME`. 0 slots, 0 counted TEST reads, holdout sealed. Amended in place (`D0-amendment-001`).
- **Results / observations:** `SCREEN_DELIVERED`; `S_fam=28`, `S*=7`, axis perm-p≈0.0002, ADMITTED across FWER
  {0.025/0.05/0.10}, MC-stable. Per sub-screen S — CORE **28**, VOL-LOW 22, VOL-MED 25, VOL-HIGH 20, TREND 0,
  FILTER 1. Regime `Δ̂_rand` flat (LOW 0.050 / MED 0.080 / HIGH 0.045 ATR); CORE 0.060. Per-domain CORE passes
  15m 16/16, 1h 11/16, 4h 1/14; all 16 instruments represented; effective ~3-bar horizon (77% caps at FLOOR=3);
  favourable `MFE_med` ≈0.75 ATR. Determinism/recon/holdout-fence clean; bite GREEN `f01a000b…`. Audit PASS
  (0C/0W/3I).
- **Hypothesis-specific conclusion (NON-BINDING — G-020 binding):** provisional **ADMITTED**, driven by the
  **bare RSI-2 fade (leg 1, CORE)** — *not* the vol-regime partition (inert) and *not* a variant
  (counter-productive). On admit, G-020 opens the bare fade, intraday, first. Availability ≠ tradability.
- **Hypothesis-agnostic observations:** (1) imposing trend/momentum agreement on a fade destroys its favourable
  availability (TREND/FILTER → S 0/1) — direct, unambiguous. (2) The short-horizon reversion availability is a
  higher-frequency phenomenon, monotone-decaying 15m→1h→4h and absent by 4h. (3) The result is conservative
  w.r.t. ATR-normalization (extremes carry elevated entry ATR, deflating the signal metric).

### EXP-090 — detailed card (`CF-MR-001/HYP-002`)

- **Hypothesis tests:** readiness/calibration (no edge claim) — for each of 32 cells (16 × {15m,1h}) on TRAIN:
  (1) bare-fade entry deterministic, look-ahead-safe, ≥15 events; (2) every frozen exit arm resolves to one
  terminal through the 1-minute engine (deterministic, timestamp-aligned, causal, holdout-fenced, real fill
  prices); (3) controlled per-cell FPR (≤0.05 under two structurally-different nulls) and a **finite event-level
  MDE** under the binding mean net-expectancy lower bound (`Z=1.645`). One binding estimator, none gates a
  market edge.
- **Scope:** TRAIN-only, gross, real-OHLC; 32 cells; five unified-engine arms (RCT, ERT, ATR-barrier,
  RSI-revert, fixed-bar; two-leg partial/trail deferred to EXP-091); calibration on matched-random exit-resolved
  returns (real fade outcomes never read — anti-overfitting fence). New module `xen.intrabar_fill`. 0 slots, 0
  counted TEST reads, holdout sealed. Amended in place (`D0-amendment-002`).
- **Results / observations:** `READINESS_CALIBRATION_DELIVERED`; **20 MEMBER / 12 COVERAGE_EXCLUDED**,
  determinism PASS (EURUSD-15m, AUDJPY-1h byte-identical; SHA-pinned). Members 10×15m + 10×1h, carried margins
  RCT 0.0125 / ERT 0.025 ATR (RCT carries 15 cells, ERT 5). All 32 cells `IN_FLOOR` (15m 12,827–16,225; 1h
  3,293–4,156 events; dropped ≤0.217). Fill-validity / timestamp / determinism TRUE ∀ cell×arm; resolution
  0.991–1.000; tie-break ≤0.18%. FPR symmetric+controlled (native median 15m 0.050/0.049, 1h 0.051/0.048
  A/B; every member arm ≤0.050 under both nulls); `null_fpr_sanity.controlled_alpha0:false` is the over-strict
  pooled boolean tripping on noise-level points (A max 0.071, B 0.082). The 12 excluded all fail *no finite MDE
  on either native arm*. Median leg dropped (D5 non-binding; mean bit-identical to `xen.ass`). **Audit (3
  runs):** Run 1 HALT (1m fill-window over-assignment + limit gap-throughs), Run 2 Null-B path-rotation
  pathology (ATR-return variance ×30–145), both fixed (`D0-amendment-002`) + rerun. Audit PASS.
- **Hypothesis-specific conclusion:** **DELIVERED.** The bare-fade entry + 1-minute intrabar exit-fill engine +
  the binding referee are constructible, deterministic, causal, fenced, and **powered on 20 of 32 cells**, which
  carry to EXP-091 with their margins. The 12 excluded cannot bound a confirmation at their count (with record).
  No edge claimed — the real fade outcomes were never resolved (EXP-091 does that first).
- **Hypothesis-agnostic observations:** (1) the 1-minute fill model must anchor each domain bar to its **own**
  resample window and fill limit/stop gap-throughs at the touching 1m **open** — anchoring to the previous kept
  close corrupts fills across dropped/session-gap windows (a reusable readiness invariant). (2) A calibration
  second null must **block-permute the resolved returns**, not rotate the price path, when returns are
  ATR-normalised and the binding statistic is the **mean** (path rotation matches entries to wrong-era prices →
  variance ×30–145; harmless under a median statistic, fatal under a mean). (3) With a hard ≤0.05 FPR gate and
  ~±0.014 sampling noise, membership near the boundary flips between runs — the 9 cells that were members under
  both the broken and fixed Null B are the robust core.

### EXP-091 — detailed card (`CF-MR-001/HYP-002`)

- **Hypothesis tests:** over the frozen D2 exit slate on the 20 EXP-090 member cells, net of EXP-085 cost,
  TRAIN-only — (1, binding) does **any** exit net-clear (`net ci_low_1s>0`, moving-block bootstrap) in a quorum
  of **≥5 cells / ≥3 instruments**? (2, descriptive) do the native intrabar targets beat the reactive contrast,
  esp. RCT vs RSI-revert-on-close? Empty screen ⇒ G-021 NOT_TRADABLE at 0 reads.
- **Scope:** TRAIN sub-split; real OHLC; 6 frozen arms (native RCT/ERT + contrast RSI-revert-on-close, fixed-bar,
  ATR triple-barrier, partial/trail), single parameter point each; reuses the EXP-090 `xen.intrabar_fill`
  substrate verbatim; net of the operator-ratified Phase-021-local conservative cost table (`D0-amendment-003`,
  RT 3–6 bps, F=0). 0 slots, 0 counted TEST reads, holdout sealed. Pre-exec issue caught + resolved at Stage 4:
  the inherited EXP-085 `COST_CONSTANTS` priced only 4 of 13 member instruments → a global OHLC-spread RT rule
  was attempted and empirically refuted (Abdi–Ranaldo / Corwin–Schultz ~10× inflated on no-quoted-spread data),
  so a Phase-021-local table was frozen (`D0-amendment-003`); shared module not mutated (Phase-018 integrity).
- **Results / observations:** `SCREEN_DELIVERED`, non-empty. **EXIT-RCT passes (5 cells / 5 instruments, all
  1h: EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h); ERT, ATR-barrier, RSI-revert-on-close, fixed-bar, partial/trail all
  net-clear 0 cells.** Both natives gross-clear 20/20 (availability real and broad; RCT terminal_fav ~0.99, gross
  ~0.27–0.30 ATR all cells); the conventional arms gross-clear only 7–8/20. Net collapse is pure ATR-normalized
  cost: fixed-bps RT ÷ entry ATR(14) = ~0.6 ATR on 15m vs ~0.24–0.30 on 1h, so 15m is all net-negative and RCT
  clears 0/10 on 15m, 5/10 on 1h. Native A/B: RCT − RSI-revert net Δ > 0 in 20/20 cells (median +0.261 ATR,
  Wilcoxon p≈1.9e-6, descriptive/non-binding). Determinism PASS (USTEC-15m + EURUSD-1h); 5 CSVs SHA-256-pinned;
  resolution 0.9943–0.9996; min n_resolved 3835. Audit PASS (0C/3W/3I).
- **Hypothesis-specific conclusion:** the bare RSI-2 fade's gross availability **does** convert to a positive
  net-of-conservative-cost expectancy — but **only via RCT, only on 1h, only on the cheapest instruments, and on
  a boundary-fragile, partly mean/tail-carried basis** (3 of 5 clearing cells have net_median<0; only USTEC-1h &
  US2000-1h are mean-and-median-positive). Screen non-empty ⇒ advances to EXP-092 (1h-scoped, smallest-defensible
  candidate set centered on the robust core), not G-021 NOT_TRADABLE.
- **Hypothesis-agnostic observations:** (1) ATR-normalized transaction cost scales inversely with the bar's ATR,
  so the *same* bps round-trip is structurally lethal on the faster domain — a short-horizon fade's tradability
  is decided by cost geometry, not signal strength, exactly as the honest prior predicted. (2) Proactive intrabar
  resting + 1m fill (RCT) beats reactive exit-on-close (RSI-revert) by ~0.26 ATR/event uniformly — the phase's
  organizing hypothesis is supported, but only for the *near* native target (RCT); the *far* one (ERT, return to
  EMA10) holds longer into adverse moves and fails. (3) The faster-cost companion (RT/2 → 14 clears) confirms the
  result is cost-dominated, not signal-absent — the edge exists gross and is reachable under a less conservative
  cost assumption.

### EXP-092 — detailed card (`CF-MR-001/HYP-002`)

- **Hypothesis tests:** for the sole surviving exit **EXIT-RCT**, which of the 11 carried `(instrument, domain)`
  cells reach a TRAIN-only `SEQUENCE_PASS` (net `ci_low_1s>0` at α=0.05 one-sided, power-confirmed by the
  EXP-090/094 MDE), and what hash-pinned candidate set + phase Holm rule does that yield for EXP-093? (D6/4b;
  necessary-but-not-sufficient for TEST — decides no G-021 verdict.)
- **Scope:** TRAIN sub-split only; EXIT-RCT on the inherited survivor cells — 1h {EURUSD, GBPUSD, NZDUSD, US2000,
  USTEC} (EXP-091 quorum) + 4h {AUDJPY, EURJPY, EURUSD, GBPJPY, USDCHF, XAUUSD} (EXP-094 `ADMIT_4H` members);
  real OHLC, ATR(14); net of the `D0-amendment-003` conservative cost; verbatim EXP-090 substrate +
  `xen.intrabar_fill`; 1 binding test / 4 plots / 0 new modules; 0 slots, 0 counted TEST reads, holdout sealed.
- **Results / observations:** `SEQUENCE_DELIVERED`; **11/11 `SEQUENCE_PASS`**, candidate set pinned at sha256
  `f6427e8342400d46…` (reproduced from the canonical serialization). `net_ci_low` +0.0044 (GBPUSD-1h) … +0.135
  (EURUSD-4h); 4h holds ranks 1–4, 7, 8. Resolved counts byte-identical to EXP-091/094 (1h ~3845–3984, 4h
  855–1088); `terminal_fav` ~0.99; determinism PASS (USTEC-1h, EURUSD-4h). Cross-check vs the independent
  EXP-091/094 bounds agrees within ≤6.2e-4 (seed-level), all same-sign. Margin pre-read (`margin_preread.csv`):
  10/11 clear the EXP-093 margin (only GBPUSD-1h fails, 0.0044<0.0125); 8/11 mean-AND-median positive.
- **Hypothesis-specific conclusion:** the candidate set is **non-empty and frozen**, so Phase 021 proceeds to
  the EXP-093 one-shot TEST. The defensible carry is the **robust core (8)** — all six 4h members + USTEC-1h +
  US2000-1h (margin-clearing AND mean-AND-median positive); **GBPUSD-1h is excluded** (below margin,
  median-negative) and the two mean-carried 1h cells (EURUSD-1h, NZDUSD-1h) are lower priority than the 4h core.
  No out-of-sample edge is claimed — this is a TRAIN eligibility set.
- **Hypothesis-agnostic observations:** (1) the 4h cells systematically out-rank the 1h cells on the binding
  net lower bound despite ~4× fewer events — larger effect per event (smaller ATR-normalized cost), not noise;
  (2) the family's median-fragility is **1h-specific** here (4h members are uniformly mean-AND-median positive),
  reproducing the EXP-094 robustness contrast; (3) a pooled "11/11 pass" headline would mask the quality split —
  the per-cell margin + mean/median flags are what make the EXP-093 selection mechanical.

### EXP-093 — detailed card (`CF-MR-001/HYP-002`)

- **Hypothesis tests:** of the 11 EXP-092 hash-pinned EXIT-RCT cells, which **CONFIRM** on the analysis-TEST
  stratum under the frozen referee, phase **Holm-11**, and the per-cell margin (`CONFIRM iff Holm-adj p ≤ 0.05 ∧
  net ci_low_1s > margin`; D6/4c)? The phase's single binding tradability read. (1 binding test + descriptive
  companions.)
- **Scope:** analysis-TEST stratum only (`[ts_lo, analysis_edge]`, last 30% of the first-70% analysis set);
  verbatim EXP-090/092 substrate, the only change being the TEST loader (TRAIN region = causal warmup, no TRAIN
  entry in the estimand; 1m fill clips at the analysis edge); EXIT-RCT, 2.0×ATR stop + MR-tempo cap,
  `D0-amendment-003` cost (F=0); 4 plots / 0 new modules. Carried set = **all 11 SEQUENCE_PASS cells, Holm-11**
  (operator-ratified `D0-amendment-006`, superseding the §8.3 "smallest defensible" sizing). **11 counted TEST
  reads (each carried stratum 0→1; cap 2/stratum); final-30% global holdout never loaded; 0 candidate slots.**
- **Results / observations:** `TEST_CONFIRMED` — **8 CONFIRM / 3 non-confirm.** The **six 4h cells** clear
  `Holm-adj p=0.0011` with `net ci_low_1s` 0.039–0.094 (1.6–3.7× the 0.025 margin), **mean-AND-median positive**
  (EURUSD-4h +0.094/+0.060, XAUUSD +0.072/+0.085, USDCHF +0.062/+0.056, AUDJPY +0.057/+0.026, EURJPY +0.044/+0.015,
  GBPJPY +0.039/+0.018; n 388–458). The **two 1h confirms** (US2000-1h ci_low +0.073, USTEC-1h +0.046; n~1.6k)
  clear the binding mean but are mean-carried (USTEC TEST median −0.026, US2000 ≈+0.004). Non-confirm (audit-W1
  re-label): **GBPUSD-1h (net_mean −0.080, ci_low −0.103, n=1653) and EURUSD-1h (−0.010, −0.032, n=1619) are
  well-powered net-negative — EVIDENCE_AGAINST**; **NZDUSD-1h (+0.003, −0.015) near-zero — INCONCLUSIVE**.
  `terminal_fav` 0.985–0.996; `tie_break_frac≈0`; determinism PASS (USTEC-1h, EURUSD-4h); numbers reproduced
  from raw data; holdout untouched. Audit PASS (0C / 1 non-verdict-material Warning [the INCONCLUSIVE-label
  coarseness, routed to interpretation] / 3I).
- **Hypothesis-specific conclusion:** **HYP-002 tradability SUPPORTED** — ≥1 carried cell CONFIRMS (8, across 7
  instruments and both domains), so the bare RSI-2 fade with EXIT-RCT is **net-tradable out-of-sample**, routing
  **G-021 TRADABLE.** The **programme's first net-positive OOS price entry**, reversing the G-019 "price-derived
  information exhausted" routing for this lever. The read is on the analysis-TEST stratum — **not** a global-
  holdout confirmation (that is a separate, later gate; the final-30% global holdout stays sealed).
- **Hypothesis-agnostic observations:** (1) the OOS confirm reproduces the EXP-091/092 **cost-geometry**
  mechanism — gross is ~domain-invariant (~0.22–0.31 ATR) and 4h nets clear by a wider margin only because
  fixed-bps cost is a smaller ATR fraction there; 4h dominance is not a stronger 4h signal. (2) **Selection-
  overlap shrinkage is uniform** (every cell shrank TRAIN→TEST, Δ net_ci_low −0.005…−0.107); the robust core's
  larger TRAIN bounds survived above margin while the thin-margin 1h tier reversed — the honest *availability ≠
  capturable edge* prior, with the strongest cells holding. (3) The family's median-fragility is **1h-specific**
  out-of-sample too — the six 4h confirms are mean-AND-median positive, the two 1h confirms are mean-carried.

### EXP-095 — detailed card (`CF-MR-001/HYP-003`)

**Status**: COMPLETED 2026-06-25 (D0-amendment-001 amend-in-place rerun; analysis-set only — NO holdout verdict) · **Phase**: 022 (batch 3) · **Audit**: PASS (re-audit — C1 fixed + MTM defect corrected; verified faithful, not goalpost-moving)
**Instruments**: 8 G-021-confirmed cells (EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/GBPJPY-4h + USTEC-1h + US2000-1h)
**Data Views / Feature Categories**: per-cell EXIT-RCT net per-event return streams (ATR units) reused from the EXP-090/093 substrate **with intra-1h mark-to-market of open positions** (D0 §D2.1 / amendment-001 A1); analysis set (TRAIN + EXP-093 analysis-TEST series as portfolio-aggregate disclosure); causal 1h common grid.

#### Hypothesis Tests

1. **Hypothesis (`HYP-003`, portfolio-economics leg):** a causal, parameter-free ERC portfolio of the 8 confirmed cells delivers materially better risk-adjusted performance (annualized Sharpe lower bound) than a deployment-realistic single-cell baseline, and an online circuit-breaker (Portfolio B) de-risks vs static ERC (Portfolio A).
   - Sub-read (gate readiness): the NEW portfolio-level confirmation statistic is calibrated (synthetic-null FPR ≤ 0.05) and has a finite, clearable MDE so G-022a can freeze it.

#### Scope

- **Instruments**: the 8 deployable cells (no instrument/domain outside the set).
- **Risk model (frozen, D0)**: ERC on a causal trailing-90-day Ledoit-Wolf covariance, weekly rebalance, 10% annualized-vol anchor, 1.5× concurrent-risk cap; circuit-breaker (B) = de-allocate a cell whose trailing-50-trade mean net < 0. **Amendment-001:** intra-1h MTM (A1; P&L matrix for returns/cov, per-trade matrix for counts/breaker); like-for-like benefit vs cross-cell-median baseline (A2); co-binding Calmar/CVaR/Ulcer (A3); MDE-curve bite (A4). Brackets disclosure-only, never tuned.
- **Exclusions**: final-30% global holdout never loaded; noise/entry-fill model (EXP-096); any exit re-resolution or hyperparameter selection from brackets.
- **Constraints**: causal everywhere; timestamp alignment (`CloseTime`), never bar index; real-price outcomes; 0 candidate slots, 0 counted TEST reads.

#### Results / Observations

- Portfolio A (static ERC): ann Sharpe **11.691**, MBB one-sided lo **10.239**, MaxDD **0.0344**, Calmar **71.75** (lo 61.34), ann_return 0.950, ann_vol 0.112, n_weeks 185.
- Portfolio B (ERC + circuit-breaker): Sharpe **11.572**, lo **10.187**, MaxDD **0.0375**, Calmar **66.35** (lo 57.50), Ulcer 0.0037, ann_return 0.938, ann_vol 0.113.
- Naive inverse-vol (disclosed contrast): Sharpe **11.546**, lo **10.066**, MaxDD 0.0309.
- Best single cell: US2000-1h Sharpe **8.725** (lo **7.526**). Per-cell Sharpe LBs: EURUSD-4h 6.10, XAUUSD-4h 3.43, USDCHF-4h 5.04, AUDJPY-4h 4.94, EURJPY-4h 2.01, GBPJPY-4h 3.50, USTEC-1h 6.50, US2000-1h 7.53. Cross-cell median Sharpe LB **4.99**; median Calmar LB 8.25.
- Benefit (binding, like-for-like LB-vs-LB): A/B Sharpe-LB margin vs median-cell baseline **+5.25 / +5.20** (ADDS_VALUE); A vs best-cell LB **+2.71**; A LB (10.24) > naive-IV LB (10.07); co-binding Calmar-LB margin **+53.1 / +49.3** (ADDS_VALUE). Mean cross-cell |corr| **0.10**; portfolio MaxDD (0.034) below every constituent (0.031–0.100).
- Circuit-breaker de-allocation timeline intact (fragile 1h cells); B MaxDD 0.0375 **>** A 0.0344.
- Calibration (MDE-curve): FPR A **0.000** (Wilson-hi 0.0038) / B **0.002** (0.0073) — controlled; gate **MDE m\*** A **1.75** / B **2.00** (finite); realized portfolio LB 10.24 ≫ m\* ⇒ `statistic_ready_for_g022a=true`.
- Integrity: MTM conservation Σ(marks)=net per cell ≤2.8e-14; marks causal (perturbation test); determinism byte-identical; `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`; provenance reconciled abs-diff 0.0 (8/8); vol-anchor Sharpe-invariance 1.8e-15.

> Note: No interpretation — preserve what the data shows.

#### Hypothesis-Specific Conclusion

**SUPPORTED (analysis-set; no holdout verdict).** Restoring the D0 §D2.1 intra-1h mark-to-market reverses the superseded flat-at-exit reading: the portfolio Sharpe **lower bound** (A 10.24 / B 10.19) **clears every baseline** — cross-cell median (4.99, +5.25), best-cell point (8.73), best-cell LB (7.53, +2.71), and naive-IV LB (10.07) — with co-binding Calmar LB also clearing; margins ≫ the sampling band. Mechanism: genuine moment-to-moment diversification of 8 low-correlation cells (mean |corr| 0.10) → portfolio MaxDD below every constituent (the benefit the lumpy booking hid). **Two reversals (faithful negatives):** ERC **≈ naive-IV** (marginally ahead; prior refutation overturned); the **circuit-breaker is NEUTRAL** — A ≈ B within noise (Sharpe LB 10.24 vs 10.19; MaxDD 3.44% vs 3.75%; B marginally *better* on Ulcer), so its positive de-risking claim is not supported (the prior −22.4% MaxDD was a flat-at-exit artifact) — a wash, not a degradation. The NEW gate statistic is **READY** (FPR-controlled + finite, clearable MDE m\*=1.75/2.00). **Scale caveat:** Sharpe ~11–12 is in-sample favorable-selected, not deployment-realistic; binding read = EXP-097.

#### Hypothesis-Agnostic Observations

- **Booking method changes the verdict for a high-frequency overlapping-position portfolio:** flat-at-exit lumping understated diversification (and spuriously credited the circuit-breaker with drawdown reduction); continuous mark-to-market is required for economically comparable portfolio risk statistics across domains.
- **Equal-risk-contribution ≈ naive inverse-vol** in-sample on this low-correlation set — the diversification lift is generic (averaging imperfectly-correlated cells), not an ERC-specific property.
- **A bite/readiness gate must report its detectable effect (MDE), not assert a fixed plant:** a fixed Sharpe=1.0 plant is structurally unattainable at the ~79-week holdout-equivalent (recurring since EXP-094); the MDE-curve fixes this and feeds the G-022a band (band ≥ m\*).

## Gate

| Gate | Status | Outcome |
| --- | --- | --- |
| G-020 | **ADMITTED — adjudicated 2026-06-23** ([`G-020-gate-review.md`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md); criteria [`G-020-gate-criteria.md`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-criteria.md)) | **ADMITTED** — `S_fam=28 > S*=7`, axis perm-p≈0.0002 ≤ 0.05 (FWER 0.05, no cross-axis Holm). Lever = **bare RSI-2 fade (CORE)**, intraday; vol-regime inert, variants dead. **CF-MR-001 consumes its first candidate slot.** Next scope (future G0/D0): capture-geometry / exit / cost for the bare fade. 0 counted TEST reads; holdout sealed; ledger unchanged. |
| G-021 | **TRADABLE — ADJUDICATED 2026-06-24** ([`G-021-gate-review.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-review.md); criteria [`G-021-gate-criteria.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-criteria.md); Phase 021 CLOSED, [`retrospective.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/retrospective.md)) | EXP-093 `TEST_CONFIRMED` — **8/11 carried cells CONFIRM** (`Holm-adj p=0.0011 ∧ ci_low_1s > margin`), six 4h mean-AND-median-positive + USTEC-1h/US2000-1h mean-carried, across 7 instruments and both domains. Per the frozen D6/4c mechanical rule (`TRADABLE iff ≥1 carried cell CONFIRMS`), G-021 **routes TRADABLE** — the bare RSI-2 fade is the **programme's first net-positive OOS price entry.** Non-confirm: GBPUSD-1h/EURUSD-1h EVIDENCE_AGAINST (OOS reversal), NZDUSD-1h INCONCLUSIVE. **11 counted TEST reads spent (each carried stratum 0→1); final-30% global holdout never loaded.** Next (separate gates): a sanctioned global-holdout release decision for the 4h robust core; deferred levers each under their own slot/D0. |
| G-022a | **PLANNED (pre-holdout freeze)** — Phase 022 | EXP-095 (COMPLETE, D0-amendment-001 rerun) delivered the analysis-set portfolio read and the **gate statistic is now READY** (`statistic_ready_for_g022a=true`: FPR controlled A 0.000/B 0.002; MDE-curve resolves m\*=1.75/2.00 cleared by realized LB 10.24). G-022a must (i) **freeze the confirmation band ≥ m\*** (≥1.75 A / ≥2.00 B) and adopt the MTM construction; (ii) take the EXP-096 noise-survivor deployable set; (iii) **decide A vs B** (the circuit-breaker is now neutral — no drawdown benefit on the analysis set) — else HALT (holdout preserved). EXP-095 recorded: **portfolio benefit SUPPORTED** (diversification clears every baseline); ERC ≈ naive-IV; circuit-breaker NEUTRAL (A ≈ B; no material de-risking). |
| G-022 | **PLANNED (terminal)** — Phase 022 | DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE on the EXP-097 global-holdout release, per the G-022a-frozen band. Binding deployment verdict; gated behind G-022a. |
