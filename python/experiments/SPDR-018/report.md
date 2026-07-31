# SPDR-018 — Report (powering sweep over the complete checkpoint-017 residue)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Lane:** SPDR · TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Status:** **COMPLETE AND CLOSED 2026-07-26** — screen, analysis and integrity addendum all final
- **Code pin:** `44c720f82af52b8b…` · **18 HARD checks, 0 failed** · 37,791 cells · 24,098 signed cells
- **Analyst recommendation:** `HYP-D5` **SUPPORTED**, with two integrity items raised — **both since fixed and re-run** (§7)
- **Operator verdict:** **SUPPORTED — powering succeeded. No gating verdict is taken or implied by this experiment** (§8)
- **Binding analysis of record:** `analysis.md` (fresh-context analyst + orchestrator addendum). `screen.md` is subordinate.
- **Replication companion:** `python/experiments/SPDR-018B/` — cTrader universe, closed separately
- **Post-closure addenda (additive; frozen artifacts untouched):** `addendum-p04-c3-reachability.md`
  (P4 — C3 terminally unpowerable), `addendum-p02-p03-ci-recovery.md` (P2 partly / P3 closed)
- **Corrections:** `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/corrections-log.md`
  — independent adversarial audit 2026-07-26; **this report carried two errors, both now fixed in place**
  (the pooled `edge` and the `log R` sign claim). Verdict unaffected.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: every net figure in this report OVERSTATES performance; the true cost floor is
               strictly higher than the 13.1-16.1 bps charged
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 1. What this experiment was, and what it was not

Checkpoint-017 closed with the extraction question **unresolved at power**, not refuted: SPDR-014
produced **0 powered cells of 927** (MDE 20 / 172 / 796 bps against a ≤10 bps floor) while leaving
coherent but unpowered direction leads on the table.

SPDR-018 is a **precision experiment**. It re-measures every 017 open question **in its original
statement**, using legitimate power levers only — pool with σ̂-normalisation, use the full TRAIN span
where the parent permits, score CONFIRM explicitly, report effective rather than nominal coverage.
No estimand was substituted and no conditioner was un-nested from its event.

> **It carries no gating verdict.** Checkpoint design §2 is explicit: SPDR-018 being an input to the
> capture-axis decision is a *consequence* of its job, not its definition. It does not gate the
> checkpoint, the exploration, or the magnitude work. What SPDR-018 changes is how a capture
> experiment would be *parameterised*, not whether one happens.

**The proof that this was a powering experiment and not a re-scoping one is parent parity**, asserted
in code: each arm reproduces its parent's published cells on the parent's own band to
**4.5e-13 / 1.8e-12 / 9.1e-13 / 0.0** across arms A–D. The object is the same object; only the data
behind each estimate changed.

---

## 2. The powering result — did the levers work?

**Yes, decisively, for most of the residue.**

| | SPDR-014 (parent) | SPDR-018 |
|---|---|---|
| powered signed cells | **0 of 927** | **1,413** (+98 straddle characterisation cells) |
| median block MDE on the C1 object | 20 / 172 / 796 bps | **7.87 bps** against a ≤10 bps target |
| residue items carrying cells | — | **all 27** — nothing narrowed |
| `NOT_RESOLVABLE` delivered as a quantified answer | — | **3,559 cells**, median shortfall 7.87×, p90 27.3× |

Arms A and D are substantially resolved. Arm C's event-nested strata are the stubborn ones: 632 of
22,194 arm-C cells reach target (2.8%), and **C3 alone is 1,946 of the 3,559 unresolved cells (55%)**.

---

## 3. Per-item ledger — every checkpoint-017 open question, booked

This is the deliverable the mid-checkpoint reflection needs. Each item is booked into exactly one of
three classes. **Per B-5, class C is a statement about sample size and is never evidence against.**

### Class A — NOW POWERED AND ANSWERED (the question is closed with a magnitude)

