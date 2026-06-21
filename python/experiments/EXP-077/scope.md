# Experiment: EXP-077 — Dogfood + Calibration under `WF-EXPANDING` (`ASS/VAL-002`)

> **Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation.** G0 PASS 2026-06-20; D0
> predeclarations frozen (`checkpoints/2026-06-20-017-capgeo-qualifier-validation/D0-predeclarations.md`).
> Gated on **EXP-076 G-017a PASS** (RECOVERY_VALIDATED_G017a, 2026-06-20) — satisfied.
> This experiment validates the **error-control + protocol** legs of G-017 (FPR / MDE / `P(>X)`
> reliability **under the expanding-window walk-forward**, plus the counted-read accounting rule).
> **0 candidate slots, 0 counted TEST reads, holdout never touched** (synthetic substrates + a
> current-data **TRAIN-only** dogfood confined to the first-49% region).

## Hypothesis

Under the frozen `WF-EXPANDING` expanding-window walk-forward protocol (D0 §D4), the `ASS` qualifier
controls error and behaves as a usable yardstick:

1. **FPR (D2.2):** on each known-null synthetic type (`U0`; `B_zero` treated as a median/expectancy
   null per its leg) **and** the EXP-076-mandated **small-`n` stratum** (`n < 30`), the false-positive
   edge-call rate under the **margin-calibrated** rule `expectancy CI_low > m` is **≤ 0.05** with
   **Wilson upper-95% ≤ 0.075**, where `m` is the synthetic-null-calibrated margin (the `m_cell`
   analog) measured at production scale (`R_REP ≥ 2000`, `N_BOOT = 10_000`).
2. **MDE (D2.3):** the minimum-detectable-effect `MDE(type, n)` (smallest true `μ` with
   `TPR(expectancy CI_low > 0) ≥ 0.80`) is **finite / non-degenerate** for every `n ≥ 30`; the full
   `MDE(n)` curve is reported (degeneracy, not magnitude, is the gate).
3. **`P(return>X)` reliability (D2.4):** on held-out folds, predicted vs realized frequency bucketed
   into deciles satisfies **max |predicted − realized| ≤ 0.10** **and** calibration-line slope
   **∈ [0.85, 1.15]** for `X ∈ {0, 0.05, 1.0, 2.0}`.
4. **Counted-read accounting (D4.1):** one frozen, pre-declared `WF-EXPANDING` run on a stratum is
   **exactly one** counted TEST read; the individual folds are in-protocol disclosures (no
   between-fold selection); the accounting demonstrably honors the **2-lifetime-counted-reads** cap
   and reverts each fold to a separate counted read when any D4.1 condition fails.
5. **Dogfood (D4.2):** the full `WF-EXPANDING` + `ASS` pipeline runs end-to-end on **real 1-minute
   bars** within the **current first-49% TRAIN region only**, with **moving-block** bootstrap, and
   **never** slices the next-21% TEST stratum or the final-30% holdout — confirming the machinery runs
   on real data with **0 counted TEST reads**.
6. **Determinism (D6):** a second full pass is byte-identical.

**Falsified (feeds G-017 `DISCOVERY_ONLY`)** if any null type's (or the small-`n` stratum's)
margin-calibrated FPR exceeds 0.05, OR any `n ≥ 30` MDE is degenerate/never-detecting, OR `P(>X)`
reliability falls outside the D2.4 band. **`PROTOCOL_DEFECT`** if the `WF-EXPANDING` accounting cannot
honor the 2-read cap OR determinism fails.

## Question

Now that `ASS` recovers known ground truth (EXP-076), does it **control error and stay reliable when
carried by the protocol that will actually adjudicate Phase 018 candidates** — the expanding-window
walk-forward — and is the per-fold counted-read accounting against the 2-read TEST-stratum cap sound
*before* any real TEST contact? And does the whole pipeline actually run on real bars without touching
a single TEST or holdout row?

## Scope Boundaries

