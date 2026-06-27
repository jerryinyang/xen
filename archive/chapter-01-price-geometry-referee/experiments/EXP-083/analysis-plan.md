# Analysis Plan: Experiment EXP-083 — TRAIN-Only Candidate Screen Behind the Separability Gate (CF-CAPGEO-001 / HYP-004a)

## Objective

Decide, **on TRAIN data only and gross**, which `{exit-candidate × substrate × instrument × domain}`
combinations are **valid candidates** — i.e. clear the cheap **G-018a** gross screen *and* pass the
binding **separability gate** (S1 attribution ∧ S2 tail non-residual) — over the 3 frozen derived exits
(`D1/D2/D3`) plus the full enumerated benchmark exit grid, applied to the 4 frozen substrates' held
positions across the 46 EXP-080 member cells. Emit, freeze, and **sha256-hash-pin** the surviving
valid-candidate set + the pre-declared Holm correction rule as the binding hand-off artifact for the
deferred counted-read confirmation (EXP-084). **No TEST stratum is sliced, no holdout is touched, no
counted read is spent, and the frozen referee suite is not invoked here** (all EXP-084). Verdict ∈
{`SCREEN_DELIVERED` (≥1 survivor) | `ALL_CANDIDATES_FAIL` (empty set → G-018 closure, 0 lifetime reads
ever spent)}. The crux (EXP-082): the derived adverse leg reproduces the CF-HA-HARAMI-001 "harvest the
median, leave the catastrophe" geometry, so **S2 is the binding shape-guard** and is expected to be the
leg most candidates fail on.

All methods are **non-parametric / moving-block bootstrap / matched-control**, on **real-price** ATR-unit
returns, per-stratum (no pooling as a binding statistic — LESSON-001). Constants are the D4/D9 frozen
values; nothing is tuned against outcomes.

---

## Methodology

### Step 0 — Provenance & frozen-constant assertions (no market data)

- **Method**: hard assertions before any read — (a) import `xen.capgeo_exits` and assert
  `sha256(derive_barriers source) == 34d03f45…` (the EXP-082 pin); (b) assert the EXP-080
  (`READINESS_DELIVERED`, 46-cell member set), EXP-081 (`CHARACTERISATION_DELIVERED`, 184 cells, 0
  underpowered, `holdout_untouched`), and EXP-082 (`DERIVATION_DELIVERED`, 552 triples) `run_metadata.json`
  fingerprints; (c) load the EXP-080 member-cell list (the only cells screened); (d) record the D4/D9
  frozen constants (`K_tail=3.0, τ_tail=0.06, δ=0.40, m_cell=Q95(null CI_low), N_BOOT=10_000`, S2 floor
  `n≥120`, event floor `≥30`) into `run_metadata.json`.
- **Why**: makes EXP-083 provably derived from the audited upstream chain and pins the binding rule that
  EXP-084 re-imports; a mismatch is a HALT (process-level Evidence AGAINST), not a result.
- **Simpler alternative**: trusting the files without hashing — rejected; the whole "many candidates, one
  honest read" legitimacy (D4.1) rests on the freeze/hash chain.
- **Assumptions**: none statistical.
- **Expected output**: assertion log + frozen-constant block in `run_metadata.json`.

### Step 1 — Per-cell entries & forward paths (TRAIN region only)

