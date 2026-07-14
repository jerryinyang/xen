# INFR-009 — XENA Adjudication Redesign

**Type:** INFR-class programme task (adjudication layer only)  
**Status:** **P5 COMPLETE** — net-path amendment (flat RT 1.0 bps) + re-VAL **PASS** + **route RESTORED**  
**Binding design:** `.ignore/temp/cons/consolidated-03.md`  
**Supersedes:** INFR-006 frozen registry v3 (absolute extensive-F binders) — **do not delete**  
**Default route:** **RESTORED** under `results/pc_frozen_registry.json` (v2 / P5 pin)  

---

## 1. One falsifiable question

Can the XENA adjudication layer be rebuilt by **subtraction** — intensive portfolio
turnover-edge + pre-search economics + evidence package, without absolute extensive-F
scalars or the HARD permutation battery — so that:

1. score explosion with cadence/band/compounding is structurally impossible;
2. day-one economics (XENA-003 archetype) surface before search;
3. no binder re-pins an absolute log-wealth scale;

…while leaving LCB calibration (P3), freeze/default-route restore (P4), and cost-aware
search (P5) as **operator-gated** follow-ons?

**Mechanism (why the old referee failed):** one root error — extensive log-wealth F treated
as intensive — produced A1/A2/A3 (dead scalars), B1–B3 (cadence/cost fragility), D1/D2
(composition screens on the wrong object). Audit: `.ignore/sofar/02-flaws-and-redesign/post-xena-infr-audit.md`.

---

## 2. Object identity

| Declaration | Value |
|---|---|
| Layer | `python/src/xen/xena/*` adjudication only |
| Measurement object | Portfolio subset S under full shared-capital oracle (unchanged) |
| Binding score (P1) | Intensive gross turnover-edge \(g_\mathrm{gross}\) on **admitted** legs |
| Not redesigned | Emission, oracle mechanics, estimand gate, holdout/causality fences, Rust kernel |

---

## 3. Estimand / binding statistic (fixed once)

```
g_gross(S,W) = 1e4 · Σ_{ℓ∈A(S,W)} PnL_gross_ℓ  /  Σ_{ℓ∈A(S,W)} |notional_entry_ℓ|
```

- `A(S,W)` = trades admitted by the full oracle for subset S on window W  
- notional_entry = Units · EntryPrice · money_per_unit  
- Search / folds use **identical** definition; bootstrap = common-block P25 of g_gross  
- Net companion: same denominator, NetMoney numerator (cost-charged) — evidence until P3  
- **Denominator decision before CAL:** entry-notional (this design). Risk-notional alternative needs operator sign-off before P3 — never vary silently  

Log-wealth F remains computable for secondary evidence; **not binding**.

---

## 4. Authorized scope (stop conditions)

| Phase | Change | Stop condition |
|---|---|---|
| **P0** | Q1 `economics_disclosure` + cost-map integrity (E3) | Fixtures recompute p50(mean RealizedBps) ≈ **+0.043 / −0.284 / +1.91** bps (see §8 provenance); missing pin refuses search without deleting candidates |
| **P0′** | High-cadence random-entry null generator (§5) | Entry edge ≈ 0; cadence matches 003 class |
| **P1** | `g_gross` search/rank/fold; certification → evidence package; retire absolute binders | No F_floor/Hamming/resim/S as binder; filter-helpful planted case not cadence-displaced |
| **P2** | Retire HARD permutation battery; mandatory print/path decomposition | Grid vs limit fixtures show expected decompositions |

**NOT authorized:** P3 CAL numbers, P4 freeze/default-route, P5 cost-aware search.  
**Never:** invent/tune/freeze calibration floats; call `run_final_gate` on live universes; read TEST/holdout; tune against XENA-001/002/003.

---

## 5. Architecture (target; P0–P2 subset)

```
emission + integrity (unchanged)
    ▼
Q1  economics_disclosure  (P0) — discloses; never drops candidates
    │  incomplete cost map → INTEGRITY_INCOMPLETE → search+gate refused
    ▼
LAHC on P25(g_gross)  (P1) — generator only; charge_costs=False (A-1 cost policy)
    ▼
EVIDENCE PACKAGE (P1+P2) — not a threshold pile
   ├─ random-subset ref (+ S, percentile) — EVIDENCE ONLY
   ├─ Jaccard / core / spread
   ├─ ubiquity + enrichment
   ├─ delete-one / keystone
   ├─ print-vs-path fill-basis (P2)
   └─ eval count + distinct-subset count
    ▼
[P3+] LCB gate + taxonomy — NOT IN THIS MANDATE
```

---

## 6. Audit-closure matrix (carry from §9)

| Item | Closure in P0–P2 | Residual |
|---|---|---|
| A1 F_floor dead | retired from binding path | — |
| A2 gate scalar | retired; LCB deferred to P3 | P3 |
| A3 resim vacuous | retired as binder; intensive fold units | — |
| B1 cadence max | g_gross turnover-normalised | — |
| B2 conditioning | Q1 slices + intensive objective | — |
| B3 gross/net inversion | net disclosed; selection still costless | §6.1 / P5 operator |
| C1 limit basis | battery retired; print/path | — |
| C2 bar-close decrowding | independent rotation retired | — |
| D1/D2 composition | delete-one + Jaccard evidence, not conjunction | — |
| E1/E2 premature freeze/default | default route stays SUSPENDED | P4 |
| E3 unenforced pins | cost map integrity hard | — |
| E4 no cheap economics | Q1 mandatory | — |
| F R_max vs DD | not reconciled here | P3 operator pair |
| binder validation | form fixed; coverage unproven | §6.3 / P3 stop-condition |
| multiplicity | package carries counts | §6.2 |

---

## 7. Registered open risks (named owners)

| Residual | Owner | Notes |
|---|---|---|
| §6.1 B3 selection still costless | operator | P5 only if decisive after P1 |
| §6.2 cross-universe multiplicity | programme | family conclusions must discount |
| §6.3 LCB coverage unproven | P3 CAL | stop-condition if coverage fails |
| §6.4 cost-floor / MDE density formula | operator + design | **DRAFT below — not frozen** |
| A-1 implementation amendment (intensive vs total-wealth) | operator sign-off | costless-selection **policy** kept |
| (R_max, DD) policy pair | operator | never raise limit to pass history |
| Denominator: entry- vs risk-notional | operator before CAL | pin once |

### §6.4 DRAFT cost-floor formula (not frozen)

```
# DRAFT — for Q1 disclosure context only. Do not hash-pin.
# RT cost amortised into a bps/leg survival floor at live density:
#
#   floor_bps ≈ cost_bps_rt / max(1, expected_holds_per_round_trip)
#             + financing_bps_per_leg(hold, rate)
#
# Density-aware restatement of WS-6 "20–40 bps" band:
#   MDE_leg(density) = MDE_ref × sqrt(n_ref / n_live)   # power sketch only
#
# Freeze procedure + numbers only after operator-signed CAL power curve.
```

---

## 8. Acceptance protocol (no fixture tuning)

**Q1 statistic (binding for P4 VAL):** universe-level **p50 of per-candidate mean
`RealizedBps`** on the pre-registered TRAIN search band
`(2021-06-02T00:01Z, 2023-03-08T00:00Z)`, non-censored legs only. Computed by
`xen.xena.economics.economics_disclosure` / `results/verification.json` (INFR-009 P0).

| Fixture | Q1 p50 target (recomputed) | Intent |
|---|---|---|
| XENA-001 | **≈ +0.043 bps** (near zero) | no deployment credit |
| XENA-002 | **≈ −0.284 bps** (sub-zero / sub-floor) | no credit |
| XENA-003 | **≈ +1.910 bps** | real gross; print-path limit-print dominance; sub-cost archetype |

