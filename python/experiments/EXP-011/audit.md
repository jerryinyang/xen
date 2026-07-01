# EXP-011 (E7) Audit — Referee 15m-Domain Extension

**Verdict: PASS — 0 Critical, 0 Warning, 3 Info. FREEZE LICENSED is supported.** The 15m-domain
extension is correctly built, candidate-blind (L-12), leak-clean (L-01), and leaves the frozen
1h/4h referee bit-identical. The freeze mechanics (`apply_freeze.py`) have **not** been run — the
frozen module source is still byte-frozen (== E5/E6). The audit supports proceeding to
`apply_freeze.py` (operator-gated) + Stage 5.

Scope: analysis-only (synthetic substrates + frozen referee primitives on aggregated 15m timebar
extracts). 0 counted reads, 0 candidate slots, holdout sealed. This is the L-12 governance-critical
review BEFORE the extended referee adjudicates a live candidate (CF-MR-003 exec-15m).

---

## 1. Verdict Forensics (per-stratum, non-pooled — L-03)

**Re-derived FREEZE_LICENSED from `battery_15m_full.json` (112 rows = 7 configs × 16 instruments).**
The headline is genuinely per-instrument×15m, not a pooled collapse — every one of the 16 prior
strata is emitted and adjudicated individually (`battery_15m.csv` rows: AUDJPY, BTCUSD, EURJPY,
AUDUSD, JP225, EURUSD, GBPUSD, GBPJPY, US2000, NZDUSD, US500, USDJPY, USDCAD, USDCHF, XAUUSD, USTEC).

| Metric (prior config, 16 strata) | Result | Per-stratum? |
|---|---|---|
| verdict | **16/16 DET_DOMINANT** | yes (per instrument) |
| `fpr_controlled` | **16/16 true** | yes |
| `dense_powered` | **16/16 true** | yes |
| STATE or SPARSE recovery >0 | **16/16** | yes |
| `pstar_identity` (P*-gate reduces to §10.3a) | **16/16 true** | yes |

**Mechanism (why it licensed) — §10.3a recovery genuinely survives the domain change, NOT
DENSE-only.** `state_delta_mde = MDE_frozen − MDE_adaptive` is **strictly positive on all 16 prior
strata** (3.5 on FX majors, 7.5–15.5 on JPY-crosses/indices/BTC), and `sparse_delta_mde` is positive
on 15/16 (11.5–23.5; JP225 sparse = NaN, one arm UNPOWERED — a coverage detail, not a regression).
That is the exact E2/E3a signature: the frozen conjunctive gate is STATE/SPARSE-blind, and the
adaptive §10.3a economic leg recovers it — and that recovery reproduces at 15m. DENSE is powered on
all 16, so DET-dominance is `MDE_adaptive ≤ MDE_frozen ∀ shape ∧ strictly < on ≥1` with the strict
gain coming from STATE+SPARSE — not DENSE detection masquerading as recovery. **The mechanism is the
same one E3a froze; E7 shows it is domain-portable.**

**Masking check.** No pooled figure is doing load-bearing work: the "16/16" is a count of independent
per-stratum passes, and the band table (§4) confirms the count is stable, not an average hiding a
flip. No heterogeneity is masked — the weakest cell (JP225, sparse UNPOWERED on one arm) still passes
via STATE recovery (`state_delta_mde=7.5`) and DENSE power.

**Gate-shape check.** The binding 15m gate (§10.3a adaptive) is the *correct* instrument for the
shapes tested — it is precisely the shape-adaptive gate E3a built to cure the frozen gate's
location-only blindness, and the positive SPARSE/STATE ΔMDE confirms it sees non-location shapes at
15m. No shape blindness introduced by the domain change.

---

## 2. Regression Anchor (binding correctness gate) — PASS

