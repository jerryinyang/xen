# Audit Report: Experiment EXP-007 (E6 — P*-capable Referee Variant)

## Summary

- **Verdict**: **PASS** — ADOPT (freeze) is justified; **0 blockers**.
- **Critical Issues**: 0
- **Warnings**: 1 (N2 single-draw Wilson artifacts — non-material under the E4 rule)
- **Info Notes**: 3 (Arm-P returns-space caveat; matplotlib deprecation; bracket path-ordering simplification)

Classification: **analysis-only** (synthetic substrates + frozen primitives; no price→signal). 0 reads /
0 slots; global holdout sealed. The experiment adds an adjudication path (`referee_pstar.gate_stack_
pstar`) so the §10.3a renewed referee can score an engine-realized per-bar net series (the CF-MR-002
intrabar `P*` fill, EXP-006) without editing the hash-frozen modules.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `referee_pstar.py` | Additive-only | PASS | Imports + reuses frozen sub-primitives; no new threshold/knob/constant. Frozen modules byte-unchanged (hashes below). |
| `referee_pstar.py` | Correctness (mirror) | PASS | `inspect`-diff vs `gate_stack_adaptive`: exactly one computational change (`strategy = realized_bps`) + a defensive length check; every sub-primitive call + the naive leg + the return dict identical. |
| `referee_pstar.py` | Type hints / docstrings | PASS | Public fns typed; provenance contract in `make_realized_fill` docstring. |
| `referee_pstar.py` | NaN handling | PASS | `_cores_equal` NaN-aware; `make_realized_fill` clip/where explicit; empty-episode → ABSTAIN upstream. |
| `run_experiment.py` | Plan compliance | PASS | Three arms R/N/P per stratum as designed; reuses EXP-002 substrate verbatim. |
| `run_experiment.py` | Holdout exclusion | PASS | `load_analysis_minutes` lazy scan → sort `CloseTime` → `slice(0, 0.70·n)` → collect; holdout never materialized. `ERA_GLOB="20210602_*"` = the §10.3a 32-strata grid. |
| `run_experiment.py` | Per-stratum binding | PASS | Verdict emitted per instrument×domain; no collapsed cross-cell PASS/FAIL (L-03). |
| `run_experiment.py` | Determinism | PASS | All draws seeded (fixed offsets per arm). Full run reproduces the smoke verdicts. |
| `run_experiment.py` | Progress / output | PASS | `tqdm` over strata; concise logger summary + blocking tripwire report. |
| `run_experiment.py` | Org / import side-effects | PASS | dirs created in `main()`; constants/helpers/orchestration sectioned. |

## Numerical Validation

### Spot checks (independent re-derivation)
- **`_cores_equal` genuineness (adversarial):** identical copy → `True`; perturb a scalar (`effective_n
  +1e-9`) → `False`; perturb one array element (`neutral_means[0]+1e-6`) → `False`; both-NaN → `True`.
  The deep NaN-aware equality is real, not trivially passing.
- **Reduction identity (Arm R):** independently confirmed bit-identical core dicts and identical
  `adaptive_row` verdicts on fresh random draws (1h+4h) and across all 32 strata in the run
  (`R_core_identical=R_verdict_identical=32/32`).
- **N1 symmetric null (independent):** matched fav=adv=15 bps bracket on block-permuted no-edge returns →
  held-bar mean **−0.215 bps** (= amortized cost only), verdict **REJECT**. Confirms the symmetric
  construction injects no phantom edge.
- **Provenance non-look-ahead:** `make_realized_fill(returns)` output `[:1000]` is **byte-unchanged** when
  every bar after index 1000 is replaced — output `[t]` reads only `returns[t]` (the held bar's own
  realized outcome) and `positions[t-1..t]`. No future bar informs any value.

### Range / sanity checks

| Metric | Expected | Observed | Pass |
|--------|----------|----------|------|
| Arm-R core/verdict identical | 32/32 | 32/32 | YES |
| Frozen module hashes (pre==post) | unchanged | `referee_adaptive b4fd6cb1…ae847` (== E5 freeze), `referee_calibration 04f933f6…7994` | YES |
| N1 symmetric FPR | 0 (no phantom) | 0/32 all 0.000 | YES |
| N3 dogfood FPR | ≤ §10.3a (0/32) | 0/32 all 0.000 | YES |
| N2 future-destroy FPR | collapse to ~0 | max 0.013 (5 strata at 1/80), 27 strata 0.000 | YES (Warning 1) |
| Arm-P MDE | finite | 32/32 finite, 0.5–4.0 bps | YES |

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