- **Method**: per member cell, load the 5-year file (latest-glob), slice the **first-70% analysis set**,
  build domain bars via the holdout-fenced `build_domain_bars` (`min_coverage=0.90` + analysis-boundary
  fence), take the **TRAIN sub-split** `[0, train_cutoff)` (`train_cutoff = int(len(analysis)*0.7)`).
  Generate the 4 substrates' entries with the frozen `xen.capgeo_substrates` interface
  (`avwap_entries`, `harami_native_entries` shared by both harami substrates, `random_entries` with
  `n_target` matched to the substrate-cell's entry count, seed fixed). Materialize each event's **real-OHLC
  forward path** (high/low/close from entry+1 to the per-event cap), the entry ATR (Wilder ATR(14)), and
  direction — the same inputs `xen.capgeo_geometry.lifetime_path_geometry` consumes.
- **Why**: reuses the frozen, audited substrate + geometry path EXP-080/081 already validated; the
  matched-random control is the same `random_entries` null used throughout the family.
- **Simpler alternative**: reusing EXP-081's `per_event_geometry.parquet` directly — insufficient, because
  EXP-081 computed MFE/MAE/TTP over the *adaptive cap*, not the per-event first-touch under each candidate's
  `(T_fav, S_adv, H_cap)`; EXP-083 must resolve the actual exit. Entry **populations** are reused/asserted
  identical to EXP-080/081 (EXP-042 same-denominator invariant).
- **Assumptions**: causal — only bars at/after entry are read; entries land on completed closes
  (look-ahead-safe by construction); cross-view alignment by timestamp/`entry_epoch`, never bar index.
- **Expected output**: per-cell `{entry_idx, entry_epoch, atr_entry, direction, forward OHLC window}` for
  each substrate; `n_usable` per cell (assert == EXP-081 within the TRAIN region).

### Step 2 — Exit application → per-event realized ATR return (the candidate surface)

- **Method**: for each candidate exit, resolve **per-event first-touch** of the three barriers on the
  real-OHLC forward path and record the realized **ATR-unit return** at the exit bar (real prices). The
  **fill / intrabar tie-break convention is the EXP-054 P15 standard** (the adopted 014-B fill model) —
  frozen, applied identically to every candidate and every substrate (incl. matched-random). Candidate
  surface (frozen, enumerated):
  - **Derived (3):** `(T_fav, S_adv, H_cap)` from the pinned `derive_barriers` **re-fit on this cell's
    TRAIN-region** EXP-081-style statistics (`mfe_med/mfe_q40/ttp_med/ttp_q75/mae_q90/m_anti`), via the
    *same* function EXP-082 locked. (D1≡D2 numerically wherever `m_anti` is NaN or `<MAE_q90`, but carried
    as distinct items.)
  - **`/EXIT-RR`:** triple-barrier with `T_fav = R·S_adv`, `S_adv = MAE_q90`, `H_cap = TTP_q75`, for
    conventional `R ∈ {1.0,1.5,2.0,3.0}` (reuse `xen.favourable_targets.barriers_from_distance` +
    `xen.adverse_targets.barriers_with_adverse`).
  - **`/EXIT-TRAIL`:** ATR trailing stop at `k ∈ {1,2,3}`·ATR + a ZigZag-structure trailing arm
    (`xen.zigzag` / `xen.position_exits.resolve_legs`), each capped at `TTP_q75`.
  - **`/EXIT-VP`:** POC and value-area-70% favourable targets via
    `xen.favourable_targets.volume_profile_levels` (**`TickVolume` proxy — disclosed**), `S_adv = MAE_q90`,
    cap `TTP_q75`.
  - **`/EXIT-PARTIAL`:** named **PARTIAL-V2A**, **V2A-ADVNONE**, **AVWAP-FH** arms reproduced via
    `xen.position_exits` / `xen.exit_rules`, plus a generic ≤3-leg favourable-scaling menu.
  - **`/SIZE-VOLADJ`:** overlay — scale each event's return by an inverse-ATR(entry) sizing factor
    (vol-normalized), scored as the **difference vs the unit-size (raw) baseline** of the same exit.
  - The enumerated benchmark list is **finalized and frozen in this plan's companion constant block before
    any TRAIN read** (it is the countable surface, not a sweep). The cost layer is **OFF** (gross screen,
    operator decision 2026-06-22).
- **Why**: reuses the audited exit/barrier kernels; the P15 fill standard is the family's frozen
  realistic-fill convention (EXP-054), preventing optimistic tie-breaks from manufacturing edge.
- **Simpler alternative**: scoring on the EXP-081 lifetime MFE/outcome — rejected; that is the *available*
  geometry, not what an exit *realizes*. The whole family question is realized capture, so the exit must be
  resolved.
- **Assumptions**: first-touch on real OHLC is causal; ties broken adverse-first (P15) so no look-ahead
  optimism; identical event set across candidates (EXP-042 guard — exits never change the denominator).
- **Expected output**: per `{substrate × cell × candidate}` an array of per-event realized ATR returns on
  the common `n_usable` event set.

### Step 3 — G-018a gross screen (cheap, vs SUB-RANDOM + matched-random)

- **Method**: per `{substrate × cell × candidate}`, compute on the realized-return array, in
  entry-time order, via **moving-block bootstrap** (block `b=max(1,round(m^(1/3)))`, `N_BOOT=10_000`,
  one-sided 95% lower bound; reuse the block construction in
  `xen.favourable_targets.paired_median_contrast_ci` / `xen.expectancy` kernels, extended to the mean):
  1. **gross expectancy** (mean ATR return) `CI_low_1s > 0`;
  2. **gross median** ATR return `CI_low_1s > 0`;
  3. **beats matched-random** — paired moving-block CI of `median(candidate) − median(matched_random)`
     on the same cell (`paired_median_contrast_ci`), and the mean analogue, `CI_low_1s > 0`. The
     **per-cell matched-random control** = `random_entries` on the same instrument×domain with the
     **identical exit applied** (so the contrast isolates the entry, holding the exit fixed). `SUB-RANDOM`
     (the 4th substrate) is reported alongside as the substrate-level attribution null (disclosure).
  - **G-018a PASS** = legs (1) ∧ (2) ∧ (3). Tail is *disclosed* here (binding tail-shape is S2).
  - **Guard (i)** (D6): at effective-n ≤ 60, defer the expectancy leg to the median leg (the bimodal
    mean-null under-coverage region) — recorded per cell.
- **Why**: the cheap "fail cheaply first" screen (design §4) — eliminates obviously-null candidates before
  the costlier separability decomposition; matched-control beats absolute-zero because the family's null is
  same-substrate random, not zero (CF-CAPGEO discipline).
- **Simpler alternative**: a single mean t-test vs 0 — rejected (assumes normality; ignores the
  same-random null and the regime-clustered dependence the moving block captures).
- **Assumptions**: exchangeability of blocks under the null; block length captures intra-regime
  dependence; paired contrast cancels shared event/regime noise.
- **Expected output**: per-candidate gross expectancy/median/matched-excess `CI_low`, G-018a pass flag,
  guard-i flag.

### Step 4 — Separability S1 (attribution: the obstacle moves without moving the edge)

- **Method**: additively decompose each candidate's gross expectancy (EXP-031 precedent, additive to
  machine precision) into:
  - `X_full` = expectancy with the full `(T_fav, S_adv, H_cap)`;
  - `X_fav` = expectancy with the **adverse leg at a neutral reference** (stop removed / set to the
    time-cap-only exit), i.e. favourable-target + time-cap contribution only;
  - `X_tail = X_full − X_fav` = the stop-truncation contribution (verified additive to ≤1e-9).
  **S1 PASS iff `X_fav` independently beats the per-cell matched-random control** — moving-block CI of the
  `X_fav` matched-control excess with `CI_low > m_cell`, where `m_cell = Q95(null CI_low)` is the
  per-cell synthetic-null-calibrated margin (the EXP-027/070 `m_cell` standard; calibrated FPR ≤ 0.05,
  Wilson-hi ≤ 0.075). A candidate whose edge is **entirely `X_tail`** (`X_fav ≈` matched-random) is a
  capture-bound / tail-truncation artifact → **FAIL**.
