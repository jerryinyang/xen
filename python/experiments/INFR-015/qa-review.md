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
