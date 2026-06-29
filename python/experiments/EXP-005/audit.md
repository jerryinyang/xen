# Audit Report: Experiment EXP-005 — E5 DET-Adjudication + FREEZE (+ folded Q4 form-check)

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1 (a forensic-disclosure naming caveat — **RESOLVED post-audit**; non-material)
- **Info Notes**: 3
- **Scope**: analysis-only; 0 TEST reads; 0 candidate slots; global holdout sealed; not tuned on
  CF-MR-002 (absent). Methodological — screens no candidate.
- **Binding outcome audited**: §10.3a (`gate_stack_adaptive` + `adaptive_row`) **matches-or-beats**
  the single-statistic variant-c on **32/32** strata under DET-dominance (lower MDE at equal-or-better
  FPR); §10.3a is **leak-clean 32/32**; variant-c is **refuted** (no FPR control). The renewed referee
  is **FROZEN** at §10.3a, q\*=0.75. The regression anchor reproduces EXP-003(A1)/EXP-004 **0/32**.

A mid-run logic fix (below, "Resolved during execution") was applied to the adjudication/freeze
**classification** before the binding rerun; the audit certifies the **post-fix** run. The underlying
computed quantities (MDE / dogfood-FPR / future-destroy rates) were unchanged by the fix — only the
verdict assembly was corrected — and the regression anchor passed in both runs.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `referee_adaptive.py` (+`adaptive_row_variant_c`) | Additivity / frozen integrity | PASS | `git diff --numstat` = **70 insertions, 0 deletions**; `adaptive_row`, `gate_stack_adaptive`, all constants byte-unchanged. `referee_calibration.py` byte-frozen (no git change). |
| `adaptive_row_variant_c` | Correctness | PASS | Consumes the **same** `gate_stack_adaptive` core; verdict = `L1 ∧ (ci_naive.lower>0)`, power-aware ABSTAIN on `n_naive==0`; L5 pooled+studentized-subpop + L3 neutral CI emitted as non-binding `DIAG_*`. Matches design. |
| `run_experiment.py` | Plan compliance | PASS | 3-form DET (frozen/§10.3a/variant-c) at the single point (q\*=0.75, NB=500, off=0); E5 FPR rule (`MIN_FPR_PASSES=2`, `2α`) in classify only; per-stratum adjudication; regression anchor; both-form tripwires; freeze manifest. |
| `run_experiment.py` | Holdout exclusion | PASS | `load_analysis_minutes` lazy-scans, `sort("CloseTime")`, `slice(0, total*0.70)`; holdout never collected. |
| `run_experiment.py` | NaN / edge cases | PASS | `mde_le/mde_lt` handle inf=UNPOWERED; `state_delta*` NaN-guard on inf; empty-stratum skip (`len(returns)<200`). |
| `run_experiment.py` | Determinism | PASS | Fixed seeds per draw; `ra.Q_STUD_MIN=Φ⁻¹(q*)` set per worker (= module default at 0.75); ProcessPool strata-independent. Anchor 0/32 ⇒ deterministic. |
| `run_experiment.py` | Organization / import side-effects | PASS | Constants→types→I/O→pure helpers→plotting→orchestration→`main()`; dirs created in `main()`; `tqdm` on the instrument loop; `logging`. |
| `run_experiment.py` | Plot data reuse / memory | PASS | Plots consume the bounded per-stratum row list; no reload. |

---

## Numerical Validation

### Spot checks (independent re-derivation from `form_adjudication_per_stratum.csv`)

- **§10.3a-vs-frozen STATE ΔMDE**: median **7.5**, min **4.0**, max **23.5** — bit-matches
  EXP-003(A1)/EXP-004 (BTCUSD/4h 32→12 =20; EURUSD/1h 8→1 =7; EURUSD/4h 12→4 =8). The regression
  anchor's own check returns **PASS, 0/32 mismatches** (verdict + STATE ΔMDE + adaptive FPR).
- **§10.3a dogfood FPR**: **0.0 on all 32** strata; future-destroy max **0.050** (≤ guard). Leak-clean.
- **variant-c dogfood FPR**: range **0.062 – 1.000** (EURUSD/1h 0.988, BTCUSD/4h 0.704, EURUSD/4h
  0.494; **all 16 1h strata ≈1.0**); future-destroy max **1.000**. FPR-unacceptable **31/32**;
  leak-clean **0/32**.

### Range / statistical sanity

| Quantity | Value | Sensible? | Notes |
|---|---|---|---|
| adjudication tally | 32× `10.3a_MATCHES_OR_BEATS` | YES | variant-c DET-ineligible (not leak-clean) on every stratum ⇒ §10.3a wins by the FPR gate. |
| §10.3a verdict vs frozen | 32× `DET_DOMINANT` | YES | reproduces the E3a/E4 binding result. |
| variant-c leak-clean | 0/32 | YES | mechanism below. |
| freeze manifest | `FROZEN` → §10.3a; `sha256=bf28c8…01f4` | YES | constants (q\*0.75, Q_STUD_MIN 0.67449, materiality 1.5/3.0, full 17-cost map, open-to-open ≤t-1) recorded; rejected = variant-c. |

