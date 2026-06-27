# CF-MR-001 — Mean-Reversion Entry (RSI-2) — Detail Index

**Status:** `CLOSED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead invalidates the net-tradable / deployment
arc (EXP-091→098). G-021 TRADABLE + G-022 DEPLOYABLE_CONFIRMED RETRACTED. Availability-only (EXP-089 / G-020
ADMITTED) stands. Family not reopenable by re-parameterization; outcomes retained.` See **§CLOSURE** below.

> ## §CLOSURE — REFUTED (2026-06-26): EXIT-RCT exit look-ahead
>
> **Source of truth:** `XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md` (final) +
> `XRSI-V1/ISSUE-booked-vs-real-feed-divergence.md` (initial), confirmed by an independent Xen-code trace.
>
> **Mechanism (the why).** EXIT-RCT's favourable intrabar limit is built with a one-bar look-ahead.
> `arm_levels` (`python/experiments/EXP-090/code/run_experiment.py:305-310`) sets the resting limit for the
> domain bar at offset `off` (`di = entry_idx+off`) to `ctx.rct_target[di]` — the reversion-completion target
> `P*_di = Close_di + (period-1)·(AL_di − AG_di)` computed from **bar `di`'s own close**
> (`python/src/xen/mean_reversion.py:174`; the readiness invariant treats `rct_target[i]` as the *hypothetical
> next-bar close*, i.e. the target for bar `i+1`). A limit that can rest *during* bar `di` is only live-actable
> from `rct_target[di-1]`. `resolve_exit_paths` reads `fav_level[j, off-1]` (`intrabar_fill.py:212`), but `off-1`
> is merely the array slot for offset `off` — it does **not** shift the rct value back a bar, so the engine rests
> `rct[di]` during `di`. The off-by-one is worth **~+0.25 ATR/trade** (booked-lookahead `rct[di]` gross +0.20 vs
> causal `rct[di-1]` −0.05); **causalized (`rct[di-1]`), the bare RSI-2 fade + EXIT-RCT is net-negative even
> gross.** It surfaced only on porting to cTrader (XRSI-V1) + forward-testing, because native execution can rest
> a limit no earlier than `rct[di-1]`. A secondary, compounding cBot-port-only defect (the REAL stream also
> omitted the binding v2 0.05·ATR entry slippage the research charges) reinforced the negative result but is not
> the research-level cause.
>
> **Scope.** EXP-091/092/094 (screen/sequence), **EXP-093 `TEST_CONFIRMED`** (11 counted TEST reads),
> EXP-095/096 (portfolio + v2 fill), **EXP-097 `DEPLOYABLE_CONFIRMED`** (the global-holdout shot), and EXP-098
> robustness — all **net-tradable / deployment claims REFUTED**. **EXP-089 availability / G-020 ADMITTED stands**
> (gross `MFE_med`, no RCT limit): the fade's favourable *availability* is real; it is not net-*capturable* live.
> HYP-002/HYP-003 close REFUTED; HYP-001 (availability) stands.
>
> **Governance.** Family **CLOSED — REFUTED**, not reopenable by re-parameterization. The 11 EXP-093 counted TEST
> reads (strata stay 1/2) and the EXP-097 global-holdout shot stay **SPENT — spent-on-defect** (a discovered
> defect does not refund a read/shot); recorded in `test-read-ledger.md` + `multiplicity-registry.md` (Phase
> 021/022 banners) + `candidate-families/cf-mr-001.md` §CLOSURE. **G-021 TRADABLE and G-022 DEPLOYABLE_CONFIRMED
> RETRACTED** (checkpoint gate reviews + retrospectives superseded). All cards below are **retained, not deleted**.
> Live-backtest observations (native-fill behaviour, slow-domain cost geometry) may seed a **new family** under
> its own D0 — only after a pipeline fix that causalizes the EXIT-RCT limit — out of scope here.
>
> *Everything below this banner is the prior (now superseded) DEPLOYABLE record, retained verbatim.*