| Item | Object | Answer, with magnitude | Direction vs registration |
|---|---|---|---|
| **A1** | V-REGIME-HMM HIGH−LOW next-\|move\| gap (017: 76/83 unpowered) | Pooled TRAIN **D1 +180.4 bps [119.7, 252.1]**, **H4 +67.5 [54.7, 80.6]**, **H1 +48.0 [41.7, 54.7]**. A second, smaller emitted variant set gives D1 +100.1 / H4 +34.3 / H1 +18.1 — **the honest H1 range is +18 to +48 bps**. Per symbol: H1 median +24.7, **97.3% CI-excluding-zero positive** | **SUPPORTED** — large, positive, on every clock and band |
| **A2** | V-TAIL p90/p95 exceedance at D1 | H1 median **+0.056** (p90) / **+0.031** (p95), **90.9%** of per-symbol cells CI-excluding-zero; D1 **+0.040 / +0.022** at 4.5% / 0.0%. Every cell lands WASH because the magnitude is below the band threshold, **not** because it is unmeasured | **SUPPORTED as a WASH-magnitude** on H1; D1 not resolvable |
| **A3** | DESIGN-band date deficit across V-LEVEL / V-REGIME / V-XS | Two-part: per-symbol DESIGN runs **99–102 dates** against the 225 required (6.2% reach it) — **not resolvable by catalog history**; **pooled** DESIGN reaches **327–330 dates (85.7% ≥ 225)** and CONFIRM/TRAIN per-symbol reach 285–394 | **RESOLVED** — the band cannot support the claim per symbol; pooling can |
| **A4** | V-CLOCK calendar/session dummies at D1 | D1 cells run at exactly **1.000 observations per date** against 6–9 dummies. Median incremental R²: D1 **−0.032 to −0.050**, H1 **−0.0004 to −0.003**, H4 **−0.001 to −0.015**; session-only on D1 exactly 0.000 in all 48 cells | **REFUTED in the registered direction** — measured incremental value of calendar features is zero to slightly negative everywhere measurable. Consistent with SoT §3.2 "do not use calendar/session features" |
| **A5** | §6.4 clause unsatisfiability + calendar-thirds vacuity (017: 42/45 had one powered third) | **135 of 135** cells now have `thirds_populated == 3`, `clause_satisfiable == True`, `thirds_sign_agree == 3` | **SUPPORTED — a clean reversal.** The cleanest single resolution in the run |
| **A-IC** | rank IC apparatus | H1 per-symbol median **0.3262**, **100% of 165 cells CI-excluding-zero**; pooled H1 **0.421–0.434**. Replicates and slightly exceeds SoT §3.2's banked 0.338 / 0.301 | **SUPPORTED** |
| **B4** | ZZ structural leg per symbol (017: "unpowered via MDE, not trade count") | **30 of 146** powered. `p` **0.3475**, `W` 152.5, `L` 83.1, `W/L` **1.804**, `p_be` 0.3567, `p_be_net` **0.4112**, gross **−2.82 bps**, net **−16.74**, edge **−0.067** | **RESOLVED — below both break-evens** |
| **B5** | M15 arms (largest powered block in arm B) | **736 of 2,555** powered. M15: `p` 0.3358, `W/L` 1.841, `p_be_net` 0.4385, gross **−1.98**, edge −0.102. H1: `p` 0.3372, `W/L` 1.961, gross **−0.13**, edge −0.069. **H1 is ~1.9 bps closer to gross break-even than M15** — a real clock effect, ~7× smaller than the cost floor | **RESOLVED — below break-even, with a measured clock ordering** |
| **C1** | the residual object itself (017: **0 of 927 powered**) | **121 of 7,181** powered at median block MDE **7.87 bps**. Median gross mean **−0.30 bps**; 1 of 121 CI-excluding-zero. Grid-wide C1 median MDE still 103 bps at median n=77, so **105 C1 cells stay formally NOT_RESOLVABLE** | **PARTIALLY RESOLVED — the headline reversal of the 017 blocker** |
| **C4** | E-TOUCH / E-CLOSE asymmetry | **33 of 170** powered; `p` 0.4672, `W/L` 1.132, gross **−0.17 bps**. Grid-wide ordering **E-TOUCH (+0.6 to +1.5) > E-HORIZON (−0.03 to +0.69) > E-CLOSE (−1.2 to −3.0)** — a real ~3–4 bps structure, below the cost floor | **RESOLVED — genuine measured structure, sub-cost** |
| **C5** | magnitude scaling | **174 of 3,570** powered. The registered claim was "magnitude strata lift residual *magnitude* while the rate stays ≈0.50" — **that is what the data shows**: rate pinned in **0.4147–0.4795** while `W` ranges **109.5 → 235.4 bps** and `L` **94.7 → 171.1**; `W/L` moves only 1.10 → 1.40 | **SUPPORTED as registered — and it is the kill.** Selection scales *both* sides of the identity, so it scales a near-zero (SoT §3.1 measured, not argued) |
| **C6** | z / h dose-response | **14 of 62** powered, monotone and measurable: z=1.0/h=4 **+1.15 bps** (`p` 0.4761, `W/L` 1.116); z=1.0/h=12 **+2.86** (`p` 0.4999, `W/L` 1.025); z=1.5/h=12 **−1.43**; z=2.0/h=4 **−0.52**. Longer hold at low z pushes `p` → 0.50 and `W/L` → 1.0; higher z pushes `p` down and `W/L` up — **they move against each other and the mean stays within ±3 bps of zero** | **RESOLVED — dose-response exists and runs along the zero line** |
| **C7** | DESIGN→CONFIRM sign flip | **RESOLVED, and it reverses the 017 concern.** 2,714 pairs, **44.14% flip — below a coin flip**; only **6.63%** of all pairs exceed the two-band MDE; `n`-weighted the bands agree to **0.33 bps** (DESIGN −13.72, CONFIRM −13.39). The equal-weight gap was a thin-cell artifact | **REFUTED as an instability** — more sign-stable than noise |
| **C8** | pooled rate lean, two weightings disagreeing | Row-weighted `p_momo` **0.4676**, symbol-weighted **0.4699**. **Those two medians differ by 0.0023, but that is a difference OF MEDIANS, not a typical per-cell disagreement — the per-cell median \|difference\| is 0.0082 (p95 0.0431) across 340 cells.** The conclusion holds (0.0082 against a rate of 0.47 is still agreement) but the 0.0023 figure, carried from `analysis.md`, understates the per-cell spread ~3.6×. The measured lean is toward **mean-reversion**, ~0.47 against a 0.50 reference, on both weightings | **REFUTED as a disagreement** — the 017 concern dissolves |
| **C9** | `DA-STRADDLE` | **98 of 150** at target. **CHARACTERISATION ONLY** (SoT §0 operator exception): median per-cell mean partial-net **−29.07 bps**, median-of-medians **−30.0**. No strategy framing, no policy, no graduation path | **Characterised, not a branch** |
| **D1** | `trans_up` / `trans_dn` counts (017: `n_trans` < 50 blocker) | **1,398 of 1,800** powered. H1 median `n_trans` **624.5 / 400** CONFIRM and **1,032 / 635** TRAIN, **94.7% / 92.7% ≥ 50**. H4 CONFIRM 82.0% / 76.7%; **H4 DESIGN is the residual gap at 54.7% / 52.7%** | **RESOLVED on H1, mostly on H4-CONFIRM — the 017 blocker is gone** |
| **D2** | run-length MAE | H1 median MAE **11.95–12.00 bars** against a predicted `E[run]` of **18.9–23.1**; H4 **10.9–11.3** vs 17.8–21.1. **The predictor's typical error is roughly half the quantity it predicts.** 0 of 300 at target is a **definitional** gap — no target rule was ever defined for this item — not a power failure | **RESOLVED as a disclosure; weak predictor quantified** |
| **D3** | T-GT-MED10 (017: "12/21 SUPPORTED → INCONCLUSIVE") | Lift over base rate: `ridge_cont` **+0.063** CONFIRM / +0.064 TRAIN, `ar1_threshold` **+0.048**, `logit_ridge` **+0.058 / +0.042**. 74 cells NOT_RESOLVABLE | **RESOLVED with magnitudes — a measured +5 to +6 point lift**, model-dependent resolvability |
| **D4** | T-GT-MED5 (017: "2 unexamined failures") | `ridge_cont` **+0.107** CONFIRM / +0.102 TRAIN / +0.096 DESIGN; `ar1_threshold` +0.077 to +0.087; `logit_ridge` +0.022 to +0.059. **`ridge_cont` at K=5 is the strongest D3/D4 cell: hit 0.585 vs base 0.483, 21 of 26 SUPPORTED on CONFIRM.** The two unexamined failures are the `logit_ridge` DESIGN cells | **SUPPORTED — the strongest ordinal-target object in the run** |
| **D5** | 2a H4 k=1 (017: "6/16 SUPPORTED, median ≈ +0.0002") | ΔBrier vs persistence, k=1: median **0.0000** CONFIRM/DESIGN, **−0.00049** TRAIN → **k=1 is inert**. But the same model at k=4/k=12 on H1 gives **−0.0199 / −0.1085**, 57–59% CI-excluding-zero — reproducing SoT §3.2's banked −0.025 / −0.114 to within 0.006 | **Split verdict: k=1 REFUTED as a gate; k=4/12 SUPPORTED and replicated** |
| **D6** | R-HMM-RV as a forecaster | H1: k=1 **−0.00135**, k=4 **−0.00595**, k=12 **−0.0317**; 36–47% CI-excluding-zero, H4 weaker. **Roughly one third of R-MARKOV's effect at matched k** | **RESOLVED — weak but non-zero.** Consistent with "do not use R-HMM-RV as a forecaster" |
| **D7** | D1 stickiness (was disclosure-only) | `p_stay` median **0.9486** CONFIRM / 0.9376 DESIGN / 0.9365 TRAIN, range 0.866–1.000, 22 of 25 SUPPORTED. **Daily level-regimes are ~94% persistent — the mechanical explanation for D1's rare-transition problem** | **SUPPORTED — now scored** |
| **D8** | the CONFIRM verify slice SPDR-015 never scored | **2,534 cells, 1,800 flagged `never_scored_before`.** Pooled `T-GT-CUR` on CONFIRM: `ar1_threshold` **0.6465 [0.6247, 0.6678]**, `logit_ridge` **0.6999 [0.6831, 0.7176]**, `ridge_cont` **0.6781 [0.6589, 0.6978]** against a base rate of **0.4674**, n = 5,698. All three CIs sit 16–23 points above base and do not approach it | **SUPPORTED — the most robust positive object in the entire run.** CONFIRM reproduces DESIGN |

