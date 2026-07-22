# Data Analysis: VAL-008 (INFR-010 Phase D — pipeline dry run)

Analyst: data-analyst stage, 2026-07-16. Own code: `analysis_code/{run_gate.py,interrogate.py}`.
Estimands: `xen.nautilus.adjudication_shim` → `xen.adjudication` only. Raw emissions:
`data/nautilus_runs/VAL-008/` (39 cells). Hypothesis under test = the APPARATUS (design §1),
not a market effect.

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (39/39 cells blocking_pass; family completeness 39 cells, emitted == {BTC,ETH,SOL}USDT; no local accounting in code/ or analysis_code/) | **PASS** | `results/estimand_validation.json` (`blocking_pass: true`); reconciliation abs_diff ≤ 1e-12 bps class per cell |
| STUB attestation negative test (must FAIL gate) | **PASS (correctly fails)** | `results/stub_negative_check.json` `blocking_pass: false`, fence reason = Phase-B STUB |
| Provenance trace (verdict-bearing columns ≤ t−1) | **PASS** | table below |
| Leak tripwire collapsed + non-vacuous | **PASS** (after AMENDMENT-4; §3/§5) | LEAK-SHUF collapse 0.977–1.064, LEAK-LAG1 0.996–1.055, all 3 symbols; destroy moves the mean statistic (direction×return alignment), not the P&L multiset |
| Holdout untouched | **PASS** | all reads via `fenced_bar_query(band="TRAIN")`; window ends 2023-12-18 (train_end); holdout_start 2025-01-08; wrapper refuses HOLDOUT unconditionally; fence attestation PINNED sha `35d3375e…` in all 39 emissions |
| Price-primary (Nautilus BacktestNode under fence) | **PASS** | 39 runs via `run_val008.py`; emission contract v1; no Python price backtest anywhere in `code/` |
| T1 spread-scale routing declared | **PASS (declared; moot by design)** | design §12 — no tradability claim exists in scope |
| No experiment-local accounting defs | **PASS** | `check_no_local_accounting` clean on `code/` + `analysis_code/` (in gate artifact) |

Provenance (verdict-bearing columns):

| Column | Inputs & timestamps | ≤ t−1? | Location |
|---|---|---|---|
| BASELINE signal | SMA(20/100) over closes of confirmed bars ≤ t (decision on bar-close event; order fills next bar open) | YES | `code/val008_strategies.py` `MACrossFlip.on_bar` |
| LEAK direction | sign(Open[t+2]−Open[t+1]) — **deliberately acausal** (the plant) | NO — by design | `code/gen_schedules.py` `oracle_dir` |
| LEAK-LAG1 direction | sign(Open[t]−Open[t−1]), confirmed data only | YES | `gen_schedules.py` `lag1_dir` |
| Fills / RealizedBps | engine fills at next-bar open ±1 tick (L1 book synthesis); RealizedBps from `positions_ledger` via shim | YES | verified: EntryFillPrice == next-bar RealOpen ±1 tick across legs |
| Bar marks | fenced catalog bars, ts_event = CloseTime | YES | `run_val008.bar_marks_for` |

## 2. Question list

