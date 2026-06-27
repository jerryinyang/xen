# Pre-Execution Governance Review — EXP-061 (dual-object re-run)

**Experiment:** EXP-061 — MA(20,50)-Substrate Capture Readiness & Benchmark-Geometry Conditioned
Efficacy (**dual conditioning object: hybrid + native**). Phase 015 lead **L1** ·
`CF-HA-HARAMI-001/HYP-014`.
**Reviewer:** research-pipeline Stage 4 (consolidated governance).
**Date:** 2026-06-17.
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`.
**Context:** Re-run under `D0-amendment-001-dual-parallel-substrate.md`; **supersedes the prior
EXP-061 result in place**. The prior post-exec governance is void for the superseded result.

## Checks

- **Mandatory-reading precondition (014-A lessons):** recorded in `scope.md`, with conditioning now
  explicitly disambiguated (hybrid = ZigZag-move filter; native = MA-segment filter). PASS.
- **Conditioning / harami-anchor / descriptive-position / endpoint discipline:** entry = harami
  confirmation-bar real close (both objects); no position-in-move filter; binding endpoint = median;
  mean/trim/tail = P4 diagnostic, never a gate. PASS.
- **Holdout fence:** TRAIN-only F01 prefix (`load_train_1m` unchanged); never sorts/collects the full
  file; TEST + final-30% global holdout never read; forward scans clipped to `train_end_ts` →
  `DATA_CENSORED`. PASS.
- **Real-price discipline:** detection on HA candles; every outcome metric on real OHLC; MA(20,50) on
  real close; no HA price in any metric. PASS.
- **Dual-object individuality (Amendment 001):** hybrid (`H0`/`RH0`) and native (`M0`/`RM0`) carry
  separate arms, separate matched-random nulls, separate per-cell viability, separate P11 (P6 non-4h),
  and separate EVIDENCE_* readouts; `generalisation_readout` composes each object independently and
  **never pools them**; the phase verdict is the stronger object's (design §7). PASS.
- **Reconciliation roles (corrected P12):** native `M0` and `Z0` reproduce EXP-060B BENCH arms to
  `RECON_TOL = 1e-9` (a missing anchor remains a defect); hybrid `H0` has **no outcome anchor** — its
  ZigZag `/STRONG-STAT` conditioning mask is verified transitively via `Z0`'s exact reconciliation to
  EXP-053/060B `n_conditioned`. Matches the amendment. PASS.
- **RNG / reproduction safety:** `M0/RM0/Z0/RZ0` keep the original purposes (byte-identical to the
  prior run and EXP-060B); the new hybrid arms (`H0`: `PB_HSEG*`; `RH0`: `PB_RH0_*`) use disjoint
  dedicated purposes; per-cell seeding `(BASE_SEED, cell_index, purpose)` is order-independent.
  Determinism second-pass extended to `H0`/`RH0` and the `h0_rh0` contrast. Byte-identical across
  `--workers`. PASS.
- **Matched-count invariant, per object:** `RH0.draw_count == H0.m`, `RM0.draw_count == M0.m`,
  `RZ0.draw_count == Z0.m` (extended `_cell_invariants`). PASS.
- **Zero-baseline / power:** < 30 qualifying events → `NOT_VIABLE-by-power` per arm (non-reportable);
  worst-5% tail-share finite (0.0 on no negative mass). PASS.
- **Code conventions:** imports→constants→helpers→pure→plots→orchestration→`main`; output dirs created
  in `run()`; `tqdm` over instruments; bounded plotting from collected summaries (no reloads);
  vectorized resolvers reused; ProcessPoolExecutor with native-thread pinning; lines ≤100; compiles
  (`py_compile` OK). PASS.
- **Complexity budget:** 3 methods / 5 plots / 0 new `xen` modules — within scope. PASS.
- **Slot & ledger:** 0 candidate slots, 0 TEST reads; `native` mode already countable at G0; no new
  countable item; holdouts sealed; `test-read-ledger.md` unchanged. PASS.

## Verdict

```text
VERDICT: APPROVE
```

The dual-object re-run is consistent with Amendment 001, preserves the native/Z reconciliation, adds
the genuinely-new hybrid object with its own matched-random null, and reports both objects
individually. Cleared for the manual execution gate.
</content>
