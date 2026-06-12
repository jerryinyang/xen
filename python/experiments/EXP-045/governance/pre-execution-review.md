# Pre-Execution Governance Review — EXP-045

**Date:** 2026-06-11
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, `code/cell_exits.py`
**Phase alignment:** Phase 011 design §5.4/§6 (Track B exit training) under
**G1 CLOSED** (adjudication 2 of 2, 2026-06-11) — the 37-cell COVERED grid is
exactly the authorized Track B population; registered in the multiplicity
registry (`CF-AVWAP-001/PI-EXIT` — EXP-045, Track B, 0 slots, 0 TEST reads).
No misalignment.

## Core constraints

- **Simplicity:** the experiment is a verbatim operationalization of the
  G0-frozen design — two families, one deterministic exit scan, a 3-point
  stability mean, one bootstrap SE per cell×family. No inference machinery
  beyond the predeclared SE; no p-values as decision objects. The few
  operational details the design left open (forced-close handling, SE
  definition, tie-breaks, split-half minima) are fixed in the scope/plan
  pre-data, each with a one-line rationale. PASS.
- **No academic-finance pitfalls:** no normality/stationarity/i.i.d.
  assumptions; cluster bootstrap SE; split-half stability check on
  chronological halves. PASS.
- **Strict scoping:** single question (per-cell tunability/selection +
  membership + G2 readout); boundaries explicit (37 COVERED cells from the
  artifact chain, never hard-coded); deliverable-criterion success
  (TRAINING_DELIVERED); budget 2 tests / 5 plots / 1 module, met exactly.
  **No frozen constant is tuned, re-derived, or extended** — grids,
  k, SE multipliers, P4 floor, and the P2 cost table (incl. the EURUSD 3.0
  RT correction) are transcribed constants. PASS.
- **OOS holdout:** F01 file-order TRAIN slice (lazy scan, column projection,
  `head(train_rows)`), EXP-043 source-identity binding (file name, row
  counts, TRAIN-end timestamp), chronology asserted post-collect. TEST and
  the final-30% holdout never enter the scan engine; membership is decided
  with zero TEST contact. PASS.
- **Look-ahead:** exits scan strictly forward from the trigger over
  completed closes; AVWAP/spread/targets frozen at trigger; the
  trend-change bar is the *confirmation* bar of the next opposite regime
  (searchsorted strictly after the trigger). FH exits are index offsets with
  no path information. PASS.
- **Real-price discipline:** all returns are direction-signed log bps on
  real domain `Close`; costs and financing per the frozen P2 model; no
  synthetic prices. PASS.
- **Safe optimization:** the FH leg's vectorization is causally trivial
  (fixed offsets). The MAD ladder scan (one pass per event over a monotone
  target ladder) is guarded by `verify_mad_scan()` — 200 randomized
  fixtures against the naive per-target reference, raising before any cell
  runs; both passed at review. The split-half θ\* reuses the per-event nets
  (subset of events, not a path recompute) exactly as the plan predeclares.
  PASS.
- **No silent drops:** forced-close events flagged and included; >20%
  forced fraction recorded as a per-grid-point disclosure; split-half
  failures fail closed with named reasons; gate failures hard-fail. PASS.
- **Determinism:** the only stochastic step (bootstrap SE) is seeded via
  `seed_for`; two predeclared replay cells (GBPUSD-1h, JP225-4h — both in
  the COVERED set) fully re-run and compared row-identically on both the
  selection and curve tables; the verdict binds determinism. PASS.
- **Selection-bias honesty:** the plan predeclares the winner's-curse caveat
  on TRAIN net at θ\* and forbids reporting TRAIN means as tradability
  evidence — the binding inference is Track C's single TEST read. PASS.

## Artifact checks

- **scope.md:** exploratory question precise and measurable; mandatory
  holdout exclusion stated; denominators/zero-baseline section present;
  exit-family semantics fully specified (incl. no-stop rule, forced-close
  rule, financing convention matching EXP-033); complexity budget realistic.
  PASS.
- **analysis-plan.md:** each step carries why-this/simpler-alternative/
  assumptions; interpretation guide predeclared (TRAINING_DELIVERED;
  NON_TUNABLE/floor-fail as valid outcomes; the G2 readout explicitly a
  governance input, not an experiment verdict); three predeclared caveats
  (selection bias, forced-close compression, single-point SE). PASS.
- **code:** implements the plan exactly — grids {2,…,23}/{0.5,…,5.7}, k=1
  interior-only argmax with smaller-θ tie-break, 1×SE separation vs interior
  median, chronological split-half (odd event to the first half, <10 events
  fail-closed), P4 floor on the leading family, FH-wins family tie-break,
  G2 = ≥5 cells over ≥3 instruments. Typed, sectioned, docstringed; output
  dirs only in `main()`; `tqdm` with per-cell postfix; plots from bounded
  summary rows; per-instrument frame loaded once and freed; empty-membership
  CSV path handled. Both modules compile; fixtures pass. PASS.

