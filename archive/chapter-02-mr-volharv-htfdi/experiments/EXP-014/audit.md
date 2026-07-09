# Audit Report: Experiment EXP-014 — CF-MR-004 / HYP-002 (faithful full-exit cross-instrument MR)

## Summary

- **Verdict**: PASS (verdict trustworthy; no fix+rerun required)
- **Critical Issues**: 0
- **Warnings**: 2 (both interpretation-framing, non-verdict-moving — routed to Stage 5)
- **Info Notes**: 3
- **Binding result audited**: **NOT_TRADABLE** — PRIMARY arm (none/R), 38 strata, **0/38 net-admit, 0/38 gross-admit** under the frozen 4h referee (`referee_pstar.gate_stack_pstar`, q\*=0.75), per stratum. Homogeneous, no masking.
- **Faithfulness confirmed (L-14 discharged)**: the two proposal-named exits **fired** — form-1 event-reversion 281, form-2 refreshing-limit 1898, horizon 1266 (primary arm). This is a verdict on the *faithful* strategy, not the EXP-013 vehicle-incomplete confound.

Execution: 152/152 cells (4 series × 4 arms), 0 harness failures. Binding adjudication on none/R only (design §9); none/S (A/B), allow/R, extend/R emitted for disclosure.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `Xen.cs` native block | Correctness | PASS | Multi-leg engine: leg list keyed by Position.Id; form-1 (`sc=logClose−anchorLog`, short sc≤0 / long sc≥0), refreshing form-2 (`ModifyTakeProfitPrice` each bar, favorable-asserted), horizon; reentry none/allow/extend; A/B static-arm gates ENTRY only (form-2 refresh runs in both arms — verified). |
| `Xen.cs` `ApplyEventExits`/`RefreshForm2Targets` | Causality | PASS | Exits act on completed bar i at open of i+1 (open-to-open); forming-bar OHLC never read; engine enforces by construction. |
| `CrossInstrumentSpreadPlanner.cs` | Correctness | PASS | S8 F-fix applied (`MedianW=90`, basket feed via conf mates). VR/HL/OLS from-scratch, standard formulas. |
| `CrossInstrumentBasketFeed` (Xen.cs) | Correctness | PASS | Exact-CloseTime, no carry-forward; `LastMateCount`/`ExpectedMates` drive the min-mate rule; gap → no new arm (β/anchor fixed). |
| `SignalRecords.cs` / `StrategyRunParquetWriter.cs` | Correctness | PASS | 18 new per-bar cols + `CisTradeRecord`/`cis_trades.parquet`; sentinels keep other models byte-unchanged. |
| `lib.py` | Correctness | PASS | `assemble_realized_bps` = engine-fill open-to-open + RT cost once/entry; reuses frozen referee wrappers untuned. |
| `mr_characterisation.py` | Correctness | PASS | 6-stage screen (VR/HL reuse xen; ADF/KPSS from-scratch, informative); native estimands via `reversion_targets`; dislocation-matched control. |
| `run_experiment.py` | Correctness | PASS | Per-leg split, referee adjudication (none/R), Holm, phase-shift + bite-check. Deterministic seed 20260702. |
| all Python | Holdout exclusion | PASS | Reads only emitted TRAIN runs under the fence; final-30% never touched. |
| all Python | Organization / side effects | PASS | dirs created in `main()`; lazy/ingest reads; no import-time effects. |

## Numerical Validation

### Spot Checks (independent re-derivation — fresh code, not `lib`)

Re-computed per-bar NET bps from raw `positions.parquet` with independently-written open-to-open assembly:

| Cell | independent net (bps/active) | verdict.json `net_mean_bps` | Δ |
|---|---|---|---|
| S5:EURUSD | +0.307 | +0.313 | 0.006 |
| S7:US2000 | +0.845 | +0.861 | 0.016 |
| S8:US500 | −1.354 | −1.405 | 0.052 |

Match to within ≤0.05 bps (residual = `net!=0` vs `pos!=0` denominator nuance). Assembly reproduces. **(Numeric reproduction is necessary, not sufficient — see Causal-Provenance section.)**

### Range / sanity

| Metric | Expected | Actual | Pass |
|---|---|---|---|
| Position | {−1,0,+1} | {−1,0,+1} | YES |
| exit-fill in [Low,High] | ≥95% | S5:EURUSD 52/52; S8:US500 272/274 (0.7% isolated) | YES |
| MateGap frac | ≈0 | 0.0004 (FX) / 0.0019 (IDX) | YES |
| n_episodes | ≥ floor 8 to power | 12–57 (all 38 ≥ 8) | YES |
| net ci_low (referee) | — | all 38 < 0 | consistent w/ 0 admit |

## Verdict Forensics

### Per-stratum re-derivation & masking check

