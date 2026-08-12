## QA run 1 — 2026-08-11T03:52:39Z — mode: subagent — HEAD d9730b5982c8d4b4e2ed76f2f458d87e2ee70a03

Verdict: REVISE

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Liquidity-level catalogue includes previous 1D/1W/4H/1H levels | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:6,56`; checkpoint `design.md:104` | DEVIATES | Checkpoint excludes 1W. |
| Sweep causal ordering and raid state | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:10-22`; checkpoint `design.md:131-153` | MATCHES | Strict excursion, inclusive return, ambiguity, ordering, and positive reversal are stated. |
| Value-gap interval and profile definition | `docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md:43-49,67`; checkpoint `design.md:158-181` | MATCHES | Includes the strict rule `gap_span < 0.30*(VAH-VAL)`. |
| Timeframes, confirmation references, sessions, ATR, 1m input, fences and holdout | checkpoint `design.md:75-121,141-153,305-307` | MATCHES | 1H references are used for 15m/30m and 1D for 1h. |
| Controls and required emissions | checkpoint `design.md:204-253`; EXP-100 `design.md:46-55` | MATCHES | Design-only review; no implementation exists. |

### Golden-trace diff

No implementation or smoke emission exists. The design-only golden trace is consistent for the matched clauses; the 1W catalogue branch is an explicit deviation.

### Governance & boundary

- Review mode: fresh `subagent` context.
- No experiment was run and no implementation was reviewed.
- Reviewed state: 5 modified files and 11 untracked paths at the reviewer timestamp.
- Literal 100% SoT preservation is not established.

### Issues

1. **REVISE — approved scope differs from literal SoT.** The SoT requires 1W levels, while the checkpoint excludes them. Either restore 1W or record this as a formally operator-approved deviation and change the fidelity claim to “SoT preserved except approved amendment.”

## QA run 3 — 2026-08-11T11:06:37Z — mode: subagent — HEAD bd2aea6fc902c7f10f6e6dc5791d3f5dcb41c11f

Reviewed state before append: dirty files: `python/experiments/EXP-100/qa-review.md`.

Verdict: APPROVE — design-only readiness.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Full level catalogue, including previous completed 1H/4H/1D/1W levels (§5.2) | checkpoint `design.md:104-108`; registry `cf-liqswp-001.md:25-31` | MATCHES | Current checkpoint and registry retain all four timeframes; the earlier 1W issue is superseded/resolved. |
| Scope, confirmation, causal state, and TPO profile (§5.1–§8) | checkpoint `design.md:74-181`; EXP-100 `design.md:21-44` | MATCHES | Design-only trace; scope, 1m input, confirmation rules, and profile definitions agree. |
| Future-destroy control and integrity tripwire (§10) | EXP-100 `design.md:46-68`; checkpoint `design.md:204-234` | MATCHES | Zero-fixed-point derangement, non-vacuity, and `INTEGRITY_Z=2.8` are declared. |
| Required governance, holdout, cost, and amendment declarations | EXP-100 `design.md:6-120`; checkpoint `design.md:19-42` | MATCHES | Required blocks and boundaries are present; no implementation exists. |

### Golden-trace diff

T1–T3 pass by hand against the design: strict excursion with inclusive return, most-recent resolvable attribution while retaining both level objects, and confirmation/profile closure at the completed higher-timeframe close. No implementation or smoke emission exists, so runtime parity remains unverified.

### Governance & boundary

- Fresh-context `subagent` review; no prior sections were rewritten.
- No execution and no holdout data inspection; `python/experiments/EXP-100/code/` is absent.
- TRAIN-only scope, causal timestamps, Nautilus boundary, and no TEST/holdout reads are declared.
- Required zero-cost disclosure, amendment ledger (`0L / 1T / 3N`), derangement destroy, and integrity tripwire pass.
- No MDE, power, detection-floor, minimum-n, or machine-assigned value-verdict machinery is declared.
- Registry family is registered; current checkpoint and registry explicitly include 1W.

### Issues

1. **INFO — implementation does not yet exist.** Code-line fidelity, emission completeness, the one-`BacktestNode` process boundary, derangement regeneration, and smoke emission require a later fresh QA after implementation.

## Compact QA result — 2026-08-11T11:04:59Z — mode: subagent — HEAD bd2aea6fc902c7f10f6e6dc5791d3f5dcb41c11f

Verdict: APPROVE — design-only readiness.

- SoT scope passes: full level catalogue including 1W, declared universes/timeframes, confirmation rules, and online TPO fidelity.
- Required declarations, amendment ledger, causal/Nautilus/holdout boundaries, derangement, and `INTEGRITY_Z` tripwire pass.
- No MDE, power, detection floors, or planned TEST/holdout reads.
- Registry family is registered.
- Implementation is absent; code fidelity, emission completeness, process boundaries, and smoke golden trace remain for post-implementation QA.

## QA run 2 — 2026-08-11T00:00:00Z — mode: subagent — HEAD bd2aea6fc902c7f10f6e6dc5791d3f5dcb41c11f

Reviewed state: clean worktree (no dirty files). Design-only review: `python/experiments/EXP-100/code/` is absent; no implementation, run, or holdout data was inspected.

Verdict: APPROVE

### Design-fidelity trace

