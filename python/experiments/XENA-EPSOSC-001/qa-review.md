## QA run 1 — 2026-07-17T20:15:00Z — mode: subagent — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc

**Verdict:** REVISE  
**Dirty tree:** HEAD from `.git/refs/heads/main` (= INFR-015 complete / pin abbb1842). `git status` not executable in this subagent toolset; experiment tree `python/experiments/XENA-EPSOSC-001/**`, smoke emissions under `data/nautilus_runs/XENA-EPSOSC-001/**`, and results artifacts are present and almost certainly uncommitted relative to that HEAD (treat as dirty).  
**Reviewer note:** fresh-context subagent; did not implement. Developer `clause_map.md` used as a map to verify only.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §1 VOLARM arm ATR14/ATR56 ≥ 1.25 fixed | `features.py:26-28,136-147` | **MATCHES** | `VOLARM_RATIO=1.25`; matches SPDR-005 `spdr005_screen.py:53-56` |
| §1 stretch ≥ k · ATR; fade dir (up→short) | `features.py:149-168,185-225` | **MATCHES** | stretch_units=(c−anchor)/ATR; `su≥k → −1`, `su≤−k → +1` |
| §1 confirmed features ≤ t−1; entry next LTF open | `epsosc_strategy.py:176-200,212-254`; `features.py:95-97` | **MATCHES** | Features update on LTF complete; market entry submitted when next LTF window’s first 1m arrives (= next LTF open) |
| §1 clear RET_ANCHOR 0.25·k·ATR or anchor cross | `features.py:170-182`; SPDR `simulate_episodes` thr | **MATCHES** | `RET_CLEAR_FRAC=0.25`; dist < thr OR crossed |
| §1 HYBRID H=W; TIME-only excluded | `epsosc_strategy.py:96-97,115,219-222` | **MATCHES** | config rejects non-{RET_ANCHOR,HYBRID}; `_h_time=w` |
| §2 object identity: market-only episode; no re-entry while open | `epsosc_strategy.py:227-229,256-267` | **MATCHES** | `order_factory.market` only; gate skips while in_pos / awaiting |
| §2 limit_entry_cells=false / no limits | strategy + pin registry `limit_entry_cells:false` | **MATCHES** | no LimitOrder; pin honors L-27 trivially |
| §3 estimand via shim; L-16 episode-native | `run_batch.py:58,196-222,392-420`; smoke `smoke_estimand_validation.json` | **MATCHES** | `positions_ledger_to_cis_trades` / emission_to_adjudication; smoke `blocking_pass:true`, recon 0 |
| §3 SlPrice = Entry − side × k·ATR14[t−1] finite | `epsosc_strategy.py:296-308` | **MATCHES** | smoke DOGE short: entry 0.06824, sl 0.06949 > entry |
| §3 segment-end censoring; silent drop banned; fraction disclosed | `epsosc_strategy.py:202-210`; `run_batch.py:264-281,437-562` | **MATCHES** | open left open; `censoring.json` + `censoring_disclosure.json`; >20% flag |
| §3 no local accounting in code/ | grep banned defs; shim only | **MATCHES** | no `def assemble_*` / `build_episodes` / `per_leg_net`; floor uses shim or labelled feature_replay |
| §4.1 causal top-10 daily 00:00 UTC; rule_hash 0dd53037… | `build_universe.py:105-122,504-527`; `selection_rule.json`; strategy `_is_member_at` | **MATCHES** (rule) | rule_hash pin_match true; daily day-set membership |
| §4.1 membership metric “USDT-notional Σ vol×close” | design text vs `SelectionRule(metric=trailing_volume)` | **DEVIATES** | pin/code = trailing sum of 1m **volume** (not vol×close). Pin wins (D3). Design text wrong. |
| §4.1 delisted included (anti-survivorship binds) | `results/selection_rule.json:16-17`; manifest `delisted_included:false` | **DEVIATES** | built with `spdr005_reuse` listed-only. Design requires delisted-inclusive PIT set. D2 unapproved. |
| §4.1 symbol axis ≥90 TRAIN membership-days | `build_universe.py:296-307`; `membership_days.csv` 15 symbols | **MATCHES** | 90–521 days; includes SHIB/XRP/DOGE/JASMY + BONK/BTT counter-strata |
| §4.2 binding grid 16/symbol VOLARM×15m×W×k×clear×side | `build_universe.py:352-379`; manifest n_binding=240=16×15 | **MATCHES** | W{96,192}×k{2.5,3.0}×{RET,HYB}×{L,S} |
| §4.2 STRETCH×1h×RET_ANCHOR disclosure | `build_universe.py:380-406`; 8/symbol | **MATCHES axes / DEVIATES prose** | axes product=8; design claims “=16/symbol” arithmetic typo; code correct |
| §4.3 cadence LOW attestation | `cadence_fstar_attestation.json` | **MATCHES** | med dur p50=19.81h; 0 HIGH_SHAPED; LOW_ONLY_CERTIFY |
| §4.3 F\*=16 reachability honest | same + floor summary | **MATCHES** | 33 cells gate_expected≥16; top3 pool 70.2; note single-cell underfloor |
| §5 stage bands search0.5/rank0.25/embargo0.2 | `stage_bands.json`; `calibration_pc` fracs | **MATCHES** | immutable UTC bounds written; TRAIN fence |
| §5 binder pin CLS-EPISODE: two_stage, n_legs_floor=16, g_net, overlap | manifest `registry.*`; INFR-015 registry content | **MATCHES** | never re-derived; floor=16; e2e stage2_gross_lcb_positive |
| §5 pin sha256 abbb1842… | design vs on-disk artifact | **MATCHES (content)** | `artifact["sha256"]=abbb1842…` (verify_* re-hashes registry body). Developer **file-bytes** hash `04c0c312…` is wrong method → false D1 |
| §5 funding × episode duration in cost stack | `build_universe.py:323-343`; `emit_pre_search_floor.py:288-304` | **MATCHES** | `bybit_round_trip_cost_bps(..., hold_hours=…)` funding_rt = rate×(hold/8) |
| §5 L-30 dispose_on_completion=False; L-31 one node/process | `run_batch.py:310-329` | **MATCHES** | multi_instrument_single_node; single BacktestNode |
| §6 pre-search gross floor | `emit_pre_search_floor.py` → parquet/csv/summary | **MATCHES** | binding 223/240 ≥ BE; not entire-mass park; source=feature_replay_pre_emission |
| §6 per-symbol spread re-measure before search | floor summary `spread_label` | **PARTIAL** | GAP 5.0 deferred; disclosed “re-measure before search” — OK pre-search, binding before search |
| §7 RAND-TIMING + GRID-SHAPE identity | design only; no analysis_code/ | **MATCHES design; code deferred** | P-12 inspection: no inventory cap / banded rebalance in strategy (**MATCHES**) |
| §8 L-28 episode-label DERANGEMENT tripwire | design §8 complete; analysis_code/ absent | **MATCHES design plan; MISSING analysis impl** | destroy form DERANGEMENT, hard REJECT collapse<0.5. Acceptable pre-emission; **required before certification read** |
| §9 true-α ≤~0.06 caveat | design §1,§9 | **PARTIAL** | design yes; **not** in results/manifest registry caveats |
| §11 CONVERSION-PIN | design §11 | **MATCHES** | native bps; no ATR divisor on promote facet |
| §12 SPREAD-SCALE-ROUTING | design §12 | **MATCHES** | declared; runtime per-finalist before verdict (analysis stage) |
| §13 golden traces G1–G3 | strategy logic (+ smoke partial) | see Golden-trace | expected from DESIGN only |
| §14 HARD integrity list | pin/cadence/fence/shim | **MATCHES** framework | fence PINNED non-STUB on smoke |
| §15 no search/gate in runner | `run_batch.py:24,568-569` | **MATCHES** | operator-gated |
| DEVIATIONS D1/D2/D3 operator-approved? | clause_map only | **MISSING evidence** | unapproved D2 is binding REVISE driver |