**Provenance.** Earlier proposal/consolidation tables cited −0.065 / +0.085 / +1.91
without a local full-universe scan (XENA-001/002 reports echoed that sketch). Honest
INFR-009 recompute (`results/verification.json`, 2026-07-13) supersedes 001/002 table
cells; **003 matches 1.91**. Do not re-tune code to hit the old sketch — P4 blind VAL
checks against **this** table.

**Sampling noise:** |p50 − target| ≤ ~0.15 bps is within expected variation for 001/002;
003 should stay within ~0.05 of 1.91.

**Redesign rejected if** (full protocol; P4 VAL): credits 001/002 as tradable; collapses 003’s real gross diagnosis; reintroduces absolute extensive-F binder.

---

## 9. A-1 amendment flag (implementation only)

| Clause | Status |
|---|---|
| Costless selection (`charge_costs=False` in search/cert) | **KEPT** |
| Gross/net separation | **KEPT** |
| Implementation claim “costless total wealth = signal quality” | **AMENDED** → intensive g_gross (LOOSER/TIGHTER tag at P4 freeze) |
| Cost-aware search | **NOT** default (P5 operator-only) |

---

## 10. Complexity budget

| Item | Budget |
|---|---|
| New modules | `score`, `economics`, `fill_basis`, `high_cadence_null` |
| Modified | `search`, `certify`, `calibration`, `final_gate` (suspend note) |
| Frozen scalars invented | **0** |
| Engine / StrategyHost changes | **0** |

---

## 11. Implementation map (code)

| Clause | Location |
|---|---|
| g_gross + bootstrap | `xen.xena.score` |
| Q1 disclosure + integrity | `xen.xena.economics` |
| Search objective | `xen.xena.search.run_restart` → `robust_g_hat` |
| Evidence package | `xen.xena.certify.certify_and_rank` |
| Print/path | `xen.xena.fill_basis` |
| High-cadence null | `xen.xena.high_cadence_null` |
| HARD battery | retired in package field; no new battery runner |

---

## 12. Guardrails

- NEVER `run_final_gate` on live; NEVER TEST/holdout  
- NEVER tune vs XENA-001/002/003  
- NEVER re-pin absolute extensive-F  
- Emission / oracle / estimand / fences / Rust: unchanged unless operator-approved  
- Default route SUSPENDED  

---

## §P3 — Calibration predeclaration (committed BEFORE bank results)

**Authority:** operator Round-1 + Round-2 locks (2026-07-13).  
**Discipline:** L-12 — no value below is chosen after seeing bank results.  
**Scope:** P3 only. No registry freeze, no blind VAL, no default-route restore, no cost-aware search.

### P3.1 Operator-frozen decisions (verbatim; do not re-open)

| # | Decision | Frozen value |
|---|---|---|
| 1 | Objective | Binding search/rank/fold score = **P25(g_gross)**, **COSTLESS** (`charge_costs=False`). A-1 cost policy kept; no min-n floor. |
| 2 | Denominator | **Entry notional** \|Units·EntryPrice·money_per_unit\| — identical in search, folds, fixed-TEST. |
| 3 | DD | **DISCLOSURE-ONLY**. Deployability label = **net-LCB > 0** alone. Reconcile (R_max, DD) offline once for honest disclosure; **binds nothing**. |
| 4 | Binder | One-sided **95% LCB(g_gross) > 0**. End-to-end false-positive **α = 5%** after full **search → rank → fixed-TEST**, at **both** cadences. Power/MDE **measured & disclosed** at live density — **not** frozen to INFR-006 30/40 bps cells. No extensive-F re-pin, no WS-6 power-cell reuse. |
| 5 | Q1 cost floor | `floor = RT_cost_bps × k`. **k** from rule P3.2. MDE disclosed separately, never baked into floor. |
| 6 | Block bootstrap | Reuse common-block (`bootstrap_block_starts` / `bootstrap_g_gross`). **block ≥ H** (H = max hold bars). Length from coverage-sweep rule P3.2. |
| 7 | Null bank | **FRESH multi-source only**: synthetic multi-cadence + P0′ high-cadence null + 1–2 held-out-instrument nulls. **XENA-001/002/003 stay BLIND** (P4 VAL only). |

### P3.2 Deterministic selection rules (rule → number falls out of bank)

| Quantity | Predeclared rule (not a fixture fit) | Candidate set / floor |
|---|---|---|
| **block length L** | Smallest L ≥ H such that empirical one-sided 95% LCB coverage on the **null bank** (fixed null portfolios, no search) has **P(LCB>0) ≤ α=0.05** at **both** cadences; among such L, pick the **smallest**. If none, **coverage FAIL** (stop-condition). | Sweep L ∈ {H, 2H, 4H, max(H,32), max(H,64), max(H,128)} unique sorted |
| **k (cost-floor margin)** | Smallest k ∈ {1.0, 1.25, 1.5, 2.0} with k ≥ 1.0 such that on the **planted** battery with gross edge = k·RT_cost, end-to-end **net-LCB>0** recovery rate ≥ 0.50. If none qualify, report FAIL for k-rule (disclose curve; do not invent k). | {1.0, 1.25, 1.5, 2.0} |
| **K (random-subset ref count)** | Start K=32; double until \|median_K − median_{2K}\| / max(\|median_{2K}\|, ε) < 0.10 **and** same for IQR; cap K=256. **Evidence only** — never a pass threshold. | 32, 64, 128, 256 |
| **n null universes / cadence** | **n_null = 40** per cadence (low, high) for end-to-end α. Binomial SE at α=0.05: √(0.05·0.95/40) ≈ 0.034. | 40 low + 40 high |
| **Held-out instrument nulls** | **2** extra instruments (EURUSD, XAUUSD path-nulls), **n_heldout = 10** universes each cadence class, folded into the multi-source bank counts above as part of the 40 (8 synthetic + 8 P0′-class + 4 EURUSD + 4 XAUUSD + remainder synthetic path-nulls) — exact mix fixed below. | see bank composition |

### P3.3 Null-bank composition (fresh; predeclared counts)

**Shared layout (all synthetic):** `SegmentLayout.from_span` 50/30/20 search/ranking/gate on the synthetic bar span. Finite `cost_bps = 2.0` (non-placeholder). `skip_economics_precondition=True` for synthetic (no live Q1 artifact).

| Cadence | Generators (per universe seed) | H (hold bars) | n_cand | n_trades / density |
|---|---|---|---|---|
| **LOW** | `path_universe` null (n_planted=0) regime-GBM | H=20 | 16 | 80 trades/cand, n_bars=6000 |
| **HIGH** | P0′ `build_high_cadence_null` style (coin-flip, dense) | H=12 | 16 | target_legs≈800–1500, n_bars=12000 |
| **Held-out** | path nulls with symbol tags EURUSD / XAUUSD, independent path seeds | same H as cadence arm | 12 | matched to cadence arm |

**Per cadence (40 universes):** seeds `1000+i` (low), `2000+i` (high); of each 40: 28 path/P0′-class + 6 EURUSD-tagged + 6 XAUUSD-tagged zero-edge universes.

**Forbidden:** any use of XENA-001/002/003 emissions or their TEST bands.

### P3.4 Pipeline under test (per null universe)

```
synthetic universe
  → LAHC search on P25(g_gross), charge_costs=False, search band only
  → evidence-package rank on ranking folds (intensive g_gross)
  → fix ONE subset = top-ranked (or sole shortlist member)
  → fixed-TEST = synthetic layout.gate band ONLY
  → LCB_95(g_gross) and LCB_95(g_net) on that walk
```

