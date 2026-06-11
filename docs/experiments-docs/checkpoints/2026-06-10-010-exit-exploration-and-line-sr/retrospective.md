# Phase 010 Retrospective — EXIT_FLAT / HYP-001 INCONCLUSIVE (The Screen Worked; The Lever Is Empty)

**Checkpoint:** `2026-06-10-010-exit-exploration-and-line-sr`
**Status:** **CLOSED 2026-06-11** — Tracks A and B complete (EXP-039 audit PASS,
EXP-040 audit PASS); Track C (INFR-002) carried OPEN past the close.
**Outcome classes:** Track A `EXIT_FLAT` (design §9 — nothing qualified at G1;
EXP-041 reserved-inactive, slot unused). Track B HYP-001 `INCONCLUSIVE`
(design §8.3 — permanent mechanism record; the hypothesis remains OPEN).
**Follows:** `2026-06-10-009-avwap-holdout-release` (HOLDOUT_INCONCLUSIVE,
shot SPENT).
**Candidate family:** `CF-AVWAP-001`.

---

## 1. Why this phase existed

Phase 009 spent the programme's single holdout read without confirmation or
refutation, leaving the Phase 008 TEST evidence (EURUSD-4h, FH H\*=12,
+40.56 bps net, permanently non-upgradable) as the family's standing record.
Three independent questions remained: (A) is there a structurally different
exit that beats the FH exit — the only lever that had ever delivered — on this
substrate; (B) does the AVWAP line itself act as support/resistance, the
mechanism question that survives all strategy-form outcomes; (C) groundwork for
the new-asset universe, the programme's declared confirmation path. Phase 010
ran them as parallel tracks with two-speed gating: G1 lenient (TRAIN screen),
G2 strict (one-shot TEST freeze), no holdout consequence anywhere.

## 2. The experiments and their verdicts

| EXP | Track | Verdict | Headline |
| --- | --- | --- | --- |
| **EXP-039** | A — `/EXIT-X` TRAIN screen (DIAG-006, 0 slots) | **MEASUREMENT_COMPLETE — FLAT** | 0/10 (exit × domain) cells qualify under the predeclared §8.1 rule. 4h: R-FH(12) reference +37.3 bps pooled net (n=86 intersection) is the binding bar; best candidate E2 (HA trailing, parameterless) +31.9 bps, gap −5.4 bps ≈ 0.5 bootstrap SE. 1h: every candidate **and the R-BTC reference** net-negative. Determinism PASS; reconciliation to EXP-022 (0.0 bps) and EXP-033 (2.1e-14 bps). |
| **EXP-040** | B — HYP-001 direct S/R test (0 slots) | **INCONCLUSIVE** | Binding pooled contrasts: 1h Δ = +1.55 pp, CI [−4.52, +8.43], Holm p = 0.585; 4h below the 100-episode reportability floor (n = 50/22). Moving-copy control arm (descriptive): 1h Δ_m = +3.41 pp [−1.23, +8.35] — the kinematic confound does not explain the premium; 4h Δ_m ≈ 0 — the negative static Δ was a kinematic artifact. |
| **EXP-041** | A — one-shot TEST confirmation (1 slot, reserved) | **NEVER ACTIVATED** | G1 never opened. Slot unused; ID reserved-inactive, never reusable. No TEST row was read in Phase 010. |
| — INFR-002 | C — new-universe collection | **OPEN (carried)** | No new-universe file had landed at phase close. Collection script and VAL-003 admission validation scaffolded at close (`tools/ctrader-cli/run-infr002-collection.sh`, `python/experiments/VAL-003/`). Holdout seal binds at first touch. |

## 3. What the phase established

- **The capture-efficiency lever is exhausted beyond FH on this substrate.**
  Five structurally distinct exit families (HA-pattern, HA-trailing, Last-X
  trailing, adverse-band stop, target-conditional time-stop) all failed the
  mechanical qualification rule. The predeclared expectation (design §7.9:
  "most candidates failing to beat it is the base case") was confirmed exactly.
