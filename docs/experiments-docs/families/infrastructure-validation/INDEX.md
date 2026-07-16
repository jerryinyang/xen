# Family Index — infrastructure-validation (Chapter 04)

VAL-/INFR-series items for the Nautilus/Bybit stack (INFR-010 migration onward).
Not a candidate family — no signals, no slots; apparatus and substrate work only.

## ToC

- [VAL-008 — INFR-010 Phase D end-to-end pipeline dry run](#val-008)

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
