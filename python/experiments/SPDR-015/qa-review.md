# SPDR-015 — QA / Compliance review (append-only)

## QA run 1 — 2026-07-24T04:49:48Z — mode: subagent — HEAD d30babfc245b75c193da15cc971ed53a53688f95
Verdict: **REVISE**

Reviewed git state: HEAD `d30babf` (dirty tree; SPDR-015 is untracked `??`). Lane: SPDR
TRAIN-only speed-run (`docs/references/spdr-lane.md`) — no `estimand_validation.json` gate;
integrity substitute = code-asserted fence + causal-lag self-check. Screen + analysis already
COMPLETE; this is pre-disposition QA.

**Headline:** the HARD integrity firewall is fully intact and independently verified (fence,
causal `t-1`, universe pin, shock≠regime, Δ-vs-persistence headline, golden traces G1–G4, all
four binding O3-SOT clauses). No REJECT trigger (no holdout contact, no causality break, no
tradable claim). The REVISE is confined to the **informative tier** — the disposition-bearing
band labels rest on control/CI machinery that deviates from the frozen design, and one emitted
artifact asserts a `DERANGEMENT` it did not perform (L-28). The fresh-context analyst
(`analysis.md` §1, A13, closing caveat) already disclosed the CI/control weakness to the
operator; these fixes bring the code back into design compliance before any WORTH_EXPLORING
routes to graduation.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §0 Band DESIGN primary, CONFIRM verify, TEST/holdout never | config.py:38-43; run_screen.py:97,118-130 | MATCHES (partial) | Origins masked to DESIGN (`in_design`, slot_end<2023-03-01); full TRAIN feeds fit continuity/targets. **CONFIRM "verify" pass not separately emitted** — see Issue 5. |
| §0 Universe Top-25 pin + recompute assert | universe.py:50-102; results/universe_pin_check.json | MATCHES | Recompute == family pin == results pin; `set_equal_all=true`. |
| §0 Clocks: H1 primary, H4 co-report full 2a, D1 R-MARKOV stickiness disclosure only | config.py:57-64; run_screen.py:111-149 | MATCHES | CLOCKS_2A=(H1,H4); D1 only emits `stickiness_disclosure`. |
| §0 SPREAD-COST-DISCLOSURE (UNAVAILABLE_NOT_CHARGED / null / PARTIAL_FEES_FUNDING_ONLY) | config.py:116-125; integrity_selfcheck.json:116-127 | MATCHES | Verbatim; prohibited_claims include tradable/deployable/fully-net/cost-complete. |
| §2.1 R-MARKOV = HIGH iff rv20 ≥ trailing median over warm-up window | features.py:204-210 | MATCHES | `_rolling_median(rv20,w)`, causal (min_periods=w). |
| §2.1 R-HMM-RV = 2-state Gaussian HMM on **rv20 level** (not r), expanding causal fit, forward-filter obs ≤ t | hmm.py:74-176; features.py:220-223 | MATCHES | Baum-Welch on rv20; HIGH=argmax(mu) on level; monthly refit; fit uses x[:a], filter to x[:b]; fit_end idx a-1 < origin a. Golden G1 hand-verifies. |
| §2.1 R-SHOCK = HIGH iff \|r\|≥ expanding p90; **named shock comparator only, never regime** | features.py:212-218; transitions.py:304-305; run_screen.py:214-220 | MATCHES | `_expanding_p90` uses history <t (strict). Rows carry `is_shock_comparator=True`; integrity `shock_not_regime` asserts; excluded from headline; Golden G4 titled "shock flag — NOT regime". |
| §2.2 Targets s_{t+1}, s_{t+k} k∈{4,12}, trans_up/dn, run_len (cap 48) | features.py:256-285; transitions.py (HORIZONS_K); features.py:108-125 | MATCHES | future_state_targets, transition_flags, `_remaining_run_len` censored at 48. |
| §2.3 Frozen predictor list (no zoo): s_t,dur_t,rv20,park_ewma,lvl_pct,n_high_K,shock_t | transitions.py:117-150 | MATCHES | Exactly 8 columns; no extra features. Parkinson EWMA λ=0.94 (config.py:69). |
| §2.4 Forecast methods incl. **mandatory persistence baseline**; empirical P; logistic-ridge monthly WF refit | transitions.py:153-226 | MATCHES | persistence P=1{s_t=HIGH}; empirical expanding conditional; logistic ridge monthly expanding refit (IN-1 initial 40%). |
| §2.5 Headline = **Δ Brier vs persistence** (neg=better); levels + Δ; state gap for level models | transitions.py:259,297-300,308-324; integrity `delta_vs_persistence_emitted` | MATCHES | delta_brier_vs_pers emitted on all non-persistence, non-shock rows (600 rows). state_gap_bps for R-MARKOV/R-HMM-RV only. |
| §2.5 Bands 2a: SUPPORTED = ΔBrier<0 AND CI_hi<0 on powered (n≥80,dates≥30) | transitions.py:266-274 | MATCHES (logic) | Band logic matches; **but CI machinery deviates from design §5 inference — Issue 3.** |
| §2.5 Non-compliance guard: stickiness ≠ transition skill | transitions.py:276-279 (stickiness reported separately); Golden G2 | MATCHES | Persistence Brier = 1−stay hand-verified; skill judged only via Δ. |
| §3.1 ZZ ATR 2.0×ATR(14) Wilder, H1 primary; features at swing k known at confirm | zz_ordinal.py:46-127,434-463 | MATCHES | Wilder ATR; reversal 2.0; confirm_idx≥end_idx asserted (integrity zz_features_le_confirm). |
| §3.2 Targets T-GT-CUR, T-GT-MED K=5 and K=10 (both) | zz_ordinal.py:96(config),228-244 | MATCHES | y_cur, y_med5, y_med10. |
| §3.3 Models AR1-threshold, Ridge-cont, Logit-ridge; WF monthly causal | zz_ordinal.py:249-308 | MATCHES | Expanding train prefix X[:k]; three models. |
| §3.4 Metrics hit/Brier/rank-IC/calibration | zz_ordinal.py:315-354 | MATCHES | present. |
| §3.4 **Bands 2b: SUPPORTED = hit≥base+0.05 AND CI_low>base OR Brier<base with CI_hi<0** | zz_ordinal.py:327-338 | **DEVIATES** | Code drops the **AND CI** requirement — point-estimate only (`band="SUPPORTED" if hit>=base+0.05 or d_brier<-0.005`). Undeclared LOOSER — Issue 2. |
| §4 CONTROL LABEL-SHUFFLE (2a/2b), destroy form DERANGEMENT, fixed-point-free, bite +0.05 plant, collapse fraction | run_screen.py:53-91; controls.json | **DEVIATES** | (a) 2a not run (structural note + eligible count only); (b) 2b uses plain `rng.shuffle` (run_screen.py:77) — **no fixed-point rejection despite artifact labeling `destroy_form: DERANGEMENT`** (L-28); (c) single seed vs 200-seed `DERANGE_SEEDS` declared; (d) no +0.05 bite plant. Issue 1. |
| §4 CONTROL PERSISTENCE-ONLY (Δ table mandatory) | transitions.py:281-306; run_screen.py:360-364 | MATCHES | Δ Brier/logloss/acc vs persistence in every metric row. |
| §4 CONTROL FEATURE-SHIFT (2b): causal lag0 vs +1 lag vs illegal future | zz_ordinal.py:389-431 | MATCHES | ic_causal_lag0 / ic_extra_lag_plus1 (X[k-1]) / ic_illegal_future (X[k+1]). |
| §4 TRIPWIRE TARGET-FUTURE-DESTROY: residual HARD = construction asserts (HMM fit end<origin; ZZ≤confirm) | hmm.py:163-171; zz_ordinal.py:472; integrity hmm_fit_causality/zz_features_le_confirm | MATCHES (HARD part) | HARD residual enforced+checked. Informative derange part = same weakness as Issue 1. |
| §4 HARD: TRAIN fence; max target ts<train_end; universe pin; HMM causality; integrity_selfcheck; O3-SOT | catalog_io.py:90-91; run_screen.py:158-256 | MATCHES | Load-level assert `ts_event.max()<end_ns` (covers every read incl. ZZ/D1); max_ts 1702854000e9 < train_end 1702857600e9. |
| §5 Inference: date-block bootstrap blocks 1/3/7; multi-seed envelope; 2000 resamples | config.py:100-102 (declared) vs transitions.py:329-350 (used) | **DEVIATES** | `_boot_delta_brier` = single 1-day block, single seed=101, n_boot=500. BOOT_BLOCKS/BOOT_SEEDS/2000 declared but unused. Issue 3. |
| §5 Golden traces G1–G4 | golden_traces.py; results/golden_traces.json | MATCHES | All four pass, hand-recompute (see diff below). |
| §5 Artifacts (regime_states/transition_metrics/zz_ordinal/ordinal_metrics/golden/integrity) | run_screen.py:294-382; results/ | MATCHES | All present. |
| §6 Refusals mirrored; no family status change; no XENA | config.py:127-140; integrity role field | MATCHES | prohibited_claims + role="conditioner science only — not standalone trade". |
| §A O3-SOT compliance map (all 8 rows) | design.md:26-36; verified vs O3 source | MATCHES | O3 source exists at pinned path; 4 key clauses verified below. |