### Golden-trace diff

Expected values from **design §13 only**. Smoke under `data/nautilus_runs/XENA-EPSOSC-001/` is VOLARM×15m×W96×k2.5×RET_ANCHOR×SHORT for SHIB/GALA/DOGE (not G1 XRP / G2 DOGE HYBRID).

| Trace | Design expected | Implemented logic | Smoke support | Verdict |
|---|---|---|---|---|
| **G1** XRP VOLARM k=2.5 W=96 after 2022-09-01; member top-10; arm+stretch; market fade at next 15m RealOpen; RET_ANCHOR clear; finite SlPrice | arm≥1.25, stretch≥k, side=fade, entry next open, clear 0.25k·ATR/cross, Sl=entry−side·k·ATR | `event_side`+`armed`+`member_next`+market+`clear_hit`+SlPrice formula | Smoke is DOGE not XRP; confirms short SlPrice geometry & market fills exist | **LOGIC MATCHES**; catalog hand-event not re-derived here (QA logic-diff only) |
| **G2** DOGE HYBRID W=192 k=3.0 hits time cap H=192 w/o RET clear; exit at cap-bar RealOpen; no second entry while open | HYBRID exit on time; no pyramid | `_bars_held >= w` → `_submit_exit`; entry blocked while `_in_position` | No HYBRID smoke cell | **LOGIC MATCHES** |
| **G3** stretch≥k but OUT of top-10 at t−1 → NO entry | membership gate causal | entry requires `want and member_next` | not event-logged for a negative bar | **LOGIC MATCHES** |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Mandatory design blocks (mechanism, object-identity, controls, tripwire, bands, power, golden, CONVERSION-PIN, SPREAD-SCALE, hard/info) | **PASS** | design.md §§1–14 |
| `check_no_local_accounting` banned defs in code/ | **PASS** | no `assemble_realized_bps` / `assemble_multileg_bps` / `per_leg_net` / `build_episodes` |
| No Python strategy backtest for verdict | **PASS** | Nautilus runner only; feature_replay floor labelled pre-emission disclosure |
| Holdout fence | **PASS** | `fenced_bar_query` TRAIN; smoke fence PINNED sha 35d3375e… |
| L-28 derangement form in design | **PASS** | destroy form DERANGEMENT; zero fixed points; hard REJECT |
| L-28 code (analysis_code) | **DEFERRED** | not required to block emission; blocks certification/analysis readiness |
| L-30 / L-31 topology | **PASS** | dispose_on_completion=False; one BacktestNode/process |
| XENA pin VOID check | **PASS** | post-CAL INFR-015 pin active; content sha abbb1842; CLS-EPISODE LOW_ONLY; n_legs_floor=16; selection_rule_default_hash 0dd53037… |
| limit_entry_cells false | **PASS** | pin + market-only strategy |
| CONVERSION-PIN | **PASS** | design §11 |
| SPREAD-SCALE-ROUTING | **PASS** | design §12 |
| Amendment ledger L-23 | **PASS** | 0 L / 0 T / 0 N |
| DEVIATIONS operator-approved | **FAIL (D2)** | D1 false-alarm; D3 design text; D2 material unapproved |
| new_data_attestation agent-authored | **N/A** | no final gate run |
| Search/gate spend | **not run** | correctly operator-gated |
| True-α ≤~0.06 surfaced | **design only** | missing in results/manifest |
| F\* attestation honest | **PASS** | cadence_fstar_attestation.json |
| P-12 structure identity | **PASS** | no hard inv cap / banded rebalance in traded object |
| Censoring disclosed | **PASS** | smoke + aggregate disclosure |
| Funding × duration | **PASS** | cost helpers |

