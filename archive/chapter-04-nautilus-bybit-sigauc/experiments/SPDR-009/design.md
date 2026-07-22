# SPDR-009 — Design: signed absorption marginal value (S9), CF-SIGAUC-001 Phase 6′

**Item:** SPDR-009 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 015 §3 seq 1 + **§D6** · **Lane:** SPDR (TRAIN-only screen)
**Role:** the checkpoint's **master go/no-go** — framework-falsifier #3. Decides whether the signed thesis has soil (§7 of the ckpt-015 design).
**Revision:** D6 four-pair rewrite (operator **option A**, 2026-07-21) + QA-4 residual fix +
AMENDMENT-22 frozen INFR-020 handoff. Prior 1d/1m-only design was QA-APPROVED (runs 1–3);
D6 suspended that execution approval. **Pair-invariant:** §1 mechanism core, §3.3 arms, T1–T5
*structure*, §4.2 controls, §4.3 tripwire, §5 band *labels*, §8 D1 golden traces.
**Pair-dependent (rewritten):** §0, §1 DERIVED horizon, §2 entry/IB/refractory, §3.1–3.2,
§3.4, §4.1 strata, §4 T3 mid-range scale, §5 zone-sensitivity text, §6.1 floors, §6.3
power, §7 HARD IB/COMPLETE/1m fences, §9. **Prerequisite: INFR-020 COMPLETE** — QA Run 10
APPROVE; operator accepted pin manifest `5f170b71…` on 2026-07-22. Developer implementation,
post-implementation QA, and the operator execution gate still remain.
**Source (NORMATIVE):** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` — **S9** · **Addendum v1.1 GOVERNS** · ckpt-015 §D6.
**Predecessor pins:** INFR-018 registry `5c386984…` · INFR-017 baselines `1b7244c8…` ·
column_pins `e3b9fd9b…` · fence `35d3375e…` · **INFR-020 pin manifest
`5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5`** (all nine artifact
hashes; accepted by the operator 2026-07-22).
**Predecessor reads:** SPDR-007 / SPDR-008 both `NOT_WORTH` on daily-anchored objects only — D6.5 re-run trigger if a coarser pair carries signal where 1d/1m does not.
**Operator direction — holds:** primary = **5 and 10 LTF detection bars** per pair (wall-clock grows with LTF); session-remainder secondary (disclosure). Source S9 micro horizon scales with detection bar.
**Operator direction — universe (option A):** keep **all four pairs**; power and disposition on the **liquid-active core** per pair (INFR-020 0.50 retention floor ≈ 194 / 72 / 47 / 31), with **activity-conditioning** stated in every coarse-pair disposition.
**Operator direction — D7 (2026-07-22), post-census:** pair set **unchanged at four**. **D4 is pre-declared POWER-LIMITED** on the measured candidate census (162 candidates / 12 instruments on its core) — it runs for horizon coverage and an UNPOWERED/INCONCLUSIVE D4 is **not** a null; D3 is not pre-declared. **Closure rule restated:** a powered null on **every pair that reaches power at realised n, minimum D1 and D2** (supersedes "all four pairs", unattainable under the D4 pre-declaration). See §6.3 + AMENDMENT-23/24.
**Deliverable:** operator-signed disposition on *"does the measured Δ signature add reversal information over identical unsigned climax-hold events at the same levels"*, **per pair**, money floor first. **Never a tradability claim** (SPDR lane): 0 counted reads, no TEST, no holdout.

---

## §0 Scope fence

| | |
|---|---|
| **Produces** | per located climax-hold event **and per domain pair**: forward side-signed return in **bps** at holds H∈{5,10} **LTF bars** (primary; wall-clock = H × LTF minutes) and to HTF-session end (secondary), favourable/adverse excursion on the **1-minute path**, signed aggression score, arm {S9, MIRROR, BASE}, level kind — report layers vs same-pool unsigned, mirror, derangement, matched-random, bare-level-touch |
| **Must NOT produce** | a net tradable-edge claim, deployability claim, family status change, counted read, TEST/holdout contact, **per-level Δ** (card ban 2), local accounting, S1 acceptance gate as qualifier, any outcome built from LTF bars instead of 1-minute bars (D6.3) |
| **Primary read** | **T1 — marginal contrast** `S9 − BASE` forward bps on identical location-qualified events, **per pair**. Bare "signed absorption reverts" is not a result. |
| **Domain pairs (pre-registered, D6.2)** | **D1** 1d/1m · **D2** 1h/5m · **D3** 4h/15m · **D4** 1d/1h — all four in **one** screen under one frozen design |
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01Z)` fit/freeze. CONFIRM `[2023-03-01Z, 2023-12-18Z)` one verify, TRAIN-INTERNAL. TEST `≥ 2023-12-18` never. Holdout `≥ 2025-01-08` never. |
| **Counted reads / slots** | 0 / 0 |

### D6.3 invariant (binding — restated)

> **HTF and LTF govern session framing and event detection ONLY. Every price-path and volume-at-price measurement stays on 1-minute bars in all four pairs.**

Outcomes and volume profiles (POC/VA) use prior-HTF-session **1-minute** bars so K-UNIFORM stays inside its calibrated regime. Detection residuals and arm labels use the pair's LTF bar and that pair's INFR-020 baseline/threshold pins.

### Universe (operator option A)

```
PER-PAIR SIGNED-READ universe (INFR-020 COMPLETE-window retention, DESIGN band):
  D1 (1m):   the 194 A5-fitted instruments (INFR-017 pin remains the 1m baseline).
  D2 (5m):   instruments with LTF window retention ≥ 0.50  → measured ~72 of 194
  D3 (15m):  retention ≥ 0.50                               → measured ~47 of 194
  D4 (1h):   retention ≥ 0.50                               → measured ~31 of 194
  Source: frozen INFR-020 results/coverage_report.json (median retention
  0.38505 / 0.20110 / 0.08815 at 5m/15m/1h; floor counts 72 / 47 / 31 and re-emitted
  at run in power_census).
  Instruments below the floor are DISCLOSED as liquidity-limited for that pair, never as a
  signed negative. D1 is not liquidity-limited by retention; D2–D4 are.

THRESHOLDS: INFR-020 emits per-(symbol, timeframe) cuts by the frozen p90/p10 rule
  (classes.derive_thresholds unmodified). D1 consumes the frozen `class_thresholds_1m.json`
  for all 194 symbols; its 137 registry overlaps reproduce INFR-018 value-identically.
  D2–D4 consume `class_thresholds_mtf.json` for 194 × {5m,15m,1h}. Every read reports
  registry-overlap vs extended membership; a positive confined to extended-only names is flagged.

ACTIVITY CONDITIONING (D2–D4, binding on disposition wording — INFR-020 §5 / option A):
  A COMPLETE LTF window is one in which the instrument traded every source minute. Surviving
  windows carry 2.4×–27× the median volume of partials (universe median ~6.7× at 60m). Coarse-
  pair reads measure absorption during continuously-traded windows, unequally across the
  cross-section. Every pooled D2/D3/D4 disposition states this; stratified or disclosure-only
  pooled reads are permitted, never silent.

BREADTH denominator: 296 readable-TRAIN (ckpt-015 §6). Survivorship caveat (Addendum §2.9) on
  every breadth line. Point-in-time, delisted included.
```

### Applicability of standard design blocks

| Block | Status |
|---|---|
| Nautilus `BacktestNode`; `xen.adjudication`; estimand gate | **N/A — SPDR lane** (vectorised Python, no P&L booked, no estimand-gated verdict). Integrity substitute = code-asserted band fence + causal `t−1` self-check (§7). A `WORTH_EXPLORING` graduates into the Nautilus pipeline where these bind. |
| §10 SPREAD-SCALE-ROUTING | **APPLIES** — §6.2. Binding here: a 10-minute hold is the highest-turnover object this family has screened, so spread dominates. |
| §11 spread as a verdict leg | **APPLIES in substance, with the tradability clause N/A** (QA-1 I-11 — the earlier blanket N/A contradicted §5, which does define a SUPPORTED label). §5's SUPPORTED is a *label on an availability contrast*, not a tradability claim, and this item emits no tradable band; but 1× spread is a **binding leg** of the §6.1 floor and every arm's absolute return is read against it. 0.5×/2× spread stay disclosure-only sensitivities. |
| §12 amendment ledger | §10. |
| §13 battery/eligibility/null rules | **APPLIES** — F02 time-stability §5, F04 exit-matched in every control block, F06 derived tripwire threshold §4.3. **F07 (MDE-consistent TEST-read floors) is N/A with reason:** F07 governs counted TEST reads; this item spends 0 counted reads and never touches the TEST band, so it has no read floor to set (QA-1 I-13). |
| L-29/L-30/L-31 (Nautilus) | N/A — no engine run. |

### Frozen inputs — re-hashed at every entry point, `assert_frozen_inputs()` raises on mismatch

| Input | Pin | Consumed as |
|---|---|---|
| `INFR-018/…/instrument_registry.json` | `5c386984…` | D1 anchor **A-USOPEN**, IB L=15; **K-UNIFORM**, VA `share=0.685`; 1m class cuts for 137 symbols |
| `INFR-017/…/seasonal_baselines.parquet` | `1b7244c8…` | **sole** 1m A5 pin (D1 residuals). INFR-020 must not emit a competing 1m baseline |
| `INFR-017/…/column_pins.json` | `e3b9fd9b…` | `SpreadBps` = **UNUSABLE** |
| Catalog fence | `35d3375e…` | `train_end 2023-12-18`, `holdout_start 2025-01-08` |
| **INFR-020** `seasonal_baselines_mtf.parquet` | `86c81937cbee23f76a62bd4051394f59da3deb2230e7dd958fc573cee38a12c1` | A5 residuals for **5m / 15m / 1h** (D2–D4) |
| **INFR-020** `class_thresholds_1m.json` | `dee853ad96f11754f410aa8c0a7632b0a782029dee0b770b500a74a9f959e9fc` | D1 p90/p10 cuts for all 194; 137 registry overlaps asserted identical |
| **INFR-020** `class_thresholds_mtf.json` | `745fb435eeb9e70fec88d55a32e6dfce38b4c02619824f9cff4d51ca3dcb3ae7` | D2–D4 per-(symbol,timeframe) p90/p10 cuts |
| **INFR-020** `sessions_mtf.json` | `c55cd8806bba048f90e48795fdcab021738d9984a1602ca14f164a0f05b262df` | A-H1 / A-H4 operational anchors + generalised IB |
| **INFR-020** `zone_scale_census.json` | `f64e0d22355f8c5f3c5acafff598ae43fa0e84cfac9acc6f9e88fbd458487f1e` | prior-HTF-session-range scale census |
| **INFR-020** `zone_scale_census_d1_ibwidth.json` | `76c3d4b58c00361d081de9225e226db2fe2aa86a56f17c18ec23e0e046705f0c` | D1 ib_width sensitivity census |
| **INFR-020** `coverage_report.json` | `68dac757a4c96f0989da902805e11265e8108f7555f3d02df6a66f2dafc3a424` | per-pair usable universe + activity-conditioning ratios |

**May NOT rely on:** `SpreadBps`; §2.5 spread layer; per-level Δ; S1 as event qualifier; net breadth claim (INFR-019 absent); treating A-H1/A-H4 as edge-bearing (INFR-020 certifies OPERATIONAL; A-H4 inherits measured-negative A-FUND breakout contrast on half its instants — **anchor quality only**, not absorption at a level).

---

## §1 Mechanism statement

