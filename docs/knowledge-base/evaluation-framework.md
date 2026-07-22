# Evaluation / Referee Framework (Frozen)

> **Chapter-02 renewal (binding since 2026-06-29):** the operative referee is the **renewed
> §10.3a gate at q\*=0.75** with the **E6 P\*-capable variant** and the **E7 15m domain** — see
> the "Chapter-02 renewed referee" section below. The Chapter-01 suite described next remains
> the historical baseline the renewal was DET-dominance-adjudicated against.

Built and calibrated in Phases 001–003b (framework-referee family, EXP-001–019). **Frozen.**
Report its components on any candidate; never retune thresholds, losses, costs, denominators,
or pass logic after seeing a candidate's outcome. Full per-experiment cards:
`archive/chapter-01-*/docs/experiments-docs/families/framework-referee/INDEX.md`.

**Authoritative implementation (code wins on any disagreement):**
`python/src/xen/referee_calibration.py` (5-check gate stack + shared primitives),
`python/src/xen/incremental_referee.py` (portfolio-fitness / incremental unit).

## The frozen three-component suite

| Component | Source | Detection floor (MDE) by domain |
|---|---|---|
| **Strict 5-check gate stack** | EXP-003 / EXP-005 | 5m 1 bps · 1h 4 bps · 4h 12 bps |
| **Ratified-loose referee** | EXP-011 / EXP-012 | 5m 0.5 bps · 1h 2 bps · 4h 8 bps |
| **Revised portfolio-fitness unit** | EXP-018 | 5m 12 bps · 1h 16 bps · 4h 32 bps |

A candidate may be reported against all three; the binding gate depends on the scope.

## The 5-check gate stack (legs)

Legs **as implemented** (`gate_stack_core` / `gate_stack_row`); `passed = L1 ∧ L2 ∧ L3 ∧ L4 ∧ L5`:
- **L1 readiness** — `effective_n ≥ min_effective_n` **and** min(train_up, train_down, test_up,
  test_down) episodes `≥ min_state_count`.
- **L2 integrity** — hard-coded `True` (placeholder leg; carries no test in the frozen code).
- **L3 outcome** — neutral CI lower `> 0` **and** vs-naive-control CI lower `> 0` (folds
  standalone-significance and CI-vs-naive into one leg; beats both a zero baseline and a naive
  prior-return-sign control). α-dependent.
- **L4 stability** — mean(train net) `> 0` **and** mean(test net) `> 0` (direction holds in both
  segments).
- **L5 materiality** — neutral CI lower `> materiality_bps` (the economic floor, binding,
  α-invariant). τ scales the strict→loose threshold.

Key calibration facts:
- Gate-stack **FPR ≈ 0** at every domain/α (drives FPR from ≈α to 0), bought with a **2–8×
  larger economic MDE** vs the minimal baseline (EXP-003 keystone trade-off).
- **L5 materiality is the binding, α-invariant leg** — it sets the gate MDE; the α grid moves
  only the minimal baseline.
- Lowering τ reduces MDE (strict 1/4/12 → loose 0.5/2/8 bps) with FPR still 0 (EXP-006). The
  **loose point was ratified on fresh draws** (EXP-012, all domains ADOPT_LOOSE).
- Per-instrument MDEs can be lower than pooled (EXP-008: EURUSD/1h 2 vs 4; EURUSD & XAUUSD 4h
  8 vs 12) — the pooled map is conservative, not permissive.
- Split-protocol robust on 5m/1h; 4h alt-protocols give a *lower* MDE (OOS-sample-size effect,
  not a logic change) (EXP-010, corrected for a multi-fold CI artifact).

## Incremental / portfolio-fitness unit

EXP-013–019. The first incremental unit (EXP-015) was **REFUTED** (L2 standalone leg had no
finite MDE in high-overlap synchronous null_R cells, BTCUSD-driven). The **revised** unit
(drops standalone-L2; EXP-017/018) is validated on accepted dependence cells (FPR controlled
126/126; finite worst-case MDEs 12/16/32 bps). EXP-019 composed the full suite end-to-end
(dogfood negative rejects across all domains; synthetic positive passes all three components).

## Anchors that bound interpretation

- **Lower/null anchor (EXP-004, EXP-009):** untuned Donchian/MA and 6 broadened simple
  strategies carry no positive edge even gross; net medians ≈ −1 bps. Simple intraday edges sit
  **below every gate MDE** — so a gate rejection of a simple strategy is a true negative, but
  this only *bounds* structural blindness, it does not close it.
