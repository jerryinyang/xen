# Data Analysis: EXP-019 — CF-VOLHARV-001/HYP-001 seed/fill falsification (4h, 16 instruments × 25 seeds)

Analyst: data-analyst (fresh interrogation, own code in `analysis_code/`). Emissions:
`data/strategy_runs/EXP-019` (400 runs, 286,476 legs), `EXP-019-delay1` (25 runs, 17,839 legs).
All numbers from `analysis_code/interrogate.py` → `results/*.csv` unless noted.

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation, all cells blocking_pass | PASS | `results/estimand_validation.json` (400 cells, manifest 16/16, missing []) + `results/estimand_validation_delay1.json` (25 cells) |
| Provenance (verdict-bearing columns ≤ t-1) | PASS | Entries fired only from a pre-run CSV fixed from (seed, bar calendar) — `Xen.RandomHold.cs` `FireRhScheduledEntries`; no price enters any decision; exits fire at completed-bar count only (`ProcessRhBar` matched-hold block). QA regenerated all 50 NZDUSD CSVs byte-identical (qa-review.md run 1) |
| Leak tripwire collapsed + non-vacuous | PASS | Tripwire 3 (entry-delay +1 twin, the only free input moved wholesale): live vs twin battery indistinguishable (§3 twin table; max pair-diff 0.74 bps, ≤1.6×SE). Non-vacuity: with no conditioning there is no edge to destroy — the twin instead verifies schedule data-INdependence, its designed role. Tripwires 1–2 (regeneration byte-diff, fill causality) passed in QA |
| Holdout untouched | PASS | All 425 runs under EXP-013/018 49% TRAIN fences; `HoldoutFence` stop; max emitted SourceCloseTime ≤ fence per cell (estimand gate fence check) |
| Price-primary | PASS | cTrader engine emissions, Mode=NativeOrders, m1 fills; no Python backtest anywhere |
| No experiment-local accounting | PASS | `check_no_local_accounting('experiments/EXP-019')` → ok; analyst code uses `xen.adjudication.per_leg_net` only |

Censored legs: **0** live, **0** twin (generator drop-can't-complete rule A2 worked as designed —
a clean-run invariant, confirmed).

## 2. Question list

| # | Question | Answer |
|---|---|---|
| 1 | Per-bar/per-leg reconcile? | PASS all 425 cells (gate artifact; smoke diff 2.3e-12 bps) |
| 2 | Estimand == traded object? | Yes — individual fixed-hold leg, no episode structure; stratum aggregation over identical objects (design §2) |
| 3 | Per-leg distribution | §3/§4; per-leg σ 40–500 bps by instrument/hold, means ≈ 0 |
| 4 | Episode anatomy | N/A by construction (no episodes); max concurrent legs 5–6 (cap 6, cap_skips ≈ 0–small) |
| 5 | Concentration | BTCUSD-48 probe: trim top 1%/3%/5% |legs| → mean 36.9→35.0/33.4/20.4 (tail-fed but not single-event); other strata ≈0, moot |
| 6 | Per-year stability | `results/per_year.csv`; BTCUSD-48: 2021 +73.5, 2022 +34.7, 2023 +11.0, 2024 +28.3 — 2021-bull-concentrated; NZDUSD/others: no stable year pattern |
| 7 | Per-stratum headlines | §3 battery table; 2/64 strata beyond MDE (≈3 expected by chance at 2×SE) |
| 8 | Occupancy story | ~96% bar-occupancy, avg ~2.8 open legs (cap 6) — matches the design's always-on random inventory; not a conditioned strategy, as intended |
| 9 | Ann. return/Sharpe vs B&H | Smoke NZDUSD: ann 9.7%/Sharpe 0.5 vs B&H −2.5% — a single seed's realization of a zero-mean construction (seed battery shows the dispersion; §4) |
| 10 | Exposure risk | Max 5–6 legs; per-leg MAE tracked; no exposure blowups (cap deterministic) |
| 11 | Cost sensitivity | §5: gross ≈ 0 ⇒ any positive cost ⇒ negative net; the deliverable is the floor itself |
| 12 | Control collapse fractions | Twin/live ratio ≈ 1.0 by stratum (nothing to collapse; verifies independence). Planted +15: battery-level detectable in 61/64 strata (MDE<15); per-seed CI criterion under-powered by design mis-spec (§6 anomalies) |
| 13 | "What would make it wrong?" per headline | NZDUSD ≈ 0: checked per hold, per year, per direction — all consistent. BTCUSD-48 +36.6: checked seed-sign coherence (13/25 → incoherent), per-year (2021-driven), trim (tail-fed) |
| 14 | Power / UNPOWERED | BTCUSD H∈{12,24,48} battery MDE 16.8/20.9/32.1 bps ≥ 15 → UNPOWERED for the plant scale, never read as negatives (predeclared §8 expectation matched) |

