# EXP-094 — 4h Readiness + Falsification Re-Screen (RSI-2 fade / EXIT-RCT, TRAIN-only)

**Phase 021 (CF-MR-001 batch 2) · `CF-MR-001/HYP-002` · 2026-06-24 · Verdict: `ADMIT_4H` (4h opened →
**admitted** as a domain expansion) · Audit: PASS (re-audit after a corrected-bite-check rerun) · 0 candidate
slots · 0 counted TEST reads · holdout sealed.**

## Question

`D0-amendment-004` opened the 4h domain (excluded at G-020 as dead-by-absence, EXP-089 1/14) behind a binding
falsification gate, after an operator hunch (archived `TEMP-091`: EXIT-RCT net-clears 12/12 on 4h). EXP-094 asks:
**is the 4h net-of-cost EXIT-RCT edge the fade *entry signal*, or generic ATR-normalized oscillation harvesting?**
Three TRAIN-only legs: (a) 4h readiness/MDE (EXP-090 analog); (b) the frozen net exit screen (EXP-091 analog);
(c) the binding **matched favourable-target-distance oscillation null** (`D0-amendment-005`) — real EXIT-RCT must
beat a same-distance favourable limit fired at random times in ≥5 cells / ≥3 instruments — plus a 1h positive
control and a GREEN bite-check of the new statistic.

## Result

**`ADMIT_4H`.** On the **6 powered 4h members** (AUDJPY, EURJPY, EURUSD, GBPJPY, USDCHF, XAUUSD-4h):

| Leg | Result |
|---|---|
| (a) readiness | **6 MEMBER / 7 COVERAGE_EXCLUDED** (6 "no finite RCT MDE"; JP225 build-fail) |
| (b) net screen | EXIT-RCT net-clears **6/6 cells / 6 instruments** |
| (c) falsification (binding) | real beats matched-distance null **6/6** (`delta_lo` 0.19–0.27) |
| (c) realized-capture sensitivity | real beats the nearer-distance null **6/6** (non-binding; robustness) |
| (d) 1h positive control | **5/5** beat (statistic empirically powered) |
| (e) bite-check | **GREEN** (FPR per-cell 0.052 / quorum 0.000; per-cell power@0.10-ATR 0.857; two-sample MDE 0.10 ≪ observed Δ 0.276) |

## Why (mechanism)

A **completion-rate** result, not a magnitude artifact. Both arms rest a favourable limit at the **same target
distance** with the **same** 2×ATR stop + MR-tempo cap + 1m fill + cost; only the *timing* differs. Real RCT
(fade extreme) hits its reversion-completion target on **~99%** of events; the same-distance limit fired at
**random times** is reached only ~**65%**, so the ~1/3 misses run to the stop/cap → the null **nets negative**
(−0.09…−0.18) while real **nets positive** (+0.07…+0.16). Entering at a genuine RSI extreme is what makes the
target get hit. The verdict is **robust to the matched-distance choice**: the realized-capture null (nearer
~0.36-ATR target) also nets negative and is beaten 6/6. EXP-089's 4h dead-by-absence is, on these cells, a
metric-specific false negative of the ~3-bar MFE_med statistic.

## Caveats binding on EXP-092

1. **6 powered cells, not 12.** TEMP-091's "12/12" over-claimed — the readiness gate excludes 7/13 (incl. the
   indices USTEC-4h/US2000-4h). Any 4h carry is at most these 6; the powered set is JPY-cross / EUR-GBP-CHF
   major / gold.
2. **Admission ≠ tradability.** `ADMIT_4H` is a TRAIN-only screen outcome opening the EXP-092/093 sequence; the
   counted-TEST tradability read is EXP-093.
3. **Robust core (favourable):** all 6 members are **mean *and* median net-positive** (net_median
   +0.016…+0.132) — unlike the 1h EXP-091 pass (3/5 median-negative). The whole 6-cell set is a defensible carry.

## Integrity

