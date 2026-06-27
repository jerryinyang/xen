# Results: EXP-060B — MA(20,50) Substrate Dominance: Genuine Lead or Skew Artifact?

**Verdict:** `SUBSTRATE_LEAD_FOUND` (audit PASS — 0 Critical, 2 Warning, 3 Info).
**One-line:** On the MA(20,50) substrate the conditioned HA-harami expresses a **real median edge** that it
does **not** express on ZigZag — but that edge is a *median* phenomenon: the gross **mean** is ≈0/negative
across most of the grid (the capped-up/uncapped-down left tail), so it is **not yet a tradeable, mean-positive
edge**. The lead clears P11 only via 14 cells (8 of them low-n 4h). G2 should **not close**
CF-HA-HARAMI-001, but the open question is now the **skew (the mean)**, not the signal's existence.

---

## 1. What was measured

EXP-060 returned `CHARACTERISED_NOT_VIABLE_ELIGIBLE` and read the MA(20,50) baseline's ~3–4× median advantage
as a "substrate property." Two confounds made that read unsafe: (i) EXP-060 emitted MA's *median* only — never
its mean or exit composition — and the champion's own gross mean is ≈0 on 5/6 domains (capped V2A upside +
uncapped `/ADV-NONE` downside); (ii) MA's advantage was never tested against a matched-random control **on the
MA substrate**, so "the harami adds value on MA" was untested.

EXP-060B re-instruments EXP-060's pipeline on the identical conditioned `/STRONG-STAT` HA-harami population
(byte-identical; reconciliation exact 99/99) with: the **mean** bootstrapped alongside the median for all arms
(D1); the new **matched-random-on-MA control RM3** (D2, the binding discriminator); and MA exit-reason
composition (D3). Binding endpoint unchanged: median per-event gross expectancy (P14); mean disclosed. TRAIN
only, 99-cell grid, gross.

## 2. Findings (against analysis-plan §6 criteria)

### D2 — The binding discriminator: M3 vs its own-substrate matched-random (RM3)

| Quantity | Value | Composes P11? |
|---|---|---|
| M3 median-viable cells | **89 / 99** (17 instruments) | yes |
| M3 beats RM3 (independent median contrast CI_low > 0) | **85 / 99** | yes |
| M3 mean-viable cells | **14 / 99** | yes (9 instruments) |
| **M3 lead cells** (median-viable ∧ beats RM3 ∧ mean-viable) | **14 / 99 (9 instruments)** | **yes → SUBSTRATE_LEAD_FOUND** |

- **RM3 is a live, non-degenerate control:** RM3 median across cells = 0.268 / **0.380** / 0.530
  (min/median/max) — i.e. RM3 reproduces the **~0.38-ATR geometry drift-capture baseline** that the ZigZag
  random/champion produced in EXP-060. The control is fair.
- **M3 genuinely lifts the median above the geometry baseline:** M3 median = 0.075 / **1.158** / 1.821; the
  `M3 − RM3` median contrast CI_low has median **0.551** (range −0.199…0.993; only 4/89 ≤ 0). The harami+strong
  signal adds ~0.78 ATR of median over random on the MA substrate.
- **This reverses the ZigZag result.** On ZigZag the same signal failed to beat its matched-random control
  (EXP-060: 3/99); on MA it beats it broadly (85/99). **The substrate genuinely determines whether the harami
  expresses an edge** — the central, validated finding.

→ **Supports the SUBSTRATE_LEAD_FOUND branch of the predeclared fork** (median-viable ∧ beats-own-random ∧
mean-viable composes P11). Mechanically met.

### D1 — The skew: median ≫ mean, ADV-NONE-driven (audit W2)

The lead is a **median** result; the mean tells a sharply different, decisive story.

- **M3 gross mean is ≈0/negative at the typical cell:** M3 mean median across cells = **−0.065** (RM3 mean
  median −0.054). M3's mean clears zero with one-sided confidence in only **14/99** cells — the binding
  constraint on the lead. The 75 cells that are median-viable but *not* lead-viable are blocked by the mean.
- **The skew is ADV-NONE-driven and enormous on MA.** Median (median−mean) gap by adverse model:

  | Substrate | ADV-NONE arms gap | 1:1 arms gap |
  |---|---|---|
  | ZigZag | 0.163 | 0.114 |
  | **MA** | **1.201** | 0.495 |

  Removing the stop (`/ADV-NONE`) is what manufactures the median≫mean skew; on MA the ADV-NONE gap is **1.20
  ATR** — the capped V2A upside with an uncapped, time-cap-realized downside produces a fat left tail that
  zeroes the mean even where the median looks strong. This is the same mechanism as the ZigZag champion, far
  larger in absolute terms because MA defines larger moves/targets.

### D3 — Mechanism: M3 escapes the TIMECAP trap less than random, wins by magnitude not hit-rate

