# EXP-006 — D-benchmark: Causal RSI-2 Fade (CF-MR-002/HYP-001) — Report

**Phase:** 001 (referee renew + causal RSI-2 benchmark). **Classification:** PRICE-PRIMARY
(in-engine), analysis-only adjudication side. **Reads/slots:** 0 counted TEST / 0 candidate;
global holdout sealed. **Verdict:** **NOT-TRADABLE 34/34 — CF-MR-002 EXONERATED** (honest prior
confirmed). **Audit:** PASS, 0 Critical (`audit.md`).

## Question (one, falsifiable)

Does the bare RSI-2 fade — exited only on the live-actable `rct[di-1]` reversion-completion limit,
run in the cTrader engine (bar-open decisions, open-to-open returns, binding-leg cost) — produce a
positive net expectancy clearing the referee on TRAIN, with the leak tripwire collapsing the control?
**Honest prior: NO** (L-01: causalized the bare fade is net-negative even gross; CF-MR-001's net edge
was a one-bar EXIT-RCT look-ahead, P-05). **Answer: NO — confirmed on all 34 strata.**

Dual purpose: **O2** causal tradability screen + **O3** architecture benchmark of the lean
cTrader-primary pipeline.

## Scope / method

- **Apparatus:** `StrategyHost/RsiFadeModel.cs` (`rsi2_fade_causal`) — RSI(2) Wilder on Close, fade at
  10/90, exit on the causal `P*_{t-1}=Close_{t-1}+(p−1)(AL_{t-1}−AG_{t-1})` rested limit (engine
  intrabar fill on `High_t/Low_t`); decision-before-state-update by construction. Emitted to
  `data/strategy_runs/EXP-006/` under per-symbol `AnalysisEndUtc` fence.
- **Strata:** 17 instruments × {1h, 4h} = **34 cells**, per-stratum binding (L-03). First-70% only.
- **Adjudication (parallel disclosure, 3 referees):**
  - **A** Frozen Chapter-01 suite — close-to-close, position-state proxy (native convention).
  - **B** Renewed adaptive gate §10.3a (`gate_stack_adaptive`) — open-to-open ≤t-1, position-state.
  - **C** E6 **P\*-capable** gate (`referee_pstar.gate_stack_pstar`, FROZEN EXP-007) — open-to-open
    ≤t-1, signal leg = **engine-realized `P*` fill** series. **The faithful, binding gate.**
- **Tripwires:** **T1** future-destroy (block-permute o2o returns at the input, L-07; re-adjudicate —
  must collapse); **T2** causal-provenance (realized series departs the proxy only on engine exit
  bars; no Python `rct` recompute, P-09).

## Results (per-stratum; 34/34, no pooling — "34/34" is the per-cell minimum)

| Metric | Result |
|---|---|
| **Verdict** | **NOT-TRADABLE 34/34** |
| Gate A (frozen) PASS | 0 / 8 scored (26 cells `N/A_FROZEN_COSTMAP`, 4-core map) |
| Gate B (§10.3a proxy) PASS | **0 / 34** |
| Gate C (P\* realized, binding) PASS | **0 / 34**; ci_lower < 0 on every cell (−0.22 … −5.14 bps) |
| Net P&L mean (realized) | **negative on all 34** (−0.03 … −9.66 bps / active bar) |
| **T1 future-destroy FPR** | **0.000 / 34** (collapsed; bound 2α=0.10) |
| **T2 provenance clean** | **34 / 34** |
| n_trades / cell | 593–3547 | 

Per-stratum table: `results/per_stratum.csv` (+ `per_stratum_full.json`). Plots:
`plots/net_pnl_per_stratum.png`, `gate_pass_map.png`, `t1_leak_collapse.png`, `gate_margins.png`.

Representative cells (independently re-derived in `audit.md`): EURUSD/1h net −0.41, C ci −0.22;
AUDJPY/1h net −1.28, C ci −0.55; BTCUSD/4h net −9.66, C ci −5.14. 4h uniformly worse than 1h (fewer
episodes, same per-trip cost). Cost-scaling visible: BTCUSD (10 bps) worst, EURUSD/USDJPY (1 bps) best.

