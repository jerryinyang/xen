# EXP-011 (E7) — Referee 15m-Domain Extension — Report

**Status:** COMPLETE + **FROZEN** (2026-07-01). **Verdict:** **FREEZE_LICENSED** (audit PASS, 0
Critical). **Class:** referee-renew (D-referee), **analysis-only**. **Budget:** 0 counted TEST reads,
0 candidate slots, global holdout sealed. **Checkpoint:** Phase-003 CONC-1, Track 2 (critical path).

**One line.** A **15m trading domain** was added to the frozen renewed referee (§10.3a q\*=0.75 + E6
P\*-gate), calibrated candidate-blind and **frozen + hash-pinned** — the 1h/4h referee is byte-for-byte
unchanged. This unblocks **EXP-010 Track 2** (CF-MR-003 exec-15m: T2a 14 S3_DETREND single-symbol +
T2b 10 S5_SPREAD multi-symbol), which had no 15m referee to be adjudicated under.

---

## 1. Question

Does the frozen renewed referee, extended by a new 15m domain whose calibration constants are derived
**candidate-blind**, retain **FPR-control AND finite power** at 15m — licensing a freeze — **while
leaving every 1h/4h verdict bit-identical** to E5/E6? (L-12: a referee extension is a predeclared
experiment, FPR-recalibrated on the dogfood-negative + synthetic-positive battery and frozen *before*
it adjudicates the live candidate.)

## 2. Method (reuse, not reinvent)

The exact E2/E3a/E4/E6 battery pointed at `domain="15m"`. The 15m constants are injected at runtime
into the frozen module dicts (E4 candidate-blind injection pattern) so the frozen **source** stays
byte-frozen during the battery; the permanent additive source edit + `freeze_manifest.json` are
emitted **only after** the battery licensed the freeze (`code/apply_freeze.py`, guarded on the license
verdict). No gate leg is added, removed, or re-thresholded — the extension is four additive dict rows.

- **Data:** 16 instruments (INFR-003 5-yr, DE30 absent), 15m via `aggregate_ohlc(min_coverage=0.90)`
  + analysis-boundary fence; open-to-open ≤t-1; first-70% analysis (anchor), first-49% TRAIN (15m
  dogfood + substrate). Holdout never sliced.
- **Battery:** 3-arm DET (frozen / frozen_amortized / adaptive=§10.3a) + E6 P\*-gate reduction
  identity, per (config × instrument × shape∈{DENSE,TAIL,SPARSE,STATE}). Endpoints per stratum
  (L-03): dogfood FPR (4 null families + skew guard), MDE per shape, DET verdict.

## 3. The 15m constants (mechanical derivation — candidate-blind)

Every constant: mechanical prior + battery confirmation + pre-registered sensitivity band. No magic
constant; nothing fit to CF-MR-003.

| Constant | Frozen value | Derivation (reproduces frozen 1h/4h) |
|---|---|---|
| `MATERIALITY_BPS["15m"]` | **0.75** | √-period `0.19365·√15`; `k=1.5/√60` reproduces **1h=1.5, 4h=3.0 exactly** |
| `DomainSpec.min_effective_n` | **90** | log-period interp(5m 120, 1h 60)=93.5 → 90 |
| `DomainSpec.min_state_count` | **25** | log-period interp(5m 30, 1h 20)=25.6 → 25 |
| `EPISODE_LENGTHS["15m"]` | **17** | log-period interp(5m 24, 1h 8)=16.9 → 17 (substrate L, referee-consumed) |
| `ROUND_TRIP_COST_BPS_17[i]["15m"]` | inherit i's 1h | per-*trade* round-trip is domain-invariant (E1: only per-*held* over-charges turnover) |
| `ADAPTIVE_DOMAINS` | `("15m","1h","4h")` | — |

## 4. Results

### 4.1 Regression anchor (binding correctness gate) — PASS
`regression_anchor_check.json`: **0/32 mismatch**, E6 P\*-gate reduction identity **32/32**. With 15m
injected, 1h/4h §10.3a verdicts + STATE ΔMDE (1e-9) + adaptive dogfood-FPR (1e-9) reproduce
EXP-003/E6 **bit-for-bit**. Frozen source hashes unchanged **during** the battery (== E5/E6). "Adds a
domain, changes nothing else" holds.

