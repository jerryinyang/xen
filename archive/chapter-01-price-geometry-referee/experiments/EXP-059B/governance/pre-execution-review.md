# Pre-Execution Governance Review — EXP-059B

**Experiment:** EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)
**Family / HYP:** `CF-HA-HARAMI-001/HYP-012b` (Phase 014-B; follow-up to EXP-059)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, the extension to
`python/src/xen/position_exits.py`, and the 014-B checkpoint / signal-registry updates.
**Date:** 2026-06-16. **Reviewer:** research-pipeline consolidated governance (Stage 4).

---

## Constraint checks

### Scope (`scope.md`)
- **Single falsifiable hypothesis** — ✅ one question (does an uncapped, no-initial-stop structure
  trailing model beat the benchmark single fixed exit on conditioned median expectancy?), with an
  explicit falsification rule.
- **Boundaries / exclusions** — ✅ 99-cell member grid, TRAIN-only (F01 prefix), gross, real prices;
  TEST and the final-30% global holdout explicitly excluded; favourable/horizon/other-adverse levers
  explicitly out of scope.
- **Holdout exclusion** — ✅ stated; forward scans clip to `train_end_ts` → `DATA_CENSORED`.
- **Real-price discipline** — ✅ HA candles for harami detection only; every metric on
  `RealOpen/High/Low/Close`.
- **Measurable criteria** — ✅ EVIDENCE_FOR / AGAINST / INCONCLUSIVE / DEFECT defined mechanically
  (P11 ≥5 cells/≥3 instruments, CI_low>0, ≥30 events). Success is attainable in principle; the
  acknowledged likely INCONCLUSIVE-by-power (uncapped censoring) is a valid predeclared outcome, not
  an unattainable goalpost. No percentage-vs-zero-baseline comparison (absolute median + paired
  contrast). Denominators defined (<30 → NOT_VIABLE_BY_POWER; separated censoring).
- **014-B mandatory-reading precondition** — ✅ `scope.md` records that
  `014-A-conditioning-gap-and-validation-lessons.md` was read and honours conditioning / harami-anchor
  / descriptive-position / expectancy-endpoint. (Stage-4 REVISE trigger satisfied.)
