# INFR-009 — QA / Compliance Review

## QA run 1 — 2026-07-13T12:00:00Z — mode: subagent — HEAD `9d0aabe72c06c52ad3c4dc4451577e32f6fa18e9`

**Mode:** subagent (fresh context; no implementation work in this conversation)  
**HEAD:** `9d0aabe72c06c52ad3c4dc4451577e32f6fa18e9` (`refs/heads/main`)  
**Dirty files:** full `git status --short` unavailable in this QA environment (no shell). Reviewed live tree includes INFR-009 artifacts (`design.md`, `report.md`, `results/verification.json`, `analysis_code/verify_p0_p2.py`), `python/src/xen/xena/{score,economics,fill_basis,high_cadence_null,search,certify,final_gate,calibration}.py`, and `python/tests/test_xena_infr009.py` (+ related search/certify/final_gate tests). This write appends only `qa-review.md`.

**Scope under review:** INFR-009 P0–P2 XENA adjudication redesign (`python/src/xen/xena/*`), not a StrategyHost experiment.  
**Binding design:** `.ignore/temp/cons/consolidated-03.md` §0–10; experiment pin `python/experiments/INFR-009/design.md`.  
**Authorized scope:** P0, P0′, P1, P2 ONLY.

**Verdict: REVISE**

---

### Design-fidelity trace (consolidated-03 / design.md → code)

| Design clause (§ref) | Code (file) | Verdict | Notes |
|---|---|---|---|
| Intensive binding statistic \(g_\mathrm{gross}=1e4·Σ PnL_gross / Σ\|notional_entry\|\) (c03 §3; design §3) | `score.py` `g_gross_from_ledger` / `g_gross_point` | **MATCHES** | Entry-notional = Units·EntryPrice·mpu; empty notional → `-inf`; formula verbatim. |
| Bootstrap = common-block P25 of g_gross (c03 §4.2; design §3) | `score.py` `grid_gross_notional`, `bootstrap_g_gross`, `robust_g_hat` | **MATCHES** | Per-bar gross + \|notional\| on universe grid; circular block starts; default quantile 0.25. |
| Net companion (same denom, NetMoney num) — evidence until P3 (design §3) | `score.py` `net=` flag | **PARTIAL** | API exists; search/`EvalRecord`/evidence package do **not** surface `g_net` beside results. |
| Search objective = P25(g_gross); not log-wealth F (c03 §4.2; design §5) | `search.py` `run_restart` → `robust_g_hat`; `EvalRecord.score_kind="g_gross"` | **MATCHES** | LAHC accepts on `F_hat` names retained for API stability but hold g_gross. `bootstrap_F` retained as secondary only. |
| Costless selection policy kept (`charge_costs=False`) (c03 §4.2; design §9) | caller-supplied `OracleConfig`; tests use `False` | **PARTIAL** | Not enforced inside `run_restart`; default `OracleConfig.charge_costs=True` can still select under costs. Policy documented, not hard-coded. |
| Q1 `economics_disclosure` pre-search; never drops candidates (c03 §4.1; design §4 P0) | `economics.py` `economics_disclosure` | **MATCHES** | Gross quantiles + domain/hold/variant slices; `binding_note` states no candidate deletion. |
| Cost-map integrity hard; incomplete → `INTEGRITY_INCOMPLETE`; search/gate refused (c03 §4.1 E3; design §4) | `economics.py` `check_cost_map_integrity`, `assert_cost_map_allows_search`, `require_economics_before_search`; `cost_bps==0` placeholder | **PARTIAL** | Integrity logic correct and tested; **not wired into `run_restart` / live search entry**. Refusal is opt-in call-site only → E3/E4 still bypassable. |
| Q1 fixture medians ≈ −0.065 / +0.085 / +1.91 (design §4/§8) | `results/verification.json` + `economics_disclosure` on fixtures | **PARTIAL** | 003 = **1.910** MATCHES. 001 = **+0.043** vs −0.065 (near-zero intent OK; table number wrong/swapped). 002 = **−0.284** vs +0.085 **outside** 0.15 tol. Report/verification honestly document this; no fixture tuning observed. |
| Incomplete cost map blocks search on 001/002/003 without deleting candidates (design §4 P0) | verification + integrity code | **MATCHES** | All three `cost_map_complete=false`, `search_allowed=false`, `INTEGRITY_INCOMPLETE`. |
| High-cadence zero-edge null (c03 §5; design P0′) | `high_cadence_null.py` | **MATCHES** | Coin-flip directions on shared path; diagnostics: edge ≈0, high cadence legs band. verification: mean edge 0.007 bps, med legs 4000. No frozen scores. |
| Certification → evidence package, not cliff gate (c03 §4.3; design P1) | `certify.py` `certify_and_rank` | **MATCHES** | All distinct terminals shortlisted; `package_kind=evidence_package`; `binding=False` on S/Jaccard/resim/Hamming. |
| Retire F_floor / gate scalar / resim / min_drop_ratio / Hamming / S-as-threshold binders (c03 §8; design §4) | `certify.py` `retired_binders` + shortlist path; `calibration.py` shortlist vs cliff split | **MATCHES** | Package lists retired binders; shortlist ignores cliff. Legacy `passed`/`f_floor` kept for WS-6 continuity only. |
| Same-universe random-subset ref (+ S, percentile) evidence only (c03 §3/§4.3) | `certify.py` `random_subset_reference` | **MATCHES** | `binding=False`; note cites search bias. |
| Delete-one / keystone attribution, not flatness penalty (c03 §4.3) | `certify.py` `plateau_screen` | **PARTIAL** | `binding=False`; drop_scores always present. **Keystone field zeroed when `legacy_pass`** (`None if legacy_pass else keystone`) — under defaults (f_floor=-inf, threshold=0) profitable terminals often suppress named keystone. Attribution recoverable from `drop_scores` only. |
| HARD permutation battery retired; no new battery binder (c03 §4.4; design P2) | `certify.py` `hard_permutation_battery="RETIRED (INFR-009 P2)"`; no battery runner in xena | **MATCHES** | Field only; no new HARD path. |
| Mandatory print-vs-path fill-basis in evidence package (c03 §4.4; design §5 tree + P2) | `fill_basis.py` module; **not** called from `certify_and_rank` | **DEVIATES** | Decomposition correct (identity, grid_like, limit_print_dominance). Fixture samples OK (001 print≈0; 003 print dominance). **Package return dict has no `fill_basis` field** despite `fill_basis_package` docstring claiming package use and design architecture placing print/path inside the package. |
| Default route SUSPENDED until P4 (c03 §4.7 E2; design §1/§12) | `final_gate.py` module docstring; `__init__.py`; INDEX | **MATCHES** (code/docs notes) | `docs/references/xena-lane.md` still states XENA is **DEFAULT route** with v3 absolute-F pin — **spec lag**, not a P0–P2 code over-scope. |
| final_gate: suspend note only for P0–P2 (design §10 complexity) | `final_gate.py` header + still-runnable extensive-F gate | **MATCHES** authorized scope | Old extensive-F `pass_threshold` path retained for CAL replay; not redesigned to LCB (correctly deferred to P3). Soft risk: still callable on live without hard refuse. |
| No P3 CAL numbers / LCB binder / coverage freeze (design §4 stop) | score/certify/calibration | **MATCHES (absence)** | LCB mentioned only as future note; no calibrated floats invented. |
| No P4 registry v4 / default-route restore | no new freeze; SUSPENDED retained | **MATCHES (absence)** | INFR-006 registry retained; not deleted. |
| No P5 cost-aware search | search stays gross-intensive objective | **MATCHES (absence)** | No cost-in-objective search path added. |
| No invent/tune/freeze calibration floats (design §12) | economics draft floor optional; null `cost_bps=2.0` for integrity tests only | **MATCHES** | `cost_floor_status: DRAFT_UNFROZEN`; null docs `binding_scores_frozen: false`. |
| No `run_final_gate` on live; no TEST/holdout (design §12) | `verify_p0_p2.py` explicit; tests synthetic | **MATCHES** | Fixture Q1 uses SEARCH band only. |
| Emission / oracle / estimand / Rust untouched (design §2/§12) | no oracle/estimand/StrategyHost redesign in mandate | **MATCHES** | Adjudication-layer modules only. |
| Calibration shortlist vs cliff (design map: calibration) | `calibration.py` `n_legacy_cliff_pass`, `shortlist_rate` | **MATCHES** | FPR continuity preserved; evidence package shortlist separate. |
| Filter-helpful planted case not cadence-displaced (design §4 P1 stop) | `test_xena_search.test_search_recovers_planted_optimum` + intensive unit | **PARTIAL** | Intensive property + winner recovery tested; no explicit high-cadence-low-edge vs low-cadence-high-edge filter recovery fixture. |

