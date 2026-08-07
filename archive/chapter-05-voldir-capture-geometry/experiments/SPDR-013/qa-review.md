## QA run 1 — 2026-07-23T12:30:00Z — mode: subagent — HEAD 8d19daad4593ef4f49708f019bf3ad439b46d838

Verdict: **REVISE**

**Review posture:** Fresh-context subagent; did **not** implement SPDR-013. Design text derived first; code and results checked independently. `results/compliance_trace.md` was treated as a claim map, not evidence.

**Git state:** `HEAD = 8d19daad4593ef4f49708f019bf3ad439b46d838` (refs/heads/main). Dirty-file list not obtained (no shell in this review context); on-disk review used workspace files as present.

**Run under review (results/):** Partial / smoke-shaped. Controls + zz_forecast cover **BTCUSDT only** (both clocks, DESIGN+CONFIRM). No `matched_random` keys. Golden missing G3. `integrity_selfcheck.json` → `all_pass: false` (`g3_zz_features_match: false`). §10 parquets and `screen.md` / `analysis.md` **absent**.

---

### Design-fidelity trace

| Design clause (§ref) | Expected (from design) | Code (file:line) | Verdict | Notes |
|---|---|---|---|---|
| §0.1 Universe pin recompute + assert vs top-25 | Recompute 30d `sum(close×volume)` on TRAIN 1m; assert set-eq pin files | `universe.py:56–110`; `run_screen.py:162–166` | **MATCHES** | Asserts family + results pins; abort on mismatch. Emitted `universe_recomputed.json` set-eq `universe_top25.json` / family pin. |
| §0 Clocks H1 **and** M15 both full suite | Both clocks mandatory first-pass | `config.py:67–74`; `run_screen.py:180–214` | **MATCHES** (code) | Full loop over `CLOCK_ORDER`. Results only BTC; not full 25×grid emission. |
| §3.2 D-SMA periods 14,25,50 × angle OFF/ON × both clocks | 12 cells/symbol | `config.py:79–82`; `arms.py:14–35`; `run_screen.py:82–83,206–214` | **MATCHES** (code) | 200-SMA absent. BTC results show all 6 SMA × 2 clocks × 2 bands. |
| §3.3 D-ZZ signed next-leg policy both clocks | Next dir = `−direction_k`; enter open[t+1]; §4 geometry | `arms.py:38–48`; `indicators.py:122–179`; `capture.py:67–172` | **MATCHES** | Causal confirm → signal hold until next confirm. |
| §3.3 ZZ features mag/dir/angle/path_noise | As frozen formulas | `indicators.py:98–119` | **MATCHES** | path_noise = MAD vs linear bridge / mean ATR on swing. |
| §3.3 ZZ mag **and** path_noise forecast AR + ridge both clocks | Mandatory characterisation | `zz_forecast.py:72–103`; `run_screen.py:203` | **MATCHES** (code) | Walk-forward IC/MAE; results only BTC H1+M15. |
| §4 Capture geometry | Next-open entry; 1.5 ATR stop; trail 1.0→0.5 lock / 2.0 ratchet; time 48 H1 / 192 M15; one pos | `config.py:88–92,68–71`; `capture.py:49–172` | **MATCHES** | IN-1..IN-3 resolve ATR-per-clock, open HWM, open-exit on stop (no fill at stop price). |
| §4 Partial costs | fee 11; funding stamps; allow 0/2/5 (2 governing); spread not charged | `expectancy.py:25–51`; `config.py:98–112` | **MATCHES** | Fee asserted `== 2×xen.evaluation` taker; stamps via `count_bybit_funding_stamps`; SPREAD-COST-DISCLOSURE present. |
| §5 Expectancy decomposition | Right on **gross** sign; p_right, avail, damage, exp_partial headline; win_rate disclosure only | `expectancy.py:54–75`; `stats_core.py:131–144` | **MATCHES** | `gross > 0` = right; win_rate not a band driver. |
| §6 Direction derangement 0 fixed points ≥200 seeds | Derange sides within symbol×third; destroy form DERANGEMENT | `controls.py:27–36,54–76`; `config.py:145` | **MATCHES** (core) / **DEVIATES** (bite) | Fixed-point-free index perm. Seeds 31000..31199. **+20 bps plant not implemented** (config pin unused). |
| §6 Matched random entry ≥200 seeds | Same side dist/third; same cap; exclude live ±1h; ≥200 seeds | `controls.py:128–194`; `config.py:146` | **DEVIATES** | Seeds OK. DISJOINT blocks ±**1 bar**, not ±**1 hour** → wrong on M15 (15m not 1h). Current results: control **skipped** (no keys). |
| §6 SMA benchmark Δ | ZZ − SMA14/25 on same geometry/cost | `controls.py:218–232`; `run_screen.py:232–244` | **MATCHES** (code) | BTC cells present in `controls.json`. |
| §6 Tripwire path future-destroy | D-SMA14; derange foreign paths; +30 plant collapses | `controls.py:82–122`; `run_screen.py:220–222,278–295` | **MATCHES** | Wired HARD into integrity; BTC powered cells pass; plant envelope OK. |
| §7.1 Thirds sign ≥2/3 for SUPPORTED eligibility | Must condition SUPPORTED label | `run_screen.py:119–126`; `stats_core.py:131–144`; `config.py:131` | **DEVIATES** | `thirds_sign_agree` computed/stored; **`THIRDS_SIGN_MIN` never applied** to `band_label`. Compliance_trace falsely claims eligibility wiring. |
| §8 TRAIN fence; no TEST/holdout | max exit &lt; train_end; no holdout | `catalog_io.py:91–92`; `config.py:45–46`; `run_screen.py:273–286` | **MATCHES** (code intent) | Loads only TRAIN fence. Integrity uses `max_exit ≤ train_end` (design text says `&lt;`). No holdout path. |
| §0 Forbidden range-break primary | Must not implement | screen_code/ (arms only D-SMA, D-ZZ) | **MATCHES** | No range-break arm. |
| §9 Golden G1–G3 | G1 BTC SMA flip; G2 stop synthetic; G3 SOL ZZ 1e-6 | `golden_traces.py:24–95`; `results/golden_traces.json` | **DEVIATES** (artifacts) | G1 pass; G2 synthetic logic OK in code; **G3 absent** from golden JSON (SOL never run) → integrity FAIL. G3 hand-check is formula-tautological vs `_swing_features`. |
| §8 Integrity self-check PASS | `all_pass: true` | `results/integrity_selfcheck.json` | **MISSING / FAIL** | `all_pass: false`; `g3_zz_features_match: false`. |
| §10 episodes.parquet | one row/episode + right flag | `run_screen.py:254–255` | **MISSING** (disk) | Writer exists; **file not present**. Episodes also never attach explicit `right` flag column (only gross; flag derivable). |
| §10 expectancy_by_cell.parquet | decomposition + CIs | `run_screen.py:253` | **MISSING** (disk) | Writer exists; file not present. |
| §10 zz_features.parquet | swing features + **next** mag/vol targets | `run_screen.py:195–202,256–257` | **MISSING** (disk) / **DEVIATES** (schema) | Rows lack next-swing targets (only current features). |
| §10 screen.md / analysis.md | neutral + full interrogation | — | **MISSING** | Not present (analysis stage not done; compliance_trace still lists them as deliverables as if present). |
| AMENDMENT-U1 completeness | top-25 universe | universe pin + recompute | **MATCHES** | |
| AMENDMENT-A2 completeness | M15; SMA50; ZZ mag/vol both clocks mandatory | config/arms/zz_forecast/run_screen | **MATCHES** (code grid) | Not thinned in code. Results thinned to BTC smoke. |

