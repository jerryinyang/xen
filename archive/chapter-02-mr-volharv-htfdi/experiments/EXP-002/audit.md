# Audit Report: Experiment EXP-002 (E2 — Synthetic-Positive Battery + Dogfood)

## Summary

- **Verdict**: PASS. The blindness map is independently reproduced, the mechanism is confirmed at
  the **leg level**, FPR control holds (0/all strata + dogfood 0/64), the frozen suite is
  byte-untouched, the promotion is behaviorally identical, and the dogfood causal lag is correct
  (no look-ahead). No verdict-material findings.
- **Critical**: 0
- **Warnings**: 2 (interpreter framing — sparse "inflated-9" are effectively blind; tail-robustness
  refines L-12 and re-scopes E3)
- **Info**: 2

Classification: **analysis-only** — confirmed (synthetic exogenous positions + planted oracle
stimulus + frozen primitives; no price→signal). Not price-primary.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | MDE/DETECTED_FLOOR, classify, FPR, future-destroy re-derived; match. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `slice(0,0.7n)` on CloseTime-sorted minutes + domain fence; global 30% never collected. |
| `code/run_experiment.py` | Causal lag | PASS | `lag_open_to_open` (Critical-class area) verified correct — see Causal Provenance. |
| `code/run_experiment.py` | Determinism | PASS | all draws seeded; reused suite `wilson_interval` (no local re-roll). |
| `code/edge_shapes.py` | Matched-magnitude | PASS | mean drift over each shape's denominator == DENSE δ (asserted + re-verified). |
| `code/edge_shapes.py` | Shape constructions | PASS | tail/sparse/state correct; constants `F_TAIL/A_SPARSE/FRAC_A` module-level, performance-independent. |
| `src/xen/referee_adaptive.py` | Promotion integrity | PASS | promoted `strategy_return_bps_turnover`+`entry_mask` **behaviorally identical** to EXP-001 local (`np.array_equal` on outputs). |
| `src/xen/referee_calibration.py` | Frozen integrity | PASS | `git diff` empty — **byte-unmodified**. |

---

## Numerical Validation

### Independent blindness re-derivation (binding = amortized)

| Cell | Shape | MDE (re-derived) | per_shape.csv | Class | Match |
|---|---|---|---|---|---|
| EURUSD/1h | SPARSE | inf | inf | DENSE_ONLY_BLIND | ✓ |
| BTCUSD/4h | SPARSE | inf | inf | DENSE_ONLY_BLIND | ✓ |
| XAUUSD/4h | STATE | 8.0 | 8.0 | DETECTED | ✓ |

Matched-magnitude (EURUSD/1h, e=8): per-state-A mean == DENSE δ (`np.isclose` True); pooled/δ = 0.51
≈ `FRAC_A` 0.5. ⇒ blindness is **shape**, not magnitude.

### FPR control

Abstract-null FPR max = **0.000** both conventions, all 32 strata (Wilson hw ≈ 0.026 at 160 draws/
stratum). Dogfood (Donchian R + MA 20/50, causally lagged, no plant): **0/64** PASS both conventions
(Wilson hw 0.028). Null control sound — no calibration break.

---

## Verdict Forensics

### Per-stratum re-derivation & masking

| Shape | Binding map | Masking check |
|---|---|---|
| DENSE | DETECTED 32/32 | anchor; uniform |
| TAIL | DETECTED 32/32 | uniform; MDE ≈ DENSE (within ~1 grid step) |
| SPARSE | 23 DENSE_ONLY_BLIND + 9 MDE_INFLATED | **the 9 inflated only reach grid-top 32 bps** (marginal) — effectively blind; pooled "sparse blind" does **not** mask a robust subset. Spans all cost tiers (1.0→10.0) → not cost-driven. |
| STATE | 15 DETECTED + 17 MDE_INFLATED | inflation ~2–4× DENSE; the DETECTED 15 are where DENSE MDE is already coarse-grid-adjacent (≤1 step) so "inflated" and "detected" are grid-resolution-adjacent, not two regimes. |

