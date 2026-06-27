# EXP-092 — Per-Instrument Cost-Bearing Tradability Sequence (EXIT-RCT; 1h + 4h survivors)

**Phase:** 021 (CF-MR-001 batch 2 — RSI-2 Fade Capture-Geometry & Tradability)
**Family / lever:** `CF-MR-001` — bare RSI-2 fade (CORE), admitted at G-020. First candidate slot **already
consumed** (G-020). **HYP:** `CF-MR-001/HYP-002` (tradability of the admitted lever).
**Role (design §4):** the **per-instrument cost-bearing tradability sequence** (A1-style; analog
EXP-034/083). It takes the **sole surviving exit from EXP-091/094 — EXIT-RCT** — on its net-clearing cells
and produces the **hash-pinned `SEQUENCE_PASS` candidate set (sha256) + the phase Holm rule** that EXP-093
(the one-shot TEST) will draw from. **Necessary-but-not-sufficient for TEST.**
**Governing design / D0:** [`docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/`](../../../docs/experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/)
— `design.md` §4 (EXP-092 row), `D0-predeclarations.md` §D6/4b + §D7, `D0-amendment-003` (cost),
`D0-amendment-004`/`-005` (4h opened → admitted, EXP-094), `G-021-gate-criteria.md` §2.
**Discipline (binding):** TRAIN sub-split only (**0 counted TEST reads, 0 candidate slots**); real-price
outcomes; deterministic; **no entry/exit parameter tuning**; per-stratum reporting (LESSON-001). The
final-30% global holdout is **never** loaded.

---

## 0. Signal-registry precondition (Stage 1 gate — confirmed)

- **Candidate family `CF-MR-001` is `ADMITTED (BINDING)`** (G-020, 2026-06-23; first slot consumed) in
  [`docs/signal-registry/candidate-families/cf-mr-001.md`](../../../docs/signal-registry/candidate-families/cf-mr-001.md).
- **EXP-092 is registered** in [`docs/signal-registry/multiplicity-registry.md`](../../../docs/signal-registry/multiplicity-registry.md)
  Phase 021 batch (line 891, **PLANNED**, 0/0). EXP-092 introduces **no new countable item** — no new
  variant, detector, parameter branch, or candidate. It is a TRAIN-only sequence over the *already-screened*
  EXIT-RCT survivors (EXP-091 1h, EXP-094 4h). No multiplicity-registry addition is required.
- **TEST-read ledger:** EXP-092 reads **no TEST stratum** (TRAIN-only). The 11 carried `(instrument, domain)`
  strata are all **0/2 counted reads (open)** per
  [`test-read-ledger.md`](../../../docs/signal-registry/test-read-ledger.md) (5-year INFR-003 active ledger,
  incl. the six 4h strata admitted by EXP-094). No counted read is spent until the one-shot EXP-093 TEST.

## 1. Falsifiable question (single hypothesis)

> For the surviving exit **EXIT-RCT**, which specific `(instrument, domain)` cells reach a **TRAIN-only
> `SEQUENCE_PASS`** — net (post-cost) per-event expectancy one-sided lower bound `net ci_low_1s > 0` at
> **α = 0.05** (Z = 1.645, moving-block bootstrap), **power-confirmed** by the cell's EXP-090 / EXP-094
> finite event-level MDE — and what is the resulting **hash-pinned candidate set + phase Holm rule** eligible
> for the EXP-093 counted TEST read?

This is **not** an edge claim and **not** a TEST confirmation. It is the predeclared candidate-freezing step:
it re-derives, on the carried cells, the binding net lower bound that the EXP-091/094 screen used, certifies
each cell's `SEQUENCE_PASS`, and **pins the candidate set + Holm rule before any TEST row is read** (the
EXP-034/083 hash-pin discipline). G-021 verdict is decided at EXP-093, not here.

## 2. Carried set (frozen by upstream verdicts — no re-selection)

The exit slate was screened in EXP-091 (15m/1h) and EXP-094 (4h); **only EXIT-RCT passed the D6 quorum**
(EXIT-ERT, ATR triple-barrier, RSI-revert-on-close, fixed-bar, partial/trail all net-cleared 0 cells and
**die at the screen** — retained in the file drawer, not reopened). The carried `(exit × cell)` candidate
universe is therefore **EXIT-RCT on its 11 net-clearing cells**:

| Domain | Source | Net-clearing cells (EXIT-RCT, `net ci_low_1s > 0` on TRAIN) | n |
| --- | --- | --- | --- |
| **1h** | EXP-091 (D6/4a quorum 5/5) | EURUSD-1h, GBPUSD-1h, NZDUSD-1h, US2000-1h, USTEC-1h | 5 |
| **4h** | EXP-094 (`ADMIT_4H`; 6 powered members, all net-clear + beat the binding oscillation null 6/6) | AUDJPY-4h, EURJPY-4h, EURUSD-4h, GBPJPY-4h, USDCHF-4h, XAUUSD-4h | 6 |

