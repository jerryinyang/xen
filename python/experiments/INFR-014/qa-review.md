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
