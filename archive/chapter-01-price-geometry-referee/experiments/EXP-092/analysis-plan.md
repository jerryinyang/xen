# Analysis Plan: Experiment EXP-092

**Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT; 1h + 4h survivors) → hash-pinned candidate set + Holm rule**

Phase 021 · `CF-MR-001` · `HYP-002` · TRAIN-only · 0 counted TEST reads · 0 slots · holdout sealed.
Governing D0: `D0-predeclarations.md` §D6/4b + §D7; `D0-amendment-003` (cost), `-004`/`-005` (4h). Scope:
[`scope.md`](scope.md).

## Objective

For the **sole surviving exit EXIT-RCT** (EXIT-ERT + 4 conventional arms died at the EXP-091/094 screen),
determine **which of the 11 carried `(instrument, domain)` cells** (5×1h from EXP-091, 6×4h from EXP-094)
reach a TRAIN-only **`SEQUENCE_PASS`** under the frozen rule — net per-event expectancy one-sided lower bound
`net ci_low_1s > 0` at α=0.05 (Z=1.645, moving-block bootstrap), power-confirmed by the cell's EXP-090/094
finite MDE — and emit the **hash-pinned candidate set (sha256) + the sized phase Holm rule** for the EXP-093
counted TEST read. This is the candidate-freezing step (EXP-034/083 precedent), **not** an edge claim or a
TEST confirmation; it is **necessary-but-not-sufficient** for TEST and adjudicates no G-021 verdict.

No new statistic is introduced — the binding gate is the **same net lower bound** validated in EXP-090 and
applied in EXP-091/094 (D0 §D4 ⇒ no bite-check). The analysis is deliberately a faithful re-derivation on the
carried cells plus the hash-pin/Holm freeze, not a new modeling exercise.

## Methodology

### Step 1: Resolve real EXIT-RCT exits + cost overlay on the 11 carried cells (descriptive substrate)

- **Method**: verbatim reuse of the EXP-090 substrate (`build_cell_context`, `resolve_arm`/RCT, the 1-minute
  intrabar fill engine, `net_return_atr`) → per-cell resolved-event **gross** ATR(14) returns on real OHLC;
  overlay the frozen `D0-amendment-003` conservative cost (`event_costs`/`holding_days`, `RT_i=4·c_i`, `F=0`)
  → per-event **net** series. 4h cells patch `DOMAINS["4h"]=240` exactly as EXP-094.
- **Why this method**: the substrate is already validated (EXP-090 readiness PASS; EXP-091/094 audit PASS);
  re-using it byte-for-byte guarantees the candidate set is built on the identical entry/exit/fill/cost
  machinery the screen used. No reimplementation risk.
- **Simpler alternative considered**: reading EXP-091/094's already-written `screen_per_cell_arm.csv` net
  bounds directly. Rejected — EXP-092 must **own** a deterministic, hash-pinned re-derivation under its own
  fixed seeds so the pinned candidate set is reproducible from EXP-092 alone (the EXP-093 hand-off artifact),
  not a transcription of two upstream files.
- **Assumptions**: real-price returns (no synthetic prices); causal 1m fills clipped at the TRAIN edge by
  timestamp; resolved-event denominator. All hold for time-ordered data (the engine is the EXP-090-audited
  causal one).
- **Expected output**: per-cell `{n_events, n_resolved, resolved_frac, tie_break_frac, terminal_mix,
  holding_days_mean, gross_mean/median, net_mean/median}` for EXIT-RCT (the 11 carried cells).

### Step 2: Binding per-cell sequence test — net one-sided lower bound vs 0 (the 1 binding test)

- **Method**: **moving-block bootstrap** of the per-event net series → one-sided 95% lower bound
  `net ci_low_1s` (`xen.ass.moving_block_bootstrap_cis`, `n_boot=10_000`, `alpha=0.10` ⇒ 5th-pct lower =
  Z=1.645; seeds fixed via `seed_for("EXP-092", instrument, domain, "RCT", "net")`). **`SEQUENCE_PASS` iff
  `net ci_low_1s > 0` AND power-confirmed** (finite EXP-090/094 MDE — satisfied for all 11 carried members by
  construction).
- **Why this method**: the programme's non-parametric, autocorrelation-respecting interval for a
  per-event-expectancy lower bound on overlapping/time-ordered trade returns; the frozen binding estimator of
  EXP-090–094 (catalog: Bootstrap CI, ≥10k resamples). The moving block preserves the serial dependence that
  an i.i.d. bootstrap or a t-interval would understate.
