# SPDR-012 — QA / compliance review (append-only)

Each run appends a dated section. Never rewrite a previous run's findings.

---

## QA run 1 — 2026-07-23T14:31Z — mode: subagent — HEAD 549cd38 (dirty: 8 untracked paths)

**Verdict: REVISE**

Applied as a *post-execution* design-to-code fidelity + governance review (the screen was
executed under explicit operator authority). The screen was **not** re-run. All quoted numbers
come from the artifact set completed at `2026-07-23T14:22:48Z`
(`results/integrity_selfcheck.json.generated_utc`), which finished during this review; an
earlier artifact set (14:10Z) was also inspected and agrees on every figure quoted here.

Reviewed: `screen_code/` (13 modules), `analysis_code/summarise.py`, `results/*`.
Authority stack read in full: RAW brief, `design.md`, checkpoint-017 design, `cf-voldir-001.md`
+ `-universe.json`, `chapter-06-governance.md`, `spdr-lane.md`, lessons-and-amendments,
pitfalls-ledger.

**No TEST or holdout data was read at any point in this review.**

---

### 1. Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Note |
|---|---|---|---|
| §0 vehicle = vectorised Python on fenced catalog, no Nautilus, no estimand gate | `screen_code/catalog_io.py:63,92` | **PASS** | Only `xen.nautilus.catalog_fence` imported; no `xen.adjudication` anywhere. |
| §0 DESIGN band `[2021-06-29T06:53Z, 2023-03-01Z)` | `config.py:38-39`; `pipeline.py:59,69` | **PASS** | Dates match the INFR-011 fence manifest `analysis_start_utc` exactly. |
| §0 CONFIRM band, verification read only | `config.py:40-41`; `pipeline.py:194,236-242` | **PARTIAL** | Frozen-model scoring is correct, but one DESIGN origin per cell takes its target price at `DESIGN_END` — see **F-7**. |
| §0 TEST `≥2023-12-18` never | `catalog_fence.assert_within_fence`; check `7.1b` | **PASS** | Max target end = `2023-12-17T22:00Z`. Read window upper bound is `train_end_utc`; TEST unreachable by construction. |
| §0 Holdout `≥2025-01-08` never | `catalog_fence.py:110-116` | **PASS** | Fence refuses; check `7.2` max slot_end `2023-12-17T21:00Z`. |
| §0 Symbols = top-25 pin, code-asserted | `universe.py:56,87` | **PASS** | 903 catalog symbols scanned, 286 with data, exact set match to **both** pin files; `UniversePinMismatch` aborts on mismatch. |
| §0 Clocks H1/H4/D1 all primary, full arm suite each | `config.py:58-63`; `run_screen.py:294` | **PASS** | 25 × 3 = 75 cell tasks constructed. |
| §0 Warm-up ≥ max(60 D1, 60 H4, 120 H1) | `config.py:59-68`; `features.py:136-149` | **PASS** | 60 calendar days **and** the per-clock bar count — stricter than the literal max. |
| §0 8 arms × 3 clocks, no post-outcome arm invention | `arms.py:447-455` + `cross_section.py` | **PASS** | All 8 arms present on all 3 clocks for every symbol with data (verified against `metrics_by_cell.parquet`). |
| §0 SPREAD-COST-DISCLOSURE wherever bps appear | `config.py:131-140`; `run_screen.py:247` | **PASS** | Emitted verbatim into `integrity_selfcheck.json`; `summarise.py:173` prints it. No cost is charged anywhere, no net object exists. |
| §0 Battery / derangement applies | `controls.py:70-98,145,167` | **PASS** | 200-seed circular shift, 2000-seed derangement (verified `n_seeds` in `controls.json`). |
| §0 / §5 Future-destroy tripwire | `controls.py:226-267` | **FAIL** | Destroy form changed post-measurement; resulting gate cannot fail. **F-1, F-2, F-3**. |
| §0.1 UNIVERSE-PIN recompute + assert | `universe.py:32-110` | **PASS** | Metric, window, band, N all match the pin verbatim. |
| §0.1 coverage: short-history symbols stay listed, low-n → UNPOWERED, never dropped | `pipeline.py:129-131`; `run_screen.py:120-124` | **PARTIAL** | 3 of 25 pinned symbols emit no metric row at all. **F-9**. |
| §2 conditioning uses only information at origin `t` | `features.py:62-165`; verified independently | **PASS** | Every V-LEVEL feature is a realised measure of bars ≤ i; `oo_move` (origin-known) is emitted for disclosure and is never a regressor. |
| §2 effect-splitting windows non-overlapping | `features.py:115-120` | **PASS** | Targets of consecutive origins are adjacent, not overlapping. |
| §3.1 `open_ts = ts_event − 1m`, slots = truncate(clock) | `catalog_io.py:168-170` | **PASS** | Epoch-multiple flooring gives correct UTC 1h/4h/1d boundaries. |
| §3.1 complete iff last print == slot_end **and** coverage ≥ 48/192/1000 | `catalog_io.py:185-189`; `config.py:59-61` | **PASS** | |
| §3.1 incomplete bars counted, excluded from forecasts | `catalog_io.py:171-191`; `features.py:79` | **PASS** | Counts in `cell_diagnostics.json` (`n_clock_slots` vs `n_complete`). |
| §3.2 `r_i`, `rv_cc`, `rv20`, `parkinson`, `gk` | `features.py:93-108` | **PASS** | Formulas match the design verbatim; GK = `0.5·ln(H/L)² − (2ln2−1)·ln(C/O)²`, zeroed on invalid OHLC. G1 reproduces `rv20` to rel error 0.0. |
| §3.2 `rv_next_i` = rv20 at end of bar i+1 | `features.py:119-120` | **PASS** (literal) | Correct as written; see **F-13** for why the resulting IC ≈ 0.97 is mechanical. |
| §3.2 vs §3.3 target indexing (IN-7) | `features.py:115-118` | **PASS** | The author's resolution is **correct** — see §2 below. |
| §3.3 origin = `slot_end_i`; drop terminal bar | `features.py:143-149` | **PASS** | `is_origin` requires a finite target and a valid next slot. |
| §4 V-PERSIST (autocorr 1/2/3/5, AR(1) half-life, HAR 6/24) | `arms.py:93-135`; `pipeline.py:161-162` | **PASS** | |
| §4 V-LEVEL (EWMA λ=0.94; OLS and ridge α=1.0 on rv20/ewma/park/gk) | `pipeline.py:159-160,201-215`; `arms.py:180-188` | **PASS** | Primary model choice (ridge) is a config addition, not a design pin — **F-16**. |
| §4 V-REGIME 2-state Markov on rv20, rolling-median split | `features.py:184-196`; `arms.py:240-244` | **PASS** | Trailing median window ends at bar i inclusive (causal). Window length not pinned by design; set to the per-clock warm-up count. |
| §4 V-REGIME-HMM 2-state Gaussian, causal expanding fit, decode from data ≤ t | `hmm.py:81-171`; `pipeline.py:218-248` | **PASS** | Forward filtering only — see §3 below. |
| §4 V-MEASURE co-report + pairwise rank corr | `arms.py:277-304` | **PASS** | |
| §4 V-CLOCK session 0-8/8-16/16-24 + DOW, incremental R² over V-LEVEL, not standalone | `pipeline.py:91-97,166-177`; `arms.py:310-362` | **PARTIAL** | Correct construction and the "not a standalone edge claim" note is carried; DOW base labelled wrongly — **F-12**. D1 session degeneracy explicitly noted in-row. |
| §4 V-XS same-timestamp rank across all available symbols, lexical tie-break, terciles | `cross_section.py:25-45` | **PASS** | `rank("ordinal")` after `sort(["slot_start","symbol"])` gives the lexical tie-break. |
| §4 V-TAIL P90/P95 by regime + exceedance | `arms.py:368-400` | **PASS** | |
| §4 multiplicity disclosed, no arm promoted on one cell | `run_screen.py:341-342`; `summarise.py:269-274` | **PASS** | Full per-stratum table emitted; only V-XS emits a POOLED row, labelled disclosure-only. |
| §5 CONTROL TIME-SHUFFLE-PREDICTORS, CIRCULAR_SHIFT, U{1..n−1}, ≥200 seeds 101–300 | `controls.py:145-164` | **PASS** | 200 seeds confirmed in `controls.json`. IN-3 (shift the prediction series with the model frozen) is equivalent to shifting feature rows for a deterministic model — accepted. |
| §5 CONTROL TARGET-LABEL-DERANGEMENT, symbol × calendar-month blocks, zero fixed points, ≥200 seeds | `controls.py:44-98,167-202` | **PASS** | 2000 seeds taken; block form retained and reported per cell; derangement is genuinely fixed-point-free. |
| §5 CONTROL UNCONDITIONAL-MEAN-BASELINE, ΔMAE with CI | `models.py:119-121`; `arms.py:166-176` | **PASS** | Baseline mean comes from the same expanding fit window (no future). |
| §5 bite/MDE +0.25 plant destroyed by both destroys | `controls.py:101-114,205-223` | **PARTIAL** | Plant is checked against the shuffle and the **block** derangement only; the newly-adopted unrestricted form has no bite check of its own. Uses 50 of the 200/2000 seeds. |
| §5 TRIPWIRE TARGET-FUTURE-DESTROY, destroy = "same as label derangement", HARD | `controls.py:26-41,226-267` | **FAIL** | **F-1/F-2/F-3**. |
| §6.1 UNIT-PIN (target already bps, no ATR divisor) | `config.py:142-146` | **PASS** | No normalised effect size is reported anywhere, so the L-21 divisor trap does not arise. |
| §6.2 per-symbol before pooled; pooled disclosure-only | `arms.py:41-63`; `cross_section.py:103-105` | **PASS** | |
| §6.2 date-block bootstrap, blocks 1/3/7, seeds 101/211/307/401/503, 10k resamples | `config.py:98-100`; `stats_core.py:133-204` | **PASS** | Circular over ordered unique UTC dates; block ≥ H holds for all three clocks. |
| §6.2 emit the block/seed grid (IN-4, L-20) | `stats_core.py:112-117` | **FAIL** | Grid computed then discarded; `BootResult.to_dict()` never called. **F-6**. |
| §6.2 OOS protocol: expanding window, 40% initial fit, monthly refit | `models.py:69-126`; `pipeline.py:82-84` | **PASS** | Independently replicated to max abs diff **0.0** — see §3 below. IN-1 (per-cell 40%) is forced; the calendar reading is empty. |
| §6.2 chronological DESIGN thirds | `arms.py:406-444` | **PASS** | Both calendar (literal) and sample thirds emitted; neither dropped. |
| §6.3 band thresholds (IC 0.10/0.05/−0.05; gap +15/10/−15; dates<40; MDE ceilings) | `stats_core.py:277-293,324-337` | **PASS** | Primary `band_label` is the literal design rule, unmodified. A fifth residual label `INDETERMINATE` covers cases the design's four bands do not span. |
| §6.3 disclosure companion `band_label_detected` | `stats_core.py:296-321,340-355` | **PASS (as disclosure)** | Separate column, never overwrites `band_label`; both counted side by side in `summarise.py:182-185`. But see **F-4** — under the literal rule the DESIGN band is 42/45 UNPOWERED, so the disclosure column carries the whole read. |
| §6.4 PASS/STOP clauses computed, operator decides | `summarise.py:112-162` | **PARTIAL** | Computed under both label rules and both thirds definitions — honest. But clauses 1 and 3 are unsatisfiable under the literal frozen design. **F-4**. |
| §6.5 MDE(IC) ≈ 1.5/√n_eff | `stats_core.py:267-269` | **PASS** | Implemented exactly; the prospective power estimate (500+ dates) did not materialise (median 99–102). |
| §7.1 every query TRAIN; max target ts < train_end | `run_screen.py:169-181` | **PASS** | |
| §7.2 no row ≥ holdout_start | `run_screen.py:182-185` | **PASS** | |
| §7.3 CONFIRM not in estimation coefficients | `run_screen.py:187-198` | **PARTIAL** | Check compares origin timestamps only; it cannot see the one boundary target price per cell. **F-7**. |
| §7.4 features ≤ origin; target next bar only | `run_screen.py:200-207` | **PARTIAL** | Asserts `target_slot_start ≥ slot_end`, which is the entry leg only; the exit leg is guaranteed by construction, not by the check. |
| §7.5 derangements have 0 fixed points | `run_screen.py:209-217` | **FAIL (vacuous)** | Checks a hardcoded string literal. The property does hold (`controls.py:70-98`). **F-10**. |
| §7.6 write `integrity_selfcheck.json` with all asserts PASS | `run_screen.py:372-384` | **PASS** | Present, `all_pass = true`. |
| §8 G1 / G2 / G3 golden traces | `golden_traces.py:26,56,86` | **PASS** | See §4 below. |
| §9 deliverables | `results/` | **PASS** | All listed artifacts present except `screen.md` / `analysis.md`, which are later pipeline stages. |
| §10 HARD: holdout/TEST untouched, causal lag, tripwire, self-check | — | **PARTIAL** | Three of four HARD items pass cleanly; the tripwire does not. |
| §10 no direction, no combination, no XENA | `screen_code/` | **PASS** | Verified by scan — no directional or combination logic exists. |
| RAW §3 Step A / §5.1 axes (persistence, level, regime, realised, calendar, cross-sectional, tail) | all 8 arms | **PASS** | No axis dropped. |
| RAW §6 refusals; chapter-06 governance §3 | — | **PASS** | No breakout device, no win-rate metric, no combination, no TEST/holdout, no family status change from code. |
| SPDR lane: no local accounting primitives (L-18) | scan of `screen_code/` | **PASS** | No P&L, position, fee, equity or commission primitive exists. Every metric is a forecast-skill or magnitude object. |
| SPDR lane: matched control + seed battery (L-19) | `controls.py` | **PASS** | 200 / 2000 / 50-seed batteries with percentile reads; no single-twin control. |
| SPDR lane: dependence-matched uncertainty, block ≥ H | `stats_core.py:133-204` | **PASS** | |
| Pitfalls ledger P-01…P-20 | — | **PASS** | Nothing here re-runs a closed dead end. V-XS re-screens the cross-sectional axis on a *magnitude* endpoint, which P-06 explicitly permits. |

