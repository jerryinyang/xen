# INFR-015 — Analysis (data-analyst evidence)

**Emission:** synthetic CAL banks (no Nautilus emission; estimand gate N/A — no price
emission read; per design §12 N/A declarations).  
**Artifacts:** `results/design_CLS-EPISODE.json`, `results/confirm_CLS-EPISODE.json`,
`results/cal15_summary.json`, `results/cal15_run.log`.

## 1. Headline

| Bank | Cadence | no_search_cov | e2e α̂ | inflation | band |
|---|---|---:|---:|---:|---|
| DESIGN (n=80, seeds 95k/96k) | low | 0.0375 | — | — | ok (disclosure) |
| DESIGN | high | 0.0500 | — | — | ok (disclosure) |
| CONFIRM (n=200, seeds 97k/98k) | low | **0.095** | **0.135** | +0.040 | FAIL_ALPHA (selection_unsafe) |
| CONFIRM | high | **0.050** | **0.055** | +0.005 | FAIL_ALPHA (Wilson [0.031, 0.096]) |

Bite (design bank): low survival 0.125 (≤0.125), select 0.875; high survival 0.000,
select 1.000 — **bite PASS** (blocking did not kill power).

**Verdict recommended: TERMINAL-2.** Write policy held: no registry write; INFR-014 pin
`ac8a1eb6…` stands (CLS-FILTER LOW_ONLY_CERTIFY; CLS-EPISODE certified:false).

## 2. Evidence FOR the amendment mechanism (partial success)

- HIGH cadence: α̂ 0.080 (INFR-014) → **0.055**; cov 0.050 → 0.050; inflation +0.005.
  Blocks engaged everywhere (B 12–30, median 23; median n_legs 261). Where legs are
  plentiful and overlap-blocking applies, the fix moved both cov and α̂ toward target.
  0.055 is within 1 SE (0.016) of 0.05 — NEAR-MISS band per design §7, still not certified.

## 3. Evidence AGAINST (why LOW got worse, 0.075 → 0.135)

Per-row interrogation of `alpha_low_rows` (n=200):

| LOW slice | n | stage-2 pass rate |
|---|---:|---:|
| n_legs < 8 (⇒ B=1, fix inert) | 67 | **0.179** |
| n_legs 8–15 | 89 | 0.101 |
| n_legs 16–49 | 44 | 0.136 |
| B=1 | 67 | 0.179 |
| B=2–4 | 125 | 0.098–0.139 |

- Median top-1 n_legs on LOW = **11**. The dominant false-certify source is the
  **small-sample studentized LCB** (bootstrap-t on <16 legs, n_boot 200), not overlap:
  the worst cell is exactly where the block rule reduces to the legacy B=1 path.
- Bank-to-bank: design cov 0.0375 vs confirm cov 0.095 (Δ≈2.4·SE₈₀) — LOW coverage is
  also unstable across banks at these leg counts; the INFR-014 LOW read (cov 0.100)
  plus both INFR-015 banks are consistent with a small-n LCB defect of varying severity.
- Story-vs-proven: overlap correlation (INFR-015 hypothesis) is REAL but secondary on
  LOW; the primary LOW defect is leg-count starvation of the top-1 subset. HIGH result
  proves the overlap mechanism where n_legs is large.

## 4. Discipline

- No retune performed on confirm data (forbidden list in artifact `stop_condition`).
- Seeds verified in artifacts: coverage + α̂ rows both on 97000/98000 bases (Issue-9
  guard asserted at runtime).
- n_null fixed 80/200; no optional stopping; single form change.

## 5. Follow-up candidates (NEW design required — not this experiment)

1. `n_legs_floor` domain guard on stage-2 (`lcb_g_leg_studentized` already accepts
   `n_legs_floor`; out-of-domain ⇒ not certifiable) — attacks the proven LOW defect
   directly; floor must be derived (MDE/coverage curve on a design bank), not asserted.
2. Episode-level resampling unit (resample episodes, not leg-blocks).
3. Generator realism review of LOW top-1 leg starvation (n_cand 64 × thin episodes).

**Recommended experiment verdict: TERMINAL-2 (CLS-EPISODE remains uncertified); the
amendment is NOT SUPPORTED as sufficient, with the overlap mechanism SUPPORTED on HIGH
as a partial effect. XENA-EPSOSC stays blocked.**

---

# AMENDMENT-4 Analysis (2026-07-18)