---

### Governance checklist (adapted — INFR adjudication redesign)

| Check | Result | Evidence |
|---|---|---|
| Fresh-context independence | PASS | Subagent; no implementation co-authorship in this context |
| Authorized scope P0–P2 only | PASS | No LCB binder, no registry v4, no default-route restore, no cost-aware search |
| No absolute extensive-F re-pin as binder | PASS | Search/certify use `g_gross`; retired_binders list; package `binding_note` |
| L-12: avoid fixed-threshold conjunction stack as adjudicator | PASS (intent) | Evidence package replaces cliff conjunction; LCB deferred to P3 with stop-condition |
| L-22: cost/spread integrity for deployability claims | PASS (stage-appropriate) | Cost pins = hard integrity; deploy claims still require net (P3+); 0.0 cost = incomplete |
| L-23: no silent scalar freeze / amendment direction for A-1 | PASS | Design §9 flags LOOSER/TIGHTER at P4; no new frozen floats in code |
| No TEST/holdout contact | PASS | Verification + tests avoid gate band / holdout |
| No live `run_final_gate` in programme verification | PASS | `verify_p0_p2.py` forbids it |
| No fixture-tuned thresholds | PASS | Q1 numbers not re-fit to force within_tol; 002 failure reported honestly |
| Default route not silently restored | PASS | Indexes + module docs SUSPENDED; lane.md lag noted |
| INFR-006 artifacts retained | PASS | Index SUPERSEDED-BY; registry files remain |
| Complexity budget (new modules) | PASS | `score`, `economics`, `fill_basis`, `high_cadence_null` present; engine 0 |
| Unit / verification coverage | PASS (with gaps) | Report claims 55 passed on infr009+search+certify+final_gate; verification.json complete. Gaps: package fill_basis integration untested; economics not auto on search entry |
| Side-effect note | NOTE | `verify_p0_p2.economics_disclosure(..., write_artifact=True)` writes into live `data/strategy_runs/XENA-00x/` |

---

### Golden / fixture read-check (design acceptance intent, not VAL)

| Fixture / synthetic | Design expectation | Observed | Verdict |
|---|---|---|---|
| XENA-001 Q1 p50 | ≈ −0.065; no deploy credit | +0.043; integrity incomplete; search refused | Intent OK; table number DEVIATES |
| XENA-002 Q1 p50 | ≈ +0.085; sub-floor | −0.284; search refused | Intent OK (sub-zero); table number DEVIATES |
| XENA-003 Q1 p50 | ≈ +1.91; sub-cost archetype | +1.910; search refused | MATCHES |
| P0′ null | entry edge ≈ 0; 003 cadence | edge 0.007; legs med 4000 | MATCHES |
| g_gross intensive | doubling equal-edge trades ≉ 2× score | unit test | MATCHES |
| Evidence package | retire absolute binders; S not pass | synthetic package fields | MATCHES |
| Fill-basis 001 grid | print ≈ 0 | print_mean 0.0; grid_like | MATCHES |
| Fill-basis 003 limit | print dominance | print +21.6 / path −18.2 sample | MATCHES |
| HARD battery | retired | package field RETIRED | MATCHES |

---

### Issues

1. **[REVISE — experiment-developer] Print/path not attached to evidence package**  
   - **Design:** consolidated-03 §4.3/§4.4; design.md §5 architecture (print-vs-path under EVIDENCE PACKAGE); P2 “mandatory print/path”.  
   - **Code:** `fill_basis.py` complete; `certify.certify_and_rank` return (≈L456–487) has `hard_permutation_battery` only — **no** `fill_basis` / print-path summary. `fill_basis_package` docstring falsely claims package use.  
   - **Required:** Wire optional/mandatory fill-basis into the package (e.g. accept run_dir map or streams and call `fill_basis_package` / `decompose_stream` for shortlisted members), set `binding=False`, add test that package contains print/path fields.

2. **[REVISE — experiment-developer] Q1 integrity refuse not enforced at search entry**  
   - **Design:** c03 §4.1 / E3–E4 — incomplete cost map **refuses search**; Q1 is on the critical path before LAHC.  
   - **Code:** `require_economics_before_search` exists (`economics.py` ≈L363–383) and is unit-tested, but `search.run_restart` never calls it; live universe search can skip Q1.  
   - **Required:** Enforce at the live-universe entry (e.g. require `universe_root` / economics artifact check on production search drivers, or optional hard flag on `run_restart` for non-synthetic runs). Document that pure synthetic/CAL paths may bypass.

3. **[Note — experiment-developer] Keystone attribution suppressed on legacy_pass**  
   - **Design:** keystone is always attribution evidence.  
   - **Code:** `plateau_screen` L133 `None if legacy_pass else keystone`.  
   - **Suggested:** Always populate keystone (worst drop); keep `passed` as legacy-only flag. Non-blocking if drop_scores remain operator-visible.

4. **[Note — experiment-developer] Net companion not packaged**  
   - **Design:** net travels beside every result (evidence until P3).  
   - **Code:** `g_gross_point(..., net=True)` only.  
   - **Suggested:** Attach point `g_net` on EvalRecord / package ranked rows when costs pinned.

5. **[Note — quant-designer / operator] Q1 proposal-table numbers for 001/002**  
   - Honest recompute ≠ design table (−0.065/+0.085). 003 exact. Acceptance **intent** holds; do not retune code to the sketch numbers. Update design/report table or restate as “near-zero / sub-floor” only before P4 VAL.

6. **[Note — operator] Spec lag: `docs/references/xena-lane.md`**  
   - Still advertises XENA as default route + absolute F binders. Code/indexes say SUSPENDED. Align at P4 freeze, not by inventing P3 numbers now.

7. **[Note — residual, design-owned] final_gate still runs extensive-F binder if called**  
   - Authorized “suspend note only.” No hard refuse on live. Operator/process gate until P3/P4. Acceptable for P0–P2.

8. **[Note] No explicit filter-vs-cadence recovery fixture** for P1 stop wording; intensive + planted-winner tests partially cover.

---

### Scope overreach audit

| Forbidden | Present? |
|---|---|
| P3 LCB numbers / coverage freeze | **No** |
| P4 registry v4 / default-route restore | **No** |
| P5 cost-aware search | **No** |
| Invented frozen calibration floats | **No** |
| `run_final_gate` on live fixtures | **No** |
| TEST/holdout reads | **No** |
| StrategyHost / Rust / oracle redesign | **No** |

---

### Why REVISE (not APPROVE / REJECT)

**Core redesign is substantially correct:** intensive `g_gross` + common-block P25 search, Q1 disclosure + placeholder-cost integrity, evidence package retirement of absolute extensive-F binders, HARD battery retirement, high-cadence null, and suspend posture are implemented and verified without P3–P5 over-scope or fixture tuning.

**Not APPROVE:** two design-fidelity gaps remain on the P0/P2 critical path — (1) mandatory print/path is a standalone module, not package evidence; (2) E3/E4 search refusal is not on the search entry path. These are fixable without redesign.

**Not REJECT:** no holdout contact, no silent absolute-F re-pin, no unauthorized P3–P5, no causality/emission breach, no invented frozen scores.

---

*End QA run 1.*

---

## QA run 2 — 2026-07-13T18:00:00Z — mode: subagent — HEAD `9d0aabe72c06c52ad3c4dc4451577e32f6fa18e9`

**Mode:** subagent (fresh context; re-review after REVISE fixes only; no implementation work)  
**HEAD:** `9d0aabe72c06c52ad3c4dc4451577e32f6fa18e9` (`refs/heads/main`)  
**Dirty / tree note:** static review of live tree; this write appends only `qa-review.md`. Report claims 56 pytest passed post-fix (not re-executed in this QA environment).

