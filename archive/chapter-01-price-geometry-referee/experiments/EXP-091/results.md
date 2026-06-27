# Results: EXP-091 — RSI-2 Fade Exit / Capture-Geometry Screen (TRAIN-only, gross + EXP-085 cost)

**Phase 021 · CF-MR-001 · HYP-002.** TRAIN-only, 20 EXP-090 member cells, 6 frozen exit arms, net of the
operator-ratified Phase-021 conservative cost (`D0-amendment-003`, F=0). Binding figure: net per-event
expectancy moving-block bootstrap one-sided lower bound (`net ci_low_1s`, Z=1.645); net-clear iff `>0`; arm
passes iff net-clears in ≥5 cells over ≥3 instruments (frozen D6/4a). Audit: **PASS** (no blocking findings;
numbers reproduce exactly; three forensic caveats carried below). 0 candidate slots, 0 counted TEST reads,
holdout sealed.

---

## 1. Headline

**Experiment verdict: `SCREEN_DELIVERED` — the screen is NOT empty.** Exactly one exit arm passes the frozen
quorum:

| Exit arm | Net-clearing cells | Distinct instruments | Quorum (≥5/≥3)? |
|---|---|---|---|
| **EXIT-RCT** (native, reversion-completion target) | **5** | **5** | **PASS** |
| EXIT-ERT (native, equilibrium-return target) | 0 | 0 | fail |
| ATR triple-barrier | 0 | 0 | fail |
| RSI-revert-on-close | 0 | 0 | fail |
| fixed-bar | 0 | 0 | fail |
| favourable partial/trail | 0 | 0 | fail |

RCT's five net-clearing cells: **EURUSD-1h, GBPUSD-1h, NZDUSD-1h, US2000-1h, USTEC-1h**.

Because at least one exit passes, the EXP-091 screen does **not** route G-021 NOT_TRADABLE. Per the design §4 /
D6 lifecycle, the screen **advances to EXP-092** (per-instrument cost-bearing sequence) carrying the surviving
exit (RCT) and its net-clearing cells — subject to the three caveats in §4, which materially shape what EXP-092
should carry.

## 2. What the data shows (per-stratum, LESSON-001)

**Availability is real and broad; the net edge is not.** Both native arms net-clear *gross* on **20/20** cells
(RCT and ERT each `gross_ci_low>0` everywhere); the conventional arms clear gross on only 7–8/20. RCT hits its
reversion-completion target on **~99%** of events (`terminal_fav` 0.989–0.997) for a gross mean of **~0.27–0.30
ATR on every cell**, 15m and 1h alike. The fade's gross favourable availability (the G-020 finding) is confirmed
to survive a real, intrabar-filled exit rule.

**Conservative cost erases it on all but the cheapest 1h cells.** Net = gross − cost (financing F=0 by
`D0-amendment-003`, so net = gross − transaction cost exactly). The result is a **pure ATR-normalized
cost-geometry** outcome:

- The round-trip is a fixed bps figure, converted to price and divided by the entry **ATR(14)**. A 15m bar's
  ATR is far smaller than a 1h bar's, so the *same* round-trip costs **~0.6 ATR on 15m vs ~0.24–0.30 ATR on 1h**.
- Gross is ≈ domain-invariant (~0.28 ATR); cost is not. So net is deeply negative on every 15m cell (cost ≈ 2×
  gross) and hovers around zero on 1h, turning positive only on the lowest-bps / larger-ATR instruments.
- **RCT net-clears 0/10 on 15m and 5/10 on 1h.** Every 15m cell is net-negative for every arm.

This is exactly the programme's honest prior — *availability ≠ capturable edge* — realized: the short ~3-bar,
~0.28-ATR gross geometry leaves no room for conservative cost on the faster domain.

**The native intrabar machinery decisively beats reactive exit-on-close (RCT vs RSI-revert-on-close).** The clean
A/B — proactive resting limit + 1m intrabar fill (RCT) vs exit at the domain close on RSI₂-cross-50
(RSI-revert) — favours RCT in **20/20 cells** (per-cell net Δ range +0.223…+0.293, median **+0.261 ATR**;
Wilcoxon p ≈ 1.9e-6, descriptive/non-binding). Proactive intrabar capture is worth ~0.26 ATR per event over the
reactive analog — the phase's organizing hypothesis is **supported descriptively**. Note this is an
*RCT-specific* win: the other native, ERT, fails entirely (its equilibrium-return target is farther/slower, so it
holds longer into adverse moves and never net-clears). "Natives beat contrast" is therefore true only of RCT, not
of the native pair as a class.

## 3. Interpretation-guide resolution (predefined in analysis-plan §"Interpretation Guide")

- **≥1 arm passes ⇒ `SCREEN_DELIVERED`, non-empty, advance to EXP-092.** ✓ RCT passes. *Capture lever is
  non-empty on TRAIN net-of-cost* — but only on 1h (see §4).
- **Native beats contrast** ⇒ supported descriptively for RCT (20/20, median Δ +0.261, p small). ERT does not;
  report plainly.
- **Cell net-clears gross but not net ⇒ cost is the binding constraint.** ✓ This is the dominant pattern: 20/20
  gross-clear for the natives collapsing to ≤5 net-clear. Attribution: transaction cost (financing is 0 by
  amendment); the collapse tracks ATR-normalized bps, not holding duration.
