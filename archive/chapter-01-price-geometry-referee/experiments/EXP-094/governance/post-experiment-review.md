# EXP-094 — Post-Experiment Governance Review (Stage 8)

**Phase 021 · CF-MR-001/HYP-002 · `D0-amendment-004`+`005`.** Consolidated review of `audit.md` (+ re-audit),
`results.md`, `report.md`, and the index/registry updates against the governance constraints.

## Checks

**Verdict forensics present (audit).** PASS. The audit carries: a **per-stratum re-derivation with a masking
check** (all 6 powered cells beat both nulls, homogeneous, drop-one-robust; and the masking correction — 6
powered vs TEMP-091's naive 12, with the unpowered cells incl. USTEC/US2000-4h enumerated and retained); an
explicit **mechanism statement** (reversion-completion hit rate ~65% random → ~99% real, identical
exit/stop/fill/cost); and a **gate-shape check** (the binding matched-distance paired-Δ quorum sees the effect,
and its calibration is the GREEN bite-check). Not a pooled rubber-stamp.

**Verdict-material findings fixed-and-rerun, not down-classified.** PASS. The first run's **CRITICAL**
bite-check RED (verdict-gating) was diagnosed (power-leg miscalibration — planted the sub-threshold single-arm
MDE), **fixed** (per-cell power at a fixed 0.10-ATR reference; exact `Δ_lo(null+g)=Δ_lo(null)+g` vectorization)
and the experiment **re-run** to a GREEN bite-check + binding `ADMIT_4H` — not documented-and-proceeded. The
**Warning** (anti-conservative entry-bar-target distance) was **closed by the realized-capture sensitivity**
(real beats the nearer-distance null 6/6), not merely noted.

**Signal-registry disposition recorded (registry-relevant result).** PASS. `report.md` records it; and in the
same change: the multiplicity-registry Phase-021 batch advances EXP-094 PLANNED → **COMPLETE `ADMIT_4H`** and
the 4h domain OPENED → **ADMITTED (domain expansion, 0 new slots)** with the 7 COVERAGE_EXCLUDED cells retained;
`cf-mr-001.md` gains the EXP-094 ADMITTED outcome (family stays `ADMITTED (BINDING)`, 0 new slots);
`test-read-ledger.md` carries the EXP-094 (and EXP-091) **TRAIN-only disclosure** — **0 counted reads**, all 48
strata (incl. the 6 admitted 4h strata) stay 0/2 open. The new binding statistic is recorded **bite-checked
GREEN**. Indexes (`python/experiments/INDEX.md`, master `INDEX.md` live status + family-detail card) updated.

**Holdout / discipline.** PASS. TRAIN sub-split only (`holdout_untouched=true`); real OHLC; determinism replay
PASS; cost table unchanged (`fa7c887…`, shared `COST_CONSTANTS` not mutated); no candidate slot, 0 counted TEST
reads. No scope expansion beyond `D0-amendment-004`/`005` (operator-ratified); the EXP-092 4h carry is named as
a **future** scope, not performed here.

**Safe-optimization integrity.** PASS. The readiness cache is content-keyed (deterministic; invalidates on any
input change; holdout never read) with provenance in metadata; the bite-check `d+g` grid is an exact algebraic
identity. Neither changes `n_boot`, block length, seeds, denominators, the binding statistic, or sample
membership.

## Verdict

```text
VERDICT: APPROVE
```

EXP-094 is complete and sound: the binding `ADMIT_4H` is FPR-controlled, robust to the null distance, and
mechanistically explained; the one verdict-material finding was fixed-and-rerun; the registry disposition is
fully recorded with the holdout sealed and no read spent. The 4h domain is admitted as a domain expansion (0 new
slots); the 6 powered cells are cleared to carry into the EXP-092 cost-bearing sequence.