**Scope under review:** INFR-009 P0–P2 only — verify REVISE items from run 1 closed; confirm no P3–P5 over-scope.

**Verdict: APPROVE**

---

### REVISE closure (run 1 → run 2)

| # | Run-1 issue | Required fix | Code evidence | Status |
|---|---|---|---|---|
| 1 | Print/path not on evidence package | Wire fill-basis into package; `binding=False`; test | `certify.certify_and_rank(..., include_fill_basis: bool = True)` → union shortlist members → `decompose_stream` + `summarize_decomposition`; package keys `"fill_basis"`, `binding=False`, `retired_replacement_for=HARD_permutation_battery`. Test `test_evidence_package_retires_binders`: `out["fill_basis"] is not None` and `binding is False`. verification.json `fill_basis_gridlike_or_ok` / print_mean present. | **CLOSED** |
| 2 | Q1 / cost integrity not on search entry | Enforce at `run_restart`; refuse placeholder `cost_bps=0` unless skip | `search.run_restart(..., universe_root=None, skip_economics_precondition=False)`: (a) `universe_root` set → `require_economics_before_search`; (b) else stream-level `check_cost_map_integrity` → `SearchRefusedIntegrity` if incomplete. Synthetic path: finite non-placeholder costs **or** `skip_economics_precondition=True`. Test `test_search_refuses_placeholder_costs` raises on `cost_bps=0`. Default synthetic helpers use `cost_bps=2.0` so CAL/unit search still runs. | **CLOSED** |
| 3 | Keystone suppressed when `legacy_pass` | Always surface worst-drop keystone | `plateau_screen` returns `keystone` whenever `drop_scores` exist; comment: “Always surface keystone… legacy_pass only affects the retired cliff flag”. Package exposes `"keystones"` map. Tests: `test_broad_plateau_passes` asserts `rep.keystone is not None` even when `passed`; `test_f_floor_legacy_flag_not_binding` keeps attribution under high f_floor. | **CLOSED** |
| 4 | Net companion not packaged | Attach g_net evidence on package | `certify_and_rank` builds `g_net_top` with `g_gross_point` / `g_net_point` (costed `replace(config, charge_costs=True)`), `binding=False`, P3 note. Package key `"net_companion"`. Test asserts non-None + `binding is False`. | **CLOSED** |

---

### Design-fidelity delta (only clauses that changed status)

| Design clause | Run 1 | Run 2 | Notes |
|---|---|---|---|
| Net companion on evidence | PARTIAL | **MATCHES** | Top shortlist gross/net pair; evidence until P3 |
| Cost-map integrity refuses search (E3) | PARTIAL | **MATCHES** | Hard on `run_restart` (stream pins and/or universe Q1); explicit synthetic skip |
| Delete-one / keystone always attribution | PARTIAL | **MATCHES** | No longer zeroed on legacy_pass |
| Mandatory print/path in package (P2) | DEVIATES | **MATCHES** | Default-on package field; opt-out `include_fill_basis=False` only |
| Q1 001/002 table numbers | PARTIAL | PARTIAL (unchanged) | Honest recompute; non-blocking; not retuned |
| Costless selection hard-enforced in search | PARTIAL | PARTIAL (unchanged) | Policy via callers/tests (`charge_costs=False`); not hard-coded inside `run_restart` — acceptable for P0–P2 with design §9 “KEPT” |

All other MATCHES from run 1 (intensive g_gross, bootstrap P25, Q1 disclosure never drops candidates, HARD retired, SUSPENDED route, no P3–P5) re-confirmed by static pass; no regression of retired binders or absolute-F re-pin observed.

---

### Governance checklist (run 2)

| Check | Result | Evidence |
|---|---|---|
| Fresh-context independence | PASS | Subagent re-review; no co-implementation |
| Authorized scope P0–P2 only | PASS | No LCB freeze, no registry v4, no default-route restore, no cost-aware search objective |
| Run-1 REVISE blockers closed | PASS | Table above |
| No absolute extensive-F re-pin | PASS | `score_kind=g_gross`; `retired_binders` list intact |
| No invented frozen CAL floats | PASS | Draft cost-floor remains unfrozen; null `binding_scores_frozen: false` |
| No TEST/holdout / live final_gate in programme verify | PASS | Unchanged posture |
| Complexity budget | PASS | Same four new modules; no engine/StrategyHost changes |

---

### Scope overreach audit (unchanged)

| Forbidden | Present? |
|---|---|
| P3 LCB numbers / coverage freeze | **No** |
| P4 registry v4 / default-route restore | **No** |
| P5 cost-aware search | **No** |
| Invented frozen calibration floats | **No** |
| `run_final_gate` on live fixtures in verify | **No** |
| TEST/holdout reads | **No** |
| StrategyHost / Rust / oracle redesign | **No** |

---

### Residual notes (non-blocking — do not reopen REVISE)

1. **[Note — quant-designer / operator] Q1 proposal-table 001/002** — recompute +0.043 / −0.284 vs table −0.065 / +0.085; 003 exact. Update design table before P4 VAL; do not retune code.  
2. **[Note — operator] Spec lag** — `docs/references/xena-lane.md` may still lag SUSPENDED / absolute-F language; align at P4.  
3. **[Note — residual] `final_gate` still callable with extensive-F binder** — authorized “suspend note only”; process gate until P3/P4.  
4. **[Note] No dedicated high-cadence-low-edge vs low-cadence-high-edge filter recovery fixture** — intensive property + planted recovery partially cover P1 stop wording.  
5. **[Note] Costless selection not hard-coded in `run_restart`** — callers must supply `OracleConfig(charge_costs=False)`; design keeps policy, not a new binder.  
6. **[Note] Live XENA-00x drivers** — existing stage2/search scripts call `run_restart` without `universe_root`; with fixture `cost_bps=0` they will now correctly hit `SearchRefusedIntegrity` (desired E3). Not an INFR-009 defect.

---

### Why APPROVE

All four run-1 REVISE items are fixed with design-aligned code paths and tests:

1. Evidence package carries mandatory print/path (`fill_basis`, default on).  
2. Search entry hard-refuses incomplete/placeholder cost maps unless an explicit synthetic skip.  
3. Keystone is always attribution evidence, independent of legacy cliff pass.  
4. Net companion rides on the package as non-binding evidence.

Scope remains **P0–P2 only**. Residual items are operator/docs/VAL notes, not design-fidelity blockers for this mandate. Programme may stop at P2 and hand off P3+ decisions per `design.md` / `report.md`.

---

*End QA run 2.*

---

## QA run 3 — 2026-07-13 — mode: subagent (qa-compliance) — P3 ONLY

**Mode:** subagent (fresh context; no implementation work)  
**Scope under review:** INFR-009 **P3 harness + stop discipline** only — *not* “pass CAL” (CAL already STOP’d).  
**Not in scope:** P0–P2 re-open, P4 freeze/VAL, P5 cost-aware search.  
**Sources:** `design.md` §P3; `report.md` §3; `results/p3_calibration.json`; `xen.xena.calibration_p3`; `xen.xena.score.lcb_g`; `analysis_code/run_p3_cal.py`; `tests/test_xena_p3.py`.

**Verdict: APPROVE**

---

