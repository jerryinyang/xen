# SPDR-018 — Screen summary (neutral quantification)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Lane:** SPDR · TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Design:** `design.md` (frozen, operator-signed). **No amendments.**
- **Code pin:** `screen_code/` sha256 `44c720f82af52b8b…`
- **Status:** SCREEN COMPLETE — **no disposition taken here**

> **This document is subordinate to `analysis.md`.** It quantifies; it does not adjudicate.
> The binding read is the fresh-context analyst's; the disposition is the operator's, at the
> mid-checkpoint reflection. Nothing below is a verdict, and no cell is described as passing
> or failing anything.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 1. What was run

A **precision experiment**, not a mechanism experiment. Four arms, each re-scoring its parent
screen's own emitted rows under the design §5 power levers — pool across symbols with
σ̂-normalisation, use the full TRAIN span, score CONFIRM explicitly, report effective coverage,
quantify the shortfall. No estimand was re-defined, no conditioner un-nested, no thin symbol
dropped.

| | Cells | At the parent's own target precision |
|---|---|---|
| Arm A — SPDR-012 residue | 3,047 | 1,923 |
| Arm B — SPDR-013 residue | 5,110 | 879 |
| Arm C — SPDR-014 residue | 22,194 | 632 |
| Arm D — SPDR-015 residue | 7,440 | 4,620 |
| **Total** | **37,791** | |
| cTrader replication (separate, never pooled) | 42 | — |

**Residue inventory — every design §2 item carries cells. Nothing was narrowed.**

`A1` 143 · `A2` 372 · `A3` 1,965 · `A4` 432 · `A5` 135 · `B1` 2,044 · `B2` 1,022 · `B3` 830 ·
`B4` 146 · `B5` 2,555 · `C1` 7,181 · `C2` 1,020 · `C3` 6,987 · `C4` 170 · `C5` 3,570 · `C6` 62 ·
`C7` 2,714 · `C8` 340 · `C9` 150 · `D1` 1,800 · `D2` 300 · `D3` 405 · `D4` 405 · `D5` 675 ·
`D6` 900 · `D7` 75 · `D8` 2,534.

Only authorised drop: `SPDR-017` (design §2.1).

**Unit pin (measured at run, never asserted):** σ̂ = LTF H1 Parkinson EWMA(λ=0.94), 60-bar warm-up,
causal ≤ t−1, in bps. Pooled TRAIN median **73.00 bps**, all 25/25 symbols measured
(`results/unit_pin.json`). bps is the primary unit throughout; σ̂-normalisation is used only to
make cross-symbol pooling valid and is never reported as a headline unit.

---

## 2. Power — the question checkpoint-017 asked

Checkpoint-017 closed with the extraction question *unresolved at power*: SPDR-014 produced
**0 powered cells of 927**.

**1,511 signed cells now reach their parent's own declared target precision** — of which
**1,413 carry every term of the `(p, W, L)` decomposition** and are the population all §3 figures
below are measured on. (The 98-cell difference is cells powered on count/date criteria whose
one-sided return distribution leaves `W` or `L` undefined.)

`NOT_RESOLVABLE` — short of target after every §5 lever (pooled, σ̂-normalised, full TRAIN span) —
is reported for **3,559 cells**, each with realised `n`, block MDE, target, the multiple short and
the `n` that would be required (`results/not_resolvable.json`). Concentration: `C3` 1,946,
`C5` 914, `C2` 263, `C1` 105, `C4` 105, `D3` 74, `D4` 63. Median shortfall **7.9×** the target
MDE, p90 **27.3×**.

Per B-5 these are power statements. They are not negatives.

---

## 3. The `(p, W, L)` picture (design §4.1 / SoT §2)

Measured on the 1,413 powered signed cells carrying all terms. **Medians:**

| Term | Value |
|---|---|
| `p` (rate) | 0.3887 |
| `W` (mean win) | 128.6 bps |
| `L` (mean loss) | 75.6 bps |
| `W/L` | 1.484 |
| `p_be` — break-even, **gross** | 0.4025 |
| `p_be_net` — break-even, **net** | 0.4992 |
| gross mean | −1.18 bps |
| net mean | −15.16 bps |
| cost charged | 13.54 bps |

Distributional facts, stated without adjudication:

