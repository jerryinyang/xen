# Data Analysis: EXP-018 — CF-MR-005 HYP-003 deliberate ladder harvest disposition probe

Analyst: data-analyst (INFR-001), 2026-07-04. All numbers from
`analysis_code/interrogate.py` (+ inline probes noted) on the raw emissions via canonical
`xen.adjudication` / `xen.evaluation`. Frozen 4h RT costs: US2000 5.0 / NZDUSD 2.0 /
US500 3.0 / USTEC 4.0 / JP225 4.0 bps per leg (`adaptive_cost_bps_for`).

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation, all 14 roots + smoke | **PASS** | `results/estimand_validation.json` (`blocking_pass: true`, 15 roots); per-root reports in `results/`; reconciliation diffs ≤ 7e-12 bps |
| Provenance (verdict-bearing columns ≤ t-1) | **PASS** | table below |
| Leak tripwires collapsed + non-vacuous | **PASS (no live edge to survive)** | rt destroy moves the mean statistic by construction (different entries/exits: e.g. US2000 A/extend live +381.9 vs rt +187.2 bps/ep); delay1 reads graceful (collapse 0.42–1.13, no sign flip / discontinuity) — no timing leak signature. No cell admits, so "surviving edge" is moot |
| Holdout untouched | **PASS** | fences = 49% TRAIN cutoffs (US2000 2024-09-10T09:33Z, NZDUSD 2024-09-06T05:42Z, US500 2024-09-17T17:26Z), all < 70% cut; last emitted bars precede fences (estimand reports) |
| Price-primary under fence | **PASS** | engine emissions `data/strategy_runs/EXP-018-4h-*/cross_instrument_spread_mr_*_4h_*`; m1 native fills (Mode=3) |
| No experiment-local accounting | **PASS** | `check_no_local_accounting('python/experiments/EXP-018/code')` → `{'ok': True}` |

Provenance (key columns; engine structural, verified by QA golden trace + spot-read):

| Column | Inputs & timing | ≤ t-1? |
|---|---|---|
| Entry fills (`cis_trades.EntryFillPrice`) | limits rested from completed-bar decision state (`Xen.cs RearmBracket`, `_decisionBracket` = bar-i state), filled by cTrader m1 next bar | ✓ |
| TP refresh (`RefreshedTp`) | `_decisionBracket.ExitPrice` = anchor at bar i, applied to bar i+1 onwards | ✓ |
| `EntryZ/EntrySigma/EntryTrend*` | decision-bracket state at arm bar | ✓ |
| `RealizedBps` | engine fill-to-fill; no Python recompute | ✓ |
| rt schedule entries | pre-generated seeded CSV (`gen_exp018_schedules.py`, seed 20260704), market order at scheduled bar's next open | ✓ |

## 2. Question list

1. Reconcile per-bar↔per-leg per cell? → ANSWERED §1 (≤7e-12 bps, all cells).
2. P&L object = episode (design §2)? → ANSWERED: primary read on `build_episodes` output; per-leg secondary (§3/§4).
3. Per-leg net distributions? → ANSWERED §3/§4 tables.
4. Episode anatomy? → ANSWERED §4 (counts, legs/ep, durations, peak legs).
5. Concentration (net minus top winners)? → ANSWERED §4 (US2000 A/extend: top-5 episodes = 82% of net).
6. Year stability? → ANSWERED §4 (2022-carried everywhere).
7. Per-stratum? → all headline numbers are per cell; pooled never used.
8. Occupancy matches design story? → ANSWERED §4 (52–69% occupancy, avg 2.2–5.7 open legs — a standing inventory engine, not a sparse dislocation fader).
9. Ann return/Sharpe/maxDD vs B&H? → ANSWERED §3/§4 (exposure-honest reads).
10. Exposure risk? → ANSWERED §4 (peak 43 legs US2000; maxDD ≈ −29.5k bps ≈ 61% of total net).
11. Cost sensitivity? → ANSWERED §3/§4 (cost not the binder anywhere; US2000 per-leg survives 2× cost).
12. Control collapse fractions? → ANSWERED §3/§4 (rt 0.49 / 1.96 / −2.09 / 2.74; shift 0.53–2.72; delay 0.42–1.13).
13. Falsification probe per headline? → ANSWERED: per-leg CI_low>0 recomputed on the rt controls (§4 item A2 — the decisive read); concentration & year splits as artifact probes.
14. Power on negatives? → ANSWERED: episode MDEs 23.8–655 bps/ep; per §8 of design, US2000 A/extend is POWERED for the residue effect (MDE 504 < ~575); US500 well-powered (MDE 23.8); B/extend marginal (MDE 655).
15. (mechanism) Does dislocation timing beat matched random timing? → ANSWERED §4 A1/A2 — no.
16. (mechanism) Ladder-depth gradient? → ANSWERED §3 F3 (deeper levels earn more per leg, both US2000 arms).

