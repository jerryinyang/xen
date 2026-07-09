# Phase 010 — HTF-DI Conditioning (SPDR CTRL-01/02/03 series) — SPDR speed-run screen

**Opened / closed:** 2026-07-08 (single-sitting SPDR series; screen-only, no counted reads).
**Lane:** SPDR (speed-run availability screen) — `docs/references/spdr-lane.md`. TRAIN-only,
0 TEST reads, 0 holdout touch, no engine execution, no estimand gate. **This checkpoint is the
phase container for the three SPDR legs; it does not itself spend any budget.**
**Origin idea:** `origin-mtf.md` (verbatim `mtf.md`, operator, 2026-07-07).
**Binding output:** `synthesis.md` (cross-leg synthesis + operator disposition, operator-signed).

## What this phase is

A three-leg SPDR series screening one thesis from `origin-mtf.md`:

> **Higher-timeframe context (DI direction, ADX strength, ATR vol) gives credibility to
> lower-timeframe decisions** — does HTF context carry its own conditional effect on the LTF
> forward-return distribution, and does it hold across base-strategy type?

Three control bases were the measurement instruments (not candidates):

| Leg | Dir | Base (CTRL) | Role |
|---|---|---|---|
| **SPDR-001** | `python/experiments/SPDR-001/` | CTRL-01 RANDOM entry | null-by-construction base → **cleanest HTF isolation** (`E[sign·m]=0`) |
| **SPDR-002** | `python/experiments/SPDR-002/` | CTRL-02 naive momentum | informative base; HTF as own conditional effect + base-failure characterised |
| **SPDR-003** | `python/experiments/SPDR-003/` | CTRL-03 naive reversion (causal m1 limit fill) | informative base; slow-domain fade coupling; base tail-eaten signature |

Each leg ran a fresh-context data-analyst pass **blind of the others** (only the causal primitives
were reused) — so cross-leg agreement in `synthesis.md` is genuine replication. Full per-stratum
magnitude tables, plots, and analysis live in each leg's own directory (canonical SPDR home per
lane spec; the legs remain indexed in `python/experiments/INDEX.md`).

## Series disposition (operator-signed 2026-07-08; CORRECTED same day post-audit)

> An independent audit + correction probe (`correction/`) superseded the original two-thread
> disposition: SPDR-001's CIs were under-blocked for its overlapping estimand, and SPDR-003's
> headline fade cell was a mislabelled side-signed interaction. See `synthesis.md` (corrected,
> binding) and `correction/correction.md`.

**WORTH_EXPLORING** — graduate HTF-DI **continuation** as a **single thread**:

- **Thread A (sole thread):** HTF-DI continuation — **USTEC 1h/5min** (replicated across two blind
  bases; CI-clear at every hold under hold-matched blocks; corrected breadth 9+/0−). EURUSD 1d/1h
  demoted to a power-up candidate stratum (point +0.27→+0.47, no CI-clear hold). BTC 1h/5min
  discounted (repackaged LTF autocorr).
- **Thread B (fade) — WITHDRAWN / NOT SUPPORTED (corrected evidence):** no CI-clear fade-signed
  cell on the corrected grid; XAU −0.86 was a strategy × DI interaction (raw-move −0.083 n.s.,
  half-unstable); the year-split probe ran at the correction and failed.
- **Separate line (NOT this verdict):** tail-managed naive base exploration (both informative bases
  median-positive / tail-killed).

Routes to a **full cTrader-primary experiment + candidate-family registration** under the
corrected `synthesis.md` §7 design constraints. Family registered: **CF-HTFDI-001**
(`docs/signal-registry/candidate-families/cf-htfdi-001.md`, corrected to single-thread).

## Integrity (SPDR code-asserted substitute — all three legs)

TRAIN-only fence (first 70%×70%), causal `t-1` lag, HTF-bar-boundary (`CloseTime < Open(t)`),
≥25-seed matched random battery, no local P&L accounting (L-18), holdout/TEST untouched — all
`integrity.json` all-pass per leg (see each `analysis.md` §Integrity gate). **0 slots, 0 counted
TEST reads, holdout sealed.**

## Pointers

- `synthesis.md` — the binding cross-leg read + full disposition (§1 axes, §2 continuation,
  §3 fade, §4 breadth+causal corroboration, §5 caveats, §6 tail lever, §7 design constraints,
  §8 disposition).
- `origin-mtf.md` — the source idea.
- Per-leg analysis: `python/experiments/SPDR-00{1,2,3}/analysis.md` (binding), `screen.md`
  (neutral, subordinate), `design.md`, `results/`, `plots/`.