### O3-SOT clause verification (BINDING — `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`)

| O3 clause | Requirement | Code evidence | Verdict |
|---|---|---|---|
| §2.1 | HMM refit on rv20 level NOT on r; R-SHOCK named shock, never regime success | hmm.py fits rv20; argmax(mu) on level; R-SHOCK is_shock_comparator flag + G4 title | MATCHES |
| §2.2 | Transition skill measured as Δ vs persistence — raw stickiness alone non-compliant | Headline delta_brier_vs_pers; stickiness reported separately; G2 shows persistence=stickiness ceiling | MATCHES |
| §4 Group 2 | Both 2a and 2b arms in one screen | transitions.py (2a) + zz_ordinal.py (2b) | MATCHES |
| §4/§6 | No tradable/money-primary claim; no family status change | SPREAD-COST-DISCLOSURE + prohibited_claims + role field | MATCHES |

### Golden-trace diff (expected from DESIGN vs implemented)

| Trace | Design expectation | Implemented / emitted | Verdict |
|---|---|---|---|
| G1 BTC R-HMM-RV | fit window ends strictly before origin t; state decode matches hand forward-filter step | fit idx 407, fit_end 1659308400e9 < first_origin 1659312000e9; hand_state 0 == screen_state 0 | PASS |
| G2 ETH persistence | persistence Brier == empirical stay frequency (1−stay) | screen 0.0594296228 vs hand 0.0594296228 (Δ<1e-9); stickiness 0.9406 | PASS |
| G3 SOL T-GT-CUR | y = 1{mag_{k+1}>mag_k} on two consecutive swings; ridge score present | mag_k 537.5, mag_k1 982.2 → hand_y 1.0 == row_y 1.0; ridge_p 0.674 | PASS |
| G4 R-SHOCK | top-decile \|r\| label = hand percentile; NOT titled regime | hand_p90 == screen_p90 (Δ<1e-9); label match; title "shock flag — NOT regime" | PASS |