---

### 2. Causality — independent verdict on IN-7

**The author's resolution is correct and the implemented target is genuinely in the future.**

Design §3.2 defines `abs_oo_i = 1e4·|O_{i+1}/O_i − 1|` and calls it "target for bar i forecast".
Design §3.3 says "Target = next bar's `abs_oo`". These cannot both hold. Taking §3.2 literally,
the target for an origin at `slot_end_i` is a function of `O_i` (long known) and `O_{i+1}` (the
price at the origin instant, since `slot_start_{i+1} == slot_end_i`) — i.e. **already realised at
the origin**. Regressing bar-i realised measures on that quantity is not a forecast; it would
produce a large, meaningless IC. §3.3 and §7.4 ("targets use next bar only") force the other
reading, which is what `features.py:117-118` implements:

```
target_abs_oo_i = oo_move_{i+1} = 1e4·|O_{i+2}/O_{i+1} − 1|
```

Origin at `slot_end_i` = `slot_start_{i+1}`; the target spans exactly the bar that begins at the
origin and is entered at that bar's open. Strictly one clock bar ahead. Confirmed empirically in
G2: for the same ETHUSDT H1 row, `target_abs_oo` = 24.09 bps while the origin-known variant
`oo_move` = 7.65 bps — different objects, and only the origin-known one is discarded.

