# Phase 017 — CF-CAPGEO-001 Qualifier & Protocol Validation

**Status:** **CLOSED at G-017 (2026-06-21) — `DISCOVERY_ONLY`.** Slate EXP-076/077/078 complete; the
`ASS_VALIDATED` conjunction failed on EXP-078's two binding legs → `ASS` non-binding (discovery use
only), frozen referee suite stays the binding gate for Phase 018; no `PROTOCOL_DEFECT`. See
[`G-017-gate-review.md`](G-017-gate-review.md) and [`retrospective.md`](retrospective.md).
*(Design-phase history below, for the record.)* G0 PASS (2026-06-20): D0 predeclarations ratified and
frozen (`D0-predeclarations.md`; bite-check GREEN); slate proceeded EXP-076 (G-017a cheap screen) →
EXP-077 → EXP-078.
**Date:** 2026-06-20 (design).
**Family:** `CF-CAPGEO-001` (REGISTERED, SCREENING-GATED — `candidate-families/cf-capgeo-001.md`).
**Opened by:** operator selection of the next candidate family (2026-06-20), per the two-family
retrospective §6.1 ("select the next family for its exit/capture geometry") and the consolidated
draft `.ignore/dump/re.md`.
**Discipline (binding throughout Phase 017):** synthetic substrates + **current**-data dogfood
(TRAIN-only) only; **0 candidate slots, 0 counted TEST reads, holdout never touched**; all
return/expectancy metrics on **real prices**; deterministic (fixed seeds); no parameter tuned
against any TEST or holdout data.

---

## 1. Why Phase 017 exists (validate the yardstick before the signal)

CF-CAPGEO-001 introduces two new *instruments of judgement* at once:

- the **`ASS`** qualifier (adaptive-bandwidth KDE + empirical-Bayes shrinkage + bootstrap CI, scored
  on **expectancy + median + tail diagnostic**, with a `P(return>X)` extension), and
- the **`WF-EXPANDING`** expanding-window walk-forward evaluation protocol.

The single deepest lesson of the two closed families (retrospective §4.2) is that **expectancy is a
smoothed mean, and the raw mean is fragile to exactly the bimodal/tail structure that killed both
families.** A qualifier that scores on a smoothed mean therefore cannot be trusted to *adjudicate*
until it is shown to (a) recover known expectancy/median/tail on controlled substrates, (b) control
error under the protocol that will carry it, and (c) actually see tail/bimodal shape — the EXP-074
gap where the anti-p-hacking guard was structurally blind to tail-shape effects (§2.3, §5.4).

The programme already paid this tax once and it paid off: ~5 phases (001–003b) hardened the referee
suite before any real signal was measured, and every later verdict rode that calibrated, dogfood-
tested gate (§2.7). Phase 017 is the CF-CAPGEO-001 analogue. **Validate-first** is the operator's
ratified posture (2026-06-20).

This phase changes no verdict about any market signal. It decides only whether `ASS` is **binding-
eligible** in Phase 018 or **discovery-only**.

## 2. The two instruments under validation

### 2.1 `ASS` — Expectancy-Robust Qualifier

Component spec: `docs/signal-registry/components/global-techniques.md`; source `.ignore/dump/ass.md`.
Pipeline: per signal type → kNN-bandwidth adaptive KDE → empirical-Bayes shrinkage toward the pooled
KDE (`weight = n/(n+k)`, `k` = median sample size by default, the one tunable knob) → bootstrap CI.
**Scoring posture (binding deviation from the raw draft):** report **expectancy + median + tail
diagnostic** — never expectancy alone. `P(return>X)` for X ∈ {0, breakeven, 1R, 2R} as a separate,
non-collapsed output with its own reliability check.

### 2.2 `WF-EXPANDING` — expanding-window walk-forward

Component spec as above; source `.ignore/dump/wf-model.md`. Primary protocol is the expanding window
(`Train A → Test_A`; `Train A + Test_A + Train B → Test_B`; …), rolling 1y/2y/3y windows disclosed.
**The binding governance question Phase 017 must answer:** how does per-fold reading reconcile with
the TEST-read ledger's **2-lifetime-counted-reads-per-stratum** cap? The counted-read accounting is
predeclared and validated here, before any Phase 018 TEST contact. The final-30% holdout is never a
fold.

## 3. The single question

> Are `ASS` and `WF-EXPANDING` trustworthy enough to **bind** a CF-CAPGEO-001 verdict — i.e., does
> `ASS` recover known expectancy/median/tail to calibrated tolerance across unimodal/skewed/bimodal/
> sparse synthetic types; control FPR and deliver finite MDE and reliable `P(return>X)` under
> `WF-EXPANDING`; and discriminate bimodal from unimodal shape — or must it be demoted to
> discovery-only with the frozen referee suite remaining the binding gate?

## 4. Binding inheritances (carried from the retrospective)

