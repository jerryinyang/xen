# XENA Run Design — Template (INFR-006, item 4)

Copy to `python/experiments/XENA-<NNN>/design.md`. Every field below is **pre-registered**:
filled before any search iteration runs. The quant-designer fills it; QA traces it
clause-by-clause (qa-compliance §3 XENA clauses a–e). Spec: `docs/references/xena-lane.md`.

---

## XENA-<NNN> — <one-line idea statement>

**Status:** DESIGN | GATED | SEARCHED | CERTIFIED | GATE-SPENT | CLOSED
**Frozen registry:** sha256 `<pinned hash>` — verified via
`xen.xena.calibration.verify_frozen_registry` on `<date>` (paste output). Thresholds are
NEVER re-derived per run.

### 1. Idea + mechanism (why these candidates)

<2–5 sentences: information source, why portfolio-level, KB/pitfalls check —
name the `pitfalls-ledger.md` entries closest to this idea and why this is not a re-run.>

### 2. Universe manifest (the candidate grid — every cell enters; no quality gates)

| Axis | Values |
|---|---|
| Models | <ISignalModel names> |
| Parameters | <grid per model> |
| Instruments | <symbols — each Loaded/VAL-admitted> |
| Domains | <bar domains> |
| **Total candidates** | N = <product> |

Manifest file: `data/strategy_runs/XENA-<NNN>/universe_manifest.json`.

### 3. Per-candidate cost + unit pins (L-21/L-22 — verifiable, QA-traced)

| Symbol | spread (pinned, source+date) | commission (FTMO table) | cost_bps RT | money_per_unit (rate pin if non-USD-quote) |
|---|---|---|---|---|

Costs are **excluded from selection** (gross-selection amendment 2026-07-10) and
**charged at the final gate** (forced in code). The pins above are therefore
gate-verdict-bearing: wrong pin = wrong verdict.

### 4. Band boundaries (pre-registered; Q1 partition)

Layout shape: 50/30/20 (frozen). On this universe's real calendar:

| Band | Start (UTC) | End (UTC) | Bars (approx) |
|---|---|---|---|
| TRAIN search | | | |
| TRAIN ranking (folds) | | | |
| TEST gate | | | |

Folds: n=<3–5>, purge = <≥ max holding horizon, state it>. Gate band must support
block=64 bootstrap non-degenerately (bars ≫ block).

### 5. Run parameters (all from the frozen registry — cite, don't restate)

Restarts <10–15>, budget <from smoke flattening>, seeds = restart ids. Everything else:
frozen registry values, byte-checked by QA.

### 6. Amendments (L-23)

| # | Date | Change | Direction (LOOSER/TIGHTER/NEUTRAL) | Running count |
|---|---|---|---|---|

### 7. Gate plan

Gate ledger state at design time: <slots spent / 2>. Intended gate spend condition:
<what certification evidence justifies spending a slot — operator decides at the gate>.
`new_data_attestation` is operator-only; agents never author it.

### 8. Ledger row (fill at close)

Registered in `docs/signal-registry/xena-runs.md` on <date>: evaluation_count=<>,
distinct_subsets=<>, outcome=<>.
