# EXP-025 — CF-HTFDI-001/HYP-A Graduation: HTF-DI-Confirmed Breakout, 22-Symbol 1h/5min (Phase 011)

**Family:** CF-HTFDI-001 (`docs/signal-registry/candidate-families/cf-htfdi-001.md`, §Phase 011 graduation scope).
**Registry:** Chapter 02 · Phase 010 batch, `CF-HTFDI-001/HYP-A` row → EXP-025. **Designer:** quant-designer, 2026-07-08.
**Lane:** full cTrader-primary pipeline (design → fresh-context QA → engine → estimand gate → analyst → operator verdict).
**Prior evidence:** SPDR-001/002/003 corrected synthesis (checkpoint 2026-07-08-010, binding). Screen only — no tradability claim carried.

## 1. Question + mechanism

**One falsifiable question.** Does a CTRL-02 momentum breakout gated by last-closed HTF-DI agreement carry a net-of-commission, per-trade directional edge on any instrument of the 22-symbol loaded universe at 1h/5min — confirmed on a counted TEST read under per-instrument max-stat over holds + Holm across instruments read — with the vol-regime interaction measured as an amplifier?

```
MECHANISM: The last CLOSED 1h bar's Wilder ±DI direction conditions the sign of the 5min
forward return (continuation). The effect is magnitude-weighted — HTF alignment puts the
position on the side of the larger forward moves over 12–48 LTF bars — not a hit-rate bias
(screen |hit−0.5| ≤ 0.05). Event cadence: LTF close beyond the last-X HH/LL agreeing with HTF
DI (dense: ~10–30% of 5min bars pre-gate). P&L-bearing object: the individual non-overlapping
TRADE (one position at a time; entry next-bar-open after the confirmed signal bar; open-to-open).
Established stratum: USTEC 1h/5min, dir_gap +0.09→+0.50 ATR, replicated on two blind bases.
DERIVED: estimand = per-trade net open-to-open return (bps primary; fixed-window-ATR units as
disclosure)  null = 25-seed matched-cadence random-direction battery (distributional read: candidate vs
battery mean in seed-SD units; percentile rank disclosed) +
random-entry reference arm dir_gap  horizon = H ∈ {12,24,36,48} LTF bars (1–4× HTF ratio,
mechanism scale)  test = per-instrument max-|t| over the 4 holds vs a block-resampled null
(block ≥ H) + Holm across instruments read; USTEC one-sided (TRAIN sign prior), others two-sided.
```

Not copy-pasteable to another mechanism: the holds are multiples of the HTF/LTF ratio, the null battery matches the breakout cadence, the reference arm re-measures `dir_gap = E[m|+DI] − E[m|−DI]`, and the exit set includes the mechanism-native HTF-DI-flip exit. (L-13 satisfied.)

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — the engine-filled non-overlapping trade (entry at
    next 5min bar open after the signal close; exit per exit-object; open-to-open). Estimand is
    per-leg from xen.adjudication; 1 leg == 1 episode == 1 trade (no pyramiding).        # B-8/L-16
  measured conditioning event == traded entry event: YES — capital commits at Open(t+1) after
    bar t closes beyond the X-bar HH/LL with HTF-DI agreement; the conditioning is measured on
    exactly that (signal-close + last-closed-HTF-state) event, not a touch/intrabar proxy.  # B-4
  effect-splitting windows non-overlapping: YES — trades are non-overlapping by construction
    (one position at a time per run); any per-bar diagnostic uses block ≥ H CIs.            # B-9
