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

## QA run 8 — 2026-08-12T02:05:12Z — mode: subagent — HEAD 46116fff4c6c2da0ef364d2cd01eca2f06719c73

Reviewed state before append: modified `docs/superpowers/specs/2026-08-12-exp-100-execution-apparatus-design.md`, `python/experiments/EXP-100/{code/run_experiment.py,design.md}`, `python/src/xen/exp100/{features.py,processor.py}`, `python/src/xen/nautilus/catalog_fence.py`, and `python/tests/{test_estimand_validation_v2.py,test_exp100_processor.py,test_exp100_runner.py}`; untracked `python/experiments/EXP-100/code/run_matrix.py` and `python/tests/test_exp100_matrix_runner.py`. Fresh-context subagent; reviewer did not implement the apparatus. Baseline requested and reviewed: HEAD `46116ff` plus the listed dirty state.

Verdict: **APPROVE**

### Design-fidelity trace

| Design clause (§ref) | Code/evidence | Verdict | Notes |
|---|---|---|---|
| Venue-specific repository pins and actual attestation paths (apparatus spec §Venue pins) | `run_experiment.py:57-97,394-401`; `catalog_fence.py:153-169`; repository SHA-256 checks | **MATCHES** | Bybit manifest SHA `35d3375e…00448`; cTrader INFR-021 SHA `4cdc7b01…6de0`. Attestation path derives from the loaded manifest and must remain inside the repository. |
| cTrader engine venue identity uses catalog case (apparatus testing item 2) | `run_experiment.py:130,152-160`; `test_exp100_runner.py:153-173`; real safety emission | **MATCHES** | `InstrumentId("EURUSD.CTrader")` produces engine venue `CTrader`; real BacktestNode safety run completed. |
| cTrader closure rule: aligned, strictly increasing observations; no synthetic bars/TPO; reset incomplete aggregation (approved clarification) | `processor.py:97-108,596-608`; `features.py:30-56`; focused chronology test; raw safety catalog/emission inspection | **MATCHES** | Raw safety slice has 1,545 observed minutes, 13 absent minutes, strict ordering/alignment; emission has 97 complete 15m bars each with `source_bars=15`. Gaps reset partial windows; TPO consumes observed bars only. |
| Deterministic exact 936-cell frozen grid (apparatus §Frozen matrix) | `run_matrix.py:18-46,83-131`; `test_exp100_matrix_runner.py:20-31,48-54` | **MATCHES** | Independently expanded 720 Bybit + 216 cTrader cells; 936 unique stable IDs; 1H reference for 15m/30m and 1D for 60m. |
| Exact one-cell 30-day preflight (apparatus §Scheduler contract) | `run_matrix.py:47-48,108-121`; `test_exp100_matrix_runner.py:34-45` | **MATCHES** | BTCUSDT, 15m, BREAKOUT_BAR, 1H, PREVIOUS_1H; `2023-11-18T00:00Z` through `2023-12-17T23:59Z`. |
| One fresh subprocess / one BacktestNode per cell (L-31; scheduler contract) | `run_matrix.py:271-381`; `run_experiment.py:408-428`; command inspection | **MATCHES** | Serial loop invokes the one-cell CLI once per cell; process-local guard refuses a second node. No concurrency path exists. |
| Future-destroy control enabled for every scheduled cell (EXP-100 §Controls/Tripwire) | `run_matrix.py:185-226`; `run_experiment.py:476-507`; `control.py:100-141,163-269` | **MATCHES** | Command always includes `--destroy-control`; zero-fixed-point cyclic derangement and non-vacuity fail closed. Real safety metadata: 9 eligible/changed rows, 0 fixed points. |
| Venue-specific TRAIN-only bounds (apparatus §Venue pins; OOS rule) | `run_experiment.py:68-97,394-401`; `run_matrix.py:93-105,124-131` | **MATCHES** | Full cells use the exact manifest TRAIN bounds: Bybit `2021-06-29T06:53Z..2023-12-18T00:00Z`; cTrader `2021-06-02T00:01Z..2023-11-22T00:00Z`; one-cell runner rechecks `band="TRAIN"`. |
| Fail-closed resume, disk, timeout, staging, child, and integrity behavior (apparatus §Scheduler contract) | `run_matrix.py:153-182,257-381`; matrix runner tests | **MATCHES** | Skip requires final emission plus `blocking_pass is True`; stale/orphan/invalid states refuse; journal appends with flush+fsync; low disk, timeout, child/gate failure stop without deletion. |
| No methodology, cost, TEST, holdout, schema, or estimand change (apparatus §Explicit exclusions) | diff from `46116ff`; runner command/config; no-local-accounting and denylist scans | **MATCHES** | Dirty research-code change is only the operator-approved source-gap validation/reset behavior. Zero-cost remains pinned, control/object lifetimes and emissions unchanged, and no TEST/holdout route was added. |

### Golden-trace diff

