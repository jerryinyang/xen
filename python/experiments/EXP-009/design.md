# EXP-009 — CF-MR-003/HYP-001 (native re-screen): does price return to the anchor?

**Family:** CF-MR-003 (REGISTERED) · **Phase:** 002 · **Type:** target-based reversion-availability screen
**Classification:** **ANALYSIS-ONLY** (justified §2) · **Slots/reads:** 0 candidate slots, 0 counted TEST
reads · **Holdout:** final-30% sealed; TRAIN-only · **Supersedes the *vehicle* of EXP-008** (not the family;
see EXP-008 Amendments A1/A2 + L-13).

## 0. Why this experiment (mandate)

EXP-008 evaluated CF-MR-003 with a vehicle **inherited from the price-geometry family** — fixed-horizon
signed-**MFE-toward-anchor** + Δ-over-regime-matched-**random-timing** — and was closed as a **methodology
finding**: that vehicle is **non-native to mean-reversion**. Its EXP-008 diagnostic
(`EXP-008/results/vehicle_diagnostic.json`) **demonstrated** that under a **dislocation-matched** null the
native target metrics separate (anchor-hit **+2.9 pp**, fraction-recovered **+2.7 pp**, CIs exclude 0)
while the MFE metric is blind, and that the random-timing null reads spuriously negative on near-anchor
bars. EXP-009 re-asks the family's native question with a native vehicle. **The MR selector carries
forward unchanged** (2-leg `VR∧HL`, EXP-008 Amendment A1); only the **estimand and null** change.

## 1. Falsifiable question (one)

*Among bars at a **matched dislocation** (`|z|` in the same bin), does the cross-domain MR-screen
(`VR∧HL` on the deviation, `≤ t-1`) identify entries whose price **returns to the higher-domain anchor**
more — higher anchor-hit rate / greater fraction-of-dislocation recovered / faster time-to-anchor (scaled
by the fitted half-life) — than a dislocation-matched, regime-matched, screen-free control, per stratum
— or not?* Honest prior after EXP-008: a **small positive** native separation is plausible (~+2.9 pp), but
it is unproven, un-cost-tested, and may carry a residual `|z|`-depth confound this design removes by
binning. Edge = Δ-over-**dislocation-matched**-random, never a raw hit rate.

## 2. Price-primary vs analysis-only — ANALYSIS-ONLY (justified)

Characterises **reversion-to-target availability** on real prices vs a matched control; books **no**
position, order, P&L, or cost. Real-price intrabar touches of a fixed anchor level are an availability
diagnostic (EXP-047/081 lineage), not a strategy. The tradeable step — a **limit-at-anchor** order with
real-price fill, binding-leg cost, open-to-open entry — is **price-primary and DEFERRED** to a later,
separately-gated in-engine experiment, admissible **only** if this screen admits (avoids "measure
tradability before availability"; keeps L-01 discipline — no vectorized price-strategy P&L here).

## 3. Data scope

- **Universe:** 16-instrument INFR-003 5-year canonical (VAL-003 minus DE30). TRAIN only (first 70% of the
  first-70% analysis set); TEST band + final-30% holdout never loaded.
- **Anchor-series axis (5, unchanged from EXP-008 §4):** S1 CENTER, S2 RANGE, S3 DETREND, S4 OU, S5 SPREAD.
- **Domain-pair axis (3):** 4h/1h, 4h/15m, 1D/1h.
- **Stratum = (instrument, anchor-series, domain-pair)**; ≤240 cells. Per-stratum binding (L-03); pooled =
  disclosure-only.
- **Selector (carried forward, `≤ t-1`):** entry event = exec bar with `VR(q=4)<0.90 ∧ half-life∈(0,48]`
  on the trailing-`W_s` deviation **and** `|z|≥z*=2.0`. Same causal machinery as EXP-008 (evaluate at bar
  open on `≤ t-1`; `xen.cross_domain_mr`).

## 4. Native target-based endpoints (the change)

Anchor level in price: `a_target = a[i-1]` for S1/S2/S4 (price-space anchor) or `exp(a[i-1])` for S3/S5
(log-space). Fade side `s = sign(dev[i-1])`. **Event-specific native horizon** `H_i = min(H_CAP=48,
ceil(m·HL_i))`, `m=3` (frozen; sensitivity §8), `HL_i` = **that event's own** fitted AR(1) half-life (finite
by construction — the event passed the HL leg). The horizon tracks each event's own reversion speed, not a
cell aggregate or a round number (fixes the EXP-008 arbitrary-24 fault + the operator's HL=6-vs-HL=20
point). **Horizon-matched pairing (no cross-arm confound):** each conditioned event's matched controls
(§5) are measured over that event's **same `H_i`**, so a longer window can never masquerade as a pass-vs-fail
effect. All excursions strictly forward of exec `Open[i]`, on **real** intrabar prices.

