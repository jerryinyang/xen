# Audit Report: Experiment EXP-008 — CF-MR-003/HYP-001 cross-domain MR availability screen

## Summary

- **Verdict**: **PASS** (audit) — the recorded experiment verdict **INCONCLUSIVE (underpowered)** is
  verdict-correct, holdout-clean, and causally sound.
- **Critical Issues**: **0**
- **Warnings**: 1
- **Info Notes**: 5

The frozen, pre-registered design ran faithfully and returned **INCONCLUSIVE** — the predeclared §7
branch for *">½ of axes ineligible-UNPOWERED"*. The cause is fully diagnosed and **consistent with**
the verdict (it produces it), so it is not verdict-material: the design's 3-leg MR screen
(`VR ∧ half-life ∧ Hurst-DFA<0.45`) is vetoed by the **Hurst leg**, which is near-unsatisfiable on
deviation *level* series. No leak, no holdout touch, no counted read.

Classification: **analysis-only, comparative across data views** → thorough audit depth.

---

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `cross_domain_mr.py` | Correctness | PASS | Anchor constructors, MR-screen legs, robust-z re-derived independently (below). DFA validated on known processes. |
| `cross_domain_mr.py` | Edge cases | PASS | Warmup→NaN, `0<φ<1` OU guard, zero-MAD/zero-std guards, lone-class S5→UNPOWERED, degenerate windows→NaN. |
| `cross_domain_mr.py` | Type safety | PASS | Typed public fns + `AnchorSeries` dataclass. |
| `cross_domain_mr.py` | NaN handling | PASS | Explicit; `where=`/masked divides; no silent propagation. sqrt-domain guarded. |
| `run_experiment.py` | Correctness | PASS | Event detection, excursion, control/pool, gate wiring, Holm, verdict re-derived below. |
| `run_experiment.py` | Holdout exclusion | PASS | `load_train_1m` slices first `int(0.7·int(0.7·total))` rows of the CloseTime-sorted lazy scan; TEST band + final-30% holdout never materialized (independent check below). |
| `run_experiment.py` | Loader ordering | PASS | `scan_parquet().sort("CloseTime").slice(0, train_cutoff)` — sort before slice; column-projected; lazy collect of TRAIN only. |
| `run_experiment.py` | Memory/performance | PASS | Screen evaluated **only at extreme candidates** (causally-identical bound); plots consume bounded per-cell frame; no re-load for plotting. |
| `run_experiment.py` | Safe optimization | PASS | The extreme-only screen bound does not change the event set (an event needs `|z|≥z*` AND screen-pass, so screening where `|z|<z*` is dead). Verified: independent full-scan screen == `detect_events`. |
| `run_experiment.py` | Progress tracking | PASS | `tqdm` over instrument-load and series loops; helpers quiet. |
| `run_experiment.py` | Organization / import side effects | PASS | Constants→types→I/O→pure→plotting→orchestration→`main()`; `mkdir` only in `main()`. |
| `availability_gate.py` | Additive change | PASS | `git diff`: +`STAT_TAILMASS_UPPER`/`TAU_UPPER` + one branch in each of `_stat_1d`/`_stat_2d`; the single deletion is a **comment** edit. `median` / lower-`tailmass` behavior + all frozen constants (Z/FWER/N_PERM/B_SE/K_TAIL) **byte-unchanged**. |
| all | Docstrings | PASS | Provenance-contract docstring on `cross_domain_mr`; per-fn docs. |

---

## Numerical Validation

### Spot checks (independent re-derivation from raw data)

1. **Holdout / TRAIN boundary (EURUSD).** `total=1,870,801`; `train_rows=916,692 == int(0.49·total)` ✓.
   TRAIN max `CloseTime = 2023-11-21 23:44` **<** analysis boundary `2024-12-12 15:10` **≪** full-file
   max `2026-06-19 20:56`. The TEST band and the final-30% global holdout are **never read**.
2. **Event count (S4_OU · EURUSD · 4h/1h).** A **fresh** VR/half-life/Hurst screen over trailing-200
   windows at the extreme bars → **1** screen-passing event; `detect_events` → **1**; defined-regime →
   **1**. `per_cell.parquet` has **no row** for this cell — consistent, because `cell_read` drops cells
   with `<2` events. Numbers reproduce.
