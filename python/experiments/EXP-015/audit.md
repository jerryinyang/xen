# EXP-015 Audit — CF-MR-005/HYP-001 ladder-harvest mechanism characterisation

**Auditor:** experiment-auditor (2026-07-03, post-fix re-run). **Artifacts:** `code/lib.py`,
`code/run_experiment.py`, `results/{summary,part_b_mechanism,part_a_anatomy}.json`, `plots/` (5).
**Verdict on trust: PASS — 0 open Critical.** Two Critical-class implementation defects were
found, fixed, and the full experiment re-executed before this report (findings C1/C2 below,
both discharged). Per-cell labels were identical before and after the fixes.

---

## 1. Scope compliance — PASS

- **Classification honored.** Analysis-only throughout. No signal/entry/fill is generated for
  P&L anywhere in Python; Part-A P&L is exclusively engine-realized fills read from
  `data/strategy_runs/EXP-014{b,c}-4h-s8-*` (read-only; nothing written there — verified: no
  write call targets `DATA_ROOT`). Part B computes *measurements* (events + conditional
  forward-return profiles), no strategy simulation, no exits (P-02 honored).
- **Universe/params verbatim.** 11 cells = design §2 (FX 7 + IDX 4), 4h only. Median_90 /
  σ_200 / z\* 1.5 / bins [1.5,2),[2,2.5),[2.5,3),[3,∞) / horizons {6,12,24,48} / de-cluster
  exit |z|<1.0 / ≥30-event power floor / block 12 / 10,000 resamples / 200 permutation
  replicates / seeds 20260703 (bootstrap), 20260704 (permutation) — all match design §2/§3/§7
  (`lib.py:56-99`).
- **Budget respected.** 4 test families (M1 Δ, M2 slope, M3 splits, permute null), exactly 5
  plots, 1 module + 1 script, no new `python/src/xen` module.
- **No scope creep.** Every result key maps to a design method (M1–M5, tripwires, §5 labels).
  No undeclared analyses.

## 2. Data handling & holdout — PASS

- **Fence.** Part B loads the 5y-era 1m file **pinned by prefix** `timebars_<sym>_20210602_*`
  (`lib.load_4h_bars`) — correct era (plain latest-glob would wrongly select the 2023-era
  file; this was caught at implementation). Filter `CloseTime < fence` **before** aggregation,
  fence = EXP-013 `ANALYSIS_END` verbatim (diffed against `tools/ctrader-cli/experiments/
  EXP-013.conf` — identical, 11/11). Post-filter assert `max CloseTime < fence`. Audited value
  (EURUSD): max 2024-08-23 20:00 < fence 2024-08-25 22:19 ✓. Fence ≈ first-49% ⇒ final-30%
  holdout untouched; no code path reads past the fence.
- **Part-A fence.** Every emission load runs `assert_run_within_holdout` +
  `validate_provenance` (fills within [Low,High] tolerance, >5% breach = hard fail) —
  re-asserted on all 87 loaded cells (design §4.2); zero failures in the run log.
- **Ordering.** All sorts by `CloseTime` / `SourceCloseTime` / `EntryTime`; no bar-index
  alignment anywhere.
- **Aggregation.** `aggregate_ohlc(period=240, min_coverage=None)` (strict) — drops partial
  windows; no boundary-fence issue by construction (dataset-reference: strict mode needs no
  fence).
- **NaN.** Warmup nulls excluded via finiteness checks in `extract_events`/`build_strata`;
  fence-censored horizons return NaN and are excluded + counted (`n_measured` per cell/bin/h).

## 3. Causal-provenance & leak pass — PASS

**Provenance trace (verdict-bearing quantities, Part B):**

| Quantity | Definition site | Inputs at decision/measure time |
|---|---|---|
| S, σ, z | `lib.build_series` (rolling on closed bars) | value at index i uses bars ≤ i only |
| event trigger | `lib.extract_events` loop — reads `z[t-1]`, `s[t-1]`, `drift[t-1]` | strictly ≤ t−1; fires at open of bar t |
| frozen anchor / \|S\| | `abs(s[t-1])` captured into the event row | frozen at event time; never refreshed |
| R_h | `lib.recovery` — `dir·(logOpen[t+h] − logOpen[t])/|S_{t-1}|` | open-to-open from the action-bar **open**; forming bar's OHLC never read |
| matching features | `build_strata` — `vol[t-1]`, `abs_ret[t-1]`, `s[t-1]` (explicit shift) | ≤ t−1 |
| control R_h | `control_recovery` — control's own `s[c-1]`, opens c..c+h | ≤ c−1 / forward opens |

