# Experiment: EXP-011 — Predeclared-Loss Operating-Point Synthesis & Recommendation

## Hypothesis

EXP-011 is **exploratory** (design §4: "no pass/fail, measurement only"). It does not test a falsifiable hypothesis; it produces a **recommendation** under a fully predeclared loss. The exploratory question is below.

## Question

Given a loss function predeclared in full **before any operating point is read**, which per-domain operating point on the frozen gate stack's L5 stringency lever (the EXP-006 threshold `τ`-frontier) does the loss select for each of 5m / 1h / 4h — and is that selection **robust** across three predeclared loss specifications? Record the loss-minimising recommended operating point per domain plus a predeclared **conditional adoption rule** for Phase 003.

This is the Phase 002 synthesis. Per **D-posture**, EXP-011 *recommends*; it does **not** adopt or freeze any referee. Adoption is the Phase 003 decision phase, run on **fresh** synthetic draws (D-freshdraw / meta-Goodhart guardrail).

## Predeclaration integrity (design §2 ⚠ gate — read first)

This scope is the **full instantiation** of the design `D-loss` family, which the operator confirmed on 2026-06-03 as *"per-domain cost-weighted penalty on false positives and missed material edges,"* before any Phase 002 measurement existed (recorded in `python/experiments/EXP-005/governance/pre-execution-review.md`, token `PHASE002-PREDECLARATION-CONFIRMED`).

Binding discipline for this scope, enforced at Stage 4:

1. **The loss form and all coefficients below are derived from economic first principles and the frozen design** (`D-loss` family + the `D-lenientL5` materiality caveat + the frozen `MATERIALITY_BPS` constants). They reference **no Phase 002 outcome** (no EXP-005/006/007/008 result value) as a *justification for any coefficient*.
2. **No term is removed or re-weighted to favor a particular `τ`.** In particular, the false-positive penalty term is retained in all three losses **even though** the operating substrate may render it inactive; its presence is mandated by the `D-loss` family, not by any observed FPR value.
3. The decision space (the EXP-006 `τ`-frontier) and the planted-edge grid are **predeclared, frozen Phase 001/002 objects**, not chosen here.
4. EXP-011 is computed on the **same shared draws** as the frozen reference. This is permitted because the loss is fully predeclared and EXP-011 produces only a *recommendation* (D-freshdraw). The Goodhart-sensitive **adoption** step is deferred to Phase 003 on **fresh draws**; the conditional adoption rule below is the predeclared hand-off.

Once EXP-011 results are read, the loss is frozen for the phase; any change requires a new dated amendment authored before the dependent results are read, referencing only predeclared reasoning.

## Predeclared structural relationship (erratum citation — design §2 erratum 2026-06-03)

Per the active checkpoint's **D-lenientL5 erratum** and EXP-007's "Predeclared Structural Relationship", the **lenient-L5 variant is the EXP-006 `τ=0` (zero-buffer) threshold endpoint**, not a structurally distinct mechanism: on the frozen harness, `L5_lenient = ci_lower_bps > 0` equals EXP-006's `L5_τ = ci_lower_bps > τ` at `mult=0`, and (because L3 already enforces `ci_lower_bps > 0`) equals dropping L5. EXP-007 confirmed this verdict-level across all shared draws (`improves_beyond_frontier = false`, `lenient_eq_tau0_mde = true`, all 9 rows).

**Consequence for EXP-011:** the operating-point decision space is the **single EXP-006 `τ`-frontier** `τ ∈ {0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00} × materiality_bps(domain)`. `τ=1.00` is the **frozen strict reference** (reproduces EXP-003 exactly); `τ=0.00` is the **lenient / zero-buffer endpoint**. There is **no separate "lenient mechanism" axis** — including one would double-count the erratum-confirmed equivalence. EXP-011 must describe the lenient option as the `τ=0` endpoint plus its EXP-007 sub-material accounting, never as a distinct sensitivity gain.

## Predeclared loss function (full — frozen before any operating point is read)

For each domain `d ∈ {5m, 1h, 4h}` the recommendation is selected over the frozen `τ`-frontier. All three losses use only these per-`τ` quantities, all already measured by frozen Phase 001/002 experiments:

