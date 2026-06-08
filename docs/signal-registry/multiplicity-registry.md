# Phase 004 Multiplicity Registry

**Status:** ACTIVE - Batch 004-A registered; EXP-020 substrate gate supported; no full candidate screened.
**Opened:** 2026-06-07
**Governing phase:** `docs/experiments-docs/checkpoints/2026-06-07-004-avwap-signal-exploration/design.md`

## Purpose

This file is the Phase 004 programme-level file-drawer ledger. The frozen
three-component suite controls per-candidate qualification error; this registry
controls the programme risk created by trying many candidates, variants, or
definitions and only remembering the winners.

No Phase 004 candidate screening is admissible unless the candidate family,
hypothesis, parameter branch, and EXP-ID appear here first.

## Frozen Qualification Suite

| Component | Source | Detection floor by domain |
| --- | --- | --- |
| Strict gate stack | EXP-003 / EXP-005 | 5m: 1 bps; 1h: 4 bps; 4h: 12 bps |
| Ratified-loose referee | EXP-012 | 5m: 0.5 bps; 1h: 2 bps; 4h: 8 bps |
| Revised portfolio-fitness unit | EXP-018 | 5m: 12 bps; 1h: 16 bps; 4h: 32 bps |

The suite is frozen. Phase 004 scopes may report all three components, but may
not retune thresholds, losses, costs, denominators, or pass logic after seeing
candidate outcomes.

## Batch 004-A Budget

| Field | Predeclared value |
| --- | --- |
| Candidate-family count | 1 |
| Candidate family | `CF-AVWAP-001` |
| First-branch trend detector | Simple MA crossover, fast 20 / slow 50, on domain `Close` |
| First-branch AVWAP weight | `TickVolume ** 0.75` |
| First-branch band rule | Median absolute deviation from the anchored typical-price series, multiplier 1.0 |
| Domains | 5m, 1h, 4h |
| Instruments | BTCUSD, EURUSD, USTEC, XAUUSD |
| Candidate-screening starts only after | EXP-020 substrate readiness, EXP-021 fixed-horizon reaction study, and EXP-022 original lifetime move study, if supported or explicitly ruled sufficient by governance |

The original band-target/trend-change lifetime method and brainstorming metric
book are part of Batch 004-A. Original non-baseline AVWAP concepts are
registered in `candidate-families/avwap.md`; each requires a dedicated scope and
EXP-ID before measurement. Unregistered exit overlays, position-management
rules, cross-timeframe variants, or separate signal families still require a
registry update before measurement.

## Candidate Ledger

| Candidate ID | Family | Hypothesis | EXP-ID | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| `CF-AVWAP-001/HYP-001` | Anchored VWAP on regime pivots | The frozen AVWAP definition can be built as a deterministic, look-ahead-safe event substrate with usable event coverage. | EXP-020 | SCREENED | SUPPORTED_FULL: readiness/substrate experiment supported on all three domains; not a market-edge claim; clears EXP-021/022 scoping. |
| `CF-AVWAP-001/HYP-002` | Anchored VWAP on regime pivots | AVWAP bounce events have better fixed-horizon direction-signed real-price reaction than matched non-event controls. | EXP-021 | PLANNED | Blocked until EXP-020 is supported or governance narrows domains; metric family is fixed in `candidate-families/avwap.md`. |
| `CF-AVWAP-001/HYP-003` | Anchored VWAP on regime pivots | Under the original band-target/trend-change lifetime definition, AVWAP bounces produce favorable completed-move outcomes. | EXP-022 | PLANNED | Blocked until EXP-020 is supported or governance narrows domains; lifetime metric family is fixed in `candidate-families/avwap.md`. |
| `CF-AVWAP-001/HYP-004` | Anchored VWAP on regime pivots | The baseline AVWAP signal can pass standalone or portfolio-fitness qualification under the frozen suite while reporting the original strategy metric book. | EXP-023 | PLANNED | Blocked until EXP-021 and EXP-022 are complete or governance records why one reaction operationalization is sufficient. |

## File-Drawer Ledger

No Phase 004 full candidate-screening result exists yet. Component results are recorded below.

| Date | Candidate ID | EXP-ID | Result | Disposition |
| --- | --- | --- | --- | --- |
| 2026-06-08 | `CF-AVWAP-001/HYP-001` | EXP-020 | SUPPORTED_FULL | Substrate readiness supported: all 12 cells reportable, all three domains ready, zero invariant violations, deterministic replay. Proceed to EXP-021/022 component scopes; no market-edge claim. |

## Amendment Rules

An amendment is required before measurement if any of these change:

- adding a candidate family;
- adding an AVWAP variant or alternative trend detector;
- changing MA windows, volume exponent, band multiplier, bounce definition, or
  domains;
- changing the reference book used for portfolio-fitness screening;
- changing the registered EXP-021 fixed-horizon reaction metric family;
- changing the registered EXP-022 lifetime completion or metric family;
- dropping the original metric book from EXP-023;
- changing the planned EXP sequence or result gates;
- allowing an implementation to screen a candidate before its component
  characterization experiment is complete.

Amendments must state whether the changed item consumes a new multiplicity slot.
