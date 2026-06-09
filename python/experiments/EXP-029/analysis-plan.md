# Analysis Plan: Experiment EXP-029 — cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy

## Objective

Confirm that the **corrected** C# AVWAP strategy (`AvwapBounceModel.cs`, pyramid
bounces included), run **bar-by-bar inside cTrader's engine** via the validated
`tools/ctrader-cli/` per-bar streaming path, reproduces the **event-level**
findings of the Python-only EXP-028 re-analysis under the **frozen EXP-027
event-level evaluation method**.

This is a **parity confirmation**, not a re-litigation of edge. EXP-028 already
found `EVAL_SUPPORTED` (all 3 domains `EVIDENCE_FOR`) on the canonical EXP-020/022
event substrate; EXP-029 adds the missing **production-path** evidence the EXP-028
omission record identified. The binding question is per-domain:

> Does the cTrader per-bar streaming execution, evaluated through the *same*
> estimand and the *same* frozen inference EXP-028 used, agree with EXP-028's
> per-domain PRIMARY verdict and effect — within the scope's parity tolerances?

We must determine, for each domain (5m / 1h / 4h):
1. the cTrader per-bar PRIMARY event-level effect (matched-control excess, bps),
   its 95% regime-cluster bootstrap CI, Holm-adjusted permutation p, and verdict;
2. whether that verdict and effect are **CONSISTENT** with EXP-028 under the
   predeclared parity criteria;
3. the resulting parity disposition (`CONSISTENT` / `INCONCLUSIVE` / `INCONSISTENT`)
   and its consequence for EXP-028's status.

This experiment was created to close **two** prior divergences. Both are guarded
explicitly below (see *Divergences To Avoid*):
- **D1 — execution-path divergence** (EXP-028 omission): the faithful re-screen
  must come from the cTrader per-bar streaming path, not a pure Python re-analysis.
- **D2 — estimand/framing divergence** (Phase-005 root cause, recurred once in
  EXP-028 Stage 4): the comparison must be on the **same estimand** EXP-028
  reports — per-event *symmetric own-exit matched-control excess* — never raw
  per-event return against EXP-028's excess.

---

## Adversarial-review hardening (2026-06-09)

A pre-execution adversarial review found the original parity design could only
*confirm* EXP-028: a coarse "verdict + CI-overlap" read with a CI-overlap primary
signal could not be falsified by a magnitude divergence, the binding estimand's Python
re-scan left the corrected C# completion code ungraded, count drift was pre-attributed
to "benign feed coverage" without a signal-layer check, the pyramid split was not
gated, and the frozen-hash equality was documented-but-unenforced. The plan adds five
binding hardenings, all **predeclared here before any cTrader result exists** (D8):

- **F01 — exit-parity (new Step 4b, binding).** The corrected C# concurrent-completion
  code is graded per event against the Python `scan_lifetime` on the **same** feed
  (exit bar, reason, signed bps). The C# now serializes its executed completion onto
  the event-detail row (`ExitIdx`/`ExitTime`/`ExitClose`/`ExitReason`/`ExitBars`/
  `ExitLifetimeBps`). A domain whose C# exits reproduce the Python scan on <99% of
  completed events is **INCONSISTENT**. (The binding PRIMARY estimand still uses the
  symmetric Python scan for both event and control, preserving EXP-028 comparability;
  exit-parity is a separate gate, not a change of estimand.)
- **F02 — magnitude equivalence (Step 6).** CONSISTENT requires the EXP-029 vs EXP-028
  effect difference inside `max(2 bps, 25%·|ref|)`; a difference beyond
  `max(2 bps, 50%·|ref|)` is **INCONSISTENT**. CI overlap is demoted to a diagnostic.
- **F03 — signal-layer 5m reconciliation (new Step 3b, binding on 5m).** The C# 5m
  event set is reconciled against the EXP-020 substrate (≥98% trigger match; matched
  frozen-target median rel-diff ≤1e-3). On the feed-exact 5m domain this isolates
  signal-layer parity from feed drift, so a signal-logic divergence is not absorbed as
  "benign feed coverage". A 5m divergence blocks a CONSISTENT upgrade.
- **F04 — pyramid split in the count gate (Step 6).** Per-domain pyramid count must be
  within ±10% of EXP-028's (loaded from EXP-028 `event_diagnostics.csv`).
- **F05 — frozen-hash hard-assert (Step 0).** `frozen_inference_hash` is hard-asserted
  equal to EXP-028's recorded `ea261b9ee0a8aca3`; mismatch aborts (no longer a
  non-gating boolean).

Overall: **INCONSISTENT** if any domain is INCONSISTENT; else **CONSISTENT** iff all
gates hold on ≥2/3 domains and 5m signal-layer passes; else **INCONCLUSIVE**.

---

## Dependencies & Gates

