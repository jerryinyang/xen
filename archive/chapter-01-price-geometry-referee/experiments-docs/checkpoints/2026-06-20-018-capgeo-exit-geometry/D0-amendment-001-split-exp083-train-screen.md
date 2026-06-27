# Phase 018 D0-amendment-001 — Split EXP-083 into a TRAIN-only screen + a deferred counted-read confirmation

**Status:** **OPERATOR-DIRECTED 2026-06-22.** Amends the ratified Phase 018 D0
(`D0-predeclarations.md`, G0 PASS 2026-06-21) §D2 slate and §D4/§D5 read accounting **only** in
*where the counted TEST read is spent*. No frozen constant, derivation rule, gate threshold, substrate,
universe, or verdict definition changes. The separability gate (S1/S2), the G-018a screen, the
`derive_barriers` hash-pin, the `WF-EXPANDING` schedule, the frozen referee suite, the 2-lifetime-read
cap, and the Holm-over-`{candidate × stratum}` correction are **all unchanged**; this amendment only
relocates the moment the cap is touched into a separately-ratified experiment.

**Governing design:** `design.md` · **Governing D0:** `D0-predeclarations.md` · **Family:**
`CF-CAPGEO-001` · **Checkpoint:** `2026-06-20-018-capgeo-exit-geometry`.

---

## 1. Why this amendment

The ratified D0 §D2 bundled the whole of HYP-004 into **one** experiment, EXP-083, that (a) screens all
exit candidates on TRAIN (G-018a + separability), then (b) spends **counted TEST read #1** (of the
2-lifetime cap) via a single frozen `WF-EXPANDING` run across every member stratum that carries a valid
candidate.

EXP-082 (`DERIVATION_DELIVERED`, audit PASS) closed by flagging that the derived adverse leg reverts to a
generic `MAE_q90` stop sitting **at** the catastrophe edge `|q05|` in a wide-stop/modest-target geometry —
the **CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" trap geometry reproduced in the derived
exit** — making the **separability gate (S2) the crux**. The S2 gate is **TRAIN-only**. There is therefore
a real, design-anticipated chance that the separability gate eliminates the derived (and/or benchmark)
candidates on TRAIN, in which case the correct number of counted reads to spend is **zero** (the §4
"fail cheaply first" structure).

Spending the **first of two lifetime** counted reads, simultaneously across up to 46 member strata, is
irreversible and is the programme's largest single TEST commitment to date. The operator has directed
(2026-06-22) that the TRAIN-only screen be executed and reviewed **before** that commitment is made.

## 2. The split (binding)

| EXP-ID | Role | Reads | Gate |
| --- | --- | --- | --- |
| **EXP-083** (this slate, amended) | **HYP-004a — TRAIN-only candidate screen.** Apply every exit candidate (the 3 derived `D1`/`D2`/`D3` **and** the full enumerated benchmark grid under `/EXIT-RR`, `/EXIT-TRAIL`, `/EXIT-VP`, `/EXIT-PARTIAL`, `/SIZE-VOLADJ`) to the frozen-substrate held positions on the **TRAIN region only**; run the **G-018a gross screen** (expectancy + median + tail vs `SUB-RANDOM` and the per-cell matched-random null) and the **binding separability gate (S1 ∧ S2)**. Emit, freeze, and **hash-pin** the surviving **valid-candidate set** (`{candidate × stratum}` survivors) **and** the pre-declared Holm correction rule. **Stop before any TEST row.** | **0 counted TEST reads.** TRAIN-only disclosure (EXP-074/075/080/081 precedent). | G-018a + separability (S1/S2). Verdict ∈ {`SCREEN_DELIVERED` (≥1 valid candidate, set frozen), `ALL_CANDIDATES_FAIL` (empty valid set → family routes to G-018 closure)}. |
| **EXP-084** (reserved-conditional; next free ID) | **HYP-004b — counted-read WF confirmation.** Run the single frozen `WF-EXPANDING` confirmation (D5) on **exactly the EXP-083 hash-pinned valid-candidate set**, adjudicated by the frozen referee suite (binding) under the D4 G-018 conjunction, Holm over the frozen `{valid-candidate × stratum}` grid. **This experiment spends counted TEST read #1.** | **1 counted read per member stratum carrying a valid candidate** (D4.1; ≤ 2 lifetime cap honored). | G-018 terminal conjunction (frozen suite ∧ beats-random ∧ separability already passed at EXP-083). |

