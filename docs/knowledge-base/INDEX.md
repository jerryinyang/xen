# Xen Knowledge Base — Read First

The curated, cross-chapter canon for the Xen research programme. Distilled from Chapter 01
(~98 experiments, ~25 phases) and Chapter 02 (EXP-001–025 + SPDR-001..003, 11 phases,
2026-06-27 → 2026-07-09; seven family arcs, all closed negative with mechanisms recorded).
Read this **before** designing any new experiment: it records what is frozen, what is dead,
what worked, and the lessons that cost a false positive to learn.

This KB is canonical and **append-merged** at every chapter rollover (new chapters add/update;
they do not wipe prior canon). The **signal-registry** (`docs/signal-registry/`) is the *live*
operational ledger (multiplicity, test-reads, candidate families) and is referenced here, not
copied — it persists across chapters and must never be reset.

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
