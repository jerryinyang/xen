# EXP-003 (E3a) Audit — Economic-Leg Adaptive Gate, 3-arm DET-dominance

**Verdict: PASS (CHARACTERISATION trustworthy).** Numbers reproduce; mechanism independently
established; leak tripwires hold; D0 "L1 rigid" honored; `referee_calibration.py` byte-frozen;
causal provenance clean; perf optimizations bit-identical. **No Critical findings; no forced
rerun.** Two Warning findings carry **mandatory interpreter framing** (F2 sparse mechanism, F3
FPR-split brittleness) — the headline "15 DET_DOMINANT / 17 FPR_BROKEN" is correct per the
predeclared rule but materially misleading and must be reframed as a spectrum in `report.md`.

Scope: analysis-only. 32 strata (16 inst × {1h,4h}; DE30 absent). First-70% slice; global holdout
untouched. 0 TEST reads, 0 slots. Three arms: `frozen` = `gate_stack_core_costfn(strategy_return_bps)`
(per-held), `frozen_amortized` = same with `strategy_return_bps_turnover`, `adaptive` =
`gate_stack_adaptive`.

---

## Headline result (re-derived, corrected)

| | value |
|---|---|
| Predeclared split | 15 DET_DOMINANT / 17 FPR_BROKEN |
| **Corrected (Wilson-resolved) FPR breaks** | **1 / 32** — only JP225/4h (6/162, CI-lo > 0) |
| FPR_BROKEN with Wilson CI-lower ≤ 0 (≈ indistinguishable from 0) | **16 / 17** |
| FPR_BROKEN driven by ≤2 dogfood passes (1–2 / 162) | 10 / 17 |
| STATE ΔMDE (frozen − adaptive), finite n=32 | median 10.5, range 7.5–24.0 bps |
| Sparse adaptive-recovered (frozen UNPOWERED → adaptive finite) | 28 / 32 (14×1h + 14×4h) |
| Adaptive dogfood FPR | max 0.037, mean 0.0073; frozen & frozen_amortized exactly 0 |

The robust finding: **the adaptive gate uniformly and largely lowers STATE MDE (and recovers
sparse) at a small sub-population-driven dogfood FPR that is, on 31/32 strata, within sampling
noise of frozen's exact zero.** The binary DET/FPR_BROKEN partition is sampling-noise-sensitive
in **both** directions and must not be read as "17 genuine FPR regressions."

---

## Verdict Forensics

### F1 — D0 "L1 rigid": HONORED. Orchestrator's stated mechanism REFUTED. *(Info, governance-clarifying)*

The pre-audit hypothesis was that amortized accounting shifts `estimate_block_length` →
`effective_n` → sparse clears L1 (a possible back-door L1 loosening = D0 violation). **Traced
term-by-term on EURUSD/{1h,4h}, XAUUSD/4h, AUDJPY/4h: L1 is BIT-IDENTICAL between the frozen and
adaptive arms** — same `effective_n`, same `block_length` (=1 on this substrate), same episode
counts. Proof points (sparse, e=32):

| stratum | frozen L1 | adaptive L1 | eff_n (both) | bl (both) | ep counts (both) |
|---|---|---|---|---|---|
| EURUSD/1h | False | False | 6462 | 1 | (51,63,16,27) |
| EURUSD/4h | True | True | 1580 | 1 | (26,23,9,16) |
| XAUUSD/4h | True | True | 1360 | 1 | (24,18,12,13) |

Why identical: L1 = `effective_n ≥ min_effective_n AND min(episode_counts) ≥ min_state_count`.
The episode-count term comes from `_episode_counts(positions)` — **position-only, cost-invariant**
→ identical across arms by construction. The `effective_n` term uses `block_length` from the
cost-charged series, but `estimate_block_length` returns **1** for these low-autocorrelation
substrates in *both* conventions, so `effective_n = len(test)` identically. **The only L1 term that
ever binds on this substrate is `min_state_count` (coverage), which is cost-independent.** D0 is
satisfied not by the claimed effective_n story but because L1 is literally the same computation
producing the same value. **No D0 violation. Not Critical.** `referee_adaptive.py:413-414` (adaptive
L1) is the same expression as `:270-273` (frozen-seam L1).

