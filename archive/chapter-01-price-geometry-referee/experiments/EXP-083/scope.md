# Experiment: EXP-083 — TRAIN-Only Candidate Screen of Derived + Benchmark Exits Behind the Separability Gate (CF-CAPGEO-001 Phase 018 / HYP-004a)

**Phase:** 018 (CF-CAPGEO-001 data-derived exit / capture geometry; checkpoint
`2026-06-20-018-capgeo-exit-geometry`, **G0 PASS 2026-06-21**) · **HYP:** HYP-004a (the TRAIN-only
screen leg of HYP-004) · **Registry:** `CF-CAPGEO-001` Phase 018 batch (multiplicity-registry); the
3 derived `/EXIT-DERIVED` candidates and the benchmark branches `/EXIT-RR`, `/EXIT-TRAIL`, `/EXIT-VP`,
`/EXIT-PARTIAL`, `/SIZE-VOLADJ` are **already registered at D0** (no new countable item) · **Candidate
slots:** 0 (TRAIN screen; slots consumed only at the deferred confirm) · **TEST reads:** **0 counted
(TRAIN-only).**

**Slate amendment (binding):** **D0-amendment-001 (operator-directed 2026-06-22)** splits HYP-004 —
**EXP-083 is the TRAIN-only candidate screen** that emits and hash-pins the surviving valid-candidate
set, and **the counted `WF-EXPANDING` confirmation is deferred to the reserved-conditional EXP-084**,
opened only on a non-empty EXP-083 valid set + operator ratification. EXP-083 reads **no TEST row** and
spends **no counted read**. See
`docs/experiments-docs/checkpoints/2026-06-20-018-capgeo-exit-geometry/D0-amendment-001-split-exp083-train-screen.md`.

**Counted-read precondition (Stage-1 check):** the INFR-003 5-year ledger
(`docs/signal-registry/test-read-ledger.md`, re-materialized 2026-06-21 on VAL-005 PASS) shows **all
16 instruments × {15m,1h,4h} = 48 strata at 0/2 counted reads, open** (EURUSD fully eligible, clean
slate — D8). **EXP-083 makes no stratum-specific TEST inference and slices no TEST stratum**: all
screening runs on the TRAIN region only. Per the TRAIN-only convention (EXP-074/075/080/081 precedent)
this is a **disclosure, not a counted read**; the ledger is unchanged and every tally stays 0/2 open.

**Gating preconditions (met):** EXP-080 `READINESS_DELIVERED` (46-cell member set; re-audit PASS),
EXP-081 `CHARACTERISATION_DELIVERED` (D3 inputs locked; audit PASS 0C/1W/3I), EXP-082
`DERIVATION_DELIVERED` (552/552 triples; `xen.capgeo_exits.derive_barriers` **sha256-pinned** `34d03f45…`;
audit PASS 0C/1W/3I).

---

## Hypothesis / Exploratory Question

**Screening question (no holdout/TEST contact, gross, TRAIN-only):** Among the three frozen
data-derived exits (`D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT`) and the full
enumerated grid of conventional benchmark exits, does **any** `{candidate × substrate × stratum}`
combination, applied to the frozen-substrate held positions over the TRAIN region, **(a)** clear the
cheap gross G-018a screen (positive expectancy + median + bounded tail vs `SUB-RANDOM` and the per-cell
matched-random null) **and (b)** pass the binding pre-TEST **separability gate** (S1 attribution ∧ S2
tail non-residual) — i.e. survive as a **valid candidate** eligible for a future counted-read
confirmation?

**Falsifiable structure.** The experiment verdict is one of:

- **`SCREEN_DELIVERED`** — the screen completes for every member cell and **≥1** `{candidate × stratum}`
  survives both TRAIN gates; the surviving **valid-candidate set + the Holm correction rule are frozen
  and hash-pinned** as the binding hand-off artifact for EXP-084. (This is *not* an edge/tradability
  claim — it is a TRAIN-only eligibility result; the binding referee-suite adjudication and the counted
  read happen only at EXP-084.)
