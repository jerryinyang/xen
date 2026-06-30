# Audit Report: Experiment EXP-006 — D-benchmark, causal RSI-2 fade (CF-MR-002/HYP-001)

## Summary

- **Verdict**: **PASS** (0 Critical) — the 34/34 NOT-TRADABLE result is trustworthy, causal, and
  leak-clean; the honest prior (L-01: causalized the bare fade is net-negative) is confirmed across
  the full 17×{1h,4h} universe.
- **Critical Issues**: 0
- **Warnings**: 1 (frozen gate-A coverage gap — shown non-material)
- **Info Notes**: 4 (infra-bug findings fixed mid-run [O3]; returns-space caveat does **not** bind here;
  gate-shape clean; complexity within budget)

Classification: **price-primary, analysis-only adjudication side.** Edge generated in the cTrader
StrategyHost (`RsiFadeModel`), emitted to `data/strategy_runs/EXP-006/` under the per-symbol
`AnalysisEndUtc` fence; Python ingests/validates/adjudicates only. No vectorized price backtest.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `StrategyHost/RsiFadeModel.cs` | Correctness (Wilder/RSI/P*) | PASS | Wilder seed = mean of first `period` deltas then `(avg·(p−1)+x)/p`; RSI standard; `P*=Close+(p−1)(AL−AG)`. |
| `RsiFadeModel.cs` | Causal ordering | PASS | Decision-before-update: entry/exit use `_restedRsi`/`_restedPStar` (state ≤ t-1); `UpdateWilder`/`RefreshRested` fold `bar.Close` **after** emit (l.108-109). Forming-bar OHLC never read for a decision. |
| `code/run_experiment.py` | Correctness (3-gate + T1/T2) | PASS | Gates A/B/C wired to the right primitives; classification on binding gate C. |
| `xen/signals/ingestion.py::returns_and_positions_realized` | Realized-series build | PASS | Departs from `strategy_return_bps_turnover` only on engine exit bars (`ExitFillPrice` non-NaN); cost amortized once per entry. |
| all | NaN handling | PASS | RSI warmup → `NaN` position 0; `ExitFillPrice` NaN on non-exit bars; `np.errstate` guards the exit-bar log. |
| all | Holdout exclusion | PASS | `HoldoutFence` (engine) + per-symbol `ANALYSIS_END`; verified 0/34 runs reach the fence. |
| `run_experiment.py` | Import side effects | PASS | `mkdir` only in `main()`; no module-level I/O. |
| `run_experiment.py` | Progress/logging | PASS | `tqdm` over 34 runs; concise summary; blocking tripwire check logged. |
| `run_experiment.py` | Determinism | PASS | `seed_for(...)` per cell; re-run gate C bit-identical (verified). |

---

## Numerical Validation

### Spot checks (independent re-derivation from raw `positions.parquet`, not the harness CSV)

Recomputed net P&L and the gate-C verdict from the emitted parquet via an independent path:

| Cell | net bps (mine / CSV) | Gate C (mine / CSV) | reduction-identity | T2 | determinism |
|---|---|---|---|---|---|
| EURUSD/1h | −0.4101 / −0.4101 | REJECT ci −0.2195 / −0.2195 | True | True | bit-identical |
| AUDJPY/1h | −1.2800 / −1.2800 | REJECT ci −0.5511 / −0.5511 | True | True | bit-identical |
| BTCUSD/4h | −9.6629 / −9.6629 | REJECT ci −5.1442 / −5.1442 | True | True | bit-identical |

`gate_stack_pstar_reduces_to_adaptive(...) == True` on **real** positions for all three → the P*-gate
is §10.3a plus the signal-leg source swap, on this experiment's data (not just EXP-007's synthetic grid).

### Range checks