Pooled headline is a disclosure; the per-stratum picture is homogeneous within each shape. No masking.

### Mechanism (leg-level trace — gate_stack_row `leg_results`, EURUSD/1h)

| Shape | e=2 | e=8 | e=32 | Driver |
|---|---|---|---|---|
| DENSE | pass | pass | pass | — (192/192 episodes, eff_n 6462) |
| **SPARSE** | veto **L1+L5** | veto **L1+L5** | veto **L1+L5** | **L1_readiness structural**: test episodes **16/27 < min_state_count 20** → L1=False at **every** e incl. 32. Edge-independent. (L5 also vetoes on the diluted mean.) |
| **STATE** | veto **L5** | pass | pass | **L5_materiality**: pooled mean halved (pooled/δ=0.51) → below the materiality floor until e≈2× lifts it. (L1 fine, 192/192.) |
| TAIL | pass | pass | pass | none — matched mean + dense activity; all mean-based legs see the DENSE mean. |

**Mechanism hypotheses (a)/(b)/(c) all CONFIRMED:**
- (a) **SPARSE blindness = the L1 readiness leg** (too few state-episodes at ~6% activity), structural
  and edge-independent — the L-12 §2 "structurally-impossible leg". Not insufficient
  `N_PLANT`/bootstrap (L1=False even at e=32). ✓
- (b) **STATE inflation = L5 materiality on the pooled-diluted mean** (L-03 pooling; frac_A=0.5 →
  ~2× MDE). Per-state magnitude matches DENSE. ✓
- (c) **TAIL robust** — matched mean + dense activity; tail concentration perturbs variance/stability
  (L4) but not the location/materiality legs that bind. MDE ≈ DENSE. ✓

### Gate-shape check

This experiment **is** the gate-shape check: the frozen conjunctive gate is the correct instrument
for **dense+location** edges, **structurally blind** to **sparse/event** shapes (L1 veto), and
**degraded** on **sub-population/state** shapes (L5 on the pooled mean). It is **not** blind to tail
concentration per se. This distinguishes "no effect" from "effect of a shape this gate cannot see"
for the sparse/state shapes — recorded for the interpreter; **the gate was not retro-edited**.

---

## Causal Provenance & Leak

### Provenance trace (verdict-bearing inputs)

| Column | Inputs & timestamps | ≤ t (≤ t-1 next-bar)? | Lines |
|---|---|---|---|
| real returns | open-to-open `log(Open[t+1]/Open[t])` | YES | `referee_adaptive.next_open_to_open_returns_from_bars` |
| synthetic positions (persistent/sparse/state) | seeded RNG, **no price input** | YES (trivially) | `edge_shapes.py` |
| planted edge (4 shapes) | `returns + drift·states` — exogenous oracle stimulus | N/A (stimulus, not a tradable signal) | `edge_shapes.py` |
| **dogfood positions** (Donchian, MA) | domain **Close[i]** → **lagged +1 bar** | **YES** — verified below | `run_experiment.lag_open_to_open` + `dogfood_pass` |

**Dogfood causal lag (developer deviation — verified correct):** `donchian_breakout_positions` /
`ma_crossover_positions` form state from bar `i`'s close (`raw[i]`), then the harness applies
`lag_open_to_open` (prepend a flat bar, drop last): verified `lagged[0]==0` and
`lagged[i]==raw[i-1]`. So the position acting at the open-to-open return `r[i]` (act at bar `i`'s
open) uses signal computed only through **close[i-1] ≤ t-1**. **No look-ahead.** Synthetic/abstract
substrates read no OHLC → no lag needed (correct). This deviation is a **correctness improvement**:
without it the dogfood null would carry a one-bar look-ahead (the L-01 off-by-one class).

