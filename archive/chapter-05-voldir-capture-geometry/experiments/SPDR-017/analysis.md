# SPDR-017 — Analysis (fresh-context binding quantification)

- **Experiment:** SPDR-017 · CF-VOLDIR-001 / HYP-D4 (independent predicted-price mispricing, O3 Group 3b)
- **Lane:** SPDR TRAIN-only screen · vectorised Python · 0 TEST reads · not Nautilus price-primary
- **Object:** M-ZONE band from walk-forward M-RIDGE ŷ (A2 features) → E-TOUCH events → MOMO **and** MR residual characterisation (SPDR-014 grammar)
- **Band:** DESIGN `[2021-06-29, 2023-03-01)` primary; CONFIRM `[2023-03-01, 2023-12-18)` verify
- **Sources re-derived independently** from `results/*.parquet` + `controls.json` via `analysis_code/interrogate.py`; nothing taken from `screen.md` or `screen_code/` outputs.
- **Binding read.** `screen.md` is subordinate. This file re-derives every headline.

**Unit pin (binding).** All effect sizes are **open-to-open return in bps**: `r_h = 1e4·(RealOpen[exit]/RealOpen[entry] − 1)`, side-signed. **No ATR normalisation is applied to `r_h`.** The mispricing band half-width is `σ_bps = max(|ŷ_bps|, Z-VOL σ_bps, 1.0)`, where `Z-VOL σ_bps` = EWMA-Parkinson volatility (**λ=0.94, 60 H1-bar warmup, causal ≤ t−1**) in bps; ŷ = M-RIDGE forecast of the next-H open-to-open return (bps), anchor = `RealOpen[t+1]`. MDE / CI units are bps of `r_h`.

**Partial-cost disclosure (binding).** `spread_cost_status=UNAVAILABLE_NOT_CHARGED` · `cost_scope=PARTIAL_FEES_FUNDING_ONLY` (fee 11 + funding + allowance 2 bps). **`partial_net` overstates full cost.** No fully-net / cost-complete / tradable / deployable claim. No family-status change, no XENA, no TEST/holdout touch.

---

## 1. Integrity gate (Phase 0 — SPDR substitute; blocking items only)

SPDR has no `estimand_validation.json`. Integrity = code-asserted TRAIN fence + causal lag + golden + selfcheck; `r_h` is a **return estimand in bps, not a booked P&L** (no `xen.adjudication` object to reconcile, no local-accounting mimicry — lane §Artifacts exempts the screen).

| Check | Result | Evidence (re-derived) |
|---|---|---|
| Universe pin = family top-25 | **PASS** | `universe_pin_check.json` `set_equal_all=true` |
| TRAIN fence (all exit ≤ train_end) | **PASS** | my recompute: max `exit_ts` = 2023-12-17T20:00Z (post_event) / 2023-12-17 (money) < train_end 2023-12-18 |
| Causal lag t−1 | **PASS** | ŷ/features/Z-VOL lagged; golden G1 ŷ_hand==ŷ_engine (1926.3325918542923, abs_diff 0.0) |
| Golden G1–G4 | **PASS** | `golden_traces.json` all_pass; G2 band floor ok, G3 r_h/label match, G4 A0≠A2 under WEAK-DIR |
| Dependence-matched CI (block ≥ H) | **PASS** | bootstrap aggregates to **per-calendar-day** sufficient stats, resamples day-blocks of {1,3,7} days. Min block 1 day = 24 H1 bars **≥ max post window h=24** and ≥ H=12. Not the block=5 trap; envelope = min/max over blocks×seeds (conservative). |
| Leak tripwire (T1 path-future-destroy) | **PASS (informative)** | 0 positive money survivors above null-p95 across 25 symbols (`controls.json`; `t1_survive=false` all) |
| Holdout untouched | **PASS** | CONFIRM_END == train_end; no query ≥ 2023-12-18 |
| Both MOMO and MR emitted | **PASS** | both labels present on every decided residual |
| Ablation A0/A1/A2 emitted | **PASS** | `ablation.parquet`, 25 symbols × 3 layers |
| No 014 start-gate dependency | **PASS** | ran to completion with 014 residual_status=NONE |

**Phase 0 verdict:** integrity clear → quantification permitted. Integrity `runtime 289.9s`, 25 symbols, 277,509 events, 700,802 post rows.

---

## 2. Question list

