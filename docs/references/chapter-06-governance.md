# Chapter 06 Governance — Structural Volatility + Direction Programme

**State:** `CHECKPOINT-017 CLOSED / CHECKPOINT-018 OPEN — SPDR-018 + SPDR-018B CLOSED; EVIDENCE INVENTORY AND SPDR-021/022/023 DESIGNS APPROVED 2026-07-30; SPDR-021/022/023 AMENDED RERUN COMPLETE; ANALYSIS COMPLETE; AWAITING OPERATOR INTERPRETATION 2026-08-04`

**Governing RAW brief (checkpoint-017):** `.ignore/what-next/alts/vol-direction-structural-programme-raw.md`

**Governing SoT (checkpoint-018):** `.ignore/what-next/alts/opportunity.md`

**Family:** `CF-VOLDIR-001` — `REGISTERED` 2026-07-23 (unchanged through both checkpoints)

**Checkpoints:**
- `docs/experiments-docs/checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md`
  — **CLOSED** (`retrospective.md`, 2026-07-25)
- `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/design.md`
  — **OPEN**

This file records the approved route and enforcement boundary for the structural
vol → direction expectancy → combination programme, and its checkpoint-018 extension
into trade-opportunity modelling / capture geometry. It is **not** a reopening of
`CF-VOLCONV-001` / SPDR-011 late range-break conversion.

## 1. Fixed route — checkpoint-017 (CLOSED)

1. `SPDR-012` — volatility characterisation (reliability). **COMPLETE.**  
2. `SPDR-013` — direction expectancy (SMA + ZigZag; not win-rate). **COMPLETE.**  
3. Mid-checkpoint reflection — **SIGNED:** O3 direction-agnostic only; Decision A.  
4. O3 sequence:  
   - `SPDR-014` — Group 1: zone / mispricing event / post-event MOMO vs MR.
     **SCREEN COMPLETE** — INCONCLUSIVE / UNPOWERED (0/927 powered; `residual_status=NONE`).  
   - `SPDR-015` — Group 2: level-regime transitions + ordinal ZZ magnitude.
     **SCREEN COMPLETE — WORTH_EXPLORING** (per-arm).  
   - `SPDR-016` — Group 3a: refine named 014 residual.
     **CLOSED — SUPERSEDED, NEVER RUN** (2026-07-25 retrospective §4): its DERIVED feature layer was
     independently measured inert by SPDR-017, and its actual target — powering the 014 leads — is
     carried forward inside `SPDR-018` arm C, in the original event-nested form. 0 reads consumed.  
   - `SPDR-017` — Group 3b: independent predicted-price mispricing.
     **CLOSED — NOT_WORTH.**  
5. `XENA-VOLDIR-001` — **only if** a graduated cost-surviving base emerges + separate authority.
   Still **RESERVED**, never opened.

Sequence brief: `.ignore/what-next/alts/cf-voldir-o3-zone-event-sequence.md`

**Closure:** checkpoint-017 closed 2026-07-25 as
`STRUCTURAL PACKAGE DELIVERED / EXTRACTION UNRESOLVED-AT-POWER` — neither frozen end-state was
honestly claimable, because the extraction failure was never *established* (0 powered cells; B-5
forbids reading unpowered as negative). 0 counted TEST reads; 0 multiplicity slots; family status
unchanged.

## 1b. Fixed route — checkpoint-018 (OPEN)

**Binding premise:** *Unconditional direction is dead. Conditional direction is unpowered, not
refuted. Volatility is a multiplier on a direction term, never a substitute for it.*

**Organising object (binding identity):**

```
E[net per leg] = p·W − (1−p)·L − cost      p_be_net = (L+cost)/(W+L)      edge = p − p_be_net
```

Exact by the definition of conditional expectation. **The target is not "`p > 0.5`" but "`p` above
its own `p_be_net`"**, which can be satisfied at `p < 0.5` when `W > L`. `W/L` is a real,
measurable degree of freedom and is the natural handle for the capture branch; κ is a non-tradable
diagnostic that multiplies nothing. Direction is **measured, not targeted** — no work in this
checkpoint tries to improve `p`, select a better entry, or build a direction model. Terms are
estimated and reported separately; a blended opportunity score without its term-level decomposition
is refused.

