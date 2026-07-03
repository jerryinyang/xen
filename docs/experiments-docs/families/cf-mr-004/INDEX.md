# Family Index — CF-MR-004 (Cross-Domain Mean-Reversion, fixed-parameter cross-instrument spreads)

Cross-instrument spread MR fade: capture an instrument's deviation from a higher-domain
**cross-instrument anchor series** (a price-derivable, invertible spread), entering with precalculated
resting limit orders and exiting on reversion to the anchor mean. Registry:
`docs/signal-registry/candidate-families/cf-mr-004.md`. Governing checkpoint:
`docs/experiments-docs/checkpoints/2026-07-01-004-cross-domain-mr-renewal/`.

**Status:** **RETIRED (2026-07-03, operator D1) — EXP-014c CREDIBLE_NEGATIVE_RETIRE.** Final arc:
EXP-014b (HYP-003) collapse-verified the availability to 4h JP225 + weakly EURUSD and exposed the
moving-mean exit as a loss engine; EXP-014c (HYP-004) traded the exact measured two-barrier object
(frozen TP / outward SL / ⌈3·HL⌉ time-stop) on prespecified primaries and both failed powered +
bite-valid — the confirmed availability does not convert because the traded **entry** (limit fill
at the band touch) is a different conditioning event than the measured one (open after confirmed
close-breach); JP225 realized TP-share 0.52 vs measured 0.696. Exits exonerated. Fourth MR family
closed at the capture/attribution seam. **Spin-out:** the extend-arm own-price ladder field (53
non-admitted cells net ci_low>0, year-stable 2021–24, 50–85% shift-surviving) → **CF-MR-005
(REGISTERED 2026-07-03)**. Re-opening CF-MR-004 requires a confirmed-breach entry object under a
new D0. 0 slots, 0 counted reads, holdout sealed, referee untuned.

**Prior status (retained):** **NOT-TRADABLE (faithful; EXP-014, 2026-07-02) — RETIRE recommended, operator-gated.** Arc:
**EXP-013** screened NOT-TRADABLE but was **DOWNGRADED CONFOUNDED** (amendment 2026-07-02) — the strategy
that ran was not the one proposed (form-1 event-reversion exit absent; form-2 TP frozen at entry, never
refreshed as the moving anchor drifts → peer-side reversion never exits; the "~30% hit" was the static-TP
hit rate, not the reversion rate). **EXP-014 (HYP-002)** is the from-scratch faithful redo: **both
proposal-named exits fire** (form-1 + refreshing form-2), reentry none/allow/extend (multi-leg engine),
trend/vol conditioners, independent 6-stage MR characterisation booked pre-verdict. It **still closes
NOT-TRADABLE** — per stratum, 0/38 net- AND gross-admit under the frozen 4h referee (homogeneous, no
masking); availability does not separate at 4h (native reversion-completion Δ vs dislocation-matched control
ci_low<0 on ~all cells). Mechanism = **capture-vs-dispersion wash** (per-trade −57…+29 bps; net ci_low<0) —
the **same cost/capture veto** that closed CF-MR-002 (EXONERATED) and CF-MR-003 (RETIRED). L-14 (silent
dropped core exit) originated + discharged here. Referee untouched (L-12); 0 slots, 0 counted TEST reads,
holdout sealed.