| # | Question | §answer |
|---|---|---|
| Q1 | Powered residual ≠ ambient at the primary cell, per stratum? | 3.1 |
| Q2 | Base-conditional: does the mispricing event shift the forward-return distribution vs ambient? | 3.2 |
| Q3 | Model OOS skill (mechanism check — is a mispricing centre even forecastable)? | 3.3 |
| Q4 | Ablation A0/A1/A2 — is DERIVED (error-dynamics) load-bearing; is WEAK-DIR load-bearing? | 3.4 |
| Q5 | Does M-ZONE beat the 014 Z-VOL level baseline? | 3.5 |
| Q6 | Do the destroy controls (time-shuffle / matched-random / feature-shuffle) distinguish live? | 3.6 |
| Q7 | CONFIRM — does it replicate any DESIGN nominal signal? | 3.1 |
| Q8 | Money under partial cost (P-MOMO / P-MR)? | 3.7 |
| Q9 | Is a direction-aware extraction path justified? | 3.8 |

---

## 3. Answers (magnitudes, per stratum)

### 3.1 Primary residual cell — per stratum (Q1, Q7)

Primary cell = **DESIGN · M-ZONE · A2 · M-RIDGE · z=1.5 · H=12 · E-TOUCH · h=12 · P-NONE**. `r_h` bps, side-signed. CI = day-block bootstrap envelope over blocks {1,3,7} days × 5 seeds (my recompute, `an_primary_per_stratum_DESIGN.parquet`).

| Symbol | n | mean | median | std | p_momo | p_mr | CI-env (bps) | MDE | band |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| BTCUSDT | 151 | +0.4 | −17.1 | 182 | .35 | .58 | [−28.8, +30.8] | 42 | UNPOWERED |
| ETHUSDT | 148 | −22.1 | −30.7 | 268 | .41 | .55 | [−68.7, +25.9] | 62 | UNPOWERED |
| SOLUSDT | 168 | +79.2 | −19.7 | 575 | .46 | .51 | [−9.4, +188.9] | 125 | UNPOWERED |
| XRPUSDT | 145 | +17.6 | +13.3 | 269 | .54 | .46 | [−26.3, +61.8] | 63 | UNPOWERED |
| DOGEUSDT | 134 | +5.2 | −15.7 | 463 | .46 | .51 | [−69.5, +90.4] | 114 | UNPOWERED |
| LINKUSDT | 146 | +5.4 | −24.0 | 303 | .47 | .53 | [−51.3, +60.9] | 71 | UNPOWERED |
| ADAUSDT | 162 | −1.8 | −3.3 | 204 | .47 | .49 | [−34.2, +29.9] | 45 | UNPOWERED |
| BNBUSDT | 144 | −25.2 | −19.8 | 250 | .39 | .58 | [−65.8, +17.8] | 60 | UNPOWERED |
| MATICUSDT | 484 | −14.2 | +0.7 | 423 | .50 | .49 | [−56.2, +28.4] | 55 | UNPOWERED |
| GALAUSDT | 143 | **+74.4** | +32.7 | 432 | .52 | .48 | **[+6.1, +159.6]** | 104 | UNPOWERED* |
| OPUSDT | 156 | −51.9 | −53.9 | 422 | .42 | .56 | [−120.1, +14.2] | 96 | UNPOWERED |
| DYDXUSDT | 84 | +62.3 | +52.1 | 529 | .54 | .46 | [−52.8, +179.7] | 163 | UNPOWERED |
| AVAXUSDT | 127 | −9.1 | −10.1 | 322 | .45 | .52 | [−65.3, +49.4] | 80 | UNPOWERED |
| INJUSDT | 73 | −52.1 | −17.4 | 647 | .49 | .51 | [−214.3, +114.6] | 215 | UNPOWERED |
| 1000LUNCUSDT | 74 | +24.6 | −38.4 | 430 | .46 | .54 | [−72.4, +133.0] | 142 | UNPOWERED |
| 1000BONKUSDT | 15 | −2.7 | −45.5 | 351 | .47 | .53 | [−183.2, +187.3] | 257 | UNPOWERED |

9 of 25 listings (ORDI/TIA/BIGTIME/BLUR/1000PEPE/SEI/WLD/PYTH/1000RATS) have 0 DESIGN events (late listings).

**Magnitudes:** mean sign split **8 pos / 8 neg**; median-of-means **−0.7 bps**. **Every stratum MDE = 42–257 bps** against a **≤10 bps** design floor → **15–25× underpowered**; all UNPOWERED (B-5: this is a *power* statement, not a negative).

**\*Lone nominal CI-exclusion:** GALAUSDT DESIGN envelope excludes zero (all three blocks: low +6.1/+8.0/+6.4). Under **16 uncontrolled per-stratum tests at 95%**, ~0.8 false-positives are expected — GALA is consistent with that. It is **not decisive**: MDE 104 ≫ floor, and it **does not replicate** — GALA CONFIRM mean = **−14.4 (sign flip)**.