- **Binding pass for structure:** `LCB_95(g_gross) > 0`  
- **Deploy label (measured, not auto-verdict):** `LCB_95(g_net) > 0`  
- **Not used:** `run_final_gate` extensive-F path; `gate_pass_threshold`; XENA fixtures  

**Search params (engine, not score scale):** `SearchParams` defaults with reduced budget for CAL compute honesty: `n_restarts=3`, `budget=50`, `SearchParams(L=40, n_boot=80, block_bars=max(H,64) provisional until sweep picks L for LCB only)`. Search block may stay 64; **LCB block** = rule-selected L.

### P3.5 Measurements

| Metric | Definition | Target / role |
|---|---|---|
| LCB coverage (no search) | On fixed full-universe or random k=5 null subset, fraction with LCB_95(g_gross)>0 | ≤ 5% both cadences (coverage) |
| End-to-end α | Fraction of null universes with LCB_95(g_gross)>0 after full pipeline | ≤ 5% **each** cadence — **HARD STOP if either fails** |
| Power / MDE | Planted edge recovery rate vs edge_bps at each density | **Disclose only** — not frozen cells |
| Block sweep | Coverage vs L | Selects L by P3.2 |
| k curve | net-LCB recovery vs k·RT plant | Selects k by P3.2 |
| K convergence | median/IQR stability of random-subset ref | Selects K by P3.2 |
| (R_max, DD) | Breach rate of daily 5% under R_max=5% on null paths | **Disclosure pair only** |

### P3.6 HARD stop-condition

If **end-to-end α > 5% at either cadence**, OR **one-sided 95% LCB coverage (no-search) is not ≤ 5% at either cadence** after the block rule is applied:

→ **STOP.** Write failure. **Do not freeze. Do not lower confidence, widen α, or re-pin extensive-F.**  
Failure ⇒ binder/procedure change + re-run on a **disjoint** bank — never fixture-fit.

### P3.7 Deliverable paths

- Harness: `xen.xena.calibration` P3 API + `analysis_code/run_p3_cal.py`  
- Results: `python/experiments/INFR-009/results/p3_*.json`  
- Report: `report.md` §P3 with STOP/PROCEED recommendation  

---

---

## §P3b — Re-calibration after P3 HARD STOP (procedure change; disjoint bank)

**Committed before any P3b result.** Not a target soften: α=5%, one-sided 95% LCB,
entry-notional, costless g_gross, DD disclosure-only, no extensive-F — **unchanged**.

**Parent:** §P3 (failed stop). **Artifact baseline:** `results/p3_calibration.json`.

### P3b.1 Diagnosis (carried)

| ID | Mechanism | Evidence |
|---|---|---|
| **F1** | Raw percentile LCB of intensive ratio undercovers at low effective-n (calendar-bar bootstrap, empty bars) | Low no-search P(LCB>0)=10–20%; high OK 2.5–5% |
| **F2** | Selection inflation across unpurged rank→TEST seam | High coverage OK, e2e α=15%; layout 50/30/20 contiguous |
| Scale | Toy budget/n → α magnitudes not freeze-grade | budget=50, n=40, ~16 cands |

### P3b.2 Procedure changes (predeclared)

| Code | Change | Spec |
|---|---|---|
| **A1** | Coverage-calibrated LCB | **bootstrap-t (studentized)** one-sided 95% LCB on g_gross/g_net. Same common-bar bootstrap path. Formula: `LCB = ĝ − t*_{0.95} · sê` with `t*_b = (g*_b − ĝ) / sê`, `sê = sd({g*_b})`. BCa not used (small-n instability). Emit every call: `n_legs`, `n_nonempty_blocks`, `empty_bar_fraction`. |
| **A3** | Min-effective-n domain fence | After A1: if `n_legs < n_legs_floor` OR `n_nonempty_blocks < n_blocks_floor` → `OUT_OF_CALIBRATION_DOMAIN` (no LCB pass claim). Floors = **smallest** thresholds on the bank at which A1 no-search coverage holds at both cadences among universes above the floor. Not from fixtures. Not a paper-over for A1 above the floor. |
| **B1** | Purge rank→TEST | `SegmentLayout.from_span(..., purge_ns ≥ H·bar_ns)` inserts embargobetween ranking end and gate start. Default **purge = H bars**; allow 2H if predeclared in run. |
| Search budget | Declared (not silent) | Toy/medium: budget=**80**, restarts=**3**. Production confirm: budget=**200**, restarts=**5**, n_cand=**64**. |

### P3b.3 Disjoint bank seeds

P3 used bases 1000/2000. **P3b uses 11000 (low) / 12000 (high)** + held-out offsets. Same mix shape (28+6+6 per cadence). XENA-001/002/003 still blind.

### P3b.4 Scale plan (C2)

1. **Loop 1 — toy/medium:** n_null=40–60/cadence, n_cand=16–24, budget=80. Iterate only if implementation bugs; **no** α softening.  
2. **Loop 2 — production confirm (mandatory before P4 talk):** n_null=40/cadence min, n_cand=64, budget=200, restarts=5.  

Stop-condition applied at **both** loops; production is required for proceed-to-P4 eligibility.

### P3b.5 HARD stop (unchanged)

If after A1+B1 at production confirm, e2e α > 5% at either cadence OR no-search coverage fails either cadence → **STOP**. Escalation not in this mandate: B2 distant TEST; then B3 selection correction only after A1+B1+scale exhausted.

### P3b.6 Code map

| Piece | Location |
|---|---|
| Studentized LCB + diagnostics | `xen.xena.score.lcb_g_studentized` |
| Purged layout | `SegmentLayout.from_span(..., purge_ns=)` |
| Harness | `xen.xena.calibration_p3b` |
| Results | `results/p3b_calibration.json` |

---

---

## §P3c — Freeze-grade-n confirm (resolution of low e2e residual; no procedure change)

**Committed before any P3c result.** Resolution fix only: re-estimate α at n with
SE≤1.5% under the **held** P3b procedure. **Not** target softening; **not** a new LCB/purge.

**Parent:** §P3b STOP (high e2e 2.5% pass; low e2e 7.5% @ n=40 underpowered).  
**Baseline:** `results/p3b_calibration.json`.

### P3c.1 What this is

| | |
|---|---|
| **IS** | One freeze-grade-n re-CAL: coverage + e2e α, n_null=**200**/cadence, same studentized LCB + purge ≥ H |
| **IS NOT** | Procedure change, α soften, UCB gate, optional stopping, fixture use |
| **Gate** | Point **α̂ ≤ 5%** both cadences **and** no-search coverage ≤5% both at selected L |
| **Disclosure** | Wilson interval + SE on α̂ — never the pass bar |

### P3c.2 Held frozen (do not re-open)

α=5%; one-sided 95% **studentized** LCB; entry notional; costless g_gross; DD disclosure-only;
rank→TEST purge ≥ H; no extensive-F; production within-universe scale (n_cand≈64, budget=200,
restarts=5).

### P3c.3 Predeclared parameters

| Item | Value / rule |
|---|---|
| **n_null / cadence** | **200** (design-power: SE at p=0.05 ≈ 0.218/√n ≤ **1.5%**) |
| **Seeds** | Bases **21000** (low) / **22000** (high) — disjoint from P3 (1k/2k) and P3b (11k/12k) |
| **L** | Re-apply P3b **joint L-selection** on this bank (do not blind-pin 40). Report reselected L; **flag drift from 40** |
| **Coverage n** | n=200 at selected L (and full joint sweep for L choice) |
| **Single run** | No optional stopping / draw-until-pass |
| **Wilson/SE** | Disclosure only |

