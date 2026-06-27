# Audit Report: Experiment EXP-074

TRAIN-only substrate-wide loser-tail characterization of the 99-cell MA-native N-PARTIAL-V2A
harami (CF-HA-HARAMI-001 / HYP-027).

## Summary

- **Verdict**: CONDITIONAL PASS (code correct & fences intact; two interpretation-critical
  findings must be carried into Stage 6, plus one housekeeping item)
- **Critical Issues**: 0
- **Warnings**: 2
- **Info Notes**: 3

The implementation is numerically faithful to the analysis plan: the TRAIN/TEST/holdout fence
holds, real-price outcome discipline is intact, the statistics reproduce known closed-form
values, the run is deterministic, and all 99 cells resolved (237,698 events, no empty cells). The
binding per-domain verdicts in `domain_verdict.json` are computed correctly **under the
pre-registered candidacy definition**.

**However, the operator's caution is well-founded and is the headline of this audit:** the
binding "no uniform lever / NO_SEPARATOR" reading does *not* mean H1 is refuted. The H1 lead
(`msofar_atr`, exhaustion magnitude) is a **near-universal separator of the extreme q05 loss tail**
— the exact tail that produced the EXP-071 raw-mean<0 problem — yet it registers as **0 candidate
cells** purely because the all-framing consistency gate is structurally blind to tail-only effects.
This must lead the interpretation, not be buried under the pooled `NO_SEPARATOR`.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Resolution mirrors EXP-071 with the TRAIN mask only; alignment hard-checked (`np.allclose(res.r_full[qual][order], res.r_e)`, line 291). |
| `code/run_experiment.py` | Edge cases | PASS | Empty cells, undefined state/strong-stat (`bad_state`, `~ss["defined"]`), zero-denominator guards in `phi_binary`/`cramers_v`/`kruskal_epsilon_sq`, `n<POWER_FLOOR` CI short-circuit all handled. |
| `code/run_experiment.py` | Type safety | PASS | Type hints + docstrings on all public functions; dataclass `CellEvents` frozen. |
| `code/run_experiment.py` | NaN handling | PASS | Per-feature `_clean_pair` / `np.isfinite` masking; undefined features set to NaN explicitly, never imputed; coverage counts recorded. |
| `code/run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` slices `[0, train_cutoff)` only; TEST + holdout never sliced/collected (see Numerical Validation). |
| `code/run_experiment.py` | Loader ordering | PASS | Lazy `scan_parquet().select(cols).sort("CloseTime")` before `.slice`; `is_sorted` assertion (line 155); domain bars re-asserted strictly increasing (line 264). |
| `code/run_experiment.py` | Memory/performance | PASS | Column projection on scan; per-cell TRAIN slice collected only; plots reuse in-memory `events`/`rank_df` (no reload); bounded `N_BOOT`. |
| `code/run_experiment.py` | Safe optimization | PASS | No vectorization alters sample membership/temporal order; per-event Python loops in `strong_stat_detail`/`trailing_pctile` are genuinely causal/sequential and bounded. |
| `code/run_experiment.py` | Progress tracking | PASS | `tqdm` on the 99-cell loop; concise `tqdm.write` per cell. |
| `code/run_experiment.py` | Logging/output | PASS | Helpers return data; orchestration prints a concise per-domain summary. |
| `code/run_experiment.py` | Organization/import side effects | PASS | imports → path → constants → types → I/O → pure compute → plotting → orchestration → `main`; dirs created in `run()`, not at import; `Agg` backend. |
| `code/run_experiment.py` | Plot data reuse | PASS | All 6 plots consume computed tables/`events`; no heavy reload. |
| `code/run_experiment.py` | Docstrings | PASS | Module + function docstrings with semantics and causality notes. |

## Numerical Validation

### Spot Checks

**Statistics (re-derived against known cases):**
- `rank_biserial`: perfect separation (tail group strictly higher) → r=+1.0, AUC=1.0 ✓;
  reversed → sign flips correctly ✓.
- `spearman_loss`: strictly increasing feature vs `r_e` → −1.0 (loss-oriented) ✓.
- `_rankdata`: tie-averaging matches `scipy.stats.rankdata("average")` construction ✓.
- `kruskal_epsilon_sq` / `cramers_v`: closed-form H and χ² with the documented epsilon²/V
  normalizations; zero-margin and single-category guards present ✓.

**TRAIN/TEST/holdout fence (focus area 1):**
- `train_cutoff = int(int(total*0.7)*0.7)` ⇒ first ~49% of each file, strictly inside the analysis
  set; the next-21% TEST band and final-30% holdout are never sliced or collected. The forward
  resolver operates on domain bars built from the TRAIN 1-minute slice, so boundary entries censor
  at the TRAIN edge (`res.data_censored`) — no TEST/holdout row is reachable. PASS.