### Checks (mandated)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Predeclaration committed before results (design §P3 rules) | **PASS** | `design.md` §P3.1–P3.6 freezes objective, LCB form, α=5%, block/k/K rules, bank mix, pipeline, HARD STOP *before* any bank outcome language. Harness constants match predeclaration (`ALPHA=0.05`, `LCB_CONFIDENCE=0.95`, `N_NULL_PER_CADENCE=40`, `N_RESTARTS=3`, `SEARCH_BUDGET=50`, `K_CANDIDATES`, block sweep set, seeds 1000+/2000+). Results JSON `predeclared` block echoes same; outcomes did **not** rewrite α/confidence/rules. Report §3.1 cites predeclaration → measured. |
| 2 | No XENA-001/002/003 TEST/holdout contact in harness | **PASS** | `calibration_p3.py` builds only synthetic `path_universe` / `build_high_cadence_null` streams; no `strategy_runs`, no fixture paths, no holdout segment. Gate band = synthetic `SegmentLayout.gate` only. `fixtures_forbidden` recorded in report JSON. Runner docstring forbids fixtures. `test_xena_p3.py` synthetic only (no XENA-00x / `run_final_gate` / holdout strings). P0–P2 `verify_p0_p2.py` fixture Q1 is out of P3 harness path. |
| 3 | Binder is LCB(g_gross), not extensive-F `run_final_gate` | **PASS** | Binding path: `evaluate_lcb` → `score.lcb_g` (`pass_positive` ⇔ one-sided 95% LCB>0 on intensive g_gross; `binder_form` / `score_kind=g_gross`). E2e rows: `gate_kind=LCB_G_GROSS_95`, `redesign_binder=true`. `predeclared.legacy_extensive_F_gate=false`. **No** import/call of `run_final_gate`, `gate_pass_threshold`, or extensive-F cliff in P3 module. Search/rank still use P25(g_gross) via `run_restart` / `certify_and_rank` with `skip_economics_precondition=True` (synthetic). |
| 4 | Hard stop honored (no freeze, no target softening) | **PASS** | Measured: coverage fail (low 10–20% all L; high OK); e2e α̂ low **0.075**, high **0.15** (both >0.05); `selected_block=null`, `selected_k=null`; `stop_condition.STOP=true`, `verdict=STOP`. α target remains **0.05**; confidence remains **0.95** — not widened. Fallback `block_lcb=64` used only for diagnostic e2e after coverage rule failed; does **not** clear STOP. Report §3.4: no P4, no freeze, no blind VAL, no default-route restore, no extensive-F re-pin. No registry v4 / frozen procedure artifacts in results. |
| 5 | Scope P3 only (no P4/P5) | **PASS** | Deliverables = harness + JSON + STOP report. Explicit non-claims: no accepted freeze, no route restore, no P5 cost-aware search. Status: P4 blocked. |

---

### Design-fidelity (P3 pipeline)

| Clause | Code / artifact | Verdict |
|---|---|---|
| Binding search = P25(g_gross), costless | `run_e2e_one` → `OracleConfig(charge_costs=False)` + `run_restart` | **MATCHES** |
| Denominator entry-notional via `g_gross` / `lcb_g` | `score.lcb_g` → `robust_g_hat` / `g_gross_point` | **MATCHES** |
| Fixed-TEST = synthetic gate only | `layout.gate` in `evaluate_lcb` | **MATCHES** |
| Block rule P3.2 (smallest L, both cadences) | `select_block_length` → `coverage_stop_fail` when none | **MATCHES** |
| Bank 28+6 EURUSD+6 XAUUSD per cadence | `bank_seeds` assert len==40 | **MATCHES** |
| Power / k / K / (R_max,DD) disclose-only | `binding: false` / `k_rule_fail` / DD non-binding | **MATCHES** |
| HARD STOP if coverage or either e2e α fails | `stop = cov_fail or alpha_fail` | **MATCHES** |

---

### Numbers cross-check (`p3_calibration.json` ↔ `report.md` §3)

| Metric | JSON | Report | Match |
|---|---|---|---|
| coverage_fail / selected_block | true / null | FAIL all low; null L | yes |
| alpha_low α̂ | 0.075 (3/40) | 7.5% | yes |
| alpha_high α̂ | 0.15 (6/40) | 15% | yes |
| selected_k / k_rule_fail | null / true | null | yes |
| selected_K | 256 | cap 256 | yes |
| R_max/DD breach_rate | 1.0 | 1.0 | yes |
| verdict | STOP | STOP | yes |
| generated_utc | 2026-07-13T14:53:20Z | cited | yes |

---

### Governance checklist (P3)

| Check | Result |
|---|---|
| Fresh-context independence | PASS |
| L-12 predeclaration discipline | PASS (rules fixed; numbers fall out; no post-hoc rule edit) |
| No fixture-tuned rescue after fail | PASS |
| No α/confidence softening | PASS |
| No extensive-F re-pin | PASS |
| No freeze / default-route restore | PASS |
| No TEST/holdout / live fixture bank | PASS |
| STOP ≠ “fail QA” | PASS — CAL stop is the *authorized* outcome; harness discipline is the review object |

---

### Issues

1. **[Note — non-blocking] Diagnostic block fallback after coverage FAIL**  
   When `selected_block is None`, harness continues e2e at `block_lcb = max(H_low, H_high, 64)` (`block_fallback_used`). Allowed for measurement honesty; STOP still forced by `coverage_stop_fail`. Do not treat fallback L as a selected/frozen block.

2. **[Note — non-blocking] Weak unit assertion in `test_xena_p3.test_lcb_zero_edge_often_not_positive`**  
   Final assert ends with `or True` (always passes). Shape/coverage tests and full bank results still discipline the binder. Optional tighten later; not a stop-discipline defect.

3. **[Note — non-blocking] E2e package opts out of random-ref / fill_basis**  
   `include_random_ref=False`, `include_fill_basis=False` for CAL compute. Design binding pass is LCB after search→rank→TEST; evidence fields are non-binding. Acceptable for α harness.

4. **[Note — operator] Next step is procedure change + disjoint bank**  
   Per design P3.6 / report §3.4 — not target softening, not fixture-fit, not P4. Outside this QA mandate.

---

### Scope overreach audit (P3 review)

| Forbidden | Present? |
|---|---|
| P4 registry freeze / blind VAL / default-route restore | **No** |
| P5 cost-aware search | **No** |
| Softened α or LCB confidence after fail | **No** |
| Extensive-F `run_final_gate` as P3 binder | **No** |
| XENA-001/002/003 or holdout in P3 harness | **No** |
| Frozen “accepted” LCB procedure despite STOP | **No** |

---

### Why APPROVE (not REVISE / REJECT)

**APPROVE:** P3 predeclaration, synthetic-only bank, LCB(g_gross) binder (not extensive-F gate), honest STOP with α/coverage failures left intact, and no P4/P5 over-scope or target softening. Report §3 matches JSON stop_condition.

**Not REVISE:** No design-fidelity gap that would change STOP/PROCEED handling or binder identity. Notes above are optional polish / operator next-step, not harness defects.

**Not REJECT:** No holdout/fixture contact, no silent freeze, no unauthorized binder re-pin, no softened stop-condition.

**Reminder:** APPROVE means the **P3 harness + stop discipline** are compliant. It does **not** mean CAL passed or P4 is authorized. P4 remains **blocked**.

---

*End QA run 3 (P3).*

---

## QA run 4 — 2026-07-13 — mode: subagent (qa-compliance) — P3b ONLY

**Mode:** subagent (fresh context; no implementation work)  
**Scope under review:** INFR-009 **P3b harness + stop discipline** only — *not* “CAL passed” (production CAL STOP’d on low e2e).  
**Not in scope:** P0–P2 re-open, P3 re-litigation, P4 freeze/VAL, P5 cost-aware search.  
**Sources:** `design.md` §P3b; `report.md` §3–4; `results/p3b_calibration.json` (`stop_condition` + production α/coverage); `xen.xena.score.lcb_g_studentized`; `xen.xena.calibration_p3b`; `SegmentLayout.purge_ns` (`calibration.py`); `analysis_code/run_p3b_cal.py`; `tests/test_xena_p3b.py`.

**Verdict: APPROVE**

---