**Total: 11 candidate cells, all EXIT-RCT** (10 distinct instruments; EURUSD appears on both 1h and 4h —
distinct strata). The 15m domain contributes **nothing** (EXIT-RCT net-cleared 0/10 on 15m — ATR-normalized
cost geometry; EXP-091). Cells are **inherited, not re-selected** — EXP-092 does not re-run the screen or
re-open any died arm/cell.

**Per-cell power margins (EXP-090 / EXP-094 calibrated MDE — the EXP-093 margins, carried for the
power-confirmation leg and the descriptive EXP-093 margin pre-read):** 1h EXIT-RCT margin = **0.0125 ATR**
(EXP-090); 4h EXIT-RCT margin = **0.025 ATR** (EXP-094 `readiness_4h.csv`). All 11 carried cells are powered
members (finite MDE) by construction, so the **power-confirmation leg is satisfied for every carried cell**;
the binding `SEQUENCE_PASS` discriminator is `net ci_low_1s > 0`.

## 3. Data views, instruments, parameters, exclusions

- **Dataset:** VAL-005-admitted INFR-003 5-year 1-minute bars, holdout-fenced `build_domain_bars`. Domain
  bars: **1h (60-min) and 4h (240-min)** only — the carried domains. Real OHLC; ATR(14) units.
- **Entry (inherited, frozen — NO re-tuning):** `RSI(2)` Wilder on domain `Close`, long `RSI₂<10` / short
  `RSI₂>90` (2 / 10 / 90), byte-for-byte from `xen.mean_reversion` (Phase 020 D0).
- **Exit (the only carried arm):** **EXIT-RCT** — reversion-completion target `P*_t = Close_t + (AL_t − AG_t)`
  (long; short symmetric), recomputed each domain bar (trailing), rested as a proactive limit, filled on the
  first 1-minute bar touching it via the frozen `xen.intrabar_fill` engine (timestamp-aligned domain→1m,
  causal order-of-touch, conservative adverse-first tie-break, real touched fill price). Adverse side held
  frozen and identical: `2.0×ATR(14)` stop + EXP-089 MR-tempo cap (exit-on-close at cap). **All exit
  constants frozen at D0 — none tuned here.**
- **Cost (frozen, `D0-amendment-003`):** Phase-021-local CONSERVATIVE round-trip `RT_i = 4·c_i` bps (per
  the frozen 13-instrument table; e.g. EURUSD 3.0 / NZDUSD 4.5 / USTEC 5.0 / XAUUSD 6.0 / US2000 6.0 / JPY
  crosses 6.0), financing `F_i = 0`. Net = gross − cost in ATR units. The shared
  `xen.capgeo_cost.COST_CONSTANTS` is **not** mutated (Phase-018 integrity); only `event_costs`/`holding_days`
  mechanics are imported with the Phase-021 `RT_i`, `fin_bps_day = 0`.
- **Time range / split:** TRAIN sub-split only, `[0, int(analysis_rows·0.7))` per file (= first 49% of each
  file). The 1-minute fill walk is clipped by **timestamp** at the TRAIN edge (never by 1m index). The
  next-21% analysis-TEST stratum and the final-30% global holdout are **never sliced or materialized**.
- **Mandatory exclusion:** the **final 30% global holdout is excluded from all analysis** (never loaded,
  incl. its 1m bars).
- **Substrate reuse (verbatim):** the EXP-090 module (`build_cell_context`, `resolve_arm`/RCT,
  `net_return_atr`, the 1m engine, the cost overlay, `moving_block_bootstrap_cis`) is imported unchanged —
  byte-identical entry/exit substrate to EXP-090/091/094. The 4h cells patch `DOMAINS["4h"]=240` exactly as
  EXP-094 did. EXP-092 adds only the per-cell sequence test, the candidate-set hash-pin, and the Holm rule.

## 4. Method (sequence rule — frozen D6/4b)

1. For each of the 11 carried EXIT-RCT cells, resolve the **real** CORE-fade exits through the verbatim
   substrate, overlay the `D0-amendment-003` cost, and compute the binding **net per-event expectancy
   one-sided lower bound** `net ci_low_1s` (moving-block bootstrap, Z = 1.645, `n_boot = 10_000`, seeds
   fixed via `seed_for("EXP-092", …)`).
2. **`SEQUENCE_PASS`** (binding, per-cell, α = 0.05 one-sided) **iff** `net ci_low_1s > 0` **AND**
   power-confirmed (finite EXP-090/094 MDE — satisfied for all 11 by construction).
3. Emit the **hash-pinned candidate set** = the `SEQUENCE_PASS` cells, with a deterministic ranking by
   `net ci_low_1s` (descending), SHA-256-pinned (the EXP-093 hand-off).
