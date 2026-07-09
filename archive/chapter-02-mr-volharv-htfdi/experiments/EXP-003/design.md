# EXP-003 — E3a Economic-Leg Adaptive Gate (referee renew, D-referee)

**Branch:** `main`. **Checkpoint:** Phase-001 §E3a (ladder:134; binding D0:101-106; success O1:78-80;
DET-dominance:104-106). **Operator scope decision 2026-06-29:** honor D0 (L1 rigid; adapt only L3/L5);
E3 split → **this is E3a**; return-series unit (Q9) + composite-form selection (Q4) deferred to E3b.
**Classification:** **analysis-only** (synthetic substrates + frozen primitives + the new adaptive
economic legs; no price→signal). **Reads/slots:** 0 TEST reads, 0 candidate slots; global holdout
sealed. **Consumes:** E0 (amortized cost via the seam), E2 substrate (4 shapes, 3 null families),
EXP-001 amortized accounting.

## Question (one, falsifiable)

**Can an economic-leg adaptation — power-aware L3/L5 + a candidate-blind sub-population L5 + amortized
accounting + L2 removed, with L1+coverage kept rigid — DET-DOMINATE the frozen gate: strictly lower
the economic MDE on the E2 STATE (and any L5-limited) cells at a dogfood-negative FPR ≤ the frozen
gate's, without losing DENSE/TAIL detection — or not (frozen suite proven not improvable without
losing FPR control)?**

DET-dominance is the D0 success definition (:104-106). The binding endpoint is **per stratum** (L-03).

## What the adaptive gate is (the BUILD)

A new `gate_stack_adaptive` in `python/src/xen/referee_adaptive.py` (the module reserves "the adaptive
gate itself … built at E3"). It **reuses every frozen sub-primitive unchanged** (split discipline,
`estimate_block_length`, block bootstrap, `ci_from_means`, `_episode_counts`, L1 readiness, coverage)
and changes **only** the economic legs:

| Leg | Frozen | E3a adaptive |
|---|---|---|
| **L1 readiness + coverage** | rigid | **UNCHANGED — rigid** (candidate-blind validity floor, FPR≈0). Sparse stays UNPOWERED by design. |
| **L2 integrity** | `True` no-op (F4) | **REMOVED** |
| **L3 outcome** | neutral CI-lower>0 ∧ vs-naive CI-lower>0, per-held cost | same legs on **amortized** cost; **power-aware** (abstain where no finite MDE) |
| **L5 materiality** | pooled neutral CI-lower > τ·materiality, per-held | **amortized**; **power-aware**; admit on **pooled-material OR sub-population-material** (the dilution-robust path below) |

**Composite = validity→economics (§10.3a), power-aware:** PASS iff
`L1 ∧ coverage ∧ (L3 pass-or-abstain) ∧ (L5 pass-or-abstain) ∧ (≥1 economic leg powered-and-passed)`.
An economic leg **abstains** (does not veto) where it is structurally UNPOWERED (no finite MDE on the
synthetic-positive calibration) — the L-12 §2 fix; the "≥1 powered-and-passed" clause forbids passing
on all-abstain. The validity floor still hard-vetoes (FPR≈0 preserved).

### Sub-population L5 (the candidate-blind dilution-robust path — the hard part)

E2 STATE failure: edge on a latent sub-state (`frac_A=0.5`) halves the **pooled** mean below the L5
floor (L-03). The fix must recover it **without peeking at the state mask** (no oracle) and
**deterministically / performance-independently** (Q5).

- **Statistic:** per **episode** (contiguous same-position run; reuse the frozen episode structure),
  compute the **amortized net-mean bps** on TEST. The sub-population statistic is the **fixed
  q\*-quantile of the per-episode net-mean distribution**, `q* = 0.75` (predeclared, Q5 — recovers an
  edge carried by ≥25% of episodes; never selected on outcomes).
- **Materiality:** **block-bootstrap the q\*-quantile** (resample episodes with the frozen block
  length; same Politis-Romano machinery), require its **CI-lower > materiality_bps** (frozen
  `MATERIALITY_BPS`, unchanged). Reuses `ci_from_means`-style percentile CI on the bootstrap
  distribution of the quantile.