- **Detection floor (EXP-005):** on a scoped realistic candidate the gate detects at the MDE
  with FPR 0 (DETECTED_FLOOR) — the MDE map is an honest floor here, not evidence of blindness.

## Event-level method (sparse signals)

The per-bar suite is calibrated for **≥80%-active** series. A sparse (~6%-active) event signal
scored against a per-bar floor is dominated by denominator dilution (the EXP-023 framing
defect). For sparse event vehicles use the **event-level method** (EXP-027, METHOD_VALID:
per-event expectancy + matched-control lifetime excess, regime-cluster bootstrap, Holm). This
is a standing distinction — match the evaluation vehicle to the signal's activity rate.
See [lessons-and-amendments.md](lessons-and-amendments.md) L-04.

## Chapter-02 renewed referee (FROZEN 2026-06-29; 15m added 2026-07-01)

Chapter-02 Phase 001 (E-series, EXP-001–005) renewed the gate; it is the binding referee for
all price-primary reads. Never retune after outcome contact (L-12 honored — frozen before any
live read).

- **Form: §10.3a (validity→economics, `adaptive_row`), q\*=0.75.** Amortized cost convention
  (E1: the per-held-bar convention over-charged turnover ~L× on persistent signals); power-aware
  L3/L5; **studentized** sub-population L5 (`q*-quantile/std > Φ⁻¹(q*)≈0.674`, candidate-blind —
  the E3a A1 fix that cured the high-σ 4h FPR leak *at the gate*); L2 removed; L1 bit-identical
  to frozen. DET-dominates the frozen gate 32/32 (STATE ΔMDE median 7.5 bps; sparse recovered
  28/32) at dogfood FPR 0.
- **variant-c REFUTED (E5):** a single incremental-over-naive statistic has **no absolute
  floor** — it admits anything less-bad than a money-losing baseline and survives
  future-destroy. The neutral-CI + materiality + studentized-subpop legs are what supply FPR
  control. Recorded as the rejected alternative.
- **E6 P\*-gate (`referee_pstar.gate_stack_pstar`):** §10.3a with the signal leg sourced from an
  injected **engine-realized** series — the referee for real intrabar-fill P&L. Reduction
  identity 32/32 bit-identical; realized-fill FPR controlled.
- **E7 15m domain (EXP-011):** four additive dict rows, gate logic byte-unchanged; constants
  mechanically derived candidate-blind; 16/16 DET_DOMINANT, sensitivity 112/112 0 flips. Frozen
  + hash-pinned **before** any 15m read.
- **Hash pins:** `freeze_manifest.json` per freeze — `referee_adaptive 96c940b5…`,
  `referee_calibration d10e6a27…`, `incremental_referee 1b33e70a…`, `referee_pstar 1fd06b28…`.
- **Freeze-adjudication FPR rule (E4):** single 1/162 label artifacts are not gate defects;
  require `MIN_FPR_PASSES=2` / control-relative `2α` before calling FPR_BROKEN.
- **INFR-004 hardening (L-20):** `xen.evaluation.block_bootstrap_ci` gained a seed battery,
  block-length sweep, and robust statistic after a zero-width small-n CI was caught. Gate logic
  untouched; verdicts re-checked (EXP-020 robust, 2 immaterial flips).
- **Known blind spot (L-17, open):** the L1 readiness floor is band-length-blind — it cannot
  adjudicate short (TEST-band, ~1,100-bar) samples at any edge size. A short-band instrument is
  required before any final TEST read; none exists yet.

## Chapter-03 XENA portfolio referee (INFR-006 → INFR-009; route restored 2026-07-14)

The XENA lane adjudicates a family at the **portfolio-selection** level (search over a
candidate universe → certify a subset), replacing per-candidate A/B reads. Chapter 03 ran it
live for the first time (XENA-001..003) and exposed, then fixed, the adjudication layer:

- **INFR-006 v3 (extensive-F/plateau) SUPERSEDED.** `F_floor` was an absolute threshold on
  log-wealth — an *extensive* statistic — calibrated at 24 candidates/400 budget; at live
  scale (2,736 cands) every finalist cleared it 8–57×, leaving a plateau screen that passes
  50.8% of pure noise (RANDOM certified 4/12 finalists vs a 0.75% battery null). Mechanism =
  **L-25**. Artifacts retained; not binding.