---

### Golden-trace diff (design is truth)

| ID | Design expected | Implementation / result | Verdict |
|---|---|---|---|
| **G1** | BTCUSDT D-SMA14: first signal flip after 2022-09-14; hand SMA14 from H1 closes; entry = next hour open; confirm side | `g1_sma_flip`: flip found; `sma14_engine == sma14_hand`; `side_confirms: true`; `entry_next_open` stored. Result ts ~2022-09-14 window. | **PASS** (logic + artifact) |
| **G2** | ETHUSDT **synthetic** path: low breaches entry − 1.5×ATR → §4 exit rule | Pure synthetic independent-engine path; breach bar 2 → exit idx 3 (next open). Not ETH market data (design allows synthetic). | **PASS** (logic); integrity calls `g2_stop_rule()` live at emit |
| **G3** | SOLUSDT D-ZZ: one confirmed swing; mag/angle/path_noise vs linear bridge to 1e-6 rel | Code path only runs when `symbol==SOLUSDT` H1. **Not present** in `golden_traces.json`. Integrity marks fail. Even when run, recompute duplicates engine formulas (weak independent hand-check). | **FAIL** (artifact); **WEAK** (method) |
| Engine parity | (extra) batch vs sequential §4 | BTC H1 `parity_ok: true`, max_rel 0 | **PASS** (informative) |

---

### Governance & boundary checklist

