# INFR-009 Report — XENA Adjudication Redesign

**Date:** 2026-07-14  
**Latest:** **P5 COMPLETE — net-path fixed (flat RT 1.0 bps) + re-VAL `VAL_PASS` + route RESTORED.** Gross clean (001/002 rejected, 003 real-gross); deployability top-1 net@1.0 bps all ≤0. α̂=5.0% boundary accepted. Active pin `pc_frozen_registry.json` v2 sha256 `db87dc1a…` (parent P4 `44e1aa3c…`).  
**Default route:** **RESTORED** under exit (c) + injected net 1.0 bps; INFR-006 v3 extensive-F remains superseded; operator final on capital.

---

## Trajectory

| Phase | Result |
|---|---|
| P0–P2 | Shipped |
| P3 | STOP — percentile LCB; high e2e 15% |
| P3b | STOP — F2 closed (high e2e 2.5%); low e2e 7.5% @ n=40 underpowered |
| P3c | STOP — low e2e→5% (noise); joint L fail; high coverage-driven 5.5% |
| P3d | STOP on CONFIRM — leg bootstrap design OK; confirm e2e 8.5%/6.5% |
| **P-BF** | **DESIGN STOP** — bite OK; amended K-rule fails on low; host crash mid high; **no confirm** |
| **P-C** | **CONFIRM DUAL_CERTIFY** — two-stage sample-split; e2e α̂ 5.0%/5.0% (10/200 both); cov 4.5%/4.0%; **selection_inflation 0.005/0.010 (P3d ~3pp leak killed)** |
| **P4** | Freeze + blind VAL; GROSS clean; deployability cost-robust; **route WITHHELD** (net-path defect) |
| **P5** | **Net inject 1.0 bps + re-VAL VAL_PASS + route RESTORED** (v2 registry `db87dc1a…`) |

---

## P-BF — permutation-through-search binder

### Scope (operator mandate)

Replace LCB(g_gross)>0 with selection-aware **search→select→TEST under permutation null**.  
Frozen functional: **mean per-leg bps**. g_gross / LCB = companion disclosure only.  
Not authorized: P3e, α soften, LCB knobs, P4, implement (c).

### Procedure freeze (predeclaration)

- Recipe: `circular_shift_marks_open_rebuild_fills` (entry↔forward break; not P&L shuffle)
- Pass: `T_real > q_{1−α}` of own K-perm null (α=5%)
- Banks: design 51000/52000 n=16; confirm 61000/62000 n=200 (confirm **never started**)
- **K-rule amendment (2026-07-13, pre-freeze):** certify K∈{99,149} vs **q_199** (rel≤0.25). Top rung never frozen by construction. See `design.md` §P-BF.4.

### Bite-check (DESIGN) — PASS

| Cadence | Plant real→perm | Collapse | Null real→perm |
|---|---|---|---|
| Low | 5.27 → −0.20 | **96.2%** | 0.33 → 0.34 |
| High | 20.00 → −0.05 | **99.7%** | 0.03 → −0.05 |

Causal-alignment permutation has **bite**. Not a vacuous mean-invariant null.

### K-convergence (amended) — FAIL (low complete; high incomplete)

**Low (16/16 complete):**

| K | rel vs q_199 | Certifiable? | ≤0.25? |
|---|---|---|---|
| 19 | 1.246 | no | no |
| 39 | 1.388 | no | no |
| 59 | 0.664 | no | no |
| **99** | **0.559** | yes | **no** |
| **149** | **0.270** | yes | **no** |
| 199 | 0.0 | no (validator only) | — |

`chosen_K = None` on low. Joint K\* requires both cadences → **not freezeable**.

**High:** reached **8/16** under K_pool=199 × 8 workers, then host **hung and hard-shut down** (operator report; uptime reset). No high quantile certified.

**Pre-amendment self-ref run** (quarantined `pbf_design_pre_amendment_K99ref.json`): would have frozen K=99 because top rung vs itself is always 0 — **rejected** as mis-specified.

### Confirm bank

**NOT RUN.** Gate not attempted. `pbf_confirm.json` not produced (by design after design STOP).

### Verdict

```
design_ok = false
stop_reason = K_not_converged_and_compute_crash
confirm = NOT_TOUCHED
P4 = blocked
```

**Recommend: exit (c)** — two-stage (intensive screen + TEST statistic on a genuinely independent band).

