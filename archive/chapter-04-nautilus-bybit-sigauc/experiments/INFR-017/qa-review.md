# QA review — INFR-017 (signed-bar tier: provenance, pins, catalog lane, seasonal baselines)

Append-only. Each run adds a dated section. Never rewrite a prior run.

---

## QA run 1 — 2026-07-20T18:40Z — mode: subagent — HEAD af7bf9e1f2f8aea4756a7eb73ff7828c6b997a09

Reviewed git state: HEAD `af7bf9e` + working-tree additions (untracked `python/experiments/INFR-017/`,
`python/src/xen/sigbar/`, `docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/`,
`docs/signal-registry/candidate-families/cf-sigauc-001.md`; modified `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/multiplicity-registry.md`).

**Verdict: REVISE** (two blocking defects; one item escalated to the operator).

**FAILING_ARTIFACT (primary):** `python/src/xen/sigbar/baselines.py` + `python/experiments/INFR-017/results/seasonal_baselines.parquet`
**REQUIRED_SKILL (primary):** `experiment-developer`
**FAILING_ARTIFACT (secondary):** `python/experiments/INFR-017/design.md` §3(b)
**REQUIRED_SKILL (secondary):** `quant-designer` (restate §3 on a TRAIN-bounded read) — with operator adjudication of the holdout touch

Note: this item has already been executed (results present, mtimes 18:07–18:12). QA is nominally
pre-execution; this review therefore covers the emitted artifacts as well as the code.

---

### 1. Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §2 object: signed 1-min bar `O,H,L,C,V + Buy/Sell + NTrades + spread + Δ` | `python/src/xen/sigbar/data_types.py:42-58` | MATCHES | All fields present; `delta` derived, `spread_status` enum added (beyond design, justified by W2) |
| §2 band: TRAIN only; TEST/holdout not read | see §3 Fence below | **DEVIATES** | Code paths are bounded; **design.md §3(b)'s own numbers are not** (Issue 2) |
| §4 W1: re-download raw CSVs, recompute Buy/Sell/NTrades **independently** of `stream_pipeline` | `a8_provenance_audit.py:131-190` | MATCHES | No import of `stream_pipeline` (grep: only docstring/path references, `a8:10,11,18,135,138`). Genuine re-fetch from `public.bybit.com`. See Issue 6 for the residual blind spot |
| §4 W1: emit per-day per-symbol max relative deviation | `a8:281-292`, `summarise` `a8:311-354` | MATCHES | `results/a8_provenance_audit.json` carries all 20 rows |
| §4 W1: "must match stored values **to rounding**" | `a8:220` inner join | **DEVIATES** | Reconciliation is an INNER join on `bar_ms`; bars present in one side only are silently excluded from the deviation stats and only surface as a `detail` string (`a8:278-279`), never as FAIL. A dropped-minute defect in the producing pipeline would pass the kill-gate. Benign in this run (all 20 days had `n_bars_raw == n_bars_stored == n_bars_matched`) but the gate is weaker than declared (Issue 5) |
| §4 W2: pin exact definition | `spread_pin.py:72-90` `STORED_SPREAD_DEFINITION` → `column_pins.json:W2_stored_definition_pin` | MATCHES | Verbatim, includes the doc/artifact disagreement and the `t1_round_trip_spread_bps` consumer note |
| §4 W2: **decide** among (i) recompute / (ii) floor-and-flag / (iii) UNUSABLE; chosen option **frozen and hash-pinned**; **losing options recorded with reasons** | `spread_pin.py:384-397` `build_pin` | **MISSING** | `build_pin` emits four numbers per symbol and nothing else. `column_pins.json` has no `decision` field, no rejected-option reasons, no sha256 self-pin. The decision exists only as a hard-coded constant elsewhere (`signed_bar_lane.py:129` → `SPREAD_UNUSABLE`) — the pin artifact does not state it. Violates §8.2 (Issue 3) |
| §4 W2 candidate set | `spread_pin.py:423-426` | PARTIAL | Only candidates `A` and `C` declared/evaluated; the label gap implies a `B` that was never declared. Option (ii) floor-and-flag is never evaluated against option (iii) |
| §4 W3: measure `corr(Δ/V, SpreadBps)` per symbol on the sample | `spread_pin.py:311-318`, `pearson_with_ci:241-257` | MATCHES (numerically) | Measured; BTC stored −0.031 [−0.057, −0.006], flip −0.005. All below the 0.20 threshold |
| §5 W3: `\|corr\| ≥ 0.20` ⇒ independence constraint **written binding into the pin** | — | MISSING (non-binding this run) | No code branch writes the constraint. Threshold not breached, so no live consequence, but the declared mechanism is absent and would not fire if a rerun breached it |
| §4 W4: confirm `V/NTrades` usable; **record the secular drift caveat (order-splitting)**; "never a standalone signal" | `spread_pin.py:320-338` | **PARTIAL/MISSING** | Emits a 3-number distribution of average trade size on 4 sample days. No usability verdict, no drift caveat, no "never standalone" constraint in the artifact. §8.2 requires "the W4 `NTrades` verdict" |
| §4 W5: `SignedBar` custom Nautilus `Data` type | `data_types.py:42-58` (`@customdataclass`) | MATCHES | |
| §4 W5: fenced ingest writing `data/catalog/` | `signed_bar_lane.py:51,195,234` | DEVIATES (accepted) | Writes `data/catalog_sigbar/` instead, to leave the pinned OHLCV catalog + fence sha untouched. Sound and documented at `signed_bar_lane.py:9-11,277-280`; strictly a departure from the design text — record it as a declared deviation rather than leave the design/code disagreeing |
| §4 W5 / §8.4: round-trip equals **the staging source** bit-for-bit on all signed fields | `signed_bar_lane.py:138-178` | **DEVIATES** | `roundtrip_check` compares `written` (the in-memory `SignedBar` list) against `read`, never against `source`; `source` is used only for `n_source_rows` (`:149`). It proves catalog serialisation fidelity, not staging→`SignedBar` fidelity. A column-mapping error in `to_signed_bars` (e.g. `BuyVolume`→`sell_volume`) round-trips perfectly and reports `exact_match: true` (Issue 4) |
| §4 W5: `pipeline_version` + `config_hash` stamped on every record | `data_types.py:58` | PARTIAL | `pipeline_version` present; **no `config_hash` field** on `SignedBar`. Design §4 W5 names both |
| §4 W5: fence attestation via `catalog_fence.fence_attestation_payload` | `signed_bar_lane.py:37,269,281-286` | DEVIATES (minor) | Uses `load_fence_manifest` and hand-builds the payload rather than calling `fence_attestation_payload`. Manifest sha `35d3375e…` matches the pinned catalog fence — substantively equivalent |
| §5 W5 pipeline version = `sigbar-0.1.0` | `data_types.py:32`; manifest confirms | MATCHES | |
| §4 W6: minute-of-day × day-of-week, per instrument | `baselines.py:43-48` | **FAILS** | `mod` overflows Int8 (Issue 1). The emitted grid is 256 aliased buckets, not 1,440 minutes |
| §4 W6: five metrics incl. `\|Δ\|` and `Δ/V` normalised **separately** | `baselines.py:27-33`; `seasonal_baselines.py:107-119` | MATCHES | `delta_abs` and `delta_ratio` are distinct metrics with independent loc/scale. **A5's separation clause is honoured** — the defect is in the grid key, not the metric split |
| §4 W6: uses "the **W2-pinned** spread feature" | `seasonal_baselines.py:98,111` | DEVIATES | Fits the raw `SpreadBps` column. Execution order confirms it preceded the pin: `seasonal_baselines_manifest.json` 17:09:23Z vs `column_pins.json` 18:11 local. The spread baseline was fitted on a column later pinned UNUSABLE |
| §5 W6: robust scale = **MAD** | `baselines.py:40,100` `1.4826 * MAD` | DEVIATES (minor) | Frozen declaration says MAD; code ships normalised MAD. Standard practice, but §5 is declared frozen — the design text and the manifest (`"scale": "1.4826 * MAD"`) disagree with each other |
| §5 W6: cells < 8 obs flagged SPARSE and **fall back to the day-of-week marginal** | `baselines.py:88-99` | MATCHES | Fallback genuinely implemented (`loc_m`/`mad_m`), not just flagged |
| §5 W6: 10,080 cells per instrument per metric | `baselines.py:81` | **FAILS** | Max realised = 1,792 (= 256 × 7). Cells with zero observations are also absent entirely (no row, no fallback) — `residualise:144` left-joins them to null |
| §5 W6: fallback usage rate disclosed per instrument | `seasonal_baselines.py:140` | PARTIAL | `cells["sparse"].mean()` is the mean over *existing* cells, not over the declared 10,080. Understates the true fallback/no-coverage rate |
| §5 W6 fit band: DESIGN bank only, CONFIRM untouched | `seasonal_baselines.py:43,101` + re-assert `:128-132` | **MATCHES** | Filter `OpenTime < 2023-03-01` plus a post-hoc realised-max assertion that raises. Verified in artifact: max `last_bar` observed `2023-02-28 23:57:00`. **CONFIRM bank is untouched** |
| §4 W7: explain 904 staging vs 894 admitted symbol-by-symbol; no unexplained symbol | `seasonal_baselines.py:176-200` | MATCHES | `admission_reconciliation.json`: 904 staged, 894 admitted, 10 staged-not-admitted each with an `admission` reason (9 `SPEC_INCOMPLETE`, 1 other), `admitted_not_staged: []`. 0 unexplained |
| §7 deliverable `code/admission_reconcile.py` | folded into `seasonal_baselines.py:176-202` | DEVIATES (minor) | W7 now cannot be run without running W6 |
| §8.1: audit covers **all 20** pre-declared symbol-days | `a8:328` | PARTIAL | 20/20 covered in this run. But the verdict rule `n_fail == 0 and n_pass > 0` would return PASS with 1/20 covered and 19 `DOWNLOAD_FAILED` — a partial pass, which §5 forbids (Issue 5) |
| §8.3: baselines exist for all five metrics **per admitted instrument** | artifact | **FAILS** | 194 of 894 admitted symbols fitted; 697 `NO_DESIGN_BANK_BARS`, 3 `ERROR` (corrupt parquet: `KAVAUSDT`, `KLAYUSDT`, `KNCUSDT`). 78% of the admitted cross-section has no baseline (Issue 7) |
| §8.5: re-running reproduces every artifact sha256 | — | UNVERIFIED | No determinism re-run performed. `generated_utc` timestamps are embedded in every JSON, so the JSONs can never be sha-stable by construction; only the parquet can |
| §10 kill-gate HYP-I1 PASS/FAIL semantics | `a8:328,380` | MATCHES | Hard integrity gate with an explicit verdict field — correct under INFR-016 (validity gates stay HARD; only value reads became report layers) |

