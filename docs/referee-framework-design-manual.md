# Xen Referee / Evaluation Framework — Design Manual

**Purpose.** A complete, neutral description of the *frozen* Xen referee — the gate that decides
whether a candidate trading signal has a real, material, tradable edge. Written as an unbiased
reference for external auditors: it states the architecture and the exact mechanics, and nothing
else. Strengths/weaknesses, problem statements, improvement proposals, and open design questions are
**deliberately excluded** and live in the companion document
`docs/referee-framework-assessment.md`.

Canonical sources this manual distils:
- `docs/knowledge-base/evaluation-framework.md` (frozen-facts summary)
- `python/src/xen/referee_calibration.py` (5-check gate stack + shared primitives)
- `python/src/xen/incremental_referee.py` (portfolio-fitness / incremental unit)

Where this manual and the code disagree, **the code is authoritative**.

---

## 0. One-paragraph summary

The referee is a **frozen three-component suite**. Each component is a **conjunction of
fixed-threshold legs** evaluated on a chronological train/test split with a stationary block
bootstrap, charging a frozen per-instrument round-trip cost. The suite was calibrated (Phases
001–003b, EXP-001–019) to a measured false-positive rate of ≈0 and was verified end-to-end on a
dogfood-negative (must reject) plus a synthetic-positive (must pass). A fourth, parallel vehicle —
the event-level method (EXP-027) — handles sparse signals.

---

## 1. Architecture: the frozen three-component suite

| Component | Source experiments | Detection floor (MDE) by domain | Binding question |
|---|---|---|---|
| **Strict 5-check gate stack** | EXP-003 / EXP-005 | 5m 1 bps · 1h 4 bps · 4h 12 bps | Does a standalone per-bar signal have a real, material, cost-surviving edge vs neutral and vs a naive control? |
| **Ratified-loose referee** | EXP-011 / EXP-012 | 5m 0.5 bps · 1h 2 bps · 4h 8 bps | Same gate at a lower materiality threshold τ, ratified on fresh draws (ADOPT_LOOSE all domains). |
| **Revised portfolio-fitness / incremental unit** | EXP-013–019 | 5m 12 bps · 1h 16 bps · 4h 32 bps | Does candidate C add **incremental net edge beyond** a reference signal R already in the book? |

A candidate may be reported against all three; the binding component depends on the scope. The
**event-level method** (EXP-027) is a fourth, parallel vehicle for *sparse* signals (§6) — it is not
one of the three frozen per-bar components but is part of the same canon.

**MDE = minimum detectable (net) effect** — the smallest planted edge the component reliably passes
at FPR≈0 (EXP-005 DETECTED_FLOOR).

---

## 2. Shared statistical substrate (all components)

All defined in `referee_calibration.py`.

- **Split discipline.** Data is sliced to the first 70% (analysis set); within it a 70/30
  chronological train/test split. The split boundary is fixed once on the canonical 1-minute base as
  a **wall-clock timestamp** (`train_end_ts`) and every resampled domain inherits the *same*
  timestamp — never a per-timeframe row fraction (`domain_split_index`, `resolve_split_index`). The
  final 30% global holdout is never loaded.
- **Returns.** Close-to-close next-step log returns per domain bar (`next_log_returns_from_bars`).
  (The Chapter-02 standing execution convention elsewhere in the programme is open-to-open on
  confirmed bars `≤ t-1`; the frozen Chapter-01 referee uses close-to-close.)
- **Cost model.** Frozen per-instrument round-trip bps, charged on every active bar
  (`strategy_return_bps`, `ROUND_TRIP_COST_BPS`): EURUSD 1.0 · XAUUSD 3.0 · BTCUSD 10.0 · USTEC 4.0
  (all domains).
