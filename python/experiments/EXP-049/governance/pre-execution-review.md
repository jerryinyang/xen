# EXP-049 — Pre-Execution Governance Review

**Phase 014-A · `CF-HA-HARAMI-001` / HYP-002 · 3-Barrier Capture Readiness & Gross
Capture Rate.** Reviewed artifacts: `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, `python/src/xen/capture_barriers.py`. Checked against the
bundled governance constraints, the developer code conventions, and the active
checkpoint `design.md` (§6/§8/§10) + `D0-predeclarations.md` (P1–P5, P11–P12).

```text
VERDICT: APPROVE
```

## Constraint checks

| # | Constraint | Result |
|---|---|---|
| 1 | Simplicity over complexity | **PASS** — cheapest decisive gross read (favourable-before-adverse). MBB bootstrap justified over i.i.d./Wald with the simpler alternative documented and rejected for serial dependence. Budget: 1 test / 4 plots / 1 module — matched exactly in code. |
| 2 | No academic-finance pitfalls | **PASS** — non-parametric block bootstrap; no normality/i.i.d./stationarity-strong/constant-vol assumption; null `r=0.50` is structural (symmetric 1:1 barriers), not distributional. |
| 3 | Strict scoping | **PASS** — single capture-geometry hypothesis (readiness + rate, the EXP-020/043/048 primitive-readiness pattern); boundaries, exclusions, and concrete verdicts (CAPTURE_READINESS_DELIVERED / BARRIER_REFUTED / NOT_VIABLE_BY_POWER) all explicit; no bonus analyses. |
| 4 | Framework principles | **PASS** — data-driven, non-parametric, real-price discipline; HA detector not imported; alignment by `CloseTime` (`confirm_indices` epoch searchsorted); forward window is index math *within one fenced real-bar frame*, not a cross-view bar-index comparison. |
| 5 | OOS holdout | **PASS** — F01 prefix loader reads metadata row-count then `slice(0, train_rows)` (first 49%); full file never sorted/collected; TEST and final-30% holdout never read; every domain bar fenced to `CloseTime ≤ train_end_ts`; forward windows clipped to `n_bars-1`. `inv_window_fence` re-asserts the frame fence. |
| 6 | Look-ahead prevention | **PASS** — barrier thresholds use only the just-confirmed move and durations of moves confirmed **strictly before** the event; forward scan strictly after `ConfirmIdx`; ZigZag is the frozen causal streaming generator; `inv_causality` checks strict confirmation monotonicity. |
| 7 | Real-price discipline | **PASS** — all barriers/excursions on real domain OHLC; no HA/Renko price in any metric (gross, exit-agnostic; the harami detector is absent from EXP-049). |
| 8 | Safe performance/memory | **PASS** — lazy scan + projection; per-cell bounded memory (frames not retained across cells); bootstrap batched at 2,000; plots from collected summaries (no reloads); `tqdm` on the instrument outer loop; first-touch scan and ZigZag kept explicit/sequential (causal semantics preserved). |

## Code-convention checks (developer conventions)

Import side-effect freedom (verified: results dir not created at import) · output
dirs created only in `run()` · lazy F01 slicing with no pre-split full-file
sort/collect · no silent `.unique()` dedup · bounded 4 plots from summaries · VAL-style
sectioning · `logging` with concise `main()` summary · helpers return data · `tqdm`
present · deterministic seeds (frozen `BASE_SEED`, per-cell spawned RNG, deterministic
block length) with a determinism replay comparing classes + CI exactly · zero-baseline
finite (`resolved<30 → NOT_VIABLE_BY_POWER`; `defined=0 → None` fractions; `r=None`
when `resolved=0`; degenerate resamples discarded + disclosed) · type hints/docstrings ·
functions ≤ ~30 lines · 0 lines > 100 chars · `py_compile` clean · synthetic unit tests
of geometry/resolution/tie-break/warmup/bootstrap pass.

## Design / D0 alignment

- **§10 routing not self-adjudicated:** the script emits the P12/P11 readout
  (`composition_readout.json`) and explicitly records that PROCEED_TO_SCREEN vs
  CHARACTERISED_NOT_VIABLE is the desk-level G1 adjudication. ✓
- **P1–P5 barriers implemented verbatim** (Wilder ATR-14/`ATR_MULT=1.0` via frozen
  `xen.zigzag`; 50% favourable; 1:1 adverse; adaptive `N=max(6,round(1.5·median(trailing-20
  durations)))`; `LOOKBACK=1`). **P12/P11 thresholds verbatim** (`r≥0.55`, one-sided
  bootstrap `CI_low>0.50`, `resolved≥30`; `≥5 cells/≥3 instruments`). ✓

## Info notes (non-blocking; flagged for the Stage-5 auditor)

1. **Binding precondition for the execution gate:** EXP-049 cell membership = EXP-048
   READY ∪ READY_FLAGGED, read from `EXP-048/results/readiness_map.csv`. EXP-048
   currently has `results/` but is **not yet audited/closed**. Per `scope.md`, the
   manual execution gate is **blocked** until EXP-048 reaches READINESS_DELIVERED +
   audit PASS. This is a sequencing precondition, not a code defect.
2. **Two favourable geometries, G1 binding:** the scope designates G1 (distance-based)
   as the predeclared **primary/binding** for P12 routing and G2 (retracement-level)
   as a disclosed secondary, per the operator's pre-data "test both, nothing frozen"
   decision. Both `r` values and both composition readouts are emitted; the G1-primary
   designation is justified (P3 1:1 coherence, no degeneracy) and disclosed. The
   auditor should confirm G1 remains the binding readout and G2 stays non-binding.
3. **P4 trailing-window reading:** "trailing 20 confirmed moves" is implemented as the
   durations of moves confirmed **strictly before** the event (the event's own move
   excluded), `<5` available → warmup-excluded — the literal reading of D0 P4
   ("measured strictly on moves confirmed before the signal"). Auditor to confirm
   against D0 intent.
4. **Compound readiness+rate question** is acceptable under the primitive-readiness
   pattern (EXP-020/043/048) and is one hypothesis (HYP-002), not scope creep.

No Critical or Warning issues. Scope, plan, and code are internally consistent,
causally safe, holdout-clean, real-price-disciplined, and within budget.
```text
VERDICT: APPROVE
```
