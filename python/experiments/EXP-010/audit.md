# EXP-010 — CF-MR-003 CONC-1 Track 1 · AUDIT (uncapped)

**Scope:** 5 distinct S5_SPREAD exec-1h cells (AUDUSD, GBPUSD, NZDUSD [FX_MAJORS], US2000, US500 [INDICES]).
**Provisional outcome:** UNPOWERED / NOT-TRADABLE (0/5 powered, 0 admit, tripwire PASS-but-vacuous).
**Audit verdict:** **PASS — outcome stands (UNPOWERED / NOT-TRADABLE), 0 Critical.** 1 Medium + 2 Low findings,
all shown non-verdict-material. Booking allowed as a TRAIN UNPOWERED/NOT-TRADABLE record (no tradability
claim, holdout sealed). Numeric reproduction here is paired with the causal-provenance pass below (L-01).

---

## 1. Scope & governance compliance

| Check | Result |
|---|---|
| Member set = 5 EXP-009-admitted distinct S5 exec-1h cells (P-02, no re-screen) | ✓ AUDUSD/GBPUSD/NZDUSD/US2000/US500 |
| Frozen referee untouched (L-12) | ✓ `gate_stack_pstar` + `adaptive_row` called unedited; no referee module diff |
| Price-primary in-engine (L-01), no vectorized Python backtest | ✓ edge in `StrategyHost/CrossDomainMrLimitModel.cs`; Python only ingests `data/strategy_runs/EXP-010/` |
| Holdout sealed / 0 counted reads / 1 slot / first-49% fence | ✓ see §2 (0 emitted rows at/after `AnalysisEndUtc`) |
| Multiplicity = phase Holm over 5 distinct cells | ✓ Holm(5) on bootstrap p; degenerate 1D/4h-anchor duplicate correctly collapsed |

---

## 2. Data handling / fence (holdout discipline)

Per-cell `positions.parquet` vs `run_metadata.analysis_end_utc`:

| Cell | rows at/after fence | last emitted CloseTime | AnalysisEndUtc |
|---|---|---|---|
| AUDUSD | **0** | 2023-11-21 03:00 | 2023-11-21T03:29 |
| GBPUSD | **0** | 2023-11-21 20:00 | 2023-11-21T20:10 |
| NZDUSD | **0** | 2023-11-21 07:00 | 2023-11-21T07:19 |
| US2000 | **0** | 2023-11-20 15:00 | 2023-11-20T15:47 |
| US500  | **0** | 2023-11-22 02:00 | 2023-11-22T05:06 |

Holdout + analysis-TEST band never emitted. Fence = first-49% (`int(int(N·0.7)·0.7)`) ✓. Real emitted OHLC only;
open-to-open assembly; timestamp-aligned (`SourceCloseTime`), never bar index ✓.

---

## 3. Verdict Forensics

### 3.1 Per-stratum re-derivation (independent recompute from emitted positions)
Re-derived `realized_bps` (entry+exit fills + MTM, cost = `ROUND_TRIP_COST_BPS_17[sym]["1h"]`) → `gate_stack_pstar`:

| Cell | eff_n | train_up/dn | test_up/dn | **min_state** | n_epi | net bps/active | ci_low | L1 | L3 |
|---|---|---|---|---|---|---|---|---|---|
| AUDUSD | 5232 | 29/25 | 7/3 | **3** | 10 | −0.26 | −0.19 | ✗ | FAIL |
| GBPUSD | 5254 | 38/28 | 12/11 | **11** | 23 | +0.10 | −0.04 | ✗ | FAIL |
| NZDUSD | 5230 | 32/19 | 15/7 | **7** | 22 | −0.26 | −0.11 | ✗ | FAIL |
| US2000 | 5034 | 36/29 | 11/7 | **7** | 18 | −0.70 | −0.56 | ✗ | FAIL |
| US500  | 4720 | 24/47 | 17/15 | **15** | 32 | −0.61 | −0.16 | ✗ | FAIL |

**L1=False is GENUINE low power, not a bug.** 1h floor = `min_effective_n=60` (all cells pass: eff_n≈5000) **AND
`min_state_count=20`** (all cells FAIL: min_state 3/11/7/7/15 < 20). Binding constraint = too few reversion
**episodes** per direction/split, exactly the design-anticipated "low-turnover limit fills thin episodes →
UNPOWERED."

### 3.2 Masking check (L-03)
No pooled headline is used as the verdict; all 5 cells reported per-stratum. Per-cell picture is homogeneous
(all UNPOWERED, all net ci_low ≤ 0) — no cell is masked by aggregation. The lone positive point estimate
(GBPUSD +0.10 bps) has ci_low = −0.04 (not separated) and is UNPOWERED. No heterogeneity hidden.

