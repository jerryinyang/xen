## QA run 1 — 2026-07-17T18:40:05Z — mode: subagent — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc
Verdict: **REVISE**
Dirty: untracked `python/experiments/XENA-HTFCAP-001/` (entire tree); no other tracked diffs on experiment path.
Re-verified: `git rev-parse HEAD` → `eaea177d4a113ef416ff0780018e15ff3d2ef4bc`; `git status --porcelain -- python/experiments/XENA-HTFCAP-001/` → `?? python/experiments/XENA-HTFCAP-001/`.

**Scope:** design-first read-only review of design.md + `code/*` + smoke emissions under `data/nautilus_runs/XENA-HTFCAP-001/`. Did not run search/final gate. Independent SPDR-def recomputation + smoke emission inspection used for golden/fill/HTF checks.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §1 mechanism: confirmed 4h DI×VOL / DI_ADX×VOL gate → fixed-hold market legs | `htfcap_strategy.py:72-195`, `features.py:178-196` | **DEVIATES** | Gate/hold machinery present, but HTF buckets are not clock-aligned 4h (see §4.3 / focus-1). |
| §1 / §5 binder never re-derived; CLS-FILTER LOW only | `build_universe.py:54-55,256-271` | **MATCHES** (pin body) | On-disk pin `verify_frozen_registry` OK; CLS-FILTER LOW α̂=0.045 cov=0.035; HIGH not certified. Manifest incorrectly uses **file-bytes** sha (see Issues #5). |
| §2 object identity: market leg; gate ≤ t−1; entry next 15m RealOpen | `htfcap_strategy.py:134-208`, smoke cis | **DEVIATES** | One-leg / no pyramid OK. **Fill is 1m bar close, not next-15m RealOpen** (L-29 fail on smoke). |
| §2 non-overlapping windows / no pyramiding | `htfcap_strategy.py:164-172,197-199` | **MATCHES** | Gate skipped while `_in_position` / awaiting fills; re-entry only after exit. |
| §3 estimand via shim; no local accounting for verdict path | `run_batch.py:55-62,339-366`; `emit_pre_search_floor.py:69-84` | **MATCHES** | Emissions via `write_emission_v1` + `positions_ledger_to_cis_trades`. Floor uses shim when emission present; feature-replay fallback is disclosure-only (labeled). No `assemble_realized` in experiment dir. |
| §3 finite synthetic SlPrice = Entry − side × 1.0 × HTF ATR14; no live stop | `htfcap_strategy.py:231-246`; `run_batch.py:176-202` | **MATCHES** | Smoke: all SlPrice finite; formula matches; no stop order submitted. |
| §3 L-29 EntryFillPrice == next-15m RealOpen ±1 tick | smoke `cis_trades` vs `bar_marks` | **DEVIATES** | BTC smoke: 33/33 fills == 1m **close** at EntryTime; 2/33 within 1 tick of 15m RealOpen; median \|Δ\| ≈ 14.2 price units. |
| §4.1 BTC+SOL binding, ETH disclosure | `build_universe.py:58-60,153-154` | **MATCHES** | Manifest n_binding=72, n_disclosure=36. AMENDMENT-0 NEUTRAL recorded in design. |
| §4.2 grid 108 = DI×VOL 27 + DI_ADX×VOL 81; axes exact | `build_universe.py:62-67,151-221` | **MATCHES** | Assert n=108, n_di=27, n_di_adx=81. vol_thr {1.10,1.25,1.50}, ADX {20,25,30}, H {16,32,64}. |
| §4.3 feature defs W=100, ATR14, Wilder DI/ADX, vol_ratio, map_htf_to_ltf (no retune) | `features.py:19-120` vs `spdr006_screen.py:220-295` | **MATCHES** (batch funcs) / **DEVIATES** (engine path) | Pure functions logic-match SPDR-006. Streaming HTF path builds non-clock-aligned 4h → features ≠ SPDR at same wall times. |
| §4.3 gate on last **confirmed** HTF only (no forming-bar leak) | `htfcap_strategy.py:157-161`; `StreamingHtfState.update` only on complete 16×15m | **MATCHES** (within engine buckets) | Forming HTF never fed to gate. Bucket misalignment still breaks SPDR-equivalent G3 semantics (wall-clock forming ≠ engine forming). |
| §4.4 LOW cadence attestation; park if HIGH-shaped | clause_map + codebase | **MISSING** | No candidate-gate attestation of legs/mean-hold vs HIGH class. Design §14 HARD. |
| §5 stage bands frozen fracs on TRAIN | `build_universe.py:83-112` → `results/stage_bands.json` | **MATCHES** | search_frac 0.5 / ranking 0.25 / embargo 0.2 via `calibration_pc`; TRAIN 2021-06-29→2023-12-18; holdout_start 2025-01-08. |
| §5 multi_instrument_single_node + L-30 dispose_on_completion=False + L-31 one node/process | `run_batch.py:250-284,333-334` | **MATCHES** | One `BacktestNode` per `run_param_group`; dispose False; sequential groups = one node at a time. Smoke run_config records topology. |
| §5 cost stack bybit_round_trip_cost_bps_v1 + funding binds | `build_universe.py:69-71,127-148` | **MATCHES** | GAP 5.0 bps + conservative funding; funding_coverage GAP. |
| §6 pre-search gross floor | `emit_pre_search_floor.py` → results | **MATCHES** (procedure) / **DEVIATES** (comparability) | 108-cell table written; park rule implemented; binding not all sub-floor (21/72 above). Floor used **clock-aligned** feature-replay; engine uses misaligned HTF → floor not comparable to future emissions. |
| §7 RAND-SIGN-BATTERY 25-seed percentile | design only; no `analysis_code/` | **MISSING** | Designed, not coded. L-19/L-28 escape requires battery percentile implementation. |
| §8 gate-schedule derangement tripwire (zero fixed points; BTC collapse <0.5 hard-block) | design only; no `analysis_code/` | **MISSING** | No derangement construction/assert, no collapse test. Design §14 HARD. SPDR has `make_derangement` but experiment does not call/port it. |
| §11 CONVERSION-PIN L-21 | design.md §11 | **MATCHES** (design) | Declared; no ATR divisor retune in code. |
| §12 SPREAD-SCALE-ROUTING | design.md §12 | **MATCHES** (design) | Declared for finalist stage; not yet executable (analysis later). |
| §13 golden-trace G1/G2/G3 | QA-derived + smoke | **DEVIATES / INCOMPLETE** | Smoke window 2023-06–08 only — cannot hit G1/G2 calendar anchors. Structural fill+HTF failures imply emission would not match hand-derived SPDR open-to-open path. |
| §14 holdout fence + non-STUB attestation | smoke `fence_attestation.json` | **MATCHES** | status `PINNED`; manifest_sha256 `35d3375e…`; holdout_start 2025-01-08; not STUB. |
| §15 analysis_code derangement/battery scripts | tree | **MISSING** | `analysis_code/` absent entirely. |
| Family CF-HTFCAP-001 registered | `docs/signal-registry/*`, manifest family field | **MATCHES** | REGISTERED ckpt-013; manifest `family: CF-HTFCAP-001`. |
| XENA VOID avoided via INFR-015 pin | pin path + verify | **MATCHES** | Pin is INFR-015 Bybit CLS-FILTER LOW_ONLY; void_priors ch03 listed; not using voided pins. |

### Mandatory focus checks (operator list)

1. **Gate causality (confirmed 4h ≤ t−1):** Partial. Engine never uses a partial HTF bucket, but HTF windows end at **:45** (e.g. 03:45/07:45/…) not clock 04:00/08:00/… — 366/366 smoke HTF closes non-aligned. vs SPDR `aggregate_ohlc(240)`: **4047/4047** ready LTF feature pairs differ; gate thr=1.25 only_stream=6 only_spdr=118 both=538. **DEVIATES.**
2. **Market entry fill = next 15m RealOpen (L-29):** **FAIL** on smoke (fills at 1m close; EntryTime minute ∈ {1,16,31,46}).
3. **108-cell grid:** **MATCHES** exactly (§4.2).
4. **Feature defs vs spdr006_screen.py:** batch **logic-match** (W=100, ATR14, Wilder, vol_ratio, map_htf_to_ltf); engine application **not** SPDR-equivalent due to HTF alignment.
5. **Finite synthetic SpPrice:** **MATCHES** on smoke; formula correct; no live stop.
6. **Pin abbb1842…:** **body-hash verified** via `xen.xena.calibration.verify_frozen_registry` → PASS (`artifact["sha256"]` == body sha == design claim). File-bytes sha `04c0c312…` is **not** the pin digest; developer's D1 is a **false mismatch**. Binder CLS-FILTER LOW only; no threshold re-derivation in experiment code.
7. **§4.4 cadence-coverage attestation:** **MISSING.**
8. **Derangement tripwire:** **MISSING** (not coded).
9. **RAND-sign 25-seed battery:** **MISSING** (not coded).
10. **Holdout fence + non-STUB:** **MATCHES** on production smoke emissions.
11. **No local accounting:** **MATCHES** for engine/adjudication path; floor feature-replay is labeled disclosure only.
12. **multi_instrument_single_node + dispose_on_completion=False + one node/process:** **MATCHES.**

### Golden-trace diff

Smoke emissions present only for `*__DI_VOL_HI__v1.25__adxna__H16` × {BTC,SOL,ETH}, window 2023-06-01→2023-08-01 — **not** G1/G2 anchors. Independent full-TRAIN G1 recompute via fenced catalog from analysis_start returned **0 bars** in this environment for the early window (query/band coverage gap at QA time); G1/G2 numeric anchors therefore **not fully hand-derived here**. Logical + smoke evidence:

| Trace | Expected (design §13 + SPDR map) | Observed / analysis | Result |
|---|---|---|---|
| **G1** BTC DI×VOL_HI thr=1.25 first after 2021-08-01; entry next 15m RealOpen; exit +16; finite SlPrice | EntryFillPrice = 15m RealOpen; side = DI; SlPrice = entry − side×ATR14[t−1] | No emission covering G1 date. Smoke shows fill≠15m open; HTF state ≠ clock SPDR → **would fail** if run with current strategy | **FAIL (predicted)** |
| **G2** SOL DI_ADX×VOL thr=1.25 ADX≥25 after 2022-01-01; hold 64; no second entry while open | Same fill/HTF discipline; hold 64×15m; skip re-entry while open | No emission for G2 cell/date. No-pyramid logic present in code. Fill/HTF issues remain | **INCOMPLETE / predicted FAIL on fill+HTF** |
| **G3** negative: vol≥thr but DI flips only on **forming** 4h → no entry | Confirmed-bar only | Engine suppresses partial bucket (good). Misaligned HTF means wall-clock “forming” DI can sit inside a completed engine bucket → **G3 not guaranteed vs SPDR clock definition** | **DEVIATES (semantics)** |

Smoke positive checks that do hold: hold length exactly 16×15m on BTC H16 cell; SlPrice finite and formula-consistent with recorded atr_htf; fence PINNED.

### Governance & boundary

| Check | Result |
|---|---|
| Design declaration blocks (OBJECT-IDENTITY, MECHANISM, CONVERSION-PIN, SPREAD-SCALE-ROUTING, CONTROLS, TRIPWIRE, AMENDMENT ledger) | Present in design.md |
| L-23 AMENDMENT-0 instrument scope NEUTRAL | Present; count 0L/0T/1N |
| Family CF-HTFCAP-001 registered | Yes (ckpt-013 / multiplicity registry) |
| CONVERSION-PIN L-21 | Declared; screen unit already bps; no divisor retune |
| SPREAD-SCALE-ROUTING | Declared for finalist stage |
| L-22 cost stack + funding binding | Manifest + floor use `bybit_round_trip_cost_bps_v1` + funding |
| XENA VOID avoidance | Uses INFR-015 pin, not ch03 void pins |
| `check_no_local_accounting` surface | No local estimand reimplementation for verdict path |
| Price-primary path is Nautilus emission (not vectorised backtest as primary) | Engine path is Nautilus; floor feature-replay is pre-emission disclosure only — OK if not used as certify input |
| Holdout fence on emissions | PINNED / non-STUB |
| Pin verify | `verify_frozen_registry` **PASS** (body sha abbb1842…) |
| Deviations operator-approved | Self-labeled D1 pin mismatch is **incorrect** (method error). **No operator approval** found for HTF non-alignment or close-fill (silent D1-class defects). |
| clause_map.md | Useful map; correctly admits §4.4 and §7–§8 deferred — those deferrals **fail** design §14 HARD list for execution sign-off |

### Issues

1. **critical** — design §2/§3 L-29 — `htfcap_strategy.py:197-208` + Nautilus market fill on 1m bar — **Entry fills at 1m close, not next 15m RealOpen** (smoke: 33/33 close-fills; L-29 match 2/33). Required: gate decision on confirmed 15m close, market entry priced/filled at **next 15m RealOpen** (open-to-open contract). Route: **experiment-developer**.

2. **critical** — design §4.3 / SPDR pin — `htfcap_strategy.py:136-161` HTF roll every 16 LTF from first seen bar — **HTF not clock-aligned to 4h** (smoke closes at :45; SPDR at :00). Features/gates disagree with `spdr006_screen.py` + `aggregate_ohlc`. Required: clock-aligned 4h buckets (same as SPDR `aggregate_ohlc(..., 240)`), then re-smoke and re-floor. Route: **experiment-developer**.

3. **high** — design §8 / §14 / §15 — no `analysis_code/` — **derangement tripwire not implemented** (zero fixed points, BTC collapse <0.5 hard-block). Required: implement gate-schedule block derangement + collapse attestation before any certify/gate spend. Route: **experiment-developer**.

4. **high** — design §7 / L-19 / L-28 — **RAND-sign 25-seed battery missing** (percentile battery, not single twin). Required: analysis script with 25 seeds + percentile read. Route: **experiment-developer**.

5. **high** — design §4.4 / §14 — **cadence-coverage attestation missing** (per-candidate legs + mean hold; park if HIGH-shaped under LOW-only pin). Required: candidate-gate attestation writer + park path. Route: **experiment-developer**.

6. **high** — design §6 + §4.3 — `emit_pre_search_floor.py` uses clock-aligned features while engine is misaligned — **pre-search floor not production-comparable**. Fix lands with Issue #2; re-run floor after engine alignment (prefer emission-based medians). Route: **experiment-developer**.

7. **medium** — design §5 pin pin — `build_universe.py:79-80,213,256-260` — pins **file-bytes** sha (`04c0c312…`) vs design body sha (`abbb1842…`), self-labels false D1. Required: use `verify_frozen_registry` / body `sort_keys` digest; drop false D1; record pin PASS. Route: **experiment-developer**.

8. **medium** — design §13 — golden G1/G2 emissions absent; G3 wall-clock semantics unsafe under misaligned HTF. Required: after #1–#2 fixes, emit cells covering G1/G2 anchors (or full TRAIN) and re-diff all three traces. Route: **experiment-developer**.

9. **low** — design §3 estimand gate v2 — not evidenced on smoke emissions in this review. Required: run `python -m xen.estimand_validation` on production emissions before analysis. Route: **experiment-developer** (execution checklist).

### Verdict rationale

Implementation is a partial skeleton of XENA-HTFCAP-001: **grid, instruments, costs, topology (L-30/L-31), SlPrice contract, fence PINNED, and SPDR batch feature functions** are in good shape; the **active pin body-hash is correct** despite a mistaken D1 note.

It is **not** execution-ready. Two critical path bugs break the measurement object (close-fill vs open-fill; non-SPDR HTF alignment), and three HARD integrity items from design §14 (cadence attestation, derangement tripwire, battery) are **not coded**. Silent deviations lack operator approval.

**REVISE** (not REJECT): design remains coherent and family/pin scope is valid; failures are fixable implementation gaps, not a void design or wrong family.

### Re-review gate (minimum)

Before QA run 2 / execution sign-off:
1. Clock-aligned HTF + L-29 open fills fixed and demonstrated on re-smoke.
2. Golden G1–G3 re-diffed against corrected emissions.
3. `analysis_code/` derangement + 25-seed battery present with L-28 zero-fixed-point assert.
4. §4.4 cadence attestation implemented.
5. Pin verification uses official body hash (abbb1842… PASS); false D1 removed.
6. Floor table regenerated from aligned path / emissions.

---

## QA run 2 — 2026-07-17T20:24Z — mode: operator-session — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc
Verdict: **REVISE**
Dirty: untracked `python/experiments/XENA-HTFCAP-001/` (entire tree) + `python/experiments/XENA-EPSOSC-001/`; no tracked diffs on experiment path.
Re-verified: `git rev-parse HEAD` → `eaea177…`; `git status --porcelain` → `?? python/experiments/XENA-HTFCAP-001/`.

**Fresh-context self-check:** PASS — this session did not produce the implementation; no dev diffs/discussion present. Independent recomputation used throughout (pin digest, no-local-accounting, feature byte-match, catalog re-derivation of gate schedule, emission price/hold checks).

**Scope:** re-review after QA-1 REVISE. Reviewed revised `code/*`, new `analysis_code/controls.py`, `code/cadence_attestation.py`, and `results/*` (smoke re-run present). Ran: `verify_frozen_registry`, `check_no_local_accounting`, SPDR-006 feature byte-diff, catalog re-derivation of the first gate-ON, emission L-29/SlPrice/hold verification, derangement grid-unit audit. Did not run search/final gate (operator-gated).

### QA-1 disposition (what changed)

| QA-1 issue | Sev | Status now | Evidence |
|---|---|---|---|
| #1 L-29 fill at 1m close, not next-15m RealOpen | critical | **RESOLVED** | `run_batch.open_to_open_anchor` floors engine fill-ts to 15m grid → `real_open_at`. Emission BTC v1.25 H16: EntryFillPrice vs mark-RealOpen mismatch **0/39**, exit **0/39**, max\|Δ\|=0.0. |
| #2 HTF not clock-aligned (:45 closes) | critical | **RESOLVED** | Strategy rewritten to `_agg_bucket_id` = `aggregate_ohlc` bucket key. Emission EntryTimes all on :00/:15/:30/:45; first gate-ON re-derived from catalog matches emission (below). |
| #3 derangement tripwire missing | high | **PRESENT but DEFECTIVE** | `analysis_code/controls.py gate_derangement` exists; zero-fixed-point assert + regen; hard-block <0.5 → exit 2. **But block/hold applied on a 1-minute grid — Issue #10.** |
| #4 RAND-sign 25-seed battery missing | high | **RESOLVED** | `controls.rand_sign_battery`: 25 seeds (1000–1024, = SPDR-006 `RAND_SEEDS`), percentile + `at_or_above_p95`. Reads open-to-open cis (correct 4h holds). |
| #5 cadence-coverage attestation missing | high | **RESOLVED** | `cadence_attestation.py` → `results/cadence_attestation.json`; mean hold 4.0h (16 bars), high_shaped=false, LOW-coverage OK; park-if-top1-high-shaped rule stated. |
| #6 floor not production-comparable | high | **PARTIAL** | Floor now emission-first (`source=nautilus_emission` for the 3 emitted; 105 `feature_replay_pre_emission`). Replay uses SPDR **greedy** re-entry; engine uses **skip-exit-bar** re-entry → residual seam, Issue #11. Self-heals at `--all` (all cells emit). |
| #7 pin file-bytes vs body sha; false D1 | medium | **RESOLVED** | `build_universe.pin_body_sha256` = body `sort_keys` digest; asserts == design + == artifact `sha256` field. Independent recompute = `abbb1842…` PASS. `clause_map` D1 removed. |
| #8 golden G1/G2 absent | medium | **PARTIAL (env-blocked)** — see Golden-trace diff |
| #9 estimand gate v2 not evidenced | low | **OPEN (execution checklist)** — `xen.estimand_validation` importable; run on production emissions before analysis. |

### Design-fidelity trace (delta from QA-1; unchanged MATCHES omitted)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §1/§4.3 confirmed 4h HTF, clock-aligned, ≤ t−1 | `htfcap_strategy.py:65-75,161-196` | **MATCHES** | HTF finalized only on new bucket (`_finalize_htf`), never forming. Re-derived first gate: HTF close 04:00 **strict <** entry open 04:15. |
| §2/§3 L-29 entry = next 15m RealOpen | `run_batch.py:210-290` | **MATCHES** | 0/39 price mismatch on emission. Anchor floors fill-ts to 15m grid, robust to Nautilus close-fill off-by-one. |
| §3 estimand via shim; no local accounting | `run_batch.py:271`; `estimand_validation.check_no_local_accounting` | **MATCHES (with note)** | `check_no_local_accounting` → `{ok:True, banned_defs_found:[]}`. `open_to_open_anchor` recomputes `RealizedBps = d·(xp−ep)/ep·1e4` as the L-29 open-to-open value; anchored prices copied onto the ledger (`apply_anchor_to_ledger`) so the shim re-derives consistently downstream. Passes the primitive scan; flagged informationally. |
| §3 SlPrice = Entry − side·1.0·ATR14, finite, no live stop | `htfcap_strategy.py:285`; `run_batch.py:274` | **MATCHES** | 39/39 finite; formula max\|Δ\|=0.0 vs recorded ATR; no stop order submitted. |
| §4.3 feature defs verbatim SPDR-006 | `features.py:24-119` vs `spdr006_screen.py:220-295` | **MATCHES** | `_wilder_rma`/`wilder_rma`, `wilder_adx_di`, `map_htf_to_ltf`, `causal_rolling_median` byte-identical (modulo leading `_`); ATR via `xen.zigzag.wilder_atr` (same). W=100/ATR14/ADX14. |
| §7 RAND-SIGN-BATTERY 25-seed percentile | `analysis_code/controls.py:69-98` | **MATCHES** | Rademacher, schedule fixed, seeds 1000–1024, percentile + P95 read (L-19). |
| §8 gate-schedule block derangement (≥64 LTF, ≥ max hold H; HARD <0.5 BTC) | `analysis_code/controls.py:101-195` | **DEVIATES (HARD)** | Derangement + zero-fixed-point assert present, but **operates on a 1-minute mark grid**: `MIN_BLOCK_LTF=64` → 64-**minute** blocks (1.07h) not 16h; `hold_bars` (15m units) used as 1-**minute** index offset → deranged legs measured over ~16 min vs real 4h. §8 block-length guarantee (B-6, "block ≥ H prevents within-leg leakage") violated; collapse fraction is horizon-mismatched. **Issue #10.** |
| §4.4 cadence attestation | `cadence_attestation.py` | **MATCHES** | See QA-1 #5 disposition. |

### Golden-trace diff

Catalog **in this environment** begins ~2022-07-15 (BTC 2021-06-29→2021-09-01: **0 bars**; 2022-06→08: bars from 2022-07-15; SOL 2022-01→03: **0 bars**). The literal §13 anchors — G1 BTC 2021-08-01, G2 SOL 2022-01-01 — **cannot be hand-derived here** (same environment gap as QA-1; not a code defect). Verified instead on the emitted smoke window (2023-06→08), which IS a real design-vs-emission golden diff for the G1-shaped event:

| Trace | Expected (design §4.3 + SPDR map, re-derived from catalog) | Emission | Result |
|---|---|---|---|
| **G1-analog** BTC DI×VOL thr=1.25 H16, first gate-ON after 2023-06-01 | entry_open **2023-06-21T04:15Z**, side **+1**, entry RealOpen **28680.50**, exit RealOpen **28884.90**, HTF confirmed close **04:00 strict< 04:15** | first cis leg identical to the penny | **MATCH** |
| **G2-analog** hold discipline / no second entry while open | H16 legs all exactly 16×15m; one open leg at a time | holds unique = {16}; no overlap | **MATCH** |
| **G3** confirmed-bar only (no forming-bar entry) | HTF finalized only on new-bucket roll; forming HTF never gates | every emission entry's confirming HTF close strict< entry open (39/39) | **MATCH (logic)** |
| **Leg population** greedy vs skip-bar re-entry | SPDR greedy back-to-back = **41 legs** | engine skip-exit-bar = **39 legs**; re-entry lags one 15m bar (08:15→08:30) | **DIVERGES — Issue #11** |

Literal G1/G2 numeric diff must be re-run in an environment holding the full 894-symbol catalog (or over the emitted `--all` TRAIN) before final sign-off.

### Governance & boundary

| Check | Result |
|---|---|
| Pin hash (abbb1842…) body digest | **PASS** — recompute == artifact `sha256` == design; `verify_frozen_registry` OK; class CLS-FILTER, LOW_ONLY |
| No threshold re-derivation | Binder params cited from pin in manifest; no re-fit in code |
| `check_no_local_accounting(code/)` | **PASS** `{ok:True}` |
| Feature byte-match SPDR-006 | **PASS** (four funcs identical) |
| 108-cell grid (27 DI + 81 DI_ADX; 72 binding/36 disclosure) | **PASS** (asserted in `build_universe`; manifest confirms) |
| Holdout fence — no TEST path in code | **PASS** — `run_batch --band` choices=`("TRAIN",)`; TEST operator-gated |
| Fence attestation non-STUB | **PASS** — status PINNED, manifest_sha `35d3375e…`, holdout_start 2025-01-08, no STUB |
| Cadence coverage attestation (§4.4 HARD) | **PRESENT** — LOW-only, mean hold 4h, non-high-shaped |
| SlPrice finiteness (HARD) | **PASS** 39/39 |
| Derangement destroy = DERANGEMENT, zero fixed points (L-28) | assert + regen present; **but wrong grid unit — Issue #10** |
| RAND-sign battery 25-seed (L-19) | **PASS** |
| XENA VOID avoidance (INFR-010 R4) | **PASS** — INFR-015 post-CAL hash-pinned registry, not ch03 void pins |
| `new_data_attestation` operator-only | **PASS** — not agent-authored; final gate not run |
| L-30 dispose_on_completion=False / L-31 one node/process | **PASS** — `run_param_group` |
| Amendment ledger L-23 | **PASS** — AMENDMENT-0 NEUTRAL, 0L/0T/1N, no streak |
| Estimand gate v2 pre-analysis | **OPEN** (execution checklist) |

### Issues

10. **critical (HARD, design §8/§14)** — `analysis_code/controls.py:120-178` `gate_derangement` runs on the **1-minute** mark grid (`positions.parquet` = bar_marks, 87 841 rows @ 60 s). Two unit errors: (a) `MIN_BLOCK_LTF = 64` produces **64-minute** blocks (~1.07 h), not the design's **64 LTF bars = 16 h ≥ max hold H**; (b) `hold_bars` (in 15 m units, =16 for H16) is used as an index offset on the 1-minute grid, so deranged legs are priced over **~16 minutes** instead of the real **4-hour** hold. The collapse fraction compares mismatched horizons and the §8 within-leg-leakage guarantee (B-6) is void — the HARD leak gate (<0.5 BTC) is ill-posed and its smoke value (0.845) is not the design's block-derangement collapse. Required: operate on the 15 m LTF open grid (aggregate/snap marks to 15 m), block in 15 m units of ≥ max hold H (64), and offset the deranged exit by `hold_bars` **15 m** steps. Route: **experiment-developer**.

11. **medium (design §4.3/§6/§10)** — engine re-entry lags SPDR **greedy** re-entry by one 15 m bar (skips the exit bar: `_on_ltf_complete` returns after `_submit_exit`, and the exit-bar gate is blocked while `_awaiting_exit_fill`). Smoke: 39 engine legs vs 41 SPDR-greedy legs on the same cell/window. The pre-search **floor** (`emit_pre_search_floor.feature_replay_returns`) and the SPDR-sourced power/effect expectations (§6 cost-floor framing, §10 MDE) are computed on the greedy population, not the certified engine object. Conservative (fewer legs, no lookahead) and self-heals once `--all` emits every cell (floor switches to emission medians), but the design should either (a) accept the skip-bar semantics and note that SPDR effect/power transfer is on a ~5%-larger leg set, or (b) align the engine to greedy back-to-back re-entry to match the evidence generator. Route: **quant-designer** (semantics decision) + **experiment-developer** if (b).

12. **low (design §8, L-19)** — the derangement HARD gate uses a **single seed** (`seed=42`). Design §8 is written single-destroy, so this is not a fidelity deviation, but a single-seed random control feeding a HARD REJECT is fragile (L-19 argues for percentile reads). Consider a small seed battery + percentile for the collapse read once Issue #10 is fixed. Route: **quant-designer** (optional hardening).

13. **low (design §3, informational)** — `open_to_open_anchor` recomputes `RealizedBps` locally as the L-29 open-to-open value rather than routing the re-priced ledger back through the adjudication shim for the bps field. Passes `check_no_local_accounting` (no banned primitives) and the anchored prices/times are copied onto the ledger so downstream shim reads reconcile; noted for transparency. Route: **experiment-developer** (optional — prefer shim-derived bps on the anchored ledger).

14. **low (execution checklist)** — literal §13 G1/G2 numeric golden diff not completed (this environment's catalog starts ~2022-07-15). Re-derive G1/G2 against the full-catalog `--all` TRAIN emission before final sign-off; and run `python -m xen.estimand_validation` (gate v2, incl. L-29 anchor) on production emissions before any certification read. Route: **operator/execution**.

### Verdict rationale

Substantial progress since QA-1: both critical measurement-object bugs (open-to-open fill, clock-aligned HTF) are **fixed and independently verified** — the first gate-ON re-derived from the catalog matches the emission to the penny, and confirmed-bar causality holds strictly (HTF close < entry open, 39/39). Cadence attestation and the 25-seed RAND-sign battery are now present and correct; pin body-hash is genuinely `abbb1842…`; no-local-accounting and feature byte-match pass.

The blocker is **Issue #10**: the gate-derangement leak tripwire — a design §14 **HARD** control — is implemented on the wrong grid, so its block length and hold horizon are both wrong-unit and the collapse gate is ill-posed. A HARD leak gate that emits a plausible-but-meaningless number is not execution-safe. Issue #11 (leg-construction seam) is a real but non-HARD comparability/screen-transfer concern for the designer.

**REVISE** (not REJECT): design is coherent, family/pin scope valid, and every other HARD item passes; the defect is a fixable unit error in one analysis script plus a semantics decision. Not APPROVE: cannot sign off execution while the primary future-destroying tripwire is numerically invalid.

### Re-review gate (minimum for QA run 3)
1. `gate_derangement` reworked to the 15 m LTF grid — blocks ≥ 64×15 m, hold offset in 15 m steps — re-smoked; collapse recomputed on matched horizons.
2. Operator/designer decision on Issue #11 recorded (accept skip-bar, or align engine to greedy); floor/power framing updated to match.
3. Literal G1/G2 golden diff on full-catalog TRAIN emission; estimand gate v2 PASS evidenced on production emissions.

---

## QA run 3 — 2026-07-18T00:07:56Z — mode: subagent — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc
Verdict: **REVISE**
Dirty: ` M docs/signal-registry/xena-runs.md`; `?? python/experiments/XENA-EPSOSC-001/`; `?? python/experiments/XENA-HTFCAP-001/` (entire tree untracked). No tracked diffs on the experiment path.
Re-verified: `git rev-parse HEAD` → `eaea177…`; `git status --porcelain` as above.

**Fresh-context self-check:** PASS — this session did not produce the implementation; no dev diffs/discussion present. Independent recomputation used throughout (pin scope from design, ledger leg-count + re-entry timing from `positions_ledger.parquet`, derangement grid audit by reading `controls.py` + `controls_smoke.json`, `check_no_local_accounting`, `_awaiting_exit_fill` presence grep).

**Scope:** re-review after QA-2 REVISE. Focus: QA-2 Issue #10 (derangement grid), #11 (re-entry seam decision), #12 (single-seed collapse), #14 (execution-conditional). Read revised `analysis_code/controls.py`, `code/htfcap_strategy.py`, `code/run_batch.py`, `design.md` (AMENDMENT-1/2), and smoke JSONs; inspected the on-disk BTC emission (`data/nautilus_runs/XENA-HTFCAP-001/BTCUSDT__DI_VOL_HI__v1.25__adxna__H16/`). Did not run search/final gate (operator-gated).

### QA-2 re-review-gate disposition

| QA-2 gate item | Status | Evidence |
|---|---|---|
| **#10 (HARD)** `gate_derangement` reworked to 15m LTF grid; blocks ≥64×15m; hold offset in 15m steps; collapse on matched horizons | **RESOLVED** | `controls.py:108-128` `_build_15m_open_grid` builds a 5856-pt 15m OPEN grid from the 1-min marks (87 841/15≈5856 ✓). Blocks `n_grid//64`=91 of ≥64×15m ⇒ `block_hours=16.0`; deranged exit offset `j0+hold_bars` in **15m** steps (`_deranged_median:165`), `hold_bars` derived from `ExitTime−EntryTime` ns (=16 → 4h matched horizon). Smoke: `block_hours 16.0`, `max_hold_bars 16`, `n_blocks 91`. The QA-2 unit errors (64-min blocks, 16-min hold) are gone. |
| **#11** operator/designer decision recorded + floor/power framing updated to match | **NOT SATISFIED — new Issue #15** | Design AMENDMENT-1 records **accept skip-bar / 39 legs (option A)**; the **code implements greedy back-to-back / 41 legs (option B)** via D3 HEDGING. Design ≠ code. See Issue #15. |
| **#12 (low, L-19)** single-seed HARD collapse → fold in seed battery + percentile | **RESOLVED** | AMENDMENT-2 (TIGHTER). `controls.py:174-281`: 15-derangement battery (`N_DERANGE_SEEDS=15`, seeds 7000–7014), each zero-fixed-point asserted (`_deranged_median:148-149`), HARD gate reads **battery-median** collapse (`med_collapse`, `hard_fail = med_collapse < 0.5`). Smoke: `collapse_median 1.124`, `hard_fail_leak false`, `derangement_zero_fixed_points true`. |
| **#14** golden G1/G2 + estimand gate v2 on production (execution-conditional) | **OPEN (execution-conditional, per operator routing)** | Not a pre-exec blocker (full `--all` emission is operator-gated post-APPROVE). Estimand smoke on the BTC cell: `blocking_pass true`, reconciliation `abs_diff 1.7e-13 ≪ 1.0`, fence PINNED (`35d3375e…`), schema ok. No integrity defect found. |

### Design-fidelity trace (delta from QA-2; unchanged MATCHES omitted)

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §8 derangement tripwire on 15m grid, ≥64-bar blocks, 15m-step hold, ≥15-seed battery-median collapse, L-28 zero-fixed-point | `analysis_code/controls.py:174-281` + `_deranged_median:131-171` | **MATCHES** | Grid/block/hold units all 15m; battery median read; zero-fixed-point asserted per seed. Smoke `block_hours 16.0` / `max_hold_bars 16` / `collapse_median 1.124`. QA-2 Issue #10 closed. |
| §7 RAND-SIGN battery 25-seed percentile | `controls.py:72-101` | **MATCHES** | Rademacher, schedule fixed, 25 seeds, P95 read. Smoke: `raw_percentile_vs_battery 0.16`, `at_or_above_p95 false` — informative (this is a losing 2-month smoke window; not a gate). |
| §4.3 AMENDMENT-1 re-entry semantics: "engine **skips the exit bar** (`_awaiting_exit_fill` blocks exit-bar gate); emits **39 legs**; skip-bar ACCEPTED" | `htfcap_strategy.py:8-14, 125, 249-258`; emission ledger | **DEVIATES (fidelity)** | Code does the **opposite**: greedy back-to-back (`_next_allowed_ns = t_ns + _hold_ns`, D3 HEDGING). `_awaiting_exit_fill` **does not exist** in the code (grep: NOT FOUND). On-disk emission = **41 legs**, exit-bar-open == next-entry-open (verified 08:15→08:15 back-to-back, prices coincide). **Issue #15.** |
| §6 floor caveat / §10 power: "skip-bar engine object ~5% fewer legs; SPDR transfer read on ~5%-LARGER greedy set (conservative)" | design §6, §10 | **DEVIATES (stale)** | The certified object IS the greedy 41-leg set (= SPDR greedy exactly, no seam). The "conservative ~5% larger" framing describes a skip-bar object the code does not emit. **Issue #15.** |
| §3 estimand via shim; no local accounting | `check_no_local_accounting("code")` | **MATCHES** | `{ok:True, banned_defs_found:[]}` (re-run this review). |
| D3 venue OMS = HEDGING (was NETTING at INFR-014 S1) | `run_batch.py:357,422`; `htfcap_strategy.py:8-14` | **DEVIATES (governance)** | Topology deviation from the NETTING `multi_instrument_single_node` validated at INFR-014 S1 / L-31. Smoke ran 3-instrument HEDGING single-node cleanly (metadata `oms_type HEDGING`, `n_instruments_engine 3`) — but the deviation's approval trail is self-contradictory (see Issue #16). |

### Golden-trace diff

Environment catalog still starts ~2022-07-15, so literal §13 G1 (BTC 2021-08-01) / G2 (SOL 2022-01-01) anchors cannot be hand-derived here (same env gap as QA-1/2; execution-conditional per Issue #14). Re-verified the G1-analog on the emitted BTC smoke window (independent ledger read): first leg entry **2023-06-21T04:15Z**, entry RealOpen **28680.5**, exit RealOpen **28884.9**, hold exactly 16×15m — matches design §4.3 open-to-open discipline. **Leg population now DIVERGES from the design's stated object the other way:** engine emits **41 = SPDR-greedy**, not the design's stated **39 skip-bar**. So QA-2's "39 skip-bar" object was replaced (via D3) by the greedy object, and the design text was not updated to match.

### Governance & boundary

| Check | Result |
|---|---|
| Derangement grid unit (QA-2 #10 HARD) | **PASS** — 15m grid, 16h blocks, 15m-step hold, matched horizon |
| Derangement = DERANGEMENT, zero fixed points (L-28) | **PASS** — asserted per seed; `derangement_zero_fixed_points true` |
| Derangement collapse = seed battery + percentile (L-19, AMENDMENT-2) | **PASS** — 15 seeds, battery-median HARD read |
| Estimand gate v2 (smoke) | **PASS** — `blocking_pass true`, reconciliation 1.7e-13, fence PINNED non-STUB |
| `check_no_local_accounting(code/)` | **PASS** — `{ok:True}` |
| Pin hash abbb1842… body digest / CLS-FILTER LOW_ONLY | **PASS** (unchanged from QA-2; no threshold re-derivation in code) |
| Holdout fence — no TEST path in code | **PASS** — `--band` choices `("TRAIN",)`; TEST operator-gated |
| Amendment ledger L-23 | **PASS (format)** but AMENDMENT-1 **content** contradicts code (Issue #15); 0L/1T/2N, no streak ≥3 |
| Re-entry object matches design (fidelity) | **FAIL** — design skip-bar/39 vs code greedy/41 (Issue #15) |
| D3 HEDGING deviation operator-approved with evidence | **CONTRADICTORY** — code D3 asserts operator approved greedy/HEDGING 2026-07-18 citing QA-2 #11; design AMENDMENT-1 (same date, same QA-2 issue) records **accept skip-bar** instead. Approval evidence is self-contradictory (Issue #16). |

### Issues

15. **medium (design-fidelity DEVIATES; NOT integrity/HARD)** — design §4.3 AMENDMENT-1 + §6/§10/§15 vs `htfcap_strategy.py:8-14,125,249-258` + `run_batch.py:357` + emission. The design documents and "ACCEPTS" the **skip-bar / 39-leg** re-entry object (option A) and even references `_awaiting_exit_fill` — a construct **absent from the code** (grep: NOT FOUND). The code + on-disk emission implement **greedy back-to-back / 41-leg** re-entry (option B, D3 HEDGING); ledger confirms exit-bar-open == next-entry-open (08:15→08:15, coincident price). Consequences: (a) §6 floor caveat and §10 power note describe a "conservative ~5%-larger greedy set" that is now the *actual* object, so the conservatism framing is void; (b) QA traces against a design that misdescribes the trading object being certified — an operator approving execution off this design would believe they are certifying the conservative skip-bar object. **Required:** reconcile design.md to the implemented greedy/41-leg object — rewrite AMENDMENT-1 (drop `_awaiting_exit_fill`/skip-bar narrative; record that QA-2 #11 was resolved via **option (b) greedy alignment**), fix §6/§10 framing (object == SPDR greedy exactly, seam closed), and re-derive the amendment direction/rationale. Route: **quant-designer**. (If the operator's true intent was skip-bar, route **experiment-developer** to revert D3 instead — but design and code must agree before sign-off.)

16. **low (governance / deviation-approval)** — `htfcap_strategy.py:8` D3 asserts "operator-approved 2026-07-18, QA-2 #11" for the HEDGING OMS + greedy re-entry, a topology deviation from the NETTING `multi_instrument_single_node` validated at INFR-014 S1 (L-31). The design amendment ledger (§15) carries **no** HEDGING/greedy amendment — AMENDMENT-1 records the contradicting skip-bar decision. The deviation's operator approval is therefore *asserted in code but contradicted by the design record* (QA protocol: each DEVIATION must be operator-approved with **evidence, not assertion**). **Required:** record the D3 HEDGING+greedy decision as an explicit, direction-tagged amendment consistent with the code, and confirm the S1-NETTING→HEDGING topology change is operator-signed. Route: **quant-designer** (ledger) + **operator** (sign-off). Note: the smoke did run 3-instrument HEDGING single-node cleanly — this is a records/approval-consistency gap, not an observed engine failure.

17. **low (execution checklist, carried from QA-2 #14)** — literal G1/G2 numeric golden diff and estimand gate v2 on the full-catalog `--all` production emission remain to be evidenced before FINAL sign-off. Execution-conditional (operator-gated); not a pre-exec blocker. Route: **operator/execution**.

### Verdict rationale

The QA-2 primary blocker — **Issue #10, the design §14 HARD gate-derangement tripwire on the wrong (1-minute) grid** — is **RESOLVED and independently verified**: the tripwire now lives on the 15m open grid with 16h blocks and 15m-step matched-horizon holds, draws a 15-seed zero-fixed-point derangement battery, and reads the HARD gate off the battery-median collapse (L-19/L-28/AMENDMENT-2). The single-seed fragility (Issue #12) is folded in. No HARD/integrity item is currently failing on the emitted object: estimand reconciles (1.7e-13), fence PINNED non-STUB, no local accounting, causal ≤ t−1 gate, pin body-hash intact, holdout untouched.

The blocker is a **new design-to-code fidelity contradiction (Issue #15)** surfaced by independent inspection: the design's re-entry object (skip-bar / 39 legs, AMENDMENT-1, referencing a non-existent `_awaiting_exit_fill`) is **not** what the code certifies (greedy / 41 legs, D3 HEDGING). This is exactly the design-drift class QA exists to catch (A-1) — the document QA traces against misdescribes the trading object, and the operator-approval trail for the switch is self-contradictory (Issue #16). It is a fixable documentation/decision-reconciliation defect (the greedy object is itself causally clean and arguably *better* — it matches the SPDR evidence generator exactly), not a void design or wrong family.

**REVISE** (not APPROVE): cannot sign off execution while design.md and the code disagree about the re-entry semantics of the certified object and the deviation's approval is contradictory. **REVISE** (not REJECT): every HARD integrity item passes on the emitted object; the defect is design/code reconciliation, not a leak/holdout/causality/estimand failure.

### Re-review gate (minimum for QA run 4)
1. design.md reconciled to the **implemented greedy / 41-leg (D3 HEDGING)** object — AMENDMENT-1 rewritten (no `_awaiting_exit_fill`/skip-bar narrative), §6 floor caveat + §10 power note corrected (object == SPDR greedy, seam closed), amendment direction re-derived. **OR**, if the operator wants skip-bar, code reverted to skip-bar and the smoke/emissions regenerated.
2. D3 HEDGING+greedy topology deviation recorded as an explicit direction-tagged amendment consistent with the code, with operator sign-off (Issue #16).
3. (Execution-conditional, carried) literal G1/G2 golden diff + estimand gate v2 on the full-catalog `--all` TRAIN emission before FINAL sign-off.

---

## QA run 4 — 2026-07-18T00:20Z — mode: subagent — HEAD eaea177d4a113ef416ff0780018e15ff3d2ef4bc
Verdict: **APPROVE**
Dirty: ` M docs/signal-registry/xena-runs.md`; `?? python/experiments/XENA-EPSOSC-001/`; `?? python/experiments/XENA-HTFCAP-001/` (entire tree untracked). No tracked diffs on the experiment path.
Re-verified: `git rev-parse HEAD` → `eaea177…`; `git status --porcelain` as above.

**Fresh-context self-check:** PASS — this session did not produce the implementation; no dev diffs/discussion present. Independent recomputation used throughout (design grep for skip-bar/`_awaiting_exit_fill` residue, code re-read of the greedy gate + HEDGING mapping, `check_no_local_accounting` re-run, official `pin_body_sha256` recipe recompute, `verify_frozen_registry`, on-disk smoke JSON reads for legs/derangement/estimand/cadence).

**Scope:** re-review after QA-3 REVISE. QA-3 confirmed the two prior HARD blockers RESOLVED (Issue #10 derangement 15m grid; Issue #12 seed-battery collapse) and found no HARD/integrity failure on the emitted object; its REVISE rested on Issue #15 (design↔code fidelity: skip-bar/39 design vs greedy/41 code) + Issue #16 (D3 approval-trail self-contradiction). Operator DECIDED 2026-07-18 to keep the greedy object and reconcile design to it (option B), signing off D3 HEDGING; **design.md reconciled, no code change.** This run verifies the reconciliation independently and re-checks every HARD item for regression. Did not run search/final gate (operator-gated).

### QA-3 re-review-gate disposition

| QA-3 gate item | Status | Evidence |
|---|---|---|
| **#15** design.md reconciled to greedy/41-leg (D3 HEDGING); AMENDMENT-1 rewritten (no `_awaiting_exit_fill`/skip-bar); §6 floor + §10 power corrected (object == SPDR greedy, seam closed); direction re-derived | **RESOLVED** | Design grep: **zero** skip-bar/39-leg/`_awaiting_exit_fill` residue in `design.md` (hits are only in prior append-only QA runs). §2 B-9, §4.3 AMENDMENT-1, §5 D3, §6 floor note, §10 power note, §15 ledger all describe **greedy back-to-back / 41-leg = SPDR `greedy_entries` exactly, non-overlap `next entry ≥ prev entry + H`, no seam.** Code `htfcap_strategy.py:226-258` implements exactly this (`_next_allowed_ns = t_ns + _hold_ns`; entry eligible iff `t_ns >= _next_allowed_ns`); `_awaiting_exit_fill` absent (grep NOT FOUND). Emission = **41 legs** (controls/estimand/cadence smoke all `n_legs 41`). Design==code==emission. |
| **#16** D3 HEDGING+greedy topology recorded as explicit direction-tagged amendment consistent with code, operator-signed | **RESOLVED** | Design §5 "Topology deviation D3 (operator-signed 2026-07-18)" + §15 **AMENDMENT-3** (D3 HEDGING, NEUTRAL, operator-signed 2026-07-18; L-31 one-node/process preserved). Code `htfcap_strategy.py:8-15` D3 header + `run_batch.py:357` `oms_type="HEDGING"` + metadata `oms_type HEDGING`. Design and code now agree (both HEDGING/greedy); the self-contradiction is gone. |
| **#17** literal G1/G2 golden diff + estimand gate v2 on full `--all` TRAIN (execution-conditional) | **OPEN (execution-conditional, carried)** | Not a pre-exec blocker (operator-gated post-APPROVE). Estimand smoke on the BTC cell PASSES: `blocking_pass true`, reconciliation `abs_diff 1.7e-13 ≪ 1.0`, fence PINNED non-STUB (`35d3375e…`), schema ok, `n_legs 41`. Must be evidenced on `--all` before FINAL sign-off. |

### Design-fidelity trace (delta from QA-3; unchanged MATCHES omitted)

| Design clause (§ref) | Code (file:line) / artifact | Verdict | Notes |
|---|---|---|---|
| §4.3 AMENDMENT-1: greedy back-to-back re-entry = SPDR `greedy_entries`; coincident exit/entry open; non-overlap `next entry ≥ prev entry + H`; 41 legs | `htfcap_strategy.py:226,246,249-258,287-291` | **MATCHES** | `_next_allowed_ns = t_ns + _hold_ns`; `eligible = on and t_ns >= _next_allowed_ns`; on_position_opened FIFO-maps each HEDGING position to a pending leg. Emission 41 legs. QA-3 Issue #15 (design said skip-bar/39) closed by design reconciliation. |
| §2 B-9 non-overlap / no pyramiding under HEDGING | `htfcap_strategy.py:249-258` | **MATCHES** | Gate blocked until `t_ns >= _next_allowed_ns` ⇒ contiguous, never overlapping; HEDGING keeps each leg a distinct FIFO position. |
| §5 / §15 AMENDMENT-3 D3 venue OMS = HEDGING (was NETTING at INFR-014 S1), operator-signed, L-31 preserved | `run_batch.py:357-358,422`; `htfcap_strategy.py:8-15` | **MATCHES** | Explicit direction-tagged amendment (NEUTRAL), operator-signed 2026-07-18; consistent design↔code. QA-3 Issue #16 closed. |
| §6 floor leg-set note: greedy leg set == certified object, no seam | design §6 | **MATCHES** | "conservative ~5%-larger" stale framing removed; floor computed on the same greedy object the engine certifies. |
| §10 power note: leg counts = greedy engine object = SPDR order-of-magnitude directly | design §10 | **MATCHES** | Skip-bar seam framing removed; object == SPDR greedy. |
| §15 amendment ledger + direction count | design §15 | **MATCHES** | AMENDMENT-0 N, -1 N (greedy, operator-signed), -2 T, -3 N (D3 HEDGING, operator-signed); running count **0L/1T/3N**; no one-directional streak ≥3; pinned INFR-015 qualifier gate set untouched ⇒ false-qualifier expectation unchanged. AMENDMENT-1 NEUTRAL is defensible: the switch aligns the traded object to the evidence generator without altering any pinned pass threshold. |

### Golden-trace diff

Environment catalog still starts ~2022-07-15, so literal §13 G1 (BTC 2021-08-01) / G2 (SOL 2022-01-01) anchors cannot be hand-derived here (same env gap as QA-1/2/3; execution-conditional per Issue #17). G1-analog on the emitted BTC smoke window (independent ledger read, carried from QA-2/3): first leg entry **2023-06-21T04:15Z**, entry RealOpen **28680.5**, exit RealOpen **28884.9**, hold exactly 16×15m; leg population **41 = SPDR-greedy**, now consistent with the reconciled design object (no longer the divergence QA-3 flagged). No new golden defect.

### Governance & boundary

| Check | Result |
|---|---|
| Design↔code re-entry object (fidelity) | **PASS** — greedy/41 in design, code, and emission; no skip-bar/`_awaiting_exit_fill` residue |
| D3 HEDGING deviation operator-approved with evidence, consistent design↔code | **PASS** — §5 + §15 AMENDMENT-3, operator-signed 2026-07-18; code header + `oms_type=HEDGING` |
| Estimand gate v2 (smoke) | **PASS** — `blocking_pass true`, reconciliation 1.7e-13, fence PINNED non-STUB, schema ok |
| `check_no_local_accounting(code/)` | **PASS** — re-run this review: `{ok:true, banned_defs_found:[]}` |
| Pin hash abbb1842… body digest | **PASS** — official `pin_body_sha256` recipe (`sha256(registry, sort_keys)`) recomputed == artifact `sha256` field == design claim `abbb1842…`. (Whole-artifact-minus-sha256 recipe gives a different digest — not the pin; the file-bytes/alt-recipe mismatch is the QA-1 false-mismatch trap, not a defect.) |
| Pin class / cadence scope | **PASS** — `verify_frozen_registry`: CLS-FILTER `confirm_summary` verdict `LOW_ONLY_CERTIFY`; low `e2e_alpha 0.045`, `no_search_cov 0.035` (== design §1); high `FAIL_ALPHA`. No threshold re-derivation in experiment code. |
| Causal ≤ t−1 gate (confirmed 4h HTF) | **PASS** — `_finalize_htf` updates HTF only on new-bucket roll (≥14/16 coverage), never forming; gate reads last confirmed HTF (unchanged from QA-2/3 verification). |
| Holdout fence — no TEST path in code | **PASS** — `run_batch --band` `choices=("TRAIN",)`; TEST operator-gated |
| Derangement grid/battery (L-28/L-19, AMENDMENT-2) | **PASS** — `controls_smoke.json`: 15m open grid (5856 pts), `n_blocks 91`, `block_hours 16.0`, `max_hold_bars 16`, `n_derange_seeds 15`, `derangement_zero_fixed_points true`, battery-median `collapse_median 1.124`, `hard_fail_leak false` |
| RAND-sign battery 25-seed (L-19) | **PASS** — `n_seeds 25`, Rademacher, percentile read (`raw_percentile_vs_battery 0.16`, informative — losing 2-month smoke window, not a gate) |
| Cadence coverage attestation (§4.4 HARD) | **PASS** — `cadence_attestation.json`: `pin_cadence CLS-FILTER LOW_ONLY`, emitted cells mean_hold 4.0h, `high_shaped false`, `coverage_ok_for_low_pin true`, park-if-top1-high-shaped rule stated |
| SlPrice finiteness (HARD) | **PASS** — unchanged (39/39→41/41 finite; formula max\|Δ\|=0.0 verified QA-2) |
| Amendment ledger L-23 | **PASS** — 0L/1T/3N, no streak ≥3; AMENDMENT-1/D3 now consistent across design (§4.3/§5/§15) and code |
| XENA VOID avoidance (INFR-010 R4) | **PASS** — INFR-015 post-CAL hash-pinned registry, not ch03 void pins (`void_priors` listed) |
| `new_data_attestation` operator-only | **PASS** — not agent-authored; final gate not run |
| L-30 dispose_on_completion=False / L-31 one node/process | **PASS** — one `BacktestNode` per `run_param_group`; smoke ran 3-instrument HEDGING single-node cleanly |

### Issues

No open pre-execution issues. QA-3 Issues #15 and #16 are **RESOLVED**; #17 is carried as an execution-gate condition (not a pre-exec blocker). No new issue found; no HARD/integrity item failing.

17. **low (execution checklist, carried from QA-3 #17 / QA-2 #14)** — literal G1/G2 numeric golden diff and estimand gate v2 on the full-catalog `--all` production TRAIN emission remain to be evidenced before FINAL sign-off. Execution-conditional (operator-gated); not a pre-exec blocker. Route: **operator/execution**.

### Verdict rationale

The QA-3 blockers are both resolved by the operator's design reconciliation (no code change, as intended). Independent verification confirms design.md now describes the **greedy back-to-back / 41-leg (D3 HEDGING)** object throughout (§2/§4.3/§5/§6/§10/§15) with **zero** skip-bar or `_awaiting_exit_fill` residue, matching the code (`_next_allowed_ns` greedy gate + HEDGING FIFO mapping) and the on-disk emission (41 legs across all three smoke artifacts). The D3 HEDGING topology deviation is now an explicit, direction-tagged (NEUTRAL), operator-signed amendment (§5 + §15 AMENDMENT-3) consistent between design and code — the QA-3 approval-trail contradiction is closed.

Every HARD/integrity item passes on the emitted object and re-checks clean: estimand reconciles (1.7e-13 ≪ 1.0), fence PINNED non-STUB, no local accounting (`{ok:true}` re-run), pin body-hash intact under the official recipe (`abbb1842…`, CLS-FILTER LOW_ONLY), causal ≤ t−1 gate, holdout untouched (TRAIN-only runner), derangement on the 15m grid with 16h blocks + 15-seed zero-fixed-point battery-median collapse (no leak), 25-seed RAND-sign battery, cadence LOW-coverage attestation, SlPrice finite. The amendment ledger is 0L/1T/3N with no directional streak and the pinned qualifier gate set untouched.

**APPROVE** — ready for the operator's execution gate. Two execution-conditional obligations carry to FINAL sign-off (Issue #17): the literal G1/G2 golden diff and estimand gate v2 on the full `--all` TRAIN emission. Execution approval and the final experiment verdict remain operator gates; QA APPROVE launches nothing.

---

## INFR-016 RE-ANALYSIS (report-layer reframe) — 2026-07-18

**Lane:** VAL re-analysis (emission REUSED, no re-emission — engine runs only at emission).
Prior gate-framed VALUE artifacts archived to `archive/pre-infr016/`; validity/provenance set
(`estimand_validation.json`, `boundary_trim_receipt.json`, `universe_manifest.json`,
`stage_bands.json`, `cadence_attestation.json`, nautilus_runs emission) retained. New artifacts:
`analysis.md` (rewritten), `results/layer_reports.json`, `results/layer_tables.md`, and
`analysis_code/reframe_layers.py` (composes `xen.xena.report_layer` + `xen.xena.controls`).

**HARD data-validity attestations re-checked on the reused emission — all PASS:** estimand
reconciliation 108/108 (≤ 8.2e-12 bps), strict fence 72/72 binding (post boundary-trim, last bar
2025-01-07 23:59), cadence LOW-coverage (0 HIGH-shaped), pin `abbb1842…`, causal ≤ t−1, holdout
sealed. No `future_destroy` control applies (this run's derangement is within-sample attribution).

**Value/quality/significance reads re-expressed as report layers** (observed/ideal/interpretation,
no pass/fail; ALL 72 binding + 36 ETH-disclosure candidates reported, nothing machine-dropped).
Retired gates and what they hid:
- `one_subset` top-1 → **stage-2 per cell + per subset.** 5 binding cells carry a positive
  embargoed **gross** LCB; the binder's certified top-1 (`v1.5/adx30/H64`, LCB −123) was the
  worst corner. Selection machinery hid the real gross edge.
- `at_or_above_p95` boolean → **2000-seed sign battery (effect+p+CI).** 20/72 cells at p ≤ 0.15;
  strongest BTC adx25 mid-threshold cells at p = 0.017–0.043. Corrected baseline reproduced.
- `hard_fail_leak` collapse<0.5 → **reported collapse fraction.** Old "top-1 leak 0.14" was a
  near-zero-denominator artifact (raw ≈ 1 bps; sign p 0.44 = noise; collapse now 0.90 ± 16).
  Not a leak — no edge to attribute.
- `n_legs_floor` veto → **power layer** (reported, never a drop).

**Recommended (non-final) read — EXPLORATORY, in-sample, NOT deployable:** a real,
gate-attributable, sign-null-clearing GROSS edge exists on BTC mid-threshold `DI_ADX×VOL_HI adx25`
H32/H64 holds (embargoed gross LCB +8..+18; sign p 0.02–0.05; collapse ~0.9). **Net-of-cost,
zero cells and zero subsets resolve above zero** (best net LCB −4.6) — costs + funding at 8–16h
holds are the wall. SOL `v1.5/adxna/H64` (full-window 24.9 bps) is strongly negative on the
embargoed band (−154) → edge does not transfer. Plain: **the HTF-interaction filter carries a
real directional edge on BTC that is too small to beat cost at these holds** — not dead, not
deployable. Family status changes only at a checkpoint; the operator authorises any follow-up
(new designs: lower-cost venue / maker entries, or denser-cadence variants).

**OPERATOR VERDICT (2026-07-18):** book **exploratory negative-with-nuance** — real gross,
gate-attributable BTC edge (mid-threshold adx25 H32/H64) that is sub-cost net; not deployable.
Recorded as CF-HTFCAP-001 experiment-level evidence for the next checkpoint retrospective. **No
family status change now; no new run authorised.** Family open/retire decisions remain a
checkpoint gate.

**RE-RUN 2026-07-19 (structural-label framework update).** Framework retired machine-assigned
p-cutpoint labels (STRONG/SUPPORTED/SUGGESTIVE/WASH → structural-only UNPOWERED/CONTRADICTED/—;
`label_from_p_and_power` → `structural_label`) — a hardcoded-p label re-imported the L-32 trap in
miniature. Re-ran `reframe_layers.py`; all numbers deterministic and **unchanged** (5 cells gross
LCB>0, 0 net LCB>0, sign p 0.017–0.441 as before). Only the sign-battery label column changed:
23/72 CONTRADICTED (wrong-sign raw), 49/72 positive-sign with p read directly. `analysis.md` +
`results/layer_{reports.json,tables.md}` regenerated. **Operator verdict stands** (exploratory
negative-with-nuance) — the retired labels were presentational; the read (number + p + CI) is
identical.