1. Reconcile per cell? → ANSWERED §1 (39/39, ~1e-12 bps).
2. P&L object == traded object? → ANSWERED: single legs from positions_ledger; estimand per-leg RealizedBps (§3).
3. Per-leg distributions per cell? → ANSWERED §3/§4 table.
4. Episode anatomy? → N/A (single-leg strategy; 28–66 adjacent-slot merged legs disclosed, immaterial).
5. Concentration (minus top-5 legs)? → ANSWERED §3 (LEAK totals stay hugely positive; BASELINE stays ≈0/negative).
6. Stability across time (thirds)? → ANSWERED §3 (LEAK positive in all 9 thirds; destroys ≈0 in all).
7. Per-stratum? → ANSWERED: every number below is per symbol; no pooling anywhere.
8. Occupancy matches story? → ANSWERED: BASELINE 0.9997 (always-in flip — as designed); LEAK 0.029 (1-bar holds at cross cadence — as designed).
9. Physicality vs B&H? → ANSWERED §3 (sanity flags fire on LEAK exactly as they should).
10. Exposure risk? → N/A for apparatus verdict; max 1 unit position by construction.
11. Cost sensitivity? → ANSWERED §5 disclosure (BTC RT spread ≈ 1–2 bps class vs BASELINE −0.9 bps gross: dead at any cost — no tradability claim in scope).
12. Collapse fractions (not binaries)? → ANSWERED §3 per seed per symbol.
13. "What would make the headline wrong?" → ANSWERED: hit-rate recomputed from bar_marks independently of RealizedBps (agrees: LEAK 1.0000); fill prices cross-checked vs staged opens (±1 tick); fixed-point defect probe (§5) — found and repaired.
14. Power? → ANSWERED: LEAK plant 2.9–8.0 bps vs destroy-arm MDE ≈ 0.16–0.4 bps (SE 0.05–0.14, CIs above) — 20–60× MDE as designed; no UNPOWERED strata.

## 3. Evidence FOR the apparatus hypothesis

Per-symbol, per-arm (n ≈ 4.2k legs each; CI = hardened `block_bootstrap_ci`, 5-seed battery):

| Symbol | Arm | mean bps/leg | 95% CI | first-bar hit rate |
|---|---|---|---|---|
| BTC | LEAK | **+2.916** | [+2.753, +3.083] | **1.0000** |
| BTC | LEAK-SHUF s0–s4 | −0.140…+0.08 class | s0 [−0.311, +0.024] | 0.502 |
| BTC | LEAK-LAG1 | −0.065 | [−0.224, +0.099] | 0.495 |
| BTC | BASELINE | −0.945 | [−2.099, +0.249] | 0.494 |
| ETH | LEAK | **+3.122** | [+2.973, +3.275] | **1.0000** |
| ETH | LEAK-LAG1 | −0.173 | [−0.327, −0.017] | 0.495 |
| SOL | LEAK | **+8.010** | [+7.606, +8.428] | **1.0000** |
| SOL | LEAK-LAG1 | +0.029 | [−0.369, +0.416] | 0.510 |
| SOL | BASELINE | −1.049 | [−4.049, +2.035] | 0.493 |

(Full 39-cell table incl. all seeds: `results/analysis_summary.json`.)

1. **Plant visible at design magnitude.** LEAK raw = +2.92/+3.12/+8.01 bps/leg ≈ predicted
   mean|1m o2o| (3.1/3.4/8.7); bootstrap 95% CI excludes zero by >30 SE in all 3 symbols;
   positive in all 9 chronological thirds; total minus top-5 legs still ≥ +11,952 bps — not
   tail-driven.
2. **Future-destroy collapses the plant.** LEAK-SHUF (deranged block permute, seeds
   1000–1004): collapse fraction 0.977–1.064 across all 15 seed×symbol cells; every destroyed
   CI straddles 0. LEAK-LAG1 (causalized same rule): collapse 0.996–1.055 — the stolen
   information dies in exactly one bar, the lookahead fingerprint.
3. **Blind leak-catch protocol: 3/3 vs 0/3.** Rule (predeclared §7): flag iff first-fill-bar
   hit-rate CI-low > 0.55 AND all destroy collapses ≥ 0.9. LEAK flagged in 3/3 symbols
   (hit = 1.0000, Wilson CI-low ≥ 0.999); BASELINE flagged in 0/3 (hit 0.493–0.494, CI-low
   ≈ 0.478).
4. **Physicality layer screams at the plant.** Gate sanity flags on LEAK: Sharpe 47.9,
   225%/yr > 3× B&H vol — "non-physical, interrogate before trusting". Silent on BASELINE.
   The apparatus's independent smell test points at the planted arm unprompted.
5. **Machinery end-to-end.** 39 BacktestNode runs (subprocess-isolated), emission v1 with
   PINNED attestation, gate v2 blocking_pass, STUB negative correctly rejected, schedules
   byte-regenerable (QA-verified), golden trace G1–G3 matched (QA run 1).