- **Mean-vs-median split (median ≤ 0 while mean lower bound > 0) ⇒ EXP-089 signature persists; the mean lower
  bound is binding, disclose the median, do not promote on it.** ✓ Triggered — see §4.3.

## 4. Caveats binding on the verdict and the EXP-092 hand-off

The mechanical screen verdict (RCT passes 5/3) reproduces exactly and is firm *as computed*. But the audit's
verdict forensics surface three properties of that pass that the EXP-092 candidate selection and the eventual
G-021 narrative must carry. None flips the screen count; all three constrain how much the pass should be relied on.

### 4.1 The pass is entirely a 1h, low-cost-instrument phenomenon
RCT clears 5/10 on 1h and **0/10 on 15m**. The "RCT is tradable on TRAIN net-of-cost" reading applies **only to
1h cells of the cheapest instruments** (EURUSD/GBPUSD/NZDUSD 3–4 bps, USTEC 5 bps, US2000 6 bps with a large
ATR). It does **not** generalize to 15m or to higher-cost majors (GBPJPY-1h, USDJPY-1h, EURJPY-1h, USDCHF-1h all
fail). EXP-092 should carry a **1h-scoped** candidate set, not a domain-pooled one.

### 4.2 The pass is boundary-fragile
Four of the five clearing cells have `net_ci_low` ≥ +0.039; the fifth, **GBPUSD-1h, is +0.0043** — essentially
touching the zero floor. Drop that one cell and RCT = 4 cells → fails the 5-cell quorum. The pass clears the
quorum by a single marginal cell. This argues for the §8-3 "smallest defensible set" discipline at EXP-092/093:
the robust core is **USTEC-1h and US2000-1h** (see §4.3), not the full five.

### 4.3 On 3 of 5 clearing cells the net edge is mean/right-tail-carried
The binding endpoint is the **mean** lower bound (scoped, matching EXP-090) — legitimately positive on all five.
But the co-reported **median** is negative on three of them:

| Clearing cell | net_mean | net_median | net_ci_low | Read |
|---|---|---|---|---|
| USTEC-1h | +0.121 | **+0.040** | +0.108 | robust (mean & median > 0) |
| US2000-1h | +0.117 | **+0.028** | +0.104 | robust (mean & median > 0) |
| EURUSD-1h | +0.061 | −0.010 | +0.047 | mean/tail-carried |
| NZDUSD-1h | +0.050 | −0.005 | +0.039 | mean/tail-carried |
| GBPUSD-1h | +0.018 | −0.052 | +0.004 | mean/tail-carried + boundary |

On the three mean/tail-carried cells the *typical* trade loses after cost; the positive expectancy comes from the
favourable right tail. This is the predeclared EXP-089 mean-fragile signature persisting into the net exit. It is
not a verdict-flip (the gate measures the mean, the correct scoped endpoint), but EXP-092 should read these cells
shape-aware and weight **USTEC-1h / US2000-1h** (mean *and* median positive) as the defensible core.

## 5. Disclosed companion (non-binding): cost sensitivity

Under the predeclared faster round-trip variant (`RT/2`), RCT net-clears **14** cells vs 5 binding — confirming
the screen is **cost-dominated, not signal-absent**. The binding result uses the operator-ratified conservative
table (`D0-amendment-003`, hash `fa7c887…`); the shared `xen.capgeo_cost.COST_CONSTANTS` was not mutated
(Phase-018 integrity). The companion is a sensitivity disclosure, never substituted for the binding screen.

## 6. Integrity

Determinism replay passed (USTEC-15m + EURUSD-1h; net_ci_low / net_clear / n_resolved frame-identical); five
headline CSVs SHA-256-pinned. Real prices throughout (real touched fill levels, real ATR; no HA/Renko). TRAIN
sub-split only; analysis-TEST and final-30% global holdout never sliced (`holdout_untouched=true`). Resolution
0.9943–0.9996; min n_resolved 3835 — no thin-cell power concern. PARTIAL-TRAIL used the coarser domain-bar
two-leg resolver (disclosed; non-primary contrast; fails anyway).

## 7. Conclusion & next step

**The bare RSI-2 fade's gross availability does convert to a positive net-of-conservative-cost expectancy — but
only via the native reversion-completion target (RCT), only on 1h, only on the cheapest instruments, and on a
boundary-fragile, partly mean/tail-carried basis.** The screen is non-empty, so Phase 021 advances rather than
closing at G-021 NOT_TRADABLE.

**Next experiment — EXP-092** (per-instrument cost-bearing sequence, TRAIN-only, 0 reads / 0 slots): take the
surviving exit **RCT** and produce the hash-pinned `SEQUENCE_PASS` candidate set + phase Holm rule. The §4 caveats
recommend a **1h-scoped, smallest-defensible set centered on USTEC-1h and US2000-1h** (the mean-and-median-positive
cells), with EURUSD-1h / NZDUSD-1h as secondary and GBPUSD-1h flagged boundary-marginal. EXP-092 must not promote
on the median-negative cells and must keep the carried set ≤1–2 cells per the §8-3 TEST-read economy. No follow-up
re-parameterizes any frozen constant; the deferred levers (15m capture, regime, contrarian, 25/75, 4h) each remain
behind their own `D0-amendment-*`.
