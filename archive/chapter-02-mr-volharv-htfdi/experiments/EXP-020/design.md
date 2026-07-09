# EXP-020 — CF-VOLHARV-001/HYP-002: structure-borne oscillation harvest — rebalance + grid arms (price-primary, 4h)

**Stage:** 1 (quant-designer). **Status:** DESIGN — awaiting QA pre-exec (fresh context) →
operator execution gate. **Family:** CF-VOLHARV-001 (gate lifted by checkpoint-007
retrospective, 2026-07-05). **Checkpoint:** `2026-07-05-008-cf-volharv-001-structure-harvest`.
**Slots:** 0 at design. **Counted reads:** 0 (TRAIN only). **Holdout:** sealed.

Operator-locked (elicitation 2026-07-05): BOTH structures as arms (rebalance + grid); full
16-instrument universe; all structure parameters derived candidate-blind from EXP-019
measurements (zero tuning); spread snapshot supplied (closed-market ceiling — see §7 blocker).

---

## 1. Question + mechanism statement

**One falsifiable question.** Does a rebalancing/crossing structure convert the measured FX-block
oscillation (EXP-019: VR 0.76–0.92 at H=6–48) into positive net expectation at capped
inventory — where EXP-019 proved the unconditioned fixed-hold object cannot (E[gross]=0)?

```
MECHANISM: range persistence (VR<1 ⇒ negative return autocorrelation at 6–48×4h horizons)
  pays a structure that mechanically sells rises and buys dips: each completed
  down-up (or up-down) traversal of width g realizes ≈ g·(traded size) that an
  unrebalanced holder does not book. The harvest scales with realized variance × MR
  strength and is paid for in crossings (spread+commission per rebalance trade) and in
  tail inventory (a trend that never crosses back). P&L-bearing object: ARM R — the
  continuous rebalanced-portfolio path (per-bar return + per-rebalance-trade ledger);
  ARM G — the grid round-trip (paired fill+unwind) plus censored end-inventory MTM.
  Cadence: rebalances/crossings every ~2–10 bars (derived, §4). Two-sided by
  construction; no directional forecast anywhere.
DERIVED: estimand = ARM R: Δ(per-bar net log return) vs unrebalanced same-mix B&H twin
                    (the classical rebalancing premium, drift cancels in the pair);
                    ARM G: per-round-trip net bps + episode(=month) net incl. MTM
         null     = twin-differencing (premium=0 if no oscillation harvest) + RW-block
                    instruments as mechanism negative controls (VR≈1 ⇒ premium≈−costs)
         horizon  = structure-intrinsic (band/spacing g), not a fixed clock
         test     = block bootstrap on premium series per stratum; MR-vs-RW-block
                    contrast as the discriminating prediction
```

The mechanism makes a **discriminating prediction**: premium > costs possible only on the MR
block (NZDUSD/AUDUSD/GBPUSD/USDCAD); on VR≈1 instruments (BTCUSD, JPY crosses, XAUUSD,
USDCHF) the same structure must earn ≈ −costs. A positive on the RW block = artifact alarm.

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object:
    ARM R: YES — estimand is the emitted rebalanced path itself (per-bar) and its trade
      ledger; the premium is a paired difference of two emitted paths (twin also engine-run).
    ARM G: YES — per-round-trip P&L on engine fills + month-episode net incl. MTM of open
      inventory (censoring disclosed, never dropped — the e1-survivorship lesson, VAL-006). # B-8/L-16
  measured conditioning event == traded entry event: YES —
    ARM R: rebalance triggers when |w−w*| ≥ b at bar close t−1, trades at bar-open t
      (measurement conditions on the same t−1 close state).
    ARM G: resting limits AT grid levels; fill event == limit touch (m1, native orders);
      availability/quality reads condition on fills, not on close-breaches.               # B-4
  effect-splitting windows non-overlapping: YES — arms run as separate engine runs
    (separate confs); no shared positions; cross-arm comparison is disclosure-only.       # B-9