### Governance & boundary

- **TRAIN fence (HARD):** PASS. Enforced at load (`catalog_io.py:90-91` asserts max ts_event < end_ns for every symbol read, incl. universe/ZZ/D1) + run-level max_ts check. band=TRAIN end=CONFIRM_END everywhere. No TEST/holdout code path.
- **Causal t-1 (HARD):** PASS. HMM fit_end idx a-1 < origin a (golden G1 + 621 fits checked); expanding walk-forward for empirical/logistic/ZZ; ZZ features at confirm≥end; expanding p90 uses history <t.
- **No tradability/deployability claim (HARD):** PASS. Only \|move\| bps readability (state_gap_bps, next_abs_oo) per design §0; prohibited_claims enforced; role = conditioner science.
- **No local accounting primitives:** PASS. No `xen.adjudication`-style booked P&L; metrics are forecast-skill (Brier/hit/IC) + magnitude bps, not a ledger. (SPDR lane uses `screen_code/`; the `check_no_local_accounting` gate is not the SPDR firewall — code-asserted fence substitutes. Manual scan clean.)
- **No Python strategy backtest:** PASS. Vectorised forecast screen; no engine, no fills.
- **Universe pin:** PASS. Recompute == family + results pins.
- **Missing-spread disclosure (chapter 05):** PASS. UNAVAILABLE_NOT_CHARGED / spread_rt_bps null / PARTIAL_FEES_FUNDING_ONLY present; no SpreadBps enters anything.
- **Derangement destroy (L-28):** **FAIL → Issue 1.** LABEL-SHUFFLE artifact declares `destroy_form: DERANGEMENT` but code path is `rng.shuffle(ys)` with no fixed-point rejection; 2a arm not run at all.
- **Seed battery (L-19):** partial. Headline attribution rests on the **analytic** persistence baseline (no random twin needed → HARD seed-battery N/A for the headline). The declared 200-seed derange battery is used as a single draw — Issue 1(c).
- **Dependence-matched CI, block≥H (L-20 / lane):** H1 primary k=1 has H=1 (no overlap); for k≥4 the day-resample block (H1: 24 bars) ≥ H, so the HARD block≥H holds on H1. **But** the design-declared blocks 1/3/7 + 5-seed envelope + 2000 resamples are not implemented (single 1-day block, single seed, 500) and analyst §1 shows the CIs fail to cover the point estimate — Issue 3. (H4 k=12: 1-day = 6 H4 bars < H=12 → under-blocked for that secondary cell; disclosure.)
- **Amendment-direction ledger (L-23):** design §7 AMENDMENT-S1 declared NEUTRAL (0L/0T/1N). But the 2b band CI-drop (Issue 2) is an **undeclared LOOSER** relative to design §3.4 — must be declared or reverted.
- **Holdout:** PASS. No path touches TEST/holdout.
- **DEVIATIONS block:** empty (`DEVIATIONS=[]`); config comment "NONE authorised." The three items in Issues 1–3 are therefore *unauthorised* code-vs-design drift, not signed deviations.
- **XENA VOID / multi-node / one-BacktestNode:** N/A (no engine, no XENA).