| # | Endpoint | Definition (per event, real prices, over `H_i`) | Cell statistic |
|---|---|---|---|
| **E1 ANCHOR-HIT** (primary) | did real price touch `a_target` within `H_i`? short: `min Low[i..i+H_i-1] ≤ a_target`; long: `max High ≥ a_target` | **hit rate** = mean(0/1) |
| **E2 FRAC-RECOVERED** | `s·(price_entry − most-toward-anchor real price)/|price_entry − a_target|`, capped at 1.0 (reached) | **median** |
| **E3 TIME-TO-ANCHOR** | bars to first touch of `a_target`, censored at `H_i`, divided by `HL_i` (half-life units); paired control uses the conditioned event's `HL_i` | **median** (lower = faster) |

`price_entry = Open[i]`. Cells with `< N_min` events → **UNPOWERED** (reported, never failed). E1/E2 higher
= more reversion; E3 lower = faster reversion.

## 5. Null, estimand, statistics, multiplicity

- **Binding null — SCREEN-FAIL extremes at matched dislocation (operator-ratified 2026-07-01).** The
  control population is the **non-selected extreme** bars: `{|z|≥2 ∧ VR∧HL screen-FAIL}` — *not* random
  timing. This is the direct pass-vs-fail contrast that isolates the incremental value of VR∧HL:
  `|z|≥2 → {selector passes = conditioned}` vs `{selector fails = control}`. Bin by `|z|` (**B1 [2,2.5), B2
  [2.5,3), B3 [3,∞)**); within each (`|z|`-bin × ATR-tercile regime) stratum, sample the fail population to
  **count-match** the conditioned events (random sampling used *only* for count balance, per the operator's
  note). Each control bar is measured over its **paired conditioned event's `H_i`** (§4 horizon-matched
  pairing), same anchor, fade side from its own `dev` sign, `E3` scaled by the paired `HL_i`. This holds
  **dislocation + regime + extreme-eligibility fixed** and varies **only** whether VR∧HL fired.
- **Disclosure nulls (non-binding):** (i) EXP-008 regime-matched **random-timing**; (ii) **random within the
  `|z|` bin** (the EXP-008-A2 diagnostic C2). Reported beside the binding fail-control to expose how the
  null choice moves the read (transparency, never the verdict).
- **Δ + uncertainty:** `Δ̂ = endpoint(cond) − endpoint(dislocation-binned ctrl)`; **moving-block bootstrap**
  on conditioned events (serial dependence), iid on control; per-cell `ci_low` (`xen.availability_gate.cell_se`,
  `n_boot≥10 000`). Block-permute the per-event outcome series, never rotate the price path (L-07).