### 3.3 Mechanism
The concretized form-2 limit strategy fires only where VR<0.9 ∧ HL∈(0,48] ∧ |z|≥2 co-occur — a rare
conjunction → 77–157 entries over ~17k bars → **10–32 episodes/cell**, which after the 70/30 referee split
leaves 3–17 episodes in the smallest direction/split bucket, below the 20 floor. Net point estimates are
~null-to-negative (only GBPUSD marginally positive, within noise). **Availability (EXP-009) does not survive to
net** — consistent with the honest LOW prior and CF-MR-002's exoneration.

### 3.4 Gate-shape check
The referee's L1 min_state_count is a **power/readiness** floor, not an effect-shape gate; it correctly reports
UNPOWERED (cannot see an effect) rather than EVIDENCE-AGAINST. This is the right instrument: the finding is
"too few episodes to test," properly distinguished from "tested and refuted." No gate retro-edit. Note for the
interpreter: this is UNPOWERED, **not** a positive refutation — the net sign is suggestive-negative but unpowered.

---

## 4. Causal-Provenance & Leak Pass (L-01) — independent of the numbers

### 4.1 Provenance trace (decide-before-fold)
`CrossDomainMrLimitModel.OnBar(bar_t)`: all decisions read `_rested*` (Anchor/Dev/Z/Vr/Hl/Beta/Sigma) that were
frozen by the **previous** bar's `FoldAndRefresh` → values **through t−1**. `BuildPosition` (emission) runs
**before** `FoldAndRefresh(bar_t)`, so the emitted provenance columns at row t are the through-t−1 decision
inputs (verified: the parity in §6 aligns emitted(t) ↔ reference(t−1)). Entry/exit limits rest from t−1 and fill
intrabar on `bar.High`/`bar.Low` (a resting limit filling within bar t is `≤ t`, live-actable — not look-ahead).
The forming bar's own Close is folded into state **only after** emission. No verdict-bearing value reads `> t`.
**No `rct[di]`-style same-bar-close leak** (the P-05/L-01 pattern is absent — fills key off the resting limit
price + the bar range, not the bar's own close).

### 4.2 Fill executability (smoke-caught bug + fix, verified)
Smoke run #1 exposed 41/77 AUDUSD entry fills **outside** the emitting bar's [Low,High] (a limit the bar gapped
through was filled at the limit price — non-executable / over-favourable). Fixed to **gap-through fill at the
Open** (`CrossDomainMrLimitModel.cs` entry + exit legs). Re-verified on all 5 live cells:

| Cell | entry fills (oob) | exit fills (oob) |
|---|---|---|
| AUDUSD | 77 (**0**) | 77 (0) |
| GBPUSD | 116 (**0**) | 115 (0) |
| NZDUSD | 89 (**0**) | 89 (0) |
| US2000 | 119 (**0**) | 119 (0) |
| US500  | 157 (**0**) | 156 (0) |

All fills within the traded range → executable (L-02 binding-leg discipline: both limit legs charged full RT
`cost_bps`; the market fallback pays too). (GBPUSD/US500: exit = entry − 1 — one position still open at the
fence, benign; the assembler MTM-holds it with no exit truncation.)

### 4.3 Leak tripwire — **shipped, PASS, but VACUOUS/non-informative** (⚠ recorded)
The T1 future-destroy (`EXP-010-shuffle`, `--BasketPhaseShiftHours=2000` decorrelating the basket from the
traded price) ran on all 5 cells. `surviving-under-shuffle = []` → PASS by the letter. **But the tripwire is
non-informative here:** the LIVE edge is already null/negative (nothing to collapse), and the phase-shifted
control is in fact *more* positive on 4/5 cells (AUDUSD +1983 vs −656; NZDUSD +1138 vs −702; US2000 +1112 vs
−2140; US500 +750 vs −2116 bps) — all UNPOWERED noise. **A tripwire can only demonstrate leak-resistance when
there is a live edge to destroy; with a null live edge it is vacuously satisfied.** ⇒ **leak-resistance of this
vehicle remains UNTESTED**; it neither indicates nor rules out a leak. This is acceptable for an UNPOWERED /
NOT-TRADABLE verdict (no positive claim to protect), but the tripwire MUST be exercised on any future powered
positive arm before a tradability claim.

### 4.4 Shared-module contract
`SignalPositionRecord` gained 6 provenance fields (EntryFillPrice, Anchor, Dev, Z, Vr, Hl, Beta), all
**NaN-default**; `StrategyRunParquetWriter` positions schema extended accordingly. Other models
(MA/AVWAP/Donchian/RSI) construct with named args ending at `ExitFillPrice` → unaffected (build clean, 0
warnings). No shared-module causal contract broken.

### 4.5 Price-primary check
Edge (anchor/β/VR/HL/z/limit fills) computed in the cTrader engine; `data/strategy_runs/EXP-010/` emitted under
the fence; Python `run_experiment.py` only ingests/assembles/adjudicates. **No vectorized Python price-strategy
backtest.** ✓

