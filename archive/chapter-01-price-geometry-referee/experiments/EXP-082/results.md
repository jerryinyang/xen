# Results: Experiment EXP-082 — Mechanical Exit Derivation from the Frozen D3 Rule

**Phase:** 018 (CF-CAPGEO-001) · **HYP:** HYP-003 (derive) · **Verdict:** **DERIVATION_DELIVERED** ·
0 candidate slots · 0 counted TEST reads · no exit simulated · audit PASS (0C/1W/3I) · 2026-06-22.

## Summary

Applying the frozen D0 §D3 mechanical exit-derivation rule to EXP-081's 184 locked per-cell TRAIN
statistics produced a well-defined triple-barrier exit `(T_fav, S_adv, H_cap)` for **all 552**
(184 cells × 3 derived candidates `D1-MEDIAN-CAPTURE` / `D2-TAIL-ROBUST` / `D3-CAPTURE-EFFICIENT`).
The derivation is deterministic (byte-identical replay), holdout-clean (no market data read — only the
EXP-081 result files), provenance-asserted against the audited EXP-081 fingerprint, and the derivation
function is sha256-pinned as the binding artifact EXP-083 will import. **DERIVATION_DELIVERED** is met
on every cell. This is a *lock* step: it builds and freezes the exit definitions but makes **no edge,
tradability, or viability claim** — no exit was applied to any return.

The substantive read is not whether the rule ran (it did, faithfully) but **what the derived exits
turned out to be**. Two structural facts dominate, both flowing from EXP-081's finding that the
post-entry catastrophe is a *heavy continuous left tail, not a separated mode*: (1) the rule's
tail-engaging adverse instrument (`m_anti`) is dormant in 551/552 rows and the adverse leg reverts to a
generic `MAE_q90` stop; and (2) that stop sits *at the edge of* the catastrophe it was designed to cut,
in a wide-stop/modest-target geometry that reproduces the CF-HA-HARAMI-001 failure shape inside the
derived exit. These pre-load EXP-083's separability gate as the decisive question.

## Detailed Findings

### Finding 1 — The rule is total over the member set: 552/552 valid (DERIVATION_DELIVERED)

- **Observation:** every (cell, candidate) yields `(T_fav>0, S_adv>0, H_cap≥1)`; 0 `UNDERPOWERED`,
  0 `DEGENERATE`. `n_valid = 552/552` (`derivation_validity.json`).
- **Evidence:** barrier ranges are comfortably interior — `T_fav` ∈ [2.42, …] med 3.31 (D1/D2),
  [1.81, …] med 2.56 (D3); `S_adv` ∈ [1.79, …] med 9.21; `H_cap` ∈ [34, 73] bars (D1/D2, q75-based),
  [17, 41] (D3, median-based). No cell approaches the ≥30-event floor (EXP-081 `n_usable` ∈ [46, 5535]).
- **Interpretation:** the verdict is robust, not marginal — well-conditioned inputs map to well-defined
  triples. The interpretation guide's **DERIVATION_DELIVERED** condition (all cells valid ∧ determinism
  ∧ harami identity ∧ hash-pin) is satisfied.

### Finding 2 — 3 registered candidates collapse to 2 distinct exit definitions on this snapshot (D1≡D2)

- **Observation:** D1 and D2 emit **numerically identical** triples on **184/184** cells
  (`d1_eq_d2_accounting`: `n_d1_ne_d2 = 0`). D3 differs from D1/D2 only by using the q40 favourable
  target and the median (vs q75) time cap.
- **Evidence:** D2's distinguishing operation is `S_adv = min(m_anti, MAE_q90)` when the dip resolves,
  else `MAE_q90`. The dip resolves in **1/184** cells (US500-1h `SUB-AVWAP`), and there
  `m_anti = 1.79 < MAE_q90 = 9.00`, so `min` returns `m_anti` — exactly D1's value. Everywhere else both
  fall back to `MAE_q90`. The audit confirmed D1/D2 are genuinely **distinct functions** (a synthetic
  `m_anti = 6 > MAE_q90 = 4` makes D1 keep 6.0 while D2 tightens to 4.0); they merely **coincide** here.
