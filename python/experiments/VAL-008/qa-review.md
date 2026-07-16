# QA review — VAL-008 (append-only)

## QA run 1 — 2026-07-16T11:33Z — mode: subagent — HEAD 9282e59
Dirty at review: `docs/signal-registry/multiplicity-registry.md` (VAL-008 registration row), `python/experiments/VAL-008/` (untracked).

Verdict: **REVISE**
FAILING_ARTIFACT: `design.md` (§3 gate invocation; §2/§5 factual claims) — REQUIRED_SKILL: quant-designer.
Secondary: seed-stream deviation needs either a design amendment or a code+schedule regen (experiment-developer).

### Design-fidelity trace

Expected behaviour derived from design text first, then code read. Clause map (`code/clause_map.md`) used as the developer's claims and independently verified.

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §4 vehicle: SMA(20/100) 1m closes, confirmed-bar signal ≤ t−1, always-in flip, MARKET next open | `val008_strategies.py:46-62` (`MACrossFlip.on_bar`) | MATCHES | Own deque of closes; signal computed on the confirmed bar's close event; order submitted after close → engine fills at next bar open (verified in smoke fills: ts = next-bar open time). |
| §4 warmup: signal valid only after 100 in-window bars | `val008_strategies.py:49` (`len(closes) < slow_period`); `gen_schedules.py:69` (`range(SLOW-1, n)`) | MATCHES | First signal at bar index 99 (100th bar) in both paths; schedule manifest confirms `first_signal_idx: 99` all 3 symbols. |
| §4 window 2023-06-01 → train_end 2023-12-18, TRAIN band, fenced query | `gen_schedules.py:44-61`, `run_val008.py:74-96` (`fenced_bar_query(band="TRAIN")`), `run_val008.py:52` | MATCHES (note) | bar_marks + schedule reads via `fenced_bar_query`. Engine feed `BacktestDataConfig(start_time, end_time)` (`run_val008.py:156-163`) is a DIRECT catalog read with the identical bounds — see Issue 4 (INFO). Smoke bar_marks span 2023-06-01 00:00 → 2023-12-18 00:00, 288,000 bars. |
| §4 fence: manifest sha256 `35d3375e…`, attestation PINNED via `fence_attestation_payload` | `run_val008.py:197`; `catalog_fence.py:150-162` | MATCHES | `shasum -a 256` of `fence-manifest.json` = `35d3375ec5ec…c00448` (matches design pin). Smoke `fence_attestation.json`: `status: PINNED`, correct sha, `analysis_end_utc = holdout_start = 2025-01-08`. |
| §4 holdout never queried | all reads bounded ≤ train_end 2023-12-18 | MATCHES | No code path constructs a read beyond `fence.train_end_utc`; holdout start is 2025-01-08. `fenced_bar_query` raises on band violation. |
| §4 emission contract v1, flat run dirs `<SYMBOL>__<ARM>` | `run_val008.py:61,186-201` (`write_emission_v1`) | MATCHES | Smoke dir `data/nautilus_runs/VAL-008/BTCUSDT__BASELINE/` has all 8 contract files; deterministic `event_log.jsonl` + sha in metadata. |
| §4 complexity budget: 2 strategies, 2 stat reads, ≤4 plots | `val008_strategies.py` (exactly 2 classes) | MATCHES | Stat reads/plots land at analysis stage; code respects budget. |
| §4 registration: one multiplicity-registry row | `docs/signal-registry/multiplicity-registry.md:1325-1335` | MATCHES | Row present, 0 slots, informative-only, TRAIN-only. NB registry row repeats "seeds 0–4" — see Issue 2. |
| §5 arms table: 13 runs/symbol, 39 total | `run_val008.py:55-59` (`ARMS` = 13), 3 symbols | MATCHES | BASELINE + LEAK + LEAK-LAG1 + 5 LEAK-SHUF + 5 BASELINE-SHUF. |
| §5 LEAK oracle: sign(Open[t+2]−Open[t+1]) known at decision t | `gen_schedules.py:128-129` | MATCHES | Independently recomputed from smoke bar_marks: BTC LEAK schedule (8,432 rows) reproduced row-for-row; golden slots verified (see golden-trace section). Tie rule (0 → +1) deterministic, disclosed in code. |
| §5 LEAK-LAG1: sign of LAST confirmed o2o return ≤ t | `gen_schedules.py:130-131` (`sign(Open[t]−Open[t−1])`) | MATCHES | Open[t] known at bar-t open, hence ≤ decision at bar-t close. Causal. Reproduced row-for-row (all 3 symbols). |
| §5 LEAK-SHUF ×5: directions block-permuted, 240-slot blocks, "seeds 0–4" | `gen_schedules.py:137-139` (seeds **1000+s**) | DEVIATES | Design and registry row say seeds 0–4; code uses 1000–1004 (and 2000–2004 for BASELINE-SHUF). Recorded in `schedules/manifest.json` + clause_map, NOT in design.md; no operator approval evidence. Regenerability unaffected. Issue 2. |
| §5 BASELINE-SHUF ×5: sig series block-permuted 240-bar blocks, flip occupancy preserved | `gen_schedules.py:141-143` | MATCHES (note) | Permutes sig from first-signal index; always-in occupancy trivially preserved; block-boundary artifact flips add ~n/240 events — acceptable for a ≈0-edge consistency arm. Seeds 2000+s — same deviation as above. |
| §5 1-bar hold; §2 "LEAK hold never overlaps the next schedule slot (spacing ≈ 68 bars median)" | `gen_schedules.py:95-101` (`oneshot_rows`) | DEVIATES (design wrong, code honest) | Measured cross-spacing medians 53/52/54 bars (design's "≈68" is the MEAN); min spacing = 1 with 52/43/58 adjacent slot pairs (BTC/ETH/SOL, ~1.0–1.4% of slots). Same-direction adjacent slots merge into one ≥2-bar leg (change-compression); opposite-direction adjacent slots flip without a flat bar. Design §2 OBJECT-IDENTITY "never overlaps" is factually false. Symmetric across LEAK/LEAK-SHUF/LEAK-LAG1 (same slots), so the tripwire comparison stays like-for-like. Issue 3. |
| §5 schedule cadence = symbol's own BASELINE cross timestamps; counts ~4,256/4,286/4,218 | manifest: 4,256/4,282/4,222 | MATCHES (note) | ETH −4, SOL +4 vs design estimates; immaterial to §9 power. |
| §5 schedules regenerable byte-identically (L-19 D1) | `gen_schedules.py` deterministic RNG + `schedules/manifest.json` | MATCHES — VERIFIED | (a) sha256 of all 36 parquet files matches manifest.json; (b) QA re-derived all 12 arms/symbol from an INDEPENDENT reimplementation (BTC from smoke bar_marks; ETH/SOL from fresh fenced catalog reads) — all 36 schedules reproduce row-for-row (ts_ns, target). |
| §5 oracle/destroy arms traverse the same BacktestNode + emission path | `val008_strategies.py:75-104` (`ScheduleExecutor`), `run_val008.py:136-201` (single `run_cell` for all arms) | MATCHES | Identical venue/data/emission config; only the strategy differs. ScheduleExecutor applies targets on decision-bar close (`ts <= bar.ts_event`) → fill next open, matching MACrossFlip timing. `on_stop` close_all in both. |
| §3 estimand: shim → `xen.adjudication`, reconciliation blocking | smoke gate run | MATCHES | Smoke `validate_run` (no --expect): `blocking_pass: True`, reconciliation abs_diff 9.1e-13 bps (tol 1.0), fence PINNED ok. |
| §3 gate command: `python -m xen.estimand_validation … --expect BTCUSDT,ETHUSDT,SOLUSDT` | `xen/estimand_validation.py:355-382,186-206` | **DEVIATES / DEFECT** | Verified empirically: `validate_family` propagates `expected_instruments` into every per-cell `validate_run`; `_manifest_check` prefers `metadata["symbol"]` (set by the runner, `run_val008.py:200`) over `instrument_id_map` keys, so each single-symbol cell reports 2 missing symbols → per-cell `manifest.ok = False` → per-cell and family `blocking_pass = False` **even on a fully correct 39-run emission**. Design's parenthetical ("manifest check reads instrument_id_map keys") holds only when `symbol` is absent from metadata. Issue 1 (blocking-path defect; must be fixed pre-execution). |
| §3 STUB negative check, outside family root | `run_val008.py:218-245` (`--stubcheck` → `VAL-008-stubcheck/`, `fence=None` → STUB payload) | MATCHES | `_fence_check_v2` rejects STUB (`estimand_validation.py:129-136`) → `blocking_pass False` guaranteed; report written to `results/stub_negative_check.json`. Dir is outside `VAL-008/` family root so it cannot contaminate `validate_family`. |
| §11 no local accounting | `check_no_local_accounting("experiments/VAL-008/code")` | MATCHES — VERIFIED | `{'ok': True, 'banned_defs_found': []}`. No accounting primitives in `code/`; gen_schedules computes directions only, no P&L. |
| §11 hard/informative split | design §11; no auto-verdict machinery in code | MATCHES | Runner emits data only; no threshold/verdict logic anywhere in `code/`. |
| §12 SPREAD-SCALE-ROUTING declared; t1_undecidable YES, no tradability claim | design §12 | MATCHES | Apparatus-only disposition; routing exercised at analysis as disclosure. Nothing for code to implement pre-analysis. |

### Golden-trace diff (expected from DESIGN; diffed against sanctioned smoke `BTCUSDT__BASELINE`)

QA recomputed SMAs and crosses independently from `bar_marks.parquet` (which itself matches the fenced catalog read).

| Event | Design expectation | Independent recompute | Emission (fills.parquet) | Verdict |
|---|---|---|---|---|
| G1 2023-06-01 04:21 → +1 | fill first bar opening ≥ 04:21 @ ≈26766.5; SMA 26775.245/26775.075 | cross confirmed; SMAs **exact match** to design; next Open 26766.5 | BUY 0.2 @ **26766.5**, ts 04:21:00 | MATCHES |
| G2 06:39 → −1 | fill 06:39 @ ≈26834.5; SMA 26829.060/26829.686 | SMAs exact; next Open 26834.5 | SELL 0.2 @ **26834.6**, ts 06:39:00 | MATCHES (+1 tick, see note) |
| G3 07:35 → +1 | fill 07:35 @ ≈26827.4; SMA 26820.680/26820.185 | SMAs exact; next Open 26827.4 | BUY 0.2 @ **26827.5**, ts 07:35:00 | MATCHES (+1 tick) |
| LEAK dirs at G1/G2/G3 | = sign(Open[t+2]−Open[t+1]), QA-recomputed from data | −1 (26753.2−26766.5), +1 (26845.9−26834.5), −1 (26817.4−26827.4) | LEAK schedule parquet rows carry exactly these targets at these ts | MATCHES |

Timestamps match exactly (design requirement). Fill-price note: engine deviates from staging Open by ±1 tick on some fills (G2/G3 +0.1; later fills also −0.1 observed) — Nautilus L1 book synthesis from bars, not quantization strictly; ≈0.04 bps/leg on BTC, immaterial vs the 3.1–8.7 bps plant and within the design's declared tolerance intent. Analyst should disclose the mechanism.

### Governance & boundary

| Check | Evidence | Result |
|---|---|---|
| Mandatory declaration blocks (design-requirements §1–§8) | MECHANISM+DERIVED §1; OBJECT-IDENTITY §2; 3 CONTROL blocks §6 (question/population-B1/bite-B5/non-vacuity-B6/expected/disclosure all present); TRIPWIRE §7; BANDS §8; POWER §9; GOLDEN-TRACE §10 (designer-computed, developer did not generate — QA reproduced from data); HARD/INFORMATIVE §11 | PASS (content defects in §2/§5 → Issue 3) |
| §9 CONVERSION-PIN | N/A declared (no screen evidence cited) — correct | PASS |
| §10 SPREAD-SCALE-ROUTING | Declared; `t1_undecidable: YES`, no tradability band exists anywhere in design → no REVISE trigger | PASS |
| §11 L-22 spread verdict leg | N/A — no SUPPORTED band in design | PASS |
| §12 L-23 amendment ledger | "no amendments yet" declared. NB: the fixes required by this review land AFTER registration → each must carry `AMENDMENT-n` + LOOSER/TIGHTER/NEUTRAL + running count | PASS (conditional — see required changes) |
| §13 L-24 battery rules | Battery is the apparatus plant, not an eligibility gate; 5-seed vs L-19 ≥25 deviation openly declared in design for operator judgment | PASS (informative to operator) |
| TRAIN-only fence; no holdout contact | All reads ≤ 2023-12-18; holdout starts 2025-01-08; `fenced_bar_query` used for bar_marks + schedules; engine feed same bounds (Issue 4 INFO) | PASS |
| PINNED attestation | Smoke `fence_attestation.json` status PINNED, manifest sha matches pinned `35d3375e…` | PASS |
| `check_no_local_accounting("…/VAL-008/code")` | ok=True, no banned defs | PASS |
| No Python strategy backtest | Both arms in-engine (BacktestNode); gen_schedules computes directions only (no P&L, no fills) — sanctioned by design §5 | PASS |
| L-19 schedule regenerability | All 36 schedule files: sha256 vs manifest PASS; independent row-for-row regeneration PASS (BTC from bar_marks; ETH/SOL from fresh fenced reads) | PASS |
| Exit-set / destroy comparability (L-14/B-6) | Destroys permute the causal input (directions), not P&L; same slots, same holds, same execution path; mean of direction×return is the moved statistic | PASS |
| Golden-trace columns in emission | `bar_marks` (SourceCloseTime, RealO/H/L/C, Volume), `positions_ledger` (ts_opened/ts_closed, avg_px_open/close, realized_*), fills, orders, event_log, instrument_id_map, fence_attestation all present in smoke | PASS |
| Registry preconditions | VAL-008 registered (0 slots, no family, no counted TEST reads); no XENA routing (R4 not triggered); no counted TEST read planned | PASS |
| DEVIATIONS blocks | Code files declare "DEVIATIONS: none" — but seed streams deviate from design §5 (Issue 2): a silent deviation as written | FAIL → Issue 2 |
| Elicitation hygiene | No open operator questions in design | PASS |

### Issues

1. **MAJOR (blocks execution sign-off) — §3 gate command mechanically fails on a valid emission.**
   Design §3 vs `python/src/xen/estimand_validation.py:355-382` + `:186-206` and `run_val008.py:200`.
   `validate_family` passes `--expect BTCUSDT,ETHUSDT,SOLUSDT` into every per-cell `validate_run`; `_manifest_check` reads `metadata["symbol"]` (single symbol per cell, set via `extra_metadata`) → every cell reports 2 missing instruments → family `blocking_pass=False` always. Verified empirically on the smoke cell.
   Required change (quant-designer, coordinate with developer): amend §3 so the family-level expectation binds at family level only — e.g. run the gate without `--expect` per cell and assert the family `manifest.emitted ⊇ {BTC,ETH,SOL}` (validate_family already aggregates this correctly), or change `validate_family` to not propagate `expected_instruments` per-cell (shared-code change — needs its own care + smoke). Do NOT fix by deleting `symbol` from run metadata (degrades provenance).
2. **MINOR — undeclared seed-stream deviation.** Design §5 and the registry row say shuffle "seeds 0–4"; code uses 1000–1004 (LEAK-SHUF, `gen_schedules.py:139`) and 2000–2004 (BASELINE-SHUF, `gen_schedules.py:142`). Recorded only in `schedules/manifest.json`/clause_map; code headers claim "DEVIATIONS: none". Regenerability verified, so the science is unaffected — but as written this is a silent design deviation. Required change: amend design §5 (and note in registry row if edited) to name the seed streams — direction NEUTRAL — or regenerate schedules with seeds 0–4. Amendment must carry an L-23 `AMENDMENT-n` block.
3. **MINOR — design §2/§5 factual claims contradicted by data.** "Cross spacing ≈ 68 bars median" is the mean; measured medians = 53/52/54 (BTC/ETH/SOL). "LEAK hold (1 bar) never overlaps the next schedule slot" is false: min spacing = 1; adjacent slot pairs = 52/43/58 (~1.0–1.4% of slots); same-direction adjacent slots merge into single ≥2-bar legs (change-compression, `gen_schedules.py:95-101`). Required change: amend §2 OBJECT-IDENTITY (effect-splitting) and §5 to disclose the adjacency rate and the deterministic merge rule; note leg-count < slot-count consequence for the analyst. Tripwire validity unaffected (identical slots across LEAK/destroy arms). Direction NEUTRAL.
4. **INFO — engine feed bypasses the fenced wrapper.** `run_val008.py:156-163` `BacktestDataConfig(start_time=WIN_START, end_time=fence.train_end_utc)` reads the catalog directly. Bounds are identical to the fenced `bar_marks_for` query executed first for each symbol, so no holdout exposure exists; still, `catalog_fence` doc says every catalog read goes through `fenced_bar_query`/`assert_within_fence`. Recommend one `assert_within_fence(fence, WIN_START, fence.train_end_utc, band="TRAIN")` line beside the config. Not blocking.
5. **INFO — fill prices ±1 tick vs staging Open** (Nautilus L1 book synthesis). Within design tolerance; ≈0.04 bps/leg; analyst to disclose mechanism.
6. **INFO — slot-count estimates** off by 4 on ETH/SOL (4,282 / 4,222 actual); §9 power unaffected.

### Verdict rationale

Implementation fidelity is strong: golden trace reproduces exactly (SMA values to the design's 3 decimals; timestamps exact), all 36 schedules regenerate row-for-row from independent reimplementation, the STUB negative path is sound, accounting/holdout/attestation checks pass. But the design's own blocking-gate invocation (§3) fails mechanically on a correct emission — that must be repaired before the operator's execution gate — and two design-text claims (seeds, slot overlap) do not match the verified implementation/data. REVISE with the three required changes above; re-run QA (appended section) after amendment. Post-registration amendments must carry L-23 direction declarations (all three expected NEUTRAL).

---

## QA run 2 — 2026-07-16T11:43Z — mode: subagent — HEAD 9282e59
Dirty at review: `docs/signal-registry/multiplicity-registry.md`, `python/experiments/VAL-008/` (untracked). Scope: verification of the run-1 amendment set (AMENDMENT-1/2/3 + fence assert + L-23 ledger).

Verdict: **APPROVE**

### Fix-verification trace (run-1 issues → amended artifacts)

| Run-1 issue | Amendment | Evidence (verified in file / by execution) | Verdict |
|---|---|---|---|
| 1 MAJOR — §3 gate command mechanically fails on valid emission | AMENDMENT-1: gate = `analysis_code/run_gate.py`; `validate_family` with NO per-cell `--expect`; predeclared family completeness `n_cells==39 AND emitted=={BTCUSDT,ETHUSDT,SOLUSDT}`; `check_no_local_accounting` on `code/` + `analysis_code/`; top-level `blocking_pass` conjoins all | `design.md:60-69` matches `analysis_code/run_gate.py:16-49` line-for-line in logic. QA replicated the wrapper's exact logic in-memory against the smoke cell: family `blocking_pass=True` per-cell (no expectation → per-cell manifest ok, the run-1 failure mode gone), `completeness ok=False` with 1 cell (correct — binds only at the full 39-run stage), both accounting checks ok, final conjunction `False` as expected. On a complete 39-run emission every conjunct is satisfiable: per-cell checks are expectation-free, family-level `manifest.emitted` aggregation (`estimand_validation.py:367-373`) supplies the 3-symbol set. Strict `n_cells==39` and set equality also guard against stray extra run dirs. Output path `results/estimand_validation.json` per §3; exit code 1 on failure. **RESOLVED** |
| 2 MINOR — undeclared seed streams | AMENDMENT-2: §5 now pins seeds 1000–1004 (LEAK-SHUF) / 2000–2004 (BASELINE-SHUF) | `design.md:92,94` match `gen_schedules.py:139,142` and `schedules/manifest.json` (`shuffle_seeds_leak: [1000..1004]`, `shuffle_seeds_baseline: [2000..2004]`, verified run 1). Registry row updated (`multiplicity-registry.md:1332`: "seeds 1000–1004/2000–2004"). Schedules unchanged (no regen needed — shas still match manifest from run-1 check). **RESOLVED** |
| 3 MINOR — §2/§5 overlap/spacing claims false | AMENDMENT-3: §2 corrected | `design.md:46-51`: adjacent slots exist, min spacing 1, counts 52/43/58 (BTC/ETH/SOL — matches QA run-1 measurements exactly), deterministic later-slot-wins resolution, same-direction merges into ≥2-bar ledger legs, median spacing ≈53 (mean ≈68). Resolution description verified against `gen_schedules.py:95-101` semantics (targets array assignment = later slot's direction occupies the would-be exit bar; change compression merges equal-direction adjacents). Estimand note ("legs as booked from positions_ledger") is correct. **RESOLVED** |
| 4 (required) — L-23 ledger | Amendment ledger block added | `design.md:215-227`: AMENDMENT-1/2/3 each with DIRECTION: NEUTRAL + rationale; running count 0 looser / 0 tighter / 3 neutral; correctly notes no false-qualifier re-derivation needed (no qualification gate set exists in this apparatus design). No one-directional streak. **RESOLVED** |
| 5 INFO — engine feed fence assert | `run_val008.py:44` imports `assert_within_fence`; `run_val008.py:140` calls it inside `run_cell` with the exact engine-feed bounds (`WIN_START, fence.train_end_utc, band="TRAIN"`) before every run config — per cell, stronger than the recommended per-symbol placement | **RESOLVED** |

### Governance re-check (deltas only; run-1 results otherwise stand)

| Check | Evidence | Result |
|---|---|---|
| Amended gate has no auto-verdict machinery | `run_gate.py` conjoins integrity checks only (gate v2 blocking + completeness + accounting) — all four conjuncts are integrity-class, none quality-class | PASS |
| No local accounting incl. new `analysis_code/` | `check_no_local_accounting` executed on both dirs: ok=True, ok=True | PASS |
| Wrapper is analysis-stage code in the right place | `analysis_code/run_gate.py` — gate artifact per pipeline layout; imports canonical `xen.estimand_validation` only, zero imports from `code/` | PASS |
| Amendments change no arm, schedule, band, or threshold | Diff surface = §2/§3/§5 text, ledger block, one assert + import in runner, new wrapper file; schedules' shas unchanged vs manifest | PASS |
| Registry row consistency | Seed text updated; slot accounting unchanged (0 slots, informative-only) | PASS |

### Issues

1. **INFO (editorial, non-blocking):** `design.md:229-233` retains the stale pre-amendment sentence "§12/§13 (L-23/L-24): no amendments yet", directly contradicting the ledger block immediately above it (`design.md:215-227`). The dated ledger governs and the contradiction cannot mislead the gate, but the clause "no amendments yet" should be deleted (or changed to "see ledger above") at the next touch of the file. No re-QA needed for that edit alone.
2. Run-1 INFO notes 5 and 6 (±1-tick fill mechanism disclosure; ETH/SOL slot counts 4,282/4,222 in §5/§9 prose still showing the ~4,286/4,218 estimates) remain open for the data-analyst stage — informative only.

### Verdict rationale

All three REVISE items are resolved with content-verified amendments (each independently checked against code, data, or execution — not against the developer's claims), the amendment ledger satisfies L-23 with an all-NEUTRAL count, and the repaired gate wrapper was exercised: the run-1 failure mode is gone and the conjunction shape is correct for the full 39-run emission. Remaining items are editorial/disclosure notes that do not touch integrity. **APPROVE** — ready for the operator's execution gate (execution itself remains the operator's decision; QA APPROVE launches nothing).

---

## QA run 3 — 2026-07-16T12:38Z — mode: subagent — HEAD 9282e59
Dirty at review: `docs/signal-registry/multiplicity-registry.md`, `docs/knowledge-base/INDEX.md` + `docs/knowledge-base/reviews/` (capture-geometry review — unrelated to VAL-008, see governance note), `python/experiments/VAL-008/` (untracked). Scope: post-execution review of the AMENDMENT-4 (derangement) amend-in-place cycle and the executed/rerun artifact state.

Verdict: **APPROVE** (amended state sound; final experiment verdict remains the operator's)

### (a) AMENDMENT-4 text vs implementation

| Claim (design ledger, `design.md` AMENDMENT-4) | Code / data | Verdict |
|---|---|---|
| Block permutation → derangement (resample until no block maps to itself) | `gen_schedules.py:76-91`: single `default_rng(seed)`, initial `permutation(n_blocks)`, `while (order == arange).any(): order = rng.permutation(...)` | MATCHES |
| Deterministic per seed | Single rng object drawn sequentially; rejection loop consumes the same stream in the same order every run → deterministic. Verified concretely: schedule regeneration reproduces byte-identical files (see (b)); QA also replayed the rejection loop for all 10 seeds at both block-count scales (18 leak-slot blocks, 1200 sig blocks) — terminates, deranged, deterministic | MATCHES |
| Criterion UNCHANGED | §7 tripwire text verbatim identical to run-1/run-2 reads: collapse ≥ 0.9 per seed/arm/symbol; leak-catch FLAG iff hit CI-low > 0.55 AND collapse ≥ 0.9; 3/3 vs 0/3 | MATCHES — criterion did not move |
| Defect mechanism (plain permutation keeps E[1] fixed block; seeds 1000/1003 had 2/18 fixed blocks → 11.1% slots at TRUE alignment; residual +0.38 bps; collapse 0.870) | Arithmetic verified: 2/18 = 11.1% × BTC plant +2.916 = +0.324 bps predicted residual ≈ +0.38 observed; 1 − 0.38/2.92 = 0.870 exactly. Contaminated emissions are hard-deleted (unverifiable directly — disclosed, and the L-10 route requires the deletion), but the analytic account is internally consistent and the defect class is real: run-1's `block_permute` (in my QA record) was indeed a plain permutation | CONSISTENT |
| DIRECTION: NEUTRAL, running count 0/0/4 | Ledger block present, dated, post-first-measurement L-10 flag explicit. Direction note: a stronger destroy makes the LEAK collapse criterion *reachable*, which in this apparatus design eases APPARATUS-PASS — the ledger addresses this head-on (control repaired to its own declared population property, "direction independent of forward return by construction", which was false at fixed points). QA concurs NEUTRAL is defensible; the operator sees the reasoning either way | ACCEPTED (operator judges) |

### (b) Schedule regenerability under amended code (L-19)

- QA ran the current `gen_schedules.py` with `OUT_DIR` redirected to the session scratchpad (project tree untouched): all **36/36 sha256 match** `code/schedules/manifest.json`.
- On-disk schedule files vs manifest: all match.
- Every one of the 30 rerun *-SHUF emissions' `run_metadata.run_config.schedule_sha256` matches the current manifest — no stale-schedule cell survived the rerun. LEAK/LEAK-LAG1/BASELINE cells (mtimes 12:47–13:02, pre-rerun) correctly untouched: their schedules don't route through `block_permute`.

### (c) Change-surface audit vs run-2 state

| File | Status |
|---|---|
| `design.md` | AMENDMENT-4 block only (ledger); §5/§6/§7 body otherwise unchanged (see Issue 2) |
| `code/gen_schedules.py` | `block_permute` derangement + docstring only |
| `code/run_val008.py` | subprocess-per-cell driver in `main()` (Nautilus Rust logging is once-per-process — clause_map runtime note 2); `run_cell` and all governance-bearing logic unchanged; failure path aborts with rc≠0 |
| `code/clause_map.md` | runtime note 2 added |
| `code/val008_strategies.py`, `analysis_code/run_gate.py` | byte-size and mtime unchanged since run 1/run 2 respectively — untouched |
| `analysis_code/interrogate.py`, `analysis.md`, `results/*` | new analyst-stage artifacts (expected) |
| `python/src/xen/**` | clean in git status — no shared-code changes |
| Registry row | updated for seeds + Amendments 1–3; does NOT yet mention AMENDMENT-4 (Issue 3) |
| `docs/knowledge-base/INDEX.md` + `reviews/capture-geometry-review.md` | UNRELATED repo activity (capture-geometry cross-chapter review); not part of VAL-008's change set — flagged for the operator's awareness only, no VAL-008 governance implication |

### (d) Criterion stability

§7 verbatim unchanged across all three QA reads (collapse ≥ 0.9; hit-rate CI-low > 0.55; LEAK 3/3, BASELINE 0/3; hard FAIL semantics). §8 bands unchanged. No gate-set change anywhere; L-23 count 0 looser / 0 tighter / 4 neutral is accurate.

### (e) analysis.md integrity table vs artifacts (sanity re-derivation, not a re-audit)

| analysis.md claim | QA verification | Verdict |
|---|---|---|
| Gate 39/39 blocking_pass, completeness ok, accounting clean | `results/estimand_validation.json` re-read: `blocking_pass: true`, n_cells 39, completeness ok (39 cells, 3 symbols), both accounting checks ok, all 39 cells PINNED, max reconciliation abs_diff 7.3e-12 bps | MATCHES |
| STUB negative correctly fails | `results/stub_negative_check.json`: `blocking_pass: false`, fence reason = Phase-B STUB | MATCHES |
| BTC LEAK +2.916 bps/leg | QA recomputed independently via `adjudication_shim` → mean RealizedBps = **+2.916**, n = 4,228 legs (= 4,256 slots − 28 same-direction merges, matching the disclosed merge counts) | MATCHES |
| LEAK-SHUF collapse 0.977–1.064; LEAK-LAG1 0.996–1.055 | QA recomputed BTC: SHUF s0–s4 collapse 1.048/0.997/1.029/1.064/1.003; LAG1 1.022 — inside the reported ranges; destroyed means −0.19…+0.01 bps (CI-straddling-zero class) | MATCHES |
| Leak-catch 3/3 vs 0/3 | Consistent with recomputed LEAK mean ≈ plant magnitude (hit 1.0 is the only arithmetic consistent with mean ≈ mean|o2o|) and BASELINE hit ≈ 0.49; protocol rule quoted verbatim from §7 | CONSISTENT |
| Evidence-against section present with equal rigor | §4 lists the shipped control defect first, the analyst's own initial mis-read, the ±1-tick deviation, and a marginal LAG1 negative — symmetric | PASS |
| No auto-verdict | §6 recommendation explicitly non-final, operator-owned, with "would change if" conditions | PASS |

### Issues (all non-blocking)

1. **INFO — collapse-fraction definition sloppy in design §6:** disclosure line says "collapse fraction (destroyed/raw)" but §7's "collapse ≥ 0.9" and the analyst's usage are 1 − destroyed/raw (the only reading consistent with the tripwire; values can exceed 1 when destroyed goes slightly negative). Recommend a one-line clarification if design.md is touched again; no ambiguity in practice.
2. **INFO — §5/§6 body text still says "block-permuted"** without the derangement qualifier; the dated AMENDMENT-4 ledger governs (L-23 convention), but a "(deranged — AMENDMENT-4)" pointer in the §5 arms table would help future readers. Also the trailing line "Amendments: see ledger above (3 NEUTRAL)" is stale — count is now 4.
3. **INFO — registry row enumerates "Amendments 1–3" only;** it points at the design ledger (which contains 4), but the row should say 1–4 (and could note the amend-in-place rerun) at next registry touch.
4. **INFO — pre-deletion defect numbers are unverifiable post-hoc** (contaminated emissions hard-deleted per L-10). The analytic account is internally consistent (fixed-point count → predicted residual → collapse 0.870 arithmetic all checks) and the defect is independently established from QA run-1's own record of the plain-permutation code. Acceptable; noted for the record.
5. **INFO — KB candidate lessons** proposed in analysis.md §5 (derangement rule; fill-ts semantics; one-node-per-process) are operator/checkpoint decisions — correctly not self-adopted by the analyst.

### Verdict rationale

The amend-in-place cycle is clean: the defect was caught by the predeclared criterion (the tripwire did its job — arguably the strongest apparatus evidence in the whole experiment), the fix implements the control's own declared intent without moving any criterion, the contaminated cells were deleted and rerun with provenance intact (all 30 SHUF emissions pin the new schedule shas), schedules remain byte-regenerable under the amended code from an out-of-tree regeneration, the gate passes 39/39 on PINNED attestations with the STUB negative behaving correctly, and the analyst's verdict-bearing numbers survive independent recomputation. Change surface matches the declared set exactly; shared `xen` code untouched. **APPROVE.** Final Phase D PASS/FAIL is the operator's call — the honest caveat (first-pass destroy was defective) is properly surfaced in analysis.md §4/§6 for that decision.