- **Why**: this is the inherited single-most-actionable lesson (retrospective §4.1) — it directly asks
  whether the favourable signal survives once the catastrophe-stop's contribution is removed.
- **Simpler alternative**: reporting `X_full` only — rejected; it cannot distinguish a real entry edge from
  pure stop-truncation, which is exactly the prior-family death mode.
- **Assumptions**: additive decomposition holds (verified numerically per candidate); `m_cell` calibration
  controls the edge-call FPR.
- **Expected output**: per candidate `X_full, X_fav, X_tail, x_fav_excess_CI_low, m_cell, s1_pass`.

### Step 5 — Separability S2 (tail non-residual: the binding shape-guard ASS lacks)

- **Method**: after the candidate's exit is applied, re-measure the candidate's **own** realized outcome
  distribution and the matched-random control's post-exit distribution with `xen.capgeo_geometry.tail_stats`
  (`K_tail=3.0`). **S2 PASS iff** post-exit `tailmass ≤ τ_tail = 0.06` **AND** post-exit
  `q05 ≥ q05_control − δ`, `δ = 0.40` ATR. The two legs are complementary (tailmass catches a separated
  `B_zero` mode; relative-q05 catches deep `B_neg` catastrophes); S2 fails if either trips. **Operating
  floor `n ≥ 120`**: cells with `n_usable < 120` get `s2_deferred = True` (D4 default; reported as a
  candidate but flagged, adjudication carried at EXP-084 by the frozen suite + median/tail disclosure).
  Disclose the residual `B_pos` blind spot (D9, benign).