`regression_anchor_check.json`: **status PASS, n_strata 32, n_mismatch 0, pstar_identity_count 32.**
With the 15m rows injected in-memory, the 1h/4h §10.3a 3-arm DET reproduces EXP-003 **bit-for-bit**
(verdict + STATE ΔMDE to 1e-9 + adaptive dogfood-FPR to 1e-9) on all 32 strata, AND the E6 P*-gate
reduction identity (`gate_stack_pstar` with realized:=turnover == `gate_stack_adaptive`) holds
**32/32**. Spot-checked `regression_anchor.csv`: US2000/JP225/NZDUSD × {1h,4h} all DET_DOMINANT,
matching EXP-003.

**Byte-freeze — the "adds a domain, changes nothing else" claim holds.** `byte_freeze_check.json`
`unchanged: true`; the four frozen modules' sha256 are identical before/after the battery and match
the pinned E5/E6 values:
- `referee_adaptive.py` = `b4fd6cb1…ae847` (== E5)
- `referee_calibration.py` = `04f933f6…7994` (== E5)
- `referee_pstar.py` = `1fd06b28…4f23` (== E6)
- `incremental_referee.py` = `b0ad99b2…4c075`

Independently re-verified live: `shasum` on all four == the pinned values, and `grep -c '"15m"'`
returns **0** in all three domain-dict modules → the freeze has not been applied; the extension lived
entirely in in-memory dict mutation during the battery (the E4 candidate-blind injection pattern,
`inject_15m`, `run_experiment.py:186-198`). The anchor bit-identity is real, not a wiring artifact.

---

## 3. Causal-Provenance & Leak Pass (L-01) — CLEAN

**(a) Candidate-blindness (L-12 HARD GUARD) — CONFIRMED.** Traced every data path in
`run_experiment.py`: the only market input is `era_file_for()` →
`data/timebars/timebars_<inst>_20210602_*.parquet` (`:157-160`), aggregated to 15m via
`aggregate_ohlc` (`:172-175`). **No CF-MR-003 file, no EXP-008/009/010 event/output, no S3/S5 series
is read anywhere.** The 15m constants originate solely from the module-level mechanical priors
(`M15_PRIOR/N15_PRIOR/S15_PRIOR/EP15_DERIVED`, `:130-133`) and the OAT band (`build_band_configs`,
`:151-160`), injected by `inject_15m` (`:186-198`). The constants cannot be fit to the candidate —
they are literals derived from the frozen domain anchors. The freeze is written (by the separate
`apply_freeze.py`) only after the license, before any CF-MR-003 adjudication. Candidate-blindness
holds by construction.

**(b) Future-destroy tripwire — COLLAPSED (the planted edge dies under block-permute).** The control
(`future_destroyed_passrate`, `:305-315`) plants shape-`e`, block-permutes the returns to destroy the
position↔return alignment (L-07), and re-adjudicates. Distribution over all 112 rows:
**91 cells 0.000, 20 cells 0.050 (=1/20), 1 cell 0.100 (=2/20).** The planted 15m edge collapses to
FPR everywhere — proof the detected power is genuine alignment, not a leak.

- **Scrutiny of `future_destroy_max=0.100`:** it is a **single cell — M0.5/GBPUSD** (a materiality
  *stress* band member, `materiality=0.5`, NOT the prior/frozen config), 2 of 20 planted draws
  surviving. The guard is `max(dogfood_fpr + 2·hw, 2α)=0.10`; `0.100 > 0.10` is false → no tripwire
  trip, correctly. This is the textbook E4 single-draw artifact (`wilson_lower(2,20)=0.028 ≪` any
  control): at a *lenient* materiality floor a couple of block-permuted draws pass by chance. It is
  **not systematic** — the same instrument at the **prior** (frozen) config is 0.05, and dogfood FPR
  is **0.0** there. No stratum shows a systematic surviving edge. **Non-material to the freeze** (the
  frozen config is the prior; M0.5 is a probe that still returned DET_DOMINANT + fpr_controlled).