- `MDE(d, τ)` — economic MDE in bps at `α₀ = 0.05` (EXP-006 `threshold_mde_summary.csv`).
- `FPR(d, τ)` — pooled gate-stack false-positive rate and its Wilson upper bound at `α₀` (EXP-006 `threshold_fpr_summary.csv`).
- `TPR(d, τ, e)` — true-positive rate at planted edge `e` (EXP-006 `threshold_tpr_summary.csv`).
- `sub(d, τ)` — economically sub-material pass rate at the operating MDE: fraction of positive-scenario passes at the operating edge whose **net point estimate `< materiality_bps(d)`**, using the EXP-007 definition. Available directly for `τ=0` (EXP-007 `submaterial_pass_rates.csv` / `lenient_vs_frontier.csv`); for `τ>0` it is reconstructed deterministically from the frozen EXP-003/EXP-006 draw-level effect estimates under the identical definition (bounded post-processing, no new market data).
- `materiality_bps(d)` — frozen per-domain materiality buffer: **5m = 0.5, 1h = 1.5, 4h = 3.0 bps** (`xen.referee_calibration.MATERIALITY_BPS`). The economically ideal MDE is `materiality_bps(d)` — detect every material edge, admit no sub-material pass.

**Economic rationale (first principles, common to all three losses).** A referee allocates scarce validation capacity. Two opposing costs: (1) **missed material edges** — if `MDE > materiality_bps`, edges in the band `(materiality_bps, MDE]` are real and material yet rejected (false negatives that matter); (2) **sub-material admissions** — buying a lower MDE by passing reliably-positive but economically-negligible edges (`< materiality_bps`) wastes validation capacity (the `D-lenientL5` caveat). A third cost, **false positives** (`FPR`), is always priced even where it does not bind on this null substrate.

### Loss A — lexicographic, FPR-constrained (PRIMARY; headline recommendation)

Per domain, over the `τ`-frontier:
1. **Hard constraint** — keep only `τ` whose `FPR` Wilson **upper** bound `≤ α₀ = 0.05`.
2. Among survivors, **minimize `MDE(d, τ)`**.
3. **Materiality tie-break** — among the min-MDE survivors, drop any with `sub(d, τ) > 0.50` (a lower MDE bought mostly by sub-material passes is not a real sensitivity gain, per `D-lenientL5`); among the remainder choose the **lowest `sub(d, τ)`**.
4. **Conservatism tie-break** — if still tied, choose the **largest `τ`** (most stringent operating point achieving the min MDE; defaults toward the frozen strict reference under indifference).

Loss A is the most parameter-free specification and matches the phase's FPR-as-hard-constraint framing; it is the **primary** loss. If step 3 eliminates *all* min-MDE survivors in a domain, the recommendation is the **lowest-MDE `τ` whose `sub ≤ 0.50`** (i.e. the materiality term overrides a raw MDE minimum), reported explicitly as a materiality-limited recommendation.

### Loss B — weighted scalar (robustness specification)

Per domain, minimize over `τ`:

```
L_B(d, τ) = w_blind · max(0, MDE(d,τ) − materiality_bps(d)) / materiality_bps(d)
          + w_fp    · ( FPR(d,τ) / α₀ )
          + w_sub   · sub(d, τ)
```

Each term is normalized to be O(1) at its "bad" end (blind band as a fraction of the materiality buffer; FPR as a fraction of the α-budget; sub-material as a rate in [0,1]). **Predeclared weights `w_blind = w_fp = w_sub = 1.0`** (a neutral first-principles prior: a full-buffer-width material blind band, an at-budget FPR, and an all-sub-material pass set are treated as equally bad). Weights are frozen here and **not** tuned to results.

### Loss C — Bayes risk over a predeclared material-edge prior (robustness specification)

Per domain, minimize over `τ`:

```
L_C(d, τ) = c_fp · FPR(d,τ)
          + c_fn · E_{e ~ G_d}[ 1 − TPR(d, τ, e) ]
```

with **predeclared coefficients `c_fp = c_fn = 1.0`** and **`G_d` a predeclared uniform prior over the material-edge band `[materiality_bps(d), 4 × materiality_bps(d)]`** — i.e. 5m [0.5, 2.0], 1h [1.5, 6.0], 4h [3.0, 12.0] bps, evaluated at the EXP-006 planted-edge grid points falling in that band. `G_d` places mass only on **material** edges, so detecting sub-material edges earns no credit (over-leniency is implicitly not rewarded). **`G_d` is a predeclared reference prior, deliberately not the EXP-009 empirical distribution**, because EXP-009's untuned-strategy effects sit almost entirely below the materiality buffer (an EXP-009-measured expectation would be degenerate/non-discriminating). EXP-009 is used as a **context reality-check** ("do observed real effects even reach the material band?"), not as the integration measure.

### Cross-loss consistency verdict (predeclared meta-rule)

