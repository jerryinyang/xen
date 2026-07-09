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

## Chapter 02 dead ends

| # | Dead end | Evidence that closed it | Re-open only if |
|---|----------|------------------------|-----------------|
| **P-10** | Own-price / anchor-deviation **mean-reversion fades captured via passive limit entries** | Four vehicles, same veto: CF-MR-002 (net-negative absolute), CF-MR-003 (0/24 powered admits at 15m), CF-MR-004 (entry-seam mismatch — limit-touch fill ≠ measured confirmed-breach event, adverse selection), CF-MR-005 (ladder P&L reproduced by random-timing controls). | A **confirmed-breach entry object** traded natively (not a limit at the measured level), new D0. Passive-limit entry on an MR fade is banned as a capture vehicle. |
| **P-11** | **Per-leg CI_low>0 on a ladder/scale-in object** read as conditioning evidence | EXP-018: matched-cadence/matched-hold random ladders reproduce it with no signal (NZDUSD +31.5 CI_low +13.7 unconditioned). | Never read per-leg CIs as evidence. Demand an episode-level, cadence-matched random-timing control with a **seed battery** (L-19). |
| **P-12** | **Banded-rebalance / symmetric-grid volatility harvest** on the FX MR block | EXP-020: rebalance premium ~100× below the `w(1−w)σ²` design estimate (UNPOWERED); grid cadence collapses to 5–28% of implied, cap-locks, censored inventory erases the harvest. | A within-episode-clearing structure (rolling anchor, no hard cap) on an unseen band = NEW family with its own D0 — not a re-parameterisation. |
| **P-13** | **Cross-sectional consensus-residual reversion** (hedged basket fade) | EXP-021/022/024: residual reverts (VR<1 everywhere) but 0 hedged constructions clear multiplicity on either basket; all leads effect-at-MDE. | A different cross-sectional endpoint or a construction that doesn't route through `argmax|s|` event concentration; leads (AUDUSD/USDCAD, USTEC) need a **fresh family**, not a re-read. |
| **P-14** | **HTF-DI continuation conditioning as a tradable edge** at 1h→5min | EXP-025 T1-terminal: 0/440 qualifiers, MDE ≤5.2 bps, true effect ≈1–4 bps < cost; index positives drift-shaped, no dose-response. | A vehicle whose per-trade capture is ≥10× larger (longer holds / different granularity) — and only via a NEW family with the L-21 unit pin applied at design time. |
| **P-15** | Trusting a **screen-quoted effect size across the screen→graduation seam** without re-deriving its unit | EXP-025: SPDR screen normalised by 5min ATR, graduation design asserted 1h ATR — target inflated 4.1×; entire graduation chased a fictitious 30–60 bps. | Never. L-21 unit pin + money-unit floor are binding at every seam (`docs/references/spdr-lane.md`). |

## The terminal branch (state it honestly)

If single-series magnitude, cross-sectional, **and** flow all reproduce ≈-random, then
price-derived information — single or relational — is **exhausted on this dataset**, and the
real frontier is **non-price data acquisition** (order book, cross-asset, fundamentals) — a
data decision, not a modelling one. The screens are designed so the programme can reach this
conclusion having spent **zero** reads and zero slots.
