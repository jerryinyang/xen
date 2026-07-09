# EXP-018 — CF-MR-005/HYP-003: Deliberate Ladder Harvest Disposition Probe (price-primary, 4h)

**Completed:** 2026-07-04 · **Operator verdict: NOT SUPPORTED** (booked 2026-07-04; analyst
recommendation NOT SUPPORTED, adopted) · Checkpoint: `2026-07-04-006-cf-mr-005-disposition`.
First experiment run end-to-end under the INFR-001 pipeline (quant-designer → fresh-context QA
subagent APPROVE → operator execution gate → estimand script gate → data-analyst → operator
verdict). Artifacts: [design](design.md) (+ Amendment A1) · [qa-review](qa-review.md) ·
[analysis](analysis.md) · [code notes](code/IMPLEMENTATION.md) ·
[gate](results/estimand_validation.json) · emissions `data/strategy_runs/EXP-018-4h-*/`.

## 1. Question + mechanism

Does the VAL-006 residue (US2000 e0/e2 ladder cluster; US500 both-leg cluster) survive as a
**dislocation-conditioned, exposure-honest, regime-robust** positive episode economics when the
ladder harvest is specified deliberately (not as EXP-014b's accidental arm), emitted under the
correct accounting contract (`xen.adjudication`, post-critical-017), and evaluated natively —
and NOT in a predeclared negative-control cell (NZDUSD, a confirmed per-leg loser)?

Mechanism claimed: 4h index dislocations vs the S8 basket-relative anchor overshoot and partly
revert; a resting ladder (adds at z ∈ {1.5, 2.0, 2.5}) buys the overshoot in tranches; each
leg's reversion to the moving anchor mean is the P&L unit; legs chain into multi-week episodes.
The kill test: random-timing ladders with the same cadence should earn materially less.

## 2. Scope + method

- **5 live cells:** US2000 arm A (harvest: moving-anchor TP + ⌈3·HL⌉ cap-48 time-stop, no SL,
  no form-1) × reentry extend (primary) and allow (contrast); US2000 arm B (braked: frozen TP +
  outward SL 1·D + time-stop = `bracket`); US500 both-leg market arm A (joint form-1 + group
  time-stop, reentry none — Amendment A1); NZDUSD arm A/extend (negative control).
- **Controls (per cell):** random-timing destroy — seeded schedule (live episodes as rigid
  templates at random non-warmup TRAIN bars; matched per-level counts, gaps, dirs, realized
  holds; **matched-hold market exits**, A1 — never the anchor, L-08); entry-delay +1 bar
  (causal tripwire); 60h basket phase-shift (disclosure-only, extend cells). 18 engine runs.
- **Band/fence:** TRAIN only (49% cutoffs: US2000 2024-09-10, NZDUSD 2024-09-06, US500
  2024-09-17); TEST/holdout never emitted; 0 counted reads, 0 slots.
- **Estimand:** episode net (`build_episodes`) primary, per-leg net secondary; frozen 4h costs
  (US2000 5 / NZDUSD 2 / US500 3 bps per leg); block-5 bootstrap CIs; exposure-honest
  economics (`xen.evaluation`); predeclared bands (design §7); no frozen-referee reads.
- **Integrity:** estimand gate `blocking_pass: true` on all 14 roots (reconciliation ≤ 7e-12
  bps); QA golden trace PASS (levels < 1e-6; 311/311 fills at-or-favorable; time-stops exact);
  `check_no_local_accounting` ok; delay tripwire graceful everywhere (no timing leak).

## 3. Key evidence

**Primary (episode net, frozen cost) — WASH in all four residue cells; control passed:**

| Cell | n_ep | mean bps/ep | 95% CI | MDE | Band (§7) |
|---|---|---|---|---|---|
| US2000 A/extend | 127 | +381.9 | [−122, +809] | 504 | WASH (powered vs residue ~575) |
| US2000 A/allow | 132 | +82.5 | [−151, +228] | 234 | WASH |
| US2000 B/extend | 70 | +85.2 | [−570, +644] | 655 | WASH (marginal power, predeclared weak) |
| US500 both-leg A | 79 | **−2.5** | **[−26, +24]** | 24 | **WASH, well-powered** — VAL-006's "4/4 variants positive" does not reproduce |
| NZDUSD (neg-ctl) | 75 | −273.6 | [−694, +52] | 421 | control-pass (stayed ≤ 0) |

**Kill test (random-timing destroy) — dislocation conditioning unsupported:**

- US2000 A/extend: control earns +187.2 bps/ep — **collapse fraction 0.49**; live−control diff
  CI [−516, +866] (indistinguishable). A/allow control **beats** live (1.96); B/extend and
  US500 reads are noise (−2.09, 2.74 on tiny magnitudes).
- **NZDUSD random-timing per-leg net = +31.5, CI [+13.7, +49.9] — CI_low > 0 from pure random
  timing** while the dislocation-timed live arm loses −20.6/leg. The per-leg-CI-positive
  signature the residue was built on is reproducible with no signal; dislocation timing
  anti-selects on NZDUSD.

**What is real (evidence for, retained honestly):** US2000 A/extend per-leg net +36.8
CI [+9.2, +64] at frozen cost, survives 2× cost (CI_low +4.2 at 10 bps); exposure-honest
return on avg deployed exposure 24.8%/yr vs 2.8% exposure-matched B&H; ladder-depth gradient
persists (+17.0/+49.4/+67.5 by level). But:

**Attribution (evidence against):** 2022 is the only CI-positive year in any cell (US2000
A/extend 2022 +811 [+348, +1441]; 2023 mean −393); longs +72.7/leg vs shorts +7.2 (long-side
index drift dominates); top-5 of 127 episodes carry 82% of total net; peak 43 concurrent legs,
maxDD −29.5k bps ≈ 61% of total net, return on **peak** exposure 2.9%/yr ≈ matched B&H; braked
arm B dies (SL fires as often as TP: 588 vs 579). Shift disclosure incoherent (0.53/1.03/2.72)
— consistent with neither construction- nor timing-dependence.

## 4. Verdict

**Operator verdict (final, booked 2026-07-04): NOT SUPPORTED.** The hypothesis required
dislocation-conditioned + exposure-honest + regime-robust episode economics in the residue
cells and not in the control. Realized: episode-level wash everywhere (US500 a well-powered
zero), the random-timing kill test unfalsified (a random ladder reproduces the per-leg
signature outright on NZDUSD), and 2022/long-drift concentration. The negative control
behaving as predicted validates the discrimination machinery. The US2000 per-leg positive is
real as an accounting fact but indistinguishable from unconditioned ladder carry riding 2022
index drift with deep-add inventory.

Analyst recommendation: NOT SUPPORTED (identical; `analysis.md` §6).

## 5. Registry disposition

Evidence row appended to `docs/signal-registry/candidate-families/cf-mr-005.md` (HYP-003 →
COMPLETE, NOT SUPPORTED) and `docs/signal-registry/multiplicity-registry.md`. 0 slots, 0
counted TEST reads, holdout sealed. Family status transition (CF-MR-005 → RETIRED) is recorded
in the checkpoint-006 retrospective (operator-signed 2026-07-04), not here.

## 6. Follow-ups (separate future experiments, not commitments)

- Side-split (long-only vs short-only) episode economics on the existing emissions.
- Random-timing variant with episode-level (not leg-level) cadence matching.
- The NZDUSD random-ladder anomaly (+31.5/leg CI_low>0 from unconditioned matched-hold
  ladders) — a two-sided vol/rebound-harvest question, NOT mean reversion; would be a new
  registered family if ever pursued.
- Standing caution (KB-worthy): a per-leg CI_low>0 on a ladder object is not evidence of
  conditioning — random-timing ladders can produce it; demand an episode-level,
  cadence-matched control before believing any such read.