1. **Expectancy + median + tail, never one alone** (§4.2). The qualifier is validated on all three.
2. **Calibrated / data-derived thresholds, not magic numbers** (§5.3). Every tolerance/threshold in
   Phase 017 is fixed by a **fixture/bite check** on synthetic data (measure whether the threshold
   actually discriminates) before it is ratified, or is a pre-registered sensitivity band shown to be
   routing-invariant.
3. **A guard must fit the shape of the observation** (§2.3/§5.4). The shape-discrimination read
   (EXP-078) is the predeclared escape hatch built *before* the guard fires.
4. **Per-stratum / per-type adjudication; pooled is a disclosure** (§2.5).
5. **Determinism** (§2.8): fixed seeds; a second full pass is byte-identical.
6. **Real-price discipline:** all returns/expectancy on real prices; no HA/Renko brick prices.
7. **Holdout sealed; 0 counted TEST reads.** Synthetic + current first-70% TRAIN only.

## 5. Experiment slate

EXP-IDs pre-assigned (next free ID = EXP-076; EXP-072/073 never opened, conditional in Phase 016).

### EXP-076 — `ASS` synthetic-substrate recovery (`ASS/VAL-001`)

**Question:** On synthetic return populations with **known** expectancy, median, and shape
(unimodal, left/right-skewed, bimodal, and sparse/uneven sample sizes), does `ASS` recover each
estimand within a fixture-calibrated tolerance? Does shrinkage pull sparse types toward the pooled
prior and leave data-rich types essentially unmoved (monotone in `n`)?
**Artifacts:** `python/experiments/EXP-076/`; synthetic only; 0 slots; 0 TEST reads.
**Pass criteria (D0):** recovery bias within the fixture-calibrated tolerance band on every synthetic
type for expectancy and median; shrinkage weight monotone in `n`; bootstrap CI coverage at nominal
on the synthetic ground truth. Cheap **G-017a** screen — must pass before EXP-077 dogfood.

### EXP-077 — Dogfood + calibration under `WF-EXPANDING` (`ASS/VAL-002`)

**Question:** On known-null synthetic populations evaluated **under the expanding-window walk-forward
protocol**, is `ASS`'s FPR ≤ 0.05 per type, is per-domain MDE finite, and is `P(return>X)` reliable
(predicted vs realized within tolerance on held-out folds)? Does the predeclared per-fold counted-read
accounting honor the 2-read stratum cap? A current-data **TRAIN-only** dogfood confirms the pipeline
runs end-to-end on real bars without touching any TEST stratum or the holdout.
**Artifacts:** `python/experiments/EXP-077/`; synthetic + current first-70% TRAIN dogfood; 0 slots;
0 counted TEST reads.
**Pass criteria (D0):** FPR ≤ 0.05 on every synthetic null type; finite MDE per domain; reliability
within the predeclared band; counted-read accounting demonstrably cap-honoring; determinism.

### EXP-078 — Shape discrimination + `k`-sensitivity (`ASS/VAL-003`)

**Question:** Does the tail/bimodality diagnostic flag bimodal vs unimodal populations at a
fixture-calibrated effect-size threshold (closing the EXP-074 tail-shape-blind-guard gap)? How
sensitive is `ASS` to its one tunable knob `k` (default = median sample size) across a pre-registered
grid?
**Artifacts:** `python/experiments/EXP-078/`; synthetic only; 0 slots; 0 TEST reads.
**Pass criteria (D0):** the diagnostic separates bimodal from unimodal at the calibrated threshold
with controlled false-flag rate on unimodal nulls; routing invariant across the pre-registered `k`
band (or the `k`-dependence is disclosed and bounded).

## 6. D0 decisions required before G0

Ratify in `D0-predeclarations.md` before any result-producing code:

- **D1 — Synthetic data-generating processes** (frozen): the unimodal/skewed/bimodal/sparse families,
  their ground-truth expectancy/median/shape, and seeds.
- **D2 — Fixture/bite-calibrated tolerances** (§5.3): recovery tolerance bands, FPR target (0.05),
  MDE finiteness definition, reliability band, shape-discrimination effect-size threshold — each set
  by a fixture/bite check, not hand-set.
- **D3 — `ASS` configuration:** kNN bandwidth, shrinkage `k` default (= median sample size) and the
  EXP-078 `k`-grid, bootstrap draws/seed, `P(return>X)` thresholds.
- **D4 — `WF-EXPANDING` parameters:** initial train span, step, minimum fold size, rolling-window
  comparison set (1y/2y/3y), and the **per-fold counted-read accounting rule** (what counts as a
  stratum-specific counted read vs an in-protocol disclosure; how the 2-read cap is honored on the
  future 5-year strata; holdout never a fold).
- **D5 — G-017 mechanical verdict rule** (§7): the exact conjunction for `ASS_VALIDATED` vs
  `DISCOVERY_ONLY`.
- **D6 — Determinism & real-price discipline:** fixed seeds, byte-identical second pass; all returns
  on real prices.

## 7. G-017 gate outcome criteria