```

## 3. Vehicle (fixed first-branch definitions)

| Element | Definition |
|---|---|
| LTF signal (CTRL-02) | at 5min bar `t` close: `Close[t] > max(High[t−X..t−1])` → long candidate; `Close[t] < min(Low[t−X..t−1])` → short candidate. Confirmed bars only; act at `Open(t+1)` (market). |
| HTF gate | trade taken iff candidate side matches last-closed 1h DI: long iff `+DI > −DI`, short iff `+DI < −DI`. **HTF state = most recent 1h bar with `CloseTime < Open(t+1)`** — never the forming HTF bar. Code-asserted + golden-trace (load-bearing leak guard). |
| HTF indicators | Wilder ADX/±DI/ATR, period 14, on 1h (frozen — screen provenance). Warmup: no signal until ≥ 28 closed 1h bars. |
| Lookback grid | **X ∈ {2, 3, 4, 5, 8}** (predeclared final; placeholder adopted). |
| Holds (benchmark exit) | H ∈ {12, 24, 36, 48} 5min bars from entry; exit at bar open (fixed-hold). |
| Variants | `di` (primary) + `atrL_di`/`atrM_di`/`atrH_di` — **analysis-side strata** of the same `di` trade stream, keyed by the ATR regime emitted per trade (below). The amplifier is measured as a conditional effect (constraint 1), not run as separate vehicles. |
| ATR regime | last-closed 1h ATR(14) vs terciles of its own trailing 2,016 closed 1h bars (~12 wk); causal, deterministic; `UNSET` until window full (excluded from ATR strata, included in `di`). |
| Position | fixed 1-unit notional; one position per run; signals during an open position ignored. No sizing lever (P-02). |
| Universe | 22 loaded symbols: EURUSD GBPUSD USDJPY USDCHF USDCAD AUDUSD NZDUSD EURJPY GBPJPY AUDJPY · USTEC US500 US2000 JP225 AUS200 US30 STOXX50 DE40 HK50 UK100 · XAUUSD BTCUSD (all VAL-005/VAL-007 admitted). Justification: operator-directed scope — SPDR qualified the idea, not the instruments; the experiment selects instruments under the multiplicity structure of §8. |
| Domain | 1h/5min ONLY. 1d/1h deferred; 4h/1h stays NOT SUPPORTED. |
| Engine | C# `ISignalModel` (StrategyHost), `tools/ctrader-cli/experiments/EXP-025*.conf`, m1 backtest data, `AnalysisEndUtc` fence at the 70% analysis cutoff per symbol. Costless engine; costs analyst-injected (§10). |

### Exit-method candidate set (6 + benchmark) — cTrader fitness review

All exits decide on closed bars and act at next 5min bar open, except stop orders (native engine stop, m1 fill). Each capping exit measures its **erosion** vs the same cell's fixed-hold benchmark (constraint 2).

| ID | Exit | Predeclared config | Fitness note | Capping? |
|---|---|---|---|---|
| E0 | Fixed-hold (benchmark) | H ∈ {12,24,36,48} | trivial | no |
| E1 | Triple-barrier | TP 3.0× / SL 1.5× entry-frozen HTF ATR(14); time backstop 96 bars | native stop+limit orders, m1 fills (never StrategyHost OHLC self-fill — L: native-orders) | **yes (TP)** |
| E2 | Trailing last-X HH/LL | trail lookback = entry X; close-confirmed breach → exit next open | KB global-technique; close-confirmed keeps it causal | no |
| E3 | Heiken-Ashi trailing | exit when LTF Close crosses `min(HAOpen,HAClose)` (long) / `max` (short) of last closed HA bar | HA for decision only; P&L on real prices | no |
| E4 | Adverse-excursion stop only | SL 1.5× entry-frozen HTF ATR(14), native stop; time backstop 96 bars | motivated by tail-eaten base finding; uncapped upside | no (SL only) |
| E5 | HTF-DI-flip | exit next LTF open after the last-closed 1h bar's DI direction flips | mechanism-native, horizon-free, uncapped | no |
| E6 | Opposite-breakout (DI-gated) | exit next open when the opposite X-breakout signal fires AND the HTF-DI gate admits the opposite direction (+DI<−DI for a long's short-breakout exit; mirror short) — i.e. the full §1 gated event, not the raw breakout | reversal-symmetric; may double as reverse entry — NOT here (exit only). **Amended 2026-07-08 (operator, QA Issue 4/D3):** original raw-breakout reading is predicate-identical to E2; gated reading restores a distinct exit | no |

## 4. Estimand

- **Primary:** per-trade net open-to-open return, bps of entry price, from `xen.adjudication` per-leg objects (1 leg = 1 episode). Reconciliation invariant must hold on the emission; `python -m xen.estimand_validation` blocking gate before ANY read.
- **Units discipline:** bps primary. ATR-normalised figures use a **fixed per-instrument TRAIN-median 1h ATR(14)** divisor (disclosure only). Never ATR[t−1] normalisation for dispersion claims (constraint 4).
- **Reference-arm estimand:** `dir_gap = E[m|+DI] − E[m|−DI]` on the random-entry arm's forward returns (the null-base reference implementation of the hypothesis).
- No accounting primitives in the experiment dir (`check_no_local_accounting`).

## 5. Protocol — staged TRAIN selection, WF-EXPANDING, counted TEST

Emission covers the full analysis window (first 70%); **TEST rows (last 30% of analysis) are quarantined** — no analyst contact until a counted read is approved per §8. Global final-30% holdout never loaded.

- **Stage T1 (TRAIN, benchmark exits).** Engine runs: 22 instruments × 5 X × 4 H = **440 runs** (`di` gate; ATR regime emitted per trade). Per-stratum reads on TRAIN only.
- **Stage T2 (TRAIN, exit methods).** Only on T1 survivors (instrument × X plateau, §7): 6 exits × survivors (expected ≤ 10 instrument-cells) ≈ **≤ 60 runs**. Fixed-hold is the benchmark; capping-exit erosion reported per cell.
- **WF-EXPANDING folds (analysis-side, inside TRAIN).** TRAIN split chronologically 60/20/20: F0 (selection), F1, F2 (expanding validation). Selection statistics computed on F0; SEL-NEIGHBOR qualification requires the F1 and F2 reads (§7). Folds are time-splits of the emitted TRAIN trades — no engine re-runs, no parameter re-fit. TEST is never a fold.
- **TEST confirmation.** One vehicle per qualifying instrument (X*, exit*, `di`; holds all 4 for max-stat) read ONCE on the TEST band as a **counted read** (ledger, cap 2/stratum; stratum = instrument × 1h/5min). Pre-read requires passing `estimand_validation.json` for the emission (pipeline gate 3).

## 6. Controls (named, pre-registered seeds) + tripwire

```
CONTROL CTRL-RND-BATTERY (25-seed matched-cadence random-direction battery):
  question answered: does the candidate's per-trade net exceed what its cadence/hold/instrument
    earns with no directional information? (availability benchmark, Control-B role)
  population: same entry TIMESTAMPS as the candidate cell, direction ~ Bernoulli(0.5), seeds
    1001–1025 (pre-registered); regenerable from seed + bar calendar, byte-diff at QA.
    DISJOINT: direction is independent of DI — the only channel under test.            # B-1
  bite/MDE: battery seed-SD per stratum is the MDE yardstick; a synthetic plant of Δ = 2× the
    declared MDE on one seed must clear the detection threshold before any verdict read
    (recovery ≈98% for a healthy apparatus). Amended 2026-07-08 pre-measurement: a plant AT
    the MDE clears its own threshold only ~50% by definition — single-seed coin-flip gate,
    the L-19 fragility inside the apparatus check itself.
  non-vacuity: randomising direction zeroes Cov(htf_dir, m) — the exact sufficient statistic
    of the mean-based estimand.                                                          # B-6
  expected if H true: candidate exceeds the battery mean by ≥ 2 seed-SD (distributional read —
    with 25 seeds a percentile threshold ≥ 97.5 degenerates into a beat-all-seeds order
    statistic, single-lucky-seed fragile; amended 2026-07-08 pre-measurement). If false: inside
    battery.
  disclosure: candidate percentile rank + battery mean/SD per stratum (L-19: rank read, never
    a single-twin diff).