I traced the index arithmetic myself rather than trusting the docstrings. Every V-LEVEL regressor
(`rv20`, `ewma_vol`, `parkinson`, `gk`) and every HAR regressor is a realised measure of bars ≤ i;
`rv20` at index i is `sqrt(mean(r²))` over `r_{i-19}…r_i`, first finite at i = 20 (r[0] is NaN, so
the window at i = 19 propagates NaN). The EWMA recursion (`features.py:38-49`) is strictly
backward. Calendar attributes are taken from the *forecast* bar i+1 but are deterministic and
known at the origin. `oo_move` is emitted but never enters a feature matrix.

**Caveat worth stating in the write-up:** the "known at origin" status of `O_{i+1}` is exact only
if the origin instant is the first print of bar i+1. In this construction the model is fitted on
targets that begin at the origin instant, so the entry price is contemporaneous with the decision.
That is the correct one-step-ahead convention for an open-to-open magnitude object and is what the
design asks for — but it means the screen assumes zero decision latency, which is normal for a
characterisation screen and must not silently carry into any later tradability claim.

---

### 3. Band discipline, walk-forward and HMM — verification performed

**Walk-forward (models.py:69-126).** I reimplemented the expanding-window monthly-refit loop from
scratch and compared against the emitted `pred__vlevel_ridge__target_abs_oo` for BTCUSDT H4 DESIGN
(n = 1013 origins, start = 405, 608 OOS rows): **max abs diff = 0.0**. A deliberately leaky
variant (fit on `X[:b]` instead of `X[:a]`, i.e. including the rows it predicts) differs by up to
20.4 bps, so the test discriminates. `fit_linear(X[:a], y[:a])` predicting rows `[a, b)`: **no
off-by-one; no fit window contains a row it predicts.** Standardisation `mu`/`sd` are computed
inside the fit window only. Initial-fit fraction is 0.400 ± 0.001 for every cell.

