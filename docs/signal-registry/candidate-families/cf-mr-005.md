# CF-MR-005 — 4h Ladder Scale-In Own-Price Mean-Reversion Harvest

**Status:** `REGISTERED (2026-07-03, operator decision D2 — EXP-014c disclosure spin-out).
HYP-001 SCOPED as EXP-015 (design gated APPROVE 2026-07-03, analysis-only mechanism
characterisation — python/experiments/EXP-015/design.md); awaiting Stage 2.`
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

## Deferred / follow-on

- Phase-shift-control semantics on mixed own-price/construction P&L — **deferred behind
  mechanism characterisation** (operator D3).
- Relation to CF-MR-004's ~5 bps raw-minus-shift increment on US2000 — only testable with a
  paired raw-vs-control design; not part of this family's first branch.

## Discipline

0 candidate slots consumed at registration; no counted TEST reads; every future screen requires
a registered hypothesis + EXP-ID here first; refuted/blocked/inconclusive outcomes retained.
