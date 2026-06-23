# Audit — EXP-089 (CF-MR-001 Mean-Reversion Entry Availability Screen, Phase 020)

**Auditor:** experiment-auditor (pipeline Stage 5)
**Date:** 2026-06-23
**Run audited:** the **amended** run (`D0-amendment-001`: causal MR-tempo cap; regime-matched + horizon-matched
control; leg-2 retired; all 6 sub-screens single-test). The first run was a deviation — its audit (findings
**C-1**, **C-2**) is retained in the **Appendix** below and is what `D0-amendment-001` references.
**Artifacts:** `scope.md` (bannered), `analysis-plan.md` (amended), `code/run_experiment.py`,
`xen.mean_reversion` / `xen.vol_regime`, `results/`.

---

## Headline verdict

**`SCREEN_DELIVERED` is valid, and the provisional `ADMITTED` is now credible** — both deviation confounds are
empirically confirmed removed, and the result is driven by the bare mean-reversion entry, not an artifact.

- Deterministic (`determinism_ok`, `determinism_cells`, `determinism_gate_stream` all true), reconciled
  (`recon_all_ok`, `regime_match_recon_ok` true), TRAIN-only (`holdout_untouched=true`,
  `counted_test_reads=0`), real-price, bite GREEN at the single-test `f01a000b…` (recorded sha ==
  `bite_expected_single_test_sha256`).
- `S_fam = 28`, `S* = 7`, axis perm-p ≈ 0.0002; ADMITTED across the full FWER band {0.025, 0.05, 0.10};
  MC-stable (1000: S*=6, p≈0.001). Independently re-derived from `cell_availability.csv` — matches to the
  integer.
- **Driver: CORE** (bare RSI-2 fade), z=17.3, argmax lever = CORE — *not* a single regime. The regimes are now
  near-uniform (LOW=22, MED=25, HIGH=20), so the family is admitted on the entry mechanism itself.

No Critical findings. Three Info disclosures for the interpreter (§Findings).

## 1–3. Scope / data / code — PASS (inherited from the Stage-4 review, re-verified on outputs)

- **Scope/plan compliance:** the amended plan is implemented exactly — MR-tempo cap, regime-matched controls,
  6 single-test sub-screens via `run_sub_screen` → `combine_axis`; no leg-2 residue; no bonus analyses.
- **Holdout / look-ahead / real-price:** TRAIN sub-split only; MR-tempo cap uses only reversion episodes closed
  strictly before each entry; RSI/EMA/ATR/regime causal; all metrics on real domain OHLC. (Verified in Stage 4;
  outputs consistent — `read_region` and fences as recorded.)
- **Determinism / reconciliation:** byte-identical second pass on cells + gate stream; matched-random
  count/direction and regime-membership integrity guards all pass.
- **W-1 cosmetic (carried):** `run_metadata.provisional_disposition_NON_BINDING` still reads "pending G-019
  cross-axis Holm" (the frozen `combine_axis.disposition` string). `family_admission.json` carries the corrected
  "pending G-020" caption. Non-material (free text; binding `S_fam`/`S*`/`perm_p` are separate). See Findings.

## 4. Numerical re-derivation — PASS

Independent recompute from `cell_availability.csv` (beats-random ∧ powered):

```
CORE          S=28 (powered 46)     CORE-VOL-LOW  S=22 (46)
CORE-VOL-MED  S=25 (46)             CORE-VOL-HIGH S=20 (46)
CORE+TREND    S= 0 (46)             CORE+FILTER   S= 1 (29)
```

Matches `family_admission.json` exactly. `S_fam = max = 28` (CORE), `S* = 7`, perm-p ≈ 0.0002.

---

## Verdict Forensics

### Per-stratum re-derivation & masking check

The headline is **not** a single-stratum artifact this time, and it is **not masking a contradiction**:

- **Across sub-screens:** CORE and all three regimes pass strongly and similarly (28/22/25/20), all four inside
  the D2a coin-flip band [17,29]. The variant toggles collapse to noise (0, 1). The family is admitted on a
  broad, mechanism-level signal, not one cell or one regime.