- **Data Views**:
  - **Binding validations (FPR / MDE / reliability):** **synthetic return populations only** (D0 §D1,
    reused unchanged from EXP-076). No market data feeds any binding numeric leg. Returns in **ATR
    units** (`R = 1.0 ATR`).
  - **Dogfood smoke (non-binding pipeline check):** the **current** collected 1-minute time bars,
    sliced to the **first 49% of each instrument file** (= the TRAIN region: first 70% of the first-70%
    analysis set). Domains **15m / 1h / 4h** (the CF-CAPGEO-001 family domains), constructed by
    clock-aligned resampling (`xen.bar_aggregator`, `min_coverage=0.90`). The dogfood return series is
    a **developer-defined causal real-price series** (per-event or per-bar forward returns in ATR
    units) carrying **no market-edge claim** — it exists only to prove the pipeline runs on real bars.
- **Parameters (frozen, D0 §D1/§D3/§D4)**:
  - Synthetic null/effect types and `n ∈ {15, 30, 60, 120, 250, 500, 1000, 2000, 8000}`; replicates
    `R_REP = 2000` per `(type, n)`; master seed `20260620`; per-draw seed = deterministic hash of
    `(type_id, n, replicate)` (extended with a fold/stream tag).
  - **`ASS` config (D3):** kNN bandwidth `k_bw = max(5, round(√n))`; shrinkage `weight = n/(n+k)`,
    `k` default = median sample size; bootstrap `N_BOOT = 10_000`, CI = 5th/95th pct. **Synthetic iid
    → simple within-type resample; real-data dogfood → moving-block bootstrap** with
    `b = round(m^(1/3))`. Thresholds `X ∈ {0, 0.05(breakeven), 1.0(1R), 2.0(2R)}`.
  - **`WF-EXPANDING` (D4):** initial train = first **0.50** of the (synthetic or dogfood) series; **5
    expanding folds** of **0.10** each, each tested fold rolled into the next train; min fold size **≥
    30 events** (below-floor folds **disclosed**, not dropped); rolling **1y/2y/3y** comparison
    disclosed (real-data dogfood only); fold-clustered moving-block bootstrap aggregates to **exactly
    one** stratum verdict.
  - **Margin `m` (D2.2):** calibrated on the synthetic nulls at production scale so measured FPR ≤
    0.05 at the realized fold-cluster structure; reported, not hand-set.
- **Instruments**: none for the synthetic legs. Dogfood uses the **4-instrument core**
  (EURUSD, XAUUSD, BTCUSD, USTEC) × {15m, 1h, 4h} — a deliberately small smoke subset (pipeline
  proof, not a universe sweep); justified because the dogfood makes no edge claim and a wider universe
  buys no additional pipeline coverage.
- **Time range**: the dogfood loads and slices **only the first 49% of the full dataset** per file.
  The **next-21% TEST stratum and the final-30% global holdout are never sliced, materialized, or
  inspected.** All synthetic legs touch no dataset at all.
- **Global holdout**: never loaded. The dogfood's lazy slice stops at the first-49% cutoff; the
  holdout (and the TEST stratum) are out of range by construction.
- **Look-ahead bias prevention**: `WF-EXPANDING` is causal — a completed test fold rolling into the
  next train is **historical at the next train time**, not leakage (component spec). Dogfood returns
  use only data at/before each event timestamp; temporal ordering by `CloseTime` (and
  `SourceCloseTime` if any chart-type view is used); moving-block bootstrap preserves serial
  dependence. No bar-index alignment.
- **Real-price outcome discipline**: every dogfood return is computed on **real time-bar prices**
  (`Close` / `RealClose`), ATR-normalised. **No HA or Renko brick prices** anywhere. Synthetic returns
  are ATR-unit by construction (no market prices involved).
