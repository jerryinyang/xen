# Analysis Plan: Experiment EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate on the EXP-083 Valid-Candidate Set

**Phase:** 018 (CF-CAPGEO-001) · **HYP:** HYP-004 cost read-gate (D0-amendment-002) · **Mode:** TRAIN-only,
0 counted TEST reads, 0 candidate slots · **Governing scope:** `python/experiments/EXP-085/scope.md` ·
**Governing amendment:** `docs/experiments-docs/checkpoints/2026-06-20-018-capgeo-exit-geometry/D0-amendment-002-train-cost-readgate.md`

---

## Objective

Decide, **on TRAIN only**, whether **any** of the 26 EXP-083 hash-pinned valid `{candidate × stratum}`
survivors retains a **net** per-event edge once a predeclared conservative cost/slippage + holding-time
financing model is subtracted, or whether realistic cost consumes the gross edge as it did in CF-AVWAP-001
(EXP-030) and CF-HA-HARAMI-001 (EXP-045). The result is a **read-gate input** to the operator's G-018
decision (NET_SURVIVES → EXP-084 read-eligible pending ratification; NET_FLAT → HYP-004 closes at G-018 with
0 lifetime TEST reads spent). It is **not** an edge/tradability/confirm verdict — no referee suite, no
`WF-EXPANDING`, no TEST/holdout contact.

**Binding verdict (per-stratum, no pooling — LESSON-001):**
`NET_SURVIVES` iff ≥1 of the 26 survivors clears **net expectancy `CI_low_1s > 0` AND net median
`CI_low_1s > 0`**; else `NET_FLAT`.

---

## Frozen inputs and provenance (assert BEFORE any net number)

| Item | Value / source |
|---|---|
| Candidate set | `python/experiments/EXP-083/results/valid_candidate_set.json` — 26 members, read verbatim |
| Binding pin | **internal** field `sha256 = fa4035f371a2ada656f05d697b709be48559e6a5ad322526f45dbbfccd8f3126` (a content hash over the canonical 26-member list — **not** the whole-file hash; re-derive the canonical serialization EXP-083 hashed and assert equality) |
| Survivor strata | AUDUSD-1h (`SUB-HARAMI-V2A`, n=988, **S2-PASS**); NZDUSD-4h, USDCAD-4h, USTEC-4h (`SUB-AVWAP`, n=44–78, **S2-DEFERRED**) |
| Read region | TRAIN sub-split `[0, int(analysis_rows·0.7))` of each cell's **first-70%** analysis slice (identical to `ass_overlay.py` line 235: `train_frame = li.frame.slice(0, int(li.frame.height*0.7))`). Analysis-TEST stratum and final-30% holdout **never** sliced/materialized/inspected |
| Frozen modules (record hashes, unchanged from EXP-083) | `xen.capgeo_screen`, `xen.capgeo_substrates`, `xen.capgeo_geometry`, `xen.domain_bars`, `xen.capgeo_exits` |
| Reuse harness | EXP-083 `run_experiment.py` imported as a module (the `ass_overlay.py` pattern, lines 70–78, 210–241); re-resolve survivors via `resolve_cell_returns`-style assembly using `rx._path_inputs` / `rx.build_candidates` |
| Bootstrap kernels | `xen.capgeo_screen.one_sided_lo` (expectancy + median, one-sided 95% lower); `xen.capgeo_screen.two_sample_diff_lo` (matched-random excess) |
| Bootstrap config | moving-block `b = max(1, round(m**(1/3)))`, `N_BOOT = 10_000`, one-sided 95% `CI_low`, fixed recorded seed, second pass byte-identical |
| Units | ATR (Wilder ATR(14), the EXP-081 normalization) — costs converted to ATR units to match the screen's ATR-unit returns |

---

## Predeclared cost model (frozen structure; constants pending operator ratification at Stage 4)

Per **resolved** event `e` of a survivor on instrument `i`:

```
cost_txn_ATR_e = (RT_i / 1e4) * P_entry_e / ATR_entry_e
cost_fin_ATR_e = (F_i  / 1e4) * holding_days_e * P_entry_e / ATR_entry_e
cost_ATR_e     = cost_txn_ATR_e + cost_fin_ATR_e          # always > 0  (RT_i > 0)
net_ATR_e      = gross_ATR_e - cost_ATR_e                 # identical events, same ATR denominator
```

- `P_entry_e = close[entry_idx_e]` — the entry domain-bar close (= `c0` in every frozen resolver). Price units.
- `ATR_entry_e = pin.atr_entry[e]` — **reuse the exact array** the screen used (do not recompute). Price units, > 0 on every resolved event (the resolver excludes ATR≤0 events).
- `gross_ATR_e = cand_full.ret[cand_full.resolved][e]` — the frozen realized ATR return.
- `holding_days_e` — **wall-clock** calendar days between entry and final exit (see §"Holding duration", below).

**Proposed constants (CONSERVATIVE = 2×BASE binding; PENDING OPERATOR RATIFICATION at Stage 4):**

| Instrument | RT_i (bps, round-trip) | F_i (bps/day, adverse financing) |
|---|---|---|
| AUDUSD | 4.0 | 0.8 |
| NZDUSD | 4.5 | 0.8 |
| USDCAD | 4.0 | 0.7 |
| USTEC  | 5.0 | 1.2 |

Frozen as module-level constants in `xen.capgeo_cost`, recorded verbatim in `run_metadata.json`, never
tuned against EXP-085 outcomes. One round-trip charge per event; nothing amortized (scope §1). Financing is
always a **cost** (subtracted), charged on holding duration regardless of trade direction or P&L sign —
never credited.

---

## Methodology

### Step 0 — Provenance + sha assertion (process-level HALT on failure)

- **Method:** Load `valid_candidate_set.json`; re-derive the canonical serialization of its 26 members the
  way EXP-083 hashed them (the `members` list; reproduce key order / number formatting EXP-083 used) and
  assert `sha256 == fa4035f3…`. Record the 5 frozen-module source hashes and assert they match the EXP-083
  record.
- **Why:** The whole gate reads a frozen artifact; a silent drift of the candidate set or a frozen module
  invalidates every net number. Assert before any market read.
- **Output:** `sha_ok = True`; module-hash dict. Any mismatch → **HALT**, route to fix (no read).

### Step 1 — Re-resolve the 26 survivors on TRAIN (gross reconciliation, EXP-042 same-denominator)

- **Method:** For each of the 4 survivor cells, reuse the EXP-083 orchestration exactly as `ass_overlay.py`:
  load first-70% via `rx._load_val005().load_first70`, take `train_frame = frame.slice(0, int(height*0.7))`,
  `bars = rx.build_domain_bars(train_frame, period)`, `ohlc = rx._real_ohlc(bars)`,
  `atr = rx.wilder_atr(...)`, `es = rx.make_entrysets(bars, inst, domain, cell_index)`,
  `pin = rx._path_inputs(bars, inst, domain, sub, es[sub], ohlc, atr)`,
  `cand_map = rx.build_candidates(pin, stats, atr_med)`. Extract `cand_full.ret[cand_full.resolved]` for each
  survivor candidate. **Cell index / seeds must be rebuilt over the same member grid** as EXP-083 (ass_overlay
  lines 213–227) so `make_entrysets` reproduces identical entries.
- **Reconciliation (binding, HALT on failure):** per survivor assert (a) `n_resolved == EXP-083 n_resolved`
  (exact); (b) re-resolved gross **mean** within `1e-9` of `valid_candidate_set.json` `gross_exp`; (c) the
  `resolved` boolean mask is identical to the frozen one. This is the EXP-042 same-denominator invariant — the
  cost layer must score the **identical** event set.
- **Output:** per-survivor frozen arrays `{gross_ret, entry_idx, atr_entry, direction, ohlc, bars.CloseTime}`.

### Step 2 — Recover the per-event exit bar (the new `xen.capgeo_cost` module; reconciliation-guarded)

