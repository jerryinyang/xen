# Audit Report: Experiment EXP-004 — E4 Robustness Pass (referee renew, D-referee)

## Summary

- **Verdict**: PASS
- **Critical Issues**: 0
- **Warnings**: 1 (A1.3 verdict-rule single-draw brittleness — recorded E5 precondition; NOT
  verdict-material to E4's range-bounded conclusion)
- **Info Notes**: 2

E4 ran autonomously, analysis-only, 0 TEST reads, global holdout sealed. Every key claim was
independently re-derived from `results/robustness_per_config_stratum.csv` and the frozen modules were
confirmed byte-unchanged (`git status --porcelain` clean on `referee_adaptive.py` +
`referee_calibration.py`). The binding conclusion — **freeze licensed at q\*=0.75 (safe range
{0.7,0.75})** — survives forensics and the causal-provenance/leak pass.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Thin orchestration mirrors EXP-003 with `(q, n_bootstrap, seed_off, null_mode)` threaded explicitly; anchor reproduces EXP-003 bit-exactly (0/32). |
| `code/run_experiment.py` | Knob injection / candidate-blindness | PASS | `q` passed to `gate_stack_adaptive`; coupled `ra.Q_STUD_MIN = NormalDist().inv_cdf(cfg.q)` set per-config in `run_job` (worker) — derived from `q` alone, reads no data/FPR/outcome/mask (Q5). `materiality_bps`, L1+coverage, cost map untouched. |
| `code/run_experiment.py` | Frozen-module integrity | PASS | `referee_adaptive.py` / `referee_calibration.py` byte-unchanged (git clean). Only a runtime attribute (`ra.Q_STUD_MIN`) is set in-process; no file edit. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_analysis_minutes` slices first-70% after `sort("CloseTime")`; D-regime recent slice is the last third *within* the analysis set; global holdout never collected. |
| `code/run_experiment.py` | Look-ahead / open-to-open | PASS | returns via `next_open_to_open_returns_from_bars` (open-to-open `≤t-1`); dogfood Donchian/MA `lag_open_to_open`-ed (+1 bar). No forming-bar read. |
| `code/run_experiment.py` | NaN / edge cases | PASS | `finite_values` guards; `math.isfinite` on ΔMDE; UNPOWERED=inf reported never failed; `len(returns)<200` skip; skew guards `sd==0`. |
| `code/run_experiment.py` | Determinism | PASS | explicit per-draw seeds + `seed_off`; ProcessPool strata independent; anchor reproduces. |
| `code/run_experiment.py` | Per-stratum verdict | PASS | `classify_stratum` per (config,stratum); pooled counts disclosure-only (summarise()). |
| `code/run_experiment.py` | Progress / org / imports | PASS | `tqdm` on config×instrument; sectioned; dirs created in `main()`; no import side effects. |
| `code/run_experiment.py` | Safe optimization | PASS | early-stop denominator stays `N_PLANT` (MDE decision bit-identical, mirrors EXP-003); frozen-arm q-invariance verified (not exploited as a shortcut — recomputed each config). |

## Numerical Validation

### Spot Checks (independent re-derivation from results CSV)

- **Regression anchor.** `(q=0.75, nb=500, off=0, standard)` joined to `EXP-003/results/
  det_dominance_per_stratum.csv` on (instrument,domain): **0/32 verdict mismatches, 0/32 STATE ΔMDE
  mismatches (<1e-9), 0/32 adaptive-FPR mismatches**. The sweep harness reproduces EXP-003 (A1)
  exactly → the swept-knob plumbing is correct and the sweep is interpretable.
- **FPR_BROKEN mechanism.** All **6** FPR_BROKEN rows have `dogfood_passes_adaptive == 1` and
  `dogfood_draws_adaptive == 162` (verified `.all()`), adaptive FPR `= 1/162 = 0.00617`, frozen `=
  0.0`. `wilson_lower(1,162) = 0.00109 > 0` ⇒ the A1.3 rule (`wilson_lower(adaptive) > frozen≡0`)
  resolves them as FPR_BROKEN. `wilson_lower(2,162) = 0.00339`. These are **single-draw passes**.
- **Frozen-arm q-invariance.** `mde_frozen_state` has `n_unique == 1` per stratum across the R1
  q-sweep (max distinct = 1) → `q` perturbs **only** the adaptive arm, as designed (the frozen/
  frozen_amortized DET references are q-independent). Confirms the sweep isolates the knob.

### Range / Statistical Sanity

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| adaptive dogfood FPR (all 288 rows) | ≤ control 2α=0.10 | max **0.00617** (=1/162) | YES |
| future-destroy max (adaptive, all configs) | ≈ FPR, ≤ guard | **0.050** ≤ 0.10 | YES |
| baseline q=0.75 per-shape regressions (adaptive>frozen) | 0 | 0 on dense/tail/sparse/state | YES |
| R3 skew adaptive FPR | ≈ 0 (skew must not lift FPR) | **0.0** (0/32 passes) | YES |
| R3 skew **frozen** FPR (null well-formedness) | ≈ 0 (else null carries structure) | **0.0** | YES |
| 4h sub-pop episode counts (D-CIwidth) | ≥ MIN_EPISODES_SUBPOP=5, non-degenerate | 144–231 | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| q-sweep | `Q_STUD_MIN=Φ⁻¹(q)` candidate-blind at every point | YES | derived from `q` alone in `run_job`; 0.6/0.75/0.8 → 0.253/0.674/0.842; no data read |
| R3 skew null | a genuine *no-edge* null (marginal skew only) | YES | frozen + frozen_amortized FPR = 0.0 on it → no return/position alignment introduced; transform is elementwise (provenance below) |
| sub-pop bootstrap CI (L-06) | CI width tracks `effective_n`/dispersion, not degenerate | YES | 4h half-widths 0.83–8.87 bps scale with vol (BTCUSD widest), all strata ≥144 episodes |

## Results Plausibility

The full picture is internally consistent: baseline 32/32 DET with adaptive FPR 0.0; q*=0.7 also
32/32; the extremes q*=0.6 and q*=0.8 each pick up exactly one single-draw (1/162) dogfood pass;
R2 off=+100000 corners and the D-regime recent-third each pick up two — **all** of which are the same
1/162 single-pass artifact, never a future-destroy survivor (max 0.05). R3 skew is uniformly clean.
Nothing implausible.

## Verdict Forensics

### Per-stratum re-derivation & masking check

Binding endpoint is per (config, stratum) (L-03); E4 reports per-stratum, no pooled verdict. Re-derived:

| Config (probe) | DET_DOMINANT | FPR_BROKEN | Which stratum flipped | Mechanism |
|---|---|---|---|---|
| R1 q*=0.6 | 31/32 | 1 | JP225/4h | 1/162 dogfood pass |
| R1 q*=0.7 | **32/32** | 0 | — | clean |
| **R1 q*=0.75 (anchor)** | **32/32** | 0 | — | clean (= EXP-003) |
| R1 q*=0.8 | 31/32 | 1 | NZDUSD/4h | 1/162 dogfood pass |
| R2 nb500 off+100000 | 31/32 | 1 | JP225/4h | 1/162 dogfood pass |
| R2 nb1000 off0 | 32/32 | 0 | — | clean |
| R2 nb1000 off+100000 | 31/32 | 1 | USDCAD/4h | 1/162 dogfood pass |
| R3 skew | **32/32** | 0 | — | clean |
| D-regime recent⅓ | 30/32 | 2 | BTCUSD/4h, GBPUSD/4h | 1/162 dogfood pass (noisier regime, fewer bars) |

**Masking check:** no pooled headline is used as the verdict — the binding read is the per-stratum
stability table above. The headline "freeze licensed" is **not** masking a flipped stratum: the
binding operating point (q*=0.75, standard nulls) is 32/32 with zero passes; every flip elsewhere is
a single 1/162 pass on a *different, non-anchor* sweep point and is individually disclosed. All flips
are 4h (the lowest-episode/highest-cost domain), consistent with single-draw noise, not a systematic
instrument or domain veto.

### Mechanism

E4's conclusion is driven by three concrete facts: (a) the **adaptive arm's true dogfood FPR never
exceeds 1/162 ≈ 0.62%** anywhere — two orders below the 2α=0.10 control bound — so the gate's FPR
control is intact across the whole sweep; (b) **STATE recovery is preserved** across the safe range
(median ΔMDE 7.5–8.0 bps, min 4.0, zero per-shape regressions at baseline); (c) the only "breaks" are
a **labeling consequence** of the A1.3 rule comparing a single noise pass against a *zero* frozen
baseline (`wilson_lower(1,162)=0.0011>0`), not an FPR leak. R3 isolates the A1.2 concern: a strongly
right-skewed null (sample skew ≈ 3.6, mean ≈ 0) produces **0/32** adaptive passes — the studentized
floor `Q_STUD_MIN=Φ⁻¹(q*)` holds against marginal skew because skew lifts the *raw* q\*-quantile but
not the *studentized* one (the null shape still lands at ≈Φ⁻¹(q\*)). So the residual-skew-FPR worry
is **refuted**, and no `Q_STUD_MIN` bump is warranted.

### Gate-shape check

Binding gate = the E3a adaptive composite (validity→economics, studentized∧bps sub-pop L5). E4 does
not test a new effect shape — it perturbs the gate's own knobs and the null shape. The gate sees all
four substrate shapes at baseline (0 regressions). The one shape-relevant stress (R3 right-skew null)
is correctly *not* mistaken for an edge (0/32). No gate-shape blindness; the gate is the right
instrument for what E4 measures.

## Causal Provenance & Leak (independent of numeric reproduction)

### Provenance trace (verdict-bearing columns)

| Column | Inputs & timestamps | Uses only ≤t (≤t-1 next-bar)? | Lines |
|---|---|---|---|
| swept `q` → adaptive verdict | module constant `cfg.q`; no data input | YES (constant) | `run_job`, `gate_passes(... q=q)` |
| `Q_STUD_MIN` floor | `NormalDist().inv_cdf(cfg.q)` — `q` alone | YES (candidate-blind; reads no data/FPR/outcome/mask) | `run_job` |
| returns | open-to-open `≤t-1` log returns | YES | `build_domain` → `next_open_to_open_returns_from_bars` |
| dogfood Donchian/MA positions | real OHLC, then **lagged +1 bar** | YES (`≤t-1`) | `dogfood_fpr` → `lag_open_to_open` |
| `skew_returns` (R3 null) | elementwise transform of the input series only | YES (marginal; no future bar, no positions, no outcome) | `skew_returns` |
| adaptive/frozen gate legs | frozen sub-primitives (split/bootstrap/CI/episodes) | YES (inherited from EXP-003/frozen suite, already provenance-audited) | imported, byte-frozen |

- `rct[di]`-style own-close-as-intrabar-limit pattern? **NO** (no intrabar limits in this analysis-only
  substrate experiment).
- Decisions at the action bar's open on confirmed bars `≤t-1`, no forming-bar OHLC read? **YES**.
- Returns open-to-open (not open-to-close)? **YES**.

### Leak tripwire

- Future-destroying control shipped (`future_destroyed_passrate`: plant edge → block-permute returns
  → re-run adaptive) at **every** sweep point: **YES**.
- Edge collapsed under it? **YES** — `future_destroy_max_adaptive = 0.050` overall (≤ guard 0.10);
  no tripwire failure logged on any of the 288 (config,stratum) rows ("All leak tripwires held across
  every sweep point"). A studentized quantile *can* mine noise; it did **not** here. No surviving
  future-destroyed edge ⇒ no leak.
- No-plant guard + Wilson-resolved dogfood-FPR control: held on all rows.

### Shared-module provenance contracts

`gate_stack_adaptive` / `adaptive_row` / `subpop_quantile_materiality` are the EXP-003 module,
**byte-unchanged** (git clean). The only runtime mutation is `ra.Q_STUD_MIN` (a derived constant);
its sole consumer is `adaptive_row`'s studentized comparison, and it is set coherently with the `q`
passed to `gate_stack_adaptive`. `skew_returns` documents its causal contract (reads input series
only). Contracts match.

### Price-primary check

**Analysis-only** — synthetic exogenous positions + planted oracle edges + frozen primitives + the
adaptive economic legs; **no price→signal generation**. Not price-primary; no `data/strategy_runs/`
expected. No booked-vs-real feed involved. Correct classification.

## Scope Compliance

- Analysis plan followed: **YES** (R1 q-sweep {0.6,0.7,0.75,0.8}; R2 bootstrap/seed 2×2; R3 skew;
  D-CIwidth + D-regime disclosures; regression anchor; all leak tripwires retained per sweep point).
- Deviations: **none**. (R3 skews all null-returns families incl. the dogfood draws while holding
  signals on real OHLC — within the design's "skew is a stress on the null *shape*" intent; the
  standard mode mirrors EXP-003's full 3-family dogfood exactly, which the 0/32 anchor confirms.)
- Complexity budget: **3 stat probes** (R1/R2/R3) / 2–4; **3 plots** (`qsweep_surface`,
  `bootstrap_seed_stability`, `skew_fpr`) / 3–5; **0 new src modules** (1 self-contained driver,
  reuses all frozen primitives) / 0–1. Within comparative budget.
- Holdout exclusion verified: **YES**.
- Not tuned on CF-MR-002 (absent). Referee FROZEN (not frozen *here*; E5 freezes).

## Issues

### Critical
None.

### Warning

1. **A1.3 verdict-rule retains single-draw brittleness vs a zero frozen baseline.**
   - File: `code/run_experiment.py`, `classify_stratum` (FPR clause) — faithful to design A1.3.
   - Description: with `frozen ≡ 0`, the rule `wilson_lower(passes_adaptive, draws) > 0` flips to
     FPR_BROKEN on a **single** 1/162 dogfood pass (`wilson_lower(1,162)=0.0011>0`). All 6 FPR_BROKEN
     across the sweep are this artifact; the gate's *actual* FPR (≤0.62%) is far below the 2α=0.10
     control bound and future-destroy collapses.
   - Materiality (why NOT Critical / no rerun): it does **not** move E4's binding conclusion. The
     binding operating point (q*=0.75, standard nulls) is 32/32 DET with zero passes (= EXP-003,
     anchor 0/32); E4's predeclared outcome is explicitly **RANGE-BOUNDED** (design §"KNOB-SENSITIVE
     / RANGE-BOUNDED"), and the safe range {0.7, 0.75} is read directly off the per-stratum table.
     The finding is a faithful surfacing of a **rule** weakness (not an E4 implementation bug, not a
     gate FPR leak), and its remedy is a predeclared **E5 freeze precondition** — adopt a
     min-pass-count (≥2) or control-relative FPR-comparison in the freeze adjudication rule — which
     the design (A1.2/A1.5) explicitly defers to E5 and forbids applying in E4 (tuning-on-test).
   - Fix (E5, not E4): in the freeze adjudication, require the adaptive dogfood-FPR to be
     Wilson-resolved above frozen **and** `passes_adaptive ≥ 2` (or compare against the 2α budget,
     not 0), then freeze at q*=0.75.

### Info

1. **Matplotlib glyph warning** — `Φ⁻¹` superscript-minus (U+207B / glyph 8315) missing from Arial
   in `qsweep_surface.png` axis label. Cosmetic; plots render correctly. Non-material.
2. **R2/D-regime breaks share the single-pass mechanism.** The 2 R2 (off=+100000) and 2 D-regime
   flips are the same 1/162 artifact (Warning 1), on 4h strata; expected under seed reshuffling /
   the shorter recent-third sample. Disclosure-only; does not affect the baseline verdict.

## Materiality & Re-Audit Requirements

- **No Critical findings → no fix + rerun required.** The single Warning is shown not to move any
  verdict-bearing number for E4 (baseline 32/32 clean; gate FPR ≪ control; future-destroy collapses;
  R3 skew clean), and its remedy is correctly an E5 precondition, not an E4 change.
- **Re-audit:** none required. The regression anchor (0/32) is the standing proof the harness is
  correctly wired; the causal-provenance/leak pass is clean (future-destroy max 0.05, frozen modules
  byte-unchanged, candidate-blind `Q_STUD_MIN`).

**AUDIT VERDICT: PASS (0 Critical).** E4 is a correct, leak-clean, per-stratum robustness
characterisation. Freeze is **licensed at q\*=0.75** (safe range {0.7,0.75}); residual skew-FPR is
**refuted** (R3 0/32); the only caveat is a recorded **E5 verdict-rule precondition** (single-draw
FPR-label brittleness), not a gate defect.
