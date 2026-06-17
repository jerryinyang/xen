# Experiment: EXP-060B — MA(20,50) Substrate Dominance: Genuine Lead or Capped-Up/Uncapped-Down Skew Artifact? (Conditioned HA Harami, EXP-060 Gap-Fill)

> **Mandatory-reading precondition (014-B, binding).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this scope was written. EXP-060B is a **diagnostic addendum to EXP-060**
> (HYP-013 follow-up, "HYP-013b"); it adds **no new countable item** and feeds the **single 014-B G2**.
> The four mandatory rules are honoured, recorded so Stage 4 can check:
> - **(a) conditioning** — honoured. The signal object is the **live `/STRONG-STAT`-conditioned HA harami**,
>   population byte-identical to EXP-053/060 (binding). `/STRONG-STAT` (P7) is binding. The added
>   **matched-random controls** (on both substrates) are deliberate **nulls**, not signal claims.
> - **(b) harami-anchor** — honoured for every signal arm: entry is the **harami confirmation-bar real
>   close** `C`. Swapping the move-segmentation substrate (ZigZag → MA(20,50)) changes only the
>   *move definition* that supplies `rd`, `M_sofar`, and the adaptive cap — **not** the entry anchor. The
>   matched-random controls intentionally break the anchor (that is what makes them nulls).
> - **(c) position-in-move descriptive-only / never a live filter** — honoured. No position metric is used;
>   every exit is acted on at a bar known forward-in-time.
> - **(d) expectancy / not first-hit `r`** — honoured. The **binding** endpoint stays the 014-B **median**
>   gross per-event expectancy (P14). The **mean** per-event return is a P14-sanctioned **disclosed
>   secondary**, here promoted to the central *characterisation* lens (the median≫mean skew is the object
>   under study). No new binding gate contradicts P14. First-hit `r` is disclosed for single-leg arms only.

**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15).
**Family / candidate:** `CF-HA-HARAMI-001` (`REGISTERED`, OPEN) · follow-up to `CF-HA-HARAMI-001/HYP-013`
(EXP-060). Composes the already-registered objects `CF-HA-HARAMI-001/EXIT-PARTIAL` (P17, V2A scheme),
`CF-HA-HARAMI-001/ADV-NONE` (P3 alternative), the benchmark adaptive cap (P4), and the two **P13 baselines**
(matched-random, MA(20,50)) already used by EXP-053/060. **No new branch, variant, detector, or parameter is
introduced.** Registers as a diagnostic line **`CF-HA-HARAMI-001/HYP-013b` — EXP-060B** (Phase 014-B batch),
exactly as EXP-059B registered HYP-012b. **0 candidate slots, 0 TEST reads.**
**Surface role:** an **interpretation gap-fill for EXP-060**, run **before** the single 014-B G2 adjudicates.
EXP-060 returned `CHARACTERISED_NOT_VIABLE_ELIGIBLE` and recorded its rationale as *"MA-baseline dominance
is a substrate property — ZigZag single-point entry cannot match multi-leg MA trend hold."* EXP-060B tests
whether that recorded interpretation is **correct** (closure strengthened) or whether the MA(20,50) median
dominance is the **same capped-upside / uncapped-downside skew artifact** that EXP-060's own champion exhibits
(median positive, mean ≈ 0). Output feeds the single 014-B **G2**; **no closure or candidate registration here.**
**Governing design:** `014-B-design.md` (§3 binding endpoint = median, mean disclosed; §4 no intermediate
gates; §8 G2 criteria) + `014-B-D0-addendum.md` (P14/P15/P17/P20/P21); inherits Phase 014 `design.md` §8 D0
and `candidate-families/harami.md` (`/EXIT-PARTIAL`, `/ADV-NONE`).
**Reuses (no new `xen/` module expected):** the **entire EXP-060 per-cell pipeline** — `xen.zigzag.generate_zigzag`,
`xen.heiken_ashi_generator`, `xen.ha_harami.detect_ha_harami`, `xen.expectancy.live_in_progress_state` /
`live_strong_stat` / `adaptive_time_caps_by_epoch` / `benchmark_barriers` / `bootstrap_median_distribution` /
`median_ci` / `contrast_ci`, `xen.position_exits.resolve_legs` / `leg_levels_from_fracs` / `weighted_returns`
/ `exit_reason_weights`, `xen.adverse_targets.adverse_none_sentinel`,
`xen.favourable_targets.paired_median_contrast_ci`, and EXP-060's own `ma_segment_moves` / `ma_seg_arm` /
matched-random machinery (`code/run_experiment.py`). EXP-060 **already computes** the MA(20,50) arm for every
arm; EXP-060B (i) **emits** what EXP-060 dropped (MA mean + MA exit-reason composition) and (ii) adds the one
genuinely new computation — a **matched-random control on the MA substrate**.

