# Results: Experiment EXP-080 — Phase 018 CF-CAPGEO-001 Substrate/Exit Readiness

**Stage 6 interpretation.** Companions: [`scope.md`](scope.md), [`analysis-plan.md`](analysis-plan.md),
[`audit.md`](audit.md). **Verdict: `READINESS_DELIVERED`.** This is a readiness/coverage deliverable,
**not a market-edge claim** — no edge, return, capture, MFE/MAE, expectancy, or P&L metric is computed
anywhere in EXP-080 (the only return series is the non-tradable null-FPR machinery probe). Results are
interpreted strictly against the analysis-plan Interpretation Guide; no goalposts were moved.

> Interpreted on the re-run after the Stage-5 audit fixed two verdict-material defects (dropped-fraction
> metric; null-FPR probe scale) and re-audit returned PASS. The pre-fix run's `SUBSTRATE_REFUTED` is
> superseded and not interpreted as a finding (see [`audit.md`](audit.md) Critical-1/2 and Re-Audit).

---

## 1. Headline (against the pre-defined Interpretation Guide)

The 192-substrate-cell readiness map, the per-cell entry-count + D7-bracket table, the null-FPR
machinery sanity, and the harami entry-identity disclosure were all produced → **`READINESS_DELIVERED`**.
No `SUBSTRATE_REFUTED` halt leg fired: non-determinism on 0 cells; no invariant violated on ≥3
instruments for any substrate (0 invariant failures total); null-FPR controlled across the binding
operating regime (n ≥ 120).

| Quantity | Value |
|---|---|
| Substrate-cells | 192 (4 substrates × 16 instruments × {15m,1h,4h}) |
| READY | **184 / 192** |
| NOT_READY (`COVERAGE_EXCLUDED`) | **8 / 192** = US500-4h + JP225-4h, ×4 substrates each |
| Non-deterministic cells | 0 |
| Invariant-failure cells | 0 |
| D7 bracket [15,8000] | **192 / 192 IN_BRACKET** |
| Null-FPR (operating regime n ≥ 120) | CONTROLLED (all wilson_hi ≤ 0.075) |
| Harami entry identity | identical in all cells |
| Domain-bar regression vs VAL-005 | frame-identical (85,839 rows, EURUSD-15m) |

---

## 2. Readiness map (per stratum — no pooling)

**184/192 READY** across all 16 instruments × {15m,1h,4h} except the two excluded 4h cash-equity-index
cells. READY = coverage-based construction integrity PASS (dropped ≤ 0.25, fence held) ∧ zero
entry-detector invariant violations ∧ determinism PASS — the lenient EXP-043/048 readiness convention
(entry count / bracket do not affect READY).

**8 NOT_READY = 2 unique instrument×domain cells × 4 substrates:**

| Cell | Dropped fraction | Construction | Invariants | Determinism | Disposition |
|---|---|---|---|---|---|
| **US500-4h** | 0.251 | COVERAGE_EXCLUDED (>0.25) | pass | pass | excluded from EXP-081 with record |
| **JP225-4h** | 0.281 | COVERAGE_EXCLUDED (>0.25) | pass | pass | excluded from EXP-081 with record |

These are **genuine 4h coverage-sparsity exclusions**, not substrate or generator defects: both cells
pass every invariant and determinism check; only the coverage drop exceeds the frozen 0.25 band. The
outcome is consistent with the EXP-043 precedent (index cells thin at coarse domains — JP225-2h was
NOT_READY at 0.2566 there). At 4h, cash-equity-index session + holiday structure leaves a fraction of
data-bearing 4h windows below the 0.90 coverage threshold. Under the lenient convention these are
**disclosures excluded from downstream with record**, not failures of the substrate.

**Caveat (from audit):** US500-4h at **0.251** is borderline — it clears the 0.25 FAIL band by 0.001.
The band is predeclared (frozen EXP-043/048/VAL-005) and is not retro-edited; the borderline status is
recorded so EXP-081 membership treats US500-4h as a knife-edge exclusion rather than a clear failure.