- **Simpler alternative considered**: a one-sample t-interval / Mann-Whitney on the net series. Rejected —
  assumes normality/independence the catalog flags as academic-finance pitfalls on overlapping trade returns;
  and it would deviate from the frozen estimator (goalpost-moving). The moving-block bootstrap is the minimal
  sufficient method already ratified.
- **Assumptions**: exchangeability of blocks under resampling; block length from `xen.ass.default_block_length`
  (the EXP-090/091/094 convention). Fits time-ordered financial returns; this is exactly the estimator the
  referee calibration certified.
- **Expected output**: per-cell `net_ci_low`, `SEQUENCE_PASS` boolean; the `SEQUENCE_PASS` cell set.

### Step 3: Hash-pin the candidate set + fix the phase Holm rule (the EXP-093 hand-off)

- **Method**: collect the `SEQUENCE_PASS` cells, order them deterministically by `net_ci_low` (descending;
  ties broken by instrument-domain string) → write `candidate_set.csv`; compute its **sha256** over a
  canonical serialization (sorted cells + the binding fields). Fix the **phase Holm rule** descriptor:
  Holm-Bonferroni over the one-sided TEST p-values of the cells EXP-093 carries, **sized to the carried-set
  cardinality** (the cardinality is recorded; the exact ≤1–2-per-exit/domain subset is selected at EXP-093's
  D0 from this pinned set — not here).
- **Why this method**: the EXP-034/083 freeze-before-TEST discipline — pinning the set + multiplicity rule
  *before* any TEST row is read is the anti-goalpost-moving control. SHA-256 is the programme's standard
  provenance pin.
