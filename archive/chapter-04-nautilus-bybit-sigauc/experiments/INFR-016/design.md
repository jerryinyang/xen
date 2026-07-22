# INFR-016 — Arbitrary-Gate Retirement: Value Gates → Report Layers

**Type:** INFR-class infrastructure (framework update; not a candidate-family experiment)
**Status:** RATIFIED — 2026-07-18 · operator sign-off on the (a)/(b) split (§4): **split by control class** (option A, §4c — future-destroy stays HARD; within-sample attribution → report) + **sign battery ≥ 2000 seeds** (§7). Implementation authorised.
**Lineage:** motivated by **XENA-HTFCAP-001** (exploratory, 2026-07-17) which reproduced the
"arbitrary-gate trap" the programme's own principles forbid
(`_pipeline-config.md` § *Integrity gates hard, value reads informative*: "no auto-verdicts,
no threshold stacks, no auto-RETIRE").
**Scope discipline:** deterministic; **no data re-emission**; does NOT weaken holdout sealing,
causal provenance, or estimand reconciliation as validity attestations (§4a guardrail).
**Stop this session:** design + ratification gate. Implementation only after the §4 sign-off.

---

## 1. One change + mechanism

**Change.** Convert **every value / quality / significance / selection GATE** in the strategy
value chain into a **REPORT LAYER**. No automated invalidation or nullification anywhere in the
value chain. Each layer, **for every authorised candidate**, emits exactly:

```
observed result          = ###
ideal range              = ###   (practical real-world expectation — NOT academic perfection)
realistic interpretation = <plain language; underpowered / within-noise / suggestive / strong; NO verdict>
```

Every layer **runs for all authorised candidates**, all the way to the final layer (incl. the
former "final gate"). **Nothing is machine-dropped between layers.** All facts go to the
operator plainly and unbiased; the **operator authorises** which candidates advance.

```
MECHANISM (why the current design is broken — grounded in HTFCAP, exact values):

FAILURE 1 — a 25-seed sign battery with an at_or_above_p95 BOOLEAN auto-labelled real,
  directionally-positive, gate-attributable cells as "fails":
    SOL v1.5 DI_VOL_HI H64 : raw_median = 24.93 bps gross, percentile-vs-battery = 0.80 (P80),
      at_or_above_p95 = FALSE   (controls_SOLUSDT__DI_VOL_HI__v1.5__adxna__H64.json:39-40)
    BTC#2 v1.5            : ~10.7 bps, p ≈ 0.23, at_or_above_p95 = FALSE
  25 seeds cannot resolve a P95: that bar IS ~the top order statistic of 25 draws = pure noise.
  The SAME read at ≥2000 seeds resolves to ~P78, one-sided p ≈ 0.22 — "suggestive but
  underpowered", NOT a refutation. Absence of evidence at an arbitrary threshold was reported
  as evidence of absence. (controls.py:72-101, N_BATTERY_SEEDS = 25, key `at_or_above_p95`.)

FAILURE 2 — the pinned stage-2 binder's "one_subset / top-1 only" HID those cells entirely.
  It certified a near-zero (~1 bps) leak-class cell and never reported the suggestive ones.
  (calibration_bybit15.py:409,860 `one_subset: True`.)

FAILURE 3 (same class) — gate-schedule derangement collapse < 0.5 is a HARD BTC REJECT
  (controls.py:251,301,324 `hard_fail_leak`, `hard_block_btc_derangement`). A continuous
  attribution fraction (how much edge is timing/construction-attributable) collapsed to one
  bit and wired to auto-kill — the L-15 "binarize noise at the admit bar" error, at gate scale.

ROOT CAUSE: value/quality/significance thresholds are wired to DECIDE, not INFORM. The fix is
structural (move the decision to the operator), not a re-tuning of any threshold.
```

This is the same lesson family already codified but not yet enforced in the XENA value chain:
[[L-12]] fixed-threshold conjunctions over-reject; [[L-15]] a binary on a continuous
attribution control binarizes noise — report the collapse fraction; [[L-17]] a fixed floor is
band-length-blind; [[L-19]] a percentile read needs a real seed battery; [[L-25]] scale-broken
thresholds; [[L-26]] a costless objective cannot adjudicate a filter thesis.

## 2. Object identity

The object being reframed is the **XENA value chain** — every layer between a passing candidate
gate and the operator's verdict. The **candidate emissions and the oracle are unchanged**
(deterministic, bit-identical). Only the **adjudication layer** changes: from "gates that drop
candidates" to "report layers that describe candidates for the operator".

## 3. The unbiased layer framing (the schema every layer emits)

A reusable renderer/schema lives in `xen` (`xen.xena.report_layer`). One record per
(layer × candidate):

| Field | Meaning |
|---|---|
| `layer` | layer name (e.g. `cost_floor`, `sign_battery`, `stage2_bounds`) |
| `candidate_id` / `subset` | the authorised candidate (or subset) this row describes |
| `observed` | the measured number(s) — effect size, CI, p, fraction, count — never hidden |
| `ideal_range` | practical real-world expectation for this layer (NOT theoretical perfection) |
| `interpretation` | plain-language sentence — `underpowered` / `within-noise` / `suggestive` / `strong`; **no pass/fail, no verdict** |
| `interpretation_label` | optional enum tag for scanning: `SUPPORTED / WASH / CONTRADICTED / UNPOWERED / SUGGESTIVE / STRONG` — a **label on the layer, never a gate** |
| `supporting` | dict of raw numbers backing the row (n, seeds, block, MDE, …) |

Hard rule: `report_layer` records carry **no `pass` / `blocking_pass` / `passed` field**. The
renderer produces an operator-facing table (`observed | ideal | interpretation`) per layer,
across ALL authorised candidates. `interpretation_label` is descriptive only.

## 4. CRITICAL DECISION — the (a)/(b) split (operator must ratify before build)

Separate two things the current code conflates.

### 4a. VALIDITY / INTEGRITY attestations — stay HARD (attest the numbers are REAL)

These do **not** rank or kill a strategy's value. A failure here means **"emission invalid →
fix the data"**, never "strategy has no edge". They still run and still block, but they gate
**DATA VALIDITY**, not strategy value.

| Attestation | Where today | Stays hard? |
|---|---|---|
| Holdout fence (every emitted ts < holdout_start / AnalysisEndUtc) | `ingest.gate_candidate` `fence`; catalog fence | **YES** |
| Causal ≤ t-1 provenance (entries in grid, entry<exit, monotone marks) | `ingest` `causality` | **YES** |
| Estimand reconciliation / fill self-consistency (L-18) | `ingest` `fill_consistency`; `xen.estimand_validation` gate v2 | **YES** |
| Fence attestation non-STUB | estimand gate v2 | **YES** |
| No-local-accounting (`check_no_local_accounting`) | estimand gate | **YES** |
| Structural computability (files / schema / non-empty / finite stop-distance denominator) | `ingest` `files`/`schema`/`non_empty`/`stop_contract` | **YES** (can't compute without them) |
| Oracle determinism smoke (bit-identical re-eval) | `ingest` `oracle_smoke` | **YES** |
| Look-ahead / future-destroy leak survival (edge survives destroying **future** info ⇒ acausal leak ⇒ L-01 REJECT) | VAL-008 destroy tripwire | **YES — see 4c** |

**Recommendation: keep 4a exactly as-is.** This is the guardrail; it is not weakened.

### 4b. VALUE gates → REPORT layers (operator-authorised progression, no auto-drop)

Every layer below emits the §3 framing per candidate, runs for ALL authorised candidates, and
**machine-drops nothing**. Interpretation bands become **labels**, never gates.

| Layer (former gate) | Was (auto-behaviour) | Becomes (report layer) |
|---|---|---|
| Candidate value/schema readout | — | observed n_legs / cadence / gross bps vs ideal |
| Pre-search cost floor & breakeven | (implicit veto) | observed gross bps vs breakeven; interpretation |
| Cadence coverage | (implicit) | observed coverage vs ideal band |
| Leg-count / power | **`n_legs_floor` in-domain veto** (`calibration_bybit15`) | report **power** (n_legs, per-leg vol, MDE) — **never a floor veto** |
| Search score | — | observed g_gross; interpretation (selection-biased, disclosed) |
| Ranking-fold stability | (evidence already) | median/worst fold F + PBO-like, as a layer |
| Stage-2 lower/upper bounds | **`one_subset` top-1 only** | **ALL certified subsets AND per-cell** LCB/UCB — top-1 hiding retired |
| Controls — derangement collapse | **HARD collapse < 0.5 REJECT** | **reported attribution fraction** (how much edge is timing/construction-attributable) + observed/ideal/interp — **see 4c** |
| Controls — sign battery | **25-seed `at_or_above_p95` boolean** | **≥1000-seed** battery: **effect size + one-sided p + CI**, NOT a P95 boolean |
| Cost / funding sensitivity | (informational) | observed net under cost/funding scenarios |
| Spread-scale routing | (park/route) | observed gross-vs-spread multiple; interpretation |
| Net deployability (former **final gate** `passed`) | **binding P25 ≥ threshold** | **final report layer**: net P25/median/P75, DD, decay — no `passed` |

### 4c. The leak / derangement tripwire — the ONE to decide explicitly

**Today:** the gate-schedule derangement collapse is a **HARD collapse < 0.5 REJECT** on BTC
(`controls.py:251,301`). This is the crux the operator must sign off on, because it is the one
place where "value → report" touches a leak control.

**The distinction that resolves it** (recommended framing):

- A **future-destroying** control — time-reversal / future-shuffle / label-permutation that
  destroys information from **after** the decision — tests **acausal provenance**. If the edge
  **survives destroying the future**, that is the L-01 leak that shipped a false
  `DEPLOYABLE_CONFIRMED`. **This stays a HARD VALIDITY attestation (4a).**
- A **within-sample alignment/attribution** control — the HTFCAP gate-schedule derangement —
  scrambles the HTF conditioning **timing** while entries remain causal (≤ t-1). A partially
  surviving edge here does **not** prove a look-ahead leak; it means the base entries carry edge
  independent of the HTF gate — an **attribution** finding, not a leak. HTFCAP mis-classified
  this attribution read as a leak gate and auto-killed on it.

**Recommendation (option A below): the attribution-collapse read becomes a REPORT layer
(observed collapse fraction + battery percentiles + plain interpretation); the future-destroy
leak-survival test stays HARD.** Each control declares its class (`future_destroy` vs
`within_sample_attribution`) at design time; the HTFCAP-style gate-schedule derangement defaults
to `within_sample_attribution` → report.

**Trade-off the operator is signing (stated plainly):** under option A, a strategy whose edge
partly survives the *within-sample* attribution control is **no longer auto-blocked** — the
operator must read the collapse fraction and judge whether the surviving edge is a construction
leak or a genuine base-signal edge. We trade an automatic tripwire for operator judgement on
exactly the cells where the automatic tripwire was demonstrably wrong (HTFCAP). The L-01
future-look-ahead protection is **untouched**.

## 5. Scope of changes (files)

| Area | Change |
|---|---|
| `xen.xena.report_layer` (**new**) | `LayerReport` schema (§3) + markdown/table renderer; no `pass` field; deterministic |
| `xen.xena.ingest` | split `gate_universe`/`gate_candidate` return into **validity block** (4a checks, blocking) + **report block** (any value read moves out); keep validity `blocking_pass`; rename value reads to layers |
| `xen.xena.certify` | `certify_and_rank` already evidence-only (INFR-009) — emit **all certified subsets AND per-cell** stage-2 bounds via `report_layer`; retire `one_subset` top-1 selection |
| `xen.xena.calibration_bybit15` (+ siblings) | `n_legs_floor` domain guard → **power report layer** (report n_legs/MDE, no in-domain veto); stage-2 bounds reported for all subsets/cells |
| `xen.xena.final_gate` | `run_final_gate` → **final report layer** (net P25/median/P75, DD, decay per candidate); drop `passed` binding; keep ledger count + holdout-safety as validity |
| controls (sign battery / derangement) | promote to reusable `xen` controls: sign battery **≥1000 seeds** → effect size + one-sided p + CI; derangement → **attribution-fraction report** with class tag (§4c); retire `at_or_above_p95` + `hard_fail_leak` |
| `research-pipeline` skill + `_pipeline-config.md` | stage table + "operator gates" = **only holdout-safety + data validity**; everything else = operator-authorised **layer progression** |
| `data-analyst` + `quant-designer` skills | layer schema (§3); remove auto-verdict language; interpretation bands = labels |
| `docs/references/xena-lane.md` + `references/governance-constraints.md` | reflect validity-vs-report split; value gates listed as report layers |
| KB `lessons-and-amendments.md` | new **L-32** (arbitrary-gate retirement; cite HTFCAP two failures) |
| project memory | INFR-016 pointer + MEMORY.md line |

## 6. Deliverables

1. `INFR-016/design.md` (this file) + operator-ratified §4 split.
2. `xen.xena.report_layer` + the six module edits (§5), deterministic, tests green.
3. Updated skills (`research-pipeline`, `data-analyst`, `quant-designer`) + refs
   (`xena-lane.md`, `governance-constraints.md`).
4. KB lesson **L-32**; project-memory update.
5. `INFR-016/report.md` recording the operator's ratification + what changed.

## 7. Guardrails (binding)

- **Do NOT weaken** holdout sealing, causal ≤ t-1 provenance, or estimand reconciliation as
  VALIDITY attestations (4a). The future-destroy leak-survival test stays hard (4c).
- **Deterministic**; **no data re-emission** required by this change.
- No `pass` field on any report layer; interpretation is plain language, no verdict.
- Every layer runs for **all** authorised candidates; **nothing machine-dropped** between layers.
- Sign battery **≥ 1000 seeds** (design target ≥ 2000 where feasible); report effect size,
  one-sided p, CI — never an `at_or_above_pXX` boolean.

## 8. Interpretation bands become labels (not gates)

The former §9-style bands (`SUPPORTED / WASH / CONTRADICTED / UNPOWERED`) survive only as
`interpretation_label` values on a layer — a scanning aid. They never gate progression and never
drop a candidate. Adds `SUGGESTIVE` and `STRONG` for the underpowered-but-directional and
clear-signal cases the boolean gates previously mislabelled.

## 9. Success criteria (verifiable)

1. No module in the value chain returns a value/quality auto-verdict (`passed`/`blocking_pass`
   on a value read) — grep-verifiable; only 4a validity checks keep `blocking_pass`.
2. `report_layer` renders `observed | ideal | interpretation` per layer for ALL authorised
   candidates; HTFCAP SOL/BTC#2 cells appear as `SUGGESTIVE` (p ≈ 0.22, underpowered), not
   hidden and not "fail".
3. Sign battery at ≥1000 seeds reproduces the ~P78 / p ≈ 0.22 read for the HTFCAP cells.
4. Derangement collapse renders as a fraction with interpretation; no `hard_fail_leak` auto-kill.
5. Existing determinism/parity tests stay green; no emission changes.
