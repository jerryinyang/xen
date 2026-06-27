# EXP-093 — One-Shot TEST Confirmation of the RSI-2 Fade (EXIT-RCT, 11 carried cells)

**Phase:** 021 (CF-MR-001 batch 2 — RSI-2 Fade Capture-Geometry & Tradability) · **Family / HYP:**
`CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Stage:** 1 (Scope) · **Type:** one-shot counted-TEST confirmation (the phase's single binding tradability read)
**Governing design:** [`design.md`](../../../docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md)
§4 (EXP-093 row) · D0 [`D0-predeclarations.md`](../../../docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-predeclarations.md)
§D6/4c, §D7 · gate [`G-021-gate-criteria.md`](../../../docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-criteria.md)
· **carried-set decision:** [`D0-amendment-006.md`](../../../docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-006.md)
(operator-ratified 2026-06-24 — all 11 SEQUENCE_PASS cells, Holm-11).

---

## 1. Research question (single, falsifiable)

**Do the EXP-092 hash-pinned EXIT-RCT candidate cells confirm a positive net-of-cost per-event expectancy on the
analysis-TEST stratum — under the frozen referee suite, the phase Holm rule (sized to the 11 carried cells), and
the per-cell margin condition?**

This is the **binding tradability read** of Phase 021 (analog EXP-037/038/032). It is the one experiment in the
phase that spends counted TEST reads. A confirming cell makes the bare RSI-2 fade the programme's **first
net-positive price entry** (G-021 TRADABLE); all carried cells failing the margin/Holm gives G-021 NOT_TRADABLE;
power-limited / spans-zero gives INCONCLUSIVE. The honest prior carried from the programme is **availability ≠
capturable edge** — the TRAIN sequence is necessary-but-not-sufficient, and TEST is a genuine falsification.

EXP-093 decides no G-021 verdict by itself; it produces the per-cell TEST adjudication that the G-021 review
reads against the frozen `G-021-gate-criteria.md` rubric.

## 2. Signal-registry precondition (verified at scope time)

- **Family `REGISTERED` / `ADMITTED`:** `CF-MR-001` is `ADMITTED (BINDING)` at G-020 (first candidate slot
  consumed); `HYP-002` (tradability of the admitted lever) is the active hypothesis. EXP-093 consumes
  **0 new candidate slots**.
- **Multiplicity registry:** EXP-093 is the registered terminal-confirmation experiment of the Phase 021 batch
  (`multiplicity-registry.md`); it introduces **no new countable item** (no new variant, detector, parameter
  branch, or candidate) — it reads the EXP-092-pinned set forward onto TEST. The carried-set scope change (all
  11 vs the §8.3 "smallest defensible") is recorded as `D0-amendment-006`.
- **TEST-read ledger — current tally (stated per the Stage-1 precondition):** all 48 INFR-003 strata are
  **0 counted reads / open** (`test-read-ledger.md`, active 5-year ledger). The **11 carried strata are each
  0/2 open**:

  | Domain | Carried strata (each currently 0/2) |
  |---|---|
  | 4h | EURUSD-4h, USDCHF-4h, AUDJPY-4h, XAUUSD-4h, GBPJPY-4h, EURJPY-4h |
  | 1h | USTEC-1h, US2000-1h, EURUSD-1h, NZDUSD-1h, GBPUSD-1h |

  EXP-093 spends **11 counted TEST reads** — one per carried (instrument, domain) stratum, each **0→1** (one
  read preserved per stratum under the 2-lifetime cap). EURUSD-1h and EURUSD-4h are **distinct strata**. These
  reads are entered in `test-read-ledger.md` **in the same change** that records the EXP-093 result (Stage 7).

## 3. Carried set (frozen by EXP-092 pin + D0-amendment-006)

The complete EXP-092 `SEQUENCE_PASS` set, sha256 `f6427e8342400d46…` — **11 cells, exit = EXIT-RCT** (the only
exit to survive EXP-091/094; EXIT-ERT + the 4 conventional arms died and stay in the file drawer). Per-cell
margin = the EXP-090/094-calibrated MDE: **1h 0.0125 / 4h 0.025 ATR**.

| # | Stratum | Domain | TRAIN net_ci_low | margin | clears margin (TRAIN) | mean & median + (TRAIN) | Disclosure |
|---|---|---|---|---|---|---|---|
| 1 | EURUSD-4h | 4h | 0.13509 | 0.025 | ✓ | ✓ | robust core |
| 2 | USDCHF-4h | 4h | 0.12224 | 0.025 | ✓ | ✓ | robust core |
| 3 | AUDJPY-4h | 4h | 0.11910 | 0.025 | ✓ | ✓ | robust core |
| 4 | XAUUSD-4h | 4h | 0.11492 | 0.025 | ✓ | ✓ | robust core |
| 5 | USTEC-1h | 1h | 0.10802 | 0.0125 | ✓ | ✓ | robust core |
| 6 | US2000-1h | 1h | 0.10393 | 0.0125 | ✓ | ✓ | robust core |
| 7 | GBPJPY-4h | 4h | 0.08645 | 0.025 | ✓ | ✓ | robust core |
| 8 | EURJPY-4h | 4h | 0.04986 | 0.025 | ✓ | ✓ | robust core |
| 9 | EURUSD-1h | 1h | 0.04697 | 0.0125 | ✓ | ✗ (median −0.010) | mean-carried 1h |
| 10 | NZDUSD-1h | 1h | 0.03907 | 0.0125 | ✓ | ✗ (median −0.005) | mean-carried 1h |
| 11 | **GBPUSD-1h** | 1h | **0.00441** | 0.0125 | **✗** | ✗ (median −0.052) | **below margin on TRAIN — carried per operator decision; near-certain FAIL (D0-amendment-006 §2)** |

**Binding interpretation disclosure (carried into `results.md` / G-021):** GBPUSD-1h is below its own EXP-093
margin already on TRAIN and is a near-certain FAIL by construction; its counted read is spent regardless. The
robust core (8) is the strongest evidence; the two mean-carried 1h cells clear margin on the binding mean gate
(D5) but are median-negative (the disclosed shape read). All read **per stratum** (LESSON-001) — no collapsed
cross-cell boolean is binding.

## 4. Data views, instruments, slice, exclusions

- **Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars`. Domain bars
  built per cell: **1h = 60-min, 4h = 240-min** (the EXP-094 `DOMAINS["4h"]=240` patch). Real OHLC only;
  all metrics in **ATR(14) units**.