### 4.2 15m battery (16 strata, prior config)
| Metric | Result |
|---|---|
| DET_DOMINANT | **16/16** |
| dogfood-negative FPR (4 null families) | **max 0.000** |
| skew-stressed null FPR (E4 R3) | **0.000** |
| DENSE-powered | **16/16** |
| STATE recovery ΔMDE (frozen−adaptive) | **all 16 positive**, median **5.5** bps (3.5–15.5) |
| SPARSE recovery ΔMDE | **15/16 positive**, median 23.5 (JP225 sparse UNPOWERED on one arm) |
| P\*-gate identity @15m | **112/112** |

**Mechanism.** The strict FPR control *and* the §10.3a shape-recovery (STATE+SPARSE ΔMDE>0 — the
E2/E3a signature: the adaptive economic leg lowering the detection floor the rigid frozen gate cannot)
both carry into 15m. Recovery is genuine, **not DENSE-only** — DENSE is powered on all 16 while the
strict DET gain comes from STATE+SPARSE. No structurally-impossible leg at 15m (floors attainable).
[`plots/recovery_map_15m.png`, `plots/fpr_by_stratum_15m.png`]

### 4.3 Sensitivity band — verdict invariant
All **7 configs × 16 = 112 rows** DET_DOMINANT ∧ fpr_controlled ∧ dense_powered; `band_flip_strata=[]`.
Sweeping M∈{0.5,0.75,1.0}, N∈{75,90,105}, S∈{20,25,30} left the verdict unchanged — the prior sits in
the interior of a flat region, not on a cliff. [`plots/band_surface_15m.png`]

### 4.4 Leak tripwires — clean
- **Future-destroy collapses:** dogfood FPR 0.0; future-destroy over 112 rows = 91×0.000, 20×0.050
  (1/20), **1×0.100** (M0.5/GBPUSD, 2/20). The 0.100 is a single **band-stress** cell at a lenient
  materiality — not the frozen prior (GBPUSD prior = 0.05) — an E4 single-draw artifact
  (`wilson_lower(2,20)=0.028 ≪` control); it did not trip the guard. Non-material.
- **No-plant guard + standing dogfood null:** clean on all 112 rows.

### 4.5 Calibration vs the frozen 1h/4h referee
| Domain | DET-dominant | dogfood FPR | STATE ΔMDE (median) |
|---|---|---|---|
| **15m** | 16/16 | **0.000** | 5.5 bps (3.5–15.5) |
| 1h | 16/16 | 0.000 | 7.5 (4.0–23.5) |
| 4h | 16/16 | 0.000 | 8.0 (4.0–20.0) |

15m is a **clean peer**: identical (perfect) FPR control, marginally gentler recovery lift — expected
from √-time compression of the 15m economic floor. No domain-specific weakness.

## 5. Freeze (hash-pinned)
`apply_freeze.py` applied the five additive edits (17 cost rows); `byte_freeze_check_post.all_intact =
True` (1h/4h DomainSpec/materiality/episode byte-preserved). Post-freeze sha256
(`results/freeze_manifest.json`):

| Module | Post-freeze | Prior |
|---|---|---|
| `referee_adaptive.py` | `96c940b5…` | E5 `b4fd6cb1…` |
| `referee_calibration.py` | `d10e6a27…` | E5 `04f933f6…` |
| `incremental_referee.py` | `1b33e70a…` | `b0ad99b2…` |
| `referee_pstar.py` | `1fd06b28…` **UNCHANGED** | == E6 (no domain dict) |

Freeze written **before** any CF-MR-003 exec-15m adjudication (L-12 honored). Operating point
unchanged: q\*=0.75, Q_STUD_MIN=0.6745, N_BOOTSTRAP=500, α=0.05.

## 6. Audit caveats
Audit PASS, 0 Critical / 0 Warning / 3 Info (`audit.md`): (1) future-destroy 0.100 = single band-stress
artifact (non-material); (2) 15m battery ran the synthetic MDE substrate on first-49% TRAIN (slice-
agnostic, more conservative); (3) EP15=17 log-derived + manifest-recorded but not swept (verdict
invariant across M/N/S with EP15 fixed; optional hardening). None move the verdict. Causal-provenance:
candidate-blind (no CF-MR-003 read), leak tripwire collapsed, analysis-only (calibrates a gate,
generates no edge).

## 7. Conclusion & framing (important — not a rescue)

**FREEZE_LICENSED.** The renewed referee is now **15m-capable and frozen**; Track 2 is unblocked.

