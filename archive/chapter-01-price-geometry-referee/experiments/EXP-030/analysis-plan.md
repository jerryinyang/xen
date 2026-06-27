# Analysis Plan: Experiment EXP-030

## Objective

Determine whether the faithful selective AVWAP strategy — trade logic identical to the
EXP-028/029 baseline — retains **positive net per-event expectancy** on at least one
domain (5m, 1h, 4h) after a predeclared, event-level per-position cost/slippage model is
charged, on the first-70% analysis set. The **CONSERVATIVE** cost variant is binding;
**BASE** is a reported diagnostic that never decides the verdict.

This is the **hard tradability gate** for any future holdout-release experiment
(EXP-032, deferred). The Phase 006 result (`EVAL_SUPPORTED`, cTrader-confirmed) is
**gross of all costs**; this experiment is a deterministic cost overlay on the
already-validated EXP-022 realized positions (EXP-028 PRIMARY event set, EXP-029
production-path parity confirmed).

## Binding-metric discipline (read before implementing — the central correctness point)

The scope designates **absolute net per-event expectancy** as the binding metric. This is
a **different quantity** from the EXP-028 PRIMARY matched-control *excess*, and confusing
the two is the single largest implementation risk in this experiment.

| Quantity | Definition | Role in EXP-030 |
|---|---|---|
| EXP-028 PRIMARY **excess** | `mean( event_lifetime_bps − mean(matched_control_lifetime_bps) )` | **Reconciliation anchor only** (must reproduce +5.78/+23.38/+69.02). **Not** the cost base. |
| Gross **absolute** event expectancy | `mean( event_lifetime_bps )` (no control subtraction) | The quantity costs are charged against. Per EXP-024, the absolute 5m hold is ~0 while the excess is positive — so these differ materially, by design. |
| **Binding net** expectancy | `mean( event_lifetime_bps − RT_i )` = gross absolute − `RT_i` | **The verdict basis.** |
| Attribution companion (non-binding) | gross excess − `RT_i` (controls uncosted) | Continuity with Phase 006; never decides. |

**Costs are subtracted from the absolute event lifetime, not from the excess.** The
scope's "Suggested Direction" prose loosely calls +5.78 bps "gross"; that figure is the
*excess*. The frozen binding definition (scope §"Estimand and denominators") is the
absolute series, and this plan implements it. Because matched controls are counterfactual
(never traded), the deployable per-event P&L is the event leg net of its own round-trip
cost — the absolute metric. A 5m net-negative is therefore an **expected, informative**
outcome (EXP-024: edge is relative-not-absolute on 5m), not an experiment failure.

## Frozen vs. re-used components

Only the **inference-tail functions** are frozen and imported unchanged from
`python/experiments/EXP-027/code/event_method.py`, hash-guarded by `inspect.getsource`
over the named symbols (mismatch → abort `FROZEN_INFERENCE_MODIFIED`; **not** a whole-file
hash):

| Reused **unchanged** (frozen tail) | Defined in EXP-030 (predeclared) |
|---|---|
| `build_strata`, `bootstrap_effect_distribution`, `domain_effect`, `holm_adjust`, `decide_label` | the **net-series construction** (cost subtraction); the **one-sided bootstrap p-value** on the absolute estimand; cost-table join; break-even/attribution/diagnostic tables |