## 3. Evidence FOR the hypothesis (H_artifact: EXP-018 anomaly = sampling draw, E[gross]=0 holds)

1. **NZDUSD battery centres on zero in every stratum.** Battery means (gross bps/leg): H6 −0.73 (MDE 1.44), H12 +1.04 (2.85), H24 −2.85 (3.94), H48 +2.20 (5.31); n=25 seeds × ~4,450 legs/stratum. All |mean| < MDE.
2. **EXP-018's +31.5 lies ABOVE the entire 25-seed NZDUSD distribution.** Pooled per-seed means span [−11.5, +8.6] bps; percentile of +31.5 = 100% — outside the ceiling, exactly the ARTIFACT_CONFIRMED signature (a tail draw of the construction, not a property).
3. **Global battery ≈ 0.** Mean of all 1,600 seed-stratum means = −0.017 bps; median |battery mean|/MDE = 0.31; only 2/64 strata exceed MDE (~3 expected by chance).
4. **Direction split is drift-shaped, not asymmetric.** Long/short displacements track the analytic ±μ̂·H benchmark with opposite signs (e.g. NZDUSD H48: long −11.3 / short +15.7 vs drift ∓7.7 — negative-drift window, sides separate symmetrically). The "impossible signature" (both sides displaced the same way) appears in exactly one stratum (BTCUSD-48, §4.1).
5. **Delay-twin indistinguishable** (NZDUSD ×25 seeds, all bars +1): pair-diff means per hold 0.74/−0.27/0.12/0.58 bps, SEs ≈ 0.5–0.6 — schedule provably data-independent end-to-end.
6. **Bootstrap calibration clean:** at offset 0, per-seed CI_low>0 in 42/1600 seed-strata = 2.6% vs 2.5% nominal.

## 4. Evidence AGAINST the hypothesis

1. **BTCUSD-48: battery mean +36.6 bps, MDE 32.1** — the one stratum with a same-direction split displacement (long +39.8/short +34.5 above drift). Against reading it as PROCESS_ASYMMETRY: seed-sign coherence FAILS (13/25 positive vs ≥20 required by the predeclared band); 2021-concentrated (+73.5 bps 2021 vs +11–35 after); tail-fed (top-5% trim → +20.4); stratum is UNPOWERED (MDE 32 vs plant 15); all 25 seeds share one price window, so across-seed dispersion understates window-level uncertainty for common-path shocks — the +36.6 is ~1.1 seed-SD from zero at window level. Band: WASH/UNPOWERED, not asymmetry.
2. **EURUSD-12: +2.18 vs MDE 2.00** — marginal exceedance, 15/25 seeds positive (fails coherence), stable but tiny across years (+0.6…+4.3). One expected false exceedance among 64 strata. Band: WASH.
3. Nothing else. No stratum shows the PROCESS_ASYMMETRY triple (mean ≥ MDE ∧ ≥20/25 same-sign ∧ coherent split displacement).

## 5. COST_FLOOR deliverable (booked regardless) + substrate disclosure

Commission round-trip (FTMO snapshot 2026-07-04, per-side ×2 / round-turn ×1 readings, at median
entry price; **spread unpinned — live-only on FTMO page, must be added before any deployable claim**):

