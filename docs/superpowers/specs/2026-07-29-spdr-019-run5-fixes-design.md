# SPDR-019 QA Run-5 Fix Design

## Goal

Close every finding in `python/experiments/SPDR-019/qa-review.md` Run 5 without inventing
sample counts, weakening an integrity check, or touching TEST/holdout data.

Implementation is split into two gates:

1. **Population preflight:** may be authored and run before payoff code. It emits only
   payoff-blind population/count artifacts.
2. **Payoff implementation:** remains blocked until `expected_resolution.json` exists,
   is committed, and passes fresh QA.

The existing SPDR-020 additions to `xen.resolution_basis` and its tests are shared dirty-worktree
changes. Preserve them and extend their interfaces compatibly.

## Design corrections

### Tripwires

Replace aggregate-effect phrases such as “materially change” with structural, executable rules.

- **Causal-state canary:** precompute the legal and `[+1]` state streams. Hard-pass requires:
  the shifted stream is an exact one-row shift of the legal stream; at least one eligible row
  changes state/selection; observed retention and changed-row count equal the independently
  generated preflight artifact. `log R` differences remain informative because a value threshold
  would turn a validity check into an effect gate.
- **Fill-resolution canary:** generate exact event IDs whose fills differ under decision-clock
  OHLC versus M1 resolution, and exact event IDs where favourable precedence differs from adverse
  precedence. Hard-pass requires the emitted counts and IDs to match the preflight artifact and
  every favourable-precedence fill to be mechanically no worse for the position. Aggregate
  `log R` differences remain informative.

Both checks bind to named fields in `integrity_selfcheck.json`; no developer-chosen magnitude is
allowed.

### Comparator

ATR20 normalises `deltaThreshold` only. Every L4 unmodulated boundary uses the per-symbol
TRAIN-median of the same Parkinson-EWMA `ŝ` used by the modulated arm. Add a hard assertion that
estimator, unit, clock, horizon scaling, and multiplier match; only constant-versus-conditional
`ŝ` may differ.

### Block bootstrap

Copy SPDR-018 §6.2 exactly:

- aggregate per-calendar-day sufficient statistics;
- day-block sweep `{1,3,7}`;
- minimum one day / 24 H1 bars;
- min/max envelope across blocks × five seeds;
- `xen.evaluation.block_bootstrap_ci`;
- effective block capped `< n`;
- emit per-seed bound spreads and per-block sensitivity.

The full rule string is pinned in both the design and resolution-basis JSON.

## Resolution artifacts

### Corrected parent basis

`resolution_basis.json` is regenerated from SPDR-018 **arm C only**. It records:

- input filter and source hash;
- input, retained, and excluded row counts, with exclusions by reason;
- `cells` and `distinct_n` per band;
- horizon counts and horizon-specific `c` summaries;
- the complete SPDR-018 bootstrap rule.

The design must report the measured 15k+ thinness (26 cells / 8 distinct `n`) and qualify the
non-flat horizon medians rather than claim global flatness.

### Payoff-blind population preflight

Add `python/experiments/SPDR-019/preflight_code/count_populations.py`.

Allowed inputs:

- fenced TRAIN timestamps and OHLC needed to form entries, fills, state labels, and episode
  lifecycles;
- frozen universe, clocks, deltas, layer/device grid, and fill rules;
- corrected `resolution_basis.json`.

The preflight may follow future TRAIN prices only as required to determine fill eligibility,
episode exit time, and suppression membership. It must not compute or persist return sign or
magnitude. Its pure entry/fill/lifecycle functions become the implementation's shared source after
fresh QA; payoff code must import them rather than create a second resolver.

Forbidden outputs and persisted intermediates:

- signed returns, exit P&L, `p`, `W`, `L`, `W/L`, `log R`, cost-adjusted effects, CIs, bands,
  or any outcome ranking.

The preflight writes `results/population_preflight.parquet` at the exact reporting grain:
clock × delta × layer/device cell × symbol/pooled × band. It includes expected episode count,
signal count, fill count, suppression count, and the structural tripwire event IDs/counts.

It also writes an attestation containing:

- TRAIN fence and zero TEST/holdout reads;
- allowed output-column list and forbidden-column scan;
- source, config, universe, code, and catalog hashes;
- generation timestamp.

### Expected resolution

Extend `xen.resolution_basis` compatibly with SPDR-020 so it consumes only the preflight count
artifact plus the corrected basis. It must:

- reject payoff/outcome columns;
- expand every declared SPDR-019 stratum;
- reject missing strata and placeholder statuses;
- preserve genuine zero-count strata as numeric zero with an explicit reason;
- compute expected `mde50` only for positive expected `n`;
- write deterministic JSON with input hashes and timestamp.

`results/expected_resolution.json` must exist and be committed before payoff-bearing
`screen_code/` may be authored. Fresh QA reviews the artifact and preflight attestation.

## B-5 and reporting

- Every inference and aggregate uses **realised** CI/MDE/resolution only.
- Predeclared-versus-realised resolution is a calibration audit; report the complete signed
  discrepancy distribution. It never admits, drops, labels, or ranks a cell.
- A pessimistic forecast is described as evidence waste, not as the same false-negative mechanism
  as an optimistic forecast.
- Phase-(b) reports the fraction above **all six** ladder rungs, never only 0.10.
- `mde50/mde80/mde95` remain descriptive curve coordinates, not gates.

## Ledger and artifact completeness

- Keep the correct tally: 4 looser / 7 tighter / 5 neutral.
- Replace stale AMENDMENT-11 references with superseding AMENDMENT-15.
- Correct AMENDMENT-10: the change adds 1 hour and drops 24 hours; 20 is not beyond 24.
- Derive nominal global-null “above mirror” counts from the exact emitted row counts in the
  preflight (`0.025 × rows`) by reporting tier, alongside an empirical battery estimate where
  available. This is disclosure only.
- Add collapse fractions to applicable controls.
- Map span fields, both resolution JSONs, preflight artifacts, and shared module in §15.
- Disclose the per-symbol row expansion.
- State G1/G2 holds in hours.

## Tests

Follow test-first development.

1. Shared resolution tests fail until:
   - arm-C filtering and exclusion accounting are emitted;
   - horizon summaries are present;
   - payoff columns are rejected;
   - incomplete/placeholder SPDR-019 strata are rejected;
   - deterministic hashes and genuine zero-count handling work.
2. Preflight tests use synthetic bars and fail until:
   - only TRAIN rows are admitted;
   - every declared cell is counted;
   - forbidden outcome columns are absent;
   - structural tripwire IDs/counts are deterministic.
3. Design-contract tests fail until the comparator, full block rule, all-rung phase-(b)
   distribution, ledger corrections, and artifact mappings are present.
4. Run focused tests, then the existing `test_resolution_basis.py` suite and relevant shared
   evaluation tests.

## Success criteria

- All Run-5 findings R5-01 through R5-09 are addressed.
- Corrected `resolution_basis.json` reproduces arm-C 15k+ = 26 cells / 8 distinct `n`.
- The preflight emits no outcome-bearing column and reads no TEST/holdout data.
- `expected_resolution.json` contains every declared stratum, no placeholders, and pinned hashes.
- Fresh QA can authorise payoff implementation; execution remains separately blocked by the
  registered C6 trigger conflict and unsigned reflection decision.
