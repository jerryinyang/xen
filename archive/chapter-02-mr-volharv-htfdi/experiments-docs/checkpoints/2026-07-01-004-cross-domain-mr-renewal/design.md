# Phase 004 — Cross-Domain MR Renewal (CF-MR-004) (Chapter 02)

**Status:** G0 RATIFIED (2026-07-01). **Chapter:** 02
(cTrader-primary era). **Prior phase:** 003 CLOSED (CF-MR-003 RETIRED 2026-07-01).
**Family:** CF-MR-004 — `docs/signal-registry/candidate-families/cf-mr-004.md` (REGISTERED
2026-07-01). **Origin:** operator renewal proposal `.ignore/idea/README.md`.

## Context — where the programme is

Phase 003 closed at CF-MR-003 RETIRED (availability real, NOT-TRADABLE at 1h + 15h; cost/capture
veto). All prior MR families closed (CF-MR-001 refuted, CF-MR-002 exonerated, CF-MR-003 retired).
Programme was at the **terminal branch** (price-derived info exhausted; frontier = non-price data).

Operator's renewal proposal: 3 new cross-instrument spread designs (fixed-ratio pair,
fixed-weight basket, relative-value index) targeting the **UNTESTED** cross-section/magnitude cell
in the availability 2×2; S5 redo (rolling-β basket, from scratch); from-scratch mandate (L-13);
no lower-domain (precalc limit orders, set-and-forget); informative-not-gating MR screen (L-12);
full faithful cTrader from the start (operator mandate).

**Honest prior: LOW.** All price-derived MR closed. New series carry a distinguishing information
source (fixed-parameter cross-instrument spreads, untested 2×2 cell), gated at zero cost (0 slots,
0 counted reads, TRAIN-only).

## Objective

**O1 — Full-strategy availability + tradability (TRAIN, price-primary).** Does the complete
precalc limit-order strategy on the 4 cross-instrument anchor series produce (a)
reversion-to-anchor beyond dislocation-matched matched-random (availability) AND (b) net-positive
under frozen referee (tradability), per stratum, on TRAIN?

Two outcomes: **tradable-on-TRAIN** (→ separately gated counted TEST read) or **not-tradable**
(record; family retained; availability characterized, does not survive to net).

## Ratified forks (operator, 2026-07-01)

| # | Fork | Decision |
|---|------|----------|
| **Governance** | Open vs terminal-branch redirect | **Open CF-MR-004.** New info source; LOW prior; 0 cost. |
| **Initial scope** | Availability-first vs full-strategy-first | **Full-strategy-first** (operator mandate). Complete strategy in cTrader; availability + tradability from one emission. |
| **`/SERIES`** | Which series | **4 cross-instrument spreads:** S5 redo + S6 + S7 + S8. Defs in `cf-mr-004.md`. |
| **Lower-domain** | Keep vs remove | **Removed.** Precalc limit orders, set-and-forget. |
| **Gating** | MR-screen gating vs informative | **Informative.** Screen characterizes, does not disqualify. L-12. |
| **Budget** | TRAIN vs TEST | **TRAIN-only, 0 counted reads, holdout sealed.** 0 slots (first probe). |

## Forks for Stage 1 predeclaration (quant-analyst → EXP-013 design.md)

| Fork | Recommendation | Rationale |
|---|---|---|
| **Anchor domain(s)** | 4h + 1D | Higher domains where spread is stable; 1h may be too noisy for fixed-parameter spreads. |
| **Instruments / groupings** | FX majors (7) primary; equity indices (4) secondary | Cross-instrument spreads need natural groupings. |
| **Multiplicity** | Series × domain × grouping cells; Holm family | Predeclare based on realized cell count. |
| **Cost model** | Analyst-derived (limit entries change cost structure) | Binding-leg discipline (L-02). Frozen before outcome contact. |
| **From-scratch scope** | Family-specific logic = from scratch; multi-symbol StrategyHost = reusable infra | L-13 applies to family-specific code, not general framework. |

## Sequencing (gates)

1. **G0 (this checkpoint):** ratify scope; register CF-MR-004; 0 reads/slots. *(pending ratification)*
2. **EXP-013 design (Stage 1):** quant-analyst merges scope + plan; predeclares cost model,
   per-stratum net + availability endpoints, referee adjudication, member set, multiplicity,
   leak tripwire(s). Inline pre-exec GATE.
3. **Implement (Stage 2):** C# `ISignalModel` (4 series, precalc limit orders, set-and-forget,
   multi-symbol) + `EXP-013.conf`; Python ingest/validate only. From-scratch family-specific code.
4. **Execute (Stage 3, operator-gated):** credentialed cTrader-CLI run — **re-confirm with
   operator before running.** TRAIN fence; holdout sealed.
5. **Audit (Stage 4) → Document (Stage 5):** verdict forensics + causal-provenance/leak pass;
   per-stratum availability + net verdict; registry + index updates; inline post-exec GATE.

## Hard guards (binding)

- Price-primary → **cTrader in-engine** only; no vectorized Python edge/outcome module (L-01/P-09).
  Real emitted OHLC; open-to-open; `≤ t-1`; intra-bar fills engine-realized.
- **From-scratch:** no reuse of CF-MR-003 family-specific code. Multi-symbol StrategyHost = reusable
  infra. L-13.
- **No lower-domain:** precalc limit orders, set-and-forget.
- **Informative-not-gating MR screen:** L-12.
- **Per-stratum** binding verdicts; pooled = disclosure-only (L-03).
- Frozen referee; CF-MR-004 **never** tunes it (L-12).
- **0 counted TEST reads, holdout sealed**; tradability→OOS = separate dated D0.
- No scope expansion after G0. Cost model + endpoints predeclared, frozen before outcome contact.
- Cost realism binding, early (L-02).

## Success criteria (O1)

- **Tradable-on-TRAIN:** net-positive per-stratum edge (binding-leg cost) clearing frozen referee
  on predeclared majority at predeclared MDE, AND availability confirmed. → gate counted TEST read.
- **Not-tradable:** availability does not survive to net on admitted majority. Record; family
  retained; terminal-branch prior reinforced.
- **Inconclusive/underpowered:** finite-MDE cells too few, or direction mixed. Record as UNPOWERED.

*(Concrete cost model, MDE, endpoints, member set, multiplicity, leak tripwires predeclared in
`python/experiments/EXP-013/design.md`, frozen before outcome contact.)*