---

### 2. Golden-trace diff

The design carries no golden-trace block (reasonable — no strategy, no P&L). Hand-evaluated the
load-bearing transforms instead, expectations derived from the design/source text.

| Event | Expected (from design/source) | Implemented | Verdict |
|---|---|---|---|
| Bar at `2023-01-02 05:00:00` → seasonal key | `mod = 300`, `dow = 1` | `mod = 44` (Int8 wrap), `dow = 1` — collides with `00:44` | **FAIL** |
| Bar at `2023-01-02 02:00:00` → seasonal key | `mod = 120` | `mod = 120` | pass (only hours 0–2 are correct) |
| Bar at `2023-01-02 23:59:00` → seasonal key | `mod = 1439` | `mod = −97` | **FAIL** |
| Distinct `mod` values per instrument-metric | 1,440 | 256 (min −128, max 127) | **FAIL** |
| Raw-trade minute `t`, side split → `BuyVolume` | Σ size where side=='buy' | `a8:185` identical | pass |
| A8 reconciliation, BTC 2023-01-11 | rel dev ≤ 1e-9 | 0.0, `NTrades` mismatches 0 | pass (see Issue 6 on interpreting exact 0.0) |
| `SignedBar.ts_event` | bar **close** (`CloseTime`) | `signed_bar_lane.py:114` uses `CloseTime` | pass — L-29 anchor correct |
| Round-trip BTC 2023-01-11 | 1,440 rows, 0 mismatches vs **staging** | 1,440 rows, 0 mismatches vs **the written objects** | weakened (Issue 4) |
| Stored `SpreadBps`, BTC, TRAIN band | design §3(b): n 2,103,839, 39.6% negative, median 0.09 | code (TRAIN-bounded): n 750,081, 32.4% negative, median 0.147 | **design figures do not reproduce on TRAIN** (Issue 2) |

---

### 3. Governance & boundary

| Check | Evidence | Result |
|---|---|---|
| Fence — every code read bounded | `a8:200-204` (day filter), `spread_pin.py:271-275` (`< train_end`), `spread_pin.py:374-380` (`< train_end` **and** day filter), `seasonal_baselines.py:95-104` (`< 2023-03-01`), `signed_bar_lane.py:82-93` (caller-bounded, callers pass `fence.train_end_utc` `:243` or the validation day `:205`) | **PASS** — all 6 `scan_parquet`/`query` sites bounded; the `_tick_bps_reference` fix is complete and correctly reasoned at `spread_pin.py:346-355` |
| Fence — run-time assertions | `a8:300-308`, `seasonal_baselines.py:128-132`, `signed_bar_lane.py:192-193,247-249` | PASS — all raise, none warn |
| **Holdout — design.md's own numbers** | §3(b) BTC n = 2,103,839 = the full staging file (verified: file spans 2022-07-15 → **2026-07-14**, 796,320 bars at/after `holdout_start` 2025-01-08). SOL n = 2,103,447 likewise. Checkpoint-014 §3's null counts (BTC 168 / ETH 4,652 / SOL 7,066) are full-history too — TRAIN-bounded BTC nulls are 158 | **FAIL** (Issue 2) |
| DESIGN/CONFIRM split — CONFIRM untouched | `seasonal_baselines.py:43,101,128-132`; artifact max `last_bar` = `2023-02-28 23:57:00` across all 194 fitted symbols | **PASS** |
| Frozen parameters match §5 | Sample symbols/days: `a8:51-66` ≡ `spread_pin.py:48-49` ≡ §5 ✓. Tolerance `a8:69` = 1e-9 ✓. Failure rule `a8:328` ✓ (with the partial-pass hole, Issue 5). W3 threshold `spread_pin.py:63` = 0.20 ✓. Fit band `seasonal_baselines.py:43-44` ✓. Pipeline version `data_types.py:32` ✓. Grid/scale: **mismatch** — §5 says MAD, code ships 1.4826×MAD; §5 says 10,080 cells, artifact has 1,792 | PARTIAL |
| No evidence of post-result tuning | Constants are module-level and match §5 verbatim; frozen blocks are echoed into the artifacts. No tolerance/sample edits detected | PASS |
| A8 independence (L-01) | `stream_pipeline` not imported anywhere in `code/` or `xen/sigbar/`; recomputation written from the archive schema (`a8:131-190`); raw bytes re-downloaded per symbol-day and discarded (`a8:259`) | **PASS**, with a caveat (Issue 6) |
| A5 fidelity: `\|Δ\|` and `Δ/V` normalised **separately, per instrument** | `baselines.py:27-33`; `seasonal_baselines.py:113-119,136-141`; artifact carries 5 distinct metrics × 194 symbols | **PASS on the separation clause** |
| A5 fidelity: minute-of-day × day-of-week grid | `baselines.py:46` | **FAIL** (Issue 1) |
| `check_no_local_accounting("python/experiments/INFR-017/code")` | run: `{"ok": true, "banned_defs_found": []}` | PASS |
| No Python strategy backtest | none present; W5 is a catalog write | PASS |
| No auto-verdicts / INFR-016 report layers | W3's 0.20 is explicitly framed as a reporting threshold (`spread_pin.py:61-63`); the only `verdict` field is HYP-I1, a hard validity gate — correctly retained | PASS |
| L-28 derangement | N/A — no permutation control in this item | N/A |
| L-29 fill-ts anchor | `ts_event` = bar close, stated and implemented (`signed_bar_lane.py:114`, `data_types.py:22-24`) | PASS |
| L-30 / L-31 (Nautilus node) | No `BacktestNode` constructed; catalog write only | N/A |
| L-21 CONVERSION-PIN / T1 SPREAD-SCALE-ROUTING | N/A — item makes no money-unit or tradability claim | N/A |
| XENA clauses (INFR-006) | N/A — no XENA route | N/A |
| Registry precondition | CF-SIGAUC-001 registered 2026-07-20 (ckpt-014 §2, D1 signed); 0 counted TEST reads | PASS |
| Amendment-direction ledger (L-23) | No pre-measurement amendments recorded this run | N/A |
| Unsourced claims in shared code | `data_types.py:13` asserts the aggressor side was *"verified at INFR-017 W1 (side=Buy co-occurs with PlusTick ~26:1)"*. W1 computes no tick-direction statistic, and no artifact anywhere in the repo contains this figure | **FAIL** (Issue 8) |

---

### Issues

**1 — CRITICAL — the A5 seasonal grid is silently aliased; the baselines artifact is invalid**
Design §4 W6 / §5, source A5 · `python/src/xen/sigbar/baselines.py:46`

```python
(pl.col(time_col).dt.hour() * 60 + pl.col(time_col).dt.minute()).alias("mod")
```

Polars `dt.hour()` and `dt.minute()` return **Int8**. `hour * 60` overflows for every hour ≥ 3 and
the whole expression wraps: verified `02:00 → 120`, `03:00 → −76`, `05:00 → 44`, `23:59 → −97`.
`mod` takes 256 distinct values (min −128, max 127) instead of 1,440.

Consequence: the emitted grid is 256 × 7 = **1,792 cells per instrument-metric** (confirmed on
`results/seasonal_baselines.parquet`: max cells = 1,792 across all 970 symbol-metric pairs), and each
cell pools roughly 5–6 unrelated minutes-of-day. Every "high volume" / "large |Δ|" / "wide spread"
residual computed off this baseline mixes, e.g., 00:44 with 05:00 with 10:16 — which is precisely the
seasonal confound A5 exists to remove. `residualise` (`baselines.py:143`) uses the same key, so the
error is self-consistent and will not surface downstream as an exception; it will surface as
uninterpretable Stage II results.

The manifest is also factually wrong about its own artifact:
`seasonal_baselines_manifest.json.frozen_parameters.grid` claims "1440 minute-of-day x 7 day-of-week
= 10080 cells" against a 1,792-cell file. sha `78dd7988…` must be discarded, not re-pinned.

Required change: cast before arithmetic (e.g. `pl.col(t).dt.hour().cast(pl.Int16) * 60 + …`), assert
`mod` ∈ [0, 1439] and `n_unique(mod) == 1440` in code, refit, and re-hash. Add a unit test over a
synthetic 1,440-minute day asserting the key is the identity on minute index.

**2 — BLOCKING (operator adjudication) — design.md §3(b)'s "measured" figures were computed across the sealed holdout**
design.md §3(b) table; ckpt-014 §3 row 2 · no live code path

The §3(b) table reports BTCUSDT `n = 2,103,839` and SOLUSDT `n = 2,103,447`. Those are the **full
staging row counts**, verified: `BTCUSDT.parquet` spans 2022-07-15 → 2026-07-14 and contains 796,320
bars at or after `holdout_start` 2025-01-08. The TRAIN-bounded recomputation in `spread_pin.py:271-275`
returns `n = 750,081`, 32.4% negative, median 0.147 — the design's 39.6% / median 0.09 does not
reproduce on TRAIN. The null counts quoted in checkpoint-014 §3 (BTC 168) are likewise full-history;
TRAIN gives 158.

The code was fixed; the *design* was not. §3(b) is framed as "pre-audit ground truth… established on
disk before any design decision" and it is what sets the item's agenda (W2 exists because of it), so
the touch is load-bearing on the design, not incidental. Mitigating: it is a univariate distribution
of a data-quality column, not an edge or P&L read, and it spends no sanctioned shot. I am not calling
REJECT on that basis, but per the skill this is an operator call, not mine to clear.

Required change: recompute §3(b) and the ckpt-014 §3 null counts on `OpenTime < train_end_utc`,
restate both tables with the TRAIN figures, and record the touch explicitly (what was read, when, why
it does not consume a read). Propagate to `data_types.py:20` ("negative ~40% of minutes on BTC" —
32.4% on TRAIN).