- **"Exhausted" means unresolvable at TRAIN power, not FH-optimal.** E2's
  −5.4 bps gap is ~0.5 SE on 86 events; the screen cannot distinguish E2 from
  FH. But a tie buys nothing: FH is simpler, TEST-confirmed (EXP-037/038), and
  frozen. The practical conclusion is unchanged.
- **The power wall is the real finding.** ~86 boundary-contained 4h TRAIN
  events yield bootstrap SEs of 7–30 bps. Any future TRAIN-side comparison on
  this substrate is structurally blind to gaps under roughly 15–35 bps. Event
  scarcity, not candidate creativity, is the binding constraint — and the only
  way to buy power without spending sealed reads is more instruments (Track C).
- **1h is now triply dead on this substrate.** EXP-030 (net-negative
  equal-weight), EXP-033 (FH grid max ≤ 0), and now all ten candidates negative
  with the reference exit itself negative. The events are the problem, not the
  exit. No further 1h spend is warranted.
- **The mechanical gates earned their keep.** E3(3) posted the highest raw
  pooled net (+39.9 bps, above the FH bar), but the predeclared max-min grid
  rule selected E3(8), whose split-half gap flips sign (+24.9/−19.7). A less
  disciplined process would have promoted that cell and burned the one-shot
  TEST slot on a fragile selection. The slot survives because the rules were
  written before the data was read.
- **HYP-001 is narrower but still open.** The confound-free framing finally ran
  (the EXP-025 defect did not recur), and the moving-copy arm resolved the
  kinematic ambiguity in-scope: the 1h premium, if real, is not explained by
  approach kinematics. But the binding CI spans zero and 4h lacked episodes.
  Neither the line-S/R story nor its relative-momentum rival was closed — so
  the prior-reweighting input the design hoped to hand the §9 decision did not
  materialize.

## 4. What changed vs the original design

- **Pre-execution adversarial amendments (§11, 2026-06-10, before any outcome
  read):** EXP-039 containment/intersection populations pinned per criterion;
  ranking on the qualifier-intersection population; EURUSD-share disclosure
  columns. EXP-040 binding family narrowed to the 2 pooled domain contrasts;
  immaterial-null symmetrized; power statement and censoring bracket added.
- **Operator addition (§11/8, 2026-06-11, pre-read):** the EXP-040 moving-copy
  control arm — added before any contrast was read, descriptive-only, and it
  ended up doing real interpretive work (resolving the kinematic confound in
  both domains). Nothing was amended after any outcome read.

## 5. Lessons learned

1. **State the power wall before proposing variants, not after.** EXP-039's
   mandatory power statement (~86 events, SEs 7–30 bps) predicted the FLAT
   outcome's shape. Future substrate-bound screens should treat "can this
   design resolve the gap it is asking about" as a go/no-go input at Stage 1 —
   several of the 10 cells were foreseeably unresolvable.
2. **Parameterless candidates are the right shape for power-starved screens.**
   The only candidate that survived to the final criterion (E2) carries no
   parameters; both gridded families (E3/E5) lost their best points to the
   mechanical selection rule or stability filter. On small event bases, each
   grid point spends stability budget the screen cannot afford.
3. **A reference bar that is itself TEST-confirmed makes FLAT a clean verdict.**
   Because R-FH(12) was frozen and hash-pinned from EXP-037, the screen's
   negative is an honest "nothing beats the incumbent," not "nothing beats a
   number we tuned." Carrying validated incumbents as references should stay
   standard.
4. **Descriptive companion arms are cheap insurance for mechanism science.**
   The moving-copy arm cost one predeclared amendment and converted EXP-040's
   4h read from "puzzling negative" to "kinematic artifact, below floor" — and
   bounded the 1h read. Without it the INCONCLUSIVE would have been murkier.
5. **Floor rules prevented a false negative.** The 4h static contrast
   (Δ = −24.67 pp) would have read as evidence against HYP-001; the
   reportability floor correctly refused the verdict, and the moving-copy arm
   showed the sign was an artifact. Predeclared floors are not bureaucracy.