**[SUPERSEDED — see §CLOSURE]** The bare RSI-2 fade, deployed as the G-022a-frozen carry-8 causal ERC portfolio (binding-v2 fill,
intra-1h MTM, circuit breaker, primary Portfolio B), confirms on the final-30% global holdout (B Sharpe LB 4.762 >
band 2.00, Calmar LB 10.731 > 0) — the **programme's first deployment-grade price strategy**. (EXP-089
`SCREEN_DELIVERED`, 2026-06-23, amended `D0-amendment-001`; G-020 ADMITTED.) First candidate family opened
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
| EXP-096 | `CF-MR-001/HYP-003` | Noise Infusion — Realistic 1-Minute Entry Fill (8 G-021-confirmed cells; v1/v2-binding/v3 entry-fill ladder; pure entry-leg perturbation on the EXP-095 ERC construction; analysis-set, NO holdout verdict) | **COMPLETED 2026-06-25 — fill-realism leg SURVIVES at binding v2; circuit-breaker NEUTRAL at v2 / TAIL-PROTECTIVE at v3; statistic clearable under noise (audit PASS 0C/0W/5I).** | Under the binding realistic fill (v2 = next-1m-open + 0.05×ATR adverse slippage, intra-1h MTM) the EXP-095 diversification benefit **SURVIVES**: A v2 Sharpe 6.50 (MBB LB **5.147**) / B 6.29 (LB 4.90) / naive-IV 6.44 (LB 5.09). Benefit (like-for-like LB vs cross-cell-median single-cell LB **2.554**): A **+2.59 > sampling band 1.35 = ADDS_VALUE**; co-binding Calmar LB +4.28; **broad-based** (all 8 per-cell v2 Sharpe LBs positive 0.13–3.65; portfolio LB > best cell — no broken cell masked); ERC ≈ naive-IV. **Mechanism:** v1 latency-neutral (mean entry gap ≈0; v1 A LB 10.31 ≈ idealized 10.28) + a flat 0.05×ATR tick subtracting an **EXACT −0.05 ATR/event uniformly** → halves BOTH the portfolio LB AND the baseline → relative margin preserved (keep mask byte-identical to EXP-093; not variance hiding). **Ladder (A Sharpe LB):** ideal 10.28 → v1 10.31 → v2 5.15 → v3 **−1.65** (A BREAKS, MaxDD 40.9%); **v3 B +1.83 (MaxDD 6.0%)** — v3 is a deliberately harsh STRESS CEILING (worst-of-3-1m absolute; disclosure-only, NOT deployment failure). **A-vs-B (G-022a input):** breaker NEUTRAL at binding v2 (A≈B: d Sharpe LB +0.25, d MaxDD +0.0013; reproduces EXP-095) but large TAIL-INSURANCE at v3 (de-allocates fragile 1h cells USTEC 26.1%/US2000 21.7% of steps, prevents 40.9%→6.0% MaxDD) — real edge-decay-threshold effect (dormant at v2 when no cell's trailing-50 mean<0; active at v3) → argues for Portfolio **B**. **Gate re-check (inherited m*, NOT recomputed):** v2 A LB 5.15 ≥ m* 1.75 (+3.40); B LB 4.90 ≥ m* 2.00 (+2.90) → `statistic_clearable_under_noise=true` → G-022a band ≥ m*. **EURJPY-4h flagged NOISE_DEGRADED** (v2 net ci_low 0.0079 < 0.025 margin) but net-positive, **RETAINED** (operator portfolio-only membership; G-022a decides set); GBPJPY-4h next-weakest (0.0278, just clears). Integrity: provenance abs_diff 0.0 vs EXP-093 all 8; MTM conservation ≤1.4e-14; determinism/causal-fill/causal-weight PASS; ideal variant reproduces EXP-095 A Sharpe point **11.691 exactly**; 0 counted TEST reads, 0 slots, holdout untouched (11 carried strata stay 1/2). Next: G-022a freeze (band ≥ m*; A-vs-B leans B; decide EURJPY-4h carry) → EXP-097 global-holdout release. |
| EXP-093 | `CF-MR-001/HYP-002` | **One-Shot TEST Confirmation** (EXIT-RCT on all 11 EXP-092 SEQUENCE_PASS cells; analysis-TEST stratum; Holm-11; `D0-amendment-006`) | **`TEST_CONFIRMED` 2026-06-24 — HYP-002 tradability SUPPORTED → routes G-021 TRADABLE** | **8/11 cells CONFIRM** (`Holm-adj p=0.0011 ∧ net ci_low_1s > margin`) across **7 instruments, both domains** — the **programme's first net-positive out-of-sample price entry.** **Robust core = six 4h cells mean-AND-median positive** (net_ci_low 0.039–0.094 vs 0.025: EURUSD +0.094 / XAUUSD +0.072 / USDCHF +0.062 / AUDJPY +0.057 / EURJPY +0.044 / GBPJPY +0.039) + **two mean-carried 1h** (US2000-1h +0.073, USTEC-1h +0.046; USTEC TEST median −0.026). Non-confirm: **GBPUSD-1h (ci_low −0.103, n=1653) & EURUSD-1h (−0.032) well-powered net-negative — EVIDENCE_AGAINST (OOS reversal)**; NZDUSD-1h near-zero (INCONCLUSIVE). Mechanism: RCT target hit ~99%; 4h nets clear via cost geometry (smaller ATR-cost fraction), not stronger signal; uniform TRAIN→TEST shrinkage (Δ ci_low −0.005…−0.107) — robust core absorbed it, thin 1h tier did not. **11 counted TEST reads spent (each carried stratum 0→1; cap 2/stratum); final-30% global holdout never loaded; 0 slots.** Determinism PASS; numbers reproduced from raw data. Audit PASS (0C/1W non-material re-label/3I). |
| EXP-097 | `CF-MR-001/HYP-003` | **Global-Holdout Release — One-Shot OOS-Final Confirmation** (carry-8; binding-v2 ERC + intra-1h MTM; primary Portfolio B; the single sanctioned final-30% global-holdout shot, à la EXP-032) | **`DEPLOYABLE_CONFIRMED` 2026-06-25 — holdout shot SPENT; audit PASS (0C/0W/4I); post-exec APPROVE** | The G-022a-frozen RSI-2 fade ERC portfolio **CONFIRMS on the global holdout**: primary **B holdout ann Sharpe 6.639 (MBB LB 4.762) > band 2.00** (+2.76, 2.4×) AND co-binding **Calmar LB 10.731 > 0** → `DEPLOYABLE_CONFIRMED`; A co-confirms (Sharpe 6.055, LB 4.250 > 1.75), no OR rescue. n=80 holdout weeks (final 30% per file, 2024-12-13→2026-06-19). **Masking check — broad-based:** 7/8 cells positive holdout net ci_low; the only net-negative cell (EURJPY-4h net mean −0.006, ci_low −0.031) is the **pre-flagged NOISE_DEGRADED** cell and the smallest contributor (dropping it improves the book — no masking). **Mechanism:** high Sharpe is structural (diversified ERC of 8 low-corr cells, vol-anchored 10%; in-family with the analysis-set LB ≈4.9 the band was calibrated against — not a bug); portfolio did **NOT** decay (B LB 4.897→4.762, Δ−0.135) because per-cell decay was heterogeneous (EURUSD/XAUUSD/USDCHF-4h *improved* OOS +0.015…+0.033; JPY/index cells decayed) and the **circuit breaker drove B≫A** (A LB 5.147→4.250, Δ−0.897) by de-allocating fragile 1h cells during weak stretches. Gate matches the effect shape (location + downside). Integrity: headline **re-derived bit-for-bit** from saved series; MTM conservation ≤2.8e-14; determinism/causal-weight/causal-fill PASS (assertions exercised **in the holdout region**); real-price only. **One shot SPENT (non-repeatable, non-upgradable);** holdout-governance event recorded in `test-read-ledger.md` + `multiplicity-registry.md`; counted_test_reads=0, candidate_slots=0 (11 carried strata stay 1/2). **The bare RSI-2 fade is the programme's first deployment-grade price strategy.** |
| EXP-098 | `CF-MR-001/HYP-003` | **Cross-Broker & Aggregation-Method Robustness Replication** (carry-8 frozen portfolio rerun on independent broker PPS data; Arm 1 `PPS-CANON` bucket-boundary agg + Arm 2 `PPS-ALTAGG` last-source-close agg; full PPS timeline; **non-binding disclosure**; `D0-amendment-002`) | **`CROSS_BROKER_ROBUST` ∧ `AGGREGATION_ROBUST` 2026-06-25 — audit PASS (0C/0W/3I); EXP-097 verdict UNCHANGED** | The G-022a-frozen deployment portfolio replicates **verbatim** on an INDEPENDENT broker's data (`data/timebars/pps/`, the 8 carry-8 instruments) and is robust to the bar-aggregation method. **Both arms ROBUST:** primary Portfolio B PPS Sharpe LB **5.97 (CANON) / 6.10 (ALTAGG) > band 2.00**, co-binding Calmar LB **12.5 / 13.3 > 0** (n=251 evaluable weeks; A co-confirms LB 6.15/6.30) → rules out **broker-feed overfit** (Arm 1) AND **aggregation-method overfit** (Arm 1 vs 2). **Broad-based, no masking:** all **8/8 cells net-positive on both arms** (PPS net ci_low +0.0105…+0.0941); **EURJPY-4h** (net-negative −0.006 on the INFR-003 holdout) **recovers to +0.026**; drop-one masking (removes largest contributor US2000-1h) still confirms B (LB 5.48/5.57, no flip). **Aggregation near-inert:** domain-bar counts identical across arms except USTEC-1h/US2000-1h (±1 trailing bar); 4h per-cell nets identical to ~1e-5 — the last-source-close relabel can only move the trailing/incomplete window. **Mechanism:** the cost-geometry edge is **price-structural, not feed-specific** (per-cell nets within ~10–25% of INFR-003); ~7 Sharpe is structural diversification (in-family with EXP-097's ~4.9 LBs). **Retention caveat:** PPS full-timeline (n=251 wk) vs INFR-003 holdout (n=80 wk) ratio ≈1.25–1.45 reads as "confirms at least as strongly," not "stronger" (different slices). Integrity: MTM conservation ≤2.8e-14; determinism + causal-weight/fill PASS in the evaluable region; real-price only; **INFR-003 holdout NEVER loaded** (`infr003_holdout_loaded=false`). **0 candidate slots / 0 counted TEST reads** (PPS outside the analysis-TEST 48-stratum ledger AND the INFR-003 holdout; robustness governance disclosure; 11 carried strata stay 1/2). **EXP-097 `DEPLOYABLE_CONFIRMED` UNCHANGED — strengthening companion, non-upgradable;** PPS now "touched" as a robustness dataset (future binding use needs its own governance). |

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