### INFR-015 pin verification (independent)

| Field | On-disk registry | Design claim | Match |
|---|---|---|---|
| Content `artifact["sha256"]` | `abbb184229236a75f624537ca605668a73f6f85138c150e14a3609c4191bf786` | abbb1842… | **YES** |
| File-bytes sha256 (developer) | `04c0c3128d3da2641f6f3fb5b92b64135793f77f62ee5aa661de7b98f3314070` | n/a | wrong method for pin verify |
| CLS-EPISODE cadence | LOW_ONLY_CERTIFY (HIGH FAIL_COV) | LOW only | **YES** |
| n_legs_floor | 16 | 16 | **YES** |
| selection_rule_default_hash | `0dd530374fd3283ba9a82796d719c7bbd019d759e62c6987e0162ba5bcfc5ad2` | 0dd53037… | **YES** |
| α̂ low / cov | 0.03 / 0.025; Wilson high ≈0.064 | true α ≤~0.06 | **YES** (caveat justified) |
| limit_entry_cells | false | false | **YES** |

### Issues

1. **MEDIUM** — design §4.1 · `results/selection_rule.json:16-17` + manifest `instruments.delisted_included=false` · **Unapproved D2**: membership built via `--reuse-spdr-membership` (listed-only SPDR top-10), not ADMITTED+delisted `universe_selection` recompute. Anti-survivorship clause violated for the universe that floor + smokes used. **Required:** recompute membership without SPDR reuse **or** operator written approval of listed-only bootstrap (scope + impact). · **Route:** `experiment-developer` (+ operator if exception).

