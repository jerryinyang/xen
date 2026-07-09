# Data Analysis: EXP-022 — CF-CSRR-001 HYP-002 Indices consensus-residual reversion

Execution-agnostic availability + A×B×C×D component-characterisation SCREEN on the 10-index equity
basket, 4h TRAIN-only. Indices mirror of EXP-021 (Currencies). No engine, no fills, no P&L, no
`xen.adjudication` estimand gate (nothing to reconcile — availability screen; precedent EXP-008/009/021).
All numbers computed by the data-analyst's own code (`analysis_code/screen.py`, `plots.py`) on raw 1m
emissions via canonical `xen.bar_aggregator` (1m→4h, `min_coverage=0.90`) + `xen.evaluation` (hardened
CI, L-20). Results: `results/`. Panel: 3,253 union 4h bars, span **2021-06-02 → 2023-12-18** (first 49%),
median **8** present members/bar, 97% of bars ≥4 present.

---

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (blocking_pass all cells) | **N/A** | Availability screen: no P&L/accounting object to reconcile (design §9; EXP-008/009/021 precedent). Binding integrity gates here are tripwire + holdout + causal ≤t-1. |
| Provenance trace (verdict-bearing cols ≤ t-1) | **PASS** | anchor/u/m/s/k/HL from confirmed RealClose ≤ t (`reset_anchor` uses prior reset-period's last close; `trailing_threshold`/`trailing_pct_active` windows strictly `< t`); forward **open-to-open** from next bar: entry `Open(t+1)`, exit `Open(t+1+h)` (`build_rows`). Golden trace bit-verifiable (§ below). |
| Leak tripwire collapsed + non-vacuous | **PASS** | Temporal block-permute (block=12 ≥ max h) of the (s→forward-idio) pairing collapses ρ→0: across the 38 real-positive N/P cells mean \|tripwire\| = **0.32 bps** vs mean signal **3.61 bps** (max \|tripwire\| 1.85). On the strongest disclosed lead (USTEC R_US/S hedged) 4.40→**0.16 bps** (collapse 0.037). Non-vacuous — the permute re-pairs the residual with an unrelated time's forward return, moving the conditional mean (not a mean-invariant P&L rotation; EXP-012/B-6 compliant). |
| Holdout untouched | **PASS** | Load capped at first `TRAIN_FRAC=0.49` of each file (`load_member`); panel ends 2023-12-18 (~49% of the 5-year window). Final-30% global holdout never opened. TEST band (49→70%) not emitted. |
| Price-primary (engine emission under fence) | **N/A** | No cTrader run — execution-agnostic screen (design §4/§9). Signal + forward return from real time-bar OHLC only. |
| No experiment-local accounting defs | **PASS (honored)** | Only `xen.evaluation` statistics used; no per-bar/leg/episode accounting defined anywhere in `analysis_code/`. No P&L object exists. |

**Golden trace** (`results/golden_trace.parquet`; first-3 single-worst post-warmup, N/P, median/raw/single/hedged):
US2000 at 2021-06-07T16:00 (7 present, h=2, entry Open 2314.07 → exit Open 2320.12, ρ=−0.00326), 2021-06-07T20:00
(entry 2320.30 → 2318.79), 2021-06-08T20:00 (5 present, entry 2343.03 → 2344.79). Entry/exit are next-bar opens
h apart, signal from closes ≤ t; hand-recomputable. First-3-post-warmup is the frozen rule (no hand-picking).

---

## 2. Question list

1. **Does the equity-basket consensus residual mean-revert (substrate)?** ANSWERED §3.1 — YES, unanimous VR<1.
2. **Does conditioning on a large residual predict positive idiosyncratic (hedged) reversion at the PRIMARY construction (N/P), beyond the max-stat permuted-axis null?** ANSWERED §4.1 — NO cell clears; best fw_p 0.33.
3. **Is any cell powered for the design's ≥1 bp SUPPORTED band?** ANSWERED §4.2 — NO. MDE 3.9–21.7 bps across all powered cells; the ≥1 bp band is below MDE everywhere (B-5 UNPOWERED).
4. **Do the twins (random-index extremeness, random-timing) separate?** ANSWERED §4.1/§4.3 — no consistent separation at primary; twins ≈ 0, collapse fractions noisy because signal ≈ 0 (L-15).
5. **Does any robustness construction (anchor S, build A, build R) produce a lead, and is it bookable?** ANSWERED §3.3/§4.3 — 8 sub-0.05 cells appear ONLY in non-primary constructions (build A/anchor S, build R_US/anchor S); none is sign-anchored to a primary lead, so per §3.1 they are **disclosed leads, not bookable** significance.
6. **Is the effect leak-driven?** ANSWERED §1 — no; tripwire collapses ρ→0 everywhere.
7. **Per-stratum heterogeneity (L-03)?** ANSWERED §4 — yes; single-worst selection concentrates events on JP225/US-large; EU50/HK50/US500 get ~0 primary events (UNPOWERED, not negatives).
8. **Falsification of each headline:** substrate MR — checked across 240 cells (90% VR<1); primary null — checked uncorrected AND max-stat; leads — checked hedged-vs-unhedged decomposition (drift split) + tripwire.

Mandatory-set items on P&L object / occupancy / cost / episode anatomy / Sharpe are **N/A** — there is no
traded object at this tier (per-event forward idio return is the correct availability object, design §2/L-16).

---

## 3. Substrate & construction

### 3.1 Substrate — the consensus residual mean-reverts (unanimous) — EVIDENCE FOR

Primary build N × anchor P, VR(2) < 1 on **40/40** instrument×A×B cells (per-instrument mean VR2
0.52–0.87), VR(6) ≈ 0.19–0.53, AR(1) half-life **~0.8–1.9 4h-bars** (~1 session). Across ALL 6
build×anchor constructions VR(2)<1 on **216/240 (90%)**. The predeclared **substrate kill precheck is NOT
triggered** (it required VR≥1 AND autocorr≥0 on all instruments across builds) — the residual is a genuine
mean-reverting level. HK50 HL is NaN (only 600 present bars → AR(1) fit unstable; UNPOWERED, N2).

*Band note (inherited from EXP-021 Finding 1):* the design's `autocorr1<0` sub-band was mis-specified for
a **level** residual — a mean-reverting level has `0<AR(1)<1` (here ≈0.5–0.7, HL=−ln2/ln(AR)); VR<1 is the
correct MR read and it is unanimous. Disclosed, not a data defect. (`plots/1_substrate.png`.)

### 3.2 Power reality — single-worst events concentrate far below the §8 projection

Design §8 projected ~1,000–1,600 fade events/instrument (MDE 0.3–0.9 bps). Actual **N/P single-worst**
event counts: JP225 395, USTEC 239, US2000 209, UK100 119, GER40 64, AUS200 53, US30 28, US500 1, EU50 0,
HK50 0. Two structural causes: (a) `argmax_i|s_i|` on a 10-member basket assigns one owner/bar, and max|s|
concentrates on a few high-vol / always-present indices; (b) session-limited indices (EU50 1,224 / HK50 600
present bars, from the 90%-coverage 4h filter) are rarely the extreme and rarely present. Consequence:
**every primary cell is UNPOWERED for the ≥1 bp band** — MDE 3.9–21.7 bps on the 74 cells with n≥100. The
design's ≥1 bp SUPPORTED threshold sits **below MDE everywhere**; it cannot be resolved on 4h TRAIN.

### 3.3 The robustness constructions (disclosure — NOT extra significance, §3.1)

| construction | min fw_p (max-stat) | reading |
|---|---|---|
| **N/P (PRIMARY)** | **0.33** (JP225) | no lead |
| N/S | 0.181 | no lead |
| A/P | 0.418 | no lead |
| **A/S** | **0.001** (US2000) | disclosed lead, drift-heavy (§4.3) |
| R_US/P | 0.146 | no lead |
| **R_US/S** | **0.008** (USTEC) | disclosed lead, hedged (§4.3) |
| R_EU/P | 0.076 | borderline, no lead |
| R_EU/S | 0.154 | no lead |
| R_ASIA/P, R_ASIA/S | 0.44, 0.48 | UNPOWERED (Asia n=3, N2) |

All 8 sub-0.05 cells live in **anchor S** + gated/bloc builds (US2000 A/S ×4, USTEC R_US/S ×4). None
coincides with a primary (N/P) lead — the primary is null on both. Per §3.1's net rule a lead is bookable
only if it (a) clears the PRIMARY max-stat, (b) is sign-stable across both anchors, (c) survives ≥2 of 3
builds. **These clear none of (a)–(c)** — they are exactly the "second bite in a secondary construction"
that the multiplicity discipline forbids booking. Recorded as disclosed leads for the operator.

---

## 4. Evidence FOR and AGAINST the hypothesis

### 4.1 AGAINST — the primary idiosyncratic reversion does not separate

- **0/74** powered-n (≥100 events) primary cells clear even the *uncorrected* `ci_low>0 & mean≥1 bp`.
- Under the mandated **max-stat multiplicity** over the 16 cells, **0/9** instruments reach fw_p<0.05
  (HK50/EU50 excluded — ~0 events); best is JP225 fw_p **0.33** (obs 5.5 bps), US2000 0.37, EU50 0.49.
- The headline V5-screen cell (median/raw/single/hedged, N/P) is mixed-sign and wide: JP225 +1.5 bps
  (CI [−8.2, …]), US2000 +2.1 (CI [−2.7, …]), USTEC −0.4, GER40 −8.9, AUS200 −3.6 — all CIs straddle 0,
  all n far below the 1 bp-band power requirement.
- Twins do not separate: random-index and random-timing twin means sit ≈0 at primary; collapse fractions
  are numerically unstable because the signal itself ≈0 (L-15 — the *level* ≈0 is the read, not the ratio).

### 4.2 UNPOWERED, not CONTRADICTED (B-5)

No primary cell is a powered negative either: with MDE 3.9–21.7 bps, the several small-negative point
estimates (GER40 −8.9, AUS200 −3.6, US30 −4.2) are within their own noise — none has CI_high<0 at the ≥1 bp
scale. The primary construction **cannot distinguish "no idiosyncratic reversion" from "reversion below a
few bps"** on this 2.5-year single-regime TRAIN. This is a resolution ceiling, not a refutation.

### 4.3 FOR (disclosed leads only — do NOT meet the bookable bar)

- **USTEC in the US regional bloc, session-open reset (R_US/S), hedged** — the cleanest disclosed lead:
  median/raw +4.40 bps (n=571), mean/raw +4.71 (n=582), fw_p **0.008–0.018**; **hedged** (consensus removed
  = mechanism-faithful), beats random-timing (rt_percentile 0.92–1.0), random-index twin ≈0.16 bps,
  **tripwire collapses** 4.40→0.16 (collapse 0.037). Mechanistically plausible: restricting consensus to
  the 4 tightly-cointegrated US indices and resetting at NY cash open isolates a real intraday US-bloc
  residual. BUT it is **anchor-S-and-bloc-specific** — primary USTEC N/P fw_p = 1.0 (ρ ≈ 0), so it is NOT
  sign-stable across anchors and does not survive in build N; **disclosed lead, not support**.
- **US2000, activity-gated, session-open reset (A/S)** — fw_p 0.001–0.037, but drift-contaminated: the
  significant cells are **unhedged** (mean/raw/allk +8.4 bps, unhedged) and the hedged (alpha) half is
  smaller (mean/raw/allk +3.8, ci_low +1.37, p_perm 0.0) — i.e. roughly half the A/S US2000 signal is
  consensus/market beta, mirroring EXP-021's AUDUSD survivor. Again primary N/P US2000 is null (fw_p 0.37).
  Disclosed lead, mostly drift.

Neither lead clears the primary; both are confined to the **session-open (S) anchor** and to
consensus-narrowing builds (US bloc / activity gate). The natural follow-up read is: does a US-bloc,
session-open-anchored hedged residual reversion hold up as a *registered primary* (new multiplicity row),
and does it survive on the P&L object at the tradability tier (EXP-023)?

---

## 5. Anomalies & open questions

- **Session-limited indices barely enter the screen.** EU50 (1,224 present) and HK50 (600) yield ~0
  single-worst primary events and NaN/unstable HL; build-A activity gate zeroes HK50 entirely (its
  90%-coverage 4h bars fall outside the {0,4}-UTC liquid window used). These are UNPOWERED by construction,
  never negatives — but it means the "10-index" basket is effectively an 8-index (US-heavy) basket at 4h.
  Open question: is a lower `min_coverage` or a coarser (1d) domain needed to bring EU/Asia indices into the
  consensus, or is 4h simply the wrong cadence for those sessions?
- **The disclosed US-bloc/session lead is the one signal worth chasing** — it is hedged, leak-clean, and
  beats both twins, but only under a non-primary construction. It is not evidence for the family thesis as
  posed (native single-factor, common anchor), but it is a concrete registered-branch candidate.
- **Design §8 power estimate was ~10× optimistic** for single-worst on a 10-member basket; a future primary
  should use `all>k` (more events) or a per-instrument-cap selection so power reaches the ≥1 bp band.

---

## 6. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: NOT SUPPORTED (availability) at the PRIMARY construction — with an UNPOWERED-band
  nuance and two disclosed non-bookable leads.**
- **Driven by:** (1) 0/74 powered primary cells clear even an uncorrected ci_low>0; best max-stat fw_p 0.33
  — the native single-factor, common-anchor idiosyncratic reversion the thesis requires does not separate.
  (2) Every primary cell is UNPOWERED for the design's own ≥1 bp band (MDE 3.9–21.7 bps ≫ 1 bp), so this is
  a genuine *NOT-SUPPORTED-at-the-resolvable-scale*, not a powered refutation (B-5). (3) The substrate DOES
  mean-revert (VR<1 unanimous) and two hedged/leak-clean leads exist — but only in non-primary
  (session-anchor + consensus-narrowed) constructions, which §3.1 forbids booking as significance.
- **Would change if:** a registered primary built on the US-regional-bloc + session-open (S) anchor + a
  higher-event selection (all>k or per-instrument-cap) powered the ≥1 bp band and reproduced the USTEC
  R_US/S hedged +4.4 bps as the PRE-registered primary with fw_p<0.05 and both-anchor sign stability. That
  is a NEW multiplicity row (new construction), not a re-read of this one.
- **Substrate kill precheck: NOT triggered** — the Indices arm is not dead at substrate.

**Final verdict is the operator's.** Suggested probes: (A) register a US-bloc / session-open / all>k primary
and re-run as a clean single-family max-stat (does the disclosed USTEC lead survive as a primary?); (B) run
the hedged-vs-unhedged (alpha-vs-drift) split + momentum-signed inverted twin on the US2000 A/S lead to
quantify how much is market beta before spending any tradability read; (C) decide whether EU/Asia indices
need a lower `min_coverage` or a coarser domain to enter the consensus at all.

---

## 7. USTEC lead probe (operator Phase-2, characterisation only — verdict NOT re-booked)

Probe of the disclosed USTEC lead (R_US bloc, anchor S, hedged; `analysis_code/ustec_probe.py`,
reuses `screen.py` construction; TRAIN-only, holdout untouched). Primary cell = mean/raw/single/hedged,
n=582, h=4 (2×HL, HL=1.90), mean ρ = **+4.71 bps**.

### Q1 — Robustness: coherent + sign-stable, but does NOT clear the hardened CI (L-20)

- **Axis-sweep coherence: STRONG.** 14/16 A×B×C×D cells positive; **all 8 hedged cells positive**
  (+0.3 to +4.7 bps), permutation p 0.002–0.009 on the raw/single hedged cells. Not one lucky cell.
- **Hardened block-bootstrap CI does NOT exclude zero.** ci = **[−0.58, +9.87] bps**; ci_low seed-range
  [−0.64, −0.50] (stable **negative**); block-sensitivity ci_low at block 3/5/10 = [−0.21, −0.58, −0.80]
  (sign stable, all <0). **MDE 5.28 bps ≈ the effect 4.71** → borderline-/under-powered (mirrors EXP-021
  AUDUSD: effect ≈ MDE). The **permutation max-stat (fw_p .008) and the hardened block-boot CI disagree**;
  under programme discipline (L-20) the reporting standard is "CI excludes zero" — **here it does not**.
- **Temporal halves: sign-stable, individually underpowered.** H1 +4.10 bps (CI [−3.1, +11.2], n=291),
  H2 +5.31 bps (CI [−2.3, +12.7], n=291) — same sign in both halves (not a single sub-period), but each
  half's CI straddles zero.
- **Horizon: monotone-increasing with h** — +1.41 (1×HL, h=2) / +4.71 (2×HL, h=4) / +6.20 bps (3×HL, h=6),
  every horizon's ci_low <0. A reversion *snap* would peak near 1×HL and fade; a monotone rise with horizon
  is more consistent with a slow accumulation than a sharp mean-reversion at the half-life.

**Plain read:** a *coherent, sign-stable* construction-wide effect (not a single-cell/single-period
artifact), but **not a resolved effect** — the hardened CI never clears zero and the effect sits at its
own MDE. Its significance rests solely on the permutation null.

### Q2 — Time-in-market

582 single-worst events, h=4, over **3,165 USTEC active(valid) bars in the R_US construction**:
- **event-rate 18.4%** of active bars (comparable to EXP-021 AUDUSD ~17–21%);
- **held-fraction n·h/active = 73.6%** — with h=4 and frequent entries, overlapping holds keep a position
  open ~74% of the time. As a single-position sequential leg this is closer to a **grid/high-occupancy**
  profile than a sparse deep-dislocation fader (the EXP-021 occupancy caveat applies).

### Q3 — Beta: the +4.71 bps is GENUINELY idiosyncratic, not bloc drift

Same-event alpha/beta split (fade of USTEC residual, forward open-to-open):
- rho **hedged (alpha) = +4.71 bps**; rho **unhedged (raw) = +0.30 bps**; **beta component = −4.41 bps**;
  USTEC forward **beta to bloc consensus = 1.185**.
- The raw signal is ≈0 **because** the +1.185 beta drags −4.41 bps against the fade, cancelling the
  idiosyncratic +4.71. So — unlike US2000 A/S (drift-heavy, raw ≫ hedged) — **removing the consensus
  ADDS the signal here**: the effect is genuine consensus-hedged idiosyncratic reversion, the correct
  mechanism. Fading USTEC's raw (unhedged) over-extension earns nothing; fading the *residual* earns it.

### Probe verdict (characterisation, non-booking)

The USTEC lead **survives as a real follow-up candidate, but underpowered**: it is coherent across the
axis sweep, sign-stable across both TRAIN halves, and — importantly — **genuinely idiosyncratic** (hedged
alpha +4.7 vs raw +0.3; beta 1.19), not the bloc drift the US2000 lead was. It does **not** dissolve.
But it **does not clear the hardened block-bootstrap CI** (ci_low −0.58, effect ≈ MDE 5.28), rides ~74%
of the time at h=4, and lives only in the non-primary (US-bloc + session-open) construction — so it is a
**registered-branch candidate for a powered, pre-registered primary + tradability read (EXP-023)**, not
present support for HYP-002. This does not change the §6 recommended verdict (NOT SUPPORTED at primary).

### Q4 — Is the lead USTEC-specific or a construction-wide US-bloc/anchor-S property?

Same construction (R_US bloc, anchor S, mean/raw/single/hedged, h=4) for all four bloc members
(`ustec_probe.py` generalised; fw_p = single-cell permutation p, not the 16-cell max-stat):

| member | n | rho bps | ci_low | ci_high | perm p | MDE | evt-rate% | held% | alpha | raw | beta-comp | β to bloc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **USTEC** | 582 | **+4.71** | −0.58 | +9.87 | **0.002** | 5.28 | 18.4 | 73.6 | **+4.71** | +0.30 | −4.41 | 1.19 |
| US500 | 5 | −5.72 | −11.69 | +0.25 | 0.583 | 5.97 | 0.2 | 0.7 | −5.72 | −23.4 | −17.7 | 1.18 |
| US2000 | 686 | +1.40 | −3.60 | +6.38 | 0.188 | 5.00 | 21.7 | 86.9 | +1.40 | +7.59 | +6.19 | 1.15 |
| US30 | 294 | −1.81 | −8.99 | +5.72 | 0.770 | 7.19 | 9.3 | 37.2 | −1.81 | +2.66 | +4.47 | 0.75 |

**Conclusion: the effect is USTEC-SPECIFIC, not a construction-wide artifact.** Only USTEC separates
(alpha +4.71, perm p .002); US30 is negative (−1.81), US2000 is ≈0 hedged and *drift-heavy* (alpha +1.40
≪ raw +7.59, perm p .19), US500 is UNPOWERED (n=5). Siblings do NOT reproduce the hedged alpha, so the
anchor-S/US-bloc choice does not manufacture the signal — it is idiosyncratic to USTEC. This *strengthens*
the USTEC lead as a genuine member-specific candidate (while the §7-Q1 power caveat stands: its own
hardened CI still does not exclude zero).

### Q5 — Why did the screen effectively only test US indices?

Per-member bar counts through the pipeline stages (first-49% TRAIN; single-worst = primary N/P
median/raw/single/hedged events):

| member | raw 4h bars (cov≈0) | after cov≥0.90 | present in ≥4-join panel | single-worst events | cov-filter drop |
|---|---|---|---|---|---|
| USTEC | 3957 | 3168 | 3162 | 239 | 20% |
| US500 | 3965 | 3050 | 3044 | 1 | 23% |
| US2000 | 3955 | 3163 | 3157 | 209 | 20% |
| US30 | 3958 | 3168 | 3162 | 28 | 20% |
| JP225 | 4051 | 2797 | 2791 | 395 | 31% |
| AUS200 | 3901 | 1982 | 1978 | 53 | 49% |
| **EU50** | 2800 | **1228** | 1225 | **0** | **56%** |
| GER40 | 3844 | 2891 | 2885 | 64 | 25% |
| **HK50** | 3124 | **621** | 619 | **0** | **80%** |
| UK100 | 3745 | 2967 | 2961 | 119 | 21% |

**Mechanistic reading — three separable causes, in order of impact:**

1. **The 90%-coverage 4h filter × short cash sessions is the dominant cull for EU50/HK50.** A 4h UTC
   window has 240 1-min slots; an index trading ~8.5h/day (Euro Stoxx ~08:00–16:30 CET) or ~6.5h with a
   lunch break (HK ~01:30–08:00 UTC) rarely fills ≥90% of any 4h grid box, so most windows are dropped:
   EU50 loses **56%** (2800→1228), HK50 **80%** (3124→621). US index CFDs (near-24h with only a short
   maintenance break) and the near-continuous JP225/UK100/GER40 lose only ~20–31%. This filter — not the
   join, not the anchor — is what thins EU50/HK50 to a fraction of the panel. **The ≥4-member join is
   negligible on top** (present ≈ post-coverage: EU50 1228→1225, HK50 621→619 — the panel almost always
   has ≥4 of the always-on US/UK/GER/JP members, so no member is dropped for lack of a valid consensus bar).

2. **`argmax|s|` single-worst selection then concentrates events on the highest-variance, always-present
   members.** Even where a member survives to the panel with thousands of bars (US500 3044, US30 3162,
   AUS200 1978), it is rarely the *cross-sectional extreme*: US500 gets **1** event, US30 **28**, AUS200
   **53** — the max|residual| is repeatedly won by USTEC/US2000/JP225 (higher idiosyncratic vol). So
   single-worst is a second concentrator on top of the coverage cull: it turns even present non-extreme
   members into ~0-event strata. (The `all>k` selection arm gives every present member events and is the
   right lens for the low-vol members — but it too is dominated by the US bars that survive coverage.)

3. **The UTC daily anchor (P) is NOT a material cause** — it is defined per-member on that member's own
   bars, so it does not drop bars; anchor S (session-open) changes *which* bars reset, not how many exist.

**Q6 — Is "NOT SUPPORTED" a fair read for the 10-index basket?**

**No — EXP-022 tested a US-index sub-basket, not the 10-index basket.** By powered single-worst events the
consensus and the fade are carried by USTEC/US2000/JP225/UK100/GER40; **EU50 and HK50 are UNPOWERED (0
events — no test), US500 (1) and US30 (28) are near-UNPOWERED, AUS200 (53) borderline.** The non-US-cash
members are **UNPOWERED (not CONTRADICTED)** — the screen never delivered a resolvable test for them at 4h,
so B-5 applies: their absence of a positive is *no evidence*, not evidence against. The NOT-SUPPORTED read
is fair **only for the US-cash cluster on the primary construction** (where it IS powered and does not
separate — 0/74 powered cells clear, best fw_p 0.33). For the Indices *arm* as a whole the honest label is
**coverage-limited / partially UNPOWERED**: a fair family read needs a rerun that admits EU/Asia — either a
lower `min_coverage` (e.g. 0.5, accepting causal-but-partial 4h windows) or a coarser **1D domain** (a full
cash session fits one daily bar, so EU50/HK50 stop being culled). Recommend the operator treat the Indices
arm as **NOT SUPPORTED (US-cash cluster, powered) + UNPOWERED (EU/Asia, coverage-limited)**, not a clean
10-index NOT SUPPORTED — and NOT auto-retire the arm on this run.

---

## 8. Addendum A1 — fair-basket coverage-corrected read (min_coverage 0.90 → 0.50)

Re-ran `screen.py` with the ONLY change being the 4h aggregation coverage knob (0.90→0.50); everything
else frozen (estimand ρ, 3 builds × 2 anchors, 16 cells, twins, permuted-axis max-stat, tripwire, hardened
block-boot CI, bands). Additive — primary parquets untouched; outputs suffixed `_cov050` / `_1d`. Panel
grows to 3,912 union 4h bars, median **9** present/bar (was 8). Integrity unchanged: TRAIN first-49%,
holdout never loaded, ≤t-1 causal, open-to-open; **tripwire collapses** (21 real-positive N/P cells: mean
\|trip\| 0.44 vs mean signal 6.78 bps, max 1.59). Substrate still MR (VR<1 on 215/240 = 90%).

### A1.1 — Power: EU/Asia partially admitted; single-worst reshuffles

| member | SW events @cov0.90 | @cov0.50 | @1D (cov0.50) | powered @0.5 (≥100)? |
|---|---|---|---|---|
| HK50 | 0 | **519** | 152 | **now POWERED** |
| JP225 | 395 | 269 | 20 | powered |
| USTEC | 239 | 201 | 47 | powered |
| US2000 | 209 | 162 | 33 | powered |
| AUS200 | 53 | 74 | 8 | still unpowered |
| UK100 | 119 | 61 | 7 | dropped below floor |
| GER40 | 64 | 39 | 7 | unpowered |
| US30 | 28 | 23 | 0 | unpowered |
| US500 | 1 | 1 | 0 | unpowered |
| **EU50** | 0 | **0** | 12 (allk 21) | **still UNPOWERED at 4h AND 1D** |

- **HK50 crosses into powered** (519 single-worst events) — thin/volatile HK 4h bars admitted at 0.5 are
  frequently the cross-sectional extreme, so HK50 now carries a real test. This is the main gain.
- **EU50 remains untestable at every setting** — 0 single-worst / 21 allk events at 4h@0.5, and only
  12 single-worst / 21 allk at 1D (660 daily bars). No coverage/domain choice on this 2.5-yr TRAIN powers
  EU50: it is both the thinnest survivor and rarely the extreme. Honest label stays **UNPOWERED (no test)**.
- Single-worst counts for the US-cash members *fall* slightly (more competitors for the argmax).

### A1.2 — Primary read on the fuller basket: STILL a null (US-cash NOT-SUPPORTED generalises)

Primary N/P: **0/76** powered cells clear the uncorrected `ci_low>0 & mean≥1 bp`. Under the max-stat over
16 cells, **only US2000** reaches fw_p<0.05 — cell **median/raw/single/UNHEDGED**, fw_p 0.049, ρ +11.5 bps,
**but**: (a) UNHEDGED = drift/beta, not the idiosyncratic mechanism; (b) hardened block-boot **ci_low −0.59
does NOT exclude zero**; (c) effect ≈ MDE (11.5 vs 12.1); (d) **not sign-stable across anchors** (same-family
hedged: N/P +5.1, N/S −2.7). Fails the bookable bar on all four counts → disclosed lead, weaker than USTEC.
- **The newly-powered HK50 is a clean null** — 0 cells fw_p<0.10 in any construction. So the US-cash
  NOT-SUPPORTED **generalises to HK50**: admitting the biggest previously-starved member does not surface a
  reversion edge. No hedged/idiosyncratic EU/Asia lead appears anywhere; the only EU/Asia fw_p<0.10 cell is
  GER40 N/S single/**unhedged** (n=87, UNPOWERED, drift, single anchor) — not a lead.

### A1.3 — USTEC lead SURVIVES the coverage change

R_US bloc, anchor S, single-worst, hedged, under cov0.50: mean/raw **+4.79 bps** (n=699, p_perm 0.002,
rt_percentile 1.0, tripwire −0.13) and median/raw +4.67 (n=685, p_perm 0.002) — essentially identical to the
cov0.90 values (+4.71 / +4.40). Same permutation significance, same clean tripwire, and the **same
underpowered caveat** (hardened ci_low −0.42, still does not exclude zero). The registered USTEC lead is
robust to the coverage knob — not a coverage-filter artifact.

### A1.4 — Recommended read (non-final; §6 verdict NOT re-booked)

The fair-basket, coverage-corrected read **does not change the picture**: (1) the substrate still
mean-reverts; (2) on the now-fuller, HK50-powered basket the primary is **still a clean null** — the US-cash
NOT-SUPPORTED **generalises** to the newly-testable EU/Asia member (HK50), with no hedged/idiosyncratic
EU/Asia lead surfacing; (3) EU50 alone remains structurally **UNPOWERED** at both 4h@0.5 and 1D (disclose as
untested, never as a negative, B-5); (4) the registered **USTEC lead survives** unchanged (+4.79 bps,
p_perm 0.002, tripwire-clean, still underpowered on the hardened CI). Recommendation to the operator: the
coverage correction **confirms** the split verdict rather than overturning it — book the Indices arm as
**NOT SUPPORTED (US-cash + now HK50, powered) + UNPOWERED (EU50 only, structurally untestable on this TRAIN)**,
keep USTEC as the sole registered lead, and treat any EU50 test as requiring a longer panel, not a further
coverage/domain tweak. No new significance family is claimed (1D is domain-robustness disclosure only; its
anchor-P daily reset degenerates toward a 1-bar-return residual and is a power probe, not a mechanism test).