No `rct[di]`-pattern anywhere; no bar's own close used as its intrabar reference. Part-A
`assemble_realized_bps` (`lib.py`) is a transcription of the audited EXP-014c function
(same formula, verified line-by-line against `EXP-014c/code/lib.py:137-158`): realized_bps[t]
reads pos[t], RealOpen[t]/[t+1], and the engine's own emitted fills — no future bar, no Python
fill recompute (L-01/P-09 clean).

**Leak tripwire (binding, L-07).** Block-permuted-returns null (block 12, 200 replicates, seed
20260704), full M1 pipeline per replicate, per (cell, bin). Result: the measured ΔR_24 sits
**inside** the permuted 95% band in 41/44 (cell,bin) reads. The 3 exceedances (GBPUSD bin3
0.413 > 0.335; USDJPY bin3 0.369 > 0.304; AUDUSD bin4 0.482 > 0.414) are all **UNPOWERED**
bins (n = 13/22/6 < 30) and 2 of 3 have bootstrap CIs straddling 0 — no admissible edge exists
to survive or collapse, so no REJECT-class survival. Collapse fractions disclosed per
(cell,bin) in `plots/collapse_fractions.png` + `results/part_b_mechanism.json` (W3/L-15
satisfied). Null design is return-permutation, not path-rotation (L-07) and no
signal-derived-target null exists (L-08).

**Price-primary check.** N/A by classification — and verified: no vectorized strategy backtest
exists in the code (the only P&L assembly is on emitted engine fills).

**Shared modules.** No `python/src/xen` module was created or modified; `xen.bar_aggregator`,
`xen.signals.ingestion`, `xen.referee_adaptive.adaptive_cost_bps_for` used read-only per their
existing contracts.

## 4. Numerical spot checks — PASS

Manual re-derivation, EURUSD, 6th bin-2 event (t = event bar index):

- S from raw log-closes via `np.median(logc[t-90:t])`: **−0.0295415059** = lib `abs_s` ✓
- z via independent per-bar rolling-median σ reconstruction: **−2.2561951296** vs lib
  `z[t-1]` −2.2561951296 (Δ ≈ 3e-15) ✓
- R_24 by direct open-log arithmetic: **−0.5322543277** = `lib.recovery` ✓
- Part-A EURUSD e0/extend/z15: 749 legs, L0 n=328 mean +7.68 bps/leg, ≥2-leg overlap share
  0.81, cost stress 2.93/2.70/2.47 bps at 1/2/3× — all internally consistent, magnitudes
  plausible vs the EXP-014c audited tables.
- Determinism: frozen seeds throughout (`default_rng([SEED, cell_idx])`); the post-fix re-run
  reproduced every per-cell label and every M1 point estimate exactly (slope point estimates
  unchanged; only slope CIs moved, as expected from the C1 fix).

## 5. Verdict forensics

**Per-stratum re-derivation & masking check.** The binding outputs ARE per-stratum: one label
per (cell), one CI per (cell, bin, h); the only family-level figures are **counts** of
per-cell labels (`summary.json`), never a pooled statistic — L-03 satisfied, nothing to mask.
Re-read of all 44 (cell,bin) ΔR_24 CIs confirms the label logic fired correctly:

- **Powered stratum (bin 1, n 32–62, 10 cells):** every ΔR_24 CI straddles 0 except **US2000,
  which is significantly NEGATIVE** (−0.295, CI [−0.443, −0.007]) — anti-recovery vs matched
  control. No cell separates positively.
- **Depth strata (bins 2–4):** 0/33 reach the 30-event floor (max n = 28). Every deep-bin read
  is UNPOWERED by the design's own denominator rule — reported, never FAIL.
- **JP225:** 14 bin-1 events ⇒ UNPOWERED overall (correct per design §3).

**Mechanism statement (why the verdict came out this way).** Two concrete drivers:

1. **Event scarcity is itself the finding.** The basket-free own-price trigger produces only
   ~30–60 de-clustered episodes/cell over 3.2y, vs ~750 engine legs in the same cells'
   EXP-014b extend runs. `S = logP − Median_90(logP)` on own price is slow-moving (the median
   trails the price), so |z|≥1.5 episodes are long and rare once de-clustered. The engine
   ladder's entry cadence was therefore supplied by the **basket construction** (S8 spread
   volatility), not by own-price dislocation frequency — the design's premise that the field
   P&L lives at own-price dislocation depth gets no native event mass to stand on.
2. **No conditional recovery at any powered read.** Where power exists (bin 1), median paired
   ΔR_24 ∈ [−0.30, +0.13] and straddles 0 in 9/10 cells (negative-significant in the 10th).
   M2 slope CIs straddle 0 in 11/11 cells. The depth-graded reversion premise has no support
   in the powered region.