- **Instruments / cells:** the 11 carried strata in §3 (6 instruments × 4h + 5 instruments × 1h). No instrument
  or domain outside the carried set is read.
- **Slice — the analysis-TEST stratum (the counted read):**
  `[int(int(total_rows·0.7)·0.7), int(total_rows·0.7))` per file = the **last 30% of the first-70% analysis
  set** (the next-21% of the file after the EXP-090–092 TRAIN region). Entries are CORE fade signals whose
  domain-bar `CloseTime` falls in this stratum; the 1-minute intrabar fill walk is **clipped by timestamp at
  the TEST-stratum's right edge** (the analysis-set boundary `int(total_rows·0.7)`), never by 1m index.
- **MANDATORY EXCLUSION — the final-30% global holdout `[int(total_rows·0.7), total_rows)` is NEVER loaded,
  sliced, or materialized** (including its 1-minute bars). A global-holdout release is a separate, later gate,
  not part of EXP-093. `holdout_untouched=true` asserted in `run_metadata.json`.
- **No look-ahead:** exits resolved causally — only domain/1m bars at/after entry, within the MR-tempo cap, and
  forward resolution clips at the analysis-set edge.

## 5. Frozen parameters (inherited — NO tuning at any stage)

Every parameter is frozen upstream; EXP-093 changes **only the data slice** (TRAIN → analysis-TEST) relative to
the verbatim EXP-090/092 substrate.

- **Entry:** `RSI(2)` Wilder, long `RSI₂<10` / short `RSI₂>90` (2/10/90), `xen.mean_reversion`.
- **Exit (sole surviving arm):** EXIT-RCT — `P*_t = Close_t + (AL_t − AG_t)` long / symmetric short, trailing,
  resolved through the 1-minute intrabar fill engine (`xen.intrabar_fill`); real touched fill price (D2.1/D2.5).
- **Adverse side:** `2.0×ATR(14)` stop + EXP-089 MR-tempo cap (exit-on-close at cap), identical to upstream.
- **Cost:** EXP-085 CONSERVATIVE round-trip, Phase-021-local `D0-amendment-003` table (hash `fa7c887…`),
  `F=0`; shared `xen.capgeo_cost.COST_CONSTANTS` **not** mutated.
- **Inference:** moving-block bootstrap one-sided lower bound `net ci_low_1s` (Z=1.645, `n_boot=10_000`,
  `xen.ass`), seeds fixed (`seed_for`), master seed `20260623`.
- **Margins:** the EXP-090/094 per-cell MDE (1h 0.0125 / 4h 0.025 ATR), re-read from the upstream artifacts
  with the same drift assertions EXP-092 used.

## 6. Decision rule (frozen D0 §D6/4c + D0-amendment-006 Holm sizing)

```
Per carried cell, on the analysis-TEST stratum:
  compute net per-event expectancy (mean, ATR units, after D3 cost) over resolved EXIT-RCT exits
  net ci_low_1s = moving-block bootstrap one-sided lower bound (Z=1.645, n_boot=10_000)
  one-sided bootstrap p-value for H0: net expectancy <= 0

Phase Holm family = the 11 carried cells (Holm-Bonferroni, one-sided, alpha=0.05)   [D0-amendment-006]

Cell CONFIRMS    iff Holm-adj p <= 0.05  AND  net ci_low_1s > margin (cell MDE: 1h 0.0125 / 4h 0.025)
Cell FAILS       iff Holm-adj p > 0.05   OR   net ci_low_1s <= margin (significant-but-immaterial)
Cell INCONCLUSIVE iff the bound spans zero / power-limited at the realized TEST count (a la EXP-032)

G-021 (terminal, adjudicated separately in G-021-gate-review.md):
  TRADABLE      iff >= 1 carried cell CONFIRMS
  NOT_TRADABLE  iff every carried cell FAILS the margin/Holm
  INCONCLUSIVE  iff the binding read(s) are power-limited / span zero
```