| Design clause | Evidence | Verdict | Notes |
|---|---|---|---|
| Full level catalogue, including 1W | checkpoint `design.md:105-108`; registry `cf-liqswp-001.md:25-31` | MATCHES | Full catalogue retained; run 1’s 1W finding is resolved. |
| Scope, universe, timeframe, confirmation, TPO | checkpoint `design.md:74-181`; registry `cf-liqswp-001.md:14-66` | MATCHES | Scope, 1m input, observations, confirmations, online profile, VA/gap rules match SoT. |
| Mandatory declarations and amendment ledger | EXP-100 `design.md:10-120`; checkpoint `design.md:19-42` | MATCHES | Required blocks present; ledger is 0L/1T/3N. |
| Causal/Nautilus/holdout boundaries | EXP-100 `design.md:6,12-16,99-105`; checkpoint `design.md:96-103` | MATCHES | TRAIN-only Nautilus execution and causal state are specified; no TEST/holdout reads. |
| Derangement and integrity tripwire | EXP-100 `design.md:46-68`; checkpoint `design.md:204-234` | MATCHES | Zero-fixed-point derangement, non-vacuity, and `INTEGRITY_Z × bootstrap_SE` with `INTEGRITY_Z=2.8`. |
| No MDE, power, or floors | EXP-100 `design.md:71-84`; checkpoint `design.md:259-280` | MATCHES | No count gate or research-power machinery; thin rows remain visible. |
| Registry preconditions | `cf-liqswp-001.md:1-12,68-92` | MATCHES | Family REGISTERED; planned counted TEST/holdout reads are zero. |

### Golden-trace note

T1–T3 pass by hand: strict excursion plus inclusive return, most-recent resolvable attribution while retaining both objects, and confirmation/profile closure at the completed higher-timeframe close. No code or smoke emission exists, so implementation parity remains unverified.

### Governance & boundary

- Fresh-context `subagent` mode; run 1 preserved unchanged.
- No code or holdout data inspected; `code/` is absent.
- Causal ordering, Nautilus boundary, TRAIN fence, and no TEST/holdout use are declared.
- Future-destroy is a zero-fixed-point derangement with bite and non-vacuity checks.
- Amendment ledger: 0 looser / 1 tighter / 3 neutral; no three-direction streak.
- No MDE, power curve, detection floor, minimum-n veto, or machine-assigned value verdict.
- Canonical zero-cost disclosure is present; prohibited net/tradable/deployable claims are refused.

### Issues

1. **INFO — implementation gate remains open.** Code-line fidelity, derangement regeneration, one-`BacktestNode` process boundaries, emission completeness, and an actual golden-trace smoke emission require a later fresh QA run after implementation.

1. **REVISE — approved scope differs from literal SoT.** The SoT requires 1W levels, while the checkpoint excludes them. Either restore 1W or record this as a formally operator-approved deviation and change the fidelity claim to “SoT preserved except approved amendment.”

## QA run 4 — 2026-08-12T16:30:00Z — mode: subagent — HEAD 7a8417aabb93b3d4c5dc4300910e5cc38d28f77b

Reviewed state: first post-implementation QA after the four-gap remediation. Fresh-context subagent (did not implement EXP-100). `git rev-parse` not available in this tool environment; HEAD taken from `.git/refs/heads/main` = `7a8417aabb93b3d4c5dc4300910e5cc38d28f77b`. Dirty-file list unavailable without `git status`; live tree reviewed under `python/src/xen/exp100/`, `python/experiments/EXP-100/code/run_experiment.py`, `python/tests/test_exp100_*.py`, design/SoT/registry/spec paths listed in the task. No experiment execution launched.

Verdict: **REVISE**

### Remediated gaps (re-check)

