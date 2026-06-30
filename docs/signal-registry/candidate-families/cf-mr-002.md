# CF-MR-002 — Causal RSI-2 Mean-Reversion Fade (cTrader-primary)

**Status:** `SCREENED — EXONERATED (NOT-TRADABLE)` (D-benchmark **EXP-006**, 2026-06-30; audit PASS, 0
Critical). Prior: `REGISTERED` (2026-06-27) — G0 RATIFIED at Chapter-02 Phase 001 (D0 §D0). 0 candidate
slots consumed, 0 counted TEST reads, global holdout sealed; never used to tune the gate (L-12 honored —
gates frozen at E5/E6 before the read).

**D-benchmark outcome (EXP-006/HYP-001, 2026-06-30).** Causal RSI-2 fade (RSI(2) 10/90, causal
`rct[di-1]`/`P*_{t-1}` exit, engine-realized intrabar fill) run in the cTrader StrategyHost over
17×{1h,4h} = 34 strata, adjudicated under 3 referees (frozen Chapter-01 / §10.3a position-state proxy /
E6 P\*-capable `referee_pstar.gate_stack_pstar`). **NOT-TRADABLE 34/34** — all gates REJECT every cell;
net P&L negative on all 34 (−0.03…−9.66 bps/active bar); the faithful P\*-realized gate's ci_lower<0
everywhere. Binding leg = **L3 absolute neutral floor** (the fade beats a naive momentum baseline but is
net-negative in absolute terms). **Leak-clean:** T1 future-destroy collapsed 0.000/34, T2 causal-
provenance clean 34/34 — the L-01 falsification confirmed on the faithful engine-fill mechanism (not a
proxy). **CF-MR-002 is exonerated as a tradable edge** on the causal TRAIN screen. Family remains in the
registry (never deleted); deferred levers (vol-regime, 25/75, 15m) each need a fresh D0 + slot and face
the same absolute-floor wall absent new information. See `python/experiments/EXP-006/report.md`,
`audit.md`, and `families/cf-mr-002/INDEX.md`.

**Provenance.** Successor to **CF-MR-001** (CLOSED — REFUTED 2026-06-26; the net-tradable/deployment
arc rested on a one-bar EXIT-RCT look-ahead, `rct[di]` rested during bar `di`; causalized the bare
fade is net-negative even gross — see `cf-mr-001.md` §CLOSURE and KB **L-01**). CF-MR-001 is **not
reopenable by re-parameterization**; its closure note authorises a **new family under its own D0 only
after the `rct[di-1]` causal fix**. CF-MR-002 is that family. The reopened lever is not a re-parameter:
it is the **causalized exit + cTrader-primary execution** — a structurally different (leak-resistant)
construction of the same entry, which has never been screened.

## Thesis (one falsifiable sentence)

*With the reversion-completion exit rested only from the live-actable `rct[di-1]` limit, executed in
the cTrader engine (bar-open decisions, open-to-open returns, binding-leg slippage), the RSI-2 fade
produces a positive net expectancy clearing the referee — or it does not (honest prior: it does not).*

## Fixed first-branch definitions (frozen at Phase-001 D0)

- **Entry:** `RSI(2)`, Wilder, on domain `Close`; extremes **10 / 90** (inherited from CF-MR-001,
  no re-tuning). Long `RSI₂<10`, short `RSI₂>90`, evaluated at bar **open** on confirmed bars (`≤ t-1`).
- **Exit:** reversion-completion target rested **only** from `rct[di-1]` (the causal limit). The
  `rct[di]` same-bar limit is **banned** (L-01). Stop/cost per the Phase-001 D0 cost table.
- **Execution:** cTrader StrategyHost (`ISignalModel`); `data/strategy_runs/<EXP-ID>/` emissions;
  Python analysis-only. Returns **open-to-open**; an `OnClose` fill is non-tradable.
- **Leak tripwire (mandatory):** a future-destroying control (future-shuffle / time-reversal /
  label-permutation) that must collapse any measured edge; a surviving edge ⇒ leak ⇒ REJECT.

## Allowed domains / parameters

Domains 1h and 4h first (the CF-MR-001 cost-geometry survivors); 15m disclosed but cost-dominated.
No parameter tuning in batch 1. Instrument set = the CF-MR-001 carried strata, re-screened causally.

## Hypotheses (EXP-IDs assigned at promotion)

- `CF-MR-002/HYP-001` — *Causal tradability screen.* Does the causal (`rct[di-1]`) fade, run in-engine,
  net-clear the referee on TRAIN with the leak tripwire collapsing the control? Admit/exonerate;
  0 reads/slots. The dual purpose: this is also the **architecture benchmark** vehicle (O2/O3 of the
  Phase-001 checkpoint).
- (Further hypotheses — counted TEST read, deployment — only on a TRAIN admit, each at its own D0.)

## Referee note (binding)

CF-MR-002 is adjudicated under **both** the frozen Chapter-01 suite **and** the Phase-001 adaptive gate
(once that gate is FPR-recalibrated and frozen on the dogfood-negative + synthetic-positive). CF-MR-002
must **not** be used to tune the adaptive gate (L-12 selection-bias guard).

## Exclusions / deferred

No deployment economics, no holdout release, no CF-MR-001 deferred levers (vol-regime, contrarian,
25/75, 15m, regime×variant cross-cuts) in batch 1 — each needs its own dated D0 + slot decision.

## Discipline

Real-price outcomes only (`RealOpen/High/Low/Close`); final-30% global holdout never read in screening;
counted TEST reads spent only at a future binding confirmation under the 2-lifetime-per-stratum cap.
All outcomes (admit/exonerate/inconclusive) retained, never deleted or silently reopened.