Pooled exit-weight composition (favourable legs vs time cap):

| Object | TIMECAP weight | FAV weight |
|---|---|---|
| Z3 (ZigZag champion) | 0.642 | 0.358 |
| **M3 (MA champion)** | **0.408** | **0.592** |
| RM3 (MA random) | 0.178 | 0.822 |

- M3 is **less** TIMECAP-bound than Z3 (0.41 vs 0.64) — the MA substrate does convert more weight to favourable
  targets than ZigZag.
- But RM3 hits FAV **more** than M3 (0.82 vs 0.59): non-conditioned random entries have smaller `M_sofar` →
  nearer targets → higher hit-rate. So **M3's median advantage is not a higher favourable hit-rate** — strong
  conditioning pushes targets *further out* (larger `M_sofar`), and M3 wins by **larger realized magnitude per
  resolution**. That same further-target-with-no-stop geometry is exactly what generates the left tail in D1.

## 3. Interpretation

The two confounds resolve in opposite directions, and both matter:

1. **Redundancy confound → refuted (on MA).** The harami+strong signal is **not** redundant on the MA
   substrate. It lifts the median from the ~0.38 geometry baseline to ~1.16 and beats its own matched-random
   control in 85/99 cells. Unlike ZigZag, MA segmentation lets the signal express a real reversal edge. This is
   the genuine, audit-validated discovery.
2. **Skew confound → confirmed.** That edge does **not** translate into tradeable expectancy. M3's gross mean
   is ≈0/negative across most of the grid; the ADV-NONE uncapped downside (gap 1.20 ATR on MA) caps it. The
   mean-positive subset is exactly the 14 lead cells.

So `SUBSTRATE_LEAD_FOUND` is **true at the binding median and correctly triggered**, but it is a **narrow,
median-only lead**, not a broad tradeable one. The honest characterisation: *a real MA-substrate signal edge
exists; the binding obstacle to viability is no longer "does the signal work" (it does, on MA) but "does the
no-stop geometry leave a positive mean" (it does not, except marginally).*

## 4. Caveats (from audit)

- **W1 — Lead is narrow and 4h-concentrated.** 14 lead cells / 9 instruments; **8 of 14 are 4h** (n=108–194),
  the highest-noise domain (same domain that carried EXP-060's spurious random-beaters). The high-count lead
  cells (GBPUSD-5m, AUDUSD-30m, GBPJPY-30m) have mean CI_low barely > 0 (0.037, 0.053, 0.088). P11 is met, but
  robustness leans on small-n cells — do not read this as a broad, stable edge.
- **W2 — Median overstates tradeable expectancy** (foregrounded above): the lead is a median phenomenon; the
  average M3 trade makes ≈0 gross, before costs.
- **I2 — Plan/code note:** analysis-plan §2 mislabeled the M3−RM3 contrast as *paired*; the code correctly used
  **independent** `contrast_ci` (matched-random are different events). The code is right; the report carries the
  correction.
- **I3 — Attribution breadth:** M3 vs RM3 attributes the lift to the **combined** harami+`/STRONG-STAT` signal,
  not separately to the harami pattern, the strong conditioning, or their interaction with MA direction (same
  convention as EXP-060).
- **Gross only:** no costs. Costs would erode the already-marginal mean further.

## 5. G2 routing consequence

Per the predeclared fork, `SUBSTRATE_LEAD_FOUND` means the single 014-B **G2 should not close
CF-HA-HARAMI-001** without a scoped MA-substrate follow-up. But EXP-060B reframes *what* that follow-up must
target: the binding constraint is no longer the signal (it works on MA) but the **skew / mean** — the no-stop
geometry that produces median≫mean. A follow-up that simply re-runs the MA signal under the current
V2A×ADV-NONE geometry will inherit the mean≈0 problem.

## 6. Recommended follow-ups (new scopes only — not extensions of EXP-060B)

1. **MA-substrate geometry vs the skew (highest priority).** Re-screen the MA-conditioned harami under
   **stop-bearing** adverse models (the registered 1:1 and `/ADV-EXTREME-rr1`) and capped favourable schemes,
   with the **mean** as a co-primary endpoint, to test whether a bounded-downside geometry converts the real
   median edge into a positive mean. D1 shows the 1:1 gap (0.49) is less than half the ADV-NONE gap (1.20) on
   MA — a stop may recover the mean at some median cost. New scope; would consume a candidate slot only at its
   own gate.
2. **Signal-component attribution on MA.** Isolate harami-pattern vs `/STRONG-STAT` conditioning vs MA-direction
   (e.g. harami-only and strong-only arms vs RM3) to locate the source of the MA edge — only if G2 routes to a
   SUBSTRATE follow-up.
3. **Cost-bearing screen** of any MA geometry that achieves a mean-positive P11 quorum (out of 014-B gross
   scope; future tradability phase).

These are new experiments; EXP-060B's scope is closed.