**EXP-084 is reserved-inactive and conditional** (EXP-036 reserved-inactive precedent): it is scoped and
run **only** if (a) EXP-083 returns `SCREEN_DELIVERED` with a non-empty frozen valid-candidate set, **and**
(b) the operator ratifies spending counted read #1 at EXP-084's own D0/scope. If EXP-083 returns
`ALL_CANDIDATES_FAIL`, EXP-084 is not opened, **0 lifetime reads are spent**, and HYP-004 closes at
G-018 on the TRAIN screen alone. The EXP-084 ID is reserved, never reused for anything else.

## 3. The D4.1 "many candidates, one honest read" legitimacy is preserved — and strengthened

The D4.1 legitimacy condition requires the valid-candidate set **and** the Holm rule to be **frozen and
hash-pinned before any TEST row is read, with no human selection among candidates after seeing TEST.**
The split **satisfies this by construction and makes it auditable**: the freeze/hash-pin is the *output
artifact of EXP-083* (produced with provably zero TEST contact), and EXP-084 imports that pinned set
verbatim and asserts its hash before reading a single TEST row. The screen→freeze→confirm boundary that
D4.1 demanded *within* one experiment is now an *inter-experiment* boundary with an explicit, hash-pinned
hand-off — a stricter, not weaker, guarantee. The 2-lifetime-read cap and the Holm-over-the-full-grid
correction are unchanged and bind at EXP-084.

## 4. What does NOT change (unchanged frozen items)

- Substrates (4, frozen), universe (16 instruments), domains (15m/1h/4h), member set (46 cells), data
  (5-year VAL-005-admitted, holdout-fenced `build_domain_bars`) — D1.
- The frozen `derive_barriers` rule (`xen.capgeo_exits`, sha256-pinned at EXP-082) and the §D3 derivation
  — EXP-083 re-fits barriers on its screen-TRAIN region via the *same* pinned function; EXP-084 re-fits
  per WF fold-TRAIN via the *same* pinned function (causal, no human selection).
- The separability gate S1/S2 and all D9-frozen constants (`K_tail=3.0, τ_tail=0.06, δ=0.40, m=m_cell`,
  S2 operating floor `n≥120`; sub-floor cells get S2 deferred + disclosed) — D4/§D9.
- The frozen referee suite as the binding qualifier at the confirm; `ASS` non-binding discovery overlay
  (G-017 `DISCOVERY_ONLY`) — D4.
- The `WF-EXPANDING` schedule and the D4.1 counted-read rule — D5.
- Co-primary endpoint (expectancy + median + tail, real prices), gross matched-control screen with the
  cost-aware layer deferred to a conditional follow-up (operator decision 2026-06-22), per-stratum
  adjudication default (LESSON-001), determinism/real-price/holdout discipline — D4/§D10.

## 5. Registry / accounting effects

- **Multiplicity registry** Phase 018 batch slate (`multiplicity-registry.md`): the EXP-083 row is amended
  to the TRAIN-only screen (0 counted reads); a reserved-conditional EXP-084 row is added for the counted
  confirmation. No new countable item is created (the derived/benchmark variants were already registered at
  D0); the EXP-ID split consumes **no new candidate slot**.
- **TEST-read ledger** (`test-read-ledger.md`): unchanged by this amendment and by EXP-083 (TRAIN-only
  disclosure). It changes only when EXP-084 runs, if ever.
- This amendment changes the **planned EXP sequence** (registry Amendment Rules) and is recorded here +
  in the registry in the same change, before any EXP-083 measurement.

---

*Companion: `D0-predeclarations.md` (§D2/§D4/§D5/§D9), `design.md` (§3/§4), EXP-082
(`python/experiments/EXP-082/`), `multiplicity-registry.md` Phase 018 batch.*