| Event | Design expectation | Apparatus implementation/evidence | Verdict |
|---|---|---|---|
| **T1** | Strict source-minute excursion; later inclusive return; max excursion 1.20; prior count 0 | Raid lifecycle code is unchanged by this apparatus; source gaps change only admission/reset of missing-market periods. Existing focused golden-trace tests pass. | **PASS** |
| **T2** | Most-recent resolvable attribution while retaining both objects | Attribution, identities, and object lifetimes are untouched in the reviewed diff; full focused suite passes. | **PASS** |
| **T3** | Confirmation/profile at completed reference close; later opposing close ends swing/profile | Reference/terminal logic is untouched; closure gaps cannot manufacture confirmations or TPO counts. Real cTrader profile conservation passes. | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context / append-only QA | PASS | dedicated subagent; prior runs 1–7 retained unchanged; only run 8 appended |
| Venue hashes and attestation paths | PASS | direct `sha256sum` of both repository manifests; real cTrader attestation and fresh gate resolve INFR-021 |
| Exact matrix / preflight / process boundary | PASS | independent expansion and command inspection; 936 unique cells; one subprocess command per loop iteration |
| Real cTrader safety emission | PASS | pointer `/tmp/exp100-ctrader-safety-latest` → `.../three-day`; fresh `/tmp/exp100-ctrader-safety-run8-validation.json` has `blocking_pass=true`, correct expected/emitted `EURUSD`, pinned hash, schema, fence, reconciliation, and no-cost checks |
| Closure semantics | PASS | raw safety catalog: 1,545 aligned/increasing observed minutes and 13 absent minutes; emitted observations contain only complete `source_bars=15`; no synthetic rows; defined TPO rows conserve counts |
| Focused tests | PASS | 88 passed, 1 skipped in 11.31 s |
| Full Python suite | PASS | 315 passed, 5 skipped in 12.41 s; one existing NumPy runtime warning |
| Static check | PASS | Ruff clean on `src/xen/exp100`, fence, EXP-100 code, focused tests, and estimand validation test |
| No local accounting | PASS | `check_no_local_accounting("experiments/EXP-100/code")` returned `ok=true` |
| Zero-cost / no power machinery | PASS | no live cost-stack imports, charged-cost path, MDE/power floor, or machine value verdict in reviewed apparatus |
| Operator execution gate | PRESERVED | QA did not launch the preflight or full matrix; execution remains an operator decision |

### Issues

1. **INFO — safety smoke starts after the requested Saturday bound because cTrader was closed.** The requested window is `2023-11-18T00:00Z..2023-11-20T23:59Z`; the first observed EURUSD minute is Sunday `2023-11-19T22:02Z`. This is the approved no-synthetic-bars closure behavior, not missing manufactured data.

No blocking REVISE/REJECT findings. The execution apparatus is ready for the operator's 30-day Bybit preflight gate; QA does not launch it or the full matrix.

## QA run 9 — 2026-08-12T19:11:08Z — mode: subagent — HEAD 3eb18d8683e7b5555331c88870db05d6334eea75

Reviewed dirty/untracked (`git status --short`):
```
 M docs/experiments-docs/INDEX.md
 M docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/design.md
 M docs/experiments-docs/checkpoints/2026-08-11-019-liquidity-sweeps/liquidity.md
 M docs/signal-registry/README.md
 M docs/signal-registry/candidate-families/cf-liqswp-001-universe.json
 M docs/signal-registry/candidate-families/cf-liqswp-001.md
 M docs/signal-registry/multiplicity-registry.md
 M docs/superpowers/plans/2026-08-12-exp-100-progress-handoff.md
 M docs/superpowers/specs/2026-08-11-liquidity-sweeps-design.md
 M python/experiments/EXP-100/code/run_matrix.py
 M python/experiments/EXP-100/design.md
 M python/experiments/EXP-101/design.md
 M python/experiments/EXP-102/design.md
 M python/experiments/EXP-103/design.md
 M python/experiments/EXP-104/design.md
 M python/experiments/INDEX.md
 M python/src/xen/exp100/config.py
 M python/src/xen/exp100/processor.py
 M python/src/xen/exp100/state_store.py
 M python/src/xen/exp100/tpo.py
 M python/tests/test_exp100_matrix_runner.py
 M python/tests/test_exp100_processor.py
 M python/tests/test_exp100_state_store.py
 M python/tests/test_exp100_tpo.py
?? .pi/
?? docs/superpowers/specs/2026-08-12-exp-100-late-window-active-raid-optimization-design.md
?? python/experiments/EXP-100/analysis_code/
?? python/experiments/EXP-100/results/close_all_eligible_probe_3d.json
?? python/experiments/EXP-100/results/close_all_eligible_probe_7d.json
?? python/experiments/EXP-100/results/fullstack_and_close_all_investigation.md
```

Object judged: AMENDMENT-8 observation-bar raid grain (QA runs 4–8 are stale; they judged the later 1m raid path). Fresh-context subagent; reviewer did not implement EXP-100. No preflight, matrix, BacktestNode, TEST, or holdout launched. AMENDMENT-6/7/8 methodology not reopened.

