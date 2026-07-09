# Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark (Chapter 02 opener) — Retrospective

**Phase number:** 001 (Chapter 02)
**Design ratified:** 2026-06-27 (G0)
**Retrospective written:** 2026-06-30
**Status:** COMPLETED — all three objectives met: (O1) renewed referee FROZEN at §10.3a, q\*=0.75 + E6 P\*-capable variant ADOPTED; (O2) CF-MR-002 EXONERATED — NOT-TRADABLE 34/34; (O3) architecture benchmark delivered — lean pipeline verified, 3 infra bugs fixed.
**Slots/reads:** 0 candidate slots, 0 counted TEST reads; global holdout sealed throughout.

**Design reference:** [design.md](design.md) · [E0-frozen-constants.md](E0-frozen-constants.md)
**Amendment A1 (EXP-003):** studentized sub-pop statistic — cured the high-σ FPR leak at the gate (operator-directed, inline)
**Amendment A2 (EXP-006, superseded):** deferred D-benchmark for E6 P\*-gate — operator decision 2026-06-29
**Experiments:** EXP-001 [E1], EXP-002 [E2], EXP-003 [E3a], EXP-004 [E4], EXP-005 [E5], EXP-007 [E6], EXP-006 [D-benchmark] — see `python/experiments/<ID>/report.md`.

---

## 1. Phase objective recap

Phase 001 was the Chapter-02 opener with dual purpose: (i) **referee renew** — replace the rigid fixed-threshold conjunctive gate (L-12 failures) with a power-aware, candidate-matched adaptive scheme that preserves or improves FPR control while fixing the over-rejection and mis-scaling modes; and (ii) **architecture benchmark** — push the causal RSI-2 fade (CF-MR-002) through the new cTrader-primary lean pipeline to measure correctness, efficiency, and resolve L-01's causal question. Three concrete objectives ([design §2](design.md)):

1. **O1 — Referee adaptivity (methodological).** Replace rigid fixed-threshold conjunctive gating with a power-aware, candidate-matched scheme that keeps or improves FPR control but stops over-rejecting and mis-scaling. Validate on nulls + synthetics; freeze before any live read.
2. **O2 — Causal RSI-2 (CF-MR-002).** Re-run the RSI-2 fade with `rct[di-1]` causal exit in the cTrader engine (look-ahead impossible by construction), bar-open/open-to-open convention. Establish whether the bare fade has any net edge once causal. Honest prior: NO.
3. **O3 — Architecture benchmark.** Record wall-clock + token cost + artifact count for the full lean pipeline run vs the Chapter-01 8-stage baseline, as the rollover's efficiency proof.

The hard governance guard: the renewed referee must be **frozen before** it adjudicates any live candidate (L-12 selection-bias guard); L-01's causal-provenance pass + leak tripwires are mandatory.

## 2. Outcomes vs objectives

| Objective | Outcome | Evidence |
|-----------|---------|----------|
| **O1 — Referee adaptivity** | **COMPLETE** — renewed referee FROZEN at §10.3a, q\*=0.75 (E5); E6 P\*-capable variant ADOPTED and hash-pinned (EXP-007). Both frozen before any live read. | E0→E5 ladder: all 5 rungs COMPLETE with audit PASS, 0 Critical. E6 additive variant FPR-recalibrated and frozen. |
| **O2 — Causal RSI-2 (CF-MR-002)** | **COMPLETE** — CF-MR-002 **EXONERATED** (NOT-TRADABLE 34/34). L-01 falsification confirmed on the faithful engine-fill mechanism: the causal RSI-2 fade is net-negative on all 34 strata. | EXP-006: all 3 referees REJECT every cell; net P&L −0.03…−9.66 bps/active bar; T1 future-destroy collapsed at 0.000/34; T2 provenance clean 34/34. Audit PASS, 0 Critical. |
| **O3 — Architecture benchmark** | **COMPLETE** — lean pipeline verified. 3 latent `run-experiment.sh` infra bugs exposed and fixed in the first price-primary run. Pipeline efficiency measured. | EXP-006 O3 observations: stamp-suffix completion, flush race, report-json gate, symlink race, cost-map limit, benign shutdown exception. KB-lesson candidate documented. |

---

## 3. The experiment arc

### D-referee ladder (E0→E5): all analysis-only, 0 reads, holdout sealed

