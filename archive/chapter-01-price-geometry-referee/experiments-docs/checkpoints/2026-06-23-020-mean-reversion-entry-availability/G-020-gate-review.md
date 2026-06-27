# G-020 Gate Review — Mean-Reversion Entry Availability Screen (Terminal)

**Date:** 2026-06-23
**Gate:** G-020 (Phase 020 terminal gate — admit / exonerate / inconclusive verdict on the CF-MR-001
mean-reversion entry family by a TRAIN-only availability screen; **not** candidate screening, **not** a
tradability / edge / P&L verdict).
**Adjudication basis:** the predeclared **D5 mechanical verdict rule** (`D0-predeclarations.md` §D5) over the
**D2b multiplicity-adjusted joint-max permuted-axis admission gate**, applied against the realized EXP-089
(amended run) statistics. Rubric frozen pre-run in [`G-020-gate-criteria.md`](G-020-gate-criteria.md).
**Outcome:** **ADMITTED.** `S_fam = 28 > S* = 7` and axis perm-p ≈ **0.0002 ≤ 0.05** (FWER 0.05, no cross-axis
Holm — single family; the joint max over the 6 sub-screens absorbs the within-family multiplicity). The argmax
sub-screen — and therefore the admitted **lever** — is **CORE: the bare RSI-2 mean-reversion (fade) entry**.
**CF-MR-001 consumes its first candidate slot.** This is the programme's **first non-random price entry to
clear the family-selection availability gate**, reached at **0 counted TEST reads** with the holdout sealed.
**Holdout:** never touched in Phase 020. `test-read-ledger.md` **unchanged** (all 48 strata stay 0/2 open).

> **Provenance note (carried from G-019).** CF-MR-001 was opened by **explicit operator override** of the
> G-019 price→non-price routing: the G-019 terminal sentence ("price-derived information is exhausted") was
> scoped to the *screened* continuation / magnitude / relational surface, and the **mean-reversion (fade)
> mechanism had never been screened**. Phase 020 screened exactly that unscreened lever plus a
> strategy-agnostic volatility-regime partition. G-020 now admits it. The G-019 mechanical adjudication
> (CF-VOLEXP-001 and CF-XSECT-001 CLOSED and retained) is unchanged.

---

## 1. Decision

The family is adjudicated by the predeclared §2 rule over the 6 single-test sub-screens:

| Sub-screen | S (powered cells) | single-test S* | reading |
| --- | --- | --- | --- |
| **CORE** (bare RSI-2 fade) | **28 / 46** | 5 | **the lever** — favourable availability beyond matched random |
| CORE-VOL-LOW | 22 / 46 | 5 | passes, but adds nothing over CORE (inert regime) |
| CORE-VOL-MED | 25 / 46 | 6 | passes, but adds nothing over CORE (inert regime) |
| CORE-VOL-HIGH | 20 / 46 | 3 | passes, but adds nothing over CORE (inert regime) |
| CORE+TREND | 0 / 46 | 5 | edge destroyed by trend agreement (dead-by-absence) |
| CORE+FILTER | 1 / 29 | 5 | edge destroyed by momentum agreement (dead-by-absence) |

| Family statistic | Value |
| --- | --- |
| `S_fam` (joint max over the 6 sub-screens) | **28** (CORE) |
| `S*` (Q95 joint permuted-axis null) | **7** |
| axis permutation-p | **≈ 0.0002** (0.00019996) |
| FWER band {0.025, 0.05, 0.10} | ADMITTED at all three (S* = 7 / 7 / 6) |
| MC stability (1000 ↔ 5000 perms) | stable (S* 6↔7; perm-p 0.001↔0.0002; **no routing flip**) |
| D2a coin-flip band | [17, 29] — CORE/LOW/MED/HIGH all inside; variants below |
| **Driving lever (argmax)** | **CORE** — the bare fade (family ranking z = 20.2; CORE sub-screen z = 17.3) |

**The ADMITTED conjunction holds.** Per the D5 programme-routing table this opens the **bare RSI-2 fade** as the
first post-admission scope and consumes CF-MR-001's first candidate slot.

## 2. Relationship to the predeclared D5 verdict rule (mechanical)

