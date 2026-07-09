# EXP-022 — Design (CF-CSRR-001 HYP-002)

**Title:** Indices-basket cross-sectional consensus-residual reversion — availability +
A×B×C×D component characterisation (native single-factor equity basket, 4h, TRAIN-only,
execution-agnostic). **Mirror of EXP-021 (Currencies).**
**Family:** CF-CSRR-001 (checkpoint-009). **Tier:** exploratory. **Reads:** 0 (TRAIN-only).
**Status:** DESIGN → QA (fresh context). **Vehicle:** Python availability characterisation on 4h
TRAIN timebars — **no strategy, no fills, no P&L** (precedent EXP-008/009/021). Not an engine run;
the cTrader price-primary + `xen.adjudication` estimand gate binds at the *tradability* tier
(EXP-023), not here. See §9 for what gates this run.
**Gate cleared:** VAL-007 PASS (2026-07-06) — Indices basket 10/10 admitted, `holdout_rows_read=0`.

**Operator construction decisions (2026-07-06, this design turn):**
- **Run ALL THREE basket builds AND BOTH anchor resets** (operator, this turn) for maximal-robustness
  reporting. To keep the family-wise null honest, **ONE construction is the pre-registered PRIMARY**
  (the significance family / SUPPORTED band); the others are **cross-construction robustness** reads.
  A lead is credible only if it survives the primary max-stat AND is sign/band-stable across all
  builds × anchors — a *higher* bar, not extra bites at significance (§3.1 multiplicity accounting).
- **Native single-factor, NO sign-alignment needed.** Unlike the Currencies USD-strength problem, every
  index loads **positively** on one common factor (global equity risk), so σ_i = +1 for all members and a
  plain median / equal-weight consensus of log-moves is factor-coherent by construction. This is the whole
  point of the Indices mirror — it tests the family on its *natural* single-factor substrate.

---

## 1. Falsifiable question + mechanism

**Q.** On the 10-index equity basket at 4h TRAIN, is the cross-sectional consensus-*residual*
mean-reverting (VR<1 / lag-1 autocorr<0), and does conditioning on a large residual predict a positive
**residual-reversion** forward return over BOTH a matched random-index and a random-timing twin, beyond
a dislocation-matched permuted-axis null — and which (A×B×C×D) construction maximises that separation,
robustly across basket builds and anchor conventions?

```
MECHANISM: A single dominant common factor (global equity risk) drives most co-movement across the 10
index CFDs at 4h. When one index's session-accumulated move deviates from the basket consensus, that
idiosyncratic residual is dominated by transient local flow (one exchange's session open, thin
extended-hours liquidity, lagged propagation of a regional shock), NOT genuine index-specific
repricing, and therefore decays toward the consensus within a bounded horizon (~half-life of the
residual). The exploited regularity is the negative predictive relation between a member's current
cross-sectional residual s_i(t) and its forward IDIOSYNCRATIC (consensus-hedged) return. Event cadence
= per confirmed 4h bar (single-worst) or per member-over-threshold (multi). P&L-bearing object at the
tradability tier = a single-position episode (V5); HERE, execution-agnostic, the object is the
per-event forward idiosyncratic return over horizon h — the correct object for an availability screen
(§2, L-16).

DERIVED:
  estimand = signal-conditional residual-reversion return  rho_i(t,h) = -sign(s_i(t))*idio_i(t,h),
             idio_i(t,h) = g_i(t,h) - G(t,h)   (consensus-hedged forward, OPEN-to-OPEN: entry Open(t+1),
             exit Open(t+1+h); signal from confirmed closes <= t)                         [target-based, L-13]
  null     = within-bar cross-sectional identity permutation (dislocation-matched; preserves each
             member's marginal dislocation, destroys the i->i residual/forward-return linkage) + max-stat
             over cells for multiplicity                                                  [L-13, L-08]
  horizon  = h_i = clamp(round(2*HL_i), [1,12]) 4h bars; HL_i = AR(1) half-life of s_i   [half-life, not round #]
  test     = mean rho with hardened block-bootstrap CI (L-20) + permuted-axis p + twin deltas   [MR-native]
```

Not copy-pasteable onto another mechanism: the estimand is *consensus-hedged* forward reversion of a
*cross-sectional* residual; the null is a *cross-sectional identity* permutation; the horizon is the
*residual's own* half-life. All three are specific to a cross-sectional consensus-reversion mechanism.
Difference from EXP-021: native single-factor (no USD-strength alignment; σ_i=+1 all), 10 members,
session-disjoint members handled by the basket-build axis (§3).