### Issues

1. **[REVISE — L-28 derangement + missing 2a coverage] LABEL-SHUFFLE control.**
   - Artifact `results/controls.json` asserts `destroy_form: DERANGEMENT`, but `run_screen.py:77`
     uses `rng.shuffle(ys)` — a plain permutation with ~1 expected fixed point, **no
     fixed-point rejection**. Design §4 requires `DISJOINT: fixed-point-free` / `destroy form:
     DERANGEMENT`.
   - The 2a arm collapse is **not computed** (`run_screen.py:64-66` emits only a structural note +
     eligible-cell count); only 6 BTC 2b groups are shuffled. Design §4 mandates 2a **and** 2b.
   - No `+0.05` bite/MDE plant (design §4 `bite/MDE`); single seed vs declared 200-seed
     `DERANGE_SEEDS` (L-19).
   - **Required change:** regenerate/reject draws until zero fixed points; run the collapse across
     2a transition cells (store per-cell y/p so Brier collapse is computable) and a fuller 2b
     multi-symbol table; add the +0.05 plant; read as a seed-battery percentile.
   - **Route:** `experiment-developer`.

2. **[REVISE — L-23 undeclared LOOSER] 2b SUPPORTED band drops the design-mandated CI leg.**
   - Design §3.4 SUPPORTED = `hit≥base+0.05 AND CI_low>base` OR `Brier<base with CI_hi(Δ)<0`.
     `zz_ordinal.py:327-338` labels SUPPORTED on the point estimate only (`hit>=base+0.05 or
     d_brier<-0.005`), CI dropped (code comment: "stricter CI not always available").
   - **Required change:** either implement the CI clearance (block bootstrap on swing dates) so the
     AND-condition binds, or amend design §3.4 with an explicit LOOSER declaration + updated
     directional count. As-is the 2b SUPPORTED labels are point-estimate stamps.
   - **Route:** `experiment-developer` (implement CI) or `quant-designer` (amend band).