- **Why**: G-017 proved `ASS`'s tail diagnostic is structurally blind to the subtle median-positive
  minority-catastrophe shape; S2 is the binding replacement built directly on minority-mass, and EXP-082
  flagged it as the crux for the derived exits.
- **Simpler alternative**: trusting `ASS`'s tail flag — rejected by G-017 (the exact blind spot that killed
  the prior family).
- **Assumptions**: the minority-mass boundary `median − 3·MAD` separates the catastrophe mode where it is
  separated; thresholds frozen at the D9 bite-check (ROC-calibrated false-flag ≤0.05 / detection ≥0.80).
- **Expected output**: per candidate `tailmass_post, q05_post, q05_control, s2_pass, s2_deferred`.

### Step 6 — Valid-candidate decision, freeze & hash-pin (the binding EXP-084 artifact)

- **Method**: `valid = g018a_pass ∧ s1_pass ∧ (s2_pass ∨ s2_deferred-with-disclosure)`. Record, for every
  failing candidate, the **first failing leg** (`g018a` / `s1` / `s2`) for the attribution table. Assemble
  the surviving `{candidate × stratum}` set, canonicalize (sorted, explicit fields), and **sha256-hash-pin**
  it together with the **pre-declared Holm rule**: *Holm–Bonferroni at one-sided α=0.05 across the full
  frozen `{valid-candidate × stratum}` grid*, to be applied at EXP-084 on the WF verdict p-values. Emit
  `valid_candidate_set.json` (set + Holm rule + sha256 + upstream fingerprints).
- **Why**: the freeze-before-TEST + hash-pin is the D4.1 legitimacy condition; making it EXP-083's output
  artifact (with zero TEST contact) is a stricter, auditable inter-experiment hand-off.
- **Assumptions**: none statistical; this is bookkeeping discipline.
- **Expected output**: `valid_candidate_set.json` (hash-pinned), per-`{candidate × stratum}` `valid` +
  `fail_leg`.

### Step 7 — `ASS` discovery disclosure (non-binding)

- **Method**: carry the EXP-081 `ASS` per-cell expectancy/median/tail + shape flag forward as disclosure
  columns; optionally re-run `xen.ass` on the **post-exit** candidate distributions for the disclosure
  overlay. **No screen decision reads `ASS`** (G-017). Confirm §D7 `[15,8000]` bracket (EXP-080: 192/192
  IN_BRACKET) and the §D6 guards are recorded as context.
- **Expected output**: `ass_exp/med/tail` disclosure columns; bracket/guard notes.

### Step 8 — Determinism replay

- **Method**: re-run the full screen a second time with the recorded seeds; assert byte-identical
  `screen_results.parquet` and identical `valid_candidate_set.json` sha256.
- **Expected output**: determinism fingerprint in `run_metadata.json` (`determinism_ok: true`).

---

## Visualisations

1. **Survivor map** — `{candidate (rows) × substrate×domain (cols)}` heatmap coloured by outcome
   (`valid` / `fail@g018a` / `fail@s1` / `fail@s2` / `s2_deferred`). Answers: *does anything survive, and
   where do candidates die?*
2. **S1 decomposition scatter** — `X_fav` vs `X_tail` by substrate, with the matched-random `m_cell`
   threshold line. Answers: *is surviving edge favourable-attributable or pure tail-truncation?*
3. **S2 shape plane** — post-exit `tailmass` vs relative-`q05` (`q05_post − q05_control`) per candidate,
   with the frozen `τ_tail`/`δ` thresholds and the `n<120` deferred cells marked. Answers: *does the exit
   leave a catastrophe residual (the trap)?*
4. **Gross edge vs matched-random** — gross expectancy & median (CI_low whiskers, tail-flag marker) vs the
   matched-random control, by candidate × domain. Answers: *which candidates even clear the cheap screen?*
5. **`ASS` discovery overlay** — `ASS` expectancy/median/tail per cell (disclosure), shaded by S2 status.
   Answers: *where does `ASS` agree/disagree with the binding S2 — and where is it blind?*

All five are rendered from the single screening pass's bounded outputs (no re-simulation for plotting).

## Interpretation Guide (pre-registered, before results exist)

