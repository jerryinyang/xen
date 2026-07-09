# Phase 003 — CF-MR-003 Tradability Concretization (CONC-1) (Chapter 02)

**Status:** G0 RATIFIED (2026-07-01). **Chapter:** 02 (cTrader-primary era). **Prior phase:** 002 CLOSED
(availability — EXP-008 methodology finding, EXP-009 SCREENED-ADMIT). **Family:** CF-MR-003
(`docs/signal-registry/candidate-families/cf-mr-003.md`, SCREENED-ADMIT). **Governing experiment:** EXP-010.

## Context — where the programme is

CF-MR-003 reached **SCREENED-ADMIT** (EXP-009: 36 leak-clean per-stratum reversion-to-anchor passes —
S5_SPREAD 20, S3_DETREND 14, S4_OU 2). That is **availability, not tradability**. Phase 002 scoped
availability-only and forbade scope expansion ("a tradability question is a new experiment under a new
D0"). CONC-1 is that new D0: the family's **first tradability test** (availability → net), price-primary,
in-engine (L-01), adjudicated under the **frozen** renewed referee (§10.3a q\*=0.75 + E6
`referee_pstar.gate_stack_pstar`; L-12 — never tuned on this candidate).
  +
## Objective

**O1 — Tradability screen (net, TRAIN).** Does the family's **form-2 limit-at-anchor** concretization
(`/TARGET`=mean, `/DIRECTION`=fade, `/REENTRY`=none, live-limit entries precalculated on `≤ t-1` anchor
levels) produce a **net-positive** edge (binding-leg cost charged) on the admitted strata, per stratum,
under the frozen referee — or not (honest prior: LOW, same broad reversion mechanism as the exonerated
CF-MR-002)? Two outcomes: **tradable-on-TRAIN** (→ a separately gated counted TEST read) or **not-tradable**
(record; family retained; availability edge stands but does not survive to net).

## Ratified forks (operator, 2026-07-01)

| # | Fork | Decision |
|---|------|----------|
| **Concretization** | Which native form | **form-2 limit-at-anchor, `/TARGET`=mean, `/DIRECTION`=fade, `/REENTRY`=none** (roadmap CONC-1). Live-limit entries precalc on `≤ t-1` anchor; engine-realized intra-bar fill (EXP-006 P* precedent). |
| **Scope axis** | S3 / S5 / both | **Both S3_DETREND + S5_SPREAD** (34 admitted strata). Operator accepts HIGH infra risk + wider multiplicity. |
| **Budget / reads** | TRAIN vs TEST | **TRAIN-only, 0 counted TEST reads, holdout sealed.** Consume **1 candidate slot** (tradability exploration opened). A counted TEST read / holdout release is **deferred**, gated on a TRAIN net-positive at a later dated D0. |
| **Cost model** | inherit vs derive | **Analyst-derived in `EXP-010/design.md`** (limit entries change entry-cost structure vs a market-order model), ratified at the inline pre-exec GATE. Binding-leg discipline (L-02). |

## Binding constraints (surfaced at G0)

`StrategyHost/ISignalModel.cs` is **single-symbol**: `OnBar(TimeBar bar, string domain)` sees one
instrument's bars. Consequences for CONC-1:
- **S3_DETREND** (per-instrument rolling-OLS residual anchor) → fits the **proven single-symbol path**
  (EXP-006). No infra extension needed.
- **S5_SPREAD** (rolling-β cross-instrument basket anchor) → the anchor is **part of the entry edge**, so it
  **must be computed in-engine** (precomputing it in Python re-opens the L-01 shared-vectorized-edge-module
  risk). This requires a **multi-symbol StrategyHost extension** (synchronized cross-instrument feeds) — an
  explicit CONC-1 infra prerequisite for the S5 arm. If not delivered clean, the S5 arm **defers to CONC-1b**
  and CONC-1 books S3 alone (no Python-side spread edge — REJECT-class leak).

## Corrected decision cadence + program (operator, 2026-07-01)

**Correction (supersedes an interim error).** A limit strategy fills at exact prices (operator's point holds),
but EXP-009 computes the **screen (`VR∧HL`) + extreme (`|z|≥2`)** — the entry information — on the **exec-domain
grid**, so decisions/booking are at the **exec** cadence, which sets the referee domain. An interim "referee
domain = anchor 4h" claim was **wrong** and is retracted. Admitted cells by **exec** domain: **exec-1h = 10**
(S5_SPREAD; frozen referee `domain=1h`, no change) · **exec-15m = 24** (14 S3_DETREND + 10 S5_SPREAD; need a
15m referee).

**Multi-symbol is feasible in-engine** (sibling `XRSI-V1` runs 8 symbols via `MarketData.GetBars` +
`Symbols.GetSymbol`), so the S5 basket anchor can be built in-engine (earlier "unvalidatable" read retracted).

**Program — "both tracks parallel" (ratified 2026-07-01):**
- **Track 1 (EXP-010 / CONC-1, T1):** multi-symbol StrategyHost build → **10 S5_SPREAD exec-1h** cells under the
  **frozen** referee (`domain=1h`, untouched, L-12). First net read. cTrader run operator-gated.
- **Track 2 (EXP-011 / E7):** referee **15m-domain extension** (cost map + `DomainSpec` + materiality),
  FPR-recalibrated on the dogfood-negative + synthetic-positive battery, **frozen + hash-pinned before it
  adjudicates CF-MR-003** (L-12). Unlocks **T2a** (14 S3 single-symbol) + **T2b** (10 S5 exec-15m multi-symbol).

Full detail: `python/experiments/EXP-010/design.md §2–§3`. EXP-011 (E7) is a referee-renew experiment with its
own design/G0.

## Sequencing (gates)

1. **G0 (this checkpoint):** ratify scope; open Phase 003; consume 1 candidate slot; 0 counted reads;
   holdout sealed. *(done 2026-07-01)*
2. **EXP-010 design (Stage 1):** `experiment-quant-analyst` merges scope + analysis plan; predeclares the
   cost model, per-stratum net endpoint + referee adjudication, the member set (admitted cells only), the
   multiplicity control, and the **leak tripwire(s)** (future-destroy on the realized-fill edge, provenance
   trace). Inline pre-exec GATE.
3. **Implement (Stage 2):** T1 first — multi-symbol StrategyHost extension + C# `ISignalModel` (S5_SPREAD
   exec-1h basket anchor in-engine) + `EXP-010.conf` (10 cells); Python ingest/validate only. (T2a S3
   single-symbol + T2b S5 exec-15m built later, after E7/EXP-011.)
4. **Execute (Stage 3, operator-gated):** credentialed/cost-bearing cTrader-CLI run — **re-confirm with
   operator before running.** TRAIN fence per file (`ANALYSIS_END` = **first-49% cutoff** = `int(int(total·0.7)·0.7)`,
   the TRAIN sub-split — seals the analysis-TEST band too; matches EXP-010 design §10); holdout sealed.
5. **Audit (Stage 4) → Document (Stage 5):** verdict forensics + causal-provenance/leak pass; per-stratum
   net verdict under the frozen referee; registry + index updates; inline post-exec GATE.

## Hard guards (binding)

- Price-primary → **cTrader in-engine** only; no vectorized Python edge/outcome module (L-01/P-09). Real
  emitted OHLC for all returns; open-to-open; `≤ t-1` decision inputs; intra-bar fills engine-realized.
- The S5 basket anchor is edge-bearing → **in-engine or the arm is deferred** (no Python-precomputed anchor).
- **Per-stratum** net verdicts; pooled = disclosure-only (L-03). Member set = **EXP-009 admitted cells only**
  (no re-screening dead cells; no downstream-stack tuning to rescue a dead entry, P-02).
- Frozen referee (§10.3a q\*=0.75 + E6 P*-gate); CF-MR-003 **never** tunes it (L-12).
- **0 counted TEST reads, holdout sealed** in CONC-1; a tradability→OOS read is a separate dated D0.
- No scope expansion after this G0. Cost model + endpoints predeclared in `EXP-010/design.md`, frozen before
  outcome contact.

## Success criteria (O1)

- **Tradable-on-TRAIN:** net-positive per-stratum edge (binding-leg cost) clearing the frozen referee on a
  predeclared majority of admitted strata, at the predeclared MDE. → gate a counted TEST read (new D0).
- **Not-tradable:** availability edge does not survive to net (cost-dominated / referee-REJECT / CI overlaps
  zero) on the admitted majority. Record; family retained; terminal-branch prior reinforced.
- **Inconclusive/underpowered:** finite-MDE cells too few, or direction mixed. Record as UNPOWERED, not FAIL.

*(Concrete cost model, MDE, net endpoint, referee adjudication rule, member cell list, multiplicity control,
and leak tripwires are predeclared in `python/experiments/EXP-010/design.md` and frozen before outcome
contact.)*
