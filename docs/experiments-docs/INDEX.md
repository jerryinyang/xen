# Chapter 06 Research Status

## Current checkpoint status

**Checkpoint 019 is open.** `CF-LIQSWP-001` is registered with five TRAIN-only
experiment designs. EXP-100 completed its AMENDMENT-13 analysis and now has an
operator-authorised AMENDMENT-14 full TRAIN rerun for one forward pre-MFE retracement field; its
operator upheld HYP-000. EXP-101–104 remain separate readiness items; their
fresh-context QA and operator progression gates are independent.

| Checkpoint | Family | Status | Design |
|---|---|---|---|
| `2026-08-11-019-liquidity-sweeps` | `CF-LIQSWP-001` | OPEN — EXP-100 HYP-000 upheld; EXP-101–104 readiness in progress | [`design.md`](checkpoints/2026-08-11-019-liquidity-sweeps/design.md) |

Read `docs/knowledge-base/INDEX.md` before designing anything.

## Standing constraints (carried across the rollover, not re-litigated)

- **INFR-022 (2026-08-08) — zero-cost model, powering strip, PSR, neutrality.**
  **Zero-cost**: no spread, commission, or swap enters any calculation in any experiment type
  (`cost_model: NO_COST_CHARGED`); the ZERO-COST-DISCLOSURE caveat appears verbatim on every
  money-bearing report/analysis/results artifact; a costed experiment requires an operator
  cost directive recorded in the design + `operator_cost_directive.json`. Deployability /
  tradability / expectancy claims remain refused **by rule** (the zero-cost model does not
  loosen this). **Powering strip**: no MDE / detection floors / power curves / UNPOWERED
  machine labels on the value path — sample-size context + direct baseline comparison only
  (L-63). **PSR** pairs every mean-trade/leg bps read (`psr` + `psr_n`, same series — L-64).
  **Neutrality**: N1–N11 (`docs/references/neutrality-standard.md`) bind every
  analysis/screen/report (L-65). Full authority:
  `docs/superpowers/plans/2026-08-08-infr-022-zero-cost-neutrality-psr-pipeline-update.md`.
  The chapter-05 no-spread amendment and AMENDMENT-7 floor apparatus are
  superseded-for-live-use (historical record).
- **Holdout fences.** Both sanctioned legacy FX/indices shots are SPENT. The Bybit
  global-calendar holdout is sealed. Never load any holdout outside a separately sanctioned,
  governed release.
- **Ledgers persist and are never reset** — `docs/signal-registry/multiplicity-registry.md`,
  `test-read-ledger.md` (cap 2 counted reads per stratum, lifetime),
  `candidate-families/`.
- **Sample-size context (INFR-022 L-63, supersedes the AMENDMENT-7 detection-floor rows):**
  every row is reported with its count; a design minimum-n for primary-inference language is
  descriptive only; every channel declares its `sigma_denominator` and channels with different
  denominators are never ranked on one ladder; no row is dropped or labelled by its count;
  where the estimand's ceiling is algebraically knowable it is computed **per cell in the
  design** as context. The leak tripwire's bite is `INTEGRITY_Z × bootstrap_SE` (N6b).
- **Emission minimums** established by SPDR-024 and now standard: realised state labelled at
  decision time whenever a design gates on that state (`E1`); counterfactual outcome carried for
  declined origins, never `0.0` (`E2`); a capital-normalised estimand for any sizing, exposure or
  capital-efficiency claim (`E6`).
- **HARD checks are reconciled by name AND by count** (`L-52`), every check depends on an emitted
  artifact, and every control carries a non-degeneracy assertion (`L-57`).

## Directory

- `checkpoints/` — one directory per checkpoint (`YYYY-MM-DD-NNN-slug/`), each with `design.md`
  and, at close, `retrospective.md`.
- `families/` — per-family working docs. Created as a chapter opens them.
- `reflections/` — mid-checkpoint operator reflections.

## Prior chapters

| Chapter | Arc | Archive |
|---|---|---|
| 05 | Structural volatility + direction; `CF-VOLDIR-001` retired characterised-not-tradable | `archive/chapter-05-voldir-capture-geometry/` |
| 04 | Nautilus/Bybit migration, signed auction; EPSOSC refuted, HTFCAP characterised, SIGAUC closed | `archive/chapter-04-nautilus-bybit-sigauc/` |
| 03 | XENA portfolio referee; `CF-MTFCTX-001` retired, route restored | `archive/chapter-03-xena-mtfctx/` |
| 02 | MR / vol-harvest / HTF-DI; seven family arcs closed negative | `archive/chapter-02-mr-volharv-htfdi/` |
| 01 | Price-geometry + referee construction | `archive/chapter-01-price-geometry-referee/` |
