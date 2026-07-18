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

## 6. Guardrails held

No holdout/causal/estimand weakening; deterministic; no data re-emission; pinned CAL artifacts
untouched. Not a family disposition — an INFR framework update.