- **Within CORE (28 cells):** spread across **all 16 instruments**, with a clear **domain gradient** —
  15m: 16 passing, 1h: 11, 4h: 1. No domain shows a *reversed* effect; 4h is simply weak/absent (the fast
  RSI-2 bounce is a higher-frequency phenomenon with fewer 4h events). The pooled S=28 is an honest count but
  is **predominantly a 15m/1h availability** — the interpreter should report it per domain, not as a
  timeframe-flat claim (LESSON-001).
- `theta_signal > theta_random` in 100% of CORE passing cells; `n_cond` healthy (855–16218, no zero/degenerate
  cells).

### Mechanism statement — the driver is the short-term reversion bounce, measured conservatively

After an RSI-2 extreme, price reverts favourably over the next few bars more than from a random-timed,
direction-matched entry: bare CORE shows a median signed favourable excursion of ~0.75 ATR over a ~3-bar
reversion window, with per-cell `Δ̂_rand` median ≈ 0.06 ATR positive in ~87% of cells, clearing the one-sided
lower bound in 28/46. This is the documented short-horizon mean-reversion effect — the *availability* the screen
is designed to detect.

**Why it is not a residual normalization artifact (unlike the deviation):**
- The endpoint divides favourable excursion by **entry-bar ATR**. RSI-2 extremes typically occur *after* sharp
  moves, so signal entries carry **elevated** entry ATR relative to random bars → this **deflates** signal
  `MFE/ATR` and biases the test **against** the signal. A positive CORE result is therefore **conservative**,
  not inflated — the opposite direction from the deviation's C-1.
- The **regime uniformity** (LOW≈MED≈HIGH, flat `Δ̂_rand` ≈ 0.05–0.08) confirms the entry-ATR↔regime coupling
  that drove the deviation is gone: with regime-matched controls the within-regime denominators cancel, and the
  monotone LOW>>HIGH ladder (was +0.55/0/−0.52) has collapsed to noise.
- The **variant kill** (TREND S=0, FILTER S=1) is mechanistically coherent and corroborating: imposing
  trend/momentum agreement on a fade (long only if `Close>EMA20` / `RSI5>50`) contradicts the oversold entry
  condition, removing the reversion population and the edge. A spurious result would not respond this cleanly to
  a mechanism-negating filter.

### C-1 / C-2 fix verification (the reason for the amendment)

| | Deviation (voided) | Amended run |
|---|---|---|
| Regime `Δ̂_rand` (LOW/MED/HIGH) | +0.55 / ≈0 / −0.52 (symmetric ladder) | 0.050 / 0.080 / 0.045 (flat) |
| `theta_signal` by regime | 3.98 / 3.39 / 2.89 (window-inflated) | 0.77 / 0.73 / 0.73 (MR-scale) |
| Driver | CORE-VOL-LOW only (z=115) | CORE (z=17.3), regimes uniform |
| Cap median | ~30–100 bars (trend) | 3–4 bars (MR; 77% at FLOOR) |

Both confounds are empirically resolved. C-1: regime-matched control → flat regime profile, entry-ATR cancels.
C-2: MR-tempo cap → ~3-bar reversion window (the realized horizon is dominated by `FLOOR=3`, i.e. the typical
RSI-2 reversion median is ≤3 bars — confirming the family is genuinely short-lived).

### Gate-shape check

The binding gate is a **location** (median) test over the joint-max of 6 sub-screens; the effect **is** a
location shift in favourable `MFE_med`. Gate shape matches the effect shape — the gate can see it. No
tail/bimodal/asymmetric read is owed (directional location family; magnitude is the closed CF-VOLEXP-001
surface). No gate-shape mismatch.

---

## Findings (no Critical; three Info)

### I-1 — Info: realized MR-tempo cap is FLOOR-dominated (effective ~3-bar horizon)

- 77% of CORE caps sit at `MR_CAP_FLOOR=3`; `cap_median` per cell is 3–4 bars; `CAP_MAX=40` never binds. The
  RSI-2 reversion median duration is mostly ≤3 bars, so the "adaptive" tempo rarely exceeds the floor.