**CONFIRM (Q7, `an_primary_per_stratum_CONFIRM.parquet`, 17 strata):** exactly one nominal CI-exclusion = **DOGEUSDT** (mean +38.1, env low +9.1, MDE 42). But DOGE **DESIGN** mean was +5.2 with a CI crossing zero → no cross-band replication either. **The two lone nominal clears are different symbols and neither replicates across bands** — the signature of noise, not a residual object.

→ **Q1/Q7: no powered, cross-band-stable residual ≠ ambient at any stratum.** `017_residual_pin.residual_status=NONE` reproduced.

### 3.2 Base-conditional — event vs ambient forward distribution (Q2)

Lane obligation: quantify the mispricing event's **own** effect on the forward-return distribution, independent of profitability. Live = M-ZONE E-TOUCH conditioned; ambient = unconditional band (`UNCOND-BAND` control arm), same z/H/h. Per stratum `an_base_conditional_DESIGN.parquet`; 16 symbols with both arms finite:

| Facet | Median | Mean | Spread / split |
|---|---:|---:|---|
| Δmean `r_h` (live − ambient), bps | **−5.0** | −15.4 | q25 −31.3, q75 +15.4, range [−188.9, +76.9]; **7 pos / 9 neg** |
| Δp_event (event rate) | **−0.044** | — | event fires marginally *less* under model band than uncond |
| Δp_momo (MOMO share) | **+0.012** | — | no MOMO/MR tilt from conditioning |

**Quantified magnitude of the mispricing-context shift = essentially zero** (median −5 bps) with **very large heterogeneity** (265 bps range). There is **no consistent distributional mean shift, dispersion shift, or sign shift** from the event vs ambient. This is a measured wash, reported as a magnitude — not "no effect" asserted: the effect on the forward distribution is ~0 ± tens of bps per symbol, unpowered.

*Population caveat:* the control-arm `live` counts exceed the pinned-cell decided counts (e.g. BTC 254 vs 151) because the control's summariser counts all finite-`r_h` posts incl. `side==0`, whereas the pinned cell requires `side≠0`. Base-conditional deltas are therefore **directional on a slightly broader post set**, not the identical population — immaterial given everything is unpowered.

### 3.3 Model OOS skill (Q3 — mechanism)

DESIGN · M-RIDGE · A2 · H=12; my recompute `IC(ŷ, realised H-bar OO return)`, `an` script:

| | Rank IC (Spearman) | Linear IC (Pearson) | MAE bps |
|---|---:|---:|---:|
| median (16 symbols, n≥50) | **−0.008** | **−0.032** | ~290 |
| range | −0.085 (AVAX) … +0.085 (LUNC) | −0.065 (AVAX) … +0.079 (BNB) | 199–617 |

Pearson IC **reproduces `screen.md` exactly** (BNB +0.079, SOL −0.046, MATIC −0.042). Rank IC adds robustness: **also ≈0**. ŷ carries **no OOS return skill**. Consequence: when |ŷ| is small/noisy the band collapses to `max(Z-VOL σ, 1.0)` → M-ZONE ≈ Z-VOL. The mechanism ("a forecastable mispricing centre") is **not present** in the ridge head.

### 3.4 Ablation — DERIVED and WEAK-DIR load-bearing (Q4)

Cross-symbol `mean_r_h` at the primary cell (`ablation.parquet`, 16 symbols with data):

| Layer | Features | median | mean | vs prior layer |
|---|---|---:|---:|---|
| A0 | PROVEN | +1.1 | −13.1 | — |
| A1 | + DERIVED (error dynamics) | −5.5 | −19.3 | **A1−A0 median −5.8 bps; only 31% of symbols improve** |
| A2 | + WEAK-DIR | −0.7 | +5.6 | A2−A1 median +7.1 bps; 56% improve |