EXP-011 is a **referee prerequisite, NOT a CF-MR-003 rescue** (P-02 discipline). It makes the 15m cells
**adjudicable at all** — EXP-010 (1h) returned NOT-TRADABLE **(UNPOWERED)** on episode sparsity, *not* a
negative edge. The honest prior for T2a/T2b stays **LOW**:
1. More bars → more episodes *could* clear the power floor — **but** the 15m floors are **higher** by
   design (min_state_count 25 vs 20; min_effective_n 90 vs 60), partially cancelling.
2. Shorter-horizon reversion captures a **smaller** move against the **same** per-instrument round-trip
   cost → net likely **worse**.
3. Sister family **CF-MR-002** (causal RSI-2 fade) was **EXONERATED** (net-negative).

Expected T2a/T2b outcome: **still NOT-TRADABLE, but a POWERED verdict** (a definitive close, not a power
gap) — plus T2a covers **14 S3_DETREND** cells EXP-010 never tested. A small, genuine chance the extra
episodes surface an edge the 1h test could not power.

## 8. Follow-ups (separate experiments)
- **EXP-010 T2a/T2b** (price-primary, cTrader in-engine, operator-gated cost-bearing run): adjudicate
  CF-MR-003 exec-15m under the now-frozen 15m referee. Pay EXP-010 gate-debt F-1 (vehicle fidelity) /
  F-2 (leak-resistance) *before* booking any powered-positive.
- Optional: EP15 sensitivity sweep (belt-and-suspenders; not verdict-blocking).

## 9. Registry disposition
**registry: not a candidate screen — referee-renew methodology (0 reads / 0 slots).** No candidate-family
status change, no `multiplicity-registry.md` row, no `test-read-ledger.md` entry. The referee-freeze is
recorded as a governance/methodology event (E-series, mirroring E5/E6) in the master index live status;
`cf-mr-003.md` + the family index note the **15m-referee dependency for Track 2 is now satisfied**.

## Links
[design.md](design.md) · [audit.md](audit.md) · [code/run_experiment.py](code/run_experiment.py) ·
[code/apply_freeze.py](code/apply_freeze.py) ·
results: [license_verdict.json](results/license_verdict.json),
[freeze_manifest.json](results/freeze_manifest.json), [battery_15m.csv](results/battery_15m.csv),
[regression_anchor_check.json](results/regression_anchor_check.json),
[byte_freeze_check_post.json](results/byte_freeze_check_post.json) ·
plots: recovery_map_15m, fpr_by_stratum_15m, band_surface_15m

---

## GATE: APPROVE (orchestrator inline post-exec, 2026-07-01)

Checked `audit.md`, `report.md`, and index/registry updates against `references/governance-constraints.md`
+ the Phase-003 checkpoint:
- **Verdict forensics + causal-provenance/leak pass present** (`audit.md` §1/§3) — per-stratum
  re-derivation, mechanism (§10.3a STATE/SPARSE recovery survives the domain change, not DENSE-only),
  candidate-blindness traced, leak tripwire collapsed. ✓
- **Per-stratum masking check** — 16/16 is a count of independent per-instrument passes, not a pooled
  headline; band 112/112 confirms stability (L-03). ✓
- **Every verdict-material finding fixed-and-rerun** — none: audit PASS, 0 Critical / 0 Warning; the 3
  Info items are shown non-material (future-destroy 0.100 = single band-stress artifact; 15m substrate on
  first-49% is conservative; EP15 unswept but verdict-invariant). ✓
- **Regression anchor + byte-freeze** — 0/32 mismatch, P\*-identity 32/32, 1h/4h byte-preserved
  (`byte_freeze_check_post.all_intact=true`); freeze hash-pinned **before** any CF-MR-003 read (L-12). ✓
- **Registry disposition recorded** — referee-renew (D-referee), **not a candidate screen**: no
  candidate-family status change, no `multiplicity-registry.md` row, no `test-read-ledger.md` entry
  (0 counted reads / 0 slots, holdout sealed). The referee-freeze is logged as a governance/methodology
  event in the master-index E-series live status; `cf-mr-003.md` + the family index mark the 15m-referee
  dependency **satisfied**. ✓
- **Scope discipline** — analysis-only, no scope creep; framed as a referee prerequisite, not a P-02
  dead-entry rescue (honest LOW prior for T2a/T2b recorded). ✓

No REVISE issues. **EXP-011 COMPLETE.** The renewed referee is 15m-capable and frozen; EXP-010 T2a/T2b
are unblocked (next critical path, operator-gated cTrader runs).
