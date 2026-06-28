# Audit Report: Experiment EXP-001 (E1 — Cost-Control Arm)

## Summary

- **Verdict**: CONDITIONAL PASS — ΔMDE result is sound and independently reproduced; one shipped
  leak-tripwire (`no-real-edge guard`) is **mis-specified** and fired 12× on correct gate
  behaviour. Guard must be corrected + re-executed before Stage 5. **The ΔMDE verdict cannot move
  on rerun** (proven below).
- **Critical Issues**: 1 (mis-specified no-real-edge guard → fix + re-execute)
- **Warnings**: 2 (ΔMDE units framing for the interpreter; 4h low-power partial passes)
- **Info Notes**: 2

Classification: **analysis-only** — confirmed (synthetic exogenous positions, planted edge, no
price→signal). Not price-primary; cTrader engine correctly not invoked.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | FPR/MDE/ΔMDE logic re-derived independently; matches. |
| `code/run_experiment.py` | Holdout exclusion | PASS | Lazy `slice(0, 0.7n)` on CloseTime-sorted minutes; domain fence `CloseTime ≤ last minute`. Global 30% never collected. |
| `code/run_experiment.py` | Loader ordering | PASS | `sort("CloseTime")` before slice; per-instrument 5-year-era glob (`20210602_*`), no era mixing. |
| `code/run_experiment.py` | Determinism | PASS | All draws seeded (persistent 6000+k, gate 7000+k, nulls 1000–5000+k). |
| `code/run_experiment.py` | Import side effects | PASS | `mkdir` only in `main()`; no import-time I/O. |
| `code/run_experiment.py` | Progress/output | PASS | `tqdm` on strata loop; helpers quiet. |
| `code/cost_conventions.py` | Correctness | PASS | `entry_mask` (pos≠0 ∧ pos≠prev) + per-entry charge; matches frozen `strategy_return_bps` shape. |
| `src/xen/referee_adaptive.py` | Seam faithfulness | PASS | `gate_stack_core_costfn` mirrors frozen core; equivalence verified (below). |
| `src/xen/referee_calibration.py` | Frozen integrity | PASS | `git diff` empty — **byte-unmodified**. |

---

## Numerical Validation

### Spot checks — independent ΔMDE re-derivation (raw data → DETECTED_FLOOR)

Re-derived from scratch (separate script, same E0 primitives), 3 strata across the cost range:

| Stratum | cost | L | n | MDE_perheld | MDE_amort | **ΔMDE** | CSV ΔMDE | Match |
|---|---|---|---|---|---|---|---|---|
| EURUSD/1h | 1.0 | 8 | 21,537 | 2.0 | 1.0 | **1.0** | 1.0 | ✓ |
| USTEC/1h | 4.0 | 8 | 20,791 | 4.0 | 0.5 | **3.5** | 3.5 | ✓ |
| BTCUSD/4h | 10.0 | 4 | 6,247 | 12.0 | 0.5 | **11.5** | 11.5 | ✓ |

MDE = first `EDGE_GRID_BPS` level with detection rate ≥ 0.5 (DETECTED_FLOOR). Computed correctly.

### Masking check (the binding integrity check for this experiment)

Both conventions are fed the **identical planted return array per draw** (`planted` constructed
once, passed to both `gate_passes` calls; only `strategy_fn` differs):

```
planted-array-shared = True   (single array → both arms)
net-series-differ-by-costfn-only = True   (perheld vs turnover net series differ, same input)
```

⇒ ΔMDE is a **clean accounting contrast** — same physical signal, same seeds, same split, same
bootstrap; the only moving part is the in-gate cost convention on the signal leg. Not a
plant/seed asymmetry. **L-03 masking: not masking** — every stratum reported per-cell; ΔMDE>0 is
near-universal (28/32 strata; 4 ties at low cost / 4h where the grid is too coarse to separate).

---

## Verdict Forensics

### Per-stratum re-derivation & masking

