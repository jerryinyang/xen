# SPDR-018B — `analysis.md` (fresh-context data analyst, BINDING read)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5` — the checkpoint-017 residue on a **second universe**
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Universe:** cTrader — `EURUSD`, `XAUUSD`, `USTEC` (INFR-021 fence)
- **Lane:** SPDR stage 5 · TRAIN-only · 0 counted TEST reads · no family action · no XENA
- **Design:** `design.md` (frozen, operator-approved 2026-07-25, no amendments) — binding
- **Screen summary:** `screen.md` — subordinate, **and stale in its headline numbers**. Every figure in it is treated below as a claim to verify; the stale ones are flagged individually in §2.
- **Analyst code:** `analysis_code/b01…b08` — every number below re-derived by me from `results/*.parquet` and `results/*.json`. **`screen_code/` was never read, imported, listed or opened.**
- **Analyst artifacts:** `results/analyst_per_cell_magnitudes.parquet` (6,156 signed cells: full `(p,W,L,W/L,p_be,p_be_net,edge)` + CIs + `log R` + payoff scale — L-03, nothing hidden behind a pooled count) and `results/analyst_stratum_tables.csv` (11 stratum views).
- **Supersedes:** the previous `analysis.md` of 2026-07-25. That document's *reasoning* largely stands; its *numbers* were computed against a wrong cost deflator and a non-portable precision target and are replaced here.

```
SPREAD-COST-DISCLOSURE + DOUBLY-SYNTHETIC-COST DISCLOSURE
  (repeated because EVERY net figure in this document inherits both)
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps:      null
  cost_scope:         PARTIAL_FEES_FUNDING_ONLY — BORROWED from Bybit AND RESCALED
  what the cost is:   Bybit taker fee 11.0 bps rt + discrete funding stamps + 2.0 bps allowance,
                      multiplied by a per-arm payoff-scale deflator (arm B 0.2611, arm C 0.3118).
                      Perp funding does not exist on EURUSD/XAUUSD/USTEC and the fee schedule is a
                      different broker's.
  therefore:          this is NOT any instrument's real cost, NOT a cTrader cost measurement, and
                      NOT a tradability input. It supports exactly one claim — cross-universe
                      comparability on one common yardstick.
  and:                spread is not charged at all, so every net figure OVERSTATES performance.
  blocking:           the per-symbol spread pin remains a blocking prerequisite for any money read.
  prohibited_claims:  fully-net, cost-complete, tradable, deployable, "this is the cTrader cost"
  GROSS IS PRIMARY EVERYWHERE BELOW.
```

> **Scope.** This document quantifies and recommends. It takes **no disposition** — the verdict is the operator's at the mid-checkpoint reflection. Nothing here is a family action, a graduation, a tradability claim or a XENA authorisation.
>
> **B-5 applied symmetrically throughout.** `UNPOWERED` / `NOT_RESOLVABLE` are statements about sample size and are **never** reported as evidence against anything. An unpowered non-replication says nothing. Only **powered** cTrader cells are informative about the crypto result.
>
> **AMENDMENT-C1 / S1.** cTrader is **replication and credibility only**. It is never pooled into crypto `n` and is never cited as power for the crypto estimate.
>
> **Power counts here are NOT comparable to SPDR-018's.** The two runs use different precision bases (see §2.2). Wherever the two appear side by side, that incomparability is restated.
>
> No read anywhere is phrased against `p > 0.5`. The reference is always each cell's own `p_be` / `p_be_net`.

---

## 0. Executive summary for the operator (plain language, ~20 seconds)

**The core crypto result reproduces on a second asset class, and it reproduces more tightly than before. Nothing here is profitable, and after two corrections nothing comes close.**

1. **The trade sits exactly on the zero line.** Across the 315 cells measured precisely enough to trust, the win rate is **0.4868** against the rate those same cells need just to cover their own payoff geometry, **0.4855** — a gap of **0.0013**. Average gross result: **−0.08 bps per trade**. That is indistinguishable from zero on a different asset class, a different broker, its own date fence and its own band split.
2. **Nothing clears cost. Zero of 315.** The earlier "12.9% clear cost" figure was the product of two compounding errors (a cost charge ~2× too light and a precision bar 5.6× too loose). Corrected, it is **0.0%** — which is exactly what crypto showed. The best single cell earns **+1.39 bps gross against a 2.43 bps charge**: it misses by 1.04 bps, and the real charge is higher still because spread is not charged.
3. **The "payoff-shape" lever is confirmed to be the arithmetic mirror of the win rate, not a free handle.** On the corrected 315 cells the mirror explains **97.5%** of the variation in payoff asymmetry (crypto: 96.7%). Exit geometry moves payoff asymmetry by **36×** and the win rate moves inversely by almost exactly the offsetting amount; the average result does not improve. The screen's earlier "the mirror fails here (R² 0.31)" was an artifact of the loose precision bar — **corrected, the mirror replicates.**
4. **The one crypto survivor — shock-conditioned momentum — does not reproduce here, but I rule that this evidence is WEAK and must not be used to close the thread.** Two reasons. First, the comparator this test measures against is not a neutral yardstick: its own average swings from **+1 bps in the European session to +12 bps in Asia**, and in Asia a genuinely zero-effect arm would read the same "significant" as the observed one. Second, when I rebuilt the comparator myself from the emitted rows, one of its two legs **flipped sign** (§7.3). The honest statement is that the crypto thread is **not replicated and not refuted**.
5. **Two integrity items and one new one.** The controls and tripwires that were silently missing are now present and I verify **11 HARD checks / 0 failed / 12 entries**. But **seven design-declared HARD checks that SPDR-018 ran do not exist in this run at all** (§1.1) — including determinism and the golden traces — and `run_summary.json` still says `deviations: []`. Separately, I found that **the cost deflator is derived from the very subset the precision correction invalidated** (§2.3). None of these flips a conclusion; all three should be recorded rather than left implicit.
6. **What I could not resolve stays open, and is not a null.** `C9` (straddle characterisation) and `D3`/`D4` (ordinal swing targets) were never run on this universe. They are **OPEN / NOT RUN**. They are not absent, not negative, and not evidence of anything.

---

## 1. Phase 0 — Integrity audit (blocking; artifact-backed, with COUNTS)

The SPDR lane exempts screens from `estimand_validation.json`; the integrity substitute is the code-asserted fence + causal-lag self-check (`docs/references/spdr-lane.md`). I audit that substitute against the HARD list SPDR-018B inherits verbatim from SPDR-018 §12 (design §6 states the inheritance explicitly).

**I do not accept "HARD checks held" as a count-free statement.** Four failures in this build shared one cause — a declared check living in transient state or in an artifact a later stage regenerates, so it silently did not run while the run reported success. The count is therefore asserted, and the *absences* are enumerated.

### 1.1 Declared HARD vs what actually ran — the count

`results/integrity_selfcheck.json` carries **12 entries: 11 HARD, 1 INFORMATIVE, `failed_checks: []`, `hard_all_held: true`.** I counted the array element by element. `results/controls.json` carries **both** `tripwires` (3 entries) and `arm_C_ambient_base`. Both requirements the orchestrator flagged are satisfied.

| Inherited HARD item (SPDR-018 §12) | Present in 018B self-check | Severity emitted | Held | Analyst note |
|---|---|---|---|---|
| cTrader TRAIN fence (`max ts < 2023-11-22Z`) | yes | HARD | ✅ | max exit_ts in `panel_C` = **2023-11-21T20:00Z**; **0 rows** at/after `train_end` |
| cTrader holdout (≥ 2024-12-13 never queried) | yes | HARD | ✅ | **0 rows** at/after 2024-12-13 in the emitted panel — verified by me, not from the catalog |
| cTrader fence sha256 | yes | HARD | ✅ | measured == `4cdc7b01dd47…6de0` |
| Identity reconstruction < 0.01 bps | yes | HARD | ✅ | **independently re-derived, §2.1** (max 8.53e-14) |
| M-1 block-MDE drives every band label | yes | HARD | ✅ | `mde_source_for_bands` = `block`; iid columns carry the `__COMPANION_ONLY` suffix |
| No `pass` field / no `at_or_above_pXX` | yes | HARD | ✅ | `offending_columns: []`; I confirm no such column in any of the 6 parquets |
| Derangement fixed points == 0 | yes | HARD | ✅ | 0 for both side-derangements and for TRIPWIRE-3, 2,000 seeds each |
| **CROSS-UNIVERSE OBJECT IDENTITY** (design §5, substitutes for parent parity) | yes | HARD | ✅ | 70 BTCUSDT cells, max abs gross diff **1.14e-13**, max n diff **0.0** |
| TRIPWIRE-1 construction assertions | yes | HARD | ✅ | `min(entry − decision) = 1`; exit at declared offset h=12; 2,602 rows. I independently reproduce `entry_idx − event_idx = 1` for **100%** of 233,569 panel rows |
| TRIPWIRE-2 leaky-variant discrimination | yes | HARD | ✅ | legal **0.494 bps** vs leaky twin **203.65 bps** — ratio **412×**, on 106 matched rows. Genuinely orders of magnitude (SPDR-018's own TRIPWIRE-2 managed only 7.55×) |
| AMBIENT-BASE control present | yes | HARD | ✅ | *artifact-presence check, not an item on the inherited HARD list — see below* |
| TRIPWIRE-3 forward-path derangement | yes | **INFORMATIVE** | report layer | live −4.654 vs null mean +0.338 (sd 1.544), pct 0.000, collapse 1.073 — correctly **not** the causality claim |

**The seven declared-HARD checks that are ABSENT from this run.** SPDR-018's post-fix emission carries **18 HARD** checks. 018B carries 11, and one of those 11 (`AMBIENT-BASE control present`) is a presence assertion added by the post-hoc fix rather than an item on the inherited HARD list. So **10 inherited HARD items ran; 7 did not exist in any form**:

| Missing | What it guarded in SPDR-018 | Consequence here |
|---|---|---|
| **Determinism** (`--jobs` parallel == sequential) | SPDR-018's own defect: silently downgraded, then fixed to run unconditionally so a resumed run cannot skip it | **Not run.** This run *was* resumed (arm C's controls were skipped once by exactly that path). The one check designed to catch a resume-path defect is the one absent. Cheap to run. |
| **Golden traces G1–G6** | independent self-check-side recomputation from the fenced catalog with no arm module imported | Not run. The cross-universe identity guard is a strong partial substitute (it *is* an independent recomputation) but it certifies the object, not the trace values. |
| **Universe pin set-equality** | 25 pinned == 25 recomputed, no extras/missing | Not run as a check. I verify by hand: `unit_pin.json` measures **3 of 3** requested symbols, `symbols_without_a_value: []`, and all four arm parquets carry exactly `{EURUSD, USTEC, XAUUSD}` (+ pooled rows). Effectively satisfied, formally unchecked. |
| **Bootstrap speed path == `xen.evaluation.block_bootstrap_ci`** | proof the fast path is bitwise the library | Not run. Every CI in this document comes from that path; I cannot attest it. |
| **No local accounting primitive** | L-18 / critical-017 — the defect that cross-certified three wrong verdicts | Not run as a check. Circumstantial evidence is good: `panel_C` carries `cost_model = BORROWED_CRYPTO_PAYOFF_SCALED` and I verify `c_net = c_gross − cost_vol_scaled` and `c_net_unscaled = c_gross − cost_raw` to **max abs diff 0.0**, i.e. the overlay is a subtraction, not a re-implementation. |
| **Spread never charged** | the disclosure's own attestation | Not run as a check; consistent with `spread_rt_bps: null` and with `cost_raw_bps` decomposing into fee+funding+allowance only. |
| **Global (Bybit) holdout ≥ 2025-01-08** | the §5 guard reads *Bybit* bars for BTCUSDT | Not run as a check on the guard's own reads. I verify 0 rows ≥ 2025-01-08 in the emitted cTrader panel, but the guard's Bybit-side reads are not covered by any emitted artifact. **The single genuine residual exposure in Phase 0.** |

**Ruling I ask the operator for.** None of the seven is load-bearing for the direction of this run's conclusion (the result is negative-to-null; look-ahead inflates edges, and there is no inflated edge to explain away — the same mitigation SPDR-018 §1.2 accepted, and here TRIPWIRE-2 actually *did* run and separates by 412×). But three are cheap and two matter procedurally:

- **(a)** accept the emission with the seven recorded as un-run inherited HARD checks, and correct `run_summary.json` (`deviations: []` is still inaccurate — `integrity_selfcheck.json`'s own `late_addition_note` contradicts it in the same directory); or
- **(b)** require **determinism** + the **Bybit-holdout assertion on the §5 guard** before the reflection consumes these numbers.

**I recommend (a) plus running determinism.** It is one sequential pass, and this run is precisely the resumed-run case the SPDR-018 fix was built for.

### 1.2 Provenance / causal-lag trace (verdict-bearing columns)

Traced on the only arm with an emitted row-level panel (`panel_C.parquet`, 233,569 rows, arm C — the arm carrying 5,526 of 7,578 cells):

| Column | Decision-time derivation | Verdict |
|---|---|---|
| `shock_flag`, `mag_high`, `vol_tercile`, `last_k_state_*`, `slow_regime` | conditioner state at `t_idx`, `anchor_idx = t_idx + 1` | causal by construction; TRIPWIRE-1 asserts the offset |
| `side`, `policy` | assigned at `event_idx` | `entry_idx − event_idx = 1` for **100%** of rows — entry is strictly the bar after the decision bar |
| `r_h`, `gross_bps` | `entry_idx → exit_idx`, `exit_idx − entry_idx == h` exactly for every h | no intrabar look-ahead available in an OHLCV open-to-open construction |
| `c_net_bps`, `c_net_unscaled_bps` | subtraction of an analyst-side overlay | max abs diff 0.0 against `c_gross − cost`; no local accounting |
| unit pin σ̂ | H1 Parkinson EWMA λ=0.94, 60-bar warm-up, **causal ≤ t−1**, horizon-scaled √h | object stated verbatim; L-21 compliant; **measured at run**, 3/3 symbols, pooled median **13.0342 bps** |

**One provenance label defect, no numeric consequence.** `entry_ts == event_ts` in **100%** of panel rows while `entry_idx = event_idx + 1`. The *index* is causal (and it is the index that drives the return), but the *timestamp* column is stamped one bar early. This is cosmetically the fill-ts off-by-one shape that has bitten this programme before; here it cannot leak, because no computation joins on `entry_ts`. It should still be fixed, and no downstream work should join on `entry_ts`.

**One label inconsistency in `unit_pin.json`.** Its `band` field reads `TRAIN [2021-06-29T06:53Z, 2023-12-18T00:00Z)` — those are **Bybit's** TRAIN dates, not cTrader's `2021-06-02 → 2023-11-22` (which `integrity_selfcheck.json` records correctly). Per-symbol `n` (14,571–15,363 H1 bars) is consistent with a ~902-day 24/5 span, so I read this as a carried-over label string rather than a mis-scoped measurement — but it is asserted, not proven, and it is the kind of stale-constant carry-over the retarget was supposed to eliminate.

### 1.3 The cross-universe identity guard did real work — record it

Design §5 substitutes this for parent parity, which cannot exist on a universe with no published parent cells. It runs the retargeted code path over a **Bybit** symbol and requires SPDR-018's emitted cells to be reproduced exactly. Final state: **70 cells compared, 0 differ in count, max abs gross difference 1.14e-13.**

`screen.md` §5 records that it **failed twice on genuine defects in this experiment's own code** before passing (a ZigZag start index, and — more seriously — a band-construction difference producing a different episode set, max gross difference 14,217 bps). I cannot verify those failure values from the emitted artifacts (only the final passing state is emitted), so I report them as the screen's claim. What I *can* verify is that the guard now holds to 1e-13, and the structural point stands on its own: **without this guard, 018B would have reported an arm-B "non-replication" that was an artifact of its own code, on a 3-symbol universe where a null is the expected outcome and therefore easy to accept.** That is the highest-value single thing this build's integrity layer produced.

### 1.4 Not applicable / not gaps

- **Price-primary does not apply.** SPDR is a vectorised-Python lane by operator-signed rule and makes no tradability claim.
- **`estimand_validation.json`** is exempt in this lane (spdr-lane §Artifacts).
- **`plots/`** exists; the design budgets ≤8 plots. Not a finding either way.

---

## 2. Verification of every headline number in `screen.md` — including the stale ones

`screen.md` is subordinate to this document. It was itself corrected once (its §9 records seven analyst corrections) but its **§3 and §4 tables were never recomputed** after the cost/precision fixes. Each stale figure is flagged and replaced.

### 2.1 The identity `p·W − (1−p)·L = mean` — CONFIRMED

| Basis | Signed cells | max residual (bps) | p99 | cells > 0.01 bps tol |
|---|---|---|---|---|
| gross, vs `gross_mean_signed_rows` | 5,888 | **8.53e-14** | 2e-16 | **0** |
| gross, vs `gross_mean` (all rows incl. flat) | 5,888 | 6.31 | 0.042 | — |

The identity holds against the mean over **non-flat** rows, as in SPDR-018 §2.1. Flat-row leakage is smaller here than on crypto: median `p_flat` **0.0000**, p95 **0.0036**, max 0.3333. Also re-derived from scratch: `p == n_pos/(n_pos+n_neg)` to max diff **0.0**; `p_be = L/(W+L)` to **0.0**; `p_be_net = (L+cost)/(W+L)` to **0.0**; `edge = p − p_be_net` to **0.0**. The emitted `gross_identity_residual_bps` matches my recomputation exactly.

**The column-name trap holds here too** (SPDR-018 §2.2). `gross_*` carries the correct SoT §2 object with the cost in `gross_p_be_net`; `net_*` is the decomposition of the already-net series, where `net_cost_bps = 0` and `net_p_be_net == net_p_be` by construction. Every figure in this document uses the `gross_*` family.

### 2.2 Powered-cell counts — the precision correction verified, and one residual discrepancy

| Claim | Source | My re-derivation | Verdict |
|---|---|---|---|
| absolute precision target 10 bps carried from crypto | screen (superseded) | `target_mde_bps_absolute__SUPERSEDED` = **10.0 for all 6,156 signed cells** (no 15-bps signed cells, so the scaling touched a homogeneous population) | confirmed |
| σ-scaled target = **1.7855 bps** | corrected run | `10 × 0.17854966 = 1.7854966`; emitted value identical on all 6,156 | **confirmed** |
| precision deflator = σ̂ ratio **0.17855** | `deflators.json` | `13.034237 / 73.001 = 0.1785488` — matches to 7 dp | **confirmed** |
| powered signed cells **2,401 → 315** | corrected run | `at_parent_target_precision & signed` = **315**; on the superseded flag = **2,401** | **confirmed** |
| `screen.md` §3: "**2,388** powered signed cells of **6,156**" | screen (STALE) | the powered count on that basis is **2,401**, not 2,388; and signed cells are **6,156** by `gross_p`-notnull but **5,888** by `(p,W,L)`-all-notnull | **STALE and internally unreproducible.** 2,388 reproduces under no definition I can construct. |
| the flag is reproducible from the block MDE | — | `gross_block_mde_mean_bps ≤ 1.7855` gives **317** vs the emitted 315 (99.97% agreement, 2 cells); on the absolute basis **2,485** vs 2,401 (98.5%) | **minor provenance gap.** The flag is not a pure function of the emitted MDE column; ~1–3% of cells carry an additional undisclosed condition. Immaterial to every conclusion, but it means the power flag cannot be independently regenerated from the emission. |

**Why this correction was necessary, and why the counts are not comparable across runs.** The parents' 10 bps rule was written for a universe with pooled σ̂ = **73.00 bps**. Importing it unchanged into a universe with σ̂ = **13.03 bps** loosens it by **5.6×** in the only units that matter — it is 0.137σ on crypto and 0.767σ here. Median block MDE on cTrader signed cells is **13.36 bps** (p5 1.74, p95 81.6), so the absolute rule was admitting cells whose measurement error was 7× the effect being measured. **Restating: SPDR-018's 1,413 powered cells and SPDR-018B's 315 are counted against different bars and must never be compared as counts.**

*(Operator ruling recorded, not acted on: this correction applies to 018B only. SPDR-018 is COMPLETE and FROZEN and is not reopened. The finding is recorded against it in §9 as a methodological note for future legs.)*

### 2.3 Cost — the deflator verified, and a circularity nobody flagged

| Claim | My re-derivation | Verdict |
|---|---|---|
| cost and precision deliberately use **different** deflators | confirmed: `deflators.json` states cost = realised payoff scale, precision = σ̂ noise ratio, and the emission applies them to different objects | **confirmed, and correct.** Cost scales with what a trade *pays*; the MDE scales with bar *noise*. Collapsing them was the original error. |
| arm B cost deflator **0.2611**, arm C **0.3118** | `panel_C` carries `cost_deflator = 0.31183168` for arm C and `median(cost_vol_scaled / cost_raw) = 0.31183168` exactly. Arm B's median charge (3.92 bps) is consistent with `13.5 × 0.2611 = 3.53` plus funding | **confirmed as applied** |
| the deflator supersedes the 0.17855 bar-vol ratio, "which was ~2× too low" | at the unscaled borrowed floor the median charge on the 315 is **7.89 bps** vs **2.43 bps** as applied — so the vol-scaled charge is ~3.2× lighter than the raw borrowed model | confirmed in direction |
| **NEW — the payoff scale is measured on the subset the precision fix invalidated** | `deflators.json` arm B = **43.166**; I reproduce it as *median W + median L over the 270 **absolute-powered** arm-B cells* = **43.182**. Arm C = **83.015**; I reproduce it as *median(W+L) over the 2,131 **absolute-powered** arm-C cells* = **83.015** (exact). | **the deflator's basis is the superseded power flag.** |

**What that circularity does and does not mean.** It is *defensible* as constructed: the crypto side used its own powered subset too (SPDR-018's powered arm B `W+L = 107.6+53.9 = 161.5` ≈ the stated 165.30; arm C `142.1+124.5 = 266.6` ≈ 266.22), so both sides are "payoff scale of the parent-powered population" — matched in construction. But the deflator is then **applied to a differently-defined population**, and it is not identified: the same statistic on the corrected 315-cell population is arm B **30.51** / arm C **52.12** (→ deflators 0.185 / 0.196), and over all signed cells arm B **116.21** / arm C **102.67** (→ 0.703 / 0.386). **The defensible deflator range spans 0.185 to 0.703 — a factor of 3.8 — depending on which population you scale.** Every net figure in this document is therefore uncertain by roughly ±2× in the charge.

**This does not touch the conclusion, and I checked that explicitly.** The net-clearing count is **0 of 315** at the applied vol-scaled charge (median 2.43 bps) *and* **0 of 315** at the unscaled borrowed charge (median 7.89 bps). Moreover the **maximum gross mean among all 315 powered cells is +1.389 bps**, so any charge above **1.39 bps** — i.e. anything above 57% of the applied charge, and far below the lowest defensible deflator — yields zero clearing cells. **The 0% is robust across the entire deflator range, and gross is primary anyway.**

### 2.4 The stale §2/§3/§4 headline figures, replaced

| `screen.md` figure | Status | Correct value |
|---|---|---|
| "12.9% of powered cells clear net break-even" | **STALE** (it is the 2,401-cell absolute-basis figure: I reproduce **310/2,401 = 12.91%**) | **0 of 315 = 0.0%** on the corrected basis — crypto's 0.0% is reproduced |
| "1 of 2,388 clears net at the unscaled 13.5 bps floor" | **STALE / unreproducible count** | **0 of 315** at the unscaled charge |
| `p` = **0.4922** | STALE (2,401-cell basis; I reproduce 0.49206) | **`p` = 0.4868** on the 315 |
| `p_be` (gross) = 0.4917 | STALE (I reproduce 0.49160 on 2,401) | **0.4855** |
| `p_be_net` = 0.5265 | STALE (I reproduce 0.52644) | **0.5334** |
| `W/L` = 1.034 | STALE (I reproduce 1.0342) | **1.0597** |
| gross mean = **−0.08 bps** | **holds on both bases** (−0.0801 on 2,401; −0.0804 on 315) | **−0.080 bps** |
| net mean = −2.62 bps | STALE (I reproduce −2.614) | **−2.500 bps** |
| "clears gross break-even 47.5%" | STALE (I reproduce 47.69% on 2,401) | **129 of 315 = 41.0%** |
| "W/L mirror R² **0.311**, and the low R² is a narrow-range artifact" | **STALE — and the conclusion it was defending is now unnecessary** | **R² 0.9746, slope 0.9656** on the 315. The mirror **replicates** (crypto 0.9667 / slope 0.9408). The R² 0.311 was noise admitted by the loose bar. |
| "mean log residual −0.0024" | mislabelled (it is the mean of `log R`, not a regression residual) | median `log R` = **−0.0098** on the 315 |
| band labels 2,424 WASH / 2,407 NOT_RESOLVABLE / 939 UNPOWERED / 301 CONTRADICTED / 85 SUPPORTED | **confirmed exactly** (all five counts reproduce) | — |
| unit pin σ̂ 13.03 bps, 3/3 symbols; crypto 73.00 | **confirmed** | EURUSD 7.69 · XAUUSD 13.71 · USTEC 20.62 |
| cells 7,578 = A 675 · B 630 · C 5,526 · D 747 | **confirmed exactly** | — |
| residue-item counts (A1 36 … D8 249) | **confirmed** item by item, allowing for the emission's multi-tag labels (`B1,B5`, `D5,D6,D8`, …) which sum to the screen's per-item totals | — |
| C2 "−4.21 bps / 30,319 rows" | **STALE and off-object** — already flagged by the prior analyst; the artifact now says so itself (`magnitude_matched_full_panel_shock_flag: "SUPERSEDED — net, and over all shock bars incl. rows carrying no momentum policy"`) | §7 |
| C2 raw split "shock True −3.43 / False +0.33 bps" | **STALE.** I re-derive from `panel_C`: **gross** −1.522 (n 30,319) vs **+0.265** (n 203,250). The screen's −3.43/+0.33 pair is neither the gross nor the net split I can reproduce | §7.1 |

---

## 3. The `(p, W, L, W/L, p_be, p_be_net, edge)` picture on the 315 powered signed cells

Every value is my own recomputation. **Pooled lines are disclosure only (L-03); the per-stratum tables below and in `results/analyst_stratum_tables.csv` are the binding object.**

### 3.1 Pooled disclosure, and the crypto comparison

| Term | **cTrader (315 powered)** | crypto SPDR-018 (1,413 powered) — *claim from its frozen `analysis.md`, different precision basis* |
|---|---|---|
| `p` | **0.4868** | 0.3887 |
| `W` (bps) | **24.66** | 128.65 |
| `L` (bps) | **20.99** | 75.55 |
| `W/L` | **1.0597** | 1.4844 |
| `p_be` (gross) | **0.4855** | 0.4025 |
| `p_be_net` | **0.5334** | 0.4992 |
| `edge` (`p − p_be_net`) | **−0.0544** | — |
| gross mean | **−0.080 bps** | −1.178 bps |
| gross **median** | **−0.560 bps** | −14.43 bps |
| gross 10% trimmed mean | **−0.573 bps** | −11.67 bps |
| net mean | **−2.500 bps** | −15.157 bps |
| cost charged | **2.431 bps** | 13.540 bps |
| clears gross break-even | **129 / 315 = 41.0%** | 459 / 1,413 = 32.5% |
| **clears net break-even** | **0 / 315 = 0.0%** | **0 / 1,413 = 0.0%** |
| `W/L > 1` share | 0.813 | 0.999 |
| rate term (`p_be − p`) | **+0.0023** | +0.0067 |
| cost term (`p_be_net − p_be`) | **+0.0529** | +0.0650 |
| **cost share of the gap** | **95.8%** | 90.7% |
| median `n` | 3,258 rows | 3,027 rows |

**The zero-line result replicates, and more tightly.** `p` sits **0.0013** from its own gross break-even; the gross mean is **−0.080 bps** on a universe whose σ̂ is 13.03 bps, i.e. **0.006σ**. On crypto the same quantity was −1.178 bps on σ̂ 73.00 = 0.016σ. **In volatility units the cTrader cells sit ~2.6× closer to the zero line than the crypto cells.**

**The distance to net break-even is the cost, not the rate** — the same decomposition crypto produced: arm C rate term **−0.0004** / cost term **+0.0469** (cost = 100.8% of the gap; the rate is *marginally above* its own gross break-even); arm B rate **+0.0046** / cost **+0.0788** (cost = 94.5%).

**And unlike crypto, the three point statistics broadly agree here.** Crypto's mean (−1.18) and median (−14.43) disagreed by 13 bps with 67.8% sign agreement — the fat-tail warning that made "at gross break-even" the most favourable of three framings. Here mean **−0.080** / median **−0.560** / trimmed **−0.573** differ by ~0.5 bps, with sign agreement 0.619 (mean-vs-median) and 0.721 (mean-vs-trimmed). The narrative and the median tell the same story on this universe. **But see §4: median and trimmed-mean CIs are not emitted at all**, so their uncertainty is unquantified — worse coverage than crypto's 1%.

### 3.2 By arm (binding stratum)

| Arm | powered | signed | med `n` | `p` | `W` | `L` | `W/L` | `p_be` | `p_be_net` | `edge` | gross bps | net bps | cost share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **B** (SPDR-013 residue) | **136** | 630 | 3,841 | **0.3604** | 20.03 | 10.46 | **1.7457** | 0.3642 | 0.4462 | −0.0820 | **−0.148** | −2.540 | 0.945 |
| **C** (SPDR-014 residue) | **179** | 5,526 | 3,256 | **0.4950** | 26.18 | 25.94 | **1.0167** | 0.4959 | 0.5430 | −0.0489 | **+0.018** | −2.429 | 1.008 |
| A (SPDR-012 residue) | 152 | — | — | *unsigned items — §5* | | | | | | | | | |
| D (SPDR-015 residue) | 525 | — | — | *unsigned items — §5* | | | | | | | | | |

**The two signed arms are structurally different objects and must not be pooled into one story** — the same warning SPDR-018 §9.1 issued, and it holds identically here. Arm B is a low-rate / high-asymmetry object (`p` 0.36, `W/L` 1.75); arm C is a near-coin-flip / near-symmetric object (`p` 0.495, `W/L` 1.017) **whose gross median is positive (+0.018 bps)** and whose rate sits *0.0004 above* its own gross break-even. Both arms' structure matches their crypto counterparts qualitatively (crypto: B 0.336/1.880, C 0.467/1.136) — **the arm-level geometry replicates across asset classes.**

### 3.3 By band

| Arm | Band | cells | `p` | `W/L` | gross bps | net bps | `edge` | cost share |
|---|---|---|---|---|---|---|---|---|
| B | DESIGN | 60 | 0.3532 | 1.657 | **−0.299** | −2.663 | −0.0936 | 0.867 |
| B | CONFIRM | 56 | 0.3647 | 1.757 | **+0.026** | −2.373 | −0.0805 | 0.993 |
| B | TRAIN | 20 | 0.3579 | 1.788 | −0.116 | −2.555 | −0.0629 | 0.959 |
| C | DESIGN | 25 | 0.4937 | 1.031 | +0.032 | −2.405 | −0.0431 | 0.992 |
| C | CONFIRM | 13 | 0.5179 | 0.958 | **+0.343** | −2.076 | −0.0714 | 1.015 |
| C | TRAIN | 141 | 0.4950 | 1.019 | −0.005 | −2.431 | −0.0480 | 1.000 |

**Bands agree.** The widest DESIGN-vs-CONFIRM gap is arm B at **0.33 bps** — an order of magnitude below the charge and ~2.5% of σ̂. Arm C's CONFIRM cell count is 13 and its +0.343 must not be over-read. **No band-instability problem exists at this `n`** — the same conclusion §6 reaches independently from the 627 native C7 pairs.

### 3.4 By clock

| Clock | cells | `p` | `W/L` | gross bps | `edge` | med `n` |
|---|---|---|---|---|---|---|
| H1 | 199 | 0.4947 | 1.0276 | **−0.006** | −0.0493 | 3,220 |
| M15 | 116 | 0.3541 | 1.7872 | **−0.148** | −0.0829 | 3,961 |

H1 sits **0.14 bps closer to gross break-even** than M15 — the same ordering crypto measured (H1 −0.13 vs M15 −1.98 bps there), at roughly one-fourteenth the magnitude, consistent with the 5.6× smaller volatility scale. The clock split is confounded with the arm split (arm C is H1-only among powered cells), so this is a disclosure, not an isolated clock effect.

### 3.5 By symbol (the binding stratum per AMENDMENT-S1 — credibility, never power)

| Symbol | cells | `p` | `W` | `L` | `W/L` | `p_be` | `p_be_net` | `edge` | gross bps | clears gross be | CI-excl-0 (−/+) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **USTEC** | 20 | 0.3658 | 27.85 | 15.02 | 1.857 | 0.3520 | 0.4030 | **−0.0540** | **+0.164** | 65.0% | 0 / 0 |
| **XAUUSD** | 26 | 0.3551 | 18.22 | 9.55 | 1.803 | 0.3567 | 0.4309 | −0.0910 | −0.262 | 26.9% | 2 / 0 |
| **EURUSD** | 62 | 0.4062 | 15.11 | 12.66 | 1.363 | 0.4232 | 0.5555 | **−0.1060** | −0.286 | 30.7% | 10 / 2 |
| `__CTRADER_POOLED__` | 207 | 0.4917 | 26.69 | 25.18 | 1.037 | 0.4909 | 0.5358 | −0.0499 | −0.023 | 43.5% | 0 / 0 |

**Heterogeneity in gross mean spans 0.45 bps across the three named instruments (+0.16 to −0.29) — about 3% of σ̂, and ~18% of the charge.** But the **`edge` is negative in every named symbol and in the pooled cells, without exception** — range −0.054 (USTEC) to −0.106 (EURUSD). **No instrument is an exception.** As on crypto, the *tightest* instrument carries the *worst* edge: EURUSD has the smallest `W` and `L` (15.1 / 12.7 bps), so the fixed charge is the largest fraction of its move — a cost-scaling effect, not a signal effect, and SoT §3.1's selection argument running in reverse. Only 3 symbols, so per-symbol homogeneity is asserted weakly; design §7 predeclared exactly this.

### 3.6 By residue item (powered cells only)

| Item | cells | `p` | `W/L` | `p_be` | `p_be_net` | `edge` | gross bps | med `n` |
|---|---|---|---|---|---|---|---|---|
| C1 (residual object) | 58 | 0.4967 | 1.0097 | 0.4976 | 0.5463 | −0.0521 | **+0.062** | 3,120 |
| C2 (shock-MOMO) | 20 | 0.4962 | 1.0116 | 0.4971 | 0.5407 | −0.0470 | −0.065 | 3,918 |
| C3 (ordered vol-flip) | 37 | 0.4886 | 1.0381 | 0.4907 | 0.5444 | −0.0544 | −0.051 | 2,277 |
| C4 (E-TOUCH/E-CLOSE) | 20 | 0.4949 | 1.0245 | 0.4940 | 0.5371 | −0.0433 | +0.062 | 4,614 |
| C5 (magnitude scaling) | 35 | 0.4962 | 1.0155 | 0.4962 | 0.5430 | −0.0483 | −0.006 | 3,221 |
| C6 (z/h dose-response) | 9 | 0.4947 | 1.0284 | 0.4930 | 0.5355 | −0.0405 | +0.111 | 13,108 |
| B5 (M15 arms) | 111 | 0.3595 | 1.7757 | 0.3603 | 0.4538 | −0.0864 | −0.145 | 4,018 |
| B4,B5 (ZZ leg) | 5 | 0.3537 | 1.8053 | 0.3565 | 0.3973 | −0.0432 | −0.170 | 3,054 |
| B-carried | 20 | 0.3874 | 1.5171 | 0.3973 | 0.4433 | −0.0535 | −0.210 | 1,819 |

Every arm-C item sits within **±0.11 bps** of zero gross, with `p` within **0.002** of its own `p_be` — the C5 pattern crypto found (selection scales `W` and `L` together, so it scales a near-zero) reproduces here in compressed form: across C1–C6 `W` moves 23.5→28.8 and `L` 22.7→27.8 **together**, and `W/L` moves only 1.010→1.038.

### 3.7 By exit geometry and event type

| exit_mode (powered) | cells | `p` | `W/L` | gross bps | `edge` |
|---|---|---|---|---|---|
| `combined` | 73 | 0.3938 | 1.486 | −0.080 | −0.0879 |
| `signalflip` | 63 | 0.3528 | 1.794 | −0.221 | −0.0737 |
| `stop` / `time` / `trail` | **0** | — | — | — | — |

| event_type (powered) | cells | `p` | `W/L` | gross bps | `edge` |
|---|---|---|---|---|---|
| E-TOUCH | 100 | 0.4964 | 1.0179 | **+0.124** | −0.0468 |
| E-HORIZON | 11 | 0.4897 | 1.0327 | +0.158 | −0.0405 |
| E-CLOSE | 68 | 0.4924 | 1.0039 | **−0.491** | −0.0521 |

**The E-TOUCH > E-HORIZON > E-CLOSE ordering replicates.** Crypto measured E-TOUCH +0.6…+1.5, E-HORIZON −0.03…+0.69, E-CLOSE −1.2…−3.0 bps. Here: **+0.124 / +0.158 / −0.491** — same sign pattern, ~0.6 bps spread against crypto's ~3–4 bps, i.e. ~1/5 the magnitude on a universe with 1/5.6 the volatility. **A genuine measured structural replication, and it is well below the cost floor in both universes.**

**That `stop`/`time`/`trail` contribute 0 powered cells is a power statement, not a negative** — and it is the hinge of the selection finding in §8.

---

## 4. Uncertainty, CI hygiene, and what is *not* emitted

| Statistic | CI present on the 315 |
|---|---|
| `gross_mean`, `gross_p`, `gross_W`, `gross_L`, `gross_W_L`, `gross_edge` | **315 / 315 (100%)** |
| `gross_median`, `gross_trimmed_mean_10`, `net_median`, `net_trimmed_mean_10` | **no CI column emitted at all** |

Design §6.1 (inherited) requires block-bootstrap CIs on **mean, median and 10% trimmed mean**, "all three always co-reported", explicitly because this family is fat-tailed. On crypto this was 1% present; here the columns **do not exist**. The point statistics are all emitted; the uncertainty on two of three is entirely absent.

**Practical impact is smaller here than on crypto** — the three point statistics agree to ~0.5 bps on the 315 (§3.1), so the mean is not the flattering choice this time. **But the arm-B `trail` population in §8 is exactly the case where it matters** (mean-of-means −24.3 bps vs median-of-means +7.6 bps, min −1,002 bps), and there is no bootstrapped median anywhere to check it against. Recorded as an inherited compliance gap and as proposal **P2**.

**Other CI hygiene:** all mean CIs come from the block-bootstrap path with the block-MDE driving band labels (M-1, HARD, held). I could not verify `ci_low_seed_range` or a `block_sensitivity` sweep — **neither is emitted**, so no read in this document can be checked for MC-fragility or block-fragility. For the two positive CI-excluding-zero cells in §3 (both C1 EURUSD DESIGN, CI_low 0.146 and 0.118 bps) that fragility matters directly: their CI_low is within a whisker of zero and I cannot state whether the seed band straddles it. **I therefore report them as CI-excludes-zero but MC-unverifiable, and I do not treat them as findings.** Proposal **P3**.

---

## 5. Arms A and D — the unsigned residue items (what replicates)

These arms carry no `(p, W, L)` layer; their estimands are gaps, ICs, R², Brier deltas and stickiness. Reported as magnitudes per stratum, never as verdicts.

| Item | cells / at target | Measured answer on cTrader | vs crypto claim |
|---|---|---|---|
| **A1 V-REGIME-HMM** | 36 / 24 | HIGH−LOW next-\|move\| gap median **+6.88 bps** [p5 −5.91, p95 +33.38]; **55.6%** of cells CI-excluding-zero positive; thirds populated 3/3, sign agrees 3/3 (median). Labels: 27 WASH · 6 UNPOWERED · 2 SUPPORTED · 1 NOT_RESOLVABLE | crypto pooled H1 +18…+48 bps. **Direction and CI-positivity replicate**; magnitude scales roughly with σ̂ (6.9/13.0 ≈ 0.53σ vs 18–48/73 ≈ 0.25–0.66σ) — **a real replication** |
| **A2 V-TAIL exceedance** | 72 / 56 | p90/p95 exceedance-rate gap median **+0.0095** [p5 −0.019, p95 +0.047]; only **8.3%** CI-excluding-zero; **all 72 WASH** | crypto H1 +0.056/+0.031 with 90.9% CI-excluding-zero. **Does NOT replicate at this `n`** — magnitude ~6× smaller and mostly inside the CI. Reported as a magnitude, not a negative |
| **A3 DESIGN-band deficit / IC** | 432 / 292 | rank IC median **+0.2277** [p5 +0.010, p95 +0.449], `ic_ci_low` median **+0.152**; labels **305 SUPPORTED** · 61 UNPOWERED · 28 WASH · 2 CONTRADICTED. Date coverage median **390** dates, `n_dates_short_of_225` median **0** | crypto H1 per-symbol IC 0.326, 100% CI-excluding-zero. **Replicates at ~70% of the magnitude.** The 225-date shortfall that bound crypto's DESIGN band does **not** bind here |
| **A4 V-CLOCK calendar dummies** | 108 / 72 | incremental R² median **+0.0291** [p5 −0.0007, p95 +0.127] | crypto measured **−0.032 to −0.0004** (zero to slightly negative). **Does not replicate — and it reverses sign.** On 3 instruments with in-sample R², a small positive incremental R² is what over-fitting looks like; I read this as an estimator statement, not a market statement, and flag it in §11 |
| **A5 §6.4 clause + calendar thirds** | 27 / 0 | **27 of 27** `clause_satisfiable = True`, `thirds_populated = 3`, `thirds_sign_agree = 3` | crypto: 135/135 identical. **Replicates completely.** (0 at target is a definitional gap — no bps target attaches to this item — not a power failure) |
| **D1 / D-carried transitions** | 216 / 216 | `n_trans` clears the min-transitions rule; ΔBrier vs persistence median **−0.0205** (improvement), `delta_brier_ci_hi` median **−0.074** | crypto D1 resolved on H1. **Replicates** |
| **D2 run-length MAE** | 36 / 0 | MAE median **9.73 bars** against predicted run length `E[run]` median **23.8 bars** | crypto: MAE 11.95 vs E[run] 18.9–23.1. **Replicates** — the predictor's typical error is ~40% of the quantity it predicts (crypto: ~55%) |
| **D5 R-MARKOV k=1** | 81 / 81 | ΔBrier at k=1 median **0.0000** | crypto: "k=1 is inert". **Replicates exactly** |
| **D6 R-HMM-RV** | 108 / 108 | ΔBrier median **−0.0178** (k median 4), `ci_hi` median −0.0059 | crypto: −0.0060 (k=4) / −0.0317 (k=12). **Replicates, same order** |
| **D7 D1 stickiness** | 9 / 0 | `p_stay` median **0.9517** [p5 0.921, p95 0.984] | crypto 0.9365–0.9486. **Replicates to within 0.005** — daily level-regimes are ~95% sticky on this universe too |
| **D8 CONFIRM verify slice** | 249 / 249 | ΔBrier median **−0.0256**, `ci_hi` median −0.039; accuracy median 0.827 vs base rate 0.238 | crypto: the most robust positive object in the run. **Replicates** |

**Arms A and D are the strongest replication evidence in this run** — the `E[|move|]` and regime-forecasting objects reproduce across the asset-class boundary at magnitudes that scale roughly with volatility. SoT §1.1's "the `E[|move|]` results parameterise capture design regardless of what the rate does" survives a second universe. **Two items do not replicate (A2, A4); both are reported as magnitudes and neither is powered enough on 3 instruments to be read as a refutation (B-5).**

---

## 6. Coverage gaps CLOSED — C7, C8 (native) and B3 (native)

SPDR-018's B3 was defined by pointing at SPDR-013's published *crypto* table, which has no cTrader analogue; C7/C8/C9 were simply not implemented in the original 018B arm-C runner. C7, C8 and a **native** B3 were subsequently built and emitted. I verified all three from the emitted tables.

### 6.1 C7 — DESIGN→CONFIRM sign flip (`coverage_gap_C7_C8.parquet`, 627 pairs)

| Quantity | cTrader | crypto SPDR-018 (claim) |
|---|---|---|
| pairs | **627** | 2,714 |
| share flipping sign | **40.99%** | 44.14% |
| of flipped, band CIs overlap | **90.27%** | 91.82% |
| pairs whose \|Δ\| exceeds the pooled two-band MDE | **1.44%** (flipped only: **3.11%**) | 6.63% (flipped: 12.94%) |
| DESIGN / CONFIRM, equal-cell-weighted | **−4.37 / −1.24 bps** | −1.65 / −19.77 |
| DESIGN / CONFIRM, **`n`-weighted** | **−2.82 / −2.17 bps** (diff **0.65**) | −13.72 / −13.39 (diff 0.33) |
| median `n` | DESIGN 301, CONFIRM 140 | 41 / 111 |

**C7 resolves the same way it did on crypto, independently.** The flip rate is **below** a coin flip (signs *agree* in 59.0% of pairs), 98.6% of all changes are inside the measurement error, and the apparent band reversal is a **weighting artifact**: weighted by information content the two bands agree to **0.65 bps**. The checkpoint-017 DESIGN→CONFIRM instability is **not present at this `n` on this universe either.** A genuine resolution; record it as one.

### 6.2 C8 — pooled rate lean (339 cells)

Row-weighted `p_momo` median **0.4939**; symbol-weighted **0.4946**; median absolute difference between the two weightings **0.0009**. Per-symbol lean: median 1 momo-leaning vs 2 MR-leaning of 3 symbols.

**The 017 "two weightings disagree" concern dissolves here exactly as it did on crypto** (which found 0.4676 / 0.4699, differing by 0.0023). **The measured lean is toward mean-reversion in both universes** — 0.494 here, 0.468 on crypto, against a 0.50 reference — and the two weightings agree to a thousandth. Note the cTrader lean is *weaker* (0.494 vs 0.468): closer to symmetric, consistent with everything else on this universe sitting nearer the zero line.

### 6.3 B3 — positive-mean cells, NATIVE definition (159 cells)

Built natively as "arm-B cells whose mean is positive on this universe" rather than by reference to a crypto table.

- **159 cells; 100% have `gross_mean > 0` AND `net_mean > 0`** (median gross **+15.79 bps**, median net **+9.34 bps**).
- Median `p` **0.5484**, `W` 98.04, `L` 68.21, `W/L` **1.161**.
- Split: DESIGN 76 · CONFIRM 70 · TRAIN 13; H1 82 / M15 77; USTEC 50 · pooled 39 · EURUSD 36 · XAUUSD 34.
- **`at_parent_target_precision`: 0 of 159.** Median `n` **84** episodes over **61** dates; **median block MDE 29.22 bps against a 1.785 bps target — 16.4× short.**

**B3's substantive answer on this universe: UNPOWERED, by a factor of 16.** Per B-5 that is a power statement and nothing else — these 159 cells are not evidence of an edge and not evidence against one. **And they are the direct illustration of §8:** 63 of the 159 are `trail` cells and 36 are `stop` cells — 99 of 159 (62%) are the one-tailed exit geometries whose loss tail has not yet fired. A positive-mean selection on this family is dominated by cells whose dispersion is too large to measure, which is precisely why the precision bar exists.

### 6.4 Items still OPEN — never to be read as nulls

| Item | State | Why |
|---|---|---|
| **C9 `DA-STRADDLE`** | **OPEN / NOT RUN** | not implemented in the 018B arm-C runner. **0 cells** in the grid (verified: no `residue_item` contains "C9"). Operator accepted it stays open. |
| **D3 `T-GT-MED10`** | **OPEN / NOT RUN** | arm D's 2b leg reads SPDR-015's emitted crypto ZigZag panel; a cTrader ZigZag panel was not built. **0 cells** in the grid. |
| **D4 `T-GT-MED5`** | **OPEN / NOT RUN** | same cause. **0 cells.** On crypto, `ridge_cont` at K=5 was the *strongest* D3/D4 cell (hit 0.585 vs base 0.483, +0.107 lift). **Its cTrader status is unknown, not negative.** |

**These three are not absent, not null, and not evidence of anything.** They require a ZigZag panel on cTrader bars (D3/D4) and a straddle runner (C9) before any statement about them is possible.

---

## 7. `C2` shock-conditioned MOMO — the replication target, and my adjudication

This item is the reason SPDR-018B exists. It was SPDR-018's only live thread — the single object simultaneously above the partial cost floor, surviving its M-3 magnitude-matched control, and in the registered direction — and it had **zero external replication**.

### 7.1 The object, rebuilt by me from `panel_C`

The `−4.21 bps / 30,319 rows` figure in `screen.md` §4 is **net** and covers **all** shock bars. I confirm from the panel why that is off-object: of 30,319 shock rows, **only 1,594 (5.26%) carry the momentum policy**; 27,055 (89.2%) carry `P-NONE`. The emitted artifact now self-labels that read `SUPERSEDED`.

My own reconstruction of the raw split, **gross**:

| Slice | n rows | gross mean |
|---|---|---|
| all rows, `shock_flag = True` | 30,319 | **−1.522 bps** |
| all rows, `shock_flag = False` | 203,250 | **+0.265 bps** |
| **`P-MOMO` & shock (the C2 object)** | **1,594** | **−2.414 bps** |
| `P-MOMO` & no shock | 9,758 | **+1.854 bps** |
| `P-MR` & shock | 1,670 | −0.149 bps |
| `P-MR` & no shock | 9,856 | — |

The emission's `magnitude_matched_C2_MOMO_gross.live_effect_bps = −2.4137` reproduces my figure **exactly**.

### 7.2 The M-3 comparator as emitted, and by session

| Read | live (bps) | comparator mean | pct | `n_live` | plant curve {5,10,20,40} → pct |
|---|---|---|---|---|---|
| `P-MOMO` gross (the C2 object) | **−2.414** | **+3.763** | **0.000** | 1,594 | {0.27, 1.00, 1.00, 1.00} |
| `P-MR` gross | −0.149 | +1.972 | **0.0665** | 1,670 | {0.965, 1.00, 1.00, 1.00} |
| `shock_flag`, primary cell *(the like-for-like crypto analogue)* | **−9.383** | −1.585 | **0.043** | **290** | {0.285, 0.755, 1.00, 1.00} |
| `mag_high`, primary cell | −3.402 | −2.068 | 0.2735 | 1,145 | {0.955, 1.00, 1.00, 1.00} |
| **`P-MOMO` by session — ASIA** | **−13.572** | **+12.052** (sd 5.14) | **0.000** | **184** | **{0.00, 0.00, 0.115, 0.995}** |
| **`P-MOMO` by session — EU** | **+0.620** | +0.967 (sd 2.49) | **0.443** | 557 | {0.98, 1.00, 1.00, 1.00} |
| **`P-MOMO` by session — US** | **−1.988** | +3.459 (sd 1.67) | **0.000** | 853 | {0.42, 1.00, 1.00, 1.00} |

All comparators are non-vacuous on supply: `deciles_with_no_comparator_supply: []` in every case, and I verified the decile tables directly (C2 MOMO: live 157–162 per decile against pool 805–1,249; ASIA: live 18–19 against pool 350–546). 2,000 seeds, decile-stratified, ±1 bar neighbourhood excluded, `status: MATCHED`.

**Every number the orchestrator asked me to verify reproduces from the artifact: −2.41 / pct 0.000 / n 1,594; P-MR −0.15 / 0.067; ASIA −13.57 / 0.000 / 184; EU +0.62 / 0.443 / 557; US −1.99 / 0.000 / 853.**

### 7.3 My independent rebuild — where it agrees and where it does not

I rebuilt the decile-stratified comparator myself (my own decile edges on the live rows' `|r_h|`, same-decile draws without replacement from the disjoint no-shock pool, 2,000 seeds):

| Read | emitted live / comparator / pct | **my rebuild** live / comparator / pct |
|---|---|---|
| `P-MOMO` gross | −2.414 / +3.763 / 0.000 | **−2.414 / +1.497 / 0.0045** |
| `P-MR` gross | −0.149 / +1.972 / **0.0665** | **−0.149 / −1.450 / 0.826** |
| ASIA | −13.572 / +12.052 / 0.000 | **−11.530 / +9.980 / 0.000** (my session cut, n 162) |
| EU | +0.620 / +0.967 / 0.443 | **−1.111 / −1.166 / 0.5125** (n 334) |
| US | −1.988 / +3.459 / 0.000 | **−1.465 / +2.322 / 0.0115** (n 1,098) |

**The live values reproduce exactly. The comparator level does not.** My comparator sits **2.3 bps lower** than the emitted one on `P-MOMO` and **3.4 bps lower** on `P-MR` — differences of the same order as the effects being adjudicated. **On `P-MR` that flips the read entirely**: the emission places `P-MR` *below* its comparator at pct 0.0665; my rebuild places it *above* at pct 0.826. My session boundaries are my own guess (UTC hour <7 / <13 / else), which explains the session `n` differences, but the pooled `P-MOMO` and `P-MR` reads use no session cut at all — those discrepancies are pure comparator construction.

**The session *pattern* is robust; the comparator *level* is not.** Asia strongly negative, EU indistinguishable, US mildly negative reproduces under my independent construction. The magnitudes and the `P-MR` sign do not.

### 7.4 The decisive structural problem: the comparator is not a neutral yardstick

Three facts from the emitted null distributions:

1. **The comparator's own mean varies 12× across sessions** — ASIA **+12.05**, US **+3.46**, EU **+0.97** bps. A yardstick that moves from +1 to +12 bps depending on the hour is measuring something session-specific, not providing a neutral zero.
2. **In Asia, the entire null distribution sits above zero.** Null quantiles are q5 **+2.09** → q95 **+22.16**. **Therefore any live value at or below +2.09 bps returns percentile ≈ 0.000 — including a live value of exactly zero.** The same holds pooled (`P-MOMO` null q5 = **+1.09**) and in the US (q5 = **+0.03**). The reading "percentile 0.000" is *not* evidence of a reversal; it is evidence that the live arm is below a comparator whose own mean is far above zero.
3. **The Asia control's plant curve is nearly blind upward.** A **+20 bps** plant only reaches percentile **0.115**; even **+40 bps** reaches 0.995. So on 184 rows this control could not have detected a +20 bps *positive* shock-MOMO effect at all — while it reports 0.000 downward. **The control is directionally asymmetric at this `n`, and its upward resolution is ~40 bps against a live effect of −13.6.** Reporting a 0.000 from an instrument that cannot see +20 bps in the other direction is not a two-sided read.

I can name what the comparator is picking up: within Asia-session no-shock `P-MOMO` rows, the *unstratified* mean is only **+0.83 bps**, but the *magnitude-matched* comparator mean is **+9.98**. The matching selects large-`|r_h|` no-shock rows, and **those** earn strongly positive in Asia. So the honest mechanical statement is: *large moves without a volatility shock carry positive momentum continuation in the Asia session; large moves with a shock do not.* That is a statement about the interaction of magnitude and shock on 162–184 rows — not "shock predicts reversal on cTrader".

### 7.5 **C2 ADJUDICATION — my ruling on how much weight it can carry**

> **The C2 crypto thread is NOT REPLICATED and NOT REFUTED. C2 evidence from SPDR-018B may carry weight ONLY as a "this does not transport cleanly" flag. It may NOT be used to close the C2 thread, and it may NOT be reported as a cross-asset-class reversal.**

Six reasons, in order of force:

1. **The like-for-like objects are not the same object.** Crypto's survivor was `shock_flag` on the arm-C primary cell (**n 505**, live +22.6, pct 0.95). Its direct cTrader analogue is `magnitude_matched.shock_flag` (**n 290**, live −9.38, pct 0.043) — whose plant curve says a **+10 bps** plant only reaches pct **0.755**. That control **could not have resolved crypto's +22.6 bps effect reliably at this `n`**. The corrected `P-MOMO` object (n 1,594) is a *different and better* object, but it has no crypto counterpart to be compared against. **There is no properly matched pair of reads in existence.**
2. **The comparator's zero is not zero** (§7.4). Percentile 0.000 is attainable by a genuinely zero-effect arm in every session and in the pooled read.
3. **The comparator level does not survive independent reconstruction** (§7.3), and on `P-MR` the sign of the read reverses.
4. **The session structure destroys any clean asset-class reading.** The effect concentrates in **Asia** (n 184, the thinnest and least liquid session) and **vanishes in EU** (pct 0.443), the deepest-liquidity session for two of the three instruments. A cross-asset-class mechanism should not live exclusively in the thinnest session; a microstructure or comparator-composition artifact plausibly would.
5. **The grid agrees with neither story.** The 20 **powered** C2 cells sit at gross **−0.065 bps**, `p` 0.4962 against `p_be` 0.4971 — i.e. flat. The C2 signal is nowhere in the powered grid, in either direction.
6. **Multiplicity.** 7,578 cells, five separately-cut M-3 reads on the same object. Per L-34 the tail counts must be read against the realised multiple-testing process, not against zero.

**What C2 *can* support.** One negative and one positive statement, both narrow: (a) *shock-conditioned momentum does not carry an above-cost positive residual on EURUSD/XAUUSD/USTEC in TRAIN* — 20 powered cells at −0.065 bps gross, best gross among all 315 powered cells +1.39 bps against a 2.43 bps charge; and (b) *within this universe, magnitude and shock interact in a session-dependent way that is worth its own measurement* — momentum continuation on large no-shock moves runs +10 bps in Asia and ~0 in EU. **(b) is a new lead, not a replication result, and it is the only genuinely new substantive thing in this run.**

**Consequence for the reflection.** Checkpoint-018's C2 thread remains **OPEN on the crypto evidence**. The correct next step is the one SPDR-018 §14 P1 already named — re-run the M-3 comparator at `n` in the thousands on the *powered crypto grid strata*, with multiplicity treated and with the comparator's own mean reported as a first-class quantity. **A comparator whose null mean is not disclosed alongside the percentile is not interpretable**, and that is the single most reusable lesson from this pass.

### 7.6 The other controls

| Control | live | comparator/null | pct | resolution (own plant curve) | What it establishes |
|---|---|---|---|---|---|
| SIDE-DERANGEMENT, arm B | −1.441 bps | mean +0.027, sd 1.905 | **0.229** | ~5 bps (plant 5 → 0.97) | arm B's side labels carry **no side-attributable effect above ~5 bps**. A resolution statement, not "no effect" |
| SIDE-DERANGEMENT, arm C | **−2.632 bps** | mean +0.382, sd 1.551 | **0.023** | ~5 bps (plant 5 → 0.92) | **the sides in arm C's primary cell carry real directional information, and it points against the registered direction.** 0 fixed points, 2,000 seeds, side-label agreement 0.498. **Replicates crypto's arm-C finding** (there: −12.22, pct 0.0065) at ~1/5 the magnitude — i.e. it scales with σ̂ |
| M-3 `mag_high` | −3.402 | −2.068 | 0.2735 | ~5 bps | live minus comparator **−1.33 bps**: the magnitude-matched comparator **reproduces essentially the whole `mag_high` effect**. On this cell `mag_high` is "the decision bar was large", not "the volatility state" — **replicating crypto's `mag_high` conclusion exactly** |
| AMBIENT-BASE, arm C | live mean −4.654 [−7.99, −1.19], `p` 0.4500, `W` 53.01, `L` 51.84, `W/L` 1.0226 | ambient mean −4.601, `p` 0.4367, `W` 46.34, `L` 44.10, `W/L` 1.0508 | disclosure | n_live 2,602 vs n_ambient 210,691 | **Δmean −0.053 bps** — the conditional effect on the mean is *nil*. **But the distribution moves:** `p` **+0.0133**, `W` **+6.67**, `L` **+7.74**, `W/L` **−0.028**, dispersion IQR **+13.77 bps**. **The arm-C event scales the opportunity and scales both sides of it, so the rate gain and the `L` inflation offset to ~zero — the crypto ambient-base finding replicated on an independent universe.** A mean-only read would have said "nothing happened", and something did |
| TRIPWIRE-3 forward-path derangement | −4.654 | mean +0.338, sd 1.544 | 0.000 | report layer | correctly **not** the causality claim (SPDR-012 AMENDMENT-T1). Collapse 1.073, disclosure-only per M-5 (the live mean is near zero, so the ratio is uninterpretable). **Carries no weight in either direction** |
| TRIPWIRE-2 | legal 0.494 bps | leaky twin 203.65 bps | — | 106 matched rows | **412× separation** — genuinely orders of magnitude, and materially stronger than SPDR-018's own 7.55×. The causality claim (with TRIPWIRE-1) is **satisfied on this universe** |

**Note on M-5 and every collapse fraction in this run:** live means here are 1–5 bps on a 13 bps σ̂ universe, so *every* collapse fraction is uninterpretable by M-5's own rule. The emitted values (1.019, 1.145, 0.392, 0.831, 2.559, 14.24, 1.073) should be read as disclosure only and none of them carries an inference.

---

## 8. The selection-artifact check on the powered subset

**The candidate KB finding, as stated:** *a precision gate is a DISPERSION gate, and on skewed P&L it is not sign-neutral — it retains cells whose loss tail has not yet fired. Claim: in 018B it manufactured ten arm-B trailing-stop cells at +7 to +23 bps drawn from a population of 116 excluded cells averaging −27.6 bps.*

### 8.1 The specific claim — VERIFIED EXACTLY, on the superseded basis, and it has since VANISHED

| | Value |
|---|---|
| arm-B `trail` cells | **126** |
| powered on the **superseded absolute 10 bps** basis | **10** |
| their gross means | **+7.13, +7.21, +8.55, +9.51, +10.24, +11.33, +17.03, +22.07, +22.89, +22.97** — i.e. exactly "**ten cells at +7 to +23 bps**" |
| all ten with `gross_mean_ci_low > 0` | **10 / 10** (CI_lows +2.68 to +15.48) |
| the excluded population | **116 cells, mean of means −27.610 bps** — reproduces the claim to 3 dp |
| **powered on the corrected σ-scaled basis** | **0 of 126** |

**The claim is exactly right, and the precision correction has already removed the artifact.** The ten cells are all `CONFIRM`/`DESIGN` × `M15`/`H1` on EURUSD (7) and XAUUSD (3), median `n` 72 episodes, block MDE 2.5–9.1 bps — all above the corrected 1.785 bps bar, none above the old 10 bps bar.

### 8.2 Why they looked like an edge — the mechanism, quantified

The ten cells carry **`p` 0.797–0.889 together with `W/L` 1.01–6.67**. A high win rate *and* a high payoff ratio is the arithmetic signature of a **truncated loss tail**, not of an edge: a trailing stop books many small wins and defers the large losses until they fire.

The full `trail` population proves that directly:

| `trail` gross_mean distribution (126 cells) | value |
|---|---|
| min | **−1,002.19 bps** |
| p5 / p25 | −191.97 / −29.07 |
| **median** | **+7.64** |
| p75 / p95 / max | +21.07 / +49.26 / +89.15 |
| **mean of means** | **−24.32** |
| cells with gross_mean > 0 | **82 of 126 (65%)** |

**The median `trail` cell is +7.6 bps and the mean `trail` cell is −24.3 bps.** The population is 65% positive and catastrophically negative on average. A dispersion filter applied to *this* distribution selects the pre-tail cells by construction. **Confirmed, with numbers. Those ten cells must never be read as an edge, and neither must the 63 `trail` cells in the native B3 set (§6.3).**

### 8.3 The general effect on the corrected 315 — and it runs the OTHER way

The mechanism is real and general, but its *direction* is not fixed. Measured on the whole grid:

| | payoff scale `W+L` (median) | mean of gross means | share with gross mean > 0 |
|---|---|---|---|
| 315 powered (σ basis) | **46.17 bps** | −0.08 | 41.0% |
| excluded signed cells | **106.38 bps** | −0.17 | — |
| arm B powered / excluded | **30.51 / 180.33** | **−0.138 / +6.627** | **0.287 / 0.518** |
| arm C powered / excluded | 52.12 / 104.65 | −0.058 / −2.320 | 0.503 / 0.477 |

**The precision gate cuts the payoff scale roughly in half — it is unambiguously a dispersion gate.** And on arm B it removes the *positive* cells: excluded cells average **+6.63 bps** and are 51.8% positive, while powered cells average **−0.14 bps** and are 28.7% positive. On the superseded basis the same asymmetry was milder (powered 40.4% positive vs excluded 51.7%).

**Refinement I am adding to the KB finding:** the gate is **not sign-neutral, and its bias direction depends on the sign of the population's skew, not on the gate.** On the fat-left-tailed `trail`/`stop` population it retains the pre-tail *positives* (the original claim). On arm B as a whole it *discards* the positives. Either way the powered subset's magnitudes are a biased read of the population's, and the correct discipline is the same in both directions.

### 8.4 The operational check I recommend become standard

For any powered subset drawn from a fat-tailed population, report three numbers before reading any magnitude:

1. **payoff scale ratio** — median `W+L` powered ÷ excluded (here **0.43**: the gate halves the payoff scale);
2. **sign-share differential** — share with positive mean, powered vs excluded (here arm B **0.287 vs 0.518**);
3. **mean-vs-median divergence in the excluded population** (here `trail`: **−24.3 vs +7.6 bps** — a 32 bps gap that announces an unfired tail).

All three are one line of code on the emitted per-cell table, and any of the three alone would have caught this instance.

---

## 9. The two candidate KB findings — confirmed / refined / overturned

### Finding 1 — **CONFIRMED, and strengthened. Recommend ratification.**

> *An absolute-bps precision target is not portable across universes with different volatility scales. Targets must be stated in σ units or re-derived per universe.*

| Evidence | Value |
|---|---|
| pooled σ̂: crypto vs cTrader | **73.00 vs 13.03 bps — 5.6×** |
| the 10 bps target in σ units | **0.137σ on crypto, 0.767σ on cTrader** — silently loosened 5.6× |
| powered signed cells: absolute vs σ-scaled | **2,401 → 315 (a 7.6× inflation)** |
| net-clearing rate: absolute vs σ-scaled | **12.91% → 0.00%** |
| `W/L` mirror R²: absolute vs σ-scaled | **0.139 (all signed) / ~0.31 (screen's read) → 0.9746** |
| median block MDE on signed cells | **13.36 bps** — the absolute bar was admitting cells whose error was ~7× the effect |

**Three separate headline conclusions were wrong in the same direction because of this one defect**, and each was corrected by the same fix: the net-clearing rate, the powered count, and the mirror R². **This is the load-bearing methodological finding of SPDR-018B.** It generalises beyond precision targets to **any absolute-unit threshold crossing a universe boundary** — cost floors, MDE bars, effect-size gates, "materiality" cut-offs. It is the same class of defect as P-15 / L-21 (the EXP-025 unit-seam inflation), one level up: L-21 pins the *normaliser object*; this pins the *threshold's units*.

**Proposed wording:** *any threshold expressed in absolute price units (bps) is universe-specific. Crossing a universe, asset class, or volatility regime, a threshold must be either (a) re-derived from the new universe's own measured scale, or (b) restated in σ units with the σ object pinned per L-21. Carrying an absolute threshold unchanged is a silent amendment whose looseness equals the σ ratio — and it will not appear in any diff.*

**Recorded against SPDR-018, not acted on:** SPDR-018's own single cTrader replication leg (42 cells, gross only) reported medians against crypto-derived reference values. Its `analysis.md` §9.5 handled this correctly (gross only, no `edge` claimed, credibility not power) so no SPDR-018 number is affected. **SPDR-018 is not reopened.**

### Finding 2 — **CONFIRMED in mechanism, REFINED in direction, and its named instance is now MOOT.**

> *A precision gate is a DISPERSION gate, and on skewed P&L it is not sign-neutral — it retains cells whose loss tail has not yet fired.*

- **Mechanism: confirmed** — the gate halves the payoff scale (median `W+L` 46.2 powered vs 106.4 excluded).
- **The specific instance: verified exactly** — 10 arm-B `trail` cells at +7.13…+22.97 bps, all with CI_low > 0, against 116 excluded cells averaging **−27.610 bps** (§8.1).
- **And that instance no longer exists** — 0 of 126 `trail` cells survive the corrected σ-scaled bar. Finding 1's fix removed Finding 2's example.
- **Refinement (mine):** the bias is **not directionally fixed.** On the fat-left-tailed `trail` population the gate retained the positives; on arm B overall it *discards* them (powered 28.7% positive vs excluded 51.8%; excluded mean +6.63 vs powered −0.14 bps). **The finding should be stated as "a dispersion gate biases the retained magnitudes whenever the population is skewed — in the direction of the skew, not in a fixed direction" — with the three-number check in §8.4 as the operational remedy.**

**Both findings survive. Finding 1 is the more consequential and I recommend it be ratified as a lesson; Finding 2 should be ratified in its refined form with the §8.4 check attached.**

---

## 10. What replicates, what does not, and what is NOT RESOLVABLE — the three-way split

Every row carries its power statement. **Only powered cTrader cells are informative about crypto (B-5 / design §7).**

### 10.1 REPLICATES (powered on cTrader, agrees with crypto)

| # | Object | cTrader | crypto claim | Power statement |
|---|---|---|---|---|
| R1 | **The zero-line result** — `p` at its own gross break-even | `p` **0.4868** vs `p_be` **0.4855** (gap 0.0013); gross mean **−0.080 bps = 0.006σ** | 0.3887 vs 0.4025 (gap 0.0138); −1.178 bps = 0.016σ | 315 powered, median n 3,258. **Powered.** In σ units cTrader sits **2.6× closer** to zero |
| R2 | **Nothing clears net break-even** | **0 / 315 = 0.0%**, at both the vol-scaled and the unscaled charge, and at any charge above 1.39 bps | 0 / 1,413 = 0.0% | **Powered.** Best cell +1.389 bps gross vs a 2.43 bps charge |
| R3 | **The `W/L` mirror** — payoff asymmetry is the arithmetic mirror of the rate | **R² 0.9746, slope 0.9656, intercept −0.0030**, sd(log R) 0.0607, free share **0.163**, median log R −0.0098 | R² 0.9667, slope 0.9408, sd(log R) 0.0729, free share 0.193 | 315 powered. **Powered, and a tighter replication than crypto's own fit** |
| R4 | **`W/L` is movable and moving it does not help** | exit geometry moves `W/L` **0.274 → 9.975 = 36.4×** while `p` moves inversely 0.840 → 0.0625; gross median does not improve (`trail` +7.6 median but **−24.3 mean**; `stop` −10.4 median; `signalflip` −0.22) | 67× movable, `p` inverse, mean worst at the extreme | all 630 arm-B signed cells. Per-mode powered counts: `combined` 73, `signalflip` 63, others **0 — a power statement** |
| R5 | **Per-cell `W/L` cannot be separated from the driftless mirror** | CI excludes the mirror in **22 of 315 (7.0%)**; **93.0% indistinguishable** | 17.2% / 82.8% | **Powered.** Even *less* separable here |
| R6 | **The cost, not the rate, is the whole gap** | cost share **95.8%** pooled; arm C **100.8%** (rate −0.0004), arm B **94.5%** | 90.7%; C 98.8%, B 88.4% | **Powered** |
| R7 | **Selection scales both sides of the identity** | ambient-base arm C: `W` **+6.67**, `L` **+7.74**, `W/L` **−0.028**, `p` **+0.0133**, Δmean **−0.053 bps**; C1–C6 `W` 23.5→28.8 with `L` 22.7→27.8 and `W/L` 1.010→1.038 | `W` +130, `L` +88, `W/L` −0.174, Δmean +11.1 | n_live 2,602 vs 210,691 ambient. **Powered.** SoT §3.1 measured on a second universe |
| R8 | **Arm C's sides carry real information pointing against the registered direction** | side-derangement live **−2.632** vs null +0.382 (sd 1.551), **pct 0.023**, 0 fixed points | −12.221, pct 0.0065 | 2,602 rows, plant resolution ~5 bps. **Powered.** ~1/5 the magnitude — it scales with σ̂ |
| R9 | **`mag_high` is "the bar was large", not the volatility state** | live −3.402 vs comparator −2.068, pct 0.2735; gap **−1.33 bps** | live −11.607 vs −10.704, pct 0.46; gap +0.90 | 1,145 live / 1,457 pool, all 10 deciles supplied. **Powered to ~5 bps** |
| R10 | **C7 — the DESIGN→CONFIRM sign flip is not distinguishable from noise** | 40.99% flip (below chance), 90.3% of flips have overlapping CIs, **1.44%** exceed the two-band MDE, `n`-weighted bands agree to **0.65 bps** | 44.14% / 91.8% / 6.63% / 0.33 bps | 627 native pairs. **Powered** |
| R11 | **C8 — the two weightings agree, and the lean is toward mean-reversion** | row-weighted `p_momo` **0.4939**, symbol-weighted **0.4946**, median \|diff\| **0.0009** | 0.4676 / 0.4699 / 0.0023 | 339 native cells. **Powered** |
| R12 | **The `E[|move|]` / regime objects** — A1 HMM gap, A3 rank IC, A5 clause, D1/D2/D5/D6/D7/D8 | §5: A1 +6.88 bps (55.6% CI-excl-0), A3 IC +0.228 (305 SUPPORTED), A5 **27/27**, D7 `p_stay` **0.9517**, D8 ΔBrier −0.0256 | +18…+48 bps, IC 0.326, 135/135, 0.9365–0.9486, most robust positive object | mostly at target. **Powered.** Magnitudes scale with σ̂ |
| R13 | **E-TOUCH > E-HORIZON > E-CLOSE** | **+0.124 / +0.158 / −0.491 bps** | +0.6…+1.5 / −0.03…+0.69 / −1.2…−3.0 | 100 / 11 / 68 powered cells. **Powered.** ~1/5 the spread |

### 10.2 DOES NOT REPLICATE (and the power statement that qualifies each)

| # | Object | crypto | cTrader | Power statement — **binding** |
|---|---|---|---|---|
| N1 | **C2 shock-conditioned MOMO, the like-for-like `shock_flag` cell** | live **+22.6 bps**, pct 0.95, n 505 | live **−9.383 bps**, pct 0.043, n **290** | **The cTrader control's plant curve reaches only 0.755 at a +10 bps plant.** It could not reliably have detected crypto's +22.6 bps effect at n=290. **This is a WEAK non-replication and per B-5 it says very little.** §7.5 |
| N2 | **C2 on the corrected `P-MOMO` object** | *no crypto counterpart exists* | live −2.414 vs comparator +3.763, pct 0.000, n 1,594 | Better powered, but **not comparable to anything on the crypto side**, and the comparator's own mean is +1.5 to +3.8 depending on construction (§7.3). **Not a replication test at all** |
| N3 | **A2 V-TAIL exceedance lift** | +0.056 (p90) / +0.031 (p95), 90.9% CI-excl-0 | **+0.0095**, only 8.3% CI-excl-0, all 72 WASH | 56 of 72 at target on the *exceedance* metric, but the magnitude is ~6× smaller and mostly inside its CI on 3 instruments. **Reported as a magnitude; NOT a refutation** |
| N4 | **A4 V-CLOCK incremental R²** | −0.032 to −0.0004 (zero to slightly negative) | **+0.0291** — sign reversal | 72 of 108 at target. **A positive in-sample incremental R² on 3 instruments is what over-fitting looks like**; I do not read it as a market statement. §11 T6 |
| N5 | **The counter-outcome does not route — and here it barely exists** | 129 powered cells CI-excluding-zero negative, best flipped +12.93 vs a 13.1 bps floor | **12** negative, **2** positive of 315; best flipped gross **+1.754 bps** vs its own 2.544 bps charge; **0 of 12** clear it when flipped; median flipped net ≈ −0.9 bps | **Powered.** The tails are near the nominal-95% expectation (~8 per tail on 315), so unlike crypto's 1-positive/129-negative asymmetry there is **no enriched tail here at all** — 12 negative and 2 positive is close to what 315 correlated cells would give under a null |

### 10.3 NOT RESOLVABLE (a first-class quantified answer, never a negative)

**2,407 cells carry `band_label_mean == NOT_RESOLVABLE`; 939 carry `UNPOWERED`; 4,330 carry `levers_exhausted`.** Of the 5,888–6,156 signed cells, **only 315 (5.1%) reach the corrected bar.** Predeclared in design §7 — 3 instruments against 25 — and it bound exactly as predicted.

| Item | Not-resolvable state | Required to resolve |
|---|---|---|
| **B3 (native, 159 positive-mean cells)** | **0 of 159** at target; median block MDE **29.22 bps** vs a 1.785 target — **16.4× short**; median n 84 episodes / 61 dates | ~270× the realised `n` at the same variance |
| **arm B `stop` / `time` / `trail`** | **0 of 378** at target on all three | one-tail estimators by construction (`p` 0.06 / 0.51 / 0.84); pooling across 3 symbols does not fix them |
| **arm C at large** | 179 of 5,526 (3.2%) at target | the event-nested conditioner science remains substantially unanswered on this universe |
| **D2, D7, A5** | 0 at target | **definitional** — no bps target attaches to these items; **not** a power failure |
| **C9, D3, D4** | **NOT RUN** — 0 cells | a straddle runner (C9) and a cTrader ZigZag panel (D3/D4). §6.4 |

**Every one of these is a statement about a 3-instrument universe's size, and none of it is evidence against the crypto result.** The reverse also holds: a cTrader cell that fails to replicate a crypto finding is informative only if it is powered — which is why N1/N3/N4 above are qualified as heavily as they are.

---

## 11. Evidence FOR, evidence AGAINST, and threats to validity

### 11.1 Evidence FOR the hypothesis

`HYP-D5` on this universe asks: *do SPDR-018's results — the break-even geometry, the `W/L` mirror, the powered/`NOT_RESOLVABLE` split, and specifically the `C2` shock-MOMO survivor — reproduce on an independent asset class with its own fence?* Evidence FOR is evidence that they do.

1. **The break-even geometry replicates, and more tightly.** `p` 0.0013 from its own gross break-even; gross mean 0.006σ from zero; 0 of 315 clearing net. On a different broker, asset class, fence, band split and volatility scale. (R1, R2)
2. **The `W/L` mirror replicates at R² 0.9746 / slope 0.9656** against crypto's 0.9667 / 0.9408 — an *independent* confirmation of the decisive SPDR-018 finding, on cells that share no data with it. (R3)
3. **The movability test replicates** — 36.4× movement in `W/L`, `p` moving inversely, no improvement in the mean. Crucially, **all five exit geometries ran here** where SPDR-018's cTrader leg ran only `signalflip`; the design's stated reason for existing is discharged. (R4)
4. **The cost-vs-rate decomposition replicates** — 95.8% of the gap is the cost; arm C's rate sits 0.0004 *above* its own gross break-even. (R6)
5. **Selection scaling both sides of the identity replicates from two independent angles** — the ambient-base deltas and the C1–C6 item structure. SoT §3.1 is now measured on two universes. (R7)
6. **Arm C's side-derangement replicates in sign, significance and σ-scaling** (pct 0.023 vs crypto 0.0065, magnitude ~1/5 on a 1/5.6-σ universe) — the strongest single control result in either run. (R8)
7. **Two coverage gaps that were open on crypto are now resolved natively and agree with crypto's resolutions** — C7 (flip rate below chance, bands agree to 0.65 bps `n`-weighted) and C8 (weightings agree to 0.0009). (R10, R11)
8. **The `E[|move|]`/regime layer replicates broadly across arms A and D** — 10 of 12 items, at magnitudes that scale with σ̂. (R12)
9. **The integrity substitute did real work.** TRIPWIRE-2 separates legal from leaky by **412×** (SPDR-018 managed 7.55×), TRIPWIRE-1 holds on 100% of 233,569 rows by my own recomputation, and the cross-universe identity guard reproduces SPDR-018's BTCUSDT cells to **1.14e-13** after catching two genuine defects in this experiment's own code.
10. **`NOT_RESOLVABLE` was delivered as a first-class quantified answer** (2,407 cells, with realised `n`, block MDE, target and shortfall per cell) rather than as silence — exactly as design §7 predeclared.

### 11.2 Evidence AGAINST the hypothesis

1. **The one thing this experiment was built to test did not transport, and cannot be cleanly read either way.** C2 was the *reason* for SPDR-018B (design §1: it "left the run's single surviving live thread with zero external replication"). The answer is neither a replication nor a refutation — the objects are mismatched, the comparator's zero is not zero, its level does not survive independent reconstruction, and the effect lives in the thinnest session. **The experiment's headline purpose is unfulfilled.** (§7.5)
2. **Seven inherited HARD checks do not exist in this run** — determinism (on a run that *was* resumed), golden traces, universe-pin set-equality, bootstrap-path parity, no-local-accounting, spread-never-charged, and the Bybit-holdout assertion on the §5 guard. `run_summary.json` still reports `deviations: []`. (§1.1)
3. **The cost deflator is derived from the subset the precision correction invalidated**, and is not identified: the defensible range spans **0.185 to 0.703** — a factor of 3.8, i.e. ±2× on every net figure. (§2.3)
4. **Median and trimmed-mean CIs are not emitted at all** — worse than crypto's 1% coverage, on a family the design itself flags as fat-tailed. And no `ci_low_seed_range` or `block_sensitivity` sweep is emitted anywhere, so **no CI in this document can be checked for MC- or block-fragility.** (§4)
5. **Power bound hard, as predeclared.** 315 of 6,156 signed cells (5.1%). Arm C: 179 of 5,526 (3.2%). Three of five exit geometries contribute zero powered cells. Per B-5 this is a power statement — but the experiment's ambition was breadth, and on breadth it delivered 5%.
6. **`screen.md`'s §3 and §4 headline tables were never recomputed** after the corrections, and one of its counts (2,388) reproduces under no definition I can construct.
7. **The power flag is not reproducible from the emission.** Recomputing `MDE ≤ target` gives 317 vs 315 (and 2,485 vs 2,401 on the old basis) — ~1–3% of cells carry an undisclosed additional condition.
8. **Two items reverse rather than replicate** (A2 magnitude ~6× smaller and inside its CI; A4 incremental R² positive where crypto measured negative). Both are unpowered-to-weak, so neither is a refutation — but neither is a replication.
9. **`entry_ts` is stamped one bar early on 100% of panel rows.** Harmless here (nothing joins on it), and the *index* is causal — but it is a known-dangerous shape in this programme.
10. **`unit_pin.json` carries Bybit's TRAIN band string on a cTrader measurement** — a carried-over constant of exactly the kind the retarget was built to eliminate.
11. **Multiplicity disclosed, not treated** (operator directive). 7,578 cells and five separately-cut M-3 reads on one object; per L-34 tail counts must be read against the realised testing process.

### 11.3 Threats to validity

| # | Threat | Severity | Assessment |
|---|---|---|---|
| T1 | **Spread not charged, and the whole cost model doubly synthetic** | **High, disclosed, unavoidable** | Every net figure overstates. All conclusions here become *more* negative once spread is charged, so it cannot flip a negative to a positive. But it is the single most decision-relevant unknown, and the per-symbol spread pin is already a declared blocking prerequisite. **Gross is primary throughout for exactly this reason.** |
| T2 | **Cost deflator unidentified (0.185–0.703)** | **High (inferential)** | Quantified in §2.3. Neutralised for the headline: 0 of 315 clear net at *any* charge above 1.39 bps, and the best cell is +1.39. Not neutralised for any *magnitude* comparison between universes' net figures. |
| T3 | **3 instruments — power bound as predeclared** | **High, by design** | 315 of 6,156 signed cells. Per B-5 and design §7 this is never evidence against crypto. It does mean N1/N3/N4 carry very little weight, and it means the *replications* (R1–R13) are the load-bearing content. |
| T4 | **C2 comparator is not a neutral yardstick** | **High** | §7.4: its own mean runs +0.97 → +12.05 bps across sessions; the Asia null lies entirely above zero, so a zero-effect arm reads pct 0.000; the Asia plant curve is blind to +20 bps upward. **Fully governs the §7.5 ruling.** |
| T5 | **Comparator level not reproducible** | **High** | My independent rebuild shifts the comparator 2.3–3.4 bps and **flips the `P-MR` read** (0.0665 → 0.826). Any M-3 percentile in this run should be treated as construction-dependent. |
| T6 | **In-sample R² and IC on 3 instruments (A3, A4)** | Medium | A4's sign reversal is the visible symptom. No held-back fold exists in a TRAIN-only lane, so A3's IC +0.228 and A4's +0.029 are both in-sample. A3 replicates a banked crypto result and is corroborated; A4 does not and should not be read as a market statement. |
| T7 | **Seven un-run HARD checks; determinism absent on a resumed run** | Medium (procedural) | §1.1. Mitigated by TRIPWIRE-1+2 both holding (412× separation), the identity guard at 1e-13, and the negative direction of the result. Ruling requested. |
| T8 | **Median/trimmed CIs and all fragility diagnostics absent** | Medium | §4. Matters most for the two positive CI-excluding-zero cells (CI_low 0.146 / 0.118 bps) and for the `trail` population's 32 bps mean-vs-median gap. |
| T9 | **Pooling validity** — 207 of 315 powered cells are `__CTRADER_POOLED__` | Medium | Partly checked: `edge` is negative in **all three** named symbols *and* in the pooled cells, so the pooled sign is not a Simpson artifact. But per-symbol gross means span 0.45 bps, and with only 3 symbols homogeneity is weakly established. Design §8's "POOLED: disclosure-only unless homogeneity is shown" is the right rule and I applied it. |
| T10 | **Column-name trap** (`net_*` is *not* net-of-cost; `gross_p_be_net` is the real net break-even) | Low but sharp | Would silently mis-state `p_be_net` by ~0.09. Every figure here uses `gross_*`. |
| T11 | **`levers_exhausted` semantics** — 4,330 cells; means "levers applied", not "levers failed" | Low | Do not read it as a power verdict. |
| T12 | **Flat legs excluded from `p`** | Low | Quantified: median `p_flat` 0.0000, p95 0.0036, max 0.3333; identity-vs-`gross_mean` p99 gap 0.042 bps. Immaterial here (crypto's was larger). Still: charge flat legs their cost in any 019/020 budget. |
| T13 | **`entry_ts` off by one bar; `unit_pin.json` carries Bybit's band string** | Low | Neither affects a number. Both are the class of defect that has previously cost this programme a full re-run. |

---

## 12. Open threads — resolved here, and not resolved

**Resolved in this pass:**

- the corrected `(p, W, L)` picture on the 315 (§3), with the identity re-derived to **8.53e-14 bps** and `p_be`/`p_be_net`/`edge` reconstructed from `W`,`L`,`cost` to **exactly 0.0**;
- the net-clearing rate: **0 of 315**, robust at both charges and at any charge above **1.39 bps** (§2.3);
- the `W/L` mirror: **R² 0.9746 / slope 0.9656 — it replicates**, and the screen's "the mirror fails here" reasoning is no longer needed (§2.4, R3);
- the **cost-deflator circularity** — its basis identified exactly (median W + median L on the *absolute*-powered subset) and its defensible range bounded at 0.185–0.703 (§2.3) — **nobody had flagged this**;
- the **C2 comparator's non-neutrality** — the null's own mean by session, the Asia null lying entirely above zero, and the Asia plant curve blind to +20 bps (§7.4) — **nobody had flagged this**;
- **C2 rebuilt independently**, live values reproduced exactly and the comparator level shown to be construction-dependent to the point of flipping `P-MR` (§7.3);
- the ten `trail` cells verified exactly (+7.13…+22.97 against 116 cells at −27.610) **and shown to have vanished** under the corrected bar (§8.1);
- the selection effect's **direction** shown to be skew-dependent rather than fixed (§8.3) — a refinement of the candidate finding;
- the **seven un-run inherited HARD checks** enumerated by name (§1.1);
- C7 / C8 / native B3 verified from their emitted tables, with B3's substantive answer supplied (**0 of 159 at target, 16.4× short**);
- arms A and D reported item by item, with A2 and A4 identified as the two non-replications;
- the stale `screen.md` figures replaced one by one (§2.4).

**Could not resolve — proposals for the operator, not actions I took:**

| # | Thread | Why it needs new work |
|---|---|---|
| **P1** | **Is `shock_flag` real?** Unchanged from SPDR-018 §14 P1 and now sharper: re-run M-3 at `n` in the thousands on the **powered crypto grid strata**, with multiplicity treated **and with the comparator's own mean reported alongside every percentile**. 018B shows a percentile is uninterpretable without it. **The highest-value single follow-up in either run.** |
| **P2** | **Median and trimmed-mean CIs** on the 315 powered cells and on the `trail`/`stop` populations. Cheap, in-scope, and it is the only way to size the 32 bps mean-vs-median gap that produced the §8 artifact. |
| **P3** | **`ci_low_seed_range` + `block_sensitivity` sweep** on every CI carrying a read — required by INFR-004/L-20 and emitted nowhere in this run. |
| **P4** | **Determinism** (one sequential pass) and a **Bybit-holdout assertion on the §5 guard's own reads**. Both cheap; the second is the only genuine residual Phase-0 exposure. |
| **P5** | **The per-symbol spread pin** (SoT §3 axis E, blocking, unresolved). Until it exists, no net figure on this universe means anything, and the cost deflator cannot be pinned. |
| **P6** | **The Asia magnitude × shock interaction** (§7.5b) — momentum continuation on large no-shock moves runs ~+10 bps in Asia and ~0 in EU, on 162–184 rows. **The only genuinely new lead in this run.** It needs its own powering attempt and a session-composition control before it is anything at all. |
| **P7** | **C9 / D3 / D4 on cTrader** — a straddle runner and a cTrader ZigZag panel. D4's `ridge_cont` K=5 was the strongest D3/D4 object on crypto and its cTrader status is entirely unknown. |
| **P8** | **Why is the power flag not reproducible from `gross_block_mde_mean_bps`?** 2 cells on the σ basis, 84 on the absolute. Small, but it means the emission cannot be independently regenerated. |

---

## 13. RECOMMENDED verdict (non-final — the operator decides)

### 13.1 On `HYP-D5` as posed by `design.md` §1

> ### **PARTIALLY SUPPORTED — the structural result replicates convincingly; the specific replication target does not resolve in either direction.**

The design asked four things. Three replicate; the fourth is the one the experiment was built for and it comes back unresolved.

| Design §1 question | Answer |
|---|---|
| Does the **break-even geometry** reproduce? | **YES, and more tightly.** `p` 0.4868 vs `p_be` 0.4855 (gap 0.0013); gross mean −0.080 bps = 0.006σ against crypto's 0.016σ; **0 of 315 clear net**, at any charge above 1.39 bps |
| Does the **`W/L` mirror** reproduce? | **YES.** R² **0.9746**, slope **0.9656** against crypto's 0.9667 / 0.9408. 93% of powered cells cannot be distinguished from the driftless mirror. And with all five exit geometries running (which SPDR-018's cTrader leg could not do), `W/L` moves **36.4×** while `p` moves inversely and the mean does not improve |
| Does the **powered / `NOT_RESOLVABLE` split** reproduce? | **YES in structure, and it bound harder** — 315 of 6,156 signed (5.1%); 2,407 `NOT_RESOLVABLE`; three of five exit geometries at zero powered cells. Exactly as design §7 predeclared for 3 instruments against 25. **Counts are not comparable to SPDR-018's** (§2.2) |
| Does the **`C2` shock-MOMO survivor** reproduce? | **UNRESOLVED — not replicated and not refuted.** §7.5 |

The three pieces of evidence that most drive this:

1. **The `W/L` mirror at R² 0.9746 on data sharing nothing with SPDR-018** — the decisive crypto finding, independently confirmed. The screen's earlier "the mirror fails here" was an artifact of the non-portable precision bar.
2. **0 of 315 powered cells clear net break-even, with the best cell at +1.389 bps against a 2.43 bps charge** — robust at both charges and across the entire defensible deflator range, and gross-primary.
3. **The cross-universe identity guard at 1.14e-13 after catching two real defects** — without it, an arm-B "non-replication" produced by this experiment's own code would have been reported as an asset-class fact on a universe where a null was the expected outcome.

**What would change this verdict:** a determinism run showing the parallel and sequential paths differ (which would invalidate the emission); or a C2 re-run with a properly matched object and a disclosed comparator mean that put the cTrader shock-MOMO effect *above* its comparator after all.

### 13.2 The `(p, W, L, W/L, edge)` picture the mid-checkpoint reflection needs

**For parameterising any later capture-geometry work. cTrader is credibility, never power, and never pooled into crypto `n`.**

```
CTRADER (EURUSD, XAUUSD, USTEC) — 315 powered signed cells, TRAIN only, GROSS PRIMARY
  p          = 0.4868      p_be (gross) = 0.4855      gap to own gross break-even = +0.0013
  W          = 24.66 bps   L            = 20.99 bps   W/L = 1.0597
  p_be_net   = 0.5334      edge (p - p_be_net) = -0.0544
  gross mean = -0.080 bps  (= 0.006 sigma, sigma-hat = 13.03 bps)
  net mean   = -2.500 bps  (DOUBLY SYNTHETIC charge, median 2.43 bps, spread NOT charged)
  gross median = -0.560    gross trimmed-10 = -0.573     (all three agree here, unlike crypto)
  clears gross break-even = 129/315 (41.0%)   clears net break-even = 0/315 (0.0%)
  best single powered cell = +1.389 bps gross vs its own 2.43 bps charge  (short by 1.04 bps)
  gap decomposition: rate term +0.0023 | cost term +0.0529 -> cost is 95.8% of the gap
  arm B: p 0.3604  W/L 1.7457  p_be 0.3642  p_be_net 0.4462  edge -0.0820  gross -0.148
  arm C: p 0.4950  W/L 1.0167  p_be 0.4959  p_be_net 0.5430  edge -0.0489  gross +0.018
  W/L movability (all 630 arm-B signed cells, exit geometry as the lever):
      trail  p 0.840  W/L 0.274  |  time  p 0.509  W/L 0.994  |  combined p 0.393 W/L 1.498
      signalflip p 0.343 W/L 1.840 | stop p 0.0625 W/L 9.975      -> 36.4x, p moves inversely
      gross median across those modes: +7.6 / +0.8 / -0.005 / -0.22 / -10.4 bps
      (trail's +7.6 median sits against a -24.3 MEAN and a -1,002 bps min: an unfired tail)
  mirror fit: log(W/L) = -0.0030 + 0.9656 * log((1-p)/p),  R2 0.9746,  sd(log R) 0.0607
              93.0% of powered cells cannot be distinguished from the driftless mirror
  edge is NEGATIVE in every named symbol: USTEC -0.054, XAUUSD -0.091, EURUSD -0.106
```

**Three constraints this picture places on any 019/020 design:**

1. **The joint sits at break-even on two independent universes.** `p − p_be` is +0.0013 here and +0.0138 on crypto; the gap to *net* break-even is 96% cost on this universe and 91% on crypto. SoT §1.1's gate — "a capture design cannot manufacture expectancy out of a joint `(p, W, L)` that sits at break-even" — now binds on two asset classes. **Any 019/020 proposal must name the mechanism that puts `R` above 1, because five distinct exit devices spanning 36× of `W/L` did not, on either universe.**
2. **Do not parameterise off a powered subset's magnitudes without the §8.4 three-number check.** The gate halves the payoff scale (46 vs 106 bps), and on arm B it discards the positive cells (28.7% vs 51.8% positive). The ten `+7…+23 bps` `trail` cells are the worked example of what happens otherwise.
3. **Do not state any threshold in absolute bps across a universe boundary.** σ̂ is 73.00 on crypto and 13.03 here. A 10 bps bar is 0.137σ on one and 0.767σ on the other, and carrying it unchanged silently loosened it 5.6× and produced three wrong headline numbers.

### 13.3 Inputs to the checkpoint decision (I take no disposition)

- **The zero-line / mirror result is now replicated across asset classes.** SoT §10 end-state 1 is where this evidence points, and 018B strengthens that pointing considerably — the mirror fit is *tighter* here than on crypto, and the cost-vs-rate decomposition is *more* extreme (95.8% vs 90.7%).
- **But the checkpoint still should not be closed as end-state 1, and 018B does not change the two reasons it could not be** on crypto: (a) the **C2 thread remains open** — 018B neither replicated nor refuted it, and its own C2 evidence is too weak to close anything; and (b) **`NOT_RESOLVABLE` remains large on the conditional-direction objects** — 179 of 5,526 arm-C cells powered here, 3,559 unresolved on crypto with 55% in C3. **Closing over those would read UNPOWERED as a negative, which B-5 forbids and which is precisely the error checkpoint-017 was closed to avoid.**
- **End-state 3 (a powered counter-outcome that routes) is checked and not satisfied** — 12 negative CI-excluding-zero cells, best flipped gross +1.754 bps against its own 2.544 bps charge, 0 of 12 clearing when flipped. And unlike crypto, the tail counts (12 negative / 2 positive of 315) are near the nominal-95% expectation, so there is no enriched tail to route.
- **End-state 2 requires something to clear `p_be_net`.** Nothing does, on either universe.
- **The shape I would suggest** (entirely the operator's call): resolve **P4** (cheap, closes Phase 0), **P2/P3** (cheap, and they decide whether "at gross break-even" survives contact with the median), and **P5** — the spread pin, already a declared blocking prerequisite — before taking the end-state decision. **P1** is the only probe that can settle C2, and **P6** is the one new lead worth a look. A capture experiment framed as **apparatus or characterisation** is consistent with everything measured on both universes; as a tradability test it is not.

---

**Final verdict and disposition are the operator's.** Suggested probes: push on **P1** if you want to know whether the crypto C2 thread is real (and demand the comparator's own mean, not just its percentile); **P2/P3** if you want to know whether the near-break-even framing survives the median and a seed battery; **P5** if you want any net figure in this document to mean anything. To attack §3's conclusion, the place to do it is the free residual `log R` (sd 0.0607, median −0.0098) — ask whether any exit geometry *outside* these five could hold `R > 1`, and demand the mechanism rather than the search. To attack §7.5, build a C2 comparator whose null mean is zero by construction and show the reversal survives it.

**No tradability, deployability, cost-complete, family-status, graduation or XENA claim is made or implied by this document. No disposition is taken.**

---

# ADDENDUM — added by the orchestrator AFTER the analyst's pass (2026-07-26)

This section is **not** the analyst's text. It records one factual error found by an independent
adversarial audit of the downstream documentation, which re-derived every figure from `results/`.

## The §7.5 C2 ruling rests on four reasons; **reason 3 is false.**

§7.5 states that the like-for-like `shock_flag` cell (n = 290) "could not reliably have detected
crypto's +22.6 bps effect", citing a plant curve that reaches only percentile 0.755 at a +10 bps
plant. **The +10 bps point is quoted correctly, but the curve does not stop there.** From
`results/controls.json`, `magnitude_matched.shock_flag.plant_curve`:

| plant | +5 bps | +10 bps | **+20 bps** | **+40 bps** |
|---|---|---|---|---|
| percentile | 0.285 | 0.755 | **1.000** | **1.000** |

The control's resolution is therefore **10–20 bps, not ">20 bps"**, and an effect of crypto's
magnitude (+22.6) **would** have been detected. The live value is **−9.383 bps at percentile 0.043**.

**Consequence for the ruling.** The correct reading is the *opposite* of what §7.5 argues on this
point: the cTrader control **was** powered for an effect of crypto's size and measured the **opposite
sign**. This is a **powered non-replication on that cell** — it strengthens "not replicated" and
**removes one of the four supports for "not refuted"**.

**The ruling itself is not withdrawn**, because reasons 1, 2 and 4 are unaffected and were verified:
the comparator's own mean runs +0.97 (EU) → +3.46 (US) → +12.05 bps (Asia) with the Asia null lying
entirely above zero; the effect vanishes in EU (+0.62, pct 0.443); and an independent rebuild shifts
the comparator 2.3–3.4 bps and flips the `P-MR` read (0.0665 → 0.826). What changes is the **balance**:
"not replicated" is now better supported than this document presents it, and the operator should treat
"not refuted" as resting on three legs rather than four. The limits that remain are n = 290 on a single
cell, a one-sided p ≈ 0.04, and a magnitude (−9.4) far smaller than crypto's +22.6.

**No other figure in this document was changed.** The audit re-derived ~110 of its numbers and the
great majority matched to the last quoted digit. Two other items are recorded against it: §9.2's
"`entry_ts == event_ts` on 100% of panel rows" is actually **96.26%** (224,830 of 233,569), and the
C7 "1.44% exceed the two-band MDE" uses a *sum* of the two band MDEs where SPDR-018's comparable
6.63% uses quadrature — on a common basis the two universes read 6.63% vs 7.02%, so C7's conclusion
holds but the apparent 5× improvement does not exist.

**The analyst's verdict (`HYP-D5` PARTIALLY SUPPORTED) stands, and the disposition remains the
operator's.**