- **Signal-registry precondition** — ✅ the new countable variant `/EXIT-TRAIL-UNCAPPED` is registered
  in `multiplicity-registry.md` (Registered variant surface + the EXP-059B/HYP-012b batch row) and in
  `candidate-families/harami.md`, before any result-producing code. No TEST stratum is read, so no
  `test-read-ledger.md` entry is required (the scope states this and the conditioned population is
  byte-identical to EXP-053's already-contacted TRAIN stratum).

### Analysis plan (`analysis-plan.md`)
- **Method justification** — ✅ each step gives "why this method" + "simpler alternative considered" +
  assumptions; methods are the EXP-056/057/058/059 family (moving-block median bootstrap, paired
  contrast, P13 baselines).
- **No academic-finance pitfalls** — ✅ non-parametric throughout; the moving-block bootstrap respects
  serial/regime dependence; no normality/stationarity/i.i.d./constant-vol assumption. The median
  endpoint (P14) is justified against the fat-tailed return distribution that the no-initial-stop
  model widens.
- **Timestamp alignment** — ✅ all views aligned by `CloseTime`; no bar-index cross-view.
- **Interpretation guide pre-defined** — ✅ if-X-then-Y rules set before results, including the binding
  rule that the separated `DATA_CENSORED` disclosure gates interpretation of the vs-BENCH contrast.
- **Budget** — ✅ 4 statistical methods / 5 visualisations / 0 new modules (extends `position_exits`).

### Code (`code/run_experiment.py` + `position_exits.py` extension)
- **Plan compliance** — ✅ implements the 5 arms, both paired contrasts, P13 baselines, P11
  composition, separated censoring, holding duration, and the 7 invariant + determinism + EXP-053
  anchor checks exactly as planned; no out-of-plan analyses.
- **Holdout / look-ahead** — ✅ F01 prefix slice only (`load_train_1m`); the full file is never sorted
  or collected; every domain bar fenced to `CloseTime ≤ train_end_ts`; the uncapped scan runs to
  `last_train_idx` and censors at the edge; the trailing stop reads only secondary confirmations with
  `ConfirmIdx ≤ i`; a runtime `_causality_ok` gate asserts strict grid + reference-move ≤ entry.
- **Real-price discipline** — ✅ all exits are real-bar P15 fills; HA only locates the harami.
- **Memory / performance (the scope's flagged risk)** — ✅ the uncapped resolver computes the trailing
  stop **lazily** inside the scan (advancing secondary-confirmation pointer); it does **not** call the
  dense `build_active_stops`, so the `O(n_events × train_len)` array blow-up is avoided. The
  sequential scan is bounded by `last_train_idx`, documented "do not vectorize", and carries the
  correct causal semantics. `tqdm` over the 99-cell grid; bounded per-cell memory.
- **Frozen-function integrity** — ✅ additive-only. At first review `resolve_legs`, `build_active_stops`,
  and `_scan_event` were byte-identical and the new `resolve_legs_uncapped`/`_scan_event_uncapped` were
  added alongside. The post-review F04 remediation (see "Adversarial-findings remediation" below)
  extended `_scan_event`/`resolve_legs` and `resolve_path_ordered`/`_scan_path` with an **additive**
  exit-offset return / optional out-param: the returned classes/prices and every downstream metric are
  unchanged whether or not the new argument is supplied, so EXP-059's frozen results and the
  BENCH/capped-sibling reproduction remain unaffected (confirmed: existing `tests/` suite green; all
  EXP-049/053–059 callers unpack the unchanged 2-tuples). The exact post-fix resolver source is now
  pinned by `resolver_source_sha256` in `run_metadata.json` (F06).
- **Invariant coverage** — ✅ includes the two uncapped-specific gates required by the plan:
  (Step 13.6) uncapped arms emit **no** `PX_TIMECAP`; (Step 13.4) the lazy uncapped stop reproduces
  the dense capped (no-init) stop on the shared `[entry+1, entry+bench_n]` prefix to ≤1e-9 — both
  asserted per cell. BENCH-reproduces-EXP-053 anchor retained.
- **Quality** — ✅ type hints, docstrings, VAL-001 sectioning, no import-time side effects (dirs in
  `run()`), concise logging, fixed seed + determinism replay. Compiles; ruff-clean; no line >100.
  Behavioural spot-checks confirm a correct trailing fill (`PX_TRAIL` at the right bar), no `TIMECAP`,
  `DATA_CENSORED` at the edge, and lazy==dense stop on the prefix.

### Phase alignment
- ✅ EXP-059B is a 014-B surface follow-up (HYP-012b), 0 candidate slots, 0 TEST reads, gross,
  TRAIN-only; it joins the **single 014-B G2** with no intermediate gate and no closure — consistent
  with the checkpoint design (`014-B-design.md` §4/§8/§10 addendum, `014-B-D0-addendum.md` P21). It
  does not displace EXP-060 (combined event system, HYP-013), which keeps its planned slot.

## Acknowledged items (Info — not blocking)

1. **Capped no-init sibling arms** (`TRAIL-PURE-NOINIT-CAPPED`, `COMBINED-V2A-NOINIT-CAPPED`) are
   configurations of the already-registered `/EXIT-TRAIL-STRUCT` branch that EXP-059 did not run as
   exact arms. They are **disclosed-only reference siblings** whose sole purpose is the cap-isolation
   contrast; the code enforces that **only the uncapped (binding) arms can score a P11 WIN**
   (`win = ... and a.kind == KIND_UNCAPPED`). They therefore cannot become a "remembered winner" and
   do not inflate file-drawer multiplicity — analogous to EXP-059's disclosed `/STRONG-HA`/MAD arms.
   The binding countable claim (`/EXIT-TRAIL-UNCAPPED`) is registered. No separate registry line is
   required for the disclosed references; this rationale is recorded for the post-experiment review
   and G2.
2. The cap-isolation contrast reuses `paired_median_contrast_ci` (the same method, a different arm
   pair) — within the 4-method budget, as the plan states.

## Adversarial-findings remediation (post-review, pre-execution)

An adversarial review (`bmad-review-adversarial-general`) of the unexecuted experiment raised seven
findings; the actionable code/doc fixes were implemented before the manual execution gate. F01
(experiment not yet executed) and F05 (vs-BENCH contrast on the uncensored common subset — already
disclosed) require no code change.

1. **F02 — cap-isolation contrast was structurally degenerate.** The uncapped arm and its capped no-init
   sibling exit byte-identically for any event resolving within `bench_n` (identical no-init trailing
   stop + P15 path on the shared prefix), so a paired-median contrast over the *full* common subset
   collapses toward 0 from structural zeros — not evidence the cap is irrelevant. Fix: the cap-isolation
   contrast now reports both the full-common contrast (`capiso_full_*`, retained for continuity) **and**
   the **divergent-subset** contrast (`capiso_div_*` — events the uncapped arm held *past* `bench_n`,
   the only events whose exit can differ) with `capiso_div_share`. The divergent contrast is the
   interpretable read; the plot and `composition_readout.json` `cap_isolation` summary use it, and the
   note warns that a near-zero full contrast on a small divergent share is not a null cap effect.
2. **F03 — O(train_len) invariant re-resolutions.** The per-cell `_cell_invariants` re-ran the uncapped
   resolver three times over the *full* conditioned population. Fix: those structural checks now run on a
   bounded, deterministic, evenly-spaced sample of up to `INVARIANT_MAX_EVENTS=1500` events
   (`_subsample_mask`); the cheap dense-bounded monotone + lazy==dense-prefix checks still run on the
   full population. Disclosed in `run_metadata.json` `invariant_gates`.
3. **F04 — holding-duration comparator was the cap ceiling.** BENCH/capped arms reported `bench_n` as
   their hold (an upper bound), biasing the "extra holding the uncapped model buys" diagnostic. Fix:
   `resolve_path_ordered`/`_scan_path` and `resolve_legs`/`_scan_event` return the **measured** resolving
   exit offset (additively); every arm now reports its true holding duration.
4. **F06 — resolver integrity was convention-only.** `run_metadata.json` now records
   `resolver_source_sha256` (SHA-256 of each frozen + uncapped resolver's source) to pin the post-fix
   baseline so a later silent edit is detectable.
5. **F07 — the uncapped region (offset > `bench_n`) had no external oracle.** Added
   `tests/test_position_exits_uncapped.py`: hand-derived ground-truth for a trailing fill past offset 6,
   DATA_CENSORED at the TRAIN edge, no-TIMECAP, shared-stop binding all open V2A legs, lazy==dense on the
   shared prefix, and F04 additivity (5 tests, green).

The fixes touch the disclosed cap-isolation contrast, the invariant runtime, the holding-duration
diagnostic, and test/metadata coverage — none changes the binding endpoint, the conditioned population,
the BENCH/capped/uncapped exit semantics, or any verdict logic. The verdict below stands; re-run the
manual execution gate to produce results.

## First-execution correction + performance (post-review)

The first full execution returned `SUBSTRATE_METHOD_DEFECT` on a single gate — `invariant_violations:
["GBPUSD-2h", "AUDUSD-5m"]` (determinism, causality, and the EXP-053 anchor all passed). Root cause: a
conditioned harami entered on the **very last TRAIN bar** (`entry_idx == last_train_idx`) has zero
forward room, so `_scan_event_uncapped` correctly returns offset 0 with all legs `DATA_CENSORED` — but
the `edge_ok` invariant required `off >= 1` and flagged this correct edge-censoring as a violation. Fix:
`_edge_ok` now skips the `off >= 1` requirement for an event whose legs are **all** `DATA_CENSORED` at
offset 0 (the only way offset 0 arises). Both flagged cells re-verified to pass all seven invariants
(GBPUSD-2h and the heavy AUDUSD-5m), so a re-run produces no `invariant_violations`; the verdict then
reflects the measured results, not a defect.

**Logic-preserving speed-ups** (the first run took ~31 min; the determinism replay re-ran the heavy 5m
cell twice per instrument — ~56% of wall-clock): (i) the determinism + reconciliation guard now runs on
the **lightest** member cell per instrument (any non-empty BENCH-powered cell validates a code property)
and recomputes **once** vs the live cell instead of twice; (ii) the 17 instruments — independent and
seeded by `cell_index`, so order never affects results — run across worker processes
(`ProcessPoolExecutor`, `XEN_WORKERS` override, serial fallback at `XEN_WORKERS=1`). Both were validated
**byte-identical to serial** (`parallel == serial` records confirmed on NZDUSD + AUDJPY; per-cell seeds
unchanged). No computation, endpoint, population, or verdict logic is altered — only execution venue and
which cell carries the determinism check.

## Verdict

```text
VERDICT: APPROVE
```

All core constraints pass with no Critical or Warning findings. The mandatory-reading precondition and
the signal-registry precondition are satisfied; the holdout is sealed; causality and real-price
discipline hold; the flagged memory risk is correctly avoided by the lazy resolver; the frozen EXP-059
machinery is untouched; and the uncapped-specific invariants (no `TIMECAP`; lazy==dense prefix) are
asserted. Proceed to the manual execution gate.
