# INFR-009 — Progress So Far (session handoff)

**Date:** 2026-07-14 · **Status:** **P5 COMPLETE — VAL_PASS + route RESTORED** · active pin v2 `db87dc1a…` (flat net RT 1.0 bps) · α̂ 5.0% boundary accepted · default route **RESTORED**
**Purpose:** self-contained state so a new session continues without re-deriving. Read this, then the linked artifacts.

---

## 0. One-line status

INFR-009 **closed the binder path**: exit (c) two-stage sample-split **CONFIRM DUAL_CERTIFY** (α̂ 5.0%/5.0%, selection_inflation≈0, boundary accepted). **P4** froze the procedure and validated gross on 001/002/003 (SEG_PROXY; holdout never read). **P5** fixed deployability: **inject flat 1.0 bps RT on net only** (top-1 binding); re-VAL **`VAL_PASS`** (001/002 not certified; 003 gross +1.077 / net@1.0 −0.085). **Route RESTORED** under `results/pc_frozen_registry.json` v2 (parent P4 `44e1aa3c…` archived). Operator remains final on capital; INFR-006 v3 extensive-F stays superseded.

---

## 1. What INFR-009 is

Redesign of the XENA adjudication layer, superseding the frozen INFR-006 v3 registry (whose absolute-F thresholds were shown to be coin-flips at live scale — audit A–F). **Binding design + provenance:** `.ignore/temp/cons/consolidated-03.md`. Canonical design: `python/experiments/INFR-009/design.md`.

Core moves (all shipped in P0–P2): stop binding on extensive log-wealth F; disclose intensive economics before search (Q1); search/rank on an **intensive** turnover-edge `g_gross`; turn plateau/Jaccard/random-subset into **evidence not thresholds**; retire the confounded permutation battery for print/path decomposition; make the final gate a **scale-free** binder. The unresolved piece is the **binder** — see §4.

---

## 2. Locked operator decisions (predeclared; do not re-open silently)

| # | Decision | Value |
|---|---|---|
| Objective | intensive `P25(g_gross)`, **costless** (A-1 impl amended, cost policy kept); no min-n floor | LOCKED |
| Denominator | **entry notional** `|Units·EntryPrice·mpu|`; identical search/fold/TEST | LOCKED |
| DD | **disclosure-only**; deployability = `net-LCB>0` alone; R_max/DD reconciled offline, binds nothing | LOCKED |
| Binder target | one-sided **95% LCB > 0**; **α = 5%** end-to-end FP at **both** cadences; power/MDE measured & disclosed (not frozen to INFR-006 cells) | LOCKED |
| Cost floor (Q1) | `floor = RT_cost_bps × k`, k on CAL; MDE disclosed separately | LOCKED |
| Block | reuse common-block; **block ≥ H**; length from CAL sweep | (superseded by per-cadence/leg work) |
| Null bank | fresh multi-source; **XENA-001/002/003 stay BLIND** (P4 VAL fixtures) | LOCKED |
| α gate rule | **point α̂ ≤ 5%** (not UCB); Wilson/SE disclosure only; predeclare n; **no optional stopping** | LOCKED |
| CAL discipline | **design/confirm bank split** (fit on design, gate on disjoint confirm); disjoint seeds each round | LOCKED |

---

## 3. Phase timeline

### P0–P2 — shipped, compliant (6 QA findings fixed)
- **P0** `economics.py`: Q1 universe economics disclosure + cost-map integrity precondition (`INTEGRITY_INCOMPLETE` refuses search/gate; drops NO candidate). Fixture recompute: 001 +0.043, 002 −0.284, **003 +1.910** bps (003 matches design; 001/002 near-zero, sub-floor). *NB: design acceptance table still lists −0.065/+0.085 for 001/002 — correct to the honest recompute before P4 VAL.*
- **P0′** `high_cadence_null.py`: zero-edge high-cadence null generator (003 density).
- **P1** `score.py` (`g_gross`, `robust_g_hat`), `search.py`: binding score = intensive `P25(g_gross)`; `certify.py`: certification → **evidence package** (F_floor, min_drop, Hamming, resim, **S all non-binding**).
- **P2** `fill_basis.py`: mandatory print-vs-path; HARD battery RETIRED.
- Emission/oracle/estimand/fences/Rust kernel UNCHANGED. 56 tests pass.