- **Materiality — non-material:** `FLOOR=3` is a pre-registered frozen constant (justified pre-data); the result
  is the intended MR-scale read and is robust across the FWER band. This is a disclosure for the interpreter
  (the effective horizon is ~3 bars), not a defect — it confirms C-2 is fixed and that the family is short-lived.

### I-2 — Info: CORE availability is a 15m/1h phenomenon (domain gradient)

- The 28 CORE passes are 15m: 16, 1h: 11, 4h: 1. The interpreter should report the per-domain decomposition; the
  pooled S=28 is disclosure, and a "works at all timeframes" reading would be unsupported.
- **Materiality — non-material:** does not change `S_fam`/`S*`/perm-p or the binding gate (which is per-cell then
  joint-max); it refines *how* the verdict is described, not the verdict.

### I-3 — Info (carried W-1): stale "G-019" string in `run_metadata.json`

- `provisional_disposition_NON_BINDING` reads "pending G-019 cross-axis Holm" (frozen `combine_axis` string).
  `family_admission.json` has the corrected G-020 caption. Free text only; no binding number depends on it.
- **Materiality — non-material.** Fix-on-touch (documenter/G-020 cite the G-020 caption); no rerun.

## Materiality summary

| Finding | Class | Moves a verdict-bearing number? | Action |
|---|---|---|---|
| I-1 FLOOR-dominated cap | Info | No (pre-registered constant; intended MR horizon) | Disclose effective ~3-bar horizon at Stage 6. |
| I-2 domain gradient | Info | No (refines description, not the gate) | Report per-domain decomposition at Stage 6. |
| I-3 stale G-019 string | Info | No (free text; corrected caption in family_admission.json) | Fix-on-touch; cite G-020 caption. |

## Disposition

`SCREEN_DELIVERED` is a valid, deterministic, fenced, causal, real-price computation. The provisional
`ADMITTED` is **credible and may be carried to G-020** as the realized statistic — driven by the bare RSI-2
mean-reversion entry, broad across instruments, robust across the FWER band, with both deviation confounds
empirically removed. Stage 6 should (a) report the result per domain (I-2), (b) note the effective ~3-bar MR
horizon (I-1), and (c) frame the argmax = CORE as "the lever is the bare fade, not the regime partition" (the
regimes pass uniformly; the regime split adds nothing the unconditioned entry lacks). No re-execution required.

---

## Appendix — VOIDED first-run (deviation) audit (findings C-1, C-2)

*Retained as the forensic record `D0-amendment-001` references. These findings pertain to the first run, whose
results were hard-deleted; they are resolved by the amendment and re-verified fixed above.*

- **C-1 (Critical, verdict-material) — ATR-normalization confound.** The first run's provisional `ADMITTED`
  (`S_fam=27`) was driven entirely by **CORE-VOL-LOW** via the (then-binding) leg-2 conjunction. The endpoint
  normalized forward excursion by entry-bar ATR, and the `/VOLREGIME` label *is* the entry-ATR percentile; with
  volatility mean-reverting over the forward window this produced a symmetric, monotone, baseline-independent
  ladder (LOW +0.55 / MED ≈0 / HIGH −0.52 ATR), with leg-1 ≈ leg-2 and universal across ~91% of cells — the
  signature of a mechanical artifact. The leg-2 conjunction and regime-membership null were structurally blind
  to it (z=115 measured a structural label-correlate, not an edge). **Fix:** regime-matched control (entry-ATR
  cancels within-regime). **Re-verified fixed:** regime `Δ̂_rand` now flat (0.050/0.080/0.045), driver = CORE.

- **C-2 (Critical, verdict-material) — trend-length horizon / construct mismatch.** The endpoint was measured
  over the trend-length MA-segment adaptive cap (~30–100 bars) vs the 1–5 bar RSI-2 reversion scale; MFE being
  monotone in horizon, it credited post-reversion drift, not the bounce — testing a different strategy. **Fix:**
  causal MR-tempo cap (RSI-2 reversion-episode tempo). **Re-verified fixed:** cap median now 3–4 bars.
