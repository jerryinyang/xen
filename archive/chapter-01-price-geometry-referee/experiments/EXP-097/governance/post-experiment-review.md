# EXP-097 — Post-Experiment Governance Review (Stage 8)

**Experiment:** EXP-097 — Global-Holdout Release: One-Shot OOS-Final Confirmation (RSI-2 Fade Deployment Portfolio)
**Phase:** 022 · **Family/HYP:** `CF-MR-001`/`HYP-003` · **Date:** 2026-06-25
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`,
`docs/experiments-docs/INDEX.md`, `docs/experiments-docs/families/cf-mr-001/INDEX.md`,
`docs/signal-registry/{candidate-families/cf-mr-001.md, multiplicity-registry.md, test-read-ledger.md}` ·
**Against:** the bundled governance constraints + the G-022a freeze.

---

## Verdict

```text
VERDICT: APPROVE
```

The result is the frozen-rule read of the single sanctioned global-holdout shot; the audit carried full verdict
forensics; the signal-registry disposition is complete and consistent across all files. No Critical or Warning
issues; no goalpost movement.

---

## Verdict-forensics confirmation (the central Stage-8 check)

The audit (`audit.md`) carries all four required elements, and they hold up on review:

- **Per-stratum re-derivation + masking check.** The pooled headline (B Sharpe LB 4.762) is affirmatively shown
  **not** to mask heterogeneity: 7/8 cells carry a positive holdout net ci_low; the single net-negative cell
  (EURJPY-4h) is the pre-flagged NOISE_DEGRADED smallest contributor (dropping it improves the book). The verdict
  is broad-based, not one-cell-driven, and no broken cell is hidden. ✓
- **Mechanism statement.** The audit explains *why*: the ~6.6 Sharpe is structural (diversified ERC, in-family with
  the analysis-set LB the band was calibrated against — not a bug); the portfolio did not decay because per-cell
  decay was heterogeneous and offsetting; B≫A because the circuit breaker de-allocated the fragile 1h cells. This
  is a genuine mechanism, not a restatement that the number cleared the bar. ✓
- **Gate-shape check.** The binding gate (Sharpe LB + Calmar LB) matches the effect's location/downside shape; no
  blindness to tail/bimodal structure. ✓
- **Numeric reproduction.** The headline was independently re-derived bit-for-bit from the saved return series — a
  necessary check, present, and explicitly treated as not sufficient on its own. ✓

## Materiality / blocking authority

The audit found **0 Critical, 0 Warning** findings; all 4 Info notes carry explicit materiality reasoning showing
they cannot move a verdict-bearing number (the B Sharpe LB, Calmar LB, or the binding stratum). No verdict-material
finding was down-classified. Correctly, **no fix + rerun was forced** — and, per one-shot holdout discipline, none
is permitted (a confound found after the read is a permanent caveat, not a re-read). Consistent with the materiality
gate.

## Frozen-rule / OOS-holdout discipline — PASS

- The read reads **exactly** the G-022a-frozen set (carry-8), construction (binding-v2 ERC + intra-1h MTM), primary
  (B), bands (A 1.75 / B 2.00), and rule; nothing data-derived from the holdout. No goalpost moved after the read.
- The final-30% global holdout was loaded **once, here** (`global_holdout_shot_spent=true`,
  `holdout_first_touch=EXP-097`); the binding metric is restricted to the holdout region (`epoch ≥ H`), warmup is
  past-only; causal-weight + causal-fill assertions exercised in the holdout region and pass.

## Signal-registry disposition — PASS (registry-relevant, complete)

Recorded in the same change as the result:

- `candidate-families/cf-mr-001.md` — status advanced to **`DEPLOYABLE` (G-022 DEPLOYABLE_CONFIRMED)**; EXP-097
  outcome section added.
- `multiplicity-registry.md` — EXP-097 row updated to **COMPLETE / holdout shot SPENT / DEPLOYABLE_CONFIRMED**.
- `test-read-ledger.md` — the **single sanctioned global-holdout-governance event** entered; analysis-TEST ledger
  untouched (11 carried strata stay 1/2, other 37 stay 0/2); `counted_test_reads=0`, `candidate_slots=0`;
  non-repeatable, non-upgradable.
- Indexes updated: `python/experiments/INDEX.md` (EXP-097 row), master `docs/experiments-docs/INDEX.md` (CF-MR-001
  family row + Phase 022 checkpoint live-status), family detail INDEX (summary row + detailed card + G-022 gate row
  + header status). No per-experiment card was added to the master.

## Read accounting — PASS, ratified

One holdout-governance event (à la EXP-032); A+B from one materialization = one read (operator decision
2026-06-25); terminal keys off B (no OR-multiplicity); 0 counted analysis-TEST reads; 0 candidate slots.

## Conclusion

EXP-097 is complete and sound: `DEPLOYABLE_CONFIRMED`, audit PASS with full verdict forensics, registry disposition
complete. The bare RSI-2 fade is the programme's first deployment-grade price strategy. The terminal **G-022**
adjudication and the Phase 022 retrospective are the remaining checkpoint-level governance steps (outside this
experiment's pipeline). **APPROVE.**