### EXP-096 — detailed card (`CF-MR-001/HYP-003`)

**Status**: COMPLETED 2026-06-25 (analysis-set only — NO holdout verdict) · **Phase**: 022 (batch 3) · **Audit**: PASS (0C/0W/5I; full verdict forensics — per-cell masking, mechanism, gate-shape)
**Instruments**: 8 G-021-confirmed cells (EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/GBPJPY-4h + USTEC-1h + US2000-1h)
**Data Views / Feature Categories**: EXIT-RCT net per-event return streams (ATR units) reused verbatim from the EXP-090/093 substrate with intra-1h MTM (amendment-001 A1); the **entry execution price** re-resolved from real 1-minute bars under the v1/v2(binding)/v3 fill ladder (new `xen.intrabar_fill.resolve_entry_fills`); analysis set (TRAIN + EXP-093 analysis-TEST series as portfolio-aggregate disclosure); causal 1h common grid.

#### Hypothesis Tests

1. **Hypothesis (`HYP-003`, fill-realism leg):** under a realistic 1-minute entry fill (binding v2 = next-1m-open + 0.05×ATR adverse slippage), the portfolio annualized-Sharpe lower bound (co-binding Calmar LB) still clears the deployment-realistic cross-cell-median single-cell LB by more than its sampling band — the in-sample diversification benefit survives execution.
   - Sub-reads: which cells (if any) realistic execution breaks (per-cell disclosure); does the inherited gate m\* remain clearable under noise; does the circuit-breaker (B) change the EXP-095 "neutral" read under noise.