| Gap | Evidence | Verdict |
|---|---|---|
| Production level catalogue (not only seed_level) | `levels.py` `LevelCatalogue` + `PERIOD_MINUTES`/`SESSION_WINDOWS`/`ROLLING_PERIODS` incl. 1W; `processor.py` auto catalogue insert | **MATCHES** |
| LEVEL_CLOSE not vs swept raid price | `processor.py:491-515` uses previous reference high/low; emits `confirmation_level_high/low`; tests `test_level_close_*` | **MATCHES** |
| strong_move + destroy non-vacuity | `processor.py:406-442` `strong_move = swing_atr > max_excursion_atr`; `run_experiment.py:427-444` value_columns include `strong_move`, fail if eligible and unchanged | **MATCHES** |
| Publication integrity TPO + raid/state | `run_experiment.py:234-295` DEFINED profiles require `tpo_conservation_ok`; raid↔profile ids; terminal statuses; event counts | **MATCHES** |

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Family A/B/C catalogue: PREVIOUS_1H/4H/1D/1W; Asia/Europe/America DST; rolling 16..256 (checkpoint §5.2; registry; EXP-100 scope) | `config.py:17-32`; `levels.py:21-40,99-145`; `processor.py:111-121,517-569` | **MATCHES** | Auto catalogue + `SUPERSEDED_NO_RAID` for unraided same-side. |
| Sessions IANA/DST: Tokyo 09–18, London 08–17, NY 08–17 (checkpoint §5.2) | `levels.py:28-32,164-222` | **MATCHES** | ZoneInfo local windows; emit after session end. |
| Strict 1m excursion + later inclusive return; same-1m AMBIGUOUS (registry raid state; SoT; golden T1) | `processor.py:214-242` evaluates on **observation** OHLC only | **DEVIATES** | Registry: “1m high strictly above the level”. Same observation cross-and-return → `AMBIGUOUS_INTRABAR` even when separate 1m bars. Silent deviation; no design DEVIATIONS block. |
| Most-recent resolvable primary attribution; retain other levels (checkpoint §6; golden T2) | `processor.py:343-397,361-379` | **MATCHES** | Latest by `(sweep_ts_ns, raid_id)`; earlier raids remain live without primary flag. |
| Confirmation refs: 1H for 15m/30m, 1D for 1h; methods BREAKOUT_BAR vs LEVEL_CLOSE (checkpoint §7) | `config.py:75-80`; `processor.py:57-59,491-515` | **MATCHES*** | *LEVEL_CLOSE and BREAKOUT_BAR share the same previous-reference extreme rule (intentional vs raid price). Separate strata; numeric identity disclosed here. |
| Confirmation timestamp = completed reference close, not next open (golden T3) | `processor.py:365,338-340` | **MATCHES** | `confirmation_ts_ns = bar.ts_event_ns` of completed reference. |
| Expected-side sweep vs excursion-side breakout; swing ends at first opposing after confirm (checkpoint §7) | `processor.py:343-383` | **MATCHES** | `FAILED_BREAKOUT` / `COMPLETED`; right-censor paths in `finish` / `_censor_status`. |
| Online TPO: 1m bins, 0.10×ATR, VA≥70%, gap≥30% VA mass, tight `gap_span < 0.30×VA_width`, reset on new max (checkpoint §8) | `tpo.py:47-175`; `processor.py:186-212` | **MATCHES** | Conservation, tight boundary, and reset covered by tests. |
| Outcomes: `swing_atr`, duration, `strong_move = swing_atr > max_excursion_atr` (checkpoint §9) | `processor.py:406-442`; `strategy.py:204-212` | **MATCHES** | Post-confirmation `swing_extreme` vs max excursion in ATR units. |
| Required raid emissions incl. raw/bps/ATR distances; gap_span_atr; gap/VA ratio (checkpoint §11) | `strategy.py:164-214`; `tpo.py:154-175` | **MISSING** | Emits raw + ATR + `duration_ns` + `gap_span`/`va_width`/`tight_gap`. **No** `*_bps`, **no** `gap_span_atr`, **no** `gap_span_va` (or equivalent). |
| Future-destroy derangement, zero fixed points, non-vacuity on swing/duration/strong_move (EXP-100 control; checkpoint §10) | `control.py:100-141,163-269`; `run_experiment.py:426-454` | **MATCHES** | Cyclic derangement; rejects fixed points; runner records/fails vacuity when eligible rows exist. |
| One BacktestNode per process; streaming; no analysis; frozen account (impl design; L-31) | `run_experiment.py:48-52,102-133,358-377` | **MATCHES** | `_CELL_NODE_CREATED` guard; `chunk_size`; `run_analysis=False`; `frozen_account=True`. |
| TRAIN-only fence; no holdout (EXP-100; pipeline OOS) | `run_experiment.py:349-351` | **MATCHES** | `assert_within_fence(..., band="TRAIN")`. |
| Zero-cost; no local accounting; no strategy fills objective | `run_experiment.py:199,409-421`; empty fills/orders/positions via emission; no banned accounting defs in `code/` | **MATCHES** | `cost_model: NO_COST_CHARGED`. |
| Causal ATR(14) / regime on completed observation bars (checkpoint §5.3) | `features.py:91-174`; `processor.py:244-248` | **MATCHES** | Raid path uses pre-update ATR (`atr_before`). |

### Golden-trace diff

Hand-check against **design** expectations (not implementation as oracle):

| Event | Expected (design) | Implemented logic | Verdict |
|---|---|---|---|
| **T1** | Active high 100.00; 1m high=101.20 establishes excursion max 1.20; later 1m inclusive touch 100.00 → one completed raid, `prior_raid_count=0` | Raid start/return only at observation close. If both 1m bars share one observation window → `AMBIGUOUS_INTRABAR`, not a completed raid. Max excursion path is fine only after a non-returning observation beyond the level. | **FAIL** |
| **T2** | Second high level raided before confirm; most recent resolvable gets primary attribution; both level/raid objects retained | `_latest_active_raid` + `primary_attribution`; earlier raid stays active until its own terminal | **PASS** |
| **T3** | Confirm at completed 1H close (not next open); profile ends at that close; later opposing reference ends swing | `confirmation_ts_ns` / profile finalize at reference close; opposing → `COMPLETED` | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context | PASS | mode: subagent; no implementation work in this conversation |
| Append-only qa-review | PASS | prior runs 1–3 left intact |
| Design mandatory blocks | PASS | mechanism, object-identity, control, tripwire, bands, sample-size, golden, hard/informative, ZERO-COST in EXP-100 `design.md` |
| Zero-cost model | PASS | design verbatim; runner metadata `NO_COST_CHARGED`; no live cost stack imports in exp100 |
| No local accounting | PASS | `code/run_experiment.py` has no `BANNED_LOCAL_DEFS`; apparatus emits empty ledgers |
| No Python strategy backtest | PASS | Nautilus `BacktestNode` only |
| No holdout / TRAIN-only | PASS | fence assert TRAIN; no TEST path |
| Derangement destroy (L-28) | PASS | zero fixed points; cycle mapping |
| One BacktestNode/process (L-31) | PASS | process guard + CLI one cell |
| No MDE / power floors | PASS | none in design or exp100 code |
| Amendment ledger | PASS | inherits 0L / 1T / 3N; no ≥3 one-direction streak |
| Registry family | PASS | `CF-LIQSWP-001` REGISTERED; planned counted TEST/holdout = 0 |
| No execution | PASS | review only |

