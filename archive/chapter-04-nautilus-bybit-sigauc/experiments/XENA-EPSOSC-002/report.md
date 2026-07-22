# XENA-EPSOSC-002 — report (CF-EPSOSC-001, Bybit VOLARM episode-fade, mass-aligned RET_ANCHOR)

**Status:** COMPLETE 2026-07-18 · **Operator verdict: NOT SUPPORTED (refuted).**
**Lane:** XENA · **Family:** CF-EPSOSC-001 · **Pin:** INFR-015 `abbb1842…` (CLS-EPISODE, LOW,
F*=16) · **Gate slots spent: 0/2 · Global holdout SEALED (never queried).**
**Predecessor:** XENA-EPSOSC-001 (top-1 REJECT; leak collapse 0.395; AKRO single-symbol drift).

## Research question
With the search band aligned to the VOLARM mass and the grid restricted to endogenous-clear
(RET_ANCHOR), does a **cross-symbol** portfolio (K≥3 distinct symbols, pooled n_legs ≥ 16)
certify under the pinned CLS-EPISODE binder (stage-2 gross LCB > 0), AND survive the derangement
tripwire after the directional-drift pedestal is subtracted (drift-adjusted collapse ≥ 0.5)?

**Mechanism (unchanged from 001):** after a confirmed vol-expansion-armed stretch, price reverts
toward the anchor within the episode; harvest as a one-sided market-entry fade cleared
endogenously (return-to-anchor only, no time cap). P&L object = the EPISODE.

## What 002 changed vs 001 (four fixes)
1. **Mass-aligned window** — TRAIN_START shifted to 2022-07-01 (plateau; predeclared search-band
   coverage floor 0.80, measured 0.842) so the pinned 50% search fraction lands on populated data.
2. **RET_ANCHOR-only grid** — HYBRID (time-cap) + STRETCH disclosure dropped (001 showed HYBRID's
   edge was drift). 19 symbols × 8 variants = 152 binding cells.
3. **K≥3 distinct-symbol certification** (AMENDMENT-1 TIGHTER) — post-rank filter after
   `certify_and_rank`; singleton/2-symbol finalists disclosure-only.
4. **Drift-twin pair + drift-adjusted derangement (HARD)** — matched-drift twin (random entry
   times) vs coin-flip twin (random side), to isolate/subtract the unconditional drift pedestal.

## Method
Nautilus BacktestNode emission (contract v1) under the catalog fence, strategy + features
byte-identical reuse of 001 restricted to RET_ANCHOR (`code/`, QA-approved). Shifted TRAIN
window [2022-07-01, 2023-12-18]; pinned SegmentLayout 0.5/0.25/0.2 → search 2022-07-01→2023-01-31,
ranking →2023-05-18, stage-2 gate 2023-09-02→2023-12-18. LAHC search (12 restarts, budget 200,
g_net) → `certify_and_rank` on ranking folds → K≥3 post-rank filter → pinned stage-2 studentized
gross LCB (`episode_overlap_rule_v1`, F*=16). Tripwire + drift-twin analyst-owned (`analysis_code/`).

## Integrity gates (all PASS)
| Gate | Result |
|---|---|
| Estimand validation v2 | **PASS** — `blocking_pass:true`, 152/152 cells, 19×8, 13 physicality flags (informative) |
| Provenance ≤ t−1 | PASS — arm on confirmed LTF ≤ t−1, entry next-bar RealOpen, causal membership |
| Leak tripwire non-vacuous | PASS — derangement moves the mean; drift-twin pair added |
| Holdout sealed | PASS — train_end 2023-12-18 < holdout_start 2025-01-08; no holdout path |
| Price-primary | PASS — Nautilus emission, non-STUB fence attestation |
| Shared-code boundary | PASS — `check_no_local_accounting(code/)` → ok |

## Key quantitative evidence

**Search:** eval_count **1898**, distinct restart terminals **12/12** (non-degenerate).
Raw top-1 = 2-symbol (1000BONK×2 + AKRO, medianF 58.5) and rank-1 = 2-symbol (AKRO+LEVER) —
**both correctly excluded by AMENDMENT-1**. Certified = rank-2, **4 distinct symbols**:
`10000LADYS_L, AKRO_S, LEVER_L, STMX_S`.