| Dependency | Required state | Check | Consequence if unmet |
|------------|----------------|-------|----------------------|
| EXP-027 method | `method_verdict == METHOD_VALID` (`EXP-027/results/run_metadata.json`) | hard assert at startup | abort — no valid yardstick / inference tail |
| EXP-028 results | `event_level_results.csv` + `run_metadata.json` (`overall_verdict == EVAL_SUPPORTED`) present | hard assert; load as comparison target | abort — no parity reference |
| Frozen inference tail | local `event_method.py` byte-identical to `EXP-027/code/event_method.py` for the named `FROZEN_FUNCTIONS` | sha256 source guard (see Step 0) | abort `FROZEN_INFERENCE_MODIFIED` |
| Corrected C# model | `AvwapBounceModel.cs` opens/tracks one position per bounce (incl pyramids) and **serializes** the per-event AVWAP-detail table | C# contract (see *C# Behavioral & Emission Contract*) + emission-schema assert on ingest | abort — cannot reconstruct the estimand |
| cTrader CLI | `tools/ctrader-cli/` reachable; Docker image + credentials configured | invoked by orchestration step (manual-run gate) | abort — no cTrader run |
| cTrader runs | 12 cells (4 instruments × 3 domains) emitted under `data/strategy_runs/avwap_*` for the corrected model | presence + holdout-fence assert on ingest | abort / mark cell missing |

**Gate logic:** EXP-029 runs only when EXP-027 is `METHOD_VALID` (inference tail)
and EXP-028 results exist (comparison target). Both are satisfied as of the
2026-06-09 phase amendment.

---

## Methodology

### Step 0 — Frozen-inference + control-matching integrity guards

- **Method**: (a) sha256 over the *source* of the named frozen inference functions
  in the local `event_method.py` vs `EXP-027/code/event_method.py`; (b) call the
  bundled `verify_control_matching()` self-test (no market data).
- **Why this method**: identical to EXP-028's `verify_frozen_inference()` /
  `verify_control_matching()`. It proves the statistical method is byte-for-byte
  the EXP-027-calibrated one **before any data is touched**, so a CONSISTENT
  parity result cannot be an artifact of a silently-changed estimator.