- **Exclusions**:
  - **No shape-discrimination / tail diagnostic / `k`-sensitivity sweep** — that is EXP-078.
  - **No candidate screening, no slot, no real TEST/holdout contact.** The counted-read accounting is
    **validated** here (rule correctness + cap arithmetic), **not exercised** against the live ledger
    (that happens in Phase 018 on the post-INFR-003 5-year strata).
  - **No MDE-magnitude gate** — only finiteness/non-degeneracy at `n ≥ 30` is the criterion.
  - **No `k` or `ASS`-parameter tuning** — all frozen at D0.
  - **No EXP-079** (reserved-inactive; opened only if the dogfood shows the protocol needs isolating
    from the qualifier — not this scope).

## Success / Failure Criteria

Pass criteria are the D0 §D2.2/§D2.3/§D2.4 + §D4.1 fixture/bite-calibrated bands. **Reported
PER STRATUM** (per null type / per `n` / per domain) — no single collapsed cross-cell boolean is
binding (LESSON-001; D0 §8 per-stratum doctrine; EXP-076 audit C1).

- **Evidence FOR (PASS — error-control + protocol validated):** *all* of —
  1. **FPR:** margin-calibrated `expectancy CI_low > m` FPR **≤ 0.05** (Wilson upper-95% **≤ 0.075**)
     on **every** null stratum — `U0` (each `n`), `B_zero` (per its null leg), and the small-`n`
     (`n < 30`) stratum mandated by the EXP-076 disposition. `m` reported per the realized structure.
  2. **MDE:** `MDE(type, n)` **finite / non-degenerate for every `n ≥ 30`**; the full `MDE(n)` curve
     reported per type (and per dogfood domain where applicable).
  3. **Reliability:** **max |predicted − realized| ≤ 0.10** across deciles **and** slope
     **∈ [0.85, 1.15]** for `P(return>X)` on held-out folds, per `X`.
  4. **Counted-read accounting:** a unit test / arithmetic demonstration shows one frozen WF run = one
     counted read; folds are disclosures; an at-cap stratum is rejected; any violated D4.1 condition
     flips each fold to a separate counted read. **Demonstrably honors the 2-read cap.**
  5. **Dogfood:** pipeline completes on the real first-49% slice for every cell with **0 counted TEST
     reads**; the first-49% cutoff is asserted in-code; determinism byte-identical.
- **Evidence AGAINST (FAIL → feeds G-017 `DISCOVERY_ONLY` or a fix):** any null stratum's calibrated
  FPR > 0.05 (or Wilson-hi > 0.075), OR a degenerate MDE at any `n ≥ 30`, OR reliability outside the
  D2.4 band — recorded per stratum, no clean PASS.
- **`PROTOCOL_DEFECT`:** the `WF-EXPANDING` counted-read accounting **cannot** honor the 2-read cap,
  OR the determinism (D6) second pass is not byte-identical → fix the protocol/accounting and re-run
  the affected leg before any Phase 018 TEST design.
- **Inconclusive:** a fold/cell too sparse (< 30 events) to estimate FPR/MDE stably is **disclosed
  per stratum**, never silently passed; an inconclusive binding null stratum blocks the clean PASS and
  is surfaced to G-017.

**Cross-leg tension to resolve in the analysis plan (Stage 2):** the FPR margin `m` and the MDE both
read the **expectancy CI_low**; the analysis plan must state precisely how `m` is calibrated (on the
nulls) and then **held fixed** while MDE is measured (on the effect types), so the two legs are not
circular. The small-`n` FPR stratum must be defined against the EXP-076 finding (expectancy CI
under-covers at `n < 30`): confirm whether that under-coverage translates into FPR inflation under the
margin rule, and report it per `n`. Resolve before implementation — do not hand-wave.

## Complexity Budget

This is a multi-leg calibration validation (FPR + MDE + reliability + protocol accounting + real-data
dogfood) — comparative-tier complexity.

- **Max statistical / validation checks: 4** — (1) margin-calibrated FPR per null stratum, (2)
  `MDE(n)` finiteness, (3) `P(>X)` reliability (decile max-gap + slope), (4) counted-read accounting
  demonstration. (The dogfood and determinism check are procedural integrity checks, not hypothesis
  tests.)
