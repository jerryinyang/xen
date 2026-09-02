# Chapter 06 Experiment Index

Chapter 06 checkpoint 019 is **closed**. `CF-LIQSWP-001` is **retired —
characterised, not tradable** (2026-09-02). EXP-100 apparatus retained with
ATR-undefined exclusion. EXP-101–104 leftover tables are winner-only; VAL-009–011
record the selection/anatomy caveats. AMENDMENT-17 was not computed.

Before designing anything, read `docs/knowledge-base/INDEX.md` — in particular
`lessons-and-amendments.md` (mechanisms, not just symptoms) and `pitfalls-ledger.md` (do not
re-run these).

## Infrastructure (ad-hoc)

| ID | Status | Purpose |
|---|---|---|
| INFR-022 | COMPLETE (2026-08-08) | Programme-wide update: zero-cost model, neutrality standard (N1–N11), powering strip (no MDE/floors), PSR pairing — all lanes. Plan: `docs/superpowers/plans/2026-08-08-infr-022-zero-cost-neutrality-psr-pipeline-update.md` (Task 5 review §13; Task 6 sign-off) |

## Chapter 06 — active

| ID | Family | Status | Purpose |
|---|---|---|---|
| EXP-100 | CF-LIQSWP-001 | COMPLETED — OPERATOR-APPROVED | Current 264-cell TRAIN run retained; ATR-undefined excursion values excluded, unaffected apparatus findings retained |
| EXP-101 | CF-LIQSWP-001 | INCONCLUSIVE — winner-only slice; checkpoint closed | Strong-move rate falls on some windows; not a live-raid object |
| EXP-102 | CF-LIQSWP-001 | COMPLETED — descriptive ATR/strong-move; winner-only | Later winners usually leave a smaller leftover; duration does not confirm |
| EXP-103 | CF-LIQSWP-001 | INCONCLUSIVE — winner-only slice; checkpoint closed | Tight-gap leftovers often smaller in ATR; rare arm; duration does not separate |
| EXP-104 | CF-LIQSWP-001 | COMPLETED — descriptive ATR/strong-move; winner-only | Calm leftovers larger, wild smaller; clock and start-rate disagree |
| VAL-009 | CF-LIQSWP-001 | COMPLETED — characterisation | Completed primaries ~8%; confirmed-not-primary ~44% |
| VAL-010 | CF-LIQSWP-001 | COMPLETED — characterisation | Repeat drop is larger first push / smaller leftover, not duration |
| VAL-011 | CF-LIQSWP-001 | COMPLETED — characterisation | HIGH starts more raids; leftover ATR weaker; duration the other way |

## Carried in from Chapter 05

- **No additional family carried in from Chapter 05.** `CF-VOLDIR-001` was retired 2026-08-07
  as *characterised, not tradable*; `CF-VOLCONV-001` is closed. Prior chapters' families are
  all closed or retired — see `docs/knowledge-base/families-explored.md`.
- **Do not open a family whose thesis is that a better exit, hold, trail or size rule converts a
  break-even joint into a positive one.** That class is refuted at power (chapter-05 §"What
  Chapter 05 changed about the frame"). `W/L` is ~97% the arithmetic mirror of `p`.
- **Zero-cost model (INFR-022).** No spread, commission, or swap enters any calculation in
  any experiment type unless an explicit operator cost directive requests costs (recorded in
  the design + `operator_cost_directive.json`). The ZERO-COST-DISCLOSURE caveat appears on
  every money-bearing artifact. Deployability/tradability claims stay refused by rule.
- **No research powering (INFR-022).** Sample-size context + direct baseline comparison only;
  MDE/floors/power curves/UNPOWERED labels are retired. PSR (`psr` + `psr_n`, same series)
  pairs every mean-trade/leg bps read. Neutrality N1–N11 binds every analysis/screen/report
  (`docs/references/neutrality-standard.md`).
- **Both sanctioned legacy holdout shots are spent**; the Bybit global-calendar holdout is sealed.
- **Ledgers persist and are never reset:** `docs/signal-registry/multiplicity-registry.md`,
  `test-read-ledger.md`, `candidate-families/`.

## Archived

Chapter 05 (`INFR-021`, `SPDR-011..024`, checkpoints 016/017/018):
`archive/chapter-05-voldir-capture-geometry/`. Raw Nautilus emissions were purged at the rollover
as regenerable from pinned code; analysis artefacts, self-checks, preflight and performance
records are retained.
