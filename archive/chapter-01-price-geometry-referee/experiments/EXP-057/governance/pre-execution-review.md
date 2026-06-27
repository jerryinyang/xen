# EXP-057 — Pre-Execution Governance Review

**Experiment:** EXP-057 — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)
**Phase / checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B; G0-B PASS 2026-06-15)
**Family / candidate:** `CF-HA-HARAMI-001` (REGISTERED, OPEN) · HYP-010
**Reviewed artifacts:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `xen/adverse_targets.py` (new module)
**Date:** 2026-06-16

---

## Registry & ledger precondition (Stage-1/Stage-4 gate)

| Check | Result |
| --- | --- |
| Family `CF-HA-HARAMI-001` REGISTERED | PASS — `candidate-families/harami.md`, OPEN |
| Experiment registered | PASS — `multiplicity-registry.md` line 385: `CF-HA-HARAMI-001/HYP-010` — **EXP-057**, PLANNED, 0/0 |
| Branches registered | PASS — `/ADV-EXTREME` (line 341) and `/ADV-NONE` (line 342) both REGISTERED; raw/rr1 are the two predeclared forms of the registered `/ADV-EXTREME` branch (family spec line 262 "optional ≥1:1 R:R constraint") — not new countable branches |
| New predeclared parameters | PASS — buffer `0.25·ATR`, `ADV_FLOOR 0.10·ATR`, `∓∞` sentinel are within the registered branches; declared in scope §Parameters and the D0 addendum lineage, not tuned |
| TEST stratum read | NONE — TRAIN-only; no `test-read-ledger.md` tally applies; global holdout sealed; conditioned population already had first TRAIN contact in EXP-053 |
| Slot accounting | PASS — 0 candidate slots, 0 TEST reads (014-B characterization; P21 forbids slot consumption before G2) |

## Mandatory-reading precondition (014-B binding)

PASS. `scope.md` opens with the explicit confirmation that
`014-A-conditioning-gap-and-validation-lessons.md` was read in full, and records compliance with the
four binding rules: (a) conditioning — measures the live `/STRONG-STAT`-conditioned harami (binding),
`/STRONG-HA` disclosed; (b) harami-anchor — entry at the harami confirmation-bar real close, not the
ZigZag confirmation; (c) position-in-move descriptive-only — the `/ADV-EXTREME` reference is the causal
running extreme of the in-progress move, never EXP-050's metric or an unconfirmed pivot; (d) expectancy
endpoint (P14) binds, first-hit `r` disclosed-only. Phase alignment confirmed (014-B §5 surface read 2).

## Scope (`scope.md`)

| Check | Result |
| --- | --- |
| Single falsifiable hypothesis | PASS — one question (does an alternative adverse geometry beat benchmark 1:1 on median expectancy?), explicit falsification |
| Boundaries explicit | PASS — data views, 99-cell grid, TRAIN range, instruments, exclusions, 4-variant set all stated |
| Success/failure/inconclusive | PASS — EVIDENCE_FOR/AGAINST/INCONCLUSIVE/DEFECT all concrete and measurable |
| Holdout exclusion | PASS — final-30% never loaded; nested TEST not read; F01 prefix slicing |
| Real-price discipline | PASS — detection on HA candles; every metric (`M_sofar`, faded extreme, barriers, fills, returns, `r`) on real OHLC |
| Metric denominators / zero-baseline | PASS — qualifying = built-barrier FAV/ADV/TIMECAP; `<30` → NOT_VIABLE_BY_POWER (never a ratio); degenerate `r` for `/ADV-NONE` disclosed and non-binding |
| Complexity budget | PASS — 4 stat methods / 5 plots / 1 module |

## Analysis plan (`analysis-plan.md`)

| Check | Result |
| --- | --- |
| Method justification + simpler alternative | PASS — every step carries "why" + "simpler alternative considered" |
| Non-parametric, no academic-finance pitfalls | PASS — median moving-block bootstrap; no normality/stationarity/i.i.d. assumption; paired contrast for correlated arms |
| Timestamp alignment | PASS — exact `CloseTime` match (searchsorted + equality), never bar index |
| Interpretation guide pre-defined | PASS — mechanical EVIDENCE_* fork frozen before results |
| Multiplicity posture | PASS — report-all 4 variants, P11 breadth, family-wise correction deferred to single G2; no within-experiment Holm |
| Budget compliance | PASS — 4 / 5 / 1 |

