# EXP-006 — D-benchmark: Causal RSI-2 Fade (CF-MR-002/HYP-001) — in-engine

**Branch:** `main`. **Checkpoint:** Phase-001 §D0 (O2/O3); family `cf-mr-002.md`.
**Classification:** **PRICE-PRIMARY** — generates entries/positions/edges from price ⇒ runs in the
cTrader StrategyHost (`tools/ctrader-cli/run-experiment.sh`), emits `data/strategy_runs/EXP-006/`,
Python is analysis-only on emissions. A vectorized Python backtest of this fade is **REJECT** (L-01).
**Reads/slots:** 0 counted TEST reads, 0 candidate slots, global holdout sealed (first-70% only).
**Consumes (frozen):** E0 `referee_adaptive.ROUND_TRIP_COST_BPS_17`; frozen Chapter-01 referee suite
(`referee_calibration.py`); renewed adaptive gate §10.3a q\*=0.75 (`EXP-005/results/freeze_manifest.json`,
`sha256=b4fd6cb1…ae847`). The adaptive gate is **never** tuned on this candidate (L-12 selection guard).

## Question (one, falsifiable)

**Does the bare RSI-2 fade, exited only on the live-actable `rct[di-1]` reversion-completion limit and
run in the cTrader engine (bar-open decisions, open-to-open returns, binding-leg slippage), produce a
positive net expectancy that clears the referee on TRAIN — with the leak tripwire collapsing the
control — or does it not?** Honest prior: **NO** (L-01: causalized, the bare fade is net-negative even
gross; the CF-MR-001 net edge was a one-bar EXIT-RCT look-ahead, P-05).

This is dual-purpose: O2 (causal tradability screen) **and** O3 (architecture benchmark of the lean
cTrader-primary pipeline). No deployment claim, no holdout, no parameter tuning in this batch.

## Price-primary apparatus

### C# model — `StrategyHost/RsiFadeModel.cs` (`ISignalModel`), strategy `rsi2_fade_causal`

Frozen first-branch (cf-mr-002.md; **no tuning**): `RSI(2)` Wilder on domain `Close`, extremes 10/90.
Causality is by construction (bar-open + lagged reference, KB standing rule):

- Maintain Wilder average-gain/-loss state (`AG,AL`) and `prevClose`, updated **only after** each bar
  closes (byte-identical seeding/recursion to `wilder_avg_gain_loss`: simple mean of first `period`
  deltas, then `avg=(avg·(p−1)+x)/p`; warmup `NaN` for first `period` bars).
- `OnBar(bar_t, domain)` decides using **state through `t-1` only** (computed *before* folding
  `bar_t.Close`): `RSI₂(≤t-1)`. **Entry:** `RSI₂<10`→`+1` (long), `RSI₂>90`→`−1` (short), else hold/flat.
  The forming bar's own OHLC is **never** read for the decision.
- **Exit (causal `rct[di-1]`):** the trailing reversion-completion limit active during bar `t` is
  `P*_{t-1}=Close_{t-1}+(period−1)(AL_{t-1}−AG_{t-1})` — **rested from the prior bar's closed state**
  (known before `t` opens). Long exits if `bar_t.High≥P*_{t-1}` (fill at `P*`); short if
  `bar_t.Low≤P*_{t-1}`. The same-bar `rct[di]` limit (rested from `bar_t.Close`) is **BANNED** (L-01/P-05).
  A resting-limit fill on `bar_t`'s High/Low is causal (order placed before the bar opened).
- No stop / second target / re-anchor in batch 1 (deferred levers out of scope). Re-entry allowed on the
  next qualifying extreme after an exit.
- **Emission** (`SignalPositionRecord`): per-bar position + the **real** domain-bar OHLC executed on;
  exit-limit price recorded in the event/blotter stream. Returns/P&L are computed in Python from emitted
  **real** Open (entry, open-to-open) and the realized limit fill `P*` (exit) — never synthetic prices.

Register in the `XenStrategy` enum + `CreateStrategyModel()` switch (`Xen.cs`); `dotnet build`. Template:
`DonchianBreakoutModel.cs`. **Decision-before-update ordering is the binding causal contract** the audit
will trace (verdict-bearing columns derive only from `≤t-1`).

### Cells / fence (`tools/ctrader-cli/experiments/EXP-006.conf`)

- **Strata = 17 instruments × {1h, 4h} = 34 cells** (E0/Q6 universe). Per-instrument, **per-stratum
  non-pooling** (L-03); a pooled figure is disclosure-only until cross-stratum homogeneity is shown.