- **`ALL_CANDIDATES_FAIL`** — no `{candidate × stratum}` survives the separability gate (the
  EXP-082-anticipated outcome if the derived adverse leg is the inseparable "harvest the median, leave
  the catastrophe" trap). Then **EXP-084 is never opened, 0 lifetime TEST reads are ever spent**, and
  HYP-004 closes at G-018 on the TRAIN screen alone.

The crux (EXP-082): the derived adverse leg reverts to a generic `MAE_q90` stop sitting **at** the
catastrophe edge `|q05|` in a wide-stop/modest-target geometry — the CF-HA-HARAMI-001 trap reproduced.
**S2 is the binding shape-guard `ASS` cannot supply** (G-017); whether *any* exit cuts the continuous
catastrophe tail without also removing the median edge is exactly what this screen tests on TRAIN.

## Question (plain language)

Built on each substrate's own realized geometry, do the data-derived exits — or any conventional exit —
look good enough on training data, *and* survive the separability shape-guard, to be worth spending one
of the programme's two lifetime TEST reads on? If not, we learn that for free.

## Scope Boundaries

- **Data views:** the **5-year, post-INFR-003, VAL-005-admitted** 1-minute time bars
  (`data/timebars/timebars_<sym>_20210602_*_2026062*_*.parquet`, latest-glob per symbol), resampled to
  domain bars by the **holdout-fenced** `build_domain_bars` (`min_coverage=0.90` + drop any window whose
  right-labelled `CloseTime` crosses the analysis-slice boundary — VAL-005 G1). Real OHLC only. No HA /
  Renko / synthetic price enters any return, expectancy, capture, or tail metric (the harami substrates
  *detect* on HA candles but every outcome is on real prices — `RealOpen/High/Low/Close`).
- **Substrates (4, frozen; never tuned):** `SUB-AVWAP`, `SUB-HARAMI-PARTIAL-V2A`,
  `SUB-HARAMI-V2A-ADVNONE`, `SUB-RANDOM` (matched-control, seed fixed at D2). Reuse the frozen
  `xen.capgeo_substrates` entry interface (EXP-080/081); the two harami substrates share one entry
  population (asserted identity; reported individually, never pooled).
- **Universe / domains / member set:** **16 instruments × {15m, 1h, 4h}**, restricted to the **46
  EXP-080-READY instrument×domain member cells** (US500-4h, JP225-4h `COVERAGE_EXCLUDED`; no DE30).
  4 substrates × 46 cells = **184 substrate-cells**, each screened against the candidate surface below.
- **Candidate surface (frozen at this scope; the multiplicity-registry Phase 018 countable items):**
  - **Derived (3):** `D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT`, barriers from the
    **sha256-pinned `xen.capgeo_exits.derive_barriers`**, re-fit on the **screen-TRAIN region** statistics
    (same pinned function EXP-082 locked and EXP-084 will call per WF fold — causal, no human selection).
  - **Benchmark grid (full enumerated, conventional, recalibrated per substrate-cell — operator decision
    2026-06-22):** representative arms per registered branch, parameters **conventional or data-anchored
    to EXP-081 quantiles, never tuned against outcomes** (exact operationalization fixed in the analysis
    plan from these frozen definitions, reusing `xen.favourable_targets` / `xen.adverse_targets` /
    `xen.third_barrier` / `xen.capture_barriers` / `xen.position_exits` / `xen.exit_rules`):
    - `/EXIT-RR` — fixed favourable:adverse RR triple-barrier; favourable target = `R × S_adv` for the
      conventional ratio set **R ∈ {1.0, 1.5, 2.0, 3.0}**, adverse stop `S_adv = MAE_q90` (data-anchored),
      time cap = `TTP_q75`.
    - `/EXIT-TRAIL` — ATR trailing stop at conventional **k ∈ {1, 2, 3}** ATR, and a market-structure
      (ZigZag-pivot) trailing arm (`xen.zigzag` / `xen.position_exits`), each with the `TTP_q75` cap.
    - `/EXIT-VP` — volume-profile POC and value-area (70%) targets via `xen.favourable_targets.volume_profile_levels`
      (**`TickVolume` proxy — disclosed**), adverse `MAE_q90`, cap `TTP_q75`.
    - `/EXIT-PARTIAL` — the named prior-family reference arms **PARTIAL-V2A**, **V2A-ADVNONE**, and
      **AVWAP-FH** (fixed-horizon) reproduced via `xen.position_exits` / `xen.exit_rules`, plus a generic
      2-leg ≤3-split menu (favourable-side scaling).
    - `/SIZE-VOLADJ` — volatility-adjusted sizing applied as an **overlay on each exit above**, scored
      **against the raw-return (unit-size) baseline** as a hypothesis (never assumed superior).
  - The benchmark variant list is **enumerated and frozen in the analysis plan before any TRAIN read**;
    it is the candidate surface, not a swept optimisation. Refuted/blocked/inconclusive arms remain in
    the file-drawer ledger (never deleted/reused).
- **Read region (TRAIN only):** screening uses the **TRAIN sub-split** of each cell's analysis slice
  (`[0, train_cutoff)`, the same first-49%-of-file region EXP-081 read). The next-21% analysis-TEST
  stratum and the final-30% global holdout are **never sliced, materialized, inspected, counted, or
  used**, and are never made a WF fold here. (The expanding-window WF that reads the TEST stratum is
  **EXP-084's** machinery, not run in EXP-083.)
- **Global holdout:** excluded from all analysis (mandatory); never loaded, never a fold.
- **Look-ahead / causality:** every per-event outcome uses only bars at or after entry and at or before
  the resolved exit; barriers for the derived candidates are re-fit from **screen-TRAIN-only** statistics
  via the causal pinned function (no forward/cross-fold dependence). Substrate detection is the frozen,
  streaming-safe `xen.capgeo_substrates` path.
- **Cost treatment (operator decision 2026-06-22): GROSS screen.** Expectancy/median/tail are **gross**
  matched-control excess; the binding cost-calibrated floors live in the frozen referee suite, which is
  **not invoked here** (it binds at EXP-084). A dedicated per-event cost/slippage + financing layer is a
  **conditional EXP-072/073-analog follow-up**, registered at its own D0 only on a confirmed EXP-084 —
  **not** applied in EXP-083 (matches the Phase-016 EXP-071 gross-screen precedent).
- **`ASS` discovery overlay (non-binding):** `ASS` expectancy/median/tail are reported per cell as
  **disclosure only** (G-017 `DISCOVERY_ONLY`); **no screen decision rests on `ASS`.** Carry the §D6
  guards (Guard (i) defer-to-median at effective-n ≤ 60; Guard (ii) `P(>X)` slope inapplicable at
  compressed span) and the §D7 `[15,8000]` bracket (EXP-080 confirmed 192/192 IN_BRACKET) as disclosure
  context.
- **Exclusions:** no counted TEST read, no TEST-stratum slice, no holdout contact, no WF-EXPANDING run,
  no frozen-referee-suite adjudication (all EXP-084); no entry tuning (entries frozen); no barrier grid
  search or tuning of the derived candidates (barriers *are* the pinned-function quantiles); no
  cross-cell / cross-substrate pooling as a binding statistic (per-stratum default, LESSON-001; any
  aggregate is disclosure); no post-hoc candidate/cell selection after seeing TRAIN results beyond the
  pre-declared mechanical G-018a + separability rules; no `ASS`-binding decision.

## Separability gate (the binding pre-TEST shape-guard — frozen D4/D9 constants)

Both legs TRAIN-only; both must pass for a `{candidate × stratum}` to be a **valid candidate**
(constants FROZEN at the D9 bite-check GREEN, 2026-06-21):

- **(S1) Attribution separability** — additively decompose each candidate's gross expectancy into
  `X_fav` (favourable-target + time-cap contribution, adverse leg at a neutral reference) and `X_tail`
  (stop-truncation contribution), additive to machine precision (EXP-031 precedent). **PASS iff `X_fav`
  independently beats the per-cell matched-random control** (moving-block bootstrap, `CI_low > m_cell`,
  `m_cell = Q95(null CI_low)`, calibrated FPR ≤ 0.05). Edge that is entirely `X_tail` with `X_fav ≈`
  matched-random → a capture-bound/tail-truncation artifact → **FAIL**.
- **(S2) Tail non-residual** — after the candidate's exit is applied, re-measure its **own** realized
  distribution. **PASS iff** post-exit `tailmass ≤ τ_tail = 0.06` **AND** post-exit `q05 ≥ q05_control − δ`,
  `δ = 0.40` ATR, where `tailmass` = fraction of mass below `median − K_tail·MAD`, `K_tail = 3.0`. The two
  legs are complementary (tailmass catches the separated `B_zero` mode; relative-q05 catches deep `B_neg`
  catastrophes). **Operating floor `n ≥ 120`**: sub-floor cells (some 4h) get **S2 deferred + disclosed**
  (D4 default, operator decision 2026-06-22) — they may still be reported as candidates but are flagged
  `S2_DEFERRED`, and at EXP-084 their adjudication is carried by the frozen referee suite + median/tail
  disclosure. Residual `B_pos` blind spot disclosed (D9, dispositioned benign).

## Success / Failure / Inconclusive Criteria

- **`SCREEN_DELIVERED` (experiment verdict):** every member substrate-cell is screened against the full
  candidate surface; per `{candidate × stratum}` the G-018a gross legs and the separability S1/S2 legs are
  computed (or S2 deferred+disclosed below the floor); **≥1** `{candidate × stratum}` passes both gates;
  and the resulting **valid-candidate set + the pre-declared Holm-over-`{valid-candidate × stratum}` rule
  are emitted and sha256-hash-pinned** with full provenance for EXP-084. Determinism replay byte-identical.
- **`ALL_CANDIDATES_FAIL` (experiment verdict, equally valid):** the screen completes but **0**
  `{candidate × stratum}` pass both gates (empty valid set). This is a real, publishable result — it
  closes HYP-004 at G-018 with **0 lifetime TEST reads spent** and routes the family to its G-018
  disposition. Record the per-candidate failure attribution (which leg failed: gross G-018a vs S1 vs S2).
- **Cell-level INCONCLUSIVE:** a cell below the ≥30-event floor for a given candidate is
  `UNDERPOWERED_DISCLOSED` (none expected — EXP-081 had 0 underpowered cells); an S2-sub-floor cell is
  `S2_DEFERRED` (carried, disclosed). Recorded, never silently dropped.
- **Evidence AGAINST (process-level — HALT, not a result):** non-determinism on replay; any TEST-stratum
  or holdout row touched; a frozen-rule / pinned-function hash mismatch (`derive_barriers` sha256 ≠
  EXP-082); the harami-substrate entry-identity assertion failing; a real-price-discipline violation; or
  the G-018a / separability constants differing from the D4/D9 frozen values. Any halts and routes to a fix.
- There is **no edge / tradability / referee-suite-pass / confirm verdict** here (0 counted reads). Only
  TRAIN-only eligibility + the frozen valid-candidate hand-off.

## Complexity Budget

- **Max statistical-method families: ≤ 4** — (1) gross per-event expectancy/median/tail with moving-block
  bootstrap CIs (G-018a); (2) per-cell matched-random contrast CI (`SUB-RANDOM` + within-cell
  matched-random null); (3) S1 additive `X_fav`/`X_tail` decomposition + matched-control edge-call
  (`m_cell` FPR-calibrated); (4) S2 tailmass/relative-q05 shape legs. All non-parametric / bootstrap /
  matched-control; reuse `xen.capture_barriers.block_bootstrap_ci`, `xen.capgeo_geometry.tail_stats`,
  `xen.favourable_targets.paired_median_contrast_ci`.
- **Max visualisations: ≤ 5** — (i) survivor map: `{candidate × substrate × domain}` pass/fail heatmap of
  the two gates; (ii) S1 `X_fav` vs `X_tail` decomposition scatter by substrate (separable vs
  tail-truncation region); (iii) S2 post-exit `tailmass` / relative-`q05` vs the frozen thresholds, by
  candidate; (iv) gross expectancy+median (with tail flag) vs matched-random, by candidate/domain;
  (v) `ASS` discovery disclosure (expectancy/median/tail) overlay. All from the single screening pass's
  bounded outputs (no heavy reloads for plotting).
- **Max new code modules: ≤ 2** under `python/src/xen/` — at most one screening/separability harness
  (e.g. `xen.capgeo_screen`: apply an exit → gross legs → S1/S2 → valid-candidate decision) and one
  benchmark-exit definition module **only if** the existing `favourable_targets`/`adverse_targets`/
  `position_exits`/`exit_rules`/`third_barrier` cannot be composed without it. **Reuse first**;
  **import the frozen `xen.capgeo_exits.derive_barriers` unchanged** (assert its sha256). No edits to any
  frozen generator/detector/geometry/substrate/derivation module.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Event denominator:** every candidate is scored on the **identical frozen-substrate held-position
  event set** per cell (EXP-042 guard: exits never filter/select/alter the entry population — the
  denominator is fixed by the substrate, identical across all candidates). Report `n_usable` per cell;
  the ≥30-event floor gates candidate formation, never divides.
- **Expectancy / matched-control excess:** mean (and median) per-event real-price return in ATR units;
  the matched-control excess is `candidate − matched_random` on the **same events** (paired). No
  percentage-vs-zero-baseline metric is used; effects are absolute ATR-unit differences with bootstrap
  CIs, so there is no `0/0` or divide-by-zero exposure. Finite handling explicit (no silent NaN).
- **Tail metrics (S2):** `tailmass` is a fraction over `n_usable` (shown explicitly); `q05` is an ATR
  quantile; both undefined only if `n_usable < ` the S2 floor → `S2_DEFERRED`, never `0/0`.
- **`SIZE-VOLADJ`:** scored as the **difference** vs the raw-size baseline on identical events (no ratio
  against a possibly-zero raw expectancy).

## Frozen Constants (predeclared at D0/G0/D9; recorded here pre-screen)

- Separability: `K_tail = 3.0`, `τ_tail = 0.06`, `δ = 0.40` ATR, S2 floor `n ≥ 120`; S1 `m_cell = Q95(null
  CI_low)`, FPR-calibrated ≤ 0.05, `N_BOOT = 10_000`. Derivation: `derive_barriers` sha256
  `34d03f45…` (EXP-082). Event floor ≥ 30. Units: barriers/returns in **ATR** (Wilder ATR(14), EXP-081
  normalization); caps in **domain bars**. WF / referee-suite constants are **not used here** (EXP-084).
- Seeds: all RNG seeds fixed and recorded (substrate random-entry seed, bootstrap seeds); a second full
  pass is byte-identical (D10).

## Data Requirements

For each of the 46 member instrument×domain cells: load the 5-year 1-minute file (latest-glob), slice the
**first-70% analysis set**, build domain bars via the holdout-fenced `build_domain_bars`, take the
**TRAIN sub-split** (`[0, train_cutoff)`), generate the 4 substrates' entries (`xen.capgeo_substrates`),
resolve each event's real-price held-position path, apply every candidate exit (3 derived via the pinned
`derive_barriers` re-fit on this TRAIN region + the enumerated benchmark grid), compute the gross
expectancy/median/tail and the matched-random contrast (G-018a), run S1 (additive decomposition +
`X_fav` matched-control edge-call) and S2 (post-exit tailmass/relative-q05), decide valid/invalid per
`{candidate × stratum}`, and emit the frozen valid-candidate set + Holm rule + hash-pin. `tqdm` over the
(cells × candidates) loop; lazy Polars scan + column projection + first-70% slice before any heavy work;
bounded plot inputs returned by the analysis pass. Outputs (suggested):

- `results/screen_results.parquet` — one row per `{substrate × instrument × domain × candidate}`:
  `n_usable, gross_exp, gross_exp_lo, gross_med, gross_med_lo, tailmass_post, q05_post, q05_control,
  matched_excess_lo, x_fav, x_tail, x_fav_excess_lo, m_cell, s1_pass, s2_pass, s2_deferred, g018a_pass,
  valid, fail_leg, ass_exp/med/tail (disclosure)`.
- `results/valid_candidate_set.json` — the frozen surviving `{candidate × stratum}` set **+ the
  pre-declared Holm-over-grid rule**, with a sha256 over the canonicalized set (the binding EXP-084
  hand-off artifact), and the EXP-080/081/082 provenance fingerprints.
- `results/run_metadata.json` — seeds, module hashes (incl. asserted `derive_barriers` sha256), frozen
  constants, determinism replay fingerprint, `holdout_untouched: true`, `counted_test_reads: 0`,
  `candidate_slots: 0`, `test_stratum_touched: false`.

### Standard Loading Pattern (5-year data; TRAIN sub-split only; no TEST/holdout)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_<sym>_20210602_*_2026062*_*.parquet"))[-1]
scan = pl.scan_parquet(path).sort("CloseTime")
total = int(scan.select(pl.len()).collect().item())
analysis_cutoff = int(total * 0.7)                 # first 70% analysis set; final 30% holdout NEVER read
bars_1m = scan.slice(0, analysis_cutoff).collect()  # build_domain_bars(...) → domain bars (holdout-fenced)
# train_cutoff = int(len(analysis_set_rows) * 0.7); screen reads [0, train_cutoff) only.
# TEST stratum [train_cutoff, analysis_cutoff) and holdout [analysis_cutoff:] are never sliced here.
```

## Suggested Direction (non-binding)

Build one screening harness that, per cell, resolves each candidate exit's per-event real-price outcomes
once, then derives all gross legs, the S1 decomposition, and the S2 shape legs from that single resolved
path set — so plotting reuses bounded analysis outputs and nothing is re-simulated. Spend the experiment's
discipline budget on (1) asserting the pinned `derive_barriers` hash and the EXP-080/081/082 provenance
before any read, (2) the EXP-042 same-denominator invariant across candidates, (3) the harami
entry-identity assertion, (4) the **freeze + hash-pin of the valid-candidate set and Holm rule as the
binding artifact EXP-084 imports verbatim**, and (5) the byte-identical determinism replay. Keep the
derive/screen/confirm boundary clean: EXP-083 decides *eligibility on TRAIN*; only EXP-084 (if opened)
spends a counted read and lets the frozen referee suite decide.
