# INFR-018 — QA / Compliance review (append-only)

---

## QA run 1 — 2026-07-20T19:40Z — mode: subagent — HEAD 76cf916f842185e519f56070bc9f0cf705038f87

**Reviewed state:** working tree dirty. Untracked: `python/experiments/INFR-018/`, `python/src/xen/sigbar/{acceptance,classes,fences,profile,sessions}.py`, `python/tests/test_sigbar_infr018.py`. Modified: `python/src/xen/sigbar/__init__.py`.
**Nothing executed on the full universe.** `results/` holds a 12-symbol smoke (`--limit 60`).

**Verdict: REVISE**

Six blocking issues. The design document is strong and the HYP-I2 spine is verifiably correct — GT-1 and GT-2 reproduce exactly from staging data, the frozen-input hashes verify, and the universe lag is causal in the right direction. The failures are concentrated in the **controls and the hard tripwires**: three of the six blockers are controls that cannot referee what they are pointed at, and one stops HYP-I3 from executing at all. Two of them (I-2, I-6) would be REJECT-class had this item already run and been reported on; pre-execution they are fixable in code.

---

### 1. Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §0 band fence — DESIGN/CONFIRM only, raise never warn | `fences.py:80-99`, `102-140` | **MATCHES** | `assert_band` raises; holdout checked first and named separately. Every bar read routes through `load_bars`. No unfenced full-file scan — the INFR-017 7b(i) shape does not recur. |
| §0 band fence — enforced on *every* read path | `common.py:91` | **DEVIATES** | `except Exception` swallows `assert_band`'s RuntimeError into `unreadable_staging_files`. See I-7. |
| §0 band fence — raw-trade downloader | `hyp_i4_validation.py:81-94` | **DEVIATES** | No band assertion; the only fence is the `CAL_DAYS` literal. See I-19. |
| §0 CONFIRM used only for confirmation | `hyp_i4_validation.py:140,176-178,202` | **DEVIATES** | Kernel winner selected on DESIGN+CONFIRM pooled. See I-6. |
| §0 no expectancy/hit-rate emitted unlabelled | `hyp_i2:145-154` / `acceptance.py:399-411` | **PARTIAL** | `CALIBRATION_ONLY` wrapper applied in HYP-I2 only; HYP-I3 emits `p_accept_given_yes`, `base_rate` unwrapped. See I-21. |
| §0 frozen inputs re-hashed at every entry point | `fences.py:167-201`; `hyp_i2:170`, `hyp_i3:104`, `hyp_i4:325`, `freeze_and_pin:127` | **MATCHES** | Verified independently: on-disk `seasonal_baselines.parquet` sha256 = `1b7244c8…`, equal to the committed `seasonal_baselines_manifest.json::artifact_sha256`. `column_pins.json::pin_sha256` = `e3b9fd9b…` as contracted. The discarded `78dd7988…` fit cannot load — the hash is checked before use and raises. |
| §2 windows non-overlapping — I2 (IB ⟂ break ⟂ excursion) | `sessions.py:302,322,366` | **MATCHES** | IB `mins_since < L`; break search `>= L`; excursion `OpenTime > break_ts` (strictly after the break bar). Confirmed by GT-1: break bar high 17490.5 excluded, MFE from post-break extreme only. |
| §2 windows non-overlapping — I3 (qualify ⟂ outcome), `assert_windows_disjoint` raises on overlap | `acceptance.py:98-111,175,180` | **BROKEN** | Assertion is `<=`; construction sets `outcome_start == qualify_end`. Raises on the *correct* construction. See I-1. |
| §2 windows non-overlapping — I4 (event bar excluded from its own level set) | `classes.py:180-183`; `hyp_i4:264` | **BROKEN** | `level_created_ts` is literal null for every level ⇒ filter never excludes. See I-4. |
| §3.1 4 anchors × 3 IB lengths, k=12 pre-registered | `sessions.py:65-70,27`; `hyp_i2:204-210` | **MATCHES** | Smoke emitted exactly 12 cells. |
| §3.1 DST-correct equity opens via `zoneinfo` | `sessions.py:207-210` | **MATCHES** | Test pins `{810, 870}` = 13:30 UTC EDT / 14:30 UTC EST. |
| §3.2 IB = `[High.max(), Low.min()]` over `[anchor, anchor+L)` | `sessions.py:301-310` | **MATCHES** | GT-1: 17479.5 / 17416.5, width 63.0, n_ib 60. Exact. |
| §3.2 coverage ≥ 0.9·L and ≥ 0.9·(session_len−L), INCOMPLETE **counted** | `sessions.py:295-337` | **PARTIAL** | Thresholds applied, but `session_len` is the global max across anchors (DST asymmetry, I-25) and INCOMPLETE sessions are dropped without a count (I-27). |
| §3.2 break = first close strictly beyond an IB edge, first in time wins | `sessions.py:345-362` | **MATCHES** | GT-1: 01:07 up-break at 17490.5 (02:17 down-break correctly not the event). GT-2: 08:40 down-break at 15.975 (09:22 up correctly not the event). Both exact. |
| §3.2 excursion normalised by *this session's* IB high−low (L-21) | `sessions.py:378,389-402` | **MATCHES** | GT-1 asym +5.7063; GT-2 asym +4.4167. Both exact to float. |
| §3.3 racing statistic is the paired excess `E`, never a level | `hyp_i2:114,141` | **MATCHES** | Headline is `contrast_median`; absolute levels quarantined under `CALIBRATION_ONLY`. |
| §3.4 pseudo-anchor control, n=30, ≥60 min from the *controlled* anchor | `sessions.py:91,94,103-169` | **MATCHES** | AMENDMENT-1 implemented as written. |
| §3.4 destroy form — zero fixed points, asserted (L-28) | `sessions.py:172-187`; `hyp_i2:196` | **MATCHES** | By construction *and* asserted. Verified for all 4 candidates across 5 seeds. |
| §3.4 bite/MDE — co-designed plant curve, published before the read | `common.py:232-247`; `hyp_i2:159` | **PARTIAL** | Present for I2 only, and it is a location-shift plant on the realised contrast, not the design's synthetic-breakout plant (`widen post-break drift by s·IB_width`). Absent entirely for I3/I4. See I-13. |
| §3.5 tripwire `future_shift` — IB from the next session, windows fixed | `sessions.py:311-321`; `hyp_i2:225-239` | **MATCHES (mechanism)** | `shift(-1)` genuinely moves the boundary; test pins day-0 carrying day-1's IB. |
| §3.5 tripwire is **HARD** — survival ⇒ emission invalid, fix and re-run | `freeze_and_pin.py:82,190` | **BROKEN** | Result copied into the pin; nothing blocks. Smoke returned collapse −6.10 and would have frozen. See I-5. |
| §3.6 CONFIRM refuses before `anchor_freeze.json` exists | `hyp_i2:173-177` | **MATCHES** | GT-3(b) satisfied. |
| §3.7 spot-check **mandatory**, divergence rule escalates before freezing | `hyp_i2:167,241-260`; `freeze_and_pin.py:51-89` | **BROKEN** | Opt-in flag (smoke emitted `spot_check: null`); divergence rule unimplemented; auto-freezes. See I-8. |
| §4.1 poke = first bar whose High/Low exceeds edge by ≥ δ·IB_width | `acceptance.py:143-155` | **MATCHES** | Extremum-based, correctly not close-based (B-4 identity argument holds). |
| §4.2 8 families × params × 3 δ, grid written+hashed before execution | `acceptance.py:69-95`; `hyp_i3:126-137` | **MATCHES** | Grid emitted pre-execution; ids unique; flow/price-only balanced. |
| §4.2 D3 = volume-weighted **median** price | `acceptance.py:259` | **DEVIATES** | Computes a volume-weighted **mean**. Unlogged. See I-9. |
| §4.2 D5–D8 = rule AND same-direction net Δ with `delta_ratio_resid > 0` | `acceptance.py:298-308` | **DEVIATES** | Tests `sign(Σ resid) == poke_side`. See I-10. |
| §4.2 A5 — never a raw Δ number | `acceptance.py:293-297` | **MATCHES** | Raises if `delta_ratio_resid` absent. |
| §4.2 AMENDMENT-2 — one shared 30-min qualifying window | `acceptance.py:36`; `hyp_i3` | **MATCHES** | Ledger direction NEUTRAL is correct; code matches. |
| §4.3 outcome labels ACCEPTANCE / TRAP / UNRESOLVED | `acceptance.py:316-376` | **DEVIATES** | Both qualifying clauses missing; `poke_extreme` is dead. See I-3. |
| §4.3 UNRESOLVED reported with its rate, never dropped | `acceptance.py:387,410`; `hyp_i3:190` | **MATCHES** | |
| §4.4 `S` primary, base rate reported beside it | `acceptance.py:379-411` | **MATCHES** | Call-rate invariance pinned by test. |
| §4.4 control = labels deranged **within calendar-day blocks** | `hyp_i3:212-217` | **DEVIATES** | Deranged across the whole pooled frame. See I-12. |
| §4.4 derangement = zero fixed points (L-28) | `hyp_i3:70-84,213` | **MATCHES** | Rejection-sampled and asserted. |
| §4.4 tripwire `outcome_path_swap` — swap the outcome **price path** | `hyp_i3:291-296` | **BROKEN** | Swaps labels, not paths — identical to the soft control. See I-2. |
| §4.6 bands SEPARATES/SUGGESTIVE/WASH/CONTRADICTED/**UNPOWERED** | `hyp_i3:235-252` | **PARTIAL** | UNPOWERED branch absent (I-14); WASH tested before SEPARATES (I-28). |
| §4.6 bands are labels, nothing dropped or hidden (L-32) | `hyp_i3:254-273,348` | **MATCHES** | No `pass` field; all cells emitted; degenerate cells retained with a status. |
| §5.1 kernel calibrated against trade truth, 3 kernels, winner frozen once | `profile.py:64-124`; `hyp_i4:121-204` | **PARTIAL** | Calibration performed; winner selected on CONFIRM-inclusive pool (I-6); displacement units mislabelled (I-17). |
| §5.1 per-level Δ barred, asserted in code | `fences.py:204-217`; `profile.py:91` | **BROKEN** | Guard checks a hard-coded constant. See I-16. |
| §5.2 thresholds derived as p90/p10 of the DESIGN residual distribution, per symbol, realised values pinned | `classes.py:48-73`; `hyp_i4:231` | **MATCHES** | Values and percentile levels both emitted to the pin. |
| §5.2 classes per source §2.3 | `classes.py:32-39,115-158` | **PARTIAL** | `DRY_UP` declared, never classified (I-20); `|delta_ratio_resid|` vs signed p90 (I-26). |
| §5.2 `d_norm` to nearest structural level (IB edge, prior VA/POC, prior extreme) | `hyp_i4:254-265` | **DEVIATES** | Only IB and prior-IB edges. See I-11. |
| §5.2 control = residual-matched non-events | `classes.py:201-242` | **BROKEN** | Does not match. See I-3 (control), measured below. |
| §5.3 spread bands UNAVAILABLE with binding downstream consequence | `hyp_i4:368-382` | **MATCHES** | Reason, operator decision and downstream consequence all written into the pin. |
| §6.1 universe n=20, quote turnover, causal ≤ t−1, eligibility, tie-break, delisting | `fences.py:224-305`; `common.py:112-120` | **MATCHES** | Turnover on day D ranks day D+1 — lag verified in the right direction (`fences.py:288-297`), pinned by test. Quote turnover (not base volume) with the USDT divisor stated. |
| §6.1 200-vs-197 reconciliation emitted with per-symbol reasons | `common.py:101-121` | **MATCHES** | Emitted; unexercised at full scale (smoke saw 12/12). |
| §6.3 calendar-day-clustered block bootstrap; interval-excludes-zero phrasing | `common.py:175-229` | **MATCHES** | Clustering unit is genuinely the calendar day (`anchor_ts.dt.truncate("1d")`), correctly collapsing A-FUND's 3 sessions/day into one unit. Seed spread, block sensitivity and trimmed-mean all reported. No p-values. |
| §7 HARD — future-destroy tripwires block | `freeze_and_pin.py` | **BROKEN** | See I-5. |
| §7 HARD — `check_no_local_accounting` asserted | — | **MISSING** | Never called anywhere. See I-18. |
| §8 GT-1 / GT-2 | verified live | **MATCHES** | Both exact. See below. |
| §8 GT-3(a) fence raises / (b) CONFIRM-before-freeze raises / (c) wrong sha raises | `fences.py:91-99`; `hyp_i2:173`; `fences.py:182` | **MATCHES** | |
| §8 GT-3(d) per-level Δ construction raises | `profile.py:91` | **BROKEN** | Does not raise. See I-16. |
| §9 registry self-hashed, `pin_sha256` excluded from the body | `freeze_and_pin.py:38-41,214` | **MATCHES** | Follows the `column_pins.json` pattern. |
| §10 execution order enforced by filesystem freezes | `hyp_i3:107-112`; `hyp_i4:326-333` | **MATCHES** | I3 refuses without `anchor_freeze.json`; I4 refuses without both. |
| §11 amendment ledger — directions and running count | `design.md:556-583` | **MATCHES** | Verified below. |

### Golden-trace diff

Re-derived live from `INFR-011/data/staging/bars/` under the design's frozen rules, then compared against design §8. **Expected values taken from the design text, not from the implementation.**

| Event | Design §8 expects | Implementation produced | Verdict |
|---|---|---|---|
| GT-1 IB window / count | `[00:00, 01:00)`, 60 bars | `n_ib = 60` | MATCH |
| GT-1 IB high / low / width | 17479.5 / 17416.5 / 63.0 | 17479.5 / 17416.5 / 63.0 | MATCH |
| GT-1 break | 2023-01-11 01:07, close 17490.5, side UP | 01:07:00, 17490.5, side 1 | MATCH |
| GT-1 later down-break at 02:17 is *not* the event | not selected | not selected | MATCH |
| GT-1 MFE / MAE | 540.50 / 181.00 | 540.5 / 181.0 | MATCH |
| GT-1 MFE_norm / MAE_norm / A | 8.5794 / 2.8730 / **+5.7064** | 8.579365 / 2.873015 / **+5.706349** | MATCH |
| GT-2 session partition (8h funding) | `[08:00, 16:00)` | anchor 08:00, n_post 450 | MATCH |
| GT-2 IB high / low / width | 16.10 / 15.98 / 0.12 | 16.1 / 15.98 / 0.12 | MATCH |
| GT-2 break (DOWN branch) | 08:40, close 15.975 | 08:40:00, 15.975, side −1 | MATCH |
| GT-2 later up-break at 09:22 is *not* the event | not selected | not selected | MATCH |
| GT-2 MFE / MAE / A | 0.6850 / 0.1550 / **+4.4166** | 0.685 / 0.155 / **+4.416667** | MATCH |
| GT-3(a) DESIGN path sees `OpenTime ≥ 2023-03-01` | raises | raises `BAND VIOLATION` | MATCH |
| GT-3(b) CONFIRM before `anchor_freeze.json` | raises | raises | MATCH |
| GT-3(c) baselines sha ≠ `1b7244c8…` | raises | raises `FROZEN INPUT MISMATCH` | MATCH |
| GT-3(d) per-level Δ profile construction | raises | **accepted, returned a profile summing to 2880.0** | **FAIL** |

GT-1/GT-2 exact reproduction is a genuine result: the HYP-I2 session, break and excursion construction is correct, including the first-break-in-time rule across both sides and the 8-hourly partition. The design's own §8 status claim ("both reproduce EXACTLY from the implementation") is confirmed independently rather than accepted.

### Governance & boundary

| Check | Evidence |
|---|---|
| All 13 mandatory declaration blocks present | §1 mechanism, §2 object-identity, §3.4/§4.4/§5.2 control-validity (3 blocks, each with question / population / disjointness / bite / non-vacuity / expected-if-true / expected-if-false / disclosure / destroy form / class), §3.5+§4.4 tripwires, §4.6 bands, §6.2 power, §8 golden trace, §7 hard-vs-informative, §11 ledger. Blocks 9/10/11 declared N/A with reasons that hold (no P&L object, no money conversion, no tradability band; `SpreadBps` additionally pinned UNUSABLE). |
| Frozen inputs verified independently | `seasonal_baselines.parquet` sha256 `1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72` — matches design §0, INFR-017 report §8, **and** the committed `seasonal_baselines_manifest.json::artifact_sha256`. `column_pins.json::pin_sha256` = `e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225` — matches the contract. Discarded `78dd7988…` unloadable. `assert_frozen_inputs` additionally re-checks that the W2 decision still reads UNUSABLE. |
| Holdout | No path can reach `≥ 2025-01-08`. `assert_band` checks the holdout first and names it. Trade-archive `CAL_DAYS` are all ≤ 2023-11-01. **No holdout contact.** |
| TEST band | Untouched; 0 counted reads; no TEST read attempted anywhere. |
| CONFIRM band | **Violated for HYP-I4 exit 1** — see I-6. Correctly gated for I2/I3 by the freeze-file refusals. |
| Causality ≤ t−1 on universe selection | Correct direction, verified at `fences.py:288-297` and by `test_universe_selection_is_causal_and_lags_one_day`. Turnover measured over day D ranks day D+1. Not off by one in either direction. |
| L-28 derangement | HYP-I2 pseudo-anchor: satisfied by construction **and** asserted. HYP-I3 label derangement: rejection-sampled to zero fixed points and asserted. **But** the I3 destroy is applied to the wrong object (I-2) and at the wrong stratification (I-12). |
| L-32 / INFR-016 report layers | Honoured. No `pass` field anywhere; bands are labels; no candidate hidden or machine-dropped between layers. One exception: the CI auto-drop at I-23. |
| L-23 amendment ledger | Both entries verified. **AMENDMENT-1 direction TIGHTER is correct** — I re-derived the mechanism: scoping the exclusion to the controlled anchor admits control clocks near *other* meaningful times, which raises the control level and therefore lowers `E`, i.e. conservative. Code matches (`PSEUDO_EXCLUSION_MINUTES=60`, `N_PSEUDO=30`, stratified placement, `OCCUPIED_MINUTES` consulted per-anchor). **AMENDMENT-2 direction NEUTRAL is correct**; `QUALIFY_MINUTES=30` shared across all candidates. Running count 0L/1T/1N is right; no one-directional streak. **However** the D3 mean-for-median substitution (I-9) is an unlogged third pre-measurement change. |
| L-21 unit pins | Honoured for the excursion divisor (session IB high−low, stated with every number) and the turnover unit (USDT). **Violated** for kernel displacement (I-17). |
| `check_no_local_accounting` | Never invoked (I-18). Substantively satisfied — no accounting primitive exists in the item — but the design claims it is machine-checked. |
| No Python strategy backtest | Confirmed. No `BacktestNode`, no fills, no positions, no P&L. L-29/L-30/L-31 correctly N/A. |
| XENA VOID on new stack | N/A — this item routes to no XENA gate. |
| Registry preconditions | CF-SIGAUC-001 REGISTERED 2026-07-20 (checkpoint-014 D1). 0 slots, 0 counted reads declared and honoured. |
| Source fidelity (Appendix B order) | Honoured. Phase 1 → freeze → Phase 2 → freeze → Phase 3 → pin, enforced by filesystem freezes. The **provisional pre-A6 break rule** in Phase 1 is a legitimate reading, not circular: the source itself orders Phase 1 before the A6 freeze, so Phase 1 cannot use A6; the code applies `FIRST_CLOSE_BEYOND` identically to all 12 cells *and* to all 30 control clocks (`hyp_i2:100-108` passes the same `ib_minutes` and rule to both arms), so it cannot favour a candidate, and it is recorded in the pin as provisional and race-internal. Accepted. |
| Source fidelity — Phase 1 "raw breakout expectancy" | The design substitutes a matched contrast `E` for the source's "raw expectancy". This is a **strengthening** consistent with source §6.3 ("conditional minus matched unconditional IS the edge") and with the §0 scope fence. Accepted. |
| Source fidelity — Phase 2 "race on out-of-sample power" | Substituted with DESIGN-select → CONFIRM-verify per checkpoint D3. Declared in design §4.5 and recorded in the pin. Accepted. |
| Source fidelity — Phase 3 "spread regime bands are finalized here" | Recorded UNAVAILABLE with reason and binding downstream consequence rather than faked. Accepted. |
| Operator-facing communication | Chat summary kept plain; file:line detail confined to this document. |

**Test suite: 26 passed in 1.36s.** The tests are well-written but systematically miss the production seams:

- `test_window_overlap_raises` (`:216`) tests `outcome_start = qualify_end − 1min` and `+ 1min`. It never tests the **equal** case, which is what `find_pokes` actually emits — so the suite is green while the production path raises on every event.
- `test_per_level_delta_is_barred` (`:65`) exercises the guard in isolation with named Series. It never asserts that `build_profile` rejects anything, which is the only place the ban matters.
- No test that `residual_matched_control` produces a matched control.
- No test that a future-destroy tripwire blocks anything.
- No test of `label_outcomes` against §4.3.
- No end-to-end test of `find_pokes` → `evaluate_discriminator` → `separation`.

The suite pins helper behaviour and the HYP-I2 construction (which is genuinely correct). It does not pin the load-bearing controls.

---

### Issues

**I-1 — BLOCKER — HYP-I3 cannot execute: the window assertion rejects the correct construction.**
`acceptance.py:106` — `bad = events.filter(pl.col("outcome_start") <= pl.col("qualify_end")).height`
`acceptance.py:175` — `.with_columns(pl.col("qualify_end").alias("outcome_start"))`
`outcome_start` is set *equal* to `qualify_end`. The qualifying window is `[poke_ts, qualify_end)` (`:200`) and the outcome window is `[outcome_start, session_end)` (`:336`) — both half-open, so equality is exactly the correct, disjoint, adjacent construction. The assertion's `<=` flags it as an overlap, so `find_pokes` raises on every non-empty poke set (`:180`), and `hyp_i3:184` would raise again.
*Verified:* on a synthetic session with one clean poke, `find_pokes` raised `WINDOW OVERLAP: 1 events…`.
*Why it matters:* Phase 2 produces nothing, and `freeze_and_pin.py a6` therefore never runs, which blocks Phase 3 and the registry. The tempting "fix" — deleting or loosening the assert — would remove the item's only guard on its most leak-prone seam.
*Fix:* change the comparison to `<` (strict). Add a test pinning the equal case as **valid** and `qualify_end + 1ns` as valid, and `qualify_end − 1min` as invalid.

**I-2 — BLOCKER — the HYP-I3 hard tripwire is not the tripwire the design specifies, and it cannot fail.**
`hyp_i3_a6_race.py:291-296` — the "outcome_path_swap" permutes `label`, `t_accept`, `t_trap`.
Design §4.4 requires: *"Replace each event's OUTCOME-WINDOW PRICE PATH with the outcome path of a DERANGED other event"*, and explicitly contrasts this with label destruction: *"the labels are computed FROM the outcome path, so swapping paths destroys the true rule→outcome pairing at the source rather than at the label."*
As implemented it is byte-for-byte the same operation as the soft `control_deranged` arm at `:212-217`.
*Why it matters:* the mechanism, not the rule. A label derangement collapses `S` **whether or not a leak exists**, because the discriminator's calls are compared against labels that no longer belong to those events. So the tripwire returns "collapsed" under both hypotheses and carries zero information. The specific failure it exists to catch — a qualifying window that reaches into outcome bars, e.g. an off-by-one in `:200` or a widened `w` in D3/D4 exceeding `QUALIFY_MINUTES` — would still produce calls correlated with the *true* outcome path, which is precisely what a path swap destroys and a label swap does not. This is the item's only HARD leak check on the seam the design itself calls "the item's single most leak-prone".
*Fix:* derange the outcome-window **bars** (matched on remaining session length), recompute labels from the swapped path via `label_outcomes`, then re-run the discriminator against those labels. Assert zero fixed points on the path assignment. Add a positive control: plant a deliberately leaky discriminator (one whose window extends past `qualify_end`) and confirm the tripwire collapses it while leaving a clean discriminator's `S` intact — that is the only evidence the tripwire can referee at all.

**I-3 — BLOCKER — the residual-matched control does not match.**
`classes.py:224-231` — deciles are computed **separately within the pool and within the events**:
```
pool = all_bars.filter(sig_class.is_null()).with_columns((volume_resid.rank("ordinal") * 10 // (pl.len()+1)).alias("v_dec"), …)
ev   = event_bars.with_columns((volume_resid.rank("ordinal") * 10 // (pl.len()+1)).alias("v_dec"), …)
```
then matched on `v_dec`/`r_dec` at `:234`. Because each population is ranked against itself, this matches *relative rank within disjoint populations*, not residual **values**. Class events are by construction in the upper tail of the full distribution, so event-decile 0 (the mildest class events) is matched to pool-decile 0 (the quietest ordinary bars) — opposite ends of the residual axis.
*Verified:* 2,000-bar synthetic, events = top-decile `volume_resid`:
`EVENT mean +1.709 [1.27, 3.07]` · `CONTROL mean −0.207 [−2.97, 1.27]` · `POOL mean −0.221`.
The control sits on the pool mean, not the event mean. It is the unmatched pool.
*Why it matters:* this is the exact confound the design names as fatal — §5.2: *"whether proximity to structure is a property of the CLASS or merely of high-volume/wide-range bars generally — which is exactly the confound that would make the classes decorative."* With no matching, the HYP-I4 exit-2 contrast reduces to "active bars vs quiet bars", and since active bars are mechanically nearer session extremes and IB edges, the contrast is biased toward the "classes cluster" conclusion. The design's non-vacuity proof (B-1/B-6) does not hold of this code.
*Fix:* bin on a **common** reference distribution — compute the decile edges once from `all_bars` (or from the frozen per-symbol residual quantiles already derived at `classes.py:48-73`) and apply those same edges to both arms. Add a test asserting the control arm's mean `volume_resid` and `range_resid` lie within a tolerance of the event arm's.

**I-4 — BLOCKER — the event-bar exclusion in the clustering test is inert, and its failure is directional.**
`hyp_i4_validation.py:264` — `.with_columns(pl.lit(None, dtype=pl.Datetime).alias("level_created_ts"))`
`classes.py:180-183` — the filter is `level_created_ts.is_null() | (level_created_ts != OpenTime)`.
With `level_created_ts` null for every level, the left disjunct is always true and **nothing is ever excluded**.
*Why it matters:* `tagged` (`hyp_i4:239`) contains all session bars including the IB window, and the level set is the IB high/low. A class event that *is* the bar which set `ib_high` scores `d_norm = 0` by construction. Class events are high-volume / wide-range / extreme-delta bars — disproportionately the bars that set session extremes — while matched non-events are not. So the defect pushes the event arm toward zero distance relative to control, in the direction that makes exit 2 pass. Design §2 declares this exclusion code-asserted precisely because *"including it would manufacture the clustering the test is meant to detect."*
*Fix:* populate `level_created_ts` with the timestamp of the bar that established each level (for IB edges, the argmax/argmin bar of the IB window; for prior-session levels, the corresponding prior bar), then verify the filter removes a non-zero count and emit that count.

**I-5 — BLOCKER — the two HARD future-destroy tripwires never block anything.**
`freeze_and_pin.py:82` (`"tripwire_future_shift": race["tripwire_future_shift"]`), `:116` (same for I3), `:190-191` (`validity_attestations`).
Both tripwire results are copied into the freeze files and the registry. No code path reads them, compares them to a threshold, or refuses to freeze.
Design §7 lists them under **HARD (block — failure means EMISSION INVALID, fix the data/code and re-run; never "no edge")**; §3.5 says *"IF E SURVIVES: … EMISSION INVALID ⇒ fix the code and re-run."*
*Verified in the smoke:* `tripwire_future_shift` returned `contrast_raw = +0.382`, `contrast_shifted = −2.333`, `collapse_fraction = −6.10`, with the shifted CI `[−2.694, −1.957]` excluding zero. That is not a collapse to ≈ 0 within the control band — it is a larger-magnitude effect of opposite sign, i.e. an uninterpretable result under the design's own reading. Nothing stopped, and `freeze_and_pin.py anchor` would have frozen on it.
*Why it matters:* the design's careful separation of *value* reads (report layers, operator judges — correct per L-32) from *integrity* gates (hard, machine-blocking) collapses if the integrity gates are also merely reported. An invalid emission would be pinned as a validated instrument and inherited by all of Stage II.
*Fix:* implement the decision explicitly in `freeze_anchor` / `freeze_a6` — refuse to write the freeze file unless `|E_shift|` lies inside the control band (and `|S_swapped|` inside its band), and raise naming the tripwire. Separately, investigate why the shifted arm produces a large negative contrast rather than ≈ 0: shifting to the next session's IB also changes `ib_width`, so the normaliser moves with the boundary, which may make this tripwire's null non-zero by construction. If so, the tripwire needs the divisor held fixed, or a different destroy.

**I-6 — BLOCKER — the frozen kernel is selected using CONFIRM-bank data.**
`hyp_i4_validation.py:140` — `band = "DESIGN" if day in DESIGN_CAL_DAYS else "CONFIRM"`
`hyp_i4_validation.py:176-178` — `summary` aggregates **all four** `CAL_DAYS`.
`hyp_i4_validation.py:202` — `"winner": summary["kernel"][0]`.
`summary_design_only` is computed at `:179-186` and emitted — but is never used to choose.
*Judgment on the disclosure:* the design's permission (§5.1) is that CONFIRM days may be used because *"kernel calibration measures reconstruction fidelity of a bar aggregation, not expectancy, and consumes no selection budget."* The first half is defensible — reconstruction fidelity genuinely is not an expectancy read. The second half is falsified by the code: the winner **is** selected on the pooled set, so a selection budget is spent on CONFIRM. Checkpoint-014 §5 defines CONFIRM as *"untouched during that phase's tuning"* and design §0 as *"DESIGN bank for all tuning/selection."* This is a violation dressed in a disclosure, not a permitted use — the disclosure describes a weaker act than the code performs.
*Why it matters:* the kernel is a frozen instrument inherited by every downstream profile, VA edge and POC. Selecting it on CONFIRM leaves HYP-I4 with no untouched band in which to confirm anything, which is the whole point of the D3 adaptation.
*Fix:* select from `design_only` (`:202` → `design_only["kernel"][0]`), and report the all-days table as the TRAIN-internal confirmation, labelled as such. This is a one-line change and costs nothing — the DESIGN subset is already computed.

**I-7 — MAJOR — the band fence is downgraded from raise to log at the one path that scans the whole staging directory.**
`common.py:88-93`:
```
try:    bars = load_bars(sym, band, root=root)
except Exception as exc:  # corrupt staging parquet — INFR-011 owns these
    unreadable.append({"symbol": sym, "reason": f"{type(exc).__name__}: {exc}"})
    continue
```
`load_bars` raises `RuntimeError("HOLDOUT VIOLATION: …")` / `("BAND VIOLATION: …")` via `assert_band`. Both are `Exception` and are swallowed into a reconciliation note.
*Why it matters:* this is structurally the INFR-017 defect 7b(i) shape — a full-directory scan whose fence does not stop the run — inverted. Today the filter at `fences.py:126` runs before the assert so the assert should not fire; that makes this a latent, not an active, breach. But `fences.py:5-9` states the module's first guarantee as *"Band fences raise, never warn"*, and at the one place it matters most that guarantee is not kept. A future change to the filter (or a parquet with an out-of-range `OpenTime`) would be recorded as a corrupt-file note and the run would continue and report.
*Fix:* catch only the parquet/IO error classes, or re-raise when the message names a BAND or HOLDOUT violation.

**I-8 — MAJOR — the mandatory per-instrument spot-check is optional, and its escalation rule is unimplemented.**
`hyp_i2_anchor_race.py:167` — `--spot-check` is an opt-in flag defaulting to off. The existing smoke artifact records `"spot_check": null`.
`freeze_and_pin.py:51-89` — `freeze_anchor` never reads `spot_check` and freezes `ranked[0]` unconditionally.
Checkpoint-014 §4 (adherence resolution 2, operator-signed) makes the spot-check **mandatory**. Design §3.7 pre-declares the DIVERGENCE RULE — *"MATERIAL divergence … record as a SCOPE LIMIT and ESCALATE TO THE OPERATOR BEFORE FREEZING. Do not auto-freeze."*
*Why it matters:* the rule was pre-declared specifically so it could not be argued after the table is seen. Code that cannot evaluate it converts a signed operator control into a manual step that a run will silently skip. `build_registry:163` then writes `pooled_vs_spot_check: null` into the deliverable while the §9 spec requires that table.
*Fix:* run the spot-check unconditionally on the DESIGN band; implement the MATERIAL/COSMETIC classification in `freeze_anchor` and raise with the table on MATERIAL, instructing the operator.

**I-9 — MAJOR — D3/D7 compute a volume-weighted mean where the design specifies a median, on an incorrect justification, unlogged.**
`acceptance.py:259` — `((tp * Volume).sum() / Volume.sum()).alias("vwap_w")`, commented *"a weighted MEDIAN over bars would need per-level placement, which is barred."*
Design §4.2 defines D3 as *"the qualifying window's volume-weighted **median** price migrates beyond the edge"*, and the §4.2 hard-constraint paragraph analyses D3 on that basis.
*Why it matters:* three separate problems. (a) The stated reason is wrong — a volume-weighted median over per-bar typical prices is computed by sorting bars on `tp`, cumulating `Volume`, and taking the 50% crossing; no per-level placement is involved, so the card ban 2 argument does not apply. (b) The substitution is material: a mean is dragged by a single wide vacuum bar in a way the median is not, which is exactly the regime D3 is meant to discriminate. (c) It is a pre-measurement change with no §11 ledger entry and no direction — an L-23 breach, and the ledger's "no amendment loosened anything" re-derivation is therefore computed over an incomplete set.
*Fix:* implement the volume-weighted median, or amend the design with a logged direction and a correct rationale.

**I-10 — MAJOR — the flow-augmented twins do not implement the declared rule, and invert it for down-pokes.**
`acceptance.py:298-308`:
```
.agg(delta_ratio_resid.sum().alias("resid_sum"), poke_side.first().alias("side"))
.with_columns(((resid_sum * side) > 0).alias("flow_ok"))
```
Design §4.2 defines D5–D8 as *"the same rule **AND** net Δ over the qualifying bars is same-direction with **seasonal-residual** `delta_ratio_resid > 0`"* — two conditions: direction agreement, and an elevated residual.
The code tests one: that the **sign of the summed residual** agrees with the poke side. Raw Δ direction is never evaluated. And for a down-poke (`side = −1`) the condition requires `resid_sum < 0`, i.e. Δ/V *below* its seasonal baseline — the opposite of the declared `delta_ratio_resid > 0`.
*Why it matters:* D5–D8 are the flow-augmented arm, and whether signed flow improves the A6 discriminator is the family's headline Phase-2 question. A6 in the source reads *"acceptance accompanied by same-direction Δ vs against it"* — direction — which the code only approximates via the residual's sign. A5 compliance is intact (a residual is used, not a raw number), but the discriminator being raced is not the discriminator that was pre-registered.
*Fix:* decide the intended rule and state it unambiguously in §4.2 — most likely `sign(Σ Δ) == poke_side AND Σ delta_ratio_resid > 0` — then implement exactly that, and log the clarification with a direction.

**I-11 — MAJOR — the structural level set omits two of its three declared families, and orphans the kernel.**
`hyp_i4_validation.py:254-263` builds levels from `IB_HIGH`, `IB_LOW`, `PRIOR_IB_HIGH`, `PRIOR_IB_LOW` only.
Design §5.2 requires *"the nearest **structural level** (IB edge, prior-session VA edge / POC from the frozen kernel, prior-session extreme)"*.
Missing: the prior-session **VA edge and POC** (which exit 1 calibrates the kernel expressly to produce). Substituted: prior-session **IB** high/low stands in for the prior-session **extreme**, which is a different object (the IB is the first 15–60 minutes; the session extreme is the full session's range).
*Why it matters:* exit 2 adjudicates whether the §2.3 classes cluster at structure. Testing against a reduced and partly substituted level set answers a narrower question, and it means the kernel calibrated in exit 1 is never consumed by exit 2 — so the two exits do not compose the way §5 describes. It also makes a null result uninterpretable: "classes do not cluster at IB edges" is not "classes do not cluster at structure".
*Fix:* build prior-session profiles with the frozen kernel and add POC/VAH/VAL to the level set; add the prior session's true high/low alongside (or instead of) the prior IB edges; emit `nearest_kind` counts per class so the operator can see which level family carries the contrast.

**I-12 — MAJOR — the label derangement is pooled, not blocked by calendar day.**
`hyp_i3_a6_race.py:212` and `:291` — `perm = derangement(res_only.height, rng)` over the whole concatenated frame.
Design §4.4: *"outcomes DERANGED across poke events **within calendar-day blocks**"*.
*Why it matters:* deranging across the entire panel destroys the day-level common component as well as the rule→outcome pairing, so the control's `S` is driven closer to zero than the declared within-day control would be. The collapse fraction — the disclosure the operator reads — is therefore flattered, and the contrast between real and control is inflated. It also makes the control inconsistent with the day-clustered inference used everywhere else in the item.
*Fix:* derange within `day` groups, and assert zero fixed points per block. Note that small day-blocks may not admit a derangement (`n < 2`); those days must be reported, not silently passed through unpermuted.

**I-13 — MAJOR — the declared MDE curves exist for one gate out of three, and HYP-I3 substitutes a different object.**
`mde_curve` (`common.py:232-247`) is called **only** at `hyp_i2:159`.
`hyp_i3:234` — `mde_here = ci.get("stat") is not None and abs(ci["ci"][1] - ci["ci"][0]) / 2 or None` — a CI half-width, not a plant curve. (The `and`/`or` chain also silently yields `None` when the half-width is exactly 0.0.)
`hyp_i4` computes no MDE at all.
Design §4.4 requires *"plant a synthetic rule with known separation s and confirm the deranged version reads S ≈ 0 across s — the MDE curve for S at the realised n is published before the read"*; §5.2 requires *"plant class events at known distances from levels and sweep"*; §6.2 requires the MDE *"read off the co-designed plant curves (§3.4, §4.4, §5.2) at the realised n per stratum and PUBLISHED BEFORE the real read. No MDE is asserted from memory."*
Additionally, the I2 plant that does exist (`common.py:242`, `values - median(values) + s`) is a location shift on the realised contrast, not the design's *"widen post-break drift in the break direction by s·IB_width"* — it inherits the realised dispersion honestly but does not exercise the construction, so it cannot detect a construction that is insensitive to a real effect.
*Why it matters:* the MDE is what separates WASH ("cannot distinguish") from a negative, and it is what B-5 depends on. Without a plant curve, `WASH` in HYP-I3 is defined by the width of the interval it is being compared against — circular — and HYP-I4 has no basis for declaring any class UNPOWERED.
*Fix:* implement the two declared bite checks; emit each curve to its artifact before the real statistic is written; keep the CI half-width as a secondary disclosure only.

**I-14 — MAJOR — the UNPOWERED band is not implemented.**
`hyp_i3_a6_race.py:235-252` — the band ladder emits `DEGENERATE_CALL_RATE`, `WASH`, `SEPARATES`, `SUGGESTIVE`, `CONTRADICTED`. No `UNPOWERED`. `grep -rn UNPOWERED` over `experiments/INFR-018/code/` and `src/xen/sigbar/` returns nothing.
Design §4.6 declares *"UNPOWERED: MDE > 0.15 at the realised n → **EXCLUDED FROM NEGATIVES (B-5)**, reported as power, never folded into a failure"*, and §6.2 pre-declares four UNPOWERED strata.
*Why it matters:* an underpowered cell will be labelled `WASH`. `WASH` reads as "measured and cannot distinguish"; `UNPOWERED` reads as "not measurable at this n". Collapsing the second into the first is how absence of evidence becomes evidence of absence — the L-32 failure the programme retired, and the XENA-HTFCAP-001 selection defect (a suggestive-underpowered cell passed over) in miniature.
*Fix:* add the UNPOWERED branch ahead of WASH, driven by the I-13 plant curve; emit the §6.2 pre-declared strata explicitly flagged.

**I-15 — MODERATE — the outcome labels do not implement §4.3; `poke_extreme` is dead.**
`acceptance.py:329` selects `poke_extreme`; `grep` confirms it is referenced nowhere after selection.
Design §4.3: `TRAP` = *"price returns inside and touches the opposite IB edge **before exceeding the poke extreme**"*; `ACCEPTANCE` = *"price travels ≥ 1·IB_width further beyond the edge **before returning inside the IB range**"*.
`acceptance.py:339-364` races `hit_accept` (High ≥ ib_high + ib_width) against `hit_trap` (Low ≤ ib_low). Neither qualifying clause is implemented.
*Why it matters:* these labels are the ground truth the entire HYP-I3 race is scored against, and the frozen A6 rule is whichever candidate best predicts them. As coded, `TRAP` admits events that first exceeded the poke extreme (which S3 treats as invalidation — *"A second poke exceeding the first extreme. Exit; never average."*), and `ACCEPTANCE` admits events that round-tripped back inside the IB before running. The winner is selected against a different object than the one §4.3 defines, and that object is inherited by all of Stage II.
*Fix:* implement both clauses as first-passage races over the outcome window; assert `poke_extreme` is consumed.

**I-16 — MODERATE — the per-level-Δ ban is asserted against a hard-coded constant.**
`profile.py:91` — `assert_no_per_level_delta(pl.Series("Volume", []))  # contract check: volume only`
The guard (`fences.py:204-217`) inspects `obj.name` for `delta`/`signed`/`buyvolume`/`sellvolume`. Passing a literal `pl.Series("Volume", [])` means it evaluates the same constant on every call and can never fail, regardless of what `bars` contains.
*Verified:* `build_profile` on a frame whose `Volume` column was replaced with `|Delta|` returned a profile summing to 2880.0 — no exception. GT-3(d) is not satisfied.
*Substantively the ban holds*, because `build_profile:103` hard-codes `bars["Volume"]` and no signed profile is constructed anywhere. But `profile.py:16-17` states *"Every entry point calls `assert_no_per_level_delta`, so a signed column cannot reach a kernel even by accident"*, design §7 lists *"no per-level Δ attribution anywhere (asserted)"* as HARD, and `freeze_and_pin.py:196` writes `"per_level_delta": "BARRED — asserted in xen.sigbar.fences.assert_no_per_level_delta"` into the deliverable. All three assert a verification that is not performed — the INFR-017 run-1 Issue-8 shape.
*Fix:* either check the actual column identity being distributed (pass the column name through `build_profile`), or drop the guard and state plainly in the pin that the ban holds by construction because the kernel reads only `Volume`. Do not pin a claim of machine enforcement that does not exist.

**I-17 — MODERATE — kernel displacement is normalised by the day range but will be pinned as IB-width units.**
`hyp_i4_validation.py:153` — `scale = float(bars["High"].max() - bars["Low"].min())` over the **full calibration day**.
`profile.py:176-205` — `displacement(…, scale)`, docstring *"The window's IB width (or range)"*, emits `poc_disp_norm`, `val_disp_norm`, `vah_disp_norm`.
Design §5.1 specifies *"POC displacement … in **ticks** and in **IB-width units**"*.
No tick-unit figure is emitted at all, and the normalised figures are day-range-normalised while the design and the registry label them IB-width. `profile.py:38-47` separately documents that the grid is relative rather than tick-multiple, contradicting §5.1's *"tick-multiple bins, per symbol"*.
*Why it matters:* card ban 5 and L-21 — *"every normalised effect states its normaliser object exactly"*, and the programme's recorded 4× ATR-unit inflation at the EXP-025 screen→graduation seam came from exactly this. The registry is the artifact SPDR-007 reads.
*Fix:* normalise by the session IB width (the object §5.1 names) or relabel the field to `poc_disp_norm_dayrange` everywhere including the pin; add the tick-unit figure for the symbols where tick size is recoverable and state SPEC_INCOMPLETE for the rest.

**I-18 — MODERATE — `check_no_local_accounting` is never called.**
Design §7 lists it under HARD: *"no local accounting primitives (`check_no_local_accounting`) — trivially satisfied, no accounting occurs; **asserted anyway so the guarantee is machine-checked**."*
`grep -rn check_no_local_accounting` over `python/experiments/INFR-018/` and `python/src/xen/sigbar/` matches only the design text.
The guarantee is substantively true — I found no accounting primitive in the item — but it is not machine-checked, and `freeze_and_pin.py:197` writes the claim into the registry.
*Fix:* call it in `freeze_and_pin.build_registry`, or soften the design and pin language to "verified by inspection at QA run 1".

**I-19 — MODERATE — the raw-trade downloader has no band assertion.**
`hyp_i4_validation.py:81-94,99-113,131` — days come from the `CAL_DAYS` literal and the parsed trade frame is never passed through `assert_band` (nor is any equivalent check applied to the downloaded timestamps).
Design §3.5 requires the fence *"code-asserted on every read path"*.
Currently safe: all four days are ≤ 2023-11-01, well inside TRAIN. But the protection is a constant, not a check, and this is the one read path that fetches data from outside the fenced staging tree.
*Fix:* assert the parsed trade timestamps fall inside the declared band for that day before use.

**I-20 — MODERATE — `DRY_UP` is declared as a class but never classified.**
`classes.py:36` lists `DRY_UP` in `CLASSES`; the `classify` when-chain (`:116-157`) has no `DRY_UP` branch. `LOCATED_CLASSES` (`:45`) excludes it with a sound reason — it is a trend across bars, not a location — but that justifies excluding it from the *clustering test*, not from *classification*.
Design §5.2 lists it among the classes to detect; §9 promises per-class counts in the pin.
*Why it matters:* the registry will carry a per-class count table in which `DRY_UP` is silently absent rather than reported as "not implemented, with reason". A reader of the pin cannot tell the difference between "no DRY_UP events occurred" and "DRY_UP was never looked for".
*Fix:* either implement the multi-bar detector or record `DRY_UP: NOT_DETECTED_THIS_ITEM` with the reason in the pin and in §5.2.

**I-21 — MODERATE — the §0 `CALIBRATION_ONLY` labelling is applied in one gate out of three.**
`hyp_i2:145-154` wraps absolute arm levels under `CALIBRATION_ONLY: NOT_AN_EDGE_CLAIM`.
`acceptance.py:399-411` emits `p_accept_given_yes`, `p_accept_given_no`, `base_rate`, `call_rate` — per-discriminator absolute conditional hit rates — and `hyp_i3:254-273` writes them with no such wrapper. `hyp_i4` likewise emits `median_d_norm_event` unwrapped.
§0 requires *"absolute per-anchor / per-discriminator levels are written to artifacts under `CALIBRATION_ONLY: NOT_AN_EDGE_CLAIM`"*, and §0's forbidden list explicitly names "hit rate".
§4.4 does require the base rate be reported beside `S` — that is correct and should stay. The issue is the missing label, which §0 makes the enforcement mechanism.
*Why it matters:* §0 asks whether the labelling is load-bearing or decorative. Applied to one of three gates, it is decorative. `p_accept_given_yes` for the winning discriminator is precisely the number a downstream reader would mistake for an edge claim.
*Fix:* wrap the absolute conditional rates in HYP-I3 and the absolute distances in HYP-I4 under the same key.

**I-22 — MODERATE — smoke artifacts occupy the exact filenames the freeze step consumes.**
`results/hyp_i2_anchor_race_DESIGN.json` and `results/universe_membership_DESIGN.parquet` on disk are from a `--limit 60` / 12-symbol smoke. `freeze_and_pin.freeze_anchor` (`:59`) reads `hyp_i2_anchor_race_DESIGN.json` blindly; the race artifact records no universe size, symbol count or `--limit` value (that information lives only in `universe_reconciliation.json`, a different file which is overwritten independently).
*Why it matters:* running `freeze_and_pin.py anchor` before a full race would silently freeze the anchor on 12 symbols, and the registry would carry no field revealing it.
*Fix:* stamp `n_symbols`, `n_days` and the `--limit` value into the race artifact, and have `freeze_anchor` refuse to freeze an artifact whose universe is smaller than the declared n=20 panel.

**I-23 — MODERATE — days on which a rule made no call are silently dropped from the HYP-I3 interval.**
`hyp_i3_a6_race.py:220-229` — `p_yes` / `p_no` are computed with `.filter(…).mean()`, then `.drop_nulls()` removes any day where the rule made no accept-call *or* no reject-call.
*Why it matters:* for a low-call-rate discriminator this conditions the uncertainty estimate on the days the rule fired — a selection effect on the very inference used to place the cell in a band. The dropped-day count is not emitted, so it is invisible. Design §7: *"Nothing is machine-dropped between layers."*
*Fix:* emit `n_days_dropped_no_call` per cell; consider a pooled-within-day estimator that tolerates one-sided days.

**I-24 — MINOR — `block_fragile` only inspects the lower CI bound.**
`common.py:222` — `signs = {np.sign(r["ci"][0]) for r in sens}`. A negative effect whose zero-exclusion flips across the ½×/1×/2× sweep (e.g. `[−0.5, −0.1]` → `[−0.5, +0.2]`) keeps `sign(ci[0]) = −1` throughout and is not flagged.
*Fix:* flag when `ci_excludes_zero` or the sign of the point estimate differs across the sweep.

**I-25 — MINOR — the session-coverage floor uses the global maximum session length, penalising DST-short sessions.**
`sessions.py:295-299` takes `session_len` as the **max** over all anchors, then `:333` applies `n_post >= 0.9 * (session_len − ib_minutes)` to every session.
For `A-USOPEN`/`A-EUOPEN`, DST makes sessions 23h, 24h or 25h. With `session_len = 1500` and `L = 60`, a 23h session (1320 post-IB bars available) must supply 1296 — a ~98% coverage bar rather than 90%.
*Why it matters:* small (≈2 days/year × 2 anchors) but it is an **anchor-asymmetric** admission filter inside a race between anchors, and the DST anchors are the two it penalises.
*Fix:* compute `session_len` per session from `session_end − anchor_ts`.

**I-26 — MINOR — `classify` compares an absolute residual against a signed percentile.**
`classes.py:123` — `delta_ratio_resid.abs() >= dr_hi`, where `dr_hi` is the p90 of the **signed** residual distribution (`:48-73`).
Capturing both tails matches the BLOWOFF mechanism ("extreme one-sided Δ"), so the intent is right — but the pin records the signed p90 while the code applies it to `|resid|`, so the threshold cannot be re-derived from the pin as written.
*Fix:* derive and pin the percentile of `|delta_ratio_resid|` explicitly, or record the transformation alongside the value.

**I-27 — MINOR — INCOMPLETE sessions are dropped without a count.**
`sessions.py:329-337` — under-covered sessions are removed by the `ok` semi-join; no count is returned or emitted.
Design §3.2: *"else `INCOMPLETE` (counted, never silently dropped)"*.
*Fix:* return the incomplete count per (symbol, anchor, L) and emit it in the cell record.

**I-28 — MINOR — the band ladder tests WASH before SEPARATES.**
`hyp_i3_a6_race.py:237` — a cell with `|S| < mde_here` is labelled WASH even if `S ≥ 0.15` with `ci_low > 0.05` and a collapse ≤ 0.25. Design §4.6 lists SEPARATES first.
*Fix:* evaluate in the design's order, or state the precedence in §4.6.

---

### What was verified sound (recorded so run 2 need not re-derive it)

- **Frozen inputs.** `seasonal_baselines.parquet` sha256 `1b7244c8…` verified on disk, against INFR-017 report §8, and against the committed `seasonal_baselines_manifest.json::artifact_sha256`. `column_pins.json::pin_sha256` = `e3b9fd9b…`. Discarded `78dd7988…` provably unloadable — `assert_frozen_inputs` re-hashes before use and raises with the reason.
- **GT-1 and GT-2 reproduce exactly** from staging data, including the IB, the first-break-in-time rule on both sides, the excluded break bar, the 8-hourly funding partition, and both normalised excursions.
- **Universe causality** is correct and in the right direction (day D turnover ranks day D+1), on quote turnover with the USDT divisor stated, with eligibility, lexicographic tie-break and delisting all implemented as declared.
- **All bar reads route through the fenced `load_bars`.** No unfenced full-file scan exists — the INFR-017 defect does not recur (subject to I-7's caller-side swallow).
- **No holdout contact anywhere**, and no TEST read attempted. 0 counted reads.
- **HYP-I2's pseudo-anchor destroy satisfies L-28** by construction *and* by assertion, verified across all four candidates and five seeds.
- **The day-clustering unit is genuinely the calendar day**, correctly collapsing A-FUND's three sessions into one resampling unit.
- **Both amendment-ledger entries are accurate**, their stated directions are correct (I re-derived AMENDMENT-1's TIGHTER claim from the mechanism), and the code matches what each says was changed.
- **All 13 mandatory design blocks are present**; the §9/§10/§11 N/A declarations are justified.
- **Appendix B order is preserved and filesystem-enforced**; the provisional pre-A6 Phase-1 break rule is a legitimate reading of the source, not a circularity, because it is applied identically to every cell and every control and is pinned as provisional.

### Routing

- **`experiment-developer`:** I-1, I-2, I-3, I-4, I-5, I-6, I-7, I-8, I-11, I-12, I-13, I-14, I-15, I-16, I-17, I-18, I-19, I-21, I-22, I-23, I-24, I-25, I-26, I-27.
- **`quant-designer`:** I-9 and I-10 (the design text and the code disagree on what D3 and D5–D8 *are*; the design must decide before the code is changed, and the change must be logged with a direction under §11). I-20 and I-28 are design-text clarifications.

QA APPROVE is not granted; execution remains the operator's gate and nothing should be launched on the current tree.

---

## QA run 2 — 2026-07-20T22:15Z — mode: subagent — HEAD 76cf916f842185e519f56070bc9f0cf705038f87

**Reviewed state:** working tree dirty (same family as run 1; uncommitted INFR-018 + `xen.sigbar` apparatus + tests). HEAD unchanged from run 1 (`76cf916f…`). Dirty / untracked of interest: `python/experiments/INFR-018/**`, `python/src/xen/sigbar/{acceptance,classes,fences,profile,sessions}.py`, `python/tests/test_sigbar_infr018.py`, modified `python/src/xen/sigbar/__init__.py`.
**Nothing executed on the full universe.** `results/` holds universe membership/reconciliation only (no race artifact present for re-read). Post-fix smoke claim (collapse ≈ −6.8 with ib_width fixed) treated as operator-supplied evidence, not re-run here.
**Independence:** fresh subagent; run-1 sound list accepted without re-derivation (GT-1/GT-2, frozen hashes, universe causality, L-28 pseudo-anchor, holdout, Appendix B order). All claimed I-1…I-28 fixes re-derived design→code.

**Verdict: REVISE**

Most run-1 structural fixes are real in code. Three residual integrity seams still block APPROVE / freeze: (1) the HYP-I2 future-shift tripwire’s null is still non-zero after the divisor pin (smoke collapse still huge and negative); (2) the HYP-I3 path-swap positive control cannot actually leak into the outcome window; (3) MDE plants are still location-shifts, not the design’s co-designed plants. Freeze *would* refuse a non-collapsing tripwire now — that is progress — but the item still cannot complete a valid freeze.

---

### Design-fidelity trace (material clauses, re-checked)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §2 I3 windows: equal case valid | `acceptance.py:104-112,181,186` | **MATCHES** | Assert is strict `<`; `outcome_start = qualify_end`. |
| §3.5 tripwire: ib_width held fixed | `sessions.py:311-336` | **MATCHES (mechanism pin)** | Width computed before shift; levels only shifted. |
| §3.5 tripwire HARD blocks freeze | `freeze_and_pin.py:120-157,200-201` | **MATCHES (enforcement)** | Refuses if missing / null / \|cf\| > 0.25. |
| §3.5 expected collapse ≈ 0 after pin | smoke residual | **BROKEN (null)** | ib_width fix present; smoke still ≈ −6.8. See I-29. |
| §3.7 spot-check mandatory + divergence | `hyp_i2:264-287`; `freeze_and_pin.py:47-106,203-213` | **MATCHES** | DESIGN always runs spot-check; MATERIAL raises before write. |
| §4.2 D3 volume-weighted median | `acceptance.py:253-290` | **MATCHES** | Sort by tp, cum_v ≥ 0.5·tot_v. |
| §4.2 / AMENDMENT-3 two-leg flow | `acceptance.py:308-354`; `design.md:263,598-609` | **MATCHES** | `(mean ratio_resid)×side > 0` AND `mean abs_resid > 0`. |
| §4.3 both label clauses + poke_extreme | `acceptance.py:357-464` | **MATCHES** | accept before re-entry; trap before beyond-poke. |
| §4.4 derange within calendar-day blocks | `hyp_i3:91-125,331-340` | **MATCHES** | `derange_within_blocks(..., "day")`; singletons counted. |
| §4.4 outcome_path_swap (paths, not labels) | `hyp_i3:139-203,460-485` | **MATCHES (core)** | Donor path re-timed; `label_outcomes` recomputed. |
| §4.4 path-swap positive control | `hyp_i3:487-509`; `acceptance.py:200-207` | **BROKEN** | LEAK-PROBE w=240 is still capped to qualify window. See I-30. |
| §4.6 UNPOWERED first, then SEPARATES…WASH | `hyp_i3:374-398` | **MATCHES** | Order matches design. |
| §5.1 kernel winner DESIGN only | `hyp_i4:245-270` | **MATCHES** | `winner = design_only[…]`; `winner_selected_on: DESIGN`. |
| §5.1 displacement in IB-width + ticks | `profile.py:190-248`; `hyp_i4:209-220` | **MATCHES (named)** | Keys name divisors; residual: grid still relative not tick-multiple. |
| §5.1 per-level Δ barred on real column | `profile.py:70-107` | **MATCHES** | `assert_no_per_level_delta(bars[weight_col])`. |
| §5.2 level families (IB + prior extreme + prior VA/POC) | `hyp_i4:283-368` | **MATCHES** | All three families; prior via frozen kernel. |
| §5.2 level_created_ts for self-exclusion | `sessions.py:306-307`; `hyp_i4:305-317`; `classes.py:232-235` | **MATCHES** | IB edges carry create-ts; null prior levels cannot be self-created in current session. |
| §5.2 residual match on common deciles | `classes.py:257-329` | **MATCHES** | Common edges from `all_bars`; `match_quality` emitted. |
| §5.2 DRY_UP detected, not clustered | `classes.py:32-50,136-207,413-422` | **MATCHES** | Multi-bar detector; counted, not in `LOCATED_CLASSES`. |
| §5.2 abs_high for BLOWOFF | `classes.py:79-90,124-163` | **MATCHES** | Pin records `abs_high`; classify uses it. |
| §0 CALIBRATION_ONLY on I3/I4 absolutes | `hyp_i3:400-434`; `hyp_i4:510-514` | **MATCHES** | Wrapped. |
| §0 band fence re-raise RuntimeError | `common.py:89-100` | **MATCHES** | `RuntimeError` re-raised; other Exception = unreadable. |
| §3.2 session_len per session | `sessions.py:345-354` | **MATCHES** | From `session_end − anchor_ts`. |
| §3.2 INCOMPLETE counted in cell | `sessions.py:356-426`; `hyp_i2:96-120,152` | **PARTIAL** | Counted when any admitted row exists; all-incomplete returns empty frame with no count. |
| §6.2 / §4.4 / §5.2 MDE co-designed plants | `common.py:243-258`; callers | **DEVIATES** | Curves exist all gates; plant is still location-shift. See I-13. |
| §7 `check_no_local_accounting` | `freeze_and_pin.py:283-294` | **MATCHES** | Called on experiment code + `xen.sigbar`. |
| §5.1 trade-archive band assert | `hyp_i4:185-194` | **MATCHES** | `assert_band` on trade timestamps + day span check. |
| §3.7 / I-22 universe_scale + smoke refuse | `hyp_i2:205-210`; `hyp_i3:248-253`; `freeze_and_pin.py:160-181` | **MATCHES (I2/I3)** | I4 registry path still has no smoke-scale refuse. See I-31. |
| §11 AMENDMENT-3 + running count | `design.md:598-619` | **MATCHES** | 0L/2T/1N; final-gate re-derivation present; divisor-fixed called NEUTRAL wording. |
| §4.6 / I-28 band order | `hyp_i3:374-398` | **MATCHES** | UNPOWERED ahead of WASH. |

### Run-1 issue disposition (I-1…I-28)

| ID | Severity (run 1) | Disposition | Evidence |
|---|---|---|---|
| **I-1** | BLOCKER | **FIXED** | `acceptance.py:112` uses `<`; `test_window_equality_is_valid_adjacent_disjoint` pins equality. |
| **I-2** | BLOCKER | **PARTIAL** | Path swap reimplemented (`hyp_i3:139-203`). Positive control still non-leaky — see **I-30**. |
| **I-3** | BLOCKER | **FIXED** | Common quantiles in `residual_matched_control`; `match_quality`; test balances means. |
| **I-4** | BLOCKER | **FIXED** | `ib_high_ts`/`ib_low_ts` from sessions; prior levels shifted causal ≤ t−1; filter can exclude. |
| **I-5** | BLOCKER | **PARTIAL** | Freeze blocks non-collapse (**enforcement FIXED**). ib_width held fixed (**pin FIXED**). Destroy null still ≫ 0 on smoke (**mechanism OPEN** → **I-29**). |
| **I-6** | BLOCKER | **FIXED** | `hyp_i4:254-270` selects from `design_only` only. |
| **I-7** | MAJOR | **FIXED** | `common.py:91-97` re-raises `RuntimeError`. |
| **I-8** | MAJOR | **FIXED** | DESIGN always spot-checks; freeze classifies MATERIAL and raises. |
| **I-9** | MAJOR | **FIXED** | VW median in `acceptance.py:253-290` (no design amendment needed — code matches original §4.2). |
| **I-10** | MAJOR | **FIXED** | AMENDMENT-3 restates two residual legs; code matches (`acceptance.py:342-346`). Direction TIGHTER is correct. |
| **I-11** | MAJOR | **FIXED** | Prior session high/low + POC/VAL/VAH via frozen kernel (`hyp_i4:283-368`). |
| **I-12** | MAJOR | **FIXED** | Within-day derangement (`hyp_i3:91-125,336`). |
| **I-13** | MAJOR | **PARTIAL** | MDE curves now on I2/I3/I4, but all via `mde_curve` location-shift, not design plants (§3.4 synthetic breakout / §4.4 synthetic rule / §5.2 planted distances). |
| **I-14** | MAJOR | **FIXED** (I3) | `UNPOWERED` branch first in I3. I4 still maps \|obs\| < mde → WASH not UNPOWERED (minor residual). |
| **I-15** | MODERATE | **FIXED** | Both clauses + `poke_extreme` consumed; tests pin accept/trap paths. |
| **I-16** | MODERATE | **FIXED** | Real `weight_col` checked; GT-3(d) shape covered by `test_build_profile_rejects_signed_weight_column`. |
| **I-17** | MODERATE | **FIXED** (naming) | IB-width + tick keys; residual: grid is relative (`profile.py:38-47`), not tick-multiple per §5.1. |
| **I-18** | MODERATE | **FIXED** | `check_no_local_accounting` in `build_registry`. |
| **I-19** | MODERATE | **FIXED** | Trade timestamps `assert_band`’d. |
| **I-20** | MODERATE | **FIXED** | DRY_UP multi-bar detector; counted not clustered. |
| **I-21** | MODERATE | **FIXED** | CALIBRATION_ONLY on I3 rates and I4 distances. |
| **I-22** | MODERATE | **FIXED** (I2/I3 freeze) | `universe_scale` + smoke refuse. Residual on I4 → **I-31**. |
| **I-23** | MODERATE | **FIXED** | `n_days_dropped_no_call` emitted (`hyp_i3:359,429`). |
| **I-24** | MINOR | **FIXED** | `block_fragile` on zero-exclusion set (`common.py:233-239`). |
| **I-25** | MINOR | **FIXED** | Per-session `session_len`. |
| **I-26** | MINOR | **FIXED** | `abs_high` pinned and applied. |
| **I-27** | MINOR | **PARTIAL** | Count in cell when admitted rows exist; silent zero when all incomplete (`sessions.py:362-363` empty return). |
| **I-28** | MINOR | **FIXED** | Band order UNPOWERED → SEPARATES → … → WASH. |

### New issues (run 2)

**I-29 — BLOCKER — HYP-I2 future-shift tripwire null still non-zero after ib_width pin.**
- Design §3.5 (post-amendment text) claims that with the normaliser fixed, “the ONLY thing destroyed is the boundary’s causality” and expected collapse ≈ 0.
- Code holds `ib_width` fixed (`sessions.py:314-336`) and freeze refuses \|cf\| > 0.25 (`freeze_and_pin.py:141-147`) — both verified.
- Operator smoke after those changes still reported collapse_fraction ≈ −6.8 on the leading cell. That is **not** “edge collapsed to 0”; it is a large opposite-sign contrast, i.e. the destroyed arm’s null is still far from the design’s expectation.
- So either (a) another construction artifact remains (break/event-set / control pairing under `ib_shift`, session composition, multi-session shift semantics), or (b) the destroy form’s expected null is misspecified and needs a design revision.
- **Consequence:** freeze correctly blocks; the item **cannot** emit a valid `anchor_freeze.json` until this is resolved. Do not interpret the large negative as “tripwire worked.”
- **Required:** diagnose with a controlled synthetic (same paths, shifted levels only, width fixed) and either fix construction so E_shift ≈ 0 under a no-edge plant, or amend §3.5 with a correct null and a bite check that is non-vacuous. Route: `experiment-developer` first; `quant-designer` if the destroy form itself must change.

**I-30 — MAJOR — HYP-I3 path-swap positive control cannot see outcome bars (I-2 incomplete).**
- `hyp_i3:491` plants `Discriminator("LEAK-PROBE", "D4", False, {"tau": 0.5, "w": 240})` claiming the window runs past `qualify_end`.
- `evaluate_discriminator` **always** filters to `[poke_ts, qualify_end)` first (`acceptance.py:200-207`). D4’s `w` is then applied *inside* that already-capped window (`acceptance.py:291-298`). `w=240` is a no-op relative to the 30-minute qualify cap.
- Freeze’s positive-control check (`freeze_and_pin.py:148-156`) therefore validates “a clean D4 collapses under path swap,” which any non-leaky disc should do — **not** “a leaky disc is caught.”
- **Required:** implement a probe that genuinely reads past `qualify_end` (bypass or optional override of the hard qualify filter for the probe only), show high S_raw on true labels and collapse under path swap; keep the real race path capped.

**I-31 — MODERATE — HYP-I4 has no smoke-scale refuse at registry build (I-22 residual).**
- I2/I3 freeze paths call `_assert_full_universe`. `build_registry` loads `hyp_i4_validation_DESIGN.json` with no `universe_scale` / limit check (`freeze_and_pin.py:296-298`, `hyp_i4` never stamps `universe_scale`).
- A `--limit` I4 run can still be pinned into the deliverable.
- **Required:** stamp scale into the I4 artifact; refuse registry build on smoke-scale I4.

**I-32 — MINOR — I4 maps \|contrast\| < MDE to WASH, not UNPOWERED.**
- Design §6.2: class below MDE floor → UNPOWERED (never a negative). `hyp_i4:486-487` uses WASH when mde is finite and \|obs\| < mde.
- **Required:** align label with §6.2 / B-5.

**I-33 — MINOR — `derange_within_blocks` fixed-point rate statistic is wrong.**
- `hyp_i3:122-124`: `moved[np.isin(idx, idx)]` is identity indexing; singleton rows inflate the rate. Derangement itself is correct; disclosure is misleading.
- **Required:** report fixed points only within permutable blocks.

### Golden-trace / sound list

Not re-derived (per run-1 handoff). Spot-check only: GT-3(d) path now raises via real `weight_col` (I-16 FIXED). Window equality test added (I-1 FIXED). Residual-match test added (I-3 FIXED). Label-clause tests added (I-15 FIXED). Tripwire freeze unit test pins refusal on cf=−6.10 (I-5 enforcement FIXED) — does **not** pin mechanism null ≈ 0.

### Governance & boundary

| Check | Evidence |
|---|---|
| Holdout / TEST | No path to ≥ 2025-01-08; TEST untouched; 0 counted reads. |
| Value vs integrity | Value reads remain report layers; tripwire freeze is hard (good). Residual: tripwire null broken (I-29). |
| L-28 | I2 pseudo-anchor OK (run 1). I3 within-day derangement OK. |
| L-23 ledger | AMENDMENT-3 present; 0L/2T/1N; final-gate re-derivation present; no ≥3 one-way streak. |
| L-32 | No `pass` fields; bands are labels; UNPOWERED first in I3. |
| `check_no_local_accounting` | Invoked at registry build. |
| No strategy backtest | Confirmed. |
| Stage I scope | Parameters/instruments only; no expectancy edge claims unwrapped (I-21 fixed). |
| Appendix B order | Filesystem freezes still enforce I2→I3→I4. |

### Routing

- **`experiment-developer`:** **I-29** (blocker), **I-30** (major), I-13 (partial plant form), I-31, I-27 residual, I-32, I-33; finish any incomplete I-5 mechanism work.
- **`quant-designer`:** I-29 if construction proves the destroy form’s null cannot be ≈0; optional I-17 tick-grid vs relative-grid disclosure if SPEC_INCOMPLETE remains the binding constraint.

QA APPROVE is not granted. Do not freeze. Do not launch the full race for keep-and-pin until I-29 is resolved (and I-30 so the I3 tripwire is known to be sensitive).

---

## QA run 3 — 2026-07-20T23:55Z — mode: subagent — HEAD 76cf916f842185e519f56070bc9f0cf705038f87

**Reviewed state:** HEAD re-checked via `.git/refs/heads/main` = `76cf916f842185e519f56070bc9f0cf705038f87` (unchanged from runs 1–2). Working tree still dirty / untracked for the INFR-018 + `xen.sigbar` apparatus: `python/experiments/INFR-018/**`, `python/src/xen/sigbar/{acceptance,classes,fences,profile,sessions}.py`, `python/tests/test_sigbar_infr018.py`, modified `python/src/xen/sigbar/__init__.py`. Full DESIGN race artifact present: `results/hyp_i2_anchor_race_DESIGN.json` (generated_utc 2026-07-20T20:59:42Z).
**Independence:** fresh subagent; no implementation context. Run-1 sound list accepted without re-derivation (GT-1/GT-2, frozen hashes `1b7244c8…` / `e3b9fd9b…`, universe causality, L-28 pseudo-anchor, holdout non-contact, Appendix B order). All claimed post–run-2 fixes re-derived design→code. Full-race tripwire/spot-check/universe fields re-read from the artifact as field evidence only — not as proof of design fidelity.

**Verdict: REVISE**

Post–run-2 code fixes for I-29…I-33 are real and match the amended design text. The HYP-I2 destroy’s non-zero opposite-sign null is no longer a mystery: the full-race shift arm shows `asym_real_median ≈ −4.0` with `collapse_fraction ≈ −41.7` and `day_corr ≈ 0.06`, which is exactly the foreign-IB → fake-break → mean-revert geometry. **AMENDMENT-4’s survival rule is the right null-aware adjudication for this destroy form** — it is not a free pass that ignores same-sign or high day-correlation survival.

What still blocks APPROVE / freeze is not “cf is large.” It is that the hard integrity gate was **respecified after smoke saw the large opposite-sign**, and the new rule still has **no plant proving it catches a leaky construction** (the I-30-class gap, now on I2). Freeze of the present artifact would *mechanically* pass under the current code; QA does not authorise that freeze until the bite and the post-smoke ledger are closed.

---

### Design-fidelity trace (material clauses, re-checked)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3.5 destroy: next-session IB levels; windows fixed; **ib_width fixed** | `sessions.py:311-336` | **MATCHES** | Width computed before `shift(-ib_shift)` on levels only. |
| §3.5 DESTROY NULL (foreign IB → fake break → reverse) | artifact `tripwire_future_shift` + `CALIBRATION_ONLY_shift_arm` | **MATCHES (empirical)** | Full race: `contrast_shifted ≈ −4.17`, shift-arm `asym_real_median ≈ −4.0`, control ≈ −0.037 — mechanical reverse, not “edge collapsed to 0”. |
| §3.5 SURVIVAL := same-sign material \|cf\|>0.25 **OR** \|day_corr\|>0.5 | `hyp_i2:310-334`; `freeze_and_pin.py:123-177` | **MATCHES (rule text)** | Emitter sets `survives`; freeze refuses when `survives` true. Legacy \|cf\| path retained for HYP-I3 (no `survives` field). |
| §3.5 HARD freeze enforcement | `freeze_and_pin.py:220-221` | **MATCHES** | Called before write. |
| §3.5 / AMENDMENT-4 “leak sensitivity not loosened” | plant / freeze re-derive | **DEVIATES (evidence)** | No I2 positive-control plant; freeze trusts precomputed `survives` and does not require `day_corr`. See **I-34**, **I-35**. |
| §11 AMENDMENT-4 ledger: NEUTRAL, 0L/2T/2N, pre-measurement | `design.md:617-634` | **PARTIAL** | Count arithmetic matches. Direction NEUTRAL is *conceptually* right for null-respec vs leak power — but “pre-measurement” is false relative to smoke that produced I-29. See **I-35**. |
| §3.7 spot-check mandatory + MATERIAL/COSMETIC | `hyp_i2:339-362`; `freeze_and_pin.py:47-106,223-233` | **MATCHES** | DESIGN always emits spot table; freeze classifies. Re-derived on artifact: pooled winner A-USOPEN/L=15; SOL weak/negative only → **COSMETIC** (not ≥2 instruments). |
| §3.7 / I-22 universe_scale + smoke refuse | `hyp_i2:206-210`; artifact `universe_scale`; `freeze_and_pin.py:180-201` | **MATCHES** | Artifact: `limit: null`, `n_symbols_selected: 140`, `n_days: 609`. Freeze refuses smoke. |
| §4.4 leak probe past qualify_end (I-30) | `acceptance.py:190-229`; `hyp_i3:449-518` | **MATCHES** | Default `read_past_qualify=False`; LEAK-PROBE calls with `True` so D4 `w=240` can reach outcome bars. Real race path stays capped. **No unit test** for the flag. |
| §4.4 derangement fixed_point_rate (I-33) | `hyp_i3:109-131` | **MATCHES** | Rate only over `n_permutable` (block size ≥2); singletons counted separately. |
| §4.6 / I-32 I4 UNPOWERED when \|obs\| < MDE | `hyp_i4:484-494` | **MATCHES** | UNPOWERED before WASH/CLUSTERS. |
| §5 / I-31 I4 universe_scale + registry refuse | `hyp_i4:540-568`; `freeze_and_pin.py:321-322` | **MATCHES** | Stamped; `_assert_full_universe(i4)` at registry build. |
| §3.4 / §4.4 / §5.2 co-designed MDE plants | `common.py:243-258` | **DEVIATES** | Still location-shift on realised statistic. **I-13 STILL OPEN.** |
| §4.4 I3 path-swap + positive control freeze | `hyp_i3:145-203,468-518`; `freeze_and_pin.py:168-176` | **MATCHES (code)** | Path swap + probe collapse required when `positive_control` present. |
| §7 check_no_local_accounting | `freeze_and_pin.py:307-314` | **MATCHES** | Experiment code + `xen.sigbar`. |
| §0 / band fences / holdout | run-1 sound + `common.py` RuntimeError re-raise | **MATCHES** (not re-broken) | |

### Attack on AMENDMENT-4 (binding question)

**Is SURVIVAL a correct validity gate, or a LOOSER that lets leaks freeze through?**

| Attack | Finding |
|---|---|
| Non-zero null is real geometry, not a construction bug | **Supported.** With width fixed, shift-arm absolute asymmetry is still ≈ −4 IB-widths (full race). Foreign absolute levels produce immediate “breaks” and mean-reversion. Demanding \|cf\|≈0 permanently false-refuses a causal construction. |
| Same-sign material \|cf\|>0.25 | **Correct leak leg.** If raw already used future IB levels, raw ≈ shifted → same sign, large \|cf\| → `survives=True` → freeze blocks. |
| \|day_corr\|>0.5 | **Correct complementary leg.** Full race `day_corr ≈ 0.06` under a clean opposite-sign null: day patterns are nearly orthogonal, not preserved. A boundary leak that preserves day structure would elevate this. |
| Thresholds 0.25 / 0.5 | **Pre-registered only in the post-I-29 amendment text.** 0.25 recycles the old collapse constant; 0.5 for day_corr is new and was not sealed before the first tripwire emission on real bars. |
| Direction NEUTRAL vs LOOSER | **NEUTRAL vs true leak power is plausible; LOOSER vs the previous freeze rule is certain.** Old rule blocked every large \|cf\| (including the destroy null). New rule intentionally allows opposite-sign + low day_corr. That is the right null correction *if* leak catch-rate is preserved — which is not machine-proven. |
| Positive-control story for I2 | **Incomplete.** HYP-I3 has LEAK-PROBE + freeze refusal if the probe fails. HYP-I2 has **no** planted construction that must set `survives=True`. Tests only assert freeze respects a hand-built `survives` flag (`test_tripwire_blocks_freeze_on_survival_not_opposite_null`). |
| Can a leaky construction still freeze? | **Yes, under soft freeze enforcement:** (1) if `day_corr` computation fails (`except Exception` → `day_corr=None`), survival reduces to same-sign only — opposite-sign leak-like patterns pass; (2) freeze does **not** re-derive survival from `collapse_fraction` / `day_contrast_correlation` / `same_sign_material` — it trusts `survives`. A buggy emitter that always writes `survives: false` freezes through. |
| Full-race artifact under the rule | Fields complete: `survives: false`, `same_sign_material: false`, `day_corr: 0.060…`, `day_corr_error: null`, ranked #1 A-USOPEN L=15 contrast ≈ +0.100. **Would pass** `_assert_tripwire` + `_assert_full_universe` + COSMETIC spot-check as code stands. |

**Bottom line:** AMENDMENT-4 is **not** a casual LOOSER of leak detection; the null story is sound and empirically confirmed. It **is** an under-evidenced respec of a HARD gate (post-smoke, no bite plant, freeze soft on the correlation leg). That is enough for REVISE, not REJECT.

---

### Disposition table (I-1…I-35)

| ID | Run-2 state | Run-3 disposition | Evidence (file:line) |
|---|---|---|---|
| I-1 | FIXED | **FIXED** | `acceptance.py` strict `<`; equality test present (run 2). |
| I-2 | PARTIAL→I-30 | **FIXED** (via I-30) | Path swap + `read_past_qualify` probe. |
| I-3…I-4, I-6…I-12, I-14…I-26, I-28 | FIXED (run 2) | **FIXED** (no regression spotted) | Not re-broken in this pass. |
| I-5 | PARTIAL→I-29 | **FIXED** (enforcement + null-aware rule) | `freeze_and_pin.py:123-177`; residual bite → I-34. |
| I-13 | PARTIAL | **STILL OPEN (PARTIAL)** | `common.py:243-258` location-shift only; not co-designed plants in §3.4/§4.4/§5.2. |
| I-27 | PARTIAL | **PARTIAL** | Counted when admitted rows exist (`sessions.py:356-426`, `hyp_i2:96-120`); empty return still silent (`sessions.py:362-363`). |
| I-29 | BLOCKER | **FIXED** (adjudication) | Design §3.5 + AMENDMENT-4; `hyp_i2:310-334`; full-race null geometry confirms. Ledger/bite residuals → I-34/I-35. |
| I-30 | MAJOR | **FIXED** | `acceptance.py:195-229`; `hyp_i3:506-517`. Residual: no test pins `read_past_qualify`. |
| I-31 | MODERATE | **FIXED** | `hyp_i4:540-568`; `freeze_and_pin.py:321-322`. |
| I-32 | MINOR | **FIXED** | `hyp_i4:484-494` UNPOWERED when `mde is None or abs(obs) < mde`. |
| I-33 | MINOR | **FIXED** | `hyp_i3:121-131` `fixed_point_rate_within_permutable`. |
| **I-34** | — | **NEW MAJOR** | No I2 tripwire positive control / bite plant; freeze trusts `survives` and allows `day_corr is None`. See Issues. |
| **I-35** | — | **NEW MAJOR** | AMENDMENT-4 is post-smoke respec of a HARD gate; design claims pre-measurement. See Issues. |

### Golden-trace / sound list

Not re-derived (per run-1 handoff). Spot checks only: freeze unit test now pins survival adjudication (opposite-sign null accepted; same-sign survival refused; legacy I3 \|cf\| path). Full-race tripwire fields consistent with emitter logic. Spot-check COSMETIC re-derived for SOL-weak case.

### Governance & boundary

| Check | Evidence |
|---|---|
| Holdout / TEST | No path ≥ 2025-01-08; TEST untouched; 0 counted reads. |
| L-28 | I2 pseudo-anchor OK; I3 within-day derangement OK; fixed-point rate disclosure fixed (I-33). |
| L-23 ledger | Running count 0L/2T/2N as written. **I-35:** AMENDMENT-4’s “pre-measurement” claim is false relative to smoke that motivated it; operator ratification required. No ≥3 one-way streak. |
| L-32 | Value reads remain report layers; bands are labels; no auto-drop of candidates. |
| Hard vs informative | Tripwires hard in code; MDE/bands report. Residual: I2 bite incomplete (I-34). |
| `check_no_local_accounting` | Invoked at registry build. |
| No strategy backtest | Confirmed. |
| Stage I scope | Parameters/instruments only; absolute levels under CALIBRATION_ONLY. |
| Appendix B order | Filesystem freezes still enforce I2→I3→I4. |
| Full-race freeze *mechanical* readiness | universe_scale PASS; tripwire `survives=false` PASS under AMENDMENT-4; spot-check COSMETIC PASS — **QA still refuses authorisation** until I-34/I-35 closed. |

### Issues (run 3)

**I-34 — MAJOR — HYP-I2 survival gate has no bite plant; freeze enforcement is softer than the ledger claims.**

- Design/AMENDMENT-4 claims leak sensitivity is not loosened: survival still catches constructions that keep the same day-contrast pattern under the destroy.
- Code implements the boolean (`hyp_i2_anchor_race.py:310-334`) and freeze refuses when `survives` is true (`freeze_and_pin.py:148-157`).
- **Missing:** a planted leaky construction (e.g. force raw arm to use `ib_shift=1` levels while claiming to be causal) that must yield `survives=True` and block freeze. Without that plant, the NEUTRAL claim is assertion.
- **Soft freeze path:** (a) `hyp_i2:304-308` swallows day-corr errors → `day_corr=None` → correlation leg off; (b) freeze does not re-derive survival from primitives and does not require `day_corr is not None` when `"survives" in tw`.
- HYP-I3 already has the symmetric positive-control requirement (`freeze_and_pin.py:168-176`); I2 does not.
- *Required:* (1) plant + unit test that a future-IB “raw” arm sets `survives=True`; (2) freeze re-derives survival from `collapse_fraction` / signs / `day_contrast_correlation` and refuses if `day_corr` is null under the survival adjudicator. Route: **experiment-developer**.

**I-35 — MAJOR — AMENDMENT-4 is a post-smoke respec of a HARD tripwire, mis-labelled pre-measurement.**

- Timeline: smoke collapse ≈ −6.8 after ib_width pin (run 2 I-29) → design §3.5 rewritten to survival → full race freezes-through under the new rule.
- Design §11 states amendments are “pre-measurement — before any gate was run on real data.” Smoke on real DESIGN bars **is** a gate read of the tripwire object.
- Survival thresholds (|cf|>0.25 same-sign; |day_corr|>0.5) were not sealed before the first real tripwire emission; they were chosen knowing the observed null is large opposite-sign with low day correlation.
- Mechanism diagnosis remains valid (I-29 FIXED on substance). The process defect is goalpost timing on a HARD integrity gate.
- *Required:* operator explicitly ratifies AMENDMENT-4 as a post-smoke hard-gate respec (direction NEUTRAL OK once ratified), **or** seal thresholds independently and re-run the race under a frozen adjudication. Route: **operator** (+ quant-designer if thresholds need independent pre-registration language).

**I-13 — MAJOR residual (unchanged class) — MDE plants still location-shifts.**

- Still `values - median + s` (`common.py:253`), not synthetic breakout / synthetic rule / planted distances.
- Does not block HYP-I2 freeze integrity; blocks power-honesty claims (WASH vs UNPOWERED) for later gates. Route: **experiment-developer**.

**I-27 — MINOR residual — all-incomplete path still silent.** Unchanged.

### Routing

- **`experiment-developer`:** **I-34** (required for APPROVE); I-13 residual; I-27 residual; add `read_past_qualify` unit test under I-30.
- **`operator` (+ quant-designer note):** **I-35** — ratify post-smoke AMENDMENT-4 or re-seal and re-run.
- **Not routed for redesign of the survival rule itself:** the foreign-IB null geometry is accepted; do not revert to \|cf\|≈0.

### Freeze authorisation

**`freeze_and_pin.py anchor` is NOT authorised under this verdict (REVISE).**

What still blocks freeze (QA gate, not mechanical code crash):
1. **I-34** — no proof the survival rule bites a leaky I2 construction; freeze must re-derive / require `day_corr`.
2. **I-35** — operator ratification of post-smoke hard-gate respec (or sealed re-run).

Mechanical note (not a green light): the present full-race artifact would pass the *current* freeze checks (full universe, `survives=false`, COSMETIC spot-check). That is why I-34/I-35 matter — without them the item would pin under a rule that has not been shown to catch leaks and was adjusted after seeing the null.

QA APPROVE is not granted. Do not freeze. Do not launch HYP-I3/I4 freezes.

---

## QA run 4 — 2026-07-20T23:55Z — mode: subagent — HEAD 76cf916f842185e519f56070bc9f0cf705038f87

**Reviewed state:** `refs/heads/main` = `76cf916f…` (unchanged since run 1). Working tree still carries uncommitted INFR-018 implementation (`python/experiments/INFR-018/`, `python/src/xen/sigbar/*`, `python/tests/test_sigbar_infr018.py`). No freezes or races launched. Full-race artifact on disk is **PRE–I-34** (no `positive_control`).

**Independence:** fresh subagent; no implementation context. Claimed post–run-3 fixes re-derived design→code. Prior FIXED dispositions (I-1…I-33 except residuals) not re-opened unless this pass re-broke them.

**Verdict: REVISE**

Most of the I-34 *machinery* is real: shared `adjudicate_i2_survival`, freeze re-derives survival, null `day_corr` raises, lying `survives` is caught, unit tests cover the adjudicator under the string `"HYP-I2"`. I-35 is closed on the design record (TIMING + operator date). **The freeze still has a soft path:** the live call site never hits the plant-required branch, so the pre–I-34 full-race JSON would still pin. That is enough to refuse APPROVE and freeze authorisation.

---

### Design-fidelity trace (I-34 / I-35 / freeze path)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3.5 SURVIVAL := same-sign \|cf\|>0.25 OR \|day_corr\|>0.5 | `common.py:272-316` | **MATCHES** | Shared adjudicator; thresholds 0.25 / 0.5. |
| §3.5 freeze RE-DERIVES survival; finite day_corr required | `freeze_and_pin.py:123-137,161-177` | **MATCHES (logic)** | `ValueError` on null/non-finite day_corr → freeze RuntimeError. Disagreement with emitter `survives` refused. |
| §3.5 POSITIVE CONTROL required (raw ib_shift=1, destroy=2; must SURVIVE) | `hyp_i2:309-359` emitter; `freeze_and_pin.py:187-215` | **DEVIATES (enforcement)** | Emitter builds plant correctly. Freeze *requires* plant only when `name == "HYP-I2"`, but `freeze_anchor` calls `_assert_tripwire(..., "HYP-I2 future_shift")` (**line 268**). Production name never equals `"HYP-I2"` → missing plant is a free pass. See **I-36**. |
| §3.5 plant has bite on real geometry (not only unit numbers) | mechanism + full-race shift arm | **MATCHES (mechanism)** | Full race: shift-1 arm ≈ −4.17 (foreign IB → fake break → reverse). Shift-2 is the same class of foreign level. Plant raw=shift1 vs destroy=shift2 ⇒ same-sign large \|cf\| under the adjudicator → SURVIVES by construction. Unit-test numbers are illustrative; bite does not depend on them. |
| §3.5 HARD freeze before write | `freeze_and_pin.py:268` | **MATCHES (called)** | Called; plant branch dead (I-36). |
| AMENDMENT-4 TIMING / I-35 post-smoke operator ratification | `design.md:622-637` | **MATCHES** | Explicit **post-smoke**, NEUTRAL, thresholds sealed, operator-ratified 2026-07-20; full DESIGN admissible once I-34 plant present. |
| §11 preamble “All amendments … pre-measurement” | `design.md:578-579` | **PARTIAL residual** | Global sentence still claims all amendments pre-measurement; AMENDMENT-4 TIMING correctly overrides for that row. Not a freeze blocker. |
| AMENDMENT-4a ledger TIGHTER; 0L/3T/2N | `design.md:639-652` | **MATCHES (text)** | Count arithmetic OK; no LOOSER; no ≥3 one-way streak. Enforcement claim overstated until I-36 fixed. |
| HYP-I3 freeze path not forced through I2 survival | `freeze_and_pin.py:318`; I3 tripwire lacks `survives`/`day_corr`/`adjudication_kind` | **MATCHES** | `use_i2` false → magnitude collapse path; I3 plant uses collapse check when present. |
| Stale full-race artifact blocked (missing `positive_control`) | artifact has no `positive_control` (grep empty); freeze name bug | **DEVIATES** | **Would NOT refuse.** Attack Q5 fails. |
| I-13 MDE co-designed plants | `common.py:243-253` | **STILL OPEN** | Still `values - median + s`. |
| Unit tests I-34 | `test_sigbar_infr018.py:569-688` | **MATCHES (lab)** | Null day_corr, missing plant, insensitive plant, lying flag, EDGE SURVIVED, opposite-sign null, I3 legacy — all under **`name="HYP-I2"`**, never under production `"HYP-I2 future_shift"`. Tests green-wash the name bug. |

### Golden-trace / attack answers (binding)

| Attack question | Answer |
|---|---|
| Does freeze still trust a soft path? | **Yes.** (1) **Plant-required branch never runs** on `freeze_anchor` because name is `"HYP-I2 future_shift"` not `"HYP-I2"`. (2) Real-arm survival is re-derived (good) via field heuristics (`survives`+`day_corr` or `adjudication_kind`), so lying `survives` / null day_corr on the real arm are closed when those fields exist. Soft path is specifically **missing plant** (and any future omission of plant). |
| Leak plant (shift 1 vs 2) bite on real geometry? | **Yes, by mechanism.** Same foreign-IB reverse geometry already measured on shift-1 in the full race (cf ≈ −41.7). A further shift keeps the same non-causal class → same-sign material survival expected. Not smoke-re-verified this run; mechanism is sufficient. |
| I-35 ratification recorded? | **Yes.** TIMING block labels post-smoke, NEUTRAL, sealed thresholds, operator date 2026-07-20. Not still pure pre-measurement for AMENDMENT-4. Preamble residual only. |
| HYP-I3 freeze without false I2 requirements? | **Yes.** Name `"HYP-I3 outcome_path_swap"`; no I2 survival fields → magnitude path; plant require gated on `name == "HYP-I2"` only. |
| Stale full-race artifact correctly blocked? | **No.** Missing `positive_control` does not raise under the live call site. Artifact would still pass re-derived non-survival + full universe + COSMETIC spot-check. |

### Disposition table (focus)

| ID | Run-3 state | Run-4 disposition | Evidence |
|---|---|---|---|
| I-29 | FIXED | **FIXED** (held) | Survival null story + adjudicator. |
| I-34 | NEW MAJOR | **PARTIAL** | Adjudicator + re-derive + day_corr mandatory + emitter plant + lab tests **FIXED**. Production plant *requirement* **NOT FIXED** → **I-36**. |
| I-35 | NEW MAJOR | **FIXED** | `design.md:632-637` TIMING / operator-ratified post-smoke. Residual preamble `578-579` non-blocking. |
| I-13 | STILL OPEN | **STILL OPEN** | Location-shift MDE only. |
| I-27 | PARTIAL | **PARTIAL** (not re-probed) | Empty incomplete path residual. |
| **I-36** | — | **NEW MAJOR** | Freeze plant gate name mismatch: live `"HYP-I2 future_shift"` vs required exact `"HYP-I2"`. |

### Governance & boundary

| Check | Evidence |
|---|---|
| Holdout / TEST / 0 counted reads | Not re-broken; Stage I parameters only; value reads report layers. |
| L-23 ledger | 0 LOOSER / 3 TIGHTER / 2 NEUTRAL as written. AMENDMENT-4 NEUTRAL (operator-ratified). 4a TIGHTER intent OK; **not delivered on freeze path until I-36 fixed**. |
| L-28 derangement | I2 shift not permutation; I3 path-swap derangement held from prior runs. |
| Hard vs informative | Tripwires intended hard; I2 plant hard-gate bypassed in production. |
| No strategy / no local accounting | Unchanged; registry still runs `check_no_local_accounting`. |
| Full-race freeze *mechanical* readiness | **Still freezes through without plant** under current code — regression vs claimed I-34 close. |

### Issues (run 4)

**I-36 — MAJOR — HYP-I2 plant requirement is dead on the real freeze call site (I-34 enforcement incomplete).**

- Design §3.5 / AMENDMENT-4a: freeze must refuse without a surviving `i2_leak_plant` positive control.
- Code that *looks* right: `freeze_and_pin.py:188-193` raises if `name == "HYP-I2" and probe is None`.
- Live call: `freeze_and_pin.py:268` → `_assert_tripwire(..., "HYP-I2 future_shift")`.
- `"HYP-I2 future_shift" == "HYP-I2"` is **False** → missing plant never raises.
- Same exact-equality appears in `use_i2` (`line 156`); production currently reaches I2 adjudication only via field heuristics (`survives`+`day_corr` on the pre–I-34 artifact, or `adjudication_kind` on the new emitter). That is accidental coupling, not a named-gate contract.
- Tests only pass `"HYP-I2"` (`test_sigbar_infr018.py:612+`) — they do not exercise the production name string.
- On-disk `results/hyp_i2_anchor_race_DESIGN.json` has **no** `positive_control` and would **freeze under current code**.
- *Required:* (1) match production names (`name.startswith("HYP-I2")` / structured gate id / pass `"HYP-I2"` and put detail elsewhere); (2) unit test that `_assert_tripwire(tw_without_plant, "HYP-I2 future_shift")` raises; (3) re-run DESIGN so the artifact carries the plant field; freeze then re-derives plant survival. Route: **experiment-developer**.

**I-34 — MAJOR residual closed only after I-36.** Adjudicator/re-derive/day_corr work; bite *requirement* does not fire until I-36 is fixed. Do not claim I-34 FIXED in isolation.

**I-35 — FIXED.** Post-smoke TIMING + operator ratification present. Optional cleanup: §11 preamble should not claim universal pre-measurement.

**I-13 — STILL OPEN (MAJOR residual class, not freeze-blocking for HYP-I2 integrity).** MDE plants remain location-shifts.

### Routing

- **`experiment-developer`:** **I-36** (required for APPROVE / freeze). Then DESIGN re-run for plant-bearing artifact. Optional: I-13; test production name string; I-30 residual unit test for `read_past_qualify`.
- **Not routed:** I-35 (closed). Survival rule itself (still accepted). Revert to \|cf\|≈0 (still wrong null).

### Freeze authorisation

**`freeze_and_pin.py anchor` is NOT authorised (REVISE).**

| Question | Answer |
|---|---|
| Authorised to freeze now? | **No.** |
| DESIGN re-run required before freeze? | **Yes** — current artifact lacks `positive_control` / `adjudication_kind` / I-34 plant. Even after I-36 code fix, freeze must refuse this file until re-run. |
| After I-36 fix only, without re-run? | Freeze should hard-refuse missing plant (desired). Still not a pin. |
| After I-36 + DESIGN re-run with plant SURVIVES + real arm non-survival? | Then re-request QA (or operator gate) before freeze. |

QA APPROVE is not granted. Do not freeze. Do not launch races from this review.

---

## QA run 5 — 2026-07-20T22:45Z — mode: subagent — HEAD `76cf916f`
Verdict: **REVISE**

**Reviewed state:** `refs/heads/main` = `76cf916f…` (unchanged since run 1). Working tree carries
the uncommitted INFR-018 implementation (`python/experiments/INFR-018/`, `python/src/xen/sigbar/*`,
`python/tests/test_sigbar_infr018.py`). No freeze, no pin launched by this review.

**Scope of this run (per orchestrator brief):** I-36 fix; I-34 bite on the live path; I-35
AMENDMENT-4 TIMING; and first review of the post-run-4 performance refactor of
`code/hyp_i2_anchor_race.py` (`code/PERF-NOTE.md`). Run 1's "verified sound" ground (hashes,
ground truth, universe causality, L-28 fixed-point freedom, holdout safety) was not re-derived
except where the refactor could have disturbed it.

**Headline:** the HYP-I2 gate is now genuinely armed — I-36 is fixed on the production call
path and I verified the freeze refuses every stripped/toothless/null plant I could construct.
The performance refactor is numerically neutral; I proved it two independent ways. The item
still does not pass, for two reasons that have nothing to do with the refactor: the HYP-I3
freeze path carries the *same* unwired-requirement defect I-36 named (`is_i3_gate` is computed
and never used), and the deliverable registry as coded is materially thinner than design §9 —
including dropping the winner's interval and MDE, which is the one thing a reader needs, since
every A-USOPEN cell's contrast sits below its own MDE.

### Design-fidelity trace (this run's scope)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §3.5 POSITIVE CONTROL required (raw `ib_shift=1`, destroy `ib_shift=2`, MUST survive) | `hyp_i2_anchor_race.py:514-528,549-562` emitter; `freeze_and_pin.py:157,192-219` | **MATCHES** | `name.startswith("HYP-I2")` fires on the live string `"HYP-I2 future_shift"`. Plant required, re-derived, insensitive plant refused. **I-36 CLOSED.** |
| §3.5 freeze re-derives SURVIVAL from primitives; `day_corr` mandatory + finite | `common.py:272-316`; `freeze_and_pin.py:123-181` | **MATCHES** | Single shared adjudicator; emitter and freeze call the same function; a lying `survives` is caught by the disagreement check. **I-34 CLOSED.** |
| §3.5 destroy holds `ib_width` fixed (divisor pinned) | `sessions.py:314,316-336` | **MATCHES** | Only `ib_high`/`ib_low` shift; `ib_width` computed before the shift. |
| §3.4 control = 30 stratified pseudo-anchors, ≥60 min from the controlled anchor, regenerable | `sessions.py:120-188`; `hyp_i2:408-418` | **MATCHES** | All four control ensembles regenerate byte-identically from the frozen seeds; `fixed_points: 0`; `assert_no_fixed_points` passes (L-28). Seed-uniqueness caveat → **I-42**. |
| §11 AMENDMENT-4 TIMING, operator-ratified, post-smoke, NEUTRAL | `design.md:632-637` | **MATCHES** | Dated 2026-07-20, explicitly `**post-smoke**`, thresholds sealed. **I-35 CLOSED.** Preamble residual → **I-40**. |
| §11 AMENDMENT-4a direction/count (0L/3T/2N, no ≥3 streak) | `design.md:639-652` | **MATCHES (arithmetic)** | Count correct; max consecutive same-direction run = 1. Timing note absent → **I-40**. |
| PERF-NOTE claim: refactor changes no number | `hyp_i2_anchor_race.py:74-91,108-155,256-361,458-482` | **MATCHES (verified twice)** | See "Refactor audit" below. |
| §9 registry `anchor` block = full 12-cell table (E, control level, collapse fraction, stability) | `freeze_and_pin.py:394-406` | **DEVIATES** | `design_table = race["ranked"]` → `{anchor_id, ib_minutes, contrast_median}` only. No control level, no collapse fraction, no per-cell stability, no CI, no MDE. → **I-38**. |
| §9 / §6.1 `universe` block = rule + membership hash + churn + count + 200-vs-197 | `freeze_and_pin.py:429`; `common.py:108-128` | **DEVIATES** | No membership hash, no churn rate anywhere in the item. → **I-38(b)**. |
| §9 `scope_limits` = every UNPOWERED stratum | `freeze_and_pin.py:446-448` | **DEVIATES** | Pointer text ("see each gate artifact's power block"), not the §6.2 pre-declared list. → **I-38(c)**. |
| §4.4 HYP-I3 tripwire positive control (leaky disc must collapse) | `hyp_i3_a6_race.py:495-519` emitter; `freeze_and_pin.py:158,191-227` | **DEVIATES (enforcement)** | Emitter builds it; `is_i3_gate` is computed and **never used**, so freeze accepts an I3 tripwire with no `positive_control` at all. Same shape as I-36. → **I-37**. |
| §3.2 INCOMPLETE sessions counted, never silently dropped | `hyp_i2:134-138`; `sessions.py:356,426` | **PARTIAL** | Counted, but over a different population than `n_real_sessions` (→ **I-39**); all-incomplete empty-frame path still silent (I-27, unchanged). |
| §3.4 bite/MDE = co-designed plant (inject drift `s·IB_width` at the true anchor) | `common.py:243-258` | **DEVIATES** | Still `values − median + s` on the realised day series. **I-13 STILL OPEN** — and now load-bearing, since the winner sits below the MDE this approximation reports. |

### Refactor audit (PERF-NOTE claims, attacked)

| Claim | How I tested it | Result |
|---|---|---|
| Whole refactor is numerically neutral | Leaf-diff of the current full-scale `hyp_i2_anchor_race_DESIGN.json` against the archived **pre-refactor, pre-I-34** full-scale artifact (`<scratchpad>/pre_i34_archive/`, generated 20:59:42Z, matching the artifact run 4 reviewed) | **4 differing leaves total**, all I-34 additions: `adjudication` text, `adjudication_kind`, `positive_control` (new), `day_corr_error` (removed). Every `cells`, `ranked`, `spot_check`, `controls`, `universe`, `universe_scale`, `multiplicity`, `frozen_inputs` value and every tripwire numeric (`contrast_raw`, `contrast_shifted`, `collapse_fraction`, `day_contrast_correlation`, `survives`, `shifted_ci`, `CALIBRATION_ONLY_shift_arm`) **identical**. |
| `--workers` cannot move a number | Independent 12-symbol reproduction (`--limit 60`) at `--workers 1` and `--workers 10`, written to scratchpad, full leaf-diff | **Identical** — 2 reported leaves are `NaN != NaN` on the same field, same value (see I-44). |
| **Anchor cache key is safe** (the flagged high-risk line) | Enumerated all 124 specs (4 candidates + 4×30 pseudos). `PSEUDO-1x-00` is genuinely reused across the three daily anchors at offsets **76 / 18 / 19** | **SAFE.** Key is the whole frozen `AnchorSpec`; `__eq__`/`__hash__` include `minutes_of_day`, so the three are distinct entries (`hash(a)==hash(b)` → False). `anchor_table` never reads `anchor_id` (verified by source and by building a table under a fabricated id — frame-equal), so identical minutes ⇒ identical table regardless of id. Zero key collisions producing different tables. |
| Control arm reuse across `ib_shift` is sound | Source: `hyp_i2:147` calls `_sessions_for(bars, cspec, L, band)` with no `ib_shift`; `session_breaks` applies the shift only at `sessions.py:316-336` | **SOUND**, and independently confirmed: the pre-refactor code rebuilt the control per shift and produced identical `contrast_shifted` / `collapse_fraction` / `day_contrast_correlation` / `shifted_ci`. |
| Reduced column set drops nothing downstream | `sessions.py` references exactly `OpenTime/High/Low/Close` among bar columns; race consumes only `day/asym/break_ts/symbol` | **SOUND.** `load_bars` sorts by `OpenTime` in the lazy plan, so the `set_sorted()` flag is truthful (a false flag here would silently disable the `attach_sessions` sort — it is not false). `hyp_i3`/`hyp_i4` build their own frames and are untouched. |
| Ordering/chunking cannot move a number | `tasks` is symbol-major; `chunksize=len(jobs)` = exactly one symbol's job list; `Executor.map` preserves input order; every cell statistic is median/min/max/count/first-by-sort | **SOUND.** Free cross-check: the tripwire re-runs job `(winner, L, 0)` in a second `run_jobs` call and reproduces the race cell's contrast to all 17 digits (`0.09996560808347366`). |
| `n_incomplete_sessions` accumulated over the same symbol set | Serial (`run_cell:239-250`) and parallel (`_worker_job:304-306`) both skip only symbols absent from membership; `run_jobs:352` accumulates `n_inc` even when the symbol's admitted rows are zero | **CONSISTENT** across paths, and identical to the pre-refactor artifact. Its *scope* is nonetheless wrong → **I-39**. |
| `xen.sigbar` untouched | `git status` shows only `sigbar/__init__.py` modified plus the five new untracked modules, all pre-dating the refactor (mtimes ≤ 22:33 vs `hyp_i2` 23:07) | **CONFIRMED.** |

### Freeze-gate behaviour on the artifact now on disk (dry-run, sub-functions only — nothing written)

| Probe | Result |
|---|---|
| `_assert_full_universe` on the real artifact (limit `null`, 140 symbols, 609 days) | **PASS** |
| `_assert_tripwire(tw, "HYP-I2 future_shift")` as emitted (cf −41.72, day_corr 0.060, `survives false`; plant cf 0.703, day_corr 0.708, `survives true`) | **PASS** |
| `_spot_check_divergence` | **COSMETIC** (1 of 3 below local median, 1 of 3 locally negative — SOL) |
| plant key deleted | **REFUSE** — "positive_control leak plant is REQUIRED" |
| plant = `null` | **REFUSE** — same |
| plant = `{"kind": "i2_leak_plant"}` (no primitives) | **REFUSE** — "leak plant is incomplete" |
| plant mutated to genuinely NOT survive (opposite sign, cf −0.024, day_corr 0.05) | **REFUSE** — "POSITIVE CONTROL … did NOT survive … gate is insensitive" |
| plant `kind` renamed + `day_contrast_correlation` removed (falls to legacy cf branch) | **REFUSE** — "did not collapse (0.703)" |
| real arm `day_contrast_correlation` forced to 0.9 | **REFUSE** — "emitter survives=False disagrees with re-derived survives=True" |
| real arm `day_contrast_correlation = null` | **REFUSE** — "day_contrast_correlation is required" |
| real arm `collapse_fraction = null` | **REFUSE** |
| `status: COULD_NOT_RUN` | **REFUSE** |
| `adjudication_kind` renamed (production name kept) | **PASS** (correct — the name drives the branch) |
| `universe_scale.limit = 60` / `n_symbols_selected = 19` | **REFUSE** both |
| my own 12-symbol smoke artifact | **REFUSE** — "produced with --limit 60 (a smoke run)" |
| **I3-shaped tripwire with NO `positive_control`** (`"HYP-I3 outcome_path_swap"`) | **PASS — this is the defect. See I-37.** |

### Golden-trace / internal-consistency checks

- Tripwire `contrast_raw` (`0.09996560808347366`) is bit-identical to `ranked[0].contrast_median`,
  reproduced through a second independent `run_jobs` dispatch. Determinism confirmed.
- All four control blocks in the artifact regenerate exactly from `SEED_PSEUDO_DAILY`/`SEED_PSEUDO_FUND`
  + `pseudo_offsets` (A-UTC0 `20180101`, A-USOPEN `20180103`, A-FUND/A-EUOPEN `20180104`); 30 clocks each;
  `fixed_points: 0`.
- Universe reconciliation: 904 staged files scanned, 200 with DESIGN-band bars, 197 admitted,
  3 named non-admitted (`BTTUSDT`, `COCOSUSDT`, `RAYUSDT`), 0 unreadable, 140 distinct symbols
  ever in the panel over 609 days. Reconciles with the checkpoint's 200-vs-197.
- Power read across the 12 cells (report layer): the winner A-USOPEN/15 has `contrast_median`
  **0.0999**, `contrast_ci` **[−0.282, +0.444]** (does not exclude zero, not block-fragile) and
  **MDE 0.50**. A-USOPEN/30 → 0.0971 vs MDE 0.20; A-USOPEN/60 → 0.0938 vs MDE 0.15. Every
  candidate contrast is below the MDE reported for its own cell. This does not block the freeze —
  §3.3's selection rule is "highest paired contrast", stability reported and never re-ranking, and
  Stage I must pick a parameter. It is why **I-38** matters: the pin as coded carries the ranking
  and drops the interval and the MDE.

### Governance & boundary

| Check | Evidence |
|---|---|
| Fresh context | Subagent; did not produce the implementation. |
| Holdout | `BANDS` has DESIGN/CONFIRM only; `assert_band` raises on `≥ HOLDOUT_START` (2025-01-08) and on `≥ band_end`; every read goes through `load_bars`. Never queried. |
| TEST band | No TEST entry exists; 0 counted reads. |
| Frozen inputs | `assert_frozen_inputs` re-hashes at every entry point; artifact carries baselines `1b7244c8…`, column pin `e3b9fd9b…`, fence manifest `35d3375e…` — all matching the pins. |
| Per-level delta | `assert_no_per_level_delta` present; no signed quantity distributed across levels. |
| No local accounting | `check_no_local_accounting` **clean** on `experiments/INFR-018/code` and `src/xen/sigbar` (re-run by me, not taken from the pin). |
| No Python strategy backtest / L-31 | No Nautilus engine in this item at all. The new `ProcessPoolExecutor` is pure-polars symbol parallelism — L-31 does not apply. |
| Unit tests | 34/34 pass. Tripwire tests now run under the **production** strings `"HYP-I2 future_shift"` / `"HYP-I3 outcome_path_swap"` (the run-4 green-wash is fixed) — but the I3 test at `tests/test_sigbar_infr018.py:695-699` *asserts* that a plantless I3 tripwire passes. See I-37. |
| L-32 (values are report layers) | Holds for value reads. Ledger sentence naming the hard gates is incomplete → **I-41**. |
| L-23 amendment ledger | 0 LOOSER / 3 TIGHTER / 2 NEUTRAL; no ≥3 one-directional streak (max consecutive run = 1). Timing-record residual → **I-40**. |
| L-28 derangement | Destroy is a deterministic shift, not a permutation; the *control* ensemble is fixed-point-free by construction and asserted. Verified. |

### Issues

**I-37 — MAJOR — the HYP-I3 freeze path never requires its positive control (`is_i3_gate` is dead code).**
- `freeze_and_pin.py:158` computes `is_i3_gate = name.startswith("HYP-I3")` and **never reads it**.
  The plant requirement at line 192 is gated on `is_i2_gate` alone.
- Demonstrated: `_assert_tripwire({"collapse_fraction": 0.05, "class": "future_destroy"},
  "HYP-I3 outcome_path_swap")` returns OK with no `positive_control`. `tests/test_sigbar_infr018.py:695-699`
  encodes that pass as expected behaviour.
- This is exactly the I-36 shape: the leaky-disc probe (QA run 2, I-30) is built by the emitter
  (`hyp_i3_a6_race.py:495-519`) and is the only evidence the path-swap destroy has bite, but nothing
  makes its absence fatal. A future edit, or a `_run_disc` returning `S: None`, degrades the HYP-I3
  gate to a bare `|cf| ≤ 0.25` magnitude check with no sensitivity proof.
- **Required:** require `positive_control` on the I3 path too (use `is_i3_gate`), and change the unit
  test at :695 to assert refusal on a plantless I3 tripwire. Blocks `freeze_and_pin.py a6`, not
  `freeze_and_pin.py anchor`.

**I-38 — MAJOR — the deliverable registry is materially thinner than design §9.**
- (a) `freeze_and_pin.py:398` writes `design_table: anchor["full_table"]`, which is `race["ranked"]` —
  `{anchor_id, ib_minutes, contrast_median}` only. §9 requires the full 12-cell table with **E, the
  control level, the collapse fraction, and stability**. `contrast_ci` and `power` exist in
  `anchor_freeze.json` and are dropped at the registry boundary. Given every A-USOPEN contrast is
  below its own MDE and the winner's CI spans zero, a pin carrying medians alone reads as a ranking
  of resolved effects when nothing here is resolved. Same omission on `a6_rule` (`day_clustered_ci`
  is in `a6_freeze.json`, absent from the pin).
- (b) `universe` (`freeze_and_pin.py:429`) has no **realised membership hash** and no **churn rate**;
  §9 and §6.1:445 require both. Neither is computed anywhere in the item.
- (c) `scope_limits.unpowered_strata` (`:446-448`) is a pointer string; §9 requires **every** UNPOWERED
  stratum, and §6.2:464-470 pre-declares them (per-symbol strata < 40 sessions; the third-splits on
  A-USOPEN/A-EUOPEN; the BTC/ETH/SOL spot-check cells).
- **Required:** carry per-cell E / control level / collapse fraction / stability / CI / MDE into
  `anchor.design_table`; add the membership hash and churn rate; enumerate the UNPOWERED strata.

**I-39 — MINOR — `n_incomplete_sessions` is counted over a different population than `n_real_sessions`.**
- `hyp_i2:134-138` reads the count from `r_full`, i.e. **before** `_restrict_to_members`, while
  `n_real_sessions` is post-restriction. The winner cell reports 22,805 incomplete against 8,175
  admitted; the numbers cannot be reconciled by a reader. (Pre-existing — identical in the
  pre-refactor artifact.) Report layer, no gate impact.
- **Required:** count incomplete on the membership-restricted frame, or rename the field to say it
  spans the full band for every panel symbol.

**I-40 — MINOR — §11's pre-measurement preamble is still false, and AMENDMENT-4a has no timing note.**
- `design.md:578-579` asserts *all* amendments are pre-measurement. AMENDMENT-4 corrects itself in its
  TIMING block (post-smoke, operator-ratified 2026-07-20) — that part is honest and closes I-35.
  AMENDMENT-4a was authored after the full DESIGN race and carries **no** timing note at all, so it
  sits under the blanket false claim.
- Direction is TIGHTER (enforcement only), so there is no qualification risk. This is record accuracy,
  not a bar move. **Judged non-blocking** but it should not survive into the pin: the same
  "pre-measurement" claim was a MAJOR (I-35) one run ago.
- **Required (one line each):** amend the preamble to except AMENDMENT-4/4a, and give 4a the same
  dated timing note.

**I-41 — MINOR — §11's "the only hard gates are …" sentence is incomplete.**
- `design.md:653-656` names the future-destroy tripwires and the band/hash/window assertions.
  `_assert_full_universe` (`freeze_and_pin.py:231-252`) and the spot-check MATERIAL branch
  (`:275-284`) also hard-block a freeze, and the latter is value-keyed (below local median, or
  negative, on ≥2 of 3 instruments). It **escalates to the operator** rather than adjudicating a
  verdict, so it is compatible with L-32 and with INFR-016's retirement of auto-deciding value gates —
  but the ledger should name it rather than imply it does not exist.

**I-42 — MINOR — control-clock seeds collide by construction; the comment claims more than the code delivers.**
- `hyp_i2:411` computes `seed = (SEED_PSEUDO_FUND if shape == 3 else SEED_PSEUDO_DAILY) + i`, and
  `SEED_PSEUDO_FUND = SEED_PSEUDO_DAILY + 2`. A-FUND and A-EUOPEN therefore both draw seed
  `20180104`, and A-USOPEN draws `20180103` = `SEED_PSEUDO_FUND`. The comment at `:407` says the
  per-anchor seeding is what stops two anchors sharing a control ensemble; in fact the ensembles are
  distinct only because `feasible_offsets` differs per anchor. Verified: all four ensembles are
  distinct, regenerable and fixed-point-free. No numeric impact today; the stated guarantee is not
  the operative one.

**I-43 — MINOR — the race artifact does not record `--workers`.**
- `universe_scale` records `limit` but not the worker count, so the artifact no longer fully describes
  the run that produced it. Cheap fix; add it beside `limit`.

**I-44 — MINOR — `x.median() or float("nan")` maps a true median of 0.0 to NaN.**
- `hyp_i2:210-211` (and the `not in (None, 0)` guard at `:214`). Observed live in my 12-symbol
  reproduction: A-UTC0 L=30 and L=60 report `CALIBRATION_ONLY.asym_control_median: NaN` with **27,300
  control sessions** and `collapse_fraction: -0.0` — the median was exactly 0.0, not missing.
- Not present in the full-scale artifact, and `CALIBRATION_ONLY` is barred from any headline, so this
  is report-layer only. Use an explicit `is None` test.

### Residuals carried forward

| Item | State after run 5 |
|---|---|
| **I-13** | **STILL OPEN.** `common.py:243-258` remains a location shift (`values − median + s`), not §3.4's injected-drift plant. Materiality has *risen*: the "winner is below its MDE" read now rests on this approximation. |
| **I-27** | **UNCHANGED.** `sessions.py:362-363` returns a bare empty frame when every session is incomplete, so the count is silently zero. Distinct from I-39. |
| §11 preamble vs AMENDMENT-4 TIMING | Now **I-40** (with 4a added). Non-blocking, one-line fix. |

### Disposition (I-34 / I-35 / I-36 and new)

| Item | Run 4 | Run 5 |
|---|---|---|
| I-34 | PARTIAL | **CLOSED** — adjudicator shared, freeze re-derives, `day_corr` mandatory and finite, plant required and its insensitivity refused. Verified by attack, not by reading. |
| I-35 | FIXED | **CLOSED** (residual → I-40). |
| I-36 | NEW MAJOR | **CLOSED** — prefix match fires on the live string; production-name tests added; all bypasses I tried were refused. |
| Perf refactor | not reviewed | **ACCEPTED** — numerically neutral at full scale and under `--workers 1` vs `10`; cache key sound; control reuse sound; no dropped column. |
| I-37 | — | **NEW MAJOR** — I3 plant requirement unwired. |
| I-38 | — | **NEW MAJOR** — registry thinner than §9 (CI/MDE, membership hash, churn, UNPOWERED strata). |
| I-39, I-40, I-41, I-42, I-43, I-44 | — | **NEW MINOR.** |

### Routing

- **`experiment-developer`:** **I-37** (required before `freeze_and_pin.py a6`), **I-38** (required
  before `registry`), I-39, I-43, I-44; optionally I-42 comment/seed.
- **`quant-designer` / operator:** I-40 (§11 preamble + 4a timing note), I-41 (name the value-keyed
  escalation among the hard gates), **I-13** (plant form).
- **Not routed:** the survival rule itself, the anchor-cache design, the parallel execution model —
  all verified sound this run.

### What a freeze would do today (mechanical, not authorisation)

`freeze_and_pin.py anchor` would now pass all three of its checks on the artifact on disk (full
universe, non-surviving tripwire with a surviving plant, COSMETIC spot-check), and I could not find a
way through the HYP-I2 tripwire gate that should have been blocked. That step is sound. The item is
still REVISE because the *next* two steps are not: the a6 freeze does not require its own bite plant
(I-37), and the registry it produces would understate what §9 requires it to carry (I-38).

---

## QA run 6 — 2026-07-20T23:41Z — mode: subagent — HEAD `76cf916f` (dirty: INFR-018/, `xen/sigbar/*`, `tests/test_sigbar_infr018.py`)
Verdict: **REVISE**

Scope: re-derive every run-5 fix (I-37, I-38, I-39–I-44), attack the never-reviewed registry code
(`_design_table`, `_unpowered_strata`, `resolution`, `membership_sha256`, `panel_churn`), attack the
I-13 closure-by-demonstration, and re-verify the freeze gates on the regenerated full-scale artifact.
Nothing was written to `results/`; the freeze was not run; helpers were exercised in-process only.

### Run-5 fixes — verified

| Claim | Verdict | Evidence |
|---|---|---|
| I-37 — I3 freeze requires `positive_control` | **CLOSED (mechanically)** | `freeze_and_pin.py:294`; live probe: plantless I3 tripwire REFUSED, real emitter shape (`purpose/read_past_qualify/S_raw/S_swapped/collapse_fraction`, no `kind`) PASSES, probe cf 0.9 REFUSED, cf None REFUSED. No spurious block. **But see I-45 — the required polarity is wrong.** |
| I-38a — full 12-cell design table | FIXED | `_design_table` recomputed live: E, CI, zero-exclusion, block fragility, MDE, `below_own_mde`, calibration levels, collapse fraction, n, stability. 8.6 kB. `a6_freeze.full_table` + registry `a6_rule.day_clustered_ci`/`design_table` present by reading. |
| I-38b — membership hash + churn | FIXED | `membership_sha256` recomputed = `f11dd7f0…` (artifact matches); order-invariant (row-shuffled frame hashes identically); CSV-not-parquet choice is sound. `panel_churn` 0.09323 reproduced; divisor named (L-21). **Caveats I-46, I-51.** |
| I-38c — `unpowered_strata` enumerated | **PARTIAL** | 73 per-symbol strata < 40 paired days (reproduced: winner cell has 130 symbols, median 26 days, 73 below floor) and 10 of 12 cells below own MDE (reproduced exactly) are right. **Third-splits are the wrong object (I-47); the class leg is a dead branch (I-49).** |
| I-39 — field renamed | FIXED | `n_incomplete_sessions_band_total`, counted pre-restriction (`hyp_i2:132-137`), comment accurate. Caveat under I-27 below. |
| I-40/I-41 — §11 ledger | MOSTLY FIXED | preamble now excepts 4/4a; 4a has a dated TIMING block (RATIFICATION PENDING); 4b added; 4-item hard-gate list including the value-keyed spot-check escalation. **Still incomplete — I-54.** |
| I-42 — seed comment | FIXED | `hyp_i2:419-423` now names `feasible_offsets` as the operative guarantee and states the collision. |
| I-43 — `--workers` | FIXED | artifact `universe_scale.workers = 10`. |
| I-44 — `median or NaN` | FIXED | explicit `is None` tests at `hyp_i2:215-223`; artifact carries no NaN levels. |

### Freeze-gate behaviour on the artifact now on disk (dry-run, helpers only)

`_assert_full_universe` PASS (limit null, 140 symbols, 609 days). `_assert_tripwire` PASS
(`survives false`, plant `survives true`, cf 0.703, day_corr 0.708). `_spot_check_divergence`
COSMETIC (BTC/ETH above local median and positive; SOL below and negative → 1 of 3, rule needs ≥2).
Attacks all refused: plant stripped, plant `{}`, plant that does not survive, plant with `kind` and
`day_contrast_correlation` removed, `--limit 12`, 19 symbols, spot-check absent. One bypass remains
(I-53): a tripwire passed under a gate name that starts with neither `HYP-I2` nor `HYP-I3` needs no
positive control at all — no production call site does this today.

### Golden trace (re-derived from the design, not from the emitter)

| Trace | Design | Live | Verdict |
|---|---|---|---|
| GT-1 BTCUSDT A-UTC0 L=60 2023-01-11 | IB 17479.5/17416.5, w 63.0, break 01:07 @ 17490.5, MFE 540.50 (8.5794), MAE 181.00 (2.8730), A +5.7064 | identical, A +5.706349 | MATCHES |
| GT-2 SOLUSDT A-FUND 08:00 L=30 2023-01-11 | IB 16.10/15.98, w 0.12, MFE_norm 5.7083, MAE_norm 1.2917, A +4.4166 | identical, A +4.416667 | MATCHES |
| GT-3 (a)(b)(c)(d) negative traces | must raise | CONFIRM row in DESIGN path, holdout row, per-level Δ, unknown band — all raise | MATCHES |

### Governance & boundary

- `check_no_local_accounting` ok on `INFR-018/code` and `xen/sigbar`. No Nautilus run, no P&L object.
- Bands: DESIGN max `OpenTime` 2023-02-28 23:59; holdout assert fires at `≥ 2025-01-08`. TEST band has
  no code path (`band_window` raises on `"TEST"`). 0 counted reads. Holdout never queried.
- Frozen inputs re-hashed at entry: baselines `1b7244c8…`, column pin `e3b9fd9b…` — both verified live.
- No `pass` field anywhere in the new registry code; `below_own_mde` / `resolution` drop, hide and
  re-rank nothing (L-32 satisfied). Selection remains "highest contrast", unweighted by stability.
- Derangement: pseudo-anchor destroy fixed-point-free by construction and asserted; verified.
- 34/34 unit tests pass.

### Issues

**I-45 — MAJOR — the HYP-I3 path-swap tripwire cannot fire on the leak it names, and its positive control has inverted polarity. AMENDMENT-4b has just made that mandatory.**
- `swap_outcome_paths` (`hyp_i3_a6_race.py:145-205`) builds `swapped_bars` (donor path re-timed onto the
  target window) but passes it **only** to `label_outcomes`; it returns labels. `_run_disc`
  (`:448-465`) then evaluates every discriminator against `per_symbol_bars` — the **real** bars.
- Consequence: under the destroy a discriminator's calls are a function of the target's real path
  while the labels are a function of an independent donor path. Both an honest rule and a genuinely
  leaky rule therefore lose all correlation and collapse. There is no construction of the leak the
  design names ("the qualifying window is seeing outcome information") that can survive this destroy,
  so the HARD gate at `freeze_and_pin.py:282` is structurally unable to fire on it.
- The probe confirms this rather than testing it: `positive_control` is a deliberately leaky
  discriminator (`read_past_qualify=True`, w=240) that is **required to collapse**
  (`freeze_and_pin.py:323-330`). Compare the I2 gate, where the plant must **survive**. The two gates
  use opposite polarities for the same concept, and the freeze's own error text —
  "a deliberately leaky discriminator survived the destroy, so the tripwire is insensitive" — asserts
  the inverse of what survival would mean (a plant that survives is a gate that fires, i.e. sensitive).
- design.md §4.4's vacuity check has the same inversion ("A discriminator computed strictly
  pre-outcome CANNOT survive this" is true but empty; the load-bearing claim would be that a leaky one
  CAN), and §4.4 declares no positive control at all, so AMENDMENT-4b enforces an artefact the design
  never specifies. §11 hard-gate item 1 ("each of which must also carry a positive control that
  fires") is false for I3 as implemented.
- **Required (cheap, and HYP-I3 has not been run so nothing is contaminated):** evaluate the
  discriminator on bars whose **outcome window has been replaced by the donor path** (qualifying
  window untouched), so the leaky probe reads the same path the labels came from. Then the honest
  rule collapses, the leaky probe survives, the gate fires on it, and the probe becomes a bite plant
  with the same polarity as I2's. Update §4.4 (declare the probe and its direction), AMENDMENT-4b, and
  the `freeze_and_pin` else-branch polarity + message. Blocks `freeze_and_pin.py a6`, not `anchor`.

**I-46 — MAJOR — `universe_reconciliation.json` is not band-scoped, so the registry can pin the CONFIRM panel as "the universe".**
- `hyp_i2_anchor_race.py:399` writes `universe_reconciliation.json` on **both** bands under one name
  (the membership parquet is correctly band-suffixed at `:400`; this file is not). §3.6 requires a
  CONFIRM run of the winner after the anchor freeze and before the registry (`build_registry` reads
  `hyp_i2_anchor_race_CONFIRM.json` at `:487`), so by the time `registry` runs the file on disk will
  describe the **CONFIRM** bank.
- `build_registry:563` copies it verbatim into the pin's `universe` block — which now carries
  `membership_sha256` and `churn`. The deliverable would pin the membership hash, churn rate,
  symbol count and 200-vs-197 reconciliation of a panel **nothing was selected on**, silently. The
  only tell is the `band` field inside the block, and no code checks it.
- **Required:** band-suffix the filename (`universe_reconciliation_DESIGN.json`) or have
  `build_registry` load the DESIGN file explicitly, and assert
  `universe["reconciliation"]["band"] == "DESIGN"` before pinning.

**I-47 — MAJOR — `_unpowered_strata` declares the POOLED chronological thirds unpowered; §6.2 pre-declares the PER-SYMBOL thirds.**
- `freeze_and_pin.py:176-182` walks `cells[*].stability.thirds`, which is the pooled day-contrast split
  (`hyp_i2:182-184`): 18 rows at ~202 **days** each. Design §6.2:487 pre-declares "the 3
  chronological-third splits on A-USOPEN/A-EUOPEN **per-symbol** (~76 sessions/third)".
- The pin would therefore label a well-powered pooled stratum UNPOWERED, and an UNPOWERED stratum "can
  never be read as a negative" (B-5). This is not hypothetical: the winner cell's pooled thirds are
  +0.161 / **−0.677** / +0.451, so the block as written licenses waving away the one strongly negative
  third in the deliverable. That is exactly the misuse B-5 exists to prevent.
- **Required:** enumerate per-symbol thirds (or drop the third leg and state that the per-symbol
  thirds were not computed), and never list a pooled stratum under an unpowered heading.

**I-48 — MAJOR — I-13 is not closed by the demonstration: leg 1 is circular, and the design's literal plant moves `asym` by 2s, not s.**
- `mde_plant_equivalence.py:87-98` adds `s·ib_width` to the `mfe` column, recomputes
  `asym = mfe/ib_width − mae_norm`, and reports `|Δasym − s| ≈ 1e-14`. That is float arithmetic on an
  identity, not evidence about the modelling step. The load-bearing sentence — "widening post-break
  drift by s·IB_width adds s·IB_width to MFE **and nothing to MAE**" (design.md:202-203) — is asserted
  in prose and never tested.
- It is also false for the design's literal plant. §3.4 says "widen post-break drift in the break
  direction by s·IB_width". `mfe = post_high − break_close`, `mae = break_close − post_low`
  (`sessions.py:410-418`), and the excursion window is strictly after the break bar, so a constant
  drift `c = s·IB_width` applied to the post-break path shifts **both** extremes by `c` and leaves
  `break_close` fixed: `mfe → mfe + c`, `mae → mae − c`, hence `asym → asym + 2s`.
- Materiality: the reported MDEs are then 2× the design-plant MDE. Recomputing `below_own_mde` at
  `mde/2` turns the pin's headline from **10 of 12** cells below their own floor into **6 of 12**
  (A-UTC0 15/60, A-EUOPEN 15, A-USOPEN 60 flip). The winner's own read does not change
  (E = 0.0999 < 0.25), and no verdict moves, but a headline number in the deliverable depends on an
  unstated plant convention.
- Leg 2 is sound as far as it goes (day-median invariance and identical day set at every `s`,
  reproduced from the artifact), and the re-centring is a defensible detectability floor, honestly
  disclosed in design §3.4 and in the artifact.
- **Required:** pick one. Either restate §3.4's plant as "add `s·IB_width` to the favourable excursion
  (MFE) only" — which is what the code does — or keep the drift wording and halve the swept `s`. Do
  not record I-13 as "closed by demonstration" while the demonstrated leg is the arithmetic one.

**I-49 — MINOR — the class leg of `_unpowered_strata` is a dead branch.**
- `freeze_and_pin.py:188` reads `i4["exit_2_class_clustering"]["unpowered_classes"]`; the HYP-I4
  emitter never writes that key (it writes `per_class[<cls>].band_label == "UNPOWERED"`,
  `hyp_i4_validation.py:486-495`). The fallback pointer string is therefore the only reachable value,
  so the pointer-string defect I-38c set out to remove survives for the class strata §6.2 pre-declares.
- **Required:** derive the list from `per_class[*].band_label`, or from `event_counts` against the
  published MDE floor.

**I-50 — MINOR — `resolution.n_cells_ci_excludes_zero: 4` omits the sign, and the sign is the whole point.**
- All four cells whose interval excludes zero are **negative** (A-UTC0 15/30, A-FUND 15, A-EUOPEN 15),
  and the winner is not among them. As printed, the pin reads as if the race resolved four effects.
- **Required:** add `n_cells_ci_excludes_zero_positive: 0` (or list them) beside the count.

**I-51 — MINOR — the churn rate is a mean over panel days of wildly different width, and the width is not disclosed.**
- Realised panel sizes run 2 → 20; **258 of 609** days have fewer than 20 members and **153** fewer
  than 10 (first full 20-symbol day is 2022-02-08). Churn over full-panel consecutive pairs is
  **0.1333** (n=338) against the reported **0.0932** (n=608) — a 43% difference driven by thin early
  days where one substitution is 1/2 to 1/10 of the panel.
- The divisor is named (L-21 satisfied); the population is not. **Required:** emit the panel-size
  distribution (or `n_days_at_full_panel` and the full-panel churn) beside the headline rate.

**I-52 — MINOR — the re-derived survival verdict never reaches disk.**
- `freeze_anchor:375` discards the dict `_assert_tripwire` returns and writes the raw emitter block at
  `:411`, so `survives_rederived` (the whole point of I-34) appears in neither `anchor_freeze.json`
  nor `validity_attestations.tripwire_future_shift_i2`. The pin attests with the emitter's own flag.
- **Required:** `tw = _assert_tripwire(...)` and write `tw`.

**I-53 — MINOR — the positive-control requirement is still keyed on a caller-supplied name string.**
- `freeze_and_pin.py:294` requires the probe only when the name starts with `HYP-I2`/`HYP-I3`.
  Verified: a tripwire with no `positive_control` passed under the name `"future_shift"`. Both
  production call sites are correct today; this is the I-36 shape one layer down.
- **Required:** require `positive_control` unconditionally — there is no third caller.

**I-54 — MINOR — §11's "complete list" of hard gates is still not complete.**
- Also machine-enforced and unnamed: `assert_no_fixed_points` (`sessions.py:172`), the
  CONFIRM-before-freeze refusal (`hyp_i2:392`), `assert_no_per_level_delta` (`fences.py:204`), and
  `check_no_local_accounting` inside `build_registry` (`:467-473`). The preamble also enumerates
  1–3 / 4 / 4a and omits 4b, which carries its own TIMING block.
- The TIGHTER-streak note is honest and errs conservatively (amendments 1, 3, 4a, 4b are TIGHTER with
  NEUTRALs interleaved; the longest consecutive run is 2). L-23 flagging is satisfied.

**I-55 — COSMETIC.** (a) `scope_limits.realised_design_span_days` (`freeze_and_pin.py:577`) has an
unclosed parenthesis. (b) the new I3 probe unit test (`tests:690-700`) uses
`{"kind": "i3_leaky_disc", …}`, a shape the emitter never writes; I verified the real shape
(no `kind`) is accepted, but the test does not pin the emitted contract.

### Residuals

| Item | State after run 6 |
|---|---|
| **I-13** | **OPEN, reclassified — see I-48.** The closure argument's load-bearing leg is untested and its literal reading is off by 2×. |
| **I-27** | **ACCEPTABLE AS RECORDED, with one addition.** The comment at `sessions.py:363-369` is accurate and the return-contract argument is sound (HYP-I3/I4 share it). But the caveat lives only in source: the artifact publishes `n_incomplete_sessions_band_total` with no note that symbols whose sessions are *all* incomplete contribute zero. Carry one sentence into the emitted field or the pin's scope limits; do not change the contract mid-item. |
| I-34 / I-35 / I-36 / I-37 | CLOSED (I-37 mechanically; its polarity is now I-45). |
| I-39 / I-42 / I-43 / I-44 | CLOSED. |
| I-38 | PARTIAL — (a) closed, (b) closed but see I-46/I-51, (c) see I-47/I-49. |

### Routing

- **`experiment-developer`:** I-46, I-47, I-49, I-50, I-51, I-52, I-53, I-55, and the implementation
  half of I-45 (evaluate the discriminator on swapped outcome-window bars).
- **`quant-designer` / operator:** I-45 (§4.4 tripwire vacuity check + declare the probe and its
  direction; AMENDMENT-4b), I-48 (§3.4 plant wording), I-54 (§11 list), I-27 caveat placement.
- **Not routed — verified sound this run:** the HYP-I2 freeze path end to end, the survival
  adjudicator and its plant, `_design_table`, `membership_sha256`, the golden traces, the fences, the
  universe rule and its causal shift, the anchor/control construction.

### What a freeze would do today (mechanical, not authorisation)

`freeze_and_pin.py anchor` would pass on the artifact on disk and I again found no way through that
gate that should have been blocked. `freeze_and_pin.py a6` would pass on a well-formed I3 artifact —
but on a tripwire that cannot fire (I-45). `freeze_and_pin.py registry` would run without error and
would pin the CONFIRM panel's membership hash and churn as the universe (I-46) and mis-label the
pooled thirds as unpowered (I-47).

---

## QA run 7 — 2026-07-21T00:35Z — mode: subagent — HEAD `76cf916f` (dirty: `INFR-018/`, `xen/sigbar/*`, `tests/test_sigbar_infr018.py`)

Verdict: **REVISE**

Scope of this run: re-derive everything claimed fixed since run 6, with the sharpest attack on
AMENDMENT-6 (I-45). Nothing was written to the repo (`git status` unchanged; race artifact md5
`019405d6…` before and after). No freeze launched, no pin written.

### Run-6 fixes — verified

| Item | State | Evidence |
|---|---|---|
| I-45 **design half** | **CLOSED** | §4.4 now declares the spliced-path destroy, the `i3_leak_plant` probe and `required_outcome: SURVIVES`; AMENDMENT-6 present with direction TIGHTER and a TIMING block. `freeze_and_pin.py:339-371` re-derives probe survival from `S_raw`/`S_swapped`/`cf` and refuses when the emitter's flag disagrees (verified live: `survives:False` on a surviving probe → refused). |
| I-45 **polarity, on real data** | **CONFIRMED WORKING** | Mini-I3 on 8 symbols (A-USOPEN, L=15, δ=0.05, DESIGN, 2107 events): honest `D4-t50-w30` cf **−0.046** (collapses), leaky probe (`w=240`, `read_past_qualify`) cf **+1.33** (survives). The gate can now fire on the leak it names. |
| I-46 | **CLOSED** | `hyp_i2:401` writes `universe_reconciliation_{band}.json`; `freeze_and_pin:527-533` loads the DESIGN file and raises unless `reconciliation.band == "DESIGN"`. No stale un-suffixed file on disk. Artifact band field = `DESIGN`. |
| I-47 | **CLOSED** | `freeze_and_pin:214-219`. 18 pooled thirds republished under `NOT_unpowered_pooled_thirds` with "are NOT that stratum, are NOT unpowered, and may not be dismissed as such". Re-read for the inverse reading; there isn't one. |
| I-48 | **CLOSED** (residual → I-65) | `mde_plant_equivalence.leg1` now drifts `post_high`/`post_low` by `s·W·break_side` and recomputes MFE/MAE from their own definitions. I re-derived the algebra independently: both extremes shift by `c`, `break_close` is fixed, so `asym → asym + 2s`. Artifact max deviation from `2s` = **2.9e-12**, from `1s` = the full `s`. Leg 2 reproduces (7.1e-15). AMENDMENT-5's contrast-units declaration is internally consistent: `mde_curve` sweeps the contrast series, `_design_table.below_own_mde` compares `abs(E)` to that same `mde`. Materiality restated: at `mde/2` the below-floor count is 6 of 12 (reproduced), but under the contrast-units declaration 10 of 12 is the correct like-for-like read. |
| I-49 | **CLOSED** | `freeze_and_pin:195-199` reads `per_class[*].band_label == "UNPOWERED"`; exercised with `i4=None` → honest `class_strata_source` fallback string, no pointer masquerading as data. |
| I-50 | **CLOSED** | `cells_ci_excludes_zero` (all four reproduced: A-UTC0 15/30, A-FUND 15, A-EUOPEN 15, contrasts −0.416/−0.299/−0.163/−0.303), `n_cells_ci_excludes_zero_positive`, `winner_ci_excludes_zero_flag`. |
| I-51 | **CLOSED** | `panel_size` {max 20, min 2, full 351, below-full 258, below-half 153} and `churn_rate_full_panel_pairs_only` **0.13328** over 338 pairs vs headline 0.09323 — both reproduced from the artifact. |
| I-52 | **CLOSED for the tripwire body** (residual → I-63) | `freeze_anchor:419` keeps the return; `survives_rederived` present in the returned dict. |
| I-53 | **CLOSED** | `positive_control` required unconditionally (`:309-316`). Verified: `{"collapse_fraction":0.05}` under the name `"future_shift"` is now REFUSED. |
| I-54 | **PARTIAL** → I-64 | List grew to nine; four machine refusals still unnamed. |
| I-55 | **CLOSED** | Parenthesis closed at `:649-650`; the I3 probe test now uses the emitted shape (`kind`/`purpose`/`required_outcome`/`read_past_qualify`/`S_raw`/`S_swapped`/`collapse_fraction`). |
| I-27 | **CLOSED** | Caveat travels in `scope_limits.incomplete_session_counts`. |
| Same-symbol donors starving the pool | **NOT A PROBLEM AT SCALE** | 8-symbol run: 80 blocks, 2103 permutable rows, **4** singleton rows. The constraint costs ~0.2% of the population. |
| Artifact reproduction | **HOLDS** | 140 symbols, 609 days, `limit: null`, `workers: 10`; winner A-USOPEN×15, E=+0.0999656, MDE 0.50; tripwire `survives:false` (cf −41.7, day_corr 0.060), plant `survives:true` (cf 0.703, day_corr 0.708); spot-check COSMETIC (1 below median, 1 negative, 3 instruments) — all recomputed live from the artifact. 36/36 tests pass. `check_no_local_accounting` passes on `INFR-018/code` and `xen/sigbar`. |

### Design-fidelity trace (this run's scope)

| Design clause (§ref) | Code | Verdict | Notes |
|---|---|---|---|
| §4.4 path swap: "evaluated bars = target's bars before `outcome_start` ⧺ donor's outcome-window bars, re-timed" | `hyp_i3:199-250` | **DEVIATES** | The splice is built, but ~half the events never reach the label step and the rebuilt frame is not well-formed (I-56, I-61). |
| §4.4 "zero fixed points, asserted" | `hyp_i3:113-131`, `:191` | **DEVIATES** | Singleton blocks are self-donors, counted as spliced, never asserted or dropped (I-57). |
| §4.4 "coverage: events with no usable donor path are dropped and their count published" | `hyp_i3:255-258` | **DEVIATES** | `spliced_fraction` is published but attributes a code defect to donor unavailability (I-56). |
| §4.4 `SURVIVAL := |cf| > 0.25 with the same sign as S_raw` | `freeze_and_pin:297-303` | **DEVIATES** | Magnitude-only; sign clause absent (I-59). |
| §4.4 POSITIVE CONTROL required, `required_outcome: SURVIVES` | `hyp_i3:570-589`, `freeze_and_pin:339-371` | **MATCHES** | Polarity correct and enforced; verified by attack. |
| §4.4 "the qualifying window is untouched" | `hyp_i3:242-246`; test `:840-847` | **MATCHES** | Verified: pre-`outcome_start` closes identical after the splice. |
| AMENDMENT-5 "the pin gains an explicit units field" | `freeze_and_pin` (grep `unit`) | **MISSING** | No units annotation anywhere in the pin (I-62). |
| §11 "every amendment states its direction and the running count" | `design.md:195-227` | **DEVIATES** | AMENDMENT-5 has no running count (I-64a). |

### Golden trace

GT-1/GT-2 unchanged and untouched by this run's diffs (`sessions.py` not modified since run 6;
36/36 tests including the construction pins pass). GT-3 negatives re-exercised through
`_assert_tripwire`: every malformed tripwire and probe shape I tried raised.

### Issues

**I-56 — BLOCKER — the path-swap destroy silently drops ~half its events, and which half is a monotone function of calendar time.**
- `attach_sessions` (`sessions.py:242-256`) leaves a `session_end` column **on the bar frame**.
  `label_outcomes` (`acceptance.py:403-415`) then joins the poke's `session_end` in; polars suffixes
  the right-hand copy to `session_end_right`, so `pl.col("session_end")` in the outcome-window filter
  resolves to the **bars'** column, not the poke's.
- In the splice (`hyp_i3:215-219`) donor rows keep the **donor session's** `session_end` while their
  `OpenTime` is re-timed onto the target. The filter therefore reads
  `OpenTime >= tgt.outcome_start AND OpenTime < donor.session_end`. Every event whose target session
  is **later** than its donor's yields an empty window, `lab.height == 0`, and the event is skipped.
- Measured, not inferred. BTCUSDT alone (A-USOPEN, L=15, δ=0.05, DESIGN): **115 of 227** events
  labelled as-is; **227 of 227** after dropping the stale bars-side column — nothing else changed.
  8-symbol run: 1031 of 2107 retained, and retention by 30-day bucket runs
  1.00 → 0.80 → 0.65 → 0.48 → 0.34 → 0.22 → 0.08 → **0.00** across the bank. The last month of the
  DESIGN bank is not destroyed at all.
- The artifact would publish this as `spliced_fraction: ~0.50` under a design clause that reads
  "events with no usable donor path are dropped" — attributing a column-name collision to donor
  availability. Nothing else in the pin reveals it.
- The same collision reaches `evaluate_discriminator(read_past_qualify=True)`
  (`acceptance.py:212-229`): `window_end = pl.col("session_end")` is likewise the bars' column, so on
  the spliced frame the leaky probe's read window on donor rows ends at the **donor's** session end.
- **Required:** drop or rename the bars-side `session_end` before relabelling (verified sufficient),
  or have `label_outcomes`/`evaluate_discriminator` select the poke columns under explicit aliases so
  a bar-frame column can never shadow them. Add a test on the production bar schema — see I-58.
  Blocks `freeze_and_pin.py a6`. Does not touch the HYP-I2 anchor path.

**I-57 — BLOCKER — singleton donor blocks are self-donors, are counted as spliced, and no fixed-point assertion exists.**
- `derange_within_blocks` (`hyp_i3:113-118`) leaves blocks of size 1 in place. `swap_outcome_paths`
  then splices the target's outcome window with **its own path** (offset 0), recomputes the true
  label, and increments `n_events_spliced`.
- Demonstrated on the project's own fixture: 12 events, 10 blocks, 8 singletons →
  `spliced_fraction: 1.0` while only **4 of 12** outcome windows actually changed. The remaining 8
  are undestroyed events inside the destroy arm.
- Design §4.4 declares "zero fixed points, asserted" (L-28). Nothing asserts it and nothing is
  dropped. The direction is **non-conservative for the bite plant**: undestroyed events preserve the
  probe's true correlation and make it survive more easily, which is the VAL-008 shape L-28 exists
  for (11.1% fixed points → collapse 0.87).
- At the 8-symbol scale this is 4 rows of 2107, so it is small — but it is unbounded, unasserted, and
  mis-counted.
- **Required:** drop singleton-block events from the destroy population and publish their count as a
  separate field, or raise. Do not count them in `spliced_fraction`.

**I-58 — BLOCKER — `test_path_swap_donors_are_same_symbol` cannot fail, and the second half of the I-45 fix is untested.**
- Mutation run (module substituted in `sys.modules`, both new tests executed):

  | mutation | `…replaces_the_bars…` | `…donors_are_same_symbol` |
  |---|---|---|
  | baseline | PASS | PASS |
  | M1 return the ORIGINAL bars | **FAIL** | PASS |
  | M2 **drop `symbol` from the block key** | PASS | **PASS** |
  | M3 donor path = target's own path | **FAIL** | **FAIL** |
  | M4 insert donor rows without removing the target's | **FAIL** | PASS |
  | M5 remove the window, insert nothing | **FAIL** | PASS |

- M2 is the mutation the test is named for and it survives. Reason: both fixture symbols have
  identical horizons, so `rank("ordinal")` breaks the ties in sort order (all AAA before all ZZZ) and
  the deciles never mix — under the mutation there are **0 cross-symbol donors out of 24**. The test
  asserts a property the fixture guarantees regardless of the code.
- Separately, no test exercises `_run_disc(..., bars_by_symbol=swapped_bars)`
  (`hyp_i3:499-520`, call sites `:535`/`:564`). That call is the half of AMENDMENT-6 that makes the
  gate fire; a mutation there is caught by nothing.
- Both fixtures hand-build bar frames that lack `session_end`, which is exactly why they cannot see
  I-56. **Required:** build the swap fixture through `attach_sessions` so it carries the production
  bar schema; give the same-symbol test symbols with overlapping horizons; add a test that a leaky
  rule survives and an honest rule collapses end to end on the spliced bars.

**I-59 — MAJOR — the I3 HARD gate ignores the sign clause its own design declares.**
- §4.4 (AMENDMENT-6): "SURVIVAL := |collapse_fraction| > 0.25 **with the same sign as S_raw**".
  `freeze_and_pin:297-303` refuses on `abs(cf) > 0.25` alone. Verified: `cf=−6.10`, `S_raw=+0.4`,
  `S_swapped=−2.44` is refused as "leaking future information".
- Direction is conservative (false refuse, not false pass), but the diagnosis is wrong and it
  reproduces on HYP-I3 precisely the trap AMENDMENT-4 had to fix on HYP-I2 — a destroy whose null is
  non-zero and opposite-signed being read as a leak. Under the swap the labels are partly driven by
  the donor's price level (see I-66), so an opposite-sign `S_swapped` is not exotic.
- **Required:** implement the sign clause (reuse the `adjudicate_i2_survival` shape), or amend §4.4
  to magnitude-only and say why.

**I-60 — MAJOR — the collapse fraction divides two different populations.**
- `hyp_i3:541-545`: `S_raw` is `top["separation"]["S"]`, computed over every resolved event at that
  δ; `S_swapped` is computed over the spliced subset only. With I-56 that subset is time-ordered, so
  the ratio mixes a population change with the destroy's effect.
- Measured (8 symbols): raw over all events **0.7166** (n=1257); raw restricted to the spliced events
  **0.7212** (n=607); swapped **0.0354** (n=1023). The two collapse fractions agree here
  (0.0494 vs 0.0491) — but that is luck, not construction.
- **Required:** compute and publish `S_raw` restricted to the spliced event set beside the pooled
  one, and take the collapse fraction from the restricted pair.

**I-61 — MAJOR — the spliced bar frame is not well-formed: donor paths over- and under-run the target window.**
- Donors are matched on horizon **decile**, not on horizon, so the re-timed donor path does not cover
  `[tgt.outcome_start, tgt.session_end)` exactly. The removal step (`hyp_i3:243-246`) deletes the
  whole target window regardless.
- Measured (8 symbols): duplicated `OpenTime` values per symbol 127–870, net row deltas from
  **−1037** (bars lost) to **+2354** (bars duplicated). Absolute horizon mismatch is usually ~1 min
  but reaches 547 min.
- Duplicated rows carry the target's `anchor_ts` and sit past the target's `session_end`; combined
  with I-56's collision the leaky probe's window end on those rows is the donor's `session_end`, so
  the probe can read rows outside the target's own session. D4's `w` cap makes this mostly moot today
  — it is not a property anyone should rely on.
- **Required:** truncate/pad the donor path to the target's own horizon (or drop unmatched events and
  publish the count), and assert `OpenTime` uniqueness per symbol after the splice.

**I-62 — MINOR — AMENDMENT-5 promises a units field in the pin; the pin has none.**
- §3.4: "the pin gains an explicit units field". `grep -n unit freeze_and_pin.py` returns nothing.
  `power.mde`, `_design_table[*].mde` and `resolution.winner_mde` are all bare numbers.
- `hyp_i2_anchor_race.py:67` still reads "Planted-effect grid for the MDE curve, **in IB-width
  units**" — the drift framing AMENDMENT-5 supersedes. `hyp_i4_validation.py:81` carries the same
  comment for the clustering grid, where the drift-vs-contrast question has not been examined at all.
- **Required:** carry `"mde_units": "contrast (E) units; the equivalent drift plant is half this"`
  into `power`/`resolution`, fix the two comments, and say whether §5.2's grid needs the same audit.

**I-63 — MINOR — the I2 positive control's re-derived verdict still never reaches disk.**
- `freeze_and_pin:321-338` computes `p_der` for the I2 probe and discards it; only the I3 branch
  writes `survives_rederived` back (`:370-371`). Verified on the live artifact: after
  `_assert_tripwire`, `tw["positive_control"]` has no `survives_rederived`. This is I-52 one branch
  over.

**I-64 — MINOR — §11 ledger housekeeping.**
(a) AMENDMENT-5 states `DIRECTION: NEUTRAL` but carries no `running count:` line, which the preamble
requires of every amendment. (b) The preamble's timing enumeration lists 1–3 / 4 / 4a / 4b / 5 and
omits **6** — the same omission I-54 raised about 4b, one amendment later. (c) "There is a 4-long
TIGHTER streak (amendments 1, 3, 4a, 4b)" is stale; with 6 there are five TIGHTER amendments.
(d) Still unnamed among the nine hard gates: `acceptance.assert_windows_disjoint`, the HYP-I3
runner's refusal to start without `anchor_freeze.json` (`hyp_i3:271-276` — execution order, not the
CONFIRM refusal), `_spot_check_divergence`'s refusal when the spot-check table is absent
(`freeze_and_pin:62-66`), and `evaluate_discriminator`'s refusal when the A5 residual columns are
missing (`acceptance.py:352-357`). The count 0 LOOSER / 5 TIGHTER / 3 NEUTRAL is arithmetically
correct.

**I-65 — MINOR — `mde_plant_equivalence.leg1` re-implements the estimand instead of re-invoking it.**
- The demonstration is no longer circular and the `2s` result is right (I re-derived it by hand), but
  it copies the MFE/MAE formulas from `sessions.py:410-418` rather than drifting the bars after
  `break_ts` and calling `session_breaks`. If that formula moved, the demo would still "confirm".
  The drift is strictly post-break, so break detection cannot change — the honest version is cheap.

**I-66 — MINOR — the destroy's null is partly a price-level randomiser, and the probe's survival is close to tautological. Undisclosed.**
- A same-symbol donor from a different date still sits at a foreign price level relative to the
  target's IB (crypto drift over a 609-day bank dwarfs an IB width). Measured (8 symbols):
  `UNRESOLVED` falls from **40%** of real events to **1%** of swapped events, because the donor path
  crosses the target's accept or trap level almost immediately. The probe's swapped separation is
  **0.9865** — it is largely reading "is this path above or below the target's IB".
- The accept/trap balance does survive (504/530), so the labels are not degenerate, and the gate's
  logic still holds. But the operator should be told what the bite plant demonstrates.
- **Required:** publish the swapped `unresolved_rate` and a level-offset statistic (median
  |donor level − target IB mid| in IB widths) inside `tripwire_outcome_path_swap`.

### Governance & boundary

- Bands: only `DESIGN`/`CONFIRM` exist (`fences.py:49-52`); `assert_band` raises on `≥ 2025-01-08`
  and on any out-of-band row. **TEST never read; holdout never queried; 0 counted reads.**
- `check_no_local_accounting` passes on `experiments/INFR-018/code` and `src/xen/sigbar`. No P&L, no
  Nautilus run, no strategy backtest. L-29/L-30/L-31 correctly N/A.
- Per-level Δ barred and asserted; flow legs read A5 residuals only.
- Value reads remain report layers; no `pass` field; nothing machine-dropped (L-32 holds).
- Derangement (L-28): satisfied and asserted for the I2 pseudo-anchor destroy; **not** satisfied for
  the I3 path swap (I-57).
- Frozen inputs `1b7244c8…` / `e3b9fd9b…` re-verified at every entry point.
- Repo untouched by this run (`git status` identical; race artifact md5 unchanged).

### Routing

- **`experiment-developer`:** I-56, I-57, I-58, I-60, I-61, I-62 (code half), I-63, I-65, I-66.
- **`quant-designer` / operator:** I-59 (§4.4 sign clause — implement or amend), I-62 (design half),
  I-64 (§11).
- **Not routed — verified sound this run:** the HYP-I2 freeze path end to end, its survival
  adjudicator and bite plant, `_design_table`, `_unpowered_strata`, `_spot_check_divergence`,
  `membership_sha256`/churn, the universe rule and its causal shift, the band/hash/window fences,
  the MDE plant equivalence, the AMENDMENT-6 polarity (which does now work on real data).

### What a freeze would do today (mechanical, not authorisation)

`freeze_and_pin.py anchor` still passes on the artifact on disk, and I again found no way through
that gate that should have been blocked. `freeze_and_pin.py a6` cannot yet be run, but on a race
artifact produced by the current emitter it would pass a tripwire computed on roughly half the
events, chosen by calendar order, with self-donors counted as destroyed (I-56/I-57).
`freeze_and_pin.py registry` would now correctly refuse a non-DESIGN universe reconciliation and
would no longer mis-label the pooled thirds.

---

## QA run 8 — 2026-07-21T01:15Z — mode: subagent — HEAD `76cf916f` (dirty: `INFR-018/`, `xen/sigbar/*`, `tests/test_sigbar_infr018.py`)

Verdict: **APPROVE**

Scope: independent re-derivation of the run-7 BLOCKER cluster (I-56..I-61) and MINORS (I-62..I-66);
mutation-resistance of I-58 tests; sign-clause I-59; proactive path-swap / fence scan; hold of
I-45..I-55 closures. Nothing written to `results/`; freeze not launched; no pin written.
Process runner was unavailable in this subagent tool surface — pytest was **not** re-invoked live.
Evidence for tests: new path-swap nodeids are in `.pytest_cache/v/cache/nodeids` and
`.pytest_cache/v/cache/lastfailed` has **no** `test_sigbar_infr018` entry (only an unrelated chart
generator). Accounting verified by the same static rule `check_no_local_accounting` uses
(`def assemble_realized_bps|assemble_multileg_bps|per_leg_net|build_episodes` — **zero hits** under
`experiments/INFR-018/code` and `src/xen/sigbar`). Operator should still run
`python/.venv/bin/python -m pytest python/tests/test_sigbar_infr018.py -q` once before the
execution gate if this environment gap is not closed by a follow-on session.

### Run-7 claims — verified independently

| Item | State | Evidence |
|---|---|---|
| **I-56** session_end collision | **CLOSED** | `acceptance._bars_join_pokes` (`acceptance.py:190-206`) drops every non-key bar column that collides with the selected poke columns, then joins; both `label_outcomes` (`:417-426`) and `evaluate_discriminator` with `read_past_qualify=True` (`:230-243`) route through it so `pl.col("session_end")` is always the **poke's**. Path-swap additionally overwrites donor `session_end` with the target's before splice (`hyp_i3:261-265`) — defense in depth. Fixture builds through `attach_sessions` (`test_sigbar_infr018.py:800-832`); `test_path_swap_session_end_collision_does_not_drop_events` requires `n_events_spliced == n_permutable_rows` and `n_no_donor_path == 0`. Production race always `attach_sessions` before swap (`hyp_i3:423-424`). |
| **I-57** self-donors | **CLOSED** | `perm[i] == i` rows skipped (`hyp_i3:221-223`); `n_self_donor_skipped` published; `spliced_fraction` denominator is `n_events - n_self_donor_skipped` (`:324-343`); fixed-point rate among permutable asserted `== 0` and raises otherwise (`:197-202`). |
| **I-58** fixture + mutation resistance | **CLOSED** | Fixtures use `attach_sessions` + shared horizons / interleaved day offsets. Same-symbol block key is `symbol\|h_bucket` with **average** rank (`:189-195`); cross-symbol donor **raises** (`:228-235`). Mutation table (static): drop symbol from key → raise (test fails); return original bars → `n_changed` assertion fails; self-donor / empty insert still fail `replaces_the_bars`. End-to-end leaky-survives / honest-collapses pin present (`test_path_swap_leaky_survives_honest_collapses`). |
| **I-59** sign clause | **CLOSED** | `common.adjudicate_i3_survival` requires `S_raw * S_swapped > 0` **and** `\|cf\| > 0.25` (`common.py:421-428`); freeze I3 branch calls it, not magnitude-only (`freeze_and_pin.py:303-330`). Manual re-derive: `cf=-6.10, S_raw=+0.4, S_swapped=-2.44` → product &lt; 0 → `survives=False` (not refused as leak); same-sign `cf=0.9` → `survives=True` → hard block `"DID NOT COLLAPSE"`. Tests at `:689-707`. |
| **I-60** restricted S_raw | **CLOSED** | Collapse uses `st_raw_spliced` over the semi-join of race events onto spliced keys; `S_raw_pooled_race` published beside it (`hyp_i3:627-659`). Probe arm uses the same population discipline (`:673-680`). |
| **I-61** truncate + uniqueness | **CLOSED** | Donor path filtered to target `[outcome_start, session_end)` after retime (`:263-265`); `OpenTime` uniqueness asserted per symbol after splice, raises on duplicate (`:313-318`). |
| **I-62** mde_units | **CLOSED** | `MDE_UNITS` string in `power`, `_design_table[*].mde_units`, registry resolution (`freeze_and_pin.py:136-137,239,479,601`). I2 comment is contrast units (`hyp_i2:67-69`); I4 notes not re-audited for drift factor (`hyp_i4:81-83`). |
| **I-63** I2 plant survives_rederived | **CLOSED** | I2 probe branch writes `survives_rederived` back (`freeze_and_pin.py:366-368`); test `:773-776`. |
| **I-64** §11 ledger | **CLOSED** | AMENDMENT-5 has `running count: 0 looser / 4 tighter / 3 neutral` (`design.md:217`); final count 0/5/3; TIGHTER streak names 1,3,4a,4b,6; timing enum includes 6; hard-gate list items 10–13 named (`design.md:733-773`). |
| **I-65** leg1 re-invokes session_breaks | **CLOSED** | Drifts post-break OHLC on bars, then `session_breaks(...)` (`mde_plant_equivalence.py:101-120`). |
| **I-66** swap_stats level disclosure | **CLOSED** | `swapped_unresolved_rate` and `median_donor_level_offset_ib_widths` published (`hyp_i3:325-349`). |

### Previously CLOSED (run 7) — re-hold

| Item | Hold? | Notes |
|---|---|---|
| I-45 polarity (AMENDMENT-6) | **HOLDS** | Spliced bars returned and fed to `_run_disc`; probe `required_outcome: SURVIVES`; freeze refuses collapsed probe. |
| I-46 universe band suffix | **HOLDS** | `universe_reconciliation_DESIGN.json` on disk with `band: DESIGN`; registry asserts band. |
| I-47 NOT_unpowered_pooled_thirds | **HOLDS** | Explicit inverse reading blocked in pin helper. |
| I-48 / I-50 / I-51 / I-52 / I-53 / I-55 | **HOLDS** | Code paths unchanged in substance; I-63 completes I-52's I2 probe write-back. |
| I-49 class_strata from band_label | **HOLDS** | Reads `per_class[*].band_label == "UNPOWERED"`. |

### Design-fidelity trace (this run's attack surface)

| Design clause (§ref) | Code | Verdict | Notes |
|---|---|---|---|
| §4.4 path swap: spliced bars = pre-outcome target ⧺ re-timed donor outcome | `hyp_i3:147-351`, `:591-612` | **MATCHES** | Qualifying window asserted untouched in test; outcome window changes. |
| §4.4 zero fixed points, asserted (L-28) | `hyp_i3:196-202,221-223` | **MATCHES** | Per-mutable rate 0; singletons excluded from destroy population. |
| §4.4 same-symbol donors | `hyp_i3:189-195,228-235` | **MATCHES** | Block key + hard raise. |
| §4.4 SURVIVAL sign clause | `common:395-429`; `freeze_and_pin:303-330` | **MATCHES** | Emitter and freeze share adjudicator. |
| §4.4 POSITIVE CONTROL must SURVIVE | `hyp_i3:669-708`; `freeze_and_pin:369-401` | **MATCHES** | Polarity correct (I-45). |
| §4.4 collapse on same event set | `hyp_i3:627-645` | **MATCHES** | I-60. |
| AMENDMENT-5 units field in pin | `freeze_and_pin` MDE_UNITS sites | **MATCHES** | I-62. |
| §0 DESIGN/CONFIRM only; frozen hashes | `fences.py:49-52,43-45`; all entry `assert_frozen_inputs` | **MATCHES** | TEST not in choices; holdout raises; hashes `1b7244c8…` / `e3b9fd9b…`. |
| §0 Stage I — no edge claims | race/freeze scope strings; CALIBRATION_ONLY wrappers | **MATCHES** | Parameters only. |

### Golden-trace / freeze dry-read

- GT-1/GT-2 construction code (`sessions.py`) not in this revision set; prior exact pins still the authority; unit tests for first-break / IB shift still present.
- I2 artifact on disk: winner A-USOPEN×15, `contrast_median≈0.09997`, tripwire `survives:false` (cf −41.7), plant `survives:true` (cf 0.703, day_corr 0.708) — re-read from `hyp_i2_anchor_race_DESIGN.json`.
- I3 freeze path: with opposite-sign large \|cf\| alone + missing probe → refuses for **missing positive_control**, not for leak (I-59 trap closed). Same-sign material → `"DID NOT COLLAPSE"`.

### Proactive path-swap / fence scan (beyond I-56 cluster)

| Scan | Result |
|---|---|
| Other poke/bar name collisions (`ib_high`/`ib_low` on bars) | Production bars from `attach_sessions` do not carry IB edges; `_bars_join_pokes` would drop them if present. |
| `find_pokes` join when bars already have `session_end` | Left/right values equal (same anchor table); not a path-swap seam. |
| Soft control still label-deranges within days | By design (report layer); distinct from HARD path swap. |
| Under-run donor horizons | Truncate only (no pad); shorter window kept and labelled; empty → `n_no_donor_path`. Acceptable under design "truncate/pad **or** drop and publish". |
| Uniqueness after multi-window splice | Sessions disjoint per symbol; uniqueness asserted. |
| TEST / holdout contact | No `"TEST"` band path; `assert_band` holdout-first. |
| New silent magnitude-only I3 path | None found; both emitter and freeze go through `adjudicate_i3_survival`. |

### Governance & boundary

- Bands: DESIGN/CONFIRM only; holdout sealed; 0 counted TEST reads.
- `check_no_local_accounting` (static equivalent): **ok** on `experiments/INFR-018/code` and `src/xen/sigbar`. Registry still calls the live helper at `freeze_and_pin:541-548`.
- No Nautilus strategy backtest; no P&amp;L primitive; L-29/L-30/L-31 N/A.
- L-28 derangement: I2 pseudo-anchors + I3 path-swap both asserted fixed-point free among permutable.
- L-32: interpretation bands remain labels; no `pass` field dropping candidates.
- Frozen inputs contracted `1b7244c8…` / `e3b9fd9b…` at every entry point.
- Stage I discipline: scope strings and CALIBRATION_ONLY wrappers intact.
- No freeze/pin executed this run.

### Issues

None blocking. Residual process note (not a design/code defect):

**N-1 — PROCESS — live pytest not re-run in this subagent.** Cache nodeids include all five path-swap tests; lastfailed has none of them. Operator (or a session with a process runner) should execute
`python/.venv/bin/python -m pytest python/tests/test_sigbar_infr018.py -q`
once before treating APPROVE as the final pre-execution attestation if desired. Does **not** reopen I-56..I-66 on code review grounds.

### Routing

- **Operator execution gate:** APPROVE for pre-execution. HYP-I3 DESIGN race may be run when ready; `freeze_and_pin.py a6` still waits for a clean race artifact + this approval chain. `freeze_and_pin.py anchor` remains independently freezeable on the existing I2 artifact (tripwire + plant still sound by re-read).
- **Not routed — closed this run:** I-56, I-57, I-58, I-59, I-60, I-61, I-62, I-63, I-64, I-65, I-66.

### What a freeze would do today (mechanical, not authorisation)

- `freeze_and_pin.py anchor`: still should pass on the on-disk I2 artifact (opposite-sign null + surviving plant + full universe + cosmetic spot-check).
- `freeze_and_pin.py a6`: still needs a HYP-I3 race artifact; the destroy that would feed it is now well-formed (full permutable coverage, same-symbol derangement, restricted S_raw, sign clause, uniqueness) rather than the calendar-ordered half-population destroy of run 7.
- `freeze_and_pin.py registry`: still requires a6 + i4 artifacts; accounting and DESIGN-universe checks remain hard.