| Why (c), not terminal “cannot certify α” | Why not more K / re-run |
|---|---|
| Failure is **K-validity + compute**, not measured e2e α under a certified null | Low already proves q_99/q_149 unsettled vs q_199; under-K forbidden |
| Host-killing cost of search-through-perm null at freeze-grade n | Re-running K_pool≥199 × confirm n=200 risks same crash; 12h budget not a license to brick the machine |
| Bite recipe is sound — the **binder cost structure** is the blocker | No P3e / no α soften / no LCB revival |

**Do not implement (c) in this phase** (operator mandate).

### Explicit non-actions

- No confirm bank  
- No under-K freeze  
- No P3e / LCB knobs / α soften  
- No P4 / route restore  
- No re-launch of K_pool=199 full design on this host without compute plan  

---

## P3d (prior) — design / confirm (last estimator round)

### Confirm-bank gate (`results/p3d_confirm.json`)

| Metric | Low | High | Gate |
|---|---|---|---|
| No-search coverage | **5.5%** | **3.5%** | low FAIL |
| E2e α̂ | **8.5%** | **6.5%** | **both FAIL** |

Selection residual forced binder-form. P-BF was the forced path; design bank closed it via K/compute.

---

## P-C — exit (c) two-stage sample-split (design.md §P-C)

### Scope (operator locks, 2026-07-14)

The last structural card. Select on stage-1 data only; test ONCE on a distant/embargoed stage-2
band → the selection leak is prevented **by construction**, not corrected post-hoc. No permutation,
no K×-search, no tail quantile → host-safe. Two operator forks:

- **Fork A — per-cadence certification.** Dual-AND retired for (c) gate logic only (scope, not
  integrity: α=5%, point α̂, n=200, design/confirm split, no optional stopping — all unchanged).
- **Fork B — bite failure → TERMINAL; no held-out-instrument escalation** in this experiment
  (held-out = different estimand = separate future programme, never a P4 route-restore here).

### Procedure (frozen after design; `results/pc_design.json`)

- Stage 1: search + certify → **exactly one** subset (top-1); no shortlist.
- Embargo: **0.20 of span** between ranking end and gate start (low 60·H, high 200·H ≫ regime
  memory ~100 bars; the P3d adjacent-purge that leaked was 1·H).
- Stage 2: `lcb_g_leg_studentized(g_gross) > 0` — the **P3d frozen estimator** on the binding
  g_gross ratio (design §3), leg bootstrap, `n_boot=200`, `block_legs=1`, 95%. (Reconciled the
  handoff's "mean_per_leg" phrasing: (c) drops permutation, so stays on the binding g_gross.)
- Banks: design 71000/72000 n=80; confirm 81000/82000 n=200. Disjoint from all P3*/P-BF.

### Bite-check (DESIGN) — independence PASS both cadences (Fork B terminal NOT triggered)

Stage-1-localized plant (`edge=20`, de-plant the stage-2 band via exact inverse
`raw_exit = ExitPrice/(1+d·e/1e4)`) must **not** survive into stage-2.

| Cadence | Stage-1 selects plant | Stage-2 survival (≤0.125) | Verdict |
|---|---|---|---|
| Low | 1.000 (8/8) | **0.000** (0/8) | PASS |
| High | 1.000 (8/8) | **0.125** (1/8) | PASS — *borderline (exactly at threshold)* |

Embargo independence holds: a stage-1-only edge collapses on the distant band. High is the weak
link (1/8 leaked, ≈ high coverage noise at n=8).

Design no-search coverage (disclosure, n=80): low **7.5%**, high 2.5% — the low-cadence
coverage-limited residual, at small-n. Resolved at confirm n=200 below.

### Confirm gate (`results/pc_confirm.json`) — DUAL_CERTIFY

| Metric | Low | High | Gate (point ≤5%) |
|---|---|---|---|
| No-search coverage | 4.5% (9/200) | 4.0% (8/200) | ✓ both |
| **E2e α̂** | **5.0% (10/200)** | **5.0% (10/200)** | ✓ both (boundary) |
| **selection_inflation** (e2e − no-search) | **+0.5pp** | **+1.0pp** | — |
| Wilson-95 on α̂ | [2.7%, 9.0%] | [2.7%, 9.0%] | disclosure only |

**The result that matters:** `selection_inflation` collapsed from P3d's **~3pp** (8.5%/6.5% e2e over
5.5%/3.5% no-search) to **≈0** (0.5pp / 1.0pp). (c) prevented the selection leak by construction —
exactly the design claim. e2e ≈ no-search at both cadences.