### P3 → P3d — CAL saga (each STOPped correctly; the guard INFR-006 lacked)
| Phase | Change | Verdict | Key numbers |
|---|---|---|---|
| **P3** | raw 5th-pctile LCB on ratio | STOP | low no-search coverage 10–20% (est. defect); high e2e 15% (selection); no block clears |
| **P3b** | **A1** studentized LCB + **B1** rank→TEST purge≥H | STOP (big progress) | **F2 closed** high e2e 15%→2.5%; low coverage fixed @ L=40; low e2e 7.5% @ n=40 (underpowered) |
| **P3c** | freeze-grade **n_null=200** | STOP | low e2e residual = **NOISE** (5.0% @ n=200); exposed **no joint L** (low wants ≤32, high under-covers 5.5–7.5% at *every* L) + high e2e 5.5% |
| **P3d** | design/confirm split; **leg-studentized** LCB | STOP (terminal for estimator path) | cleared DESIGN (n=80) but **FAILED CONFIRM (n=200)**: e2e 8.5%/6.5% vs no-search 5.5%/3.5% |

**P3d conclusion:** e2e inflates *over* no-search at both cadences (~3%). Forensics (`p3c_high_e2e_passers.json`, and p3d confirm rows): e2e passers ≈ fails on search score → **not cherry-picking; it's pick-best-of-restarts multiplicity leaking across the seam.** An LCB on a *searched* subset structurally cannot cancel this (the **searched≠unselected** residual, consolidation §3/§6.3). No interval knob fixes it → pivot to binder form.

### P-BF — binder-form (permutation-through-search) — FAILED at design bank
- Recipe `circular_shift_marks_open_rebuild_fills` (causal-alignment break, NOT P&L shuffle): **bite-check PASS** (plants collapse 96–99.7%, nulls flat). `score.mean_per_leg_bps` frozen as the statistic (light (a)+(b)).
- **K-rule bug caught + amended** before freeze: original rule measured `|q_K − q_99|` (self-referential — can only pick the top rung). Amended to reference q_199.
- **Failure (design_ok=false):** even amended, **K does not converge** — low K=99 rel 0.559, K=149 rel 0.270 vs q_199 (tol 0.25). The pass threshold is the tail quantile of a **max-over-restarts** statistic → intrinsically high-variance, unestimable at feasible K (foreshadowed: consolidation §3 "P95/P99 tail unestimable at affordable K"). Compute (K=199 × 8 workers × full-search/perm) **bricked the host.**
- `stop_reason = K_not_converged_and_compute_crash`; **recommend exit (c)**; confirm NOT_RUN; P4 blocked.