```
MECHANISM: At a level that is already structurally qualified — a balance edge (this session's IB
edge), a prior-session value edge (VAH/VAL), the prior session's completed-profile HVN (POC), or a
prior-session extreme — a bar prints HEAVY measured aggression and produces NO price result (top-
decile seasonal volume residual, bottom-decile seasonal range residual: the source's Absorption
signature). The exact taker split then names the LOSING side by measurement: if the |Δ| is large
and its sign points INTO the level, the aggressors pressing toward the level met a larger passive
counterparty and got nothing — they paid costs, hold inventory pressing the wrong way, and the
defender of the level is the other side. The level therefore holds and price resolves AWAY from
the absorbed side over the MICRO horizon (source S9: `rej(level)`, micro). This is definitionally
invisible to price alone: at a flat-price, high-volume bar every price-derived sign estimator goes
flat, so the direction is available only from the measured split. That is the distinction from the
DELETED S3 Δ+ arm, whose signed tag rode on a price-visible failed break. The P&L-bearing object is
a SINGLE-LEG micro reversal: one entry at the open of the bar after the absorption bar closes, one
exit H bars later. Cadence is sparse and event-driven (order 10^1–10^2 events per instrument per
DESIGN bank), so the read is cross-sectional.

DERIVED:
  estimand = per-event side-signed forward return in BPS OF ENTRY PRICE, open-to-open, at H ∈
             {5, 10} **LTF detection bars** (wall-clock = H × LTF minutes; path from 1-minute
             opens) and to HTF-session end (secondary) — EVENT-LEVEL; single leg ⇒ event ==
             episode (L-16). MFE/MAE on the 1-minute path; MEDIAN + TRIMMED (Addendum §2.6).
  null     = (primary) SAME pool's UNSIGNED arm — fail the two-leg Δ conjunction (GT-4 pattern).
             (mirror) anti-monotone arm. (attribution) ≥2000-seed score derangement.
             (availability) matched random-timing. (base) bare level touches.
  horizon  = H∈{5,10} LTF bars per pair — source S9 micro, scaled to detection bar:
               D1: 5 / 10 min · D2: 25 / 50 min · D3: 75 / 150 min · D4: 5 / 10 h.
             HTF-session remainder = secondary disclosure.
  test     = calendar-day-clustered block bootstrap on per-day arm contrast (5-day block ≥ every
             primary hold wall-clock, including D4's 10 h); derangement as effect + one-sided p +
             CI; mirror-tail + per-symbol census on every promote.
```

**Anti-L-13 check.** Nothing here transfers. The event is a tail region of *this* family's frozen A5 residual pair; the conditioning quantity is a *measured aggressor split* projected onto a *structural direction*, which is meaningless for any price-only mechanism; the primary null is the same-event unsigned arm, which exists only because the signal is a refinement of a class rather than a standalone trigger; the mirror arm is the mechanism's own antisymmetry. No prior Xen referee stack adjudicates; `xen.evaluation` supplies bootstrap/MDE primitives as tools.

---

## §2 Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES.
    Both are the single-leg micro reversal of §1. The forward bps return and the excursion are
    functions of exactly the path that leg would experience, from the same entry price. No
    multi-leg structure ⇒ no episode aggregation (L-16).
  measured conditioning event == traded entry event: YES.
    Conditioning = absorption **LTF** bar CLOSE (residuals + distance complete). Entry = OPEN of
    the **next LTF bar** (confirmed ≤ t−1). No resting limit ⇒ B-4 seam cannot arise. Levels fixed
    earlier: prior HTF session closed before this one; IB edges after IB wall-clock completes
    (D1: anchor+15m; D2: +15m; D3: +15m; D4: +60m — D4 DEVIATES, disclosed). IB-edge events
    before IB complete are REFUSED.
  effect-splitting windows non-overlapping: YES for primary holds, code-asserted —
    prior HTF session  ⟂  IB  ⟂  event LTF bar  ⟂  outcome window on 1m path (entry open →
    entry + H×LTF_minutes]. Event bar's own path excluded from excursion. Within (symbol, pair),
    REFRACTORY of max(H)=10 LTF bars — no two primary outcome windows overlap. Cross-symbol
    dependence by day clustering. SESSION-remainder secondary: may overlap within a session;
    DISCLOSURE only, day-clustered, no promote claim (QA-1 I-12, pair-generalised).
```

---

## §3 The event, the arms, the estimand

### 3.1 Level set (gate-free, location-only — Addendum §3.1) — per HTF session

Seven level kinds per **HTF session**, knowable at or before session open. Profiles and extremes
from the **prior HTF session's 1-minute bars** (D6.3 / INFR-020 `assert_levels_from_1m`):

| kind | definition | availability |
|---|---|---|
| `IB_HIGH` / `IB_LOW` | this HTF session's IB edges | after IB wall-clock completes |
| `PRIOR_VAH` / `PRIOR_VAL` | prior HTF session value-area edges | prior HTF session closed |
| `PRIOR_POC` | prior HTF session POC | prior HTF session closed |
| `PRIOR_SESSION_HIGH` / `PRIOR_SESSION_LOW` | prior HTF session true extremes | prior HTF session closed |

| pair | HTF session | anchor | IB (wall-clock → LTF bars) | IB share of session |
|---|---|---|---|---|
| **D1** | 1d | A-USOPEN (frozen) | 15 min = 15×1m | 1.0% |
| **D2** | 1h | A-H1 clock UTC (operational) | 15 min = 3×5m | **25.0%** |
| **D3** | 4h | A-H4 00/04/08/12/16/20 UTC (operational) | 15 min = 1×15m | 6.3% |
| **D4** | 1d | A-USOPEN (frozen) | **60 min = 1×1h** — **DEVIATES** | 4.2% |

IB edges are **location only** — S1 acceptance gate never consulted (Addendum §2.7). A-H1/A-H4 are
operational; no edge-bearing read. A-H4's funding-subset instants inherit INFR-018 A-FUND's
measured-negative **breakout** contrast (anchor quality, not S9). S13 defended bands **not built**
(declared). IB-share varies 1%→25% across pairs — IB-derived objects are **not cross-pair
comparable** without saying so (INFR-020 W4).

**Level-set provenance.** All four pairs consume
`xen.sigbar.ltf.structural_levels_1m` — the exact level-set constructor used by INFR-020's census —
with 1-minute source bars. SPDR-009 must import it rather than lift or recreate the INFR-018 D1
helper. Candidate session assignment and per-bar level availability likewise import
`xen.sigbar.ltf.assign_candidate_sessions` and `available_levels_for_candidates`; these enforce
the close-time, not-yet-formed, and self-made exclusions without a second implementation. Every
level kind must carry non-null `formed_ts`: edge-setting time for extrema and last contributing
1m source time for profile levels. Missing provenance raises; prior-session levels are not assumed
past-formed when a D4 bar straddles A-USOPEN.

### 3.2 The event pool P — "heavy effort, no result, at a level" (per pair)

Per (symbol, **pair**, LTF bar `b`, level `L`), all four legs — residuals and cuts from that pair's
timeframe (INFR-020 for D2–D4; frozen 1m for D1). Candidate bars come from the **shared**
`absorb_candidate_predicate()` on the **COMPLETE-window** LTF series (INFR-020 §1.1 — zero-fill
withdrawn):

| leg | rule | source |
|---|---|---|
| **effort** | `volume_resid(b) ≥ volume.high` | per-(symbol, tf) p90 |
| **no result** | `range_resid(b) ≤ range.low` | per-(symbol, tf) p10 |
| **at the level** | `|Close(b) − L| ≤ τ_pair · zone_scale` | see below |
| **direction defined** | `into_side = sign(L − Close(b))`; tie → prior LTF bar close; still 0 ⇒ drop | S9 into-level |

**Zone scale (D6.4.5).** Primary scale = **prior HTF session range** (price units of that session).
IB-width collapses at coarse pairs (D3/D4 IB = one bar). **τ_pair is re-picked per pair on EVENT
COUNTS ONLY** (no outcome), frozen to `results/pool_cuts.json` before any read. **D1 sensitivity:**
retain `0.25 × ib_width` (original QA-approved zone) as a pre-registered sensitivity census from
INFR-020 `zone_scale_census_d1_ibwidth.json` — not a second promote cell.

**D1 τ on prior-session-range scale** is chosen from the same count-only discipline as the original
τ = 0.25 on ib_width (`diag_pool` / `diag_grid` for the ib_width sensitivity; new count-only
census on prior-session-range scale at run-prep, frozen before outcomes). Zone-dilution asymmetry
from the original registration still binds: a wide zone dilutes precise-contact effects; a null
under a wide zone does **not** refute a precise-contact variant; the narrower sensitivity is emitted
alongside.

**Secondary pool `P_WIDE` (per pair, pre-registered):** no-result leg at per-(symbol,tf) **p25**
range residual + tighter τ (count-frozen). Separate stratum; never pooled with P. Multiplicity:
**4 pairs × 2 pools × 2 holds = 16 primary cells**, mirror-tail rule on each.

**Event granularity.** One event per (pair, LTF bar, level kind); nearest-level once for pooled
read; consecutive qualifiers at same level → first bar; multi-bar aggregate = disclosure.

### 3.3 The three arms (the marginal framing, and its mirror)

Within pool P, using the frozen per-symbol cuts `delta_abs.high` (`d_hi`) and
`delta_ratio.abs_high` (`dr_hi`), and `signed_score = into_side × delta_ratio_resid(b)`:

| arm | rule | meaning |
|---|---|---|
| **S9** | `delta_abs_resid ≥ d_hi` **and** `signed_score ≥ dr_hi` | large measured aggression pointing INTO the level — absorbed. The signal. |
| **MIRROR** | `delta_abs_resid ≥ d_hi` **and** `signed_score ≤ −dr_hi` | equally large aggression pointing AWAY from the level — the anti-monotone twin. |
| **BASE** | everything else in P | the unsigned climax-hold class at the same levels — the marginal baseline. |

`signed_score` is the **continuous** form of the same quantity and carries the dose-response read
(T2). A raw Δ number is never used (A5 / card ban 5); `delta_ratio_resid` is the seasonally
normalised Δ/V **direction** column and `delta_abs_resid` the magnitude column, exactly as
INFR-018's frozen classifier consumes them.

### 3.4 Entry, exit, estimand (per pair)

| quantity | definition (L-21 unit pin with every number) |
|---|---|
| `entry_ts` | OpenTime of the **next LTF bar** after the detection LTF bar closes |
| `entry` | that bar's **Open** (≤ t−1 confirmed) |
| `side` | `−into_side` — resolve AWAY from absorbed side |
| holds (primary) | H ∈ {5, 10} **LTF bars** → wall-clock minutes = H × {1, 5, 15, 60} for D1–D4 |
| holds (secondary) | remainder of the **HTF session** containing the event — DISCLOSURE |
| **`ret_bps`** | `side × 1e4 × (Open_1m[t_exit] − Open_1m[entry]) / Open_1m[entry]` — money units of entry price; **path from 1-minute opens** (D6.3), not LTF closes |
| `mfe_bps` / `mae_bps` | max fav/adv excursion of **1-minute real prices** over `(entry, t_exit]`; median + 10% trimmed (Addendum §2.6) |
| `ret_norm` | `ret_bps / prior_htf_session_range_bps` — **disclosure only** (divisor = prior HTF session range in bps of entry; pair-native; **not** IB width — §6.1 pin matches this) |
| contiguity | unbroken 1-minute bars over the whole outcome span; else drop and COUNT |

| pair | H=5 wall-clock | H=10 wall-clock |
|---|---|---|
| D1 | 5 min | 10 min |
| D2 | 25 min | 50 min |
| D3 | 75 min | 150 min |
| D4 | 5 h | 10 h |

---

## §4 The reads (report layers — the operator judges; L-32 / INFR-016)

**T0 — money floor** (Addendum §2.1 leg iii, binding first act): per-symbol **and per-pair** cost
floors published **before any estimation** (§6.1). The **~11.0 bps fee leg is hold-invariant**
(~85% of the floor at short holds). Funding grows with wall-clock (material at D4 H=10 ≈ 10 h).
Spread is hold-invariant at the one-round-trip charge. **Central D6 economic claim:** coarser pairs
get more wall-clock to clear the **same fee-dominated floor** (D3 H=10 = 2.5 h vs D1 H=10 = 10 min).

| id | Question | Statistic | Class | Band |
|---|---|---|---|---|
| **T1** *(PRIMARY — the marginal value)* | Does the Δ signature add forward information over the identical unsigned events at the same levels? | `mean/median ret_bps(S9) − ret_bps(BASE)`, per stratum, day-clustered block-bootstrap CI; **and** the mirror-tail companion `ret_bps(S9) − ret_bps(MIRROR)` | report | §5 |
| **T2** *(dose-response)* | Is forward return monotone in the measured aggression-into-level score? | Spearman `ρ(signed_score, ret_bps)` within pool P, read against a **≥2000-seed derangement of `signed_score`** (effect + one-sided p + CI); un-normalised and finite-guarded | report | §5 |
| **T3** *(location necessity — the source's own prediction)* | Is the same signed effect present with **no** qualified level nearby? Source S9: *"Unqualified mid-range absorption = =="* — predicted ≈ 0. | identical `S9 − BASE` on MID-RANGE climax-hold bars: no level within **`1.0 × prior_htf_session_range`** (same scale family as the contact zone, not ib_width). Per-pair stratum; **not cross-pair comparable** when session ranges differ in role. | report | §5 |
| **T4** *(availability)* | Does the S9 arm beat a matched random-timing entry at all — i.e. is the absolute arm above zero and above the floor? | `ret_bps(S9) − ret_bps(matched_random)`, ≥30-donor battery, day-clustered CI | report | §5 |
| **T5** *(base disclosure)* | How much does the LOCATION alone give, with no climax-hold signature? | `ret_bps(BASE) − ret_bps(bare_level_touch)` | disclosure | §5 |

**What counts as soil (declared before the read, judged by the operator).** Addendum §2.1 rewrote
the master gate as a **conjunction of three co-equal legs**, and all three bind here — the earlier
draft omitted two of them (QA-1 I-1):

| leg | Addendum §2.1 | this design |
|---|---|---|
| (i) the signal's own claim reproduces | calibration | **T1** marginal contrast positive, **and** materially exceeding its MIRROR companion, **and** **T2** surviving the score derangement, **and** **T3 ≈ 0** (the effect is located, not generic aggression) |
| (ii) beats a matched unconditional control | conditioning skill | **T4** positive — the S9 arm must beat matched random-timing entries, not merely beat the BASE arm |
| (iii) clears the measured cost floor | economics | the S9 arm's median `ret_bps` compared against its per-symbol floor (§6.1); `AT_OR_BELOW_FLOOR` ⇒ market science, not strategy |

**Reproduction alone never passes** — a gate that can pass on leg (i) alone is defective by
construction (Addendum §2.1). T1 ≈ 0 with adequate power on both pools is the **third independent
powered null** of ckpt-015 §7. **T1 UNPOWERED is INCONCLUSIVE, never a null** (B-5) — the single
most important reading rule in this design, given §6.3.

### 4.1 Strata (per-stratum binding; pooled disclosure-only — L-03)

**Leading dimension: domain pair** `{D1, D2, D3, D4}` — pairs are never pooled into one headline
contrast. Within each pair:

`level_kind × symbol × hold {5, 10, session} × pool {P, P_WIDE} × chronological third`, plus margins.

**UNPOWERED first** (§5). Given §6.3, the **primary read per pair is the POOLED cross-section over
that pair's usable universe** (option A floor), co-reporting the per-symbol census (Addendum §2.3).
Per-symbol binds only where its own MDE clears. Multiplicity: **4 pairs × 2 pools × 2 primary
holds = 16 primary cells** (plus session disclosure and level-kind margins). Mirror-tail rule
governs every cluster claim **within a pair** — not across pairs.

**Cross-pair comparison (D6 purpose):** pairs compared **internally under one frozen design** —
same arms, controls, tripwire, bands. Differences are **not** automatically mechanism differences:
usable-universe size, IB share-of-session, activity conditioning, and hold wall-clock all change.
Any "pair X beats pair Y" line must state those confounds.

**Mirror-tail promote rule (Addendum §2.2, mandatory).** Both tails counted in every cell grid. A
cluster claim requires the positive-tail count to **materially exceed** its anti-monotone mirror
count, not merely null expectation. Positive ≈ mirror ⇒ **dispositive multiplicity noise**
(SPDR-008 7-vs-6 failure mode).

### 4.2 Controls

```
CONTROL unsigned_same_pool  (PRIMARY marginal baseline; class: within_sample_attribution → REPORT)
  question answered: is the forward return attributable to the MEASURED Δ signature, or to the
    unsigned climax-hold-at-a-level geometry that the signed events also possess?
  population: the BASE arm — pool-P events failing the Δ legs. DISJOINT from the S9 arm by
    construction (a bar is in exactly one arm), same levels, same session phases, same effort/
    no-result legs, same entry and exit rules. NON-DEGENERATE: the signal does NOT fire on every
    member of the conditioning set — the measured S9 share of pool P is ~6% (19 of 313 events over
    ten instruments; SOL 5 of 87 — deduplicated event counts, §6.3, not the withdrawn pair counts),
    so the
    baseline is a large, genuinely different population that can and does produce a different mean.
  bite/MDE: additive plant on the S9 arm's ret_bps, swept over a grid, MDE read off the curve at
    the realised n per stratum and PUBLISHED BEFORE the real read (never asserted from memory).
  non-vacuity: different bars ⇒ different entry prices and different forward paths — it moves the
    contrast's entire sufficient statistic, not a label.
  exit-matched (L-24 F04): both arms resolved at the same H, same open-to-open convention.
  expected if H true: contrast > 0 and stable across thirds. If false: ≈ 0.
  disclosure: collapse fraction and per-symbol census per stratum.

