# SPDR-021/022/023 critical-path performance review

Recorded 2026-08-03 during the amended six-cell TRAIN rerun. This is an operational review,
not an economic read. It does not contact TEST/holdout, change the experiment grid, alter a
family status, or issue a verdict.

## Governing acceptance rule

An optimisation is admissible only when it preserves fences, inputs, origins, arms, schedule and
engine event order, row order, numeric precision, schemas and deterministic bytes. It needs focused
edge-case tests, bounded and representative measurements, and exact artifact parity. Cache purging
or the deferred streaming-report rewrite remains prohibited by the binding execution handoff.

## Measurements

| Probe | Before | After | Evidence |
| --- | ---: | ---: | --- |
| BTCUSDT schedule initialisation, 3,625,870 rows | 9.327 s; 8.410 GB RSS | 0.509 s; 3.474 GB RSS | same frozen schedule; future rows retained columnarly and consumed in sorted order |
| 2,000-arm HOLD replay | 27.016 s | 5.945 s | 4/4 Parquet SHA-256 hashes and all row counts equal |
| Full BTCUSDT candidate replay | production unit completed at 1,486.3 s including preparation/publication | optimised engine replay 428.245 s | 4/4 engine reports byte-equal to the pre-optimisation unit |
| Full BTCUSDT optimised engine peak | not captured on original unit | 5.749 GB RSS | child-process resource measurement |
| Full BTCUSDT preparation, 12,504 H1 rows | 39.410 s; 3.892 GB RSS | not changed | 3,625,870 execution rows; parent retains emitted tables while child runs |
| ETHUSDT sequential retry | not previously isolated | replay reached report generation at 414 s | interrupted before publication after three swap-growth checks; zero throttled pages and 39% memory free |
| Five sibling native-state bootstrap columns, 9,000 rows | 0.543 s | 0.202 s | 2.69×; every estimate, interval, MDE and effective count exactly equal |
| PYTHUSDT episode-ledger filter, warm scan | 0.0108 s | 0.00330 s | 3.27×; exact membership retained, 237,974 rows in both paths |
| SPDR-023 cTrader full analysis | 1,056.134 s canonical | 539.170 s | 1.96×; all 13 artifact SHA-256 hashes equal to the canonical pass |

Full BTCUSDT parity counts: 827,105 orders, 796,647 fills, 398,388 positions and 4,767,815
state-ledger rows. Hash equality covered `orders.parquet`, `fills.parquet`,
`positions.parquet` and `state_ledger.parquet`.

## Accepted fixes

1. **Columnar schedule consumption.** Do not call `iter_rows(named=True)` over millions of future
   rows and retain the resulting dictionaries. Keep the sorted Polars frame behind an iterator and
   materialise only the next actionable row.
2. **Frozen shared account.** These are independent research arms, not a shared-capital portfolio.
   `frozen_account=True` skips unused aggregate balance/PnL recalculation while native order, fill,
   position and strategy ledgers remain unchanged.
3. **No Nautilus post-run performance analysis.** `run_analysis=False`; canonical outputs come from
   trader reports and the strategy state ledger. The unused analyzer remains outside the estimand.
4. **Release terminal client-order IDs.** `_entry_orders` must release IDs when
   `_by_client_order` and the rest of the episode state become unreachable. Retain the compact
   `_entry_terminal` and `_closed` keys because they make duplicate terminal callbacks idempotent.
5. **Stream file hashes.** Unit publication/resume hashes use `hashlib.file_digest`; never allocate a
   Python `bytes` object for a multi-gigabyte Parquet file.
6. **Share identical native-state bootstrap draws.** The `ALL` and state-specific origin rows use
   the same population, block partition and reset seed. Build the partition and draw positions once
   per arm, then apply each column's original NumPy mean to the same ordered positions. Nullable
   inputs retain the independent reference path.
7. **Expose exact ledger bounds to Parquet pruning.** Retain the complete origin-ID membership
   predicate, but add its inclusive lexical min/max bounds. The bounds let Polars reject unrelated
   symbol-major row groups without weakening exact membership or changing row order.