- Per-symbol `ANALYSIS_END` = that file's **first-70% analysis cutoff**; `HoldoutFence` refuses any
  emission at/after `AnalysisEndUtc` (global holdout impossible by construction). `DE30` history is
  broker-truncated to 2026-01-16 — its analysis slice is shorter (note, not exclude).

## Return / cost convention (binding)

- **Open-to-open `≤t-1`** real returns (Q7/E0). Entry market order at `bar_t.Open` charged **binding-leg
  slippage** (L-02: cost on the leg that actually moves; the favourable exit is a resting limit at `P*`).
- Net cost = E0 `ROUND_TRIP_COST_BPS_17[instrument][domain]` per round trip. The **two gates apply their
  own frozen cost conventions** (frozen suite = per-held-bar; adaptive = amortized-per-episode, E1/E3a) —
  this convention split is inherent **parallel disclosure**, not a candidate choice. The emission is
  convention-agnostic (positions + real OHLC); Python builds both return series from the one emission.
- **Denominators:** per-trade net P&L in bps over realized round trips; per-bar return-series over active
  bars. **Zero-baseline:** a cell with 0 trades, or no finite MDE under a gate leg, is **UNPOWERED** for
  that gate (reported, never FAIL — power-aware discipline, L-12 Mode-2).

## Adjudication (per stratum; parallel disclosure)

Each of the 34 cells is adjudicated under **both** referees, reported side-by-side (cf-mr-002 §referee):

1. **Frozen Chapter-01 suite** (`referee_calibration.py`, byte-frozen) — close-to-close basis retained
   for parallel disclosure (its native convention).
2. **Renewed adaptive gate §10.3a, q\*=0.75** (`referee_adaptive`, hash-pinned) — open-to-open `≤t-1`,
   validity→economics composite, studentized sub-pop L5, per-stratum.

**Dual metric unit (Q9/F10):** report per-trade net-P&L **and** the per-bar return-series stat
(Sharpe-LB co-bound with Calmar/tail, MTM per L-09); disclose which binds. Decision-margin reported
alongside each pass/fail.

## Leak tripwire(s) — mandatory (L-01 layer 3; audit verifies collapse)

- **T1 — entry-signal block-permutation (future-destroy).** On the emitted positions, block-permute the
  entry-event labels against the return stream (break signal↔outcome alignment, preserve marginal return
  distribution). Net expectancy **must collapse into the null CI** on every cell. A surviving edge ⇒ leak
  ⇒ **REJECT**. (Block-permute, not path-rotate — L-07.)
- **T2 — causal-provenance trace (structural).** Confirm the active exit limit on bar `t` derives only
  from state `≤t-1` (decision-before-update ordering); confirm no Python `rct[di]` favourable-index pass
  exists (P-09). cTrader streaming + `HoldoutFence` are the by-construction guarantee.
- **Diagnostic (labelled non-tradable, optional):** acausal `rct[di]` vs causal `rct[di-1]` net-edge
  delta — expected ≈ the L-01 +0.25 ATR/trade inflation, to *quantify the removed leak*. **Not** a
  tradability claim (P-05); excluded from any verdict. Run only if cheap.

## Predeclared interpretation criteria (no goalpost-moving)

Per stratum, under each gate:
- **NET-TRADABLE (surprise vs prior):** gate PASS with positive decision-margin **and** T1 collapses the
  control. Triggers a critical-decision pause (deployability-adjacent) before any further step — no
  counted read or holdout in this experiment.
- **NOT-TRADABLE (expected):** gate FAIL / net expectancy ≤ 0 / CI-lower ≤ 0. Confirms the honest prior.
- **UNPOWERED:** no finite MDE / too few trades on that cell (reported, not a refutation — L-04 vehicle
  match; sparse cells are not failures).
- **INVALID (must fix+rerun):** T1 does **not** collapse the edge, or the provenance trace finds a `≤t`
  read on a verdict-bearing column ⇒ leak ⇒ REJECT-class → Stage-4 material, fix + re-execute (Stage 3).
- **Shape-aware read:** report the per-stratum net-P&L distribution and frozen-vs-adaptive agreement;
  flag cells where the two gates disagree (expected on sparse/STATE shapes the renew targeted).

## O3 — architecture benchmark metrics (record during the run)

Pipeline wall-clock per stage; approximate token cost; artifact count (target **4**: `design.md`,
`code/`, `audit.md`, `report.md`); number of operator stops; whether the causal-provenance audit + leak
tripwire **fire correctly**. Compare against the Chapter-01 8-stage norm. Reported in `report.md`.

## Complexity budget

