# Experiment: EXP-061 — MA(20,50)-Substrate Capture Readiness & Benchmark-Geometry Conditioned Efficacy (Dual Conditioning Object: Hybrid **and** Native, Phase 015 Lead L1)

> **Re-run under `D0-amendment-001-dual-parallel-substrate.md` (2026-06-17).** The prior EXP-061
> measured a single MA arm (`M0`) labelled *hybrid* but actually conditioned on MA-segment
> `/STRONG-STAT` — i.e. the **native** object (8360-class). The genuine **hybrid** object
> (ZigZag-`/STRONG-STAT`-conditioned × MA-segment geometry, 3202-class) was never computed. This
> re-run emits **both** conditioning objects **individually** (separate arms, separate matched-random
> nulls, separate viability, separate P11, separate G-015 inputs — never pooled) and **supersedes the
> prior EXP-061 result in place**.

> **Mandatory-reading precondition (Phase 015, binding — inherited from 014-B).**
> `../../docs/experiments-docs/checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. The four mandatory rules are honoured, recorded so
> Stage 4 can check:
> - **(a) conditioning** — honoured, **and now disambiguated**. Two live `/STRONG-STAT`-conditioned
>   HA-harami objects are measured individually: **hybrid** (filter on the in-progress confirmed
>   *ZigZag* move — entry population byte-identical to EXP-053/060) and **native** (filter recomputed
>   on the in-progress confirmed *MA segment*). `/STRONG-STAT` (P7) is binding in each. Each object's
>   matched-random control is a deliberate **null**, not a signal claim.
> - **(b) harami-anchor** — honoured: entry is the **harami confirmation-bar real close** `C` in both
>   objects. The MA(20,50) substrate supplies only the outcome geometry (`rd` / `M_sofar` / target /
>   cap); it does **not** move the anchor. Each matched-random control intentionally breaks the anchor.
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. No position metric is
>   used; every exit acts on a bar known forward-in-time.
> - **(d) expectancy / not first-hit `r`** — honoured. The **binding** endpoint is the Phase 015
>   **median** gross per-event expectancy (P3/P14), computed **per object**. The **mean** (+ 10% trim
>   + worst-5% tail-share) is the P4 **diagnostic co-primary**, disclosed per object (the mean-recovery
>   investigation is the L3 read, EXP-063). First-hit `r` disclosed for single-leg arms only.

**Phase / checkpoint:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface` (Phase 015; **G0 PASS 2026-06-17; D0 Amendment 001 2026-06-17**).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · Phase 015 lead **L1** ·
`CF-HA-HARAMI-001/HYP-014` — EXP-061 (Phase 015 batch, `multiplicity-registry.md`).
**Registry precondition (satisfied):** `CF-HA-HARAMI-001/MA-SUBSTRATE` and its two conditioning modes
(`hybrid`, `native`) are **REGISTERED** (Phase 015 batch, 2026-06-17, G0 PASS), and **both are
parallel first-class substrates carrying the full surface** (Amendment 001). HYP-014/EXP-061 is the
listed plan. The benchmark 3-barrier geometry (50% favourable × 1:1 adverse × adaptive cap) and the
matched-random baseline are already registered. **No new countable item is introduced here.**
**Surface role:** the Phase 015 **lead L1** — does the EXP-060B MA-substrate signal (which beat its
matched-random 85/99 only at the **V2A × `/ADV-NONE` champion** geometry) **generalise to the
benchmark geometry**, separately **for each conditioning object**? Plus the MA-substrate capture
**readiness/reconciliation** precondition for the whole phase. Output feeds the single terminal
**G-015** after the full slate; **no closure or candidate registration here.**
**Governing design / D0:** `design.md` (§1 two objects; §3 objective; §5 slate; §7 G-015 criteria) +
`D0-predeclarations.md` (P1 substrate; **P2 both objects parallel/individual**; P3 median binding;
P4 mean diagnostic; **P5 matched-null per object every read**; P6 non-4h composition; P9 slate; P10
power; **P12 reconciliation roles — native↔EXP-060B 1e-9, hybrid anchorless/EXP-053-population**) +
`D0-amendment-001-dual-parallel-substrate.md`. Inherits 014-B P14/P15.
**Reuses (no new `xen/` module expected):** the EXP-060/060B per-cell pipeline wholesale —
`xen.zigzag.generate_zigzag`, `xen.heiken_ashi_generator`, `xen.ha_harami.detect_ha_harami`,
`xen.expectancy.*` (`live_in_progress_state` / `live_strong_stat` / `adaptive_time_caps_by_epoch` /
`benchmark_barriers` / `bootstrap_median_distribution` / `median_ci` / `contrast_ci`),
`xen.position_exits.*`, and EXP-060's `ma_segment_moves` / matched-random machinery. The prior
EXP-061 code already computes `M0`/`RM0`/`Z0`/`RZ0`; the **one new computation** is the **hybrid
arm `H0`** (ZigZag-`/STRONG-STAT` conditioning mask applied to the MA-segment benchmark geometry)
**and its matched-random null `RH0`**.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the Phase 015 D0 (P11).
  `MA-SUBSTRATE` (+ both modes) is registered at G0/Amendment 001; the benchmark geometry and
  matched-random baseline pre-exist; each matched-random arm is a null, not a candidate. A slot is
  consumed only at G-015 PROCEED on a future scope.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis
  set; F01 file-order prefix; identical fence to EXP-049/053–060). The hybrid population is
  byte-identical to EXP-053/060; the native population is byte-identical to EXP-060B's `M`-arms; no
  new stratum opened; `test-read-ledger.md` requires no entry; global-holdout seal carries forward.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price OHLC**; MA(20,50)
  computed on **real close** (identical to EXP-060's `ma_segment_moves`). No HA price enters any metric.

---

## Hypothesis

On the conditioned `/STRONG-STAT` HA harami, 99-cell TRAIN grid, the **benchmark 3-barrier geometry**
(favourable = `0.50·M_sofar`, adverse = 1:1, MA-defined adaptive cap) on the **MA(20,50) substrate**,
entered at the harami confirmation-bar real close, produces positive gross per-event **median**
expectancy — **tested separately for each conditioning object** (never pooled):

- **Hybrid object (arm `H0`):** ZigZag-`/STRONG-STAT`-conditioned population × MA geometry.
- **Native object (arm `M0`):** MA-segment-`/STRONG-STAT`-conditioned population × MA geometry.

For **each** object independently, the claim is that the benchmark MA arm:

1. is **median-viable** per cell (one-sided 95% regime-clustered moving-block-bootstrap CI_low > 0,
   ≥ 30 qualifying events), **AND**
2. **beats its own same-object matched-random-on-MA null** through the identical benchmark pipeline
   (`H0 − RH0` for hybrid; `M0 − RM0` for native; contrast CI_low > 0), **AND**
3. **clears P11** (≥ 5 viable, null-beating cells over ≥ 3 instruments, **with ≥ 3 cells outside the
   4h domain** — P6 non-4h breadth).

**Falsifiable (per object):** if an object's benchmark MA arm fails P11 viability **or** does not beat
its same-object null in the P11 quorum, the EXP-060B MA-substrate edge **does not generalise** to the
benchmark geometry **for that object**. **This does not close the family**: the surface (L2/L3/S1–S3
and the combined champions) runs regardless (no early-closure, P9). The two objects are reported
**individually**; the phase outcome at G-015 is the stronger object's outcome.

**Disclosed substrate contrast (ZigZag):** the benchmark signal is expected to beat random on **MA**
but **not on ZigZag** (`Z0 ⊁ RZ0`, reproducing EXP-053/060).

**Readiness precondition (P12, corrected roles):** the MA-substrate benchmark 3-barrier construction
is causal, deterministic, and covered; **the native arm `M0` reconciles to EXP-060B's `BENCH-MA`
(M0) and the ZigZag arm `Z0` to EXP-053/EXP-060B `BENCH-ZZ` (Z0) per-cell median + qualifying count to
float tolerance (`1e-9`)**; **the hybrid arm `H0` has no outcome back-reconciliation anchor (new
object)** — its ZigZag-`/STRONG-STAT` conditioning mask reconciles **exactly** to EXP-053's, and it
relies on determinism + causality + the structural invariants. A reconciliation/causality/determinism
failure is a **SUBSTRATE/METHOD_DEFECT** — fixed before any efficacy read is interpreted.

## Question

For **each** conditioning object individually, does the benchmark-geometry conditioned harami express
a signal-attributable median edge **on the MA substrate** (`H0 ≻ RH0`? `M0 ≻ RM0`?) the way it does
**not** on ZigZag (`Z0 ⊁ RZ0`) — i.e., does the EXP-060B 85/99 edge generalise beyond the
V2A × `/ADV-NONE` champion to the simplest stop-bearing geometry, and does it depend on **where the
strong-move filter is computed** (ZigZag move vs MA segment)? And is the MA-substrate benchmark
capture machinery causal/deterministic/covered and reconciled per the corrected P12 roles?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`) for the MA(20,50)-crossover substrate (`ma_segment_moves` on real close), the
  ZigZag substrate (`atr_mult=1.0`, disclosed contrast), confirmed moves/segments, **both**
  `/STRONG-STAT` magnitude sets (ZigZag-move magnitudes for hybrid; MA-segment magnitudes for native),
  the adaptive cap, benchmark favourable/adverse levels, P15 fills, ATR normalisation, and **all**
  outcome metrics.
- **Heiken Ashi candles** for harami detection only (frozen EXP-048 detector). **No HA price in any metric.**

### Event population (two conditioning objects, measured individually)

Both objects share the **same** frozen HA-harami detection and the **same** MA-segment outcome
geometry; they differ **only** in the `/STRONG-STAT` conditioning filter:

- **Hybrid (`H0`).** Qualifies iff the harami passes `/STRONG-STAT` on the in-progress confirmed
  **ZigZag** move (`M_sofar^{ZZ} ≥ p75` of trailing-20 confirmed-ZigZag magnitudes) **and** has a
  buildable MA-segment benchmark geometry at `C`. Conditioning mask is **byte-identical to EXP-053/060**
  (the same `zz["stat"]["retained_p75"]`). Outcome geometry (`rd` / `M_sofar` / target / cap) is the
  **MA segment** (exact EXP-060 construction). **This is the genuinely-new object.**
- **Native (`M0`).** Qualifies iff the harami passes `/STRONG-STAT` on the in-progress confirmed
  **MA segment** (`M_sofar^{MA} ≥ p75` of trailing-20 confirmed-MA-segment magnitudes) **and** has a
  buildable MA-segment benchmark geometry at `C`. Outcome geometry is the same MA segment.
  **Population byte-identical to EXP-060B's `M`-arms** (reconciles 1e-9).

Entry anchor is the harami close `C` in both. Each object's matched-random control draws **non-harami**
in-MA-regime timestamps (same cell / direction, EXP-021/027 exclusion convention), **matched-count to
that object's qualifying harami count**, through the identical MA benchmark pipeline. The hybrid and
native null draws use **independent dedicated RNG streams** (no existing stream shifts).

### Predeclared object set (benchmark geometry; two binding objects + disclosed ZigZag contrast)

Notation as EXP-060: `C` entry close; `M_sofar` magnitude-so-far (substrate-specific); benchmark
`fav_dist = 0.50·M_sofar`; adverse 1:1; adaptive cap `(k=1.5, window=20, floor=6, median, min_moves=5)`.
All levels on **real prices** under the **P15** path model; forward scan `[entry_idx+1, entry_idx+N]`,
TRAIN-fenced; truncated windows `DATA_CENSORED` (disclosed).

| # | Object | Substrate | Conditioning | Entry | Geometry | Role |
|---|--------|-----------|--------------|-------|----------|------|
| **H0** | `BENCH-MA-hybrid` | MA(20,50) | **ZigZag** `/STRONG-STAT` | harami `C` | 50% × 1:1 × cap | **Binding object — HYBRID.** NEW; no outcome anchor. |
| **RH0** | `BENCH-MA-hybrid-random` | MA(20,50) | — | **random in-MA-regime** | 50% × 1:1 × cap | **Binding null for `H0`.** NEW computation; matched to `H0` count. |
| **M0** | `BENCH-MA-native` | MA(20,50) | **MA-segment** `/STRONG-STAT` | harami `C` | 50% × 1:1 × cap | **Binding object — NATIVE.** Reconciles to EXP-060B `M0` (1e-9). |
| **RM0** | `BENCH-MA-native-random` | MA(20,50) | — | **random in-MA-regime** | 50% × 1:1 × cap | **Binding null for `M0`.** Matched to `M0` count (the prior EXP-061 `RM0`). |
| Z0 | `BENCH-ZZ` | ZigZag | ZigZag `/STRONG-STAT` | harami `C` | 50% × 1:1 × cap | Disclosed substrate contrast. Reconciles to EXP-053/060B `Z0` (1e-9). |
| RZ0 | `BENCH-ZZ-random` | ZigZag | — | **random in-ZZ-regime** | 50% × 1:1 × cap | Disclosed ZigZag null (expect `Z0 ⊁ RZ0`). |

`/STRONG-STAT` is binding for every signal/random arm (the random arms inherit the benchmark geometry,
not the conditioning). **No** V2A / `/ADV-NONE` / favourable-alt / third-alt / exit / horizon arm here.
The binding discriminators are **`H0` vs `RH0`** (hybrid) and **`M0` vs `RM0`** (native), **each judged
individually; the two objects are never pooled.**

### Parameters (all frozen / predeclared; no tuning)

Identical to EXP-060/060B: ZigZag Wilder ATR(14), `ATR_MULT=1.0`; **MA(20,50) on real close (fixed; P1
— not swept)**; `/STRONG-STAT` trailing-20 ≥ p75 (computed on ZigZag magnitudes for the hybrid object,
on MA-segment magnitudes for the native object); benchmark `fav=0.50·M_sofar`, adverse 1:1, cap
`(k=1.5, window=20, floor=6, median, min_moves=5)`; ATR-normalisation = Wilder ATR(14) at the harami
entry bar (P14); bootstrap `b = round(m^(1/3))`, `N_BOOT = 10_000`, **fixed per-cell seed (P3)**. No
grid swept; no parameter tuned against outcomes.

### Instruments / cells / time range

The **99-cell EXP-049/053–060 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3
COVERAGE_EXCLUDED: US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11** with the P6 non-4h
breadth rule, **separately per object**. **TRAIN only** = first 70% of the first-70% analysis set (F01
file-order prefix; identical fence to EXP-049/053–060). TEST and the final-30% global holdout are
**not** read. Forward windows clipped to `train_end_ts`; truncated → `DATA_CENSORED`. DE30 carries the
truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- ZigZag and MA(20,50) segmentation are future information until confirmed. The signal (harami +
  `/STRONG-STAT`, on either substrate), `M_sofar`, the benchmark levels, and the cap use **only**
  confirmed prior moves/crossovers and **real bars at or before the entry bar** (via
  `live_in_progress_state`). The **native** `/STRONG-STAT` filter references only **MA segments
  confirmed at/before the harami bar**; the **hybrid** filter references only **ZigZag moves confirmed
  at/before the harami bar**. MA(20,50) `_sma` is trailing. Matched-random entries are constructed
  causally with the identical pre-entry-only state.
- Every exit is forward (P15 intrabar touch / 1:1 stop / cap-bar real close); no exit references an
  unconfirmed pivot or future bar. Forward scan reads only `[entry_idx+1, min(entry_idx+N,
  last_train_idx)]`, `CloseTime ≤ train_end_ts`. Ordering/alignment by `CloseTime`, never bar index.

### Exclusions

- No costs (gross only). Object set is exactly the 6 above; **no** V2A / `/ADV-NONE` / `/VPTARGET` /
  `/MAGTARGET` / `/ADV-EXTREME` / `/THIRD-*` / `/EXIT-*` / horizon arm; **no** MA-parameter sweep
  (MA(20,50) fixed); **no** position-in-move filter; **no** `/BARCFG` / `/CONFIRM`.
- **No pooling/aggregation of the hybrid and native objects** in any metric, contrast, or composition.
- No parameter tuning; **no post-result variant selection**; no gate adjudication (single G-015 after
  the full slate). No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All **gross**, per-cell first, P11-composed (≥ 5 cells over ≥ 3 instruments, **≥ 3 outside 4h**),
**computed and reported separately for each object**; per-cell viable iff **CI_low > 0** (one-sided
95% regime-clustered moving-block bootstrap, fixed seed) **AND ≥ 30 qualifying events**. Binding
endpoint = **median** per-event position-weighted gross expectancy (P3/P14); the **mean** (raw + 10%
trimmed + worst-5% tail-share, each CI'd) is the P4 disclosed diagnostic.

Each object receives its **own** EVIDENCE_* classification (and the deliverable records both,
individually):

- **EVIDENCE_FOR (object's signal generalises to benchmark geometry on MA):** the object's benchmark
  MA arm is median-viable **AND beats its same-object null** (`H0 − RH0` for hybrid / `M0 − RM0` for
  native; CI_low > 0) **AND clears P11** with non-4h breadth.
- **EVIDENCE_AGAINST (object's edge is champion-geometry-specific):** the object's arm fails P11
  viability **or** does not beat its same-object null in the quorum. **Family stays OPEN — the surface
  runs regardless** (P9).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥ 30 qualifying events on
  the object's signal or null arm; no correctness failure. Disclosed; never defaulted.
- **SUBSTRATE/METHOD_DEFECT:** any reconciliation, determinism, causality, or invariant failure → fix
  before reporting. Invariant checks: (i) **`M0` reproduces EXP-060B `BENCH-MA` (M0)** per-cell median
  + qualifying count to `1e-9`; (ii) **`Z0` reproduces EXP-053/EXP-060B `BENCH-ZZ` (Z0)** likewise;
  (iii) **`H0`'s ZigZag-`/STRONG-STAT` conditioning mask reconciles exactly to EXP-053** (same retained
  set / count per cell), and `H0`'s qualifying count is disclosed (new); (iv) the 1:1 stop, when it
  binds, closes at the same bar/level; (v) **matched-count holds per object** — `RH0` count = `H0`
  count and `RM0` count = `M0` count (and `RZ0` = `Z0`); (vi) every exit price is a real-bar P15 fill
  with `CloseTime ≤ train_end_ts`.

Deliverable label: **MA_BENCHMARK_GENERALISATION_CHARACTERISED (dual-object)**, carrying — **per object,
individually** — the signal-vs-null binding discriminator (per cell + P11 tally with non-4h breadth),
the per-object EVIDENCE_* classification, the readiness/reconciliation table (`M0`↔EXP-060B M0 1e-9;
`Z0`↔EXP-060B Z0 1e-9; `H0` ZZ-conditioning↔EXP-053 exact), the disclosed `Z0`-vs-`RZ0` substrate
contrast, and the disclosed mean/trim/tail diagnostic + first-hit `r` (single-leg arms). **No phase
closure or candidate registration here.**

## Complexity Budget

- **Max distinct statistical methods: 3** — (1) regime-clustered moving-block bootstrap CI on an arm's
  **median** per cell (`bootstrap_median_distribution` + `median_ci`); (2) the same bootstrap applied
  to the per-cell **mean** + 10% trimmed mean (the P4 diagnostic); (3) same-object signal−null contrast
  CI (`contrast_ci`, independent — matched-random are different events): `H0 − RH0`, `M0 − RM0`, and
  disclosed `Z0 − RZ0`. A parameterised re-instrumentation across the 6-arm set, not new methods.
- **Max visualisations: 5** — (i) **per-object signal-vs-null per-cell forest** (`H0`/`RH0` and
  `M0`/`RM0`, faceted) — headline; (ii) **hybrid-vs-native viability map** across cells (each object's
  median-viable ∧ beats-own-null; non-4h cells marked); (iii) **substrate contrast** (`H0−RH0`,
  `M0−RM0`, `Z0−RZ0`) by domain; (iv) **median vs mean** for `H0` and `M0` (the P4 skew preview);
  (v) **P11 (non-4h) composition** per object. Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** Reuses the existing EXP-061 / EXP-060B machinery (which
  already computes `M0`/`RM0`/`Z0`/`RZ0`); the only new computation is the **hybrid arm `H0`** (ZigZag
  conditioning mask through the MA benchmark geometry) and its matched-random null **`RH0`**. At most
  one thin orchestration change under `code/`; **no new `xen/` analysis module**.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event` (identical to
  EXP-060), defined for every **qualifying** event (`fav_dist > 0`, finite positive `ATR_entry`, exit
  reaches a finite P15 fill within the TRAIN-fenced window). `DATA_CENSORED` and construction-warmup
  events are **excluded** from median and mean and **disclosed as counts** per cell per arm.
- **Per-cell endpoints (per object):** `E_cell_median` (binding, P14) and `E_cell_mean` + 10% trimmed
  mean (P4 diagnostic), each over the arm's qualifying-event population, each with its own fixed-seed
  bootstrap CI.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for an arm is NOT_VIABLE-by-power
  for that arm (non-reportable), never an undefined/infinite ratio. The hybrid and native objects
  qualify **different** counts (3202-class vs 8360-class on EURUSD-5m); both disclosed per object;
  depleted cells disclosed, never defaulted.
- **First-hit `r`** defined for the single-leg benchmark arms (`H0`/`M0`/`Z0`), disclosed; never binding.
- **Disclosed secondaries (never binding):** per-arm qualifying / `DATA_CENSORED` / warmup counts, win
  rate, mean + trimmed mean + tail-share, single-leg `r`, the `Z0`/`RZ0` substrate contrast.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows =
int(total*0.7)`, `train_rows = int(analysis_rows*0.7)`; collect only the first `train_rows` file-order
rows (F01 prefix; never sort/collect the full file, never read TEST/holdout); assert chronological;
`train_end_ts` = last `CloseTime`. Aggregate each member domain (5m strict; others `min_coverage=0.90`);
fence to `CloseTime ≤ train_end_ts`; generate HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves
+ `confirm_indices`; run `ma_segment_moves` (MA(20,50) on real close) → MA confirmed segments; detect
haramis on HA candles aligned by `CloseTime`; build **both** conditioning masks (hybrid =
`zz["stat"]["retained_p75"]`; native = `ma["stat"]["retained_p75"]`) and the shared MA benchmark
geometry (`rd` / `M_sofar` / fav / adv / cap) from the MA segment; for `H0` (hybrid mask × MA geometry),
`M0` (native mask × MA geometry), and `Z0` (ZZ mask × ZZ geometry) compute per-event benchmark exits
via the existing resolvers + `R_event` + qualifying mask; build `RH0` / `RM0` (MA) and `RZ0` (ZZ) by
matched-count random in-regime selection through the identical benchmark pipeline, each matched to its
**own** object's count, with **independent dedicated RNG streams**; bootstrap per-cell **median + mean
+ trimmed mean** per arm (fixed seed); compute `H0 − RH0`, `M0 − RM0`, and disclosed `Z0 − RZ0`
contrasts; compose by P11 with the non-4h rule **per object**; second full pass for determinism.
`tqdm` over the 99-cell grid; **bounded per-cell memory** (forward scans bounded by `bench_n ≈ 6`).
Outputs (`results/`): `per_cell_expectancy.parquet` (per cell × arm: object tag, median/mean/trimmed +
CIs, n_qualifying, censoring/warmup, win rate, viability + beats-own-null flags); `object_efficacy_map.csv`
(per object: `H0`-`RH0` / `M0`-`RM0` binding discriminator + P11 non-4h tally, EVIDENCE_* per object);
`substrate_contrast.csv` (`H0−RH0`, `M0−RM0`, `Z0−RZ0`); `reconciliation.csv` (`M0`↔EXP-060B M0,
`Z0`↔EXP-060B Z0 median/count 1e-9; `H0` ZZ-conditioning↔EXP-053 exact); `readiness.csv` (per-cell
construction PASS / coverage / invariant flags); `generalisation_readout.json` (per-object EVIDENCE_*
→ G-015 input); `run_metadata.json` (seed, frozen constants, EXP-053/060/060B source paths/hashes).
Bounded plots from collected per-cell summaries (no reloads).

### Standard Loading Pattern (TRAIN slice, per cell)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob(f"timebars/timebars_{symbol}_*.parquet"))[-1]

scan = pl.scan_parquet(path)                      # F01 file-order prefix; no full sort/collect
total_rows = int(scan.select(pl.len()).collect().item())
analysis_rows = int(total_rows * 0.7)             # first 70% = analysis set
train_rows = int(analysis_rows * 0.7)             # first 70% of analysis = TRAIN
train_bars = scan.slice(0, train_rows).collect()  # TEST + holdout never sliced
# assert chronological; train_end_ts = train_bars["CloseTime"].max()
# domain aggregation (xen.bar_aggregator) for 5m strict / others min_coverage=0.90
```

## Suggested Direction

Fork the prior EXP-061 `code/run_experiment.py` (it already computes `M0`/`RM0`/`Z0`/`RZ0`). Three
changes: **(1)** add the **hybrid signal arm `H0`** — resolve the benchmark MA geometry over the
population `pop_hybrid = ma["buildable"] & zz["stat"]["retained_p75"]` (the genuinely-new object: the
*ZigZag* `/STRONG-STAT` conditioning mask applied to the *MA-segment* `rd`/`M_sofar`/fav/adv/cap). A
small refactor lets `bench_signal_arm` take an explicit conditioning mask while drawing geometry from
the MA context. **(2)** add the **hybrid matched-random null `RH0`** — the existing matched-random-on-MA
selector, matched to `H0`'s qualifying count, excluding the `H0` signal entries, on **independent
dedicated RNG purpose offsets** (no existing stream shifts). **(3)** relabel the existing `M0`/`RM0`
as the **native** object and `H0`/`RH0` as **hybrid**, emit **per-object** P11 / EVIDENCE_* readouts
(never pooled), and update reconciliation to the corrected P12 roles: `M0`↔EXP-060B M0 (1e-9),
`Z0`↔EXP-060B Z0 (1e-9), `H0` ZZ-conditioning mask↔EXP-053 (exact count). Keep the 10% trimmed mean +
worst-5% tail-share P4 diagnostic on every arm. **Do not adjudicate G-015** (single gate after the full
slate). Fixed per-cell seed throughout (P3).
</content>