## Interpretation

**Mechanism (why NOT-TRADABLE).** The binding leg is **L3's absolute neutral floor**: the strategy's
own realized net-return CI-lower is **< 0** on every cell — it loses money in absolute terms after
cost. At EURUSD/1h the fade actually **beats a naive momentum baseline** (vs-naive ci_lower **+0.87**)
and its sub-population raw quantile clears materiality (**+3.06** vs 1.5), yet the **neutral floor**
fails (−0.22) and the **studentized sub-pop guard** (A1) denies the sub-pop pass (0.637 < Q_STUD_MIN
0.674). The fade is **"less-bad-than-momentum but still net-negative"** — exactly the absolute floor
that §10.3a carries and the rejected variant-c lacked (E5 / L-12). This is the L-01 falsification
landing on the **faithful** mechanism: with the causal `rct[di-1]` exit and a **real engine intrabar
`P*` fill** (not a capped returns-space proxy — EXP-007's bracket-cap caveat does **not** bind here;
the engine fills on the bar's actual High/Low), the captured edge that made CF-MR-001 look tradable is
gone.

**Leak-clean.** Every cell collapses under T1 future-destroy (FPR 0.000) and passes the T2 provenance
trace — no edge survives breaking signal↔outcome alignment, and the realized series uses only the
engine's causal fill. The L-01 four-layer defence (cTrader-primary execution, causal-provenance audit,
future-destroy control, provenance contracts) held end-to-end.

**Gate-shape.** Dense per-bar position-state effect; gate C is the matched instrument; L1 powered on
all 34. The NOT-TRADABLE is a genuine economic refutation, not a gate artifact or an UNPOWERED veto.

**Honest framing (L-11).** This is not a within-noise wash — the absolute net edge is negative with
CI-lower below zero on every stratum, magnitude scaling with cost. CF-MR-002 is **exonerated as a
tradable edge** on the causal TRAIN screen.

## O3 — architecture benchmark (the lean cTrader-primary pipeline)

EXP-006 is Chapter-02's **first** price-primary run; it exercised the full lean pipeline (4 artifacts,
inline governance, autonomous execution with one operator stop for the credentialed run) and **earned
its keep by exposing latent infra bugs** in `tools/ctrader-cli/run-experiment.sh` (all fixed):

1. **Completion-detection** ignored the writer's `_{stamp}` dir suffix → `run_complete` never matched →
   4h `max_wait` hang per cell. Fix: glob the newest suffixed dir.
2. **Flush race** — a container that exits on its own can write parquet a moment after the wait-loop
   sees it gone → false "incomplete" + the worker skipped its sibling (4h) cell. Fix: bounded retry.
3. **Report-json gate** — `run_complete` required the cTrader `report.json`, which is **never written
   when the console crashes on shutdown** *after* a valid parquet flush (benign cTrader lifecycle
   exception) → hang. Fix: gate on the StrategyHost parquet only (the report is an unused diagnostic).
4. **prepare_cache_layout race** — 17 parallel `one`-invocations race on the cache symlink setup →
   subset reruns must run sequentially (operational note, not a script edit).
5. **Frozen gate-A coverage** — `referee_calibration.ROUND_TRIP_COST_BPS` covers only the 4-core
   (EURUSD/XAUUSD/BTCUSD/USTEC); gate A scored 8/34, the rest `N/A_FROZEN_COSTMAP`. The renewed §10.3a
   (E0 17-instrument map) is what generalizes — non-material (binding gate C covers all 34).

Recommend a **KB lesson candidate** capturing the price-primary harness robustness contract
(stamp-suffix detection, flush-retry, parquet-not-report completion gate, sequential subset reruns).

## Audit caveats (from `audit.md`, PASS, 0 Critical)

- Causal-provenance clean: exit limit rested strictly from `t-1` (`_restedPStar`, refreshed after
  emit); **no `rct[di]`** own-close-as-limit; decisions at bar-open on ≤t-1 state; returns open-to-open.