Price-primary: **new code** = 1 C# model (`RsiFadeModel`) + `EXP-006.conf` + 1 Python adjudication
harness (reuse `xen.signals.ingestion`, `referee_calibration`, `referee_adaptive`; no new shared `xen`
module). **Stat apparatus** = the two frozen referees per stratum (not free tests — frozen instruments) +
T1 permutation. **Visualisations** 4: (1) per-stratum net-P&L distribution; (2) frozen-vs-adaptive PASS
map (34 cells); (3) T1 leak-collapse (edge → null band); (4) per-trade equity/return per representative
cell. No tuning, no scope expansion after the gate.

## Success / failure / inconclusive (O2)

- **Success (either direction):** a causal, T1-passing per-stratum verdict (net edge yes/no/inconclusive)
  with the global holdout untouched and the provenance trace clean. Honest-prior confirmation (NOT-
  TRADABLE) is a successful, informative outcome.
- **Failure:** T1 fails to collapse the edge, or a `≤t` provenance read is found ⇒ leak ⇒ REJECT, fix +
  rerun. A vectorized-Python edge claim ⇒ REJECT.
- **Inconclusive:** cells UNPOWERED at the available analysis-slice trade counts → reported as such; not
  forced into a verdict.

## Safety constraints for `experiment-developer`

- C# **decision-before-state-update** ordering (entry & exit limit use `≤t-1` state only); never read the
  forming bar's OHLC for the decision; resting-limit fill on `bar_t` High/Low only.
- Emit real domain-bar OHLC + the realized limit fill; no synthetic prices in any return/P&L.
- Python ingestion is **read/validate-only** (`xen.signals.ingestion`); no signal re-generation.
- Timestamp alignment by `CloseTime`/`SourceCloseTime`, never bar index; first-70% slice via per-symbol
  `ANALYSIS_END`; T1 permutation is block-wise on bounded resamples (state draw count + Wilson half-width).
- NaN handling explicit (RSI warmup); progress (`tqdm`) over the 34 cells.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-29)

Checked against `references/governance-constraints.md` + checkpoint §D0 + `cf-mr-002.md`:
- **Classification** PRICE-PRIMARY — correct; runs cTrader StrategyHost, Python analysis-only on
  emissions; vectorized-Python backtest explicitly REJECTed (L-01). ✓
- **Single falsifiable question**; honest prior stated (NO). **Boundaries** explicit (17×2=34 cells,
  first-70%, frozen 10/90 RSI(2), `rct[di-1]` exit). **Holdout** sealed by `HoldoutFence` + per-symbol
  `ANALYSIS_END`; never loaded. ✓
- **Causality:** decision-before-state-update (`≤t-1` only); `rct[di]` BANNED (P-05/L-01); resting-limit
  fill on `bar_t` High/Low is causal. ✓ **Real-price** outcomes only; open-to-open `≤t-1`; binding-leg
  slippage (L-02). ✓
- **Leak tripwire(s) shipped:** T1 block-permutation future-destroy (must collapse → else REJECT) + T2
  provenance trace; block-permute not path-rotate (L-07). ✓
- **Per-stratum binding** verdicts, pooled disclosure-only (L-03); UNPOWERED-not-FAIL (L-04/L-12 Mode-2);
  **shape-aware** read predeclared; dual metric unit (Q9). ✓
- **No magic constants:** thresholds = frozen E0 cost map + two frozen referees; **adaptive gate not
  tuned on CF-MR-002** (L-12 guard). ✓
- **Registry precondition:** CF-MR-002 REGISTERED; 0 counted TEST reads, 0 candidate slots; a NET-TRADABLE
  surprise triggers an operator critical-decision pause before any further step. ✓
- **Budget** respected (1 C# model + conf + 1 Python harness; 4 plots; no new shared `xen` module).
- **Note (not blocking):** the credentialed/cost-bearing cTrader run is the operator-gated Stage-3 stop —
  pre-approved per the checkpoint pointer; orchestrator will still confirm at the run bar.

No REVISE issues. Proceed to Stage 2 (implement `RsiFadeModel` + `EXP-006.conf` + the Python adjudication
harness).

---

## AMENDMENT A1 — exit-realization mechanism ratified (operator, 2026-06-29, pre-execution)

The referees consume a **per-bar position·next-step-return series** (`ingestion.returns_and_positions`;
`strategy_return_bps` = `positions·returns`); there is **no fill-price channel**. The design's
reversion-completion exit "realized at `P*`" is therefore under-specified against the apparatus.
Operator ratified **Option C — engine-realized `P*` fill (faithful)** over the conservative
position-state proxies (A: RSI-reverts-to-50 state exit; B: rct-touch → next-open exit). This resolves
an under-specified mechanism **within** the approved O2 question (not a scope expansion); recorded
in-place per the amend-in-place norm (L-10).

**Mechanism (binding).** The rested limit `P*_{t-1}=Close_{t-1}+(period−1)(AL_{t-1}−AG_{t-1})` (causal,
known before `t` opens) fills intrabar: long exits at `P*` when `High_t≥P*_{t-1}`, short when
`Low_t≤P*_{t-1}` (same-bar entry+exit handled). The engine emits, per bar, `ExitFillPrice` (= `P*` on
an exit bar, else `NaN`) alongside `Position` + real OHLC. Per-bar realized **log** return:
held-through bars `dir·log(Open_{t+1}/Open_t)`; the exit bar `dir·log(P*/Open_t)`; flat `0` — these
telescope exactly to a trade's entry-open→`P*` log return (open-to-open basis with the exit bar
truncated at the favourable limit). Built in Python from emitted real opens + the engine's realized
`ExitFillPrice` (no Python `rct` recompute — P-09 clean).