### F2 — Sparse "recovery" is economic-leg adaptation, NOT L1. Design predeclaration refuted. *(Warning — mandatory interpreter framing; orthogonal to verdict numbers)*

Sparse L1 is **domain-specific**: FAILS on 1h (`min_state=20`; ~6%-active draws give test-episode
counts ~16–27, straddling 20 → ~coin-flip per draw) but PASSES on **every** 4h stratum
(`min_state=8`). Where sparse clears L1, the *frozen* gate still reports UNPOWERED (28/32 frozen
sparse MDE = inf) — so frozen sparse blindness on those cells is driven by the **economic composite
(L4 both-segment positivity + pooled L5 hard veto + L2)**, not L1. The `adaptive` composite
(power-aware L3/L5 + sub-pop L5, L4/L2 removed) passes them → sparse becomes detectable (MDE down to
0.5 bps on 1h, 4–24 bps on 4h).

Consequences:
- **The design's predeclaration "sparse stays UNPOWERED by design (L1 rigid)" is REFUTED.** Sparse
  recovery (28/32) is real (no_plant ≤ 0.05; future-destroy ≤ 0.05 — §Leak). It is D0-compliant
  (the recovery is in L3/L5, the sanctioned legs) and an *over-delivery* vs the STATE-only E3a scope.
- **E2's "sparse blindness = L1 structural veto, edge-independent" was domain-conflated** — true on
  1h, false on 4h. The interpreter must correct this cross-experiment, and E3b/E5 scope (which
  assumed sparse stays out) must absorb that the economic adaptation also moves sparse.

Materiality: this finding changes *narrative/scope*, not any computed number. The MDE/FPR values
stand. Not Critical.

### F3 — FPR_BROKEN binarization is brittle (the central caveat). *(Warning — mandatory interpreter framing; NOT a rerun)*

`classify_stratum` (`run_experiment.py:247`) assigns FPR_BROKEN on a **strict point comparison
`dogfood_adaptive > dogfood_frozen` with `dogfood_frozen ≡ 0`** — so a *single* dogfood pass
(1/162 = 0.0062) trips it. Re-derived per stratum:

- 16/17 FPR_BROKEN have adaptive-FPR **Wilson CI-lower ≤ 0** → indistinguishable from zero.
- 10/17 rest on 1–2 passes. Only **JP225/4h (6/162, CI-lo > 0)** is a statistically-resolved
  nonzero FPR. All are far below the predeclared `FPR_CONTROL_BOUND = 0.10`.
- The 15 DET_DOMINANT are all *exactly* 0 passes — equally a function of "no draw happened to
  pass," not a proof of FPR-safety.

So the 15/17 split is largely **sampling-noise-determined**. The honest, robust reading:
*adaptive carries a small subpop-driven dogfood FPR (point est 0–3.7%, one stratum Wilson-resolved
> 0), uniformly recovering STATE/sparse.* The `report.md` MUST present FPR_BROKEN strata with their
Wilson CIs and state that only JP225/4h resolves as a genuine break; it must NOT headline "17 FPR
regressions."

**Materiality reasoning (why Warning, not Critical/rerun):** every verdict-bearing *number*
(per-stratum FPR, MDE, ΔMDE) is correct and reproduces; a rerun of the same code yields identical
labels. The brittleness is in the *binarization rule*, which is the **predeclared, GATE-APPROVED
binding endpoint** — re-binarizing post-hoc would be moving goalposts, an interpreter/operator
decision, not an auditor code fix. The per-stratum FPR + Wilson CIs are all persisted for the
interpreter to re-bin. Recommend E5 adopt a noise-tolerant rule (e.g. adaptive-FPR Wilson CI-lower
> frozen, or > control bound) — logged as a follow-up, not a fix to E3a.

### F4 — "sparse must stay UNPOWERED" tripwire is mis-specified but orthogonal. *(Warning — no rerun)*