### Class B — POWERED, AND THE ANSWER RUNS AGAINST REGISTRATION

| Item | Finding | Does it route? |
|---|---|---|
| **The counter-outcome** | **130 of 1,413** powered cells have a gross-mean CI excluding zero — **129 negative, 1 positive**. Median **−4.12 bps**, max \|effect\| **12.93 bps**. On signed direction cells a powered negative mean **is** a powered directional statement: the registered side reliably loses | **NO.** Flipping the side: **0 of 129** clear even the *partial* cost floor; best flipped gross **+12.93 bps** against 13.1–16.0 bps; best flipped net **−0.65 bps**. SoT §10 end-state 3 is checked and **not satisfied at this cost floor** |
| **Tail asymmetry** | Under a pure null with nominal 95% CIs on 1,413 cells you would expect ~35 per tail. Observed **1 positive, 129 negative** — the positive tail is **depleted well below chance** while the negative tail is **enriched ~3.7×** | Reported as a positive quantification, not a null. Corroborated independently by C8's mean-reversion lean (`p_momo` ≈ 0.468–0.470) and by arm C's side-derangement (live −12.22 bps, percentile **0.0065**) |
| **`W/L` as a free lever** | **REFUTED as a free degree of freedom, confirmed as a real and large one.** `log(W/L) = −0.0048 + 0.9408·log((1−p)/p)`, **R² 0.9667** — 96.7% of payoff-asymmetry variance is the arithmetic mirror of the rate. Exit geometry moves `W/L` **0.150 → 10.05 (67×)** while `p` moves inversely by almost exactly the offsetting amount; the gross mean does **not** improve (−0.99 bps at `W/L` 2.06; **−37.9 bps at `W/L` 10.05**). Free residual `log R` has sd 0.073 and is negative **at the centre** — median **−0.0301**, mean **−0.0356**, and negative in all five per-exit-mode medians — but **not in every cell**: `log R > 0` in **459 of 1,413 (32.5%)**, which is the *identical* set to the 32.5% clearing gross break-even, since `R > 1 ⟺ p > p_be`. (An earlier draft of this row said "uniformly negative"; that was false and contradicted the 32.5% figure four lines above it. `analysis.md` §5.3 was precise — it said this of the per-mode medians.) **82.8%** of powered cells cannot have their `W/L` distinguished from the driftless mirror at all | This is the decisive finding for the capture branch. The branch has a lever; on this evidence the lever **does not have a positive direction** |