- **Block bootstrap.** Stationary (Politis–Romano) block bootstrap of the sample mean
  (`block_bootstrap_means`). Block length = first ACF lag dropping below 1/e, estimated on the
  **train** segment (`estimate_block_length`). CIs are percentile intervals on the **test** segment's
  bootstrap-mean distribution (`ci_from_means`). The same bootstrap-mean distribution is reused
  across the α grid (only the percentile cut changes).
- **Effective sample size.** `effective_n = len(test) / block_length` — counts independent *blocks*
  (episodes), not raw bars. Drives the L1 readiness leg.
- **α grid.** {0.10, 0.05, 0.01}. **Materiality base** (`MATERIALITY_BPS`): 5m 0.5 · 1h 1.5 · 4h 3.0.
- **Domain readiness specs** (`DOMAIN_SPECS`): min effective-n and min per-direction episode count —
  5m (120, 30) · 1h (60, 20) · 4h (25, 8); 1h/4h additionally require ≥0.90 bar coverage.
- **Calibration edge grid** (`EDGE_GRID_BPS`): {0, 0.5, 1, 2, 4, 8, 12, 16, 24, 32} — the planted
  net edges used to measure each component's MDE and FPR.

---

## 3. Component A — the 5-check gate stack

`gate_stack_core` / `gate_stack_row`. Five legs, conjoined (`passed = L1 ∧ L2 ∧ L3 ∧ L4 ∧ L5`).

| Leg | Code name | Definition (as implemented) | α-dependent? |
|---|---|---|---|
| **L1** | readiness | `effective_n ≥ min_effective_n` **and** min(train_up, train_down, test_up, test_down) episodes `≥ min_state_count` | no |
| **L2** | integrity | hard-coded `True` (placeholder in this implementation) | no |
| **L3** | outcome | neutral CI lower `> 0` **and** vs-naive-control CI lower `> 0` (beats both a zero baseline and a naive prior-return-sign control) | yes |
| **L4** | stability | mean(train net) `> 0` **and** mean(test net) `> 0` (direction holds in both segments) | no |
| **L5** | materiality | neutral CI lower `> materiality_bps` (the economic floor) | yes |

The naive control (L3) is the sign of the prior return aligned to the next bar
(`naive_momentum_positions`).

Naming note (factual): `evaluation-framework.md` labels the five legs *readiness /
standalone-significance / CI-vs-naive / direction / materiality*; the implementation folds
standalone-significance and CI-vs-naive into `L3_outcome` and renders `L2_integrity = True`. The
table above reflects the implemented logic (authoritative).

**Calibration facts (EXP-003/005/006/008/010/011/012):**
- Gate-stack **FPR ≈ 0** at every domain/α; the conjunction drives FPR from ≈α down to ≈0 at a
  larger economic MDE than the minimal single-leg baseline.
- **L5 materiality is the binding, α-invariant leg** — it sets the gate MDE; the α grid only moves
  the minimal baseline.
- Lowering the materiality threshold τ (strict → loose) reduces MDE (1/4/12 → 0.5/2/8 bps) with FPR
  still ≈0 (EXP-006); the loose point was **ratified on fresh draws** (EXP-012).
- **Per-instrument MDEs run below the pooled map** (EXP-008: EURUSD/1h 2 vs 4; EURUSD & XAUUSD/4h 8
  vs 12).

---

## 4. Component B — the revised portfolio-fitness / incremental unit

`incremental_referee.py`. Judges a candidate **C** by the **incremental net edge it adds to a book
already holding a reference signal R** — the economic reading is *portfolio fitness of a single
candidate* (it is not a multi-asset book-level evaluator).

**Mechanics.**
- **Marginal net P&L estimator** (`marginal_net_series`, model-free): combine positions additively
  then clip to the per-domain bound (`combined = clip(R + C, ±1)`); the marginal position is
  `m = combined − R`; evaluate `m` on **real** returns; charge **incremental** turnover cost only
  where C changes the book (`cost_bps / episode_length` per denominator bar). No linear / i.i.d. /
  stationarity model of the R–C relation is imposed.