3. **[REVISE — L-20 / design §5 inference] Δ-Brier CI machinery deviates from the frozen plan.**
   - Design §5 + `config.py:100-102` declare blocks 1/3/7, 5-seed envelope, 2000 resamples;
     `transitions.py:329-350` runs a single 1-day block, single seed=101, 500 resamples, `np.isin`
     mask (no multiplicity reweighting). Analyst `analysis.md` §1 independently shows these CIs
     "systematically fail to cover the full-sample point estimate" → many 2a SUPPORTED labels are
     CI-fragile.
   - **Required change:** use `xen.evaluation.block_bootstrap_ci` (or an equivalent block sweep +
     seed envelope with block≥H per clock) and disclose block sensitivity; re-label 2a bands on the
     corrected CI. Until then SUPPORTED must not be read as CI-significant (analyst already says so).
   - **Route:** `experiment-developer`.

4. **[MINOR / note] CONFIRM-band "verify" pass not separately emitted.**
   - Design §0 names CONFIRM `[2023-03-01,2023-12-18)` as a verify slice; the run uses CONFIRM only
     for fit continuity/target lookup and scores origins on DESIGN only. Not integrity-fatal (fence
     holds), but the design's CONFIRM verify read is absent. Note for the operator; amend design or
     add the slice if the verify read is wanted before graduation.

**Disposition-readiness note (operator-facing):** the integrity firewall the SPDR lane exists to
protect is solid and independently re-verified. The REVISE items are all in the informative
tier — control quality and confidence-interval calibration behind the SUPPORTED labels — and the
fresh-context analyst already flagged the same CI/control weakness and told the operator not to
trust the SUPPORTED stamp as CI-significant. Fix the control (derangement + 2a coverage) and the
CI machinery (or amend the bands with a declared direction) before any WORTH_EXPLORING routes to a
full cTrader graduation.

---

## QA run 2 — 2026-07-24T05:28:08Z — mode: subagent — HEAD d30babfc245b75c193da15cc971ed53a53688f95
Verdict: **APPROVE**

Reviewed git state: HEAD `d30babf` (dirty tree; SPDR-015 untracked `??`). Scope: verify the three
QA-run-1 REVISE findings (informative tier) are resolved by the re-run, without regressing the HARD
integrity firewall. Finding 4 (CONFIRM verify slice) is explicitly out of scope and remains an open
MINOR note. Screen was re-run (`results/rerun_stdout.log`: "Done in 456.3s", exit 0; artifacts dated
2026-07-24 06:24).

**Headline:** all three REVISE findings are fixed in code AND confirmed in the regenerated artifacts;
the two new interpretation notes (IN-4, IN-5) are honestly `weakens_clause: False` — they tighten or
fulfil the frozen design, not loosen it; `DEVIATIONS` remains `[]` and these are legitimate notes, not
undeclared LOOSER deviations (L-23). The HARD firewall is intact and independently re-verified.

### Finding-resolution trace

| Finding (run 1) | Fix location | Artifact evidence | Verdict |
|---|---|---|---|
| **1 — LABEL-SHUFFLE mislabeled/incomplete** (plain `rng.shuffle`, 2b-only, single seed, no bite) | `controls.py::label_derange_collapse` uses canonical `xen.xena.controls.make_derangement` (L-28), asserts zero fixed points per seed; 200-seed `DERANGE_SEEDS` read as `collapse_frac` percentile; +0.05 bite plant. Wired 2a `transitions.py:515-527`, 2b `zz_ordinal.py:412-416`; assembled `run_screen.py:54-84`. | `controls.json` LABEL_SHUFFLE: `destroy_form=DERANGEMENT`, `derangement_zero_fixed_points_all=True`, `n_seeds_per_cell=200`, `n_cells_2a=372`, `n_cells_2b=189`, `collapse_frac_median=0.0`, `bite_detected_frac=0.898`. `label_derange_collapse.parquet` (561 rows, both arms, `n_seeds=200`, every `derangement_zero_fixed_points=True`). | **RESOLVED** |
| **2 — 2b SUPPORTED dropped the CI leg** (point-estimate only) | `zz_ordinal.py::_swing_ci_sweep` (canonical `block_bootstrap_ci`, blocks 1/3/7 swings, 5-seed envelope, 2000 resamples); SUPPORTED now `= (hit≥base+0.05 AND hit_ci_lo>base) OR (Δbrier<0 AND Δbrier_ci_hi<0)`. New cols `hit_ci_lo`, `delta_brier_ci_hi`, sweep JSON. | `ordinal_metrics.parquet` carries the CI cols; **0** of 133 SUPPORTED cells violate the AND-CI condition (independently re-checked). | **RESOLVED** |
| **3 — ΔBrier CI machinery deviated from §5** (single block/seed, 500 resamples, failed to cover) | `transitions.py::_delta_brier_ci_sweep` on per-origin `d_i=(p_i-y_i)²-(p0_i-y_i)²` via canonical `block_bootstrap_ci`; day-blocks 1/3/7 → origin-positions (`BARS_PER_DAY`) floored at H=k (block≥H incl. H4 k=12), 5-seed envelope, 2000 resamples; band uses conservative envelope (max ci_hi). | `transition_metrics.parquet` sweep JSON = blocks [1,3,7] → eff_bars [24,72,168] on H1; band reads `delta_brier_ci_hi`; **0** of 389 SUPPORTED rows violate point-AND-ci_hi<0. | **RESOLVED** |

