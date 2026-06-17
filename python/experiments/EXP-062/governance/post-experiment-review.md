# Post-Experiment Governance Review — EXP-062 (dual-object re-run)

**Reviewed:** `audit.md`, `results.md`, `report.md`, and the index/registry updates against the bundled
governance constraints and the Phase 015 D0 (incl. `D0-amendment-001-dual-parallel-substrate.md`).
**Date:** 2026-06-17 (supersedes the prior single-object post-experiment review).

## Checks

- **Audit integrity:** `is_defect=false`; determinism 17/17 byte-identical; causality + window invariants
  clean; matched-count per object; **EXP-055 reconciliation 99/99 exact** (native `A_MA_nat` ↔ `ma_seg`,
  `A_ZZ` ↔ `stat`), `reconciliation_mismatch: []`. Audit verdict PASS. PASS.
- **Results faithful to data:** the interpretation reports AVAILABILITY_GOOD by magnitude (91/94
  MOVE_AVAILABLE) **and** the binding caveat that it is **not signal-attributable** (4/99, 2/99; contrast
  median CI_low negative) — i.e. ambient MA-segment-length room, not a harami edge. No over-reading of the
  mechanical AVAILABILITY_GOOD label; the per-object attribution tally is foregrounded. PASS.
- **Dual-object / no pooling (Amendment 001):** both objects reported individually throughout
  (results.md table, report findings, registry card); phase verdict = stronger object; no pooled
  aggregate. PASS.
- **Median binding, mean diagnostic (P3/P4):** median MFE/MAE binding; MAE mean/trim/tail disclosed as the
  L3 input, never a viability gate. PASS.
- **Holdout / gross discipline:** TRAIN-only, 0 candidate slots, 0 TEST reads, holdouts sealed; gross
  throughout; reference band never subtracted. No closure or candidate registration (no early-closure,
  P9). PASS.
- **Registry disposition recorded (Stage 7 requirement):** `multiplicity-registry.md` line 486 advances
  `CF-HA-HARAMI-001/HYP-015 (EXP-062)` SUPERSEDED → **CHARACTERISED (dual-object): AVAILABILITY_GOOD but
  not signal-attributable**; `candidate-families/harami.md` MA-SUBSTRATE L2 card updated; family stays
  REGISTERED/OPEN; `test-read-ledger.md` unchanged (no TEST stratum touched). The item is retained (not
  deleted/renamed). Master + family + python indexes carry the dual-object live status. PASS.
- **Reproducibility note:** the cosmetic `x`-marker Matplotlib warning is fixed in code (colour unchanged);
  no result impact.

The report does not overstate: it explicitly labels availability as ambient and defers tradability. The
disposition is consistent across `report.md`, the registry, and all three indexes.

```text
VERDICT: APPROVE
```
