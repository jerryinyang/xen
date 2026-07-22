# QA review — INFR-015

## QA run 1 — 2026-07-17T05:15:21Z — mode: subagent — HEAD 89fb4fef7b2dfdf68759ed86033a4d6b8adea1a7
Reviewed state: design.md only (pre-implementation design review; no code/results exist).
Dirty files: `python/experiments/INFR-015/` (untracked — the design under review).

Verdict: **REVISE** (design defects — route to quant-designer; all are text-level amendments, no re-scoping)

### Design-fidelity trace (design vs cited artifacts — no code exists yet)

| Design clause (§ref) | Evidence (file:line) | Verdict | Notes |
|---|---|---|---|
| §1.1 low: cov 0.100, α̂ 0.075, inflation −0.025, `coverage_limited` | INFR-014/results/confirm_CLS-EPISODE.json:49-68 | MATCHES | no_search_cov 0.1, e2e_alpha 0.075, selection_inflation −0.025 (float −0.02500000000000001), failure_label coverage_limited, n=200 |
| §1.1 high: cov 0.050, α̂ 0.080, inflation +0.030, `selection_unsafe` | confirm_CLS-EPISODE.json:74-93 | MATCHES | exact; n=200 |
| §1.1 seeds 93000/94000, n=200/cell | confirm_CLS-EPISODE.json:4-7, per_cadence.n | MATCHES | |
| §1.1 CLS-FILTER contrast cov 0.035/0.065, α̂ 0.045/0.060 | confirm_CLS-FILTER.json (recomputed) | MATCHES | low 0.035/0.045, high 0.065/0.060, n=200 |
| Header: INFR-014 pin sha256 `ac8a1eb6…` | registry_verify.json (`ok: true`, sha256 ac8a1eb679e2…, schema xena.infr014.bybit_pc_registry.v1) | MATCHES | NOTE: this is the canonical/recorded sha, not the raw file sha of `bybit_pc_frozen_registry.json` (1c927b05…). See Issue 5. |
| §1 mechanism: one shared path per candidate, sorted entries, lognormal durations median 4h/1h cap 48h, overlap | calibration_bybit.py:248-303 | MATCHES | rng.lognormal(mean=log(median_h), sigma=0.6) clipped to [1/60, 48]; entries `np.sort(rng.choice(..., replace=False))` on one `regime_gbm_path`; hold_bars up to 2880 1m-bars with entry gaps that can be 1 bar ⇒ heavy overlap ⇒ cross-leg P&L correlation under the null. Mechanism claim is consistent with the generator. Attribution caveat: see Issue 3. |
| §3 "everything else unchanged" constants | confirm_CLS-EPISODE.json procedure:8-42 | MATCHES | two_stage_sample_split, g_net+charge_costs, embargo 0.2, fracs 0.5/0.25, n_boot 200, conf 0.95, α 0.05, one_subset, held_out_escalation false, gross-LCB α̂ event, net deployability separate, cost_stack bybit_round_trip_cost_bps_v1 — all match the pinned procedure; only block_legs changes (1 → episode_overlap_rule_v1) |
| §4 generator reused byte-identical, n_cand 64 | calibration_bybit.py:248-316 | MATCHES | default n_candidates=64; `factory_fingerprint` exists (line 306) — design's EQUALITY assert vs INFR-014 is the correct inverse of the §4.1 inequality assert |
| §5 CAL-FPR n_null scaling | SE formula check | MATCHES | 0.218/√200 = 0.0154; 0.218/√80 = 0.0244; matches √(.05·.95/n). Gate on point α̂ (not UCB), Wilson disclosure-only — complies with the CAL-FPR rule |
| §5 seed freshness/disjointness | INFR-014 design.md:202 (bite 951000/952000), confirm json (93000/94000), procedure.design_seeds (91000/92000) | MATCHES | 95000/96000, 97000/98000, 953000/954000 are disjoint from 91k–94k(+0..199), 951k/952k, and ch03 banks (71k/72k, 81k/82k, 791k/792k). Internal note: 95000-bank offsets top out at 95199 < 951000 — no collision with the new bite banks either |
| §3 single form change, deterministic, not a knob | §3 text | MATCHES (with defects) | One change (resampling unit); B(stream) is a deterministic function of the stream's own timestamps, frozen at QA, no α/n_boot/confidence/frac motion. However the rule TEXT as written is not fully deterministic — Issues 1 and 2 |
| §5.3-of-014 lineage ("predeclared binder-form switch") | INFR-014 design.md:206-213 | MATCHES | "One clean cycle before binder-form change… binder-form change requires NEW design.md" — INFR-015 is exactly that |
| §11 amendment policy | §11 text vs governance | MATCHES | CLS-FILTER byte-identical carry-over; TERMINAL-2 ⇒ no write, pin ac8a1eb6 stands; superseded_pins appended; INFR-014 report/indexes not rewritten |

### Golden-trace diff (hand-checked from design text; no implementation exists)

| Event | Expected (from design) | Hand-check | Verdict |
|---|---|---|---|
| G1 uncapped | durations [2,4,8,16]h ⇒ q90 = 13.6, gaps 1h ⇒ B = ceil(13.6/1.0) = 14 | q90 = 13.6 only under linear-interpolation quantile (numpy default); "higher"/"nearest" methods give 16. ceil and cap arithmetic correct: floor(40/4)=10 ⇒ B=10 | ARITHMETIC CORRECT, method unpinned (Issue 2) |
| G1 capped | n_legs=40 ⇒ cap floor(40/4)=10 ⇒ B=10 | 10 ✓ | MATCHES |
| G2 degenerate | single leg ⇒ B=max(1,…)=1, bit-for-bit equal to block_legs=1 | Rule as literally written: cap floor(1/4)=0 conflicts with max(1,…) — order of operations unstated (Issue 1). Bit-for-bit equality additionally requires B=1 to route through the identical RNG path (Issue 4) | AMBIGUOUS |
| G3 seed assert | confirm-coverage run with design seed bases raises IntegrityError | Correct Issue-9-class regression, re-pinned to 015 constants (95000/96000 vs CONFIRM 97000/98000) | MATCHES |

### Governance & boundary

| Check | Status | Evidence |
|---|---|---|
| Mechanism statement | PRESENT | §1 MECHANISM block with DERIVED estimand/null/horizon/test |
| Object identity | PRESENT (N/A with reasons) | §2 — infrastructure CAL, synthetic banks; design/confirm disjointness declared |
| Control validity proofs | PRESENT | §6 — no-search-coverage (B-1 disjoint decision path, MDE >3 SE at the observed defect size 0.10 vs 0.05), bite-plant power control with anti-overcorrection exit (select <0.5 ⇒ Fork B TERMINAL) |
| Tripwire | PRESENT (HARD, integrity class) | §6 TRIPWIRE — seed-disjointness + coverage-arm seed asserts; vacuity argued (caught Issue-9 class); P&L-leak tripwires correctly N/A on synthetic banks |
| Bands (no binaries) | PRESENT | §7 per-cadence lattice incl. NEAR-MISS and UNPOWERED |
| Power statement | PRESENT & correct | §8 — SE 0.0154, 2-SE detectability 0.081, honest disclosure that a repeat 0.075/0.080 failure sits at 1.6–1.9 SE (NEAR-MISS risk); UNPOWERED distinctions predeclared |
| Golden trace | PRESENT (developer must not generate) | §9 — see diff above |
| Hard/informative split | PRESENT | §10 |
| CONVERSION-PIN (L-21) | N/A with reason | §12 — no screen→money conversion. Valid |
| SPREAD-SCALE-ROUTING (T1) | N/A with reason | §12 — synthetic banks, no verdict-bearing T1 read. Valid |
| Spread verdict leg (L-22) | N/A with reason | §12 — no SUPPORTED/tradability band in a CAL; cost stack enters only via g_net (matches pinned `bybit_round_trip_cost_bps_v1`). Valid |
| Amendment ledger (L-23) | PRESENT | §12 — running count 0L/0T/0N |
| L-28 derangement | N/A with reason | end of §6 — no permutation destroy; deplant is band removal (P-C form). Valid |
| L-31 one node/process | N/A at design stage | No BacktestNode involved (synthetic CAL); flag to developer regardless if any parallel cell runner is added |
| L-24 battery/eligibility clauses | NOT EXPLICITLY ADDRESSED | Multi-cell (2 cadences) capped-read design; read floors (n=200) and derived tripwires are effectively covered, but no explicit §13/L-24 declaration or N/A. Issue 6 (Info) |
| Iterated-calibration discipline | COMPLIES | design/confirm bank split, fresh disjoint seeds, single form change, no optional stopping, one-clean-cycle STOP rule (§5, §13) |
| CAL-FPR n_null scaling / point-α̂ gate | COMPLIES | §5, §7, §10 |
| XENA VOID on new stack (INFR-010 R4) | COMPLIES | Amends the post-CAL hash-pinned Bybit registry (ac8a1eb6, operator-accepted); ch03 pin db87dc1a stays VOID |
| Registry amendment policy | SOUND | §11 — byte-identical CLS-FILTER carry-over with before/after verify (§10 HARD), TERMINAL ⇒ no write, supersession appended, INFR-014 artifacts not rewritten, pin acceptance stays operator-gated |
| Holdout | UNTOUCHED | Synthetic banks only; §12 declares |
| No local accounting / no Python backtest | N/A | No code yet; re-check at QA run 2 |
| DEVIATIONS block | NONE | — |