| Rung | EXP | Role | Outcome | Key finding |
|------|-----|------|---------|-------------|
| **E0** | _prereq_ | Freeze 17-instrument cost map + re-baseline open-to-open ≤t-1 | Candidate-blind prereq; `E0-frozen-constants.md` pinned before any measurement. | The Chapter-01 frozen cost map covers only the 4-core; the renewed E0 map generalizes to the full 17-instrument universe. |
| **E1** | EXP-001 | Cost-control arm: amortized vs per-held-bar cost | **COMPLETED** — ACCOUNTING_MATERIAL: per-held-bar over-charges turnover ~L×; amortizing recovers ΔMDE 1.0–11.5 bps/stratum (median 1.5). | L-12 Mode-1 partly accounting, not just gate shape. Suite byte-unchanged. |
| **E2** | EXP-002 | Synthetic-positive battery + dogfood (non-constant shapes) | **COMPLETED** — frozen gate SHAPE-BLIND: structurally blind to SPARSE/event edges (L1 veto, edge-independent), degraded on STATE (L5 pooled mean). FPR=0/32 + dogfood 0/64. | Confirms L-12 §1/§2; localizes blindness to L1+L5 → scopes E3. Leak-clean. |
| **E3a** | EXP-003 (+ A1) | Adaptive gate: return-series unit + power-aware + validity→economics composite | **COMPLETED** — **DET-DOMINANT 32/32** (post-A1 re-audit PASS). Adaptive recovers STATE (ΔMDE median 7.5, max 23.5 bps) + sparse 28/32; dogfood FPR 0/32 ≤ frozen. | **A1 story:** original raw-bps q\*-quantile over-fired on high-σ 4h nulls (brittle "15/17") → studentize the sub-pop statistic (`q\*-quantile/std > Q_STUD_MIN=Φ⁻¹(q\*)`, candidate-blind) → cured the FPR leak at the gate. Designed "sparse UNPOWERED" predeclaration REFUTED. |
| **E4** | EXP-004 | Robustness: q\*/bootstrap-seed/skew sweep | **COMPLETED** — **FREEZE LICENSED (RANGE-BOUNDED)**. Baseline q\*=0.75 = 32/32 DET_DOMINANT. Safe range {0.7,0.75}. Skew-FPR refuted 0/32. All FPR_BROKEN are single-draw artifacts (true FPR ≤0.62%). | E5 precondition recorded: min-pass-count≥2 / control-relative FPR rule for freeze-adjudication. Regression anchor 0/32. |
| **E5** | EXP-005 | DET-adjudication + FREEZE (+ Q4 form-check) | **COMPLETED** — **RENEWED REFEREE FROZEN** at §10.3a, q\*=0.75; `sha256=b4fd6cb1…ae847`. Q4: §10.3a matches/beats variant-c 32/32. **Variant-c REFUTED** — single-statistic has no absolute floor → admits anything less-bad than a losing momentum baseline; dogfood FPR up to 1.0, survives future-destroy. | §10.3a's neutral-CI + materiality + studentized-subpop legs supply the FPR control variant-c lacked. D-referee ladder E0→E5 complete. |

### E6 — Insertion by operator decision (2026-06-29)

| Rung | EXP | Role | Outcome | Key finding |
|------|-----|------|---------|-------------|
| **E6** | EXP-007 | P\*-capable referee variant (additive) | **FROZEN — ADOPTED** (audit PASS, 0 Critical). `referee_pstar.gate_stack_pstar` hash-pinned (`sha256=1fd06b28…4f23`). Additive to §10.3a; prior suites byte-unchanged (hash == E5). Arm R reduction identity **32/32 bit-identical**. Arm N realized-fill FPR controlled (symmetric 0/32, dogfood 0/32, future-destroy max 1/80). Arm P finite power 32/32 (MDE 0.5–4.0 bps). | Inserted because D-benchmark surfaced a structural gap: **both frozen gates** (Chapter-01 and §10.3a) consume `position·market-return` only — no `strategy_fn` seam on the binding adaptive path. E6 fills the gap additively. Honest caveat: returns-space bracket caps not captures — true intrabar `P*` capture exercised by real engine in D-benchmark. |

### D-benchmark (2026-06-30) — price-primary, cTrader engine