### Checks (mandated)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Predeclaration before results | **PASS** | `design.md` §P3b header: “Committed before any P3b result.” Freezes A1 studentized LCB, A3 floor rule, B1 purge ≥H, bank seeds 11000/12000, scale plan, HARD stop (α=5%, 95% LCB unchanged). Harness constants match (`ALPHA=0.05`, `LCB_CONFIDENCE=0.95`, `SEED_BASE_LOW/HIGH=11000/12000`, TOY/PRODUCTION scale params). JSON `predeclared` block echoes method/seeds/purge; outcomes did **not** rewrite α/confidence. Report §3 cites predeclaration → measured §4. |
| 2 | Studentized LCB used for e2e (not percentile) | **PASS** | Binding path: `evaluate_lcb_st` → `score.lcb_g_studentized` only. **No** call to `lcb_g` (percentile) in `calibration_p3b.py`. E2e rows: `method=studentized_bootstrap_t`, `gate_kind=LCB_G_GROSS_95_STUDENTIZED`. Coverage sweeps same method. `lcb_g` retained as P3 baseline with “prefer studentized for P3b” note — unused by P3b harness. |
| 3 | Purge between rank and gate | **PASS** | `SegmentLayout.from_span(..., purge_ns=)` allocates search/rank/gate over span minus purge; `gate_start = ranking_end + purge_ns`. P3b `_layout`: `purge_ns = H · purge_mult · bar_seconds · NS` (default purge_mult=1 → ≥H bars). E2e uses purged layout for search→gate; production rows record `purge_ns=1.2e12` (low, H=20) / consistent with H·60s. Unit: `test_purge_separates_ranking_and_gate`. |
| 4 | Disjoint seeds from P3 | **PASS** | P3 `calibration_p3.bank_seeds`: bases **1000/2000**. P3b: `SEED_BASE_LOW=11000`, `SEED_BASE_HIGH=12000` + EUR/XAU offsets (+500/+600). JSON `predeclared.seed_bases` + `disjoint_from_p3=true`. Production e2e rows start at seed 11000 (low) / 12000 (high). Unit: `test_seeds_disjoint_from_p3` (LOW base ≥11000). |
| 5 | No fixtures / TEST holdout / `run_final_gate` | **PASS** | Harness builds only synthetic `path_universe` / `build_high_cadence_null`; gate = synthetic `layout.gate`. No `strategy_runs`, no XENA-001/002/003 load, no holdout fence reads. **No** import/call of `run_final_gate` / extensive-F cliff. Module + runner docs forbid fixtures. `fixtures_forbidden` in predeclared. Tests synthetic only. |
| 6 | Hard stop honored (α=5% not softened; low e2e 7.5% → STOP) | **PASS** | Production binding: coverage joint **PASS** at `selected_block=40` (low rate 5.0%, high 0.0%); e2e α̂ low **0.075** (3/40) `pass_stop=false`; high **0.025** (1/40) `pass_stop=true`. Top-level `stop_condition`: `coverage_fail=false`, `alpha_low_fail=true`, `alpha_high_fail=false`, `STOP=true`, `verdict=STOP`, `alpha_target=0.05` unchanged. Report §4.4: explicitly refuses “close enough” / noise argument; no freeze, no α soften, no extensive-F, no P4. Escalation listed not executed. |
| 7 | Scope P3b only | **PASS** | Deliverables = procedure change harness + studentized binder + purged layout + toy→production CAL JSON + STOP report. No registry v4, no default-route restore, no P5 cost-aware search, no fixture-tuned rescue. Status: **P4 blocked**. |

---

### Design-fidelity (P3b procedure)

| Clause (design §P3b) | Code / artifact | Verdict |
|---|---|---|
| A1 bootstrap-t LCB = ĝ − t\*·sê | `lcb_g_studentized` (t\* = quantile of (g\*−ĝ)/sê) | **MATCHES** |
| A1 diagnostics n_legs / nonempty blocks / empty_bar_frac | emitted on every studentized call; e2e rows carry them | **MATCHES** |
| A3 n_legs_floor from bank coverage (not fixtures) | `select_block_and_floors` A3 curve; prod `selected_n_legs_floor=null` (coverage already OK without floor) | **MATCHES** |
| B1 purge ≥ H rank→gate | `_layout(..., purge_mult=1)` + `SegmentLayout.purge_ns` | **MATCHES** |
| Targets unchanged (α=5%, 95% LCB, costless g_gross, no extensive-F) | `ALPHA`, `LCB_CONFIDENCE`, `OracleConfig(charge_costs=False)`, no `run_final_gate` | **MATCHES** |
| Bank mix 28+6+6 shape, disjoint seeds | `bank_seeds` n_main + EUR + XAU; bases 11k/12k | **MATCHES** |
| C2 toy then production; production binds proceed | `run_p3b_calibration` → toy then prod; final STOP from production | **MATCHES** |
| HARD STOP if coverage or either e2e α fails at production | `stop = cov_fail or alpha_fail`; prod low α fails → STOP | **MATCHES** |

---

### Numbers cross-check (`p3b_calibration.json` ↔ `report.md` §4)

| Metric | JSON (production / top stop) | Report §4 | Match |
|---|---|---|---|
| selected_block | 40 | 40 | yes |
| low cov @L=40 rate | 0.05 OK | 5.0% OK | yes |
| high cov @L=40 rate | 0.0 OK | 0.0% OK | yes |
| coverage_fail | false | PASS | yes |
| alpha_low α̂ | 0.075 (3/40) | 7.5% FAIL | yes |
| alpha_high α̂ | 0.025 (1/40) | 2.5% PASS | yes |
| alpha_target | 0.05 | ≤5% | yes |
| selected_n_legs_floor | null | null | yes |
| selected_k / k_rule_fail | null / true (disclose) | disclosed, not stop-gate | yes |
| method | studentized_bootstrap_t | studentized | yes |
| purge_mult | 1 | B1 purge ≥H | yes |
| verdict / STOP | STOP / true | STOP; P4 blocked | yes |
| generated_utc | 2026-07-13T18:15:55Z | 2026-07-13 scope | yes |

Toy loop STOP (coverage joint fail; high e2e 7.5%) is consistent with scale plan; production is the binding layer.

---

### Governance checklist (P3b)

| Check | Result |
|---|---|
| Fresh-context independence | PASS |
| L-12 predeclaration discipline | PASS (A1/B1/bank/scale fixed; numbers fall out) |
| Studentized binder for counted e2e | PASS (not percentile residual) |
| Purge on rank→TEST seam | PASS |
| Disjoint null bank vs P3 | PASS |
| No fixture-tuned rescue after fail | PASS |
| No α/confidence softening (“close enough” refused) | PASS |
| No extensive-F re-pin / `run_final_gate` | PASS |
| No freeze / default-route restore | PASS |
| No TEST/holdout / live fixture bank | PASS |
| STOP ≠ “fail QA” | PASS — CAL stop is authorized; review object is harness discipline |

---

### Issues

1. **[Note — non-blocking] Weak unit assertion on seed disjointness**  
   `test_seeds_disjoint_from_p3` only asserts `SEED_BASE_LOW >= 11_000` (does not assert HIGH=12000 or non-overlap with P3 1000/2000 ranges). Constants + JSON bank are correct; optional tighten later.

2. **[Note — non-blocking] E2e package opts out of random-ref / fill_basis**  
   Same as P3: `include_random_ref=False`, `include_fill_basis=False` for CAL compute. Binding pass is studentized LCB after search→rank→purged gate; evidence fields non-binding. Acceptable.

3. **[Note — non-blocking] A3 floor null when coverage already holds**  
   Design allows floors only when needed for domain; production correctly leaves `selected_n_legs_floor=null` after joint coverage at L=40 without floor. Not a paper-over (low e2e still fails honestly).

4. **[Note — operator] Escalation outside this mandate**  
   Report lists B2 distant TEST → stronger low-n interval → B3 selection correction → larger n_null. Not executed; correct under P3b.5. Next mandate only — not a harness defect.

5. **[Note] Unused import hygiene in harness/tests**  
   `g_gross_point` imported in `calibration_p3b`; `lcb_g` imported in `test_xena_p3b` without use. Non-blocking polish.

---

### Scope overreach audit (P3b review)

| Forbidden | Present? |
|---|---|
| P4 registry freeze / blind VAL / default-route restore | **No** |
| P5 cost-aware search | **No** |
| Softened α or LCB confidence after low e2e 7.5% | **No** |
| Percentile LCB as counted P3b e2e binder | **No** |
| Extensive-F `run_final_gate` as P3b binder | **No** |
| XENA-001/002/003 or holdout in P3b harness | **No** |
| Reused P3 seed bank (1000/2000) | **No** (11k/12k) |
| Frozen “accepted” procedure despite STOP | **No** |

---

### Why APPROVE (not REVISE / REJECT)

**APPROVE:** P3b predeclaration, studentized (not percentile) LCB binder, rank→gate purge, disjoint bank, synthetic-only nulls, honest production STOP on low e2e α=7.5%>5% with α target left at 5%, and no P4/P5 over-scope or target softening. Report §3–4 matches JSON production `stop_condition`.