Re-derived per stratum (38 cells). **Every cell**: referee `passed=False` on gross AND net; `ci_lower_bps < 0`. Per-series powered (L1-readiness ∧ episodes≥8) / net-Holm-admit: **S5 8/0, S6 3/0, S7 7/0, S8 6/0**.

- Pooled headline (0/38 admit) **is not masking heterogeneity**: an independent sweep for any cell with `net ci_low > 0` returns **NONE**. No separating stratum is hidden by the aggregate (L-03 satisfied). The read is homogeneously null across all series, instruments, and FX-vs-index classes.

### Mechanism (why 0 admit)

Not a single binding leg — a **capture-vs-dispersion** failure. The faithful exits fire (form-2 refreshing limit is the dominant exit, 1898/3445 trades; horizon 1266; form-1 281), so positions DO exit on both price-side and peer-side reversion (the EXP-013 defect is gone). But:
1. **Availability does not separate** — native reversion-completion Δ (reach-anchor / fraction-recovered) vs the dislocation-matched control has `ci_low < 0` on ~all 38 cells (a few +point estimates ≤ +0.036, all CIs cover 0). Among equally-dislocated bars the screen does not pick better reversion at 4h.
2. **Per-trade P&L is a dispersed wash** — `cis_trades.RealizedBps` ranges −57 to +29 bps/trade per cell; several cells are positive per-trade (S7:US2000 +28.6, S7:AUDUSD +23.5, S5:NZDUSD +21.4) yet net `ci_low<0` because the dispersion swamps the mean. The capturable reversion is not reliably larger than the round-trip cost (same cost/capture veto that closed CF-MR-002 and CF-MR-003).

### Gate-shape check

- Binding gate: frozen 4h `gate_stack_pstar` (§10.3a validity→economics, per-bar mean-stat with neutral-CI + materiality + studentized sub-pop). Effect shape here: a **discrete, high-variance round-trip bracket** (few episodes, ±hundreds-of-bps per trade).
- **Gate-shape mismatch present (bite-check evidence).** A planted +8 bps/active edge is detected in only **19/38** cells; the 19 bite-FAILING cells are concentrated in high-cost indices (US500/USTEC/JP225/US2000, cost 3–5 bps) and low-episode FX. For those cells the per-bar mean-referee has **no finite power at +8 bps**, so its rejection is *non-informative* (an "unpowered", not an "effect-absent", read — L-12 mode-2). This is exactly the vehicle-fit risk flagged in amendment §7 (a per-bar/episode referee may misfit a discrete round-trip bracket). **Not retro-edited** — recorded for the interpreter. The per-trade disclosure lens (`cis_trades`) is the co-emitted cross-check and shows the same dispersed-wash picture.

## Causal Provenance & Leak

### Provenance trace (verdict-bearing columns)

| Column | Inputs & timestamps | ≤ t (≤ t-1 next-bar)? | Location |
|---|---|---|---|
| `Position` (dir) | armed from planner bracket rested through bar i (≤ i), entry filled intrabar in period i+1 | YES | `Xen.cs` `RearmBracket`/`OnNativePositionOpened` |
| `EntryFillPrice` | cTrader m1 engine fill of a limit rested from ≤ t-1 | YES (engine-realized) | `OnNativePositionOpened` `pos.EntryPrice` |
| `ExitFillPrice` | engine fill: form-2 limit (favorable) / form-1+horizon market at next open | YES (engine-realized) | `OnNativePositionClosed` `ClosingPriceOf` |
| `Anchor`/`Dev`/`Sigma`/`SpreadMean` | planner state through completed bar i | YES | `EmitNativePosition` from `_lastBracket` |
| net bps (Python) | `RealOpen[i]`, `RealOpen[i+1]`, engine fills | YES (open-to-open) | `lib.assemble_realized_bps` |

- `rct[di]`-style use of a bar's own close as its intrabar limit? **NO.** All limits rest from the ≤ t-1 bracket; fills are the engine's.
- Every decision at the action bar's **open** on confirmed bars only, forming-bar OHLC unread? **YES** (C# `OnBar` streaming + the m1 backtester own resolution).
- Returns **open-to-open**? **YES** — `pos·log(next_open/open)` with fills substituted at trade ends; no open-to-close.
- Fence: max emitted `SourceCloseTime` < `AnalysisEndUtc` on spot cells (S5:EURUSD, S8:US500); final-30% never processed (`HoldoutFence.AssertCanEmit`).

### Leak tripwire

- Future-destroying controls shipped: (T1) peer-feed phase-shift (`--BasketPhaseShiftHours`, re-adjudicate a decorrelated-basket twin), (T2) label-permutation, each gated by a planted-positive bite-check (§10).
- Edge collapsed under it? **Moot — 0/38 admit, so no live edge to destroy.** Correctly handled: T1 phase-shift twins were not generated (only needed on an admit); `tripwire=None` recorded (not a false pass). T2 label-perm is correctly flagged **mean-invariant / vacuous** for the mean-stat referee (a permutation cannot move a mean → cannot collapse it; memory `permutation_destroy_mean_invariant`, EXP-012 precedent) — reported, **not gating**. The binding future-destroy remains T1 (a genuinely different emission), to be exercised only if a future cell admits.