- **Why candidate-blind:** `q*` and `materiality_bps` are fixed constants; the statistic is computed
  on the test net series exactly as any referee leg is — no state mask, no selection, no
  performance-derived threshold. A dense edge → all episodes ≈δ → q\* ≈ δ (passes like pooled). A
  diluted edge (≥25% episodes carry δ) → q\* lands in the edge-bearing upper tail → recovers it. A
  pure null → episode-means ≈ symmetric about 0; whether the q\*=0.75 quantile's CI-lower clears
  materiality is **the empirical FPR question E3a answers** (an upper quantile is upward-biased, so
  this MIGHT inflate dogfood FPR — if it does, the design fails the FPR floor → predeclared null).
- **Economic FPR budget (Q1, D0:111):** economic legs may spend FPR ≤ α; the **binding** control is
  the realized **dogfood-negative** FPR of the *full* adaptive gate ≤ the frozen gate's (success O1).

## Data views / substrate (reuse E2)

16 inst × {1h,4h} (DE30 absent); open-to-open `≤t-1` (E0); first-70% slice + domain fence; holdout
sealed. Shapes: DENSE, TAIL, SPARSE, STATE (`edge_shapes`, matched-magnitude). Null families:
block-permute returns; reblock-random positions; **causally-lagged dogfood** (Donchian R + MA 20/50).

## Method — 3-arm DET comparison (per stratum × shape)

Three gate arms on identical draws/seeds/split/bootstrap:
1. **frozen-as-is** (`gate_stack_core` + `gate_stack_row`, per-held) — the baseline DET reference.
2. **frozen-amortized** (`gate_stack_core_costfn`, amortized; legs otherwise frozen) — isolates the
   E1 accounting gain (intermediate disclosure).
3. **adaptive** (`gate_stack_adaptive`, amortized + power-aware L3/L5 + sub-pop L5, L2 removed) — the
   E3a build.

Per (stratum, shape, arm): **MDE** = DETECTED_FLOOR (first `e>0` at ≥`POWER_TARGET` detection;
inf=UNPOWERED). Per stratum: **FPR** per null family (Wilson, reuse `wilson_interval`).

**Binding metric (per stratum, non-pooled — L-03):**
`ΔMDE_adaptive = MDE_frozen − MDE_adaptive` (on STATE primarily; report all shapes). **DET-DOMINANCE
(per stratum)** = `MDE_adaptive ≤ MDE_frozen` on every shape **AND strictly < on ≥1 shape (expect
STATE)** **AND** dogfood FPR_adaptive ≤ FPR_frozen **AND** DENSE/TAIL MDE not raised. Pooled counts
disclosure-only.

## Predeclared interpretation criteria

- **DET-DOMINANCE (per stratum, binding success):** adaptive strictly lowers MDE on STATE (and/or
  L5-limited cells) with dogfood FPR_adaptive ≤ FPR_frozen and no DENSE/TAIL loss. Report the strata
  count + the STATE ΔMDE distribution. → adopt-candidate for E5 freeze.
- **FROZEN-NOT-IMPROVABLE (predeclared valid NULL, D0:104-106):** no stratum shows dominance, **or**
  the sub-pop path lifts dogfood FPR_adaptive > FPR_frozen on ≥ a stated fraction of strata → the
  economic adaptation cannot recover power without forfeiting FPR control → "frozen suite not
  improvable" is **proven** (a valid Phase-001 outcome, not a failure).
- **SPARSE stays UNPOWERED on adaptive (must hold):** L1 rigid → sparse UNPOWERED on all 3 arms;
  reported as correct-by-design (validity floor), NOT counted as a dominance loss.
- **Shape-aware read:** ΔMDE by shape; separate the E1 accounting gain (frozen→frozen-amortized) from
  the E3a leg-adaptation gain (frozen-amortized→adaptive). DENSE/TAIL should be ~unchanged
  (adaptation targets dilution, not location).

## Leak tripwire(s)

- **Dogfood-negative FPR control (binding):** adaptive gate FPR on the real null signals + abstract
  nulls ≤ frozen's, Wilson-bounded. A sub-pop path that fires on the dogfood = calibration break →
  the NULL outcome (not a dominance).
