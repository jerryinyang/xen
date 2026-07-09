# CF-HTFDI-001 — Higher-Timeframe DI Conditioning (MTF continuation)

**Status:** `RETIRED (2026-07-09, operator-signed, checkpoint-010/011 retrospective)` — EXP-025
HYP-A graduation NOT SUPPORTED (magnitude, not existence; powered negative, 0/440 qualifiers,
0 TEST reads). Channel real at ≈4 bps/trade h48 (~1–3 after capture dilution) — below cost/selection
bar; registration target was a 4.1× units artifact. Retrospective:
`docs/experiments-docs/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/retrospective.md`.
Re-open requires a NEW family (own D0) with a magnitude-changing construction.
*(Prior)* `REGISTERED (2026-07-08). G0 PENDING` — promoted from the SPDR CTRL-01/02/03 series
(WORTH_EXPLORING, operator-signed 2026-07-08; **corrected same day post-audit** — see Correction
below). 0 slots, 0 counted TEST reads, holdout sealed.
**Family ID:** CF-HTFDI-001. **Chapter:** 02 (cTrader-primary era).
**Prior evidence (screen, not a read):** SPDR-001/002/003 — checkpoint Phase 010
`docs/experiments-docs/checkpoints/2026-07-08-010-htf-di-conditioning-spdr-series/` (binding
corrected `synthesis.md`; audit + probe in `correction/`); per-leg `python/experiments/SPDR-00{1,2,3}/`.
**Origin idea:** `origin-mtf.md` in the Phase-010 checkpoint (verbatim `mtf.md`).

## Correction (2026-07-08)

The original registration carried two tiered threads (A continuation / B fade). An independent
audit + correction probe (`correction/correction.md`) found (1) the SPDR-001 CIs under-blocked for
the overlapping per-bar estimand (block=5 vs dependence ≈ H) and (2) the SPDR-003 fade cell
computed on a side-signed interaction, not the labelled raw-move conditioning. Under corrected
statistics **no fade-signed cell is CI-clear anywhere**; Thread B was **withdrawn (NOT
SUPPORTED)** and EURUSD 1d/1h was demoted from Thread-A anchor to a power-up stratum. This card
was rewritten in place accordingly.

## Thesis

Higher-timeframe (HTF) context — specifically the last **closed** HTF bar's directional state
(Wilder ±DI) — conditions the sign of the lower-timeframe (LTF) forward return. The effect is a
pure conditioning shift: on a null (random-sign) LTF base `E[sign·m]=0`, so any CI-clear
`dir_gap = E[m|+DI] − E[m|−DI] = 2·Cov(htf_dir, m)` is HTF's own contribution with no base-strategy
confound. On the corrected TRAIN evidence the coupling is established as **continuation on USTEC
1h/5min only**; the high-vol ATR regime **amplifies** it (interaction). The edge is
**magnitude-weighted** (aligns the position with the larger forward moves), not a per-trade
hit-rate bias.

This is NOT a universal "HTF improves LTF" claim (recorded NOT SUPPORTED). It is an
instrument-specific directional-conditioning family with, at present, a single supported stratum.

## Registered thread (single)

| Thread | Coupling | Anchor stratum (corrected SPDR evidence) | Hypothesis |
|---|---|---|---|
| **A — continuation** | trade WITH last-closed HTF DI | **USTEC 1h/5min**: dir_gap +0.09→+0.50 ATR, CI-clear at all four holds under hold-matched blocks (random base); independently CI-clear +0.26→+0.39 at H24–H48 on the blind momentum base (non-overlapping trades); corrected breadth 9+/0− of 84 DI-axis cells; survives mis-aligned-HTF control and phase-shift control; HTF-specific vs the LTF-momentum twin (direction corroborated) | HYP-A |

**Power-up stratum (inside HYP-A, not separately registered):** EURUSD 1d/1h — point dir_gap
+0.27→+0.47 ATR, no hold CI-clear under corrected blocks (B-5 power statement). The graduation
experiment may include it as a pre-registered secondary stratum; it carries no screen evidence
weight.

**Withdrawn (NOT SUPPORTED, corrected):** Thread B (XAUUSD fade). All original pillars failed
re-derivation: the 17/23 negative-cell breadth collapsed to 4+/3− at block=H (under-blocking
artifact); the −0.86 "powered cell" measured the side-signed reversion × DI interaction (raw-move
conditioning −0.083 [−0.68,+0.53] n.s., both half-splits n.s.); EURUSD-intraday and BTC-daily fade
cells not CI-clear. **Revival condition:** a pre-registered, adequately powered CI-clear negative
`dir_gap` on the raw-move estimand with dependence-matched blocks. The symmetric-estimand logic
(a real negative = equal-information fade signal) remains valid; the corrected data contain no
real negative to read.

BTCUSD 1h/5min continuation is **explicitly NOT registered as a thread** — CI-clear H12–36 but
mostly shared with plain LTF autocorrelation (LTF-own +0.20 > HTF +0.13; loses conflicts).

## Control apparatus (carried from the SPDR legs — CONTROLS, not candidates)

