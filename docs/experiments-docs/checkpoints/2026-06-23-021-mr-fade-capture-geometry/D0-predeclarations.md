# Phase 021 D0 — Predeclarations (CF-MR-001 RSI-2 Fade Capture-Geometry & Tradability)

**Status:** **FROZEN — G0 RATIFIED (2026-06-23, operator-authorized).** This freezes the batch-2
(availability→tradability) design for the **bare RSI-2 fade (CORE)** admitted at G-020. D1–D9 and the
ratified-parameter table below are **FROZEN**; no result-producing code (EXP-090) runs against anything but
these. No amendment without a dated `D0-amendment-*` file in this directory (programme norm). No new selection
statistic is introduced ⇒ no bite-check is required (the binding gate is the existing frozen referee suite).

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry` · **Governing design:** `design.md` ·
**Gate criteria:** `G-021-gate-criteria.md`.
**Family / lever:** CF-MR-001, first candidate slot **consumed at G-020**; lever = **bare RSI-2 fade (CORE)**,
intraday. **HYP:** `CF-MR-001/HYP-002` (tradability of the admitted lever).
**Discipline (binding):** TRAIN sub-split only until the single terminal TEST read (EXP-093); real-price
outcomes; deterministic (fixed seeds, byte-identical second pass); **no entry re-tuning**; per-stratum reporting
(LESSON-001). The final-30% global holdout is **never** loaded at any stage of Phase 021.

---

## Ratified parameter table (the four §8 decisions — frozen here)

| # | Parameter | Frozen value | One-line justification |
| --- | --- | --- | --- |
| 1 | **ERT equilibrium reference** | **`wilder_ema(Close, 10)`** (domain EMA-10) | A small multiple of the realized ~3-bar reversion horizon (EXP-089) — reachable within the hold cap, a stable local mean, and a *distinct scale* from RSI(2) and from the dead EMA(20) trend filter (no conflation). SMA(20) registered as a future sensitivity, not run. |
| 2 | **Adverse stop** | **`2.0 × ATR(14)`** from entry, identical across all arms | ≈2.7× the favourable target scale (`MFE_med`≈0.75 ATR) gives a fade room to breathe through continued adverse movement before reverting, while bounding the catastrophe tail; round, conventional, untuned. Held fixed across native + contrast arms ⇒ favourable-capture isolation (EXP-057). |
| 3 | **Hold cap (max-hold)** | **the EXP-089 causal MR-tempo cap**, reused unchanged: `mr_tempo_caps` (mult 1.0, `MR_CAP_FLOOR=3`, `MR_CAP_MAX=40`, `MR_EPISODE_WINDOW=20`); exit-on-close at cap | Matches the measured reversion horizon (~3 bars; 77% at FLOOR=3) and is **already frozen** in `xen.mean_reversion` — no new tuning. The time backstop for both native targets and the stop. |
| 4a | **EXP-091 net-clear + quorum rule** | a (exit × cell) **net-clears** iff net (post-cost) expectancy one-sided lower bound (`Z=1.645`, moving-block bootstrap) **> 0**; an **exit passes the screen** iff it net-clears in **≥5 cells over ≥3 instruments** | The established EXP-046/056 quorum; floor = break-even after EXP-085 cost. Gross-clears reported descriptively (sanity). |
| 4b | **EXP-092 sequence α** | **α = 0.05** one-sided, per-cell `SEQUENCE_PASS` (net `ci_low_1s`>0, power-confirmed by the EXP-090 MDE) | EXP-034 A1-sequence precedent; produces the hash-pinned candidate set + phase Holm rule for EXP-093. |
| 4c | **EXP-093 TEST PASS rule** | **PASS iff Holm-adjusted p ≤ 0.05 AND `ci_low_1s` > margin**, margin = the cell's **EXP-090-calibrated MDE**; else `INCONCLUSIVE_SPANS_ZERO` / `FAIL` | The EXP-037/038/032 margin rule (necessary-and-sufficient: significance *and* a materially-bounded effect). |

---

## D1 — Entry (inherited frozen), dataset, domains, member cells

**Entry — inherited byte-for-byte from Phase 020 D0 / `xen.mean_reversion` (NO re-tuning):** `RSI(2)` Wilder on
domain `Close`; **long `RSI₂<10`**, **short `RSI₂>90`** (period 2, extremes 10/90). Favourable = long→up,
short→down.

**Dataset:** VAL-005-admitted 5-year 1-minute bars, 16 instruments, holdout-fenced `build_domain_bars`.
**Domains: {15m, 1h} only** (4h excluded — dead-by-absence at EXP-089, 1/14; not carried). The **1-minute base
series** is the intrabar fill source (D2.5). **TRAIN sub-split `[0, int(analysis_rows·0.7))` only** for
EXP-090–092; EXP-093 reads the analysis-TEST stratum (D7). The final-30% global holdout is never sliced. All
P&L/excursion metrics in **ATR(14) units** on real OHLC. Master seed `20260623`.

**Member cells:** the 15m/1h subset of the EXP-080-READY set = **32 instrument×domain cells** (16 instruments ×
{15m, 1h}). EXP-090 re-confirms exit-substrate readiness + per-cell event-level MDE; a cell failing the D8
bracket is `COVERAGE_EXCLUDED` with record.

## D2 — Exit slate (frozen). Native MR pair (primary) + conventional contrast.

All arms share the **same adverse side** (D2.3) and the **same intrabar 1m fill engine** (D2.5); only the
favourable-exit mechanism varies ⇒ a win is attributable to the target, not the stop.

### D2.1 — EXIT-RCT (Reversion-Completion Target; operator-proposed)
- **Target price (long):** `P*_t = Close_t + (AL_t − AG_t)`, where `AG_t`, `AL_t` are the Wilder period-2
  average gain/loss at domain bar *t* (the next-bar move that returns RSI₂ to 50; `n=2`). Short:
  `P*_t = Close_t − (AG_t − AL_t)`. **Recomputed each domain bar after entry** ⇒ trailing.
- **Implementation freeze:** `xen.mean_reversion` exposes the Wilder average gain/loss arrays
  (`wilder_avg_gain_loss(close, 2)`, a deterministic additive helper to the existing `wilder_rsi`); the target
  is a pure transform of `(Close, AG, AL)`. No look-ahead (uses state at/through bar *t* only).
- **Honest caveat (frozen interpretation):** a model-derived target *price* — RSI is **not** recomputed
  intrabar; the claim is "price reached the reversion-completion level." The fill price is a **real** touched
  price (D2.5), not synthetic.

### D2.2 — EXIT-ERT (Equilibrium-Return Target; Claude-designed)
- **Target price:** `M_t = wilder_ema(Close, 10)` at domain bar *t* (param #1), the local equilibrium the
  deviation reverts toward; recomputed each domain bar ⇒ trailing. Long fills when 1m high ≥ `M_t`; short when
  1m low ≤ `M_t`.
- Complementary to RCT by construction (signal-completion vs price-to-mean). No look-ahead.

### D2.3 — Adverse side (frozen, identical across ALL arms)
- **Stop:** `2.0 × ATR(14)` from entry (param #2), a static price level. **Max-hold:** the EXP-089 causal
  MR-tempo cap (param #3); on cap expiry, exit-on-close at the cap bar's domain close.
- The stop and cap are the *only* adverse mechanism; no trailing stop on the adverse side in batch 2.

### D2.4 — Conventional contrast arms (tested, not expected to dominate)
- **RSI-revert-on-close** — exit at the domain **close** when RSI₂ crosses 50 (the reactive, non-intrabar
  analog of RCT; quantifies what proactive-resting + intrabar fill buys).
- **Fixed-bar** — close at the MR-tempo-cap horizon (`xen.exit_rules.fixed_horizon_exit_idx`).
- **ATR triple-barrier** — favourable `1.0×ATR` target / `2.0×ATR` stop, intrabar-filled (the same engine);
  the **third (time) barrier is the same EXP-089 MR-tempo cap (param #3)** used by every other arm, so the
  adverse side (stop + hold horizon) is identical across all arms (D2.3) and only the favourable leg varies
  (clarified in `D0-amendment-001`, 2026-06-23).
- **Favourable partial / trail** — EXP-059 V2A-style two-leg (`xen.capgeo_cost.partial_two_leg_exit`), as the
  primitive allows.
- Each arm is a **single frozen parameter point — no grid** (multiplicity discipline).

### D2.5 — Intrabar 1m fill engine (frozen; new module `xen.intrabar_fill`)
- **Mapping:** each domain bar → its constituent 1-minute bars by **timestamp** (`CloseTime`/`SourceCloseTime`),
  never by bar index. Forward from entry, walk 1m bars in chronological order.
- **Order-of-touch:** within each 1m bar, if both the favourable target and the adverse stop lie inside
  `[Low, High]`, resolve by the **conservative tie-break** (adverse-first) — the EXP-054 fill-model question,
  answered at 1m granularity. Record tie-break incidence per cell.
- **Fill price:** the target/stop **level** (a real, marketable touch), not the 1m close. Causal: only 1m bars
  at/after entry; the 1m slice is **clipped by timestamp at the TRAIN edge** for EXP-090–092 (the analysis-TEST
  1m bars enter only at EXP-093; holdout 1m bars never).
- Determinism: byte-identical second pass including the 1m walk.

## D3 — Cost model (frozen; EXP-085 conservative, reused unchanged)

`xen.capgeo_cost` / `xen.financing` exactly as ratified for Phase 018 (EXP-085): **CONSERVATIVE round-trip =
2× BASE** transaction cost + per-instrument adverse-side **financing bps/day** on realized holding duration
(`holding_days`, `event_costs`). Per-instrument `(RT_i, F_i)` table inherited unchanged. **Net = gross − cost**
in ATR units. A faster-turnover round-trip sensitivity is a disclosed companion at EXP-091, **not** a
re-estimation of the binding model.

## D4 — Binding tradability gate (frozen referee suite; not re-derived)

The **frozen qualification suite** — strict gate stack + EXP-012 ratified-loose referee + EXP-018 revised
incremental/fitness unit (`xen.incremental_referee`, `xen.referee_calibration`) — is the binding gate, exactly
as it remained binding for Phase 018 after G-017. The **`ASS` qualifier is NON-BINDING discovery overlay only**
(G-017 `DISCOVERY_ONLY`); it may be reported, never gates. **No new referee is built or tuned.** No new
selection statistic is introduced ⇒ **no bite-check is required** (if EXP-091/092 introduce a novel selection
statistic, it must be bite-checked GREEN before that experiment runs).

## D5 — Endpoint / metrics (frozen)

Per (exit × cell): **net per-event expectancy** (mean and median), ATR(14) units, real prices, after D3 cost,
over the resolved exit path (D2). Co-reported: gross expectancy, fill-rate, realized hold (bars/days), adverse
tail (MAE/`q05`), tie-break incidence, and the favourable-capture fraction. The binding figure for advancement
is the **net expectancy one-sided lower bound** (D6); medians are co-reported (the family is median-positive /
mean-fragile per EXP-089 — both legs disclosed, never pooled across cells).

## D6 — Screen / sequence / TEST decision rules (frozen; = parameter table 4a–4c)

- **EXP-091 (screen):** net-clear iff net `ci_low_1s` > 0; exit passes iff net-clears in **≥5 cells / ≥3
  instruments**. **Empty screen ⇒ G-021 NOT_TRADABLE at 0 TEST reads** (no candidate to confirm).
- **EXP-092 (sequence):** per-cell `SEQUENCE_PASS` at **α=0.05** one-sided (net `ci_low_1s`>0, power-confirmed by
  the EXP-090 MDE) → the **hash-pinned candidate set** (sha256) + the phase Holm rule for EXP-093.
- **EXP-093 (TEST, one-shot):** for the carried cells, **PASS iff Holm-adj p ≤ 0.05 AND `ci_low_1s` > margin**
  (margin = the cell's EXP-090 MDE); else `INCONCLUSIVE_SPANS_ZERO` / `FAIL`. The single binding tradability
  read.

## D7 — Counted-read accounting / TEST plan (binding)

- **EXP-090–092: 0 counted TEST reads** — TRAIN sub-split only; analysis-TEST + holdout never sliced
  (TRAIN-only disclosure convention). `test-read-ledger.md` unchanged through EXP-092.
- **EXP-093:** carries the **smallest defensible set — best 1–2 cells per surviving exit** (param ratified §8.3).
  Each carried **(instrument, domain) cell spends 1 counted TEST read on that stratum**, recorded in
  `test-read-ledger.md` **in the same change** that records the result. **Cap = 2 lifetime counted reads /
  stratum**; all 48 strata are currently 0/2, so each carried stratum goes 0→1 (one read preserved for any
  future confirmation). The read is on the **analysis-TEST stratum** (last 30% of the analysis set) — **not**
  the final-30% global holdout, which stays sealed (a global-holdout release is a separate, later gate).
- **One stratum = one counted read, even if multiple surviving exits select the same cell** (clarified in
  `D0-amendment-001`, 2026-06-23). The counted read attaches to the **(instrument, domain) stratum**, not to
  the (exit × cell) pair: if two surviving exits both carry the same (instrument, domain) cell to EXP-093, that
  stratum spends **1** counted read (0→1), not 2 — the binding read is the stratum's events entering the gate,
  which happens once regardless of how many exits are evaluated on it. This keeps a single EXP-093 from pushing
  any stratum toward its 2/2 cap.
- The candidate slot is **already consumed** (G-020); Phase 021 consumes **no additional slot**.

## D8 — Member-cell readiness bracket (EXP-090)

Per 15m/1h cell: RSI-MR event coverage **≥15 events** (EXP-080 floor; no upper bound); exit substrate
deterministic; per-cell event-level **MDE finite** under the frozen referee (a cell with no finite MDE is
`COVERAGE_EXCLUDED` — it cannot bound a confirmation, à la EXP-044 BTCUSD-4h). Realized counts supersede design
power figures and are disclosed per cell.

## D9 — Determinism, real-price discipline, no tuning

- All seeds fixed/recorded; second full pass (incl. the 1m intrabar walk and any bootstrap stream) is
  byte-identical.
- **Real prices only** (`RealOpen/High/Low/Close`, 1m real OHLC for fills); no HA/Renko synthetic-price returns.
- **No tuning:** RSI 2/10/90, ERT EMA-10, adverse 2.0×ATR, the MR-tempo cap, the EXP-085 cost table, and the
  D6 thresholds are **frozen**. The vol-regime partition, the TREND/FILTER variants, the contrarian arm, the
  25/75 scheme, regime×variant cross-cuts, and instrument/domain (incl. 4h) expansion are
  **registered-but-deferred** (multiplicity ledger); opening any requires a dated `D0-amendment-*` stating
  whether it consumes a new slot.

## Slot & TEST accounting (summary)

- **0 additional candidate slots** (the first was consumed at G-020).
- **0 counted TEST reads through EXP-092**; EXP-093 spends ≤1 read/carried-stratum (cap 2/stratum; all currently
  0/2) recorded in `test-read-ledger.md` in the same change.
- Final-30% global holdout sealed throughout Phase 021.
