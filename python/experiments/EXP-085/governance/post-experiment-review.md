# Post-Experiment Governance Review — EXP-085

**Experiment:** EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate on the EXP-083 Valid-Candidate Set
(CF-CAPGEO-001 Phase 018 / HYP-004 cost read-gate)
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, `python/experiments/INDEX.md`,
`docs/experiments-docs/families/cf-capgeo-001/INDEX.md`, `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/{multiplicity-registry.md, test-read-ledger.md, candidate-families/cf-capgeo-001.md}`
**Date:** 2026-06-22

---

## Governance checks

| Check | Verdict | Evidence |
|---|---|---|
| **Audit carried verdict forensics** | PASS | `audit.md` has a per-stratum re-derivation table, an explicit masking check, a mechanism statement, and a gate-shape check — run autonomously, not contingent on the result being questioned. |
| **Per-stratum masking check (binding)** | PASS | The audit independently re-derived the verdict per stratum and **affirmatively flagged** that the pooled `NET_SURVIVES` (21/26) masks heterogeneity: all 21 NET_POS are S2-DEFERRED low-n 4h cells; the only S2-PASS well-powered stratum (AUDUSD-1h, n=988) is NET_INCONCLUSIVE. The pooled headline is explicitly labelled a disclosure, not a clean signal. |
| **Gate-shape check** | PASS | The audit assessed whether the binding exp∧median gate can see the effect's shape — concluded it is appropriately tail-aware (mean leg incorporates the persisting catastrophe tail), and that the limitation is power/separability adjudication (S2 deferred at n<120), not gate-shape blindness. |
| **No verdict-material finding down-classified** | PASS | 0 Critical findings. The 2 Warnings (per-stratum masking; small-n expectancy CI under-coverage) are each shown unable to move any verdict-bearing number — the masking is faithful to the predeclared rule (per-cell verdicts independently reproduced), and the small-n expectancy concern is overridden by the conservative both-legs rule (NET_POS cells also clear the robust median leg). Materiality reasoning is stated per finding. No fix-and-rerun was owed and skipped. |
| **Per-stratum verdict representation (code)** | PASS | The binding verdict is emitted per survivor row; the experiment verdict is the OR over `NET_POS`, not a collapsed `.all()`/pooled flag. Companion excess + any aggregate are non-binding. |
| **Numeric reproduction** | PASS | The audit reproduced two survivors (one NET_POS, one NET_INCONCLUSIVE) from raw data to full float precision, manually (not via the tested `event_costs`), and verified the three reconciliation guards (sha, gross 1e-9, exit-mirror) are real. |
| **Results honesty / no overreach** | PASS | `results.md` and `report.md` lead with `NET_SURVIVES` (predeclared, rule-correct) but immediately foreground the per-stratum masking, state "authorizes nothing — read-gate input to G-018", quantify CIs and n per stratum, and recommend follow-ups only as new scopes / an operator G-018 decision input. |
| **Holdout / reads / slots** | PASS | `holdout_untouched=true`, `test_stratum_touched=false`, `counted_test_reads=0`, `candidate_slots=0`. TRAIN-only. |
| **Gate-threshold calibration** | PASS | Binding gate is `CI_low_1s > 0` (no magic threshold); cost constants are data-anchored (EXP-030/034) and operator-ratified at Stage 4 (disclosed in `run_metadata.json`). |
| **Complexity budget** | PASS | 2 stat-method families (reused), 3 plots, 1 new module — within budget. |

## Signal-registry disposition (confirmed recorded in the same change)

- **Result is registry-relevant** — disposition recorded:
  - `multiplicity-registry.md` — EXP-085 row advanced to **COMPLETE — `NET_SURVIVES` (per-stratum-masked)**;
    item retained; 0 slots / 0 reads. EXP-084 row updated: leg (a) `NET_SURVIVES` satisfied, still gated on
    leg (b) operator ratification; read-eligible set flagged shape-unadjudicated low-n only.
  - `test-read-ledger.md` — **unchanged** (TRAIN-only disclosure); an EXP-085 disclosure paragraph appended per
    the EXP-074/075/080/081/082/083 precedent; all 48 strata stay 0/2 open.
  - `candidate-families/cf-capgeo-001.md` — HYP-004 line updated with the EXP-085 read-gate outcome; family
    stays `REGISTERED`/SCREENING; G-018 decision pending operator ratification.
  - `report.md` carries an explicit **Registry Disposition** section listing the above.

## Index updates (confirmed)

- `python/experiments/INDEX.md` — EXP-085 row added.
- `docs/experiments-docs/families/cf-capgeo-001/INDEX.md` — detailed EXP-085 card added (anchor
  `exp-085-card`), summary bullet advanced to COMPLETE, EXP-084b bullet de-duplicated and updated.
- `docs/experiments-docs/INDEX.md` (master) — CF-CAPGEO-001 Family Indexes row + the Phase 018 checkpoint
  status line updated to EXP-085 COMPLETE / `NET_SURVIVES` (per-stratum-masked) / G-018 pending. No
  per-experiment card added to the master (correctly lives in the family index).

---

```text
VERDICT: APPROVE
```

The implementation is correct and numerically reproduced; the audit ran full verdict forensics and correctly
foregrounded the per-stratum masking that inverts the pooled headline; the documentation reports the verdict
honestly per stratum and the registry disposition is recorded. No verdict-material finding remains open. The
G-018 read decision now passes to the operator (this experiment authorizes nothing).