### Class C — STILL NOT RESOLVABLE (a power statement, never a negative), with new information

| Item | State | New information gained |
|---|---|---|
| **B1** `stop`-only / `trail`-only | **0 of 2,044** at target; pooling did not fix it | Now *measured*: `stop`-only at `p` **0.067**, `W/L` **10.05**, gross **−37.9 bps**; `trail`-only at `p` **0.870**, `W/L` **0.150**, gross **−7.0 bps**. One-tail estimators by construction, exactly as design §9 predicted. **Their value is not as expectancy cells but as the `W/L` movability evidence above** |
| **B2** unpowered `time`-arm cells | **0 of 1,022** at target; median n 108 episodes / 108 dates | The `time` arm sits at `p` **0.4923**, `W/L` **0.9993**, gross **−7.50 bps** — almost exactly the symmetric-payoff coin flip the martingale argument predicts. **Itself informative** |
| **B3** the positive-mean cells | **UNPOWERED — and the count is 830, not the design's 125.** 0 of 830 at target; median 46 episodes / 28 dates | The 830 are exactly the arm-B `per_symbol` DESIGN+CONFIRM cells with positive **partial-net** mean (284+194+187+165), reproducing all three of the screen's cross-checks. **The design's "125" reproduces under no constructible slice — a premise defect in a frozen operator-signed design.** The pooled counterparts of the same arms *are* powered and sit below break-even, so the pooled evidence speaks where the per-symbol cells cannot |
| **C2** shock-conditioned MOMO | **UNPOWERED in the grid** — 65 of 1,020 at target, 263 NOT_RESOLVABLE. Powered C2 cells: `p` 0.4695, `W/L` 1.124, gross **−0.32 bps** | **The one live thread in the run**, and it lives in the *control*, not the grid: M-3 magnitude-matched comparator gives live **+22.6 bps** against a null mean of −14.5 (sd 22.35), **percentile 0.95**, one-sided p = 0.05, n = 505 — **+37.1 bps above magnitude-matched bars**, and above the partial cost floor (15.3 bps) on this cell class. Also: 622 of 2,040 `shock_flag` cells have a gross mean above their cost floor and 22 have a CI-low above it — **none at target precision.** Four caveats bind hard: n=505 is one control cell not a powered stratum; percentile 0.95 is exactly the boundary against an enormous null; multiplicity across 37,791 cells; spread not charged. **SPDR-018B was built to replicate this and returned UNRESOLVED — neither replication nor refutation** (see that report §4) |
| **C3** ordered `last_k` vol-flip | **NOT_RESOLVABLE, decisively** — 127 of 6,987 at target, **1,946 NOT_RESOLVABLE = 55% of the entire unresolved population**. Median n 102 events | Powered C3 cells: `p` 0.4668, `W/L` 1.140, gross **+0.34 bps** — the only positive item-level gross median in arm C. The 017 "thin strata" concern is **confirmed as the binding constraint**; pooling + σ̂-normalisation did not close it in the registered event-nested form. **This is the "conditional direction is unpowered, not refuted" object the checkpoint premise names, and it is still that** |
| **A3 (per-symbol DESIGN)** | `NOT_RESOLVABLE` by catalog history — 99–102 dates against 225 required | The shortfall is a property of the Bybit catalog's length, not of the effect. Pooled DESIGN resolves it |
| **D3 / D4 residual cells** | 74 and 63 cells NOT_RESOLVABLE respectively | Resolvability is **model-dependent**: `ridge_cont` resolves, `logit_ridge` DESIGN largely does not |