CONTROL CTRL-REF-RANDOM (random-entry reference arm):
  question answered: does the HTF conditioning effect (dir_gap) exist on TEST free of the
    breakout-base confound? (the null-base estimand is the hypothesis's reference form)
  population: random-timing entries (seed 2001, matched count per instrument), forward
    returns at H ∈ {12,24,36,48}; dir_gap conditioned on last-closed HTF DI.
    DISJOINT: entries carry no breakout information; only the HTF state is shared.
  bite/MDE: screen effect +0.09→+0.50 ATR vs MDE ≈ 2·SD/√n at realised n (reported per hold).
  non-vacuity: measures the covariance channel directly.
  expected if H true: dir_gap > 0 on USTEC, CI-clear at block ≥ H. If false: ≈ 0.
  disclosure: dir_gap + CI per hold, TRAIN and (at the counted read) TEST.
CONTROL CTRL-NULLSENT (null sentinel):
  question answered: does the TEST-side machinery report null where TRAIN established null?
  population: symmetric-sign gating with NO DI — ADX-only (gate: ADX > median) — behaved null
    on TRAIN screen. DISJOINT: no directional information by construction.
  bite/MDE: n matched to candidate cells.
  non-vacuity: any systematic non-zero here indicates apparatus bias, not signal.
  expected if H true OR false: ≈ 0. Judged FAMILY-WISE, never per stratum (amended 2026-07-08
    pre-measurement): with ~88 sentinel strata at 5% per-stratum false-positive rate, ≥1
    nominal CI breach is near-certain (~99%) under a healthy machine. Investigation triggers
    only if the COUNT of CI-clear sentinel strata exceeds the binomial 95th percentile at
    p=0.05×N (or the sentinel max-stat clears its own block-resampled null).
  disclosure: sentinel net + CI per stratum + family-wise breach count vs expectation.
TRIPWIRE (hard, blocking; criterion quantified 2026-07-08 pre-measurement): HTF phase-shift —
  roll the 1h DI/ATR stream by +60 closed 1h bars (misaligned context, cadence preserved).
  Vacuity check: the shift breaks the htf_dir↔m alignment causally — it moves Cov(htf_dir,m),
  the sufficient statistic (NOT a P&L permutation, which is mean-invariant — L: permutation-
  destroy).
  BLOCKING CRITERION (pooled, not per-cell): pool the shifted-vs-raw contrast across all read
  cells of an instrument. REJECT iff the pooled shifted effect exceeds 50% of the pooled raw
  effect AND its CI excludes the ≤25% region. Rationale: a genuine lookahead leak survives the
  shift at ~100%; a real slow-context edge retains a small nonzero residual because 1h Wilder
  DI is autocorrelated over tens of bars and a +60-bar shift does not fully decorrelate it in
  persistent regimes — and per-cell "any nominal CI-clear survivor ⇒ REJECT" would spuriously
  trip ≈40% of the time over ~20+ shifted cells (order-statistic trap in the disqualifying
  direction). Per-cell collapse fractions (shifted/raw) remain a disclosure (L-15); any
  individual surviving cell is investigated and disclosed, never an automatic REJECT.
```

## 7. Selection: `SEL-NEIGHBOR` (registered component)

Registered in `docs/signal-registry/components/global-techniques.md` + multiplicity registry before measurement (this design's pre-exec action; see §12).

Definition (binding here; amended 2026-07-08 pre-measurement, operator-directed — hostile-neighbour hard veto removed as outlier-fragile): parameter grid axis = X ∈ {2,3,4,5,8} (grid order; ±1 step = adjacent list position; boundary cells have one neighbour). A cell (instrument, X, H) **qualifies** iff:
1. its own F0 statistic clears (net per-trade mean > 0 with block-≥-H bootstrap CI_low > 0), and
2. the **median** of the neighbourhood {X−1, X, X+1} (same instrument, H) F0 net means is > 0, and
3. fold persistence: the F1+F2 **pooled** net mean shares the F0 sign, and neither fold is significantly contradicted (block-≥-H CI_high < 0). (Amended 2026-07-08 pre-measurement: raw per-fold sign agreement on two 20% slivers was a coin-flip-fragile binary gate; pooled sign + no-significant-contradiction keeps the persistence requirement without single-fold noise vetoes.)

Contradicted neighbours (CI_high < 0) are a **disclosure, not a disqualifier**: the analyst lists them per qualifying cell; the operator judges. Rationale: the neighbourhood median already tolerates exactly one outlier (robust smoother); a hard veto on a 1-of-3 sample re-introduces single-cell fragility in the opposite direction. An isolated maximum still fails rule 2 (needs 2 of 3 neighbourhood cells positive).

Tie/edge rules: even-count medians use the lower median (conservative); a 2-cell boundary neighbourhood requires both cells' sign to agree (lower median of 2 = min) — **deliberately stricter than interior**: boundary cells have less plateau evidence, so they get zero outlier tolerance by design. X* per instrument = the qualifying X with the highest **neighbourhood median** (not own value; median not mean — robust to a single outlier); ties → smaller X. Exit* = the T2 exit whose F0 net beats E0's by more than one battery seed-SD, else E0 (benchmark wins ties). Capping-exit **erosion vs E0 is a disclosure, not a selection veto** (amended 2026-07-08 pre-measurement: a TP exit has positive erosion nearly by construction even when net-superior; constraint 2 requires erosion be measured, not gate selection). H is never selected — all 4 holds go to TEST inside the max-stat.

## 8. Multiplicity structure + counted-TEST pre-commitment (the math)

**TRAIN plane (selection, uncounted):** 22 instruments × 5 X × 4 H × 4 variant-strata = 4,400 conditioning cells + ≤ 60 exit cells — priced by walk-forward selection (TRAIN-only) and by the fact that NO TRAIN figure is confirmatory. Registry batch row discloses the plane.

**TEST family (confirmatory, counted):**
- Per instrument read (clarified 2026-07-08 pre-implementation, operator-resolved: holds parametrize only E0, so a horizon-free exit* cannot span them): the confirmatory family is **E0 at 4 holds + the selected exit\* as one additional pre-registered stat** — max over those 5 statistics per instrument (if exit\* = E0, it degenerates to the 4-hold max). Statistic = max of |mean/SE| (SE from block-≥-H circular block bootstrap, 5-seed battery, INFR-004). Null: the same max-stat on the 25-seed battery + block-resampled sign-null → one p per instrument. USTEC one-sided (continuation prior); all others two-sided.
- Across instruments: **Holm at α = 0.05 over the m instruments actually read.**
- **Eligibility to spend a read (ALL required; amended 2026-07-08 pre-measurement):** (i) SEL-NEIGHBOR qualification (§7 — already contains the CI_low > 0 gate; the former separate full-TRAIN-band CI condition was redundant AND-stacking and is dropped); (ii) candidate exceeds the TRAIN battery mean by ≥ 2 seed-SD (distributional read; replaces the ≥ 97.5th-percentile order statistic, which with 25 seeds required beating every seed — single-lucky-seed fragile); (iii) projected TEST n ≥ 50 trades; (iv) passing estimand gate; (v) operator approval per read (pipeline gate 3).
- **Hard cap: ≤ 5 counted TEST reads in this experiment** (5 instruments × 1 read; ledger cap 2/stratum untouched — each stratum retains its second lifetime read). USTEC is read first if eligible. If > 5 instruments qualify, rank by TRAIN neighbourhood-median net and read the top 5; the rest are recorded QUALIFIED-UNREAD (file-drawer row, no read spent).
- Worst-case arithmetic: m = 5 reads → Holm thresholds 0.01/0.0125/0.0167/0.025/0.05. With TEST n ≈ 800–1,500 trades (H48–H12, §9) and per-trade SD ≈ 60–120 bps, the max-stat MDE at Holm-corrected α ≈ 8–18 bps/trade — well below the screen's TRAIN economics for USTEC (+0.26–0.50 ATR ≈ 30–60 bps at TRAIN-median ATR). The plane is priced: 4,400 TRAIN cells buy at most 5 counted confirmations under FWER 0.05.
- The ATR×DI amplifier is measured on the read instruments as a TEST **disclosure** (interaction contrast atrH vs atrL with block-≥-H CI) — never a separate read and never a sign-setter (constraint 1).

## 9. Power statement

```
POWER (TRAIN ≈ 2.47y ≈ 175k 5min bars/instrument (USTEC measured: 175,045; FX ~180k);
       TEST ≈ 75k bars):
  trades/cell (non-overlap ≈ bars/(H+1), DI-gate ≈ halves raw cadence; X=3 raw signal frac 0.32):
    TRAIN E0: H12 ≈ 6–13k · H24 ≈ 3–7k · H36 ≈ 2.5–4.5k · H48 ≈ 1.8–3.5k
    TEST  E0: H12 ≈ 2.5–5.5k · H48 ≈ 0.8–1.5k
  MDE (95% CI excl. 0, per-trade SD 60–120 bps): TRAIN H48 n≈2k → 2.7–5.4 bps;
    TEST H48 n≈1k → 3.8–7.6 bps; TEST H12 n≈3k → 2.2–4.4 bps. Screen effect ≈ 30–60 bps → powered.
  ATR-tercile strata: n/3 → MDE ×√3 — amplifier contrast still powered on dense instruments.
  strata predeclared UNPOWERED: any (cell) with n < 50 trades (expected: none at E0 on the full
    22-symbol set; possible on E5/E6 exits if exit cadence collapses, and on atr-tercile × TEST
    sub-strata for low-coverage symbols e.g. HK50/JP225 session gaps). UNPOWERED cells are never
    read as negatives (B-5); they are listed by the analyst with their MDEs.
```

## 10. Costs

Engine costless; analyst injects the corrected FTMO commission model (`xen.evaluation`, netted-turnover rule, commit `f4b7bc9` tier): FX 0.5–1.0 bps RT, BTCUSD ~13, indices 0 commission. Binding tier = **net-of-commission**; live spread unpinned → spread-scenario curve (0.5×/1×/2× a disclosed per-symbol spread estimate) as disclosure, never a verdict leg. Cost sensitivity reported per stratum.

## 11. Interpretation bands (per stratum; informative — operator judges)

```
BANDS (per instrument read, TEST):
  SUPPORTED:    Holm-adjusted max-stat p < 0.05 AND net-of-commission per-trade mean CI_low > 0
                (block ≥ H, 5-seed battery; sign-stable = CI_low > 0 retained across the
                registered INFR-004 block sweep — this definition is binding, no stricter
                analyst reading) AND candidate > battery mean by ≥ 2 seed-SD AND pooled
                tripwire collapse confirmed (§6 quantified criterion).
  WASH:         |net| < 1 battery seed-SD → report A≈B with absolute effect sizes (L-11).
  CONTRADICTED: CI_high < 0 at the selected vehicle (two-sided instruments only; for USTEC a
                CI_high < 0 additionally triggers a sign-prior review note, not a silent flip).
  UNPOWERED:    n < 50 or MDE > TRAIN point effect — excluded from negatives.
POOLED: any cross-instrument aggregate is disclosure-only (L-03). Exit-erosion, amplifier
  interaction, cost curves, collapse fractions: all disclosures with CIs, no thresholds.
```

## 12. Pre-execution actions (before QA)

1. `SEL-NEIGHBOR` registered in `global-techniques.md` + multiplicity-registry Phase-010 batch (DONE with this design — 0 slots, 0 reads).
2. Registry batch row updated: EXP-025 assigned to `CF-HTFDI-001/HYP-A` (evidence row only; no status transition).
3. Control seeds frozen in this file (battery 1001–1025; reference arm 2001). QA verifies regenerability byte-diff.
4. Developer implements `HtfDiBreakoutModel` + confs; **no Python analysis in `code/`**.

## 13. Golden trace (QA diffs vs emission; designer-derived, developer must NOT generate)

Derivation: USTEC m1 file `timebars_ustec_20210602_000000_20260621_190833.parquet`, TRAIN = first 70%×70% (m1 rows → 2021-06-02 00:01 → 2023-11-20 23:15 UTC), clock-aligned 5min/1h resample on OpenTime, Wilder DI(14) on 1h, X = 3. Price tolerance ±0.1 index points; timestamp exact.

| # | Signal bar Open (UTC) | Side | LTF Close vs ref | HTF bar used (Open / CloseTime) | +DI / −DI | Expected entry (bar open / px) |
|---|---|---|---|---|---|---|
| 1 | 2021-07-01 00:05 | short | 14562.8 < LL₃ 14563.1 | 2021-06-30 23:00 / 2021-07-01 00:00 | 16.241 / 19.002 | 2021-07-01 00:10 @ 14562.9 |
| 2 | 2021-07-01 01:15 | long | 14583.3 > HH₃ 14581.6 | 2021-07-01 00:00 / 01:00 | 18.867 / 17.914 | 2021-07-01 01:20 @ 14583.2 |
| 3 | 2021-07-01 01:55 | long | 14579.9 > HH₃ 14578.4 | 2021-07-01 00:00 / 01:00 | 18.867 / 17.914 | 2021-07-01 02:00 @ 14580.0±0.1 |

Each event also pins the leak guard: the HTF bar's CloseTime strictly precedes the entry bar's Open; QA must verify the emission's per-trade HTF-state columns match these values and that no trade anywhere uses an HTF bar with `CloseTime ≥ entry Open`.

## 14. Integrity vs informative split

```
HARD (block): phase-shift tripwire collapse (pooled quantified criterion, §6 — never a
  per-cell survivor read); holdout fence (AnalysisEndUtc; final-30% never
  loaded); TEST quarantine until an approved counted read; causal provenance (HTF CloseTime <
  entry Open; decisions on closed bars; open-to-open returns); estimand reconciliation gate;
  battery/reference-arm seed regenerability.
INFORMATIVE (operator judges): every effect size, max-stat/Holm read, battery percentile,
  amplifier interaction, exit erosion, cost curve, collapse fraction. No auto-verdicts.
```

## 15. Complexity budget & exclusions

- Engine runs: 440 (T1) + ≤ 60 (T2) + 25-seed battery on read-eligible cells (≤ 5 × 25 = 125) + reference arm (22) + sentinel (22) ≈ **≤ 670 runs**, `run-experiment.sh parallel` bounded 4 + 10s stagger (EXP-020 infra rule).
- Stat families 4 (per-trade CI; max-stat+Holm; battery percentile; interaction/erosion contrasts). Plot classes ≤ 6. New modules: 1 C# model; 1 analysis-side SEL-NEIGHBOR selector (analyst's own code).
- **Exclusions:** no 1d/1h; no 4h/1h; no ADX variant axis; no fade priors; no pyramiding/sizing; no exit re-tuning after TEST contact; no scope expansion post-QA (new questions → new EXP).
