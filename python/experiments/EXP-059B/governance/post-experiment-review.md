# Post-Experiment Governance Review — EXP-059B

**Experiment:** EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami;
`/EXIT-TRAIL-UNCAPPED`)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-012b` — EXP-059B
**Stage:** 8 (post-experiment consolidated governance)
**Artifacts reviewed:** `audit.md`, `results.md`, `report.md`, index updates,
signal-registry updates (`multiplicity-registry.md`, `candidate-families/harami.md`,
`test-read-ledger.md`), `python/experiments/INDEX.md`,
`docs/experiments-docs/INDEX.md`,
`docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`
**Reference framework:** `research-pipeline/references/governance-constraints.md`;
`_pipeline-config.md`; `014-B-EXP-059B-uncapped-trailing-addendum.md`.

---

## 1. Audit sanity

- **Verdict:** PASS — 0 Critical, 1 Warning (BENCH itself weak in 90/99 cells — interpretation caveat, not a code/integrity issue), 5 Info.
- No correctness, data-integrity, or causal-semantics issues.
- Determinism verified (17 instruments, byte-identical replay).
- Holdout fence verified (TRAIN-only, lazy scan, `CloseTime` fenced, uncapped scan clips to `last_train_idx` → DATA_CENSORED).
- Real-price discipline verified (all metrics on real OHLC; HA for detection only).
- F02/F04/F06/F07 adversarial remediation verified: cap-isolation divergent-subset contrast, additive exit-offset returns, `resolver_source_sha256`, uncapped test coverage.
- First-execution correction (edge_ok invariant for offset-0 DATA_CENSORED) verified.

## 2. Results interpretation sanity

- Interpretation (`results.md`) matches the predeclared EVIDENCE_FOR/AGAINST criteria.
- No post-hoc goalpost movement. The scope flagged "possible INCONCLUSIVE-by-power (uncapped censoring)" — this did not materialize (censored events negligible), and the result is correctly EVIDENCE_AGAINST.
- Results separate factual observations from speculation.
- Limitations properly documented (BENCH weak in most cells, vs-BENCH contrast on uncensored common subset, frozen `atr_mult_trail`, gross-only).

## 3. Report completeness

- `report.md` covers: hypothesis, scope boundaries, method summary, key quantitative results, audit caveats, conclusion, registry disposition, follow-up recommendations, artifact links.
- Registry disposition recorded and is registry-relevant.

## 4. Index updates

| File | Check |
| --- | --- |
| `python/experiments/INDEX.md` | Row added for EXP-059B (EVIDENCE_AGAINST) — verified present. |
| `docs/experiments-docs/families/cf-ha-harami-001/INDEX.md` | ToC entry + detailed card appended (5-field schema). |
| `docs/experiments-docs/INDEX.md` | Checkpoint live status updated. |

## 5. Signal-registry disposition

| Registry | Check |
| --- | --- |
| `multiplicity-registry.md` | HYP-012b outcome recorded (EVIDENCE_AGAINST, 0/2 binding arms clear P11). |
| `candidate-families/harami.md` | `/EXIT-TRAIL-UNCAPPED` branch updated with result; closed as characterized negative. |
| `test-read-ledger.md` | No changes — 0 TEST reads. Correct. |

Refuted/blocked/inconclusive items: EVIDENCE_AGAINST outcome — retained in multiplicity-registry as a characterized negative; branch not deleted. Correct per the pipeline constraint ("refuted, blocked, and inconclusive items stay in the registry — never deleted").

## 6. Issues

None. All governance constraints pass.

---

## VERDICT

```text
VERDICT: APPROVE
```
