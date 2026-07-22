# INFR-016 — Report: Arbitrary-Gate Retirement (Value Gates → Report Layers)

**Status:** COMPLETE — 2026-07-18 · operator-ratified split implemented + verified.
**Design + ratification:** `design.md` (§4 split ratified: option A by control class + ≥2000-seed
sign battery). **Tests:** `python/tests/test_xena_infr016.py`.

## 1. What changed

The XENA value chain is split into two disjoint layers (design §4):

- **VALIDITY attestations stay HARD** — holdout fence, causal ≤t-1, estimand reconciliation,
  non-STUB fence, no-local-accounting, structural computability, oracle determinism, and
  **future-destroy** leak survival. A failure = *emission invalid → fix the data*, never *no edge*.
  **Untouched** — no weakening (guardrail §7).
- **VALUE reads became report layers** — `xen.xena.report_layer.LayerReport`: per candidate
  `observed / ideal / interpretation`, **no `pass` field**, nothing machine-dropped. The operator
  authorises which candidates advance.

## 2. Operator ratification (2026-07-18)

| Decision | Ratified |
|---|---|
| (a)/(b) split | Keep validity attestations hard (4a); all value gates → report layers (4b) |
| Leak/derangement tripwire (§4c) | **Option A — split by control class**: `future_destroy` HARD; `within_sample_attribution` → report layer (collapse fraction reported, operator judges leak-vs-edge) |
| Sign-battery seeds | **≥2000** (report effect size + one-sided p + CI; no `at_or_above_pXX` boolean) |

**Trade-off accepted:** a partly-surviving edge on a within-sample attribution control is no
longer auto-blocked — the operator reads the collapse fraction and judges. L-01 future-look-ahead
protection is untouched.

## 3. Deliverables

| Deliverable | Where |
|---|---|
| `LayerReport` schema + renderer + builders (`power_layer`, `stage2_bounds_layer`) | `xen.xena.report_layer` (new) |
| Reusable controls (`sign_battery` ≥2000, `attribution_derangement` reported fraction, class guard) | `xen.xena.controls` (new) |
| Former final gate as report layer (net deployability, no `passed`) | `xen.xena.final_gate.final_report_layer` |
| Tests (schema guards + HTFCAP reproduction + retirements) | `python/tests/test_xena_infr016.py` (16 tests) |
| Skills reframed (report layers, no auto-verdict) | `research-pipeline` SKILL + `_pipeline-config.md`; `data-analyst`; `quant-designer` |
| References | `docs/references/xena-lane.md`; `references/governance-constraints.md` |
| KB lesson | `lessons-and-amendments.md` **L-32** |
| Project memory | `arbitrary_gate_retirement_infr016.md` (DELIVERED) + MEMORY.md |

## 4. Retired auto-verdicts

| Retired | Was | Now (report layer) |
|---|---|---|
| `at_or_above_p95` | 25-seed sign-battery boolean | `controls.sign_battery` — ≥2000 seeds, effect + one-sided p + CI |
| `n_legs_floor` in-domain veto | auto-fail thin-leg cells | `report_layer.power_layer` — reports power, labels UNPOWERED |
| `one_subset` top-1 | hid all but the top subset | `report_layer.stage2_bounds_layer` — ALL subsets + per-cell |
| derangement `hard_fail_leak` | collapse<0.5 auto-REJECT | `controls.attribution_derangement` — reported collapse fraction |
| final-gate `passed` | binding P25 ≥ threshold | `final_gate.final_report_layer` — net P25/median/P75 + DD |

## 5. Verification (success criteria, design §9)

1. **No value auto-verdict in the value chain** — `LayerReport` rejects any `pass`/`passed`/
   `blocking_pass`/`hard_fail_leak`/`at_or_above_p95` key (guard `_forbid_verdict_keys`); only
   4a validity checks (`ingest.gate_*`, estimand gate) keep `blocking_pass`. ✅