| Metric | Expected | Actual (all 34 runs) | Pass |
|--------|----------|----------------------|------|
| `Position` | {−1,0,1} | {−1,0,1} | YES |
| `RealOpen`/`RealClose` | > 0 | min 0.55097 | YES |
| `ExitFillPrice` (exit bars) | > 0 | 104,363 fills, 0 non-positive | YES |
| max emitted `SourceCloseTime` vs `AnalysisEndUtc` | strictly before | 0/34 reach fence | YES |

### Statistical sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| Gate-C ci_lower | −0.22 … −5.14 bps, all < 0 | YES | Net-negative absolute edge everywhere; magnitude scales with cost (BTCUSD 10 bps worst). |
| T1 future-destroy FPR | 0.000 / 34 | YES | A misaligned (block-permuted) signal has no edge → gate rejects → leak control holds. |
| n_trades | 593–3547/cell | YES | Dense fade (RSI-2 10/90), plausible turnover for 1h/4h over ~4y analysis slice. |

---

## Verdict Forensics

### Per-stratum re-derivation & masking check

The headline is **per-stratum**, not pooled: all **34/34** strata independently return NOT-TRADABLE
(gate C REJECT, ci_lower < 0). There is **no pooling** in the verdict — "34/34" is the per-cell
minimum, not an average. Masking risk is therefore nil: a pooled figure cannot hide a flip when every
stratum already shares the same sign and verdict. Spot-checked cells (EURUSD/1h cheapest, AUDJPY/1h
mid, BTCUSD/4h highest-cost) all re-derive identically. **No stratum separates.**

| Stratum class | Per-stratum verdict | Agrees with headline | Note |
|---|---|---|---|
| 17 instr × 1h | NOT-TRADABLE (17/17) | YES | net −0.41…−4.69 bps |
| 17 instr × 4h | NOT-TRADABLE (17/17) | YES | net −0.03…−9.66 bps; 4h uniformly worse (fewer episodes, same cost) |

### Mechanism (why NOT-TRADABLE)

The binding leg is **L3 (absolute neutral floor)**: the strategy's own realized net-return CI-lower is
**< 0** on every cell — it loses money in absolute terms after cost. Inspected at EURUSD/1h: vs-naive
leg is *positive* (ci_vs_naive_lower +0.87) and the sub-pop raw quantile clears materiality (+3.06),
but the **neutral floor** (`ci_neutral.lower > 0`, required by L3) fails (−0.22), and the **studentized
sub-pop guard** (A1) also denies the sub-pop pass (0.637 < Q_STUD_MIN 0.674). So the fade is
"less-bad-than-momentum but still net-negative" — exactly the absolute-floor failure §10.3a is built to
catch and that variant-c lacked (E5/L-12). This is the L-01 falsification: with the causal `rct[di-1]`
exit and a real engine fill, the captured edge that made CF-MR-001 look tradable is gone; net-negative
even gross-of-nothing on the favourable side.

### Gate-shape check

- Binding gate: **C (P\*-realized §10.3a)**. Effect shape: **dense, per-bar, position-state** (RSI-2
  fade holds a position most bars). Gate C consumes a per-bar realized series → correct instrument.
- `L1_readiness == True` on all 34 (effective_n 7.9k @ EURUSD/1h; 951 episodes) — the gate is **powered**,
  not vetoing on readiness. This is a genuine economic refutation, **not** "an effect of a shape this
  gate cannot see." No gate-shape mismatch.

---

## Causal Provenance & Leak

### Provenance trace (verdict-bearing columns)