The three CTRL bases were **measurement instruments**, not tradable candidates. The random base
especially has **no candidacy of its own** — registering it would be registering the ruler. Its
machinery graduates on the **control side of the ledger**:

1. **25-seed matched-cadence random battery** — the availability benchmark inside the
   cTrader-primary run (the Control-B role), now with costs modeled; any vehicle is ranked against
   its own matched random battery.
2. **Random-entry reference arm** — a CTRL-01-style random-sign arm kept **alongside** the base
   vehicle, so the HTF conditioning effect can be re-measured on TEST **without base confounding**
   (the null-base estimand is the reference implementation of the graduated hypothesis).
3. **Null sentinels** — at least one symmetric-sign gating variant (ADX-only / ATR-only, no DI),
   which behaved as null on TRAIN; kept so the TEST-side machinery has a known-null to verify
   itself against.

**QA note:** all three are declared as **named controls with pre-registered seeds** in the
experiment design doc, so a fresh-context QA pass does not flag an undeclared arm touching TEST.

## Design constraints (binding on the graduation experiment — corrected synthesis §7)

1. **Vol-regime interaction as an AMPLIFIER hypothesis** — high-vol amplifies the continuation
   effect (established: BTC `atrH_adxHi_di` +0.12→+0.41 CI-clear all holds); the low-vol branch
   showed no CI-clear effect in either direction. Do NOT carry "ATR sets the sign".
2. **Uncapped / horizon exit** — the edge is magnitude-weighted; capping winners clips it. If a TP
   is used, measure the erosion explicitly.
3. **Pre-registered family-wise max-stat per instrument over its holds** — the honest multiplicity
   test; answers the 960×3-cell screen multiplicity.
4. **Raw-bps / fixed-window ATR for any dispersion claim** — never ATR[t−1] (≈1.5× normaliser
   inflation, established all 3 legs).
5. **Sign fixed a priori from TRAIN for the registered stratum only:** USTEC 1h/5min =
   continuation. No other instrument sign is established; no fade prior anywhere.
6. **Dependence-matched uncertainty** — any CI on an overlapping per-bar estimand uses
   block ≥ hold H (or non-overlapping trade series). Lane-spec rule from the correction.

## Fixed first-branch definitions (G0)

1. **HTF state at LTF entry bar `t`:** Wilder ADX / ±DI / ATR(14) from the **most recent HTF bar
   whose `CloseTime < Open(t)`** — never the still-forming HTF bar (the single most likely MTF
   leak; enforced in code + golden trace). Decisions on confirmed bars (`≤ t-1`), acted at next
   bar open; open-to-open returns.
2. **Domain pairs:** 1h/5min primary; 1d/1h only as the pre-registered EURUSD power-up stratum.
   **4h/1h is registered NON-baseline / recorded NOT SUPPORTED** (structurally small, all CIs
   include 0, all 3 legs).
3. **Direction filter:** `LONG = +DI > −DI`, `SHORT = +DI < −DI` (continuation convention).
4. **Vol-regime interaction:** ATR(14) LOW/MED/HIGH robust regime, measured as an amplifier
   (constraint 1).
5. **Hold horizon:** H ∈ {1,2,3,4}× the HTF/LTF ratio in LTF bars; fixed horizon exit.

## Hypotheses

| ID | Question | EXP-ID |
|---|---|---|
| HYP-A | Does HTF-DI **continuation** conditioning (CTRL-02 breakout vehicle) carry a net-of-cost tradable directional edge on the 22-symbol universe at 1h/5min, with the vol-regime interaction measured, vs the matched random battery? Scope: §Phase 011 graduation scope. | **EXP-025** (design 2026-07-08, `python/experiments/EXP-025/design.md`) |

(Former HYP-B — fade on XAUUSD — withdrawn at the correction; see Exclusions. Its revival requires
new pre-registered evidence, not a re-read of this screen.)

## Exclusions / registered non-baseline branches / deferred

- **NOT SUPPORTED (recorded):** universal "HTF improves LTF" thesis; ATR as a *direct* dispersion
  signal (retained only as the amplifier interaction); ATR as a sign-setter (low-vol branch not
  CI-clear); 4h/1h domain; BTC 1h/5min continuation as an HTF-specific thread; **XAUUSD fade
  thread (withdrawn at the 2026-07-08 correction — under-blocked CIs + mislabelled estimand)**.
- **Deferred design hypothesis (one-leg, 002 only):** ADX conditions LTF *dispersion* more cleanly
  than ATR — carried as a question, NOT an established axis.
- **Separate exploration log line (NOT this family):** **tail-managed naive base** — both
  informative bases (momentum, reversion) are median-positive / tail-killed
  (`mean_excl_worst5` +ve 46/48; BTC 4h/1h median>0, mean<0, skew −0.55→−1.18). A risk/tail overlay
  is an orthogonal direction; if pursued it makes one base the **object** of study, not an
  instrument here. Logged for a future own-D0 family, not opened.

## Phase 011 graduation scope (amendment 2026-07-08, operator-directed)

Scope for the HYP-A graduation experiment, fixed before design. Rationale: **SPDR qualified the
idea, not the instruments** — the experiment selects instruments; the exploration plane is
stripped to the axes the corrected screen left alive.