---

## 5. Operationalizations scrutinized (developer-flagged, design-implicit)

| # | Choice | Assessment |
|---|---|---|
| a | Entry-limit price = band-edge `exp(a±Z*σ)` | Reasonable mapping of "z=±2 band → price"; entries executable (§4.2). Non-material to UNPOWERED. |
| b | Mate read = causal carry-forward (most-recent CloseTime ≤ t) | **Deviates from design §4 / substrate "joined by CloseTime" (exact)** → contributes to the §6 fidelity gap. See F-1. |
| c | Gap-through fill fix | Correct + verified (§4.2). Resolves the smoke bug. |
| d | Tripwire = phase-shift, not per-bar block shuffle | Valid cross-domain-structure destroyer; but vacuous here (§4.3). |
| e | Fence = first-49% | Verified sealed (§2). |

---

## 6. C# anchor numerical parity (was UNVERIFIED) — Python `cross_domain_mr` reconstruction, AUDUSD

Reconstructed the exec-grid-β vehicle in Python from the mate 1h bars (`build_domain_bars`, `rolling_beta_fit`
W_Z=200, `rolling_std_z`), aligned emitted(t) ↔ reference(t−1) (the correct causal alignment; the 1-bar shift
was tested and does **not** explain the gap):

| Series | corr | median &#124;Δ&#124; | note |
|---|---|---|---|
| **Anchor** (price) | **0.990** | 0.0023 (~0.35% of price) | β regression structurally CORRECT |
| Dev (residual) | 0.727 | 0.0033 | tiny residual, hypersensitive |
| Z (extreme selector) | 0.669 | 0.611 | 80.6% sign agreement; \|z\|≥2 sets Jaccard **0.30** |

**Diagnosis:** the anchor *level* replicates tightly (β/α correct), but `dev = logp − a` is a small difference of
near-equal large numbers → hypersensitive to per-bar price differences, which come from two identified,
defensible sources: (1) **cTrader-native 1h bars** (real execution prices) vs Python **m1-aggregated** bars;
(2) **basket carry-forward** (≤t) vs **exact-CloseTime join**. Not a formula bug (anchor corr 0.99; both |z|≥2
counts similar magnitude, 1875 vs 2529). ⇒ **F-1 (Medium, non-blocking).**

---

## 7. Findings

### F-1 — Concretized vehicle is a LOOSE (not tight) replica of the screened availability vehicle — **Warning / Medium, non-blocking**
The in-engine z-selector diverges from `cross_domain_mr` (dev corr 0.73, z corr 0.67, |z|≥2 Jaccard 0.30),
driven by cTrader-native-bar vs m1-aggregation + basket carry-forward vs exact-join (F-1a: item (b) also
deviates from the design §4 "joined by CloseTime" wording).
**Materiality (why non-blocking):** does NOT move the UNPOWERED verdict — power fails on **episode sparsity**
(min_state 3–17 < 20), and the reference vehicle is *equally* sparse (|z|≥2 count 2529 ≈ emitted 1875; the VR∧HL
conjunction thins both to a handful of episodes). Net is null/negative and there is no basis for the ref-z to
manufacture a positive edge. The selector difference changes *which* bars fire, not *how many* episodes clear
the floor, nor the sign of the (unpowered) net. **Blocking condition for the future:** if any arm (T2a/T2b, or a
re-powered T1) yields a **powered positive**, this fidelity gap MUST be closed (reconcile the basket
construction to exact-join or justify carry-forward; document the cTrader-bar vs m1 source) before any
tradability claim — there, which extremes fire is verdict-bearing.

### F-2 — Leak tripwire vacuous on a null edge — **Warning / Low, non-blocking**
§4.3. Leak-resistance UNTESTED. Non-material to UNPOWERED (no positive claim); must be exercised on any future
powered positive.

### F-3 — One open position at the fence on GBPUSD/US500 — **Info / Low**
exit_fills = entry_fills − 1; a position opened but not yet closed at the first-49% cut. Assembler MTM-holds it
(no exit truncation, no forward leak). Immaterial to the per-bar realized series / verdict.

---

## 8. Verdict

**PASS — 0 Critical. Outcome UNPOWERED / NOT-TRADABLE stands and is correctly derived** (L1 power failure is
genuine; fence sealed; fills executable; provenance causal; frozen referee untouched; price-primary in-engine).
Two Warnings (F-1 vehicle fidelity, F-2 vacuous tripwire) are non-verdict-material for an UNPOWERED result but
are **binding preconditions** for any future powered-positive booking. No fix + re-execute required for this
verdict. → Stage 5 (Document): record TRAIN UNPOWERED/NOT-TRADABLE; family retained; terminal-branch prior
reinforced; carry F-1/F-2 as tradability-gate debt; holdout + counted reads untouched.
