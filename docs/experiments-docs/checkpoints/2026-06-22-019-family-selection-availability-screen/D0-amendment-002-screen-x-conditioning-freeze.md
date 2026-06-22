# Phase 019 D0-Amendment-002 — Screen X Cross-Sectional Conditioning Freeze

**Date:** 2026-06-22.
**Status:** **RATIFIED (operator, EXP-087 scoping session).** Concretizes the D1 "frozen at D0"
placeholders for **Screen X (EXP-087)** that the ratified D0 (`D0-predeclarations.md`) carried as an
unresolved menu (*"basket-relative momentum / divergence **rank** across the 16-instrument universe
(lookback, rank-vs-divergence formulation, rebalance cadence frozen at D0)"*). **No other D0 decision
changes**; D2–D6, the GREEN bite-check, the gate constants, the member set (`C=46`), seeds, and the
TRAIN-only / 0-slot / 0-read discipline are unchanged.

## Why this amendment exists

D0 §D1 left Screen X's cross-sectional conditioning unpinned along three axes — the **lookback**, the
**rank-vs-divergence formulation**, and the **rebalance cadence / event definition** — plus the
unstated **universe-synchronization** rule needed to rank 16 instruments with heterogeneous trading
calendars (FX 24/5, crypto 24/7, cash indices session-bound) at a common timestamp. All four materially
change the event population and therefore the matched-random control and the realized cell count the D2b
admission gate is calibrated against (`C=46`), so they must be pinned **before** result-producing code,
on the record, to avoid a post-hoc goalpost. The operator ruled on all four at EXP-087 scoping.

## The freezes (binding for EXP-087 and the eventual CF-XSECT-001 family)

1. **Two conditioning primitives (mirrors the EXP-086 two-primitive clone structure).** Both are
   computed from the **same** 16-instrument cross-section; neither is tuned:
   - **`COND-XSRANK`** — at each domain timestamp, rank every instrument's trailing **20-domain-bar**
     real-price log return across the synchronized 16-instrument cross-section; an entry fires when the
     instrument enters the **top decile** (relative strength → **LONG**) or the **bottom decile**
     (relative weakness → **SHORT**). Ordinal cross-sectional rank.
   - **`COND-XSDIV`** — the same trailing 20-bar return **minus the equal-weight basket mean** across
     the synchronized cross-section; an entry fires on **extreme divergence** (top/bottom decile of the
     divergence distribution → LONG / SHORT). Continuous relative-strength deviation.
   Both are **directional** by construction (the cross-sectional anomaly is directional); the D3.X
   endpoint is the directional-favourable `MFE_med` Δ-over-random. The directional sign is taken from
   the rank/divergence tail (long the strong, short the weak) — this is the axis's information, not a
   tuned parameter.

2. **Lookback = 20 domain bars (both tails).** The momentum/divergence window is **20 bars** in each
   cell's own domain ({15m, 1h, 4h}); both extremes fire (long top-decile, short bottom-decile) for a
   symmetric directional-favourable read. Parameter-free otherwise. Causal: the rank at timestamp `t`
   uses only returns over bars completed strictly at or before `t`.

3. **Every-bar cadence on a forward-filled union timestamp grid.** The cross-sectional rank is
   recomputed **every domain bar** (no fixed rebalance throttle) on the **union** of all instruments'
   completed-bar timestamps at that domain; each instrument contributes its **last completed bar**
   (forward-fill, strictly causal — no look-ahead, no future bar consulted) when a timestamp falls
   between its own bar closes. An **event** is any (instrument, domain, timestamp) bar that enters the
   extreme decile. This matches EXP-081's per-bar availability read and preserves the like-for-like
   per-(instrument, domain) cell count against Screens M/F, so the bite-checked `C=46` admission gate
   applies as calibrated. The intersection-only grid (drop any timestamp lacking a completed bar for
   every instrument) was **rejected** — it discards crypto-weekend / off-session bars and shrinks 4h
   cells below the ≥30-event floor.

## Accounting (unchanged)

- These are the two conditioning primitives **within** the already-registered Screen-X axis
  (`X — CF-XSECT-001/HYP-001`, multiplicity-registry Phase 019 batch). They are **not** new countable
  axes — the axis is the countable selection unit; both the `COND-XSRANK` and `COND-XSDIV` reads sit
  inside it. **No new multiplicity-registry entry** is created by this amendment.
- **0 candidate slots, 0 counted TEST reads, holdout never touched** — unchanged. TRAIN sub-split only;
  the cross-section is built from each instrument's TRAIN region only, and the forward-fill consults no
  TEST/holdout bar.
- The D2b permuted-axis admission gate, its GREEN bite-check (report sha256 `208dfb3f…`), the realized
  cell count `C=46`, the FWER band, and the cross-axis Holm structure are **unchanged** — the gate is
  conditioning-agnostic by construction (it permutes the conditioning labels of whatever primitive is
  supplied, here the cross-sectional extreme-decile membership).

## Multiplicity caution carried (design §5, candidate-family §CF-XSECT-001)

Cross-sectional ranking over 16 instruments manufactures the **most** cells of any screen → the binding
D2b permuted-axis admission gate matters most here; a lucky single cell must not admit the axis. The
permuted-axis null shuffles which timestamps are "extreme-decile signal" within TRAIN, preserving
per-cell event counts, so it absorbs exactly this manufactured-cells multiplicity.

*Governing design: `design.md` §5 (EXP-087) · `D0-predeclarations.md` §D1/§D3.X · candidate family
`../../../signal-registry/candidate-families/family-selection-phase-019.md` (CF-XSECT-001).*
