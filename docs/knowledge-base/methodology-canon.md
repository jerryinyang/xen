# Methodology Canon — What Earned Its Keep (and What Didn't)

Distilled from Chapter 01 reflections and retrospectives. These are the methods to reach for,
and the traps to avoid, on any new experiment.

## Productive methodology (use these)

- **Availability-screen-first.** Before committing a candidate slot, run a cheap TRAIN-only
  Δ-over-matched-random availability read (EXP-081 clone). The programme's recurring mistake
  was measuring availability *last*. Availability is now the **selection gate**, measured
  first, family-agnostically.
- **Matched random controls.** Compare a conditioned entry against a within-substrate /
  within-instrument random-entry control with matched count and regime. Edge = Δ-over-random,
  not raw outcome. (EXP-047, EXP-081, EXP-021 control-excess.)
- **Multiplicity-adjusted admission gate.** When screening many axes/cells, gate admission on
  a **permuted-axis / shuffled-label null at the realized cell count** (the EXP-077 / `m_cell`
  pattern), not a single-axis band. Cross-sectional screens manufacture the most cells and are
  the worst multiplicity offenders. The admission decision is the high-stakes one; ranking
  among survivors is secondary.
- **Per-stratum adjudication, never pool-as-verdict.** Emit the binding verdict per
  domain/instrument/cell. A pooled/equal-weight headline is a **disclosure**, not a verdict,
  until cross-stratum homogeneity is itself shown. (LESSON-001; EXP-076 C1 collapsed-`.all()`
  precedent.) One high-cost instrument can veto a domain; one separating cell can be masked by
  a pooled null.
- **Inverted-inference predeclaration.** Freeze the kill/pass thresholds and the binding
  estimand *before* any outcome contact (at the phase G0/D0). A near-miss cannot be argued up
  after the fact. Show routing invariant across a pre-registered sensitivity band.
- **Two-speed gating + one-shot TEST.** TRAIN-only characterisation with mechanical selection
  rules; lenient G1 to continue exploring; strict G2 to spend a scarce TEST read. Hash-pin the
  frozen selection before any TEST row is read.
- **File-drawer + test-read discipline.** Register every candidate/variant/branch before
  measuring it; keep refuted/blocked/inconclusive items in the ledger (never delete or rename).
  Hard cap **2 lifetime counted reads per TEST stratum**; portfolio-aggregate reads are
  disclosures, not counted reads. A defect found later does **not** refund a spent read.
- **Cost realism is binding, early.** Charge conservative round-trip + holding-time financing
  on the binding leg. Many gross-positive edges die net (AVWAP, capgeo). A gross "pass" is not
  a tradable edge.
- **Shape-aware reads.** If an effect can be tail/bimodal/asymmetric, predeclare a shape-aware
  read alongside the location guard, and check whether the binding gate can even *see* the
  effect's shape. A location/consistency gate is structurally blind to a tail-only separator.
- **Execution-causality convention (bar-open + open-to-open).** Decide at the action bar's
  **open**, conditioned only on previous **confirmed (closed)** bars (`≤ t-1`) — never the forming
  bar's own OHLC. Measure returns **open-to-open**, never open-to-close (`OnClose` is not
  executable live). This generalizes the L-01 `rct[di]→[di-1]` fix into a standing rule the
  cTrader engine enforces by construction. See [lessons-and-amendments.md](lessons-and-amendments.md)
  L-01/L-02.

## Futile / low-yield methodology (don't repeat)

- **Measuring availability last** — building a whole family around a pattern, then discovering
  the move was never conditionally available. The single biggest waste of the chapter.
- **Tuning the downstream stack on a dead entry** — exits, capture geometry, conditioning,
  anchors, sizing were all exhausted on single-series directional price-pattern entries with no
  binding lever found (EXP-084 exit-invariance, 0/11 arms positive OOS). Sizing is a near-global
  rescale: it amplifies an edge, it cannot create one.
- **Scoring a sparse event signal against a per-bar floor** — the EXP-023 dilution artifact.
  Match the evaluation vehicle to the signal's activity rate (event-level method for sparse).
- **Pooling heterogeneous cells into one PASS/FAIL** — masks the binding stratum (EXP-076 C1;
  EXP-085 all-NET_POS were low-n deferred cells while the one powered cell was inconclusive).
- **Vectorised look-ahead in a shared outcome module** — the L-01 failure. See
  [lessons-and-amendments.md](lessons-and-amendments.md); the Chapter 02 structural fix is
  cTrader-primary execution + a causal-provenance audit pass.