**DESIGN/CONFIRM separation.** All fitting happens on `cell.design` only (`pipeline.py:142-215`);
CONFIRM is scored by `final` (fitted on all DESIGN rows) and a DESIGN-mean baseline. Check 7.3
verifies `final_fit_end_ts ≤ DESIGN_END` for all 855 model entries — 0 violations. Rolling
statistics (rv20, EWMA, rolling median) are built once over `[DESIGN_START, CONFIRM_END)` but only
ever look backwards, so DESIGN rows never see CONFIRM bars.

**The one boundary defect (F-7).** `_split_bands` (`pipeline.py:69`) admits a DESIGN origin when
`target_end ≤ DESIGN_END`, where `target_end` is the *close* of the target bar. But the
open-to-open target needs the open of the bar **after** the target bar. Verified on SOLUSDT H1:
the last DESIGN origin is `2023-02-28T22:00Z`, its target bar is `[23:00, 00:00)`, and its target
is `|O(2023-03-01T00:00Z)/O(23:00Z) − 1|` — the numerator is the first CONFIRM print. Exactly one
row per cell (45 rows, ≈0.06 % of DESIGN rows); it enters the final-model fit that is then applied
to CONFIRM. Numerically irrelevant, literally a §7.3 breach, invisible to check 7.3. I confirmed
by a shifted-index scan that **no other** DESIGN row's target price lands at or after
`DESIGN_END` (0 of 79 977).

**HMM causality (hmm.py).** Parameters come from `fit_gaussian_hmm(x[:a])` — strictly prior data.
Decoding uses `filter_high_prob`, which runs `_forward` alone (`hmm.py:134-136`); `_backward` is
called only inside Baum–Welch, on the past-only fit window. `alpha[t]` depends on `x[0..t]` by the
recursion's prefix property, so `filter_high_prob(x[:b])[a:b]` equals what a real-time filter would
have produced at each t. Rows before `start_idx` carry NaN → state −1 → excluded from every arm.
For CONFIRM, the DESIGN-frozen parameters filter the concatenated series and only the CONFIRM tail
is taken. **No smoothed/backward pass reaches a decoded state.** Confirmed.

---

### 4. Golden-trace diff (expected from the design, not from the run)

| Trace | Design expectation (§8) | Implemented logic | Verdict |
|---|---|---|---|
| **G1** | BTCUSDT H4, first complete bar after 2022-09-14T00:00Z with full rv20 history; recompute `rv20` by hand from 20 prior H4 log closes; match to 1e-9 rel | `golden_traces.py:26-53` selects `slot_start ≥ 2022-09-14T00:00Z`, recomputes `sqrt(mean(log(C_t/C_{t-1})²))` over the 20 returns ending at i. Emitted: 21 closes, 20 log returns, `rv20_manual = rv20_screen = 0.02021971063148725`, rel error **0.0** | **PASS** — I re-derived the window bounds from the design text; they match. Note the "hand" recompute reuses the same aggregated bar frame, so it validates the rolling formula, not the aggregation. |
| **G2** | ETHUSDT H1, one V-LEVEL origin; list `{rv20, ewma, park, gk}`; confirm none use the target bar's open-to-open | `golden_traces.py:56-83` emits the vector plus three boolean checks. Origin `2023-01-09T06:00Z`, target bar starts `07:00Z`, `target_abs_oo` 24.09 bps vs origin-known `oo_move` 7.65 bps | **PASS** — this is the trace that makes IN-7 auditable, and it does. |
| **G3** | SOLUSDT, one time-shuffle seed 101; fixed points N/A; verify the IC changes vs live | `golden_traces.py:86-106`; live 0.2598 → shuffled −0.0292 at shift 190, n = 611 | **PASS** — the design only asks that the IC move. The check `live != shuffled` is weak but is exactly the design's own bar. |

---

### 5. The tripwire re-specification — reasoned judgement (item 5)

This is the single highest-risk judgement in the work and it deserves a plain answer in three
parts: was the diagnosis right, is the new rule a legitimate reading, and is the gate weaker.

**The diagnosis is right.** Design §5 pins the tripwire's destroy to "another symbol-month
deranged target (same as label derangement)" and asks it to *collapse*. Deranging targets inside
calendar-month blocks preserves every month's target distribution and therefore preserves the
entire **between-month** component of the association. Volatility level structure is slow-moving:
a high-vol month has both high forecasts and high realised moves, so a within-month shuffle leaves
that co-movement untouched. The null therefore cannot be centred at zero, and its median rises
with the strength of the true relationship. The artifacts confirm this quantitatively: across all
90 powered cells the block-restricted null has median IC **0.109** against a median live IC of
**0.259** — the null retains a median **42.9 %** (max 178 %) of the live value. A collapse
adjudication on that form flags the cells where the hypothesis is *most* true. The 33/90 FAIL the
author saw was an artifact of the destroy's incompleteness, not evidence of leakage. I would have
reached the same diagnosis.