- `W/L > 1` in **99.9%** of powered cells.
- **32.5%** of powered cells sit above their **gross** break-even; **0.0%** sit above their
  **net** break-even.
- The gap decomposes as: `p_be_net − p_be = +0.0650` (the cost term) against `p_be − p = +0.0067`
  (the rate term).
- `p > 0.5` in 0.5% of powered cells. Per SoT §2.2 and chapter-06 governance §3, no read in this
  screen is phrased against 0.5; the reference is each cell's own `p_be_net`.

**Identity reconstruction** `|p·W − (1−p)·L − mean| < 0.01 bps` holds on **every** signed cell
(max residual ~1e-12 bps), asserted as a HARD check.

---

## 4. Arm-level quantification

### Arm A — SPDR-012 residue

Measurement objects (state-conditional magnitude, forecast skill); no P&L claim, therefore no
`(p, W, L)` layer.

- **A1 V-REGIME-HMM**, pooled full TRAIN, HIGH−LOW next-|move| gap with block CI:
  D1 **+180.4 bps** [119.7, 252.1] · H4 **+67.5** [54.7, 80.6] · H1 **+48.0** [41.7, 54.7].
- Band labels: IC cells 1,366 SUPPORTED / 337 UNPOWERED / 44 WASH / 23 CONTRADICTED;
  gap cells 215 SUPPORTED / 386 WASH / 106 UNPOWERED / 3 CONTRADICTED;
  incremental-R² cells (A4 V-CLOCK) 20 SUPPORTED / 170 WASH / 148 UNPOWERED / 94 CONTRADICTED.
- **A4** co-reports observations-per-date on every cell — the D1 cells run at ~1.0 observation per
  date against 7–9 dummies, which is a statement about the estimator, not the market.
- **A5** reports, per cell, how many of the three calendar thirds contain any scored origin at
  all, and whether the §6.4 clause is satisfiable on that band.

### Arm B — SPDR-013 residue (where `W` and `L` are measured)

- 879 of 5,110 cells at target precision. Band labels (mean): 1,539 CONTRADICTED, 3,346
  UNPOWERED, 148 SUPPORTED, 41 WASH, 36 NOT_RESOLVABLE.
- Largest gross edges are all small and net-negative — e.g. BTCUSDT H1 CONFIRM D-SMA14_angle-on
  signalflip: n 1,013, `p` 0.349 vs `p_be` 0.308 (gross edge +0.041), `W/L` 2.25,
  gross +4.54 bps, net −9.04 bps.
- **B3 note:** the design's "125 positive-mean cells" does not reconcile against SPDR-013's
  published table under any slice (830 grid-wide; 352 DESIGN; 187 DESIGN×H1; 471 H1 both bands).
  The **superset of 830** is tagged so nothing intended is dropped. Raised, not resolved
  (config `IN-4`).

### Arm C — SPDR-014 residue (event-nested, original form)

- 632 of 19,140 signed cells at target precision — against 0 of 927 in the parent.
- Band labels (mean): 2,873 CONTRADICTED, 12,467 UNPOWERED, 3,368 NOT_RESOLVABLE, 261 SUPPORTED,
  21 WASH.
- **C7 (DESIGN→CONFIRM sign flip):** 2,714 symbol-cell pairs; **44.1%** flip sign, and in
  **91.8%** of those the two bands' block CIs overlap.
- **C8 (rate lean):** row-weighted `p_momo` 0.4676 vs symbol-weighted 0.4699 — the two weightings
  agree at this `n`.
- **C9 `DA-STRADDLE`:** 150 cells, 98 at target, median partial-net **−29.1 bps**.
  **Characterisation only** — not a strategy branch, no policy, no graduation path (SoT §0).

### Arm D — SPDR-015 residue (incl. the never-scored CONFIRM slice)

- 4,620 of 5,850 cells at target precision. **D8 carries 2,534 cells** — the slice SPDR-015 never
  scored separately, because it pooled both bands into one number.
- Pooled `T-GT-CUR` hit rate holds on **CONFIRM**: ar1 0.6465 [0.6247, 0.6678], logit 0.6999
  [0.6831, 0.7176], ridge 0.6781 [0.6589, 0.6978], against base rate 0.4674 — matching its DESIGN
  behaviour (0.6637 / 0.6874 / 0.6686 vs base 0.4781).
