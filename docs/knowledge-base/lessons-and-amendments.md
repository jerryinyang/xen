# Lessons & Amendments — Every Lesson Carries Its Mechanism

The file that prevents reverting to past mistakes. Each entry: **what happened**, the
**mechanism (why it occurred and slipped through)**, the **fix/new rule**, and **where it is
enforced now**. A lesson without a mechanism is incomplete — re-deriving the numbers is not an
explanation.

---

## L-01 — Look-ahead leak in a shared outcome module shipped a false DEPLOYABLE_CONFIRMED ⭐

**What.** CF-MR-001 (RSI-2 fade + EXIT-RCT exit) passed TRADABLE (G-021) and
DEPLOYABLE_CONFIRMED (G-022, the spent EXP-097 global-holdout shot), then was **RETRACTED**
(2026-06-26).

**Mechanism.** The EXIT-RCT favourable limit rested `rct_target[di]` — the target computed
from bar `di`'s **own close** — as the intrabar limit *during* bar `di`. The live-actable
limit is `rct_target[di-1]` (`archive/chapter-01-price-geometry-referee/experiments/EXP-090/code/run_experiment.py:305-310`,
`archive/chapter-01-price-geometry-referee/src-archived/xen/mean_reversion.py` →
`reversion_completion_target`). This one-bar look-ahead inflated the captured edge by **~+0.25
ATR/trade**. Causalized, the bare RSI-2 fade is net-negative even gross. It slipped past a
sophisticated auditor because (a) the leak lived in a **shared vectorized outcome module**
feeding the "favourable target," and (b) the audit's verdict-forensics **re-derived the
numbers from the same contaminated module**, so the biased numbers reproduced perfectly.
**Numeric reproduction is structurally blind to acausal provenance.** It was finally exposed
only by the cTrader port + forward test (diagnosis lives in the **XRSI-V1 cTrader port project**,
external to this repo — see the `XRSI.code-workspace` sibling project, not committed here).

**Fix / new rule.** Four layers, independent of numeric reproduction:
1. **cTrader-primary execution** for any price-primary (edge-generating) experiment —
   look-ahead is impossible in-engine by construction. Python becomes analysis-only on emitted
   runs.
2. **Causal-provenance audit pass** — trace every verdict-bearing column's input timestamps;
   assert each value used at decision-time `t` derives only from data `≤ t` (`≤ t-1` for
   next-bar action). Cannot be satisfied by re-running the numbers.
3. **Leak tripwires / negative controls** — every price-primary experiment ships a control
   that *should* destroy the edge (future-shuffle / time-reversal / outcome-label permutation);
   a surviving edge ⇒ leak ⇒ REJECT.
4. **Provenance contracts** for shared `xen` modules emitting outcome/target columns; ban the
   `rct[di]` favourable-index pattern (the causal choice is `rct[di-1]`).

**Enforced at.** `experiment-auditor` Causal-Provenance & Leak section + audit checklist;
`research-pipeline` governance REJECT triggers (surviving edge under a future-destroying
control; missing provenance trace on a deployability claim); `experiment-developer` leak-tripwire
requirement; cTrader-primary policy in the pipeline skills. **Budget consequence stands:** the
11 EXP-093 counted reads and the EXP-097 holdout shot are **spent-on-defect, non-refundable**.

---

## L-02 — Booked-vs-real feed divergence hid a binding entry slippage

**What.** The XRSI-V1 cTrader port's REAL feed diverged from the research/booked feed; an
apparent "+0.093 ATR native-fill edge" was largely an artifact.

**Mechanism.** REAL omitted the **binding v2 entry slippage** (`Config.SlippageAtr=0.05`) that
the booked feed charged via `EntryFillV2`/`NetOf`; REAL's market order filled at raw `v1`. Of
the +0.085 ATR REAL−booked gap, +0.046 ATR (54%) was this un-charged slippage. The 0.5-pip
"realistic spread" was 5×–234× too small to substitute. Faithfully modeled (slippage restored)
the strategy is **negative at zero RT cost**.

**Fix / new rule.** Charge slippage/cost on the **binding leg**; the causal feed (`rct[di-1]`)
is the live-actable one; look-ahead favourable-index views (`rct[di]`) are **non-tradable** and
must be labelled as such, never used for a P&L/deployability claim.

**Enforced at.** `code-conventions.md` + audit checklist (booked-vs-real / binding-leg slippage
discipline). Links to [[L-01]].

---

## L-03 — Pooled verdicts mask the binding stratum

**What.** Collapsed cross-cell PASS/FAIL hid heterogeneity more than once (EXP-076 audit C1: a
collapsed `overall_pass_literal`; EXP-085: all 21 NET_POS were low-n S2-DEFERRED cells while
the one powered cell was NET_INCONCLUSIVE).

**Mechanism.** A `.all()` conjunction or equal-weight pooled statistic presented as *the
verdict* averages away a stratum that flips it — one high-cost instrument vetoes a domain, or
one separating cell is drowned by a pooled null.

**Fix / new rule.** Emit the binding verdict **per stratum**. A pooled/aggregated figure is a
**disclosure**, non-binding, until cross-stratum homogeneity is itself demonstrated.

**Enforced at.** governance per-stratum verdict-representation check; auditor verdict-forensics
per-stratum masking check (both already in the skills — keep them).

---

## L-04 — Match the evaluation vehicle to the signal (sparse vs per-bar; gross vs net)

**What.** EXP-023 falsely REFUTED the AVWAP baseline; the broader "AVWAP trap" is gross→net
erosion.

**Mechanism.** A ~6%-active event signal was scored against a per-bar MDE floor calibrated for
**≥80%-active** series (EXP-005) → ~16× denominator dilution dominated the result. Separately,
gross-positive edges (AVWAP bounce +3.8/+9.1/+37.6 bps) were consumed **entirely by cost** at
realistic RT (EXP-030 net EVIDENCE_AGAINST).

**Fix / new rule.** Use the **event-level method** (EXP-027) for sparse event vehicles; charge
conservative cost+financing **early**; a gross "pass" is never a tradability claim.

**Enforced at.** analysis-plan activity-rate + cost-realism checks; scope real-price/cost rules.

---

## L-05 — Verify a parameter's role before using it as a lever

**What.** EXP-042 (Track A0) set aside as FRAMING_ERROR.

**Mechanism.** The band multiplier was applied as an **entry filter** when it had always been
an **exit parameter** (Phases 004–010). The rule measured a filtered deep-pullback
subpopulation; "band 1.0 selected" reflected event *availability*, not exit quality.

**Fix / new rule.** Confirm a parameter's role against the substrate code before treating it as
an entry/exit/structural lever (parameter-governance table).

**Enforced at.** governance scope check; audit scope-compliance.

---

## L-06 — Pooled-OOS CI must scale with pooled-OOS size (multi-fold artifact)

**What.** EXP-010's original walk-forward/CV MDE inflation on 1h/4h (adversarial review F01).

**Mechanism.** The wrapper concatenated per-fold bootstrap-mean distributions, giving multi-fold
protocols a **per-fold-sized CI on a pooled-OOS estimate** → spurious MDE inflation.

**Fix / new rule.** Test-size-weighted, per-resample average of per-fold bootstrap means
(stratified pooled-OOS bootstrap); single-fold must be bit-identical to the frozen referee.

**Enforced at.** standing audit requirement (CI width decreases with `effective_n`).

---

## L-07 — Null design: block-permute returns, don't rotate the price path

**Mechanism.** Rotating the price path with a mean statistic blows up cross-regime variance and
miscalibrates the null. **Fix.** Block-permute returns. **Enforced at.** analysis-plan
null-design check. (Memory: `null_b_block_permute_returns`.)

---

## L-08 — Don't build a null around a signal-derived target

**Mechanism.** A null calibrated to a signal-derived target biases the test toward ADMIT.
**Fix.** Bite-checks must be two-sample at the √2 scale, per cell; the bite-check is an
MDE-curve co-designed with the band, not a fixed plant. **Enforced at.** governance
gate-threshold-calibration check; analysis-plan. (Memories: `falsification_null_design`,
`portfolio_mtm_and_bite_mde`.)

---

## L-09 — Portfolio risk stats need intra-position mark-to-market

**What.** EXP-095 portfolio verdict was verdict-materially wrong until an amend-in-place rerun.

**Mechanism.** Flat-at-exit booking (vs intra-1h MTM) fabricated a circuit-breaker "de-risks
−22.4%" and refuted ERC≈naive-IV; restoring D2.1 intra-position MTM overturned both (benefit
SUPPORTED, breaker NEUTRAL). Cross-domain positions are not comparable without MTM.

**Fix / new rule.** Multi-domain portfolio risk stats require intra-position mark-to-market.
**Enforced at.** scope MTM requirement; audit materiality. (Memory: `portfolio_mtm_and_bite_mde`.)

---

## L-10 — A frozen-design confound is fixed by amend-in-place, not a follow-up

**Mechanism/process.** When a confound is found in a frozen design, a *new* experiment would
leave the contaminated record as apparent evidence. **Fix.** Dated amendment + hard-delete of
the contaminated artifacts + full rerun under the amended design. **Enforced at.** deviation-
handling process. (Memory: `deviation_handling_amend_in_place`.)

---

## L-11 — Framing discipline (symmetry of skepticism; horizon/control parity)

**Mechanism.** (a) A binary NOT_SUPPORTED overstates a within-noise A≈B wash — report absolute
effect sizes, flag within-noise, note when metrics disagree. (b) An availability screen's
horizon + control parity must match the family's own mechanism, or the read is non-comparable.
**Enforced at.** analysis-plan interpretation criteria; auditor gate-shape check. (Memories:
`symmetry_of_skepticism_framing`, `availability_horizon_matches_mechanism`.)

---

## L-12 — Referee gate rigidity: fixed-threshold conjunctions over-reject and mis-scale ⭐ (Chapter-02 renew)

**What.** A standing weakness, not a single bug — surfaced repeatedly across the chapter and
patched ad hoc each time. The frozen referee is a **conjunction of fixed-threshold legs**
(5-check stack L1–L5; portfolio-fitness unit), and that shape produced three recurring failure
modes that wrongly killed, or could not even test, real candidates.

**Mechanism (why), with the three modes.**
1. **Conjunctive fragility.** Requiring all of L1–L5 simultaneously drives **FPR ≈ 0 but at a
   2–8× larger economic MDE** (EXP-003 keystone trade-off). A real-but-modest, tail-only, or
   sparse edge that any *single* leg is structurally blind to is vetoed by the AND — the gate is
   theoretically ideal (no false positives) yet practically a near-impossible bar that also
   rejects true positives (selection that favours only large, location-shaped, dense edges).
2. **Structurally-impossible legs.** A leg can have **no finite MDE** in a regime, so no true
   effect could ever satisfy it there — it is an automatic fail, not a test. EXP-015's
   incremental unit was REFUTED for exactly this (standalone-L2 had no finite MDE in high-overlap
   synchronous-null cells) and the revised unit had to **drop** that leg; many CF-MR-001 cells
   were `COVERAGE_EXCLUDED` for the same "no finite MDE on the carried arm" reason. Power was
   conflated with evidence-against.
3. **Fixed thresholds mis-scaled to the candidate.** A threshold calibrated to a reference
   vehicle mis-rejects a candidate of different sparsity / shape / instrument: the fixed per-bar
   MDE floor wrongly REFUTED a ~6%-active signal via ~16× denominator dilution (L-04); per-instrument
   MDEs run *below* the pooled floor (EXP-008); and inside CF-MR-001 a **fixed Sharpe=1.0 bite**
   and a **SUB-RANDOM-entry null** both had to be swapped mid-family for an **MDE-curve co-designed
   with the band** (EXP-095) and a **matched-distance** null (`D0-amendment-005`). The repeated
   manual fix was always the same shape: replace a fixed plant with a candidate-matched, power-aware
   construction (see L-08).

**Fix / new rule (Chapter-02 renew — needs validation, not yet applied).** Investigate replacing
rigid fixed-threshold conjunctive gates with **power-aware, candidate-matched adaptive gating**
that preserves the FPR control the frozen suite earned: apply a leg only where it has finite MDE
(report *unpowered*, never *fail*); scale thresholds to the candidate's vehicle/shape/instrument
(generalize the MDE-curve-co-designed-with-the-band pattern); and replace the hard AND with a
calibrated composite that no single structurally-blind leg can veto. **Governance constraint:** the
referee is FROZEN — any redesign is itself a predeclared experiment, FPR-recalibrated on the
dogfood-negative + synthetic-positive (EXP-019 style) and frozen **before** it adjudicates any live
candidate; it must **not** be tuned on the candidate it will judge.

**Enforced at.** Chapter-02 Phase-001 checkpoint
(`docs/experiments-docs/checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/`); the
causal RSI-2 rerun (**CF-MR-002**) is the held-out benchmark vehicle + end-to-end architecture
test, not a tuning set. Builds on [[L-03]] (pooled-as-verdict), [[L-04]] (vehicle match),
[[L-08]] (bite = MDE-curve, not a fixed plant), [[L-11]] (gate-shape blindness).

---

## L-13 — A reused evaluation vehicle can silently mis-fit a new family (EXP-008 / CF-MR-003) ⭐

**What.** CF-MR-003's cross-domain MR availability screen (EXP-008) was built by **reusing the
price-geometry availability stack** — `availability_gate` Δ-over-**regime-matched-random-timing** +
**fixed-horizon (24-bar) signed-MFE-toward-anchor**. It first returned INCONCLUSIVE (an inherited
`Hurst-DFA<0.45` leg, structurally unsatisfiable on deviation *levels* — the wrong-object + estimator-
unfit forensic, EXP-008 Amendment A1), then, with Hurst dropped, EXONERATE. A **reactive** vehicle diagnostic
(not pre-registered) **indicated** EXONERATE was **vehicle-dependent**: under a **dislocation-matched** null
(random bars at the same `|z|≥2`, no screen) the native target metrics separated — **anchor-hit +2.9 pp**
(CI [+2.0,+3.7]),
**fraction-of-dislocation-recovered +2.7 pp** (CI [+1.3,+3.1]), 82% of cells positive — while the
**MFE metric stayed within 0** (CI [−3.1,+2.4]). Against the *original* regime-matched-random control the
native metrics read **−17 to −20 pp** (near-anchor random bars trivially "revert"). So both prior
verdicts were artifacts of an ill-fit vehicle, not readings of the family.

