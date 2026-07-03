# EXP-013 — CF-MR-004/HYP-001: full-strategy availability + tradability screen

**Family:** CF-MR-004 (REGISTERED, G0 ratified) · **Phase:** 004 · **Type:** full-strategy screen (net + availability, TRAIN)
**Classification:** **PRICE-PRIMARY** (in-engine; L-01/P-09) · **Slots/reads:** 0 candidate slots (first probe), **0
counted TEST reads** · **Holdout:** final-30% sealed; emit over **first-49% TRAIN sub-split only** · Frozen
referee — **never tuned** (L-12).

## 0. Mandate

G0 ratified full-strategy-first (operator mandate): the complete precalc limit-order cross-instrument MR
strategy runs in cTrader from the start. Availability (gross) + tradability (net) are measured from one
emission. Honest prior: **LOW** — all prior MR families closed (CF-MR-001 refuted, CF-MR-002 exonerated,
CF-MR-003 retired); cost/capture veto is the structural risk. From-scratch family-specific code (L-13);
multi-symbol StrategyHost = reusable infra.

## 1. Falsifiable question (one)

*On the 4h anchor domain, does the complete precalc limit-order cross-instrument MR strategy (4 series: S5
redo + S6/S7/S8; entry at |z|≥2 extreme, exit at anchor mean, set-and-forget per 4h bar, horizon fallback)
produce (a) a gross reversion edge beyond a dislocation-matched matched-random control (availability) AND
(b) a net-positive per-stratum edge under the frozen 4h referee (tradability) — or not?*

## 2. Price-primary classification — PRICE-PRIMARY (confirmed)

Generates signals/entries/positions from price → cTrader in-engine via **NATIVE pending orders**
(`Mode=NativeOrders`). The robot places real cTrader limit orders; cTrader's **m1 backtester owns fill
resolution** — no self-adjudicated fills on aggregated bars (the Route-A faithful build; the earlier
self-adjudicating 4h-OHLC model was a vectorized residue and was removed). Python is analysis-only on
emitted `data/strategy_runs/EXP-013*/` parquet with **engine-realized** fill prices. No vectorized Python
edge/outcome module (L-01/P-09). The frozen referee (§10.3a q\*=0.75 + E6 `referee_pstar.gate_stack_pstar`,
domain=4h) adjudicates the emitted per-bar realized net series.

## 3. Data scope

| Field | Value |
|---|---|
| Universe | INFR-003 5-year, 16 instruments (VAL-003 minus DE30) |
| Traded instruments | FX majors (7: EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD) + equity indices (4: USTEC, US500, US2000, JP225) = **11 traded** |
| Basket/pair peers | FX: other 6 majors per class basket; EURJPY/GBPJPY/AUDJPY available for JPY-cross pairs. Indices: other 3 per class basket. XAUUSD/BTCUSD standalone (not in baskets — no natural cross-instrument anchor). |
| Anchor domain | **4h only** (frozen referee supports 4h; 1D deferred — needs referee extension prerequisite like E7/EXP-011 was for 15m). No lower-domain (operator mandate). |
| Time range | Full 5-year; first-70% analysis slice; **first-49% TRAIN sub-split** (`int(int(total·0.7)·0.7)`, the TRAIN fence — seals the analysis-TEST band too; matches EXP-010 §10). |
| Global holdout | Final-30% **never loaded/inspected**. `AnalysisEndUtc` = each file's first-49% cutoff. |
| Stratum | `(series, instrument-or-pair, 4h)`; per-stratum binding (L-03); pooled = disclosure-only. |
| Exclusions | No lower-domain processing; no 1D/1h/15m domain (this EXP); no TEST read; no holdout release. S1–S4 (single-instrument) not in scope. `/REENTRY /TARGET=opposite /EXIT=plane /DIRECTION=trend` deferred.

## 4. Anchor series + execution model

### Series definitions (all ≤ t-1, on 4h bars, from-scratch C# code)

