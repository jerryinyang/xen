# Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark (Chapter 02 opener)

**Status:** G0 RATIFIED (2026-06-27) — O1 D0 predeclared below (§D0). **Chapter:** 02 (cTrader-primary era).
**Slots/reads:** 0 candidate slots, 0 counted TEST reads at G0; global holdout sealed.
**Consolidation source:** `docs/referee-framework-redesign-plan.md` (3-assessment merge, code-cross-validated).

This is the first Chapter-02 phase. It does double duty: (1) the **referee renew** — fix the
gating-system rigidity uncovered in Chapter 01 (KB **L-12**); (2) the **architecture benchmark** —
push the finalised, causally-correct RSI-2 fade (**CF-MR-002**) end-to-end through the new
cTrader-primary lean pipeline to measure the rollover's correctness *and* speed/efficiency.

## Objectives

1. **O1 — Referee adaptivity (methodological).** Replace rigid fixed-threshold conjunctive gating
   with a power-aware, candidate-matched scheme that **keeps or improves the earned FPR control** but stops
   over-rejecting and mis-scaling. Validate on nulls + synthetics; freeze before any live read.
2. **O2 — Causal RSI-2 (CF-MR-002).** Re-run the RSI-2 fade with the `rct[di-1]` causal exit, in
   the cTrader engine (look-ahead impossible by construction), under the new bar-open / open-to-open
   convention. Establish whether the bare fade has any net edge once causal — the honest prior is it
   does **not** (L-01: causalized, net-negative even gross).
3. **O3 — Architecture benchmark.** Record wall-clock + token cost + artifact count for the full
   lean pipeline run, vs the Chapter-01 8-stage baseline, as the rollover's efficiency proof.

## O1 — the weakness (from L-12) and the investigation

The frozen 5-check stack is an **AND of fixed-threshold legs**. Three documented failure modes:

| Mode | Chapter-01 evidence | Direction to investigate (predeclare at D0) |
|---|---|---|
| Conjunctive fragility (FPR→0 bought with 2–8× MDE; modest/tail/sparse true edges vetoed) | EXP-003 keystone trade-off; CF-VOLEXP tail-only below band; L-11 | Replace hard AND with a **calibrated composite** no single blind leg can veto; predeclared FPR target |
| Structurally-impossible legs (no finite MDE in a regime ⇒ auto-fail, not a test) | EXP-015 standalone-L2 dropped; CF-MR-001 `COVERAGE_EXCLUDED` cells | **Power-aware gating**: apply a leg only where finite MDE exists; report *unpowered*, never *fail* |
| Fixed thresholds mis-scaled to the candidate | L-04 (16× dilution false REFUTE); EXP-008 per-instrument MDE < pooled; fixed-Sharpe=1.0 bite + SUB-RANDOM null both swapped mid-CF-MR-001 | **Candidate-matched thresholds**: MDE-curve co-designed with the band per vehicle/shape/instrument (generalize L-08) |

**Hard governance (binding).** The referee is FROZEN. The redesign is a *predeclared* experiment:
its FPR is re-calibrated on the **dogfood-negative + synthetic-positive** (EXP-019 protocol) and the
new gate is **frozen before** it adjudicates any live candidate. The new gate must **not** be tuned
on CF-MR-002 (that is the exact selection bias L-12 warns against). Old frozen suite is retained and
reported in parallel until the new one is ratified on fresh draws.

## O2 — CF-MR-002 (causal RSI-2 fade), the benchmark vehicle

- **New family, not a reopen.** CF-MR-001 is CLOSED/REFUTED and not reopenable by re-parameterization;
  its closure note authorises a *new* family under its own D0 only **after** the `rct[di-1]` causal
  fix. CF-MR-002 is that family. See `docs/signal-registry/candidate-families/cf-mr-002.md`.
- **Entry:** RSI(2) fade, frozen 10/90 extremes (inherited definition, no re-tuning).
- **Exit:** reversion-completion target rested **only** from `rct[di-1]` (the causal limit). Engine =
  cTrader StrategyHost; Python is analysis-only on emitted `data/strategy_runs/`.
- **Execution convention:** decide at bar **open** on confirmed bars (`≤ t-1`); returns **open-to-open**;
  binding-leg slippage charged. Ships a future-destroying control (must collapse any edge).
- **Honest prior:** availability (gross MFE, no RCT limit) was real (EXP-089/G-020); net capturability
  is what was refuted. Expectation = causal bare fade is **not** net-tradable. A surprise either way is
  read on its own terms.

## O3 — architecture benchmark metrics

Record for the CF-MR-002 run: pipeline wall-clock per stage; approximate token cost; artifact count
(target 4: `design.md`, `code/`, `audit.md`, `report.md`); number of operator stops; and whether the
causal-provenance audit + leak tripwire fire correctly. Compare against the Chapter-01 8-stage norm.