## Chapter 02 additions (earned 2026-06-27 → 2026-07-09)

- **SPDR speed-run screening lane.** Before any engine run or estimand gate, a candidate can be
  screened TRAIN-only in Python (0 engine runs, 0 counted reads, 0 slots): blind multi-leg
  analyst passes, ref-arm replication, control battery. Cheap WORTH_EXPLORING/KILL routing —
  CF-HTFDI-001 was registered and retired for ~0 budget. Lane spec: `docs/references/spdr-lane.md`.
- **Unit pin at every screen→graduation seam (L-21).** A dimensionless screen effect becomes a
  money claim only through an explicit unit derivation (which ATR, which timeframe, which lag),
  re-computed — not asserted — at graduation, plus a **money-unit floor** (bps/trade vs the cost
  stack). The 4.1× EXP-025 inflation is the canonical failure.
- **Spread is a verdict leg on 0-commission instruments (L-22).** A commission-only cost band
  never binds where commission is 0; the SUPPORTED tier must price spread.
- **Amendment-direction ledger (L-23).** Every pre-measurement amendment declares looser/tighter
  and increments a running count; re-derive the joint false-qualification rate at the final gate.
- **Seed batteries, never single-draw controls (L-19/L-20).** One random twin is one draw; kill
  tests need ex-ante seed batteries and percentile reads. The CI machinery itself is hardened
  (block sweep, robust stat) after INFR-004 killed a zero-width small-n bootstrap CI.
- **Block ≥ dependence horizon on overlapping estimands.** Per-bar forward returns at hold H
  overlap; bootstrap blocks < H under-cover (the Phase-010 correction). Verify the computed
  estimand matches its label before reading CIs.
- **Symmetric selection rules.** No hard single-cell vetoes; median-smooth qualification in both
  directions (SEL-NEIGHBOR amendment) — outlier robustness must not be one-sided.
- **Exposure-honest comparison.** Never kill a part-time strategy on raw B&H comparison;
  normalize by average and peak exposure time.
- **Equal-info fade tiering.** On a null base, a negative is an equal-information fade signal —
  but tier such threads by replication strength; controls graduate as **apparatus**, not candidates.
- **Native orders for limit strategies.** StrategyHost fills on aggregated-bar OHLC; any
  limit/stop capture claim needs native cTrader orders with m1 fills (EXP-013 lesson,
  Mode=NativeOrders).
- **Event-mass match.** A re-attributed trigger must reproduce the field object's event cadence,
  or the thesis strata are UNPOWERED by construction (EXP-015).
- **Controlled thesis-shopping is the model.** Exploration from refuted hypotheses is allowed —
  gate with registration + multiplicity, never dismiss by origin.

## Chapter 03 additions (XENA lane + calibration discipline)

- **Portfolio-selection adjudication (XENA) is the default route for family verdicts** —
  search + certify over a candidate universe, no per-candidate A/B. Binding binder + pins:
  [evaluation-framework.md](evaluation-framework.md) chapter-03 section.
- **Check gross bps/trade against breakeven spread BEFORE search** (XENA-003). A universe
  whose gross edge sits within ~3× the round-trip spread is undecidable on costless/coarse
  data — the search will maximize a print artifact. Route to finer data or park.
- **Calibrate α with sized nulls.** e2e α̂ SE ≈ 0.218/√n_null: scale n_null (not candidates or
  budget) to the resolution the gate needs; predeclare n; no optional stopping; gate on the
  point α̂.
- **Design/confirm bank split, then binder-FORM pivots.** Estimator knob-turning inside one
  form converges slowly or not at all (P3→P3d left a ~3pp selection residual three rounds
  running); prevent the defect **by construction** (sample-split + embargo) instead of
  correcting it post-hoc.
- **Sparse-calendar resampling resamples legs, not bars** — bar-level blocks on a sparse trade
  calendar destroy the leg structure the statistic lives on.
- **Objectives must carry the binding cost** (L-26). A costless cadence-maximizing objective
  structurally penalizes any filter/conditioning thesis; net cost is a verdict leg inside the
  frozen procedure, never informational-only.

## Statistical defaults

Non-parametric / empirical by default (block / stationary / moving-block bootstrap;
permutation nulls). No normality, stationarity, i.i.d., or constant-vol assumptions. Block
length estimated on TRAIN only. When permuting for a null, **block-permute returns** — do not
rotate the price path with a mean statistic (cross-regime variance blowup). Wilson intervals
for rates. Holm across the binding family. Report effect sizes and `ci_low`, not just p.