- **Denominator** = bars where the combined book differs from R-alone (`m ≠ 0`).
- **Contiguous block length** (`_contiguous_block_length`): the block length is estimated on the
  full-length, time-contiguous marginal series (zeros off-denominator) rather than the gap-extracted
  denominator, so within-episode autocorrelation is preserved and `effective_n` counts independent
  *episodes* (adversarial-review fix F04).

**Revised legs** (`revised_incremental_gate_row`; `passed = L1 ∧ L3 ∧ L4' ∧ L5`):

| Leg | Definition |
|---|---|
| **L1** readiness | incremental denominator effective-n + both-direction episode counts, train and test |
| **L3** reference-control | incremental-beyond-R edge CI lower `> 0` (C significantly beats R, not just zero) |
| **L4'** no material sign reversal | the incremental edge does not *materially* flip sign across the two segments (immaterial near-zero cost drag still confirms) |
| **L5** strict materiality | incremental edge CI lower `> materiality_bps` |

**History.** The *first* incremental unit (EXP-015) carried a standalone-C significance leg (L2) and
was **REFUTED** — that leg had no finite MDE in high-overlap synchronous-null cells (BTCUSD-driven).
The revised unit **drops L2** and was validated on accepted dependence cells (FPR controlled
126/126; finite worst-case MDEs 12/16/32 bps).

---

## 5. Calibration & freeze protocol

- **FPR side (known-negative).** Candidates with no planted edge (bar-permuted returns, random state
  positions) must reject at the target rate.
- **Power side (known-positive).** Edges planted at the `EDGE_GRID_BPS` levels via closed-form drift
  (`plant_positive_edge`) measure the MDE — the smallest edge reliably passed.
- **End-to-end (EXP-019).** The full suite was composed against a **dogfood-negative** (real-data
  null-shaped candidate that must reject across all domains) and a **synthetic-positive** (must pass
  all three components).
- **Governance rule.** The suite is **frozen**: report its components on any candidate; never retune
  thresholds, losses, costs, denominators, or pass logic after seeing a candidate's outcome. A
  redesign is itself a predeclared experiment, recalibrated on *fresh* dogfood/synthetic draws and
  frozen **before** it adjudicates any live candidate.

---

## 6. The event-level method (sparse signals)

The per-bar suite is calibrated for **≥80%-active** series. For sparse (~6%-active) event vehicles
the canon uses the **event-level method** (EXP-027, METHOD_VALID): per-event expectancy +
matched-control lifetime excess, regime-cluster bootstrap, Holm multiplicity correction. Standing
rule: match the evaluation vehicle to the signal's activity rate.

---

## 7. Anchors that bound interpretation

- **Lower/null anchor (EXP-004/009).** Untuned Donchian/MA and 6 broadened simple strategies carry
  no positive edge even gross (net medians ≈ −1 bps); simple intraday edges sit below every gate MDE.
- **Detection floor (EXP-005).** On a scoped realistic candidate the gate detects *at* the MDE with
  FPR 0 — the MDE map is an honest floor there.

---

## 8. Operational properties (measured)

These are measured properties of the frozen suite, stated without evaluation:
- **FPR ≈ 0** across domains and α, re-verified end-to-end (EXP-019).
- **Causal/streaming-safe primitives** — train-estimated block length, test-segment inference,
  timestamp-fixed splits.
- **Dependence-robust marginal estimator** (Component B) — model-free; shared structure does not
  produce a phantom positive.
- **Quantified power floor** — MDE maps are explicit; per-instrument MDEs run below the pooled map
  (EXP-008).
- **Deterministic** — fixed seeding throughout; one bootstrap distribution reused across α.

---

*End of design manual. Authoritative code references: `python/src/xen/referee_calibration.py`,
`python/src/xen/incremental_referee.py`. Frozen-facts summary:
`docs/knowledge-base/evaluation-framework.md`. Assessment, weaknesses, and improvement proposals:
`docs/referee-framework-assessment.md`.*
