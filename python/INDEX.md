# Xen: Event-Based Price Aggregation Research

## Programme Direction

Xen compares event-based price aggregation methods (Line Break, Renko, Heiken Ashi) against traditional time bars to understand their trading-relevant characteristics. The programme proceeds in phases, each with a checkpoint in `docs/experiments-docs/checkpoints/`.

**Current phase:** 001 — Chart-Type Validation
**Phase design:** `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`

## Architecture

- **Data collection:** cAlgo robot collects completed 1-minute time bars
- **Chart-type generation:** Python generators produce Line Break, Renko, Heiken Ashi on-demand
- **Analysis:** Python experiments in `python/experiments/`
- **Architecture reference:** `docs/references/architecture.md`
- **Dataset reference:** `docs/references/dataset-reference.md`

## Key Constraints

- All strategy returns evaluated on time-matched real prices (synthetic price discipline)
- Chart-type generators must be deterministic and streaming-compatible
- No look-ahead bias in any generation or analysis
- Non-parametric methods by default
- Final 30% global holdout never used