Re-derived per instrument×domain (32 cells, `per_stratum.csv`). **No pooling** — the headline "ADOPT
32/32" is a per-stratum conjunction, not an averaged statistic. Every stratum independently shows:
`R_core_identical=true ∧ R_verdict_identical=true ∧ N1=0 ∧ N3=0 ∧ N2≤0.0125 ∧ finite P_mde`. No stratum
flips; nothing is masked (the pooled "32/32" equals the per-stratum minimum). The 5 N2=0.0125 strata
(GBPUSD-4h, JP225-4h, US500-4h, USDCAD-4h, XAUUSD-4h) are not outliers vetoing a domain — they are
single-draw artifacts (below), and their R/N1/N3/P all pass.

### Mechanism (why ADOPT)

The P*-capable gate is **§10.3a with the signal leg sourced from `realized_bps` instead of
`strategy_return_bps_turnover(returns, positions)`** — proven by the `inspect`-diff (one change) and the
bit-identical reduction (Arm R). Therefore:
- **R passes** because, when `realized := strategy_return_bps_turnover(...)`, the source-swap is a no-op
  → identical core → identical verdict. The new path inherits §10.3a's earned FPR control by construction
  for any position-state input.
- **N passes** because the new FPR surface (a realized series that ≠ position·return) does **not**
  manufacture a phantom edge: the binding N1 **symmetric** bracket on a martingale return stream truncates
  the favourable and adverse tails equally → expectancy ≈ 0 → the L1/L3/L5 legs (unchanged) reject. The
  L-01/L-02 leak class (favourable-only asymmetry) is precisely what N1 controls, and it does not pass.
- **P passes** because a genuinely positive realized series (planted directional drift through a wide
  bracket) clears the same legs → finite MDE.
The driver is the **structural equivalence** (R) plus the **symmetric-truncation no-phantom property**
(N1), not a tuned threshold.

### Gate-shape check

Binding gate = §10.3a (validity floor + L3 vs-naive + L5 pooled/studentized sub-pop), unchanged. The new
input *shape* is a realized-fill (bracket-truncated) return series. The gate sees it correctly: N1 shows
it is not blind in a way that admits a phantom; Arm P shows it retains power on a real realized edge. **No
shape mismatch.** Honest limitation (Info 1): in returns-space the bracket can only **cap**, so a realized
series never exceeds position-state magnitude — the *intrabar capture* that distinguishes a `P*` fill from
a close-to-close hold is not exercised here (it needs intrabar high/low; the real cTrader engine exercises
it in EXP-006). Arm P therefore validates **finite power on a realized series** (the binding success
criterion), **not** "capture beyond position-state." Design + code state this; **not overclaimed**.

## Causal Provenance & Leak (independent of numeric reproduction)

### Provenance trace (verdict-bearing columns)

| Column | Inputs & timestamps | Uses only ≤ t (≤ t-1 for next-bar)? | Lines |
|---|---|---|---|
| `realized_bps` (signal leg) | `make_realized_fill`: `pos[t-1..t]` (entry), `returns[t]` (held bar's own open-to-open outcome), rested bracket constants | YES — verified by the future-shuffle invariance test (output[:t] unchanged when future bars change) | `referee_pstar.py:make_realized_fill` |
| `returns` (market / naive leg) | `next_open_to_open_returns_from_bars`: `log(Open[t+1]/Open[t])` | YES — open-to-open `≤ t-1` (E0 basis) | `referee_adaptive.py:136` |
| positions (episodes / sub-pop) | synthetic (`persistent_positions`) or dogfood lagged `lag_open_to_open` (one-bar lag → acts at next open) | YES | `run_experiment.py:lag_open_to_open` |

- **`rct[di]`-style own-close intrabar limit?** **NO.** The bracket limits are rested constants
  (parameters), not a bar's own close; `make_realized_fill` never uses `returns[t]` as a *decision* input,
  only as the realized outcome of an already-open position. P-09 clean.
- **Decisions at the action bar's open on confirmed bars?** YES (dogfood positions one-bar lagged; synthetic
  positions are exogenous states).
- **Returns open-to-open?** YES (E0 basis); the bracket truncates the held bar's open-to-open move at the
  rested limit — a calibration construct, not an open-to-close fill.

### Leak tripwire

- **T1 (N1 symmetric-limit FPR):** shipped + **held** — 0/32 passes; a no-edge symmetric bracket does not
  pass (the binding new control).