| Series | Construction | Invertible entry/exit price | Cells |
|---|---|---|---|
| **S5 (REDO)** | `d = log P^A − (β·basket + α)`; basket = equal-weight log(class-mates minus self); `(β,α)` = OLS on trailing W_a=200 4h bars | `P^A = basket^β · e^(α + d)` | 7 FX + 4 idx = **11** |
| **S6 (NEW)** | `S = log P^A − β·log P^B`; β **fixed=1** (simple log-price diff) | `P^A = P_B · e^S` | 5 pairs: EURUSD/GBPUSD, AUDUSD/NZDUSD, USDCHF/USDCAD, USTEC/US500, US500/US2000 = **5** |
| **S7 (NEW)** | `S = log P^A − Σ wᵢ·log Pᵢ`; weights **fixed equal** (1/n each) | `P^A = (Π Pᵢ^wᵢ) · e^S` | 7 FX + 4 idx = **11** |
| **S8 (NEW)** | `S = (log P^A − β·log P^B) − Median_W(·)`; β=1, W=60 4h-bar rolling median | `P^A = P_B · e^(S + C_t)` | Same 5 pairs as S6 = **5** |

**Total: 32 cells across 4 series × 1 domain (4h).**

### Extreme + entry/exit — RESTING BRACKET (≤ t-1, native orders; operator-ratified 2026-07-01)

**Entry = a resting bracket, no z pre-gate.** Each 4h bar (when flat), from ≤ t-1 anchor/σ, the robot
arms BOTH band limits and lets price reach them; the band level **is** the trigger. This captures intrabar
excursions that spike to ±2σ and revert before the 4h close — the intrabar reversion the renewal exists to
capture (`post-exps-reflection.md` §1). z is emitted as **provenance only** (informative-not-gating, L-12).
This replaces the design's original `|z_t|≥2`-then-place-limit rule, which was internally incoherent (if the
close already prints |z|≥2 the band is already breached) and could only arm after the excursion printed.

- **σ / anchor:** `σ = std(S, W_Z)`, `mean = mean(S, W_Z)`, `W_Z=200` 4h bars (trailing, ≤ t-1). Anchor log
  `a`: S5 = OLS fit; S6/S7 = `feedLog + mean`; S8 = `feedLog + C_t + mean`.
- **Sell-limit (short):** `exp(a + z*·σ)` (upper band). **Buy-limit (long):** `exp(a − z*·σ)` (lower band),
  `z*=2.0`. Both precalc from ≤ t-1, placed as real cTrader pending limit orders.
- **On fill:** the filled side opens the position; its **form-2 take-profit** is set to `exp(a)` (the anchor
  mean, **fixed at entry**); the sibling band order is cancelled (`/REENTRY=none`).
