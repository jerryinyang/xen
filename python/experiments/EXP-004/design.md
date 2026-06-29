# EXP-004 — E4 Robustness Pass (referee renew, D-referee)

**Branch:** `main`. **Checkpoint:** Phase-001 §E4 (ladder:137; binding D0:101-106; DET-dominance
:104-106; success O1:78-80). **Consumes:** E3a (EXP-003, A1) — the as-built `gate_stack_adaptive`
(studentized∧bps sub-pop L5, L1 rigid) + its 3-arm DET harness + the E2 substrate. **Purpose:**
due-diligence that **licenses the E5 freeze** — don't freeze the adaptive gate on untested knobs
(checkpoint:38, E3a report follow-up #2, A1.2 deferred residual skew-FPR, A1.5 §"STUDENTIZED FLOOR
TOO STRICT"). **Classification:** **analysis-only** (synthetic substrates + frozen primitives + the
E3a adaptive legs; no price→signal). **Reads/slots:** 0 TEST reads, 0 candidate slots; global
holdout sealed. **Does NOT** freeze the gate (E5), adjudicate CF-MR-002, touch L1, alter
`referee_calibration.py`/`referee_adaptive.py`, or change any frozen constant.

## Question (one, falsifiable)

**Is E3a's per-stratum DET-dominance verdict (32/32 DET_DOMINANT, STATE ΔMDE>0, dogfood FPR 0/32 ≤
frozen) ROBUST — does it survive perturbation of the gate's one free knob `q*∈{0.6,0.7,0.8}` (with
`Q_STUD_MIN=Φ⁻¹(q*)` co-moving, candidate-blind), of the bootstrap count + master seed, and of a
skew-stressed null (the A1.2 residual skew-FPR) — such that the freeze is licensed at the as-built
`q*=0.75`; OR does some perturbation flip a stratum (lose STATE recovery, break dogfood-FPR control,
or survive future-destroy), bounding the safe operating range?** Binding endpoint is **per stratum**
(L-03). A **robustness characterisation**, not a candidate screen and not a re-tune.

## What E4 perturbs (and what it must NOT)

| Probe | Knob | Sweep | Rationale | Tripwire it stresses |
|---|---|---|---|---|
| **R1 q*-sensitivity** | `SUBPOP_QUANTILE` + coupled `Q_STUD_MIN=Φ⁻¹(q*)` | `{0.6, 0.7, 0.8}` (+ `0.75` = E3a baseline, regression anchor) | the only adaptive free knob; checkpoint "threshold-perturbation Δverdicts" | dogfood-FPR control + STATE recovery at each q* |
| **R2 bootstrap/seed-stability** | `N_BOOTSTRAP`, master seed offset | `N_BOOTSTRAP∈{500, 1000}`; seed-offset `{0, +100000}` | ΔMDE / FPR must not be a small-resample / single-seed artifact (E3a §inconclusive; L-06 CI-width-vs-n) | verdict-boundary stability |
| **R3 residual skew-FPR** | null shape | add a **right-skewed/fat-tailed** null family | A1.2 left this for E4: skewed returns may push `stud_q` above `Q_STUD_MIN≈0.674` and inflate FPR via the studentized path | dogfood-FPR control on a skew-stressed null |

**Frozen / NOT perturbed (binding):** `materiality_bps` (frozen economic floor — perturbing it
breaks frozen discipline + candidate-blindness); L1+coverage (rigid, untouched); the cost map (E0,
frozen); `ALPHA`, `POWER_TARGET`. `Q_STUD_MIN` is **never** swept independently — it is **always**
re-derived as `Φ⁻¹(q*)` at each R1 point, so candidate-blindness (Q5) holds at every sweep value
(zero free knobs added; `Q_STUD_MIN` tracks `q*` by the same principle as A1.2). This is a sweep of
*pre-registered* knobs to map the verdict surface, **not** a search for a better operating point.

## Disclosures (ride along, no new tests — checkpoint:137)

- **D-CIwidth — per-instrument 4h CI-width audit.** 4h has the fewest episodes (highest-cost
  strata); report the sub-pop bootstrap CI half-width per 4h instrument and confirm it shrinks with
  episode count (L-06: CI width ↓ with effective_n). A degenerate (near-zero-episode) 4h cell that
  only ABSTAINs is disclosed, not a failure.
