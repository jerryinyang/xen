## QA run 1 — 2026-07-16T18:30:00Z — mode: subagent — HEAD f41ba3213784bfeec6e9a7e656fa6e6763fbfba9

**Mode:** subagent (fresh context; did not author design)  
**HEAD:** `f41ba3213784bfeec6e9a7e656fa6e6763fbfba9` (`refs/heads/main`)  
**Working tree:** not shell-verified in this subagent; review inputs are design-only. Confirmed on disk: `python/experiments/INFR-014/` contains `design.md` only (no `code/`, no results); `python/src/xen/nautilus/universe_selection.py` **does not exist** (expected deliverable).  
**Scope:** design completeness / operator-requirement compliance **before** implementation/execution. No code review (none yet). No execution approval.

**Verdict: REVISE**

---

### Design-fidelity trace

| Design clause / requirement | Design § | Verdict | Notes |
|---|---|---|---|
| 1. Fresh Bybit/Nautilus XENA CAL; chapter-03 pin `db87dc1a…` VOID (INFR-010 R4) | §1, §3, §11 HARD, §17.1 | **MATCHES** | New pin path `results/bybit_pc_frozen_registry.json`; archive pin explicit VOID; no path loads ch03 as binding. Aligns `xena-lane.md` VOID clause + ckpt-013 §3. |
| 2. Shape to two classes: conditioning/filter (HTFCAP) + episode-harvest (EPSOSC) | §4, WP1 | **PARTIAL** | Config IDs CLS-FILTER / CLS-EPISODE and family priors are named; **class-shaped null/plant generator contracts are not specified** beyond bullets (see Issue 3). Risk: two identical batteries with different labels. |
| 3. CAL discipline: n_null SE≈0.218/√n; gate point α̂ not UCB; no optional stopping; design/confirm split; one clean cycle | §5.1–§5.3, §11, §16 | **MATCHES** | DESIGN n=80 → SE≈0.024; CONFIRM n=200 → SE≈0.0154 (math correct: √(0.05·0.95)≈0.218). Seeds 91k/92k vs 93k/94k + bite 951k/952k disjoint from INFR-009. Point-α̂ gate, Wilson disclose-only, incomplete bank → no pin. |
| 4. Binder = INFR-009 two-stage CONFIRM DUAL_CERTIFY form re-measured (no threshold invention) | §3, §5.4, §11 BANDS | **MATCHES** (schema gap → Issue 2) | Form constants match archived `pc_frozen_registry.json` / `calibration_pc.py` (embargo 0.20, search/ranking 0.50/0.25, leg_studentized, n_boot 200, α 0.05, one_subset, Fork B). Freezables = measured α̂/cov only. Dual-class **pin schema** still dual-option / unfrozen (Major). |
| 5. Net-cost-binding selection (L-26) with `xen.evaluation.bybit_round_trip_cost_bps` | §6, COST-STACK, §17.5–6 | **PARTIAL** | Intent correct and TIGHTER vs P5 flat 1.0 bps; API named and exists (`evaluation.py`). **Stage-1 g_net scoring path under-specified** vs archived `charge_costs=False` + search `score_kind="g_gross"` (Issue 1). CLS-EPISODE “preferred” not binding — acceptable for L-26 (filter-specific) if declared. |
| 6. L-27 guard: limit → next-open or battery inadmissible; absorb SPDR-005 §2.3 | §7.1, §7.3, §12.6 | **MATCHES** | CAL `limit_entry_cells: false`; future limits require control or inadmissible; next-open apparatus required even if unused. Covers SPDR-005 §2.3(a). Clause (b) (no certify solely on limit-print) is implicit via market-only CAL + pin-usage amend rule — strengthen wording (Minor). |
| 7. S1 multi-instrument single-engine smoke; bitwise determinism; L-30/L-31 | §8, §11 HARD, G3 | **MATCHES** | Path A multi-instr single node vs Path B subprocess-per-instrument; `dispose_on_completion=False`; one node/process; PASS/FAIL → batch topology; TRAIN fence; estimand gate v2; L-29 fill-ts sample. |
| 8. NEW `xen.nautilus.universe_selection`: PIT ≤t−1, rebalance+hysteresis, membership parquet + rule_hash | §9, WP0, G1 | **MATCHES** | Module absent as expected. API, causality assert, pools (SPDR listed vs XENA PIT+delisted), artifacts, tests (causality/determinism/tie-break/fence), golden G1 — implementable/testable. Elevates ckpt-013 §5 “not blocking” to blocking for **pin usage on real membership** (consistent with operator req + XENA need). |
| 9. TRAIN-only / no holdout; ∥ SPDR per D4; stop at design+QA | header, §10, §14, §19 | **MATCHES** | No TEST/holdout; no `run_final_gate` on live families; parallel SPDR cited; stop + operator gates explicit. |
| 10. L-28 derangement for permutation destroys | §7.2, §15 CONTROL, §11 HARD | **MATCHES** | `destroy form: DERANGEMENT`; regenerate fixed points; alignment-break not P&L shuffle (L-14). |

---

### Golden-trace / acceptance checks

Design §13 predeclares infra golden events (no implementation to diff yet). Completeness check:

| ID | Design expectation | Pre-impl verdict | Notes |
|---|---|---|---|
| G1 | `rule_hash` stable under key reorder; membership@asof matches hand top-10 volume ≤t−1 on fixture day | **ACCEPTABLE as written** | Testable once WP0 lands; ε on asof window should be named in tests (Minor). |
| G2 | design bank refuses confirm-seed reuse (assert disjoint) | **ACCEPTABLE** | Seeds predeclared; assert must be code-enforced (design §17.2). |
| G3 | S1: 3 instruments; dispose_on_completion=False; non-empty reports; fill-ts anchor; no second BacktestNode in-process | **ACCEPTABLE** | Matches L-30/L-31/L-29. Canonicalisation rule for “overlapping columns” needs emission-contract column list at implement time. |
| G4 | confirm gate takes frozen procedure dict only — no free thresholds | **PARTIAL** | Intent good; **α̂ event definition** (what counts as stage-2 “pass” for e2e α) not pinned relative to stage2 net (Issue 4). |

Additional acceptance surfaces present: integrity HARD vs INFORMATIVE split (§11), bands CERTIFIED/FAIL_*/DUAL_CERTIFY, exit criteria §12, power §16, artifacts §18.

