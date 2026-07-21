# INFR-020 — QA review (append-only)

## QA run 1 — 2026-07-21T16:33Z — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time: `docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md` (M);
`python/experiments/INFR-020/` and `python/experiments/SPDR-009/` untracked.

**Stage: DESIGN-ONLY.** `python/experiments/INFR-020/code/` is empty. This is a design-fidelity +
governance review against ckpt-015 §D6, Addendum v1.1, SIGNAL-SIGNED A5/A7/A8, and the existing
`xen.sigbar` / `xen.bar_aggregator` code the design makes factual claims about. Clauses that can only
be checked against an implementation are listed in **§QA-run-2 trace items** and are NOT passed here.

**Verdict: REVISE**
**FAILING_ARTIFACT:** `python/experiments/INFR-020/design.md`
**REQUIRED_SKILL:** `quant-designer` (all issues are design defects; none are implementation defects,
because there is no implementation)

---

### 1. D6 discharge trace (ckpt-015 §D6.4 → INFR-020)

| D6 requirement | INFR-020 clause | Verdict | Notes |
|---|---|---|---|
| D6.4.1 baselines per LTF timeframe (5m→288×7, 15m→96×7, 1h→24×7), frozen + hash-pinned | §2 W1, §7 artifacts | **MATCHES (premise defective)** | Grid arithmetic correct. The *coverage premise* attached to it is empirically false — Issue 3. |
| D6.4.2 class thresholds per (symbol, timeframe) by the unchanged frozen p90/p10 rule | §2 W3 | **MATCHES** | `classes.derive_thresholds` is timeframe-agnostic (reads `<metric>_resid` columns only); calling it unmodified is verified feasible — `classes.py:53-92`. |
| D6.4.3 1h/4h clock-aligned UTC, operational anchors, no race, funding coincidence = property | §2 W4 + ANCHOR CERTIFICATION block | **DEVIATES** | Certification is well-formed and VT-4(g) machine-checks the edge-bearing ban, but "selection contrast is UNMEASURED" is false for half of A-H4 — Issue 4. |
| D6.4.4 IB = 15 min wall-clock as LTF bars, min one bar; D1 reproduces frozen L=15; D4 deviates at 60 min | §2 W4 IB table | **MATCHES** | D1 15×1m ⇔ `mins_since < 15` in `sessions.py:296`, identical to the frozen path; A3 tests it. D4 deviation disclosed. Secondary comparability gap — Issue 8. |
| D6.4.5 zone scale = prior HTF session range; τ re-picked per pair on counts only; **D1's `0.25 × ib_width` retained as a pre-registered sensitivity** | §2 W5 | **MISSING (partial)** | W5 defines only the prior-session-range scale. The retained D1 `ib_width` sensitivity has no emitted census — Issue 6. |
| D6.3 invariant: HTF/LTF govern framing + detection ONLY; every price-path and volume-at-price measurement stays on 1-minute bars | §0, §2 W5, §3 | **MISSING** | The invariant is never restated in INFR-020, and W5 computes distance-to-structural-level without stating the levels are built from prior-HTF-session **1-minute** bars — Issue 5. |
| D6 "no forward outcome" (implicit; explicit at SPDR-009 QA-1 I-15) | §0, §3 `check_no_outcome_columns`, §4 A7 | **MATCHES (weak enforcement)** | No outcome is computed anywhere in the design or in `agg_trace.py` (verified line by line). Enforcement mechanism is name-based only — Issue 1. |

### 2. Factual claims about existing code — independently verified

| Design claim (§ref) | Code (file:line) | Verdict | Evidence |
|---|---|---|---|
| §1.1 `fit_seasonal_baseline` hard-wired to 1440×7 and **raises** otherwise, cited `baselines.py:166` | `python/src/xen/sigbar/baselines.py:166-169` | **CONFIRMED** | `if out.height != FULL_GRID_CELLS: raise RuntimeError(...)`, `FULL_GRID_CELLS = 1440*7` at :45. |
| §1.1 "There is no timeframe parameter" | `baselines.py:94-100` | **CONFIRMED** | Signature is `(df, metric, *, time_col, min_cell_obs)`. |
| §1.1 (unstated) a second 1440-hard-wired guard exists | `baselines.py:68-83` `assert_seasonal_keys_valid` | **DESIGN GAP** | Raises unless `mod ∈ [0,1439]`. Must be generalised too; design never names it — run-2 trace item T3. |
| §1.2 `aggregate_ohlc` requires `Symbol`/`CloseTime`/`TickVolume`, sums TickVolume only; `Volume`/`BuyVolume`/`SellVolume`/`NTrades` pass through unrepresented | `bar_aggregator.py:86-89, 96, 106-117, 133-137` | **CONFIRMED** | `required` set excludes the signed columns; `output_cols` is a fixed list, so signed columns are **silently dropped**, not raised on. "Silently destroy the measurement" is accurate. |
| §1.2 therefore "NOT reusable" → new module `xen.sigbar.ltf` | — | **ACCEPTED, but weakly argued** | The function is a generic group-by; adding four `pl.sum` columns is ~5 lines. The stronger and *correct* justification is the window convention: `bar_aggregator` buckets on `(CloseTime.epoch − 1) // period` (:100-104) while the designer's own trace uses `group_by_dynamic("OpenTime")` (`agg_trace.py:41`). Two conventions now coexist and nothing in the battery cross-checks them — Issue 2b. |
| §1.3 `xen.sigbar.sessions` "knows four daily anchors, none hourly or 4-hourly" | `sessions.py:65-70` | **CONFIRMED with correction** | Four anchors confirmed. They are not all *daily*: `A-FUND` is 8-hourly `(0, 480, 960)`. This matters — see Issue 4. |
| §1.3 `session_breaks` takes IB in minutes with no notion of an LTF bar | `sessions.py:259-261, 296` | **CONFIRMED** | `ib_minutes: int`; window is `mins_since < ib_minutes`. |
| §2 W3 "calls `classes.derive_thresholds` unmodified" | `classes.py:53-92` | **CONFIRMED** | Operates only on `f"{m}_resid"` columns; timeframe-agnostic. `abs_high` for `delta_ratio` present at :86 as the design states. |
| §4 A2 "the **137** per-symbol threshold blocks in `instrument_registry.json`" | measured | **CONFIRMED** | `class_thresholds.per_symbol_values` → 137 entries. |
| §0 "the **194** instruments with a fitted A5 1-minute baseline" | measured | **CONFIRMED** | `seasonal_baselines.parquet` → 194 distinct symbols, 9,777,600 rows, columns `[symbol, metric, mod, dow, loc, scale, n, sparse]`. |
| §3 `check_no_outcome_columns`, `assert_bar_causality`, `assert_design_only_fit` | grep across `python/src` | **NOT YET EXISTING** | All three are new. Run-2 trace items T1, T2, T4. `check_no_local_accounting` exists (`xen/estimand_validation.py:385`). |

### 3. Designer artifact verification — §6 VT traces (re-derived independently)

Re-derived directly from `python/experiments/INFR-011/data/staging/bars/BTCUSDT.parquet`, filtered to
`[2022-07-15 13:00, 14:00)`, **without** calling `agg_trace.py`.

| Trace | Design value | Independently re-derived | Verdict |
|---|---|---|---|
| VT-1 5m | O 20975.0 H 20999.0 L 20970.0 C 20970.5 · V 718.345 B 443.107 S 275.238 Δ +167.869 · n=5 | identical | **MATCHES** |
| VT-2 15m | O 20975.0 H 21094.5 L 20945.0 C 20947.5 · V 4653.376 B 2550.228 S 2103.148 Δ +447.080 · n=15 | identical | **MATCHES** |
| VT-3 60m | O 20975.0 H 21094.5 L 20790.5 C 20855.5 · V 13447.757 B 6786.452 S 6661.305 Δ +125.147 · n=60 | identical | **MATCHES** |
| Buy+Sell−Volume | 0.0 / 9.09e-13 / 1.82e-12 | 0.0 / −9.09e-13 / +1.82e-12 | **MATCHES** (design reports absolute value; sign differs on VT-2, immaterial) |
| Nesting claim (same Open; H/L widen monotonically; Δ non-monotone) | asserted | reproduced exactly: H 20999.0→21094.5→21094.5, L 20970.0→20945.0→20790.5, Δ +167.9→+447.1→+125.1 | **MATCHES** |
| `agg_trace.py` computes no forward outcome | asserted | **CONFIRMED** — read in full (110 lines); it loads DESIGN-band bars via the fenced `load_bars`, aggregates, re-checks, writes JSON. No forward window, no return, no excursion, no shift. | **MATCHES** |
| A8 additivity survives aggregation | asserted | **CONFIRMED** at all three periods within float tolerance | **MATCHES** |

Minor, non-blocking: `agg_trace.py:70-73` filters `bars` (unsorted) for the recheck while
`aggregate_signed` sorts internally; `src["Open"][0]` / `src["Close"][-1]` are therefore
order-dependent on the input file. It agrees here because staging is already sorted, but the
"independent recheck" is not fully independent of input ordering.

### 4. Governance & mandatory-declaration trace (`quant-designer/references/design-requirements.md`)

| Block | Present? | Verdict |
|---|---|---|
| §1 MECHANISM / DERIVED | **absent, and not declared N/A** | **MISSING** — Issue 7 |
| §2 OBJECT-IDENTITY | **absent, and not declared N/A** | **MISSING** — Issue 7; substantively live (W5's "candidate event bar" vs SPDR-009's event object) |
| §3 CONTROL validity proofs | N/A declared, §0 applicability table | **ACCEPTED** — a control answers an attribution question about an effect; this item measures no effect. Substitute (reproduction battery) is the right shape but has gaps — Issue 2 |
| §4 TRIPWIRE | N/A declared | **ACCEPTED** on the same reasoning; nothing to collapse |
| §5 BANDS | N/A implied by "no verdict" | **ACCEPTED** (no read, no verdict) |
| §6 POWER | N/A declared, replaced by §5 COVERAGE | **ACCEPTED in form**, but the coverage statement predeclares no usable-coverage **floor** and no action on breach — Issue 3b |
| §7 GOLDEN-TRACE | §6 VT-1..VT-4 | **PARTIAL** — covers W2 only. No hand-derived expected value for a seasonal cell (W1), a threshold (W3), a session boundary (W4), or a zone-scale quantile (W5) — Issue 9 |
| §8 HARD vs INFORMATIVE split | **absent as a block** | **MISSING** — Issue 7. Effectively present in prose (§4 "hard assert" vs §5 "reported"), but not declared |
| §9 CONVERSION-PIN (L-21) | absent | **CORRECTLY N/A** — no money claim anywhere; should still be declared N/A |
| §10 SPREAD-SCALE-ROUTING | N/A declared with reason | **ACCEPTED** — no edge, no contrast, no verdict |
| §11 Spread as verdict leg (L-22) | N/A declared with reason | **ACCEPTED** — same |
| §12 Amendment ledger (L-23) | §8, opens 0L/0T/0N | **MATCHES** |
| §13 Battery/eligibility (L-24) | F06 mapped to W3; rest N/A as read-gating | **ACCEPTED** — F06 discharge is real (realised cut values emitted; `derive_thresholds` already emits `high/low/n/high_pctl/low_pctl/applied_to`) |
| L-28 derangement | no permutation anywhere | **CORRECTLY N/A** |
| L-31 one BacktestNode/process | no Nautilus | **CORRECTLY N/A** |
| `check_no_local_accounting` | §3 asserts it | **ACCEPTED** (run-2 trace item) |
| Holdout unreachable | §0 band + `fences.assert_band` raising, `BANDS` dict has no TEST/holdout key (`fences.py:49-52`, `:91-95`) | **MATCHES** — "unreachable by construction" is literally true: `load_bars` cannot be asked for a TEST band |
| Registry preconditions / counted reads | §0 "0 / 0" | **MATCHES** |
| Operator-facing communication | design is technical-artifact-tier | **ACCEPTED** |

---

### Issues

**1. [MAJOR — design] The outcome ban is enforced by column *name*, not by provenance, and the W5 census has no declared band.**
§0 / §3 / §4 A7. `check_no_outcome_columns` is specified as "raises if any emitted artifact carries a
forward return, excursion, hold, **or any column derived from bars after an event bar**". The second
clause is not machine-checkable from a schema — a name check cannot see provenance, so any future
column with an innocuous name would pass. Given that SPDR-009 freezes τ and its pool cuts against
these artifacts, this is the one ban that must be structural.
Compounding: **§2 W5 does not state which band the zone-scale census is computed on.** §3 fences
fitting to DESIGN and permits CONFIRM "for coverage reporting", but W5 is neither a fit nor a
coverage report. If the census spans CONFIRM, SPDR-009's τ freeze becomes CONFIRM-informed.
*Required:* (a) add a provenance assert — for every emitted row, `max(source bar OpenTime
contributing to the row) ≤ the row's own key timestamp` — and keep the name check as a second
layer; (b) state explicitly that W5's census is **DESIGN-band only**; (c) state plainly that W1/W3/W5
are whole-band in-sample fits (as INFR-017/018 were) so §3's "no look-ahead" sentence is not read as
a causality guarantee the fitted objects do not have.