| Column | Inputs & timestamps | Uses only ≤ t (≤ t-1 for decision)? | Lines |
|---|---|---|---|
| Position (entry) | `_restedRsi` = RSI₂ of Wilder state folded through **t-1** | YES (decided at bar-t open from ≤ t-1) | `RsiFadeModel.cs:85, 108-109, 194-204` |
| ExitFillPrice (`P*`) | `_restedPStar = Close_{t-1}+(p−1)(AL_{t-1}−AG_{t-1})`, rested from t-1; fills on `High_t/Low_t` of a limit **placed before bar t opened** | YES | `RsiFadeModel.cs:74, 95, 117-122, 204` |
| realized_bps | `RealOpen[t]`, `RealOpen[t+1]` (executable next open), `ExitFillPrice[t]`, `Position[t]` | YES (next-step open-to-open; standard, not look-ahead) | `ingestion.py::returns_and_positions_realized` |
| market returns (naive leg) | `next_open_to_open_returns_from_bars` (log Open[t+1]/Open[t]) | YES | `referee_adaptive.py:136-164` |

- **`rct[di]` own-close-as-limit-during-bar-`di` pattern?** **NO.** The exit limit is rested strictly
  from `t-1` state (`_restedPStar`, refreshed *after* the emit). This is the live-actable `rct[di-1]`
  choice — the explicit structural fix for L-01/P-05. The banned same-bar `rct[di]` is absent.
- **Decision at the action bar's open on confirmed bars only?** **YES** — entry/exit read only rested
  (≤ t-1) state; `bar.Close` is folded after the emit. High/Low are read **only** to trigger a resting
  limit placed before the bar (causal), never to inform the decision.
- **Returns open-to-open?** **YES** — held bars `dir·log(Open_{t+1}/Open_t)`; exit bar `dir·log(P*/Open_t)`
  (truncated at the engine fill). No open-to-close edge claim.

### Leak tripwire

- **T1 future-destroy** (block-permute the o2o market returns at the **input**, L-07; re-adjudicate):
  shipped, and the edge **collapsed on every cell — FPR 0.000/34** (well under the 2α=0.10 bound).
  gate_stack_pstar(realized:=turnover) reduces to §10.3a (verified True on real data), so T1 binds the
  realized gate too. **No surviving edge ⇒ no leak.**
- **T2 provenance (structural)**: the realized series departs from the position-state proxy **only** on
  engine exit bars — re-derived True on all 34 (and the harness's own T2 flag is True 34/34). An injected
  Python fill on a non-exit bar would break this; the smoke test confirmed T2 catches exactly that
  (P-09 simulation). No Python `rct`/favourable-index pass exists.

### Shared-module provenance contracts

- `referee_pstar.gate_stack_pstar` — matches its documented contract (one signal-leg source swap;
  frozen sub-primitives reused). Reduction identity holds on real EXP-006 positions. Frozen modules
  byte-unchanged (E5 freeze hashes; `referee_pstar.py` hash-pinned in EXP-007 freeze_manifest).
- `ingestion.returns_and_positions_realized` — new helper; output `[t]` reads only `≤ t+1` opens +
  `ExitFillPrice[t]`; reduction-identical to the turnover leg off exit bars (its stated contract).

### Price-primary check

- **Ran in the cTrader engine** — 34 runs under `data/strategy_runs/EXP-006/`, each fenced at
  `AnalysisEndUtc` (verified 0/34 over fence). **Not** a vectorized Python backtest. ✓
- **Booked-vs-real (L-02):** outcomes use the emitted **real** OHLC and the **engine-realized** `P*`
  fill; round-trip cost charged once per entry (amortized binding-leg convention). The favourable exit
  is a resting limit (the binding leg is the entry market order, cost-charged). No look-ahead favourable
  view is used for the P&L. ✓

---

## Scope Compliance

- Analysis plan followed: **YES** (3-gate parallel disclosure A/B/C exactly per design + A1/A2; T1/T2
  tripwires shipped; per-stratum binding; UNPOWERED-not-FAIL semantics available though unused — all
  cells powered).
- Deviations: **none** material. `frozen_gate_row` gained graceful `N/A_FROZEN_COSTMAP` handling for
  out-of-core instruments (see Warning 1) — a disclosure path, not a scope change.
- Complexity budget: 1 C# model + `EXP-006.conf` + 1 Python harness (no new shared `xen` module — the
  realized builder is a function added to existing `ingestion.py`); 4 plots; 2 frozen referees + T1
  permutation. **Within budget.**