**3 — MAJOR — the W2 pin records no decision, no rejected-option reasons, and no hash**
design.md §4 W2, §8.2 · `spread_pin.py:384-397`, `results/column_pins.json`

§8.2 requires the pin to state "the chosen resolution with reasons for the rejected options, the W3
dependence figure with CI, and the W4 `NTrades` verdict — all hash-pinned". `build_pin` emits four
numbers per symbol. The artifact has no `decision`, no rationale for rejecting (i) recompute or (ii)
floor-and-flag, and no self-sha256. Meanwhile `signed_bar_lane.py:129` hard-codes
`SPREAD_UNUSABLE` — so the decision was made and is encoded in a *different* file from the pin that
is supposed to freeze it. That is exactly the drift shape the pin exists to prevent, and INFR-018
inherits an unpinned decision.

Note the measured evidence supports a stronger option than UNUSABLE: candidate C (flip-pair) returns
0.0% negatives on all five symbols with medians of 0.244 / 0.305 / 0.727 / 1.470 / 1.929 bps against
one-tick references of 0.043 / 0.058 / 0.376 / 1.477 / 1.965 bps — i.e. a plausible, non-negative,
tick-consistent estimator. Whether to ship it (option i) is a design call; either way the reason must
be written down.

Required change: add an explicit `W2_decision` block (chosen option, reason, reasons each rejected
option lost, evidence references) and a self-sha256; make `signed_bar_lane.py` read the status from
the pin rather than hard-code it.

**4 — MAJOR — the W5 round-trip does not compare against the staging source**
design.md §4 W5, §8.4 · `signed_bar_lane.py:138-178`, esp. `:144-146,159-164`

The check zips `written` against `read`. `source` appears only as `result["n_source_rows"]` (`:149`).
It therefore proves Nautilus serialisation is lossless — which was already proven at INFR-013 — and
proves nothing about `to_signed_bars`. Swap `BuyVolume` and `SellVolume` at `:123-124` and this test
still reports `exact_match: true`. The design's exit condition is equality with *the staging source*.

Required change: compare read-back rows against the `source` DataFrame directly (join on ts, assert
`Volume == volume`, `BuyVolume == buy_volume`, `SellVolume == sell_volume`,
`NTrades == n_trades`, `BuyVolume − SellVolume == delta`, and `OHLC`), and include `spread_feature`
and `spread_status` in the comparison. Also add the missing `config_hash` field required by §4 W5.

**5 — MODERATE — the kill-gate admits two silent partial passes**
design.md §5 ("No partial pass"), §8.1 · `a8_provenance_audit.py:220,275-279,328`

(a) `verdict = "PASS" if (n_fail == 0 and n_pass > 0)`. Nineteen `DOWNLOAD_FAILED` days plus one PASS
returns PASS. §8.1 requires coverage of all 20 declared symbol-days. Add a coverage requirement:
`n_pass == len(SAMPLE_SYMBOLS) * len(SAMPLE_DAYS)`, else `FAIL_INCOMPLETE_COVERAGE`.
(b) The inner join means unmatched bars never enter the deviation statistics. Promote a bar-count or
key-set mismatch to FAIL rather than a `detail` string.
Neither bit in this run (20/20 PASS, all counts equal), so the recorded HYP-I1 PASS stands on its
evidence — but the gate as coded is not the gate as declared.

**6 — MODERATE (note, no change strictly required) — how to read `max_rel_dev == 0.0`**
`results/a8_provenance_audit.json`

All 20 symbol-days report **exactly** 0.0 relative deviation on `Volume`, `BuyVolume`, `SellVolume`.
That is stronger than "matches to rounding" and is worth stating plainly: it means the audit and the
producing pipeline perform the same float summation over the same rows in the same order using the
same library. Independence here is genuine at the level of *code path* (no import — L-01 satisfied)
but not at the level of *algorithm*. Residual blind spot: the audit copies the INFR-011 cleaning rule
(`a8:167-173`, declared at `a8:342`), so a defect in that rule reproduces silently. Mitigated by
`NTrades` matching exactly and `n_bars_raw == n_bars_stored` on all 20 days, which bounds any
systematic trade-dropping to zero on the sample. Recommend the report state this explicitly rather
than presenting 0.0 as extraordinary corroboration.

**7 — MODERATE — §8.3 is unmet and the shortfall is not flagged**
design.md §8.3 vs §5 W6 fit band · `results/seasonal_baselines_manifest.json`

194 of 894 admitted symbols were fitted. 697 returned `NO_DESIGN_BANK_BARS` (they list after
2023-03-01) and 3 failed on corrupt parquet (`KAVAUSDT`, `KLAYUSDT`, `KNCUSDT`). §8.3 says baselines
"exist for all five metrics per admitted instrument" — as written it is unachievable under the §5
DESIGN-bank restriction, and the artifact does not surface the 78% shortfall as a finding.

This matters beyond bookkeeping: ckpt-014 §6 routes SPDR-008 at the "full ADMITTED cross-section"
with anti-survivorship binding, and the breadth advantage is the family's stated thesis. Roughly
four-fifths of that cross-section currently has no A5 apparatus, and the 194 that do are precisely the
symbols listed before 2023-03 — a survivorship-shaped subset. Needs a designer decision (extend the
baseline fit band beyond the DESIGN bank for late-listing symbols? per-symbol fit windows? declare
the scope limit?), not a code patch. Separately, the 3 corrupt staging parquets should go back to
INFR-011.

**8 — MODERATE — unsourced verification claim in shared code**
`python/src/xen/sigbar/data_types.py:13`

> "Bybit's archive `side` column is the **aggressor** side; verified at INFR-017 W1 (side=Buy
> co-occurs with PlusTick ~26:1)."

W1 computes volume/count reconciliation only; it never touches tick direction. Grepping the repo finds
no artifact containing this figure. A shared data contract must not assert a verification that its
cited source did not perform — INFR-018 and SPDR-007 will read this docstring as established.
Required change: delete the claim, or run the tick-direction check, emit it into
`a8_provenance_audit.json`, and cite the artifact.

**9 — MINOR — cells with zero observations vanish from the grid**
`baselines.py:81`

`group_by(["mod","dow"])` only yields cells that have data. Empty cells produce no row at all — they
are neither marked `sparse` nor given the day-of-week fallback, and `residualise:144` left-joins them
to a null residual. Independent of Issue 1 and will persist after it is fixed (thin symbols:
`USTUSDT` currently yields 858 of a possible 1,792). Materialise the full grid, mark uncovered cells,
and apply the fallback. Relatedly, `sparse_cell_rate` (`seasonal_baselines.py:140`) averages over
existing cells only and so understates coverage loss — denominate it on the declared grid size.

**10 — MINOR — assorted design/code disagreements**
- `baselines.py:40,100`: ships `1.4826 × MAD`; §5 declares "MAD". Reconcile the text (the code is the
  better statistic; the frozen declaration is what is wrong).
- `baselines.py:102-107`: comment says "Floor the scale" and the docstring says "floored above zero",
  but the code sets non-positive scale to **null**. Two different downstream behaviours; the
  docstring is wrong.
- `spread_pin.py:156-170` `estimator_stored` is labelled "reproduce the stored definition" but uses
  `mean(all prices)` as the denominator where the stored definition uses `(MeanBuy + MeanSell)/2`
  (`spread_pin.py:78`). Candidate A is therefore not the stored column. Conclusions are unaffected
  (the numerator drives the sign), but a pin artifact must not mislabel its own baseline.
- `spread_pin.py:117-148` never sorts trades by timestamp, yet `estimator_flip_pair:191-195` depends
  on row order via `shift(1)`. Bybit archive day-files are not uniformly time-ordered. Add an explicit
  `.sort("timestamp")`.
- `spread_pin.py:241-257`: the Fisher-z CI assumes independent observations on minute-level data;
  reported as ±0.026 on n=5,760. Disclosure-only, so not blocking, but label it as not
  dependence-honest.
- `spread_pin.py:342` `_tick_bps_reference(symbol, sample, staging_dir)` — `sample` is unused.
- `spread_pin.py:369` day filter uses `< d.replace(hour=23, minute=59)`, dropping the 23:59 bar of each
  sampled day. Harmless for a median, but inconsistent with `a8:196`, which includes it.
- §7 declares `code/admission_reconcile.py`; W7 is implemented inside `seasonal_baselines.py:176-202`,
  so it cannot be run independently. Either split it or amend §7.
- §4 W5 says the ingest writes `data/catalog/`; the code writes `data/catalog_sigbar/`
  (`signed_bar_lane.py:51`). The code's choice is right — amend the design so the two agree.
- §8.5 (determinism / sha reproducibility) was never exercised, and every JSON embeds `generated_utc`,
  so JSON shas can never be stable. Either exclude the timestamp from the hashed payload or restate
  §8.5 as parquet-only.

---

### What is sound

Recorded so the rebuild does not re-litigate it: the TRAIN fence on all six code read paths is correct
and asserted, including the `_tick_bps_reference` repair; the DESIGN/CONFIRM split holds with a
post-hoc realised-max assertion and is confirmed in the artifact; A8 independence from
`stream_pipeline` is real; the A5 `|Δ|`-vs-`Δ/V` separation clause is honoured; the SPARSE
day-of-week fallback is genuinely implemented; W7 reconciles 904→894 with zero unexplained symbols;
`ts_event` is anchored to bar close per L-29; no local accounting primitives; and the one hard verdict
field is a validity gate, correctly left hard under INFR-016.

---

## QA run 2 — 2026-07-20T17:37Z — mode: subagent — HEAD af7bf9e1f2f8aea4756a7eb73ff7828c6b997a09

Reviewed git state: HEAD `af7bf9e` + working-tree additions (untracked `python/experiments/INFR-017/`,
`python/src/xen/sigbar/`, `python/tests/test_sigbar_baselines.py`,
`docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/`,
`docs/signal-registry/candidate-families/cf-sigauc-001.md`; modified `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/multiplicity-registry.md`).

Scope: re-review after run 1 REVISE. (a) verify each run-1 issue is genuinely fixed rather than
papered over; (b) hunt for defects the fixes introduced. Re-run artifacts present (mtimes 18:26–18:28
local). `report.md` is new this round and was not covered by run 1 — reviewed here for the first time.

**Verdict: REVISE** (both run-1 blockers genuinely fixed; one MAJOR and one MODERATE regression in the
documentation/handoff layer. No code defect, no new fence violation.)