- **Interpretation:** D2 ("tail-robust") was the one candidate designed to *differ* by cutting the
  catastrophe tail tighter. On this data its lever is **dormant** — so the tail-robustness hypothesis is
  **untested by construction** at this snapshot, not refuted. EXP-083's {candidate × stratum} Holm grid
  must account D1 and D2 as numerically identical here while preserving them as distinct functions for
  the per-fold causal re-fit (a fold subsample could resolve `m_anti > MAE_q90`).

### Finding 3 (mechanism, from the audit) — the catastrophe-engaging guard is inert; the derived stop reverts to a generic wide quantile

- **Observation:** `s_adv_source` is `m_anti` in exactly **3/552 rows** (the US500-1h-AVWAP cell ×3
  candidates) and `MAE_q90` in **549/552**.
- **Evidence:** EXP-081 found the MAE distribution unimodal almost everywhere (`dip_p` median 0.976;
  only 0.5% of cells dip below 0.05) — the catastrophe is a heavy **continuous** tail, not a separated
  second mode. D0 §D3 left-tail-parameterized the adverse leg on `m_anti` *specifically* as the
  structural anti-harami guard; with no separated mode to detect, the guard's instrument is dormant and
  the leg falls back to a generic `MAE_q90` stop (~9.0–9.7 ATR by substrate).