Let `τ*_A, τ*_B, τ*_C` be the per-domain minimisers. Per domain:
- **ROBUST** if all three select the same `τ` **or** all three fall within **one grid step** of each other on the frozen `τ`-frontier. Headline recommendation = `τ*_A`; report it as robust.
- **LOSS-SENSITIVE** otherwise. Headline recommendation = `τ*_A`, reported explicitly as loss-sensitive, with the full `{τ*_A, τ*_B, τ*_C}` range and a one-line statement of which cost term drove the disagreement. The conditional adoption rule (below) must reflect the sensitivity.

The recommendation read is **mechanical** once these losses are fixed.

## Scope Boundaries

- **Data Views**: **result-level artifacts only** (CSV / JSON) from EXP-003, EXP-005, EXP-006, EXP-007, EXP-008, EXP-009, EXP-010. **No market data is loaded; no chart-type views; no new draws.** EXP-011 is post-processing of frozen measurements, like EXP-007.
- **Decision space**: the frozen EXP-006 `τ`-frontier `{0.00, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00} × materiality_bps(domain)`, gate-stack referee only. `τ=1.00` = frozen strict reference; `τ=0.00` = lenient endpoint (erratum). No new thresholds, no `τ` values added after reading results.
- **Loss specifications**: the three predeclared losses A (primary) / B / C above, with frozen coefficients. Measured once.
- **Parameters**: domains 5m / 1h / 4h; primary `α₀ = 0.05` (the α grid {0.10, 0.05, 0.01} is reported for context only, never to select a different recommendation); materiality buffers 0.5 / 1.5 / 3.0 bps (frozen).
- **Instruments**: EURUSD, XAUUSD, BTCUSD, USTEC, **pooled by domain** for the headline recommendation (matches how EXP-003/006 calibrated the lever). The EXP-008 per-instrument MDE map enters only as a **robustness/masking overlay** for the conditional adoption rule, never as the headline decision object.
- **Time range**: Full dataset with nested chronological split as already applied by the upstream experiments. First 70% = analysis set; final 30% = global holdout, **never loaded or inspected**. EXP-011 reads only derived result tables, which were themselves produced under this split.
- **Global holdout**: not loaded, inspected, or used in any capacity. No code path touches raw market data or the holdout.
- **Look-ahead bias prevention**: no new signal construction. All reused fields derive from the frozen `t → t+1` real Close-to-Close returns with train-only block-length estimation already in EXP-003.
- **Real-price outcome discipline**: every effect, CI, MDE, FPR, TPR, and sub-material quantity reused is based on **real domain `Close` prices**. No synthetic (HA / Renko) prices are in scope.
- **Exclusions**:
  - **Adopting or freezing** any operating point or referee variant (Phase 003, fresh draws — D-posture).
  - Re-running or modifying the frozen referees, the substrate, the harness, or any upstream draws.
  - Tuning loss coefficients against any observed result; adding loss specifications or `τ` values after reading results.
  - A separate "lenient mechanism" axis (erratum: it is the `τ=0` endpoint — would double-count).
  - Per-instrument *headline* recommendations (per-instrument is overlay-only).
  - Walk-forward / purged-CV *re-selection* (EXP-010 enters only as a split-sensitivity caveat on the single-split recommendation).
  - Chart-type signals; the incremental-information unit (Phase 003 seed); programme-level multiplicity.

## Success / Failure / Inconclusive Criteria

EXP-011 is exploratory; the deliverable is a recommendation, not a SUPPORTED/REFUTED verdict.

- **Success (recommendation delivered)**: for every domain, (a) a loss-minimising operating point `τ*_A` is selected under the primary loss with the FPR-precision gate met (`FPR` Wilson half-width `≤ 0.03`) and the MDE reportable at `α₀`; (b) the cross-loss consistency verdict (ROBUST / LOSS-SENSITIVE) is recorded with `{τ*_A, τ*_B, τ*_C}`; (c) the predeclared conditional adoption rule is recorded; (d) the EXP-008 per-instrument and EXP-010 split-protocol overlays are reported as adoption caveats. Phase success (design §9d) is **landing the recommendation + rule**, not adopting anything.
- **Inconclusive (per domain)**: the FPR/TPR/sub-material inputs for that domain fail their precision targets, or the required upstream artifact is missing/invalid, or all three losses are non-discriminating in a way that prevents naming a single `τ*_A`. Reported honestly as "no recommendation for domain `d`", not forced.
- **Failure (experiment-level)**: a required upstream dependency artifact (EXP-003/006 in particular) is missing or fails its own internal reproduction gate, so the lever cannot be evaluated at all.

## Complexity Budget