```

## 3. The two arms (structures, fully specified)

**ARM R — banded rebalance (volatility pumping):**
- Virtual portfolio per instrument: constant-mix w* = 0.5 asset / 0.5 cash, unit notional.
- Trigger: at bar open t, if weight w(t−1 close) outside [w*−b, w*+b] → trade back to w*
  at open (market order). Band b derived §4.
- Emission: per-bar path + every rebalance trade (side, size, fill).
- **Twin (same run count):** identical 50/50 start, NEVER rebalanced (pure B&H mix) —
  same drift exposure, zero crossings. Premium(t) = R_reb(t) − R_unreb(t), computed by the
  analyst from the two emissions (both engine paths; no synthetic prices).

**ARM G — symmetric fixed grid:**
- Anchor A = previous calendar-month close (deterministic, causal, monthly reset; open
  inventory carried across resets, never force-closed by the reset).
- Levels: A ± k·g, k = 1..4 per side (inventory cap 8 legs, mirrors EXP-019's cap logic).
  Buy limits below A, sell limits above A, 1 unit each (native pending orders, m1 fills).
- Unwind rule (unambiguous): a buy filled at A−k·g rests its unwind sell at A−(k−1)·g —
  exactly one level toward the anchor (k=1 unwinds at A itself); mirrored for sells above A.
  Each completed round trip books +g minus costs. No SL; month-end censored inventory
  marked to market and disclosed per episode.
- **Twin:** same grid geometry with levels placed at A ± k·g but direction-INVERTED
  (buy above / sell below — momentum grid). Twin entries are stop orders (a buy at A+k·g
  triggers on a rise); twin unwind rule (clarified 2026-07-05, pre-implementation): a buy
  filled at A+k·g rests its unwind sell at A+(k+1)·g — one level AWAY from the anchor, the
  mirror of the MR rule; each completed round trip books +g minus costs (same width, same
  costs, opposite conditioning — the only construction satisfying the B-6 declaration). Under VR<1 the MR grid should harvest and the
  momentum grid should bleed symmetrically; under VR≈1 both ≈ −costs. Sharper than a
  random twin (L-19: single random draws are noisy yardsticks) and needs no schedule RNG.

## 4. Parameter derivation (candidate-blind, zero tuning)

All from EXP-019 emissions (already booked) or bar data before the TRAIN band start:
- σ_H per instrument: median |H-bar log move| at H=12 from EXP-019's substrate profile.
- ARM R band: b = 0.5·σ_12 (in weight terms: |Δw| = 0.5·|Δp|/p ⇒ b_w = 0.25·σ_12).
- ARM G spacing: g = σ_12 (one typical 2-day move per level).
- ONE value per instrument, fixed in the conf, derived by a committed script
  (`derive_exp020_params.py`) that reads only EXP-019 result artifacts — rerunnable by QA,
  byte-diff. No grid of alternatives; sensitivity is HYP-002b territory if supported.
- Expected cadence check (informative): implied crossings/month from σ and g; if a cell
  implies <4 crossings/month it is predeclared low-cadence (power note §8).

## 5. Scope

| Item | Value |
|---|---|
| Instruments | 16 (full universe minus DE30). MR block predeclared PRIMARY: NZDUSD, AUDUSD, GBPUSD, USDCAD. RW block predeclared NEGATIVE CONTROLS: BTCUSD, USDJPY, AUDJPY, GBPJPY, EURJPY, XAUUSD, USDCHF. Middle block (EURUSD, indices) disclosure. |
| Domain | 4h decisions; ARM G fills on m1 (native pending orders, Mode=3) |
| Band | TRAIN only, EXP-013/018/019 fence lineage (same `AnalysisEndUtc` per instrument as EXP-019) |
| Runs | ARM R: 16 + 16 twins; ARM G: 16 + 16 inverted twins = 64 runs (+4 delay twins §7: NZDUSD/USDCAD × both arms) |
| Sizing | fixed unit notional; no compounding, no sizing rules |
| Inventory cap | ARM G: 4 levels/side = 8 legs hard cap; ARM R: bounded by construction (w∈[0,1]) |
| Model | new C# `RebalanceHarvestModel` (ARM R + twin flag) + `GridHarvestModel` (ARM G + invert flag); reuse EXP-019 cap/emission machinery |
| Exclusions | holdout never loaded; TEST band never emitted; EXP-016 TEST rows excluded |
| Complexity budget | 4 stat reads (premium per block, grid RT per block, MR-vs-RW contrast, cost sensitivity), 6 plots, 2 C# models + 1 param-derivation script |

## 6. Controls (validity proofs)

```
CONTROL unrebalanced-twin (ARM R primary comparator):
  question answered: is there a rebalancing premium at all (harvest beyond holding)?
  population: the identical 50/50 portfolio path without rebalancing; DISJOINT decision set
    (zero trades vs N trades) — it CAN show a different answer (premium ≤ 0 whenever
    oscillation fails to exceed crossings cost).                                          # B-1
  bite/MDE: premium series MDE via block bootstrap on ~4,900 TRAIN bars ≈ 0.4–1.2 bps/bar
    equivalent; expected premium from theory ≈ w(1−w)·σ²_bar·(MR boost) — computable per
    instrument at design time from EXP-019 σ; plant: a synthetic +2 bps/rebalance offset
    injected analysis-side must be detected in the premium read before the real read.     # B-5
  non-vacuity: premium differences the exact statistic under test (mean per-bar diff).    # B-6
  expected if H true: premium > 0 on MR block, ≈ −cost drag on RW block.
  expected if H false: premium ≈ 0 gross everywhere (costs make it < 0).
  disclosure: collapse fraction = twin premium / arm return; per stratum.                 # B-2
