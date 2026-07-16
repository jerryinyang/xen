# VAL-008 design-clause → code-location map (developer handoff, 2026-07-16)

| Design clause | Code location |
|---|---|
| §4 vehicle: SMA(20/100) confirmed-close signal, ≤ t−1, MARKET fill next open | `val008_strategies.py` `MACrossFlip.on_bar` (own deque; order submitted on bar-close event, fills next bar open in Nautilus bar execution) |
| §4 warmup 100 in-window bars | `MACrossFlip.on_bar` len(closes) < slow_period guard; `gen_schedules.causal_sig` sig=0 until SLOW−1 |
| §4 window / TRAIN band / fence | `run_val008.py` WIN_START + `fence.train_end_utc`; reads via `fenced_bar_query(band="TRAIN")`; `BacktestDataConfig(start_time, end_time)` |
| §4 emission contract v1 + PINNED attestation | `run_val008.run_cell` → `write_emission_v1(..., fence=fence_attestation_payload(fence), catalog_version="INFR-011-A4-2026-07-16", catalog_path=data/catalog)` |
| §5 arms table (13 runs/symbol) | `run_val008.ARMS`; schedules from `gen_schedules.py` |
| §5 LEAK oracle sign(Open[t+2]−Open[t+1]) | `gen_schedules.main` `oracle_dir` (ties → +1, deterministic) |
| §5 LEAK-LAG1 causalized sign(Open[t]−Open[t−1]) | `gen_schedules.main` `lag1_dir` |
| §5 LEAK-SHUF 240-slot block permute, seeds 1000+s | `gen_schedules.block_permute` + `oneshot_rows` |
| §5 BASELINE-SHUF 240-bar block permute of sig, seeds 2000+s | `gen_schedules.block_permute(sig[first:])` + `target_changes` |
| §5 1-bar hold, adjacent-slot safety | `gen_schedules.oneshot_rows` (per-bar target array; later slot overrides zero row) |
| §5 schedule regeneration byte-identity (L-19 D1) | deterministic numpy Generator per seed; `schedules/manifest.json` sha256 per file; zstd level pinned |
| §3 gate runnable on emission | smoke PASS: `BTCUSDT__BASELINE` blocking_pass=true, recon 9.1e-13 bps |
| §3 STUB negative check | `run_val008.py --stubcheck` → `VAL-008-stubcheck/` + `results/stub_negative_check.json` |
| §11 no local accounting | no accounting defs in `code/` (shim/adjudication only, at analysis stage) |

**Deviations:** none. (Design amended pre-QA by designer: flat run-dir layout; `--expect`
archive symbols — both recorded in design.md.)

**Runtime note 2:** Nautilus Rust logging initializes once per process — a second
`BacktestNode` in the same process panics (`logging.rs:198`). Runner spawns one subprocess
per cell when >1 cell requested.

**Runtime note:** `BacktestRunConfig(dispose_on_completion=False)` required — default True
disposes the engine before report capture (node-path reports silently empty otherwise;
Phase B never exercised node-path report capture — its emission came from the engine path).

**Run:** from `python/`: `uv run python experiments/VAL-008/code/gen_schedules.py` then
`uv run python experiments/VAL-008/code/run_val008.py --all` then `--stubcheck`.