## Sequencing (gates)

1. **G0 (this checkpoint):** ratify scope; register CF-MR-002; predeclare the O1 redesign criteria +
   FPR target + the synthetic-positive/dogfood-negative calibration set. 0 reads/slots.
2. **D-referee:** build + FPR-recalibrate the adaptive gate on nulls/synthetics; **freeze** (hash-pin).
3. **D-benchmark:** run CF-MR-002 causal in-engine through the lean pipeline; adjudicate on BOTH the
   frozen old suite and the newly-frozen adaptive gate (parallel disclosure).
4. **Critical decisions (operator-gated):** any counted TEST read; any deployability claim;
   credentialed/cost-bearing cTrader runs; anything holdout-adjacent. The global holdout is **not** in
   scope for Phase 001.

## Out of scope / deferred

Holdout release; CF-MR-002 deployment economics; the CF-MR-001 deferred levers (vol-regime,
contrarian, 25/75, 15m, cross-cuts). Each needs its own dated D0 + slot decision.

## Success criteria

- O1: an adaptive gate with FPR ≤ the frozen suite's on the dogfood-negative, finite power on the
  synthetic-positive, frozen before any live read — or a documented decision that the frozen suite is
  not improvable without losing FPR control.
- O2: a causal, leak-tripwire-passing CF-MR-002 verdict (net edge: yes/no/inconclusive) with the
  global holdout untouched.
- O3: a recorded efficiency delta (time/tokens/artifacts/stops) vs the Chapter-01 baseline.

## D0 — O1 referee-renew predeclarations (ratified 2026-06-27)

Derived and evidence-backed in `docs/referee-framework-redesign-plan.md` (consolidates the manual-author
assessment + 2 independent auditors, cross-validated against `python/src/xen/referee_calibration.py` +
`incremental_referee.py`). This section is the **binding** D0; the plan carries the derivation.

### Code-cross-validation outcome (what is real)
- **Refuted by code** (not defects): block-length runs on the **P&L series** not raw returns (`:964,972`);
  L3 vs-naive is the **difference-series** CI not two weak CIs (`:975,1037`).
- **Confirmed**: A charges cost **per-held-bar** vs B **per-episode** (`:538` vs `:131`) — cost-convention
  asymmetry (**F3/F9**); `L2_integrity=True` no-op (**F4**); "5-check" is **3 binding legs** L1/L3/L5
  (**F5**); MDE planted only vs **constant drift** (**F6**); single fixed naive control (**F7**); post-hoc
  component selection (**F8**); **verdict statistic = mean of sparse per-trade P&L** (**F10**, operator-raised).
- **Affirm, do not touch**: split discipline; B's model-free marginal estimator; F04 contiguous block length;
  one-bootstrap-across-α; negative anchors.

### Central synthesis & success criterion
- **Rigidity = bug AND asset → hard validity floor / soft economics.** Keep L1+coverage rigid, candidate-blind,
  FPR≈0; adapt only the economic legs (L3/L5) where Modes 1–2 demonstrably cost true positives.
- **Success = DET-dominance.** A redesign is adopted iff it **strictly lowers economic MDE at equal-or-better
  dogfood-negative FPR**. If none dominates, "frozen suite not improvable without losing FPR control" is
  **proven** (a valid Phase-001 null). This is Q8's operational definition.

### Ratified forks (operator, 2026-06-27)
| # | Decision |
|---|---|
| **Q1 FPR frontier** | Surgical small budget: validity floor hard at FPR≈0 & candidate-blind; small FPR (≤α) only on economic legs. |
| **Q4 composite form** | Primary **validity→economics** (§10.3a) + **single-statistic** variant (c), select by **DET-dominance**. Soft-vote **dropped**. |
| **Q6 scope universe** | **Full 17-instrument (VAL-003), 1h/4h only** (5m dropped). **Prereq E0:** freeze a predeclared **17-instrument per-instrument cost map** (current `ROUND_TRIP_COST_BPS:57-62` covers only 4) candidate-blind before any measurement. Per-instrument MDE becomes the powered default; per-stratum non-pooling unavoidable (17×2 cells). |
| **Q7 return convention** | **Re-baseline open-to-open `≤ t-1`** (Chapter-02 standing). Retained old suite keeps close-to-close for parallel disclosure. |
| **Q9 metric unit (F10)** | **Enforce dual reporting**: per-trade net-P&L **and** per-bar **return-series** stat (**Sharpe LB co-bound with Calmar/tail**, MTM per L-09, high-Sharpe scrutiny flag). DET-test whether the return-series stat **binds**. L5 gets a parallel return-series materiality floor (Phase-022 m\* style). **Scope note:** imports the Phase-022 deployment-stage lesson (assessment §11 sense 2) **upstream** into the referee (sense 1) — a deliberate O1 widening. |

