# Audit Report: Experiment EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate (CF-CAPGEO-001 Phase 018)

## Summary

- **Verdict**: **PASS** (implementation correct and numerically reproduced to full float precision; verdict
  forensics complete). The headline `NET_SURVIVES` is rule-faithful but **materially masked** — see Verdict
  Forensics. No verdict-material defect.
- **Critical Issues**: 0
- **Warnings**: 2 (both forensic/disclosure; shown non-material below)
- **Info Notes**: 3

This is a TRAIN-only cost read-gate (0 counted reads, 0 slots). The audit ran the full verdict-forensics
protocol autonomously because the positive headline contradicts the governing amendment's expectation
(EXP-030/045 cost-kill pattern).

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `capgeo_cost.py` | Exit-mirror line-faithfulness | **PASS** | `static_barrier_exit`/`fixed_horizon_exit`/`partial_two_leg_exit` are line-for-line transcriptions of `capgeo_screen.resolve_static_barrier`/`resolve_fixed_horizon`/`resolve_partial_two_leg` — same `i+1..min(cap,last)` window, same **adverse-first** intrabar tie-break, same mark-to-close-at-cap, same CENSORED branch, same `tf<=0`→excluded guard. `partial` returns leg-2 (`k2`, final) as `exit_idx`. Diff confirmed by inspection (capgeo_cost L88–224 vs capgeo_screen L97–341). |
| `capgeo_cost.py` | Reconciliation guard | PASS | `reconcile_exit_path` checks finite-mask equality, `cls` exact, `ret` within 1e-9, and `exit_idx>=0` on every resolved event. HALT-on-False at the call site. |
| `capgeo_cost.py` | Cost arithmetic / NaN / div-zero | PASS | `event_costs` raises on non-finite/≤0 ATR or negative holding; `mean(cost_ATR)>0` always (`RT>0`) → no 0/0 in shares. Reused `pin.atr_entry` (not recomputed). |
| `run_experiment.py` | Interception correctness | PASS | `_ExitInterceptor` swaps `rx.resolve_*` to wrappers that call the original (truth) and the mirror on **identical args**, reconcile, stash by `id(Resolution)`; restored on `__exit__`. Frozen module files untouched (hashes recorded). |
| `run_experiment.py` | Holdout exclusion | PASS | `train_frame = li.frame.slice(0, int(height*0.7))` on the already-first-70% VAL-005 frame; `CloseTime`-sorted assertion; TEST/holdout never sliced. |
| `run_experiment.py` | Per-stratum verdict representation | PASS | Binding verdict emitted per survivor row; experiment verdict is OR over `NET_POS` (not a collapsed `.all()`/pooled flag). Companion excess + any aggregate are non-binding. |
| `run_experiment.py` | Determinism | PASS | Seeded per-survivor rng; full second pass fingerprint-compared → `determinism_ok=True`. |
| `run_experiment.py` | Organization / tqdm / plots | PASS | VAL-001 sectioning; dirs only in `main()`; tqdm over load + cost-cell loops; 3 plots from one bounded `to_pandas()`; helpers return data. |

---

## Numerical Validation

### Spot checks (independent reproduction from raw data, manual cost formula — not via `event_costs`)

| Survivor | n (file) | gross_exp | holding_mean | cost_atr_mean | net_exp | net_med | Match |
|---|---|---|---|---|---|---|---|
| USDCAD-4h/RR-1 (NET_POS) | 77 (77) | 1.6568798286 | 7.242424 | 0.31549750 | 1.34138233 | 2.00077377 | **exact (all)** |
| AUDUSD-1h/AVWAP-FH (INCONCLUSIVE) | 988 (988) | 0.9395844290 | 1.958333 | 0.28757270 | 0.65201173 | 0.50408901 | **exact (all)** |

Both reproduce the `cost_readgate.csv` rows to full printed precision. `all holding>0` and `all exit>entry`
True in both. This independently validates the gross reconciliation, the exit-bar mirror, the bar-count
holding proxy, the ATR-unit cost arithmetic, and the net point estimates.

### Reconciliation guards (all three exercised, run completed without HALT)

- **(a) Valid-set hash** — `assert_valid_set` re-derives `sha256(json.dumps({"members": data["members"],
  "holm_rule": data["holm_rule"]}, sort_keys=True, default=str))`; this is byte-identical to EXP-083
  `_freeze_valid_set` (run_experiment L607–617). Independently confirmed it reproduces `fa4035f3…` and
  matches the pin (n_valid=26). PASS.
- **(b) Gross reconciliation** — every survivor's recomputed `n_resolved`==EXP-083 (exact) and mean within
  1e-9 of the pinned `gross_exp`. The two spot-checks reproduce gross to full precision; because
  `make_entrysets`/`_matched_control` seed off `cell_index` (full-grid position), an incorrect grid would
  perturb the entries and break this 1e-9 match — so the pass also **proves the reconstructed cell_index/seed
  grid is identical to EXP-083's**. PASS.
