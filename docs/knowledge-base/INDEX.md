# Xen Knowledge Base — Read First

The curated, cross-chapter canon for the Xen research programme. Distilled from Chapter 01
(~98 experiments, ~25 phases), Chapter 02 (EXP-001–025 + SPDR-001..003, 11 phases,
2026-06-27 → 2026-07-09; seven family arcs, all closed negative with mechanisms recorded),
and Chapter 03 (XENA-001..003 + INFR-006..009, 2026-07-09 → 2026-07-14; first live XENA
portfolio universes, CF-MTFCTX-001 retired, referee redesigned and route restored), and
Chapter 04 (INFR-010..020, VAL-008, SPDR-004..009 and three candidate families,
2026-07-14 → 2026-07-22; Nautilus/Bybit migration, exact taker-side volume, and the first
full signed-auction investigation).
Read this **before** designing any new experiment: it records what is frozen, what is dead,
what worked, and the lessons that cost a false positive to learn.

This KB is canonical and **append-merged** at every chapter rollover (new chapters add/update;
they do not wipe prior canon). The **signal-registry** (`docs/signal-registry/`) is the *live*
operational ledger (multiplicity, test-reads, candidate families) and is referenced here, not
copied — it persists across chapters and must never be reset.

## Programme status (2026-07-22): Chapter 04 archived; Chapter 05 blocked on preflight

The NautilusTrader/Bybit stack is operational and VAL-008 passed 39/39 reconciliation and
leak checks. Chapter 04 then closed three candidate arcs: **CF-EPSOSC-001 RETIRED—REFUTED**
(volatility-window clustering and AKRO drift, not armed reversion), **CF-HTFCAP-001
CLOSED—CHARACTERISED** (real BTC high-volatility directional gross effect; 0/72 cells net),
and **CF-SIGAUC-001 CLOSED** (price spine, signed trap load and D1 signed absorption all null
against their binding controls). Only XENA-HTFCAP-001 touched TEST, as an explicitly
exploratory read with no reserved OOS. A disclosed INFR-017 path scanned one univariate
spread-quality column beyond the fence; it exposed no price, return, P&L or signal and the
operator cleared it with zero sanctioned reads consumed. The global holdout remains formally
sealed, with that disclosure permanent.

The durable data gain is exchange-native **taker buy/sell volume** with raw-trade provenance.
The durable economic warning is that stored `SpreadBps` is **not executable spread**: it is a
mean-print differential, is often negative, and is pinned `UNUSABLE`. No exact net claim may
use it. The repeated material gross source is directional drift/continuation amplified by
high volatility; no Chapter-04 implementation established deployable net edge. See
[data-architecture.md](data-architecture.md), [evaluation-framework.md](evaluation-framework.md),
and [families-explored.md](families-explored.md).

Chapter 05 may test one bounded volatility-to-direction conversion object, but no family may be
registered and no outcome-bearing work may begin until the cost/data preflight passes focused tests
and fresh-context QA. The approved route is one TRAIN-only SPDR characterisation followed, only if
authorised, by one frozen Nautilus EXP; XENA and historical TEST are excluded. Enforcement lives in
[`chapter-05-governance.md`](../references/chapter-05-governance.md) and the active
[`experiments-docs/INDEX.md`](../experiments-docs/INDEX.md). The mechanism is sequencing: invalid
cost composition or an unusable spread field would make the economic front gate meaningless, so
infrastructure correctness must precede family registration and outcome contact.

## What's FROZEN (do not re-derive)

- **Evaluation governance** — validity failures remain hard stops; value, significance,
  power and selection are reported as complete frozen-arm distributions for operator judgement,
  never automatic winner gates. Historical frozen referees remain calibration evidence, not a
  licence to hide cells. See [evaluation-framework.md](evaluation-framework.md).
- **The active data layer** — NautilusTrader, global calendar fence, Bybit USDT-perp OHLCV,
  exact taker-side volume, deterministic derived views and emission reconciliation. Raw
  `SpreadBps` is excluded from costs. See [data-architecture.md](data-architecture.md).
- **Holdout fences** — both sanctioned legacy FX/indices holdout shots are SPENT (EXP-032 and
  EXP-097). The current Bybit global-calendar holdout remained sealed through Chapter 04.
  Never load any holdout outside a separately sanctioned, governed release; archived-data
  obligations do not expire.

## What's OPEN / what's DEAD

- [families-explored.md](families-explored.md) — every candidate family + disposition, and the
  **availability 2×2** that frames the open frontier.
- [pitfalls-ledger.md](pitfalls-ledger.md) — refuted directions and dead ends; do not re-run.
- Chapter-04 boundary: exact signed volume is now an established input, but the tested S3/S9
  transforms added no marginal directional value. The surviving product question is whether an
  intentionally directional, risk-managed volatility/trend exposure can clear exact intraday
  costs—not whether drift can be defined away as a nuisance control.
- [reviews/capture-geometry-review.md](reviews/capture-geometry-review.md) — cross-chapter
  extraction of every **capture geometry / exit** modality tried against "availability exists,
  cannot capture"; mechanisms, observations, Mode A/B/C failure taxonomy, independent-review
  checklist.
- [reviews/capture-geometry-recommendations.md](reviews/capture-geometry-recommendations.md) —
  diagnosis + design recommendations: proven cores, proven ineffective, genuine gaps, C0–C3
  capture stack and four-layer D0 contract.
- [reviews/unsigned-failed-break-bounce-review.md](reviews/unsigned-failed-break-bounce-review.md)
  — standalone viability of the one CF-SIGAUC-001 object that clears its cost floor, stripped of
  the dead signed claim. Reproduces on PVA/PRIOR only (IB is a day-weighting artifact), but the
  lift is **+5–11% relative** over matched-random on an **MFE ceiling with no realized return ever
  computed**, MFE:MAE ≈ 1.35:1, and 81% STOP under the only exit tested. **Characterisation, not a
  candidate** — re-opening needs a new information source (P-01).

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
- `archive/chapter-04-nautilus-bybit-sigauc/` — Chapter 04 experiments, complete
  experiments-docs, source snapshot and deprecated tests; active neutral source was restored from
  this snapshot.