**The re-classification has independent governance support.** L-32 (INFR-016) splits destroy
controls by class: `future_destroy` (edge survives destroying FUTURE information ⇒ acausal leak)
stays HARD; `within_sample_attribution` (timing scrambled inside the sample, entries still causal)
becomes a **report layer** whose collapse fraction is reported for the operator to judge, never a
hard verdict. A within-month derangement is squarely the second class. So demoting the block form
to the design's own §5 CONTROL — read in the design's stated direction, "live IC above null p95"
(68/90 cells, median one-sided p = 0.0005) — is the *correct* classification under standing
programme lessons, not a convenience.

**But the new gate is strictly weaker, and it is non-binding by construction.** For any fixed
prediction vector, an unrestricted derangement of the target makes the expected Spearman
correlation zero; with n ≈ 10²–10³ observations and 2000 seeds, the null median cannot land far
from zero. Measured: unrestricted null median **−0.00022**, **max |median| 0.0052** across all 90
cells, against a ceiling of 0.05 — an order of magnitude of headroom. 90/90 PASS, and the gate
could not have failed. It is a sanity check that the permutation machinery works, not a leak test.
Worse, *neither* destroy form is capable of detecting the failure it names: if the forecast
secretly contained the outcome, destroying the outcome would still collapse the correlation. A
target-side destroy cannot distinguish leak from skill. The screen therefore ships with **no
working future-destroy tripwire**, and causal validity rests entirely on the construction
(features ≤ i, target = bar i+1) — which I verified independently, and which holds — plus the
`§7.4` assert. The operative non-vacuity device in this screen is the **predictor-side** circular
shift, which does discriminate (live outside the null central 90 % in 72/90 cells, with a
notably wide null: median p95 = 0.169).

**Where it fails governance.** The change was made *after* seeing the first run's results, to a
clause the design marks HARD, and it moves the gate from discriminating (33 failures) to
unfailable (0 failures, provably). Under L-23 that requires a dated amendment declaring
DIRECTION: **LOOSER** with a running directional count; under the programme's
deviation-handling rule it is a design amendment plus full rerun, not a note. What was actually
recorded is an "interpretation note" (IN-8) that exists only in `results/compliance_trace.md`
prose, under a header that states **"Deviations: none"**, while `design.md` §5 still pins the
block form and carries no amendment. Additionally the two new thresholds (`0.05` absolute,
`0.50` retention) are asserted, not derived — L-24 (F06) names exactly this, and `0.50` is the
same asserted retention figure that lesson was written about.

**What I would accept.** The substance of the change; the block form retained and reported; both
envelopes in `controls.json`. What must change is the paperwork and the framing: record it as a
DEVIATION with direction LOOSER and operator sign-off, and state in `screen.md`/`analysis.md`
that SPDR-012 has no working leak tripwire and that the 42.9 % between-month retention is a
**first-class result about what the IC is made of**, not a control footnote.

---

### 6. Governance & boundary checklist

| Check | Evidence | Result |
|---|---|---|
| TRAIN-only fence, code-asserted | `catalog_fence.assert_within_fence`, checks 7.1/7.1b/7.2 | **PASS** |
| Holdout unreachable | Read upper bound = `train_end_utc`; fence refuses `band != TEST` past holdout | **PASS** |
| 0 counted TEST reads, 0 slots, no family status change | no registry write in `screen_code/` | **PASS** |
| No local accounting primitives (L-18) | scan: no pnl/equity/position/fee/commission symbol anywhere | **PASS** |
| No tradability / deployability / net claim | `PROHIBITED_CLAIMS` declared; no cost applied; no net object exists | **PASS** |
| Spread disclosure `UNAVAILABLE_NOT_CHARGED` / `spread_rt_bps: null` / `PARTIAL_FEES_FUNDING_ONLY` | `config.py:131-140` → `integrity_selfcheck.json` | **PASS** |
| No direction or combination logic | scan of all 13 modules | **PASS** |
| Matched control + seed battery (L-19) | 200 / 2000 / 50 seeds, percentile reads | **PASS** |
| Derangement destroy is fixed-point-free (L-28) | `controls.py:70-98` regenerates until zero fixed points, raises after 64 attempts | **PASS** |
| Per-stratum reporting, multiplicity disclosed (L-03) | full per-cell table; POOLED labelled disclosure-only | **PASS** |
| Block ≥ H dependence-matched CI | date blocks 1/3/7 days ≥ every clock's horizon | **PASS** |
| CI hardening — seed battery + block sweep emitted (L-20) | grid computed, **not emitted** | **FAIL** (F-6) |
| Amendment-direction ledger (L-23) | no amendment recorded for the tripwire re-spec | **FAIL** (F-1) |
| Tripwire thresholds derived, not asserted (L-24 F06) | 0.05 / 0.50 asserted | **FAIL** (F-3) |
| Arbitrary value gate wired to auto-decide (L-32) | `verdict: PASS/FAIL` on asserted thresholds; mitigated because `future_destroy` legitimately stays HARD | **PARTIAL** (F-3) |
| Unit pin (L-21) / conversion pin | no normalised effect size reported; target already in bps | **N/A — PASS** |
| One BacktestNode per process (L-31) | no Nautilus engine used | **N/A** |
| XENA clauses | not a XENA run | **N/A** |
| No dead end re-run (pitfalls ledger) | V-XS uses a magnitude endpoint, permitted under P-06 | **PASS** |
| Code↔artifact provenance | `screen_code/` and `results/*.json` untracked; module mtimes postdate the earlier artifact set | **OBSERVATION** (F-17) |

---

### 7. Findings