Determinism replay PASS (EURUSD-4h, GBPUSD-4h; net_ci_low / net_clear / delta_lo / beats_random frame-identical);
headline CSVs SHA-256-pinned. Real OHLC throughout (real touched fill levels + real ATR; no HA/Renko). TRAIN
sub-split only; analysis-TEST + final-30% holdout never sliced (`holdout_untouched=true`). Cost table
Phase-021-local (`D0-amendment-003`, hash `fa7c887…`); shared `xen.capgeo_cost.COST_CONSTANTS` untouched
(Phase-018 integrity). **Process note:** first run HALTed on a RED bite-check (power-leg miscalibration —
planted the sub-threshold single-arm MDE); diagnosed (audit §4), corrected to per-cell power at a fixed 0.10-ATR
reference (+ realized-capture sensitivity, content-keyed readiness cache, exact `Δ_lo(null+g)=Δ_lo(null)+g`
bite-check vectorization — all result-preserving), re-run GREEN. Audit: **PASS** (re-audit; 1 CRITICAL
fixed-and-rerun, 1 Warning closed by the sensitivity).

## Conclusion & next step

**The bare RSI-2 fade's 4h net-of-cost EXIT-RCT edge is the entry signal, not oscillation harvesting — it beats
both the entry-bar-target and realized-capture oscillation nulls 6/6 on the powered cells via a 65%→99%
completion-rate lift.** 4h is **admitted** as a domain expansion (0 new slots). **Next — EXP-092** extends the
planned per-instrument cost-bearing sequence to include the **6 powered 4h cells** (smallest-defensible,
TRAIN-only, 0 reads / 0 slots → hash-pinned candidate set + phase Holm rule); EXP-093 carries the
smallest-defensible 1h∪4h set to a counted TEST read (2/stratum cap; 4h strata currently 0/2). No frozen
constant is re-parameterized; the other deferred levers (15m capture, vol-regime, contrarian, 25/75) each remain
behind their own `D0-amendment-*`.

## Signal-registry disposition

**Registry-relevant — updated in this change.**
- **Multiplicity registry** (Phase 021 batch): EXP-094 row PLANNED → **COMPLETE — `ADMIT_4H`**; the 4h domain
  moves OPENED → **ADMITTED (domain expansion, 0 new slots)**; the 6 powered cells recorded as the EXP-092 carry
  set; the 7 COVERAGE_EXCLUDED 4h cells retained in the file drawer. The binding matched-distance falsification
  statistic is recorded **bite-checked GREEN**.
- **Candidate family** `cf-mr-001.md`: EXP-094 outcome appended; family stays `ADMITTED (BINDING)`; 4h admitted;
  0 additional slots.
- **Test-read ledger:** **no counted read** — EXP-094 reads the TRAIN sub-split only; all 48 strata (incl. the
  4h strata) stay **0/2 open**, holdout sealed (TRAIN-only disclosure, consistent with EXP-090/091).

## Artifacts

- Scope `scope.md` · Analysis plan `analysis-plan.md` · Amendments `D0-amendment-004.md` (4h opened) +
  `D0-amendment-005.md` (binding null corrected)
- Code `code/run_experiment.py` (reuses EXP-090 substrate + `xen.intrabar_fill` / `xen.capgeo_cost` /
  `xen.ass` / `xen.capgeo_substrates` verbatim; content-keyed readiness cache)
- Results `results/` (`readiness_4h.csv`, `screen_per_cell_arm_4h.csv`, `quorum_per_arm_4h.csv`,
  `falsification_paired_delta_4h.csv`, `falsification_quorum.csv`, `positive_control_1h.csv`,
  `cost_decomposition_4h.csv`, `bite_check.json`, `run_metadata.json`)
- Plots `plots/` (net ci_low heatmap, paired-Δ, mechanism quorum, 1h positive control)
- Audit `audit.md` (+ re-audit) · Interpretation `results.md` · Governance `governance/`