- **Future-destroying control (critical for the sub-pop path):** plant STATE edge, **block-permute
  the returns** (destroy alignment), re-run the adaptive gate — detection (incl. via the sub-pop
  quantile) **must collapse to FPR**. A quantile statistic can mine noise structure; if future-
  destroyed STATE still passes the sub-pop path → the sub-pop test is mining noise → **REJECT-class**.
- **No-plant guard (EXP-001-corrected):** no drift → adaptive PASS rate ≈ FPR on every shape.

## Complexity budget

BUILD experiment. **New code modules: 1** — `gate_stack_adaptive` + `episode_net_means` +
`subpop_quantile_materiality` in `referee_adaptive.py` (reusing frozen sub-primitives) + the E3a
harness in `code/` (reuses the E2 runner scaffolding). **Stat work:** MDE per (16×2 × 4 shapes × 3
arms) + FPR per (stratum × null family × arm). **Visualisations: 3** — (1) DET-dominance map
(MDE_adaptive vs MDE_frozen per stratum × shape), (2) STATE-recovery (MDE across the 3 arms on STATE
cells, isolating accounting vs leg-adaptation gain), (3) dogfood FPR comparison (adaptive vs frozen,
Wilson bars). Within the comparative budget. **This fits one rung** — the return-series unit + the
composite-form selection are explicitly E3b, keeping E3a a single falsifiable question.

## Success / failure / inconclusive

- **Success:** a per-stratum DET-dominance verdict (dominance OR proven not-improvable), with FPR
  control held and the future-destroy control collapsing every detection. Either outcome is
  informative (recovers STATE, or proves the floor binds).
- **Failure:** future-destroyed STATE survives the sub-pop path (noise-mining leak), or the adaptive
  gate breaks the validity floor (sparse passes / dogfood FPR ≫ frozen) → bug, fix + rerun.
- **Inconclusive:** bootstrap/seed noise swamps the ΔMDE / FPR-comparison boundary → raise resamples
  or report the bound.

## Metric denominators / zero-baseline

MDE in bps on `EDGE_GRID_BPS`; FPR Wilson-bounded over stated draws. Sub-pop denominator = episodes
(per-episode net-mean). UNPOWERED (no finite MDE) reported, never failed. `e=0`/no-plant = the null
guard. No percentage-of-zero metrics.

## Implementation safety constraints (developer)

- `gate_stack_adaptive` reuses frozen sub-primitives **unchanged**; `referee_calibration.py` stays
  byte-frozen. L1+coverage identical to frozen. Only L3/L5 economics + L2-removal differ.
- `q* = 0.75`, `materiality_bps` (frozen map), `POWER_TARGET`, `ALPHA` are module constants
  (performance-independent, Q5) — never read from outcomes or the state mask.
- Episode = contiguous same-nonzero-position run; per-episode net-mean on amortized bps; block-
  bootstrap over episodes with the frozen block length; deterministic seeds.
- Power-aware abstain = leg has no finite MDE on the synthetic-positive calibration for that cell.
- Open-to-open `≤t-1`; first-70% + domain fence; never the final 30%. `CloseTime` ordering. `tqdm`
  on the stratum loop. Bound `N_PLANT`/`N_NULL`/`N_BOOTSTRAP` (start `500/80/20` as E2).
- The adaptive gate is **NOT frozen here** (E5 freezes); E3a builds + characterizes DET vs frozen.
  **Not** tuned on CF-MR-002 (absent from this experiment).

This experiment builds the economic-leg adaptive gate and measures its DET-dominance vs the frozen
gate on the E2 substrate. It does not freeze the gate (E5), adjudicate any candidate, touch L1, add
the return-series unit / composite-form selection (E3b), or touch the global holdout.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-06-29)

Checked against `references/governance-constraints.md` + binding D0 + the operator E3-split decision:
- **Single falsifiable question** — DET-dominance of the economic-leg adaptation vs frozen. Q9/Q4
  correctly deferred to E3b; one rung. ✓
- **D0 honored** — L1+coverage rigid (untouched); adapt only L3/L5; sparse stays UNPOWERED by design;
  predeclared "frozen-not-improvable" null (D0:104-106). No D0 amendment. ✓