- **Frozen function set** (must match EXP-028's `FROZEN_FUNCTIONS`):
  `domain_effect, build_strata, bootstrap_effect_distribution, permutation_p,
  holm_adjust, decide_label, sortino_ratio, wilson_interval, nearest_controls,
  equity_advantage`. Record the 16-char hash in `run_metadata.json`; it must equal
  EXP-028's `frozen_inference_hash = ea261b9ee0a8aca3`.
- **Simpler alternative considered**: trust-by-convention (no hash). Rejected — the
  whole experiment is a parity claim; the inference must be provably unchanged.
- **Assumptions**: none beyond source stability.
- **Expected output**: `frozen_inference_hash` (must equal EXP-028's),
  `control_matching_equivalence_pass = true`. Either failing → hard abort.

### Step 1 — cTrader per-bar streaming run (corrected C# model) [D1 guard]

- **Method**: orchestrate the corrected `AvwapBounceModel.cs` over all 12 cells
  via `tools/ctrader-cli/` (adapt `run-exp023-backtests.sh`; enable pyramid
  positions + the enriched event-detail emission). Each cell runs bar-by-bar
  inside cTrader's engine, resampling the 1-minute cTrader feed internally to the
  domain, fenced by `AnalysisEndUtc`.
- **Per-instrument `AnalysisEndUtc`** (identical to EXP-023/028; the C# host emits
  **no** row at or after it):
  `BTCUSD 2025-06-17T22:38:00Z`, `EURUSD 2025-05-09T16:55:00Z`,
  `USTEC 2025-05-12T04:54:00Z`, `XAUUSD 2025-05-12T03:35:00Z`.
- **Why this method**: this *is* the omission EXP-029 closes. The strategy must be
  evaluated **from its real execution environment** (cTrader per-bar streaming),
  the path VAL-002 validated, not from a Python re-aggregation of EXP-020/022
  events. The existing `avwap_baseline_*` runs are EXP-023 output (pyramids
  suppressed) and are **NOT reusable** — fresh runs from the corrected model only.
- **Simpler alternative considered**: reuse EXP-023's emitted runs. Rejected — they
  suppress pyramids (would drop ≈ half the events; EXP-028 had 6 785 pyramids of
  13 906) and lack the serialized event-detail table.
- **Assumptions / discipline**: deterministic in-engine generation; look-ahead-safe
  (sequential bars); holdout-fenced. cTrader resamples its **own feed**, so per-bar
  prices may differ slightly from local timebars (VAL-002: 5m exact; 1h/4h ≤ 1.83
  bps). This is expected and benign.
- **Expected output**: 12 `data/strategy_runs/<run>/` directories, each with
  `positions.parquet`, `events.parquet` (with the AVWAP event-detail columns),
  `trade_blotter.parquet`, `run_metadata.json` (incl. `analysis_end_utc`).
- **Execution note**: this step runs at the **manual execution gate** (the pipeline
  does not run experiment/cTrader code). The harness invokes/expects the runs but
  the operator performs the cTrader execution.

### Step 2 — Ingestion, domain frame on the cTrader feed, holdout re-assertion

- **Method**: for each cell, load `positions.parquet`; sort by `SourceCloseTime`;
  build the per-cell **domain frame** as the ordered `RealClose` series →
  `log_close`. **Returns basis = cTrader-emitted `RealClose`** (the strategy's own
  executed real domain bar close), per scope and VAL-002 self-consistency. Assert
  every `SourceCloseTime < AnalysisEndUtc` (Python re-assertion of the in-robot
  fence) and that `SourceCloseTime` is strictly increasing.
- **Why this method**: the estimand must be evaluated on the **same feed the C#
  executed on** so the parity test isolates execution-path effects, not feed
  swaps. Re-asserting the fence in Python is the mandatory holdout guard
  (architecture rule 6 / pipeline hard constraint).
- **Simpler alternative considered**: compute returns on local `data/timebars`
  frames (as EXP-028 did). Rejected — that would re-introduce the local feed and
  blur the cTrader-vs-Python comparison; scope mandates cTrader `RealClose`.
- **Assumptions**: temporal ordering by `SourceCloseTime`; one contiguous
  first-70%-fenced series per cell.
- **Expected output**: `{(instrument, domain): log_close ndarray}`, per-cell row
  counts, and a holdout-fence check table (`analysis_end` per instrument, max
  emitted `SourceCloseTime`).

### Step 3 — Event ingestion + index alignment (cTrader-sourced metadata)

- **Method**: load the cTrader-emitted **AVWAP event-detail** rows (bounce entries,
  incl pyramids). Each row carries, from the C# (already computed internally,
  serialized by the EXP-029 correction): `regime_id`, `direction`,
  `is_pyramid_bounce`, `anchor_age_bars`, `trigger_time` (`SourceCloseTime` of the
  trigger bar), `trigger_close`, `favorable_target_at_trigger`,
  `adverse_target_at_trigger`. Map each event's `trigger_time` to its integer
  `trigger_idx` in the cell's `SourceCloseTime`-ordered domain frame (timestamp
  join, **never bar-index transfer across feeds**). Hard-fail if a trigger
  timestamp is absent from the frame or if `trigger_close` disagrees with the
  frame `RealClose` at that timestamp beyond a tight tolerance (alignment guard,
  mirrors EXP-028 `validate_alignment` / reconciliation).
- **Why this method**: the strategy **signal** (regime, anchor, bounce, frozen
  targets, pyramid tag) is authored by the C# — Python must not re-derive it
  (architecture: *Python never re-generates the strategy signal as an oracle*).
  Python's only job downstream is the analysis construct (controls) and the frozen
  inference. The timestamp→index alignment guard is the cross-feed correctness
  check.
- **Simpler alternative considered**: re-run the AVWAP state machine in Python on
  the cTrader feed to recover regime/targets. **Rejected and forbidden** — that is
  a Python signal oracle and would defeat the parity purpose; it is exactly the
  kind of re-analysis EXP-029 exists to avoid.
- **Assumptions**: the C# serializes the event-detail table (see contract); one
  regime LUT is derivable from the contiguous `regime_id` runs in the frame.
- **Expected output**: a per-event table keyed
  `[instrument, domain, regime_id, direction, trigger_idx]` with the frozen
  targets, `is_pyramid_bounce`, and `trigger_close`; plus a per-cell **regime LUT**
  (`regime_id → start_idx, end_idx, anchor_idx, direction`) and a per-regime
  **trend-change boundary map** (opposite-regime confirmation bar), both derived
  from the emitted `regime_id` sequence — the inputs the imported EXP-021/022
  control helpers require.

### Step 4 — PRIMARY estimand reconstruction (binding) [D2 guard]

The PRIMARY estimand is **identical in definition** to EXP-028's
`build_primary_excess`: per-event **symmetric own-exit matched-control excess**,

```
paired_excess_bps = event_lifetime_bps − mean(control_lifetime_bps)
```

direction-signed log return in bps on real domain `RealClose`. Both the event and
its matched controls are completed under the **same** EXP-022 band-target /
trend-change own-exit rule, so the null paired-excess is mean-zero / sign-symmetric
and the frozen EXP-027 FPR control transfers.