**FAILING_ARTIFACT (primary):** `python/experiments/INFR-017/report.md` §8
**REQUIRED_SKILL (primary):** `experiment-documenter`
**FAILING_ARTIFACT (secondary):** `docs/signal-registry/candidate-families/cf-sigauc-001.md` §3
**REQUIRED_SKILL (secondary):** `experiment-developer` (Issues 13–16, artifact labelling only)

---

### 1. Run-1 issue disposition (verified independently, not accepted on claim)

| # | Run-1 issue | Claim | Verification performed | Verdict |
|---|---|---|---|---|
| 1 | CRITICAL Int8 overflow in seasonal grid | Int32 casts, `assert_seasonal_keys_valid`, `_full_grid()`, regression test, new sha | Read `baselines.py:48-91`. Re-read the emitted parquet: **9,777,600 rows = 970 symbol-metric pairs × exactly 10,080 cells** (min=max=10,080); `mod` spans **0–1439 with 1,440 distinct values**; `dow` 1–7; `(symbol,metric,mod,dow)` unique on all 9,777,600 rows. Reproduced the OLD expression directly: `[120, -76, 44, -18, -97]` vs the test's asserted `[120, 180, 300, 750, 1439]` — **the test genuinely fails against the old code**, it is not a tautology. `pytest tests/test_sigbar_baselines.py` → **5 passed**. Parquet sha recomputed from bytes = `1b7244c8…` = manifest value; old `78dd7988…` absent from the artifact | **FIXED** |
| 2 | BLOCKING holdout-crossing figures in design §3(b) | Table restated on TRAIN, ckpt-014 §3 corrected, `data_types.py` corrected, explicit NOT-self-cleared disclosure | design.md §3(b) now reads BTC 750,081 / 32.4% / 0.147 / 158 nulls — **reproduces exactly from `column_pins.json.per_symbol.*.stored_column_full_train`** (32.374, null 158) for all five symbols. Disclosure block present at design.md:60-73, marked "Recorded, not self-cleared". ckpt-014 design.md:69 corrected to TRAIN counts **with** the correction noted. `data_types.py:22` now 32.4%/39.9%. Grepped repo for `2103839 / 2,103,839 / 2103447 / 39.6 / 4652 / 7066`: all surviving hits are the QA file itself or explicitly-labelled "originally reported" disclosure text — **except one** (Issue 12) | **FIXED in the experiment; one propagation missed** |
| 3 | MAJOR W2 pin recorded no decision | `W2_decision` block, `pin_sha256` excluding `generated_utc`, ingest reads status via `load_w2_pin()` | `column_pins.json` carries `W2_decision` with `chosen`, `stored_column_status`, `stored_column_reason`, `replacement_estimator` (incl. `known_bias`, `blocker_to_full_adoption`), `rejected_options` for both (i) and (ii) with distinct reasons, `downstream_constraint`. `W4_ntrades_verdict` now present too (run 1 had it MISSING). **Ingest genuinely cannot run without the pin**: `load_w2_pin` (`signed_bar_lane.py:98-113`) raises `RuntimeError` on a missing file and is called unconditionally by **both** `run_validation:257` and `run_ingest:304` before any write; no fallback constant. `SPREAD_UNUSABLE` no longer read in this file. **`pin_sha256` recomputed from the artifact = `f210a05b9bbb…` = recorded value** — self-consistent and stable across reruns of identical inputs by construction | **FIXED** (see Issue 14 on the numbers *inside* the block) |
| 4 | MAJOR W5 round-trip compared written objects against themselves | `roundtrip_check` joins read-back against staging `source` on ts_event, nine mapped columns | `signed_bar_lane.py:158-246`: `read_df` is built from `catalog.query`, `src_df` from the staging frame, joined on `ts_event`, with count-match and key-set-match early exits, then nine `src_col != field` comparisons plus the buy+sell==volume invariant. **A deliberate `BuyVolume`/`SellVolume` swap in `to_signed_bars:143-144` would now fail**: `BuyVolume->buy_volume` and `SellVolume->sell_volume` both mismatch on every row, and `Delta->delta` mismatches too (source `Delta` is derived independently at `load_staging_window:95`). Note the split invariant alone is symmetric under that swap and would *not* catch it — the column pairs are what does the work | **FIXED** (partial: Issues 15, 16) |
| 5 | MODERATE kill-gate partial passes | Coverage requirement + count/key-set mismatch promoted to FAIL | `a8_provenance_audit.py:440-445`: `n_fail>0 → FAIL`; `n_pass < declared → FAIL_INCOMPLETE_COVERAGE`; else PASS. The 19-DOWNLOAD_FAILED-plus-1-PASS hole is closed. `:339` PASS now additionally requires `counts_agree`, so a bar-count/key-set disagreement is a FAIL, not a `detail` string | **FIXED** |
| 6 | MODERATE how to read `max_rel_dev == 0.0` | (note only) | report.md §7d states it plainly: same float summation, independence at code-path not algorithm level, L-01 satisfied, bounded by `NTrades` exact + bar counts agreeing | **ADDRESSED** |
| 7 | MODERATE 194/894 baseline coverage | Escalated to operator, not a code fix | **Properly disclosed, not dropped.** report.md §6 gives the population table (894 / 296 / 197 / 194), §8 "May NOT rely on" makes the 296 limit binding on INFR-018, and §6 carries an explicit *recommended checkpoint amendment* marked operator's call with a NEUTRAL L-23 direction. Manifest lists all 894 per-symbol statuses (194 OK / 697 `NO_DESIGN_BANK_BARS` / 3 `ERROR`); the 3 corrupt parquets are named in §7d and routed back to INFR-011 | **DISCLOSED** (as intended) |
| 8 | MODERATE unsourced tick-direction claim | `aggressor_side_evidence()` computes the cross-tab in W1, emits `aggressor_side_convention`, docstring cites the artifact | `a8_provenance_audit.json.aggressor_side_convention` present: 20 symbol-days, `convention: AGGRESSOR`, `unanimous: true`, `buy_plus_over_buy_minus` median **26.23** (min 5.27, max 371.98) — the "~26:1" figure now has a computed source. `data_types.py:11-15` no longer asserts the result; it says the evidence is emitted and instructs "Cite that artifact, not this docstring" | **FIXED** |
| 9 | MINOR empty cells vanish / sparse denominator | Full grid materialised | Uncovered cells are now explicit rows (`n=0`, `sparse=true`, dow fallback) — 103,371 such rows in the artifact. `sparse_cell_rate` (`seasonal_baselines.py:140`) is now `cells["sparse"].mean()` over the **full 10,080-cell** frame, so the denominator is the declared grid by construction | **FIXED** (but see Issue 16) |
| 10 | MINOR assorted design/code disagreements | various | `estimator_stored:166` now uses `(mb+ms)/2` as denominator — matches the stored definition; `_read_trades:142` now `.sort("timestamp")` before the `shift(1)` in `estimator_flip_pair`; `_tick_bps_reference:344` unused `sample` param removed; day filter `:369` now `< d + timedelta(days=1)` — the dropped 23:59 bar is restored and consistent with `a8:257`; design §5 now declares "1.4826 × MAD"; `baselines.py:154-162` docstring/comment now say **null** (not "floored"), matching the code; design §4 W5 now says `data/catalog_sigbar/`; design §7 lists W7 inside `seasonal_baselines.py`; design §8.5 restated as parquet sha + `pin_sha256` only; W3 threshold consequence now actually coded (`build_w3_verdict:401-437` sets `breached` and swaps the constraint text) | **FIXED** |

---

### 2. Governance & boundary (re-verified after the edits)

| Check | Evidence | Result |
|---|---|---|
| **Fence — no NEW violation introduced** | All 5 parquet read sites re-enumerated and each bound re-read: `seasonal_baselines.py:95` (`>= ANALYSIS_START & < DESIGN_BANK_END`), `signed_bar_lane.py:81` (caller-bounded; callers pass `fence.train_end_utc` `:315` or the validation day `:274`), `a8:255` (`>= lo & <= hi`, single day), `spread_pin.py:273` (`< TRAIN_END_UTC`), `spread_pin.py:375` (`< TRAIN_END_UTC` **and** day filter). The 6th site is `catalog.query` on the freshly-written validation catalog. Staging parquets do extend to 2026-07-14, past `holdout_start` 2025-01-08 — **every read is bounded** | **PASS** |
| Fence — assertions raise, not warn | `signed_bar_lane.py:261-262` (validation day inside TRAIN), `:320-321` (realised max < train_end), `seasonal_baselines.py` caller re-assert, `a8:300-308` | PASS |
| Fence manifest | `35d3375ec5ec…` — matches the pinned OHLCV catalog fence; `train_end 2023-12-18`, `holdout_start 2025-01-08` confirmed by loading the manifest | PASS |
| DESIGN/CONFIRM split still holds after refit | Max `last_bar` across all 194 fitted symbols = **`2023-02-28 23:59:00`** < `2023-03-01`. (Run 1 saw 23:57; the full-grid refit reaches 23:59 because the key no longer wraps — expected, still inside the bank) | **PASS** |
| `_full_grid()` did not corrupt `sparse` semantics | `sparse = n < 8` is applied **after** `fill_null(0)`, so `n=0` cells are `sparse=true` and inherit the dow marginal — consistent with design §5 ("cells with < 8 observations"). Left-joins verified non-duplicating: row count is exactly `970 × 10,080` with no key duplication | **PASS** on semantics; see Issue 16 on *reporting* |
| `pin_sha256` stability | Recomputed `sha256(json.dumps({k:v for k,v in payload if k != 'generated_utc'}, sort_keys=True, default=str))` from the artifact → **exact match** to the recorded value | **PASS** |
| Report/design/artifact number consistency | design §3(b) and report §3 tables reproduce cell-for-cell from `column_pins.json`. W3 table (§4) reproduces. W4 medians (§5) reproduce. Kill-gate figures (§2) reproduce. Grid claims (§5, §7a) reproduce from the parquet. **Three exceptions: Issues 11, 13, 14** | **PARTIAL** |
| `check_no_local_accounting("python/experiments/INFR-017/code")` | re-run: `{"ok": true, "banned_defs_found": []}` | PASS |
| No Python strategy backtest / no `BacktestNode` (L-30, L-31) | none; W5 is a catalog write | N/A |
| L-28 derangement / L-21 CONVERSION-PIN / T1 routing / XENA clauses | no permutation control, no money-unit or tradability claim, no XENA route | N/A |
| L-29 fill-ts anchor | `ts_event` = `CloseTime` (`signed_bar_lane.py:133`) | PASS |
| Registry precondition | CF-SIGAUC-001 registered; 0 counted TEST reads; report §5 states "0 counted reads, 0 slots" | PASS |
| L-23 amendment direction | report §6 carries a NEUTRAL-tagged recommended amendment routed to the operator; no directional streak | PASS |
| Regression test added and meaningful | `python/tests/test_sigbar_baselines.py`, 5 cases, all pass, and case 2 provably fails against the pre-fix expression | PASS |