### Issues

1. **REVISE — high — raid lifecycle is observation-bar, not 1m (SoT/registry/golden T1).**  
   - Design: registry raid state + checkpoint golden T1; SoT “bar by bar” with engine 1m.  
   - Code: `python/src/xen/exp100/processor.py:214-242` (`_on_observation_bar` beyond/return/ambiguous).  
   - Required change: detect strict excursion, inclusive return, and same-bar ambiguity on **source 1m** bars (observation TF remains the stratum/ATR/rolling unit). Or, if observation-bar detection is intended, add an operator-approved design amendment and rewrite golden T1 — do not leave a silent deviation.  
   - `FAILING_ARTIFACT`: `python/src/xen/exp100/processor.py` (and tests that encode observation-bar raids).  
   - `REQUIRED_SKILL`: experiment-developer (code) or quant-designer (if design is to change).

2. **REVISE — medium — required emission columns incomplete (checkpoint §11).**  
   - Design: raw, **bps**, and ATR for distances; **gap_span_atr** and **gap_span_va** (gap/VA ratio).  
   - Code: `strategy.py` raid schema ~164-214; `tpo.py` finalize ~154-175 — raw/`swing_atr`/`max_excursion_atr`/`gap_span`/`va_width`/`tight_gap` only.  
   - Required change: emit bps fields for excursion/swing (and any other price distances the contract lists), plus `gap_span_atr` and `gap_span_va` (or identically named contract fields) on defined profiles.  
   - `FAILING_ARTIFACT`: emission schemas in `strategy.py` / profile finalize in `tpo.py` / processor terminal rows.  
   - `REQUIRED_SKILL`: experiment-developer.

3. **INFO — LEVEL_CLOSE ≡ BREAKOUT_BAR numerically under current reference definition.**  
   - Both use previous completed confirmation-reference high/low (`processor.py:502-515`). Separate method strata remain; overlap is disclosed. Not blocking if design accepts full numeric identity for the frozen 1H/1D confirmation references.

4. **INFO — future-destroy is opt-in (`--destroy-control`).**  
   - Mechanism and non-vacuity enforcement exist (`run_experiment.py:426-444`). Full matrix execution must enable the control for the hard integrity tripwire.