**Certified subset — stage-2 gate band (62 legs ≥ F*16):**
| Read | Value | Rule | Result |
|---|---|---|---|
| Pin stage-2 **gross LCB** (studentized, overlap-aware) | **−68.2 bps** | > 0 | **FAIL** |
| Pin stage-2 net LCB | −102.1 bps | > 0 | FAIL |
| Naive pooled mean (block-bootstrap 5-seed) | 94.5 bps, CI95 [68.3, 116.4] | — | positive (over-optimistic) |

The naive equal-weight bootstrap ignores episode-overlap + concentration; the pin's overlap-aware
LCB is the certification-relevant interval and is **negative**.

**Per-symbol gate-band gross (canonical, block-bootstrap CI95) — the story:**
| Symbol | n | mean bps | CI95 |
|---|---|---|---|
| AKROUSDT (S) | 10 | **450.1** | [372.8, 534.2] |
| 10000LADYS (L) | 16 | 171.1 | [34.1, 308.1] |
| LEVERUSDT (L) | 13 | 0.6 | [−83.2, 81.5] |
| STMXUSDT (S) | 23 | −60.2 | [−130.0, 10.6] |

Pooled positive is **AKRO drift + one positive name, diluted by two dead names** (LEVER/STMX,
36 of 62 legs, no edge). **001's single-symbol pedestal reproduced.**

**Tripwire + drift-twin (200 derangement + 200×2 twin seeds):**
| Quantity | Value | Rule | Result |
|---|---|---|---|
| live mean gross | 95.0 bps | — | — |
| raw collapse (arm-time derangement) | **0.091** | ≥ 0.5 | **FAIL** |
| drift-adjusted collapse | **0.135** | ≥ 0.5 | **FAIL** |
| matched-drift twin median (random entry) | 31.2 | — | — |
| coin-flip twin median (E[gross]=0 null) | 8.5 | ≈ 0 | ok |
| bite: live > P95 both twins | 95 < drift-P95 131.5 | — | no |

**Mechanism:** deranging among actual arm times barely moves the mean (86 vs 95) but uniformly
random entry times drop it to 31 → the edge is **volatility-window clustering, not arm→reversion
alignment**. No signal-conditioned reversion survives.

## Evidence for vs against
- **For:** pooled naive mean +94.5 (CI excludes 0); 62 legs (powered, MDE ~38 bps); 2/4 symbols
  positive; coin-flip null behaves (~0); search well-formed; AMENDMENT-1 excluded concentrated
  finalists.
- **Against (decisive):** pin stage-2 gross LCB −68 (no certification); derangement raw +
  drift-adjusted collapse both < 0.15 (edge not signal-conditioned); AKRO concentration = 001
  pedestal; live < matched-drift twin P95 (no bite).

## Verdicts
- **Analyst recommendation:** NOT SUPPORTED — refuted on both certification and tripwire legs.
- **Operator final verdict (2026-07-18): NOT SUPPORTED (accepted).** No TEST slot spent; holdout
  untouched. Experiment-level only — CF-EPSOSC-001 family status unchanged (checkpoint-level).

## Follow-ups (future experiments, not run here)
- AKRO's 450 bps likely the same 2023 directional drift as 001 — a per-episode sign/direction
  confirmation would close the pedestal question. A within-episode-clearing structure that is
  drift-decorrelated by construction would be a **new family**, not a re-open of CF-EPSOSC-001.
- Reusable caution logged: equal-weight block bootstrap is over-optimistic vs the overlap-aware
  studentized LCB on concentrated, overlapping cross-symbol subsets.

## Artifacts
`design.md` (FROZEN) · `qa-review.md` (APPROVE) · `code/{build_universe,run_batch,
run_search_certify,epsosc_strategy,features}.py` · `analysis_code/{tripwire_drift_twin,
canonical_reads}.py` · `results/{estimand_validation,search_certify_package,
derangement_tripwire,analyst_canonical_reads,power_table,freeze_diagnostics}.json` ·
`analysis.md`.

**Registry disposition:** evidence rows only — `multiplicity-registry.md` +
`candidate-families/cf-epsosc-001.md` (NO status transition); `xena-runs.md` close-out row.
No counted TEST read (`test-read-ledger.md` unchanged).