CONTROL inverted-grid twin (ARM G):
  question answered: is grid P&L oscillation harvest or level-placement luck/drift?
  population: same anchors, same spacing, opposite direction logic; DISJOINT fills (a bar
    that fills a buy at A−g in the MR grid fills a sell there in the inverted grid).      # B-1
  bite/MDE: under VR<1, theory: MR grid ≈ +f(g,σ,VR), inverted ≈ −f − costs; the SPREAD
    between twins is 2f — twice as detectable as either alone; MDE from month-episode
    bootstrap (~44 episodes/cell).                                                        # B-5
  non-vacuity: direction inversion flips the sign of the crossing-harvest component while
    preserving costs and level geometry — moves the mean directly.                        # B-6
  expected if H true: MR grid > 0 > inverted on MR block; both ≈ −costs on RW block.
  expected if H false: twins symmetric around −costs everywhere.
  disclosure: twin asymmetry + collapse fraction per stratum.                             # B-2
CONTROL RW-block (mechanism negative control, both arms):
  question answered: does the structure fabricate P&L absent the claimed substrate?
  population: 7 VR≈1 instruments — disjoint substrate, same structures.                   # B-1
  bite: EXP-019 measured the VR separation directly (0.76–0.92 vs ≈1).
  expected if H true: ≈ −costs. A CI-positive RW-block cell = artifact alarm → fill
    forensics before ANY MR-block claim is booked.                                        # B-2/B-6
```

## 7. Leak tripwires + integrity gates (HARD)

```
TRIPWIRE 1 — entry-delay +1 (both arms, NZDUSD + USDCAD): all decisions delayed one bar.
  A genuine 6–48-bar-horizon oscillation harvest degrades gracefully (<~20%); a collapse
  ⇒ the edge lived at the fill seam (microstructure/limit-race artifact) → REJECT-class.
  vacuity check: delay shifts every trade's timing — directly moves realized crossing P&L.
TRIPWIRE 2 — param provenance: QA reruns derive_exp020_params.py against EXP-019
  artifacts; byte-diff conf values. Any diff = data-dependent tuning = REJECT.
TRIPWIRE 3 — fill causality (ARM G): every fill at a resting level must satisfy
  m1 High/Low touch; fills never early vs order placement bar.