`D0-predeclarations.md` §D5 / `G-020-gate-criteria.md` §2:

```
S_fam = max over the 6 sub-screens of S_ss
  ADMITTED      iff  S_fam > S*  (joint permuted-axis Q95)  AND  axis perm_p <= 0.05  (FWER 0.05)
  EXONERATED    iff  every sub-screen S is within the D2a noise band (no sub-screen beats the joint null)
  INCONCLUSIVE  iff  the joint permuted null cannot separate at the realized cell count
```

- **`S_fam = 28 > S* = 7`** — the per-family count conjunct holds, by a wide margin (4× the noise ceiling).
- **axis perm-p ≈ 0.0002 ≤ 0.05** — the FWER conjunct holds; robust across the full band {0.025, 0.05, 0.10}
  (S* = 7/7/6, ADMITTED at all three) and MC-stable to the 5000-perm production scale.
- **No cross-axis Holm** is applied (contrast G-019): CF-MR-001 is a **single family**, and the joint-max
  statistic across its 6 sub-screens already controls the within-family multiplicity (the necessity of the
  joint max was shown at the bite-check — a single-sub-screen S\* inflates to 0.40, the joint S\* → 0.043).

**The admission is the predeclared mechanical consequence of the D5 rule, not operator discretion.** The
operator's decision to *open* CF-MR-001 (the G-019 override) is upstream of and independent from this
adjudication; the verdict here follows only from the realized statistic against the frozen rubric.

### 2.1 Lever identification — the bare entry, not the regime, not the variants

The argmax names the lever, and it is unambiguous:

- **CORE (the bare RSI-2 fade) is the lever.** It carries the maximum count (28) and the family ranking z.
- **The volatility-regime partition is INERT.** The three `/VOLREGIME` sub-screens pass uniformly (22 / 25 / 20)
  with flat, small per-cell `Δ̂_rand` medians (LOW 0.050 / MED 0.080 / HIGH 0.045 ATR — indistinguishable from
  CORE's own 0.060). Conditioning on volatility regime neither raises nor concentrates the availability: the
  regimes merely **inherit** the unconditioned edge, they do not **add** to it. The second "new lever" the
  family was opened on is empty.
- **The TREND / RSI-FILTER variants KILL the edge** (S = 0, 1; both below the D2a band → dead-by-absence). This
  is mechanistically corroborating, not a defect: imposing trend (`Close>EMA20`) or momentum (`RSI5>50`)
  agreement on a fade directly contradicts the oversold/overbought entry, removing the reversion population.

Per the §4 routing, G-020 opens the **bare RSI-2 fade, intraday, first**; the vol-regime lever is a
**low-priority** follow-up on this evidence (it adds nothing).

### 2.2 Where the availability lives — per-stratum (the pooled S is disclosure)

The admitted count is **predominantly a 15m / 1h phenomenon** and is read per domain (LESSON-001):

| Domain | CORE cells passing | per-cell `Δ̂_rand` median (ATR) |
| --- | --- | --- |
| 15m | **16 / 16** (universal) | 0.085 |
| 1h | 11 / 16 | 0.072 |
| 4h | **1 / 14** | ≈ 0 |

Passing cells span **all 16 instruments** (no single market drives it); the effect is **monotone in bar
frequency** — near-universal intraday, absent at 4h. The honest admitted claim is *favourable availability for
the bare RSI-2 fade at 15m / 1h, across instruments, over a ~3-bar horizon* — not a timeframe-flat edge, and
explicitly **not** a tradability claim (no exit, no cost, gross, TRAIN-only).

## 3. Adjudication checklist (G-020-gate-criteria §3) — affirmative confirmation

1. **Bite-check GREEN (precondition) — PASS.** The D2b gate passed its fixture check at the **6-sub-screen**
   structure and C=46 (`bite-check/bite_check_report.json`, `OVERALL: GREEN`; all four checks True —
   A_real_module_routes_correctly, B_not_vacuous_and_not_impossible_across_band,
   C_joint_max_necessary_and_sufficient, D_mc_stable_1000_vs_5000). Necessity of the joint max shown
   (single-sub-screen S\* → 0.40; joint S\* → 0.043). Planted family (`CORE+FILTER`, +0.20-ATR, 8 cells)
   detected with power (planted perm-p 0.0004 @ 5000); MC-stable 1000↔5000. The single-test bite sha
   `f01a000b1b230cd172cb4a6cde914014f1efb7ba6b5fc92d25376ee0b6ffab65` is recorded in `run_metadata.json` and
   **equals `bite_expected_single_test_sha256`**. The leg-2 extended-bite requirement is **N/A** — leg-2 (the
   beats-CORE conjunction + regime-membership null) was **retired by `D0-amendment-001`**; all 6 sub-screens
   are single-test. The gate is valid; G-020 is **not void**.
2. **Permutation null validity — PASS.** The joint-max permuted-axis null ran at production scale
   (`N_PERM=5000`, MC-stable vs 1000); the distribution is well-formed (not degenerate); the seed stream is
   byte-reproducible (determinism gate stream true). Axis perm-p ≈ 0.0002 independently re-derived by the
   auditor from `cell_availability.csv` — matches to the integer.
3. **Per-sub-screen and family verdict — recorded (§1, §2)** with realized `S_ss`, `S_fam = 28`, `S* = 7`, axis
   perm-p ≈ 0.0002 quoted; the argmax sub-screen (**CORE**) named as the lever.
4. **Control & leg-2 validity — PASS.** Every sub-screen used the same direction-matched `SUB-RANDOM`; the
   `/VOLREGIME` sub-screens drew their controls from **same-regime bars** so the entry-ATR denominator cancels
   within the comparison (count / direction / regime-membership reconciliation all PASS). **The leg-2
   beats-CORE conjunction was retired** by `D0-amendment-001` after it was shown structurally blind to the
   C-1 entry-ATR↔regime confound; the regimes are now evaluated on the same single-test leg-1 as CORE, and
   they pass *uniformly* (no regime ADDS edge over the pooled CORE). The amendment's two fixes are
   **empirically confirmed**: the regime `Δ̂_rand` ladder collapsed from +0.55 / 0 / −0.52 to flat
   0.050 / 0.080 / 0.045, and the driver flipped from CORE-VOL-LOW (z=115, artifact) to CORE (z=17.3, the
   entry mechanism).
5. **Member-cell readiness — PASS.** 46 member cells (16 instruments × {15m, 1h, 4h} less US500-4h and
   JP225-4h `COVERAGE_EXCLUDED`); RSI-MR event coverage ≥15 per member cell, `n_cond` healthy (855–16218, no
   zero/degenerate cells; EXP-080 8000 ceiling correctly dropped for this dense entry). Realized counts
   supersede design power figures.
6. **Integrity — PASS.** Determinism byte-identical including the permutation stream (`determinism_ok`,
   `determinism_cells`, `determinism_gate_stream` all true); TRAIN sub-split only (analysis-TEST + final-30%
   holdout never sliced); `test-read-ledger.md` unchanged; **0 candidate slots consumed during the screen,
   0 counted TEST reads**; real-price (real domain OHLC) metrics only; causal MR-tempo cap (reversion episodes
   closed strictly before each entry) and causal RSI / EMA / ATR / regime. EXP-089 audit **PASS — 0 Critical,
   0 Warning, 3 Info** (all non-material); Stage-8 post-experiment governance **APPROVE**.
7. **No goalpost-moving — PASS.** The frozen D1 definitions / D2 thresholds / D3 endpoint were not retro-edited
   after seeing any sub-screen outcome; the binding rule was frozen in `G-020-gate-criteria.md` before the run.
   The honest prior (availability ≈ random) did not bias the verdict — it is the hypothesis the screen
   **rejected**. The per-stratum doctrine (LESSON-001) is enforced: the pooled S=28 is reported per domain
   (§2.2) and every collapsed convenience flag treated NON-BINDING.

### 3.1 On the amendment (deviation handling — for the record)

The first EXP-089 run was a **deviation** (audit findings C-1 ATR-normalization confound, C-2 trend-length
horizon — both verdict-material confounds of the frozen design, not code bugs; that run's provisional
`ADMITTED S_fam=27` was driven *entirely* by CORE-VOL-LOW via the then-binding leg-2). Per operator direction
and programme norm ([[deviation_handling_amend_in_place]]) the experiment was **amended in place**
(`D0-amendment-001`: causal MR-tempo cap fixes C-2; regime-matched + horizon-matched control with leg-2
retired fixes C-1; all 6 sub-screens single-test), the deviation results were **hard-deleted**, and the
experiment was **fully re-run and re-audited**. This G-020 adjudicates **only the amended run**; the voided
audit is retained as the forensic record in `audit.md` §Appendix.

## 4. Programme routing (mechanical consequence — D5 / gate-criteria §4)

**ADMITTED ⇒ the argmax sub-screen names the lever and CF-MR-001 consumes its first candidate slot.** Stated a
priori in `G-020-gate-criteria.md` §4:

> *The argmax sub-screen names the lever. CF-MR-001 consumes its first candidate slot; a future G0/D0 opens
> batch 2 (readiness → characterization → capture geometry → TEST), expanding to regime×variant cross-cuts,
> the 25/75 scheme, and the contrarian arm, best-lever-first. The programme's first non-random price entry.*

Concretely:

| Action | Disposition |
| --- | --- |
| **Lever opened first** | **Bare RSI-2 fade (CORE), intraday (15m / 1h)** — the argmax sub-screen. The vol-regime partition is **inert** (low-priority follow-up); the trend / momentum variants are **counter-productive** and not carried. |
| **Candidate slot** | **CF-MR-001 consumes its first candidate slot** (the first slot consumed since the four prior closed families). The family advances from `SCREENED — provisional ADMITTED` to **`ADMITTED`** (binding). |
| **Next phase** | A future **G0 / D0** opens batch 2 as a NEW scope — the **availability→tradability step**: capture-geometry / exit phase for the bare fade (does ~0.75-ATR / ~3-bar availability survive a real exit net of cost?), then frequency-boundary characterization of the 15m→1h→4h decay. Registered-but-deferred and **low-priority on this evidence**: the 25/75 regime scheme, the contrarian arm, regime×variant cross-cuts (the regime partition added nothing). |
| **Holdout / reads** | **No counted TEST read and no holdout touch** is authorized by this admission — admission is an availability verdict on TRAIN, not a TEST contact. The first counted read is a future decision inside batch 2 under its own design, recorded in `test-read-ledger.md` in the same change. |

**Availability ≠ capturable edge.** This gate admits the *raw favourable room* for the bare RSI-2 fade — gross,
no exit, no cost, TRAIN-only. Whether that ~0.06-ATR median room over ~3 bars converts to a tradable
after-cost edge is the question of the next phase, and the short ~3-bar horizon means any capture mechanism
must act fast (slippage / cost bite hardest exactly there).

## 5. Integrity expectations at adjudication (carried)

- **Holdout sealed** throughout Phase 020; the final-30% global holdout never loaded. TRAIN sub-split only.
- **TEST discipline:** 0 counted TEST reads; analysis-TEST and final-30% holdout never sliced;
  `test-read-ledger.md` unchanged (all 48 strata stay 0/2 open). The admission consumes a **candidate slot**,
  not a TEST read.
- **Determinism / anchors:** byte-identical second pass confirmed (cells + permutation gate stream); bite
  report byte-identical with recorded sha == expected.
- **No goalpost-moving:** frozen D1 / D2 / D3 not retro-edited; LESSON-001 per-stratum doctrine enforced; the
  amendment was a verdict-material **fix-and-rerun**, not a down-classification.
- **File drawer:** the inert vol-regime sub-screens and the dead TREND / FILTER variants are **retained** in
  the registry and the multiplicity-registry Phase 020 batch (never deleted or reused); the retired leg-2 item
  is recorded, not erased. An admitted lever is opened; the not-carried branches are closed and not silently
  reopened by re-parameterization.

---

*Companion documents: [`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) §D5 ·
[`D0-amendment-001-mr-horizon-and-regime-matched-control.md`](D0-amendment-001-mr-horizon-and-regime-matched-control.md) ·
[`G-020-gate-criteria.md`](G-020-gate-criteria.md) · family spec
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md) ·
multiplicity registry Phase 020 batch · EXP-089 report / results / audit.*