**F-1 — MAJOR — post-measurement change to a HARD clause recorded as "no deviation"**
`screen_code/controls.py:26-41,226-267`; `screen_code/config.py:3,150-227`;
`results/compliance_trace.md:7,118`; `design.md` §5 (unamended).
Design §5 pins the tripwire destroy as "another symbol-month deranged target (same as label
derangement)". The code adjudicates an **unrestricted** derangement instead. The change was made
after the first run produced 33/90 FAIL. It is recorded as interpretation note IN-8, which exists
only in the prose compliance trace, beneath the header "**Deviations: none**", while
`config.py`'s machine-readable `INTERPRETATION_NOTES` stops at IN-6 and `design.md` carries no
amendment. **Failure scenario:** a future reader reconciling `design.md` against the artifacts
concludes the pinned block-restricted tripwire passed, when in fact it was replaced by a different
and looser test. **Required fix:** dated amendment in `design.md` §5 declaring DIRECTION: **LOOSER**
with the running directional count (L-23), operator sign-off recorded, IN-8 re-labelled DEVIATION,
and the "Deviations: none" header corrected.

**F-2 — MAJOR — the re-specified HARD tripwire cannot fail**
`screen_code/controls.py:226-249`; `results/controls.json`.
Under an unrestricted derangement, `E[Spearman(pred, y_deranged)] = 0` for any fixed `pred`.
Measured across all 90 powered cells: null median **−0.00022**, max |median| **0.00522**, against
`TRIPWIRE_ABS_CEILING = 0.05`; verdict 90/90 PASS. **Failure scenario:** the screen reports a
green HARD leak gate that carries no information, and a genuine look-ahead defect would pass it —
indeed *no* target-side destroy can detect one, because destroying the target removes the
association whether or not the predictor leaked. **Required fix:** state in `screen.md` and
`analysis.md` that the future-destroy tripwire is a null-centring sanity check, not a leak test;
name the predictor-side circular shift as the operative non-vacuity device; and rely on the
construction-level causality argument (which this review verified independently) for the L-01
claim.

**F-3 — MAJOR — tripwire thresholds asserted, not derived**
`screen_code/controls.py:40-41,236-238`.
`TRIPWIRE_ABS_CEILING = 0.05` and `TRIPWIRE_RETAIN_CEILING = 0.50` appear in no design document
and are wired to a boolean `verdict` field. L-24 (F06) requires tripwire retention thresholds to
be derived from the destroy's own mechanics; `0.50` is the same asserted retention number that
lesson was written about (EXP-025). L-32 permits `future_destroy` to stay HARD but still forbids
an arbitrary bar wired to auto-decide. **Required fix:** derive the ceiling from the null's own
dispersion (e.g. the seed-battery p99 of the unrestricted null), or convert the tripwire to a
report layer with `observed / ideal / interpretation` and no `pass` field.

