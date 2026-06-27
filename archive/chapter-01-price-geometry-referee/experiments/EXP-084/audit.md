# Audit Report: Experiment EXP-084 — AVWAP-4h Portfolio Confirmation Read (CF-CAPGEO-001 Phase 018 / HYP-004b)

## Summary

- **Verdict**: **PASS**
- **Critical Issues**: 0
- **Warnings**: 0
- **Info Notes**: 3
- **Experiment verdict audited**: `NOT_CONFIRM` (portfolio unit, 0 counted reads, disclosure) — **reproduces exactly** from the raw outputs and is mechanistically sound.

The implementation matches the approved plan, the holdout is sealed, reconciliation/determinism invariants
hold, and the `NOT_CONFIRM` is faithful to the per-stratum and per-fold structure (no masking). The Stage-4
S2-floor HALT correctly did **not** fire (pooled WF initial-train `n_train_sep=152 ≥ 120`), so S2 was
genuinely adjudicated.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Verdict legs, pooling, separability, WF aggregate re-derived; all reproduce (below). |
| `code/run_experiment.py` | Edge cases | PASS | `_safe_disclosure_agg` guards thin arms (VP-POC n=169) → NaN row, never HALT; S2-floor HALT guards the unadjudicable branch; finite handling explicit. |
| `code/run_experiment.py` | Type safety | PASS | Typed public helpers; dataclass fields from `xen.wf` consumed correctly. |
| `code/run_experiment.py` | NaN handling | PASS | `np.isfinite` guards on `s1_excess_lo`/`m_margin`; disclosure NaN rows explicit. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `val005.load_first70` materializes only `int(total*0.7)`; WF series = `li.frame` (analysis set); OOS = `net[152:303]` ⊂ analysis set. No fold reaches the holdout. |
| `code/run_experiment.py` | Loader ordering | PASS | `CloseTime`-sorted assertion (`frame.get_column("CloseTime").is_sorted()` → HALT else); pooling by event close-time via `lexsort`, never bar index. |
| `code/run_experiment.py` | Memory/performance | PASS | Plots consume the bounded payload (pooled net ≈303 elts); no heavy re-load for plotting. |
| `code/run_experiment.py` | Safe optimization | PASS | Sequential exit-mirror kept explicit; pooling/cost vectorized; no change to sample membership / ordering / denominators. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` over the basket; helpers quiet. |
| `code/run_experiment.py` | Logging/output | PASS | Concise `LOGGER` summary in `main()`. |
| `code/run_experiment.py` | Organization/import side effects | PASS | `matplotlib.use("Agg")` only at import; `mkdir` in `main()`; sectioned VAL-001 style. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 4 plots from the result payload. |
| `code/run_experiment.py` | Docstrings | PASS | Reusable helpers documented. |

## Numerical Validation

### Spot Checks — binding G-018 conjunction (re-derived from `portfolio_confirm.parquet`)

| Leg | Computed | Pass? |
|-----|----------|-------|
| L1 suite: `exp_lo > m` | `-1.0450 > -0.0396` | **False** |
| L2 median: `med_lo > 0` | `-0.8207 > 0` | **False** |
| L3 beats-random: `beats_lo > 0` | `-0.6558 > 0` | **False** |
| S1 attribution | `s1_excess_lo 1.1092 > m -0.0396` | True |
| S2 tail non-residual | `tailmass 0.0263 ≤ 0.06` ∧ `q05 -5.049 ≥ q05c-δ -8.430` | True (floor_ok, n=152) |

`CONFIRM = L1∧L2∧L3∧S1∧S2 = False` → **`NOT_CONFIRM`** reproduces exactly. Separability (S1∧S2) **passes** on
TRAIN; all three economic OOS legs **fail**.

### Range / structural checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `n_train_sep` (separability region) | = `round(0.5·n_pool)` = 152 | 152 | YES |
| `n_oos` (pooled WF test) | = `n_pool − n_train` = 151 | 151 (fold sizes 30/30/30/31/30 sum=151) | YES |
| TRAIN/OOS disjoint | `[:152]` vs `[152:]` | disjoint, aligned to `folds[0].test_start` | YES |
| Fold floor | all ≥ MIN_FOLD=30 | 30/30/30/31/30, 0 subfloor | YES |
| Gross reconciliation | n+mean to EXP-083 anchor within 1e-9 | `reconciliation_ok=true` (USTEC anchor n=46, gross 1.806) | YES |

### Statistical sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| pooled net_exp | −0.221 ATR | YES | OOS net is negative; consistent with all-negative per-stratum and fresh-fold reversal. |
| pooled exp CI_low | −1.045 ATR | YES | Wide negative lower bound at modest n; legitimately fails the margin. |
| S2 tailmass | 0.0263 | YES | Below τ=0.06 — the AVWAP-FH catastrophe tail is non-residual (validates the pin rationale). |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| `xen.wf` block bootstrap (`kind="block"`) | Serial dependence preserved | YES | `kind="block"` used (not iid); real serially-dependent data. |
| Pooled ATR-unit returns | Cross-instrument dimensional consistency | YES | All net returns ATR-normalized per instrument; cost applied per-instrument **before** pooling (`COST_CONSTANTS[inst]`). |
| FPR-calibrated margin `m` | Non-parametric null calibration | PARTIAL | `m=−0.0396` is mildly **negative** (Info 1) — conservative-safe for a `NOT_CONFIRM`. |

## Results Plausibility

All net values are in plausible ATR units; per-arm point estimates span −0.22…+0.75 but **no arm** has a
positive CI_low (best: VP-POC exp_lo −0.259) — the basket fails to confirm under every exit, not merely the
pinned arm. Consistent with EXP-083/085's "edge lives in low-n unadjudicated cells" finding.

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

| Stratum | net_exp | exp_lo | net_med | Per-stratum read | Agrees with pooled `NOT_CONFIRM`? |
|---------|---------|--------|---------|------------------|-----------------------------------|
| NZDUSD-4h | −0.579 | −2.100 | −0.200 | net-negative | YES |
| USDCAD-4h | −0.484 | −2.468 | −0.127 | net-negative | YES |
| USTEC-4h | −0.159 | −2.949 | **+0.925** | mean-neg / median-pos | YES (mean & exp_lo negative) |

- **Pooled headline `NOT_CONFIRM` is NOT masking a positive stratum.** All three strata are net-negative on
  expectancy with deeply negative CI_lows (−2.1, −2.5, −2.9). USTEC shows a positive *median* point estimate
  (+0.925) but a negative mean and a −2.95 expectancy CI_low — a single-instrument median quirk on n=77 that
  does not flip the basket and is disclosure-only by design. The pooled verdict faithfully represents the
  basket; it is conservative, not concealing.

### Mechanism

The basket **separates on TRAIN** (S1 attribution + S2 tail non-residual both pass at n=152) but has **no net
edge out-of-sample**: all three economic legs miss (expectancy CI_low −1.045 < m; median CI_low −0.821 < 0;
beats-random CI_low −0.656 < 0). The **driver is temporal**: the per-fold trajectory is positive in the two
**non-fresh** [50–70%] selection-overlap folds (fold0 +1.866, fold1 +0.068) and **negative in all three fresh**
[70–100%] folds (fold2 −1.002, fold3 −1.250, fold4 −0.754). The apparent edge is concentrated in the region
that overlaps EXP-083/085's selection window and **reverses** in the genuinely held-back region — exactly the
Risk-1 concern the plan flagged, now realized. The non-confirmation is **exit-invariant** (no arm has a
positive CI_low), so it is not an artifact of the pinned `AVWAP-FH` choice.

### Gate-shape check

- Binding gates: WF mean-expectancy + median co-primary (location) + S2 (tail) + S1 (attribution).
- **Is the gate the wrong instrument for the shape? NO.** S2 was genuinely adjudicated (n=152) and **passed**
  (tailmass 0.026, q05 −5.05 vs control −8.03) — the gate can see the catastrophe tail and finds it
  non-residual. Both location measures are non-positive at their CI_lows (mean −1.045, median −0.821), so the
  effect is not a hidden median- or tail-only positive that a location gate missed. This is **"no OOS edge,"
  not "effect of a shape this gate cannot see."** The mildly positive pooled/USTEC median point estimates do
  not survive their CIs.

### Power adequacy

`NOT_CONFIRM` (not `INCONCLUSIVE_SPANS_ZERO`) is justified: `n_oos=151 ≥ 2·MIN_FOLD (60)`, all 5 folds ≥ 30
(0 subfloor). Although the expectancy CI spans zero (exp_lo −1.045 < 0), `verdict_logic` correctly routes to
`NOT_CONFIRM` because power is adequate and the binding legs fail decisively — consistent with the scope's
definition ("fails ≥1 binding leg with adequate power").

## Scope Compliance

- Analysis plan followed: **YES**. Portfolio binding unit; per-stratum (3) + per-arm (11) + per-fold (5)
  emitted `binding=false` disclosure; binding suite = `xen.wf` aggregate + FPR margin (not the bps gate
  stack), as the plan's binding clarification requires.
- Deviations: none beyond the Stage-4-approved S2-floor HALT (did not fire here).
- Complexity budget: 3/3 method families, 4/4 plots, 0 new modules — within budget.
- Holdout exclusion verified: **YES** — `load_first70` first-70% only; OOS folds ⊂ analysis set; metadata
  `holdout_untouched=true`, `test_stratum_in_analysis_only=true`.
- Registry/ledger: `counted_test_reads=0`, `candidate_slots=0`, portfolio-aggregate disclosure against the 3
  strata — consistent with D0-amendment-003. (Recorded by the documenter at Stage 7.)
- Provenance: EXP-083 sha `fa4035f3…` asserted; EXP-085 cost constants verbatim; basket+rule hash-pin
  (`4245d901…`) emitted before OOS folds. Determinism: two-pass in-process fingerprint `determinism_ok=true`.

## Issues

### Critical
None.

### Warning
None.

### Info

1. **FPR-calibrated margin `m` is mildly negative (−0.0396).** `run_metadata.json` → `separability.m_margin`.
   A negative null-calibrated margin makes leg L1 (`exp_lo > m`) marginally *more lenient* than `exp_lo > 0`.
   For this `NOT_CONFIRM` it is conservative-safe (a lenient margin can only ease CONFIRM; the verdict still
   fails by a wide margin on all three legs). Flagged for the interpreter and for any future CONFIRM-bearing
   read where a negative `m` could matter.

2. **USTEC-4h mean/median sign split (disclosure).** USTEC net_med +0.925 vs net_exp −0.159 on n=77 — an
   asymmetric single-instrument signature. Disclosure-only (non-binding); context for a future scope, not a
   verdict driver.

3. **Stage-4 S2-floor HALT did not fire.** `n_train_sep=152 ≥ S2_FLOOR=120`, so S2 was adjudicated as
   intended; the governance fix's HALT path was not exercised this run. Recorded for traceability.

## Materiality & Re-Audit Requirements

- **No Critical or Warning findings → no fix-and-rerun required.**
- **Materiality of each Info finding (why none can move a verdict-bearing number):**
  - Info 1: the negative `m` only loosens leg L1; `exp_lo −1.045` fails it regardless, and legs L2/L3 fail
    independently of `m`. Cannot move `NOT_CONFIRM`.
  - Info 2: USTEC is a `binding=false` disclosure stratum; the binding verdict is the portfolio unit. Cannot
    move the binding number.
  - Info 3: a non-fired guard; no effect on any computed value.
- **Re-audit**: not required. The verdict reproduces from the raw outputs, the mechanism is established, and
  all invariants (holdout, reconciliation, determinism, ledger) hold.

**Overall audit verdict: PASS** — `NOT_CONFIRM` is trustworthy, well-powered, exit-invariant, and not masking
any per-stratum or per-fold positive. Cleared for Stage 6 interpretation.
