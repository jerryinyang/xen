# Xen Knowledge Base — Read First

The curated, cross-chapter canon for the Xen research programme. Distilled from Chapter 01
(~98 experiments, ~25 phases), Chapter 02 (EXP-001–025 + SPDR-001..003, 11 phases,
2026-06-27 → 2026-07-09; seven family arcs, all closed negative with mechanisms recorded),
and Chapter 03 (XENA-001..003 + INFR-006..009, 2026-07-09 → 2026-07-14; first live XENA
portfolio universes, CF-MTFCTX-001 retired, referee redesigned and route restored).
Read this **before** designing any new experiment: it records what is frozen, what is dead,
what worked, and the lessons that cost a false positive to learn.

This KB is canonical and **append-merged** at every chapter rollover (new chapters add/update;
they do not wipe prior canon). The **signal-registry** (`docs/signal-registry/`) is the *live*
operational ledger (multiplicity, test-reads, candidate families) and is referenced here, not
copied — it persists across chapters and must never be reset.

## Programme status (2026-07-14): INFR-010 migration in progress

The substrate is being replaced (`python/experiments/INFR-010/design.md`): engine → **NautilusTrader**,
primary data → **Bybit USDT-perp 1m OHLCV derived from trades archives** (full universe incl.
delisted, anti-survivorship). Chapter 04 research opens only after the migration's end-to-end
VAL (Phase D). Governance principles (holdout fence, causal-by-construction execution, estimand
gate, XENA adjudication form, multiplicity/test-read ledgers) carry forward; implementations
rebind at INFR-012. The XENA frozen registry is **VOID on the new stack** — fresh CAL cycle
required. See [data-architecture.md](data-architecture.md) (migration banner) and
[evaluation-framework.md](evaluation-framework.md).

## What's FROZEN (do not re-derive)

- **The evaluation/referee suite** — the Chapter-02 **renewed §10.3a gate (q\*=0.75) + E6
  P\*-gate + E7 15m domain**, hash-pinned; plus the Chapter-01 5-check stack it dominated and
  the per-domain MDE maps. See [evaluation-framework.md](evaluation-framework.md). Reusing it
  is mandatory; retuning it after seeing a candidate's outcome is a governance violation.
- **The data layer** — 1-minute time-bar base, deterministic derived views, the cTrader
  strategy-host contract, the holdout fence. See [data-architecture.md](data-architecture.md).
- **The global holdout** — final 30% per file. One sanctioned read existed per dataset; both
  are SPENT (EXP-032 old dataset; EXP-097 new dataset). Never load it outside a sanctioned,
  governed release.

## What's OPEN / what's DEAD

- [families-explored.md](families-explored.md) — every candidate family + disposition, and the
  **availability 2×2** that frames the open frontier.
- [pitfalls-ledger.md](pitfalls-ledger.md) — refuted directions and dead ends; do not re-run.

## How to work

- [methodology-canon.md](methodology-canon.md) — the methods that earned their keep
  (availability-screen-first, matched-random controls, multiplicity-adjusted admission gates,
  per-stratum non-pooling, inverted-inference predeclaration) and the ones that wasted effort.
- [lessons-and-amendments.md](lessons-and-amendments.md) — **the most important file.** Every
  observation that forced an amendment, each with its **mechanism (why)**. The look-ahead that
  shipped a false `DEPLOYABLE_CONFIRMED` is lesson L-01.

## Project memory

- [memory/MEMORY.md](memory/MEMORY.md) — atomic, append-as-you-go facts (one per file),
  the lightweight companion to this curated canon.

## Live operational ledgers (not part of the KB; referenced)

- `docs/signal-registry/multiplicity-registry.md` — programme file-drawer ledger.
- `docs/signal-registry/test-read-ledger.md` — per-stratum counted-read budget (cap 2/stratum).
- `docs/signal-registry/candidate-families/` — per-family registration + status.

## Archived chapter material

- `archive/chapter-01-*/` — the full Chapter 01 experiments, family indexes, checkpoints, and
  reflections. Reachable for convention reference; not loaded by default.
- `archive/chapter-02-mr-volharv-htfdi/` — the full Chapter 02 experiments (EXP-001–025,
  SPDR-001..003, VAL-006/007), experiments-docs, thesis-specific cBots, and run tooling.
- `archive/chapter-03-xena-mtfctx/` — the full Chapter 03 experiments (XENA-001..003,
  INFR-006..009), experiments-docs (checkpoints 011/012), and the **retired cTrader stack**
  (Xen.cs, StrategyHost/, tools/ctrader-cli/) archived at the INFR-010 migration.