---

## Verdict Forensics

### Per-stratum re-derivation & masking check

Re-computed the adjudication per stratum from the CSV: **all 32** are `10.3a_MATCHES_OR_BEATS`, and
all 32 are leak-clean for §10.3a / not-leak-clean for variant-c. **No pooled headline masks
heterogeneity** — the result is genuinely homogeneous (every stratum tells the same story), not an
average over a flipping minority. The one stratum where variant-c's *dogfood-FPR* alone was
"acceptable" (USDJPY/4h, FPR 0.062, `wilson_lower≈0.034 ≤ 0.10`) is still **not leak-clean** because
it **survives future-destroy at 0.20** — correctly DET-disqualified by folding future-destroy into
eligibility (this is exactly the stratum the pre-fix logic mislabeled `VARIANT_C_DOMINATES`; see
Resolved-during-execution). Pooled tally is therefore a faithful disclosure, not a verdict shortcut.

### Mechanism (why the verdict came out this way)

- **§10.3a wins because variant-c has no FPR control, not because §10.3a has lower MDE.** This is the
  DET-dominance definition working as designed: a form off the FPR curve cannot win on MDE. variant-c
  in fact shows *lower* raw MDE on most shapes (`state_delta_vc_minus_103a` median −2.5) — but that is
  the **leak signature** (a gate that passes ~everything "detects" at the lowest grid edge), not real
  recovery. The corrected adjudication disqualifies it before the MDE comparison.
- **Why variant-c leaks:** its single binding statistic is `ci_naive.lower > 0` — the incremental edge
  over the **naive-momentum** control — with **no absolute floor** (no neutral CI-lower>0, no
  materiality, no sub-pop). The naive momentum strategy is net-negative on these series (whipsaw +
  cost), so a null/random position "beats naive" trivially ⇒ dogfood FPR up to 1.0, and the comparison
  to a losing baseline **persists under return-permutation** ⇒ survives future-destroy. `referee_adaptive.py:adaptive_row_variant_c` (verdict = `l1 and economic=="PASS"`, economic from `ci_naive.lower`).
- **Why §10.3a does not:** the §10.3a composite additionally requires L3 **neutral** CI-lower>0 **and**
  L5 materiality (pooled OR studentized-subpop > `Q_STUD_MIN` ∧ > materiality) — all of which collapse
  under future-destroy. Hence FPR 0/32, future-destroy ≤0.05.

**Conclusion:** the form-check is a clean, decisive **refutation of the single-statistic
(incremental-over-naive) form** and a strong validation of freezing §10.3a — the multi-leg
validity→economics composite supplies the FPR control the single statistic lacks.

### Gate-shape check

The binding instrument is the **DET-dominance test at equal-or-better FPR** (MDE × dogfood-FPR ×
future-destroy across DENSE/TAIL/SPARSE/STATE). It sees all four predeclared shapes; STATE is the
designed discriminator (§10.3a recovers it via the studentized sub-pop, the E3a finding). No
shape-blindness: the comparison is between two forms on the identical shape battery, and the FPR axis
is what separates them. Not the wrong instrument.

---

## Causal Provenance & Leak

### Provenance trace (verdict-bearing columns)

| Column | Inputs & timestamps | Uses only ≤ t (≤ t-1 next-bar)? | Lines |
|---|---|---|---|
| returns | open-to-open `log(Open[t+1]/Open[t])`, last bar dropped | YES (E0 basis) | `referee_adaptive.next_open_to_open_returns_from_bars` |
| §10.3a / variant-c verdict | frozen split / block-bootstrap / neutral+naive CI / per-episode sub-pop on the **test** slice of the cost-charged net series | YES — no future read; identical core for both forms | `gate_stack_adaptive`; `adaptive_row` / `adaptive_row_variant_c` |
| dogfood signals | Donchian-20 + MA 20/50 on real OHLC, **lagged +1** (`lag_open_to_open`) | YES (`≤ t-1`) | `run_experiment.dogfood_fpr` |

- `rct[di]`-style own-close-as-intrabar-limit: **NONE** (no intrabar limits in this experiment — pure
  position×return net series). 
- Decisions at action-bar open on confirmed bars: YES (lagged signals; open-to-open basis).
- Returns open-to-open: YES (not open-to-close).

### Leak tripwire

- Future-destroying control shipped (block-permute returns) on **both** adaptive forms: YES
  (`future_destroyed_passrate`).
- **§10.3a collapsed** under it (max 0.050 ≤ guard) → leak-clean, freezable. ✓
- **variant-c did NOT collapse** (max 1.000) → this is the predeclared, **expected refutation** of
  variant-c (a future-destroyed "edge" surviving = no FPR control), **not** a §10.3a defect. The
  freeze gate keys on §10.3a-only leak-cleanliness; variant-c's leak is recorded as its rejection
  rationale. Correctly handled. ✓

