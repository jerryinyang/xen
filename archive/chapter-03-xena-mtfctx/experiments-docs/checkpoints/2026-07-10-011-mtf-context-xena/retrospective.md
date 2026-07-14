# Checkpoint 011 — MTF Context Filters via XENA (Chapter 03, Phase 1) — Retrospective

**Phase number:** 011 (Chapter 03, Phase 1) · first live XENA universes
**Design opened:** 2026-07-10 · **Universes completed:** 2026-07-13 · **Retrospective drafted:** 2026-07-14
**Status:** COMPLETED — three universes adjudicated with operator verdicts; a blocking adjudication-layer
defect was exposed, redesigned (INFR-009), and the default route restored.
**Slots / reads:** **0/2 gate slots on every universe; no counted TEST read; global holdout never loaded.**
**Family group:** [CF-MTFCTX-001](../../../signal-registry/candidate-families/cf-mtfctx-001.md) (REGISTERED 2026-07-10).

**DRAFT — operator sign-off required.** Two decisions below are operator-only and are *proposed*, not
applied: (§6) CF-MTFCTX-001 family status, (§7) lesson ratification. The family card, registry, and
`docs/knowledge-base/lessons-and-amendments.md` are **not** edited until sign-off.

**Design reference:** [design.md](design.md) · **Runs:** XENA-001/002/003 (`python/experiments/<ID>/report.md`)
· **INFR redesign:** `python/experiments/INFR-009/report.md` · **Adjudication audit:**
`.ignore/temp/new-referee/post-xena-infr-audit.md`.

---

## 1. Objective recap (design §Objectives)

1. **O1** — Exercise the full XENA lane end-to-end on real emissions for the first time.
2. **O2** — Adjudicate the CF-MTFCTX-001 thesis (HTF context improves LTF signal quality) at the
   **portfolio-selection** level — no A/B claim; the read is whether filtered variants (V01–V18) are
   selected over the unfiltered baseline (V00).
3. **O3** — Deliver the two INFR-006 leftovers blocked on a real candidate: the **C# batch manifest
   runner** and the **permutation-null battery**.

Hard guards carried in: gross gate = selection verdict, never deployability (L-22); gate cap 2/universe;
`new_data_attestation` operator-only; holdout untouched; universe status transitions only here.

## 2. Outcomes vs objectives

| Objective | Outcome | Evidence |
|---|---|---|
| **O1 — Exercise the lane** | **COMPLETE, with a load-bearing finding.** The **emission layer held** on all three universes (candidate gate, estimand gate, provenance, fence, oracle reconciliation all PASS). The **adjudication layer failed** — a scale defect that made every certification uninformative (§5). | Estimand gates 2,736/2,773/2,777 PASS; fence+provenance PASS all three. |
| **O2 — Adjudicate CF-MTFCTX-001** | **NOT ADJUDICABLE as built; negative filter-structure read is CONFOUNDED.** On all three controls the unfiltered V00 is *not* under-selected (0.45× / 1.18× / **4.0× over**-represented). But the objective is costless cadence-maximizing, which structurally penalizes any filter (audit B2) → the lane cannot fairly test the thesis. See §6. | Filter-structure rows, XENA-001/002/003; audit B2. |
| **O3 — Infra deliverables** | **Batch runner: COMPLETE** (reusable for any manifest). **Permutation battery: DELIVERED but CONFOUNDED on limit-entry universes** — it destroys the entry-price basis, not just alignment (XENA-003). Design fix required before the next native-fill universe. | C# runner shipped; battery v2 on MTFCTX-C1; XENA-003 ARM-NEXTOPEN control. |

## 3. The experiment arc

| Run | Substrate | Operator verdict | Headline | Filter-structure (V00 vs 5.3% share) |
|---|---|---|---|---|
| [XENA-001](../../../../python/experiments/XENA-001/report.md) | CTRL-01 RANDOM | **MACHINERY-ALARM** | 4/12 finalists certified (33%) vs 0.75% battery null. Substrate is noise; the alarm is about the **referee**, not the entries. Live−permuted **−1.67** (0th pct). | V00 **0.45×** — no filter preference on noise |
| [XENA-002](../../../../python/experiments/XENA-002/report.md) | CTRL-02 NAIVE MOMENTUM | **NO DETECTABLE STRUCTURE** | +0.26 above the random control on the battery, inside restart dispersion 2.90. 7/12 certified is uninformative (F_floor defect). | V00 **1.18×** — filters not preferred |
| [XENA-003](../../../../python/experiments/XENA-003/report.md) | CTRL-03 NAIVE REVERSION (native limit) | **NOT SUPPORTED (magnitude)** | Real +1.958 bps/leg gross, breakeven RT spread 0.71 bps, 0/12 survive 1.5 bps (band 20–40). **91.2%** of the edge is the limit print, not the registered mechanism (0.172 bps, 8.8%). P-10 re-encountered. | V00 **4.0× over**-represented — thesis contradicted here |