CONTROL mirror_arm  (the anti-monotone twin; class: within_sample_attribution → REPORT)
  question answered: is any S9 effect specific to aggression pointing INTO the level, or does
    equally large aggression pointing AWAY produce the same forward return — i.e. is the effect
    about DIRECTION at all, or just about a big |Δ| at a level?
  population: the MIRROR arm. DISJOINT from S9 (opposite sign of the same score), matched on
    |Δ| magnitude by construction (both clear d_hi).
  non-vacuity: reverses the sign that the mechanism's whole claim rests on.
  bite/MDE: the same additive-plant sweep as unsigned_same_pool, run on the S9 − MIRROR contrast;
    MDE at the realised n published before the read. The MIRROR arm is the SMALLER of the two on
    the measured census (§6.3), so this contrast's MDE, not T1's, is the binding power constraint.
  exit-matched (L-24 F04): identical H and open-to-open convention on both arms.
  disclosure: collapse fraction (mirror contrast / raw S9−BASE contrast) and per-symbol census.
  expected if H true: S9 − MIRROR > 0 materially. If false: ≈ 0.
  This control IS the §2.2 mirror tail at the event level, not only at the cell-grid level.

CONTROL signed_score_derangement  (attribution null; class: within_sample_attribution → REPORT)
  question answered: does the CONTINUOUS measured score carry forward information, or would a
    random score value predict the same return?
  population: the same pool-P events; `signed_score` DERANGED across events (zero fixed points,
    L-28, regenerated until the fixed-point count is EXACTLY 0 and asserted); ρ recomputed per
    seed; ≥2000 seeds; reported as observed minus the deranged distribution — effect + one-sided
    p + CI (never `at_or_above_pXX`, never a collapse auto-kill).
  DERANGEMENT SCOPE — GLOBAL across the pooled event set, NOT day-blocked (QA-1 I-2; the draft was
    self-contradictory on this). Reason, stated with its cost: the measured cadence is ~1 event per
    symbol-day (§6.3), so a within-day-block derangement has almost no permutable mass and would
    reproduce SPDR-007's failure mode (60 of 7,070 events derangeable) — a null with no teeth,
    which Addendum §2.4 explicitly warns about for sparse-session events. A global derangement has
    teeth but a known limitation: it does NOT hold the market regime fixed, so it tests "the score
    is uninformative" against a marginal, not a same-day-conditional, alternative. Two mitigations,
    both reported, neither a gate: (a) the same ρ is re-read within each chronological third, so a
    regime-driven ρ shows up as third-instability; (b) a WITHIN-SYMBOL derangement (each symbol's
    scores permuted among that symbol's own events) is emitted as a second null, removing any
    cross-sectional composition effect. The deranged fraction is reported beside every effect.
  bite/MDE: on the real arm, standardise `signed_score`, remove the observed monotone component
    by deterministic Spearman centring, then plant `u × score_z` bps over `u = 0, 0.5, …, 30`.
    At every point, 200 seeded GLOBAL zero-fixed-point score derangements publish their mean,
    95% interval and one-sided p. The first positive plant whose rho exceeds the deranged p95
    with p ≤ 0.05 is the MDE, published both as bps per score-SD and as rho before the read. The
    full real T2 read still uses ≥2000 derangements; the 200-seed plant sweep is its separate
    pre-read resolution instrument. If no grid point resolves, T2 is explicitly UNPOWERED.
  non-vacuity: re-pairs score with return ⇒ moves ρ's sufficient statistic.
  disclosure: collapse fraction (deranged ρ / observed ρ) per stratum, with the deranged fraction.
  destroy form: DERANGEMENT (zero fixed points, asserted).

CONTROL matched_random_timing  (availability baseline; class: within_sample_attribution → REPORT)
  question answered: does entering the same side at the same symbol and session phase on an
    UNCONDITIONAL day produce the same forward return — i.e. does the number belong to the EVENT
    or to that instrument's generic behaviour at that minute-of-session?
  population: cross-session donors (SPDR-007 D-1 pattern, operator-ratified): for each event
    (side d, phase φ = mins_since_anchor), draw 30 donor sessions (≥ the L-19 floor of 25, seeded)
    from the SYMBOL's own pool, excluding the event's own session; enter at anchor(donor)+φ on
    side d, exit after the same H. Horizon-matched by construction.
  DISJOINT: donor session ≠ event session ⇒ different bar, price, and forward path.
  bite/MDE: co-designed additive plant on the event arm, MDE in CONTRAST UNITS (bps), published
    before the real read.
  non-vacuity: moves the entry price and the entire forward path — the metric's whole support.
  exit-matched (L-24 F04): every donor entry resolved at the same H, same convention.
  disclosure: collapse fraction and per-symbol census per stratum.
  expected if H true: contrast > 0. If false: ≈ 0.
  destroy form: independent re-drawing of the instant (not a permutation).

CONTROL bare_level_touch  (location-only base; class: within_sample_attribution → DISCLOSURE)
  question answered: how much of any effect is the LEVEL rather than the absorption signature?
  population: bars entering the same level's zone with NO climax-hold signature, same symbol,
    same level kind, same phase band, same side; DISJOINT from pool P (a bar is in one or the
    other by the effort/no-result legs). NON-DEGENERATE: this population is orders of magnitude
    larger than pool P, so it is subsampled to 30 matched draws per event, seeded.
  bite/MDE: same additive-plant sweep, MDE at realised n published before the read.
  non-vacuity: different bars ⇒ different entry prices and forward paths.
  exit-matched (L-24 F04): same H, same convention.
  disclosure: collapse fraction and per-symbol census per stratum.
  expected: may be > 0 (location) or ≈ 0; never promotable — the signed warrant is T1/T2.
```

### 4.3 Leak tripwire (HARD — validity)

```
TRIPWIRE outcome_path_swap  (class: future_destroy — HARD)
  Replace each event's forward price path with a DERANGED donor event's forward path (matched on
  hold length; zero fixed points, asserted; re-based to the target's entry price). Everything at or
  before entry — the residual legs, the level, into_side, the arm label, the score — is IDENTICAL;
  the outcome is unrelated to it. Implemented as the FIXED-H analogue in `xen.sigbar.absorb`
  (§9) — `spine.outcome_path_swap` / `path_swap_bite` are NOT reused as-is (QA-2 R-4); donors are
  bucketed by hold length rather than remaining-session length.
  ADJUDICATES: T1 (the S9 − BASE contrast) and T2 (ρ). Both are SUBGROUP/PAIRING statistics inside
    one pool, so a within-pool outcome derangement legitimately destroys them.
  DOES NOT ADJUDICATE: T4 — but for a DIFFERENT reason than the draft claimed (QA-1 I-5). The
    draft asserted mean-vacuity by analogy with SPDR-008's AMENDMENT-8; that analogy is wrong.
    SPDR-008 deranged WITHIN the treatment population, so the treatment mean was literally
    preserved and the destroy was vacuous by symmetry. Here the derangement runs across pool P, a
    strict SUPERSET of the S9 arm, so the S9 arm's mean is NOT preserved and the destroy is not
    vacuous. The actual reason T4 is out of scope is that the swap has NO DEFINED REFERENCE for it:
    T4 compares the S9 arm against an EXTERNAL, cross-session control population that the swap does
    not touch, so a "swapped T4" contrast has no null value to collapse toward — it measures
    pool-P-mean minus control-mean, a quantity with no interpretation under the destroy. T4's
    causality therefore rests on the ≤ t−1 construction plus the matched-unconditional control
    itself, which is the comparison it already is.
  vacuity check: T1 and T2 are functions of the (arm/score ↔ outcome) pairing; the swap destroys
    exactly that pairing while preserving both marginals.
  STATISTIC: collapse_fraction = destroyed_contrast / raw_contrast, per adjudicated read.
  MATERIAL-EDGE PRECONDITION (inherited SPDR-007 AMENDMENT-11 / SPDR-008): the HARD survival rule
    fires ONLY where the RAW contrast is a material edge (day-clustered CI excludes zero). Where no
    material raw edge exists the tripwire is UNPOWERED (`NO_MATERIAL_EDGE`) — NOT a leak, and per
    Addendum §2.8 it is ALSO NOT evidence that anything is leak-free; it means the gate had teeth
    and nothing to bite, and may not be cited as a clean bill of health.
  SURVIVAL := (raw CI excludes zero) AND (|collapse_fraction| > CF*, same sign as raw) AND
    (swapped CI excludes zero).
  CF* IS DERIVED, NOT INHERITED (QA-1 I-4; L-24 F06 requires derivation on the stream under test).
    INFR-018's 0.25 was derived on a SESSION-scale object; this design's stream is a 5/10-minute
    open-to-open return, whose autocorrelation and donor-similarity structure are different, so
    importing the number would be exactly the asserted-threshold defect F06 exists to stop.
  CALIBRATION REGIME — ON A PLANTED CAUSAL EDGE, NOT ON A NULL ARM (QA-2 R-2 corrected a defect
    this design introduced). Calibrating on a known-null arm is invalid: there the raw contrast is
    ≈0, so `collapse_fraction = destroyed/raw` has a vanishing denominator and is undefined-to-
    explosive — and it would calibrate the threshold in precisely the regime where the
    material-edge precondition forbids the threshold from ever being used. CF* is instead
    calibrated with the design's OWN additive-plant instrument (§4.2), in the regime where it is
    applied: plant a known CAUSAL effect of ~1× the published MDE on the S9 arm so the raw
    contrast is material by construction, run the path swap over ≥200 seeds, and take the upper
    95th percentile of |collapse_fraction|. That is "how much of a genuinely causal, non-leaking
    edge survives this destroy by chance", which is the quantity the survival rule needs.
    STABILITY (QA-3 R20): a plant at 1× MDE is the noisiest point and therefore yields the HIGHEST
    CF*, i.e. the most PERMISSIVE leak gate. CF* is therefore emitted at THREE plant sizes
    (1×, 2×, 3× MDE) so its stability is visible; the 1× value is the one applied, and a CF* that
    moves materially across plant sizes is reported as a caveat on the tripwire's resolution.
    Published to results/tripwire.json with its seed set and all three plant sizes BEFORE any
    real read. 0.25 is recorded
    as the PRIOR; if the derived CF* lands far from it, that is reported, not smoothed.
  IF A MATERIAL ADJUDICATED READ SURVIVES: the construction is reading the outcome ⇒ EMISSION
    INVALID ⇒ fix and re-run. NEVER read as "no effect".
  coverage: events with no usable donor dropped and COUNTED; spliced fraction reported.
  permutation-based: YES → DERANGEMENT, zero fixed points, asserted.

POSITIVE CONTROL bite (REQUIRED — no disposition emits without it): pooled,
  `corr(swapped_mfe_bps, donor_real_mfe_bps) > 0.5` — computed in **bps of the target's entry
  price**, this design's own excursion unit, NOT spine's IB-normalised excursion (QA-2 R-4: donor
  and target divisors differ and would attenuate the correlation). SPDR-007 measured 0.77 and
  SPDR-008 0.64 on the session-scale version of this swap; those are PRIORS on a different object,
  not thresholds transplanted here — the 0.5 floor is the inherited rule, the comparison numbers
  are context. If the bite fails, the swap reached nothing the reads consume and the tripwire has
  no teeth (INFR-018 A-6 defect).
```

---

## §5 Interpretation bands — labels, never gates (CI validity evaluated first — L-32 / B-5)

```
T1 / T2 / T3 / T4 contrasts (per stratum) — EXHAUSTIVE decision table, no undefined cell:
  UNPOWERED:    no valid CI (tested FIRST); or, after the interval-sign checks below, MDE
                unavailable at the realised n for a branch that needs it (never a negative)
  CONTRADICTED: ci_high < 0  (for T2: return ANTI-monotone in aggression-into-level — genuine
                evidence against the mechanism, and a result in its own right). Tested BEFORE
                MDE availability because this band has no MDE term.
  SUPPORTED:    ci_low > 0 and effect ≥ its own MDE  (T2 also: derangement one-sided p ≤ 0.05)
  SUGGESTIVE:   ci_low > 0 but effect < its own MDE, OR ci_low > 0 with MDE unavailable
  WASH:         CI spans zero AND |effect| < MDE → "cannot distinguish", never a refutation
                (L-11). This is the design's POWERED NULL cell.
  IMPRECISE:    CI spans zero AND |effect| ≥ MDE → the point estimate exceeds what this arm can
                resolve, yet the interval still spans zero. Added at QA run 13 (AMENDMENT-30):
                the MDE is defined by planting a CONSTANT shift on every treated event, so it
                carries no dispersion, while a real effect does — an estimate can therefore beat
                the MDE and remain indistinguishable from zero when the effect is concentrated
                in few days rather than uniform. READING: INCONCLUSIVE — the effect is not
                stable enough to resolve. It is NEVER a powered null (a large point estimate
                cannot support "nothing is there", B-5) and NEVER a positive. For the
                AMENDMENT-24 closure rule it behaves exactly like UNPOWERED: horizon-covered
                but inconclusive, neither blocking nor contributing to a family close. Reported
                with effect, CI, MDE and per-day n so the analyst can see the dispersion.
  CI spans zero with MDE unavailable: UNPOWERED — MDE is required to separate WASH from
                IMPRECISE honestly.
  POOLED:       declared PRIMARY here (§4.1) with the per-symbol census attached, not hidden
SIGNED-VALUE reading (the screen's point): soil requires ALL THREE §4 legs, not leg (i) alone —
  (i) T1 SUPPORTED **and** S9 − MIRROR materially positive **and** T2 surviving derangement **and**
      T3 ≈ 0;
  (ii) T4 positive — the S9 arm beats matched random-timing entries, not merely the BASE arm;
  (iii) the S9 arm's median ret_bps clears its per-symbol cost floor (§6.1).
  Reproduction alone never passes (Addendum §2.1). The §4 conjunction table is authoritative; this
  clause restates it so a reader of §5 alone cannot disposition on leg (i) (QA-2 R-1).
  T4 SUPPORTED with T1 WASH ⇒
  "absorption events go somewhere, but the SIGN adds nothing" — recorded, NOT the signed warrant.
  T5 SUPPORTED with T1 WASH ⇒ a LOCATION effect (P-01-adjacent geometry), recorded, not promoted.
FLOOR framing (Addendum §2.1 leg iii): every arm's absolute ret_bps is reported against its
  per-symbol floor. AT_OR_BELOW_FLOOR ⇒ MARKET SCIENCE, NOT STRATEGY.
```

**Zone-dilution asymmetry (binding on disposition wording, §3.2 / D6).** Primary contact zone =
`τ_pair × prior_htf_session_range` (τ count-frozen per pair). A POSITIVE under a wide τ is
conservative; a NULL is a null for absorption in that neighbourhood and does **not** refute a
tighter-contact variant. Sensitivities reported beside every null (not promote cells):
(1) **P_WIDE** — p25 range residual + tighter τ_pair (count-frozen on the same prior-session-range
scale); (2) **D1 only:** retained `0.25 × ib_width` census (former primary zone, INFR-020
`zone_scale_census_d1_ibwidth`). Pre-D6 `τ = 0.10 × ib_width` is **withdrawn as a named
sensitivity** — replaced by the two above.

**Finite-value guard (Addendum §2.5, binding).** Every correlation/regression path guards
`is_finite` explicitly on both operands before the statistic is computed, and reports the count
dropped. Null-dropping that passes float NaN silently flipped a Spearman from +0.130 to −0.040 in
SPDR-007; the guard is asserted, not assumed.

**Time stability (L-24 F02), reported not gated:** every read repeated on the three DESIGN thirds
and once on CONFIRM; sign consistency and per-third n published.

---

## §6 Money floor, conversion pin, power, uncertainty

### 6.1 Money floor + CONVERSION-PIN

```
CONVERSION-PIN:
  divisor object: NONE — the estimand is already in bps of the entry price
    (`side × 1e4 × (Open_1m[t_exit] − Open_1m[entry]) / Open_1m[entry]`). No ATR/IB between the
    screen number and the money claim (L-21 closed by construction).
  disclosure normaliser `ret_norm` (NOT a money pin): divisor =
    **prior HTF session range in bps of entry** (same object as the contact-zone scale family).
    IB-width normalisation is **not** used for `ret_norm` under D6 (IB share varies 1%→25% and
    collapses to one bar at D3/D4). D1 may still *emit* an IB-relative column as a continuity
    diagnostic labelled `ret_norm_ib_d1_only`, never mixed with `ret_norm`.
  normaliser object (conditioning): A5 seasonal residuals of volume, range, |Δ| and Δ/V —
    1m pin `1b7244c8…` on D1; INFR-020 MTF baselines on D2–D4. Residuals, never raw numbers.
  cost floor — every input DERIVED FROM A PINNED ARTIFACT, none recalled (QA-1 I-3 rewrote this
    block; the previous spread figures had no derivation and are withdrawn):
      spread input = max(one_tick_bps, candidate_C_flip_pair.median), both read per symbol from
        INFR-017 `column_pins.json` (`e3b9fd9b…`, per_symbol.<SYM>). `SpreadBps` itself is pinned
        UNUSABLE (INFR-017 W2), so the flip-pair estimator — the only non-negative candidate in
        that pin, 0.0% negative on the sample days — carries the spread leg, floored at one tick.
        **LABELLED AS THE PIN LABELS IT (QA-2 R-3): a CONSERVATIVE UPPER BOUND on the spread, NOT
        the quoted spread.** Consequence, stated in the direction it cuts: the floor is an UPPER
        bound on cost for the five audited symbols, so a "clears the floor" reading on them is
        conservative, while a "below the floor" reading on them is NOT conclusive. For every other
        instrument the tick floor makes it a LOWER bound on cost, i.e. the opposite direction —
        the two classes are never mixed in one statement.
        **VALIDATED_ON_SAMPLE_ONLY:** the flip-pair medians come from the pin's four pre-declared
        sample days (2022-09-14, 2023-01-11, 2023-06-07, 2023-11-01), not the TRAIN band. A
        4-day spread median is a point estimate of a time-varying quantity; the floor inherits
        that uncertainty and no floor comparison is presented as exact.
        Convention check: `t1_round_trip_spread_bps` charges ONE full spread per round trip, so
        the input is a full spread, not a half-spread.
      floor = xen.evaluation.bybit_round_trip_cost_bps(taker, spread_bps=<above>,
        hold_hours = wall_clock_hours of the pair's H), computed at freeze time.
        D1 H=10 (hold_hours=10/60) — audited symbols, 2026-07-21:
        | symbol | one_tick_bps | flip_pair_bps | spread used | floor @10min |
        | BTCUSDT  | 0.04289 | 0.24421 | 0.24421 | **11.265** |
        | ETHUSDT  | 0.05836 | 0.30495 | 0.30495 | **11.326** |
        | SOLUSDT  | 0.37564 | 0.72678 | 0.72678 | **11.748** |
        | DOGEUSDT | 1.47732 | 1.47037 | 1.47732 | **12.498** |
        | XRPUSDT  | 1.96541 | 1.92901 | 1.96541 | **12.986** |
        components @10min: fee RT 11.0 + spread + funding ≈ 0.021 bps.
      PER-PAIR HOLD (primary H=10 wall-clock → hold_hours):
        D1: 10/60 · D2: 50/60 · D3: 150/60=2.5 · D4: 10.0
        Fee stays 11.0; funding scales with hold_hours (D4 H=10 ≈ +1.25 bps funding vs D1's
        ~0.02 — order-of-magnitude; exact table emitted to results/floor_table.json per pair).
        **~85% of the short-hold floor is hold-invariant fee** — coarser pairs do not buy a lower
        fee; they buy more time for the same fee to be earned back.
      COVERAGE CAVEAT: flip-pair only on 5 audited symbols; others TICK FLOOR ONLY
        (`SPREAD_TICK_FLOOR_ONLY`). No net breadth claim (INFR-019 absent — Addendum §2.9).
FLOOR BAND (framing, not a gate):
  ABOVE_FLOOR / AT_OR_BELOW_FLOOR as before — MARKET SCIENCE, NOT STRATEGY when at/below.
```

### 6.2 SPREAD-SCALE-ROUTING (mandatory, T1 lane)

```
SPREAD-SCALE-ROUTING (per symbol at screen time):
  estimated_rt_spread_bps: max(tick_bps, flip-pair) on audited symbols; tick floor elsewhere
  gross_edge_bps: the stratum's T1 marginal contrast in bps (already money units — no conversion)
  t1_undecidable: xen.evaluation.spread_scale_route(gross, rt_spread) — the 3× threshold is USED,
    never re-derived
  if YES: stratum reported AWAITING_MBP; pooled T1 reads stay disclosure-only on that symbol
```

### 6.3 Power — measured (D1) and projected (D2–D4 under option A)

#### D1 (1d/1m) — measured census (stands)

DESIGN bank, ten deep instruments, deduplicated events + 10-bar refractory —
`design_derivations/diag_census.json`, count-only:

| symbol | effort∧no-result | **pool P** | S9 | MIRROR | BASE | **P_WIDE** | S9 | MIRROR |
|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 20 | 3 | 0 | 1 | 2 | 5 | 1 | 0 |
| ETHUSDT | 27 | 10 | 0 | 0 | 10 | 21 | 3 | 3 |
| SOLUSDT | 231 | 87 | 5 | 5 | 77 | 176 | 6 | 3 |
| XRPUSDT | 36 | 10 | 1 | 0 | 9 | 29 | 5 | 1 |
| DOGEUSDT | 65 | 22 | 0 | 3 | 19 | 38 | 3 | 1 |
| ADAUSDT | 192 | 57 | 5 | 5 | 47 | 111 | 7 | 7 |
| AVAXUSDT | 46 | 8 | 1 | 1 | 6 | 24 | 4 | 1 |
| LINKUSDT | 67 | 25 | 2 | 6 | 17 | 41 | 1 | 3 |
| MATICUSDT | 271 | 81 | 4 | 10 | 67 | 255 | 16 | 15 |
| LTCUSDT | 31 | 10 | 1 | 0 | 9 | 27 | 4 | 2 |
| **total** | 986 | **313** | **19** | **31** | **263** | **727** | **50** | **36** |

Binding facts from D1:
- **S9 ≈ 6% of P; MIRROR is larger (31 vs 19)** — S9−MIRROR carries the binding MDE, not T1.
- **Per-symbol reads dead on arrival** (max 5 S9/symbol) — pooled per pair is PRIMARY.
- **BTCUSDT and ETHUSDT contribute 0 S9 events on pool P** (SOL/ADA/MATIC/LINK do contribute) —
  disposition states this; not "the majors contributed zero."

#### Withdrawn projection (QA-era defect under D6)

The prior draft projected "pooled pool-P of order 10³–10⁴ with S9 arm 10²–10³" from **~194
instruments at every scale**. That is **invalid under D6 + INFR-020 measurement**:

| pair | LTF | median COMPLETE retention | usable @ 0.50 floor |
|---|---|---|---|
| D1 | 1m | (full 1m path) | **194** |
| D2 | 5m | **0.387** | **~72** |
| D3 | 15m | **0.202** | **~47** |
| D4 | 1h | **0.089** | **~31** |

Source: INFR-020 `diag_universe_coverage.json` (all 194). Surviving COMPLETE windows are also
**activity-conditioned** (median COMPLETE/partial volume ratio ~6.7× at 60m; 2.4×–27× on named
names). Operator **option A**: keep all four pairs; read the liquid-active core; state conditioning.

#### D2–D4 — what is and is not projected

Event rates at coarser LTF bars are **not known at design time** (INFR-020 emits apparatus only;
no absorption outcome). Coarsening changes the event object (one 1h bar ≠ sixty 1m bars of residual
class). Therefore:

- **No invented event counts** for D2–D4. No "10³–10⁴ from 194" line.
- **Usable-universe floors** above are measured and predeclared.
- **At run**, before any contrast: `results/power_census.json` emits per-pair actual pool-P / S9 /
  MIRROR / BASE counts on the usable universe, plus per-symbol census. MDE curves from plants at
  **realised** n. Nothing above is a result.

#### Measured CANDIDATE census — the upper bound on every pair (INFR-020 pin `5f170b71…`)

The one count-only quantity INFR-020 **does** emit is the shared absorption-candidate population
(`zone_scale_census.json`, DESIGN band, `absorb_candidate_predicate` on COMPLETE windows). It is
**not pool P** — it precedes τ contact, refractory de-duplication and the S9/MIRROR/BASE split,
each of which only reduces it — so it is an **upper bound**, cited as such and never as an event
projection:

| pair | candidates (194) | candidates on the 0.50 core | core symbols | carrying ≥1 | median / max per carrying symbol |
|---|---|---|---|---|---|
| **D1** | **95,836** | 95,836 | 194 | **189** | 194 / 7,469 |
| **D2** | 9,497 | **5,226** | 72 | **60** | 14 / 746 |
| **D3** | 2,974 | **933** | 47 | **28** | 8 / 293 |
| **D4** | **640** | **162** | 31 | **12** | 5 / 98 |

Two facts follow, both binding on the disposition:

1. **The ten-instrument D1 census above is a sample, not a scale property.** Its 986 effort∧no-result
   events sit inside a 194-instrument candidate population of 95,836. D1's power under option A is
   therefore far better than the ten-name table suggests — but **the arm ratios (S9 ≈ 6% of P;
   MIRROR > S9) are what carry the MDE**, and they are measured only on the ten names until
   `power_census.json` lands. No universe-scaled S9 count is asserted here.
2. **D4 is pre-declared power-limited** (operator decision **D7**, 2026-07-22): 162 candidates on
   12 instruments before every reducing cut, one symbol holding 98 of them. D4 runs for horizon
   coverage; an INCONCLUSIVE/UNPOWERED D4 is the expected outcome and is **not** a null. **D3 is
   not pre-declared either way** — thin on the same measure, but resolved at run from realised n.

```
POWER:
  MDE: plant curves (§4.2) at REALISED n per (pair, stratum), published BEFORE the real read.
    D1 order-of-magnitude (ten deep instruments only): S9 n=19 vs BASE n=263 is scarce; contrast
    MDE is coarse relative to the ~11–13 bps floor — INCONCLUSIVE is the most likely D1 outcome
    and is predeclared as such, not a family-closing null.
  D2–D4: MDE unknown until power_census; may be better or worse than D1 depending on whether
    coarser bars concentrate or dilute the absorption signature.
STRATA PREDECLARED UNPOWERED (never negatives — B-5):
  - every per-symbol and per-symbol×level-kind cell on pool P (**any** of the four pairs)
  - D1: BTCUSDT and ETHUSDT on pool P at any hold (0 S9 measured)
  - D2–D4: every instrument below the 0.50 retention floor for that pair → liquidity-limited,
    disclosed, never a signed negative
  - **D4 POOLED (operator decision D7, 2026-07-22): pre-declared POWER-LIMITED on the measured
    candidate census — 162 candidates / 12 instruments on its core, before τ, refractory and the
    arm split. D4 runs for HORIZON COVERAGE. An UNPOWERED or INCONCLUSIVE D4 is the expected
    outcome and is NOT a null; a POWERED D4 result, if realised n contradicts the pre-declaration,
    reads normally. D3 is NOT pre-declared — its power is read from realised n.**
  - any chronological third of any per-symbol read
  - instruments without the pair's baseline/threshold pin → uncovered
  - every UNPOWERED cell reported WITH n and MDE
DISPOSITION CONSEQUENCE (binding on ckpt-015 §7 under D6, as restated by D7):
  - A family-closing "third powered null" requires T1 UNPOWERED-or-null **with adequate power**
    on the relevant pool(s) — and under D6, a null **at D1 alone no longer closes the family**
    (D6.5 / §7 amended).
  - **D7 restatement (supersedes "powered null across all four pairs"):** close requires a powered
    null on **every pair that reaches power at its realised n**, and **at minimum on D1 and D2**.
    A pair that lands UNPOWERED is recorded as **horizon-covered but inconclusive** — it neither
    blocks the close nor contributes to it. Rationale: with D4 pre-declared power-limited, the
    all-four-pairs form was unattainable by construction and would have made the family
    unclosable. The closure statement NAMES every pair's power state, so "closed" is never read
    as "tested everywhere".
  - If POOLED T1 is UNPOWERED on BOTH P and P_WIDE **for a pair**, that pair is INCONCLUSIVE,
    not a powered null (Addendum §2.4).
  - Every D2/D3/D4 disposition states activity conditioning (option A).
```

### 6.4 Uncertainty

**Calendar-day-clustered circular block bootstrap** on the per-day arm contrast, via
`xen.evaluation.block_bootstrap_ci` (INFR-004 / L-20). Resampling unit = calendar day (all symbols'
events that UTC day, **within pair**). **Block ≥ H wall-clock:** 5-day blocks cover D1–D3 primary
holds with margin; D4 H=10 = 10 h still ≪ 5 days. Within-(symbol, pair) refractory (§2) keeps
primary windows non-overlapping. SESSION-remainder secondary may overlap — DISCLOSURE only,
day-clustered, no promote (QA-2 R-5). Report **"95% interval excludes zero"**, never a p-value
(L-20). T2 derangement ≥2000 seeds: effect + one-sided p + CI.

---

## §7 Integrity vs informative split

```
HARD (block — failure means the EMISSION IS INVALID; fix and re-run; NEVER read as "no edge"):
  - future-destroy tripwire: outcome_path_swap must collapse T1 and T2 wherever they are material,
    AND its positive control (bite corr > 0.5) must survive
  - band fences: DESIGN/CONFIRM asserted on EVERY read path (`fences.assert_band`, raise not warn);
    TEST and holdout unreachable by construction
  - CONFIRM-before-freeze refusal: no CONFIRM path executes before results/pool_cuts.json and
    INFR-020 pins (baselines_mtf, thresholds_mtf, sessions_mtf, coverage_report) exist with hashes
  - causal ≤ t−1: every conditioning input complete at the event LTF bar's close; entry at the NEXT
    LTF bar's open; **IB-edge events before IB wall-clock completes for that pair REFUSED**
    (D1–D3: anchor+15 min; **D4: anchor+60 min** — not a universal +15); prior-HTF-session levels
    from the PRIOR closed HTF session only
  - D6.3: any outcome path (ret / MFE / MAE) or level/profile construction that consumes LTF bars
    instead of 1-minute bars raises
  - COMPLETE-window only: candidate / event with `window_class ≠ COMPLETE` raises (INFR-020
    zero-fill withdrawal; shared predicate)
  - window disjointness (§2), incl. entry-bar exclusion from the excursion and the within-
    (symbol, pair) refractory
  - frozen-input hash re-verification at every entry point (INFR-017/018 + INFR-020)
  - `fences.assert_no_per_level_delta` — per-level signed attribution raises (card ban 2)
  - `check_no_local_accounting` — no accounting primitive in this experiment dir
  - S1-gate refusal: any code path consulting `acceptance.evaluate_discriminator` as an event
    qualifier raises (Addendum §2.7 — S1 is an operational anchor only)
  - A-H1/A-H4 consumed as edge-bearing raises

INFORMATIVE (report layers; the OPERATOR judges — L-32 / INFR-016):
  every contrast, Spearman, collapse fraction, derangement p/CI, census, stability read, floor
  comparison, band label, and mirror-tail count. No `pass` field anywhere; nothing machine-dropped
  between layers. The disposition is an OPERATOR ACT.
```

---

## §8 Golden trace — designer-derived, for QA to diff before execution

Derived from real DESIGN-band bars under this design's frozen rules by
`design_derivations/gt_derive.py` (full output `design_derivations/gt_output.json`), designer-side
and INDEPENDENT of the future `xen.sigbar.absorb` (it recomputes the residuals via
`baselines.residualise` and rebuilds the level set itself). **The developer must NOT regenerate
these.** All events are DESIGN band. Entry = OPEN of the bar at `event_ts + 1min`.

```
GT-1  S9 arm, DOWN-into-level (aggression into an IB_LOW below) — SOLUSDT.
      event_ts 2022-12-28 03:27Z  anchor 2022-12-27 14:30Z  level IB_LOW 10.700  ib_width 0.380
      bar OHLC 10.770 / 10.775 / 10.765 / 10.765   |Close − L| = 0.065 = 0.171·ib_width (≤ 0.25 ✓)
      volume_resid +5.6998 (≥ p90) · range_resid −1.0117 (≤ p10) · delta_abs_resid +9.8776 (≥ d_hi)
      into_side −1 (level below Close) · delta_ratio_resid −1.5016 ⇒ signed_score +1.5016 (≥ dr_hi)
      ⇒ arm S9 · entry_ts 03:28Z · entry Open 10.770 · side LONG (= −into_side)
      ret_bps_H5 −4.6425 · ret_bps_H10 −9.2851

GT-2  S9 arm, at a PRIOR_SESSION_LOW (prior-session level, causality-critical) — SOLUSDT.
      event_ts 2022-12-29 01:24Z  anchor 2022-12-28 14:30Z  level PRIOR_SESSION_LOW 9.590
      ib_width 0.555 · bar OHLC 9.740 / 9.740 / 9.725 / 9.725 · |Close − L| = 0.135 = 0.243·ib_width
      volume_resid +9.4710 · range_resid −0.8993 · delta_abs_resid +23.9289
      into_side −1 · delta_ratio_resid −1.5397 ⇒ signed_score +1.5397 ⇒ arm S9
      entry_ts 01:25Z · entry Open 9.725 · side LONG · ret_bps_H5 +15.4242 · ret_bps_H10 −5.1414
      Proves the level came from the PRIOR closed session (anchor 12-28, level from 12-27's session).

GT-3  MIRROR arm — the SIGN GUARD, identical geometry, opposite Δ direction — SOLUSDT.
      event_ts 2022-12-26 23:34Z  anchor 2022-12-26 14:30Z  level PRIOR_VAL 11.265225
      bar OHLC 11.250 / 11.265 / 11.250 / 11.260 · ib_width 0.030
      volume_resid +6.8339 · range_resid −0.8993 · delta_abs_resid +25.5469 (≥ d_hi — large |Δ|)
      into_side +1 (level ABOVE Close) · delta_ratio_resid −1.3820 ⇒ signed_score −1.3820 (≤ −dr_hi)
      ⇒ arm MIRROR, NOT S9: the aggression was heavy but pointed AWAY from the level.
      entry_ts 23:35Z · entry Open 11.260 · side SHORT · ret_bps_H5 −35.5240 · ret_bps_H10 −26.6430
      QA diffs the ARM LABEL here: a magnitude-only rule (|Δ| ≥ d_hi alone) would call this S9.

GT-4  BASE arm — the THRESHOLD boundary case — SOLUSDT (pinned cuts: volume.high +5.3440,
      range.low −0.8993, delta_abs.high +4.8546, delta_ratio.abs_high +1.3778).
      event_ts 2022-11-12 22:08Z  level IB_LOW 14.945 · bar OHLC 14.955/14.955/14.950/14.950
      volume_resid +14.1027 (≥ 5.3440 ✓) · range_resid −1.6862 (≤ −0.8993 ✓) ·
      delta_abs_resid +26.0113 (≥ 4.8546 ✓ — huge measured aggression)
      into_side −1 · delta_ratio_resid +1.2096 ⇒ signed_score −1.2096.
      |signed_score| = 1.2096 < dr_hi 1.3778 ⇒ it clears NEITHER the S9 leg (+1.3778) NOR the
      MIRROR leg (−1.3778) ⇒ arm BASE. A bar with enormous |Δ| is still unsigned-class because the
      Δ/V DIRECTION residual is not extreme enough. QA diffs the three-way assignment against the
      per-symbol cut values, not against a pooled cut.

GT-5  Fence + hash + order behaviour (must RAISE, not warn):
      (a) any read path with OpenTime ≥ 2023-12-18 → raises;
      (b) a CONFIRM path before results/pool_cuts.json (+ INFR-020 pins) exist with hashes → raises;
      (c) registry ≠ 5c386984… or 1m baselines ≠ 1b7244c8… or kernel ≠ K-UNIFORM or INFR-020
          pin mismatch → raises;
      (d) a per-level Δ access → raises (card ban 2);
      (e) an IB-edge event before IB wall-clock completes for that pair → raises;
      (f) a PRIOR_* level from the CURRENT (not prior) HTF session → raises;
      (g) a derangement seed with any fixed point → raises (L-28);
      (h) `acceptance.evaluate_discriminator` as event qualifier → raises;
      (i) matched_random donor inside the event's own HTF session → raises;
      (j) outcome or level path consuming LTF bars instead of 1-minute bars → raises (D6.3);
      (k) A-H1/A-H4 consumed as edge-bearing → raises;
      (l) candidate bar with window_class ≠ COMPLETE → raises (INFR-020 withdrawal).

GT-1…GT-4 remain **D1-only** golden traces (valid under A-USOPEN / 1m). D2–D4 golden traces are
emitted at implementation against INFR-020 fixtures (count-only expected values for one named
session per pair) — not designer-pinned here because MTF baselines do not exist until INFR-020 runs.
```

---

## §9 Artifacts, complexity budget, execution order

| | |
|---|---|
| Statistical reads | 5 (T1 + mirror, T2, T3, T4, T5) × **4 pairs** — T1 per pair is the master |
| Controls | same five attribution controls + HARD path-swap + bite — applied **per pair** |
| Code modules | `xen.sigbar.absorb` (pool/arms, zone, refractory, 1m-path estimands, derangement, matched-random, fixed-H path-swap). Imports **INFR-020** `xen.sigbar.ltf.{absorb_candidate_predicate,structural_levels_1m,assign_candidate_sessions,available_levels_for_candidates}` + MTF baselines/thresholds/sessions; no level, candidate, session, or availability rule is reimplemented. Inherited: `sessions, profile, baselines, classes, fences`, `xen.evaluation`. Not modified: `acceptance.py`, `profile.py`, `classes.py`, `hyp_i4_validation.py`. Fixed-H path-swap (not raw `spine.outcome_path_swap` — QA-1 I-6). Runner `SPDR-009/screen_code/absorb_screen.py`. |
| Plots | ≤5 types × pair facet or small-multiples: census · arm ret_bps · dose-response · T1 by level kind + mirror tails · arm median vs floor |
| Artifacts | `results/{universe_membership,pool_cuts,power_census,mde_curves,floor_table,events_DESIGN,events_CONFIRM,derangement,tripwire,layers,census}.{json,parquet}` · `screen.md` · `analysis.md` (fresh-context analyst mandatory) |

**Execution order is strict.**
1. **INFR-020 frozen** — Run 10 APPROVE; full battery green; pin manifest `5f170b71…`
   operator-accepted; coverage report + both census artifacts present.
2. SPDR frozen-input hash verify (INFR-017/018 + INFR-020 pins).
3. Per-pair usable universe from coverage_report (option A 0.50 floor) → `universe_membership`.
4. Per-pair τ / P_WIDE cuts frozen on **counts only** → `pool_cuts.json` (+ D1 ib_width sensitivity).
5. Cost floors + `power_census`; then, **for each pair**, all of that pair's MDE curves before
   that pair's first contrast. Pairs are disjoint estimands and the curves are deterministic, so
   a completed earlier pair cannot enter or adapt a later pair's population, cuts, plants or MDE.
6. DESIGN reads T1–T5 + controls **per pair** → tripwire → CONFIRM once → layers + census.
7. `screen.md` → fresh-context analyst → operator disposition (per pair + overall under D6.5/§7).

CONFIRM before freeze is unattributable and re-runs.
## §10 Amendment ledger (opens empty — pre-measurement amendments append at QA; L-23)

All amendments below are **pre-measurement** (QA run 1, 2026-07-21) — logged before any read on
real DESIGN/CONFIRM outcome data. Issue numbers refer to `qa-review.md` run 1.

```
AMENDMENT-1 (I-1): the "soil" reading restored to Addendum §2.1's FULL three-leg conjunction —
  T4 (beats matched unconditional) and the cost-floor leg were missing, leaving a gate that could
  pass on reproduction alone. §4 rewritten with the three-leg table. DIRECTION: TIGHTER. 0L/1T/0N.
AMENDMENT-2 (I-2): derangement scope pinned GLOBAL (not day-blocked), with its cost stated and two
  reported mitigations (chronological-thirds re-read; a within-symbol second derangement). The
  draft was self-contradictory; a day-blocked null would have been near-vacuous at the measured
  cadence, reproducing SPDR-007's 60/7,070 failure. §4.2. DIRECTION: NEUTRAL (a vacuous null
  replaced by a teeth-bearing one with a declared limitation). 0L/1T/1N.
AMENDMENT-3 (I-3): cost-floor spread inputs replaced with values DERIVED from the INFR-017
  column pin (one_tick_bps and the flip-pair estimator, per symbol); the previous figures had no
  derivation and are withdrawn. Coverage caveat added for the 189 non-audited instruments
  (tick floor only ⇒ lower bound on cost). §4 T0, §6.1. DIRECTION: TIGHTER. 0L/2T/1N.
AMENDMENT-4 (I-4): tripwire survival threshold CF* is now DERIVED on this design's own 5/10-minute
  stream before use (L-24 F06), not inherited from INFR-018's session-scale 0.25; 0.25 is recorded
  as a prior only. §4.3. DIRECTION: TIGHTER. 0L/3T/1N.
AMENDMENT-5 (I-5): the tripwire's T4 exclusion re-argued correctly — the draft's mean-vacuity
  analogy to SPDR-008 AMENDMENT-8 was wrong (that derangement was within-treatment; this one is
  across a superset). The exclusion stands on the absence of a defined reference for a swapped T4.
  §4.3. DIRECTION: NEUTRAL (same scope, correct reason). 0L/3T/2N.
AMENDMENT-6 (I-6): `spine.outcome_path_swap`/`path_swap_bite` no longer claimed as inherited
  unmodified; `absorb.py` implements a fixed-H analogue with a regression test against the
  session-scale original. §9. DIRECTION: TIGHTER (removes a false reuse claim). 0L/4T/2N.
AMENDMENT-7 (I-7, I-8, I-9): §6.3 power table replaced with the DEDUPLICATED, post-refractory
  event census over ten instruments (`diag_census.py`, count-only); pair counts withdrawn; the
  P_WIDE multiplier corrected from "3–5×" to the measured ~2.3×; the BTC row corrected; the
  extrapolation explicitly caveated against source A4. All per-symbol cells declared UNPOWERED.
  DIRECTION: TIGHTER (the honest numbers are worse than the ones they replace). 0L/5T/2N.
AMENDMENT-8 (I-10): the mandatory `disclosure`, `bite/MDE`, `non-vacuity` and `exit-matched` lines
  added to mirror_arm, signed_score_derangement, matched_random_timing and bare_level_touch.
  §4.2. DIRECTION: NEUTRAL (completeness). 0L/5T/3N.
AMENDMENT-9 (I-11, I-12, I-13, I-14): §11 re-scoped from a blanket N/A to "applies in substance,
  tradability clause N/A"; §13 F07 marked N/A with reason; the non-overlapping-windows claim
  narrowed to the MICRO holds with the session secondary declared dependence-limited; §1's
  "without the Δ signature" corrected to the two-leg conjunction (GT-4 is a large-|Δ| BASE event);
  the GT-4g citation corrected to GT-5(e). DIRECTION: NEUTRAL (accuracy). 0L/5T/4N.
AMENDMENT-10 (I-15): `gt_output.json` trimmed to the PINNED golden traces only. Dumping all 157
  pool events' forward returns would have made any later change to τ, the pool legs, the arm cuts
  or the holds outcome-informed by construction. The event-definition justification now rests
  solely on `diag_census.py`, which computes no outcome. `gt_derive.py` additionally now defines
  entry by the CLOCK (event_ts + 1min) rather than by row position, which differed across a data
  gap (QA-1 R13). DIRECTION: TIGHTER. 0L/6T/4N.
AMENDMENT-11 (I-16): the τ = 0.25-over-0.10 rationale put on the record, WITH its cost — the zone
  is ~9× the event bar's range at GT-1, so the design dilutes a precise-contact effect toward
  zero; a null under this τ does not refute a precise-contact variant, and τ = 0.10 is emitted as
  a pre-registered sensitivity. §3.2. DIRECTION: NEUTRAL (disclosure of a known limitation).
  0L/6T/5N.
```

Second QA pass (run 2, 2026-07-21), still pre-measurement:

```
AMENDMENT-12 (R-1): §5's soil clause restated with all three §2.1 legs. The three-leg table had
  landed in §4 only, and §5 is what the analyst reads — the item could still have been
  dispositioned on reproduction alone, the exact defect AMENDMENT-1 was meant to close.
  DIRECTION: TIGHTER. 0L/7T/5N.
AMENDMENT-13 (R-2, a defect introduced by AMENDMENT-4): CF* calibration moved OFF the known-null
  arm and onto a PLANTED CAUSAL edge at ~1× MDE, using the design's own additive-plant instrument.
  On a null arm the raw contrast is ≈0, so collapse_fraction has a vanishing denominator, and the
  threshold would have been calibrated in the one regime the material-edge precondition forbids it
  from being used in. §4.3. DIRECTION: TIGHTER (a valid calibration replaces an invalid one).
  0L/8T/5N.
AMENDMENT-14 (R-3): the flip-pair spread is now labelled as the INFR-017 pin labels it — a
  CONSERVATIVE UPPER BOUND, not the quoted spread — with VALIDATED_ON_SAMPLE_ONLY (4 sample days,
  not TRAIN band) disclosed and the direction of error stated for BOTH symbol classes, which cut
  OPPOSITE ways (upper bound on cost for the 5 audited, lower bound elsewhere). §6.1.
  DIRECTION: NEUTRAL (accuracy of a cost claim's direction). 0L/8T/6N.
AMENDMENT-15 (R-4): §4.3's residual "reuses spine.outcome_path_swap" removed to match §9, and the
  bite statistic restated in bps of entry price rather than spine's IB-relative excursion units
  (donor and target divisors differ and would attenuate the correlation). DIRECTION: TIGHTER.
  0L/9T/6N.
AMENDMENT-16 (R-5, R-6, R-7, R-8): §6.4's un-narrowed non-overlap claim aligned with §2; §6.3
  totals corrected to their own column sums; §4.2's non-degeneracy argument re-based on
  deduplicated events (19/313, ~6%) instead of withdrawn pair counts; and the `Close == level`
  tie-break UNIFIED across `gt_derive.py` and `diag_census.py` (previous BAR, not previous
  QUALIFYING bar), which moved census cells by ≤3 and left all golden traces byte-unchanged.
  DIRECTION: NEUTRAL (consistency; no rule loosened). 0L/9T/7N.
AMENDMENT-17 (R-9, R-10): duplicate row removed from the pinned golden-trace emission; L-23's
  final-gate false-qualifier re-derivation recorded as N/A WITH ITS REASON — this item has no
  qualifier gate set, spends no counted read, and emits no admission decision, so there is no
  false-qualifier count to re-derive. DIRECTION: NEUTRAL (completeness). 0L/9T/8N.
```

Operator-directed scope amendment (post-QA-run-3 APPROVE, still pre-measurement — nothing has been
run and no outcome exists):

```
AMENDMENT-18 (operator decision D6, 2026-07-21): the item is widened from ONE domain pair (1d/1m)
  to FOUR pre-registered HTF/LTF pairs — 1d/1m, 1h/5m, 4h/15m, 1d/1h — run together under one
  frozen design, with the pairs compared internally. The 1d/1m execution approval is SUSPENDED
  until INFR-020 supplies per-timeframe seasonal baselines, per-(symbol,timeframe) class
  thresholds, and 1h/4h session construction. Binding sub-decisions, all from D6:
    (a) HTF/LTF govern SESSION FRAMING AND EVENT DETECTION ONLY. Every price-path and
        volume-at-price measurement stays on 1-MINUTE bars in all four pairs — outcomes measured
        minute-by-minute, and volume profiles (POC/VA) built from the prior HTF session's 1-minute
        bars so the frozen K-UNIFORM kernel stays inside its trade-truth-calibrated regime and the
        full seven-kind level set survives at every pair.
    (b) IB = 15 minutes of wall-clock in every pair, expressed as the LTF bars covering it,
        minimum one bar (D1 15x1m — reproducing the frozen IB exactly; D2 3x5m; D3 1x15m;
        D4 1x1h, which DEVIATES at 60 minutes and is disclosed as such).
    (c) 1h/4h anchors are clock-aligned UTC and asserted as OPERATIONAL anchors with NO anchor
        race; their selection contrast is unmeasured and no read may treat them as edge-bearing.
    (d) the contact-zone scale moves from IB width to the PRIOR HTF SESSION RANGE (the IB collapses
        to one bar at coarse pairs), with tau re-picked per pair on EVENT COUNTS ONLY and frozen
        before any read; D1's 0.25 x ib_width is retained as a pre-registered sensitivity so the
        QA-approved 1d/1m read is not lost.
    (e) multiplicity becomes 4 pairs x 2 pools x 2 holds = 16 primary cells, pre-registered, under
        the Addendum §2.2 mirror-tail rule.
    (f) the cost floor is recomputed per pair — funding is negligible at D1-D3 but material at D4
        (a 10-hour hold accrues ~1.3 bps), while the hold-invariant 11.0 bps fee leg dominates
        everywhere. This is the widening's central economic argument: the same floor gets 2.5
        hours to be cleared at D3 instead of 10 minutes at D1.
  DIRECTION: **LOOSER** — it enlarges the grid fourfold and adds three unraced anchors. Recorded as
  LOOSER without hedging, even though the motivation is power and mechanism fidelity rather than
  result-chasing: the direction label describes what the change does to the search space, not what
  motivated it. Count: 1L/9T/8N.
```

Operator option A + pair-dependent rewrite (still pre-measurement — no outcome exists):

```
AMENDMENT-19 (operator option A + D6 pair-dependent rewrite, 2026-07-21): pair-dependent sections
  rewritten: §0 (four pairs, option-A universe floors, activity conditioning, INFR-020 pins),
  §1 DERIVED horizon, §2 entry/IB/refractory generalisation, §3.1–3.2 (HTF sessions, prior-session-
  range zone scale, COMPLETE-window shared predicate, per-pair τ count-only freeze), §3.4 (holds
  as LTF bars; 1m path outcomes), §4.1 (pair as leading stratum; 16 primary cells), §6.1 (per-pair
  floors; fee hold-invariant), §6.3 (D1 census stands; ~194-instrument projection WITHDRAWN;
  usable ~194/72/47/31; D2–D4 event counts not invented; family close requires all four pairs
  under D6), §9 (INFR-020 prerequisite + execution order). D1 golden traces (§8) unchanged and
  remain D1-only. DIRECTION: NEUTRAL on validity (implements signed D6 + option A without
  loosening integrity); the search-space LOOSER was already booked as AMENDMENT-18. Count stays
  1L/9T/9N after this NEUTRAL.
AMENDMENT-20 (D6.5 / §7 interaction, recorded with AMENDMENT-19): disposition consequence updated
  so a powered null at D1 alone cannot close CF-SIGAUC-001; close needs powered null across all
  four pairs (or explicit operator session-horizon scoping). DIRECTION: TIGHTER (harder to close
  the family). 1L/10T/9N.
AMENDMENT-21 (QA-4 I-1…I-7): §7 HARD IB fence generalises to per-pair wall-clock (D4=anchor+60,
  not universal +15) — MAJOR causality defect if coded from old HARD text; COMPLETE-window + D6.3
  1m-path + A-H non-edge added to HARD; `ret_norm` pin unified to prior HTF session range (§3.4 =
  §6.1); T3 mid-range uses `1.0 × prior_htf_session_range` (pair-stratum); §5 sensitivities =
  P_WIDE + D1 ib_width census (pre-D6 τ=0.10×ib withdrawn as named sensitivity); header
  pair-invariant list corrected; "either pair" → "any of the four pairs". DIRECTION: TIGHTER
  (I-1 causality). 1L/11T/9N.
AMENDMENT-22 (INFR-020 operator freeze, 2026-07-22): the accepted Run-10 pin manifest and exact
  consumer hashes replace every placeholder. D1 now explicitly consumes the pinned 194-symbol
  `class_thresholds_1m.json`; the 137 registry overlaps remain value-identical. This closes the
  otherwise ambiguous 57-symbol D1 consumer path before implementation. Final measured coverage
  replaces design-time approximations. DIRECTION: TIGHTER (frozen-input enforcement).
  1L/12T/9N.
AMENDMENT-23 (operator decision D7, 2026-07-22 — census disclosure + D4 pre-declaration): the
  measured candidate census from INFR-020's W5 is recorded in §6.3 as an explicit UPPER BOUND on
  each pair's event supply (194-universe / 0.50-core: D1 95,836 / 95,836 on 189 carrying symbols;
  D2 9,497 / 5,226 on 60; D3 2,974 / 933 on 28; D4 640 / 162 on 12, one symbol holding 98). It is
  NOT pool P and is never cited as an event projection — every reducing cut (τ contact, refractory
  dedup, arm split) still applies. Two consequences booked: (a) the ten-instrument D1 table is
  labelled a SAMPLE, not a property of 1d/1m — D6's motivating "19 events" figure was a
  ten-name artifact, and the widening now rests on its economic argument (hold-invariant fee, more
  time to clear it) rather than on event supply; (b) **D4 POOLED is pre-declared POWER-LIMITED**,
  so an UNPOWERED/INCONCLUSIVE D4 cannot later be presented as a null, and D3 is explicitly NOT
  pre-declared. DIRECTION: TIGHTER (a pre-registered UNPOWERED cell removes the post-hoc option of
  reading D4's silence as evidence). 1L/13T/9N.
AMENDMENT-24 (operator decision D7, 2026-07-22 — closure rule; partially reverses AMENDMENT-20):
  AMENDMENT-20 required a powered null ACROSS ALL FOUR PAIRS to close CF-SIGAUC-001. With D4
  pre-declared power-limited (A-23), that condition is unattainable BY CONSTRUCTION and would make
  the family unclosable regardless of evidence. Restated: close requires a powered null on EVERY
  PAIR THAT REACHES POWER at its realised n, and AT MINIMUM on D1 and D2; a pair landing UNPOWERED
  is recorded as HORIZON-COVERED BUT INCONCLUSIVE, neither blocking nor contributing to the close;
  the closure statement names every pair's power state so "closed" is never read as "tested
  everywhere". DIRECTION: **LOOSER** — it lowers the bar for closing the family, and is booked
  LOOSER without hedging even though the removed condition was impossible to satisfy. The
  horizon-menu clause (Addendum §2.10) is still met: every pair is screened and reported.
  2L/13T/9N.
```

**POST-MEASUREMENT amendments (run 1 of 2026-07-22 executed and DISCARDED).** Everything below
this line was written **after** a full DESIGN+CONFIRM execution whose outputs were inspected.
That run is **hard-deleted, not carried forward**: its `results/` tree was removed and the screen
re-run from the frozen inputs, per the programme's amend-in-place rule (a frozen-design confound
is closed by a dated amendment + hard delete + full rerun, never by a follow-up read). What was
seen before these amendments were written is recorded here so the operator can weigh it:
**D1 T1 WASH at both holds (+1.8 / −3.2 bps, CI spanning zero, S9 n=310, 168 days); D2/D3/D4
UNPOWERED; D4 zero signed events; D1 S9 median −0.0 bps against an ~11.3–13 bps floor.**

```
AMENDMENT-25 (run-1 precondition failure — MDE arm + CF* arm, 2026-07-22): §4.2's MDE was
  computed on a 30-symbol subsample while the contrast used the full usable universe, so the
  published MDE (9.5 bps at D1) did not correspond to the realised n of the read (true value
  13.0 bps). §4.3's CF* was then calibrated by planting 1× that wrong MDE on a SINGLE sample
  symbol, whose day-clustered CI can never exclude zero — every seed was discarded (0 of 200 at
  all three plant sizes, all four pairs) and the code silently substituted the inherited
  INFR-018 prior 0.25, which is exactly what AMENDMENT-4 forbids. Fixed: each pair's arm is
  built ONCE; the MDE is computed on that arm PER POOL (P and P_WIDE label against their own
  MDE, §5); CF* plants 1× that MDE on the POOLED arm across symbols; and CF* is NEVER defaulted
  to the prior — an arm that cannot support a material plant reports `UNDERIVABLE`, the survival
  rule is marked inapplicable, and the tripwire status says so rather than implying adjudication.
  Measured after the fix: D1 CF* DERIVED = 3.36 (10/10 seeds usable), and it falls to 1.44 / 0.92
  at 2× / 3× plants — the §4.3 R20 caveat is now visible and is emitted as
  `cf_star_spread_across_plants`. The derived value is ~13× the 0.25 prior; reported, not smoothed.
  DIRECTION: TIGHTER (a derived threshold replaces an inherited one; an inapplicable gate is
  labelled instead of passing silently). 2L/14T/9N.
AMENDMENT-26 (run-1 precondition failure — P_WIDE contact zone, 2026-07-22): §3.2 defines P_WIDE
  as the p25 no-result leg **plus a tighter τ**. Run 1 froze P at the τ-grid floor (0.05) on every
  pair, and the P_WIDE grid started at the same 0.05, so P_WIDE could only equal P's zone: the
  "tighter τ" leg went unmet and the §5 zone-dilution sensitivity was half-delivered. Fixed: the
  P_WIDE grid extends below the P floor (0.005–0.20) and selection is restricted to τ strictly
  less than the P value, raising if no such value exists. **Outcome-informed risk, stated:** this
  was written after run-1 outcomes were seen. Mitigations — the selection remains COUNT-ONLY, the
  new grid values were added below the existing floor rather than chosen against any result, and
  **P's own τ is unchanged at 0.05**, so the PRIMARY read is not re-picked; only the secondary
  stratum moves. DIRECTION: TIGHTER (a strictly tighter zone; removes a case where the two pools
  silently coincided). 2L/15T/9N.
AMENDMENT-27 (run-1 precondition failure — tripwire positive control, 2026-07-22): the §4.3 bite
  `corr(swapped_mfe_bps, donor_real_mfe_bps) > 0.5` was computed as ONE pooled correlation. The
  two quantities divide the same donor excursion by different entry prices (target's vs donor's),
  and the D1 cross-section spans seven orders of magnitude in price (0.00067 → 20551), so the
  pooled figure measured divisor dispersion, not whether the swap reached the reads — the exact
  mismatch AMENDMENT-15 / QA-2 R-4 introduced the bps unit to avoid. It read 0.33 at D1 and
  FAILED the floor, which under §4.3 blocks a disposition outright. Fixed: the correlation is
  computed PER SYMBOL, where the divisors are comparable, and the 0.5 floor is applied to the
  per-symbol median; the pooled figure is still emitted, labelled as an artifact, alongside the
  per-symbol minimum and the fraction of symbols clearing the floor. Measured after the fix:
  D1 per-symbol median 0.963 over 131 symbols, 97.7% above the floor (D2/D3/D4 already passed).
  DIRECTION: **LOOSER** — booked LOOSER without hedging because it converts a failing required
  control into a passing one, even though the failure was a defect in the statistic rather than
  in the swap. 3L/15T/9N.
AMENDMENT-28 (run-1 disclosure defect — contiguity drops, 2026-07-22): §3.4 requires events with
  no unbroken 1-minute outcome span to be "dropped and COUNTED". Run 1 recorded the count as a
  per-batch scalar broadcast onto every row, which cannot be aggregated (naive summation gave
  3.87M against 7,186 kept events). The attrition was large and invisible: 32,433 located D1
  events became 7,186 with outcomes (78% dropped); D2 68%, D3 55%, D4 69%. Fixed: located,
  with-outcome and dropped counts are accumulated per pool and emitted in each pair's
  `coverage` block, and `census.json` now carries the census-vs-layers reconciliation directly.
  DIRECTION: NEUTRAL (disclosure of an existing quantity; no rule changed). 3L/15T/10N.
```

```
AMENDMENT-29 (defect INTRODUCED by AMENDMENT-25, caught at QA run 12 before any re-run,
  2026-07-22): moving the MDE onto the contrast's own arm made "MDE = 0" and "the raw contrast
  is already materially positive" the SAME condition, because §4.2's plant sweep starts at 0.0.
  Two consequences, both fatal in the regime that matters: (a) `calibrate_cf_star` accepted 0.0
  as a valid 1× plant, so CF* would have been calibrated on the OBSERVED — possibly leaking —
  edge rather than a known causal one, which is precisely the AMENDMENT-13 defect, and it would
  have happened only where the tripwire's material-edge precondition is met, i.e. the one regime
  CF* is ever used in; (b) `label_band` nulls any MDE ≤ 0, so the same condition demoted a
  strongly positive contrast to SUGGESTIVE and **SUPPORTED — soil leg (i) — became unreachable**.
  Fixed at the root rather than by a guard: the MDE sweep now CENTRES the treat arm on the base
  arm (subtracting the observed contrast) before sweeping, so the MDE measures the arm's
  RESOLUTION at realised n independently of what was observed, u = 0 can never qualify, and the
  result is strictly positive or None. `calibrate_cf_star` additionally refuses any non-positive
  plant (UNDERIVABLE, never the prior), and `label_band` treats 0 as a valid resolution so the
  two consumers finally agree on what 0 means. Verified: on an arm with a 39.3 bps already-
  material raw edge the MDE is 2.0, not 0.0; SUPPORTED/SUGGESTIVE/CONTRADICTED/WASH/UNPOWERED
  are each reachable. Regression tests pinned.
  DIRECTION: **LOOSER** — centring removes the observed effect from the denominator of the
  `effect ≥ its own MDE` test, which lowers the MDE (D1: 13.0 → ~10) and therefore makes
  SUPPORTED easier to reach. Booked LOOSER without hedging even though the same change makes the
  LEAK gate strictly harder to satisfy (CF* can no longer be calibrated on the observed edge) —
  the label describes the effect on the positive-claim bar, not the net intent. 4L/15T/10N.
  COUNTER-DIRECTION, recorded at QA run 13's request: a smaller MDE also makes the FAMILY
  HARDER TO CLOSE, because fewer zero-spanning cells satisfy |effect| < MDE and so fewer land
  in WASH (the powered-null cell). The two effects point opposite ways and neither is netted.
  VERIFIED NOT TO MOVE RUN 1: run-1's D1 readings (+1.81 ci [−3.66, 7.10]; −3.22 ci
  [−12.86, 5.18]) label WASH at MDE 13.0 / 10.0 / 5.0 and only change below ~2, far under the
  centred value. Both SUGGESTIVE and SUPPORTED require ci_low > 0, which run 1 never had, so
  the MDE cannot resurrect the discarded null.
AMENDMENT-30 (§5 label gap found at QA run 13, quant-designer call, 2026-07-22): §5's bands were
  NOT exhaustive — a contrast with |effect| ≥ MDE and a CI spanning zero matched no band
  (SUPPORTED/SUGGESTIVE need ci_low > 0; CONTRADICTED needs ci_high < 0; WASH needs
  |effect| < MDE; UNPOWERED asserts MDE > |effect|, which is false there). The code returned
  UNPOWERED, which under AMENDMENT-24 means "horizon-covered but inconclusive" — silently
  converting a measured cell into an untested one on the checkpoint's master go/no-go.
  AMENDMENT-29's centring makes the gap REACHABLE (a smaller MDE moves cells out of WASH), so
  it had to be closed before the re-run. WASH was rejected as the fix: it is the design's
  POWERED NULL cell, and a point estimate larger than the arm's own resolution cannot support
  "nothing is there" (B-5, and the design's own "T1 UNPOWERED is INCONCLUSIVE, never a null").
  Resolution — a new band **IMPRECISE**: CI spans zero AND |effect| ≥ MDE. Mechanism: the MDE
  plants a CONSTANT shift on every treated event and therefore carries no dispersion, while a
  real effect does, so a day-concentrated effect can exceed the MDE and still fail to exclude
  zero. Reading: INCONCLUSIVE, never a null and never a positive; for the AMENDMENT-24 closure
  rule it behaves exactly like UNPOWERED (neither blocks nor contributes). §5 is now an
  EXHAUSTIVE decision table with no undefined cell, pinned by a test that sweeps effect × CI ×
  MDE combinations and asserts every result is a defined band. DIRECTION: NEUTRAL — closure
  semantics are unchanged (the affected cells were already non-contributing as UNPOWERED); the
  change is accuracy of the reported reason, and it forecloses a later mislabel as WASH that
  WOULD have been LOOSER. 4L/15T/11N.
AMENDMENT-31 (QA run 14 ordering defect, operator option A, 2026-07-22): §5's A-30 table said
  "MDE unavailable ⇒ UNPOWERED, tested first", which pre-empted CONTRADICTED even though that
  band is defined solely by `ci_high < 0`. A measured negative interval was therefore reported
  as untested whenever its control MDE was missing. Ordering is corrected: invalid/no CI first;
  then CONTRADICTED; then positive-CI labels (MDE-less positives are SUGGESTIVE); only a
  zero-spanning CI needs an MDE to separate WASH from IMPRECISE and is UNPOWERED without one.
  T4/T5 MDE curves remain mandatory under §4.2 and are implemented independently of this
  ordering fix; the clarification is not permission to omit them. DIRECTION: **LOOSER** — it
  makes measured evidence against the signed mechanism reachable, but it also moves an
  MDE-less positive interval from UNPOWERED to SUGGESTIVE. SUGGESTIVE cannot satisfy soil and
  does not contribute to family closure, yet booking the change at its permissive component is
  the conservative L-23 treatment. 5L/15T/11N.
AMENDMENT-32 (QA run 15 T2 plant specification, 2026-07-22): §4.2 required a known monotone
  score→return plant but did not pin its centring, grid or seed count, and the runner incorrectly
  called the real-read derangement-null quantiles an MDE. The plant is now fully specified:
  deterministic Spearman centring on the real arm; 0–30 bps per score-SD in 0.5-bps steps; 200
  seeded GLOBAL zero-fixed-point derangements at every evaluated point; and the first positive
  plant clearing deranged p95 with one-sided p ≤ 0.05 published in both plant-bps and rho units.
  The real read remains ≥2000 seeds. DIRECTION: **LOOSER** — replacing a misnamed null critical
  value with a planted resolution can make T2 support easier or harder; the permissive possibility
  is booked conservatively. 6L/15T/11N.
AMENDMENT-33 (QA run 15 publication-order clarification, 2026-07-22): §9's global phrase “MDE
  curves before any contrast” conflicted with its next step's per-pair reads. It now states the
  contamination-safe operational rule already accepted at QA run 12: every curve for a pair is
  immutable and published before that pair's first contrast; an earlier pair cannot adapt any
  later pair input. DIRECTION: NEUTRAL — pair estimands, populations and deterministic plants are
  disjoint and unchanged; only the scheduling sentence is made literal. 6L/15T/12N.
```

**Running count: 6 LOOSER / 15 TIGHTER / 12 NEUTRAL.** LOOSERs = AMENDMENT-18 (D6 widen),
AMENDMENT-24 (closure rule under D7), AMENDMENT-27 (bite computed per symbol), AMENDMENT-29
(MDE centred on the observed contrast), AMENDMENT-31 (MDE-less positive CI → SUGGESTIVE),
AMENDMENT-32 (planted T2 resolution). No
validity/causality threshold loosened. No LOOSER streak ≥ 3
(A-25 T → A-26 T → A-27 L → A-28 N → A-29 L → A-30 N → A-31 L → A-32 L → A-33 N).

**Contested direction label (QA run 2).** AMENDMENT-2 NEUTRAL vs possible LOOSER — recorded;
still short of a streak either way.

**Standing note for QA.** D1 τ / P_WIDE registration and count-only provenance stand for D1
sensitivities. Per-pair τ on prior-session-range scale is frozen from **counts only** before any
read. Any post-freeze change to τ, pool legs, arm cuts, holds, or pair set is an amendment with
direction; LOOSER streak ≥ 3 flags the execution gate.