- **Direction:** fade (sell the upper band, buy the lower band → both target the anchor mean).
- **Breach policy:** if a band is already through the market at arm time, that side is **skipped and
  refreshed next 4h bar** (don't chase an in-progress/past excursion). Documented modeling choice.
- **Refresh:** each 4h bar (while flat) cancels stale band orders and re-arms from fresh ≤ t-1 anchor/σ.
- **Horizon fallback:** `H_i = min(48, 3·HL_i)` 4h bars (HL = AR(1) half-life). Unexited at H_i → **market
  close at a bar open** (executable; not `OnClose`). Pays full cost.
- **No lower-domain:** decisions at 4h cadence; **fills adjudicated by cTrader at m1 resolution** (real
  pending orders), so same-4h-bar round trips (enter band → revert to mean within one 4h bar) are captured.
- `/REENTRY` = none (≤1 entry per 4h bar).

### Multi-symbol in-engine (reusable StrategyHost infra)

Cross-instrument spreads require multi-symbol `MarketData.GetBars(tf, sym)` (XRSI-V1 proven pattern,
EXP-010 built). The StrategyHost framework is **reusable infrastructure** (operator-ratified). Only the
family-specific spread computation, z-score, entry/exit price mapping, and order management are from scratch.

## 5. Cost model (analyst-derived; binding-leg discipline, L-02)

Form-2 = both legs limit (favourable-price fills) + market fallback on exit only.

| Component | Binding (conservative) | Disclosure (non-binding) |
|---|---|---|
| RT cost | Frozen per-instrument **4h** `cost_bps` (referee's own cost map) on **every completed round-trip**, applied to engine gross fill P&L → `realized_bps` (already net). Deliberately pessimistic for a limit strategy → net pass is robust. | `cost ∈ {0.5, 1, 2}×` RT + limit-favourable variant (commission-only on filled legs, half-spread only on market fallback). |
| Fallback exit | Full half-spread + commission (inside the RT `cost_bps`). | — |
| Unfilled entry | No trade, no cost (selection effect — diagnostic tests fill rate). | — |
| Naive control leg | Same `cost_bps` (frozen contract). | — |

## 6. Endpoints, adjudication, multiplicity, power

| Component | Specification |
|---|---|
| **Tradability (binding)** | Per-4h-bar realized net series `realized_bps` (engine exact-fill, intra-position MTM, cost-charged §5) → frozen referee (`referee_pstar.gate_stack_pstar`, domain=4h, q\*=0.75). Per-stratum verdict (L-03). |
| **Availability (alongside)** | From same emission: (E1) entry fill rate; (E2) gross P&L per filled round-trip (before cost); (E3) anchor-hit = exit-fill rate (did price reach the anchor mean?). Compared to dislocation-matched matched-random control (§7). |
| **Multiplicity** | 4 series × 1 domain = **4 Holm axes** (S5, S6, S7, S8). Cross-axis Holm max-statistic over the 4 axes (`availability_gate` G-019 pattern). Per-stratum is the binding read; axis max-stat is the admission unit. |
| **Power / MDE** | Per-cell MDE = smallest Δ the block-bootstrap resolves at `n_episodes`; `MDE > Δ*` or `n_episodes < N_min` → UNPOWERED (never FAIL). N_min = 20 (4h referee floor). |
| **TEST-stratum tally** | **0 counted reads** (TRAIN-only; all strata open on INFR-003 5-year dataset — `test-read-ledger.md` confirms 0). |

## 7. Availability endpoint (native vehicle, L-13)

**Native metric** (target-based, not MFE — L-13): does the entry fill AND does price return to the anchor
mean (exit fill)? This is the family's own mechanism (reversion-to-anchor), not an inherited price-geometry
metric.

**Dislocation-matched matched-random control:**
- Among 4h bars at the same `|z|` bin (same dislocation), sample screen-free random bars to count-match the
  conditioned events. Each control bar gets a **random entry level** and **random exit level** at the same
  distance (preserving the round-trip geometry, varying only whether the MR screen placed them at the
  extreme/mean vs random).
- Δ = endpoint(cond) − endpoint(dislocation-matched ctrl); **moving-block bootstrap** on conditioned events
  (serial dependence), iid on control; per-cell `ci_low` (`n_boot ≥ 10 000`). Block-permute per-event
  outcomes, never rotate the price path (L-07).
- **Disclosure nulls (non-binding):** random-timing (EXP-008's inherited null — expected to read negative on
  near-anchor bars, transparency only); random-within-|z|-bin (EXP-008-A2 diagnostic C2).

## 8. Leak tripwires (binding — must collapse the edge)

1. **Peer-feed phase-shift shuffle.** Shift the peer/basket price feeds by a random phase in time, recompute
   the spread, re-emit, re-adjudicate. The cross-instrument edge **must collapse** (the spread carries real
   cross-instrument co-movement, not a leak). A surviving edge ⇒ the spread is not carrying real information
   ⇒ **REJECT**. (Valid for cross-instrument spreads — the peer feed is the information source; shuffling it
   destroys the relationship. Unlike EXP-009's time-reversal which was time-symmetric for a stationary
   single-instrument deviation.)
2. **Label permutation.** Among the `|z|≥z*` bars, permute which are "entry" vs "no-entry" (shuffle the
   extreme labels), recompute Δ. The screen's marginal edge **must collapse**. A surviving edge ⇒ selection
   artifact ⇒ **REJECT**. (EXP-009 pattern; the specific |z|≥2 selection, not a random split, carries the
   edge.)

## 9. MR screening framework (informative, not gating — L-12)

Computed on each spread series (≤ t-1, TRAIN only), reported alongside results:

| Stage | Metric | Role |
|---|---|---|
| 1 | Lag-1 autocorrelation | Characterize momentum/reversion tendency |
| 2 | Variance Ratio (q=4) | Characterize random-walk vs reversion |
| 3 | ADF | Evidence against unit root |
| 4 | KPSS | Evidence against unstable stationarity |
| 5 | AR(1)/OU half-life | **Parameter** (used for H_i = min(48, 3·HL_i)); not a gate |
| 6 | Robust detrending (rolling median) | Characterize trend |

**None disqualify.** Binding admission = availability-over-matched-random (§7) + net-tradability under
frozen referee (§6). The MR screen is reported to characterize the spread series, not to gate entry.

## 10. Interpretation criteria (predeclared, frozen before outcome contact)

| Outcome | Condition |
|---|---|
| **Tradable-on-TRAIN** | ≥1 series axis clears cross-axis-Holm **AND** ≥50% of that axis's powered cells show referee-ADMIT (net `ci_low > 0`, §10.3a+P\*) **AND** availability Δ > 0 with `ci_low > 0` on ≥50% of powered cells **AND** both leak tripwires collapse on admitting cells. → gate a counted TEST read (new D0). |
| **Not-tradable** | Availability may be positive (gross) but net doesn't clear referee on the majority → record; family retained; availability characterized. Terminal-branch prior reinforced. Same cost/capture veto as CF-MR-002/003 if gross-positive but net-negative. |
| **Inconclusive / UNPOWERED** | <3 powered cells in an axis, or `n_episodes < N_min=20` on majority, or direction mixed. Record as UNPOWERED, never FAIL. |
| **REJECT** | Edge survives either leak tripwire (future-destroy control) → proof of leak → hard stop. |

Effect floors (economic-reasoning, band disclosed — L-08): availability E1 anchor-hit `Δ*_hit = +0.03`
(min advantage that could survive to net), band `{0.02, 0.03, 0.05}`; E2 gross-P&L `Δ*_gross = +0.03`;
E3 supportive (exit-fill rate, non-binding). Referee MDE = frozen 4h domain floor (candidate-blind).

## 11. Complexity budget

| Item | Planned | Budget |
|---|---|---|
| Statistical tests | 4 (availability Δ + referee adjudication + 2 leak tripwires) | 4 (comparative) ✓ |
| Visualisations | 4 (per-axis availability Δ, per-axis net verdict, fill-rate summary, MR-screen characterization) | 3-5 ✓ |
| Code modules | C# ISignalModel (1, from scratch) + Python ingest/analysis (1) + leak-tripwire shuffle runner (1) | 1-2 (price-primary: C# model + Python ingest) — leak tripwire is a config variant, not a new module |

## 12. Implementation safety constraints (for experiment-developer)

- **Timestamp alignment:** all spread computation on 4h bars by `CloseTime`; limit orders fill on 1-min
  price movement; positions emit per-4h-bar with real OHLC. `CloseTime` / `SourceCloseTime` for all
  temporal alignment, never bar indices.
- **Causality:** all decision inputs `≤ t-1` (previous 4h bar's close). The forming 4h bar's own OHLC is
  never read for decisions. Entry/exit limits are precalculated from `≤ t-1` data. Engine enforces this by
  construction (L-01).
- **Denominators:** per-4h-bar realized series; active-bar denominator (not per-bar total). Zero-baseline =
  naive control (same cost, no MR screen). Referee's internal naive leg is the zero-baseline.
- **Bounded iteration:** 32 cells × 4h bars (~5y × 6 bars/day × 252 days ≈ 7,560 4h bars/cell) × 16
  instruments (multi-symbol feed). W_Z=200 trailing window. All O(n) per bar; no quadratic operations.
- **Vectorization safety:** spread computation, z-score, and price inversion are O(1) per bar (streaming,
  stateful). OLS for S5 β is rolling (update, not refit). Block bootstrap is post-hoc in Python on emitted
  data. No vectorized price-strategy P&L (L-01).
- **Progress:** `tqdm` on the outer cell loop (32 cells). cTrader-CLI `run-experiment.sh` reports per-cell.
- **From-scratch:** family-specific C# code (spread, z-score, entry/exit mapping, order management) is new.
  Multi-symbol StrategyHost framework = reusable. Python ingestion = `xen.signals.ingestion` (reusable).
  Python analysis (availability Δ, referee adjudication, leak tripwire post-hoc) = new but follows EXP-009/
  010 patterns (not code reuse — logic reuse is fine, code is from scratch per L-13).
- **Holdout fence:** `AnalysisEndUtc` = each file's first-49% cutoff. `HoldoutFence.AssertCanEmit` throws
  on any emission at/after the fence. Final-30% never processed.

## GATE: REVISE → re-APPROVE (orchestrator inline pre-exec, 2026-07-01)

**First pass (APPROVE) was in ERROR** and is superseded. On review of the implementation against the
proposal (`.ignore/idea/`), three verdict-material faithfulness/correctness defects were found that the
first gate missed:

1. **Self-adjudicated fills (CRITICAL).** The original C# model consumed only aggregated 4h bars and
   adjudicated limit fills on the 4h High/Low — a vectorized residue, not native execution. Same-4h-bar
   round trips (the intrabar reversion the family targets) were uncapturable; the "1-min fill" claim was
   false. → **Route A rebuild:** native cTrader pending orders (`Mode=NativeOrders`); cTrader's m1
   backtester owns fills (`CrossInstrumentSpreadPlanner` + robot; self-adjudicating model deleted).
2. **Incoherent `|z|≥2` entry gate.** Gate + band were redundant and could only arm after the excursion
   printed on the close. → **resting-bracket, no z-gate** (§4), operator-ratified.
3. **Feed contamination.** `MarketDataBasketFeed` (CF-MR-003, 1h + carry-forward, the F-1 artifact) was
   reused. → **fresh `CrossInstrumentBasketFeed`** at 4h, exact-CloseTime alignment, from scratch (L-13).
   Also: horizon fallback fixed from `OnClose` to market-close at a bar **open** (open-to-open rule).

**Re-review (post-rebuild) checks passed:** single question (§1) · boundaries (§3) · criteria (§10) ·
budget (§11) · price-primary NATIVE-orders classification (§2) · holdout sealed, real first-49% cutoffs
computed (§3/§12; conf) · per-stratum binding (§6, L-03) · leak tripwires shipped (§8; phase-shift now a
valid 4h-bar feed decorrelation) · registry precondition (CF-MR-004 registered; 0 TEST reads) · from-scratch
family code (planner + feed, L-13) · no lower-domain (§4) · informative-not-gating (§9, L-12; z now pure
provenance) · frozen referee not tuned (L-12) · cost realism binding (§5, L-02).

**Open info notes:** (a) the availability §7 conditioned-event = a bracket fill; the matched-random control
is unchanged. (b) Python ingest/availability/leak-tripwire analysis is not yet built (Stage 3+). (c) The
credentialed cTrader-CLI run remains **operator-gated** (cost/credentials).

**Verdict: APPROVE (post-rebuild).** Proceed to Stage 3 (Execute) — pending the operator-gated run.