---

## 4. The `(p, W, L)` layer — the axis-B object that had never been measured

Checkpoint design §3 named `W`, `L`, `W/L` as **NEVER MEASURED**. They are now measured on
**24,098 signed cells**, with the identity `p·W − (1−p)·L = mean` reconstructing to **1.46e-11 bps**
(against a 0.01 bps tolerance) and `p_be`, `p_be_net`, `edge` re-derived from `W`, `L`, `cost` to
**max difference 0.0**.

```
CRYPTO (25 Bybit perps) - 1,413 powered signed cells, TRAIN only, GROSS PRIMARY
  Each term is reported as MEDIAN | MEAN | 10%-TRIMMED MEAN across the powered cells.
  The medians are the headline (fat-tailed family); all three are given because they differ.

  term        median      mean    trim10
  p           0.3887    0.3781    0.3821
  W (bps)    128.65    128.81    126.67
  L (bps)     75.55     84.69     82.32     <-- L is the term where mean and median diverge most
  W/L          1.4844    1.7548    1.6655
  p_be         0.4025    0.3859    0.3908
  p_be_net     0.4992    0.4641    0.4688
  edge        -0.0728   -0.0860   -0.0818
  gross mean  -1.1775   -1.1942   -1.1796   (per-cell gross mean, aggregated three ways)

  gap to own gross break-even (median p - median p_be) = -0.0138
  W/L > 1 in 99.93% of cells
  gross mean = -1.178 bps (= 0.016 sigma, sigma-hat = 73.00 bps)
  net mean   = -15.157 bps  (cost 13.540 bps charged; spread NOT charged)
  gross median = -14.43   gross trimmed-10 = -11.67   <-- the three statistics DISAGREE by 13 bps
  clears gross break-even = 459/1,413 (32.5%)   clears net break-even = 0/1,413 (0.0%)
  gap decomposition: rate term +0.0067 | cost term +0.0650  -> cost is 90.7% of the gap
      arm C: rate +0.0007, cost +0.0575 -> cost is 98.8%; the rate sits ESSENTIALLY AT gross BE
      arm B: rate +0.0114, cost +0.0866 -> cost is 88.4%
  arm B: p 0.336  W 107.6  L 53.9  W/L 1.880  p_be_net 0.434  edge -0.096  gross -1.75
  arm C: p 0.467  W 142.1  L 124.5 W/L 1.136  p_be_net 0.526  edge -0.057  gross +0.08
  mirror fit: log(W/L) = -0.0048 + 0.9408 * log((1-p)/p),  R2 0.9667,  sd(log R) 0.0729
              82.8% of powered cells cannot be distinguished from the driftless mirror
  edge is NEGATIVE in every one of 21 named symbols (-0.020 to -0.160); no symbol is an exception
```

> **Reading note — do not subtract these rows.** `edge = p − p_be_net` holds **exactly per cell** (max
> deviation 0.0), but **neither the median nor the mean operator is additive across cells**. Median `p`
> − median `p_be_net` gives −0.1105, whereas the true **median `edge` is −0.0728** — a 0.038
> discrepancy, and the derived figure is the more pessimistic one. Always read `edge` from its own
> column. (This report previously carried the derived −0.1105; corrected 2026-07-26 against
> `results/analyst_per_cell_magnitudes.parquet`. The binding `analysis.md` never stated a pooled
> `edge` — its arm-level figures are B −0.096 / C −0.057, and its per-symbol range is −0.020 to
> −0.160, all consistent with a pooled median of −0.0728.)

**The two arms are structurally different objects and must not be pooled into one story.** Arm B is
low-rate / high-asymmetry (`p` 0.34, `W/L` 1.88); arm C is a near-coin-flip, near-symmetric object
(`p` 0.47, `W/L` 1.14) whose **gross median is positive (+0.08 bps)**.

**Nothing clears `p_be_net`:** 0 of 1,413 powered cells, 0 of 24,098 signed cells with a `net_mean`
CI-low above zero, 0 with a `gross_edge` CI-low above zero, and 0 with a `net_edge` CI-low above zero.

---

## 5. Controls — what each one can and cannot separate

Report layers per L-32 / INFR-016, never gates. Each read against **its own plant curve**, which
states what the control could have detected.