### Issues

1. **MEDIUM (design, §3 + §9 G2) — B-rule cap degenerate for small n_legs; order of operations unstated.** `B = max(1, ceil(q90/median_gap))`, "capped at floor(n_legs/4)": for n_legs ≤ 3 the cap is 0, contradicting `max(1, …)` (and G2's expected B=1). ~10–15% of INFR-014 confirm rows have n_legs ≤ 3 (plus n_legs=0 empties), so this branch WILL be hit. Required change: restate the rule as `B = min( max(1, ceil(q90/median_gap)), max(1, floor(n_legs/4)) )` (or equivalent), and state B for empty/single-leg streams explicitly. Route: quant-designer (frozen-rule text must be unambiguous before code exists).
2. **MEDIUM (design, §3 + §9 G1) — quantile/median estimators unpinned.** G1's 13.6 presumes linear-interpolation q90 (numpy default); "higher"/"nearest" give 16. Same for `median(inter_entry_gap_h)` (even-count interpolation; gap definition entry-to-entry vs entry-to-exit is stated as entry timestamps — keep, but pin it). Required change: pin the quantile method (e.g. `np.quantile(..., method="linear")`) and the gap definition in the §3 rule text. The rule is the freezable object; an ambiguous rule leaves a post-freeze degree of freedom to the implementation.
3. **MINOR (design, §1.1) — mechanism attribution overstated for high cadence.** The artifact shows high-cadence coverage_ok=true (cov 0.050 exactly at target, label `selection_unsafe`, inflation +0.030); "primary failure = base LCB coverage" is grounded on low only. Blocking plausibly still fixes high α̂ (wider LCBs shrink the selected-max exceedance), but the design should disclose that on high the fix acts through the selection channel, and that a high-cadence CERTIFY/FAIL is a weaker test of the stated overlap mechanism. One-line disclosure amendment (NEUTRAL); non-blocking.
4. **MINOR (design, §9 G2) — "bit-for-bit" equality at B=1 is an implementation constraint, not a free property.** A circular-block resampler with B=1 equals the legacy `block_legs=1` draw only if the RNG consumption path is identical. Either require the implementation to route B=1 to the unchanged legacy code path, or relax G2 to numerical equality with a stated tolerance. Flag for experiment-developer at implementation.
5. **MINOR (design, header/§11) — pin hash provenance should be pinned to the verify method.** `ac8a1eb6…` is the canonical sha recorded in `registry_verify.json`/inside the registry, not the raw file sha of `bybit_pc_frozen_registry.json` (1c927b05…). §11's "byte-identical CLS-FILTER / new sha256 recorded" must state it uses the same canonicalization as `verify_bybit_registry`, else the before/after byte-identity check can false-fail or false-pass. Clarification only.
6. **INFO (design, §12) — L-24 battery clauses not explicitly declared.** Multi-cell capped-read design; read floor (n=200 ⇒ UNPOWERED) and derived tripwires are present in substance, but add an explicit L-24 N/A-or-covered line for completeness.

### Disposition
REVISE — Issues 1 and 2 must land as design-text amendments (both NEUTRAL: they remove ambiguity, moving no gate) before implementation starts; Issues 3–6 are disclosure/clarity and implementation flags. No governance violations, no seed reuse, no holdout contact, amendment policy sound, arithmetic and artifact quotes verified. Re-run QA (run 2) after amendments + implementation for the fidelity trace against code.

## QA run 2 — 2026-07-17T05:25:43Z — mode: subagent — HEAD 89fb4fef7b2dfdf68759ed86033a4d6b8adea1a7
Reviewed state: amended design.md + implementation (`python/src/xen/xena/calibration_bybit15.py`,
`python/tests/test_xena_infr015.py`, `python/experiments/INFR-015/code/run_cal15.py` — all untracked/new).
Dirty tracked files: NONE. **Frozen INFR-014 harness `calibration_bybit.py` UNTOUCHED** (git status clean;
`git diff HEAD -- calibration_bybit.py` empty).

Verdict: **APPROVE** (ready for the operator execution gate; Issues 7–9 are non-blocking MINOR/INFO)

### Run-1 issue resolution

| # | Run-1 issue | Resolution | Verdict |
|---|---|---|---|
| 1 | MEDIUM B-rule cap order-of-ops degenerate | §3 restated `B = min(max(1,ceil(q90/med_gap)), max(1,floor(n/4)))`, single-leg/zero-gap ⇒ 1 (AMENDMENT-1). Code `calibration_bybit15.py:104-106` implements exactly; G1b test asserts B≥1 at n=3 | RESOLVED |
| 2 | MEDIUM quantile/median unpinned | §3 pins `numpy.quantile(…,0.9,method="linear")`, `numpy.median`, gaps from consecutive sorted EntryTime (AMENDMENT-2). Code lines 95-103 match verbatim | RESOLVED |
| 3 | MINOR HIGH-cadence selection-channel disclosure | §1.1 final bullet added (NEAR-MISS predeclared, read per §7) | RESOLVED |
| 4 | MINOR G2 bit-for-bit needs legacy routing | §9 G2 amended; code routes B==1 to unmodified `eval_lcb_legs(block_legs=1)` (lines 130-134) — same evaluate/seed+99/LCB_CONF path, bit-for-bit by construction; test asserts lcb/point equality | RESOLVED |
| 5 | MINOR canonical-sha language | §11 pins identity checks to `verify_bybit_registry` canonicalization; `amend_registry_episode` compares CLS-FILTER via canonical JSON (`_canon`, sort_keys) and re-hashes the same way as `write_bybit_registry` | RESOLVED |
| 6 | INFO L-24 line | §12 explicit L-24 N/A-with-reason added | RESOLVED |

Amendment ledger: 3 amendments, all NEUTRAL, count 0L/0T/3N — no directional streak; correctly recorded in §12.

### Design-fidelity trace (code vs amended design)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3 B rule (pinned text) | calibration_bybit15.py:86-106 | MATCHES | min/max order, linear quantile, np.median, sorted-EntryTime gaps, n≤1 ⇒1, zero/degenerate gap ⇒1; extra guard drops non-finite/≤0 durations then B=1 if none remain (conservative, degenerate-only) |
| §3 B==1 legacy routing (G2) | :130-134 | MATCHES | routes to untouched `eval_lcb_legs` with block_legs=1; identical seed offset (+99), LCB_CONF=0.95 |
| §3 B>1 path wiring | :136-142 vs calibration_p3d.py:74-81 | MATCHES | same evaluate(cfg replace charge_costs), `lcb_g_leg_studentized(seed+99, confidence=0.95, block_legs=b)`; n_admitted attached |
| B population = bootstrap population | :121-127 vs score.py:250-272 | MATCHES | B from `ledger.sort("EntryTime")` entry/exit pairs; bootstrap resamples same ledger rows via `ledger_leg_arrays` stable argsort(EntryTime) — same legs, same time order; circular blocks over time-ordered legs (score.py:290-298) match the overlap mechanism |
| §3 everything-else-unchanged | run_two_stage_ep :148-205 vs calibration_bybit.py:334-398 | MATCHES | line-for-line mirror: g_net stage-1, charge_costs=True, budget/restarts/folds/purge, seed & seed+17, gross α̂ event + net deployability; only stage-2 estimator call swapped |
| §3 stage-1 hard refuse | :159 `assert_stage1_net_binding` | MATCHES | reused from frozen harness |
| §4 generator unchanged, imported | :51 import `make_episode_null_universe` from calibration_bybit | MATCHES | imported, not copied; frozen file untouched ⇒ byte-identical by construction; n_cand 64 via ScaleSpecs |
| §5 seeds 95k/96k, 97k/98k, 953k/954k | :64-66 | MATCHES | disjointness assert :211-226 covers INFR-014 (91k-94.5k, 951k/952k) + ch03 (71k/72k/81k/82k/791k/792k) ranges; widths (500/50) cover actual usage (max offset 199/49) |
| §5 n_null 80/200, no knob motion | :68-71 vs calibration_bybit.py:56-59 | MATCHES | ScaleSpecs numerically identical to INFR-014 DESIGN/CONFIRM_SCALE |
| §5 fixed n / no optional stopping | confirm_gate_ep :456-458 | MATCHES | binding confirm n_null hard-pinned to 200 |
| §5/§9 G3 coverage-arm seed assert | :467-470, :475-477 | MATCHES | guards both coverage and e2e seed_bases == CONFIRM_SEEDS_15 |
| §6 no-search coverage control | no_search_coverage_ep :271-304 vs calibration_bybit.py:491-539 | MATCHES | same rng seed+91, subset 5, charge_costs=True config, coverage_ok ≤ α; blocked LCB via eval_lcb_legs_ep |
| §6 bite-plant control | bite_check_ep :232-268 vs calibration_bybit.py:404-460 | MATCHES | same deplant chain (deplant_stage2 + _deplant_class_plants), thresholds ≥0.5 / ≤0.125, BITE_N=8, edge 20 bps; bite FAIL ⇒ design_ok=False TERMINAL (run_design_ep :365-375) |
| §7 bands / verdict lattice | confirm_gate_ep :479-498, `_outcome` reused | MATCHES | point-α̂ gate, Wilson disclosure-only, selection_inflation reported |
| §10 HARD: confirm refuses wrong form | :445-448 | MATCHES | `block_legs != "episode_overlap_rule_v1"` ⇒ IntegrityError |
| §11 write policy | amend_registry_episode :549-555 | MATCHES | non-certifiable verdict ⇒ IntegrityError, pin stands (TERMINAL-2) |
| §11 CLS-FILTER byte-identical | :562-565, :596-598 | MATCHES | canonical-JSON before/after assert; block carried over from deepcopy of verified old registry |
| §11 superseded_pins append; verify after write | :592-594, :600-605 | MATCHES | appends old canonical sha `ac8a1eb6…`; `verify_bybit_registry` green required post-write |
| §11 pin_usage/void_priors unchanged | deepcopy carry-over; verify enforces | MATCHES | new block keys ⊇ INFR-014 block keys + `amended_by`; verify schema checks pass |
| §13 Fork B / TERMINAL-2 runner | run_cal15.py:34-63 | MATCHES | design fail ⇒ summary+return (no confirm); amend refusal caught ⇒ pin_amended=False; summary always written |
| Forbidden-list scan | whole diff surface | CLEAN | no new knobs, no seed reuse, no optional stopping, no chapter-03 pin load, no g_net→gross swap, no local accounting (`check_no_local_accounting` ok:true), no Python backtest, no BacktestNode (L-31 N/A) |

### Golden-trace results

| Trace | Expected (design) | Result | Verdict |
|---|---|---|---|
| G1 | q90 linear [2,4,8,16]=13.6 ⇒ ceil=14; n=40 cap 10 ⇒ B=10 | `test_g1_block_rule_fixture` PASS (asserts b==10; 4-leg fixture capped at 1) | MATCHES |
| G1b | n_legs=3 ⇒ cap max(1,0)=1 ⇒ B=1 | `test_g1b_cap_degenerate_never_zero` PASS | MATCHES |
| G2 | B==1 bit-for-bit vs legacy | `test_g2_b1_routes_to_legacy_bitwise` PASS; QA independently confirmed the fixture takes the B==1 branch (block_legs_used=1, n_legs=6) so the lcb/point equality asserts executed | MATCHES |
| G3 | confirm coverage on design bases ⇒ IntegrityError | Runtime guard verified LIVE by QA sabotage run (neutralized `_set_seeds`, preset 95000/96000 ⇒ `IntegrityError: confirm coverage seed_bases {…95000…} != CONFIRM_SEEDS_15`). Unit test covers the wrong-block-rule refusal instead of the literal seed sabotage (Issue 8) | MATCHES (guard live) |

Test run: `uv run pytest tests/test_xena_infr015.py tests/test_xena_infr014.py -q` → **20 passed**.

### Governance & boundary

| Check | Status | Evidence |
|---|---|---|
| Frozen INFR-014 harness untouched | PASS | git clean; only new untracked files; imports (not copies) from calibration_bybit |
| check_no_local_accounting(experiments/INFR-015/code) | PASS | ok:true, no banned defs |
| No Python strategy backtest | PASS | synthetic CAL only |
| Seed disjointness (HARD tripwire) | PASS | assert_seed_disjoint_15 covers 014+ch03; `test_seed_disjointness` green |
| Iterated-calibration discipline | PASS | design→confirm once; confirm scale pinned; forbidden list embedded in stop_condition |
| L-21/L-22/T1/L-24/L-28/L-31 | N/A with reasons (design §12/§6) — unchanged from run 1, still valid | |
| XENA VOID (R4) | PASS | amends post-CAL Bybit pin; no ch03 pin path exists in new module |
| Holdout | UNTOUCHED | synthetic banks only |
| Registry amendment policy | PASS | write policy, canonical identity, supersession, post-write verify all implemented |
| DEVIATIONS block | NONE | — |

### Issues (new, from 7)

7. **MINOR (implementation, calibration_bybit15.py:600-605 + run_cal15.py:51-61) — post-write verify failure leaves an invalid file on disk.** `amend_registry_episode` writes the artifact then verifies; if `verify_bybit_registry` raised after the write, the bad registry would remain in results/ while `run_cal15` catches the IntegrityError and records `pin_amended=False` — the same field that encodes a legitimate TERMINAL-2 refusal. Suggested (post-approval hygiene, not gating): write to temp + rename after verify, and record the refusal reason distinctly from a verify failure (the current `write_refusal` string does carry the message, so the artifact trail is auditable).
8. **MINOR (tests, test_xena_infr015.py:89-100) — G3 unit test does not exercise the literal seed sabotage.** It tests the wrong-block-rule refusal; the seed-bases guard itself was verified live by QA's sabotage run (recorded above). Suggested: add a monkeypatch-based regression test (neutralize `_set_seeds`, preset design bases) so the Issue-9-class guard stays covered without a QA rerun.
9. **INFO (tests + dead code) — no automated test drives `eval_lcb_legs_ep` with B>1 end-to-end** (the rule function is G1-tested; the B>1 wiring was verified by inspection: same res, seed+99, confidence 0.95, block semantics in score.py:290-298 are circular blocks over time-ordered legs as designed). Also `_pnl, _notional, et = ledger_leg_arrays(...)` at calibration_bybit15.py:121 is unused computation (`del et`) — harmless, no behavioral effect.

### Disposition
APPROVE — all six run-1 issues resolved in the amended design and faithfully implemented; frozen harness untouched; golden traces G1/G1b/G2 pass and the G3 guard is demonstrated live; governance clean. Issues 7–9 are non-blocking hygiene items the operator may queue post-execution. Execution remains operator-gated.

## QA run 3 — 2026-07-17T05:47:58Z — mode: subagent — HEAD 89fb4fef7b2dfdf68759ed86033a4d6b8adea1a7
Verdict: **APPROVE** (post-execution faithfulness + governance review; APPROVE means artifacts and analysis.md are faithful and governance held — it does NOT certify CLS-EPISODE, which is TERMINAL-2 / uncertified)

Dirty state at review: untracked `python/experiments/INFR-015/`, `python/src/xen/xena/calibration_bybit15.py`, `python/tests/test_xena_infr015.py` (the experiment itself; frozen files clean).

### Number verification (analysis.md vs raw artifacts — all recomputed independently)

| Claim (analysis.md) | Artifact | Recomputed | Verdict |
|---|---|---|---|
| DESIGN cov low 0.0375 / high 0.0500 (n=80, seeds 95k/96k) | design_CLS-EPISODE.json coverage | 3/80=0.0375; 4/80=0.0500; seed_bases {95000,96000} | MATCHES |
| Bite low survival 0.125 / select 0.875; high 0.000 / 1.000; PASS | design bite block | 0.125/0.875, 0.000/1.000, bite_ok both true | MATCHES |
| CONFIRM low cov 0.095, α̂ 0.135, inflation +0.040, FAIL_ALPHA selection_unsafe | confirm + cal15_summary per_cadence.low | cov rows 19/200=0.095; gross_pass 27/200=0.135 (= n_gross_lcb_positive 27) | MATCHES |
| CONFIRM high cov 0.050, α̂ 0.055, inflation +0.005, Wilson [0.031, 0.096], SE 0.016 | per_cadence.high | 10/200=0.050; 11/200=0.055; wilson [0.0310, 0.0958]; SE 0.0161 | MATCHES |
| NEAR-MISS read on HIGH (0.055 ≤ 0.05 + 1·SE) | design.md §7 band def (line 163) | 0.05+0.0161=0.0661 ≥ 0.055; band correctly still NOT certified | MATCHES |
| Slice: n_legs<8 pass 0.179 on 67 rows | alpha_low_rows | 12/67=0.1791 | MATCHES |
| Slice: n_legs 8–15 → 0.101 on 89 | alpha_low_rows | 9/89=0.1011 | MATCHES |
| Slice: n_legs 16–49 → 0.136 on 44 | alpha_low_rows | 6/44=0.1364 (no rows ≥50) | MATCHES |
| B=1 → 0.179 on 67; B=2–4 → 0.098–0.139 on 125 | alpha_low_rows | B=1 0.1791/67; B=2 0.1053/38, B=3 0.0980/51, B=4 0.1389/36 (Σ125) | MATCHES |
| Median top-1 n_legs LOW = 11; HIGH median 261, B 12–30 median 23 | alpha rows | 11.0; 261.0; B min 12 / med 23 / max 30 | MATCHES |
| Bank-to-bank Δ ≈ 2.4·SE₈₀ (0.0375 vs 0.095) | — | SE₈₀=√(.05·.95/80)=0.0244; Δ/SE=2.36 | MATCHES |
| INFR-014 baseline: HIGH 0.080→0.055; LOW 0.075→0.135; INFR-014 LOW cov 0.100 | INFR-014 cal_summary.json CLS-EPISODE | low α̂ 0.075 / cov 0.100; high α̂ 0.080 / cov 0.050 | MATCHES |

### Seed integrity (Issue-9 class)
- Confirm coverage rows: seeds 97000–97605 (low), 98000–98605 (high). Confirm alpha rows: same bases. `per_cadence.*.seed_bases` = {low: 97000, high: 98000} in both coverage and alpha records — PASS.
- No 95k/96k (design) or 91k–94k (INFR-014) seeds in any confirm row — PASS.
- Runtime guard present and binding: `assert_seed_disjoint_15` (calibration_bybit15.py:211) + confirm-gate seed_bases asserts (lines 467–477, explicitly citing G3/Issue-9).

### Write policy & frozen-pin verification
- No `bybit_pc_frozen_registry.json` in INFR-015/results (directory listing) — write refused; `cal15_summary.json` records `pin_amended: false` + explicit `write_refusal` string — PASS.
- INFR-014 pin re-verified live via `xen.xena.calibration_bybit.verify_bybit_registry`: passes; stored sha256 `ac8a1eb679e22290d854ad245ef1620f5f8bdb446a5c0166c618d0c292b2da6f`, independently recomputed over canonical registry blob — identical. Pin stands (CLS-FILTER LOW_ONLY_CERTIFY, CLS-EPISODE certified:false) — PASS.
- Frozen harness `python/src/xen/xena/calibration_bybit.py`: clean in git status, no diff vs HEAD — PASS.

### No retune / optional stopping
- n=200 per confirm cell in artifacts; design n=80; both match declared plan. Single design→confirm sequence in cal15_run.log with numbers matching JSON artifacts. `stop_condition.forbidden` present with the full list incl. "no retune on this confirm data (TERMINAL-2 => new design)" — PASS (see Issue 11 caveat).

### Governance
- No family transitions, no counted TEST reads, no holdout contact (synthetic CAL banks only; no price emission).
- No chapter-03 pin load: only registry references in run_cal15.py are the INFR-014 pin path (read/verify) and the refused write target; `forbidden` list includes "no chapter-03 pin". VOID priors (db87dc1a, 537d691a) listed in the verified registry — PASS.
- Follow-up candidates in analysis §5 correctly framed as NEW designs, not amendments to this confirm.

### Story-vs-proven audit (analysis §2–§3)
- "HIGH improvement 0.080→0.055" — numbers correct; analysis appropriately hedges (NEAR-MISS, 1 SE of target, still FAIL_ALPHA/uncertified). Note the two runs use different seed banks and n=200 each (SE≈0.016–0.019), so the 0.025 improvement is ~1σ of the difference — analysis calls it "partial effect", not proven; acceptable framing.
- "LOW worse 0.075→0.135" — correct; same cross-bank caveat applies but the analysis itself flags LOW instability across banks (0.0375 design vs 0.095 confirm, 2.4·SE) — consistent.
- "Small-n_legs diagnosis" — supported: worst cell is exactly B=1/n_legs<8 (0.179), and B=1 ⇔ n_legs<8 exactly (identical 67 rows). Analysis correctly labels overlap "REAL but secondary on LOW" and does report the non-monotone 16–49 slice (0.136 > 0.101) rather than hiding it. No story-beyond-evidence found.

### Issues (numbered from 10)
10. **INFO (calibration_bybit15.py:211-218) — seed-disjointness window narrower than actual consumption.** `assert_seed_disjoint_15` reserves base+500 per bank, but confirm rows consumed seeds up to base+605 (empty-draw skipping). Empirically still disjoint (97605 < 98000; 98605 below all prior ranges), so no contamination occurred — widen the window to +1000 in any successor harness.
11. **INFO (results/cal15_run.log:1) — stray `tee: … No such file or directory` line at log head.** Indicates an initial invocation attempted before the results directory existed. The retained log contains one complete design→confirm sequence whose numbers match the JSON artifacts, and all banks are seed-deterministic, so a repeat would be bit-identical — no optional-stopping evidence. Operator should confirm no earlier completed confirm run was discarded.
12. **INFO (cal15_summary.json vs analysis.md) — LOW `deployability_rate` 0.095 reported in artifact but not discussed in analysis.** Net-pass rate on LOW nulls (0.095) is itself elevated vs the 0.05 target; immaterial to the TERMINAL-2 verdict (gross α̂ already fails) but worth carrying into any follow-up design.

### Disposition
APPROVE. All analysis.md numbers reproduce from the raw artifacts; per-slice table recomputed exactly; seed integrity holds on confirm bases 97000/98000 with no design contamination; write policy held (no registry write, INFR-014 pin ac8a1eb6… re-verified live); frozen harness untouched; no retune/optional stopping; governance clean. Outcome TERMINAL-2 stands: CLS-EPISODE remains uncertified; XENA-EPSOSC stays blocked. Issues 10–12 are informative only.

## QA run 4 — 2026-07-17T10:55:41Z — mode: subagent — HEAD ec87269012ed7dbed60dee4486dc2d1c77c160cc
Reviewed dirty state: design.md (+§14 append), report.md (§7/§8 update), calibration_bybit15.py (pure append, verified via git diff), test_xena_infr015.py (+A4 tests), new code/run_cal15_a4.py.
Scope: pre-execution review of AMENDMENT-4 (design §14 + implementation). Runs 1–3 stand unmodified.

Verdict: **REVISE** — one material defect on the CERTIFY write path (Issue 13); all other clauses MATCH.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §14 direction TIGHTER, ledger 0L/1T/3N | design.md:253-257 | MATCHES | Floor can only remove certifications; ledger arithmetic correct; no streak ≥3 in one direction (3N+1T) |
| §14 deviation from §13 authorized | report.md:95-105 (operator verbatim) | MATCHES | Operator TERMINAL-2 approval + directed amendment recorded verbatim; spent banks never reused |
| §14.1 floor via existing `n_legs_floor` param | score.py:306-350; calibration_bybit15.py:641-668 | MATCHES | `n_legs < floor ⇒ in_domain=False ⇒ pass_positive=False`; LCB itself unchanged by the floor (score.py:325-347), so floor-ON pass ≡ floor-OFF pass ∧ n_legs ≥ F — the §14.2 monotone-filter equivalence is exact |
| §14.1 block rule kept | calibration_bybit15.py:654-663 | MATCHES | Same `episode_overlap_block_legs` routing; `eval_lcb_legs_ep_floor` calls `lcb_g_leg_studentized(seed+99, block_legs=b, confidence=0.95)` even at b==1 — bit-identical to the legacy `eval_lcb_legs` path (p3d:74-81, LCB_CONF=0.95, same seed offset), so G2 identity is preserved without the explicit route |
| §14.2 grid predeclared | calibration_bybit15.py:613 `FLOOR_GRID` | MATCHES | (0,4,6,8,10,12,16,20,24,32) verbatim |
| §14.2 one design-bank run, post-hoc filter | run_design_a4:789-810; derive_n_legs_floor:671-710 | MATCHES | Floor-OFF cov+e2e rows collected once (`_bank_rows_ep`); per-floor evaluation is pure counting; filter direction CORRECT: false-certify counted iff `pass ∧ n_legs ≥ F` (cov_rows use `pass`, alpha_rows `gross_pass` — matches emitting row schemas at :293/:325); `n_legs=None→0` conservative |
| §14.2 F* = smallest F passing both gates both cadences; None ⇒ TERMINAL-3 | derive_n_legs_floor:702-704; run_design_a4:805-810 | MATCHES | `chosen` = first all_ok in ascending grid; None returns design_ok=False, terminal, "TERMINAL-3_no_admissible_floor", no confirm |
| §14.2 out-of-domain disclosure | derive:692,699; e2e_alpha_a4:951,958 | MATCHES | ood frac per cadence per floor + at confirm; informative only |
| §14.2 F* frozen before confirm | run_design_a4:844; confirm_gate_a4:970-982 | MATCHES | `n_legs_floor` in frozen procedure; confirm reads it (`fstar = int(procedure["n_legs_floor"])`), never recomputes; forbidden list includes "no floor adjustment after design freeze" |
| §14.3 banks 99k/100k, 101k/102k, 955k/956k | :614-616 | MATCHES | Constants verbatim |
| §14.3 disjoint from ALL prior | assert_seed_disjoint_a4:623-638 | MATCHES | Prior set = INFR-014 (91k–94k+500, 951k/952k+50) + ch03 + `_SPENT_15_RANGES` (95k–98k+500, 953k/954k+50); called in run_design_a4 AND confirm_gate_a4 |
| §14.3 confirm n=200, no optional stopping | confirm_gate_a4:983-984 | MATCHES | Refuses n_null≠200 for scale.name=="confirm"; n fixed by ScaleSpec |
| §14.3 coverage arm asserts CONFIRM-A4 bases | confirm_gate_a4:992-998 | MATCHES | Both coverage and e2e seed_bases hard-asserted == CONFIRM_SEEDS_A4 (Issue-9 class) |
| §14.4 everything else verbatim | frozen dict :829-858 vs :386-422 | MATCHES | binder/stage1/embargo/fracs/n_boot/confidence/alpha/gate rule/α̂ event identical; only additions are n_legs_floor(+rule) |
| §14.4 bite same criteria, floor active | bite_check_a4:728-786; run_design_a4:812-827 | MATCHES | Runs AFTER derivation with F* ON (correct power check — the guard must not kill plant certification); select≥0.5 / survival≤0.125 both cadences; FAIL ⇒ TERMINAL-3, no confirm. See Issue 14 on §14.2 wording |
| §14.4 G4a/G4b/G4c golden traces | tests :126-141, :144-150, :153-167 | MATCHES | G4a: F=8 counts rows (T,8),(T,20) ⇒ 0.5, F=0 ⇒ 0.75 — hand-checked against §14.4 fixture; G4b missing-floor IntegrityError; G4c out-of-domain flags. Expected values from design, not from running the implementation |
| §14.5 exit table | run_cal15_a4.py:49-53,60-70 | MATCHES | TERMINAL-3 paths (no floor / bite fail) write summary and stop before confirm; confirm-fail path: `amend_registry_episode` raises on non-certifiable verdict ⇒ `pin_amended=false` + `write_refusal`, no write |
| §11 write policy reuse | amend_registry_episode:536-606 | DEVIATES | Write policy (refuse non-certifiable, CLS-FILTER canonical-identical, supersede sha) correct — but see Issue 13: A4 path would stamp WRONG seed metadata into a certified pin |

### Golden-trace diff
- G4a fixture (design §14.4): rows {(T,4),(T,8),(F,50),(T,20)} under F=8 ⇒ numerator {row2,row4} = 2/4. `derive_n_legs_floor` counts `gross_pass ∧ n_legs≥8` ⇒ (T,8)✓,(T,20)✓,(T,4)✗,(F,50)✗ = 0.5. MATCHES (test_g4a asserts exactly this).
- G4b: procedure with block rule but no `n_legs_floor` ⇒ IntegrityError at confirm_gate_a4:970-973. MATCHES.
- G4c: `n_legs < F*` ⇒ pass_positive=False, out_of_calibration_domain=True — score.py:325-350 sets exactly these. MATCHES.
- Monotone-filter equivalence (the §14.2 load-bearing identity): verified by code reading that the floor changes ONLY the pass flag, never the LCB/seed/block path; floor-OFF derivation rows therefore predict floor-ON behaviour exactly on the same bank. Confirm then runs floor-ON on DISJOINT 101k/102k banks — no design-row reuse in the binding gate.

### Faithfulness of duplicated stage-1 (e2e_alpha_a4 / bite_check_a4 vs run_two_stage_ep)
Line-by-line diff: same `_search_params(cspec)`, budget/restarts from ScaleSpec, `restart_id=r+1`, `segment=layout.search`, `skip_economics_precondition=True`, `score_kind="g_net"`, 3 contiguous purged folds with `purge_ns=max(hold_bars,1)*60*NS`, `certify_and_rank` flags identical, single top-1, gross seed=seed / net seed=seed+17, stage-2 seed+99 inside. No drift found. Minor: `e2e_alpha_a4` omits the per-call `assert_stage1_net_binding` (it is asserted once in confirm_gate_a4 from the frozen procedure, and g_net/charge_costs are hardcoded) — acceptable, noted.

### Governance & boundary
- Tests: `uv run pytest tests/test_xena_infr015.py tests/test_xena_infr014.py -q` → **25 passed** (12 INFR-015 incl. G4a/G4b/G4c, 13 INFR-014).
- Frozen `calibration_bybit.py` untouched (git clean; last commit 89fb4fe). INFR-014 artifacts clean. `calibration_bybit15.py` diff is pure append after line 604. Prior INFR-015 artifacts unmodified except design §14 append + report §7/§8 operator-record update. run_cal15.py unchanged. New file: run_cal15_a4.py only.
- No accounting primitives in experiment code (runner is orchestration + json dump only); no Python strategy backtest; synthetic banks only — holdout untouched.
- Amendment ledger: L-23 satisfied (0L/1T/3N; TIGHTER declared and correct). Deviation from §13 operator-authorized with verbatim record (report §8) — evidence, not assertion.
- L-28 derangement: N/A (no permutation destroy — deplant is band removal), declared in §6. L-31: N/A (no BacktestNode). CONVERSION-PIN / SPREAD-SCALE-ROUTING / L-22: N/A per §12, reasons valid. XENA frozen-registry clauses: no registry consumed at run time; the only registry touch is the verified INFR-014 pin on the (gated) amend path. No agent-authored attestation anywhere.
- No optional stopping: n fixed by ScaleSpecs; forbidden lists present in both confirm gates.

### Issues (numbered from 13)
13. **MATERIAL (design §11/§14.3 vs calibration_bybit15.py:571-572, run_cal15_a4.py:61-63) — certified A4 pin would record the WRONG seed banks.** `amend_registry_episode` hard-codes `"design_seeds": dict(DESIGN_SEEDS_15)` (95k/96k) and `"confirm_seeds": dict(CONFIRM_SEEDS_15)` (97k/98k) into the class-config block, but the A4 evidence comes from 99k/100k and 101k/102k. The embedded `procedure` dict carries the correct A4 seeds, so a certified pin would be internally contradictory, and top-level seed fields are provenance-bearing (future seed-disjointness reasoning reads pins). Fires only on the CERTIFY path — but that is exactly the path the pin exists for. Required change (experiment-developer): A4-specific amend wrapper (or seed parameters) writing DESIGN_SEEDS_A4/CONFIRM_SEEDS_A4 (and preferably `"amended_by": "INFR-015/AMENDMENT-4"`); one regression test asserting the pin's top-level seeds equal the A4 constants.
14. **MINOR (design §14.2 wording vs run_design_a4:812-827) — bite floor state ambiguous in design text.** §14.2's sentence groups "bite" into the floor-OFF design-bank run, but bite uses its own 955k/956k banks and the implementation runs it with F* ON — which is the mechanistically correct power check (§14.1: guard must not kill plant certification) and the TIGHTER reading. Recommend a one-line §14.2 clarification (DIRECTION: NEUTRAL) at or before the execution gate; not blocking.
15. **INFO (assert_seed_disjoint_a4:624-631) — carry-over of Issue 10.** Reserved windows (+500/+50) remain narrower than worst-case consumption (~+605 observed on confirm banks in the original cycle). A4 bases are 1000 apart and 102k+605 collides with nothing, so disjointness holds empirically; widen to +1000 in any successor harness.
16. **INFO (run_cal15_a4.py:57) — confirm-fail summary verdict label.** On confirm failure the summary records the outcome verdict (e.g. "TERMINAL") plus `write_refusal`, not the literal "TERMINAL-3" of §14.5. Cosmetic; the no-write behaviour is correct.

### Disposition
REVISE — Issue 13 must be fixed (and covered by a test) before execution; it is the only defect that can corrupt the deliverable. Design §14 itself is coherent, predeclared, properly authorized, and F06-compliant; the monotone floor filter is mathematically exact against the shared estimator; seeds are fully disjoint; duplicated stage-1 logic is faithful; all 25 tests pass; frozen harness and prior artifacts untouched. On the Issue-13 fix (plus optional Issue-14 wording), this reviewer expects APPROVE without re-litigating the above.

## QA run 4b — 2026-07-17T11:01:49Z — mode: subagent — HEAD ec87269012ed7dbed60dee4486dc2d1c77c160cc
Verdict: **APPROVE**

Scope: fix-verification of run-4 Issues 13-16 only (per run-4 disposition, run-4 MATCHES clauses not re-litigated).

### Fix-verification table

| Issue | Fix claimed | Verified | Evidence |
|---|---|---|---|
| 13 (MATERIAL) | Seed params + provenance guard in `amend_registry_episode` | FIXED | calibration_bybit15.py:536-560 — `design_seeds`/`confirm_seeds`/`amended_by` params (defaults = 15-era 95k-98k); guard at :557 raises IntegrityError when params != `design["frozen_procedure"]` seed fields. Guard fires at :557, BEFORE first file I/O (`verify_bybit_registry` at :569) — confirmed by code order and by test using `/nonexistent` paths. Pin block now stamps passed-in seeds (:583-584) + `amended_by` (:599) |
| 13 — A4 runner | run_cal15_a4.py passes A4 seeds | FIXED | run_cal15_a4.py:66-67 — `design_seeds=DESIGN_SEEDS_A4, confirm_seeds=CONFIRM_SEEDS_A4, amended_by="INFR-015/AMENDMENT-4"`; A4 frozen dict carries A4 seeds (:862-863), so guard passes on CERTIFY path and pin top-level seeds == procedure seeds structurally |
| 13 — original path | run_cal15.py defaults still correct | VERIFIED | run_cal15.py:52-54 — no seed params → defaults `DESIGN_SEEDS_15`={95k,96k}/`CONFIRM_SEEDS_15`={97k,98k} (:64-65); `run_design_ep` frozen dict includes matching `design_seeds`/`confirm_seeds` (:411-412), so guard passes for a 15-era frozen procedure |
| 13 — regression test | test_issue13_pin_seed_provenance_guard | PRESENT | tests/test_xena_infr015.py:183-193 — A4 frozen procedure + default (15-era) params ⇒ IntegrityError; nonexistent paths prove pre-I/O firing. Note (INFO): no positive-path test asserting a written pin's top-level seeds, but the guard makes pin-seeds != procedure-seeds unreachable, satisfying run-4 intent |
| 14 (MINOR) | design §14.2 bite-floor-ON wording | FIXED | design.md:276-277 — "bite then runs with F* ON (power must survive the guard — QA run 4 Issue 14 clarification)"; matches code (run_design_a4 :824-827, `bite_check_a4(..., n_legs_floor=fstar)`). DIRECTION: NEUTRAL (wording only) |
| 15 (INFO) | none required | ACCEPTED | Reserved-window note stands for successor harness; non-blocking |
| 16 (INFO) | none required | ACCEPTED | Cosmetic verdict label; no-write behaviour correct; non-blocking |

### Test run
`uv run pytest tests/test_xena_infr015.py tests/test_xena_infr014.py -q` → **26 passed** in 0.44s.

### Scope check
`git diff --stat` vs HEAD ec87269: only design.md, qa-review.md, report.md, calibration_bybit15.py, test_xena_infr015.py (+ new run_cal15_a4.py, untracked) — all within the AMENDMENT-4/fix scope; no other files touched.

### Disposition
APPROVE — Issue 13 fixed with pre-I/O provenance guard and regression test; Issue 14 wording aligned; ready for the operator's execution gate.

## QA run 5 — 2026-07-17T11:31:13Z — mode: subagent — HEAD ec87269012ed7dbed60dee4486dc2d1c77c160cc
Post-execution audit of AMENDMENT-4. Dirty files at review: analysis.md, design.md, qa-review.md, report.md, calibration_bybit15.py, test_xena_infr015.py (+ untracked run_cal15_a4.py, results/{bybit_pc_frozen_registry,cal15_a4_summary,confirm_a4_CLS-EPISODE,design_a4_CLS-EPISODE}.json) — all in-scope.

Verdict: **APPROVE** (artifacts faithful; governance held; pin ACCEPTANCE remains the operator's). Two editorial corrections requested in analysis (Issues 17–18); neither is verdict-material.

### 1. Numbers vs raw artifacts (all recomputed independently)

| Claim (analysis A4.1/A4.3) | Artifact | Recomputed | Verdict |
|---|---|---|---|
| DESIGN F=0 low cov 0.1375 / α̂ 0.1250 | design_a4 curve | 11/80, 10/80 from per-row data | MATCH |
| DESIGN F=0 high cov 0.0375 / α̂ 0.0500 | design_a4 curve | 3/80, 4/80 | MATCH |
| F=12 row low cov 0.075 / α̂ 0.025 / ood 0.5125 | curve | recomputed from coverage_rows/alpha_rows (`gross_pass ∧ n_legs≥F`; ood over alpha rows) | MATCH exact |
| F=16 row low cov 0.050 / α̂ 0.025 / ood 0.750 | curve | recomputed | MATCH exact |
| CONFIRM low cov 0.025 / α̂ 0.030 / ood 0.750 / Wilson [0.014,0.064] | confirm_a4 | 5/200, 6/200, 150/200 from rows | MATCH |
| CONFIRM high cov 0.060 / α̂ 0.030 / ood 0.000, FAIL_COV coverage_limited | confirm_a4 | 12/200, 6/200 | MATCH |
| Bite F*=16 ON: survival 0.000/0.000, select 0.875/1.000 | design_a4.bite + bite_rows (bases 955000/956000 per §14.3) | criteria select≥0.5, survival≤0.125 — PASS | MATCH |
| cal15_a4_summary.json / cal15_a4_run.log | identical per-cadence blocks; log shows exactly ONE design→bite→confirm→write sequence with matching numbers | — | MATCH |

### 2. F* derivation integrity
- Full grid {0,4,6,8,10,12,16,20,24,32} reproduced from per-row data; F=16 is the **smallest all_ok** point (F≤12 fail on LOW cov; F∈{16,20,24,32} all ok). Curve monotone non-increasing in cov and α̂ on both cadences. PASS.
- frozen_procedure carries n_legs_floor=16 + rule string + design_seeds {99000,100000} + confirm_seeds {101000,102000}; confirm procedure block byte-matches it. PASS.
- Confirm rows: low seeds 101000–101605, high 102000–102605; design seeds 99000–100605; **zero overlap** (and disjoint from 91k–98k, 951k–956k). PASS.

### 3. Amended pin (results/bybit_pc_frozen_registry.json)
- `verify_bybit_registry` on new pin: **PASS**. Canonical sha independently recomputed (sha256 of sort_keys registry blob) = `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786` — matches embedded sha and summary. PASS.
- CLS-FILTER block canonical-identical (sort_keys JSON equality) to the block in INFR-014's pin `ac8a1eb6…`. PASS.
- `superseded_pins == [ac8a1eb679…2da6f]`. PASS.
- CLS-EPISODE block: `amended_by: INFR-015/AMENDMENT-4`; confirm_summary verdict LOW_ONLY_CERTIFY, certified true (low certified, high FAIL_COV); n_legs_floor 16 in procedure + per-cadence; A4 seeds 99k/100k design + 101k/102k confirm stamped (Issue-13 guard outcome correct). PASS.
- INFR-014's own pin file UNCHANGED: re-verified in place, sha still `ac8a1eb6…`. PASS.

### 4. Governance
- No retune: F* frozen in design artifact before confirm (log ordering confirms); single execution sequence in log; `stop_condition.forbidden` carries no-optional-stopping / no-floor-adjustment / no-UCB / no-ch03-pin list. PASS.
- n=200 fixed both confirm cadences; design n=80 per §14.3. PASS.
- No chapter-03 pin load: runner reads only INFR-014 pin; void_priors [db87dc1a, 537d691a] intact. PASS. No holdout/TEST contact (synthetic seed banks only). No family transitions (CLS-FILTER untouched; experiment-level only). PASS.
- Bite ran floor ON (n_legs_floor 16 in bite blocks; QA-4 Issue-14 semantics). PASS.
- L-23: §14 declares TIGHTER, running count 0 looser / 1 tighter / 3 neutral — no one-directional streak. PASS.
- Tests: 13/13 pass (test_xena_infr015.py, incl. Issue-13 provenance guard).

### 5. Claims vs evidence
- Monotone floor curve claim: SUPPORTED (verified above).
- ood 0.75 domain-starvation flag (§14.2 >0.5): fired and disclosed — faithful.
- **HIGH boundary-noise sequence "0.065 → 0.050 → 0.060" — MISCITED (Issue 17)**: 0.065 is INFR-014 **CLS-FILTER** high cov; INFR-014 **CLS-EPISODE** high cov is **0.050** (confirm_CLS-EPISODE.json). Correct sequence: 0.050 → 0.050 → 0.060. The boundary-noise framing itself survives (max excursion ≈0.65·SE₂₀₀=0.0154; α̂ 0.030 fine) — conclusion unchanged, citation wrong. Same miscite at analysis.md:25 and report.md:49.
- Bite power claim "plants carry enough legs" — **overstated on LOW (Issue 18)**: 5/8 LOW bite plant rows have n_legs<16 (in_domain false); only HIGH plants (130–262 legs) clear the floor. Bite PASS rests on the predeclared select≥0.5 / survival≤0.125 criteria, which are met; the parenthetical rationale is story-beyond-evidence for LOW.

### Issues (continuing from 16)
17. **MINOR (analysis.md:113, :25; report.md:49)** — HIGH cov 0.065 attributed to INFR-014 CLS-EPISODE is actually CLS-FILTER high; CLS-EPISODE high was 0.050. Correct the three-bank sequence to 0.050→0.050→0.060 (framing/verdict unaffected).
18. **INFO (analysis.md:102-103)** — "plants carry enough legs" holds only for HIGH; LOW bite plants are majority sub-floor. Reword to cite the predeclared bite criteria (select≥0.5, survival≤0.125) as the basis of PASS.
19. **INFO (confirm_a4 per_cadence)** — `deployability_rate` 0.01 counts net_pass floor-OFF (2/200); net∧gross∧in-domain is 0.005. Disclosure-only metric; note the definition wherever quoted.

### Disposition
APPROVE — all binding numbers reproduce exactly from raw artifacts; F*=16 derivation and freeze are sound; the amended pin verifies, is provenance-correct, and leaves the INFR-014 pin intact; governance constraints held. Operator pin sign-off remains PENDING and is not granted by this review. Issues 17–18 are editorial corrections for analysis/report before archival.

## QA run 6 (adversarial manipulation audit) — 2026-07-17T11:57:38Z — mode: subagent — HEAD 6505442bf0482be35c95ebe3703bc6083eb6ee1d
Posture: assume the LOW_ONLY_CERTIFY pass (pin `abbb1842…`) was MANUFACTURED; attempt to prove it. Working tree clean at HEAD. All numbers below recomputed independently from raw artifacts or reproduced by re-execution; nothing taken from analysis.md/report.md.

### Attack surface 1 — Procedure shopping across cycles: **SUSPECT (structural), heavily mitigated — see integrity verdict**
- Fact: three sequential confirm attempts on CLS-EPISODE (INFR-014 block_legs=1 → INFR-015 c1 overlap blocks → A4 blocks+floor), each with a fresh bank, until one passed. This IS sequential testing at the procedure level; no cross-cycle multiplicity correction is applied anywhere, and none is claimed.
- Predeclaration evidence (same-commit granularity means git alone cannot prove order; corroborating chain does): design §14 + FLOOR_GRID reviewed by QA run 4 at 10:55:41Z and fix-verified 4b at 11:01:49Z (HEAD ec87269, pre-execution), execution artifacts mtime 11:09Z (design_a4) / 11:24Z (confirm+pin, local 12:09/12:24 BST), post-exec QA run 5 at 11:31Z, commit 6505442 at 11:33Z. Design→QA→run→audit→commit ordering is internally consistent across three independent timestamp sources. Cycle-1 likewise: QA runs 1–2 (05:15/05:25Z) precede design/confirm artifacts (05:31/05:41Z mtimes).
- Mitigations verified as genuinely present: (a) disjoint fresh banks every cycle (seed-range audit below); (b) both changes mechanism-motivated against the previously measured failure (overlap→blocks; thin-top-1→floor) and TIGHTER/NEUTRAL only — no α, n, n_boot, confidence, or event ever moved; (c) both adverse cycles reported TERMINAL in full, INFR-014 pin left standing each time; (d) the A4 pass is not boundary-hugging: LOW cov 0.025, α̂ 0.030, Wilson UCB 0.064.
- Multiplicity number: naive three-shot family-wise false-pass at nominal 5%/attempt = **1−0.95³ = 14.3%**. That figure is the right order for "could this be the 3-shot artifact?" but overstates the actual gate: each certification requires BOTH point α̂≤10/200 AND cov≤10/200. If the A4 procedure were truly broken at the INFR-014 measured sizes (α 0.075, cov 0.10), per-cadence lucky-pass = 0.0009; over all 6 cadence-slots in 3 cycles ≈ **0.5%** — a pass of this kind is very unlikely to be luck. The exposed risk is a *marginally* miscalibrated procedure: at true rates 0.06/0.06 per arm, per-cadence pass = 0.116, i.e. ≈ **31% over 3 LOW-slots (52% over all 6 slots)**. Sequential cycling therefore cannot have manufactured a pass from a badly broken procedure, but it materially raised the odds of certifying a procedure whose true rates sit in (0.05, ~0.07]. The point estimates (0.025/0.030) sit ~2 SE below the boundary, which argues against the marginal case but cannot exclude it — Wilson UCB 0.064 > 0.05.

### Attack surface 2 — Floor derivation gaming: **CLEAN**
- F* recomputed from raw `design_a4_CLS-EPISODE.json` rows over the full grid {0,4,6,8,10,12,16,20,24,32}: F≤12 fail on LOW cov (0.1375→0.075); F=16 first all_ok (LOW cov 0.050, α̂ 0.025); 16 = smallest passing ⇒ derivation matches the predeclared rule exactly, not retro-fitted to a nicer point (20/24/32 also pass — a gamed pick would be free to choose).
- Grid appears verbatim in code (`FLOOR_GRID`, calibration_bybit15.py:625) and design §14.2 and was traced by QA run 4 (10:55Z) BEFORE the confirm artifacts existed (11:24Z).
- Confirm-bank virginity: exhaustive grep of python/src + python/experiments + `git log -S` across all history for 101000/102000/101_000/102_000 finds only INFR-015 A4 files (one hit in 074f898 is a dollar-equity test fixture `101_000.0`, not a seed). No INFR-014 or discarded cycle-1 artifact contains any 101k/102k seed. Design bank (99000–100605) and confirm bank (101000–102605) row-seed ranges recomputed from artifacts: zero overlap with each other or with 91k–98k / 951k–956k / ch03 ranges. `assert_seed_disjoint_a4` enforces this at both design and confirm entry.
- F* frozen into the procedure dict before confirm; `confirm_gate_a4` reads it and refuses a missing floor (G4b); "no floor adjustment after design freeze" in the forbidden list.

### Attack surface 3 — Selective discarding / rerun-until-pass: **CLEAN**
- `cal15_a4_run.log` contains exactly ONE design→floor-curve→bite→confirm→write sequence; numbers in the log match the JSON artifacts line-for-line; all three confirm-stage files share one mtime (12:24:29 local).
- Determinism reproduced by this auditor: re-executed the first 20 LOW confirm e2e rows (seeds 101000–101019) via `e2e_alpha_a4(LOW, n_legs_floor=16)` with `_set_seeds(101000,102000)` in the project venv — `gross_pass`, `n_legs`, and `gross_lcb` match the stored `alpha_low_rows` **bit-for-bit** (e.g. seed 101000: lcb −41.05325128461321 exact). The pipeline is seed-deterministic: re-running an adverse bank cannot change its outcome, so "discard-and-rerun" is not an available manipulation without changing seeds — which the disjointness asserts and pinned seed fields would expose.
- Adverse results were kept, not discarded: cycle-1 confirm (cov 0.095, α̂ 0.135 LOW; α̂ 0.055 HIGH) fully preserved in `confirm_CLS-EPISODE.json` and reported TERMINAL-2 with no pin change. Cosmetic anomalies noted, non-material: cal15_run.log first line contains a stray `tee: … No such file or directory` capture artifact; design §14 header is dated "2026-07-18" (future relative to actual 07-17 execution) — a typo, contradicted by all timestamps.

### Attack surface 4 — Gate definition drift: **CLEAN**
- Certified gate in the A4 procedure dict: `gate_rule` "per_cadence point α̂≤5% AND no-search cov≤5% (Fork A)", `e2e_pass_event` "stage2_gross_lcb_positive", alpha 0.05, n_boot 200, confidence 0.95, n=200/cell — byte-equal to the INFR-014 pin's CLS-EPISODE and CLS-FILTER gate fields (diffed directly). Only ADDITIONS: `block_legs: episode_overlap_rule_v1`, `n_legs_floor: 16` (+rule text), both TIGHTER. Wilson remains disclosure-only in both (never gated), consistent with the INFR-009 point-α̂ convention. No event redefinition, no n reduction, no alpha-source switch anywhere in the chain.

### Attack surface 5 — Domain-guard laundering (denominator): **CLEAN**
- Recomputed from `confirm_a4_CLS-EPISODE.json` raw rows: LOW α̂ = 6 passes / **200 total rows** (150 of which are out-of-domain and counted in the denominator as non-passes) = 0.030; cov = 5/200 = 0.025; HIGH cov = 12/200 = 0.060 (fails). Zero rows are simultaneously `gross_pass ∧ ¬in_domain`, zero passes with n_legs<16 — the floor cannot be bypassed and refusals are never excluded from the denominator. Code path (`e2e_alpha_a4`:958-973) confirms `n = len(rows)` before any domain filtering.
- Conditionality disclosed, not laundered: `out_of_domain_frac: 0.75` is stamped in the pin's per-cadence block, cal15_a4_summary.json, run log, analysis, report, and all three indexes ("ood 0.75 caveat"); deployability honestly DEPLOY_WEAK at rate 0.01. Operator should read this certification as: *the LOW procedure is calibrated conditional on refusing ~75% of top-1 subsets; live certifications will be correspondingly rare.* That is a narrow claim, but the artifacts state it as such.

### Attack surface 6 — HIGH-cadence asymmetry: **CLEAN**
- HIGH: cov 0.060 ⇒ band FAIL_COV, `certified: false`, deployability N/A in confirm artifact, summary, pin, report, and both doc indexes. Grep for any "HIGH … CERTIF" re-labeling: none. Verdict lattice (LOW_ONLY_CERTIFY) was predeclared in cycle-1 design §7 before any A4 data existed.

### Attack surface 7 — CLS-FILTER contamination: **CLEAN**
- CLS-FILTER block in `abbb1842` pin vs `ac8a1eb6` pin: canonical JSON (sort_keys) **identical**, verified directly. New pin sha256 recomputed from the registry blob = `abbb1842…` exact; `verify_bybit_registry` semantics re-executed by hand (schema, substrate, pin_usage flags, g_net/charge_costs per class, hash) — green. INFR-014's own pin file unmodified at its committed path; `superseded_pins = [ac8a1eb6…]` only.

### Overall integrity verdict: **CERTIFICATION SOUND** (as the narrow, conditional claim it makes)
No evidence of manufacture found on any surface: banks virgin, derivation reproducible and rule-exact, pipeline bit-deterministic (rerun-shopping impossible), adverse cycles preserved, gate unweakened, denominator honest, HIGH not certified, CLS-FILTER untouched. The one structural weakness is real and cannot be audited away: the pass is the third attempt of an uncorrected sequential procedure-refinement sequence.
**Residual multiplicity risk to price into pin acceptance:** if each attempt is charged its nominal 5%, the three-shot family-wise false-pass floor is **14.3%**; under the compound gate the realistic exposure is not "badly broken slipped through" (≈0.5% across all six cadence-slots at INFR-014 failure sizes) but "marginally miscalibrated certified" — at true rates ≈0.06 per arm the sequence had ≈**31%** (3 LOW-slots) to ≈52% (all slots) chance of eventually producing a CERTIFIED read. The observed 0.025/0.030 point estimates argue the true rates are comfortably inside target, but the Wilson UCB (0.064) does not exclude 0.05–0.064. Recommended pricing: treat the CLS-EPISODE LOW certification as calibrated-with-one-sided-uncertainty (true α plausibly up to ~0.06), require any first live XENA-EPSOSC read on this pin to be interpreted with that inflated α in mind, and treat a fourth CLS-EPISODE cycle — if ever proposed — as requiring an explicit family-wise correction or a doubled confirm bank.
