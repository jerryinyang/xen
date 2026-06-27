# Phase 018 D0-amendment-002 — Re-sequence the conditional cost layer as a TRAIN-only G-018 read-gate (EXP-085)

**Status:** **OPERATOR-DIRECTED 2026-06-22.** Amends the ratified Phase 018 D0
(`D0-predeclarations.md`, G0 PASS 2026-06-21) §D2 slate **sequencing** and the §D2/§D4 **GROSS-endpoint
deferral** only — it relocates the **already-registered conditional cost-aware follow-up** (§D2 note:
"Conditional cost-aware / portfolio follow-ups register at their own D0 … EXP-072/073 precedent") to run
**TRAIN-only, before the counted-read confirmation (EXP-084)**, as a read-gate on whether spending a
lifetime TEST read is warranted. **No frozen constant, derivation rule, separability/gate threshold,
substrate, universe, member set, referee suite, Holm rule, `WF-EXPANDING` schedule, 2-lifetime-read cap, or
verdict definition changes.** The EXP-083 hash-pinned valid-candidate set (`fa4035f3…`) is read unchanged;
this amendment adds an evaluation layer on those survivors, it does not re-screen or alter them.

**Governing design:** `design.md` · **Governing D0:** `D0-predeclarations.md` (§D2/§D4) · **Prior
amendment:** `D0-amendment-001` (HYP-004 split) · **Family:** `CF-CAPGEO-001` · **Checkpoint:**
`2026-06-20-018-capgeo-exit-geometry`.

---

## 1. Why this amendment

EXP-083 (`SCREEN_DELIVERED`, re-audit PASS, valid set `fa4035f3…`) delivered 26 valid `{candidate ×
stratum}` survivors across 4 cells: **4 S2-PASS** (binding shape-guard cleared) — all conventional arms
(`AVWAP-FH`, `RR-1.5/2/3`) on the single well-powered `SUB-HARAMI-V2A × AUDUSD × 1h` cell (n=988) — and **22
S2-DEFERRED** (binding S2 not evaluated, n<120) across three `SUB-AVWAP` 4h cells (NZDUSD, USDCAD, USTEC).
The screen was **GROSS** (operator decision 2026-06-22, §D2/§D4); the cost-calibrated referee suite was not
invoked.

Two findings make a TRAIN-only cost read-gate the disciplined next step **before** EXP-084 spends counted
read #1 (the programme's largest single irreversible TEST commitment):

1. **The binding survivors clear S2 only via magnitude-unpriced stop-truncation.** The 3 RR S2-passers pass
   the S2 tail-non-residual leg because the fixed `MAE_q90` stop clips the left tail to a point mass at
   **≈ −7.28 ATR per stop-out**; S2 is a *shape* guard (no separated continuous catastrophe mode), not a
   *magnitude* guard. Whether a −7.28-ATR stop tail is survivable net of cost is exactly the open question
   the GROSS screen deferred.
2. **Cost consumed the gross edge in both prior families.** CF-AVWAP-001 (EXP-030: 5m/1h net
   EVIDENCE_AGAINST, 4h INCONCLUSIVE) and CF-HA-HARAMI-001 (EXP-045: 0/37 cells net-positive under frozen
   conservative costs) both produced a real *gross* edge that did not survive realistic cost. Spending a
   scarce lifetime read before pricing cost repeats the pattern that has cost the programme reads before.

The operator has directed (2026-06-22) a **TRAIN-only gross→net cost screen on the full EXP-083 valid set —
all 26 survivors, including the 22 S2-deferred unadjudicated ones — run before EXP-084**, so the counted
read is gated behind the question most likely to eliminate the candidates, **at 0 lifetime reads**.

## 2. The re-sequenced read-gate (binding)

A new experiment is registered (the cost layer is an evaluation re-run of the already-registered survivors —
**no new candidate slot**, EXP-030 precedent):

| EXP-ID | Role | Reads / slots | Verdict |
| --- | --- | --- | --- |
| **EXP-085** (new; next free ID) | **HYP-004 cost read-gate — TRAIN-only.** Apply a predeclared per-event cost/slippage + holding-time financing model (§3) to the realized exit paths of **all 26 EXP-083 hash-pinned valid `{candidate × stratum}` survivors** (the 4 S2-PASS **and** the 22 S2-DEFERRED), on the **TRAIN region only**, and re-evaluate **net** per-event expectancy + median per stratum (moving-block bootstrap one-sided `CI_low`), with the net matched-random excess as a companion. Reads the frozen valid set verbatim; asserts its sha256 `fa4035f3…` first. **Stop before any TEST row.** | **0 counted TEST reads** (TRAIN-only disclosure, EXP-074/075/080/081/082 precedent) / **0 candidate slots** (cost layer on the registered survivors — EXP-030 precedent). | `NET_SURVIVES` (≥1 of the 26 retains net `CI_low > 0` on TRAIN, per stratum) **or** `NET_FLAT` (none) — per-stratum, no pooling as a binding statistic (LESSON-001). |
| **EXP-084** (reserved-conditional; re-gated by this amendment) | **HYP-004b — counted-read WF confirmation** (unchanged definition). Now opens only on **(a) EXP-085 `NET_SURVIVES`** on ≥1 stratum **and (b)** operator ratification at EXP-084's own D0/scope. | 1 counted read per stratum carrying a surviving candidate (≤ 2 lifetime cap) | G-018 terminal conjunction (D4), unchanged. |

