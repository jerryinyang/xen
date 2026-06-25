# EXP-091 — Pre-Execution Governance Review (Stage 4)

**Date:** 2026-06-24 · **Reviewer:** research-pipeline (consolidated Stage-4 governance) · **Artifacts:**
`scope.md`, `analysis-plan.md`, `code/run_experiment.py` · **Phase:** 021 (CF-MR-001 batch 2) · **HYP:**
`CF-MR-001/HYP-002`.

---

## Signal-registry precondition (programme file-drawer control) — PASS

- **Family admitted.** `CF-MR-001` is `ADMITTED (BINDING)` (G-020, 2026-06-23); first candidate slot consumed;
  lever = bare RSI-2 fade (CORE). Phase 021 consumes **0 additional slots** (`multiplicity-registry.md` §851).
- **Countable items registered before measurement.** The six exit families screened (EXIT-RCT, EXIT-ERT,
  RSI-revert-on-close, fixed-bar, ATR triple-barrier, favourable partial/trail) are all entered in the Phase 021
  batch (§854), single frozen parameter point each. No new countable item is introduced.
- **No new selection statistic ⇒ no bite-check** (D0 header; binding gate = the frozen referee suite, screen
  statistic = the established net `ci_low_1s>0` EXP-046/056 quorum).
- **TEST-stratum tally stated.** EXP-091 reads the TRAIN sub-split only; all 48 strata are **0/2 counted reads,
  open** (`test-read-ledger.md`, re-materialized 2026-06-21). EXP-091 spends **0** (TRAIN-only disclosure).

## Phase-alignment check — PASS

EXP-091 is the design §4 / §3 exit-capture-geometry screen for the admitted lever, on the EXP-090 member set,
TRAIN-only, gross + EXP-085 cost, native pair vs conventional contrast, with the frozen D6 net-clear + quorum
rule. Domains {15m,1h} only (4h not carried). Matches the checkpoint objectives exactly.

## Pre-execution issue caught and resolved (recorded) — D0-amendment-003

A **verdict-material specification gap** was found at Stage 3: the inherited EXP-085 `COST_CONSTANTS` prices only
4 instruments, but the member set spans 13 — leaving only 4 priceable cells over 3 instruments, below the ≥5/≥3
quorum, which would have **forced** a spurious `SCREEN_EMPTY` → NOT_TRADABLE by cost-coverage rather than
economics. Resolution (operator-ratified `D0-amendment-003`, FROZEN 2026-06-24): a global OHLC-spread RT rule was
**attempted and empirically refuted** (Abdi–Ranaldo / Corwin–Schultz both ~10× inflated or degenerate on this
no-quoted-spread data — recorded), so a **Phase-021-local conservative cost table** (`RT_i = 4·c_i` from
documented anchors + conservative tiers; **`F_i = 0`** per operator decision, immaterial at the ~3-bar hold) was
frozen. The shared `xen.capgeo_cost.COST_CONSTANTS` is **not** mutated (Phase-018 integrity); the experiment
imports only the cost mechanics. This is the proper deviation handling (dated amendment + operator ratification
before any binding run), not a silent fix.

---

## Constraint checklist

### Scope (`scope.md`)
- **Hypothesis** testable/falsifiable (net-clear quorum; empty ⇒ NOT_TRADABLE). **PASS**
- **Boundaries** explicit: 20 member cells, {15m,1h}, frozen entry/exit slate, EXP-085 cost (as amended),
  exclusions enumerated (regime/variants/4h/expansion deferred). **PASS**
- **Success/failure/inconclusive** concrete (≥5 cells/≥3 instruments; SCREEN_EMPTY; per-cell INCONCLUSIVE).
  **PASS**
- **Holdout exclusion** explicit (TRAIN sub-split; analysis-TEST + final-30% never sliced incl. 1m fill bars).
  **PASS**
- **Real-price rule** explicit (real OHLC / real 1m fills; no HA/Renko). **PASS**
- **Gate-threshold calibration:** `net ci_low_1s>0` and `≥5/≥3` are **frozen D6** (inherited EXP-046/056 quorum,
  not a magic constant); margin (EXP-090 MDE) carried not applied. **PASS**