**Not REVISE:** No design-fidelity gap that would change STOP/PROCEED handling, binder identity, purge placement, or bank isolation. Notes above are optional polish / operator next-step.

**Not REJECT:** No holdout/fixture contact, no silent freeze, no unauthorized binder re-pin, no softened stop-condition, no P3 seed reuse.

**Reminder:** APPROVE means the **P3b harness + stop discipline** are compliant. It does **not** mean CAL passed or P4 is authorized. Production verdict is **STOP**; **P4 remains blocked**.

---

*End QA run 4 (P3b).*

---

## QA run 5 — 2026-07-13 — mode: subagent (qa-compliance) — P3c ONLY

**Mode:** subagent (fresh context; no implementation work)  
**Scope under review:** INFR-009 **P3c harness + stop discipline** only — *not* “CAL passed” (freeze-grade run STOP’d).  
**Not in scope:** P0–P2 re-open, P3/P3b re-litigation, P4 freeze/VAL, P5 cost-aware search.  
**Sources:** `design.md` §P3c; `report.md` P3c; `results/p3c_calibration.json`; `xen.xena.calibration_p3c`; `xen.xena.calibration_p3b.run_scale` (held procedure); `analysis_code/run_p3c_cal.py`; `tests/test_xena_p3c.py`.

**Verdict: APPROVE**

---

### Checks (mandated)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | n=200 predeclared; single run; no optional stopping | **PASS** | `design.md` §P3c.3 freezes n_null=200 before results. Harness `FREEZE_GRADE.n_null=200`, `n_coverage=200`. JSON `predeclared.n_null_per_cadence=200` + design-power rule; e2e/coverage blocks all `n=200`. `run_p3c_calibration` calls `p3b.run_scale` **once** (no draw-until-pass / optional stopping loop). Runner writes one artifact. |
| 2 | Procedure held (studentized LCB, purge) — no A1/B1 change | **PASS** | P3c is thin wrapper: swaps seeds + n only; procedure via `p3b.run_scale(..., purge_mult=1)`. Binder path remains `evaluate_lcb_st` → `lcb_g_studentized` (`method=studentized_bootstrap_t`, `gate_kind=LCB_G_GROSS_95_STUDENTIZED`). Rank→gate purge ≥ H via `_layout(purge_mult=1)`; e2e rows `purge_ns=1.2e12` (low, H=20). `predeclared.procedure_change=false`. No new LCB form, no UCB gate, no percentile reversion. |
| 3 | Disjoint seeds 21000/22000 | **PASS** | `SEED_BASE_LOW=21000`, `SEED_BASE_HIGH=22000`; process mutates `p3b.SEED_BASE_*` then runs. Explicit `disjoint_from` P3 [1000,2000] / P3b [11000,12000]. Rows: low bank starts seed **21000**; high **22000**. Unit `test_seeds_disjoint`. |
| 4 | Gate = point α̂≤5% + coverage (Wilson disclosure only) | **PASS** | `pass_stop = rate <= ALPHA` on point α̂ (`end_to_end_alpha`). Hard stop: `cov_fail or alpha_low_fail or alpha_high_fail`. Wilson/SE only via `enrich_alpha_disclosure` with `alpha_disclosure_only=true` and `gate_rule: point alpha_hat <= 0.05 (Wilson/SE not binding)`. Top-level `gate_rule` restates PASS iff point ≤5% both + coverage ≤5% both at selected L. Wilson intervals present on α blocks but **not** used as pass bar (high α̂=5.5% FAILs despite Wilson lower bound <5%). |
| 5 | No fixtures; no `run_final_gate`; no P4/P5 | **PASS** | Nulls only via P3b synthetic `path_universe` / `build_high_cadence_null`. No XENA-00x / `strategy_runs` / holdout in P3c harness, runner, or tests. No import/call of `run_final_gate` / extensive-F cliff. Report: default route SUSPENDED, P4 blocked; non-claims no registry v4, no escalation implemented. Scope = freeze-grade-n re-CAL only. |
| 6 | STOP honored given coverage_fail + high 5.5% | **PASS** | JSON `stop_condition`: `coverage_fail=true`, `alpha_low_fail=false`, `alpha_high_fail=true`, `STOP=true`, `verdict=STOP`, `selected_block=null`, `alpha_target=0.05` unchanged. Coverage: `ok_blocks=[]`, all joint L fail (e.g. L=40 low 6.0% / high 6.5%). High e2e 11/200 = **5.5%** > 5%. Report HARD STOP; refuses freeze / α soften / extensive-F / optional stopping / P4. Escalation listed as recommend-only, not executed. |
| 7 | Low e2e 5% correctly reported as resolving n=40 residual | **PASS** | Low e2e: 10/200, `alpha_hat=0.05`, `pass_stop=true`. Report interpretation #1: 7.5% @ n=40 → **5.0% @ n=200** = underpowered-noise resolution; primary P3c residual question answered without blaming low-cadence purge leak. Matches design purpose (resolution fix only). |

---

### Design-fidelity (P3c freeze-grade-n)

| Clause (design §P3c) | Code / artifact | Verdict |
|---|---|---|
| IS: one re-CAL at n=200, same studentized LCB + purge ≥ H | `FREEZE_GRADE` + single `run_scale` | **MATCHES** |
| IS NOT: procedure change, α soften, UCB, optional stop, fixtures | `procedure_change=false`; point gate; synthetic bank | **MATCHES** |
| Gate: point α̂≤5% both + coverage ≤5% both at selected L | stop rebuild + `pass_stop` + `coverage_stop_fail` | **MATCHES** |
| Wilson/SE disclosure only | `enrich_alpha_disclosure` | **MATCHES** |
| Seeds 21000/22000 disjoint | constants + bank rows | **MATCHES** |
| L: re-apply joint L-selection; do not blind-pin 40 | `select_block_and_floors`; selected_block null; sweeps reported | **MATCHES** |
| Within-universe scale n_cand=64, budget=200, restarts=5 | `FREEZE_GRADE` + JSON scale_params | **MATCHES** |
| Escalation not executed in P3c; recommend rung 1 on STOP | `escalation_if_stop` text only; no purge-scale change | **MATCHES** |
| STOP → no freeze / no P4 | report + verdict STOP | **MATCHES** |

---

### Numbers cross-check (`p3c_calibration.json` ↔ `report.md` P3c)

| Metric | JSON | Report | Match |
|---|---|---|---|
| n_null / cadence | 200 | 200 | yes |
| seeds | 21000 / 22000 | 21000/22000 | yes |
| selected_block / ok_blocks | null / [] | null; coverage_fail | yes |
| L=40 low/high cov rate | 0.06 / 0.065 | 6.0% / 6.5% | yes |
| L=20 low/high | 0.045 / 0.065 | 4.5% / 6.5% | yes |
| alpha_low α̂ | 0.05 (10/200) | 5.0% PASS | yes |
| alpha_high α̂ | 0.055 (11/200) | 5.5% FAIL | yes |
| Wilson low (disclosure) | ~[2.7%, 9.0%] / [3.1%, 9.6%] | same bands | yes |
| method / purge_mult | studentized / 1 | held | yes |
| block_lcb e2e (fallback) | 64 | fallback L=64 when no joint L | yes |
| STOP / verdict | true / STOP | STOP; P4 blocked | yes |
| alpha_target | 0.05 | ≤5% point gate | yes |

---

### Governance checklist (P3c)

| Check | Result |
|---|---|
| Fresh-context independence | PASS |
| L-12 predeclaration (n, seeds, gate, held procedure) | PASS |
| No procedure reopen (A1/B1 frozen) | PASS |
| No optional stopping / multi-look bank | PASS |
| Point α gate; Wilson not binding | PASS |
| No fixture / holdout / `run_final_gate` | PASS |
| No α/confidence softening after fail | PASS |
| No freeze / default-route restore / P4–P5 | PASS |
| STOP ≠ “fail QA” | PASS — CAL stop authorized; review object is harness discipline |
| Residual-resolution claim honest | PASS — low 5.0% at n=200 closes n=40 7.5% noise question |

---

### Issues