- `rct[di]`-style own-close intrabar limit: **none** (no intrabar limits).
- Returns **open-to-open** (not open-to-close): YES.
- Decision-on-forming-bar: **none** — synthetic positions are exogenous; dogfood is lagged to ≤t-1.

### Leak tripwires

| Tripwire | Result |
|---|---|
| **Future-destroy** (block-permute planted returns → re-gate) | **HELD** — collapsed to ≤FPR on every detecting shape (run asserted; construction verified: permutes the planted series, destroying position↔return alignment). A surviving detection would be REJECT-class; none. |
| **No-plant guard** (shape positions, no drift → ~FPR) | **HELD** both conventions. |
| **FPR control** (null Wilson-upper ≤ 2α) | **HELD** — FPR 0 everywhere. |

### Shared-module provenance contracts

- `edge_shapes` docstrings (matched-magnitude; exogenous-stimulus, no OHLC read) match the code.
- `referee_adaptive` promotions carry the EXP-001 provenance note; behavior identical.
- `gate_stack_core_costfn` seam unchanged (E1-audited bit-identical at `strategy_return_bps`).

### Price-primary check

Not price-primary; correctly not run in cTrader; no `data/strategy_runs/`. Cost charged as the E0
frozen round-trip on the signal leg. ✓

---

## Scope Compliance

- Plan followed: **YES**, with two surfaced deviations — (1) promotion of the turnover helpers to
  `referee_adaptive` (design-anticipated reuse; behaviorally identical; EXP-001 local copy left as
  its frozen record); (2) the dogfood causal lag (correctness addition, verified no look-ahead).
  Neither expands scope.
- Budget: shapes 4 / conventions 2 / **plots 3** / **new module 1** (`edge_shapes` + harness) —
  within the comparative budget.
- Holdout: first-70% minute slice + domain fence; global 30% never collected; DE30 skipped
  (no 5-year file). ✓

---

## Issues

### Warning

1. **SPARSE "MDE_INFLATED 9" are effectively blind, not a robust subset.** Those 9 cells reach a
   finite MDE only at the **grid top (32 bps)** — far above any usable edge. The interpreter should
   report SPARSE as ~uniformly blind (23 fully + 9 only-at-32), not "23 blind / 9 detected". Cannot
   move the binding classification (UNPOWERED vs detected-at-32 are both "gate cannot see a usable
   sparse edge"); framing only.

2. **TAIL-robustness refines L-12 and re-scopes E3.** The blind spots are **activity** (sparse → L1
   readiness) and **pooling** (state → L5 materiality), **not tail concentration**. E3's composite
   should target (i) a power-aware L1 that applies only where it has finite MDE (don't veto sparse
   structurally) and (ii) a sub-population/per-state read so L5 isn't fooled by a pooled-diluted
   mean — **not** a generic "tail shape" fix. Framing/scoping for the interpreter + E3; cannot move
   any E2 number.

### Info

1. **Sparse carries a dual L1+L5 veto.** Even a power-aware L1 (E3) would still face L5 materiality
   on the sparse diluted mean. E3 must address both legs for sparse, not L1 alone.
2. Compute as-run (`N_PLANT=20, N_NULL=80, N_BOOTSTRAP=500`) is adequate: the binding sparse veto is
   L1=False (deterministic given the substrate), not a bootstrap-noise boundary, so raising resamples
   would not change the sparse classification.

---

## Materiality & Re-Audit Requirements

- **No blocking findings.** Both Warnings are interpreter framing and provably cannot move a
  blindness classification, the FPR, or temporal validity. No fix+rerun required.
- **Verdict status:** the E2 blindness map is independently reproduced, mechanism-confirmed at the
  leg level, FPR-controlled, causally sound (dogfood lag verified), frozen-suite intact, promotion
  behaviorally identical. **Audit PASS.** Warnings 1–2 carried to the documenter/interpreter.