- **Event lifetime**: for each cTrader event, complete its lifetime under the
  EXP-022 own-exit rule using the **imported, unchanged** EXP-022
  `scan_lifetime` / `transfer_targets` (loaded by file path, as EXP-028 does),
  driven by the cTrader-emitted frozen `favorable/adverse_target_at_trigger` and
  the cell's `log_close`/`Close` (cTrader feed) and the regime trend-change
  boundary. Only **completed** outcomes (`favorable`, `adverse`, `trend_change`)
  contribute; right-censored events are dropped — identical to EXP-028
  `COMPLETED_OUTCOMES`.
- **Matched controls (rebuilt in Python — the core D2 requirement)**: the cTrader
  run emits only the strategy's positions, **not** counterfactual controls. For
  each event, draw same-regime non-trigger control **start** bars via the imported
  EXP-021 `select_controls` (nearest anchor-age, EXP-022 `regime_candidate_base` /
  `build_exclusion_masks` for eligibility), and complete each control under the
  **same** own-exit rule (`transfer_targets` + `scan_lifetime`) from its own start.
  Require `≥ EM.MIN_CONTROLS` finite completed controls per event (else drop the
  event) — identical gate to EXP-028. `control_lifetime_bps` is the mean over the
  event's completed controls.
- **Why this method**: this reproduces EXP-028's binding estimand exactly, so the
  per-domain numbers are **comparable category-for-category**. Rebuilding controls
  (rather than importing EXP-022's `lifetime_observations.csv`, which was computed
  on the *local* feed for the EXP-020 event set) is mandatory because EXP-029's
  events live on the **cTrader feed** and may differ slightly in membership; the
  controls must be drawn and completed on that same feed for the same event set.
- **Simpler alternative considered & FORBIDDEN (D2)**: compare cTrader **raw
  per-event return** (trigger→exit) against EXP-028's matched-control **excess**.
  This is a category mismatch (the Phase-005 framing error) and is explicitly
  prohibited. The comparison target is excess-vs-excess only.
- **Assumptions**: regime LUT, trend-change map, and frozen targets are
  cTrader-sourced (Step 3); the EXP-021/022 control machinery is imported
  unchanged; reconciliation guard (Step 3) ensures index alignment so completion
  scans index the correct bars.
- **Expected output**: per-event PRIMARY table with
  `instrument, domain, regime_id, direction, is_pyramid_bounce, event_trigger_idx,
  event_lifetime_bps, mean_control_lifetime_bps, paired_excess_bps,
  n_controls_finite`, plus diagnostics (`n_primary_events`, pyramid split,
  reconciliation_bad — must be 0).

### Step 5 — Frozen EXP-027 inference (binding)

- **Method**: per domain, run the **imported, unchanged** frozen tail on
  `paired_excess_bps`: instrument-averaged equal-weight `domain_effect`;
  regime-cluster `bootstrap_effect_distribution` → 95% CI (percentiles 2.5/97.5,
  `N_BOOT = 1000`, `CHUNK = 200`); stratified paired sign-`permutation_p`
  (`N_PERM = 1000`); `holm_adjust` across the 3 domains; `decide_label` (Evidence-
  FOR rule + secondary-horizon stability, with the EXP-021 fixed-horizon {1,3,6}
  stability inputs computed the same way EXP-028 does when available). Reportability
  gates identical to EXP-028: `MIN_REPORTABLE_EVENTS = 30`,
  `MIN_DIRECTION_EVENTS = 8`, `DOMAIN_MIN_INSTRUMENTS = 3`; `ALPHA = 0.05`.
- **Why this method**: it is the only admissible yardstick (EXP-027, frozen).
  Reusing it unchanged is what makes the parity claim meaningful. **This counts as
  reused machinery, not a new test** — no statistical method is defined in EXP-029.
- **Simpler alternative considered**: a lighter two-sample test on raw returns.
  Rejected — would not be the calibrated event-level method and would break
  comparability.
- **Assumptions**: as calibrated in EXP-027 (sparse-event regime, mean-zero
  symmetric null); inherited, not re-tested here.
- **Expected output**: per-domain `effect_bps, ci_low, ci_high, ci_half_width,
  raw_p, holm_p, n_events, n_bull, n_bear, n_instruments, verdict` — the same
  columns as `EXP-028/results/event_level_results.csv`.

### Step 6 — Parity comparison vs EXP-028 + disposition (binding)

- **Method**: per domain, evaluate the predeclared binding gates against the loaded
  EXP-028 PRIMARY row (see *Adversarial-review hardening* above for thresholds):
  1. **Verdict agreement** — EXP-029 PRIMARY verdict == EXP-028 PRIMARY verdict.
  2. **Magnitude equivalence (F02)** — `|EXP-029 effect − EXP-028 effect| ≤
     max(2 bps, 25%·|EXP-028 effect|)`. This replaces the demoted point-in-CI check;
     CI overlap is computed only as a diagnostic.
  3. **Count alignment (F04)** — EXP-029 vs EXP-028 total count, bull/bear balance,
     **and pyramid split** each within **±10 %**.
  4. **Exit-parity (F01)** — the domain's C# exits reproduce the Python scan (Step 4b
     `exit_parity_ok`).
  5. **Signal-layer (F03, 5m only)** — Step 3b `signal_5m_ok`.
