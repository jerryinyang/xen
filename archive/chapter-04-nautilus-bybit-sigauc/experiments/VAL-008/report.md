# VAL-008 Report — INFR-010 Phase D: End-to-End Pipeline Dry Run (Nautilus Stack)

**Type:** VAL / apparatus (pipeline integrity test — no research hypothesis)
**Dates:** designed / executed / closed 2026-07-16
**OPERATOR FINAL VERDICT: SUPPORTED — Phase D PASS (2026-07-16).** Analyst recommendation
was also SUPPORTED (no divergence). **Chapter 04 unblocked** (checkpoint-013 may open).

## 1. Question + mechanism

Does the new stack — catalog → fenced query → BacktestNode → emission contract v1 (PINNED
attestation) → estimand gate v2 → shim → adjudication → leak battery → analyst read —
produce a complete, gate-passing, leak-honest evidence package? Pass = (a) integrity gates
pass mechanically, (b) future-destroys collapse a known planted edge, (c) a blind
leak-detection protocol flags the planted-lookahead arm and clears the causal arm (L-13:
test the masking, don't assert it).

## 2. Scope

- BTCUSDT / ETHUSDT / SOLUSDT (`{SYM}-LINEAR.BYBIT`), 1m bars, TRAIN sub-window
  2023-06-01 → train_end 2023-12-18 (~288k bars/symbol). Holdout never touched.
- Vehicle: SMA(20/100) always-in flip (throwaway). Plant: next-bar-sign oracle
  (sign(Open[t+2]−Open[t+1]) at decision t), 1-bar hold, baseline-cross cadence.
- 39 runs = 3 symbols × {BASELINE, LEAK, LEAK-LAG1, LEAK-SHUF×5, BASELINE-SHUF×5};
  engine costless; disposition informative-only; 0 slots, 0 counted TEST reads.
- Amendments: 4, all NEUTRAL (L-23 ledger in design.md) — incl. AMENDMENT-4 mid-experiment
  control repair (below).

## 3. Method summary

In-engine `MACrossFlip` + `ScheduleExecutor` (precomputed target schedules, byte-regenerable
from seeds — QA-verified sha-identical). Emissions per contract v1 with PINNED fence
attestation (manifest sha `35d3375e…`). Gate: `analysis_code/run_gate.py`
(validate_family + 39-cell/3-symbol completeness + no-local-accounting). Analyst
interrogation from raw emissions via `xen.nautilus.adjudication_shim` only.

## 4. Key evidence (per symbol; n ≈ 4.2k legs/cell; hardened block-bootstrap CIs)

| Read | BTC | ETH | SOL |
|---|---|---|---|
| LEAK raw bps/leg | +2.916 [+2.75,+3.08] | +3.122 [+2.97,+3.28] | +8.010 [+7.61,+8.43] |
| LEAK first-bar hit rate | 1.0000 | 1.0000 | 1.0000 |
| LEAK-SHUF collapse (5 seeds) | 0.997–1.064 | 0.977–1.049 | 1.006–1.023 |
| LEAK-LAG1 collapse | 1.022 | 1.055 | 0.996 |
| BASELINE bps/leg (wash) | −0.945 [−2.10,+0.25] | −0.509 [−1.73,+0.73] | −1.049 [−4.05,+2.04] |
| BASELINE hit rate | 0.4935 | 0.4935 | 0.4925 |
| Blind leak-catch | LEAK flagged / BASELINE clear in **3/3 symbols** | | |

Integrity: gate blocking_pass 39/39 (recon ≤ 7.3e-12 bps); STUB attestation correctly FAILS
the gate; physicality sanity flags fire on LEAK unprompted (Sharpe 47.9, 225%/yr) and stay
silent on BASELINE; LEAK positive in all 9 chronological thirds and after removing top-5
legs; BASELINE-SHUF twins ≈ 0 everywhere (no hidden leak in the causal path).

**Evidence against / caveats (recorded honestly):** (1) first-pass shuffle control was
defective — plain block permutation kept E[1 fixed block] (11.1% of slots on seeds
1000/1003) of TRUE alignment → destroyed-arm residual +0.38 bps, collapse 0.870 < 0.9. The
predeclared criterion caught it; mechanism verified analytically (fixed-point counts
predicted residuals); repaired via L-10 amend-in-place (AMENDMENT-4: derangement; criterion
unchanged; contaminated SHUF emissions hard-deleted + rerun; QA run 3 verified fix,
schedule regeneration, and change surface). (2) ETH LEAK-LAG1 CI marginally negative
([−0.33,−0.02]) — weak genuine 1m anti-momentum residue, not a defect. (3) ±1-tick fill
deviation vs staged opens (~0.04 bps/leg) — immaterial here, real for future designs.

## 5. Stack findings (candidate KB lessons — codify at checkpoint-013, operator-signed)

1. **Destroy permutations must be derangements** — a plain permutation leaks plant/true
   signal through fixed points (measured: 11.1% alignment → collapse 0.87).
2. **Nautilus fill-ts semantics**: fill timestamp = decision-bar close (= wall-clock open of
   fill bar); naive searchsorted on bar closes mis-indexes the fill bar by one. Anchor on
   `EntryFillPrice == next-bar RealOpen ±1 tick`.
3. **`BacktestRunConfig(dispose_on_completion=False)`** required for node-path report
   capture (default silently empties reports; Phase B never exercised this path).
4. **One BacktestNode per process** (Rust logging init panic on second node) — runner uses
   subprocess-per-cell.
5. Multi-instrument single-engine run still untested — defer to the XENA CAL INFR.

## 6. Verdict record

- Analyst recommendation: SUPPORTED (apparatus PASS) — `analysis.md` §6.
- **Operator final verdict: SUPPORTED / Phase D PASS, 2026-07-16** (option 1: document +
  open Chapter 04 at checkpoint-013). Operator accepted the AMENDMENT-4 amend-in-place.
- QA: run 1 REVISE (3 findings, fixed as NEUTRAL amendments); run 2 APPROVE; run 3 APPROVE
  (amended state, independent recomputation of headline numbers).

## 7. Registry disposition

`multiplicity-registry.md` Chapter 04 · VAL-008 row: apparatus test COMPLETE, SUPPORTED /
Phase D PASS; 0 slots, 0 counted TEST reads, TRAIN-only, holdout sealed. No family opened,
no family status touched. Test-read ledger: no entries (no TEST contact).

## 8. Artifacts

[design.md](design.md) · [qa-review.md](qa-review.md) (3 runs) · [analysis.md](analysis.md) ·
[code/](code/) (strategies, schedule generator + manifest, runner, clause_map) ·
[analysis_code/](analysis_code/) (gate wrapper, interrogation) ·
[results/](results/) (estimand_validation.json, stub_negative_check.json,
analysis_summary.json, run_log.jsonl) · emissions `data/nautilus_runs/VAL-008/` (39 cells) +
`VAL-008-stubcheck/`.

## 9. Follow-ups (separate future work)

- Checkpoint-013: ratify §5 lessons into KB/skills; open Chapter 04 research.
- XENA CAL INFR (fresh registry calibration on Bybit universe — INFR-010 R4) including a
  multi-instrument engine smoke.
- Optional: patch `xen.nautilus.backtest_util.run_ma_cross_node` report capture
  (`dispose_on_completion`) — currently only misleading in smokes.
