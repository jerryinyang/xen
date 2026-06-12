# Audit Report: Experiment EXP-047

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 4

The implementation is correct, deterministic, TRAIN-only, and reproduces the
persisted results to full float precision. The headline empirical fact — 0/51
SHIFTED_VIABLE with `fallback_rate ≈ 0` and many exactly-zero deltas — is
**genuine and correctly computed**: the ratified `/ANCHOR` rule (k=1.0)
structurally collapses to the baseline anchor in ~95–99% of regimes *by
qualification*, not by fallback. That collapse is a property of the frozen
definition, not a bug; see W1/W2 for what it means for interpretation.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `src/xen/avwap.py` | Correctness | PASS | Manual recomputation of a differing regime's ATR(14)-prominence pivot (EURUSD-1h, bear regime, confirm bar 5114-segment) reproduces the code's selection exactly; baseline arm reproduces the frozen population (P8 fixture + EXP-046 anchors). |
| `src/xen/avwap.py` | Look-ahead bias | PASS | Anchor selected from segment bars ≤ confirmation bar; trailing TR deque causal; truncation-probe test green and the per-cell probes (≥3, √n-scaled) all passed in the run. |
| `src/xen/avwap.py` | Generator determinism | PASS | Double-generation full-frame equality in all 51 cells, both arms; P8 suite 15/15. |
| `code/move_size.py` | Correctness | PASS | `lifetime_end` (EXP-022 boundary), 0-floored excursions, P5 legs, P4 floors all verified by independent recompute (below). |
| `code/move_size.py` | Edge cases | PASS | Empty windows → 0 excursion; <30-event arms never classified; empty arms → NaN medians not computed; clamp fixture cases verified pre-run. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `head(train_rows)` lazy slice, `train_rows = floor(0.7·floor(0.7·total))`, bound to EXP-043 certified `train_end_ts` per instrument (EURUSD: 610,569 rows, end 2024-08-25 22:19, verified). TEST/holdout rows never materialised; `test_reads: 0`. |
| `code/run_experiment.py` | Synthetic price discipline | PASS | Real domain-bar OHLC only; no chart-type views in scope. |
| `code/run_experiment.py` | Chart-type alignment | PASS | `CloseTime` ordering throughout; cross-arm comparison is distributional (no event pairing or bar-index alignment). |
| `code/run_experiment.py` | Safe optimization | PASS | Anchor state machine kept sequential; vectorized excursion/window logic is retrospective per completed event; no denominator or membership changes. |
| `code/run_experiment.py` | Progress/logging/output dirs | PASS | `tqdm` outer loop; dirs created in `main()`; concise summary logging. |
| both | Type safety / docstrings | PASS | Public functions typed and documented. |

## Numerical Validation

### Spot Checks (all reproduced from raw TRAIN data, independent code path)

1. **Prominence pivot, manual**: EURUSD-1h, first differing regime — manual
   trailing-ATR(14) + suffix-extreme scan selects bar 5114; code 5114;
   baseline 5113. MATCH.
2. **Median MFE recompute**: EURUSD-1h anchor arm 14.24898730682779 bps
   (n=244), baseline 13.949610442187538 (n=243) — both equal the persisted
   `shift_classification.csv` values to the last digit.
3. **Reconciliation**: 125/125 checks pass; EURUSD-1h baseline gross(H=8)
   recompute −2.0008329410072583 vs EXP-046 persisted value, **diff = 0.0**
   (the 1e-9 tolerance retained in revision was correct — the anchor is an
   exact recompute).
4. **Counts**: readiness `n_baseline_events` equals EXP-043 realized counts in
   every reconciled cell (count legs all pass).

### Statistical Checks

- MFE/MAE medians ≥ 0 everywhere (clamp convention respected); IQRs and SEs
  in plausible bps ranges (1h ~6–10, 4h ~8–15 SE_diff); floors 4–25 bps
  consistent with the frozen P2 table and observed median lifetimes.