Verdict: **APPROVE**

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Raid start / return / beyond / same-bar ambiguity on completed observation bar; 1m wick that is not the observation OHLC is not a raid (EXP-100 scope; golden T1; checkpoint §5.2/§6; AMENDMENT-8) | `processor.py:1-8,97-125,154-164,257-319` | **MATCHES** | `_update_active_raids_from_source` does not create raids. `_process_observation_raid_state` runs only after `StreamingOHLC` completes. Same-observation beyond+return → `AMBIGUOUS_INTRABAR`. |
| Engine input = 1m; TPO bins, max-excursion reset, post-confirm swing = 1m (AMENDMENT-3/8; checkpoint §5.2/§8) | `processor.py:109-110,154-186,203-252,396-427`; `tpo.py:1-8,88-108,147-182,247-281`; `strategy.py:386-401` | **MATCHES** | 1m updates bins / `max_price` / `swing_extreme`. New raid seeds TPO from first 1m beyond through observation close. |
| Confirmation + later endpoint = 1H (15m/30m) or 1D (1h) (AMENDMENT-2; checkpoint §7) | `config.py:75-80`; `processor.py:50-52,429-504`; `run_matrix.py:73` | **MATCHES** | Reference aggregator is 60m or 1440m. Matrix and `validate()` pin the pairing. |
| AMENDMENT-6 close-all-eligible: latest expected-side stays primary; earlier eligible returned → `CONFIRMED_NON_PRIMARY`; opposing unconfirmed → `FAILED_BREAKOUT`; primary completes on later opposing (checkpoint §6–§7; golden T2) | `processor.py:429-504` | **MATCHES** | Eligible rows sorted by `(sweep_ts_ns, raid_id)`; latest expected-side kept live; others settled on the same reference close. |
| AMENDMENT-7 cTrader-only 216 cells: EURUSD, XAUUSD, USTEC × 3 TF × 2 methods × 12 configs (EXP-100 scope; registry universe pin) | `run_matrix.py:20-98`; `test_exp100_matrix_runner.py:20-32`; `cf-liqswp-001-universe.json` | **MATCHES** | Full grid is 216 unique CTRADER cells; 0 BYBIT. Preflight is EURUSD 15m BREAKOUT_BAR PREVIOUS_1H, 2023-10-23..2023-11-21T23:59Z. |
| Family A/B/C catalogue incl. 1W; IANA/DST sessions; rolling 16..256 (checkpoint §5.2) | `config.py:21-32`; `levels.py:21-40,99-222`; `processor.py:111-124,655-687` | **MATCHES** | Auto catalogue + `SUPERSEDED_NO_RAID` for unraided same-side. |
| Causal ATR(14) / regime on completed observation bars; raid uses ATR available before that bar updates (checkpoint §5.3) | `features.py:91-174`; `processor.py:113-118,257-261,321-341` | **MATCHES** | Raid path reads `_atr.value` before `_on_observation_bar`. |
| Online TPO: 1m bins, `0.10×ATR`, VA≥70%, gap≥30% VA mass, `tight_gap = gap_span < 0.30×VA_width`; reset on new max; no historical replay (checkpoint §8) | `tpo.py:88-108,147-245,283-370`; `processor.py:203-252`; `state_store.py:357-376` | **MATCHES** | Reset starts a new generation. Finalize rematerializes only when `bracket_count==0`; production path increments online after start/seed. |
| Outcomes: raw/bps/ATR distances; `strong_move = swing_atr > max_excursion_atr`; `gap_span_atr` / `gap_span_va` (checkpoint §9/§11) | `processor.py:506-591`; `strategy.py:164-247`; `tpo.py:219-245` | **MATCHES** | Required raid/profile columns are in the emission schemas. |
| Future-destroy derangement, zero fixed points, non-vacuity on swing/duration/strong_move (EXP-100 control/tripwire; checkpoint §10) | `control.py:100-141,163-269`; `run_experiment.py:426-454`; `run_matrix.py:185-226` | **MATCHES** | Cyclic derangement; rejects fixed points / singletons. Matrix always passes `--destroy-control`. |
| One BacktestNode per process; TRAIN-only fence; zero-cost; no strategy fills objective (L-31; EXP-100 HARD) | `run_experiment.py:48-52,199,349-377,409-421`; `run_matrix.py:271-381` | **MATCHES** | Process guard; `assert_within_fence(..., band="TRAIN")`; `cost_model: NO_COST_CHARGED`; empty fills/orders/positions. |
| cTrader closure: minute-aligned strictly increasing observed bars; no synthetic bars/TPO; reset incomplete window (EXP-100 scope) | `processor.py:704-717`; `features.py:30-56` | **MATCHES** | Duplicate/backward timestamps rejected; gap resets `StreamingOHLC`. |
| Amendment ledger 0L / 3T / 4N (checkpoint §2; EXP-100 header) | EXP-100 `design.md:6-8`; checkpoint `design.md` AMENDMENT-2..8 | **MATCHES** | AMENDMENT-8 declared NEUTRAL. Consecutive tighter streak is 2 (A6–A7), not ≥3. |

### Golden-trace diff

Expected values from **current design text** (EXP-100 `design.md:86-96`; checkpoint §13), not from running the impl.

| Event | Expected (design) | Implemented logic | Verdict |
|---|---|---|---|
| **T1** | Active high 100.00; a **completed observation bar** high=101.20 starts one raid, max excursion 1.20, not returned; a **later observation bar** low=100.00 completes the raid, `prior_raid_count=0`. A 1m wick that is not the observation high does not start a raid. | Raid create/return/ambiguity only in `_process_observation_raid_state` on completed observation OHLC (`processor.py:113-118,257-319`). Initial `max_excursion` is observation high−price (`processor.py:349-356`). 1m path cannot `_new_raid`. Intra-observation beyond+return → `AMBIGUOUS_INTRABAR`, not a live completed raid. Incomplete windows never emit an observation, so a lone 1m wick cannot start a raid. | **PASS** |
| **T2** | Second high level raided on a later observation bar before confirm; latest eligible returned raid is primary and stays live; earlier eligible returned raid settles `CONFIRMED_NON_PRIMARY` on the same expected-side reference (AMENDMENT-6). | `_eligible_active_raids` + latest `(sweep_ts_ns, raid_id)` kept live with `primary_attribution=true`; earlier rows `_terminal_raid(..., "CONFIRMED_NON_PRIMARY")` (`processor.py:457-479`). Covered by `test_processor_confirms_all_eligible_raids_and_keeps_only_latest_primary`. | **PASS** |
| **T3** | 1H expected-side close timestamps confirmation at that completed close, not a 15m/1m stamp; 1m TPO ends there; later opposing reference closes the swing. | `confirmation_ts_ns = bar.ts_event_ns` of completed reference (`processor.py:463-479`). Profile finalize at that close for primary; opposing later → `COMPLETED` (`processor.py:481-504,593-627`). | **PASS** |