- T1 collapsed 34/34; T2 clean 34/34 (and T2 verified to catch an injected non-exit-bar fill).
- Holdout fence verified 0/34 over `AnalysisEndUtc`; ranges clean (Position∈{−1,0,1}, prices>0, 104,363
  exit fills all positive); reduction identity `gate_stack_pstar→§10.3a` True on real positions;
  determinism bit-identical. 1 Warning (gate-A 4-core, non-material), 4 Info.

## Conclusion & follow-up

**CF-MR-002/HYP-001 EXONERATED — NOT-TRADABLE across 17×{1h,4h}.** The causal RSI-2 fade has no net
edge that clears the referee; the CF-MR-001 "tradable" arc was the L-01 look-ahead, now structurally
impossible in-engine. No deployment claim, no counted read, no holdout; no NET-TRADABLE surprise, so no
operator deployability pause was triggered.

Follow-up (each a separate future experiment, own D0):
- **KB lesson** — price-primary cTrader-harness robustness contract (the 4 infra findings above).
- The bare-fade entry's **gross MFE availability** (EXP-089/G-020) is unaffected and remains *not* a
  tradable claim — do not resurrect EXIT-RCT (P-05). CF-MR-002 deferred levers (vol-regime, 25/75, 15m)
  each need a fresh D0 + slot decision and would face the same absolute-floor wall absent new information.

## Links
`design.md` · `code/run_experiment.py` · `python/src/xen/referee_pstar.py` ·
`python/src/xen/signals/ingestion.py` · `results/per_stratum.csv` · `audit.md` · `plots/`

## Registry disposition

**CF-MR-002 — EXONERATED at D-benchmark** (causal TRAIN screen, NOT-TRADABLE 34/34). Family stays
**REGISTERED**, status advanced to **SCREENED — refuted-as-tradable** (`candidate-families/cf-mr-002.md`).
**0 candidate slots, 0 counted TEST reads** (analysis-set screen, honest-prior exoneration; entered as a
disclosure, not a counted read — `test-read-ledger.md`). Global holdout never loaded. CF-MR-002 was
**not** used to tune any gate (L-12 honored; the gates were frozen at E5/E6 before this read).

---

## GATE: APPROVE (orchestrator inline post-exec, 2026-06-30)

Checked against `references/governance-constraints.md`:
- **Verdict forensics present** (`audit.md`): per-stratum re-derivation (3 cells independently,
  exact match) + masking check (no pooling — 34/34 per-cell minimum, uniform sign) + mechanism
  (L3 absolute neutral floor; less-bad-than-momentum-but-net-negative) + gate-shape (dense
  position-state, gate C matched, L1 powered all 34). ✓
- **Causal-provenance & leak pass present**: provenance trace from the C# decision-before-update
  ordering + the realized-series construction (not re-running the same module); **no `rct[di]`**;
  T1 future-destroy collapsed 34/34; T2 clean 34/34; shared-module contracts verified (reduction
  identity on real data; `returns_and_positions_realized` contract). ✓
- **Every verdict-material finding fixed-and-rerun**: no Critical findings; the infra bugs were
  fixed mid-execution and the affected cells re-run to valid emissions (re-derived clean). ✓
- **Price-primary**: ran in-engine under the fence (0/34 over `AnalysisEndUtc`); not a vectorized
  Python backtest; binding-leg cost charged. ✓
- **Per-stratum binding** (L-03); UNPOWERED-not-FAIL available (unused — all powered); **not tuned on
  CF-MR-002** (L-12). ✓
- **Registry disposition recorded**: CF-MR-002 → SCREENED/exonerated; 0 slots / 0 counted reads;
  disclosure entered; holdout sealed. ✓

No REVISE/REJECT issues. **APPROVE — EXP-006 COMPLETE.** D-benchmark (O2/O3) closed: causal RSI-2 fade
exonerated; the lean cTrader-primary architecture validated end-to-end (with 4 infra fixes banked).