| Check | Evidence | Status |
|---|---|---|
| SPDR lane: vectorised OK; no estimand-gate required | Vectorised Python; bands are labels not gates (`stats_core.band_expectancy`) | OK |
| No local adjudication accounting as verdict P&L | Fees/funding via `xen.evaluation`; no `xen.adjudication` import | OK |
| No holdout / TEST contact | Fence band TRAIN only; TEST_START never used for loads | OK |
| Derangement L-28 | `_derangement` rejects fixed points | OK |
| Partial-cost claims / SPREAD-COST-DISCLOSURE | Present in config + integrity echo; prohibited claims listed | OK |
| AMENDMENT-U1 | Top-25 pin recompute+assert | OK |
| AMENDMENT-A2 | Full arm options in code (M15, SMA50, ZZ heads) | OK (code) |
| Multiplicity disclosure | Large grid (25×7 arms×2 clocks×2 bands); no multiplicity text artifact yet | OPEN (screen.md stage) |
| Tripwire HARD in integrity | `tripwire_path_future_destroy_pass` | OK (BTC cells) |
| compliance_trace trustworthiness | Claims parquets, G3, screen.md, integrity PASS | **UNTRUSTWORTHY** vs disk |
| DEVIATIONS authorised | `DEVIATIONS: []` | OK; unauthorised drifts are the REVISE list below |

---

### Issues (numbered)

1. **Severity: HIGH — §8 integrity FAIL / incomplete run**  
   - Evidence: `results/integrity_selfcheck.json` `all_pass: false`, `g3_zz_features_match: false`; `golden_traces.json` has no G3; only BTC in controls/zz_forecast; run.log ends at 1/25 symbols.  
   - Required: Full top-25 run (both clocks, all arms, both bands); emit G3 on SOL; integrity `all_pass: true`.

2. **Severity: HIGH — §10 primary artifacts MISSING**  
   - Missing on disk: `results/episodes.parquet`, `results/expectancy_by_cell.parquet`, `results/zz_features.parquet`, `screen.md`, `analysis.md`.  
   - Required: Successful `_emit` of parquets after full run; later screen/analysis stages.

3. **Severity: HIGH — §6 MATCHED-RANDOM-ENTRY not in current results**  
   - No `matched_random` keys in `controls.json` (consistent with `--skip-matched-random`).  
   - Required: Full battery ≥200 seeds without skip for design-complete control suite.

4. **Severity: MEDIUM — §7.1 thirds eligibility not applied to SUPPORTED**  
   - `config.THIRDS_SIGN_MIN=2` unused; `band_expectancy` never sees thirds.  
   - File: `stats_core.py:131–144`, `run_screen.py:119–121`.  
   - Required: SUPPORTED only if `thirds_sign_agree >= THIRDS_SIGN_MIN` (else INDETERMINATE/WASH as design intent).

5. **Severity: MEDIUM — §6 bite/MDE +20 plant missing for derangement & matched-random**  
   - `PLANT_EXPECTANCY_BPS = 20.0` in `config.py:148` never referenced by `controls.py`.  
   - Required: Implement plant detection disclosure as design CONTROL blocks specify (analogous to tripwire plant).

6. **Severity: MEDIUM — §6 matched-random DISJOINT ±1h wrong on M15**  
   - Code blocks `entry_idx ± 1` bar (`controls.py:146–156`). H1≈1h; M15≈15m.  
   - Required: Exclude live entries by **time** window ±1h (or ±4 M15 bars), not ±1 bar.

7. **Severity: LOW — §10 episode `right` flag / zz next targets**  
   - Design episodes row includes right flag; zz_features includes next mag/vol targets.  
   - Required: Explicit `right` (gross sign) column; next-swing target columns on zz_features rows.

8. **Severity: LOW — G3 golden is self-referential**  
   - Hand path clones `_swing_features` math; will not catch systematic feature bugs.  
   - Required: Prefer independent numeric fixture or distinct hand derivation.

9. **Severity: LOW — compliance_trace overclaim**  
   - Lists missing deliverables and PASS integrity as if complete.  
   - Required: Regenerate after a clean full run; do not treat current trace as SoT.

10. **Severity: INFO — §4 train_end inequality**  
    - Design §8: max exit **&lt;** train_end; code check `<=` (`run_screen.py:285`). Observed max_exit is strictly before train_end. Tighten assert for literal match.

---

### What is *not* broken (anti-false-alarm)

- Arm **grid is not thinned in code**: 3 SMA periods × 2 angles × 2 clocks + D-ZZ both clocks + AR/ridge mag & path_noise heads are all implemented.  
- Capture geometry constants and sequential engine match §4 freeze (with documented IN-1..IN-3).  
- Cost stack partial-only; spread disclosure correct; no range-break arm; TRAIN fence present.  
- Derangement is true fixed-point-free; tripwire plant logic for +30 is implemented and passes on BTC D-SMA14 cells.

---

### Recommended next step

1. Fix code issues **#4–#7** (thirds gate, +20 plant, M15 ±1h DISJOINT, schema columns).  
2. Re-run full universe **without** `--skip-matched-random`.  
3. Confirm integrity `all_pass: true` and all §10 parquets present.  
4. Only then author `screen.md` and fresh-context `analysis.md`.  
5. Do **not** treat current `compliance_trace.md` or BTC-only controls as programme evidence for HYP-B.

**Route:** `experiment-developer` for #1–#3; operator re-exec; then data-analyst for screen/analysis.
