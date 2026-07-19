# QA review — XENA-EPSOSC-002 (CF-EPSOSC-001)

## QA run 1 — 2026-07-18T01:33Z — mode: subagent — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc
Verdict: **APPROVE** (with 2 non-blocking documentation notes; both are stale numbers in prose, not code/behaviour defects)

Reviewed git state: HEAD `eaea177`; working tree carries untracked `python/experiments/XENA-EPSOSC-002/` (the frozen design + freeze artifacts under review). Fresh-context self-check PASS — this context did not produce the implementation.

Stage context: this is the Stage-2 QA gating EXECUTION. The Stage-3 002 strategy does not exist yet (expected pre-gate); it will reuse `python/experiments/XENA-EPSOSC-001/code/epsosc_strategy.py` restricted to RET_ANCHOR. Fidelity trace covers (a) the frozen `design.md`, (b) the freeze machinery (`build_universe.py`, `freeze_diagnostics.py` + emitted results), (c) the design→(reused-001-strategy) plan.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §4.1 axis: ≥90 membership-days on shifted window [2022-07-01,2023-12-18], rule_hash 0dd53037 | build_universe.py:79,199-209,282; reslice_membership:182-196 | MATCHES | 19 symbols, 152 binding cells; `n_unique(rebalance_ts) ≥ 90` |
| §4.1 002 axis ⊆ 001 axis (asserted) | build_universe.py:287-293 | MATCHES | Hard `RuntimeError` if not subset; passes on re-run |
| §4.1 rule_hash 0dd53037 pinned | build_universe.py:114-130; selection_rule.json | MATCHES | `rule_hash(rule)` recomputed == PIN_RULE_HASH, else raises |
| §4.2 RET_ANCHOR-only 8/symbol grid; HYBRID+STRETCH dropped | build_universe.py:82-83,234-251,302-303 | MATCHES | `CLEARS_BINDING=("RET_ANCHOR",)`; 2×2×1×2=8; asserts n_bind==8×n_sym; no STRETCH object |
| §5 TRAIN_START=2022-07-01, TRAIN_END=fence(2023-12-18) | build_universe.py:75,133-179 | MATCHES | End pulled from fence.train_end_utc; asserts start>analysis_start, end<holdout_start |
| §5 pinned 0.5/0.25/0.2 SegmentLayout on shifted window | build_universe.py:55-60,147-152; stage_bands.json | MATCHES | Fracs imported from `xen.xena.calibration_pc`, applied to shifted span; bands reproduce §5 dates |
| §5 bands: search→2023-01-31, ranking→2023-05-18, stage2 2023-09-02→2023-12-18 | stage_bands.json; re-run stdout | MATCHES | Reproduced exactly; embargo gap ~107d = purge_ns |
| pin abbb1842 as CONTENT-sha (not file-bytes) | build_universe.py:102-111,305-307; manifest.registry | MATCHES | `content_pin_sha256` = sha256(json.dumps(registry,sort_keys)); validated ==stored; file-bytes sha recorded audit-only |
| §4.3 K≥3 distinct-SYMBOL as post-rank filter (no native param) | certify.py:352-363 (signature); manifest.certification | MATCHES | `certify_and_rank` exposes `subset_size` (cell count) only — no min-distinct-symbol param; post-rank filter correct |
| §6/§11 cost floor, GAP spread 5.0, per-symbol NOT measurable on T1 | build_universe.py:86-87,217-231; pre_search_gross_floor.json | MATCHES | `bybit_round_trip_cost_bps` (shared primitive) funding_coverage=GAP; 18.5 bps floor |
| §3/emission: synthetic finite SlPrice | manifest.emission.sl_price; strategy references | MATCHES (spec) | `EntryFill − side×1.0×k·ATR14[t-1]`; strategy build occurs Stage-3 |
| Reused 001 strategy = faithful RET_ANCHOR-only | epsosc_strategy.py:94,214-223 | MATCHES | Time-cap exit gated on `clear_policy=="HYBRID"`; under RET_ANCHOR only endogenous `clear_hit` fires — no time cap (satisfies §4.2/§7 and golden T2) |

### Golden-trace diff (§13 spec, `golden_traces_spec.json`)
- T1 (SPELL W96 k2.5 RET_ANCHOR_S, entry 2022-07-10 11:01Z → clear 14:31Z): duration self-consistent (3.5h = 14:31−11:01); both endpoints on the same 15m grid. Full L-29 anchor / SlPrice / causal-feature derivation is correctly deferred to execution-time QA against 002's own emissions (strategy not built yet). Spec, not developer-generated — compliant.
- T2 (longest-hold W192, no return): verified by code inspection — no HYBRID/time-cap path reachable under RET_ANCHOR (epsosc_strategy.py:219); non-returning episode ends only by segment-end censoring. MATCHES design intent.
- T3 (SPELL arm on 2023-06-28 while OUT of top-10 → no entry): membership gate exists (epsosc_strategy.py:230-232, causal ≤ next-open rebalance). Spec sound; actual membership-absence verified at execution against membership.parquet.