## Adversarial findings

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Whole schedule expanded into retained Python dictionaries",
    "evidence": "AdaptiveManagementStrategy.__init__ converted 3,625,870 BTCUSDT rows with iter_rows(named=True); isolated peak was 8.410 GB RSS.",
    "impact": "One child consumed over half of a 16 GB host before replay and made two workers unsafe.",
    "fix": "Resolved: retain the sorted columnar frame behind an ordered iterator; memory test and full byte-parity replay added."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "Nautilus recalculated an irrelevant shared margin account per fill",
    "evidence": "Interrupt samples landed in Portfolio.update_order/update_position and AccountsManager.update_positions; frozen-account probe reduced 2,000-arm replay from 27.016 s to 5.945 s with 4/4 identical hashes.",
    "impact": "Compiled but unnecessary account work dominated wall time; moving surrounding Python to Rust would not remove it.",
    "fix": "Resolved: frozen_account=True with pinned output parity; run_analysis=False removes unused post-run statistics."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Terminal client-order IDs grew for the full run",
    "evidence": "_forget removed callback maps but did not discard their client-order IDs from _entry_orders.",
    "impact": "Millions of unreachable Python client-order strings accumulated after episode completion.",
    "fix": "Resolved: discard client-order IDs with their callback maps. A regression test proved that _entry_terminal/_closed keys must remain to suppress duplicate terminal callbacks, so those compact idempotency guards are deliberately retained."
  },
  {
    "id": "F04",
    "severity": "Major",
    "title": "Artifact hashing allocated entire files as Python bytes",
    "evidence": "_publish_unit and _unit_is_complete used path.read_bytes(); a 20 MB regression fixture produced a 20.0 MB traced allocation.",
    "impact": "Publication and resume validation could add a full largest-file memory spike while wide frames were still live.",
    "fix": "Resolved: stream SHA-256 with hashlib.file_digest; traced peak is bounded below 4 MB in the regression test."
  },
  {
    "id": "F05",
    "severity": "Major",
    "title": "Parent retains all materialised tables while the child engine runs",
    "evidence": "Full BTCUSDT preparation peaks at 3.892 GB; the optimised child peaks at 5.749 GB. The runner returns tables and bar marks from prepare() and holds them until report publication.",
    "impact": "One job has an approximately 9.6 GB combined live set; two jobs exceed the 16 GB host and reproduce sustained swapping.",
    "fix": "Deferred by the governing plan: pre-stage deterministic table bytes, release frames before spawning the child, and publish atomically from paths. Prove clean/parallel/resume byte identity before adoption."
  },
  {
    "id": "F06",
    "severity": "Major",
    "title": "Report extraction retains multiple wide Python/Pandas/Polars representations",
    "evidence": "run_work_unit builds all three Nautilus reports, stringifies them through Pandas, then run_work_unit_subprocess reads all four Parquet reports into the parent at once. The sequential ETHUSDT retry reached generate_order_fills_report at 414 s while swap-outs grew across three checks.",
    "impact": "Post-engine memory can spike and limits safe symbol parallelism even after schedule retention is fixed.",
    "fix": "Highest-priority post-rerun work, but deferred by the binding handoff: generate, normalise and atomically write one report at a time; return paths/counts instead of reloading all reports beside retained preparation tables. Cache purging requires a pinned parity corpus."
  },
  {
    "id": "F07",
    "severity": "Minor",
    "title": "Preparation repeats Python breach-path work and component joins",
    "evidence": "breach_episodes iterates Python dictionaries for every native arm; _attach_component_columns repeats joins; expanding feature quantiles contain quadratic Python/Numpy prefix work. Full BTCUSDT preparation is 39.410 s, about 8% of the optimised per-symbol path.",
    "impact": "Not currently dominant, but it can become the next bottleneck after engine improvements or on larger grids.",
    "fix": "Profile by function before change. Prefer vectorised Polars/NumPy and cached component frames; require exact schedule hashes, null/NaN/tie/order fixtures and full-unit parity."
  },
  {
    "id": "F08",
    "severity": "Minor",
    "title": "Hold-timer lookup is linear and repeatedly materialises timer names",
    "evidence": "_on_hold_timer scans _hold_timer.items(); _on_exit_filled checks membership in clock.timer_names for every timed close.",
    "impact": "Avoidable callback overhead scales with concurrently open timed arms, though the active-arm cap bounds it.",
    "fix": "Use a tested reverse timer-name-to-execution map and remove fired timers from both maps; benchmark before adoption."
  },
  {
    "id": "F09",
    "severity": "Minor",
    "title": "Rust would be premature without a remaining Python CPU profile",
    "evidence": "The dominant sampled stack was already Nautilus Cython; configuration removed 4.5x of bounded runtime. Remaining Python preparation is 39.410 s versus a 428.245 s optimised engine replay.",
    "impact": "A Rust rewrite now adds parity/toolchain surface while targeting less than the dominant cost.",
    "fix": "Use Rust only for a measured pure-Python kernel after columnar/vectorised options fail, with a pinned Python/Rust bit-parity corpus as in INFR-007."
  },
  {
    "id": "F10",
    "severity": "Major",
    "title": "Identical bootstrap partitions and draws repeated once per native state",
    "evidence": "An interrupted SPDR-023 crypto analysis landed in _origin_row → _clustered_interval while concatenating block samples. ALL and every state rebuilt the same partition and reset the same seed. Sharing the draw positions was 2.69× faster on a 9,000-row five-column probe and cut the full cTrader analysis from 1,056.134 to 539.170 seconds with 13/13 artifact hashes equal.",
    "impact": "The redundant Python/NumPy loop dominated the canonical analysis and multiplied across every arm, state, symbol and reproduction pass.",
    "fix": "Resolved: one partition and draw stream per arm, original ordered NumPy mean per column, nullable fallback, focused exactness tests and real-cell byte parity."
  },
  {
    "id": "F11",
    "severity": "Major",
    "title": "Exact symbol-origin queries hid Parquet row-group bounds",
    "evidence": "The 88.3-million-row SPDR-023 episode ledger has 719 row groups; 695 contain only one symbol. Each symbol query supplied only a large is_in predicate. Adding inclusive origin-ID bounds while retaining exact membership improved a warm PYTHUSDT scan 3.27× with the same 237,974 rows.",
    "impact": "The analyser repeatedly considered unrelated symbol-major row groups during each one-symbol pass.",
    "fix": "Resolved: add min/max pruning bounds AND the unchanged membership predicate; never replace exact membership with a prefix or range alone."
  }
]
```

## Required checklist for future Nautilus development

Before a large run:

1. Profile preparation, engine replay, report extraction and publication separately.
2. Search critical paths for `to_dicts`, retained `iter_rows(named=True)`, large `to_list`,
   `read_bytes`, repeated joins, prefix recomputation and terminal sets/maps without release.
3. Inventory Nautilus defaults (`frozen_account`, `run_analysis`, risk, message queue, report and
   cache behavior). Disable only work outside the estimand; never change matching/event ordering.
4. Measure worker and parent RSS separately. Worker count is bounded by their **combined** live set,
   not by child RSS alone.
5. Require a failing regression test, corrected bounded fixture, exact artifact/key/value parity,
   one representative full-unit replay, wall/RSS before-after, and clean/resume/parallel hashes.
6. Reject speedups that alter symbols, dates, bars, fences, origins, arms, scheduling, seeds,
   bootstrap draws, precision, row order, schemas or Nautilus event semantics.
7. Consider Rust only after the profile identifies a stable pure-Python kernel; pin the toolchain
   and compare Python/Rust outputs bitwise on synthetic edge cases and a real corpus.
8. When repeated estimates reset the same seed over the same population, compare their partitions
   and draw streams before recomputing them independently. Share only proven-identical positions;
   retain each metric's original arithmetic and a fallback outside the proven domain.
9. For symbol-major Parquet inputs, expose safe min/max predicates alongside—not instead of—exact
   keys so the reader can prune row groups. Prove row membership, order and final artifact hashes.