- *Note (Info I2):* `scope.md §Data-View Comparison` says `round(0.7×round(0.7×total))`, but the
  code uses `int()` per the frozen EXP-068/071 convention and the scope's own *Standard Loading
  Pattern* (`int(total*0.7)`). `int` truncates downward → strictly more conservative (smaller
  TRAIN), so the fence is safe; only the doc wording is inconsistent.

**Real-price outcome discipline (focus area 2):** `r_e` is the certified `exp068.signal_arm`
realized N-PARTIAL-V2A return (real prices, inherited from EXP-068). Heiken Ashi is used only in
`harami_directions` for detection (directions/body sizes), never for returns. PASS.

**Feature `favdist_atr` collinearity (focus area 3) — see Warning W1:** verified
`favdist_atr / msofar_atr = 0.5` exactly, zero variance, every event (GBPUSD-5m). `fav_dist ≡
0.5·m_sofar` is a *structural identity* of the V2A geometry (partial barrier at half the
move-so-far), not random collinearity and not a return-side bug. Because rank statistics are
scale-invariant, `favdist_atr` yields byte-identical rank-biserial/Spearman effects and CIs to
`msofar_atr` in every cell (hence the identical `0.7052309183979011` medians).

**H1 lead 0-candidate behaviour (focus area 4) — see Warning W2:** confirmed the only failing gate
is **cross-framing sign consistency**, not the CI. `msofar_atr` TA_q05 effect is strongly positive
(e.g. GBPUSD-5m 0.680, EURUSD-15m 0.680, BTCUSD-1h 0.724, XAUUSD-30m 0.799) while TA_neg/TB_median/TC
are ~0 or sign-flipped. On the TA_q05 framing alone the effect clears 0.15 in **100% of powered cells
in every powered domain** (5m/15m/30m/1h), median 0.70–0.79, minimum 0.60. The candidacy gate
(`_is_cell_candidate`, lines 640–652) requires identical sign across all four framings, which a
tail-only effect cannot satisfy.

### Range Checks

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Cells resolved | 99 | 99 (no empty) | YES |
| Total events | > 0 | 237,698 | YES |
| Powered cells | per-domain ≥30 q05 | 5m=17,15m=17,30m=17,1h=16; 2h/4h=0 (→INCONCLUSIVE) | YES |
| Pooled powered | matches metadata | 67 = `pooled_n_powered_cells` | YES |
| Rank-biserial / phi / Spearman | [−1, 1] | within range | YES |
| Cramér's V / eps² | ≥ 0 / [0,1]-ish | within range | YES |

### Statistical Sanity

| Statistic | Value | Sensible? | Notes |
|-----------|-------|-----------|-------|
| `msofar_atr` TA_q05 breadth | 100% powered cells, all domains | YES | H1 confirmed for the extreme tail; the binding metric just doesn't credit tail-only effects. |
| Per-domain verdicts | 5m NO_SEPARATOR; 15m/30m/1h SEPARABLE_NO_UNIFORM_LEVER; 2h/4h INCONCLUSIVE_POWER | YES | Matches sep_rate (0.35/0.88/0.71/0.94) and the <5-powered rule. |
| Pooled (disclosed-only) | NO_SEPARATOR | YES but misleading | Pools 5m noise + underpowered tails; correctly non-binding. |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Rank-biserial / Spearman / Kruskal | Rank-based, distribution-free (heavy left tail) | YES | Appropriate for the fat-tailed `r_e`; no mean/normal-theory statistic used. |
| Moving-block bootstrap | Local serial dependence among clustered events | PARTIAL/OK | Block `b=round(n^{1/3})`; approximate within-TRAIN stationarity, acceptable for a descriptive CI. |
| All-framing consistency as anti-p-hacking guard | Genuine separators are distribution-wide monotone | **DOES NOT HOLD for tail-shape effects** | H1 is a real tail-only mechanism; the guard rejects it by construction (W2). |

## Results Plausibility

Outputs are internally consistent and within domain ranges. The stratified per-domain structure
(15m–1h separable; 5m noisier; 2h/4h underpowered) is the intended read and is correctly computed.
The pooled `NO_SEPARATOR` is correctly flagged `disclosed_only` and non-binding.

## Scope Compliance

- Analysis plan followed: YES (per-domain dual-metric verdict; pooled disclosed-only; GBPUSD-5m as
  continuity cell; 14-feature set; three tail framings; block bootstrap).
- Deviations: none material. (Doc/code `int` vs `round` wording, I2.)
- Complexity budget: 3 stat families + bootstrap (≤3 ✓); 6 plots (=6 ✓; **but one orphan stale
  plot present**, I1); 1 module (=1 ✓).