| Control | Non-vacuous? | Resolution | What it establishes |
|---|---|---|---|
| Side-derangement, arm B | yes (0 fixed points, 2,000 seeds) | ~10–20 bps | live −1.302 bps at percentile **0.475** — dead centre of the null. **No side-attributable effect above ~10–20 bps**; a smaller one would be invisible |
| Side-derangement, arm C | yes | ~20 bps up, sharp down | live **−12.221 bps at percentile 0.0065**, ~2.4 null sd below the null mean. **The sides carry real directional information and it points the wrong way.** The strongest single control result in the run |
| M-3 `mag_high` | yes (disjoint pool in all 10 deciles) | ~15–20 bps | live −11.607 vs comparator −10.704, percentile **0.46**, gap **0.90 bps**. **`mag_high` is "the decision bar was large", not "the volatility state"** |
| M-3 `shock_flag` | yes (disjoint pool in all 10 deciles) | ~5 bps | live **+22.569** vs comparator −14.516 (sd 22.352), percentile **0.95**, n_live 505. **+37.1 bps over magnitude-matched.** The one live thread |
| Ambient-base, arm B | disclosure | mean CI ±25 bps | Rate **+0.0423**, `W` **+130.2**, `L` **+87.6**, IQR **+202.3 bps** — but `W/L` **−0.174**. The conditioner scales the opportunity **and scales both sides of it**. Mean and median move in *opposite* directions (+11.1 vs −49.3) |
| Ambient-base, arm C | disclosure | mean CI ±10 bps | Rate **+0.0255**, `W` **−33.7**, `W/L` **−0.124**, Δmean only **−0.318 bps**. The event selects a **higher-rate, smaller-win, more symmetric** distribution whose net effect on the mean is ~zero because the terms offset. **A mean-only read would have called this "nothing happened", and something did** |
| TRIPWIRE-3 forward-path derangement | report layer only | n/a | Collapse fractions 0.161 and 0.904, correctly **not** the causality claim. Per M-5 uninterpretable near a zero live mean — **neither number carries weight in either direction** |

---

## 6. Integrity

**18 HARD checks, 0 failed** (code pin `44c720f82af52b8b…`) after the §7 addendum. Fences, holdouts
and provenance all hold with margin: zero rows at or after 2025-01-08 (Bybit) or 2024-12-13
(cTrader); unit pin computed on **25 of 25 symbols** with `symbols_without_a_value: []`, pooled TRAIN
median σ̂ **73.0006 bps**, L-21 compliant.

**Disclosures the analyst raised that remain open as recorded gaps, none of them verdict-bearing:**

| # | Gap | Assessment |
|---|---|---|
| 1 | **Arm C parent parity covers 6,127 of 8,450 parent cells (72.5%)** — arms A/B/D cover 100% | No evidence of drift, but the designated anti-drift proof is 27.5% incomplete on the arm carrying 59% of the grid |
| 2 | **Median and 10% trimmed-mean CIs exist on 240 of 24,098 signed cells (1.0%)** — 4.0% of powered cells — while design §6.1 requires all three co-reported *because the family is fat-tailed* | **The material one.** The three statistics disagree by 13 bps with 68% sign agreement. The "cells sit at gross break-even" narrative is the **most favourable of the three by 13 bps**; on the median the typical powered cell is 14 bps below zero *before* cost |
| 3 | **M-2 span disclosure missing on 3,054 of 22,044 horizon-carrying arm-C cells (13.9%)** | Measured span effect is ~1.3 bps on cells that do carry it — changes no read |
| 4 | **`plots/` is empty**; design §10 budgeted ≤8 | Cosmetic |
| 5 | **Column-name trap**: `net_*` is the decomposition of the already-net series (`net_cost_bps = 0`), so `net_p_be_net` reads 0.4141 instead of the correct **0.4992**. `gross_*` is the correct SoT §2 family | Documented; every figure here uses `gross_*` |
| 6 | **`levers_exhausted` means "levers applied", not "levers failed"** — 376 cells carry it *alongside* `at_parent_target_precision` | `not_resolvable.json` is the authoritative object |
| 7 | **Flat legs are excluded from `p`**, so the identity describes the mean over non-flat legs | ≤0.6 bps on powered cells; 226 cells grid-wide exceed 5% flat. **Charge flat legs their cost in any 019/020 budget** |
| 8 | **Multiplicity disclosed, not treated** (operator directive, AMENDMENT-C3) | Affects only the two single-cell positives, both already discounted on those grounds |

---

## 7. Addendum disposition — the two integrity items the analyst raised, both fixed

The analyst reviewed an emission carrying **16** HARD checks and correctly identified two
design-declared HARD items that had never run, underneath a `screen.md` claiming "Deviations: none".
Both were fixed and the screen re-run; the emission of record carries **18**.

