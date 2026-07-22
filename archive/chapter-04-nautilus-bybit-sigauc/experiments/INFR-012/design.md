# INFR-012 — Governance Rebind (Phase C)

**Type:** infrastructure (spawned from INFR-010 §6 Phase C)
**Status:** IN PROGRESS — verify block
**Parent:** INFR-010 design v2 (2026-07-14)

---

## 1. Objective

Rebind programme governance from the archived cTrader/FX-indices substrate to the Nautilus +
Bybit USDT-perp stack without changing integrity principles (holdout, causal execution,
estimand-before-hypothesis, operator gates).

## 2. Scope (Phase C steps)

| Step | Deliverable | Status |
|------|-------------|--------|
| C1 | `architecture.md` v2, `dataset-reference.md` v2, `_pipeline-config.md`, skill execution refs | this INFR |
| C2 | Principle rebind (engine, fence, timestamps, returns) | docs + skills |
| C3 | `xen.estimand_validation` v2 vs emission contract v1 | code + tests |
| C4 | Bybit cost model + T1 spread injection + spread-scale routing | `xen.evaluation` + checklists |
| C5 | `xena-lane.md` v2 — Nautilus fills; frozen registry **VOID** on new data | doc |
| C6 | Fresh-context QA dry-read of doc set | `qa-review.md` |

**Out of scope:** INFR-011 A6 fence manifest (pending); VAL dry run (Phase D).

## 3. Binding inputs

- Fill tiers + spread-scale routing: INFR-010 §4
- Carry-forward table: INFR-010 §5
- Emission contract v1 + Phase B STUB fence: `python/experiments/INFR-010/code/emission_contract_v1.md`
- Universe census: INFR-011 A1 (910 USDT linear perps)
- Pin: `nautilus_trader==1.230.0`, CPython 3.13.1, macOS arm64

## 4. Hard requirements

1. **STUB fence rejection:** v2 estimand gate MUST `blocking_pass=false` when
   `fence_attestation.json` has `status: STUB` (Phase B smokes only).
2. **Real experiments** require INFR-011 A6 hash-pinned fence manifest attestation.
3. **`check_no_local_accounting` unchanged.**
4. **XENA frozen registry VOID** — no crypto universe adjudication until fresh CAL INFR.

## 5. Verify block

- [ ] Doc set internally consistent (QA subagent dry-read)
- [ ] `pytest python/tests/test_estimand_validation_v2.py` — STUB fail + shim reconcile pass
- [ ] No cTrader-primary execution paths in binding docs/skills (archived references labelled)
- [ ] Spread-scale routing codified in quant-designer + qa-compliance

**Stop here.** Phase D (VAL) opens Chapter 04 research.