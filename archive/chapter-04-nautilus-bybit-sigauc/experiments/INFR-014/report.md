# INFR-014 — Fresh Bybit/Nautilus XENA Calibration + Universe Selection

**Type:** INFR infrastructure  
**Status:** COMPLETE 2026-07-17 — **operator pin sign-off: ACCEPTED (partial pin)**; QA run 4 APPROVE  
**Design:** QA-APPROVED (run 2) + L-23 amendments A-1…A-4 (§20)  
**Operator execution GO:** 2026-07-16 (WP0–WP7)

---

## 1. Question + mechanism

Can the INFR-009 two-stage sample-split CONFIRM form be **re-measured** on Bybit/Nautilus
(net-cost-binding stage-1, class-shaped nulls, causal universe selection) such that a new
hash-pinned registry certifies e2e α̂ ≤ 5% on both class configs?

Chapter-03 pin `db87dc1a…` remains **VOID** — never loaded as binding.

---

## 2. QA fix summary (Issues 9–13)

| Issue | Severity | Fix |
|---|---|---|
| **9** | Major | `no_search_coverage` no longer re-pins DESIGN seeds; confirm cov uses 93k/94k; assert `seed_bases == CONFIRM_SEEDS` |
| **10** | Moderate | S1: ADMITTED BTC/ETH/SOL catalog; Path **A-vs-B** bitwise; estimand-v2 blocking_pass; PINNED fence |
| **11** | Minor | `run_cal.py` always writes `cal_summary.json` (producer field); no early return before summary |
| **12** | Minor | `verify_bybit_registry` requires `void_priors` list VOID prefixes (was vacuous loop) |
| **13** | Minor | Confirm gate uses `procedure["alpha"]`, not free global |

First-run confirm cov (design-seed contamination) **discarded**. This report = re-run only.

---

## 3. Deliverables

| WP | Outcome |
|---|---|
| WP0 universe_selection + tests | **PASS** |
| WP5 S1 multi-instr smoke | **PASS** → `multi_instrument_single_node` |
| WP1 Bybit CAL harness | **SHIPPED** (+ Issue 9/13 fixes) |
| WP6 next-open control | **SHIPPED** |
| WP2 DESIGN both classes | **bite PASS** |
| WP3 CONFIRM n=200 | CLS-FILTER **LOW_ONLY_CERTIFY**; CLS-EPISODE **TERMINAL** |
| WP4 registry | **WRITTEN** + verify green |
| WP7 report + INDEX | this file |

**Deviations:** none silent. Design §20 documents A-1…A-4.

---

## 4. S1 multi-instrument smoke (re-run)

| Criterion | Result |
|---|---|
| ADMITTED catalog BTC/ETH/SOL USDT-LINEAR.BYBIT | PASS |
| TRAIN fence PINNED attestation | PASS |
| `dispose_on_completion=False` (L-30) | PASS |
| One node / process Path A (L-31) | PASS |
| Path **A-vs-B** bitwise (canonical cols) | PASS |
| Estimand v2 `blocking_pass` all cells | PASS |
| L-29 fill-ts anchor sample | PASS |
| fills (A): BTC 3200 / ETH 3280 / SOL 3072 | non-empty |
| **Batch topology** | **`multi_instrument_single_node`** |

Artifact: `results/s1_smoke.json`. Emissions: `data/nautilus_runs/INFR-014-S1/`.

---

## 5. DESIGN bank (seeds 91000/92000)

| Class | Cadence | select | survival | bite_ok |
|---|---|---:|---:|---|
| CLS-FILTER | low | 1.000 | 0.000 | True |
| CLS-FILTER | high | 1.000 | 0.000 | True |
| CLS-EPISODE | low | 0.875 | 0.125 | True |
| CLS-EPISODE | high | 1.000 | 0.000 | True |

---

## 6. CONFIRM bank (seeds **93000/94000** — verified)

Gate: point α̂ ≤ `procedure.alpha` (0.05) ∧ no_search_cov ≤ 0.05.  
α̂ event = stage-2 **GROSS** LCB > 0 on top-1. Wilson disclosure-only.

**Seed integrity:** coverage rows and α̂ rows both start at 93000 (no design 91k overlap).

### CLS-FILTER

| Cadence | α̂ | SE | Wilson 95% | no_search_cov | inflation | band | certified |
|---|---:|---:|---|---:|---:|---|---|
| low | **0.045** | 0.015 | [0.024, 0.083] | **0.035** | +0.010 | **CERTIFIED** | **yes** |
| high | **0.060** | 0.017 | [0.035, 0.102] | **0.065** | −0.005 | FAIL_ALPHA | no |

