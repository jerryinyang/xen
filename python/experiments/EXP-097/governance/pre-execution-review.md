# EXP-097 — Pre-Execution Governance Review (Stage 4)

**Experiment:** EXP-097 — Global-Holdout Release: One-Shot OOS-Final Confirmation (RSI-2 Fade Deployment Portfolio)
**Phase:** 022 · **Family/HYP:** `CF-MR-001`/`HYP-003` · **Date:** 2026-06-25
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py` · **Against:** the bundled
governance constraints + the G-022a freeze ([`G-022a-gate-criteria.md`], [`G-022-gate-criteria.md`]).

> **This is the gate immediately before the single sanctioned global-holdout shot is spent.** The review verifies
> the read reads *exactly* what G-022a froze, that the holdout is touched once and only here, and that the rule is
> frozen so the verdict cannot be reverse-engineered after the read.

---

## Verdict

```text
VERDICT: APPROVE
```

All governance constraints pass. The implementation reads exactly the G-022a-frozen set / construction / primary /
band / rule; the holdout is loaded once (here, first touch); the binding statistic is the verbatim m*-calibrated
function; and the verdict logic is frozen and mechanical. No Critical or Warning issues.

---

## Frozen-rule fidelity (the central check at this gate)

| Frozen item (G-022a) | Implementation | OK? |
| --- | --- | --- |
| Deployable set = carry-8 | `CELLS = E96.CELLS` (the 8 G-021-confirmed cells), reused unchanged | ✓ |
| Construction = binding-v2 ERC + intra-1h MTM, verbatim | `E96.resolve_cell_noise` (v2 stream) + `E95.build_grid` + `PF.build_portfolio` with the EXP-095/096 frozen kwargs (LW-90d, weekly, 10% vol, 1.5× cap, trailing-50 breaker); seed `20260624` | ✓ |
| A-vs-B = both on one read; primary = B; no OR | `adjudicate_g022` keys off B only; A computed from the same materialization, disclosed; `verdict.json` records `no_OR_rescue` | ✓ |
| Band = inherited A4 m\* (A 1.75 / B 2.00) | `BAND = {"A":1.75,"B":2.00}` hard-frozen; `confirm()` applies `Sharpe_LB > band AND Calmar_LB > 0` | ✓ |
| Binding statistic = the m\*-calibrated function | `E95.series_risk_metrics` reused verbatim (same function that produced the analysis LBs + m\* calibration) — **not** re-implemented | ✓ |
| Terminal rubric | `DEPLOYABLE_CONFIRMED iff CONFIRM(B)`; `DECAYED iff Sharpe_pt(B) ≤ 2.00 OR Sharpe_LB(B) ≤ 0`; else `INCONCLUSIVE` — exactly G-022 §2 | ✓ |

**No goalpost can move after the read:** the set, construction, primary, band, and rule are all hard-coded /
inherited constants frozen *before* the holdout is loaded; nothing is data-derived from the holdout.

## OOS-holdout discipline (§5; the sanctioned exception)

- **EXP-097 is the one experiment that loads the final-30% holdout** — by G-022a design. `load_full_1m` is the
  sole loader (full file `[0, total)`); `run_metadata.json` records `global_holdout_shot_spent=true`,
  `holdout_first_touch=EXP-097`, `holdout_untouched=false`, per-file holdout row counts. No second holdout pass.
- **Holdout-region honesty:** the binding metric is computed on `grid_epochs ≥ H` (`H = max per-cell analysis
  cutoff`) — so **no analysis-set return enters the holdout statistic**; the ~2-day transition zone is
  conservatively excluded. The analysis set is loaded as **past-only causal warmup** (indicators, trailing
  covariance/vol, breaker mean, weight history) — not a new read (EXP-093 pattern). The binding metric n
  (~78 weeks) matches the m\* calibration n.

## Look-ahead / causality (§6) — PASS

Weights/cov/vol/cap/breaker at any grid timestamp consume only returns resolved strictly before it (continuous
causal `build_portfolio`); the v2 entry fill uses only 1-minute bars at/after the signal close. Two assertions are
**exercised in the holdout region**: `causal_weight_holdout` (perturb after a holdout rebalance → weight
unchanged) and `causal_fill_holdout` (perturb a pre-signal 1m bar of a holdout event → fill unchanged). Alignment
by `CloseTime` epoch / `searchsorted`, never bar index.

## Read accounting (§3 / D0 §D7) — PASS, ratified

EXP-097 is the **single sanctioned global-holdout release** — one holdout-governance event (à la EXP-032),
**outside** the analysis-TEST 48-stratum ledger (the 11 carried strata stay 1/2; `counted_test_reads=0`);
**0 candidate slots**; non-repeatable / non-upgradable. Per the operator decision 2026-06-25, **reading both A and
B from one materialization is ONE read** — governance-honest because both are weightings of the same streams from a
single materialization, the A-vs-B choice was fixed pre-holdout (no tuning), and the terminal verdict keys off B
only (no OR-multiplicity). The holdout-governance event must be recorded in `test-read-ledger.md` +
`multiplicity-registry.md` in the **same change** as the result (Stage 7).

## Other constraints — PASS

- **Real-price discipline:** real domain & 1-minute OHLC; entry/exit fills are real touched prices; no HA/Renko.
- **Per-stratum doctrine (LESSON-001):** per-cell holdout outcomes + masking disclosed alongside the primary-B
  portfolio estimand; A co-reported; no collapsed boolean is the binding verdict.
- **Determinism:** seeds off master `20260624`; `determinism_replay` (full build) + a binding-statistic re-seed
  identity check; second pass byte-identical.
- **Complexity budget:** 1 binding test + descriptive companions; 5 plots; 0 new modules. Within budget.
- **Code standards:** sectioned; output dirs in orchestration only; lazy Polars; `tqdm`; concise logging;
  NaN/zero-baseline guarded; compiles + imports clean (verified).

## Info notes (non-blocking)
- **I1 — full-file collect.** `load_full_1m` collects the whole sorted file (~1.87M rows/cell) — necessary (the
  holdout is the read); 8-column schema, bounded. Not a memory concern at this scale.
- **I2 — two ratifiable lines.** primary=B and carry-8 are the G-022a-frozen defaults; the operator may flip
  either before launch (a one-line change). Recorded; both default forward.
- **I3 — holdout exclusion exception.** This experiment intentionally loads the holdout (the sanctioned shot) — the
  one place the "never load the holdout" rule is suspended, by G-022a design and recorded as the single event.

---

## Manual execution gate (the operator launches this)

This read **spends the programme's single new-dataset global-holdout shot — irreversible, non-repeatable,
non-upgradable.** Confirm primary=B and carry-8 (or flip before launch). On approval to run:

```text
cd python && uv run python experiments/EXP-097/code/run_experiment.py
```

Expected outputs: `python/experiments/EXP-097/results/` (verdict.json, holdout_metrics.csv, per_cell_holdout.csv,
holdout_boundary.json, shrinkage.json, mtm_conservation.csv, portfolio_returns_A/B.csv, run_metadata.json) + 5
plots. After the run, the holdout-governance event is recorded in `test-read-ledger.md` +
`multiplicity-registry.md` (Stage 7), and the terminal G-022 verdict is read from the frozen rubric.