**Mechanism (why), three coupled faults — none native to mean-reversion.**
1. **Metric confounds signal with volatility.** Fixed-horizon **MFE** toward a target grows like `√H·σ`
   at *any* bar; a volatility-matched control earns the same MFE from noise → the reversion component is
   invisible. (The MR-native reads are **target-based**: reach-anchor / time-to-anchor scaled by the
   fitted half-life / fraction-of-dislocation recovered / limit-at-anchor P&L — not a max-excursion.)
2. **The null is not dislocation-matched.** An extreme-entry (`|z|≥2`) strategy compared to
   regime-matched *random-timing* (mostly near-anchor) bars asks the wrong question — near-anchor bars
   are trivially "already reverted." The native null holds **dislocation** fixed and varies only the
   screen: "among equally-dislocated bars, does the screen pick better reversion?"
3. **Arbitrary inherited thresholds.** The 24-bar horizon and the `Hurst<0.45` leg were carried over
   without a mechanism check; the horizon should track the fitted half-life, and Hurst-DFA measures
   long-range/increment persistence, not reversion-to-a-level.

**Fix / new rule.** When starting a **new family**, re-derive the evaluation vehicle from the family's
own mechanism before reusing a prior one: (a) match the **metric** to the mechanism (target-based for a
target-reverting strategy, not a max-excursion); (b) match the **null** to the entry condition
(dislocation-matched for an extreme-entry strategy, not random-timing); (c) tie horizons to a fitted
mechanism scale (half-life), not a round number; (d) mechanism-check every inherited threshold/leg for an
attainable-pass region before it can gate. A "clean" reused pipeline that runs without error is **not**
evidence the vehicle fits — verify separation-vs-null on a native metric first. **Do not book a
family verdict from a vehicle whose fit to the family is unverified.**

**Enforced at.** EXP-008 recorded as a **methodology finding** (verdict *held*, not booked). The native
re-screen **EXP-009** (target-based estimands + screen-fail dislocation-matched null + event-specific
half-life horizon) then **SCREENED-ADMIT** CF-MR-003 with **36 leak-clean per-stratum reversion-to-anchor
passes** (S5_SPREAD/S3_DETREND/S4_OU) where the EXP-008 vehicle read EXONERATE — a **strong confirmation
that the vehicle, not the family, was the problem**. Practical corollaries proven in the loop: the null
must be **dislocation-matched** (random-timing flipped the sign −29pp); the horizon must be **event-specific
(half-life)**; the disposition must separate **precision-limited (UNPOWERED_HINT) from no-signal**; and
per-stratum reporting (L-03) beats an axis-majority rule. Builds on [[L-04]] (match the vehicle to the
signal), [[L-11]] (control/horizon parity to the mechanism), [[L-12]] (near-impossible leg — here the
inherited Hurst leg). Memory: `evaluation_vehicle_must_be_native`.

---

## L-14 — A silently-dropped core exit shipped a confounded verdict (EXP-013 / CF-MR-004) ⭐

**What.** EXP-013 booked CF-MR-004 `NOT_TRADABLE` (audit `CONFIRMED, 0 material`). An operator-directed
review **downgraded it to CONFOUNDED**: the strategy that ran was **not the strategy proposed**. The
proposal (`.ignore/idea/original-phase002-thoughts.md`) mandates **two** native exits — **form-1**
(event-driven exit when the anchor *series* reverts, i.e. spread → mean recomputed each bar against the
**moving** anchor) and **form-2** (a favorable limit at the anchor mean). EXP-013 shipped only form-2
**frozen at entry** + a time-horizon stop. No form-1; the form-2 TP never refreshed as the peer basket
(hence the anchor) drifted.

**Mechanism (why, and why it slipped through).** The spread `S = logClose − feedLog` reverts either by the
traded price moving **or by the peer/basket moving**. A **fixed-price** TP can only capture price-side
reversion; **peer-side reversion never triggers an exit**, so those positions ride to the horizon and book
adverse. That manufactured the report's "~70% ride to horizon adverse." The reported "~30% favorable-hit →
spread not mean-reverting" was the **static-TP hit rate**, not the reversion rate — the audit even named the
right cause ("reversion shared with the peer") and then **dismissed it** as a bug artifact. It slipped
through because (a) form-1 was dropped **silently** in the design (design §4 listed only "exit at anchor
mean … horizon fallback"; the pre-exec gate never diffed the implemented exits against the proposal's
**named** exits), and (b) the audit's verdict forensics re-derived P&L from the same crippled-exit
emission, so the numbers reproduced perfectly — **numeric reproduction is blind to a missing mechanism, just
as it is to acausal provenance** ([[L-01]]).

**Fix / new rule.**
1. **Exit-set diff at the pre-exec gate.** For any strategy with a proposal-specified exit set, the gate
   **must enumerate the implemented exits and diff them against the proposal's named exits**; a missing or
   substituted core exit (e.g. a time-stop standing in for an event-reversion exit) is a REVISE, not an
   approve. A dropped core component is an **unauthorised deviation** and needs explicit operator sign-off
   ([[L-10]]; renewal `README.md` "any deviation MUST be explicitly approved").
2. **A moving-target exit must move.** When the exit level is a function of a live series (a moving anchor /
   peer basket), a fixed-at-entry limit is a **different strategy** — refresh it each bar (or express it as
   the series condition, not a frozen price).
3. **Separate the fill metric from the mechanism metric.** "Favorable-limit hit rate" ≠ "reversion-
   completion rate." Book the native reversion estimand ([[L-13]]: reach-anchor / fraction-recovered /
   time-to-anchor ÷ HL) independently of any static-TP fill rate, or the availability read is confounded.
4. **Don't book a family verdict from a vehicle-incomplete run.** A `NOT_TRADABLE` from a crippled exit set
   does **not** reinforce the terminal-branch prior.

**Enforced at.** `research-pipeline` pre-exec gate (exit-set diff vs proposal); `experiment-auditor`
materiality (a missing/substituted proposal-named exit is verdict-material → fix + re-execute); EXP-013
downgraded, **EXP-014 (HYP-002)** is the faithful redo (amendment
`checkpoints/2026-07-01-004-cross-domain-mr-renewal/amendment-001-faithful-full-strategy-redo.md`). Builds
on [[L-01]] (reproduction is blind — here to a missing mechanism, not a leak), [[L-10]] (silent frozen-
design deviation → amend-in-place), [[L-13]] (native estimand ≠ inherited/incidental metric).

**Discharged (2026-07-02, EXP-014, audit PASS 0 Critical).** The faithful redo shipped **both** proposal-named
exits — form-1 event-reversion + **refreshing** form-2 anchor-mean limit (audit confirmed they fire: primary
none/R 3445 trades = form-1 281 / form-2 1898 / horizon 1266) — so the strategy tested was the one proposed.
It **still** closes **NOT-TRADABLE** (0/38 strata net- and gross-admit under the frozen 4h referee, homogeneous),
and availability itself does not separate from a dislocation-matched control at 4h. So EXP-013's confound was
real (form-1/refresh materially changed the exit mix) **but not verdict-flipping** — the family is a genuine
cost/capture wash, now booked on a faithful vehicle. Residual caveat: the per-bar mean-referee is a partial
gate-shape mismatch for a discrete high-variance round-trip bracket (19/38 cells cannot detect a planted +8 bps,
L-12 mode-2) — a per-trade/episode-native referee would need its own predeclared freeze before re-judging.

## L-15 — A binary admit on an attribution control binarizes noise at the admit bar; report the collapse fraction (EXP-014c / CF-MR-004)

**What.** EXP-014c's per-cell leak tripwire (60h peer-feed phase-shift) was read as a binary
admit/no-admit through the frozen referee. On US2000 extend/z15 the shifted edge stayed
**CI-positive at every exit object** (net ci_low +0.19 e0, +0.485 e2, +0.482 e3) and "collapsed"
only because the 3.0-bps **L5 materiality leg** failed at e2/e3 (shifted effect 2.26–2.58 bps) —
while the *same cell* at e0/z15 passed the full stack under the shift. A ~50% shrink on a
still-positive edge was one referee leg away from being read as a construction-specific
collapse. (EXP-014c `audit.md` W3 / §5.4.)

**Mechanism (why).** An attribution control (phase-shift, or any destroy) produces a
**continuous** quantity: how much of the raw edge survives when the tested relationship is
destroyed. Piping that through a threshold conjunction (materiality bar, studentized floor,
Holm) collapses the continuum to one bit, so a control net sitting *near* any leg's threshold
flips between ADMIT and NO-ADMIT on noise — and the flip direction then masquerades as a
mechanism claim ("needs the construction" vs "own-price leak"). The referee's legs were
designed to gate *candidate admission* conservatively, not to measure *attribution*; reusing
the admit stack as the attribution read imports thresholds that mean nothing for the
survives-vs-collapses question. A genuinely construction-specific edge must go **toward zero**
under the destroy at **every** exit object; failing one materiality leg at one exit while
staying CI-positive everywhere is a shrink, not a zeroing.

**Fix / new rule.**
1. **Always disclose the collapse fraction** (control net / raw net), per cell and per exit
   object, alongside any binary control verdict. The binary alone is inadmissible as an
   attribution statement.
2. **A construction-specificity claim requires collapse toward zero at every exit object** —
   not a threshold flip on one leg. Conversely, a leak claim (edge survives the destroy)
   should cite the surviving fraction, not just the surviving admit.
3. Where an attribution read is load-bearing, prefer a **paired raw-vs-control statistic**
   (CI on the difference/ratio) over two independent admit reads.
4. Sequencing: for mixed own-price/construction P&L, the control's semantics are only
   interpretable once the harvest mechanism is characterised — the shift destroys trigger
   timing, not the harvest (operator D3, 2026-07-03).

