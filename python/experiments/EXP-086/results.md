# Results: EXP-086 — Screen M (single-series magnitude / non-directional availability)

**Phase 019 family-selection availability screen · axis M · `CF-VOLEXP-001/HYP-001` · TRAIN-only, gross, 0 candidate slots / 0 counted TEST reads.**
Companions: `scope.md`, `analysis-plan.md`, `audit.md` (PASS-with-findings; its Verdict Forensics is the spine of this interpretation), `results/axis_admission.json`, `results/cell_availability.csv`, `results/run_metadata.json`.

---

## Verdict block (two distinct verdicts — do not conflate)

| Layer | Verdict | Meaning |
|---|---|---|
| **Experiment integrity** | **`SCREEN_DELIVERED`** | All statistics produced deterministically for both primitives across all 46 member cells; determinism, matched-random reconciliation, and holdout fence all clean (`determinism_ok=true`, `recon_all_ok=true`, `holdout_untouched=true`, `counted_test_reads=0`, `candidate_slots=0`). This is the only verdict EXP-086 *owns*. |
| **Availability disposition** | **`ADMITTED` — PROVISIONAL, NON-BINDING** | Single-axis read at FWER 0.05: `S_M = 3 > S* = 2`, axis `perm_p = 0.0326`, `ranking_z = 2.62`. **The binding admit/exonerate is G-019**, where the cross-axis Holm step-down over {M, X, (F)} can only *raise* `perm_p`. At `perm_p = 0.0326` there is little headroom under 0.05. |

**This is not an edge and not a tradability claim.** It is a gross, TRAIN-only availability read. The provisional admit is **tail-only** and therefore, by the harvest-model guard (design §8), a **long-vol** finding for `CF-VOLEXP-001` — **never** a directional edge.

---

## The two reads, kept strictly separate (D3.M — no pooled `|move|`)

Four sub-screens = {2 primitives} × {typical-range, tail}. Per-cell "beats random" = one-sided 95% lower bound of Δ-over-matched-random > 0. `S = #cells-beat-random` over the 46 powered cells.

| Sub-screen | Statistic | `S` (of 46) | single-sub `S*` | single-sub `perm_p` | In D2a null band [17,28]? |
|---|---|---|---|---|---|
| HARAMI · typical-range | median `max(MFE,MAE)` | 0 | 0 | 1.000 | no (below) |
| HARAMI · tail | tailmass | 0 | 1 | 1.000 | no (below) |
| NR7 · typical-range | median `max(MFE,MAE)` | 0 | 2 | 1.000 | no (below) |
| **NR7 · tail** | **tailmass** | **3** | 2 | **0.0066** | no (below) |

- **Typical-range (normal-size) availability is dead.** `S = 0` on both primitives. The NR7 conditioned median range is *below* random (per-cell `Δ̂` median ≈ −0.28 ATR) — a quiet bar is followed by a compressed near-term range. This is a **true no-(positive-)location effect**, matching the EXP-081 prior (`MFE_med` Δ −0.140, `MAE_q90` Δ −0.719).
- **The single live thread is NR7 · tail.** It drives the axis statistic `S_M = 3`. On its own it is strong (`perm_p = 0.0066`); the binding axis `perm_p = 0.0326` is that number after the **max-statistic within-axis multiplicity penalty** for screening 4 sub-screens and keeping the best — the honest, larger p.

### FWER sensitivity band (pre-registered robustness sweep, not a selection)

| FWER | `S*` | Admitted? |
|---|---|---|
| 0.025 | 3 | **NO** (`S_M = 3` not `> 3`) |
| 0.05 | 2 | yes |
| 0.10 | 2 | yes |

**The admit is borderline:** it survives at 0.05/0.10 but **fails at 0.025**. MC stability (1000 vs 5000 permutations) is invariant (`S* = 2`, `perm_p ≈ 0.033–0.038`).

---

## Per-domain breadth of the NR7 · tail effect (disclosure — the anti-masking read)

The three admitted cells are **all 15m** (NZDUSD-15m, USTEC-15m, US2000-15m), so masking must be ruled out. Re-derived per domain for NR7 · tail:

| Domain | cells | median `n_cond` | median tailmass `Δ̂` | cells with `Δ̂ > 0` | median `s_cell` | `S` (beats random) |
|---|---|---|---|---|---|---|
| 15m | 16 | 10254 | +0.0052 | **15 / 16** | 0.0050 | **3** |
| 1h | 16 | 2514 | +0.0024 | 10 / 16 | 0.0085 | 0 |
| 4h | 14 | 430 | +0.0006 | 7 / 14 | 0.0211 | 0 |

**The pooled `S_M = 3` is conservative, not masking.** The tailmass lift (`Δ̂ > 0`) is positive in the large majority of NR7 cells in *every* domain. Whether a cell clears `beats_random` is governed by `Δ̂` vs `s_cell ∝ 1/√n`: several 4h cells have *larger* raw lifts (EURJPY-4h +0.022, USTEC-4h +0.013) but fail because `s_cell ≈ 0.02`; the 15m winners have *smaller* lifts (~0.010) yet clear because `s_cell ≈ 0.005`. The three winners are 15m **because that is where the ~10k event count powers the one-sided bound**, not because the effect is 15m-specific. `S_M` therefore *understates* a broadly-present-but-underpowered effect.

---

## Mechanism (why ADMITTED)