| Class | comm RT bps (×2) | Note |
|---|---|---|
| FX majors/crosses | 0.47–1.04 | e.g. NZDUSD 0.96, EURUSD 0.55, AUDJPY 1.04 |
| XAUUSD | 0.28 | percent-type; published fields inconsistent, disclosed in `xen.evaluation` |
| BTCUSD | 13.0 | 0.065%/side of notional |
| Indices (USTEC/US500/US2000/JP225) | 0.0 | spread-only pricing — the entire cost is the unpinned spread |

Gross ≈ 0 everywhere ⇒ net = −(commission+spread) — the floor any HYP-002 harvest structure must
clear per leg. 2× stress: double the table. Full per-symbol values: `results/costs.csv`.

**VR profile** (`results/vr.csv`, plot `vr_profile.png`): mean-reverting substrate (VR<1,
deepening with H) across FX and indices — strongest NZDUSD (0.92/0.88/0.80/0.80 at 6/12/24/48),
AUDUSD (0.95/0.90/0.80/0.76), GBPUSD, USDCAD; flat/random-walk BTCUSD (≈0.99–1.03), USDJPY,
XAUUSD, USDCHF. The oscillation HYP-002 wants exists in the FX block — but per §3 it is NOT
harvestable by unconditioned fixed-hold legs (as the analytic null demands).

## 6. Anomalies & open questions

1. **Design plant criterion mis-specified (disclosure, not a defect in the data):** §5's "battery must flag +15 in ≥24/25 seeds" reads per-seed CI_low>0, which has power only where the per-seed SE < 7.5 bps — realized per-seed SEs are 5–50 bps, so per-seed flagging fails in most strata (e.g. USTEC-48 0/25). The battery-level detector (across-seed mean vs MDE) — the §8 power object — detects +15 in 61/64 strata. Both readings reported; the bite check passes at the battery level, which is the level all §3/§4 reads use.
2. **BTCUSD-48** (§4.1) — if the operator wants to push: a window-level block bootstrap (resampling 4h blocks of the common path, not seeds) or an ex-2021 battery would settle it; both are new analysis passes, no new emissions needed.
3. ~17 stale schedule rows per seed (pre-2021 m1 feed start; uniform across seeds/instruments, QA-disclosed) — no effect on strata balance (hold counts 181–182 per seed).
4. Fill lags at session opens (~2% of fills 60s–2h late, never early; QA INFO-6) — direction-symmetric, cannot bias a coin-flip mean.
5. `spread_pips` unpinned in `xen.evaluation.FTMO_COSTS` — blocks only the final deployable-cost statement, not this experiment's verdict (gross reads).

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: SUPPORTED — ARTIFACT_CONFIRMED in all powered strata.** The EXP-018
  random-timing per-leg positive is a sampling draw of a zero-mean construction: 25 independent
  seeded schedules put NZDUSD at 0 ± MDE in every hold stratum, and +31.5 sits above the entire
  seed distribution. COST_FLOOR booked (§5). BTCUSD H∈{12,24,48} labelled UNPOWERED;
  BTCUSD-48/EURUSD-12 WASH (fail every coherence requirement of PROCESS_ASYMMETRY).
- **Driven by:** (i) NZDUSD battery ≈ 0 across all strata with +31.5 outside the seed
  distribution; (ii) drift-shaped direction splits everywhere (no coherent same-direction
  displacement passing seed-sign coherence); (iii) clean twin + calibrated bootstrap + byte-exact
  schedule regeneration removing every artifact channel.
- **Would change if:** a window-level bootstrap showed BTCUSD-48's +36.6 to be >2.5σ robust
  ex-2021 AND a fill-forensics pass found a directional fill asymmetry — neither is suggested by
  the current data.
- **Final verdict is the operator's.** Suggested probes if you want to push: BTCUSD-48
  ex-2021 battery; window-level block bootstrap; pin spreads and restate the cost floor at 1×/2×.

Plots: `plots/nzdusd_seed_battery.png`, `plots/battery_strata.png`,
`plots/direction_vs_drift_h48.png`, `plots/vr_profile.png`.