---

### Issues (run 2)

**11 — MAJOR — `report.md` §8 hands INFR-018 the *discarded* baseline sha**
`python/experiments/INFR-017/report.md:161`

> "The A5 seasonal baselines (`seasonal_baselines.parquet`, sha256 `78dd7988…`) for every threshold"

`78dd7988…` is the sha of the **invalid, aliased artifact** that §7a of the same report explicitly says
is "discarded, not re-pinned". The emitted parquet's sha, recomputed from bytes, is
`1b7244c87aaafe29…`, and §5 and §7a both quote it correctly. §8 is the section that defines what the
next item may freeze on, so this is the one place the wrong hash does real damage: INFR-018 either
fails its pin check or, worse, goes looking for the superseded file. This is precisely the
pin-drift shape Issue 3 was raised about, reintroduced one section later.

Required change: replace with `1b7244c8…` in §8 and re-read the report for any other sha reference.

**12 — MODERATE — the holdout-derived null counts survive uncorrected in the family registry**
`docs/signal-registry/candidate-families/cf-sigauc-001.md:49`

> "| P4 spread proxy | `SpreadAbs` `SpreadBps` | present, **has nulls** (BTC 168, ETH 4,652, SOL 7,066 minutes) …"

These are the **full-history** counts — the same holdout-crossing scan Issue 2 was raised about. The
TRAIN figures are BTC **158**, ETH **4,543**, SOL **6,951** (`column_pins.json`, and now design §3(b)).
The fix propagated to design.md, checkpoint-014 §3 and `data_types.py` but stopped short of the family
registry, which is the durable cross-chapter record downstream items read. An incompletely propagated
correction of a BLOCKING finding reads, later, as an unflagged holdout figure.

Required change: restate the three counts on TRAIN and carry the same one-line correction note that
checkpoint-014 §3 now carries.

**13 — MODERATE — the breadth numbers driving a checkpoint amendment reproduce from no result file**
`report.md:109-111` (296 / 197), inherited by §8 "May NOT rely on"

report §6 presents 296 (any bars before TRAIN end) and 197 (before DESIGN-bank end) in a table headed
"Measured", and they carry real weight: they are the basis of a recommended amendment to
checkpoint-014's SPDR-008 universe and of a binding limit on INFR-018. Neither number appears in any
file under `results/`, and no function in `code/` computes them.

I recomputed both independently over the 894 admitted symbols (min `OpenTime` per staging parquet vs
`2023-12-18` and `2023-03-01`): **296 and 197 — both correct**. So this is a provenance gap, not an
error. But a number that amends a checkpoint must be re-derivable from an artifact, not from prose.

Required change: emit both counts (and the per-symbol first-bar basis) into
`admission_reconciliation.json` or the baselines manifest, and cite the file from §6.

**14 — MODERATE — the hash-pinned W2 decision quotes sample-day figures under a TRAIN-band label**
`spread_pin.py:450-459` → `column_pins.json.W2_decision.stored_column_reason`

> "Measured negative on the **TRAIN band** in {'BTCUSDT': 30.99, 'ETHUSDT': 40.538, 'SOLUSDT': 22.814,
> 'DOGEUSDT': 11.708, 'XRPUSDT': 7.593} percent of minutes"

`build_decision` sources these from `build_pin` → `sample.candidate_A_stored_definition.pct_negative`,
which is the **4-sample-day recomputation** (n ≈ 5,760), not the TRAIN column. The full-TRAIN figures
live in the same artifact under `stored_column_full_train` and are 32.374 / 39.939 / 24.937 / 11.506 /
7.282 — which is what design §3(b) and report §3 publish. The pin therefore disagrees with the design
and the report by 1–2 points on every symbol, inside the one block that is frozen and hash-pinned as
the decision of record.

Not a fence issue (the four sample days are inside TRAIN) and it does not change the decision — every
figure is unambiguously non-trivial. But a pin must not mislabel its own evidence, and the label says
"TRAIN band" while the number says "20 symbol-days".

Required change: either quote `stored_column_full_train.pct_negative` and keep the "TRAIN band"
wording, or keep the sample figures and label them "on the 20-symbol-day audit sample". Re-hash.
Related: `analyse_stored_column`'s docstring (`spread_pin.py:268`) still says *"Full-history
distribution"* while the body filters `< TRAIN_END_UTC` — stale prose on the exact function whose
unbounded read caused Issue 2.

**15 — MINOR — the round-trip still omits the two fields run 1 named**
`signed_bar_lane.py:218-228`, `:293`

Run 1's required change was to compare the nine mapped columns "and include `spread_feature` and
`spread_status` in the comparison". `pairs` covers OHLC + Volume + Buy/Sell + NTrades + Delta; neither
spread field is compared, so a mis-mapping of `SpreadBps → spread_feature`, or a status stamped from
the wrong branch at `:148`, round-trips unnoticed. Low impact while the pin says UNUSABLE — but the
field is carried into every record and INFR-018 reads it.

Separately, the manifest reports `signed_fields_checked = SIGNED_FIELDS + ["ts_event"]` (`:293`), i.e.
volume/buy/sell/delta/n_trades — which **understates** the check (OHLC are compared too) while
implying spread coverage that does not exist. Derive that list from `pairs` rather than from a
constant that is no longer what the check uses.

**16 — MINOR — `sparse` now conflates "thin" with "no data at all", and the difference is undisclosed**
`baselines.py:148`, `seasonal_baselines.py:140`

A consequence of the (correct) full-grid fix. `sparse = n < 8` now covers both a cell with 5
observations (fallback is a reasonable shrink) and a cell with **0** observations (fallback is pure
extrapolation onto a time-of-week the instrument never traded). `sparse_cell_rate` is the only figure
disclosed, so the two are indistinguishable in the manifest.

Measured on the artifact: **73 of 194 symbols have uncovered cells**. `USTUSDT` reports
`sparse_cell_rate = 1.0` while **62% of its grid has zero observations and 43% has no usable baseline
at all** (`loc` null → null residual downstream); `BUSDUSDT` 61% uncovered; `1000FLOKIUSDT` 42%. A
consumer reading `1.0` cannot tell "thin everywhere" from "most of this grid does not exist", and the
null-baseline rate — the one that silently produces null residuals in `residualise` — is reported
nowhere.

Required change: disclose `uncovered_cell_rate` (`n == 0`) and `no_baseline_rate` (`loc` null)
alongside `sparse_cell_rate`, per symbol per metric.

**17 — MINOR (latent) — the round-trip mismatch count is blind to nulls**
`signed_bar_lane.py:230`

`(pl.col(src_col) != pl.col(field)).sum()` — in Polars a null on either side yields null, and `sum`
skips nulls, so a null-vs-value disagreement counts as **zero mismatches**. Verified directly:
`{'a':[1.0,None,3.0]}` vs `{'b':[1.0,5.0,3.0]}` → mismatch count `0`.

Not live: I checked the nine compared columns across the first 120 staging symbols and found **zero
nulls**, so the current `exact_match: true` stands on real evidence. It would bite at universe-scale
ingest on any symbol carrying a null in a signed field. Use `.ne_missing()` (or add an explicit
null-count assertion on both sides).

---

### What is sound (run 2)

The two run-1 blockers are genuinely resolved, not papered over: the grid defect is fixed in the
expression, guarded at the point of use, materialised to the full 10,080 cells, proven in the emitted
parquet, and pinned by a regression test that demonstrably fails against the old code; the holdout
touch is corrected in the design, the checkpoint and the shared docstring, and carries an explicit
"NOT self-cleared, operator's call" disclosure rather than a quiet edit. The W2 pin now states its
decision with rejected-option reasons and a reproducible self-hash, and the ingest cannot run without
reading it. The round-trip compares against staging and would catch the Buy/Sell swap that motivated
the finding. The kill-gate's two partial-pass holes are closed. The aggressor-side claim is now a
computed, emitted number. All five staging read paths remain bounded — no new fence violation was
introduced by the edits — and the CONFIRM bank is still untouched. Every run-1 MINOR was addressed.

The residue is documentation and artifact labelling: a stale sha in the handoff section, an
uncorrected registry row, two unsourced-but-correct figures, and a mislabelled evidence line in the
pin. No re-run of the pipeline is required to clear them — but the sha in §8 must not reach INFR-018.

---

## QA run 3 — 2026-07-20T17:48Z — mode: subagent — HEAD af7bf9e1f2f8aea4756a7eb73ff7828c6b997a09

Reviewed git state: HEAD `af7bf9e` + working-tree additions (untracked `python/experiments/INFR-017/`,
`python/src/xen/sigbar/`, `python/tests/test_sigbar_baselines.py`,
`docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/`,
`docs/signal-registry/candidate-families/cf-sigauc-001.md`; modified `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/multiplicity-registry.md`).

Scope: narrow final check on the four run-2 bookkeeping items and three minor notes, plus the
declared regression battery. Items confirmed sound in runs 1–2 were **not** re-litigated.

**Verdict: REVISE** (one item, item 4, is mitigated but not fixed where it was flagged. Items 1, 2, 3
and all three minor notes verified genuinely fixed. No code defect, no fence violation, no regression.)

**FAILING_ARTIFACT:** `python/experiments/INFR-017/results/column_pins.json` → `W2_decision.stored_column_reason`
(source `python/experiments/INFR-017/code/spread_pin.py`)
**REQUIRED_SKILL:** `experiment-developer`

---

### 1. Run-2 item disposition (verified from the artifacts, not accepted on claim)