**Adjudication wiring (leak-safe, additive — no frozen-gate edit).**
- **Adaptive gate §10.3a:** fed the realized series via the existing E1 `strategy_fn` seam
  (`referee_adaptive.gate_stack_core_costfn(strategy_fn=…)`); the vs-naive control leg stays on the
  frozen per-held-bar reference (seam scope unchanged). This is the **faithful, binding** adjudication.
- **Frozen Chapter-01 suite:** byte-frozen, has **no** `strategy_fn` seam ⇒ it necessarily adjudicates
  the **position-state proxy on its native close-to-close basis** (`Position·return`, ignoring
  `ExitFillPrice`). This is a **forced consequence** of C + the freeze, **not** a silent choice: the
  frozen suite is the *retained reference reported as-is* (checkpoint O1), the adaptive gate is the one
  under benchmark. The two gates therefore see **different return realizations** — disclosed explicitly
  in `report.md` (frozen = conservative proxy / close-to-close; adaptive = faithful `P*`-fill /
  open-to-open). Honest prior (NOT-TRADABLE) is unaffected by the gap.

**Emission/ingestion contract delta (additive).** `SignalPositionRecord` gains `ExitFillPrice`
(`double`, default `NaN`); the positions parquet gains the column (other models default `NaN`,
`_REQUIRED_COLUMNS` unchanged so prior runs still validate). New ingestion `returns_and_positions_
realized()` builds the realized per-bar series; required only on this path. The realized fill is the
**engine's causal realized fill** (audited), never a Python favourable-index pass.

**Leak tripwire T1 unchanged** and now binds the realized series: block-permuting the entry labels
against the return stream must collapse the realized-fill edge into the null CI too.

---

## AMENDMENT A2 — BLOCKED pending a P*-capable referee (operator, 2026-06-29, pre-execution)

**Discovery (verdict-material).** A2's Option-C plan assumed the realized-`P*` series could feed the
binding §10.3a gate via a `strategy_fn` seam. **It cannot.** `referee_adaptive.gate_stack_adaptive`
(the hash-frozen §10.3a renewed referee) **hardcodes** `strategy_return_bps_turnover(returns,
positions)` and exposes **no** `strategy_fn` seam (only E1's frozen-*mirror* `gate_stack_core_costfn`
has one, and it yields the frozen-suite row, not the adaptive row). The frozen Chapter-01 suite
likewise consumes `positions·returns`. So **both frozen gates structurally adjudicate
`position·market-return` only**; injecting an engine-realized `P*` series requires editing a
hash-frozen module — forbidden (freeze is REJECT-class). This is the same architectural truth that
forced CF-MR-001's bespoke Python intrabar fill engine (the L-01 leak site): the cTrader-primary +
frozen-referee stack adjudicates **per-bar position-state** strategies only.

**Operator decision.** **Defer D-benchmark**; build a **P*-capable referee variant** first — a new
predeclared experiment (**EXP-007**) that adds a realized-return adjudication path, FPR-recalibrated on
the dogfood-negative + synthetic-positive (EXP-019 protocol) and **frozen before** it adjudicates
CF-MR-002 (L-12 guard). EXP-006 resumes (Stage 3 run) only after EXP-007 freezes.

**State at block (already built, retained):** `StrategyHost/RsiFadeModel.cs` (causal RSI-2 fade +
engine-realized `P*` exit) + `XenStrategy.Rsi2Fade` registration + `ExitFillPrice` emission
(`SignalPositionRecord`/writer) — **`dotnet build` PASS, 0 warn/0 err**; `tools/ctrader-cli/
experiments/EXP-006.conf` (34 cells, per-symbol first-70% fence). **Pending:** the Python adjudication
harness (`code/`) — deferred until the EXP-007 P*-capable gate exists to call.
**Status: BLOCKED — depends on EXP-007.**
