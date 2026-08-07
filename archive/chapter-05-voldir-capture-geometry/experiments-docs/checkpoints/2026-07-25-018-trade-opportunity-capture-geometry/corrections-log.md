# Checkpoint 018 — Corrections log for the SPDR-018 / SPDR-018B documentation

- **Date:** 2026-07-26
- **Trigger:** operator instruction to have an independent, unbiased agent verify that every claim,
  observation and interpretation in the closed documentation is 1-to-1 data-backed.
- **Method:** an adversarial verifier, read-only on the repo, re-derived ~110 figures from
  `results/*.parquet` and `results/*.json` with its own code. Every finding below was then
  **re-verified independently by the orchestrator** before being accepted — findings are not taken on
  the auditor's word.
- **Audit report:** `scratchpad/audit/AUDIT.md` (session scratchpad, not a repo artifact)
- **Audit verdict:** **RELIABLE WITH CORRECTIONS** — 2 critical, 12 material, 8 minor, 2 unverifiable.
  **Both operator verdicts survive.** No B-5 violation, no prohibited claim, staleness handling clean,
  and the "seven un-run inherited HARD checks" claim correct in count and in all seven names.

---

## Critical — accepted and corrected

### C-1. The C2 ruling's third reason was false, and false in the direction the ruling needed

**As written** (018B `report.md` §4.1, `analysis.md` §7.5, `reflection-inputs.md` §3.1, `INDEX.md`,
`cf-voldir-001.md`): *"the like-for-like cell (n=290) could not reliably have detected crypto's
+22.6 bps."*

**What the data says.** `controls.json` → `magnitude_matched.shock_flag.plant_curve`:

| plant | +5 | +10 | **+20** | **+40** |
|---|---|---|---|---|
| percentile | 0.285 | 0.755 | **1.000** | **1.000** |

The +10 figure was quoted correctly; the curve does not stop there. Resolution is **10–20 bps**, so an
effect of crypto's magnitude **would** have been detected. Live value **−9.383 bps at pct 0.043**.

**Consequence.** The honest reading is the *opposite*: the cTrader control **was** powered for an
effect of crypto's size and measured the **opposite sign** — a **powered non-replication on that
cell.** This **strengthens "not replicated" and removes one of the four supports for "not refuted".**

**Disposition.** The **ruling stands but on three legs, not four.** Reasons 1, 2 and 4 were verified
and are unaffected (comparator mean +0.97 EU → +12.05 Asia with the Asia null entirely above zero; the
effect vanishes in EU at pct 0.443; the rebuild flips `P-MR` 0.067 → 0.826). Corrected in all five
locations; an orchestrator ADDENDUM was appended to 018B `analysis.md` rather than rewriting the
analyst's text. **The operator should treat "not refuted" as more weakly supported than first
presented.**

### C-2. "The free residual `log R` is uniformly negative" — false at cell level

**As written** (018 `report.md` §4/§8, `reflection-inputs.md`, `INDEX.md`, `cf-voldir-001.md`).

**What the data says.** `log R > 0` in **459 of 1,413 powered cells (32.5%)** — and that is the
**identical set** to the 32.5% reported as clearing gross break-even, because `R > 1 ⟺ p > p_be`.
An internal contradiction sitting four lines from its own refutation. What *is* negative: the median
(**−0.0301**), the mean (**−0.0356**), and all five per-exit-mode medians.

**Provenance.** The binding `analysis.md` §5.3 was **precise** — it said "uniformly negative" of the
five per-mode medians. The unqualified generalisation was introduced by the orchestrator's summary,
not the analyst.

**Disposition.** Corrected everywhere to "negative at the centre … though positive in the same 32.5%
of cells that clear gross break-even, by identity". **No conclusion changes** — the mirror finding
rests on R² 0.9667, the 82.8% indistinguishability, and the movability test, none of which are
affected.

---

## Material — accepted and corrected

