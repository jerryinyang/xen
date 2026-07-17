# QA review — SPDR-005 (CF-EPSOSC-001 TRAIN-only SPDR screen)

Append-only. Precedent format: python/experiments/SPDR-004/qa-review.md.

## QA run 1 — 2026-07-17 — mode: subagent (operator-requested post-execution pass) — HEAD f41ba32
Reviewed state: HEAD f41ba3213784; dirty: docs/references/spdr-pack-{epsosc,htfcap}-001.md,
docs/signal-registry/{cf-epsosc-001,cf-htfcap-001,multiplicity-registry}.md, python/experiments/INDEX.md;
untracked: SPDR-004/, SPDR-005/, SPDR-006/, INFR-014/.
Note: SPDR lane stage 2 is normally code-asserted self-check (no QA subagent); this is an
operator-requested post-execution QA pass. No estimand_validation.json / Nautilus emission by design.

**Verdict: REVISE** (two deviations need operator ratification; promote-facing math itself verified sound)

### Design-fidelity trace

| Design clause (§ref) | Code (screen_code/spdr005_screen.py) | Verdict | Notes |
|---|---|---|---|
| §0 registration precondition, refuse if not REGISTERED | check_registration():106-122; run():1048-1052 exits(2) | MATCHES | Card `REGISTERED` (cf-epsosc-001.md:3); multiplicity row Chapter 04 present |
| §5.1 instrument selection: online daily top-10 trailing 24h volume, lex tie-break, ≤ t−1 | daily_volume_series():195-227 (searchsorted side="left" → closes < ts, strictly ≤ t−1); build_membership():230-255 | MATCHES (membership) | membership.parquet 5217 rows, 77 distinct symbols |
| §5.4 grid symbols "online top-10 / 10" | run():1080-1082 — `primary_syms = mem_days["symbol"].head(10)` (top-10 by TOTAL membership days over full TRAIN) | **DEVIATES** | See Issue 1. Cells computed only on these 10 fixed symbols, not the online 77-symbol member set |
| §5.2 TRAIN fence [2021-06-29, 2023-12-18), band="TRAIN", holdout sealed | load_train_1m():148-189 fenced_bar_query(band="TRAIN") + CloseTime < train_end; simulate 535 censors exit ≥ train_end | MATCHES | integrity item 2: max_exit_ns=1702857000e9 < train_end_ns=1702857600e9; holdout_start 2025-01-08 in fence block, never queried |
| §5.3 Object A/B: anchor rolling median W lagged; stretch \|c−a\|/ATR ≥ k at t−1; VOLARM ATR14/ATR56 ≥ 1.25; market entry open[t] | anchors 311-314 (causal_rolling_median incl. bar i) + a_prev/c_prev/atr_prev shifts 377-379, 389-398; entry at open[t_entry] 540 | MATCHES | Decision at bar t uses closes ≤ t−1, ATR ≤ t−1. Causal by inspection |
| §5.3 clears RET_ANCHOR (re-cross < 0.25·k·ATR or anchor cross), TIME H=W, HYBRID | 494-529; RET_CLEAR_FRAC=0.25:56; h_time=w:430 | MATCHES | Exit priced at open[t_exit] (o2o, §3 formula, line 542) |
| §5.4 frozen grid levels + 640 primary slice | constants 45-59; is_primary_cell():926-932 | MATCHES | Emitted 3240 cells / 640 primary; parquet levels verified: domains {15m,1h}, W {96,192}, k {2.5,3.0}, clear {RET_ANCHOR,HYBRID} |
| AMENDMENT-1 censoring: CENSORED excluded from mean, fraction disclosed, >20% flagged, no silent drop | 496-499, 526-537, 552-560; columns n_censored/censored_frac/censored_flag_gt20 emitted per cell | MATCHES | 94 cells flagged >20%; max censored_frac 0.973 disclosed |
| §3 L-16 episode-native primary, per-event fixed-H disclosure only | R_ep_bps 540-542; `primary_unit="bps_per_episode"` all 3240 rows; `fixed_h_disclosure_only=True` | MATCHES | No fixed-H promote read anywhere |
| §6 Control A: ≥25 seeds {2000..2024}, cadence-matched random entries, same clear/side/non-overlap, no stretch labels for timing | 444-470; battery loop 1215-1230; RAND_SEEDS_PRIMARY = 25 | DEVIATES (partial) | Primary slice: 25 seeds — MATCHES. Non-primary 2600 cells: RAND_SEEDS_DISCLOSURE = 5 seeds (line 68) — see Issue 2 |
| §6 Control B: derangement shuffle, zero fixed points (L-28), must collapse promote cells | make_derangement():275-282 (regenerate-until-derangement + rotation fallback); applied 407-412; per-cell collapse frac 1242-1245 | MATCHES | Runtime self-check n∈{10,50,100,251} lines 1149-1153. Verified in artifact: powered primary CI+ cells n=86, median collapse 0.951, 100% > 0.5 |
| §6 Control C GRID_TWIN (banded + hard inv cap, disclosure) | grid_twin_bps():731-767; separate grid_twin.parquet | MATCHES | Not in treatment table; is_grid_twin flag |
| §2.2 P-10 market-only; §5.4 P-12 ban in treatment | no limit/passive fill path; static scan 1161-1168 | MATCHES | Fill = next-bar-open market semantics only |
| §5.5 VR facet lags {2,4,8,16} per instrument×domain | variance_ratio():713-725; loop 1133-1146 | MATCHES | vr_facet.parquet emitted; coupling applied by analyst |
| §8 L-20: block rule, seed range, block sensitivity | summarize_episodes():595-650 — block=1 (episode-level, design §8 option "block by episode") + block_h = median duration sensitivity + ci_low_seed_range (3 seeds); lift CI two-sample block on treatment 653-710 | MATCHES | All L-20 columns present AND finite on all 2343 powered rows (SPDR-004 item-9 lesson checked directly in cells.parquet) |
| §4 L-21 unit pin + money floor before disposition | measure_unit_pin():773-796; spreads 799-822; bybit_round_trip_cost_bps examples 1115-1128; written before cells 1129 | MATCHES | unit_pin.json: per-stratum TRAIN-median ATR bps measured (not pre-asserted), spreads, fee 11 bps RT, funding GAP disclosed |
| §12/L-18 no local adjudication accounting | AST scan bans xen.adjudication imports 1332-1340; imports xen.evaluation only | MATCHES | |
| §9 integrity 12/12 gates promote write | run():1361-1384 — exits(2) before cells.parquet on any FAIL | MATCHES | integrity.json written pre-gate; cells only after all_pass |

