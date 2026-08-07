## Gate problem first

`docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md` is **0 bytes** and untracked. B1–B5 text does not exist anywhere on disk. So I cannot confirm "B1 fixed / B2 fixed" as such — the only recoverable anchors are two test docstrings (`B1` = live `da_*.py` on emission path; `B5` = label ban too narrow) and `B3` markers that predate this review. B2/B4 are unrecoverable.

Handoff stop condition #9 fires on its own terms: *"Task 5 Claude review missing... no purge, no full four-cell run."* Completion log still says Task 5 `pending`.

What I did instead: full independent adversarial pass on the current code against R1–R5. Findings below stand regardless of what B1–B5 said.

---

# SPDR-024 MDE floor fix — delta re-review

## Verdict
**BLOCKED_NEEDS_OPERATOR**

## Executive summary
- Prior review artifact is empty; the gate has no evidence, so purge cannot be authorised on it.
- The two B-items I *can* trace are genuinely fixed: `da_*.py` quarantined and refusing to run; label ban widened past `_estimate_rows`.
- Core R2 fix is real: row floors now come from bootstrap SE of the same draws as the CI, on scale, per-symbol, and selection. `2.8/√blocks` is gone from row floors.
- R3, R4, R5 look substantively landed: no resolve labels, denominators declared, preflight on simulated fills against the R1 ceiling.
- Three residuals survive that would poison the re-emission, one of them in a HARD integrity control.

## Blocking findings

**BR-1 — tripwire leak-test skips half the declined population** — `spdr024_analysis.py:1399`
The selection tripwire filters `rejection_class == "EVALUATED_DECLINED"` only. The selection *emission* uses `DECLINED_CLASSES`, which also includes `EVALUATED_DECLINED_ORDER_EXPIRED` — and the code's own comment at `:885` says that expiry-decline is **the only decline a PENDING_EXPIRY arm makes**. Those arms get `n_declined == 0` → `applicable=False` → never leak-tested, while their emitted estimate is fully populated. The stated purpose ("the selection channel was previously never leak-tested") is not met for that arm class.
Fix: use `DECLINED_CLASSES` in the tripwire, same as the emission.

**BR-2 — parametric row-count floor still emitted inside selection rows** — `spdr024_analysis.py:1078`, `_two_sample_mde` at `:1141`
Each regime stratum in `regime_strata` carries `mde_bps = MDE_Z·σ·√(1/n_l + 1/n_r)`, computed on **raw row counts** — the call site passes no `n_left`/`n_right` block overrides, despite the docstring saying that is what they are for. That is D3.2's exact shape: an unblocked parametric floor sitting on the same emitted object as a bootstrap CI. A reader comparing a stratum contrast to its stratum floor is back on the old ladder.
Fix: derive stratum floors from the same bootstrap family, or drop `mde_bps` from `regime_strata` and emit counts only.

**BR-3 — R1 ceiling computed on a different outcome than the estimand** — `preflight.py:102-172`, `:224`
`_simulate_domain_fills` exits at `close[fill_i + 1]` — a **one-domain-bar hold**. `size_mechanism_ceiling` then takes `sharpe_per_trade` from that distribution. The production estimand is the capital-normalised episode return over the real cap-rule hold, which is materially longer (`FIXED_EXPIRY_BARS=2`, plus hold cap). Sharpe scales roughly √hold, so the ceiling is understated by that factor. Direction is conservative (more cells labelled `DESCRIPTIVE_...`), but the magnitude is wrong, and R5 requires the preflight endpoint to be the *same* endpoint as the post-run context.
Fix: hold the simulation to the cell's declared hold rule, or label the ceiling provisional with the scale factor disclosed in the JSON.

## Non-blocking findings

**NB-1 — two governing rules under one design clause** — `:483` vs `:915`
Scale governs by `max(mde_sigma)` (highest floor). Selection governs by `min(effective_blocks)`, width as tie-break. These do not coincide in general. The comment at `:912` asserts *"Same conservatism rule as the scale channel: fewest independent blocks wins"* — that is not what `governing_treatment` does. Design §11 states one rule; pick one implementation.

**NB-2 — per-symbol bootstrap cost is unmeasured** — `:656`
Per-symbol scale rows now run a real `clustered_interval` at `n_boot=2000` (previously a free `2.8/√n`). That is arms × 2 lenses × 3 regimes × n_symbols additional 2000-draw bootstraps per cell. Task 4's smoke was synthetic at small `n_boot`, so this cost has not been observed. Handoff's performance standard asks for wall-time deltas recorded before a four-cell run.

**NIT-1 — `interval_implied_se` (`:365`) is defined and never called.** Documented fallback, currently dead.

## Defect coverage matrix

| Item | Status | Evidence |
|---|---|---|
| D1 / R1 mechanism ceiling | PARTIAL | `size_mechanism_ceiling:372` correct as `√p·|μ|/σ`; input distribution wrong (BR-3) |
| D2 / retire Step-3 range | ADDRESSED | `STEP3_*` gone from `preflight.py` (test asserts source-level absence); survives only as labelled historical context in `analyse.py:248` |
| D3.1 / no pass mark on \|est\| | ADDRESSED | `contrast_over_mde` → `contrast_over_se:990`; collapse no longer MDE-gated `:1101`; tripwire `at_bite` renamed to integrity-bite-scale |
| D3.2 / R2 single SE family | PARTIAL | `row_floor_from_se:349` used at `:445`, `:668`, `:844`, tripwire both halves — but BR-2 |
| D4 / R4 channel scales | ADDRESSED | `sigma_denominator` = `paired_delta` (scale) / `outcome_level_bps` (selection), tested at `test_scale_and_selection_declare_distinct_denominators` |
| D5 / R5 preflight fills | PARTIAL | `count_basis: PROVISIONAL_DOMAIN_BAR_SIMULATED_FILLS`, `power_label_basis: FILLS_NOT_ORDERS`, endpoint `R1_SIZE_MECHANISM_CEILING`; but BR-3 |
| B1 (traceable) | FIXED | `analysis_code/` holds only `analyse.py`; `legacy_pre_a7/` scripts raise on import; test at `:402` |
| B5 (traceable) | FIXED | value + column denylist widened, `contrast_over_mde` explicitly banned; test at `:421` |
| B2, B3, B4 | **UNVERIFIABLE** | review artifact empty; no on-disk statement of the findings |

## Explicit non-findings
- No `band` / `resolution_class` / `WASH` / `UNPOWERED` / `CLEARS_FLOOR` anywhere in the emission path; `_selection_band` and siblings absent, asserted by `hasattr` checks.
- `MDE_Z/√n` in `preflight._planning_floor:97` is legitimate — pre-run planning, no bootstrap exists, and R3 sanctions exactly that use. Not a row floor.
- Scope intact: no arm/device/universe/cost/TEST change in the diff.
- `class`-suffixed columns (`breakeven_spread_class`, `BASELINE_CHARACTERISATION_...`) are population/scenario descriptors, not power labels.
- Tripwire `pass` criterion is still "non-vacuous shift and no surviving shifted edge"; collapse remains informative-only.

## Recommendation
Do **not** purge or start the four-cell run.

Two things needed, in this order:
1. **Operator call on the gate.** The Task 5 review produced no output. Either re-run it and land a real artifact, or waive it in writing in the handoff. As it stands the handoff's own stop condition #9 is active.
2. **Fix BR-1, BR-2, BR-3 under TDD** — all three are within AMENDMENT-7's scope, no new remedy needed, no research-scope change.

NB-1 and NB-2 can ride along or be waived. After that, a focused delta re-review of just those three sites is enough; a full re-review is not.