- **`SCREEN_DELIVERED` + non-empty valid set**: ≥1 `{candidate × stratum}` clears G-018a ∧ S1 ∧ S2 (or S2
  deferred). The frozen valid set is the EXP-084 hand-off. *This is TRAIN-only eligibility, not an edge
  claim* — interpret which candidate families and substrates survive and whether survival is broad
  (many strata) or narrow (few, possibly low-n). Recommend EXP-084 only if the operator ratifies the read.
- **`ALL_CANDIDATES_FAIL`**: 0 survivors. Read the `fail_leg` attribution: if most die at **S2**, the
  EXP-082 trap is confirmed binding (the exit cannot cut the continuous catastrophe tail without removing
  the median edge) — the family's central hypothesis is refuted on TRAIN, 0 reads spent, route to G-018
  closure. If most die at **S1**, the edge was pure tail-truncation/capture-bound. If at **G-018a**, no
  gross edge over matched-random at all (the EXP-081 "capture availability ≈ random" finding carried into
  realized exits).
- **Derived vs benchmark**: if benchmarks survive where the derived exits do not (or vice-versa),
  interpret per-stratum and disclose — the family thesis is specifically whether *data-derived* beats
  *conventional*; do not pool across substrates to manufacture breadth (LESSON-001).
- **Inconclusive at cell level**: `s2_deferred` (n<120) or `UNDERPOWERED_DISCLOSED` (n<30, none expected)
  cells carry forward flagged; they are neither survivors-by-default nor failures.
- **HALT (not a result)**: any determinism break, hash mismatch, harami-identity failure, TEST/holdout
  touch, or constant drift → route to a fix.

## Implementation Safety & Performance Constraints (for `experiment-developer`)

- **Holdout / TEST discipline**: read **only** `[0, train_cutoff)` of the analysis set; never slice the
  next-21% analysis-TEST stratum or the final-30% holdout; assert `test_stratum_touched == false` and
  `holdout_untouched == true` in metadata. No WF folds, no referee suite here.
- **Temporal ordering**: sort by `CloseTime`; align everything by `entry_epoch`/timestamp, never bar index;
  first-touch scans read only entry+1…cap (causal). P15 fill tie-break frozen and identical across
  candidates.
- **Denominators / zero-baseline**: the per-cell event set is **identical across all candidates** (EXP-042
  guard — assert it); `n_usable` gates candidate formation (≥30), never divides; `tailmass` is a fraction
  over `n_usable` (explicit, never `0/0`); matched-control excess and `SIZE-VOLADJ` are **differences** on
  paired events (no ratio-vs-zero). Finite handling explicit; no silent NaN.
- **Bounded iteration / progress**: `tqdm` over the (46 cells × 4 substrates × candidate-grid) outer loop;
  `N_BOOT=10_000` fixed; lazy Polars scan + column projection + first-70% slice before any heavy work;
  return bounded plot inputs from the analysis pass (no reloads/re-simulation for plotting).
- **Vectorization discipline**: the per-event first-touch resolution is genuinely sequential per event —
  keep it explicit/bounded (reuse the audited `lifetime_path_geometry`-style causal loop or the
  `capture_barriers.resolve_first_touch` kernel); only vectorize the bootstrap (block index gather), which
  is causally equivalent.
- **Reuse first**: import the pinned `xen.capgeo_exits.derive_barriers` unchanged (assert sha256); reuse
  `xen.capgeo_substrates`, `xen.capgeo_geometry`, `xen.capture_barriers`, `xen.favourable_targets`,
  `xen.adverse_targets`, `xen.position_exits`, `xen.exit_rules`, `xen.third_barrier`, `xen.ass`. New code
  ≤ 2 modules (a screen/separability harness; a benchmark-exit definition module only if existing kernels
  cannot be composed). No edits to any frozen generator/detector/geometry/substrate/derivation module.
- **Determinism**: all seeds fixed/recorded (substrate-random seed, bootstrap seeds derived deterministically
  per cell, e.g. `referee_calibration.seed_for(...)`); second pass byte-identical.

## Complexity Check

- **Statistical-method families: 4 / 4** — (1) moving-block bootstrap mean/median CI (G-018a); (2) paired
  matched-random contrast CI; (3) S1 additive decomposition + `m_cell`-calibrated `X_fav` edge-call;
  (4) S2 tailmass/relative-q05 shape legs. (All reuse existing kernels; no new test *type*.)
- **Visualisations: 5 / 5**.
- **New modules: ≤ 2 / 2**.

Within budget. Endpoint gross/TRAIN-only/real-price; per-stratum default; 0 counted TEST reads.
