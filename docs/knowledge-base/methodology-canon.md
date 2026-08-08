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
- **Unit pin at every screen→graduation seam (L-21; live core retained under INFR-022).** A
  dimensionless screen effect becomes a money claim only through an explicit unit derivation
  (which ATR, which timeframe, which lag), re-computed — not asserted — at graduation. The
  historical **money-unit floor** (bps/trade vs a cost stack) is **superseded-for-live-use by
  L-62** (zero-cost model): live money claims are gross, carry ZERO-COST-DISCLOSURE, and are
  never gated on a cost floor. The 4.1× EXP-025 inflation remains the canonical unit-pin failure.
- **Spread as a verdict leg on 0-commission instruments (L-22) — superseded-for-live-use
  (INFR-022 L-62).** Under the zero-cost model, spread/commission/swap are not charged and do
  not form a binding tradability tier; the historical L-22 lesson (commission-only bands never
  bind where commission is 0) remains true as *why* partial cost scopes were unsafe, not as a
  live requirement to price spread into every SUPPORTED read.
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
  [**superseded-for-live-use (INFR-022): the spread-scale routing and breakeven-spread
  pre-search check are retired (zero-cost model); the underlying lesson — a search can
  maximize a print artifact — survives via the fill-basis (print vs path) evidence read.**]
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
  frozen procedure, never informational-only. [**superseded-for-live-use (INFR-022): the
  net-cost-binding selection path is retired — selection is gross-only (`g_gross`); the CAL
  apparatus that measured it is bannered legacy.**]

## Chapter 04 additions (Nautilus/Bybit + signed-volume arc)

- **Validity is hard; value is an operator read.** Fence/provenance/reconciliation/leak-plant
  failures invalidate data. Significance, power, subset ranking and collapse magnitudes are
  report layers over all frozen arms, not machine verdicts. XENA-HTFCAP's top-1 hid the actual
  positive-gross cells.
- **Freeze one event set and emit all conditioning arms together.** Vol state, drift, beta,
  rank and signed volume should be columns on the same events. Read ordered layers from one
  artifact; if a layer fails, stop that branch—do not create a new mining run.
- **Matched random timing is the binding timing control.** A stable target quantile or a
  future-destroy pass is near-vacuous when unconditional matched times reproduce it. For
  volatility-window objects add matched random-entry and coin-flip/drift twins because
  destroying labels at actual event times preserves the volatility pedestal.
- **Count both tails and the null winner rate.** SPDR-008's 7 positive qualifiers looked like
  K≥3 until compared with 6.0 null-expected and 10 anti-monotone qualifiers. Require connected
  neighbourhoods, magnitude reproduction and sign-stable CONFIRM, not a positive-only census.
- **Breadth is not diversification.** A K-symbol subset can still be economically carried by
  one name. Report per-symbol census, leave-one-name-out behaviour, contribution concentration
  and overlap-aware portfolio uncertainty.
- **Separate detection resolution from economic hold.** Coarser bars reduced candidate supply
  from 95,836→9,497→2,974→640 in SPDR-009, but this does not prove finest is universally best.
  Detect at the finest *reliable* scale that preserves the event, then test the independently
  justified holding horizon; disclose outcome-availability conditioning.
- **Reproduction is not skill.** A reproduced statistic must also separate from its matched
  control and clear a valid money floor. Quantile stability alone is market characterisation.
- **Mechanism deletion means no threshold re-mining.** Once a powered marginal-value test says
  the signed transform adds nothing (S3/S9), do not tighten the same score until a winner appears.
- **Directional return sources may be the product.** Drift, beta and volatility clustering are
  controls when the claim is residual alpha; if the objective is a deployable return product,
  a risk-managed trend/volatility exposure is legitimate and must be benchmarked and costed
  honestly rather than automatically residualised away.

## Chapter 05 additions (structural decomposition + the estimand-capability rule)

- **Decompose the claim before testing it.** `CF-VOLDIR-001`'s whole value came from separating
  (A) is volatility modellable, (B) does direction have positive expectancy in bps, (C) capture
  geometry, (D) cost — so that failure was **diagnosable** rather than "markets empty". The
  chapter's answer ("the joint sits at break-even and 91–96% of the gap is cost") is only
  available because the terms were measured separately.
- **Write the identity down and let it constrain the search.**
  `E[net] = p·W − (1−p)·L − cost`, `p_be_net = (L+cost)/(W+L)`, `edge = p − p_be_net`. This is
  what showed the target is **not** `p > 0.5` (an edge exists at `p < 0.5` when `W > L`) — and it
  is also what made the mirror relation between `p` and `W/L` a checkable claim rather than an
  intuition.
- **Check whether the estimand can express the effect, before power.** The order is: *can this
  instrument see the thing at all* → *is the floor on the same scale as the effect* → *is n
  sufficient*. Skipping the first two produced an exact `0.000000` on 1,400/1,400 rows (a units
  artifact read as a null, **L-60**) and a floor that failed every read in three of four cells
  (**L-56**). Neither was a power problem, and neither was fixable after the run.
- **Compute the estimand's algebraic ceiling in the design.** Where the maximum is a function of
  knowable quantities — a Sharpe ratio, a bounded rate, a fixed multiple — evaluate it per cell
  along with the implied block requirement, and declare incapable cells **before** they run.
- **Classify devices as admission or valuation.** An admission rule partitions the origin set and
  cannot change the value of a trade both arms take — the paired trade-lens difference is exactly
  zero by construction (**L-58**). Read admission devices on the **origin lens**, carrying declined
  origins at their counterfactual value.
- **Gating implies labelling.** If a design gates on a state, emit that state as a decision-time
  column. Otherwise every question about it is unaskable, not underpowered (**L-59**).
- **Controls must be shown to differ.** Assert non-degeneracy as a HARD check: a control that
  reproduces the real estimate has tested nothing and reports green while doing so (**L-57**).
- **Leave-one-out on small panels.** Below ~10 strata, report leave-one-out sign stability and the
  mass share of the largest contributor with every pooled figure. A three-instrument pooled sign
  that flips on one drop is one instrument wearing a panel's credibility (**L-61**).
- **A second universe is replication, never added `n`.** The cTrader panel's role stays credibility
  only; it is never pooled into crypto's count (AMENDMENT-C1/S1). Its value in this chapter was
  exactly that: the break-even structure replicated *more tightly* on a universe sharing no
  instrument, venue, cost model or vendor.

## Statistical defaults

Non-parametric / empirical by default (block / stationary / moving-block bootstrap;
permutation nulls). No normality, stationarity, i.i.d., or constant-vol assumptions. Block
length estimated on TRAIN only. When permuting for a null, **block-permute returns** — do not
rotate the price path with a mean statistic (cross-regime variance blowup). Wilson intervals
for rates. Holm across the binding family. Report effect sizes and `ci_low`, not just p.