---

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| No family / registry family status transitions from this INFR | **PASS** | §10 no live family XENA; §14 live family runs = 0; infrastructure CAL only. |
| No inventing free thresholds (procedure constants vs measured α̂) | **PASS** (pending Issues 1–4 not inventing thresholds) | §3, §5.4, §14 “Frozen invented thresholds: 0”. |
| XENA VOID: design must not allow ch03 pin on Bybit | **PASS** | §3 VOID table; §11 HARD; §17.1; new pin path only. |
| Integrity hard vs informative split present | **PASS** | §11 HARD / INFORMATIVE blocks. |
| Holdout sealed / TRAIN-only | **PASS** | §2, §9.2 band=TRAIN, §10, §14. |
| L-23 amendment direction for post-design edits | **PASS** | §3 form-change rule; §6 TIGHTER tags vs P5; L-23 ledger if post-design edit. |
| L-26 net binds selection (filter class) | **GAP** | Declared binding stage-1 for CLS-FILTER but mechanics incomplete (Issue 1). |
| L-27 / SPDR-005 §2.3 handoff | **PASS** (Minor on 2.3b wording) | §7. |
| L-28 derangement in CONTROL block | **PASS** | §15 `destroy form: DERANGEMENT`. |
| L-30 / L-31 | **PASS** | §8, §11. |
| No optional stopping / under-n freeze | **PASS** | §5.1, §17.3. |
| Gate on point α̂ not UCB | **PASS** | §5.1, §17.4. |
| Cost API = `bybit_round_trip_cost_bps` (L-22 stack) | **PASS** naming | Fee RT 2×5.5=11.0 comment consistent with `evaluation.py`. |
| Stop at design+QA; execution operator-gated | **PASS** | header, §19. |
| Fresh-context QA skill constraints | **PASS** | This run: design-only review; only writes `qa-review.md`. |

---

### Issues

1. **Major — Stage-1 net-binding under-specified (L-26 vs archived costless search)** — design §6, §5.4  
   **Problem:** Design binds CLS-FILTER stage-1 to **`g_net` with Bybit costs charged**, and marks costless `g_gross` as disclosure-only. Archived `calibration_pc.run_two_stage` always uses `OracleConfig(charge_costs=False)` and `search.run_restart` scores **`score_kind="g_gross"`** (`robust_g_hat` gross). Design does **not** pin the implementation contract for that change:  
   - Does stage-1 set `charge_costs=True` with per-stream `cost_bps` prefilled from `bybit_round_trip_cost_bps`?  
   - Or does search evaluate intensive `g_net` without oracle cost charging?  
   - How do **synthetic** null streams obtain `hold_hours` / funding for RT (leg duration distribution)?  
   - Is costless stage-1 a **hard refuse** for CLS-FILTER (assert), or only a documented preference?  
   **Risk:** Implementer ports P-C harness with only stage-2 Bybit inject (P5 shape) → **L-26 still violated** for HTFCAP while looking “Bybit-complete.”  
   **Required change:** In design §6 (or §5.4 procedure dict), predeclare a single stage-1 scoring path per class, including score_kind, cost injection site, synthetic hold/funding defaults, and a hard integrity assert that CLS-FILTER confirm/search cannot run with costless stage-1.

2. **Major — Dual-class pin schema ambiguous** — design §4, WP4, §14 “v3 Bybit schema”  
   **Problem:** Predeclaration is dual: “prefer one registry with `class_configs[]`” **or** “two sibling pins with a joint manifest.” No frozen field list for `class_configs[]` entries (procedure, seeds, confirm_summary, limit_entry_cells, cost_stack version, selection_rule_hash policy). No rule for: one class DUAL_CERTIFY and the other FAIL/partial — is a partial registry writable? How does a XENA universe bind the matching class block (manifest field name)?  
   **Risk:** Implementer invents schema at write time; `verify_frozen_registry` today only re-hashes (`calibration.py`) — v3 accept path can ship without class-routing guarantees.  
   **Required change:** Lock **one** artifact shape (recommend single file + `class_configs[]`); list required keys per class block; pin partial-write policy; pin universe→class selection field.

3. **Major — Class-shaped null/plant generators under-specified** — design §4, WP1, mechanism block  
   **Problem:** ckpt-013 §3 requires CAL **shaped** to filter vs episode classes. Design names implications (“filter thinning must be able to win under net”; “episode/leg-level streams”; “avoid cadence-only artifacts”) but does not specify generator contracts: candidate roles (filtered vs unfiltered twins?), thinning mechanism under null, episode length / clear-time distributions, what differs from `make_null_universe` / p3b LOW/HIGH.  
   **Risk:** Both classes re-use the same cadence-null battery → dual pin is cosmetic; HTFCAP net-binding never stress-tested against a filter-shaped null.  
   **Required change:** Minimal per-class generator spec (inputs, candidate structure, null properties, plant for bite) sufficient to implement WP1 without invention.

4. **Major — e2e α̂ event definition vs stage-2 net deployability** — design §5.1, §5.4, BANDS  
   **Problem:** Gate is `point α̂ ≤ 0.05 ∧ no_search_cov ≤ 0.05`. Procedure lists stage-2 **gross** LCB and stage-2 **net** LCB after Bybit RT. Archived confirm α counted **`n_gross_lcb_positive`** / `gross_pass`; P5 net was deployability on the selected subset. Design does not state whether a false-positive for α̂ is (a) stage-2 gross pass only (P5 form, net disclosed/binding separately on top-1), or (b) gross ∧ net both positive.  
   **Risk:** Different α̂ definitions → different certify outcomes and non-comparable “DUAL_CERTIFY” semantics.  
   **Required change:** One sentence in §5.1/§5.4: define the e2e pass event; state whether net is inside α̂ or a separate deployability binding field on the pin (and if separate, when it can fail the class pin).

5. **Minor — SPDR-005 §2.3(b) not explicit in pin-usage rules** — design §7.1  
   Forward note requires CF-EPSOSC not be certified **solely** on limit-print passive edge. Covered indirectly by market-only CAL + amend-for-limits. Prefer explicit registry/pin-usage sentence quoting §2.3(b).

6. **Minor — Module path naming drift for next-open control** — design §7.3  
   Proposes `xen.xena.fills_basis…` while existing module is `xen.xena.fill_basis`. Pick one home to avoid dual modules.

7. **Minor — G1 asof ε / fixture day not named** — design §9.1, §13 G1  
   `asof_ts−ε` causality needs a concrete ε (e.g. 1 bar / 1 ns) in the test contract.

8. **Minor — Doc item numbering** — §5 “item 1”, §6 “item 3”, §7 “item 4”  
   Skips item 2; non-blocking hygiene.

---

### Summary

INFR-014 design correctly frames a **fresh Bybit XENA CAL**: chapter-03 pin VOID, INFR-009 two-stage DUAL_CERTIFY form re-measured (not threshold-copied), n_null/SE math and design/confirm discipline sound, L-27/L-28/L-30/L-31 and TRAIN-only stop conditions present, and `universe_selection` is specified enough to ship/test. **REVISE** before implementation: bind **how** stage-1 net-cost search actually runs (L-26), freeze the **dual-class registry schema**, specify **class-shaped generators**, and define the **e2e α̂ pass event** relative to stage-2 net. No REJECT triggers (no holdout contact, no VOID pin as binding, form not fundamentally wrong). After design.md addresses Issues 1–4, re-run QA; do not execute.

---

## QA run 2 — 2026-07-16T20:15:00Z — mode: subagent — HEAD f41ba3213784bfeec6e9a7e656fa6e6763fbfba9