> **This is the central implementability constraint.** The frozen resolvers (`resolve_static_barrier`,
> `resolve_partial_two_leg`, `resolve_fixed_horizon`) compute the exit bar `k` internally but **return only
> `ret/cls/resolved`** — the exit index is discarded. The financing leg needs realized holding duration, so
> the exit bar must be recovered. We may **not** edit any frozen module (hash assertion). Therefore the one
> budgeted new module `xen.capgeo_cost` supplies **exit-bar-returning mirrors** of exactly the resolver
> families the 26 survivors use, then **binds them with a reconciliation guard**.

- **Survivor exit families (only three):**
  - `AVWAP-FH` → `resolve_fixed_horizon`: exit bar is deterministic `hi = min(entry_idx + h_cap, last)` — **no
    scan needed**; recover directly.
  - `RR-1/1.5/2/3`, `D1/D2/D3`, `VP-POC` → `resolve_static_barrier`: exit bar = first-touch `k` (FAV or ADV,
    adverse-first P15 tie-break) else `hi` at time-cap.
  - `PARTIAL-V2A`, `V2A-ADVNONE` → `resolve_partial_two_leg`: leg-1 exit at the favourable touch, leg-2 exit
    at stop/cap; the **final** exit bar = leg-2's bar (see §"Holding duration").
- **Method:** In `xen.capgeo_cost`, mirror each family's causal first-touch scan **byte-for-byte in tie-break
  order** (adverse-first; read only `entry+1..min(cap,last)`), returning `exit_idx_e` (and `leg1_idx_e`,
  `leg2_idx_e` for partial) **and the same realized `ret`**. To minimize divergence risk, key the search off
  the frozen per-event `cls` where possible (e.g. if `cls==FAV` find the first FAV touch; if `cls==ADV` the
  first ADV touch; if `cls==TIMECAP` exit = `hi`).
- **Reconciliation (binding, HALT on failure):** assert the mirror's recomputed realized return reproduces the
  frozen `Resolution.ret` within `1e-9` for **every** resolved event of every survivor, and that the recovered
  `resolved` mask is identical. Passing this guard proves `exit_idx_e` is the bar the frozen resolver actually
  exited on — the only correctness evidence that the recovered holding duration is faithful.
- **Why a new module (not inline):** the mirror reproduces sequential causal scan logic with an exact
  tie-break; it is genuinely new computation that cannot be composed from existing kernels, and it is the
  scope-sanctioned ≤1 new module (`xen.capgeo_cost`). It performs **no** I/O, **no** RNG, **no** entry/exit
  *selection* — it only recovers the exit index of an already-frozen resolution.

### Step 3 — Per-event cost and net return

- **Method:** Apply the §cost-model arithmetic per resolved event. `holding_days_e` per §"Holding duration".
  Compute `cost_txn_ATR_e`, `cost_fin_ATR_e`, `cost_ATR_e`, `net_ATR_e`. Pure vectorized arithmetic over the
  resolved-event arrays (safe — no temporal/causal semantics changed; cost is applied to the **already-resolved**
  path, no look-ahead).
- **Finite handling (explicit):** operate only on the frozen `resolved` mask; `ATR_entry_e > 0` guaranteed.
  Any non-finite `P_entry`/`ATR`/`holding` → exclude with record (none expected; if any occur it is a Step-1/2
  reconciliation failure → HALT, not a silent drop).
- **Output:** per-survivor arrays `{gross_ATR, cost_txn_ATR, cost_fin_ATR, cost_ATR, net_ATR, holding_days}`.

### Step 4 — Per-stratum net inference (binding)

- **Method:** Per survivor, with a fixed seeded `rng`:
  - `net_exp, net_exp_lo = one_sided_lo(net_ATR, rng, kind="mean")`
  - `net_med, net_med_lo = one_sided_lo(net_ATR, rng, kind="median")`
- **Why this method:** moving-block bootstrap one-sided lower bound is the **same kernel EXP-083 used** —
  distribution-free, respects entry-ordering serial dependence via the block, no normality/i.i.d. assumption
  (Programme Principles). Simpler alternative (t-interval / sign test) rejected: assumes normality / discards
  the block-dependence the screen already standardized on. No new method type.
