# CF-MR-004 — Cross-Domain Mean-Reversion (Fixed-Parameter Cross-Instrument Spreads)

**Status:** **RETIRED (2026-07-03, operator decision D1)** — `EXP-014c (HYP-004) COMPLETE —
CREDIBLE_NEGATIVE_RETIRE`: both prespecified primaries (4h JP225 + EURUSD, e3/none/z20) powered,
bite-non-vacuous, net-fail under the frozen referee (JP225 +0.26 bps/bar ci_low −1.84; EURUSD
+0.28 ci_low −0.46). The measurement-matched bracket was the family's declared last shot; the
confirmed availability does not convert because the traded entry (limit fill at the band touch,
D = z\*σ) is a **different conditioning event** than the measured one (open after confirmed
close-breach, depth ≥ band) — JP225 realized TP-share 0.52 vs measured p_inward 0.696. No exit
rule unlocks the entry (E0→E3 attribution). Disclosure: 4 REJECT_LEAK extend/z15 cells + a
robust cross-instrument extend-arm field (53 non-admitted cells net ci_low>0, year-stable
2021–2024, 50–85% survives phase-shift) → own-price ladder harvest, **spun out to CF-MR-005**
(REGISTERED 2026-07-03; mechanism characterisation first). Re-opening CF-MR-004 requires a new
entry object matched to the measured conditioning event (confirmed-breach entry), under a new D0.
0 slots, 0 counted reads, holdout sealed, referee untuned. `python/experiments/EXP-014c/{report,audit}.md`.

**Prior status (retained):** `EXP-014b (HYP-003) COMPLETE — REJECT_LEAK (audited; C1/C2 fixed analysis-only). HYP-004
(EXP-014c lean bracket rerun) OPEN — the family's last shot before retire.` (2026-07-03).
Prior: EXP-014 (HYP-002) NOT-TRADABLE, RETIRE was recommended; superseded by the amendment-003/004
exploratory track (operator-directed). EXP-013 record
retained (CONFOUNDED, never deleted). **EXP-014 discharges L-14** — both proposal-named exits fire
(form-1 event-reversion + refreshing form-2), so the faithful strategy was tested; it STILL closes
NOT-TRADABLE per stratum (0/38 net- AND gross-admit under the frozen 4h referee, homogeneous/no-masking),
and availability does not separate at 4h (native reversion-completion Δ vs dislocation-matched control
ci_low<0 on ~all cells). Mechanism = capture-vs-dispersion wash — same cost/capture veto that closed
CF-MR-002 + CF-MR-003. Power caveat: 19/38 cells bite-fail (per-cell referee underpowered on a discrete
round-trip bracket; the credible null rests on the bite-passing subset, which also all reject). 0 counted
reads, 0 slots, holdout sealed, referee untuned. See `python/experiments/EXP-014/{report,audit}.md`.

**Prior status (retained):** `EXP-013 CONFOUNDED (vehicle-incomplete) → HYP-002 faithful redo (EXP-014)`
(amendment 2026-07-02). **EXP-013's `NOT_TRADABLE` is DOWNGRADED** — the review
(`amendment-001-faithful-full-strategy-redo.md`) found the strategy that ran was not the strategy proposed:
**form-1 (event-driven back-to-anchor) exit absent** and **form-2 TP frozen at entry** (never refreshed as
the moving anchor/peer basket drifts), so peer-side reversion never exits → positions ride to the time
horizon and book adverse. The "~30% favorable-hit" was the **static-TP hit rate**, not the reversion rate;
the null is confounded, not a family reading. **Do not reinforce the terminal-branch prior on EXP-013.**
Additional gaps: MR characterisation not independent + only 2/6 stages (VR+HL); no re-entry; S8 shipped
pair−median-60 vs the doc's basket−median-90. → **EXP-014** (HYP-002) is the from-scratch faithful redo.
0 counted TEST reads, holdout sealed.
**Family ID:** CF-MR-004. **Chapter:** 02 (cTrader-primary era).
**Origin:** operator renewal proposal `.ignore/idea/README.md` (mean-reversion family renewal),
concretized via `/research-pipeline` 2026-07-01. Source idea files:
- `.ignore/idea/original-mean-reversion-screening-framework.md` (6-stage MR screen)
- `.ignore/idea/original-phase002-thoughts.md` (cross-domain MR design)
- `.ignore/idea/new-anchor-series-suggestions.md` (3 new cross-instrument spread designs)
- `.ignore/idea/post-exps-reflection.md` (contamination concerns from CF-MR-003)