| Stratum group | Per-stratum picture | Agrees w/ pooled? | Notes |
|---|---|---|---|
| 1h, cost ≥ 2.5 (L8) | ΔMDE 1.5–3.5 | YES | per-held over-charges ~L× → loses 2–7 grid steps |
| 1h, cost ≤ 1.5 (L8) | ΔMDE 1.0 | YES | small but present |
| 4h (L4) | ΔMDE 0–11.5 | YES | larger absolute at high cost (BTCUSD 11.5); ties at low cost (coarse grid ≥4 bps) |
| perheld no-edge passrate | 0.000 all 32 | YES | per-held null clean everywhere |

- Pooled headline (median ΔMDE 1.50, max 11.50): **disclosure-only**, not masking — the
  per-stratum sign is homogeneous (ΔMDE ≥ 0 everywhere; `mde_monotone_ok = true` all 32).

### Mechanism (why ΔMDE > 0, and why the 12 fires)

**ΔMDE > 0:** the frozen per-held-bar convention charges `cost_bps` on **every** active bar; for a
persistent signal of episode length L it pays ≈ `L × cost` the round-trip it actually incurs.
Amortized charges once per entry (≈ `cost`/episode). For the same gross drift, amortized nets
more → detects at a lower planted floor → MDE_amort < MDE_perheld. Magnitude scales with `cost`
(BTCUSD 10 bps largest) and with L (1h L8 vs 4h L4) — the predicted F3 over-charge signature.
This is direct evidence for L-12 Mode-1 being **partly accounting**, not solely gate shape.

**The 12 `no-real-edge` fires (amortized only):** verified quantitatively, **not** a leak.
`plant_positive_edge` adds gross drift `(net_edge_bps + cost_bps)·states`; at `net_edge_bps=0`
the `+cost_bps` gross drift is calibrated to cancel the **per-held-bar** charge (→ true zero net
for per-held; observed pass = 0.000 on all 32). But amortized charges only ≈ `cost/L`, so at
edge=0 the amortized **net edge ≈ cost·(1 − entries/active) ≈ cost·(1 − 1/L) > 0** — a genuine
positive edge the gate correctly passes. Independent prediction vs observation:

| dom | cost | L | entries/active | amort net@0 | materiality | predict | observed passrate |
|---|---|---|---|---|---|---|---|
| 1h | 1.0 | 8 | 0.061 | 0.94 | 1.5 | reject | 0.00 ✓ |
| 1h | 2.0 | 8 | 0.061 | 1.88 | 1.5 | pass | 0.42–0.79 (borderline) ✓ |
| 1h | 3.0 | 8 | 0.061 | 2.82 | 1.5 | pass | 1.00 ✓ |
| 1h | 10.0 | 8 | 0.062 | 9.38 | 1.5 | pass | 1.00 ✓ |
| 4h | 4.0 | 4 | 0.123 | 3.51 | 3.0 | pass | 0.04–0.08 (low n→low power) |
| 4h | 10.0 | 4 | 0.124 | 8.76 | 3.0 | pass | 0.42 |

Direction, threshold (`net0 > materiality`), and the borderline/partial cells (cost≈2.0 1h;
all 4h, where n≈4–6k starves bootstrap power) all match. **The guard's premise — "edge=0 ⇒ zero
net for both conventions" — is false for amortized.** The guard fired on correct gate behaviour.

**A correctly-specified shared null holds for both arms** (real returns, persistent positions,
**no planted drift**): pass rate **0.000 / 0.000** (perheld/amortized) on EURUSD, BTCUSD, XAUUSD
1h and BTCUSD 4h. So the experiment *has* a valid no-real-edge control; the shipped guard simply
used `plant(edge=0)` (not a true zero for amortized) instead of the no-plant null.

### Gate-shape check

- Binding gate: the frozen 5-leg stack via the seam; effect shape: **location** (planted constant
  drift) → the gate is the right instrument. No tail/bimodal blindness here. The E2 non-constant
  battery (per design) will test shape sensitivity; out of scope for E1.
- Units note (→ interpreter, Warning 1): the `EDGE_GRID` is in **per-held-net-edge** bps (the plant
  is calibrated so `net_edge_bps` = per-held net). MDE_amort is therefore the **grid level** at
  which amortized detects, i.e. ΔMDE = reduction in the per-held-net detection floor for the same
  gross signal. Correct and interpretable, but must be stated in those units — not as "amortized
  net-edge MDE."

---

## Causal Provenance & Leak