- **Interpretation:** the rule degraded **gracefully and as the D9 bite-check anticipated** ("the D3
  adverse leg predominantly uses the `MAE_q90` fallback at realistic cell sizes") — this corrupts no
  EXP-082 number. But it means the *specific* tail-cutting mechanism the rule was built to express is
  inactive; the derived stop is a location/quantile stop, not a catastrophe-boundary stop.

### Finding 4 (the crux for EXP-083) — the derived exit reproduces the CF-HA-HARAMI-001 failure geometry

- **Observation:** the derived stop `S_adv` (≈9.2 ATR, `MAE_q90`) sits **at the edge of** the
  catastrophe magnitude `|q05|` (≈9 ATR): median `S_adv − |q05| = −0.008 ATR`, with the stop landing
  *outside* the catastrophe in ~50% of cells. The reward-to-risk geometry is `T_fav/S_adv ≈ 0.35`
  (D1/D2) / `0.28` (D3) — a **modest target behind a wide stop**.
- **Evidence (per substrate, D1; uniform — not a one-substrate artifact):** median `S_adv − |q05|` =
  +0.06 (AVWAP), −0.0001 (both harami), −0.08 (random); `T_fav/S_adv` = 0.34–0.37 across all four
  substrates. Plot 3 (`T_fav` vs `S_adv` with `|q05|` sizing) encodes this directly.
- **Interpretation:** geometrically, a stop this wide rarely triggers before the catastrophe completes,
  while the modest target harvests the median — **the prior family's "harvest the median, leave the
  catastrophe" shape reproduced inside the derived exit itself.** This is exactly the situation the
  Phase 018 separability gate (S2: "is the median edge propped up by a structure that will collapse?")
  was created to adjudicate. EXP-082 has faithfully *built* the guard the rule specified; whether any
  exit geometry can cut the tail without removing the median edge is the live EXP-083 question, and this
  result **pre-loads it toward "the tail truncation as parameterized does little."**

### Finding 5 — integrity: deterministic, holdout-clean, hash-pinned, harami-identical

- **Observation:** determinism replay byte-identical (`determinism_replay_byte_identical=true`); harami
  triple-identity holds (46×3 triples bit-identical across the two harami substrates,
  `harami_identity_ok=true`); EXP-081 provenance fingerprint asserted (8/8 checks); the
  `derive_barriers` module sha256 matches on-disk (EXP-083's hash-pin will hold); `holdout_untouched`,
  `counted_test_reads=0`, `candidate_slots=0`.
- **Evidence:** `run_metadata.json`, `derivation_validity.json`; audit independently re-derived all 552
  triples from the raw EXP-081 summary with **0 mismatches**.
- **Interpretation:** the locked exit definitions are trustworthy and reproducible; EXP-083 can import
  the exact frozen rule and re-fit it per fold without ambiguity.

## Hypothesis Verdict

**DERIVATION_DELIVERED** (the experiment's predeclared completeness verdict — there is no
SUPPORTED/REFUTED axis here; 0 slots, no edge evaluated). The HYP-003 question — *does the frozen D3
rule yield a well-defined, estimable triple-barrier exit for every member cell?* — is answered **yes**
for all 552 (cell × candidate). The derivation is faithful (independent re-derivation 552/552 exact),
deterministic, holdout-clean, and the binding function is hash-pinned for EXP-083.

The result carries **no edge or tradability claim**. Its informative content is structural: the derived
exits are, on this data, a **wide generic-quantile stop behind a modest target** (Findings 3–4), with
the rule's intended catastrophe-engaging instrument dormant — making the EXP-083 separability gate the
decisive next test rather than a formality.

## Limitations / Caveats (from the audit, binding into Stage 7/EXP-083)

- **No edge / tradability / viability verdict.** Gross, TRAIN-only, no exit applied, no return computed,
  no counted TEST read. EXP-082 *defines* exits; it does not *evaluate* them.
- **D2's tail-robustness lever is dormant** (D1≡D2 184/184) because `m_anti` resolves once and below
  `MAE_q90`. The tail-robust thesis is untested by construction here, not refuted (Finding 2).
- **The catastrophe guard is inert by construction** (Finding 3): the adverse leg reverts to `MAE_q90`
  in 549/552 rows because the catastrophe is a continuous tail, not a separated mode. This is the same
  family of shape-blindness G-017 flagged for `ASS` (a mode/dip detector cannot see an unseparated
  tail); the rule degrades gracefully, so it moves no EXP-082 number, but the *intended* differentiation
  is inactive on this snapshot.
- **The derived stop sits at the catastrophe edge in a harami-trap geometry** (Finding 4) — the single
  most important carry-forward: EXP-083's separability gate (S2) is the crux, pre-loaded toward the
  derived stops doing little tail truncation.
- **D1/D2 are distinct functions** despite coinciding numerically; per-fold re-fit in EXP-083 could
  separate them. Do not collapse them in the registry.

## Recommended Next Experiments (new scopes, not extensions)

- **EXP-083 (HYP-004, test + benchmark — already on the Phase 018 slate):** evaluate all TRAIN-valid
  derived candidates (D1/D2/D3) **and** the conventional benchmark exits under the **frozen referee
  suite (binding)** with the **separability gate (S1 ∧ S2)** as the pre-TEST shape-guard, per substrate,
  on the new 5-year strata. Counted TEST reads are spent only there (D4.1: one frozen WF run per stratum,
  all valid candidates batched, Holm across the {candidate × stratum} grid). This result frames S2 as
  the crux: a candidate whose net edge survives only because its wide stop never cuts the catastrophe is
  a capture-bound/median-only artifact and must fail S2.
- **(Conditional, own D0 only on a confirmed EXP-083 result):** if no registered exit (derived or
  benchmark) cuts the catastrophe without removing the median edge, an operator-directed
  **re-parameterization of the adverse leg** from a *dip-mode* detector to a *tail-quantile* stop (e.g.
  an inner quantile of the loss tail rather than `MAE_q90`) would be a new D0-amendment — **not** an
  EXP-082/083 scope extension. EXP-082 deliberately did not pursue this (the rule is frozen at D0).