## Table of contents
- [EXP-013 — HYP-001, screen (DOWNGRADED CONFOUNDED)](#exp-013)
- [EXP-014 — HYP-002, faithful full-exit redo (NOT-TRADABLE)](#exp-014)
- [EXP-014b — HYP-003, S8 symmetry availability + moving-mean tradability (REJECT_LEAK)](#exp-014b)
- [EXP-014c — HYP-004, lean bracket exit-set (CREDIBLE_NEGATIVE_RETIRE)](#exp-014c)

---

## EXP-013 — CF-MR-004/HYP-001: cross-instrument spread MR fade (Route-A native orders, 4h) {#exp-013}

- **Hypothesis Tests.** Does the precalc limit-order cross-instrument MR-fade (4 series S5/S6/S7/S8) produce
  availability + net edge per stratum on TRAIN under the frozen 4h referee?
- **Scope.** Native cTrader pending orders (Mode=NativeOrders), 4h anchor, 4 series × 32 cells, first-49%
  TRAIN fence, cost on/off. Referee frozen (L-12).
- **Results / Observations.** As-run: spreads weakly mean-reverting (median VR≈0.90–1.06), 0/32 admit net
  and gross, 21/32 powered. **BUT DOWNGRADED CONFOUNDED (amendment 2026-07-02):** form-1 exit absent + form-2
  TP frozen at entry → the exit set was not the proposed one; the "~30% favorable-hit" was the static-TP hit
  rate, not the reversion rate. Leak tripwires vacuous on the null. Record retained (never deleted).
- **Hypothesis-Specific Conclusion.** **Vehicle-incomplete → NOT a family reading; terminal-branch prior NOT
  reinforced on EXP-013.** Superseded by the faithful EXP-014.
- **Hypothesis-Agnostic Observations.** Route-A native pending orders + fresh exact-CloseTime basket feed
  (no carry-forward) are the reusable price-primary substrate; fixed the CF-MR-003 F-1 timing artifact.
  Lesson **L-14** (a silently-dropped core exit ships a confounded verdict; the pre-exec gate must diff the
  implemented exit set against the proposal's named exits).

---

## EXP-014 — CF-MR-004/HYP-002: faithful full-exit cross-instrument MR (4h) {#exp-014}

- **Hypothesis Tests.** Does the **faithful** full-exit strategy — form-1 event-reversion **and** refreshing
  form-2 anchor-mean limit (horizon last-resort), reentry none/allow/extend, trend/vol conditioners — produce
  availability + net edge per stratum on TRAIN, and if not, **which leg fails where**?
- **Scope.** Price-primary in-engine (Mode=NativeOrders, m1 fills). 4 series × 4 arms (none-R primary /
  none-S A/B / allow-R / extend-R) = **152 cells, 0 failures**. 38 binding strata (none/R). First-49% TRAIN
  fence (= EXP-013 cutoffs), final-30% never loaded. Frozen 4h referee untuned; 0 counted reads, 0 slots.
- **Results / Observations.** **Both proposal-named exits fire** (primary 3445 trades: form-1 281 /
  **refreshing form-2 1898** / horizon 1266) → L-14 discharged. Binding referee: **0/38 net-admit AND
  0/38 gross-admit, homogeneous (no masking — 0 cells net ci_low>0)**; net −2.3…+0.9 bps/active. Availability
  does **not** separate at 4h (reversion-completion Δ vs dislocation-matched control ci_low<0 on ~all cells,
  max +0.036). Per-trade P&L a dispersed wash (−57…+29 bps; several cells +per-trade yet net ci_low<0). 6-stage
  MR screen (informative, booked pre-verdict): VR<1 broadly (S7/S8 baskets 0.27–0.37; S6 pairs near random
  walk, HL 139–3173). Audit PASS (0 Critical, 2 interpretation Warnings). Leak tripwires moot (0 admits);
  label-perm mean-invariant/vacuous.
- **Hypothesis-Specific Conclusion.** **NOT-TRADABLE (faithful, TRAIN).** The faithful full-exit fade is a net
  wash at 4h AND its availability does not beat matched-random — same cost/capture veto as CF-MR-002/003.
  Powered on the bite-passing cell subset (which also all reject); **RETIRE CF-MR-004 recommended (operator-
  gated).**
- **Hypothesis-Agnostic Observations.** Reusable multi-leg netting engine (reentry none/allow/extend, per-leg
  provenance) + rich per-bar/per-trade emission (`cis_trades`) + min-mate valid-basket rule. **Power caveat
  (L-12 mode-2):** the per-bar mean-referee is a partial gate-shape mismatch for a discrete, high-variance
  round-trip bracket — 19/38 cells cannot detect a planted +8 bps (amendment §7 vehicle-fit risk); a per-trade/
  episode-native referee variant would need its own predeclared FPR calibration + freeze before judging this
  family. Harness `prepare_cache_layout` `ln` made race-tolerant for bounded-concurrency dispatch (EXP-006 O3
  op-note closed).

---

## EXP-014b — CF-MR-004/HYP-003: S8 symmetry availability + moving-mean tradability (1h+4h) {#exp-014b}

- **Hypothesis Tests.** On S8 (basket−Median₉₀), does the outlier revert beyond a coin flip
  (symmetry two-barrier first-passage, null = 0.5) and does any single-leg (moving-mean exit;
  reentry none/allow/extend; z* 2.0/1.5) or both-leg config clear the frozen referee, per
  (cell, domain, arm, z*)?
- **Scope.** Price-primary in-engine (native orders, m1 fills), 11 cells × {1h, 4h}, EXP-013
  TRAIN fence. Frozen referee untuned; 0 slots, 0 counted reads.
- **Results / Observations.** **REJECT_LEAK — 0 TRADABLE / 220 strata** (audited; C1 per-stratum
  label logic + C2 both-leg spread-weighting fixed analysis-only; family outcome unchanged;
  p_inward re-derived exactly from raw). Every 1h availability raw-pass survives the peer-feed
  phase-shift → own-price auto-reversion, and the S8 basket *dilutes* it (EURUSD live 0.508 vs
  shift 0.688) → S8-at-1h retired. Collapse-verified availability only **4h JP225 (p_inward
  0.696, ci_low 0.638; replicated at z1.5) + weakly 4h EURUSD (0.589/0.520)** — not tradable
  there: the moving-mean exit is small form-2 wins vs large form-1 anchor-drift losses ≈ 0 gross
  (the moving-target loss engine). extend admits = own-price MR harvest (persists under shift).
  Both-leg: median-positive, mean-killed by the ~50-bar loss tail + N+1 legs of cost.
- **Hypothesis-Specific Conclusion.** Availability is real but narrow (4h JP225 ≫ EURUSD) and
  the moving-mean traded object is a different object than the measured race → HYP-004
  (EXP-014c): trade the measured object itself, the family's declared last shot.
- **Hypothesis-Agnostic Observations.** The two-barrier symmetry read is a clean availability
  instrument (ambiguous-bar rate ≈ 0 off-index). The moving-target loss-engine pattern
  (favorable-limit refreshed into drift) generalizes; frozen-bracket comparison is the right
  dissection tool. Extend-arm own-price harvest first flagged here (matured in EXP-014c → CF-MR-005).

---

## EXP-014c — CF-MR-004/HYP-004: lean bracket exit-set — trade the measured object (4h) {#exp-014c}

- **Hypothesis Tests.** Does the exit-set matching the measured two-barrier object — TP frozen
  at the entry-time anchor (E1), + SL at the symmetric outward barrier (E2), + ⌈3·HL⌉ time-stop
  (E3) vs the moving-mean E0 baseline — extract the collapse-verified 4h availability on the
  prespecified primaries (JP225, EURUSD), across reentry and z* characterisation axes?
- **Scope.** 4h only, S8 only, single-leg, 11 cells; E0 = reused 014b emissions (read-only);
  198 new native runs + 33 shift-twin runs; PRIMARY = (e3, none, z2.0) on JP225 + EURUSD,
  prespecified. Fence byte-identical to EXP-013 (audit-verified). 0 slots, 0 counted reads.
- **Results / Observations.** **CREDIBLE_NEGATIVE_RETIRE** (audit PASS, 0 Critical; every key
  number re-derived from raw emissions). Both primaries powered + bite-valid + net-fail (JP225
  +0.26 bps/bar, ci_low −1.84; EURUSD +0.28, −0.46); 0 Holm admits in the binding family; census
  NULL 218 / UNPOWERED 22 / NOT_TRADABLE 14 / NET_ADMIT 4 / REJECT_LEAK 4. **Entry-seam
  mechanism:** traded limit-touch fills (D = z*σ, adverse selection) vs measured
  confirmed-close-breach races — JP225 TP-share 0.52 vs 0.696; 20/32 TP fills without spread
  reversion; EURUSD 0/20 stops with spread reversion. **Attribution:** frozen TP recovers the E0
  loss engine; SL subtracts value; time-stop benign. **Extend-arm field:** 61 cells net ci_low>0
  (53 never admitted), all extend/allow, year-stable 2021–24, 50–85% shift-surviving; ladder-depth
  P&L gradient (US2000 L2 +26.3 bps/leg); NZDUSD survives 3× cost. US2000's shift "collapse" =
  L5-materiality flip on a CI-positive shifted edge → no construction-specific claim (W3
  collapse-fraction disclosure rule, KB lesson-candidate). JP225 residual P&L Asia-session-
  structural.
- **Hypothesis-Specific Conclusion.** **NO — family RETIRED (operator D1).** The measurement-
  matched bracket cannot extract the confirmed availability because the traded entry is a
  different conditioning event than the measured one; exits are exonerated. Re-opening requires
  a confirmed-breach entry object under a new D0.
- **Hypothesis-Agnostic Observations.** (1) Measure→trade translation must match the
  **conditioning event** (fill seam), not just the barrier object — a limit-touch entry is not a
  close-breach entry. (2) The extend-arm own-price ladder harvest is a robust cross-instrument,
  year-stable phenomenon → spun out as **CF-MR-005** (registered 2026-07-03; mechanism
  characterisation first, basket-free trigger). (3) Attribution controls must report collapse
  fractions alongside binary admits (W3). (4) E1-with-reentry-none is structurally vacuous (one
  open leg blocks re-arming for years).
