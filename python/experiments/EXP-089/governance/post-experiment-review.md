# Post-Experiment Governance Review — EXP-089 (CF-MR-001 Mean-Reversion Availability Screen, Phase 020)

**Reviewer:** research-pipeline consolidated Stage-8 governance. **Date:** 2026-06-23.
**Artifacts:** `audit.md` (amended-run audit + C-1/C-2 appendix), `results.md`, `report.md`, index + registry
updates, `results/`. **Run:** amended (`D0-amendment-001`).

---

## Checks

### Verdict forensics present and autonomous — PASS
The audit ran full verdict forensics on the amended run, not contingent on anyone questioning it:
- **Per-stratum re-derivation + masking check:** independent S re-derivation matches `family_admission.json`;
  the headline is decomposed across sub-screens (CORE the driver; regimes uniform-and-inert; variants dead) and
  **per domain** (15m 16/16, 1h 11/16, 4h 1/14). Affirmatively confirms the pooled S=28 is **not masking a
  contradiction** (no stratum reverses; 4h is weak-not-opposite) and flags the domain gradient as
  disclosure-only.
- **Mechanism statement:** short-horizon reversion bounce; explicitly argued **conservative** w.r.t. the
  entry-ATR denominator; variant-kill corroboration.
- **Gate-shape check:** location effect vs location gate — shape-appropriate, unsaturated.

### Verdict-material findings fixed-and-rerun (not down-classified) — PASS
The deviation's C-1 (ATR-normalization confound) and C-2 (trend-length horizon) were **Critical /
verdict-material** and were **resolved by an in-place amendment + a full re-run** (`D0-amendment-001`), not
documented-and-proceeded. The deviation results were hard-deleted. The fresh audit verifies both fixes
empirically (regime ladder collapsed to flat; cap median ~3 bars; driver flipped CORE-VOL-LOW→CORE) and finds
**no Critical or Warning issues** (3 Info, each with explicit non-materiality reasoning).

### Per-stratum doctrine (LESSON-001) — PASS
No collapsed cross-cell PASS/FAIL is binding; per-sub-screen `S` and per-cell tests are emitted; the pooled
S=28 and the cross-sub-screen comparison are labelled disclosure; `results.md`/`report.md` report per domain.

### Integrity / holdout / real-price / determinism — PASS
`determinism_ok`, `recon_all_ok`, `regime_match_recon_ok`, `holdout_untouched=true`, `counted_test_reads=0`,
`candidate_slots=0`; bite GREEN at the single-test `f01a000b…` (recorded sha == expected). All metrics on real
domain OHLC; MR-tempo cap and forward path causal, clipped at the TRAIN edge.

### Honest reporting / no overreach — PASS
`results.md`/`report.md` state **availability ≠ capturable edge** (no exit/cost, gross, TRAIN-only), the ~3-bar
horizon, the 4h absence, and the inert vol-regime lever; the provisional `ADMITTED` is consistently captioned
**NON-BINDING — pending G-020**. Follow-ups are framed as new scopes (capture-geometry phase), not extensions.

### Signal-registry disposition — PASS (registry-relevant; recorded)
- **`candidate-families/cf-mr-001.md`:** advanced to `SCREENED — provisional ADMITTED (NON-BINDING), pending
  G-020`; amendment banner + Outcome section added. **Correctly NOT marked ADMITTED and no slot consumed** —
  the binding admit is G-020, not EXP-089.
- **`multiplicity-registry.md` (Phase 020 batch):** EXP-089 outcome recorded — CORE lever, regimes inert,
  variants dead; **leg-2 conjunction retired by `D0-amendment-001` and recorded as no-longer-countable**; all
  items **retained**; 0 slots / 0 counted reads.
- **`test-read-ledger.md`:** EXP-089 entered as a TRAIN-only **disclosure**; all 48 strata unchanged **0/2
  open**; holdout sealed.
- **Indexes:** `python/experiments/INDEX.md`, `families/cf-mr-001/INDEX.md` (detail card, five-field), and the
  master `INDEX.md` (live status + Family Indexes table) all updated; no per-experiment card placed in the
  master.

### Amendment governance — PASS
The deviation→amendment→rerun cycle is fully recorded: dated `D0-amendment-001`, voided audit retained as the
referenced forensic record, frozen D0 + scope bannered, MR-tempo cap constants pinned pre-data (could not be
tuned — deviation results deleted before the amendment). No new countable registry item; question/member
set/budget unchanged.

---

## VERDICT

```text
VERDICT: APPROVE
```

The audit carried full verdict forensics with an affirmative per-stratum masking check; the two
verdict-material deviation confounds were fixed and the experiment fully re-run (not down-classified); the
amended run is deterministic, fenced, causal, real-price, and honestly interpreted; and the signal-registry
disposition is correctly recorded (SCREENED — provisional ADMITTED, NON-BINDING, no slot consumed, items
retained, ledger unchanged). EXP-089 is complete. Binding admit/exonerate is deferred to **G-020**.