## Thesis

Capture deviations of an instrument from a higher-domain **cross-instrument anchor series** (a
price-derivable, mean-reverting spread). Extreme deviations signal entry; **precalculated limit
orders** are placed at the extreme level and left **set-and-forget** until filled or refreshed by
the next anchor bar. Exit = precalculated favorable limit at the anchor mean.

## Key design changes from CF-MR-003 (the closed predecessor)

| # | Change | Rationale |
|---|--------|-----------|
| 1 | **From-scratch mandate** — all family-specific components (spread, entry/exit, z-score) are new code; no reuse of CF-MR-003 implementations | L-13; proposal's contamination concern |
| 2 | **Fixed-parameter spreads** (3 new series) — fixed weights/β, no rolling re-estimation | Simpler, more robust than S5's rolling-β; `new-anchor-series-suggestions.md` |
| 3 | **No lower-domain layer** — precalc limit orders, set-and-forget, refreshed per anchor bar | Proposal: lower-domain redundant for precalc orders |
| 4 | **Informative-not-gating thresholds** — MR screen characterizes, does not disqualify | L-12; proposal's concern about arbitrary thresholds |
| 5 | **Full faithful cTrader from the start** — no initial simplifications | Operator mandate |
| 6 | **Full-strategy-first** — availability + tradability from one emission | Operator-confirmed fork |

## Why this is not a re-parameterization of CF-MR-003

CF-MR-003 is RETIRED (availability real, NOT-TRADABLE at 1h + 15h; cost/capture veto).
Re-opening requires "a genuinely cheaper capture mechanism or a lower-cost universe, not a
re-parameterization" (`cf-mr-003.md`). CF-MR-004 is a **new family**:
- 3 new anchor series (S6/S7/S8) are genuinely new constructions, not re-parameterizations of S5.
- Execution model different (no lower-domain, precalc limit orders only).
- Evaluation vehicle re-derived from family's mechanism (L-13).
- S5 redo = from-scratch reimplementation, not reuse of CF-MR-003 S5 code.

**Risk acknowledged:** cost/capture veto closed CF-MR-003. New fixed-parameter series may have
different capture characteristics, but structural risk remains. **Cost realism binding, early.**

## Anchor series (first-branch definitions)

All series: **cross-instrument spreads** on the anchor domain, price-derivable (invertible to
target price), `≤ t-1` data only.

### S5 (REDO) — Rolling-β cross-instrument basket spread
- `spread = log P^A − β·log(basket)`, basket = equal-weight log-basket of predeclared class-mates,
  β = rolling OLS on W_a anchor-bars. From scratch (no reuse of CF-MR-003 S5 code).
- Invertible: `P^A = basket^β · e^spread`. Params: β window W_a, basket membership (predeclared).

### S6 (NEW) — Fixed-ratio pair spread
- `S = log P^A − β·log P^B`, β **fixed** (not re-estimated).
- Invertible: `P^A = P_B^β · e^S`. Params: β (fixed), pair selection (predeclared).
- Source: `new-anchor-series-suggestions.md` design 1.

### S7 (NEW) — Fixed-weight basket deviation
- `S = log P^A − Σ wᵢ·log Pᵢ`, weights **fixed** (equal / liquidity / contract-size).
- Invertible: `P^A = (Π Pᵢ^wᵢ) · e^S`. Params: weights, basket membership (predeclared).
- Source: `new-anchor-series-suggestions.md` design 2.

### S8 (NEW) — Relative-value index (spread minus rolling median)
- `S = (log P^A − Σ wᵢ·log Pᵢ) − Median_W(·)`, equal-weight **basket** (F-fix EXP-014: was pair),
  **W=90** (F-fix: was 60) rolling median window. Headline "practical variation" of
  `new-anchor-series-suggestions.md`.
- Invertible: `P^A = (Π Pᵢ^wᵢ) · e^(S + C_t)` where C_t = rolling median.
- Params: basket membership + weights (equal), W=90 (predeclared). Source: design 3 practical variation.