- **(c) Exit-mirror reconciliation** — enforced per candidate (ret 1e-9 + cls exact + mask exact + exit≥0);
  the spot-check confirms exits are valid and `holding>0` everywhere. PASS.

### Range / sanity

| Metric | Expected | Observed | Pass |
|---|---|---|---|
| `n_resolved` per survivor | == EXP-083 | 44–988, all exact | YES |
| `txn_share + fin_share` | = 1 | =1 by construction | YES |
| `holding_days` | > 0 (exit≥entry+1) | min > 0 | YES |
| `cost_atr_mean` | > 0 | 0.15–0.35 ATR | YES |
| `net_matched_excess_lo` | finite | >0 in all 26 (companion) | YES |

---

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

| Stratum (cell) | substrate / n / S2 | per-stratum picture | Agrees with pooled `NET_SURVIVES`? |
|---|---|---|---|
| **AUDUSD-1h** | SUB-HARAMI-V2A / **988** / **S2-PASS** | **4/4 NET_INCONCLUSIVE** — exp_lo 0.057–0.081 > 0 but **med_lo −0.020 to −0.047 < 0** (fails the median leg) | **NO — the only well-powered, S2-adjudicated stratum is NOT a net survivor** |
| NZDUSD-4h | SUB-AVWAP / 77 / **S2-DEFERRED** | 9 NET_POS, 1 INCONCLUSIVE (D3, exp_lo −0.017) | survivors, but shape-unadjudicated |
| USDCAD-4h | SUB-AVWAP / 77 (VP-POC 44) / **S2-DEFERRED** | 11/11 NET_POS | survivors, but shape-unadjudicated |
| USTEC-4h | SUB-AVWAP / 46 / **S2-DEFERRED** | 1/1 NET_POS (RR-1) | survivor, but shape-unadjudicated |

- **Pooled headline:** `NET_SURVIVES`, 21/26 NET_POS. **Is it masking heterogeneity? YES.** All **21 NET_POS
  are S2-DEFERRED low-n 4h SUB-AVWAP cells (n=44–78)** whose separability gate was never adjudicated (n<120);
  the **single S2-PASS, well-powered stratum (AUDUSD-1h, n=988) is NET_INCONCLUSIVE on the median leg in all 4
  cells.** The pooled "net survives" is therefore a disclosure, not a clean tradability signal: **the only
  stratum that passed the binding pre-TEST shape guard does not survive net, and every net survivor is
  shape-unguarded.** This must be foregrounded by the interpreter (Stage 6).

### Mechanism

Why is the headline net-positive when EXP-030/045 were cost-killed? **Gross magnitude dwarfs cost in the ATR
frame, and only in the low-n 4h cells.** The 4h SUB-AVWAP survivors carry gross expectancy 0.74–2.07 ATR
(median 1.2–4.4 ATR) against a cost of only 0.15–0.35 ATR (~15–30% of gross): a fixed price-bps round-trip
divided by a *large* 4h ATR is a small ATR-unit cost (txn_share ≈ 0.40–0.60 on 4h vs **0.72** on the 1h
AUDUSD cell, where the smaller ATR makes the same bps bite harder). EXP-030/045 edges were bps-scale, where
cost was comparable — hence the kill. Here cost is **immaterial relative to the gross magnitude**, so net ≈
gross. Two caveats temper this: (i) the favourable cost/ATR ratio on 4h is partly real (a fixed spread is a
smaller fraction of a larger expected move) and partly a property of the ATR normalization; (ii) these gross
magnitudes sit entirely in **n=44–78 cells whose separability was deferred and whose gross magnitudes the
EXP-083 ASS overlay already flagged as small-n-inflated.** The binding leg that fails AUDUSD-1h is the
**median** (net_med ≈ 0.48–0.50 but med_lo just below 0) — the CF-HA-HARAMI "median-positive-but-not-quite"
signature, now appearing in the only well-powered cell.

### Gate-shape check

- **Binding gate:** co-primary net **expectancy ∧ median**, one-sided bootstrap CI_low. **Effect shape:**
  strongly left-skewed (4h `net_med ≫ net_exp`, e.g. USDCAD/D1 net_med 3.98 vs net_exp 1.17) — the catastrophe
  tail **persists after cost**.
