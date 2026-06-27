# Post-Experiment Governance Review — EXP-063 (dual-object re-run)

**Reviewed:** `audit.md`, `results.md`, `report.md`, and the index/registry updates against the bundled
governance constraints and the Phase 015 D0 (incl. `D0-amendment-001-dual-parallel-substrate.md`).
**Date:** 2026-06-17 (supersedes the prior single-object post-experiment review).

## Checks

- **Audit integrity:** `is_defect=false`; determinism byte-identical; causality clean (incl. the new
  hybrid ZigZag leg); per-object structural invariants pass (V-RAW ≤ V-RR1, V-NONE 0 ADV, weights, matched
  count); **EXP-061 reconciliation 99/99 exact for both objects** (native `V-BENCH` ↔ `M0`, hybrid
  `V-BENCH` ↔ `H0`), `exp061_mismatch: []`; EXP-062 tail cross-check available (disclosed). Audit PASS.
  PASS.
- **Results faithful to data + P4 closure rule:** native EVIDENCE_FOR is reported in its **weak,
  median-preserving** form — the bounded-downside median edge generalises and beats RM, and bounding
  truncates the `/ADV-NONE` catastrophic left tail (raw mean −0.058 → ≈0; trimmed +0.42 → ≈0) — but the
  recovery contrast is **flat (0/99)** and the gross mean is **neutralised, not made positive**. The
  interpretation does **not** over-read the mechanical EVIDENCE_FOR; it states plainly that this is not a
  mean-positive demonstration, and that the MEDIAN_ONLY structural-irrecoverability case is equally not
  met (the negativity is a removable tail). The P4 closure-on-mean rule is honoured (no closure asserted).
  PASS.
- **Hybrid EVIDENCE_AGAINST justified:** median-viable (V-RR1 90/99) but beats-RM 0 → not
  signal-attributable; reported as ambient, consistent with EXP-061. PASS.
- **Dual-object / no pooling (Amendment 001):** both objects reported individually (results table, report,
  registry card); phase verdict = stronger object; no pooled aggregate. PASS.
- **Median binding, mean diagnostic (P3/P4); holdout / gross discipline:** median binding; the full §4 mean
  decomposition is the diagnostic; TRAIN-only, 0 slots, 0 TEST reads, holdouts sealed; gross; no closure or
  candidate registration (P9). PASS.
- **Registry disposition recorded (Stage 7 requirement):** `multiplicity-registry.md` line 487 advances
  `CF-HA-HARAMI-001/HYP-016 (EXP-063)` SUPERSEDED → **CHARACTERISED (dual-object): native EVIDENCE_FOR
  (median edge + bounded ≈0 mean; recovery flat), hybrid EVIDENCE_AGAINST**; `candidate-families/harami.md`
  MA-SUBSTRATE L3 card updated; family stays REGISTERED/OPEN; `test-read-ledger.md` unchanged. Item
  retained. Master + family + python indexes carry the dual-object live status. PASS.
- **Deferred secondaries transparent:** `/STRONG-HA`, MAD, and a separate ZigZag adverse surface explicitly
  not computed (runtime/budget; recorded in `run_metadata.json`) — a disclosed reduction of non-binding
  outputs, not scope creep; no verdict depends on them. PASS.

The report is appropriately hedged (gross mean ≈0; net viability a later phase) and the disposition is
consistent across `report.md`, the registry, and all three indexes.

```text
VERDICT: APPROVE
```
