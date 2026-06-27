# Analysis Plan: Experiment EXP-054 — Intrabar Fill-Model Correction (Benchmark Capture Re-Read vs EXP-049 Worst-Case Tie-Break)

## Objective

Quantify how much of the EXP-049 benchmark capture null (`r ≈ 0.50`, 0-of-99 VIABLE, worst-case
same-bar tie-break) is an **artifact of the blanket-adverse fill assumption** versus a genuine
symmetric-path property, by re-resolving the **identical** EXP-049 benchmark events / barriers / cells
under the **P15 path-ordered intrabar fill model** (bullish bar `Close ≥ Open`: `Open→Low→High→Close`;
bearish bar `Close < Open`: `Open→High→Low→Close`). This is HYP-007, the Phase-010-carried "dedicated
fill-rule method validation."

**Binding comparison endpoint:** first-hit capture rate `r = FAV/(FAV+ADV)` on the **primary G1
distance geometry** — apples-to-apples with EXP-049's readout. **Disclosed secondaries:** the same on
the G2 retracement geometry; the P14 **median per-event gross ATR-normalised expectancy** under *both*
fill rules; per-cell same-bar double-touch exposure.

**Family-material rule (operator-ratified, predeclared):** the benchmark **flips materially** iff,
under P15, the primary G1 read **meets P11** (≥ 5 VIABLE cells over ≥ 3 instruments) where EXP-049 had
0/99 → `014-B-design.md` §8 SUBSTRATE/METHOD_DEFECT (re-baseline the benchmark on P15 before G2). A
per-cell `TIE_BREAK_SENSITIVE` flag fires iff its VIABLE status flips (NOT_VIABLE→VIABLE under P15)
**OR** `Δr = r_P15 − r_EXP049 ≥ 0.05`.

**Structural fact stated before data contact (a correctness anchor, not a result).** The tie-break can
touch **only** same-bar fav∧adv double-touch events. The first bar with *any* hit is identical under
both resolvers (verified: `xen.capture_barriers._scan_window` and `xen.expectancy._scan_path` both
return on the first bar with a hit; single-touch bars resolve identically; only tie bars can differ).
Therefore, per cell and geometry:

- `resolved_P15 == resolved_EXP049` **exactly** (same events resolve; a tie resolves under both rules);
- a tie is reassigned ADV→FAV under P15 iff `(rd=+1 ∧ bearish bar)` or `(rd=−1 ∧ bullish bar)`; never
  FAV→ADV;
- hence `FAV_P15 ≥ FAV_EXP049`, `ADV_P15 ≤ ADV_EXP049`, and `r_P15 ≥ r_EXP049` over a **fixed**
  denominator. `Δr ≥ 0` is mandatory; any cell with `Δr < 0`, `FAV_P15 < FAV_EXP049`, or
  `resolved_P15 ≠ resolved_EXP049` is a **METHOD_DEFECT** (implementation bug), not a finding.

## Reuse Map (no new modules — scope budget: 0)

| Need | Reused symbol | Notes |
| --- | --- | --- |
| TRAIN F01 loader, domain build, cell loop, heatmaps | EXP-049 `run_experiment.py` orchestration pattern | Same INSTRUMENTS/DOMAINS order, `cell_index` enumeration, `BASE_SEED=20260614`, `GEOM_G1=1/GEOM_G2=2`, `MEMBER_STATUSES`, F01 prefix slicing. **Identical** to EXP-049 so the reconciliation leg reproduces EXP-049's RNG. |
| Domain aggregation | `xen.bar_aggregator.aggregate_ohlc` | 5m strict; 15m/30m/1h/2h/4h `min_coverage=0.90`. |
| ZigZag substrate + per-confirm ATR | `xen.zigzag.generate_zigzag` | Frozen Wilder ATR(14), `ATR_MULT=1.0`. Provides `ConfirmClose` (entry `C`) and **`ATRAtConfirm`** (= `ATR_entry` for P14). |
| Confirm-bar indices | `xen.capture_barriers.confirm_indices` | Maps `ConfirmTime`→domain-bar index. |
| Adaptive P4 time cap | `xen.capture_barriers.time_caps` | Identical to EXP-049 (confirm-index durations). |
| **Benchmark barriers (G1+G2)** | `xen.capture_barriers.build_barriers` | From confirmed-move magnitude `M = |E−S|` (LOOKBACK=1). **Not** `xen.expectancy.benchmark_barriers` (that uses `M_sofar` for the harami-anchored EXP-053 object). |
| **Worst-case leg (reconciliation)** | `xen.capture_barriers.resolve_first_touch` | Reproduces EXP-049 same-bar→ADVERSE. |
| **P15 leg (experimental)** | `xen.expectancy.resolve_path_ordered` | Path-ordered class + exit price. Needs `Open`/`Close` (in addition to `High`/`Low`). |
| `r`, CI, viability per geometry | `xen.capture_barriers.summarize_geometry`, `viable_status`, `block_bootstrap_ci` | Applied to **both** class arrays. |
| Median-expectancy disclosure | `xen.expectancy.realised_returns`, `qualifying_mask`, `bootstrap_median_distribution`, `median_ci` | `entry_close=ConfirmClose`, `atr_entry=ATRAtConfirm`. |
| P11 composition / sensitivity readout | EXP-049 `_compose` / `_relaxed` pattern | Applied to the P15 viability statuses. |