**(c) No-plant guard + dogfood standing null — CONTROLLED.** `tripwire_failures` is empty on all 112
rows (no-plant PASS ≤ guard everywhere). **Dogfood-negative FPR max = 0.000 across all 112 rows**
(4 null families: block-permute returns, reblock-random positions, Donchian-20, MA-20/50), and the
**skew-stressed FPR (E4 R3) max = 0.000** — FPR control is *perfect*, strictly better than the 2α
bound and matching the frozen 1h/4h suite's 0/32. The 15m dogfood ran on the **first-49% TRAIN**
slice (`load_slice_minutes(train_only=True)`, `:163-170` via `run_job` `:349`).

**(d) Fences.** Open-to-open ≤t-1 via `next_open_to_open_returns_from_bars` (frozen E0);
`aggregate_ohlc(min_coverage=0.90)` + analysis-boundary fence (`build_domain` `:172-175`); first-70%
for the anchor, first-49% TRAIN for the 15m battery; **holdout never sliced** (`load_slice_minutes`
slices only `[0, cutoff)` with cutoff ≤ int(N·0.7)). No bar-index alignment; `CloseTime` ordering.

**Shared-module contract.** E7 adds no new `xen` outcome/target module — it only mutates domain dicts
at runtime and (post-license) appends dict rows. The frozen §10.3a/E6 primitives are consumed
unchanged (byte-freeze §2). No `rct[di]` pattern; nothing price-primary (correctly analysis-only — it
calibrates a gate, generates no edge).

---

## 4. Gate-Threshold-Calibration (governance crux) — PASS

Every 15m constant is mechanically derived + battery-confirmed + sensitivity-banded — no magic
constant, nothing fit to the candidate.

| Constant | Value | Derivation (re-verified) | Battery outcome |
|---|---|---|---|
| `MATERIALITY_BPS["15m"]` | **0.75** | √-period `k·√15`, `k=1.5/√60=0.19365`; reproduces frozen **1h=1.5, 4h=3.0 exactly** (`0.19365·√240=3.0000`) | FPR 0.0; band M∈{0.5,1.0} both DET_DOMINANT |
| `min_effective_n` | **90** | log-period interp(5m 120, 1h 60) = 93.5 → 90 | N∈{75,105} both 16/16 ok |
| `min_state_count` | **25** | log-period interp(5m 30, 1h 20) = 25.6 → 25 | S∈{20,30} both 16/16 ok |
| `EPISODE_LENGTHS["15m"]` | **17** | log-period interp(5m 24, 1h 8) = 16.9 → 17 | fixed (substrate L); disclosed in manifest + design |
| cost `["15m"]` | inherit 1h | per-trade round-trip is domain-invariant (E1: only *per-held* over-charges turnover) | all 17 rows domain-invariant → inheritance exact |

**Sensitivity band is real, not a coverage gap.** Confirmed all **7 configs × 16 strata = 112 rows
actually ran** (`rows per config = {prior:16, M0.5:16, M1.0:16, N75:16, N105:16, S20:16, S30:16}`).
Every config is **16/16 DET_DOMINANT ∧ fpr_controlled ∧ dense_powered** → `band_flip_strata=[]` is a
genuine invariance result: the verdict does not flip anywhere in the pre-registered band. The prior
sits in the interior of a flat verdict region, not on a cliff — the floors are attainable at 15m (no
L-12 §2 near-impossible leg: DENSE + STATE + SPARSE all powered).

**EP15=17 rigor (flagged in the brief).** EP15 is a frozen referee-*consumed* constant
(`incremental_referee.EPISODE_LENGTHS`, read by the cost-amortization path) — it gets the **same
log-period derivation** as the floors and is recorded in the freeze manifest + design derivation
table. It was not swept (design scoped the band to M/N/S). Given it is the substrate block length and
the FPR/DET verdict is invariant across the M/N/S band with EP15 fixed, this is adequate; a formal
EP15 sensitivity sweep would be a belt-and-suspenders addition, not a gap that moves the verdict
(**Info-3**).

---

