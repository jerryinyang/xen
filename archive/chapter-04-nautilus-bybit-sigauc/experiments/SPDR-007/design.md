# SPDR-007 — Design: the statistical spine (S1 + S2), CF-SIGAUC-001 master gate

**Item:** SPDR-007 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §4 seq 3 · **Lane:** SPDR (TRAIN-only screen)
**Source (NORMATIVE):** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` — Appendix B Phase 4, S1, S2, §6.2, §6.3, §6.6, §6b, §6.10 falsifier #1.
**Predecessor pin:** `python/experiments/INFR-018/results/instrument_registry.json`, `pin_sha256 5c3869845bd514bf…`.
**Deliverable:** the layered evidence for the source's **master go/no-go** — does the anchored-break excursion spine reproduce out of its estimation band, does regime conditioning hold, does Δ-coherence stratify — each measured **against a matched unconditional baseline**, with the money floor computed first.

**A SPDR result is never a tradability claim** (`docs/references/spdr-lane.md`). This item spends **0 counted reads**, touches **no TEST band**, **never queries the holdout**, and **registers nothing**. Disposition only; the operator signs it.

---

## §0 Scope fence

| | |
|---|---|
| **Produces** | the DESIGN-estimated Protection level per stratum; its realised CONFIRM hit rate; the target-before-invalidation race rate; the IB-width regime read; the Δ-coherence read; every one of these minus its matched unconditional baseline; the per-symbol money floor |
| **Must NOT produce** | a net tradable-edge claim, a deployability claim, a family status change, a counted read, any TEST or holdout contact, any per-level Δ attribution, any local accounting primitive |
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01Z)` = estimation. CONFIRM `[2023-03-01Z, 2023-12-18Z)` = verification, read **once**, **TRAIN-INTERNAL** (checkpoint-014 §5 / D3) — not out-of-sample in the programme's sense, and labelled so in every artifact. TEST `≥ 2023-12-18` **never read**. Holdout `≥ 2025-01-08` **never queried**. |
| **Counted reads / slots** | 0 / 0 |

### Applicability of standard design blocks

| Block | Status |
|---|---|
| Nautilus `BacktestNode`; `xen.adjudication`; `xen.estimand_validation` gate | **N/A — SPDR lane** (`spdr-lane.md`: vectorised Python, no P&L booked, no estimand-gated verdict). The integrity substitute is the code-asserted band fence + causal `t−1` self-check (§7). A `WORTH_EXPLORING` graduates into the Nautilus pipeline, where these bind. |
| §10 SPREAD-SCALE-ROUTING | **APPLIES** — §6.4. |
| §11 spread as a verdict leg | **N/A with reason** — no SUPPORTED/tradability band is emitted. The 1× spread is nonetheless a binding leg of the §6.3 money floor. |
| §12 amendment ledger | 9 QA-run-1 + 2 ratified developer deviations: **0 LOOSER / 6 TIGHTER / 5 NEUTRAL** (§10). |
| §13 battery rules | **APPLIES** — §6.5, §6.6, §7. |
| L-29/L-30/L-31 (Nautilus) | N/A — no engine run. |

### Frozen inputs — re-hashed at every entry point, `assert_frozen_inputs()` raises on mismatch

| Input | Pin | Consumed as |
|---|---|---|
| `INFR-018/results/instrument_registry.json` | `pin_sha256 5c3869845bd514bf…` | anchor **A-USOPEN**, IB **L = 15 min**; A6 = **D4, τ=0.50, W=30 min**, poke **δ = 0.0**, qualify window 30 min; per-symbol class residual thresholds |
| `INFR-017/results/seasonal_baselines.parquet` | sha256 `1b7244c8…` | A5 residuals (`delta_ratio_resid`, `delta_abs_resid`, `range_resid`, `volume_resid`) — the Δ-coherence stratifier reads **residuals only**, never a raw Δ number |
| `INFR-017/results/column_pins.json` | `pin_sha256 e3b9fd9b…` | `SpreadBps` status = **UNUSABLE** |
| Catalog fence manifest | sha `35d3375e…` | `train_end 2023-12-18`, `holdout_start 2025-01-08` |

