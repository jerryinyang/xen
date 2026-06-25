# EXP-093 — Post-Experiment Governance Review

**Phase:** 021 (CF-MR-001 batch 2) · **Family / HYP:** `CF-MR-001` / `HYP-002` · **Date:** 2026-06-24
**Artifacts reviewed:** `audit.md` · `results.md` · `report.md` · `python/experiments/INDEX.md` ·
`docs/experiments-docs/families/cf-mr-001/INDEX.md` · `docs/experiments-docs/INDEX.md` ·
`docs/signal-registry/` (test-read-ledger, candidate-families/cf-mr-001, multiplicity-registry).
**Against:** governance-constraints.md (post-experiment checks).

---

## Decision

```
VERDICT: APPROVE
```

EXP-093 — the phase's one-shot counted-TEST confirmation — is complete and trustworthy. The verdict
(`TEST_CONFIRMED`; 8/11 CONFIRM → routes G-021 TRADABLE) is reproduced from raw data, holdout-clean, deterministic,
and Holm-correct; the audit carried full verdict forensics; and the registry/ledger disposition — including the
**11 counted TEST reads** — was recorded in the same change.

## Checks

**Audit verdict forensics present (required) — PASS.** `audit.md` carries: (a) a **per-stratum re-derivation**
with an **affirmative masking check** — the 8 CONFIRMs are confirmed to span 7 instruments across both domains
(not a single-cell/single-domain artifact), no pooled number is presented as the verdict, and the 1h-tier
reversal is disclosed per stratum; (b) a **mechanism statement** (RCT ~99% target capture; 4h clears by cost
geometry not signal strength; uniform TRAIN→TEST selection-overlap shrinkage that the robust core absorbed and
the thin 1h tier did not); (c) a **gate-shape check** (binding mean gate is the right instrument for a tradable
P&L claim; the co-reported median exposes USTEC-1h's mean-carried confirm — disclosed, not masked). Independent
re-derivation reproduced EURUSD-4h (+0.094) and GBPUSD-1h (−0.103) bit-for-bit via `xen.ass`. ✓

**Materiality / no verdict-material finding down-classified — PASS.** One Warning (W1: the `INCONCLUSIVE` label
conflates power-limited with well-powered net-negative). The audit shows explicitly it **cannot move any
verdict-bearing number** — `experiment_verdict` is `TEST_CONFIRMED` on ≥1 CONFIRM regardless of the three
non-confirming cells' labels, the 8 binding CONFIRM strata are untouched, all 11 counted reads are spent
regardless, and the underlying statistics are correct in the table. Correctly classified Warning and **resolved
in interpretation** (results.md re-labels GBPUSD-1h/EURUSD-1h EVIDENCE_AGAINST, NZDUSD-1h INCONCLUSIVE) — not a
suppressed Critical. No fix-and-rerun was required or skipped. ✓

**Per-stratum doctrine (LESSON-001) — PASS.** The binding verdict is emitted and documented per cell
(`test_adjudication.csv`); `experiment_verdict` / "routes TRADABLE" is an explicit routing readout, not a
collapsed binding boolean. ✓

**Holdout discipline — PASS.** The binding read is the analysis-TEST stratum; the final-30% global holdout was
never loaded (`holdout_untouched=true`; ~561k holdout rows/file confirmed not read; fill clipped at the analysis
edge). Audited and reproduced. ✓

**Signal-registry disposition recorded (required; registry-relevant) — PASS.**
- **`test-read-ledger.md`:** the **11 counted TEST reads** are entered in the **same change** — each carried
  (instrument, domain) stratum advanced **0→1** (EURUSD-1h, GBPUSD-1h, NZDUSD-1h, US2000-1h, USTEC-1h,
  AUDJPY-4h, EURJPY-4h, EURUSD-4h, GBPJPY-4h, USDCHF-4h, XAUUSD-4h; EURUSD-1h/4h distinct), with the EXP-093
  narrative entry (first counted reads of the family). Cap 2/stratum honored; other 37 strata stay 0/2; global
  holdout outside the ledger, untouched. ✓
- **`candidate-families/cf-mr-001.md`:** EXP-093 outcome section added (TEST_CONFIRMED; HYP-002 tradability
  SUPPORTED; per-cell outcomes retained incl. the 2 EVIDENCE_AGAINST + 1 INCONCLUSIVE). ✓
- **`multiplicity-registry.md`:** Phase 021 batch EXP-093 row advanced `PLANNED → TEST_CONFIRMED` with the 11
  counted reads and all per-cell outcomes retained; no new countable item; 0 slots. ✓

**Results honesty / no overreach — PASS.** `results.md` states effect sizes, CIs, and n per cell; treats the
EVIDENCE_AGAINST/INCONCLUSIVE non-confirms as valid findings; flags 4h dominance as cost-geometry (not stronger
signal) and the 1h confirms as mean-carried; scopes the verdict to the analysis-TEST stratum (not the global
holdout). Verdict SUPPORTED is justified by ≥1 CONFIRM (8, with breadth). ✓

**No goalpost-moving — PASS.** Frozen D2/D3/D6 definitions, margins, cost table, and Holm sizing were not
retro-edited after seeing outcomes; the carried-set expansion to all 11 was ratified *before* the read
(`D0-amendment-006`) and widens (conservatively) the Holm family. ✓

**Next-steps are new scopes — PASS.** Global-holdout release (separate gate), 1h median-fragility diagnostic,
and deferred levers are all framed as future experiments under their own D0/slot, not extensions. ✓

**Indexes updated — PASS.** `python/experiments/INDEX.md` row added; CF-MR-001 family detail card + summary row +
G-021 gate row + header updated; master `INDEX.md` live status updated (no per-experiment card added to master).
✓

## Note (not blocking)

The formal **G-021 adjudication** (`G-021-gate-review.md`) is an operator/checkpoint step, not part of EXP-093.
EXP-093 mechanically **routes** G-021 TRADABLE (≥1 CONFIRM under the frozen D6/4c rule); the documentation
correctly records it as "routes TRADABLE — adjudication pending." A sanctioned **global-holdout release** for the
4h robust core remains a separate, later gate.

## Outcome

No Critical or Warning governance issues. Registry/ledger disposition complete (11 counted reads recorded in the
same change). **APPROVE** — EXP-093 closes.