2. **LOW** — design pin header · `build_universe.py:501-601` / clause_map D1 · **False pin-mismatch D1**: content pin abbb1842 matches design; file-bytes hash must not be used as pin identity (`verify_bybit_registry` / `json.dumps(registry, sort_keys=True)`). Manifest `sha256_match_design:false` misleads gate. **Required:** store content pin sha (abbb1842) as binding; drop or relegate file-bytes hash; delete false D1. · **Route:** `experiment-developer`.

3. **LOW** — design §4.1 metric wording · design.md:75-78 vs pin `trailing_volume` · Design claims USDT-notional Σ vol×close; pin/code use trailing volume. **Required:** design cite pin metric verbatim (or document pin-wins). · **Route:** `quant-designer`.

4. **LOW** — design §4.2 · design.md:101-103 · STRETCH probe arithmetic says 16/symbol; axes product and code = 8. **Required:** fix design count. · **Route:** `quant-designer`.

5. **INFO** — design §8 / §15 · no `analysis_code/` · Derangement tripwire design complete; implementation deferred. Acceptable for emission/search prep; **hard block before any certification/analysis read**. · **Route:** `data-analyst` at analysis stage.

6. **INFO** — checklist true-α · design only · Surface `true_alpha_priced_le_0.06` on manifest/results cadence attestation before gate claims. · **Route:** `experiment-developer` (optional pre-search).

7. **INFO** — design §6 · GAP 5.0 spread · Per-symbol pseudo-quote re-measure still deferred; must complete before search cost stack is binding. · **Route:** `experiment-developer` pre-search.

### Operator gate

- **Execution (full TRAIN emissions / search / gate):** **blocked** until REVISE items 1–2 addressed (or operator explicitly accepts D2 + pin-hash bookkeeping) **and** QA re-run → APPROVE + separate operator execution approval.
- **Smoke / already-emitted 3 cells:** integrity OK for tooling validation only; not a substitute for production membership universe.
- **Search/gate spend:** not in scope of this review’s approval; remains separate operator gate.
- **Ready for operator execution gate?** **No** (REVISE).

### Summary counts

| Severity | n |
|---|---|
| CRITICAL / REJECT | 0 |
| MEDIUM | 1 |
| LOW | 3 |
| INFO | 3 |

---

## QA run 2 — 2026-07-17T21:40:00Z — mode: operator-session — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc
**Verdict:** APPROVE (with carried conditions §Issues 1–4)
**Dirty tree:** `git status --porcelain` = untracked `python/experiments/XENA-EPSOSC-001/` + `python/experiments/XENA-HTFCAP-001/`. Experiment tree, `results/**`, and smoke emissions uncommitted vs HEAD (treat as dirty). Since run 1, the developer edited in place (no commit): universe recomputed delisted-inclusive → **29 symbols / 464 binding / 696 total** (was 15 / 240).
**Reviewer note:** fresh-context operator session; did not implement. `clause_map.md` fix-map treated as a map to verify, not evidence. This run re-verifies the run-1 REVISE fixes independently and re-traces the full clause set against the corrected (larger) manifest.

### Run-1 fix verification (independent)