- **Per-domain band**:
  - **INCONSISTENT** if: a *powered* verdict conflict (verdict disagrees, EXP-029
    effect finite, CIs non-overlapping); **or** `|Δeffect| > max(2 bps, 50%·|ref|)`;
    **or** exit-parity fails. (An *underpowered* EXP-029 domain cannot be INCONSISTENT
    — it is INCONCLUSIVE.)
  - **CONSISTENT** if all five gates (1)–(5) hold.
  - **INCONCLUSIVE** otherwise (e.g. counts diverge >20 %, verdict differs but CIs
    overlap, domain underpowered, or 5m signal-layer divergent).
- **Overall disposition**: **INCONSISTENT** if any domain is INCONSISTENT (vetoes the
  upgrade); else **CONSISTENT** iff (1)–(5) hold on **≥ 2 of 3** domains **and** 5m
  signal-layer passes; else **INCONCLUSIVE**.
- **Why this method**: implements the strengthened scope Parity Criteria. The binding
  signal is verdict agreement **plus a bounded effect-difference** (not CI overlap,
  which cannot bound the disagreement) plus a graded C# completion (not a count) plus
  a feed-exact signal-layer check; the ±10 % count tolerance still absorbs benign
  1h/4h own-feed membership drift (VAL-002), which is *not* charged to the signal layer.
- **Simpler alternative considered**: keep the original verdict + CI-overlap rule.
  Rejected — it is confirmation-biased (cannot be falsified by a magnitude divergence)
  and leaves the corrected C# completion code ungraded.
- **Assumptions**: EXP-028 rows are the fixed reference (no recomputation of EXP-028).
- **Expected output**: `parity_comparison.csv` (per domain: both effects, both CIs,
  CI-overlap bool, effect delta, magnitude-equivalent/divergent flags, count deltas
  incl. pyramid, exit-parity + signal-layer booleans, per-domain band) and the overall
  disposition in `run_metadata.json`.

### Step 3b — 5m signal-layer reconciliation (binding on 5m; F03)

- **Method**: load EXP-020 `avwap_events.csv` (5m), and per instrument compare its
  bounce-trigger set to the C# 5m event set by **timestamp** (`reconcile_signal_layer`).
  Report matched fraction and, on matched triggers, the relative agreement of the
  frozen favorable/adverse targets. `signal_5m_ok` iff every instrument matches ≥98%
  of EXP-020 triggers and the matched-target median rel-diff ≤1e-3.
- **Why this method**: on 5m the cTrader feed reproduces local bars to float precision
  (VAL-002), so a 5m event-set mismatch is a **signal-layer** divergence, not feed
  drift — it cannot be excused as "benign feed coverage". (1h/4h are intentionally not
  reconciled: their feed differences are expected and absorbed by the ±10% count gate.)
- **Output**: `signal_reconciliation.csv` (per instrument: counts, matched fraction,
  target rel-diffs, pass/fail) and `signal_5m_ok` in `run_metadata.json`.

### Step 4b — Exit-parity grading of the C# completion code (binding; F01)

- **Method**: for every Python-scanned event, compare the C#-executed completion
  serialized on the event-detail row (`ExitIdx`/`ExitReason`/`ExitLifetimeBps`) to the
  Python `scan_lifetime` completion on the **same** feed (`build_exit_parity`): exit
  bar exact, reason equal, bps within 1e-3. `exit_parity_ok[domain]` iff ≥99% of
  completed events match. Restricted to the Python event population (apples-to-apples,
  F06 — not a raw blotter count over a different population).
- **Why this method**: the binding PRIMARY estimand re-scans exits in Python for
  EXP-028 comparability, which alone would leave the corrected C# concurrent-completion
  logic — the actual code the omission demanded — ungraded. Same feed + same frozen
  targets ⇒ a correct implementation matches to float; a multi-position completion bug
  drops the match rate and forces the domain INCONSISTENT.
- **Output**: `exit_parity.csv` (per domain: n_events, n_matched, match_rate, bar/
  reason/bps mismatch counts, max bps discrepancy, pass/fail) feeding Step 6.

### Step 7 — Diagnostics (non-binding)

- **(7a) Superseded by Step 4b.** The original coarse, count-only exit-alignment
  diagnostic is replaced by the **binding** per-event exit-parity grading (Step 4b),
  which the corrected C# executed-exit serialization now makes possible.
- **(7b) Pyramid split & event-count diagnostic**: per domain, event counts by
  direction and pyramid/non-pyramid, vs EXP-028's split (6 785 / 7 121).