- **Per-survivor verdict** (uses the one-sided lower bound + the point estimate; both legs co-primary):
  - `NET_POS` iff `net_exp_lo > 0` **AND** `net_med_lo > 0`.
  - `NET_NEG` iff `net_exp < 0` **AND** `net_med < 0` (point estimates both negative — clearly net-losing).
  - `NET_INCONCLUSIVE_SPANS_ZERO` otherwise (a leg's point ≥ 0 but its `CI_low ≤ 0`, or legs disagree —
    cannot reject zero from below). **Expected** for the low-n S2-deferred 4h cells (n=44–78, wide CIs);
    recorded, never silently dropped, neither survivor-by-default nor failure.

### Step 5 — Net matched-random excess (companion / disclosure — NOT binding)

- **Method:** For each survivor, reproduce the screen's per-cell **matched-random** control (same
  `make_entrysets` random arm, same `cell_index`/`SEED_RANDOM`) and resolve the **same candidate exit** on it
  via the frozen resolver; recover its exit bars via the Step-2 mirror; apply the **identical** cost constants
  to both arms. Then
  `net_matched_excess_lo = two_sample_diff_lo(net_candidate, net_control, rng, kind="mean")`.
- **Why two-sample (independent), not paired:** candidate and control are **different** entry sets → the
  `two_sample_diff_lo` (independent moving-block resample of each arm) is the correct kernel, matching EXP-083.
- **Status:** companion only. The binding leg is net-positive expectancy (the tradability question). Reconcile
  the control's **gross** matched excess to EXP-083's stored value where persisted (disclosure of fidelity).

### Step 6 — Determinism replay + accounting

- **Method:** Run the full pipeline twice with the recorded seed; assert the two `cost_readgate` tables are
  byte-identical. Assert `holdout_untouched=True`, `test_stratum_touched=False`, `counted_test_reads=0`,
  `candidate_slots=0`.
- **Output:** `determinism_ok`, accounting flags in `run_metadata.json`. Failure → HALT.

---

## Holding duration (predeclared; flag for operator confirmation at Stage 4)

`holding_days_e = (CloseTime[final_exit_idx_e] − CloseTime[entry_idx_e]).total_seconds() / 86400`, using the
**domain-bar `CloseTime`** timestamps (wall-clock calendar days).

- **Rationale:** the scope/amendment text is "the resolved **exit time minus entry time** in days" — the
  faithful reading is the wall-clock timestamp difference, which correctly counts weekend/gap calendar time
  that an FX/index financing (carry/swap) charge accrues over. The parenthetical "(domain bars → minutes →
  days)" describes how the timestamps are sourced (domain bars), not a bar-count proxy.
- **Alternative reading (flag):** `holding_days = n_bars_held × domain_minutes / 1440` (pure bar-count).
  This **undercounts** calendar time across weekends/gaps → understates financing → less conservative. **Flag
  for Stage-4 operator ratification**; whichever is ratified is frozen before the TRAIN read. Recommend the
  wall-clock form.
- **Partial two-leg duration:** single financing duration = entry → **leg-2 (final) exit** (the bar the full
  position closes). Conservative (longest holding → highest financing). One round-trip RT charged once per
  event per scope §1 (the scale-out leg-1 fill is **not** separately charged — a disclosed simplification
  faithful to the frozen "one round-trip per event" rule). **Flag**; alternative (leg-fraction duration
  weighting) noted, not recommended (less conservative, adds a denominator choice).
- **Zero-duration:** every exit is ≥ `entry+1` (`lo = i+1`), so `holding_days_e > 0` always; the scope's
  zero-duration→zero-financing branch is defensive and will not trigger here (assert `holding_days_e ≥ 0`).

---

## Output schema (per scope §Data Requirements)

### `results/cost_readgate.parquet` / `.csv` — one row per survivor (26 rows)