| Run-1 issue | Fix claimed | Independent verification | Verdict |
|---|---|---|---|
| #1 MEDIUM D2 listed-only membership | default recomputes ADMITTED+delisted | `build_universe.py:511` default `load_admitted_pool(include_delisted=True)` → `build_membership_delisted_inclusive`; `selection_rule.json` `membership_source=universe_selection_trailing_volume_delisted_inclusive`, `include_delisted_in_ranking_pool=true`; realized axis contains delisted names (LUNAUSDT, SRMUSDT, FTTUSDT-pool, MATICUSDT, OMGUSDT) | **RESOLVED** |
| #2 LOW false pin-hash D1 | content pin sha, file-bytes audit-only | recomputed `sha256(json.dumps(registry,sort_keys=True))` = `abbb1842…` == `artifact['sha256']` == design claim; manifest `sha256_match_design=true` | **RESOLVED** |
| #3 LOW metric wording | design cites `trailing_volume` | design.md §4.1:78 reads `trailing_volume`; `selection_rule.json.metric_note` documents "not USDT-notional" | **RESOLVED** |
| #4 LOW STRETCH 16/symbol typo | design → 8/symbol | design.md §4.2:102 = "**8/symbol**"; manifest `disclosure.variants_per_symbol=8`, 232=8×29 | **RESOLVED** |
| #6 INFO true-α surfaced | on manifest + attestation | `cadence_fstar_attestation.json.true_alpha_priced_le=0.06`; manifest `registry.true_alpha_priced_le=0.06`; design §1/§9 | **RESOLVED** |

