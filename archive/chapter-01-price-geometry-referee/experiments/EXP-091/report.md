# EXP-091 — RSI-2 Fade Exit / Capture-Geometry Screen (TRAIN-only, gross + EXP-085 cost)

**Phase 021 (CF-MR-001 batch 2) · `CF-MR-001/HYP-002` · 2026-06-24 · Verdict: `SCREEN_DELIVERED` (non-empty —
one exit passes) · Audit: PASS · 0 candidate slots · 0 counted TEST reads · holdout sealed.**

## Question

The bare RSI-2 fade (CORE) was admitted at G-020 on a TRAIN-only *availability* verdict (gross ~0.75-ATR / ~3-bar
favourable excursion). EXP-091 asks the first *tradability-direction* question: over the frozen exit slate, on the
20 EXP-090 member cells, **does any exit produce a positive per-event expectancy that survives the EXP-085
conservative cost** — and **do the native intrabar reversion targets beat the reactive conventional contrast**?
This is the first Phase-021 experiment to resolve the *real* bare-fade exit outcomes (EXP-090 never read them).

- **Binding rule (frozen D6/4a):** an (exit × cell) **net-clears** iff its net per-event expectancy moving-block
  bootstrap one-sided lower bound (`net ci_low_1s`, Z=1.645) > 0; an exit **passes** iff it net-clears in **≥5
  cells over ≥3 instruments**. **Empty screen ⇒ G-021 NOT_TRADABLE at 0 reads.**
- **Scope:** 20 member cells (10×15m + 10×1h, 13 instruments); 6 frozen exit arms; TRAIN sub-split only; net of
  the operator-ratified Phase-021 conservative cost (`D0-amendment-003`, F=0); real OHLC throughout. No candidate
  selection, no Holm rule, no TEST read (those are EXP-092 / EXP-093).

## Result

**One arm passes: EXIT-RCT (the native reversion-completion target).** The other five net-clear in zero cells.

| Exit arm | Net-clearing cells | Instruments | Quorum (≥5/≥3)? |
|---|---|---|---|
| **EXIT-RCT** (native) | **5** | **5** | **PASS** |
| EXIT-ERT (native) | 0 | 0 | fail |
| ATR triple-barrier | 0 | 0 | fail |
| RSI-revert-on-close | 0 | 0 | fail |
| fixed-bar | 0 | 0 | fail |
| favourable partial/trail | 0 | 0 | fail |

RCT's five net-clearing cells: **EURUSD-1h, GBPUSD-1h, NZDUSD-1h, US2000-1h, USTEC-1h** (all 1h, 5 distinct
instruments). Because at least one exit passes, the screen is **not** empty and Phase 021 **advances to EXP-092**
rather than closing at G-021 NOT_TRADABLE.

## Why (mechanism)

A **pure ATR-normalized cost-geometry** result, not a signal-strength result:

- **Availability is real and broad.** Both native arms net-clear *gross* on 20/20 cells; RCT hits its
  reversion-completion target on ~99% of events (`terminal_fav` 0.989–0.997) for a gross mean of **~0.27–0.30 ATR
  on every cell**, 15m and 1h alike. The G-020 availability survives a real intrabar-filled exit.
- **Cost erases it everywhere except cheap 1h cells.** The round-trip is a fixed bps figure ÷ entry ATR(14). A
  15m bar's ATR is far smaller than a 1h bar's, so the *same* round-trip costs **~0.6 ATR on 15m vs ~0.24–0.30
  ATR on 1h**. Gross is ≈ domain-invariant, cost is not — so net is deeply negative on every 15m cell (cost ≈ 2×
  gross) and positive only on the cheapest / largest-ATR 1h cells. **RCT clears 0/10 on 15m, 5/10 on 1h.** This is
  the programme's honest prior — *availability ≠ capturable edge* — realized exactly as predicted for a short
  ~3-bar, ~0.28-ATR-gross geometry.
- **Native intrabar machinery beats reactive exit-on-close (RCT vs RSI-revert-on-close).** RCT wins the clean A/B
  in **20/20 cells** (per-cell net Δ median **+0.261 ATR**; Wilcoxon p ≈ 1.9e-6, descriptive). Proactive resting
  + 1m intrabar fill is worth ~0.26 ATR/event over the reactive analog. But this is RCT-specific: the other
  native, ERT (return-to-EMA10, a farther/slower target), holds longer into adverse moves and fails entirely.
  "Natives beat contrast" is true of RCT, not of the native pair as a class.

## Caveats binding on EXP-092 (from the audit verdict forensics)

The mechanical pass (5/3) reproduces exactly and is firm as computed, but three properties constrain how much it
should be relied on. None flips the count; all three are mandatory context for the candidate selection:

1. **Domain-conditional — 1h only.** RCT is 0/10 on 15m, 5/10 on 1h. The "tradable on TRAIN net-of-cost" reading
   applies only to 1h cells of the cheapest instruments; EXP-092 should carry a **1h-scoped** candidate set.
2. **Boundary-fragile.** Four of the five clearing cells have `net_ci_low` ≥ +0.039; the fifth, **GBPUSD-1h, is
   +0.0043** (touching zero). Drop it and RCT = 4 cells → fails the quorum. The pass clears by one marginal cell.
3. **Mean/tail-carried on 3 of 5.** The binding endpoint is the **mean** lower bound (positive on all five), but
   the co-reported **median** is negative on EURUSD-1h, GBPUSD-1h, NZDUSD-1h (typical trade loses after cost;
   edge carried by the favourable right tail — the predeclared EXP-089 signature). Only **USTEC-1h and US2000-1h**
   have mean *and* median positive — the **defensible robust core** for EXP-092.

**Disclosed companion (non-binding):** under the faster round-trip variant (RT/2) RCT net-clears 14 cells vs 5
binding — confirming the screen is **cost-dominated, not signal-absent**.

## Integrity

Determinism replay passed (USTEC-15m + EURUSD-1h; net_ci_low / net_clear / n_resolved frame-identical); 5
headline CSVs SHA-256-pinned. Real touched fill levels + real ATR throughout (no HA/Renko). TRAIN sub-split only;
analysis-TEST and final-30% global holdout never sliced (`holdout_untouched=true`). Resolution 0.9943–0.9996; min
n_resolved 3835 (no thin-cell power concern). Cost table is Phase-021-local (`D0-amendment-003`, hash
`fa7c887…`); shared `xen.capgeo_cost.COST_CONSTANTS` untouched (Phase-018 integrity). PARTIAL-TRAIL used the
coarser domain-bar two-leg resolver (disclosed; non-primary; fails anyway). Audit: **PASS** (0 Critical, 3
Warning, 3 Info — all Warnings shown unable to move the mechanical screen verdict).

## Conclusion & next step

**The bare RSI-2 fade's gross availability does convert to a positive net-of-conservative-cost expectancy — but
only via RCT, only on 1h, only on the cheapest instruments, and on a fragile, partly mean/tail-carried basis.**
The screen is non-empty, so Phase 021 advances.

**Next — EXP-092** (per-instrument cost-bearing sequence, TRAIN-only, 0 reads / 0 slots): take RCT and produce the
hash-pinned `SEQUENCE_PASS` candidate set + phase Holm rule, **1h-scoped, smallest-defensible**, centered on
**USTEC-1h and US2000-1h** (mean-and-median-positive), with EURUSD-1h / NZDUSD-1h secondary and GBPUSD-1h flagged
boundary-marginal — not promoting on the median-negative cells, ≤1–2 cells carried to the eventual EXP-093 TEST.
No follow-up re-parameterizes any frozen constant; the deferred levers (15m capture, vol-regime, contrarian,
25/75, 4h) each remain behind their own `D0-amendment-*`.

## Signal-registry disposition

**Registry-relevant — updated in this change.**
- **Multiplicity registry** (Phase 021 batch, exit-families item): EXP-091 outcome recorded — **EXIT-RCT clears
  the screen quorum (5 cells / 5 instruments, 1h)**; **EXIT-ERT, ATR-barrier, RSI-revert-on-close, fixed-bar,
  favourable partial/trail each net-clear 0 cells → die at the screen** (retained in the file drawer, not
  reopened by re-parameterization). EXP-091 row advanced PLANNED → COMPLETE.
- **Candidate family** `cf-mr-001.md`: EXP-091 outcome appended; family stays `ADMITTED (BINDING)`, Phase 021
  OPEN and **advancing** (screen non-empty); 0 additional slots.
- **Test-read ledger:** **no counted read** — EXP-091 reads the TRAIN sub-split only; all 48 strata stay **0/2
  open**, holdout sealed (TRAIN-only disclosure entered, consistent with EXP-090).

## Artifacts

- Scope `python/experiments/EXP-091/scope.md` · Analysis plan `analysis-plan.md`
- Code `code/run_experiment.py` (reuses EXP-090 `xen.intrabar_fill` substrate verbatim)
- Results `results/` (`screen_per_cell_arm.csv`, `quorum_per_arm.csv`, `native_vs_contrast.csv`,
  `cost_decomposition.csv`, `cost_sensitivity_faster.csv`, `run_metadata.json`)
- Plots `plots/` (quorum bar, net ci_low heatmap, gross→net cost decomposition, RCT-vs-RSI-revert A/B scatter)
- Audit `audit.md` · Interpretation `results.md` · Governance `governance/`