## Execution model (operator-mandated)

| Axis | Decision | Status |
|---|---|---|
| Entry | **Precalc limit orders** at extreme, set-and-forget, refreshed per anchor bar, live intra-bar fill | ACTIVE |
| Lower-domain | **Removed** — no lower-domain bar event triggering | ACTIVE |
| Direction | Fade-toward-anchor (entry at extreme, exit at mean) | ACTIVE |
| Exit | Form-1 event-reversion (moving anchor) **+** form-2 **refreshing** favorable limit at anchor mean **+** horizon last-resort | ACTIVE (EXP-014; EXP-013 shipped form-2-frozen + horizon only — confound) |
| Reentry | none / allow / extend | EXP-014: none=primary, allow/extend=disclosure variants |
| Target | reversion-to-mean / opposite-extreme | mean ACTIVE; opposite DEFERRED |
| Trend/regime conditioner | fade only adverse-to-4h-trend; vol-regime slices | ACTIVE (EXP-014, disclosure slices — operator NEW) |
| Recalc→fill (refresh vs static) | R (refresh/bar) vs S (place-once) | ACTIVE (EXP-014, A/B) |

## MR screening framework (informative, not gating)

6-stage framework: 1. Robust detrending · 2. Lag-1 autocorrelation · 3. Variance Ratio ·
4. ADF · 5. KPSS · 6. AR(1)/OU half-life. **All INFORMATIVE** — reported, never disqualify.
Binding admission: (1) availability = reversion-to-anchor over dislocation-matched matched-random
(per-stratum CI excludes zero); (2) tradability = net P&L clears frozen referee per stratum.

## Hypotheses

### HYP-001 — Full-strategy availability + tradability (first EXP)
Does the complete precalc limit-order strategy (form-2 exit at mean, fade, no reentry, no
lower-domain) on the 4 cross-instrument anchor series produce (a) reversion-to-anchor beyond
dislocation-matched matched-random (availability) AND (b) net-positive under frozen referee
(tradability), per stratum, on TRAIN? **EXP-013** — **CONFOUNDED** (form-1 exit absent, form-2 TP frozen;
see amendment). Verdict downgraded from NOT-TRADABLE. 0 slots, 0 counted reads, holdout sealed.

### HYP-002 — Faithful full-exit strategy + conditioners (redo) — **NOT-TRADABLE (EXP-014, 2026-07-02)**
Does the **faithful** strategy — form-1 event-reversion exit **and** refreshing form-2 anchor-mean limit
(horizon last-resort), re-entry variants, trend + vol conditioners — produce availability + net edge per
stratum on TRAIN, and if not, **exactly which leg fails where**? **EXP-014 answer: NO — NOT-TRADABLE**
(price-primary, cTrader in-engine; audit PASS, 0 Critical). 152/152 cells (4 series × 4 arms). Both
proposal-named exits fire (form-1 281 / refreshing form-2 1898 / horizon 1266, primary none/R) → L-14
discharged; the frozen 4h referee rejects **all 38 strata net AND gross** (homogeneous, no masking).
Availability does not separate at 4h; the failing "leg" is not a leg but the **capture-vs-dispersion wash**
(per-trade −57…+29 bps, net ci_low<0). Power caveat: 19/38 cells bite-fail (referee underpowered on a
discrete bracket); credible null on the bite-passing subset. Independent 6-stage MR screen booked pre-verdict
(VR<1 on S7/S8 baskets; S6 pairs near random walk). 0 slots, 0 counted reads, holdout sealed, referee untuned.
**Disposition: RETIRE recommended (operator-gated).** `python/experiments/EXP-014/report.md`.

