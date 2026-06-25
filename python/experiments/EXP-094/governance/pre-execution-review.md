# EXP-094 — Pre-Execution Governance Review

**Phase 021 · CF-MR-001 / HYP-002 · governed by `D0-amendment-004` + `D0-amendment-005`.** Consolidated Stage-4
review of `scope.md`, `analysis-plan.md`, `code/run_experiment.py` against the governance constraints, the
developer code conventions, and the active checkpoint design.

## Checks

**Signal-registry precondition (file-drawer control).** PASS. Family `CF-MR-001` is `ADMITTED (BINDING)`.
EXP-094 is registered in the Phase-021 multiplicity batch (4h readiness + falsification re-screen); the 4h
domain is OPENED by `D0-amendment-004` (**0 new candidate slots** — domain expansion of the admitted lever) with
the binding null corrected by `D0-amendment-005`. TRAIN-only ⇒ **0 counted TEST reads**; `test-read-ledger.md`
unchanged (all 4h strata stay 0/2). TEMP-091 recorded as a file-drawer disclosure and archived.

**New selection statistic ⇒ bite-check required GREEN before the binding read.** PASS (gated). The binding
§4(c) statistic is the **matched-distance paired-Δ quorum** (`D0-amendment-005`). The code computes a
bite-check (leg e: FPR under a same-distribution null ≤ 0.10 ∧ power at the planted per-cell MDE ≥ 0.80) and the
verdict function **withholds the binding verdict** (`HALT_BITE_NOT_GREEN`) unless the bite-check is GREEN.
Computation order (bite-check after resolution in one pass) is immaterial because no 4h admission verdict is
emitted or acted upon unless GREEN — the spirit of "bite-check before relying on the statistic" is honoured.

**Methodology soundness (the crux).** PASS. The original §4(c) SUB-RANDOM-entry RCT null was found at Stage 3 to
be biased toward admission (signal-derived RCT target degenerate/wrong-side at random bars → engine instant-fill,
`xen/intrabar_fill.py:220`); it was corrected by `D0-amendment-005` to the matched favourable-target-distance
oscillation null (favourable by construction → no instant-fill regime) and retained only as a non-binding
companion. The binding test now genuinely falsifies the oscillation hypothesis. The 1h positive control gates
INCONCLUSIVE if the test is under-powered.

**Holdout / TRAIN discipline.** PASS. TRAIN sub-split only via the reused EXP-090 `load_train_1m`
(`int(total_rows·0.7)` analysis → `int(·0.7)` train; asserts 0 holdout rows read); 1m fill clipped by timestamp
at the TRAIN edge; `holdout_untouched=True` in metadata. Analysis-TEST + final-30% holdout never sliced.

**Real-price / alignment / determinism.** PASS. `net_return_atr` on real fill prices + real ATR; no HA/Renko.
Cross-view alignment by epoch in the 1m engine, never bar index. All seeds via `seed_for`; determinism replay on
2 cells (net_ci_low, net_clear, delta_lo, beats_random frame-identical) + SHA-256-pinned headline CSVs.

**Denominators / zero-baseline.** PASS. Resolved-event denominators (finite gross, ATR>0, valid hold) per
(cell × arm); the falsification statistic is an **absolute ATR difference** compared to the 0 floor — no
percentage-vs-zero-baseline. Matched random counts matched to real resolved counts; `rand_resolved_frac`
reported.

**Code conventions.** PASS. Imports→paths→constants→dataclasses→helpers→pure computation→aggregation→
orchestration→writers→plots→main; output dirs in `run()` only; lazy TRAIN load; `tqdm` on outer loops; bounded
plot inputs (≤13 cells, no reloads); concise logging; 0 new `xen` modules.

**Complexity budget.** PASS. Binding tests 2/≤3 (net-screen bootstrap; matched-distance paired-Δ); companions
(SUB-RANDOM, 1h control, RT/2) non-binding; plots 4/≤4; new modules 0.

## Disclosed deviations (reviewed — not verdict-material)

1. **PARTIAL-TRAIL omitted from leg (b).** Leg (b) screens the 5 intrabar-engine arms; PARTIAL-TRAIL (coarse
   domain-bar resolver, non-primary) net-cleared 0 cells in both EXP-091 and TEMP-091. Immaterial to the binding
   RCT verdict; disclosed. Acceptable.
2. **Random draw from EXP-090 `eligible_pool`** (look-ahead-safe, real-CORE-entry-fenced) rather than
   `random_entries` over all bars — a correctness improvement consistent with EXP-090's matched-random
   semantics; documented in the module docstring. Acceptable.

## Verdict

```text
VERDICT: APPROVE
```

The implementation faithfully encodes the amended (corrected) binding falsification, gates the binding verdict on
a GREEN bite-check, preserves TRAIN/holdout discipline and determinism, and stays within budget. The two
disclosed deviations cannot move the binding RCT admission verdict. Proceed to the manual execution gate.