**Enforced at.** `experiment-quant-analyst` design stage (any shift/destroy control predeclares
collapse-fraction disclosure — already binding in `cf-mr-005.md` first-branch constraint 6 and
EXP-015 M3a/tripwire design); `experiment-auditor` leak pass (a binary-only control read on an
admitting cell is a REVISE); `research-pipeline` post-exec gate. Builds on [[L-11]] (report
absolute effect sizes; don't overstate a binary read when the magnitudes are a wash) and the
EXP-014c W3 finding (`python/experiments/EXP-014c/audit.md` §5.4, §7-W3).

## L-16 — A characterisation estimand must match the P&L-bearing object, or its null is object-mismatch, not absence (EXP-015/EXP-016 / CF-MR-005) ⭐

**What.** EXP-015 characterised the CF-MR-005 ladder harvest with a **per-event** estimand
(single dislocation → fraction-of-dislocation recovered vs matched control) and returned
NO_MECHANISM_EVIDENCE (0/11 supported; per-event non-reversion independently confirmed under a
control-free symmetric read) → retire recommended. The operator instead spent 3 counted TEST
reads (EXP-016, one-shot, criteria frozen pre-contact): the traded object's net **reproduced
out-of-TRAIN above its TRAIN level in all 3 cells** (US2000 +11.83 vs 10.90 bps/active,
TEST ci_low +5.33, boot_p 0.0001, 20 episodes; NZDUSD Holm-significant too). Both results are
true: the P&L object is a **multi-leg episode structure** (EXP-015's own Part A: ~68% of net
accrues with ≥2 legs open; per-leg P&L fattens with add depth), and a single-entry estimand is
structurally deaf to a structure-borne P&L.

**Mechanism (why).** A scale-in ladder's return is a function of the **joint path over an
episode** (adds at deepening levels, one shared frozen exit family, position-size path), not of
any single event's forward return. Measuring per-event recovery marginalises exactly the
dimension the strategy monetises — like characterising a straddle by the underlying's mean
drift. The per-event null then reads as "no mechanism" when it only established "no *per-event*
mechanism". This is [[L-13]] (evaluation vehicle must be native to the family) extended one
stage upstream: **characterisation estimands** must be re-derived from the family's own P&L
mechanism too, and a characterisation null may only trigger retirement if its estimand
provably covers the object that earns the P&L.

**How to apply.** Before booking a characterisation null as family-terminal: (1) state the
P&L-bearing object explicitly (event, episode, portfolio-path); (2) show the estimand is a
function of that object (an episode-native estimand for multi-leg strategies); (3) if the
estimand is narrower, label the outcome `NO_<object>_MECHANISM`, never family-level absence.
Enforced at: `experiment-quant-analyst` design (object statement mandatory in scope),
pre-exec gate, `experiment-auditor` gate-shape check. Builds on [[L-13]]; companion fact
recorded as project memory `event-mass-must-match-field-cadence` (now scoped to the per-event
object). EXP-016: `python/experiments/EXP-016/report.md` §4.

## L-17 — The frozen referee's L1 readiness floor is band-length-blind: it cannot adjudicate short (TEST-band) samples at any edge size (EXP-016) ⭐

**What.** EXP-016's TEST band (~1,110 4h bars ≈ 9 months, rows 49%→70%) was adjudicated with
the frozen 4h referee. On the strongest cell (US2000: net +11.83 bps/active, ci_low +5.33,
boot_p 0.0001, 20 episodes) the gate still REJECTED — leg forensics show **L3 PASS, L5
materiality PASS, sole failing leg `L1_readiness`** (effective_n 333 vs a floor calibrated on
full ~3.2-year TRAIN samples). The +8 bps bite plant fails the same leg: the gate is provably
blind on this band — its negative (and its positive) carry no evidential weight there.

**Mechanism (why).** L1 is a fixed effective-sample floor, edge-independent ([[L-12]] §2's
readiness-veto mode). Any band that is a fraction of the calibration sample fails it
mechanically, so confirmation reads on TEST bands (~21% of rows by construction) are
structurally unadjudicable by the frozen instrument. The referee was frozen against
full-sample screening; nobody re-derived its readiness leg for the short-band confirmation
use case — a vehicle-fit gap ([[L-13]]) inside the referee itself.

**How to apply.** (1) Never book a frozen-referee verdict (either direction) on a band the
bite plant cannot pass — run the plant first; if it fails on sample-size legs, the gate is
inapplicable, not negative. (2) Any TEST-band or short-window confirmation needs a
**predeclared, candidate-blind, frozen-before-use short-band instrument** (band-length-aware
readiness rule or an episode-native statistic with its own FPR calibration — the L-12
mode-2 fix finally becomes binding work before the *last* TEST read of any stratum is spent).
(3) Until that exists, short-band reads report frozen-seed bootstrap p + ci_low as
predeclared descriptives (as EXP-016 design §4 did), clearly labelled non-referee. Enforced
at: design pre-exec gate (any TEST read must name its band-capable instrument),
`experiment-auditor` gate-shape check. Builds on [[L-12]], [[L-13]].

## L-18 — RESERVED (critical-017): accounting primitives live only in `xen.adjudication`

Placeholder: the ID L-18 is already cited across the programme (`_pipeline-config.md`,
`xen.estimand_validation.check_no_local_accounting`, VAL-006) for the critical-017 lesson —
per-bar/per-leg accounting must come from canonical `xen.adjudication` with the reconciliation
invariant; experiment-local reimplementations certified three wrong verdicts. Recorded here as
a stub so the ID is never reused; the operative rule is enforced in code (blocking gate).

## L-19 — A single-draw random control is a noisy yardstick: kill tests need seed batteries and percentile reads (EXP-018 → EXP-019 / CF-VOLHARV-001) ⭐

**What.** EXP-018's random-timing control was ONE seeded schedule per cell. Its NZDUSD draw
printed +31.5 bps/leg with CI_low +13.7 — strong enough to look like a process property and to
seed a new family's founding anomaly. EXP-019 ran 25 independent ex-ante seeds per instrument:
the same construction centres on 0 in every (instrument × hold) stratum (NZDUSD |battery mean|
< MDE 1.4–5.3 bps), with per-seed stratum means spanning **[−11.5, +8.6]** pooled (per-stratum
seed SD 3.6–13.3 bps/leg) — the +31.5 sits above the entire distribution. A one-seed control
can land anywhere in that band, so any live-vs-single-twin comparison inherits it.

**Mechanism (why).** A seeded random arm is one draw from a sampling distribution whose spread
(seed variance × window luck) is the same order as the effect sizes under test. Leg-level CIs
within the draw are clustering-optimistic and do not see across-draw variance at all, so a
single twin can be "significantly" positive by luck (EXP-018's +31.5) or negative — biasing a
beats-random read either way. The failure is asymmetric in practice: a lucky control can kill a
genuine edge; an unlucky one can pass a dead strategy. EXP-018's verdict survived only because
its primary leg was control-free (episode WASH) and its live arms were ≈0/negative — the
single-twin reads were corroborating, not load-bearing.

**How to apply.** (1) Random/timing controls are **batteries, never single twins**: ≥25
disjoint seeds, provably data-independent (regenerable from seed + bar calendar, byte-diff at
QA — EXP-019 D1/tripwire-1 pattern). (2) The binding read is the live arm's **percentile
within the seed distribution** (rank read) plus the battery mean vs its MDE — never a diff
against one draw. (3) Anchor on an analytic null when the object permits (coin-flip direction
⇒ E[gross]=0 by construction); the seeds then calibrate, not define, the null. (4) Run both
control flavours where drift matters: dir/exposure-MATCHED twin (carry benchmark, E≠0 by
design) and coin-flip twin (zero benchmark) — their gap isolates the drift-carry component.
(5) Inference at seed level; declared MDE; UNPOWERED never read as negative (B-5). (6) All
seeds share one price window: across-seed dispersion understates common-shock variance —
window-level block bootstrap before booking any cross-seed "coherent" positive (EXP-019's
BTCUSD-48 WASH). (7) A single-twin comparison may still be run for cost reasons, but it is
**corroboration-only** and must be labelled as such — no verdict leg may rest on it. Enforced
at: quant-designer control declarations (B-1/B-5 blocks), QA pre-exec (schedule regeneration),
data-analyst battery/percentile protocol. Builds on [[L-11]], [[L-15]]; supersedes the
implicit single-twin practice of EXP-018; companion memory
`single-random-control-fragility`. EXP-019: `python/experiments/EXP-019/report.md`.

## L-20 — The CI referee itself has fragilities: a small-n block bootstrap can emit a zero-width CI, and a single seed is one draw (INFR-004 / `xen.evaluation`) ⭐

**What.** `block_bootstrap_ci` (the shared CI on every effect read) had two defects. (1) Start
positions were drawn on `[0, n-block)` then wrapped `% n`; for `n <= block+1` (and for
`block >= n`) that range collapses to a single start, so all 10k resamples equal the original
series and the reported CI is `[stat, stat]` — **zero width, false certainty** on exactly the
sparse strata (UNPOWERED cells, thin per-leg counts) where uncertainty is largest. With
`DEFAULT_BLOCK=5` any stratum with ≤6 events was affected. (2) A fixed `seed=0` made every
reported bound a **single Monte-Carlo draw**; near the zero decision boundary the 2.5% quantile's
MC noise can flip a CI-positive/negative read — L-19's single-draw disease, aimed at the
measurement apparatus instead of the strategy.

**Mechanism (why).** A moving-block bootstrap needs ≥2 distinct start positions to inject
resampling variability; truncating starts to `[0, n-block)` removes them when the block is a
large fraction of n, and a single block of length ≥n is just a rotation of the whole series
(mean-invariant) → variance 0. Separately, the 2.5%/97.5% quantiles of a 10k-rep draw are
themselves random; one seed hides that spread, so a boundary read looks certain when it is not.

**How to apply.** (1) Cap effective block to `[1, n-1]` and draw starts over the full circular
range `[0, n)` (proper circular block bootstrap) — guarantees genuine resampling for any n≥2;
never emit a sampling-derived zero-width CI. (2) Aggregate every CI across a **seed battery**
(`DEFAULT_N_SEEDS=5`, median of each bound) and disclose the per-seed bound spread
(`ci_low_seed_range`/`ci_high_seed_range`) — a boundary read with a seed range straddling 0 is
UNPOWERED-adjacent, not significant. (3) Block length has no correct value: disclose a
**`block_sensitivity`** sweep (½×/1×/2×) and flag if `sign(ci_low)` changes — block-fragile
inference is not evidence. (4) The mean chases outliers: report a `trimmed_mean`/median CI
alongside as a robustness disclosure (the `stat` arg already supports it). (5) A percentile CI
is **not** a hypothesis test — report "`bootstrap 95% CI excludes zero`", never "<5% if the true
effect were 0" (`CI_EXCLUDES_ZERO_PHRASE`). Declined: BCa (jackknife acceleration assumes iid,
unsound on block bootstrap; no decision-flip for the mean at these n). Builds on [[L-19]];
enforced in `xen.evaluation`, tests in `python/tests/test_evaluation.py`. Companion memory
`evaluation-ci-hardening`.

## L-21 — The screen→graduation seam is where dimensionless numbers become money claims; pin the unit and floor it in money (EXP-025 / SPDR series) ⭐

**What.** EXP-025's graduation design converted the SPDR screen's +0.26–0.50 ATR effect to
"30–60 bps" by asserting a **1h HTF ATR(14)** divisor from memory. The screen actually
normalised by the **5-min LTF ATR(14)[t−1]** (`spdr001_screen.py:204,299`). USTEC TRAIN-median
1h ATR = 33.9 bps vs 5min ATR = 8.19 bps → the target was inflated **4.1×**. The full T1 run
(440 cells, 22 symbols, 2.4M trades) was powered against a fictitious 30–60 bps effect; the
true effect (≈4 bps/trade at h48, ≈0.2–1 at short holds) replicated end-to-end
(screen→ref-arm→battery) but is untradeable net of spread + one-sided capture. Verdict:
NOT SUPPORTED (magnitude, not existence) — an honest closure, but the run would have been
avoided (or re-framed as apparatus test) had the conversion been checked.

**Mechanism (why).** Screen guards test *existence* (blind-base replication, phase-shift
collapse, seed battery); none checks *magnitude-in-money*. The unit conversion happens exactly
at the handoff between two documents owned by different stages — nobody owns it, so it is
asserted, not verified. A dimensionless effect size is only as good as its divisor's bps value.

**How to apply.** (1) Screen artifacts state the normaliser **object** exactly (indicator,
period, timeframe, lag) with every normalised number. (2) A graduation design converting a
screen effect to money must state the divisor object verbatim from screen code + its measured
TRAIN-median bps value + the resulting bps/trade — each verifiable, QA-traced. (3) **Money-unit
floor at disposition**: convert best-cell effect to bps/trade with the actual normaliser and
compare vs cost floor (spread + commission + capture dilution ≈ gap/2); at/below floor →
graduate only as apparatus/characterisation test. Enforced in `docs/references/spdr-lane.md`
(Graduation §, 2026-07-09). Builds on [[L-11]]. EXP-025: `python/experiments/EXP-025/analysis.md` §5.

## L-22 — A commission-only SUPPORTED band never binds on 0-commission instruments; spread must be a verdict leg (EXP-025 external review F01)

**What.** EXP-025's SUPPORTED band required net-of-commission CI_low > 0; indices carry 0
commission and spread was disclosure-only. The design's most likely SUPPORTED cell (dense
index, short hold, thousands of trades) is exactly where spread dominates: a 10–20 bps/trade
edge can be SUPPORTED while a 1–2 index-point spread erases it live. Qualification then
selects high-turnover statistical edges — anti-correlated with spread robustness. Moot in
EXP-025 (0/440 qualified) but structural.

**How to apply.** Future designs make the 1× spread scenario a **binding tier** for any
SUPPORTED claim (SUPPORTED-GROSS vs SUPPORTED-NET-OF-ALL-COSTS as separate bands, or minimum:
CI_low > 0 must survive the 1× spread estimate before an instrument counts toward the
multiplicity family). 0.5×/2× spread remain disclosure. Builds on [[L-21]]; companion memory
`cost-model-and-injection`.

**Where enforced.** `quant-designer/references/design-requirements.md` §10 (binding band
declaration) + `qa-compliance/SKILL.md` §3 (L-22 clause; commission-only band on a
0-commission instrument = REVISE). Codified at the chapter-02→03 rollover (2026-07-09).

## L-23 — Pre-measurement amendments must declare their direction (looser/tighter) and keep a running count; re-derive the joint false-qualification rate at the final gate set (EXP-025 external review F03)

**What.** All seven 2026-07-08 pre-measurement amendments to EXP-025's design moved the same
direction — easier qualification, harder rejection (hostile-neighbour veto removed; per-fold
sign → pooled; erosion veto → disclosure; 97.5th-pct → 2 seed-SD; redundant CI gate dropped;
sentinel per-stratum → family-wise; tripwire per-cell → pooled 50%). Each was individually
well-argued; the aggregate false-qualification rate under the final gate set was never
re-derived — the "plane is priced" arithmetic was written for the stricter gates. No false
admit resulted (0/440 qualified), but the pattern is what a motivated design process produces
even with honest local reasoning.

**How to apply.** (1) Every pre-measurement amendment states its direction (LOOSER/TIGHTER/
NEUTRAL) and the running directional count for the experiment. (2) After the final amendment,
re-state the expected number of false qualifiers under the global null with the FINAL gate
set (simulable from the battery machinery: apply the selection rules to random-direction
runs); if materially above budget, tighten one gate back. (3) A one-directional streak ≥3 is
an explicit flag to the operator at the execution gate. Builds on [[L-12]]; companion memory
`selection-rules-symmetric-outlier-robustness`.

**Where enforced.** `quant-designer/references/design-requirements.md` §11 (AMENDMENT block
format + final-gate re-derivation) + `qa-compliance/SKILL.md` §3 (L-23 clause). Codified at
the chapter-02→03 rollover (2026-07-09).

## L-24 — Eligibility/null design gaps surfaced by EXP-025 external review (F02/F04/F06/F07) — future-design rules

**What.** Four design-level gaps, all moot for EXP-025's verdict (no cell qualified; T2 and
tripwire never ran; no TEST read spent) but binding on future designs:

1. **(F02) Seed-SD prices direction-randomization only, not regime concentration.** A
   same-timestamps Bernoulli battery shares one market path; a candidate whose entire TRAIN
   edge sits in one volatility episode clears 2 seed-SD easily. Rule: eligibility includes a
   time-stability read — TRAIN net positive in ≥2 of 3 chronological thirds, or a
   concentration ceiling (fraction of net from top decile of trades / top quarter). Cheap,
   uses existing emissions. Builds on [[L-19]].
2. **(F04) An exit-dependent statistic needs a null run under the same exit.** Battery trades
   under a path-dependent exit (e.g. DI-flip) have different hold/exposure distributions than
   candidate trades; comparing the exit* leg of a max-stat against an entry-cadence-only null
   mis-specifies variance and drift exposure. Rule: each battery seed re-runs under exit* when
   exit* ≠ benchmark, so the null max-stat spans identical statistics; the exit-selection step
   itself goes in the multiplicity registry. If infeasible → exit* demoted to disclosure.
   Builds on [[L-16]].
3. **(F06) Tripwire retention thresholds must be derived, not asserted.** EXP-025's 50%/25%
   phase-shift retention criterion came from DI-autocorrelation intuition. Rule: compute the
   actual autocorrelation-implied retention (e.g. corr(state[t], state[t+shift]) on the real
   TRAIN streams per instrument, with CI) and set the REJECT threshold from it — the data
   exists before any read.
4. **(F07) The TEST-read n floor must be MDE-consistent.** n ≥ 50 admits reads with MDE
   17–34 bps against a shrunk effect — near-guaranteed coin flips that burn capped reads.
   Rule: read-eligibility floor = the n at which MDE ≤ the (shrinkage-adjusted, see F05 note
   below) TRAIN point estimate of that cell, applied prospectively; keep the absolute
   UNPOWERED line. Corollary (F05): power claims must compare TEST MDE against a
   **shrunk** TRAIN effect — estimate the shrinkage factor from F0→F1+F2 attenuation (the
   folds give it for free), never against the unshrunk selected maximum. Builds on [[L-06]],
   [[L-19]].

**How to apply.** quant-designer checks all four at design time for any battery-gated,
multi-cell, capped-read design; QA traces them as clauses. EXP-025 reviews:
`archive/chapter-02-mr-volharv-htfdi/experiments/EXP-025/report.md`.