- **Binding adjudicator: INFR-009 exit-(c) two-stage binder.** Stage 1 selects **exactly one**
  subset (top-1) on stage-1 data; 0.20-span embargo; stage 2 = leg-studentized LCB on the
  binding g_gross ratio, per cadence. Selection leak prevented **by construction**:
  CONFIRM DUAL_CERTIFY e2e α̂ 5.0%/5.0% (n=200, point-α̂ gate, boundary pass — Wilson upper
  9.0%), selection_inflation ≈0 vs P3d's ~3pp. Blind VAL on the three fixtures matched
  predeclared (001/002 rejected; 003 gross-real, cost-fatal reproduced).
- **Net cost binds the objective (L-26 closure):** flat **1.0 bps** RT injected on the net
  path inside the frozen registry (P5) — engine-costless emissions can no longer produce a
  vacuous NET verdict. Per-symbol spread pins remain un-pinned (operator data needed before
  any live deployability claim).
- **Active pin:** `pc_frozen_registry.json` v2 sha256 `db87dc1a…` (parent P4 `44e1aa3c…`).
  Do not re-run the (c) confirm (α-shopping); do not revise thresholds on gate outcomes (L-23).
- **CAL discipline (binding for any recalibration):** e2e α̂ SE ≈ 0.218/√n_null — size n_null
  to the α resolution needed; design/confirm bank split; predeclared n, no optional stopping;
  gate on point α̂, not the UCB. After one clean design cycle fails to close a residual,
  switch **binder form**, not more α/L knobs (the P3→P3d→P-C lesson).
