# Chapter 06 Research Status

## Current checkpoint status

**No checkpoint is open. No family is registered.** Chapter 06 begins on a clean slate after the
chapter-05 rollover (2026-08-07).

Read `docs/knowledge-base/INDEX.md` before designing anything.

## Standing constraints (carried across the rollover, not re-litigated)

- **Spread is never charged programme-wide** (2026-07-23). Reported cost understates total cost;
  reported net is overstated. Every money, expectancy, tradability and deployability claim is
  refused **by rule**, not by pending work. Lifting this needs a real executable-spread source,
  not a proxy — staging `SpreadBps` is pinned `UNUSABLE`.
- **Holdout fences.** Both sanctioned legacy FX/indices shots are SPENT. The Bybit
  global-calendar holdout is sealed. Never load any holdout outside a separately sanctioned,
  governed release.
- **Ledgers persist and are never reset** — `docs/signal-registry/multiplicity-registry.md`,
  `test-read-ledger.md` (cap 2 counted reads per stratum, lifetime),
  `candidate-families/`.
- **Detection floors follow AMENDMENT-7** (`L-56`): a floor is built from the same SE family as
  the row's own CI; every channel declares its `sigma_denominator` and channels with different
  denominators are never ranked on one ladder; no row is dropped or labelled by its floor; and
  where the estimand's ceiling is algebraically knowable it is computed **per cell in the design**
  with the implied sample requirement. See `docs/knowledge-base/evaluation-framework.md`
  § *Detection floors*.
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
