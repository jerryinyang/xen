# E0 — Frozen Constants & Return-Basis Re-baseline (D-referee prereq)

**Status:** RATIFIED & FROZEN (2026-06-28). Branch `referee-renew-phase-001`.
**Binding once ratified:** frozen + hash-pinned **before E1**; candidate-blind; **never tuned on any
E1–E5 or CF-MR-002 outcome** (L-12). Parent: checkpoint `design.md` §D0 (Q6, Q7).

E0 is not an experiment (no falsifiable question) — it is the predeclaration that freezes the two
candidate-blind inputs every D-referee experiment consumes. Two items: a 17-instrument cost map (Q6)
and the open-to-open `≤ t-1` return basis (Q7).

---

## 1. Return-basis re-baseline (Q7)

- **Change.** Replace the frozen referee's close-to-close return primitive
  (`referee_calibration.py:next_log_returns_from_bars:463-472`, `Close[t+1]/Close[t]`) with an
  **open-to-open** next-step return evaluated on **confirmed bars `≤ t-1`**: the decision at bar `t`'s
  open is conditioned only on data through `t-1`; the return is `Open[t+1]/Open[t]`. Matches the
  Chapter-02 standing execution convention (`OnClose` is not live-actable).
- **Scope.** Applies to the **recalibrated adaptive** suite only. The retained Chapter-01 frozen suite
  keeps close-to-close for parallel disclosure (do not mutate the frozen artifact).
- **Implementation.** A new primitive (e.g. `next_open_to_open_returns_from_bars`) alongside the legacy
  one; the adaptive gate consumes the new one. No change to split discipline / block bootstrap / CIs.
- **Consequence.** The per-bar **net equity curve** built from these returns is the natural input for the
  Q9/F10 return-series statistic (Sharpe LB + co-binding Calmar/tail).

---

## 2. 17-instrument round-trip cost map (Q6) — PROPOSED, PENDING RATIFICATION

**Why operator-gated.** Timebars are OHLC + TickVolume only — **no spread column**, so the map cannot be
measured from data. It is class-anchored judgment extending the frozen referee's existing 4 anchors,
**conservative** (over- not under-charge), candidate-blind, frozen before E1. This mirrors the EXP-085
precedent ("conservative, data-anchored to precedent, PENDING OPERATOR RATIFICATION, never tuned on
outcomes").

**Convention.** Per-bar round-trip **bps** in the referee's `ROUND_TRIP_COST_BPS` sense (domain-invariant;
1h and 4h only — 5m dropped per Q6). Anchors retained **unchanged**: EURUSD 1.0, XAUUSD 3.0, BTCUSD 10.0,
USTEC 4.0.

| Instrument | Class | Proposed RT (bps) | Anchor / rationale |
|---|---|---|---|
| EURUSD | FX major | **1.0** | frozen anchor (unchanged) |
| USDJPY | FX major | **1.0** | most-liquid major, ≈ EURUSD |
| GBPUSD | FX major | **1.2** | major, slightly wider than EUR |
| USDCHF | FX major | **1.5** | major, wider spread |
| USDCAD | FX major | **1.5** | major (EXP-085 class) |
| AUDUSD | FX major | **1.5** | major, wider than EUR (EXP-085) |
| NZDUSD | FX major | **2.0** | less liquid than AUD (EXP-085 NZD>AUD) |
| EURJPY | FX cross | **2.0** | JPY cross, wider than majors |
| AUDJPY | FX cross | **2.5** | less-liquid JPY cross |
| GBPJPY | FX cross | **2.5** | widest common JPY cross |
| XAUUSD | metal | **3.0** | frozen anchor (unchanged) |
| US500 | index | **3.0** | deepest equity index, ≤ USTEC |
| USTEC | index | **4.0** | frozen anchor (unchanged) |
| DE30 | index | **4.0** | ≈ USTEC; broker history truncated 2026-01-16 |
| JP225 | index | **4.0** | ≈ USTEC |
| US2000 | index | **5.0** | small-cap, wider than large-cap indices |
| BTCUSD | crypto | **10.0** | frozen anchor (unchanged) |

**Derivation rule (frozen).** Cost ranks monotonically by liquidity class: FX major (1.0–2.0) < FX cross
(2.0–2.5) < metal/large-index (3.0–4.0) < small-index (5.0) < crypto (10.0); the 4 frozen anchors are
fixed points; within-class values are conservative (rounded up). The rule is performance-independent and
fixed in advance — it is **not** re-derived from any candidate's realized returns.

**Out of scope.** Financing/overnight cost (the referee charges round-trip only, per its frozen
convention); per-domain cost variation (held domain-invariant as in the frozen map).

---

## 3. Freeze record (2026-06-28)

- **Operator ratification (2026-06-28):** §2 cost map ratified as-proposed; §1 build path = extend map +
  new open-to-open primitive in a separate module (frozen Chapter-01 suite untouched).
- **Implementation:** `python/src/xen/referee_adaptive.py` — `ROUND_TRIP_COST_BPS_17` (17 instruments,
  1h/4h), `adaptive_cost_bps_for`, `next_open_to_open_returns_from_bars`. The frozen
  `referee_calibration.py` is **not** mutated (its hash stays stable; the renew is additive).
- **Hash-pin (E0 state):** `referee_adaptive.py` SHA256
  `78c3e23ad485276b5c1a16c0b3397cd3e6a5b20056cf1dc0b73e6b7fb4e532c4`, committed on
  `referee-renew-phase-001`. The E3 adaptive-gate code will be appended to this module and
  **re-pinned**; git history is the authority that the E0 constants predate any E1–E5 / CF-MR-002
  outcome (the binding freeze guarantee). No E1–E5 / CF-MR-002 outcome may revise either input.
- **Verification:** 17 instruments present; 5m correctly absent (KeyError); O2O returns numerically
  correct (`log(Open[t+1]/Open[t])`).

**E0 closed → E1 (cost-control arm) unblocked.**
