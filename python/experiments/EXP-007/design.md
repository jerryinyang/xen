# EXP-007 — E6: P*-capable Referee Variant (referee renew, D-referee)

**Branch:** `main`. **Checkpoint:** Phase-001 §D0 + AMENDMENT (2026-06-29, E6 inserted before D-benchmark).
**Classification:** **analysis-only** (synthetic substrates + frozen referee primitives; generates no
price edge). **Reads/slots:** 0 counted TEST reads, 0 candidate slots, global holdout sealed.
**Consumes (frozen):** E0 `referee_adaptive.ROUND_TRIP_COST_BPS_17`; §10.3a `gate_stack_adaptive`/
`adaptive_row` (hash-pinned, `EXP-005/results/freeze_manifest.json`); frozen Chapter-01 suite
(`referee_calibration.py`). All three stay **BYTE-FROZEN** (regression-anchor proves it). The EXP-002
synthetic battery (`SHAPES`, `make_shape`, `mde_curve`, `dogfood_pass`, 32-strata grid) is the substrate.

## Question (one, falsifiable)

**Can an additive P*-capable adjudication path — §10.3a's exact leg logic (L1 rigid validity floor; L3
vs-naive; L5 pooled + studentized sub-pop) but with the STRATEGY LEG sourced from an injected
engine-realized per-bar net series instead of `position·market-return` — be FPR-recalibrated to
match-or-better the frozen suite's dogfood-negative FPR while keeping finite power on the
synthetic-positive, and frozen before any live read?** Else: record **"not constructible without losing
FPR control."**

Motivation (EXP-006 A2 / checkpoint AMENDMENT): both frozen gates consume `position·market-return`
only (`strategy_return_bps_turnover`/`strategy_return_bps`); §10.3a has **no `strategy_fn` seam**. A
CF-MR-002 intrabar engine-realized `P*` fill is a realized series ≠ `position·market-return`, so the
frozen gates structurally cannot adjudicate it, and the freeze forbids editing them. E6 supplies the
missing adjudication path **additively** so D-benchmark can report a faithful realized-fill verdict.

## What is built (analysis-only)

New module `python/src/xen/referee_pstar.py`:
- `gate_stack_pstar(returns, positions, realized_bps, *, domain, cost_bps, n_bootstrap, seed, q,
  split_index)` — a faithful mirror of `referee_adaptive.gate_stack_adaptive` with **one** change: the
  **signal leg** is `realized_bps` (the injected engine-realized per-bar net series, already
  cost-amortizable) instead of `strategy_return_bps_turnover(returns, positions)`. Every other
  sub-primitive (L1 + coverage rigid; L3 `_gate_bootstrap_pair`; L5 `episode_net_means` + raw &
  studentized `_block_bootstrap_*_quantile_dist`; block-length; split) is **imported from the frozen
  module and reused unchanged**.
- **L3 vs-naive control leg stays frozen** on the per-held-bar **market-return** reference
  (`strategy_return_bps(returns, naive_momentum_positions(returns), cost_bps)`) — identical seam scope
  to E1's `gate_stack_core_costfn` (the naive control is a fixed reference, never the realized series).
- `adaptive_row` is reused **as-is** on the `gate_stack_pstar` core dict (same schema) → identical
  alpha logic, studentized sub-pop floor `Q_STUD_MIN`, verdict. No new threshold, knob, or constant.
- **Reduction identity (by construction):** `gate_stack_pstar(realized_bps := strategy_return_bps_
  turnover(returns, positions))` ≡ `gate_stack_adaptive(returns, positions)` — the seam is a pure
  source-swap of the signal leg.