- **Multiplicity — cross-axis Holm max-statistic** over the 15 series×domain axes (`availability_gate`
  G-019 pattern), computed per endpoint; the axis max-stat is the admission unit, the per-stratum Δ is the
  read (L-03). E1 hit-rate uses an additive `STAT_MEAN`; E2/E3 use `STAT_MEDIAN` (additive only; frozen
  gate constants Z/FWER/N_PERM untouched, as with EXP-008's `STAT_TAILMASS_UPPER`).
- **Power / MDE:** per-cell MDE = smallest Δ the block-bootstrap resolves at `n_events`; `MDE>Δ*` or
  `n_events<N_min` or degenerate `HL_cell` → UNPOWERED.

## 6. Leak tripwires

**Binding — pass/fail-label permutation.** Among the `|z|≥2` bars (pass ∪ fail), permute the screen
pass/fail labels, recompute Δ; the screen's marginal edge **must collapse** (the specific VR∧HL split, not a
random split of the same extreme population, carries the edge). Δ surviving ⇒ selection artifact ⇒ **REJECT**.

**Diagnostic (non-binding) — time-reversal.** Measure the reach-anchor window **backward** (`[i-H_i+1..i]`).
**Amendment B1 (2026-07-01, smoke-caught, mechanism argument, pre-binding-run):** for the *reach-anchor*
estimand this is **not** a valid future-destroyer — target-touch on a **stationary** mean-reverting deviation
is **time-symmetric** (a screen-pass bar sits in an oscillatory regime that crosses the anchor in both time
directions), so a non-collapse is the **expected** signature of genuine causal MR, not a leak. Reported for
transparency; **does not gate admission**. (Causality is already guaranteed by construction: every decision
input is `≤ t-1`; the forward window is the outcome only. The label permutation is the operative
selection-artifact control.) Audit re-runs the label permutation on every admitting cell.

## 7. Interpretation criteria (predeclared, frozen before outcome contact)

Per-cell `N_min=100` events; axis **eligible** only with ≥4 powered instrument-cells; within-axis majority
= **≥50% of powered cells**. Effect floors (economic-reasoning, **band** disclosed to avoid a fixed plant,
L-08): **primary E1 anchor-hit `Δ*_hit=+0.03`** (min advantage that could survive to a limit-at-anchor
P&L test — tradability separately gated), band `{0.02, 0.03, 0.05}`; **E2 `Δ*_frac=+0.03`**; E3 supportive
(faster, `Δ<0`), non-binding.

- **ADMIT-TO-EXPLORE (family):** ≥1 (series×domain) axis clears cross-axis-Holm **and** ≥50% of that axis's
  powered cells show `Δ̂≥Δ*` with block-bootstrap `ci_low>0` on **E1 (primary) or E2** — **and both leak
  tripwires collapse Δ** on the admitting cells. ⇒ concretize the **limit-at-anchor** tradability test as a
  new dated-D0 **price-primary** experiment (still 0 counted reads until that gate).
- **EXONERATE (family):** ≥ the eligible axes are powered and **no** axis clears Holm+floor+leak → the
  screen confers no material reversion-to-anchor advantage over dislocation-matched random. Honest closure;
  family retained.
- **INCONCLUSIVE:** Holm-admitted-but-sub-floor on all axes / >½ axes ineligible-UNPOWERED / leak-ambiguous
  (the EXP-008 arc showed this branch is real — a large-n Holm flag at negligible effect is **not** ADMIT).
  Report effect sizes; re-scope as a new experiment.

No metric re-defined after results (inverted-inference predeclaration). Report **absolute effect sizes**
on every axis regardless of verdict (L-11 — do not overstate a Holm flag as an edge, nor a small edge as
tradability).

## 8. Robustness / sensitivity (disclosure, non-binding)

