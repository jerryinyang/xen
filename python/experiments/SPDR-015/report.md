# SPDR-015 — Report (Group 2 conditioner science)

- **Family:** `CF-VOLDIR-001` · **Hypothesis:** `CF-VOLDIR-001/HYP-D2` · **Checkpoint:** 017
- **Lane:** SPDR TRAIN-only · 0 TEST reads · global holdout sealed
- **Disposition (operator-signed 2026-07-24):** **WORTH_EXPLORING (per-arm)** — conditioner science
  for experiments 014/016; **not** a standalone trade. Fold in by amendment only; no family status
  change; no XENA.

## 1. Question + mechanism

Two direction-agnostic conditioner arms (O3 Group 2):
- **2a** — after defining volatility states on the vol **level** (not a single-bar return), can the
  **next state / transition** be predicted **better than persistence** ("just stay put")?
- **2b** — can we predict whether the **next ZigZag swing is larger** than the current one (or the
  last-K median), with useful hit rate / calibration — magnitude only, no direction?

## 2. Scope + integrity

- TRAIN band only (`[2021-06-29, 2023-12-18)`); top-25 universe pin (recompute == pin).
- H1 primary, H4 co-report; D1 stickiness disclosure only. Warm-up ≥60 H1 bars.
- Causal by construction: HMM fit window ends strictly before the scored origin; ZigZag features
  known at swing confirmation. No tradability/money claim (spread cost UNAVAILABLE_NOT_CHARGED).
- **Integrity: PASS** — `integrity_selfcheck.json` `hard_pass=true`; golden traces G1–G4 all pass;
  shock (R-SHOCK) never reported as a regime; Δ-vs-persistence headline emitted (600 rows).
- **QA:** run 1 REVISE (control + CI machinery) → fixes → run 2 **APPROVE** (`qa-review.md`).

## 3. Key evidence (per-stratum; magnitudes from `analysis.md`)

Metric for 2a = **Δ Brier vs persistence** (prediction error; negative = better). Full per-stratum
tables: `results/transition_metrics.parquet`, `results/ordinal_metrics.parquet`,
`results/per_stratum_2a.parquet`, `results/per_stratum_2b.parquet`.

### Arm 2a — vol level-state + transitions (H1)
| Horizon | Lazy (persistence) error | Gate error | Improvement | Coverage |
|---|---|---|---|---|
| k=1 (1h) | 0.060 | 0.056 | ~6% less error — **thin** | 13/16 coins |
| k=4 (4h) | 0.164 | 0.132 | ~15% less error | 16/16 coins |
| k=12 (12h) | 0.341 | 0.225 | ~33% less error | 16/16 coins |

- Multi-bar (k=4/12) gate beats persistence on **all 16 powered coins**, CI excludes zero
  (e.g. BTC k=12 Δ −0.103, CI-high −0.080). At k=12 persistence is *worse than a coin-flip*
  (0.341 > 0.25); the gate beats both.
- The vol-**HMM** does **not** beat persistence one bar ahead (~98% stickiness) but is the better
  **state label**: next-|oo| gap HIGH−LOW **+35 bps** (HMM) vs **+16 bps** (R-MARKOV).
  Units: next-bar open-to-open |return| in bps (H1).
- Caveat (disclosed): on very sticky cells the CI does not always sit atop the point estimate (rare
  flip days dominate); the SUPPORTED rule needs both on the right side, so stamps are conservative.

### Arm 2b — ordinal next-swing magnitude (H1; ZigZag 2.0×ATR(14) Wilder)
- **T-GT-CUR** ("bigger than current swing"): **SUPPORTED on all 21 powered coins × 3 models**;
  hit ~**+20 points over each coin's base rate** (BTC +15, ETH +16, SOL +21), size-rank IC ≈ 0.37
  (matches SPDR-013), CIs clear on both hit and Brier legs.
- **T-GT-MED5**: weaker, mostly supported. **T-GT-MED10**: secondary/INCONCLUSIVE.

### Control (LABEL-SHUFFLE, both arms)
True L-28 zero-fixed-point derangement, 200-seed battery, run on 372 (2a) + 189 (2b) powered cells:
skill **collapses** when labels are scrambled (collapse fraction ≈ 0 on every 2a cell, median 2b
cell), and a +0.05 planted edge is detected on ~98% (2a) / ~73% (2b) of cells — the SUPPORTED
cells carry real structure, not label alignment. `results/label_derange_collapse.parquet`.

## 4. Operator disposition (verbatim, per-arm — 2026-07-24)

- **2b ordinal swing-size gate (T-GT-CUR)** → **WORTH_EXPLORING** (primary hand-off).
- **2b T-GT-MED5** → WORTH_EXPLORING (weaker); **T-GT-MED10** → INCONCLUSIVE.
- **2a R-MARKOV multi-bar level gate (k=4/12)** and **HIGH/LOW vol-state labels** → **WORTH_EXPLORING**.
- **2a k=1 next-bar** (R-MARKOV thin; H4 k=1; R-HMM-RV forecast) → **NOT_WORTH**; R-SHOCK stays a
  named comparator only.
- Net: accept the hand-off for the swing-size gate + vol level-state labels/multi-bar gate into
  014/016 gates/labels **by written amendment only**. Do **not** carry a bar-to-bar regime-flip
  timer as proven. Conditioner science, not a trade. Analyst recommendation = operator sign-off
  (no divergence).

## 5. Hand-off fields (for amendment into 014/016)

- Recommended vol-state **gate** = **R-MARKOV** for multi-bar (k=4/12) forecasting; use the
  **HMM HIGH/LOW label** where separating next-move *size* matters (larger gap).
- Recommended ordinal **score** = **T-GT-CUR** (ridge/logit heads).
- Do not use next-bar (k=1) vol forecasting as a gate.

## 6. Follow-ups (separate work)

- Score the design's **CONFIRM verify slice** separately before any graduation (carried MINOR from
  QA; not integrity-fatal, fence intact).
- Amendment into SPDR-014 re-run and/or SPDR-016 (conditioner gates/labels) — new registered work.

## 7. Registry disposition

Evidence rows only (no family status change): `docs/signal-registry/candidate-families/cf-voldir-001.md`
(§3 D2 row + registration ledger 2026-07-24). Family `CF-VOLDIR-001` remains `REGISTERED`.
No counted TEST read; nothing entered in `test-read-ledger.md`.

## Links
`design.md` · `qa-review.md` (run 1 REVISE → run 2 APPROVE) · `analysis.md` · `screen.md` ·
`screen_code/` · `analysis_code/` · `results/`
