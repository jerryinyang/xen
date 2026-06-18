# Phase 016 D0 — Predeclarations (CF-HA-HARAMI-001, Candidate Screening)

**Status:** **RATIFIED 2026-06-18 — G0 PASS.** These predeclarations are frozen. No
amendment is permitted after G0 without a dated D0-amendment file in this directory.
**Checkpoint:** `2026-06-18-016-harami-candidate-screening`
**Governing design:** `design.md` (this directory).
**Family:** `CF-HA-HARAMI-001` (REGISTERED, OPEN — first candidate active).
**Candidate:** `CF-HA-HARAMI-001/CAND-001` — MA(20,50)-native `/STRONG-STAT` conditioned
HA harami, MA-segment 3-barrier geometry. First candidate slot consumed at G-015 2026-06-18.
**Inherits:** Phase 015 `D0-predeclarations.md` (P1–P22), `D0-amendment-001` (dual-object
elevation), `D0-amendment-002` (EXP-067 drop). Where a Phase 016 item supersedes, it says so.
**Discipline (binding throughout Phase 016):** detection on HA candles; every outcome metric
on real prices (`RealOpen/High/Low/Close`), never HA prices; holdouts sealed; gross only in
EXP-070/EXP-071; no TEST or holdout contact before the freeze protocol (P8) is complete;
nothing tuned against TEST data; EXP-072 and EXP-073 each require their own D0 before data
contact.

---

## P1 — Substrate and conditioning object: inherited, binding

All Phase 015 substrate parameters are **inherited without change**:

- **MA(20,50) on real close** — fixed, not swept (Phase 015 P1, ratified 2026-06-17).
- **Conditioning object: MA-native only.** `/STRONG-STAT` recomputed on confirmed MA
  segments (magnitude-so-far ≥ p75 trailing-20 confirmed MA-segment magnitudes; causal).
  8360-class event population on the TRAIN set. The hybrid object is
  CHARACTERISED_NOT_VIABLE and is never re-introduced as a binding arm.
- **Outcome geometry: MA-segment 3-barrier** — favourable 50% of `M_sofar`, adverse 1:1
  stop, MA-adaptive cap; P15 path-ordered intrabar fills.
- **EURUSD excluded instrument-wide.** TEST-capped (holdout-contaminated EXP-032 +
  EURUSD-4h at 2-read cap). No EURUSD stratum enters any binding inference.
- **P12 reconciliation:** all Phase 016 code must reproduce EXP-061 M0 / EXP-068
  BENCH/PARTIAL-V2A / EXP-066 PARTIAL-V2A at 1e-9 before any new result is reported.
- **Fixed per-cell bootstrap seed** (Phase 015 P3 [REC], now binding): `seed` is a
  deterministic function of `(instrument, domain)` — same as Phase 015 convention.

## P2 — Two arms, parallel, different roles

Both `N-PARTIAL-V2A` and `N-V2A×ADV-NONE` run on every Phase 016 data contact. They are
**never pooled**. Their roles are fixed:

| Arm | Role | Gate input? |
| --- | --- | --- |
| `N-PARTIAL-V2A` | **Binding lead arm** — composition threshold, G-016 verdict | Yes |
| `N-V2A×ADV-NONE` | **Disclosed secondary arm** — MEAN_RECOVERABLE diagnostic, EXP-072/EXP-073 input | No — reported alongside but never upgrades or vetoes the lead arm |
| `N-BENCH` | Disclosed signal-check anchor | No |
| `RM-native` | Matched-random-on-MA null for attribution | Yes (contrast) |

`N-V2A×ADV-NONE` result does not determine TEST_CONFIRMED / NOT_CONFIRMED. A failing
disclosed arm does not veto a passing binding arm; a passing disclosed arm does not rescue
a failing binding arm.

## P3 — Binding viability endpoint: median gross per-event expectancy

Inherited from Phase 015 P3:

- **Per-event gross ATR-normalised return** on real prices, direction-signed, under the
  predeclared arm's exit rule.
- **Binding per-cell endpoint:** median CI_low > 0 (regime-clustered moving-block
  bootstrap, `b = round(m^(1/3))`, `N_BOOT = 10_000`, fixed seed per P1).