- `leg1_borderline` false in all 51 rows — no seed-brittle leg-1 calls; the
  composition readout (0 cells) is robust (sensitivity flags at ≥4/≥2 and
  ≥3/≥2 also false).

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Bootstrap median SE | Descriptive only, non-i.i.d. acknowledged | YES | No significance claims; 0 binding tests. |
| Unpaired location shift | Different event populations per arm | YES (but see W1) | 38/51 cells differ; 13/51 are *identical* populations. |
| Matched controls | EXP-021/027 convention | YES | Same-regime, 6-bar exclusion, ≤5 nearest by anchor age, min 3 — verified in `move_size.matched_controls`. |

## Results Plausibility

Plausible and internally consistent. The dominant pattern — anchor-arm and
baseline-arm distributions nearly or exactly identical — is structurally
explained: by the time MA(20,50) confirms a regime change, price has already
moved far off the segment extreme, so the extreme almost always has a
completed ≥1×ATR(14) counter-move and qualifies; being the most price-extreme
candidate, it is then selected, coinciding with the baseline anchor.

Audit quantification (added as `results/audit_anchor_coincidence.csv`,
regenerated deterministically from TRAIN):

| Domain | Mean anchor coincidence | Min | Mean fallback | Identical event populations |
|--------|------------------------|-----|---------------|-----------------------------|
| 1h | 0.978 | 0.963 | 0.007 | 0/17 |
| 2h | 0.983 | 0.972 | 0.008 | 5/17 |
| 4h | 0.985 | 0.946 | 0.015 | 8/17 |

## Scope Compliance

- Analysis plan followed: YES (including all pre-data revision-record changes)
- Deviations: none
- Complexity budget: 0 binding tests / 0; 4 plots / 4; 1 new module / 1
- Holdout exclusion verified: YES (0 TEST reads, 0 holdout reads)

## Issues

### Critical

None.

### Warning

1. **The predeclared collapse disclosure (`fallback_rate`) does not capture
   the actual collapse mechanism.**
   - Files: `results/shift_classification.csv` (`fallback_rate` column);
     D0 P1 ("a high fallback rate means /ANCHOR collapses toward baseline").
   - Description: fallback is ~0–2%, yet the anchors coincide with baseline
     in ~95–99% of regimes — the collapse happens through *qualification of
     the running extreme*, a path D0's disclosure column cannot see.
   - Impact: a reader using only the predeclared columns would conclude
     `/ANCHOR` was exercised and found flat; in fact the rule barely moves
     any anchor at k=1.0. Interpretation must use the audit coincidence
     table.
   - Fix: none required in code; Stage 6 must report the coincidence rates
     and frame the verdict accordingly.

2. **The FLAT outcome is conditional on the ratified k=1.0, and the
   diagnostic had little room to detect anything.**
   - Description: with ≥95% identical anchors, the two arms' MFE
     distributions are nearly forced equal, so leg 1 (ΔMFE ≥ 1×SE) was
     near-unpassable by construction. The result cleanly closes the
     *ratified* `/ANCHOR` definition but is weak evidence about
     significant-pivot anchors generally (a different k or confirmation
     convention is a new phase per the no-re-parameterisation rule).
   - Impact: interpretation/routing language must say "this `/ANCHOR`
     definition collapses to baseline," not "anchor placement does not
     matter."
   - Fix: interpretive framing only; no code change.

### Info

1. `results/audit_anchor_coincidence.csv` is an **audit artifact** (verified
   deterministic regeneration), not a scope expansion; it adds no statistic
   to the binding readout.
2. Reconciliation diffs are exactly 0.0 — the revision-record decision to
   keep the 1e-9 bps tolerance is vindicated.
3. `unreconciled_cells` is empty because the EXP-043 power statement covers
   all 51 cells (count leg grid-wide); the gross(H=8) leg binds on the 37
   EXP-046 baseline cells as scoped.
4. Runtime ~12 s for the full grid is consistent with domain-bar event
   generation (~10k bars/cell) and vectorized bootstraps; not an
   under-computation signal (verified by exact recomputes above).

## Re-Audit Requirements

None — PASS. Warnings are interpretive obligations for Stage 6, not code
fixes.
