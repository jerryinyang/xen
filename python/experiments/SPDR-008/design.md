# SPDR-008 — Design: signed-trap breadth (S3 Δ+), CF-SIGAUC-001 Phase-5 sweep

**Item:** SPDR-008 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §4 seq 4 (Phase 5) · **Lane:** SPDR (TRAIN-only screen)
**Source (NORMATIVE):** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` — S3 (failed break / trap, Δ+, boundaries = **IB edge, VA edge, prior extreme**), §2.1 proxy profile, §2.3 Absorption, §6.3/§6.5/§6.6/§6b, §6.10 falsifier #2, §6.12 breadth, Appendix B Phase 5.
**Scope note (operator direction 2026-07-21):** the trap boundary set is **widened to all three source S3 boundaries** — the anchored IB edge, the **prior-session value-area edge** (VAH/VAL, proxy profile), and the **prior-session extreme** — not the IB edge alone. `boundary-type ∈ {IB, PVA, PRIOR}` is a stratum dimension; the signed reads (T1/T2) are identical across types.
**Predecessor pins:** `INFR-018/results/instrument_registry.json` `pin_sha256 5c3869845bd514bf…`; `INFR-017/results/seasonal_baselines.parquet` `1b7244c8…`; `INFR-017/results/column_pins.json` `e3b9fd9b…`; catalog fence `35d3375e…`.
**Predecessor read:** SPDR-007 dispositioned the **price-only** S1/S2 spine `NOT_WORTH` (a P-01 confirmation; the signed warrant was untested and deferred). SPDR-008 tests the **deferred signed warrant**: does the *measured* taker-Δ trap load carry reversal information the price-only failed-break pattern does not.
**Deliverable:** a per-instrument **allocation map** — where across the venue's cross-section signed-trap reversal availability pays — plus a `K=3` cluster disposition on the **signed marginal value** (trap-load monotonicity), money floor computed first. **A SPDR result is never a tradability claim** (`docs/references/spdr-lane.md`): 0 counted reads, no TEST band, no holdout, registers nothing. Disposition only; the operator signs it.

---

## §0 Scope fence

| | |
|---|---|
| **Produces** | **per boundary-type** `{IB, PVA, PRIOR}`, per confirmed-trap event: the reversal excursion toward the OPPOSITE edge of that boundary's structure (MFE/MAE, IB-width-normalised), the opposite-edge-before-poke-extreme race outcome, and the measured **trap load** (Σ same-direction Δ of the poke bars, A5-residual); each read as a report layer against a matched-unconditional baseline **and** against a trap-load derangement; the per-symbol allocation map; the per-symbol money floor |
| **Must NOT produce** | a net tradable-edge claim, a deployability claim, a family status change, a counted read, any TEST or holdout contact, any per-level Δ attribution (card ban 2), any local accounting primitive, **any cross-boundary-type pooled verdict** (boundary types are tested independently — §4.1) |
| **Primary read** | **S3 SIGNED** — trap-load monotonicity + the high-vs-low-load marginal value, **evaluated independently per boundary type**. The **price-only** trap-reversal (T3) is carried only as the P-01 base/control, never as a promotable facet (SPDR-007 dispositioned the price-only spine; the mechanism doctrine bars re-running dead price geometry as an edge). S1 price-only breadth is **NOT re-run**. |
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01Z)` = estimation (tercile cuts, plants). CONFIRM `[2023-03-01Z, 2023-12-18Z)` = verification, read **once**, **TRAIN-INTERNAL** (ckpt-014 §5/D3) — labelled so in every artifact. TEST `≥ 2023-12-18` **never read**. Holdout `≥ 2025-01-08` **never queried**. |
| **Counted reads / slots** | 0 / 0 |

### Universe (checkpoint-014 §6 D4, AMENDMENT-1 — breadth is the thesis)

```
BREADTH universe (availability map, T3/T4): the 296 ADMITTED instruments with any readable
  TRAIN bar (< 2023-12-18), point-in-time, DELISTED INCLUDED, anti-survivorship binding.
  Survivorship caveat (ckpt-014 AMENDMENT-1) carried in every breadth read: the covered set is
  precisely instruments listed before train_end — a survivorship-shaped subset of the venue; the
  map describes older listings, not the venue as a whole.
SIGNED-READ universe (T1/T2, the primary): the subset with a fitted A5 |Δ| baseline
  (194 fitted at INFR-017; DESIGN-bank), NAMED in results. Trap load is a residual against that
  baseline; an instrument without it gets the unsigned base (T3/T4) only — disclosure, never a
  signed negative. Draw pool for DESIGN estimation = the 197 with DESIGN-bank coverage.
Rebalance: none — the breadth read is point-in-time membership per session, not a top-n panel.
  (SPDR-007 used the n=20 online panel for depth/comparability; SPDR-008 is breadth, so it runs
  the full readable cross-section — the two universes are intentionally different, ckpt-014 §6.)
```

### Applicability of standard design blocks

| Block | Status |
|---|---|
| Nautilus `BacktestNode`; `xen.adjudication`; estimand gate | **N/A — SPDR lane** (vectorised Python, no P&L booked, no estimand-gated verdict). Integrity substitute = code-asserted band fence + causal `t−1` self-check (§7). A `WORTH_EXPLORING` graduates into the Nautilus pipeline where these bind. |
| §10 SPREAD-SCALE-ROUTING | **APPLIES** — §6.4. |
| §11 spread as a verdict leg | **N/A with reason** — no SUPPORTED/tradability band is emitted (screen). 1× spread is nonetheless a binding leg of the §6.3 money floor. |
| §12 amendment ledger | opens **0L / 0T / 0N**; pre-measurement amendments append at QA (§10). |
| §13 battery/eligibility/null rules | **APPLIES** — §4.2, §6.5. |
| L-29/L-30/L-31 (Nautilus) | N/A — no engine run. |

### Frozen inputs — re-hashed at every entry point, `assert_frozen_inputs()` raises on mismatch

| Input | Pin | Consumed as |
|---|---|---|
| `INFR-018/…/instrument_registry.json` | `pin_sha256 5c386984…` | anchor **A-USOPEN**, IB **L=15 min**; poke detection **δ=0**; A6 window **W=30 min**; **profile kernel K-UNIFORM** (INFR-018 HYP-I4, `share=0.685` value area); per-symbol class residual thresholds |
| `INFR-017/…/seasonal_baselines.parquet` | `1b7244c8…` | A5 residuals — the trap-load reads the **signed** `delta_ratio_resid` (Δ/V direction) as primary; `delta_abs_resid` (|Δ| magnitude) only in the disclosure inventory variant; **never a raw Δ number** |
| `INFR-017/…/column_pins.json` | `e3b9fd9b…` | `SpreadBps` status = **UNUSABLE** |
| Catalog fence manifest | `35d3375e…` | `train_end 2023-12-18`, `holdout_start 2025-01-08` |

