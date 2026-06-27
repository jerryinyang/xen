# Experiment: EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate on the EXP-083 Valid-Candidate Set (CF-CAPGEO-001 Phase 018 / HYP-004 cost read-gate)

**Phase:** 018 (CF-CAPGEO-001 data-derived exit / capture geometry; checkpoint
`2026-06-20-018-capgeo-exit-geometry`) · **Registration:** **D0-amendment-002 (operator-directed
2026-06-22)** — re-sequences the already-registered conditional cost layer (D0 §D2, EXP-072/073 precedent)
to run **TRAIN-only as a G-018 read-gate, before the counted-read confirmation (EXP-084)**. · **HYP:** not a
new hypothesis — the **cost-robustness extension of the HYP-004a TRAIN screen** on the registered survivors.
· **Candidate slots:** 0 (cost layer on the registered survivors — EXP-030 precedent; no new countable
candidate item). · **TEST reads:** **0 counted (TRAIN-only).**

**Registry precondition (Stage-1 check).** `CF-CAPGEO-001` is `REGISTERED`/SCREENING. The countable item is
the **EXP-085** row registered in `multiplicity-registry.md` Phase 018 batch (added with D0-amendment-002);
no new candidate variant, detector, or parameter branch is introduced (the cost layer evaluates the already
hash-pinned survivors). EXP-085 reads **no TEST stratum** — it is TRAIN-only — so no `test-read-ledger.md`
tally is spent; all 48 strata stay 0/2 open (the EXP-074/075/080/081/082/083 TRAIN-only-disclosure
precedent). The binding EXP-083 valid set sha256 `fa4035f3…` is asserted before any read.

---

## Hypothesis / Exploratory Question

**Read-gate question (TRAIN-only, net, no holdout/TEST contact):** Under a **predeclared conservative
per-event cost/slippage + holding-time financing model** (frozen before any TRAIN read; never tuned), does
**any** of the 26 EXP-083 hash-pinned valid `{candidate × stratum}` survivors — the 4 binding S2-PASS arms
**and** the 22 S2-DEFERRED arms — retain a **net** per-event edge (net expectancy ∧ net median one-sided
`CI_low > 0`, per stratum) on the screen-TRAIN region? Or does realistic cost consume the gross edge, as it
did in both prior families (EXP-030, EXP-045)?

**Falsifiable structure.** The verdict is one of:

- **`NET_SURVIVES`** — **≥1** of the 26 survivors clears the net per-stratum gate (net expectancy ∧ net
  median `CI_low_1s > 0`). The surviving subset (the net-positive `{candidate × stratum}`) is reported as the
  **read-eligible set** for a *possible* EXP-084 counted read — **opened only on additional operator
  ratification at EXP-084's own D0** (this experiment does not authorize a read).
- **`NET_FLAT`** — **0** of the 26 retains a net edge. Then **EXP-084 is never opened, 0 lifetime TEST reads
  are ever spent**, and HYP-004 closes at G-018 on the TRAIN screen + cost gate alone (the EXP-030/045
  "gross edge, cost-killed" outcome reproduced on this family).

This is a **gross→net robustness gate, not a confirm**: no frozen referee suite, no `WF-EXPANDING`, no TEST
or holdout contact (all EXP-084). It is a **read-gate input** to the operator's G-018 decision; it does not
itself close or open the family.

## Question (plain language)

The screen found these 26 survivors *gross*. Their stops sit at the catastrophe edge (≈ −7.28 ATR per
stop-out), and the screen never charged a cent of cost. Do any of them still make money once realistic
spread, slippage, and financing are subtracted on training data — before we spend one of the programme's two
lifetime TEST reads? If not, we learn it for free.

## Scope Boundaries

- **Data views:** the **5-year, post-INFR-003, VAL-005-admitted** 1-minute time bars, resampled by the
  holdout-fenced `build_domain_bars`, **identical** to EXP-083. Real OHLC only. No new data is read beyond
  the strata the survivors occupy.
