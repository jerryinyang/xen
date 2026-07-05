# CF-MR-005 — 4h Ladder Scale-In Own-Price Mean-Reversion Harvest

**Status:** `RETIRED (2026-07-04, operator-signed, checkpoint-006 retrospective —
docs/experiments-docs/checkpoints/2026-07-04-006-cf-mr-005-disposition/retrospective.md).
Basis: EXP-018 (HYP-003, first full INFR-001 pass) — the VAL-006 residue does not survive
deliberate specification: episode-net primary WASH in all 4 residue cells (US500 both-leg a
well-powered zero −2.5 [−26,+24]); random-timing kill test unfalsified (US2000 collapse 0.49;
NZDUSD random ladder per-leg +31.5 CI_low +13.7 > 0 with NO signal while the live arm loses);
surviving per-leg positive attributed to 2022 long-side index-drift carry on deep-add
inventory (peak 43 legs; return on peak exposure ≈ B&H). NZDUSD negative control passed.
python/experiments/EXP-018/report.md.`
*(Prior: OPEN — NO VALID TEST EVIDENCE; TRAIN BASE RE-DERIVED (VAL-006, 2026-07-04).
EXP-016's "TEST PERSISTENCE RETAINED" is VOID: its 3 counted TEST reads (AUDUSD/NZDUSD/
US2000-4h, each 1/2) were SPENT_ON_DEFECT on the corrupted multi-leg per-bar estimand
(critical-017.md — profit counted per leg, risk marked once; 3.8x inflation / sign flips).
No TEST-retention claim stands; reads not refunded. Corrected TRAIN picture
(python/experiments/VAL-006/analysis.md, canonical xen.adjudication estimands): the "61-cell
extend field" collapses — 44 of 52 corrected CI-positive cells are e1 frozen-TP survivorship
artifacts; AUDUSD/NZDUSD extend ladders are outright losers per leg; the named candidate
US2000 e3/extend/z15 is +9.5 bps/leg gross with CI [−15.9,+32.0] (≈0 even at zero cost).
Residual unadjudicated weak-positive: a US2000 e0/e2 cluster (net/leg CI_low>0, ~2-5%/yr on
peak exposure, 2022-concentrated, 2023 negative) + a small US500 both-leg cluster. Mechanism
question OPEN on this much thinner base. Family disposition = checkpoint-retrospective
decision (operator).)*
*(Prior-prior: OPEN — TEST PERSISTENCE RETAINED (EXP-016, 2026-07-03) — VOIDED by critical-017 +
VAL-006. Prior-prior: CHARACTERISED-NULL / retire-recommended after EXP-015 — superseded per
operator fork. Originally REGISTERED 2026-07-03, operator D2.)*
**Family ID:** CF-MR-005. **Chapter:** 02 (cTrader-primary era).
**Origin:** EXP-014c extend-arm field discovery (`python/experiments/EXP-014c/{report,audit}.md`
§6/§5.4; operator decision record `.ignore/temp/d1/exp-014c-findings-and-decisions.md` D2/D3).

## Thesis

Scaling into 4h dislocations with a ladder of deepening adds harvests short-horizon **own-price**
mean reversion; per-leg P&L fattens with add depth. The phenomenon is the field EXP-014b/014c
observed in every extend arm: **61 cells net ci_low > 0 (53 never admitted), exclusively
extend/allow arms, across all 11 instruments (10 powered), both z\* triggers, all four exit sets; positive
every year 2021–2024 in the strongest cells; 50–85% of the edge survives a 60h basket
phase-shift** (the basket was a trigger, not the source). This family claims the harvest on its
own terms, with a **basket-free trigger**.

## Evidence base (inherited disclosure — not admissible as this family's screen)