2. **HTFCAP cells surface as SUGGESTIVE, not hidden/"fail"** — SOL v1.5 DI_VOL_HI H64 on the real
   emission: raw **24.9 bps**, one-sided **p=0.224**, percentile **P78**, effect **+23.6 bps**,
   label **SUGGESTIVE** (was `at_or_above_p95 = FALSE` → auto-"fail"). ✅
3. **Sign battery at ≥2000 seeds reproduces the ~P78 / p≈0.22 read.** ✅
4. **Derangement renders a fraction with interpretation; no `hard_fail_leak` auto-kill.** ✅
5. **Determinism/parity tests stay green; no emission changes.** Full `tests/test_xena_*` green;
   pinned CAL registries (INFR-014/015) untouched — INFR-016 changes forward adjudication, not pins. ✅

## 6. Follow-up strips (2026-07-19) + framework validation

**Do-now strip batch** (fragility removed by deletion, not addition):
- **Retired p-band labels** (`label_from_p_and_power` → `structural_label`): only UNPOWERED
  (seed count) + CONTRADICTED (sign) auto-assign; STRONG/SUPPORTED/SUGGESTIVE/WASH were
  hardcoded p-cutpoints that re-read as verdicts — the L-32 trap in miniature. The number + p +
  CI carries the read.
- **`oracle_smoke` → `oracle_computable`** (`ingest`): dropped the per-candidate determinism
  re-proof (an oracle-wide property, proven once by the pinned parity corpus); kept the
  runs-at-all + finite-F computability check.
- **Single-source skill mirrors**: `scripts/sync_skills.sh` regenerates the 8 mirror dirs from
  `.claude/skills`; mirrors gitignored + untracked (1400 files left git tracking) — ends the 9×
  diff churn. Deferred to an INFR-017 archival bundle (coupled to the chapter-03 calibration
  cluster): retire the CAL threshold-derivation stack + `run_final_gate` + `PlateauReport`
  legacy fields; prune the duplicated certify Jaccard.

**Framework validation** (`validation/`, why we can trust the minimal framework — and why the
old CAL power/FPR test could NOT be trusted):
- The old CAL battery certified the binder as "FPR ≤1%, power 94%" yet it picked the worst
  HTFCAP cell. Two design flaws: **circular** (planted the edge in the objective's own units,
  then checked that objective could detect it) and **detection-not-selection** (2 clean classes,
  never a graded ranking).
- **`synth_ranking_validation.py` (12/12)** — a graded universe with ground truth = DEPLOYABLE
  NET quality (outside any objective) + three adversaries (cost-trap, concentration, negative).
  Result: the old costless-extensive + `one_subset` top-1 **reproduces the failure** (certifies
  the non-deployable concentration cell, hides the good). The minimal layers recover the true
  ranking — but the key finding is that **a single layer is not a gate**: ranking by net-LCB
  alone is *also* fooled by the concentration cell (mean +9) — only the cross-layer
  **disagreement** (median/sign says p=0.94 CONTRADICTED) exposes it. The combined read
  (net-LCB>0 AND sign-clean) = exactly `{strong, modest}`, no adversary; marginal honestly
  underpowered. This is the INFR-016 thesis proven: safety is showing all layers, not one number.
- **`htfcap_replay.py` (6/6)** — the report layers over the REAL HTFCAP emissions (108 cells)
  reproduce the redo on a known-answer case: BTC adx25 H32 p=0.017–0.037, H64 (v1.25) p=0.043,
  gross +7 to +22 bps; SOL v1.5 DI_VOL_HI H64 p=**0.224** (suggestive, not refuted); a 10-cell
  sign-clean set the binder had hidden; negatives read CONTRADICTED.
- Regression-guarded: `python/tests/test_xena_infr016_validation.py`.

## 7. Guardrails held

No holdout/causal/estimand weakening; deterministic; no data re-emission; pinned CAL artifacts
untouched. Not a family disposition — an INFR framework update.