**Resulting read-gate sequence:** EXP-083 (TRAIN screen, COMPLETE) → **EXP-085 (TRAIN cost read-gate)** →
**G-018 read decision** → EXP-084 (conditional counted-read confirm, only if `NET_SURVIVES` + ratified). If
EXP-085 returns `NET_FLAT`, **EXP-084 is not opened, 0 lifetime reads are spent, and HYP-004 closes at G-018
on the TRAIN screen + cost gate alone.** EXP-085 evaluates **all 26** survivors so the net picture is
complete: the 22 S2-deferred cells are priced too (they were never magnitude-adjudicated, and the ASS
overlay flagged their gross magnitudes as small-n-inflated), so the read-gate does not silently discard
them.

## 3. Predeclared cost model (structure frozen here; exact constants frozen at EXP-085 Stage-1 before any TRAIN read)

To prevent tuning, the cost model's **structure and binding criterion are frozen now**; the per-instrument
constants are frozen in the EXP-085 `scope.md` **before any TRAIN read**, data-anchored and never tuned
against outcomes (EXP-030/034 framework, extended to the new-universe instruments AUDUSD, NZDUSD, USDCAD,
USTEC):

- **Per-event round-trip transaction cost** (spread + slippage), conservative variant binding (EXP-030
  precedent), **converted to ATR units** to match the screen's ATR-unit returns (`net = gross_ATR −
  cost_ATR` per event).
- **Holding-time financing / carry** on the adverse side, scaled by the realized holding duration of each
  event (EXP-034 financing framework: e.g. per-instrument bps/day, adverse-side).
- **Binding read:** net per-event **expectancy** `CI_low_1s > 0` **and** net **median** `CI_low_1s > 0` per
  stratum (moving-block bootstrap), read jointly with the net matched-random excess companion. Co-primary
  expectancy + median (D4), real prices, per-stratum (no pooling).
- **Units / discipline:** real prices only (`RealOpen/High/Low/Close`); ATR(14) normalization (EXP-081);
  causal (cost applied on the already-resolved exit path; no look-ahead); deterministic seeds; holdout
  never read; TRAIN sub-split `[0, int(analysis_rows·0.7))` only.

This is a **gross→net robustness gate, not a confirm**: the frozen referee suite and any TEST/holdout
contact remain at EXP-084. EXP-085 introduces **no new candidate** and **no new hypothesis** — it is the
cost-robustness extension of the HYP-004a TRAIN screen on the registered survivors.

## 4. What does NOT change (unchanged frozen items)

- The EXP-083 hash-pinned valid-candidate set (`fa4035f3…`) and the Holm-over-`{valid-candidate × stratum}`
  rule — read verbatim, not modified.
- Substrates, universe (16), domains, member set (46), 5-year VAL-005 data + holdout-fenced
  `build_domain_bars`, the `derive_barriers` pin, the separability gate S1/S2 and all D9 constants
  (`K_tail=3.0, τ_tail=0.06, δ=0.40`, floor `n≥120`) — D1/D3/D4/§D9.
- The frozen referee suite as the binding qualifier at the confirm; `ASS` non-binding (G-017
  `DISCOVERY_ONLY`); the `WF-EXPANDING` schedule and the D4.1 counted-read rule; the **2-lifetime-read cap**
  and **0 reads spent so far** — D4/D5.
- The G-018 terminal verdict conjunction (frozen referee suite ∧ beats matched-random ∧ separability) — D4.
  EXP-085 is a **read-gate input** to the operator's G-018 decision; it does not itself close or open the
  family.

## 5. Registry / accounting effects (recorded in the same change, before any EXP-085 measurement)

- **Multiplicity registry** Phase 018 batch (`multiplicity-registry.md`): add an **EXP-085** row (TRAIN-only
  cost read-gate; 0 reads / 0 slots; **no new countable candidate item** — the cost layer was a registered
  conditional follow-up, here re-sequenced earlier; the EXP-030 "cost layer on the registered baseline
  consumes no slot" precedent applies). Update the **EXP-084** row to note it is now gated behind EXP-085
  `NET_SURVIVES` + ratification.
- **TEST-read ledger** (`test-read-ledger.md`): **unchanged** by this amendment and by EXP-085 (TRAIN-only
  disclosure); all 48 strata stay 0/2 open. It changes only if EXP-084 runs, if ever.
- This amendment changes the **planned EXP sequence** (registry Amendment Rules) and is recorded here + in
  the registry in the same change, before any EXP-085 measurement.

---

*Companion: `D0-predeclarations.md` (§D2/§D4), `D0-amendment-001` (HYP-004 split), EXP-083
(`python/experiments/EXP-083/` — report · results.md [§ASS overlay] · audit.md), `multiplicity-registry.md`
Phase 018 batch.*
