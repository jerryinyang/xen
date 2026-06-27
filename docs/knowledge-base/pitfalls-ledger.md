# Pitfalls Ledger — Dead Ends; Do Not Re-Run

Directions Chapter 01 closed with evidence. Re-opening any of these requires a new mechanism or
a new information source — not a re-parameterisation. Live registry detail:
`docs/signal-registry/`; archived cards: `archive/chapter-01-*/`.

| # | Dead end | Evidence that closed it | Re-open only if |
|---|----------|------------------------|-----------------|
| **P-01** | Single-instrument, event-driven, **directional price-geometry** entries | Availability ≈ random, established twice with matched controls (EXP-047 AVWAP MFE ≈ control; EXP-081 harami 17/46 cells beat random — coin-flip). Dead twice over. | A genuinely new **information source** (not another price-pattern), screened availability-first. |
| **P-02** | Tuning the **downstream stack** (exits, capture geometry, conditioning, anchors, sizing) to rescue a dead entry | EXP-084 exit-invariance (0/11 arms positive OOS CI_low); EXP-035 zero conditioning dims; EXP-047 anchor flat; sizing is a near-global rescale (amplifies, can't create an edge). | Never, on a dead entry. The lever is the entry's information, not its exit. |
| **P-03** | **CF-AVWAP-001** (anchored-VWAP bounce) as a tradable strategy | Gross-positive but cost-dominated (EXP-030 net AGAINST); holdout INCONCLUSIVE (EXP-032). Exits/entry/anchor all flat (Phases 010–013). EURUSD holdout permanently contaminated. | New universe powering 4h, *and* a new exit mechanism — but the family is closed for in-family phases. |
| **P-04** | **CF-CAPGEO-001** capture-geometry basket | EXP-084 NOT_CONFIRM — basket separates on TRAIN but all economic OOS legs fail; the edge was selection-region overlap that reverses in held-back folds. | A capture-geometry signal with OOS-stable separation, screened on truly held-back folds. |
| **P-05** | **CF-MR-001** RSI-2 fade + **EXIT-RCT** favourable-limit exit | REFUTED via L-01 look-ahead; causalized it is net-negative even gross. Counted reads + holdout shot **spent-on-defect**. | Never resurrect the EXIT-RCT result. The gross MFE availability (G-020, no RCT limit) is unaffected, but is *not* a tradable claim. |
| **P-06** | **Cross-sectional relative-strength** on a *directional-favourable* endpoint | CF-XSECT-001 / Screen X NOT_ADMITTED — below the multiplicity-adjusted admission band. | Cross-sectional remains mechanism-plausible on **other** endpoints/targets; re-screen with a different target, gated on the permuted-axis null. |
| **P-07** | **Tick-volume-weighted** signal construction | EXP-046 found it inert; tick volume is broker-dependent. | A flow source that is not broker-reported tick volume (true order-book / volume-at-price). |
| **P-08** | **Lenient-L5** as a distinct referee mechanism | EXP-007 REFUTED — it exactly equals the EXP-006 τ=0 threshold endpoint (0 verdict mismatches); L5 is redundant once L3 requires `ci_lower>0`. | Never; it is a threshold endpoint, already characterised. |
| **P-09** | **Vectorised look-ahead in shared outcome modules** (the `rct[di]` favourable-index pattern) | L-01: shipped a false DEPLOYABLE_CONFIRMED; invisible to numeric re-derivation. | Banned. Price-primary edges run cTrader-in-engine; analysis modules carry provenance contracts. |

## The terminal branch (state it honestly)

If single-series magnitude, cross-sectional, **and** flow all reproduce ≈-random, then
price-derived information — single or relational — is **exhausted on this dataset**, and the
real frontier is **non-price data acquisition** (order book, cross-asset, fundamentals) — a
data decision, not a modelling one. The screens are designed so the programme can reach this
conclusion having spent **zero** reads and zero slots.