**Mode:** subagent (fresh context re-review after design REVISE; did not author design)  
**HEAD:** `f41ba3213784bfeec6e9a7e656fa6e6763fbfba9` (`refs/heads/main`)  
**Working tree:** design-only inputs; on disk: `design.md` + `qa-review.md` (no `code/`, no results). `universe_selection.py` still absent (expected pre-exec).  
**Scope:** Re-trace run-1 Issues 1–4 (Majors) + Minors 5–7 + all 10 operator requirements against **updated** `design.md`. Append-only; run 1 left intact. No execution approval.

**Verdict: APPROVE**

---

### Run-1 Major re-trace (Issues 1–4)

| # | Issue | Status | Evidence in updated design |
|---|---|---|---|
| 1 | Stage-1 net-binding under-specified (L-26) | **CLOSED** | **Single contract** §5.4 + §6.1: both classes `score_kind="g_net"`, `OracleConfig.charge_costs=True`, per-leg/stream `cost_bps` from `bybit_round_trip_cost_bps(...)`. **Hard refuse** `IntegrityError` if `charge_costs is False OR score_kind != "g_net"`. Synthetic hold defaults: CLS-FILTER `max(1/60, exit−entry)` else LOW **8.0 h** / HIGH **2.0 h**; CLS-EPISODE `episode_duration_hours`; GAP `spread_bps=5.0`. Companion `g_gross` disclosure only — never search key. Porting P-C costless stage-1 is process FAIL, not a variant. |
| 2 | Dual-class pin schema ambiguous | **CLOSED** | **Single file only** (§4, §4.2) — “no sibling-pin dual option.” Schema id `xena.infr014.bybit_pc_registry.v1`. Frozen `class_configs[]` keys: `class_id`, `family_prior`, `procedure`, `design_seeds`, `confirm_seeds`, `cost_stack`, `stage1_score_kind`, `stage1_charge_costs`, `e2e_pass_event`, `deployability_binding`, `confirm_summary`, `limit_entry_cells`. **Partial-write:** write iff ≥1 class verdict ∈ {DUAL_CERTIFY, HIGH_ONLY_CERTIFY, LOW_ONLY_CERTIFY}; TERMINAL classes present with `certified: false`, not live-selectable. Manifest field **`xena_class_id`**: gate refuses missing/unknown/uncertified. Universe→pin via `verify_frozen_registry` + match `class_configs[i]`. |
| 3 | Class-shaped null/plant generators under-specified | **CLOSED** | §4.1 binding contracts. **CLS-FILTER** `make_filter_null_universe`: BASE (unfiltered high-cadence) + FILT (same entries thinned by synthetic HTF gate, τ∈{0.3,0.5,0.7}); null E[g]≈0 both; costless prefers BASE; plant_filter stage-1 FILT +edge, BASE unplanted; bite select-FILT ≥0.5 / stage-2 survival ≤0.125; n_cand=64 ≥25% each. **CLS-EPISODE** `make_episode_null_universe`: episode objects entry→marks→clear; D~trunc lognormal (median 4h LOW / 1h HIGH, cap 48h); plant_episode stage-1-only; hold=episode duration; all episode-shaped. Factories must differ (class id on streams; refuse byte-identical factories). Shared p3b LOW/HIGH shell only. |
| 4 | e2e α̂ event vs stage-2 net | **CLOSED** | §5.1 frozen: false-certify IFF `stage-2 lcb_g_leg_studentized(g_gross) > 0` on stage-1 top-1 (P-C / P5 `n_gross_lcb_positive`). **α̂ = (# false-certifies)/n_null**. Stage-2 net is **separate deployability field** (`deployability_pass ⇔ LCB(g_net)>0`); **not inside α̂**. DUAL_CERTIFY may write on gross even if net weak; deployability disclosed; live XENA still charges net; operator fork for net-binding pin acceptance. Schema pins `e2e_pass_event` / `deployability_binding`. BANDS: DEPLOY_WEAK = alpha CERTIFIED but net often ≤0 (disclosure). |

**All four Majors closed. No new Critical or Major found.**

---

### Run-1 Minor re-trace (5–7 + 8)

| # | Issue | Status | Evidence |
|---|---|---|---|
| 5 | SPDR-005 §2.3(b) pin-usage wording | **CLOSED** | §4.2 `pin_usage.limit_print_sole_certify_forbidden: true` + note; §7.1 explicit “must not be certified … solely on a limit-print passive edge (P-10 + L-27).” |
| 6 | `fills_basis` vs `fill_basis` path drift | **CLOSED** | §7.3: implement on **existing** `fill_basis` module only; never parallel `fills_basis` package. Registry tool string still says `xen.xena.fill_basis…` in §4.2 JSON — cosmetic string vs §7.3 binding path; implementers must use `fill_basis` (see Residual note R1). |
| 7 | G1 asof ε | **CLOSED** | §9.1: `ts_event ≤ asof_ts − 1ns` (ε = 1 nanosecond strictly before asof; equiv. last closed 1m bar). |
| 8 | Doc item numbering skips “item 2” | **OPEN (hygiene)** | Still §5 item 1, §6 item 3, §7 item 4… Non-blocking; does not block APPROVE. |

---

### Operator-requirement re-trace (all 10)

| # | Requirement | Verdict | Notes |
|---|---|---|---|
| 1 | Fresh Bybit/Nautilus XENA CAL; ch03 pin VOID | **MATCHES** | §1, §3, §11 HARD, §17.1; new pin path only. |
| 2 | Shape to CLS-FILTER (HTFCAP) + CLS-EPISODE (EPSOSC) | **MATCHES** | §4 + §4.1 generator contracts (was PARTIAL run 1). |
| 3 | CAL discipline: n_null SE; point α̂; no optional stopping; design/confirm; one clean cycle | **MATCHES** | §5.1–5.3, §11, §16 unchanged and sound. |
| 4 | Binder = INFR-009 two-stage DUAL_CERTIFY form re-measured | **MATCHES** | §3, §5.4 form constants; dual-class schema frozen (was schema gap). |
| 5 | Net-cost-binding (L-26) via `bybit_round_trip_cost_bps` | **MATCHES** | §5.4, §6, §6.1 single contract + hard refuse (was PARTIAL). |
| 6 | L-27 limit → next-open or inadmissible; SPDR-005 §2.3 | **MATCHES** | §7.1–7.3; 2.3(b) explicit in pin_usage. |
| 7 | S1 multi-instrument smoke; L-30/L-31 | **MATCHES** | §8, G3, §11 HARD. |
| 8 | NEW `xen.nautilus.universe_selection` PIT ≤t−1 | **MATCHES** | §9 API/integrity/tests; ε named; WP0 blocking. |
| 9 | TRAIN-only; ∥ SPDR; stop at design+QA | **MATCHES** | header, §10, §14, §19. |
| 10 | L-28 derangement destroys | **MATCHES** | §7.2, §15, §11 HARD. |

---

### Golden-trace / G4 re-check

| ID | Verdict | Notes |
|---|---|---|
| G1 | **ACCEPTABLE** | ε = 1 ns pinned; fixture-day hand-rank still implement-time. |
| G2 | **ACCEPTABLE** | Seeds + code assert disjoint. |
| G3 | **ACCEPTABLE** | Unchanged S1 / L-30/L-31/L-29. |
| G4 | **ACCEPTABLE** (was PARTIAL) | α̂ event + deployability field frozen §5.1/§5.4; gate takes frozen procedure dict only. |

---

### Governance & boundary (run 2)

| Check | Result |
|---|---|
| No family / registry family status transitions | **PASS** |
| No invented free thresholds | **PASS** |
| Ch03 pin not binding on Bybit | **PASS** |
| Integrity HARD vs INFORMATIVE | **PASS** |
| Holdout sealed / TRAIN-only | **PASS** |
| L-26 stage-1 net binding mechanics | **PASS** (closed Major 1) |
| L-27 / L-28 / L-30 / L-31 | **PASS** |
| Point α̂ gate; no optional stopping | **PASS** |
| Stop at design+QA; execution operator-gated | **PASS** |
| New Critical/Major from REVISE | **NONE** |

---

### Residual notes (non-blocking; do not reopen REVISE)

- **R1 (cosmetic):** §4.2 JSON `l27_next_open_tool` string still reads `xen.xena.fill_basis…` while §7.3 binds implementation to existing `fill_basis`. Prefer aligning the registry string at write time to `xen.xena.fill_basis.next_open_discriminating_control` so pin matches import path. Not a Major (binding prose is clear).  
- **R2 (hygiene):** Doc “item N” numbering still skips item 2 (run-1 Minor 8).  
- **R3 (implementer):** plant `edge_bps` magnitude for bite power is success-criterion-driven (select rate ≥0.5 / survival ≤0.125), not a frozen numeric — same pattern as archived P-C; acceptable.

---

### Summary (run 2)

Updated `design.md` closes all four run-1 Majors: (1) stage-1 single contract `g_net` + `charge_costs=True` + hard refuse + synthetic hold defaults; (2) single-file `class_configs[]` schema with partial-write + `xena_class_id`; (3) CLS-FILTER BASE/FILT vs CLS-EPISODE episode generator contracts; (4) e2e α̂ = stage-2 **gross** LCB only, net = separate deployability field. Minors 5–7 closed; Minor 8 hygiene remains. All 10 operator requirements **MATCHES**. No new Critical/Major. No REJECT integrity triggers.

**Verdict: APPROVE** — design complete for operator execution gate. Execution remains **operator-gated** (§19); this QA does **not** authorize WP0–WP7 execution.

---

## QA run 3 — 2026-07-17T04:16:43Z — mode: subagent — HEAD fe8bf598efe49b64b459a763471b5df33375bf3b

**Mode:** subagent (fresh context; did not author implementation).  
**HEAD:** `fe8bf598efe49b64b459a763471b5df33375bf3b` (main). Dirty/untracked reviewed state: `python/experiments/INFR-014/{code,results,report.md}`, `python/src/xen/nautilus/universe_selection.py`, `python/src/xen/xena/calibration_bybit.py`, modified `xen/xena/{certify,search,fill_basis}.py`, `xen/nautilus/__init__.py`, tests `test_universe_selection.py` / `test_xena_infr014.py` (all untracked/modified, not yet committed).  
**Scope:** post-implementation, post-execution full compliance review (requested as "QA run 2" of the implementation cycle; numbered run 3 here because this file already contains two appended runs). Reviewed: design.md, prior QA runs, report.md, `code/` (run_cal.py, run_s1_smoke.py, clause_map.md), all `results/` artifacts, and referenced source modules. 18/18 unit tests pass (`pytest tests/test_universe_selection.py tests/test_xena_infr014.py`).

**Verdict: REVISE** — one Major execution-fidelity defect (confirm-bank coverage leg ran on DESIGN seeds), plus S1 spec deviations undeclared in the report. Scope-limiting fact: both classes came out **TERMINAL** and **no registry pin was written** (partial-write policy correctly refused), so no invalid pin exists; the REVISE binds any future re-CAL / pin attempt and the report's deviation ledger, not a shipped certification.

### Run-1 issue resolution table (Issues 1–8, verified against code)

| # | Run-1 issue | Status | Evidence |
|---|---|---|---|
| 1 | Stage-1 g_net scoring path under-specified (L-26) | **RESOLVED** | `calibration_bybit.py:83-89` `assert_stage1_net_binding` raises `IntegrityError` on costless/`!=g_net`; `run_two_stage` (:334-357) hardcodes `OracleConfig(charge_costs=True)` + `score_kind="g_net"` in `run_restart` and `certify_and_rank`; plumbing exists in `search.py:325,357-359` and `certify.py:302-330`; hold/funding defaults `HOLD_DEFAULT_H` (:64), `bybit_cost_bps_for_hold` (:92-110); enforced again at confirm (`confirm_gate` :760-763); test `test_hard_refuse_costless_stage1`. |
| 2 | Dual-class pin schema unfrozen | **RESOLVED** | Single-file schema `xena.infr014.bybit_pc_registry.v1` in `write_bybit_registry` (:871-954) with all §4.2 keys per class block; `verify_bybit_registry` (:957-988) checks schema/substrate/limit_entry_cells/pin_usage/g_net; partial-write policy implemented and **exercised**: refused with 0 certifiable classes (`results/registry_verify.json` ok=false). Test `test_registry_schema_and_verify`. |
| 3 | Class-shaped null/plant generator contracts unspecified | **RESOLVED** | `make_filter_null_universe` (:134-242, BASE+FILT, τ∈{0.3,0.5,0.7}, ≥25% each) vs `make_episode_null_universe` (:248-303, truncated-lognormal episode durations median 4h/1h cap 48h); `factory_fingerprint` module-level assert (:314-316); bite plant/deplant incl. `_deplant_class_plants` (:463-485); tests `test_factories_differ`, `test_filter_universe_has_base_and_filt`, `test_episode_universe_episode_shaped`. |
| 4 | α̂ event definition not pinned | **RESOLVED** | `run_two_stage` α̂ event = `eval_lcb_legs(..., net=False)` gross LCB on top-1 (:374-388); net is a separate `net_pass` deployability field (:379-393), never in `e2e_alpha` numerator (:567 counts `gross_pass` only); frozen dict pins `e2e_pass_event: stage2_gross_lcb_positive` / `deployability_binding` (:699-700) and registry echoes them. |
| 5 | SPDR-005 §2.3(b) wording | **RESOLVED** | `pin_usage.limit_print_sole_certify_forbidden: true` + note in registry payload (:935-941); `verify_bybit_registry` enforces (:972-973). |
| 6 | fills_basis vs fill_basis drift | **RESOLVED** | Implementation on existing `xen/xena/fill_basis.py` (`next_open_discriminating_control` :307); registry string `xen.xena.fill_basis.next_open_discriminating_control` (:933). No parallel package. |
| 7 | G1 asof ε | **RESOLVED** | `_ASOF_EPS_NS = 1` / `_asof_cutoff_ns` (`universe_selection.py:24,61-63`); causality test passes. |
| 8 | Doc item numbering (hygiene) | **OPEN (hygiene)** | Unchanged; non-blocking. |

### Design-fidelity trace (execution)

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| Fresh Bybit CAL; ch03 pin `db87dc1a` never loaded (§3, §17.1) | `VOID_PRIORS` (:68-71); no code path reads `pc_frozen_registry.json`; grep clean | **MATCHES** | Registry not written (TERMINAL), so no new pin either. |
| Seeds disjoint: design 91k/92k, confirm 93k/94k, bite 951k/952k, archive-disjoint (§5.2, G2) | `DESIGN_SEEDS/CONFIRM_SEEDS/BITE_SEEDS` (:52-54); `assert_seed_disjoint` (:612-634) called in `run_design` and `confirm_gate` | **DEVIATES (Major — Issue 9)** | Constants are correct and statically disjoint, but at runtime `no_search_coverage` (:507-508) re-sets `p3b` seed bases to **DESIGN_SEEDS** unconditionally, overriding `confirm_gate`'s `_set_seeds(CONFIRM_SEEDS…)` (:778). Emitted evidence: `confirm_CLS-FILTER.json` coverage rows seeds 91000…/92000… (design bank) while α̂ rows are 93000…/94000… (confirm bank). Confirm coverage gate leg was measured on the design bank. |
| n_null DESIGN 80 / CONFIRM 200; no optional stopping; point-α̂ gate not UCB (§5.1) | `DESIGN_SCALE`/`CONFIRM_SCALE` (:56-59); run_cal.py:110-111 hard `n_null=200`; `confirm_gate` :770-773; certified = `cov_ok ∧ alpha_ok` on point rates (:791); Wilson recorded disclosure-only (:575, :811) | **MATCHES** | Confirm artifacts show n=200 per cadence per class; single pass, no extension. |
| α̂ event = stage-2 gross LCB>0 on top-1; net separate (§5.1/§5.4) | see run-1 Issue 4 row | **MATCHES** | — |
| Bite: select ≥0.5, survival ≤0.125, stage-1-only plant, Fork B TERMINAL (§4.1, §5.3) | `bite_check` (:404-460); `run_design` early TERMINAL return (:661-677); results: all four bite cells PASS | **MATCHES** | Bite uses BITE_SEEDS; deplant applied for both generic and class plant prefixes. |
| One clean cycle; confirm blocked without design_ok (§5.3, §17.12) | `confirm_gate` refuses without `design_bite_ok` procedure (:750-751); run_cal skips confirm when `design_ok` false (:102-104) | **MATCHES** | — |
| COST-STACK L-26/L-22: `bybit_round_trip_cost_bps`, taker, GAP spread 5.0, funding 1.0/8h, hold-derived (§6, §6.1) | `bybit_cost_bps_for_hold` (:92-110) → `xen/evaluation.py:419` (fees 2×side + T1 spread + funding×hold/8); `cost_pins.json` discloses GAP | **MATCHES** | Per-leg hold from trade spans with cadence defaults 8h/2h (:119-128). |
| L-28 derangement destroys (§7.2) | No index/label permutation exists anywhere in the α̂/coverage path (grep `permut|derange` over calibration_bybit + deps: none); nulls are synthetic path nulls; plant removal is analytic deplant | **MATCHES (N/A)** | clause_map declares this; consistent with L-28 (rule binds only if a permutation destroy is used). |
| L-27 next-open control shipped on `fill_basis` even if unused (§7.3) | `fill_basis.py:307` + `next_open_sanity_artifact` (:991-994); `results/next_open_control.json` gap ≈ −0.86 bps ≈ 0 | **MATCHES** | Near-zero discrimination as design's sanity expectation. |
| `limit_entry_cells: false` + pin_usage rules (§4.2, §7.1) | write/verify enforce; registry not written this run | **MATCHES** | Values present in `write_bybit_registry` payload and verifier. |
| Partial-write policy (§4.2) | `write_bybit_registry` raises when 0 certifiable (:922-926); exercised → `registry_verify.json` ok=false; no pin file on disk | **MATCHES** | Correct refusal; XENA counted path stays blocked (report §6). |
| universe_selection PIT ≤t−1, fence, rule_hash, hysteresis, pools (§9) | `universe_selection.py`: ε=1ns cutoff (:61-63), HOLDOUT unconditional refuse (:208-209), band-bounds + `assert_within_fence` (:219-238), `rule_hash` canonical JSON (:47-50), hysteresis (:163-188), pools field; 7 unit tests pass | **MATCHES** | `selection_rule_default.json` hash `0dd53037…` recorded; membership parquet series builder present (real-catalog series deferred, disclosed in `membership_rule_0dd530374fd3.json`). |
| S1 smoke spec (§8, L-29/L-30/L-31) | `run_s1_smoke.py`; `s1_smoke.json` PASS, topology `multi_instrument_single_node` | **DEVIATES (Issue 10)** | dispose_on_completion=False (:229), one node/process with replay in subprocess (:264-295), N=3, reports non-empty — all match. But: PASS criterion is Path-A **self-replay** bitwise, not the design's Path A vs Path B overlapping-column identity (A-vs-B equality holds for BTC digest `735323b9…` but is not gated); instruments are **synthetic bars**, not ADMITTED perps under TRAIN PINNED fence attestation; estimand-gate v2 `blocking_pass` not applied; Path A's single EMACross trades only BTC, so multi-instrument execution is exercised as data-load, not multi-strategy fills; L-29 anchor check is nearest-open rel<5% (not next-bar RealOpen ±1 tick) and excluded from overall PASS (:394-396). |
| TRAIN-only, no holdout/TEST (§10, §11 HARD) | CAL banks fully synthetic; S1 synthetic temp catalog; universe_selection refuses HOLDOUT; no TEST read anywhere in `code/` | **MATCHES** | No holdout contact possible in this run. |
| Artifacts §18 | All present except `bybit_pc_frozen_registry.json` (correctly absent) and membership **parquet** (JSON stub note instead) | **MATCHES (note)** | Membership parquet deferred to live XENA use; disclosed. |

### Golden-trace table

| ID | Design expectation | Verdict | Evidence |
|---|---|---|---|
| G1 | rule_hash stable under key reorder; membership@asof = hand top-n ≤t−1 | **PASS** | `test_rule_hash_stable_under_key_reorder`, `test_causality_future_volume_cannot_enter_rank`, `test_tie_break_lexicographic_id`, `test_determinism_byte_identical` — all green. |
| G2 | design bank refuses confirm-seed reuse | **PARTIAL** | `assert_seed_disjoint` + `test_seed_disjoint` verify **constant** disjointness, but the guard did not catch the runtime reuse in Issue 9 (confirm coverage silently ran on design seeds). Guard is necessary but insufficient as implemented. |
| G3 | S1: 3 instruments, dispose=False, non-empty reports, fill-ts sample, no 2nd node in-process | **PASS (with Issue 10 caveats)** | `s1_smoke.json` criteria block all true; replay via fresh subprocess respects L-31 logging constraint. |
| G4 | confirm gate takes frozen procedure dict only — no free thresholds | **PASS (minor note)** | `confirm_gate` requires and consumes frozen keys (:753-768); no CLI-injectable thresholds. Minor: `e2e_alpha`/`no_search_coverage` compare against module global `ALPHA` rather than `procedure["alpha"]` (same value 0.05) — Issue 13. |

### Governance table

| Check | Result | Evidence |
|---|---|---|
| No family status transitions | **PASS** | report.md §10 "Family status transitions: none"; no registry/family docs touched by code. |
| No invented thresholds | **PASS** | All gate constants inherited (§5.4) or measured; bite thresholds match design (`test_bite_thresholds_match_design`); TERMINAL outcome accepted rather than retuned. |
| No holdout/TEST touch | **PASS** | Synthetic CAL; HOLDOUT refuse coded + tested; no TEST reads. |
| ch03 pin not loaded on Bybit | **PASS** | VOID_PRIORS only as strings; no load path. |
| `check_no_local_accounting` scope | **PASS** | No accounting primitives in `experiments/INFR-014/code/`; verdicts derive from `xen.xena`/`xen.evaluation` shared modules; S1 uses Nautilus reports for smoke identity only, not P&L adjudication. |
| No Python-strategy backtest as evidence | **PASS (noted)** | S1 EMACross run is an infrastructure determinism smoke (design-sanctioned §8), not a candidate evaluation. |
| L-23 amendment ledger | **PASS** | No post-design procedure edits found; report declares "none silent" (but see Issue 10 — S1 deviations should have been declared). |
| Registry pin sign-off remains operator's | **PASS** | report §9/§11 leaves verdict to operator; recommends TERMINAL, no pin. |

### Issues (numbering continues from run 1)

9. **Major — CONFIRM coverage leg ran on DESIGN seeds (design §5.2 design/confirm split violated at runtime).** `python/src/xen/xena/calibration_bybit.py:507-508`: `no_search_coverage` unconditionally calls `_set_seeds(DESIGN_SEEDS…)` internally, clobbering `confirm_gate`'s `_set_seeds(CONFIRM_SEEDS…)` (:778-779). Emitted proof: `results/confirm_CLS-FILTER.json` (and CLS-EPISODE) `coverage_low_rows`/`coverage_high_rows` seeds are 91000…/92000… while `alpha_*_rows` are 93000…/94000…. The binding certify gate is `cov_ok ∧ alpha_ok`, so one of its two legs was measured on the design bank (overlapping the n=80 design-coverage universes). Consequence bounded this run — both classes TERMINAL, no pin written — but the confirm coverage numbers (and `selection_inflation` / `failure_label: coverage_limited` readings in report §5/§9) are design-bank quantities mislabeled as confirm-bank. **Required change:** remove the internal `_set_seeds` (seed control belongs to the caller) or parameterize the bank; add a runtime assert that emitted row seeds fall in the caller's declared bank; any future re-CAL or pin attempt must not reuse these confirm files' coverage legs. Route: experiment-developer.
10. **Moderate — S1 smoke deviates from design §8 and deviations are undeclared.** `code/run_s1_smoke.py`: (a) PASS gates on Path-A self-replay bitwise identity (:390,394-396), not Path A vs Path B overlapping-column identity; A-vs-B match exists for BTC (`735323b9…` both) but is not asserted; (b) instruments are synthetic (`synthetic_bars`, temp catalog), not "N≥3 ADMITTED Bybit perps" under "TRAIN-only, PINNED attestation"; (c) estimand-gate v2 `blocking_pass` never invoked; (d) Path A trades only inst0 (BTC) — multi-instrument is data-load-level, fills are single-instrument; (e) L-29 anchor implemented as nearest-open rel-err <5% (design: next-bar RealOpen ±1 tick) and excluded from the overall PASS conjunction. report.md §2 "Deviations: none silent" and §3 "PASS" therefore overstate; the `multi_instrument_single_node` topology recommendation (informative per §11) rests on weaker evidence than designed. **Required change:** either declare these as operator-approved deviations in report.md (+ downgrade the S1 evidence claim), or re-run S1 per spec before relying on the topology decision for live XENA batches. Route: experiment-developer / documenter.
11. **Minor — `cal_summary.json` not reproducible from committed runner.** `code/run_cal.py` returns 1 on registry refusal (:145) *before* writing the summary, and its summary dict (:149-166) lacks `s1_outcome`/`s1_topology`/`registry_written`/`recommend` keys present in `results/cal_summary.json`. The artifact was evidently produced by a later/variant runner state not in `code/`. Provenance hygiene: commit the runner that wrote the artifact, or regenerate the summary. Non-verdict-material (per-class confirm files + `cal_run.log` are internally consistent).
12. **Minor — dead/vacuous code in shipped harness.** `calibration_bybit.py:984-988` VOID-prior loop in `verify_bybit_registry` is a no-op (`continue` only — the intended "never accept ch03 as binding" check checks nothing); `:199` unused `w` weights in the FILT thinning gate; `:238-240` no-op class-tag loop (class identity carried only by id prefix — declared in clause_map, acceptable, but the dead loop should go). Clean up on next touch.
13. **Minor — gate constants partially read from module globals.** `e2e_alpha` (`pass_stop`, :578) and `no_search_coverage` (`coverage_ok`, :529) compare to global `ALPHA` rather than the frozen `procedure["alpha"]` passed to `confirm_gate`. Values are identical (0.05); G4 spirit says thread the frozen dict through.

### Summary

Implementation faithfully delivers the QA-approved design on nearly every clause: L-26 net-binding stage-1 with hard refuse, frozen single-file registry schema with a correctly-firing partial-write refusal, distinct class-shaped generators, gross-LCB α̂ event with net as separate deployability, point-α̂ gate at fixed n=200, PIT universe selection with ε=1ns and HOLDOUT refusal (18/18 tests), L-27 apparatus, no holdout/TEST contact, no family transitions, no invented thresholds, ch03 pin untouched. Outcome: both classes **TERMINAL**, **no registry pin** — governed correctly. **REVISE** on: Issue 9 (confirm coverage measured on design seeds — must be fixed before any future confirm/pin run, and the report's coverage-limited reading re-labeled), Issue 10 (S1 §8 deviations undeclared; topology evidence weaker than specified), plus Minors 11–13. Operator pin sign-off recommendation (TERMINAL, no pin) is unaffected in direction by these findings.

---

## Implementation fix note — 2026-07-17 (orchestrator, not independent QA)

Independent post-exec QA: **REVISE** (Issues 9–13). Fixes applied + full re-run:

| Issue | Resolution |
|---|---|
| 9 Major confirm cov on design seeds | `no_search_coverage` no longer calls `_set_seeds(DESIGN_*)`; confirm asserts bases==CONFIRM_SEEDS; artifacts show cov seeds 93000+ |
| 10 Moderate S1 deviations | rewritten `run_s1_smoke.py`: ADMITTED catalog, A-vs-B identity, estimand-v2, PINNED — outcome PASS |
| 11 cal_summary | always written by `run_cal.py` with `producer` field; no early return before summary |
| 12 vacuous void_priors | `verify_bybit_registry` requires VOID prefixes present |
| 13 procedure alpha | confirm gate uses `float(procedure["alpha"])` |

Design §20 L-23 amendments A-1…A-4. Re-run verdict material: CLS-FILTER LOW_ONLY_CERTIFY, CLS-EPISODE TERMINAL, registry pin written. **Fresh-context QA re-review recommended** before operator treats pin as final.

---

## QA run 4 — 2026-07-17T05:02:39Z — mode: subagent — HEAD fe8bf598efe49b64b459a763471b5df33375bf3b

**Mode:** subagent (fresh context; did not author implementation or fixes).
**HEAD:** `fe8bf598efe49b64b459a763471b5df33375bf3b` (main). Dirty/untracked reviewed state: `python/experiments/INFR-014/{code,results,report.md,design.md §20,qa-review.md}`, `python/src/xen/nautilus/universe_selection.py`, `python/src/xen/xena/calibration_bybit.py`, modified `xen/xena/{certify,search,fill_basis}.py`, `xen/nautilus/__init__.py`.
**Scope:** independent post-fix, post-re-execution review. Verified run 3's Issues 9–13 and run 1's Issues 1–8 directly against code and emitted artifacts (numbers recomputed from raw rows, hashes recomputed, tests re-run: **20/20 pass** via `.venv/bin/python -m pytest tests/test_universe_selection.py tests/test_xena_infr014.py`).

**Note on task framing:** the review request described the outcome as "TERMINAL, no registry pin written" — that describes the **discarded first execution**. The current artifacts (this re-run) show CLS-FILTER **LOW_ONLY_CERTIFY**, CLS-EPISODE **TERMINAL**, and a registry pin **WRITTEN** (`bybit_pc_frozen_registry.json`, sha256 `ac8a1eb679e22290d854ad245ef1620f5f8bdb446a5c0166c618d0c292b2da6f` — recomputed independently, matches). This review binds the re-run artifacts.

**Verdict: APPROVE** (for operator pin sign-off; three new Minor issues 14–16 for the ledger, none verdict-material).

### Verification of run-3 issues (independent, against artifacts)

| # | Run-3 finding | Verdict on run 3 | Fix status now | Evidence |
|---|---|---|---|---|
| 9 | Major — confirm coverage ran on DESIGN seeds via `no_search_coverage` re-pinning | **CONFIRMED** (was real: A-1 ledger + report §2 acknowledge; contaminated artifacts discarded) | **FIXED** | `calibration_bybit.py:491-539`: `no_search_coverage` reads caller-set `p3b.SEED_BASE_*`, no internal `_set_seeds`; `confirm_gate` pins CONFIRM_SEEDS once (:796) and hard-asserts `cov["seed_bases"] == CONFIRM_SEEDS` (:805-809) and same for e2e (:820-822). Artifacts: `confirm_CLS-FILTER.json` / `confirm_CLS-EPISODE.json` coverage rows seeds **93000–93605 / 94000–94605** (no 91k/92k); `cal_run.log` prints `bases={'low': 93000, 'high': 94000}` on all four confirm cov legs. Regression test `test_no_search_coverage_respects_caller_seed_bases` passes. |
| 10 | Moderate — S1 deviations from §8 undeclared | **CONFIRMED** (A-2 ledger acknowledges) | **MOSTLY FIXED** — residual regraded Minor (new Issue 14) | Rewritten `run_s1_smoke.py`: ADMITTED catalog BTC/ETH/SOL-LINEAR.BYBIT with existence check (:408-413); TRAIN fence `assert_within_fence` (:182,:287) + emission `fence_attestation.json` `status: PINNED`, manifest sha `35d3375e…`; **A-vs-B** bitwise per symbol gated into overall PASS (:439-467,:490-493) — all 3 symbols match (e.g. BTC fills digest `dad36c3b…` both paths); estimand v2 `blocking_pass` gated (`gate_version: v2`, all true); all 3 instruments trade in Path A (fills 3200/3280/3072). Residual: L-29 anchor form (Issue 14). |
| 11 | Minor — `cal_summary.json` not reproducible from committed runner | **CONFIRMED** | **FIXED** | `run_cal.py:151-172` always writes summary (registry refuse handled via try/except, `registry_verify.json` written either way); `cal_summary.json` carries `"producer": "experiments/INFR-014/code/run_cal.py"`; its per-cadence numbers match `confirm_CLS-*.json` exactly. |
| 12 | Minor — vacuous void-prior loop + dead code | **CONFIRMED** | **PARTIALLY FIXED** | `verify_bybit_registry:1024-1031` now raises when a VOID prefix (`db87dc1a`, `537d691a`) is missing from `void_priors`; test `test_verify_void_priors_required` passes; registry artifact lists both prefixes. Residual dead code remains: unused `w` weights (:199) and no-op class-tag loop (:238-241) — cosmetic, fold into next touch. |
| 13 | Minor — gate compared to global `ALPHA` not `procedure["alpha"]` | **CONFIRMED** | **FIXED** | `confirm_gate:787` `alpha = float(procedure["alpha"])`, threaded into both `no_search_coverage(..., alpha=alpha)` (:799-803) and `e2e_alpha(..., alpha=alpha)` (:816-819); artifacts carry `alpha_target: 0.05` per cell; `stop_condition.gate_rule` cites "alpha from frozen procedure". |

### Run-1 issues 1–8 (re-verified)

1 **RESOLVED** (`assert_stage1_net_binding` :83-89; `run_two_stage` hardcodes `OracleConfig(charge_costs=True)` + `score_kind="g_net"` :348-366; plumbing verified in `search.py:357-359` and `certify.py:317-319`; registry verifier refuses non-g_net class blocks :1017-1019). 2 **RESOLVED** (single-file schema written + hash-verified; sha256 recomputed = stored). 3 **RESOLVED** (distinct factories + module-load fingerprint assert :313-316). 4 **RESOLVED** (α̂ counts `gross_pass` only :583-589; net separate deployability field). 5–7 **RESOLVED** as per run 3. 8 **OPEN (hygiene)** — item numbering unchanged, non-blocking.

### Fresh design-fidelity trace (re-run artifacts, numbers recomputed)

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| Seeds disjoint; confirm on 93k/94k (§5.2, G2, A-1) | `assert_seed_disjoint` :630-652 (design/confirm/bite/archive); artifact row seeds verified | **MATCHES** | Confirm α̂ rows 93000–93605/94000–94605; coverage rows same bank. Design bank rows 91k/92k; bite on 951k/952k. |
| n_null 80/200, no optional stopping (§5.1) | `DESIGN_SCALE`/`CONFIRM_SCALE` :56-59; `confirm_gate` n_null guard :789-792; `run_cal.py:110-111` | **MATCHES** | Every confirm cell n=200. Single pass; recomputed from raw rows: FILTER low 9/200=**0.045**, high 12/200=**0.060**; EPISODE low 15/200=**0.075**, high 16/200=**0.080**; cov 7/200=**0.035**, 13/200=**0.065**, 20/200=**0.100**, 10/200=**0.050** — all match `cal_summary.json` and report §6 exactly. |
| Point-α̂ gate not UCB (§5.1, §17.4) | `pass_stop = ph <= alpha` :592; `coverage_ok = rate <= alpha` :536; Wilson disclosure-only | **MATCHES** | EPISODE low Wilson [0.046,0.120] not consulted by gate. Boundary case cov=0.050 passes per design "≤ 0.05". |
| Bands / verdicts (§11) | `_outcome` :608-627 | **MATCHES** | FILTER: low CERTIFIED (0.045∧0.035), high FAIL_ALPHA → **LOW_ONLY_CERTIFY**. EPISODE: both FAIL_ALPHA → **TERMINAL**. DEPLOY_WEAK disclosed (net pass rate 0.01). |
| Partial-write policy (§4.2) | `write_bybit_registry` :923-965 | **MATCHES** | ≥1 certifiable (LOW_ONLY_CERTIFY) → single-file write; EPISODE present `certified: false`. `verify_bybit_registry` green; sha256 recomputed matches report §7. |
| L-26 net-binding stage-1 (§5.4/§6.1) | see Issue 1 row | **MATCHES** | Hard refuse tested. |
| L-27 apparatus (§7.3) | `next_open_control.json`: gap −0.865 bps ≈ 0 on 592 legs | **MATCHES** | Market-only sanity as designed; registry `l27_next_open_tool` string = `fill_basis` path. |
| L-28 derangement (§7.2) | no permutation destroy exists in α̂/coverage path (grep clean) | **MATCHES (N/A)** | Rule binds only when a permutation destroy is used. |
| PIT ≤t−1 / fence (§9) | `universe_selection.py`: ε=1ns :24,:61-63; HOLDOUT unconditional refuse :208-209; band-bounds + fence assert :219,:238; belt-and-suspenders ts>cutoff skip :247-248 | **MATCHES** | 7/7 unit tests incl. causality, determinism, holdout refusal. `rule_hash` `0dd53037…` pinned in registry. |
| ch03 pin never loaded (§17.1) | grep `pc_frozen_registry|db87dc1a` over harness/code: strings only in VOID list | **MATCHES** | — |
| TRAIN-only / no holdout / no TEST (§10) | CAL synthetic; S1 window 2023-06-01→07-01 < TRAIN end 2023-12-18; attestation PINNED | **MATCHES** | — |
| L-30/L-31 S1 (§8) | `dispose_on_completion=False` :195,:290; one node/process, Path B via fresh subprocesses :364-399 | **MATCHES** | — |
| One clean cycle (§5.3) | confirm requires `design_bite_ok` :769-770; same form constants re-run per §20 (no retune: α gate, n_null, thresholds unchanged) | **MATCHES** | A-1..A-4 are integrity/fidelity fixes, tagged TIGHTER/NEUTRAL (L-23); no LOOSER entries. |

### Golden-trace table

| ID | Verdict | Evidence |
|---|---|---|
| G1 | **PASS** | `test_rule_hash_stable_under_key_reorder`, causality, tie-break, determinism tests green. |
| G2 | **PASS** (was PARTIAL run 3) | Constant disjointness + runtime `seed_bases == CONFIRM_SEEDS` asserts in `confirm_gate` + regression test close the run-3 gap. |
| G3 | **PASS** | 3 ADMITTED instruments, dispose=False, non-empty reports (3200/3280/3072 fills), no 2nd in-process node; A-vs-B identity all symbols. L-29 form residual → Issue 14. |
| G4 | **PASS** | Frozen-procedure-only gate incl. `procedure["alpha"]` (Issue 13 fixed). |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| No family status transitions | **PASS** | report §10; pin is experiment-level, sign-off left to operator (§8/§11). |
| No invented binding thresholds | **PASS (one informative exception → Issue 15)** | All gate constants §5.4 or measured; `_SELECTION_INFLATION_MAX=0.02` labels failure mode only, never gates certification. |
| No holdout/TEST contact | **PASS** | — |
| ch03 pin VOID enforced | **PASS** | verify requires VOID prefixes (Issue 12 fix). |
| `check_no_local_accounting(code/)` | **PASS** | No accounting primitives in `experiments/INFR-014/code/`; verdict math in shared `xen.xena`/`xen.evaluation`. |
| No Python-strategy backtest as evidence | **PASS** | S1 EMACross is the design-sanctioned §8 determinism smoke. |
| L-23 ledger | **PASS** | §20 A-1 TIGHTER, A-2/A-3/A-4 NEUTRAL; no ≥3 one-directional LOOSER streak. |
| Report ↔ artifact number consistency | **PASS** | Every §5/§6/§7 number re-derived from raw artifact rows matches (see fidelity trace). One unverifiable provenance claim → Issue 16. |

### Issues (numbering continues from 13)

14. **Minor — L-29 anchor check weaker than design §8 and excluded from the PASS conjunction; S1 `deviations: []` overstates.** `code/run_s1_smoke.py:157-177` checks one sample fill against the **nearest** open in the whole window with rel-err < 5% (design: `EntryFillPrice == next-bar RealOpen ± 1 tick`); `:483-485` uses `any()` across symbols; `:490-493` omits `pass_anchor` from `overall`. Materially satisfied this run (rel_err 0.0 exact on all three symbols), but this was run-3 Issue 10(e), was not covered by amendment A-2, and `s1_smoke.json` `"deviations": []` + report §3 "Deviations: none silent" do not declare it. **Required change:** one deviation-ledger line in report.md (or tighten the check to next-bar-open ±1 tick and include it in the conjunction) — does not affect the topology decision (informative per §11) or the pin.
15. **Minor — `_SELECTION_INFLATION_MAX = 0.02` is an undeclared informative threshold.** `calibration_bybit.py:49,:601-605`: the `coverage_limited` vs `selection_unsafe` `failure_label` boundary (0.02) appears nowhere in design.md; §14 declares "Frozen invented thresholds: 0". It is disclosure-only (set only on non-certified cells; never gates), and report §6/§8 quote its labels. **Required change:** declare the 0.02 label boundary in the report (or design §20 note) as informative; no re-run needed.
16. **Minor (provenance note) — report §8 before/after claim unverifiable.** "confirm cov for CLS-FILTER low from contaminated 0.060 → 0.035": the contaminated first-run confirm artifacts were discarded/overwritten, so 0.060 exists in no reviewable artifact. The current 0.035 is verified (7/200). Keep the claim but mark it as from the discarded run's console/log, or drop the number.

### Summary

Run 3's findings all **CONFIRMED** as legitimate; the fix cycle (design §20 A-1..A-4) genuinely resolved Issues 9, 11, 13, resolved Issue 12's binding half (dead code remains), and resolved Issue 10 except the L-29 anchor form (regraded Minor, Issue 14). Fresh trace found no seed leakage, no optional stopping, no UCB gating, no ch03 pin contact, no holdout/TEST contact, no family transitions; every reported number recomputes exactly from emitted rows; registry sha256 `ac8a1eb6…` independently recomputed and verify-green; 20/20 tests pass. **APPROVE** — the pin artifact and report are fit for the operator's sign-off decision (recommended reading unchanged: CLS-FILTER LOW_ONLY_CERTIFY with DEPLOY_WEAK disclosure, CLS-EPISODE TERMINAL). Issues 14–16 are ledger/disclosure items; none change any verdict-bearing quantity.
