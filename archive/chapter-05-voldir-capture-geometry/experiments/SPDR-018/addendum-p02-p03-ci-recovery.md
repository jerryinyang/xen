# SPDR-018 — Addendum P2 + P3: median / trimmed-mean CIs and CI fragility

- **Date:** 2026-07-26
- **Threads:** **P2** and **P3** from `analysis.md` §14 / `report.md` §9 (P3 also SPDR-018B §12)
- **Class:** analysis addendum. **Frozen artifacts not rewritten; `screen_code/` imported, never modified.**
- **Script:** `analysis_code/p02_p03_full_ci.py` · **Artifact:** `results/p02_p03_full_ci_armB.parquet` (451 rows, 118 cols)
- **Coverage:** the **451 powered signed arm-B `per_symbol` cells**. See §5 for what is *not* covered.
- **Status:** **P3 CLOSED. P2 ANSWERED on this stratum — and it changes how the headline should be worded.**

---

## 1. Why these were open, and why neither needed a re-emission

Both were recorded as gaps in the closed analyses:

- **P2** — design §6.1 requires block-bootstrap CIs on **mean, median and 10% trimmed mean**, "all
  three always co-reported", *explicitly because this family is fat-tailed*. They existed on **240 of
  24,098 signed cells (1.0%)**, and on 4.0% of powered cells.
- **P3** — INFR-004 / L-20 require a seed battery and block sweep behind any CI carrying a read.
  Neither was emitted anywhere in either run.

**Neither was a missing method.** Both are already implemented in the frozen statistics layer:

| Thread | Where it already lives | Why it was absent |
|---|---|---|
| P2 | `metrics.signed_cell(full=...)` computes both CIs | `full` defaults to `False`; the arms pass `full=exhausted`, so only levers-exhausted cells got them |
| P3 | `metrics.envelope_ci_suff()` builds `per_block` with per-block CIs over blocks {1,3,7} days **and** `ci_low_seed_range` / `ci_high_seed_range` across the 5 seeds, returned as `signed_cell()["_ci_detail"]` | **`cells.py:127` explicitly skips `_ci_detail` when building the record.** It was computed on every one of the 37,791 cells in both runs and discarded at serialisation |

So P3 was never a measurement gap — it was a **serialisation gap**, which is why recovering it costs
nothing beyond recomputation.

## 2. Why this addendum is trustworthy — the validation contract

Reproducing a cell's input series by regrouping the parent panel is the one place drift could enter.
So **every recomputed cell must reproduce its frozen mean-family values** — `mean`, `p`, `W`, `L`,
`W/L`, `edge`, `block_mde_mean_bps` — to **1e-6 relative**, or it is reported and **excluded rather
than published**. A cell that reproduces those values was provably computed on the same input series,
which is what licenses trusting its new CIs.

> **451 of 451 cells validated.** Zero exclusions. Runtime 6.1 min at `--jobs 8`.

---

## 3. P2 — the three point statistics disagree, and only one of them fails to reject zero

| Across the 451 cells | mean | median | 10% trimmed mean |
|---|---|---|---|
| median across cells (gross bps) | **−2.079** | **−17.600** | **−14.794** |
| **CI excludes zero** | **46 of 451** (45 neg, 1 pos) | **449 of 451** (all negative) | **451 of 451** (all negative) |

| Fat-tail diagnostics | Value |
|---|---|
| median (mean − median) | **+15.61 bps** |
| p95 \|mean − median\| | **32.06 bps** |
| sign agreement across the three statistics | **0.803** |

### What this means, stated carefully

**This is threat T2 converted from a caveat into a finding, and it makes the negative read stronger,
not weaker.**

On the **mean** — the statistic the identity is built on — these cells look indistinguishable from
zero: only **10.2%** reject zero. On the **median and trimmed mean**, **essentially every cell
(99.6% / 100%) is significantly negative.** So the familiar framing *"the powered cells sit
essentially at gross break-even"* is not merely the most favourable of three statistics by 13–16 bps
— **it is the only one of the three that fails to reject zero.**