Note: `test_raid_start_and_return_use_source_one_minute_bars` uses default `observation_minutes=1`, so that test is a 1m-observation cell, not the production 15m T1. Hand-trace of the production observation path still matches T1.

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context / append-only | PASS | mode `subagent`; runs 1–8 left intact; this is run 9 only |
| Mandatory design blocks | PASS | mechanism, object-identity, control, tripwire, bands, sample-size, golden, hard/informative, ZERO-COST in EXP-100 `design.md` |
| Zero-cost verbatim + no live cost path | PASS | EXP-100 `design.md:107-119` matches design-requirements §10; runner metadata `NO_COST_CHARGED`; no `spread_scale_route` / `bybit_round_trip` / `PARTIAL_FEES` / `charge_costs` in `xen.exp100` or `EXP-100/code` |
| No local accounting | PASS (static) | `BANNED_LOCAL_DEFS` (`assemble_realized_bps`, `assemble_multileg_bps`, `per_leg_net`, `build_episodes`) are absent from `python/experiments/EXP-100/code/*.py`. Module import of `check_no_local_accounting` was not executable in this reviewer environment. |
| No Python strategy backtest | PASS | Nautilus `BacktestNode` only; `run_analysis=False` |
| Registry | PASS | `CF-LIQSWP-001` REGISTERED; planned counted TEST/holdout reads = 0; universe pin is EURUSD/XAUUSD/USTEC TRAIN |
| No research powering | PASS | no MDE / `MDE_Z` / detection floors / `UNPOWERED` / `min_powered_seeds` / `n_legs_floor` in EXP-100 design or `xen.exp100` |
| PSR pairing | N/A | apparatus estimand is coverage/reconciliation, not mean-trade/leg bps |
| Amendment ledger | PASS | 0 looser / 3 tighter / 4 neutral; AMENDMENT-8 NEUTRAL; no consecutive one-direction streak ≥3 |
| Derangement destroy | PASS | `destroy form: DERANGEMENT` in design; code builds a cycle and raises on fixed points |
| One BacktestNode / process | PASS | process-local guard + one subprocess command per matrix cell |
| Holdout fence | PASS | TRAIN-only pin + `assert_within_fence(..., band="TRAIN")`; no TEST/holdout loader |
| Screen conversion pin | N/A | no SPDR/money conversion |
| XENA frozen registry | N/A | not a XENA run |
| No execution | PASS | review only |

### Issues

1. **INFO — one-cell CLI still accepts Bybit.** `run_experiment.py:57-83,486` and `config.py:7` still pin/validate `BYBIT`. The **scheduled** object is cTrader-only 216 (`run_matrix.py:20-98`). Not a matrix deviation.
2. **INFO — LEVEL_CLOSE ≡ BREAKOUT_BAR numerically.** Both use previous completed reference high/low (`processor.py:629-653`). Separate strata remain; overlap is disclosed in checkpoint §7. Methodology not reopened.
3. **INFO — no focused 15m golden-T1 test.** Production path is observation-bar; the named T1 unit test is a 1m-observation cell (`test_exp100_processor.py:61-66,727-744`). Hand-trace still PASSes. Optional follow-up, not blocking.
4. **INFO — live state is in-memory** (`state_store.py:1-8,64-79`) with an append-only 1m high/low log for deferred TPO (`tpo.py:26-54`). Semantics match the prior store; not a design-fidelity break.

No blocking REVISE/REJECT issues. Ready for the operator's execution gate; QA does not launch it.

## QA run 10 — 2026-08-13T18:54:22Z — mode: subagent — HEAD 3eb18d8683e7b5555331c88870db05d6334eea75

Reviewed dirty-file list: see `git status --short` snapshot supplied by supervisor; `python/experiments/EXP-100/qa-review.md` was already modified. This independent review supersedes the stale AMENDMENT-8-era run 9 scope. No Nautilus, preflight, matrix, TEST, or holdout reads were launched.

Verdict: REVISE

### Design-fidelity trace