**Artifacts:** `results/design_a4_CLS-EPISODE.json`, `results/confirm_a4_CLS-EPISODE.json`,
`results/cal15_a4_summary.json`, `results/cal15_a4_run.log`,
`results/bybit_pc_frozen_registry.json` (amended pin, sha `abbb1842…`).

## A4.1 Headline

| Bank | Cadence | cov | α̂ | ood_frac | band |
|---|---|---:|---:|---:|---|
| DESIGN-A4 n=80 (99k/100k), F=0 | low | 0.1375 | 0.1250 | 0 | (floor-off rows) |
| DESIGN-A4, F=0 | high | 0.0375 | 0.0500 | 0 | (floor-off rows) |
| **F\* derivation** | — | — | — | — | **F\* = 16** (smallest all-ok in grid) |
| Bite-A4 (F*=16 ON) | low/high | — | — | — | survival 0.000/0.000, select 0.875/1.000 — PASS |
| CONFIRM-A4 n=200 (101k/102k) | low | **0.025** | **0.030** (Wilson [0.014, 0.064]) | **0.750** | **CERTIFIED** |
| CONFIRM-A4 | high | **0.060** | **0.030** | 0.000 | FAIL_COV (coverage_limited) |

**Verdict: LOW_ONLY_CERTIFY.** Write policy fired positively: pin amended,
new sha `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786`,
`superseded_pins: [ac8a1eb6…]`, CLS-FILTER block canonical-identical (guarded),
`amended_by: INFR-015/AMENDMENT-4`. **Operator pin sign-off pending.**

## A4.2 Evidence FOR

- Floor curve is clean and monotone on LOW: cov 0.138→0.050, α̂ 0.125→0.025 as F 0→16 —
  confirms the small-n LCB diagnosis quantitatively (the defect drains exactly as small-n
  cells leave the domain).
- Confirm on fresh banks (101k/102k): LOW certified with margin (α̂ 0.030, cov 0.025);
  seed bases asserted; F* frozen before confirm contact.
- Bite with floor ON: plant select unchanged (0.875/1.000), survival 0.000 — the
  predeclared bite criteria are met (QA note: 5/8 LOW bite plants were sub-floor; power
  read rests on the select/survival criteria, not on plants clearing F*).

## A4.3 Evidence AGAINST / caveats (operator should weigh)

- **LOW out-of-domain fraction 0.75:** under this pin, ~3 in 4 LOW-cadence top-1 subsets
  are refused certification for thin legs. Certification is calibrated but RARELY REACHABLE
  on LOW at this universe shape — a real LOW episode family needs ≥16 gate-band legs to be
  certifiable. Predeclared domain-starvation flag (design §14.2, >0.5) FIRES on LOW.
- **HIGH regressed to FAIL_COV (0.060 vs 0.050):** floor is inert on HIGH (ood 0.000 —
  legs plentiful) so HIGH coverage is bank-to-bank noise around the boundary
  (0.050 → 0.050 → 0.060 across INFR-014/015/A4 banks — QA run 5 Issue 17 correction;
  SE₂₀₀ ≈ 0.0154). HIGH α̂ 0.030 is
  fine; the binding miss is the coverage arm at ~0.6·SE above target. Not certifiable
  under the predeclared point gate; no retune permitted on this bank.
- LOW deployability_rate 0.01 — net-deployability disclosure remains weak (as CLS-FILTER).

## A4.4 Bottom line

The n_legs_floor amendment did what it targeted: LOW small-n false-certifies eliminated,
LOW CERTIFIED. Cost: 75% LOW domain refusal + HIGH still uncertified (coverage boundary
noise, not the floored defect). Recommended verdict: **AMENDMENT-4 SUPPORTED /
LOW_ONLY_CERTIFY** — pin acceptance is the operator's; if accepted, XENA-EPSOSC unblocks
on CLS-EPISODE **low cadence only**, with the ood 0.75 reachability caveat binding on any
XENA-EPSOSC design (expected leg counts must clear F*=16).

## A4.5 Fallback paths if operator rejects (documented per operator instruction)

1. **Episode-level resampling unit** — resample whole episodes (not leg blocks); attacks
   HIGH coverage boundary + could lower F* by making small-n LCBs honest instead of refused.
2. **LOW generator leg-starvation realism review** — top-1 subsets at median 11 legs may be
   a generator artifact (n_cand 64 × thin episode streams); more realistic episode density
   would shrink ood at fixed F*.
Both are NEW designs (new ID or operator-directed amendment; this cycle's banks are spent).
