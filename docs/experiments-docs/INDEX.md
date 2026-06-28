# Xen Experiments — Master Index (Chapter 02)

Live status + family navigation for the current chapter. Chapter 01 is archived at
`archive/chapter-01-price-geometry-referee/experiments-docs/`. Distilled canon:
`docs/knowledge-base/` (read first).

## Current Checkpoint Status
**Phase 001 — Referee-Gate Adaptivity + Causal RSI-2 Benchmark** — DRAFT, G0 PENDING (2026-06-27).
`checkpoints/2026-06-27-001-referee-adaptivity-rsi2-benchmark/design.md`. Dual purpose: (1) referee
renew (fix gate rigidity, KB L-12); (2) end-to-end benchmark of the rollover via the causal RSI-2
fade (CF-MR-002). 0 slots / 0 reads; global holdout sealed.

**Referee-renew E-series (D-referee):** **E1 — EXP-001 COMPLETE (2026-06-28, audit PASS).**
ACCOUNTING_MATERIAL: the frozen per-held-bar cost convention over-charges turnover ~L× on
persistent signals; amortizing (once per episode) recovers ΔMDE 1.0–11.5 bps/stratum (median 1.5),
scaling with cost & L. L-12 Mode-1 is partly accounting, not solely gate shape → scopes E3. Seam is
additive (`referee_adaptive.gate_stack_core_costfn`); frozen suite byte-unchanged. Next: E2
(non-constant plant), E3 (composite redesign adopting amortized accounting).

## Current Infrastructure Tasks
_(none)_

## Family Indexes
| Family | EXP range | Status |
|--------|-----------|--------|
| CF-MR-002 — causal RSI-2 fade (cTrader-primary) | _(EXP-IDs at promotion)_ | REGISTERED — G0 PENDING (Phase 001) |

## Checkpoint Retrospectives
_(none yet)_