| # | Run-2 item | Verification performed | Verdict |
|---|---|---|---|
| 1 | report §8 cited the discarded baseline sha | `sha256(seasonal_baselines.parquet)` recomputed from bytes = **`1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72`** = `seasonal_baselines_manifest.json.artifact_sha256`. `report.md:176` (§8) now cites `1b7244c87aaafe29…` **and** names `78dd7988…` as the discarded one. Every other sha reference re-read: `:99` (§5) `1b7244c8…` ✓, `:130` (§7a) discard note ✓, `:165` (§7e) correction record ✓. **No location in the report hands a consumer the wrong hash** | **FIXED** |
| 2 | family registry carried holdout-derived null counts | `cf-sigauc-001.md:49` now "**on the TRAIN band** (BTC 158, ETH 4,543, SOL 6,951 minutes)"; `multiplicity-registry.md:1481` now "TRAIN band: BTC 158 / ETH 4,543 / SOL 6,951 null minutes". Both reproduce from `column_pins.json.per_symbol.*.stored_column_full_train.n_null`. Scoped grep over `docs/signal-registry`, `docs/experiments-docs`, `python/experiments/INFR-017`, `python/src/xen/sigbar`, `python/tests` for `2103839 / 2,103,839 / 2103447 / 2,103,447 / 78dd7988 / 39.6% / 4,652 / 7,066 / 4652 / 7066`: **4 surviving hits, all legitimate** — `report.md:130` (discard note), `:138` (§7b holdout disclosure), `:165–166` (§7e correction record), `design.md:61-62` (§3(b) standing disclosure). Every one is explicitly framed as "originally reported / discarded / corrected to". Repo-wide hits outside this scope are chapter-02 archive coincidences (`EXP-014/015/025`, `SPDR-002`), unrelated | **FIXED** |
| 3 | breadth numbers were prose-only | `admission_reconciliation.json.band_coverage` present: `n_admitted` 894, `n_with_bars_before_train_end` 296 (`train_end_utc` 2023-12-18), `n_with_bars_before_design_bank_end` 197 (`design_bank_end_utc` 2023-03-01), plus a `note` and a `survivorship_caveat`. **Recomputed independently** from `INFR-011/artifacts/admission-ledger.jsonl` (910 rows, 894 ADMITTED, 0 missing `first_bar`): **296 and 197 — exact match**. Computation at `seasonal_baselines.py:204-209` uses `first_bar < DESIGN_BANK_END / < TRAIN_END` over the admitted set — correct basis. `report.md:106` (§6) now cites the artifact by path and key before presenting the table | **FIXED** |
| 4 | pin mislabelled sample-day figures as TRAIN-band | Top-level `band_note` added ✓ ("TWO DISTINCT SCOPES, do not conflate…"). `scope` labels added to both blocks ✓ (`stored_column_full_train` → "FULL TRAIN band (OpenTime < train_end_utc)"; `sample` → "4 pre-declared SAMPLE DAYS only — not the full TRAIN band"). **But the sentence run 2 actually flagged is unchanged** — see Issue 18 | **MITIGATED, NOT FIXED** |
| m1 | round-trip omitted `spread_feature` / `spread_status` | `signed_bar_lane.py:249-264`: `SpreadBps->spread_feature(+status)` comparison added, and it is **status-coupled** — `SpreadBps.is_null() != (spread_status == SPREAD_MISSING)` catches a status stamped from the wrong branch at `:148`, and the value leg catches a mis-mapping. Emitted into `field_mismatches`. Correct construction | **FIXED** |
| m2 | mismatch counter blind to nulls | `signed_bar_lane.py:229-246`: replaced with `(a.is_null() != b.is_null()) \| (a.is_not_null() & b.is_not_null() & (a != b))`. This is null-correct — a null-vs-value disagreement now counts 1, matching `.ne_missing()` semantics — and applied to **all nine** `pairs` entries plus the spread leg. Comment cites the finding | **FIXED** |
| m3 | `cell_coverage` conflated empty with thin | `seasonal_baselines.py:143-144`: `empty_cell_rate` = `(n == 0).mean()` and `thin_but_nonempty_rate` computed separately; emitted at `:159` under `cell_coverage` on the full grid. The two failure modes run 2 named (`USTUSDT` "1.0 sparse" hiding 62% empty) are now distinguishable. `report.md:158` discloses the split | **FIXED** |

---

### 2. Regression battery (all declared checks run)

| Check | Evidence | Result |
|---|---|---|
| `pin_sha256` moved to `e495d349…` | Recorded `e495d34922be8bf3790697dc4072d49ed11ba428be700f5f1ce0d4524bd05a6d` | confirmed |
| `pin_sha256` **recomputes** from the artifact | `sha256(json.dumps({k:v for k,v in payload if k != 'generated_utc'}, sort_keys=True, default=str))` over the emitted file → **exact match** to the recorded value | **PASS** |
| `pin_sha256` **stable across reruns** | `spread_pin.py:563-568` excludes `generated_utc` from the hashed payload and sorts keys; the only other time-varying field in the payload is `generated_utc` itself. Hash is therefore a pure function of the measured inputs — stable across reruns of identical inputs by construction | **PASS** |
| Lane manifest tracks the new pin (no stale stamp) | `signed_lane_manifest.json.roundtrip.w2_pin_sha256` = `e495d349…` — **identical to `column_pins.json.pin_sha256`**. Records are stamped from the same value: `run_validation:290` / `run_ingest:337` call `load_w2_pin()`, pass `pin_sha` into `to_signed_bars(...)`, which sets `config_hash=config_hash` at `:150`. No path can stamp a pin that no longer exists | **PASS** |
| `seasonal_baselines.parquet` sha UNCHANGED | Recomputed from bytes = `1b7244c87aaafe29…` = the run-2 value and the manifest value. The W6 report-layer/coverage edits touch only the emitted JSON summary, not the fitted frame | **PASS (deterministic)** |
| Grid integrity did not regress | Parquet re-read: **9,777,600 rows**; `mod` range 0–1439 with **1,440 distinct**; cells per `(symbol, metric)` = **10,080** for every pair (single unique value) | **PASS** |
| CONFIRM bank still untouched | Max `last_bar` across all 194 fitted symbols = **`2023-02-28 23:59:00`** < `DESIGN_BANK_END` 2023-03-01. Manifest per-symbol statuses: 194 OK / 697 `NO_DESIGN_BANK_BARS` / 3 `ERROR` over 894 — unchanged from run 2 | **PASS** |
| **No new fence violation** | All 6 read sites re-enumerated and each bound re-read: `spread_pin.py:273` (`< TRAIN_END_UTC`), `spread_pin.py:376-379` (`< TRAIN_END_UTC` **and** day filter), `seasonal_baselines.py:96-102` (`>= ANALYSIS_START & < DESIGN_BANK_END`), `signed_bar_lane.py:81-86` (caller-bounded; `:348` passes `fence.train_end_utc`, `:294` asserts the validation day inside TRAIN), `a8:255-257` (single day, `>= lo & <= hi`; `:374` refuses a sample day `>= TRAIN_END_UTC`), `signed_bar_lane.py:174` (`catalog.query` on the freshly-written validation catalog). Post-hoc realised-max assertions raise, not warn (`seasonal_baselines.py:130`, `signed_bar_lane.py:353-354`). **None of the run-2 edits touched a read path** | **PASS** |
| Every `report.md` number reproduces from `results/` | Kill-gate (§2), TRAIN spread table (§3), flip-pair + tick table (§3), W3 correlations (§4), W4 medians (§5), grid claims (§5/§7a), breadth table (§6), shas (§5/§7a/§8), `config_hash` (§5), 26.2:1 (§2) — **all reproduce**. **Two exceptions, Issue 19** | **PARTIAL** |
| `check_no_local_accounting("python/experiments/INFR-017/code")` | re-run: `{"ok": true, "banned_defs_found": []}` | PASS |
| L-28 / L-29 / L-30 / L-31 / L-21 / T1 routing / XENA | no permutation control; `ts_event` = `CloseTime` (`:133`); no `BacktestNode`; no money-unit or tradability claim; no XENA route | N/A / PASS |
| Registry precondition | CF-SIGAUC-001 registered; 0 counted TEST reads; 0 slots | PASS |

---

### Issues (run 3)

**18 — MODERATE (carry-forward of run-2 Issue 14) — the hash-pinned decision of record still labels sample-day figures as TRAIN-band**
`python/experiments/INFR-017/code/spread_pin.py` (`build_decision`) → `results/column_pins.json.W2_decision.stored_column_reason`

The emitted string is unchanged from run 2:

> "Measured negative on the **TRAIN band** in {'BTCUSDT': 30.99, 'ETHUSDT': 40.538, 'SOLUSDT': 22.814,
> 'DOGEUSDT': 11.708, 'XRPUSDT': 7.593} percent of minutes"

Verified against the same artifact: those five values are exactly `per_symbol.*.sample.candidate_A_stored_definition.pct_negative` (the 4 sample days, n ≈ 5,760). The TRAIN figures — which design §3(b) and report §3 publish — are `per_symbol.*.stored_column_full_train.pct_negative` = **32.374 / 39.939 / 24.937 / 11.506 / 7.282**. The label says one scope, the number is the other.

What was done is real mitigation: the new top-level `band_note` and the two `scope` fields mean a careful reader of the whole file can now work out that these must be sample figures. But run 2's required change was specific — *"either quote `stored_column_full_train.pct_negative` and keep the 'TRAIN band' wording, or keep the sample figures and label them 'on the 20-symbol-day audit sample'"* — and neither was applied to the sentence itself. A consumer who quotes `W2_decision` (the block explicitly framed as the frozen decision of record, and the block INFR-018 reads for the UNUSABLE call) still gets a number under the wrong band label, and the disagreement with the design and the report persists at 1–2 points per symbol.

Two related over-claims followed from treating this as done:
- `report.md:159` (§7d): "The pin distinguishes its two scopes explicitly." True of the `per_symbol` blocks; not true of `W2_decision`.
- `report.md:168` (§7e item 4): "Scope labels added to both blocks." Accurate as far as it goes, but presented under a heading asserting the item is corrected.

Not a fence issue (the four sample days are inside TRAIN), and it does not change the decision — every figure is unambiguously non-trivial, so UNUSABLE stands either way. It is a labelling defect inside a frozen artifact, second run running.

