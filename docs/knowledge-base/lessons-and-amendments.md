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
limit is `rct_target[di-1]` (`EXP-090/code/run_experiment.py:305-310`,
`mean_reversion.py:174`). This one-bar look-ahead inflated the captured edge by **~+0.25
ATR/trade**. Causalized, the bare RSI-2 fade is net-negative even gross. It slipped past a
sophisticated auditor because (a) the leak lived in a **shared vectorized outcome module**
feeding the "favourable target," and (b) the audit's verdict-forensics **re-derived the
numbers from the same contaminated module**, so the biased numbers reproduced perfectly.
**Numeric reproduction is structurally blind to acausal provenance.** It was finally exposed
only by the cTrader port + forward test (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`).

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