The dropped-fraction metric measures coverage quality (validated `(candidate − retained)/candidate` over
fence-eligible data-bearing windows), confirmed by its realized stratification: @15m BTCUSD 0.013,
USTEC 0.002, forex/gold ~0.02, US500 0.091, JP225 0.161 — i.e. it tracks per-cell coverage, not
market-session structure (the Critical-1 defect, now fixed).

---

## 3. Entry coverage & D7 bracket (descriptive)

**All 192 substrate-cells are IN_BRACKET [15,8000]** → every cell sits inside the Phase-017-validated
`ASS`-discovery sample-size regime; `ASS` discovery readouts are trustworthy in their validated regime
for every cell (and the **frozen referee suite is the binding gate regardless**, per D0 §D7 — no
readiness consequence either way). No `OUT_LOW` / `OUT_HIGH` cells.

| Substrate | Cells | Entry count min / median / max |
|---|---|---|
| SUB-AVWAP | 48 | 78 / 495 / 2,641 |
| SUB-HARAMI-PARTIAL-V2A | 48 | 284 / 1,658 / 7,657 |
| SUB-HARAMI-V2A-ADVNONE | 48 | 284 / 1,658 / 7,657 |
| SUB-RANDOM | 48 | 284 / 1,658 / 7,657 |

`SUB-AVWAP` is the **sparser, more selective** entry stream (78–2,641); the conditioned-harami stream is
denser (284–7,657, max just inside the 8,000 ceiling). `SUB-RANDOM` is matched per cell to the harami
realized count (the headline matched control), so its range coincides with harami by construction.
Entry rates are reported per 1,000 domain bars in `ready_map.csv` with disclosed denominators; no
zero-baseline / 0/0 ratios occur.

---

## 4. Null-FPR machinery sanity (the one statistical test)

Moving-block bootstrap one-sided `CI_low > 0` false-positive rate on a non-tradable, mean-centered,
block-permuted EURUSD-15m domain-bar log-return carrier, at the **validated m_cell machinery scale**
(N_NULL = 5,000, N_BOOT = 10,000; gate wilson_hi ≤ 0.075 at operating floor n ≥ 120 — unchanged).

| n | FPR | Wilson-hi | Regime | Controlled |
|---|---|---|---|---|
| 15 | 0.083 | 0.0908 | small_n_disclosed | — (disclosed, non-binding) |
| 30 | 0.078 | 0.0853 | small_n_disclosed | — (disclosed, non-binding) |
| 60 | 0.074 | 0.0814 | small_n_disclosed | — (disclosed, non-binding) |
| **120** | 0.057 | **0.0642** | operating | **yes** |
| 250 | 0.061 | 0.0680 | operating | yes |
| 500 | 0.059 | 0.0657 | operating | yes |
| 2000 | 0.049 | 0.0555 | operating | yes |

**The moving-block inference machinery is CONTROLLED at the 5-year data scale across the entire binding
operating regime (n ≥ 120).** The downstream `WF-EXPANDING` inference can be trusted at this scale.
The small-n (n < 120) FPR inflation persists (0.081–0.091) but is the **disclosed Phase-017 EXP-077/078
property** (percentile-bootstrap small-sample under-coverage; D0 §D6 Guard (i) defers to the median at
effective-n ≤ 60) — recorded, non-binding, by the ratified D0 §D9 operating floor.

**Scale-sensitivity caveat (from audit Critical-2).** The n=120 boundary decision is scale-sensitive:
at the original bounded probe (N_NULL=1000, N_BOOT=2000) it read wilson_hi 0.0787 (>0.075, an apparent
halt); at the validated machinery scale it resolves to 0.0642 (controlled). The prior exceedance was a
probe-scale artifact, not a machinery defect. This is reported honestly: control at n=120 holds at the
validated scale, and the operating-floor gate decision should always be evaluated at that scale (as it
will be in EXP-083 at N_BOOT=10,000). It is a one-cell boundary that is comfortably (not marginally)
controlled once correctly scaled, but it is not a wide margin — worth carrying forward as a known
scale dependence.