**May NOT rely on:** `SpreadBps` as a spread/cost input; the §2.5 spread-regime layer (**UNAVAILABLE — NO USABLE INPUT**, INFR-018 §5.3 — carried here); any per-level Δ (card ban 2); flip-pair spreads outside the audited symbols without recomputation; breadth beyond the readable cross-section.

**Inherited-anchor caveat (carried in every headline, INFR-018 `anchor.resolution`).** A-USOPEN×15's own breakout selection contrast was **not a resolved effect** — `E=+0.100`, day-clustered CI `[−0.282, +0.444]` (contains zero), below its own MDE 0.50; SOL was locally **negative** (−0.117). SPDR-008 uses the anchor **only to fix the IB reference frame** for locating pokes; no read may imply the anchor carries an established breakout edge. S3 is a distinct mechanism (failed-break **reversal**, not break continuation), so the weak anchor does not by itself bear on it — but the reference-frame status is stated, not assumed away.

---

## §1 Mechanism statement

```
MECHANISM: A poke beyond a session BOUNDARY — the anchored IB edge, a prior-session value-area
edge (VAH/VAL), or a prior-session extreme (source S3 lists all three) — that FAILS to gain
acceptance (frozen A6 = fewer than half of the next 30 min close beyond) and CLOSES BACK INSIDE
traps the aggressors who entered beyond the boundary: they are now underwater and must unwind,
and that forced unwind is the one reversal that carries its own fuel — so the session tends to
rotate back across the range toward the OPPOSITE edge of that boundary's structure (session
horizon). Each boundary type is a DISTINCT reference and is tested independently — the mechanism
may pay at one and not another. The data-tier's new, falsifiable content is that the trapped
inventory is MEASURED, not inferred: trap load = the seasonally-normalised net taker Δ of the poke
bars **signed by the MEASURED aggressor split** (Δ/V residual projected onto the poke direction) —
positive only when measured flow AGREED with the poke (a genuine trap), negative under ABSORPTION
where flow opposed it; the sign is from measured flow, not price geometry. The central claim — the
reason this screen
exists after the price-only spine came back P-01 — is that reversal expectancy is MONOTONE in
measured trap load, and that high-load traps rotate further than low-load traps of the SAME price
geometry. The P&L-bearing object is a SINGLE-LEG, SESSION-HORIZON reversal: one entry at the open
of the bar after the reclaim close, one exit at the first of {opposite edge of the poked boundary,
poke-extreme stop, session end}. Cadence is sparse — at most one primary trap per (boundary,
symbol, session).

DERIVED:
  estimand = per-event favourable/adverse reversal excursion from the reclaim entry toward the
             OPPOSITE edge of the poked boundary's structure, normalised by this session's own IB
             width (uniform across boundary types), and the opposite-edge-before-poke-extreme race
             outcome on the same path — an EVENT-LEVEL object (single leg, no adds/ladder/carry ⇒
             event == episode, L-16)
  null     = (primary, signed) trap-load DERANGEMENT across events: does the MEASURED Δ load carry
             reversal info, or would a random load value predict the same excursion?
             (availability) MATCHED UNCONDITIONAL cross-session entries: same symbol, same session
             phase, same reversal side, same normaliser (source §6.3)
             (base, disclosure) ORDINARY boundary touches with no confirmed trap — isolates the
             price-only geometry (P-01)
  horizon  = the anchored-session remainder (S3 LIKELIHOOD "session horizon"), not chosen for power
  test     = calendar-day-clustered block bootstrap on paired day-level contrasts (source §6b);
             load-monotonicity via Spearman ρ vs a ≥2000-seed derangement null (effect + one-sided
             p + CI, INFR-016 — never a boolean); all reported as report layers, never gates
```

**Anti-L-13 check.** The machinery is S3-native and non-transferable: the estimand is a reversal toward the opposite edge of *this family's* frozen session boundaries under *this* frozen anchor; the trap load is a residual against *this* A5 |Δ| baseline; the primary null (load derangement) exists only because the conditioning quantity is a *measured signed magnitude* — it is meaningless for any price-only mechanism. No prior Xen referee stack adjudicates; `xen.evaluation` supplies bootstrap/MDE primitives as tools.

---

## §2 Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES.
    Both are the single-leg session-horizon REVERSAL described in §1. MFE_rev/MAE_rev and the
    opposite-edge race are functions of exactly the path that leg would experience. No multi-leg
    structure ⇒ no episode aggregation (L-16).
  measured conditioning event == traded entry event: YES.
    The conditioning event is a poke beyond a session BOUNDARY that FAILED A6 and RECLAIMED
    (closed back inside the poked boundary within the 30-min window). Every boundary level is
    known ≤ t−1: the IB edge is fixed at anchor+15 of the CURRENT session; the prior value-area
    edges and prior extreme are fixed by the PRIOR anchored session, fully closed before the
    current session opens. The trade is entered at the OPEN of the bar whose OpenTime ==
    reclaim_ts (the first instant the reclaim is decidable). No resting limit, no touch-fill, no
    fill at a rule-defined level ⇒ the B-4 entry-seam mismatch cannot arise. Trap load is measured
    on the poke bars, all strictly ≤ reclaim_ts.
  effect-splitting windows non-overlapping: YES, code-asserted —
    prior session (PVA/PRIOR levels)  ⟂  IB [anchor, anchor+15)  ⟂  poke search [anchor+15,
    session_end)  ⟂  poke-and-fail window [poke_ts, reclaim_ts]  ⟂  reversal outcome
    (reclaim_ts, session_end].
    Trap load is a function of the poke-and-fail window ONLY; the reversal excursion is measured
    STRICTLY AFTER the entry bar opens; the entry bar's own range is excluded from MFE/MAE.
    `trap.assert_windows_disjoint` + `trap.assert_entry_after_reclaim` raise on violation.