### Adopted recommendations (evidence-based, not operator forks)
- **Q2 synthetic battery (do first):** predeclare **non-constant** edge shapes (dense, tail-only, sparse/event,
  state-dependent; sub→super-MDE) on the cells the frozen gate failed — extend `plant_positive_edge` beyond
  constant drift (F6).
- **Q3 dogfood draws:** reuse EXP-019 construction + fresh nulls; report FPR with **Wilson half-width** + draw
  count (`wilson_interval` exists); never "≈0".
- **Q5 threshold-derivation rule:** any candidate-matched threshold uses a **frozen, deterministic,
  performance-independent** rule computed on **calibration/planted data only** (never candidate realized returns).
- Plus: **binding component predeclared per candidate** (F8); **per-stratum verdict by construction** (L-03);
  **implement-or-delete L2** (F4); **reconcile spec↔code** leg names; **report decision-margin** alongside pass/fail.

### Experiment ladder (D-referee branch; all analysis-only until D-benchmark)
```
E0  Freeze 17-instrument cost map (Q6) + re-baseline returns open-to-open ≤t-1 (Q7). Candidate-blind. Prereq.
E1  Cost-control arm (lever 0): A with B-style amortized cost vs per-held-bar → isolate accounting (F3/F9)
    vs gate shape. Freeze-clean.
E2  Synthetic-positive battery (Q2) + fresh dogfood (Q3). Non-constant shapes; Wilson-bounded FPR. 17×{1h,4h}.
E3  Adaptive gate build: return-series unit (Q9/F10) + power-aware leg gating (lever 1) + validity→economics
    composite (Q4) + candidate-matched economic-leg thresholds (Q5). Per-stratum. Implement/remove L2.
E4  Robustness pass: threshold-perturbation Δverdicts; per-instrument 4h CI-width audit; bootstrap sensitivity;
    recent-regime disclosure.
E5  DET adjudication: adopt the dominating point OR record proven "not improvable". FREEZE + hash-pin
    BEFORE D-benchmark.
D-benchmark  CF-MR-002 causal in-engine; report on BOTH frozen old suite AND newly-frozen adaptive gate.
```

### Hard guards (binding)
Referee FROZEN until E5 freeze; new gate **never** tuned on CF-MR-002; global holdout sealed (not in Phase-001
scope); per-stratum binding verdicts (pooled = disclosure-only); no scope expansion after this G0; cost map +
return basis frozen candidate-blind at E0.

---

## AMENDMENT — E6 inserted: P*-capable referee variant (operator-ratified, 2026-06-29)

**Why.** D-benchmark (EXP-006) implementation surfaced a structural gap: CF-MR-002's faithful exit is an
intrabar **engine-realized `P*` favourable-limit fill** (operator-ratified, EXP-006 amendment A1), but
**both frozen gates** (Chapter-01 suite and §10.3a `gate_stack_adaptive`) consume **`position·market-
return` only** — no `strategy_fn` seam on the binding adaptive path; feeding a realized series requires
editing the hash-frozen module (forbidden). This is the same architecture limit that forced CF-MR-001's
bespoke intrabar fill engine (L-01 leak site): the cTrader-primary + frozen-referee stack adjudicates
**per-bar position-state** strategies only.

**Decision.** Insert a new D-referee rung **before** D-benchmark; **D-benchmark is BLOCKED** until it
freezes:
```
E6  P*-capable referee variant (EXP-007). Analysis-only. Add a realized-return adjudication path that
    consumes an engine-realized per-bar net series (generalize the E1 strategy_fn seam to the §10.3a
    adaptive form, additively — referee_adaptive stays byte-frozen; new path in a new module). FPR-
    recalibrate on the EXP-019 dogfood-negative + the E2 synthetic-positive battery; per-stratum;
    Wilson-bounded FPR. FREEZE + hash-pin BEFORE it adjudicates CF-MR-002 (L-12). 0 reads/slots.
D-benchmark  CF-MR-002 causal in-engine; adjudicate under the frozen old suite, §10.3a (position-state
    proxy), AND the newly-frozen E6 P*-capable gate (realized fill). Parallel disclosure.
```
**Guards (unchanged + extended).** §10.3a stays byte-frozen (E6 is additive, never mutates it); E6 is
**never** tuned on CF-MR-002 and frozen before any live read; the realized `P*` fill is the **engine's**
causal realized fill, audited (never a Python `rct` recompute — P-09). EXP-006 ID/design retained;
its run resumes post-E6-freeze.