| Design clause | Code/artifact | Verdict | Notes |
|---|---|---|---|
| cTrader TRAIN universe: EURUSD, XAUUSD, USTEC; 264 cells; 66 15m, 66 30m, 132 1h | `python/experiments/EXP-100/code/run_matrix.py:16-148`; `results/analysis/scan_summary.json` | MATCHES | Family gate reports 264 cells with exact 66/66/132 split and no zero-level or zero-raid cells. |
| AMENDMENT-6 close-all settlement | `python/src/xen/exp100/processor.py:429-504`; `design.md:48-53,109-113`; `analysis.md:Q19` | MATCHES | Latest eligible expected-side raid remains primary; earlier eligible raids become `CONFIRMED_NON_PRIMARY`; opposing eligible raids become `FAILED_BREAKOUT`. |
| AMENDMENT-8 observation-bar grain; 1m reserved for TPO, excursion reset, swing path | `processor.py:257-319`; `design.md:47-48,106-108`; `analysis.md:Q18` | MATCHES | Raid creation/return uses completed observation OHLC; 1m source bars update profile/swing state and cannot independently create raids. |
| AMENDMENT-9 references: 15m/30m → 1H; 1h → 1H and 4H | `config.py:65-85`; `run_matrix.py:91-148`; scan summary grid check | MATCHES | No 1D confirmation cells; 1h has both reference strata. |
| AMENDMENT-10 NY trading clocks for 1D/1W | `levels.py:191-278`; `config.py:21-29`; `analysis.md:Q20` | MATCHES | America/New_York 17:00 trading day and Monday–Friday week logic; no weekend anchor keys. |
| AMENDMENT-11 rolling 7/14/22/252 and 264-cell matrix | `levels.py:35-40`; `run_matrix.py:21-35`; scan summary | MATCHES | All four rolling configurations are present; observed configuration set exactly matches expected. |
| AMENDMENT-12 50% tightness and 30% gap selection | `config.py:45-47,93-99`; `tpo.py:218-245,385-416`; `strategy.py:218-245`; scan summary | MATCHES | `tight_gap` uses 0.50 VA width and gap mass uses 0.30; `tight_rule_mismatch=0`. |
| AMENDMENT-13 same-bar return lifetime | `processor.py:257-319`; `design.md:48,105-107`; `analysis.md:Q17` | MATCHES | Same-bar beyond plus return records `return_ts_ns` while leaving the raid active; emission reports 7,669,654 same-bar returns and zero ambiguous rows. |
| Causal ATR/regime and 1m TPO/profile path | `features.py:91-174`; `processor.py:109-215,321-427`; `tpo.py:88-245` | MATCHES | ATR is read before observation update; TPO bin width is frozen at 0.10×ATR and source bars update profile/swing state. |
| Required raid/profile emissions, including raw/bps/ATR distances and gap ratios | `strategy.py:164-247`; `processor.py:506-579`; `tpo.py:218-245` | DEVIATES | Most fields are present, but excursion duration is absent; `duration_ns` is only endpoint minus confirmation and is not an excursion-duration field. |
| Online streaming profile with no historical replay | `tpo.py:1-8,26-54,156-178,247-281`; `processor.py:109-110,169-215` | DEVIATES | Every source minute is retained in unbounded `SourceMinuteLog` lists. This violates the design’s bounded online/no-replay boundary even though normal paths also increment profile bins online. |
| Future-destroy derangement and non-vacuity | `control.py:100-269`; `run_experiment.py:426-454`; per-cell metadata | MATCHES | Full emission reports 264/264 changed controls and zero fixed points. |
| TRAIN fence, no holdout, one BacktestNode per process, zero cost | `run_experiment.py:349-377,408-421`; `run_matrix.py:271-381`; per-cell gates | MATCHES | All 264 per-cell gates and family gate have `blocking_pass=true`; pinned cTrader fence and `NO_COST_CHARGED` are present. |

### Golden-trace diff

| Event | Expected from current design | Implemented/emitted behavior | Verdict |
|---|---|---|---|
| T1 | Observation bar strictly beyonds high level; later observation return records on same raid; same-bar return leaves raid live; non-surviving 1m wick does not create raid | Observation path creates the raid and records return without terminal settlement; source 1m path cannot create raids. | PASS |
| T2 | Latest eligible expected-side raid is primary; earlier eligible raid settles `CONFIRMED_NON_PRIMARY`; opposing eligible raid fails | `_on_reference_bar` sorts eligible rows by sweep time/raid ID, retains only latest primary, and terminally settles the others. | PASS |
| T3 | Confirmation occurs at completed 1H/4H close; profile ends at that close; later opposing reference ends primary swing | `confirmation_ts_ns` and profile endpoint use completed reference timestamp; later opposing event emits `COMPLETED`. | PASS |

### Governance & boundary

- Fresh independent `subagent` review; prior QA sections were not rewritten.
- Current final object is AMENDMENT-13, not the stale AMENDMENT-8-era 216-cell object.
- Family gate: `python/experiments/EXP-100/results/estimand_validation.json` reports `blocking_pass=true`, `n_cells=264`.
- Per-cell artifacts: `python/experiments/EXP-100/results/execution/full/` contains 264 gate files; scan summary reports 264/264 passing.
- Registry family is registered; counted TEST reads are 0; no TEST or holdout reads were performed in this review.
- Holdout and TRAIN boundary checks report no holdout timestamps; only endpoint/censor timestamps reach the TRAIN boundary.
- Zero-cost disclosure is present in `design.md`; per-cell gates report `NO_COST_CHARGED` and zero non-zero cost columns.
- Future-destroy uses a zero-fixed-point derangement; all 264 cells changed non-vacuously.
- No MDE, power floor, detection floor, or machine-assigned value verdict was found in the reviewed EXP-100 design/code.
- PSR is not applicable because the apparatus has no trade/leg ledger or mean-trade read.
- No XENA run, SPDR conversion pin, or cost directive applies.
- No tests or execution commands were run; the task explicitly prohibited launches and reads outside existing artifacts.

### Issues

