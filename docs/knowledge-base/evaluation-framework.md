# Evaluation / Referee Framework (Frozen)

Built and calibrated in Phases 001–003b (framework-referee family, EXP-001–019). **Frozen.**
Report its components on any candidate; never retune thresholds, losses, costs, denominators,
or pass logic after seeing a candidate's outcome. Full per-experiment cards:
`archive/chapter-01-*/docs/experiments-docs/families/framework-referee/INDEX.md`.

**Authoritative implementation (code wins on any disagreement):**
`python/src/xen/referee_calibration.py` (5-check gate stack + shared primitives),
`python/src/xen/incremental_referee.py` (portfolio-fitness / incremental unit).

## The frozen three-component suite

| Component | Source | Detection floor (MDE) by domain |
|---|---|---|
| **Strict 5-check gate stack** | EXP-003 / EXP-005 | 5m 1 bps · 1h 4 bps · 4h 12 bps |
| **Ratified-loose referee** | EXP-011 / EXP-012 | 5m 0.5 bps · 1h 2 bps · 4h 8 bps |
| **Revised portfolio-fitness unit** | EXP-018 | 5m 12 bps · 1h 16 bps · 4h 32 bps |

A candidate may be reported against all three; the binding gate depends on the scope.

## The 5-check gate stack (legs)

Legs **as implemented** (`gate_stack_core` / `gate_stack_row`); `passed = L1 ∧ L2 ∧ L3 ∧ L4 ∧ L5`:
- **L1 readiness** — `effective_n ≥ min_effective_n` **and** min(train_up, train_down, test_up,
  test_down) episodes `≥ min_state_count`.
- **L2 integrity** — hard-coded `True` (placeholder leg; carries no test in the frozen code).
- **L3 outcome** — neutral CI lower `> 0` **and** vs-naive-control CI lower `> 0` (folds
  standalone-significance and CI-vs-naive into one leg; beats both a zero baseline and a naive
  prior-return-sign control). α-dependent.
- **L4 stability** — mean(train net) `> 0` **and** mean(test net) `> 0` (direction holds in both
  segments).
- **L5 materiality** — neutral CI lower `> materiality_bps` (the economic floor, binding,
  α-invariant). τ scales the strict→loose threshold.

Key calibration facts:
- Gate-stack **FPR ≈ 0** at every domain/α (drives FPR from ≈α to 0), bought with a **2–8×
  larger economic MDE** vs the minimal baseline (EXP-003 keystone trade-off).
- **L5 materiality is the binding, α-invariant leg** — it sets the gate MDE; the α grid moves
  only the minimal baseline.
- Lowering τ reduces MDE (strict 1/4/12 → loose 0.5/2/8 bps) with FPR still 0 (EXP-006). The
  **loose point was ratified on fresh draws** (EXP-012, all domains ADOPT_LOOSE).
- Per-instrument MDEs can be lower than pooled (EXP-008: EURUSD/1h 2 vs 4; EURUSD & XAUUSD 4h
  8 vs 12) — the pooled map is conservative, not permissive.
- Split-protocol robust on 5m/1h; 4h alt-protocols give a *lower* MDE (OOS-sample-size effect,
  not a logic change) (EXP-010, corrected for a multi-fold CI artifact).

## Incremental / portfolio-fitness unit

EXP-013–019. The first incremental unit (EXP-015) was **REFUTED** (L2 standalone leg had no
finite MDE in high-overlap synchronous null_R cells, BTCUSD-driven). The **revised** unit
(drops standalone-L2; EXP-017/018) is validated on accepted dependence cells (FPR controlled
126/126; finite worst-case MDEs 12/16/32 bps). EXP-019 composed the full suite end-to-end
(dogfood negative rejects across all domains; synthetic positive passes all three components).

## Anchors that bound interpretation

- **Lower/null anchor (EXP-004, EXP-009):** untuned Donchian/MA and 6 broadened simple
  strategies carry no positive edge even gross; net medians ≈ −1 bps. Simple intraday edges sit
  **below every gate MDE** — so a gate rejection of a simple strategy is a true negative, but
  this only *bounds* structural blindness, it does not close it.
- **Detection floor (EXP-005):** on a scoped realistic candidate the gate detects at the MDE
  with FPR 0 (DETECTED_FLOOR) — the MDE map is an honest floor here, not evidence of blindness.

## Event-level method (sparse signals)

The per-bar suite is calibrated for **≥80%-active** series. A sparse (~6%-active) event signal
scored against a per-bar floor is dominated by denominator dilution (the EXP-023 framing
defect). For sparse event vehicles use the **event-level method** (EXP-027, METHOD_VALID:
per-event expectancy + matched-control lifetime excess, regime-cluster bootstrap, Holm). This
is a standing distinction — match the evaluation vehicle to the signal's activity rate.
See [lessons-and-amendments.md](lessons-and-amendments.md) L-04.
