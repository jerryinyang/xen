# INFR-020 — QA run 6 fix map (2026-07-21)

Issue → change → where. Written for the fresh QA that verifies these; every number below is
from the re-emitted artifacts, not from prose.

| Issue | Fix | Location |
|---|---|---|
| **I-1** level availability + refusal | Level rows carry `available_mins_since` (IB edges = `ib_minutes`, prior-session levels = 0) and `level_source_bar_minutes`. W5 computes `mins_since = candidate.OpenTime − anchor_ts`; a pre-IB candidate is measured against prior-session levels only, and is **refused** when the nearest level over the full set would have been an IB edge. Counts emitted per (symbol, pair). | `ltf.py` `structural_levels_1m` / `_finalise_levels`; `run_apparatus.py` W5 candidate loop |
| **I-2** asserts off the emitting path | `assert_split_additive`, `assert_bar_causality` (rewritten vectorised — one re-bucket + join, no per-row filter), `assert_no_forward_provenance` now run in W2 on every aggregated frame; `assert_windows_complete` + provenance on W1/W3/W5 COMPLETE frames; `assert_no_per_level_delta("Volume")` in the level builder; every JSON artifact key-checked at write via `emit_json`; `assert_levels_from_1m` rewritten to *trace* provenance (measured spacing of the source series via `infer_bar_minutes`, and the emitted frame's stamped column) instead of echoing a literal. | `ltf.py`, `fences.py`, `run_apparatus.py` |
| **I-3** battery scope + pin | `a2(full=True)` traverses all 137 pinned blocks; `--full` runs A1 over all 194. `pins.json` records `reproduction_battery.json`'s hash plus a `battery` block, and **raises** if a `--full` run finds anything but a passing full battery. | `reproduction_battery.py`, `run_apparatus.py` |
| **I-4** unreachable gap class | Design §2 W2a now states `GAP_CONTAMINATED` is provably empty for day-aligned windows over whole-day gaps and names `gap_excision_report.json` as the live disclosure (AMENDMENT-16). No code change — the excision behaviour was already correct. | `design.md` |
| **I-5** unpinned D1 thresholds | New W3b step emits `class_thresholds_1m.json` for all 194 (residuals against the frozen INFR-017 1m pin, no re-fit) and raises on any drift against the 137 registry blocks. W5's D1 branch consumes it instead of deriving inline. | `run_apparatus.py` `w3b_thresholds_1m` |
| **I-6** prior-session identity | `prior_htf_session_ranges` now maps each consumer anchor to its **calendar-adjacent** predecessor (the level set's rule), never `shift(1)` over sessions that happen to hold bars. Anchors whose predecessor traded nothing get a null range and are counted (`n_sessions_prior_missing`). | `ltf.py` |
| **I-7** vacuous battery members | A2's identity check replaced with a discrimination test (real estimator matches the pin; a p89 lookalike does not). A5b promoted from prose to a measured assert against `xen.bar_aggregator.aggregate_ohlc`. | `reproduction_battery.py` |
| **I-8** blocklist vocabulary | Added this programme's outcome names (`ret_bps`, `ret_norm`, `trap_load`, `mfe_rev_norm`, `mae_rev_norm`, `bite`, `edge_bps`, …) plus a prefix/token rule. Prefixes are underscore-terminated so `retention` is not swept up. | `fences.py` |
| **I-9** silent drops / disclosures | Degenerate IB sessions flagged not dropped (`ib_degenerate`, counted as `n_sessions_ib_degenerate`); `null_scale_volume_cells` at 5/15/60m and a new `one_minute` block in the coverage report; ledger reconciliation fields in `gap_excision_report.json`; `measurable: false` on every skip path instead of a bare `n_candidates: 0`; `assert_windows_complete` now has one implementation (`fences` delegates to `ltf`); dead `inv` removed. | `ltf.py`, `fences.py`, `run_apparatus.py` |

## Process defect found and fixed during the fix run

A 5-symbol smoke run wrote into `results/`, replacing the full-universe W1/W3 artifacts; the
next `--from-w5` run then reused 5 symbols and produced a census with D2 = 238 candidates.
Caught by comparing against QA-6's recorded totals. `--out-dir` added so a sample run cannot
overwrite pinned artifacts; the full pipeline was rebuilt end to end (W1→W5, no `--from-w5`).

## Re-emitted state (full universe)

* battery: `mode: full`, `all_ok: true`, A1 over 194 (no metric errors), A2 over all 137
* baselines 194 symbols / 2,216,256 rows; thresholds 194; `class_thresholds_1m.json` 194 with
  137 registry-overlap checks passing; census 194
* candidates and refusals — D1 95,836 (692 pre-IB, 510 refused, 95,264 measured, 1 unmeasurable);
  D2 9,497 (2,390 / 1,109 / 8,388); D3 2,974 (191 / 111 / 2,862); D4 640 (32 / 18 / 614)
* coverage unchanged from the published universe table: median retention 0.3851 / 0.2011 / 0.0882;
  usable at the 0.50 floor 72 / 47 / 31; ≥0.90 20 / 11 / 6; <0.20 28 / 95 / 132
* gap ledger reconciliation: BNXUSDT + GSTUSDT are ledger misses; 31 instruments ledger-flagged
  with zero in-band day-holes

---

# QA run 7 fixes (2026-07-21)

| Issue | Fix | Location |
|---|---|---|
| I7-1 (MAJOR) D4 IB nesting false | Availability + session membership decided at the bar's **close** (session = anchor of last source minute; IB available when `close − anchor ≥ ib_minutes`). D4's 13:30 anchor no longer mis-times the test. Straddling bar assigned to the session it ends in; `n_candidates_straddling_anchor` published. Design §1.1 corrected. | `run_apparatus.py` W5, `design.md` AMENDMENT-19 |
| I7-2 (MOD) refuse-whole-bar vs per-kind events | Operator decision: keep the bar, drop only the unformed IB edge from its level set. | `run_apparatus.py` W5 |
| I7-3 (MOD) silent drops, identity broke | Degenerate IB no longer suppresses prior-session levels; `n_candidates_no_levels` added so `n_candidates == n_measured + n_no_levels + n_unanchored`. | `ltf.py structural_levels_1m`, `run_apparatus.py` |
| I7-4 (MOD) silent run-local refit | Missing pinned MTF baseline → cell `measurable: false`, no refit. | `run_apparatus.py` W5 |
| I7-5 (MOD) out-dir/battery + from-w5 coverage | `--out-dir` threaded into `run_battery`; `--from-w5` asserts on-disk W1/W3 cover the run's universe by name. | both scripts |
| I7-6..I7-9 (MINOR) | VT-4(g) demoted to declared; `pins.json` + battery routed through the key-checked writer; pin stamped at write with battery module scope; literal `assert_no_per_level_delta` echo removed (real enforcement in `profile.py`). | `design.md`, both scripts |

# QA run 8 fixes (2026-07-21)

| Issue | Fix | Location |
|---|---|---|
| I8-1 (MAJOR) self-made IB edge | Carry INFR-018 `ib_high_ts`/`ib_low_ts` as `formed_ts`; a level with `formed_ts ≥ bar.OpenTime` is excluded (the bar's own minutes made it). `n_ib_edge_self_made_excluded` published. | `ltf.py session_ib_from_1m` / `structural_levels_1m` / `available_levels_for_candidates` |
| I8-2 (MAJOR) no shared availability impl | Extracted `assign_candidate_sessions` + `available_levels_for_candidates` into `xen.sigbar.ltf`; W5 and SPDR-009 both import; runner no longer hand-codes the rule. | `ltf.py`, `run_apparatus.py` |
| MOD (from-w5 provenance) | Full re-emit run **without** `--from-w5`, so W1–W4 are also produced by the shipped code — no earlier-code artifacts in the pin. | run invocation |
| I8-3 (MOD) counter definition | Define `n_ib_edge_unavailable` as the subset whose nearest full-set level is an unavailable IB edge; `n_candidates_pre_ib` remains the full pre-IB count. | `design.md` §1.1 |
| I8-5/6 (MINOR) count check / orphan import | Compute `n_candidates_unanchored` from the unjoined candidates and raise if the count identity fails; remove the unused import. | `run_apparatus.py` W5/imports |
| I8-7 (MINOR) duplicate level-set plan | SPDR-009 imports `structural_levels_1m` and the two availability functions rather than recreating a D1 path. | `SPDR-009/design.md` §3.1/§9 |
| I8-8/9 (MINOR) amendment direction / revision | Rebook AMENDMENT-19 as looser with a tightening leg and advance the design to revision 6. | `INFR-020/design.md` header/§8 |

# QA run 9 fixes (2026-07-21)

| Issue | Fix | Location |
|---|---|---|
| R9-1 (MAJOR) D4 prior levels overlap the candidate | Every level kind now requires non-null `formed_ts`. Prior extrema carry their first edge-setting minute; POC/VAH/VAL carry the last contributing 1m source minute. Missing provenance fails closed. Separate IB/prior/any self-made counters expose the affected populations. | `ltf.py structural_levels_1m` / `available_levels_for_candidates`; `run_apparatus.py` W5 |
| Related: D1 sensitivity schema drift | Both W5 artifacts must carry the full count schema, `measurable`, straddling count, zeroed unmeasurable cells, and the candidate identity. The runner raises before writing on any omission. | `run_apparatus.py _assert_census_schema` |
| Regression coverage | Added a pinned GMXUSDT D4 straddling regression (A11), fail-closed provenance check, tied-extreme timestamp test, and synthetic straddling-profile test. | `reproduction_battery.py`; `python/tests/test_sigbar_infr020.py` |

Clean full rebuild: `results/full_run_qa10.log`, no `--from-w5`, terminal
`{"ok": true, "n_symbols": 194}`. All 9 hashes match; battery `mode: full`,
`all_ok: true`, 194 symbols. Census self-made candidate counts after first-formation tie handling:
D1 IB/prior/any = 399/0/399; D2 = 1,777/0/1,777; D3 = 191/0/191;
D4 = 66/43/66 with 43 anchor-straddling candidates. Coverage remains
0.38505/0.20110/0.08815, usable 72/47/31.
