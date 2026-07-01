# EXP-008 — CF-MR-003/HYP-001: Cross-Domain Mean-Reversion Availability Screen

**Family:** CF-MR-003 (REGISTERED 2026-07-01) · **Phase:** 002 G0 · **Type:** availability screen (event study)
**Classification:** **ANALYSIS-ONLY** (justified §2) · **Slots/reads:** 0 candidate slots, 0 counted TEST
reads · **Holdout:** final-30% sealed; TRAIN-only (first 70% of the analysis set) · **Honest prior:** LOW,
**but deliberately given a fair full-space test** (operator, 2026-07-01): this screen **gates the entire
family**, so it explores **5 anchor-series constructions × 3 domain pairs**, not one, under strict
multiplicity control — the family is admitted or closed on breadth, not dismissed by analogy.

## 1. Falsifiable question (one)

*Do exec-domain entry events conditioned on a **cross-domain deviation series characterised mean-reverting
at `≤ t-1`** exhibit a favourable reversion excursion (price collapse toward the higher-domain anchor)
exceeding a matched-random, matched-count, matched-regime within-instrument control — for **any** of 5
anchor constructions × 3 domain pairs, per stratum — or not?* Honest prior: not (CF-MR-002 exonerated;
terminal-branch). **Edge = Δ-over-random**, never raw excursion. Anchor-series and domain-pair are
**exploration axes** under cross-axis multiplicity control (§5); the binding endpoint stays per stratum.

## 2. Price-primary vs analysis-only — ANALYSIS-ONLY (justified)