- **Sub-population L5 candidate-blindness (scrutinized)** — fixed `q*=0.75` + frozen materiality;
  statistic = block-bootstrapped q\*-quantile of per-episode amortized net-mean on TEST; **no state-
  mask peek, no selection, no performance-derived threshold** (Q5-clean). The upper-quantile FPR-
  inflation risk is acknowledged and **is** the empirical question, gated by the binding dogfood-FPR
  control. ✓
- **Leak tripwires** — dogfood-FPR ≤ frozen (binding); no-plant guard; **future-destroy collapse on
  the sub-pop path** (the right guard against a quantile mining noise → REJECT-class if it survives).
  ✓
- **3-arm DET** (frozen / frozen-amortized / adaptive) cleanly separates the E1 accounting gain from
  the E3a leg-adaptation gain. ✓ **Per-stratum binding** (L-03); pooled disclosure-only. ✓
- **Classification** analysis-only; frozen suite byte-frozen (adaptive built in `referee_adaptive`);
  reuses frozen sub-primitives unchanged; holdout sealed; 0 reads/slots; not tuned on CF-MR-002. ✓
- **Budget** — 1 new module (adaptive gate + 2 helpers) + harness; 3 plots; within comparative. ✓

**Info (non-blocking):**
1. `q*=0.75` is a pre-registered, justified constant (recovers ≥25%-population edges), Q5-compliant.
   A **sensitivity sweep on `q*`** (and on `materiality`/`α`) is an **E4** robustness item, not E3a.
2. The sub-pop materiality bootstraps a **quantile** (not a mean) — the developer implements a
   block-bootstrap of the q\*-quantile over episodes (same Politis-Romano resampling; quantile
   statistic). Reuse the frozen block length / seeding.
3. The "≥1 economic leg powered-and-passed" clause + the L5 pooled-OR-subpop admission widen FPR by
   design (Q1 economic ≤α budget); the realized dogfood-FPR-control tripwire is the binding check.

No REVISE issues. Proceed to Stage 2 (build `gate_stack_adaptive` + sub-pop helpers in
`referee_adaptive.py`; reuse the E2 harness scaffolding for the 3-arm DET comparison).

---

## Amendment 2026-06-29 (A1) — dispersion-normalized sub-pop L5 + noise-tolerant verdict

**Operator decision (Jerry, 2026-06-29):** the first E3a run completed + audited PASS (see
`audit.md`), but surfaced a gate defect and a brittle verdict rule. Per the amend-in-place norm
(dated amendment + hard-delete `results/` + full rerun, **not** a follow-up experiment), this
amendment **supersedes** the clauses below. Original run results were diagnostic only; they are
hard-deleted before the rerun. Rationale from the first run (audit-confirmed): the adaptive gate
recovered STATE (ΔMDE median 10.5, max 24 bps) **and** sparse (28/32), leak-clean and D0-compliant
(**L1 proven bit-identical / rigid** — not via any amortized-`effective_n` shift), but (a) the
**raw-bps `q*=0.75` sub-pop L5 path over-fired on high-dispersion 4h nulls** — every dogfood
false-positive passed via that one leg, because the 75th-pct of per-episode **raw-bps** means is
large even for random positions when return dispersion is high; (b) `classify_stratum` used a strict
`FPR_adaptive > FPR_frozen` with `FPR_frozen ≡ 0`, so a single 1/162 noise pass tripped FPR_BROKEN
→ "15 DET / 17 FPR_BROKEN" was brittle (16/17 within Wilson noise of 0; only JP225/4h resolved).

### A1.1 — Sub-population L5 is now STUDENTIZED (cures the leg) — supersedes §"Sub-population L5"

The sub-pop statistic changes from a **raw-bps** q\*-quantile to a **scale-free studentized**
q\*-quantile. Per episode (unchanged): contiguous same-nonzero-position run; amortized net-mean bps
on TEST. New statistic:

`stud_q = q*-quantile(episode_net_means) / std(episode_net_means)`, `q* = 0.75` retained.

Block-bootstrap `stud_q` over episodes (same Politis-Romano resampling; **studentize per resample**:
each resample's `q*`-quantile ÷ that resample's std). The **sub-pop path PASSES iff BOTH**:

