# EXP-086 — Stage 8 Post-Experiment Governance Review

**Experiment:** EXP-086 — Screen M: single-series magnitude / non-directional availability (Phase 019 Family-Selection, axis M, `CF-VOLEXP-001/HYP-001`).
**Reviewed:** `audit.md`, `results.md`, `report.md`, index updates, and signal-registry updates, against the bundled governance constraints.

---

## Verdict

```text
VERDICT: APPROVE
```

The experiment is complete and trustworthy. Integrity verdict `SCREEN_DELIVERED` and the provisional, NON-BINDING availability disposition `ADMITTED` are both faithfully supported, kept distinct, and not overstated. No verdict-material findings remain. Pipeline complete; the binding admit/exonerate is correctly deferred to G-019.

---

## Governance checks

### Audit (`audit.md`) — PASS
- **Thoroughness:** correctness, edge cases, NaN/zero-tail/mad-zero, holdout fence, look-ahead, real-price, timestamp alignment, determinism, and reconciliation all checked with line references.
- **Verdict forensics present (autonomous):** mechanism statement (NR7 compression → rare adverse-tail excess; tail-only not location), **not** a bare numeric confirmation. ✓
- **Per-stratum masking check:** per-domain re-derivation of NR7·tail (tailmass Δ̂>0 in 15/16·15m, 10/16·1h, 7/14·4h; `s_cell ∝ 1/√n`) affirmatively shows the pooled `S_M=3` is **conservative/anti-masking**, not hiding heterogeneity. ✓
- **Gate-shape check:** confirms the tailmass gate sees the tail shape (admit is tail-driven), the typical-range `S=0` is a true no-location-effect, and records the left-tail-only nature of the binding statistic. ✓
- **Materiality & blocking:** 0 Critical; both Warnings (independent-stream max-stat null = conservative; magnitude-budget `net_atr` necessary-not-sufficient) are explicitly shown unable to move `S_M`, `S*`, `perm_p`, the three `beats_random` flags, or the integrity verdict. No verdict-material finding was down-classified; no fix-and-rerun owed. ✓
- **Numerical validation:** tailmass reproduced exactly from `per_event_geometry.parquet`; `ci_low = Δ̂ − 1.645·s_cell` verified; `perm_p` arithmetic (162/5000 ⇒ Q95=2, Q97.5=3) reconciled to the FWER band. ✓

### Results interpretation (`results.md`) — PASS
Honest and non-overreaching: two verdicts separated; effect called economically tiny; borderline (fails FWER 0.025) stated plainly; **tail-only ⇒ long-vol, never directional** carried; both audit Warnings carried as caveats (esp. `net_atr` not an edge); two reads kept strictly separate (no pooled `|move|`); pooled figures labelled disclosure-only; next steps are specific new experiments (EXP-087/088, G-019, conditional HYP-002+), not scope extensions. Real-price discipline affirmed.

### Final report (`report.md`) — PASS
Self-contained; embeds the two decisive plots (`03_permuted_axis_null.png`, `02_delta_tail.png`) with captions; honest limitations section; all artifacts linked by relative path; carries a Registry Disposition subsection.

### Index updates — PASS
- `python/experiments/INDEX.md`: EXP-086 row added (status + one-line finding + 2026-06-22).
- `docs/experiments-docs/INDEX.md` (master): Family Indexes row added (Family-Selection Phase 019) and the Phase 019 checkpoint live-status line updated to EXP-086 COMPLETE; no per-experiment card placed in the master.
- `docs/experiments-docs/families/family-selection-phase-019/INDEX.md`: created (header + overview + ToC) with the EXP-086 five-field detailed card.

### Registry & ledger disposition (registry-relevant) — PASS
A disposition is recorded, and because the result is registry-relevant all three were updated in this change:
- `multiplicity-registry.md` Phase 019 Batch: EXP-086 outcome advanced `AUTHORIZED → SCREEN_DELIVERED` + provisional `ADMITTED` (NON-BINDING), with the full statistics; **retained**, not deleted; batch status header updated; EXP-087 set to scope-next.
- `candidate-families/family-selection-phase-019.md`: `CF-VOLEXP-001` status advanced to `SCREEN-M-DELIVERED, PROVISIONALLY-ADMITTED (NON-BINDING), PENDING-G-019`; HYP-001 outcome recorded; kill/pass logic retained.
- `test-read-ledger.md`: EXP-086 disclosure entry added (TRAIN-only, no stratum-specific inference, 0 counted reads; all 48 strata remain 0/2 open; holdout never read).

### Programme constraints — PASS
0 candidate slots, 0 counted TEST reads, holdout untouched (`holdout_untouched=true`), TRAIN-only, gross, real-price, deterministic, per-stratum reporting (LESSON-001), no goalpost movement (Stage-4-reconciled constants ran as predeclared). Single hypothesis. Complexity budget respected (3 tests / 5 plots / 2 modules).

---

## Disposition

**APPROVE — EXP-086 complete.** Axis M enters the Phase 019 slate as provisionally `ADMITTED` (NON-BINDING). No further action on EXP-086. The binding admit/exonerate is the terminal G-019 gate after EXP-087 (Screen X) and optionally EXP-088 (Screen F).