**F-4 — MAJOR — the frozen DESIGN band is under-powered by the design's own rule; §6.4 is unsatisfiable as written** *(design defect — route to `quant-designer`, not to the developer)*
`design.md` §0/§6.3/§6.4/§6.5; `stats_core.py:267-293`; `results/metrics_by_cell.parquet`.
The DESIGN band `[2021-06-29, 2023-03-01)` mostly predates the catalog's trailing history cap
(earliest 1m bar 2022-07-15 for all but MATICUSDT). Realised unique dates per cell: median
**99–102** on DESIGN vs **286–292** on CONFIRM. §6.3 declares a cell UNPOWERED when
`MDE = 1.5/√n_dates > 0.10`, i.e. below 225 dates — so **42 of 45** DESIGN cells are UNPOWERED and
only 3 SUPPORTED, while **42 of 45** CONFIRM cells are SUPPORTED. §6.4 clause 1 ("SUPPORTED for
≥10 of 25 symbols") cannot be met on DESIGN. §6.4 clause 3 ("sign stable in ≥2/3 DESIGN thirds")
also cannot: the first literal calendar third is entirely empty, so 39 of 45 cells have exactly
**one** non-empty calendar third (`n_thirds_positive_calendar ≤ 1`). **Failure scenario:** the
downstream analyst quietly reads the recommendation off `band_label_detected` and `thirds_sample`
— two non-frozen disclosure variants — or off the CONFIRM band, which §0 designates a verification
read; either route produces a PASS that the frozen design does not license. **Required fix:**
operator decision, before `analysis.md` is written, on exactly which band and which label rule the
§6.4 recommendation is computed from, recorded as a dated amendment. The screen code needs no
change; the honest emission of both readings is the right behaviour.

**F-5 — MAJOR — the three most consequential interpretation notes are not in the machine-readable record**
`screen_code/config.py:150-227`; `results/integrity_selfcheck.json.interpretation_notes`;
`results/compliance_trace.md:7,117-119`.
`INTERPRETATION_NOTES` contains IN-1…IN-6 only; the self-check therefore mirrors IN-1…IN-6 only
(verified). IN-7 (target indexing), IN-8 (tripwire re-spec) and IN-9 (band UNPOWERED disclosure) —
the causality resolution, the HARD-clause change and the band-label disclosure — exist solely in
the prose trace. The trace also miscounts them ("**Six** ambiguity resolutions (IN-1…IN-7)"; there
are nine). **Required fix:** add IN-7/IN-8/IN-9 to `config.py:INTERPRETATION_NOTES` so they land in
`integrity_selfcheck.json`, and correct the count.

**F-6 — MAJOR — the block × seed CI grid is computed and discarded**
`screen_code/stats_core.py:112-117,190`; `screen_code/config.py:200-201`;
`results/compliance_trace.md` §5.
`BootResult.grid` holds the 15 (block × seed) CI cells, but `BootResult.to_dict()` — the only
producer of the `block_sensitivity` key — is never called anywhere in the codebase (verified by
grep). No artifact contains `block_sensitivity`. IN-4 and the compliance trace both assert "full
15-cell grid emitted per metric". **Failure scenario:** the min/max envelope that assigns every
band label cannot be audited, and L-20's block-sensitivity requirement is unmet — a cell whose
`ci_low > 0` rests on one lucky block length is indistinguishable from a robust one. **Required
fix:** serialise `BootResult.grid` alongside each bootstrapped metric (a JSON sidecar keyed by
`arm|symbol|clock|band|metric` is sufficient), or correct both claims.

**F-7 — MINOR — one DESIGN origin per cell takes its target price from the first CONFIRM print**
`screen_code/pipeline.py:69`.
The DESIGN filter requires `target_end ≤ DESIGN_END`, where `target_end` is the *close* of the
target bar; but the open-to-open target needs the open of the bar **after** the target bar.
Verified on SOLUSDT H1: last DESIGN origin `2023-02-28T22:00Z`, target bar `[23:00, 00:00)`,
target = `|O(2023-03-01T00:00Z)/O(23:00Z) − 1|`, and `O(2023-03-01T00:00Z)` is the first CONFIRM
bar's open. 45 rows total (1 per cell, ≈0.06 % of DESIGN rows); each enters the final-model fit
applied to CONFIRM. All other DESIGN rows are clean (0 of 79 977 by a shifted-index scan).
Numerically immaterial, but a literal §7.3 breach that check 7.3 cannot see (it compares origin
timestamps, not target price timestamps). **Required fix:** `target_end + span ≤ d_end`, and
extend check 7.3 to the target's exit timestamp.

**F-8 — MINOR — contiguity claim is wrong**
`results/compliance_trace.md` IN-5 ("measured ≈1.00"); `screen_code/features.py:122-125`.
Actual `target_contiguous` means: DESIGN median **0.949**, min **0.636** (1000LUNCUSDT H4);
CONFIRM median 0.979, min **0.598** (1000LUNCUSDT D1). So 5–36 % of targets span a longer-than-
clock horizon, contradicting §1's stated "horizon = next completed H1/H4/D1 bars". I tested
whether this manufactures the result: primary OOS IC on the contiguous subset (median **0.237**)
is essentially identical to IC on all rows (median **0.245**), and gap rows tend to score *lower*
— so the confound does not inflate the headline. **Required fix:** correct the claim and state the
measured contiguity; optionally report the contiguous-subset IC alongside (it is reassuring).

**F-9 — MINOR — 3 of 25 pinned symbols emit no metric row**
`screen_code/pipeline.py:129-131`; `run_screen.py:120-124`; `results/metrics_by_cell.parquet`.
TIAUSDT, PYTHUSDT and 1000RATSUSDT have zero origins in both bands and appear nowhere in the
per-cell metric table (22 real symbols + POOLED). Design §0.1 and `cf-voldir-001.md` §5.2 require
"cells with too few dates are **UNPOWERED**, never silently dropped from reporting". They are
disclosed in `cell_diagnostics.json` (status `NO_DESIGN_HISTORY`) and in `summarise.py:34-50`'s
coverage table, so this is a partial, not a total, omission. **Failure scenario:** §6.4 clause 1
counts "≥10 of **25** symbols" against a table whose denominator silently became 22. **Required
fix:** emit an explicit `UNPOWERED` placeholder row per (arm, symbol, clock, band) for zero-origin
cells, or state the denominator adjustment wherever the clause is evaluated.

**F-10 — MINOR — integrity check 7.5 is vacuous**
`screen_code/run_screen.py:209-217`.
The check tests `destroy_form == "DERANGEMENT"`, a hardcoded string literal set at
`controls.py:192`. It cannot detect a fixed point. The property does hold — `derange()`
(`controls.py:70-88`) repairs and re-verifies until zero fixed points and raises after 64 attempts,
and `derange_within_blocks` asserts (`controls.py:96`) — but assertions are stripped under
`python -O`. **Required fix:** count actual index-level fixed points across the seed battery and
report the number (expected exactly 0) in the self-check detail.

**F-11 — MINOR — mixed conservatism between the CI envelope and the SE**
`screen_code/stats_core.py:196-203`; `stats_core.py:324-337`.
`ci_low`/`ci_high` take the **worst case** over the 15 (block × seed) grid — conservative, and
correctly disclosed as IN-4 — but `se` takes the **median** SD over the same grid, and `se` drives
the gap-band UNPOWERED test via `mde_from_se`. A cell whose worst-block SD would push MDE above the
15 bps ceiling can still be labelled SUPPORTED. Separately, the min/max envelope is not a 95 %
interval and should not be described as one (design §6.3 says "date-block 95 % CI"). **Required
fix:** use the same grid statistic for both, or state explicitly that the reported interval is a
conservative envelope and the SE is a median.

**F-12 — MINOR — day-of-week base label is wrong**
`screen_code/features.py:133`; `screen_code/arms.py:361`; `screen_code/pipeline.py:37`.
`dow = ((tgt_sec // 86400) + 4) % 7` with 1970-01-01 = Thursday yields a **Sunday = 0**
convention (Thursday → 4). The V-CLOCK residual rows are annotated `"0=Monday"` and the dummy
comment says `base = Monday`. Every V-CLOCK day-of-week row is therefore mislabelled by one day.
Values are correct; only the label is wrong. **Required fix:** change the note to `0=Sunday` (or
re-index).

**F-13 — OBSERVATION — the `rv_next` target is mechanically predictable**
`screen_code/features.py:119-120`; `screen_code/arms.py:156-158`.
`rv_next_i = rv20_{i+1}` shares 19 of its 20 return terms with the `rv20` feature at origin i.
Median OOS IC: **0.968 (DESIGN) / 0.978 (CONFIRM)**. The row carries the correct note ("rv20
windows overlap 19/20 with this target → mechanical persistence, not forecast skill"), which is
exactly right — but it is emitted under the same `oos_ic` metric name as the primary object and
will be quoted out of context if the analyst is not explicit. This is faithful to design §3.2 as
written; it is a design property, not a code fault.

**F-14 — OBSERVATION — the substantive read the controls already contain**
`results/controls.json`.
Two numbers belong in the headline, not in a controls appendix. (a) The design's block-restricted
derangement — retained as the §5 CONTROL — has median null IC **0.109** against median live IC
**0.259**: roughly **43 %** of the reported V-LEVEL skill survives destroying within-month pairing,
i.e. is between-calendar-month level structure ("this month is a high-vol month") rather than
within-month ranking skill. (b) The circular-shift null is wide — median p95 **0.169** — because
two strongly persistent series correlate at arbitrary offsets; live sits outside the central 90 %
in **72 of 90** cells. Both bear directly on how much of the vol "reliability" is usable for later
conditioning.

**F-15 — OBSERVATION — CONFIRM is the only band for 7 symbols**
`screen_code/pipeline.py:129-131`; `run_screen.py:120-124`.
ORDIUSDT, 1000BONKUSDT, BLURUSDT, 1000PEPEUSDT, SEIUSDT, WLDUSDT and BIGTIMEUSDT have zero DESIGN
origins but substantial CONFIRM origins (151–4 793). They emit the non-fitted arms (V-PERSIST,
V-REGIME, V-MEASURE, V-TAIL, V-XS) on CONFIRM only. Nothing there verifies a DESIGN-derived
object — CONFIRM is their estimation band. Worth one caveat line so no CONFIRM-only regime gap is
read as a replication.

**F-16 — OBSERVATION — the band-carrying V-LEVEL model is a config choice**
`screen_code/config.py:82-86`.
Design §4 lists EWMA, OLS and ridge for V-LEVEL; §6.3 says "V-LEVEL primary" without naming one.
`V_LEVEL_PRIMARY_MODEL = "ridge"` is declared in config with a comment asserting it predates any
outcome read. `screen_code/` is untracked, so that cannot be verified from git. It is not
outcome-material: DESIGN median OOS IC is ridge 0.2014, OLS 0.2012, EWMA 0.1710, and all three are
emitted.

**F-17 — OBSERVATION — code/artifact provenance is unpinned**
`git status`: `screen_code/`, `analysis_code/` and five `results/*.json` are untracked. Module
mtimes (`controls.py`, `run_screen.py` at 15:12 local) postdate the 15:10 artifact set; a rerun
completed at 14:22 UTC during this review and regenerated everything. All figures quoted above come
from that completed run. Nothing pins code to artifacts. **Suggestion:** commit `screen_code/` and
the results manifest before `analysis.md` is written, so the analyst's read is reproducible.

---

### 8. Verdict

**REVISE.**

Nothing here reaches REJECT. Causality is sound and I verified it independently rather than
trusting the docstrings: the walk-forward reproduces bit-for-bit with no off-by-one, the HMM
decodes by forward filtering only, the target is genuinely one clock bar ahead, TEST and holdout
are unreachable, the universe pin recomputes exactly over 903 catalog symbols with a hard-fail
path, all 8 arms × 3 clocks are present, and there is no P&L primitive, no direction logic and no
tradability claim anywhere.

The revisions required before `analysis.md` is written:

1. **`design.md` §5** — record the tripwire destroy-form change as a dated **DEVIATION**, direction
   **LOOSER**, with operator sign-off; correct `compliance_trace.md`'s "Deviations: none" header.
   (F-1)
2. **`screen.md` / `analysis.md`** — state plainly that the future-destroy tripwire is a
   null-centring sanity check that cannot fail, that no target-side destroy can detect a
   look-ahead leak, and that causal validity rests on the verified construction. (F-2)
3. **`controls.py:40-41`** — derive the tripwire thresholds or convert the tripwire to a report
   layer with no `pass` field. (F-3)
4. **Operator decision, then a dated amendment** — which band and which label rule the §6.4
   PASS/STOP recommendation is computed from. As frozen, §6.4 clauses 1 and 3 are unsatisfiable on
   the DESIGN band. No recommendation should be written until this is settled. (F-4)
5. **`config.py:INTERPRETATION_NOTES`** — add IN-7/IN-8/IN-9 so they reach
   `integrity_selfcheck.json`; fix the "six … (IN-1…IN-7)" miscount. (F-5)
6. **`stats_core.py` / emission** — emit the 15-cell block × seed grid, or withdraw the claim that
   it is emitted. (F-6)
7. **`pipeline.py:69`** — tighten the DESIGN filter to `target_end + span ≤ d_end` and extend check
   7.3 to the target exit timestamp. Full rerun (cheap: 561 s wall). (F-7)
8. **`compliance_trace.md` IN-5** — replace "≈1.00" with the measured contiguity (median 0.949,
   min 0.636); optionally add the contiguous-subset IC, which is reassuring. (F-8)
9. Minor: zero-origin placeholder rows (F-9), non-vacuous fixed-point check (F-10), consistent
   grid statistic for CI vs SE (F-11), `0=Sunday` label fix (F-12).

Items 1–6 are governance and disclosure; item 7 is the only code correction that touches a number,
and it touches 45 rows out of 232 798. The screen's substantive result — that a large share of the
measured volatility "reliability" is between-calendar-month level structure, and that the frozen
DESIGN band is under-powered by the design's own rule while the verification band is not — is
already sitting in the artifacts and should lead the write-up.