1. `SPDR-018` — **powering sweep over the complete checkpoint-017 residue**, each item in its
   **original statement**, no omissions. Four arms reusing the parents' `screen_code/`:
   A = SPDR-012 residue, B = SPDR-013 residue (**where `W`/`L` get measured**), C = SPDR-014
   residue (event-nested, original form; `DA-STRADDLE` characterisation-only), D = SPDR-015
   residue (incl. the never-scored CONFIRM slice). **Only authorised drop: `SPDR-017`.**
   Multiplicity disclosed, not rationed. `NOT_RESOLVABLE` is a first-class result.
   **COMPLETE / CLOSED 2026-07-26 — `HYP-D5` SUPPORTED.** Plus `SPDR-018B`, the cTrader replication
   leg (**PARTIALLY SUPPORTED**). Neither carries a gating verdict. **Binding outcome, now governing
   every downstream design:** the joint `(p, W, L)` sits **at break-even on both universes** and
   **nothing clears `p_be_net`** (0 of 1,413 crypto; 0 of 315 cTrader); the gap is **91–96% cost, not
   rate**; and **`W/L` is NOT a free degree of freedom** — R² 0.9667 (crypto) / 0.9746 (cTrader)
   against the driftless mirror `(1−p)/p`, 36–67× movable by exit geometry with `p` moving inversely
   and the mean not improving. **Still `UNPOWERED`-not-refuted: C2 shock-MOMO and C3.**
2. Mid-checkpoint reflection — the evidence inventory was **approved 2026-07-30**. It remains an
   evidence artifact and selects no experiment itself:
   `checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid.md`.
3. **Adaptive opportunity management — DESIGN APPROVED 2026-07-30.** Three independent Nautilus
   characterisations are registered: `SPDR-021` fixed breakout, `SPDR-022` MOMO
   (`E-TOUCH/E-CLOSE`) and `SPDR-023` MR (`E-TOUCH/E-CLOSE`). None gates another. Each compares its
   fixed strategy with direct and reverse volatility-adaptive native parameters (breakout
   threshold/expiry; breach `z/H`) and individual volatility-component × external-management arms.
   Native-native combinations are bounded; native parameters are not crossed with external
   management. All origins and strata are reported with origin-/device-native measures and
   informative uncertainty, without per-experiment verdict labels. Common contract:
   `checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/adaptive-management-design.md`.
   Implementation and execution remain unauthorised.
   **Carry-forward fix still discharged by SPDR-018:** the DESIGN→CONFIRM sign flip **is** a
   power/weighting artifact (flip rate *below* chance on both universes; `n`-weighted bands agree to
   0.33 bps crypto / 0.65 bps cTrader). The selectivity-visibility fix still stands: `p_event` is
   measured and reported on every cell (never an eligibility filter), including the previously
   hidden 0.938–0.998 range.
4. `XENA-VOLDIR-001` — unchanged; conditional on a graduated cost-surviving base.

**New, binding on any capture-geometry design (from the 018/018B evidence):** any proposal must
**name the mechanism** that puts `R = p·W/((1−p)·L)` above 1 — five distinct exit devices spanning a
36–67× range of `W/L` did not, on either universe. Demand the mechanism, not a search. Thresholds must be
stated in σ̂ units or re-derived per universe (**L-50**), and no powered subset's magnitudes may be
read without the three-number selection check (**L-51**).

**Standing design rules (SoT §9), binding on every 018 design:** report the
**dependence-matched block length** for every bootstrap CI (`block ≥ H`; a library default is
not a substitute); `h` is an index offset, so co-report the exact-span
subset; magnitude-defined conditioners need a magnitude-matched comparator; **sample-size context**
uses effective, not nominal, multi-symbol coverage (INFR-022 L-63: expected counts are
context — never a hide rule, never a resolve rule; no block-MDE, no `2.8σ/√n` floor);
collapse fraction is disclosure-only near a zero mean.

SoT: `.ignore/what-next/alts/opportunity.md`

**Data roles are exclusive (operator-signed):** crypto pooled = the powered estimate; cTrader
(EURUSD / XAUUSD / USTEC, INFR-021 fence) = **independent replication read only**, never pooled into
the powered estimate. cTrader holdout from **2024-12-13** must never be queried.

**Standing caveat (binding, INFR-022 — supersedes the chapter-04/05 cost interpretation):**
the programme is **ZERO-COST** (`NO_COST_CHARGED`): no spread, commission, or swap enters any
calculation in any experiment type unless an explicit operator cost directive requests costs
(recorded in the design before execution). Every money-bearing report carries the
ZERO-COST-DISCLOSURE caveat verbatim (§3.1 / `neutrality-standard.md` § N9). "Zero" is a
model, not a measurement. **No checkpoint-018 money read, expectancy claim, tradability
claim or graduation is licensed** — by rule, permanently (the zero-cost model does not loosen
deployability refusals). This bites harder on a capture-geometry branch than on a forecasting
branch, which is a reason to state it on every report, not a reason to await a measurement.

