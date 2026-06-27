# Pre-Execution Governance Review — EXP-082

**Phase:** 018 (CF-CAPGEO-001) · **HYP:** HYP-003 (derive) · **Reviewer:** research-pipeline Stage 4 ·
**Date:** 2026-06-22 · **Artifacts reviewed:** `scope.md`, `analysis-plan.md`,
`code/run_experiment.py`, `python/src/xen/capgeo_exits.py`.

## Signal-registry precondition (programme file-drawer control)

- **Family `CF-CAPGEO-001` is `REGISTERED` / SCREENING-UNBLOCKED** (`candidate-families/cf-capgeo-001.md`);
  Phase 018 OPEN (G0 PASS 2026-06-21). ✓
- **Countable items:** the three derived candidates `D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`,
  `D3-CAPTURE-EFFICIENT` were **registered at the Phase 018 D0** under `/EXIT-DERIVED`
  (`multiplicity-registry.md` Phase 018 batch; D0 §D2). EXP-082 introduces **no new countable item** —
  it locks the parameterization of items already registered. ✓
- **TEST-stratum read:** none. The scope states the ledger tally (all 16×{15m,1h,4h}=48 strata at
  **0/2 counted reads, open**, EURUSD clean-slate per D8) and EXP-082 reads **no market data at all** —
  only EXP-081's TRAIN-derived per-cell summary. **0 counted TEST reads**; ledger unchanged. ✓

## Constraint checks

| Constraint | Verdict | Evidence |
| --- | --- | --- |
| 1. Simplicity over complexity | PASS | Pure deterministic transformation of 184 EXP-081 rows; clear per-row apply of one frozen function; 0 tests, 3 plots, 1 module — the simplest sufficient form. |
| 2. No academic-finance pitfalls | PASS (N/A) | No distributional assumption, no inference. Barriers are empirical quantiles measured by EXP-081. |
| 3. Strict scoping | PASS | Single question (apply frozen D3 rule → triples); boundaries explicit; verdict criteria measurable (all-cells-valid ∧ determinism ∧ harami identity); budget respected (0/0 tests, 3/≤3 plots, 1/≤1 module). No bonus analysis — the structural-guard read is explicitly disclosure-only. |
| 4. Framework principles | PASS | Data-driven (rule consumes measured statistics); non-parametric (quantiles); real-price discipline inherited (EXP-081 ATR-normalized real-price geometry; no returns recomputed); timestamp alignment N/A (no cross-view join). |
| 5. OOS holdout rule | PASS (strongest) | **No market data is opened** — inputs are EXP-081's TRAIN-only summary + metadata. Code asserts `holdout_untouched` and `counted_test_reads==0` on the EXP-081 fingerprint (Step 1). No code path can reach any TEST/holdout row. |
| 6. Look-ahead bias | PASS | The derivation is a pure function of TRAIN-only summary statistics; causal by construction (per-cell, no cross-fold/forward dependency) — which is exactly what lets EXP-083 call it per fold-TRAIN without leakage. |
| 7. Real-/synthetic-price discipline | PASS | No P&L/return/excursion is computed (no exit applied). Barriers carried in EXP-081 ATR units; `H_cap` in domain bars. No HA/Renko/synthetic price anywhere. |
| 8. Safe performance/memory | PASS | 184-row table in, 552-row table out; trivially bounded; plots from the single derived table (no reloads). `tqdm` unnecessary (sub-second). |

## Artifact-specific

- **Scope:** hypothesis falsifiable (well-defined triple per cell, adverse leg always defined);
  success/failure/HALT criteria concrete; data views, candidates, member set, exclusions all explicit;
  holdout exclusion explicit; real-price rule stated; complexity budget realistic. No binding gate
  threshold is introduced (no screen here), so the gate-calibration check is N/A. ✓
- **Analysis plan:** each step has its exact formula + faithfulness check against D0 §D3; the one
  genuinely ambiguous item (D2 "tightened to the dip") is pinned **parameter-free** as
  `min(m_anti, MAE_q90)`, with the simpler "≡ D1" alternative explicitly considered and rejected
  (it would erase D2's distinct function); interpretation guide pre-defined; per-stratum default honored
  (no pooled edge claim — there is no edge); plots purposeful (disclosure of derived definitions);
  budget compliant. ✓
- **Code (`run_experiment.py` + `capgeo_exits.py`):** implements exactly the plan — provenance
  assertion, per-row derivation via the pure function, validity/degeneracy gates, harami-identity
  assertion, byte-identical determinism replay, disclosure-only structural-guard read, D1≡D2 accounting,
  module hash-pin. Type hints + docstrings present; NaN handled explicitly via `math.isfinite`
  (`capgeo_exits.py:_is_finite`); edge cases (degenerate quantile, sub-floor n, `H_cap<1`) gated; pure
  module has **no I/O/globals/side-effects**; experiment script sectioned VAL-001 style; output dirs
  created only in `main()`; concise `logging`; no magic numbers beyond plan-defined `EVENT_FLOOR=30`
  (D9) and the `K_tail`/quantiles inherited from EXP-081. The script consumes only the approved D3-input
  columns (no `ass_*`). ✓
- **Verdict representation (per-stratum doctrine, EXP-076 C1 precedent):** the experiment verdict
  (`DERIVATION_DELIVERED`/`HALT`) is a **process-level** completeness/determinism check, **not** a
  collapsed cross-stratum edge PASS/FAIL. Per-(cell,candidate) `disposition` and `valid` are emitted in
  the 552-row table; no pooled edge statistic is presented as a verdict. Compliant. ✓

## Notes (Info — non-blocking; flagged for documentation/operator visibility)

1. **D2 "tightened to the dip" operationalization.** D0 §D3 leaves "tightened to the dip" in prose.
   The plan freezes it as `S_adv(D2) = min(m_anti, MAE_q90)` when the dip resolves, else `MAE_q90` —
   the only parameter-free, column-computable reading that (i) adds no new constant (D0 "no magic
   numbers"), (ii) reduces to `MAE_q90` when unimodal exactly as D0 states, and (iii) is
   tighter-or-equal to D1. This is an **operationalization of the frozen rule's own wording**, not a new
   degree of freedom, and is consistent with the D9 bite-check disposition that `m_anti` is power-limited
   and predominantly falls back to `MAE_q90`. Verified to keep D1 and D2 **distinct functions** (they
   diverge iff `m_anti > MAE_q90`; unit-checked). Surfaced here so the documenter records it and the
   operator may object at Stage 7/8 if a different intent was meant; no D0-amendment is required because
   no frozen design constant is changed.
2. **Anticipated D1≡D2 numerical coincidence** on the EXP-081 snapshot (`m_anti` resolves in 1/184 and
   below `MAE_q90` there). This is a **disclosed derivation outcome**, accounted explicitly (Step 8),
   and flagged for EXP-083's {candidate × stratum} Holm grid / slot accounting. Not a defect.

## Verdict

```text
VERDICT: APPROVE
```

All constraints pass; no Critical or Warning issues. The two Info notes are transparency flags, fully
documented in the scope and plan, and do not affect correctness, sample membership, denominators,
temporal validity, or the (absent) edge verdict. Proceed to the manual execution gate.