### P-C — exit (c) two-stage sample-split — **CONFIRM DUAL_CERTIFY** (2026-07-14)
Predeclaration `design.md` §P-C. Forks locked by operator: **A** per-cadence certification (dual-AND retired for (c) gate logic only — scope, not integrity), **B** bite-fail → terminal, no held-out.
- **Procedure (frozen after design, `results/pc_design.json`):** stage-1 search+certify → **exactly one** subset (no shortlist) → **embargo 0.20 of span** (low 60·H, high 200·H ≫ regime memory; P3d adjacent-purge that leaked was 1·H) → stage-2 `lcb_g_leg_studentized(g_gross)>0` (the **P3d frozen estimator** on the binding g_gross ratio; reconciled the handoff's "mean_per_leg" phrasing — (c) drops permutation so stays on binding g_gross). Banks design 71000/72000 n=80, confirm 81000/82000 n=200, disjoint from all P3*/P-BF.
- **Bite (independence proof) PASS both cadences** — stage-1-localized plant (de-plant stage-2 via exact inverse `raw=ExitPrice/(1+d·e/1e4)`) does NOT survive to stage-2: low 0/8 survival, high **1/8 (borderline, exactly at 0.125 threshold)**; both select the plant 8/8. **Fork B terminal NOT triggered — embargo independence holds.**
- **CONFIRM DUAL_CERTIFY (`results/pc_confirm.json`):** e2e α̂ **5.0%/5.0%** (10/200 both), no-search cov 4.5%/4.0%, **selection_inflation 0.5pp/1.0pp (≈0 — P3d's ~3pp leak killed by construction).** certified both → recommend **P4_both**.
- **Boundary caveat (do not oversell):** both cadences land **exactly on the α̂=5% gate line**. Passes the **predeclared point-α̂ ≤5% rule** (locked gate — point, not UCB), but Wilson-95 upper = 9.0% → thin margin, not decisive. High bite borderline. Discipline held: single n=200, predeclared, no optional stopping.

---

### P4 — freeze + blind VAL — **DONE: GROSS clean; deployability clean after cost correction** (2026-07-14)
Predeclaration `design.md` §P4. Operator mandate: freeze (c) + blind VAL (route-restore NOT in scope).
- **Pre-freeze flags cleared:** (1) Rust fold-parity red case `best-r00` was a **stale pinned digest** (XENA-001 `search_restart_00.json` best_subset regenerated upstream), NOT a kernel divergence — **proven python==rust bitwise**; pins regenerated (499/500 unchanged), gate green (7 passed). (2) binding estimand = **g_gross ratio** (design §3), not mean_per_leg.
- **Freeze:** `results/pc_frozen_registry.json` sha256 `44e1aa3c…` (frozen (c) proc + confirm summary + integrity attestation + operator signoff). Route-restore explicitly NOT frozen.
- **Blind VAL (SEG_PROXY only; holdout TEST NEVER read):** stage-1 g_gross top-1 over each fixture's 12 finalists → stage-2 leg-LCB gross+net on SEG_PROXY.
  - **GROSS (the (c) FPR claim) — clean, matches expected:** 001 gross_LCB −0.249, 002 −0.248 → not certified (FPR control on real nulls); 003 **gross_LCB +1.077** → gross-certified (real gross, corroborates Q1 +1.910).
  - **NET first run INVALID (under-charged, not ≈gross):** real fixtures engine-costless (cost_bps median 0.0, few up to ~13); `eval_lcb_legs(net=True)` charges only sparse stream cost — far below the real ~1–3 bps FTMO RT. Net IS below gross (003 top-1 +1.077 gross/−0.180 net; gaps 0.1–1.3 bps) but under-charged → 003 spuriously 7/12 finalists net+. Cost must be INJECTED (xen.evaluation FTMO), not read off stream ([[cost_model_and_injection]]).
  - **NET corrected (flat-cost sweep, `pc_val_costsweep.json` = governing deployability record):** 003 top-1 net_LCB 0.0→+1.08, 0.7→+0.32, 1.0→−0.09, **1.5→−0.65**, 2.0→−1.21; 003 finalists net-pass 12/12@0.7 → 2/12@1.0 → **0/12@≥1.5**; 001/002 net-negative at all costs. Deployability dies across **0.7–1.5 bps = known 003 breakeven→ruin band** → at realistic spread NOTHING deployable; **003 = real gross, cost-fatal, reproduced exactly.** Deployability PASSES on the corrected read. **NB primary `pc_val.json` verdict field stays `VAL_FAIL_redesign_rejected`** (strict any-finalist rule on the INVALID net axis; NOT re-run) — to flip the machine verdict, re-run VAL with injected cost.
  - **Per-symbol FTMO injection ATTEMPTED → BLOCKED:** 12 fixture symbols are index/commodity CFDs; FTMO commission ≈0 (cost is all SPREAD); `spread_pips` NOT pinned (round_trip_cost_bps refuses; needs live FTMO page). Can't fabricate. But **verdict is COST-ROBUST**: on the §P4.2 binding top-1 rule, 003 top-1 net<0 for ALL cost ≥1.0 (1.0→−0.085, 1.5→−0.654), 001/002 net<0 everywhere → **`VAL_PASS_binding_top1`** (`pc_val_injected.json`), no fixture deployable across the realistic band, no cost cherry-pick. (Raw `pc_val.json` verdict stays FAIL — any-finalist DISCLOSURE rule mis-wired vs §P4.2 binding top-1, on the invalid stream-cost axis; superseded.)
  - **FROZEN-PROCEDURE DEFECT (fix before live; GOVERNANCE):** (c) net gate reads stream cost_bps → inert on engine-costless live emissions → would falsely credit sub-cost deployable. Fix = inject FTMO cost into net-LCB, or make injected-cost net-LCB>0 the binding stage-2 objective (also closes B3). Changes the FROZEN procedure → needs its own predeclaration + operator sign-off (not an in-place edit). Gross cert unaffected.

---

### P5 — net-path amendment + re-VAL + route-restore — **COMPLETE** (2026-07-14)
Predeclaration `design.md` §P5. Operator locks: flat RT **1.0 bps** enough; α̂ **5.0% boundary accepted**.
- **Amended freeze (v2):** `results/pc_frozen_registry.json` sha256 `db87dc1a…`; parent P4 `44e1aa3c…` archived as `pc_frozen_registry_p4.json`.
- **Net path:** inject flat **1.0 bps** on net stage-2 only; gross costless; deployability = **top-1** net_LCB>0.
- **Re-VAL (`pc_val_p5.json`):** **`VAL_PASS`** — 001 net@1.0=−1.137; 002 −1.221; 003 gross +1.077 / net −0.085; nothing deployable.
- **Route RESTORED** under this pin (INFR-006 v3 extensive-F remains superseded; operator final on capital).

---

## 4. Current position + exact next step

**INFR-009 binder programme complete.** Live pin = P5 v2 (`db87dc1a…`). Default XENA route **RESTORED**. Do not re-run (c) confirm (α-shopping); do not read holdout; do not loosen α gate silently.

**Next outside this EXP:** use the restored route on new universes; optional per-symbol spread pins later if you want finer net fairness (not required for the flat 1.0 bps gate).

**Historical context below (superseded):** the pre-(c) fork discussion.

---

## 4b. (superseded) Pre-(c) recommendation

**Exit (c) two-stage** is recommended and is the design's reserved exit. It is **not a fallback — it is structurally cleaner:** (b) tried to *correct* selection post-hoc (ill-conditioned + host-unsafe); (c) *prevents* leakage by construction — **fix ONE subset → test on a genuinely independent band** → no permutation, no K× re-search, no tail quantile → host-safe. It reduces e2e back to the **no-search coverage** problem the leg bootstrap nearly solved (high 3.5% OK, low 5.5% borderline).

**Recommended (c) predeclaration:**
- Stage 1 (cheap): Q1 economics + `g_gross` search → shortlist → **fix ONE subset** (or tiny pre-registered shortlist) before stage 2.
- Stage 2: `lcb_g_leg_studentized(mean_per_leg) > 0` on the **independent** band. Single eval/universe. No permutation.
- **Gate:** e2e point α̂ ≤ 5% both cadences, n=200 confirm; design/confirm split; no optional stopping.
- **Compute:** n_null × (1 search + 1 stage-2 eval) — trivial vs K×, host-safe.

**THE OPEN FORK (decide before writing the (c) prompt): the stage-2 independence recipe.** The adjacent purge already leaked in P3d, so stage-2 must be *genuinely* decorrelated:
1. **Distant/embargoed segment** — large temporal gap; may still leak on long-memory regimes.
2. **Held-out instruments** — strongest decorrelation; changes estimand (cross-instrument generalization); needs bank support.
3. **Bite-checked either** — predeclare, then *prove* independence (a stage-1-only planted edge must NOT survive into stage-2).

My lead recommendation: **distant/embargoed + mandatory bite-check**, held-out-instruments as the stronger variant if the embargo leaks. **If even max-achievable independence still leaks α>5% → terminal "cannot certify at α=5%"** (a valid programme outcome). (c) is the **last structural card**.

**Ops constraint:** never run uncapped K×-search batteries on the laptop again — cap workers/memory or offload to EC2 (INFR-007 note).

---

## 5. File map

**Design/provenance:** `.ignore/temp/cons/consolidated-03.md` (binding design) · `INFR-009/design.md` (canonical; §P-BF.7 = NOT_FROZEN) · `INFR-009/report.md` · `INFR-009/qa-review.md`

**Shipped code (`python/src/xen/xena/`):** `economics.py` `score.py` `fill_basis.py` `high_cadence_null.py` (new) · `search.py` `certify.py` `final_gate.py` `calibration.py` `__init__.py` (modified) · `calibration_p3{,b,c,d}.py` `calibration_pbf.py` **`calibration_pc.py`** (CAL harnesses)
`score.py` functions: `g_gross_point`, `mean_per_leg_bps`, `robust_g_hat`, `effective_n_diagnostics`, `lcb_g` (retired raw-pctile), `lcb_g_studentized`, `lcb_g_leg_studentized` (current), `bootstrap_g_legs`, `ledger_leg_arrays`.

**Drivers:** `INFR-009/analysis_code/run_p3{,b,c,d}_cal.py`, `run_pbf_cal.py`, **`run_pc_cal.py`**, **`run_pc_val.py`** (`--p5` = amended freeze + re-VAL + route pin)

**Results (`INFR-009/results/`):** … + **`pc_frozen_registry.json`** (v2 live pin `db87dc1a…`) + **`pc_frozen_registry_p4.json`** (archive) + **`pc_val_p5.json`** (**VAL_PASS**) + `pc_val_costsweep.json` + `pc_val_injected.json`

**Memory (read at session start):** `infr009-binder-form-pivot` · `iterated-calibration-discipline` · `cal-fpr-resolution-scales-with-n-null` · `diagnosis-ground-in-artifact` · `xena-referee-scale-defect`

---

## 6. Guardrails still in force
- NEVER read XENA-001/002/003 TEST/holdout on calibration; holdout remains fenced for counted TEST gates.
- NEVER re-enable absolute extensive-F binder (INFR-006 v3 superseded).
- No α softening after seeing results; **do NOT re-run (c) confirm to "improve" 5.0%** (α-shopping). Boundary accepted as-is.
- Deployability uses **injected flat RT 1.0 bps** on net path (P5); do not use bare stream `cost_bps` on engine-costless emissions.
- **Active pin:** `results/pc_frozen_registry.json` v2 sha256 `db87dc1a…`. Default route **RESTORED**. Operator final on capital/universe certify.

---

## 7. Two terminal exits — **exit A HIT; P4/P5 completed**
- **✅ A CONFIRM passes** → P4 freeze+VAL → **P5 net fix + route-restore**. Done 2026-07-14.
- **(c) fails on measured α** → terminal cannot-certify. *(Not taken.)*