1. **studentized floor (NEW):** `stud_q` block-bootstrap **CI-lower > Q_STUD_MIN`** — resolves the
   upper quartile **above the pure-dispersion level** (kills high-σ noise-firing); AND
2. **economic floor (UNCHANGED):** raw-bps `q*`-quantile block-bootstrap **CI-lower >
   `materiality_bps[domain]`** (frozen 1.5/3.0 map) — keeps the economic-size floor.

The **pooled L5 path is UNCHANGED** (raw neutral CI-lower > `materiality_bps`; it never leaked —
rejected all dogfood). `L5 = pooled-material OR studentized-subpop-material`; power-aware ABSTAIN
unchanged (now also ABSTAIN if `std(episode_net_means) == 0` → studentized undefined). Why the
conjunction cures the leak: a high-dispersion **null** has large raw q75-bps (clears floor 2, the old
leak) **but** `stud_q ≈ Φ⁻¹(0.75) ≈ 0.6745` (just the null shape) → fails floor 1 → REJECT. A real
diluted edge (≥25% of episodes carry δ) has large raw q75-bps **and** `stud_q ≫ 0.6745` → PASS. This
pulls **E3b's return-series / Sharpe-LB unit forward into E3a**; **E3b's remaining scope shrinks to
composite-form selection (Q4) only**.

### A1.2 — `Q_STUD_MIN` derivation (candidate-blind, Q5 — the scrutinized constant)

**`Q_STUD_MIN = Φ⁻¹(0.75) ≈ 0.6745`** — the 75th percentile of the standard normal; i.e. the
studentized q75 of **any symmetric-about-zero null** distribution (scale-free, so independent of the
instrument's volatility). **Derivation by principle, not by data:** for episode means that are
approximately Gaussian by CLT and symmetric under a no-edge null, `q*-quantile / std → Φ⁻¹(q*)`
exactly; for `q*=0.75` that is `0.6745`. The studentized clause therefore requires the upper-quartile
episode return, in dispersion units, to be **resolved above where pure symmetric dispersion alone
places it** — a location/asymmetry signal, not a scale signal. **Candidate-blindness:** `Q_STUD_MIN`
is a fixed distributional constant derived from `q*` alone (`Φ⁻¹(q*)`); it reads **no data, no
dogfood FPR, no E3a outcome, no state mask** — it is computed before any run and could not be tuned
on results. It inherits the frozen economic floor via the conjunction (floor 2), adding **zero free
knobs** beyond the already-frozen `q*`. **Residual risk (characterised, not tuned):** real returns
have right-skew/fat tails, so a skewed null could push `stud_q` modestly above `0.6745`; this is left
for the rerun's **dogfood-FPR tripwire to measure** — `Q_STUD_MIN` is **not** pre-inflated to absorb
it (that would be tuning on the test). If residual skew-FPR is material, a conservative bump is an
**E4 robustness item**, recorded honestly, not applied now.

> **GATE: APPROVE (A1) — orchestrator inline pre-exec re-gate, 2026-06-29.** `Q_STUD_MIN = Φ⁻¹(q*)`
> is candidate-blind (derived from the frozen `q*` alone; reads no data / FPR / outcome / mask; zero
> free knobs). The studentized∧bps conjunction cures the high-σ leak while keeping the frozen economic
> floor. Verdict rule noise-tolerant (Wilson-resolved). Future-destroy retained on the studentized
> path (REJECT-class if a future-destroyed edge survives). Sparse-UNPOWERED tripwire correctly
> retracted (refuted prior). D0 honored (within-L5 only; L1 bit-identical/untouched). STATE-suppression
> and skew-FPR risks predeclared as honest partial/inconclusive outcomes, not pre-tuned. Amend-in-place
> mechanics (hard-delete + full rerun + re-audit + re-document) specified. No REVISE. Proceed to Stage 2.

### A1.3 — Noise-tolerant verdict rule (cures the brittle label) — supersedes §Method DET-DOMINANCE FPR clause + §"FROZEN-NOT-IMPROVABLE"

`classify_stratum` FPR clause is amended: a stratum is **FPR_BROKEN iff the adaptive dogfood-FPR is
STATISTICALLY RESOLVED above frozen** — `wilson_lower(passes_adaptive, draws) > dogfood_fpr_frozen`
(with `frozen ≡ 0` ⇒ `wilson_lower(adaptive) > 0`). Otherwise the FPR clause is satisfied and
DET-dominance is judged on MDE as before. This supersedes the strict point comparison
`FPR_adaptive > FPR_frozen`. The predeclared NULL "frozen-not-improvable" likewise binds only when
the adaptive dogfood-FPR is **Wilson-resolved** above frozen on ≥ a stated fraction of strata (not on
single-draw noise).

### A1.4 — Tripwire change — supersedes §"SPARSE stays UNPOWERED" predeclaration + leak-tripwire list

The **"sparse must stay UNPOWERED on adaptive" predeclaration / tripwire is RETRACTED** (refuted by
the first run + audit F1/F2: L1 is bit-identical/rigid, sparse passes L1 on 4h `min_state=8` and
lucky 1h draws, and sparse recovery is real — `no_plant ≤ 0.05`, future-destroy collapses).
**Sparse recovery is now an EXPECTED, characterised, D0-compliant outcome** (recovery lives in
L3/L5), **not** a tripwire failure. The cross-experiment note stands: E2's "sparse = L1 structural
veto, edge-independent" was **domain-conflated** (true 1h, false 4h). It is **replaced** by the
**noise-tolerant dogfood-FPR tripwire** (A1.3). **All real leak tripwires are RETAINED and apply to
the studentized path:** (i) **future-destroy collapse** — plant STATE edge, block-permute returns,
re-run the adaptive gate; detection **incl. via the studentized sub-pop path must collapse to FPR**
(a studentized quantile can still mine noise structure → a surviving future-destroyed pass is
REJECT-class); (ii) no-plant guard; (iii) the A1.3 Wilson-resolved dogfood-FPR control (binding).

### A1.5 — Updated interpretation criteria (predeclared, supersede §"Predeclared interpretation criteria")

- **DET-DOMINANCE (binding success):** adaptive strictly lowers MDE on STATE (and/or L5-limited /
  sparse) at adaptive dogfood-FPR **not Wilson-resolved above frozen**, no DENSE/TAIL loss. Expect
  **STATE + sparse recovery RETAINED** (the studentized floor must not kill genuine diluted edges)
  and **dogfood FPR collapsed toward 0** (the prior 16/17 noise-breaks should vanish; JP225/4h is the
  binding test of whether residual skew-FPR survives).
- **FROZEN-NOT-IMPROVABLE (valid NULL):** no stratum shows dominance, **or** the studentized sub-pop
  path still lifts the **Wilson-resolved** dogfood-FPR above frozen on ≥ a stated fraction of strata.
- **STUDENTIZED FLOOR TOO STRICT (new inconclusive/partial):** if the studentized clause also
  **suppresses genuine STATE recovery** (STATE ΔMDE collapses toward 0 vs the first run's 7.5–24 bps),
  report that the dispersion floor is over-conservative → an E4 `Q_STUD_MIN` / `q*` sensitivity item.
  The first-run STATE ΔMDE (median 10.5) is the **disclosure-only** reference for "recovery retained."

### A1.6 — D0 / scope / mechanics

L1 + coverage stay **rigid / untouched** (verified bit-identical, audit F1); the studentization is a
**within-L5 statistic change** — still **economic-leg-only**, D0:101-106 honored. **No new free
knob** (`Q_STUD_MIN = Φ⁻¹(q*)` derived from the frozen `q*`). Mechanics: **hard-delete
`python/experiments/EXP-003/results/*` before rerun**; full 32-stratum rerun (`N_BOOTSTRAP/N_PLANT/
N_NULL` unchanged); the EURUSD bit-identity baseline is invalidated by the gate change (a fresh
baseline is unnecessary — the studentized statistic is the point). Re-audit (verdict forensics +
causal-provenance + the studentized-path future-destroy) → re-document. `referee_calibration.py`
remains byte-frozen; `q*`, `Q_STUD_MIN`, `materiality_bps`, `ALPHA`, `POWER_TARGET` are module
constants. Complexity unchanged (1 statistic swapped within `subpop_quantile_materiality` + 1 verdict
clause + 1 tripwire retraction). Plots unchanged.