1. **REVISE — high — required excursion-duration emission is missing.**
   - Design: `python/experiments/EXP-100/design.md:11` required-emissions clause and checkpoint `design.md:11`.
   - Code: `python/src/xen/exp100/strategy.py:164-214` defines no excursion-duration column; `python/src/xen/exp100/processor.py:557-579` computes only `duration_ns = endpoint_ts_ns - confirmation_ts_ns`.
   - Required change: emit an explicit excursion duration from first excursion through return/settlement (with the contract’s required duration representation), and retain the specified swing/reversal duration separately or explicitly map it to a named contract field.
   - `FAILING_ARTIFACT`: `python/src/xen/exp100/processor.py`, `python/src/xen/exp100/strategy.py`.
   - `REQUIRED_SKILL`: experiment-developer.

2. **REVISE — high — unbounded source-minute history violates the online streaming boundary.**
   - Design: `python/experiments/EXP-100/design.md:8,44,96-98`; checkpoint `design.md:160-164,237-261` requires online state and says historical bars are never retrospectively replayed.
   - Code: `python/src/xen/exp100/tpo.py:1-8,26-54` stores every source minute in unbounded `SourceMinuteLog` lists; `tpo.py:156-178,247-281` retains a deferred materialization path over that log.
   - Required change: remove unbounded full-history retention from the live path and maintain only bounded online profile state, or submit an operator-approved design amendment explicitly changing the streaming/memory contract. Do not silently retain an entire TRAIN source history per cell.
   - `FAILING_ARTIFACT`: `python/src/xen/exp100/tpo.py` and the corresponding processor wiring at `processor.py:60-68,109-110`.
   - `REQUIRED_SKILL`: experiment-developer; quant-designer if the design is intentionally changed.

No REJECT finding: no holdout contact, surviving future-destroy control, or unapproved causal timestamp breach was established. Execution remains prohibited until both REVISE issues are resolved and a fresh QA run is completed.

## QA run 11 — 2026-08-13T20:47:00Z — mode: subagent — HEAD 477287b81d93b2830e10aaa1384bf469a8908983

Reviewed dirty state: modified `python/experiments/EXP-100/{code/run_experiment.py,design.md,qa-review.md}`, `python/src/xen/exp100/{config.py,control.py,levels.py,processor.py,state_store.py,strategy.py,tpo.py}`, and `python/tests/{test_exp100_processor.py,test_exp100_runner.py,test_exp100_tpo.py}`; untracked `docs/superpowers/plans/2026-08-13-exp-100-implementation-handoff.md`. Fresh-context subagent; reviewer did not implement this tree. No Nautilus, preflight, matrix, TEST, holdout, or new-result read was launched.

Verdict: **REVISE**

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| cTrader TRAIN scope: EURUSD/XAUUSD/USTEC; 15m/30m→1H, 1h→1H+4H; 264 cells (EXP-100 Scope; checkpoint §5/§7) | `config.py:7-99`; `levels.py:21-278`; `run_matrix.py:21-148` | **MATCHES** | Current config carries rolling 7/14/22/252, NY-17 trading clocks, and the declared confirmation references. |
| Observation-bar raid grain and AMENDMENT-13 same-bar lifetime (EXP-100 Scope/Golden T1; checkpoint §5.2/§6) | `processor.py:95-130,236-280,305-411` | **MATCHES** | Source minutes cannot create/return a raid. Completed observation OHLC creates the raid; same-bar return is recorded without terminal settlement. The bounded current observation deque locates/seeds the first causal 1m excursion. |
| AMENDMENT-6 close-all-eligible settlement (EXP-100 Scope/Golden T2; checkpoint §7) | `processor.py:413-485` | **MATCHES** | Expected-side candidates are sorted and only the latest remains primary; earlier and opposing candidates settle under their distinct states. |
| Reference confirmation and swing endpoint chronology (EXP-100 Golden T3; checkpoint §7) | `processor.py:55-57,413-485` | **MATCHES** | Reference aggregation is 1H/4H; confirmation and later opposing endpoint use completed reference timestamps. |
| Explicit excursion vs swing duration fields (EXP-100:15,58; checkpoint §6/§9/§11) | `processor.py:524-556`; `strategy.py:164-217` | **MATCHES** | `excursion_duration_ns = return-or-censor − first_excursion`; `swing_duration_ns = endpoint − confirmation`; `duration_ns` is the exact swing alias. Both new fields cross the Parquet schema. |
| Bounded online profile; no full-history source log or deferred replay (EXP-100:14,58; checkpoint §8) | `processor.py:38-70,174-234,305-341`; `tpo.py:1-105,209-296`; `state_store.py:64-88,417-548` | **MATCHES** | No `SourceMinuteLog` remains. Each 1m bar directly increments sparse SQLite bins; reset replaces the current generation; finalization uses cursor passes over current profile state. Only the bounded observation deque is replayed once to seed a newly known observation-bar raid. |
| Future-destroy is a zero-fixed-point derangement over the declared population (EXP-100 Controls/Tripwire; checkpoint §10; L-28) | `control.py:100-148,228-276`; `run_experiment.py:476-516` | **DEVIATES** | Groups of size ≥2 are deranged. Singleton eligible groups are skipped, copied unchanged, omitted from `rows`, and still permit a published artifact reporting `fixed_points=0`; this is not a derangement of the declared same-emitted-object population. |
| TRAIN fence, one BacktestNode/process, zero-cost, no strategy fills (EXP-100 HARD; L-31) | `run_experiment.py:48-52,349-421`; `run_matrix.py:271-381` | **MATCHES** | Static path remains TRAIN-pinned and cost-free; no Python strategy backtest exists. No engine was launched in this review. |
| Amendment direction ledger for the next execution object (EXP-100:7-16; design requirements §12) | EXP-100 `design.md:5-16`; checkpoint `design.md:22-108`; registry `cf-liqswp-001.md:1-146` | **MISSING** | `AMENDMENT-14 IMPLEMENTATION` is named without LOOSER/TIGHTER/NEUTRAL, running count, final false-qualifier re-derivation, or checkpoint/registry approval record. |

