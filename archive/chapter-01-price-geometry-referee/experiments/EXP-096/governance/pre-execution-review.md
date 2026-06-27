# EXP-096 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-096 — Noise Infusion: Realistic 1-Minute Entry Fill (RSI-2 Fade Portfolio, 8 cells)
**Phase:** 022 · **Family/HYP:** `CF-MR-001`/`HYP-003` · **Date:** 2026-06-25
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/intrabar_fill.py`
(entry-side extension) · **Governing:** Phase-022 `design.md` §3-4/§8, `D0-predeclarations.md` §D1/§D5/§D7/§D9,
`D0-amendment-001.md` (A1-A4 inherited).

---

## Verdict

```text
VERDICT: APPROVE
```

All governance constraints pass. No Critical or Warning issues. The one item D0 explicitly defers to Stage 4 —
the read-accounting classification of the entry-fill re-resolution — is **ratified as a disclosure** below.

---

## Read-accounting ratification (D0 §D7 — required at this gate)

D0 §D7 states: *"EXP-096 re-resolves the entry-fill leg of the 8 cells on the analysis-TEST series under a new
fill model. This is a robustness re-derivation of an already-spent read under a perturbed execution model — same
cells, same selection, no new stratum-specific claim (the EXP-085 cost-re-resolution precedent) ⇒ disclosure,
not a new counted read. Confirmed at pre-execution governance."*

**RATIFIED — disclosure, not a counted read.** Verified: (i) the 8 cells are exactly the EXP-093 carried set
(subset of 11, each at **1/2**); (ii) the exit resolution (`res.fill_price`/index/`keep`) is reused verbatim —
only the entry execution price changes (`resolve_cell_noise`), so there is **no new per-stratum selection or
inference**; (iii) `run_metadata.json` asserts `counted_test_reads=0`, `candidate_slots=0`,
`holdout_untouched=true`; (iv) the final-30% global holdout (incl. 1-minute bars) is never sliced
(`load_analysis_1m` slices `[0, int(total·0.7))`, fill walk clipped at `train_edge_epoch`). **11 carried strata
stay 1/2; 37 stay 0/2.** Multiplicity registry has EXP-096 `PLANNED` with the v1/v2/v3 ladder entered at frozen
values; family `CF-MR-001` is `ADMITTED`/`TRADABLE`. Stage-1 precondition satisfied.

---

## Constraint checks

### OOS holdout (§5) — PASS
`load_analysis_1m` (reused from EXP-095) lazy-slices the first 70% only; the entry-fill `searchsorted`+scan is
fenced at `train_edge_epoch`; `EntryFill` masks any event whose post-signal window crosses the fence
(`available=False`). `run_metadata` asserts `holdout_untouched=true` + max-touched `CloseTime` < analysis edge.

### Look-ahead / causality (§6) — PASS
Entry fill consults only 1-minute bars with `CloseTime ∈ (signal_close, train_edge]`. Two binding asserts:
`causal_entry_fill_assertion` (perturbing a pre-signal 1m bar leaves the fill unchanged — verified to raise
otherwise) and `causal_weight_assertion` (future per-cell returns cannot enter a past weight). All cross-domain
alignment is by `CloseTime` epoch / `searchsorted`, never bar index.

### Real-price / synthetic-price discipline (§7) — PASS
Entry and exit fills are real touched 1-minute prices; returns in ATR units off real OHLC. No HA/Renko prices in
any metric.

### Pure entry-leg perturbation (the structural correctness check) — PASS
Confirmed in the engine: the EXIT-RCT target (`P*` from the signal-bar close + Wilder state) and adverse stop
are built from the signal close and are **frozen**, so `resolve_exit_paths` outputs are identical under noise
and are reused verbatim. Only `entry_fill` changes via `net_return_atr(fill_price=exit_fill,
entry_close=entry_fill(v))`. **Keep-mask invariance** is enforced (provenance `count_match` vs EXP-093 +
`n_entry_unavailable_on_keep==0` raises). Cost notional pinned to the signal close (identical to EXP-093, not
double-counted by the slippage) — exactly as the plan specifies.

### MTM conservation (amendment-001 A1) — PASS
`conservation_check` asserts Σ(intra-1h marks) == realized net(v2) per cell ≤1e-9; `mtm_marks` also pins the
per-position total and raises on breach. The first mark increment is booked from `entry_fill(v2)` so the noise
flows through the path correctly.

### Per-stratum doctrine / shape-aware reads (analysis-plan checks) — PASS
The binding estimand is the **portfolio** (D0 design decision; a genuine combined return stream, not a collapsed
`.all()` over per-cell verdicts) with **per-cell disclosure alongside** (LESSON-001): per-cell degradation
ladder + per-cell baselines + `NOISE_DEGRADED` flags (flag-only, no mechanical drop — operator membership
decision). The benefit read is **like-for-like LB vs the cross-cell-median single-cell LB** (per-stratum-aware,
deployment-realistic), not an ex-post-max. Shape covered: per-cell mean **and** median; co-binding **Calmar LB**
+ CVaR₅/Ulcer alongside the location Sharpe. No collapsed binding verdict.

### Gate-threshold calibration (scope check) — PASS
No magic constants. m* (1.75/2.00) is **inherited** from EXP-095's calibrated A4 MDE-curve (operator decision,
not recomputed under noise). The `NOISE_DEGRADED` flag threshold = EXP-093 per-cell **data-derived margins**.
Slippage 0.05×ATR and k=3 are **D0-frozen**, with v1/v3 the **disclosed sensitivity bracket**; cov {60,90,120}
is disclosure-only. Optional FPR sanity uses the `block_permute_zero_mean` (null_b) form — not a path rotation,
not built around a signal-derived target (`falsification_null_design`).

### No optimization / single hypothesis / simplicity (§1-3) — PASS
One falsifiable question (does the diversification benefit survive realistic entry execution). All hyperparameters
D0-frozen; brackets disclosure-only; binding variant v2. Simplest correct approach: reuse EXP-095's construction
verbatim (imported as a module) and add only the minimal causal entry-side fill. No scope expansion.

### Academic-finance pitfalls (§2) — PASS
Non-parametric moving-block bootstrap (serial dependence preserved); the Sharpe normality/upside pitfall is
reconciled by the MBB lower bound + co-binding downside metrics (documented in the plan).

### Code quality / organization (code checks) — PASS
Sectioned (imports → path setup → constants → types → I/O → pure computation → plotting → orchestration →
`main()`); output dirs created in orchestration only; no import-time side effects; `tqdm` on cells/variants/null
loops; concise logging; NaN/zero-baseline guarded (NaN not inf); seeds off master `20260624`; determinism replay
asserts byte-identical. Compiles; `resolve_entry_fills` unit-tested (v1/v2/v3, causality, fence, edge-clip);
module import + E95 wiring verified.

### Complexity budget — PASS
2 binding tests (v2 noise survival + v1/v2/v3 ladder) / ≤2; 5 plots / 5; 0 new modules + 1 small `intrabar_fill`
entry-side extension / ≤1. Gate statistic inherited (m* not recomputed).

---

## Info notes (non-blocking)
- **I1 — cost notional under noise.** Cost uses the signal-close notional for all variants (plan-specified;
  keeps cost byte-identical to EXP-093 and avoids double-counting the slippage). Faithful; not verdict-bearing.
- **I2 — `ideal` 4th variant.** An internal cross-check (reproduces EXP-095) + the plan's required idealized
  equity overlay + the provenance reference. Not scope creep; the provenance gate HALTs on any drift.
- **I3 — FPR sanity is disclosure-only and skippable.** m* is inherited; the sanity confirms noise did not break
  FPR control but does not re-gate readiness (operator decision).