`run_experiment.py:294-295` appends a tripwire failure whenever adaptive sparse MDE is finite. It
fired 28× (every recovered sparse stratum). It encodes the refuted prior (F2), not a correctness
invariant. **Confirmed orthogonal to every verdict number:** `classify_stratum(mde, dogfood)` reads
only MDE + dogfood; the `failures` list is logged only, never feeds `summary["verdict"]`. Removing
the assertion is bit-identical on all CSVs. Recommend deleting/reclassifying it for run-log
cleanliness (and replacing with the F3 noise-tolerant FPR tripwire) — but **no rerun required**.

### F5 — FPR mechanism = the q*=0.75 sub-population path, exclusively. *(Info)*

Traced dogfood `leg_results` on JP225/4h (6 FP), GBPUSD/4h (4), AUDJPY/4h (3): **every** false
positive passes with `L5_subpop_pass=True, L5_pooled_pass=False`. The frozen pooled-mean L5 rejects
all of them. On high-dispersion 4h instruments the 75th-percentile of per-episode means clears
materiality even on reblocked-random noise (JP225/4h subpop CI-lower 11–16 bps), explaining the 4h
concentration of breaks. **The same subpop quantile leg is the sole engine of both the STATE/sparse
recovery and the dogfood FPR** — they are two faces of one mechanism. This is the predeclared
design risk realised, not a bug.

### Gate-shape / masking
Pooled headline masks heterogeneity (F3): the equal-weight "17 broken" hides that 16 are
noise-level and the break concentrates on high-volatility 4h. STATE recovery is homogeneous
(ΔMDE > 0 on all 32, no_plant ≤ 0.05). The 3-arm decomposition cleanly separates E1 accounting
(frozen→frozen_amortized, e.g. EURUSD/4h 12→8) from E3a leg-adaptation (frozen_amortized→adaptive,
8→1) — both contribute to STATE recovery.

---

## Causal-Provenance & Leak

- **Leak tripwire (future-destroy) — HOLDS.** Adaptive STATE future-destroy `fd_max ≤ 0.05` on
  31/32 (GBPUSD/4h at the 0.10 control boundary, not `>` guard → not a failure; 2/20 at the 2α
  level by construction). Sparse `fd_max ≤ 0.05`. Recovery collapses under permutation → **real,
  not noise-mining**, including via the subpop path. No surviving sub-pop pass = no leak.
- **no-plant guard — clean.** Adaptive no_plant ≤ 0.05 everywhere (< guard ≥ 0.10).
- **Provenance.** Returns = open-to-open `≤ t-1` (`next_open_to_open_returns_from_bars`,
  `referee_adaptive.py:135`, last bar dropped). Dogfood donchian/ma lagged +1 bar via
  `lag_open_to_open` (`run_experiment.py:121,234-235`) → `lagged[i]=raw[i-1]`, acts at next open on
  bars `≤ t-1`, no look-ahead. Planted edges (`dense/tail/state_*_planted`) are exogenous oracle
  drift added to returns, not tradable signals. Synthetic substrates read no OHLC (no lag needed).
  First-70% slice via `load_analysis_minutes` (`:98-102`); global holdout never collected.
- **Price-primary check:** N/A — analysis-only on synthetic positions + planted oracle edges + real
  return *substrate*; no signal is generated from price (the dogfood donchian/ma are nulls, not the
  object under test). Correctly classified.

## Seam / shared-module integrity

- `referee_calibration.py` **byte-frozen** — `git diff` empty (not in modified set).
- `gate_stack_adaptive` reuses frozen primitives unchanged (`estimate_block_length`,
  `_episode_counts`, `_gate_bootstrap_pair`, `materiality_bps_for`, `resolve_split_index`,
  `naive_momentum_positions`, `ci_from_means`, `_stationary_block_indices`, `finite_values`). L1 +
  neutral/naive bootstrap pair are the same code path as `gate_stack_core_costfn` (verified line by
  line). L2 removed cleanly (no `l2` key, absent from composite). Composite rule confirmed:
  `passed = l1 AND ("FAIL" not in [l3,l5]) AND ("PASS" in [l3,l5])` (`:447`) — ABSTAIN never vetoes,
  all-abstain cannot pass.
- Sub-pop path candidate-blind: `q*=0.75`, `MIN_EPISODES_SUBPOP=5`, materiality are fixed module
  constants; statistic computed on the test net series with **no state mask** (`episode_net_means`
  reads positions+net only). Q5 satisfied.

