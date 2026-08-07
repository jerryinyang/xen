# SPDR-024 MDE floor fix — Claude pre-run review (final gate)

**Verdict: READY_FOR_PURGE_AND_FULL_RUN.** Zero blocking. Review at `docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.delta2.md`.

Three prior blockers all cleared:
- **BR-1** tripwire now uses `DECLINED_CLASSES` (`spdr024_analysis.py:1399`), same as emission. Test at `test_spdr024.py:421`.
- **BR-2** `regime_strata` emits counts + means only, no `mde_bps` (`:1072-1079`). Test at `:431`.
- **BR-3** premise was wrong, not code: baseline holds exactly one domain bar 100% of rows (`design.md:249`), so preflight sim matches production. Now stated in code and in the emitted basis field.

Also re-checked: row floor is `MDE_Z × bootstrap_SE` everywhere on emission path (only surviving `MDE_Z/√n` is preflight planning, sanctioned by R3); no result labels; preflight endpoint is R1 ceiling; `legacy_pre_a7/` quarantine holds — all ten scripts raise on import.

Tests: **580 passed, 4 skipped** (`python -m pytest tests`). ruff clean.

Three non-blocking residuals:
1. `_two_sample_mde` now dead code — the exact forbidden shape, still in the module. Delete it.
2. Two stale sentences say governing = "fewest blocks"; code uses highest floor. Text only.
3. Per-symbol bootstrap cost never timed on real data. Time `ctrader_H1` first — schedule risk, not correctness. Do not cut draws.

One footgun: bare `pytest tests` from `python/` gives 3 collection ImportErrors (pre-existing `sys.path` artifact, unrelated). Use `python -m pytest` in Task 7/8 so it isn't misread as a regression.

---

# SPDR-024 MDE floor fix (AMENDMENT-7 R1–R5) — final pre-purge gate review

Date: 2026-08-07
Scope: delta re-review of the three blocking findings from
`2026-08-07-spdr-024-mde-floor-claude-review.delta1.md`, plus re-check of R2 floor form,
result-label ban, and preflight R1 endpoint. No production edits made. No hypothesis verdict.

## Verdict

**READY_FOR_PURGE_AND_FULL_RUN**

Blocking findings: **0**. Residuals below are all NON_BLOCKING.

## Prior blocking findings — status

| ID | Finding | Status | Evidence |
|---|---|---|---|
| BR-1 | Selection tripwire filtered `rejection_class == "EVALUATED_DECLINED"` only, so `PENDING_EXPIRY` arms (whose only decline is `EVALUATED_DECLINED_ORDER_EXPIRED`) were never leak-tested | **FIXED** | `spdr024_analysis.py:1399` now `pl.col("rejection_class").is_in(list(DECLINED_CLASSES))`, identical to the emission filter at `:888`. `DECLINED_CLASSES` at `:49` = both classes. Test `test_selection_tripwire_uses_all_declined_classes` (`test_spdr024.py:421`) asserts the constant is used *and* that the bare-string filter is absent from `tripwire_collapse` source. |
| BR-2 | `regime_strata` carried `mde_bps` = parametric two-sample floor on raw row counts, next to a bootstrap CI | **FIXED** | `_regime_matched_contrast` (`:1072-1079`) emits counts + means + `contrast_bps` only; explicit comment "No parametric row-count floor here (R2)". Test `test_regime_strata_do_not_emit_parametric_mde` (`:431`) parses the emitted JSON and asserts `"mde_bps" not in payload` per stratum. |
| BR-3 | R1 ceiling computed from a one-domain-bar hold while the estimand used a longer hold | **FIXED (basis reconciled, not changed)** | The premise was wrong, not the code: design §7 / `design.md:249` records the FIXED native baseline holds **exactly one** H1 bar on 100% of rows (`hold_bars = 1`, median = p99 = max), and `design.md:495` declares the preflight basis as "stop-touch + one-domain-bar hold; reconcile to engine fills post-run". `preflight.py:153-156` now states that match in code, and `size_mechanism_ceiling_basis` (`:269-271`) emits `PROVISIONAL_DOMAIN_BAR_SIM_ONE_BAR_HOLD_MATCHES_FIXED_NATIVE_HOLD`. Simulated hold and production hold are the same endpoint; no √hold understatement. |

Prior NB-1 (two different governing rules across channels) is also resolved: both channels now
govern by **highest R2 floor with interval width as tie-break** — scale at `governing_treatment:483-501`
(`max` on `mde_sigma`), selection at `:913-930` (`max` on `mde_bps`).

## R2 / R3 / R5 re-check

**R2 — floor = `MDE_Z × bootstrap SE`, one SE family.**
`row_floor_from_se:349` is the single floor constructor. Call sites: pooled/per-symbol scale
(`clustered_interval:445`), selection contrast (`_contrast_interval:844`), selection row fallback
(`:940`). Both tripwire halves take their bite scale from those same intervals (`:1342`, `:1414`).
`MDE_Z/√blocks` appears nowhere as a row floor in the emission path — the only surviving `MDE_Z/√n`
is `preflight._planning_floor:97`, which is pre-run planning with no bootstrap in existence and is
sanctioned by R3. Guarded by `test_row_floor_uses_bootstrap_se_not_blocks_sqrt` (constructs
within-block dependence so bootstrap SE ≠ 1/√blocks, then asserts the row floor tracks SE and is
*not* the block floor) and by the per-symbol assertion in
`test_emission_frames_have_no_banned_label_values_or_columns:483-486`.