- `T-GT-MED5` and `T-GT-MED10` are mixed across models and bands (WASH / SUPPORTED), which is the
  D3/D4 open question measured rather than asserted.

---

## 5. cTrader replication — separate, never pooled

EURUSD / XAUUSD / USTEC on the INFR-021 fence (`train_end` 2023-11-22, sha256 `4cdc7b01…`
verified; holdout 2024-12-13 never queried). **Gross only** — no sanctioned cTrader cost table
exists, so `p_be_net` and `edge` are not reported for these cells.

42 cells. Median `p` **0.3531** against median **gross** break-even **0.3559**; median `W/L`
**1.810**; median gross mean **−0.25 bps**. The same geometry as the crypto arms, on a different
asset class, at a different vol scale.

Role: independent replication / credibility only. **Never pooled into `n`** (AMENDMENT-C1,
AMENDMENT-S1).

**Scope limits of the replication — stated explicitly so it is not over-read.** The cTrader arm
covers **arm B's object only**, at **one exit geometry**, **gross only**:

| | Covered |
|---|---|
| Arm B — SPDR-013 episode object (D-ZZ + 6 D-SMA signals) | yes — 42 cells, ~151k episodes |
| Arms A, C, D | **no** — no volatility characterisation, no event-nested residual, no conditioner science |
| Exit geometries | **`signalflip` only** — 1 of the 5 arm-B modes |
| Cost | **gross only**; `p_be_net` and `edge` are not computed for these cells |

Two consequences follow and both are binding on how this arm may be cited:

1. **The `W/L` movability evidence does NOT replicate here.** The 67× range across exit geometries
   is measured on crypto only, because cTrader carries a single geometry. What replicates is the
   *static* mirror relationship at one geometry (log `W/L` vs the driftless mirror `(1−p)/p`:
   R² **0.969** on cTrader against **0.967** on the crypto powered cells).
2. **`C2` shock-conditioned MOMO has no cTrader test at all.** It is an arm-C object, and arm C
   was not built on these instruments. The one live thread in the run is therefore also the one
   with zero external replication.

---

## 6. Controls and tripwires (report layers — no `pass` field anywhere)

- **SIDE-DERANGEMENT** (2,000 seeds, **0 fixed points**): arm B live −1.30 bps at percentile
  0.475; arm C live −12.22 bps at percentile 0.006. Plant curves are monotone and bite —
  arm B {5,10,20,40} bps → {0.695, 0.875, 1.000, 1.000}.
  1 row of 9,694 (0.01%) sits in a singleton symbol×month group and is excluded from the control
  population, disclosed, because a singleton cannot be deranged without leaving a fixed point.
- **MAGNITUDE-MATCHED COMPARATOR (M-3)**, 2,000 seeds, decile-stratified, live rows ±1 bar
  excluded: a genuine disjoint pool existed in every decile for both conditioners.
  `shock_flag` live at percentile **0.95** of its magnitude-matched comparator; `mag_high` at
  **0.46**.
- **AMBIENT-BASE:** per-cell deltas on mean / median / dispersion / `p` / `W` / `L` / `W/L`, each
  with CI, reported as magnitudes.
- **TRIPWIRE-1** (construction assertions) held. **TRIPWIRE-3** (forward-path derangement) is a
  report layer, not the causality claim.
- Collapse fraction is **disclosure only** throughout (M-5).

---

## 7. Standing corrections as measured

- **M-1** — every band label is driven by the **block** MDE (day blocks {1,3,7}, 5 seeds, min/max
  envelope). The iid `2.8σ/√n` form is emitted only as a labelled companion column and is
  asserted in code never to drive a label.
- **M-2** — 18,990 cells carry a horizon; median exact-span fraction **0.906**, and **78.2%** of
  those cells contain at least some rows whose wall-clock span exceeds the nominal `h` hours.
- **M-4** — effective multi-symbol coverage emitted per cell; median 1.000 of nominal on the
  pooled full-TRAIN cells.
- **M-5** — collapse fraction disclosure-only, everywhere.

---

## 8. Integrity (design §12 — all HARD checks held)

**18 HARD checks, 0 failed** (`results/integrity_selfcheck.json`), code pin sha256
`44c720f82af52b8b…`:

