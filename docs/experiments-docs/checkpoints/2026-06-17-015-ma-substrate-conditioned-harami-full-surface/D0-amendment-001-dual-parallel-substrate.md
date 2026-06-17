# D0 Amendment 001 — Dual Parallel Conditioning Substrate (hybrid + native)

**Status:** RATIFIED (operator direction, 2026-06-17). Dated amendment to the Phase 015
`design.md` and `D0-predeclarations.md` under the rule "any change after ratification is a new
registered branch or a dated amendment" (`D0-predeclarations.md` head). **No new countable item is
introduced** — both conditioning modes (`hybrid`, `native`) were already registered at G0
(`multiplicity-registry.md` Phase 015 batch; `candidate-families/harami.md` `MA-SUBSTRATE`). This
amendment **elevates the `native` mode from "co-investigated, bounded" to a parallel first-class
substrate** and corrects a propagated labelling defect.

---

## 1. The defect (root cause)

The Phase 015 design (`design.md` §1; `D0` P2) defines two conditioning objects by **where the
`/STRONG-STAT` magnitude filter is computed**:

- **Hybrid** = filter on the **ZigZag** move (`M_sofar^{ZZ} ≥ p75` of trailing-20 confirmed-ZigZag
  magnitudes) → the EXP-053/060 byte-identical population (**3202** events on EURUSD-5m) — MA
  supplies **only** the outcome geometry.
- **Native** = filter recomputed on confirmed **MA segments** (`M_sofar^{MA} ≥ p75` of trailing-20
  confirmed-MA-segment magnitudes) → a **different** entry population (**8360** events on
  EURUSD-5m).

**EXP-060B's `M`-arms (`M0/M1/M2/M3`) — and EXP-061's `M0`, forked from them — condition on
MA-segment `/STRONG-STAT`,** i.e. `live_strong_stat(state.k, state.m_sofar, seg["magnitude"])` with
`seg` = MA segments (`EXP-061/code/run_experiment.py:708`, `:722`; `m0.m == ma_conditioned == 8360`,
`EXP-061/code/run_experiment.py:663`). **That is the design's `native` definition.** The `M`-arms
were nonetheless labelled the *hybrid* "BENCH-MA" object and used as the P12 reconciliation anchor.

Consequences:

1. **The genuine hybrid object (ZZ-conditioned 3202 × MA-segment geometry) was never computed**
   anywhere in the frozen lineage. EXP-060B produced ZZ×ZZ (`Z`-arms, 3202) and MA×MA (`M`-arms,
   8360); never ZZ×MA.
2. **D0 P12 reconciled EXP-061 `M0` to EXP-060B `M0` and "passed" — but against the wrong object.**
   Both sides were native; the test was self-consistent and silent on the mislabel.
3. **EXP-061's "lead L1 — EVIDENCE_FOR (benchmark-geometry generalisation)" and the EXP-060B "85/99
   edge" were measured on the NATIVE population,** not the hybrid object the design names as primary.
   The hybrid object's benchmark efficacy is, as of this amendment, **unmeasured**.

This is a labelling/conditioning defect propagated EXP-060B → EXP-061, not a scope typo. Verified in
code and in the frozen parquets (`EXP-060B`, `EXP-061` `per_cell_expectancy.parquet`).

## 2. The decision (operator, 2026-06-17)

Elevate **native** to a **parallel first-class substrate** tested across the **full surface** beside
**hybrid**. Both objects are **measured and reported individually** — separate arms, separate
matched-random nulls, separate per-cell viability, separate P11 composition, separate G-015 inputs.
**No pooling or aggregation of the two objects in any read** (aggregation would defeat the
comparison's purpose).

Operator-ratified parameters of the amendment:

- **(a) Re-run lineage ≥ EXP-061** under the dual-object design via the full pipeline
  (scope → plan → code → audit → interpret → document → governance). Prior EXP-061/062/063 results
  are **superseded in place** (same IDs; each report + index records the prior finding as
  `SUPERSEDED` with a one-line pointer and the defect reason).
- **(b) Reconciliation roles flip** (see §3 / amended P12).
- **(c) Slate restructure** (see §4 / amended P9): the bounded native track collapses — EXP-067 is
  the **hybrid** combined champion; a single new **EXP-068** is the **native** combined champion
  (merging the old N1+N2); **EXP-069 is dropped**.
- **(d) Reporting is per-object throughout** (amended P5 / P3 viability / P6 composition).

## 3. Reconciliation roles (corrected)

Because the existing `M`-results **are** the native object:

- **Native arm → reconciles to EXP-060B `M0/M3` (and EXP-061 `M0`) to 1e-9.** The native object
  keeps a valid back-reconciliation anchor (the mislabelled-but-numerically-correct `M`-arms).
- **Hybrid arm → genuinely new; NO back-reconciliation anchor.** It leans on **population
  reconciliation to EXP-053's 3202 ZigZag-`/STRONG-STAT` set (exact)** + determinism + causality +
  the structural invariants (the P12 discipline the design already prescribes for an anchor-less
  object — previously, wrongly, assigned to native).

## 4. Slate after this amendment

| ID | Object(s), reported individually | Mirrors | Role |
| --- | --- | --- | --- |
| EXP-061 | hybrid **and** native | 049+053 | L1 capture readiness + benchmark efficacy (re-run, supersedes) |
| EXP-062 | hybrid **and** native | 055 | L2 lifetime availability (re-run, supersedes) |
| EXP-063 | hybrid **and** native | 057 + mean diag | L3 adverse geometry + mean diagnostic (re-run, supersedes) |
| EXP-064 | hybrid **and** native | 056 | S1 favourable-target OAT surface (paused → resume dual-object) |
| EXP-065 | hybrid **and** native | 058 | S2 third-barrier OAT surface |
| EXP-066 | hybrid **and** native | 059 | S3 position-management-exit OAT surface |
| EXP-067 | **hybrid** combined champion (native disclosed) | 060 | S4 hybrid integrative readout |
| EXP-068 | **native** combined champion (hybrid disclosed) | 060 | native integrative readout (merges old N1+N2) |
| ~~EXP-069~~ | — | — | **DROPPED** (folded into the parallel surface + EXP-068) |

The native object now carries the **full** favourable/third/exit OAT surface (S1–S3), which the
original P2 withheld from it. G-015 stays the single terminal gate and spans both objects, judged
**individually** (a PROCEED may register either object's combined definition).

## 5. Registry / governance impact

- `multiplicity-registry.md` Phase 015 batch table updated: native rows added at L1–S3; EXP-067
  retagged hybrid-combined; EXP-068 = native-combined (HYP-021 reassigned); HYP-022/EXP-069 marked
  **DROPPED** (retained in the ledger, never deleted). No new countable item; `native` was already
  countable at G0.
- `candidate-families/harami.md` `MA-SUBSTRATE` entry: native mode re-described as parallel
  full-surface; EXP-061 HYP-014 card marked SUPERSEDED-pending-re-run.
- `design.md` §1/§5/§7 and `D0-predeclarations.md` P2/P5/P9/P12 amended (this file is the governing
  record; in-file edits cross-reference it).
- **0 candidate slots, 0 TEST reads** unchanged; holdouts sealed; `test-read-ledger.md` unchanged.
</content>
</invoke>