- **DERIVED layer (the core of original-#3) is inert / mildly harmful:** A1 does not lift A0 (median −5.8, 5/16 improve). The error-dynamics features the experiment was built to test add nothing.
- **WEAK-DIR is load-bearing — CONFIRMED independently:** A2 is the **only** layer with a positive cross-symbol *mean*, and the A2 mean advantage is entirely on the WEAK-DIR increment. But the advantage is **mean-only** (A2 median still ≈0), **heterogeneous** (SOL A2 +79 vs A1 +19; GALA +74 vs +36; **ETH A2 −22 vs A1 +32 — WEAK-DIR hurts ETH**), unpowered, and driven by a few symbols. `weak_dir_load_bearing_flag=true` is verified. Per design §2.5 this is **disclosed, not a silent signed-product revival** — WEAK-DIR stays inputs-only; there is no powered signed edge here.

### 3.5 vs 014 Z-VOL baseline (Q5)

`vs_014_baseline.parquet`, informative (not a start gate):

| Scope | median Δ (M-ZONE − Z-VOL) | frac M-ZONE > Z-VOL |
|---|---:|---:|
| primary cell (z1.5·H12·h12·E-TOUCH), 16 symbols | **−3.0 bps** | 5/16 (31%) |
| all matched cells (144 rows) | −1.6 bps | 46.5% |

Z-VOL also fires **more events** (median 188 vs 144). The independent mispricing zone **does not beat the dumb magnitude zone** — it is marginally worse at the primary cell.

### 3.6 Destroy-control indistinguishability (Q6 — strongest AGAINST)

Per-symbol live-mean **percentile within its own null** under three destroys (200 seeds time-shuffle & matched-random; 50 seeds feature-shuffle), 16 symbols:

- Percentiles scatter across the whole [0.05, 1.0] range with **no concentration** (e.g. OP 0.06 / XRP 0.08 low; AVAX ~1.0 / MATIC ~0.93 high) — the live mean is **not systematically above** its nulls.
- The three destroys are **near-identical per symbol**: corr(time-shuffle, matched-random)=**0.985**, (ts, feat-shuffle)=0.88, (mr, fs)=0.90; mean |ts−mr| = **0.04**. Destroying **event timing**, the **anchor**, or the **model ŷ** each leaves the live mean at the **same** percentile.

→ The mispricing model contributes **no information beyond each symbol's ambient forward-return drift**. Where the live mean sits high (AVAX, MATIC, ETH) it sits equally high under feature-shuffle → attributable to that symbol's directional drift, not to the model/event.

### 3.7 Money under partial cost (Q8)

`money_episodes.parquet`, DESIGN P-MOMO/P-MR · primary money cell:

| Policy | median symbol mean_net | median symbol median_net | median mean_gross | symbols mean_net > 0 |
|---|---:|---:|---:|---:|
| P-MOMO | **−14.3** | −79.2 | −0.2 | 5/16 |
| P-MR | **−9.9** | −65.4 | +4.2 | 4/16 |

Even **gross** (pre fees/funding) is a wash (median ≈0). After partial cost, negative on mean and deeply negative on median. Spread uncharged ⇒ true economics worse. **No tradability claim.** T1 path-destroy: 0 positive survivors.

### 3.8 Direction-aware path (Q9)

No powered MOMO or MR residual (3.1), no distributional shift (3.2), rate lean `MIXED_SUGGESTIVE` (8 MOMO- vs 10 MR-class labels, disclosure-only), gross money ≈0 (3.7). **A direction-aware extraction path is not justified** from this screen.

---

## 4. Evidence FOR the hypothesis

1. **Path is implementable and legal without a 014 residual** — integrity clean; O3 Group 3b satisfied; full MOMO+MR grammar emitted on both bands.
2. **Some strata carry large raw means** — SOL +79, GALA +74, DYDX +62 (DESIGN H=12) — magnitude exists in the tails.
3. **GALA (DESIGN) and DOGE (CONFIRM)** each produce a nominal CI-exclusion of zero at the primary cell — but see §Against #2.
4. **WEAK-DIR features do move the cross-symbol mean** (A2 mean +5.6 vs A1 −19.3) — a measurable, disclosed layer contribution.
5. **CONFIRM does not systematically invert DESIGN** into a coherent opposite residual.

## 5. Evidence AGAINST the hypothesis

1. **Model OOS IC ≈ 0** (rank −0.008, linear −0.032) — no forecast skill; the mispricing centre is not forecastable. *(Powered mechanism read, not a per-stratum power statement.)*
2. **The two nominal CI-clears do not replicate** — GALA +74 (DESIGN) → −14 (CONFIRM, sign flip); DOGE +5 (DESIGN, crosses) → +38 (CONFIRM). Different symbols, no cross-band stability → noise-consistent (~0.8 false-positives expected across 16 tests).
3. **DERIVED error-dynamics layer is inert** — A1 fails to lift A0 (median −5.8 bps; 5/16 improve). The experiment's core feature layer adds nothing.
4. **Three destroy controls are indistinguishable** (corr ts–mr 0.985) — the event carries no information beyond ambient drift.
5. **M-ZONE ≤ Z-VOL baseline** (primary Δ −3.0 bps; 5/16 beat it).
6. **Base-conditional shift ≈ 0** (median −5 bps, 7+/9−) — no distributional effect from the event.
7. **All primary strata UNPOWERED** — MDE 42–257 vs ≤10 floor; no residual object can be established either way.
8. **Money gross ≈ 0, partial_net negative** on mean and median.
9. **WEAK-DIR "lift" is mean-only, heterogeneous** (hurts ETH), unpowered — load-bearing disclosure, not an edge.

## 6. Anomalies & open questions

- **Control-arm vs pinned-cell population mismatch** (BTC 254 vs 151, etc.): control summariser counts all finite-`r_h` posts incl `side==0`; pinned cell requires `side≠0`. Base-conditional deltas are directional, not identical-population. Same class as SPDR-014's control-walk-vs-cell pattern. Does not affect the pin (cell rows). *Probe if pushed:* recompute the uncond control on the exact `side≠0` decided set.
- **9/25 listings have 0 DESIGN events** (late-listed) — AMENDMENT-S1 per-symbol OK, multi-symbol credibility thin; the "credible" strata are the ~12–16 liquid ones.
- **SOL / GALA large positive means with negative/near-zero medians** → tail-driven, not central tendency.
- **M-GBM deviation** (DEV-1): pure-numpy tree ensemble (sklearn absent), sensitivity only; ridge is primary throughout — does not affect the read.

---

## 7. Recommended disposition (operator decides — NOT final, NOT family)

**Per-stratum (direct residual ≠ ambient test):** every stratum is **UNPOWERED → INCONCLUSIVE** (B-5 — cannot be booked as a negative). GALA (DESIGN) and DOGE (CONFIRM) are lone, non-replicated nominal CI-clears → still INCONCLUSIVE, noise-consistent.

**Screen/graduation recommendation: `NOT_WORTH`.** This does **not** rest on the (unpowered) per-stratum residual test; it rests on **apparatus/mechanism facets that are decisive on their own**:

| Driver | Read |
|---|---|
| Model OOS IC ≈ 0 (rank & linear) | the forecastable mispricing centre the mechanism needs is absent |
| DERIVED (error-dynamics) A1 fails to lift A0 | the experiment's core feature layer is inert |
| 3 destroy controls indistinguishable (corr 0.985) | the event adds no information over ambient drift |
| M-ZONE ≤ Z-VOL baseline | independent mispricing doesn't beat the dumb magnitude zone |

**WEAK-DIR load-bearing status:** CONFIRMED — any A2 mean advantage is carried entirely by WEAK-DIR features (not by error-dynamics); it is mean-only, heterogeneous, unpowered, and disclosed as **inputs-only, not a signed-product revival**.

**Would change if:** a redesigned head showed OOS IC materially > 0 on a single liquid stratum with a pre-declared power plan (n large enough for MDE ≤ 10), *and* the effect survived the matched-random/feature-shuffle destroys distinguishably. Not supported by the current apparatus.

**Caveat (B-5, binding):** `NOT_WORTH` = "no availability worth graduating", grounded in mechanism reads — **not** a claim that any per-stratum residual is a proven zero (they are UNPOWERED). Partial cost only (spread uncharged); any positive raw `r_h` is not cost-complete.

**Scope:** does not change family status (CF-VOLDIR-001 stays REGISTERED — checkpoint retrospective only); no XENA; SPDR-016 remains the separate 014-gated refine path; `017_residual_pin` is not consumed by 016.

---

## 8. Hand-off

Final disposition is the **operator's**. My independent re-derivation reproduces the screen's `residual_status=NONE`, weak IC, and "M-ZONE does not beat Z-VOL", and adds three findings the screen did not surface: (a) the two nominal CI-clears **do not cross-replicate** across bands; (b) the base-conditional distributional shift is **~0 (median −5 bps), not a positive quantification**; (c) the three destroy controls are **indistinguishable** (event carries no incremental information).

**Suggested probes only if the operator chooses to amend (new EXP/SPDR ID, not a silent rescope):**
1. Diagnose *why* ridge IC is null on proven features before building any zone on top of ŷ.
2. Try a non-return event definition (path-residual head) rather than a return-bps band.
3. Focus one liquid stratum with an explicit power plan (target MDE ≤ 10), not a 6000-cell grid re-run.

**Artifacts (mine):** `analysis_code/interrogate.py`; `results/an_primary_per_stratum_DESIGN.parquet`, `an_primary_per_stratum_CONFIRM.parquet`, `an_base_conditional_DESIGN.parquet`. **Screen:** `results/017_residual_pin.json`, `ablation.parquet`, `vs_014_baseline.parquet`, `model_oos.parquet`, `controls.json`, `integrity_selfcheck.json`.