- **(7c) Equity companion** (non-gating): exposure-matched cumulative own-exit
  log-return advantage on PRIMARY trades, mirroring EXP-028's `equity_companion`,
  for context only. Not part of any verdict.

---

## C# Behavioral & Emission Contract (consumed by the harness; built in Stage 3)

The harness depends on the following from the corrected `AvwapBounceModel.cs`. These
are **the only** C# changes; the AVWAP **signal logic** (regime detector, anchor,
AVWAP/band computation, bounce arm/trigger, re-arm, target freezing) is unchanged.

1. **Pyramid positions opened & tracked independently.** Replace the single-position
   state (`_position`, `_favorableTarget`, `_adverseTarget`, `pyramid_skipped` at
   `HandleTrigger`) with a set of concurrently-tracked positions; each bounce
   (incl. `isPyramid = _bounceCount > 1`) opens its own position with its own frozen
   targets, and `MaybeCompletePosition` evaluates each active position's own-exit
   (band-target / trend-change) independently. Multiple simultaneous positions
   permitted.
2. **Serialize the per-event AVWAP-detail table** (the "table EXP-029 consumes"):
   the model already constructs `AvwapEventDetail` (regime_id, direction,
   is_pyramid_bounce, anchor idx/time/price, trigger idx/time, trigger_close,
   favorable/adverse target at trigger, anchor_age_bars) — **serialize it** to the
   run output (e.g. as columns on `events.parquet` or a companion
   `avwap_events.parquet`). This is **serialization of already-computed state**, not
   a signal-logic change.