#### Scope

- **Instruments**: the 8 deployable cells (no instrument/domain outside the set).
- **Noise model (frozen, D0 §D5)**: v1 next-1m-open (mild floor); **v2 = v1 + 0.05×ATR adverse slippage (BINDING)**; v3 = worst touched price over the next k=3 1m bars (stress ceiling). Only the entry execution price changes; exit target/stop/cost frozen; cost notional pinned to the signal close (not double-counted). Pure entry-leg perturbation: exit path + keep mask reused verbatim from EXP-093.
- **Construction**: the EXP-095 frozen ERC build reused verbatim (Ledoit-Wolf 90d covariance, weekly rebalance, 10% vol anchor, 1.5× cap, trailing-50 breaker, intra-1h MTM); both A (static) and B (breaker). m\* **inherited** from EXP-095 (A4 MDE not recomputed under noise — operator decision). Membership **portfolio-only** (operator 2026-06-25): all 8 retained, per-cell flags disclosure-only.
- **Exclusions**: final-30% global holdout never loaded; G-022a freeze + EXP-097 release; any exit re-resolution or hyperparameter/variant selection from brackets (v2 binding; v1/v3 + cov-window {60,90,120} disclosure-only).
- **Constraints**: causal everywhere (entry fill consults only 1m bars in `(signal_close, train_edge]`); timestamp alignment (`CloseTime`), never bar index; real-price outcomes; 0 candidate slots, 0 counted TEST reads.

