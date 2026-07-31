# SPDR Lane — Speed-Run Exploration Screens

The SPDR (`SPDR-###`) series is a **lightweight, TRAIN-only availability/exploration lane**
that gates a `WORTH_EXPLORING` disposition on an idea **before** it is committed to a full
cTrader-primary experiment and a candidate-family registration. It strips formal steps
(family registration, checkpoint design, fresh-context QA, referee framework, cTrader
execution) — but it does **not** strip the integrity firewall. SPDR reuses the already
sanctioned **availability-screen-first** discipline (methodology-canon: TRAIN-only, 0 slots,
0 reads, pre-registration).

Ratified 2026-07-07 (operator-signed). Source idea: `.ignore/temp/new-research/mtf.md`.

## Purpose

Fast, cheap read of whether an idea carries **signal-conditional availability** worth the
cost of a full experiment. A speed-run compounds several coherent questions in one grid and
runs vectorised in Python on the local dataset. Its only output is a disposition, never a
tradability or deployability claim.

**Hard vs flexible.** The integrity boundary below is HARD and never waivable. Everything
else — execution vehicle, stage shape, artifact extras — is a **default the operator may
override by directive** (recorded in the leg's `design.md`). Example: the operator may
direct an SPDR leg to run on the cTrader engine instead of vectorised Python (e.g. when
fill mechanics matter to the screen question); the leg remains an SPDR — TRAIN-only,
disposition-only, no estimand-gated verdict, no family action.

## Integrity boundary (HARD — this is what keeps L-01 intact)

| Rule | Why |
|------|-----|
| **TRAIN-only.** Train slice of the analysis set (first 70% of the first 70%). Never the TEST set, never the global holdout. Asserted in code. | Holdout/test are reserved for graduated, governed reads. |
| **Causal `t-1` lag.** Every decision at bar-open on confirmed (≤ `t-1`) bars; open-to-open returns; any limit-fill simulation (e.g. CTRL-03) resolved causally on the 1-minute bars, no intrabar look-ahead. | A Python screen is numerically blind to a leak (L-01). The lag must hold by construction. |
| **No tradability / deployability claim.** Output = availability/lift disposition only. No net-of-cost tradable-edge number, no counted TEST read, no holdout touch, no family status change. | Only cTrader-primary experiments may make a tradable claim. |
| **Matched-control + seed battery.** Lift is measured as the treatment (HTF filter) *over the control model* (the baseline). Random controls use a ≥25-seed battery with a percentile/rank read, never a single twin (L-19). | Single random twins are noisy yardsticks that can pass a dead idea or kill a live one. |
| **Per-stratum reporting; multiplicity disclosed** (L-03). A pooled figure is disclosure-only. Speed-runs sweep large grids — disclose the cell count and the multiplicity treatment. | Pooled verdicts mask the binding stratum; big grids inflate false positives. |
| **No local accounting primitives** mimicking `xen.adjudication` P&L for a verdict. Screen metrics = availability/lift (`xen.evaluation` toolbox), not a booked P&L. | Local accounting certified three wrong verdicts (L-18 / critical-017). |
| **Dependence-matched uncertainty.** Any CI on a per-bar estimand with overlapping H-bar forward windows must use a block bootstrap with **block ≥ H** (or resample a non-overlapping / greedy trade series). Library defaults (e.g. block=5) do not substitute for this choice; a mismatch invalidates every CI-clearance call on that estimand. | Phase-010 correction (2026-07-08): block=5 on overlapping H=48 windows (autocorr 0.84 at lag 5) understated uncertainty ~2–3× and manufactured a fade thread that did not exist. |

## Dispositions an SPDR may output

Per-stratum disposition, one of:

| Disposition | Meaning |
|-------------|---------|
| `WORTH_EXPLORING` | Signal-conditional lift over the matched baseline is present; route to a full cTrader-primary EXP + family registration. |
| `NOT_WORTH` | No lift over the matched baseline. |
| `INCONCLUSIVE` | Underpowered / vehicle-limited; not a negative (B-5, UNPOWERED ≠ evidence-against). |

SPDR **never** registers a family, spends a read, or makes a tradability claim. A single
SPDR leg never opens a checkpoint; a multi-leg series' disposition lives in its **phase
container** checkpoint (e.g. checkpoint-010 for the SPDR-001/002/003 series). A
`WORTH_EXPLORING` is a *routing signal*, not a verdict.

## SPDR characterisation contract (BINDING — added 2026-07-30)

The pipeline's general **single-hypothesis-per-experiment** rule does **not** apply literally to
exploratory SPDR characterisation. It is replaced here by this contract, which permits breadth and
forbids the vagueness that usually comes with it:

- an SPDR **may** traverse a **predeclared** full grid of components, devices and combinations;
- **every stratum must name the exact comparison** it makes and emit **its own direct estimate and
  uncertainty** — not a share of a pooled effect, and not an inference from a neighbouring stratum;
- **all strata are reported.** No winner-only pruning, and no experiment-wide
  supported / refuted verdict over the grid;
- **individual component × device strata must remain visible before any combined stratum is
  interpreted.** A combination read never substitutes for the individual contribution reads;
- **measures are device-native.** Choose each outcome for what that device actually does; do not
  impose one universal score across every device in the grid;
- **every adaptive or conditioned arm carries a direct comparator** — the same device unconditioned,
  on the same eligible population;
- for an operator-declared characterisation series, event count, uncertainty and MDE may be
  **informative metadata only**: they remain visible but do not create positive/negative labels,
  prune rows or gate companion experiments;
- the **operator** interprets the resulting map and decides the next research action. The SPDR
  produces the map, not the decision.

**Why this exists.** A grid whose strata share one scale-free summary score, or whose device
questions are bundled behind a single shared protocol, cannot say which component helped which
device — it produces a verdict nobody can attribute. Two designs were withdrawn from the programme
on 2026-07-30 for exactly that defect.

## Stages (lean)

```
1 Design ......... quant-designer (lightweight)   → design.md  (+ screen-boundary declaration)
2 QA ............. code-asserted self-check         (no fresh-context subagent)
3 Screen run ..... Python, TRAIN-only, causal       → results/ plots/
4 Screen summary . neutral quantification          → screen.md
5 Deep analysis .. FRESH-CONTEXT analyst (subagent) → analysis.md  (+ follow-up threads)
    [OPERATOR — disposition]
```

**Stage 5 is mandatory (SPDR-001 lesson, 2026-07-07).** A same-context screen summary drifts
toward a mean-only, verdict-shaped read that buries facets and can invert the conclusion (SPDR-001
`screen.md` first-pass wrongly booked a drift-confound + NOT_WORTH; the fresh-context analyst
overturned it — τ≈0, dispersion = normaliser mechanic, HTF-specific coupling on 2 instruments).
Every SPDR therefore runs a **fresh-context data-analyst pass** (subagent invoking the
`data-analyst` skill) that **quantifies** the relationship across every facet (effect sizes + CIs,
distribution shape, dose-response, heterogeneity, power) — magnitudes, not a verdict. `screen.md`
must stay neutral and quantification-first, subordinate to `analysis.md`; the analyst resolves its
own open threads before the operator disposition.

**Base-conditional interpretation (operator directive 2026-07-07).** The control strategies
(random / momentum / reversion) are **baselines, not viable strategies**, and their own failure is
generally uncharacterised. Therefore: (1) do NOT read a small HTF-filter lift over a failing
baseline as "HTF ineffective" — attributing a broken strategy's continued failure to the HTF
overlay is a misattribution; (2) quantify HTF context as its **own conditional effect** on the
outcome distribution — the magnitude by which the LTF forward-return distribution (mean, dispersion,
sign) moves as the HTF state varies — independent of whether either arm is profitable; lift-vs-
baseline is one lens, not the frame; (3) characterise the base strategy's own behaviour as a
**separate facet** so the HTF effect is interpretable; (4) a measurable HTF-induced distributional
shift on a null base is a **positive quantification** of HTF context, reported as a magnitude —
never qualified away as "within noise". This is the deeper reason quantify-not-qualify is binding.

**Granularity + quantify-not-qualify are binding (operator directive 2026-07-07).** The analyst
reports **per stratum** — the stratum is (instrument × domain-pair × filter-variant × hold) — as
**magnitudes with uncertainty**, so the hypothesis is judgeable one stratum at a time. Two standing
faults are prohibited: (1) **qualifier/verdict framing** ("wash", "not supported", "at the chance
rate", "no systematic effect") — report the measured Δ and its CI, not an adjudication; (2)
**detrimental pooling** — grid-wide summary counts ("X% of cells cross zero", "N+/M− of 872",
"median percentile") must never be the headline; a pooled line is disclosure-only (L-03). Emit the
full per-stratum magnitude table to `results/` (nothing hidden behind a pooled count). Per-stratum
UNPOWERED is a power statement, never folded into a negative (B-5).

**Series verdict.** When an idea is split across a multi-leg SPDR series (e.g. CTRL-01/02/03 →
SPDR-001/002/003), the candidate disposition is taken **once, after the last leg** — individual
legs are characterisation only, no per-leg disposition.

Stage 2 is a **code-asserted self-check**, not a fresh-context QA subagent: the screen script
must assert the TRAIN-only fence, the `t-1` lag, and (for random controls) seed-battery
regeneration; `design.md` carries a short integrity checklist. Fresh-context QA is reserved
for the full cTrader pipeline the winner graduates into.

## Artifacts

```
python/experiments/SPDR-###/
├── design.md      # mechanism, grid, metric, screen-boundary declaration + integrity checklist
├── screen_code/   # self-contained: signal-gen + HTF filter + matched-baseline lift
├── analysis_code/ # fresh-context analyst's own richer emissions (stage 5)
├── results/  plots/
├── screen.md      # neutral quantification summary (subordinate to analysis.md)
└── analysis.md    # fresh-context analyst: full-facet quantification — UNCAPPED (binding read)
```

- IDs zero-padded, never reused: `SPDR-001`, `SPDR-002`, …
- Indexed in `python/experiments/INDEX.md` with an **SPDR** marker.
- **Not** listed in family detail indexes (an SPDR has no family).
- No `estimand_validation.json` gate (that gate adjudicates cTrader emissions / canonical
  accounting; a screen makes no P&L verdict). The integrity substitute is the code-asserted
  fence + causal-lag self-check above.

## Graduation

A `WORTH_EXPLORING` disposition routes the idea into the **standard pipeline**: candidate-family
registration → checkpoint design → mechanism-first `design.md` → fresh-context QA → cTrader
execution → estimand gate → data-analyst → operator verdict. The SPDR result is prior evidence
for that experiment; it is never itself promoted to a family verdict.

### Unit convention + money-unit floor (BINDING — amended 2026-07-09, EXP-025 lesson L-21)

The screen→graduation handoff is where a dimensionless screen number becomes a money claim.
EXP-025 inflated its target 4× by asserting the wrong ATR divisor from memory (design declared
1h HTF ATR; the screen normalised by 5-min LTF ATR(14)[t−1]).

1. **Unit pin (screen side).** Every SPDR `design.md` and `analysis.md` must state the
   normaliser **object** exactly (indicator, period, timeframe, lag — e.g.
   `LTF 5min ATR(14)[t−1]`) wherever a normalised effect size is reported. A bare "ATR" is
   non-compliant.
2. **Conversion pin (graduation side).** A graduation `design.md` that converts a screen
   effect into bps/money must state (a) the divisor object verbatim from the screen code,
   (b) its measured TRAIN-median value in bps on the target instrument(s), (c) the resulting
   bps/trade effect — each verifiable against data, none asserted from memory. QA traces this
   as a clause.
3. **Money-unit floor (disposition gate, informative).** Before a `WORTH_EXPLORING` routes to
   graduation, convert the best-cell screen effect to bps/trade with the actual normaliser
   value and compare against a cost floor: spread estimate + commission + one-sided-capture
   dilution (≈ gap/2). If the best cell sits at or below the floor, the disposition must say
   so explicitly; the operator may still graduate it — but only re-framed as an apparatus or
   characterisation test, never a tradability test.