Required change: fix the string (quote `stored_column_full_train.pct_negative` with the "TRAIN band" wording is the cleaner option, since it then matches design §3(b) and report §3 verbatim), re-hash the pin, re-stamp `signed_lane_manifest.json.roundtrip.w2_pin_sha256`, and update the `config_hash` reference at `report.md:98`. The cascade is proven — it is exactly what this round already executed when the hash moved `f210a05b…` → `e495d349…`. Also correct the two report sentences above.

Related, unchanged from run 2: `spread_pin.py:268` `analyse_stored_column`'s docstring still reads *"Full-history distribution of the stored SpreadBps column"* while the body filters `< TRAIN_END_UTC` (`:275`). Stale prose on the exact function whose unbounded read caused run-1 Issue 2 — the one docstring in this item that should not say "full history".

**19 — MINOR — two report numbers do not reproduce from `results/`**
`python/experiments/INFR-017/report.md:145`, `:98`

(a) `:145` (§7b, "Fence state after the fix"): *"the CONFIRM bank is untouched (max fitted bar `2023-02-28 23:57:00`)"*. The artifact says **`2023-02-28 23:59:00`** (max `last_bar` over all 194 fitted symbols in `seasonal_baselines_manifest.json`). `23:57` is the run-1 figure, from before the grid fix; run 2 recorded the move to `23:59` and explained it (the key no longer wraps, so the last two minutes of the bank are now reachable). The conclusion is unaffected — both are inside the bank — but the report publishes a superseded number as the current fence evidence. Related: `:145` says "all six code read paths" while `:163` says "all five read paths"; both are defensible countings (6 sites total vs 5 staging scans + 1 catalog query), but the report should not state two different numbers for the same check.

(b) `:98` (§5 W5): *"0 mismatches across all nine mapped columns"*. The check now covers **ten** comparisons — the nine `pairs` entries plus `SpreadBps->spread_feature(+status)` added this round — so the report undersells its own strengthened test. Same root cause as the manifest field below.

**20 — MINOR (carry-forward of run-2 Issue 15, second paragraph) — `signed_fields_checked` still understates the round-trip**
`signed_bar_lane.py:326` → `signed_lane_manifest.json.roundtrip.signed_fields_checked`

Emits `['volume', 'buy_volume', 'sell_volume', 'delta', 'n_trades', 'ts_event']` — derived from the `SIGNED_FIELDS` constant rather than from the `pairs` dict that the check actually iterates. OHLC are compared and not listed; `spread_feature` / `spread_status` are now compared and not listed either, so adding the spread leg widened the gap between what the manifest claims was checked and what was checked. Run 2's required change (derive the list from `pairs`) was not applied. Understating a check is the safe direction of error, but the manifest is the record a later reader uses to decide whether a field was validated.

---

### What is sound (run 3)

Recorded so a fourth run does not re-litigate it. The report's hash handoff is correct and defensive — §8 names the live sha and explicitly names the discarded one, so INFR-018 cannot be misdirected. The holdout-derived null counts are corrected in both registry files with the TRAIN band named, and the scoped grep confirms every surviving mention of an old value is explicitly framed as a correction or a disclosure. The breadth numbers are now computed, emitted, cited, and reproduce exactly (894 / 296 / 197) from the admission ledger on the correct basis. All three minor notes are fixed properly rather than nominally: the null-aware comparison is genuinely null-correct and applied to every column, and the spread leg is status-coupled rather than a bare value check. `pin_sha256` recomputes exactly, is stable across reruns by construction, and the lane manifest stamps the same value — no record carries a pin that does not exist. The baselines parquet sha is unchanged and the 10,080-cell grid is intact. All six read paths remain bounded with raising assertions, the CONFIRM bank is untouched, and no run-2 edit went near a read path.

The residue is one mislabelled string inside the pin — mitigated by a new band note, but not corrected where it was flagged — and three number-hygiene items in the report and the lane manifest. No re-run of the measurement is required; the pin edit requires a re-hash and a manifest re-stamp, which this round already demonstrated.

---

## QA run 4 — 2026-07-20T17:56Z — mode: subagent — HEAD af7bf9e1f2f8aea4756a7eb73ff7828c6b997a09

Reviewed git state: HEAD `af7bf9e` + working-tree additions (untracked `python/experiments/INFR-017/`,
`python/src/xen/sigbar/`, `python/tests/test_sigbar_baselines.py`,
`docs/experiments-docs/checkpoints/2026-07-20-014-signed-auction-structure/`,
`docs/signal-registry/candidate-families/cf-sigauc-001.md`; modified `docs/experiments-docs/INDEX.md`,
`docs/signal-registry/multiplicity-registry.md`) — unchanged from run 3.

Scope: narrow final check on run-3 Issue 18 (the one blocking item), Issues 19a/19b/20 (number
hygiene), plus the declared regression battery. Items confirmed sound in runs 1–3 were **not**
re-litigated.

**Verdict: APPROVE.** The blocking item is genuinely fixed at the point it was flagged, all three
hygiene items are fixed, and the full regression battery passes with no new defect.

---

### 1. Run-3 item disposition (verified from the artifacts and the source, not accepted on claim)

| # | Run-3 item | Verification performed | Verdict |
|---|---|---|---|
| **18** | `W2_decision.stored_column_reason` quoted the 4-sample-day rates under a "TRAIN band" label | **Source:** `spread_pin.py:455-458` — `train_neg` is now built as `b["stored_column_full_train"]["pct_negative"]` per symbol, i.e. derived from the full-TRAIN block, not from `build_pin()` (which supplies the sample figures and is now routed only to `evidence_scopes.sample_days_pct_negative` at `:459,473`). **Artifact:** the emitted string reads *"Measured negative on the **FULL TRAIN band** in {'BTCUSDT': 32.374, 'ETHUSDT': 39.939, 'SOLUSDT': 24.937, 'DOGEUSDT': 11.506, 'XRPUSDT': 7.282} percent of minutes"*. Regex-extracted the five numerals from the string and compared elementwise against `per_symbol.*.stored_column_full_train.pct_negative` → **exact equality, all five**. Cross-checked against the two published tables: design.md §3(b) (32.4 / 39.9 / 24.9 / 11.5 / 7.3) and report.md §3 (same) — **agree at the published precision**. `evidence_scopes` present with three keys: `full_train_band_pct_negative` (= the `stored_column_full_train` block, verified equal), `sample_days_pct_negative` (= `sample.candidate_A_stored_definition.pct_negative`, verified equal), and a `note` stating the decision rests on the FULL TRAIN figures. Both scopes are now carried in the frozen block itself, so a consumer reading only `W2_decision` gets the right number under the right label and can see the other scope without leaving the block | **FIXED** |
| **19a** | report.md:145 published the superseded fence figure 23:57 | `report.md:145` now reads *"max fitted bar `2023-02-28 23:59:00`"*. Recomputed independently: max `last_bar` over all 194 `OK` rows in `seasonal_baselines_manifest.json` = **`2023-02-28 23:59:00`** < `DESIGN_BANK_END` 2023-03-01 | **FIXED** |
| **19b** | report.md:98 said "nine mapped columns"; the check covers ten | `report.md:98` now reads *"0 mismatches across all ten compared fields"* and enumerates them. Recounted from the artifact: `signed_lane_manifest.json.roundtrip.per_symbol.*.field_mismatches` has **10 keys** on every symbol (9 `pairs` entries + `SpreadBps->spread_feature(+status)`), all `0` | **FIXED** |
| **20** | `signed_fields_checked` understated the round-trip | `signed_lane_manifest.json.roundtrip.signed_fields_checked` now emits **11 entries** — `open, high, low, close, volume, buy_volume, sell_volume, delta, n_trades, spread_feature+spread_status` + `ts_event (join key)`. Compared elementwise against the `pairs` dict at `signed_bar_lane.py:226-236` plus the spread leg: **the manifest list now matches exactly what the check iterates**. OHLC and the spread leg are no longer omitted | **FIXED** (see note N2) |

---

### 2. Regression battery (all declared checks run)

