# Chapter 02 Rollover — mr-volharv-htfdi (closed 2026-07-09)

**Theme.** Mean-reversion arc (CF-MR-002..005), volatility harvest (CF-VOLHARV-001),
cross-sectional residual reversion (CF-CSRR-001), HTF-DI conditioning (CF-HTFDI-001), plus
the referee renewal (E-series, §10.3a q\*=0.75 + P\* gate + 15m domain). Seven family arcs,
all closed negative with mechanisms recorded; 0 counted TEST reads spent this chapter except
EXP-016's 3 (SPENT_ON_DEFECT, critical-017); holdout sealed throughout.

## Phase 1 — Extract

KB files updated (append-merged, commit `e7ff457`):
- `families-explored.md` — chapter-02 disposition table (8 rows) + updated availability frame.
- `pitfalls-ledger.md` — P-10..P-15 (passive-limit MR capture, per-leg ladder CIs,
  rebalance/grid harvest, consensus-residual reversion, HTF-DI magnitude, screen-seam units).
- `methodology-canon.md` — chapter-02 additions (SPDR lane, unit pin, spread leg, amendment
  ledger, seed batteries, block ≥ H, symmetric selection, exposure-honest reads, equal-info
  fade tiering, native orders, event-mass match, controlled thesis-shopping).
- `evaluation-framework.md` — chapter-02 renewed referee section (frozen form, hash pins,
  variant-c refutation, INFR-004 hardening, L-17 open blind spot).
- `data-architecture.md` — INFR-005 10-symbol indices basket.
- `INDEX.md` — chapter-02 scope + archive pointer.
- `memory/` — 3 new atomic facts (renewed-referee-frozen, spdr-speed-run-lane,
  unit-pin-money-floor) + MEMORY.md pointers.

Lessons L-13..L-24 were already codified in `lessons-and-amendments.md` during the chapter
(each with mechanism); L-22/L-23/L-24 gained explicit "Where enforced" lines at Renew.

## Phase 2 — Archive

All moves `git mv` (history verified via `git log --follow` on EXP-025/report.md);
tag **`chapter-02-close`**.

- `experiments/` — EXP-001..025 (+014b/c), SPDR-001..003, VAL-006/007, chapter INDEX.md.
- `experiments-docs/` — master INDEX, `families/` (7), `checkpoints/` (11).
- `ctrader-cli/` — all chapter `.conf` (EXAMPLE.conf kept live), `reports/` (340M run
  outputs, untracked), `run-exp014c-all.sh`, `run-exp019-all.sh`.
- `src-archived/` — full `python/src/xen` snapshot; live tree pruned (operator-confirmed) of
  `cross_domain_mr.py`, `cross_sectional.py`, `move_position.py`, `reversion_targets.py`.
  No contaminated modules this chapter (engine exonerated at EXP-025).
- `strategyhost-archived/` — thesis cBot partials (`Xen.BothLeg/RandomHold/StructureHarvest/
  HtfDiNative.cs`), thesis models (`CrossDomainMrLimitModel`, `HtfDiBreakoutModel`,
  `CrossInstrumentSpreadPlanner`, `WilderHtfState`, `AvwapBounceModel`, `RsiFadeModel`), and
  `Xen.cs.chapter02-full` (pre-strip snapshot). Live `Xen.cs` stripped to the neutral core
  (StrategyHost / TimeBars / Parity; MaCrossover + Donchian20 benchmarks); NativeOrders mode
  and all thesis wiring removed; `archive/**/*.cs` excluded from compile.
  **Verified: `dotnet build` 0 errors; `pytest` 35/35 pass.**

Kept live: `docs/knowledge-base/`, `docs/signal-registry/` (untouched), generic collection
scripts + `run-experiment.sh`, neutral `python/src/xen` core, StrategyHost runner/writers/
generators.

## Phase 3 — Renew

Change-set (operator-selected): **codify the EXP-025 seam checks (L-21..L-24) as enforced
pipeline checks.**

| Item | Files touched | Enforced at |
|---|---|---|
| L-21 unit pin + money floor | (already enforced pre-rollover) | `quant-designer/references/design-requirements.md` §9 CONVERSION-PIN + `qa-compliance/SKILL.md` §3 clause; `docs/references/spdr-lane.md` |
| L-22 spread verdict leg | `design-requirements.md` §10 (new) | QA §3 L-22 clause — commission-only band on 0-commission instrument = REVISE |
| L-23 amendment-direction ledger | `design-requirements.md` §11 (new) | QA §3 L-23 clause — direction + running count + final-gate false-qualifier re-derivation; ≥3 one-directional streak = operator flag |
| L-24 eligibility/null rules (F02/F04/F06/F07) | `design-requirements.md` §12 (new) | QA §3 L-24 clause-trace (time-stability eligibility, exit-matched nulls, derived tripwire thresholds, MDE-consistent read floors) |

KB propagation: "Where enforced" lines added to L-22/L-23/L-24 in
`docs/knowledge-base/lessons-and-amendments.md`.

Guardrails: holdout untouched all phases; signal-registry (multiplicity + test-read ledgers)
never reset; no evaluation logic changed.

## Verification

`verify_rollover.py --root . --chapter 02` — see final rollover commit for output.