- **T2 (N2 future-destroy):** shipped + **held** — a strong planted edge (`EDGE_GRID_BPS[-1]`) **collapses**
  from power≈1.0 to FPR max 0.0125 after block-permuting the market returns *before* realizing. The fix
  (destroy alignment at the **input** per L-07, not the realized P&L output) is correct and verified: an
  earlier version permuted the realized series (preserving its mean → FPR 1.000) and was caught + fixed.
- **T3 (byte-freeze + reduction identity):** shipped + **held** — `referee_adaptive.py`/
  `referee_calibration.py` SHA-256 unchanged pre/post run; reduction identity 32/32.

### Shared-module provenance contracts
`referee_pstar.make_realized_fill` matches its documented contract (limits rested `≤ t-1`; output reads
`returns[t]` + `positions[t-1..t]`; no future bar) — verified empirically. `gate_stack_pstar` documents
and honors "signal leg = injected realized; naive leg = frozen market-return reference."

### Price-primary check
N/A — analysis-only. `make_realized_fill` is explicitly a **calibration-substrate construct**, never used
to adjudicate a real price strategy (the cTrader engine's `ExitFillPrice` is, in EXP-006). No vectorized
price-strategy backtest. Holdout never loaded.

## Scope Compliance

- Analysis plan followed: **YES** (Arms R/N/P; per-stratum; DET-dominance adoption rule).
- Deviations: **none material.** Arm-P uses a wide-bracket planted-drift positive (returns-space) rather
  than an intrabar-capture positive — a forced consequence of the returns-only substrate, disclosed; the
  binding criterion (finite power) is met.
- Complexity budget: 1 new module + 1 harness (✓ ≤ budget); 3 plots emitted (≤ 4 budgeted); stat apparatus
  = gate per (32 strata × {R,N1,N2,N3,P}).
- Holdout exclusion verified: **YES.**

## Issues

### Critical
None.

### Warning
1. **N2 future-destroy single-draw FPR artifacts (5 strata at 1/80 = 0.0125).**
   - File: `results/per_stratum.csv` (GBPUSD-4h, JP225-4h, US500-4h, USDCAD-4h, XAUUSD-4h).
   - Description: after future-destroy, 1 of 80 null draws passes on these 4h strata; 27/32 strata are 0.
   - **Materiality: non-blocking.** These are exactly the E4-characterized `wilson_lower(1,N)>0`
     single-pass label artifacts. Under the E4-derived freeze-adjudication rule (`MIN_FPR_PASSES=2` /
     control-relative `2α`) adopted at E5, a single 1/80 pass is **not** an FPR-control failure (true FPR
     ≤ 0.0125 ≪ the 2α=0.10 control bound; Wilson-lower of 1/80 ≈ 0.002). The strong planted edge
     collapsed from power≈1.0 — the tripwire held. Does **not** move any verdict-bearing number; ADOPT
     stands. (If freezing demands a stricter showing, raise `N_NULL` to shrink the Wilson half-width;
     not required.)

### Info
1. **Arm-P returns-space caveat (honest limitation, not a defect).** The bracket caps, it cannot capture
   an intrabar excursion the close misses; Arm P validates finite power on a realized series, not
   capture-beyond-position-state (the latter needs intrabar high/low — exercised by the engine in
   EXP-006). Stated in design + code; not overclaimed.
2. **Bracket path-ordering simplification.** `make_realized_fill` brackets the *net* per-bar return (no
   intrabar High/Low ordering of which limit hit first). For FPR calibration (symmetric N1 → 0) this is
   conservative and unbiased; documented. The real engine uses actual High/Low touch (`ExitFillPrice`).
3. **matplotlib `boxplot(labels=...)` deprecation** in `plot_arm_p` — cosmetic; matches the EXP-002
   convention; no effect on results.

## Materiality & Re-Audit Requirements

- **No Critical findings → no rerun required.** The single Warning is shown not to move any verdict-bearing
  number (per-stratum R/N1/N3/P all pass; N2 artifacts are within the frozen freeze-adjudication rule).
- **ADOPT (freeze) is justified:** Arm-R reduction identity 32/32 + byte-freeze intact (proves the path is
  §10.3a + a pure source-swap), Arm-N realized-fill FPR ≤ §10.3a control (N1/N3 0/32; N2 single-draw
  artifacts), Arm-P finite power 32/32. Stage 5 may freeze + hash-pin `referee_pstar.gate_stack_pstar`
  (its own `freeze_manifest.json`) **before** any CF-MR-002 read, recording the prior suites' unchanged
  hashes. The freeze itself is the operator-gated sign-off.