NR7 (narrowest true-range in 7 bars) is a genuine low-volatility **compression** state. Conditioned on it, the regime-signed realized outcome over the adaptive cap carries a small but consistent **excess of rare large adverse-signed moves** (catastrophe-tail mass below `median − 3·MAD`) versus matched random-timing entries — the classic **compression → expansion** fingerprint. Simultaneously the typical/median range is *below* random (the quiet state suppresses the near-term median move), so the structure lives **only in the rare tail, not in location**. This is precisely the low, tail-concentrated `CF-VOLEXP-001` prior. HARAMI shows the same-sign tail lift but weaker (best `Δ̂ ≈ +0.007`), never clearing its SE ⇒ `S = 0`.

**The effect is economically tiny.** At 15m the tailmass lift is `Δ̂ ≈ 0.005–0.011`, i.e. ~0.5–1.1 *extra* catastrophe-tail events per 100 over a random-timing control.

Plots: `plots/01_delta_typical_range.png` (null location read), `plots/02_delta_tail.png` (the live tail read, beats-random cells ringed), `plots/03_permuted_axis_null.png` (the admission decision: `S_M` vs the max-stat null and FWER band), `plots/04_outcome_examples.png` (conditioned vs random signed-outcome on the densest cells), `plots/05_magnitude_budget.png` (see caveat 1).

---

## Gate-shape note (for the interpreter of the *next* axis and for G-019)

- The binding gate reads **tailmass — a shape statistic — and it can see the effect's shape**: the admit is driven by the tail read while the location read is correctly null. Right instrument for the shape present.
- The tail read is **left-tail-only on a regime-signed outcome** (the catastrophe boundary on `rd · outcome`). By design this targets the *adverse* catastrophe tail (the documented non-trivial-prior signal). A purely *favorable*-signed (right-tail) magnitude expansion would be only partially visible (the median typical-range read won't catch a rare tail; the `q05` companion is non-binding). This bounds what "magnitude availability" this screen could detect; it does not affect the present admit (the effect that exists is the adverse tail).
- Typical-range used direction-agnostic `d=+1` geometry (`max(MFE,MAE)`); its `S = 0` is a real no-location-effect, not a wrong-instrument miss.

---

## Caveats & limitations

1. **The magnitude-budget `net_atr` is necessary-not-sufficient — do NOT read it as an edge (audit W2).** For the tail read, harvestable = `|q05|` (the *size* of the rare adverse move, several ATR), so `net_atr` is large and positive (NZDUSD-15m +8.27, USTEC-15m +11.40 ATR; US2000-15m is `cost_available=false` — US2000 ∉ the EXP-085 4-instrument cost table). This only says the rare move is bigger than round-trip friction — it presupposes you are *positioned* to monetise that tail (the long-vol thesis itself, untested here). It is **not** part of the admission gate and moves no verdict-bearing number.
2. **Borderline admit.** Fails FWER 0.025; survives 0.05/0.10. One primitive (NR7), one powered domain (15m), tiny effect.
3. **Conservatively-built null (audit W1).** The max-statistic joint null uses independent per-sub-screen permutation streams; max-over-independent ≥ max-over-dependent, so `S*` is if anything *too high* — the admit cleared a bar at least as hard as a shared-permutation construction. Cannot inflate the admit.
4. **Binding decision deferred.** EXP-086 emits statistics only; the admit/exonerate is **G-019**, after the slate, under the cross-axis Holm step-down (which can only raise `perm_p = 0.0326`).
5. **TRAIN-only, gross.** No exit, cost-as-gate, sizing, or P&L. No TEST or holdout contact; all 48 strata remain 0/2 counted reads / open.

---

## What this does and does not establish

- **Establishes:** the single-series **magnitude** cell of the availability 2×2 is **not uniformly dead** — there is a small, real, broadly-present (but mostly underpowered) **compression → rare-tail-expansion** signal under NR7, provisionally clearing the multiplicity-adjusted gate at FWER 0.05. **Typical/normal range is dead.**
- **Does not establish:** any edge, any tradability, any directional signal, or any binding admission. The signal is tail-only (long-vol), tiny, borderline, and pending G-019.

---

## Recommended next steps (new scopes only — no extension of EXP-086)

1. **EXP-087 — Screen X (cross-sectional relative strength, `CF-XSECT-001/HYP-001`)**, then optionally **EXP-088 — Screen F (order-flow, `CF-FLOW-001/HYP-001`, reserved-conditional)**, on the same D2b gate, so G-019 has the full {M, X, (F)} slate.
2. **G-019 adjudication** (terminal gate): cross-axis Holm step-down over the three axis `perm_p` values. Note M enters at `perm_p = 0.0326` with little headroom under 0.05 — its binding survival depends on how many other axes carry small p-values.
3. **Conditional on M surviving G-019 as ADMITTED:** open `CF-VOLEXP-001` at its own G0/D0 and run a **long-vol readiness / characterization** (`CF-VOLEXP-001/HYP-002+`) — two-sided-cost net harvest of the NR7 rare tail, with NR7 confirmed as the stronger compression primitive and 15m as the powered domain. **No exit/sizing/P&L work before that admission** (those levers are deferred until a first-order availability edge exists).
4. **If M is exonerated at G-019** (or all axes exonerated): record the single-series magnitude cell as measured-dead and route per the design §7 / D5 mechanical rule. The result is **retained** in the registry regardless.

*Registry disposition is recorded by the documenter in `report.md` and the Phase 019 batch (see Stage 7).*