---

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: PARTIAL-BY-DESIGN + justified. EXP-022 measures the PER-EVENT
    forward idiosyncratic return (availability), NOT the multi-leg episode P&L object (EXP-023/V5). This
    is the CORRECT object for an availability screen and for the substrate kill criterion ("residual not
    MR"). L-16 binds only when a characterisation null would RETIRE a multi-leg P&L family; EXP-022 cannot
    retire the family (checkpoint-level, operator-signed) and its kill criterion is substrate-level, which
    the per-event estimand covers exactly. Episode-object estimand deferred to EXP-023.
  measured conditioning event == traded entry event: YES. Screen conditions on confirmed |s_i(t)| >= k at
    bar close (data <= t-1), fade acted at next bar OPEN. Tradability vehicle V5 = ACTIVE confirmed-breach
    entry at next open — the SAME event. (V1-V4 passive-limit entry is a DIFFERENT event, characterised
    execution-agnostically only; not the EXP-023 vehicle, so no B-4 seam imported.)
  effect-splitting windows non-overlapping: forward horizons OVERLAP across events (rolling). Handled by
    block-bootstrap CI (circular block >= h, L-07/L-20) — never iid CIs on overlapping windows.
```

---

## 3. Construction (frozen for this run)

**Members (10):** USTEC, US500, US2000, US30, JP225, AUS200, EU50 (broker `STOXX50`), GER40 (`DE40`),
HK50, UK100. All σ_i = **+1** (rising index = risk-on = same common-factor sign). Latest-glob 5-year
files; `CloseTime` join on shared 4h grid; a bar enters a member's consensus only if that member is
present (and, in the activity arm, active). Minimum consensus membership per bar = **≥4 present members**
(else no valid consensus at t; disclosed count of dropped bars).

| Step | Definition |
|---|---|
| Session anchor (causal reset) | `anchor_i(t)` = 4h RealClose at most recent daily rollover ≤ t. **Anchor axis** (both run): (P) common **00:00-UTC** daily reset [PRIMARY, clean mirror]; (S) **per-index session-open** reset (Tokyo/Sydney/HK/London/NY cash open) [robustness]. **Extend to multi-day if HL multi-day.** |
| Accumulated move | `u_i(t) = ln(P_i(t) / anchor_i(t))` (σ_i=+1), accumulates from reset, P = 4h RealClose |
| Consensus (axis A) | `m(t) = A_est({u_i(t)})`, A ∈ {median, equal-wt mean} over present members |
| Residual | `s_i(t) = u_i(t) − m(t)`; axis B ∈ {raw, ÷σ_t}, σ_t = cross-sec MAD/std of {u_j(t)} |
| Selection (axis C) | single-worst `argmax_i|s_i|` · OR all `|s_i|>k` |
| Threshold (axis G) | `k` = trailing-median of per-bar `max_i|s_i|` (adaptive, 1 param; primary). Robustness: fixed 1.5·σ_t |
| Fade direction | `−sign(s_i(t))` (fade the idiosyncratic over-extension) |
| Forward return (**open-to-open**) | `g_i(t,h) = ln(Open_i(t+1+h) / Open_i(t+1))` — entry next bar OPEN, exit h bars later at OPEN. Signal `u/m/s/k/HL` use confirmed RealClose ≤ t; traded forward return uses RealOpen (L-01) |
| Consensus forward (hedge, axis D) | `G(t,h) = A_est({g_j(t,h)})`; D ∈ {hedged: idio = g_i−G, unhedged: idio = g_i} |
| **Estimand** | `rho_i(t,h) = −sign(s_i(t)) · idio_i(t,h)` — positive ⇒ residual reverts in fade direction |
| Horizon | `h_i = clamp(round(2·HL_i),[1,12])`; HL_i = AR(1) half-life of s_i. Robustness: fixed h=6 |

**Basket-build axis (all three run):**
- **(N) all-10 present-member join, NAIVE** [PRIMARY] — all present members in consensus; a closed member's
  CFD bar carries real overnight repricing (not a spurious zero), consistent with the native-factor premise.
- **(A) all-10 + per-bar ACTIVITY gate** [robustness] — a member is dropped from a bar's consensus when its
  4h bar is inactive (range < 10th-pct of its own trailing 4h true-range OR outside its liquid session);
  tests whether thin/closed bars distort the consensus.
- **(R) session-coherent REGIONAL BLOCS** [secondary arm, own internal max-stat] — US {USTEC,US500,US2000,US30},
  Europe {EU50,GER40,UK100}, Asia {JP225,AUS200,HK50}; consensus within bloc; report per bloc. Cleanest
  simultaneous factor; small baskets (Asia n=3) → power-limited, disclosed.

**Axis sweep (characterisation grid):** A(2)×B(2)×C(2)×D(2) = **16 construction cells**, read
**marginally per axis** (not 16 independent hypotheses), × instrument strata. G and horizon fixed at
primary; second value disclosed as robustness. Deferred registered branches (NOT run; new multiplicity
rows): A=weighted-implied, B=range-scaled, 1-bar/V4 residual-return-autocorr anchor, sliding fixed-L
(non-reset) anchor. Causality: anchor, m, s, k, HL all use data `≤ t−1`; decision at bar close; return from
next open (open-to-open).

### 3.1 Multiplicity accounting (binding — the honest cost of "all three + both anchors")

- **PRIMARY significance family = build (N) × anchor (P)**: max-stat permuted-axis null over the **16
  A×B×C×D cells** per instrument (family-wise), exactly as EXP-021. The SUPPORTED band and the headline
  read are evaluated HERE.
- **Robustness overlays** (build A, anchor S): the SAME 16-cell read recomputed; reported as **sign/band
  stability**, NOT as new significance claims. A primary lead that flips sign or crosses into WASH under any
  overlay is **downgraded to disclosure/lead**.
- **Secondary arm** (build R, regional blocs): its OWN internal max-stat over 16 cells per bloc; a positive
  is disclosed WITH the construction-level look count. **3 basket builds were examined** → any cross-build
  positive is credited only if it survives in ≥2 builds (cross-construction survival is the bar).
- **Net rule:** a lead is booked as a candidate only if it (a) clears the primary max-stat, (b) is
  sign-stable across both anchors, and (c) survives in ≥2 of the 3 builds. Anything less = disclosed lead.
  Total constructions computed = 3 builds × 2 anchors × 16 cells; significance is NOT claimed 96×.

---

## 4. Scope

| Item | Value |
|---|---|
| Instruments | 10 indices (above). Regional blocs {US:4, Europe:3, Asia:3} in build R |
| Domain | 4h only (aggregate from 1m via `xen.bar_aggregator`, `min_coverage=0.90` + analysis-boundary fence) |
| Data | latest-glob 5-year files (INFR-003/VAL-005/VAL-007); 6 new symbols reach 2021-06-02, 0 truncations |
| Split | **TRAIN = first 49%** (first 70% analysis → first 70% train). TEST band NOT emitted. Final-30% holdout NEVER loaded |
| Time alignment | join members on shared 4h `CloseTime`; member enters m(t) only if present (build A: present+active); ≥4 members required for a valid consensus bar |
| Complexity budget | 3 stat families (substrate VR/autocorr · reversion-Δ bootstrap CI · permuted-axis null); ≤6 plots (one extra for cross-build robustness); 1 analysis module `analysis_code/` |
| Engine | **N/A** — execution-agnostic availability; no fills/P&L; no `xen.adjudication` accounting (nothing to reconcile). Family card §Implementation path; precedent EXP-008/009/021 |
| Reads / slots | 0 counted TEST reads, 0 slots (TRAIN-only by construction) |

---

## 5. Controls (validity proofs)

```
CONTROL random-index-twin:
  question answered: does picking the MOST extreme residual (max|s|) beat a random basket member? (extremeness)
  population: same bars/timing; fade signal assigned to a UNIFORMLY RANDOM present member j≠argmax, ≥25 seeds.
             DISJOINT: a random member is typically near-consensus (small |s|), forward idio ≈0 — different
             population than the max-|s| tail.
  bite/MDE: seed battery gives a null band; signal minus twin-mean vs its MDE (§6). Co-designed, not a fixed plant.
  non-vacuity: moves the conditional mean (pairs the fade with a low-|s| member's forward idio, ≠ the extreme's).
  expected if H true: signal rho >> twin rho (Δ>0). If H false: Δ≈0 (extremeness irrelevant).
  disclosure: collapse fraction (twin rho / signal rho) per cell (L-15).

CONTROL random-timing-twin (BATTERY ≥25 seeds, L-19):
  question answered: does dislocation-CONDITIONING (fire on |s|>k) beat firing at random times? (timing)
  population: enter at random bars (matched count/instrument), same instrument, direction −sign(s_i) at that
             random bar. DISJOINT: random bars mostly non-extreme, |s| small.
  bite/MDE: per-stratum seed SD → MDE; binding read = signal PERCENTILE within the 25-seed distribution + battery
            mean vs MDE (L-19 rank read), never a diff vs one draw.
  non-vacuity: changes which s_i(t) values (and forward idio) enter the mean.
  L-13 caveat: random-timing reads spuriously NEGATIVE near consensus for an MR strategy; therefore SECONDARY —
            the PRIMARY significance null is the dislocation-matched permutation below.
  expected if H true: signal >> twin (Δ>0, high percentile). If H false: signal within seed band.
  disclosure: collapse fraction + percentile per cell.

CONTROL permuted-axis-null (PRIMARY significance null; dislocation-matched, L-13/L-08):
  question answered: does member i's residual predict i's OWN forward reversion beyond an equally-dislocated
             random pairing? (the cross-sectional linkage, holding dislocation fixed)
  population: within EACH bar, permute the map {residual s_i} ↔ {forward idio return owner} across present members
             (≥1000 perms). Preserves every member's marginal |s| and the contemporaneous market state
             (dislocation-MATCHED); destroys only the i→i linkage. DISJOINT: permuted pairing is a genuinely
             different assignment; symmetric consensus (median/mean) is label-invariant so m,s magnitudes untouched
             — only the linkage moves.
  bite/MDE: permutation distribution width per cell → effective MDE; multiplicity via MAX-STAT over the 16 cells
            (family-wise). Reads the "best cell by chance" honestly.
  non-vacuity: re-pairs s_i(t) with a different member's forward idio → moves the conditional mean statistic
            (NOT a mean-invariant permutation of one series; EXP-012/B-6 compliant).
  expected if H true: observed rho beyond the permutation upper tail (p_perm small) in ≥1 axis-coherent cell.
            If H false: rho inside the permutation band.
  disclosure: p_perm (max-stat adjusted) + observed-vs-null band per cell.
```

DRIFT-CARRY CHECK — deferred to EXP-023 (not run here). A momentum-contrast at THIS availability tier is
vacuous: ρ_mom = +sign(s_i)·idio_i ≡ −ρ_rev (exact algebraic negation), no independent attribution. The
genuine drift-carry test is the momentum-signed INVERTED twin on the P&L object at the validatory tier
(EXP-023, family-card mandate, USDCAD lesson). Booked as an EXP-023 requirement, not an EXP-022 control.

```
TRIPWIRE future-destroyer (MUST collapse):
  temporal block-permutation of the (s_i(t) → forward-return) pairing: block-shuffle forward returns across time
  (block ≥ h, L-07) so s_i(t) pairs with a forward return from an unrelated time. A causal reversion edge MUST
  collapse to rho≈0 (the conditioning loses its own future).
  expected collapse fraction ≈ 1.0 (rho → 0 within noise).
  vacuity check: block-permuting the temporal pairing moves the conditional mean E[idio | s_i] (NOT a rotation of
  the price path, L-07, NOT a mean-invariant permutation of realized P&L, EXP-012). A surviving rho ⇒ leak ⇒ REJECT.
```

---

## 6. Test selection (candidate-aware)

| Purpose | Method | Why matched to mechanism |
|---|---|---|
| Substrate (is s_i MR?) | Variance-ratio of s_i (lags 2/4/6) + lag-1 autocorr, per instrument × A × build × anchor | MR-native; VR<1 & autocorr<0 = reversion |
| Half-life | AR(1) on s_i → HL_i | sets horizon from mechanism scale, not a round number (L-13) |
| Effect (rho) | mean rho + `xen.evaluation.block_bootstrap_ci` (circular block ≥h, ≥10k×5-seed battery; `block_sensitivity` ½/1/2×; `trimmed_mean` disclosure) | hardened CI, overlap-correct, no zero-width on sparse cells (L-20) |
| Significance | permuted-axis max-stat p_perm (§5) at PRIMARY build×anchor | dislocation-matched, multiplicity-adjusted (L-08/L-13) |
| Twin separation | signal−twin Δ + percentile (random-index, random-timing battery) | extremeness vs timing decomposition (L-19 rank read) |
| Robustness | sign/band stability of the primary read across builds (N/A/R) × anchors (P/S) | operator-mandated cross-construction robustness (§3.1) |

Non-parametric/bootstrap throughout; no parametric gate; no fixed referee stack (frozen referee RETIRED from
service). Report "CI excludes zero", never a p-value from the bootstrap (L-20).

---

## 7. Interpretation bands (per stratum — no binaries)

```
BANDS (per instrument × cell, on rho, bps of idiosyncratic forward return; evaluated at PRIMARY build×anchor):
  SUPPORTED:    mean rho ≥ +1 bp AND block-boot CI_low > 0 AND p_perm < 0.05 (max-stat) AND beats BOTH twins (Δ>0)
                AND sign-stable across both anchors AND survives in ≥2 of 3 builds (§3.1)
  WASH:         |mean rho| < max(1 bp, seed-SD) — report as reverts≈random, NOT a refutation (L-11)
  CONTRADICTED: mean rho ≤ −1 bp with CI_high < 0 (residual CONTINUES / momentum)
  UNPOWERED:    n_events < 100 OR MDE > 1 bp OR permutation band wider than the effect — excluded from negatives (B-5)
SUBSTRATE (kill precheck): VR≥1 AND autocorr≥0 across BOTH A-estimators on ALL instruments AND across builds ⇒
  residual not MR ⇒ Indices arm dies (0 slots) — reported to operator; family disposition is checkpoint-only.
POOLED: any cross-instrument/cross-cell aggregate is DISCLOSURE-ONLY unless homogeneity is shown (L-03).
Collapse fraction disclosed for EVERY control and the tripwire (L-15).
```

Bands are informative reads for the operator; no auto-verdict, no auto-RETIRE (integrity/informative split §9).

---

## 8. Power statement

```
POWER: 4h TRAIN ≈ 0.49 × ~5y ≈ 2.4y × ~6 bars/day × ~260 d/y ≈ 3,600 bars/instrument (nominal).
  CAVEAT vs EXP-021: indices have session gaps + the ≥4-member consensus-validity filter → ACTIVE candidate
    bars < 3,600; expect ~2,000–3,200/instrument on build N, fewer on build A (activity gate) and build R
    (bloc-restricted, esp. Asia).
  single-worst: events with |s|>k(trailing-median) ≈ top ~50% of active bars → ~1,000–1,600 fade events/inst (powered).
  all|s|>k: multi-member, higher counts; per-member few hundred+.
  MDE at n≈1,200, block-boot 4h: ≈ 0.3–0.9 bp/event — effects ≥1 bp detectable on build N single-worst.
  Predeclared UNPOWERED risk: Asia bloc (n=3 members) in build R; ÷σ_t (B=z) cells; fixed-h=6 robustness; any
    activity-gated cell that thins < 100 events. Any cell with n<100 or MDE>1 bp is UNPOWERED, never a negative (B-5).
```

---

## 9. Integrity vs informative split

```
HARD (block this run):
  - TRIPWIRE collapse: rho must → 0 under temporal block-permutation of the pairing. Surviving edge ⇒ REJECT (leak).
  - HOLDOUT: TRAIN-only (first 49%); TEST band not emitted; final-30% never loaded. Any touch ⇒ REJECT.
  - CAUSAL PROVENANCE: every verdict-bearing column (u, m, s, k, HL, selection) uses data ≤ t−1; return from next open.
    Trace asserted in analysis_code (≤t-1 lag), diffed by QA. (Estimand-reconciliation gate N/A — no P&L/accounting.)
INFORMATIVE (operator judges worth): all rho magnitudes, CIs, p_perm, twin Δ / percentiles, collapse fractions,
  substrate VR/autocorr, cross-build stability. No materiality thresholds, no readiness floors, no gate
  conjunctions, no auto-RETIRE.
```

---

## 10. Golden trace (QA diffs before sign-off)

Deterministic, hand-computable from the frozen PRIMARY construction (build N, anchor P/00:00-UTC, A=median,
B=raw, C=single-worst, D=hedged, k=trailing-median, h=HL). Analyst emits `results/golden_trace.parquet`; QA
recomputes by hand:

**Disclosures (QA N1/N2, not tuned knobs):**
- **N1 — HL and k are data-fitted, emitted inputs, not hand-set parameters.** `h_i` is taken from index i's
  own AR(1)-fitted residual half-life and `k` from the trailing median of `max_i|s_i|` — both computed from
  the emitted series under ≤t−1 causality, not chosen. They are frozen construction outputs, not levers.
- **N2 — build-R Asia bloc (JP225/AUS200/HK50, n=3) is coarse-null / power-limited.** A 3-member basket
  gives few distinct within-bar permutations → wide permutation null. Predeclared UNPOWERED (§8/§7); a weak
  Asia read is never a negative (B-5).

```
GOLDEN-TRACE: the FIRST 3 single-worst fade events after warmup (first full-session + HL/threshold-window bars)
  in TRAIN, on build N × anchor P. For each:
  timestamp t (4h CloseTime); the present-member u_i(t) (σ_i=+1); m(t)=median; every s_i(t)=u_i−m; the selected
  argmax_i|s_i| and fade side −sign(s_i); h_i from HL; g_i = ln(Open_i(t+1+h)/Open_i(t+1)), G(t,h), idio, and
  rho_i(t,h). QA hand-verifies:
    (a) member set present at t (≥4); m = median of present u (label-invariant);
    (b) s_i, k, HL from confirmed RealClose ≤ t; anchor = last 00:00-UTC close ≤ t;
    (c) selected instrument = true argmax|s|; direction = −sign(s);
    (d) all signal inputs use bars ≤ t−1; forward return uses RealOpen: entry Open(t+1), exit Open(t+1+h) —
        open-to-open, no close leakage;
    (e) rho recomputed matches the emission bit-for-bit.
  The developer/analyst must NOT hand-pick these events — first-3-post-warmup is the frozen rule.
```

---

## 11. Deliverables

- `analysis_code/` — one module: construction (u/m/s/k/HL over 3 builds × 2 anchors), estimand rho, controls
  (3 twins + tripwire), substrate VR/autocorr, bootstrap CI (`xen.evaluation`), permuted-axis null. Canonical
  `xen` helpers only; no local accounting (`check_no_local_accounting` N/A but honored — no P&L).
- `results/` — per-(instrument×cell×build×anchor) rho + CI + p_perm + twin Δ/percentile + collapse fractions;
  substrate table; HL table; cross-build stability table; `golden_trace.parquet`.
- `plots/` — ≤6: substrate VR/autocorr heatmap; rho-by-axis (marginal per A/B/C/D); signal-vs-twins with CI;
  permutation null bands; collapse-fraction disclosure; cross-build/anchor stability.
- `analysis.md` (data-analyst, later) — evidence for+against + recommended (non-final) verdict; operator decides.

**Next pipeline stage:** QA-compliance (FRESH context — subagent or new operator session) → operator execution
gate → data-analyst → operator verdict. This is an availability screen: no engine run, no estimand-validation
gate; the integrity gates are §9 (tripwire collapse, holdout fence, causal ≤t-1 provenance).

---

## 12. Amendment A1 — coverage-corrected fair-basket addendum (operator 2026-07-06, post-primary-verdict)

**Why.** The primary run's `min_coverage=0.90` at 4h × short cash sessions thinned EU50 (0 events),
HK50 (0), US500 (1), AUS200 (53) to UNPOWERED — EXP-022 primary effectively tested a **US-cash
sub-basket**, not the 10-index basket (analysis.md §7-Q5/Q6). EU/Asia members are **UNPOWERED, not
CONTRADICTED** (B-5). The primary verdict (NOT SUPPORTED, US-cash powered) stands and is **not**
invalidated; this addendum *extends* coverage to the untested members — additive, not a confound rerun.

**Scope (same design, one aggregation knob relaxed; same estimand/null/twins/tripwire/bands):**
- **Primary addendum:** re-aggregate at 4h with **`min_coverage≈0.5`** (keeps 4h domain-comparability
  to the primary + Currencies EXP-021) so part-day EU/Asia indices admit enough valid 4h bars.
- **Cross-check:** if HK50/EU50 still < 100 single-worst events at 4h@0.5, add a **1D-domain** read
  (one full cash session = one daily bar — the natural fix for part-day indices); disclose as a domain
  robustness, not a new significance family.
- Everything else frozen: build N/A/R × anchor P/S, 16 A×B×C×D cells, max-stat FWER at primary
  (N×P), USTEC lead re-checked under the new coverage, per-stratum bands, ≤t-1 causality, TRAIN-only,
  holdout sealed. Multiplicity: this is a coverage-corrected read of the SAME HYP-002, not a new axis.
- **Read as:** does the full 10-index basket (EU/Asia now powered) support cross-sectional
  consensus-residual reversion, and does the US-cash NOT-SUPPORTED read generalise or not.