**Vehicle.** CTRL-02 momentum breakout (close beyond last-X HH/LL of prior bars) gated by
HTF-DI confirmation, trade WITH last-closed HTF DI. cTrader-primary C# `ISignalModel`, costs
modeled. (CTRL-03 produced no survivors on the corrected estimand; CTRL-01 machinery graduates as
the control apparatus only.)

**Plane (operator-selected 2026-07-08):**

| Axis | Values |
|---|---|
| Instruments | **full 22-symbol loaded universe** (10 currencies + 10 indices + XAU + BTC; all VAL-admitted) |
| Domain | **1h/5min only** (1d/1h deferred; 4h/1h stays NOT SUPPORTED) |
| Variants | **`di` + 3 ATR×DI** (`atrL_di`/`atrM_di`/`atrH_di`) — ADX axis dropped (dead on the mean; adx≥75 absent regime) |
| Hyperparameter 1 | breakout lookback X (HH/LL), small predeclared grid (e.g. {2,3,4,5,8}) |
| Hyperparameter 2 | exit method (below), each measured vs the fixed-hold benchmark |
| Hold H (benchmark exit) | {1,2,3,4}× ratio (12/24/36/48 LTF bars) |
| Frozen | ADX/DI/ATR periods = 14 (not hyperparameters; screen provenance) |

**Exit-method candidate set** (each requires cTrader-implementation revision + fitness review at
design; fixed-hold exit is the benchmark; per constraint 2 any capping exit must have its erosion
measured explicitly):
1. Triple-barrier (CF-CAPGEO-001 machinery, TP/SL/time);
2. Trailing last-X HH/LL (KB global-technique);
3. Heiken-Ashi trailing exit (KB Pattern 2);
4. Adverse-excursion stop only (no TP — motivated by the tail-eaten base finding);
5. HTF-DI-flip exit (exit when the last-closed HTF DI direction flips — mechanism-native,
   uncapped, horizon-free);
6. Opposite-breakout exit (the entry signal reversing).

**Selection model.** Neighbour-stability ("plateau") selection: a parameter cell qualifies only if
its ±1-step neighbourhood also clears (median read); isolated maxima disqualified. To be
registered as a reusable component (`SEL-NEIGHBOR`) in `global-techniques.md` + the multiplicity
registry before measurement.

**Protocol.** `WF-EXPANDING` walk-forward with all optimisation/selection folds **inside TRAIN
(first 70%×70%)**; TEST touched once per surviving stratum as a counted confirmation read
(cap 2/stratum honored), under the pre-registered per-instrument max-stat over holds + Holm across
instruments. Dependence-matched blocks everywhere (constraint 6). Sign priors: USTEC 1h/5min
continuation only; all other instruments two-sided at registration (a corrected-statistics fade
appearing elsewhere is admissible evidence — priced, not presumed).

## Implementation path

cTrader-primary (C# `ISignalModel`) — the screen was TRAIN-only vectorised Python and makes **no
tradability claim**. Full pipeline: mechanism-first design → fresh-context QA → engine execution →
estimand gate → data-analyst → operator verdict. Costs modeled at the graduation experiment (never
in the SPDR screen).

## Real-price outcome discipline / holdout

All SPDR evidence is TRAIN-only (first 70%×70%), 0 counted TEST reads, holdout never touched. The
global final-30% holdout remains sealed. The USTEC continuation sign is carried as a TRAIN prior;
TEST reads are counted and governed at the graduation experiment.

## EXP-025 evidence (2026-07-09 — evidence row only; status transition reserved for checkpoint retrospective)

**EXP-025 (HYP-A graduation) COMPLETE — operator verdict NOT SUPPORTED (magnitude, not
existence).** T1-terminal: 0/440 SEL-NEIGHBOR qualifiers (own-F0 CI_low > 0 fails in every
cell), 0 counted TEST reads spent, powered negative (MDE 0.18–5.23 bps; 2.43M TRAIN trades).
Reconciled units artifact: the design's "30–60 bps" target used a 1h-ATR divisor where the
SPDR screen normalised by the 5min LTF ATR(14)[t−1] — 4.1× inflation; the true screen effect
is ≈4 bps/trade at h48 (0.2–1 at short holds) and REPLICATES in the engine ref-arm (0.42 vs
0.50 ATR_5m at h48) and in the 25-seed diagnostic battery (US500 cells ≥2 seed-SD; genuine
direction-timing gap +1.9–6.2 bps on traded slots). Post-dilution tradable residue ~1–3
bps/trade: below FX commission, ~1/10 of the noise-robust selection bar on indices. Index
grid positives drift-shaped (99% drift-side aligned), no DI dose-response; FX 200/200 ≤ 0.
Engine/apparatus exonerated (provenance hard-assert + golden trace; sentinel 1/22 vs
threshold 3). Two external reviews (2026-07-09) confirmed the chain; design gaps codified as
KB **L-21..L-24** (unit pin + money-unit floor binding in `docs/references/spdr-lane.md`).
Exit-method (T2) rescue not recommended. `python/experiments/EXP-025/report.md`.