### Design-fidelity trace (re-verified on corrected manifest)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §1 VOLARM arm ATR14/ATR56 ≥ 1.25 | `features.py:28,143-147,211-219` | **MATCHES** | `VOLARM_RATIO=1.25`; batch + streaming identical |
| §1 stretch ≥ k·ATR; fade up→short | `features.py:149-168,208-225` | **MATCHES** | `su≥k → −1`, `su≤−k → +1` |
| §1 features ≤ t−1; market entry next LTF open | `epsosc_strategy.py:210-253,254-265` | **MATCHES** | state updated on completed LTF; market order at next-window boundary; `on_order_filled` fills next open (L-29 anchor gate v2 PASS on smoke) |
| §1 clear RET_ANCHOR 0.25·k·ATR or cross | `features.py:170-182` | **MATCHES** | `RET_CLEAR_FRAC=0.25`; dist<thr OR crossed |
| §1 HYBRID H=W; TIME-only excluded | `epsosc_strategy.py:94-95,113,218-222` | **MATCHES** | `_h_time=w`; config rejects non-{RET,HYBRID} |
| §2 episode==trading object; no pyramiding (L-16) | `epsosc_strategy.py:226-227,254-256` | **MATCHES** | market-only; entry gate returns while in_pos/awaiting |
| §2 limit_entry_cells=false | strategy market-only + pin `limit_entry_cells=false` (3×) | **MATCHES** | no LimitOrder anywhere; pin honored trivially |
| §3 estimand via shim; L-16 | `run_batch.py:58,208,392-420`; `smoke_estimand_validation.json` | **MATCHES** | shim only; recon abs_diff 0.0 bps; `blocking_pass=true` |
| §3 SlPrice = Entry − side·k·ATR14[t−1] finite | `epsosc_strategy.py:290-306` | **MATCHES** | ATR frozen from `_pending_entry` (no drift); smoke short SL>entry |
| §3 segment-end censoring; silent drop banned; fraction disclosed | `epsosc_strategy.py:200-208`; `run_batch.py:264-281,547-563` | **MATCHES** | on_stop leaves open → shim Censored; per-cell `censoring.json` + aggregate `censoring_disclosure.json`; >20% flag |
| §3 no local accounting in code/ | `check_no_local_accounting` (estimand_validation.py:385) | **MATCHES** | `ok:true, banned_defs_found:[]`; floor bps path labelled `feature_replay_pre_emission` (disclosure, not estimand) |
| §4.1 causal top-10 daily 00:00 UTC; rule_hash 0dd53037 | `build_universe.py:123-140,255-327`; `_is_member_at` | **MATCHES** | `rule_hash` recomputes to `0dd53037…`; `member_next` uses rebalance ≤ next open (causal ≤ t−1) |
| §4.1 delisted included (anti-survivorship) | `build_universe.py:187-208,510-520`; manifest `delisted_included=true` | **MATCHES** | run-1 D2 fixed; delisted names present |
| §4.1 symbol axis ≥90 TRAIN membership-days | `build_universe.py:361-372`; `membership_days.parquet` | **MATCHES** | 29 symbols, 90–518 days; incl. SHIB1000/DOGE/JASMY + 1000BONK/1000BTT counter-strata |
| §4.2 grid 16 binding + 8 disclosure /symbol | `build_universe.py:411-472,556-561` | **MATCHES (counts)** | 464=16×29, 232=8×29; hard-asserted in builder |
| §4.2 realized universe size vs design "≈14 sym / ~224 cand" | manifest `n_symbols=29, n_binding=464` | **DEVIATES (prose)** | binding rule is authoritative ("≈" = estimate); §4.2/§10 quantitative figures now ~2× stale — see Issue 1 |
| §4.3 cadence LOW attestation | `cadence_fstar_attestation.json` | **MATCHES** | p50 dur 20.0h; 0 HIGH_SHAPED; LOW_ONLY_CERTIFY |
| §4.3 F*=16 reachability; floor by binder not design | attestation + pin `class_configs[1].procedure.n_legs_floor=16` | **MATCHES** | 18 cells gate≥16; top3 pool 60.8; `portfolio_Fstar_reachable=true`; **floor lives in pinned binder procedure**, absent from strategy — required separation held |
| §5 stage bands search0.5/rank0.25/embargo0.2 | `build_universe.py:143-184`; `stage_bands.json` | **MATCHES** | immutable UTC bounds on TRAIN fence |
| §5 binder pin CLS-EPISODE two_stage, g_net, overlap, floor16 | manifest `registry.*`; pin registry | **MATCHES** | never re-derived; `e2e_pass_event=stage2_gross_lcb_positive` |
| §5 pin sha abbb1842 | independent recompute | **MATCHES** | content-pin method correct |
| §5 funding × episode duration in cost stack | `build_universe.py:388-408`; `emit_pre_search_floor.py:288-304` | **MATCHES** | `bybit_round_trip_cost_bps(..., hold_hours, funding_coverage=GAP)`; funding scales with hold |
| §5 L-30 dispose_on_completion=False; L-31 one node/process | `run_batch.py:311,329` | **MATCHES** | single BacktestNode; multi_instrument_single_node |
| §6 pre-search gross floor | `emit_pre_search_floor.py`; summary | **MATCHES** | binding 395/464 ≥ BE; not entire-mass park → PROCEED |
| §6 per-symbol spread re-measure before search | floor `spread_label=GAP 5.0` | **PARTIAL (deferred)** | GAP 5.0 placeholder; disclosed "re-measure before search" — Issue 3 |
| §7 controls (RAND-TIMING / GRID-SHAPE) | design §7; no analysis_code/ | **MATCHES design; impl deferred** | P-12 code inspection: no hard cap / banded rebalance in strategy (MATCHES) |
| §8 L-28 episode-label DERANGEMENT tripwire | design §8 complete; analysis_code/ absent | **MATCHES design; impl deferred** | derangement form, zero fixed points, hard REJECT collapse<0.5 — required before any certification read (Issue 2) |
| §9 true-α ≤~0.06 caveat | design §1/§9 + attestation + manifest | **MATCHES** | now surfaced in results |
| §11 CONVERSION-PIN (L-21) | design §11 | **MATCHES** | native bps, no ATR divisor on promote facet |
| §12 SPREAD-SCALE-ROUTING | design §12 | **MATCHES** | declared; runtime per-finalist before verdict |
| §13 golden traces G1–G3 | see Golden-trace diff | **LOGIC MATCHES; G1/G3 symbol gap** | Issue 4 |
| §14 HARD integrity list | pin/cadence/fence/shim/censoring/SL/P-12 | **MATCHES** | all green (below) |
| §15 no search/gate in runner | `run_batch.py:497,568` | **MATCHES** | operator-gated |