### Golden-trace diff (design §10 vs implementation + artifact)

- G1 (15m STRETCH W=96 k=2.5 RET_ANCHOR SHORT): stretch condition re-verified from ≤ t−1 arrays at first event (stretch_units 2.889 ≥ 2.5, direction −1) — PASS. But `forming_bar_not_used: True` is a hardcoded literal (line 860), not a computed check, and the design's "hand r_bps to clear" is not hand-derived. Independent code inspection confirms causality (Issue 3).
- G2 (1h VOLARM TIME H=W): exit_open_ns 1663884000e9 < train_end — PASS; conjunct `ep["n_episodes"] >= 0` (line 883) is vacuous (Issue 3).
- G3 (membership rebalance 2023-04-02): expected list independently recomputed from daily volume series, got == expected exact — PASS, genuine.

### Governance & boundary

- Registration/multiplicity: PASS (card REGISTERED 2026-07-16, 0 slots, uncounted screen; no family status change by screen).
- TRAIN fence / holdout: PASS — verified in integrity.json fence block (train_end 2023-12-18, holdout_start 2025-01-08, manifest 35d3375e…) and numerically (max_exit_ns < train_end_ns). Staging spread read (799-822) is outside fenced_bar_query but filters CloseTime < train_end — no holdout contact.
- check_no_local_accounting equivalent: PASS (AST, no xen.adjudication).
- No Nautilus/backtest anywhere: PASS (SPDR lane, vectorised).
- L-23 ledger: AMENDMENT-1 NEUTRAL, count 0/0/1 — carried in design §11b, integrity.json, summary.json. No ≥3 streak.
- L-28: PASS (derangement enforced + runtime self-check + artifact collapse verified). Note: implementation deranges bar indices of the direction array ("episode-label" in screen.md); zero-fixed-point letter of L-28 satisfied.
- SPREAD-SCALE-ROUTING: disclosure-only per design §4; no T1 tradability band claimed anywhere. PASS.
- Integrity-claims-vs-artifacts (SPDR-004 lesson): items 1-12 independently re-verified true of emitted artifacts; only item 7's detail string is unqualified (Issue 2). Screen.md headline numbers re-derived from cells.parquet and match (primary med mean −11.42, med lift −9.18, 15m/1h +3.80/−46.01, powered CI+ collapse med 0.951, frac>0.5 = 1.0).