**Where enforced.** `quant-designer/references/design-requirements.md` §12 (four mandatory
rules) + `qa-compliance/SKILL.md` §3 (L-24 clause-trace). Codified at the chapter-02→03
rollover (2026-07-09).

## L-25 — An absolute threshold on an EXTENSIVE statistic, calibrated at small N, is inoperative at live scale (XENA-001 / INFR-009) ⭐

**What.** The XENA `F_floor` (0.4302, INFR-006 v3) is an absolute threshold on log-wealth — an
**extensive** statistic that grows with candidate count and budget — calibrated at **24 candidates /
400 budget** (null F̂ median 0.19). At live scale (2,736 candidates) XENA-001/002/003 finalists cleared
it **8.3×–57×**, so the floor was inoperative and the plateau screen — which passes **50.8% of
pure-noise finalists** — became the sole certification criterion. A pure RANDOM control (XENA-001)
certified **4/12 finalists (33%)** against a **0.75%** battery-null rate (MACHINERY-ALARM). The emission
layer was clean; the defect was entirely in the adjudication layer.

**How to apply.** Never gate a portfolio/selection statistic with an absolute threshold on an
**extensive** quantity. Use an **intensive** (per-unit / per-leg / ratio) statistic, or a
**selection-aware two-stage gate** whose end-to-end FPR is controlled by construction (INFR-009 exit (c):
stage-1 screen fixes exactly one subset → embargo → stage-2 leg-studentized LCB on a genuinely
independent band; CONFIRM DUAL_CERTIFY e2e α̂ 5.0%/5.0%). Either the calibration N matches live N or the
statistic is scale-invariant — otherwise the threshold means nothing at the scale it is used. Supersedes
the informal `xena-referee-scale-defect` note.

**Where enforced.** INFR-009 restored binder `results/pc_frozen_registry.json` v2 (sha256 `db87dc1a…`);
INFR-006 v3 extensive-F (`537d691a…`) superseded. Spec: `docs/references/xena-lane.md`;
`python/experiments/INFR-009/report.md`.

## L-26 — A costless cadence-maximizing objective cannot adjudicate a conditioning/filter thesis (XENA-002 audit B2 / INFR-009 P5) ⭐

**What.** The XENA search objective (`charge_costs=false` log-wealth) pays for **trade count**. Every HTF
context filter thins cadence, so the objective penalizes any filter **regardless of whether it improves
signal quality** — a conditioning thesis cannot win under it, whether or not it is true. Across
XENA-001/002/003 the unfiltered V00 was **never under-selected** (0.45× / 1.18× / **4.0× over**-represented
of its universe share); the negative filter-structure read is therefore **confounded**, not evidence
against conditioning. Compounded by a governance near-miss: spread pins (`cost_bps`) were unset on 10/12
instruments, so a gross gate pass would have carried a **vacuous net block** (the L-22 failure shape) and
nothing in the pipeline blocked it.

**How to apply.** When the thesis is about trade **quality/selectivity vs quantity**, **net cost must bind
the selection objective**, not be informational-only. INFR-009 P5 injects a flat RT cost (**1.0 bps**) into
the binding stage-2 net objective. A filter/conditioning read taken under a costless objective is
uninterpretable — **do not retire a thesis on it** (repeats the L-12/L-13 broken-adjudicator error).
Reinforces [[L-22]] (spread must be a verdict leg). Builds on [[L-13]].

**Where enforced.** INFR-009 P5 net-inject registry v2; `docs/references/xena-lane.md`;
`python/experiments/INFR-009/report.md`.

## L-27 — The permutation-null battery is confounded on limit-entry / non-grid-priced universes (XENA-003) ⭐

**What.** The permutation-null battery (causal alignment-break, not P&L shuffle — L-14) is **confounded on
limit-entry universes**. XENA-003 (native limit fills) scored live F̂ ≈ 23; the discriminating control that
moved only the entry-price basis to the adjacent grid open (ARM-NEXTOPEN; times/exits/sizing held) dropped
F̂ to **0.09–1.93**, *below* the permuted null (5.66). The live≫permuted gap was the **passive-limit print**
(+7.5 bps/leg, 91.2% of the gross edge), **not** predictive timing — the permutation destroys the
entry-price basis along with the temporal alignment.

**How to apply.** Before reading any limit-entry / non-grid-priced universe with the battery, add a
**next-open discriminating control** (re-price entries to the adjacent grid open, hold times/exits/sizing
fixed) to separate the passive-limit fill advantage from predictive timing. If the battery cannot be
de-confounded this way, it is **inadmissible** for that universe. Builds on [[L-14]]; companion pitfall
[[P-10]].

**Where enforced.** Design note for the next native-fill XENA universe; `docs/references/xena-lane.md`;
`python/experiments/XENA-003/report.md`.

## L-28 — Destroy permutations must be derangements (VAL-008 / checkpoint-013) ⭐

**What.** VAL-008 Phase D stack smoke: a plain (non-derangement) destroy permutation left
**11.1% fixed-point alignment** with the true schedule, so the planted edge only partially
collapsed (collapse fraction **0.87**, not ≈0). A tripwire that "almost" collapses can pass as
non-vacuous while still leaking plant/true signal through fixed points.

**Mechanism.** A uniform random permutation of n items has **E[fixed points] = 1 for any n**
and P(≥1 fixed point) = 1 − 1/e ≈ 63% (1/e ≈ 37% is the derangement probability). The leak
scales inversely with block count: at VAL-008's 18 permuted blocks, one fixed block = 5.6% of
slots at TRUE alignment (two = 11.1%, the observed case). Those fixed points keep the original
timing/signal at those indices; the destroy is therefore a **partial** destroy.
Collapse fraction under a fixed-point-leaking permutation understates residual signal and can
mis-calibrate tripwire bite (L-14 vacuity / L-19 control-noise shapes compounded).

**Fix / new rule.** Every destroy permutation used as a leak tripwire, attribution control, or
null battery arm must be a **derangement** (zero fixed points) — regenerate or reject draws
with any fixed point. State derangement explicitly in the CONTROL / TRIPWIRE block; measured
alignment after destroy must be 0% fixed points (or disclosed residual if a softer destroy is
predeclared). Builds on [[L-14]], [[L-19]].

**Enforced at.** `quant-designer/references/design-requirements.md` §3 control blocks + §4
tripwire (L-28 derangement clause); `qa-compliance` §3 governance clause list. Evidence:
`python/experiments/VAL-008/report.md` §5; D1-signed at checkpoint-013
(`docs/experiments-docs/checkpoints/2026-07-16-013-chapter04-open-htfcap-epsosc-cal/design.md` §1).

## L-29 — Nautilus fill-ts = decision-bar close; naive searchsorted on closes is off-by-one (VAL-008)

**What.** On the Nautilus stack, fill timestamp equals the **decision-bar close** (wall-clock
**open** of the fill bar). Aligning fills to bars with naive `searchsorted` on bar-close times
mis-indexes the fill bar by **one**.

**Mechanism.** Decision at bar-open on confirmed data ≤ t−1 places the market order for the
*next* bar; the engine stamps the fill at the decision bar's close timestamp, which is the
fill bar's open. Treating that stamp as "close of the fill bar" (or `searchsorted` side that
picks the decision bar) lands one bar early/late. Price anchors then disagree with the ledger.

