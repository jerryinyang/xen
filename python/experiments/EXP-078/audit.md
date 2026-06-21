# Audit Report: Experiment EXP-078

**Title:** `ASS`/VAL-003 — Shape Discrimination + `k`-Sensitivity (Phase 017, last experiment before terminal G-017)
**Auditor:** experiment-auditor (research-pipeline Stage 5)
**Date:** 2026-06-21
**Artifacts audited:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/ass.py` (shape extension), `results/` (verdict.json, integrity.json, shape_rates.csv, shape_skew.csv, k_sensitivity.csv, k_sensitivity_shrinkage.csv)

## Summary

- **Verdict (trust): PASS** — the implementation is faithful and the experiment's **substantive double-FAIL** result is **genuine**, not contaminated by any verdict-material defect. The FAIL feeds G-017 `DISCOVERY_ONLY` (per the pre-registered interpretation guide).
- **Critical Issues**: 0 (no rerun required — the FAIL is implementation-faithful; verified below)
- **Warnings**: 2
- **Info Notes**: 4

The experiment verdict (`results/verdict.json`): `shape_discrimination` = **FAIL** on both binding legs; `k_sensitivity` = **ROUTING_FLIP**. I independently reproduced the binding numbers and confirmed each FAIL is a genuine property of the **frozen** diagnostic, not a bug.

---

## Independent re-derivation (anti-spurious-FAIL check)

Run with a clean-room reimplementation (NOT the experiment script) of the DGPs + diagnostic. Results matched the experiment to MC noise, confirming the registry tuple-unpacking, gap formula, MAD scale, and dip-test usage are all correct.

**Mixture parameterization (rules out a `for label, tid, w, mu1, s1, mu2, s2 in bis` unpacking bug):** closed-form means reproduced to 1e-4 —

| type | recomputed mean | truth (`w·μ1+(1−w)·μ2`) | true large-n \|g\| | gap_flag (>0.30) | dip_p @ n=8000 | dip_flag rate |
|------|-----------------|------------------------|--------------------|------------------|----------------|---------------|
| B_neg | −0.1724 | −0.1725 | **0.503** | **True** | 0.12 (med) | 0.30 |
| B_zero | −0.0150 | −0.0150 | **0.250** | **False** | 0.996 | 0.00 |
| B_pos | +0.0449 | +0.0450 | **0.067** | **False** | 0.993 | 0.00 |
| B_strong | −0.2399 | −0.2400 | **0.604** | **True** | 0.000 | 1.00 |

**U0 false-flag (combined OR rule, independent 4 000 reps):** n=30 → **0.1455** (exp: 0.146), n=60 → **0.0435** (exp: 0.046), n=120 → **0.0063** (exp: 0.006). Exact reproduction ⇒ implementation faithful and the n=30 elevation is real.

**K2 mechanism:** SP `pool_mean = +0.518` (dominated by the two right-skew `Splus` members at n=30 and n=8000). The shrunk null center for U0 = `(1−w)·pool_mean`: k=120 → +0.414 (< margin 0.415), **k=240 → +0.460 (> margin) → FPR explodes**, k=500 → +0.489. The CONTROLLED→INFLATED flip is the mechanical consequence of shrinkage pulling the null estimate toward a positive prior against a margin frozen at k=120.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | DGPs, gap = `(mean−median)/MAD`, Wilson interval, shrinkage `n/(n+k)`, paired-draw seeding all verified. |
| `code/run_experiment.py` | Edge cases | PASS | `MAD==0` branch (`g=0`, `gap_flag=False`, `mad_zero` counted) + hard `assert mad_zero_total==0` (=0 in run); `shape_diagnostic` guards `n<4`. |
| `code/run_experiment.py` | Type safety / docstrings | PASS | Hints + docstrings on public functions; clear VAL-001-style sectioning. |
| `code/run_experiment.py` | Holdout / look-ahead / real-price | PASS (N/A) | Synthetic only; imports `from xen import ass` — no timebars loader; no HA/Renko prices; ATR-unit synthetic. |
| `code/run_experiment.py` | Determinism | PASS | All draws via `rng_for(SeedSequence)`; `k` never enters a draw seed (paired); dip p-value analytic (no RNG); `--verify-determinism` shape/k1/k2 all hash-match. |
| `code/run_experiment.py` | Import side effects / org | PASS | Output dirs created in `main()` only; helpers return data; concise logging; `tqdm` over cells; process-pool order-stable. |
| `code/run_experiment.py` | Plot data reuse | PASS | Plots consume bounded result tables; Plot 4 redraws 60 bounded deterministic samples/type (acceptable, bounded). |
| `python/src/xen/ass.py` | `shape_diagnostic` addition | PASS | Raw-sample-only (k-independent by construction, as designed); existing `score`/`bootstrap_cis` unchanged (integrity anchor diff 0.0 confirms). |

## Numerical Validation

### Spot checks
- U0/n=30 false-flag, U0/n=60, U0/n=120 reproduced exactly (above).
- B_zero/B_pos true \|g\| < 0.30 and dip_p ≈ 0.99 reproduced (above) — both diagnostic legs are blind to these shapes.
- Integrity anchor: EXP-076 stream (TAG_SAMPLE) recomputed 0.07605389804248094 = recorded (diff **0.0**); EXP-077 stream (TAG_EFF) 0.1278884399289532 = recorded (diff **0.0**); self-anchor `direct_expectancy == mean(x)` diff 0.0.

### Range / sanity
- All rates in [0,1] with fixed denominator `R_REP=2000`; Wilson intervals well-formed. `mad_zero_total=0` (continuous DGPs, as predicted). `diptest 0.11.0` pinned and recorded.

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Binomial / Wilson | independent Bernoulli flags across replicates | YES | independent per-replicate seeds |
| MC rate | iid draws from frozen DGP | YES | by construction |
| Paired k-sweep | same draws scored across k | YES | `k` absent from draw seed (code + determinism check) |

---

## Verdict Forensics

### Per-stratum re-derivation & masking check

**Leg A — B detection (pooled headline: FAIL, worst 0.0).** The pooled "B FAIL" **masks a clean, real 2-way split** by bimodal shape:

| B stratum | true \|g\| | dip-bimodal? | detection n≥30 | per-stratum verdict | agrees w/ pooled FAIL? |
|-----------|-----------|--------------|----------------|---------------------|------------------------|
| B_neg | 0.50 | weak (0.30) | 0.76→1.0 | **PASS-ish** (only n=30 at 0.76<0.80) | partially |
| B_strong | 0.60 | strong (1.0) | 0.875→1.0 | **PASS** (≥0.80 ∀ n≥30) | NO — detects cleanly |
| B_zero | 0.25 | none (0.99) | 0.41→**0.0** | **FAIL** (decays with n) | YES |
| B_pos | 0.067 | none (0.99) | 0.19→**0.0** | **FAIL** (decays with n) | YES |

→ **Masking confirmed and characterized.** Strongly-separated bimodals (`B_neg`, `B_strong`; \|g\|≈0.5–0.6) are detected and detection rises to 1.0 with n. Subtle median-positive bimodals (`B_zero`, `B_pos`; the **exact CF-HA-HARAMI-001 failure shape** the diagnostic was built for) are **undetectable** at the frozen operating point, and apparent small-n detection is sampling noise that **decays monotonically to 0** as n grows. The binding floor `n≥30` is where the noise tail is largest — even there `B_zero`/`B_pos` are far below 0.80. (`B_neg` n=30 = 0.7595 is itself a binding miss.)

**Leg B — U false-flag (pooled headline: FAIL, worst 0.152).** Masks an `n`-structure: **only n=30 fails** (all four U types 0.135–0.152); n≥60 passes cleanly (≤0.046 at 60, ≤0.007 at 120, →0). It is a **small-sample noise floor of the OR rule at τ_gap=0.30**, not a global false-flag problem — but n=30 **is binding**, so the FAIL stands.

**Leg C — k-sensitivity (pooled headline: ROUTING_FLIP).** K1 (shrinkage behaviour) INVARIANT across grid (correct — `n/(n+k)` monotone, sparse-pull≥0.25 holds ∀ grid k). K2 (null edge-call FPR) flips CONTROLLED→INFLATED. Per-stratum: every K2 stratum flips at **k=240 (the 2× multiplier — a core grid point, not an extreme anchor)** and k=500, with FPR 0.39–1.0. The flip is decisive and genuine.

### Mechanism

- **B_zero/B_pos non-detection:** both diagnostic legs are structurally blind. The **gap leg** fails because the true robust gap (\|g\|=0.25, 0.067) sits **below** the frozen τ_gap=0.30. The **dip leg** fails because these mixtures are **not dip-bimodal** (dip_p≈0.99) — the minority catastrophic mode is too small/broad (10%/5%, σ=0.6) to carve an antimode in the density. Net: the only signal is small-sample sampling variance on \|g\|, which shrinks with n ⇒ the monotone-decay-to-0 signature.
- **U false-flag n=30:** finite-sample variance of `(mean−median)/MAD` on N(0,1) occasionally exceeds 0.30 (~14% at n=30), plus a small dip-leg contribution (~0.6%); both vanish by n≥60. The D0 bite-check's claimed false-flag 0.000 @ τ_gap=0.30 was evaluated at a single larger n and did not probe the n=30 binding floor.
- **K2 flip:** margin frozen at k=120; increasing k shrinks the null estimate toward `pool_mean=+0.518`; the shrunk null center crosses the fixed margin between k=120 and k=240 ⇒ FPR → 1.0. Mechanical, not stochastic.

### Gate-shape check

- **Binding gate:** `flag = (dip_p<0.05) OR (|g|>0.30)`. **Effect shape it must catch:** median-positive dominant mode + minority catastrophic mode (bimodal/asymmetric).
- **Is the gate the wrong instrument for this shape? YES — for the subtle sub-family.** This is the headline forensic finding: the diagnostic catches the *obvious* version of its target shape (`B_neg`/`B_strong`) but is **structurally blind to the subtle version** (`B_zero`/`B_pos`) — precisely the shape that "a smoothed mean cannot see" and that the experiment was commissioned to close the EXP-074 gap on. This is **"effect of a shape this gate cannot see," not "no effect."** Recorded for the interpreter; the gate is **not** retro-edited. Implication for G-017/Phase 018: the EXP-074 tail-shape-blind-guard gap is only **partially** closed by `ASS`.
- **Per-stratum doctrine working as intended:** `collapsed_convenience_flag=false` is correctly NON-BINDING; the binding verdict lives in the per-stratum `strata` dict, so the heterogeneity above is exposed, not hidden.

---

## Scope Compliance

- Analysis plan followed: **MOSTLY** (see Warning 2 — one pre-registered k-sweep leg omitted).
- Complexity budget: 3/3 validation checks, 4/4 plots, 0 new modules + 1 in-family `xen.ass` extension — within budget.
- Holdout exclusion: N/A (synthetic; no loader) — verified.
- Registry: synthetic, 0 TEST reads, 0 slots — consistent with scope precondition.

---

## Issues

### Critical
None. No defect can move a verdict-bearing number; the double-FAIL is implementation-faithful (independent reproduction matches to MC noise). **No fix + rerun required.**

### Warning

1. **K2 deployed-k `INFLATED` label on `U0/n=30` is a self-calibration MC-noise artifact (interpretive caveat).**
   - File: `code/run_experiment.py:355` (`calibrate_k2_margin`), `:370` (`k2_fpr_for_cell`).
   - Description: the margin `m` is `Q95(shrunk ci_low | null)` calibrated **at k=120** and held fixed, so by construction the deployed-k FPR is pinned to ~0.05. `U0/n=30` lands at fpr=0.054 (wilson_hi 0.0648 ≤ 0.075) → labelled INFLATED, but this is third-decimal MC noise around the calibration target, not a real inflation. The per-cell CONTROLLED/INFLATED label at the deployed k is therefore noise-dominated near target and should not be read literally.
   - **Materiality (non-blocking):** cannot move the binding `k_sensitivity` verdict. The verdict is `ROUTING_FLIP` because of the **genuine, large** inflation at k=240 (2× multiplier, a core grid point) where the shrunk null center (+0.460) crosses the fixed margin (0.415) → FPR 0.39–0.87, and k=500 → 1.0. Even if `U0/n=30` were CONTROLLED at the deployed k, the flip at the 2× multiplier still yields `FLIP_UNBOUNDED` under the pre-registered rule. Verdict unchanged ⇒ Warning, for the interpreter to frame the k-fragility (not the per-cell label) as the finding.

2. **One pre-registered k-sweep disposition (CI coverage) was not implemented.**
   - File: `analysis-plan.md` Step 3 item (2) ("CI coverage of the shrunk-expectancy 90% bootstrap CI on the binding types — EXP-076 D2.1 coverage disposition — per n") vs `code/run_experiment.py` (`run_k_sensitivity` computes only K1 shrinkage-behaviour and K2 null-FPR).
   - Description: the plan pre-registered three k-dependent legs; the code swept two. The coverage leg is absent from `_routing_verdict`.
   - **Materiality (non-blocking):** cannot move the binding `k_sensitivity` verdict away from `ROUTING_FLIP`. Routing-invariance requires **every** binding disposition to be invariant; the verdict is already FLIP on K2, and adding a third disposition can only add flips, never remove the existing one. So the omission cannot rescue the FAIL to PASS. It does reduce disclosure completeness — flag for the documenter (record as a known coverage-leg gap) and the interpreter (do not claim the full pre-registered k-sweep was executed).

### Info

1. **Deployed k = median(SP population n) = 120**, not median(N_GRID)=250. D0-faithful ("k default = median sample size across signal types"), equals EXP-076 `k_shrink`; both medians recorded in `integrity.json`. Ratified at Stage 4. The D3 multipliers {0.5×,1×,2×} apply to 120 ⇒ grid {30,60,120,240,500} (the 2×=240 and anchors 30/500 are distinct; no collisions).
2. **`B_neg` n=30 detection = 0.7595 < 0.80** is itself a binding miss (small-n only; rises to ≥0.85 by n=60 →1.0). The pooled "B FAIL" is driven primarily by `B_zero`/`B_pos`, but `B_neg`@n=30 also contributes — noted so the interpreter does not classify `B_neg` as cleanly passing at the binding floor.
3. **`diptest 0.11.0`** is the analytic Hartigan p-value (deterministic given x) — pinned in `pyproject.toml`/`uv.lock` and recorded; determinism second pass byte-identical.
4. **K1 `abs_delta_driver` = 0.443** is the range of `min_pull_sparse` across the grid (a disclosed magnitude, not a flip driver); K1 verdict INVARIANT is correct.

## Materiality & Re-Audit Requirements

- **No blocking findings.** The implementation is trustworthy; the double-FAIL is genuine. The experiment proceeds to Stage 6 (interpretation) **without** a fix + rerun.
- **For the interpreter (Stage 6):** (a) report the B-detection result **per shape**, not pooled — `ASS` discriminates strongly-separated bimodals but is **structurally blind** to the subtle median-positive minority-mode shape (`B_zero`/`B_pos`), the EXP-074/CF-HA-HARAMI-001 target; (b) frame U false-flag as an n=30 binding-floor effect; (c) read k-sensitivity as genuine k-fragility of the shrunk edge-call FPR (mechanical shrink-toward-positive-prior), and treat the deployed-k per-cell labels as noise-dominated near target (Warning 1); (d) note the coverage leg was not swept (Warning 2).
- **For the documenter (Stage 7):** record Warnings 1 & 2 as known limitations of the run; the registry disposition should reflect a methodology-validation FAIL feeding G-017 `DISCOVERY_ONLY`.