HARD: tripwires; holdout; estimand_validation blocking_pass per run root; TEST fence.
INFORMATIVE: all premiums, contrasts, cost reads — operator judges.
```

**Carried blocker (cost pin).** Spread snapshot 2026-07-05 03:24 is CLOSED-MARKET
(weekend-widened; EURUSD 2.19 bps vs ~0.2 live typical; EURJPY missing). Binding net reads
use a LIVE-session re-snapshot (operator, Monday); the weekend table is the predeclared
STRESS ceiling (replaces the 2× column for spread). Commissions already pinned (FTMO
2026-07-04: FX $5/lot ≈ 0.47–1.04 bps RT; XAUUSD 0.28; BTCUSD 13.0; indices 0).
`xen.evaluation` raises on unpinned live spread — no silent NaN/zero.

## 8. Power statement

```
POWER: per instrument TRAIN ≈ 4,900 4h bars ≈ 44 month-episodes.
  ARM R: premium on ~4,900 paired bars; block bootstrap (block ≈ 60 bars);
    MDE ≈ 0.4–1.2 bps/bar-equivalent — theory premium for NZDUSD-class σ,VR ≈ 0.5–2 bps/bar
    gross: detection plausible but not guaranteed → low-cadence cells listed below.
  ARM G: ~4–15 round-trips/month expected (g=σ_12); 44 episodes/cell; RT-level MDE
    ≈ 3–8 bps/RT vs harvest-per-RT = g ≈ 30–60 bps gross — well powered on fills;
    episode-level (incl. MTM) MDE wider, disclosed per cell.
strata predeclared UNPOWERED-risk: any cell with implied crossings < 4/month (computed at
  param-derivation time, listed in the conf notes before execution); such cells are never
  read as negatives. RW-block cells are controls, not negative-evidence strata.
```

## 9. Interpretation bands (per instrument, per arm — no binaries)

```
BANDS:
  SUPPORTED:     MR-block stratum premium/RT net > 0 with ci_low > 0 at pinned live costs
                 AND RW-block same-arm ≈ −costs AND inverted twin sign-flipped (ARM G)
                 AND 2022-attribution clean (no single year > 60% of net; no top-5-episode
                 > 60% funding — the EXP-018 carry lesson).
  WASH:          |premium| < MDE — A≈B, reported with absolute sizes.
  CONTRADICTED:  ci_high < 0 at zero-spread gross (structure loses even free).
  ARTIFACT_ALARM: any RW-block CI-positive cell, or tripwire trip → forensics, no claims.
  UNPOWERED:     per §8; excluded from negatives.
POOLED: block-level (MR vs RW) figures are the headline CONTRAST but per-instrument rows
  are the binding reads; cross-block pooling disclosure-only.
```

## 10. Golden-trace spec (QA computes; developer never generates)

```
GOLDEN-TRACE:
  T1 (ARM R, NZDUSD): first rebalance trigger — QA hand-computes w drift from emitted bars
     (start 50/50), identifies first bar where |w−0.5| ≥ b_w, expects market trade at next
     open restoring w*, trade size = drift amount.
  T2 (ARM G, USDCAD): first month anchor A = prior-month close (from bar data); first
     buy-limit fill at A−g (k=1) — expects m1 Low ≤ A−g at fill bar, then a resting unwind
     sell at A−(k−1)·g = A per §3; paired exit fill when m1 High ≥ A; round trip books
     +g − costs.
  T3 (ARM G cap): densest cluster month — 9th would-be fill at cap 8 → order NOT placed,
     cap event logged.