Checked deviations: none. The endpoint rule is enforced structurally
(endpoints are never argmax-eligible) rather than detected post hoc — a
faithful implementation of the design's eligibility semantics, noted in
code. *(Superseded by Revision 1 A/F02: an explicit endpoint-dominance
check was added; eligibility alone left the declared failure mode
unreachable.)*

Computation estimate: 37 cells × (one O(bars) event scan + 8 FH gathers +
per-event bounded MAD ladder walks + 2×1000 cluster-bootstrap resamples over
≤266 events) plus a 2-cell replay — minutes, single machine; far below
EXP-044's budget.

## Verdict

```text
VERDICT: APPROVE
```

---

## Revision 1 — 2026-06-11 (pre-execution adversarial review; re-approved)

Two independent reviews (A: 6 findings, B: 5 findings) assessed before any
data contact. Dispositions:

**Code fixes applied (valid findings):**

- **A/F01 (Critical, confirmed)** — financing inflated 1000× by a
  timestamp-unit mismatch: `CloseTime` is `Datetime(ns)` (verified on the
  GBPUSD source and `aggregate_ohlc` output; 1h delta = 3.6e12), but the
  divisor assumed microseconds. Fixed: all time fields renamed to `*_ns`,
  divisor now `NS_PER_DAY = 86_400e9` (matching `xen.financing`), and a
  closed-form regression guard `verify_financing()` (1h hold at 1.2 bps/day
  must charge 0.05 bps) runs in `main()` before any cell. No results
  existed yet — caught pre-execution.
- **A/F02 (Major, valid)** — the declared `endpoint_argmax` failure mode was
  unreachable (endpoints were NaN'd out). The frozen design-§6 rule ("if the
  stability argmax lands on an endpoint, the family is non-tunable") is now
  implemented explicitly: endpoint stability is computed on truncated
  2-point neighbourhoods, and `endpoint_dominates()` (endpoint S strictly >
  every interior S) fails the family with reason `endpoint_argmax`, checked
  before all other tunability legs. Scope/plan updated to state the rule's
  operational reading; fixtures verify both the firing and non-firing cases.
- **A/F03 (Major, valid)** — the mandatory D0 P8 DE30 disclosure is now
  carried verbatim: a `disclosure` column on every row-level artifact
  (`exit_selection.csv`, `score_curves.csv`, `split_half.csv`,
  `membership.csv`), a `disclosures.DE30` field in `run_metadata.json`, and
  an annotation on the membership-map plot title.
- **A/F04 (Minor, valid)** — `split_half.csv` `agree` is now computed
  directly from the half/full positions (both halves populated and within
  ±1 step), independent of which failure reason bound first.
- **A/F05 (Minor, valid)** — `trend_change_lookup` now returns the sentinel
  `n_bars` (outside the bar range) for "no opposite confirmation", so a
  genuine trend-change exit on the final TRAIN bar is no longer flagged
  `forced_close`; `simulate_mad` flags forced only when TRAIN end is reached
  with no target and no in-range trend change. Fixtures cover sentinel,
  last-bar confirmation, and the strictly-after case.
- **A/F06 (Minor, valid)** — the determinism replay now hard-fails unless
  both predeclared cells are present in the COVERED grid before replaying;
  the replayed keys were already recorded in `run_metadata.json`.

**Documentation fixes applied:**

- **B/F01 (valid, doc-only)** — the FH grid is now described as
  near-geometric (integer bars force ratios 1.33–1.50 around √2); the grid
  itself is G0-frozen and is not changed.
- **B/F02 (note option adopted)** — the plan now states the pipeline is
  structurally deterministic (seeded bootstrap is the only stochastic step),
  so the 2-cell replay is a wiring regression check. Expanding the replay to
  a per-family pair was **rejected**: which family wins is unknowable
  pre-data, and conditioning replay selection on it would be post hoc.
- **B/F03 (valid, doc-only)** — the strictly-after trend-change convention
  (a confirmation coinciding with the trigger bar does not exit the event)
  is now stated in the scope as the predeclared conservative reading.
- **B/F04 (note adopted)** — the plan now warns that raw per-θ means in
  `score_curves.csv` are unprotected arithmetic means for transparency and
  must not be read point-by-point in thin cells; an `interior` flag was
  added to the curve rows. A median companion column was **not** added —
  the stability plane and SE are the decision objects, and a second
  statistic invites informal re-ranking.
- **B/F05 (Info, note adopted)** — the interpretation guide now states the
  direction of the single-point-SE bias: the separation rule and P4 floor
  are conservative (S(θ*) has smaller sampling error than the per-event-mean
  SE yardstick).

Both modules recompile; all fixtures pass (MAD-scan equivalence ×200,
financing unit guard, endpoint dominance firing/non-firing, trend-change
sentinel/last-bar/coincident cases).

```text
VERDICT: APPROVE (Revision 1)
```