- **Candidate set (frozen, read verbatim):** **exactly the 26 EXP-083 valid `{candidate × stratum}`
  survivors** in `EXP-083/results/valid_candidate_set.json` (sha256 `fa4035f3…`, asserted first) — the 4
  S2-PASS (`SUB-HARAMI-V2A × AUDUSD × 1h`: `AVWAP-FH`, `RR-1.5`, `RR-2`, `RR-3`) **and** the 22 S2-DEFERRED
  (`SUB-AVWAP` 4h: NZDUSD ×10, USDCAD ×11, USTEC ×1). No re-screen; no new candidate; the survivors' realized
  exit paths are reproduced via the same frozen machinery (assert n_resolved + gross mean reconcile to the
  screen within 1e-9).
- **Instruments / domains (the survivor strata only):** **AUDUSD-1h, NZDUSD-4h, USDCAD-4h, USTEC-4h** (4
  instrument×domain cells; the only cells carrying a survivor). No other cells are read.
- **Read region (TRAIN only):** the **TRAIN sub-split** `[0, int(analysis_rows·0.7))` of each cell's
  analysis slice (the same region EXP-083 read). The analysis-TEST stratum and the final-30% global holdout
  are **never sliced, materialized, inspected, counted, or used.**
- **Cost layer (the only addition):** a deterministic arithmetic overlay (below). No strategy/exit parameter,
  entry, substrate, barrier, or denominator changes. The cost layer is applied to the **already-resolved**
  real-price exit return of each event (causal — no look-ahead).
- **Exclusions:** no TEST read, no holdout contact, no `WF-EXPANDING`, no frozen-referee-suite adjudication
  (all EXP-084); no re-derivation or re-screening of candidates; no barrier/entry tuning; no cost-constant
  tuning against outcomes (constants frozen before any TRAIN read); no cross-stratum pooling as a binding
  statistic (per-stratum default, LESSON-001; any aggregate is disclosure).

## Predeclared Cost Model (frozen structure + constants — before any net number is read)

Inherits the **EXP-030 CONSERVATIVE** model + the **EXP-034 financing** model, extended to the 4 survivor
instruments. Frozen here; **operator ratification of the per-instrument constants is required at Stage 4 /
before the manual TRAIN run** (the EXP-030 cost-table convention).

1. **One round-trip charge per event.** Each held position bears one full round-trip cost `RT_i`
   (entry + exit). Nothing is amortized.
2. **Per-instrument round-trip cost `RT_i`** (bps of price): a single conservative constant covering
   spread + commission + slippage; **CONSERVATIVE = 2 × BASE is binding** (EXP-030 §5). Slippage is
   spread-scaled (folded into `RT_i`), **not** ATR-scaled (EXP-030 §4).
3. **Adverse-side financing `F_i`** (bps of price per calendar day), charged on the realized holding
   duration of each event: `financing_e = F_i × holding_days_e`, where `holding_days_e` is the resolved
   exit time minus entry time in days (domain bars → minutes → days; EXP-034).
