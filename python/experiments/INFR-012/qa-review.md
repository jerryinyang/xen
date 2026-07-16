# INFR-012 QA — Phase C doc dry-read

## QA run 1 — 2026-07-15 — mode: subagent — purpose: INFR-012 Phase C doc dry-read

**Scope:** Binding doc set (no implementation code). Cross-check INFR-010 §4/§6, INFR-012 design §4–§5.

**Verdict: APPROVE** (after orchestrator fixes to skill remnants flagged in initial pass)

---

### Initial findings (subagent) — remediated same session

| Finding | Severity | Status |
|---------|----------|--------|
| SPDR → cTrader-primary pipeline | BLOCKING | Fixed in `research-pipeline/SKILL.md` |
| `code/` C# refs | BLOCKING | Fixed |
| quant-designer FTMO cost for XENA | BLOCKING | Fixed → `bybit_round_trip_cost_bps` |
| xena-lane VOID vs active registry | BLOCKING | Fixed — archived binder section |
| research-pipeline VOID omission | BLOCKING | Fixed |
| qa-compliance VOID check | BLOCKING | Fixed |
| code-conventions timebars default | BLOCKING | Fixed — catalog + fence |
| ctrader-cli in experiment-developer | MINOR | Fixed → Phase B script |
| dataset-reference archive paths | MINOR | Fixed |

### Seven-probe checklist (post-fix)

| Probe | Result |
|-------|--------|
| Nautilus execution (not cTrader) | PASS |
| `data/nautilus_runs/` emissions | PASS |
| T1/T2 + 3× spread-scale routing | PASS |
| STUB rejected / A6 manifest required | PASS |
| XENA registry VOID on new stack | PASS |
| Bybit cost (not FTMO) ch.04 | PASS |
| 910 USDT perps universe | PASS |

**Routing:** Phase C verify block may proceed. Phase D VAL required before Chapter 04 research.