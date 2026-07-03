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
