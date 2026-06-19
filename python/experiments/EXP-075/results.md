# Results: EXP-075 — TRAIN Design of an Exhaustion-Cap Entry Filter (CF-HA-HARAMI-001 / HYP-028)

**Stratum:** TRAIN only `[0, train_cutoff)`. **0 counted TEST reads, holdout untouched.**
**Audit:** CONDITIONAL PASS (`audit.md`) — 0 Critical, 1 Warning (F4 disclosure column predated the
run; reconstructed ≡ 0.0), 2 Info.
**Binding object:** per band-core domain (15m/30m/1h) improved-cell share under a single deployable
uniform cap (M-GLOBAL); 5m and band-pooled disclosed-only.
**Returns:** real-price `N-PARTIAL-V2A` `r_e` (certified EXP-068 arm; reconciled to EXP-074 at 1e-9).
99 cells, 67 powered.

---

## Headline

**`FILTER_INEFFECTIVE`. An entry-time exhaustion cap is not a lever for the harami's loss tail.**
Neither the deployable uniform rule (M-GLOBAL) nor the per-cell overfit ceiling (M-PERCELL)
materially improves any band-core domain:

- **M-GLOBAL adds zero improved cells in every domain** (uplift Δ = 0.00 at the locked U, and Δ = 0
  across the entire pre-declared grid p85/p90/p95 — `u_sensitivity` = 0 improved domains at every
  percentile, both forms). The single uniform cap changes no cell's improved status.
- **M-PERCELL** (the diagnostic overfit ceiling, never deployable) reaches its best at 30m =
  **+0.118 < 0.15** uplift; 15m −0.059, 1h 0.000. Even bespoke per-cell tuning cannot lift the
  improved-share by the modest pre-registered bar in *any* band-core domain.

This is the cleanest possible negative for the exhaustion-cap path, and it confirms — directly, on
the strategy's own economic legs — the mechanism EXP-074 inferred.

---

## 1. Why the cap fails — the EXP-074 bimodality, now shown economically

EXP-074 found that high `m_sofar/atr` (entry exhaustion) separates the **extreme q05 loss tail**
near-universally, yet is neutral/positive on the central mass — i.e. exhausted entries are
**bimodal**: they either work (median-positive) or go catastrophic (q05). EXP-075 shows the direct
consequence for an upper cap: **removing high-exhaustion entries removes the big winners together
with the catastrophic losers.** Spot cells make this concrete — e.g. USTEC-1h baseline mean +0.167
drops to −0.089 under the M-GLOBAL cap (retention 0.90); BTCUSD-30m +0.126 → −0.154. The cap trades
tail-suppression for median/winner erosion at roughly a wash or worse, so the joint four-leg
`improved` criterion (raw-mean ∧ median ∧ beats-RM CI_low>0 ∧ retention≥0.70) never flips a cell.

**The lever EXP-074 pointed at does not survive contact with the economic endpoint.** The q05-tail
separation is real, but it is not *actionable as an entry cap* because the same feature that marks
the worst losers also marks the best winners. This is exactly the risk the joint criterion was
designed to catch (D0-amendment-007 §"Why item 4's joint criterion is the correct instrument"), and
it caught it.

## 2. Per-domain binding vector (F1, lead — binding)

| Domain | n_pow | baseline share | M-GLOBAL share | Δ (uplift) | M-PERCELL share | percell uplift | hurt |
|---|---|---|---|---|---|---|---|
| 15m | 17 | 0.059 | 0.059 | 0.000 | 0.000 | −0.059 | no |
| 30m | 17 | 0.059 | 0.059 | 0.000 | 0.176 | +0.118 | no |
| 1h | 16 | 0.188 | 0.188 | 0.000 | 0.188 | 0.000 | no |

- No band-core domain is **improved** (needs Δ ≥ +0.15, share ≥ 0.50; none reach either).
- No band-core domain is **hurt** (Δ ≤ −0.10): the locked p95 cap is gentle enough not to break a
  domain at the share level, even though it lowers individual-cell means.
- Locked U: F1 = 20.61 ATR (p95), F2 = 5.86 (p95) — locked at the least-restrictive grid point
  because no percentile helped (tie-break rule).

**F2 (normalizer-robustness, disclosed):** same conclusion. F2 M-GLOBAL shows tiny positive uplift
at 30m (+0.059) and 1h (+0.0625) but neither reaches 0.15 and `global_improved=false` everywhere;
M-PERCELL max +0.125 (1h) < 0.15. Expressing exhaustion relative to the per-entry p75 threshold
rather than ATR does not change the verdict.