1. **[Note — non-blocking] Dead double-assign of `alpha_*_fail` in `calibration_p3c`**  
   Lines first compute `alpha_hat > ALPHA or not pass_stop`, then overwrite with `not pass_stop` only. `pass_stop` already encodes point ≤ α, so final logic is correct. Optional cleanup.

2. **[Note — non-blocking] `L_drift_from_p3b_40` only when a *different* L is selected**  
   Code: `L_drift = selected_L is not None and selected_L != 40`. On full coverage fail (`selected_block=null`), flag is **false** even though L=40 is no longer joint-OK at n=200 (rates 6%/6.5%). Report narrates that drift correctly via sweeps; machine flag is narrower. Optional: also flag “P3b L no longer joint-OK.” Not a stop-discipline defect.

3. **[Note — non-blocking] Weak unit seed assertion**  
   `test_seeds_disjoint` uses `>= 21000/22000` rather than exact equality / full non-overlap ranges. Constants + JSON bank are correct.

4. **[Note — non-blocking] Module-global seed mutation on `calibration_p3b`**  
   Process-local swap of `SEED_BASE_*` for one `run_scale` call. Fine for single runner; not concurrent-safe. Acceptable for this harness.

5. **[Note — operator] Escalation re-aim after residual resolution**  
   Report correctly notes rung 1 (calendar-scaled purge for low-cadence seam) is **misaligned** now that low e2e resolved; remaining issues are joint coverage / high 5.5%. Outside harness QA — next mandate must re-predeclare if changing procedure.

6. **[Note] Design SE target ≤1.5% vs realized SE@p=0.05 ≈1.54% at n=200**  
   Predeclared explicitly (`design` + harness); not post-hoc n-tinkering.

---

### Scope overreach audit (P3c review)

| Forbidden | Present? |
|---|---|
| Procedure change (new LCB / purge rule / α soften) | **No** |
| Optional stopping / multi-look until pass | **No** |
| Wilson/UCB as pass bar | **No** |
| P4 registry freeze / blind VAL / default-route restore | **No** |
| P5 cost-aware search | **No** |
| Extensive-F `run_final_gate` as binder | **No** |
| XENA-001/002/003 or holdout in P3c harness | **No** |
| Reused P3 (1k/2k) or P3b (11k/12k) seed bases | **No** (21k/22k) |
| Escalation rung implemented inside P3c | **No** |
| Frozen “accepted” procedure despite STOP | **No** |

---

### Why APPROVE (not REVISE / REJECT)

**APPROVE:** P3c predeclared n=200 single-shot re-CAL under **held** P3b studentized+purge procedure, disjoint 21000/22000 bank, point-α + coverage gate with Wilson disclosure-only, synthetic-only nulls, no `run_final_gate`/P4/P5, and honest STOP on `coverage_fail` + high e2e 5.5% while correctly reporting low e2e **5.0%** as resolution of the n=40 residual. Report P3c matches JSON `stop_condition`.

**Not REVISE:** No design-fidelity gap that would change STOP/PROCEED, binder identity, n/seed predeclaration, or gate composition. Notes are polish / operator next-step only.

**Not REJECT:** No holdout/fixture contact, no silent freeze, no procedure reopen, no optional stopping, no Wilson-as-gate, no softened stop.

**Reminder:** APPROVE means the **P3c harness + stop discipline** are compliant. It does **not** mean CAL passed or P4 is authorized. Verdict is **STOP**; **P4 remains blocked**. Low e2e residual is resolved; joint coverage + high 5.5% remain open for a *future* predeclared procedure mandate.

---

*End QA run 5 (P3c).*

---

## QA run 6 — 2026-07-13 — mode: subagent (qa-compliance) — P3d ONLY

**Mode:** subagent (fresh context; no implementation work)  
**Scope under review:** INFR-009 **P3d harness + stop discipline** only — *not* “CAL passed” (confirm STOP’d).  
**Not in scope:** P0–P2 re-open, P3/P3b/P3c re-litigation, P4 freeze/VAL, P5 cost-aware search, binder-form implementation.  
**Sources:** `design.md` §P3d (incl. §P3d.8 freeze); `report.md` P3d; `results/p3d_design.json`; `results/p3d_confirm.json`; `xen.xena.score.lcb_g_leg_studentized`; `xen.xena.calibration_p3d`; `analysis_code/run_p3d_cal.py`; `tests/test_xena_p3d.py`.

**Verdict: APPROVE**

---

### Checks (mandated)

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Design/confirm split + disjoint seeds | **PASS** | Predeclared: DESIGN 31000/32000 n=80; CONFIRM 41000/42000 n=200 (`design.md` §P3d.2; `DESIGN_SEEDS`/`CONFIRM_SEEDS`/`DESIGN_SCALE`/`CONFIRM_SCALE`). Fit only in `design_fit_l_rule_and_interval` (`_set_seeds(*DESIGN_SEEDS)`); gate only in `confirm_gate` (`_set_seeds(*CONFIRM_SEEDS)`). Artifacts: `p3d_design.json` seeds 31000/32000; `p3d_confirm.json` 41000/42000; e2e rows low start 41000, high through 42605. Disjoint from P3 (1k/2k), P3b (11k/12k), P3c (21k/22k), and each other. Within-universe scale n_cand=64, budget=200, restarts=5 held. |
| 2 | Ladder order (leg bootstrap selected) | **PASS** | Ladder executed (1) calendar studentized B=200/400 then (2) leg_studentized. First both-ok at step 2 freezes: `interval=leg_studentized`, B=200, `block_legs=1` (trace first both-ok row: low 5.0% / high 2.5%). Steps (3) BCa / (4) confidence map **not** entered. `ladder_stop="(2) leg_studentized both cadences"`; report + §P3d.8 match. Binder path: `eval_lcb_legs` → `lcb_g_leg_studentized` (`method=leg_studentized_bootstrap_t`, `resample_unit=legs`). |
| 3 | Confirm used frozen procedure only | **PASS** | `run_p3d`: design → `proc = design["frozen_procedure"]` → `confirm_gate(proc)`. Confirm coverage/e2e read `procedure[cadence]` only — no B/bl/L refit, no ladder re-run. Confirm JSON `procedure` identical to design `frozen_procedure` and `design.md` §P3d.8. Wilson/SE on α̂ disclosure only; `pass_stop = alpha_hat <= ALPHA` (point). Single n=200; no optional stopping. |
| 4 | STOP on confirm fail; no α soften; binder-form recommended not implemented | **PASS** | Confirm: low cov **5.5%** FAIL; high cov **3.5%** OK; e2e low **8.5%** FAIL; high **6.5%** FAIL. `stop_condition`: `coverage_fail=true`, `alpha_low_fail=true`, `alpha_high_fail=true`, `STOP=true`, `verdict=STOP`, `alpha_target=0.05` unchanged; confidence remains 0.95. Fork listed as text only: (a)/(b)/(c). No mean-per-leg LCB, permutation binder, or two-stage TEST in code. Report: no P3e, no α soften, no P4; favor (a)→(b)→(c) as next *phase*, not implemented. |
| 5 | No fixtures; no `run_final_gate`; no P4/P5/P3e | **PASS** | Nulls via P3b synthetic `make_null_universe` / `path_universe` / `build_high_cadence_null` only. No `strategy_runs`, XENA-00x, holdout, or `run_final_gate` in harness, runner, or `test_xena_p3d.py`. Report: default route SUSPENDED, P4 blocked; non-actions include no P3e / seam revival / freeze. Scope = design fit + confirm gate only. |
| 6 | Seam ladder not reopened | **PASS** | `purge_mult=1` fixed (held ≥H rank→gate purge from P3b). No purge-scale sweep, no distant-TEST / B2–B3, no seam-ladder rung implementation. Residual framed as F1 interval unit (leg bootstrap), not F2 seam. Report explicit non-action: “No seam-ladder revival.” |

---

### Design-fidelity (P3d last estimator round)