G-017 is adjudicated after EXP-076/077/078.

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| **`ASS_VALIDATED`** | EXP-076 recovery within tolerance (all types) ∧ EXP-077 FPR≤0.05 + finite MDE + reliable `P(return>X)` under `WF-EXPANDING` + cap-honoring accounting ∧ EXP-078 shape diagnostic discriminates + bounded `k`-sensitivity. | `ASS` is **binding-eligible** for CF-CAPGEO-001; Phase 018 may use it as the binding qualifier (alongside the frozen suite as benchmark). Phase 018 opens once INFR-003 also completes. |
| **`DISCOVERY_ONLY`** | Any of recovery / calibration / shape fails or is power-limited, but no fundamental defect. | `ASS` is demoted to **non-binding discovery use**; the **frozen referee suite remains the binding gate** in Phase 018. Findings recorded; the qualifier may be re-validated under a future scope. |
| **`PROTOCOL_DEFECT`** | `WF-EXPANDING` counted-read accounting cannot honor the 2-read cap, or determinism fails. | Fix the protocol/accounting and re-run the affected read before any Phase 018 TEST design. |

### 7.1 Sample-size bracket re-confirmation (closing the synthetic↔real loop)

Phase 017 is validated against **known synthetic ground truth** (the only place truth exists — real
bars have no known expectancy), so it does **not** consume the 5-year data. The one real-data
dependency is *which sparsity regime* `ASS` will actually face: the realized per-cell event counts on
the 5-year data (especially 4h) are unknown until INFR-003 lands. Phase 017 handles this by
**bracketing** — the D1 `SP` family spans `n ∈ {15 … 8000}` to straddle any realized count — rather
than guessing one value.

To make the loop explicit and on the record:

- **`ASS_VALIDATED` carries a bracket condition.** The G-017 verdict is valid for realized per-cell
  `n` **inside** the validated synthetic span `[15, 8000]`.
- **Bracket re-confirmation at the Phase 018 D0 (cheap, no 017 re-run):** once INFR-003 produces the
  real cell-size distribution, confirm every (substrate × instrument × domain) cell's event count
  falls inside `[15, 8000]` (and that the dependence-aware moving-block FPR — already dogfooded on
  current data — still holds on a 5-year null slice). If all cells are inside the bracket, G-017
  stands as-is.
- **Escape hatch:** any cell whose realized `n` falls **outside** the bracket (e.g. a very sparse 4h
  cell `< 15`, or an unexpectedly rich cell `> 8000`) is either excluded from binding `ASS`
  adjudication with disclosure, or triggers a **scoped EXP-079 addendum** that extends the synthetic
  span to cover it — not a full 017 re-run.

This keeps 017 synthetic-led and parallel to INFR-003 while guaranteeing the validated regime
actually covers the data 018 will use.

## 8. Guardrails (carried)

- 0 candidate slots, 0 counted TEST reads; holdout never loaded (synthetic + current first-70% TRAIN
  only).
- Every threshold/tolerance fixture/bite-calibrated or a disclosed routing-invariant band — no
  magic-number gate constants.
- Determinism: fixed seeds; second full pass byte-identical.
- Real-price returns only; no HA/Renko brick-price returns.
- No tuning against any TEST or holdout data; `k` and all `ASS` parameters frozen at D0 (the EXP-078
  grid is a pre-registered sensitivity sweep, not a selection).
- Phase 018 (family screening) is **GATED** on G-017 PASS **and** INFR-003 completion; nothing in
  Phase 017 reads the family's market data beyond the TRAIN-only dogfood.
- **Per-stratum verdict representation (BINDING — see `LESSON-001-per-stratum-verdict.md`):** every
  experiment emits its binding verdict per stratum/cell/`n`; no single collapsed cross-cell PASS/FAIL
  is binding (collapsed flags must be captioned non-binding). Enforced at Stage-4/8 governance.
  Precedent: EXP-076 audit C1.

## 9. Immediate next steps

1. **Operator G0 ratification** — rule on D1–D6 (§6); freeze `D0-predeclarations.md`.
2. **Kick off INFR-003 in parallel** (5-year 1-minute collection + VAL + holdout re-seal) — the
   Phase 018 data precondition; tracked in the master index Infrastructure Tasks.
3. **Scope EXP-076** (Stage 1) after G0 PASS → EXP-077 (gated on EXP-076 G-017a) → EXP-078.
4. **G-017 adjudication** after the slate; route binding vs discovery-only.
5. **On G-017 PASS + INFR-003 complete:** open the **Phase 018** design (CF-CAPGEO-001 family
   screening) with its own D0/G0.

---

*Companion documents: family spec
[`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md);
components [`../../../signal-registry/components/global-techniques.md`](../../../signal-registry/components/global-techniques.md);
multiplicity registry Phase 017/018 batches
[`../../../signal-registry/multiplicity-registry.md`](../../../signal-registry/multiplicity-registry.md);
standing reference
[`../../reflections/2026-06-19-two-family-retrospective-reflections.md`](../../reflections/2026-06-19-two-family-retrospective-reflections.md);
family detail index [`../../families/cf-capgeo-001/INDEX.md`](../../families/cf-capgeo-001/INDEX.md).*