**2. [MAJOR — design] The reproduction battery has four gaps and one defective member.**
§4. The substitution of the battery for §3 controls and §4 tripwire is **legitimate** for an item that
measures no effect, and A1–A3 (byte-identity against the frozen predecessors) are exactly the right
instrument. But:
 - **2a.** A1 says "byte-identically" while the generalisation changes the seasonal key
   (`mod` → slot-of-day). The frozen parquet's schema is `[symbol, metric, mod, dow, loc, scale, n,
   sparse]`; a renamed or re-typed key column makes A1 vacuous or unpassable. Declare that at
   `bar_minutes=1` the emitted schema and column names are held **identical**, and that A1 compares
   the artifact bytes, not a re-derived frame.
 - **2b.** Nothing cross-checks the new `xen.sigbar.ltf` against the existing frozen
   `bar_aggregator.aggregate_ohlc`. The two use different window conventions (`CloseTime`-epoch
   bucketing at `bar_aggregator.py:100-104` vs `group_by_dynamic("OpenTime")` in the designer trace).
   Add an assert: for every symbol and every N ∈ {5,15,60}, `ltf` OHLC ≡ `aggregate_ohlc(...,
   min_coverage=None)` OHLC on the shared columns. This is the cheapest available regression and its
   absence is conspicuous next to A1–A3.
 - **2c.** A2 pins 137 symbols; the extension to 194 is asserted in prose ("identical estimator") with
   no assert. Add: the 194-symbol run and the 137-symbol run produce identical values on the 137
   overlap, and the 57 new symbols come from the same call site.
 - **2d.** `assert_seasonal_keys_valid` (`baselines.py:68-83`) hard-codes `mod ∈ [0,1439]` and will
   raise for every `bar_minutes > 1`. The design never names it. A1 runs at `bar_minutes=1` and so
   never exercises the generalised branch — the battery cannot catch a defect in the generalised key
   guard. Add a positive test at each `bar_minutes`.
 - **2e.** A6 is not an integrity instrument — see Issue 3.

**3. [BLOCKING — design] A6 is empirically false, and the coverage premise behind W1 is wrong.**
§2 W1 ("Coarser grids have **more** observations per cell, so sparse fallback should fall
monotonically with bar size") and §4 A6 ("sparse-cell fallback rate is monotone non-increasing in bar
size per instrument", a **hard** assert).
 - **3a. The premise is arithmetically wrong.** A seasonal cell is (slot-of-day × day-of-week), so it
   recurs **once per week at every timeframe**. Observations per cell = number of weeks in the band,
   *independent of bar size*. Coarsening reduces the number of cells and the number of bars by the
   same factor; it does not pool observations. Measured on BTCUSDT/ETHUSDT/SOLUSDT: median obs/cell =
   **33 at 1m, 5m, 15m and 1h alike**. The §2 W1 table (60 / 85 / 86 / 86) is wrong in both level and
   shape, and its "~600 days" is also wrong — the DESIGN band as staged runs 2022-07-15 → 2023-02-28
   = **229 days ≈ 33 weeks for every instrument**, including BTC.
 - **3b. Under W2's strict retention the true relation is the *reverse* of A6.** With per-minute
   presence `p`, an N-minute window survives with probability ≈ `p^N`, so obs/cell at N relative to 1m
   is ≈ `p^(N−1)` — **non-increasing in N**, strictly decreasing whenever `p < 1`. Measured, on a
   random 30-symbol sample of the 194: **A6 would fire on 26 of 30 instruments.** Example CRVUSDT
   (86.8% minute coverage, entirely benign): sparse-fallback rate 0.0000 → 0.0010 → 0.0744 → **0.6429**
   across 1m/5m/15m/1h. Median sparse rate at 1h across the sample = **1.00** — i.e. for the median
   instrument *every* 1h seasonal cell falls back to the day-of-week marginal. 83% of sampled
   instruments exceed 20% sparse at 1h.
 - **3c. §4 and §5 contradict each other.** §5 already says "Any instrument whose 1h grid is sparse is
   a data problem, not a timeframe problem, and is reported that way" — which is the correct reading
   and is incompatible with §4 making the same observation a hard assert.
 - **3d. Downstream consequence.** This is not cosmetic: it means D3 (4h/15m) and D4 (1d/1h) — the two
   pairs D6 exists to enable — would receive 15m/1h "baselines" that are dow-marginal fallbacks for
   most of the universe, i.e. not seasonal baselines at all, and W3's p90/p10 cuts would be derived
   off them.
 *Required:* delete A6 as a hard assert; replace with a **reported** obs-per-cell and fallback-rate
 census per (symbol, timeframe); correct the §2 W1 table to the measured ~33 obs/cell at all
 timeframes and correct "~600 days" to the staged 229; and predeclare a usable-coverage floor per
 (symbol, timeframe) with a stated action on breach (exclude / fall back / report), because §5
 currently names no floor and no action.

**4. [MAJOR — design] The A-H4 anchor certification is not honest as written: half its instants were raced, and lost.**
§2 W4 ANCHOR CERTIFICATION, against Addendum §2.7. The block correctly certifies OPERATIONAL, bans
edge-bearing reads, and machine-checks the ban at VT-4(g) — that part is above standard. But it states
"their selection contrast is UNMEASURED". A-H4's grid is `(0, 240, 480, 720, 960, 1200)`, a **strict
superset of the already-raced `A-FUND` = (0, 480, 960)** (`sessions.py:67`). INFR-018 measured A-FUND:
`contrast_median −0.163` at L=15, `ci_excludes_zero: true`, `below_own_mde: false` — a *powered,
negative* breakout-expectancy contrast. So three of A-H4's six daily instants carry measured evidence
and it is unfavourable. Relatedly, §1.3's "four **daily** anchors" is inaccurate — A-FUND is 8-hourly.
*Required:* amend the certification to record the measured A-FUND evidence explicitly ("the funding
subset of A-H4's grid was raced at INFR-018 and its breakout contrast was negative and CI-excluding-
zero; A-H1's grid is genuinely unraced"), and keep the operational certification. The funding
*coincidence* handling is otherwise correct — stated as a property of the clock, not a claim.

**5. [MAJOR — design] The D6.3 one-minute invariant is never restated, and W5 computes distances to levels without pinning how the levels are built.**
§2 W5 vs ckpt-015 §D6.3 / SPDR-009 AMENDMENT-18(a). D6.3 is binding: "every price-path and
volume-at-price measurement stays on 1-minute bars in all four pairs", with volume profiles built
from the **prior HTF session's 1-minute bars** so the frozen K-UNIFORM kernel stays inside its
calibrated regime. INFR-020 is the first item that will hold aggregated 5m/15m/1h bars in memory
alongside a level-construction step, which makes it the single most likely place for the invariant to
be broken — and it is the one document that does not state it. W5 says only "distance from each
candidate event bar's close to its nearest structural level".
*Required:* restate the D6.3 invariant in §0 as a hard scope clause, and specify in W5 that structural
levels and the prior-session range are computed from **1-minute** bars of the prior HTF session, with
an assert that no level-construction path consumes an aggregated LTF bar.

**6. [MODERATE — design] D6.4.5's retained `0.25 × ib_width` sensitivity has no emitted census.**
§2 W5 vs D6.4.5 / AMENDMENT-18(d). D6 retains D1's original `0.25 × ib_width` zone definition as a
pre-registered sensitivity "so the QA-approved 1d/1m read is not lost". W5 emits only the
prior-session-range scale, and `zone_scale_census.json` is not specified to carry the IB-width scale.
SPDR-009 cannot run its retained sensitivity against an artifact that does not exist.
*Required:* W5 emits both scale families per pair (prior-session range **and** IB width), count-only.

**7. [MODERATE — governance] Five mandatory declaration blocks are neither filled nor declared N/A.**
`design-requirements.md` §1 (MECHANISM/DERIVED), §2 (OBJECT-IDENTITY), §8 (HARD vs INFORMATIVE), §9
(CONVERSION-PIN) are absent from the design, and §7 (GOLDEN-TRACE) is only partially discharged
(Issue 9). The §0 "Applicability of standard design blocks" table is a good instrument but is
incomplete — it covers blocks 3, 4, 6, 10, 11, 12, 13 and silently omits 1, 2, 7, 8, 9.
§2 is not merely formal here: **object-identity is live**. W5's "candidate event bar" must be the same
object as SPDR-009's event, or the τ freeze is against a mismatched census. That equality is asserted
nowhere.
*Required:* extend the applicability table to all thirteen blocks; fill §2 with the W5-census ↔
SPDR-009-event object identity; fill §8 (A1–A7 + fences HARD; §5 coverage INFORMATIVE); declare §1 and
§9 N/A with reasons.

**8. [MINOR — design] The IB rule holds wall-clock constant but lets the IB's share of the session vary 4×.**
§2 W4. IB fraction of session: D1 15/1440 ≈ 1%, D2 3/12 = **25%**, D3 1/16 ≈ 6%, D4 1/24 ≈ 4%. At D2 a
quarter of every session is consumed by the initial balance, and the post-IB search window is 9 bars.
The design discloses the D4 wall-clock deviation but not this one, and the pairs are meant to be
compared internally under one frozen design.
*Required:* disclose the IB-share-of-session per pair alongside the wall-clock table, so a pair
difference is not read as a mechanism difference.

**9. [MINOR — governance] Golden trace covers W2 only.**
§6 discharges `design-requirements.md` §7 for the aggregator (VT-1..VT-3, verified exact above) and
adds seven raise-conditions (VT-4), which is good practice. But W1, W3, W4 and W5 have no hand-derived
expected value at all — no expected `(slot, dow)` cell `loc`/`scale`/`n` for a named instrument, no
expected p90/p10 cut, no expected 4h session boundary, no expected zone-scale quantile. Those four work
items are the ones whose defects would be silent.
*Required:* one designer-derived expected value per work item, on a named symbol and timestamp.

**10. [MINOR — design] W1 emits a 1-minute baseline that competes with the frozen INFR-017 pin.**
§0 W1 and §7 list `{1m, 5m, 15m, 1h}` in `seasonal_baselines_mtf.parquet`. After this item there will
be two on-disk 1-minute baseline artifacts with different paths and hashes. A1 is the reason the 1m
fit is run, but A1 is a regression check, not a deliverable.
*Required:* state that `INFR-017/results/seasonal_baselines.parquet` `1b7244c8…` remains the governing
1-minute pin and that the `_mtf` artifact's 1m partition is regression evidence only — or drop 1m from
the emitted artifact entirely.

---

### Design-quality note (not an issue)

The design is **not** over-engineered — the module split, the strict execution order (battery before
anything downstream), the seven VT-4 raise-conditions, and the anchor certification block are all
proportionate and several are above the programme's normal standard. The problem is the opposite:
one central quantitative premise (Issue 3) was asserted rather than measured, and it happens to be the
premise that determines whether the coarse pairs D6 was created to enable are viable at all. Ten
minutes on disk would have caught it. The reproduction-battery instinct is right; it just needs to be
pointed at the aggregator (2b) and at coverage (3) rather than at monotonicity.

### QA-run-2 trace items (verifiable only against an implementation)

| # | Clause | What run 2 must trace |
|---|---|---|
| T1 | §3 `check_no_outcome_columns` | exists; raises on a planted outcome column; and (per Issue 1) carries the provenance assert |
| T2 | §3 `assert_bar_causality()` | every aggregated bar's source window lies strictly inside `[open, close)`; raises on a planted straddle |
| T3 | §2 W1 generalisation | `_with_seasonal_keys`, `_full_grid`, `assert_seasonal_keys_valid` and the `FULL_GRID_CELLS` guard all parameterised on `bar_minutes`; positive test at each of 1/5/15/60 |
| T4 | §3 `assert_design_only_fit()` | raises on any fit path touching a CONFIRM bar |
| T5 | §4 A1 | byte-identity against `1b7244c8…`, schema and column names unchanged at `bar_minutes=1` |
| T6 | §4 A2 | 137-block exact reproduction; 194-symbol extension identical on the overlap |
| T7 | §4 A3 | `A-USOPEN`, L=15 session object byte-identical to the frozen `session_breaks` output |
| T8 | §4 A4/A5 | per-bar `Buy+Sell==Volume`; 1m→5m→15m ≡ 1m→15m; plus the new cross-check against `aggregate_ohlc` (Issue 2b) |
| T9 | §2 W5 | levels and prior-session range built from 1-minute bars only (Issue 5); DESIGN band only (Issue 1) |
| T10 | §7 | `check_no_local_accounting("python/experiments/INFR-020/code")` passes; no `BacktestNode`; `bar_aggregator.py` and `classes.py` byte-unchanged in the diff |
| T11 | §7 pins | every emitted artifact hashed into `pins.json`; frozen-input hashes re-verified at entry (`fences.assert_frozen_inputs`) |

---

## QA run 2 — 2026-07-21T16:46Z — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time: `docs/.../015-signed-value-absorption-screen/design.md` (M);
`python/experiments/INFR-020/`, `python/experiments/SPDR-009/` untracked.
Reviewing the revised `design.md` (rev. note at line 8) + new `design_derivations/diag_coverage.{py,json}`.
Still DESIGN-ONLY: `code/` is empty. Run-1 trace items T1–T11 remain open and are carried forward.

**Verdict: REVISE** — 2 blocking-class residuals, 7 lesser.
**FAILING_ARTIFACT:** `python/experiments/INFR-020/design.md` (§2 W2a, §5, §8 AMENDMENT-1)
**REQUIRED_SKILL:** `quant-designer`

The run-1 fixes are real and mostly well made — I-3's correction in particular changed the design
rather than its wording, and the new diagnostic reproduces exactly. But **the new material carries a
new defect of the same shape as the one it fixed**: W2a's justification is asserted about the whole
universe and is false for 37 of 194 instruments, and the fill's effect on the *event population* was
not measured. Both are below.

### 1. Run-1 issue disposition

| # | Run-1 issue | Fix claimed | Verified | Verdict |
|---|---|---|---|---|
| I-1 | Outcome ban name-based only; W5 band undeclared | §3 two-layer ban + `assert_no_forward_provenance`; §0/§19 W5 DESIGN-only; VT-4(a)/(e) | Provenance layer is the right instrument — max source-bar timestamp per column, raises if > row's bar close, defeats renaming. W5 band now stated three times (§0, §2 W5, §3). | **RESOLVED** (implementation → T1) |
| I-2 | Battery: A1 "byte-identical" incoherent; no generalised-branch exercise; 137→194 unasserted; no legacy-aggregator cross-check; `assert_seasonal_keys_valid` unmentioned | A1 value-identity under declared key remap; A1b; A2 extended; A5b; §1/W1 flags `[0,1439]` generalisation | All five addressed. A1's restatement is correct — the key column changes by construction, so value-identity under a declared mapping is the only coherent form. A5b's "or the window-convention difference is explicitly characterised" is an acceptable escape given the two modules genuinely bucket differently (`bar_aggregator.py:100-104` vs `group_by_dynamic`). | **RESOLVED** |
| I-3 | **BLOCKING** — coverage premise asserted and false; A6 guaranteed to fire | Premise withdrawn, measured in §5; W2a added; A6 deleted and replaced | Premise correction is **correct and independently confirmed**: obs/cell is constant in bar size (measured 33 at 5m/15m/60m on all five sampled), retention degrades ~`p^(N−1)`. `diag_coverage.json` reproduces byte-for-byte when re-run. Fix works. **But see R-1 and R-2.** | **PARTIALLY RESOLVED** |
| I-4 | A-H4 certified "unmeasured" though its grid is a superset of the raced A-FUND | Certification corrected, negative recorded | A-FUND figures verified exactly against the registry: `contrast_median −0.16270738…`, `contrast_ci [−0.2586, −0.0273]`, `mde 0.10`, `ci_excludes_zero true`, `below_own_mde false`. The design's quoted numbers are right. "Strict SUPERSET", "half of A-H4's instants" (3 of 6) — both accurate, not overstated. | **RESOLVED** (scope caveat → R-7) |
| I-5 | D6.3 1-minute invariant never restated | §1.2 restates it + `assert_levels_from_1m()`; W5 pins level provenance | Correct, and code-asserted rather than asserted in prose. VT-4(i). | **RESOLVED** (→ T9) |
| I-6 | D1 `0.25 × ib_width` sensitivity had no census | §2 W5 + `zone_scale_census_d1_ibwidth.json` in §7 | Present in both the work item and the artifact list. | **RESOLVED** |
| I-7 | Five mandatory blocks neither filled nor N/A | §0 applicability table extended to all blocks; §1.1 object-identity filled; §3 hard/informative filled | All thirteen now carry a status. §1.1 is the strongest fix in this revision: making W5's candidate bar and SPDR-009's event bar **one shared predicate function that SPDR-009 imports** converts a prose promise into a structural guarantee. | **RESOLVED** |
| I-8 | IB share-of-session variation undisclosed | §2 W4 table + explicit non-comparability statement | Shares recomputed and correct (1.0% / 25.0% / 6.3% / 4.2%). The added consequence — IB-derived objects are not cross-pair comparable — is the right inference. | **RESOLVED** |
| I-9 | Golden trace covered W2 only | §6 adds W2a, W1, W4 traces; W3/W5 gap declared | Three of five work items now carry a designer-derived value; the remaining gap is declared rather than papered over, which was the ask. | **RESOLVED** (mis-citation → R-5) |
| I-10 | W1 emitted a competing 1m baseline | §2 W1: "W1 does not emit a 1-minute baseline"; 1m path exercised only via A1 | Clean. `1b7244c8…` remains the sole 1m pin. | **RESOLVED** |

### 2. Verification of the new material

| Claim (§ref) | Method | Result |
|---|---|---|
| `diag_coverage.json` numbers | re-ran `diag_coverage.py` from repo root | **Reproduces exactly.** BTC/ETH 1.000 at all N; SOL 60m 0.9605→1.000; LTC 60m **0.4913→1.000**, obs/cell 15.5→33, sparse 0.0595→0.00; CRV 60m **0.204→1.000**, obs/cell 6→33, sparse **0.6429→0.00**. |
| §5 table vs the JSON | line-by-line | Matches, except LTCUSDT 60m obs/cell printed as **16** where the JSON says **15.5** → R-9. |
| Int8 overflow trap re-triggered and guarded | read `diag_coverage.py:84-95` | Casts to Int32 present with the INFR-017 citation. Independently corroborated: the measured obs/cell (33) matches the analytic prediction (32.6 weeks); an aliased grid would not produce a fully populated 168/672/2016-cell grid. **Numbers are right.** |
| `diag_coverage.py` computes no forward outcome | read in full (144 lines) | **Confirmed.** Retention fractions, cell counts, medians only. No shift, no forward window, no return, no excursion. |
| A5 metric guard against zero-volume windows | `INFR-018/code/common.py:222-225` | `delta_ratio` is already `when(Volume > 0) … otherwise(None)`. The obvious 0/0 hazard the fill introduces is **already handled** by the existing code path. |
| `zero_fill` bounded to the instrument's observed span | `diag_coverage.py:36-45` | Bounded to `bars.min()..bars.max()`, so no pre-listing fabrication. Good. |
| W4 golden trace: BTCUSDT 2022-07-15 13:30Z IB 20833.0 / 21020.5 / 187.5 | recomputed from staging | **Values correct** — 15 bars, high 21020.5, low 20833.0, width 187.5. Citation wrong → R-5. |
| A-FUND race figures | INFR-018 registry | Exact match (above). |

### 3. Residuals

**R-1. [MAJOR] W2a's central evidence sentence is false, and its refusal rule silently costs 19% of the universe.**
§2 W2a states `collection_gap_minutes = 0` and `outage_minutes = 0` "for **every** instrument".
Measured over `INFR-011/artifacts/admission-ledger.jsonl` (894 admitted): `outage_minutes = 0`
holds for all, but **`collection_gap_minutes > 0` for 90 of 894 admitted, and for 37 of the 194-instrument
universe** — max 138,240 minutes (OMGUSDT), 136,800 (ONEUSDT), and a cluster of 8,640-minute
(6-day) runs across BCHUSDT, SNXUSDT, SANDUSDT, LDOUSDT, CELOUSDT, APTUSDT, AAVEUSDT, ALPHAUSDT,
**AVAXUSDT** and others. Consequences the design does not state:
 - A8 refuses the fill for those 37, so they get no usable coarse bars → **D1 runs on 194
   instruments and D2/D3/D4 on 157.** The four pairs are meant to be compared internally under one
   frozen design; they would not share a population, and no read could attribute a pair difference
   to the pair rather than to the 19% of names missing from three of them.
 - **AVAXUSDT is one of SPDR-009's ten census instruments** (§6.3), so the exclusion reaches the
   deep sample the power projection was built on, not just the tail.
 - The gaps are **contiguous runs** (`max_gap_run_min` equals `collection_gap_minutes` for the
   8,640-minute cases), i.e. excisable. Dropping a whole instrument for one known 6-day window is a
   far heavier remedy than excluding that window from the fitting span.
*Required:* correct the evidence sentence to the measured counts; state the excluded-instrument
count and name them; and either excise gap runs from the fitting span (preferred — keeps the four
pairs on one population) or predeclare and disclose the D1-vs-coarse universe mismatch as a
first-order limitation of every cross-pair comparison.

**R-2. [BLOCKING] The zero-fill manufactures the absorption signature on thin instruments — the direction of the new bias is the one that flatters the hypothesis, and the amendment ledger records it backwards.**
This is the question the revision most needed answered and §2 W2a answers only half of it. The design
argues the fill *removes* a bias ("strict retention deletes exactly the quiet windows — biasing W3's
p90/p10 cuts toward active regimes, in the same direction as the low-range absorption signature").
That reasoning is correct, and it was my run-1 point. **The return leg was not measured.** Measured
now, on the zero-filled series, per (symbol, timeframe), using the frozen rule
(`volume_resid ≥ p90` ∧ `range_resid ≤ p10`) and tracking whether each qualifying window contains
any reconstructed minute:

| symbol | 1m cov | N | raw p10 range | filled p10 range | candidates raw | candidates filled | **filled candidates touching reconstructed minutes** |
|---|---|---|---|---|---|---|---|
| SKLUSDT | 0.571 | 5m | 0.000100 | **0.000000** | 3 | 20 | **18 (90%)** |
| SKLUSDT | 0.571 | 15m | 0.000290 | 0.000050 | 0 | 4 | **4 (100%)** |
| ALICEUSDT | 0.586 | 5m | 0.005000 | **0.000000** | 32 | 89 | **82 (92%)** |
| ALICEUSDT | 0.586 | 15m | 0.015000 | 0.005000 | 2 | 16 | **16 (100%)** |
| CRVUSDT | 0.868 | 5m | 0.002000 | 0.001000 | 170 | 237 | **176 (74%)** |
| CRVUSDT | 0.868 | 15m | 0.005000 | 0.002000 | 40 | 76 | **68 (89%)** |
| LTCUSDT | 0.959 | 5m | 0.070000 | 0.060000 | 9 | 5 | 0 (0%) |
| SOLUSDT | 0.999 | 5m | 0.025000 | 0.025000 | 59 | 57 | 0 (0%) |

The mechanism: reconstructing no-trade minutes adds a mass of zero-range bars (SKLUSDT 5m: **22.7%**
of all bars have `range == 0`; ALICEUSDT 5m: **26.2%**), which pulls each cell's median range and MAD
down and drags the p10 range cut to **exactly zero**. A window that is mostly reconstructed then has
near-zero range but keeps the *real* volume of its few traded minutes — and against a depressed
cell median that volume residualises **high**. The window therefore reads as "heavy volume, no
result": the ABSORPTION signature, manufactured out of inactivity. On the thin names 74–100% of the
qualifying population is of this kind, and thin names are exactly where D6 expects breadth to come
from. This lands directly on SPDR-009's D2 (1h/5m) event pool and on the τ freeze W5 hands it.
Corollary — **AMENDMENT-1's direction label is wrong.** It is recorded `TIGHTER`. For the *event
population* the fill is `LOOSER`: it raises candidate counts by 2–8× on thin names, almost entirely
through reconstructed bars. The running count `0L / 4T / 1N` is therefore wrong, and under L-23 a
mislabelled direction defeats the ledger's purpose.
*Required, before this apparatus can be handed to SPDR-009:*
 1. Carry a `n_reconstructed` (and `traded_minute_fraction`) column on every aggregated LTF bar —
    free, since `SourceBars` is already counted — and emit it in every W5 census row so SPDR-009 can
    stratify or exclude.
 2. Predeclare, and freeze before any read, a **minimum traded-minute fraction** for a bar to be a
    candidate under `absorb_candidate_predicate()`. A bar whose "no result" is reconstructed silence
    is not an absorption event under any reading of §2.3.
 3. Derive W3's p90/p10 cuts on **traded** bars only, or report both and declare which governs.
 4. Re-label AMENDMENT-1 and re-derive the running count.

**R-3. [MODERATE] The A6 replacement is unscoped and demands exact equality.**
§4 A6: "observations per cell must be **equal across timeframes** per instrument, and the sparse rate
must be **≤ its 1-minute value**". Two problems. (a) It cannot hold for the 37 instruments A8 refuses
the fill to (R-1) — for them retention still degrades as `p^(N−1)` and the assert fires for the same
benign reason the deleted A6 did. (b) "Equal" is exact; obs/cell can differ by ±1 across timeframes
at the band edges when the span is not a whole number of days (LTCUSDT already shows a fractional
median, 15.5, pre-fill). (c) "≤ its 1-minute value" compares against a rate computed on the *unfilled*
1m series, since W1 no longer fits 1m — well-defined, but say so.
*Required:* scope the assert to zero-filled instruments; state a ±1 tolerance on the equality; state
that the 1m comparator is the frozen unfilled INFR-017 rate.

**R-4. [MODERATE] The fill creates degenerate seasonal cells at 5m on thin names, and nothing catches them.**
Measured on the zero-filled series: range-metric cells whose MAD is 0 (⇒ `scale` null ⇒
`range_resid` null for every bar in that cell ⇒ the bar can never satisfy any class test) —
**ALICEUSDT 9 of 2016 cells, ANKRUSDT 3 of 2016, SKLUSDT 1 of 2016** at 5m. Zero at 15m and 60m, and
zero for volume at every timeframe. Small, but it is a *silent* hole in the event population: those
bars are neither classified nor counted as excluded, and the §5 coverage report tracks sparse-cell
fallback, not null-scale cells. `baselines.py:158-162` deliberately makes this a null rather than a
divide-by-zero, so nothing raises.
*Required:* count and report null-scale cells per (symbol, timeframe, metric) in the coverage report,
alongside the sparse-fallback rate.

**R-5. [MINOR] §6's W4 golden trace cites the wrong source.**
It attributes "BTCUSDT 2022-07-15 13:30Z, IB 20833.0 / 21020.5 / width 187.5" to **SPDR-009 §8**.
The values are correct — I recomputed them from staging (15 bars, high 21020.5, low 20833.0, width
187.5) — but SPDR-009 §8's GT-1 is a different object: **SOLUSDT, event 2022-12-28 03:27Z, anchor
2022-12-27 14:30Z, IB_LOW 10.700, ib_width 0.380** (`gt_output.json` confirms). A developer following
the citation would trace to the wrong session.
*Required:* attribute the values to this item's own derivation, or point at the actual SPDR-009 GT-1.

**R-6. [MINOR] W2a's per-instrument no-trade counts are whole-archive; §5's are DESIGN-band. They sit adjacent, unlabelled.**
§2 W2a quotes BTCUSDT 1 / ETHUSDT 134 / SOLUSDT 393 / LTCUSDT 28,450 / CRVUSDT 118,112 — those are
the ledger's whole-archive `no_trade_minutes` (verified). §5's table quotes 0 / 3 / 365 / 13,543 /
43,539 — DESIGN-band only (verified, reproduces from `diag_coverage.json`). Both correct, different
frames, three pages apart, neither labelled.
*Required:* label each set with its span.

**R-7. [MINOR] The A-H4 inference is correctly stated but not correctly scoped.**
§2 W4 says D3's prior is "LOWERED BY MEASUREMENT". The numbers are right and the superset relation is
right. But A-FUND's measured negative is a **breakout-expectancy contrast after an initial balance on
an anchored session** — the S1 object. D3's use of A-H4 is *session framing for absorption detection
at a level*, a different object, and nobody claims A-H4 is edge-bearing. The evidence is strong
against A-H4-as-edge-bearing (which the design already forbids) and weak about 4h framing for S9.
*Required:* scope the sentence to the object A-FUND was raced on, so a later reader does not carry a
breakout result into an absorption disposition.

**R-8. [MINOR] The reference `zero_fill` leaves `Delta` and `Turnover` null on reconstructed rows.**
§2 W2a's spec says `Delta = 0`. `diag_coverage.py:46-57` fills `Volume`/`BuyVolume`/`SellVolume`/
`NTrades` but not `Delta` or `Turnover`, both of which `load_bars` creates (`fences.py:132-137`).
Harmless in the diagnostic (counts only), but this is the code the implementation will be read
against.
*Required:* either fix the reference implementation or note that `Delta`/`Turnover` are recomputed
post-fill in the real path (→ T12).

**R-9. [MINOR] §5's LTCUSDT 60m obs/cell reads 16; the artifact says 15.5.**
Rounding, but §5 is the section that exists because a number was asserted rather than measured.

### 4. Carried-forward and new QA-run-2 trace items

T1–T11 from run 1 all remain open (no code). Added:

| # | Clause | What run 3 / post-implementation must trace |
|---|---|---|
| T12 | §2 W2a | reconstructed rows carry `Delta = 0`, `Turnover = 0`; fill bounded to `[first_bar, last_bar]` per instrument |
| T13 | §3 `assert_no_collection_gaps()` | refusal list emitted and non-empty (expect 37 of 194 on current ledger); named in the coverage report |
| T14 | §4 A6-replacement | scoped to filled instruments; tolerance honoured |
| T15 | §2 W2b / W5 | `n_reconstructed` and `traded_minute_fraction` present on every aggregated bar and every W5 census row (R-2) |
| T16 | §1.1 | `absorb_candidate_predicate()` is a single exported function and SPDR-009 imports it rather than reimplementing |
| T17 | §5 | null-scale cell counts reported per (symbol, timeframe, metric) (R-4) |

### 5. Note to the operator

The correction to I-3 was made properly: premise withdrawn, measured, fix derived from the
measurement, artifact reproducible, and the Int8 trap called out from experience rather than
recalled. That is the right shape. The residual worth acting on is R-2 — the fill was validated on
*coverage* (retention, obs/cell, sparse rate, all of which it fixes cleanly) but not on the *event
population*, and on thin instruments the population it produces is 74–100% reconstructed at the
5m and 15m detection bars. The fix removed a conservative bias and installed an anti-conservative
one in the same place, which is why AMENDMENT-1's `TIGHTER` label reads backwards. Carrying the
reconstructed-minute count on every bar costs nothing and makes the whole question auditable
downstream.

---

## QA run 3 — 2026-07-21T16:59Z — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Reviewing `design.md` rev. 3 (zero-fill withdrawn) + new `design_derivations/diag_fill_bias.{py,json}`.
Still DESIGN-ONLY: `code/` empty. T1–T17 carried forward.

**Verdict: REVISE** — 4 MAJOR, 3 MINOR. No blocking residual: the fabrication defect is genuinely
closed **in substance**, but the withdrawal is not fully propagated (S-1), one new mechanism is not
computable from the source it cites (S-2), and the two disclosures the operator asked about are
materially understated (S-3, S-4).
**FAILING_ARTIFACT:** `python/experiments/INFR-020/design.md` (§0/§1.1/§3/§7 stale text; §2 W2a′; §5)
**REQUIRED_SKILL:** `quant-designer`

Withdrawing the fix rather than defending it was the right call, and the run-2 finding was
reproduced independently before acting rather than taken on my word. That is the correct response.

### 1. Run-2 residual disposition

| # | Run-2 residual | Verified | Verdict |
|---|---|---|---|
| R-1 | Ledger claim false; 37 instruments; instrument-exclusion breaks cross-pair population | Claim withdrawn; excision adopted. Ledger figures re-verified: `outage_minutes = 0` universal ✓; `collection_gap_minutes > 0` on 37 of 194 ✓; OMGUSDT 138,240 ✓; AVAXUSDT 8,640 ✓. **But the frame is wrong and my own R-1 sub-claim was wrong — see S-2.** | **PARTIALLY RESOLVED** |
| R-2 | **BLOCKING** — fill manufactures the absorption signature | `diag_fill_bias.py` re-run: **reproduces byte-identically**. Every figure in §2 W2a's table matches the artifact (ALICEUSDT 5m range-zero 0.0167→0.2624, candidates 32→89, 82 touching = 92.1%, median traded fraction 0.60; 15m 2→16 at 100%; SKLUSDT 5m 3→20 at 90%; LTC/SOL 0%). Fill withdrawn from every *substantive* path; A8/A9/A10 sited at the event layer. Independent confirmation of the mechanism: the recurring `p10_range_resid` values −0.674491, −0.944287, −1.011736 are exactly −1.0/1.4826, −1.4/1.4826, −1.5/1.4826 — i.e. the residual of a **zero-range** bar in a cell whose median range is 1–1.5 ticks. Under the fill the p10 cut *is* the zero-range bar. | **RESOLVED in substance** (propagation → S-1) |
| R-3 | A6 replacement unscoped, assumed the fill, exact equality | Demoted from assert to reported statistic with the analytic expectation shown beside it. Correct — coverage is a disclosure, not a gate. | **RESOLVED** |
| R-4 | Degenerate range cells uncounted | A10 added, counts **and names** them. | **RESOLVED** |
| R-5 | W4 trace mis-cited to SPDR-009 GT-1 | Corrected, with the real GT-1 (SOLUSDT 2022-12-28) named as the thing it is not. Values re-verified from staging: 20833.0 / 21020.5 / 187.5. | **RESOLVED** |
| R-6 | Whole-archive vs DESIGN-band counts unlabelled | Labelled in §5. **But the same frame error recurs untreated in §2 W2a′ — S-2.** | **PARTIALLY RESOLVED** |
| R-7 | A-H4 prior-lowering unscoped | Scoped precisely: anchor quality, not absorption at a level, "both halves travel together". Accurate. | **RESOLVED** |
| R-8 | `zero_fill` left Delta/Turnover null | Corrected; helper retained on disk as pinned evidence for its own withdrawal — right instinct. | **RESOLVED** |
| R-9 | LTCUSDT obs/cell 16 vs 15.5 | Corrected to 15.5. | **RESOLVED** |
| L-23 ledger | AMENDMENT-1 mis-scored TIGHTER | Re-scored LOOSER; AMENDMENT-6 TIGHTER for the withdrawal; 1L/6T/4N recorded rather than netted. The closing note — "a loosening was proposed, measured, and reversed rather than never having happened" — is exactly what L-23 exists for. | **RESOLVED** |

### 2. Answers to the two questions posed

**(1) Does classification-only genuinely close R-2, or can a partial window still influence a cut?**

Substantively **yes, the fabrication channel is closed** — with one live exception in the text.
Staging contains no zero-volume minutes (min `NTrades` = 1, verified run 1), so `COMPLETE` ⇒ every
source minute traded ⇒ `traded_fraction` = 1.0 ⇒ no synthetic bar can enter a cell median or a
percentile cut. Fitting and event eligibility are both restricted to `COMPLETE`, which closes the
depressed-median channel at its source. I traced the remaining paths and found no second route:
`NO_TRADE_PARTIAL` is disclosure-only; `GAP_CONTAMINATED` is excised; the 1-minute path is untouched
so D1 is unaffected; W5's levels come from prior-HTF-session 1-minute bars.

**The exception is §1.1.** The object-identity block — the *normative definition of the shared
predicate SPDR-009 imports* — still reads "on a **zero-filled LTF series**" (line 46). That is the
one text a consumer takes its semantics from, and it still specifies the withdrawn fill. See S-1.

**(2) Is accepting the coverage loss right, or is there a non-fabricating remedy you missed?**

**Accepting it is right. There is no remedy that recovers thin instruments at D3/D4 without either
fabricating data or abandoning the frozen A5 object.** Options considered:

| Candidate remedy | Why it fails |
|---|---|
| Zero-fill / any imputation | Fabrication. Measured and withdrawn. |
| Tolerant retention + metrics on traded minutes only (my run-2 suggestion) | Your rejection is correct and I withdraw it. Partial windows would still set cell medians, and High/Low/Volume remain understated on the very windows the low-range leg selects. Gating events without gating the fit leaves the defect in the fit. |
| Activity/volume-clock bars | Recovers bars without fabricating, but destroys the slot-of-day seasonal key A5 is defined on and breaks D6.3's clock comparability across pairs. That is a different apparatus, not a fix to this one. |
| Coarser seasonal key for thin instruments | Does not help: the loss is **retention** (bars dropped), not **cells**. `MIN_CELL_OBS` fallback already handles the cell side. |

What *is* available and not taken is not a recovery but a **quantification** — §5 declares the loss
qualitatively where the numbers exist and are much worse than the sample implies (S-3), and it omits
the conditioning statement the disposition will need (S-4).

### 3. Verification of the new material

| Claim | Method | Result |
|---|---|---|
| `diag_fill_bias.json` | re-ran the script, byte-compared | **Reproduces exactly.** |
| §2 W2a table vs artifact | line-by-line | Matches on every cell. |
| `diag_fill_bias.py` computes no forward outcome | read in full (121 lines) | **Confirmed** — cuts, counts, fractions only. |
| §5 table now shows raw as operative | read | Correct; filled column retained as withdrawal evidence with LTCUSDT 15.5 fixed. |
| A-FUND scoping (R-7) | re-read against registry | Accurate and appropriately narrow. |
| W4 IB trace | recomputed from staging | 20833.0 / 21020.5 / 187.5 ✓ |
| Ledger `gap_runs` / `unresolved_error_days` carry gap **timestamps**? | inspected all fields | **NO** — `gap_runs` is a run-length histogram (`{"1m": 19309, "2-5m": 3995, "6-60m": 53, "gt60m": 1}`); `unresolved_error_days` is an integer count. → S-2 |
| "gaps are single contiguous runs" (my R-1 claim, adopted verbatim at W2a′) | checked against `gap_runs` | **FALSE for the worst cases.** OMGUSDT: `max_gap_run_min` 12,960 vs `collection_gap_minutes` 138,240, with 13 runs > 60m. True for the 8,640-minute cluster only. **My run-2 assertion was wrong and the design inherited it.** → S-2 |

### 4. Residuals

**S-1. [MAJOR] The withdrawal is not propagated; §1.1 still defines the shared predicate on the zero-filled series.**
§2/§4/§5/§8 execute the withdrawal cleanly. Six other places still describe the fill as live, and one
of them is definitional:
 - **§1.1 line 46 — "…on a `zero-filled LTF series`, inside a session whose HTF anchor and IB are
   this item's."** This is the OBJECT-IDENTITY block, i.e. the specification of
   `absorb_candidate_predicate()` **that SPDR-009 imports rather than reimplements**. As written, the
   contract SPDR-009 inherits still names the withdrawn fill. This is the one remaining path by which
   a partial window could influence a cut, and it is the highest-consequence line in the file.
 - §0 "Produces": "(W2a) no-trade-minute reconstruction" — contradicts the §2 W2a heading.
 - §1 blocker 4: "Unaddressed, this alone would make D3 and D4 unusable" — after the withdrawal it
   *is* unaddressed by design; the sentence now implies a fix exists.
 - §3 INFORMATIVE: "per-instrument fill volumes".
 - §7 modules: "`xen.sigbar.ltf` (**zero-fill**, …)"; also still lists `assert_no_collection_gaps`,
   which §3 replaced with `assert_windows_complete`.
 - §7 artifacts `fill_report.json`; §7 plots "before/after zero-fill"; §7 execution order
   "→ **W2a fill** + A8 →".
 - Header line 8 still describes revision 2 as the current state.
*Required:* propagate. §1.1 first — the predicate is defined on the **`COMPLETE`-window LTF series**.

**S-2. [MAJOR] `GAP_CONTAMINATED` is not computable from the source it cites, and the 37-instrument figure is the wrong frame — only 8 are affected in the DESIGN band.**
Three separate errors, one of them mine:
 - **(a) Not computable.** W2a defines `GAP_CONTAMINATED` as "any missing minute falls inside a
   `collection_gap_minutes` run". The ledger records no gap timestamps — `gap_runs` is a length
   histogram and `unresolved_error_days` an integer. The classification cannot be evaluated from the
   ledger. `INFR-011/scripts/admission_gate.py:322-341` shows `collection_gap_minutes` is derived
   from **unresolved missing day-files**, and those intervals were never persisted.
 - **(b) Wrong frame — the R-6 error recurring inside the section that fixed it.** The ledger spans
   the whole archive (BTCUSDT `first_bar` 2022-07-15 → `last_bar` 2026-07-14); INFR-020 reads only
   DESIGN. Measured, per instrument, as UTC days with **zero** bars inside the instrument's own
   DESIGN span: **8 of 194**, not 37 — OMGUSDT 42/505d, ONEUSDT 27/325d, BNXUSDT 11/328d,
   CELOUSDT 6/229d, TWTUSDT 5/103d, BCHUSDT 3/229d, CTSIUSDT 3/343d, GSTUSDT 2/81d. **AVAXUSDT — the
   design's headline example, "one of SPDR-009's ten census instruments" — has ZERO affected days in
   the DESIGN band** (its 6 error-days fall outside it), as does OGNUSDT (25 days, none in band). The
   argument for excision-over-exclusion is still right; the evidence cited for it is not.
 - **(c) My run-2 claim was wrong.** I asserted `max_gap_run_min == collection_gap_minutes` implies
   single contiguous runs; the design adopted it verbatim at W2a′. False for OMGUSDT (12,960 vs
   138,240; 13 runs > 60m). It holds only for the 8,640-minute cluster. My error, propagated —
   correct it in both documents.
*Required, and cheap:* derive gap days from **staging**, not the ledger — a UTC day inside an
instrument's DESIGN span with zero bars is a missing day-file. Excise those days; reconcile the
count against `unresolved_error_days` where the ledger flags the instrument, and **report the
mismatches**: 2 of the 8 (BNXUSDT, GSTUSDT) show in-band day-holes the ledger does **not** flag, so a
ledger-driven rule would have missed them. Restate the in-band figure as 8 of 194.

**S-3. [MAJOR] §5 understates the coverage loss: the five-instrument sample is unrepresentative and no universe-level number is given.**
§5 says D3/D4 are "measurable on the liquid core and UNPOWERED across much of the thin tail". The
direction is right; the magnitude is not stated, and the sample flatters it — its worst instrument
(CRVUSDT, 0.204 at 60m) sits near the **32nd percentile** of the universe. Measured across all 194
DESIGN-band instruments:

| pair | median retention | ≥0.90 | ≥0.50 | <0.20 |
|---|---|---|---|---|
| **D2** 1h/5m | **0.385** | 20 (10%) | 72 (37%) | 28 (14%) |
| **D3** 4h/15m | **0.201** | 11 (6%) | 47 (24%) | 95 (49%) |
| **D4** 1d/1h | **0.088** | 6 (3%) | 31 (16%) | 132 (68%) |

The median instrument keeps **8.8%** of its hourly windows. At a 0.50 retention floor the usable
universe is ~72 / ~47 / ~31 instruments for D2 / D3 / D4 against 194 at D1 — and **D2 is affected
too**, which §5's "D3 and D4 are liquidity-limited" wording does not convey. This is load-bearing
beyond disclosure: SPDR-009 §6.3 projects "pooled pool-P of order 10³–10⁴ events" from the
~194-instrument universe, and D6's stated purpose was to escape a 19-event census. A widening that
delivers ~31 instruments at D4 changes that projection before τ is frozen.
*Required:* run `diag_coverage.py` over all 194 and publish the retention distribution per timeframe
in §5; state the usable universe per pair at a predeclared retention floor; and extend the
liquidity-limited statement to D2.

**S-4. [MAJOR] The surviving population is activity-conditioned, unequally across the cross-section, and this is not disclosed.**
§5 frames strict retention as lost coverage. It is also a **selection on activity**: a `COMPLETE`
hour is by construction an hour in which the instrument traded every single minute. Measured, median
hourly volume of `COMPLETE` vs partial 60m windows:

| symbol | 1m coverage | COMPLETE | partial | median volume ratio |
|---|---|---|---|---|
| SOLUSDT | 0.999 | 5,302 | 218 | **3.2×** |
| MATICUSDT | 0.991 | 11,396 | 3,238 | **4.4×** |
| LTCUSDT | 0.959 | 2,700 | 2,796 | **3.1×** |
| AAVEUSDT | 0.874 | 1,125 | 4,395 | **3.6×** |
| CRVUSDT | 0.868 | 1,121 | 4,375 | **2.4×** |
| SKLUSDT | 0.571 | 140 | 5,351 | **26.9×** |

So D3/D4 do not measure "absorption"; they measure **absorption during hours in which the instrument
traded continuously** — and the conditioning is strongest exactly where coverage is worst (SKLUSDT's
140 surviving hours carry 27× the median volume of its dropped ones). Because the strength varies
2.4×–27× across instruments, the conditioning is **not constant across the cross-section**, so a
pooled D3/D4 read mixes instruments conditioned to very different degrees. This is the survivorship
analogue of Addendum §2.9's breadth-honesty rule, and it is the framing SPDR-009's disposition needs.
Note this is *not* an argument to restore the fill — the fill made it worse by fabricating the other
tail. It is an argument that the disclosure must be a **conditioning** statement, not only a coverage
statement.
*Required:* state it in §5 in SPDR-009-facing terms and carry the per-instrument ratio in the
coverage report so a pooled read can be stratified or declared disclosure-only.

**S-5. [MINOR] §5's complementarity claim overstates D1's null on the majors.**
"At D1 the majors contributed **zero** signal events (SPDR-009 §6.3)" — true for BTCUSDT and ETHUSDT
(0 and 0 on pool P), false for SOLUSDT (5), ADAUSDT (5), MATICUSDT (4), LINKUSDT (2). The
complementarity argument survives in weakened form; state it as "the two largest contributed zero".

**S-6. [MINOR] A9 is not an independent guard — say so.**
A9 ("no candidate has `traded_fraction < 1.0`") is implied by A8 given the staging invariant that no
zero-volume minute exists: `COMPLETE` ⇒ `traded_fraction` = 1.0 identically. It is worth keeping as a
cheap tripwire that would fire if staging ever admits zero-volume rows, but it should not be
presented as a second, independent line of defence at the event layer.

**S-7. [MINOR] §1 blocker 1's "raises otherwise" is misleading, and the real hazard is silent.**
`fit_seasonal_baseline` raises only when the **emitted** grid is not 1440×7. Fed 5-minute bars it does
**not** raise: measured on BTCUSDT 5m it returns a full 10,080-cell grid of which **2,016 are
populated and 8,064 (80%) are empty and silently fall back to the day-of-week marginal**. The
justification for W1 is therefore stronger than stated — the generalisation prevents a *silent* 80%
fallback, not an exception. Two consequences: VT-4(d) does catch this once `bar_minutes` is passed,
so keep it; and `diag_fill_bias.py` **deliberately relies on this behaviour** (it calls the 1m fitter
on 5m/15m bars). Its numbers remain valid — the 1440-grid is a superset of the 288-grid and no
coarse bar ever maps to an unused cell — but record that, so a later "fix" to the diagnostic does not
silently change the pinned withdrawal evidence.

### 5. Trace items added

| # | Clause | Post-implementation trace |
|---|---|---|
| T18 | §2 W2a | `window_class` derived from staging day-holes, not the ledger; count reconciled to `unresolved_error_days` per instrument; mismatches (BNXUSDT, GSTUSDT) reported (S-2) |
| T19 | §1.1 | `absorb_candidate_predicate()` operates on the `COMPLETE`-window series; SPDR-009's import resolves to the same function object (S-1) |
| T20 | §5 | coverage report carries retention distribution over all 194 and the `COMPLETE`-vs-partial volume ratio per instrument (S-3, S-4) |

---

## QA run 4 — 2026-07-21T20:30Z — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time (read via `.git/HEAD` / `.git/refs/heads/main`; no live `git status` in this
tooling): same tree as runs 1–3 at HEAD `797f926…`; `python/experiments/INFR-020/` design +
`design_derivations/` are the working changes under review (still untracked / not in that commit).

**Stage: DESIGN-ONLY.** `python/experiments/INFR-020/code/` empty. Implementation trace items
T1–T20 remain open. This run adjudicates design rev 4 against QA run 3 residuals S-1…S-7 only.

**Verdict: REVISE** — all seven run-3 residuals closed on their required elements; **one new MINOR**
(inverted universe-percentile claim in §5).
**FAILING_ARTIFACT:** `python/experiments/INFR-020/design.md` (§5 CRVUSDT percentile)
**REQUIRED_SKILL:** `quant-designer`

---

### 1. Run-3 residual disposition (S-1…S-7)

| # | Run-3 residual | Verified | Verdict |
|---|---|---|---|
| **S-1 [MAJOR]** | Zero-fill withdrawal not fully propagated; §1.1 still on zero-filled LTF series | Grep of live paths: no `fill_report`, no `assert_no_collection_gaps`, no "W2a fill", no "before/after zero-fill". §0 Produces = window-integrity classification, **no fabricated bars**. §1.1 OBJECT-IDENTITY: `COMPLETE-window LTF series (window_class == COMPLETE; traded_fraction == 1.0)` + explicit "Zero-fill / reconstruction is WITHDRAWN". §1 blocker 4: accepted by design, not repaired. §3 INFORMATIVE: COMPLETE-vs-partial volume ratios (no fill volumes). §7 modules: `absorb_candidate_predicate` on COMPLETE only; artifacts `gap_excision_report.json` not `fill_report`; plots retention+vol-ratio not fill before/after; execution order "W2a classify + A8 … no fill". Remaining zero-fill mentions are historical (W2a defect table, withdrawal narrative, amendment ledger). | **RESOLVED** |
| **S-2 [MAJOR]** | GAP_CONTAMINATED not computable from ledger; wrong 37-instrument frame; contiguity false | W2a/W2a′: gap days from staging (UTC day with zero bars in instrument DESIGN span). Table vs `diag_universe_coverage.json` **exact** on all 8: OMG 42/505, ONE 27/325, BNX 11/328 ledger_err=0, CELO 6/229, TWT 5/103, BCH 3/229, CTSI 3/343, GST 2/80 ledger_err=0. AVAXUSDT `gap_days_in_band=0` with ledger_err=6. OGNUSDT gap=0, ledger_err=25. Ledger `collection_gap_minutes>0` still 37 of 194 (confirmed count). Contiguity corrected: OMG max_run 12,960 vs coll_gap 138,240. BNX/GST ledger misses named. | **RESOLVED** |
| **S-3 [MAJOR]** | Full-universe retention + usable floor + D2 liquidity-limited | §5 publishes full-universe table from `diag_universe_coverage.json`. Independently re-derived **60m** threshold counts from the 194 rows: **≥0.90 = 6**, **≥0.50 = 31**, **<0.20 = 132** — exact match to design. D2 called liquidity-limited. Activity of usable floor 72/47/31 stated. **But** the commentary "CRVUSDT … 32nd percentile" is **inverted** — see N-1. Required S-3 elements are met. | **RESOLVED** (N-1 new) |
| **S-4 [MAJOR]** | Activity-conditioning disclosure | §5 table + universe median claim present. Sample vs JSON (60m): SOL 0.9605/5302/218/3.21 (design 0.961/5302/218/3.2×); MATIC 0.7787/11396/3238/4.43 (0.779/…/4.4×); LTC 0.4913/2700/2796/3.15 (0.491/…/3.1×); AAVE 0.2038/1125/4395/3.6; CRV 0.204/1121/4375/2.43 (2.4×); SKL 0.0255/140/5351/26.86 (0.026/…/26.9×). Extremes: STXUSDT vol_ratio 187.02, SRMUSDT 0.32 — matches "0.3×–187×". BTC vol_ratio null ⇒ n=193 for median. Conditioning framed for SPDR-009. | **RESOLVED** |
| **S-5 [MINOR]** | Complementarity = BTC/ETH zero signal, not "majors" | §5: "at D1 **BTCUSDT and ETHUSDT** contributed zero signal events; SOL/ADA/MATIC/LINK did contribute." No remaining "majors contributed zero" overstatement. | **RESOLVED** |
| **S-6 [MINOR]** | A9 not independent of A8 | §4 A9: "Not an independent guard (QA-3 S-6): … COMPLETE ⇒ traded_fraction = 1.0 identically, so A9 is implied by A8. Kept as a cheap second tripwire…" | **RESOLVED** |
| **S-7 [MINOR]** | Blocker 1 silent 80% fallback, not "raises otherwise" | §1.1 blocker 1: raise only on emitted grid height; BTCUSDT 5m → 2,016 populated / 8,064 (80%) silent dow-marginal fallback; `diag_fill_bias` reliance recorded. | **RESOLVED** |

### 2. Independent re-derivation (from `diag_universe_coverage.json`, not design prose)

| Claim | Independent result | vs design |
|---|---|---|
| n instruments | 194 symbols | match |
| in-band gap days > 0 | **8** instruments, same names/counts as W2a′ table | match |
| AVAXUSDT / OGNUSDT in-band gaps | 0 / 0 | match |
| BNXUSDT / GSTUSDT ledger_err | 0 / 0 with in-band day-holes | match |
| ledger collection_gap > 0 | **37** of 194 | match (whole-archive frame, correctly scoped) |
| 60m ≥0.90 / ≥0.50 / <0.20 | **6 / 31 / 132** | match |
| 60m median | mid-pair of sorted list ≈ **0.088–0.089** (design prints 0.089; run 3 printed 0.088) | accept as rounding of mid-pair |
| CRVUSDT 60m rank | ret=0.204; **133** instruments strictly below ⇒ **~69th** percentile (not 32nd) | **FAIL — N-1** |
| Activity sample (6 names) | all n_complete / n_partial / vol_ratio match JSON within design's displayed rounding | match |
| §5 five-name raw table vs `diag_coverage.json` | BTC/ETH/SOL/LTC/CRV retentions still consistent with prior pinned diag | match (not re-run scripts this pass; JSON on disk checked) |

Script path left for operator re-run if desired: `design_derivations/_qa4_rederive.py` (scratch; not part of design).

### 3. Zero-fill / stale-path grep (live semantics only)

| Pattern | Live claim? | Notes |
|---|---|---|
| `zero-filled LTF` / zero-fill as operative path | **No** | Only AMENDMENT-11 historical quote |
| `fill_report` | **No** | Removed from §7 artifacts |
| `assert_no_collection_gaps` | **No** | Replaced by `assert_windows_complete` |
| `W2a fill` / before-after fill plots | **No** | Execution order is classify; plots are retention+vol-ratio |
| "for every instrument" gap=0 | **No** as live claim | Only as withdrawn false assertion in W2a′ / AMENDMENT-7 history |

### 4. D6.4 discharge (ckpt-015) — still holds under rev 4

| D6 requirement | Clause | Verdict |
|---|---|---|
| D6.4.1 baselines 5m/15m/1h grids | W1 | **MATCHES** (silent-fallback hazard now correctly stated) |
| D6.4.2 class thresholds p90/p10 unchanged rule | W3 | **MATCHES** |
| D6.4.3 1h/4h operational anchors, no race | W4 | **MATCHES** (A-H4/A-FUND scoping retained) |
| D6.4.4 IB 15 min wall-clock; D4 60 min deviate | W4 | **MATCHES** |
| D6.4.5 zone = prior HTF range + D1 ib_width sensitivity | W5 | **MATCHES** |
| D6.3 1-minute invariant | §1.2 + `assert_levels_from_1m` | **MATCHES** |
| No forward outcome | §0/§3 two-layer ban | **MATCHES** (impl → T1) |

### 5. Governance & mandatory blocks

| Block | Status |
|---|---|
| Applicability table §0 | all 13 addressed; N/A reasons intact |
| OBJECT-IDENTITY §1.1 | filled; COMPLETE-window predicate |
| HARD/INFORMATIVE §3 | filled; activity ratios informative |
| GOLDEN-TRACE §6 | VT-1..3 + W4 IB + VT-4; W3/W5 gap declared |
| AMENDMENT ledger §8 | AMENDMENT-11…14; running **1L/8T/6N** arithmetic checks out |
| CONVERSION-PIN / SPREAD / derangement / BacktestNode | correctly N/A |
| Holdout / counted reads 0 | MATCHES |
| `code/` empty | DESIGN-ONLY; `check_no_local_accounting` N/A until impl |

### 6. Issues

**N-1. [MINOR — design] §5 "CRVUSDT … 32nd percentile" is inverted.**
§5 universe-retention paragraph. Re-derived from `diag_universe_coverage.json`: CRVUSDT 60m
retention = **0.204**; instruments with retention **strictly below** 0.204 = **133 / 194**
(≈68.6%) ⇒ CRV sits near the **69th percentile**, not the 32nd. (About **31%** of the universe
has *higher* 60m retention — that 31% is the number that was likely mislabeled as "32nd
percentile".) Directional claim still true: the five-name sample flatters coverage because its
worst case (CRV) is better than the universe median (~0.089). Load-bearing counts (6 / 31 / 132
and usable 72 / 47 / 31) are correct.
*Required:* replace "32nd percentile" with "~69th percentile" (or "only ~31% of instruments retain
more hourly windows than CRVUSDT").

### 7. Carried-forward implementation trace

T1–T20 from runs 1–3 remain open (`code/` empty). No new T-items beyond N-1's design fix.

### 8. Note to the operator

Rev 4 did the hard work: withdrawal fully propagated through the shared predicate, gap rule made
computable from staging with the right in-band frame (8 not 37; AVAX clean in band), and
coverage/activity numbers published at universe scale. One leftover percentile label is wrong and
should be fixed before this design is treated as frozen commentary for SPDR-009 — but it does not
reopen the fabrication channel or the gap rule.

---

## QA run 5 — 2026-07-21T22:05Z — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time (read via `.git/HEAD` / `.git/refs/heads/main`; no live `git status` in this
tooling): same committed tree as runs 1–4 at HEAD `797f926…`; `python/experiments/INFR-020/` design +
`design_derivations/` + this `qa-review.md` are the working changes under review (untracked / not in
that commit).

**Stage: DESIGN-ONLY.** `python/experiments/INFR-020/code/` empty. Implementation trace items
T1–T20 remain open. This run adjudicates the post–QA-4 N-1 fix only, with S-1…S-7 regression
spot-check. Design still labeled **Revision: 4** in the header; AMENDMENT-15 records the N-1 fix.

**Verdict: APPROVE**
**FAILING_ARTIFACT:** none (design-stage)
**REQUIRED_SKILL:** none for design residuals; `experiment-developer` when implementation begins
(T1–T20)

---

### 1. N-1 disposition (only open residual from run 4)

| # | Run-4 residual | Verified | Verdict |
|---|---|---|---|
| **N-1 [MINOR]** | §5 labelled CRVUSDT 60m retention "32nd percentile"; true rank ~69th | Live §5: "CRVUSDT 60m retention 0.204 sits near the **69th percentile** … only ~31% of instruments retain more than CRV". AMENDMENT-15 records the correction (NEUTRAL; running **1L/8T/7N**). "32nd" survives only inside AMENDMENT-15 history (correct). | **RESOLVED** |

### 2. Independent re-derivation (`diag_universe_coverage.json`)

| Claim | Independent result | vs design |
|---|---|---|
| n instruments | **194** symbols | match |
| CRVUSDT 60m retention | **0.204** (`n_complete` 1121, `n_partial` 4375, `vol_ratio` 2.43) | match |
| n with 60m retention **strictly &lt; 0.204** | **133** / 194 | match (AMENDMENT-15 cites 133/194) |
| percentile (higher = better retention) | 133/194 ≈ **68.6%** → **~69th** | match live §5 |
| share with *higher* 60m retention than CRV | ≈ **31%** | match live §5 wording |
| 60m ≥0.90 / ≥0.50 / &lt;0.20 | **6 / 31 / 132** (re-checked: ≥0.90 count = 6 on disk) | match universe table D4 row |
| in-band `gap_days_in_band` &gt; 0 | **8** names (OMG 42, ONE 27, BNX 11, CELO 6, TWT 5, BCH 3, CTSI 3, GST 2) | match W2a′ |
| ledger `collection_gap_minutes` &gt; 0 | **37** of 194 | match whole-archive frame |
| activity sample (SOL/MATIC/LTC/AAVE/CRV/SKL) | ret / n_complete / n_partial / vol_ratio still match JSON within design rounding | match |

Method: counted 60m `retention` over all 194 rows; `n_below = sum(r < 0.204)` = 133; no reliance on design prose for the rank.

### 3. S-1…S-7 regression spot-check (live paths only)

| # | Residual | Spot-check | Verdict |
|---|---|---|---|
| **S-1** | Zero-fill withdrawn; COMPLETE-window shared predicate | §1.1 OBJECT-IDENTITY: COMPLETE + traded_fraction=1.0; "Zero-fill / reconstruction is WITHDRAWN". Grep: no live `fill_report`, `assert_no_collection_gaps`, `W2a fill`, or before/after fill plots. §7 execution: "W2a classify + A8 … no fill"; artifacts `gap_excision_report.json`. Zero-fill mentions are historical (W2a defect table, AMENDMENT-6/11). | **still RESOLVED** |
| **S-2** | Staging gap days; 8 not 37; contiguity false for worst | W2a/W2a′ still derive gaps from staging; table exact vs JSON; AVAX/OGN out-of-band; OMG contiguity correction retained. | **still RESOLVED** |
| **S-3** | Full-universe retention + usable floor | §5 universe table present; D2 called liquidity-limited; 72/47/31 at 0.50 floor. | **still RESOLVED** |
| **S-4** | Activity-conditioning disclosure | §5 COMPLETE/partial vol-ratio table + universe median ~6.7× (n=193) retained. | **still RESOLVED** |
| **S-5** | BTC/ETH not "majors" | §5: BTCUSDT and ETHUSDT zero signal; SOL/ADA/MATIC/LINK did contribute. | **still RESOLVED** |
| **S-6** | A9 non-independent of A8 | §4 A9 still declares implied by A8 under staging min NTrades=1. | **still RESOLVED** |
| **S-7** | Blocker 1 silent 80% fallback | §1 blocker 1 still states raise-on-height only + 2016/8064 silent dow-marginal; diag_fill_bias reliance recorded. | **still RESOLVED** |

### 4. Governance & stage boundary

| Block | Status |
|---|---|
| Applicability / N/A blocks §0 | intact from run 4 |
| OBJECT-IDENTITY §1.1 | COMPLETE-window; no regression |
| AMENDMENT ledger §8 | AMENDMENT-15 present; **1L/8T/7N** arithmetic consistent |
| Holdout / counted reads 0 | MATCHES |
| `code/` empty | DESIGN-ONLY; `check_no_local_accounting` N/A until impl |
| Golden-trace / D6.4 | unchanged from run-4 MATCHES; not re-opened |

### 5. Issues

**None open at design stage.** N-1 closed; S-1…S-7 not regressed.

### 6. Carried-forward implementation trace

T1–T20 remain open until `code/` lands. This APPROVE is **design-only** — not an implementation or execution gate.

### 7. Note to the operator

The only leftover from run 4 (wrong CRV percentile label) is fixed and re-derived. Design is clean
enough to freeze commentary for SPDR-009 and to hand to implementation. Execution still waits on
code + a later pre-exec QA against T1–T20.


---

## Run 6 — post-implementation QA (2026-07-21) — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time (`git status --porcelain`): `docs/.../015-signed-value-absorption-screen/design.md` (M);
`python/src/xen/sigbar/{baselines,fences,sessions}.py` (M); `python/src/xen/sigbar/ltf.py`,
`python/experiments/INFR-020/`, `python/experiments/SPDR-009/` untracked.

**Stage: POST-IMPLEMENTATION.** `code/` present (`run_apparatus.py` 675 ln, `reproduction_battery.py` 564 ln);
full 194-symbol run on disk (`results/full_run_w5.log`). This is an **implementation gate, not an
execution gate** — APPROVE here would mean "the apparatus may be pinned and handed to SPDR-009",
nothing more.

**Verdict: REVISE** — 2 MAJOR (1 of them blocks the τ handoff), 4 MODERATE, 3 MINOR.
**FAILING_ARTIFACT:** `python/experiments/INFR-020/code/run_apparatus.py` (I-1, I-2, I-5),
`code/reproduction_battery.py` (I-3, I-7), `python/src/xen/sigbar/ltf.py` (I-6, I-9),
`python/src/xen/sigbar/fences.py` (I-8), `design.md` §2 W2a (I-4).
**REQUIRED_SKILL:** `experiment-developer` (I-1, I-2, I-3, I-5, I-6, I-7, I-8, I-9);
`quant-designer` (I-4 — a design claim that is structurally unreachable in any implementation).

Everything below was re-derived from the artifacts and from staging in this session. Design prose
and QA runs 1–5 were used only as the specification to trace against, never as evidence.

---

### 1. Design-fidelity trace T1–T20 (carried forward from runs 1–3)

| # | Clause | Code (file:line) | Verdict | Evidence |
|---|---|---|---|---|
| T1 | §3 `check_no_outcome_columns` + provenance layer | `fences.py:227-268` (list), `:252` (schema), `:271-303` (provenance) | **DEVIATES** | Both functions exist and both raise correctly on planted input (`fwd_return` → raise; `source_max_open+10m` → raise on 1,000 rows). But `assert_no_forward_provenance` is **never called in `run_apparatus.py`** (grep: NONE) — only in the battery, and only on aggregated 5/15/60m frames. No emitted artifact is checked by either layer. → **I-2** |
| T2 | §3 `assert_bar_causality()` | `ltf.py:197-231` | **DEVIATES** | Correct implementation (source window ⊂ `[open, open+N)`, plus `source_max_open < close`). Called only in the battery and only on `agg.head(500)` (`reproduction_battery.py:360`). Not on the production path. → **I-2** |
| T3 | §2 W1 generalisation on `bar_minutes` | `baselines.py:56-77` (`slots_per_day`, `full_grid_cells`), `:79-104` (`_with_seasonal_keys`), `:107-129` (`assert_seasonal_keys_valid`), `:141-218` (`fit_seasonal_baseline`), `:229-260` (`residualise`) | **MATCHES** | All four hard-wired 1440 sites parameterised. Int32 casts retained (measured: `mod` dtype Int32 at `bar_minutes` 1 and 5, range [0,1439] / [0,287]). `assert_seasonal_keys_valid(mod=9999, bar_minutes=5)` raises with the `[0, 287]` message; `slots_per_day(7)` raises (non-divisor). Emitted grids exact: 5m 2016×194×4 = 1,564,416 rows; 15m 672 → 521,472; 60m 168 → 130,368. |
| T4 | §3 `assert_design_only_fit()` | `fences.py:348-378`; called `run_apparatus.py:102, 143, 289` | **MATCHES** | Fed BTCUSDT CONFIRM (420,479 rows, max 2023-12-17) it raises. `BANDS` declares only `DESIGN`/`CONFIRM`; `load_bars(...,"TEST"/"HOLDOUT"/"OOS")` raises `unknown band`. TEST/holdout unreachable by construction. |
| T5 | §4 A1 value-identity vs `1b7244c8…` at `bar_minutes=1` | `reproduction_battery.py:185-255` | **PARTIAL** | Mechanism correct (join on `mod,dow`, f32 cast, null-pattern check, `n`/`sparse` exact). Passes on the 5 sample symbols on disk. **Design requires all 194.** I independently ran `a1_a1b` on 6 further random symbols (FTM, BNB, ILV, TLM, AKRO, ANT — incl. thin names): **all pass, no metric errors**. So the shortfall is evidence scope, not a suspected defect. → **I-3** |
| T6 | §4 A2 137-block reproduction + 194 extension | `reproduction_battery.py:258-308` | **PARTIAL** | Only the 5 sample symbols in the 137 are checked (`:263`); `n_pinned_blocks: 137` is printed but not traversed. I re-derived 4 further registry symbols (FTM, BNB, AKRO, ANT) from the frozen 1m pin: `high`/`low`/`n`/`abs_high` all match within 1e-4. `same_estimator` (`:300`) is **vacuous** — it compares an import to its own module attribute. → **I-3, I-7** |
| T7 | §4 A3 `A-USOPEN` L=15 frozen session object | `reproduction_battery.py:311-348` | **MATCHES** | Golden IB reproduced exactly: 20833.0 / 21020.5 / 187.5 on BTCUSDT 2022-07-15 13:30Z, 228 sessions. `ib_minutes_for_ltf(1)=15` = the frozen call. |
| T8 | §4 A4/A5 + A5b legacy cross-check | `ltf.py:234-246, 612-680`; `reproduction_battery.py:351-415` | **MATCHES (A5b weak)** | A4 additivity max gap 1.8e-12; A5 associativity passes. VT-1/2/3 **independently re-derived by me from `INFR-011/data/staging/bars/BTCUSDT.parquet`** — exact on all three periods. A5b is a *note*, not a measurement (`:399-407`). I ran the comparison the note declines to run: new aggregator vs `bar_aggregator.aggregate_ohlc` on BTCUSDT 5m, 65,952 joined windows — **max |Δ| = 0.0 on Open/High/Low/Close**. It should be an assert. → **I-7** |
| T9 | §2 W5 levels + range from 1m, DESIGN only | `run_apparatus.py:268, 286-305, 416-418`; `ltf.py:329-609` | **DEVIATES** | Levels genuinely come from 1m bars (`structural_levels_1m(bars, …)`), and I verified the whole seven-kind set against an independent brute-force derivation on 12 random SOLUSDT A-H1 sessions — **0 mismatches** (incl. K-UNIFORM POC/VA). Band is DESIGN (no date ≥ 2023-03-01 in any artifact). **But** `assert_levels_from_1m(level_source_bar_minutes=1)` at `:268` is passed a **literal** — it echoes a constant and can never detect a level priced off an aggregated bar. And the level set includes the **current** session's IB edges, which is not what §1.1 says and creates forward provenance. → **I-1, I-2** |
| T10 | §7 `check_no_local_accounting`; no BacktestNode; `classes.py`/`bar_aggregator.py` untouched | `run_apparatus.py:664-666` | **MATCHES** | I re-ran it myself on both `code/` and the whole experiment dir: `{'ok': True, 'banned_defs_found': []}`. `git status` shows no modification to `classes.py` or `bar_aggregator.py`. No Nautilus anywhere. |
| T11 | §7 pins: every artifact hashed; frozen inputs re-verified at entry | `run_apparatus.py:558-568, 594-662` | **DEVIATES** | Frozen inputs verified and recorded (`1b7244c8…`, `e3b9fd9b…`, `35d3375e…` — all match the design's declared pins). **`reproduction_battery.json` is absent from `pins.json`** because the production run used `--skip-battery` (`:571`). 7 of the 8 design-listed artifacts are pinned. → **I-3** |
| T12 | reconstructed rows carry Delta=0 etc. | — | **N/A (moot)** | Zero-fill withdrawn; no reconstruction path exists in `ltf.py`. Confirmed by reading the module end to end: no `datetime_range` fill, no `upsample`, no `join` against a synthetic minute index on any primary path. |
| T13 | `assert_no_collection_gaps()` refusal list | — | **N/A (superseded)** | Replaced by staging-derived gap days (rev 4). See T18. |
| T14 | A6-replacement scoped, tolerance honoured | `run_apparatus.py:516-524` | **MATCHES** | A6 is a reported statistic (`sparse_rate_volume`, `null_scale_range_cells` per symbol/tf), not an assert, as AMENDMENT-8 requires. |
| T15 | `traded_fraction` on every aggregated bar and census row | `ltf.py:176-189`; `run_apparatus.py:464-468` | **MATCHES** | `window_class`, `n_missing`, `traded_fraction`, `SourceBars`, `source_max_open` on every row. Census carries `min_traded_fraction`: measured across all 194 symbols × 4 pairs — **0 rows with a value other than 1.0 or null**. |
| T16 | `absorb_candidate_predicate()` single exported function, SPDR-009 imports it | `ltf.py:281-326`; SPDR-009 `design.md:188, 784` | **MATCHES (design-level)** | One definition, one call site in the runner (`:399`) and one in the battery (`:476`). SPDR-009's design commits to importing it ("no reimplementation of `absorb_candidate_predicate`"). SPDR-009 has no code yet, so the *import* itself is untestable — carried to SPDR-009's own QA. |
| T17 | null-scale cells reported per (symbol, tf, metric) | `run_apparatus.py:519-524` | **PARTIAL** | Reported for `range` at 5/15/60m — 81 nonzero (worst 1000FLOKIUSDT 576/2016 at 5m). **Not** reported for `volume`, and **not at all for the 1m/D1 path**, which is exactly where the one skipped symbol occurred. → **I-9** |
| T18 | gap days from staging, reconciled to the ledger, mismatches named | `ltf.py:36-69`; `run_apparatus.py:103-108` | **PARTIAL** | Derivation is from staging, not the ledger. Emitted result reproduces the design's §2 W2a′ table **exactly**: 8 instruments, OMG 42 / ONE 27 / BNX 11 / CELO 6 / TWT 5 / BCH 3 / CTSI 3 / GST 2; OMG spans are multi-run (6d, 9d, 9d, 9d…), consistent with the corrected contiguity claim. **The ledger reconciliation the design promises is not implemented** — `gap_excision_report.json` carries no `unresolved_error_days` comparison and does not name the BNX/GST ledger misses. Disclosure-only, but it is a stated deliverable. → **I-9** |
| T19 | predicate on the COMPLETE-window series | `ltf.py:310-322` | **MATCHES** | `window_class == COMPLETE` filter, then a hard raise if any surviving row has `traded_fraction < 1.0` (A9/VT-4(j)). W1 fits on COMPLETE only — verified by reconciliation, not by reading: `sum(n)` over the volume grid equals `n_complete` **exactly** for SOL (65,901 / 21,787 / 5,302), CRV (41,287 / 9,318 / 1,121), SKL (12,864 / 1,778 / 140). |
| T20 | coverage report: 194-symbol retention + COMPLETE/partial vol ratio | `run_apparatus.py:495-540` | **MATCHES** | Re-derived from `coverage_report.json`: median retention **0.3851 / 0.2011 / 0.0882**; ≥0.90 = 20 / 11 / 6; ≥0.50 = **72 / 47 / 31**; <0.20 = 28 / 95 / 132. Every load-bearing figure in design §5 reproduces. 60m vol-ratio: n=193, median **6.74×**, range **0.32×–187.02×** — matches "≈6.7×, 0.3×–187×". |

### 2. Targeted attacks

| Attack | Result |
|---|---|
| **Zero-fill / reconstruction absent from live paths** | **CLEAN.** No fill primitive anywhere in `ltf.py`, `run_apparatus.py`, or `reproduction_battery.py`. Missing minutes only ever *classify*. The one place a synthetic marker is written (`run_apparatus.py:322-326`, D1) stamps `window_class=COMPLETE`, `traded_fraction=1.0`, `SourceBars=1` on **real** 1-minute bars — definitionally true for a 1-minute window, not a fabricated row. |
| **COMPLETE-only predicate** | **CLEAN.** Enforced at `ltf.py:311-322`; W1/W3/W5 all pass `complete_only=True`. 0 census rows with `traded_fraction < 1.0` across 194×4. |
| **Gap days derived from staging, not asserted** | **CLEAN** (T18), ledger reconciliation missing (I-9). |
| **W1 reproduces the frozen 1m pin** | **PASSES on 11 symbols** (5 shipped + 6 I drew at random), **not on 194 as designed** (I-3). Frozen hash at battery entry = `1b7244c87aaa…` = the design's pin. |
| **Shared predicate emitted once** | **CLEAN** (T16). |
| **W5 count-only / §0 outcome ban** | **CLEAN in substance, unenforced in code.** I scanned every emitted JSON key (221/208/210/17/20/200 distinct keys): zero forbidden names, zero forward returns/excursions/P&L. But the ban is not machine-checked on any emitted artifact (I-2), and the blocklist misses this programme's own outcome names (I-8). |
| **D6.3 levels from prior HTF session's 1m bars** | **DEVIATES** — 1m yes (verified brute-force, 0/12 mismatches), *prior session only* **no**: current-session IB edges are in the level set. → **I-1** |
| **DESIGN-only fits/thresholds/census; CONFIRM read only for coverage; TEST/holdout untouched** | **CLEAN, and tighter than designed.** No artifact contains a date ≥ 2023-03-01. CONFIRM is never read at all — the coverage report is DESIGN-band. `BANDS` has no TEST/holdout key. |
| **VT-1..3** | **EXACT**, re-derived by me straight from staging without touching `agg_trace.py`. |
| **VT-4 raise conditions** | (a) ✓ raises on CONFIRM; (b) ✓ TEST/holdout not addressable; (c) ✓ via `complete_only`/`SourceBars`; (d) ✓ raises on slot key 9999 at `bar_minutes=5` and on non-divisor bar sizes; (e) ✓ schema + provenance both raise on planted input — **but neither runs on the production path** (I-2); (f) `assert_no_per_level_delta` exists but is **never called** in INFR-020; (g) **no machine check exists** for "A-H1/A-H4 consumed as an edge-bearing anchor" — `sessions_mtf.json` records `edge_bearing: false` as data, which is a declaration, not a fence; (h) ✓; (i) **tautological** (I-2); (j) ✓. |
| **Mid-run W5 vectorisation — behaviour-preserving?** | **Substantially yes, with one definitional wrinkle.** `structural_levels_1m` (asof-join + single `group_by` + `only_anchors` pruning): verified against an independent per-session brute force on 12 random SOLUSDT sessions — all seven level kinds identical to 1e-9, no extra kinds, no missing kinds. `prior_htf_session_ranges` (asof-join + `shift(1)`): value-identical wherever both define a value (0 mismatches), but session **membership** differs on gap-adjacent anchors — SKLUSDT A-H1: fast 5,451 vs brute-force 5,452, 4 extra / 5 missing out of ~5,456. → **I-6** |
| **"Skip incomplete thresholds with a note" — can it silently drop or bias the census?** | **Not silently, and it is rare — but the note is ambiguous to a machine consumer.** It fires exactly **once** in the whole run: BUSDUSDT at D1 (`threshold_keys: [volume, delta_abs, delta_ratio]` — no `range` cut, i.e. the null-MAD case A10 exists to surface). The symbol stays in the census with `n_candidates: 0` plus a `note`. A consumer reading `n_candidates` alone cannot distinguish "measured zero" from "not measurable"; 4 further symbols legitimately have 0 D1 candidates. Fix is a status field, not a redesign. Bias is negligible (1/194 at one pair). |
| **`reproduction_battery.json` = sample-path only. Sufficient?** | **No.** See I-3 for the exact re-run required. |
| **Shared-code boundary (SPDR-007/008 spine/trap/acceptance)** | **CLEAN — verified, not assumed.** `sessions.py` and `fences.py` diffs are pure additions. `baselines.py` keeps `bar_minutes=1` defaults; `mod`/`dow` dtypes unchanged (Int32); A1 value-identity on 11 symbols is itself the regression test for the 1m path. Decisive check: I ran `python/experiments/SPDR-008/screen_code/_smoke_trap.py` against its frozen golden traces — **"SMOKE OK — assert_ib_matches_frozen passed for both IB symbols"**, all four trap traces reproduce. |
| **`check_no_local_accounting`** | **PASSES** on `code/` and on the whole experiment directory. |

### 3. Independent re-derivation (numbers, not prose)

| Quantity | Design/prior-QA claim | Re-derived here | Verdict |
|---|---|---|---|
| universe | 194 | 194 in baselines, thresholds, census, coverage | ✓ |
| MTF baseline grids | 288/96/24 slots × 7 | 2016 / 672 / 168 cells, `mod` max 287 / 95 / 23, no `bar_minutes = 1` partition | ✓ |
| threshold blocks | per (symbol, tf) | 194 × {5m,15m,60m}, **0 missing**; each carries `high/low/n/high_pctl/low_pctl/applied_to` (L-24 F06 discharged) | ✓ |
| median retention 5m/15m/60m | 0.387 / 0.202 / 0.089 | **0.3851 / 0.2011 / 0.0882** | ✓ |
| usable at 0.50 floor | 72 / 47 / 31 | **72 / 47 / 31** | ✓ |
| ≥0.90 · <0.20 | 20·28 / 11·95 / 6·132 | identical | ✓ |
| 60m vol ratio | median ≈6.7×, 0.3×–187× | median **6.74×**, min 0.32, max 187.02, n=193 | ✓ |
| in-band gap instruments | 8 | **8**, same names and day counts | ✓ |
| window classes observed | 3-way classification | **2 only** — `GAP_CONTAMINATED` count is 0 universe-wide | **I-4** |
| W5 candidates | — | D1 95,836 (189 syms) · D2 9,497 (172) · D3 2,974 (118) · D4 640 (61) | recorded |
| symbols with a usable distance quantile | — | D1 189 · D2 172 · D3 **117** · D4 **60** | recorded — D4's τ would be frozen on 60 of 194 |

---

### 4. Issues

**I-1. [MAJOR — blocks the τ handoff] W5's census population and level set diverge from SPDR-009's event definition, and the divergence is forward-looking.**
`run_apparatus.py:404-456` + `ltf.py:487-498`. `structural_levels_1m` puts **this** session's `IB_HIGH`/`IB_LOW` in the level set, and W5 measures every candidate's distance against them regardless of where in the session the candidate sits. SPDR-009 §3.1 declares those levels available only "after IB wall-clock completes" and §2/§7 make it a HARD fence: *"IB-edge events before IB complete are REFUSED"*, *"an IB-edge event before IB wall-clock completes for that pair → raises"*.
Measured, SOLUSDT D2 (1h/5m, IB = 25% of session): **15 of 59 candidates (25.4%) sit inside their own IB window**; for **4** of them the nearest level *is* an IB edge that is not yet formed at the candidate's close; their distance distribution is materially different from the post-IB population (p50 0.048 vs 0.086, p90 **0.105 vs 0.282** in units of prior-session range). Pooled over the universe this is ~25% of 9,497 D2 rows and ~1% of D1's 95,836.
Two independent failures in one line: (a) **forward provenance** — a level price derived from 1-minute bars that close after the row's own bar close, the exact hole `assert_no_forward_provenance` was added to close; (b) **object-identity** — §1.1's whole purpose is that τ is not frozen against a population the screen never sees, and here the census population is strictly larger than SPDR-009's.
*Required:* in W5, compute `mins_since = candidate.OpenTime − anchor_ts` and (i) admit `IB_HIGH`/`IB_LOW` into a candidate's level set only when `mins_since ≥ ib_minutes`, and (ii) apply SPDR-009's refusal rule so a candidate whose nearest level would be an unformed IB edge is excluded from the census rather than measured against it. Re-run `--from-w5` (W1/W3/W4 are unaffected), re-emit `zone_scale_census.json` + `zone_scale_census_d1_ibwidth.json`, re-pin. Then state in §1.1 that the level set is *prior-session levels plus this session's IB edges once complete* — the current wording ("built from the PRIOR HTF SESSION'S 1-MINUTE BARS") does not describe either the code or SPDR-009.

**I-2. [MAJOR] The §3 HARD asserts are not on the path that produced the artifacts.**
`run_apparatus.py` imports and calls only `assert_design_only_fit`, `check_no_outcome_columns` (on intermediate `agg` frames at `:112` and on a hand-written string list at `:210-213`), and `assert_levels_from_1m`. Grep for the rest in the runner returns **NONE**: `assert_no_forward_provenance`, `assert_bar_causality`, `assert_split_additive`, `assert_windows_complete`, `assert_no_per_level_delta`. They exist, they are correct, and they run only inside the battery — which the production run skipped.
Worse, `assert_levels_from_1m(level_source_bar_minutes=1)` (`:268`, and `reproduction_battery.py:484`) is called with a **literal constant**. Design §1.2 specifies an assert that "raises if any level price is traced to an aggregated bar". A parameter echo cannot trace anything; it is guaranteed to pass. Same shape as the defect A7's provenance layer was invented to fix.
*Required:* (a) call `assert_no_forward_provenance` on every aggregated frame at the point of emission and carry a `source_max_open` bound into the W5 census rows; (b) call `assert_split_additive`, `assert_bar_causality` (full frame, not `head(500)`), and `assert_windows_complete` on the production path; (c) run `check_no_outcome_columns` over the **emitted artifacts** (parquet columns and JSON keys), not only over intermediates; (d) make `assert_levels_from_1m` take the level frame's actual source and derive the bar size, or delete it and replace with a provenance column on the level rows; (e) call `assert_no_per_level_delta` (card ban 2, §3 HARD, currently uncalled); (f) implement a real VT-4(g) check or demote it in the design from "must RAISE" to "declared, not enforced".

**I-3. [MODERATE] Battery evidence is 5 symbols where the design requires 194 / 137, and it is not pinned.**
`reproduction_battery.json` is `"mode": "sample"` over BTC/ETH/SOL/LTC/CRV. Design A1 requires value-identity **over the 194 fitted instruments**; A2 requires the **137** threshold blocks (`n_pinned_blocks: 137` is reported but only 5 are traversed, `:263`). The production run used `--skip-battery` (`run_apparatus.py:571`), so §7's "nothing downstream computes until the generalisation is proven inert" is satisfied only chronologically (battery 18:20Z, artifacts 18:24Z+) and only at sample scope, and `pins.json` carries **7 of 8** artifact hashes — `reproduction_battery.json` is absent.
Mitigating, and measured rather than assumed: I ran A1 on 6 further randomly drawn symbols (incl. thin AKRO/TLM/ANT) and A2 on 4 further registry symbols — all pass. So this is an evidence gap, not a suspected defect.
*Required, exactly:* extend `a2()` to iterate all 137 pinned symbols; run `reproduction_battery.py --full` (A1 over 194); re-run `run_apparatus.py --full` **without** `--skip-battery` (or, if W1–W4 are reused, re-run with `--from-w5` after the fixes and add `sha256(reproduction_battery.json)` to `pins.json`). No apparatus pin should be handed to SPDR-009 while the battery covering it is a 5-symbol sample.

**I-4. [MODERATE — design defect] `GAP_CONTAMINATED` is structurally unreachable; the shipped classification is two-way, not three-way.**
`ltf.py:87-91` flags a window when a *missing minute* falls on a gap day. Gap days (`ltf.py:36-52`) are whole UTC days with zero bars. 5/15/60-minute clock-aligned windows never straddle midnight, so a window either lies entirely inside a gap day — in which case `group_by_dynamic` emits no row at all — or contains no gap-day minute. Measured: across all 194 instruments × 3 timeframes the observed class set is `{COMPLETE, NO_TRADE_PARTIAL}`; `GAP_CONTAMINATED` count is **identically zero**, including on OMGUSDT (42 gap days).
This is not a fabrication risk — gap days are excised by producing no windows, which is the right outcome — but design §2 W2a/§4 A8 present "`GAP_CONTAMINATED` windows are excised and counted" as an active guard, and a reader (or the next QA run) will read a zero count as "checked and clean" rather than "unreachable by construction".
*Required:* either state in §2 W2a that the class is provably empty for day-aligned windows over whole-day gaps and that the gap disclosure lives in `gap_excision_report.json`, or widen gap detection below the day (partial-day holes) so the class carries meaning.

**I-5. [MODERATE] The D1 census rests on run-local thresholds that are never emitted or pinned.**
`run_apparatus.py:343-345`. For D1 the runner residualises against the frozen 1m pin (correct) but derives class cuts inline with `derive_thresholds`, and `class_thresholds_mtf.json` carries **no 1m partition** (verified). Of the 194 census symbols, **57 are absent from the frozen 137-block registry** — so for 57 instruments the D1 candidate population (part of 95,836 candidates and the whole `zone_scale_census_d1_ibwidth` artifact) cannot be reproduced from any pinned object. §1.1 requires W5's candidate bar to be the *same object* SPDR-009 sees; SPDR-009 cannot construct it.
*Required:* emit and pin the 1m threshold blocks for all 194 (a `1m` partition in `class_thresholds_mtf.json` or a separate artifact), with an assert that the 137 overlap reproduces `5c386984…` value-identically.

**I-6. [MODERATE] Prior-session identity differs between the zone scale and the level set.**
`ltf.py:375-384` derives `prior_session_range` by `shift(1)` over sessions **that contain bars**; `ltf.py:513-518` maps each consumer anchor to the **calendar-adjacent** prior anchor for `PRIOR_SESSION_HIGH/LOW/POC/VAH/VAL`. On instruments with empty sessions the two disagree: SKLUSDT A-H1 — 4 anchors get a range from a non-adjacent earlier session, 5 lose their range entirely (9 of ~5,456 ≈ 0.16%). Values are identical wherever both are defined, so this is a definition mismatch, not an arithmetic one — but on those rows the census divides a distance measured to session *k−1*'s level by session *j*'s range, and SPDR-009 rebuilding the level set will not reproduce them.
*Required:* pick one rule (calendar-adjacent prior session is the one the level set and SPDR-009 §3.1 use) and apply it to both; count and report anchors whose prior session is empty instead of silently shifting past them.

**I-7. [MINOR] Two battery members do not test what they claim.**
(a) `reproduction_battery.py:300` — `classes_mod.derive_thresholds is derive_thresholds` compares a name to its own module attribute and is True by construction; it cannot detect a lookalike estimator, which is what A2's extension clause asks for. (b) `:399-407` A5b is a prose note asserting the conventions "differ by construction". They do not differ in result: I measured the new aggregator against `bar_aggregator.aggregate_ohlc` on 65,952 BTCUSDT 5m windows and got **max |Δ| = 0.0 on all four price columns**. The check is cheap and should be an assert.
*Required:* delete the vacuous identity check or replace it with a real one (e.g. assert the 194-run and 137-run agree on the overlap); promote A5b to a numeric assert on a fixture.

**I-8. [MINOR] The outcome-ban blocklist omits this programme's actual outcome column names.**
`fences.py:227-250`. `check_no_outcome_columns(["ret_bps"])` does **not** raise, nor would `ret_norm`, `ret`, `trap_load`, `mfe_rev_norm`, `mae_rev_norm`, `bite`, `edge_bps` — the names SPDR-007/008/009 actually emit. The list covers generic English (`return`, `pnl`, `mfe`) but not the vocabulary in use.
*Required:* add the programme's own outcome names, and prefer a substring/prefix rule (`ret`, `pnl`, `mfe`, `mae`, `excursion`) over exact match.

**I-9. [MINOR] Silent drops and unfinished disclosures.**
(a) `ltf.py:426` filters `ib_width > 0` and `:383` filters `prior_session_range > 0` — dropped sessions are not counted anywhere, so a thin instrument's D1 ib-width denominator shrinks without disclosure. (b) A10 null-scale reporting covers `range` at 5/15/60m only (81 nonzero entries; worst 1000FLOKIUSDT 576/2016 at 5m) — not `volume`, and not the 1m/D1 path where the single skipped symbol (BUSDUSDT) actually arose. (c) `gap_excision_report.json` does not carry the ledger reconciliation or name the BNX/GST ledger misses that §2 W2a promises. (d) `assert_windows_complete` is defined twice with slightly different messages (`ltf.py:249` and `fences.py:305`) — two copies of a HARD assert can drift. (e) `ltf.py:552` `inv` is dead code. (f) the "incomplete thresholds" skip should emit a status field (`measurable: false`) rather than `n_candidates: 0` + a free-text note, so a machine consumer cannot read it as a measured zero.

---

### 5. Note to the operator

The apparatus is in good shape on the things earlier runs bled over: no fabricated minutes anywhere,
COMPLETE-only fitting reconciles exactly, coverage reproduces the published universe numbers to the
digit, the frozen 1-minute baseline is untouched, and the existing SPDR-008 consumer still passes its
golden traces after the shared-module edits.

What is not ready is the one artifact SPDR-009 will freeze its event threshold against. A quarter of
the D2 candidates in the census are measured against a level that has not finished forming, and
SPDR-009's own design refuses exactly those events — so the census and the screen are looking at
different populations. That is cheap to fix (a `mins_since ≥ IB` filter and a `--from-w5` re-run), but
it must be fixed before the pins are handed over. The second thing to fix is that most of the hard
safety checks live in the battery rather than in the run that produced the artifacts, and the battery
was skipped for that run and covers 5 symbols instead of 194.

**Pins should not be frozen for SPDR-009 yet.** W1/W3/W4/coverage/gap artifacts are sound and would
survive the fix unchanged; only the two W5 census artifacts and `pins.json` need to be re-emitted.

---

## Run 7 — post-implementation QA (2026-07-21) — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time (`git status --porcelain`): `docs/.../015-signed-value-absorption-screen/design.md` (M);
`python/src/xen/sigbar/{baselines,fences,sessions}.py` (M); `python/src/xen/sigbar/ltf.py`,
`python/experiments/INFR-020/`, `python/experiments/SPDR-009/` untracked. Reviewed against
**design revision 5** (AMENDMENT-16/17/18) and the run-6 issue list.

**Verdict: REVISE** — 1 MAJOR, 4 MODERATE, 4 MINOR.
**FAILING_ARTIFACT:** `design.md` §1.1 (I7-1), `python/experiments/INFR-020/code/run_apparatus.py`
(I7-1, I7-3, I7-4, I7-5, I7-7), `python/src/xen/sigbar/ltf.py` (I7-3, I7-8),
`python/experiments/INFR-020/code/reproduction_battery.py` (I7-5).
**REQUIRED_SKILL:** `quant-designer` (I7-1 design claim, I7-2 population reconciliation with
SPDR-009 §3.2); `experiment-developer` (I7-1 code, I7-3…I7-9).

**Run-6 issues I-1 … I-9: ALL VERIFIED FIXED.** Everything below was re-measured in this session
from staging and from the artifacts; `FIXES-QA6.md` was used only as a map to check.

---

### 1. Verification of the run-6 fixes

| Run-6 issue | Verdict | Evidence measured here |
|---|---|---|
| **I-1** level availability + refusal | **FIXED** (D1–D3; see I7-1 for D4) | `ltf.py:571-586` stamps `available_mins_since` (IB edges = `ib_minutes`, prior-session = 0) and `:495-500` stamps `level_source_bar_minutes`. `run_apparatus.py:587-616`: `mins_since = OpenTime − anchor_ts`; pre-IB candidates use non-IB levels only; a pre-IB candidate whose nearest level **over the full set** is an IB edge is `continue`d, not re-pointed (`:600-603`) — matches SPDR-009 §7 "IB-edge events before IB complete are REFUSED" verbatim. **Independent re-derivation from raw 1m bars, RENUSDT D2** (my own anchor/IB/prior-level/refusal code, only `load_bars`/`residualise`/`build_profile` reused): **746 candidates / 174 pre-IB / 63 refused / 683 measured — exact match** to the emitted census. Universe D2 totals re-derived: **9,497 / 2,390 / 1,109 / 8,388**, and `1,109 + 8,388 = 9,497` reconciles exactly. D1 95,836 / 692 / 510 / 95,264; D3 2,974 / 191 / 111 / 2,862; D4 640 / 32 / 18 / 614 — all as claimed. |
| **I-2** asserts on the emitting path | **FIXED** | I instrumented the runner and executed a live 1-symbol pipeline (`--out-dir` scratch): call counts on the emitting path — `assert_design_only_fit` 6, `check_no_outcome_columns` 12, `assert_split_additive` 3, `assert_bar_causality` 3, `assert_no_forward_provenance` 9, `assert_windows_complete` 9, `assert_levels_from_1m` 4, `assert_no_per_level_delta` **250** (the real one, from `profile.py:107` with the actual weight column). Every assert **fires on planted input**: causality — SourceBars inflated ✓, `source_max_open` pushed past close ✓, grid shifted 1m ✓, wrong-period frame ✓, single future-source row ✓; split additivity ✓; `assert_windows_complete` on a genuinely mixed frame (SKLUSDT 60m: 140 COMPLETE / 5,351 partial) ✓ and on a frame missing `window_class` ✓; forward provenance ✓. **The vectorised `assert_bar_causality` detects everything the per-row version did** — it re-buckets the 1m series on the same clock grid and compares count + source bound, so a shifted grid surfaces as "no 1m source rows". `assert_levels_from_1m` now traces real provenance: it **raises** on an aggregated source series, on a level frame stamped 5m, on a missing provenance column, and on nothing-supplied; `structural_levels_1m` itself refuses an aggregated source (`ltf.py:549-554`). |
| **I-3** battery scope + pin | **FIXED** | `reproduction_battery.json`: `mode: full`, `all_ok: true`, **A1 over 194 symbols, 0 with metric errors**; **A2 `n_checked: 137` of `n_pinned_blocks: 137`**. Hash `b860832259f6…` in `pins.json` matches the file. Pin refusal verified **behaviourally**: with no battery on disk the run raised `"no reproduction_battery.json on disk — pins may not be handed to a consumer without the battery that covers them"` and wrote no pins (`run_apparatus.py:901-919`). |
| **I-4** unreachable gap class | **FIXED (design)** | §2 W2a + AMENDMENT-16 now state the class is provably empty for day-aligned windows over whole-day gaps and name `gap_excision_report.json` as the live disclosure. Re-measured: observed class set across 194×3 is `{COMPLETE, NO_TRADE_PARTIAL}`. |
| **I-5** unpinned D1 thresholds | **FIXED** | `class_thresholds_1m.json`: 194 symbols, 0 with a "no block" note, `n_registry_overlap: 137`. **Independent identity check on all 137 registry blocks: 0 mismatches** at 1e-9 relative (every key incl. `abs_high`, `n`, `high_pctl`, `applied_to`). **SPDR-009 can now rebuild D1 from pinned objects alone** — I rebuilt the D1 candidate population for two symbols absent from the 137 registry using only the frozen INFR-017 1m baseline + `class_thresholds_1m.json`: 1INCHUSDT **800 = 800**, AGLDUSDT **83 = 83**. |
| **I-6** prior-session identity | **FIXED** | `ltf.py:396-425` now builds the consumer→predecessor link from the **anchor table** (`a_list[1:]` ↔ `a_list[:-1]`), the same map `structural_levels_1m:605-607` uses; a predecessor that traded nothing yields a null range and is counted (`n_sessions_prior_missing`). **Re-ran run-6's SKLUSDT A-H1 comparison**: fast 5,491 anchors vs brute-force calendar-adjacent 5,485 — **0 value mismatches, 0 missing**; the 6 differences are precisely the null-range rows the fix retains on purpose. Run 6's *4 extra / 5 missing* is gone. |
| **I-7** vacuous battery members | **FIXED** | A2's identity check is now a discrimination test (`reproduction_battery.py:302-320`): the real estimator must match the pin within 1e-4 **and** a p89 lookalike must differ by more than 1e-4 — `estimator_discriminates_lookalike: true`. Not vacuous (it would fail if `derive_thresholds` drifted to any nearby quantile). A5b is now a numeric assert (`:419-454`): **65,952 joined BTCUSDT 5m windows, max abs diff 0.0 on Open/High/Low/Close**, and `ok` gates the battery. |
| **I-8** blocklist vocabulary | **FIXED, no false positives** | `fences.py:227-288`. Catches every programme outcome name I tested: `ret_bps`, `ret_norm`, `ret`, `trap_load`, `mfe_rev_norm`, `mae_rev_norm`, `bite`, `edge_bps`, `gross_bps`, `net_bps`, `pnl`, `fwd_return`, `asym`, `excursion_up`, `hold_return`, `ret_bps_h5`, `forward_ret`, `MFE_norm`. **No false positive on `retention`, `retention_floor_predeclared`, `n_retained`, `turnover`, `level_price`, `n_missing`, `mode`, `n_1m`, `prior_session_range`, `spread`** — the underscore-terminated prefixes do their job. Independently scanned **every emitted artifact**: 9 JSON files (17–258 distinct keys each) and the parquet's 9 columns — **0 hits**. |
| **I-9** silent drops / disclosures | **FIXED** (a new one found — I7-3) | (a) `session_ib_from_1m` flags `ib_degenerate` and W5 emits `n_sessions_ib_degenerate`; `n_sessions_prior_missing` emitted. (b) `null_scale_volume_cells` present at 5/15/60m and a new `one_minute` block per instrument (`in_frozen_pin`, null-scale volume/range cells, sparse rate) — verified in `coverage_report.json`. (c) Ledger reconciliation now in `gap_excision_report.json`: `ledger_unresolved_error_days`, `ledger_miss`, `ledger_only` — **BNXUSDT and GSTUSDT named as ledger misses, 31 ledger-only**, 8 instruments with in-band gap days. (d) `measurable: false` on every skip path; the one unmeasurable cell is BUSDUSDT D1 with `threshold_keys: [volume, delta_abs, delta_ratio]`. (e) `assert_windows_complete` has one implementation (`fences.py:344-357` delegates to `ltf`). (f) dead `inv` gone. |

### 2. Design-fidelity trace T1–T20 against **revision 5**

| # | Clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|---|
| T1 | §3 outcome ban, two layers | `fences.py:227-307` (schema), `:310-341` (provenance); `run_apparatus.py:142, 146, 177, 464, 746-752` | **MATCHES** | Both layers now on the emitting path; `emit_json` key-checks at write. Residual: 2 of 10 artifacts not routed through `emit_json` → I7-7. |
| T2 | §3 `assert_bar_causality` | `ltf.py:197-247`; called `run_apparatus.py:145` | **MATCHES** | Full frame, vectorised, every planted defect caught. |
| T3 | §2 W1 generalisation on `bar_minutes` | `baselines.py` (generalised sites) | **MATCHES** | Grids exact: 5m 2016 / 15m 672 / 60m 168 cells; parquet **194 symbols, 2,216,256 rows, `bar_minutes ∈ {5,15,60}`** — no competing 1m partition (`run_apparatus.py:849-850` raises if one appears). 582/582 (symbol × tf) blocks present. |
| T4 | §3 DESIGN-only fence | `fences.py:431-453`; called `:124, 179, 246, 388` | **MATCHES** | `BANDS` = `{DESIGN, CONFIRM}` only; `load_bars(..., "TEST"/"HOLDOUT"/"OOS")` raises `unknown band`. **TEST/holdout unreachable by construction.** No data date ≥ 2023-03-01 in any artifact (only the 2026-07-21 run stamps). |
| T5 | §4 A1 value-identity over 194 | `reproduction_battery.py:186-256` | **MATCHES** | 194/194, 0 metric errors, `grid_ok`, `via_generalised_path`. |
| T6 | §4 A2 137 blocks + estimator identity | `reproduction_battery.py:259-330` | **MATCHES** | 137/137 traversed, lookalike discrimination real. |
| T7 | §4 A3 frozen session object | `reproduction_battery.py:333-370` | **MATCHES** | Golden IB 20833.0 / 21020.5 / 187.5 reproduced. |
| T8 | §4 A4/A5/A5b | `ltf.py:250-262, 700-768`; battery `:373-462` | **MATCHES** | A5b promoted to a measured assert; max diff 0.0 over 65,952 windows. |
| T9 | §1.1/§1.2 W5 levels: 1m provenance, availability, refusal | `ltf.py:513-697`; `run_apparatus.py:544-616` | **DEVIATES (D4 only)** | 1m provenance now traced, not echoed. Availability/refusal correct and independently reproduced at D2. **D4's IB boundary is not on the LTF grid** → I7-1. |
| T10 | §7 accounting fence / no BacktestNode / `classes.py`+`bar_aggregator.py` untouched | `run_apparatus.py:896-898` | **MATCHES** | `check_no_local_accounting` re-run by me on `code/` **and** the whole experiment dir: `{'ok': True, 'banned_defs_found': []}`. `git status` shows no change to `classes.py` or `bar_aggregator.py`. No Nautilus anywhere. |
| T11 | §7 pins: every artifact hashed | `run_apparatus.py:785-922` | **MATCHES** | **All 9 non-pins artifacts hashed and every hash re-computed by me matches the file on disk.** Frozen inputs re-verified: `1b7244c8…` / `e3b9fd9b…` / `35d3375e…` = the design's declared pins; INFR-017 baseline hash unchanged. |
| T12 | no reconstruction path | — | **N/A (moot)** | Re-read `ltf.py` end to end: no fill, no upsample, no synthetic minute index. The D1 stamp (`run_apparatus.py:432-436`) marks **real** 1m bars as COMPLETE/1.0/1 — definitionally true. |
| T13 | `assert_no_collection_gaps` | — | **N/A (superseded)** | See T18. |
| T14 | A6 as reported statistic | `run_apparatus.py:685-705` | **MATCHES** | Reported, not gating, as AMENDMENT-8 requires. |
| T15 | `traded_fraction` everywhere | `ltf.py:176-189`; census `min_traded_fraction` | **MATCHES** | 0 census rows with a value other than 1.0 or null. |
| T16 | shared predicate, one definition | `ltf.py:297-342` | **MATCHES (design-level)** | One definition; SPDR-009 §7/§9 commits to importing it. Untestable until SPDR-009 has code. |
| T17 | null-scale cells per (symbol, tf, metric) | `run_apparatus.py:689-726` | **MATCHES** | Volume **and** range at 5/15/60m, plus the `one_minute` block off the frozen pin. |
| T18 | gap days from staging + ledger reconciliation | `ltf.py:36-69`; `run_apparatus.py:121-138` | **MATCHES** | 8 in-band instruments; BNX/GST named as ledger misses; 31 ledger-only. |
| T19 | COMPLETE-only fit and event population | `ltf.py:327-342`; `run_apparatus.py:176, 204, 463` | **MATCHES** | `assert_windows_complete` on W1/W3/W5 COMPLETE frames, verified reached. |
| T20 | coverage: 194-symbol retention + vol ratio | `run_apparatus.py:664-733` | **MATCHES** | Re-derived: median retention **0.3851 / 0.2011 / 0.0882**; ≥0.90 **20 / 11 / 6**; ≥0.50 **72 / 47 / 31**; <0.20 **28 / 95 / 132**; 60m vol ratio n=193, median **6.74×**, range **0.32×–187.02×**. Every design §5 figure reproduces. |

### 3. Regression sweep (the fixes touched shared modules)

| Check | Result |
|---|---|
| SPDR-008 consumer vs frozen golden traces | **PASS** — `_smoke_trap.py`: all four trap traces reproduce, `SMOKE OK — assert_ib_matches_frozen passed for both IB symbols`. |
| Frozen 1m baseline untouched | **PASS** — `sha256 = 1b7244c87aaa…`, identical to the pin; `INFR-017/` and `INFR-018/` clean in `git status`. |
| Shared-module diffs are additions | `sessions.py` and `fences.py` are **pure additions** (0 removed lines). `baselines.py` is the generalisation; **the 194-symbol A1 value-identity is its regression test and passes with 0 errors**. `classes.py` / `bar_aggregator.py` untouched. |
| Zero-fill / reconstruction | **ABSENT** — no fill primitive on any path. |
| COMPLETE-only fitting reconciles | **PASS** — 582/582 (symbol × tf) baseline blocks; thresholds 194 × 3 with 0 missing. |
| Coverage reproduces the universe table | **PASS** (T20). |
| Outcome columns / out-of-band dates | **NONE** in any artifact (9 JSON + parquet). |
| `check_no_local_accounting` | **PASS** on `code/` and on the experiment dir. |
| TEST / holdout | **UNREACHABLE** — `BANDS` has no such key. |
| Counted reads | **0**, as §0 declares. |

### 4. Contamination audit (the 5-symbol overwrite)

**The artifacts on disk are all from the clean full rebuild.** Evidence:

* All 9 artifact hashes in `pins.json` **recomputed by me and matching byte-for-byte**.
* **194 everywhere**: census `pairs` 194 · `zone_scale_census_d1_ibwidth` 194 · `class_thresholds_mtf` 194 · `class_thresholds_1m` 194 · `gap_excision_report` 194 · `coverage_report` 194 · `sessions_mtf.symbols_framed` 194 · baselines parquet 194 symbols × 3 timeframes · battery `n_symbols` 194.
* Write order is a single clean sequence: `gap_excision` 19:31 → parquet 19:33 → `thresholds_mtf`/`sessions` 19:35 → `thresholds_1m` 19:36 → both census artifacts 19:41 → `coverage` + `pins` 19:43 (UTC). No file predates the rebuild except `reproduction_battery.json` (19:19), which reads **staging and the INFR-017/018 pins only — never `results/`** — so the contaminated `results/` state could not have influenced it, and it postdates every shared module it exercises (`ltf.py`/`fences.py` 19:11).
* **No 5-symbol residue anywhere**: the only other JSON in the tree is `design_derivations/` (16:24–17:19 UTC, design-stage diagnostics, not pinned).
* Two caveats, carried as issues: `pins.json.generated_utc` is stamped at run **start** (19:28:54), which reads as if it predates the artifacts it hashes — cosmetic, hashes govern; and the `--out-dir` guard is incomplete → **I7-5**.

### 5. Issues

**I7-1. [MAJOR] The D4 IB nesting claim in §1.1 is false, and every D4 pre-IB classification is therefore wrong.**
`design.md:64-65` states *"Every pair's LTF bar nests exactly into its IB boundary (D1 15×1m, D2 3×5m, D3 1×15m, D4 1×60m), so `OpenTime − anchor ≥ ib_minutes` and 'IB complete at bar close' are the same test."* Measured: **A-USOPEN sits at minute-of-day 810 (13:30 UTC), i.e. on the half hour** (`sessions.py:68`, `OCCUPIED_MINUTES` `:120` = `(810, 870)`), while D4's LTF bars are clock-aligned 60-minute bars opening on the hour. D4's IB therefore runs `anchor → anchor+60` = **13:30→14:30, which is not a 60m bar boundary**. D1 (1m), D2 (A-H1, hour-aligned) and D3 (A-H4, 4-hour-aligned) do nest; **D4 does not.**
Consequences, measured on the emitted population:
(a) The only `mins_since` value below 60 at D4 is **30** — verified on BNXUSDT and by construction for every symbol. So all **32** D4 "pre-IB" candidates are the 14:00–15:00 bar, which **closes at anchor+90, a full 30 minutes after the IB completes at anchor+60**. The IB edges *are* knowable at their close. All **18** D4 refusals are false refusals, and the other 14 are measured against a truncated (prior-session-only) level set.
(b) A 60m bar opening at anchor−30 (13:00–14:00) straddles the session boundary and is assigned wholly to the **previous** session by the backward asof-join (`run_apparatus.py:527-541`), so its close falls in a session whose levels it never sees.
There is **no forward leak** — the error is conservative — but the census population at D4 is strictly *smaller* than SPDR-009's, which is the same object-identity failure run 6 blocked on, mirrored.
*Required:* (i) correct `design.md` §1.1 to state that D1/D2/D3 nest and **D4 does not**, because A-USOPEN is a :30 anchor; (ii) in W5, decide D4 availability on the **bar close** (`OpenTime + ltf_minutes > anchor + ib_minutes`) rather than `OpenTime`, or explicitly declare and count the straddling bar as a separate class; (iii) reconcile the session assignment of the boundary-straddling 60m bar with SPDR-009 §3.1; (iv) re-emit both census artifacts and re-pin (W1–W4 unaffected).

**I7-2. [MODERATE] The refusal removes the whole candidate, but SPDR-009's events are per (bar, level kind) — the two populations still differ.**
`run_apparatus.py:600-603` drops a pre-IB candidate outright when its nearest level over the full set is an unformed IB edge. That matches SPDR-009 §7's fence read literally, and matches `design.md:60-62`. But SPDR-009 §3.2 declares **"One event per (pair, LTF bar, level kind); nearest-level once for pooled"** — so in the screen the same bar can still be an event at `PRIOR_POC`/`PRIOR_VAH`/… if it is inside τ of one, while the census contributes nothing for it. At D2 that is **1,109 of 9,497 candidates (11.7%)** absent from the distance distribution τ is frozen against, and the removed rows are systematically the *short-distance* ones (run 6 measured p90 0.105 vs 0.282), so τ is frozen on a distribution shifted wide.
*Required:* either (a) also emit, per (symbol, pair), the distance-to-nearest-**non-IB** level for the refused candidates as a second count-only distribution, so SPDR-009 can freeze τ on whichever population its §3.2 granularity actually produces; or (b) add one line to SPDR-009 §3.2 stating that a bar refused at an unformed IB edge is refused **entirely**, not re-pointed — and carry that into its own QA. This is a design reconciliation, not an arithmetic bug.

**I7-3. [MODERATE] New silent candidate drops: `n_candidates ≠ n_refused + n_measured` on 27 cells.**
The counters imply a reconciliation that does not hold. Measured across the census: **D1 24 symbols / 62 candidates lost; D3 1 symbol / 1 candidate; D4 2 symbols / 8 candidates** (BNXUSDT D4 loses 7 of 16 — **44% of that cell**). D2 reconciles exactly. Cause: `ltf.py:558-562` and `:568-569` — when a session's IB is degenerate the level builder returns an **empty frame for that session, discarding the prior-session levels too**; `run_apparatus.py:591-592` then `continue`s on `if not entries` with no counter. ACHUSDT D3 is the clean illustration: 1 candidate, `n_level_rows: 0`, `n_sessions_ib_degenerate: 45`.
*Required:* emit `n_candidates_no_levels` per (symbol, pair) so `n_candidates == n_refused + n_measured + n_no_levels` holds identically, and stop letting a degenerate IB suppress the prior-session levels — those are knowable at the open and independent of the IB.

**I7-4. [MODERATE] W5 silently refits a run-local baseline when the pinned MTF baseline lacks a (symbol, timeframe) block.**
`run_apparatus.py:479-482`: `if bl_sym.height == 0:` → `fit_seasonal_baseline(...)` inline, then residualise against it. **This is the exact mechanism that let the contaminated 5-symbol run emit a plausible 194-symbol census** rather than failing loudly: missing baselines do not raise, they get replaced. It also defeats I-5's guarantee — a census cell built this way is not reproducible from any pinned object. Not triggered in this run (582/582 blocks present, verified), but the vector is live.
*Required:* raise, or mark the cell `measurable: false` with a named reason. A run-local baseline must never silently substitute for a pinned one. (The threshold path already does the right thing at `:465-474`.)

**I7-5. [MODERATE] The `--out-dir` guard does not cover the battery, and `--from-w5` still does not check that the on-disk W1/W3 covers the run's universe.**
(a) `reproduction_battery.py:64` hard-codes `RESULTS = parents[1]/"results"` and `run_battery` writes there (`:611-612`) regardless of the runner's `--out-dir`. A sample run **with** the battery therefore still overwrites the pinned `results/reproduction_battery.json`, and then `run_apparatus.py:803-805` hashes `<out-dir>/reproduction_battery.json`, which does not exist — it clobbers the pin and crashes. (b) `run_apparatus.py:826-834` loads `seasonal_baselines_mtf.parquet` / `class_thresholds_mtf.json` from disk and only hashes them; nothing asserts their symbol set covers `symbols`. Combined with I7-4 this is the full contamination path, still open.
*Required:* thread `--out-dir` into `run_battery(out_dir=…)`; and in the `--from-w5` branch assert `set(bl["symbol"]) ⊇ set(symbols)` and the same for the thresholds dict, raising by name on any shortfall.

**I7-6. [MINOR] VT-4(g) is still neither implemented nor demoted.**
`design.md:484` keeps *"(g) A-H1/A-H4 consumed as an edge-bearing anchor"* under **"Must RAISE, not warn"**. Grep across `xen/` and `code/`: the only artefact is the data field `edge_bearing: False` in `sessions_mtf.json` (`run_apparatus.py:288`) — a declaration, not a fence. Run 6's I-2(f) asked for one or the other; neither happened.
*Required:* demote it in §6 to "declared, not enforced (no consumer exists in this item; enforced in SPDR-009 GT-5(k))", or add the check.

**I7-7. [MINOR] `emit_json` covers 8 of 10 emitted artifacts.**
`pins.json` (`run_apparatus.py:921-922`) and `reproduction_battery.json` (`reproduction_battery.py:611-612`) are written with a bare `write_text`, bypassing the key check. I scanned both by hand — clean (20 and 258 keys, 0 hits) — so this is a completeness gap, not a live defect.
*Required:* route both through `emit_json`.

**I7-8. [MINOR] `ltf.py:555` `assert_no_per_level_delta("Volume")` is a literal echo.**
Same shape as the defect run 6 raised against `assert_levels_from_1m`: the argument is a constant, so the call can never fail. The clause **is** genuinely discharged — `profile.py:107` calls it with the real weight column and I measured **250 invocations per symbol** on the live path — so this line adds nothing but re-creates the pattern the programme just removed.
*Required:* delete it, or pass the actual weight column name used by `build_profile`.

**I7-9. [MINOR] Two cosmetic provenance wrinkles in `pins.json`.**
`generated_utc` (19:28:54Z) is stamped at run start, before the artifacts it hashes were written (19:31–19:43Z), so the pin file reads as if it predates its own contents; and `battery.generated_utc` (19:19:15Z) predates the shipped `run_apparatus.py` (19:28:42Z) — harmless, because the battery exercises `ltf`/`fences`/`baselines`/`sessions` (all older) and not the runner, but a reader cannot tell that from the file.
*Required:* stamp `generated_utc` at write time and record the battery's covered module hashes, or state the scope in the pin.

### 6. Note to the operator

The nine things run 6 asked for were all done, and I checked each by measuring rather than reading:
the pre-IB refusal rule now reproduces exactly when I rebuild it from raw bars on my own code, the
hard safety checks all run inside the run that produced the artifacts and all fire on broken input,
the battery really covers 194 and 137, the 1-minute thresholds let SPDR-009 rebuild the D1 population
from pinned files alone, and the prior-session mismatch is gone. The contamination is cleanly gone
too — every artifact on disk is from the one clean rebuild, 194 everywhere, hashes matching.

Three things still block the handoff. First, one of the four pairs (D4) has its session clock on the
half hour while its bars are on the hour, so the "has the opening range finished forming yet?" test
is asked at the wrong moment — every D4 candidate it flags is actually fine, and 18 events were
thrown away that should have been kept. The design states the opposite as a fact. Second, the census
throws away a candidate entirely when the nearest level is one that has not formed yet, while the
screen would still count that same bar against a different, older level — so the two are still
counting different things, now in the opposite direction from run 6. Third, if a symbol is missing
from the pinned baselines the census quietly fits a fresh one instead of stopping, which is exactly
how the contaminated run went unnoticed for as long as it did.

**Apparatus pins may NOT be frozen and handed to SPDR-009 yet.** W1 (baselines), W3/W3b (thresholds),
W4 (sessions), coverage and the gap report are sound and survive the fixes unchanged. Only the two
W5 census artifacts and `pins.json` need re-emitting, and only D4 changes materially.

---

## Run 8 — post-implementation QA (2026-07-21) — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review time (`git status --porcelain`): `docs/.../015-signed-value-absorption-screen/design.md` (M);
`python/src/xen/sigbar/{baselines,fences,sessions}.py` (M); `python/src/xen/sigbar/ltf.py`,
`python/experiments/INFR-020/`, `python/experiments/SPDR-009/` untracked. Reviewed against
**design revision 5 + AMENDMENT-19/20** and the run-7 issue list.

**Verdict: REVISE** — 2 MAJOR, 2 MODERATE, 5 MINOR.
**FAILING_ARTIFACT:** `python/src/xen/sigbar/ltf.py` (I8-1, I8-2), `python/experiments/INFR-020/code/run_apparatus.py`
(I8-1, I8-2, I8-4, I8-5, I8-6), `design.md` §1.1/§8 (I8-1, I8-3, I8-8, I8-9),
`python/experiments/SPDR-009/design.md` §3.1 (I8-7).
**REQUIRED_SKILL:** `quant-designer` (I8-1 rule choice + §1.1 text, I8-3, I8-7, I8-8, I8-9);
`experiment-developer` (I8-1 code, I8-2, I8-4, I8-5, I8-6).

**Run-7 issues I7-1 … I7-9: ALL VERIFIED FIXED.** Everything below was re-measured in this session
from staging and from the artifacts; `FIXES-QA6.md`, the design prose and runs 6–7 were used only
as the specification to trace against.

**Operator decision held as binding and NOT re-litigated:** a candidate whose nearest level would be
an unformed IB edge is KEPT and measured against the levels that exist; only the unformed edge is
removed from that bar's level set. **The implementation matches the decision and it does not
contradict SPDR-009's text** — SPDR-009 §2 / §7 / GT-5(e) refuse an *IB-edge EVENT* before the IB
completes, and §3.2 makes an event a (pair, LTF bar, level kind) triple, so refusing the (bar,
IB-edge) event while keeping the bar at older levels is exactly what the screen does. **No forward
price is consulted** (verified below).

---

### 1. Verification of the run-7 fixes

| Run-7 issue | Verdict | Evidence measured here |
|---|---|---|
| **I7-1** availability decided at the CLOSE; D4 handled | **FIXED** | `run_apparatus.py:544-565` joins candidates to anchors on `last_source_minute = OpenTime + ltf − 1m` (session = the one holding the bar's last source minute) and derives `mins_since_close = close_time − anchor_ts`; `:619` `pre_ib = mins_since_close < ib_mins`. **Independent rebuild from raw 1m bars with my own aggregation / session-assignment / IB / prior-level / availability code** (reusing only `load_bars`, `residualise`, `anchor_table`, `build_profile`): **RENUSDT D4 61 / 1 pre-IB / 1 ib-edge-unavailable / 0 no-levels / 1 straddling / 61 measured — exact match** to the emitted census; **RENUSDT D2 746 / 113 / 38 / 0 / 0 / 746 — exact match**; **BNXUSDT D4 16 / 1 / 1 / 6 / 1 / 10 — exact match**. D4's :30 anchor is handled correctly: with A-USOPEN at 13:30 the 13:00–14:00 bar has `last_source_minute` 13:59 → assigned to the 13:30 session it **ends in**, `mins_since_close` 30 < 60 → pre-IB; the 14:00–15:00 bar is 90 ≥ 60 → post-IB and keeps its IB edges. `n_candidates_straddling_anchor` = **43 universe-wide, all at D4**, and D4 `n_candidates_pre_ib` = **43** — structurally identical because exactly one bar per D4 session straddles and exactly that bar is pre-IB. **D3 191 → 0 is legitimate**: `ib_minutes_for_ltf(15) = 15`, so the session's first 15m bar closes at `anchor+15` = the instant the IB completes, `15 < 15` is false. **D1 692 → 642, D2 2,390 → 1,579** — both match the one-bar shift the close rule implies (D1 14 of 15 minutes, D2 2 of 3 bars). **No level price is consulted before it exists**: prior-session levels come from the session that closed at the anchor (`ltf.py:594-611`, `< session_end`); IB edges carry `available_mins_since = ib_minutes` (`:583, :589`) and are filtered out whenever `mins_since_close < ib_mins`. For the straddling D4 bar the prior-session extremes are built from minutes ≤ 13:29, strictly before its 14:00 close. |
| **I7-2** keep-the-bar rule | **FIXED** | `run_apparatus.py:619-635`: a pre-IB bar increments `n_pre_ib`, records `n_ib_edge_unavailable` when its nearest level over the **full** set would have been an IB edge, then measures against `usable = [p for p, is_ib in entries if not is_ib]`. D2: **9,497 candidates, 9,497 measured, 0 dropped**; 1,579 pre-IB, of which 665 would have had an unformed IB edge as nearest. Reproduced exactly on RENUSDT D2 (113 / 38). Pre-IB bars are measured against non-IB levels only — confirmed by construction and by the independent rebuild. |
| **I7-3** count identity + degenerate IB | **FIXED** | Identity `n_candidates == n_measured + n_no_levels + n_unanchored` holds on **all 776 measurable cells, 0 violations** (independently recomputed from `zone_scale_census.json`) — but it holds *by construction*, see I8-4. `ltf.py:561-565` now filters only the degenerate IB rows and leaves the prior-session branch untouched, so a degenerate IB no longer suppresses prior-session levels. **The remaining `n_candidates_no_levels` are genuinely level-less sessions**: I re-derived the split for all 24 D1 symbols that carry one — **62 truly level-less, 0 caused by an unformed IB edge** — and BNXUSDT D4's 6 are likewise all truly level-less (BNXUSDT has 11 in-band gap days). |
| **I7-4** missing pinned baseline | **FIXED, path triggered** | `run_apparatus.py:479-492`. I ran W5 for RENUSDT with the 60m baseline block deleted: the D4 cell came back `measurable: false`, `n_candidates: 0`, `note: "no pinned 60m baseline block for symbol (no run-local refit)"`, while D2 stayed measurable at 746. No refit occurs. |
| **I7-5** `--out-dir` + `--from-w5` coverage | **FIXED, both paths triggered** | (a) `reproduction_battery.run_battery(out_dir=…)` (`:580-585, :614`), passed by `run_apparatus.py:835`. I ran the battery with `--out-dir <scratch>`: it wrote `<scratch>/reproduction_battery.json` and `results/reproduction_battery.json` was **byte-unchanged** (md5 identical before/after). (b) `run_apparatus.py:868-880`. I ran `--from-w5 --skip-battery --out-dir <scratch>` against a deliberately 2-symbol W1/W3: it raised `"--from-w5: on-disk seasonal_baselines_mtf covers 2 symbols and is missing 3 of this run's universe (first: ['CRVUSDT','LTCUSDT','SOLUSDT'])"` and wrote nothing. |
| **I7-6** VT-4(g) | **FIXED (design)** | `design.md:495-498` now reads *"(g) DEMOTED to declared, not enforced (AMENDMENT-20) … enforceable version lives in SPDR-009 GT-5(k)"*. SPDR-009 §7 and GT-5(k) do carry the enforceable clause. `sessions_mtf.json` carries `edge_bearing: false` as data. |
| **I7-7** `emit_json` coverage | **FIXED** | `pins.json` now goes through `emit_json` (`run_apparatus.py:983`) and the battery key-checks its own report before writing (`reproduction_battery.py:616-629`). I independently key-scanned all 9 JSON artifacts + the parquet with `check_no_outcome_columns`: **0 hits** (17–258 keys each). |
| **I7-8** literal `assert_no_per_level_delta("Volume")` | **FIXED** | The call is gone from `ltf.py`; `:548-552` is now a comment pointing at the real site. **The real enforcement fires**: `build_profile(..., weight_col="Delta_x")` raises `PER-LEVEL DELTA BARRED`, and the clean `Volume` path builds a 200-bin profile. (Residual: an orphan import — I8-5.) |
| **I7-9** pin provenance | **FIXED** | `run_apparatus.py:970-981` stamps `generated_utc` at write time and records `battery.covers_modules` + `covers_runner: false`. On disk: pins `2026-07-21T20:16:39Z` **after** every artifact it hashes; battery `20:07:49Z` (21:07 local) **after** `ltf.py` 21:03, `run_apparatus.py` 21:04 and `reproduction_battery.py` 21:04 — so the battery covers the shipped code. |

---

### 2. Design-fidelity trace T1–T20 against **revision 5 + AMENDMENT-19/20**

| # | Clause (§ref) | Code (file:line) | Verdict | Evidence measured here |
|---|---|---|---|---|
| T1 | §3 outcome ban, two layers | `fences.py:227-307` / `:310-341`; `run_apparatus.py:142,146,177,464,786` | **MATCHES** | All 10 artifacts key-checked at write; my own scan of 9 JSON + parquet = 0 hits. Planted `fwd_return` raises. |
| T2 | §3 `assert_bar_causality` | `ltf.py:197-247`; called `:145` | **MATCHES** | Planted `SourceBars+1` raises (`BAR CAUSALITY … 6 but 5 1m bars`). Runs on the emitting path for every (symbol, tf). |
| T3 | §2 W1 generalisation on `bar_minutes` | `baselines.py:53-130` | **MATCHES** | Grid cells 5m 2016 / 15m 672 / 60m 168; parquet 194 symbols × {5,15,60}, 2,216,256 rows, no 1m partition. `assert_seasonal_keys_valid(bar_minutes=5)` raises on slot 300 (`expected [0, 287]`). |
| T4 | §3 DESIGN-only fence | `fences.py:431-453` | **MATCHES** | `BANDS = {DESIGN, CONFIRM}`; `load_bars(…, "TEST"/"HOLDOUT"/"OOS")` raises `unknown band`. No date ≥ 2023-03-01 in any artifact (gap report max 2023-02-27). |
| T5 | §4 A1 value-identity over 194 | `reproduction_battery.py:186-256` | **MATCHES** | `reproduction_battery.json`: 194 symbols, **0 failing**, `grid_ok`, `via_generalised_path`. |
| T6 | §4 A2 137 blocks + estimator identity | `:259-330` | **MATCHES** | `n_checked 137 / n_pinned_blocks 137`, `estimator_discriminates_lookalike: true`. |
| T7 | §4 A3 frozen session object | `:333-370` | **MATCHES** | Golden IB 20833.0 / 21020.5 / 187.5 reproduced. |
| T8 | §4 A4/A5/A5b | `ltf.py:250-262, 704-773`; battery `:373-462` | **MATCHES** | A5b numeric, max abs diff 0.0. |
| T9 | §1.1/§1.2 W5 levels: 1m provenance, availability at CLOSE, keep-the-bar | `ltf.py:515-701`; `run_apparatus.py:544-645` | **DEVIATES** | Availability/session rule correct and independently reproduced at D2 and D4 (see §1). 1m provenance traced, not echoed. **Deviation: nothing prevents a bar being measured against a level its own source minutes established → I8-1; and the rule itself is not in shared code → I8-2.** |
| T10 | §7 accounting fence / no BacktestNode / `classes.py`+`bar_aggregator.py` untouched | `run_apparatus.py:945-947` | **MATCHES** | `check_no_local_accounting` re-run by me on `code/` and on the experiment dir: `{'ok': True, 'banned_defs_found': []}`. `git status` clean for `classes.py`/`bar_aggregator.py`. No Nautilus. |
| T11 | §7 pins: every artifact hashed | `run_apparatus.py:820-983` | **MATCHES** | **All 9 artifact hashes recomputed by me and matching byte-for-byte.** Frozen inputs re-verified: `1b7244c8…` / `e3b9fd9b…` / `35d3375e…`. |
| T12 | no reconstruction path | — | **MATCHES** | No fill / upsample / synthetic index anywhere in `ltf.py`. |
| T13 | `assert_no_collection_gaps` | — | **N/A (superseded by T18)** | |
| T14 | A6 as reported statistic | `run_apparatus.py:685-705` | **MATCHES** | Reported, not gating. |
| T15 | `traded_fraction` everywhere | `ltf.py:176-189`, `:327-342` | **MATCHES** | Planted `traded_fraction 0.5` on a COMPLETE row raises VT-4(j). |
| T16 | shared predicate, one definition | `ltf.py:297-342` | **MATCHES (predicate only)** | One definition of `absorb_candidate_predicate`; SPDR-009 §9 commits to importing it. **The availability rule around it is NOT shared → I8-2.** |
| T17 | null-scale cells per (symbol, tf, metric) | `run_apparatus.py:689-762` | **MATCHES** | Volume + range at 5/15/60m plus the `one_minute` block. |
| T18 | gap days from staging + ledger reconciliation | `ltf.py:36-69`; `run_apparatus.py:121-138` | **MATCHES** | 8 in-band instruments; BNX/GST named as ledger misses; 31 ledger-only. |
| T19 | COMPLETE-only fit and event population | `ltf.py:265-287`; `run_apparatus.py:176, 204, 463` | **MATCHES** | `assert_windows_complete` raises on a genuinely mixed frame (SKLUSDT 60m: 140 COMPLETE / 5,351 partial) and on a frame missing `window_class`. |
| T20 | coverage: 194-symbol retention + vol ratio | `run_apparatus.py:700-769` | **MATCHES** | Re-derived from `coverage_report.json`: median retention **0.3851 / 0.2011 / 0.0882**; ≥0.90 **20 / 11 / 6**; ≥0.50 **72 / 47 / 31**; <0.20 **28 / 95 / 132**. Every design §5 figure reproduces. |

**VT-4 planted-failure sweep (all executed by me):** (a) design-only fence raises; (b) TEST/holdout
unreachable (`unknown band`); (c) causality raises on inflated `SourceBars`; (d) slot key out of
range raises with the generalised bound; (e) outcome name raises, provenance raises; (f) per-level Δ
raises from the real call site; (g) demoted, declared as data; (h) non-COMPLETE frame raises;
(i) aggregated source series raises; (j) `traded_fraction < 1.0` raises.

---

### 3. Regression sweep

| Check | Result |
|---|---|
| SPDR-008 golden traces | **PASS** — `SPDR-008/screen_code/_smoke_trap.py` re-run: all four traces (IB BTC/SOL, PVA, PRIOR) reproduce their frozen values; `SMOKE OK — assert_ib_matches_frozen passed for both IB symbols`. |
| Frozen 1m baseline untouched | **PASS** — sha256 `1b7244c87aaa…` = the pin. |
| Zero-fill / reconstruction | **ABSENT** on every path. |
| COMPLETE-only fitting | **PASS** — 582/582 (symbol × tf) baseline blocks, thresholds 194 × 3. |
| Coverage | **PASS** — 0.3851 / 0.2011 / 0.0882 and 72 / 47 / 31 reproduce exactly. |
| Battery full, passing, covering CURRENT code | **PASS** — `mode: full`, `all_ok: true`, A1 194/194 with 0 failures, A2 137/137; battery written 21:07 local, after `ltf.py` 21:03 / `run_apparatus.py` 21:04 / `reproduction_battery.py` 21:04. |
| On-disk W1/W3 reproduce under current code | **PASS (spot check)** — the pinned run used `--from-w5`, so W1/W3/W4 are from 20:33–20:35 while `ltf.py` is 21:03. I re-ran `w1_baselines` + `w3_thresholds` for BTCUSDT and CRVUSDT under the shipped code: parquet blocks **bit-identical** (11,424 rows each) and threshold dicts **identical**. 2 of 194 checked → I8-6. |
| Outcome column / out-of-band date | **NONE** — 9 JSON (17–258 keys) + parquet (9 cols); gap-report dates span 2021-10-26 … 2023-02-27. |
| `check_no_local_accounting` | **PASS** on `code/` and on the experiment dir. |
| TEST / holdout | **UNREACHABLE** by construction. |
| Counted reads | **0**, as §0 declares. |
| All 9 artifact hashes vs `pins.json` | **MATCH**, recomputed here. |

---

### 4. Issues

**I8-1. [MAJOR] A candidate can be measured against a level its own source minutes established, and the affected distances are systematically short.**
AMENDMENT-19 moved the availability test to the bar's close. That correctly stops D4 discarding valid
events, but it also admits the *boundary* bar at every pair into the population that is measured
against the IB edges — and at three of the four pairs the boundary bar is itself inside the IB window:

* **D3** (`_PAIR_SPEC` `ltf=15`, `ib_mins=15`): the session's first 15m bar **is** the entire IB
  window, so `IB_HIGH`/`IB_LOW` are that bar's own High/Low. `|Close − level|` is then a pure
  function of the bar, bounded by its own range — and the predicate selects *low-range* bars.
  This is precisely the population whose pre-IB count went 191 → 0.
* **D2** (`ltf=5`, `ib_mins=15`): the third 5m bar contributes 5 of the IB's 15 minutes.
* **D4** (`ltf=60`, `ib_mins=60`): the 14:00–15:00 bar contributes 30 of the IB's 60 minutes; and the
  straddling 13:00–14:00 bar's own minutes lie inside the **prior** session whose extremes it may set.

Measured on the top-20 symbols by candidate count per pair (my own recomputation, real level code):

| pair | measured | nearest level self-set | share | p50 dist / prior range (self-set vs clean) | p90 (self-set vs clean) |
|---|---|---|---|---|---|
| D2 | 6,045 | 286 | **4.7%** | 0.0417 vs 0.0741 | **0.167 vs 0.435** |
| D3 | 2,275 | 79 | **3.5%** | 0.0345 vs 0.0714 | **0.083 vs 0.656** |
| D4 | 554 | 47 (16 IB + 31 prior) | **8.5%** | 0.047 / 0.048 vs 0.081 | **0.115 / 0.135 vs 1.09** |

There is **no lookahead** — every price used is ≤ the bar's close. The defect is that W5's whole
purpose is to let SPDR-009 freeze τ on the *right* distance distribution, and these rows pull it
toward zero. It is the same object-identity failure shape run 6 blocked on, and it is the exact
hazard INFR-018 already codified: `sessions.py:346-350` keeps `ib_high_ts`/`ib_low_ts` so that
*"a class event that is itself the bar which set an edge would otherwise score zero distance from
it"*. §1.1 says nothing about it, so it is currently neither refused nor disclosed.
*Required:* (i) decide the rule in `design.md` §1.1 — either **exclude** a level from a bar's set
when the bar's own source minutes fall inside the window that established that level (INFR-018's
rule, extended to the straddling case), **or** keep them and publish `n_candidates_self_set_level`
plus a second count-only distance distribution with them removed, so τ can be frozen either way;
(ii) implement it in `run_apparatus.py:612-645` / `ltf.py:576-701`; (iii) reconcile the choice with
SPDR-009 §3.1/§3.2 in one line; (iv) re-emit both census artifacts and re-pin (W1–W4 unaffected).

**I8-2. [MAJOR] The level-availability rule has no shared implementation, so SPDR-009 must retype it.**
`design.md` §1.1 requires *"W5's level set == SPDR-009's level set: MUST BE"* and, for candidates,
solves that by exporting one function (`absorb_candidate_predicate`) *"which SPDR-009 imports rather
than reimplements"*. The availability rule has no such function: session-assignment-at-close,
`close_time`, `last_source_minute`, `mins_since_close`, `straddles_anchor` and the IB-edge filter all
live in **`run_apparatus.py:544-645`**, experiment-local code. `xen.sigbar.ltf` only *stamps*
`available_mins_since` (`:583, :589, :684`); `grep` over `python/src/xen` finds no consumer of it,
and `xen/sigbar/__init__.py` exports nothing for it. SPDR-009 §9 commits only to *"no
reimplementation of `absorb_candidate_predicate`"*. So the one rule that runs 6 and 7 both blocked on
would be re-implemented by hand in the consumer — the divergence §1.1 exists to prevent.
*Required:* move the rule into `xen.sigbar.ltf` (e.g. `assign_session_at_close(cands, anchors, ltf)`
and `available_levels_for_bar(levels, mins_since_close)`), have W5 call it, and name it in §1.1
alongside `absorb_candidate_predicate`; add the corresponding "import, do not reimplement" line to
SPDR-009 §9.

**I8-3. [MODERATE] `n_ib_edge_unavailable` does not mean what its name says, and §1.1 never defines it.**
`run_apparatus.py:629-631` increments it only when the nearest level **over the full set** would have
been an IB edge. At D2 that is **665**, while the number of candidates for which an IB edge was
actually unavailable is **1,579** (`n_candidates_pre_ib`) — a factor of 2.4. `design.md:76-78` lists
the counter among the published fields without a definition, so a downstream reader (SPDR-009's power
census reads these counts) will take the plain-English meaning and be wrong.
*Required:* define it in §1.1 in one line, or rename it to something like
`n_nearest_would_be_unformed_ib`.

**I8-4. [MODERATE] The pinned run reused W1/W3/W4 from an earlier code state and records no evidence they still reproduce.**
The log line in `full_run_qa7.log` is `resuming from W5 — loading W1–W4 artifacts from disk`;
`seasonal_baselines_mtf.parquet` (20:33) / `class_thresholds_mtf.json` (20:35) / `sessions_mtf.json`
(20:35) predate `ltf.py` (21:03) and `run_apparatus.py` (21:04). The I7-5b fix asserts the reused
artifacts cover the run's **universe** but not that they were produced by the **shipped code**. I
verified BTCUSDT and CRVUSDT reproduce bit-identically, so nothing is stale in fact — but 2 of 194 is
a spot check, and the entire contamination history of this item is about reused artifacts.
*Required:* before freezing, either re-run end to end without `--from-w5`, or record in `pins.json`
which stages were reused together with a code fingerprint (e.g. sha256 of the `xen.sigbar` modules)
so a reader can tell.

**I8-5. [MINOR] The count identity is an assignment, not a check.**
`run_apparatus.py:660-662` sets `n_candidates_unanchored = cands.height − n_measured − n_no_levels`,
so `n_candidates == n_measured + n_no_levels + n_unanchored` cannot fail — the 0 violations I measured
across all 776 cells are arithmetic, not evidence. The value is also **0 on every cell**, so the
`drop_nulls("anchor_ts")` branch (`:558`) is never exercised in the emitted run.
*Required:* compute it as `cands.height − cand_joined.height` and `assert` the identity, so the
published number is a verification rather than a residual.

**I8-6. [MINOR] Orphan import left by the I7-8 fix.**
`run_apparatus.py:40` still imports `assert_no_per_level_delta`; nothing in the file calls it.
*Required:* delete the import.

**I8-7. [MINOR] SPDR-009 §3.1 plans a second implementation of the D1 level set.**
`SPDR-009/design.md` §3.1 *Level-set provenance*: *"D1 path: lift `INFR-018/code/hyp_i4_validation.py::prior_session_levels`
into `xen.sigbar.absorb` with byte-identical regression."* INFR-020's D1 census levels come from
`ltf.structural_levels_1m`. Two implementations of an object §1.1 declares MUST BE identical, with
the regression pointed at the *older* one.
*Required (quant-designer, SPDR-009 side):* name `xen.sigbar.ltf.structural_levels_1m` as the
regression target, or consume it directly.

**I8-8. [MINOR] AMENDMENT-19's direction label understates the population change (L-23).**
`design.md:643-652` books AMENDMENT-19 **NEUTRAL**. Its net effect on the census population is
**+1,109 D2 and +11 D4 candidates with none removed**; the tightening it cites (D4 stops discarding
valid events) is real but smaller. The ledger text names both directions honestly, so this is a label
nit, not a missing declaration. Running count 1L / 11T / 9N is arithmetically consistent with
AMENDMENT-18's 1L/10T/8N; no ≥3 one-directional streak at the tail.
*Required:* re-book as LOOSER-with-a-tightening-leg, or add one sentence saying why NEUTRAL is the
right label given the τ freeze reads the population.

**I8-9. [MINOR] The design's revision line is stale.**
`design.md:8-9` still reads *"Revision: 5 (post-implementation QA run 6: AMENDMENT-16/17/18 …)"*
while §8 now carries AMENDMENT-19 and AMENDMENT-20 from QA run 7.
*Required:* bump to revision 6 and name 19/20 in the header.

---

### 5. Can SPDR-009 construct exactly this population from the pins?

**Candidate population: YES.** `class_thresholds_1m.json` (194 symbols, 137 registry-overlap checks),
`class_thresholds_mtf.json` (194 × 3) and `seasonal_baselines_mtf.parquet` (582/582 blocks) are
pinned, the frozen INFR-017 1m baseline is unchanged, and `absorb_candidate_predicate` is one shared
function. I rebuilt D2/D4 candidate sets for three symbols from these objects and matched the census
exactly.

**Level set: PARTLY.** `structural_levels_1m` is shared and stamps both `level_source_bar_minutes`
and `available_mins_since`, so the *prices* are reproducible. But the **availability rule that turns
those stamps into a per-bar level set is experiment-local (I8-2)**, and the design has not decided
whether a self-set level belongs in the set at all (I8-1). Those are the two things that must close
before the population is unambiguous.

**Ambiguity remaining in the availability rule:** the rule *as implemented* is unambiguous and
correct; what is ambiguous is (a) where the consumer gets it from, and (b) the undefined
`n_ib_edge_unavailable` counter (I8-3).

---

### 6. Note to the operator

The nine things run 7 asked for are all done, and I checked every one by measuring rather than
reading. The important one — deciding "has the opening range finished forming yet?" at the bar's
close instead of its open — now reproduces exactly when I rebuild it from raw minute bars with my own
code, on three symbols across two of the four pairs. Nothing anywhere looks at a price before it
exists. The operator's decision to keep the bar and drop only the unformed level is implemented
faithfully and does **not** conflict with what SPDR-009 actually says.

Two things still block the handoff, and neither is a repeat of an earlier finding.

First, a bar can now be measured against a level that its own minutes created. At the 4-hour pair the
session's first 15-minute bar **is** the opening range, so its "distance to the opening-range edge" is
just a distance to its own high or low — and the screen deliberately selects bars with tiny ranges.
About 3.5–8.5% of kept events are affected depending on the pair, and their distances are three to
eight times shorter than everyone else's, which drags the yardstick the screen is about to freeze
toward zero. The programme already solved this once, in INFR-018, and that rule was not carried over.

Second, the availability rule itself lives in this experiment's own runner script, not in the shared
library. The whole point of the shared candidate function is that the screen imports the rule instead
of retyping it; the level-availability half has no such function, so SPDR-009 would have to rewrite by
hand exactly the logic the last two reviews rejected twice.

Everything else is small: one counter whose name promises more than it counts, one identity that is
computed rather than checked, a leftover import, and three documentation lines.

**Apparatus pins may NOT be frozen and handed to SPDR-009 yet.** W1 (baselines), W3/W3b (thresholds),
W4 (sessions), the coverage report and the gap report are sound and unaffected — I re-derived every
published figure. Only the two census artifacts and `pins.json` need re-emitting once I8-1 and I8-2
are closed.

## Run 9 — 2026-07-21T22:30:38Z — mode: subagent — HEAD 797f926973d610bc3b6d870219f90617f245fa26

Dirty at review start: the pre-existing checkpoint design and `xen.sigbar/{baselines,fences,sessions}.py`
were modified; `ltf.py`, `INFR-020/`, and `SPDR-009/` were untracked. Reviewed the current files,
INFR-020 revision 6, SPDR-009, and the complete run-9 artifact set. This section is append-only.

**Verdict: REVISE** — one MAJOR object-identity failure remains. The new D3 self-made-edge exclusion
and the shared-rule extraction are real, but D4's anchor-straddling bar can still use a prior-session
level that its own first 30 source minutes established. The W5 population is therefore not yet the
unambiguous population SPDR-009 is required to reproduce; do not hand these census pins to SPDR-009.

### Run-9 artifact and regression evidence

| Check | Result | Evidence independently measured |
|---|---|---|
| Full run / full battery | PASS | `full_run_qa9.log` is a fresh 194-symbol end-to-end run. Battery is `mode: full`, `all_ok: true`; A1 checks 194 symbols, A2 checks all 137 frozen registry blocks, and A1b grid sizes are 10080/2016/672/168. |
| All nine artifact pins | PASS | Recomputed SHA-256 for every `pins.json.artifacts` member; all nine match byte-for-byte. Frozen 1m baseline, column pin, and fence hashes also re-verify. |
| Full-universe scope | PASS | Baselines: 2,216,256 rows, 194 symbols, {5,15,60}m, four metrics. MTF thresholds: 194 x 3; 1m thresholds: 194 with 137 overlap checks; coverage, gap, sessions, D1 census, and four-pair W5 census: all 194. |
| Outcome / holdout / accounting fences | PASS | All nine JSON key vocabularies plus parquet schema pass `check_no_outcome_columns`; all run/battery reads are `load_bars(..., "DESIGN")`; `check_no_local_accounting(code/)` passes; no Nautilus/BacktestNode path exists. |
| Counter schema and identities | PASS | Every one of 776 cells has the declared counter schema; all satisfy `n_candidates == n_measured + n_no_levels + n_unanchored`. `n_ib_edge_unavailable` is defined as the nearest-full-set IB subset, distinct from `n_candidates_pre_ib`. |
| Coverage | PASS | Re-derived 194-symbol medians: 5m **0.3851**, 15m **0.2011**, 60m **0.0882** (unrounded 0.38505/0.20110/0.08815); >=0.50 counts **72 / 47 / 31**. Also reproduces >=0.90: 20/11/6 and <0.20: 28/95/132. |
| D3 raw-1m self-made rebuild | PASS | Independently re-aggregated every raw 1m series into exact 15-source-minute bars, applied pinned 15m residual blocks/cuts, and rebuilt 4-hour IB high/low formation times without the W5 availability helper. Result: **2,974** candidates and **191** self-made candidates across 194 symbols; every per-symbol count matches `zone_scale_census.json`. |
| Shared consumer contract | PASS | `absorb_candidate_predicate`, `assign_candidate_sessions`, `available_levels_for_candidates`, and `structural_levels_1m` each have one definition in `xen.sigbar.ltf`; W5 imports them and SPDR-009 §3.1/§9 explicitly requires imports rather than reimplementation. |

### T1–T20 trace and amendments 19–21

| Trace | Verdict | Evidence |
|---|---|---|
| T1–T8 | MATCHES | Outcome/provenance key checks; production causality path; generalised 5/15/60m grid; DESIGN fence; A1/A2/A3/A4/A5 battery all pass. A3 retains frozen BTC IB 21020.5 / 20833.0 / 187.5. |
| **T9 — level set / availability / self-made exclusion** | **DEVIATES — R9-1** | D3 IB-edge self-made exclusion matches raw minutes, but D4 prior-session levels do not carry a formation timestamp for anchor-straddling bars. |
| T10–T15 | MATCHES | No local accounting or engine path; all artifact hashes; no reconstruction; A6 reported; COMPLETE/traded-fraction path remains enforced. |
| T16 | MATCHES | Candidate predicate and availability/session rules are one shared implementation; SPDR-009 names the same imports. |
| T17–T20 | MATCHES | Null-scale cells are emitted, gap reconciliation is retained, fit/event paths require COMPLETE windows, and the coverage figures above reproduce. |
| AMENDMENT-19 | MATCHES | Close-time session assignment and the keep-the-bar/drop-only-unformed-IB-edge rule are implemented. D4 straddling counts (43) reproduce from raw bars with DST-aware A-USOPEN anchors. |
| AMENDMENT-20 | MATCHES | Full run emits all artifacts with checked writers, full battery, and current-time pin stamp; no local baseline substitution appears. |
| AMENDMENT-21 | PARTIAL — R9-1 | IB `formed_ts` closes the D3 defect (191/191 raw match) and the shared implementation closes the duplication defect. It does not cover D4 prior-session levels built partly by the straddling bar itself. Direction ledger is internally consistent at 2 LOOSER / 12 TIGHTER / 8 NEUTRAL. |

### Issue

**R9-1. [MAJOR] D4 anchor-straddling candidates can be measured against prior-session levels made by their own source minutes.**

`design.md` §1.1:76–85 says that **any** level whose `formed_ts >= candidate.OpenTime` is excluded.
This is necessary even though the candidate/session decision is correctly made at close. D4's daily
A-USOPEN anchor is 13:30 EDT / 14:30 EST, while a 60m candidate begins on the hour. The candidate
which straddles that anchor contributes its first 30 minutes to the session that becomes the
candidate's *prior* session.

But `structural_levels_1m` writes every `PRIOR_*` row with `formed_ts = null`
(`xen/sigbar/ltf.py:799–806`), and `available_levels_for_candidates` treats null as past-formed
(`ltf.py:440–451`). Thus those levels are unconditionally admitted in W5
(`run_apparatus.py:615–645`) even where the candidate's own minutes made or contributed to them.

Independent raw-1m reconstruction found **43** D4 straddling candidates, exactly the emitted count.
For **5** of them, the candidate itself set a prior-session high or low. Concrete failure:
`GMXUSDT`, D4 candidate open `2022-10-10 13:00Z`, assigned at close to anchor `13:30Z`; its own
minute at `13:04Z` formed `PRIOR_SESSION_LOW`. The current shared code emits that level with null
`formed_ts`, accepts it, and selects it as the nearest available level (distance 0.09). The same
30 source minutes also feed the prior session's POC/VA construction for every straddling candidate,
so treating all `PRIOR_*` rows as inherently past-formed is not valid in this case.

*Required change:* carry a usable formation boundary for **all** prior-session levels. At minimum,
stamp the prior-session completion boundary (`consumer anchor_ts`) on `PRIOR_*` profile levels and
the actual extrema timestamps on prior high/low; then let the existing shared availability predicate
exclude rows with `formed_ts >= OpenTime`. Define and emit a separate prior-self-made counter (or a
single all-level self-made counter with its exact semantics), add raw D4 DST/straddling regression
fixtures, reconcile the D4 count/distribution, and re-emit both census artifacts and `pins.json`.
SPDR-009 must continue to import the corrected shared rule, never patch this locally.

### Operator note

Run 9 repaired the main D3 problem and its provenance is otherwise clean. The remaining D4 defect is
small in row count but changes the exact population used to freeze the screen's distance cut, so it
is an integrity issue rather than a quality read. Fix the shared prior-level formation timestamps,
rebuild the two census artifacts, and re-run QA before SPDR-009 uses the pins.

## Run 10

**Reviewed:** 2026-07-21T23:24:07Z · **mode:** subagent, fresh context · **HEAD:**
`797f926973d610bc3b6d870219f90617f245fa26`

Dirty at review start: the pre-existing checkpoint design and
`xen.sigbar/{baselines,fences,sessions}.py` were modified; `ltf.py`, `INFR-020/`, `SPDR-009/`, and
`test_sigbar_infr020.py` were untracked. This review used those current files and the Run-10 results;
it did not treat older logs or pins as evidence.

**Verdict: APPROVE.** AMENDMENT-22 closes Run 9's D4 object-identity defect. Every structural level
now has non-null formation provenance, the common availability function rejects levels formed at or
after candidate open, both census schemas expose the complete accounting, and the raw D3/D4
populations independently reconcile. No blocking, major, or minor issue was found.

### Clean-run and pin evidence

| Check | Result | Independently verified evidence |
|---|---|---|
| Run provenance | **PASS** | `results/full_run_qa10.log` contains W2, W1, W3, W4, W3b, W5, and coverage, contains no `--from-w5`/resume marker, and ends `{"ok": true, "n_symbols": 194}`. This is a clean full rebuild, not W5 reuse. |
| Frozen inputs | **PASS** | Baseline `1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72`; column-pin contract `e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225`; fence manifest `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448`. Entry assertions and the fresh battery both pass. |
| Nine artifact hashes | **PASS** | Independently recomputed and matched: battery `c29bf4fe...`, gap `c1fe4aaf...`, baselines `86c81937...`, MTF cuts `745fb435...`, sessions `c55cd880...`, 1m cuts `dee853ad...`, primary census `f64e0d22...`, D1 sensitivity `76c3d4b5...`, coverage `68dac757...`. |
| Universe | **PASS** | Baselines: 2,216,256 rows, 194 symbols, four metrics, and 1,564,416/521,472/130,368 rows at 5/15/60m. MTF cuts: 194 x 3 blocks; 1m cuts: 194 with 137 frozen-registry identities. Sessions, battery, both censuses, coverage, and gap report all cover 194 symbols. |
| Battery | **PASS** | Pinned battery is full, `all_ok: true`, 194 symbols. A1/A1b/A2/A3/A4/A5/VT/A7-A10/A11 and accounting pass. A fresh full battery written to `/tmp` also passed all seven result blocks and is structurally identical to the pinned result. |

All nine SHA-256 values were compared in full; the ellipses above are display abbreviations only.
`pins.json` is stamped `2026-07-21T23:11:53.974362+00:00`, after the full battery stamped
`2026-07-21T22:57:46.924235+00:00`.

### Raw population and formation-provenance attack

I rebuilt 1m structural levels, candidate bars, session assignment, formation times, and nearest
available distances independently of the emitted census.

| Probe | Raw result | Artifact reconciliation |
|---|---|---|
| D4 full universe | 640 candidates; 43 anchor-straddling; 66 IB-self-made; 43 prior-self-made; 66 any-self-made | Exact match, including every per-symbol straddling count. Totals are 634 measured and 6 no-level. |
| D4 GMXUSDT | Candidate `2022-10-10 13:00Z`, 60 raw minutes, O/H/L/C 43.4/43.765/42.985/42.985; residuals 8.12539537/-1.17571784; assigned at close to A-USOPEN `13:30Z` | Prior high 43.765 formed exactly at candidate open and all prior profile levels formed 13:29, so they are excluded. Prior low 42.895 formed 11:59 and is available; distance `0.09 / 0.87 = 0.10344827586206502`, exactly the census value. |
| D3 API3USDT | Candidate `2022-11-05 00:00Z`, 15 raw minutes, O/H/L/C 2.113/2.127/2.109/2.115; residuals 4.478700696/-1.011736139 | IB high/low formed 00:01/00:04 and are self-made, so excluded. Prior levels formed before open; nearest is PRIOR_VAH 2.1121725, normalized distance 0.0912096774. Exact census match. |
| Missing/null provenance | Planted absent `formed_ts` and planted null `formed_ts` each raise `RuntimeError` before level use | Confirms provenance is mandatory rather than silently treated as past-formed. |
| Tied extrema | Synthetic prior high/low ties chose the first edge-setting minutes (2/3); IB high/low ties chose minutes 1/4 | Confirms earliest-tie semantics. Profile rows use the last contributing source minute. |

The primary census contains all 776 symbol/pair cells with the declared schema and `measurable` flag;
every cell satisfies `candidates = measured + no_levels + unanchored`. The D1 sensitivity artifact has
194 complete-schema cells and the same identity. The BUSD D1 unmeasurable edge case has all ten
counters zero in both artifacts, rather than a partial record.

Primary totals independently reconciled:

| Pair | candidates | measured | no-level | pre-IB | straddling | IB self-made | prior self-made | any self-made |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| D1 | 95,836 | 95,774 | 62 | 642 | 0 | 399 | 0 | 399 |
| D2 | 9,497 | 9,497 | 0 | 1,579 | 0 | 1,777 | 0 | 1,777 |
| D3 | 2,974 | 2,974 | 0 | 0 | 0 | 191 | 0 | 191 |
| D4 | 640 | 634 | 6 | 43 | 43 | 66 | 43 | 66 |

### Design-fidelity trace T1–T20 against revision 7

| # | Clause | Verdict | Evidence |
|---|---|---|---|
| T1 | Two-layer outcome/provenance ban | **MATCHES** | Every JSON vocabulary and parquet schema passes the outcome-name scan; emitted frames carry causal provenance. Planted forbidden columns/provenance raise. |
| T2 | Bar causality | **MATCHES** | Production W2 asserts source counts/timestamps for every symbol/timeframe; A4/A5/VT pass. |
| T3 | Generalised seasonal baseline | **MATCHES** | Correct 5/15/60m grids, 194-symbol parquet, four metrics, and no competing 1m partition. |
| T4 | DESIGN-only fence | **MATCHES** | All run reads use DESIGN; recursive artifact timestamp scan found no non-generation value on/after 2023-03-01. TEST/holdout are unreachable through the declared bands. |
| T5 | A1 frozen value identity | **MATCHES** | Full battery checks all 194 symbols through the generalised path. |
| T6 | A2 threshold extension/identity | **MATCHES** | 194 1m blocks, all 137 frozen-registry overlaps identical; lookalike estimator discrimination passes. |
| T7 | A3 frozen sessions | **MATCHES** | Battery passes; SPDR-008 frozen IB traces also reproduce. |
| T8 | A4/A5/A5b aggregation | **MATCHES** | Additivity/associativity/legacy numeric comparison pass; VT-1..3 reproduce. |
| T9 | 1m levels and causal availability | **MATCHES** | `structural_levels_1m` supplies non-null formation time for every level; availability requires `formed_ts < OpenTime`. Raw D3 and D4 attacks above reconcile. |
| T10 | No local accounting/engine | **MATCHES** | `check_no_local_accounting` passes on `code/` and the full experiment; no BacktestNode/Nautilus or outcome computation path. |
| T11 | Frozen inputs and artifact pins | **MATCHES** | All three frozen-input contracts and all nine artifact hashes independently match. |
| T12 | No reconstructed event path | **MATCHES** | No fill, upsample, or synthetic-minute path feeds fitting or candidates. |
| T13 | Old collection-gap refusal | **N/A — superseded** | T18's staging-derived gap-day disclosure is the binding rule. |
| T14 | A6 is reported, not gated | **MATCHES** | Sparse/null-scale statistics are emitted without becoming a hypothesis gate. |
| T15 | COMPLETE/traded-fraction invariant | **MATCHES** | Fits and candidates require COMPLETE windows and `traded_fraction == 1.0`; battery checks the guard. |
| T16 | One shared consumer contract | **MATCHES** | Single definitions of candidate predicate, session assignment, availability, and 1m structural levels in `xen.sigbar.ltf`; W5 imports/calls them and SPDR-009 §§3.1/9 names the same imports. |
| T17 | Null-scale reporting | **MATCHES** | Volume/range null-scale cells for 5/15/60m and the 1m block are present. |
| T18 | Gap derivation/reconciliation | **MATCHES** | Staging-derived gap days and ledger mismatches remain emitted; battery A11 passes. |
| T19 | COMPLETE-only fitting/events | **MATCHES** | Production assertions guard W1, W3, and W5; no fabricated/non-COMPLETE window enters the population. |
| T20 | Full coverage disclosure | **MATCHES** | Independent medians 0.38505/0.20110/0.08815; >=0.50 counts 72/47/31, >=0.90 20/11/6, <0.20 28/95/132. |

AMENDMENT-19 close-time assignment and keep-bar/drop-unavailable-level semantics match. AMENDMENT-20
checked emission, universe coverage, no local baseline substitution, and pin stamping match.
AMENDMENT-21 shared availability plus IB self-made exclusion matches. AMENDMENT-22 non-null
prior-level provenance, earliest extrema, profile completion timestamps, new counters, and complete
census schemas matches. The ledger arithmetic is consistent at **2 LOOSER / 13 TIGHTER / 8 NEUTRAL**.

### Regression and governance

| Check | Result |
|---|---|
| Focused tests | **PASS** — 49 passed, 1 skipped (`test_sigbar_baselines`, `test_sigbar_infr018`, `test_sigbar_infr020`, `test_estimand_validation`). |
| Full regression | **PASS** — 263 passed, 4 skipped with `PYTHONPATH=python`; one expected NumPy warning. |
| SPDR-007 golden trace | **PASS** — BTC/SOL rejects and ETH accept with frozen MFE/MAE/asymmetry values reproduce. |
| SPDR-008 golden trace | **PASS** — all four traces; final `SMOKE OK`. |
| Fresh full battery | **PASS** — full, 194 symbols, every block including A11 and accounting. |
| Outcome/date/accounting | **PASS** — no forbidden artifact field, no post-DESIGN data timestamp, no local accounting/engine path. |
| Repository hygiene | **PASS** — `git diff --check` clean; no test cache or bytecode created; review-start dirty set otherwise unchanged. |

### Gate disposition

There are **no open issues** from Run 10. INFR-020 revision 7 and its Run-10 artifacts are suitable
for the operator's freeze decision. The next state is the **operator freeze gate only**: this review
does not itself freeze the pins, and SPDR-009 has not been implemented.