**Honest caveats (not "pipeline green"):**
- Both cadences land **exactly on the gate line** (α̂=5.0%, 10/200). This **passes the predeclared
  point-α̂ ≤ 5% rule** (the locked gate — point, not UCB; L: `cal-fpr-resolution-scales-with-n-null`),
  but it is a **boundary pass**, not a comfortable margin — Wilson upper is 9.0%. Discipline held:
  single n=200, predeclared, no optional stopping.
- High-cadence bite was borderline (1/8). Low is the cleaner cadence on bite; high is cleaner on
  coverage — no single cadence dominates both diagnostics.

### Verdict

**DUAL_CERTIFY** under the predeclared selection-aware two-stage gate. Recommend **P4** (freeze the
(c) procedure registry; blind VAL on 001/002/003 via SEG_PROXY; route-restore) — **operator-mandated,
per cadence.** This is the first CAL confirm to pass α at both cadences across the whole
P3→P3d→P-BF→P-C arc; it is a boundary pass, so P4 should treat the margin as thin, not decisive.

### Deliverables (P-C)

| | |
|---|---|
| §P-C predeclaration + freeze | `design.md` §P-C |
| Harness | `xen.xena.calibration_pc`, `score.lcb_g_leg_studentized` |
| Driver | `analysis_code/run_pc_cal.py` |
| Design (bite + coverage; FROZEN) | `results/pc_design.json` |
| Confirm (DUAL_CERTIFY) | `results/pc_confirm.json` |
| Tests | `tests/test_xena_pc.py` (5 pass) |

---

## P4 — freeze + blind VAL (design.md §P4)

### Pre-freeze integrity (both flags resolved 2026-07-14)

- **Rust fold parity:** the one red case (`best-r00`) was a **stale pinned digest** (XENA-001
  `search_restart_00.json` `best_subset` regenerated upstream), **not** a kernel divergence —
  proven `python == rust` bitwise on that case + 488 random + 11 best-r. Pins regenerated
  (499/500 unchanged → semantics intact); gate green (7 passed).
- **Binding estimand** confirmed = **g_gross ratio** (design §3), not `mean_per_leg`.

### Freeze

`results/pc_frozen_registry.json` — sha256 `44e1aa3c…` over frozen (c) procedure + confirm
summary + integrity attestation + operator signoff. Route-restore explicitly NOT frozen.

### Blind VAL (SEG_PROXY 2023-07-13→2024-03-28; holdout TEST 2024-03-28→2024-12-11 NEVER read)

Frozen (c) binder on each fixture: stage-1 = g_gross P25 top-1 over the fixture's 12 search
finalists; stage-2 = leg-studentized LCB gross + net on SEG_PROXY.

| Fixture | Q1 p50 bps | top-1 gross_LCB | top-1 net_LCB | Verdict | Expected | Match |
|---|---|---|---|---|---|---|
| XENA-001 (null) | +0.043 | −0.249 | −0.647 | not certified | not deployable | ✓ |
| XENA-002 (sub-zero) | −0.284 | −0.248 | −0.597 | not certified | not deployable | ✓ |
| XENA-003 (real gross) | +1.910 | **+1.077** | **−0.180** | gross-certified, not deployable | not deployable | ✓ |

**GROSS axis (the (c) FPR-controlled claim): clean, matches predeclared.** 001/002 gross_LCB<0 → not
certified (FPR control on a real null holds); 003 gross_LCB +1.077 → gross-certified, corroborating
Q1 +1.910. This is the binder's core claim and it validates.

### Net axis: first run invalid → corrected by cost injection

**The frozen net path under-charges cost on real fixtures.** All three fixtures are engine-costless
(`cost_bps` median **0.0**, a few candidates up to ~13; real costs are analyst-injected via
`xen.evaluation` FTMO, not carried on the stream — memory `cost-model-and-injection`). So
`eval_lcb_legs(net=True)` charges only the sparse stream cost — **far below** the real ~1–3 bps FTMO
round-trip. Net is genuinely below gross (003 top-1 +1.077 gross vs −0.180 net; finalist gaps
~0.1–1.3 bps) but nowhere near the true cost, so 003 spuriously shows **7/12 finalists net_LCB>0**.
**That "deployable" read is a cost-under-charging defect, not signal** (not literally net≈gross —
the charged cost is just far too small).

