# SPDR-018 — `analysis.md` (fresh-context data analyst, BINDING read)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Lane:** SPDR stage 5 · TRAIN-only · 0 counted TEST reads · no family action · no XENA
- **Design:** `design.md` (frozen, operator-signed, no amendments) — binding
- **Screen summary:** `screen.md` — subordinate; every number in it treated below as a claim to verify
- **Analyst code:** `analysis_code/a01…a06` — all figures re-derived from `results/*.parquet` and `results/*.json`. **`screen_code/` was never imported or read.**
- **Analyst artifacts:** `results/analyst_per_cell_magnitudes.parquet` (24,098 signed cells, full magnitude + CI table — L-03: nothing hidden behind a pooled count), `results/analyst_stratum_tables.csv` (9 stratum views).

```
SPREAD-COST-DISCLOSURE  (repeated because every net figure below inherits it)
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: EVERY net figure in this document OVERSTATES true performance. The real cost floor
               is strictly higher than the 13.1-16.1 bps charged.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

> **Scope.** This document quantifies and recommends. It takes **no disposition**. The verdict and disposition are the operator's, at the mid-checkpoint reflection. Nothing here is a family action, a graduation, a tradability claim, or a XENA authorisation.
>
> **B-5 applied symmetrically throughout.** `UNPOWERED` and `NOT_RESOLVABLE` are statements about sample size and are never reported as evidence against. `SUGGESTIVE` is never reported as `SUPPORTED`. No read anywhere is phrased against `p > 0.5`; the reference is always each cell's own `p_be_net`.

---

## 0. Executive summary for the operator (plain language, ~20 seconds)

The powering experiment worked. Questions checkpoint-017 could not answer are now answered.

1. **The residue is now largely powered.** 1,413 signed cells reach their parent screen's own precision bar, against SPDR-014's 0 of 927. Arms A and D are substantially resolved. Arm C's event-nested strata are the stubborn ones; 3,559 cells remain short.
2. **Nothing clears the cost floor.** Of the 1,413 powered signed cells, **459 (32.5%) sit above their gross break-even and 0 sit above their net break-even.** I re-derived both. The screen's numbers are exactly right.
3. **The distance to break-even is almost entirely the cost, not the rate.** Arm C: 99% of the gap is the cost term; arm B: 88%. The measured rate sits essentially *at* gross break-even.
4. **`W/L` is not a free handle — it is 97% determined by `p`.** This is the decisive new finding and it is a direct test, not an assertion. Exit geometry moves `W/L` from 0.15 to 10.0 and moves `p` inversely by almost exactly the offsetting amount. The trade runs along the zero line, as the identity predicts.
5. **A powered counter-outcome exists but does not route.** 129 powered cells have a gross mean whose CI excludes zero, all negative. Flipping the side gives at most **+12.9 bps gross** — below even the *partial* cost floor of 13.1-16.1 bps. Zero flipped cells clear it.
6. **One live thread survives its control: shock-conditioned MOMO.** Live +22.6 bps against a magnitude-matched comparator at percentile 0.95 (one-sided p = 0.05), n = 505 rows. The only place in the run where a live effect exceeds the partial cost floor *and* survives the M-3 control. Single cell, borderline, underpowered. The one thread I would not close.
7. **Two integrity items need an operator ruling before this emission is treated as clean.** `TRIPWIRE-2` (declared HARD, and half of the design's causality claim) **was never run and is absent from the self-check**, and `Determinism` was silently downgraded from HARD to INFORMATIVE and not executed. `screen.md` §9 says "Deviations: none". §1 sets out the mitigating evidence.

---

## 1. Phase 0 — Integrity gate

The SPDR lane exempts screens from `estimand_validation.json`; the integrity substitute is the code-asserted fence + causal-lag self-check. I audit that substitute against the design's own §12 checklist.

### 1.1 What the design declared HARD vs what ran

Design §12 HARD list: `TRIPWIRE-1`, **`TRIPWIRE-2`**, TRAIN fence, holdout, universe pin, identity reconstruction, parent parity, derangement fixed-point count, golden traces, **determinism**.

| Design §12 HARD item | In `integrity_selfcheck.json` | Severity emitted | Held | Analyst note |
|---|---|---|---|---|
| TRAIN fence (`max(exit_ts) < 2023-12-18Z`) | yes | HARD | ✅ | `max_ts` = 2023-11-21; well inside |
| Global holdout (≥ 2025-01-08) | yes | HARD | ✅ | `violations: {}` |
| cTrader fence sha256 | yes | HARD | ✅ | measured == `4cdc7b01dd47…6de0` |
| cTrader TRAIN fence + holdout | yes | HARD | ✅ | max_ts < `train_end` 2023-11-22 |
| Universe pin set-equality | yes | HARD | ✅ | 25 pinned == 25 recomputed, no extras/missing |
| Identity reconstruction | yes | HARD | ✅ | **independently re-derived, §2.1** |
| M-1 block-MDE provenance | yes | HARD | ✅ | iid column labelled companion-only on all 4 arms |
| No `pass` field / no `at_or_above_pXX` | yes | HARD | ✅ | `offending_columns: {}`; I confirm no `pass` column in any parquet |
| No local accounting primitive | yes | HARD | ✅ | cost from `xen.evaluation` overlay |
| Spread never charged | yes | HARD | ✅ | consistent with the disclosure block |
| Derangement fixed points == 0 | yes | HARD | ✅ | 0 for both controls, 2,000 seeds |
| TRIPWIRE-1 construction assertions | yes | HARD | ✅ | entry strictly after decision bar asserted per arm |
| Parent parity | yes | HARD | ✅ | **independently reviewed, §1.3** |
| Golden traces G1-G6 | yes | HARD | ✅ | computed self-check side from the fenced catalog, no arm module imported |
| Bootstrap speed path == `xen.evaluation.block_bootstrap_ci` | yes | HARD | ✅ | `abs_diff [1.4e-14, 0.0]`, block 3 |
| **TRIPWIRE-2 leaky-variant discrimination** | **ABSENT** | — | **NOT RUN** | **§1.2** |
| **Determinism (`--jobs` parallel == sequential)** | present | **INFORMATIVE** | **not evaluated** | detail: *"parallel-vs-sequential comparison not requested this run"*; run used `jobs=8` |
| M-2 span disclosure | present | INFORMATIVE | report layer | **18,990 of 22,044** horizon-carrying arm-C cells carry span disclosure — **3,054 (13.9%) do not** |
| TRIPWIRE-3 forward-path derangement | present ×2 | INFORMATIVE | report layer | collapse fractions 0.161 and 0.904, correctly not the causality claim |

`screen.md` §8 states "16 HARD checks, 0 failed". That is **literally accurate about what ran** — 16 HARD entries exist and none failed. It is **incomplete about what did not run**: two design-declared HARD items are missing or downgraded, and `screen.md` §9 records "Deviations: none".

### 1.2 TRIPWIRE-2 — the finding, and the mitigation

Design §7.1 is explicit that the causality claim rests on TRIPWIRE-1 **and** TRIPWIRE-2:

> *"A forward-path derangement is therefore a REPORT LAYER only and is explicitly NOT the causality claim, which rests on TRIPWIRE-1 and -2."*

TRIPWIRE-2 was to build a deliberately leaky twin (conditioner threshold computed over a window *including* the forward horizon) and show an orders-of-magnitude separation from the legal variant. No such artifact exists anywhere in `results/`. Half of the declared causality evidence is missing.

**Mitigating evidence (why I do not call the emission unanalysable):**

- This is a **re-scoring experiment**, not a new construction. Every arm re-runs its parent's already-QA'd panels. The causal construction is inherited, not rebuilt.
- **Parent parity is exact** (§1.3): max abs diff 4.5e-13 / 1.8e-12 / 9.1e-13 / 0.0 across arms A-D on the parents' own published cells. A substituted leaky variant would break parity.
- TRIPWIRE-1 (per-row index assertions, entry strictly after the decision bar, expanding statistics excluding the decision bar) held on all four arms.
- The direction of the headline result is negative-to-null. A look-ahead leak inflates edges; there is no inflated edge to explain away.

**Operator ruling requested.** (a) Accept the emission with TRIPWIRE-2 recorded as an un-run HARD check and parent parity standing in for it; or (b) require TRIPWIRE-2 built and run before the reflection consumes these numbers. **I recommend (a)**, with the gap recorded as an amendment to `screen.md` §9 rather than left as "Deviations: none". Determinism should be re-run cheaply either way (one sequential pass).

### 1.3 Parent parity — reviewed, not pasted

The anti-drift proof that no parent estimand was silently re-specified, and the single most load-bearing check in a re-scoring design. It is clean:

| Arm | Parent | Quantity | Cells compared | Max abs diff | Outside tol |
|---|---|---|---|---|---|
| A | SPDR-012 | `gap_high_low_bps` | 109 / 109 | 4.55e-13 | 0 |
| B | SPDR-013 | `expectancy_partial` | 2,940 / 2,940 | 1.82e-12 | 0 |
| B | SPDR-013 | `n_episodes` | 2,940 / 2,940 | 0.0 | 0 |
| C | SPDR-014 | `mean_r_h` | **6,127 / 8,450** | 9.09e-13 | 0 |
| C | SPDR-014 | `n_decided` | **6,127 / 8,450** | 0.0 | 0 |
| D | SPDR-015 | `hit_rate`, `n_oos` | 189 / 189 | 0.0 / 0 | 0 |

**Caveat the screen does not surface:** arm C compares only **6,127 of SPDR-014's 8,450 parent cells (72.5%)**. Arms A, B, D compare 100%. The 2,323 uncompared arm-C cells are not evidence of drift, but parity is the designated anti-drift proof and it is 27.5% incomplete on the arm carrying 22,194 of the 37,791 cells. A disclosure, not a failure.

### 1.4 Fences, holdout, price-primary

- TRAIN fence and both holdouts hold with margin. Zero rows at or after 2025-01-08 (Bybit) or 2024-12-13 (cTrader). I did not query the catalog; every number here comes from the emitted, already-fenced parquets.
- **Price-primary does not apply.** This is an SPDR screen, vectorised Python by design and by operator-signed lane rule; it makes no tradability claim, so no cTrader-primary requirement attaches. Stated so the absence is not read as a gap.
- **Unit pin verified:** `unit_pin.json` reports a *computed* pooled TRAIN median σ̂ = **73.0006 bps**, divisor object stated verbatim (LTF H1 Parkinson EWMA λ=0.94, 60-bar warm-up, causal ≤ t−1, horizon-scaled √h), **25 of 25 symbols measured**, `symbols_without_a_value: []`. L-21 compliant. bps is primary everywhere; the σ̂ column is labelled `POOLING_AID_ONLY`.

### 1.5 Minor artifact gaps

- `plots/` is **empty**. Design §10 budgets ≤8 plots and §15 lists the directory. None emitted.
- `run_summary.json`: `disposition: "NONE — this script takes no disposition"` (correct and welcome); `deviations: []` (the §1.2 item).

---

## 2. Verification of every headline number in `screen.md`

Each re-derived independently. Unless flagged, the screen is **confirmed exactly**.

### 2.1 The identity `p·W − (1−p)·L = mean` (design §12 HARD)

**Confirmed, with a definitional clarification the screen omits.**

The identity holds against `mean_signed_rows` (the mean over *non-flat* rows), not against `mean` (which includes rows with exactly zero return). Re-derived:

| Basis | Signed cells | max residual (bps) | p99 residual | cells > 0.01 bps |
|---|---|---|---|---|
| gross | 24,098 | **1.46e-11** | 2.3e-13 | 0 |
| net | 24,100 | **7.28e-12** | 2.3e-13 | 0 |

I also confirmed `p == n_pos/(n_pos+n_neg)` exactly (max diff 0.0), and re-derived `p_be`, `p_be_net` and `edge` from `W`, `L`, `cost` with max diff **0.0** against the emitted columns.

**Clarification for 019/020.** Because flat rows are excluded from `p`, the identity describes the mean *over non-flat legs*, whereas SoT §2's `E[gross per leg]` covers every leg. On the 1,413 powered cells the discrepancy is small — median `p_flat` 0.0104, `|mean − mean_signed_rows|` median 0.022 bps, p95 0.127, max 0.585. Grid-wide, 226 signed cells carry `p_flat > 0.05` (max 0.50). At the powered scale the leakage is immaterial (≤0.6 bps against a 13.5 bps floor), but a downstream budget built on `p·W−(1−p)·L` should charge flat legs their cost.

### 2.2 The `(p, W, L)` picture on the 1,413 powered signed cells

Every median below is my own recomputation.

| Term | Analyst | Screen | Diff |
|---|---|---|---|
| `p` | **0.3887** | 0.3887 | −0.0000 |
| `W` (bps) | **128.65** | 128.6 | +0.05 |
| `L` (bps) | **75.55** | 75.6 | −0.05 |
| `W/L` | **1.4844** | 1.484 | +0.0004 |
| `p_be` (gross) | **0.4025** | 0.4025 | +0.0000 |
| `p_be_net` | **0.4992** | 0.4992 | +0.0000 |
| gross mean (bps) | **−1.178** | −1.18 | +0.002 |
| net mean (bps) | **−15.157** | −15.16 | +0.004 |
| cost charged (bps) | **13.540** | 13.54 | +0.000 |
| `W/L > 1` share | **0.9993** | 0.999 | ✓ |
| above **gross** break-even | **459 / 1,413 = 0.3248** | 0.325 | ✓ |
| above **net** break-even | **0 / 1,413 = 0.0000** | 0.000 | ✓ |
| cost term `p_be_net − p_be` | **+0.0650** | +0.0650 | ✓ |
| rate term `p_be − p` | **+0.0067** | +0.0067 | ✓ |

**Two operator verification asks are settled:** the identity holds to ~1e-11 bps (claimed ~1e-12; true bound 1.46e-11, still eleven orders below the 0.01 bps tolerance), and "0 of 1,413 clear net break-even while 32.5% clear gross" reproduces exactly.

**One naming trap for anyone reading the parquet directly.** The column families are not what the prefixes suggest. `gross_*` holds the **gross-return** decomposition *with* the cost carried in `gross_p_be_net` — the correct SoT §2 object. `net_*` holds the decomposition of the **already-net** return series, so `net_cost_bps = 0` and `net_p_be_net == net_p_be` by construction. Reading `net_p_be_net` as "the net break-even" gives 0.4141 instead of the correct 0.4992. Every figure here uses the `gross_*` family for `(p, W, L, p_be, p_be_net, edge)`, as `screen.md` did.

### 2.3 Cell inventory and power counts

All exactly reproduced:

| Arm | Cells (analyst == screen) | At parent target precision |
|---|---|---|
| A — SPDR-012 residue | 3,047 | 1,923 |
| B — SPDR-013 residue | 5,110 | 879 |
| C — SPDR-014 residue | 22,194 | 632 |
| D — SPDR-015 residue | 7,440 | 4,620 |
| **Total** | **37,791** | 8,054 |
| cTrader replication (separate) | 42 | — |

Residue-item coverage reproduces item by item (A1 143 · A2 372 · A3 1,965 · A4 432 · A5 135 · B1 2,044 · B2 1,022 · B3 830 · B4 146 · B5 2,555 · C1 7,181 · C2 1,020 · C3 6,987 · C4 170 · C5 3,570 · C6 62 · C7 2,714 · C8 340 · C9 150 · D1 1,800 · D2 300 · D3 405 · D4 405 · D5 675 · D6 900 · D7 75 · D8 2,534). **Every design §2 item carries cells. Nothing was narrowed.**

**One correction.** `screen.md` §2 says *"**1,511 signed cells** now reach their parent's own declared target precision"*. The signed count is **1,413** (arm B 879 + arm C 534). The extra 98 are the `C9 DA-STRADDLE` cells at target — **characterisation-only, direction-agnostic, carrying no `(p, W, L)` layer at all** (they emit only `mean_partial_net_bps` / `median_partial_net_bps`). They are not signed cells. The screen's own §3 uses the correct 1,413. Recommend restating as "1,413 signed cells, plus 98 straddle characterisation cells".

### 2.4 The two items the screen author raised

**(a) B3 — the design's "125 positive-mean cells". The screen is right that it does not reconcile; I additionally identify what the 830 is and what the answer to B3 is.**

The 830 tagged cells are **exactly** the arm-B `per_symbol` cells on the DESIGN and CONFIRM bands whose **partial-net** mean is positive. I verified: all 830 have `net_mean > 0` *and* `gross_mean > 0`, decomposing as CONFIRM×H1 284 + CONFIRM×M15 194 + DESIGN×H1 187 + DESIGN×M15 165 = 830. That reproduces every screen cross-check: **352 DESIGN** (187+165 ✓), **187 DESIGN×H1** ✓, **471 H1 both bands** (284+187 ✓).

It is also *faithful to the design's own wording* — design §2 states B3 as "`expectancy_partial` mean > 0", and `expectancy_partial` is the partial-net object. The tag is correct; the design's count of 125 is wrong. I searched every constructible slice and **no slice yields 125 or anything near it**:

| Slice | n cells | gross mean > 0 | net mean > 0 |
|---|---|---|---|
| all arm-B signed | 5,110 | 2,243 | 1,397 |
| DESIGN | 1,330 | 576 | 368 |
| CONFIRM | 1,890 | 826 | 509 |
| DESIGN × H1 | 665 | 338 | **187** |
| H1 both bands | 1,610 | 801 | **491** |
| DESIGN × per_symbol | 1,190 | 514 | 352 |

Nearest values in the whole 18-cell (band × clock × basis) breakdown are 165, 187, 194 — nothing in the 120s. **My read: "125" is a transcription error in `design.md` §2, and the screen's superset-of-830 choice is the correct conservative response.** No cell was dropped.

**And the substantive answer to B3, which nobody has yet stated:** of those 830 positive-partial-net cells, **0 reach SPDR-013's own precision bar** (MDE ≤ 10 bps *and* ≥ 30 dates *and* thirds-stable); median realised `n` is 46 episodes over 28 dates. B3 is therefore **UNPOWERED at the per-symbol level, unchanged by the levers**. Per B-5 that is a power statement. Note the pooled counterparts of the same arms *are* powered (§9.1) and sit below break-even, so the pooled evidence speaks where the per-symbol cells cannot.

**(b) IN-5 — median/trimmed-mean CI coverage. The screen understates the gap by a factor of ~20, and the gap is material.**

IN-5 says median and trimmed-mean CIs were bootstrapped "on the levers-exhausted cells". There are **4,903** levers-exhausted cells. Those CIs are actually present on **240 of 24,098 signed cells (1.0%)** — and on only **4.0% of the 1,413 powered cells**. Coverage:

| Statistic | CI present on | share of signed cells |
|---|---|---|
| `gross_mean` / `net_mean` | 23,700 | 0.983 |
| `gross_p` | 23,700 | 0.983 |
| `gross_W` / `gross_L` | 23,426 / 23,527 | 0.972 / 0.976 |
| `gross_W_L`, `gross_edge` | 23,253 | 0.965 |
| **`gross_median`, `gross_trimmed_mean_10`** | **240** | **0.010** |
| **`net_median`, `net_trimmed_mean_10`** | **240** | **0.010** |

Design §6.1 is explicit: *"mean, median, **10% trimmed mean** — block-bootstrap CI on each — all three always co-reported (this family is fat-tailed; SPDR-013 saw mean −2 vs median −47 on the same cell)"*. The point statistics are emitted everywhere; the **uncertainty on two of the three is 99% absent.**

**This matters, because the three statistics disagree.** On the 1,413 powered cells:

| Statistic | median across powered cells (gross, bps) | (net, bps) |
|---|---|---|
| mean | **−1.18** | −15.16 |
| **median** | **−14.43** | **−28.44** |
| 10% trimmed mean | **−11.67** | −25.38 |

Sign agreement mean-vs-median **0.678**; mean-vs-trimmed **0.703**.

The mean is the correct object for the identity (the identity is a mean identity and cannot be restated on medians). But the *narrative* "the cells sit essentially at gross break-even, only the cost floor separates them" is the **most favourable of the three point statistics by 13 bps**. On the median, the typical powered cell is 14 bps below zero *before* any cost. That is a right-skewed distribution where a minority of large wins pulls the mean to near zero — exactly the L-49 / SPDR-013 pattern the design anticipated, and it is under-quantified because 99% of those medians have no CI. **Recommend: bootstrap median and trimmed-mean CIs on at least the 1,413 powered cells before 019/020 parameterise anything off the mean.**

---

## 3. Question 1 — the power / resolvability ledger, per 017 open item

`NOT_RESOLVABLE` per `not_resolvable.json`: **3,559 cells**, median shortfall **7.87×**, p90 **27.30×** — the screen's 3,559 / 7.9× / 27.3× reproduces exactly. Concentration: C3 1,946 · C5 914 · C2 263 · C1 105 · C4 105 · D3 74 · D4 63 · C6 35 · rest ≤17.

A definitional note: three populations are labelled around non-resolvability and are **not** the same object — `levers_exhausted == True` (4,903, meaning "all §5 levers were applied"), `band_label_mean == NOT_RESOLVABLE` (3,404), `band_label_edge == NOT_RESOLVABLE` (2,641), and the JSON's 3,559. 376 cells carry `levers_exhausted == True` *and* `at_parent_target_precision == True` — fully-levered pooled/TRAIN cells that **did** reach target, so the flag reads "levers applied", not "levers failed". Correct behaviour, confusing naming. The JSON is the authoritative object.

### Arm A — SPDR-012 residue

| Item | Status | Answer, with magnitude and CI |
|---|---|---|
| **A1 V-REGIME-HMM** | **RESOLVED** (99/143 at target) | The HIGH−LOW next-\|move\| gap is a large, positive, CI-excluding-zero magnitude on **every clock and every band**. Pooled full TRAIN: **D1 +180.4 bps [119.7, 252.1]**, **H4 +67.5 [54.7, 80.6]**, **H1 +48.0 [41.7, 54.7]**. The 017 status "76/83 cells UNPOWERED" is overturned by pooling + full span. **Per symbol** (binding stratum, L-03): H1 median gap **+24.7 bps**, **97.3% of per-symbol cells CI-excluding-zero positive** (DESIGN 100%); H4 median **+45.4**, 86.5%; D1 median **+76.8** but only 24.3% (D1 remains thin). **Heterogeneity low on H1/H4, high on D1.** |
| | | **Correction to the screen.** `screen.md` §4 quotes only the larger of two emitted HMM variant sets. A second pooled variant set exists in the same emission with materially smaller gaps: **D1 +100.1 [47.9, 156.4]**, **H4 +34.3 [20.0, 48.4]**, **H1 +18.1 [13.6, 23.1]**. Both are SUPPORTED; the honest range for the H1 pooled gap is **+18 to +48 bps**, not "+48.0". |
| **A2 V-TAIL at D1** | **RESOLVED as a WASH-magnitude** (212/372 at target) | p90/p95 exceedance-rate differences are **small, positive, precisely measured**: H1 median **+0.056** (p90) / **+0.031** (p95), **90.9% of per-symbol cells CI-excluding-zero**; D1 median **+0.040** / **+0.022**, only 4.5% / 0.0%. Every cell lands WASH because the magnitude is below the band threshold, not because it is unmeasured. **Quantified not qualified: the tail-exceedance lift is real on H1 at ~5 percentage points of exceedance rate; not resolvable on D1.** |
| **A3 DESIGN-band deficit** | **RESOLVED — "the DESIGN band cannot support the claim, but pooling can"** | Per-symbol DESIGN cells run at median **99-102 dates** vs the 225 §6.3 demands; only **6.2%** reach 225; median shortfall **123-127 dates**. Exactly the predeclared outcome (design §9). But **pooled** DESIGN cells reach **327-330 dates (85.7% ≥ 225)**, and CONFIRM/TRAIN per-symbol cells reach 285-394 dates (87-95% ≥ 225). Two-part answer: per-symbol DESIGN is `NOT_RESOLVABLE` by catalog history; pooled DESIGN is resolved. |
| **A4 V-CLOCK at D1** | **RESOLVED — an estimator statement, not a market statement** | D1 cells run at **exactly 1.000 observations per date** against 6-9 dummies. Median incremental R²: D1 **−0.032 to −0.050**, H1 **−0.0004 to −0.003**, H4 **−0.001 to −0.015**. Session-only on D1 is exactly 0.000 in all 48 cells. Labels overwhelmingly WASH/UNPOWERED with a **CONTRADICTED** minority (94 cells grid-wide). **Measured incremental value of calendar dummies over V-LEVEL is zero to slightly negative everywhere it is measurable.** Consistent with SoT §3.2's "do not use: calendar/session features". |
| **A5 §6.4 clause + calendar thirds** | **FULLY RESOLVED — a clean reversal of the 017 status** | All **135 of 135** cells now have `thirds_populated == 3`, `clause_satisfiable == True`, `thirds_sign_agree == 3`. 017 recorded "42/45 cells have only one powered third; the first third precedes the catalog". On the full TRAIN span the clause is satisfiable everywhere and the sign agrees in all three thirds in every cell. **The cleanest single resolution in the run.** |
| **A IC cells** (apparatus) | RESOLVED | H1 per-symbol median rank IC **0.3262**, **100% of 165 cells CI-excluding-zero**, all SUPPORTED, all three bands. H4 **0.288** CONFIRM / 0.197 DESIGN. D1 DESIGN weak (**0.087**, 14.5%). Pooled H1 IC **0.421-0.434**. Replicates and slightly exceeds SoT §3.2's banked "rank IC 0.338 / 0.301". |

### Arm B — SPDR-013 residue

| Item | Status | Answer |
|---|---|---|
| **B1 `stop`-only / `trail`-only** | **NOT_RESOLVABLE as predeclared, mechanism now quantified** | 0 of 2,044 at target. But now **measured**: `stop`-only at **`p` 0.067, `W/L` 10.05, gross mean −37.9 bps**; `trail`-only at **`p` 0.870, `W/L` 0.150, gross mean −7.0 bps**. One-tail estimators by construction, exactly as design §9 predicted; pooling did not fix them. **Their value is not as expectancy cells but as the `W/L` movability evidence in §5.** |
| **B2 unpowered `time`-arm cells** | **NOT_RESOLVABLE** | 0 of 1,022 at target; median n 108 episodes over 108 dates. The `time` arm sits at `p` **0.4923**, `W/L` **0.9993**, gross mean **−7.50 bps** — almost exactly the symmetric-payoff coin-flip the martingale argument predicts, which is itself informative. |
| **B3 the positive-mean cells** | **UNPOWERED (830, not 125)** | §2.4(a). 0 of 830 at target; median 46 episodes / 28 dates. |
| **B4 ZZ structural leg per symbol** | **PARTIALLY RESOLVED** (30/146) | Powered D-ZZ: `p` **0.3475**, `W` 152.5, `L` 83.1, `W/L` **1.804**, `p_be` 0.3567, `p_be_net` **0.4112**, gross **−2.82 bps**, net **−16.74**, gross edge **−0.067**. 017 called it "UNPOWERED via MDE, not trade count" — now resolved for 30 cells, below both break-evens. |
| **B5 M15 arms** | **LARGELY RESOLVED** (736/2,555 — largest powered block in arm B) | M15: `p` **0.3358**, `W/L` **1.841**, `p_be_net` **0.4385**, gross **−1.98**, net **−15.30**, edge **−0.102**. H1: `p` 0.3372, `W/L` 1.961, `p_be_net` 0.4135, gross **−0.13**, net −14.11, edge **−0.069**. **H1 is materially closer to gross break-even than M15** (−0.13 vs −1.98) — a real measured clock effect of ~1.9 bps, ~7× smaller than the cost floor. |

### Arm C — SPDR-014 residue (the hardest arm)

| Item | Status | Answer |
|---|---|---|
| **C1 the residual object** | **PARTIALLY RESOLVED — the headline reversal** | **121 of 7,181** at target, against SPDR-014's **0 of 927**. Powered C1: median block MDE **7.87 bps** (parent quoted 20 / 172 / 796 against a ≤10 floor). Median gross mean **−0.30 bps**; 1 of 121 has a CI excluding zero. Grid-wide C1 median block MDE is still 103 bps at median n=77 — **105 C1 cells formally NOT_RESOLVABLE**. |
| **C2 shock-conditioned MOMO** | **UNPOWERED in the grid; the one live control signal** | 65 of 1,020 at target; **263 NOT_RESOLVABLE**. Powered C2: `p` 0.4695, `W/L` 1.124, gross mean **−0.32 bps**. **But** 622 of 2,040 shock_flag cells have a gross mean above their cost floor and 22 have a gross-mean CI-low above it — none at target precision. The M-3 control result (§7.2) is where this item's real content is. |
| **C3 ordered `last_k` vol-flip** | **NOT_RESOLVABLE, decisively** | 127 of 6,987 at target; **1,946 NOT_RESOLVABLE — 55% of the entire NOT_RESOLVABLE population.** Median n 102 events. Powered C3: `p` 0.4668, `W/L` 1.140, gross mean **+0.34 bps** (the only positive item-level gross median in arm C). The 017 "thin strata" concern is confirmed as the binding constraint; pooling + σ̂ did not close it in the registered event-nested form. |
| **C4 E-TOUCH / E-CLOSE asymmetry** | **PARTIALLY RESOLVED** | 33 of 170 at target (105 NOT_RESOLVABLE). Powered: `p` 0.4672, `W/L` 1.132, gross **−0.17 bps**. Measured asymmetry across the grid: E-CLOSE **−1.2 to −3.0 bps**, E-HORIZON **−0.03 to +0.69**, E-TOUCH ×P-NONE **+0.6 to +1.5**. **A real ~3-4 bps ordering E-TOUCH > E-HORIZON > E-CLOSE — below the cost floor, but genuine measured structure.** |
| **C5 magnitude scaling** | **PARTIALLY RESOLVED** | 174 of 3,570 at target; **914 NOT_RESOLVABLE**. The registered claim was "magnitude strata lift residual **magnitude** while the rate stays ≈0.50". **That is what the data shows.** Across `mag_high` / `shock` / `vol_tercile` the rate is pinned in **0.4147-0.4795** while `W` ranges **109.5 → 235.4 bps** and `L` **94.7 → 171.1 bps**. `W` and `L` scale **together** — `W/L` only moves 1.10 → 1.40. **Selection scales both sides of the identity, so it scales a near-zero, exactly as SoT §3.1 warned.** |
| **C6 z / h dose-response** | **RESOLVED** (14/62 at target; all 62 levers-exhausted, 35 NOT_RESOLVABLE) | Monotone and measurable: **z=1.0, h=4** gross **+1.15 bps** (`p` 0.4761, `W/L` 1.116); **z=1.0, h=12** **+2.86** (`p` 0.4999, `W/L` 1.025); **z=1.5, h=12** **−1.43** (`p` 0.4167, `W/L` 1.303); **z=2.0, h=4** **−0.52**. **Shape: longer hold at low z pushes `p` toward 0.50 and `W/L` toward 1.0; higher z pushes `p` down and `W/L` up — they move against each other and the mean stays within ±3 bps of zero.** |
| **C7 DESIGN→CONFIRM sign flip** | **RESOLVED — overturns the 017 concern** | §4. |
| **C8 pooled rate lean** | **RESOLVED — the two weightings now agree** | Row-weighted `p_momo` median **0.4676**, symbol-weighted **0.4699** (screen ✓). Across 340 cells they differ by median **0.0023**. Per-symbol lean: median 5 momo-leaning vs 11 MR-leaning of ~16-22 symbols. **The 017 "two weightings disagree" concern dissolves: they agree to 0.002 at this n. The measured lean is toward mean-reversion, ~0.47 against a 0.50 reference, on both weightings.** |
| **C9 `DA-STRADDLE`** | **CHARACTERISATION ONLY** (98/150 at target) | Median per-cell **mean** partial-net **−29.07 bps**; median per-cell **median** partial-net **−30.0 bps**. `screen.md` §4 labels −29.1 as the "median partial-net" — it is the median of the per-cell *means*; the median-of-medians is −30.0. Trivial, corrected for exactness. **No strategy framing, no policy, no graduation path** (SoT §0 operator exception). |

### Arm D — SPDR-015 residue

| Item | Status | Answer |
|---|---|---|
| **D1 `trans_up`/`trans_dn`** | **RESOLVED on H1, partially on H4** | The <50 rule is cleared on H1: median `n_trans` **624.5 (up) / 400 (dn)** CONFIRM, **1,032 / 635** TRAIN, **94.7% / 92.7% of cells ≥ 50**. H4 CONFIRM 82.0% / 76.7%; **H4 DESIGN is the residual gap at 54.7% / 52.7% (median n_trans 65.5 / 60.5)**. 1,398 of 1,800 at target. The 017 "n_trans < 50" blocker is gone on H1 and mostly gone on H4-CONFIRM. |
| **D2 run-length MAE** | **RESOLVED as a disclosure, 0 at target** | H1 median MAE **11.95-12.00 bars** against a predicted run length `E[run]` of **18.9-23.1 bars**; H4 MAE **10.9-11.3** vs `E[run]` 17.8-21.1. **The predictor's typical error is roughly half the quantity it predicts.** No target rule was defined for this item, so 0/300 at target is a definitional gap, not a power failure. |
| **D3 T-GT-MED10** | **RESOLVED with magnitudes; mixed as registered** | Lift over base rate, median by model: `ridge_cont` **+0.063** (CONFIRM) / +0.064 (TRAIN), `ar1_threshold` **+0.048**, `logit_ridge` **+0.058** / +0.042. Labels TRAIN: `ridge_cont` 16 SUPPORTED / 5 NR / 5 WASH; `logit_ridge` 11 WASH / 8 NR / 7 SUPPORTED. **017's "12/21 SUPPORTED → INCONCLUSIVE" is now a measured +5 to +6 percentage-point lift with model-dependent resolvability.** 74 cells NOT_RESOLVABLE. |
| **D4 T-GT-MED5** | **RESOLVED with magnitudes** | Lift median: `ridge_cont` **+0.107** (CONFIRM) / +0.102 (TRAIN) / +0.096 (DESIGN), `ar1_threshold` **+0.077 to +0.087**, `logit_ridge` **+0.022 to +0.059**. **`ridge_cont` at K=5 is the strongest D3/D4 cell: hit 0.585 vs base 0.483, 21 of 26 SUPPORTED on CONFIRM.** The "2 unexamined failures" from 017 are now visible as the `logit_ridge` DESIGN cells (+0.022, 14 of 17 UNPOWERED). 63 cells NOT_RESOLVABLE. |
| **D5 2a H4 k=1** | **RESOLVED — "k=1 is inert"** | ΔBrier vs **persistence** (negative = improvement), R-MARKOV H4 **k=1**: median **0.0000** (CONFIRM and DESIGN), **−0.00049** (TRAIN); 33-47% of cells CI-excluding-zero. 017's "6/16 SUPPORTED, median ≈ +0.0002" reproduces as **no improvement at k=1**. **But the same model at k=4 and k=12 is a different object**: H1 TRAIN **−0.0199 (k=4)** and **−0.1085 (k=12)**, 57-59% of cells CI-excluding-zero — reproducing SoT §3.2's banked R-MARKOV k=4/12 (−0.025 / −0.114) to within 0.006. **D5's answer: the k=1 next-bar gate is inert; the k=4/12 gate is not, and the banked result replicates.** Consistent with SoT §3.2's "do not use k=1 as a gate". |
| **D6 R-HMM-RV** | **RESOLVED — weak but non-zero** | H1: k=1 **−0.00135**, k=4 **−0.00595**, k=12 **−0.0317**; 36-47% CI-excluding-zero. H4 weaker (17-32%). **Roughly one third the effect of R-MARKOV at matched k, with about two thirds the cell-level resolvability.** Consistent with 017's "3/15 and 7/15" and SoT §3.2's "do not use R-HMM-RV as a forecaster". |
| **D7 D1 stickiness** | **RESOLVED — now scored, was disclosure-only** | `p_stay` median **0.9486** (CONFIRM, median n 266) / **0.9376** (DESIGN, n 129) / **0.9365** (TRAIN, n 395); range 0.866-1.000; 22 of 25 SUPPORTED on CONFIRM and TRAIN. **Daily level-regimes are extremely sticky — ~94% persistence — the direct mechanical explanation for D1's rare-transition problem.** 23 cells NOT_RESOLVABLE. |
| **D8 the CONFIRM verify slice** | **FULLY RESOLVED — the never-scored item is now scored** | 2,534 cells, **1,800 flagged `never_scored_before`**. Pooled `T-GT-CUR` on **CONFIRM**: `ar1_threshold` **0.6465 [0.6247, 0.6678]**, `logit_ridge` **0.6999 [0.6831, 0.7176]**, `ridge_cont` **0.6781 [0.6589, 0.6978]**, base rate **0.4674**, n = 5,698. On DESIGN: 0.6637 / 0.6874 / 0.6686, base 0.4781, n = 3,455. **Every screen-quoted figure verified to 4 decimals.** All three CONFIRM CIs sit ~16-23 points above the base rate and do not approach it. **The CONFIRM slice reproduces DESIGN. T-GT-CUR is the most robust positive object in the entire run.** |

---

## 4. C7 — is the DESIGN→CONFIRM sign flip distinguishable from noise?

**Answer: no, and the direction of the finding reverses the 017 concern.**

Verified: **2,714 pairs**, **44.14% flip sign** (screen 44.1% ✓), of those flipped **91.82% have overlapping band CIs** (screen 91.8% ✓). Three additional facts the screen does not report, which change the reading:

1. **The flip rate is *below* a coin flip, not above it.** Two independent pure-noise band estimates flip 50% of the time. Observed **0.4414** — signs **agree** in 55.9% of pairs. Naive binomial z = **−6.10**. The pairs share symbols and events so the true uncertainty is larger and true |z| smaller; I quote the naive figure only as an upper bound on the evidence. Whatever this is, it is **more sign-stable than noise**, not less.
2. **The flips are overwhelmingly inside the measurement error.** Only **6.63% of all 2,714 pairs**, and **12.94% of the flipped pairs**, show a DESIGN→CONFIRM change exceeding the two-band pooled block MDE. For ~87% of flipped pairs the change is not distinguishable from zero at the realised n.
3. **The apparent band reversal is a weighting artifact.** Equal-cell-weighted, DESIGN mean **−1.65 bps**, CONFIRM **−19.77 bps** — a large apparent shift. **`n`-weighted**: **DESIGN −13.72 bps**, **CONFIRM −13.39 bps** — a difference of **0.33 bps**. The equal-weight gap is driven by thin cells (median DESIGN n = 41, CONFIRM n = 111; 5th-percentile n = 2 and 3). Checkpoint-017's "pooled +11.3 → −4.3" does not reproduce at SPDR-018's n under either weighting; both bands are negative and, weighted by evidence, essentially identical.

**Resolution of C7:** the DESIGN→CONFIRM instability that worried 017 is **not present at this `n`**. The two bands agree to 0.3 bps when weighted by information content, the sign is more stable than chance, and the residual flipping is measurement noise on thin cells. A genuine resolution; record it as one.

---

## 5. Question 3 (decisive) — is `W/L` a real handle, or the arithmetic mirror of `p`?

This determines whether the capture branch (`SPDR-019/020`) has anything to pull on. Tested three ways rather than asserted.

**The test.** From the identity, `mean = (1−p)·L·(R − 1)` where `R = p·W / ((1−p)·L)`. So `R = 1` exactly when `mean = 0`, and on a driftless path with a fixed-horizon exit `W/L` is **fully determined** by `p`: `W/L = (1−p)/p`. If `W/L` is a free degree of freedom, it must deviate from that mirror by more than the measurement error.

### 5.1 Variance decomposition — the mirror explains 97% of `W/L`

On the 1,413 powered cells:

```
OLS   log(W/L) = -0.0048 + 0.9408 * log((1-p)/p)      r = 0.9832   R² = 0.9667
                 ^ mirror predicts intercept 0, slope 1, R² 1