**Verdict: LOW_ONLY_CERTIFY** · deployability low: DEPLOY_WEAK (net pass rate 0.01)

### CLS-EPISODE

| Cadence | α̂ | SE | Wilson 95% | no_search_cov | inflation | band | certified |
|---|---:|---:|---|---:|---:|---|---|
| low | **0.075** | 0.019 | [0.046, 0.120] | **0.100** | −0.025 | FAIL_ALPHA | no |
| high | **0.080** | 0.019 | [0.050, 0.126] | **0.050** | +0.030 | FAIL_ALPHA | no |

**Verdict: TERMINAL** · high failure_label: `selection_unsafe` (inflation 0.03)

---

## 7. Registry pin

| Field | Value |
|---|---|
| Path | `results/bybit_pc_frozen_registry.json` |
| schema | `xena.infr014.bybit_pc_registry.v1` |
| **sha256** | **`ac8a1eb679e22290d854ad245ef1620f5f8bdb446a5c0166c618d0c292b2da6f`** |
| verify_bybit_registry | **green** |
| CLS-FILTER | certified=true, LOW_ONLY_CERTIFY |
| CLS-EPISODE | certified=false, TERMINAL |
| limit_entry_cells | false |
| pin_usage.limit_print_sole_certify_forbidden | true |
| pin_usage.forbid_chapter03_on_bybit | true |
| partial_writes | false (single file; EPISODE present as uncertified) |

Live XENA must select only `class_configs` with `certified: true` for the required cadence set.
CLS-FILTER pin is **low-cadence only** under this form.

---

## 8. Recommendation for operator pin sign-off

| Option | Meaning |
|---|---|
| **Accept partial pin (Recommended)** | Accept `bybit_pc_frozen_registry.json` sha256 above; CLS-FILTER low-only certifiable; CLS-EPISODE not certified; XENA-HTFCAP may use CLS-FILTER **low** only; EPSOSC still blocked |
| Reject pin | Discard registry; XENA counted path fully blocked until new CAL |
| Demand DUAL_CERTIFY | Not available from this bank — needs new design amendment + new seeds |

**Reading:** Issue 9 fix changed confirm cov for CLS-FILTER low from contaminated 0.060 → **0.035**, unlocking low CERTIFIED. High remains above α/cov. EPISODE still fails both cadences on α̂.

---

## 9. Integrity checklist

| Check | Status |
|---|---|
| ch03 pin never binding | PASS |
| confirm cov seeds = confirm bases | PASS (assert + artifacts) |
| n_null fixed; no optional stopping | PASS |
| gate on procedure["alpha"] | PASS |
| stage-1 g_net + charge_costs hard refuse | PASS |
| L-30/L-31 S1 | PASS |
| estimand v2 on S1 cells | PASS |
| void_priors verified | PASS |

---

## 10. Artifacts

```
python/experiments/INFR-014/
  design.md (§20 amendments), qa-review.md, report.md
  code/run_s1_smoke.py, code/run_cal.py, code/clause_map.md
  results/
    s1_smoke.json
    design_CLS-*.json, confirm_CLS-*.json
    bybit_pc_frozen_registry.json   # sha256 ac8a1eb6…
    registry_verify.json            # ok=true
    cal_summary.json                # producer=run_cal.py
    cost_pins.json, next_open_control.json
data/nautilus_runs/INFR-014-S1/
python/src/xen/nautilus/universe_selection.py
python/src/xen/xena/calibration_bybit.py
python/src/xen/xena/fill_basis.py
```

**registry:** experiment-level pin written; family status transitions: **none**.

---

## 11. Operator verdict

**ACCEPTED — partial pin (2026-07-17).** Operator: "approved. complete it" — following QA run 4
APPROVE (independent verification of Issue 9–13 fixes; pin sha256 recomputed and matched).

- `bybit_pc_frozen_registry.json` sha256 `ac8a1eb6…` is the **active binding pin** for
  Bybit/Nautilus XENA.
- CLS-FILTER certified **low-cadence only** (LOW_ONLY_CERTIFY) → XENA-HTFCAP may proceed on
  CLS-FILTER low.
- CLS-EPISODE **TERMINAL** — XENA-EPSOSC remains blocked pending a new CAL amendment
  (new seeds; DUAL_CERTIFY not available from this bank).
- Chapter-03 pin `db87dc1a…` remains VOID.
- Documenter's note: analyst/report recommendation (accept partial pin) and operator verdict
  agree. QA run 4 residual Minors 14–16 recorded in `qa-review.md`; non-verdict-material.