**Two things this does NOT license:**

1. **It does not change any identity-based conclusion.** `p·W − (1−p)·L = mean` is a *mean* identity
   and cannot be restated on medians. `p_be`, `p_be_net` and `edge` are mean-family objects and are
   unaffected. **0 of 1,413 clearing `p_be_net` stands exactly as reported.**
2. **It does not make the result "worse than reported" in the direction that matters.** Both verdicts
   were already negative-to-null. A typical cell being 17.6 bps below zero on the median rather than
   2.1 bps below on the mean reinforces "no positive term", which is the conclusion both closed
   reports reached.

**Recommended wording change** wherever the near-break-even framing appears: *"the rate sits at its
own gross break-even and the mean is indistinguishable from zero, while the median and trimmed mean
are significantly negative on essentially every powered arm-B cell — the mean is the identity's
object, but it is also the most favourable of the three."*

---

## 4. P3 — the CIs are **not** fragile. This closes the thread cleanly.

Seed span = (max − min) across the 5 bootstrap seeds, expressed as a fraction of the CI's own width.
A small number means the Monte-Carlo draw is not deciding the answer.

| Statistic | median | p95 | max |
|---|---|---|---|
| mean | **0.0477** | 0.0674 | 0.0888 |
| `p` | 0.0485 | 0.0664 | 0.0836 |
| `edge` | 0.0475 | 0.0653 | 0.0764 |
| median | 0.0554 | 0.1079 | **0.4780** |
| trimmed mean | 0.0476 | 0.0637 | 0.0768 |

Block sensitivity — CI-low span across blocks {1, 3, 7} days:

| Statistic | median | p95 |
|---|---|---|
| mean | **0.433 bps** | 1.591 bps |
| median | 0.646 bps | 1.917 bps |

### Answer

> **Every CI carrying a read on this stratum is stable to both the seed draw and the block choice.**
> Seed spans run **~5% of CI width** and block spans **0.4–0.6 bps** against effects of 2–18 bps.
> The `min/max over blocks × seeds` envelope rule is doing real conservative work, and no read in
> either run rests on a Monte-Carlo artifact.

This **retroactively supports every CI-based conclusion in both closed reports** — the 129-cell
counter-outcome, the per-cell `W/L`-vs-mirror tests, and the band comparisons — and closes the
INFR-004 / L-20 gap for this stratum. **One caveat:** a single cell shows a median-CI seed span of
0.478 of width; it is an outlier, not a pattern (p95 is 0.108).

---

## 5. Coverage — what is NOT covered, stated plainly

| Population | Covered? |
|---|---|
| arm-B powered signed **`per_symbol`** cells | **451 — yes** |
| arm-B powered `per_symbol_full_train` (298), `pooled_raw` (65), `pooled_sigma_normalised` (65) | **no** — different groupings |
| **arm-C powered signed cells (534)** | **no** |
| the `trail` / `stop` populations behind L-51 | **no** — these are unpowered, so they were never in the powered target set |

So P2 is answered on **451 of the 1,413** powered signed cells (32%) and P3 on the same. The arm-C
stratum matters most for the remaining question, because arm C is the near-symmetric object whose
gross median is *positive* (+0.08 bps) — the one place where a median-vs-mean flip could in principle
run the other way. **Extending to arm C and to the `trail`/`stop` populations is the natural next
step and requires only the same script with each arm's own grouping.** Until then, §3's finding is
established for arm-B per-symbol cells and should not be generalised to arm C.

---

## 6. Governance

| Item | Value |
|---|---|
| Counted TEST reads | **0** |
| Holdout contact | **none** |
| Frozen artifacts modified | **none** — `arm_*.parquet`, `metrics_by_cell.parquet` read for validation only |
| `screen_code/` modified | **none** — imported only |
| Cells or estimands changed | **none** — SPDR-018 remains closed; this adds columns on a new artifact |
| Family status change | **none** |

**No tradability, deployability, cost-complete, family-status, graduation or XENA claim is made or
implied by this document.**