6. **Reserving a slot behind a gate costs nothing and saves everything.** The
   EXP-041 pattern (ID reserved, activation mechanical, slot unspent on FLAT)
   should be the default for any screen→confirm sequence.

## 6. Consequences and open items

- **Operator decision (recorded 2026-06-11, per design §9 EXIT_FLAT):**
  **Phase 011 proceeds on the Phase 008 frozen package** (EURUSD-4h, FH
  H\*=12, all_legs, EXP-037 freeze, hash-pinned). **Stage-C family review is
  deferred** — Stage-C variants screened on the existing universe would face
  the same 4h power wall; the review is postponed until the new universe can
  power it. HYP-001's INCONCLUSIVE tips neither way and imposes no gate
  consequence.
- **Phase 011 (multi-timeframe model, signal 4h / execution 5m–30m) is
  cleared to open** on the frozen package, still gated on an EXP-027-analog
  method calibration for any new execution domain before binding reads.
- **INFR-002 is the critical path** to both confirmation of the TEST-capped
  package and any future powered Stage-C work. Collection runs via
  `tools/ctrader-cli/run-infr002-collection.sh` (13 instruments; holdout sealed
  at first touch); admission requires **VAL-003**
  (`python/experiments/VAL-003/`, the VAL-001 rev.3 suite scoped to the new
  universe) to PASS. No experiment may read a new-universe row before that.
- **HYP-001 remains OPEN.** Any future attempt needs materially more 4h
  episodes (the new universe again) or a redesigned 1h estimand; within the
  EXP-040 scope no re-parameterization is admissible.
- **Standing constraints unchanged:** no holdout read exists for this family;
  EURUSD evidence permanently TEST-capped; BTCUSD/USTEC/XAUUSD holdouts sealed;
  costs and financing frozen; 5m retired as a primary signal source.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-039 | MEASUREMENT_COMPLETE — FLAT | Negative screen retained in the file-drawer ledger; qualification_table.csv (0/10), power_statement.csv, reconciliation evidence persisted. No rerun within scope. |
| EXP-040 | INCONCLUSIVE | Permanent mechanism record (design §8.3); binding contrasts, moving-copy arm, censoring bracket persisted. HYP-001 stays OPEN. |
| EXP-041 | RESERVED-INACTIVE | Slot unused; ID never reusable; no artifacts beyond the registry row. |
| Exit family E1–E5 | SCREENED — NOT QUALIFIED | Registered dispositions final; re-registration on this substrate requires a new registry amendment and a materially more powered design. |
| Phase 008 frozen package (FH H\*=12, all_legs) | CARRY-FORWARD CANDIDATE | Confirmed as the Phase 011 base by operator decision; unchanged, hash-pinned. |
| INFR-002 | OPEN (carried) → **COMPLETE 2026-06-11 (post-close addendum)** | Collection finished and VAL-003 PASSED the same day the phase closed: all 13 instruments admitted (0 FAIL / 0 INCONCLUSIVE; 24/24 negative controls). Disclosures: DE30 coverage truncated at 2026-01-16 (broker history); duplicate GBPUSD file verified content-identical and removed. Holdout sealed per file; no new-universe row read by any experiment. |
| Stage-C branches | DEFERRED | Family review postponed to a powered (new-universe) setting. |

## 8. Redirect — next steps

1. **Run INFR-002 collection** (`run-infr002-collection.sh`), then **VAL-003**
   once files land; admit the new universe only on PASS.
2. **Open the Phase 011 checkpoint** (multi-timeframe model on the frozen
   package), first experiment an EXP-027-analog method calibration for the
   chosen execution domain(s).
3. **New-universe confirmation design** (which candidates, what gates, whether
   any new-universe holdout read is ever sanctioned) is its own future
   checkpoint, after VAL-003.

No tuning occurred in this phase; no TEST or holdout row was read; both
verdicts were computed mechanically from predeclared rules. The slot is
intact, the books are honest, and the programme moves to execution-layer work
and the new universe.