**M3 attribution (disclosure, engine-realized):** ≥2-leg overlap share of net P&L = 0.34–0.83
(median ≈ 0.68) — the field P&L is dominantly a *scale-in-dependent* object. Shift-twin L0
collapse fractions are wildly heterogeneous (median 0.33, range −125 to +10 across 22 cells —
small-denominator cells explode the ratio; per-cell values disclosed, binary reads nowhere
used, L-15 satisfied). Deepest-decile episode P&L share is unstable across cells (−1.6 to
+3.3), i.e. several cells' entire net P&L (and more) sits in the deepest-decile episodes while
others are tail-negative — consistent with a tail-funded, exposure-flavored P&L rather than a
uniform harvest.

**Gate-shape check.** Three honest limits of the vehicle — recorded for the interpreter, not
retro-edited:

1. **Median fraction-recovered is a location read.** A hit-rate-shaped or tail-shaped
   reversion (e.g. most episodes recover slightly, a few blow out) could sit at median ≈ 0 vs
   control. The M1 estimand is the design's own ladder-native choice (L-13), but "NO_SEPARATION
   on the median" is not proof of "no effect of any shape."
2. **The M3b drift split is structurally degenerate** (design-inherited): drift is the trailing
   90-bar return and the trigger is dislocation vs the 90-bar median — a deep dislocation
   mechanically implies opposite-sign trailing drift, so the with-drift class is nearly empty
   (n = 0–4 per cell vs 36–111 against-drift). The split cannot discriminate
   exposure-vs-reversion as designed; it constrains nothing here (no cell reached the
   supported path where it binds). Any follow-up needs a drift window decoupled from the
   anchor window.
3. **Deep bins are unpowered by event scarcity, not by noise** — the family's core premise
   (monotone depth gradient) was structurally untestable at bins 3–4 in this window. That is
   an event-mass fact about the trigger, not an implementation artifact.

## 6. Findings

| # | Class | Finding | Disposition |
|---|---|---|---|
| C1 | **Critical (fixed + re-run)** | `slope_ci` (run_experiment.py) resampled bootstrap blocks via a `set` — multiplicity lost, invalid block bootstrap for the M2 slope CI (a predeclared statistic). | Fixed (multiplicity-preserving resample); full re-execution 2026-07-03. Labels/point estimates unchanged; slope CIs now valid — all 11 straddle 0. |
| C2 | **Critical (fixed + re-run)** | `running_max_recovery` (lib.py) evaluated fence-truncated horizons as full 48-bar windows — an event near the fence could be falsely counted "never recovered within 48" in the M4b census. | Fixed (partial windows → NaN, counted censored); re-run. Census denominators now honest. |
| W1 | Warning | Matching-strata quantile edges (vol terciles, \|ret\| deciles) are computed over the cell's full fenced sample, including bars after a given event. **Materiality:** the strata define the *control design*, not any decision or signal; both event and control legs face identical edges; no verdict-bearing value at time t reads future prices. Cannot move a verdict — documented. | Document-and-proceed. |
| W2 | Warning | M3b drift split degenerate (see gate-shape §5.2) — design-inherited (design §3 specifies the 90-bar drift window). Does not bind on any cell in this outcome (no cell reached the supported path). | Record for interpreter; any follow-up must decouple the drift window from the anchor window. |
| W3 | Warning | Control R_h uses the control bar's own \|S_{c−1}\| denominator; near-anchor controls give large-magnitude R. **Materiality:** the paired statistic uses the *median* of 20 controls per event and the median across events — spot-checked distribution shows no blow-up dominating any median; a denominator floor would be a post-hoc choice. | Document-and-proceed. |
| I1 | Info | Part-A emission `EXP-014c-4h-s8-e2-extend-z15` missing US500 (pre-existing gap in the 014c run set, also logged NO_DATA there). 87/88 Part-A cells loaded. | None. |
| I2 | Info | Deep-bin (2–4) events nearly all below the 30-event floor — event-scarcity mechanism, see forensics. | Interpretation input. |

## 7. Audit conclusion

Implementation faithful to the frozen design; fence and provenance clean; tripwire executed
and disclosed; both verdict-material defects fixed and the experiment fully re-executed;
per-stratum labels stand. The result set is trustworthy for Stage-5 interpretation:
**0 supported cells / 10 powered NO_SEPARATION (one significantly negative) / 1 UNPOWERED**,
with the family-level reading (retire vs inconclusive routing per design §1 vs §5) left to the
interpreter as required.