**R3 — no result labels.**
`band_label`, `resolution_class`, `_selection_band`, `_band_or_identity`, `_control_band`,
`_resolution_fields` all absent (`hasattr` asserted). `contrast_over_mde` replaced by
`contrast_over_se:990`. Collapse fraction is not MDE-gated. Tripwire fields are named as an
integrity bite scale with explicit "not a resolution statement" notes (`:1365`, `:1444`, `:1488`).
Value + column denylists cover `WASH / UNPOWERED / NOT_RESOLVABLE / CARRIES_MAGNITUDE /
FULLY_RESOLVING / CLEARS_FLOOR`, `step3_*`, `floor_over_*`, `*_band`.

**R4 — channel denominators declared.** `paired_delta` (scale) vs `outcome_level_bps` (selection),
tested.

**R5 — preflight.** `descriptive_power_label:182-194` compares planning floor to the R1 mechanism
ceiling; `power_label_endpoint = R1_SIZE_MECHANISM_CEILING`; `count_basis =
PROVISIONAL_DOMAIN_BAR_SIMULATED_FILLS`. Source-level test asserts no `STEP3_OBSERVED`, no
`CARRIES_MAGNITUDE_QUESTION`, no `0.150`/`0.022` inside the label function.

**Quarantine.** `analysis_code/` holds only `analyse.py`. `legacy_pre_a7/` has all ten `da_*.py`
plus a README stating why; every script raises `RuntimeError("AMENDMENT_7_QUARANTINE: …")` at
import, before any other statement. Enforced by `test_legacy_da_scripts_are_quarantined`.

## Verification run

- `python -m pytest tests -q` → **580 passed, 4 skipped**, 79.7 s.
- `pytest tests -q` (bare, from `python/`) collects 3 ImportErrors —
  `test_adaptive_management_policies.py`, `test_xena_certify.py`, `test_xena_final_gate.py` fail on
  `from tests.test_… import …` because bare invocation does not put the repo `python/` root on
  `sys.path`. Pre-existing invocation artifact, unrelated to AMENDMENT-7; all three collect and
  pass under `python -m pytest`. Worth pinning the invocation in the handoff so Task 7/8 does not
  read this as a regression.
- `tests/test_spdr024.py -q` → 42 passed.
- `ruff check` on all four touched files → clean.

## Non-blocking residuals

**NB-A — dead parametric-floor helper still in the module.** `_two_sample_mde:1141` has no callers
anywhere in `python/` after BR-2. It is the exact shape R2 forbids, sitting in the module a future
edit would reach for. Recommend deleting it (or moving it behind the same quarantine language).
`interval_implied_se:365` is likewise uncalled, but it is documented as an intentional fallback.

**NB-B — two stale governing-rule sentences.** `design.md:543` and `analyse.py:224-226` both say
"most conservative by **fewest blocks** / highest coherent R2 floor". The code implements highest
floor only, with width as tie-break. The dual wording could later be read as a deviation from the
frozen design. Also `design.md:440` still says the conservative treatment "governs every **band
label** in §11" — §11 withdrew band labels. Text-only; align before the Task 8 write-up.

**NB-C — per-symbol bootstrap cost still unmeasured on real data.** Per-symbol scale rows now run a
real `clustered_interval` at `n_boot = BOOTSTRAP_DRAWS` where they previously used a free
`2.8/√n`. That is arms × 2 lenses × 3 regimes × n_symbols extra bootstraps per cell, and Task 4's
smoke was synthetic at small `n_boot`. The handoff's performance standard asks for wall-time deltas.
Recommend timing `ctrader_H1` (the cheap first cell) and recording it before committing to
`crypto_H4`. Not a correctness risk; a schedule risk. Do **not** reduce draws to fix it — that is
explicitly prohibited.

## Explicit non-findings

- `outside_band` / `noise_band_95` in `analyse.py:98-148` are the ACF dependence-probe noise band
  (P-5), not power labels — same class as the sanctioned `_planning_floor`.
- `step3_observed_sizing_effects_historical_only` in `analysis_summary.json` (`analyse.py:248-257`)
  is labelled HISTORICAL CONTEXT ONLY and feeds no gate, ladder, or column.
- `*_class` columns (`breakeven_spread_class`, `BASELINE_CHARACTERISATION_*`) are population and
  scenario descriptors.
- Scope intact: no arm, device, universe, cost model, or TEST/holdout change in this diff.
- Purge targets are bounded and safe: `results/` is a real directory (7.2 G, not a symlink),
  `analysis.md` and `screen.md` exist, `plots/` is present and empty. Everything under `results/`
  except the untracked `results/runs/` is committed at `3f70a6a`, so the tracked pre-fix emission
  stays recoverable from git after deletion; `results/runs/` is untracked and its deletion is final,
  which is what §13 intends.

## Recommendation

Proceed to Task 6 purge and the four-cell TRAIN re-run. Fold NB-A and NB-B into the Task 8
documentation pass; take the NB-C timing reading on the first cell.
