# Chapter 03 Rollover — xena-mtfctx (closed 2026-07-14)

**Theme.** First live XENA portfolio-adjudication universes (XENA-001..003, CF-MTFCTX-001)
plus the referee arc they forced: INFR-006 (frozen v3 lane) → live-scale MACHINERY-ALARM →
INFR-009 redesign (exit-(c) two-stage binder, DUAL_CERTIFY, route RESTORED 2026-07-14) with
INFR-007/008 as the Rust oracle-kernel amendments. One family arc, RETIRED on
substrate-exhaustion; 0 gate slots and 0 counted TEST reads spent the whole chapter; holdout
never loaded. Executed as **Phase 0 of INFR-010** (engine/data migration master plan,
design §6; operator-approved 2026-07-14).

## Phase 1 — Extract (commit `c519a08`)

- `families-explored.md` — chapter-03 dispositions (CF-MTFCTX-001 RETIRED with the
  confound-vs-grounds distinction; INFR-006→009 referee row) + frontier update (the INFR-010
  data pivot as the answer to the terminal branch).
- `evaluation-framework.md` — chapter-03 XENA section: (c) binder canon, pin `db87dc1a…`,
  net 1.0 bps injection, CAL discipline, L-25/26/27 pointers, VOID-on-new-stack boundary,
  Rust fold one-platform rule.
- `methodology-canon.md` — chapter-03 additions (portfolio-selection default, gross-vs-spread
  pre-search check, n_null sizing, bank split + binder-form pivots, leg resampling, cost-bound
  objectives).
- `INDEX.md` — chapter-03 scope + archive pointer.
- `memory/` — `xena-pc-binder-pin.md` + MEMORY.md pointer.
- **Checkpoint-012 retrospective finalized** (`experiments-docs/checkpoints/
  2026-07-13-012-xena-referee-redesign/retrospective.md`) — the INFR-009 P3→P5 arc.
- Stale `python/experiments/INDEX.md` INFR-009 row corrected (IN PROGRESS → COMPLETE
  2026-07-14, route RESTORED).
- L-25/L-26/L-27 + P-10 fifth vehicle were already ratified into the KB at the ckpt-011
  retrospective (2026-07-14, pre-rollover).

## Phase 2 — Archive (commit `1834248`, all moves `git mv`; history verified via
`git log --follow` on INFR-009/report.md)

- `experiments/` — XENA-001..003, INFR-006..009, chapter INDEX.md. **INFR-010 stays live.**
- `experiments-docs/` — master INDEX, `checkpoints/` (011, 012), `families/` (cf-mtfctx-001).
- `ctrader-stack/` — **the retired engine**: `Xen.cs`, `Xen.NativeReversion.cs`,
  `StrategyHost/` (runner, generators, writers, models), `tools/ctrader-cli/` (tagged, dead;
  INFR-010 §5). Left at root: `Xen.csproj`/`Xen.sln` (inert cTrader scaffolding),
  `tools/{darwinex,HtfDiSmoke,StrategyHostParity}` (not in the operator mandate; flag for a
  later sweep).
- `data/` — `timebars/` (815M FX/indices m1) + `strategy_runs/` (13G, untracked) moved on
  disk (gitignored). **Holdout obligations on that data remain binding forever.**
- **`python/src/xen` NOT pruned** (deviation from the generic procedure, per INFR-010 §5):
  `xen.evaluation`, `xen.adjudication`, `xen.xena.*` + `python/rust/xena_fold` carry forward
  wholesale; feed shims are rewritten at Phase C. No module was named a leak/bias source this
  chapter. Chart-type generator ports: dormant, on demand.
- Skeleton resets: fresh `python/experiments/INDEX.md` (INFR-010 the only live row) and
  `docs/experiments-docs/INDEX.md`; empty `checkpoints/`/`families/`.
- Kept live: `docs/knowledge-base/`, `docs/signal-registry/` (untouched — ledgers never
  reset), `python/` core, `INFR-010/`.
- Tag **`chapter-03-close`** at the rollover commit.

## Phase 3 — Renew

Change-set (operator-supplied): **the INFR-010 migration** — engine → NautilusTrader, primary
data → Bybit USDT-perp 1m OHLCV derived from trades archives (full universe incl. delisted,
anti-survivorship); MBP trio deferred.

| Item | Files touched | Mechanism recorded | Enforced at |
|---|---|---|---|
| Substrate migration banner (engine, data lanes, T1/T2 tiers, spread-scale routing, global calendar fence) | `docs/knowledge-base/data-architecture.md` (legacy layer demarcated) | anti-survivorship census; bar ≡ Σ trades; causal event sequencing ≠ C# | INFR-011 fence manifest + catalog wrapper (Phase A), INFR-010 Phase B determinism + emission contract, INFR-012 doc/skill rebind (Phase C), Phase D leak battery — per design §6; until a phase lands, its legacy counterpart is mechanism-reference only |
| Cost-model replacement notice (FTMO → Bybit fees + funding + T1 spread; discipline unchanged) | `docs/knowledge-base/evaluation-framework.md` | engine costless-honest + analyst injection + netted turnover carry | `xen.evaluation` new table at Phase C (INFR-012); routing rule into quant-designer/qa-compliance checklists at Phase C |
| XENA registry VOID on new stack | `evaluation-framework.md`, `memory/xena-pc-binder-pin.md` | calibration constants are engine+data-specific (L-25 class) | fresh predeclared CAL cycle required before any crypto universe (INFR-010 §8 R4) |
| Programme-status pointer + migration memory | `docs/knowledge-base/INDEX.md`, `memory/nautilus-bybit-migration.md` | chapter-04 gate = Phase D VAL | INFR-010 §6/§9 phase gates |

Guardrails: global holdout untouched all phases (archived FX/indices obligations restated as
binding); causal-by-construction preserved (vectorised-backtest ban re-expressed for
Nautilus); signal-registry multiplicity + test-read ledgers never reset.

## Verification

`verify_rollover.py --root . --chapter 03` — output recorded in the final rollover commit.
INFR-010 §6 Phase 0 verify: tag exists; KB INDEX updated; live tree carries only
forward-assets (+ flagged leftovers above).