### Golden-trace diff (expected from design §13 only)

| Trace | Design expected | Implemented logic | Verdict |
|---|---|---|---|
| **G1** XRP k2.5 W96 armed-stretch, up→short, entry next open, RET_ANCHOR clear, finite SL | `armed & su≥k → side=−1`; entry next open; clear 0.25k·ATR/cross; SL=entry−side·k·ATR | `event_side`+`member_next`+market+`clear_hit`+SL formula | **LOGIC MATCHES**; XRP <90 membership-days → excluded from traded axis, no XRP cell emits (Issue 4) |
| **G2** DOGE HYBRID W192 k3.0 hits cap H=192 w/o clear; exit cap-bar RealOpen; no 2nd entry | `_bars_held>=192 → exit`; entry blocked while open | `time_hit` → `_submit_exit` (market→next open); gate early-return in_pos | **LOGIC MATCHES**; DOGE in traded axis |
| **G3** stretch≥k but OUT top-10 at t−1 → NO entry | membership gate causal | entry requires `want and member_next` | **LOGIC MATCHES** (symbol-agnostic gate); XRP illustrative |

### Governance & boundary

| Check | Result | Evidence |
|---|---|---|
| Mandatory design blocks | **PASS** | §§1–14 incl. CONVERSION-PIN, SPREAD-SCALE, hard/info split |
| `check_no_local_accounting(code/)` | **PASS** | `ok:true`; official guard `xen.estimand_validation` |
| No Python strategy backtest for verdict | **PASS** | Nautilus runner only; feature_replay floor = labelled pre-emission disclosure |
| Holdout fence sealed | **PASS** | TRAIN-only queries; smoke fence PINNED sha `35d3375e…` |
| Pin content sha abbb1842 (content-pin method) | **PASS** | recomputed independently == design |
| CLS-EPISODE LOW_ONLY / n_legs_floor=16 in binder | **PASS** | pin `class_configs[1].procedure.n_legs_floor=16`; floor absent from strategy/design |
| selection_rule_default_hash 0dd53037 | **PASS** | pin field + `rule_hash()` recompute match |
| limit_entry_cells false | **PASS** | pin (3×) + market-only strategy |
| XENA VOID on new stack (INFR-010 R4) | **PASS** | post-CAL INFR-015 hash-pinned registry active |
| L-28 derangement form in design | **PASS** | zero fixed points, hard REJECT, no override |
| L-30 / L-31 topology | **PASS** | dispose_on_completion=False; one BacktestNode/process |
| Funding × duration | **PASS** | hold_hours in cost helper both scripts |
| Censoring disclosed; silent drop banned | **PASS** | on_stop leaves open → shim Censored; per-cell + aggregate JSON |
| P-12 structure identity | **PASS** | no hard inventory cap / banded rebalance in traded object |
| Amendment ledger L-23 | **PASS** | design §15: 0 L / 0 T / 0 N |
| new_data_attestation agent-authored | **N/A** | no final gate run (operator-gated) |
| Membership causality ≤ t−1 | **PASS** | daily 00:00 UTC rebalance; `member_next` = rebalance ≤ next open |

### Issues

1. **LOW** (design prose) — §4.2:101 / §10 · design.md · realized manifest is **29 symbols / 464 binding / 696 total**, but §4.2 states "~14 symbols ≈ 224 binding candidates" and §10 power expectations are premised on that count. The ≥90-day rule is authoritative (design says "computed deterministically … list written into manifest"; "≈" flags an estimate), so this is **not a spec deviation** and F* reachability actually strengthens (18 cells ≥16; top3 pool 60.8). But the operator must register `evaluation_count`/`distinct_subsets` at search from the **manifest (464)**, not the stale ~224, and §10 MDE/power prose should be refreshed. · **Route:** `quant-designer` (text) + operator note at search-registration gate. *Non-blocking for emission.*

2. **INFO** (deferred by design) — §8 · no `analysis_code/` · episode-label DERANGEMENT tripwire is design-complete (zero fixed points, hard REJECT collapse<0.5) but unimplemented. Acceptable pre-emission; **hard block before any certification/analysis read**. · **Route:** `data-analyst` at analysis stage.