## 3. Evidence FOR the hypothesis

- **F1 — US2000 A/extend per-leg net is positive at frozen cost and robust to 2× cost.**
  n=1317 legs, net/leg +36.8, CI [+9.2, +64] at 5 bps; at 10 bps CI_low +4.2. (Block-5
  bootstrap over time-ordered legs.) The residue's per-leg signature reproduces on the
  deliberately-specified vehicle.
- **F2 — exposure-honest economics on US2000 A/extend clear the design bar:**
  ann. return on avg deployed exposure 24.8%/yr vs exposure-time-matched B&H 2.8%/yr
  (occupancy 0.54, avg 5.1 legs). Arm B and allow also exceed matched B&H (4.0%/1.3% and
  13%/2.7%).
- **F3 — ladder-depth gradient persists** (residue's signature shape): US2000 A/extend
  net/leg by level +17.0 / +49.4 / +67.5 (L0/L1/L2, n=642/441/234); arm B −2.2/+5.5/+21.3.
- **F4 — NZDUSD negative control stayed negative** (−273.6 bps/ep; per-leg −20.6): no
  spec-induced artifact inflating the vehicle; the experiment's discrimination machinery worked.
- **F5 — causal integrity:** delay-1 tripwire degrades gracefully everywhere (collapse
  0.42–1.13, no sign flip) — what P&L exists is not a timing artifact.

## 4. Evidence AGAINST the hypothesis

- **A1 — the predeclared PRIMARY fails in every live cell: no episode-net CI_low > 0.**

| Cell | n_ep | mean bps/ep | 95% CI | MDE | med | band (§7) |
|---|---|---|---|---|---|---|
| US2000 A/extend | 127 | +381.9 | [−122, +809] | 504 | +197 | **WASH** (powered for residue ~575) |
| US2000 A/allow | 132 | +82.5 | [−151, +228] | 234 | +148 | WASH |
| US2000 B/extend | 70 | +85.2 | [−570, +644] | 655 | +205 | WASH (marginal power, predeclared weak) |
| US500 both-leg A | 79 | −2.5 | [−26, +24] | 24 | +20 | **WASH, well-powered** — the VAL-006 "4/4 variants positive" cluster does not reproduce |
| NZDUSD (neg-ctl) | 75 | −273.6 | [−694, +52] | 421 | +161 | control-pass (≤0) |

- **A2 — the dislocation-conditioning claim fails its own kill test (decisive).**
  Random-timing matched-cadence/hold ladders earn a comparable amount:
  - US2000 A/extend: rt mean +187.2 bps/ep, collapse fraction **0.49**, live−rt diff CI
    [−516, +866] — indistinguishable.
  - US2000 A/allow rt **beats** live (collapse 1.96); B/extend and US500 rt reads are noise
    (−2.09, 2.74 — magnitudes tiny).
  - **NZDUSD rt per-leg net = +31.5, CI [+13.7, +49.9] — CI_low > 0 from PURE RANDOM TIMING**,
    while the dislocation-timed live arm loses −20.6/leg. A random ladder can produce exactly
    the per-leg-CI-positive read the residue was built on; dislocation timing *anti-selects*
    on NZDUSD. F1 therefore cannot be read as dislocation-conditioned: US2000 rt per-leg is
    +12.9 [−10.7, +37.5] — positive point value, and the live-vs-rt per-leg difference is not
    resolvable.
- **A3 — not regime-robust.** Every positive cell is 2022-carried: US2000 A/extend 2022
  +811 [+348, +1441] is the only CI-positive year; 2023 mean −393; A/allow and US500 same
  shape (2022 the only positive year). Direction attribution: US2000 live longs +72.7/leg
  (n=697) vs shorts +7.2 (n=620) — long-side index drift dominates.
- **A4 — heavy concentration + inventory tail.** US2000 A/extend: top-5 of 127 episodes carry
  82% of total net (48.5k → 8.9k bps without them); B/extend goes negative without its top-1;
  peak concurrent exposure 43 legs (A/extend), maxDD −29.5k bps ≈ 61% of total net on unit
  notional; ann. return on PEAK exposure 2.9%/yr ≈ B&H matched 2.8% — the exposure-honest read
  survives only on *average*, not peak, deployment.
- **A5 — arm B (braked) adds nothing:** exits split tp_anchor 579 / sl_outward 588 — the SL
  fires as often as the TP; per-leg +4.5 [−21.6 CI_low at cost]. The harvest does not survive
  braking, consistent with the P&L being drift-carry harvested by unbraked adds.
- **A6 — shift disclosure (non-binding):** collapse 0.53 (US2000 A/extend), 1.03 (NZDUSD),
  2.72 (B/extend) — no coherent construction-dependence signal; consistent with EXP-015's
  finding that the basket is trigger, not source, and with A2 (timing itself is not the source
  either).

## 5. Anomalies & open questions

- NZDUSD rt control's strong positive (+847 bps/ep on 37 episodes; per-leg +31.5 CI_low>0) —
  random market-timed ladders with live-drawn holds earn significantly on an instrument whose
  B&H is negative. Suggests the matched-hold construction itself harvests two-sided
  vol/rebound structure; worth remembering when reading ANY per-leg CI on ladder objects.
- rt twins produce fewer, longer episodes than live (template placement merges overlaps:
  91 vs 127 on US2000 A/extend; 37 vs 75 NZDUSD) — cadence matched at the leg level, not the
  episode level; disclosed, does not change A2's direction.
- Live long/short asymmetry (A3) suggests any future probe should split episode economics by
  side before believing a symmetric-fade story.

## 6. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: NOT SUPPORTED.** The hypothesis required dislocation-conditioned,
  exposure-honest, regime-robust positive episode economics in the residue cells and not in
  the control. Realized: episode-level WASH in all four residue cells (US500 well-powered
  wash), random-timing kill test unfalsified (collapse ~0.5–2.7; a random ladder reproduces
  the per-leg positive signature outright on NZDUSD), 2022-only regime concentration.
  The negative control behaving as predicted strengthens confidence in this read.
- Driven by: A1 (primary WASH everywhere), A2 (random-timing indistinguishability + NZDUSD
  rt CI_low>0), A3 (2022/long-drift concentration).
- Would change if: a paired live-vs-rt design with episode-level cadence matching and
  side-split economics showed a reproducible positive live−control difference on new data;
  or a longer window restored 2023-class regimes with positive episode nets.
- Final verdict is the operator's. Suggested probes if you want to push: (a) side-split
  (long-only vs short-only) episode economics on the existing emissions; (b) rt variant with
  episode-level (not leg-level) cadence matching; (c) US2000 A/extend live−rt per-leg paired
  difference with dir/level stratification.