### Golden-trace diff

Expected behavior comes from current EXP-100 `design.md:103-121` and checkpoint §13, not implementation output.

| Event | Expected | Implemented logic | Verdict |
|---|---|---|---|
| T1 | Completed observation bar starts raid; later/same-bar inclusive return is recorded; non-surviving 1m wick is not a raid | `_process_observation_raid_state` is called only for completed observations; `_new_raid` uses bounded source window for first-excursion/profile seed; source path only updates profile/swing | **PASS** |
| T2 | Latest eligible expected-side raid remains primary; earlier eligible returned raid settles `CONFIRMED_NON_PRIMARY`; opposing eligible raid fails | `_on_reference_bar` separates expected/opposing populations, sorts deterministically, and terminally settles all non-primary candidates | **PASS** |
| T3 | Completed 1H/4H close timestamps confirmation; later opposing close ends swing and profile | reference aggregator is selected from `confirmation_reference`; confirmation/profile finalization and endpoint use the reference event timestamp | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context / append-only | PASS | mode `subagent`; exact missing run 10 section restored first; runs 1–10 otherwise unchanged |
| Run-10 duration blocker | PASS | distinct tested fields in processor + Parquet schema |
| Run-10 online-profile blocker | PASS | source-history log/rebuild removed; online SQLite profile updates only |
| Focused EXP-100 tests | PASS | 87 non-execution tests passed in 5.90s, including all control/features/levels/matrix/processor/state-store/TPO tests and runner config/schema pins |
| Runner engine tests | NOT RUN | three runner tests launch `run_experiment.py`/Nautilus and were excluded by the explicit no-launch instruction |
| Ruff | PASS | `ruff check` clean on `src/xen/exp100`, EXP-100 code, and all EXP-100 tests |
| No local accounting | PASS | `check_no_local_accounting("experiments/EXP-100/code")` → `ok=true`, no banned definitions |
| No TEST/holdout | PASS (static) | no TEST/holdout loader in EXP-100 code; no data was inspected |
| Zero cost | PASS | canonical disclosure present; no live cost symbol found in design/code |
| No research powering | PASS | no MDE/power-floor/UNPOWERED machinery in EXP-100 design/code |
| Registry | PASS for AMENDMENT-13; REVISE for next object | family remains REGISTERED; AMENDMENT-13 is COMPLETE with 0 counted TEST reads; named AMENDMENT-14 is not registered |
| Derangement | REVISE | singleton eligible groups are silently outside the mapping and unchanged in the published destroy artifact |
| PSR / XENA / SPDR conversion | N/A | no trade/leg mean read, XENA route, or SPDR money conversion |
| No execution | PASS | no Nautilus, preflight, matrix, result-data, TEST, or holdout command run |

### Issues

1. **REVISE — high — singleton control groups violate the declared derangement population and can publish a misleading zero-fixed-point attestation.**
   - Design: EXP-100 `design.md:68-77` says the same emitted raid objects are deranged within the declared groups, with zero fixed points; checkpoint `design.md:282-295` binds a derangement destroy.
   - Code: `control.py:107-115` skips singleton groups; `control.py:248-265` copies those eligible rows unchanged; `run_experiment.py:489-516` publishes `VACUOUS_SINGLETON` metadata instead of failing the integrity control.
   - Required change: fail closed when any eligible singleton group exists, or predeclare and operator-approve a different grouping/population that can be fully deranged. Do not publish unchanged eligible rows under a zero-fixed-point control claim.
   - `FAILING_ARTIFACT`: `python/src/xen/exp100/control.py`, `python/experiments/EXP-100/code/run_experiment.py`.
   - `REQUIRED_SKILL`: experiment-developer; quant-designer if grouping/population changes.

2. **REVISE — high — the next execution object is not governed as an amendment.**
   - Design: EXP-100 `design.md:16` names `AMENDMENT-14 IMPLEMENTATION`, while `design.md:5-7` and checkpoint/registry still end at AMENDMENT-13 with `2L / 3T / 7N`.
   - Governance: design requirements §12 require direction, running count, and re-derived false-qualifier expectation for every pre-measurement amendment; the checkpoint/registry contains no AMENDMENT-14 operator record.
   - Required change: either record operator approval and fully register AMENDMENT-14 (direction, count, final-null false-qualifier expectation, checkpoint/registry synchronization), or remove the amendment label and clearly classify this as a non-methodological implementation correction under the existing approved design. The current text cannot authorize a new execution.
   - `FAILING_ARTIFACT`: `python/experiments/EXP-100/design.md` plus checkpoint/registry if it is truly an amendment.
   - `REQUIRED_SKILL`: quant-designer.

No REJECT finding: no holdout contact, executed invalid emission, or established causal timestamp breach occurred in this review. Execution remains blocked until both issues are resolved and fresh QA approves the exact tree.

## QA run 12 — 2026-08-13T20:55:22Z — mode: subagent — HEAD 477287b81d93b2830e10aaa1384bf469a8908983