- **Is the gate the wrong instrument for the shape? NO.** Unlike the EXP-074 all-framing consistency gate
  (tail-blind), the **mean leg here is tail-sensitive**: `net_exp` is the mean of net returns *including* the
  catastrophic losers, so requiring `net_exp_lo>0` AND `net_med_lo>0` is an appropriately tail-aware
  conjunction. `net_exp>0` means the mean survives the tail+cost. The gate **sees** the shape; the survivors
  pass it on real magnitude, not by tail-blindness. The genuine limitation is **power/adjudication, not gate
  shape**: at n=77 the bootstrap lower bound on the mean clears zero even with the tail because the gross
  magnitude is large, and S2 (the dedicated shape/separability guard) was never run on these cells (n<120).

---

## Scope Compliance

- Analysis plan followed: **YES**. 2 stat-method families (`one_sided_lo`, `two_sample_diff_lo`, both reused),
  3 plots, 1 new module (`xen.capgeo_cost`) — within budget.
- Deviations: holding-days uses the **operator-ratified bar-count proxy** (Stage-4 decision), within the
  scope's predeclared deferral; not scope creep.
- Holdout exclusion verified: **YES** (first-70% only; `counted_test_reads=0`, `holdout_untouched=True`).

---

## Issues

### Critical
None.

### Warning

1. **Pooled `NET_SURVIVES` masks per-stratum heterogeneity (forensic disclosure).**
   - File: `results/cost_readgate.csv`, `results/valid_net_set.json` (21 NET_POS, all S2-DEFERRED).
   - Description: the read-eligible set is **entirely** S2-deferred shape-unadjudicated low-n 4h cells; the
     only S2-PASS well-powered stratum (AUDUSD-1h) is NET_INCONCLUSIVE. The pooled verdict, read alone,
     overstates the tradability signal.
   - **Materiality: NON-material (cannot move any verdict-bearing number).** The code computed every
     per-survivor verdict and the OR-rule `NET_SURVIVES` exactly per the predeclared scope rule (independently
     re-derived per stratum — same per-cell verdicts). This is an interpretation/disclosure finding for Stage
     6, not a defect requiring a rerun. Fix = the interpreter (results.md) and `valid_net_set.json` must
     foreground that read-eligibility is shape-unadjudicated low-n only (the JSON already notes it "authorizes
     nothing" pending EXP-084 D0).

2. **Small-n expectancy CI under-coverage on n<60 cells (EXP-076/077 family finding).**
   - File: `results/cost_readgate.csv` — VP-POC (USDCAD-4h, n=44), USTEC-RR-1 (n=46); broadly the n=77 cells.
   - Description: EXP-076 found the percentile-bootstrap **expectancy** CI under-covers at small n; EXP-077
     Guard (i) defers expectancy to median at effective n≤60. EXP-085's rule did not invoke Guard (i) (it
     requires BOTH legs).
   - **Materiality: NON-material.** The binding rule requires `net_med_lo>0` as well, and every NET_POS cell
     **also clears the robust median leg** (VP-POC med_lo 1.483, USTEC med_lo 0.782, all 4h med_lo ≥ 0.058) —
     so even discarding the expectancy leg entirely (the EXP-077 small-n recommendation), the same cells pass
     on the reliable median. Requiring both legs is **conservative**, and the small-n expectancy concern moves
     no verdict. Recorded for the interpreter as a power caveat, not a fix.

### Info

1. **`reconciliation_ok` / `exp083_valid_set_assert_ok` in `run_metadata.json` are constants-by-completion.**
   They are hardcoded `True`; correctness is guaranteed because any guard failure raises before metadata is
   written (HALT-on-failure). Cosmetic; consider threading explicit flags in a future revision.
2. **Loads first-70% of all 16 instruments** to reconstruct the EXP-083 cell_index/seed grid (the approved
   `ass_overlay.py` pattern). Only the 4 survivor cells are measured/scored; no non-survivor cell analyzed; no
   holdout read. Intent-compliant; also self-checked by the gross-reconciliation guard.
3. **Catastrophe tail persists net** (4h `net_med ≫ net_exp`); confirms EXP-082's "harvest the median, leave
   the catastrophe" geometry survives the cost overlay — context for any EXP-084 cost-calibrated referee.

---

## Materiality & Re-Audit Requirements

- **0 Critical / verdict-material findings.** No code fix or re-execution required. The two Warnings are
  forensic/disclosure findings explicitly shown above unable to move any verdict-bearing number (the per-cell
  verdicts and the `NET_SURVIVES` call were independently re-derived per stratum and reproduce exactly; the
  small-n expectancy concern is overridden by the conservative both-legs rule + robust median leg).
- **Re-audit: not required.** The binding obligation passes to Stage 6: `results.md` must report the verdict
  **per stratum** and foreground that the 21 read-eligible survivors are all S2-deferred shape-unadjudicated
  low-n cells while the only S2-PASS well-powered stratum is net-inconclusive — i.e. the pooled NET_SURVIVES
  is not a clean tradability signal and gates only an operator G-018 read decision (it authorizes nothing
  itself).

**Audit verdict: PASS** (0C / 2W / 3I).