- Holdout exclusion verified: **YES** (fence 0/34; global final-30% never loaded).

---

## Issues

### Critical
None.

### Warning

1. **Frozen gate-A (Chapter-01 suite) covers only the native 4-core**
   - File: `python/src/xen/referee_calibration.py:57` (`ROUND_TRIP_COST_BPS` = EURUSD/XAUUSD/BTCUSD/USTEC).
   - Description: `cost_bps_for` raises `KeyError` for the other 13 instruments; the harness records
     `N/A_FROZEN_COSTMAP` for those 26 cells (gate A scored only 8 of 34).
   - **Materiality: non-material.** Gate A is **parallel-disclosure only** (design O1); the **binding**
     adjudication is gate C (renewed §10.3a, E0 17-instrument cost map), which scored **all 34**. Gate B
     (§10.3a proxy) also covers all 34. The verdict cannot move — on the 8 cells where gate A *is*
     available it agrees (REJECT). Documented, no rerun required.
   - Note: this is itself an architecture observation — the frozen Chapter-01 referee's cost map predates
     the 17-universe; the renewed gate is what generalizes. For the report's O3 section.

### Info

1. **Three infra bugs in `tools/ctrader-cli/run-experiment.sh` found + fixed mid-run (O3 benchmark
   payoff).** (a) completion-detection ignored the writer's `_{stamp}` dir suffix → 4h `max_wait` hang
   per cell; (b) flush race on natural container exit → false "incomplete" + skipped sibling cell (added
   a bounded retry); (c) `run_complete` gated on the cTrader `report.json`, which is never written when
   the console crashes on shutdown *after* a valid parquet flush → hang (dropped the report from the
   gate). Plus a re-run strategy note: parallel `one`-invocations race in `prepare_cache_layout` symlink
   setup → subset reruns must be sequential. **Non-material to the verdict** (they affected *whether*
   emissions completed, not their content); the emitted parquet is byte-valid and fully re-derived here.
   EXP-006 is Chapter-02's first price-primary run, so these latent bugs fired for the first time.

2. **EXP-007's returns-space caveat does NOT bind EXP-006.** E6 noted that its *synthetic* calibration
   bracket only *caps* (cannot capture an intrabar excursion the close misses). Here the **real engine**
   fills `P*` on the bar's actual `High_t/Low_t` touch — a genuine intrabar fill — so gate C exercises
   true intrabar `P*` capture (the very property that made CF-MR-001 *look* tradable). It still REJECTs
   net-negative → the falsification is on the faithful mechanism, not a capped proxy.

3. **Gate-shape clean.** Dense position-state effect, gate C is the matched instrument, L1 powered on
   all 34 — no shape blindness, no UNPOWERED cells. The NOT-TRADABLE is real, not an instrument artifact.

4. **DE30** analysis slice is broker-truncated (cutoff 2025-02-18); n_returns lower (21,789/4,768) — a
   noted coverage caveat, not an exclusion; its verdict (REJECT, net −2.19/−3.85) is consistent.

---

## Materiality & Re-Audit Requirements

- **No Critical findings → no rerun required.** Every non-blocking finding above carries its materiality
  reasoning showing it cannot move sample membership, a denominator, a metric, temporal/causal validity,
  the verdict, or the binding stratum.
- Numeric reproduction was **not** taken as sufficient: the verdict is independently re-derived from raw
  parquet, the causal-provenance trace is from the C# decision-before-update ordering and the ingestion
  realized-series construction (not from re-running the same module), the future-destroy control
  collapsed on every cell, and the engine-fill (vs a Python favourable-index) is confirmed structurally.
  This is the L-01 discipline applied: the audit could have seen an acausal leak and found none.

**Verdict: PASS — 0 Critical. Proceed to Stage 5 (documentation/interpretation).**
