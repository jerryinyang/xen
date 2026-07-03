# Family Index — CF-MR-005 (4h Ladder Scale-In Own-Price Mean-Reversion Harvest)

Ladder scale-in on 4h dislocations harvesting short-horizon **own-price** mean reversion, with a
**basket-free trigger**. Registry: `docs/signal-registry/candidate-families/cf-mr-005.md`.
Origin: EXP-014b/014c extend-arm field discovery (spin-out, operator decision D2 2026-07-03) —
see `docs/experiments-docs/families/cf-mr-004/INDEX.md` (EXP-014c card) and
`python/experiments/EXP-014c/{report,audit}.md`.

**Status:** **REGISTERED (2026-07-03) — HYP-001 scoped as EXP-015 (design gated APPROVE 2026-07-03; analysis-only mechanism characterisation); awaiting implementation.**

**Inherited evidence (TRAIN-only disclosure; motivates registration, pre-admits nothing):**
61 cells net ci_low > 0 in EXP-014c (53 never Holm-admitted), exclusively extend/allow arms,
all 11 instruments (10 powered), both z\* triggers, all four exit sets; strongest cells positive every year
2021–2024 (US2000 e3/extend/z15 +10.7/+17.5/+5.3/+9.2 bps/active-bar); per-leg P&L fattens with
ladder depth (US2000 L2 +26.3 bps/leg); 50–85% of edge survives the 60h basket phase-shift
(basket = trigger, not source); NZDUSD survives 3× cost, AUDUSD 2×, US2000 1× only; execution
clean end-to-end.

**First-branch design constraints (binding; full list in the registry file):** mechanism
characterisation before any tradability claim; basket-free trigger; cost realism binding early
(CF-MR-001/002/003 cost-vs-capture precedent; P-02 — no exit-stack rescues); native availability
definition for a multi-add ladder (L-13); left-tail exposure of the scale-in quantified;
attribution controls disclose collapse fractions (EXP-014c W3); frozen referee untuned (L-12).

## Table of contents
- EXP-015 — HYP-001, mechanism characterisation (design gated; in progress)
