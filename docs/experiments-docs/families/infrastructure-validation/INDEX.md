# Family Index — infrastructure-validation (Chapter 04)

VAL-/INFR-series items for the Nautilus/Bybit stack (INFR-010 migration onward).
Not a candidate family — no signals, no slots; apparatus and substrate work only.

## ToC

- [VAL-008 — INFR-010 Phase D end-to-end pipeline dry run](#val-008)
- [INFR-014 — Fresh Bybit XENA CAL + universe_selection](#infr-014)
- [INFR-015 — CLS-EPISODE overlap-block binder amendment](#infr-015)

## VAL-008 — INFR-010 Phase D end-to-end pipeline dry run {#val-008}

- **Hypothesis Tests:** apparatus only — does catalog → fenced query → BacktestNode →
  emission v1 (PINNED attestation) → estimand gate v2 → shim/adjudication → leak battery →
  analyst read produce a complete, gate-passing, leak-honest package? Leak battery per L-13:
  planted next-bar-sign oracle (bite plant) must be caught blind; future-destroys must
  collapse it.
- **Scope:** BTC/ETH/SOL USDT perps, 1m, TRAIN 2023-06-01→2023-12-18; SMA(20/100) flip
  throwaway + oracle plant; 39 BacktestNode runs; costless engine; informative-only;
  0 slots / 0 TEST reads.
- **Results / Observations:** gate blocking_pass 39/39 (recon ≤ 7.3e-12 bps); STUB
  attestation correctly fails; LEAK +2.92/+3.12/+8.01 bps/leg (hit 1.0000) destroyed to
  CI-straddling-zero by deranged block shuffle (collapse 0.977–1.064) and causalizing lag
  (0.996–1.055); blind catch 3/3 LEAK vs 0/3 BASELINE; BASELINE wash −0.5…−1.0 bps
  (CIs straddle 0); physicality flags fire on the plant unprompted.
- **Hypothesis-Specific Conclusion:** **operator verdict SUPPORTED / Phase D PASS
  (2026-07-16)** — Chapter 04 unblocked. First-pass shuffle control was defective
  (fixed-point leak-through, collapse 0.870) — caught by the predeclared criterion,
  repaired via L-10 amend-in-place (AMENDMENT-4 derangement, contaminated cells
  hard-deleted + rerun, QA run 3 APPROVE).
- **Hypothesis-Agnostic Observations:** destroy permutations must be derangements; Nautilus
  fill ts = decision-bar close (naive bar indexing off-by-one); node reports need
  `dispose_on_completion=False`; one BacktestNode per process (Rust logging); ~34s per
  288k-bar single-instrument run; multi-instrument single-engine untested (deferred to
  XENA CAL INFR). Report: `python/experiments/VAL-008/report.md`.

## INFR-014 — Fresh Bybit XENA CAL + universe_selection {#infr-014}

- **Hypothesis Tests:** re-measure INFR-009 two-stage CONFIRM form on Bybit/Nautilus under
  net-cost-binding stage-1 (L-26); class nulls CLS-FILTER + CLS-EPISODE; e2e α̂ ≤ 5% +
  no-search cov ≤ 5% for DUAL_CERTIFY; ship `universe_selection` + S1 multi-instr smoke.
- **Scope:** synthetic TRAIN-fence null banks only (n_null design 80 / confirm 200); no live
  family XENA; no TEST/holdout; no ch03 pin load; GAP cost stack disclosed.
- **Results / Observations:** Post-QA re-exec (Issues 9–13): confirm coverage uses confirm
  seeds 93k/94k; CLS-FILTER low CERTIFIED (α̂ 0.045, cov 0.035), high FAIL; verdict
  **LOW_ONLY_CERTIFY**; CLS-EPISODE TERMINAL (α̂ 0.075/0.080); registry written sha256
  `ac8a1eb679e22290d854ad245ef1620f5f8bdb446a5c0166c618d0c292b2da6f` verify green; S1
  ADMITTED A-vs-B bitwise + estimand-v2 PASS → multi_instrument_single_node.
- **Hypothesis-Specific Conclusion:** **operator ACCEPTED partial pin 2026-07-17 (QA run 4
  APPROVE)** — `bybit_pc_frozen_registry.json` sha256 `ac8a1eb6…` is the active binding pin;
  CLS-FILTER certified low-cadence only (XENA-HTFCAP may proceed on CLS-FILTER low);
  CLS-EPISODE TERMINAL (XENA-EPSOSC blocked). Full dual-class / dual-cadence restore not
  available from this bank.
- **Hypothesis-Agnostic Observations:** confirm-bank seed contamination is a hard integrity
  bug class (cov must share confirm bases with α̂); multi-instrument single-node admissible
  for batch topology. Report: `python/experiments/INFR-014/report.md`.

## INFR-015 — CLS-EPISODE overlap-block binder amendment {#infr-015}

- **Hypothesis Tests:** does `episode_overlap_rule_v1` (deterministic B from q90 duration /
  median entry gap, capped n/4) on the stage-2 leg bootstrap restore α̂ ≤ 5% ∧ cov ≤ 5% on
  CLS-EPISODE? Fresh banks (design 95k/96k n=80, confirm 97k/98k n=200, bite 953k/954k).
- **Scope:** single form change vs INFR-014 (harness frozen, generator imported
  byte-identical); synthetic TRAIN-fence banks; no TEST/holdout; CLS-FILTER never touched.
- **Results / Observations:** bite PASS; design cov 0.0375/0.0500; confirm LOW cov 0.095 /
  α̂ 0.135 (27/200, selection_unsafe), HIGH cov 0.050 / α̂ 0.055 (11/200, Wilson
  [0.031, 0.096]) — TERMINAL-2, write policy refused amendment, pin `ac8a1eb6…` unchanged
  (QA re-hash verified). LOW false-certifies concentrate at top-1 n_legs<8 (pass 0.179,
  B=1 ⇒ fix inert); HIGH (n_legs median 261, B median 23) improved vs INFR-014.
- **Hypothesis-Specific Conclusion:** amendment NOT sufficient — **TERMINAL-2, operator
  verdict pending**; XENA-EPSOSC stays blocked.
- **Hypothesis-Agnostic Observations:** overlap correlation real but secondary on LOW; the
  binding CLS-EPISODE defect is small-sample studentized-LCB fragility at n_legs<~16 —
  next form candidates: derived n_legs_floor domain guard, episode-level resampling.
  Report: `python/experiments/INFR-015/report.md`.