- **Open notes:** permutation battery confounded on limit-entry universes (**L-27** — a
  next-open discriminating control is required before any native-fill universe); plateau
  ubiquity (audit root cause #4) not re-encountered by the (c) binder but unresolved in
  general.
- **INFR-010 boundary (2026-07-14): the frozen registry is VOID on the new stack.** The
  (c) binder *form*, CAL discipline, and lane governance carry forward; the calibration
  constants are engine+data-specific — a fresh CAL cycle (predeclared n, bank split) is
  required before adjudicating any Bybit/Nautilus universe (INFR-010 §8 R4).

Oracle kernel: the fold is Rust (`xena_fold`, INFR-007/008) — bit-identical to Python by
pinned parity corpus + replay; 1-ULP macOS↔Linux libm divergence ⇒ **one universe adjudicates
on one platform**.

## Chapter-04 evidence-reporting correction (INFR-014..016)

Chapter 04 proved that the Chapter-03 pick-one binder can be calibrated yet still answer the
wrong research question. XENA-HTFCAP-001's selected top-1 was its worst embargoed cell
(gross LCB −123.2 bps), while an all-cell report exposed five positive-gross-LCB BTC cells.
The correction is binding:

- **Hard validity gates only:** holdout/fence, causal provenance, estimand reconciliation,
  non-STUB data, no-local-accounting, and positive-control leak bite. Failure invalidates the
  emission and requires repair.
- **Value is reported, not auto-decided:** significance labels, leg-count/power floors,
  subset selection, attribution collapse and final value verdicts are complete report layers
  over every frozen arm/cell. No `pass` field may silently discard evidence; the operator
  records the value judgement.
- **DESIGN/CONFIRM inside TRAIN:** use a frozen design bank, embargo and one confirm read.
  A TRAIN-internal confirm is not programme OOS and must never be described as certification.
- **Arm-distribution disclosure:** report per-symbol census, both positive and anti-monotone
  tails, concentration, all frozen subsets and overlap-aware uncertainty. Cross-symbol K does
  not by itself prevent one constituent from carrying the result.
- **Control selection:** for timing/event objects the primary attribution control is matched
  random timing on the same substrate. Future-destroy remains a leak test only when a material
  raw effect exists; collapse ratios near zero raw effect are undefined/noisy and cannot certify
  absence of leakage.

Enforcement: `xen.xena.report_layer`, `xen.xena.controls`,
`xen.xena.final_gate.final_report_layer`, `python/tests/test_xena_infr016.py`, and the
research-pipeline/design/analysis skill contracts. The historical frozen gates remain useful
calibration references; they no longer authorize machine value verdicts.

Active Bybit calibration pin: `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786`
(INFR-015), superseding `ac8a1eb6…`. It certifies CLS-FILTER LOW and CLS-EPISODE LOW only;
HIGH is blocked. CLS-EPISODE requires at least 16 gate-band legs, and a fourth CAL cycle needs
family-wise correction or a doubled CONFIRM bank. These are class-specific apparatus limits,
not candidate-value thresholds.

## Chapter-04 cost interpretation

- Bybit taker/taker fees are 11.0 bps round trip before spread, funding or slippage.
- Stored `SpreadBps` is `UNUSABLE`; it is a mean-print differential and can be negative.
  Any result that previously called it a measured spread keeps its gross/fee/funding evidence
  but loses the spread-based floor claim.
- Funding must be charged at actual crossed settlement stamps. A four-hour episode can cross
  at most one eight-hour funding stamp; continuous hold-rate multiplication is not an equivalent
  implementation.
- Stress applies once to the declared aggregate cost, never once per component and then again
  to the sum. Gross − fee − one executable spread − discrete funding − declared allowance is
  the economic identity; do not net a result twice.
- Until the cost path rejects negative spread inputs and exposes an audited executable pin,
  exact deployability is unresolved. This is an infrastructure defect, not evidence that spread
  is economically large at hourly horizons.
- The blast radius of negative/semantic-invalid `SpreadBps` through prior Chapter-04 cost reads
  has not been quantified. Do not inherit their exact spread-based net conclusions without a
  corrected replay; gross, fee and separately computed funding evidence remain usable.

## Trading-cost model (net-of-cost / tradability tier)

> **MIGRATION (INFR-010, 2026-07-14):** the FTMO table below binds only for the archived
> FX/indices data. The new stack replaces it with **Bybit USDT-perp maker/taker fees +
> funding accrual + the T1 pseudo-quote spread model** (INFR-010 §4/§5), built at Phase C
> (INFR-012) into `xen.evaluation`. The **discipline carries unchanged**: engine
> costless-honest, costs analyst-injected from a single source-of-truth table, netted-turnover
> rule, no per-signal double-charging.

Costs are **analyst-injected in Python only** — the cTrader engine is costless (emits real-OHLC
mid/last fills, gross `MtmBps`, no commission/spread applied; bid/ask appear only as disclosure
flags). The single source of truth is `xen.evaluation.FTMO_COSTS` + `round_trip_cost_bps`, so a
table update propagates to every future analysis automatically. Availability-screen tiers
(EXP-021/022/024) apply **no** cost; cost first gates at the tradability tier (EXP-023 / HYP-003).

`round_trip_cost_bps` (corrected 2026-07-07, operator-directed):
- **flat_USD** commissions are the published `usd_commission_per_lot` (e.g. $5), a **round-turn**
  fixed-USD charge → applied **once** (NOT ×`commission_events`), converted to bps via the USD
  notional of one lot. Notional is **currency-convention aware** (`usd_notional_per_lot`):
  XXXUSD = contract_size·price; USDXXX = contract_size (price-free); cross = contract_size·
  `base_usd_rate` (must be pinned explicitly, like `spread_pips`). The old code used the $3-pip
  proxy ×2 = $6-equiv — a ~20% over-charge, now removed.
- **percent** commissions are charged on notional (price-free). `commission_basis` ∈
  {per_side, round_turn} pins the convention per symbol; per_side scales by `commission_events`
  (×2 RT), round_turn is charged once. A wrong per-side assumption on a round-turn % overstates
  the fee 2×. **Standing TODO: verify BTC/XAU/XAG against FTMO** (currently declared per_side).
- **spread** is one full published spread per round trip — correct crossing cost on a mid-fill
  engine, **not** a double-count. `stress` (1×/2×) is a sensitivity bound, never "fees paid".

**Netted-turnover requirement (EXP-023, binding).** Charge cost against the **netted episode /
turnover** object, never per raw signal. Charging a full round trip per signal overstates fees
whenever adjacent/overlapping signals net into held inventory (the real over-statement vector
once flat_USD is fixed). EXP-020 armR did this right (turnover_frac × per-side); the per-event
availability estimand must NOT be costed per-event at the tradability tier.

**Position sizing** stays out of the edge/availability tier (bps-of-notional is size-invariant;
gross and cost both per-unit-notional → the ratio cancels size). It enters only at EXP-023+ /
deployment, where account-currency P&L, drawdown, the FTMO risk-amount (cost-per-unit-**risk**
vs per-notional), multi-leg notional weights, and Kelly are all size-dependent and do not cancel.