**Common:** 0/2 gate slots each; TEST never read; holdout never loaded; estimand + provenance + fence PASS.

## 4. Key decisions (operator-gated, ratified during the phase)

| # | Decision | When | Rationale |
|---|---|---|---|
| Route | Adjudicate CF-MTFCTX-001 by portfolio selection only, no registered A/B | 2026-07-10 | XENA default; thesis is a selection read (family card Q-A) |
| No gate spend | Withhold all counted TEST reads across the phase | 2026-07-12/13 | Certifications uninformative under the F_floor defect; spending a slot would bind a GROSS pass with a vacuous NET block (spread pins unset) |
| INFR redesign | Open INFR-009 rather than patch a threshold | 2026-07-13 | Audit found five root causes; L-23 forbids threshold revision on gate outcomes |

## 5. The blocking finding → INFR-009 (RESOLVED)

Post-XENA audit (`.ignore/temp/new-referee/post-xena-infr-audit.md`) — **five root causes** in the
adjudication layer (the emission layer was clean):

1. **Extensive-vs-intensive F.** `F_floor` (0.4302, v3) is an absolute threshold on log-wealth — an
   **extensive** statistic that grows with scale — calibrated at **24 candidates / 400 budget**. At live
   scale (2,736 cands) finalists clear it **8.3×–57×**, so the floor is inoperative and the plateau screen
   (which passes **50.8% of pure noise**) becomes the sole criterion.
2. **Costless cadence-maximizing objective.** `charge_costs=false` log-wealth pays for trade count; every
   HTF filter thins cadence ⇒ **a conditioning thesis cannot win regardless of whether it is true** (B2,
   load-bearing for O2).
3. **Permutation battery confounded** on non-grid-priced (limit-entry) universes — destroys the
   entry-price basis (+7.5 bps/leg on XENA-003) along with alignment.
4. **Plateau screen rewards ubiquity, not robustness** (XENA-003: 79.9% of the universe gross-profitable
   ⇒ 12/12 near-disjoint terminals all certify).
5. **Governance sequencing** — spread pins (`cost_bps`) never set; nothing in the pipeline blocked a
   GROSS-pass / vacuous-NET-block gate spend (the L-22 failure shape). Recorded near-miss.