```

---

## §3 The event, the estimand, the resolution rule

### 3.1 Event construction (inherited from the frozen apparatus — no new selection)

Per (symbol, session) on the frozen anchor. **Frozen-apparatus reuse boundary, stated precisely (QA-1 Issue 2):**
- **`IB` boundary** reuses `sessions.session_breaks` + `acceptance.find_pokes` + `acceptance.evaluate_discriminator(D4-t50-w30)` **exactly and unmodified** — the A6-REJECT set on IB (`says_accept == False`) is byte-identical to SPDR-007's rejected-poke denominator, and `trap.py` asserts this reproduction (`assert_ib_matches_frozen`). `acceptance.label_outcomes` already computes the opposite-IB-edge-before-poke-extreme `TRAP` race — reused for the IB race outcome.
- **`PVA`/`PRIOR` boundaries** need levels the frozen `find_pokes`/`evaluate_discriminator` cannot read (both are hard-wired to `ib_high`/`ib_low`). `acceptance.py` is **NOT modified** (that would break the INFR-018 pin). Instead `xen.sigbar.trap` provides NEW level-generalised plumbing — `find_pokes_at_level(level_up, level_dn)` and a `D4-t50-w30` close-count applied at that level — that **re-implements the frozen A6 form**, guarded by a regression assert that on the IB level it reproduces `acceptance.evaluate_discriminator` **byte-identically**. New plumbing to reach new levels; the frozen close-count rule and its params are unchanged, not re-raced.

**Boundary set B (three types, each a pair of levels, all known ≤ t−1):**

| type | up level | down level | source | causality |
|---|---|---|---|---|
| `IB` | IB high | IB low | `sessions.session_breaks(bars, anchors, 15)` — CURRENT session | fixed at anchor+15 |
| `PVA` | prior VAH | prior VAL | `profile.poc_and_value_area(build_profile(prior_session_bars, "K-UNIFORM"), share=0.685)` | PRIOR session fully closed before current open |
| `PRIOR` | prior real High | prior real Low | prior anchored session's `max(High)` / `min(Low)` | PRIOR session closed |

Sessions with IB coverage `<0.9` ⇒ `INCOMPLETE`, counted; a PVA/PRIOR level needs a covered prior session, else that boundary type is unavailable for the session — **counted, never silently dropped**.

**Trap detection, applied to each boundary level independently** (poke search window `[anchor+15, session_end)` uniform — the frozen post-IB window):

1. **Poke** (δ=0): the first bar in the search window trading beyond the boundary level; qualifying window `[poke_ts, poke_ts+30)`.
2. **A6 = D4-t50-w30 REJECT:** `< 50%` of the 30 qualifying bars close beyond the poked level → the poke **failed acceptance**. IB via the frozen `evaluate_discriminator`; PVA/PRIOR via the regression-guarded `trap.py` re-implementation of the same close-count form (above) — the same frozen rule applied to a different level, not a new selection.
3. **Reclaim:** the first bar in `[poke_ts, poke_ts+30)` whose **close is back on the inside** of the poked level. A failed poke **with** a reclaim = a **confirmed trap** at that boundary type; `entry_ts` = the bar after the reclaim close. A failed poke that never recloses inside within the window is **not a trap** — dropped, counted.

A session can produce at most one trap per (boundary-type, side); if multiple levels are poked, each is a separate event in its own boundary-type stratum (no dedup across types).

**Nothing above is re-raced or re-tuned.** The kernel (K-UNIFORM), anchor, L, δ, and the A6 close-count rule are all frozen at INFR-018. The only value estimated in SPDR-008 is the trap-load tercile cut (§4.1, DESIGN-only, per boundary type, frozen, applied to CONFIRM). Any change to a frozen input invalidates the pin and re-runs INFR-018.

### 3.2 Entry, exit, trap load, estimand

| Quantity | Definition (L-21 unit pin stated with every number) |
|---|---|
| `entry_ts` | the bar with `OpenTime == reclaim_ts` |
| `entry` | that bar's **Open** (decision at bar open on confirmed data ≤ t−1) |
| `side` | **reversal side** = − poke_side (failed UP poke ⇒ SHORT; failed DOWN poke ⇒ LONG) |
| `poke_extreme` | the max (UP) / min (DOWN) real price reached during the poke-and-fail window |
| `opposite_edge` | the far level of the SAME boundary structure: `IB`→opposite IB edge · `PVA`→opposite prior VA edge · `PRIOR`→opposite prior extreme (the reversal target) |
| outcome window | `(reclaim_ts, session_end)` — bars strictly after the entry bar |
| `MFE_rev` / `MAE_rev` | max favourable / adverse excursion of **real prices** from `entry` toward `opposite_edge` over the window |
| **`ib_width`** | this session's IB high − IB low, **price units** — the single **frozen L-21 divisor object** used uniformly for every normalised excursion, ALL boundary types. It is the money-conversion divisor (it cancels: `mfe_rev_norm × ib_width_bps` = true excursion bps), NOT a claim that a PVA/PRIOR reversal spans one IB width; the boundary types are read independently, never compared on the normalised scale. VA-width / prior-range normalisers are disclosure-only sensitivities |
| `mfe_rev_norm`,`mae_rev_norm` | `MFE_rev / ib_width`, `MAE_rev / ib_width` |
| `ib_width_bps` | `1e4 × ib_width / ((ib_high+ib_low)/2)` — the money conversion factor (§6.1) |
| **`trap_load`** | **signed by MEASURED flow:** `poke_side × Σ over poke-and-fail bars of delta_ratio_resid` — the seasonally-normalised net taker aggression (Δ/V residual, the A5 **signed direction** column, `INFR-017 seasonal_baselines.parquet 1b7244c8`) summed over the poke bars and projected onto the poke direction. `> 0` ⇒ measured flow AGREED with the poke (genuine same-direction trap — buyers trapped above / sellers below); `≤ 0` ⇒ flow OPPOSED (absorption — "trapped nobody", source S3). **The sign is from the measured aggressor split, NOT price geometry** (QA-1 Issue 1); this mirrors the frozen A6 flow-augmentation direction leg (`acceptance.py:381`, `delta_ratio_resid × side`) and SPDR-007's coherence stratifier. A raw-Δ figure is never used (card ban 5 / A5). **Disclosure variant** (source's inventory form Σ same-direction Δ): `poke_side × Σ [sign(Δ_bar) × delta_abs_resid]` — magnitude-scaled, reported as a sensitivity so the monotonicity is not an intensity-vs-inventory artifact |

**Resolution rule (source S3, frozen before results).** Target-before-invalidation on the same path, identical form for every boundary type: `TP = opposite_edge` of the poked boundary's structure (source: "target the opposite edge, staged through POC/VWAP" — the opposite edge is the pinned first target; POC/VWAP staging is a disclosure-only intermediate, not the pinned target); `STOP = poke_extreme` (source INVALIDATION: "a second poke exceeding the first extreme"). Outcome ∈ {`TP`, `STOP`, `TIMEOUT` at session end}. **Same-bar ambiguity resolved pessimistically → `STOP`** (sub-minute order unavailable, source A2 / card ban 3).

### 3.3 The trap-load tiers (S3's Δ+ discrimination — the signed dimension)

Source S3: the two-notch trap grade requires **measured trap load ≥ a seasonal percentile**; "a poke that failed on negligible same-direction Δ trapped nobody — demote to a rejection." Operationalised as terciles of `trap_load`, **computed on DESIGN, per boundary type × symbol (pooled-within-boundary-type fallback where per-symbol is thin), frozen to `results/trap_load_cuts.json` with its hash before any CONFIRM path runs, applied unchanged to CONFIRM**:
`LOW` (bottom tercile — "rejection, not trap") · `MID` · `HIGH` (top tercile — "confirmed trap"). The continuous `trap_load` is primary for monotonicity (T1); the tiers give the marginal-value contrast (T2).

---

## §4 The reads (report layers — the operator judges; L-32 / INFR-016)

**T0 — money floor** (card §6, the binding first act): the cost floor (taker + spread + funding) and the data-only "reversal must exceed X IB widths" thresholds are published **before any estimation**; the reversal-vs-floor comparison follows estimation (§6.3, execution order §9).

| id | Question | Statistic | Class | Band |
|---|---|---|---|---|
| **T1** *(PRIMARY, signed)* | Is reversal excursion MONOTONE in measured trap load? | Spearman `ρ(trap_load, mfe_rev_norm)` per stratum, read as **ρ vs its ≥2000-seed trap-load-derangement null** (CONTROL-B): effect + one-sided p + CI; a raw-bps `ρ(trap_load, MFE_rev_bps)` disclosure separates the physical claim from the normaliser (I-3 guard) | report | §5 |
| **T2** *(signed marginal value)* | Do HIGH-load traps rotate further than LOW-load traps of the SAME geometry? | `mfe_rev_norm` and race-win contrast, `HIGH − LOW` tier, day-clustered block-bootstrap CI; collapses under CONTROL-B | report | §5 |
| **T3** *(unsigned base, P-01 flag)* | Does the failed-poke GEOMETRY add reversal over ordinary boundary touches? | `mfe_rev_norm` contrast, confirmed-trap − ordinary-touch (CONTROL-A) | disclosure | §5 |
| **T4** *(availability)* | Does the trap reversal beat a matched-unconditional random-timing entry? | `mfe_rev_norm` / race contrast vs CONTROL-C, ≥25-seed percentile read | report | §5 |

**Promotable facet = the SIGNED one.** `K=3` (ckpt-014 §4) is evaluated on **T1∧T2 clustered with T4, WITHIN A SINGLE boundary type**: ≥3 connected cells (same signal, **same boundary type**, varying symbol and/or hold) where high-load reversal availability beats the matched control **and** the load-monotonicity survives derangement, best cell not the only positive in its neighbourhood, cluster-median reversal bps reported against the measured floor (§6.3). A cluster may NOT be assembled by mixing boundary types. **T3 positive with T1/T2 WASH ⇒ price geometry only (P-01) ⇒ NOT the signed warrant** — recorded as such.

### 4.1 Strata (per-stratum binding; boundary types independent; pooled disclosure-only — L-03)

**`boundary-type {IB, PVA, PRIOR}`** (leading dimension — the three types are tested independently; no read is pooled across them except as explicit disclosure) × `symbol` × `trap-load tier {LOW,MID,HIGH}` × `hold {session (primary), micro 1–10 bars (secondary disclosure)}` × `chronological third`, plus each margin. **UNPOWERED is evaluated first** (§5). Cross-symbol pooling is disclosure-only unless within-boundary homogeneity is shown; cross-boundary pooling is never a headline. **Multiplicity: three boundary types are three independent signal families** — the cell count and the per-boundary read structure are disclosed (L-03); a `K=3` cluster in one boundary type is not strengthened by, nor traded off against, activity in another. The breadth **allocation map** is the per-(boundary-type × symbol) margin (does the signal pay *here*), not a pooled headline.

### 4.2 Controls

**Legend (as referenced in the §4 read table):** CONTROL-A = `ordinary_touch` (unsigned base, P-01 isolator) · CONTROL-B = `trap_load_derangement` (PRIMARY signed null) · CONTROL-C = `matched_unconditional` (availability baseline).

**All three controls and the tripwire are computed independently within each boundary type** — a trap's matched/derangement/swap comparanda are drawn from its own boundary-type population, never mixed across types.

```
CONTROL trap_load_derangement  (PRIMARY signed null; class: within_sample_attribution → REPORT LAYER)
  question answered: is the load-monotonicity (T1) / high−low contrast (T2) attributable to the
    MEASURED Δ load, or to load correlating with a confound (volatility, phase, poke depth)?
  population: the same confirmed-trap events; `trap_load` labels DERANGED across events (zero fixed
    points, L-28), regenerated until the fixed-point count is EXACTLY 0 and asserted; ρ and the
    tier contrast recomputed per seed; ≥2000 seeds; reported as observed minus the deranged
    distribution — effect + one-sided p + CI (never `at_or_above_pXX`, never a collapse auto-kill).
  singleton/coverage: a calendar-day block that cannot be deranged to zero fixed points → its events
    dropped and COUNTED; deranged fraction reported beside the effect (SPDR-007 I-5 precedent).
  DISJOINT: at every index the (load, excursion) pairing differs from the real pairing.
  bite/MDE: plant a synthetic monotone load→excursion effect of known size on the real arm; confirm
    the deranged arm reads ≈0 across the sweep; MDE published before the read.
  non-vacuity: re-pairs load with excursion ⇒ moves ρ and the tier-contrast sufficient statistics.
  NOT VACUOUS BY SYMMETRY (B-6): a load SIGN flip would be a different (antisymmetric) null; a
    DERANGEMENT across events tests "load is uninformative", the correct null for monotonicity.
  expected if signed-H true: observed ρ / contrast ≫ deranged. If false: equal.
  disclosure: collapse fraction (deranged / observed) per stratum.
  destroy form: DERANGEMENT (zero fixed points, asserted).