#### Results / Observations

- Binding **v2** portfolio: A ann Sharpe **6.496** (MBB lo **5.147**), MaxDD 0.0625, Calmar 10.05 (lo 7.02), CVaR₅ 0.0140, Ulcer 0.0120, n_weeks 185; B Sharpe 6.287 (lo 4.897), MaxDD 0.0612, Calmar 11.25 (lo 6.83); naive-IV Sharpe 6.441 (lo 5.089).
- Benefit (binding, like-for-like LB-vs-LB, baseline = cross-cell-median single-cell LB **2.554**): A Sharpe margin **+2.59** (band 1.35) ADDS_VALUE; B +2.34 (band 1.39) ADDS_VALUE; co-binding A Calmar LB +4.28 (band 3.03) ADDS_VALUE. Disclosed: A vs ex-post-best-cell LB (3.652) +1.69; A LB 5.147 ≈ naive-IV LB 5.089 (ERC ≈ naive-IV).
- Per-cell v2 single-cell Sharpe LBs (all positive): EURUSD-4h 3.652, US2000-1h 3.461, USTEC-1h 2.874, USDCHF-4h 2.633, AUDJPY-4h 2.476, XAUUSD-4h 1.811, GBPJPY-4h 1.173, EURJPY-4h **0.130**. Median 2.554; portfolio LB (5.147) > best single cell.
- Per-cell net per-event mean: `v2 = v1 − 0.05000` exactly all 8 cells (v1 ≈ ideal; v1 mean entry gap ≈ 0; v2 entry gap = 0.049–0.050 ATR). v2 net `ci_low_1s`: 7/8 clear the EXP-093 margin; **EURJPY-4h 0.0079 < 0.025 → NOISE_DEGRADED (flagged, retained, still net-positive)**; GBPJPY-4h 0.0278 just clears.
- Noise ladder (A Sharpe LB): ideal **10.281** → v1 **10.305** → v2 **5.147** → v3 **−1.651** (A MaxDD 0.409, Ulcer 0.188). v3 B Sharpe LB **+1.826** (MaxDD 0.060). v3 entry gap ≈ 0.15 ATR on the 1h cells vs ≈ 0.05–0.075 on the 4h cells.
- Gate re-check (inherited m\*): v2 A LB 5.147 ≥ 1.75 (edge +3.40); v2 B LB 4.897 ≥ 2.00 (edge +2.90); `statistic_clearable_under_noise=true`.
- Adaptability v2: d(Sharpe LB) A−B +0.250, d(MaxDD) +0.0013, d(Ulcer) −0.0012 (within sampling-band overlap → neutral at v2). Fragile-cell de-allocation: USTEC-1h 26.1%, US2000-1h 21.7% of grid steps.
- cov-window bracket (disclosure): v2 A Sharpe 6.554/6.496/6.460 at 60/90/120-day (spread 0.09).
- Integrity: provenance abs_diff 0.0 vs EXP-093 (8/8, counts match); MTM conservation Σ(marks)=net(v2) ≤1.4e-14; determinism byte-identical (A & B); causal-fill (pre-signal perturbation inert) + causal-weight PASS; `n_entry_unavailable_on_keep=0`; ideal variant reproduces EXP-095 A Sharpe point 11.691 exactly; `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`.

> Note: No interpretation — preserve what the data shows.

#### Hypothesis-Specific Conclusion

