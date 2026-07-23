# SPDR-012 — Volatility characterisation (placeholder)

- **Family:** `CF-VOLDIR-001`
- **Checkpoint:** `2026-07-23-017-structural-vol-direction-programme`
- **Status:** `DESIGN PENDING` — programme registered; this file is a stub until the full SPDR design
  freezes numeric reliability bars, horizons, and arm parameters.

**Authority:** do not execute until a complete SPDR-012 design replaces this stub and the operator
authorises the screen.

## Bound by

- Checkpoint: `docs/experiments-docs/checkpoints/2026-07-23-017-structural-vol-direction-programme/design.md` §5 Step A, §8.1
- Family: `docs/signal-registry/candidate-families/cf-voldir-001.md`
- RAW: `.ignore/what-next/alts/vol-direction-structural-programme-raw.md` §3 Step A, §5.1
- Lane: `docs/references/spdr-lane.md`

## Required content of the full design (do not thin)

1. Causal definitions for each axis arm V-PERSIST, V-LEVEL, V-REGIME, V-MEASURE, V-CLOCK, V-XS, V-TAIL.  
2. Predeclared reliability metrics and numeric PASS/STOP bars.  
3. TRAIN fence, DESIGN window, core symbols, lag ≤ t−1.  
4. Shuffle controls (time / label).  
5. Per-stratum reporting; no tradability claim; partial-cost caveat if any money unit appears.  
6. Disposition language: reliability PASS → open path to SPDR-013 combination eligibility; FAIL → stop
   vol-conditioned combination branch.
