# EXP-021 — Design (CF-CSRR-001 HYP-001)

**Title:** Currencies-basket cross-sectional consensus-residual reversion — availability +
A×B×C×D component characterisation (USD-strength consensus, 4h, TRAIN-only, execution-agnostic).
**Family:** CF-CSRR-001 (checkpoint-009). **Tier:** exploratory. **Reads:** 0 (TRAIN-only).
**Status:** DESIGN → QA (fresh context). **Vehicle:** Python availability characterisation on 4h
TRAIN timebars — **no strategy, no fills, no P&L** (precedent EXP-008/009). Not an engine run; the
cTrader price-primary + `xen.adjudication` estimand gate binds at the *tradability* tier (EXP-023),
not here (family card §Implementation path). See §Integrity for what gates this run.

**Operator construction decisions (2026-07-06, this design turn):**
- **Consensus = 7 USD pairs signed to USD strength; 3 JPY crosses EXCLUDED** (USD-neutral; a
  scalar-USD consensus cannot define their residual). Crosses = disclosure-only. **This is an
  APPROVED DEVIATION from family card §Currencies consensus** ("decompose JPY crosses to USD legs
  where possible"): operator chose "7 USD pairs, drop crosses" over the all-10 currency-vector build
  in this design turn's elicitation (2026-07-06). The currency-strength-vector build that would
  service the crosses is a deferred registered branch (§3).
- **Deviation window = session/daily rollover anchor with CAUSAL RESET** (canonical G0, operator fix
  2026-07-06): `anchor_i` = the 4h RealClose at the most recent daily/session rollover ≤ t; residual
  **accumulates intraday from the reset**, reversion = the accumulated gap closing (matches V1/V2/V5;
  the terse "prior-4h-close" 1-bar line is corrected). **Accumulation window keyed to the measured
  residual half-life** — disclose the HL fit and **extend the anchor to multi-day/weekly if HL runs
  multi-day**. The 1-bar / V4 residual-return-autocorrelation build is a distinct mechanism (deferred
  registered branch), NOT this baseline.

---

## 1. Falsifiable question + mechanism

**Q.** On the 7 USD-pair Currencies basket at 4h TRAIN, is the USD-strength consensus-*residual*
mean-reverting (VR<1 / lag-1 autocorr<0), and does conditioning on a large residual predict a
positive **residual-reversion** forward return over BOTH a matched random-index and a
random-timing twin, beyond a dislocation-matched permuted-axis null — and which (A×B×C×D)
construction maximises that separation?

```
MECHANISM: A single dominant common factor (USD strength) drives most co-movement across the 7
USD pairs at 4h. When one pair's session-accumulated USD-signed move deviates from the basket
consensus, that idiosyncratic residual is dominated by transient local flow (session opens,
one leg's thin liquidity, lagged info propagation), NOT genuine currency-specific repricing, and
therefore decays toward the consensus within a bounded horizon (~half-life of the residual). The
exploited regularity is the negative predictive relation between a member's current cross-sectional
residual s_i(t) and its forward IDIOSYNCRATIC (consensus-hedged) return. Event cadence = per
confirmed 4h bar (single-worst) or per member-over-threshold (multi). P&L-bearing object at the
tradability tier = a single-position episode (V5); HERE, execution-agnostic, the object is the
per-event forward idiosyncratic return over horizon h — the correct object for an availability
screen (§2, L-16).

DERIVED:
  estimand = signal-conditional residual-reversion return  rho_i(t,h) = -sign(s_i(t))*idio_i(t,h),
             idio_i(t,h) = g_i(t,h) - G(t,h)   (consensus-hedged forward, USD-signed, OPEN-to-OPEN:
             entry Open(t+1), exit Open(t+1+h); signal from confirmed closes <= t)         [target-based, L-13]
  null     = within-bar cross-sectional identity permutation (dislocation-matched; preserves each
             member's marginal dislocation, destroys the i->i residual/forward-return linkage) + max-stat
             over cells for multiplicity                                                  [L-13, L-08]
  horizon  = h_i = clamp(round(2*HL_i), [1,12]) 4h bars; HL_i = AR(1) half-life of s_i   [half-life, not round #]
  test     = mean rho with hardened block-bootstrap CI (L-20) + permuted-axis p + twin deltas   [MR-native]
```

Not copy-pasteable onto another mechanism: the estimand is *consensus-hedged* forward reversion of
a *cross-sectional* residual; the null is a *cross-sectional identity* permutation; the horizon is
the *residual's own* half-life. All three are specific to a cross-sectional consensus-reversion
mechanism (contrast CF-MR own-price: no basket, no consensus hedge, no cross-sectional permutation).

---

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: PARTIAL-BY-DESIGN + justified. EXP-021 measures the
    PER-EVENT forward idiosyncratic return (availability), NOT the multi-leg episode P&L object
    (that is EXP-023/V5). This is the CORRECT object for an availability screen and for the
    predeclared kill criterion ("residual not MR") — a per-event/substrate property. L-16 binds
    only when a characterisation null would RETIRE a multi-leg P&L family; EXP-021 cannot retire
    the family (checkpoint-level, operator-signed) and its kill criterion is substrate-level, which
    the per-event estimand covers exactly. The episode-object estimand is deferred to EXP-023.
  measured conditioning event == traded entry event: YES. Screen conditions on confirmed
    |s_i(t)| >= k at bar close (data <= t-1), fade acted at next bar OPEN. The tradability vehicle
    is V5 = ACTIVE confirmed-breach entry at next open — the SAME event. (V1-V4 passive-limit entry
    is a DIFFERENT event and is characterised execution-agnostically only; it is NOT the EXP-023
    vehicle, so no B-4 seam is imported.)
  effect-splitting windows non-overlapping: forward horizons OVERLAP across events (rolling). Handled
    by block-bootstrap CI (circular block >= h, L-07/L-20) — never iid CIs on overlapping windows.
```

---

## 3. Construction (frozen for this run)

**Members (7):** EURUSD, GBPUSD, AUDUSD, NZDUSD (USD-quote, sign σ_i = −1) · USDJPY, USDCHF, USDCAD
(USD-base, σ_i = +1). JPY crosses EURJPY/GBPJPY/AUDJPY excluded (disclosure-only naive-median contrast).

| Step | Definition |
|---|---|
| Session anchor (causal reset) | `anchor_i(t)` = 4h RealClose at most recent daily rollover ≤ t (primary: 00:00-UTC day boundary; session-level Asia/London/NY = robustness). Resets each day; **extend to multi-day/weekly if HL multi-day** |
| USD-signed accumulated move | `u_i(t) = σ_i · ln(P_i(t) / anchor_i(t))`, accumulates from the reset, P = 4h RealClose |
| Consensus (axis A) | `m(t) = A_est({u_i(t)})`, A ∈ {median, equal-wt mean} over the 7 present members |
| Residual | `s_i(t) = u_i(t) − m(t)`; axis B ∈ {raw, ÷σ_t} where σ_t = cross-sec MAD/std of {u_j(t)} |
| Selection (axis C) | single-worst `argmax_i|s_i|` · OR all `|s_i|>k` |
| Threshold (axis G) | `k` = trailing-median of per-bar `max_i|s_i|` (adaptive, 1 param; primary). Robustness: fixed 1.5·σ_t |
| Fade direction | `−sign(s_i(t))` (fade the idiosyncratic over-extension) |
| Forward USD-signed return (**open-to-open**) | `g_i(t,h) = σ_i · ln(Open_i(t+1+h) / Open_i(t+1))` — entry at next bar OPEN, exit `h` bars later at OPEN. Signal `u/m/s/k/HL` use confirmed RealClose ≤ t; the TRADED forward return uses RealOpen (open-to-open discipline, L-01) |
| Consensus forward (hedge, axis D) | `G(t,h) = A_est({g_j(t,h)})`; D ∈ {hedged: idio = g_i−G, unhedged: idio = g_i} |
| **Estimand** | `rho_i(t,h) = −sign(s_i(t)) · idio_i(t,h)` — positive ⇒ residual reverts in fade direction |
| Horizon | `h_i = clamp(round(2·HL_i),[1,12])`; HL_i = AR(1) half-life of s_i (single-worst series). Robustness: fixed h=6 |

**Axis sweep (characterisation grid):** A(2)×B(2)×C(2)×D(2) = **16 construction cells**, read
**marginally per axis** (not 16 independent hypotheses), × 7 instrument strata. G and horizon fixed
at primary; second value disclosed as robustness only. Deferred registered branches (NOT in this
run; would be new multiplicity rows): A=weighted-implied (needs pre-registered weights), B=range-scaled,
**1-bar/V4 residual-return-autocorrelation anchor**, sliding fixed-L (non-reset) anchor,
currency-strength-vector consensus. Causality: all of anchor, m, s, k, HL use data `≤ t−1`; decision at
bar close, return measured from **next open** forward (open-to-open).

---

## 4. Scope

| Item | Value |
|---|---|
| Instruments | 7 USD pairs (above). JPY crosses disclosure-only |
| Domain | 4h only (aggregate from 1m via `xen.bar_aggregator`, `min_coverage=0.90` + analysis-boundary fence) |
| Data | latest-glob 5-year files `timebars_<sym>_20210602_*_2026*_*.parquet` (INFR-003/VAL-005) |
| Split | **TRAIN = first 49%** (first 70% analysis → first 70% train). TEST band NOT emitted. Final-30% holdout NEVER loaded |
| Time alignment | join members on shared 4h `CloseTime`; a bar enters only if all present-members quote it (else that member absent from m(t)) |
| Complexity budget | 3 stat families (substrate VR/autocorr · reversion-Δ bootstrap CI · permuted-axis null); ≤5 plots; 1 analysis module `analysis_code/` |
| Engine | **N/A** — execution-agnostic availability; no fills/P&L; no `xen.adjudication` accounting (nothing to reconcile). Justified: family card §Implementation path; precedent EXP-008/009 |
| Reads / slots | 0 counted TEST reads, 0 slots (TRAIN-only by construction) |

---

## 5. Controls (validity proofs)

```
CONTROL random-index-twin:
  question answered: does picking the MOST extreme residual (max|s|) beat a random basket member? (extremeness)
  population: same bars/timing; the fade signal assigned to a UNIFORMLY RANDOM present member j≠argmax,
             ≥25 seeds. DISJOINT from signal: a random member is typically near-consensus (small |s|), so its
             forward idio return is ≈0 — a different population than the max-|s| tail.
  bite/MDE: seed battery gives a null band; signal minus twin-mean vs its MDE (§6). Co-designed, not a fixed plant.
  non-vacuity: moves the conditional mean (pairs the fade with a low-|s| member's forward idio, ≠ the extreme's).
  expected if H true: signal rho >> twin rho (Δ>0). If H false: Δ≈0 (extremeness irrelevant).
  disclosure: collapse fraction (twin rho / signal rho) reported per cell (L-15).

CONTROL random-timing-twin (BATTERY ≥25 seeds, L-19):
  question answered: does dislocation-CONDITIONING (fire on |s|>k) beat firing at random times? (timing)
  population: enter at random bars (matched count/instrument), same instrument, direction −sign(s_i) at that
             random bar. DISJOINT: random bars are mostly non-extreme, |s| small.
  bite/MDE: per-stratum seed SD → MDE; binding read = signal PERCENTILE within the 25-seed distribution + battery
            mean vs MDE (L-19 rank read), never a diff vs one draw.
  non-vacuity: changes which s_i(t) values (and their forward idio) enter the mean.
  L-13 caveat: random-timing reads spuriously NEGATIVE near consensus for an MR strategy; therefore it is a
            SECONDARY twin — the PRIMARY significance null is the dislocation-matched permutation below.
  expected if H true: signal >> twin (Δ>0, high percentile). If H false: signal within seed band.
  disclosure: collapse fraction + percentile per cell.

CONTROL permuted-axis-null (PRIMARY significance null; dislocation-matched, L-13/L-08):
  question answered: does member i's residual predict i's OWN forward reversion beyond an equally-dislocated
             random pairing? (the cross-sectional linkage, holding dislocation fixed)
  population: within EACH bar, permute the map {residual s_i} ↔ {forward idio return owner} across the present
             members (≥1000 perms). Preserves every member's marginal |s| and the contemporaneous market state
             (dislocation-MATCHED); destroys only the i→i linkage. DISJOINT: the permuted pairing is a genuinely
             different assignment; symmetric consensus (median/mean) is label-invariant so m,s magnitudes are
             untouched — only the linkage moves.
  bite/MDE: permutation distribution width per cell → the effective MDE; multiplicity via MAX-STAT over the 16
            cells (family-wise). Reads the "best cell by chance" honestly.
  non-vacuity: re-pairs s_i(t) with a different member's forward idio → moves the conditional mean statistic
            (NOT a mean-invariant permutation of one series; EXP-012/B-6 compliant).
  expected if H true: observed rho beyond the permutation upper tail (p_perm small) in ≥1 axis-coherent cell.
            If H false: rho inside the permutation band.
  disclosure: p_perm (max-stat adjusted) + observed-vs-null band per cell.

DRIFT-CARRY CHECK — deferred to EXP-023 (not run here). A momentum-contrast at THIS availability tier is
  vacuous: ρ_mom = +sign(s_i)·idio_i ≡ −ρ_rev (exact algebraic negation), so it carries no independent
  attribution. The genuine drift-carry test is the momentum-signed INVERTED twin on the P&L object at the
  validatory tier (EXP-023, family-card mandate, USDCAD lesson) — where direction and exposure differ from a
  sign flip. Booked as an EXP-023 requirement, not an EXP-021 control.
```

```
TRIPWIRE future-destroyer (MUST collapse):
  temporal block-permutation of the (s_i(t) → forward-return) pairing: block-shuffle forward returns across
  time (block ≥ h, L-07) so s_i(t) pairs with a forward return from an unrelated time. A causal reversion edge
  MUST collapse to rho≈0 (the conditioning loses its own future).
  expected collapse fraction ≈ 1.0 (rho → 0 within noise).
  vacuity check: block-permuting the temporal pairing moves the conditional mean E[idio | s_i] (it is NOT a
  rotation of the price path, L-07, and NOT a mean-invariant permutation of realized P&L, EXP-012). A surviving
  rho under this destroy ⇒ leak ⇒ REJECT.
```

---

## 6. Test selection (candidate-aware)

| Purpose | Method | Why matched to mechanism |
|---|---|---|
| Substrate (is s_i MR?) | Variance-ratio of s_i (lags 2/4/6) + lag-1 autocorr, per instrument × A | MR-native; VR<1 & autocorr<0 = reversion (methods-catalog MR row) |
| Half-life | AR(1) on s_i → HL_i | sets the horizon from the mechanism scale, not a round number (L-13) |
| Effect (rho) | mean rho + `xen.evaluation.block_bootstrap_ci` (circular block ≥h, ≥10k×5-seed battery; `block_sensitivity` ½/1/2×; `trimmed_mean` disclosure) | hardened CI, overlap-correct, no zero-width on sparse cells (L-20) |
| Significance | permuted-axis max-stat p_perm (§5) | dislocation-matched, multiplicity-adjusted (L-08/L-13) |
| Twin separation | signal−twin Δ + percentile (random-index, random-timing battery) | extremeness vs timing decomposition (L-19 rank read) |

Non-parametric/bootstrap throughout; no parametric gate; no fixed referee stack (the frozen referee is
RETIRED from service — `_pipeline-config`). Report "CI excludes zero", never a p-value from the bootstrap (L-20).

---

## 7. Interpretation bands (per stratum — no binaries)

```
BANDS (per instrument × cell, on rho, bps of idiosyncratic forward return):
  SUPPORTED:    mean rho ≥ +1 bp AND block-boot CI_low > 0 AND p_perm < 0.05 (max-stat) AND beats BOTH twins (Δ>0)
  WASH:         |mean rho| < max(1 bp, seed-SD) — report as reverts≈random, NOT a refutation (L-11)
  CONTRADICTED: mean rho ≤ −1 bp with CI_high < 0 (residual CONTINUES / momentum) 
  UNPOWERED:    n_events < 100 OR MDE > 1 bp OR permutation band wider than the effect — excluded from negatives (B-5)
SUBSTRATE (kill precheck): VR≥1 AND autocorr≥0 across BOTH A-estimators on ALL instruments ⇒ residual not MR ⇒
  Currencies arm dies (0 slots) — reported to the operator; family disposition is checkpoint-only.
POOLED: any cross-instrument/cross-cell aggregate is DISCLOSURE-ONLY unless homogeneity is shown (L-03).
Collapse fraction disclosed for EVERY control and the tripwire (L-15).
```

Bands are informative reads for the operator; no auto-verdict, no auto-RETIRE (integrity/informative split §9).

---

## 8. Power statement

```
POWER: 4h TRAIN ≈ 0.49 × ~5y ≈ 2.4y × ~6 bars/day × ~260 d/y ≈ 3,600 bars/instrument.
  single-worst: ~3,600 candidate bars/instrument; events with |s|>k(trailing-median) ≈ top ~50% by construction
    of the max series → ~1,500–1,800 fade events/instrument (well-powered).
  all|s|>k: multi-member, higher counts; per-member ≈ few hundred+.
  MDE at n≈1,500, block-boot 4h: ≈ 0.3–0.8 bp/event (idiosyncratic return scale) — effects ≥1 bp detectable.
  Predeclared UNPOWERED risk: none expected on single-worst primary at 7 instruments; the ÷σ_t (B=z) cells and
    fixed-h=6 robustness may thin per-cell counts — any cell with n<100 or MDE>1 bp is UNPOWERED, never a negative.
```

---

## 9. Integrity vs informative split

```
HARD (block this run):
  - TRIPWIRE collapse: rho must → 0 under temporal block-permutation of the pairing. Surviving edge ⇒ REJECT (leak).
  - HOLDOUT: TRAIN-only (first 49%); TEST band not emitted; final-30% never loaded. Any touch ⇒ REJECT.
  - CAUSAL PROVENANCE: every verdict-bearing column (u, m, s, k, HL, selection) uses data ≤ t−1; return from next open.
    Trace asserted in analysis_code (≤t-1 lag), diffed by QA. (Estimand-reconciliation gate N/A — no P&L/accounting object.)
INFORMATIVE (operator judges worth): all rho magnitudes, CIs, p_perm, twin Δ / percentiles, collapse fractions,
  substrate VR/autocorr, cost (N/A here). No materiality thresholds, no readiness floors, no gate conjunctions,
  no auto-RETIRE.
```

---

## 10. Golden trace (QA diffs before sign-off)

Deterministic, hand-computable from the frozen construction (A=median, B=raw, C=single-worst, D=hedged,
daily-reset anchor, k=trailing-median, h=HL). The analyst emits a per-bar table `results/golden_trace.parquet`; QA recomputes by hand:

```
GOLDEN-TRACE: the FIRST 3 single-worst fade events after warmup (first full-session + HL/threshold-window
  bars) in TRAIN. For each:
  timestamp t (4h CloseTime); the 7 u_i(t) with signs; m(t)=median; every s_i(t)=u_i−m; the selected argmax_i|s_i|
  and fade side −sign(s_i); h_i from HL; `g_i = σ_i·ln(Open_i(t+1+h)/Open_i(t+1))`, G(t,h), idio, and
  rho_i(t,h). QA hand-verifies:
    (a) σ_i signs correct (USD-quote −1, USD-base +1);
    (b) m = median of the 7 u (label-invariant); s_i, k, HL from confirmed RealClose ≤ t;
    (c) selected instrument = true argmax|s|; direction = −sign(s);
    (d) all signal inputs use bars ≤ t−1 (anchor = last rollover close ≤ t−1, decision close ≤ t−1);
        the forward return uses RealOpen: entry Open(t+1), exit Open(t+1+h) — open-to-open, no close leakage;
    (e) rho recomputed matches the emission bit-for-bit.
  The developer/analyst must NOT hand-pick these events — first-3-post-warmup is the frozen rule.
```

---

## 11. Deliverables

- `analysis_code/` — one module: construction (u/m/s/k/HL), estimand rho, controls (3 twins + tripwire),
  substrate VR/autocorr, bootstrap CI (`xen.evaluation`), permuted-axis null. Canonical `xen` helpers only;
  no local accounting (`check_no_local_accounting` N/A but honored — no P&L).
- `results/` — per-(instrument×cell) rho + CI + p_perm + twin Δ/percentile + collapse fractions; substrate table;
  HL table; `golden_trace.parquet`.
- `plots/` — ≤5: substrate VR/autocorr heatmap; rho-by-axis (marginal per A/B/C/D); signal-vs-twins with CI;
  permutation null bands; collapse-fraction disclosure.
- `analysis.md` (data-analyst, later) — evidence for+against + recommended (non-final) verdict; operator decides.

**Next pipeline stage:** QA-compliance (FRESH context — subagent or new operator session) → operator execution
gate → data-analyst → operator verdict. This is an availability screen: no engine run, no estimand-validation
gate; the integrity gates are §9 (tripwire collapse, holdout fence, causal ≤t-1 provenance).