```

## 11. Execution plan

1. `derive_exp020_params.py` (committed, reads EXP-019 artifacts only) → per-instrument
   b, g + implied-cadence table appended to this design as A1 before implementation.
2. Developer: 2 C# models + twins/flags + 64 confs + 4 delay-twin confs.
3. QA fresh context: declarations, param byte-diff, golden traces, exit-set diff.
4. Operator execution gate → 68 runs.
5. Estimand gate per root (blocking) → data-analyst (premium/contrast/cost reads;
   evidence FOR+AGAINST) → operator verdict → documenter.

## A1 — Amendment (2026-07-05): derived parameters (§4/§11.1 executed)

`code/derive_exp020_params.py` run against EXP-019 result artifacts only
(`legs_live.parquet` H=12 gross |NetBps|, `costs.csv`); output
`results/exp020_params.csv` + `exp020_params_summary.json`; **byte-reproducible verified**
(rerun diff clean — tripwire 2 baseline). Weekend spread constants pinned in-script with
provenance (2026-07-05 03:24 snapshot, STRESS CEILING only).

| symbol | block | σ12=g (bps) | b_price (bps) | b_w | crossings/mo | weekend spread (bps) | comm x1 (bps) | stress net/RT (bps) |
|---|---|---|---|---|---|---|---|---|
| NZDUSD | MR | 60.64 | 30.32 | 0.001516 | 22.2 | 4.20 | 0.48 | +55.95 |
| AUDUSD | MR | 59.46 | 29.73 | 0.001487 | 23.1 | 5.33 | 0.44 | +53.69 |
| GBPUSD | MR | 44.61 | 22.30 | 0.001115 | 29.5 | 2.02 | 0.24 | +42.35 |
| USDCAD | MR | 36.08 | 18.04 | 0.000902 | 25.0 | 6.97 | 0.31 | +28.80 |
| EURUSD | mid | 37.84 | 18.92 | 0.000946 | 29.0 | 2.19 | 0.28 | +35.38 |
| USDJPY | RW | 46.45 | 23.23 | 0.001161 | 32.7 | 1.49 | 0.36 | +44.61 |
| USDCHF | RW | 42.07 | 21.03 | 0.001052 | 26.9 | 8.21 | 0.30 | +33.56 |
| EURJPY | RW | 44.57 | 22.28 | 0.001114 | 30.2 | UNPINNED | 0.34 | n/a |
| AUDJPY | RW | 57.40 | 28.70 | 0.001435 | 27.4 | 7.15 | 0.52 | +49.73 |
| GBPJPY | RW | 49.27 | 24.64 | 0.001232 | 30.9 | 3.85 | 0.29 | +45.12 |
| XAUUSD | RW | 75.39 | 37.69 | 0.001885 | 25.4 | 1.10 | 0.14 | +74.15 |
| BTCUSD | RW | 261.33 | 130.67 | 0.006533 | 38.0 | 0.16 | 6.50 | +254.67 |
| USTEC | mid | 118.51 | 59.25 | 0.002963 | 26.8 | 0.49 | 0 | +118.02 |
| US500 | mid | 85.97 | 42.98 | 0.002149 | 27.4 | 0.73 | 0 | +85.23 |
| US2000 | mid | 127.27 | 63.64 | 0.003182 | 24.8 | 3.13 | 0 | +124.14 |
| JP225 | mid | 101.88 | 50.94 | 0.002547 | 26.3 | 1.44 | 0 | +100.44 |

- Implied cadence: quadratic-variation traversal approx, `(bars/mo ÷ 12)·(rms12/median12)²`,
  bars/mo = 4900/44 uniform (design §8); informative only.
- **UNPOWERED-risk cells (<4 crossings/mo): NONE** (min 22.2).
- **Paper stress kill check: NOT triggered** — all MR-block cells clear the weekend-ceiling
  RT cost by 28.8–55.9 bps gross-per-RT margin. Note: gross harvest/RT ≈ g by construction;
  the real question (fills materialising at implied cadence net of trend inventory) is the
  experiment. No early exit.
- EURJPY spread UNPINNED (absent from snapshot) — no stress or binding net read until
  live-session pin; `xen.evaluation` raises by design.

**Predeclared honest prior:** MODERATE-LOW. Oscillation is real (measured), the structure
channel is mathematically sound, but live FX spread may consume g-sized harvests; the
weekend-ceiling stress read may already kill some cells on paper at step 1 — that is a
legitimate early exit (family kill criterion applies at checkpoint-008 retrospective).