- **D-regime — recent-regime disclosure.** Re-run the baseline arm on the **most-recent third** of
  the first-70% analysis slice (still holdout-sealed) and report whether DET-dominance persists —
  guards against the 32/32 being an early-regime artifact. Disclosure-only; **not** a goalpost.

## Data views / substrate (reuse E2/E3a exactly)

16 inst × {1h,4h} (DE30 absent) = 32 strata; open-to-open `≤t-1` (E0); first-70% slice + domain
fence; holdout sealed. Shapes DENSE/TAIL/SPARSE/STATE (matched-magnitude). Null families: block-
permute returns; reblock-random positions; causally-lagged dogfood (Donchian-20 + MA 20/50) — **plus
R3's skew-stressed null**. All identical seeds/split/bootstrap machinery as E3a; only the swept
knobs change.

## Method — swept 3-arm DET, reusing the E3a harness

Reuse the EXP-003 runner (`frozen` / `frozen_amortized` / `adaptive` arms; `mde_of`, `dogfood_fpr`,
`no_plant_passrate`, `future_destroyed_passrate`, `classify_stratum`) **unchanged in logic**; wrap it
in an E4 sweep driver that, per sweep point, sets `(q*, Q_STUD_MIN=Φ⁻¹(q*), N_BOOTSTRAP, seed_off)`
coherently and re-runs all 32 strata. Knob injection must be **causally-equivalent and
deterministic** (thread `q`/`q_stud_min`/`n_bootstrap`/`seed_off` as explicit params, or set the
module constants per run then restore) — never read from outcomes/state-mask.

**Endpoints per (stratum, sweep-point):** verdict ∈ {DET_DOMINANT, NOT_IMPROVED, FPR_BROKEN}; STATE
ΔMDE = `MDE_frozen − MDE_adaptive`; adaptive dogfood-FPR (Wilson, A1.3 noise-tolerant rule); R3
skew-null adaptive FPR. **Binding per stratum (L-03):** the verdict and its stability across the
sweep; pooled counts disclosure-only.

**Stat work (within comparative budget):**
1. q*-sweep verdict/ΔMDE/FPR surface — 32 strata × {0.6,0.7,0.75,0.8}.
2. bootstrap/seed-stability — verdict + STATE ΔMDE deltas across the 2×2 (N_BOOTSTRAP × seed-off) at
   q*=0.75; Wilson-resolved verdict throughout.
3. R3 skew-FPR — adaptive dogfood-FPR on the skew-stressed null per stratum (Wilson).

## Regression anchor (binding correctness gate)

At `(q*=0.75, N_BOOTSTRAP=500, seed_off=0)` the swept harness **must reproduce EXP-003 (A1)
bit-for-bit**: 32/32 DET_DOMINANT, STATE ΔMDE median 7.5 (range 4.0–23.5), adaptive dogfood FPR
0/32, future-destroy `fd_max=0.000`. A mismatch ⇒ the sweep wiring is wrong ⇒ **fix + rerun before
any sweep is interpreted** (the sweep is meaningless if the baseline point is not reproduced).

## Leak tripwire(s) — retained from E3a, applied at every sweep point

1. **Future-destroy collapse (critical, the studentized path):** plant STATE edge, block-permute
   returns, re-run adaptive — detection (incl. via the studentized sub-pop quantile) **must collapse
   to FPR at every `q*`**. A surviving future-destroyed pass at *any* sweep point = noise-mining via
   the quantile → **REJECT-class** (the knob value is unsafe; if it survives at baseline, E3a's
   freeze candidate is itself compromised).
2. **No-plant guard:** no drift ⇒ adaptive PASS rate ≈ FPR on every shape, every sweep point.
3. **Dogfood-FPR control (binding, A1.3 Wilson-resolved):** adaptive dogfood-FPR not Wilson-resolved
   above frozen — at every `q*`, every (N_BOOTSTRAP, seed), and on the R3 skew-null.

## Predeclared interpretation criteria

- **FREEZE LICENSED (success):** no stratum flips — DET-dominance holds (no DET_DOMINANT→NOT_IMPROVED
  or →FPR_BROKEN) across **all** R1 q*, the R2 bootstrap/seed grid, **and** the R3 skew-null
  (adaptive FPR not Wilson-resolved above control); STATE ΔMDE stays >0 (magnitude may move with q*);
  future-destroy collapses everywhere. → licenses E5 freeze **at q*=0.75** with the verified safe
  operating range recorded.