**Deferred (operator, 2026-07-25):** pure direction-agnostic strategies — both-side, straddle-class,
grid-class. Parked, not refuted. Direction-aware capture is required.

All SPDR stages are TRAIN-only, disposition/characterisation screens under
`docs/references/spdr-lane.md`. Historical analysis-TEST and the global holdout are never loaded.

**AMENDMENT-S1 (2026-07-23):** cross-instrument stability is **not** required for SUPPORTED labels
on SPDR-014/015/016; multi-symbol agreement is credibility only. DIRECTION: NEUTRAL.

**Universe (AMENDMENT-U1):** top **25** instruments by 30-day total USD traded volume
(`sum(close×volume)` on fenced 1m bars), ranked on TRAIN only with
`asof = train_end_utc` (window `[train_end−30d, train_end)`). Pin:
`docs/signal-registry/candidate-families/cf-voldir-001-universe.json`. Applies to SPDR-012/013/014
and any later XENA universe definition unless the operator freezes a subset at reflection C.

## 2. Cost boundary (INFR-022 zero-cost — supersedes the Chapter-05 no-spread amendment)

- **Zero-cost model (§3.1):** `cost_model: NO_COST_CHARGED` — spread, commissions, and
  swaps/funding are **not modeled**; no cost function is called on any live path. The retired
  chapter-05 cost scope (`PARTIAL_FEES_FUNDING_ONLY`) is **superseded-for-live-use**
  (historical record only).
- Every money-bearing report carries the ZERO-COST-DISCLOSURE caveat verbatim.
- No deployability claim from SPDR outputs — by rule.
- **Neutrality + PSR (INFR-022, binding):** every analysis/screen/report binds N1–N11
  (`docs/references/neutrality-standard.md`); every mean-trade/leg bps read carries
  `psr` + `psr_n` on the same series; the leak tripwire's integrity bite is
  `INTEGRITY_Z × bootstrap_SE` (N6b), never an MDE.

## 3. Hard refusals

Programme-wide (both checkpoints):

- Primary direction device = SPDR-011 confirmed daily-range breakout without new evidence.  
- Win-rate as primary direction metric.  
- Combination or XENA before A and B quantified.  
- Unbounded indicator/ML zoo without frozen arms.  
- TEST / holdout contact.  
- Automatic family open/retire from experiment code (retrospective only).

Added by checkpoint-018:

- **Any expectancy claim from exits, holds, or sizing on a joint `(p, W, L)` that does not clear
  `p_be_net` at power** — the analytic `E[gross]=0` kill (`CF-VOLHARV-001/HYP-001`, reproduced by
  SPDR-013's `time` arm). Refused by construction.
- **Any rule, band, or gate phrased against `p > 0.5`** — the break-even is `p_be_net` (§1b).
- A blended opportunity score reported without its term-level decomposition.
- Researching direction prediction — new entry models, trend filters, SMA/ZigZag sign variants, or
  tuning any entry parameter to improve `p`. Direction/event rules stay simple and fixed; only the
  predeclared direct/reverse native-geometry arms may vary threshold, expiry, `z` or `H`.
- Pure direction-agnostic **strategy branches** while the checkpoint-018 scope constraint stands.
  *Exception:* SPDR-014's `DA-STRADDLE` is powered in `SPDR-018` as **characterisation only**.
- Sizing reported as improving expectancy — sizing changes variance, not mean.
- **Narrowing the `SPDR-018` residue inventory** — every 017 UNPOWERED / INCONCLUSIVE item is in
  scope in its original statement; only `SPDR-017` may be dropped.

## 4. Enforcement

- `docs/experiments-docs/INDEX.md` is the live status record.  
- Design registration does **not** authorise implementation or execution. The former capture
  registrations remain permanently void; the live replacements are SPDR-021/022/023.
- Each SPDR requires its own `design.md` before run; SPDR lane self-check replaces full QA subagent
  unless operator demands more.  
- Operator gates: implementation plan approval, then execution authority per SPDR; all three
  analyses precede the checkpoint-level interpretation; XENA remains separate.
- Every declared lead states its expected per-stratum event counts and its declared fixed
  comparator (INFR-022 L-63: sample-size is context, never a gate). B-5 is symmetric:
  small-n ≠ negative, and suggestive ≠ supported. No predeclared target MDE — the MDE
  apparatus is retired.

## 5. Relation to checkpoint-016

- `CF-VOLCONV-001` / SPDR-011 L1 closed NOT SUPPORTED remains evidence-only until that
  checkpoint’s retrospective.  
- Chapter 06 proceeds independently under this governance file.