| Clause (design §P3d) | Code / artifact | Verdict |
|---|---|---|
| Design/confirm split; design fit, confirm gate-only | two banks, two seed bases, two JSON artifacts | **MATCHES** |
| Seeds DESIGN 31k/32k n=80; CONFIRM 41k/42k n=200 | constants + JSON | **MATCHES** |
| Ladder (1) more B calendar → (2) leg bootstrap → stop at clear | step1 then step2; freeze at first step2 both-ok | **MATCHES** (see Note 1 on step1 early-exit) |
| Forbidden: one global L to pass both | frozen procedure is leg unit, not a joint calendar L | **MATCHES** |
| Confirm PASS iff point α̂≤5% both + cov≤5% both | `cov_fail or alpha_fail` → STOP | **MATCHES** |
| Wilson/SE disclosure only | e2e carries Wilson/SE; gate is point | **MATCHES** |
| HARD STOP → binder-form recommend only; no P3e / α soften | `binder_form_fork_if_stop` text; no impl | **MATCHES** |
| Seam retired; purge ≥ H retained | `purge_mult=1`; no seam reopen | **MATCHES** |
| Artifacts: calibration_p3d, leg LCB, p3d_design/confirm | present | **MATCHES** |
| §P3d.8 freeze after design procedure | STATUS FROZEN_AFTER_DESIGN; confirm does not mutate | **MATCHES** |

---

### Numbers cross-check (`p3d_*` ↔ `report.md` P3d)

| Metric | JSON | Report | Match |
|---|---|---|---|
| Design seeds / n | 31000/32000; n=80 | 31000/32000; n=80 | yes |
| Design freeze interval | leg_studentized B=200 bl=1 | same | yes |
| Design rates (frozen) | low 0.05 / high 0.025 | 5.0% / 2.5% both OK | yes |
| ladder_stop | (2) leg_studentized both cadences | selected at (2) | yes |
| Confirm seeds / n | 41000/42000; n=200 | same | yes |
| Confirm cov low/high | 0.055 (11/200) / 0.035 (7/200) | 5.5% FAIL / 3.5% OK | yes |
| Confirm α̂ low/high | 0.085 (17/200) / 0.065 (13/200) | 8.5% / 6.5% both FAIL | yes |
| Wilson low (disclosure) | ~[5.4%, 13.2%] / [3.8%, 10.8%] | same bands | yes |
| method on e2e rows | leg_studentized_bootstrap_t | leg bootstrap frozen | yes |
| STOP / verdict | true / STOP | STOP; binder-form fork | yes |
| alpha_target | 0.05 | ≤5% point gate | yes |

---

### Governance checklist (P3d)

| Check | Result |
|---|---|
| Fresh-context independence | PASS |
| L-12 predeclaration (design/confirm, ladder, gate, seeds) | PASS |
| Design fit isolated from confirm gate | PASS |
| Frozen procedure not refit on confirm | PASS |
| Point α gate; Wilson not binding | PASS |
| No fixture / holdout / `run_final_gate` | PASS |
| No α/confidence softening after confirm fail | PASS |
| Binder-form (a/b/c) recommend-only | PASS |
| No P3e / more L/confidence-map knobs | PASS |
| No seam-ladder revival | PASS |
| No freeze / default-route restore / P4–P5 | PASS |
| STOP ≠ “fail QA” | PASS — confirm stop authorized; review object is harness discipline |

---

### Issues

1. **[Note — non-blocking] Step-(1) early-exit not coded as a hard stop**  
   Design §P3d.4 says stop at first ladder rung that clears design coverage on **both** classes. On the design bank, calendar studentized already shows high rates 1.25% (OK) and low OK at several L (e.g. L=32 @ 3.75%). Harness records step 1, prints `high ever OK?`, then **always** advances to step 2 and freezes the first leg both-ok. Justification aligned with design intent: §P3d.3 high form says calendar L is **not** the primary lever (use leg bootstrap); §P3d.1 residual is empty-bar geometry; report labels step-1 high OK “fragile” on n=80. First both-ok **within** step 2 is correctly first-clear (B=200, bl=1). Does not change confirm STOP under the frozen leg procedure. Optional: if re-run ever needed, either implement explicit step-1 joint freeze or predeclare “step 1 diagnostic only; freeze candidate starts at (2).”

2. **[Note — non-blocking] Freeze block written after confirm finishes in runner**  
   `run_p3d_cal.py` calls `run_p3d()` (design+confirm) then `write_freeze_into_design(design["frozen_procedure"])`. In-memory procedure is design-only and is what confirm uses; confirm does not mutate it. Wall-clock §P3d.8 write is after confirm compute, not between banks. Acceptable for single-shot script; process order still “design freezes procedure, confirm only evaluates.”

3. **[Note — non-blocking] Extra step-2 grid after first clear**  
   Loop continues B∈{200,400} × bl∈{1,2,4} after `selected_method` is set (trace-only). Selection is locked to first both-ok. Waste only; no cherry-pick of later cells.

4. **[Note — non-blocking] Unit tests are smoke-only**  
   `test_xena_p3d.py` covers leg bootstrap finite + LCB field names. No assertions on seed bases, design/confirm isolation, ladder stop, or STOP composition. Artifacts + source review cover governance; tests do not.

5. **[Note — operator] Confirm residual after leg unit**  
   High no-search improved (3.5% ≤5%) vs P3c calendar 5.5–7.5%; low cov 5.5% and e2e inflation (5.5%→8.5%, 3.5%→6.5%) remain. Report correctly exits to binder-form fork, not more estimator knobs. Outside harness QA.

---

### Scope overreach audit (P3d review)

| Forbidden | Present? |
|---|---|
| Confirm-bank refit of L / B / interval | **No** |
| α or confidence soften after confirm fail | **No** |
| P3e / more estimator knobs after STOP | **No** |
| Binder-form (a)/(b)/(c) implemented | **No** (text recommend only) |
| Seam-ladder reopen / purge mult sweep | **No** |
| P4 registry freeze / blind VAL / default-route restore | **No** |
| P5 cost-aware search | **No** |
| Extensive-F `run_final_gate` as binder | **No** |
| XENA-001/002/003 or holdout in P3d harness | **No** |
| Reused P3/P3b/P3c seed bases | **No** (31k/32k design; 41k/42k confirm) |
| “Accepted” frozen production procedure despite STOP | **No** (STATUS is FROZEN_AFTER_DESIGN only) |

---

### Why APPROVE (not REVISE / REJECT)

**APPROVE:** P3d predeclared design/confirm split with disjoint 31k/32k vs 41k/42k banks; interval ladder ran (1)→(2) and froze **leg-studentized** (B=200, bl=1) as first step-2 both-clear; confirm evaluated that frozen procedure only; honest STOP on low coverage 5.5% + e2e 8.5%/6.5% with α target left at 5%; binder-form (a/b/c) recommend-only; no fixtures/`run_final_gate`/P3e/P4/P5; seam ladder not reopened. Report P3d matches `p3d_confirm.json` `stop_condition`.

**Not REVISE:** No design-fidelity gap that would change STOP/PROCEED handling under the frozen procedure, confirm isolation, seed disjointness, or binder-form non-implementation. Note 1 (step-1 early-exit) is a predeclaration/process polish, not a stop-discipline defect given §P3d.3 high form + mechanistic primary at (2).

**Not REJECT:** No holdout/fixture contact, no confirm refit, no α soften, no unauthorized binder-form implementation, no seam reopen, no silent production freeze.

**Reminder:** APPROVE means the **P3d harness + stop discipline** are compliant. It does **not** mean confirm passed or P4 is authorized. Verdict is **STOP**; **P4 remains blocked**. Next authorized work is a *new* predeclared binder-form phase (favor a→b→c), not P3e knobs.

---

*End QA run 6 (P3d).*

---

## P-BF design STOP — integrity note (2026-07-13, salvage)

| Check | Result |
|---|---|
| Confirm bank touched? | **No** |
| XENA fixtures TEST/holdout? | **No** |
| `run_final_gate`? | **No** |
| P-BF.7 freeze? | **NOT_FROZEN** (correct under design STOP) |
| Under-K freeze after failed rel? | **No** |
| Pre-amendment self-ref K=99 artifact used as freeze? | **No** (quarantined) |
| Bite recipe validated? | **Yes** (both cadences) |
| Amended K-rule applied before freeze attempt? | **Yes** |
| Host crash mid kconv-high? | **Yes** (operator) — no re-launch of K_pool=199 battery on this host |

**Verdict:** design STOP is integrity-preserving. Confirm correctly withheld. Recommend exit (c) is documentation-only for this phase.