Reviewed dirty state: modified `python/experiments/EXP-100/{code/run_experiment.py,design.md,qa-review.md}`, `python/src/xen/exp100/{config.py,levels.py,processor.py,state_store.py,strategy.py,tpo.py}`, and `python/tests/{test_exp100_control.py,test_exp100_processor.py,test_exp100_runner.py,test_exp100_tpo.py}`; untracked `docs/superpowers/plans/2026-08-13-exp-100-implementation-handoff.md`. Fresh-context subagent; reviewer did not implement the tree. Run-12 scope was the run-11 remediation plus retained run-10 fixes. No Nautilus, preflight, matrix, TEST, holdout, or new-result analysis was launched.

Verdict: **APPROVE**

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Explicit excursion and swing duration clocks (EXP-100:15,58; checkpoint §6/§9/§11) | `processor.py:524-556`; `strategy.py:164-217` | **MATCHES** | `excursion_duration_ns` ends at return/censor; `swing_duration_ns` ends at endpoint; `duration_ns` remains the exact swing alias for frozen downstream readers. |
| Bounded online profile, no source-history replay (EXP-100:14,58; checkpoint §8) | `processor.py:38-70,174-234,305-341`; `tpo.py:1-105,209-296`; `state_store.py:64-88,417-548` | **MATCHES** | Every source minute updates sparse current-generation bins directly; no full-history source log/deferred rebuild exists. The only seed replay is the bounded current observation window. |
| Future-destroy is a derangement with zero fixed points over every eligible declared group (EXP-100 Controls/Tripwire; checkpoint §10; L-28) | `control.py:100-141,221-269`; `run_experiment.py:476-512`; `test_exp100_control.py:148-175` | **MATCHES** | A singleton eligible group raises before the destination writer is created. The test proves the exception and absence of a destination artifact. Groups of size ≥2 retain cyclic zero-fixed-point mapping. |
| No `VACUOUS_SINGLETON` publication path (EXP-100 Controls/Tripwire) | `run_experiment.py:489-512`; `control.py:106-112` | **MATCHES** | Runner metadata has only `VACUOUS_NO_ELIGIBLE` for a genuinely empty eligible population. Singleton eligibility cannot return a control report, reach metadata writing, or publish the staged run. |
| Existing amendment ledger and frozen-emission separation (EXP-100:5-16; design requirements §12) | EXP-100 `design.md:5-16,42-58`; checkpoint `design.md:22-108`; registry `cf-liqswp-001.md:142-149` | **MATCHES** | Text now calls the work a `POST-QA IMPLEMENTATION CORRECTION` conforming to AMENDMENT-2–13, explicitly preserves the `2L / 3T / 7N` ledger, and forbids relabeling the frozen 264-cell AMENDMENT-13 emission. No AMENDMENT-14 is claimed. |
| Observation-bar raid grain, AMENDMENT-13 lifetime, close-all settlement, and reference chronology (EXP-100 Scope/Golden T1–T3) | `processor.py:95-130,236-485` | **MATCHES** | Run-11 hand trace remains valid; remediation did not touch event identity or chronology. |
| TRAIN fence, one BacktestNode/process, zero cost, no strategy fills (EXP-100 HARD; L-31) | `run_experiment.py:48-52,349-421`; `run_matrix.py:271-381` | **MATCHES** | Static boundary unchanged. No engine was launched. |

### Golden-trace diff

Expected behavior remains current EXP-100 `design.md:104-121` and checkpoint §13.

| Event | Expected vs implementation | Verdict |
|---|---|---|
| T1 | Completed observation OHLC starts the raid; same/later observation return is recorded without closing it; a non-surviving 1m wick cannot create a raid. Run-11 trace unchanged. | **PASS** |
| T2 | Latest eligible expected-side raid remains primary; earlier expected and opposing candidates settle under their declared states. Run-11 trace unchanged. | **PASS** |
| T3 | Completed 1H/4H reference timestamps confirmation; later opposing reference closes swing/profile. Run-11 trace unchanged. | **PASS** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Fresh context / append-only | PASS | mode `subagent`; runs 1–11 unchanged; run 12 appended only |
| Run-11 singleton block | PASS | fail-closed implementation + focused regression; no destination artifact |
| Run-11 amendment block | PASS | correction is explicitly non-methodological under AMENDMENT-2–13; frozen emission remains separate |
| Non-execution EXP-100 tests | PASS | 87 tests passed in 4.48s: control/features/levels/matrix/processor/state-store/TPO plus runner config/schema pins |
| Nautilus runner tests | NOT RUN | tests that execute `run_experiment.py` were excluded by the no-launch instruction |
| Ruff | PASS | EXP-100 source, code, and test surface clean |
| No local accounting | PASS | `check_no_local_accounting("experiments/EXP-100/code")` → `ok=true`, no banned definitions |
| No TEST/holdout | PASS (static) | no TEST/holdout path introduced; no such run launched |
| Zero cost / no research powering | PASS | canonical disclosure retained; no live cost or research-power machinery introduced |
| Registry / amendment ledger | PASS | registered AMENDMENT-13 evidence remains frozen; implementation correction does not change the ledger or registry state |
| PSR / XENA / SPDR conversion | N/A | no mean trade/leg read, XENA route, or SPDR conversion |
| No execution | PASS | no Nautilus, preflight, matrix, TEST, or holdout command run |

### Issues

None. Run-11 blockers are resolved. This approval applies to the exact dirty implementation tree as a candidate for a future operator-authorized execution; it does not alter or revalidate the frozen AMENDMENT-13 emission and does not itself authorize execution.