4. Fix the **phase Holm rule** for EXP-093: Holm-Bonferroni over the one-sided TEST p-values of the cells
   EXP-093 carries, **sized to the carried-set cardinality** (the smallest-defensible 1–2 cells per surviving
   exit / per domain are chosen at EXP-093's D0 from this pinned set — not here).
5. **Co-report (descriptive, non-binding):** the EXP-093 **margin pre-read** per cell — whether
   `net ci_low_1s > margin` (margin = the cell's EXP-090/094 MDE), flagging cells that `SEQUENCE_PASS` but
   would **fail the EXP-093 margin condition** (known a-priori fragile cell: **GBPUSD-1h**, EXP-091
   `net_ci_low ≈ 0.0043 < 0.0125`); mean-vs-median split per cell (the family is median-fragile on 3 of the
   5 1h cells; all six 4h members are mean-AND-median positive = robust core); realized counts, fill-rate,
   tie-break incidence, terminal mix.
6. **Determinism replay** on ≥2 carried cells (one 1h + one 4h): `net ci_low_1s` / `SEQUENCE_PASS` /
   candidate-set hash byte-identical on a second pass (D9).

## 5. Success / failure / inconclusive criteria

- **`SEQUENCE_DELIVERED` (success):** every carried cell is adjudicated `SEQUENCE_PASS` / `SEQUENCE_FAIL` on
  the frozen rule; the candidate set is **non-empty**, **hash-pinned**, and accompanied by the sized phase
  Holm rule + the per-cell margin pre-read; determinism passes; 0 reads / 0 slots; holdout sealed. This is
  the expected outcome — the carried cells net-cleared on TRAIN upstream, so they should reproduce
  `SEQUENCE_PASS` here under EXP-092's own fixed seeds (a boundary cell flipping below 0 under independent
  bootstrap seeds — GBPUSD-1h — is a **disclosed** outcome, not a failure of the experiment).
- **`SEQUENCE_EMPTY` (failure to advance):** if **no** carried cell reaches `SEQUENCE_PASS` (e.g., all flip
  net-negative under EXP-092's seeds — not expected), there is no candidate to confirm → routes G-021
  toward NOT_TRADABLE at 0 TEST reads. Recorded; no TEST read spent.
- **Inconclusive:** a carried cell whose `net ci_low_1s` is not finitely computable (insufficient resolved
  events) is reported `SEQUENCE_INDETERMINATE` with record and excluded from the pinned set (not expected —
  all carried cells are powered members with ≥3835 resolved events upstream).

**Mathematical attainability check:** every criterion is a comparison of a bootstrap lower bound against 0
(and, descriptively, against a finite MDE) — no zero-baseline percentage, no unattainable target.

## 6. Complexity budget (design §5)

| Item | Budget | Plan |
| --- | --- | --- |
| Binding statistical tests | **1** (the per-cell sequence net lower bound) | moving-block bootstrap `net ci_low_1s` per cell; no new test family |
| Visualisations | **≤ 4** | (1) per-cell `net ci_low_1s` vs 0 and vs margin (1h+4h); (2) `SEQUENCE_PASS` candidate map; (3) mean-vs-median per cell; (4) margin pre-read / robustness ranking. Built from collected summaries — no heavy reloads |
| New code modules | **0** | reuse EXP-090 substrate + `xen.intrabar_fill` / `xen.capgeo_cost` / `xen.ass` / `xen.mean_reversion` verbatim; EXP-092 adds only orchestration + the hash-pin/Holm helper in `code/run_experiment.py` |

## 7. Metric denominators / zero-baseline behavior

- **Denominator:** per cell, the **resolved** EXIT-RCT events (real CORE entries that reach a terminal —
  favourable target, adverse stop, or cap). Unresolved/degenerate events are excluded with a recorded
  `resolved_frac`; a cell with `< 2` resolved events yields no bound → `SEQUENCE_INDETERMINATE` (not a pass).
- **Zero baseline:** the binding comparison is `net ci_low_1s > 0` (an additive ATR-unit lower bound vs a
  break-even floor of 0 after cost) — **not** a percentage improvement over a zero baseline. Finite handling:
  NaN/degenerate bounds are surfaced explicitly, never coerced to a pass.

## 8. What EXP-092 does NOT do (scope fence)

- Does **not** read the analysis-TEST stratum or the global holdout; spends **0 counted reads / 0 slots**.
- Does **not** re-screen the died exits, re-open 15m, re-select cells, or tune any entry/exit/cost parameter.
- Does **not** choose the EXP-093 carried subset or adjudicate G-021 — it pins the full `SEQUENCE_PASS` set +
  Holm rule; EXP-093's D0 (operator-ratified) selects the smallest-defensible 1–2 cells per surviving
  exit/domain from this pinned set.
- Does **not** introduce a new selection statistic (the binding gate remains the existing net lower bound /
  frozen referee suite) → **no bite-check required** (D0 §D4).
