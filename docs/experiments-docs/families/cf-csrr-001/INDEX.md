# CF-CSRR-001 — Cross-Sectional Consensus-Residual Reversion (Family Detail Index)

Authoritative detailed catalog of CF-CSRR-001 experiments (Chapter 02, checkpoint-009). Family
card: [`../../../signal-registry/candidate-families/cf-csrr-001.md`](../../../signal-registry/candidate-families/cf-csrr-001.md).
Origin / 7-axis decomposition: [origin.md](origin.md). Checkpoint:
[`../../checkpoints/2026-07-06-009-cf-csrr-001-cross-sectional-residual-reversion/design.md`](../../checkpoints/2026-07-06-009-cf-csrr-001-cross-sectional-residual-reversion/design.md).

**Thesis.** On a co-moving basket, a member's move away from the cross-sectional **consensus** is
transient idiosyncratic flow and reverts toward consensus within a bounded horizon. Reversion
endpoint (distinct from CF-XSECT-001's directional relative-strength). Availability screened first,
execution-agnostic; tradability via the V5 active-entry/passive-exit vehicle (EXP-023).

**Status:** REGISTERED (G0), checkpoint-009 open. Family status transitions occur ONLY at the
checkpoint retrospective (operator-signed); experiment cards below carry evidence, not dispositions.

## Table of Contents

- [EXP-021 — Currencies availability + A×B×C×D component screen](#exp-021--currencies-consensus-residual-reversion-availability--abcd-component-screen)
- [EXP-022 — Indices availability + A×B×C×D component screen](#exp-022--indices-consensus-residual-reversion-availability--abcd-component-screen)

---

## EXP-021 — Currencies consensus-residual reversion availability + A×B×C×D component screen

**Status**: COMPLETED — NOT SUPPORTED (availability; operator verdict)
**Date**: 2026-07-06
**Instruments**: 7 USD pairs (EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD); JPY crosses
excluded (operator-approved deviation).
**Data Views / Feature Categories**: 4h TRAIN (first 49%, 3,526 bars, 2021-06→2023-11); 1D branch
disclosure-only (NON-REGISTERED). Real OHLC; open-to-open returns. Execution-agnostic (no fills/P&L).

### Hypothesis Tests

1. **HYP-001**: On the USD-strength-aligned Currencies basket at 4h, is the consensus-residual
   mean-reverting (VR<1 / finite short half-life), and which (A×B×C×D) construction maximises
   signal-conditional residual-reversion Δ over a random-index + random-timing twin beyond a
   multiplicity-adjusted permuted-axis null?

### Scope

- **Instruments**: 7 USD pairs, signed to USD strength (quote σ=−1, base σ=+1).
- **Consensus**: USD-strength alignment (JPY crosses excluded — a scalar-USD consensus cannot define
  their residual; operator-approved deviation from card "decompose where possible").
- **Anchor**: session/daily-reset causal accumulation anchor (weekly reset on the 1D branch).
- **Estimand**: `ρ=−sign(s_i)·idio_i(t,h)`, `idio=g_i−G` = consensus-hedged forward open-to-open
  return; horizon `h=2·HL` (per-instrument AR(1) half-life).
- **Sweep**: A{median,mean} × B{raw,÷σ_t} × C{single-worst,all>k} × D{hedged,unhedged} = 16 cells × 7
  strata. Threshold `k`=trailing-median of per-bar max|s| (coarse, one primary value).
- **Controls**: random-index twin; random-timing battery (25 seeds, L-19); permuted-axis within-bar
  identity null (primary, max-stat multiplicity, 1000 perms); tripwire = temporal block-permute of
  the (s→forward) pairing.
- **Exclusions**: TEST band + final-30% holdout never loaded; 0 counted reads. Not tested: V3
  weighted-implied consensus, currency-strength-vector build, range-scaled B, V5 execution (E/F).
- **Constraints**: TRAIN-only; causal ≤ t-1; no `xen.adjudication` (no accounting object).

### Results / Observations

- **Substrate**: VR(2)<1 on **28/28** instrument×A×B cells (median 0.87), VR(6)≈0.4, AR(1)
  HL 1.1–1.8 4h-bars. VR<1 on 27/28 1D cells (median 0.85). Substrate kill NOT triggered.
- **Availability (multiplicity-adjusted)**: uncorrected 5/112 cells clear ci_low>0 + p_perm<0.05 +
  beat both twins; under max-stat over 16 cells/instrument, **1** survives fw_p<0.05: AUDUSD
  median/raw/single/**unhedged** +9.38 bps (fw_p 0.008). **0 hedged (mechanism-faithful) cells
  survive on any instrument** (best USDCHF fw_p 0.083; AUDUSD-hedged +4.48 fw_p 0.68; USDCAD +3.34
  fw_p 0.54).
- **Per-instrument mean ρ (across 16 cells)**: AUDUSD +2.11, NZDUSD +2.08, GBPUSD +1.68, USDCAD
  +1.66, USDCHF +1.39, EURUSD −0.98, **USDJPY −2.42 (0/16 cells positive; 635 single-worst events)**.
- **Alpha/beta** (single-worst raw): hedged=alpha, (unhedged−hedged)=beta. AUDUSD α+4.5/β+4.9,
  NZDUSD α+1.6/β+3.5, USDCAD α+3.3/β+0.5, USDCHF α+2.5/β−4.2.
- **Variants**: V1/V5-screen pooled +0.43 bps, V2 +0.77, V4 +0.65 — all 0/7 survive multiplicity.
- **Integrity**: tripwire collapses ρ→0 on all real-positive cells (collapse ≈ 0); holdout sealed;
  causal ≤ t-1; 0 reads/0 slots. Leak-clean.
- **AUDUSD actual time-in-market (overlap-aware)**: 4h 21.0% overlap / 17.2% sequential (h=4, 297
  events / 151 trades); 1D 7.8%/7.1% (24 events). 1D AUDUSD: 16/16 positive point estimates but
  0/16 significant, MDE≫effect (UNPOWERED).
- **Disclosures**: h=2·HL not load-bearing (per-instrument sign stable across 1·/2·/3·HL, 5/7); 1D
  branch reverts but UNPOWERED (MDE med 21.8 bps ≫ effects), sign reorders vs 4h; naive-median
  contrast not run.

> Note: no interpretation in this block — see report.md.

### Hypothesis-Specific Conclusion

**NOT SUPPORTED (availability).** The consensus residual mean-reverts, but no mechanism-faithful
(hedged) construction delivers multiplicity-robust signal-conditional residual reversion on any
instrument; the sole family-wise survivor is AUDUSD *unhedged* = market drift (hedged twin dead).
Heterogeneous (USDJPY continues, dominates selection) and borderline-powered (~2–4.5 bps ≈ MDE) on a
single 2.4-year regime. The *literal* predeclared availability kill criterion is not met (AUDUSD
unhedged separates) → not an auto-retire; disposition reserved for checkpoint-009 retrospective.

### Hypothesis-Agnostic Observations

- The cross-sectional consensus residual **is a mean-reverting level** on FX majors at 4h and 1D
  (VR<1) — substrate is real; the failure is that idiosyncratic reversion net of the common USD
  factor is thin and doesn't clear multiplicity.
- "Fade the single-worst deviator" is structurally exposed to whichever currency is trending
  (USDJPY 2021–23) — single-worst selection captures trends, not just noise.
- Much of the apparent per-instrument edge is market beta, not idiosyncratic alpha (AUD/NZD ~half).
- USDCAD carries the cleanest near-pure idiosyncratic alpha (+3.3, beta +0.5) but still
  multiplicity-fragile.
- Daily cadence is too sparse over ~2.4y to adjudicate availability (UNPOWERED) — 4h is the right
  cadence for this basket.

---

## EXP-022 — Indices consensus-residual reversion availability + A×B×C×D component screen

**Status**: COMPLETED — NOT SUPPORTED (availability; operator verdict)
**Date**: 2026-07-06
**Instruments**: 10-index equity basket (USTEC, US500, US2000, US30, JP225, AUS200, EU50=`STOXX50`,
GER40=`DE40`, HK50, UK100). Effectively a US-cash sub-basket at 4h (coverage-limited; see below).
**Data Views / Feature Categories**: 4h TRAIN (first 49%, panel 2021-06-02→2023-12-18, 3,253 union bars);
Addendum A1 re-aggregation `min_coverage=0.50` (3,912 bars) + 1D cross-check. Real OHLC; open-to-open.
Execution-agnostic (no fills/P&L/estimand gate).

### Hypothesis Tests

1. **HYP-002**: On the native single-factor equity basket at 4h, is the consensus-residual mean-reverting
   (VR<1), and which (A×B×C×D) construction maximises signal-conditional **idiosyncratic (hedged)**
   residual-reversion Δ over a random-index + random-timing twin beyond a multiplicity-adjusted
   permuted-axis (max-stat) null? Mirror of HYP-001 on the native (global-equity-risk) single-factor basket.

### Scope

- **Instruments**: 10 indices, σ_i=+1 all (rising index = risk-on; NO sign-alignment needed — native single
  factor, unlike the Currencies USD-strength problem).
- **Consensus**: axis A ∈ {median, equal-wt mean} of accumulated log-moves from a causal daily anchor.
- **Builds (operator-mandated all three)**: (N) all-10 naive [PRIMARY]; (A) per-bar activity-gated;
  (R) session-coherent regional blocs {US:4, Europe:3, Asia:3}.
- **Anchors (both)**: (P) 00:00-UTC daily reset [PRIMARY]; (S) per-index session-open reset.
- **Estimand**: `ρ=−sign(s_i)·idio_i(t,h)`, idio=g_i−G = consensus-hedged forward open-to-open; h=2·HL
  (per-instrument AR(1) half-life).
- **Sweep**: A{2}×B{raw,÷σ_t}×C{single-worst,all>k}×D{hedged,unhedged} = 16 cells × 10 strata × 6
  constructions. Threshold k=trailing-median of per-bar max|s|.
- **Multiplicity (design §3.1)**: significance ONLY at PRIMARY (N×P) max-stat over 16 cells; other 5
  constructions are cross-construction robustness (downgrade a lead, never manufacture one). Bookable =
  clears primary max-stat ∧ sign-stable both anchors ∧ survives ≥2/3 builds.
- **Controls**: random-index twin; random-timing battery (25 seeds, L-19); permuted-axis within-bar identity
  null (primary, 1000 perms); tripwire = temporal block-permute of (s→forward) pairing.
- **Exclusions**: TEST band + final-30% holdout never loaded; 0 counted reads. V5 execution (E/F) deferred
  to EXP-023.
- **Amendment A1** (operator, post-primary-verdict): coverage-corrected fair-basket rerun `min_coverage`
  0.90→0.50 (+1D cross-check) to admit EU/Asia — additive, primary verdict not invalidated.

### Results / Observations

- **Substrate**: VR(2)<1 on **40/40** primary instrument×A×B cells (mean 0.52–0.87), VR(6)≈0.19–0.53, AR(1)
  HL ~0.8–1.9 4h-bars; 216/240 (90%) across all 6 constructions. Substrate kill NOT triggered.
- **Primary availability (max-stat)**: **0/74** powered-n cells clear uncorrected ci_low>0 & mean≥1 bp;
  **0/9** instruments fw_p<0.05 (best JP225 0.33, US2000 0.37). Every primary cell UNPOWERED for the ≥1 bp
  band (MDE 3.9–21.7 bps). Twins ≈0 at primary.
- **Power reality**: N/P single-worst events — JP225 395, USTEC 239, US2000 209, UK100 119, GER40 64,
  AUS200 53, US30 28, US500 1, EU50 0, HK50 0 (§8 projection ~10× optimistic; `argmax|s|` concentrates).
- **Disclosed leads (non-primary, NOT bookable)**: USTEC R_US/S hedged +4.71 bps (n=582, p_perm 0.008,
  tripwire 4.40→0.16); US2000 A/S fw_p 0.001 but drift-heavy (unhedged +8.4 / hedged +3.8).
- **USTEC probe**: axis-coherent (all 8 hedged cells +), sign-stable both TRAIN halves; **genuinely
  idiosyncratic** — alpha +4.71 vs raw +0.30, beta 1.185 (removing consensus ADDS signal); **USTEC-specific**
  (US-bloc siblings null: US30 −1.8, US2000 ≈0 hedged/drift, US500 n=5). BUT hardened block-boot ci_low −0.58
  (does NOT exclude zero), effect ≈ MDE 5.28, event-rate 18.4% / held-fraction 73.6%.
- **Coverage forensics**: 90%-coverage 4h filter culls EU50 −56% (→0 events) / HK50 −80% (→0); ≥4-member
  join negligible on top; UTC anchor drops no bars. EU/Asia = UNPOWERED (no test), not CONTRADICTED (B-5).
- **Addendum A1 (cov0.50)**: HK50 0→**519 events, now powered — a clean null** (US-cash NOT-SUPPORTED
  generalises); EU50 still 0 at 4h & 12 at 1D (structurally UNPOWERED); USTEC lead survives (+4.79, p_perm
  0.002, tripwire-clean, same underpowered CI). No hedged/idiosyncratic EU/Asia lead anywhere.
- **Integrity**: tripwire collapses ρ→0 (0.32 vs 3.61 bps; A1 0.44 vs 6.78); holdout sealed
  (`holdout_rows_read=0`, panel ends 2023-12-18); causal ≤t-1; golden trace bit-verifiable; no local
  accounting. 0 reads/0 slots.

> Note: no interpretation in this block — see [report.md](../../../../python/experiments/EXP-022/report.md).

### Hypothesis-Specific Conclusion

**NOT SUPPORTED (availability).** The equity consensus residual mean-reverts, but no mechanism-faithful
(hedged) construction delivers multiplicity-robust idiosyncratic reversion at the primary construction on any
powered instrument (0/74 powered cells clear; best fw_p 0.33). Powered-null for the US-cash cluster + HK50;
UNPOWERED (not contradicted) for EU50 alone. Substrate kill NOT triggered and no availability kill literally
met (USTEC separates in a non-primary construction) → not an auto-retire; disposition reserved for the
checkpoint-009 retrospective.

### Hypothesis-Agnostic Observations

- The cross-sectional consensus residual **is a mean-reverting level** on the equity basket too (VR<1
  unanimous) — substrate is real on both baskets; the failure is idiosyncratic reversion net of the common
  factor being thin / multiplicity-fragile (same shape as EXP-021 Currencies).
- The **USTEC R_US/session-open hedged** residual is genuinely idiosyncratic (not drift) and member-specific
  (siblings null) — the one concrete registered-branch candidate; parallels EXP-021's AUDUSD/USDCAD leads.
- `argmax|s|` single-worst on a 10-member basket is a power sink (concentrates events on high-vol members);
  a future primary needs `all>k` or per-instrument-cap selection to reach the ≥1 bp band.
- At 4h the 90%-coverage filter makes the "10-index" basket effectively US-cash-heavy; EU50 is untestable at
  any coverage/domain on a 2.5-yr TRAIN — cross-sectional EU/Asia index work needs a longer panel.