### HYP-003 — S8 streamlined rerun: symmetry availability, 2 domains, both-leg — **REJECT_LEAK (EXP-014b, audited 2026-07-03)**
On S8 (basket−median₉₀), 1h+4h, does the outlier revert **beyond a coin flip** (symmetry two-barrier,
null=0.5) and does any single-leg (moving-mean exit; reentry none/allow/extend) or both-leg config clear
the frozen referee — per (cell,domain,arm,z\*)? **EXP-014b answer: REJECT_LEAK, 0 TRADABLE / 220 strata**
(audit: 2 Critical found+fixed analysis-only — per-stratum labels C1, both-leg spread-weighting C2;
family outcome unchanged; p_inward re-derived exactly from raw). Mechanism: **1h availability raw-passes
all survive peer-feed phase-shift** (own-price auto-reversion; the S8 basket *dilutes* it — EURUSD live
0.508 vs shift 0.688) → S8-at-1h retired. Collapse-verified availability only **4h JP225 (p=0.696,
ci 0.638; replicated z1.5) + weakly 4h EURUSD** — not tradable (unpowered/fail). Moving-mean exit =
small-f2-wins/large-f1-anchor-drift-losses ≈ 0 gross. extend admits = own-price MR harvest (net halves
but persists under shift → leak). Both-leg = median-positive, mean-killed by ~50-bar loss tail + N+1
costs. Status census post-fix: NULL 152 / REJECT_LEAK 53 / UNPOWERED_TRADABILITY 14 / NOT_TRADABLE 1.
0 slots, 0 counted reads, holdout sealed, referee untuned. `python/experiments/EXP-014b/audit.md`.

### HYP-004 — Lean bracket rerun — **CREDIBLE_NEGATIVE_RETIRE (EXP-014c, 2026-07-03)**
**Answer: NO — and the family retires on it (audit PASS, 0 Critical; all numbers re-derived from
raw emissions).** Both prespecified primaries powered + bite-valid + net-fail; 0 Holm admits in
the binding family; 262-cell census NULL 218 / UNPOWERED 22 / NOT_TRADABLE 14 / NET_ADMIT 4 /
REJECT_LEAK 4. Mechanism = **entry-seam mismatch**: limit-touch fills are shallower,
adversely-selected versions of the measured close-breach events (JP225 TP-share 0.52 vs 0.696;
20/32 TP fills without spread reversion; EURUSD 0/20 stops with spread reversion). Attribution:
frozen TP recovers E0's moving-target loss engine, SL subtracts value, time-stop benign — exits
exonerated, entry object is the failure. Disclosure: extend-arm own-price ladder field (→
CF-MR-005); JP225 residual P&L Asia-session-structural; W3 collapse-fraction rule filed as KB
lesson-candidate. 0 slots, 0 counted reads, holdout sealed. Original hypothesis text below.

*(as opened, 2026-07-03)*
Does the exit-set that **matches the measured two-barrier object** — TP frozen at entry anchor, SL at
the symmetric outward barrier, time-stop ⌈3·HL⌉, decomposed E1/E2/E3 vs the faithful moving-mean E0
baseline (reused 014b emissions) — extract the collapse-verified 4h availability? 4h only, single-leg,
z\* {2.0,1.5} + reentry {none,allow,extend} retained as characterisation axes. **PRIMARY =
(none, z2.0, E3) on JP225 + EURUSD** (prespecified); cross-cell Holm per (arm,z\*) over 11 cells;
phase-shift tripwire + per-admitting-cell bite binding; session-hour artifact disclosure. See
`docs/experiments-docs/checkpoints/2026-07-01-004-cross-domain-mr-renewal/amendment-004-lean-bracket-redesign.md`.

## Exclusions / deferred

No counted TEST read / holdout release in HYP-001 (TRAIN-only). `/REENTRY`, `/TARGET`
opposite-extreme, `/EXIT` plane, `/DIRECTION` trend/regime — DEFERRED. S1–S4 (single-instrument)
— NOT in scope (cross-instrument only; single-instrument MR explored in CF-MR-001/002/003).

## Referee note (binding)

Frozen renewed referee (§10.3a q\*=0.75 + E6 P*-gate). CF-MR-004 **never** tunes it (L-12).
Referee already adaptive (DET-dominance, power-aware, studentized sub-pop floors).

## Discipline

Real-price outcomes (emitted real OHLC, never synthetic); holdout sealed (final-30% never read,
TRAIN-only fence); per-stratum binding verdicts (L-03); availability alongside tradability from
one emission; cost realism binding early (L-02); all computation `≤ t-1`, open-to-open,
engine-realized fills; from-scratch family-specific code (L-13); all outcomes retained.