### P3c.4 Escalation ladder (pre-committed; **not** executed in P3c)

If point α̂ > 5% at either cadence **or** coverage > 5% at selected L either cadence:

1. **Calendar/regime-scaled purge** (B1 refinement) → re-CAL  
2. **B2** distant/regime-shifted low-cadence TEST  
3. **B3** selection-aware correction (last resort)  

P3c only **recommends** rung 1 on STOP; does not implement it.

If both cadences pass → **recommend P4** (operator mandate still required).

### P3c.5 Code / artifacts

| | |
|---|---|
| Harness | `xen.xena.calibration_p3c` |
| Results | `results/p3c_calibration.json` |

---

---

## §P3d — Last estimator-calibration round (design/confirm; binder-form exit)

**Committed before design-bank results.** Last knob round. If confirm fails → binder-form
fork recommendation only (no P3e, no α soften).

**Parent:** §P3c STOP. **Evidence:** `p3c_calibration.json`, `p3c_high_e2e_passers.json`.

### P3d.1 Framing (carried)

- Residual is **F1 interval**, not F2 seam. High no-search 5.5–7.5% at **every** L; low clean only at short L; joint global L impossible.
- High e2e ≈ no-search; passers ≈ fails on ĝ_search → coverage-driven.
- High cadence ≈ **94% empty calendar bars** → resample **unit** is the lever (legs/events), not more B alone.
- Seam ladder **retired** for this residual.
- Per-cadence L = bootstrap nuisance, OK only as **predeclared rule** fit on design bank only.

### P3d.2 Design / confirm split (mandatory)

| Bank | Seeds (base low/high) | n_null/cadence | Role |
|---|---|---|---|
| **DESIGN** | 31000 / 32000 | **80** | Fit L-rule + interval fix; freeze procedure |
| **CONFIRM** | 41000 / 42000 | **200** | Gate only; no refit |

Disjoint from P3/P3b/P3c and each other. Within-universe: n_cand=64, budget=200, restarts=5 (F2 hold). Purge ≥ H kept.

### P3d.3 L-rule form (predeclared; params fit on design only)

```
if cadence == low:
    L = smallest L ∈ {H, 2H, max(H,16), max(H,24), max(H,32)} such that
        design-bank no-search P(LCB>0) ≤ 5% under the chosen interval method
    (expected short-L region)
if cadence == high:
    calendar L is NOT the primary lever; use leg/event bootstrap (below).
    If a calendar fallback is needed: L = argmin rate among candidates (report only).
```

**Forbidden:** pick one global L that makes the design bank pass both.

### P3d.4 Interval-fix ladder on DESIGN (stop at first that clears design coverage ≤5% both classes)

| Order | Fix |
|---|---|
| (1) | More B (200→400) on calendar studentized — cheap A/B |
| (2) | **Leg-blocked bootstrap** of the intensive ratio (resample legs/trade order blocks, not sparse calendar bars) + studentized LCB — **mechanistic primary** |
| (3) | BCa refinement on the chosen unit (if needed) |
| (4) | Calibrated confidence map nominal→empirical (last; freeze map) |

Emit n_legs, n_nonempty_blocks / n_leg_blocks, empty_bar_frac with every LCB.

### P3d.5 CONFIRM gate

PASS iff **point α̂ ≤ 5% both cadences** AND **no-search coverage ≤ 5% both** at the **rule-selected** method/L per cadence. Wilson/SE disclosure only. Single n=200; no optional stopping.

### P3d.6 HARD STOP + binder-form fork (exit)

If CONFIRM fails either cadence:

→ **STOP.** No more L/interval knobs, no α soften, no P3e. Recommend **binder-form** change:

| | Form |
|---|---|
| **(a)** | LCB on mean per-leg bps with **leg** bootstrap (different functional) |
| **(b)** | Permutation / randomization test for g_gross > 0 |
| **(c)** | Two-stage: intensive screen + different TEST statistic |

Report which evidence favors; **do not implement** in P3d.

If CONFIRM passes both → recommend **P4** (operator mandate still required).

### P3d.7 Artifacts

| | |
|---|---|
| Harness | `xen.xena.calibration_p3d`, `score` leg-bootstrap LCB |
| Design results | `results/p3d_design.json` |
| Confirm results | `results/p3d_confirm.json` |

---

### P3d.8 FREEZE boundary (filled after DESIGN bank only — before CONFIRM)

**Frozen UTC:** 2026-07-13T20:08:57Z

```
STATUS: FROZEN_AFTER_DESIGN
procedure: {"alpha": 0.05, "block_legs": 1, "design_high_coverage_ok": true, "design_high_rate": 0.025, "design_low_coverage_ok": true, "design_low_rate": 0.05, "high": {"block_legs": 1, "method": "leg_studentized", "n_boot": 200}, "interval": "leg_studentized", "lcb_confidence": 0.95, "low": {"block_legs": 1, "method": "leg_studentized", "n_boot": 200}, "n_boot": 200, "purge_mult": 1}
confirm_must_not_change_this_block: true
```

---

## §P-BF — Binder-form: permutation-through-search (committed BEFORE design-bank results)

**Parent:** §P3d CONFIRM STOP. **Evidence:** `results/p3d_confirm.json`  
(e2e 8.5%/6.5% vs no-search 5.5%/3.5%; passers≈fails on search score → selection multiplicity
leaking into adjacent TEST). Estimator calibration **closed**. This phase is **not** P3e and
does **not** retune L/interval on the old LCB binder.

**Authorized scope:** P-BF only. **Not authorized:** P4 freeze/VAL/route, P5, α soften,
reopening LCB knobs, implement exit (c).

### P-BF.0 What the binder is

Selection-aware permutation test. For each universe, the selected subset's **TEST** statistic
is judged against a null built by **re-running search→select→TEST** on **permuted** data of the
same universe — multiplicity of pick-best-of-restarts is **inside** the null and cancels.

| | Binding | Companion disclosure only |
|---|---|---|
| Functional | **mean per-leg bps** (light (a)+(b)) | g_gross ratio; leg-studentized LCB |
| Pass knob | perm-calibrated only | bare `>0` / LCB>0 **never** pass |

### P-BF.1 Permutation recipe (predeclared; bite-validated on DESIGN before confirm)

**Exchangeability unit:** bar on the (shared) marks path.

**Recipe `circular_shift_marks_open_rebuild_fills`:**
1. Keep EntryTime, ExitTime, Direction, StopDistance, Censored (cadence + crowding).
2. Circularly shift marks `Open` by lag `L ~ Uniform{H,…,n_bars−H}\{0}`.
3. Rebuild EntryPrice/ExitPrice from the **shifted** path at original bar times.
4. **Do not** re-apply planted exit shift — plant must collapse under null.

**Forbidden (vacuous / mean-invariant):** shuffle RealizedBps or per-leg P&L directly
(programme: permutation-destroy-mean-invariant / EXP-012). Break alignment **causally**.

**Bite-check (DESIGN, before any confirm):**
| Class | Expectation | Threshold |
|---|---|---|
| Planted (`edge_bps=20`, n=8/cadence) | edge collapses under perm | collapse frac ≥ 0.50 |
| Known-null (n=8/cadence) | mean ~unchanged | \|Δmean\| ≤ 3 bps |

Fail bite → fix recipe; **do not** confirm.

### P-BF.2 Pass rule (FPR-controlling)

Universe **PASS** iff

```
T_real > quantile_{1−α}( T_perm_1, …, T_perm_K )    α = 0.05
```