## Perf optimizations — safe

- Early-stop in `detection_rate` (`:172-181`): denominator stays `N_PLANT`; break only once the
  `rate ≥ POWER_TARGET` decision is locked → MDE bit-identical. `no_plant_passrate` /
  `future_destroyed_passrate` / `dogfood_fpr` use **separate full-loop** functions (no early-stop) →
  unaffected.
- `ProcessPoolExecutor` over instruments (`run_instrument` worker): all seeds are explicit per-draw
  (`6000+k`, `7000+k`, `1000+k`, …), independent of instrument/scheduling order.
- **Independently verified bit-identical** (MDE + dogfood FPR + per-stratum verdicts) on EURUSD vs
  the pre-optimization baseline. Both verdicts DET_DOMINANT, all MDE/FPR columns equal.

---

## Findings ledger

| ID | Class | Verdict-material? | Rerun? |
|---|---|---|---|
| F1 D0 L1-rigid honored (mechanism corrected) | Info | No — L1 proven identical | No |
| F2 sparse recovery = economic legs; design "UNPOWERED" refuted | Warning | Narrative/scope only | No |
| F3 FPR_BROKEN binarization brittle (16/17 within noise of 0) | Warning | Numbers correct; framing must change | No |
| F4 mis-specified sparse-UNPOWERED tripwire | Warning | Orthogonal (logged, not in classify) | No |
| F5 FPR driver = subpop q*=0.75 leg, exclusively | Info | No | No |

**No Critical findings. Pipeline proceeds to Stage 5** with mandatory interpreter framing on F2+F3.
The interpreter must (a) report only JP225/4h as a Wilson-resolved FPR break and present the rest as
within-noise; (b) correct the sparse mechanism cross-experiment vs E2; (c) frame the subpop path as
the single engine of both recovery and FPR; (d) route the noise-tolerant FPR rule + tripwire fix to
E5/E3b as new scope.

---

# A1 Re-Audit (2026-06-29) — studentized sub-pop L5 + noise-tolerant verdict

The above (raw-bps) audit drove operator Amendment A1: the sub-pop L5 path is now **studentized**
(`q*-quantile / std` block-bootstrap CI-lower > `Q_STUD_MIN = Φ⁻¹(0.75)` **AND** raw-bps CI-lower
> `materiality_bps`); `classify_stratum` is noise-tolerant (Wilson-resolved); the mis-specified
sparse tripwire removed. Prior `results/` hard-deleted; full 32-stratum rerun. **Re-audit verdict:
PASS — both A1 defects cured at the gate, no regression, no new leak. 0 Critical.**

## Rerun headline (re-derived)

| | raw-bps (orig) | A1 studentized |
|---|---|---|
| Verdicts | 15 DET / 17 FPR_BROKEN | **32/32 DET_DOMINANT** |
| Adaptive dogfood FPR > 0 | 17/32 (max 0.037) | **0/32 (max 0.0000)** |
| STATE ΔMDE median / max | 10.5 / 24.0 | **7.5 / 23.5** (all 32 finite) |
| Per-shape regressions (adaptive worse than frozen) | 0 | **0** (DENSE/TAIL/STATE 32/32; SPARSE 28/32, frozen 2) |

## R1 — FPR cure is the GATE, not the label *(verified, governance-critical)*

Reconstructed the dogfood nulls on the three prior-worst strata under the **amended** gate:
**`passes_adaptive = 0/162` on JP225/4h, GBPUSD/4h, AUDJPY/4h.** Traced the previously-passing
reblock-random draws: `raw_ci_lower` still clears materiality (e.g. JP225/4h 15.9, 8.7, 4.3 bps —
the old leak) but `stud_ci_lower` (0.52, 0.27, 0.15) **< Q_STUD_MIN 0.674** → the **studentized leg
itself rejects them**. So FPR→0 is the gate fix (the leg no longer fires on high-σ noise), not
merely the noise-tolerant relabel. The relabel (Wilson-resolved `classify_stratum`) is also present
and correct, but here it is not even load-bearing — actual passes are 0. ✔

## R2 — STATE recovery retained; A1.5 over-suppression did NOT trigger *(verified, mechanism)*