3. **`is_pyramid_bounce`** must appear on the per-event/per-position record the
   harness reads for per-event returns (matching EXP-028's diagnostic split).
4. **Serialize the C#-executed completion per bounce (F01).** When a position exits,
   backfill its `AvwapEventDetail` row with `ExitIdx` / `ExitTime` / `ExitClose` /
   `ExitReason` (`favorable`/`adverse`/`trend_change`/`open`) / `ExitBars` /
   direction-signed `ExitLifetimeBps`. This is **serialization of already-computed
   completion state** (the exit is computed in `MaybeCompletePosition` regardless) and
   is what makes the Step 4b exit-parity grading possible.
5. **Holdout fence**: emit no row with `SourceCloseTime ≥ AnalysisEndUtc`.

> Governance note: if (2) cannot be done without altering signal logic, that is a
> **scope-clarification trigger — route back to the pipeline**, *not* a license for
> Python to re-derive the AVWAP signal. The architecture forbids a Python signal
> oracle; control reconstruction (analysis) is the only Python-side rebuild allowed.

---

## Visualisations (3 / 3)

1. **cTrader-vs-Python effect forest** — per domain, EXP-029 PRIMARY `effect_bps`
   with 95% CI overlaid on EXP-028's `effect_bps`/CI, zero line marked. Answers:
   *do the two execution paths agree on effect and uncertainty?*
2. **Event-count / pyramid diagnostic** — per domain grouped bars: EXP-029 vs
   EXP-028 counts (total, bull/bear, pyramid/non-pyramid), with the ±10 % / ±20 %
   tolerance bands annotated. Answers: *is event membership aligned, or is a
   discrepancy driving any verdict difference?*
3. **Per-domain verdict / parity alignment table** (rendered figure) — for each
   domain: EXP-028 verdict, EXP-029 verdict, and the binding-gate booleans
   (verdict-match, magnitude-equivalent, counts ±10%, exit-parity, CI-overlap
   diagnostic), the per-domain band, the overall disposition, and the 5m signal-layer
   status in the title. Answers: *what is the parity outcome and which gate drove it?*

---

## Interpretation Guide (predeclared, before results exist)

- If, on **≥ 2 of 3** domains, all five binding gates hold (verdict match; magnitude
  equivalence; counts incl. pyramid within ±10 %; exit-parity; and — on 5m —
  signal-layer), the 5m signal-layer passes, and **no** domain is INCONSISTENT →
  **CONSISTENT**: EXP-028's Python-only `EVAL_SUPPORTED` is **upgraded to
  cTrader-confirmed**. The faithful AVWAP strategy has per-bar streaming evidence of
  event-level edge — entry signal, pyramid handling, and the executed completion code
  all graded — under the EXP-027 yardstick.
- If counts diverge > 20 % on a domain, a verdict differs **but CIs overlap**, a
  domain is underpowered, or the 5m signal-layer diverges without a hard inconsistency
  → **INCONCLUSIVE**: document the discrepancy and likely cause. The Python-only
  EXP-028 verdict **stands as-is** (neither upgraded nor downgraded).
- If on **≥ 1** domain there is a *powered* verdict conflict with non-overlapping CIs,
  a magnitude divergence beyond `max(2 bps, 50%·|ref|)`, **or** an exit-parity failure
  → **INCONSISTENT**: escalate. EXP-028's verdict is **downgraded to
  `EVAL_UNCONFIRMED`** pending root-cause; both the C# path and the Python re-analysis
  are investigated before any programme-level conclusion.
- A small per-event return / membership difference attributable to cTrader's own
  **1h/4h** feed (VAL-002: 5m exact, 1h/4h ≤ 1.83 bps) is **expected and benign** —
  absorbed by the ±10 % count tolerance; it is **not, on its own**, grounds for
  INCONSISTENT, and is *not* charged to the signal layer (reconciled only on 5m).

---

## Divergences To Avoid (guard → check mapping)

| # | Divergence (prior failure) | Guard in this plan | Verifiable check |
|---|----------------------------|--------------------|------------------|
| D1 | EXP-028 went Python-only, bypassing cTrader per-bar streaming | Step 1 runs the **corrected C#** on cTrader; estimand built from cTrader-emitted runs only; EXP-023 runs explicitly non-reusable | `run_metadata.json` records the cTrader run dirs + `analysis_end_utc`; ingest asserts the runs are the corrected (pyramid-inclusive, event-detail-bearing) emission |
| D2 | Framing/estimand mismatch (raw return vs excess) | Step 4 reconstructs the **same** symmetric own-exit matched-control **excess** as EXP-028; raw-return-vs-excess comparison explicitly forbidden | comparison is excess-vs-excess; `parity_comparison.csv` compares EXP-029 `paired_excess` effect to EXP-028 `effect_bps` (also an excess); reconciliation_bad must be 0 |
| D3 | Silent change to the calibrated method | Step 0 sha256 frozen-function guard; Step 5 imports the tail unchanged | `frozen_inference_hash == ea261b9ee0a8aca3`; `control_matching_equivalence_pass == true` |
| D4 | Python re-deriving the strategy signal as an oracle | Step 3 takes regime/anchor/targets/pyramid tag **from cTrader emission**; Python rebuilds only **controls** (analysis construct) | emission-schema assert (regime_id/targets present); no AVWAP state-machine call in the harness |
| D5 | Holdout leakage | `AnalysisEndUtc` fence in-robot + Python re-assertion (Step 2); local timebars not read for the estimand | per-cell `max(SourceCloseTime) < AnalysisEndUtc`; final 30% never loaded |
| D6 | Cross-feed bar-index transfer | Step 3 aligns by **timestamp** (`SourceCloseTime`), maps to per-cell index after sort | alignment guard hard-fails on missing/disagreeing trigger timestamps |
| D7 | Zero-baseline percentage inflation | report bps effects / absolute counts / CIs only; null excess is exactly 0 bps | no percentage-of-baseline metric in any output; non-recovered = non-finite, never 0 |
| D8 | Goalpost-moving | parity criteria, bands, and disposition predeclared here before any cTrader result is read | this section is frozen at Stage 4 approval |
| D9 | Confirmation-biased disposition that can only confirm EXP-028 (F01/F02) | binding exit-parity grading of the C# completion (Step 4b) + magnitude-equivalence gate with an INCONSISTENT divergence band (Step 6) | `exit_parity.csv` match_rate ≥ 0.99 per domain; `|Δeffect| > max(2 bps, 50%·|ref|)` ⇒ INCONSISTENT; an INCONSISTENT domain vetoes the overall upgrade |
| D10 | Count/effect drift mis-attributed to "benign feed coverage" (signal-layer divergence hidden) (F03) | 5m signal-layer reconciliation vs the EXP-020 substrate on the feed-exact domain (Step 3b); pyramid split inside the count gate (F04) | `signal_reconciliation.csv` ≥98% 5m trigger match + matched-target rel-diff ≤1e-3; `count_delta_pyramid ≤ 0.10` |
| D11 | Frozen-method identity asserted in prose but not in code (F05) | Step 0 hard-asserts `frozen_inference_hash == ea261b9ee0a8aca3` (== EXP-028's recorded hash) and aborts on mismatch | run aborts `FROZEN_INFERENCE_MISMATCH` if the hashes differ |

---

## Implementation Safety Constraints (for experiment-developer)

- **Temporal ordering**: sort every cell by `SourceCloseTime`; build indices only
  after sorting; never transfer indices across feeds/cells. Use `SourceCloseTime`
  for all alignment (chart-type / strategy-host events), never bar count.
- **Returns basis**: direction-signed **log** returns on cTrader `RealClose` only.
  No synthetic chart prices; no local-timebar returns in the estimand.
- **Denominators**: per-event unit; reportable events only (`MIN_REPORTABLE_EVENTS`
  / `MIN_DIRECTION_EVENTS` / `DOMAIN_MIN_INSTRUMENTS`). Controls per event require
  `≥ EM.MIN_CONTROLS`. No per-bar floor anywhere.
- **Zero-baseline**: null per-event excess is exactly 0 bps; rates (e.g. count
  ratios) use ratios with explicit denominators, never "% improvement over ~0".
  A non-recovered / unpowered domain effect is non-finite (`None`/NaN), never 0.
- **Imports unchanged**: load EXP-021/EXP-022 helpers and the EXP-027 tail by file
  path (the EXP-028 `_load_module` pattern); do **not** copy-edit their bodies. The
  frozen tail is additionally hash-guarded.
- **Vectorization discipline**: the control-completion `scan_lifetime` is genuinely
  sequential per event/control — keep it explicit (or reuse EXP-022's
  implementation unchanged). Vectorize only index selection / reconciliation, and
  only where causally equivalent (mirror EXP-028's per-cell vectorized
  reconciliation). Do not vectorize in a way that changes membership, ordering,
  denominators, or completion semantics.
- **Bounded memory / progress**: lazy/streamed parquet reads per cell; `tqdm` over
  the 12-cell outer loop and over placebo/bootstrap loops if any. No full-dataset
  materialization before the holdout fence.
- **Side-effect-free imports**: no directory creation / data load / plotting at
  import time; output dirs created only in orchestration (`main`).
- **Output dirs**: `python/experiments/EXP-029/results/` and `…/plots/`.

---

## Determinism & Seeds

- Fixed seeds via the `seed_for(EXPERIMENT_ID, role, domain, …)` convention used by
  EXP-027/028, for every bootstrap / permutation / (if any) placebo draw.
- cTrader generation is deterministic (in-engine, no random seed); reruns over the
  same fenced feed reproduce the same events.
- Re-running the harness on the same cTrader runs must reproduce every result CSV
  bit-for-bit; record seeds and `frozen_inference_hash` in `run_metadata.json`.

---

## Outputs

**Result CSVs** (`python/experiments/EXP-029/results/`):
- `event_level_results.csv` — per-domain EXP-029 PRIMARY (same columns as EXP-028).
- `parity_comparison.csv` — per-domain EXP-029 vs EXP-028: effects, CIs, CI-overlap
  (diagnostic), effect delta + magnitude-equivalent/divergent flags (F02), count deltas
  (total / bull / bear / **pyramid**, F04), exit-parity + signal-layer booleans, the
  gate booleans, and the per-domain band.
- `event_diagnostics.csv` — per-domain counts, direction balance, pyramid split,
  reportable instruments.
- `exit_parity.csv` (binding, F01) — per-domain C#-executed vs Python-scanned
  completion: n_events, n_matched, match_rate, bar/reason/bps mismatch counts, max bps
  discrepancy, pass/fail. (Replaces the old coarse `exit_alignment.csv`.)
- `signal_reconciliation.csv` (binding on 5m, F03) — per-instrument 5m C# vs EXP-020
  trigger-set match fraction, matched frozen-target rel-diffs, pass/fail.
- `equity_companion.csv` — Step 7c exposure-matched advantage (diagnostic).
- `run_metadata.json` — `overall_parity_disposition`
  (`CONSISTENT`/`INCONCLUSIVE`/`INCONSISTENT`), per-domain bands, `frozen_inference_hash`
  (hard-asserted == `ea261b9ee0a8aca3`, F05), `control_matching_equivalence_pass`,
  `exit_parity_ok_per_domain` + `exit_parity_match_rate` (F01), `signal_layer_5m_ok`
  (F03), `exp028_pyramid_per_domain` (F04), `agreement_margins` (predeclared F01/F02/F03
  thresholds), dependency states, `analysis_end_per_instrument`, per-cell row counts +
  max `SourceCloseTime`, `pyramids_included = true`, pyramid split, seeds, parameters,
  and the EXP-028 status consequence (upgrade/stand/downgrade).

**Plots** (`python/experiments/EXP-029/plots/`): the 3 visualisations above.

---

## Complexity Check

- **Statistical tests: 2–3 / 3** — (1) regime-cluster bootstrap CI; (2) stratified
  sign-permutation + Holm; (3) the parity comparison metric (reuses 1–2's machinery
  and EXP-028's stored CIs; no new estimator). The frozen EXP-027 tail is **reused,
  not new**.
- **Visualisations: 3 / 3** — effect forest; count/pyramid diagnostic; verdict /
  parity alignment table.
- **New code modules: 1 / 1** — `python/experiments/EXP-029/code/run_experiment.py`
  (plus a local hash-verified copy of `event_method.py`, and imported-by-path reuse
  of EXP-021/022 helpers — no new shared `python/src/xen/` module). The C#
  pyramid-position + serialization correction is in `AvwapBounceModel.cs` (within
  scope's allowance).

Within budget on all three axes.