where `T` = mean per-leg bps of the selected subset on the purged TEST/gate band after full
search→certify. Empty / non-finite T → fail. Wilson/SE disclosure only.

### P-BF.3 DESIGN / CONFIRM split

| Bank | Seeds (low/high base) | n_null/cadence | Role |
|---|---|---|---|
| **DESIGN** | 51000 / 52000 | **16** | bite; K-convergence; freeze procedure |
| **CONFIRM** | 61000 / 62000 | **200** | gate only; no refit |

Disjoint from all P3* banks and each other. Within-universe: n_cand=64, budget=200,
restarts=5, purge ≥ H. Fixtures XENA-001/002/003 stay **BLIND**. No `run_final_gate`.

**Held frozen:** α=5%, costless g_gross generation, rank→TEST purge ≥ H, DD disclosure-only,
no extensive-F, no WS-6 cells.

### P-BF.4 K rule + compute

Per universe cost = 1 real + K permutation pipelines (each = full search→select→TEST).

#### P-BF.4 amendment (2026-07-13) — self-reference fix (pre-freeze)

**Defect in original rule:** measured |q_K − q_99| with K_max=99 → q_99 vs itself = 0 by
construction. When 19/39/59 all failed tol, the rule “froze” K=99 because the ladder ran out,
not because the null quantile settled (low design read: 59→99 rel=0.62 ≫ 0.25). That rule
**cannot fail K**. Fix is mis-specification repair on the DESIGN bank before freeze — not
tuning-to-pass; confirm bank untouched.

**Amended ladder:** run **K_pool=199** perms/universe on DESIGN. Diagnostic rungs
{19, 39, 59}; **certifiable** rungs {99, 149} only if they agree with the **higher** validator
q_199:

```
rel(K) = median_u |q_K(u) − q_199(u)| / (MAD_u(q_199) + ε)
K certifiable iff K ∈ {99, 149} and rel(K) ≤ 0.25
K* = smallest certifiable K on a cadence; joint K* = max(low, high)
```

| Outcome | Action |
|---|---|
| rel(99)≤tol both cadences | freeze **K\*=99** (cheap; q_99 settled vs q_199) |
| else rel(149)≤tol both | freeze **K\*=149** |
| neither | **do not freeze** top rung; **STOP** → recommend exit **(c)** (K non-convergence = compute/perm-validity class). Never under-K. |

**Feasibility (unchanged spirit):** confirm wall = median_design_wall(K\*) × 200 × 2 / n_workers.
If K\* set but wall > 12 h → **STOP**, exit **(c)** — do **not** under-K.

**Supersedes** the original self-referential K∈{19,39,59,99} vs q_99 rule above.

### P-BF.5 Gate + two terminal exits (no third)

**PASS** iff e2e point false-pass rate ≤ 5% at **both** cadences on CONFIRM (n=200).  
Single predeclared n, K; no optional stopping.

| Outcome | Action |
|---|---|
| **PASS** | Recommend **P4** (freeze perm-binder registry; blind VAL; route) — operator-mandated |
| **FAIL** | **Do not** tune knobs / open P3e. Either **TERMINAL** “cannot certify gross structure at α=5% under a selection-aware null”, or escalate **(c)** two-stage **only if** failure is compute/perm-validity (not α itself). **Do not implement (c) here.** |

### P-BF.6 Artifacts

| | |
|---|---|
| Harness | `xen.xena.calibration_pbf`, `score.mean_per_leg_bps` |
| Driver | `analysis_code/run_pbf_cal.py` |
| Design | `results/pbf_design.json` |
| Confirm | `results/pbf_confirm.json` |
| Report | `report.md` §P-BF |

### P-BF.7 FREEZE boundary (filled after DESIGN bank only — before CONFIRM)

```
STATUS: NOT_FROZEN — design STOP 2026-07-13
reason: K_not_converged (low: rel99=0.559, rel149=0.270 vs q199; tol=0.25)
        + host hard-shutdown mid kconv-high (8/16) under K_pool=199
frozen_procedure: null
confirm_must_not_run: true
recommend: exit_(c)_two_stage
artifact: results/pbf_design.json
```

---

*End design. P-BF did not reach confirm. P4 blocked. Exit (c) is recommendation only — not implemented here. No P3e.*

---

---

## §P-C — Binder-form exit (c): two-stage sample-split (committed BEFORE design-bank results)