| Check | Evidence | Result |
|---|---|---|
| `pin_sha256` moved to `e3b9fd9b…` | `column_pins.json.pin_sha256` = `e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225` | confirmed |
| `pin_sha256` **recomputes** from the artifact | `sha256(json.dumps({k:v for k,v in payload if k not in ('generated_utc','pin_sha256')}, sort_keys=True, default=str))` over the emitted file → **exact match** to the recorded value | **PASS** |
| `pin_sha256` **stable across a rerun** | `spread_pin.py:582-585` excludes `generated_utc` and sorts keys. Payload construction re-read in full (`:541-578`): the remaining entries are frozen constants (`item`, `work_items`, `band_note`, `frozen_parameters`, `W2_stored_definition_pin`), measured blocks (`per_symbol`, `summary`), or pure functions of those (`W2_decision`, `W3_dependence_verdict`, `W4_ntrades_verdict`). **No time-varying, path-varying or iteration-order-varying field survives into the hashed payload.** Hash is a pure function of the measured inputs. *(A live rerun was not executed: it requires re-downloading raw Bybit archives and would overwrite a frozen artifact — outside QA's read-only mandate. Same basis as run 3.)* | **PASS (by construction + recompute)** |
| Lane manifest tracks the new pin — no stale hash | `signed_lane_manifest.json.roundtrip.w2_pin_sha256` = `e3b9fd9b9b5851b8…` — **byte-identical to `column_pins.json.pin_sha256`**. Record path re-traced: `run_validation:296` and `run_ingest:343` both call `load_w2_pin(root)` (`:104-119`, returns `pin["pin_sha256"]`), pass it as `pin_sha` into `to_signed_bars(...)` (`:317`, `:361`), which stamps `config_hash=config_hash` at `:156`. **No code path can stamp a hash other than the one currently in the pin.** `report.md:98` cites `config_hash = e3b9fd9b…` — consistent | **PASS** |
| `seasonal_baselines.parquet` sha unchanged | Recomputed from bytes: `1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72` = `seasonal_baselines_manifest.json.artifact_sha256` = the run-2/run-3 value. The run-3 edits touch `spread_pin.build_decision`, one `signed_bar_lane` constant, and report prose — none of them the W6 fit | **PASS (deterministic across three runs)** |
| No new fence violation | All six read sites re-enumerated and each bound re-read: `spread_pin.py:273-275` (`< TRAIN_END_UTC`), `spread_pin.py:376-378` (`< TRAIN_END_UTC` **and** day filter), `seasonal_baselines.py:96-102` (`>= ANALYSIS_START & < DESIGN_BANK_END`), `signed_bar_lane.py:82-97` (`[start, end)`, caller-bounded — `:361` passes `fence.train_end_utc`, `:300` refuses a validation day whose end `>= fence.train_end_utc`), `a8_provenance_audit.py:255` + `:374` (refuses a sample day `>= TRAIN_END_UTC`), `signed_bar_lane.py:180` (`catalog.query` on the freshly-written validation catalog). Post-hoc realised-max assertions still **raise**, not warn (`seasonal_baselines.py:130`, `signed_bar_lane.py:353-354`). **None of the run-3 edits touched a read path** — `build_decision` performs no I/O, and `SIGNED_FIELDS` is a manifest label constant | **PASS** |
| CONFIRM bank untouched | Max `last_bar` across all 194 fitted symbols = `2023-02-28 23:59:00` < 2023-03-01. Manifest statuses over 894 attempted: **194 OK / 697 `NO_DESIGN_BANK_BARS` / 3 `ERROR`** — unchanged from run 3 | **PASS** |
| Every number in `report.md` reproduces from `results/` | Re-swept, with attention to anything the run-3 edits could have moved. §2 kill-gate: `a8_provenance_audit.json.verdict` = `PASS`, 20/20, `aggressor_side_convention.unanimous` = true, median odds **26.23** → report's "26.2:1" ✓. §3 TRAIN table (n / %neg / median / nulls, all five symbols) ✓ against `stored_column_full_train`. §3 flip-pair + tick table (0.244/0.305/0.727/1.470/1.929 and 0.043/0.058/0.376/1.477/1.965) ✓ against `sample.candidate_C_flip_pair.median` and `one_tick_bps`. §4 W3 correlations + CIs ✓. §5 W4 medians ✓. §5 W5 "1,440 bars × 3 symbols", "0 mismatches", "ten compared fields", `config_hash e3b9fd9b…` ✓. §5 W6 "194 instruments", "10,080-cell grid", sha `1b7244c8…` ✓. §6 breadth 894/296/197/194 ✓ against `admission_reconciliation.json.band_coverage`. §7b fence figure `23:59` ✓ (was the run-3 exception). §8 sha handoff ✓. **Both run-3 exceptions closed; no new exception found** | **PASS** |
| Regression tests | `python/tests/test_sigbar_baselines.py` — **5 passed** (project `.venv`) | PASS |
| `check_no_local_accounting("python/experiments/INFR-017/code")` | re-run: `{"ok": true, "banned_defs_found": []}` | PASS |
| L-21 / L-28 / L-30 / L-31 / T1 routing / XENA | unchanged: no money-unit or tradability claim, no permutation control, no `BacktestNode`, no XENA route | N/A / PASS |
| Registry precondition | CF-SIGAUC-001 registered; 0 counted TEST reads; 0 slots consumed | PASS |

---

### 3. Deferred to the operator — disclosed, verified present, NOT QA blockers

Both are recorded here so approval cannot be read as either clearing them or losing them.

**(a) The disclosed holdout touch (design.md §3(b)).** Present and standing at `design.md:60-73` as a
blockquote headed *"CORRECTION + DISCLOSURE (2026-07-20, QA run 1 Issue 2) — awaiting operator
adjudication"*, stating what was read (univariate distribution of one data-quality column), why it
happened, that the effect on conclusions is non-directional, that it spends no sanctioned shot, and
explicitly *"Recorded, not self-cleared — per QA this is the operator's call to clear, not the
author's."* Mirrored at `report.md:132-143` (§7b) ending **"Status: NOT self-cleared."** The
superseded figures survive only inside text that frames them as superseded. **Properly disclosed, not
silently dropped. Adjudication is the operator's, and QA does not withhold approval on it.**

**(b) Baseline coverage / universe breadth.** Present as a computed, emitted finding — not prose:
`admission_reconciliation.json.band_coverage` carries `n_admitted` 894, `n_with_bars_before_train_end`
296, `n_with_bars_before_design_bank_end` 197, plus a `note` and a `survivorship_caveat`.
`seasonal_baselines_manifest.json` carries 194 `OK` / 697 `NO_DESIGN_BANK_BARS` / 3 `ERROR`.
`report.md` §6 tables all four counts, cites the artifact by path and key, names the 3 corrupt
parquets (§7d), and raises a **recommended checkpoint amendment (NEUTRAL direction)** re-stating the
SPDR-008 universe as "all admitted instruments with readable TRAIN data — measured 296". §8 lists the
breadth ceiling under "May NOT rely on". **Properly disclosed. The design decision about coverage is
the operator's; QA does not withhold approval on it.**

---

### 4. Non-blocking notes (cosmetic; recorded, not required before execution)

**N1 — stale docstring, third run running.** `spread_pin.py:267` —
`analyse_stored_column`'s docstring still reads *"Full-history distribution of the stored SpreadBps
column for one symbol"* while the body filters `< TRAIN_END_UTC` at `:275` and stamps
`scope = "FULL TRAIN band"` at `:281`. The code is correct and the emitted artifact is correctly
scoped; only the prose is stale — on the one function whose formerly-unbounded read caused run-1
Issue 2. Zero numeric or behavioural effect. Worth a one-line edit whenever this file is next touched.

**N2 — `signed_fields_checked` is correct but hand-maintained.** `signed_bar_lane.py:60-64,332`
emits `list(SIGNED_FIELDS) + ["ts_event (join key)"]`. The constant now enumerates exactly the ten
compared fields, so the manifest is accurate **today**. Run 3's suggested form (derive the list from
the `pairs` dict at `:226-236`) was not applied, so adding an eleventh comparison without editing the
constant would re-open the same gap. Latent maintenance risk, not a present defect.

**N3 — two read-path counts in the report.** `report.md:145` says "all six code read paths";
`report.md:163` says "all five read paths". Both are defensible (6 sites total; run 2 counted 5
staging scans separately from the catalog query), and `:163` is a historical record of what run 2
did. Confusing on a skim only.

---

### 5. What INFR-018 may treat as frozen

**Frozen — may be relied on, by exact path and hash:**

| Artifact | Hash / identity | What it licenses |
|---|---|---|
| `python/experiments/INFR-017/results/seasonal_baselines.parquet` | sha256 **`1b7244c87aaafe293a945a8ac03a31222c95dcc232e7fb1d835d5227fa41ed72`** (verified from bytes; stable across three runs) | The A5 minute-of-day × day-of-week baselines. Every "high volume" / "large \|Δ\|" / "wide range" threshold is a residual against these, never a raw number. 194 instruments × 5 metrics × 10,080 cells (grid verified: `mod` 0–1439, 1,440 distinct, 10,080 cells for every (symbol, metric)) |
| `python/experiments/INFR-017/results/seasonal_baselines_manifest.json` | `artifact_sha256` matches the parquet above | Per-instrument fit status and coverage. Max fitted bar `2023-02-28 23:59:00` — DESIGN bank only |
| `python/experiments/INFR-017/results/column_pins.json` | `pin_sha256` **`e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225`** (recomputes exactly; excludes `generated_utc`) | The W2/W3/W4 decisions of record: stored `SpreadBps` = **UNUSABLE** as a cost input; flip-pair replacement `VALIDATED_ON_SAMPLE_ONLY`; W3 dependence not binding (all \|corr\| ≤ 0.048 < 0.20); `NTrades` usable as a z-scored participation multiplier only. **Read the status from this file — do not hard-code it** |
| `python/experiments/INFR-017/results/signed_lane_manifest.json` | `roundtrip.w2_pin_sha256` = `e3b9fd9b…` (identical to the pin); `fence.manifest_sha256` `35d3375e…` | The `SignedBar` contract and `data/catalog_sigbar/` as the engine-readable causal path. Round-trip exact vs staging: 1,440 bars × 3 symbols, 10/10 fields, 0 mismatches, 0 split-invariant violations |
| `python/experiments/INFR-017/results/a8_provenance_audit.json` | `verdict: PASS`, 20/20 symbol-days, worst relative deviation 0.0, `NTrades` exact | **HYP-I1 PASS.** `Δ = BuyVolume − SellVolume` is exact per-bar taker aggression, and `side` is the **aggressor** side (`aggressor_side_convention`: unanimous on all 20 symbol-days, median odds 26.23:1) — Δ's sign is verified, not assumed |
| `python/experiments/INFR-017/results/admission_reconciliation.json` | `band_coverage`: 894 / 296 / 197 (reproduced independently from `INFR-011/artifacts/admission-ledger.jsonl` in run 3) | The lane inherits ADMITTED status; 904 staged / 894 admitted / 10 staged-not-admitted each with a reason |

**NOT frozen — must not be relied on:**

- **`SpreadBps` as a spread or any cost input.** Pinned UNUSABLE. `xen.evaluation.t1_round_trip_spread_bps` passes its argument through unfloored, so feeding it this column yields a negative cost.
- **Any flip-pair spread figure outside the 20 audited symbol-days** without recomputing it from raw trades. And where it is used, it is a **conservative upper bound on the effective spread**, not the quoted spread — label it as such.
- **Universe breadth beyond 296** TRAIN-readable instruments (197 with DESIGN-bank coverage, 194 actually fitted). "Full ADMITTED cross-section" (894) is not available on this band.
- **The CONFIRM bank, TEST, and the holdout** — untouched by this item and staying untouched until each INFR-018 kill-gate confirms there.
- **The discarded baseline artifact `78dd7988…`** — invalid (aliased grid), not re-pinned. A consumer loading that hash is loading a broken file.
- **Any INFR-017 output as evidence that a signal works.** Stage I by construction: these are instruments and parameters, not claims.

**Standing operator items carried into INFR-018 (not QA gates):** the §3(b) holdout-touch adjudication
(a); the SPDR-008 universe restatement / coverage decision (b); and the blast-radius question of
whether any prior chapter-04 cost read consumed the broken spread column — raised in both design §3
and report §3, explicitly out of INFR-017's scope and not investigated here.

---

### Closing

Four runs, two blocking defects (the aliased seasonal grid, the self-comparing round-trip) and one
holdout touch found and fixed, plus a bookkeeping tail that took three rounds to clear. The pin now
says what it measures, the hashes chain without a stale link, and the report's numbers all come out
of `results/`. Ready for the operator's execution gate.