- **Simpler alternative considered**: leaving the candidate set unhashed / Holm rule implicit. Rejected — the
  hash-pin is explicitly required by D0 §D6/4b and G-021 §3.3 ("hash-pinned (sha256) … fixed before the TEST
  read").
- **Assumptions**: none beyond a stable canonical serialization (sorted, fixed field order).
- **Expected output**: `candidate_set.csv` + `candidate_set_sha256`, `holm_rule` descriptor (family size,
  α=0.05 one-sided, margin = per-cell EXP-090/094 MDE) in `run_metadata.json`.

### Step 4: Descriptive margin pre-read + robustness companions (non-binding)

- **Method**: per cell, the **EXP-093 margin pre-read** — `net_ci_low > margin?` (margin = EXP-090/094 MDE:
  1h 0.0125, 4h 0.025) — flagging cells that `SEQUENCE_PASS` but would **fail the EXP-093 margin condition**
  (a-priori known fragile cell **GBPUSD-1h**, EXP-091 `net_ci_low≈0.0043 < 0.0125`); the mean-vs-median split
  per cell (median-fragile on 3/5 1h cells; all 6 4h members mean-AND-median positive = robust core); the
  realized counts, fill-rate, tie-break incidence, terminal mix.
- **Why this method**: gives EXP-093's D0 the mechanical inputs to pick the smallest-defensible carried subset
  (the robust mean-AND-median, margin-clearing cells) without EXP-092 itself making that selection.
- **Simpler alternative considered**: omitting the margin pre-read. Rejected — without it EXP-093 cell
  selection would lack a recorded, pre-TEST basis (researcher-degrees-of-freedom risk).
- **Assumptions**: descriptive only; never gates `SEQUENCE_PASS`.
- **Expected output**: `margin_preread.csv` (per cell: `net_ci_low`, `margin`, `clears_margin`, `net_mean`,
  `net_median`, `mean_and_median_pos`, `n_resolved`).

### Step 5: Determinism replay (D9)

- **Method**: re-run the full pipeline for **one 1h + one 4h** carried cell (e.g. USTEC-1h, EURUSD-4h); assert
  `net_ci_low`, `SEQUENCE_PASS`, and the **candidate-set sha256** are byte-identical on the second pass.
- **Why this method**: the programme determinism invariant; a candidate set that does not reproduce cannot be
  pinned for a one-shot TEST.
- **Expected output**: `determinism_pass` boolean + cells checked in `run_metadata.json`.

## Visualisations (≤ 4)

1. **Per-cell `net_ci_low` vs 0 and vs margin** (forest/bar, 1h + 4h split) — shows each carried cell's binding
   lower bound, the break-even line (0), and the MDE margin line; the binding `SEQUENCE_PASS` decision and the
   margin pre-read in one view.
2. **`SEQUENCE_PASS` candidate map** (instrument × domain grid) — which carried cells pass / fail the sequence;
   the hash-pinned set at a glance.
3. **Mean-vs-median per cell** (paired bar) — surfaces the median-fragile 1h cells vs the mean-AND-median 4h
   robust core (the EXP-093 selection signal).
4. **Robustness ranking** (cells ordered by `net_ci_low`, annotated with margin-clear + mean/median flags) —
   the descending order that defines the pinned set's ranking and feeds EXP-093 smallest-defensible selection.

All plots are built from the collected per-cell summaries (no heavy reloads / no chart regeneration for
plotting).

## Interpretation Guide (pre-defined, before results)

- If **≥1 carried cell** has `net_ci_low > 0` (power-confirmed) → it is `SEQUENCE_PASS`; the non-empty
  hash-pinned candidate set + sized Holm rule are emitted → **`SEQUENCE_DELIVERED`**, Phase 021 proceeds to
  EXP-093. (Expected: the carried cells net-cleared upstream, so most/all reproduce `SEQUENCE_PASS` under
  EXP-092's own seeds.)
- If a cell `SEQUENCE_PASS`es **but** `net_ci_low ≤ margin` → it is carried in the pinned set but **flagged
  margin-fragile** (would fail the EXP-093 margin condition); EXP-093's D0 should prefer margin-clearing,
  mean-AND-median-positive cells. This is interpretation, not a re-gate.
- If a cell flips `net_ci_low ≤ 0` under EXP-092's independent bootstrap seeds (boundary cell, GBPUSD-1h the
  candidate) → `SEQUENCE_FAIL`, excluded from the pinned set, **disclosed** as a boundary-fragility finding
  (not an experiment failure).
- If **no** carried cell reaches `SEQUENCE_PASS` → **`SEQUENCE_EMPTY`**: no candidate to confirm, routes G-021
  toward NOT_TRADABLE at 0 TEST reads (not expected).
- A cell with `< 2` resolved events (no computable bound) → `SEQUENCE_INDETERMINATE`, excluded with record
  (not expected — all carried members had ≥3835 resolved events upstream).

The verdict is **mechanical and predeclared**; only the explanation is written after results.

## Implementation safety constraints (for experiment-developer)

- **Holdout**: never load the final-30% global holdout (incl. its 1m bars). TRAIN sub-split only,
  `[0, int(analysis_rows·0.7))`; the 1m fill walk clips at the TRAIN edge **by timestamp** (never by 1m index).
- **Temporal alignment**: domain→1m mapping by `CloseTime`/`SourceCloseTime`, never bar count; causal
  order-of-touch with the frozen conservative adverse-first tie-break; only bars at/after entry.
- **Real prices only**: gross/net from real OHLC in ATR(14) units; no HA/Renko/synthetic prices.
- **Frozen, no tuning**: RSI 2/10/90, EXIT-RCT target, 2.0×ATR stop, MR-tempo cap, the `D0-amendment-003`
  cost table, `Z=1.645`, `n_boot=10_000` — all frozen; do not mutate `xen.capgeo_cost.COST_CONSTANTS`
  (Phase-018 integrity); pass the Phase-021 `RT_i`/`F=0` locally.
- **Denominators / zero-baseline**: denominator = resolved events; finite-guard every bound (NaN/degenerate
  surfaced, never coerced to a pass); binding comparison is an additive lower bound vs 0, not a percent vs a
  zero baseline.
- **Determinism / seeds**: all seeds via `seed_for("EXP-092", …)`; byte-identical second pass incl. the
  bootstrap stream and the candidate-set sha256.
- **Bounded iteration / progress**: outer loop over 11 cells with `tqdm`; the bootstrap is the only heavy
  inner work (10k resamples per cell) — vectorized inside `xen.ass`, not a Python row loop. Plotting reuses
  collected summaries (no reload). Import-time side effects: none (dirs created only in orchestration).
- **Vectorization discipline**: the 1m intrabar walk stays the EXP-090 causal sequential engine (do not
  re-vectorize it); only aggregation/bootstrap are vectorized.

## Complexity Check

- Statistical tests: **1** binding (per-cell net lower bound) / budget 1 (design §5: "EXP-092 1 (sequence)"). ✓
- Visualisations: **4** / budget ≤ 4. ✓
- New modules: **0** / budget 0 (reuse EXP-090 substrate + `xen.*`; orchestration + hash-pin helper only). ✓