**Parent:** §P-BF DESIGN STOP (`results/pbf_design.json`; K non-convergence + host crash —
tail of a max-over-restarts statistic is unestimable at feasible K). Estimator-calibration
(P3→P3d) and permutation-through-search (P-BF) are both **closed**. This is the **last
structural card** (design's reserved exit (c)). **Not** P3e; **no** LCB-knob retuning; **no**
permutation.

**Authority:** operator locks 2026-07-14 (two forks below). **Authorized scope:** P-C only.
**Not authorized:** P4 freeze/VAL/route, P5, α soften, LCB-confidence drop, held-out-instrument
banks, `run_final_gate`, any XENA-001/002/003 TEST/holdout contact.

### P-C.0 Why (c) is structurally cleaner (not a fallback)

P3→P3d put an interval on a **searched** subset and tried to *correct* selection post-hoc —
structurally impossible (searched≠unselected; e2e inflated ~3pp over no-search). P-BF built a
selection-aware null but its threshold was a tail quantile of a max-over-restarts statistic —
unestimable at feasible K. (c) **prevents** the leak by construction: **select on stage-1 data
only, then test once on a genuinely independent band.** Conditional on the selection, stage-2 is
a single fresh test → α controlled at nominal *by construction*. The **entire** load then sits on
one thing: stage-2 must be genuinely decorrelated from stage-1 (P-C.2 embargo + P-C.3 bite).
This reduces e2e back to the **no-search coverage** problem the P3d leg bootstrap nearly solved
(high 3.5% OK, low 5.5% borderline) — so a low-cadence miss, if it happens, is **coverage-limited**,
not selection-unsafe (forensics P-C.6 must say which).

### P-C.1 The two-stage procedure (frozen form; params fit on design only)

```
STAGE 1 (select — cheap):  search on stage1.search band → certify/rank on stage1.ranking folds
                           → fix EXACTLY ONE subset = top-1 (pkg["ranked"][0].subset)
        ── large EMBARGO gap (P-C.2) ──
STAGE 2 (test — single):   lcb_g_leg_studentized(g_gross) > 0 on the distant stage2 band
                           one evaluation; NO permutation, NO K×-search, NO tail quantile
```

- **Exactly one subset.** No shortlist. (Fork A discipline: a shortlist would reintroduce
  stage-2 multiplicity; forbidden unless a predeclared correction — not used here.)
- **Stage-2 statistic** = `score.lcb_g_leg_studentized` on the **binding g_gross ratio**
  (design §3), leg bootstrap, studentized, `block_legs=1`, `n_boot=200`, `confidence=0.95`.
  This is the **exact P3d frozen estimator** — the one whose no-search coverage was measured
  (high 3.5%, low 5.5%), which is precisely the residual (c) inherits.
  **Reconciliation:** the handoff phrase "lcb_g_leg_studentized(mean_per_leg)" (PROGRESS §4)
  conflated two functionals; `mean_per_leg_bps` was the P-BF permutation statistic. (c) drops
  permutation, so there is no reason to leave the binding g_gross ratio — stage-2 tests
  g_gross, the design's binding estimand. Documented here so it is not a silent pick.
- **Costless g_gross generation** (`charge_costs=False`); net-LCB disclosure companion only.

### P-C.2 Independence recipe: distant/embargoed same-stream band (predeclared)

**Recipe = single distant temporal segment**, not adjacent-purge (P3d's purge=H **leaked**).

| Item | Value |
|---|---|
| Embargo | `EMBARGO_FRAC = 0.20` of the full universe span, inserted between stage-1 (ranking end) and stage-2 (gate start) via `SegmentLayout.from_span(..., purge_ns=EMBARGO_FRAC·span)` |
| Bands | search_frac=0.50, ranking_frac=0.25 of the **usable** (post-embargo) span; stage-2 = remaining ~0.25 |
| Embargo scale check | low: 1200 bars = **60·H**; high: 2400 bars = **200·H** — both ≫ regime memory (episode ~1/p_enter_high ≈ 100 bars). Adjacent-purge that leaked was 1·H. |
| Rationale | Synthetic null direction is a per-trade coin flip (E[dir·Δ]=0), so a stage-1-lucky candidate has **no persistent** property; the only residual dependence is **regime-episode straddle** across the seam. Embargo ≫ episode length breaks it. The bite (P-C.3) proves this empirically, per cadence. |

**Fork B (locked):** the recipe is **one procedure**. If the bite fails (temporal independence
inadequate) → **TERMINAL**, no held-out-instrument escalation in this experiment. Held-out
instruments answer a *different* estimand (cross-instrument transfer, not "real on this stream")
and must not become an adaptive second chance or authorize P4 route-restore — that is a separate
future programme with its own predeclaration.

### P-C.3 Bite-check (independence proof; MANDATORY before any α gate)

**Claim under test:** a signal that lives **only in stage-1** must **not** survive into stage-2.

**Mechanism (generator-agnostic; both generators plant `ExitPrice = raw_exit·(1+d·e/1e4)`):**
1. Generate a planted universe (`edge_bps = 20`, `n=8`/cadence, plant ids `plant*`/`HCPLANT*`).
2. **De-plant stage-2:** for every planted-candidate trade with `EntryTime ≥ stage2_start`,
   set `ExitPrice ← raw_exit = ExitPrice/(1+d·e/1e4)` (exact inverse). Plant now lives in
   stage-1 only. (Null candidates: edge=0 → de-plant is a no-op.)
3. Run the full stage-1 → select → stage-2 procedure. Stage-1 sees the plant and selects it;
   stage-2 sees no plant on the distant band.

| Read | PASS threshold | Interpretation of FAIL |
|---|---|---|
| **Stage-2 survival rate** = frac of stage-1-planted universes with stage-2 LCB(g_gross)>0 | **≤ α + tol = 0.05 + 0.075 = 0.125** (small-n design band, n=8) | > threshold ⇒ stage-1 signal bleeds into stage-2 ⇒ bands **dependent** ⇒ embargo inadequate |
| Stage-1 selects the plant | plant in top-1 ≥ 0.5 (sanity: bite has bite) | plant not selected ⇒ bite is vacuous; fix before reading survival |

**Bite thresholds are frozen here, before any run.** No "widen embargo until bite passes" after
seeing results — `EMBARGO_FRAC` is predeclared; the bite is a validity check, not a tuning loop.
**Bite FAIL → TERMINAL** (P-C.7), per Fork B.

### P-C.4 DESIGN / CONFIRM split (mandatory)

| Bank | Seeds (low/high base) | n_null/cadence | Role |
|---|---|---|---|
| **DESIGN** | 71000 / 72000 | **80** | bite-check + no-search coverage on stage-2 band; freeze procedure |
| **CONFIRM** | 81000 / 82000 | **200** | per-cadence α̂ gate only; no refit |

Disjoint from all P3*/P-BF banks and each other. Within-universe: n_cand=64, budget=200,
restarts=5. Fixtures XENA-001/002/003 stay **BLIND**.

**Held frozen:** α=5%, one-sided 95% studentized leg-bootstrap LCB on g_gross, entry notional,
costless g_gross, DD disclosure-only, no extensive-F, no WS-6 cells, point α̂ gate (not UCB),
single predeclared n, **no optional stopping**.

### P-C.5 Gate — per-cadence certification (Fork A amendment, in writing)

**Amendment (pre-(c)):** Binder target §2 "α = 5% at **both** cadences" is **re-scoped for the
(c) gate logic only**. This is a **scope** change, not an integrity change: α stays 5%, point α̂,
n=200, design/confirm split, no optional stopping — all locked. Historical dual-AND is retired
for (c) gate logic only.

- **Primary claim:** per-cadence end-to-end point **α̂ ≤ 5%** at n=200 confirm, **and** no-search
  coverage ≤ 5% at the frozen estimator, for that cadence.
- **Certification is per deployment cadence.** Symmetric outcome table:

| Confirm low | Confirm high | Outcome |
|---|---|---|
| α̂≤5% & cov≤5% | α̂≤5% & cov≤5% | **Dual certify** → P4 both routes |
| fail | α̂≤5% & cov≤5% | **High-only certify** (that binder); low **terminal** for this binder |
| α̂≤5% & cov≤5% | fail | **Low-only certify**; high **terminal** |
| fail | fail | **TERMINAL** |

- A single-cadence pass certifies **only that cadence's binder procedure** — **not** a full XENA
  default-route restore (operator P4 decision, per cadence).
- **No "pipeline green" banner on a partial pass.** The report states exactly which cadence(s)
  certified.

### P-C.6 Forensics tags (disclosure; recorded every cadence, either outcome)

Per cadence, always record and report:

| Tag | Definition |
|---|---|
| `no_search_cov` | no-search P(LCB>0) on the stage-2 band (random k=5 subset) |
| `e2e_alpha` | end-to-end α̂ (full stage-1→select→stage-2) |
| `selection_inflation` | `e2e_alpha − no_search_cov` |

**Honesty rule:** if a cadence fails with `selection_inflation ≈ 0` and `no_search_cov ≈ e2e_alpha ≈
5.5%`, the narrative is **coverage-limited** (data-density; sparse 94%-empty high-cadence calendar,
P3c), **not** "cannot certify under selection-aware design." The gate bit stays fail; the label
stays honest. Only `selection_inflation` materially > 0 is a selection-safety failure.

### P-C.7 Terminal exits (per Fork B; no third path)

1. **Bite FAIL** (either cadence) → **TERMINAL**: "stage-2 temporal independence failed bite;
   cannot run a selection-safe two-stage binder on this stream at α=5%." No held-out. No α gate run.
2. **Dual α/coverage pass** → recommend **P4** (freeze (c) procedure registry; blind VAL via
   SEG_PROXY; route) — operator-mandated.
3. **Single-cadence pass** → certify that cadence's binder only (P-C.5 table); the other cadence
   **terminal**; **no** full route-restore.
4. **Dual α/coverage miss** (measured α, bite OK) → **TERMINAL**: "the pipeline cannot certify
   gross structure at α=5% under a selection-aware two-stage design." Do **not** open more knob
   rounds; do **not** escalate to held-out here.

**Ops:** capped workers (no uncapped batteries — the P-BF host-crash lesson). Compute is
n_null × (1 search + 1 stage-2 eval) — trivial vs P-BF's K×; host-safe.

### P-C.8 Artifacts

| | |
|---|---|
| Harness | `xen.xena.calibration_pc`, `score.lcb_g_leg_studentized` |
| Driver | `analysis_code/run_pc_cal.py` |
| Design | `results/pc_design.json` |
| Confirm | `results/pc_confirm.json` |
| Report | `report.md` §P-C |

### P-C.9 FREEZE boundary (filled after DESIGN bank only — before CONFIRM)

**Frozen UTC:** 2026-07-14

```
STATUS: FROZEN_AFTER_DESIGN
bite: PASS both cadences (Fork B terminal NOT triggered — embargo independence holds)
      low  survival=0.000 (0/8) select=1.000
      high survival=0.125 (1/8) select=1.000   [borderline: exactly at survival_max=0.125]
design_no_search_coverage (disclosure): low=0.075 (6/80, >5%)  high=0.025 (2/80, ≤5%)
      → low-cadence coverage-limited residual confirmed at design; high-only outcome foreshadowed
frozen_procedure: {"binder": "two_stage_sample_split", "functional": "g_gross_ratio",
  "estimator": "leg_studentized_bootstrap_t", "embargo_frac": 0.2, "search_frac": 0.5,
  "ranking_frac": 0.25, "n_boot": 200, "block_legs": 1, "confidence": 0.95, "alpha": 0.05,
  "one_subset": true, "shortlist": false, "held_out_escalation": false,
  "confirm_seeds": {"low": 81000, "high": 82000}}
confirm_must_not_change_this_block: true
artifact: results/pc_design.json
```

---

*End §P-C predeclaration. Design FROZEN 2026-07-14; CONFIRM ran on frozen procedure → **DUAL_CERTIFY** (`results/pc_confirm.json`: e2e α̂ 5.0%/5.0% at n=200, cov 4.5%/4.0%, selection_inflation 0.5pp/1.0pp). Boundary pass (α̂ exactly at gate line; Wilson upper 9.0%). P4 unblocked — operator-mandated, per cadence. No P3e. No held-out in this experiment.*

---

---

## §P4 — Freeze + blind VAL (committed BEFORE VAL results; operator-mandated 2026-07-14)

**Parent:** §P-C CONFIRM DUAL_CERTIFY. Operator mandate 2026-07-14: **freeze the (c) procedure + run blind VAL**. **Route-restore is NOT in this scope** (separate operator decision; the boundary-pass margin is thin).

**Pre-freeze integrity gate (satisfied 2026-07-14):** Rust fold kernel proven **bitwise identical** to the Python oracle (`python == rust` on `best-r00` + 488 random + 11 best-r cases). The one red parity case was a **stale pinned digest** (corpus-input drift: XENA-001 `search_restart_00.json` `best_subset` regenerated upstream), **not** a kernel divergence; pins regenerated via `gen_xena_fold_parity_corpus.py` (semantics proven unchanged — 499/500 cases matched old pins), gate green. Binding estimand confirmed = **g_gross ratio** (design §3), not `mean_per_leg` (that was P-BF's permutation stat).

### P4.1 Freeze (hash-pin the (c) registry)

Pin `frozen_procedure` (from `results/pc_design.json`) + confirm summary (α̂/cov/verdict) + integrity attestation + operator signoff, SHA-256 over the registry content → `results/pc_frozen_registry.json`. Any post-freeze change is a new predeclared calibration, never an in-place edit (matches `calibration.freeze_registry` discipline).

### P4.2 Blind VAL protocol (holdout stays BLIND — SEG_PROXY only)

Validate the frozen (c) binder on the three real fixtures **without reading the holdout TEST band** (2024-03-28 → 2024-12-11). All computation on **SEG_PROXY** (2023-07-13 → 2024-03-28, matched-duration TRAIN proxy immediately preceding TEST; INFR-006 A-2 construct).

| Stage | Band | Action |
|---|---|---|
| Stage-1 select | search band 2021-06-02 → 2023-03-08 | (c) g_gross P25 score over the fixture's **12 existing search finalists** → **top-1** (reuses the real search; exactly one subset, no shortlist) |
| — embargo — | 2023-03-08 → 2023-07-13 (~127 days) | natural distant gap ≫ any regime memory (≫ synthetic 60–200·H) |
| Stage-2 test | **SEG_PROXY** | `lcb_g_leg_studentized` **gross** (`charge_costs=False`) and **net** (`charge_costs=True`), 95%, leg bootstrap, `n_boot=200`, `block_legs=1` |

- **Binding VAL verdict per fixture** = stage-2 on the top-1 subset: `gross_LCB>0` (gross structure certified) and `net_LCB>0` (deployable).
- **Disclosure:** stage-2 gross/net LCB on **all 12 finalists** per fixture, so the verdict is not hostage to one subset.
- **No `run_final_gate`, no extensive-F, no holdout read, no re-tuning** — the procedure is frozen.

### P4.3 Predeclared expected verdicts (committed before results; from §8 + P0 economics recompute)

| Fixture | Q1 p50 RealizedBps (P0) | Nature | **Expected (c) verdict** |
|---|---|---|---|
| XENA-001 | +0.043 (≈0) | random-entry null (real prices, live scale) | **NOT certified** — `gross_LCB ≤ 0` (FPR control on a real null) |
| XENA-002 | −0.284 (sub-zero) | sub-zero edge | **NOT certified** — `gross_LCB ≤ 0` |
| XENA-003 | +1.910 (real gross, sub-cost) | real gross, bounce-scale, sub-cost | **NOT deployable** — `net_LCB < 0`; `gross_LCB > 0` *acceptable* (real gross) OR `≤0` (binder conservative at ~1.9 bps density) — either preserves the honest "real-but-sub-cost" story via Q1 |

### P4.4 Acceptance / rejection (§8 alignment)

**VAL PASSES** iff **no fixture is credited DEPLOYABLE** (`net_LCB > 0` on none of 001/002/003), **and** the binder uses no absolute extensive-F, **and** 003's real-gross story is not contradicted (Q1 +1.9 stands; if `gross_LCB>0` for 003 it corroborates, if `≤0` it is conservative — neither credits 003 as tradable).

**VAL FAILS (redesign rejected)** iff any of: 001 or 002 shows `net_LCB > 0` (credited tradable); 003 shows `net_LCB > 0` (sub-cost credited deployable); any absolute-F binder reintroduced. On FAIL → do **not** route-restore; report and stop.

**Boundary-pass carry:** VAL is a **validation of the frozen binder's honesty on real fixtures**, not a second α gate. The (c) α̂ boundary margin (5.0%, Wilson upper 9.0%) is disclosed; VAL does not re-open it.

### P4.5 Artifacts

| | |
|---|---|
| Freeze | `results/pc_frozen_registry.json` (sha256-pinned) |
| VAL harness | `analysis_code/run_pc_val.py` |
| VAL result | `results/pc_val.json` |
| Report | `report.md` §P4 |

### P4.6 FREEZE + VAL boundary (filled after run)

**Run UTC:** 2026-07-14

```
STATUS: FROZEN + VAL RUN → GROSS PASS (clean); DEPLOYABILITY PASS after cost correction;
        one frozen-procedure DEFECT flagged; route-restore WITHHELD.
freeze: results/pc_frozen_registry.json  sha256=44e1aa3cd7690fe0…
holdout TEST band NEVER read (SEG_PROXY only).

GROSS axis (the (c) FPR-controlled certification claim) — clean, matches predeclared:
  XENA-001  gross_LCB=-0.249  → not certified   (null; FPR control holds on a real null)
  XENA-002  gross_LCB=-0.248  → not certified   (sub-zero)
  XENA-003  gross_LCB=+1.077  → gross-certified  (real gross; corroborates Q1 +1.910)

NET / deployability — FIRST RUN INVALID, then CORRECTED:
  Defect: real fixtures are engine-costless (cost_bps median 0.0, few up to ~13); the
  frozen net path eval_lcb_legs(net=True) charges only the sparse STREAM cost — far
  below the real ~1–3 bps FTMO RT. Net IS below gross (003 top-1 +1.077 gross / −0.180
  net; gaps 0.1–1.3 bps) but under-charged → 003 spuriously 7/12 finalists net_LCB>0.
  NOT literally net≈gross; the charged cost is just far too small. Costs must be INJECTED
  (xen.evaluation FTMO), not read off the stream (memory cost-model-and-injection).
  NB primary pc_val.json verdict field stays VAL_FAIL_redesign_rejected (strict
  any-finalist rule on the INVALID net axis, not re-run); governing deployability record
  = pc_val_costsweep.json.
  Correction (results/pc_val_costsweep.json) — flat injected RT cost sweep:
    XENA-003 top-1 net_LCB: cost 0.0→+1.077, 0.7→+0.315, 1.0→-0.085, 1.5→-0.654, 2.0→-1.207
    XENA-003 finalists net-pass: 12/12 at 0.7 → 2/12 at 1.0 → 0/12 at ≥1.5
    001/002 net-negative at ALL costs.
  → deployability vanishes across 0.7–1.5 bps = the known 003 breakeven→ruin band
    (xena-003-cost-fatal). At realistic CFD spread (1–3 bps) NO fixture deployable.
    003 = real gross, cost-fatal — reproduced exactly.

  Cost-injection attempt (2026-07-14): per-symbol FTMO injection BLOCKED — the 12
  fixture symbols are index/commodity CFDs, FTMO commission ~0 (cost is all SPREAD),
  and spread_pips is NOT pinned (round_trip_cost_bps refuses; needs live FTMO data).
  Cannot fabricate spread. BUT the verdict is COST-ROBUST so exact spread is not needed:
  on the §P4.2 BINDING top-1 rule, 003 top-1 net_LCB<0 for ALL cost ≥1.0 bps
  (1.0→-0.085, 1.5→-0.654, 2.0→-1.207); 001/002 net<0 everywhere → NO fixture deployable
  across the whole realistic index-CFD band (≥1.0 bps). → corrected verdict
  VAL_PASS_binding_top1 (results/pc_val_injected.json).
  NB the raw pc_val.json `verdict` field stays VAL_FAIL_redesign_rejected — it used the
  any-finalist DISCLOSURE rule (a code mis-wiring of §P4.2, whose binding rule is top-1)
  on the invalid stream-cost net axis; superseded by pc_val_injected.json. A per-symbol
  EXACT machine number still needs operator-supplied spread_pips.

FROZEN-PROCEDURE DEFECT (must fix before live route-restore):
  the (c) net/deployability gate uses stream cost_bps → INERT on engine-costless live
  emissions → would falsely credit sub-cost strategies deployable. Fix = inject FTMO
  cost into the net-LCB path (or make net-LCB>0 the binding stage-2 objective with
  injected cost). Gross certification unaffected.

DECISION: route-restore WITHHELD (out of §P4 scope + net-path fix required + boundary
  α̂ margin thin). P4 gross-validated; deployability-validated under corrected cost;
  net-path fix + operator sign-off needed before live.
```

---

*End §P4. Freeze DONE (registry pinned). Blind VAL: GROSS certification clean (001/002 rejected, 003 real gross); deployability clean AFTER cost correction (nothing deployable at realistic cost; 003 cost-fatal reproduced in its 0.7–1.5 bps band). Frozen net path is inert on engine-costless real fixtures — inject FTMO cost before live. Route-restore WITHHELD. Holdout TEST never read. No extensive-F.*

---

## §P5 — Net-path amendment + route-restore (operator 2026-07-14; committed BEFORE re-VAL)

**Parent:** §P4 freeze + blind VAL (gross clean; deployability cost-robust on top-1; route-restore withheld for net-path defect).

**Authority:** operator locks 2026-07-14:
1. Conservative **flat RT = 1.0 bps** is enough for the net/deployability gate (not per-symbol live pins).
2. Accept (c) confirm **α̂ = 5.0% boundary** as formal success (Wilson upper ~9% disclosed); informal risk posture may tolerate ~8–10% **without** rewriting the locked α gate.

**Not authorized:** re-run (c) confirm / α soften; holdout TEST read; extensive-F; silent in-place edit of the §P4 registry without a new hash pin.

### P5.1 Net-path amendment (predeclared)

| Item | Value |
|---|---|
| Defect | Stream `cost_bps` on engine-costless live emissions under-charges net → false deployability |
| Fix | **Inject flat round-trip cost** into the **net** stage-2 path only |
| Injected RT | **`INJECTED_RT_BPS = 1.0`** (operator conservative floor; live FTMO snapshot median ~1.5 bps, range ~0.5–4.2; source note in registry) |
| Gross path | **Unchanged** — `charge_costs=False`, no injection (FPR / structure claim) |
| Deployable | **`net_LCB > 0` on top-1** after injection (`lcb_g_leg_studentized`, n_boot=200, block_legs=1, confidence=0.95) |
| Binding subset | **Top-1 only** (§P4.2). All-finalist stage-2 remains **disclosure**, not the acceptance gate |
| Stage-1 | Unchanged — costless g_gross P25 / search |

Tag: **TIGHTER** on deployability (was inert ~0 cost; now charges 1.0 bps RT). Gross/α unchanged.

### P5.2 Re-VAL protocol

Same fixtures/bands as §P4.2 (SEG_PROXY only; holdout never read). Expected:

| Fixture | Gross | Net @ 1.0 bps (top-1) | Deployable |
|---|---|---|---|
| 001 | ≤0 | ≤0 | no |
| 002 | ≤0 | ≤0 | no |
| 003 | >0 acceptable | ≤0 | no |

**VAL_PASS** iff no fixture top-1 is deployable (`net_LCB ≤ 0` all three) and gross story matches §P4.3 (001/002 not gross-certified; 003 gross ok).

### P5.3 Amended freeze + route-restore

- New hash pin: `results/pc_frozen_registry.json` (v2 amendment; records `parent_sha256` of §P4 pin `44e1aa3c…` + net-path fields).
- Re-VAL artifact: `results/pc_val_p5.json`.
- **Route-restore AUTHORIZED** after re-VAL PASS under this amendment:
  - Active binder = exit (c) two-stage + **injected net 1.0 bps** deployability.
  - INFR-006 v3 extensive-F remains **superseded** (not re-enabled).
  - Default XENA route: **RESTORED** for incoming ideas under this pin.
  - Operator remains final on capital / universe certify; α boundary accepted as disclosed.

### P5.4 FREEZE + re-VAL + route boundary (filled after run)

```
STATUS: P5 COMPLETE 2026-07-14 — VAL_PASS; route RESTORED
amended_registry: results/pc_frozen_registry.json
  schema=xena.infr009.pc_registry.v2
  sha256=db87dc1a4d8d5700…  parent_sha256=44e1aa3cd7690fe0… (archived pc_frozen_registry_p4.json)
  injected_rt_bps=1.0  deployability=top1_net_lcb_positive_after_injection
  alpha_boundary=ACCEPTED (5.0% point; Wilson upper 9.0% disclosed)
re_VAL: results/pc_val_p5.json  verdict=VAL_PASS  all_match_expected=true
  001 gross_LCB=-0.249 net@1.0=-1.137  not deployable
  002 gross_LCB=-0.248 net@1.0=-1.221  not deployable
  003 gross_LCB=+1.077 net@1.0=-0.085  gross-certified, not deployable
holdout TEST NEVER read. No extensive-F. No α rewrite.
route_restore: RESTORED — default XENA route uses exit (c) + injected net 1.0 bps;
  INFR-006 v3 extensive-F remains superseded; operator final on capital/universe certify.
```