**SURVIVES (analysis-set; no holdout verdict).** Per the pre-registered SURVIVES/WITHIN-NOISE/BREAKS rule, the binding v2 read is SURVIVES: ≥1 of A/B has a v2 Sharpe LB clearing the cross-cell-median baseline by more than the sampling band (A +2.59 vs band 1.35), co-binding on Calmar LB, broad-based across all eight cells, and clearing the inherited m\*. The realistic fill is latency-neutral plus a flat 0.05-ATR tick that hits all cells uniformly, so the edge halves in level but the relative diversification margin survives. **Scale caveat:** Sharpe ~6–12 in-sample favorable-selected — read the survival/relative gap, not the level; binding read = EXP-097.

#### Hypothesis-Agnostic Observations

- **The circuit-breaker is free insurance, not dead weight:** neutral at the binding v2 (A≈B, reproducing EXP-095) but it prevents a 40.9%→6.0% MaxDD blow-up at the v3 stress ceiling by de-allocating the fragile 1h cells — a real edge-decay-threshold effect (dormant until a cell's trailing mean flips negative). This sharpens the G-022a A-vs-B decision toward Portfolio B, reversing the "breaker adds nothing" reading EXP-095 (noise-free, no stress probe) implied.
- **Realistic 1-minute fill cost scales with domain speed:** the v3 worst-of-3-minute entry penalty is ≈3× larger relative to ATR on the 1h cells than the 4h cells, so execution fragility concentrates in the fast (1h) tier — the same tier whose median was already fragile at G-021.
- **A uniform per-event cost shift preserves relative portfolio benefit:** because the v2 slippage subtracts an identical −0.05 ATR/event across cells, both the portfolio and the cross-cell-median baseline degrade in lockstep — diversification benefit is robust to a flat execution cost, fragile only to a domain-asymmetric one (v3).

### EXP-097 — detailed card (`CF-MR-001/HYP-003`)

#### Hypothesis Tests

- **Binding (1):** deployed as the G-022a-frozen, noise-aware (binding-v2) causal ERC portfolio with intra-1h MTM, does the primary **Portfolio B** confirm on the final-30% global holdout — `Sharpe_LB(B) > 2.00 AND Calmar_LB(B) > 0`? Portfolio A co-adjudicated on the same single materialization (one read), disclosed, **no OR rescue**.
- The single sanctioned global-holdout shot (à la EXP-032); mechanical against the pre-frozen G-022 rubric; non-repeatable, non-upgradable.

#### Scope

- **Set/construction (frozen at G-022a):** carry-8 cells; binding-v2 ERC + intra-1h MTM (LW-90d covariance, weekly rebalance, 10% vol anchor, 1.5× cap, trailing-50 breaker); primary B; bands A 1.75 / B 2.00 (= inherited A4 m\*); rule `CONFIRM(P) iff Sharpe_LB > band_P AND Calmar_LB > 0`; master seed 20260624.
- **Binding slice:** the final-30% global holdout per file, loaded for the first time; analysis set loaded as past-only causal warmup (EXP-093 pattern); binding metric restricted to the holdout region `grid_epoch ≥ H` (H = max per-cell cutoff = 2024-12-13), excluding the ~2-day transition zone.
- **Exclusions:** any re-derivation/re-tuning/re-selection; the v1/v3 fill variants + covariance-window bracket (EXP-096 ladder); the deferred levers; any second holdout read or verdict upgrade. Real-price outcomes; causal everywhere; alignment by `CloseTime`.

#### Results / Observations

- **Binding (n=80 holdout weeks):** primary **B** ann Sharpe **6.639**, **MBB LB 4.762** > band 2.00 (+2.76, 2.4×); Calmar LB **10.731** > 0; MaxDD 0.046, ann vol 0.114. **A** Sharpe 6.055, LB 4.250 > 1.75; Calmar LB 8.296. naive-IV LB 4.261 (non-binding contrast).
- **Verdict:** `DEPLOYABLE_CONFIRMED` (B confirms; A co-confirms; no OR rescue).
- **Per-cell holdout net (ATR), 7/8 positive ci_low:** EURUSD-4h +0.132 (lo +0.104), XAUUSD-4h +0.115 (+0.082), USDCHF-4h +0.095 (+0.066), AUDJPY-4h +0.064 (+0.040), GBPJPY-4h +0.046 (+0.017), US2000-1h +0.055 (+0.037), USTEC-1h +0.033 (+0.014); **EURJPY-4h −0.006 (lo −0.031), net-negative (pre-flagged NOISE_DEGRADED, smallest contributor).**
- **Shrinkage (analysis-v2 → holdout):** portfolio Sharpe LB B 4.897→4.762 (Δ−0.135), A 5.147→4.250 (Δ−0.897). Per-cell: EURUSD/XAUUSD/USDCHF-4h *improved* (+0.015…+0.033 net mean); JPY crosses/index cells decayed (EURJPY −0.034, USTEC −0.021); rest ~flat.
- **Integrity:** headline re-derived bit-for-bit from saved series; MTM conservation ≤2.8e-14 (8/8); determinism byte-identical; causal-weight (holdout row 37632) + causal-fill (holdout event 1467) assertions PASS; real-price only; holdout region = 30.04% of grid.

> Note: factual observations only — interpretation below.

#### Hypothesis-Specific Conclusion

**`DEPLOYABLE_CONFIRMED` — HYP-003 deployment leg SUPPORTED OOS-final.** The G-022a-frozen RSI-2 fade ERC portfolio confirms on the fully-fresh global holdout by 2.4× on the binding leg with the downside leg holding. The bare RSI-2 fade, deployed as the carry-8 causal ERC portfolio with circuit breaker and binding-v2 entry fill under conservative round-trip cost, is the **programme's first deployment-grade price strategy**; the frozen spec is the production deployment. One shot SPENT.

#### Hypothesis-Agnostic Observations

- **Out-of-sample decay can be heterogeneous, not uniform:** the honest prior expected uniform shrinkage; instead the three strongest 4h FX/commodity cells *improved* OOS-final while the JPY crosses and 1h index cells decayed — the offset is why the diversified portfolio LB barely moved. A portfolio verdict can be far more stable OOS than its constituents.
- **The circuit breaker earned its keep at the portfolio level:** B shrank −0.135 vs A's −0.897 because the breaker de-allocated the fragile 1h cells during their weak stretches — confirming, on genuinely held-back data, the tail-insurance role EXP-096's v3 stress probe predicted and the reason B (not A) was made primary.
- **A pre-flagged weak cell broke exactly as flagged:** EURJPY-4h (NOISE_DEGRADED at G-022a) is the only net-negative cell OOS-final; pre-registration of the flag, plus diversification, kept it from contaminating the verdict.

## Gate

| Gate | Status | Outcome |
| --- | --- | --- |
| G-020 | **ADMITTED — adjudicated 2026-06-23** ([`G-020-gate-review.md`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md); criteria [`G-020-gate-criteria.md`](../../checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-criteria.md)) | **ADMITTED** — `S_fam=28 > S*=7`, axis perm-p≈0.0002 ≤ 0.05 (FWER 0.05, no cross-axis Holm). Lever = **bare RSI-2 fade (CORE)**, intraday; vol-regime inert, variants dead. **CF-MR-001 consumes its first candidate slot.** Next scope (future G0/D0): capture-geometry / exit / cost for the bare fade. 0 counted TEST reads; holdout sealed; ledger unchanged. |
| G-021 | **TRADABLE — ADJUDICATED 2026-06-24** ([`G-021-gate-review.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-review.md); criteria [`G-021-gate-criteria.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-criteria.md); Phase 021 CLOSED, [`retrospective.md`](../../checkpoints/2026-06-23-021-mr-fade-capture-geometry/retrospective.md)) | EXP-093 `TEST_CONFIRMED` — **8/11 carried cells CONFIRM** (`Holm-adj p=0.0011 ∧ ci_low_1s > margin`), six 4h mean-AND-median-positive + USTEC-1h/US2000-1h mean-carried, across 7 instruments and both domains. Per the frozen D6/4c mechanical rule (`TRADABLE iff ≥1 carried cell CONFIRMS`), G-021 **routes TRADABLE** — the bare RSI-2 fade is the **programme's first net-positive OOS price entry.** Non-confirm: GBPUSD-1h/EURUSD-1h EVIDENCE_AGAINST (OOS reversal), NZDUSD-1h INCONCLUSIVE. **11 counted TEST reads spent (each carried stratum 0→1); final-30% global holdout never loaded.** Next (separate gates): a sanctioned global-holdout release decision for the 4h robust core; deferred levers each under their own slot/D0. |
| G-022a | **FREEZE — ADJUDICATED 2026-06-25 (pre-holdout freeze)** ([`G-022a-gate-review.md`](../../checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022a-gate-review.md); criteria [`G-022a-gate-criteria.md`](../../checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022a-gate-criteria.md); terminal rubric [`G-022-gate-criteria.md`](../../checkpoints/2026-06-24-022-portfolio-noise-holdout/G-022-gate-criteria.md)) — Phase 022; EXP-095 + EXP-096 COMPLETE | **All four D0 §D9 preconditions MET → FREEZE.** Frozen: deployable set **carry-8** (EURJPY-4h flagged NOISE_DEGRADED but net-positive → carried; ratifiable trim-to-7); construction = the EXP-095/096 binding-**v2** noise-aware ERC portfolio + intra-1h MTM, verbatim; **A-vs-B — both read on ONE holdout shot (operator decision 2026-06-25), primary = Portfolio B** (B≈A at v2 but tail-insurance at v3 → weakly dominant; chosen pre-holdout, no tuning; A co-reported, no OR rescue); confirmation rule **CONFIRM(P) iff holdout Sharpe_LB > band_P AND Calmar_LB > 0**, band_A **1.75** / band_B **2.00** (= inherited A4 m\*); read accounting = one global-holdout-governance event (à la EXP-032), outside the analysis-TEST ledger (11 carried strata stay 1/2), 0 counted reads / 0 slots, non-repeatable. **→ EXP-097.** Evidence: EXP-096 v2 A LB 5.147 / B 4.897 clear m\* (edge +3.40/+2.90); benefit ADDS_VALUE (A +2.59 > band 1.35); FPR A 0.000/B 0.002; broad-based (all 8 per-cell LBs >0). | Both analysis-set inputs are in. EXP-095 (D0-amendment-001 rerun): portfolio benefit SUPPORTED; gate statistic READY (`statistic_ready_for_g022a=true`; FPR A 0.000/B 0.002; MDE m\*=1.75/2.00 cleared by realized LB 10.24). **EXP-096 (noise infusion) COMPLETE 2026-06-25 — fill-realism leg SURVIVES at the binding v2:** A v2 Sharpe LB 5.147 clears the cross-cell-median baseline (2.554) by +2.59 > band 1.35 (ADDS_VALUE, co-binding Calmar); broad-based (all 8 per-cell LBs positive); v2 A/B LB ≥ inherited m\* (`statistic_clearable_under_noise=true`). G-022a must (i) **freeze the confirmation band ≥ m\*** (≥1.75 A / ≥2.00 B) and adopt the MTM construction; (ii) take the EXP-096 noise-survivor deployable set — **all 8 survive net-positive; EURJPY-4h flagged NOISE_DEGRADED (v2 ci_low 0.0079<0.025) → decide carry-8 vs trim-to-7**; (iii) **decide A vs B** — EXP-096 sharpens this toward **Portfolio B**: neutral at the binding v2 (A≈B) but large tail-insurance at the v3 stress ceiling (prevents a 40.9%→6.0% MaxDD blow-up), so B is ≈free downside insurance. Else HALT (holdout preserved). |
| G-022 | **DEPLOYABLE_CONFIRMED — EXP-097 read 2026-06-25 (terminal; awaits formal Phase 022 retrospective sign-off)** — Phase 022 | EXP-097 spent the single sanctioned global-holdout shot and the frozen rubric resolves **`DEPLOYABLE_CONFIRMED`**: primary **Portfolio B holdout Sharpe LB 4.762 > band 2.00** (+2.76) AND co-binding **Calmar LB 10.731 > 0**; A co-confirms (LB 4.250 > 1.75), no OR rescue. n=80 holdout weeks; broad-based (7/8 cells positive net ci_low; EURJPY-4h net-negative = pre-flagged smallest contributor — no masking); portfolio did not decay (B Δ−0.135 vs A Δ−0.897 — breaker de-allocated fragile 1h cells); high Sharpe structural (diversified ERC, in-family with analysis). One shot SPENT (non-repeatable, non-upgradable; holdout-governance event recorded in `test-read-ledger.md` + `multiplicity-registry.md`); counted_test_reads=0, candidate_slots=0. Audit PASS (0C/0W/4I); pre/post-exec governance APPROVE. **The bare RSI-2 fade is the programme's first deployment-grade price strategy.** |