TRAIN fence · global holdout · cTrader fence provenance (sha256) · cTrader TRAIN fence · cTrader
holdout · universe pin set-equality · identity reconstruction · M-1 block-MDE provenance ·
no `pass` field / no `at_or_above_pXX` · no local accounting primitive · spread never charged ·
derangement fixed-point count 0 · **TRIPWIRE-1** · **TRIPWIRE-2** · **determinism** ·
**parent parity** · **golden traces G1–G6** · bootstrap speed path bit-identical to
`xen.evaluation.block_bootstrap_ci`.

**CORRECTION (recorded, not hidden).** The first emission of this screen ran only 16 HARD checks:
`TRIPWIRE-2` — declared HARD in design §7.1 and, with TRIPWIRE-1, *the* causality claim — was
implemented but never invoked, and `determinism` was gated behind a CLI flag that the resumed runs
did not pass, so it degraded to INFORMATIVE. An earlier version of §9 below said "Deviations:
none" while both were silently absent. The fresh-context analyst caught both. Both now run
unconditionally and are reported here; this emission is the corrected re-run.

- **TRIPWIRE-2** — legal variant **85.34 bps** vs the deliberately leaky twin **644.71 bps** on
  the same 58 selected rows: a ratio of **7.55×**. Stated plainly: the design's §7.1 language
  anticipated "orders of magnitude" (SPDR-012 measured ~12 on its own analogous contrast); the
  measured separation here is 7.55×, which is material and one-directional but is **not** an
  order-of-magnitude separation. Reported as measured, not rounded up to the design's expectation.
- **Determinism** — 630 cells computed sequentially and with `--jobs 8`: **zero columns differ**.

**Parent parity** (the anti-drift proof that no object was silently re-specified) — each arm
reproduces its parent's published cells on the parent's own band:

| Arm | Parent | Quantity | Max abs diff |
|---|---|---|---|
| A | SPDR-012 | `gap_high_low_bps` (109 cells) | 4.5e-13 |
| B | SPDR-013 | `expectancy_partial`, `n_episodes` (2,940 cells) | 1.8e-12 / 0 |
| C | SPDR-014 | `mean_r_h`, `n_decided` (6,127 cells) | 9.1e-13 / 0 |
| D | SPDR-015 | `hit_rate`, `n_oos` (189 cells) | 0.0 / 0 |

**Golden traces G1–G6** were computed on the self-check side from the fenced catalog and the
parents' own primitives — no expected value is hardcoded and no arm module is imported. G1's HMM
state, G2's first episode, G3's event-nested leg and G5's identity all reproduce the emission
exactly (0.0 or ~1e-14).

---

## 9. Deviations and raised items

**Deviations: none in the design's estimands, objects, bands or controls.** One PROCESS defect
occurred and is recorded above in §8: two HARD checks did not execute in the first emission and
were fixed before this one. Interpretation notes recorded in `screen_code/config.py`:

- `IN-1` — arms import the parents' modules for constants, band rules, seeds, cost constants and
  pure helpers, and re-score the parents' own emitted panels; where a parent never computed a band
  at all (D8), the parent's module is re-run. Parent parity is what makes this verifiable.
- `IN-2` — the three uniform controls run on each arm's designated primary cells; scope emitted.
- `IN-3` — the mean-family bootstrap is vectorised; equality with
  `xen.evaluation.block_bootstrap_ci` asserted at run (|diff| ≤ 2e-14).
- `IN-4` — **raised to the operator:** the design's "125 positive-mean cells" does not reconcile;
  the superset of 830 is used.
- `IN-5` — **raised to the operator:** median and trimmed-mean CIs are bootstrapped on the
  levers-exhausted cells (the ones whose label can turn on them); all three point statistics are
  emitted on every cell, and the mean family carries its CI everywhere.

---

## 10. Artifacts

`results/arm_A.parquet` · `arm_B.parquet` · `arm_C.parquet` · `arm_D.parquet` ·
`metrics_by_cell.parquet` (37,791 cells) · `ctrader_replication.parquet` · `controls.json` ·
`not_resolvable.json` · `unit_pin.json` · `parent_parity.json` · `golden_traces.json` ·
`integrity_selfcheck.json` · `run_summary.json`.

**Next stage:** fresh-context `data-analyst` → `analysis.md` (binding), then the operator
disposition. No tradability, deployability, family-status or graduation claim is made or implied
by this document.