3. **DFA correctness.** White noise α = **0.521** (≈0.5), random walk α = **1.478** (≈1.5),
   AR(1)φ=−0.6 anti-persistent = 0.31 (<0.5). This is a correct standard DFA → the Hurst finding is a
   **real property**, not an implementation artifact.
4. **Causal lag.** `dev_lag[i] == dev[i-1]` confirmed by construction (`concat([[nan], dev[:-1]])`).

### Range / statistical sanity

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| Cells emitted (n_events≥2) | small under this screen | 33 cell×endpoint pairs (S3:1, S4:30, S5:1) | YES |
| n_events per cell | ≥100 needed for power | median 7.5, **max 18** | YES (underpowered, as recorded) |
| Powered cells / axis | ≥4 for eligibility | **0** on all 15 axes | YES |
| Eligible axes | — | **0 / 15** | YES |
| Tripwire columns finite | 100% | labelperm 1.0, timerev 1.0 | YES |

---

## Verdict Forensics

### Per-stratum re-derivation & masking check

Binding stratum = (instrument, anchor-series, domain-pair); axis = (series, domain-pair), ≤16
instrument-cells. **All 15 axes are UNPOWERED with 0 powered instrument-cells** on **both** endpoints
(`axis_results.json`). There is **no pooled headline masking a stratum** — the result is *uniform* across
all strata: no cell anywhere reaches `N_min=100` powered status. Per-stratum non-pooling is respected
(L-03): the verdict is emitted per axis and the family read is the union, not an average.

- Pooled/aggregated headline: none used as a verdict. **Masking heterogeneity? NO** — the picture is
  homogeneous UNPOWERED (drop-one confirms the veto is the Hurst leg in *every* series/pair).

### Verdict-branch re-derivation (design §7)

- **EXONERATE** requires axes to be **tested (powered) and not admitted** under Holm — "none of the
  5×3 confers availability beyond matched-random." Not satisfied: the axes were never powered.
- **INCONCLUSIVE** = "admission borderline / **>½ of axes ineligible-UNPOWERED** / leak-ambiguous."
  15/15 axes ineligible-UNPOWERED → this branch. `adjudicate` selects INCONCLUSIVE via
  `n_eligible (0) < 0.5·15`. **Correct.** INCONCLUSIVE (not EXONERATE) is the faithful reading: the
  screen could not *test* availability, distinct from *testing and finding no edge*.

### Mechanism (why INCONCLUSIVE)

The **Hurst-DFA<0.45 leg** of the 3-leg conjunction is the sole binding constraint. Drop-one-leg
disclosure (`dropone_sensitivity.json`, independently reproduced), event totals over all 240 cells:

| Leg combo | Total events | Cells ≥100 |
|---|---|---|
| VR only | 433,790 | 222/240 |
| HL only | 609,626 | 234/240 |
| **VR+HL (drop Hurst)** | **315,644** | **216/240** |
| Hurst only | 792 | 0/240 |
| VR+Hurst / HL+Hurst | 528 / 339 | 0/240 |
| **ALL3 (design screen)** | **280** | **0/240** |

Every combo **containing** Hurst yields ≤792 total events and **0/240** powered cells; every combo
**excluding** Hurst powers **216–234/240**. On EURUSD·4h/1h the per-leg extreme-bar pass counts are
VR=446, HL=1202, **Hurst=0** (S1) — the deviation *level* series is locally **persistent** (Hurst>0.5)
even while mean-reverting to the anchor in the VR/half-life sense. `Hurst-DFA<0.45` (increment
anti-persistence) is the wrong instrument on a stationary deviation *level*.

### Gate/screen-shape check

- Binding instrument: the **MR screen** (upstream of the `availability_gate`). The gate itself never
  engaged — cells were UNPOWERED before adjudication.
- **Wrong instrument for the shape? YES.** This is the **L-12 §3 pattern** (a structurally
  near-impossible conjunctive leg with, effectively, no attainable pass region) reappearing **inside
  the screen**, not the referee. It vetoes availability the VR/HL legs would otherwise power.
  Recorded for the interpreter; the gate/screen is **not** retro-edited (that would be a post-hoc
  goalpost move). Design §7's INCONCLUSIVE clause is prescriptive: *"No goalpost move; re-scope only as
  a new experiment."*