| EXP | Role | Outcome | Key finding |
|-----|------|---------|-------------|
| **EXP-006** | Causal RSI-2 fade (CF-MR-002/HYP-001) — in-engine adjudication under 3 parallel referees | **COMPLETED — NOT-TRADABLE 34/34, audit PASS, 0 Critical.** All gates REJECT every cell. Net P&L negative on all 34 (−0.03…−9.66 bps/active bar). Gate C (faithful P\*) ci_lower<0 everywhere (−0.22…−5.14). Gate B 0/34 PASS; Gate A 0/8 scored (26 N/A — frozen cost map only on 4-core). | **Binding leg: L3 neutral floor** — the fade beats naive momentum (vs-naive +0.87 @ EURUSD/1h) and clears raw materiality, but is **net-negative in absolute terms** (fails studentized sub-pop guard). T1 0.000/34, T2 34/34 → **leak-clean**. L-01 falsified on the **faithful** mechanism (real engine intrabar `P*` fill). O3: 3 infra bugs fixed (`run-experiment.sh`). |

---

## 4. Key decisions (operator-gated, all ratified)

| # | Decision | When | Rationale |
|---|----------|------|-----------|
| **A1** | Studentize the sub-pop L5 statistic (q\*-quantile/std, candidate-blind) | EXP-003, 2026-06-29 | Original raw-bps q\* over-fired on high-σ 4h nulls (brittle "15/17 FPR_BROKEN" — 16/17 within Wilson noise of 0). Amendment cured the FPR leak **at the gate** with STATE recovery retained. Pulled E3b's return-series unit forward. |
| **E6 insert** | Build P\*-capable referee variant before D-benchmark | 2026-06-29 | D-benchmark implementation exposed structural gap: both frozen gates adjudicate position·market-return only; injecting an engine-realized series requires editing a hash-frozen module (forbidden). E6 fills the seam additively, FPR-recalibrated and frozen before adjudicating CF-MR-002. |
| **§10.3a adopt** | Adopt validity→economics composite over single-statistic variant-c | E5, 2026-06-29 | variant-c has no absolute floor — admits anything less-bad than a losing momentum baseline (dogfood FPR up to 1.0, survives future-destroy). §10.3a's neutral-CI + materiality + studentized-subpop legs supply the FPR control. |
| **E6 freeze** | FREEZE and ADOPT `referee_pstar.gate_stack_pstar` | 2026-06-29, operator sign-off | Additive path: §10.3a with signal leg from injected engine-realized series. Prior suites byte-unchanged (hash == E5). FPR-controlled, finite power, leak-clean. |

---

## 5. Learnings and observations

### O3 — Infrastructure bugs exposed by first price-primary run
1. **Stamp-suffix completion detection (4h hang/cell).** The `run-experiment.sh` timestamp-suffix strategy didn't reliably detect completion on long-running 4h cells.
2. **Flush race on natural container exit.** cTrader container exit could race with the parquet flush, producing a false-incomplete + skipped sibling cell.
3. **`report.json` completion gate unmet.** A benign cTrader console crash on shutdown after a valid parquet flush left the completion gate unset.
4. **(Operational note) Parallel `one`-invocation symlink race.** `prepare_cache_layout` symlink setup races under parallel invocations → subset reruns must be sequential.
5. **Frozen suite cost-map limit.** The frozen Chapter-01 referee's cost map covers only the 4-core (EURUSD/XAUUSD/BTCUSD/USTEC); the renewed §10.3a (E0 17-instrument map) generalizes to the full universe.
6. **Benign cTrader shutdown exception.** The cTrader console throws a benign state-machine exception on shutdown after emitting valid parquet — data integrity unaffected, but noisy.

### L-01 closure
The L-01 falsification now lands on the **faithful mechanism** (real engine intrabar `P*` fill, not a capped proxy). CF-MR-001's "tradable" arc was the EXIT-RCT look-ahead, now structurally impossible in-engine. The 11 EXP-093 counted reads and EXP-097 holdout shot remain spent-on-defect, non-refundable.

### Methodology validation
- **Power-aware gating (lever 1) validated:** structurally-impossible legs detected as `UNPOWERED` instead of auto-fail (Mode 2 fixed).
- **Candidate-matched thresholds validated:** MDE-curve co-designed with the band replaces fixed plants (Mode 3 fixed).
- **Calibrated composite validated:** hard AND replaced with studentized-subpop guard, neutral-CI floor, materiality leg (Mode 1 fixed).
- **Per-stratum binding verdicts enforced throughout:** no pooled-as-verdict errors (L-03 clean).
- **Leak tripwires (T1 future-destroy, T2 provenance) mandatory in every price-primary experiment — proven effective.**


