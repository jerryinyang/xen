# Pre-Execution Governance Review — EXP-089 (AMENDED, D0-amendment-001)

**Experiment:** EXP-089 — CF-MR-001 Mean-Reversion Entry Availability Screen (Phase 020), **as amended by
`D0-amendment-001`**.
**Artifacts reviewed:** `scope.md` (bannered), `analysis-plan.md` (revised), `code/run_experiment.py` (rewritten),
the amended modules `xen.mean_reversion` (MR-tempo cap added) / `xen.vol_regime` (reduced to labeller +
regime-matched draw), and the reverted single-test `bite-check/bite_check.py`.
**Reviewer:** research-pipeline consolidated Stage-4 governance.
**Date:** 2026-06-23.

> **Supersedes** the prior pre-execution review (which approved the now-voided first run). The first run was a
> deviation (audit C-1/C-2); its results were hard-deleted. This review governs the amended rerun.

---

## What the amendment changes (and why it is in scope)

`D0-amendment-001` corrects the **operationalization** of the same single question after audit found two
verdict-material confounds of the frozen design. Three changes; everything else frozen:
1. **MR-tempo cap** (fixes C-2) — the trend-length MA-segment adaptive cap → a causal RSI-2
   reversion-episode-tempo cap.
2. **Regime-matched + horizon-matched control, leg-2 retired** (fixes C-1 + parity) — `/VOLREGIME` controls
   drawn from same-regime bars; the beats-CORE conjunction and regime-membership null removed.
3. **All 6 sub-screens single-test** through `run_sub_screen` → `combine_axis` (joint max, no Holm).

This is a faithful in-place amendment (dated `D0-amendment-001`, `scope.md`/`D0-predeclarations.md` bannered),
**not** scope expansion: the question, 46-cell member set, multiplicity budget (6 sub-screens), registry
(0 slots, 0 counted TEST reads), and TRAIN-only accounting are unchanged.

## Constraint checks

### Scope / amendment provenance
- **Single question / boundaries / criteria:** PASS. One falsifiable availability question; verdict
  `SCREEN_DELIVERED`, admit/exonerate at G-020.
- **Amendment governance:** PASS. Dated `D0-amendment-001` is authoritative; the frozen D0 and scope carry
  banners; no new countable registry item.
- **Complexity budget:** PASS, and reduced — 1 binding test (the joint-max gate), 4 plots, 2 modules. Retiring
  leg-2 removes a per-cell test and a null, simplifying.
- **Gate-threshold calibration:** PASS. The binding gate reverts to the **single-test joint-max-of-6** structure
  already bite-GREEN at sha `f01a000b…` (D0 checks A–D). The new **MR-tempo cap constants**
  (`K_MULT=1.0, W=20, MIN_EPISODES=5, FLOOR=3, CAP_MAX=40`, episode close at RSI 50) are pinned pre-data with
  structural justification (mirroring the retired cap's `WINDOW=20`/`MIN_MOVES=5`; `K_MULT=1.0` = one reversion;
  RSI-50 = the parameter-free neutral midline already used by the FILTER variant), recorded in
  `frozen_constants.mr_tempo_cap`, and — because the deviation results were deleted before the amendment — could
  not be tuned against realized availability. No unjustified magic constant.

### Analysis plan
- **Method justification / assumptions / per-stratum / interpretation guide:** PASS. Each amended step carries
  "why" + "simpler alternative considered"; the C-1 cancellation argument (within-regime entry-ATR cancels) and
  the horizon-parity-by-construction argument are stated; per-cell beats-random is per stratum; every pooled
  figure is disclosure-only (LESSON-001); the if-X-then-Y guide is predeclared, with a `/VOLREGIME` argmax now
  read as *regime-dependent MR edge*.
- **Shape-aware read:** N/A by scope (directional location family; magnitude is the closed CF-VOLEXP-001
  surface, not reopened). The directional median is the predeclared location read.
- **Budget compliance:** PASS.

### Code (`run_experiment.py` + modules) — verified (compiles, imports resolve, synthetic primitives pass)
- **Plan compliance:** PASS. Implements exactly the amended plan; no bonus analyses; leg-2 fully removed.
- **Holdout exclusion:** PASS. `load_first70` materializes only the analysis set; `train_cutoff =
  int(int(frame.height)*0.7)` is the nested TRAIN; forward windows clip at `n_bars`; all random/regime/pool
  draws are within the TRAIN frame.