### Shared-module provenance contracts

- `reversion_targets` (`measure_entry`/`event_target_metrics`) used with caller-lagged `[i-1]` anchor/dev per its docstring contract — verified in `mr_characterisation.reversion_completion` (`dev_lag=np.roll(dev,1)`, `a_lag=anchor[:-1]`). `referee_pstar`/`referee_adaptive` byte-unchanged (frozen, hash-pinned E7) — untuned (L-12).

### Price-primary check

- Edge-generating experiment ran **in the cTrader engine** (`data/strategy_runs/EXP-014-*/`, Mode=NativeOrders, m1 fills) under the fence — **not** a vectorized Python backtest. Python is analysis-only. Binding-leg RT cost charged once per entry from the frozen per-instrument 4h cost map (L-02). ✓

## Scope Compliance

- Analysis plan followed: **YES**. Deviations: none (form-2 refresh correctly decoupled from the A/B static-arm — a fix, not a deviation).
- Complexity budget: 4 tests (availability Δ + referee + 2 tripwires) / 4; 4 plots / 3–5; C#+Python modules — within envelope.
- Holdout exclusion verified: **YES** (first-49% AnalysisEndUtc fence reused from EXP-013; final-30% never loaded).
- Reads/slots: **0 counted TEST reads, 0 candidate slots**; ledger unchanged; frozen referee untuned.

## Issues

### Critical
None.

### Warning

1. **Availability (reversion-completion) does not clearly separate from matched-random — qualifies "credible NOT_TRADABLE".**
   - File: `results/mr_characterisation.json`; `mr_characterisation.reversion_completion`.
   - Description: native reach-anchor/fraction-recovered Δ vs the dislocation-matched control has `ci_low<0` on ~all 38 cells. The design's "credible NOT_TRADABLE" (design §12) presumes "availability real"; here it is at best weakly/not established at 4h.
   - Materiality: **does NOT move the verdict** (tradability is 0/38 admit regardless) or any verdict-bearing number — it bounds *how much* the null reinforces the terminal-branch prior. Route to Stage 5 (quant-analyst/documenter) to frame the disposition as "faithful full-exit is a net wash AND availability itself does not separate at 4h," not "availability real but uncaptured." No rerun.

2. **Per-cell referee power is heterogeneous — 19/38 cells are bite-failing (UNPOWERED, not effect-absent).**
   - File: `results/verdict.json` `bite_check`; `run_experiment.bite_check`.
   - Description: planted +8 bps detected in only 19/38 cells; the other 19 (high-cost indices + low-episode FX) have no finite power at that effect size, so their `passed=False` is non-informative.
   - Materiality: **does NOT move the verdict** — the credible-null rests on the bite-passing powered subset, and *those* also reject (all `ci_low<0`); it does not change sample membership, denominators, causality, or which stratum binds. It qualifies interpretation strength (per-cell POWERED-vs-UNPOWERED). Already computed + disclosed per-cell. Route to Stage 5. No rerun.

### Info

1. **Isolated exit-fill breaches** — S8:US500 2/274 (0.7%) exit fills outside [Low,High], well under the 5% systematic threshold (`lib.SYSTEMATIC_BREACH_FRAC`); benign session-gap/spread fills of a resting limit armed causally. Reported, non-material.
2. **Disclosure arms emitted** — none/S (A/B), allow/R, extend/R all ran (152 cells); per-leg breakdowns in `verdict.json.disclosure_legs`. Not binding; available for the documenter's exit-leg / reentry / R-vs-S analysis.
3. **Harness infra fix** — `run-experiment.sh` `prepare_cache_layout` `ln` made race-tolerant (EXP-006 O3 op-note) to support bounded-concurrency `one`-mode dispatch; pure infra, no logic/causality/fence change.

## Materiality & Re-Audit Requirements

- **No Critical findings → no fix+rerun.** The binding verdict (NOT_TRADABLE, 0/38 admit, homogeneous, causally clean, faithful exits fired) is trustworthy and stands.
- Both Warnings are **interpretation-framing** and shown not to move any verdict-bearing number (the tradability read is 0-admit under every power/availability lens); they are routed to Stage 5 so the documenter frames the disposition with the correct strength (faithful-but-net-wash; availability-not-separating-at-4h; per-cell power caveat) rather than overclaiming a "clean powered terminal-branch reinforcement."
- **Verdict-forensics + causal-provenance/leak pass: complete.** Numeric reproduction confirmed AND mechanism explained AND provenance traced — the audit is not certified on numbers alone.