---

## 6. Programme state after Phase 001

- **Renewed referee FROZEN** (2026-06-29, E5 §10.3a, q\*=0.75 + E6 `referee_pstar.gate_stack_pstar`). Both hash-pinned in `freeze_manifest.json`. Prior Chapter-01 suite byte-retained.
- **CF-MR-002** status: `SCREENED — EXONERATED (NOT-TRADABLE 34/34)`. 0 slots, 0 counted TEST reads, holdout sealed. Family retained in registry (never deleted). Deferred levers (vol-regime, 25/75, 15m, regime×variant cross-cuts) each require a fresh D0 + slot.
- **0 candidate slots consumed** across all Phase 001 experiments. **0 counted TEST reads spent.** Global holdout **sealed** throughout.
- **Signal-registry unchanged** by Phase 001: CF-MR-002 moved from REGISTERED → SCREENED-EXONERATED; no other family opened, advanced, or retired.
- **TEST-read ledger unchanged by Phase 001:** 0 counted reads consumed. Pre-Phase-001 tallies unchanged: 11 strata at 1/2 (from EXP-093, Chapter 01), the remaining 37 at 0/2. All 48 strata (16 instruments × {15m,1h,4h}) open for at least 1 counted read.
- **Phase 001 closes with the programme at the G-019 terminal branch state**, modified by the fade/mean-reversion exoneration: all **opened** entry-side information axes on price-derived data — directional (3 families), magnitude (CF-VOLEXP-001), relational (CF-XSECT-001), mean-reversion fade (CF-MR-002) — are now **screened and closed/exonerated** (CF-FLOW-001 reserved-conditional, never opened). The programme frontier is the G-019 terminal branch: **non-price data acquisition** (order book, cross-asset, fundamentals) — a data/infrastructure decision, not a modelling one.

### Compared to Chapter-01 Phase 022 (pre-rollover state)
| Dimension | Chapter 01 (Phase 022) | Chapter 02 (Phase 001) |
|-----------|----------------------|------------------------|
| **Referee** | Fixed-threshold conjunctive (L-12 failure modes active) | Power-aware adaptive (§10.3a, q\*=0.75) + P\*-capable variant, both FROZEN |
| **Execution** | Python vectorized (L-01 leak site) | cTrader-primary (look-ahead impossible by construction) |
| **Pipeline** | 8-stage, separate governance artifacts | 4-artifact lean, inline governance, autonomous orchestrator |
| **Pipeline cost** | ~98 experiments, ~25 phases, multiple governance layers | 7 experiments (E0→E5, E6, D-benchmark), 1 phase, all gates inline |
| **Causal correctness** | Broken — L-01 look-ahead in shared outcome module | Proven — T1 future-destroy + T2 provenance per experiment, leak-clean on all |
| **Reads/slots consumed** | 11 counted TEST reads (spent-on-defect), 1 holdout shot (spent-on-defect), slots consumed | 0 counted TEST reads, 0 slots, holdout sealed |

---

## 7. Proposed next direction

Phase 001 completes with the programme at the **terminal branch** of the screened price-derived surface. The operator-gated decision on the next direction is:

1. **Non-price data acquisition** — scope the infrastructure needed to collect and integrate orthogonal data (order book, cross-asset structure, fundamentals). This is an INFR-phase (infrastructure) decision, not a research experiment.
2. **Run Screen F — CF-FLOW-001** — the reserved-conditional order-flow axis as a final cheap screen on the existing dataset. Broker-dependent tick-volume was found inert once (EXP-046), so the honest prior is lower than X; but it is the last unmeasured cell of the availability 2×2.
3. **Other operator-defined direction.**

See the companion orchestrator status report (`python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`) for the current EXTERNAL WAIT state.

---

*Phase 001 CLOSED (2026-06-30). Design: [`design.md`](design.md) · E0 constants: [`E0-frozen-constants.md`](E0-frozen-constants.md). Experiments: EXP-001/002/003/004/005/006/007. Family index: [`docs/experiments-docs/families/cf-mr-002/INDEX.md`](../../families/cf-mr-002/INDEX.md).*