# EXP-100 late-window active-raid optimization design

**Date:** 2026-08-12  
**Status:** implemented; smoke-equivalent; fresh QA pending  
**Scope:** semantics-preserving late-window cost reduction on the active-raid /
active-level source-minute path

## Problem

The approved 30-day preflight timed out at 75.96% after two hours. Retained
`.work` state at stop:

| Live object | Count |
|---|---:|
| active levels | 388 |
| active raids | 9,557 |
| profile bins | 4,009,107 |

Raid lifecycle bucket at stop:

| State | Count |
|---|---:|
| returned, unconfirmed, live profile | 9,308 |
| in excursion, unconfirmed | 203 |
| confirmed, profile finalized | 46 |

Almost all open cost is **returned raids that never receive reference selection**.
Under the current apparatus only `_latest_active_raid` is confirmed or failed, so
earlier returned raids keep receiving every source-minute TPO update until
right-censor. That is the asymptotic driver. Pure storage opts cannot remove it;
they only reduce the per-raid / per-level tax.

## Late-window profile (pre-change)

Synthetic constant density: 5,000 returned open raids, 10 source minutes, levels
far from price so no new raids form.

| Path | Share |
|---|---|
| TPO bin `executemany` | ~37% |
| per-level JSON rewrite every minute | ~23% |
| per-raid `get_profile_state` | material |
| JSON decode of active levels + raids | material |
| wall | **424 ms/bar** (~9.7 h extrapolated at 9,557 constant density) |

## Semantics-preserving changes

1. **Bulk multi-raid TPO bin writes**  
   One source minute collects every live profile bin range, then issues two
   streaming bulk calls (bins + conservation). Membership, order of inclusive
   indexes, and conservation totals are unchanged; only the Python↔SQLite
   boundary shrinks from one pair of calls per raid to one pair per minute.

2. **Cached `profile_bin_width` on the raid row**  
   Bin width is frozen at profile start and reused for bar→bin mapping. No
   per-minute `get_profile_state` on the hot path when the cache is present.
   Missing cache still falls back to the durable profile_state row.

3. **Skip level JSON writes when `beyond` is unchanged**  
   `beyond` is the only online level field required every minute. Terminal level
   rows stamp `last_observation_ts_ns = endpoint_ts_ns` when the level existed
   before the endpoint bar; levels created on the final minute keep a null
   observation stamp. Matches the retained smoke (142 endpoint-equal rows, 2
   null final-minute rows).

4. **Scalar `count_active_levels`**  
   Operational telemetry uses `SELECT COUNT(*)` instead of decoding every active
   level payload (mirrors the approved active-raid count path).

5. **Bounded SQLite page cache**  
   `PRAGMA cache_size=-131072` (128 MiB). Live rows remain disk-backed and
   cursor-iterated; no Python materialization of active sets or bin histories.

## Explicit non-goals

- No change to raid lifetime, confirmation selection, attribution, TPO
  membership, fences, controls, or estimands.
- No in-memory bin maps for all open raids (rejected by the memory-safe design).
- No timeout raise and no full-matrix launch.
- No silent methodology fix for the 9,308 never-selected returned raids. That
  requires an operator-approved design amendment if desired.

## Output-equivalence contract

Exact equality required for:

- ordered `levels`, `raids`, `tpo_profiles`, `raids_destroyed`
- every `bar_marks` column except `state_bytes`
- event-log bytes
- destroy membership and fixed-seed values
- fence / cost / estimand attestations

`state_bytes` remains the approved operational exception.

## Verification

1. Focused + full `test_exp100_*` suite green.
2. Fresh three-day TRAIN smoke matches retained approved smoke exactly under the
   contract above (event-log SHA
   `24ce58a1e6df2b5ed4b6953dbf28c8552de0dc187ba4d8463a78b9065b10cbe7`).
3. Late-window synthetic and 1d/2d/3d wall timings recorded.
4. Fresh-context QA must approve before any preflight re-run.

## Measured effect (this machine)

| Slice | Prior cumulative wall | This change wall |
|---|---:|---:|
| late-window 5k raids | 424 ms/bar | **244 ms/bar** (~1.7×) |
| 1 day | 3.60 s | **3.43 s** |
| 2 day | 19.69 s | **12.78 s** |
| 3 day smoke | 55.41 s | **32.66 s** |

These gains reduce constant factors. They do **not** claim the full TRAIN matrix
is feasible while thousands of returned raids remain live with per-minute TPO
updates.