### Governance & boundary
- Holdout SEALED: TRAIN_END 2023-12-18 < holdout_start 2025-01-08 (fence confirmed). build_universe asserts `end_ns < holdout_start` (l.143-144); freeze_diagnostics filters `t_open < train_end`. No code path touches final-30% or counted TEST band [2023-12-18, 2025-01-08]. PASS.
- Bands immutable: fracs sourced from pinned `calibration_pc`; stage_bands note "immutable once written". PASS.
- FREEZE-FROM-DATA (§5): TRAIN_START resolved from DATA — predeclared X = search-band coverage ≥0.80; measured 0.842 → PASS. "Mass present ~2021-11 vs recalled ~2022-07" honestly disclosed (freeze_diagnostics.mass_onset_note; design §5 data-vs-recall note); 2022-07-01 defended as plateau separating 2021 ramp / single-name drift regimes, not silently forced. PASS.
- Shared-code boundary: 002 code defines NO accounting primitives. Gross proxy = labelled read of emitted `realized_return`×1e4 (freeze_diagnostics docstring l.14-15: "Canonical episode gross deferred to the Stage-4 estimand gate"); costs via shared `xen.evaluation.bybit_round_trip_cost_bps`. Consistent with check_no_local_accounting spirit. PASS.
- No Python strategy backtest in 002 code. PASS.
- L-22 (net-deployability): §9 SUPPORTED band binds on `net leg g_net LCB > 0 under fees+1×spread+funding`. PASS.
- L-28 (derangement): §8 tripwire declares zero-fixed-points derangement, slot separation ≥ max episode duration; "derangement = YES". Drift-twin (§7) correctly uses independent random draw (L-28 n/a there). PASS.
- L-23 (amendment ledger): 0 L / 1 T / 0 N; AMENDMENT-1 = TIGHTER, uni-directional, monotone-shrinking (post-rank filter only removes qualifiers); streak <3, no operator flag. PASS.
- AMENDMENT-1 direction: post-rank K≥3 distinct-symbol filter justified — certify_and_rank has no native min-distinct-symbol param (only cell-count `subset_size`). Only TIGHTENS. PASS.
- Drift-twin control validity (§7): matched-drift twin (random entry timing, E[gross]≠0 = drift-carry benchmark) vs coin-flip twin (side randomized, E[gross]=0 analytic null); signal = live − matched-drift median; non-vacuity via mean-moving randomization (B-6); drift-adjusted collapse ≥0.5 HARD (§8). Spec is sound (code is analyst-owned Stage-6). PASS.
- Per-symbol spread (§6/§11): NOT measurable on T1 (OHLCV-only catalog, no pseudo-quote series); GAP 5.0 retained (INFR-014 cost_pins); deferred to pilot/T2. Data-grounded and honest. PASS.
- XENA VOID-on-new-stack (INFR-010 R4): pin is the post-CAL Bybit registry INFR-015 (abbb1842), not an archive-only chapter-03 pin. PASS.
- L-31 (one node/process): manifest declares multi_instrument_single_node, one_node_per_process=True; runner must honour at Stage-3 (forward declaration, strategy absent).

### Independently reproduced numbers (re-ran both freeze scripts; results dir snapshotted + restored — QA read-only)
- pin content-sha = abbb1842…1bf786 == stored == design-claimed; file-bytes sha 04c0c3… recorded audit-only.
- coverage 0.8421 (128/152) ≥ 0.80 → PASS.
- in-window RET_ANCHOR episodes: 7406 across 152 cells.
- single cells ≥ F*=16 on stage2: 42 of 152.
- top3 pooled stage2 legs: 501 (SHIB1000 176 + SPELL 166 + 10000LADYS 159); AKRO mid-pack at 63.
- gross floor: 135/152 above breakeven; median gross 113.1 bps vs cost 18.5 bps.
- grid: 19 symbols × 8 = 152 binding cells.
- fence: analysis_start 2021-06-29, train_end 2023-12-18, holdout_start 2025-01-08.

### Issues (non-blocking — documentation only)
1. **MINOR / informative** — design.md §10 (l.226) states `top5 = 767`, but `power_table.json` computes `top5_pooled_stage2_legs = 794` (176+166+159+152+141). Stale prose number; non-binding disclosure (gate uses F*=16 and top3=501). Recommend correcting the design prose. Does not affect any gate.
2. **MINOR / informative** — build_universe.py docstring (l.11) cites the first-50% search band as `[2022-07-01, 2023-03-25]`; the actual layout-emitted search band is `2022-07-01 → 2023-01-31` (coverage 0.842 was correctly computed on the actual band). Docstring date only; band and coverage numbers are correct. Recommend fixing the comment.

Neither issue changes any binding number, band boundary, or gate outcome. Verdict remains APPROVE.
