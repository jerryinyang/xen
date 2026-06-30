# Family Index — CF-MR-002 (Causal RSI-2 Mean-Reversion Fade, cTrader-primary)

Successor to CF-MR-001 (CLOSED — REFUTED via L-01). The reopened lever is the **causalized exit
(`rct[di-1]`) + cTrader-primary execution** — a structurally leak-resistant construction of the same
RSI-2 fade entry. Registry: `docs/signal-registry/candidate-families/cf-mr-002.md`. Governing
checkpoint: `docs/experiments-docs/checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/`.

**Status:** SCREENED — EXONERATED (NOT-TRADABLE 34/34, D-benchmark EXP-006, 2026-06-30). 0 slots / 0
counted TEST reads; holdout sealed.

## Experiments
- [EXP-006 — D-benchmark causal tradability screen (HYP-001)](#exp-006)

---

## EXP-006 {#exp-006}

**Hypothesis Tests.** CF-MR-002/HYP-001 — does the bare causal RSI-2 fade (RSI(2) 10/90 fade, exit on
the live-actable `P*_{t-1}` reversion-completion limit, engine-realized intrabar fill, open-to-open
≤t-1 returns, binding-leg cost) clear the referee on TRAIN with the leak tripwire collapsing the
control? Honest prior: NO (L-01).

**Scope.** Price-primary, in-engine (`StrategyHost/RsiFadeModel.cs`, `rsi2_fade_causal`); Python
analysis-only on emissions. 17 instruments × {1h,4h} = 34 strata, per-stratum binding (L-03), first-70%
only, global holdout sealed by `AnalysisEndUtc` fence. Frozen first-branch (no tuning). Three referees
in parallel disclosure: **A** frozen Chapter-01 suite (close-to-close, position-state proxy), **B**
renewed §10.3a `gate_stack_adaptive` (open-to-open proxy), **C** E6 `referee_pstar.gate_stack_pstar`
(engine-realized `P*` fill — the faithful binding gate). Tripwires: T1 future-destroy (block-permute
o2o returns, L-07), T2 causal-provenance trace. 0 slots / 0 counted reads.

**Results / Observations.** **NOT-TRADABLE 34/34.** All gates REJECT every cell. Net P&L negative on
all 34 (−0.03…−9.66 bps/active bar). Gate C ci_lower < 0 on every cell (−0.22…−5.14). Gate B 0/34 PASS;
gate A 0/8 scored (26 cells `N/A_FROZEN_COSTMAP` — the frozen suite's cost map covers only the 4-core).
**T1 future-destroy FPR 0.000/34** (edge collapses), **T2 provenance clean 34/34**. 4h uniformly worse
than 1h; magnitude scales with cost (BTCUSD 10 bps worst). n_trades 593–3547/cell. Audit PASS, 0
Critical (independent re-derivation matches exactly; reduction identity `gate_stack_pstar→§10.3a` True
on real positions; holdout fence 0/34 over). Plots: `net_pnl_per_stratum`, `gate_pass_map`,
`t1_leak_collapse`, `gate_margins`.

**Hypothesis-Specific Conclusion.** **CF-MR-002 EXONERATED — the causal RSI-2 fade has no net edge
clearing the referee on any of the 34 strata.** Binding leg = L3 absolute neutral floor: the fade
**beats a naive momentum baseline** (vs-naive +0.87 @ EURUSD/1h) and clears sub-pop raw materiality
(+3.06) but is **net-negative in absolute terms** (and fails the studentized sub-pop guard) — "less-bad-
than-momentum but net-negative", exactly the floor §10.3a carries and variant-c lacked (E5/L-12). The
L-01 falsification confirmed on the **faithful** mechanism (real engine intrabar `P*` fill, not a capped
proxy). CF-MR-001's "tradable" arc was the EXIT-RCT look-ahead, now structurally impossible in-engine.

**Hypothesis-Agnostic Observations.** (1) **O3 architecture benchmark** — Chapter-02's first
price-primary run exposed + fixed 3 latent `tools/ctrader-cli/run-experiment.sh` infra bugs: timestamp-
suffix completion detection (4h hang/cell), flush race on natural container exit (false-incomplete +
skipped sibling cell), and a `report.json` completion gate unmet when the cTrader console crashes on
shutdown after a valid parquet flush; plus an operational note (parallel `one`-invocations race in
`prepare_cache_layout` symlink setup → subset reruns sequential). KB-lesson candidate for the
price-primary harness robustness contract. (2) The frozen Chapter-01 referee's cost map covers only the
4-core (EURUSD/XAUUSD/BTCUSD/USTEC); the renewed §10.3a (E0 17-instrument map) is what generalizes to
the full universe. (3) The cTrader console throws a benign state-machine exception on shutdown after
emitting valid parquet — data integrity unaffected.