**INFR-009 (COMPLETE 2026-07-14, committed 20ec9a0)** replaced the extensive-F/plateau adjudicator with a
**selection-aware two-stage binder** (exit (c)): stage-1 intensive screen fixes exactly one subset →
embargo → stage-2 leg-studentized LCB on an independent band. CONFIRM **DUAL_CERTIFY**, e2e α̂ 5.0%/5.0%
(boundary pass, Wilson-95 upper 9.0% — thin margin), selection_inflation ≈0 (P3d's ~3pp leak killed by
construction). P4 freeze + blind VAL: gross axis clean; P5 injected flat **1.0 bps** RT on the net path
(fixes root cause #2/#5 — cost now binds the objective) → re-VAL **VAL_PASS**. **Default route RESTORED**
under pin `pc_frozen_registry.json` v2 `db87dc1a…`; INFR-006 v3 extensive-F **superseded** (artifacts
retained). Root causes #3 (limit-entry battery) and #4 (plateau ubiquity) are **not re-encountered** by
the (c) binder but remain open design notes for any future native-fill universe.

## 6. Family status — CF-MTFCTX-001 (OPERATOR SIGN-OFF REQUIRED)

**Recommendation: RETIRE — on substrate grounds, explicitly NOT on the filter-structure read.**

Reasoning:
- The negative filter-structure read (V00 never under-selected) is **confounded** by root cause #2 and
  does **not** by itself refute the thesis. Retiring on it would repeat the L-12/L-13 error of trusting a
  broken adjudicator.
- But the three control **substrates are independently exhausted**, and the conditioning thesis has no
  cost-surviving base to improve on any of them:
  - CTRL-01 RANDOM — pure noise (nothing to condition).
  - CTRL-02 MOMENTUM — no detectable structure even unfiltered.
  - CTRL-03 REVERSION — real gross but **cost-fatal**, and 91.2% of it is a passive-limit print artifact
    (**P-10** re-encounter), not the registered mechanism.
- Prior position stands: **P-14 / CF-HTFDI-001** puts HTF conditioning at ~1–4 bps, sub-cost. Nothing in
  this phase moved that.

Retire the **family as scoped** (HTF context filters on these three naive controls). A fair test of the
conditioning thesis needs a substrate with a real, cost-surviving base edge **and** the INFR-009 net-cost
objective — that is a **NEW family with a new D0**, not a re-run of these controls.

**Alternative (if operator prefers):** keep REGISTERED / OPEN and re-run one universe under the restored
lane. Cost: the three substrates are noise/cost-fatal, so a re-run's expected information is low; the
value would be validating the INFR-009 binder on a live universe, which is an infra goal, not a thesis
goal.

```
OPERATOR DECISION:  RETIRE  (signed 2026-07-14)
Grounds: substrate-exhaustion (random noise / no-structure / cost-fatal P-10) + sub-cost P-14 prior;
         filter-structure read confounded (L-26), explicitly NOT the grounds.
```
Applied 2026-07-14: family card + family INDEX status → RETIRED; P-10 fifth vehicle added.

## 7. Lessons ratified (operator-signed 2026-07-14 — written to the KB)

| Proposed | Statement | Source | Status |
|---|---|---|---|
| **L-25** | An absolute threshold on an **extensive** (scale-growing) statistic, calibrated at small N, is inoperative at live scale. Use an **intensive** (per-unit) statistic or a selection-aware two-stage gate. (Supersedes the informal `xena-referee-scale-defect`.) | XENA-001 / INFR-009 | propose |
| **L-26** | A **costless cadence-maximizing objective cannot adjudicate a conditioning/filter thesis** — filters thin cadence, so the objective penalizes them regardless of signal-quality truth. **Net cost must bind the objective**, not be informational-only. | audit B2 / INFR-009 P5 | propose |
| **L-27** | The **permutation-null battery is confounded on limit-entry / non-grid-priced universes** — it destroys the entry-price basis along with temporal alignment; live≫permuted then reflects the passive-limit print, not predictive timing. Add a next-open discriminating control. | XENA-003 | propose |
| **P-10 update** | Add XENA-003 (naive reversion, native limit fills) as a fifth P-10 vehicle — passive-limit MR fade, cost-fatal, print-dominated. | XENA-003 | propose |
| **L-22 reinforce** | Governance near-miss: unset spread pins would have bound a GROSS pass with a vacuous NET block, and nothing blocked it. INFR-009 P5 (net-cost in the binding objective) closes it; reaffirm L-22. | root cause #5 | folded into L-26 |

**Applied 2026-07-14:** L-25/L-26/L-27 written to `docs/knowledge-base/lessons-and-amendments.md`;
P-10 updated with the XENA-003 fifth vehicle in `pitfalls-ledger.md`; L-22 reinforcement folded into L-26.

## 8. Slots / reads / holdout attestation

- Gate slots spent: **0/2 on each of XENA-001/002/003.** Test-read ledger unchanged.
- Counted TEST reads: **none.** Global 30% holdout: **never loaded** at any stage.
- `new_data_attestation`: not invoked (operator-only).

## 9. Next-phase direction (proposed)

1. Validate the INFR-009 restored binder on a **live universe** with a substrate that has a plausible
   cost-surviving base edge (not random/momentum/reversion) — closes root causes #3/#4 in practice.
2. Before any native-fill universe: implement the **next-open discriminating control** (L-27) so the
   battery can read limit-entry emissions.
3. Any new conditioning thesis re-enters as a **new family with a new D0** (§6), never a re-run of the
   retired controls.

---

*Drafted by research-pipeline orchestrator, 2026-07-14. §6 and §7 await operator sign-off before the
family card, registry, and knowledge base are updated.*