- Horizon multiplier `m∈{2,3,4}` and `H_CAP∈{48,96}`; **event-specific `H_i` vs a cell-median horizon**
  (the operator's HL-heterogeneity question, reported as a robustness contrast): verdict-invariance band.
- Floor band `{0.02,0.03,0.05}`; `z*∈{1.5,2.0,2.5}`; `|z|`-bin edges.
- **Null-choice contrast:** binding screen-fail control vs the two disclosure nulls (random-timing;
  random-within-bin) side by side — how much of the read is the null.
- Recent-third (most-recent 1/3 of TRAIN): regime-shift fragility.
- Anchor-drift check: fixed entry-time `a_target` vs the moving anchor (report both; fixed is binding).

## 9. Complexity budget

- **Stat tests (3 types):** block-bootstrap Δ CI per cell/endpoint; cross-axis-Holm permuted admission;
  leak-tripwire collapse. ✓
- **Plots (~6):** per-series E1 hit-Δ heatmaps; cross-axis admission (E1/E2); E2 fraction-recovered map;
  leak-tripwire before/after; MDE/powered map; dislocation-binned-vs-random-timing null contrast. ✓
- **Modules (1 new):** `xen.cross_domain_mr` reused for the selector/anchors; **new**
  `xen.reversion_targets` (anchor-level mapping, real-price hit / fraction / time-to-target, `H_nat` from
  `HL_cell`, dislocation binning) + additive `availability_gate.STAT_MEAN`. Plus the EXP-009 script. ✓

## 10. Implementation safety constraints

- **TRAIN only**; slice per file before any cross-instrument op (S5 basket, regime); never load TEST/holdout.
- Every `≤ t-1` boundary explicit (selector, `z`, `HL_cell`, ATR, S5 β on trailing windows ending `t-1`);
  **anchor level `a_target` fixed at entry** `a[i-1]`; hit/fraction/time strictly forward of exec `Open`;
  **real intrabar High/Low** for touches (no synthetic prices); no forming-bar OHLC.
- Dislocation-binned + regime-matched control draws seed-fixed, reproducible; block bootstrap `n_boot≥10 000`;
  `tqdm` over the cell loop. Explicit NaN/warmup/degenerate-`HL` handling → UNPOWERED, never NaN-propagate.
- Real-price outcomes only; align by timestamp, never bar index. Deterministic; no import side effects.

## 11. Registry / governance disposition

CF-MR-003 `REGISTERED → SCREENED-{ADMIT|EXONERATE|INCONCLUSIVE}` on completion (native vehicle). 0 slots,
0 counted reads, holdout sealed; never used to tune the frozen referee (L-12). Multiplicity-registry:
record as the 15 series×domain axes under cross-axis Holm (native endpoints). The **limit-at-anchor
tradability** step and any counted TEST read remain **DEFERRED** to a separate dated-D0 price-primary
experiment, gated on a TRAIN ADMIT here.

---

## GATE: APPROVE (pre-exec, operator 2026-07-01, with two ratified adjustments + a language fix)

Operator reviewed the draft and APPROVED the native estimand, mechanism-based horizon, and
anchor-fixed-at-entry, with **two adjustments now folded in**: (1) the binding null is the **screen-FAIL
extreme population** (`|z|≥2 ∧ VR∧HL fail`), a direct pass-vs-fail contrast at matched dislocation/regime —
not random-within-bin (random sampling only count-balances the fail pool); random-timing + random-within-bin
are demoted to disclosure nulls (§5). (2) The horizon is **event-specific** `H_i=min(48,3·HL_i)`, with
**horizon-matched control pairing** so the window is never a pass-vs-fail confound (§4); a cell-median-horizon
contrast is reported as robustness (§8). Language across the record softened: EXP-008's diagnostic
**indicated / gave evidence consistent with** a vehicle mismatch (not "demonstrated" — it was reactive, not
pre-registered). Selector (2-leg VR∧HL), universe, per-stratum non-pooling, cross-axis Holm, leak tripwires,
holdout seal, 0-read/0-slot posture unchanged. Retained gate choices: floor `Δ*_hit=0.03` (band
{0.02,0.03,0.05}); `|z|` bins {2,2.5,3,∞}; limit-at-anchor P&L deferred to a price-primary experiment. →
**Stage 2 (Implement).**