Price-primary = *generates signals/entries/positions/edges from price → must run in cTrader engine*. This
experiment **characterises conditional forward-excursion availability** on real prices vs a matched-random
control; it **books no strategy, positions, P&L, orders, or cost**. It is the EXP-081 / EXP-086–088
availability-screen pattern (analysis-only, TRAIN, Δ-over-random). No edge is generated or executed → not
price-primary. Strategy machinery (`/DIRECTION /REENTRY /TARGET /EXIT` + fills + net P&L) is **deferred** to
a later, separately-gated price-primary experiment **only if** this screen admits (avoids "measure
availability last", methodology-canon). Causality enforced: all conditioning `≤ t-1`; excursion forward,
open-to-open, real prices (§6).

## 3. Data scope

- **Universe:** 16-instrument INFR-003 5-year canonical (VAL-003 minus DE30; dataset-reference §Eras).
- **Domain-pair axis (3, operator-ratified):** **4h/1h**, **4h/15m**, **1D/1h** (anchor:exec ratios
  4:1 / 16:1 / 24:1). 15m is cost-flagged elsewhere — irrelevant to this cost-free rung.
- **Anchor-series axis (5, §4):** S1 CENTER, S2 RANGE, S3 DETREND, S4 OU, S5 SPREAD.
- **Stratum = (instrument, anchor-series, domain-pair).** Max 16×5×3 = **240 cells** (minus S5 lone-class
  UNPOWERED). Per-stratum binding (L-03); pooled = disclosure-only.
- **Prices:** real time-bar OHLC only. Domains built by `xen.domain_bars.build_domain_bars` (holdout-fenced,
  `min_coverage=0.90` + analysis-boundary fence). TRAIN = first 70% of the first-70% analysis set; final-30%
  holdout never loaded.

## 4. The 5 anchor series (all higher-domain, `≤ t-1`; windows in bar-count so they port across pairs)

Windows: `W_a=20` anchor-bars; robust-z / std scale over `W_z=200` exec-bars; screen window `W_s=200`
exec-bars. Deviation `d_t` faded toward `a_t` (`d>0`→short, `d<0`→long).

| # | Type | Anchor `a_t` | Deviation `d_t` / scale |
|---|---|---|---|
| **S1 CENTER** | single-dim | rolling **median**(4h/1D `Close`, `W_a`) | `price − a`; robust-z via MAD (`1.4826·MAD_{≤t-1}`) |
| **S2 RANGE** | range-aware | **Donchian midline** `(rolling_max(High,W_a)+rolling_min(Low,W_a))/2` | `price − a`; robust-z via MAD |
| **S3 DETREND** | derived (MR-meaning) | **rolling-OLS trendline**: fit `log(price) ~ time` over `W_a` anchor-bars; `a` = fitted value at `t` | residual `log price − a`; scale = rolling residual std |
| **S4 OU** | multi-dim source, engineered | **OU equilibrium θ**: rolling AR(1) fit `x_t=α+φx_{t-1}` on **HLC3** (range-informed base) over `W_a`; `κ=−ln φ`, `θ=α/(1−φ)`, `σ_eq=σ_ε/√(1−φ²)` | `(price − θ)/σ_eq`; requires `0<φ<1` (else UNPOWERED cell) |
| **S5 SPREAD** | cross-instrument | **rolling-β asset-class basket**: basket = equal-wt `log(price)` of predeclared class-mates (class\{i}, timestamp-aligned); OLS `log price_i ~ β·basket+α` over `W_a` anchor-bars; `a=β·basket+α` | spread `log price_i − a`; scale = rolling spread std |

**S5 asset classes (predeclared):** FX-majors {EURUSD,GBPUSD,USDJPY,USDCHF,USDCAD,AUDUSD,NZDUSD};
JPY-crosses {EURJPY,GBPJPY,AUDJPY}; indices {USTEC,US500,US2000,JP225}. **Lone → UNPOWERED for S5:**
{XAUUSD,BTCUSD} (no class-mate). Basket, β, and deviation all `≤ t-1`, timestamp-aligned (never bar index).

**MR screen (selector, identical across S1–S5), on the `d` series, trailing `W_s`, ending `t-1`:**
conjunction of **(a) Variance-Ratio** `VR(q=4)<1−δ_vr` (δ_vr=0.10); **(b) Half-life** from AR(1) on `d`:
finite, `0<HL≤HL_max=48` exec-bars; **(c) Hurst-DFA** `H<0.5−δ_h` (δ_h=0.05). ADF/KPSS dropped
(methods-catalog "avoid"; parametric). **Extreme probe:** `|z_t|≥z*`, `z*=2.0` (fixed probe, sensitivity
§8, not a tuned lever). **Entry event** = exec bar with screen-pass AND `|z_t|≥z*`, decided at exec `Open`,
`≤ t-1` only.

**Favourable excursion `θ_i`:** signed excursion **toward the anchor**, real-price, horizon `H=24` exec-bars
from exec open, ATR units (`ATR_{≤t-1}`, 14 exec-bars). MFE-style max favourable move toward `a` within `H`.
Zero conditioned events in a cell → **UNPOWERED** (not a zero pass). Tailmass = `#{θ_i≥τ}/n_events`, τ=1.0 ATR.

## 5. Estimand, control, statistics, multiplicity

- **Estimand θ (two predeclared endpoints, `availability_gate._stat_1d`):** **(L)** median `θ`; **(S)**
  upper-**tailmass**. L-11: a tail-only admit is **flagged long-tail** (CF-VOLEXP precedent), not sold as a
  location edge.
- **Matched-random control (EXP-081/047 clone, per cell):** within-instrument, same exec domain, **matched
  count** + **matched regime** (control timestamps drawn from the conditioned events' own ATR-tercile
  membership, `xen.vol_regime`, `≤ t-1`). Control excursion measured identically (same anchor, `H`,
  fade-direction from the control's own `d` sign). Isolates conditioning vs random timing.
- **Δ + uncertainty (`availability_gate.cell_se`, `_moving_block_resamples`):** `Δ̂=θ(cond)−θ(ctrl)`;
  **moving-block bootstrap** on conditioned excursions (serial dependence), iid on control; per-cell
  `ci_low`. **Block-permute the excursion series, never rotate the price path** (L-07).
- **Multiplicity — cross-axis Holm (the 240-cell control, `availability_gate` G-019 pattern):** per
  `(series,domain)` **axis** (≤16 instrument-cells), compute the **max-statistic** permuted-axis admission
  at the realized cell count (shuffle screen-pass labels, recompute Δ, count exceedances). **Holm across the
  15 series×domain axes.** Per-stratum Δ still emitted (L-03); the axis max-stat is the admission unit, the
  per-stratum pattern is the read. **Wilson** CI on within-axis pass-rate.
- **MDE / power:** per-cell MDE = smallest Δ the block-bootstrap resolves at `n_events`; a cell with
  `MDE>Δ*` or `n_events<N_min` or a degenerate anchor fit → **UNPOWERED** (reported, never *failed* —
  power-aware).

## 6. Leak tripwire (mandatory; analysis-only still ships one)

Two future-destroying controls; **both must collapse Δ to ≈0 within CI** on any admitting axis:
1. **Conditioning-label permutation** — permute which timestamps are "screen-pass"; Δ-over-random must vanish.
2. **Forward-excursion time-reversal** — measure the excursion window backward; a causal reversion edge must
   not survive.
Δ surviving **either** ⇒ artifact of the excursion/labelling construction ⇒ **REJECT** (leak), not admit.
Audit re-runs both on every admitting cell.

## 7. Interpretation criteria (predeclared, frozen before outcome contact)

Effect floor **`Δ*=0.10 ATR`**; per-cell `N_min=100` events; an axis is **eligible** only with ≥4 powered
instrument-cells; within-axis majority = **≥50% of powered cells**.

- **ADMIT-TO-EXPLORE (family):** ≥1 (series×domain) axis clears cross-axis-Holm permuted-axis admission
  **and** ≥50% of that axis's powered cells show `Δ̂≥Δ*` with block-bootstrap `ci_low>0` — on **either** (L)
  or (S) endpoint (S-only ⇒ long-tail flag) — **and both leak tripwires collapse Δ** on the admitting cells.
  ⇒ the admitting (series,domain) is the concretization target for a *new dated D0* (still 0 counted reads).
- **EXONERATE (family):** no axis admitted under Holm → **none** of the 5 constructions × 3 domains confers
  availability beyond matched-random. Honest full closure; family retained in registry (never deleted).
- **INCONCLUSIVE:** admission borderline / >½ of axes ineligible-UNPOWERED / leak-ambiguous. No goalpost
  move; re-scope only as a new experiment.

No metric re-defined after results (inverted-inference predeclaration).

## 8. Robustness / sensitivity (disclosure, non-binding)

- **Drop-one-leg** MR-screen sensitivity (VR/HL/Hurst individually + pairwise): admission leg-dependence.
- **`z*`** {1.5,2.0,2.5}, **`W_a`** {10,20,40}: verdict-invariance band. Frozen probe `z*=2.0`, `W_a=20`.
- **Recent-third** (most-recent 1/3 of TRAIN): regime-shift fragility.
- **S4 φ-stability** and **S5 β-stability** diagnostics (share of UNPOWERED cells from degenerate fits).

## 9. Complexity budget (operator-approved expansion, 2026-07-01)

- **Stat tests (3 types):** (1) block-bootstrap Δ CI per cell; (2) cross-axis-Holm permuted-axis admission;
  (3) leak-tripwire collapse. ✓
- **Plots (~6):** (P1) per-series Δ heatmaps over domain×instrument (small multiples, 5 panels); (P2)
  cross-axis admission summary (15 axes: max-stat vs null band); (P3) shape/tailmass Δ map; (P4)
  leak-tripwire before/after Δ; (P5) MDE + powered/UNPOWERED map; (P6) representative cond-vs-control
  excursion distributions. ✓ (operator-approved)
- **Modules (2):** reuse `xen.domain_bars`, `xen.bar_aggregator`, `xen.availability_gate`
  (Δ/SE/perm-null/block-bootstrap/median+tailmass/cross-axis Holm), `xen.vol_regime` (ATR terciles).
  **New:** `xen.cross_domain_mr` (5 anchor constructors S1–S5 + OU/AR(1) fit + class-basket/rolling-β
  builder + robust-z + 3-leg MR screen, all `≤ t-1`). Plus the EXP-008 script. ✓

## 10. Implementation safety constraints (for experiment-developer)

- **Split = TRAIN only.** Per file, sorted `CloseTime`: analysis set = first 70% of the file; within it,
  TRAIN = first 70% of the analysis set (≈49% of the file) and TEST = the last 30% of the analysis set
  (≈21%); global holdout = the final 30% of the file. **EXP-008 uses only the TRAIN slice.** The TEST band is
  untouched — reserved for a future counted read (cap 2/stratum); the global holdout is never loaded. This
  screen touches neither TEST nor holdout.
- **Slice TRAIN per file *before* any cross-instrument operation.** For S5, each instrument is TRAIN-sliced
  on its **own** timeline first, then class-mates are timestamp-aligned on the intersection of TRAIN ranges —
  so no instrument's TEST-band / holdout rows can leak into another instrument's basket, β, or deviation.
  Same rule for any regime/tercile stat drawn across instruments.
- Every `≤ t-1` boundary explicit: anchor from higher-domain bars with `CloseTime ≤` exec `OpenTime`;
  MAD/std, VR, HL, Hurst, ATR, OU AR(1), S5 β on trailing windows ending `t-1`; excursion strictly forward
  of exec `Open`. **No forming-bar OHLC.**
- **S5 cross-instrument:** align class-mates by timestamp (never bar index); basket over available mates at
  each exec `CloseTime`; missing-mate handling explicit (drop-to-available, min 1 mate else UNPOWERED).
- **S4 OU:** guard `0<φ<1` (mean-reverting AR(1)); non-stationary/explosive fit → UNPOWERED cell, no NaN
  propagation.
- Matched-regime control draws seed-fixed, reproducible; bounded resamples (block bootstrap `n_boot≥10 000`;
  permuted-axis `n_perm` per `availability_gate` default). `tqdm` over the 240 (cell) loop.
- Explicit NaN handling in warmup (`W_a`/`W_s`/`W_z` unfilled → event=False, not NaN). Deterministic; no
  import side effects. Vectorize excursion/bootstrap via NumPy/`availability_gate`; keep the sequential
  `≤ t-1` anchor/screen computation explicit and causal (no look-ahead vectorization shortcut).
- Real-price outcomes only; align by timestamp, never bar index.

## 11. Registry / governance disposition

CF-MR-003 `REGISTERED → SCREENED-{ADMIT|EXONERATE|INCONCLUSIVE}` on completion. 0 slots, 0 counted reads,
holdout sealed. Not used to tune the frozen referee (L-12). Multiplicity-registry: record this availability
read as **15 series×domain axes under cross-axis Holm** (realized cell counts + per-axis permuted-axis
outcomes); refuted/admitted axes all retained.

---

## GATE: APPROVE (pre-exec, orchestrator, 2026-07-01; re-frozen after operator scope expansion)

Re-checked against `references/governance-constraints.md` + Phase-002 checkpoint after the operator-directed
expansion to 5 anchor series × 3 domain pairs (pre-execution; **no results contact — not a goalpost move**).
All binding checks pass: single falsifiable family-availability question with anchor-series/domain as
declared exploration axes (§1); analysis-only justified (§2); holdout sealed + TRAIN-only (§3/§10);
per-stratum non-pooled endpoints, pooled = disclosure (L-03, §3/§5); shape-aware tailmass endpoint (L-11,
§5); block-bootstrap on excursions not price-path rotation (L-07, §5); **240-cell multiplicity controlled by
cross-axis Holm over 15 series×domain axes with max-statistic permuted-axis admission** (G-019 pattern,
`availability_gate`, §5) — the correct control for the worst multiplicity offender (methodology-canon);
leak tripwires shipped, both must collapse Δ (§6); ADF/KPSS dropped for VR/HL/Hurst-DFA (§4); OU included as
a fair parametric contender with its stationarity guard + UNPOWERED handling (§4/§10); predeclared frozen
criteria + sensitivity band (§7/§8); complexity budget **operator-approved** (§9). Registry precondition met
(CF-MR-003 REGISTERED; 0 counted TEST reads). Power-aware UNPOWERED reporting (never auto-fail) applied to
S5 lone-class + degenerate OU/β fits.

**Honest-prior note (non-blocking):** family opened against the terminal-branch prior but given a fair
full-space test by operator design; the predeclared EXONERATE path remains the expected outcome and is a
valid, cheap family-closure result. → **Stage 2 (Implement).**

---

## AMENDMENT A1 — drop the Hurst-DFA leg (2026-07-01, operator-ratified; amend-in-place + rerun)

**Trigger.** The first EXP-008 run (3-leg screen `VR ∧ half-life ∧ Hurst-DFA<0.45`) returned
**INCONCLUSIVE (underpowered)** — 0/15 axes eligible, 0 powered cells, max 18 events/cell (N_min=100).
Verdict forensics traced the cause to a **single pathological leg**: the Hurst leg (drop-one disclosure —
every leg-combo *with* Hurst → 0/240 powered cells; *without* it, `VR+HL` → 216/240 powered).

**Operator ruling (2026-07-01).** No inference about CF-MR-003 is possible — the screen never reached
analyzable power; the failure is a **screening-design pathology**, not evidence against the hypothesis.
This is handled as a **dated amendment + rerun in place** (not a new experiment): the as-run 3-leg
screen adds no value beyond documenting the unrealistic Hurst expectation. CF-MR-003 stays REGISTERED and
**untested** on this vehicle until the corrected screen runs.

**Forensic post-mortem** (`code/hurst_forensics.py` → `results/hurst_forensics.json`,
`plots/F_hurst_forensics.png`). Why the Hurst leg fails — **both** causes:
- **Wrong object (proximate).** DFA integrates its input, so on the deviation **level** it scores the
  integrated OU process → known-OU `H_level ≈ 1.0–1.44` (grows with half-life); real S4_OU deviations
  `H_level ≈ 1.08–1.28`. `Hurst-on-levels < 0.45` is **structurally impossible** → the 0/240.
- **Estimator unfit for the setting (deeper).** Even corrected to **increments**, `H_incr < 0.45` fires
  only for extreme reversion (HL≈2 bars → 0.35) and needs windows ≥400 bars; at the empirically-fitted
  HL≈4–7 bars and `W_s=200`, `H_incr ≈ 0.46–0.53 ≈ 0.5` (real: 5–8% of windows pass). DFA-Hurst measures
  long-range/increment persistence — ≈neutral (0.5) for moderate OU — **not** reversion-to-a-level. VR
  and half-life measure reversion-to-a-level directly, which is the screen's actual intent.

**Change (single leg dropped; everything else frozen unchanged).** The MR selector (§4) becomes the
**2-leg conjunction `VR(q=4)<0.90 ∧ half-life∈(0,48]`**, `≤ t-1`, on the deviation series. The extreme
probe (`|z|≥2.0`), the 5 anchor series, 3 domain pairs, endpoints (median + upper-tailmass), matched-
random regime control, cross-axis Holm admission, both leak tripwires, effect floor Δ*=0.10 ATR,
`N_min=100`, and all §5–§10 machinery are **unchanged**. `xen.cross_domain_mr.hurst_dfa` /`screen_legs`
are retained for the forensic record and §8 leg-sensitivity disclosure; Hurst is not in the binding
conjunction. No results-driven threshold change beyond removing the refuted leg (not a goalpost move —
the leg is removed on a *mechanism* proof it cannot fire, established before the amended screen's outcome
is read).

**Amend-in-place procedure (L-10).** Contaminated 3-leg artifacts hard-deleted (`results/per_cell.parquet`,
`axis_results.json`, `verdict.json`, `run.log`; `plots/P1–P6`); `results/dropone_sensitivity.json` +
`results/hurst_forensics.json` + `plots/F_hurst_forensics.png` **retained** as the amendment's supporting
forensics; `audit.md` / `report.md` regenerated. Full rerun under the amended 2-leg screen. 0 slots / 0
counted TEST reads; holdout sealed; referee untouched (L-12).

**GATE: APPROVE (amendment pre-exec, orchestrator, 2026-07-01).** Single refuted leg removed on a
mechanism proof (forensic, pre-outcome); registry precondition still met (CF-MR-003 REGISTERED, 0 counted
reads); all binding checks from the original gate still hold. → **rerun.**

**A1 rerun outcome (2-leg VR∧HL).** Screen now powered (13/15 axes eligible, events median 762 / max
7180). Verdict `adjudicate` → **EXONERATE** (0 axes clear the §7 ADMIT bar: Holm max-stat flags 4 axes on
the tail endpoint — S5_SPREAD ×3 p≈0.003–0.005, S1_CENTER|1D/1h p=0.012 — but all at negligible/negative
effect, 0% of cells clear Δ*=0.10; median endpoint underpowered at the 0.10-ATR floor with ≈0/mixed-sign
point estimates). **This EXONERATE is HELD, not booked — see Amendment A2.**

---

## AMENDMENT A2 — evaluation-vehicle mismatch indicated; EXONERATE held; native re-screen = EXP-009 (2026-07-01)

**Trigger (operator, 2026-07-01).** The A1 EXONERATE rests on an evaluation vehicle **inherited from the
price-geometry family** and never re-derived for mean-reversion: (a) the read metric is a **fixed-horizon
signed-MFE toward the anchor**, and (b) the null is **regime-matched random *timing***. Both are non-native
to an extreme-entry, target-reverting strategy. The operator challenged whether the EXONERATE is a family
reading or a vehicle artifact — correctly requiring this be **tested, not asserted**.

**Vehicle diagnostic** (`code/vehicle_diagnostic.py` → `results/vehicle_diagnostic.json`,
`plots/V_vehicle_diagnostic.png`; analysis-only, TRAIN, 0 reads; 120 cells over S1/S4/S5 × 3 pairs × 16
inst). Conditioned vs two controls — **C1** regime-matched random timing (current), **C2**
**dislocation-matched** (random among `|z|≥2` bars, no screen) — on three metrics:

| Metric | Δ under C1 (current null) | Δ under C2 (dislocation-matched null) |
|---|---|---|
| MFE-toward (current vehicle) | −0.037, CI [−0.092,+0.025] — blind | +0.006, CI [−0.031,+0.024] — **blind** |
| fraction-recovered | −0.175, CI [−0.219,−0.149] — negative | **+0.027, CI [+0.013,+0.031] — separates** |
| anchor-hit rate | −0.196, CI [−0.212,−0.169] — negative | **+0.029, CI [+0.020,+0.037] — separates** (82% cells+) |

**Finding — masking INDICATED (reactive diagnostic, not pre-registered).** Under the dislocation-matched null the native target metrics separate
positively (anchor-hit **+2.9 pp**, fraction-recovered **+2.7 pp**, CIs exclude 0) while **MFE stays within
0** — the MFE metric cannot see the reversion the native metrics resolve. Against the current
random-timing null (C1), near-anchor bars trivially "revert," so conditioned extremes read **negative** on
native metrics. Both prior EXP-008 verdicts (3-leg INCONCLUSIVE, 2-leg EXONERATE) are **vehicle
artifacts**, not family readings. **Calibration (honest):** the native separation is **small** (≈+2.9 pp
hit), statistically resolved at the cell aggregate but **economically modest and not cost-tested**, on
close-based deviations; a residual `|z|`-depth confound remains (native design must dislocation-**bin**).

**Disposition.** EXP-008 is closed as a **METHODOLOGY FINDING** (L-13). The A1 EXONERATE is **HELD, not
booked** as a CF-MR-003 verdict. CF-MR-003 stays `REGISTERED` with **preliminary positive native
evidence**. The retained deliverables are the Hurst forensic (A1), the vehicle diagnostic (A2), and L-13.
No family closure; 0 slots / 0 counted reads; holdout sealed.

**Native re-screen → EXP-009 (new D0, operator-gated).** Estimand becomes **target-based** (anchor-hit
rate; time-to-anchor scaled by the fitted half-life; fraction-of-dislocation recovered; deferred
limit-at-anchor real-price P&L) against a **dislocation-binned** null, per stratum, with leak tripwires.
That is the native CF-MR-003 screen; EXP-008's availability/MFE/random-timing vehicle is retired for this
family.