### Issues

1. **MED (REVISE — operator ratification required).** Design §5.1/§5.4 vs spdr005_screen.py:1080-1082. Design defines the symbol axis as the online daily top-10 (membership.parquet holds 77 distinct symbols), but cells were computed only on a fixed 10 symbols selected by **total membership days over the full TRAIN window** — a hindsight (non-causal) universe reduction never declared in design.md or a DEVIATIONS block. Episodes are still member-gated (per-bar `ds.member`), so within-cell numbers are causal; but which 10 symbols form the promote-cluster evidence base was chosen with full-TRAIN information (survivorship/liquidity-persistence lean → LOOSER-direction under L-23). Disclosed in screen.md ("Primary 10 (membership-days)") but disclosure ≠ approval. Required: operator either ratifies as dated AMENDMENT-2 (with L-23 direction entry) or directs analyst re-derivation over the full online member set; disposition must not be read before this is resolved.
2. **MED (REVISE — amendment or integrity-detail correction).** Design §6 Control A declares "≥25 seeds" with no tiering; screen_code/spdr005_screen.py:68 uses a 5-seed battery (RAND_SEEDS_DISCLOSURE) on the 2600 non-primary cells; integrity item 7 reads "seeds=25 regenerable" unqualified, and analysis.md repeats it. Promote path is safe (all 640 primary cells use the full 25 seeds; K-rule binds on primary only), but non-primary battery_rank has 0.2 resolution and single-seed-fragility exposure (L-19). Required: operator ratifies the tier as an amendment (direction: NEUTRAL for promote / LOOSER for disclosure facets) and the tally note is carried into disposition context; no code rerun strictly needed for the promote read.
3. **LOW.** Golden traces partially self-attesting: `forming_bar_not_used` hardcoded True (line 860); G2 conjunct `n_episodes >= 0` vacuous (line 883); no hand-computed r_bps per design §10 G1. Causality independently confirmed by this review via array construction (377-379, 389-398), so no verdict impact; tighten in future SPDR screens.
4. **LOW.** simulate_episodes tail handling: after a censored TIME/HYBRID episode near data end (lines 496-499, 519-524), `i += 1` allows the next candidate to start while the censored episode is notionally still open — overlapping censored pseudo-episodes inflate n_started/censored_frac slightly near train_end. Returns unaffected (all such episodes excluded); diagnostics-only bias.
5. **LOW.** Control A fallback when a cell has zero treatment events: n_target = eligible//20 (line 466) is not cadence-matched (design §6 "cadence-matched"). Only affects cells where lift is meaningless anyway (no treatment episodes); battery_mean still emitted.
6. **INFO.** Membership (and hence all episodes) begins 2022-07-15, not TRAIN start 2021-06-29 — driven by admitted-data availability; effective evaluation window is ~17 months. Not stated in screen.md; analyst should carry as a power note.
7. **INFO.** Promote flags (ci_excludes_zero_mean) bind on the block=1 episode-level CI; permitted by design §8 ("block by episode" — episodes non-overlapping within an arm), with block_h (median-duration) sensitivity CI and 3-seed ci_low ranges emitted per L-20. Analyst should confirm block_h CI does not flip sign on promote-cluster cells.

### Verdict rationale

All promote-facing machinery (fence, causality, L-16 object, L-28 derangement + verified collapse, L-20 columns finite on powered rows, L-21 pin, GRID_TWIN sentinel, registration) checks out against both code and emitted artifacts, and screen.md's numbers reproduce from cells.parquet. REVISE (not REJECT) because the two deviations are disclosed-in-artifact, TRAIN-only, and promote-slice-safe in the seed case — but Issue 1 changes the evidence base for the cluster read and was never operator-approved, so disposition is blocked until the operator ratifies or re-scopes.

---

## Ratification note (2026-07-17, operator)

Issues 1 and 2 ratified as dated amendments (design.md §11b AMENDMENT-2 LOOSER,
AMENDMENT-3 NEUTRAL-promote/LOOSER-disclosure). L-23 ledger now 1L/0T/2N. No rerun ordered;
fixed-strata caveat and seed-tier note are binding context for the disposition. Issues 3-5
(LOW) accepted as future-screen tightening; Issues 6-7 (INFO) carried to analyst/disposition
context. QA path clear — proceed to operator disposition on analysis.md.