### Provenance trace (verdict-bearing inputs)

| Column | Inputs & timestamps | Uses only ≤ t (≤ t-1 next-bar)? | Lines |
|---|---|---|---|
| real returns | `log(Open[t+1]/Open[t])` open-to-open | YES — executable next-step from acting at t's open | `referee_adaptive.py:106-112` |
| positions (persistent / alt / reblock-random) | **synthetic, exogenous** — seeded RNG blocks; no price input | YES (trivially — no return data flows in) | `run_experiment.py:persistent_positions/alternating/reblocked_random` |
| planted edge | `returns + states·(e+cost)/1e4` — synthetic oracle stimulus | N/A (test stimulus, not a tradable signal) | `referee_calibration.plant_positive_edge:499` |
| net strategy (signal leg) | `strategy_fn(planted, positions, cost)` | YES | `referee_adaptive.gate_stack_core_costfn` |

- `rct[di]`-style own-close-as-intrabar-limit: **none** — no intrabar limits; open-to-open only.
- Returns measured **open-to-open** (not open-to-close): **YES** (`Open[t+1]/Open[t]`). No
  open-to-close anywhere.
- Decision-on-forming-bar: **N/A** — positions are exogenous synthetic states, independent of the
  return series; no OHLC of the action bar is read to choose a position.

### Leak tripwires

Four shipped; status after this audit:

| Tripwire | Result | Note |
|---|---|---|
| Seam equivalence (wrapper == frozen core @ `strategy_return_bps`) | **HELD** | bit-identical incl. bootstrap-mean arrays on all 4 anchors (verified independently). |
| Strictly-alternating coincide @ L=1 | **HELD** | every active bar an entry → identical net series; naive leg convention-invariant by construction. |
| Cost monotonicity (entries ≤ active; amort MDE ≤ perheld MDE) | **HELD** | `mde_monotone_ok = true` all 32. |
| No-real-edge guard | **FIRED 12× — MIS-SPECIFIED** | see Critical 1. A correct no-plant null HOLDS (0.000 both arms). Not a data/gate leak. |

The valid nulls (permuted-returns+persistent; reblock-random) gave **FPR = 0.000** (Wilson
half-width 0.0094, 200 draws/stratum) for both conventions on all 32 strata — null control sound.

### Shared-module provenance contracts