- **Power floor:** ≥ 30 events per cell; cells below floor are excluded from composition.
- **Holm adjustment** across the declared TEST family for per-cell p-values.

## P4 — Mean co-primary and winsorized mean (binding + disclosed)

### Raw mean CI (binding co-primary, inherited from G-015)

The raw per-event mean with moving-block bootstrap CI is the **secondary binding
co-primary** for `N-PARTIAL-V2A`. A cell passes the full conjunction iff:
`median CI_low>0` ∧ `raw-mean CI_low>0` ∧ `beats-RM contrast CI_low>0`.
The composition threshold counts only cells satisfying the full conjunction.

### Winsorized mean (predeclared disclosed co-primary, Phase 016 D0)

**10% symmetric winsorized mean** (`winsorm`, `TRIM_FRAC = 0.10`) is a **predeclared
disclosed co-primary** in EXP-070 and EXP-071. Implementation: matches EXP-068's
`_winsorized_mean` function exactly (replace extreme 10% on each side with boundary
values `p10` / `p90`; full sample contributes; no RNG / bootstrap — point estimate
only). A cell is `winsorm+` when `m ≥ 30` and the winsorized mean point estimate > 0.

**Role by arm:**

- `N-PARTIAL-V2A` (binding): the gate is unchanged (`raw-mean CI_low>0`). A cell that
  is `median+` ∧ `beats-RM` ∧ `winsorm+` ∧ `raw-mean−` receives a **yellow-flag**
  note in results — the raw-mean failure is more informative in a PARTIAL_RECOVERY cell
  than in a TAIL_DRIVEN one; it should be investigated but does not automatically veto
  the cell's inclusion in the disclosed portfolio picture.
- `N-V2A×ADV-NONE` (disclosed): `winsorm+` ∧ `mean−` cells are the primary
  MEAN_RECOVERABLE candidates for EXP-072's tail-filter follow-up.
- The winsorized mean does **not substitute for `raw-mean CI_low>0`** in any gate.

## P5 — Predeclared TEST family (frozen at G0)

**Source:** EXP-068 `results/g015_verdict.json`, key
`native_per_arm["PARTIAL-V2A"]["g015_passes"]["cells"]`, excluding instrument `EURUSD`.
Extracted 2026-06-18 before any TEST row is loaded.

| Cell | Instrument | Domain | Type | TEST-stratum state |
| --- | --- | --- | --- | --- |
| GBPUSD-5m | GBPUSD | 5m | non-4h | 0 counted reads — open |
| GBPUSD-1h | GBPUSD | 1h | non-4h | 0 counted reads — open |
| NZDUSD-1h | NZDUSD | 1h | non-4h | 0 counted reads — open |
| NZDUSD-2h | NZDUSD | 2h | non-4h | 0 counted reads — open |
| GBPJPY-30m | GBPJPY | 30m | non-4h | 0 counted reads — open |
| US2000-4h | US2000 | 4h | 4h | 0 counted reads — open |

**Summary:** 6 cells / 4 instruments (GBPUSD, NZDUSD, GBPJPY, US2000) / 5 non-4h / 1 4h.

**Excluded EURUSD cells** (instrument-wide TEST-capped, not in family):
EURUSD-15m, EURUSD-1h, EURUSD-4h.

This list is **frozen**. No cell may be added or removed after G0 ratification except by
a dated D0-amendment that records the change and its reason.

## P6 — TEST-stratum accounting

- Every cell in P5 incurs **exactly 1 counted read** when it enters a binding
  stratum-specific inference in EXP-071. Budget: ≤ 6 strata.
- The EXP-071 portfolio-aggregate output (P10) is a **disclosure** against all 6 member
  strata — no additional counted reads.
- EXP-073 portfolio construction (conditional) is a **disclosure** — no new per-stratum
  counted reads beyond EXP-071's budget.
- Counted reads and the portfolio disclosure are recorded in `test-read-ledger.md` in the
  **same commit** that records EXP-071's result — never deferred.
- All 6 strata are confirmed at 0 counted reads as of 2026-06-18 (`test-read-ledger.md`
  "New Domains" section for GBPUSD-5m / GBPJPY-30m; legacy 1h/2h/4h rows for the rest).