### Analysis Plan (`analysis-plan.md`)
- **Method justification** with "why / simpler alternative" for each step (block bootstrap vs i.i.d./t; 1m
  resolution vs bar-close; Wilcoxon vs sign/pooling). **PASS**
- **Assumptions** listed (block-exchangeability; cost as additive location shift; ATR-unit commensurability).
  **PASS**
- **Per-stratum endpoints:** binding net-clear is per (cell×arm); quorum is the predeclared D6 aggregation, not a
  collapsed verdict; pooled/native-vs-contrast figures declared **disclosure-only**. **PASS**
- **Shape-aware / robust+raw:** mean lower bound is binding **and** median co-reported per cell (the EXP-089
  median-positive/mean-fragile signature is explicitly watched). **PASS**
- **Interpretation guide** predefined (if-X-then-Y, incl. SCREEN_EMPTY routing and mean-vs-median split). **PASS**
- **Budget:** 2 tests / ≤2, 4 plots / ≤4, 0–1 modules / target 0–1. **PASS**

### Code (`code/run_experiment.py`)
- **Plan compliance:** implements exactly the 7 steps + 4 plots; no bonus analyses. **PASS**
- **Holdout exclusion:** TRAIN slice inherited verbatim from EXP-090 `load_train_1m` (`int(int(total·0.7)·0.7)`);
  1m fill walk clips at the TRAIN edge in the reused `xen.intrabar_fill`. No holdout/analysis-TEST path. **PASS**
- **Look-ahead / timestamp alignment:** entries/targets causal; 1m→domain mapping by timestamp (`searchsorted`),
  never bar index (reused engine). **PASS**
- **Real-price outcome:** `net_return_atr` on real fill levels + real ATR; cost in ATR units; no synthetic price.
  **PASS**
- **Verdict representation (per-stratum):** per-(cell×arm) `net_clear` written to `screen_per_cell_arm.csv`; the
  experiment verdict is the **deliverable** `SCREEN_DELIVERED[_EMPTY]` driven by the frozen D6 quorum — a
  predeclared count over per-stratum net-clears, **not** a collapsed `.all()` masquerading as the binding read.
  **PASS**
- **NaN / edge cases:** `UNRESOLVED_EMPTY` guard (n_resolved<2 ⇒ not a net-clear, denominators shown); `keep`
  mask excludes non-finite/`atr≤0`/`hd<0`; no `0/0`. **PASS**
- **Separation / sectioning / type hints / docstrings:** VAL-001 sectioning; pure compute vs plotting vs
  orchestration separated; typed public fns. **PASS**
- **No magic numbers:** all constants frozen at D0 / amendment-003 (RT table, N_BOOT, BOOT_ALPHA→Z=1.645,
  quorum). **PASS**
- **Import side effects:** none (dirs created in `run()`; `matplotlib Agg`; EXP-090/VAL-005 modules import-safe).
  **PASS**
- **Determinism:** master seed + content-addressed `seed_for`; 2-cell replay asserts net_ci_low/net_clear
  frame-identical; SHA-256 output pin. **PASS**
- **Safe optimization / vectorization discipline:** bootstrap vectorized via frozen `xen.ass`; the causal 1m walk
  remains the explicit bounded sequential loop in the reused engine (not vectorized). **PASS**
- **Progress / logging:** `tqdm` over the 20-cell loop; helpers quiet/return data. **PASS**
- **Plot memory / reuse:** plots built from collected `ArmResult`s; no reloads. **PASS**
- **Cost-table provenance:** Phase-021-local, hash-recorded; shared module untouched. **PASS**

### Disclosed deviation (non-blocking)
`PARTIAL-TRAIL` uses the domain-bar `partial_two_leg_exit` resolver (coarser than the 1m engine), per D2.4 "as
the primitive allows"; it is a **non-primary contrast** arm — recorded in `run_metadata.json`
(`partial_arm_note`). The five primary arms (both natives + 3 contrasts) use the 1m engine. Does not affect the
native-vs-reactive A/B (RCT vs RSI-revert-on-close) or any binding figure.

### Smoke verification
1-cell debug run (EURUSD-1h) executed end-to-end in ~9s; determinism replay passed; partial outputs cleared.
The binding 20-cell run is the operator's to execute (manual execution gate).

---

```text
VERDICT: APPROVE
```