- Holdout exclusion verified: YES.
- Determinism (focus area 6): integer-only seeds (`[BASE_SEED, cell_index, fi, 0]`,
  `[BASE_SEED, 7770, seed_idx]`); no `hash()` on labels. PASS.
- Helper consistency (focus area 4/5): `domain_aggregate` and `substrate_aggregate` both call the
  same `_feature_breadth`/`_is_cell_candidate`; per-cell `adjudicate` (2 gates: consistency + point)
  feeds `sep_rate`, breadth adds the 3rd CI gate — intentional per pre-exec review, not divergent.

## Issues

### Warning

1. **`favdist_atr` is a deterministic 0.5× rescale of the H1 lead `msofar_atr` — not an
   independent feature.**
   - File: `code/run_experiment.py`, lines 313–318 (`"favdist_atr": ma["fav_dist"]/atr_entry` vs
     `"msofar_atr": m_sofar/atr_entry`).
   - Description: `fav_dist ≡ 0.5·m_sofar` by V2A construction (verified ratio = 0.5, zero variance,
     all events). Rank statistics are scale-invariant, so `favdist_atr` produces identical
     effects/CIs to `msofar_atr` in every cell.
   - Impact: the "14-feature surface" is effectively **13 distinct rank-orderings**; `favdist_atr`
     must **not** be read as independent corroboration of H1 — it *is* H1. No verdict changes
     (neither is a uniform lever), so this is interpretation hygiene, not a result error.
   - Fix (documentation, not re-run): Stage 6 must state f5 ≡ 0.5·f1 and collapse them; EXP-075
     should drop `favdist_atr` as a redundant lever.

2. **Binding candidacy gate is structurally blind to tail-only effects → "no uniform lever" must
   not be read as "H1 refuted".**
   - File: `code/run_experiment.py`, lines 640–652 (`_is_cell_candidate`) and 558–578 (`adjudicate`),
     requiring identical `loss_direction` across `TA_q05 / TA_neg / TB_median / TC`.
   - Description: `msofar_atr` (H1) separates the **extreme q05 tail** in 100% of powered cells
     (median effect 0.70–0.79, all domains) but has ~0/opposite effect on the all-losers, median,
     and continuous framings — because high exhaustion drives the deepest losses *and* lifts the
     typical/median return. The pre-registered all-framing consistency rule therefore disqualifies
     it, yielding 0 candidate cells and "no uniform lever" everywhere.
   - Impact: the binding metric understates the single strongest, most robust, most actionable
     signal in the data — and it is precisely the q05 tail that produced the EXP-071 raw-mean<0
     motivation. Reading the verdict literally would wrongly route CAND-001 toward "close the path."
   - Fix (interpretation/routing, not a code bug): Stage 6 must lead with the **TA_q05-only H1
     breadth** (forest of `msofar_atr` TA_q05 effects across powered cells) as the primary evidence,
     and frame the binding verdict as "no *distribution-wide-monotone* uniform lever," explicitly
     distinguishing tail-shape from location effects. EXP-075 should target an exhaustion *cap*
     designed against the q05 tail, with the consistency gate relaxed to the tail framing for the
     pre-registered lead.

### Info

1. **Orphan stale plot `02_separator_share.png` (timestamp 02:28, pre-rerun pooled version).**
   - The current run writes `02_domain_breadth.png` (03:38); `02_separator_share.png` is a leftover
     from the earlier pooled-verdict run and is not produced by the current code. Delete it to keep
     the 6-plot budget unambiguous.

2. **`scope.md` `round(...)` vs code `int(...)` for the TRAIN cutoff.** Harmonize the wording; the
   `int` form is the frozen EXP-068/071 convention, fence-conservative, and not a defect.

3. **Two-gate vs three-gate candidacy is intentional.** Per-cell `adjudicate` (consistency + point
   ≥ bar) drives `sep_rate`; breadth `_is_cell_candidate` adds the 1σ-CI-material gate. Confirmed
   consistent with the pre-execution review note; no divergent logic between domain and pooled paths.

## Re-Audit Requirements

No code re-run required — results are numerically trustworthy. The two Warnings are **binding
inputs to Stage 6 interpretation and the EXP-075 routing**, not code fixes:
1. Treat `favdist_atr` as ≡ 0.5·`msofar_atr` (collapse; 13 effective features).
2. Lead the interpretation with the TA_q05-only H1 breadth; do not read the binding "no uniform
   lever / NO_SEPARATOR" as H1 refutation.
Recommended housekeeping: remove the orphan `plots/02_separator_share.png`; harmonize the
`int`/`round` doc wording.