---

## Causal Provenance & Leak (independent of numeric reproduction)

### Provenance trace (decision-bearing quantities)

| Quantity | Inputs & timestamps | ≤ t (≤ t-1 for next-bar)? | Lines |
|---|---|---|---|
| Anchor `a` (S1–S5) | rolling stat over anchor bars ending at anchor close `k`, mapped to exec by `last anchor CloseTime ≤ exec CloseTime[j]` (`map_prev`) | YES — completed anchor bar only | `cross_domain_mr.py:map_prev`, `anchor_series` |
| Deviation `dev[j]`, `z[j]` | exec Close/anchor at close `j`; robust-z over trailing `W_z` ending `j` | YES (known at exec close `j`) | `anchor_series`, `rolling_*_z` |
| Decision at act-bar `i` | uses `dev[i-1]`, `z[i-1]`, screen window `dev[i-W_s:i]` (ends `i-1`), `regime[i-1]`, `atr[i-1]` | YES — strictly `≤ i-1` | `detect_events`, `excursion_series`, `build_exec_domain` lag arrays |
| Excursion `θ[i]` (outcome) | `Open[i]`, forward `min Low`/`max High` over `[i, i+H-1]`, `atr[i-1]`, sign `dev[i-1]` | Outcome (forward of the open); decision inputs all `≤ i-1` | `excursion_series`, `_window_extremes(forward=True)` |
| Matched-random control / pool | same-regime random bars via `vol_regime.regime_matched_entries`; `θ` measured identically | YES (regime label `≤ i-1`; θ outcome) | `matched_random_idx`, `cell_read` |

- **`rct[di]`-style own-close-as-intrabar-limit? NO.** No intrabar limit is used; the outcome is an
  MFE-style excursion, and every *decision* input is lagged one bar.
- **Decision at action-bar open on confirmed bars only? YES.** The screen/extreme/fade-sign all read
  `i-1`; the forming bar's OHLC is never read for a decision. The excursion (which reads bar `i`'s
  High/Low forward) is the **outcome**, not a decision input.
- **Open-to-open? N/A — labelled non-tradable diagnostic.** The excursion is an intrabar MFE toward
  the anchor (design §2/§4), an **availability** diagnostic on real prices (EXP-047/081 precedent), not
  a tradable open-to-open return or a P&L/deployability claim. Correctly scoped (Info-5).

### Leak tripwire

- **Two future-destroying controls shipped** and wired per cell: (1) conditioning-label permutation
  (random `n_events` among extreme candidates), (2) forward-excursion time-reversal (backward window).
  Both are inputs to `adjudicate`, which **gates ADMIT on both collapsing** (`|Δ|<Δ*`) on the admitting
  cells.
- **Edge collapsed under it? N/A — no cell admitted.** With 0 powered/admitting cells there is no edge
  to collapse; the tripwires are present and correct but had nothing to fire on. Columns are 100%
  finite. No surviving edge exists anywhere → **no leak-class finding**.

### Shared-module provenance contract

`cross_domain_mr.py` carries an explicit provenance-contract docstring (outputs known at exec close
`j`, lag-by-1 before deciding; the module emits **no** outcome column — the excursion is built in
orchestration). Code matches the contract (verified line-by-line above). ✓

### Price-primary check

Correctly classified **ANALYSIS-ONLY** (design §2): it characterises conditional forward-excursion
availability on real prices vs a matched-random control and books **no** signal/position/order/P&L.
No edge is generated or executed → not price-primary; no cTrader run required. Not a vectorized
price-strategy backtest. ✓ No booked-vs-real feed involved.

---

## Scope Compliance

- **Analysis plan followed: YES.** 5 anchor series × 3 domain pairs; MR screen VR+HL+Hurst-DFA
  (ADF/KPSS dropped per §4); robust-z; matched-random regime control; cross-axis Holm max-stat
  admission; both leak tripwires; §7 predeclared verdict logic; TRAIN-only.
