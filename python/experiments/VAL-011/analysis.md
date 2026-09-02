# Data Analysis: VAL-011

## 0. Boundary statement (N1 — binding)

This record issues NO verdict, names NO winner, ranks NO arm, claims NO tradability/
deployability, and gates NO companion experiment or family action. Observations are
**observed** (`conditioning_summary.json`) or **inference**. §7 applies only to VAL-011’s
geometry / regime / frequency question. No TEST, holdout, costs, P&L, or family action.

ZERO-COST-DISCLOSURE
  cost_model: NO_COST_CHARGED
  spread: not modeled
  commissions: not modeled
  swaps/funding: not modeled
  implication: every figure in this document is gross and cost-free; no spread,
    commission, or swap enters any calculation. Realised results would differ
    (likely worse) under any real cost schedule.
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  lifting: only an explicit operator directive may introduce a cost model for a
    scoped experiment; the directive is recorded in that experiment's design.md.

**Grid rule.** 132 physical settings vs 264 source cells. Contrast `n_strata=264` is
132 canonical source cells × 2 sides.

**Channel rule.** All-raid frequency is a start-rate. It does not confirm an outcome
mechanism when ATR / strong-move / duration disagree.

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation | **PASS** | VAL-009 gate `blocking_pass=true` |
| Zero-cost | **PASS** | inherited |
| Profile join | **PASS** | physical raids=profiles=joined=4,920,239 |
| TRAIN fence | **PASS** | raids and marks `<= TRAIN_END_NS` |
| ATR exclusion | **PASS** | outcome contrasts drop `ATR_UNDEFINED` |
| Holdout | **PASS** | EXP-100 full only |
| Local accounting | **PASS** | analyst script only |

## 2. Question list

1. Integrity / join? **ANSWERED** §1.
2. P&L / PSR? **UNANSWERED — N/A**.
3. Defined-profile geometry? **ANSWERED** §3.
4. Raid→confirmation→endpoint transitions? **ANSWERED** §4 (confirmation mostly missing).
5. All-raid start rate by preceding regime? **ANSWERED** §3–4.
6. Do LOW/HIGH vs MID outcome channels agree? **ANSWERED** §3–4.
7. Falsification probes? **ANSWERED** §5.

## 3. Evidence FOR a descriptive state split (not a mechanism)

Physical grid:

| View | Observed |
|---|---|
| Cells | 132 physical / 264 source |
| Defined geometry n | 4,897,105 |
| gap_span_va | median ≈ 1.00; p10 ≈ 0.50; p90 ≈ 1.00 |
| va_width median | 2.215 |
| All-raid starts / 1,000 preceding marks | HIGH 1451.3; MID 1276.6; LOW 1244.5; WARMUP 1105.2; ATR_UNDEFINED 234.8 (exposure 1,848) |

Outcome contrasts on ATR-defined completed primaries (264 side-strata):

| Contrast | Channel | mean Δ | strata − / 0 / + |
|---|---|---|---|
| HIGH vs MID | strong_move_rate | −0.072 | 257 / 0 / 7 |
| HIGH vs MID | swing_atr | −0.922 | 258 / 0 / 6 |
| HIGH vs MID | duration_hours | **+2.167** | 45 / 0 / 219 |
| LOW vs MID | strong_move_rate | +0.049 | 23 / 0 / 241 |
| LOW vs MID | swing_atr | +0.849 | 1 / 0 / 263 |
| LOW vs MID | duration_hours | **−0.914** | 217 / 0 / 47 |

**Inference:** LOW vs MID and HIGH vs MID **do** separate on ATR and strong-move, with
broad stratum coverage. That is a description of completed-primary outcomes, not an edge.

Raw HIGH frequency equals physical HIGH frequency (1451.3); raw exposure/starts are 2×.
Rates survive the BB/LC collapse; counts do not.

## 4. Evidence AGAINST using frequency or duration as confirmation

- **Duration disagrees with ATR/strong-move.** HIGH has *weaker* strong-move and *longer*
  duration; LOW has *stronger* strong-move and *shorter* duration. Same disagreement EXP-102/104
  already had: one channel is not three.
- **Frequency disagrees with outcomes.** HIGH has the *highest* start rate and the *weaker*
  completed-primary strong-move vs MID. Starts/exposure cannot underwrite the swing story.
- **Confirmation regime is mostly null.** The nine largest transition buckets (about 4.49M
  of 4.92M physical raids in the top-20 list) have `confirmation_regime=None`. The first
  populated confirmation path is HIGH→HIGH→HIGH at 62,719. A “raid→confirmation→endpoint”
  path census is not available for the bulk of the emission.
- Geometry `gap_span_va` is tightly piled at 0.5–1.0. Continuous span is not a wide
  discriminator in this emission.
- ATR_UNDEFINED start rate uses 1,848 marks; report it, do not lean on it.

## 5. What would make the headline numbers wrong (N7)

| Headline | Probe | Result |
|---|---|---|
| Frequency uses all starts vs preceding marks | 2 starts at one next mark | unit test: MID starts=2, exposure=1 |
| BB/LC collapse | three cells, two methods | canonical list drops the LC duplicate |
| Duration on live load | omit `swing_duration_ns` | regression: column is in `RAID_COLUMNS`; live script now writes contrasts |
| Join on `config` | frozen projection has no `config` | contrasts join `source_cell, side` |

## 6. Anomalies & open questions

- Why `confirmation_regime` is null on the bulk of rows: emission gap vs analysis projection.
  A path-transition claim needs that field filled, or an explicit “raid vs endpoint only” redesign.
- HIGH start-rate vs weaker HIGH outcomes: different populations (all starts vs completed
  primaries). Mixing them is the original EXP-104 frequency mistake; this file keeps them apart.

## 7. Recommended verdict (characterisation only — NOT final, NOT family)

- Recommendation: geometry and all-raid frequency are **describable**; they **do not**
  confirm the strong-move/ATR split. Duration moves the other way. Confirmation-path
  transitions are **not usable** for most rows.
- Driven by: HIGH vs MID sign split across channels; confirmation_regime null in the largest
  buckets; frequency HIGH > MID while strong-move HIGH < MID.
- Would change if: duration and frequency lined up with ATR/strong-move **and** confirmation
  regime were populated.
- Hand-off: operator decides how to annotate EXP-102/104 “supported” language. No family action.