The **stratified sign-permutation leg (`permutation_p`) is deliberately NOT used as a
binding test.** The absolute net estimand has no symmetric paired null (subtracting a
control is what made EXP-028's null sign-symmetric), so a sign-permutation p-value would
be invalid here. The scope explicitly authorizes Stage 2 to define the p-value mechanics
provided the `CI_low > 0` requirement is not weakened — see Step 4. The permutation-exact
significance that the gross PRIMARY carries lives upstream (EXP-028, already read); this
experiment **conditions on** that result and adds only the cost layer.

No new or modified `python/src/xen/` module. **No domain-bar reconstruction is performed**
— every input is a column already present in EXP-022's `lifetime_observations.csv`, whose
`lifetime_bps` values were reconciled against rebuilt frames in EXP-028 and confirmed on
the cTrader production path in EXP-029. This removes the EXP-027/028 index-misalignment
failure surface entirely; the substitute integrity guard is the Step-2 reconciliation.

## Methodology

### Step 1: Dependency gate

- **Method**: Load and assert upstream status before any computation:
  - `EXP-028/results/run_metadata.json`: overall verdict `EVAL_SUPPORTED`.
  - `EXP-029/results/run_metadata.json`: parity verdict `CONSISTENT` (cTrader-confirmed).
  - `EXP-022/results/lifetime_observations.csv` exists and carries the `role`,
    `reportable_event`, `regime_id`, `direction`, `is_pyramid_bounce`, `lifetime_bps`,
    `instrument`, `domain` columns.
  - Frozen-tail hash guard over the five named EXP-027 functions.
- **Why this method**: The cost overlay is only meaningful on the validated, cTrader-
  confirmed realized positions. EVAL_SUPPORTED + CONSISTENT are the binding pre-conditions
  the scope's execution-path declaration rests on.
- **Simpler alternative considered**: file-existence only. Rejected — governance requires
  status verification and frozen-code integrity.
- **Assumptions**: upstream `run_metadata.json` are well-formed and immutable post-verdict.
- **Expected output**: `dependency_status` + `frozen_tail_hash_ok` flags in
  `run_metadata.json`; hard-fail with diagnostic on any miss.

### Step 2: Event set, cost join, and reconciliation guard

- **Method**:
  1. **Event set** = `role == "event"` AND `reportable_event == true` rows of
     `lifetime_observations.csv` (pyramids **included**, faithful to EXP-028; matched
     controls = `role == "control"` rows sharing
     `(instrument, domain, regime_id, event_trigger_idx)`). This selection must reproduce
     the EXP-028 counts exactly: 5m=12795, 1h=924, 4h=187.
  2. **Cost join**: attach per-instrument one-way `c_i` and round-trip
     `RT_i = 2·c_i` (BASE) and `RT_i^cons = 4·c_i` (CONSERVATIVE = 2×BASE) from the frozen
     scope cost table (`EURUSD 0.75 / USTEC 1.25 / XAUUSD 1.50 / BTCUSD 4.00` one-way bps;
     **pending the single Stage-4 operator confirmation**). Record a content hash of the
     applied table in `run_metadata.json`.
  3. **Reconciliation guard (substitute for EXP-028's frame-alignment assertion)**:
     recompute the gross matched-control **excess** through the frozen aggregation
     (`build_strata` → `domain_effect` over `event_lifetime_bps − mean_control_lifetime`)
     and assert it reproduces EXP-028 `event_level_results.csv` `effect_bps`
     (5.778 / 23.384 / 69.016) to a tight tolerance (≤ 0.01 bps). **Hard-fail** on
     mismatch — this proves the event set, control linkage, and aggregation are identical
     to the validated upstream, so the only change is the cost overlay.
  4. **Holdout fence (inherited)**: all rows originate from EXP-022's first-70% run; assert
     no new bar load and record the inherited fence statement. Right-censored events
     (`outcome == "unfinished"`, n=2) are excluded by the `reportable_event` filter; record
     the count.
- **Why this method**: Reusing validated lifetime values + a reconciliation anchor is
  strictly safer than rebuilding domain frames and re-deriving returns (which is exactly
  where EXP-027 introduced an index bug). If the gross excess reproduces, the substrate is
  proven byte-faithful.
- **Simpler alternative considered**: trust the CSV without reconciliation. Rejected —
  the reconciliation is cheap and is the integrity backbone of a pure-overlay experiment.
- **Assumptions**: EXP-022 `lifetime_bps` is the direction-signed log lifetime return on
  real domain `Close` (verified upstream); `regime_id` is the dependence-cluster unit.
- **Expected output**: joined per-event table
  `(instrument, domain, regime_id, direction, is_pyramid_bounce, lifetime_bps,
  mean_control_lifetime_bps, c_i, rt_base, rt_cons)`; reconciliation residuals; counts
  (total, excluded, pyramid split) in `run_metadata.json`.

### Step 3: Net series construction (absolute binding metric)

- **Method**: For each event, form
  - `net_lifetime_base = lifetime_bps − rt_base`
  - `net_lifetime_cons = lifetime_bps − rt_cons` (**binding**)
  Each realized position (including each pyramid bounce, which is an independent position
  under EXP-029-corrected semantics) bears exactly one round-trip charge; nothing is
  amortized across pyramid legs. Slippage is folded into `c_i` (spread-scaled, **not**
  ATR/band-scaled) per the scope's fixed decision. `lifetime_bps` and `RT_i` are in
  identical bps units (`10000·direction·ln(exit/entry)`), subtracted directly.
- **Why this method**: This is the deterministic arithmetic the scope predeclares; the net
  per-event series is the deployable per-position P&L.
- **Simpler alternative considered**: subtract `RT_i` from the *excess*. **Rejected — that
  is the binding-metric error this plan exists to prevent** (it would cost the controls'
  uncosted benchmark, not the traded leg). Subtracting from the excess is computed only as
  the *non-binding attribution companion* (Step 6).
- **Assumptions**: per-position round-trip charge is the correct unit (scope-fixed);
  financing/swap/sizing excluded (stated limitation).
- **Expected output**: per-event `net_lifetime_base`, `net_lifetime_cons` columns.

### Step 4: Binding inference — net per-event expectancy (frozen aggregation + bootstrap p)

- **Method** (applied to `net_lifetime_cons`; re-run on `net_lifetime_base` as diagnostic):
  1. **Point estimate** (`domain_effect`): each instrument's **event-weighted** mean of
     the net series, then **equal-weight** mean across the (≥3 of 4) reportable instruments
     — identical aggregation structure to EXP-028 PRIMARY.
  2. **95% regime-cluster bootstrap CI** (`build_strata` → `bootstrap_effect_distribution`,
     `N_BOOT = 1000`, percentiles (2.5, 97.5)): resample `regime_id` clusters with
     replacement within `(instrument, direction)` strata, recompute the instrument-averaged
     net mean. This absorbs within-regime / pyramid dependence exactly as in EXP-028.
  3. **One-sided bootstrap p-value** for `net expectancy > 0`:
     `p = (1 + #{ boot_effect ≤ 0 }) / (1 + N_BOOT)` over the bootstrap distribution
     returned by `bootstrap_effect_distribution`. (This replaces `permutation_p`, which is
     invalid for the absolute estimand. It does **not** weaken the `CI_low > 0`
     requirement — both must hold for FOR.)
  4. **Holm across the 3 domains** (`holm_adjust`) on the one-sided bootstrap p; α₀ = 0.05.
  5. **Per-domain verdict** via `decide_label(effect, ci_low, ci_high, holm_p, alpha,
     effect_h1, effect_h6)` with `effect_h1 = effect_h6 = +1.0` **sentinel** (predeclared):
     there is no secondary-horizon stability concept for the absolute lifetime estimand, so
     the `INCONCLUSIVE_SECONDARY_UNSTABLE` branch is intentionally disabled. The rule
     reduces to: **EVIDENCE_FOR** ⇔ `effect > 0 ∧ CI_low > 0 ∧ Holm_p ≤ α₀`;
     **EVIDENCE_AGAINST** ⇔ `CI_high ≤ 0`; else **INCONCLUSIVE_SPANS_ZERO**.
  6. **Commute check (correctness)**: because `net = gross_abs − RT_i` is a per-instrument
     constant shift and all instruments are present in every resample, the BASE and
     CONSERVATIVE bootstrap distributions must be identical in shape, offset by exactly
     `mean_inst(RT_cons − RT_base) = mean_inst(RT_base)` at the domain level. Assert this to
     float tolerance; mismatch indicates a join or aggregation bug.
- **Why this method**: The regime-cluster bootstrap is the validated handler for clustered,
  heavy-tailed, non-normal event returns; the absolute estimand's wider CI (no
  control-differencing) is the honest cost of asking an absolute-P&L question. FPR control
  of the *gross excess* PRIMARY is upstream (EXP-028); here the binding object is the
  bootstrap CI on net P&L, which is assumption-light and appropriate.
- **Simpler alternative considered**: per-event t-test / Wilcoxon on the net series.
  Rejected — both assume cross-event independence, violated by within-regime/pyramid
  clustering. Reusing the sign-permutation leg: rejected — invalid for an absolute
  (non-paired-symmetric) estimand.
- **Assumptions**: regime clusters are the dependence unit; instruments equal-weighted;
  bootstrap ~95% coverage (EXP-027-validated structure); the one-sided bootstrap p is a
  valid significance summary for a strictly-positive-mean alternative.
- **Expected output**: `results/net_expectancy_results.csv` — per domain, per variant
  `(domain, variant, net_effect_bps, ci_low, ci_high, ci_half_width, boot_p, holm_p,
  n_events, n_bull, n_bear, n_instruments, verdict)`; CONSERVATIVE rows are binding.

### Step 5: Per-instrument net + break-even diagnostic (descriptive)

- **Method**:
  1. **Per-instrument net expectancy** = event-weighted mean of `net_lifetime_cons` (and
     BASE) per (instrument, domain), with a regime-cluster bootstrap CI (reuses Step-4
     machinery; no new test) for context only — the binding verdict is domain-level.
  2. **Break-even round-trip cost** per (instrument, domain) = the gross **absolute**
     per-event expectancy `mean(lifetime_bps)` (the `RT` at which net crosses zero, since
     `net = gross_abs − RT`). Computed from gross quantities so it cannot motivate any
     cost-model revision. A table/heatmap, **not** a gate.
- **Why this method**: localizes which instruments survive costs and exposes the cost
  headroom directly; the break-even framing communicates tradability margin without a new
  metric.
- **Simpler alternative considered**: report only domain aggregates. Rejected — the
  per-instrument break-even is the most decision-useful descriptive output and is free.
- **Assumptions**: same as Steps 3–4.
- **Expected output**: `results/net_by_instrument.csv`
  `(instrument, domain, gross_abs_bps, net_base_bps, net_cons_bps, breakeven_rt_bps,
  n_events)`.

### Step 6: Attribution companion (non-binding)

- **Method**: `net matched-control excess = EXP-028 gross excess − RT_i` (controls
  uncosted), aggregated through the frozen tail per domain for both variants. Reported for
  Phase-006 continuity; **never** decides the verdict.
- **Why this method**: shows what the costed-event-vs-uncosted-control comparison looks
  like, for narrative continuity with EXP-028; explicitly subordinate to the absolute
  binding metric.
- **Simpler alternative considered**: omit it. Rejected — the scope requires it as a
  declared companion so the absolute-vs-relative gap is visible.
- **Assumptions**: the gross excess equals EXP-028's (enforced by Step-2 reconciliation).
- **Expected output**: `results/attribution_companion.csv`
  `(domain, variant, net_excess_bps, ci_low, ci_high, holm_p)`.

### Step 7: Verdict assembly and phase outcome

- **Method**: Bind on the **CONSERVATIVE** rows of Step 4.
  - **Per-domain verdict** = CONSERVATIVE `decide_label` output.
  - **Phase outcome**:
    - **TRADABLE**: ≥1 domain CONSERVATIVE `EVIDENCE_FOR`.
    - **NOT_TRADABLE**: every reportable domain CONSERVATIVE `EVIDENCE_AGAINST` **with
      adequate in-experiment power** (event counts ≥30/≥8-per-direction/≥3-instruments AND
      a finite bootstrap CI half-width tight enough to exclude a material positive net
      effect). The EXP-027 numeric MDE (1/4/32 bps) is **not** the lifetime-power threshold
      (it is in fixed-`H=3` units; lifetime returns are larger-magnitude/higher-variance) —
      same power discipline as EXP-028.
    - **INCONCLUSIVE**: no domain FOR, but ≥1 reportable domain cannot be read cleanly
      AGAINST, **or** a BASE/CONSERVATIVE straddle (BASE clearly positive, CONSERVATIVE CI
      spanning 0). Stated explicitly; does **not** authorize a third cost variant.
  - **Anti-trap record**: a 5m-only net-negative with 1h/4h FOR is **TRADABLE**, not
    NOT_TRADABLE. A 5m net-negative in isolation is the expected stress case, not failure.
  - BASE variant and the attribution companion annotate but never flip the verdict.
- **Expected output**: `run_metadata.json` (`phase_outcome`, per-domain CONSERVATIVE
  verdicts, BASE diagnostics, dependency + reconciliation + commute flags, cost-table hash,
  seeds, determinism replay).

## Visualisations (4 / 4)

1. **Net expectancy forest** (`plots/net_expectancy.png`): per-domain net per-event
   expectancy with 95% regime-cluster bootstrap CI, **BASE vs CONSERVATIVE** side by side,
   reference line at 0; annotate `n_events`, Holm-p, verdict. Answers: does net survive
   costs, and how far does CONSERVATIVE move it.
2. **Gross→net waterfall** (`plots/gross_to_net_waterfall.png`): per domain (and per
   instrument inset) `gross_abs → −RT → net`, both variants. Answers: how much of the gross
   absolute edge each cost component consumes.
3. **Break-even heatmap** (`plots/breakeven_heatmap.png`): break-even round-trip cost per
   instrument×domain with the BASE/CONSERVATIVE `RT_i` overlaid. Answers: which cells have
   positive cost headroom.
4. **Verdict summary** (`plots/verdict_summary.png`): traffic-light per-domain CONSERVATIVE
   verdict with net effect/CI/Holm-p, BASE annotated alongside, and the (non-binding)
   attribution companion shown discounted. Answers: the headline tradability read.

## Interpretation Guide

- ≥1 domain CONSERVATIVE `EVIDENCE_FOR` (`net>0`, `CI_low>0`, `Holm_p ≤ 0.05`) →
  **TRADABLE**: the faithful AVWAP strategy retains positive net per-event expectancy under
  conservative costs on that domain; EXP-032 holdout release becomes admissible (its own
  governance; a thin-n domain such as 4h, n≈187, must be weighed there).
- Every reportable domain CONSERVATIVE `EVIDENCE_AGAINST` with adequate power →
  **NOT_TRADABLE**: real gross edge, no net edge under costs. No holdout release; pivot to
  EXP-031 mechanism read / Stage-C / HYP-001 per design §9. This does **not** overturn the
  Phase-006 gross result (different, non-substitutable estimand) and does **not** say the
  bounce event has no edge (EXP-021 shows it does at fixed horizon).
- No FOR but a domain not cleanly AGAINST, or a BASE-positive/CONSERVATIVE-straddle →
  **INCONCLUSIVE**, straddle stated. No third cost model.
- Report all effects as bps per event with CIs. **Never** a percentage improvement over a
  ~0 baseline. Non-finite ratios reported as-is, never 0.

## Implementation Safety Constraints

- **Binding metric is ABSOLUTE net** (`mean(lifetime_bps) − RT_i`), not the excess minus
  cost. Subtracting `RT_i` from the excess is the *attribution companion* only.
- **Frozen tail only**: import and `inspect.getsource`-hash-guard `build_strata`,
  `bootstrap_effect_distribution`, `domain_effect`, `holm_adjust`, `decide_label`; abort
  `FROZEN_INFERENCE_MODIFIED` on mismatch. No whole-file hash.
- **No sign-permutation as a binding test** — invalid for the absolute estimand; binding
  significance is the one-sided bootstrap p + Holm, jointly with `CI_low > 0`.
- **Pyramids included**; each realized position bears one round-trip charge; nothing
  amortized across pyramid legs. `is_pyramid_bounce` reported as a diagnostic split.
- **Reconciliation guard**: recomputed gross excess must reproduce EXP-028
  (5.778/23.384/69.016) within ≤0.01 bps before any net number is read; hard-fail
  otherwise. This is the integrity substitute for frame-alignment (no frame is rebuilt).
- **Commute check**: BASE and CONSERVATIVE domain bootstrap distributions identical in
  shape, offset by `mean_inst(RT_base)`; assert to float tolerance.
- **Holdout fence inherited**: all inputs are EXP-022 first-70% rows; no new bar load; no
  holdout in any form (release is EXP-032, out of phase).
- **Cost table frozen**: the per-instrument `c_i` table is fixed by scope pending the
  single Stage-4 operator confirmation; its content hash is recorded; no post-result cost
  re-selection, no alternative tables, no third variant — a net-negative is a valid outcome.
- **Real-price discipline**: all returns are direction-signed log returns on real domain
  `Close` (inherited from EXP-022); no synthetic chart prices in any role.
- **Power for AGAINST** from in-experiment CI half-width + counts; the EXP-027 MDE is not
  the lifetime-power threshold.
- **Determinism**: all randomness via `seed_for(EXPERIMENT_ID, domain, purpose)` (EXP-028
  convention); one-domain replay asserts byte-identical results; record in
  `run_metadata.json`.
- **Performance / output**: pure in-memory overlay on a single CSV; `tqdm` over the per-
  domain/per-variant bootstrap loops; helper functions return data (no helper-level print);
  output directories created only in orchestration; no import-time side effects.

## Complexity Check

- **Statistical tests: 1 / 3** — the regime-cluster bootstrap CI + one-sided bootstrap p +
  Holm on the binding net metric. The BASE-variant re-run, per-instrument CIs, attribution
  companion, and commute check all **reuse** that one machinery (diagnostic applications),
  adding no new test type. Well within the budget of 3.
- **Visualisations: 4 / 4** — net expectancy forest; gross→net waterfall; break-even
  heatmap; verdict summary.
- **New code modules: 1 / 1** — `python/experiments/EXP-030/code/run_experiment.py`,
  importing the frozen inference tail from `EXP-027/code/event_method.py` (hash-guarded
  over the named functions). No new/modified `python/src/xen/` module.