### Interpretation-note honesty (L-23)

- **IN-4** (conservative-envelope band; blocks/seeds/resamples): TIGHTENS. SUPPORTED uses the widest
  interval across the block sweep (2a: max ci_hi<0; 2b: min hit ci_lo>base / max Δ-Brier ci_hi<0), so
  block-fragile inference cannot earn SUPPORTED. Block floored at H=k fixes the run-1 H4 k=12
  under-blocking. `weakens_clause: False` is truthful. This directly implements design §3.4's
  previously-dropped AND-CI, so it FULFILS the frozen band — correctly a note, not a deviation.
- **IN-5** (derangement + bite): STRENGTHENS the control (true L-28 derangement vs prior plain shuffle;
  200-seed percentile vs single draw; adds the §4 bite/MDE non-vacuity plant; both arms vs 2b-only).
  `weakens_clause: False` is truthful.
- `DEVIATIONS=[]` retained (`config.py:142`; `integrity_selfcheck.json` `deviations: []`). Neither note
  loosens design, so no LOOSER declaration is owed; the run-1 L-23 concern (2b band was an *undeclared
  LOOSER*) is discharged by implementing the CI rather than weakening the band. No one-directional
  amendment streak.

### HARD firewall re-verification (no regression)

- `integrity_selfcheck.json` `hard_pass: true`; every HARD check `pass: true`.
- TRAIN-only fence: max_ts `1702854000e9` < train_end `1702857600e9`; `no_test_holdout_contact` pass.
- Causal t-1: `hmm_fit_causality` pass (621 fits, fit_end < first origin); `zz_features_le_confirm`
  pass (confirm_idx ≥ end_idx, 125 sampled).
- Universe pin **recomputed, not skipped**: `set_equal_all: true` vs family pin and results pin.
- `shock_not_regime` pass; `delta_vs_persistence_emitted` pass (600 rows); golden G1–G4 all pass.
- Canonical helpers verified at source: `make_derangement` regenerates on any fixed point (L-28);
  `block_bootstrap_ci` is the INFR-004-hardened circular bootstrap (full circular range, no zero-width
  CI, seed-battery aggregation) — addresses the run-1 root cause (CIs failing to cover the point).

### Issues

None blocking. Residual (carried from run 1, out of scope here):

4. **[MINOR / note — unchanged] CONFIRM-band "verify" pass not separately emitted.** Design §0 names
   CONFIRM `[2023-03-01,2023-12-18)` as a verify slice; the run still uses CONFIRM only for fit
   continuity/target lookup and scores origins on DESIGN. Not integrity-fatal (fence holds). Operator
   may amend the design or add the verify read before graduation.

**Operator-facing note:** The three fixes hold. The control that "shuffles the answers to prove the
model isn't cheating" now does the proper fixed-point-free shuffle over 200 tries on both halves of the
screen, and it can see a small planted edge — so it is trustworthy. The confidence intervals behind
every SUPPORTED label now use the agreed method and take the most cautious bound, so no label is a bare
point estimate. The integrity firewall (no future peeking, no holdout contact, no tradability claim) is
untouched and re-checked. Cleared for the operator's disposition gate. One small open item remains: the
CONFIRM "verify" slice named in the design is still not scored separately — worth settling before any
graduation, but not a blocker here.
