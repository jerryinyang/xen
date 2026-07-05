# EXP-015 — CF-MR-005/HYP-001: mechanism characterisation of the 4h ladder scale-in own-price MR harvest

**Family:** CF-MR-005 (REGISTERED 2026-07-03, `docs/signal-registry/candidate-families/cf-mr-005.md`)
· **Phase:** 005 (`docs/experiments-docs/checkpoints/2026-07-03-005-cf-mr-005-ladder-harvest-characterisation/design.md`; Phase 004 retrospective written 2026-07-03) · **Type:** mechanism characterisation, TRAIN.
**Classification:** **ANALYSIS-ONLY** — Part A reads existing EXP-014b/014c engine emissions
read-only; Part B is an availability-style *measurement* on 1m-derived 4h timebars (events +
conditional forward-return profiles; **no strategy P&L is simulated** — a vectorized ladder
backtest would violate the price-primary rule, so all P&L anatomy comes exclusively from
engine-realized fills in Part A). Any tradability claim is **HYP-002 material** (price-primary,
new D0), gated on this experiment. **Slots/reads:** 0 slots, 0 counted TEST reads. **Holdout:**
final-30% sealed; fence = EXP-013 first-49% TRAIN cutoffs verbatim. Frozen referee untuned and
**not the binding instrument here** (L-12; characterisation criteria predeclared below).
**Origin:** EXP-014c extend-field discovery (audit §5.4, report §6); operator decisions D2/D3
(`.ignore/temp/d1/exp-014c-findings-and-decisions.md`).

**Graveyard confrontation (P-01/P-05/P-02, stated honestly).** Single-instrument own-price MR
entries were closed at 5m/1h RSI-style fades (CF-MR-001, net-negative causalized) and directional
price-geometry availability ≈ random (P-01). This design does **not** re-run those: the observed
object is different — a **multi-add ladder position at 4h dislocation depth**, whose field
evidence is engine-realized (61 cells net ci_low>0, year-stable 2021–24, depth-graded per-leg
P&L), not a hypothesis. The experiment is built to **falsify it against the graveyard's failure
mode**: if the "harvest" is drift/short-vol exposure or dislocation-unconditional, the controls
below will say so, cheaply, before any slot or emission is spent. P-02 honored: no exit design
anywhere in scope.

## 1. Falsifiable question

*At 4h, does an instrument's own price, conditioned on a basket-free dislocation of depth `z`
below/above its own rolling median anchor, revert toward that (frozen, ≤t-1) anchor beyond a
dislocation-matched control — per instrument, monotonically in depth — over the ladder-relevant
horizon; and is the engine-observed ladder P&L (EXP-014b/c extend arms) attributable to that
depth-graded reversion rather than to directional drift, short-vol exposure, or a few tail
episodes?* If dislocation-conditional reversion does not separate from control in any powered
cell, the CF-MR-005 thesis has no mechanism and the family retires without a tradability phase.

## 2. Scope

| Field | Value |
|---|---|
| Universe | Same 11 cells as EXP-014c: FX {EURUSD,GBPUSD,USDJPY,USDCHF,USDCAD,AUDUSD,NZDUSD}, IDX {USTEC,US500,US2000,JP225}; 4h only. Rationale: the field evidence lives here; changing universe would decouple Part A from Part B. |
| Trigger (basket-free, predeclared) | `S_t = log P_t − Median_90(log P)` on 4h closes (own-price mirror of the S8 construction minus the basket); `σ_t` = rolling std of S over WZ=200 bars; `z_t = S_t/σ_t`. All from **confirmed bars ≤ t−1**; event fires at the open of bar t when `|z_{t−1}| ≥ z\*`. `z\* ∈ {1.5, 2.0}`; ladder depth bins `|z| ∈ [1.5,2), [2,2.5), [2.5,3), [3,∞)` (mirrors the extend ladder {z\*, z\*+0.5, z\*+1.0}). |
| Anchor (frozen per event) | `a = exp(Median_90(log P))` at t−1 — frozen at event time, mirroring the frozen-bracket object; reversion measured toward *this* level, not a moving median. |
| Time range | Full 5y through the EXP-013 first-49% per-symbol cutoffs. Final-30% never loaded. |
| Part A inputs (read-only) | `data/strategy_runs/EXP-014{b,c}-4h-s8-{extend,allow}-*` incl. shift twins. Never re-emitted, never rewritten; **no admissibility claim** derives from them (unpaid multiplicity — anatomy only). |
| Exclusions | No tradability claim; no exit design (P-02); no new engine emissions; no referee adjudication as a binding gate; no 1h/15m; no basket/spread triggers (CF-MR-004 property); no holdout; no counted TEST read. |