| # | Claim as written | What the data says | Effect |
|---|---|---|---|
| M-1 | **Crypto pooled `edge` −0.1105** | **−0.0728** (mean −0.0860). The −0.1105 was median `p` − median `p_be_net`; medians are not additive | Corrected before the audit, in all four locations, with a reading note. `analysis.md` never stated a pooled edge |
| M-2 | **C8: "median difference 0.0023 across 340 cells"** | 0.0023 is the **difference of medians**; the **per-cell median \|diff\| is 0.0082** (p95 0.0431) — 3.6× larger. Same non-additive-operator error, inherited from `analysis.md`; **018B computed its own correctly** | Conclusion holds (0.0082 against a rate of 0.47 is still agreement); figure corrected |
| M-3 | **L-53 / P-25: "the charge exceeds the best cell at any deflator above ~0.06"** | The break-even deflator is **0.1785**. At 0.165 two cells clear; **at 0.06, thirty-two do.** So `0/315` clears the 0.185 defensible floor by **4%**, not by 3× | **Materially thinner margin than claimed.** Conclusion survives the defensible range, but "comfortably" was wrong. Corrected in L-53 and P-25 |
| M-4 | **018B §3: "All 13 rows below are powered"** | False for R12's constituents: **A5 (27 cells), D2 (24), D7 (6) have zero powered cells** | Corrected. For those three no bps target attaches (definitional, not a power failure), but their replication claim has no power statement behind it |
| M-5 | **018B §9.2: `entry_ts == event_ts` on 100% of panel rows** | **96.26%** (224,830 of 233,569) | Corrected. Still the fill-ts off-by-one shape; still harmless (nothing joins on it; the index is causal) |
| M-6 | **reflection-inputs: "best powered cell +8.24 bps"** | Best is **+8.4991**; +8.2396 is the best *with a CI excluding zero* | Corrected with both figures distinguished |
| M-7 | **018B C7 "1.44% exceed the two-band MDE" vs 018's 6.63%** | 018B sums the two band MDEs where 018 uses quadrature. On a common basis: **6.63% vs 7.02%** | C7's conclusion holds; **the apparent 5× improvement does not exist.** Recorded in the 018B analysis addendum |
| M-8 | **L-50: one defect caused three wrong numbers** | The binding 018B report attributes the net-clearing figure **jointly** to the independent deflator error | L-50's causal chain is overstated for that one of the three; the portability defect fully owns the powered count and the mirror R² |

---

## Findings the auditor raised that were checked and NOT accepted as errors

- **018 §3's C6 dose-response magnitudes.** The auditor notes they come from all 534 powered arm-C
  cells grouped by z/h rather than from the 14 C6 cells. That is how `analysis.md` §3 reports them, and
  the report is faithful to its source. Recorded as an imprecision in the *source*, not a
  misquotation, and left as-is with the count stated.
- **Identity check on 23,270 vs 24,098 signed cells.** The 24,098 figure is the analyst's own signed-cell
  count and is reproduced exactly from the artifact; the smaller number is the subset carrying a finite
  residual. Not a wrong claim, but the two are worth distinguishing if the figure is reused.

## Could not be verified — recorded openly

| Item | Status |
|---|---|
| **A-IC's "165 cells, median 0.3262"** | The auditor's closest reconstructable slice gives 554 cells at median 0.3076. The exact 165-cell H1 subset could not be identified from the emission. **Unresolved** — treat the 0.3262 figure as unconfirmed |
| **TRIPWIRE-1 "held on 100% of 233,569 rows"** | The panel row count checks out, but the emitted check covers **2,602 rows**; the analyst's own 233,569-row recomputation was never emitted as an artifact. **Unverifiable from artifacts** — exactly the L-52 failure mode, one level up |

---

## What survived scrutiny

- **Both verdicts.** `HYP-D5` **SUPPORTED** (SPDR-018) and **PARTIALLY SUPPORTED** (SPDR-018B) are
  supported by the evidence and match their binding analyses' recommendations.
- **Every headline number of the two-universe picture**: 315 / 2,401 / 1,413 powered; `p` 0.4868 vs
  `p_be` 0.4855; mirror R² 0.9746 and 0.9667; **0 of 1,413 and 0 of 315 clearing `p_be_net`**; the
  cost-share decomposition; the 3,559 `NOT_RESOLVABLE` count; the integrity counts (18 HARD / 11 HARD
  + 1 INFORMATIVE, 0 failed).
- **The seven un-run inherited HARD checks** — correct in count and in all seven names.
- **No B-5 violation**, no prohibited claim (tradability / deployability / cost-complete /
  family-status / graduation / XENA), nothing phrased against `p > 0.5`, and the stale-figure handling
  is clean: every superseded value appears only as a labelled correction.

---

## Standing lesson this audit earned

**Aggregate-of-aggregates is its own error class, and it recurred three times in one documentation
pass** (M-1 crypto `edge`, M-2 C8, and the near-miss on the cTrader break-even gap that flips sign
between medians and means). Two of the three were inherited from a binding analyst document.

> **Rule:** a quantity that is exact per cell must be **read from its own column**, never reconstructed
> by combining aggregates of its inputs. When a table reports medians, state that the rows are not
> additive. When a conclusion could turn on the choice of aggregator, **report both** and say which one
> the conclusion needs. This is folded into **L-53**'s meta-lesson and is the reason every
> `(p, W, L, W/L, edge)` table in this checkpoint now carries median **and** mean.
