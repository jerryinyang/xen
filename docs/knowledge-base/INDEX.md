# Xen Knowledge Base — Read First

The curated, cross-chapter canon for the Xen research programme. Distilled from Chapter 01
(~98 experiments, ~25 phases), Chapter 02 (EXP-001–025 + SPDR-001..003, 11 phases,
2026-06-27 → 2026-07-09; seven family arcs, all closed negative with mechanisms recorded),
and Chapter 03 (XENA-001..003 + INFR-006..009, 2026-07-09 → 2026-07-14; first live XENA
portfolio universes, CF-MTFCTX-001 retired, referee redesigned and route restored), and
Chapter 04 (INFR-010..020, VAL-008, SPDR-004..009 and three candidate families,
2026-07-14 → 2026-07-22; Nautilus/Bybit migration, exact taker-side volume, and the first
full signed-auction investigation), and Chapter 05 (INFR-021, SPDR-011..024, checkpoints
016/017/018, 2026-07-22 → 2026-08-07; the structural volatility-and-direction programme powered
on two independent universes and retired — the chapter that established the joint `(p, W, L)`
sits at break-even and that `W/L` is not a free lever).
Read this **before** designing any new experiment: it records what is frozen, what is dead,
what worked, and the lessons that cost a false positive to learn.

> **INFR-022 (2026-08-08) — standing programme constraints (binding).** (1) **Zero-cost
> model**: no spread/commission/swap enters any calculation (`NO_COST_CHARGED`); ZERO-COST-
> DISCLOSURE caveat on every money-bearing artifact; a costed experiment requires a recorded
> operator cost directive. (2) **No research powering**: MDE/floors/power curves/UNPOWERED
> machine labels are stripped — sample-size context + direct baseline comparison only (L-63).
> (3) **PSR** beside every mean-trade/leg bps read, same series (L-64). (4) **Neutrality
> N1–N11** binds every analysis/screen/report (`docs/references/neutrality-standard.md`; L-65).
> Retired apparatus (CAL pins, AMENDMENT-7 floors, cost stack) is bannered historical record.
> Full authority: `docs/superpowers/plans/2026-08-08-infr-022-zero-cost-neutrality-psr-pipeline-update.md`.

This KB is canonical and **append-merged** at every chapter rollover (new chapters add/update;
they do not wipe prior canon). The **signal-registry** (`docs/signal-registry/`) is the *live*
operational ledger (multiplicity, test-reads, candidate families) and is referenced here, not
copied — it persists across chapters and must never be reset.

## Programme status (2026-08-07): Chapter 05 closed and archived; no family is open

**Chapter 05 is closed.** Checkpoints 016, 017 and 018 ran one family — `CF-VOLDIR-001`, the
structural volatility-and-direction programme — from registration to retirement across
`SPDR-011..024` and `INFR-021`, spending **0 counted TEST reads and 0 multiplicity slots**, with
`XENA-VOLDIR-001` reserved and never opened. The family is **`RETIRED — CHARACTERISED, NOT
TRADABLE`** (2026-08-07, operator-signed).

**What the chapter established, and it is structural rather than empirical.** The joint
`(p, W, L)` was powered on two independent universes — 25 Bybit USDT-perps and 3 cTrader
instruments sharing no venue, cost model or vendor — and it **sits at net break-even**: `0 of
1,413` powered crypto cells and `0 of 315` powered cTrader cells clear it, with **91–96% of the
distance being cost, not rate**. The reason it sits there is that **`W/L` is ~97% the arithmetic
mirror of `p`** (R² 0.9667 / 0.9746): exit geometry moves the payoff ratio 36–67× while the hit
rate moves inversely, leaving the mean unchanged. The capture programme's whole premise was that
this handle was independent. It is not. Every volatility-adaptive device tested on top either does
nothing measurable (hold), does less than its fixed counterpart (stop distance), gives back more
(trail), or has a consistent sign with a magnitude below its own detection floor after a
purpose-built experiment was run to measure it (size). See
[families-explored.md](families-explored.md).

**The transferable methodological output** is codified under **INFR-022**: sample-size context +
direct baseline comparison (L-63, retiring AMENDMENT-7 floors as live apparatus), neutrality N1–N11,
PSR pairing, and zero-cost. Historical detail: [evaluation-framework.md](evaluation-framework.md)
*Live evaluation frame* and [lessons-and-amendments.md](lessons-and-amendments.md) L-56 / L-62..65.

**Nothing is open.** Chapter 06 starts with no registered family. Two threads are parked as
terminal `NOT_RESOLVABLE` and must never be re-booked as refutations: **C2 shock-MOMO** and **C3**
(sample too thin in registered form). Live money reads are **gross under zero-cost** (L-62); do not
re-open cost-floor clearance as a disposition rule.

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

Chapter 05 is **closed and archived**. Live enforcement is
[`chapter-06-governance.md`](../references/chapter-06-governance.md) and
[`experiments-docs/INDEX.md`](../experiments-docs/INDEX.md). The programme frame is **INFR-022**
(zero-cost, powering strip, PSR, neutrality).

## What's FROZEN (do not re-derive)

- **INFR-022 programme frame** — zero-cost model; sample-size context + direct baseline
  comparison; PSR pairing; neutrality N1–N11
  ([neutrality-standard.md](../references/neutrality-standard.md)). The leak tripwire's
  integrity bite is `INTEGRITY_Z × bootstrap_SE` (N6b) — never an MDE. Historical
  detection-floor/CAL apparatus is superseded-for-live-use.
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
  — **HISTORICAL (pre-INFR-022):** standalone viability of the one CF-SIGAUC-001 object that
  historically cleared a cost floor, stripped of the dead signed claim. Reproduces on PVA/PRIOR
  only (IB is a day-weighting artifact), but the lift is **+5–11% relative** over matched-random
  on an **MFE ceiling with no realized return ever computed**, MFE:MAE ≈ 1.35:1, and 81% STOP under
  the only exit tested. **Characterisation, not a candidate** — re-opening needs a new information
  source (P-01). Live programme is zero-cost (L-62); do not treat cost-floor clearance as current
  disposition.

## How to work

- [methodology-canon.md](methodology-canon.md) — the methods that earned their keep
  (availability-screen-first, matched-random controls, multiplicity-adjusted admission gates,
  per-stratum non-pooling, inverted-inference predeclaration) and the ones that wasted effort.
- [lessons-and-amendments.md](lessons-and-amendments.md) — **the most important file.** Every
  observation that forced an amendment, each with its **mechanism (why)**. The look-ahead that
  shipped a false `DEPLOYABLE_CONFIRMED` is lesson L-01. Newest (INFR-022, 2026-08-08):
  **L-62** zero-cost model; **L-63** powering stripped to sample-size context + direct
  baseline comparison; **L-64** PSR pairing standard; **L-65** neutrality N1–N11. L-56 /
  AMENDMENT-7 are superseded-for-live-use (historical).

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
- `archive/chapter-05-voldir-capture-geometry/` — Chapter 05 experiments (`INFR-021`,
  `SPDR-011..024`), complete experiments-docs (checkpoints 016/017/018 with the 018
  retrospective, the SPDR-024 detection-floor defect record, and the 021/022/023 confirmation
  extraction), source snapshot, and `ROLLOVER.md`. **Raw Nautilus emissions were purged** at this
  rollover as regenerable from pinned code; analysis artefacts, self-checks, preflight and
  performance records are retained.