5. **INFO — PREVIOUS_1W uses fixed 10080-minute epoch buckets** (`levels.py:25`, `StreamingOHLC` minute//period).  
   - Week start is epoch-aligned (Thursday UTC), not a stated calendar week. Design does not pin week boundaries; pin explicitly if calendar weeks are required.

## QA run 5 — 2026-08-12T21:15:00Z — mode: subagent — HEAD 7a8417aabb93b3d4c5dc4300910e5cc38d28f77b

Reviewed state: independent post-fix QA after run 4 REVISE remediation. Fresh-context subagent (did not implement EXP-100). HEAD from `.git/refs/heads/main` = `7a8417aabb93b3d4c5dc4300910e5cc38d28f77b`. Dirty-file list unavailable without `git status`; live tree reviewed under `python/src/xen/exp100/`, `python/experiments/EXP-100/code/run_experiment.py`, `python/tests/test_exp100_*.py`, design/SoT/registry paths listed in the task. No experiment execution launched.

Verdict: **APPROVE**

### Remediated gaps (re-check, including run 4)

| Gap | Evidence | Verdict |
|---|---|---|
| Production level catalogue (not only seed_level) | `levels.py` `LevelCatalogue` + `PERIOD_MINUTES`/`SESSION_WINDOWS`/`ROLLING_PERIODS` incl. 1W; `processor.py:111-124` auto catalogue insert; `test_exp100_levels.py`, `test_processor_creates_previous_period_levels_without_seed` | **MATCHES** |
| LEVEL_CLOSE not vs swept raid price | `processor.py:512-536` previous reference high/low; emits `confirmation_level_high/low`; `test_level_close_*` | **MATCHES** |
| strong_move + destroy non-vacuity | `processor.py:420-440` `strong_move = swing_atr > max_excursion_atr`; `run_experiment.py:426-444` value_columns include `strong_move`, fail if eligible and unchanged | **MATCHES** |
| Publication integrity TPO + raid/state | `run_experiment.py:234-295` DEFINED profiles require `tpo_conservation_ok`; raid↔profile ids; terminal statuses; event counts | **MATCHES** |
| **Run 4 #1** raid lifecycle on source 1m bars | `processor.py:105-108,217-252` `_process_source_raid_state` on each source minute; `test_raid_start_and_return_use_source_one_minute_bars`, `test_processor_keeps_ambiguous_same_bar_raid_out_of_primary_result` | **MATCHES** |
| **Run 4 #2** emission columns bps + gap ratios | `processor.py:422-461` `max_excursion_bps`/`swing_bps`; `strategy.py:185-186,211,237-238` schemas; `tpo.py:154-175` `gap_span_atr`/`gap_span_va` | **MATCHES** |

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Family A/B/C catalogue: PREVIOUS_1H/4H/1D/1W; Asia/Europe/America DST; rolling 16..256 (checkpoint §5.2; registry; EXP-100 scope) | `config.py:17-32`; `levels.py:21-40,99-145`; `processor.py:111-124,538-590` | **MATCHES** | Auto catalogue + `SUPERSEDED_NO_RAID` for unraided same-side. |
| Sessions IANA/DST: Tokyo 09–18, London 08–17, NY 08–17 (checkpoint §5.2) | `levels.py:28-32,164-222` | **MATCHES** | ZoneInfo local windows; emit after session end. |
| Strict 1m excursion + later inclusive return; same-1m AMBIGUOUS (registry raid state; SoT; golden T1) | `processor.py:105-108,217-252` | **MATCHES** | Strict beyond / inclusive return / same-1m AMBIGUOUS on source minutes; observation TF remains ATR/rolling unit. |
| Most-recent resolvable primary attribution; retain other levels (checkpoint §6; golden T2) | `processor.py:347-401,365-387` | **MATCHES** | Latest by `(sweep_ts_ns, raid_id)`; earlier raids remain live without primary flag. |
| Confirmation refs: 1H for 15m/30m, 1D for 1h; methods BREAKOUT_BAR vs LEVEL_CLOSE (checkpoint §7) | `config.py:75-80`; `processor.py:57-59,512-536` | **MATCHES*** | *LEVEL_CLOSE and BREAKOUT_BAR share previous-reference extreme rule (not raid price). Separate strata; numeric identity disclosed. |
| Confirmation timestamp = completed reference close, not next open (golden T3) | `processor.py:365-383` | **MATCHES** | `confirmation_ts_ns = bar.ts_event_ns` of completed reference. |
| Expected-side sweep vs excursion-side breakout; swing ends at first opposing after confirm (checkpoint §7) | `processor.py:342-387` | **MATCHES** | `FAILED_BREAKOUT` / `COMPLETED`; right-censor paths in `finish` / `_censor_status`. |
| Online TPO: 1m bins, 0.10×ATR, VA≥70%, gap≥30% VA mass, tight `gap_span < 0.30×VA_width`, reset on new max (checkpoint §8) | `tpo.py:47-182`; `processor.py:189-215` | **MATCHES** | Conservation, tight boundary, reset, `gap_span_atr`/`gap_span_va` on DEFINED profiles. |
| Outcomes: `swing_atr`, duration, `strong_move = swing_atr > max_excursion_atr` (checkpoint §9) | `processor.py:403-464`; `strategy.py:209-214` | **MATCHES** | Post-confirmation `swing_extreme` vs max excursion in ATR units. |
| Required raid/profile emissions incl. raw/bps/ATR distances; gap_span_atr; gap/VA ratio (checkpoint §11) | `processor.py:422-461`; `strategy.py:164-247`; `tpo.py:152-177` | **MATCHES** | `max_excursion`/`_bps`/`_atr`; `swing_price`/`swing_bps`/`swing_atr`; `gap_span`/`gap_span_atr`/`gap_span_va`/`tight_gap`. |
| Future-destroy derangement, zero fixed points, non-vacuity on swing/duration/strong_move (EXP-100 control; checkpoint §10) | `control.py:100-141,163-269`; `run_experiment.py:426-454` | **MATCHES** | Cyclic derangement; rejects fixed points; runner records/fails vacuity when eligible rows exist. |
| One BacktestNode per process; streaming; no analysis; frozen account (impl design; L-31) | `run_experiment.py:48-52,102-133,358-377` | **MATCHES** | `_CELL_NODE_CREATED` guard; `chunk_size`; `run_analysis=False`; `frozen_account=True`. |
| TRAIN-only fence; no holdout (EXP-100; pipeline OOS) | `run_experiment.py:349-351` | **MATCHES** | `assert_within_fence(..., band="TRAIN")`. |
| Zero-cost; no local accounting; no strategy fills objective | `run_experiment.py:199,409-421`; empty fills/orders/positions via emission; no banned accounting defs in `code/` | **MATCHES** | `cost_model: NO_COST_CHARGED`. |
| Causal ATR(14) / regime on completed observation bars (checkpoint §5.3) | `features.py:91-174`; `processor.py:254-276` | **MATCHES** | Raid path uses pre-observation-update ATR (`self._atr.value` before `_on_observation_bar`). |

### Golden-trace diff

Hand-check against **design** expectations (not implementation as oracle):

| Event | Expected (design) | Implemented logic | Verdict |
|---|---|---|---|
| **T1** | Active high 100.00; 1m high=101.20 establishes excursion max 1.20; later 1m inclusive touch 100.00 → one completed raid, `prior_raid_count=0` | `_process_source_raid_state`: first source minute starts raid with `max_excursion=1.20`, `return_ts_ns=None`; later source minute sets inclusive return; not same-1m AMBIGUOUS; `prior_raid_count=0`. Covered by `test_raid_start_and_return_use_source_one_minute_bars`. | **PASS** |
| **T2** | Second high level raided before confirm; most recent resolvable gets primary attribution; both level/raid objects retained | `_latest_active_raid` + `primary_attribution`; earlier raid stays active until its own terminal | **PASS** |
| **T3** | Confirm at completed 1H close (not next open); profile ends at that close; later opposing reference ends swing | `confirmation_ts_ns` / profile finalize at reference close; opposing → `COMPLETED` | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context | PASS | mode: subagent; no implementation work in this conversation |
| Append-only qa-review | PASS | prior runs 1–4 left intact; this is run 5 only |
| Design mandatory blocks | PASS | mechanism, object-identity, control, tripwire, bands, sample-size, golden, hard/informative, ZERO-COST in EXP-100 `design.md` |
| Zero-cost model | PASS | design verbatim; runner metadata `NO_COST_CHARGED`; no live cost stack imports in exp100 |
| No local accounting | PASS | `code/run_experiment.py` has no banned accounting primitives; apparatus emits empty ledgers |
| No Python strategy backtest | PASS | Nautilus `BacktestNode` only |
| No holdout / TRAIN-only | PASS | fence assert TRAIN; no TEST path |
| Derangement destroy (L-28) | PASS | zero fixed points; cycle mapping |
| One BacktestNode/process (L-31) | PASS | process guard + CLI one cell |
| No MDE / power floors | PASS | none in design or exp100 code |
| Amendment ledger | PASS | inherits 0L / 1T / 3N; no ≥3 one-direction streak |
| Registry family | PASS | `CF-LIQSWP-001` REGISTERED; planned counted TEST/holdout = 0 |
| No execution | PASS | review only |

### Issues

1. **INFO — LEVEL_CLOSE ≡ BREAKOUT_BAR numerically under current reference definition.**  
   - Both use previous completed confirmation-reference high/low (`processor.py:512-536`). Separate method strata remain; overlap is disclosed in design §7 and code comments. Not blocking.

2. **INFO — future-destroy is opt-in (`--destroy-control`).**  
   - Mechanism and non-vacuity enforcement exist (`run_experiment.py:426-444`). Full matrix execution must enable the control for the hard integrity tripwire.

3. **INFO — PREVIOUS_1W uses fixed 10080-minute epoch buckets** (`levels.py:25`, `StreamingOHLC` minute//period).  
   - Week start is epoch-aligned (Thursday UTC), not a stated calendar week. Design does not pin week boundaries; pin explicitly if calendar weeks are required.

No blocking REVISE/REJECT issues. Ready for the operator execution gate.

## QA run 6 — 2026-08-12T00:31:13Z — mode: subagent — HEAD 99995fed26671d75c693f1d682f8d5f118b46a09

Reviewed state before append: modified `python/experiments/EXP-100/{code/run_experiment.py,design.md,qa-review.md}`, `python/src/xen/exp100/{__init__.py,processor.py,state_store.py,strategy.py,tpo.py}`, and `python/tests/{test_exp100_control.py,test_exp100_processor.py,test_exp100_state_store.py}`; untracked `.codex/config.toml`, two progress/implementation plans, the earlier memory-safe design spec, `python/experiments/EXP-100/results/`, `python/src/xen/exp100/levels.py`, and `python/tests/test_exp100_levels.py`. The approved batching spec itself is tracked. Fresh-context subagent; reviewer did not implement the change.

Verdict: **APPROVE**

### Design-fidelity trace

| Design clause (§ref) | Code/evidence | Verdict | Notes |
|---|---|---|---|
| One outer SQLite transaction per source minute (batching spec, Approved change) | `processor.py:97-134`; `state_store.py:134-160`; `test_exp100_processor.py:212-229` | **MATCHES** | `on_one_minute_bar` opens one `BEGIN IMMEDIATE`; trace test observes exactly one `COMMIT`. Memory observation remains after the transaction. |
| Standalone store calls retain auto-commit (Approved change; test-first item 3) | `state_store.py:158-160,173-243,545-567`; `test_exp100_state_store.py:177-183` | **MATCHES** | `_commit_if_standalone` commits only at depth zero; independent observer sees the row immediately. |
| Existing atomic profile operations join the outer transaction without nested `BEGIN` (Approved change; test-first item 4) | `state_store.py:330-363,411-537`; `test_exp100_state_store.py:159-174`; independent combined increment/reset check | **MATCHES** | Depth ownership suppresses nested `BEGIN`; range increments, start/reset, gap-mask replacement, and cleanup retain standalone atomicity. |
| Exception rolls back all source-minute SQLite mutations (Approved change; test-first item 2) | `state_store.py:141-156`; `test_exp100_state_store.py:159-174`; independent combined level+raid+increment+reset injection | **MATCHES** | Independent check restored the prior generation/bins and left no new level or raid. Inner transaction exceptions propagate to the owning outer rollback. |
| Processing and append-only sink order unchanged (Approved change) | `processor.py:105-125`; retained vs new smoke `event_log.jsonl` SHA-256 `24ce58a...b10cbe7` | **MATCHES** | The transaction wrapper surrounds the run-5-approved order without rearranging calls. Event logs are byte-identical. Sink writes remain append-only; runner publication staging remains unchanged. |
| No schemas, emitted columns, timestamps, calculations, labels, identities, controls, costs, or estimands change (Goal; exclusions) | exact smoke comparison; `run_metadata.json`; estimand gate | **MATCHES** | `bar_marks` (except permitted `state_bytes`), `levels`, `raids`, `tpo_profiles`, and fixed-seed `raids_destroyed` are exactly equal in schema, order, row count, and values. Empty fills/orders/positions also match. |
| No pruning, lifetime change, partitioning, materialisation, TEST/holdout, or second optimization (Explicit exclusions) | `processor.py:97-134`; `state_store.py:1-160`; smoke fence | **MATCHES** | Change is transaction ownership/depth only; cursor streaming and active-object lifetime are retained. Smoke is pinned TRAIN data through 2023-12-03. |
| Re-profile same one-/two-day slices and reduce wall time (Verification gates; success) | `/tmp/exp100-batching-smoke-20260812/{one-day.prof,two-day.prof}` | **MATCHES** | cProfile totals are 4.23 s and 24.43 s versus retained 15.7 s and 124.7 s observations. Commit frequency is reduced to one transaction per source minute. |

### Golden-trace diff

The storage boundary does not alter EXP-100 event logic. Independent retained/new smoke comparison found exact ordered equality for all research-bearing rows and a byte-identical event log, so the previously approved hand-derived traces remain unchanged:

| Event | Design expectation | Batching implementation/evidence | Verdict |
|---|---|---|---|
| **T1** | Separate source-minute strict excursion and later inclusive return; max excursion 1.20; prior count 0 | `raids.parquet` is exactly equal across the full smoke; source-minute order in `processor.py:105-125` is unchanged | **PASS** |
| **T2** | Most-recent resolvable attribution while retaining both objects | `levels.parquet`, `raids.parquet`, and ordered event payloads are exactly equal | **PASS** |
| **T3** | Confirmation/profile timestamp at completed reference close; later opposing close ends swing/profile | `raids.parquet`, `tpo_profiles.parquet`, and ordered event payloads are exactly equal | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context / append-only review | PASS | mode `subagent`; prior QA runs were not rewritten |
| Focused verification | PASS | 73 tests passed in 8.39 s: store, processor, TPO, runner, control, levels, features, streaming |
| Static check | PASS | Ruff passed on batching implementation and focused tests |
| Exact research-output equivalence | PASS | retained baseline vs `/tmp/exp100-batching-smoke-20260812/three-day`: row counts 288/144/1561/1561; all non-telemetry values exact; destroy output exact |
| Event/order equivalence | PASS | event log byte-identical; same SHA-256 `24ce58a1e6df2b5ed4b6953dbf28c8552de0dc187ba4d8463a78b9065b10cbe7` |
| Metadata scope | PASS | only `generated_utc` and `memory.peak_rss_bytes` differ; run config, counts, event hash, control, and state snapshot otherwise identical |
| Memory bound | PASS | 301,711,360-byte peak vs retained 301,203,456 bytes; no new Python materialisation or asymptotic structure |
| Estimand/fence/zero cost | PASS | independent `/tmp/exp100-batching-smoke-20260812/qa_estimand_validation.json`: `blocking_pass=true`, pinned manifest/fence, no cost charged, reconciliation true |
| No local accounting | PASS | `check_no_local_accounting("experiments/EXP-100/code")` returned `ok=true` |
| No event/order/estimand/design change | PASS | exact emissions plus batching-only transaction boundary; no live cost imports, power machinery, TEST, or holdout path |

### Issues

1. **INFO — approved telemetry exception was not needed in this smoke.** `bar_marks.state_bytes` was permitted to differ, but it also matched exactly. Metadata differed only in generation time and peak RSS (about 0.5 MB higher, operational and non-asymptotic).

No blocking REVISE/REJECT findings. The safe SQLite batching change is ready for the operator's execution gate; QA does not launch the full matrix.

## Correction addendum to QA run 6 — 2026-08-12T00:32:42Z — mode: subagent — HEAD 99995fed26671d75c693f1d682f8d5f118b46a09

Verdict: **APPROVE (unchanged)**

Run 6's INFO statement that `bar_marks.state_bytes` also matched was incorrect. Independent direct comparison of the retained and batching-smoke Parquet tables found:

- full `bar_marks` table equality: **false**;
- equality after removing `state_bytes`: **true**;
- `state_bytes` differences: **24 of 288 rows**;
- examples (zero-based row index; retained → batching): row 57, `278528 → 274432`; row 100, `622592 → 614400`; row 113, `704512 → 700416`.

This is exactly the operator-approved exception for SQLite physical-layout telemetry. All research-bearing columns remain exactly equal, so the batching QA verdict remains **APPROVE** with no blocking findings.

## QA run 7 — 2026-08-12T00:49:50Z — mode: subagent — HEAD 43541cb5ff2319b156aedd49c219ee9c081fca8b

Reviewed state before append: modified `python/experiments/EXP-100/{code/run_experiment.py,design.md,qa-review.md}`, `python/src/xen/exp100/{__init__.py,processor.py,state_store.py,strategy.py,tpo.py}`, and `python/tests/{test_exp100_control.py,test_exp100_processor.py,test_exp100_state_store.py}`; untracked `.codex/config.toml`, two prior implementation/progress plans, the prior memory-safe design spec, `python/experiments/EXP-100/results/`, `python/src/xen/exp100/levels.py`, and `python/tests/test_exp100_levels.py`. Fresh-context subagent; reviewer did not implement the SQL or scan changes. No profiling was run.

Verdict: **APPROVE**

### Design-fidelity trace

| Design clause (§ref) | Code/evidence | Verdict | Notes |
|---|---|---|---|
| Stage 1: replace only the per-bin `execute` loop with one generator-fed `executemany`; retain identical ordered inclusive SQL upserts (optimization design, Stage 1) | `state_store.py:432-450`; `test_exp100_state_store.py:212-239` | **MATCHES** | Same `INSERT ... ON CONFLICT ... count + 1`; generator yields `low..high` ascending, including negative indexes; no bin list is materialized. |
| Stage 1: preserve separate profile conservation update and exact totals (Stage 1) | `state_store.py:451-461`; focused test; exact smoke tables | **MATCHES** | `bracket_count += 1`; `expected_tpo_total += high-low+1`; test verifies six bins `-2..3`, bracket count 1, expected total 6. |
| Stage 1: preserve transaction ownership, rollback, standalone atomicity, schema/pragmas (Stage 1 exclusions) | `state_store.py:134-160,432-461`; transaction tests `170-209`; prior QA run 6 | **MATCHES** | Bulk write stays inside the existing nested transaction helper. No schema, pragma, journal, or transaction-boundary change belongs to Stage 1. |
| Stage 2: one streaming existing-raid processing cursor in profile → swing → return order (optimization design, Stage 2) | `processor.py:105-109,169-188`; `test_exp100_processor.py:233-255` | **MATCHES** | One generator cursor handles all three operations without row materialization. Reference-selection scans remain separately unchanged as explicitly allowed. |
| Stage 2: new raids do not enter the existing-raid pass until the next source minute (Stage 2) | `processor.py:105-109,229-257,282-344`; exact smoke; source-minute tests | **MATCHES** | Existing raids are scanned before the active-level start/ambiguity pass. Creation retains the already-approved first-bar profile initialization; return/update scanning begins next minute. |
| Stage 2: operational open-raid telemetry uses exact post-transaction scalar count, including new raids (Stage 2 clarification) | `state_store.py:208-213`; `processor.py:127-134,614-615`; state/count and cursor-count tests | **MATCHES** | `SELECT COUNT(*) ... active = 1` runs after commit and does not decode payloads. Active/inactive test returns exactly 1. |
| Cumulative output-equivalence contract | retained baseline vs `/tmp/exp100-stage2-tpo-20260812/three-day` and `/tmp/exp100-stage3-scan-20260812/three-day` | **MATCHES** | Ordered `levels`, `raids`, `tpo_profiles`, `raids_destroyed`, empty ledgers, and all `bar_marks` except `state_bytes` are exact; event log bytes are identical. |
| No research, control, fence, cost, schema, or estimand change (goal/exclusions) | live diff; exact emissions; both gate artifacts | **MATCHES** | Optimization is storage/cursor-only. No methodology, object lifetime, reference scan, TEST/holdout, cost, or governance change. |

### Golden-trace diff

The optimizations do not change event rules. Independent ordered table equality and byte-identical event logs preserve the already hand-derived trace:

| Event | Design expectation | Cumulative implementation/evidence | Verdict |
|---|---|---|---|
| **T1** | Strict source-minute excursion, later inclusive return, max excursion 1.20, prior count 0 | `processor.py:169-188,229-257`; exact `raids.parquet`; focused golden-T1 test | **PASS** |
| **T2** | Most-recent resolvable attribution while retaining both objects | Exact ordered `levels.parquet`, `raids.parquet`, and event-log bytes across retained/Stage-1/cumulative smokes | **PASS** |
| **T3** | Confirmation/profile at completed reference close; later opposing close ends swing/profile | Exact ordered `raids.parquet`, `tpo_profiles.parquet`, and event-log bytes across all smokes | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context / append-only QA | PASS | dedicated subagent; no implementation work; runs 1–6 and correction retained unchanged |
| Red-green structure | PASS | pre-change diff necessarily fails Stage-1 `executemany_calls == 1`; pre-change processor had separate profile/return scans plus telemetry cursor; current focused tests pass |
| Focused tests | PASS | 4 targeted tests passed in 0.76 s |
| Full EXP-100 tests | PASS | 67 tests passed in 9.11 s |
| Static check | PASS | Ruff passed for `src/xen/exp100`, all EXP-100 tests, and runner |
| Stage-1 exact safety smoke | PASS | rows `levels=144`, `raids=1561`, `tpo_profiles=1561`, `raids_destroyed=1561`, `bar_marks=288`; every research field/order exact; 24 approved `state_bytes` differences |
| Cumulative exact safety smoke | PASS | same exact counts and equality; event SHA-256 `24ce58a1e6df2b5ed4b6953dbf28c8552de0dc187ba4d8463a78b9065b10cbe7` |
| Metadata and bounded memory | PASS | only `generated_utc` and peak RSS differ; Stage 1 peak 299,827,200 bytes and cumulative peak 300,941,312 bytes vs retained 301,203,456 bytes; generator/cursors remain bounded |
| Stage-1 integrity gate | PASS | `blocking_pass=true`; pinned manifest hash; TRAIN last bar 2023-12-03 23:59; schema/reconciliation/no-cost pass |
| Cumulative integrity gate | PASS | `blocking_pass=true`; same pinned fence, schema, reconciliation, and `NO_COST_CHARGED` checks pass |
| No local accounting | PASS | independent `check_no_local_accounting("experiments/EXP-100/code")` returned `ok=true` |
| No methodology/governance change | PASS | design diff changes status only; no holdout, power/MDE, cost, emission schema, control, or estimand change |
| Profiling gate respected | PASS | QA ran no profiler; cumulative profiling remains operator-authorized only after this approval |

### Issues

1. **INFO — approved physical-state exception occurs in both safety smokes.** `bar_marks.state_bytes` differs in 24 of 288 rows, while every other bar-mark field is exact. This is SQLite page-layout telemetry and is explicitly permitted by the optimization design.

No blocking REVISE/REJECT findings. The cumulative SQL and active-raid scan optimizations are approved for the operator's profiling gate; QA does not launch profiling.