sd log(W/L)        = 0.3783
sd log((1-p)/p)    = 0.3953
sd log(R)          = 0.0729     <-- the FREE component
free share of W/L variation (sd ratio) = 0.193
```

Intercept −0.005 (mirror predicts 0), slope 0.941 (mirror predicts 1). **96.7% of the variance in log payoff asymmetry is the arithmetic mirror of the rate.** The free component has sd 0.073 in log units — about **7% multiplicative wiggle** around a quantity that ranges over a factor of ~3.

### 5.2 How far is the identity from the zero line?

`R` on powered cells: median **0.970**, 5th-95th **[0.854, 1.082]**, min 0.647, max 1.222. **50.8% of powered cells have `|log R| < 0.05`** — the mean is within 5% of the exact zero line. Median `|gross mean| / W` = **0.0164**: the typical powered cell's mean is under 2% of its own mean win size.

Per-cell significance: **130 of 1,413 (9.20%)** powered cells have a gross-mean block CI excluding zero. At a nominal 95% CI you would expect roughly 5% by construction; 9.2% is a mild excess and, as §6 shows, it is almost entirely on one side.

### 5.3 The movability test — does exit geometry actually move `W/L`?

The part that speaks to *movability* rather than accounting, possible only because arm B carries five exit modes on the same underlying signal. Across all 5,045 arm-B signed cells:

| exit_mode | n cells | `p` | `W/L` | mirror `(1−p)/p` | median log`R` | gross mean (bps) |
|---|---|---|---|---|---|---|
| `trail` | 987 | **0.870** | **0.150** | 0.149 | −0.052 | −6.98 |
| `time` | 1,022 | **0.492** | **0.999** | 1.031 | −0.032 | −7.50 |
| `combined` | 1,022 | 0.374 | 1.650 | 1.676 | −0.027 | −1.08 |
| `signalflip` | 1,022 | 0.333 | 2.062 | 2.000 | −0.025 | −0.99 |
| `stop` | 992 | **0.067** | **10.046** | 13.85 | **−0.306** | **−37.91** |

**Read this carefully — it answers the question in both directions.**

- **`W/L` is enormously movable.** Exit geometry drives it from **0.150 to 10.05 — a factor of 67.** Capture devices unambiguously control payoff asymmetry. Anyone claiming `W/L` was fixed would be wrong.
- **`p` moves inversely by almost exactly the offsetting amount.** The `mirror` column tracks the `W/L` column across the whole range. The gross mean does **not** improve as `W/L` rises; it is −0.99 bps at `W/L` 2.06 and **−37.9 bps at `W/L` 10.05**. The most aggressive asymmetry is the **worst** cell.
- **The free component (log `R`) is small and uniformly negative.** −0.025 to −0.052 for four of five modes; **−0.306 for `stop`**. The one exit mode that moves `W/L` furthest moves the cell furthest *below* the zero line — consistent with a stop paying the adverse-selection cost of the tail it truncates.

On the powered subset (`combined` and `signalflip`, the two modes reaching target precision), residual `log R` is **−0.052** vs **−0.063** — a difference of 0.011 log units, ~1 percentage point of payoff asymmetry, on cells whose gross means are −1.50 and −2.02 bps.

### 5.4 The per-cell CI test

For each powered cell I asked whether its own `W/L` block-bootstrap CI **excludes** the driftless mirror value `(1−p)/p`. **It does not, in 1,170 of 1,413 cells (82.8%).** For more than four cells in five, the data cannot distinguish the measured `W/L` from the value the rate alone forces.

### 5.5 Answer to Question 3

> **`W/L` is a real, large, and directly controllable quantity — and it is not a free degree of freedom.** It is 96.7% determined by `p` on the powered cells; exit geometry moves it by a factor of 67 while moving `p` inversely by almost exactly the offsetting amount; the free residual has sd 7% in log units and is uniformly negative; and for 82.8% of powered cells the `W/L` CI cannot be separated from the driftless mirror at all.
>
> This is the L-49 / SoT §1 martingale statement **measured rather than argued**: a path-dependent exit trades `p` against `W/L` along the zero line, and every measured deviation from that line in this dataset is negative. The largest deviation belongs to the most aggressive exit device.
>
> **`W/L > 1` in 99.9% of powered cells is therefore the arithmetic mirror of `p < 0.5`, not an independent finding.** The capture branch as registered has a lever, but on this evidence the lever does not have a positive direction.

**Caveat that keeps this honest.** SPDR-018 measured `W/L` under the *parents'* exit geometries, not under a designed capture policy. It shows the five geometries present in the data all sit on the zero line. It cannot rule out that some geometry outside this grid sits off it. What it does do is raise the bar: any 019/020 proposal must now say **which mechanism** puts `R` above 1, because five distinct exit devices spanning a 67× range of `W/L` did not.

---

## 6. Question 4 — does anything survive at power in the direction *opposite* to registration?

SoT §10 end-state 3 makes a powered counter-outcome a **routing** finding, not a null. Looked for explicitly.

### 6.1 What is there

**130 of 1,413** powered signed cells have a gross-mean block CI excluding zero. **129 negative; 1 positive.**

On signed direction cells, a powered negative mean **is** a powered directional statement: the registered side reliably loses. A genuine counter-outcome, reported as a magnitude, not qualified away.

| Over the 129 counter-direction cells | Value |
|---|---|
| median gross mean | **−4.12 bps** |
| **max** \|gross mean\| | **12.93 bps** (DOGEUSDT, CONFIRM, H1, `signalflip`, D-SMA14_angle-on, n=1,074) |
| median n | 4,420 rows |
| median cost floor charged | 13.20 bps |

### 6.2 Does it route?

**No — and by a clear margin.** If a counter-design simply flipped the side on these same cells:

| Test | Result |
|---|---|
| cells whose flipped **gross** mean exceeds their **partial** cost floor | **0 of 129** |
| cells whose flipped gross-mean CI-low exceeds the partial floor | **0 of 129** |
| best flipped gross | **+12.93 bps** vs a floor of 13.1-16.0 bps |
| best flipped **net** | **−0.65 bps** |
| median flipped net | **−9.18 bps** |

**Not one cell clears even the partial cost floor when flipped — and the true floor is higher, because spread is not charged.** The single best case misses by 0.65 bps *before* spread.

Where they sit: 89 in arm B `B5` (M15 arms, per-symbol and full-TRAIN), 26 in arm B pooled, 4 in `B-carried`, 10 arm-C pooled σ̂-normalised (C1 1, C2 2, C3 4, C5 3).

### 6.3 The positive tail is depleted, which is itself informative

Only **1** powered cell has a positive CI-excluding-zero mean: `MATICUSDT · M15 · CONFIRM · D-ZZ · signalflip`, gross **+8.24 bps [0.12, 17.00]**, n = 1,419, cost 13.62 → **net −5.38 bps**. Its CI-low is 0.12 — it barely clears.

Under a pure-null process with nominal 95% CIs on 1,413 cells you would expect roughly 35 in each tail. Observed: **1 positive, 129 negative.** Per L-34, counting only the desired tail against zero would be the error; counting both tails against the null expectation is the correct read, and it says the **positive tail is depleted well below chance while the negative tail is enriched ~3.7×**. (Cells are correlated, so the null expectation is not exactly 35; the asymmetry between the tails is the robust part.)

### 6.4 Answer to Question 4

> **A powered counter-outcome exists and is large in cell-count terms (129 cells, median −4.1 bps gross, up to −12.9 bps), but it does not route.** Flipping the side on the best of them yields +12.9 bps gross against a partial floor of 13.1 bps and a true floor that is higher. SoT §10 end-state 3 is **not** satisfied at this cost floor.
>
> It is nonetheless a **positive quantification** and must not be filed as a null: the registered side of these arms loses reliably, at power, on 129 cells — a measured directional fact about the signal, consistent with the C8 mean-reversion lean (`p_momo` ≈ 0.468-0.470) measured independently on arm C.

---

## 7. Question 6 — are the controls informative? What each can and cannot separate

Per L-32/INFR-016 these are report layers. Per M-5 collapse fraction is disclosure only. The usable objects are the percentile and the null distribution — plus, critically, **the plant curve, which states what the control could have detected**. Every control read against its own resolution.

### 7.1 SIDE-DERANGEMENT (2,000 seeds, 0 fixed points, L-28 compliant)

| | Arm B | Arm C |
|---|---|---|
| live effect | **−1.302 bps** | **−12.221 bps** |
| null mean (sd) | −0.277 (9.325) | −1.324 (4.620) |
| null quantiles (5/25/50/75/95) | −16.6 / −7.5 / −0.74 / +7.1 / +17.2 | −10.5 / −4.5 / −1.29 / +1.7 / +7.7 |
| **percentile** | **0.475** | **0.0065** |
| one-sided p | 0.475 | 0.0065 |
| collapse fraction (disclosure only) | 0.787 | 0.892 |
| n rows | 9,693 (1 singleton-group row excluded, disclosed) | 6,861 |
| plant curve {5,10,20,40} bps → percentile | {0.695, 0.875, **1.000**, 1.000} | {0.085, 0.400, **0.965**, 1.000} |

**What arm B's control can and cannot separate.** The plant curve says the control reliably detects a 20 bps side-attributable effect and only partly detects 10 bps. The live value sits at percentile 0.475 — dead centre of the deranged null. **Correct statement: arm B's side labels carry no side-attributable effect larger than roughly 10-20 bps; a smaller effect would be invisible to this control.** A resolution statement, not "no effect".

**Arm C's control is the informative one.** Live −12.22 bps at percentile **0.0065** — about 2.4 null sd below the deranged null mean. **The sides in arm C's primary cell (Z-VOL, z=1.5, H=12, E-TOUCH, h=12) carry real directional information, and it points the wrong way.** Note the plant-curve asymmetry: a +10 bps plant is *not* resolved (percentile 0.40) while the live −12.2 *is* (0.0065) — because the null is tight (sd 4.62) and the live value is far into its lower tail. This is the second independent line of evidence for the §6 counter-outcome, and the strongest single control result in the run.

### 7.2 MAGNITUDE-MATCHED COMPARATOR (M-3, 2,000 seeds, decile-stratified, live rows ±1 bar excluded)

M-3 exists to answer one question: is the effect **the volatility state**, or merely **"this was a big bar"**? Both conditioners had a genuine disjoint pool in every decile (`deciles_with_no_comparator_supply: []`), so the control is non-vacuous — I verified the decile supply table directly (live 50-51 vs pool 178-933 per decile for `shock_flag`; live 140-141 vs pool 299-933 for `mag_high`).

**`mag_high` — the comparator reproduces the effect.**

| | value |
|---|---|
| live effect | **−11.607 bps** |
| null mean (sd) | **−10.704** (9.237) |
| percentile | **0.46** |
| n live / pool | 1,404 / 5,457 |
| plant curve {5,10,20,40} → percentile | {0.64, 0.82, 0.98, 1.00} |

Live minus comparator = **0.90 bps**. The magnitude-matched comparator reproduces essentially the entire `mag_high` effect. **Conclusion: on this cell, `mag_high` is "the decision bar was large", not "the volatility state".** The control's own resolution is ~15-20 bps (a 10 bps plant only reaches 0.82), so it cannot rule out a state effect smaller than ~15 bps — but it decisively rules out the state explaining the −11.6 bps that is there.

**`shock_flag` — the comparator does *not* reproduce the effect. This is the one live thread.**

| | value |
|---|---|
| live effect | **+22.569 bps** |
| null mean (sd) | **−14.516** (22.352) |
| null quantiles (5/25/50/75/95) | −59.2 / −29.8 / −14.4 / +0.26 / +28.9 |
| **percentile** | **0.95** |
| one-sided p | **0.05** |
| collapse fraction (disclosure only) | 1.643 |
| n live / pool | **505** / 6,356 |
| plant curve {5,10,20,40} → percentile | {0.985, 0.99, 1.00, 1.00} |

Live minus comparator mean = **+37.1 bps ≈ 1.66 null sd**. The live effect **+22.6 bps also exceeds the partial cost floor** (15.3 bps on this cell class) — the only place in the run where that is true of a control-surviving effect.

**What this can and cannot support.** It **can** support: shock-conditioned MOMO produces a positive residual that magnitude-matched bars *without* the state do not reproduce, at one-sided p = 0.05. It **cannot** support more, and four caveats bind hard:

1. **n_live = 505 rows.** One control cell, not a powered grid stratum. In the 2,040 `shock_flag` grid cells, **0 of the 65 at target precision** show anything comparable — the powered `shock_flag` cells have a median gross mean of **−0.32 bps**.
2. **Percentile 0.95 is exactly the boundary**, with a null sd of 22.35 bps — an enormous null.
3. **Multiplicity.** 37,791 cells were emitted. One control at p = 0.05 is not evidence proportional to that grid, and per L-34 the correct comparison is against the realised multiple-testing process, not against zero.
4. Spread is not charged, so "+22.6 vs a 15.3 floor" overstates the margin by an unknown amount.

**Recommendation: this is the one thread I would not close.** It is the only object in SPDR-018 simultaneously (a) above the partial cost floor, (b) surviving an M-3 magnitude-matched control, and (c) in the *registered* direction. Not a finding; a lead worth a targeted powering attempt with `n` raised into the thousands (§14 P1).

### 7.3 AMBIENT-BASE (the base-conditional obligation, spdr-lane)

Per the lane's binding directive this is **not** a lift-vs-baseline read; a measured distributional shift on a null base is a positive quantification reported as a magnitude.

**Arm B** (n_live 9,694 vs n_ambient 327,884):

| Quantity | live | ambient | **Δ (the finding)** |
|---|---|---|---|
| mean (bps) | −1.332 [−25.23, +24.99] | −12.463 [−26.28, +2.98] | **+11.13** |
| median (bps) | −98.02 | −48.68 | **−49.34** |
| `p` | 0.3512 [0.3332, 0.3699] | 0.3090 | **+0.0423** |
| `W` (bps) | 481.2 [422.9, 547.3] | 351.0 | **+130.2** |
| `L` (bps) | 262.6 [241.1, 286.1] | 175.0 | **+87.6** |
| `W/L` | 1.833 [1.640, 2.063] | 2.006 | **−0.174** |
| dispersion (IQR, bps) | — | — | **+202.3** |

**The arm-B conditioning event produces a large, measurable distributional shift:** the rate rises 4.2 points, both `W` and `L` inflate by ~37% and ~50%, dispersion widens by 202 bps IQR, and the mean moves +11.1 bps. **`W/L` moves *down* by 0.17 even though `W` rises by 130 bps** — because `L` rises proportionally more. That is the §5 story from an independent angle: **the conditioner scales the opportunity, and it scales both sides of it.** Note mean and median move in *opposite* directions (+11.1 vs −49.3) — the fat-tail warning of §2.4(b) restated.

**Arm C** (n_live 6,861 vs n_ambient 557,707):

| Quantity | live | ambient | **Δ** |
|---|---|---|---|
| mean (bps) | −12.221 [−22.53, −1.90] | −11.903 [−18.92, −4.43] | **−0.318** |
| median (bps) | −15.45 | −25.61 | **+10.16** |
| `p` | 0.4645 [0.4506, 0.4788] | 0.4390 | **+0.0255** |
| `W` (bps) | 245.5 [225.1, 267.5] | 279.1 | **−33.7** |
| `L` (bps) | 235.7 [217.4, 255.4] | 239.6 | **−3.9** |
| `W/L` | 1.041 [0.973, 1.112] | 1.165 | **−0.124** |

**Arm C's conditional effect on the mean is +0.3 bps in the negative direction — a genuinely small magnitude, stated as a magnitude.** But the distribution *does* move: the rate rises 2.6 points, `W` falls 33.7 bps, `W/L` falls 0.124, dispersion tightens by 58 bps sd. **The arm-C event selects a higher-rate, smaller-win, more symmetric distribution** — a real, quantified conditional shift whose net effect on the mean is near zero because the rate gain and the `W` loss offset. That offsetting is the clearest illustration in this run of why the `(p, W, L)` decomposition was worth building: a mean-only read would have called this "nothing happened", and something did.

### 7.4 TRIPWIRE-3 forward-path derangement — correctly framed, weakly informative

Two report-layer entries with collapse fractions **0.161** and **0.904**. Correctly labelled as **not** the causality claim (design §7.1; SPDR-012 AMENDMENT-T1 established no outcome-side destroy can detect look-ahead for a fixed predictor). Per M-5 the collapse fraction is uninterpretable near a zero live mean — and these live means are near zero — so **neither number carries weight in either direction.** Correct behaviour by the screen; noted so 0.904 is not read as reassurance.

### 7.5 Controls summary

| Control | Non-vacuous? | Resolution (from its own plant curve) | What it establishes |
|---|---|---|---|
| Side-derangement, arm B | yes (0 fixed points, moves a signed mean directly) | ~10-20 bps | no side-attributable effect above ~10-20 bps |
| Side-derangement, arm C | yes | ~20 bps upward; sharp downward | **sides carry real information, pointing negative** (pct 0.0065) |
| M-3 `mag_high` | yes (disjoint pool in all 10 deciles) | ~15-20 bps | the effect is "big bar", **not** the state |
| M-3 `shock_flag` | yes (disjoint pool in all 10 deciles) | ~5 bps | the state adds **+37 bps over magnitude-matched**, pct 0.95, n=505 |
| Ambient-base, arm B | disclosure | mean CI ±25 bps | large distributional shift; `W` and `L` scale together |
| Ambient-base, arm C | disclosure | mean CI ±10 bps | rate +2.6pts, `W` −34 bps, offsetting |
| Tripwire-3 | report layer only | n/a | nothing (correctly) |

---

## 8. M-2 — does the wall-clock span issue change any horizon read?

**Verified and answered: the exposure is real, widespread, and small. It changes no read here.**

- **18,990** cells carry a horizon (screen ✓). Median exact-span fraction **0.9062** (screen 0.906 ✓).
- **78.19%** contain at least one row whose wall-clock span exceeds nominal `h` (screen 78.2% ✓).
- **But the *share* of such rows is small.** `span_frac_exceeding_nominal`: median **0.094**, p75 0.184, p90 0.273, p95 0.364, p99 0.592.
- **And the *amount* of over-span is small at the centre, large in the tail.** Ratio of realised span to nominal: median **1.000**, p95-ratio median **1.087**, but **max-ratio median 2.25**, p90 **20.2**, p99 **45.5**. A handful of rows on sparse symbols span dozens of times their nominal `h`.

**Does it change a read?** Splitting the 534 powered horizon-carrying cells by span cleanliness:

| Exact-span fraction | n cells | median gross mean | median `p` | median `W/L` | median gross edge |
|---|---|---|---|---|---|
| < 0.90 | 184 | **+1.042 bps** | 0.4704 | 1.145 | −0.0512 |
| 0.90 - 0.99 | 349 | **−0.243 bps** | 0.4668 | 1.134 | −0.0590 |
| ≥ 0.99 (clean) | 1 | +4.933 bps | 0.4844 | 1.278 | −0.0789 |

The dirtiest and cleanest strata differ by **~1.3 bps** in gross mean, with `p`, `W/L` and `edge` essentially unchanged. **An order of magnitude below the cost floor; it does not move any conclusion in this document.** M-2 is a real methodological correction, correctly implemented, whose practical effect on SPDR-018's reads is negligible.

**One gap:** span disclosure is emitted for **18,990 of the 22,044** horizon-carrying arm-C cells — **3,054 cells (13.9%) carry a horizon with no span disclosure.** M-2 says "every horizon read co-reports the exact-span subset". Recorded as an M-2 compliance gap; it does not affect the reads above, which use only cells that do carry it.

---

## 9. Question 5 — heterogeneity: who carries the powered cells, and do the strata agree?

Full tables in `results/analyst_stratum_tables.csv`; per-cell magnitudes in `results/analyst_per_cell_magnitudes.parquet`. Headlines below are **disclosure-only** pooled figures (L-03); the per-stratum tables are the binding object.

### 9.1 By arm

| Arm | powered cells | median n | `p` | `W` | `L` | `W/L` | `p_be` | `p_be_net` | gross edge | gross bps | net bps | **cost share of the gap** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **B** | 879 | 3,027 | 0.336 | 107.6 | 53.9 | **1.880** | 0.347 | 0.434 | −0.096 | −1.75 | −15.18 | **0.884** |
| **C** | 534 | 3,708 | 0.467 | 142.1 | 124.5 | **1.136** | 0.468 | 0.526 | −0.057 | **+0.08** | −15.15 | **0.988** |

**The two arms are structurally different objects and must not be pooled into one story.** Arm B is a low-rate, high-asymmetry object (`p` 0.34, `W/L` 1.88). Arm C is a near-coin-flip, near-symmetric object (`p` 0.47, `W/L` 1.14) whose **gross median is actually positive (+0.08 bps)**.

**The gross-vs-net decomposition answers Question 2's second half directly.** Distance from `p` to `p_be_net` splits into a **rate term** (`p_be − p`) and a **cost term** (`p_be_net − p_be`):

- **Arm C: rate term +0.0007, cost term +0.0575 — the cost is 98.8% of the gap.** Arm C's rate sits essentially *exactly* at its own gross break-even. There is no rate deficit to fix; there is only a cost floor.
- **Arm B: rate term +0.0114, cost term +0.0866 — the cost is 88.4% of the gap.** Arm B has a small genuine rate deficit (~1.1 percentage points below its own gross break-even) on top of the cost.

### 9.2 By band (DESIGN / CONFIRM / full TRAIN)

| Arm | Band | cells | `p` | `W/L` | gross bps | net bps | gross edge | cost share |
|---|---|---|---|---|---|---|---|---|
| B | DESIGN | 214 | 0.332 | 1.831 | −2.52 | −15.78 | −0.095 | 0.782 |
| B | CONFIRM | 320 | 0.338 | 1.892 | −1.42 | −14.84 | −0.106 | 0.920 |
| B | TRAIN | 345 | 0.336 | 1.875 | −1.67 | −15.10 | −0.089 | 0.869 |
| C | DESIGN | 25 | 0.485 | 1.110 | **+3.48** | −12.14 | −0.038 | 1.284 |
| C | CONFIRM | 187 | 0.467 | 1.156 | +0.16 | −14.75 | −0.062 | 1.050 |
| C | TRAIN | 322 | 0.467 | 1.134 | −0.16 | −15.51 | −0.055 | 0.974 |

**Bands agree closely.** Arm B DESIGN vs CONFIRM differ by 1.1 bps gross and 0.006 in `p`. Arm C's DESIGN cell count is tiny (25) and its +3.48 bps should not be over-read. **No band-instability problem exists at this `n`** — the same conclusion §4 reached from the C7 pairs.

### 9.3 By clock

Arm B **H1** (143 cells): gross **−0.13 bps**, `W/L` 1.961, edge −0.069. Arm B **M15** (736 cells): gross **−1.98 bps**, `W/L` 1.841, edge −0.102. **H1 is ~1.9 bps closer to gross break-even than M15** — a real measured clock effect, ~7× smaller than the cost floor. Arm C is H1-only among the powered cells.

### 9.4 By symbol (the binding stratum — per AMENDMENT-S1, multi-symbol is credibility only)

Powered per-symbol cells span 21 named symbols plus `__POOLED__`. Full table in the CSV. Range:

| | symbol | cells | `p` | `W/L` | gross bps | `p_be_net` | gross edge |
|---|---|---|---|---|---|---|---|
| **most positive gross** | 1000BONKUSDT | 2 | 0.372 | 1.844 | **+5.28** | 0.392 | −0.020 |
| | 1000LUNCUSDT | 23 | 0.329 | 2.287 | **+3.42** | 0.366 | −0.048 |
| | ORDIUSDT | 14 | 0.326 | 2.258 | **+0.92** | 0.359 | −0.049 |
| **most negative gross** | INJUSDT | 34 | 0.341 | 1.770 | **−4.47** | 0.419 | −0.088 |
| | BLURUSDT | 20 | 0.329 | 1.861 | **−4.71** | 0.412 | −0.084 |
| | DYDXUSDT | 31 | 0.336 | 1.636 | **−4.35** | 0.435 | −0.092 |
| **worst edge** | BTCUSDT | 65 | 0.303 | **2.252** | −0.99 | **0.470** | **−0.160** |
| | BNBUSDT | 63 | 0.335 | 1.771 | −2.53 | 0.481 | −0.146 |

**Heterogeneity in gross mean spans about 10 bps across symbols (+5.3 to −4.7), comparable to the cost floor itself.** But the *edge* is negative in **every single symbol** — range −0.020 (1000BONK, 2 cells) to −0.160 (BTC, 65 cells). **No symbol is an exception.** Note that BTC and BNB — the tightest, most liquid names — have the *worst* edges, driven by small `W` and `L` (BTC `W` 65.8, `L` 26.3): when the moves are small the fixed cost floor is a larger fraction of them. A cost-scaling effect, not a signal effect, and exactly SoT §3.1's selection argument running in reverse.

`1000BONKUSDT` and `BLURUSDT` are retained as explicit rows per design §9 (981 and 863 cells, 212 and 196 at target) — no post-outcome universe edit. Verified: all **25** pinned symbols appear.

### 9.5 Asset class — the cTrader replication (credibility only, NEVER pooled into `n`)

42 cells on EURUSD / XAUUSD / USTEC, INFR-021 fence sha256 verified, cTrader holdout never queried. **Gross only** — no sanctioned cTrader cost table exists, so `p_be_net` and `edge` are correctly not reported.

| | median `p` | median gross `p_be` | median `W/L` | median gross mean | median `n` |
|---|---|---|---|---|---|
| **all 42 cells** | **0.3531** | **0.3559** | **1.810** | **−0.248 bps** | 2,672 |
| EURUSD | 0.3460 | 0.3586 | 1.790 | −0.555 | 2,792 |
| XAUUSD | 0.3531 | 0.3510 | 1.849 | −0.074 | 2,610 |
| USTEC | 0.3713 | 0.3600 | 1.778 | −0.097 | 2,599 |

Every screen figure verified (0.3531 / 0.3559 / 1.810 / −0.25 ✓).

**The strongest single piece of external validity in the run.** A different asset class, broker, fence and volatility scale — and the geometry is the same: `p` ≈ 0.35, `W/L` ≈ 1.8, `p` within 0.003 of its own gross break-even, gross mean within 0.6 bps of zero. **The zero-line result of §5 is not a Bybit artifact.** Per AMENDMENT-C1/S1 this is credibility, not power: never pooled into `n`, no `edge` claimed.

---

## 10. Evidence FOR the hypothesis

`HYP-D5` is a **precision** hypothesis: *"for every question 017 left UNPOWERED or INCONCLUSIVE, measured in its original statement, can it be resolved to its own target precision using legitimate power levers alone — and if it can, what is the answer?"* Evidence FOR is evidence that the levers worked and answers came out.

1. **The central 017 blocker is broken.** SPDR-014 produced **0 powered cells of 927**. SPDR-018 produces **1,413 powered signed cells**, including **121 C1 cells** on the very object that produced zero. Median block MDE on powered C1 cells is **7.87 bps** against a ≤10 bps target, versus the parent's 20 / 172 / 796 bps. **The levers demonstrably bought power without changing what was measured** — parent parity to 9.1e-13 proves the object is the same one.
2. **Every design §2 item carries cells and nothing was narrowed.** All 27 residue tags populated; the only authorised drop (SPDR-017) is the only drop. Verified item by item.
3. **Several items are cleanly and completely resolved, with answers**, not merely powered: **A5** (all 135 cells now satisfy the §6.4 clause with sign agreement in all three thirds — a direct reversal of "42/45 have only one powered third"); **A1** (HIGH−LOW magnitude gaps +18 to +180 bps, CI-excluding-zero on every clock and band, 97-100% of H1/H4 per-symbol cells); **C7** (the sign-flip instability is a thin-cell weighting artifact — bands agree to 0.33 bps `n`-weighted); **C8** (weightings agree to 0.002); **D8** (never-scored CONFIRM slice scored and reproduces DESIGN); **D7** (stickiness ≈0.94 quantified with CIs).
4. **The `(p, W, L)` layer — the axis-B gap SoT §2 identified as *never measured* — is now measured on 24,098 signed cells** with an identity reconstructing to 1.5e-11 bps. This is the deliverable the mid-checkpoint reflection needed, and it exists.
5. **`E[|move|]` results that parameterise capture design are confirmed and replicate.** The HMM HIGH/LOW gap, R-MARKOV k=4/12 ΔBrier (−0.020 / −0.108 here vs SoT's banked −0.025 / −0.114), T-GT-CUR hit rate (0.65-0.70 vs base 0.47, on **CONFIRM**), and rank IC 0.33-0.42 on H1 all reproduce. **SoT §1.1's "the `E[|move|]` results parameterise capture design regardless of what the rate does" is satisfied.**
6. **One live thread survives its designated control in the registered direction:** shock-conditioned MOMO, +22.6 bps live vs a magnitude-matched comparator at percentile 0.95, above the partial cost floor (§7.2).
7. **The cross-asset replication reproduces the geometry** on three instruments in a different asset class (§9.5) — evidence the measurement captures something structural rather than a venue artifact.
8. **`NOT_RESOLVABLE` is delivered as a first-class answer**, quantified per cell with realised `n`, block MDE, target, multiple short and required `n` (3,559 cells, median 7.87× short). Per design §5 that **is** an answer to the 017 question, and it was produced rather than dodged.

## 11. Evidence AGAINST the hypothesis

"Against" here means against the *precision* claim — items where the levers did not resolve the question, or where the resolution is compromised.

1. **Arm C is largely unresolved in its registered form.** 632 of 22,194 arm-C cells reach target (2.8%). **C3 alone accounts for 1,946 of the 3,559 NOT_RESOLVABLE cells (55%)**, C5 another 914. Median shortfall is **7.87× the target MDE**, p90 **27.3×** — meaning required `n` is roughly **62× to 745× the realised `n`**. The design's predeclaration (C2/C3/C4 may not close) is vindicated, but the consequence is that the event-nested conditioner science remains substantially unanswered.
2. **Design-declared HARD checks did not run.** `TRIPWIRE-2` absent entirely — half of the declared causality evidence (design §7.1). `Determinism` downgraded to INFORMATIVE and not executed. `screen.md` §9 records "Deviations: none". (§1.2; mitigations there.)
3. **Uncertainty on two of the three required point statistics is 99% absent** (§2.4b). Design §6.1 requires block-bootstrap CIs on mean, median *and* 10% trimmed mean, "all three always co-reported", explicitly because this family is fat-tailed. Median/trimmed CIs exist on 240 of 24,098 signed cells. **And the statistics disagree by 13 bps** with only 68% sign agreement. The near-break-even narrative rests on the most favourable of the three.
4. **Parent parity is 27.5% incomplete on arm C** (6,127 of 8,450 parent cells), the arm carrying 59% of the grid and all the hardest questions (§1.3).
5. **M-2 span disclosure is missing on 3,054 horizon-carrying cells (13.9%)** despite M-2 being binding on "every horizon read" (§8).
6. **The design's B3 statement does not reconcile with any slice of the data** (§2.4a). The screen handled it conservatively, but a frozen operator-signed design contains a count that no construction reproduces — a premise defect of the kind L-49's meta-lesson warns about.
7. **Several items reach 0 cells at target and stay there**: B1 (0/2,044), B2 (0/1,022), B3 (0/830), D2 (0/300). Per B-5 these are power statements — but they are also *unresolved questions*, and the hypothesis was that the levers would resolve them.
8. **Multiplicity is disclosed but not treated.** 37,791 cells, per the operator directive that "multiplicity is disclosed, not rationed" — legitimate — but it means the single positive powered cell (§6.3) and the single `shock_flag` control at p=0.05 (§7.2) must be read against a grid of that size, and per L-34 the tail counts must be compared to the realised multiple-testing process rather than to zero.
9. **`plots/` is empty** — the design budgeted ≤8 plots and none were emitted.

## 12. What this says about the *substantive* question (separate from HYP-D5)

HYP-D5 is about precision. The operator will read this for the capture-geometry decision, so I state the substantive picture explicitly and separately.

1. **Nothing clears `p_be_net`.** 0 of 1,413 powered signed cells, and 0 of 24,098 signed cells at target precision with a `net_mean` CI-low above zero. Also 0 with a `gross_edge` CI-low above zero, and 0 with a `net_edge` CI-low above zero.
2. **The rate is not the problem — the cost floor is.** 88% (arm B) to 99% (arm C) of the distance to net break-even is the cost term. Arm C's rate sits **0.0007** below its own gross break-even.
3. **The `W/L` handle exists and does not point up** (§5). 96.7% mirror-determined; 67× movable by exit geometry with `p` moving inversely; free residual uniformly negative; 82.8% of powered cells cannot be distinguished from the driftless mirror at all.
4. **Selection scales both sides.** C5 shows `W` ranging 109→235 bps while `p` stays pinned in 0.415-0.480 and `W/L` moves only 1.10→1.40. The ambient-base deltas show the same from the other direction (arm B: `W` +130 bps, `L` +88 bps, `W/L` **−0.17**). **SoT §3.1 — "selection is a multiplier on an existing edge, never a creator of one; if `p = p*_net`, scaling the move scales a zero" — is now measured, not argued.**
5. **The one exception to close inspection is `shock_flag`** (§7.2), a single underpowered control cell at the boundary.
6. **This picture holds across a second asset class** (§9.5).

**Mapped onto SoT §10:** end-state 1 (terminal capture-geometry package) is where the evidence currently points, with **two named exceptions that keep it from being terminal**: (a) the `shock_flag` M-3 survivor, and (b) the 3,559 `NOT_RESOLVABLE` cells, 55% of them in C3 — the ordered vol-flip conditioner, precisely the "conditional direction is unpowered, not refuted" object the SoT premise names. **Declaring end-state 1 while C3 sits 7.9× short of its own MDE would be reading UNPOWERED as a negative, which B-5 forbids and which is exactly the error checkpoint-017 was closed to avoid.** End-state 3 is checked and **not** satisfied at this cost floor (§6.2). End-state 2 requires something to clear `p_be_net`; nothing does.

---

## 13. Threats to validity

| # | Threat | Severity | Assessment |
|---|---|---|---|
| T1 | **TRIPWIRE-2 never run** — half the declared causality evidence absent | **High (procedural)** | Mitigated by exact parent parity + TRIPWIRE-1 + the negative direction of the result. Operator ruling requested (§1.2). |
| T2 | **Median/trimmed CIs 99% absent** while the three statistics disagree by 13 bps | **High (inferential)** | The mean is the correct identity object, but "at gross break-even" is the most favourable framing. Bootstrap the medians on the 1,413 powered cells. |
| T3 | **Spread not charged** | **High, disclosed, unavoidable** | Every net figure overstates. All conclusions here become *more* negative once spread is charged, so it cannot flip a negative to a positive — but it can turn the `shock_flag` +22.6-vs-15.3 margin into nothing. The single most decision-relevant unknown; SoT §3 already lists it as **blocking, unresolved**. |
| T4 | **Multiplicity across 37,791 cells** | Medium | Disclosed by directive, not treated. Affects only the two single-cell positives (§6.3, §7.2), both already discounted on those grounds. |
| T5 | **Pooling validity.** σ̂-normalised pooling assumes cross-symbol comparability after scaling | Medium | Partly checked: per-symbol edges are negative in all 21 named symbols, so the pooled sign is not a Simpson artifact. But per-symbol *gross means* span 10 bps, so pooled magnitudes are less trustworthy than pooled signs. Design §8's "POOLED: disclosure-only unless homogeneity is shown" is the right rule and I applied it. |
| T6 | **Dependence in the 2,714 C7 pairs** | Medium | Explicitly handled — the naive binomial z is quoted as an upper bound; the C7 conclusion rests on the block-MDE comparison and the `n`-weighting. |
| T7 | **Arm C parity 27.5% incomplete** | Medium | No evidence of drift; but the anti-drift proof is partial on the largest arm. |
| T8 | **Flat legs excluded from `p`** | Low | Quantified: ≤0.6 bps effect on powered cells; 226 cells grid-wide exceed 5% flat. Charge flat legs their cost in any 019/020 budget. |
| T9 | **M-2 span disclosure missing on 3,054 cells** | Low | Measured span effect is ~1.3 bps on cells that do carry it (§8). |
| T10 | **Column-name trap** (`net_*` is not "net of cost"; `gross_p_be_net` is the real net break-even) | Low but sharp | Could silently produce a 0.085 error in `p_be_net`. Documented in §2.2. |
| T11 | **`levers_exhausted` semantics** — means "levers applied", not "levers failed"; 376 cells carry it alongside `at_parent_target_precision` | Low | Documented in §3; `not_resolvable.json` is authoritative. |

---

## 14. Open threads I resolved, and threads I could not

**Resolved in this pass:**

- the identity claim (verified to 1.46e-11 bps, with the flat-row clarification);
- the 0-of-1,413 / 32.5% claim (verified exactly);
- **C7** — the sign flip is not distinguishable from noise, the flip rate is *below* chance, and the band reversal is a thin-cell weighting artifact (§4);
- **M-2** — 78.2% verified; changes no read; median over-span share is 9.4% (§8);
- **B3** — the 830 identified as the per-symbol positive-partial-net set, all three cross-checks reproduced, 125 shown irreconcilable under every slice, and the substantive answer (0 of 830 at target) supplied (§2.4a);
- **IN-5** — quantified at 240/24,098 rather than "the levers-exhausted cells", and shown to matter by 13 bps (§2.4b);
- **Question 3 (`W/L`)** — tested three ways and answered (§5);
- **Question 4 (counter-outcome)** — found, sized, and shown not to route (§6);
- the screen's `1,511` vs `1,413` signed-cell discrepancy (§2.3);
- the screen's `−29.1` C9 label (it is the median of per-cell means; median-of-medians is −30.0);
- the second, smaller A1 HMM variant set the screen did not quote (§3, arm A).

**Could not resolve — proposals for the operator, not actions I took:**

| # | Thread | Why it needs new work |
|---|---|---|
| P1 | **Is `shock_flag` real?** | Needs the M-3 comparator re-run at `n` in the thousands rather than 505, on the *powered* grid strata rather than one control cell, with multiplicity treated. The highest-value single follow-up in the run. |
| P2 | **Median/trimmed-mean CIs on the 1,413 powered cells** | Cheap, in-scope, and directly changes how §12's "at gross break-even" reads. |
| P3 | **TRIPWIRE-2 and Determinism** | Both declared HARD, both cheap. |
| P4 | **What `n` would resolve C3?** | `not_resolvable.json` gives it per cell; nobody has aggregated whether it is reachable inside the Bybit catalog at all. If it is not, that is itself the answer to the conditional-direction question and should be recorded as such. |
| P5 | **The per-symbol spread pin** (SoT §3 axis E, "blocking, unresolved") | The difference between "nothing clears the floor by 0.65 bps" and "nothing comes close". No capture design should be parameterised before it exists. |
| P6 | **Arm C parity on the remaining 2,323 parent cells** | Completes the anti-drift proof. |

---

## 15. RECOMMENDED verdict (non-final — the operator decides)

### On `HYP-D5` (the experiment's own hypothesis — a precision hypothesis)

> ### **SUPPORTED, with two integrity items requiring an operator ruling.**

The hypothesis asked whether the 017 residue could be resolved to its own target precision using legitimate power levers alone, without re-defining any estimand — and if so, what the answers are.

**It could, for most of it, and the answers were produced.** 1,413 signed cells now reach their parents' own bars against SPDR-014's 0 of 927; parent parity to 1e-12 proves no estimand was re-specified; every §2 item carries cells; A5, A1, C7, C8, D7 and D8 are cleanly resolved with magnitudes and CIs; and the 3,559 cells that could not be resolved are delivered as quantified first-class `NOT_RESOLVABLE` answers rather than as silence.

The three pieces of evidence that most drive this:

1. **Parent parity at 4.5e-13 / 1.8e-12 / 9.1e-13 / 0.0 across arms A-D** — the design's own anti-drift proof, which separates a powering experiment from a re-scoping one.
2. **121 powered C1 cells at a median block MDE of 7.87 bps** on the object that gave the parent 0 of 927 at 20-796 bps.
3. **A5's complete reversal** (135/135 cells now satisfy a clause 017 found satisfiable in 3/45) and **D8's 1,800 never-before-scored cells** reproducing DESIGN on CONFIRM.

**What would change this verdict:** a TRIPWIRE-2 run showing the legal and leaky variants are *not* separated (which would invalidate the emission); or a demonstration that arm C's 27.5% parity gap hides drift.

### On the substantive capture-geometry question (separate, and the operator's actual decision)

I am not authorised to take a family disposition and I do not. What the evidence supports as an **input** to the mid-checkpoint reflection:

- **`SPDR-019`/`SPDR-020` should not open as an edge search on this evidence.** SoT §1.1 makes the gate explicit — "a capture design cannot manufacture expectancy out of a joint `(p, W, L)` that sits at break-even". The joint sits at break-even: 0 of 1,413 clear `p_be_net`, arm C's rate is 0.0007 from its own gross break-even, and §5 shows the `W/L` lever moves 67× without lifting the mean off the zero line in any of five exit geometries, replicated on a second asset class.
- **But the checkpoint should not be closed as end-state 1 either.** Two things forbid it: the `shock_flag` M-3 survivor (§7.2), and 3,559 `NOT_RESOLVABLE` cells — 55% of them C3, the ordered vol-flip that the SoT premise names as "unpowered, not refuted". Closing over those would read UNPOWERED as a negative, which B-5 forbids and which is precisely the error checkpoint-017 was closed to avoid.
- **The shape I would suggest** (operator's call entirely): resolve P1, P2, P3 and P5 first — they are cheap, in-scope, and P5 (the spread pin) is already a declared blocking prerequisite — then take the end-state decision. `SPDR-019`/`020` re-framed as **apparatus or characterisation** rather than as an edge search would be consistent with everything measured here; as a tradability test it would not be.

---

**Final verdict and disposition are the operator's.** Suggested probes: push on **P1** if you want to know whether the one live thread is real; **P2** if you want to know whether "at gross break-even" survives contact with the median; **P5** if you want any net figure in this document to mean anything. To attack my §5 conclusion, the place to do it is the free residual `log R` — ask whether any exit geometry *outside* the five in this grid could hold `R > 1`, and demand the mechanism rather than the search.

**No tradability, deployability, cost-complete, family-status, graduation or XENA claim is made or implied by this document.**agentId: a255e51318a5c9ab0 (use SendMessage with to: 'a255e51318a5c9ab0', summary: '<5-10 word recap>' to continue this agent)
<usage>subagent_tokens: 255133
tool_uses: 49
duration_ms: 1506361</usage>

---

# ADDENDUM — added by the orchestrator AFTER the analyst's pass (2026-07-25)

This section is **not** the analyst's text and does not alter any of its findings. It records the
disposition of the two integrity items the analyst raised in §0.7 and §1.1, both of which it was
correct about.

Both were fixed and the screen re-run. The emission the operator is reading now carries
**18 HARD checks, 0 failed** (code pin `44c720f82af52b8b…`), where the emission the analyst
reviewed carried 16.

| Item the analyst raised | Disposition |
|---|---|
| `TRIPWIRE-2` declared HARD but never invoked, absent from the self-check | **Fixed and run.** Now computed on the independent self-check side (`golden.g6`), which rebuilds both the legal and the leaky variant from the fenced catalog. Legal **85.34 bps** vs leaky twin **644.71 bps** on the same 58 selected rows — a **7.55×** separation. Design §7.1 anticipated "orders of magnitude"; 7.55× is material and one-directional but does **not** meet that bar, and is reported as measured. |
| `Determinism` silently downgraded from HARD to INFORMATIVE and not executed | **Fixed and run.** Now executes unconditionally whenever `--jobs > 1`, independent of `--resume`, so a resumed run cannot skip it. 630 cells sequential vs `--jobs 8`: **zero columns differ.** |
| `screen.md` §9 claiming "Deviations: none" while both were absent | **Corrected.** `screen.md` §8 now carries the defect, its cause and its fix; §9 distinguishes design deviations (none) from the process defect (one, recorded). |

**The analyst's substantive findings are unchanged by this correction** — no estimand, object,
band, control or cell value was touched. The re-run recomputed only the controls, tripwires and
self-check; arms A-D were resumed byte-identical from their emitted parquets.

The analyst's recommendation stands as written, and the verdict and disposition remain the
operator's.