> **⚠ ESTIMAND CORRUPTION (2026-07-04).** Every per-bar figure in the table below (and the
> thesis paragraph's "61 cells net ci_low > 0 … 50–85% survives the shift") was computed by the
> defective `assemble_realized_bps` lineage and is **superseded** by the per-leg re-derivation
> in `python/experiments/VAL-006/analysis.md`. Corrected: US2000 e3/extend/z15 = +9.5 bps/leg
> gross, CI [−15.9,+32.0]; ladder-depth gradient unverified; shift collapse fractions incoherent
> under per-leg truth. Rows retained for record only.

| Fact | Source |
|---|---|
| US2000 e3/extend/z15: net +10.9 bps/bar, ci_low +3.17, 40 episodes; yearly +10.7/+17.5/+5.3/+9.2 (2021–24) | EXP-014c audit §5.4 |
| AUDUSD/NZDUSD e3/extend/z15: +3.98/+4.00, ci_low +1.06/+1.53; survive shift with ~85% of edge | EXP-014c audit §5.3 |
| Ladder-depth gradient: US2000 L0 +2.8 / L1 +10.5 / L2 +26.3 bps/leg | EXP-014c audit §5.4 |
| Cost stress: NZDUSD survives 3×, AUDUSD 2×, US2000 1× only | EXP-014c audit §5.4 |
| Execution clean: fills in-range, gap slippage charged, provenance traced end-to-end | EXP-014c audit §3/§6 |

All inherited reads are TRAIN-only disclosure with **unpaid multiplicity for single-cell
claims** — the field-level regularity motivates registration; nothing here pre-admits any cell.

## First-branch design constraints (binding on the Stage-1 design)

1. **Basket-free trigger** — the trigger must be derivable from the instrument's own price
   (the S8 spread trigger is CF-MR-004 property and demonstrably not the P&L source).
2. **Mechanism characterisation before any tradability claim** (operator D2/D3): what reverts,
   at what depth/horizon; ladder-depth attribution; left-tail exposure of the scale-in (the 5y
   window may not contain the tail the martingale-flavored component is short).
3. **Cost realism binding, early** — CF-MR-001/002/003 all died on cost-vs-capture; index RT
   costs 3–4 bps; deep-ladder fills are the most slippage-exposed component.
4. **P-02**: no exit-stack rescues; the family's question is mechanism and capacity, not exits.
5. **Availability definition must be native to the ladder mechanism** (L-13) — the two-barrier
   single-entry race is the wrong object for a multi-add position.
6. **Attribution controls report magnitudes**: any phase-shift-style control discloses the
   **collapse fraction** (control net / raw net), never only a binary admit (EXP-014c W3).
7. Frozen referee untuned (L-12); per-stratum verdicts (L-03); ≤t-1 arming, m1 fills,
   open-to-open, holdout sealed.

## Registered hypotheses

| Hypothesis | EXP-ID | Registered | Scope | Status |
|---|---|---|---|---|
| HYP-001 — mechanism characterisation (per-event) | EXP-015 | 2026-07-03 | analysis-only | COMPLETED — NO_per-event_MECHANISM (object-mismatch caveat, L-16) |
| HYP-002 — tradability | (blocked) | — | — | not admissible (EXP-015 gate) |
| HYP-003 — deliberate ladder-harvest disposition probe of the VAL-006 residue (US2000 A/extend + A/allow + B/extend, US500 both-leg A, NZDUSD negative control; random-timing destroy + entry-delay tripwire + shift disclosure) | EXP-018 | 2026-07-04 (pre-execution; checkpoint-006 sanction, controlled thesis-shopping) | price-primary, TRAIN only, 0 TEST reads | **COMPLETE 2026-07-04 — NOT SUPPORTED (operator verdict).** Episode primary WASH ×4 residue cells; random-timing destroy unfalsified (NZDUSD rt per-leg CI_low > 0 with no signal); 2022 long-drift attribution; neg-control passed. → family RETIRED (checkpoint-006 retrospective). `python/experiments/EXP-018/report.md` |

*(HYP-003 trigger note: the residue is re-tested faithfully on the S8-basket trigger that
produced it — the first-branch basket-free constraint (§1) is superseded for this hypothesis
by the operator's 2026-07-04 residue-faithful sanction; a basket-free re-derivation remains a
separate future hypothesis.)*

## Deferred / follow-on

- Phase-shift-control semantics on mixed own-price/construction P&L — **deferred behind
  mechanism characterisation** (operator D3).
- Relation to CF-MR-004's ~5 bps raw-minus-shift increment on US2000 — only testable with a
  paired raw-vs-control design; not part of this family's first branch.

## Discipline

0 candidate slots consumed at registration; no counted TEST reads; every future screen requires
a registered hypothesis + EXP-ID here first; refuted/blocked/inconclusive outcomes retained.
