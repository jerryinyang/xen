# Phase 014-B Addendum — EXP-059B: Uncapped Structure Trailing (EXP-059 gap-fill)

**Checkpoint:** `2026-06-14-014-ha-harami-substrate-and-capture` (014-B).
**Date:** 2026-06-16.
**Status:** Design addendum. Extends `014-B-design.md` §5 slate and `014-B-D0-addendum.md`
P18. Adds **EXP-059B** (`CF-HA-HARAMI-001/HYP-012b`) and the new countable variant
`/EXIT-TRAIL-UNCAPPED`. **0 candidate slots, 0 TEST reads, TRAIN-only, gross** — identical
discipline to the rest of 014-B; no intermediate gate (single G2 after the full slate, P21).

> **Mandatory-reading precondition (binding, 014-B).** `014-A-conditioning-gap-and-validation-lessons.md`
> was read in full before this addendum and the EXP-059B scope were written. EXP-059B honours
> the four rules: (a) **conditioning** — the object is the live `/STRONG`-conditioned HA harami
> (identical population to EXP-053/059), only the *adverse-exit model* changes; (b)
> **harami-anchor** — entry is the harami confirmation-bar real close `C`; (c)
> **position-in-move descriptive-only** — never a live filter; (d) **expectancy endpoint (P14)**
> — median per-event position-weighted gross expectancy, P15 fills, real prices.

---

## 1. The gap (verified against EXP-059 code)

EXP-059 ("Position-Management Exits") predeclared a 12-arm sweep including three standalone
trailing arms (`TRAIL-PURE`, `TRAIL-TP-INIT`, `TRAIL-TP-NOINIT`) and four `COMBINED-*` arms,
all on the `/EXIT-TRAIL-STRUCT` adverse model. The scope held **the third barrier (the P4
adaptive time cap, floor = 6) at benchmark for every arm** (EXP-059 `scope.md` §Operator
decisions; "every arm retains the benchmark time cap as the ultimate backstop"). This is
confirmed in the implementation:

- `xen.position_exits.resolve_legs` / `_scan_event` bound the forward scan at
  `cap_end = ei + n_ev` and emit an explicit `PX_TIMECAP` exit for any leg still open at the
  cap; `n_event` is `bench_n` (the P4 adaptive cap) for every arm (`run_experiment.py`
  `resolve_arm` passes `bench_n` to both `build_active_stops` and `resolve_legs`).
- The initial stop is the benchmark 1:1 `adv` level unless `trail_init_none=True`. Among the
  trailing arms only `TRAIL-TP-NOINIT` sets `trail_init_none=True`; `TRAIL-PURE`,
  `TRAIL-TP-INIT`, and all `COMBINED-*` keep the 1:1 initial stop.

**Consequence.** The trailing mechanism is, in the family thesis, a *separate adverse-exit
model that replaces the 3-barrier geometry* — not a swap of the adverse leg inside it. But
EXP-059 implemented it as a plugin (`adv_mode = ADV_TRAIL`) inside the capped 3-barrier
resolver. Even `TRAIL-TP-NOINIT` — the closest existing arm, which already drops the initial
stop — retained the benchmark cap. **The configuration with no initial stop AND no time cap
("pure trailing as designed") was never measured.** EXP-059's trailing/combined results
describe trailing-within-a-6-bar-horizon, not the trailing exit model on its own terms.

This is a genuine scope gap, not an EXP-059 defect: EXP-059 was a clean OAT on the
position-management machinery with the third barrier deliberately held at benchmark (the
horizon lever was EXP-058; the cross-layer combination was deferred to EXP-060). Removing the
cap from the trailing model is a **new countable variant** (`/EXIT-TRAIL-UNCAPPED`), so it
gets its own experiment and registry entry rather than an EXP-059 amendment (no scope
expansion of an approved experiment).

## 2. What EXP-059B measures

The `/EXIT-TRAIL-UNCAPPED` adverse-exit model on the **same** live `/STRONG`-conditioned,
harami-anchored population and 99-cell grid as EXP-053/059:

- **No initial stop.** No adverse exit before the first secondary-ZigZag (`ATR_MULT_TRAIL = 0.5`)
  pivot confirms after entry; the first confirmed secondary up-move (long) / down-move (short)
  establishes the first trailing level.
- **No time cap.** The forward window is unbounded — from `entry_idx + 1` to `last_train_idx`
  (or until the trailing stop fills). `bench_n` is **not** used as a window bound. The only
  censoring is `DATA_CENSORED` when the window reaches the TRAIN data edge before the stop
  fills (same TRAIN-fence exclusion rule as the rest of 014-B).
- **Monotone ratchet unchanged** (P18): `stop ← max(stop, most-recent confirmed secondary
  pivot low)` for a long fade; mirror for a short. Causal — the stop moves only at a
  confirmation bar.
- **Exit:** price fills the trailing stop at the intrabar P15 path point.

### Arms (binding + disclosed)

