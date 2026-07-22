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

## Programme status (2026-07-16): Chapter 04 open — INFR-010 migration COMPLETE

**INFR-010 Phases 0/A/B/C/D/E complete** (2026-07-16). Engine is **NautilusTrader**
(nautilus_trader==1.230.0); primary data is **Bybit USDT-perp 1m OHLCV** in `data/catalog/`
(894 ADMITTED instruments, fence PINNED). Phase D end-to-end VAL (**VAL-008**) operator
verdict **SUPPORTED / PASS**. Chapter 04 research is open at checkpoint-013
(`docs/experiments-docs/checkpoints/2026-07-16-013-chapter04-open-htfcap-epsosc-cal/`) —
CF-HTFCAP-001 + CF-EPSOSC-001 (SPDR→XENA) and INFR-014 (fresh Bybit XENA CAL). Stack lessons
L-28..L-31 ratified into [lessons-and-amendments.md](lessons-and-amendments.md). Governance
principles carry forward (holdout fence, causal-by-construction, estimand gate, XENA form,
multiplicity/test-read ledgers); rebind verified at INFR-012. The chapter-03 XENA frozen
registry remains **VOID on Bybit** until INFR-014 pins a new registry. See
[data-architecture.md](data-architecture.md) and [evaluation-framework.md](evaluation-framework.md).

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