## Operator decisions (2026-06-17, recorded before any new data contact)

Established in the operator's prior investigation of EXP-060's generated results (no new data contact preceded
these):
1. **EXP-060B is a diagnostic re-instrumentation + one new control — not a search.** Every object is
   predeclared here; no post-result variant selection. It does not adjudicate G2 (it emits the readout the
   G2 desk needs).
2. **Binding endpoint unchanged (median, P14).** The mean is reported as the P14-sanctioned disclosed
   secondary and is the *characterisation* focus; it does **not** become a new binding viability gate. A
   "genuine lead" must clear the **median** P11 viability *and* beat its **own-substrate** matched-random
   control (mirroring EXP-060's champion logic), with the mean reported alongside as the tradability caveat.
3. **Two confounds EXP-060 left open are the whole experiment:**
   - **Skew confound** — does the MA-substrate champion also have median ≫ mean (capped V2A upside +
     uncapped ADV-NONE downside)? EXP-060 emitted MA *median* only.
   - **Signal-redundancy confound** — on ZigZag the harami entry was redundant vs matched-random
     (champion ≈ random ≈ 0.37 ATR on 5m). Is it **also** redundant on MA? EXP-060 ran **no** matched-random
     control on the MA substrate, so this is untested.

Additional standing decisions (precedent-default, no deviation): leg weighting fixed 3 equal legs (`w=1/3`),
V2A fractions `{1/3,2/3,1}` (identical to EXP-059/060); `/STRONG-STAT` (P7) binding for every signal arm;
`/STRONG-HA` (P8) disclosed; all gross; detection on HA candles, **every metric on real prices**.

## Slot & ledger accounting (binding)

- **0 candidate slots, 0 TEST reads.** Diagnostic per the 014-B D0 addendum. No countable item is introduced:
  V2A (`/EXIT-PARTIAL`), `/ADV-NONE`, the benchmark cap, and **both P13 baselines** are already registered;
  the **MA-substrate matched-random control is a null/baseline-of-a-baseline, not a candidate**. The MA(20,50)
  substrate is the EXP-050/053 baseline trend substrate (already in use), not a new detector. A candidate
  branch would consume a slot only if G2 returns PROCEED (P21) on a *new* MA-substrate scope — never here.
- **No TEST stratum is read.** All work on the **TRAIN** slice (first 70% of the first-70% analysis set),
  identical fence to EXP-049/053–060. Population byte-identical to EXP-053/060; no new stratum is opened;
  `test-read-ledger.md` requires no entry; global-holdout seal carries forward. No HA-harami TEST stratum has
  ever been read.
- All work **gross**; detection on HA candles; **all outcome metrics on real-price** OHLC; MA(20,50) computed
  on **real close** (identical to EXP-060's `ma_segment_moves`). No HA price enters any metric.

---

## Hypothesis

The MA(20,50)-segmented substrate's ~3–4× higher **median** per-event expectancy over the ZigZag champion
(reported by EXP-060) is **not** a genuine, signal-attributable, tradable edge but the **same
capped-upside (V2A partial take-profit) / uncapped-downside (`/ADV-NONE`) drift-and-skew artifact** that
EXP-060's own ZigZag champion exhibits. Concretely, on the conditioned `/STRONG-STAT` HA harami, 99-cell
TRAIN grid:

1. **Skew:** the MA-substrate V2A×ADV-NONE arm has **median ≫ mean**, with mean failing to clear P11
   (mean CI_low ≤ 0 in the quorum), just as the ZigZag champion does (EXP-060: champion gross mean ≈ 0 or
   negative on 5/6 domains despite positive median); AND
2. **Redundancy:** the MA-substrate harami arm **does not beat its own matched-random control**
   (`A3-MA − A3-MA-random` paired-median contrast CI_low ≤ 0 in the P11 quorum), i.e., random in-MA-regime
   entries through the identical MA V2A×ADV-NONE×cap pipeline reproduce the MA median — the harami adds
   nothing on MA either.

Falsifiable: if the MA-substrate harami arm **clears P11 median viability AND beats its own matched-random
control (CI_low > 0) in the quorum AND its mean clears P11 (CI_low > 0)**, then the MA-substrate dominance is
a **genuine MA-conditioned lead** — EXP-060's recorded "substrate property" interpretation is incomplete and
the 014-B G2 should **not** close the family without a scoped MA-substrate follow-up.

## Question

Is the MA(20,50) median advantage over the ZigZag champion (a) a tradable signal-attributable edge, or
(b) the same median-positive / mean-≈0, TIMECAP-dominated, entry-redundant artifact as the ZigZag champion?
Specifically: (i) what is the **median−mean gap** of the V2A×ADV-NONE arm on the **MA** substrate vs the
**ZigZag** substrate, and which lever (V2A capped upside vs ADV-NONE uncapped downside) drives it? (ii) does
the **MA-substrate harami beat a matched-random control on the MA substrate**? (iii) is the MA arm's
**exit-reason composition** also TIMECAP-dominated (the EXP-060 trap) or does MA actually convert to FAV?

---

## Scope Boundaries

### Data Views

- **Real domain bars** (5m strict; 15m/30m/1h/2h/4h via `xen.bar_aggregator.aggregate_ohlc`,
  `min_coverage=0.90`) for the ZigZag substrate (`atr_mult=1.0`), the **MA(20,50)-crossover substrate**
  (`ma_segment_moves` on real close), confirmed moves, strong-move magnitudes, both adaptive caps, all
  barrier/leg levels, P15 fills, ATR normalisation, and **all** outcome metrics.
- **Heiken Ashi candles** for harami detection only (frozen EXP-048 detector) and the `/STRONG-HA` arm
  (disclosed). **No HA price in any metric.**

### Event population (identical conditioned signal — byte-identical to EXP-053/060)

The live conditioned HA harami: frozen HA-harami detector **AND** `/STRONG-STAT` p75 magnitude-percentile
filter on the **in-progress confirmed-move magnitude-so-far** (binding). On the **ZigZag** substrate the
in-progress move/direction is ZigZag-defined; on the **MA** substrate it is MA(20,50)-defined (the exact
EXP-060 `ma_seg_arm` construction). **Note (binding interpretation):** swapping ZigZag→MA(20,50) is *not* a
clean substrate-only swap — at the same harami timestamp it changes **four** things at once: (1) the trade
**direction** `rd`; (2) the **qualifying subset** (the `/STRONG-STAT` percentile is recomputed against
MA-move magnitudes, so a different set of haramis passes — EXP-060: MA `m` ≈ 3–4× ZigZag `m` on liquid
cells); (3) the favourable **target levels** (`0.50·M_sofar` with MA-defined `M_sofar`); and (4) the adaptive
**cap** (MA-defined durations). The **entry anchor (harami close) is the only thing held fixed.** This is why
EXP-060's "substrate property" reading needs RM3 — the MA median advantage is most plausibly a
trend-following-direction + no-stop drift-capture effect any in-MA-regime entry would share, which only an
MA-substrate matched-random control can isolate. The matched-random controls draw **non-harami** in-regime
timestamps
(same cell/direction, EXP-021/027 exclusion convention) per substrate, matched-count to that cell's harami
count, through the identical exit pipeline. Population reconciliation vs EXP-060 is **exact** for the signal
arms (SUBSTRATE/METHOD_DEFECT if it diverges).

### Predeclared object set (2 substrates × {champion geometry + skew-attribution arms} + 2 matched-random nulls)

Notation as EXP-060: `C` entry close; `M_sofar` magnitude-so-far (substrate-specific); `fav_dist=0.50·M_sofar`;
V2A legs `{1/3,2/3,1}×fav_dist`; benchmark adaptive cap (floor=6); `/ADV-NONE` = sentinel `adv=∓inf`. All
levels on **real prices** under the **P15** path model; forward scan `[entry_idx+1, entry_idx+N]`,
TRAIN-fenced; truncated windows `DATA_CENSORED` (disclosed). The arms below are **all already computed by
EXP-060 except the two MA-random nulls**; EXP-060B adds **mean + exit-reason composition** to every one.

| # | Object | Substrate | Entry | Geometry | Role |
|---|--------|-----------|-------|----------|------|
| Z3 | `V2A-NONE-ZZ` **(champion)** | ZigZag | harami `C` | V2A × ADV-NONE × cap | EXP-060 champion A3, reproduced. **Invariant anchor (median exact).** Now report mean + ew. |
| Z2 | `V2A-1TO1-ZZ` | ZigZag | harami `C` | V2A × 1:1 × cap | Skew attribution: stop-bearing vs ADV-NONE (does the stop remove the left tail?). EXP-060 A2. |
| Z1 | `50PCT-NONE-ZZ` | ZigZag | harami `C` | 50% single leg × ADV-NONE × cap | Skew attribution: ADV-NONE without V2A (is uncapped downside alone the cause?). EXP-060 A1. |
| Z0 | `BENCH-ZZ` | ZigZag | harami `C` | 50% × 1:1 × cap | Reference; EXP-060 A0. |
| M3 | `V2A-NONE-MA` | MA(20,50) | harami `C` | V2A × ADV-NONE × cap | **The object under study.** EXP-060 `ma_seg` for V2A-NONE. Now report median **and mean and ew**. |
| M2 | `V2A-1TO1-MA` | MA(20,50) | harami `C` | V2A × 1:1 × cap | MA skew attribution (stop vs no-stop on MA). |
| M1 | `50PCT-NONE-MA` | MA(20,50) | harami `C` | 50% × ADV-NONE × cap | MA skew attribution. |
| M0 | `BENCH-MA` | MA(20,50) | harami `C` | 50% × 1:1 × cap | MA reference. |
| RZ3 | `V2A-NONE-ZZ-random` | ZigZag | **random in-regime** | V2A × ADV-NONE × cap | EXP-060 matched-random for A3, re-emitted with mean. |
| **RM3** | `V2A-NONE-MA-random` | MA(20,50) | **random in-regime** | V2A × ADV-NONE × cap | **NEW control — the decisive test.** Does the harami beat random on the MA substrate? |

`/STRONG-STAT` is binding for every signal/random arm; `/STRONG-HA` rerun of M3/Z3 disclosed. Both P13
baselines remain available for context but the **binding discriminator is M3 vs RM3** (own-substrate control).

### Diagnostic readouts (all disclosed-characterisation; feed the G2 desk)

Per cell, then P11-composed (≥5 cells over ≥3 instruments):
- **D1 — skew (median−mean gap):** for {Z3,Z2,Z1,Z0,M3,M2,M1,M0}, the per-cell median and **mean** (each with
  a regime-clustered moving-block-bootstrap CI). Headline: does **M3** have median ≫ mean like Z3? Attribution:
  compare ADV-NONE arms (Z3/Z1/M3/M1) vs stop-bearing arms (Z2/Z0/M2/M0) — if the gap is large under ADV-NONE
  and small under 1:1, the **uncapped downside** is the skew source (entry-agnostic), not the harami.
- **D2 — MA signal redundancy (binding discriminator):** the `M3 − RM3` paired-median contrast (common
  qualifying subset) and, disclosed, `M3 − RM3` on the **mean**. Mirrors EXP-060's own champion-vs-random
  test, now on the MA substrate.
- **D3 — exit-reason composition:** weight fraction exiting via each V2A leg / the 1:1 stop / the time cap, for
  Z3 vs M3 (and the matched-random nulls). Is MA also TIMECAP-dominated (~64% on Z3, EXP-060) or does it
  convert more weight to FAV? The mechanism diagnostic; never enters viability.

### Parameters (all frozen / predeclared; no tuning)

Identical to EXP-060: ZigZag Wilder ATR(14), `ATR_MULT=1.0`; MA(20,50) on real close; `/STRONG-STAT`
trailing-20 ≥p75; V2A `{1/3,2/3,1}`, 3 equal legs; benchmark cap `(k=1.5, window=20, floor=6, median,
min_moves=5)`; ATR-normalisation = Wilder ATR(14) at the harami entry bar (P14); bootstrap `b=round(m^(1/3))`,
`N_BOOT=10_000`, fixed seed (P14). **No grid is swept; no parameter is tuned against outcomes.** (Note: no
floor=48 / A4 horizon arm here — EXP-060 already characterised it; EXP-060B is substrate-vs-skew, not horizon.)

### Instruments / cells / time range

The **99-cell EXP-049/053–060 member grid** (17 instruments × {5m,15m,30m,1h,2h,4h} − 3 COVERAGE_EXCLUDED:
US500-4h, JP225-2h, JP225-4h). Per-cell first, then **P11**. **TRAIN only** = first 70% of the first-70%
analysis set (F01 file-order prefix; identical fence to EXP-049/053–060). TEST and the final-30% global
holdout are **not** read. All forward windows clipped to `train_end_ts`; truncated → `DATA_CENSORED`.
DE30 carries the truncated-coverage disclosure.

### Look-ahead / causality discipline (binding)

- ZigZag and MA segmentation are future information until confirmed. The signal (harami + `/STRONG-STAT`),
  `M_sofar`, the levels, and both caps use **only** confirmed prior moves/crossovers and **real bars at or
  before the entry bar**. The MA(20,50) `_sma` is trailing; MA segments are bounded by crossovers confirmed
  before entry (via `live_in_progress_state`). The matched-random entries are constructed causally with the
  identical pre-entry-only state.
- Every exit is forward (P15 intrabar touch / shared 1:1 stop where present / cap-bar real close); no exit
  references an unconfirmed pivot or future bar. Forward scan reads only
  `[entry_idx+1, min(entry_idx+N, last_train_idx)]`, `CloseTime ≤ train_end_ts`.
- Ordering/alignment by `CloseTime`, never bar index across views.

### Exclusions

- No costs (gross only). **Diagnostic only:** the object set is exactly the 10 above; **no** new geometry, **no**
  new substrate beyond ZigZag + the already-registered MA(20,50) baseline, **no** floor=48 horizon arm, **no**
  `/VPTARGET`/`/MAGTARGET`/`/ADV-EXTREME`/`/THIRD-*`/`/EXIT-TRAIL-*`/other V2* schemes, **no** position-in-move
  filter, **no** `/BARCFG`/`/CONFIRM`.
- No parameter tuning; **no post-result variant selection**; no gate adjudication (single 014-B G2 after the
  full slate — EXP-060B emits a characterisation readout only).
- No TEST or holdout contact; no candidate slot; no TEST read.

## Success / Failure Criteria

All **gross**, per-cell first, P11-composed (≥5 cells over ≥3 instruments); per-cell viable iff **CI_low > 0**
(one-sided 95% regime-clustered moving-block bootstrap) **AND ≥ 30 qualifying events**. The binding endpoint
remains **median** per-event position-weighted gross expectancy (P14); the **mean** is the P14 disclosed
secondary, central to the characterisation.

- **ARTIFACT_CONFIRMED (MA dominance is skew/redundancy, not a tradable signal — strengthens EXP-060 closure):**
  **either** (skew) the MA champion **M3** has median ≫ mean with the **mean failing P11** (mean CI_low ≤ 0 in
  the quorum) — like the ZigZag champion — **or** (redundancy) **M3 does not beat RM3** (the `M3 − RM3`
  paired-median contrast CI_low ≤ 0 fails the P11 quorum). Recorded as: EXP-060's "substrate property"
  reading is an **artifact** of capped-up/uncapped-down skew and/or entry redundancy; G2 closure
  well-supported (adjudicated at G2, never here). The D1 attribution sub-flag records whether ADV-NONE
  (uncapped downside) is the entry-agnostic skew source.
- **SUBSTRATE_LEAD_FOUND (would change G2 routing):** **M3 clears P11 median viability AND beats RM3**
  (`M3 − RM3` CI_low > 0 in the quorum) **AND M3's mean clears P11** (mean CI_low > 0 in ≥ the quorum).
  Recorded as: a genuine MA-conditioned harami lead exists; recommend the G2 desk **not** close
  CF-HA-HARAMI-001 without a **new scoped MA-substrate experiment** (candidate registration would occur there
  at PROCEED, never in EXP-060B).
- **INCONCLUSIVE (power-limited):** fewer than the P11 quorum of cells reach ≥30 qualifying events on M3 or
  RM3; no correctness failure. Disclosed; never defaulted.
- **SUBSTRATE/METHOD_DEFECT:** any determinism, causality, or invariant failure → fix before reporting.
  Invariant checks: (i) **Z3 reproduces EXP-060 A3 (V2A-NONE)** per-cell median, qualifying count, and
  exit-reason composition to float tolerance; (ii) **M3 reproduces EXP-060's `maseg_median` for V2A-NONE**
  exactly; (iii) population reconciliation vs EXP-060 exact for all signal arms; (iv) leg weights sum to 1.0;
  (v) the **ADV-NONE sentinel never fires an adverse exit** on Z3/Z1/M3/M1/RZ3/RM3 (no `ADV` exit class —
  only `FAV`/`TIMECAP`/`DATA_CENSORED`); (vi) the shared 1:1 stop (Z0/Z2/M0/M2), when it binds, closes all
  still-open legs at the same bar/level; (vii) **matched-count holds** — RZ3/RM3 qualifying count equals its
  cell's harami qualifying count per the matched-random convention; (viii) every exit price is a real-bar P15
  fill with `CloseTime ≤ train_end_ts`.

The deliverable label is **MA_SUBSTRATE_DOMINANCE_CHARACTERISED** carrying: the D2 binding discriminator
(`M3 − RM3` median contrast + M3 mean P11, the artifact-vs-lead fork that feeds G2); the D1 median−mean skew
table across all 8 signal arms × 2 substrates (with the ADV-NONE-vs-1:1 attribution); the D3 exit-reason
composition (Z3 vs M3); the `/STRONG-HA` disclosed rerun of M3/Z3; population reconciliation vs EXP-060; and
disclosed secondaries (per-arm qualifying / `DATA_CENSORED` / warmup counts, win rate, first-hit `r` for
single-leg arms only). **No phase closure or candidate registration here** (single 014-B G2 after the slate).

## Complexity Budget

- **Max distinct statistical methods: 4** — (1) regime-clustered moving-block bootstrap CI on an arm's
  **median** expectancy per cell (`bootstrap_median_distribution` + `median_ci`); (2) the **same bootstrap
  machinery applied to the per-cell mean** (same resampling, mean statistic — the skew readout); (3)
  paired-median contrast CI for `M3 − RM3` (and the disclosed `Z3 − RZ3`) on the common qualifying subset
  (`paired_median_contrast_ci`); (4) arm-vs-baseline contrast CI (`contrast_ci`) for context vs the two P13
  baselines. Applied across the predeclared object set — a parameterised re-instrumentation of EXP-060, not
  new methods.
- **Max visualisations: 5** — (i) **median vs mean per arm × substrate** (the skew gap; M3 vs Z3 highlighted)
  — the headline; (ii) **median−mean gap by arm grouped by adverse model** (ADV-NONE vs 1:1, both substrates)
  — the attribution; (iii) **`M3 − RM3` paired contrast per cell** (forest; does the harami beat MA-random?);
  (iv) **exit-reason composition Z3 vs M3** (TIMECAP/FAV/ADV stacked, by domain); (v) **MA-substrate viability
  map** across cells (M3 median CI_low>0 ∧ beats RM3 ∧ mean CI_low>0). Secondary tables to CSV.
- **Max new code modules: 1 — *expected 0*.** EXP-060B reuses EXP-060's `code/run_experiment.py` machinery
  wholesale (it already computes `ma_seg_arm` and matched-random); the only new computation is composing the
  existing matched-random entry selection with the existing `ma_seg_arm` pipeline (the MA-substrate
  matched-random control) plus emitting mean + exit-composition columns that EXP-060 computed but dropped. At
  most one thin orchestration wrapper under `code/`; **no new `xen/` analysis module**. Orchestration in
  `code/run_experiment.py`.

## Metric Denominators & Zero-Baseline

- **Per-event realised gross return** (ATR units) is the position-weighted `R_event` (identical definition to
  EXP-060), defined for every **qualifying** event of an arm (`fav_dist>0`, finite positive `ATR_entry`, every
  leg reaches a finite P15 exit within the TRAIN-fenced window). `DATA_CENSORED` and construction-warmup events
  are **excluded** from both the median and the mean and **disclosed as counts** per cell per arm.
- **Per-cell endpoints:** `E_cell_median` (binding, P14) and `E_cell_mean` (disclosed, the skew readout), each
  over the arm's qualifying-event `R_event` population, each with its own bootstrap CI.
- **Zero-baseline / power:** a cell with **< 30 qualifying events** for an arm is NOT_VIABLE-by-power for that
  arm (non-reportable for its readout), never an undefined or infinite ratio. The MA substrate qualifies a
  *different* (typically larger) count than ZigZag (EXP-060: MA `m` ≈ 3–4× ZigZag `m` on liquid cells) — both
  counts disclosed; depleted cells disclosed, never defaulted.
- **median−mean gap** is reported as the signed difference `E_cell_median − E_cell_mean` per arm per cell; a
  large positive gap with mean CI spanning/below 0 is the skew signature. It never enters median viability.
- **First-hit `r`** defined only for single-leg arms (Z0/Z1/M0/M1), disclosed; undefined for multi-leg arms.
- **Disclosed secondaries (never binding):** per-arm qualifying / `DATA_CENSORED` / warmup counts, win rate,
  mean and median−mean gap, exit-reason composition, single-leg `r`, the `/STRONG-HA` rerun, the two P13
  baselines for context.

## Data Requirements

Per cell (instrument × domain), TRAIN slice only: lazy `pl.scan_parquet`; `analysis_rows=int(total*0.7)`,
`train_rows=int(analysis_rows*0.7)`; collect only the first `train_rows` file-order 1-minute rows (F01 prefix;
never sort/collect the full file, never read TEST/holdout); assert chronological; `train_end_ts`=last
`CloseTime`. Aggregate each member domain (5m strict; others `min_coverage=0.90`); fence to
`CloseTime ≤ train_end_ts`; generate HA candles; run ZigZag (`atr_mult=1.0`) → confirmed moves +
`confirm_indices`; run `ma_segment_moves` (MA(20,50) on real close) → MA confirmed moves; detect haramis on HA
candles aligned by `CloseTime`; build the live conditioned `/STRONG-STAT` population on **both** substrates;
compute benchmark favourable/adverse levels + adaptive cap (per substrate); for each of the 8 signal arms
compute per-event exits via the existing resolvers + weighted `R_event` + qualifying mask; build the two
matched-random controls (RZ3 on ZigZag, **RM3 on MA**) by matched-count random in-regime selection through the
identical V2A×ADV-NONE×cap pipeline; bootstrap per-cell **median and mean** per arm; compute the `M3 − RM3`
(and `Z3 − RZ3`) paired contrasts and the disclosed baseline contrasts; compose by P11; second full pass for
determinism. `tqdm` over the 99-cell grid; **bounded per-cell memory** (do not retain all domain frames or all
bootstrap draws; forward scans bounded by `bench_n`≈6 bars). Fixed seed; deterministic. Outputs (`results/`):
`per_cell_expectancy.parquet` (per cell × arm: median/mean + CIs, exit-reason composition, n_qualifying,
censoring/warmup, win rate, viability flags); `skew_map.csv` (D1: median, mean, gap, CIs per arm × substrate);
`ma_control_map.csv` (D2: M3 vs RM3 paired contrast, M3 mean P11, artifact-vs-lead per cell + P11 tally);
`exit_reason_map.csv` (D3: Z3 vs M3 vs nulls); `secondary_map.csv` (`/STRONG-HA`, single-leg `r`, baselines);
`composition_readout.json` (ARTIFACT_CONFIRMED / SUBSTRATE_LEAD_FOUND / INCONCLUSIVE fork → G2 input);
`population_reconciliation.csv` (signal arms vs EXP-060 exact: Z3↔A3 median/count/ew, M3↔maseg_median);
`run_metadata.json` (seed, frozen constants, EXP-060 source paths/hashes). Bounded plots from collected
per-cell summaries (no reloads).

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

Fork EXP-060's `code/run_experiment.py`; it already computes the ZigZag arms (A0–A3), the MA(20,50) arm per
arm (`ma_seg_arm`), and the matched-random selection. Three minimal changes: (1) **emit mean + exit-reason
composition for the MA arm** (computed, previously dropped); (2) **add RM3** = run the existing matched-random
entry selection through `ma_seg_arm`'s V2A×ADV-NONE×cap pipeline (the one new computation); (3) **bootstrap the
mean** alongside the median for every arm, and compute the `M3 − RM3` / `Z3 − RZ3` paired contrasts. Emit the
D1 skew table, the D2 binding discriminator, the D3 exit composition, and the artifact-vs-lead readout;
**reconcile Z3↔EXP-060-A3 and M3↔EXP-060-maseg exactly** (defect if not); **do not adjudicate G2** (single
014-B G2 after the full slate).