| Column | Meaning |
|---|---|
| `substrate, instrument, domain, candidate` | survivor key |
| `s2_deferred` | bool (4 PASS False, 22 DEFERRED True) |
| `n_resolved` | == EXP-083 (asserted) |
| `gross_exp, gross_med` | reconciled gross expectancy / median (ATR) |
| `holding_days_mean` | mean realized holding (calendar days) — transparency |
| `cost_atr_mean` | mean total per-event cost (ATR) |
| `txn_share` | `mean(cost_txn_ATR) / mean(cost_ATR)` over resolved events |
| `fin_share` | `mean(cost_fin_ATR) / mean(cost_ATR)` (= 1 − `txn_share`) |
| `net_exp, net_exp_lo` | net expectancy point + one-sided 95% lower bound (ATR) |
| `net_med, net_med_lo` | net median point + one-sided 95% lower bound (ATR) |
| `net_matched_excess_lo` | companion net matched-random mean-excess lower bound (ATR) |
| `net_verdict` | `NET_POS` \| `NET_INCONCLUSIVE_SPANS_ZERO` \| `NET_NEG` |

> **Share denominator:** `mean(cost_ATR) > 0` always (`RT_i > 0`) → no `0/0`; `txn_share, fin_share ∈ [0,1]`,
> sum to 1 by construction. Define both shares on the **mean** total cost over the survivor's resolved events.

### `results/valid_net_set.json`

The read-eligible subset = the `NET_POS` survivors, with provenance (EXP-083 sha, frozen-module hashes,
cost constants, seeds) **and the explicit note that it authorizes nothing** until operator ratification at
EXP-084's own D0. Empty list if `NET_FLAT`.

### `results/run_metadata.json`

Frozen cost constants (RT_i/F_i table), `holding_days` definition ratified at Stage 4, seeds, frozen-module
hashes, EXP-083 sha assertion result, `reconciliation_ok` (gross + exit-mirror), `determinism_ok`,
`holdout_untouched: true`, `test_stratum_touched: false`, `counted_test_reads: 0`, `candidate_slots: 0`,
and the experiment verdict `NET_SURVIVES` / `NET_FLAT`.

---

## Visualisations (≤ 3)

1. **Gross→net expectancy waterfall** — per survivor (26): gross_exp marker → net_exp with `net_exp_lo`
   whisker, against the **zero line**, grouped by cell, S2-PASS vs S2-DEFERRED distinguished. *Answers the
   binding question: which survivors keep `net_exp_lo > 0`.*
2. **Cost decomposition (stacked bar)** — per survivor: mean `cost_txn_ATR` vs `cost_fin_ATR` (ATR units),
   ordered by total cost. *Answers: how much of the cost is financing — diagnoses whether long 4h holds are
   financing-dominated, the magnitude the −7.28 ATR stop geometry must overcome.*
3. **Net-vs-gross scatter** — x = `gross_exp`, y = `net_exp`, with the `net = 0` horizontal and the
   `gross = net` diagonal; point size ~ √n, colour by `net_verdict`. *Answers: how far cost moved each
   survivor and which cross zero.*

All plots are built from the bounded `cost_readgate` table (no re-load/regeneration for plotting).

---

## Interpretation Guide (pre-defined, before results exist)

- If **≥1 survivor is `NET_POS`** (`net_exp_lo > 0` **and** `net_med_lo > 0`): verdict **`NET_SURVIVES`**.
  The `NET_POS` subset is the read-eligible set for a *possible* EXP-084 counted read — **opened only on
  additional operator ratification at EXP-084's D0**. EXP-085 authorizes nothing itself.
- If **0 survivors are `NET_POS`**: verdict **`NET_FLAT`** — realistic cost consumed the gross edge (the
  EXP-030/045 pattern reproduced on this family). HYP-004 closes at G-018 on the TRAIN screen + cost gate;
  **EXP-084 is never opened and 0 lifetime TEST reads are ever spent.** A real, publishable result.
- A survivor whose net CI spans zero is **`NET_INCONCLUSIVE_SPANS_ZERO`** — the expected, honest outcome for
  the low-n (n=44–78) S2-deferred 4h cells; it is neither a pass-by-default nor a failure, and it does not by
  itself produce `NET_SURVIVES` (only a `NET_POS` does). The binding statistical power sits in the single
  well-powered AUDUSD-1h cell (n=988).