- **Max visualisations: 5** — (a) FPR vs `n` per null type with the 0.05 line and margin `m`;
  (b) `MDE(n)` curve per type/domain (finiteness highlighted); (c) `P(>X)` reliability/calibration
  diagram (predicted vs realized deciles, per `X`); (d) `WF-EXPANDING` fold schedule + per-fold event
  counts (synthetic + dogfood); (e) dogfood pipeline diagnostic (per-cell completion + first-49%
  cutoff evidence).
- **Max new code modules: 1** — a reusable **`xen.wf`** module implementing the `WF-EXPANDING`
  protocol (fold schedule, fold-clustered aggregation to one stratum verdict, and the **counted-read
  accounting rule** D4.1 as a checkable function). Justified: the walk-forward protocol is a core
  CF-CAPGEO-001 family component reused unchanged by all of Phase 018, exactly as `xen.ass` was
  introduced by EXP-076. The `ASS` qualifier core (`xen.ass`) is **reused unchanged** plus a small
  **planned extension** for the **moving-block** bootstrap variant (the `ass.py` docstring already
  reserves this as "the real-data moving-block variant is EXP-077, not here") — an in-family addition
  to the existing core, not a new module. The synthetic DGPs and the FPR/MDE/reliability harness live
  in the experiment's `code/` (reusing the EXP-076 D1 generators).

## Data Requirements

- **Synthetic legs:** reuse the frozen D1 generators and type registry from EXP-076
  (`gen_unimodal/gen_skewnormal/gen_bimodal`, closed-form moments, MC ground truth). Null types `U0`,
  `B_zero`; effect types `U1/U2/U3` (and skew/bimodal effect members as the MDE curve requires).
  Persist the realized FPR/MDE/reliability tables and the calibrated margin `m` to `results/` for the
  audit to re-derive.
- **Dogfood leg:** load current 1-minute bars via the standard lazy first-70%/first-49% pattern,
  **stopping at the first-49% cutoff** (TRAIN region). Build 15m/1h/4h domains with
  `xen.bar_aggregator`. Compute ATR-normalised causal returns on real prices for the chosen smoke
  cells. **Assert in code** that no row at or beyond the first-49% cutoff is ever read.
- **Determinism (D6):** every RNG seed fixed and recorded; a full second pass must be byte-identical
  (hash-compared, EXP-076 pattern).

### Standard Loading Pattern (dogfood only — TRAIN region, first 49%)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_<symbol>_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total_rows * 0.7)            # first 70% = analysis set
train_cutoff = int(analysis_cutoff * 0.7)          # first 70% of analysis = TRAIN = ~49% of full
# Dogfood reads ONLY [0, train_cutoff): the next-21% TEST stratum and final-30% holdout are never sliced.
train_bars = scan.slice(0, train_cutoff).collect()
# holdout = ...                                    # NEVER materialized
```

## Registry Disposition (Stage 1 precondition — satisfied)

- **Family** `CF-CAPGEO-001`: `REGISTERED` (SCREENING-GATED) — `candidate-families/cf-capgeo-001.md`.
- **Countable item** `ASS/VAL-002` / EXP-077: registered in `multiplicity-registry.md` Phase 017
  batch (status PENDING → in-progress at this scope; G0 satisfied). Components `ASS` and
  `WF-EXPANDING` registered in `components/global-techniques.md`.
- **TEST-read ledger:** **no TEST stratum is read.** Synthetic legs touch no market data; the dogfood
  is confined to the first-49% TRAIN region. **0 counted reads; ledger unchanged** — no stratum tally
  to state. (The 2-read-cap accounting **rule** is validated here as a function; it is *exercised*
  against the live ledger only in Phase 018 on the post-INFR-003 5-year strata, per D4.2.)
- **Slots:** 0 candidate slots (methodology validation, not candidate screening).