**5m / band-pooled (disclosed-only):** 5m M-GLOBAL Δ = 0.000; no flip. Nothing in the disclosed
lines contradicts the binding read.

## 3. Routing verdict and its robustness

`FILTER_INEFFECTIVE` — even the M-PERCELL ceiling fails Δ ≥ +0.15 in every band-core domain ⇒ the
exhaustion cap is not a lever; supports closing the CAND-001 exhaustion-cap path cleanly.

**Bar-sensitivity (disclosed, decision-neutral).** The verdict turns on the pinned
`UPLIFT_BAR = 0.15`. 30m's M-PERCELL uplift +0.118 falls just short; at a 0.10 bar the label would
flip to **FILTER_OVERFIT** (per-cell gains exist but the deployable M-GLOBAL improves 0 domains).
The 0.15 is a pre-registered, analogy-borrowed bar (conceptual ancestor: EXP-074's material bar,
rank-biserial 0.15 ↔ AUC ≈ 0.575), not an empirically calibrated value — so the exact tier name is
not robust to it. **The routing disposition is, however, identical under both tiers:** *do not spend
the holdout; route toward closing CAND-001.* The conclusion does not depend on the bar.

## 4. Secondary findings

- **Undefined-feature share ≡ 0.0** (computed from EXP-074 parquets; F4 disclosure). The qualifying
  population (events past the `/STRONG-STAT` p75 gate) always has a defined `msofar_atr`/`ss_excess`,
  so retention is driven entirely by the cap, not by feature-undefinedness — the retention floor is a
  clean read of the cap's aggressiveness. (The executed run predated the F4 column; the next run
  emits it natively — audit Warning 1.)
- **The cap can locally hurt** (lowers individual-cell means by removing high-exhaustion winners) but
  never *helps* at the share level — consistent across F1/F2 and all percentiles.
- **Integrity:** baseline `r_e` reconciles to EXP-074 at 1e-9; 67 powered cells identical to EXP-074;
  determinism by construction (integer seeds, collision-free null-keys).

## 5. Disposition & routing (CAND-001 / EXP-075)

**Supports closing the CAND-001 exhaustion-cap path; the family-closure decision is G-016's.**

1. **The exhaustion cap is refuted as an entry lever** on TRAIN, on the strategy's own legs, across
   the full pre-declared grid and both cap forms. The locked filter is frozen
   (`locked_filter.json`, `deployable=false`, sha256-pinned) but is **NON-CONFIRMATORY and not
   carried anywhere** — no holdout/TEST read is warranted (FILTER_INEFFECTIVE explicitly routes away
   from the holdout).
2. **No new candidate branch is registered** (EXP-075 designed a prospective filter; it confirmed
   none). CF-HA-HARAMI-001 stays `REGISTERED / OPEN`; CAND-001 remains retired-on-scope from EXP-071.
3. **The mechanism is now closed on both sides:** EXP-071 showed the raw mean fails on the binding
   TEST cells; EXP-074 located the driver (exhaustion-magnitude q05 tail); EXP-075 shows that driver
   is **not separable from the median/winner mass by an entry cap**. The harami's binding obstacle is
   an *intrinsic bimodality of the conditioned entry*, not a removable tail — there is no entry-time
   exhaustion filter that lifts the mean without eroding the median edge.
4. **G-016 input:** EXP-071 (TEST_NOT_CONFIRMED) + EXP-074 (tail driver identified, gate-masked) +
   EXP-075 (cap ineffective) jointly argue the exhaustion-cap route is exhausted. Whether to close
   CF-HA-HARAMI-001/CAND-001 or route to a *different* lever (not an exhaustion cap) is the G-016
   desk decision; this experiment removes the exhaustion cap from the menu.

## 6. Caveats

- TRAIN-only design; no causal/predictive claim confirmed (none sought). The negative is a
  TRAIN-design routing result — it says a holdout look is **not** warranted, the strongest possible
  TRAIN-only conclusion against the cap.
- In-sample per-cell q05 and pooled-quantile U; block bootstrap assumes approximate within-TRAIN
  stationarity (descriptive CIs).
- Verdict *tier* (INEFFECTIVE vs OVERFIT) is bar-sensitive at 0.15 vs 0.10; *disposition* is not (§3).
- 2h/4h excluded (0 powered cells) — the cap was never evaluable there; the conclusion is scoped to
  the 15m–1h band core (+5m disclosed), exactly as pre-registered.
- The `undef_share` columns were reconstructed from EXP-074 (run predated F4 instrumentation); value
  is 0.0 and verdict-irrelevant (audit Warning 1).