### Shared-module provenance contract

`adaptive_row_variant_c` docstring states it reads the same `gate_stack_adaptive` core and emits only
a verdict + diagnostics (no new outcome/target column); confirmed against code. `referee_calibration.py`
(Chapter-01 frozen suite) **byte-unchanged** (git). The freeze pins `sha256(referee_adaptive.py)`.

### Price-primary check

Analysis-only — synthetic exogenous positions + planted oracle edges + frozen primitives + the
adaptive verdict paths; **no price→signal generation**, so the cTrader-engine requirement does not
apply. No feed/port, no slippage leg. Not a vectorized price-strategy backtest.

---

## Scope Compliance

- Analysis plan followed: **YES**. Deviations: the adjudication/freeze classification logic was
  corrected mid-run (see below) to faithfully implement the *predeclared* "at not-worse FPR" criterion;
  not a scope change.
- Complexity budget: **3 stat blocks** (DET MDE × FPR + adjudication; within 2–4) · **3 plots**
  (form-DET map, STATE MDE, dogfood-FPR; within 3–5) · **1 new src verdict path** (variant-c, additive)
  + harness (within 0–1). PASS.
- Holdout exclusion verified: **YES** (first-70% slice; holdout never collected).

---

## Resolved during execution (transparency — not an open finding)

The **first** binding run surfaced two classification bugs in the harness (the computed MDE/FPR/FD
numbers were correct; only the verdict assembly was wrong):
1. `adjudicate` compared MDE without first DET-disqualifying a leaking form, so variant-c's
   leak-inflated low MDE produced 26 spurious `MIXED` + 1 spurious `VARIANT_C_DOMINATES`.
2. The freeze gate conflated variant-c's (expected) leak with a §10.3a leak, spuriously blocking the
   freeze.

Fix (faithful to the predeclared DET-dominance-at-equal-FPR criterion): (a) per-stratum DET-eligibility
= leak-clean (FPR-acceptable **and** future-destroy collapsed **and** no no-plant breach); a leaking
form is off the curve and the other matches-or-beats by default; (b) the freeze gate keys on
**§10.3a-only** leak-cleanliness, with variant-c's leak recorded as its refutation. The binding rerun
(certified here) gives the clean 32/32 result. The regression anchor passed in **both** runs (the
§10.3a path was never touched). This is the materiality-gate loop functioning (caught at execution,
fixed, re-executed) — there is **no surviving Critical**.

## Issues

### Critical
None.

### Warning — RESOLVED post-audit
1. **Leak-contaminated forensic field (now gated to NaN).** The original run reported a STATE-MDE gap
   `≈ −2.5`; because variant-c leaks (passes ~everything) its STATE MDE is artificially *lower* than
   §10.3a, so the field could be misread as "variant-c recovers STATE better."
   - **Materiality**: did **not** move the verdict — the binding adjudication is FPR-gated and
     disqualifies variant-c regardless of its MDE (the field was never read by `adjudicate`/freeze).
     Non-blocking.
   - **Resolution (post-audit, code)**: the field is renamed `state_mde_gap_both_eligible_bps` and
     computed **only where both forms are DET-eligible (leak-clean)**, else NaN; the summary now
     reports `n_strata_both_det_eligible = 0`, `gap = NaN` — honestly "no valid comparison." Re-run:
     binding result unchanged (32/32, FROZEN §10.3a), regression anchor still 0/32. Additionally,
     `adaptive_row_variant_c` gained an explicit "⚠ REJECTED — NOT THE FROZEN REFEREE / never call as
     a gate" docstring banner so the co-resident rejected path cannot be mistaken for §10.3a. The new
     pinned `sha256(referee_adaptive.py) = b4fd6cb1…ae847` (additivity preserved: 78 insertions, 0
     deletions; §10.3a path byte-unchanged).

### Info
1. `freeze_manifest.json` records `git_commit: 6e170d4` (HEAD at run time, pre-E5) while the
   `sha256` pins the **current** (variant-c-added, uncommitted) bytes. The sha256 is the authoritative
   pin; the E5 commit will carry exactly these bytes. Note in the report.
2. variant-c's refutation is **mechanism-general**, not a tuning artifact: any single-statistic form
   that omits an absolute edge floor inherits the "beats a losing baseline" leak. This strengthens the
   freeze rationale; record in the families/registry note.
3. DE30 absent (no 5-year-era file) → 16 inst × 2 domains = 32 strata, as in E1–E4. Consistent.

## Materiality & Re-Audit Requirements

- No Critical findings → **no rerun required**. The one Warning is shown unable to move the
  FPR-gated verdict (materiality stated above). The freeze (§10.3a, q\*=0.75) rests on: anchor PASS
  0/32, §10.3a leak-clean 32/32, variant-c refuted 32/32, frozen-suite byte-integrity, additive
  variant-c. **Audit verdict: PASS.**