| Item raised | Disposition |
|---|---|
| **`TRIPWIRE-2`** (leaky-variant discrimination) declared HARD but **absent from the self-check** — half of design §7.1's causality claim | **Fixed and run.** Now computed on the independent self-check side (`golden.g6`), rebuilding both variants from the fenced catalog. Legal **85.34 bps** vs leaky twin **644.71 bps** on the same 58 rows — a **7.55× separation**. Design §7.1 anticipated "orders of magnitude"; 7.55× is material and one-directional but **does not meet that bar**, and is reported as measured |
| **`Determinism`** silently downgraded HARD → INFORMATIVE and not executed | **Fixed and run.** Now executes unconditionally whenever `--jobs > 1`, independent of `--resume`, so a resumed run cannot skip it. 630 cells sequential vs `--jobs 8`: **zero columns differ** |
| **`screen.md` claiming "Deviations: none"** while both were absent | **Corrected.** §8 now carries the defect, cause and fix; §9 distinguishes design deviations (none) from the process defect (one, recorded) |

**No estimand, object, band, control or cell value was touched.** The re-run recomputed only controls,
tripwires and the self-check; arms A–D were resumed byte-identical from their emitted parquets. The
analyst's substantive findings are unchanged.

**Mitigating context recorded at the time, and still the right read:** this is a re-scoring
experiment whose causal construction is inherited and whose parent parity is exact; TRIPWIRE-1 held
on all four arms; and the direction of the headline result is negative-to-null, whereas a look-ahead
leak inflates edges. There was no inflated edge to explain away.

---

## 8. Verdict

### On `HYP-D5` — a precision hypothesis

> ## **SUPPORTED. The powering experiment worked.**
>
> **Operator-confirmed 2026-07-26.** No integrity item remains outstanding (§7).

`HYP-D5` asked whether every question checkpoint-017 left UNPOWERED or INCONCLUSIVE could be
resolved to its own target precision using legitimate power levers alone, without re-defining any
estimand — and if so, what the answers are. **It could, for most of it, and the answers were
produced.** 1,413 signed cells reach their parents' own bars against SPDR-014's 0 of 927; parent
parity to 1e-12 proves no estimand was re-specified; every §2 item carries cells; A1, A5, C7, C8, D7
and D8 are cleanly resolved with magnitudes and CIs; and the 3,559 cells that could not be resolved
are delivered as quantified first-class `NOT_RESOLVABLE` answers rather than as silence.

**The three pieces of evidence that most drive this:**

1. **Parent parity at 4.5e-13 / 1.8e-12 / 9.1e-13 / 0.0 across arms A–D** — the anti-drift proof
   that separates a powering experiment from a re-scoping one.
2. **121 powered C1 cells at a median block MDE of 7.87 bps**, on the object that gave the parent
   0 of 927 at 20–796 bps.
3. **A5's complete reversal** (135/135 cells satisfy a clause 017 found satisfiable in 3/45) and
   **D8's 1,800 never-before-scored cells** reproducing DESIGN on CONFIRM.

### What this experiment explicitly does NOT decide

- **No gating verdict.** SPDR-018 does not gate the checkpoint, the capture axis, or the
  exploration. Checkpoint design §2 is explicit and this report changes nothing about it.
- **No family action.** `CF-VOLDIR-001` status is unchanged and remains `REGISTERED`. Family status
  transitions happen only at a checkpoint retrospective, operator-signed.
- **No tradability, deployability, cost-complete, graduation or XENA claim.**
- **No end-state decision.** SoT §10 end-states 1, 2 and 3 are all evidenced below and none is taken
  here.

### Substantive inputs to the mid-checkpoint reflection (not decisions)

- **Nothing clears `p_be_net`** — 0 of 1,413 powered cells, and the distance is 88% (arm B) to 99%
  (arm C) **cost**, not rate. Arm C's rate sits **0.0007** from its own gross break-even.
- **The `W/L` handle exists, is 67× movable, and does not point up.** 96.7% mirror-determined; the
  free residual is negative at the centre (median log R −0.0301, mean −0.0356) though positive in
  459 of 1,413 cells — the same 32.5% that clears gross break-even, by identity; 82.8% of powered
  cells are indistinguishable from the
  driftless mirror. **Any 019/020 proposal must now name the mechanism that puts `R` above 1,
  because five distinct exit devices spanning a 67× range of `W/L` did not.**
- **Selection scales both sides of the identity** (C5 and both ambient-base reads) — SoT §3.1
  measured rather than argued.
- **End-state 1 is where the evidence points, and two things forbid taking it:** the C2 M-3 survivor,
  and 3,559 `NOT_RESOLVABLE` cells with 55% in C3 — the ordered vol-flip the checkpoint premise names
  as *unpowered, not refuted*. **Closing over those would read UNPOWERED as a negative, which B-5
  forbids and which is precisely the error checkpoint-017 was closed to avoid.**
- **End-state 3 is checked and not satisfied at this cost floor.** **End-state 2 requires something to
  clear `p_be_net`; nothing does.**

### Caveat that keeps §4's conclusion honest

SPDR-018 measured `W/L` under the **parents' own exit geometries**, not under a designed capture
policy. It shows that the five geometries present in the data all sit on the zero line. It cannot
rule out that some geometry outside this grid sits off it. What it does is **raise the bar**: the
mechanism must be named, not searched for.

