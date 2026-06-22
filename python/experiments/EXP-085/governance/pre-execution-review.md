# Pre-Execution Governance Review — EXP-085

**Experiment:** EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate on the EXP-083 Valid-Candidate Set
(CF-CAPGEO-001 Phase 018 / HYP-004 cost read-gate)
**Artifacts reviewed:** `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, `python/src/xen/capgeo_cost.py`
**Governing amendment:** `D0-amendment-002-train-cost-readgate.md`
**Date:** 2026-06-22

---

## Registry / accounting precondition (Stage-1 check, re-verified)

- **CF-CAPGEO-001** is `REGISTERED` / Phase 018 OPEN (`candidate-families/cf-capgeo-001.md`).
- **EXP-085** is registered in `multiplicity-registry.md` (Phase 018 batch, the EXP-085 row): TRAIN-only cost
  read-gate, **0 counted TEST reads / 0 candidate slots**, **no new countable candidate item** (cost layer on
  the registered survivors — EXP-030 precedent). EXP-084 row updated to note it is re-gated behind EXP-085
  `NET_SURVIVES` + ratification. ✔
- **TEST-read ledger** (`test-read-ledger.md`): unchanged; all 48 strata stay 0/2 (TRAIN-only disclosure). The
  experiment reads no TEST stratum. ✔
- Binding pin: the EXP-083 valid-set internal content hash `fa4035f3…` is asserted in code before any market
  read; re-derivation verified to reproduce the pin (n_valid=26). ✔

## Operator ratification at this gate (scope §Cost-model deferral)

The scope froze the cost-model **structure** and deferred the per-instrument **constants** and the
**holding-days definition** to operator ratification at Stage 4. Both ratified 2026-06-22:

- **Constants — ratified as proposed:** AUDUSD 4.0/0.8, NZDUSD 4.5/0.8, USDCAD 4.0/0.7, USTEC 5.0/1.2
  (RT bps / financing bps-per-day); CONSERVATIVE = 2×BASE, anchored to EXP-030/034.
- **Holding-days — ratified as the bar-count proxy:** `holding_days = (exit_idx − entry_idx) × domain_minutes
  / 1440`, over the wall-clock alternative the plan had recommended. The change was routed back through the
  developer pattern (`capgeo_cost.holding_days` + orchestration), re-compiled and unit-verified. This is
  within the scope's predeclared deferral ("operator may adjust at ratification; once ratified frozen before
  the TRAIN read"), **not** scope creep.

Both are now frozen before the TRAIN run, recorded in `run_metadata.json`, and never tuned against outcomes.

---

## Constraint checks

| Constraint | Verdict | Evidence |
|---|---|---|
| **Holdout untouched (OOS §5)** | PASS | Read region = `li.frame.slice(0, int(height*0.7))` on the already-first-70% VAL-005 frame; `CloseTime`-sorted assertion; analysis-TEST + final-30% holdout never sliced. `run_metadata.json` asserts `holdout_untouched/test_stratum_touched/counted_test_reads:0/candidate_slots:0`. |
| **Single falsifiable question (§3)** | PASS | One question: does any of the 26 survivors retain a net per-event edge on TRAIN? Verdict ∈ {NET_SURVIVES, NET_FLAT}, per-stratum. |
| **Real-price discipline (§7)** | PASS | Returns are the frozen real-OHLC ATR-unit exits; cost is price-bps → ATR via `P_entry/ATR_entry`. No synthetic prices. |
| **Look-ahead / causality (§6)** | PASS | Cost applied to the already-resolved exit path; the exit-bar mirrors are causal first-touch (`entry+1..min(cap,last)`), adverse-first P15 tie-break, sequential explicit loops. |
| **Per-stratum verdict (code check, cf-capgeo §137)** | PASS | Binding verdict emitted **per survivor** (`net_verdict` per row); experiment verdict is the **OR** over per-survivor `NET_POS` — not a collapsed `.all()`/pooled flag. Matched-random excess and any aggregate are companion/disclosure only (LESSON-001). |
| **Shape-aware + robust/raw endpoints (plan checks)** | PASS | Co-primary **expectancy AND median** (the median-positive/mean-killed shape that defined CF-HA-HARAMI-001 is exactly what a joint exp∧median read catches); both emitted, robust-vs-raw gap visible. |
| **Gate-threshold calibration (§scope)** | PASS | The binding gate is `CI_low_1s > 0` (no magic threshold). Cost constants are data-anchored (EXP-030/034), disclosed, operator-ratified. Bootstrap `b=max(1,round(m^(1/3)))`, `N_BOOT=10_000` inherited from the frozen kernels. |
| **Complexity budget (§3)** | PASS | 2 stat-method families (`one_sided_lo` exp+med; `two_sample_diff_lo` matched excess — both reused); 3 plots (waterfall, cost decomposition, net-vs-gross); 1 new module (`xen.capgeo_cost`). |
| **No frozen-module edits** | PASS | `capgeo_screen/substrates/geometry/domain_bars/capgeo_exits` untouched; source hashes recorded. Exit-bar recovery is a line-faithful mirror in the new module; resolver calls are intercepted at the `rx` namespace (runtime binding swap in a context manager), not by editing source. |
| **Determinism (§safe-opt)** | PASS | Seeded per-survivor rng; full second pass fingerprint-compared (`determinism_ok`). Reuses deterministic frozen entry/control seeds. |
| **Code organization / standards** | PASS | VAL-001 sectioning; dirs created only in `main()`; tqdm over load + cost-cell loops; helpers return data; bounded single `to_pandas()` for the 3 plots; type hints + docstrings; explicit finite handling (HALT, no silent NaN drop). |
| **NaN / edge handling** | PASS | `event_costs` raises on non-finite/≤0 ATR or negative holding; `mean(cost_ATR) > 0` always (`RT_i > 0`) → no 0/0 in `txn_share`/`fin_share`; cost computed only on the frozen resolved mask. |

---

## Reconciliation safety net (why this design is verdict-safe)

The experiment HALTs before producing any net number unless **three** guards pass:
1. **valid-set sha** re-derives `fa4035f3…` and matches the pin (else HALT);
2. **gross reconciliation** — every survivor's re-resolved `n_resolved == EXP-083` (exact) and gross mean within
   1e-9 of the pinned `gross_exp` (else HALT). This *also* proves the reconstructed `cell_index`/seed grid is
   identical to EXP-083's (a wrong grid would change `make_entrysets` entries → gross would not reconcile);
3. **exit-mirror reconciliation** — the mirror's recomputed `ret`/`cls`/resolved mask match the frozen
   `Resolution` (else HALT) on every resolved event.

## Disclosures (intent-compliant; flagged for the auditor, not blocking)

- **Loads first-70% of all 16 instruments** to reconstruct the EXP-083 deterministic `cell_index`/seed grid
  (the approved `ass_overlay.py` reuse pattern the scope's §Suggested Direction endorses). **Only the 4
  survivor cells are measured/scored**; no non-survivor cell is analyzed; no holdout is read. The scope's "no
  other cells are read" is satisfied in the analytical sense; the grid-reconstruction load is mechanical and
  is caught either way by the gross-reconciliation guard.
- **Exit-bar fidelity** for FAV/ADV touches rests on the mirror being a *line-faithful transcription* of the
  frozen scan (ret-reconciliation alone cannot pin a touch bar since `+t_fav` is bar-invariant). This is the
  **primary audit-focus area**: the auditor should diff `capgeo_cost.{static_barrier,fixed_horizon,
  partial_two_leg}_exit` against `capgeo_screen.resolve_*` for tie-break/window equivalence, and confirm the
  partial's `exit_idx` is leg-2 (final).
- **22/26 survivors are low-n S2-deferred 4h cells (n=44–78):** `NET_INCONCLUSIVE_SPANS_ZERO` is the expected,
  honest per-stratum outcome; binding power sits in AUDUSD-1h (n=988). Not a defect.
- **VP-POC (USDCAD-4h)** carries EXP-083's selection-on-geometry disclosure (POC subsample); cost layer does
  not alter membership.

---

```text
VERDICT: APPROVE
```