- **No pooled/portfolio net statistic is binding** (LESSON-001). Any cross-survivor aggregate is disclosure
  only; the verdict is the OR over per-survivor `NET_POS`.
- **No edge / tradability / confirm claim** is made here (0 reads, no referee suite) — only TRAIN-only
  net-survival eligibility feeding the operator's G-018 read decision.

---

## Methodological risks / flags (for the developer and Stage-4 governance)

1. **Exit-bar recovery is mandatory and divergence-prone (highest risk).** The frozen resolvers do not expose
   the exit index; `xen.capgeo_cost` must mirror the causal first-touch + **adverse-first (P15)** tie-break
   exactly. The **binding reconciliation guard** — recovered return reproduces frozen `Resolution.ret` within
   `1e-9` on every resolved event — is the sole correctness evidence; a HALT-on-mismatch is required. Keying
   the search off the frozen `cls` reduces divergence risk.
2. **`holding_days` definition** — wall-clock CloseTime difference (recommended) vs bar-count proxy. Flag for
   Stage-4 ratification; freeze before the TRAIN read.
3. **Partial two-leg holding duration** — single financing on entry→leg-2(final) exit (conservative); one RT
   per event per scope; leg-1 scale-out not separately charged (disclosed). Flag.
4. **Financing sign** — always a subtracted cost on holding duration, never credited, direction-agnostic.
   Verify in code.
5. **ATR/entry-price consistency** — reuse `pin.atr_entry` and `close[entry_idx]`; do not recompute ATR or
   entry price by a different path (would break the shared ATR-unit denominator with the screen).
6. **Matched-random companion is independent (not paired)** and uses the identical cost on both arms;
   companion/disclosure only.
7. **Low-n S2-deferred cells (n=44–78)** → wide CIs → `NET_INCONCLUSIVE_SPANS_ZERO` expected; honest, not a
   failure. **VP-POC (USDCAD-4h, n=44)** carries EXP-083's selection-on-geometry disclosure (scored on the
   favourable-side-POC subsample); the cost layer does not alter membership.
8. **Cost constants pending operator ratification** (Stage 4) — frozen as `xen.capgeo_cost` constants,
   recorded in `run_metadata.json`, never tuned against outcomes.

---

## Implementation safety constraints (for `experiment-developer`)

- **TRAIN slice only:** `train_frame = li.frame.slice(0, int(li.frame.height*0.7))` on the already-first-70%
  frame; **never** slice/inspect the analysis-TEST stratum or the final-30% holdout.
- **Reuse frozen building blocks** (`rx._path_inputs`, `rx.build_candidates`, `rx.wilder_atr`,
  `rx.make_entrysets`, `rx.build_domain_bars`, the resolvers) — the only new code is the exit-bar mirror +
  cost arithmetic + orchestration. **No edit to any frozen module.**
- **Sequential causal scans stay explicit** in the mirror (no vectorization that could reorder the
  adverse-first tie-break). Cost arithmetic over resolved-event arrays may be vectorized (no causal/temporal
  semantics involved).
- **Timestamps:** use domain-bar `CloseTime` for holding duration; never bar indices across views.
- **Bounded:** 26 survivors × 10k-resample bootstrap; `tqdm` over survivors. No directory creation at import;
  create `results/`/`plots/` only in `main()`. Helpers return data; concise logging.
- **Determinism:** fixed recorded seed (reuse `rx.SEED_BOOT` or an EXP-085 constant); second pass
  byte-identical.
- **No silent drops:** every excluded event is a reconciliation failure → HALT, not a filter.

---

## Complexity Check

- **Statistical-method families:** 2 / 2 — (1) `one_sided_lo` net expectancy + median; (2)
  `two_sample_diff_lo` net matched-random excess. Both reused from `xen.capgeo_screen`; no new test type.
- **Visualisations:** 3 / 3 — gross→net waterfall; cost decomposition; net-vs-gross scatter.
- **New code modules:** 1 / 1 — `xen.capgeo_cost` (exit-bar mirror + per-event `cost_ATR`). Justified: the
  exit index is not exposed by any frozen module and the financing leg requires realized holding duration.