- GBPUSD-5m and GBPJPY-30m strata use the rows materialized in the Phase 016 D0 change
  (2026-06-18, "New Domains" table in `test-read-ledger.md`).

## P7 — EXP-070 pass criteria (method calibration)

EXP-070 must pass all three legs before EXP-071 is authorised:

### Leg 1 — FPR control
Construct matched-structure null populations per cell (same harami event count, same
matched-random construction as `RM-native`, but signal arm draws shuffled). Run the
full inference pipeline (median CI, raw-mean CI, Holm adjustment). A cell **passes FPR**
iff the proportion of null-draw runs calling `median CI_low>0` ≤ 0.05.

- Any cell exceeding FPR 0.05 by > 0.01 (i.e., FPR > 0.06) is **excluded from the
  binding EXP-071 family** with record; the exclusion is disclosed in EXP-071's output.
- Any cell with FPR ≤ 0.06 is retained; the measured FPR is reported per cell.
- If > 2/3 of the declared TEST family cells fail FPR control: **METHOD_DEFECT** — fix
  and re-run EXP-070 before any TEST contact.

### Leg 2 — Finite MDE
The bootstrap CI width must be finite (non-degenerate) in all declared cells. A
degenerate CI (all-zero or width = 0) in any retained cell is a METHOD_DEFECT.

### Leg 3 — Determinism
A second full-pass execution of EXP-070 on the same TRAIN data must reproduce all
output files byte-identical (same seeds, same code). Hash-pinned.

### Leg 4 — Temporal stability (walk-forward diagnostic, TRAIN-only)
A rolling 6-month window on the TRAIN timeline (step = 1 window; no TEST rows loaded)
computes per-cell gross `N-PARTIAL-V2A` point-estimate expectancy. A cell is flagged
**`DECAYING`** if the final-window point estimate is more than 1 SE below the
full-TRAIN point estimate (SE = bootstrap SE from the full-TRAIN run).

- `DECAYING` is a **disclosed flag**, not a calibration failure. `DECAYING` cells are
  not excluded from the EXP-071 binding family on this ground alone.
- The `DECAYING` / `STABLE` / `GROWING` classification per cell is reported in EXP-070
  and carried into the EXP-071 D0 predeclarations (noted in the frozen-selection file).

## P8 — Freeze-before-TEST protocol (binding)

1. EXP-070 must complete (all legs pass) and its result file must be hash-recorded.
2. A **freeze file** (`EXP-071/frozen_selection.json`) is written **before any TEST row
   is loaded**, recording:
   - The predeclared TEST family (P5 cell list, byte-identical to this document).
   - Any EXP-070 FPR-exclusions (cells dropped from the binding family with reason).
   - The EXP-070 temporal stability flags per cell.
   - The composition threshold (P9) verbatim.
   - The inference method hash (bootstrap seed, `N_BOOT`, block-length rule).
3. The freeze file is hash-pinned (SHA-256 of its content appended to the file).
4. **No amendment to the TEST family after the freeze file is written.** Any change
   requires a dated D0-amendment and operator re-ratification — which constitutes a
   new TEST contact decision, not a correction to an existing one.

## P9 — EXP-071 composition threshold (frozen at G0)

A cell **clears the composition threshold** iff all of:
- `median CI_low > 0` (Holm-adjusted across the declared family at α = 0.05)
- `raw-mean CI_low > 0`
- `beats-RM contrast CI_low > 0` (Holm-adjusted)
- Point estimate > calibrated margin (per-cell mechanical margin set by EXP-070 Leg 1
  synthetic-null calibration, R1.2 analog)

**TEST_CONFIRMED** iff: ≥ 3 cells clear the threshold, over ≥ 2 instruments, of which
≥ 2 clearing cells are non-4h.

The ≥ 2 non-4h sub-rule prevents confirmation resting solely on the single 4h cell
(US2000-4h) plus one other. With 5 non-4h cells in the family, ≥ 2 non-4h clearing
cells is a modest, honest requirement.

**TEST_INCONCLUSIVE** iff: the composite CI spans zero (power-limited; no systematic
negative), or the cell count falls below the threshold with wide CIs.

**TEST_NOT_CONFIRMED** iff: the family fails the threshold with `CI_low ≤ 0` in the
majority of binding cells (systematic negative).

