# VAL-005 — 5-Year 1-Minute Dataset Validation (INFR-003 Gate)

**Status:** **SCOPED — PENDING (gated on INFR-003 collection).** Validation experiment for the
INFR-003 5-year data upgrade; not a market hypothesis. Governed as VAL-class
(operator-reviewed, outside the 8-stage pipeline), mirroring VAL-001 (temporal integrity) and
VAL-003 (admission / negative controls) on the re-collected dataset.
**Date scoped:** 2026-06-20.
**Governing checkpoint:** `docs/experiments-docs/checkpoints/2026-06-20-INFR-003-five-year-data-upgrade/design.md`.
**Gates:** Phase 018 (CF-CAPGEO-001) is hard-blocked until VAL-005 PASS.

---

> **Universe note (operator ratification, 2026-06-21):** DE30 is **dropped** from the INFR-003
> collection (broker m1 history ended 2026-01-16 — stale; see INFR-003 design §3.1). VAL-005
> validates the **16** collected instruments (VAL-003 universe minus DE30). References to "all 17"
> below read as **16** for this build.

## 1. Question

> Does the re-collected ~5-year 1-minute dataset (16 instruments) preserve temporal integrity,
> detect all injected negative controls, meet coverage/completeness expectations, correctly seal the
> new final-30% holdout per file at first touch, and reproduce its derived views deterministically —
> i.e., is it admissible as the canonical dataset for CF-CAPGEO-001?

This is a data-admission validation, not an edge claim. No candidate, no slot, no edge inference.

## 2. Scope

- **Instruments:** the 16 INFR-003-collected (VAL-003 universe minus the dropped DE30; 5-year m1
  files produced by INFR-003).
- **Views:** 1-minute base bars; 15m/1h/4h resamples via `bar_aggregator` (clock-aligned,
  `min_coverage=0.90`). (Chart-type views out of VAL-005 scope unless CF-CAPGEO-001 later requires.)
- **Slice:** validation reads **first-70% analysis rows only**; the new final-30% holdout is sealed
  at first touch and never inspected.
- **Reuse:** the VAL-001 rev. 3 temporal-integrity suite and the VAL-003 negative-control battery,
  unchanged. New code only for 5-year-specific coverage/span accounting.

## 3. Acceptance gates (binding; mirrors INFR-003 §5)

| Gate | Criterion | Method |
| --- | --- | --- |
| **G1 — Temporal integrity** | No future timestamps; strictly monotonic `CloseTime` per file; no cross-view (timebar ↔ resample) misalignment; head/mid/tail prefix-stability probes show no structural look-ahead. | VAL-001 rev. 3 suite, per instrument. |
| **G2 — Negative controls** | All injected controls (gap, duplicate, reorder, future-leak, sign-flip) detected; **0 FAIL / 0 INCONCLUSIVE**. | VAL-003 battery; 24/24 detection target. |
| **G3 — Coverage / completeness** | Per-instrument row count, span, and gap profile within broker-availability expectations; per-instrument truncations (DE30, short-history symbols) disclosed, boundaries derived from each file's own timeline. | Span/gap report per instrument. |
| **G4 — Holdout seal** | Final-30% sealed per file at first touch (in-robot self-guard + Python harness re-assertion); **0 holdout rows read** at validation. | Seal manifest + harness assertion. |
| **G5 — Determinism** | Derived resamples reproduce byte-identically on a second pass; run config recorded. | Two-pass byte compare. |

A FAIL on any gate blocks Phase 018; fix collection/derivation and re-validate.

## 4. Outputs / deliverables

- `python/experiments/VAL-005/results/` — per-instrument integrity, negative-control, coverage,
  seal, and determinism tables; overall verdict.
- `python/experiments/VAL-005/report.md` — admission summary + per-instrument truncation disclosures.
- Compact row in `python/experiments/INDEX.md`; card/row in the infrastructure-validation family
  index (currently listed PENDING).
- On PASS: re-materialize `docs/signal-registry/test-read-ledger.md` on the new strata (all 0 counted
  reads; old-dataset ledger retained as history); update `docs/references/dataset-reference.md`
  (new spans, disclosures); flip the master-index Infrastructure Tasks INFR-003 row to COMPLETE.

## 5. Success / failure / inconclusive criteria

- **PASS (ADMITTED):** G1–G5 all pass → dataset is canonical for CF-CAPGEO-001; Phase 018 unblocked
  (with G-017 PASS).
- **FAIL:** any gate fails → dataset not admitted; INFR-003 returns to collection/derivation fix.
- **INCONCLUSIVE:** a per-instrument coverage shortfall that is disclosed-but-not-disqualifying (e.g.
  DE30 broker truncation) → instrument admitted with a carried disclosure, not a global FAIL, per the
  INFR-002/VAL-003 precedent.

## 6. Discipline

- Holdout never loaded or inspected; validation reads first-70% only.
- Deterministic (recorded run config / seeds); real timestamps; no bar-index alignment across views.
- No edge or candidate inference of any kind — this is data admission only.