| Arm | Fav side | Adverse model | Cap | Init stop | Role |
| --- | --- | --- | --- | --- | --- |
| `BENCH` | 50% fav (1 leg) | 1:1 fixed | adaptive cap | 1:1 | Reference; reproduces EXP-053/059 BENCH (invariant). Binding paired-contrast anchor. |
| `TRAIL-PURE-UNCAPPED` | none (let it run, 1 leg) | structure trail | **none** | **none** | **Binding.** "Pure trailing as designed." |
| `COMBINED-UNCAPPED-V2A` | V2A legs {1/3,2/3,1}×fav_dist | structure trail (open weight) | **none** | **none** | **Binding.** Partial favourable legs + uncapped no-init trailing on the still-open weight. |
| `TRAIL-PURE-NOINIT-CAPPED` | none (1 leg) | structure trail | adaptive cap | none | Disclosed sibling — isolates the **cap** effect (differs from `TRAIL-PURE-UNCAPPED` only by the cap). |
| `COMBINED-V2A-NOINIT-CAPPED` | V2A legs | structure trail (open weight) | adaptive cap | none | Disclosed sibling — isolates the cap effect for the combined arm. |

PARTIAL-V2A is the chosen combined partial scheme: it was the simplest broad performer in the
capped EXP-059 results, and it uses only fixed favourable price levels (no reversal-event leg),
so the combined arm needs **no** `bench_n`-bounded reversal locator — consistent with "the cap
is not used."

### Endpoint & contrasts

- **Binding endpoint:** median per-event position-weighted gross expectancy (P14, ATR-normalised,
  P15 fills, real prices); per-cell viable iff CI_low > 0 (regime-clustered moving-block
  bootstrap, one-sided 95%) **and** ≥30 qualifying events; composed by **P11** (≥5 cells over
  ≥3 instruments).
- **Binding contrast (vs BENCH):** the arm − BENCH paired-median contrast on the common
  qualifying-event subset (events qualifying under both arms) — the EXP-056/057/058/059 design.
  This measures the value of the uncapped trailing scheme vs the benchmark single fixed exit.
- **Disclosed cap-isolation contrast:** uncapped arm − its capped no-init sibling (paired,
  common subset). Attributes any difference specifically to removing the cap, holding the
  no-init-stop + trailing structure fixed.

### Disclosures (separate from EXP-059)

- **`DATA_CENSORED` for the uncapped arms is disclosed separately** from the capped-arm
  censoring: unbounded windows on late-TRAIN events cannot complete before `train_end_ts`, so
  censoring (and therefore qualifying-count depletion) will be higher than any capped arm.
  Power (≥30 qualifying / cell) is at risk on shallow-history cells → INCONCLUSIVE-by-power is
  a real, disclosed outcome, never defaulted.
- Exit-reason composition per arm (TRAIL fill vs FAV legs vs DATA_CENSORED) is the binding
  mechanism diagnostic.

## 3. Implementation note (binding for Stage 3/4)

The existing `build_active_stops` materialises a **dense** `(n_events, width)` array with
`width = max(n_event) + 1`. Capped, `width ≈ 6`. Uncapped, `width` would become
`max(last_train_idx − entry_idx)` ≈ the full TRAIN length → an `O(n_events × train_len)` matrix
that will blow up memory. **The uncapped resolver must compute the trailing stop lazily inside
the forward scan** (advance the secondary-pivot pointer as bars advance), not via the dense
builder. Add a **new** entry point to `xen.position_exits` (e.g. `resolve_legs_uncapped` /
lazy-stop helper) that (i) ends the scan at `last_train_idx`, (ii) emits no `TIMECAP` class
(only `TRAIL` fill, `FAV` legs, or `DATA_CENSORED` at the edge), and (iii) seeds the stop NaN
(no init) until the first post-entry secondary confirmation. **Do not modify the existing
`resolve_legs`/`build_active_stops`/`_scan_event`** — EXP-059's frozen results depend on them;
add alongside. The per-event scan is `O(last_train_idx − entry_idx)` worst case, not `O(6)` —
budget runtime accordingly (`tqdm`, bounded per-cell memory).

## 4. Slate placement

EXP-059B slots into the 014-B surface as a follow-up read on HYP-012; it does **not** displace
EXP-060 (combined event system, HYP-013), which is reserved for its planned purpose. EXP-059B's
readout joins the full-surface evidence base adjudicated at the single 014-B **G2**; it never
triggers an intermediate gate or closure. Prior context that motivates the read: EXP-057 found
`/ADV-NONE` (no adverse stop at all) beat the benchmark 1:1 — but only under the capped
geometry — so an uncapped trailing adverse is a coherent next question on the same surface.

## 5. Accounting

- **0 candidate slots, 0 TEST reads.** Characterization/diagnostic per the 014-B D0 addendum.
  `/EXIT-TRAIL-UNCAPPED` is registered (countable) but consumes a slot only if a future scope
  activates it as a screening candidate (not before G2 PROCEED_TO_SCREEN, P21).
- **TRAIN only;** all forward windows clipped to `train_end_ts`; TEST and the final-30% global
  holdout are not read. The conditioned population is byte-identical to EXP-053/059 (no new
  stratum opened). TEST-read ledger unchanged.
