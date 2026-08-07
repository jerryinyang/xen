# SPDR-014 — QA review

## QA run 1 — 2026-07-24T (UTC) — mode: subagent — HEAD 43458484383b477e59f5b1e5cdbccf18b5ff5ae8

Reviewed git state: dirty tree (SPDR-014 untracked results/, screen_code/; design.md modified). This is a
**post-hoc design→code fidelity + integrity audit** at operator direction — the screen already executed
(TRAIN run complete, `integrity_selfcheck.all_pass=true`, `residual_status=NONE`, `016_start_allowed=false`).
Files read: design.md, all of screen_code/*.py, results/{integrity_selfcheck,golden_traces,universe_pin_check,
run_summary,zvol_scale,controls}.json, docs/references/spdr-lane.md, KB lessons. `analysis.md`/`screen.md`/
`_archive_v1/` deliberately NOT read (independent re-analysis in progress).

**Verdict: REVISE**

The HARD integrity firewall is fully enforced in code and the negative headline (`NONE` / no 016 start) is
conservative and unaffected by the findings below. The REVISE is for **null/control-battery form defects** that
weaken the attribution nulls the fresh-context analysis will consume — not for any leak, causality, or fence
breach. See Issues 1–5.

---

### Design-fidelity trace (HARD clauses first)

| # | Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|---|
| 1 | TRAIN-only fence; exit open < train_end 2023-12-18; no TEST/holdout load (§0, §7 HARD, §10.1) | `catalog_io.py:57` assert_within_fence(band=TRAIN); `:89-90` min≥start/max<end; load end=CONFIRM_END=train_end (`config.py:41`); exit gate `engine.py:120` (residual), `:198` (policy), `:220` (straddle); `run_screen.py:558-565` post/money exit_ts<train_end | **MATCHES / ENFORCED** | Data never loaded past train_end; exit checked at three sites + a global sweep. |
| 2 | Causal t-1: features/width ≤ t; anchor=open[t+1]; breach entry=open[j+1]; residual exit=open[entry+h]; stop ATR at entry−1 (§2.1, §4.1, §5) | features `engine.py:296-303` (sigma at t, anchor=open[t+1]); breach entry `engine.py:112` entry=event_idx+1; exit=entry+h `:113`; stop atr_e=`atr_lag[entry]`=atr[entry-1] `engine.py:159` + `prepare.py:62` | **MATCHES / ENFORCED** | No own-bar-close used as a limit/decision. Open-to-open throughout. |
| 3 | Z-VOL unit pin: Parkinson on completed H1, EWMA λ=0.94 causal, s_symbol frozen on first-60 DESIGN warm-up then reused; no post-warm-up refit (§2.2) | `indicators.py:19` Parkinson; `:28-40` causal EWMA λ=0.94 (`config.py:70`); `freeze_zvol_scale :52-70` first `ZVOL_WARMUP_BARS=60` DESIGN origins; `prepare.py:78-80` freeze once; H4 reuses `pack.s_symbol` `run_screen.py:270`; s emitted `zvol_scale.json` | **MATCHES / ENFORCED** | No refit after warm-up. Symbols with no DESIGN data → s=NaN → Z-VOL correctly unavailable (no look-ahead fill). G1 confirms EWMA+band to 1e-9. |
| 4 | Universe pin equality — recompute top-25 and assert equality (§0 AMENDMENT-U1) | `universe.py:79-99` assert_pin raises UniversePinMismatch on set≠; checks BOTH family + results pins; `run_screen.py:463-467` | **MATCHES / ENFORCED** | `universe_pin_check.json` set_equal_all=true. |
| 5 | Matched-control + ≥200-seed battery, percentile read (§7, §9; L-19) | seeds=200 `config.py:146-149`; percentile reads `controls.py:113,171,215` | **MATCHES (floor)** | Floor 200 met; design "prefer 2000" not taken. **Exception:** gate_label_shuffle uses `GATE_SHUFFLE_SEEDS[:50]` (`controls.py:201`) — 50 < 200. Minor. |
| 6 | Dependence-matched CI, block ≥ H on overlapping windows (spdr-lane HARD; Phase-010) | `stats_core.py:99-105` aggregate r_h by calendar date, then block bootstrap blocks {1,3,7} days `config.py:131`; posts non-overlapping by construction (`engine.py:371-382` busy_until) | **MATCHES / ENFORCED** | Forward window h≤24 H1 = 1 day; min block = 1 day ≥ H, plus 3/7-day blocks; CI = min/max envelope across blocks×seeds (conservative). No block=5-bar understatement trap. |
| 7 | No local accounting primitives mimicking xen.adjudication (spdr-lane HARD; L-18) | `costs.py:6-11` uses `xen.evaluation.bybit_fee_bps_per_side` + `count_bybit_funding_stamps`; partial_net = bps gross − fee − funding − allowance (`:20-36`) | **MATCHES** | Analyst-style bps cost injection, no equity curve / MTM / position-netting engine. Money is secondary/informative, not headline. |
| 8 | Derangement destroy forms (§7; L-28) | time_shuffle `controls.py:100-103`; matched_random `:159`; gate_label_shuffle `:205`; path_future_destroy `:238-242` | **PARTIAL / GAP** | See Issues 1–3. time-shuffle = soft-derangement (5 retries then fallback); gate-label = **plain shuffle mislabeled DERANGEMENT**; tripwire = mean-invariant P&L permute + random signs, not causal within-third path re-pair; matched-random = random sampling (derangement N/A, but omits the §7 "exclude live anchors ±1 H1" clause). |
| 9 | O3-SOT: no signed vol×direction product; shock never a regime; both MOMO+MR always emitted; straddle never sole headline (§A, §10) | side derives from breach path only (`engine.py:99-103`), not a signed product; shock_flag only a conditioner (`engine.py:321`); p_momo & p_mr computed every cell (`run_screen.py:91-92`); straddle → secondary `straddle.parquet` | **MATCHES / ENFORCED** | integrity flags all true; consistent with headline. |
| 10 | Golden traces G1–G4 reconcile to emission; code non-vacuous (§10) | `golden_traces.py` G1-G4; results all pass | **MATCHES** | G1 EWMA+band 1e-9; G2 residual entry=j+1 & r_h; G3 Z-MAG ineligibility before first forecast; G4 cost reconcile. Minor vacuity: G1 reuses frozen s (doesn't re-derive warm-up freeze); G4 checks cost arithmetic, not that the 1.5-ATR stop actually fired. Adequate. |

### Design-fidelity trace (other clauses, condensed)

| Design clause | Code | Verdict | Notes |
|---|---|---|---|
| §2.3 band geometry z∈{1,1.5,2}, upper/lower, centre=anchor | `engine.py:55-57,307` | MATCHES | |
| §3 E-TOUCH side tie-break by farther extreme; E-CLOSE; E-HORIZON; UNDECIDED counts in rate, excluded from residual | `engine.py:60-108`; undecided side=0 → residual None `:116`; posts require side≠0 | MATCHES | |
| §4.2 labels MOMO/MR/FLAT with c=5 bps deadband | `engine.py:139-144`; `config.py:89` | MATCHES | |
| §5 stop 1.5×ATR; costs fee 11 + funding 1×stamps + allowance 2 per leg; spread null | `config.py:90,117-119`; `costs.py`; `engine.py:162` | MATCHES | fee_rt asserted == 2×taker schedule (`costs.py:10-11`). |
| §5/§6 money subset P-MOMO/P-MR on E-TOUCH×h=12×z=1.5×{Z-VOL,Z-MAG} | `config.py:95-103`; `run_screen.py:215-240` | MATCHES | zone H=12 chosen per IN-1 (design silent on money zone H; narrowing, declared). |
| §6 straddle Z-VOL z=1.5 H∈{4,12,24} disclosure | `run_screen.py:243-267` | MATCHES | |
| §6 H4 co-report single slice | `run_screen.py:269-286`; `config.py:106-108` | MATCHES | H4 reuses frozen s from H1 pack. |
| §8.1 residual bands (labels never gates) | `stats_core.py:112-128` | MATCHES | UNPOWERED/WASH/SUPPORTED/CONTRADICTED thresholds match config. |
| §8.3 residual pin artifact even if null; 016_start only if status≠NONE AND ≥1 powered cell | `run_screen.py:304-410`; result NONE/false | MATCHES | |
| §0 SPREAD-COST-DISCLOSURE UNAVAILABLE_NOT_CHARGED / null / PARTIAL | `config.py:121-127`; propagated to pin + integrity | MATCHES | No fully-net/tradable/deployable claim in emissions. |
| §13 DEVIATIONS empty; IN-1/IN-2 interpretation notes | `config.py:164-184` | MATCHES | Both notes are narrowings ("may_narrow: YES"), not thinnings; declared. |

### Golden-trace diff (expected from DESIGN vs implemented)

| Trace | Expected (design §10) | Implemented | Verdict |
|---|---|---|---|
| G1 BTC Z-VOL band | hand Parkinson+EWMA λ=0.94+frozen s → upper/lower match 1e-9 | `g1_zvol_band` reconstructs park+ewma over [:t+1], compares band to 1e-9 rel; PASS (s=6384.32, σ=40.31 bps) | MATCHES (frozen-s freeze itself not independently re-derived — minor) |
| G2 ETH E-TOUCH | breach upper only; side=+1; entry=next open; r_12 hand | synthetic pack; r_h_hand==r_h_engine=69.79; entry=j+1 confirmed | MATCHES |
| G3 SOL Z-MAG | one confirmed swing → width; ineligible if none | first_eligible_idx=479, early_all_nan=true | MATCHES |
| G4 AVAX P-MR | against-side entry, 1.5 ATR stop, net=gross−11−fund−2 | gross −263.58 → net −277.58 reconciles | MATCHES (cost only; stop-fire not asserted — minor) |

### Governance & boundary

- SPDR lane: TRAIN-only, disposition-only, no family action, no XENA, no estimand gate — all respected.
- No-local-accounting: PASS (xen.evaluation toolbox; no adjudication clone).
- Spread disclosure: UNAVAILABLE_NOT_CHARGED / spread_rt_bps null / PARTIAL_FEES_FUNDING_ONLY present in
  config, integrity, and pin; no tradable/deployable/cost-complete claim in any emission.
- Amendment ledger (§13): S1 NEUTRAL, 0 looser / 0 tighter / 1 neutral. No ≥3 one-directional streak. OK.
- Multiplicity disclosed: `run_summary.json` grid + 8450 cell rows.
- O3-SOT map (§A) present; no signed product; shock not regime; straddle secondary. PASS.
- Holdout/TEST: no code path loads past train_end (load fence + per-exit gate). PASS.

### Issues

1. **[REVISE — L-28] gate_label_shuffle uses a plain permutation but is labeled DERANGEMENT.**
   `controls.py:205` `rng.shuffle(shuf)` (naive) while `controls.py:219` and `run_screen.py:532` report
   `destroy_form/class = "DERANGEMENT"`, and `controls.json` propagates the DERANGEMENT tag. A plain shuffle
   leaves fixed points and leaks the live label→residual pairing (VAL-008). Required change: regenerate/reject
   until zero fixed points (or swap-repair), then the DERANGEMENT label is truthful. Class is informative
   (conditioner non-vacuity), so no HARD breach — but the label is currently false.

2. **[REVISE — minor] time_shuffle_event is a *soft* derangement.** `controls.py:100-103` retries at most 5×
   for zero fixed points, then falls back to a possibly-fixed-point permutation. For small per-third pools this
   can silently leave fixed points, contaminating the null toward live. Required change: loop until zero fixed
   points (bounded swap-repair) rather than a 5-try give-up.

3. **[REVISE — design-fidelity] PATH-FUTURE-DESTROY tripwire is a mean-invariant P&L permute, not the designed
   causal path re-pair.** Design §7 specifies "derange future path pairing within symbol×third"; code
   (`controls.py:238-242`) shuffles already-netted `partial_net` values and multiplies by random ±1 signs.
   Shuffling realized P&L cannot collapse a mean stat (EXP-012 lesson); the random-sign flip produces a null
   centered ≈0 with a positive p95. Design pre-classes this INFORMATIVE (T1/DEV-1) and it **did not fire** this
   run (live mean −13.6 bps < null_p95 +8.9; `survives_above_p95=false`), so the HARD applicability clause was
   never engaged and the headline is unaffected. Still, the tripwire is weaker than specified. Required change:
   re-pair each event's entry with a *foreign future path* (open[entry']→open[entry'+h]) drawn as a
   within-third derangement, then recompute partial_net causally.

4. **[REVISE — minor] matched_random_anchor omits the §7 DISJOINT clause.** Design: "exclude live anchors
   ±1 H1"; `controls.py:156-159` samples from the full band range without excluding live-event neighborhoods.
   Low practical impact (random draw rarely lands adjacent) but the disjointness guarantee is not coded.

5. **[REVISE — minor] gate_label_shuffle seed count below the random-control floor.** `controls.py:201`
   `GATE_SHUFFLE_SEEDS[:50]` uses 50 seeds; §9 sets a 200 floor for random controls. Raise to ≥200 (the tuple
   already holds 200) unless a lower floor is justified for a non-vacuity check.

**Impact statement (per operator's post-hoc framing):** None of Issues 1–5 touches the HARD firewall (TRAIN
fence, causal t-1 lag, Z-VOL unit/freeze pin, universe pin, block≥H CI, no-local-accounting, golden traces —
all ENFORCED). The residual pin delta feeding `014_residual_pin.json` uses the **matched-random** null (valid
random sampling), and the headline is `residual_status=NONE / 016_start_allowed=false` — a conservative
negative that the control-form defects cannot flip. Therefore the **emission core is trustworthy** and the
disposition is safe. The caveat for the independent re-analysis: do **not** read the `time_shuffle`,
`gate_label_shuffle`, or `path_future_destroy` null percentiles at face value until Issues 1–3 are fixed —
those specific nulls may sit slightly closer to live than a true derangement/causal-repair would place them.

---

## QA run 2 — 2026-07-24T01:24:34Z (UTC) — mode: subagent — HEAD 43458484383b477e59f5b1e5cdbccf18b5ff5ae8

Reviewed git state: dirty tree (SPDR-014 untracked `results/`, `screen_code/`; `design.md` modified). This is a
**re-verification run**: QA run 1 returned REVISE (Issues 1–5, control-battery form); the developer applied fixes,
found + fixed an additional residual-pin builder bug, added a last-k Markov facet, and parallelised the runner.
Screen was re-run (`integrity_selfcheck.all_pass=true`). Append-only. Files read: design.md, QA run 1, all of
`screen_code/{controls,run_screen,engine,config}.py`, `results/{integrity_selfcheck,golden_traces,014_residual_pin,
controls}.json` + `{post_event,expectancy_by_cell}.parquet`, spdr-lane + KB. `analysis.md`/`screen.md`/`_archive_v1/`
NOT read. Independent checks run: derangement fixed-point/termination battery, per-cell MDE cross-check, artifact
column/field reads.

**Verdict: APPROVE**

All five QA run 1 control-battery defects are correctly fixed, the newly-found residual-pin "powered" bug is
correctly fixed (the mislabeled cell can no longer arise — the full §8.1 gate is enforced and the whole grid is
structurally UNPOWERED), the last-k Markov facet is causal and emitted, and the parallel runner cannot change any
estimand. The HARD firewall from run 1 is intact and unregressed. **The corrected emission is trustworthy for the
neutral analyst to finalize on** — with one non-blocking labeling caveat (item 6) to carry into the write-up.

### Per-item verification table

| # | Fix (task ref) | Code (file:line) | Evidence | Verdict |
|---|---|---|---|---|
| A1 | `_derangement` zero fixed points; terminates for n=2; identity for n<2 | `controls.py:17-31` | Rejection sampling (redraw full permutation until no fixed point); P(derangement)→1/e so ~e draws, independent → always terminates. Verified empirically: n∈{2,3,5,10,50}, 2000 draws each, zero fixed points; n=0→[], n=1→[0]. n=2 cannot loop (perm [1,0] drawn w.p. 0.5). | **VERIFIED** |
| A2 | `time_shuffle_event` true derangement (not 5-try give-up) | `controls.py:120-125` | `perm=_derangement(rng,len(pool))`; each event's own side re-paired to a foreign event index via `residual_r_h(pack, foreign_idx, sides[i], h)`. `destroy_form="DERANGEMENT"`; `controls.json` n_seeds up to 200. | **VERIFIED** |
| A3 | `gate_label_shuffle` true derangement + ≥200 seeds | `controls.py:228-235` | `for seed in GATE_SHUFFLE_SEEDS` (no `[:50]` slice); `perm=_derangement(rng,n)`; `GATE_SHUFFLE_SEEDS`=200 (`config.py:148`). `controls.json` destroy_form=DERANGEMENT (None only for empty-`live_p` symbols that early-return n=0). | **VERIFIED** |
| A4 | `matched_random_anchor` excludes live anchors ±1 (§7 DISJOINT); filtered once | `controls.py:168-176` | `live_event_idx={entry_idx-1}`; `excluded_pseudo={ev-1,ev,ev+1}`; `candidates=[t0 … if (t0+H) not in excluded_pseudo]` built once outside the seed loop. `disjoint_excl_live_pm1=True` for all 25 symbols; `n_candidates` emitted. | **VERIFIED** |
| A5 | `path_future_destroy` = within-third foreign-path re-pair, causal `simulate_policy`; not mean-invariant shuffle | `controls.py:278-291` | `perm=_derangement(rng,m)` per third; each live trade keeps own `trade_side`+`h`, re-paired to `foreign_entry`; `simulate_policy(pack, foreign_entry, trade_side, h)` recomputes partial_net causally (stop + cost). `destroy_form="DERANGEMENT_CAUSAL_PATH_REPAIR"`; `survives_above_p95=false` for all symbols; `integrity.tripwire_hard_fail=false`. | **VERIFIED** |
| B6 | `build_residual_pin` enforces FULL §8.1 SUPPORTED-residual (adds MDE≤10, median-sign, thirds≥2) | `run_screen.py:358-377` | `powered = n_decided≥80 AND n_dates≥30 AND mde≤10`; MOMO branch adds `delta≥5 AND ci_low>0 AND median≥0 AND thirds≥2` (MR mirror). Emitted pin: `n_powered_momo=0`, `n_powered_mr=0`, `016_start_allowed=false`, `policy_for_016=NONE`. Cross-check: 0/175 primary cells meet the powered gate (min MDE among n≥80 cells = 34.1 bps ≫ 10); whole 8450-cell grid = UNPOWERED. The run-1 tail-cell mislabel is structurally impossible now. | **VERIFIED (see note)** |
| C7 | `_last_k_high` causal + IN-3 note + emitted columns | `engine.py:389-396`; `config.py:184-195`; `run_screen.py:200,336` | `lo=max(0,t-k+1); w=regime[lo:t+1]` — counts HIGH slow_regime bars ≤ t (causal, includes t, no look-ahead). `post_event.parquet` has `last_k_high_4`,`last_k_high_12`; bounds verified k4∈[0,4], k12∈[0,12], k4≤k12 all rows. IN-3 declares the slow_regime==HIGH-Markov reading, `weakens_clause=false`. | **VERIFIED** |
| D8 | Parallel spawn Pool; deterministic; no estimand/order change; TIMING stdout-only | `run_screen.py:525-557,137-138` | Symbols fully independent; control seeds are module constants (`config.py:146-149`), RNG `default_rng(seed)` proc-independent; engine/prepare deterministic. `imap_unordered` results keyed by `res["symbol"]`, re-aggregated in `for sym in symbols` (universe order) → row order fixed regardless of proc count. `[TIMING]` via `print(flush=True)`, never written to an artifact. Re-run: `integrity_selfcheck.all_pass=true`, `golden_traces.all_pass=true`. | **VERIFIED** |
| E | HARD firewall regression (run-1 ENFORCED clauses) | see run 1 table rows 1–4,6,7,9,10 | Fixes touch only control-battery form, a report-layer pin, a strata column, and process orchestration — none touch engine causality, TRAIN fence, Z-VOL freeze, universe pin, block≥H CI, no-local-accounting, or O3. `integrity_selfcheck`: universe_pin_equal=true, golden_traces_pass=true, train_fence_asserted=true, o3_sot_path_present=true, no_signed_product/shock_not_regime/straddle_not_headline/both_momo_mr_emitted all true. Golden G1–G4 all pass (band 1e-9, entry=j+1, Z-MAG ineligibility, cost reconcile). | **VERIFIED / no regression** |

### Golden-trace diff
Unchanged from run 1 and re-confirmed on the re-run: G1 (BTC Z-VOL band, s=6384.32, σ=40.31 bps, band match 1e-9),
G2 (ETH E-TOUCH side=+1, entry=next open, r_12=69.79), G3 (SOL Z-MAG first_eligible_idx=479, early_all_nan),
G4 (AVAX P-MR gross −263.58 → net −277.58) — `all_pass=true`.

### Governance & boundary
- SPDR lane TRAIN-only, disposition-only, no family/XENA/estimand action — respected.
- No-local-accounting: costs via `xen.evaluation`; no adjudication clone (unchanged).
- Spread disclosure UNAVAILABLE_NOT_CHARGED / null / PARTIAL present in config, integrity, pin; no
  tradable/deployable/cost-complete claim in any emission.
- Derangement destroy (L-28): all four permutation arms (time-shuffle, gate-label, tripwire, and the
  time-shuffle side re-pair) now use the shared rejection-sampling `_derangement` — zero fixed points. **Run-1
  Issues 1–3 closed.**
- Seed battery / MDE floor (L-19, B-5): all four batteries = 200 seeds; UNPOWERED discipline now enforced in the
  pin builder (MDE≤10 gate) — UNPOWERED cells no longer graduate to "powered". Consistent with the whole-grid
  UNPOWERED disposition.
- Amendment ledger (§13): unchanged (S1 NEUTRAL; 0 looser / 0 tighter / 1 neutral). No ≥3 streak.

### Issues (non-blocking notes carried to the analyst)

**N-1 [NOTE, not a code REVISE] — mechanical `residual_status="MOMO_DOMINANT"` while `016_start_allowed=false`.**
`run_screen.py:412-423`: with zero powered residual cells, the builder falls to the rate-lean path
(`rate_momo=18` MOMO_RATE vs `rate_mr=7` MR_RATE; 18 > 7×1.5 → MOMO_DOMINANT) but correctly sets `start=false`,
`policy_for_016=NONE`, `n_powered_momo=n_powered_mr=0`. The binding gate is therefore safe and correct. The
caveat is *labeling*: since the entire grid is UNPOWERED and no residual cell is SUPPORTED, the truthful residual
disposition is "UNPOWERED / no SUPPORTED residual"; `MOMO_DOMINANT` here reflects only a **rate lean**
(§8.1 rate-only note: "may be SUGGESTIVE without residual SUPPORTED"), not a residual finding. The analyst's
write-up must state plainly that this is a rate lean, that no powered residual exists, and that 016 stays closed —
and should not let a downstream reader key on `residual_status` alone. Recommend the analyst either annotate the
status as rate-lean/SUGGESTIVE or keep it with an explicit "no powered residual" qualifier.

**N-2 [NOTE] — pin CI/median objects are proxies, not paired-Δ.** `run_screen.py:356-357,368-370`: `ci_low`/`ci_high`
are the block-bootstrap CI on the **raw cell mean r_h** (not on Δ vs control), and the median check uses the raw
`median_r_h` (not median Δ). The code comment acknowledges this. It never bites this run because no cell clears
the MDE≤10 gate, so the powered branch is unreachable. If any future re-run produces a powered cell, the paired-Δ
block-bootstrap CI on Δ must be substituted before asserting SUPPORTED. Flagged for the analyst / a future 016 gate.

**Impact:** Neither note touches the HARD firewall or the negative disposition. Run-1 Issues 1–5 are fully
resolved; the residual-pin bug is resolved; the added facet and parallelism are integrity-neutral. The emission
core (`016_start_allowed=false`, `n_powered=0`, whole-grid UNPOWERED, integrity all_pass) is trustworthy for the
neutral analyst to finalize on.

---

## QA run 3 — 2026-07-24T02:26:33Z (UTC) — mode: subagent — HEAD 43458484383b477e59f5b1e5cdbccf18b5ff5ae8

Reviewed git state: dirty tree (SPDR-014 untracked `results/`, `screen_code/`; `design.md` modified). This is an
**append-only re-verification** scoped to two changes made AFTER QA run 2 (APPROVE) plus a no-regression sweep:
(A) AMENDMENT-S2 — the last-k conditioner corrected from a HIGH-count to the ORDERED slow-regime label sequence
(O3 conflict rule, O3 substance > design); (B) the residual-pin builder made honest (no more mechanical
`MOMO_DOMINANT` when 0 powered cells — the QA run 2 N-1 caveat). Screen was re-run (parallel; single 03:13
emission; `integrity_selfcheck.all_pass=true`). Files read: design.md (§4.4, §13), `screen_code/{engine,config,
run_screen}.py`, `controls.py` (unchanged since 02:06, before A/B at 03:02/03:10), `results/{014_residual_pin,
integrity_selfcheck,golden_traces,controls}.json` + `{zones,events,post_event,expectancy_by_cell}.parquet`, O3
SoT §2.1/§2.2 (lines 102/133). Independent checks: string-convention + causal-consistency battery on 749,456
zone rows; full residual-pin recompute from emitted cells+controls; column/stale-reference sweep. `analysis.md`/
`screen.md`/`report.md` cross-read for numbers only; `_archive_v1/` NOT read.

**Verdict: APPROVE**

AMENDMENT-S2 is faithfully implemented and genuinely O3-consistent (not a rationalisation); the pin builder is now
honest and bit-reproducible from the emission; no regression to the HARD firewall or the run-1/2 fixes; the S2
change is estimand-neutral by construction. The corrected emission + amended design are trustworthy and
self-consistent. One non-blocking ratification note (B8) is carried to the operator.

### Per-item verification table

| # | Item (task ref) | Code / emission (file:line) | Evidence | Verdict |
|---|---|---|---|---|
| A1 | design §4.4 + §13 AMENDMENT-S2 describe ordered-sequence conditioner, K∈{1,2,3}, chronological (decision bar = last char), causal ≤t, recorded NEUTRAL | `design.md:228` (§4.4 row), `:463-477` (S2 block) | §4.4 reads "**Ordered** slow-regime label sequence over the last K∈{1,2,3} bars (chronological oldest→newest … decision bar = last char, causal ≤t)". §13 S2 dated 2026-07-24, DIRECTION NEUTRAL, replaces count columns, running count `0 looser / 0 tighter / 2 neutral (S1,S2)`. No ≥3 one-directional streak. | **VERIFIED** |
| A2 | `_last_k_state` = ordered label string oldest→newest, last char = bar t, H/L/?=NaN, left-padded, causal | `engine.py:391-403` | `lo=max(0,t-k+1); w=regime[lo:t+1]`; chars `H` if 1.0 / `L` if 0.0 / `?` else; `pad="?"*(k-len)` prepended. String convention matches design text exactly. | **VERIFIED** |
| A3 | `last_k_state_1/2/3` emitted on zones + events + post_event; old `last_k_high_4/12` fully removed | `engine.py:321-323` (zones), `:337` (events), `run_screen.py:192` (posts) | All three parquets carry `last_k_state_1/2/3`; **zero** `last_k_high` columns in any parquet; `grep last_k_high screen_code/` = NONE. No stale references. | **VERIFIED** |
| A4 | `config.py` IN-3 declares the reading + supersession | `config.py:185-197` | IN-3: HIGH/LOW == slow_regime (V-REGIME), ordered sequence per AMENDMENT-S2, K∈{1,2,3}, causal ≤t, "Supersedes the earlier count-of-HIGH (K∈{4,12}) reading", emitted on zones/events/post_event, `weakens_clause=false`. | **VERIFIED** |
| A5 | Causal spot-check: state uses only bars ≤ decision bar; slice `regime[max(0,t-k+1):t+1]` | `engine.py:399-400`; 749,456-row battery | Slice inclusive of t, nothing beyond t. On real data: `k1`=1 char, `k2`=2, `k3`=3; `k1 == k2[-1] == k3[-1]` (last char = decision bar); `k2 == k3[-2:]` (nested, all end at t); `k1` equals the decision bar's own `slow_regime` label for **all** rows → last char is bar t, no future leak. K3 shows all 8 patterns HHH…LLL. | **VERIFIED** |
| B6 | With 0 powered cells → `residual_status=NONE`, `policy_for_016=NONE`, `016_start_allowed=false`; `*_DOMINANT`/`SPLIT` reachable only when ≥1 powered cell; full §8.1 gate (MDE≤10, \|Δ\|≥5, CI-excl-0, median-sign, thirds≥2) intact | `run_screen.py:347-405` | Status branch: `n_m>0`/`n_r>0` → DOMINANT/SPLIT + start=True; else `NONE`/start=False (`:398-405`). Powered gate `:347-351` = n≥80 AND n_dates≥30 AND MDE≤10; MOMO/MR branches `:354-363` add Δ≥5/≤−5, ci_low>0/ci_high<0, median-sign, thirds≥2 — unchanged from run-2 §8.1 enforcement. Rate labels feed only `rate_*`, never `powered_*`. | **VERIFIED / no regression** |
| B7 | Emitted pin shows NONE/false/0/0/MOMO_SUGGESTIVE/18/7; code-generated + stable | `results/014_residual_pin.json`; recompute | Pin: `residual_status=NONE, 016_start_allowed=false, n_powered_momo=0, n_powered_mr=0, rate_lean="MOMO_SUGGESTIVE", n_rate_momo_suggestive=18, n_rate_mr_suggestive=7`. Independent recompute of `build_residual_pin` logic from `expectancy_by_cell.parquet`+`controls.json` (150 primary cells) reproduces **exactly** 0/0/18/7/NONE/false → pure deterministic function of the emission, not a hand-patch. `rate_lean="MOMO_SUGGESTIVE"` because 18 > 7×1.5. | **VERIFIED** |
| B8 | Is forcing NONE-when-0-powered design-consistent? | `run_screen.py:398-405`, design §8.3 | Faithful **tightening**, not a deviation: design §8.3 gate already reads "016_start only if status≠NONE AND ≥1 powered cell", so residual_status was always meant to track the powered residual object; the old builder produced the self-contradictory `MOMO_DOMINANT`+start=false state (run-2 N-1). New rule ties status to powered cells and demotes the rate lean to disclosure (`rate_lean`/`n_rate_*`), aligning with O3 "do not assume MOMO or MR". Binding gate outcome unchanged (start=false either way). **Ratify-worthy disclosure** (changes semantics of an emitted field a 016 reader may key on) but within `may_narrow: YES` latitude — see note. | **VERIFIED (ratify-worthy, non-blocking)** |
| C9 | No regression: integrity + golden all_pass; HARD firewall + run-1/2 fixes hold; S2 estimand-neutral | `integrity_selfcheck.json`; `controls.py`; grep | `integrity all_pass=true` (universe_pin_equal, golden_traces_pass, train_fence_asserted, o3_sot_path_present, tripwire_hard_fail=false all correct); `golden_traces all_pass=true`. `controls.py` (02:06) + `costs.py` (00:14) **untouched** by A/B (engine/config 03:02, run_screen 03:10) → run-2 rows A1–A5/C7-costs carry forward: `_derangement` rejection-sample, matched-random ±1 exclusion (`excluded_pseudo`, `disjoint_excl_live_pm1=True`), causal tripwire (`DERANGEMENT_CAUSAL_PATH_REPAIR`), block≥H CI, no-local-accounting all intact. **S2 estimand-neutral**: `last_k_state` is only written into zone/event/post dicts, never read by `summarise_posts`/`band_residual`/`residual_r_h`; primary-cell mean_r_h / p_momo / MDE therefore identical to pre-S2 (recomputed rate_momo/mr require populated estimands → confirmed live). | **VERIFIED / no regression** |

### O3-consistency (A1/A2 substance)
O3 SoT line 102 conditions on "**last-k states**" (plural = a sequence, not a scalar); line 133 lists
"**run-length**" as an estimand of interest; line 53/132 fix the label alphabet to the **slow Markov / rv20 level
regime** (== `slow_regime`). The original design reading ("count of HIGH Markov bars in last K") discards **both**
order and run-length that O3 explicitly cares about. The amended ordered-label-sequence conditioner preserves
both and uses the correct alphabet → AMENDMENT-S2 is a genuine O3 correction under `conflict_rule: O3 substance >
design`, not a post-hoc rationalisation. Operator-directed K∈{1,2,3} (vs design's {4,12}) is a declared narrowing
(§13: keeps every pattern analysable; K=12 raw ≈ all singletons) — consistent with `may_narrow: YES`.

### Golden-trace diff
Re-confirmed on the post-S2 re-run: G1 (BTC Z-VOL band 1e-9), G2 (ETH E-TOUCH side=+1, entry=next open,
r_12=69.79), G3 (SOL Z-MAG ineligibility), G4 (AVAX P-MR cost reconcile) — `all_pass=true`. Unchanged by A/B
(golden_traces.py untouched; S2 adds no golden-covered logic).

### Governance & boundary
- SPDR lane TRAIN-only, disposition-only, no family/XENA/estimand action — respected.
- Spread disclosure UNAVAILABLE_NOT_CHARGED / null / PARTIAL present in config, integrity, pin; no
  tradable/deployable/cost-complete claim.
- Amendment ledger (§13): S2 NEUTRAL correctly recorded; running count 0/0/2. No ≥3 one-directional streak.
- Derangement destroy (L-28): all four permutation arms unchanged and intact (controls.py untouched).
- Column sweep: no `last_k_high` residue in code or any of the 3 parquets; new columns present on all three.

### Issues (non-blocking notes to the operator)

**R3-1 [RATIFY, not a REVISE] — NONE-when-0-powered semantics of `residual_status`.** The pin now sets
`residual_status=NONE` whenever `n_powered_momo + n_powered_mr == 0`, demoting the per-cell rate lean to the
disclosure fields `rate_lean`/`n_rate_momo_suggestive`/`n_rate_mr_suggestive`. This is design-consistent with the
§8.3 gate ("016_start only if status≠NONE AND ≥1 powered cell") and resolves the run-2 N-1 contradiction, and does
**not** change any binding outcome (016 stays closed either way). It does change the meaning of an emitted field a
downstream 016 reader might key on. Recommend the operator record a one-line ratification (e.g. an IN-4 note or a
line in §8.3) that `residual_status` reflects the **powered residual object only**, rate leans being SUGGESTIVE
disclosure. Optional; the builder's inline comment + `notes` field already state this.

**R3-2 [NOTE, carried from run-2 N-2] — pin CI/median are proxies, not paired-Δ.** Unchanged: `ci_low/ci_high` and
`median_r_h` are on the raw cell mean, not on Δ vs control. Never bites this run (powered branch unreachable — min
MDE ≫ 10). Must be substituted with a paired-Δ block-bootstrap CI before any future powered cell is called
SUPPORTED / any 016 gate.

**Impact:** Neither note touches the HARD firewall or the negative disposition. AMENDMENT-S2 is faithful +
O3-consistent + estimand-neutral; the pin builder is honest + bit-reproducible; no regression. The emission core
(`016_start_allowed=false`, `n_powered=0`, whole-grid UNPOWERED, `integrity all_pass=true`, `golden all_pass=true`)
and the amended design are trustworthy and self-consistent.