STATE ΔMDE stayed large (median 7.5, all 32 finite; ~3 bps below the raw run's 10.5 = expected
studentized conservatism). Per-draw breakdown at the detected MDE (20 draws, `all-abstain-passes=0`
everywhere → **no abstain loophole**; every pass carries a genuine economic-leg PASS):

| cell | mde | passed | via pooled | via studentized-subpop |
|---|---|---|---|---|
| BTCUSD/4h | 12 | 10/20 | 10 | 0 |
| XAUUSD/4h | 8 | 11/20 | 10 | 7 |
| EURUSD/4h | 4 | 17/20 | 0 | **17** |
| USDJPY/4h | 8 | 16/20 | 11 | 12 |

**Mechanism:** STATE recovery is pooled-**OR**-studentized-subpop, and **both are load-bearing**.
Strong/high-cost edges (BTCUSD/4h) clear the **pooled** floor once amortized accounting un-dilutes
the mean. Low-cost diluted edges where the pooled mean sits below materiality (EURUSD/4h, mde 4 →
pooled ≈ 2 < 3) are carried **solely by the studentized subpop** (17/17). Why a real diluted edge
clears the studentized floor while high-σ noise does not: a genuine edge shifts the **location** of
the upper-quartile episode-mean above the null-shape level (studentized → 1–2+), whereas pure
dispersion leaves the studentized q* at ≈ `Φ⁻¹(0.75)=0.674` regardless of scale. ✔

## R3 — Future-destroy collapses on the studentized path *(leak tripwire, holds)*

Adaptive future-destroy `fd_max`: STATE **0.000/32**, SPARSE **≤ 0.050** — well under the 0.10
control. The studentized quantile does **not** survive permutation (a permuted edge loses the
upper-quartile location shift → studentized falls back to ~0.674 → fails). No noise-mining. ✔

## R4 — Sparse 28/32 recovery real; removed tripwire orthogonal *(verified)*

Sparse `no_plant ≤ 0.050`, `fd_max ≤ 0.050` → real. `classify_stratum` reads only `mde` + `dogfood`;
the deleted sparse assertion never fed a verdict (confirmed) → removal changed no verdict-bearing
number. ✔

## R5 — Q_STUD_MIN candidate-blind *(verified, Q5)*

`Q_STUD_MIN = NormalDist().inv_cdf(SUBPOP_QUANTILE)` computed at module load from `q*` alone
(`referee_adaptive.py`) — reads no data, no FPR, no outcome, no state mask; could not be tuned on
results. The studentized statistic consumes only the **test** net series + positions (no future bar,
no mask). The conjunction leaves the frozen `materiality_bps` (1.5/3.0) untouched. ✔

## R6 — Seam / provenance / determinism *(verified)*

`referee_calibration.py` **byte-frozen** (git diff empty). `gate_stack_adaptive` L1 expression is
identical to `gate_stack_core_costfn` (lines 272 vs 465; A1 is within-L5 only — L1 untouched, still
rigid/bit-identical). Studentized bootstrap deterministic (distinct sub-seed `+4` vs raw `+3`;
per-resample `std==0 → 0.0` guard; full-sample `std==0 → ABSTAIN`). Open-to-open `≤t-1`; dogfood
don/ma lagged +1; first-70% slice; global holdout untouched. Noise-tolerant `classify_stratum`
Wilson math correct (`wilson_interval(passes, draws).lower`). Perf (ProcessPoolExecutor + MDE
early-stop) unchanged by A1 — denominators/seeds/determinism intact; early-stop unaffected (decision
boundary identical). ✔

## R7 — Materiality

No verdict-material finding. Both defects cured at the gate with zero regression; the studentized
floor is genuinely load-bearing (not an abstain loophole), leak-clean (future-destroy collapses),
and candidate-blind. **No further fix+rerun required.** *Info (non-blocking):* the studentized floor
costs ~3 bps median STATE ΔMDE (10.5→7.5) — small, expected conservatism, disclosed; a `Q_STUD_MIN`/
`q*` sensitivity sweep remains an E4 robustness item. The gate is now a clean DET-dominant
candidate; E5 (freeze) is the natural next rung. E3b shrinks to composite-form selection (Q4) only.