- **Deviations (3, all non-material):**
  1. **§10 CI n_boot≥10k vs frozen-gate `B_SE=2000`** — reconciled: per-cell CI/majority use
     `cell_se(n_boot=10 000)`; the **axis permuted admission** uses the frozen `run_sub_screen`
     (calibrated `B_SE=2000`, `N_PERM=5000`) rather than overriding a frozen-GREEN gate constant.
     Both via the `availability_gate` functions §5 names. *Immaterial* — no cell powered/admitted, so
     neither the CI resolution nor the permutation count moved any verdict-bearing number.
  2. **§8 sensitivity sweeps (z*/W_a/recent-third) deferred** (operator-accepted). The **drop-one-leg**
     disclosure — the decisive §8 diagnostic here — **is** present and independently reproduced.
     *Immaterial to the verdict*; it is the non-binding robustness disclosure and the one that matters
     (leg-dependence) was run.
  3. **Excursion = intrabar MFE** (uses High/Low), not open-to-open. Explicitly a non-tradable
     availability diagnostic (design §2/§4), consistent with the availability-screen precedent.
- **Complexity budget:** stat-test types 3/3 (block-boot CI, cross-axis-Holm permuted admission, leak
  tripwire); plots 6/6 (P1–P6 present); modules: 1 new (`cross_domain_mr`) + 1 additive gate edit +
  the experiment script — within the §9 budget.
- **Holdout exclusion verified: YES** (independent boundary check).
- **Registry/reads:** 0 candidate slots, 0 counted TEST reads, holdout sealed — matches design §11.

---

## Issues

### Critical
None.

### Warning

1. **MR-screen mis-specification: the Hurst-DFA<0.45 leg is near-unsatisfiable on deviation levels
   (drives the INCONCLUSIVE).**
   - File: `python/src/xen/cross_domain_mr.py` (`hurst_dfa`, `mr_screen_pass`); design §4.
   - Description: The Hurst leg tests **increment anti-persistence** (`α<0.45`), but is applied to the
     mean-reverting deviation **level** series, which is locally **persistent** (`α>0.5`). It therefore
     contradicts the VR/half-life legs and vetoes the conjunction (≤792 events / 0 powered cells across
     all 240 cells; 315,644 events / 216 powered without it).
   - Impact: The availability screen cannot **test** the family on TRAIN → INCONCLUSIVE-underpowered.
   - **Materiality: not verdict-material for EXP-008.** The finding is the *cause* of the recorded
     verdict and fully consistent with it; it cannot flip INCONCLUSIVE to ADMIT/EXONERATE within this
     **frozen** design. Per design §7, the fix (apply Hurst to increments, or drop it and re-screen on
     VR+HL) is a **new experiment**, not an amend-in-place (there is no contamination to purge — L-10
     does not apply; the result is honestly underpowered, not wrong). **No rerun of EXP-008 required.**

### Info

1. **Cells with `<2` events are dropped** (`cell_read` returns `None`) → `per_cell.parquet` holds only
   the 33 cells that cleared 2 events. Immaterial (all remain UNPOWERED at `N_min=100`).
2. **§8 z*/W_a/recent-third sweeps deferred** (operator-accepted); drop-one leg disclosure present.
3. **Control/pool finite-θ filtering** can leave the control slightly below `n_cond` at end-of-sample.
   Immaterial — every cell is UNPOWERED regardless.
4. **10k-CI vs frozen-2k-admission reconciliation** (deviation 1). Immaterial — nothing admitted.
5. **Excursion is a non-tradable intrabar MFE availability diagnostic** (design §2/§4), not an
   open-to-open tradable return. Correctly labelled; consistent with EXP-047/081.

---

## Materiality & Re-Audit Requirements

- **Every finding is non-blocking.** The single Warning is the diagnosed **mechanism** of the recorded
  verdict and is verdict-*consistent*: it cannot move sample membership, a denominator, a metric, the
  binding stratum, or the INCONCLUSIVE outcome within the frozen design. Its resolution is explicitly a
  **new experiment** (design §7), not a fix-and-rerun of EXP-008.
- **No re-execution required.** The verdict INCONCLUSIVE (underpowered) is verdict-correct,
  holdout-clean, causally sound, and leak-free (no admitting cell → no edge to survive a tripwire).
- **Audit verdict: PASS, 0 Critical.** → proceed to Stage 5 (Document). Recommended registry
  disposition: CF-MR-003 `REGISTERED → SCREENED-INCONCLUSIVE (underpowered — Hurst-leg veto)`; family
  retained; a corrected-screen re-screen is a future dated-D0 experiment.