CONTROL matched_unconditional  (availability baseline; class: within_sample_attribution → REPORT LAYER)
  question answered: does entering the REVERSAL side at the same symbol/phase in an UNCONDITIONAL
    session produce the same excursion, i.e. does the number belong to the TRAP or to sessions'
    generic directional behaviour at that phase? (source §6.3)
  population: cross-session donors (SPDR-007 D-1 pattern, operator-ratified): for each event
    (reversal side d, phase φ = mins_since_anchor at reclaim_ts), draw 30 donor sessions (≥ L-19
    floor 25, seeded) from the SYMBOL's own pool, excluding the event's session and any too short
    to run φ; enter each at anchor(donor)+φ on side d, normalised by the DONOR IB width. Horizon-
    matched by construction; the realised remaining-horizon distributions are emitted side by side.
  DISJOINT: donor session ≠ event session ⇒ different entry bar, price, outcome window, race path.
  bite/MDE: co-designed additive plant on the trap arm's mfe_rev_norm; MDE read off the curve at the
    realised n per stratum, published in CONTRAST UNITS (L-21/L-24), before the real read.
  non-vacuity: moves the entry price and the entire excursion path — the sufficient statistic.
  exit-matched (L-24 F04): every control entry resolved under the SAME opposite-edge/poke-extreme
    rule and the same pessimistic same-bar convention.
  expected if H true: contrast > 0, stable across thirds. If false: ≈0.
  disclosure: collapse fraction per stratum. destroy form: independent re-drawing of the instant.

