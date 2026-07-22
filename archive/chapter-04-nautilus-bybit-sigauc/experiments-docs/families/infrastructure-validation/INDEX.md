# Family Index — infrastructure-validation (Chapter 04)

VAL-/INFR-series items for the Nautilus/Bybit stack (INFR-010 migration onward).
Not a candidate family — no signals, no slots; apparatus and substrate work only.

## ToC

- [VAL-008 — INFR-010 Phase D end-to-end pipeline dry run](#val-008)
- [INFR-014 — Fresh Bybit XENA CAL + universe_selection](#infr-014)
- [INFR-015 — CLS-EPISODE overlap-block binder amendment](#infr-015)
- [INFR-018 — CF-SIGAUC-001 Stage I instrument build + freeze](#infr-018)
- [INFR-020 — Multi-timeframe signed-bar apparatus](#infr-020)

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
- **Hypothesis-Specific Conclusion:** cycle 1 amendment NOT sufficient — TERMINAL-2,
  operator-approved. **AMENDMENT-4** (operator-directed, 2026-07-18): derived
  `n_legs_floor` F*=16 atop kept blocks, fresh banks 99k–102k/955k–956k → confirm LOW
  **CERTIFIED** (cov 0.025, α̂ 0.030, ood 0.75), HIGH FAIL_COV (0.060) →
  **LOW_ONLY_CERTIFY; pin sha `abbb1842…` (supersedes `ac8a1eb6…`, CLS-FILTER
  canonical-identical) — operator ACCEPTED 2026-07-18** after QA run 6 adversarial audit
  (CERTIFICATION SOUND; residual 3-cycle multiplicity priced: true α plausibly ≤~0.06;
  4th CLS-EPISODE cycle requires family-wise correction or doubled confirm bank).
- **Hypothesis-Agnostic Observations:** overlap correlation real but secondary on LOW; the
  binding CLS-EPISODE defect was small-sample studentized-LCB fragility at n_legs<~16 —
  proven by the monotone floor curve (cov 0.138→0.050 as F 0→16). Domain floors trade FPR
  for reachability (LOW ood 0.75): calibrated certification ≠ reachable certification —
  XENA designs must budget expected leg counts vs F*. Fallbacks if pin rejected: episode
  resampling; generator realism. Report: `python/experiments/INFR-015/report.md`.

## INFR-018 — CF-SIGAUC-001 Stage I instrument build + freeze {#infr-018}

- **Hypothesis Tests:** Stage I only — freeze a valid session anchor (HYP-I2), A6
  acceptance discriminator (HYP-I3), and profile/class instruments (HYP-I4); integrity
  tripwires must collapse real constructions and fire on deliberate leak plants.
- **Scope:** DESIGN select + CONFIRM train-internal; online top-20 panel (~140 symbols /
  609 DESIGN days); inherits INFR-017 baselines `1b7244c8…` / pins `e3b9fd9b…`; no P&L;
  0 TEST / holdout sealed.
- **Results / Observations:** Freezes: **A-USOPEN×L15**, **D4-t50-w30 δ=0**, kernel
  **K-UNIFORM** calibrated; registry `pin_sha256 5c386984…`. I2 shift survives=false
  (cf≈−41.7); I3 path-swap survives=false (cf≈0.037); both leak plants survive. I3
  winner band SUGGESTIVE (S≈0.75) — value label only. Spread regime UNAVAILABLE.
- **Hypothesis-Specific Conclusion:** **operator COMPLETE / registry accepted 2026-07-21**
  (QA run 8 APPROVE after 7 REVISE rounds). Instrument set ready for SPDR-007; family
  status unchanged (REGISTERED). Not evidence of edge.
- **Hypothesis-Agnostic Observations:** path-swap must move the bars the rule reads
  (AMENDMENT-6); bar-frame `session_end` can shadow poke joins; soft-control RNG order is
  load-bearing for bit-stable parallel races. Report: `python/experiments/INFR-018/report.md`.

## INFR-020 — Multi-timeframe signed-bar apparatus {#infr-020}

- **Hypothesis Tests:** apparatus only — can SPDR-009's D1–D4 grid share one causal candidate,
  session, structural-level, and availability definition while reproducing the frozen 1m path?
- **Scope:** DESIGN only; 194 A5-fitted symbols; 1m/5m/15m/1h detection support; 1h/4h session
  framing; count-only censuses; no return, P&L, TEST, holdout, or candidate disposition.
- **Results / Observations:** clean W1→W5 rebuild; full reproduction battery passes; all nine
  artifact hashes match. Coverage medians 0.38505/0.20110/0.08815 at 5m/15m/1h; 0.50-floor
  usable counts 72/47/31. Raw D4 reconciliation: 640 candidates, 43 straddling, 66 IB-self-made,
  43 prior-self-made, 634 measured, 6 no-level. Missing/null formation provenance raises.
- **Hypothesis-Specific Conclusion:** **operator COMPLETE / Run-10 pin manifest accepted
  2026-07-22** (`5f170b71…`; QA Runs 1–9 REVISE → Run 10 APPROVE). SPDR-009 implementation is
  unblocked; this is not evidence of an edge.
- **Hypothesis-Agnostic Observations:** level formation time is part of object identity; coarse
  pairs measure continuously traded windows and therefore require activity-conditioned wording.
  Report: `python/experiments/INFR-020/report.md`.