## 4. Evidence AGAINST the apparatus hypothesis

1. **First shuffle control shipped defective** (pre-AMENDMENT-4): non-deranged block
   permutation kept E[1 fixed block] of true alignment — seeds 1000/1003 retained 11.1% of
   slots → destroyed-arm residual +0.38 bps (≈6 SE above 0), collapse 0.870 < 0.9. The
   predeclared criterion caught it, the analyst diagnosed the mechanism analytically
   (fixed-point count predicted the residual), and the L-10 amend-in-place cycle repaired it —
   but Phase D's first pass did NOT produce a clean destroy. Recorded as an apparatus finding:
   **permutation destroys must be derangements** (candidate KB lesson).
2. **Fill-timestamp semantics are non-obvious.** Fill ts is stamped at the decision-bar close
   (= wall-clock open of the fill bar); a naive searchsorted on bar closes mis-indexes the
   fill bar by one (analyst's own first hit-rate read was wrong: 0.52 vs true 1.00 —
   caught by cross-checking against RealizedBps sign). Analysts must anchor on
   `EntryFillPrice == next-bar RealOpen ±1 tick`, verified here. Disclosure for the KB.
3. **±1-tick fill deviation** from staged opens (Nautilus L1 book synthesis): ~0.04 bps/leg
   class, immaterial vs the 3–9 bps plant, but a real difference vs naive open-fill
   assumptions (QA run-1 INFO note confirmed at analysis).
4. **ETH LEAK-LAG1 CI marginally negative** ([−0.327, −0.017]): a weak genuine 1m
   anti-momentum residue, not an apparatus defect (`ci_low_seed_range` near boundary; the
   collapse criterion is unaffected). Noted for symmetry — not dressed up as a problem.

## 5. Anomalies & open questions

- BASELINE gross is mildly negative everywhere (−0.5…−1.0 bps/leg, CIs straddle 0 at BTC/ETH/SOL
  widths 1.2–3.0 bps) — WASH per design §8, exactly what a throwaway SMA cross should read.
  No anomaly.
- BASELINE-SHUF occupancy-preserved twins: all 15 cells ≈ 0 (|mean| ≤ 0.7 bps, CIs straddle 0)
  → no hidden leak in the causal path.
- Cost disclosure (§12 routing): BASELINE |gross| 0.5–1.0 bps < 3× RT spread (~1–2 bps BTC
  class) → t1_undecidable YES — moot, no tradability claim permitted.
- Open for operator: (a) adopt "destroy permutations must be deranged" as a KB lesson;
  (b) fill-ts semantics + `dispose_on_completion` + one-node-per-process as Nautilus
  conventions for the KB/skills; (c) multi-instrument single-engine smoke still untested
  (deferred to XENA CAL INFR).

## 6. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: SUPPORTED (apparatus PASS)** — all §7 hard criteria met on the final
  artifact set: gate 39/39 PASS on PINNED attestation; STUB negative fails; planted leak
  caught 3/3 blind, BASELINE clear 0/3; both destroys collapse ≥ 0.97 everywhere; holdout
  untouched; schedules regenerable.
- Driven by: LEAK plant at design magnitude with hit 1.0000 → destroyed to CI-straddling-zero
  under both derangement-shuffle and causalization; blind protocol separation 3/3 vs 0/3;
  gate + STUB negative behaving exactly as specified.
- Honest caveat the operator must weigh: the first-pass shuffle control was defective
  (fixed-point leak-through) and was repaired mid-experiment via the L-10 amend-in-place
  route (AMENDMENT-4, disclosed, contaminated emissions hard-deleted + rerun). The
  criterion itself never moved.
- Would change if: QA run 3 finds the derangement fix or the rerun provenance unsound; or
  the operator rejects the amend-in-place as a goalpost move.
- **Final verdict is the operator's.** Suggested probes: rerun `analysis_code/interrogate.py`
  yourself (deterministic); inspect `results/analysis_summary.json` per-seed collapse rows;
  diff `code/schedules/manifest.json` shas against a fresh `gen_schedules.py` run.