The verdict is **mechanical and predeclared**; the explanation is not. No threshold, cost, margin, referee, or
Holm sizing is re-edited after seeing any cell's TEST outcome (no goalpost-moving — G-021 §3.8).

## 7. Measurable criteria

- **Success (TRADABLE evidence):** ≥1 carried cell CONFIRMS (Holm-adj p ≤ 0.05 ∧ `ci_low_1s` > margin) on the
  analysis-TEST stratum, with the per-stratum table disclosed.
- **Failure (NOT_TRADABLE evidence):** every carried cell FAILS the margin/Holm condition.
- **Inconclusive:** the binding TEST read(s) are power-limited / span zero at the realized counts.
- **Integrity (required regardless of verdict):** determinism byte-identical second pass (incl. the 1m walk +
  bootstrap stream) on ≥1 cell per domain; real-price metrics only; `holdout_untouched=true`,
  `counted_test_reads=11`, `candidate_slots=0` asserted in `run_metadata.json`; the 11 strata ledger entries
  recorded in the same change (Stage 7).

## 8. Metric denominators / zero-baseline (defined before implementation)

- **Endpoint:** net per-event expectancy in ATR(14) units, real prices, after `D0-amendment-003` cost, over the
  resolved EXIT-RCT exit path. **Denominator = resolved events** (entries whose exit resolves with finite gross,
  finite positive entry ATR, finite non-negative holding days) — identical `keep` mask to EXP-092
  `sequence_cell`. Resolved-fraction and tie-break incidence co-reported per cell.
- **No zero-baseline ratio is computed.** The binding figure is an absolute lower bound in ATR units compared to
  **0** (significance) and to the **fixed per-cell margin** (materiality); there is no percentage-improvement-
  over-zero metric. A cell with `< 2` resolved TEST events is `INDETERMINATE` (cannot bootstrap) — reported, not
  forced to a number.
- **Co-reported (non-binding):** gross expectancy, net median (the family's median-fragility shape read, D5),
  holding days, terminal-favourable fraction, MAE/`q05` adverse tail, tie-break fraction.

## 9. Complexity budget (D0 §5)

| Item | Budget | EXP-093 plan |
|---|---|---|
| Binding statistical tests | 1 (the confirm) + descriptive companions | 1 — the per-cell net `ci_low_1s` + one-sided bootstrap p under Holm-11; descriptive gross/median/tail companions |
| Visualisations | ≤ 4 | TEST per-cell net `ci_low` vs 0 & vs margin; CONFIRM map (per stratum); TRAIN-vs-TEST net comparison (shrinkage honesty); per-cell bootstrap distribution |
| New code modules | **0** | reuse the EXP-090 substrate verbatim (`build_cell_context`, `resolve_arm`/RCT, `xen.intrabar_fill`, `net_return_atr`, `event_costs`/`holding_days`, `xen.ass`); the **only** change is a `load_test_1m` analysis-TEST loader replacing `load_train_1m`, clipping at the analysis-set edge |

## 10. Discipline (binding)

- **Real-price outcomes only;** HA/brick prices never enter a metric; fills are real touched prices.
- **One-shot, no re-reads:** each carried stratum is read exactly once on the analysis-TEST stratum; the cap
  (0→1) is honored; no second TEST pass on any stratum within EXP-093.
- **No scope expansion after approval:** any follow-up (faster-cost sensitivity, 15m, vol-regime, contrarian,
  25/75, cross-cuts, global-holdout release) is a separate experiment under its own dated `D0-amendment-*` /
  slot decision.
- **Deviation handling:** a frozen-design confound found mid-stream → dated `D0-amendment-*` + hard-delete +
  full rerun (programme norm), not a silent follow-up. A verdict-material audit finding → fix + re-run before
  the verdict stands (no document-and-proceed on verdict-bearing numbers).
- **Per-stratum doctrine (LESSON-001):** the per-(instrument, domain) reads are the verdict; pooled counts are
  disclosure only.

## 11. Out of scope (explicit)

- The final-30% global holdout (sealed); any holdout-release decision.
- EXIT-ERT and the conventional contrast arms (died at EXP-091/094; not reopened).
- 15m capture, the vol-regime partition, the contrarian arm, the 25/75 scheme, regime×variant cross-cuts,
  parameter tuning, instrument/domain expansion beyond the 11 carried cells (all registered-but-deferred).
- Any re-tuning of entry, exit, adverse, cost, referee, margin, or Holm sizing.