Only **two new orchestration-local helpers** (in `code/run_experiment.py`, allowed by scope — "a
per-cell capture-read helper may live in the experiment script"; no `src/xen` module added):
1. `worstcase_exit_prices(classes_wc, fav, adv, confirm_idx, n_event, close, n_bars)` — maps the
   worst-case class array to exit prices (`FAV→fav_target`, `ADV→adv_target`,
   `TIMECAP→close[min(confirm_idx+N, n_bars−1)]`, `DATA_CENSORED→NaN`) so the worst-case expectancy
   leg uses the identical fill convention as P15;
2. `first_touch_tie_flags(open_, high, low, close, confirm_idx, fav, adv, rd, n_event, defined, n_bars)`
   — a bounded causal scan returning a per-event bool: `True` iff the resolving (first-hit) bar was a
   same-bar double-touch. **Diagnostic only** — it does not decide outcomes (the P15 resolver already
   did). Cross-check invariants (audit): `was_tie ⟹ event resolved`; `{reassigned events} ⊆ {ties}`.

## Methodology

### Step 1 — Reconstruct the EXP-049 benchmark per cell (frozen; identical inputs)

- **Method:** for each EXP-049 member cell (the 99-cell grid = 17 instruments × {5m,15m,30m,1h,2h,4h}
  minus US500-4h, JP225-2h, JP225-4h, read from `EXP-048/results/readiness_map.csv` →
  READY ∪ READY_FLAGGED), load the TRAIN 1-minute prefix (F01: first `int(int(total_rows·0.7)·0.7)`
  file-order rows; full file never sorted/collected; TEST + final-30% holdout never read), aggregate
  the domain, fence to `train_end_ts`, run `generate_zigzag`, compute `confirm_indices`, `time_caps`,
  `build_barriers` (G1+G2). This reproduces the exact EXP-049 event population and barrier arrays.
- **Why:** the comparison is only valid if every input except the tie rule is byte-identical to
  EXP-049. Reusing the same functions + constants + RNG indexing guarantees it.
- **Simpler alternative considered:** read EXP-049's stored per-event outcomes directly. Rejected —
  EXP-049 persisted only per-cell aggregates (`per_cell_capture.parquet`), not per-event class/bar, and
  did not store exit prices; we must recompute per-event anyway for P15 and expectancy. Recomputation
  *plus* reconciliation (Step 5) is strictly stronger.
- **Assumptions:** EXP-049 machinery is deterministic (audit PASS confirms). Holds.
- **Expected output:** per cell — `confirm_idx`, `ConfirmClose`, `ATRAtConfirm`, `rd`, `n_event`,
  `g{1,2}_defined`, `g{1,2}_fav/adv` arrays; `O/H/L/C` domain arrays.

### Step 2 — Dual-fill resolution in one pass (worst-case + P15)

- **Method:** resolve each geometry **twice** over the same forward window
  `[confirm_idx+1, min(confirm_idx+N, n_bars−1)]`:
  - **worst-case:** `classes_wc = resolve_first_touch(high, low, confirm_idx, fav, adv, rd, n_event,
    defined, n_bars)`;
  - **P15:** `classes_p15, exit_px_p15 = resolve_path_ordered(open_, high, low, close, confirm_idx,
    fav, adv, rd, n_event, defined, n_bars)`;
  - `was_tie = first_touch_tie_flags(...)` (diagnostic exposure).
- **Why:** the two resolvers share every input but the tie rule. Resolving in the same pass keeps the
  reconciliation and the comparison exactly aligned.
- **Assumptions / causality:** both resolvers are explicit bounded sequential scans (never vectorized —
  their causal/streaming semantics are the object under test); the P15 path uses only the resolving
  bar's own `O/H/L/C` (no look-ahead). Forward windows clipped to the TRAIN edge.
- **Expected output:** per event — `classes_wc`, `classes_p15`, `exit_px_p15`, `was_tie`, for G1 and G2.

### Step 3 — Capture-rate endpoint `r` under both rules (binding: G1)

- **Method:** `summarize_geometry(classes_*, defined, rng)` → `GeometryResult` (FAV/ADV/resolved/`r` +
  regime-clustered moving-block bootstrap CI). The worst-case leg uses the **exact EXP-049 RNG**
  `np.random.default_rng([BASE_SEED, cell_index, geom_id])`; the P15 leg uses a **distinct documented
  stream** `np.random.default_rng([BASE_SEED, cell_index, geom_id, 15])` so the two CIs are independent.
  Compute `Δr = r_P15 − r_EXP049` per cell. `viable_status` (P12: `r ≥ 0.55 ∧ CI_low > 0.50 ∧
  resolved ≥ 30`) under each rule.
- **Why this method (the 1 statistical test):** the regime-clustered moving-block bootstrap (block
  `b = max(1, round(m^{1/3}))`, `ceil(m/b)` contiguous blocks, `N_BOOT=10_000`, fixed seed) respects
  the serial dependence of sequential alternating moves and is distribution-free. It is the frozen
  EXP-049/EXP-027 layer — reused unchanged for comparability. A one-sided 95% lower bound is the
  binding viability gate.
- **Simpler alternative considered:** a binomial / Wald CI on `r`. Rejected — assumes independent
  Bernoulli events; the alternating-move sequence is serially dependent. Already settled in EXP-049.
- **Assumptions:** exchangeability of blocks under the null; appropriate for weakly-dependent
  sequences. Same assumption EXP-049 made.
- **Expected output:** per-cell `r_EXP049`, `r_P15`, `Δr`, both CIs, viability status under each rule;
  G1 (binding) and G2 (disclosed).

### Step 4 — P14 median-expectancy disclosure under both fill rules

- **Method:** per event, `exit_price` = `worstcase_exit_prices(...)` for the WC leg and `exit_px_p15`
  for the P15 leg; `realised_returns(classes, exit_price, entry_close=ConfirmClose, rd,
  atr_entry=ATRAtConfirm)`; `qualifying_mask` (FAV/ADV/TIMECAP with finite exit and `ATR>0`) selects
  the P14 denominator; `E_cell = median` over qualifying returns; CI via
  `bootstrap_median_distribution` + `median_ci` (distinct documented RNG stream, e.g. `[...,'exp',rule]`).
  Report `E_cell` and its CI for **both** fill rules per cell.
- **Why:** honours the mandatory-reading rule (d) — the result is legible on the family's binding P14
  endpoint — while keeping `r` as the binding *comparison* metric (the EXP-049 readout). Reuses the
  same block-bootstrap family (no new inferential method; the statistic is the median).
- **Assumptions:** same block-bootstrap exchangeability; median chosen for robustness to the fat-tailed
  per-event return distribution (P14 rationale).
- **Expected output:** per-cell `E_cell_wc`, `E_cell_p15`, both CIs, qualifying-event counts; the
  expectancy `Δ` (P15 − WC) is disclosed (expected ≥ 0, same monotonicity logic — ties that flip
  ADV→FAV raise both `r` and expectancy).

### Step 5 — Reconciliation, monotonicity & determinism gates (binding correctness)

- **EXP-049 reconciliation gate:** for every member cell, the **worst-case leg** must reproduce
  EXP-049's `g{1,2}_fav`, `g{1,2}_adv`, `g{1,2}_resolved` (exact integer) and `g{1,2}_r`,
  `g{1,2}_ci_low_1s`, `g{1,2}_ci_lo_2s`, `g{1,2}_ci_hi_2s` (full float precision, identical RNG) read
  from `EXP-049/results/per_cell_capture.parquet`. Emit `reconciliation.csv` (per-cell max abs diff +
  exact-match bool); any mismatch → **METHOD_DEFECT** halt (report, do not paper over).
- **Monotonicity gate:** assert per cell/geometry `resolved_P15 == resolved_wc`, `FAV_P15 ≥ FAV_wc`,
  `Δr ≥ 0`; the reassigned set `{classes_wc==ADV ∧ classes_p15==FAV}` must equal `{classes_wc ≠
  classes_p15}` and be a subset of `{was_tie}`. Any violation → METHOD_DEFECT.
- **Determinism replay:** run the full per-cell computation (both legs, both geometries, expectancy,
  tie flags) **twice** with identical seeds; compare frame-identical (classes, exit prices, `r`, all CI
  bounds, `E_cell`, `was_tie`, invariant counts). Any difference → METHOD_DEFECT.
- **Invariant battery (re-confirmation):** reuse EXP-049's causality/fence/`N≥6`/no-NaN-barrier
  battery; barriers are identical to EXP-049 (which passed), so this re-confirms the harness, with the
  systematic-failure rule (≥3 instruments) carried.

### Step 6 — Material readout (emitted, not adjudicated)

- **Method:** compute the P15 G1 composition (`_compose` → `n_viable`, `n_instruments`,
  `composition_met` = ≥5 cells over ≥3 instruments) and contrast it against the EXP-049 baseline (0/99).
  Flag `TIE_BREAK_SENSITIVE` cells (viable-status flip OR `Δr ≥ 0.05`). Classify the run **MATERIAL**
  (P11 met under P15 G1) vs **IMMATERIAL** (P11 not met). Carry the per-cell `dt_frac`
  (= `was_tie`-count / resolved) and `reassigned_frac` (= `Δ(FAV)`/resolved) distributions.
- **Why:** the §8 routing (re-baseline vs adopt-P15-as-standard) is desk adjudication; the experiment
  emits the mechanical readout only (no self-declared gate).
- **Expected output:** `composition_readout.json` (P15 G1 composition + material verdict +
  TIE_BREAK_SENSITIVE list + EXP-049 baseline contrast).

## Visualisations (budget: 4)

1. **Per-cell `Δr` heatmap (17×6).** Shows where, and how much, the fill rule moves `r`; NaN for
   non-member / NOT_VIABLE_BY_POWER cells. Answers "how large is the fill-rule effect, and is it
   localized or diffuse?"
2. **Per-cell same-bar double-touch fraction `dt_frac` heatmap (17×6).** The exposure surface — how
   often the tie rule is even invoked among resolved events. Answers "could the result have changed?"
3. **P15 viability-status heatmap (17×6)** (codes: VIABLE / BELOW_R / CI_SPANS_050 /
   NOT_VIABLE_BY_POWER / EXCLUDED), with `TIE_BREAK_SENSITIVE` cells marked (hatch/annotation). Answers
   "does any cell, or the composition, cross viability under P15?"
4. **Paired EXP-049-vs-P15 `r` scatter** (one point per member cell; `y=x` diagonal; `r=0.50` and
   `r=0.55` reference lines; colour by domain). Answers "is the shift uniform, and does it carry cells
   across the 0.55 bar?" — the single clearest material-change visual.

(Secondary G2 `r`/`Δr`/`dt_frac` and the dual-fill expectancy table go to CSV, not extra plots.)

## Interpretation Guide (predeclared, before results exist)

- **IMMATERIAL → "EXP-049 benchmark null confirmed; P15 adopted as the 014-B fill standard."** If P15
  G1 does **not** meet P11 (no composition flip) **and** TIE_BREAK_SENSITIVE cells are absent or
  isolated: the `r ≈ 0.50` null is a genuine symmetric-path property of the unconditioned substrate, not
  a fill artifact. P15 is the correct, less-pessimistic fill standard for EXP-053/055–060; the bounded
  fill effect (`Δr` distribution, `dt_frac`) is quantified and disclosed. *This does not revise any
  conditioned-signal result; it validates the fill method the rest of 014-B relies on.*
- **MATERIAL → "EXP-049 benchmark null was (partly) a tie-break artifact; re-baseline before G2."** If
  P15 G1 meets P11 where EXP-049 had 0/99: the worst-case tie-break manufactured part of the
  sub-threshold readout → `014-B-design.md` §8 SUBSTRATE/METHOD_DEFECT. The benchmark capture baseline
  used in the G2 adjudication must be the P15 read, and any 014-A interpretation leaning on the EXP-049
  benchmark null is re-examined. (Recall: the conditioned-efficacy claim EXP-053 already established is
  independent of this — EXP-054 audits the *unconditioned benchmark* baseline.)
- **Magnitude reading regardless of verdict:** report the cross-cell median and IQR of `Δr` and
  `dt_frac`; the count and identity of TIE_BREAK_SENSITIVE cells; and the dual-fill median-expectancy
  shift. A small `dt_frac` (few ties) bounds the maximum possible `Δr` — state this explicitly (the
  effect is capped by exposure).
- **METHOD_DEFECT (halts):** any reconciliation mismatch, any `Δr < 0` / `FAV_P15 < FAV_wc` /
  `resolved` mismatch, non-determinism on any cell, or a causality/fence invariant on ≥3 instruments →
  fix before reporting. These are implementation correctness failures, never substantive outcomes.
- **Cell-level INCONCLUSIVE:** a cell with `resolved < 30` is NOT_VIABLE_BY_POWER — recorded, excluded
  from the P11 numerator, never a ratio. (Membership and `resolved` are inherited from EXP-049, so the
  power profile matches EXP-049 by construction.)

**Experiment deliverable label:** `FILL_MODEL_CHARACTERISED` (carrying MATERIAL / IMMATERIAL),
analogous to EXP-049's `CAPTURE_READINESS_DELIVERED`. No phase closure, no candidate registration, no
gate adjudication (single G2 after the full 014-B slate).

## Implementation Safety Constraints (for experiment-developer)

- **Timestamp ordering:** assert the TRAIN slice is `CloseTime`-sorted before aggregation; align by
  `CloseTime` epochs, never bar index across views; fence every domain bar and every forward-resolution
  window to `CloseTime ≤ train_end_ts`. TEST and the final-30% global holdout are never loaded
  (only Parquet metadata + the F01 TRAIN prefix are read).
- **Denominators / zero-baseline:** `r = FAV/(FAV+ADV)` over resolved; `resolved < 30` →
  `NOT_VIABLE_BY_POWER` (never `0/0`); `resolved = 0` → NOT_VIABLE_BY_POWER. `dt_frac` and
  `reassigned_frac` use `resolved` as the denominator; `resolved = 0` → `None`, never a divide. Median
  expectancy over the qualifying mask; `< 30` qualifying → NOT_VIABLE_BY_POWER for the expectancy
  disclosure. G2 `g2_degenerate_frac` denominator = the G2 candidate pool (`g2_defined +
  g2_degenerate_excluded`); `None` when empty.
- **Bounded iteration:** the first-touch scans (`resolve_first_touch`, `resolve_path_ordered`,
  `first_touch_tie_flags`) are explicit per-event sequential loops over each event's
  `[start, end]` window (a few hundred events/cell × bounded window) — **keep sequential; do not
  vectorize** (causal/streaming semantics are under test). The block bootstrap is vectorized in bounded
  batches (`BOOT_BATCH=2_000`) — already inside the reused helpers.
- **Determinism / seeds:** worst-case leg RNG = `default_rng([BASE_SEED, cell_index, geom_id])`
  (reproduces EXP-049); P15 leg RNG = `default_rng([BASE_SEED, cell_index, geom_id, 15])`; expectancy
  RNGs = distinct documented streams per rule. `cell_index` enumerated over the full 17×6 grid in the
  EXP-049 order. Two full passes compared frame-identical.
- **Memory / progress:** per-cell bounded memory (do not retain all domain frames; `del train_1m`
  after each instrument); `tqdm` over the instrument outer loop. Plots render from the collected
  per-cell summary only — no reloads or re-generation.
- **Real-price discipline:** every barrier, fill, `r`, expectancy, and ATR figure on real domain OHLC.
  No HA price anywhere (the harami detector is not used in EXP-054).
- **Output side effects only in orchestration:** create `results/`/`plots/` in `run()`, not at import.
- **Outputs (`results/`):** `per_cell_fill_compare.parquet` (per cell: both-rule G1/G2 FAV/ADV/resolved,
  `r_exp049`, `r_p15`, `delta_r`, both viability statuses, `tie_break_sensitive`, `dt_frac`,
  `reassigned_frac`, `E_cell_wc`, `E_cell_p15`, CIs, counts); `fill_compare_map.csv` (G1 binding
  summary); `fill_compare_secondary.csv` (G2 + degenerate counts); `expectancy_dual_fill.csv`;
  `reconciliation.csv` (WC-vs-EXP-049 per cell); `composition_readout.json` (P15 G1 P11 + material
  verdict + TIE_BREAK_SENSITIVE list + EXP-049 baseline contrast); `run_metadata.json` (seeds, frozen
  constants, EXP-049 source path, fence statement, fill-rule note, P15-as-approximation disclosure).

## Complexity Check

- **Statistical tests:** 1 / 1 — the regime-clustered moving-block bootstrap (one inferential method),
  applied to the binding proportion `r` (both fill rules, both geometries) and reused for the disclosed
  median-expectancy statistic. No second method introduced.
- **Visualisations:** 4 / 4 — `Δr` heatmap, `dt_frac` heatmap, P15 viability-status heatmap, paired
  EXP-049-vs-P15 `r` scatter.
- **New modules:** 0 / 0 — reuse `xen.zigzag`, `xen.bar_aggregator`, `xen.capture_barriers`,
  `xen.expectancy`; two bounded diagnostic helpers live in `code/run_experiment.py` (orchestration),
  not in `src/xen`.