---

## 9. Threads this experiment could not resolve (proposals, not actions)

| # | Thread | Why it needs new work | Status |
|---|---|---|---|
| **P1** | **Is `shock_flag` real?** Re-run M-3 at `n` in the thousands on the *powered* grid strata rather than one 505-row control cell, with multiplicity treated | **SKIPPED BY OPERATOR 2026-07-26** — no SPDR-018C. **Consequence: C2 cannot be settled on this data**, and at the retrospective it must be booked as **unresolved-and-parked — a terminal `NOT_RESOLVABLE`, never a refutation** (B-5) | **CLOSED — WILL NOT RUN** |
| **P2** | **Median / trimmed-mean CIs on the powered cells** | **DONE for 451 of the 1,413** (arm-B `per_symbol`) → `addendum-p02-p03-ci-recovery.md`. **The median CI excludes zero on 449/451 and the trimmed on 451/451, all negative, while the MEAN CI does so on only 46/451** — so the near-break-even framing is the only one of the three statistics that fails to reject zero, and the negative read is *stronger* than reported. Identity conclusions unaffected (it is a mean identity). **Still open: arm C's 534 cells and the `trail`/`stop` populations** | **PARTLY DONE** |
| **P3** | **TRIPWIRE-2 and Determinism** | Both declared HARD, both cheap | **CLOSED** — done, §7 |
| **P4** | **What `n` would resolve C3?** | **ANSWERED 2026-07-26** → `addendum-p04-c3-reachability.md`. All 1,946 unresolved C3 cells are already pooled+σ-normalised on full TRAIN (no lever remains), median **81× short**, and at the conditioner's own event rate (3 per 10,000 bars) the median cell needs **201 years** of 25-symbol history — 88.3% need >20y. **C3 is terminally unpowerable in its registered form: unpowerable, NOT refuted.** Powering it requires changing the event definition, i.e. a new object and a new registration | **CLOSED — ANSWERED** |
| **P5** | **The per-symbol spread pin** (SoT §3 axis E) | The difference between "nothing clears the floor by 0.65 bps" and "nothing comes close". No capture design should be parameterised before it exists | **OPEN / BLOCKING** |
| **P6** | **Arm C parity on the remaining 2,323 parent cells** | Completes the anti-drift proof | **OPEN** |
| **P7** *(new)* | **CI fragility sweep** (`ci_low_seed_range` + block sensitivity), required by INFR-004 / L-20 and emitted nowhere in either run | **CLOSED 2026-07-26** → `addendum-p02-p03-ci-recovery.md` §4. Seed spans **~4.8% of CI width**, block spans **0.43–0.65 bps** against 2–18 bps effects. **No read in either run rests on a Monte-Carlo or block artifact.** It was never a missing method: computed on all 37,791 cells and discarded at `cells.py:127` | **CLOSED** |

---

## 10. Artifacts

```
python/experiments/SPDR-018/
├── design.md                    # frozen, operator-signed, no amendments
├── screen.md                    # subordinate; corrected §8/§9 after the addendum
├── analysis.md                  # BINDING (fresh-context analyst) + orchestrator addendum
├── report.md                    # this file
├── addendum-p04-c3-reachability.md      # P4 CLOSED: C3 terminally unpowerable (201y median)
├── addendum-p02-p03-ci-recovery.md      # P2 partly / P3 CLOSED: median+trimmed CIs, CI fragility
├── screen_code/                 # code pin 44c720f82af52b8b…
├── analysis_code/a01…a06         # analyst's own scripts; screen_code never imported
├── results/p04_c3_reachability.csv       # 1,946 C3 cells with required n vs the catalog ceiling
├── results/p02_p03_full_ci_armB.parquet  # 451 cells x 118 cols: recovered CIs + fragility
└── results/                     # 37,791 cells; integrity_selfcheck.json (18 HARD, 0 failed);
                                 # not_resolvable.json (3,559); unit_pin.json (sigma-hat 73.0006);
                                 # analyst_per_cell_magnitudes.parquet (24,098 signed cells);
                                 # analyst_stratum_tables.csv (9 stratum views)
```

`plots/` is empty (recorded gap §6.4).

---

## 11. Governance record

| Item | Value |
|---|---|
| Counted TEST reads consumed | **0** |
| Multiplicity slots consumed | **0** (AMENDMENT-C3: disclosed, not rationed) |
| Holdout contact | **none** — Bybit 2025-01-08 and cTrader 2024-12-13 never queried |
| Family status change | **none** — `CF-VOLDIR-001` remains `REGISTERED` |
| XENA authorisation | **none** — `XENA-VOLDIR-001` remains `RESERVED` |
| Registry rows appended | evidence / disposition only |
| Lane | SPDR (`docs/references/spdr-lane.md`) — TRAIN-only, disposition-only, no tradability claim |

**No tradability, deployability, cost-complete, family-status, graduation or XENA claim is made or
implied by this document.**