## 3. Methods (simplest sufficient; per-stratum, non-pooled)

| # | Question | Method | Why sufficient |
|---|---|---|---|
| **M1 — availability, native** | Does own-price revert toward the frozen anchor, conditional on depth? | Per (cell, depth-bin): distribution of **fraction-of-dislocation recovered** `R_h = dir·(log P_{t+h} − log P_t)/|S_{t−1}|` at horizons h ∈ {6, 12, 24, 48} bars (dir = sign toward anchor), open-to-open from the action-bar open. Estimate median R_h with a **moving-block bootstrap** CI (block = 12 bars, seed frozen) vs the **dislocation-matched control**: same-cell bars matched on realized vol tercile + |return|-magnitude decile but *not* dislocation-conditioned (methodology-canon matched-random; NOT a signal-derived-target null, L-08). ΔR_h = event − control, CI per (cell, bin, h). Overlapping events handled by event de-clustering: one event per crossing episode (entry into the bin), episode ends when |z|<1.0. | Native to a multi-add ladder: measures *continuous recovery vs depth*, not a single-entry two-barrier race (L-13). Matched control isolates dislocation-conditioning from drift. |
| **M2 — depth gradient** | Is reversion monotone in depth (the ladder's premise)? | Per cell: median ΔR_24 across the 4 depth bins + Page-type trend read (bootstrap CI on the bin-slope). Disclosure companion from Part A: per-LadderLevel realized bps/leg (L0/L1/L2), MAE/MFE, bars held, per-year split — engine-realized, read-only. | The family's mechanism *is* the depth gradient; one ordered statistic answers it. |
| **M3 — attribution (drift / vol / reversion)** | Is the Part-A P&L dislocation-conditional or exposure? | (a) Per cell: Part-A extend-arm net vs the **same cells' shift twins** per ladder level — **collapse fraction (shift net / raw net) disclosed per level** (W3, filed as **L-15** in `docs/knowledge-base/lessons-and-amendments.md`; binary reads prohibited as the only statement). (b) Direction split: ΔR_24 for with-drift vs against-drift events (sign of trailing 90-bar return); a "reversion" that exists only against the prevailing 5y drift direction is exposure, not MR. (c) Event-time overlap census: % of Part-A ladder P&L accrued while ≥2 legs open (scale-in dependency). | Uses only existing emissions + Part-B measurements; separates the three candidate explanations without new machinery. |
| **M4 — left tail** | What tail does the scale-in carry? | Part A, per cell: episode-level (all legs of one ladder occupancy aggregated) P&L distribution — empirical q{01,05} quantiles, worst-episode census (date, depth reached, bars underwater, MAE of the full position), **top-k sensitivity** (net with top 1/3/5 winning episodes removed), and % of 5y total P&L from the worst-decile-depth episodes. Part B: census of events reaching bin 4 (|z|≥3) that *never* recover 50% within 48 bars (the ladder's failure population), per year. | Empirical, per-stratum, no EVT machinery; directly answers "does the 5y window contain the tail, and how bad is the observed one". |
| **M5 — cost context (disclosure)** | Where does the harvest sit vs cost? | Part A per cell: net at {1,2,3}× frozen cost map (referee cost table, read-only constants) — disclosure table only, no gate. | Already-established read (audit §5.4); frames HYP-002 viability without claiming it. |

**Denominators/zero-baseline:** events per (cell, bin) stated in every table; a (cell, bin) with
<30 de-clustered events is **UNPOWERED** (reported, never FAIL); a cell with <30 events at bin 1
is UNPOWERED overall. Part-A per-level splits report n legs; NaN/censored legs excluded and
counted. Control sets are sampled with a frozen seed; all CIs 95%, 10,000 resamples.

## 4. Leak tripwires (binding on M1/M2)

1. **Block-permuted-returns null (L-07):** rebuild each cell's 4h price path from block-permuted
   open-to-open returns (block = 12 bars, 200 replicates, frozen seed), recompute the full M1
   pipeline. Genuine conditional mean-reversion beyond block length must **collapse**: the
   observed per-(cell,bin) ΔR_24 must exceed the permuted-null 95% band to count as separated;
   the **collapse fraction (null-median ΔR / observed ΔR) is disclosed** (W3). A ΔR that
   survives block-permutation is autocorrelation-free artifact ⇒ REJECT-class for that cell.
   (Time-reversal is NOT used as the destroy — median-reversion statistics are largely
   time-symmetric; L-07's return-permutation is the valid destroyer. No signal-derived-target
   null anywhere, L-08.)
2. **Provenance guard (Part A):** re-assert the EXP-014c audit's provenance checks on every
   emission dir read (fills within [Low,High] tolerance; fence via `assert_run_within_holdout`).

## 5. Interpretation criteria (frozen before results)

| Outcome | Condition |
|---|---|
| **MECHANISM_SUPPORTED** (per cell) | ΔR_24 CI > 0 vs matched control in ≥2 adjacent depth bins AND observed ΔR outside the block-permute null band AND M3b shows separation is not drift-sign-exclusive. ≥3 supported cells over ≥2 instrument classes ⇒ family proceeds to HYP-002 (tradability D0, price-primary, own multiplicity). |
| **EXPOSURE_ARTIFACT** | M3b: separation exists only with-drift, or M3a: Part-A collapse fractions ≈ 1 with M1 flat ⇒ the field P&L is drift/short-vol harvest ⇒ **family retires** (record; terminal-branch note per pitfalls ledger). |
| **TAIL_FUNDED** | M4: top-k removal or worst-decile census shows >50% of Part-A P&L in the deepest-decile episodes with bin-4 non-recovery events present every year ⇒ mechanism may be real but capacity is tail-funded ⇒ HYP-002 only with a predeclared tail budget; recorded as a first-branch constraint. |
| **UNPOWERED / INCONCLUSIVE** | <3 cells powered, or M1 CIs straddle 0 with permute-band overlap ⇒ report why (event scarcity vs noise); no retire, no proceed — operator routing. |
| Mixed outcomes | Per-cell labels stand independently (L-03); the family-level read uses the counts above, never a pooled statistic. |

## 6. Complexity budget

Tests: M1 control-Δ + M2 trend + M3 splits + block-permute null = 4 (within comparative budget).
Plots ≤5: ΔR_h profile grid (cell × bin); depth-gradient bars; Part-A ladder-level anatomy;
episode-tail (M4) census; collapse-fraction table-plot. Code: 1 new module
(`code/lib.py` — trigger/event/measurement; reuse `xen.bar_aggregator`, ingestion, provenance
helpers) + 1 orchestration script. No new `python/src/xen` module.

## 7. Implementation safety (for experiment-developer)

- All event logic from confirmed bars ≤ t−1; measurement starts at the action bar's **open**;
  open-to-open returns only; forming bar never read.
- 4h bars via `xen.bar_aggregator` from 1m timebars, sorted by `CloseTime` **before** the
  first-49% per-symbol slice (fence constants copied verbatim from EXP-013 conf; assert max
  CloseTime ≤ fence per cell).
- Part-A loads via `xen.signals.ingestion.load_emitted_run` + `assert_run_within_holdout`;
  emissions opened read-only; never write into `data/strategy_runs/`.
- De-clustering is sequential/stateful — keep the explicit loop, bounded, tqdm-tracked;
  everything else vectorized (Polars/NumPy) only where causally equivalent.
- Frozen seeds: bootstrap 20260703, permutation 20260704; block length 12 constant.
- Median_90/σ_200 computed streaming-compatible (rolling windows on closed bars only).
- No perf shortcut may alter event membership, denominators, matching strata, or temporal order.

## 8. Registry / governance

CF-MR-005/HYP-001 row exists (`multiplicity-registry.md`, REGISTERED — this design scopes it;
EXP-015 to be entered on gate approval). 0 slots, 0 counted reads; no TEST-stratum read. Not
registry-relevant beyond the HYP-001 row update. Follow-up (HYP-002 tradability, price-primary,
native cTrader ladder with basket-free trigger) is a **separate future scope**, admissible only
on MECHANISM_SUPPORTED (± TAIL_FUNDED constraint).

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-03)

Single falsifiable question ✓ (mechanism of the ladder harvest; M1–M5 are facets, no compound
claims). Registry precondition ✓ (CF-MR-005 REGISTERED, HYP-001 pending-scope row present; 0
slots/reads). Classification ✓ — analysis-only throughout; no vectorized strategy backtest (P&L
anatomy restricted to engine-realized Part-A fills; L-01/P-09 honored). Graveyard ✓ — P-01/P-05
confronted explicitly with a falsification-first structure; P-02 honored (no exit scope). KB ✓ —
L-07 (block-permute, not time-reversal/path-rotation), L-08 (no signal-derived-target null),
L-13 (ladder-native availability, not the two-barrier race), W3/L-15 (collapse fractions disclosed),
L-03 (per-stratum, no pooled verdicts). Holdout ✓ (EXP-013 fence verbatim; final-30% sealed).
Budget ✓ (4 tests, ≤5 plots, 1 module + 1 script). Criteria ✓ (frozen, measurable, UNPOWERED
never FAIL, retire path predeclared). **Status: READY for Stage 2 (Implement).**