- **Look-ahead bias:** PASS. RSI(2)/RSI(5)/EMA(20)/ATR(14) and the rolling-50 regime percentile are causal; the
  **MR-tempo cap uses only reversion episodes closed strictly before the entry** (`searchsorted(..., "left")`,
  confirmed by synthetic test: strict-before count monotone, warmup before `MIN_EPISODES`); `lifetime_path_geometry`
  reads `[i+1, i+cap]`.
- **Real-price discipline:** PASS. All MFE/ATR/regime/episode tempo on real domain OHLC (`_real_ohlc`); no
  synthetic price.
- **Regime-matched control integrity:** PASS. The `/VOLREGIME` control and pool are drawn from same-regime bars
  (`regime_matched_entries`), count+direction matched; a per-cell guard asserts every drawn control/pool bar
  carries the matching regime label (`regime_match_recon_ok`). Synthetic test confirms draws stay in-regime and
  distinct. This is the mechanism that removes audit C-1 (entry-ATR cancels within-regime).
- **Type safety / NaN / edge cases:** PASS. Type hints on public functions; degenerate cap stats → NaN; NaN SE
  → beats=False; empty arrays guarded; add-one permutation p.
- **Verdict representation (per-stratum):** PASS. No collapsed cross-cell PASS/FAIL is binding; the provisional
  family disposition is captioned **NON-BINDING — pending G-020**; per-cell and per-sub-screen statistics emitted.
- **Organization / sectioning / import side effects / logging / tqdm / determinism / safe optimization:** PASS.
  VAL-001 sectioning; dirs created only in `main()`; concise logging; `tqdm` on the cell loop; fixed master seed
  `20260623` with a byte-identical-fingerprint second pass (cells + gate stream); vectorized cap-by-count map +
  bounded sequential episode/RSI scans preserve causal semantics; `adaptive_time_caps_by_epoch`/`_ma_segment_moves`
  no longer used.

### Signal-registry / multiplicity
- PASS. CF-MR-001 unchanged `REGISTERED — FROZEN, G0-RATIFIED`; 6 sub-screens; **0 slots, 0 counted TEST reads**;
  all 48 strata `0/2 open`; `test-read-ledger.md` unchanged. `run_metadata` records `counted_test_reads=0`,
  `candidate_slots=0`, `holdout_untouched=true`, `amendment="D0-amendment-001"`.

### Bite-check precondition (amended)
- **SATISFIED by design.** Retiring leg-2 returns the gate to the single-test joint-max-of-6 already GREEN at
  `f01a000b…`. `bite_check.py` has been **reverted** to the A–D single-test scope (Part E + `vol_regime` imports
  removed; E ran last, so A–D RNG draws and report are unchanged → a re-run reproduces `f01a000b`). The MR-tempo
  cap and regime-matched control are **upstream geometry** (they change the MFE arrays fed to the gate, not the
  gate null calibration); integrity is enforced by the run's reconciliation guards, not the gate bite.
- **Binding manual-execution-gate instruction:** the operator must **re-run the reverted `bite_check.py` first**,
  confirm `OVERALL: GREEN` and that `bite_check_report.json` hashes to `f01a000b…`, then run the experiment.
  `run_metadata` records both the on-disk bite sha and `bite_expected_single_test_sha256 = f01a000b…` for the
  post-run audit to verify they match.

## Documented methodology decisions (recorded, non-blocking)
1. **MR-tempo cap = a single cell-level reversion clock** (both directions, median of last 20 completed
   episodes), applied identically to signal/control/pool — the parity mechanism (no resampling). Faithful to the
   amendment; not a scope change.
2. **`D2A_NULL_BAND=(17,29)` retained** as the EXONERATED coin-flip band (unchanged from D0); the beats-random
   noise ceiling 5 is the descriptive reference. Unchanged disposition semantics.

---

## VERDICT

```text
VERDICT: APPROVE
```

The amended scope, plan, and code pass all scope, plan, code, holdout, look-ahead, real-price, regime-matched
control integrity, per-stratum, registry, and complexity-budget checks; both audit findings (C-1, C-2) are
addressed by design; the gate reverts to the GREEN single-test structure. No Critical or Warning issues.
Cleared for the manual execution gate, conditional on the operator re-running the reverted bite-check to a GREEN
`f01a000b…` report before the experiment run.