## 5. `apply_freeze.py` — correct, guarded, safe (not yet run)

- **Guarded:** refuses unless `license_verdict.json.verdict ∈ {FREEZE_LICENSED, RANGE_BOUNDED}`
  (`:120-128`); `--force` is an explicit operator override only.
- **Idempotent + additive:** each edit is a unique-anchor single replacement that no-ops if `"15m"`
  is already present (`_replace_once`, `:46-54`); asserts the anchor is unique (aborts otherwise).
- **Touches only the 15m rows:** re-verified live — the cost-map regex `\{"1h": (…), "4h": \1\}`
  (backreference ⇒ domain-invariant only) matches **17/17** rows; the simulated substitution
  **preserves every 1h/4h value** (`"EURUSD": {"15m": 1.0, "1h": 1.0, "4h": 1.0}`, BTCUSD 10.0…) and
  only inserts `"15m"`. DOMAIN_SPECS/MATERIALITY/EPISODE edits insert a new key beside the existing
  5m/1h/4h entries. `referee_pstar.py` is correctly not edited (no domain dict).
- **Post-edit self-check:** writes `byte_freeze_check_post.json` asserting the 1h/4h DomainSpec,
  materiality, episode, and adaptive-domains lines are textually intact (`:150-160`), and a
  `freeze_manifest.json` mirroring E5/E6 (operating point + 15m spec + derivation + before/after
  hashes).
- **Not yet run:** confirmed — `grep -c '"15m"'` = 0 in the frozen modules; no `freeze_manifest.json`
  exists; source hashes == E5/E6. Correct sequencing (freeze is Stage-4-clean + operator-gated).

---

## Findings

**No Critical. No Warning.** No finding can move the license verdict, a per-stratum FPR/MDE, the
regression-anchor bit-identity, candidate-blindness, or leak-cleanliness.

- **Info-1 (future-destroy 0.100).** Single band-stress cell M0.5/GBPUSD, 2/20 draws, at a lenient
  materiality; `wilson_lower(2,20)=0.028 ≪` control; the prior/frozen config for GBPUSD is 0.05 and
  dogfood FPR is 0.0. E4-class single-draw artifact, not a leak. **Materiality:** cannot move the
  verdict — the frozen config is the prior (fpr_controlled, future-destroy 0.05), and it did not trip
  the guard. Non-blocking.
- **Info-2 (15m battery on first-49% TRAIN).** `run_job` loads one first-49% slice for the whole 15m
  battery, so the *synthetic-positive MDE substrate* also runs on first-49% (design text scoped only
  the dogfood to first-49%, the MDE substrate to first-70%). **Materiality:** none — the synthetic
  plant is slice-agnostic noise; more conservative, still holdout-clean. Non-blocking.
- **Info-3 (EP15 not swept).** Episode length 17 is log-period-derived + manifest-recorded but has no
  dedicated sensitivity band (only M/N/S swept). **Materiality:** none — verdict is invariant across
  the M/N/S band with EP15 fixed, and DENSE/STATE/SPARSE are all powered (floor attainable). A future
  EP15 sweep is optional hardening, not a verdict gap. Non-blocking.

---

## Causal-Provenance & Leak — Summary

Provenance traced: the only decision inputs are frozen-E0 open-to-open ≤t-1 returns on first-49%/70%
in-sample 15m bars; the 15m constants are literals from the frozen domain anchors, never from the
candidate. Leak tripwire shipped and **collapsed** (dogfood FPR 0.0, future-destroy ≤0.10 single 2/20
artifact, no-plant clean). No shared-module contract touched; not price-primary (calibrates a gate).
Numeric reproduction was confirmed (anchor 0/32, 112/112 DET_DOMINANT) **and** the mechanism +
provenance were traced independently — this audit is not a numeric-only certification.

**The 15m-extended referee is correctly built, candidate-blind, and leak-clean. FREEZE LICENSED is
supported → proceed to `apply_freeze.py` (operator-gated) + Stage 5.**