- `referee_adaptive.gate_stack_core_costfn` — documented seam scope ("signal leg only; naive leg
  frozen per-held; reduces to frozen at `strategy_return_bps`") **matches the code**: naive computed
  with `strategy_return_bps` unconditionally; equivalence verified.
- `referee_adaptive.next_open_to_open_returns_from_bars` — docstring contract (open-to-open, does
  not itself enforce ≤t-1 position conditioning) matches; conditioning is satisfied externally by
  the exogenous synthetic positions.
- `referee_calibration.py` — **byte-unmodified** (`git diff` empty). Frozen-suite charter honoured.

### Price-primary check

Not price-primary (no edge generated from price). Correctly **not** run in cTrader. No
`data/strategy_runs/` expected or produced. Booked-vs-real: N/A (no port/feed; cost charged as the
E0 frozen round-trip on the signal leg). ✓

---

## Scope Compliance

- Analysis plan followed: **YES**, with one operator-approved design refinement (the gate seam:
  "frozen `gate_stack_core` unchanged" → "frozen sub-primitives reused via an additive adaptive
  wrapper; convention on the signal leg only"). Approved before coding; documented in the wrapper.
- Complexity budget: stat work = FPR+MDE per (16×2×2 conv) ✓; **plots 3/3** ✓; **new modules 1**
  (the turnover helper; the wrapper added to existing `referee_adaptive`, not a new module) ✓.
- Holdout exclusion verified: **YES** (first-70% minute slice + domain fence; global 30% never
  collected). DE30 skipped (no 5-year-era file) — expected, logged.

---

## Issues

### Critical

1. **`no-real-edge` guard is mis-specified — uses `plant(edge=0)`, not a true shared zero-net.**
   - File: `python/experiments/EXP-001/code/run_experiment.py` — guard in `main()` (the
     `no_edge_passrate_*` check, `curve[0.0]` in `mde_bps`) and `tripwire` framing.
   - Description: `plant_positive_edge(net_edge_bps=0)` injects gross drift `= cost_bps` calibrated
     to cancel the **per-held-bar** charge only. For the amortized arm this is a genuine
     `≈ cost·(1−1/L)` edge → the gate passes correctly, firing the guard 12×. The guard tests the
     wrong null for the amortized convention.
   - Impact: a **false** leak-tripwire failure on correct behaviour. Does **not** touch the ΔMDE
     computation (planted-edge sweep is independent of this guard) — but governance requires every
     shipped control to be valid, and the run currently ships 12 firing tripwires.
   - Fix: redefine the no-real-edge guard to the **no-plant null** (real returns + persistent
     positions, **no** `plant_positive_edge`) — proven to hold at 0.000 for both arms. (Equivalent:
     plant a convention-specific true zero, gross = the arm's own per-bar cost.) Re-execute Stage 3
     so the corrected guard passes.
   - **Materiality (stated explicitly, per discipline):** Critical because a firing leak-tripwire
     is governance-blocking and the shipped control set must be valid. **It cannot move the ΔMDE
     verdict** — the guard is downstream of and independent from the planted-edge MDE sweep; the
     valid FPR nulls already hold (FPR=0) and the corrected no-plant null holds (0.000 both arms),
     both independently reproduced. The rerun is to ship a clean, valid tripwire pass, not to
     correct a number. Do **not** down-classify to Warning.

### Warning

1. **ΔMDE units must be framed as "reduction in the per-held-net detection floor."**
   - The `EDGE_GRID` is calibrated in per-held-net-edge bps. MDE_amort is the grid level at which
     amortized detects the **same gross signal**, not an amortized-net MDE. The interpreter must
     state ΔMDE in those units or it will be over-read. Cannot move the number; framing only.

2. **4h strata are low-power (n ≈ 4–6k) — some amortized partial passes / ties reflect power, not
   absence of effect.** Report 4h cells with their effective-n; do not read a 4h tie as
   "accounting immaterial" (it is grid-coarseness + low n). Materiality: framing/disclosure only.

### Info

1. Planted-edge as oracle stimulus (states-aligned drift) is standard synthetic-positive power
   analysis (EXP-019 / L-12 style), not a tradable-signal look-ahead. Legitimate.
2. `N_PLANT=24`, `N_NULL=100`, `N_BOOTSTRAP=500` — adequate for the sign of ΔMDE; if the corrected
   rerun shows borderline 4h cells, raising `N_PLANT`/`N_BOOTSTRAP` tightens the floor (design's
   inconclusive-handling).

---

## Materiality & Re-Audit Requirements

- **Blocking finding:** Critical 1 (mis-specified guard) → **fix + re-execute Stage 3**. Verify:
  (a) corrected no-plant guard passes for all 32 strata (expect ~0 both arms); (b) `per_stratum.csv`
  ΔMDE column **unchanged** vs the current run (the proof the guard was orthogonal to the verdict).
- **Non-blocking (Warnings 1–2):** framing for the interpreter; explicitly cannot move any
  verdict-bearing number.
- **ΔMDE verdict status:** independently reproduced, masking-clean, causally sound, frozen-suite
  intact, valid nulls held. Sound **pending** the cosmetic-but-governance-required guard fix.

---

## Re-Audit Closure (post-fix re-execution)

Critical 1 fixed: no-real-edge guard redefined to the **no-plant null** (`no_plant_passrate`,
`run_experiment.py`); `plant(edge=0)` retained as the `plant0_passrate_*` disclosure field. Stage 3
re-executed (32 strata).

- **All leak tripwires HELD** (equivalence, alternating, monotonicity, no-edge). `no_edge_passrate`
  max = **0.000** both arms.
- **ΔMDE / MDE_perheld / MDE_amortized columns bit-identical** to the pre-fix run (verified by join
  on instrument×domain) — empirical proof the guard was orthogonal to the verdict, as argued.
- `plant0_passrate_amortized` max = 1.0 retained as the mechanism disclosure (per-held-calibrated
  plant ≠ amortized zero).

**Audit verdict → PASS.** No remaining blocking findings. Warnings 1–2 (units framing, 4h power)
carried to the documenter/interpreter.
