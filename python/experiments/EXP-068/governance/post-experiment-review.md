# EXP-068 — Post-Experiment Governance Review

**Experiment:** EXP-068 — MA(20,50)-Substrate Native Combined Champion (Phase 015 S4/native; HYP-021)
**Reviewed artifacts:** `audit.md`, `results.md`, `report.md`, and the index/registry updates
(`python/experiments/INDEX.md`, `docs/experiments-docs/INDEX.md`,
`docs/experiments-docs/families/cf-ha-harami-001/INDEX.md`, `docs/signal-registry/`).
**Date:** 2026-06-18
**Stage:** 8 (post-experiment) — consolidated pipeline governance.

---

## 1. Integrity gates (from results, re-verified against raw outputs)

| Gate | Result | Status |
|---|---|---|
| P12 reconciliation (3 anchors × 99 cells, m + median, 1e-9) | nat BENCH↔EXP-061 M0 99/99; hyb BENCH↔EXP-061 H0 99/99; nat PARTIAL-V2A↔EXP-066 99/99; `recon_mismatch=[]` | ✅ PASS |
| Determinism (two-pass replay) | 17/17 cells byte-identical; `determinism_ok=True` | ✅ PASS |
| Causality | 0 violations; MA/ZigZag references confirmed pre-entry | ✅ PASS |
| Structural invariants | 0 violations; ADV-NONE `adv_count=0` (MA cap sole stop); weights sum 1.0; matched-count holds | ✅ PASS |
| Holdout fence | TRAIN-only (first 49% file-order prefix); TEST + final-30% never read | ✅ PASS |
| Real-price discipline | detection on HA; all metrics on real OHLC; MA on real close | ✅ PASS |
| `is_defect` | False | ✅ PASS |

## 2. Artifact review against governance constraints

- **audit.md** — Thorough and proportionate (comparative, multi-arm). Findings carry evidence
  (reconciliation counts, range checks, G-015 logic-consistency recompute = 0 mismatches,
  ADV-NONE adv_count=0). Verdict PASS (0 Critical, 0 Warning, 3 Info). The two substantive Info
  items (4h-concentration; narrow/tail-driven mean) are correctly classed as interpretive context,
  routed to results.md, not as correctness defects. ✅
- **results.md** — Anchored to the scope's pre-defined interpretation criteria; does **not** move
  goalposts. Reports observed values, effect sizes, sample sizes, and uncertainty; treats the
  caveats honestly (narrow mean breadth, 4h-concentration, ADV-NONE tail trade-off); separates
  evidence from speculation; carries the audit caveats; recommends follow-ups as **new scopes**
  gated on G-015 PROCEED, not scope extensions. Verdict SUPPORTED (surface deliverable) is
  justified and **explicitly does not adjudicate the G-015 gate** (P9 honoured). ✅
- **report.md** — Self-contained; embeds the 3 decisive plots with captions; honest about
  limitations; links all artifacts by relative path; states the result category
  (PROCEED_TO_SCREEN-candidate / G-015 input). No claim absent from results/audit/raw outputs. ✅
- **Index updates** — `python/experiments/INDEX.md` row added; master `docs/experiments-docs/INDEX.md`
  live status updated (family table + checkpoint block; EXP-067 now the sole remaining read before
  G-015); family detail card + ToC entry added to `cf-ha-harami-001/INDEX.md`. No per-experiment card
  was added to the master (correct). ✅

## 3. Signal-registry disposition (mandatory)

A registry disposition **is recorded**, and the result is registry-relevant — all required updates
applied in the same change:

- **multiplicity-registry.md** — `CF-HA-HARAMI-001/HYP-021` (EXP-068) advanced **PLANNED →
  CHARACTERISED (PROCEED_TO_SCREEN-candidate; G-015 input)**, with the full result + caveats; **0
  candidate slots / 0 TEST reads** retained. Native-mode `MA-SUBSTRATE` wording refreshed to the
  Amendment 001 "parallel first-class full-surface" framing (removing the stale "co-investigated,
  bounded"). Dropped HYP-022/EXP-069 and PLANNED HYP-020/EXP-067 left intact (retained, not reused).
- **candidate-families/harami.md** — HYP-021/EXP-068 disposition paragraph added (consistent with the
  HYP-014/017/018 paragraphs); family status confirmed **REGISTERED / OPEN** (candidate registration
  deferred to G-015). The MA-SUBSTRATE entry already carried the Amendment 001 framing.
- **test-read-ledger.md** — correctly **unchanged**: TRAIN-only; native population is the
  byte-identical 8360-class EXP-060B/061 set; no new stratum opened; holdouts sealed. The report
  states this explicitly. ✅

No candidate slot consumed, no TEST read spent — consistent with the Phase 015 D0 (P9/P11) and the
scope's slot/ledger accounting. Candidate registration is reserved for the single terminal G-015.

## 4. Phase-alignment check

The experiment matches `design.md` §5 (S4 native combined champion, mirrors EXP-060) and Amendment
001 (native binding; hybrid disclosed/P12-check-only; EXP-069 dropped). It does **not** adjudicate
G-015 — correctly deferring the gate to after the full slate (EXP-067 + cross-object comparison),
honouring the single-terminal-gate rule (P9) and the no-early-closure discipline. The PROCEED-candidate
status feeds the gate; it does not pre-empt it.

## 5. Residual notes (non-blocking)

- The PROCEED-candidate rests on a narrow mean co-primary (11–14 of 99 cells) and, for
  `N-V2A×ADV-NONE`, a 4h-concentrated / tail-driven composition. This is faithfully disclosed in
  results.md/report.md and the registry entry; the G-015 gate (not this review) weighs it. No action
  required at Stage 8.

---

## Verdict

```text
VERDICT: APPROVE
```

All integrity gates pass (reconciliation 99/99, determinism, causality, invariants, holdout fence,
real-price discipline). The audit is thorough with evidence; the interpretation is honest, anchored
to pre-defined criteria, and does not adjudicate the G-015 gate; the report is self-contained and
faithful; indexes are updated correctly. A signal-registry disposition is recorded and, the result
being registry-relevant, the candidate-family status, multiplicity-registry outcome, and
TEST-read-ledger (no-entry, justified) are all correctly handled — 0 candidate slots, 0 TEST reads.