- **KNOB-SENSITIVE / RANGE-BOUNDED (partial, still licenses freeze at baseline):** baseline q*=0.75
  holds, but a sweep extreme degrades — e.g. q*=0.8 suppresses STATE recovery (ΔMDE→0) on *k* strata
  (studentized floor too strict, A1.5), or q*=0.6 widens FPR toward control on *m* strata. → record
  the **safe q* range**; E5 freezes at the validated 0.75 with the sensitivity documented. **Not**
  freeze-blocking unless baseline itself fails.
- **SKEW-FPR MATERIAL (predeclared partial, A1.2):** if the R3 skew-null lifts adaptive dogfood-FPR
  **Wilson-resolved above control** on ≥ a stated fraction of strata via the studentized path → the
  residual skew-FPR is real; the recorded remedy is a **conservative `Q_STUD_MIN` bump deferred to
  E5** (a principled, candidate-blind inflation), **NOT applied in E4** (applying it here would be
  tuning on the test — A1.2). Recorded honestly as a freeze precondition.
- **FREEZE NOT LICENSED (failure):** baseline q*=0.75 fails the regression anchor (harness bug →
  fix+rerun), OR a future-destroyed edge survives at any sweep point (REJECT-class leak), OR baseline
  dogfood-FPR Wilson-resolved above frozen.
- **Inconclusive:** bootstrap/seed noise swamps the verdict boundary even at N_BOOTSTRAP=1000 →
  report the bound + raise resamples; do not over-claim stability.

**Shape-aware read:** report STATE ΔMDE as a function of q* (expect monotone-ish: higher q* → stricter
upper-quartile → less recovery on thinly-diluted edges); DENSE/TAIL should stay ~flat across the
sweep (the sub-pop knob targets dilution, not location).

## Complexity budget (comparative)

- **New code modules: 0–1** — an E4 **sweep driver** in `code/` that imports and re-runs the EXP-003
  harness with injected `(q*, Q_STUD_MIN, N_BOOTSTRAP, seed_off)` + the R3 skew-null generator. No
  change to `referee_adaptive.py` / `referee_calibration.py` logic (knob injection only). Reuses
  `wilson_interval`, `permuted_returns`, the substrate, the arm functions.
- **Stat tests: 3** (R1 q*-surface, R2 bootstrap/seed-stability, R3 skew-FPR). Within comparative
  (2–4).
- **Visualisations: 3** — (1) **q*-sweep verdict surface** (32 strata × q*; cell = verdict, annotate
  STATE ΔMDE); (2) **bootstrap/seed stability** (STATE ΔMDE + verdict deltas across the 2×2 at
  q*=0.75); (3) **skew-FPR** (adaptive dogfood-FPR on baseline vs skew-null per stratum, Wilson bars,
  control line). D-CIwidth + D-regime are **table disclosures** (no extra plot). Within comparative
  (3–5).
- **One falsifiable question** (freeze licensed: yes / range-bounded / no). Fits one rung.

## Metric denominators / zero-baseline

MDE in bps on `EDGE_GRID_BPS` (UNPOWERED=inf, reported never failed); FPR Wilson-bounded over stated
draws; sub-pop denominator = episodes (per-episode net-mean). STATE ΔMDE NaN where either arm
UNPOWERED. No-plant / `e=0` = the null guard. No percentage-of-zero metrics. R3 skew-null FPR
denominator = its own draw count.

## Implementation safety constraints (developer)

- **Knob injection is candidate-blind + coherent:** at every R1 point `Q_STUD_MIN := Φ⁻¹(q*)`
  re-derived from the swept `q*` (never an independent value); `materiality_bps` stays the **frozen**
  map; no knob reads outcomes / FPR / state-mask. Thread params explicitly or set-and-restore module
  constants deterministically — bit-identical to E3a at the (0.75, 500, 0) anchor.
- `referee_calibration.py` **byte-frozen**; `referee_adaptive.py` logic **unchanged** (E4 only
  injects pre-registered constants — it does not edit the gate). L1+coverage identical to frozen.