**May NOT rely on:** `SpreadBps` as a spread or cost input; flip-pair spreads outside the 20 audited symbol-days without recomputation; the §2.5 spread-regime layer (**UNAVAILABLE — NO USABLE INPUT**, INFR-018 §5.3, binding here: the source's volatility-**and**-spread regime match of §6.3 is executed on volatility only, and every read states it); breadth beyond the DESIGN-bank-covered instruments.

**Inherited scope limit, carried in the headline (INFR-018 `anchor.resolution`).** The frozen anchor's own selection contrast was **not a resolved effect**: A-USOPEN×15 `E = +0.100`, day-clustered CI `[−0.282, +0.444]` (contains zero), **below its own MDE of 0.50**; the four cells whose CI excluded zero were all *negative*. Stage I needed a parameter and the selection rule delivered one — but SPDR-007 is not measuring on top of an established anchor effect, and no read here may imply that it is.

---

## §1 Mechanism statement

```
MECHANISM: An anchored participation window (US equity open, 15-min initial balance) fixes the
session's reference range. The first side to force ACCEPTANCE beyond an edge — half or more of
the next 30 minutes closing beyond it (frozen A6) — is claimed to have won the session's
defining auction, so the remainder of that session resolves asymmetrically in the break's
direction. The P&L-bearing object is a SINGLE-LEG, SESSION-HORIZON position: one entry at the
open of the bar following acceptance confirmation, one exit at the first of {Protection Level,
invalidation stop, session end}. Cadence is sparse — at most one such event per symbol-session.
S2 adds the management claim: the Protection Level is an ORDER STATISTIC of that same
population's favourable excursion — the (1−p) quantile at p ≈ 0.65–0.70 — estimable on one band
and reproducing on the next, conditionally on the IB-width regime.

DERIVED:
  estimand = per-event favourable / adverse excursion from the entry price to session end,
             normalised by that session's own IB width, and the target-before-invalidation
             race outcome on the same path — an EVENT-LEVEL object, because the traded object
             is a single leg with no adds, no ladder and no carry (L-16: episode-native
             estimands are required only for episode-native P&L; here event == episode)
  null     = MATCHED UNCONDITIONAL entries: same symbol, same session, same side, same
             normaliser, arbitrary post-IB entry minute (source §6.3 — conditional minus
             matched unconditional IS the edge). Second null: side labels deranged across
             events within calendar-day blocks
  horizon  = the anchored session remainder, taken from S1's own LIKELIHOOD field
             ("session horizon"), not chosen for power
  test     = calendar-day-clustered block bootstrap on paired day-level contrasts (source §6b:
             episodes, not bars), reported as report layers with interpretation bands
             (L-32/INFR-016), never as gates
```

**Anti-L-13 check.** This machinery is not transferable: the estimand is normalised by *this family's* IB-width object under *this* frozen anchor; the null is a same-session, same-side re-timing that only exists because the conditioning event is a clock-anchored boundary acceptance; the horizon is the source's own session binding. No prior Xen referee stack is reused — `xen.evaluation` supplies bootstrap/MDE primitives as tools, not as an adjudicator.

---

## §2 Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES.
    Both are the single-leg session-horizon position described in §1. The measured quantities
    (MFE_norm, MAE_norm, TP-before-stop) are functions of exactly the path that leg would
    experience. No multi-leg structure exists, so no episode aggregation is required (L-16).
  measured conditioning event == traded entry event: YES.
    The conditioning event is A6 acceptance CONFIRMED at qualify_end. The trade is entered at
    the OPEN of the bar whose OpenTime == qualify_end — the first instant the rule is decidable.
    There is no resting limit, no touch-fill, and no fill at a level the rule itself defines,
    so the B-4 entry-seam mismatch that cost CF-MR-004 its availability leg cannot arise here.
  effect-splitting windows non-overlapping: YES, code-asserted —
    IB [anchor, anchor+15)  ⟂  poke search [anchor+15, session_end)  ⟂
    qualifying [poke_ts, poke_ts+30)  ⟂  outcome (qualify_end, session_end].
    The excursion is measured STRICTLY AFTER the entry bar opens; the entry bar's own range is
    excluded from MFE/MAE (it would import the decision bar into the result).
    `acceptance.assert_windows_disjoint` + a new `spine.assert_entry_after_qualify` raise.
```

---

## §3 The event, the estimand, and the resolution rule

### 3.1 Event construction (fully inherited — no new selection)

Per (symbol, session) on the frozen anchor:

1. `sessions.anchor_table(A-USOPEN)` → 24h sessions from 09:30 `America/New_York`, DST-correct.
2. `sessions.session_breaks(bars, anchors, 15)` → IB high/low/width; coverage `< 0.9` ⇒ `INCOMPLETE`, **counted, never silently dropped**.
3. `acceptance.find_pokes(..., delta_frac=0.0)` → the first bar whose High (Low) trades beyond the IB edge; qualifying window `[poke_ts, poke_ts+30)`; pokes whose window would run past session end are dropped and **counted**.
4. **A6 = D4-t50-w30:** accept iff ≥ 50% of the 30 qualifying bars *close* beyond the poked edge. Accepted pokes are the **S1 confirmed breaks** — the event population. Rejected pokes are retained as the disclosure denominator (the accept rate is part of the read).

**Nothing above is re-raced, re-tuned, or re-parameterised.** Any change to anchor, L, discriminator, or δ is a Stage-I amendment that invalidates the pin and re-runs INFR-018.

### 3.2 Entry, exit, and the estimand

| Quantity | Definition (L-21 unit pin stated with every number) |
|---|---|
| `entry_ts` | the bar with `OpenTime == qualify_end` |
| `entry` | that bar's **Open** (decision at bar open on confirmed data ≤ t−1) |
| `side` | `poke_side` (+1 up-break, −1 down-break) |
| outcome window | `(qualify_end, session_end)` — bars strictly after the entry bar |
| `MFE` / `MAE` | max favourable / adverse excursion of **real prices** from `entry` over that window |
| **`ib_width`** | **this session's IB high − IB low, in price units** — the divisor object for every normalised number in this design |
| `mfe_norm`, `mae_norm` | `MFE / ib_width`, `MAE / ib_width` |
| `ib_width_bps` | `1e4 × ib_width / ((ib_high + ib_low)/2)` — the money conversion factor (§6.3) |
| `asym` | `mfe_norm − mae_norm` (disclosure; the source's S2 object is the MFE quantile, not the asymmetry) |

**Resolution rule (source §6.2, frozen before results).** Target-before-invalidation on the same path:
`TP1 = Protection Level` (§3.3), `STOP = TP1 / 2` (the source's 1:2 R, S2 LIKELIHOOD — **pinned, not swept**; a sweep would be a second selection budget).
Outcome ∈ {`TP`, `STOP`, `TIMEOUT` at session end}. **Same-bar ambiguity is resolved pessimistically:** if a single 1-minute bar's range contains both levels the outcome is `STOP`, because sub-minute ordering is unavailable (source A2, card ban 3) and the conservative direction is the only defensible one.

### 3.3 The Protection Level (S2)

**Quantile direction, stated once and asserted in code** — a target reached with probability `p` is the **(1−p)** quantile of MFE. `p = 0.65 → q = 0.35`; `p = 0.70 → q = 0.30`. The reversed reading roughly doubles TP1 and falsifies S1 for the wrong reason (source S2 MECHANISM). `spine.protection_level()` raises if asked for a quantile above 0.5.

- **Estimated on DESIGN only**, per stratum, frozen to `results/protection_freeze.json` with its hash **before any CONFIRM path may execute** (runner raises otherwise).
- **Verified on CONFIRM once**: realised `P(mfe_norm ≥ q̂)` against nominal `p`.

---

## §4 The four reads (report layers — the operator judges; L-32/INFR-016)

**R0 — money floor.** Its two parts have different timing (I-7): the **cost floor** (taker +
spread + funding) and the data-only "TP1 must exceed X IB widths" thresholds are computed and
published **before any estimation** — the binding first act (card §6). The **TP1-vs-floor
comparison** needs the DESIGN-estimated `q̂` and therefore follows estimation; §9's order
reflects this. See §6.3.

| id | Question | Statistic | Band |
|---|---|---|---|
| **R1** | Does the DESIGN-estimated Protection Level reproduce on the next band? | `calib_err = realised_hit_rate(CONFIRM) − p`, per stratum, at `p ∈ {0.65, 0.70}` | §5.1 |
| **R2** | Under the source's own resolution rule, how often does the target come before invalidation? | race win-rate `w = P(TP before STOP)`; reported beside gross breakeven `p₀ = 1/(1+R) = 1/3` and the **cost-adjusted** breakeven of §6.3 | §5.2 |
| **R3** | Does regime conditioning hold — do narrow IBs precede larger *relative* excursions, and does conditioning improve reproduction? | **contrast-only** `ρ_signal − ρ_control` on `(ib_width_pctl, mfe_norm)`; plus a **raw-MFE** regime read (§5.3, I-3); and `\|calib_err\|` conditional vs unconditional | §5.3 |
| **R4** | Does Δ-coherence stratify the break population? | contrast in `mfe_norm` and in `w` between coherence terciles | §5.3 |

**R5 — the matched unconditional baseline runs under every one of R1–R4 and is binding** (card §5 P-01 mitigation). Every headline is reported as **signal minus matched control**, never as a level. A spine that reproduces identically on the control arm is a **P-01 confirmation** and is recorded as one.

### 4.1 Strata (per-stratum binding; pooled is disclosure-only — L-03)

`symbol` × `regime tercile` × `coherence tercile` × `chronological third`, plus each margin. **Pooled figures are disclosure-only unless cross-symbol homogeneity is demonstrated.**

- **Regime** — `ib_width_pctl` = rank of this session's `ib_width_bps` within the symbol's **trailing 60 sessions, strictly prior** (≤ t−1; a full-band quantile would be acausal — see the §7 disclosure probe). Warmup rule (I-8): a session with ≥ 30 prior sessions uses all available priors up to 60 (a shortened window down to 30); a session with < 30 priors is **excluded and counted**. Terciles: NARROW / MID / WIDE.
- **Coherence** — `coh = mean(delta_ratio_resid over the qualifying-window bars) × side`, from the **frozen A5 baselines** (residual, never a raw Δ). Tercile cut points are computed **on DESIGN, per symbol, frozen, and applied unchanged to CONFIRM**. Symbols without fitted baselines (3 of 197 lost to corrupt staging at INFR-017) are excluded and **named**.
  *Secondary, disclosure-only:* the break bar's pinned §2.3 class (`DRIVE` vs `VACUUM_RUN`) — the source's own wording, but `VACUUM_RUN` is rare (7,732 bars panel-wide at INFR-018) and is expected UNPOWERED, which is why the continuous score is primary.

### 4.2 Controls

```
CONTROL matched_unconditional (PRIMARY; class: within_sample_attribution → REPORT LAYER):
  question answered: does conditioning on an ACCEPTED anchored break beat entering the same
    session, on the same side, at the SAME SESSION PHASE, with the same normaliser?
    (source §6.3; card §5 P-01 mitigation)
  population: for each real event (side d, phase φ = entry_phase = mins_since_anchor at
    qualify_end), 30 control entries (≥ L-19 floor of 25) are drawn CROSS-SESSION
    (AMENDMENT-10 / D-1, operator-ratified 2026-07-21):
      - draw 30 DONOR sessions (seeded) from the SYMBOL's own session pool, excluding the
        event's own session and any session too short to run phase φ;
      - enter each donor at anchor(donor) + φ minutes on side d — the OPEN of the bar there —
        normalised by the DONOR session's own IB width.
    WHY CROSS-SESSION, not within-session (D-1): the design originally drew 30 within-session
    entries at a phase matched to the real events' entry-phase distribution. That is INFEASIBLE
    by construction — the real event enters at φ ≈ 45–55 min, which is precisely the
    [poke − 30, qualify_end + 30] exclusion band, so a within-session phase-matched draw always
    lands in the exclusion and is forced to a mid-session minute, reintroducing the exact
    horizon confound QA I-2 fixed (measured on the run: within-session control remaining-horizon
    723 min vs the real 1391). Phase-matching therefore REQUIRES other sessions. Cross-session
    donors at the event's own φ reproduce the real events' remaining-horizon by construction
    (measured 1395 vs 1391), match side, are disjoint (donor ≠ event session), and are
    unconditional on the A6 call — the source §6.3 / card §5 P-01 "session phase" match.
    DISJOINT from the signal population: a donor session ≠ the event's session; different entry
    bar ⇒ different entry price, outcome window and race path.
    HORIZON-MATCH DISCLOSURE: the realised remaining-horizon distributions of the two arms are
    emitted side by side per stratum, so the match is auditable, not asserted.
  what it can show that the signal series cannot: whether a same-side, same-phase entry in an
    UNCONDITIONAL session produces the same excursion distribution — i.e. whether the number
    belongs to the ACCEPTANCE EVENT or to sessions' generic directional behaviour at that phase.
    Without it, "the quantile reproduces" is a statement about price having quantiles.
  bite/MDE: co-designed plant, swept and PUBLISHED BEFORE the real read. Inject an additive
    shift u on the signal arm's mfe_norm and trace the day-clustered CI of the paired day-level
    contrast as u grows; the declared MDE is read OFF THAT CURVE at the realised n per stratum.
    MDE is published in CONTRAST UNITS — the units the contrast itself is measured in — so
    `effect` and `mde` compare like with like (INFR-018 AMENDMENT-5; the units seam that made
    EXP-025 wrong by 4×, L-21/L-24). For R2 the plant instead shifts TP1 proportionally, but a
    TP1 shift maps non-linearly to the win-rate contrast; the swept curve is therefore reported
    with its MDE in **w-contrast units** (the realised win-rate contrast), NOT in TP1 units, so
    the like-for-like requirement holds for the race read too (I-9).
  non-vacuity: it moves the entry price and therefore the entire excursion path — the
    sufficient statistic of every read, not its labels.
  expected if H true: contrast > 0 and stable across thirds. If H false: contrast ≈ 0 ⇒ the
    spine reproduces unconditionally ⇒ recorded as a P-01 confirmation.
  disclosure: collapse fraction (control statistic / signal statistic) per stratum.
  destroy form: not a permutation — an independent re-drawing of the entry instant.
  exit-matched (L-24 F04): every control entry is resolved under the SAME TP/STOP rule and the
    same pessimistic same-bar convention. The exit is path-dependent, so an unmatched control
    would price the exit, not the entry.

CONTROL side_derangement (class: within_sample_attribution → REPORT LAYER):
  question answered: does the BREAK SIDE carry directional information, or would a random side
    at the same instant produce the same excursion asymmetry?
  population: the same entry instants with `side` DERANGED across events within calendar-day
    blocks; regenerated until the fixed-point count is EXACTLY 0 and asserted (L-28 —
    VAL-008 shipped an 11.1%-fixed-point destroy).
  singleton / coverage (I-5): a calendar-day block with one event, or an all-one-side block,
    cannot be deranged to zero fixed points (INFR-018 I-57). Such events are DROPPED and
    COUNTED; the deranged fraction is reported beside the collapse fraction, exactly as the
    tripwire reports donor coverage. The read is taken on the derangeable subset with its n
    stated.
  TP1 basis under derangement (I-5): the race outcome is resolved against the FROZEN DESIGN q̂,
    NOT a quantile recomputed on the deranged arm — deranging side must test whether side
    carries direction, holding the target fixed, not re-estimate the target.
  DISJOINT: at every index the (entry, side) pair differs from the real pair.
  bite/MDE: plant a synthetic directional effect of known size on the real arm and confirm the
    deranged arm reads ≈ 0 across the sweep; MDE published before the read.
  non-vacuity: MFE and MAE are defined RELATIVE TO SIDE, so deranging side re-partitions the
    favourable/adverse split — the joint statistic, not a relabelling.
  NOT VACUOUS BY SYMMETRY (B-6 check): a per-event sign FLIP would be vacuous, because it maps
    asym → −asym by identity. A DERANGEMENT across events does not: it pairs each entry with
    another event's side, so the null is "side is uninformative", not "asym is antisymmetric".
  expected if H true: real ≫ deranged. If H false: equal.
  disclosure: collapse fraction per stratum.
```

### 4.3 Leak tripwire (HARD — validity)

```
TRIPWIRE outcome_path_swap (class: future_destroy — HARD):
  Replace each event's OUTCOME-WINDOW price path with the outcome path of a DERANGED donor
  event (matched on remaining-session length; zero fixed points, asserted), re-timed onto the
  target's window. Everything at or before entry is untouched, so every conditioning quantity
  — the break, the A6 call, the regime percentile, the coherence score, the ib_width divisor —
  is IDENTICAL, while the outcome is unrelated to it.
  vacuity check: MFE/MAE/race are functions of the outcome path alone; replacing it moves the
  metric's entire support, not its labels.
  Donor paths are re-based to the target's entry price so the swap destroys the OUTCOME's
  relation to the conditioning, not the price scale (an unrebased donor would randomise level
  as well and inflate the destroy — INFR-018 scope limit 5).
  STATISTIC, PER READ (I-4). The tripwire adjudicates each read on the EFFECT-CONTRAST it
  produces, so "collapse" is unambiguous:
    - R5 excursion contrast (primary): collapse_fraction = destroyed_contrast / raw_contrast
    - R2 race-rate contrast, R3 ρ-contrast, R4 tercile contrast: same ratio on each contrast
    - R1 (quantile reproduction / calib_err) is NOT adjudicated by the swap: calib_err is a
      reproduction diagnostic, not an effect-contrast, and destroying the outcome makes it
      random rather than collapsing it toward zero. R1's integrity rests on the freeze-before-
      CONFIRM ordering and the band fence (a frozen q̂ cannot see CONFIRM), both HARD in §7 —
      stated here so the HARD set is not silently assumed to cover R1.
  MUST COLLAPSE: expected |collapse_fraction| ≈ 0 on each adjudicated contrast.
  MATERIAL-EDGE PRECONDITION (AMENDMENT-11 / D-2, operator-ratified 2026-07-21). The HARD
  survival rule fires ONLY when the RAW contrast is a material edge — its day-clustered
  interval excludes zero. A future-destroy cannot adjudicate a leak on an edge that does not
  exist: with raw contrast ≈ 0 the collapse ratio is noise/noise and "survival" (|cf|>0.25) is
  meaningless. When no material raw edge exists the tripwire is reported UNPOWERED
  (`NO_MATERIAL_EDGE`) — NOT a leak and NOT a hard fail. This cannot hide a real leak: a
  material surviving edge still HARD-fails. It is the L-32 discipline (no auto-decide at a point
  of no estimator resolution) applied to the tripwire.
  SURVIVAL := (raw contrast CI excludes zero) AND (|collapse_fraction| > 0.25 with the SAME SIGN
  as the raw contrast) AND (swapped contrast CI excludes zero). The 0.25 threshold is INHERITED
  from the INFR-018 sealed tripwire (operator-ratified 2026-07-20); it is not re-asserted here
  (L-24 F06).
  IF A MATERIAL ADJUDICATED READ SURVIVES: the construction is reading the outcome ⇒ EMISSION
  INVALID ⇒ fix and re-run. NEVER read as "no effect".
  coverage: events with no usable donor are dropped and COUNTED; the spliced fraction is
  reported beside the collapse fraction.
  permutation-based: YES → DERANGEMENT, zero fixed points, asserted.

POSITIVE CONTROL bite test (REQUIRED — the screen refuses to emit a disposition without it):
  pooled across all symbols (AMENDMENT-11 / D-2 — a per-symbol plant fails on low-n symbols and
  the original within-arm "sign split" plant was tautological). The genuine, non-tautological
  bite: the swap installs the DONOR's re-based PRICE path, so each swapped event's price-level
  MFE is the donor's own raw price MFE over the (possibly truncated) window. The test correlates
  swapped price MFE against the DONOR's real price MFE pooled: `corr(mfe_swapped, mfe_donor)`.
  REQUIRED OUTCOME: corr > 0.5 (measured on the run: 0.77). If it fails, the swap reached
  nothing the reads consume and the tripwire has no teeth (INFR-018 AMENDMENT-6 — the exact
  defect that shipped a toothless gate there). Price MFE, not the IB-width-normalised asym,
  because the donor and target divisors differ and would attenuate an otherwise clean signal.
```

---

## §5 Interpretation bands — labels, never gates

**Order matters: UNPOWERED is evaluated FIRST**, so an unmeasurable stratum is never mislabelled WASH ("measured, cannot distinguish") when the truth is "not measurable at this n" (L-32 / B-5).

### 5.1 R1 — Protection-level reproduction (the master-gate read)

```
UNPOWERED:    MDE on calib_err > 0.05 at the realised n  → EXCLUDED FROM NEGATIVES
REPRODUCES:   |calib_err| ≤ 0.05 and the day-clustered CI contains the nominal p
DRIFTED:      0.05 < |calib_err| ≤ 0.10
BROKEN:       |calib_err| > 0.10 with CI excluding p
```
`0.05 / 0.10` are **reading labels for the operator**, not machine thresholds; nothing is dropped or hidden at any of them.

### 5.2 R2 — race rate

Reported as `w` with its day-clustered CI beside **two** breakevens: gross `p₀ = 1/3`, and the cost-adjusted `p₀ᶜ = (STOP + cost_rt) / (TP1 + STOP)` per symbol from §6.3. Bands: `ABOVE_COST_BREAKEVEN` / `BETWEEN` / `BELOW_GROSS_BREAKEVEN` / `UNPOWERED`. **This is a screen read, not a tradability claim** — it is reported per stratum against a matched control and carries no deployability meaning.

### 5.3 R3 / R4 / R5 contrasts

```
UNPOWERED:    MDE > |plausible effect| at the realised n  (tested first)
SUPPORTED:    effect ≥ its own MDE and ci_low > 0
SUGGESTIVE:   ci_low > 0 but effect < its own MDE
WASH:         |effect| < MDE  → "cannot distinguish", never a refutation (L-11)
CONTRADICTED: ci_high < 0
POOLED:       disclosure-only unless homogeneity is demonstrated (L-03)
```

**R3 normaliser-mechanic guard (I-3, binding).** `mfe_norm = MFE / ib_width` induces a spurious
*negative* `ρ(ib_width_pctl, mfe_norm)` by construction — a larger IB mechanically shrinks the
ratio, independent of any contraction→expansion mechanism (the "dispersion = normaliser mechanic"
that inverted the first-pass SPDR-001 read). Therefore R3's binding statistic is **the contrast**
`ρ_signal − ρ_control` (both arms share the divisor, so the mechanic cancels); the raw signal ρ is
never a headline. A **second, un-normalised disclosure** is emitted — Spearman `ρ(ib_width_pctl,
MFE_bps)` on raw excursion in bps — so the physical contraction→expansion claim is separable from
the normaliser artifact. Bands below apply to the contrast, not the level.

**Time stability (L-24 F02), reported not gated:** every read is repeated on the three chronological thirds of DESIGN and on CONFIRM; sign consistency and the per-third n are published.

---

## §6 Money floor, conversion pin, universe, power, uncertainty

### 6.1 Universe — binding block, declared before any cell runs

```
UNIVERSE (checkpoint-014 §6 D4; identical rule to INFR-018 — comparability is the point):
  n = 20 per day, re-evaluated daily at 00:00 UTC.
  Ranking statistic: trailing-24h QUOTE turnover = Σ over 1440 bars of Volume × (H+L+C)/3 [USDT]
    — base-asset Volume is not comparable across symbols and is rejected.
  Causality: day D's turnover ranks day D+1's membership (≤ t−1). Code-asserted.
  Eligibility: ≥ 1200 of 1440 trailing bars AND ADMITTED. Point-in-time, no membership list.
  Tie-break: lexicographic. Delisting: fails eligibility forward; no backfill, no exclusion of
  prior days (anti-survivorship, binding project-wide).
  Emitted: realised daily membership + its hash; MUST reproduce INFR-018's DESIGN membership
  hash f11dd7f0aea42f82… — a mismatch is a REVISE, not a rounding note.
```

### 6.2 Power (measured on disk 2026-07-21 under the FROZEN rule, not estimated)

The event population is **every A6-ACCEPTED poke** (`says_accept == True`) under the frozen
rule **D4-t50-w30, δ=0** — not `n_yes` (which counted only resolved-AND-accept pokes and was a
Phase-2 discriminator-scoring device, not the spine's population). Recomputed across the frozen
top-20 online panel per band (`pop.py`, designer-side; QA re-derives against the emission):

| Quantity | DESIGN | CONFIRM |
|---|---|---|
| Panel symbols with band bars | 140 | 187 |
| Total pokes (δ=0) | 13,802 | 23,604 |
| **A6 accepts = event population (`says_accept`)** | **7,148** | **11,453** |
| Per-symbol accepts: median | **34** | 51 |
| Per-symbol accepts: q25 / q75 | 16 / 84 | 27 / 90 |
| Symbols with < 40 accepts | 76 / 140 | 68 / 187 |
| Symbols with < 10 accepts | 18 / 140 | 12 / 187 |
| The 5 majors (BTC/ETH/SOL/DOGE/XRP), DESIGN accepts | 114 / 113 / 126 / 85 / 118 | — |

The CONFIRM band carries more panel symbols (187 vs 140) because later-listed instruments reach
coverage there; the master-gate reproduction read (R1) is checked on the **DESIGN-covered**
symbols, since a per-symbol Protection quantile exists only where it was estimated. CONFIRM-only
symbols are additional breadth, disclosure-only.

```
STRATA PREDECLARED UNPOWERED (never readable as negatives — B-5):
  - any per-symbol stratum below its published MDE floor at the realised n. At a median of 34
    accepts, roughly half the panel (76/140 below 40) is per-symbol marginal for a central-ish
    Protection quantile; the pooled estimator carries the thin symbols and is the honest
    PRIMARY for a tail quantile at this depth (per-symbol is binding only where its MDE clears).
  - any (symbol × regime tercile) or (symbol × coherence tercile) cell — three-way splits of a
    ~34-event symbol are power statements, not measurements
  - the VACUUM_RUN secondary class stratum (7,732 bars panel-wide at INFR-018)
  - any chronological third of a per-symbol read
  - every UNPOWERED cell is reported WITH its n and MDE, never folded into a failure
MDE: read off the co-designed plant curves (§4.2) at the realised n per stratum and PUBLISHED
  BEFORE the real read. No MDE is asserted from memory.
```

**Note on the pooled quantile and L-03.** A tail quantile at a per-symbol median of 34 events is
thin, so the Protection Level is estimated **both pooled and per-symbol**: per-symbol is binding
where its MDE clears, pooled carries the rest and is the primary for the master-gate read. This
is the one place a pooled figure is more than disclosure — declared here rather than smuggled —
and it is still reported beside the per-symbol table, never instead of it.

### 6.3 CONVERSION-PIN and the money floor (card §6 — the binding first act)

```
CONVERSION-PIN:
  divisor object: "this session's IB high − IB low in PRICE units, from the frozen anchor
    A-USOPEN with L = 15 minutes; expressed in bps as 1e4 × ib_width / ((ib_high+ib_low)/2)"
    — xen.sigbar.sessions.session_breaks, column `ib_width`; SPDR-007 screen_code/spine_screen.py
  measured value (DESIGN median ib_width_bps, computed from staging data 2026-07-21,
    NOT recalled): BTCUSDT 48.745 · ETHUSDT 69.958 · SOLUSDT 96.217 · DOGEUSDT 86.969 ·
    XRPUSDT 60.753   (the full per-symbol table is emitted for all 140 panel symbols)
  resulting effect: TP1_bps = q̂_{1−p}(mfe_norm) × ib_width_bps, computed per event and
    summarised per symbol. q̂ is the screen's own output and is NOT asserted here.
  cost floor: bybit_round_trip_cost_bps(liquidity="taker", spread_bps=<per-symbol>,
    hold_hours=<realised>) = taker RT 11.0 + spread RT + funding.
```

**Spread input.** `SpreadBps` is UNUSABLE (INFR-017 W2). Per INFR-017's own prescription the floor uses **`max(tick_bps, flip-pair_bps)`** on the five audited symbols and a **tick-size floor** elsewhere, each labelled: flip-pair is a *conservative upper bound* on the effective spread; tick is a *lower bound*. **Units, pinned:** the flip-pair median `|Δprice|` across side-flipping trade pairs is the full crossed spread, which is what a market-in/market-out round trip pays once — so it is passed as `spread_bps` (a round-trip quantity) to `t1_round_trip_spread_bps`, not doubled.

Floor arithmetic at design time, funding at 1.0 bps/8h over a ≤24h session hold (≈3.0 bps):

| Symbol | taker RT | spread RT = `max(tick, flip-pair)` | funding | **floor** | **TP1 must exceed** |
|---|---|---|---|---|---|
| BTCUSDT | 11.0 | 0.244 (flip) | 3.0 | **14.24 bps** | 0.292 IB widths |
| ETHUSDT | 11.0 | 0.305 (flip) | 3.0 | **14.31 bps** | 0.204 |
| SOLUSDT | 11.0 | 0.727 (flip) | 3.0 | **14.73 bps** | 0.153 |
| DOGEUSDT | 11.0 | **1.477 (tick > flip 1.470)** | 3.0 | **15.48 bps** | 0.178 |
| XRPUSDT | 11.0 | 1.929 (flip) | 3.0 | **15.93 bps** | 0.262 |

For DOGE the tick (1.47732 bps) exceeds the flip-pair estimate (1.47037), so the stated
`max(tick, flip-pair)` rule selects the tick — applied here per I-6.

```
FLOOR BAND (framing, not a gate — card §6):
  ABOVE_FLOOR          : the stratum's TP1 exceeds its floor → the disposition may be read as a
                         strategy candidate (still not a tradability claim — SPDR lane)
  AT_OR_BELOW_FLOOR    : recorded as MARKET SCIENCE, NOT STRATEGY — the source's own
                         framework-level falsifier ("surviving edges vanish inside costs at
                         their horizons"). It may still route forward, but only re-framed as
                         characterisation.
```

### 6.4 SPREAD-SCALE-ROUTING (mandatory, T1)

```
SPREAD-SCALE-ROUTING (emitted per symbol at screen time):
  estimated_rt_spread_bps: max(tick_bps, flip-pair) as above
  gross_edge_bps: the stratum's matched-unconditional CONTRAST expressed in bps
                  (contrast in mfe_norm × that stratum's median ib_width_bps)
  t1_undecidable: xen.evaluation.spread_scale_route(gross, rt_spread) — the 3× threshold is
                  used, never re-derived
  if YES: the stratum is reported AWAITING_MBP; pooled T1 reads stay disclosure-only.
```

### 6.5 Uncertainty

**Calendar-day-clustered circular block bootstrap** on the paired day-level contrast, via `xen.evaluation.block_bootstrap_ci` (INFR-004/L-20 hardened: effective block capped `< n`; 5-seed battery with per-seed bound spread; `block_sensitivity` ½×/1×/2× sweep; `trimmed_mean` robustness read). The resampling unit is the **calendar day**, carrying all symbols' events for that day together — sessions on one UTC day across 20 crypto perpetuals share a market-wide shock, and treating them as independent would understate variance by roughly the cross-sectional correlation. This is also the source's §6b requirement (episodes, not bars). Reported as **"the 95% interval excludes zero"**, never as a p-value (L-20).

The outcome windows of same-symbol adjacent sessions do not overlap (one event per session, exit by session end), so no block ≥ H inflation is required beyond the day clustering; the code asserts non-overlap rather than assuming it.

---

## §7 Integrity vs informative split

```
HARD (block — a failure means the EMISSION IS INVALID; fix the code/data and re-run; it is
never read as "no edge"):
  - future-destroy tripwire: outcome_path_swap must collapse, AND its positive control must survive
  - band fences: DESIGN / CONFIRM asserted on EVERY read path (`fences.assert_band`, raise not
    warn); TEST and holdout unreachable by construction
  - CONFIRM-before-freeze refusal: no CONFIRM path executes before results/protection_freeze.json
    exists with its hash
  - causal ≤ t−1: universe ranking statistic; regime percentile from strictly prior sessions;
    every conditioning input from bars at or before the entry bar's open
  - window disjointness (§2), including entry-bar exclusion from the excursion
  - frozen-input hash re-verification at every entry point
  - `fences.assert_no_per_level_delta` — per-level signed attribution raises (card ban 2)
  - `check_no_local_accounting` — no accounting primitive may appear in this experiment dir

INFORMATIVE (report layers; the OPERATOR judges — L-32 / INFR-016):
  every calibration error, race rate, Spearman, contrast, collapse fraction, stability read,
  floor comparison and band label. No `pass` field is emitted anywhere. Nothing is
  machine-dropped between layers. The disposition is an OPERATOR ACT on these layers.

DISCLOSURE PROBE (informative, not a gate): the regime percentile is recomputed from the
  WHOLE-BAND quantile (acausal) alongside the trailing-60 causal version, and the difference is
  published. Using a full-sample quantile as a conditioner is the classic silent leak in this
  read; measuring the gap makes it visible instead of asserting it away.
```

---

## §8 Golden trace — designer-derived, for QA to diff before execution

Computed from staging bars under this design's frozen rules (`gt_derive.py`, designer-side). **The developer must not regenerate these**; QA diffs the implementation's output against them.

```
GT-1  UP-side ACCEPT — ETHUSDT, session 2022-11-09 14:30Z (DESIGN)
      IB [14:30, 14:45)   high 1228.05  low 1187.45   ib_width 40.60  (336.162 bps of mid)
      poke_ts 2022-11-09 14:45:00   poke_side UP   poke_extreme 1240.45
      qualifying [14:45, 15:15)  30 bars  closes-beyond fraction 0.5667  ≥ 0.50 ⇒ A6 ACCEPT
      entry bar OpenTime 2022-11-09 15:15:00   entry = its OPEN = 1226.80
      session_end 2022-11-10 14:30:00   n_post 1394 bars
      MFE  97.80 = 2.4089 IBw     MAE 155.20 = 3.8227 IBw     asym = −1.4138
      [divisor object: this session's IB high−low in price units — L-21 unit pin]

GT-2  DOWN-side ACCEPT — SOLUSDT, session 2022-07-17 13:30Z (DESIGN; EDT, anchor at 13:30Z)
      IB [13:30, 13:45)   high 39.800  low 39.475   ib_width 0.325  (81.993 bps of mid)
      poke_ts 2022-07-17 13:46:00   poke_side DOWN   poke_extreme 39.445
      qualifying [13:46, 14:16)  closes-beyond fraction 0.9000 ⇒ A6 ACCEPT
      entry bar OpenTime 2022-07-17 14:16:00   entry = its OPEN = 39.25
      session_end 2022-07-18 13:30:00   n_post 1393
      MFE 0.990 = 3.0462 IBw      MAE 3.425 = 10.5385 IBw     asym = −7.4923
      Purpose: proves the DOWN branch, the DST-correct 13:30Z anchor, and that MFE/MAE are
      defined relative to SIDE.

GT-3  NEGATIVE trace — BTCUSDT, session 2023-01-11 14:30Z (EST, anchor at 14:30Z)
      IB high 17419.0 low 17372.0 width 47.0; poke_ts 14:48 extreme 17426.0;
      closes-beyond fraction 0.3667 < 0.50 ⇒ A6 REJECT.
      This session must NOT appear in the event population, and MUST appear in the accept-rate
      denominator. A screen that books it is conditioning on the wrong event.

GT-4  Fence + hash + order behaviour (must RAISE, not warn)
      (a) any read path invoked with OpenTime ≥ 2023-12-18 → raises;
      (b) a CONFIRM path invoked before results/protection_freeze.json exists → raises;
      (c) registry pin_sha256 ≠ 5c386984… or baselines sha ≠ 1b7244c8… → raises at entry;
      (d) protection_level(q) with q > 0.5 → raises (the reversed-quantile trap, §3.3);
      (e) a control entry minute inside [poke_ts − 30, qualify_end + 30] → raises.
```

---

## §9 Artifacts, complexity budget, execution order

| | |
|---|---|
| Statistical contrasts | 4 (R1 calibration, R2 race, R3 regime, R4 coherence) — each also against the matched control (R5) |
| Controls | 2 matched (report layers) + 1 future-destroy tripwire (HARD) + 1 required positive control |
| Code modules | **1 new shared module** `xen.sigbar.spine` (entry construction, MFE/MAE from entry, TP-before-stop race, protection quantile + calibration, matched-unconditional draw, path-swap). Runner `SPDR-007/screen_code/spine_screen.py`. Everything else is inherited from `xen.sigbar.{sessions,acceptance,classes,baselines,fences}` and `xen.evaluation`. |
| Plots | ≤ 5: MFE_norm distribution + protection level (DESIGN vs CONFIRM) · calibration curve across p · regime tercile excursions · coherence tercile contrast with CI · TP1 bps vs money floor per symbol |
| Artifacts | `results/{universe_membership,protection_freeze,mde_curves,floor_table,spine_DESIGN,spine_CONFIRM,tripwire,layers}.{json,parquet}` · `screen.md` (neutral quantification) · `analysis.md` (**fresh-context analyst — mandatory, SPDR-001 lesson**) |

**Execution order is strict.** cost floor + data-only IB-width thresholds + MDE curves published → DESIGN estimation of `q̂` → TP1-vs-floor comparison (needs `q̂`, so it follows estimation — I-7) → freeze `protection_freeze.json` + hash → CONFIRM verification (once) → controls + tripwire → layers → `screen.md` → fresh-context analyst → operator disposition. A CONFIRM number computed before the freeze is unattributable and re-runs.

## §10 Amendment ledger

All nine below are **pre-measurement** (QA run 1, 2026-07-21) — logged before any read on real
DESIGN or CONFIRM data. Each states its direction and the running count (L-23).

```
AMENDMENT-1 (I-1): §6.2 power table recomputed on the FROZEN rule and the CORRECT object.
  Population is the A6-accepted-poke count (`says_accept`) under D4-t50-w30 δ=0, not `n_yes`,
  and CONFIRM is D4 (the pin's freeze) not the D3 re-rank. New: DESIGN 7,148 / CONFIRM 11,453
  accepts; per-symbol median 34 (was mis-stated ~18). Verified from staging (pop.py).
  DIRECTION: NEUTRAL (a factual power correction; no acceptance bar moves). Count: 0L/0T/1N.

AMENDMENT-2 (I-2): matched-unconditional control is ENTRY-PHASE matched, not arbitrary-minute,
  so the excursion contrast is not confounded by outcome-window length.
  DIRECTION: TIGHTER (the contrast now isolates the event; horizon inflation removed). 0L/1T/1N.

AMENDMENT-3 (I-3): R3 binding statistic is the ρ CONTRAST (signal − control); the raw ρ is
  never a headline; an un-normalised raw-MFE regime disclosure is added.
  DIRECTION: TIGHTER (removes the normaliser-mechanic false positive). 0L/2T/1N.

AMENDMENT-4 (I-4): the future-destroy tripwire's collapse statistic is defined per read (on
  each effect-contrast); R1 is protected by freeze-order + fence, not the swap, and this is
  stated rather than assumed.
  DIRECTION: TIGHTER (enforcement clarity; the HARD set is now unambiguous). 0L/3T/1N.

AMENDMENT-5 (I-5): side_derangement gains a singleton/coverage rule (drop + count, coverage
  reported) and pins TP1 = frozen DESIGN q̂ under derangement.
  DIRECTION: TIGHTER (enforcement). 0L/4T/1N.

AMENDMENT-6 (I-6): DOGE money floor uses max(tick, flip-pair) = tick 1.477 → floor 15.48.
  DIRECTION: TIGHTER (a marginally higher cost floor). 0L/5T/1N.

AMENDMENT-7 (I-7): "money floor computed first" split into cost-floor (pre-estimation) vs
  TP1-vs-floor comparison (post-estimation); execution order updated.
  DIRECTION: NEUTRAL (timing clarification). 0L/5T/2N.

AMENDMENT-8 (I-8): regime-percentile warmup rule stated (≥30 priors → shortened window to 60;
  <30 → excluded and counted).
  DIRECTION: NEUTRAL (reproducibility). 0L/5T/3N.

AMENDMENT-9 (I-9): R2 race MDE reported in w-contrast units, not TP1 units.
  DIRECTION: NEUTRAL (units declaration). 0L/5T/4N.

AMENDMENT-10 (D-1, developer deviation, operator-ratified 2026-07-21): the matched-unconditional
  control is CROSS-SESSION (donor sessions entered at the event's own phase/side), not
  within-session. The within-session phase match is infeasible — the event occupies the
  early-session phase = the exclusion band, forcing a within-session draw to mid-session and
  reintroducing the horizon confound (measured 723 vs 1391 min). §4.2 rewritten.
  DIRECTION: TIGHTER (removes the horizon confound; the contrast now isolates acceptance). 0L/6T/4N.

AMENDMENT-11 (D-2, developer deviation, operator-ratified 2026-07-21): the HARD future-destroy
  tripwire fires only on a MATERIAL raw edge (raw contrast CI excludes zero) — a destroy cannot
  leak-test an edge that does not exist. The positive control is a POOLED bite correlation
  (swapped price MFE vs donor real price MFE, > 0.5; measured 0.77), replacing the tautological
  per-symbol sign-split plant. §4.3 rewritten.
  DIRECTION: NEUTRAL (a soundness precondition; a material surviving edge still HARD-fails, so it
  cannot hide a leak). 0L/6T/5N.
```

**Final count: 0 LOOSER / 6 TIGHTER / 5 NEUTRAL.** No amendment loosened a validity check or an
acceptance bar; the six TIGHTER are control/enforcement corrections, and there is no
auto-qualification to price in any case (every value read is a report layer, L-32). The two
developer deviations (10, 11) were discovered during implementation, flagged before the run of
record, and operator-ratified 2026-07-21. Any further pre-measurement change appends here with
its direction.
