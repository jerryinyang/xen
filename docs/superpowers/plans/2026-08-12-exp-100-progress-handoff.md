# EXP-100 Progress Handoff — AMENDMENT-8 locked; next = fresh QA

> **SUPERSEDED 2026-08-13.** Current resume:
> `docs/superpowers/plans/2026-08-13-exp-100-progress-handoff.md`.
> This file is the 2026-08-12 evening snapshot (AMENDMENT-8, 216 cells, 1h→1D).
> Do not use it to size the grid or choose confirmation clocks.

> Resume through the Xen `research-pipeline`. TEST/holdout remains forbidden.

**Experiment:** EXP-100 — Liquidity-sweep streaming apparatus  
**Family:** `CF-LIQSWP-001/HYP-000`  
**Checkpoint:** `2026-08-11-019-liquidity-sweeps`  
**Pipeline stage:** AMENDMENT-2…8 implemented in code + docs; **fresh QA required**

---

## One-line status

**AMENDMENT-8 is locked. Raid lifecycle is the original SoT grain (observation
bar). In-memory state plus that grain cut a full-TRAIN cell from ~2 h to a
projected ~3 min. Official execution is blocked only on a fresh-context QA
run, then the operator gate.**

---

## What the next session must do first

```text
1. Run qa-compliance on EXP-100 in THIS new session (fresh context).
   Append to python/experiments/EXP-100/qa-review.md. Do not rewrite old runs.
2. If APPROVE → stop and ask the operator whether to launch official
   preflight / the 216-cell TRAIN grid.
3. If REVISE → fix only the listed issues; do not reopen methodology.
4. Do not launch the 216-cell matrix from this handoff alone.
```

QA must judge the **current** object:

| Path | Binding grain |
|---|---|
| Raid start / return / beyond / same-bar ambiguity | Observation bar (15m / 30m / 1h) |
| Confirmation + later endpoint | 1H (15m/30m) or 1D (1h) |
| TPO bins, max-excursion reset, post-confirm swing | 1-minute |
| Engine input / later fills | 1-minute (AMENDMENT-3) |

Golden T1 is now a completed **observation** bar beyond the level, then a later
observation-bar return. A 1m wick that does not survive the observation OHLC
is not a raid.

---

## Binding methodology (do not relitigate)

| Item | Rule |
|---|---|
| AMENDMENT-6 | Close-all-eligible reference settlement |
| AMENDMENT-7 | cTrader only: EURUSD, XAUUSD, USTEC → **216** cells |
| AMENDMENT-8 | **NEUTRAL.** Locks the original SoT raid grain (bar-by-bar on the cell TF). Not a new estimand. Retires the later 1m over-spec. |
| Ledger | **0 looser / 3 tighter / 4 neutral** |
| Integrity | TRAIN only; no holdout; zero-cost |

AMENDMENT-8 is **not** “faster but degraded.” The SoT already said track
excursions bar by bar on the cell timeframe. Confirmation was never 1-minute.

---

## Performance (informal benches — not programme emission)

Same cell: EURUSD 15m BREAKOUT_BAR PREVIOUS_1H.

| Window | Old 1m-lifecycle + SQLite | After in-memory store | After AMENDMENT-8 grain |
|---|---:|---:|---:|
| 30 days | ~67 s | 8.9 s | **3.4 s** |
| 1 year | hours-scale | 202 s | **66 s** |
| Full TRAIN (~2.5 y) | **~2 h** | ~8 min | **~3 min projected** |

216 × ~3 min serial ≈ **11 hours**. A few workers puts a grid in a few hours.

**What actually moved the needle**

1. In-memory live state (killed per-minute SQLite/JSON).  
2. O(1) memory estimate (full bin scan every minute was most of a 30-day profile).  
3. Raid/level on the observation TF (SoT grain; fewer objects, cheaper loop).

**Storage rewrite was equivalent** (30-day in-memory vs in-memory+path-slim:
zero raid/TPO field diffs). Observation-TF vs 1m-lifecycle is **not**
equivalent — and that is intended.

**Leftover hot path** if cells must go well under a minute: 1m TPO bin increment
+ Decimal bin index. Native port is optional after QA, not a blocker.

Informal benches: `/tmp/exp100-mem-bench/`  
Stale old full-TRAIN SQLite bench: `/tmp/exp100-fulltrain-bench/` (ignore).

---

## Pipeline position

```text
1 Design .............. DONE for AMENDMENT-2…8
2 QA pre-exec ......... STALE — run now in the new session
3 Execute ............. BLOCKED on QA APPROVE + operator gate
4 Estimand gate ....... per cell when execution resumes
5 Analysis / docs ..... NOT STARTED
```

---

## 216-cell grid (unchanged)

```text
3 assets × 3 timeframes × 2 confirm methods × 12 level configs = 216
```

| Axis | Values |
|---|---|
| Assets | EURUSD, XAUUSD, USTEC |
| TF | 15m, 30m, 1h (refs 1H / 1H / 1D) |
| Method | BREAKOUT_BAR, LEVEL_CLOSE |
| Level | PREVIOUS_1H/4H/1D/1W, PREVIOUS_ASIA/EUROPE/AMERICA, ROLLING_16/32/64/128/256 |

Parallelism is approved in principle. Re-measure peak RSS after QA before
setting worker count (old SQLite cells were ~0.2–0.4 GB; 1.5 GB hard cap).

---

## Out of scope unless the operator amends again

- Changing AMENDMENT-6/7/8 raid lifetime or raid grain silently  
- TEST / holdout  
- Treating old QA runs 4–8 as current (they describe the 1m raid path)  
- Opening the 216-cell matrix without fresh QA APPROVE + operator approval

---

## Key paths

| Role | Path |
|---|---|
| This handoff | `docs/superpowers/plans/2026-08-12-exp-100-progress-handoff.md` |
| QA skill | `.agents/skills/qa-compliance/SKILL.md` |
| QA log (append-only) | `python/experiments/EXP-100/qa-review.md` |
| Processor | `python/src/xen/exp100/processor.py` |
| State / TPO | `python/src/xen/exp100/state_store.py`, `tpo.py` |
| Matrix / runner | `python/experiments/EXP-100/code/run_matrix.py`, `run_experiment.py` |
| Checkpoint / SoT | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/` |
| Family card | `docs/signal-registry/candidate-families/cf-liqswp-001.md` |
| EXP designs | `python/experiments/EXP-10{0,1,2,3,4}/design.md` |

---

## Changelog

| When | What |
|---|---|
| 2026-08-12 | Bybit preflight TIMEOUT; open-raid pile-up diagnosed. |
| 2026-08-12 | Storage opts; close-all probe; AMENDMENT-6/7 implemented; cTrader 30-day ~67 s. |
| 2026-08-12 | Operator: few-hour target; parallel workers wanted; 216 grid documented. |
| 2026-08-12 | Full-TRAIN SQLite bench ~2 h/cell; operator rejected “stable but slow.” |
| 2026-08-12 | In-memory live state; 30-day 8.9 s; 1-year 202 s. Storage rewrite equivalent. |
| 2026-08-12 | Raid lifecycle moved to observation TF. 30-day 3.4 s; 1-year 66 s. |
| 2026-08-12 | **AMENDMENT-8 locked (NEUTRAL):** original SoT grain. Docs updated. |
| 2026-08-12 | **Next session: fresh QA, then operator execution gate.** |