4. **ATR-unit conversion (to match the screen's ATR-unit returns).** Per event, the price-unit cost is
   `cost_price_e = (RT_i/10_000 + F_i/10_000 × holding_days_e) × P_entry_e`; the ATR-unit cost is
   `cost_ATR_e = cost_price_e / ATR_entry_e` (Wilder ATR(14), the EXP-081 normalization). Then
   **`net_ATR_e = gross_ATR_e − cost_ATR_e`** on identical events (same denominator as the screen).
5. **Proposed frozen constants (CONSERVATIVE binding; PENDING OPERATOR RATIFICATION):**

   | Instrument | BASE RT (bps) | **CONSERVATIVE `RT_i` = 2×BASE (bps)** | **Financing `F_i` (bps/day, adverse)** | Anchor |
   |---|---|---|---|---|
   | AUDUSD | 2.0 | **4.0** | **0.8** | FX major, slightly wider than EURUSD (3.0/0.6) |
   | NZDUSD | 2.25 | **4.5** | **0.8** | FX, less liquid than AUD |
   | USDCAD | 2.0 | **4.0** | **0.7** | FX major |
   | USTEC | 2.5 | **5.0** | **1.2** | index — reused verbatim from EXP-034 |

   These are conservative and data-anchored to the EXP-030/034 precedent (EURUSD 3.0/0.6; USTEC 5.0/1.2);
   they are **never tuned against EXP-085 outcomes**. The operator may adjust them at ratification; once
   ratified they are frozen before the TRAIN read.

## Success / Failure / Inconclusive Criteria

- **`NET_SURVIVES`:** for ≥1 of the 26 survivors, the net per-event **expectancy** `CI_low_1s > 0` **and**
  net **median** `CI_low_1s > 0` (moving-block bootstrap, block `b=max(1,round(m^(1/3)))`, `N_BOOT=10_000`,
  one-sided 95% lower bound — the same kernel EXP-083 used), per stratum. The net matched-random excess
  (`net_candidate − net_matched_random` on the same cell, same cost applied to both) is reported as a
  companion (not the binding leg here — the binding leg is net-positive-expectancy, the tradability question).
  Report the read-eligible subset; recommend EXP-084 **only** on operator ratification.
- **`NET_FLAT`:** 0 of the 26 clears the net gate. Real, publishable result — routes HYP-004 to G-018
  closure with 0 lifetime reads. Record per-survivor net expectancy/median + CI and which leg failed.
- **Cell-level INCONCLUSIVE (per stratum, disclosed):** a survivor whose net CI **spans zero**
  (`CI_low ≤ 0 ≤ CI_high`) is `NET_INCONCLUSIVE_SPANS_ZERO` — expected for the low-n S2-deferred 4h cells
  (n=44–78; wide CIs). Recorded, never silently dropped; it is neither a survivor-by-default nor a failure.
- **Process-level HALT (not a result):** the `fa4035f3…` sha256 mismatch; any TEST-stratum or holdout row
  touched; non-determinism on replay; or a reconciliation failure (re-resolved gross ≠ EXP-083 gross beyond
  1e-9). Any halts and routes to a fix.
- There is **no edge / tradability / confirm verdict** here (0 reads, no referee suite). Only TRAIN-only
  net-survival eligibility feeding the G-018 read decision.

## Complexity Budget

- **Max statistical-method families: ≤ 2** — (1) net per-event expectancy + median with moving-block
  bootstrap one-sided `CI_low` (reuse `xen.capgeo_screen.one_sided_lo`); (2) net matched-random excess CI
  (reuse `xen.capgeo_screen.two_sample_diff_lo`). Both reused from the screen; no new test type.
- **Max visualisations: ≤ 3** — (i) per-survivor net expectancy (CI_low whiskers) vs the zero line, by
  cell, with the gross value marked (the gross→net waterfall); (ii) cost decomposition per survivor
  (transaction vs financing share, ATR units); (iii) net vs gross scatter across the 26 survivors with the
  net=0 and gross=net diagonals.
- **Max new code modules: ≤ 1** under `python/src/xen/` — at most a small cost-layer helper
  (`xen.capgeo_cost`: per-event `cost_ATR` from `RT_i`/`F_i` + holding duration) **only if** it cannot be
  composed inline from existing kernels. **Reuse first**: the survivor exit paths come from the frozen
  `xen.capgeo_screen` resolvers via the EXP-083 orchestration (the `ass_overlay.py` reuse pattern); no edit
  to any frozen module.

## Metric Denominators & Zero-Baseline (predeclared, before implementation)

- **Event denominator:** each survivor is scored on the **identical frozen-substrate held-position event
  set** the screen used (the EXP-042 same-denominator invariant; assert n_resolved == EXP-083). The cost
  layer subtracts a per-event charge; it **never filters or alters the event set**.
- **Net expectancy / median:** absolute **differences** in ATR units (`net = gross − cost`), with
  moving-block bootstrap CIs — no percentage-vs-zero-baseline metric, so no `0/0` exposure. Finite handling
  explicit (no silent NaN); a degenerate ATR or missing price → event excluded with record (none expected —
  the screen already resolved these events).
- **Matched-random net excess:** a **difference** (`net_candidate − net_matched_random`) on the same cell
  under the **same cost model applied to both** — no ratio against a possibly-zero baseline.
- **Holding duration:** `holding_days_e ≥ 0`; a zero-duration (entry==exit) event has 0 financing (only the
  round-trip charge), explicit.

## Frozen Constants (predeclared; recorded here pre-run)

- Cost: `RT_i`/`F_i` per the §Cost-model table (CONSERVATIVE binding; pending operator ratification).
  Bootstrap: `N_BOOT = 10_000`, one-sided 95% `CI_low`, moving-block `b=max(1,round(m^(1/3)))` (== EXP-083).
  Units: returns + costs in **ATR** (Wilder ATR(14)). Event floor ≥ 30 (== the screen; all 26 survivors
  qualify by construction). Seeds: bootstrap seed fixed and recorded; second pass byte-identical.
- Provenance: EXP-083 valid-set sha256 `fa4035f3…` asserted; the frozen `xen.capgeo_screen` /
  `xen.capgeo_substrates` / `xen.capgeo_geometry` / `xen.domain_bars` / `xen.capgeo_exits` module hashes
  recorded (unchanged from EXP-083).

## Data Requirements

For each of the 4 survivor cells (AUDUSD-1h, NZDUSD-4h, USDCAD-4h, USTEC-4h): load the 5-year file
(latest-glob), slice the first-70% analysis set, build domain bars (holdout-fenced), take the TRAIN
sub-split, regenerate the substrate entries + the survivor candidates' resolved exit paths via the frozen
`xen.capgeo_screen` machinery (reconcile gross to EXP-083), then for each survivor compute per-event
`holding_days`, `cost_ATR`, and `net_ATR`, the net expectancy/median + bootstrap `CI_low`, and the net
matched-random excess. Emit:

- `results/cost_readgate.parquet` / `.csv` — one row per survivor `{substrate × instrument × domain ×
  candidate}`: `n_resolved, gross_exp, gross_med, cost_atr_mean, txn_share, fin_share, net_exp, net_exp_lo,
  net_med, net_med_lo, net_matched_excess_lo, net_verdict ∈ {NET_POS, NET_INCONCLUSIVE_SPANS_ZERO,
  NET_NEG}`.
- `results/valid_net_set.json` — the read-eligible subset (net-positive survivors) + provenance, **with the
  explicit note that it authorizes nothing** until operator ratification at EXP-084's D0.
- `results/run_metadata.json` — frozen cost constants, seeds, module hashes, EXP-083 sha assertion,
  reconciliation_ok, determinism replay, `holdout_untouched: true`, `counted_test_reads: 0`,
  `candidate_slots: 0`, verdict `NET_SURVIVES` / `NET_FLAT`.

### Standard Loading Pattern (TRAIN sub-split only; no TEST/holdout)

```python
# reuse EXP-083's frozen loader/orchestration (the ass_overlay.py reuse pattern):
#   load_first70 -> build_domain_bars -> TRAIN slice [0, int(analysis_rows*0.7)) -> frozen entries/exits
# the analysis-TEST stratum and final-30% holdout are never sliced here.
```

## Suggested Direction (non-binding)

Reuse the EXP-083 orchestration exactly as `ass_overlay.py` did (import `run_experiment.py`, re-resolve the
26 survivors, assert reconciliation), then apply the cost overlay as a pure per-event arithmetic transform
and re-run the same bootstrap kernels on the net returns. Spend the discipline budget on (1) asserting the
`fa4035f3…` sha + the gross reconciliation before any net number, (2) the EXP-042 same-denominator
invariant, (3) the determinism replay, and (4) keeping the cost constants frozen and operator-ratified
before the TRAIN read. Keep the gate clean: EXP-085 decides **net eligibility on TRAIN**; only EXP-084 (if
ratified) spends a counted read.
