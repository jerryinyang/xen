# VAL-008 — INFR-010 Phase D: end-to-end pipeline dry run on the Nautilus stack

**Type:** VAL / apparatus (pipeline integrity test — NOT a research hypothesis)
**Status:** DESIGN v1 (2026-07-16), quant-designer stage
**Parent:** INFR-010 §6 Phase D. Preconditions met: Phase A (INFR-011 verify PASS), Phase B
(deterministic BacktestNode + emission v1), Phase C (INFR-012 verify PASS, estimand gate v2).
**Disposition class:** informative-only. TRAIN-only. No counted TEST reads. No family action.
Chapter 04 opens only if Phase D passes (operator verdict).

---

## 1. Question + mechanism statement

**Falsifiable question:** Does the new stack (catalog → fenced query → BacktestNode →
emission contract v1 → PINNED fence attestation → estimand gate v2 → shim → adjudication →
leak battery → analyst read) produce a complete, gate-passing, leak-honest evidence package —
i.e. does the future-destroy control collapse a known edge, and is a deliberately planted
lookahead caught by the predeclared detection protocol (test the masking, don't assert it — L-13)?

```
MECHANISM: apparatus test. The "candidate" (SMA cross) is a throwaway vehicle expected ≈0
gross edge at 1m; the PLANTED-LEAK arm injects a known, large, purely-future edge (next-bar
open-to-open sign, ~3-9 bps/leg by construction) whose only information source is data > t.
The pipeline PASSES iff (a) integrity gates pass mechanically, (b) destroys collapse the
planted edge, (c) the blind leak-detection protocol flags LEAK and clears BASELINE.
DERIVED: estimand = per-leg RealizedBps via xen.adjudication (shim) + open-to-open per-bar;
null/destroy = block-permuted direction schedule (seeded battery) + causalizing lag;
horizon = 1-bar hold on the planted object (the lookahead expires in exactly 1 bar — the
destroy scale matches the leak's own horizon); test = collapse-fraction + hit-rate vs 50%
(binomial CI) + block-bootstrap CI from xen.evaluation (L-20 hardened).
```

Not-reused-vehicle note (L-13): estimand/null/horizon above derive from the planted leak's
1-bar mechanism, not from any prior family's stack.

## 2. Object identity declarations

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — single-leg positions (flip legs for BASELINE,
    1-bar legs for LEAK arms); estimand = per-leg RealizedBps from positions_ledger via
    adjudication shim; per-bar open-to-open marks reconcile against legs (L-18 invariant).
  measured conditioning event == traded entry event: YES — SMA(20/100) sign flip on the
    CONFIRMED bar close at t; capital commits via MARKET order filled at bar t+1 open. The
    leak-detection read conditions on exactly the fill bar (first-bar o2o return).
  effect-splitting windows non-overlapping: N/A — single effect per arm. LEAK hold = 1 bar;
    adjacent cross slots exist (min spacing 1 bar; 52/43/58 adjacent slots BTC/ETH/SOL) —
    the per-bar target construction resolves them deterministically (later slot's direction
    wins; same-direction adjacent slots merge into one ≥2-bar ledger leg). Estimand
    unaffected: legs come from positions_ledger as booked. Median cross spacing ≈ 53 bars
    (mean ≈ 68).
```

## 3. Estimand

- Canonical: `xen.nautilus.adjudication_shim.adjudicate_emission(run_dir)` →
  `xen.adjudication` per-leg `RealizedBps` + per-bar gross; reconciliation invariant must
  hold (estimand gate v2 blocking). No experiment-local accounting
  (`check_no_local_accounting` on `code/` + `analysis_code/`).
- Gate (AMENDMENT-1): `analysis_code/run_gate.py` calls
  `xen.estimand_validation.validate_family("data/nautilus_runs/VAL-008")` (no per-cell
  `--expect` — `_manifest_check` prefers per-cell `metadata["symbol"]`, so a family-level
  expectation fails every single-symbol cell mechanically) and then applies the predeclared
  family completeness check: `n_cells == 39` AND aggregated `manifest.emitted ==
  {BTCUSDT, ETHUSDT, SOLUSDT}`. Top-level `blocking_pass` = family blocking_pass AND that
  completeness check; written to `python/experiments/VAL-008/results/estimand_validation.json`.
  `blocking_pass` required before ANY read. STUB attestation must fail (negative gate check,
  one deliberate stub emission at `data/nautilus_runs/VAL-008-stubcheck/`, outside the
  family root).

## 4. Scope

| Item | Value |
|------|-------|
| Instruments | BTCUSDT, ETHUSDT, SOLUSDT (`{SYM}-LINEAR.BYBIT`, ADMITTED anchors) |
| Data | `data/catalog/` 1m bars via `xen.nautilus.catalog_fence.fenced_bar_query`, band="TRAIN" |
| Window | 2023-06-01T00:00Z → train_end 2023-12-18T00:00Z (~288k 1m bars/symbol, all TRAIN) |
| Fence | manifest sha256 `35d3375ec5ec18b3c6e4c5eec814ade4d492bd60e3fb694fed19e16bc2c00448`; attestation via `fence_attestation_payload` (status=PINNED) |
| Holdout | never queried (wrapper refuses); no TEST band contact |
| Vehicle | SMA(20/100) on 1m closes, confirmed-bar signal (≤ t−1), always-in flip, MARKET at next open, fixed qty, costless engine |
| Warmup | signal valid only after 100 in-window bars (both SMAs full) |
| Emission | contract v1 → `data/nautilus_runs/VAL-008/<SYMBOL>__<ARM>/` (flat — `validate_family` scans immediate subdirs); deterministic event log |
| Complexity budget | 1 in-engine strategy (MACrossFlip) + 1 schedule-executor strategy; 2 stat reads (collapse fraction, hit-rate CI); ≤4 plots |
| Registration | one multiplicity-registry row: VAL-008 apparatus vehicle, informative-only, no family |

## 5. Arms (per symbol; 13 runs/symbol, 39 total)

| Arm | Runs | Direction source | Hold | Expected gross |
|-----|------|------------------|------|----------------|
| BASELINE | 1 | in-engine SMA(20/100) flip, causal | to next cross (~68 bars med.) | ≈ 0 (throwaway) |
| LEAK | 1 | **planted**: sign of NEXT o2o return, i.e. sign(Open[t+2]−Open[t+1]) known at decision t (oracle schedule) | 1 bar | ≈ mean |1m o2o| ≈ +3.1/+3.4/+8.7 bps/leg (BTC/ETH/SOL), hit ≈ 100% |
| LEAK-SHUF ×5 | 5 seeds | LEAK schedule, directions block-permuted (240-slot blocks, seeds 1000–1004) | 1 bar | ≈ 0 |
| LEAK-LAG1 | 1 | causalized: sign of LAST confirmed o2o return (≤ t) | 1 bar | ≈ 0 (any residue = genuine 1m momentum, disclosed) |
| BASELINE-SHUF ×5 | 5 seeds | BASELINE signal series block-permuted (240-bar blocks, seeds 2000–2004) | flip occupancy preserved | ≈ 0; surviving edge ⇒ leak in baseline ⇒ Phase D FAIL |

Schedule cadence for all LEAK* arms = the symbol's own BASELINE cross timestamps
(cadence-matched; ~4,256/4,286/4,218 events). Schedules precomputed by the runner from the
fenced TRAIN band only, regenerable byte-identically from (seed, bar calendar) — QA
regeneration check (L-19 D1 pattern). Oracle/destroy arms run in-engine through the same
BacktestNode + emission path as BASELINE (the point is to exercise the pipeline, and the
plant must traverse the identical machinery it is meant to catch).

## 6. Control validity proofs

```
CONTROL LEAK-SHUF (future-destroy, the binding tripwire):
  question answered: does breaking signal→future-return alignment collapse a real edge?
  population: same timestamps, same holds, directions block-permuted — DISJOINT information
    (direction independent of forward return by construction); same-cadence/same-occupancy
    so it could show a surviving edge if P&L came from cadence/occupancy, not alignment. # B-1
  bite/MDE: the LEAK arm IS the co-designed plant: known effect ≈ +3.1–8.7 bps/leg at
    n ≈ 4.2k legs; leg SD ≈ 3–9 bps ⇒ SE ≈ 0.05–0.14 bps ⇒ MDE(95%) ≈ 0.1–0.3 bps —
    plant is 20–60× MDE. The destroy CAN be seen to bite.                        # B-5
  non-vacuity: permuting DIRECTIONS (not P&L) changes the mean of direction×return — the
    sufficient statistic of the mean-bps estimand (not a P&L multiset shuffle; L-14/B-6,
    permutation-destroy-mean-invariant memory respected: we permute the causal input).
  expected outcome if apparatus sound: LEAK collapses to ≈0 (fraction ≥ 0.9 each seed);
    if apparatus broken: edge survives permutation.
  disclosure: collapse fraction (destroyed/raw) per seed, per symbol, both arms.   # B-2/L-15
CONTROL LEAK-LAG1 (causalization / lookahead fingerprint):
  question answered: is the arm's edge attributable to future data specifically?
  population: identical rule shape, information set shifted to ≤ t — disjoint info set. # B-1
  bite/MDE: same plant, same n ⇒ same MDE as above.                                # B-5
  non-vacuity: replaces the future sign with the past sign — moves the same mean statistic.
  expected: LEAK edge collapses ≥ 0.9 (the stolen info expires in 1 bar); BASELINE
    unaffected by construction (already causal — LAG1 not run on BASELINE).
  disclosure: collapse fraction per symbol.
CONTROL BASELINE-SHUF (consistency, non-binding on edge size):
  question answered: does the causal vehicle hide a leak? population disjoint as above.
  expected: raw ≈ destroyed ≈ 0 (nothing to collapse — bite is carried by the LEAK plant,
    not this arm; declared to avoid a vacuous-collapse claim).                     # B-1/B-6
  disclosure: raw and destroyed effect + CI per seed.
```

## 7. Leak tripwire (hard)

```
TRIPWIRE: block-permutation of direction schedule (LEAK-SHUF ×5) + causalizing lag (LEAK-LAG1)
  must collapse the planted edge; expected collapse fraction ≥ 0.9 per seed/arm/symbol.
  vacuity check: destroys move direction×return alignment — the exact statistic of the
  mean-bps estimand; plant magnitude 20–60× MDE so a non-collapse is detectable.
```

**Leak-catch protocol (predeclared, run BLIND on BASELINE and LEAK identically):**
for each arm compute (1) first-fill-bar hit rate = P(direction == sign of o2o return of the
fill bar) with exact binomial 95% CI vs 0.5; (2) collapse fraction under its destroy.
**FLAG as leak iff hit-rate CI-low > 0.55 AND destroy collapse ≥ 0.9.**
Phase D integrity requires: LEAK flagged in 3/3 symbols; BASELINE flagged in 0/3.
A BASELINE flag or a LEAK non-flag is a hard Phase D FAIL (apparatus, not disposition).

## 8. Interpretation bands (per symbol stratum; apparatus reads)

```
BANDS (per stratum = symbol × arm):
  APPARATUS-PASS: gate blocking_pass; LEAK raw ≥ +2 bps/leg with ci_low > +1 (plant visible);
                  LEAK-SHUF & LEAK-LAG1 collapse ≥ 0.9; leak-catch 3/3 vs 0/3.
  WASH (BASELINE): |gross| < 2× bootstrap noise scale — expected, reported as A≈0 not refutation.
  ANOMALY: any BASELINE-SHUF seed with |effect| ci_low > 0 → investigate before verdict.
  UNPOWERED: n legs < 500 in any stratum (not expected; all ≈ 4.2k).
POOLED: cross-symbol pooled figures disclosure-only (L-03).
```

No auto-verdict: the operator reads the evidence package and rules Phase D PASS/FAIL.

## 9. Power statement

```
POWER: legs per stratum ≈ 4,256 (BTC) / 4,286 (ETH) / 4,218 (SOL) per arm.
  LEAK arms: leg SD ≈ mean|1m o2o| ≈ 3–9 bps ⇒ MDE(95%) ≈ 0.1–0.3 bps vs plant 3.1–8.7 bps.
  BASELINE: hold ≈ 68 bars ⇒ leg SD ≈ 25–70 bps ⇒ MDE ≈ 0.8–2.2 bps (adequate for the
  WASH/ANOMALY read; no tradability claim made).
  strata predeclared UNPOWERED: none.
```

## 10. Golden trace (QA diffs vs emission; designer-computed from TRAIN staging bars)

BTCUSDT BASELINE, window start 2023-06-01. SMA(20/100) on 1m closes, signal on confirmed
bar close t, MARKET fill at next bar open (bar opening at that CloseTime):

| # | Cross bar CloseTime (UTC) | New sig | Expected fill time | Expected fill ≈ next Open |
|---|---------------------------|---------|--------------------|---------------------------|
| G1 | 2023-06-01 04:21:00 | +1 (long) | first bar opening ≥ 04:21 | 26766.5 |
| G2 | 2023-06-01 06:39:00 | −1 (flip short) | 06:39 | 26834.5 |
| G3 | 2023-06-01 07:35:00 | +1 (flip long) | 07:35 | 26827.4 |

(SMA values at G1: fast 26775.245 / slow 26775.075; G2: 26829.060/26829.686; G3:
26820.680/26820.185 — hand-recomputable from the staging parquet.) Engine fill price may
differ from the staging `Open` only by tick-size quantization; timestamps must match exactly.
LEAK golden check: for the same three slots, LEAK direction must equal sign(Open[t+2]−Open[t+1])
from the bar series — QA recomputes from data, developer must not generate these.

## 11. Integrity vs informative split

```
HARD (block): estimand gate v2 blocking_pass on PINNED attestation (+ STUB negative test
  must FAIL the gate); tripwire collapse per §7; leak-catch 3/3 & 0/3 per §7; holdout
  untouched; schedules regenerate byte-identical from seeds; check_no_local_accounting clean.
INFORMATIVE (operator judges): all effect sizes, CIs, collapse fractions, cost disclosure,
  BASELINE wash read, any ANOMALY note. No auto-verdict thresholds beyond the apparatus
  integrity criteria above.
```

## 12. T1 spread-scale routing (declared for completeness)

```
SPREAD-SCALE-ROUTING:
  estimated_rt_spread_bps: from per-symbol SpreadBps series via
    xen.evaluation.t1_round_trip_spread_bps (analysis-stage disclosure; BTC ≈ 1–2 bps class)
  gross_edge_bps: BASELINE ≈ 0; LEAK ≈ 3–9 (synthetic, non-tradable by construction)
  t1_undecidable: YES for BASELINE (|gross| < 3× rt spread) — moot: NO tradability claim
    exists or may be made in VAL-008; disposition is apparatus-only. Routing rule exercised
    at analysis as a disclosure to prove the code path runs.
```

### Amendment ledger (L-23; all pre-measurement, 2026-07-16, QA run-1 findings)

```
AMENDMENT-1: gate invocation → analysis_code/run_gate.py (validate_family without per-cell
  --expect + predeclared family completeness check n_cells==39 & emitted=={BTC,ETH,SOL}USDT)
  — DIRECTION: NEUTRAL (fixes a mechanically-broken invocation; check content unchanged)
AMENDMENT-2: shuffle seeds documented as 1000–1004 (LEAK-SHUF) / 2000–2004 (BASELINE-SHUF),
  matching code + schedules/manifest.json — DIRECTION: NEUTRAL (labelling only)
AMENDMENT-3: §2 overlap statement corrected (adjacent slots exist, deterministic resolution,
  merged same-direction legs); median spacing 53 bars — DIRECTION: NEUTRAL (description only)
  running count: 0 looser / 0 tighter / 3 neutral — no gate-set change; no false-qualifier
  re-derivation needed (no qualification gates exist in this apparatus design).
AMENDMENT-4 (2026-07-16, post-first-measurement, L-10 amend-in-place): block permutation →
  DERANGEMENT (resample until no block maps to itself). Defect found at analysis: plain
  permutation keeps E[1 fixed block] ≈ 5.6–11.1% of slots at TRUE alignment (verified:
  seeds 1000/1003 had 2 fixed blocks; destroyed-arm residual +0.38 bps = predicted leak-through,
  collapse 0.87 vs ≥0.9 criterion). The criterion is UNCHANGED; the control is repaired to
  match its own declared intent ("direction independent of forward return by construction" —
  false at fixed points). Contaminated *-SHUF emissions hard-deleted + rerun. DIRECTION:
  NEUTRAL on the criterion; disclosed openly — makes the collapse criterion reachable, which
  is the control behaving as designed, not a goalpost move. LAG1 arm untouched (clean).
  running count: 0 looser / 0 tighter / 4 neutral.
```

§9 CONVERSION-PIN: N/A (no screen-derived effect cited). §11 L-22 spread verdict leg: N/A
(no SUPPORTED band exists in this design). §13 (L-24): battery here is apparatus (5 seeds,
disclosure-only), not an eligibility gate — the L-19 ≥25-seed rule binds kill-tests of
research candidates, not this plant demonstration; deviation declared openly here for QA.
Amendments: see ledger above (4 NEUTRAL).

## 13. Artifacts + stage plan

```
1 design.md (this)            → QA pre-exec (fresh subagent, append-only qa-review.md)
2 code/ (developer)           → MACrossFlip strategy, ScheduleExecutor, schedule generator,
                                runner (BacktestNode, fenced queries, emission v1 PINNED)
3 execute (operator-approved via Phase D invocation) → data/nautilus_runs/VAL-008/…
4 results/estimand_validation.json (blocking) + results/stub_negative_check.json
5 analysis_code/ + analysis.md (data-analyst: evidence for+against, leak-catch protocol,
  collapse fractions, recommended verdict only)
6 OPERATOR verdict → report.md (documenter) + INDEX rows
```