CONTROL ordinary_touch  (unsigned base, P-01 isolator; class: within_sample_attribution → DISCLOSURE)
  question answered: does the failed-poke GEOMETRY (any load) add reversal over generic same-side
    touches of the SAME boundary level that did NOT trap — i.e. how much of any effect is price
    geometry (P-01)?
  population: entries at that boundary level's touches in (symbol, session, phase-band, reversal
    side) with NO confirmed trap at that level; DISJOINT from confirmed traps; same boundary type.
  non-vacuity / bite/MDE / exit-matched: as matched_unconditional.
  expected: T3 may be > 0 (geometry) or ≈0; it is the price-only base, FLAGGED P-01, never
    promotable — the signed warrant is T1/T2, not T3.
```

### 4.3 Leak tripwire (HARD — validity)

```
TRIPWIRE reversal_path_swap  (class: future_destroy — HARD)
  Replace each event's REVERSAL outcome path with the outcome path of a DERANGED donor event
  (matched on remaining-session length; zero fixed points, asserted; re-based to the target's entry
  price). Everything at or before entry — the poke, the A6 reject, the reclaim, the trap load, the
  boundary, the side — is IDENTICAL; the outcome is unrelated to it.
  vacuity check: MFE_rev/MAE_rev/race are functions of the outcome path alone; replacing it moves
    the metric's entire support, not its labels.
  STATISTIC, per read: collapse_fraction = destroyed_contrast / raw_contrast, computed on each
    adjudicated effect-contrast — T1 ρ, T2 tier contrast, T4 availability contrast. (T3 disclosure
    is adjudicated too.) The monotonicity ρ MUST collapse: a donor's outcome is unrelated to the
    real trap load.
  MATERIAL-EDGE PRECONDITION (inherited SPDR-007 AMENDMENT-11 / D-2): the HARD survival rule fires
    ONLY where the RAW contrast is a material edge (day-clustered CI excludes zero). Where no
    material raw edge exists the tripwire is UNPOWERED (`NO_MATERIAL_EDGE`) — NOT a leak, NOT a hard
    fail (a destroy cannot leak-test an edge that does not exist). A material surviving edge still
    HARD-fails, so this cannot hide a leak.
  SURVIVAL := (raw CI excludes zero) AND (|collapse_fraction| > 0.25, same sign as raw) AND (swapped
    CI excludes zero). The 0.25 threshold is INHERITED from the INFR-018 sealed tripwire (L-24 F06),
    not re-asserted.
  IF A MATERIAL ADJUDICATED READ SURVIVES: the construction is reading the outcome ⇒ EMISSION
    INVALID ⇒ fix and re-run. NEVER read as "no effect".
  coverage: events with no usable donor dropped and COUNTED; spliced fraction reported.
  permutation-based: YES → DERANGEMENT, zero fixed points, asserted.

POSITIVE CONTROL bite (REQUIRED — no disposition emits without it): pooled across symbols,
  `corr(mfe_swapped_price, mfe_donor_price) > 0.5` (SPDR-007 measured 0.77 on the same swap). If it
  fails, the swap reached nothing the reads consume and the tripwire has no teeth (INFR-018 A-6
  defect). Price MFE, not the IB-normalised value (donor/target divisors differ and would attenuate).
```

---

## §5 Interpretation bands — labels, never gates (UNPOWERED evaluated FIRST — L-32 / B-5)

```
T1 / T2 / T4 contrasts (per stratum):
  UNPOWERED:    MDE > |plausible effect| at the realised n  (tested FIRST; never a negative)
  SUPPORTED:    effect ≥ its own MDE and ci_low > 0  (T1 also: derangement one-sided p ≤ 0.05)
  SUGGESTIVE:   ci_low > 0 but effect < its own MDE
  WASH:         |effect| < MDE → "cannot distinguish", never a refutation (L-11)
  CONTRADICTED: ci_high < 0  (for T1: load ANTI-monotone — genuine evidence against the mechanism)
  POOLED:       disclosure-only unless homogeneity is demonstrated (L-03)
SIGNED-VALUE verdict (the screen's point): the signal is signed-supported in a stratum only if
  T1 SUPPORTED (monotone, survives derangement) AND T2 ci_low > 0. T3 SUPPORTED with T1/T2 WASH ⇒
  P-01 (geometry), recorded, not promoted.
```

**Normaliser-mechanic guard (I-3, binding, inherited).** `mfe_rev_norm = MFE_rev / ib_width` and `trap_load` may share dependence on session scale. T1's binding read is therefore ρ **vs the load-derangement null** (both arms share the divisor and the marginal load distribution, so a scale confound cancels), with a second **un-normalised** disclosure `ρ(trap_load, MFE_rev_bps)`. **Time stability (L-24 F02), reported not gated:** every read repeated on the three DESIGN thirds and on CONFIRM; sign consistency + per-third n published.

---

## §6 Money floor, conversion pin, power, uncertainty

### 6.1 Money floor + CONVERSION-PIN (card §6 — binding first act)

```
CONVERSION-PIN:
  divisor object (excursion): "this session's IB high − IB low in PRICE units, frozen anchor
    A-USOPEN L=15; bps = 1e4 × ib_width / ((ib_high+ib_low)/2)" — xen.sigbar.sessions.session_breaks,
    column ib_width; SPDR-008 screen_code/trap_screen.py
  measured value (DESIGN-median ib_width_bps, computed from staging 2026-07-21, NOT recalled —
    reference symbols, reused from the frozen SPDR-007 §6.3 derivation on the identical divisor):
    BTCUSDT 48.745 · ETHUSDT 69.958 · SOLUSDT 96.217 · DOGEUSDT 86.969 · XRPUSDT 60.753 bps;
    the full per-symbol table is emitted at run to results/floor_table.json for all breadth symbols
  normaliser object (trap load): "A5 seasonal Δ/V baseline residual delta_ratio_resid (SIGNED
    direction), minute-of-day × day-of-week, INFR-017 seasonal_baselines.parquet 1b7244c8; the
    disclosure inventory variant uses delta_abs_resid magnitude carrying the measured per-bar Δ
    sign" — a residual, never a raw Δ
  resulting effect: reversal_bps = mfe_rev_norm × ib_width_bps, per event, summarised per symbol
    (divisor cancels ⇒ true excursion bps; the SCREEN measures availability, not booked P&L). Worked
    row (illustrative, not a result): a SOLUSDT full-rotation reversal mfe_rev_norm = 1.0 ⇒
    reversal_bps = 96.217, vs its floor 14.73 bps (below) ⇒ ABOVE_FLOOR as availability; the actual
    per-cell reversal magnitudes are the screen's output, not asserted here
  cost floor: bybit_round_trip_cost_bps(liquidity="taker", spread_bps=<per-symbol>, hold_hours=
    <realised>) = taker RT 11.0 + spread RT + funding (≈3.0 at ≤24h session hold); reference-symbol
    floors from SPDR-007 §6.3: BTC 14.24 · ETH 14.31 · SOL 14.73 · DOGE 15.48 · XRP 15.93 bps