## P10 — Portfolio-aggregate disclosure in EXP-071

EXP-071 emits a **gross equal-weight composite ATR-normalised expectancy CI** across
all binding cells that enter the inference (i.e., the declared family minus any FPR
exclusions from EXP-070). Implementation:

- Pool all per-event returns from the binding cells, equally weighted by cell.
- Compute the composite median and mean (raw and winsorized) with moving-block bootstrap
  CI (same bootstrap convention as per-cell; `seed` = fixed composite seed predeclared
  in the freeze file).
- This metric is entered in `test-read-ledger.md` as a **disclosure** against all member
  strata — not a counted read, not a gate condition.
- The portfolio disclosure informs G-016 and is the gross anchor for EXP-073.

## P11 — EXP-071 disclosures (full list)

All of the following run in the same data contact as EXP-071 and are disclosed (not
binding for the gate verdict):

1. `N-V2A×ADV-NONE` per-cell and portfolio-aggregate results on the same TEST strata.
2. `N-BENCH` (single-leg benchmark) per-cell results on the same strata.
3. `RM-native` matched-random per-cell distribution on the TEST strata.
4. Per-cell winsorized mean point estimates for both arms (P4).
5. Per-cell temporal stability flags from EXP-070 (`DECAYING`/`STABLE`/`GROWING`).
6. Per-cell EXP-070 measured FPR (for the binding cells retained in the family).

## P12 — Gross-only posture for EXP-070 and EXP-071

No cost model is applied in EXP-070 or EXP-071. Costs enter only in:

- **EXP-072** (cost-aware / tail-filter follow-up): its own D0 required; opened only
  after EXP-071 TEST_CONFIRMED with explicit operator direction.
- **EXP-073** (portfolio construction): its own D0 required; opened only after EXP-071
  TEST_CONFIRMED with explicit operator direction. TRAIN-side portfolio scheme selection
  is gross; a cost-adjusted portfolio read is EXP-073's own D0 item.

## P13 — Conditional scopes (EXP-072, EXP-073): deferred to own D0s

EXP-072 and EXP-073 are registered (HYP-025 / HYP-026; `multiplicity-registry.md`
Phase 016 batch) but their predeclarations are **not frozen here**. Each requires:
- An explicit operator direction to open (after EXP-071 TEST_CONFIRMED).
- Its own dated D0-predeclarations file in this directory before any data contact.
- No parameters for EXP-072 (cost model, financing, tail-filter rule) or EXP-073
  (weighting schemes, TRAIN selection rule, portfolio fitness convention) are frozen
  at this G0.

EXP-072 and EXP-073 may run in parallel. Their results both feed G-016.

## P14 — cTrader parity

No cTrader strategy implementation or parity validation exists for the harami family
(VAL-002 parity covers the AVWAP strategy only). EXP-071 proceeds as **Python-only**.
cTrader parity is a post-Phase-016 requirement before any cTrader-side holdout or live
deployment step, matching the Phase 006/008 AVWAP sequence (EXP-028 Python → EXP-029
cTrader). This does not block G-016 adjudication.

## P15 — Amendment rule

Any change to a frozen item in this document requires a **dated D0-amendment file**
(`D0-amendment-NNN-<slug>.md`) in this directory, recording: what changed, why, whether
the change consumes a new multiplicity slot or TEST read, and operator sign-off. The
amendment file is the authority; this document is not retroactively edited.

---

## G0 Ratification

**G0 PASS — 2026-06-18 (operator).**

All D0 items (P1–P15) ratified as drafted. The predeclared TEST family (P5, 6 cells),
composition threshold (P9, ≥3/≥2/≥2-non-4h), and freeze protocol (P8) are frozen.
EXP-070 may now be scoped and executed. No TEST row is loaded until EXP-070 passes all
four legs and the freeze file (P8) is written and hash-pinned.

Governing design: `design.md` (this directory).
Registry: `docs/signal-registry/multiplicity-registry.md` Phase 016 Batch (HYP-023/024/025/026;
EXP-070/071/072/073).
TEST-stratum ledger: `docs/signal-registry/test-read-ledger.md` — 6 strata at 0 counted
reads confirmed at G0.