Realized-series construction for synthetics — `referee_pstar.make_realized_fill(returns, positions,
*, fav_limit, adv_limit, cost_bps)`: a **causal resting-limit** fill model. For a held position the
per-bar realized net = `dir·log(P*_fav/Open)` if the favourable limit is touched first that bar,
`dir·log(P*_adv/Open)` if the adverse limit is touched first, else the open-to-open bar return; cost
amortized per entry (L-02 binding leg). Both limits rested from `≤t-1` (provenance contract in the
docstring). This is the synthetic analog of the cTrader engine's `ExitFillPrice` emission — used **only
to build calibration substrates**, never to adjudicate a price strategy (that is the engine's job).

## Substrate / strata

- **Strata:** the EXP-002 grid (instrument × {1h, 4h}, the established 32-cell calibration set),
  open-to-open `≤t-1` real returns, first-70% analysis slice only. Holdout never loaded. Per-stratum
  binding (L-03); pooled = disclosure-only.
- **Regression-anchor set:** the E3a/E4/E5 strata + seeds, so byte-identity is checked on the exact
  frozen draws.

## Three calibration arms (per stratum)

**Arm R — regression anchor (equivalence proof).** Inject `realized_bps := strategy_return_bps_
turnover(returns, positions)`. `gate_stack_pstar` verdict **must equal** `gate_stack_adaptive`/
`adaptive_row` **bit-identically** (target 32/32 reproducing EXP-003/E4/E5; also a `referee_*` byte-hash
check). Any mismatch ⇒ the seam is not a pure source-swap ⇒ bug → fix + rerun (Stage-4 material).

**Arm N — realized-fill NULL (the genuinely new FPR risk).** The new failure mode: a limit-fill
structure manufacturing a phantom edge on a no-edge stream (the L-01/L-02 favourable-only asymmetry).
Nulls (per L-07 block-permute returns, **not** path-rotate; per L-08 the null is **not** built around a
favourable target):
- **N1 symmetric-limit martingale:** `make_realized_fill` with **matched** favourable/adverse limits on
  block-permuted (no-edge) returns. A favourable-only model would book a phantom positive; the matched
  adverse limit must offset it → realized expectancy ≈ 0 → gate **must REJECT**. This is the binding
  FPR test that the position-state §10.3a never had to face.
- **N2 future-destroyed realized:** the EXP-002 `future_destroyed` permutation applied to the realized
  series — must collapse to the null FPR.
- **N3 dogfood-negative:** the EXP-019 dogfood generators routed through the realized path (favourable
  limit on a dogfood signal's positions). FPR Wilson-bounded, draw count stated (never "≈0").
- **Success bar:** per-stratum FPR(N1,N2,N3) **≤ §10.3a's dogfood-negative FPR** on the same strata
  (E2/E4 anchor 0/32). A realized-fill arm that passes a no-edge stream is an FPR-control failure ⇒ the
  variant is **not constructible** (a valid Phase-001 null outcome).

**Arm P — synthetic-POSITIVE realized-fill power.** A return stream with genuine reversion where the
favourable limit *legitimately* captures it: `make_realized_fill` (favourable limit at the reversion
target) on a planted mean-reverting shape (extend `make_shape` "state"/"dense" with a reversion plant).
The realized series then **exceeds** `position·market-return`, so the P*-capable gate must show **finite
power** (MDE) where the position-state gate is weaker/blind — the proof the new capability is real, not
trivially inert. MDE-curve co-designed with the plant (L-08), sub→super threshold.

## Adoption rule (DET-dominance; mirrors E3a/E5)

- **ADOPT (per stratum):** Arm R byte-identical 32/32 **AND** Arm N FPR ≤ §10.3a dogfood FPR **AND** Arm
  P finite power. Then **FREEZE** `referee_pstar.gate_stack_pstar` + hash-pin (`EXP-007/results/
  freeze_manifest.json`), record the prior suites' byte-frozen hashes, **before** any CF-MR-002 read.
- **NOT-CONSTRUCTIBLE (proven null):** if no construction keeps Arm-N FPR ≤ frozen while giving Arm-P
  power → record that the faithful `P*` fill is **not adjudicable under FPR control**; D-benchmark then
  reports CF-MR-002 on the position-state proxy only (§10.3a + frozen), with realized `P*` economics as
  a labelled non-gated diagnostic.
- **INCONCLUSIVE:** bootstrap noise swamps the Arm-N/Arm-P separation at `N_BOOT` → raise resamples or
  report the bound.

## Predeclared interpretation criteria

- **Supports** (constructible) iff R≡§10.3a (byte) ∧ N-FPR ≤ frozen ∧ P-power finite, per stratum.
- **Contradicts** (not constructible) iff any realized-fill null arm (esp. N1 symmetric-limit) passes a
  no-edge stream at FPR > frozen — the limit-fill structure manufactures edge the gate can't control.
- **Inconclusive** iff the separation is within bootstrap noise.
- **Shape-aware read:** report Arm-P power by plant shape; flag where the realized path adds power vs the
  position-state §10.3a (the intended Mode-1/2 recovery, L-12) and where it does not.

## Leak tripwire(s) — mandatory (audit verifies)

- **T1 — symmetric-limit FPR (Arm N1):** the matched favourable+adverse limit on a no-edge stream
  **must not pass**. A pass = the favourable-only asymmetry (L-01/L-02) leaking a phantom edge ⇒ the
  variant is rejected. This is the core new control.
- **T2 — future-destroy on the realized series (Arm N2):** must collapse any Arm-P planted edge into the
  null CI. A surviving edge ⇒ leak ⇒ REJECT.
- **T3 — reduction-identity / byte-freeze (Arm R):** `referee_adaptive.py` + `referee_calibration.py`
  byte-hashes unchanged; `gate_stack_pstar` reduces to §10.3a exactly. Mismatch ⇒ not additive ⇒ fix.

## Complexity budget

Comparative/calibration: **new code** = 1 module (`referee_pstar.py`: `gate_stack_pstar` +
`make_realized_fill`; reuses frozen sub-primitives + `adaptive_row`) + 1 E6 harness in `code/`. **Stat
apparatus** = the gate per (32 strata × {R,N1,N2,N3,P}); FPR Wilson-bounded; MDE-curve for Arm P.
**Visualisations 4:** (1) Arm-R agreement (must be 32/32 identical); (2) Arm-N FPR per stratum vs §10.3a
(Wilson); (3) Arm-P power/MDE by plant shape vs position-state §10.3a; (4) realized-vs-position return
divergence on a representative cell. No tuning on CF-MR-002 (L-12).

## Metric denominators / zero-baseline

FPR as a Wilson-bounded proportion over a stated draw count; MDE in bps on the plant grid; verdict
margin (CI-lower − floor) per stratum. A stratum with no finite MDE under a leg is **UNPOWERED**
(reported, not FAIL — L-12 Mode-2). Active-bar / per-episode denominators unchanged from §10.3a.

## Success / failure / inconclusive

- **Success:** a frozen, hash-pinned `referee_pstar` adopted by DET-dominance (R∧N∧P), **or** a
  documented proven "not constructible without losing FPR control" — both unblock D-benchmark (the
  latter reverts it to position-state-proxy gating + realized diagnostic).
- **Failure:** Arm R not byte-identical, or a frozen module hash changes ⇒ the seam mutated the freeze
  ⇒ fix + rerun. T1/T2 not holding ⇒ REJECT-class.
- **Inconclusive:** Arm-N/Arm-P separation within bootstrap noise → raise `N_BOOT` or report the bound.

## Safety constraints for `experiment-developer`

- **Additive only:** new `referee_pstar.py`; never edit `referee_adaptive.py`/`referee_calibration.py`
  (byte-hash assert in the harness). Import + reuse frozen sub-primitives + `adaptive_row` unchanged.
- `make_realized_fill` carries a **causal provenance contract** (both limits rested from `≤t-1`; no
  bar's own close as its intrabar limit — P-09); used for **calibration substrates only**.
- Open-to-open `≤t-1` returns; block-permute for nulls (L-07); candidate-blind thresholds (Q5);
  first-70% slice only; per-stratum binding (no collapsed cross-cell verdict — L-03).
- Deterministic seeds; NaN/zero-episode handling explicit (UNPOWERED, not crash); `tqdm` over strata×arms.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-29)

Checked against `references/governance-constraints.md` + checkpoint §D0 + AMENDMENT (E6):
- **Classification** analysis-only — correct (synthetic substrates + frozen primitives; no price edge).
  0 reads / 0 slots; holdout sealed; first-70% only. ✓
- **Additive-only freeze respect:** new `referee_pstar.py`; `referee_adaptive.py` +
  `referee_calibration.py` **byte-frozen**, asserted by Arm-R reduction identity + byte-hash (T3).
  `adaptive_row` reused as-is; no new threshold/knob/constant. ✓ (the binding freeze guard)
- **Single falsifiable question**; DET-dominance adoption rule + honest "not constructible" null
  predeclared (inverted-inference). ✓
- **Null design:** Arm-N realized-fill nulls are block-permuted (L-07) and **symmetric-limit** (not
  built around a favourable target — L-08); N1 is the binding new FPR control (favourable-only
  asymmetry = the L-01/L-02 leak class). Gate-threshold-calibration check satisfied. ✓
- **Per-stratum binding** (L-03), pooled disclosure-only; UNPOWERED-not-FAIL (L-12 Mode-2);
  shape-aware read predeclared; Wilson-bounded FPR with draw counts. ✓
- **Candidate-blind** thresholds (Q5); **never tuned on CF-MR-002** (L-12); frozen + hash-pinned
  **before** any live read. ✓
- **Leak tripwires shipped:** T1 (symmetric-limit FPR), T2 (future-destroy on realized), T3
  (byte-freeze / reduction identity). ✓
- **Budget** respected (1 module + 1 harness; 4 plots; reuse frozen sub-primitives).
- **Registry:** referee-method experiment, no candidate adjudicated → no slot; CF-MR-002 untouched.

No REVISE issues. **Operator review checkpoint before Stage 2:** this experiment defines a NEW frozen
referee path — per inverted-inference predeclaration, the design is surfaced for operator review before
implement + freeze. On go-ahead, proceed to Stage 2 (implement `referee_pstar` + the E6 harness),
then autonomous Stage 3 (analysis-only) → Stage 4 audit → Stage 5 document + freeze.