Corrected with a flat injected RT-cost sweep (`results/pc_val_costsweep.json`):

| flat RT cost (bps) | 003 top-1 net_LCB | 003 finalists net-pass | 001 / 002 top-1 |
|---|---|---|---|
| 0.0 | +1.077 | 12/12 | −0.25 / −0.25 |
| 0.7 (breakeven) | +0.315 | 12/12 | −1.05 / −0.88 |
| 1.0 | −0.085 | 2/12 | −1.14 / −1.22 |
| **1.5 (ruin)** | −0.654 | **0/12** | −1.61 / −1.69 |
| 2.0 | −1.207 | 0/12 | −2.15 / −1.98 |

003 deployability **vanishes across 0.7–1.5 bps — exactly the known breakeven→ruin band**
(`xena-003-cost-fatal`: breakeven ~0.71, ruin by ~1.5). At realistic CFD spread (1–3 bps) **no fixture
is deployable**. 003 = **real gross, cost-fatal — reproduced exactly.**

**Cost-injection attempt → per-symbol EXACT is blocked, but the verdict is cost-robust.** The 12
fixture symbols are index/commodity CFDs; FTMO **commission ≈ 0** for indices (cost is all **spread**),
and `spread_pips` is **not pinned** in the snapshot (`round_trip_cost_bps` refuses — it must be read
off the live FTMO page). Cannot fabricate spread. But exact spread is **not needed** for the verdict:
the (c) binder deploys the **top-1** subset, and on the predeclared **§P4.2 binding top-1 rule** 003's
top-1 net_LCB is **negative at every realistic cost ≥1.0 bps** (1.0→−0.085, 1.5→−0.654, 2.0→−1.207),
001/002 negative everywhere → **no fixture deployable across the whole realistic index-CFD band**.

**Corrected verdict = `VAL_PASS_binding_top1`** (`results/pc_val_injected.json`), cost-robust, no
single-cost cherry-pick. **On the artifacts:** the raw `pc_val.json` `verdict` field stays
`VAL_FAIL_redesign_rejected` — it fired the **any-finalist DISCLOSURE** rule (a code mis-wiring of
§P4.2, whose *binding* rule is top-1) on the **invalid stream-cost net axis**; it is superseded by
`pc_val_injected.json`. A per-symbol **exact** machine number still needs operator-supplied
`spread_pips`.

### Frozen-procedure defect (closed in P5)

Stream `cost_bps` under-charged net on engine-costless emissions. **P5 fix:** inject flat
**1.0 bps** RT on the net path only (predeclared §P5; new registry pin).

### Verdict + recommendation (P4 archive → P5)

P4 left route withheld. **P5 completed the mandate.**

---

## P5 — Net inject + re-VAL + route-restore

| Item | Value |
|---|---|
| Injected RT | **1.0 bps** flat (operator conservative floor) |
| Binding | top-1 `net_LCB > 0` after inject; gross costless; all-finalist = disclosure |
| Registry v2 | sha256 `db87dc1a…` · parent P4 `44e1aa3c…` → `pc_frozen_registry_p4.json` |
| Re-VAL | `pc_val_p5.json` → **`VAL_PASS`** |

| Fixture | gross_LCB | net@1.0 | Deployable |
|---|---:|---:|---|
| 001 | −0.249 | −1.137 | no |
| 002 | −0.248 | −1.221 | no |
| 003 | **+1.077** | **−0.085** | no |

**Route RESTORED** under this pin. Do not re-run (c) confirm (α-shopping); do not read holdout.

### Deliverables (P4 + P5)

| | |
|---|---|
| §P4 / §P5 | `design.md` |
| Harness | `analysis_code/run_pc_val.py` (`--p5`) |
| Live registry | `results/pc_frozen_registry.json` (v2) |
| P4 archive | `results/pc_frozen_registry_p4.json` |
| P5 re-VAL | `results/pc_val_p5.json` |

---

## Deliverables

| | |
|---|---|
| §P-BF predeclaration + K amendment | `design.md` |
| Perm harness | `xen.xena.calibration_pbf`, `score.mean_per_leg_bps` |
| Design (STOP) | `results/pbf_design.json` |
| Confirm | **not produced** (correct under design STOP) |
| Quarantine | `results/pbf_design_pre_amendment_K99ref.json` |
| Log salvage | `results/pbf_run.log` |

**Handoff: P-BF DESIGN STOP → recommend exit (c); P4 blocked; XENA route remains SUSPENDED.**