- **R3 skew-null** is a *null* (no planted edge): generate right-skewed / fat-tailed returns with a
  fixed seed (e.g. exponential-tail or sign-asymmetric scaling of block-permuted real returns) —
  document the generator; it must be a genuine no-edge null (verify: frozen + frozen_amortized arms
  also ≈0 on it, else the "null" carries structure). Skew is a *stress on the null shape*, not a
  plant.
- Open-to-open `≤t-1`; first-70% + domain fence; never the final 30%; `CloseTime` ordering. `tqdm` on
  the (sweep-point × stratum) loop; ProcessPool seed-deterministic (strata independent). Bound
  `N_PLANT=20`, `N_NULL=80`, `N_BOOTSTRAP∈{500,1000}` as predeclared.
- Deterministic seeds reused from E3a per draw; the only seed change is the explicit R2 `seed_off`.
- The adaptive gate is **NOT frozen here** (E5 freezes); E4 maps its robustness surface.

This experiment maps the robustness surface of the E3a adaptive gate over its pre-registered knobs to
license (or range-bound) the E5 freeze. It does not freeze the gate, adjudicate any candidate, retune
any constant, touch L1, or touch the global holdout.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-29)

Checked against `references/governance-constraints.md` + binding D0 (:101-106) + the checkpoint E4
ladder (:137):
- **Single falsifiable question** — freeze licensed (yes / range-bounded / no) via robustness of the
  E3a 32/32 verdict over pre-registered knobs. One rung. ✓
- **Gate-threshold calibration (scrutinized)** — `q*` sweep `{0.6,0.7,0.8}` is exactly the
  pre-registered sensitivity band governance asks for; `Q_STUD_MIN=Φ⁻¹(q*)` is **re-derived at every
  point** (never an independent knob → candidate-blindness Q5 holds at each sweep value, zero free
  knobs added); `materiality_bps` stays the **frozen** map (not perturbed). No magic constant. ✓
- **No tuning on test** — the skew-FPR remedy (a conservative `Q_STUD_MIN` bump) is **deferred to E5
  and NOT applied in E4** (A1.2 discipline); E4 only *measures* residual skew-FPR. ✓
- **Regression anchor** — `(q*=0.75, N_BOOTSTRAP=500, seed_off=0)` must reproduce EXP-003 (A1)
  bit-for-bit before any sweep is interpreted; a mismatch is a fix+rerun harness bug, not a result. ✓
- **Per-stratum binding** (L-03); pooled disclosure-only; STATE ΔMDE shape-aware read across `q*`. ✓
- **Leak tripwires** retained and applied at **every sweep point** — future-destroy collapse on the
  studentized path (REJECT-class if it survives at any `q*`), no-plant guard, A1.3 Wilson-resolved
  dogfood-FPR control (incl. on the R3 skew-null). ✓
- **R3 skew-null well-formed** — predeclared as a genuine *no-edge* null (verified: frozen +
  frozen_amortized arms also ≈0 on it, else it carries structure — guards the L-08 "structured null"
  trap); skew is a stress on the null *shape*, not a plant. ✓
- **Classification** analysis-only; `referee_calibration.py` byte-frozen; `referee_adaptive.py` logic
  unchanged (E4 injects pre-registered constants only, does not edit the gate); holdout sealed; 0
  reads / 0 slots; not tuned on CF-MR-002 (absent). ✓
- **Budget** — 0–1 new module (sweep driver reusing the EXP-003 harness + R3 skew generator); 3 tests
  (R1/R2/R3); 3 plots; D-CIwidth + D-regime are table disclosures. Within comparative. ✓

**Info (non-blocking):**
1. The sweep multiplies compute (4 `q*` × 32 strata × 3 arms + the R2 2×2 grid + R3). The E3a
   early-stop + ProcessPool keep it bounded; acceptable for analysis-only. Bound `N_*` as predeclared.
2. Knob injection should be deterministic + causally-equivalent (thread params or set-and-restore
   module constants) — the bit-identical anchor at (0.75, 500, 0) is the proof it is wired correctly.

No REVISE issues. Proceed to Stage 2 (build the E4 sweep driver in `code/`, reusing the EXP-003
3-arm harness with injected `(q*, Q_STUD_MIN=Φ⁻¹(q*), N_BOOTSTRAP, seed_off)` + the R3 skew-null).