- Max statistical operations: **2** (per-`τ` loss evaluation + the cross-loss consistency/precision gating; both mechanical/deterministic, no new inference).
- Max visualisations: **4**.
- Max new code modules: **1** (optional small `loss_functions.py`; inline is acceptable).

## Data Requirements

Inputs (all existing, result-level; **dependency-maturity note:** EXP-008/009/010 have produced results but have **not** completed their own Stage 5–8 — confirmed sound by a lightweight correctness check on 2026-06-04; EXP-011 *execution* is gated until EXP-008, and ideally EXP-009/010, complete post-experiment governance):

| Source | File(s) | Role in EXP-011 |
|---|---|---|
| EXP-003 | `results/mde_summary.csv` | Strict reference MDE (`τ=1.0`) cross-check |
| EXP-006 | `results/threshold_mde_summary.csv`, `threshold_fpr_summary.csv`, `threshold_tpr_summary.csv` | `MDE(d,τ)`, `FPR(d,τ)`, `TPR(d,τ,e)` — primary decision inputs |
| EXP-006 | `results/threshold_draw_verdicts.csv` | Draw-level reconstruction of `sub(d,τ)` for `τ>0` (only if needed; bounded) |
| EXP-007 | `results/submaterial_pass_rates.csv`, `lenient_vs_frontier.csv` | `sub(d, τ=0)` and erratum/endpoint corroboration |
| EXP-008 | `results/per_instrument_mde_summary.csv`, `mde_pool_comparison.csv` | Per-instrument robustness/masking overlay (adoption caveat) |
| EXP-009 | `results/effect_distribution_summary.csv`, `effect_vs_mde.csv` | Context reality-check: where real untuned effects sit vs the material band |
| EXP-010 | `results/protocol_comparison.csv`, `protocol_mde_summary.csv` | Split-protocol sensitivity overlay (adoption caveat) |
| EXP-005 | `results/run_metadata.json` | Honest-detection-floor context (gate not blind) for the adoption rule |

Each upstream artifact's `run_metadata.json` is checked for its completion token before its values are read (EXP-003 `COMPLETE`, EXP-006 `COMPLETE` + `strict_reference_pass`, etc.). A missing/incomplete dependency makes the affected domain Inconclusive rather than producing a fabricated recommendation.

### Standard Loading Pattern

Result-level post-processing is the norm for EXP-011 (no market data is touched). The first-70% slice pattern below is included **only** as the mandatory safety pattern if implementation ever loads raw bars (it must not):

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)
bars = scan.slice(0, analysis_cutoff).collect()
```

## Predeclared conditional adoption rule (recorded in Phase 002, executed in Phase 003)

For each domain, the recommended operating point is `τ*_A` (corroborated by B/C via the consistency verdict). **Adoption over the frozen strict reference (`τ=1.0`) is deferred to Phase 003 and conditional on re-confirmation on fresh draws:**

> Adopt `τ*` for domain `d` only if, on **fresh Phase 003 synthetic draws**, all hold: (i) `FPR(d, τ*)` Wilson upper `≤ α₀ = 0.05`; (ii) `sub(d, τ*) ≤ 0.50` at the operating MDE; (iii) an EXP-005-style realistic-candidate carrying an edge ≥ `MDE(d, τ*)` is detected with TPR `≥ 0.80`. If any condition fails on fresh draws, **retain the frozen strict reference `τ=1.0`** for that domain.

Two predeclared caveats attach to the rule:
- **Split-sensitivity (EXP-010):** the 1h and 4h MDE roughly doubles under walk-forward vs the mandated single split, while FPR stays controlled. The 1h/4h recommendation is **explicitly conditional on the single chronological split** and must be re-confirmed under walk-forward before adoption; 5m is split-robust.
- **Non-blindness (EXP-005):** the strict gate already meets the honest-detection-floor test on all domains (`DETECTED_FLOOR`), so any recommendation to move below `τ=1.0` is a *sensitivity-headroom* choice under the loss, **not** a remedy for demonstrated blindness — the adoption rule must say so.

## Suggested Direction

Treat EXP-011 as a mechanical read of a frozen loss over a frozen lever, not a search. Expect (do not engineer) the FPR term to be inactive on the null substrate and the **sub-material term to be the economically binding criterion**, especially at 5m where the `τ=0` endpoint's sub-material rate (0.4965 from EXP-007) sits just under the 0.50 cutoff. The honest synthesis is likely: *"the loss favors a low-`τ` operating point on the lever, but the gain over the frozen strict reference is mostly sub-material at 5m and is split-protocol-sensitive at 1h/4h; recommend with those conditions, ratify on fresh draws in Phase 003."*