---

## 5. Harami entry-population identity (disclosure)

`SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` produce **identical entry events in every cell**
(harami_entry_identity_all_cells = True). This is by construction — both carry the one MA(20,50)-native
`/STRONG-STAT`-conditioned HA-harami entry and differ only by their later benchmark *exit* (not applied
in EXP-080). Consequence: their **entry-level counted-read accounting coincides** (an efficiency, not a
finding). The two remain distinct substrates downstream once their exits are applied (EXP-082/083).

---

## 6. Determinism, causality, and reuse

- **Determinism:** 0 non-deterministic cells; the full second pass is frame-identical (entries) /
  byte-identical (`SUB-RANDOM` from its fixed seed). Seeds recorded in `run_metadata.json`.
- **Look-ahead safety:** 0 invariant-battery failures across all 192 cells — every entry timestamp is
  within the analysis span, on a completed bar close, with detector-specific causal anchors confirmed
  (AVWAP anchor/armed ≤ entry; harami in-progress confirm ≤ entry); `SUB-RANDOM` lands only on
  completed closes.
- **Holdout / construction:** only Parquet metadata + the first-70% analysis slice are read; the
  holdout-fenced `build_domain_bars` reconciles frame-identical to the VAL-005 original (85,839 rows on
  the shared EURUSD-15m cell), so domain construction is the validated path.
- **Real-price discipline:** no return/capture/P&L of any kind is computed. The harami detector runs on
  HA candles (entry detection only), all gating on real OHLC; the sole return series is the explicitly
  non-tradable, mean-centered null-FPR machinery probe.

---

## 7. Limitations

1. **Two 4h index cells excluded** (US500-4h, JP225-4h) on coverage; US500-4h is borderline (0.251).
   The 4h cash-equity-index domain is the thin corner of this dataset; downstream reads on those two
   cells are unavailable with record.
2. **Small-n null-FPR inflation** (n < 120) persists as the disclosed Phase-017 property; any downstream
   per-cell inference at effective-n < 120 must defer to the median / disclose per D0 §D6 Guard (i).
3. **Null-FPR operating-floor decision is scale-sensitive** (§4): it must be evaluated at the validated
   N_BOOT=10,000 machinery scale; the n=120 control margin, while clear, is not large.
4. **AVWAP is a sparser entry stream** than the harami substrates (78–2,641 vs 284–7,657); some AVWAP
   cells sit toward the low end of the bracket, so AVWAP per-cell inference will carry wider intervals
   than harami at the same instrument/domain.
5. **Readiness ≠ edge.** This experiment establishes only that the four frozen entries reproduce, are
   causal, and have adequate coverage. Nothing here supports or refutes any exit/expectancy/capture
   claim.

---

## 8. Next steps (new experiment scopes only — no EXP-080 extension)

- **EXP-081 (HYP-002, characterization):** per-substrate return-structure features (D3 inputs) + the
  minority-mass / left-tail-mass descriptive read, **TRAIN-only, gross, real prices**, on the
  **member set = 46 instrument×domain cells** (48 minus US500-4h and JP225-4h) × the frozen substrates
  — i.e. the 184 READY substrate-cells, excluding the 8 COVERAGE_EXCLUDED with record. New scope/D0
  alignment under the Phase 018 checkpoint.
- The two excluded 4h cells are carried as disclosures; if 4h index coverage is later deemed material, a
  scoped addendum (own EXP-ID) could revisit the coverage band — **not** an EXP-080 re-run.

These are registry-relevant readiness outcomes (substrate-cell membership for the Phase 018 batch) but
spend **0 counted TEST reads** (readiness exposure = disclosure); the registry disposition is recorded
at Stage 7.