## Code (`code/run_experiment.py`, `xen/adverse_targets.py`)

| Check | Result |
| --- | --- |
| Plan compliance | PASS — 4 binding variants (BENCH/raw/rr1/NONE), benchmark favourable+cap+P15 held fixed, paired binding contrast, two disclosed P13 baselines per variant, P11 composition, mechanical EVIDENCE_* |
| Holdout exclusion | PASS — `load_train_1m` slices first `int(int(total*0.7)*0.7)` file-order rows on a lazy scan; full file never sorted/collected; every domain bar fenced to `CloseTime ≤ train_end_ts` |
| Look-ahead prevention | PASS — faded-extreme span `[start_idx+1 … entry_idx]` (start = `EndTime_k` of a move confirmed `≤ t_i`); `cell_causality_ok` asserts `end_idx[k] ≤ entry_idx`, `end_epoch[k] < entry`, entry bar `≤ t_i`; first-touch scan starts at `entry_idx+1`, clipped to the data edge (`DATA_CENSORED`) |
| Real-price outcome | PASS — HA prices only in `detect_ha_harami`/`annotate_ha_impulse`; `TickVolume` loaded for aggregation parity but enters no metric |
| Sequential vs vectorized | PASS — P15 resolver, in-progress walk, and the faded-extreme scan kept explicit/bounded; only bootstrap index construction / MA segmentation vectorized |
| `/ADV-NONE` sentinel safety | PASS — `±∞` adverse level; resolver comparison yields `adv_hit=False`, no NaN; invariant `n_ADV(ADV-NONE)==0` asserted across all arms+baselines |
| Predeclared invariants (Step 9) | PASS — (1) BENCH reproduces EXP-053 `m`+median to 1e-9 (`exp053_reconciliation`, defect if unavailable/zero-checked); (2) `raw adv_dist ≤ rr1 adv_dist` event-wise; (3) `/ADV-NONE` 0 ADV; (4) raw adverse-side ordering `rd·(C−adv)>0` — all wired to `is_defect` |
| Determinism | PASS — fixed `BASE_SEED`, per-(cell,variant,purpose) RNG streams; `determinism_replay` re-runs first usable cell per instrument across binding variants + both baselines |
| NaN / edge cases | PASS — `errstate` guards, `isfinite`/`>0` gates; empty-cell, empty-move, empty-pool, `<30`-event paths handled |
| Organization / sectioning / imports | PASS — imports → path setup → constants → types → I/O → pure computation → plotting → orchestration → `main()`; VAL-001 separators; dirs created only in `run()`; no import side effects |
| Logging / progress | PASS — `logging` + concise summary; `tqdm` over the 17-instrument outer loop; helpers quiet |
| Plot memory / reuse | PASS — 5 bounded plots from collected per-cell summaries + pooled viable-cell returns; no reloads |
| Module reuse | PASS — one new module `xen/adverse_targets.py`; resolver, fills, returns, bootstrap, contrasts, ZigZag, harami, strong-move, time-cap, aggregator all reused |

## Verification performed

- `python -m py_compile` on both files — OK.
- Import resolution of all reused `xen` modules + the new module — OK.
- Synthetic unit test of `xen/adverse_targets.py` — faded-extreme min-Low/max-High over the causal span,
  entry==start edge case, buffer direction (long below / short above), `raw adv_dist ≤ rr1 adv_dist`
  (including the tight-stop widen case), `/ADV-NONE` `±∞` by direction, and warmup/unavailable
  propagation all pass.

## Issues

None Critical or Warning. The only Info note: `TickVolume` is loaded into the TRAIN frame purely to keep
domain aggregation byte-identical to EXP-053/056 (the BENCH reconciliation anchor); it is correctly
excluded from every metric. Acceptable.

---

```text
VERDICT: APPROVE
```