**Fix / new rule.** When mapping fills → bars, treat fill-ts as the open of the fill bar (=
close of the decision bar). **Anchor check (mandatory on smoke + analysis):**
`EntryFillPrice == next-bar RealOpen ± 1 tick` (or the design's declared fill basis). Do not
use unadjusted close-axis `searchsorted` as the sole bar index.

**Enforced at.** `data-analyst/references/interrogation-protocol.md` fill/alignment probe;
`experiment-developer/references/code-conventions.md` Nautilus runner conventions;
emission-contract note in
`archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-010/code/emission_contract_v1.md`.
Evidence: VAL-008 `report.md` §5; checkpoint-013 §1 D1.

## L-30 — `BacktestRunConfig(dispose_on_completion=False)` required for node-path report capture (VAL-008)

**What.** Default `dispose_on_completion=True` on `BacktestRunConfig` **silently empties**
engine reports after `BacktestNode.run()` returns; fills/orders/positions capture then yields
empty frames. Phase B smokes never exercised the node-path report path, so the trap shipped.

**Mechanism.** Node completion disposes the engine/cache before the runner can call
`generate_*_report()` unless dispose is deferred. Empty reports look like "no trades" rather
than a config bug.

**Fix / new rule.** All production/experiment runners set
`BacktestRunConfig(dispose_on_completion=False)`, capture reports from the live engine, then
`node.dispose()` explicitly. Document in runner templates; optional follow-up patch of
`xen.nautilus.backtest_util.run_ma_cross_node` (smoke-only path — currently misleading, not
blocking).

**Enforced at.** `experiment-developer/references/code-conventions.md` Nautilus runner
conventions; runner templates under experiment `code/`. Evidence: VAL-008 `report.md` §5;
checkpoint-013 §1 D1.

## L-31 — One BacktestNode per process (Rust logging init panics on a second node) (VAL-008)

**What.** Constructing a second `BacktestNode` in the same Python process panics in Nautilus
Rust logging init. Multi-cell grids cannot share a process for sequential nodes.

**Mechanism.** Global Rust logger / tracing init is process-once; a second node re-enters init
and aborts. In-process loop over cells is unsafe regardless of dispose.

**Fix / new rule.** **One BacktestNode per process.** Multi-cell / multi-instrument batching
uses **subprocess-per-cell** (or an equivalent process boundary). Until multi-instrument
single-engine is proven (INFR-014 smoke S1), do not assume one process can host N instruments
either.

**Enforced at.** `experiment-developer/references/code-conventions.md` runner template;
`qa-compliance` §3 clause (in-process multi-node = REVISE). Evidence: VAL-008 `report.md` §5;
checkpoint-013 §1 D1.

## L-32 — An arbitrary value/significance threshold wired to auto-decide reports absence-of-evidence as evidence-of-absence; retire it to a report layer (XENA-HTFCAP-001 / INFR-016) ⭐

**What.** XENA-HTFCAP-001 (exploratory) reproduced the "arbitrary-gate trap" the programme's
own principles forbid — twice, on real binding cells. (1) A **25-seed** sign-scramble battery
with an `at_or_above_p95` BOOLEAN auto-labelled directionally-positive, gate-attributable cells
as "fails": SOL v1.5 DI_VOL_HI H64 raw median **24.9 bps gross**, percentile-vs-battery **0.80**,
`at_or_above_p95 = FALSE` (`controls.py:97`; `controls_SOLUSDT__DI_VOL_HI__v1.5__adxna__H64.json:39-40`);
BTC#2 ~10.7 bps, p≈0.23. (2) The pinned stage-2 binder's **`one_subset` / top-1 only**
(`calibration_bybit15.py:409,860`) HID those cells entirely — it certified a near-zero (~1 bps)
leak-class cell and never reported the suggestive ones. (3) Same class: gate-schedule derangement
collapse **< 0.5 = HARD BTC REJECT** (`controls.py:251,301`).

**Mechanism (why).** 25 seeds cannot resolve a P95 — that bar IS ~the top order statistic of 25
draws = pure noise. The **same read at ≥2000 seeds** resolves to **~P78, one-sided p≈0.22** —
"suggestive but underpowered", NOT a refutation. Reproduced exactly in `xen.xena.controls`:
SOL → **p=0.224, percentile 0.78, effect +23.6 bps, label SUGGESTIVE**. The defect is structural:
a value/quality/significance quantity is **continuous**, and a threshold wired to DECIDE collapses
it to one bit at the least-resolved point of the estimator — so absence of evidence at an arbitrary
bar is reported as evidence of absence, and any subset-selecting binder (`one_subset`) can then hide
the cells that would contradict it. This is [[L-15]] (binarize noise at the admit bar), [[L-17]]
(band-length-blind floor), [[L-19]] (a percentile needs a real seed battery), [[L-25]] (scale-broken
threshold) and [[L-12]] (fixed-threshold conjunctions over-reject), now at gate scale in the XENA
value chain.

**Fix / new rule (INFR-016, operator-ratified 2026-07-18).** Every value/quality/significance/
selection GATE becomes a **report layer** (`xen.xena.report_layer.LayerReport`): per candidate,
`observed / ideal / interpretation`, **no `pass` field**, nothing machine-dropped; the operator
authorises progression. Split the value chain in two: **VALIDITY attestations** (holdout, causal
≤t-1, estimand reconciliation, non-STUB fence, no-local-accounting, and **future-destroy** leak
survival) stay HARD — a failure means *emission invalid → fix the data*; **VALUE reads** are report
layers. **Control class:** `future_destroy` (edge survives destroying FUTURE info ⇒ acausal L-01
leak) stays hard; `within_sample_attribution` (timing scrambled, entries still causal — the
gate-schedule derangement) is a report layer (collapse fraction reported, operator judges
leak-vs-edge). Retired auto-verdicts: `at_or_above_p95` (→ `controls.sign_battery`, **≥2000 seeds**,
effect+p+CI), `n_legs_floor` veto (→ `report_layer.power_layer`, report power), `one_subset` top-1
(→ `stage2_bounds_layer` for ALL subsets+per-cell), derangement `hard_fail_leak` (→
`controls.attribution_derangement`, reported fraction), final-gate `passed` (→
`final_gate.final_report_layer`). Interpretation bands (SUPPORTED/WASH/CONTRADICTED/UNPOWERED/
SUGGESTIVE/STRONG) are **labels, never gates**. **Trade-off signed by the operator:** a partly-
surviving edge on a within-sample attribution control is no longer auto-blocked — the operator reads
the collapse fraction and judges. L-01 future-look-ahead protection is untouched.

**Enforced at.** `xen.xena.report_layer` + `xen.xena.controls` (no `pass` field, verdict-key guard);
`xen.xena.final_gate.final_report_layer`; `research-pipeline` SKILL + `_pipeline-config.md`
(operator gates = holdout-safety + data validity only); `data-analyst` / `quant-designer` skills;
`docs/references/xena-lane.md`; `references/governance-constraints.md`. Design + ratification:
`python/experiments/INFR-016/design.md`; tests `python/tests/test_xena_infr016.py`. Builds on
[[L-12]], [[L-15]], [[L-17]], [[L-19]], [[L-25]], [[L-26]].

## L-33 — A statistic can reproduce perfectly and still contain no conditional skill (SPDR-007) ⭐

**What.** The session Protection quantile reproduced on CONFIRM (hit 0.728 versus its 0.70
target), yet matched unconditional timing hit 0.700 at its own quantile and 0.675 at the signal
level. The signal race was 0.333 versus control 0.343; the apparent success was not edge.

**Mechanism (why).** Quantiles/order statistics of a stable price process reproduce whether or
not the event that selected them is informative. Calibration asks whether the statistic is
stable; it does not ask whether conditioning added value. A positive-control bite likewise
proves apparatus sensitivity, not a positive companion edge.

**Fix / new rule.** For timing objects require all three: reproduction/calibration, separation
from matched random timing, and clearance of a valid cost floor. Matched random timing is the
binding attribution control; future-destroy is a leak tripwire, not its substitute.

**Enforced at.** `python/experiments/SPDR-007/design.md` deviations D-1/D-2 and report R1–R5;
checkpoint-014/015 retrospectives; [methodology-canon.md](methodology-canon.md). Cross-family
automation remains a Renew item rather than an already-landed check.

## L-34 — Positive-only K-of-N counts manufacture structure from the expected null tail (SPDR-008) ⭐

**What.** Seven positive signed-load qualifiers appeared to satisfy a K=3 narrative, but the
permuted null expected 6.0 and the anti-monotone mirror produced ten. The positive tail was not
enriched and did not reproduce in magnitude.

**Mechanism (why).** A large cell grid necessarily emits chance winners in both directions.
Counting only the desired tail compares the observed maximum to zero rather than to the realised
multiple-testing process; sign-only CONFIRM preserves winner's-curse labels without effect size.

**Fix / new rule.** Report positive, anti-monotone and null-expected winner counts together;
require connected neighbourhoods plus magnitude and sign reproduction on CONFIRM.

**Enforced at.** `python/experiments/SPDR-008/design.md`/`analysis.md` K=3 machinery and the
checkpoint-014 retrospective; [methodology-canon.md](methodology-canon.md). Generic pipeline
enforcement is still an explicit Renew gap.

## L-35 — Cross-symbol membership does not prevent a one-name portfolio (XENA-EPSOSC-002)

**What.** A four-symbol certified subset still derived most apparent profit from AKRO (+450 bps),
while LEVER was near zero and STMX negative. A naive positive mean coexisted with overlap-aware
gross LCB −68.2 and net LCB −102.1.

**Mechanism (why).** Requiring K symbols constrains labels, not contribution weights or temporal
overlap. One volatile constituent can carry the pooled point estimate; equal-weight resampling
understates uncertainty when episodes overlap and contributions are concentrated.

**Fix / new rule.** Every cross-sectional/portfolio read reports contribution concentration,
per-symbol results, leave-one-name-out behaviour and overlap-aware uncertainty. K is a breadth
descriptor, never proof of diversification.

**Enforced at.** XENA-EPSOSC-002 matched-drift/overlap-aware analysis, `xen.xena.report_layer`,
`data-analyst` concentration protocol, and [methodology-canon.md](methodology-canon.md).

## L-36 — A same-stream print differential is not executable spread (INFR-017) ⭐

**What.** `SpreadBps`, previously used as measured spread in SPDR-005/006, was negative in
roughly 32–40% of BTC/ETH TRAIN minutes. INFR-017 established that it is the difference between
mean aggressor-buy and mean aggressor-sell trade prices, not contemporaneous best ask minus bid.

**Mechanism (why).** The two means summarize different trades occurring at different times and
market states. Their ordering can reverse as price moves within the minute; flooring the sign
would hide the semantic mismatch rather than create a quote. The field shares the same trade
stream as delta, so it is not independent spread evidence either.

**Fix / new rule.** Pin the field `UNUSABLE`, never read it as spread or cost, and reject negative
spread inputs at the actual cost-access boundary. Chapter 05 uses no replacement proxy: spread cost
is unavailable and not charged, so reported cost understates total cost. Earlier spread-based floor
claims are withdrawn; their gross and
fee/funding evidence remains.

**Enforced at.** INFR-017 `column_pins.json`; `xen.sigbar.data_types` and
`xen.sigbar.fences.assert_frozen_inputs`. The ordinary staging/cost path is not yet quarantined;
that missing enforcement is explicitly assigned to the next infrastructure preflight.

## L-37 — Outcome availability is a post-event conditioning variable (SPDR-009)

**What.** SPDR-009 dropped 25,247 of 32,433 located D1 events because a contiguous 1m outcome
path was unavailable. Complete-window retention deteriorated with aggregation and surviving
windows carried 2.4×–27× more volume than partial windows.

**Mechanism (why).** Listings, trading activity and data continuity determine whether a forward
path exists. Conditioning on complete outcomes therefore selects older/more active instruments
after event location; it can change absolute return distributions even when same-event marginal
contrasts remain partly protected.

**Fix / new rule.** Emit located, usable and dropped counts plus covariate comparisons at every
domain; label absolute-return/floor reads as availability-conditioned; do not interpret an
unpowered coarse domain as negative evidence.

**Enforced at.** SPDR-009 report population funnel and checkpoint-015 retrospective. A reusable
availability-attestation check is still a Renew item.

## L-38 — Detection granularity and holding horizon are separate design axes (SPDR-009)

**What.** Candidate supply collapsed 95,836→9,497→2,974→640 across D1→D4, leaving only
16/2/0 signal events at D2/D3/D4. Coarser detection could not answer the hypothesis, while
fixed short bar-count holds left 16.3% of D1 H5 outcomes exactly zero.

**Mechanism (why).** Aggregation erases sparse local effort/result events; shortening the hold
in bar units then measures dead time rather than economic resolution. The data support neither
“coarser is better” nor “finest is always best”—only that the event scale and P&L scale differ.

**Fix / new rule.** Detect at the finest reliable scale that preserves the event, then choose
an independently justified economic horizon (time, first-touch, range or ATR); report power and
coverage at both seams.

**Enforced at.** checkpoint-015 retrospective and [methodology-canon.md](methodology-canon.md);
the next family must freeze both axes before emission.

## L-39 — Time-of-week keys must be typed before arithmetic (INFR-017)

**What.** The first signed-volume seasonal baseline collapsed 1,440 minute-of-day values into
256 buckets. Its hash `78dd7988…` is discarded and must never be reused.

**Mechanism (why).** `hour * 60 + minute` was evaluated in an `Int8` expression before the
result reached its destination column, so arithmetic overflow aliased distinct minutes. A final
cast cannot recover information already wrapped.

**Fix / new rule.** Cast inputs to a sufficiently wide integer before multiplying; assert key
ranges and materialise the full 10,080 minute-of-week grid with explicit fallback behaviour.

**Enforced at.** repaired INFR-017 seasonal-baseline builder, range assertions and five
regression cases covering known wrap timestamps; accepted pin `1b7244c8…`.

## L-40 — An integrity percentage is vacuous without declared coverage and join accounting (INFR-017)

**What.** The original provenance check could pass after downloading only 1/20 declared
symbol-days, and an inner join could silently hide raw/staged bars that existed on only one side.

**Mechanism (why).** Equality was computed only on successfully downloaded, matched rows. The
denominator therefore shrank when evidence was missing—the exact condition the gate was meant to
detect—and inner joins erased unmatched keys before reconciliation.

**Fix / new rule.** Integrity gates require complete declared coverage, exact key-set equality,
bar-count agreement and per-field reconciliation. A partial download is a failed attestation,
not a smaller successful sample.

**Enforced at.** INFR-017 provenance audit coverage assertions and NTrades/bar-key checks;
raw aggressor reconstruction passed all 20/20 declared symbol-days.

## L-41 — Nautilus bar callbacks fill market orders at the processed bar close, not the next open (SPDR-011) ⭐

**What.** L-29 correctly located the fill timestamp at the decision boundary but incorrectly
generalised the fill price to the next bar's `RealOpen`. Nautilus processes a complete external
OHLC bar through the exchange before dispatching `on_bar`; a market order submitted in that callback
therefore sees the processed bar's close. Continuous tape hid the defect whenever that close equalled
the next open. SPDR-011 exposed 3,314 next-open mismatches across 7,212 failed-run actions.

**Mechanism (why).** Timestamp equality is not event-order equality. The exchange traverses O/H/L/C,
then the strategy receives the bar, then the order is settled against the current L1 state. A later
ledger rewrite to catalog open creates a synthetic fill and defeats engine reconciliation.

**Fix / new rule.** For an open-to-open design, supply the catalog's real next-open price as a
separate execution event ordered after the causal decision, and delay order insertion to that event;
reconcile the actual engine fill to the source `RealOpen`. Never infer price basis from fill timestamp,
and never replace an emitted fill after execution. L-41 supersedes L-29's universal price-anchor claim;
L-29's close-axis timestamp warning remains valid.

**Enforced at.** SPDR-011 amendments A7/A8, engine-sequencing regression tests, event-to-fill
reconciliation, and fresh pre-execution QA.

## L-42 — Scheduled decisions cannot depend on a boundary bar existing (SPDR-011) ⭐

**What.** After A7 corrected the fill price, a clean Run-1 still found 24 actions whose orders were
submitted one minute late and filled two minutes after the decision. Every case occurred where the
one-minute catalog had no bar exactly at the scheduled four-hour boundary; most continuous-boundary
actions reconciled and therefore concealed the dependency.

**Mechanism (why).** `on_bar` is a data-arrival callback, not a decision clock. When the exact
boundary bar is absent, the strategy cannot submit until the next observed bar. The real-open
execution tick has already passed, so the market order settles against later engine state.

**Fix / new rule.** Time-scheduled strategies must submit from exact engine-clock alerts and test a
deliberately missing decision-bar case. Market-data callbacks may update state but cannot be the sole
clock for a predeclared decision. Reconcile every fill timestamp and source price; continuous-tape
agreement is insufficient.

**Enforced at.** SPDR-011 amendment A9, a real BacktestNode missing-boundary regression test, and
fresh pre-execution QA before another clean Run-1.

## L-43 — Nanosecond contracts must not round-trip through Python datetime (SPDR-011)

**What.** The engine emitted every A9 fill at the intended nanosecond, but reconciliation rejected
them. Polars `iter_rows` converted `datetime[ns]` values to Python `datetime`, which has microsecond
precision and silently erased the final nanosecond.

**Mechanism (why).** A precision-bearing column was converted to a lower-precision scalar before
the equality check. The checker then compared the rounded fill time to the exact scheduled offset.

**Fix / new rule.** Convert timestamp columns to integer nanoseconds inside Polars before row
iteration and compare those integers. Every sub-microsecond contract requires a regression using a
real `datetime[ns]` column, not only integer fixtures.

**Enforced at.** SPDR-011 amendment A10 and fill-reconciliation nanosecond regression.

## L-44 — Simultaneous multi-instrument market events require collision-free sequencing (SPDR-011) ⭐

**What.** With five market orders and five execution ticks sharing one venue timestamp, the first
instrument's tick could settle other instruments' pending orders against their stale prior-close
state. Fills had the expected timestamp but 128–253 non-BTC actions per symbol missed `RealOpen`;
BTC, whose tick led the merged stream, reconciled completely.

**Mechanism (why).** Equal timestamps do not define cross-stream event order. In the multi-instrument
engine, venue processing of one data event can advance pending market orders before another
instrument's same-time price event has updated its state.

**Fix / new rule.** Serialize simultaneous symbol actions with frozen nanosecond offsets. For each
symbol, issue the clock alert, insert its order one nanosecond later, then process only that symbol's
real-open tick one nanosecond after insertion; do not leave another symbol's order pending. Test at
least two instruments in one BacktestNode with deliberately different prior closes and opens. At a
shared same-symbol boundary, re-derive an explicit runtime EXIT-before-ENTRY priority rather than
relying on equal-key sort stability.

**Enforced at.** SPDR-011 amendment A10 and the multi-instrument real-engine regression.

## L-45 — Execution-event size can change a market fill even when its price is correct (SPDR-011)

**What.** After price and timestamp sequencing reconciled 2,771 actions, one 100-DOGE exit met a
real-open tick carrying only 50 DOGE. Nautilus filled the remainder one tick higher, emitting a
half-tick blended average instead of the tick's `RealOpen`.

**Mechanism (why).** A `TradeTick` is not only a price carrier; its size constrains immediately
available quantity in the matching engine. An adapter order larger than the tick therefore changes
the measured fill basis through simulated impact.

**Fix / new rule.** Unit-return characterisation uses one minimum size-increment order and asserts
that every execution tick covers it before engine construction. The adapter quantity is explicitly
non-economic and supports no capacity, liquidity, impact or deployability claim. Any later strategy
replay must size and test physical execution separately rather than inherit this adapter.

**Enforced at.** SPDR-011 amendment A11, pre-engine tick-size gate and insufficient-size regression.

## L-46 — Floating-point partition checks must preserve their declared scale (SPDR-011)

**What.** The signed-data ingest and attestation accepted
`abs(BuyVolume + SellVolume - Volume) <= 1e-9 * max(abs(Volume), 1)`, but the Run-1 join later
rechecked four-hour aggregates against an absolute `1e-9` threshold. That false-rejected 265 of
5,009 slots even though the worst relative discrepancy was only `2.04e-15`.

**Mechanism (why).** Summing many binary floating-point values increases absolute rounding residue
with the scale of volume. An absolute epsilon silently changes a relative source contract and makes
valid high-volume aggregates fail more often than low-volume ones.

**Fix / new rule.** Reuse the attested scale-aware expression at every downstream validation
boundary, including after aggregation. Regression fixtures must include a large-volume row whose
absolute residue exceeds `1e-9` while its relative residue remains inside the frozen tolerance.

**Enforced at.** SPDR-011 amendment A12 and the signed-flow relative-tolerance regression.

## L-47 — A control battery's cost must be measured before it gates a run (SPDR-011)

**What.** The SPDR-011 matched-timing battery rebuilt its candidate pool by scanning all ~12,000
timing candidates, comparing seven fields, for every one of ~1,390 live events, on every one of
2,000 seeds. Two governed Run-1 attempts were launched, and ~80 minutes of wall clock spent, before
anyone established that this single battery needed roughly 2.5 hours while every other battery in
the run finished in well under a minute.

**Mechanism (why).** Seed counts are chosen for statistical power, not for compute, so an O(n_live x
n_candidates) inner loop is invisible in the design and only surfaces at execution. The run emits no
intermediate artifact between the estimand gate and the final bundle, so a battery that is merely
slow is indistinguishable from one that is hung. Both attempts were killed on suspicion rather than
on evidence, which is how an experiment silently converts operator patience into a stopping rule.

**Fix / new rule.** Before a run is gated, measure per-seed cost of every >=2,000-seed battery on a
synthetic frame of the real shape and record the projected wall clock in the design. Where a battery
repeats a seed-invariant computation, hoist it: precompute the index once, keep the selection logic
untouched, and prove the optimisation bit-identical against a pinned pre-optimisation parity corpus
covering the exhausted-pool and no-candidate paths. A compute-path change may never alter a
selection, and its parity proof is the amendment's evidence, not a claim.

**Enforced at.** SPDR-011 amendment A13, design clause §13.16, and
`python/tests/test_spdr011_controls_parity.py`.

## L-48 — A cost convention adopted in one chapter is not a programme rule until it is enforced in code (INFR-018) ⭐

**What.** Chapter 05 removed spread from cost accounting: no stored field, no flip-pair proxy, no
fixed pin. The rule was implemented as a *call-site convention* — omit `spread_bps` and
`bybit_round_trip_cost_bps` returns `PARTIAL_FEES_FUNDING_ONLY`. Nine months of XENA
infrastructure kept charging a hardcoded `GAP_SPREAD_BPS = 5.0` through the same shared function,
which happily returned `FULL_DECLARED_COMPONENTS` because a caller had passed a spread. The two
lanes disagreed by 5.0 bps on a 17.0-bps round trip — 29% of total cost — while both claimed to
use "the" Bybit cost stack.

**Mechanism (why).** A policy expressed as "callers should omit this argument" is invisible at the
place it is violated. The function's own docstring said explicit spread survived "only for
reproducibility of historical callers", but the live crypto CAL lane was a *current* caller, so
the escape hatch silently became the default for a whole subsystem. Worse, the guard that existed
— `verify_chapter05_spread_quarantine` — only checks that the *stored* `SpreadBps` column stays
flagged UNUSABLE. It cannot see a hardcoded constant, so it passed while the proxy was live.
Governance text scoped the rule to "Chapter-05 accounting", so nothing was formally broken; the
framework simply had two cost truths and no place where they had to meet.

**Fix / new rule.** A cost convention is enforced at the boundary or it does not exist.
`bybit_round_trip_cost_bps` now **raises** if any caller passes `spread_bps`;
`economics.check_cost_map_integrity` refuses a XENA universe whose declared `cost_scope` is
anything but `PARTIAL_FEES_FUNDING_ONLY`. Undeclared scope stays loadable (existing manifests
predate the field) but a *wrong* declaration is refused — one universe may not mix conventions.
Corollary: changing a cost stack invalidates every calibration measured against it. Retiring the
proxy moved the synthetic round trip 17.0 → 12.0 bps under net-binding stage-1, so the accepted
Bybit CAL pin was marked STALE and must be re-measured before it authorises another search or gate.

**Enforced at.** `xen.evaluation.bybit_round_trip_cost_bps`,
`xen.xena.economics.is_valid_cost_scope` / `check_cost_map_integrity`,
`tests/test_evaluation.py::test_bybit_round_trip_refuses_to_charge_spread`,
`tests/test_xena_economics.py::test_cost_map_refuses_a_universe_declaring_spread_in_scope`.

---

## L-49 — A rate × magnitude decomposition is only valid when wins and losses are the same size; near a coin-flip rate the payoff asymmetry carries the sign ⭐

**What.** The exact decomposition of a signed per-trade return is

```
E[gross] = p·W − (1−p)·L        W = E[r | r > 0]      L = E[−r | r < 0]
```

This reduces to the familiar `(2p − 1) × E[|move|]` **only when `W = L`**. Whenever wins and losses
differ in size the two forms diverge, and near `p ≈ 0.5` the rate term contributes almost nothing —
**`W/L` carries the sign of the mean**. A design that reads only the rate will book a positive-mean
cell as a null, and a budget built on the rate×magnitude form will be wrong by whatever the payoff
asymmetry is worth.

A second, related error: multiplying by a capture ratio such as `κ = median(r / mfe)`. `E[|move|]`
is *already* the realised hold-to-horizon magnitude; κ is a **ceiling-relative diagnostic** against
an in-window peak that peeks. Realised magnitude × peak-relative ratio is a quantity with no
referent.

**Mechanism (why).** "Hit rate times average move" *feels* like an expectancy formula, and it is the
shape most trading folklore uses. It silently assumes a symmetric payoff. Any strategy with a
path-dependent exit — a stop, a target, a trail, a time cap — deliberately breaks that symmetry;
that is what those devices are *for*. So the one decomposition that cannot describe a
capture-geometry programme is the one that assumes the capture geometry does nothing. The error is
self-concealing: it agrees with the truth exactly at `W = L`, and its error grows precisely in the
regime such research is aimed at.

**Consequences.**

- The research target is **not** `p > 0.5`. It is `p > p_be_net = (L + cost)/(W + L)`, satisfiable
  at `p < 0.5` whenever `W > L`. Any gate, refusal, or band phrased against 0.5 is void.
- `W/L` is a **first-class, measurable degree of freedom**, not a residual. Exits, targets, stops
  and holds move it directly, so it is the natural handle for any capture-geometry branch — and it
  must be measured per cell *before* such a branch is designed.
- κ is a diagnostic ("what fraction of the best available point did the policy retain"), reported as
  non-tradable. It multiplies nothing.
- The martingale result survives intact and is sharpened: on a driftless path with a fixed-horizon
  exit `E[r] = 0` forces `p·W = (1−p)·L`, so `p` and `W/L` are locked together and a path-dependent
  exit trades one against the other **along the zero line**. Capture geometry redistributes the
  payoff; it does not create expectancy (cf. `CF-VOLHARV-001/HYP-001`, L-14).

**Fix / new rule.** Any design whose estimand is a signed per-trade return must (a) emit `p`, `W`,
`L`, `W/L`, `p_be_net` and `edge = p − p_be_net` per cell, (b) **assert the reconstruction
numerically** — `|p·W − (1−p)·L − mean| < 0.01 bps` — as an integrity check, not a report line, and
(c) state break-even against `p_be_net`, never against 0.5. A blended "opportunity score" may not be
reported without this term-level decomposition.

**Meta-lesson.** An organising identity registered in a checkpoint brief is load-bearing
infrastructure and deserves the same numerical verification as a cost model or a fill rule: check it
against emitted quantities on the first run that can, and prefer an identity that is **exact by
construction** over one that is merely intuitive. An identity that is only *usually* right is a
premise defect, and premise defects propagate into every downstream budget.

**Enforced at.** `.ignore/what-next/alts/opportunity.md` §2;
`docs/references/chapter-06-governance.md` §1b + §3;
`docs/signal-registry/candidate-families/cf-voldir-001.md` §0;
`docs/signal-registry/multiplicity-registry.md` AMENDMENT-C2;
`python/experiments/SPDR-018/design.md` §4.1 + §12 (identity-reconstruction integrity check).

---

## L-50 — A precision target stated in absolute units is not portable across universes with different volatility scales (SPDR-018B) ⭐

**What.** SPDR-018B carried SPDR-013/014's target-precision rule — **block MDE ≤ 10 bps** — unchanged
from the Bybit crypto universe (pooled σ̂ **73.00 bps**) onto the cTrader universe (pooled σ̂
**13.03 bps**). The rule looked identical. In σ units it was not: **0.137σ on crypto against 0.767σ on
cTrader — a silent 5.6× loosening.**

Three separate headline conclusions were wrong, all in the same direction:

| Figure | On the imported absolute bar | Re-derived at the σ-scaled bar (1.785 bps) |
|---|---|---|
| powered signed cells | 2,401 | **315** |
| cells clearing net break-even | 12.9% | **0.0%** |
| `W/L`-mirror fit R² | 0.311 — written up as "the mirror does not fit here" | **0.9746** — the mirror replicates *more tightly* than crypto's 0.9667 |

The third is the most instructive: a loosened power bar admitted ~2,100 noisy cells whose `log R`
scatter tripled the residual variance, and the resulting bad fit was then *explained* with a plausible
mechanism ("`W/L` has too narrow a dynamic range here"). **A wrong threshold produced a wrong number,
and the wrong number recruited a wrong story.**

**Mechanism (why it slipped through).** A target precision is a statement about a **signal-to-noise
ratio**, but it is written down in the units of the numerator alone. Once written, it looks like a
constant of the methodology rather than a property of the universe it was calibrated on — so it
travels. Nothing in the design references σ̂ at the point where the threshold is applied, so no
consistency check can fire, and the parent screen (which set the bar honestly for *its* universe)
looks like the authority. The defect is self-concealing in the favourable direction: a loosened bar
*increases* the powered-cell count, which reads as the powering experiment succeeding.

**Fix / new rule.**

- **State every precision, materiality and target threshold in σ̂ units, or re-derive it per universe
  at run time from that universe's own measured σ̂.** A threshold inherited across a universe boundary
  in absolute units is void.
- Emit the threshold **and its σ-equivalent** on every cell, so the two can never diverge silently.
- When two universes are compared, **assert that their bars are equal in σ units** as an integrity
  check, not a report line.
- **Power counts computed on different precision bases are not comparable** and must be labelled as
  such wherever they appear side by side.

**Relationship to L-21 / P-15.** Same class, one level up. L-21 pins the **normaliser object** (which
ATR, which clock) so that an effect size means what it says. L-50 pins the **threshold's units** so
that a *decision rule about* effect sizes means what it says. L-21 protects the numerator; L-50
protects the comparison.

**Meta-lesson.** A "true speed run" that reuses a parent's code and protocol verbatim inherits its
parent's **calibrations** as well as its logic, and calibrations are the part that does not travel.
When reusing a screen on new data, enumerate every constant in it and ask of each: *is this a property
of the method, or of the universe it was fitted to?*

**Enforced at.** `python/experiments/SPDR-018B/analysis.md` §2.2 + §9 (Finding 1);
`python/experiments/SPDR-018B/report.md` §2 + §10;
`docs/references/spdr-lane.md` (target precision must be σ-stated or re-derived per universe);
`docs/knowledge-base/pitfalls-ledger.md` **P-21**.

---

## L-51 — A precision gate is a dispersion gate, and on skewed P&L it is not sign-neutral (SPDR-018B)

**What.** SPDR-018B's powered subset contained **ten arm-B trailing-stop cells with gross means of
+7.13 to +22.97 bps**, every one with a bootstrap CI-low above zero, clearing every floor in the run.
They were drawn from a population of **116 excluded cells averaging −27.610 bps**. Their signature:
`p` **0.80–0.89** *together with* `W/L` up to **6.67** — arithmetically impossible for a stable
distribution, and the exact shape of a truncating exit whose loss tail has not yet fired.

**Mechanism.** A target-precision filter keeps cells whose **realised dispersion** is small relative
to `n`. On a fat-tailed, one-sided-truncated P&L distribution, *low realised dispersion is itself the
event of not having sampled the tail.* The filter is therefore correlated with the tail's absence, and
a trailing stop is precisely the device that concentrates all of a cell's loss into rare large events.
The gate selects the cells where the rare event has not happened yet — and those cells look like
skill.

**The refinement, which is the part worth carrying:** the bias direction follows the **population's
skew, not the gate**. On arm B as a whole the same gate ran the *other* way — excluded cells averaged
**+6.63 bps with 51.8% positive** against powered cells at **−0.14 bps with 28.7% positive**. So a
dispersion gate is not reliably optimistic; it is reliably **non-neutral**, and its direction must be
measured, never assumed.

**Two further facts that keep this honest.** (a) The named instance is now **moot** — 0 of those 126
cells survive the corrected σ-scaled bar (L-50), so fixing the portability defect deleted this
artifact's own example. (b) The mechanism is nonetheless general, and the same population reappears
elsewhere: **99 of the 159 native B3 "positive-mean" cells are `trail`/`stop`**, all unpowered.

**Fix / new rule.** Before any powered subset's **magnitudes** are read, emit the **three-number
selection check** comparing powered against excluded cells:

1. **payoff-scale ratio** — median `(W+L)` powered ÷ excluded (SPDR-018B: **0.43** — the gate halved
   the payoff scale);
2. **sign-share differential** — share of positive-mean cells, powered vs excluded (**28.7% vs
   51.8%**);
3. **mean-vs-median gap in the excluded set** — the unfired-tail indicator (**32 bps**).

Any powered subset drawn from a fat-tailed population is a **selected** sample, and its magnitudes are
uninterpretable until this check is reported. A per-cell CI does not protect against this: all ten
cells had CI-lows above zero.

**Meta-lesson.** Power filters are usually treated as neutral hygiene — "we only read cells we can
measure". They are a **selection rule on the outcome's own second moment**, and on skewed data the
second moment is not independent of the first. Any filter applied to cells *after* their outcomes
exist needs the same scrutiny as a signal.

**Enforced at.** `python/experiments/SPDR-018B/analysis.md` §8 + §9 (Finding 2);
`python/experiments/SPDR-018B/report.md` §7; `docs/knowledge-base/pitfalls-ledger.md` **P-22**.

---

## L-52 — A declared check that depends on transient state silently does not run, and "checks held" without a count cannot detect it (SPDR-018 / SPDR-018B) ⭐

**What.** **Four** failures across one build shared a single cause: a check that was declared, believed
to be running, and not running — while the run reported success.

| # | Failure | How it hid |
|---|---|---|
| 1 | **SPDR-018 `TRIPWIRE-2` and `Determinism`** — both declared HARD in design §12 | TRIPWIRE-2 was absent from the self-check entirely; determinism was silently emitted as `INFORMATIVE` with the detail *"parallel-vs-sequential comparison not requested this run"*. `screen.md` §9 said **"Deviations: none"** |
| 2 | **SPDR-018B arm-C controls** | A resumed run left the in-memory arm-C panel empty; the controls computed over nothing and reported success |
| 3 | **SPDR-018B post-run fixes** | `panel_C.parquet` had been deleted and was never persisted, so a later stage silently had no input |
| 4 | **SPDR-018B ambient-base + `TRIPWIRE-1/2/3`** | Appended by a manual post-step (`add_missing_controls.py`), then **wiped** when a later re-run regenerated `controls.json` and `integrity_selfcheck.json` from scratch |

Failure 4 was caught **only by manually counting HARD entries** — 8 against the expected 11. Nothing
else in the pipeline would have noticed, because every artifact was internally consistent and every
surviving check passed.

**Mechanism.** Two distinct dependencies, one symptom:

- **Transient state.** A check whose input is an in-memory object cannot distinguish "verified" from
  "there was nothing to verify". An empty panel passes every assertion over it.
- **Regenerated artifacts.** A check appended to a file that a later stage rebuilds from scratch is
  deleted by a *successful* run of that stage. The more reliably the pipeline reproduces its outputs,
  the more reliably it erases the manual additions.

And one reporting defect that made both invisible: **"18 HARD checks, 0 failed" is a statement about
the checks that exist, not about the checks that were declared.** It is literally true and materially
incomplete. A count-free "all HARD checks held" is strictly worse — it cannot even be audited.

**Fix / new rule.**

- **Every check must depend on an emitted artifact**, not on in-memory state. If the artifact is
  missing or empty, the check **fails**; it does not pass vacuously.
- **Assert the expected NUMBER of checks** as a HARD check in its own right, and reconcile the
  self-check against the design's declared list **by name**. A declared-but-absent check is a
  failure, not a silence.
- **No check may live in a manual post-step.** If it is required, it is in the runner. (Outstanding
  work: `SPDR-018B/screen_code/add_missing_controls.py` is still a manual post-step that any re-run
  silently undoes.)
- Determinism must execute **unconditionally whenever `--jobs > 1`, independent of `--resume`** — a
  resumed run is exactly the case it exists to catch, and is the case where it was skipped.
- Analysts must audit **declared-HARD vs actually-emitted, with counts**, as a Phase-0 step. Doing so
  is what caught items 1 and 4, and enumerating SPDR-018B's **seven missing inherited HARD checks**.

**Meta-lesson.** An integrity system's failure mode is not a check that fails — that is the system
working. It is a check that **does not exist while everyone believes it does**. Design the reporting so
that absence is loud: counts, names, reconciliation against the declared list. Trust no summary
statistic over a set you have not enumerated.

**Enforced at.** `python/experiments/SPDR-018/analysis.md` §1.1 + §1.2 and its ADDENDUM;
`python/experiments/SPDR-018B/analysis.md` §1.1; `python/experiments/SPDR-018B/report.md` §9.1 + §11;
`python/experiments/SPDR-018B/screen_code/run18b.py` (persists `panel_C.parquet`; guard
parameterised); `docs/knowledge-base/pitfalls-ledger.md` **P-23**.

---

## L-53 — A deflator or normaliser derived from a selected subset is circular, and its range must be reported (SPDR-018B)

**What.** SPDR-018B's cross-universe cost deflator was derived from **realised payoff scale**, median
`(W+L)`, giving arm B **0.2611** and arm C **0.3118** — a defensible improvement over the ~2×-wrong
bar-volatility ratio it replaced. But the payoff scales were computed on the **absolute-powered cell
subset**, i.e. the very selection that the L-50 precision correction invalidated.

Recomputed on other defensible bases, the same statistic gives:

| Basis | arm B | arm C |
|---|---|---|
| absolute-powered subset (**as shipped**) | 0.261 | 0.312 |
| corrected σ-scaled powered subset (315 cells) | **0.185** | 0.196 |
| all signed cells | **0.703** | 0.386 |

```
DEFLATOR: defensible range 0.185 - 0.703  ->  a factor of 3.8, i.e. +/-2x on EVERY net figure.
```

**Mechanism.** The deflator calibrates the cost charge; the cost charge enters `p_be_net`; `p_be_net`
is one of the quantities the powered subset is selected and then judged against. Deriving the deflator
*from* that subset closes the loop. The circularity is invisible because each step is individually
reasonable and the artifact records only the final ratio, with no statement of what it would have been
on any other basis.

**Why it did not change the conclusion, and why that is luck rather than method.** The headline read —
**0 of 315 powered cells clear net break-even** — is robust because the best powered cell earns
**+1.389 bps gross**, and the deflator at which that cell exactly breaks even is **0.1785**. The
conclusion therefore survives the defensible range **but only by 4%** at its lower bound (0.185 vs
0.1785) — at a deflator of 0.165 two cells clear and at 0.06 thirty-two do. The margin is thin, not
comfortable, and the earlier "~0.06" figure in this lesson was wrong. The conclusion survives
the entire defensible range. Had the best cell been near the charge, the deflator's factor-of-3.8
ambiguity would have decided the result.

**Fix / new rule.**

- **A deflator, normaliser or cost scale may not be derived from a subset that is itself selected by a
  quantity the deflator feeds.** Derive it on the full emitted population, or on a subset defined
  without reference to the outcome.
- **Report the deflator's range across every defensible basis**, and state which conclusions are
  invariant to it and which are not. A single point value is an under-specification.
- Any **cross-universe comparison of net magnitudes** is void while the deflator is unidentified.
  Gross remains primary. (Compounding disclosure for SPDR-018B: the cost is also **doubly
  synthetic** — borrowed from Bybit and rescaled — and spread is never charged at all, programme-wide
  since 2026-07-23, so both universes' net figures are overstated by unquantified amounts.)

**Meta-lesson.** Cost and normalisation constants are usually treated as inputs fixed before the
analysis, so nobody re-audits them once results exist. When such a constant is *estimated from the
data*, it becomes part of the model and inherits every selection applied to that data. Estimated
constants need provenance, a basis statement, and a sensitivity range — the same as any other
estimate.

**Enforced at.** `python/experiments/SPDR-018B/analysis.md` §2.3;
`python/experiments/SPDR-018B/report.md` §6; `python/experiments/SPDR-018B/results/deflators.json`.

---

## L-54 — Profile Python retention and Nautilus defaults as one critical path; compiled work can still be irrelevant work (SPDR-021/022/023 amended rerun)

**What.** A corrected SPDR-022 crypto unit projected nearly ten hours at one worker. The main
causes were neither the research grid nor an inherently slow Python interpreter:

- 3,625,870 future schedule rows were expanded into retained Python dictionaries before replay
  (9.327 s, 8.410 GB RSS);
- Nautilus's compiled portfolio/accounting path recalculated one shared margin account after every
  fill even though the experiment measures independent arms and emits no shared-account estimand;
- completed entry IDs and terminal episode keys remained in Python sets for the full run;
- publication/resume hashing allocated each entire Parquet file as one Python `bytes` object.

Columnar ordered consumption reduced schedule initialisation to 0.509 s and 3.474 GB. Freezing the
irrelevant shared account reduced a 2,000-arm replay from 27.016 s to 5.945 s with all four Parquet
hashes equal. A full BTCUSDT replay finished in 428.245 s at 5.749 GB RSS and reproduced the prior
orders, fills, positions and state ledger byte-for-byte (827,105 / 796,647 / 398,388 / 4,767,815
rows). Terminal guards are now released, unused Nautilus post-run analysis is disabled, and hashes
stream through `hashlib.file_digest`.

**Mechanism.** “Python is slow” and “the engine is compiled” are both too coarse to guide work.
Performance is the combined live path: columnar inputs → Python objects → Nautilus subsystems →
Pandas/Polars reports → artifact hashing. An operation can be fast in isolation or implemented in
Cython/Rust and still dominate because the experiment never consumes its result. Conversely, a
single eager Python conversion can make safe parallelism impossible even when CPU is idle.

**Fix / new rule.** Before every large Nautilus run:

1. time and measure RSS for preparation, child replay, report extraction and publication separately;
2. audit `to_dicts`, retained `iter_rows(named=True)`, large `to_list`, `read_bytes`, repeated joins,
   prefix recomputation, and lifecycle sets/maps without release;
3. inventory Nautilus defaults (`frozen_account`, `run_analysis`, risk, message queues, cache/report
   behavior) and disable only work proven outside the estimand;
4. size workers from parent + child + publication live sets, not child RSS alone;
5. require test-first edge fixtures, exact artifact/key/value parity, one representative full-unit
   replay, wall/RSS before-after, and clean/resume/parallel hashes;
6. port to Rust only after profiling isolates a stable pure-Python kernel and vectorised/columnar
   routes are exhausted; use a pinned bit-parity corpus as in INFR-007.

Never trade away fences, dates, symbols, origins, arms, event order, draws, precision, rows or
schemas for speed. The deferred cache-purge/report-streaming rewrite remains a separate governed
change, not an excuse to bypass this proof.

**Enforced at.** `python/src/xen/adaptive_management/{strategy,engine,runner}.py`;
`python/tests/test_adaptive_management_{strategy,runner}.py`;
`docs/superpowers/plans/2026-08-03-spdr-critical-path-performance-review.md`;
`docs/knowledge-base/pitfalls-ledger.md` **P-26**.

---

## L-55 — Repeated deterministic analysis is a shared-work problem before it is a faster-language problem (SPDR-023 amended rerun)

**What.** SPDR-023 crypto analysis was stopped after its live stack landed in the native-origin
bootstrap. For every arm, the analyser recomputed `ALL` and each state separately even though all
calls used the same origin population, block partition, seed and ordered random draws. It also
filtered an 88.3-million-row symbol-major episode ledger by exact membership without exposing
simple bounds to the Parquet reader; 695 of 719 row groups contained only one symbol.

The correction builds the partition and draw positions once per arm, then applies each column's
unchanged NumPy mean to those positions. Nullable columns retain the independent reference path.
Ledger scans now add inclusive min/max bounds while retaining the exact membership predicate.
The bootstrap probe improved 0.543 → 0.202 seconds (2.69×); a warm PYTHUSDT scan improved
0.0108 → 0.00330 seconds (3.27×), with 237,974 rows on both paths. Full SPDR-023 cTrader analysis
improved 1,056.134 → 539.170 seconds and reproduced all 13 canonical SHA-256 hashes exactly.

**Mechanism.** Determinism often creates reusable work: reset seeds and identical populations mean
separate-looking estimates may traverse the same sample positions. Likewise, exact key filters can
remain exact while carrying redundant bounds that let a columnar reader skip impossible row
groups. Porting the inner loop to Rust would preserve the duplicated work and add a parity surface;
removing the duplication attacks the measured cause with less code.

**Fix / new rule.** On long deterministic analyses, inspect repeated groups for identical
population, partition, seed and draw order. Share only the proven-identical positions, preserve each
metric's original arithmetic, and retain a reference fallback outside that domain. For sorted or
symbol-major Parquet, add pruning predicates only as conjunctions with the authoritative exact key.
Acceptance requires test-first edge cases, exact estimates/intervals, a representative full replay,
all artifact hashes equal, and an explicit memory measurement.

**Enforced at.** `python/src/xen/adaptive_management/analysis.py`;
`python/tests/test_adaptive_management_analysis.py`;
`docs/superpowers/plans/2026-08-03-spdr-critical-path-performance-review.md`;
`docs/knowledge-base/pitfalls-ledger.md` **P-27**.

---

## L-56 — A detection floor and the effect it judges must share a scale, and where the estimand is pinned to a known ratio the ceiling is computable BEFORE the run (SPDR-024) ⭐

**What.** The first SPDR-024 emission returned "unresolvable" on essentially every read across all
four cells. The cause was not thin data. The detection floor was `MDE_Z / √n` with `MDE_Z = 2.8`
(`spdr024_analysis.py:31`, `:392`), while the effect it judged was a σ̂-normalised paired difference
on a pure SIZE device. For that device the normalised estimand is arithmetically **pinned to the
baseline's per-trade Sharpe ratio** — 0.032 to 0.059 in these cells. Clearing a floor beneath that
ceiling needs **2,270–7,501 independent blocks**, and only **one of four cells** had them. Three of
four cells could not resolve anything **before the run started**, by arithmetic that was computable
at design time and was not computed.

Four inflations compounded on top: the yardstick was built from estimates themselves declared
unresolved; `2.8` — a **sample-size target** — was used as a **significance bar** beside a bootstrap
SE the floor ignored; two channels with different σ̂ denominators (`paired_delta` for scale,
`outcome_level_bps` for selection) were read on one shared numeric ladder; and the pre-execution
power gate used a different standard from the post-execution ladder.

**Mechanism (why).** A power constant and a test threshold answer different questions. `MDE_Z = 2.8`
encodes "how many observations do I need to have an 80% chance of seeing an effect of size δ" — it
is a *planning* quantity about a hypothetical future sample. A significance bar asks "is *this*
realised estimate distinguishable from zero given *this* sample's dispersion". Substituting the
first for the second silently imports the planning constant's conservatism into every realised read,
and — the load-bearing part — does so **on a different scale from the estimate**, because the
planning constant divides `√n` while the estimate is normalised by a σ̂ the constant never sees. The
mismatch is invisible in the code because both quantities are dimensionless floats. It becomes
visible only when you write down the estimand's algebraic ceiling, which for a size-only device
reduces to the baseline Sharpe and can therefore be evaluated from the baseline alone.

The failure is **universal rather than selective** — every read fails, not the marginal ones — and
that universality is the diagnostic signature. A floor calibrated to the data fails *some* reads. A
floor on the wrong scale fails *all* of them, which is what should have prompted the check.

**Fix / new rule (AMENDMENT-7 R1–R5 — [superseded-for-live-use (INFR-022 L-63): the MDE
floor apparatus is retired programme-wide; the surviving core — sample-size is context,
never a gate (N3), direct comparisons only (N4), no machine value labels (N11), and the
leak tripwire on `INTEGRITY_Z × bootstrap_SE` (N6b) — is codified in
`docs/references/neutrality-standard.md`].)**
1. **R1/R5** — preflight power counts and any historical observed-effect band are **context only**,
   never gates and never thresholds on a realised estimate.
2. **R2** — a detection floor must be built from the **same SE family as the row's own CI**:
   `mde = MDE_Z × bootstrap_SE` of the same estimator. Never a parametric `k/√n` beside a bootstrap
   interval.
3. **R3** — no row is dropped, demoted, or labelled by its floor. `MDE_Z` is context; the words
   `WASH` and `UNPOWERED` as row verdicts are withdrawn.
4. **R4** — every channel declares its `sigma_denominator`. Channels with different denominators
   may **never** be ranked against each other on a shared numeric ladder.
5. **Design-time ceiling check (the new one):** where the estimand's algebraic maximum is a function
   of quantities knowable before the run — a Sharpe ratio, a bounded rate, a fixed multiple —
   compute the ceiling and the implied block requirement **in the design**, per cell, and record
   whether each cell can resolve anything at all. A cell that cannot must be declared incapable
   before it runs, or dropped.

**Enforced at (live, post chapter-05 archive).**
`.claude/skills/data-analyst/SKILL.md` Phase 2 +
`.claude/skills/data-analyst/references/interrogation-protocol.md` (analysis-time floor/ladder
rules R1–R5);
`.claude/skills/quant-designer/references/design-requirements.md` §6 (design-time ceiling +
same-SE floor contract);
`docs/knowledge-base/pitfalls-ledger.md` **P-28**;
`docs/knowledge-base/methodology-canon.md` (Chapter 05 additions).

**Historical (chapter-05 archive only — not live imports).**
`archive/chapter-05-voldir-capture-geometry/python-src/adaptive_management/spdr024_analysis.py`
(floor construction and `sigma_denominator` declaration);
`archive/chapter-05-voldir-capture-geometry/experiments/SPDR-024/design.md` §10/§11.

---

## L-57 — A control that reproduces the real estimate exactly has never tested anything; assert that the control DIFFERS (SPDR-021/022/023, X-09)

**What.** `TIME_DERANGEMENT` returned **the identical number to the real estimate on 100% of rows in
all six cells**. It had been carried as a live control across multiple experiments and reported as
held. It tested nothing at any point.

**Mechanism (why).** A control earns its status by being a *different computation on deliberately
broken input*. When the derangement is applied to a quantity that is invariant to the thing being
deranged — here, a per-trade value that does not depend on the time ordering the derangement
permutes — the "control" is the identity function with extra steps. Nothing in a pass/fail harness
notices, because a control that equals the real estimate does not fail: it agrees. The check reports
green precisely because it is vacuous. This is the same family as the chapter-02 finding that
permuting realised P&L cannot collapse a mean-stat referee.

**Fix / new rule.** Every control must carry a **non-degeneracy assertion**: the control statistic
must differ from the real statistic on a stated minimum share of rows, and that share is itself a
HARD check. A control whose output equals the real estimate is a **failed control**, not a passed
one. `TIME_DERANGEMENT` is **removed** (`REMOVED_OD17`), not fixed.

**Enforced at.** SPDR-024 HARD set (`time_derangement_absent` — its removal is asserted, so it
cannot silently return); `docs/knowledge-base/pitfalls-ledger.md` **P-29**; companion to **L-52**
(assert the check *count*) — this one asserts the check has *content*.

---

## L-58 — A device that changes only WHICH trades happen cannot change WHAT the shared trades are worth (SPDR-021/022/023, X-02)

**What.** Native admission rules — entry threshold, order expiry, breach band `H` — moved the value
of shared trades by **exactly zero on ~2.3 million paired trade rows**. Not "within noise": zero.
The one apparent exception, `BAND_Z`, is a **price offset**, not an admission rule, and does move
outcomes.

**Mechanism (why).** An admission rule is a predicate over origins. It partitions the origin
population into taken and not-taken; it does not touch the price path, the entry price, or the exit
of any trade that both arms take. So for the intersection of two arms' trade sets, every outcome is
identical by construction, and a paired difference over that intersection is exactly zero as an
algebraic fact, not a measurement. Reading such a device on a **trade lens** therefore measures
nothing and consumes the whole budget doing it. The effect, if any, lives entirely in the
composition of the taken set — which is an **origin-lens** quantity.

**Fix / new rule.** Classify every device before it is emitted as **admission** (changes the origin
set) or **valuation** (changes what a trade is worth). Admission devices are read on the **origin
lens only**, with non-fills carried at their counterfactual value, never dropped. A paired trade-lens
read on an admission device must be declared void in the design, not discovered empty in the
analysis. Where a parameter does both — a price offset that also gates — say so explicitly.

**Enforced at.** SPDR-024 emission contract `E2` (counterfactual outcome for excluded origins);
`.claude/skills/quant-designer/design-requirements.md` (device classification block);
`docs/knowledge-base/pitfalls-ledger.md` **P-30**.

---

## L-59 — A screen that GATES BY a state but never LABELS realised state cannot answer any question about that state (SPDR-021/022/023)

**What.** All six cells of SPDR-021/022/023 gated their arms by volatility state. None of them
recorded the **realised** regime on the origin or the trade. Every regime-conditional question was
therefore unanswerable — not underpowered, **unaskable** — and this was only discovered at the
confirmation-extraction stage, after the runs.

**Mechanism (why).** Gating writes state into the *control flow* and then discards it. The emitted
row records what the arm did, not what the world was doing when it did it. Downstream, a regime
question needs the state as a **column**, and no amount of analysis recovers a column that was never
written — the decision-time state is not reconstructible from the outcome, and reconstructing it
post hoc from features would use a different clock than the one the gate used, silently introducing
look-ahead.

**Fix / new rule.** If a design gates on a state, it must **emit that state as a labelled column**
at decision time (`E1`), on the origin and inherited by every resulting fill. Gating without
labelling is a design defect caught at QA, not a limitation disclosed in analysis.

**Enforced at.** SPDR-024 emission contract `E1` + HARD check `e1_regime_label_present`;
`.claude/skills/qa-compliance/SKILL.md` (gate-implies-label check).

---

## L-60 — A per-notional estimand is arithmetically blind to sizing, and the exact zero it returns is not a null (SPDR-021/022/023)

**What.** The paired SIZE delta was exactly `0.000000` on **1,400 of 1,400 rows in all six cells**.
The primary estimand — per-trade bps — is per-unit-notional. The one device that survived every
other refutation was measured by an instrument that cannot see it.

**Mechanism (why).** Normalising a return by the position's own notional divides out the size term
by construction. Halving size halves both numerator and denominator. The result is not a small
effect or a noisy one; it is an algebraic identity, and it reports as a clean, confident,
tightly-CI'd zero — the most convincing-looking null in the study, and entirely an artifact of the
unit. A reader who does not check the estimand's units reads it as evidence that sizing does not
matter.

**Fix / new rule.** Any claim about **sizing, exposure, or capital efficiency** requires a
**capital-normalised** estimand (`E6`), never a per-unit-notional one. More generally: before
accepting a null, verify the estimand is capable of expressing the effect — an exact zero across
100% of rows is a **units alarm**, not a result. This is the sizing-specific instance of the
programme rule that no expectancy claim may come from exits or sizing on an estimand that cannot
represent them.

**Enforced at.** SPDR-024 emission contract `E6` + HARD check
`e6_capital_normalised_estimand_present`; `docs/knowledge-base/pitfalls-ledger.md` **P-31**.

---

## L-61 — A pooled figure over three instruments is one instrument (SPDR-021/022/023, X-10)

**What.** The pooled cTrader native-geometry number is XAUUSD. Dropping that single instrument
**flips the pooled sign**.

**Mechanism (why).** Pooling weights by event mass, and on a three-instrument panel one high-
volatility, high-event-count instrument can carry a majority of the mass. The pooled statistic is
then a disguised single-instrument statistic wearing the credibility of a panel. The failure is
invisible in the pooled number itself — it looks like a three-instrument result — and is exposed
only by leave-one-out. This is the small-panel case of the standing per-stratum rule: pooled figures
are disclosure-only.

**Fix / new rule.** On any panel with fewer than ~10 strata, report **leave-one-out sign stability**
alongside every pooled figure, and state the mass share of the largest contributor. A pooled sign
that does not survive leave-one-out is not reported as a panel result. Three instruments remain a
**replication instrument, not a substrate** — the cTrader universe's role (credibility, never
pooled `n`) is unchanged from **AMENDMENT-C1/S1**.

**Enforced at.** `.claude/skills/data-analyst/SKILL.md` (leave-one-out disclosure on small panels);
`docs/knowledge-base/methodology-canon.md` (per-stratum non-pooling).

---

## L-62 — The programme runs a ZERO-COST model; cost parameters are inert and every report carries the caveat (INFR-022)

**What.** INFR-022 (2026-08-08) retired the cost model programme-wide: no spread, commission,
or swap enters any calculation in any experiment type unless an explicit operator cost
directive requests costs (recorded in the design before execution). The retired stack
(`bybit_round_trip_cost_bps`, FTMO table, funding stamps, `spread_scale_route`, the
`PARTIAL_FEES_FUNDING_ONLY` scope, the A-4 net-informational gate run, the NET selection
path) moved to `xen/evaluation_cost_legacy.py` under an ARCHIVED banner.

**Mechanism (why).** Cost assumptions were the largest unmeasured overlay in every
money-bearing read: partial scopes understated cost, net reads implied a measurement that
did not exist, and every report needed a bespoke caveat that drifted. A single programme-wide
zero-cost model with a canonical verbatim caveat removes the drift and the implied claims
while keeping deployability refused by rule.

**Fix / new rule.** Default `NO_COST_CHARGED` everywhere; `cost_bps == 0` is a compliant pin;
non-zero `--cost-bps` / `charge_costs=True` raise without an operator cost directive
(`operator_cost_directive.json` + design clause; QA traces both). Every money-bearing report,
analysis, screen and results artifact carries the ZERO-COST-DISCLOSURE caveat verbatim (§3.1).
"Zero" is a model, never a measured zero.

**Enforced at.** `xen.evaluation.assert_zero_cost`/`zero_cost_caveat`;
`xen.estimand_validation` `no_cost_charged` blocking check;
`xen.xena.economics.check_zero_cost_compliance`; oracle directive gate;
`xen.xena.ingest` zero-cost asserts; `docs/references/neutrality-standard.md` § N9.

## L-63 — Powering is stripped to sample-size context + direct baseline comparison; MDE and floors are not live apparatus (INFR-022)

**What.** All MDE-type and every other powering method are retired from live designs, code,
artifacts and reports: `mde`, `powered_label`, `power_layer`, `structural_label`, detection
floors (`2.8/√n`, `MDE_Z × SE` on research estimands), mechanism ceilings, power curves,
`min_powered_seeds` / `n_legs_floor` vetoes, `at_or_above_p95`, and machine labels
(`UNPOWERED`/`WASH`/`CLEARS_FLOOR`/…). Retained: sample-size **context** (never a hide/drop
rule) and DIRECT comparisons against a pre-specified baseline model.

**Mechanism (why).** Power constants answer a planning question about a hypothetical sample;
using them as row gates on realised estimates silently imported planning conservatism on a
different scale (the L-56/SPDR-024 defect class). The AMENDMENT-7 apparatus fixed the
scale-mismatch but kept the concept; INFR-022 removes the concept from the value path
altogether and keeps only the two honest uses: context counts and a fixed comparator.

**Fix / new rule.** Designs state expected counts and optional minimum-n for
*primary-inference language* (descriptive only — rows still appear with counts, N3/N10);
every arm is read against its declared fixed comparator (estimate + uncertainty + counts,
no threshold, N4). The leak tripwire's validity bite is `INTEGRITY_Z × bootstrap_SE` of the
same estimator (N6b) — never called MDE.

**Enforced at.** `xen.evaluation` (symbols removed); `xen.xena.report_layer.sample_size_layer`;
`xen.xena.controls.sign_battery` (no power labels); `xen.xena.score` (no floor vetoes);
`docs/references/neutrality-standard.md` (powering-strip definitions); skills denylist (§10).

## L-64 — PSR is the paired companion of every mean-trade/leg bps read (INFR-022)

**What.** Probabilistic Sharpe Ratio (Bailey & López de Prado 2012, skew/kurt-adjusted,
empirical moments, per-trade series) is reported beside every mean trade/leg return in bps,
on the same series and population: `psr` + `psr_n` (NaN + n when n < 2 or moments
non-finite — the row still appears, N3). PSR is evidence, never a gate.

**Mechanism (why).** A mean bps alone says nothing about sampling confidence; a raw Sharpe
assumes normality. PSR gives the sampling probability that the true per-trade Sharpe exceeds
SR* using the same series the mean came from — no annualisation ambiguity by default.

**Fix / new rule.** Wherever a mean trade / mean leg return in bps is reported, PSR + n sit
beside it (same vector that produced the mean; never another population's n). Code:
`xen.evaluation.psr` / `psr_row`; XENA report layer `psr_layer`; economics disclosure rows;
estimand `psr_summary`.

**Enforced at.** `xen.evaluation.psr` + unit tests; `xen.xena.report_layer.psr_layer`;
`xen.xena.economics._leg_gross_stats` (PSR beside `gross_mean_bps`);
`xen.estimand_validation` `psr_summary`; data-analyst protocol (pairing question).

## L-65 — Neutrality N1–N11 is the binding analysis contract (INFR-022)

**What.** The chapter-05 SPDR-021/022/023/024 analysis records' common discipline —
no-verdict boundary, observed-vs-inference labels, counts as context, direct comparisons,
populations named and separated, informative controls, symmetric evidence, analyst
independence, the cost caveat on every document, completeness, operator-only value labels —
is codified verbatim as N1–N11 in `docs/references/neutrality-standard.md` and bound into
every analysis/screen/report skill contract.

**Mechanism (why).** Neutrality was achieved by repeated hard-won convention; each new
analyst had to re-derive it, and each new artifact risked a label, a gate, or a hidden row
that the convention would have forbidden. Codifying it as binding text with a single source
of truth makes the convention checkable (QA, denylists) rather than aspirational.

**Fix / new rule.** `analysis.md` / `screen.md` / reports open with the N1 boundary statement,
label observed vs inference (N2), report every row with its count (N3), compare against the
declared comparator (N4), name populations (N5), keep controls informative (N6) with the
N6b tripwire exception, end with "what would make these numbers wrong" + probe hand-off
(N7), stay analyst-independent (N8), carry the zero-cost caveat (N9), hide nothing (N10),
and leave value labels to the operator (N11).

**Enforced at.** `docs/references/neutrality-standard.md`; `data-analyst` SKILL.md +
interrogation-protocol template; `quant-designer` bands; `experiment-documenter` rules;
`research-pipeline/_pipeline-config.md` (binding sections).
