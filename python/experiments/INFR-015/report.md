# INFR-015 — CLS-EPISODE Binder-Form Amendment (Overlap-Aware Stage-2 Blocks)

**Type:** INFR infrastructure  
**Status:** cycle 1 TERMINAL-2 (operator-approved §8) → **AMENDMENT-4 executed 2026-07-18:
LOW_ONLY_CERTIFY, pin amended `abbb1842…` — operator pin sign-off PENDING (§9.3)**  
**Lineage:** amendment attempt on INFR-014 pin `ac8a1eb6…` CLS-EPISODE block (TERMINAL).
CLS-FILTER untouched throughout. ch03 pin `db87dc1a…` VOID.  
**QA:** run 1 design REVISE → AMENDMENTS 1–3 (0L/0T/3N) → run 2 **APPROVE** (design+impl,
execution cleared) → run 3 **APPROVE** post-exec (faithfulness + governance).  
**Execution authorization:** operator standing instruction 2026-07-17 ("proceed to the end…
as long as QA approves from unbiased independent review") — recorded verbatim.

---

## 1. Question + mechanism

Does replacing the CLS-EPISODE stage-2 `block_legs=1` bootstrap with a deterministic
episode-overlap block rule (`episode_overlap_rule_v1`) restore per-cadence α̂ ≤ 5% ∧
no-search cov ≤ 5%? Diagnosis basis: episode streams overlap in time (shared path, holds
to 48h) ⇒ cross-leg correlation ⇒ anti-conservative independent-leg LCB.

## 2. Method (single form change)

- `xen.xena.calibration_bybit15` (new; frozen INFR-014 harness untouched, generator
  imported byte-identical).
- `B = min(max(1, ceil(q90(dur_h)/median(gap_h))), max(1, floor(n_legs/4)))`; pinned numpy
  estimators; B==1 routes to legacy path (bit-for-bit, G2 tested).
- Fresh banks: DESIGN 95k/96k (n=80), CONFIRM 97k/98k (n=200), BITE 953k/954k — disjoint
  from all INFR-014/ch03 seeds (hard assert).
- Everything else INFR-009/014 form verbatim; gate point α̂ ≤ procedure.alpha ∧ cov ≤ 0.05.
- 7 unit tests + G1/G1b/G2/G3 golden traces pass; 20/20 prior suites green.

## 3. Results

| Bank | Cadence | cov | α̂ | inflation | band |
|---|---|---:|---:|---:|---|
| DESIGN n=80 | low | 0.0375 | — | — | disclosure ok |
| DESIGN n=80 | high | 0.0500 | — | — | disclosure ok |
| CONFIRM n=200 | low | **0.095** | **0.135** (27/200) | +0.040 | FAIL_ALPHA · selection_unsafe |
| CONFIRM n=200 | high | **0.050** | **0.055** (11/200; Wilson [0.031, 0.096]) | +0.005 | FAIL_ALPHA (NEAR-MISS band) |

Bite PASS (low survival 0.125 ≤ 0.125, select 0.875; high 0.000/1.000) — blocking kept power.

**Verdict: TERMINAL-2.** Write policy fired: `pin_amended=false`; INFR-014 pin `ac8a1eb6…`
re-verified unchanged (QA run 3, independent re-hash).

## 4. Mechanism read (analysis.md, QA-verified numbers)

- **HIGH cadence — overlap mechanism SUPPORTED as partial effect:** α̂ 0.080 → 0.055,
  cov 0.050 → 0.050 vs INFR-014 (Issue-17 correction); blocks engaged everywhere
  (B median 23; n_legs median 261).
- **LOW cadence — dominant defect is small-sample LCB, not overlap:** α̂ worsened
  0.075 → 0.135. Top-1 n_legs median **11**; false-certifies concentrate at n_legs<8
  (pass 0.179 on 67 rows) where B=1 and the fix is inert by construction. LOW coverage
  also bank-unstable (design 0.0375 vs confirm 0.095, Δ≈2.4·SE₈₀).
- Discipline held: no retune on confirm data; single execution; n fixed.

## 5. Follow-up candidates (each a NEW design; operator/checkpoint decides)

1. Derived `n_legs_floor` stage-2 domain guard (param already exists in
   `lcb_g_leg_studentized`; floor from a design-bank coverage/MDE curve, never asserted).
2. Episode-level resampling unit (resample episodes, not leg-blocks).
3. Generator/leg-starvation realism review for LOW top-1 subsets.

## 6. Integrity checklist

| Check | Status |
|---|---|
| Confirm cov+α̂ on confirm bases 97k/98k (Issue-9 guard) | PASS (QA-verified rows) |
| No pin write on TERMINAL; INFR-014 pin sha unchanged | PASS |
| Frozen calibration_bybit.py untouched | PASS |
| n_null fixed 80/200; no optional stopping | PASS |
| Stage-1 g_net + charge_costs hard refuse | PASS |
| ch03 pin never loaded; no holdout/TEST; no family transitions | PASS |
| Golden traces G1/G1b/G2/G3 | PASS |

QA run 3 informative notes: seed assert window +500 vs +605 consumed (still disjoint);
`tee` error at log head is the missing results dir at launch (same single invocation —
deterministic seeds, no stopping risk); LOW deployability_rate 0.095 undiscussed
(moot — class uncertified).

## 7. Artifacts

```
python/experiments/INFR-015/
  design.md (AMENDMENTS 1–3), qa-review.md (runs 1–3), analysis.md, report.md
  code/run_cal15.py, code/run_cal15_a4.py
  results/design_CLS-EPISODE.json, confirm_CLS-EPISODE.json, cal15_summary.json,
          cal15_run.log
  results/design_a4_CLS-EPISODE.json, confirm_a4_CLS-EPISODE.json,
          cal15_a4_summary.json, cal15_a4_run.log,
          bybit_pc_frozen_registry.json  # amended pin abbb1842… (sign-off pending)
python/src/xen/xena/calibration_bybit15.py
python/tests/test_xena_infr015.py
```

**registry:** not applicable — infrastructure CAL; no candidate-family evidence rows;
no pin change; family status transitions: none.

## 8. Operator verdict

**TERMINAL-2 APPROVED (2026-07-18).** Operator: "approved TERMINAL-2. run the n_legs_floor
follow-up as an amendment, not a new INFR. Document the other follow-ups as potential paths
if the n_legs_floor fail."

- Pin `ac8a1eb6…` stands; XENA-EPSOSC blocked.
- Operator-directed deviation from §13 exit table ("next form change = new design"): the
  n_legs_floor follow-up runs **inside INFR-015 as AMENDMENT-4** (design §14), on FRESH
  seed banks — the spent 95k–98k banks are never reused. Deviation recorded here and in
  the amendment ledger.
- Fallback paths if AMENDMENT-4 fails (documented, not executed): episode-level resampling
  unit; LOW generator leg-starvation realism review (§5).

---

## 9. AMENDMENT-4 (operator-directed follow-up, executed 2026-07-18)

**QA:** run 4 REVISE (Issue 13 MATERIAL: pin seed provenance) → fix + guard + regression
test → run 4b **APPROVE** (execution cleared) → run 5 **APPROVE** post-exec (all numbers
independently recomputed; pin verified; governance held). Issues 17–19 minor/info; 17
corrected in analysis + §4 above.

### 9.1 Result

| Item | Value |
|---|---|
| Floor derivation (design 99k/100k, n=80, F=0 rows) | LOW cov 0.1375 / α̂ 0.1250; HIGH 0.0375 / 0.0500 |
| **F\*** | **16** (smallest all-ok in predeclared grid; monotone LOW curve cov 0.138→0.050, α̂ 0.125→0.025) |
| Bite (F* ON, 955k/956k) | select 0.875/1.000, survival 0.000/0.000 — PASS |
| CONFIRM (101k/102k, n=200) LOW | cov **0.025**, α̂ **0.030** (Wilson [0.014, 0.064]), ood **0.750** — **CERTIFIED** |
| CONFIRM HIGH | cov **0.060**, α̂ **0.030**, ood 0.000 — FAIL_COV (coverage_limited) |
| Verdict | **LOW_ONLY_CERTIFY** |
| Pin | **AMENDED** per predeclared write policy: `INFR-015/results/bybit_pc_frozen_registry.json` sha256 `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786`; `superseded_pins: [ac8a1eb6…]`; CLS-FILTER block canonical-identical (guarded + QA-verified); `amended_by: INFR-015/AMENDMENT-4`; INFR-014 pin file untouched |

### 9.2 Reading

- Floor amendment SUPPORTED: LOW small-n false-certifies eliminated; the floor curve
  drains exactly with domain exit — quantitative confirmation of the TERMINAL-2 diagnosis.
- Binding caveat: LOW **out-of-domain 0.75** — certification calibrated but rarely
  reachable; any XENA-EPSOSC design must expect ≥16 gate-band legs (F*) to certify.
- HIGH: α̂ fine (0.030); coverage 0.060 is boundary noise (0.050→0.050→0.060 across banks,
  ~0.65·SE) — not certifiable under the point gate; no retune permitted.
- Fallback paths if pin rejected (documented, not executed): episode-level resampling;
  LOW generator leg-starvation review — each a NEW design.

### 9.3 Operator pin sign-off (to be recorded)

| Option | Meaning |
|---|---|
| **Accept amended pin (Recommended)** | `abbb1842…` becomes the active binding pin (supersedes `ac8a1eb6…`); CLS-FILTER low (unchanged) + **CLS-EPISODE low** certifiable; XENA-EPSOSC unblocks on low cadence with the F*=16 leg-count reachability caveat binding; HIGH stays blocked |
| Reject amendment | Delete INFR-015 pin file; `ac8a1eb6…` (INFR-014) remains active; EPSOSC stays fully blocked; fallback paths above |

_Pending operator._