3. **INFO** (deferred by design) — §6 · `GAP_SPREAD_BPS=5.0` · per-symbol pseudo-quote spread still a placeholder; disclosed "re-measure before search". Meme-alt spreads (§6 caution) can move the floor materially — must complete before the cost stack is binding at search. · **Route:** `experiment-developer` pre-search.

4. **LOW** — §13 · golden traces G1/G3 name **XRPUSDT**, which is a top-10 membership-pool member on <90 days and is therefore **excluded from the traded 29-symbol axis** (no XRP cell emits). Strategy logic is symbol-agnostic so the logic-diff holds, but a *live* golden emission diff cannot use XRP. G2 (DOGE) is in-axis and fine. · **Required:** re-point G1/G3 to an axis member (e.g. DOGE/GALA) for a live golden diff, or annotate that G1/G3 verify gating logic only. · **Route:** `quant-designer`. *Non-blocking for emission.*

5. **INFO** — §4.1 · `build_universe.py:133` · pinned `SelectionRule.pool="admitted_listed"` is **inert** in the custom `build_membership_delisted_inclusive` ranking (rule supplies only n/window/tie-break/schedule); delisted inclusion is delivered by feeding a delisted pool. `rule_hash` integrity (0dd53037) and §4.1 anti-survivorship are **both** satisfied, but the pin's declared `pool` label no longer matches effective behavior. Worth an operator note; no change required. · **Route:** none (disclosure).

### Operator gate
- **Full TRAIN emission / floor (build_universe → emit_pre_search_floor → run_batch):** integrity **APPROVED** — all HARD checks green, run-1 D2 blocker independently verified fixed.
- **Search / gate spend:** remains a separate operator gate; before registering, close Issue 1 (register 464, not 224) and Issue 3 (per-symbol spread); Issue 2 (derangement) must run before any certification read.
- **Ready for operator execution gate?** **Yes** (APPROVE), conditions 1–4 carried to search/analysis gates.

### Summary counts
| Severity | n |
|---|---|
| CRITICAL / REJECT | 0 |
| MEDIUM | 0 |
| LOW | 2 |
| INFO | 3 |

---

## Coverage audit (orchestrator, 2026-07-18) — catalog search-band coverage

**Trigger.** Discovered while running XENA-HTFCAP-001: this machine's local shards for the 3
majors (BTC/SOL/ETH) start 2022-07-14/15, three weeks *after* the pinned XENA search band ends
(search band 2021-06-29 → 2022-06-24). That makes HTFCAP (majors-only universe) unrunnable
locally. Audited whether EPSOSC's search was affected.

**Findings (grounded in catalog + `data/nautilus_runs/XENA-EPSOSC-001/`):**

| Check | Value |
|---|---|
| Global earliest bar, local catalog (any instrument) | 2021-06-29 06:54 (= fence start `35d3375e`) |
| EPSOSC universe majors (BTC/SOL/ETH) cells | **0** (universe is all alts) |
| EPSOSC instruments with ≥1 search-band leg | **288 / 464** |
| EPSOSC search-band legs / total | **6,749 / 21,986 = 30.7 %** |
| Earliest EPSOSC emitted leg | 2021-07-05 |
| Median instrument earliest leg | 2022-04-15 (later listings — expected for alts) |

**Verdict: NO data-availability deviation for XENA-EPSOSC-001; search/certify data is valid.**
The majors truncation is specific to BTC/SOL/ETH local shards and does not intersect EPSOSC's
alt universe. The catalog reaches the fence start globally; EPSOSC's search band is
substantially covered (288/464 instruments, 30.7 % of legs) and the finalists are all alts
(AKRO/PEPE/SHIB/DOGE/GALA…), none truncated. Search-band selection is well-supported; the run
is **not** nullified. (The 176 instruments with no search-band legs reflect genuine later
listings, not truncation.)

Unrelated to coverage: EPSOSC formal top-1 (AKRO W192 k3 HYBRID S) FAILS the §8 derangement
tripwire (collapse 0.395 < 0.5) with negative net LCB — a substantive negative finding recorded
in `analysis.md`, not a data-coverage artifact.
