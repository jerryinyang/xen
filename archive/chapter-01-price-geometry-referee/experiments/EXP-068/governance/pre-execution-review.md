# EXP-068 — Pre-Execution Governance Review

**Experiment:** EXP-068 — MA(20,50)-Substrate Native Combined Champion (Phase 015 S4/native)
**Family / hypothesis:** `CF-HA-HARAMI-001` / HYP-021 (native combined champion; merges old N1+N2)
**Checkpoint / D0:** `2026-06-17-015-ma-substrate-conditioned-harami-full-surface`
(`design.md` §3/§5/§7; `D0-predeclarations.md` P1–P12; **`D0-amendment-001-dual-parallel-substrate.md`**)
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`
**Date:** 2026-06-18
**Stage:** 4 (pre-execution) — consolidated pipeline governance.

---

## 1. Scope precondition gate (programme file-drawer control)

| Precondition | Status | Evidence |
|---|---|---|
| Candidate family `REGISTERED` | ✅ | `candidate-families/harami.md` — `REGISTERED`, OPEN (Phase 014 G0; carried OPEN post-G2). |
| `MA-SUBSTRATE` mode `native` registered | ✅ | `multiplicity-registry.md:456` — native mode **REGISTERED (Phase 015; 2026-06-17)**, elevated to parallel first-class by Amendment 001 (no new countable item). |
| `/EXIT-PARTIAL` (V2A) registered | ✅ | `multiplicity-registry.md:347` — REGISTERED (Phase 014-B). |
| `/ADV-NONE` registered (disclosed reference) | ✅ | `multiplicity-registry.md:342` — REGISTERED. |
| HYP-021 / EXP-068 listed as planned item | ✅ | `multiplicity-registry.md:492` — native combined champion, **0 / 0**, PLANNED. |
| New countable item introduced? | ✅ none | `V2A-ADVNONE` is the composition of two already-registered branches (`/EXIT-PARTIAL` V2A × `/ADV-NONE`); no new variant/detector/parameter branch. |
| TEST stratum read | ✅ none | TRAIN-only; native population byte-identical to EXP-060B/061 `M0` (8360-class); no new stratum; `test-read-ledger.md` requires no entry. |
| Mandatory 014-A lessons read recorded | ✅ | `scope.md` head records the 014-A conditioning/anchor/position/endpoint rules and how EXP-068 honours each. |

**0 candidate slots, 0 TEST reads** — consistent with the Phase 015 D0 (P9/P11) and Amendment 001.

---

## 2. Core constraint checks

### 2.1 Holdout / OOS discipline (REJECT-class if breached) — PASS
- `load_train_1m` reads Parquet metadata + the **first `train_rows`** file-order rows only
  (`train_rows = int(int(total*0.7)*0.7)`), never sorts/collects the full file, and asserts the
  slice is chronological by `CloseTime`. TEST and the final-30% global holdout are never sliced.
- Every domain bar is fenced `CloseTime ≤ train_end_ts`; every forward leg/cap scan is bounded by
  `last_train_idx`, and any window truncated by the TRAIN edge resolves to `PX_DATA_CENSORED`
  (excluded-with-record). No code path crosses the analysis cutoff.

### 2.2 Look-ahead / causality (REJECT-class if breached) — PASS
- MA(20,50) segmentation, `rd`, `M_sofar`, leg targets, and the adaptive cap come from
  `live_in_progress_state` / `live_strong_stat` on **confirmed prior MA segments** only; the
  per-cell `_causality_ok` gate asserts `seg.end_epoch[k] ≤ entry_epoch` and `end_idx ≤ entry_idx`
  for every valid in-progress reference (and the analogous ZigZag check for the hybrid mask).
- All exits are forward events bounded by `bench_n`; the ADV-NONE scan reads only
  `[entry_idx+1, min(entry_idx+bench_n, last_train_idx)]`.
- Alignment is by `CloseTime` epoch throughout (`_map_to_grid` exact-match), **never bar index**.

### 2.3 Real-price / synthetic-price discipline (REJECT-class if breached) — PASS
- Harami **detection** on HA candles (`generate_heiken_ashi` → `detect_ha_harami`); **every**
  outcome metric (`leg_levels_from_fracs`, P15 fills, `weighted_returns`, ATR normalisation) uses
  real OHLC (`real_ohlc`), and MA(20,50) is computed on **real close**. No HA price enters any
  metric. No Renko/brick prices in scope.

### 2.4 Single hypothesis / scope boundaries / criteria — PASS
- One falsifiable hypothesis: ≥1 of the two predeclared champion arms (`PARTIAL-V2A`,
  `V2A-ADVNONE`) satisfies the full G-015 conjunction (median-viable AND raw-mean-positive AND
  beats-RM-native) composed at P11+P6. Falsification path and the
  CHARACTERISED_NOT_VIABLE / MEAN_RECOVERABLE / EVIDENCE_FOR-surface / INCONCLUSIVE / DEFECT forks
  are all concrete and measurable. Boundaries (native binding object, 3 arms, 99-cell member grid,
  TRAIN-only, MA(20,50) fixed-not-swept) are explicit. Exclusions enumerate the deferred secondaries
  (recorded, not silent).

### 2.5 Complexity budget — PASS (at budget)
| Dimension | Scope budget | Implemented | OK |
|---|---|---|---|
| Statistical methods | ≤ 4 | 4: median CI; mean+10%-trim CI (+worst-5% tail-share); arm−RM independent contrast; arm−BENCH paired contrast | ✅ |
| Visualisations | ≤ 4 | 4: native median forest (+G-015 rings); arm−RM contrast heatmap (G-015 overlay); median-vs-mean-vs-trim P4 panel; G-015 conjunction tally | ✅ |
| New code modules | ≤ 1 (expected 0) | **0** — no `xen/` module added; `V2A-ADVNONE` is a NaN-adverse argument to existing `resolve_legs` | ✅ |

### 2.6 No academic-finance pitfalls — PASS
- Non-parametric throughout: regime-clustered moving-block bootstrap CIs (no normality /
  stationarity / IID / constant-vol assumption); median is the binding endpoint with the raw mean
  as a binding co-primary and the trimmed mean + tail-share as the P4 closure decomposition. Each
  method in `analysis-plan.md` carries a "why this method" + "simpler alternative considered" +
  assumptions block.

---

## 3. Implementation / developer-convention checks — PASS

- **Organization & sectioning:** imports → thread-pin → path setup → constants → conditioning-object
  config → arm specs → RNG purposes → types → I/O helpers → pure computation → plotting →
  orchestration → `main()`, with VAL-001-style separators. ✅
- **Import side effects:** `results/` and `plots/` created inside `run()` only; no I/O at import. ✅
- **Lazy loading / bounded memory:** lazy `scan_parquet` with column projection and `slice` before
  `collect`; per-cell arrays released (`del cell`); forward scans bounded by `bench_n`; plots built
  from collected per-cell row dicts (no reloads / no large pandas conversion). ✅
- **Progress / logging:** `tqdm` over the 17-instrument outer loop; concise `logging` only in
  orchestration/`main()`; helpers return data. ✅
- **Zero-baseline handling:** tail-share returns `0.0` (finite) when no negative mass; cells with
  `m < 30` are NOT_VIABLE-by-power (never a ratio); first-hit `r` defined for the single-leg BENCH
  arm only. ✅
- **Determinism / reproducibility:** fixed per-cell RNG `default_rng([BASE_SEED, cell_index,
  purpose])`; two-pass `determinism_replay`; output documented byte-identical across `--workers`
  (order-independent seeding + fixed-order reassembly). ✅
- **Safe optimization / vectorization discipline:** the multi-leg resolver loops are kept explicitly
  sequential (the causal/streaming object under test — `position_exits` mandates "never vectorize");
  the ADV-NONE branch changes **no** sample membership, ordering, denominator, or metric — it only
  suppresses the adverse-stop test by passing an all-`NaN` adverse level. ✅
- **Phase alignment:** matches `design.md` §5 (S4 native combined champion, mirrors EXP-060) and the
  Amendment 001 slate (native binding; hybrid disclosed; EXP-069 dropped). The code emits a
  **mechanical, explicitly non-binding** native readout and does **not** adjudicate G-015 (left to
  results.md), honouring P9's single-terminal-gate rule. ✅

### 3.1 P12 reconciliation wiring (SUBSTRATE/METHOD_DEFECT guards) — PASS
- Native `BENCH` ↔ EXP-061 `M0`, hybrid `BENCH` ↔ EXP-061 `H0` (anchor loader returns 99 cells),
  native `PARTIAL-V2A` ↔ EXP-066 native `PARTIAL-V2A` (anchor loader returns 99 cells), each per-cell
  `m` + median to `RECON_TOL = 1e-9`; a missing anchor or any mismatch sets `is_defect`. RNG-purpose
  preservation verified: `arm_pb('nat','PARTIAL-V2A')['med'] == 100020` (EXP-066 block);
  `V2A-ADVNONE` uses a fresh block `≥ 300000`; BENCH reuses EXP-061/066 purposes. Reconciled
  medians/m are RNG-independent (deterministic from data), so reproduction holds.
- ADV-NONE structural invariant wired: `advnone_no_stopout` asserts **zero** adverse stop-outs for
  the `V2A-ADVNONE` signal and its null (MA cap is the only stop). Verified on a synthetic event:
  the 1:1 arm stops out (3× `PX_ADV`) while the ADV-NONE arm reaches all favourable targets
  (3× `PX_FAV`, `adv_count = 0`).

---

## 4. Static verification performed (no experiment execution)

- `py_compile`: OK. `ruff`: clean except the **intentional** E402 (library imports after the native
  thread-pin block — identical to the frozen EXP-066 pattern and required for thread pinning).
- Module imports in the project venv; arm specs, `OBJECT_ARMS`, `CHAMPION_ARMS`, RNG purpose blocks,
  and both reconciliation anchors (99 cells each) validated.
- Synthetic resolver smoke test confirms the ADV-NONE no-adverse semantics (see §3.1).

---

## 5. Info notes (non-blocking; for Stage 7 documenter)

1. `candidate-families/harami.md:456` still carries the **pre-amendment** native-mode wording
   ("Co-investigated, bounded"). Amendment 001 §5 calls for re-describing it as *parallel
   full-surface*. The item **is** registered and countable (precondition met); this is a
   documentation refresh for Stage 7, not a Stage 4 blocker.
2. The code's mechanical native readout strings (e.g. `PROCEED_TO_SCREEN_CANDIDATE`) are explicitly
   labelled non-binding; the G-015 gate adjudication belongs in results.md after the full slate.
3. E402 on the matplotlib/polars/numpy imports is the deliberate thread-pinning convention; no fix
   required.

---

## Verdict

```text
VERDICT: APPROVE
```

All core constraints (holdout, look-ahead/causality, real-price discipline, single-hypothesis
scoping, complexity budget, non-parametric methods) pass. The implementation matches the approved
analysis plan exactly, adds no `xen/` module, preserves EXP-061/EXP-066 reproduction byte-for-byte,
wires all three P12 reconciliation anchors and the ADV-NONE no-stopout invariant, and does not
adjudicate G-015. Registry preconditions are satisfied with 0 candidate slots and 0 TEST reads.