FLOOR BAND (framing, not a gate — card §6):
  ABOVE_FLOOR       : cluster-median reversal bps exceeds its floor → may read as a strategy
                      candidate (still not a tradability claim — SPDR lane)
  AT_OR_BELOW_FLOOR : recorded as MARKET SCIENCE, NOT STRATEGY (source framework falsifier — "edges
                      vanish inside costs"); may route forward only re-framed as characterisation
```

**Spread input.** `SpreadBps` UNUSABLE (INFR-017 W2); §2.5 regime UNAVAILABLE (INFR-018). The floor uses `max(tick_bps, flip-pair_bps)` on the audited symbols (flip-pair = conservative upper bound, tick = lower bound, each labelled) and a **tick-size floor** elsewhere across the 296. Where no reliable spread exists, the symbol's tradability framing is **AWAITING_MBP** (§6.4) and its availability read stays gross/disclosure — the disposition never makes a net claim on it.

### 6.2 SPREAD-SCALE-ROUTING (mandatory, T1 lane)

```
SPREAD-SCALE-ROUTING (per symbol at screen time):
  estimated_rt_spread_bps: max(tick_bps, flip-pair) audited; tick floor elsewhere
  gross_edge_bps: the stratum's SIGNED contrast in bps (T2 HIGH−LOW mfe_rev_norm × median ib_width_bps)
  t1_undecidable: xen.evaluation.spread_scale_route(gross, rt_spread) — 3× threshold used, not re-derived
  if YES: stratum reported AWAITING_MBP; pooled T1 reads stay disclosure-only
```

### 6.3 Power (structure predeclared; counts measured on disk at run, not asserted)

The event population is **A6-REJECTED pokes that reclaim, per boundary type** (SPDR-007's IB rejected-poke denominator was DESIGN 6,654 = 13,802 pokes − 7,148 accepts on the depth panel; the reclaiming subset is a fraction of that, recomputed on the 296 breadth cross-section by `pop.py`, QA re-derives against the emission). **`PVA`/`PRIOR` pokes are RARER than `IB` pokes** — they require price to reach a prior-session level and fail there — so those boundary-type strata are thinner and more will fall UNPOWERED; the per-boundary counts are measured on disk, not assumed. Sparse per symbol; breadth dominated by thin instruments.

```
STRATA PREDECLARED UNPOWERED (never readable as negatives — B-5):
  - any boundary-type × symbol × load-tier × hold cell below its published MDE floor at realised n
  - any (boundary-type × symbol) with too few prior-session-covered sessions for PVA/PRIOR levels
  - any instrument WITHOUT a fitted A5 baseline → signed reads (T1/T2) unavailable → unsigned base
    (T3/T4) only, disclosure — never a signed negative
  - any chronological third of a per-symbol read; the micro-hold secondary facet where thin
  - every UNPOWERED cell reported WITH its n and MDE, never folded into a failure
MDE: read off the co-designed plant curves (§4.2) at the realised n per stratum, published BEFORE
  the real read. No MDE asserted from memory. Pooled + cross-sectional cluster (K=3) is the PRIMARY
  where per-symbol is thin (declared, not smuggled — L-03); per-symbol binding where its MDE clears.
```

### 6.4 Uncertainty

**Calendar-day-clustered circular block bootstrap** on paired day-level contrasts via `xen.evaluation.block_bootstrap_ci` (INFR-004/L-20: effective block capped `< n`; 5-seed battery; `block_sensitivity` ½×/1×/2×; `trimmed_mean` robustness). Resampling unit = the calendar day (all symbols' events that UTC day together — cross-sectional shock). Source §6b (episodes, not bars). Reported as **"the 95% interval excludes zero"**, never a p-value (L-20). Same-symbol adjacent sessions' outcome windows do not overlap (one event/session, exit by session end) — asserted, not assumed; no block ≥ H inflation needed beyond day clustering. The derangement null (T1) is a separate ≥2000-seed battery reported as effect + one-sided p + CI.

---

## §7 Integrity vs informative split

```
HARD (block — failure means the EMISSION IS INVALID; fix and re-run; NEVER read as "no edge"):
  - future-destroy tripwire: reversal_path_swap must collapse on every material adjudicated read,
    AND its positive control (bite corr > 0.5) must survive
  - band fences: DESIGN/CONFIRM asserted on EVERY read path (`fences.assert_band`, raise not warn);
    TEST and holdout unreachable by construction
  - CONFIRM-before-freeze refusal: no CONFIRM path executes before results/trap_load_cuts.json
    exists with its hash
  - causal ≤ t−1: trap load from poke bars ≤ reclaim_ts; every conditioning input at/before the
    entry bar's open; regime/tercile cuts from DESIGN only
  - window disjointness (§2), incl. entry-bar exclusion from the reversal excursion
  - frozen-input hash re-verification at every entry point
  - `fences.assert_no_per_level_delta` — per-level signed attribution raises (card ban 2)
  - `check_no_local_accounting` — no accounting primitive in this experiment dir

INFORMATIVE (report layers; the OPERATOR judges — L-32 / INFR-016):
  every Spearman, tier contrast, availability contrast, collapse fraction, derangement p/CI,
  stability read, floor comparison, band label, and the per-symbol allocation map. No `pass` field
  anywhere; nothing machine-dropped between layers. The disposition is an OPERATOR ACT.
```

---

## §8 Golden trace — designer-derived, for QA to diff before execution

Concretely derived from staging bars under this design's frozen rules by `design_derivations/gt_derive.py` (full output `design_derivations/gt_output.txt`), designer-side and INDEPENDENT of `xen.sigbar.trap` (it recomputes `delta_ratio_resid` via `residualise` itself) — the developer must NOT regenerate these; QA diffs the implementation against them. All events are DESIGN band (2022-07, inside `[2021-06-29, 2023-03-01)`). Entry = OPEN of the bar at `reclaim_ts + 1min`. `trap_load` is pinned as the **definition** — `poke_side × Σ delta_ratio_resid` over the poke-and-fail bars — with the raw `poke_side × ΣΔ` shown in brackets as a cross-check. **Raw and residual usually share sign but NOT always** (GT-3(b) is the deliberate counter-example): the seasonal residual can go negative on a poke that had net same-direction flow but *below* what that minute-of-week normally carries — a weak trap, correctly demoted. That divergence is a feature of the pinned measure (§3.2), not a defect; QA diffs the geometry exactly and the pinned `trap_load` residual value.

```
GT-1  IB DOWN trap, POSITIVE load (genuine seller trap) — BTCUSDT session 2022-07-15 13:30Z.
      IB via frozen apparatus: ib_high 21020.5  ib_low 20833.0  ib_width 187.5.
      poke DOWN ib_low  poke_ts 13:45  poke_extreme 20821.0  beyond_frac 0.1667 (<0.5 REJECT)
      reclaim_ts 13:46  entry (13:47 open) 20833.5  rev_side LONG  opposite_edge = ib_high 21020.5
      STOP = poke_extreme 20821.0  MFE_rev_norm 1.9307  MAE_rev_norm 1.9413  n_post 1423
      trap_load = poke_side·Σ delta_ratio_resid = +0.8821 [raw ΣΔ +151.7] (>0 ⇒ sellers trapped)

GT-2  IB UP trap, NEGATIVE load (absorption — the signed-logic GUARD for QA-1 Issue 1) —
      SOLUSDT session 2022-07-14 13:30Z. ib_high 33.925  ib_low 33.625  ib_width 0.30.
      poke UP ib_high  poke_ts 13:46  poke_extreme 33.94  beyond_frac 0.1667 (<0.5 REJECT)
      reclaim_ts 13:46  entry (13:47 open) 33.835  rev_side SHORT  opposite_edge = ib_low 33.625
      STOP = poke_extreme 33.94  MFE_rev_norm 0.4333  MAE_rev_norm 15.75  n_post 1423
      trap_load = poke_side·Σ delta_ratio_resid = −0.1229 [raw ΣΔ −83.3] (<0 ⇒ up-poke on net
      SELLING = absorption, NOT a buyer trap ⇒ LOW tier; weak reversal MFE 0.43 confirms). GUARD:
      the retired magnitude×geometry definition would score this HIGH-long; the measured-flow
      definition scores it negative. QA diffs the SIGN.

GT-3  PVA + PRIOR traps (the widening's core; prior session PINNED) — BTCUSDT.
   (a) PVA trap: current session 2022-07-17 13:30Z, PRIOR session 2022-07-16 13:30Z.
       prior value area (build_profile K-UNIFORM, share 0.685): VAL 21147.4  VAH 21468.4.
       poke DOWN prior-VAL  poke_ts 13:57  poke_extreme 21135.5  beyond_frac 0.20 (<0.5 REJECT)
       reclaim_ts 13:57  entry (13:58 open) 21152.5  rev_side LONG  opposite_edge = prior-VAH 21468.4
       ib_width 98.0 (divisor)  MFE_rev_norm 13.97  MAE_rev_norm 4.16  n_post 1412
       trap_load = poke_side·Σ delta_ratio_resid = +0.2736 [raw ΣΔ +87.2] (>0 ⇒ genuine trap)
   (b) PRIOR trap: current session 2022-07-16 13:30Z, PRIOR session 2022-07-15 13:30Z.
       prior extreme: High 21195.5  Low 20469.5.
       poke UP prior-High  poke_ts 16:14  poke_extreme 21394.5  beyond_frac 0.4333 (<0.5 REJECT)
       reclaim_ts 16:18  entry (16:19 open) 21162.0  rev_side SHORT  opposite_edge = prior-Low 20469.5
       ib_width 47.5 (divisor)  MFE_rev_norm 5.31  MAE_rev_norm 10.67  n_post 1271
       trap_load = poke_side·Σ delta_ratio_resid = **−0.7273** [raw ΣΔ **+573.4**] — the SIGN-DIVERGENCE
       counter-example: net buying entered (raw +573) but BELOW the seasonal norm for that
       minute-of-week ⇒ residual negative ⇒ weak trap ⇒ LOW tier; the poor SHORT reversal
       (favourable 5.31 vs adverse 10.67) is consistent. This is the pinned measure working, not a
       defect — QA verifies trap.py reproduces −0.7273, NOT the raw sign.
   Proves: (i) PVA/PRIOR levels come ONLY from the prior closed session; (ii) opposite_edge = the
   opposite level of the same structure; (iii) the reversal is measured relative to rev_side; (iv)
   the widening produces real events on real data; (v) trap_load is the seasonal residual, which
   can diverge in sign from raw ΣΔ (GT-3(b)). Tier assignment uses the per-boundary DESIGN cut.

GT-4  Fence + hash + order behaviour (must RAISE, not warn):
      (a) any read path with OpenTime ≥ 2023-12-18 → raises;
      (b) a CONFIRM path before results/trap_load_cuts.json exists → raises;
      (c) registry pin ≠ 5c386984… or baselines sha ≠ 1b7244c8… or kernel ≠ K-UNIFORM → raises;
      (d) a per-level Δ access (incl. a signed column reaching a profile kernel) → raises (card ban 2);
      (e) a control/donor entry minute inside the event's [poke_ts, reclaim_ts] window → raises;
      (f) a trap-load derangement seed with any fixed point → raises (L-28);
      (g) a PVA/PRIOR level computed from the CURRENT (not prior) session → raises (causality).
```

---

## §9 Artifacts, complexity budget, execution order

| | |
|---|---|
| Statistical reads | 4 (T1 monotonicity, T2 tier marginal, T3 unsigned base, T4 availability) — T1/T2 the primary signed pair |
| Controls | trap_load_derangement (≥2000 seeds, PRIMARY signed null) + matched_unconditional (≥25 seeds) + ordinary_touch (disclosure) + reversal_path_swap tripwire (HARD) + required positive control |
| Code modules | **1 new shared module** `xen.sigbar.trap`: IB reuses `acceptance.{find_pokes,evaluate_discriminator,label_outcomes}` UNMODIFIED with `assert_ib_matches_frozen` (byte-identical to SPDR-007's reject set); PVA/PRIOR add `find_pokes_at_level` + a `D4-t50-w30` close-count re-implementation regression-guarded to reproduce `evaluate_discriminator` on the IB level; plus reclaim-entry, reversal MFE/MAE to `opposite_edge`, opposite-edge/poke-extreme race, `trap_load` (signed `delta_ratio_resid`), per-boundary tercile-cut freeze, load derangement, matched-unconditional draw, path-swap. `acceptance.py`/`profile.py` are NOT modified. Runner `SPDR-008/screen_code/trap_screen.py`. Inherited: `xen.sigbar.{sessions,acceptance,profile,baselines,fences}` (+ `spine` helpers), `xen.evaluation`; `profile.{build_profile,poc_and_value_area}` supplies PVA edges under the frozen K-UNIFORM kernel — no new profile code. |
| Plots | ≤5 plot types, **faceted by boundary type {IB, PVA, PRIOR}**: trap_load distribution + tercile cuts (DESIGN vs CONFIRM) · reversal MFE by load tier with CI · monotonicity ρ vs derangement null · trap-vs-matched-control availability · per-(boundary × symbol) allocation map (reversal bps vs floor) |
| Artifacts | `results/{universe_membership,trap_load_cuts,mde_curves,floor_table,trap_DESIGN,trap_CONFIRM,derangement,tripwire,layers,allocation_map}.{json,parquet}` · `screen.md` (neutral quantification) · `analysis.md` (**fresh-context analyst — mandatory, SPDR-001 lesson**) |

**Execution order is strict.** cost floor + data-only IB-width thresholds + MDE curves published → DESIGN estimation of trap-load tercile cuts → freeze `trap_load_cuts.json` + hash → CONFIRM verification (once) → T1–T4 reads + controls + tripwire (derangement ≥2000 seeds, matched ≥25 seeds) → layers + allocation map → `screen.md` → fresh-context analyst → operator disposition. A CONFIRM number computed before the freeze is unattributable and re-runs.

## §10 Amendment ledger (opens empty — pre-measurement amendments append at QA; L-23)

All five below are **pre-measurement** (QA run 1, 2026-07-21) — logged before any read on real DESIGN/CONFIRM data.

```
AMENDMENT-1 (QA-1 Issue 1): trap_load is SIGNED BY MEASURED FLOW — poke_side × Σ delta_ratio_resid
  (the A5 Δ/V signed-direction column), not side_sign × Σ delta_abs_resid (magnitude). The prior
  form took its sign from price geometry, reducing the primary signed read to magnitude×geometry (a
  P-01 confound the T3 control already partly carries). §1/§3.2/§6.1 rewritten; disclosure inventory
  variant added. DIRECTION: TIGHTER (removes a magnitude×geometry confound from the signed read).
  Count: 0L/1T/0N.
AMENDMENT-2 (QA-1 Issue 2): frozen-reuse boundary stated exactly — IB reuses find_pokes/
  evaluate_discriminator/label_outcomes UNMODIFIED (byte-identical to SPDR-007's reject set,
  asserted); PVA/PRIOR use NEW trap.py level-generalised plumbing that re-implements the frozen
  D4-t50-w30 form, regression-guarded to reproduce evaluate_discriminator byte-identically on the IB
  level; acceptance.py is not modified (pin preserved). §3.1/§9 rewritten. DIRECTION: TIGHTER
  (pin-preservation + equivalence guards added). Count: 0L/2T/0N.
AMENDMENT-3 (QA-1 Issue 3): golden trace GT-2 (DOWN branch) and GT-3 (PVA/PRIOR — the widening's
  core) pinned to concrete named sessions with hand-derivable input state, via
  design_derivations/gt_derive.py; GT-1 TRAP-membership (reclaim) confirmed. §8 concretised.
  DIRECTION: NEUTRAL (reproducibility). Count: 0L/2T/1N.
AMENDMENT-4 (QA-1 Issue 4): CONVERSION-PIN gains the mandated measured-value line (reference-symbol
  DESIGN-median ib_width_bps) + a worked reversal_bps-vs-floor row. §6.1. DIRECTION: NEUTRAL
  (units declaration). Count: 0L/2T/2N.
AMENDMENT-5 (QA-1 Issues 5,6): control-label legend (A/B/C) added; uniform-IB-width-divisor wording
  corrected for PVA/PRIOR (divisor cancels for money bps; no "≈ ib_width_bps" claim off IB; types
  read independently, not compared). §4.2/§3.2/§6.1. DIRECTION: NEUTRAL (clarity). Count: 0L/2T/3N.
AMENDMENT-6 (build-time, pre-measurement): §8 golden trace now pins trap_load as the DEFINITION
  (`poke_side × Σ delta_ratio_resid`, residual) rather than the raw `poke_side × ΣΔ` proxy, computed
  independently in gt_derive.py. Smoke-testing the built xen.sigbar.trap surfaced GT-3(b) (BTC PRIOR
  2022-07-16): raw ΣΔ +573 but residual −0.7273 — a net-buying poke BELOW the seasonal norm, correctly
  demoted to a weak trap (the seasonal-normalisation discipline, §3.2). The §8 caveat's "investigate,
  not accept" was exercised and resolved: the residual is the pinned measure and QA diffs it, not the
  raw sign. DIRECTION: TIGHTER (the oracle now pins the exact definition, not a proxy that can
  sign-diverge). Count: 0L/3T/3N.
```

AMENDMENT-7 (post-QA-run-3, operator-directed "full machinery"): the first-pass runner shipped
  detection but omitted adjudication machinery (QA run 3 REVISE). Per operator direction, the full
  machinery is implemented and the screen re-run: (a) reversal_path_swap now adjudicates the trap−
  control CONTRAST collapse with the pooled bite `corr(swapped price MFE, donor real MFE)` and the
  material-edge precondition (reuses `spine.outcome_path_swap`/`path_swap_bite`); (b) PER-CELL
  derangement null (2000 seeds, rank-Pearson) on every powered (boundary×symbol) cell, with CONFIRM
  sign-agreement, so the K=3 cluster is null-tested not eyeballed; (c) MDE published per read (T1 =
  derangement-null 95th pct; T2/T4 = additive-plant sweep); (d) T4 gains a day-clustered CI; (e) T3
  ordinary-touch (non-trap boundary pokes, −poke_side excursion) implemented. DIRECTION: TIGHTER
  (adds the design-mandated adjudication that was missing). Count: 0L/4T/3N.
```

AMENDMENT-8 (post-machinery, operator-directed "fix and rerun"): the reversal_path_swap tripwire is
  corrected to adjudicate the SIGNED reads it can actually referee. A within-trap future-derangement
  preserves the trap mean, so it CANNOT referee the T4 mean-availability contrast (B-6 mean-vacuity);
  the prior code compared swapped-vs-raw excursion MEANS, which is neither the T1/T2 collapse nor a
  valid T4 test. Corrected: the tripwire now recomputes **T1 ρ(load, swapped excursion)** and the
  **T2 HIGH−LOW tier contrast under the swap** (both collapse toward 0 when each trap's outcome is a
  random other trap's future — the pairing the swap legitimately destroys), with the material-edge
  precondition on the SIGNED reads and the pooled bite unchanged. T4's causality is stated to rest on
  the ≤t−1 construction + the matched-unconditional control (the unconditional-entry comparison
  itself), NOT the mean-preserving swap. Verified on the sample: T1 ρ 0.071→−0.042 under swap, bite
  0.64. DIRECTION: TIGHTER (removes a vacuous/incorrect tripwire statistic; the HARD check now has
  valid bite on the reads it adjudicates). Count: 0L/5T/3N.
```

**Running count: 0 LOOSER / 5 TIGHTER / 3 NEUTRAL.** No amendment loosened a validity check or an
event definition; the five TIGHTER are correctness/enforcement fixes; no one-directional streak ≥ 3.
Further pre-measurement changes append here with direction.
