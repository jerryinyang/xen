# CF-MR-003 — Cross-Domain Mean-Reversion (deviation-from-higher-domain-anchor)

**Status:** `RETIRED — SCREENED-ADMIT → CONC-1 NOT-TRADABLE (family CONCLUDED, Phase-003 retrospective
2026-07-01)` (T1 exec-1h UNPOWERED EXP-010 + T2 exec-15m POWERED EXP-012, net, TRAIN; audit PASS, 0
Critical). Availability real, net-nil at both horizons → retired; retained in registry, re-open only with a
cheaper capture mechanism or lower-cost universe (not a re-parameterization; no P-02 rescue). Full arc:
`docs/experiments-docs/checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/retrospective.md`. **1 candidate slot consumed**
(tradability exploration; T2 opened **0 new slots**); 0 counted TEST reads; holdout sealed; referee untouched (L-12).
**T2 (EXP-012) result:** the same form-2 limit-at-anchor fade on the **24 EXP-009 exec-15m admits** (T2a 14
S3_DETREND single-symbol + T2b 10 S5_SPREAD basket, one Holm family) under the **frozen 15m referee** is **24/24
powered** (reversion episodes 70–390 ≥ 15m `min_state_count=25` — the extra 15m bars clear the higher floor), **0/24
admit**, every CI_lower ≤ 0 (net −0.77…+0.04 bps/active). This is the **powered** definitive close the LOW prior
predicted (mechanism: shorter-horizon reversion earns less against the **same** round-trip cost). **EXP-010 gate-debt
DISCHARGED:** F-1 vehicle fidelity now PASS all 24 (z_corr 1.00, Jaccard 0.97–0.99 — the S3 single-symbol path has no
basket carry-forward); F-2 leak-resistance now tested — planted-positive detected 24/24 (power real) + valid live
phase-shifted-basket future-destroy CLEAN (0 survivors). *(Raw-script `REJECT_LEAK` was a false trip from a
mean-invariant Python permutation-destroy → superseded by `verdict_corrected.json`; no re-run, verdict identical.)*
**⇒ Availability (EXP-009 SCREENED-ADMIT) does NOT survive to net at either the 1h or 15m execution horizon.**
Family **retained** (never deleted), terminal-branch prior reinforced; with sister CF-MR-002 EXONERATED, CF-MR-003
tradability is closed. CONC-2+ axis sweep is **moot** (no tradable CONC-1 base; no P-02 dead-entry rescue).
**Member-set note (substrate override):** EXP-009's "S5_SPREAD 20 admits" double-counts the exec-1h 1D/4h-anchor
label → **15 distinct** S5 strategies (5 exec-1h + 10 exec-15m); T2a adds the 14 S3_DETREND exec-15m cells.
*(T1 detail retained: 5 distinct S5 exec-1h admits, exec-grid-β in-engine, 0/5 powered — episode sparsity 10–32 <
1h floor 20; net −0.70…+0.10, CIs cover 0; read UNPOWERED, not a positive refutation.)*

**Prior status:** `SCREENED-ADMIT` (per-stratum, native vehicle — EXP-009, 2026-07-01; audit PASS, 0 Critical).
The native re-screen (target-based: anchor-hit / fraction-recovered / time-to-anchor; event-specific
half-life horizon; **screen-fail dislocation-matched null**) records **36 leak-clean per-stratum
reversion-to-anchor passes** — **S5_SPREAD 20** (FX majors: EURUSD/USDJPY/NZDUSD/USDCHF/GBPUSD), **S3_DETREND
14**, **S4_OU 2**; label-permutation collapses on all. Pervasive positive hits across all 5 series (S1/S2
precision-limited, +5–8pp point estimates, UNPOWERED_HINT). Robust on S5_SPREAD (18–20 passes across
horizon/floor/z-edges), moderate on S3_DETREND (8–16); recent-third unconfirmed (power). **Availability, not
tradability** — concretization = the family's **form-2 limit-at-anchor (target=mean)** in a separate
price-primary experiment (new D0). 0 slots, 0 counted TEST reads, holdout sealed, referee untouched (L-12).
Prior: **EXP-008 METHODOLOGY FINDING (2026-07-01); NOT exonerated, NOT admitted.** The availability screen used a vehicle **inherited from the price-geometry family** and never
re-derived for MR: fixed-horizon signed-MFE-toward-anchor + Δ-over-regime-matched-**random-timing**. Arc:
3-leg screen → INCONCLUSIVE (inherited `Hurst-DFA<0.45` leg structurally unsatisfiable on deviation
*levels* — forensic A1); 2-leg VR∧HL → EXONERATE; **vehicle diagnostic (A2) indicates EXONERATE is
vehicle-dependent** (reactive diagnostic, not pre-registered) — under a **dislocation-matched** null the native target metrics separate (anchor-hit
**+2.9 pp** CI[+2.0,+3.7], fraction-recovered **+2.7 pp** CI[+1.3,+3.1], 82% cells+) while **MFE is blind**;
the random-timing null reads spuriously negative on near-anchor bars. **EXONERATE HELD, not booked.** The
family carries **preliminary positive native evidence** (small, ≈+2.9 pp, not cost-tested) → **native
re-screen = EXP-009** (new D0: target-based estimands — anchor-hit / time-to-anchor vs half-life /
fraction-recovered / deferred limit-at-anchor P&L — against a dislocation-**binned** null). See L-13; the
2-leg VR∧HL selector carries forward, the MFE/random-timing vehicle is retired for this family. Prior:
`REGISTERED` (2026-07-01) — operator-ratified open at Chapter-02 Phase 002 G0.
0 candidate slots consumed, 0 counted TEST reads, global holdout sealed. Availability-screen-first
(analysis-only); never used to tune the frozen referee (L-12).

## Why this is not a re-parameterization (pitfall re-open test)

CF-MR-002 (EXONERATED, net-neg 34/34) faded **RSI(2) unconditionally on raw `Close`**. The programme's
terminal-branch note (Phase-001 retrospective §6) declares price-derived axes screened/closed. Re-opening
requires **a new mechanism or new information source**, not a re-parameterization (pitfalls P-01/P-02).
CF-MR-003's distinguishing information, operator-ratified 2026-07-01:

1. **Conditioning IS the entry information, not a downstream rescue.** Entry fires only where a
   **cross-domain deviation series is characterised mean-reverting first** (the screening framework:
   variance-ratio / half-life / Hurst-DFA at `≤ t-1`). This is the entry's information source, distinct
   from P-02 (tuning exits/conditioning to rescue a *dead* entry) — the dead entry there was an
   unconditional price-geometry pattern; here the MR-characterisation is the availability selector itself.
2. **Cross-domain, derived anchor — never tested.** The anchor is a **higher-domain robust-detrended
   series** (rolling median / LOESS); the traded quantity is the **lower-domain deviation from it**. Neither
   the cross-domain structure nor a screened-MR-derived anchor has been screened. CF-MR-002 was
   single-domain raw-price.

**Honest prior (recorded):** LOW. Same broad reversion mechanism as the exonerated CF-MR-002; the burden
is on the screen to show conditional availability beyond a matched-random control. The single-series ×
magnitude cell of the availability 2×2 is only "tail-only hint" (CF-VOLEXP-001), not a positive result.

## Thesis (one falsifiable sentence)

*Entries conditioned on a cross-domain deviation series characterised mean-reverting at `≤ t-1` produce a
favourable reversion excursion (deviation collapse toward the higher-domain anchor) exceeding a matched-
random control on TRAIN — or they do not (honest prior: they do not).*

## First-branch definitions (ratified forks, Phase-002 G0 2026-07-01)

- **`/SERIES` anchor (ratified: cross-domain deviation; expanded to a 5-series axis 2026-07-01).** Operator
  directed a **fair full-space** availability screen (this rung gates the whole family): **5 independent
  anchor constructions**, not one — **S1 CENTER** (rolling-median Close, single-dim), **S2 RANGE** (Donchian
  midline, range-aware), **S3 DETREND** (rolling-OLS trendline residual, derived), **S4 OU**
  (Ornstein-Uhlenbeck equilibrium θ on HLC3, engineered multi-dim source), **S5 SPREAD** (rolling-β
  asset-class-basket, cross-instrument). All higher-domain, `d_t = price − a_t`, all `≤ t-1`. Full defs +
  windows in `python/experiments/EXP-008/design.md §4`.
- **Domain-pair axis (ratified 3 pairs 2026-07-01):** **4h/1h, 4h/15m, 1D/1h** (anchor:exec 4:1/16:1/24:1).
- **MR screen (the availability selector), identical across S1–S5.** Applied to `d_t` at `≤ t-1`:
  **variance-ratio + half-life + Hurst-DFA** (conjunction). ADF/KPSS **dropped** (methods-catalog "avoid";
  parametric). Extreme probe `|robust-z| ≥ z*=2.0`. Candidate-blind, TRAIN-only (EXP-008 §4).
- **Multiplicity:** 16 inst × 5 series × 3 pairs = up to 240 cells, controlled by **cross-axis Holm over 15
  series×domain axes** (max-statistic permuted-axis admission, `availability_gate` G-019 pattern).
- **Execution machinery `/DIRECTION /REENTRY /TARGET /EXIT` — DEFERRED.** Not concretized until availability
  clears. Building the limit/exit/reentry stack first = the chapter's documented "measure availability last"
  mistake (methodology-canon). Availability screen is analysis-only, real-price excursion vs matched-random.

## Hypotheses (EXP-IDs assigned at promotion)

- `CF-MR-003/HYP-001` — **Availability screen (EXP-008).** Does MR-screen-conditioned entry produce a
  reversion excursion beyond a matched-random, matched-count, matched-regime control on TRAIN? 0 slots/reads,
  analysis-only. Admit-to-explore / exonerate. *This is the only sanctioned near-term read.*
- (Strategy concretization, cost/net tradability, counted TEST reads, deployment — only on a TRAIN
  availability admit, each at its own dated D0 + slot decision.)

## Exploration axes (registered 2026-07-01, post-ADMIT)

Full family surface from the operator dumps (`.ignore/dumps/0-phase002-thoughts.md`,
`0-mean-reversion-screening-framework.md`), registered now that the availability read ADMITTED (EXP-009).
Each axis is a registered branch; each concretization step needs its **own dated D0 + slot decision** and,
for any tradability/net claim, a **price-primary in-engine** run (L-01) adjudicated under the frozen referee
(L-12). Refuted/deferred branches are retained, never deleted. Status legend: SCREENED (availability read
done) · OPEN (registered, next up) · DEFERRED (registered, later) · REFUTED/AVOID (with mechanism).

### A. MR-screening-framework axis (the selector stack)

The dump's stack: robust-detrend → lag-1 autocorr → variance-ratio → ADF → KPSS → half-life; Hurst-DFA as a
modern alternative (dump flags it *noisy on short samples*); dump also flags *avoid OU as a screen*.

| Stage / leg | Status | Note |
|---|---|---|
| Variance-ratio (`VR(4)<0.90`) | **SCREENED — IN USE** | binding selector leg (EXP-008 A1 / EXP-009). |
| AR(1) half-life (`0<HL≤48`) | **SCREENED — IN USE** | binding selector leg; also sets the native horizon `H_i=3·HL_i` (EXP-009). |
| Hurst-DFA (`<0.45` on levels) | **REFUTED (Amendment A1)** | structurally unsatisfiable on deviation *levels* (DFA integrates → OU-level H≈1.0–1.4); the dump's "noisy on short samples" caveat confirmed. Re-open only on **increments**, power-validated first. |
| ADF / KPSS | **AVOID (dropped)** | parametric (methods-catalog "avoid"); moderate cost. Re-open only if a non-parametric leg is shown insufficient. |
| Lag-1 autocorrelation | **DEFERRED** | cheap momentum-eliminator from the dump stack; not yet added (VR∧HL already separate). Candidate extra leg. |
| Robust detrending pre-stage (rolling median / LOESS) | **PARTIAL** | S1 CENTER = rolling median, S3 DETREND = rolling-OLS trendline residual (both anchor constructions). LOESS variant DEFERRED. |
| OU characterisation | **CHARACTERISATION-ONLY** | per the dump, OU used to *characterise* (half-life/decay), **not** to screen; S4 OU-as-anchor was sparse (EXP-009). |

### B. `/SERIES` — anchor-series axis (the traded quantity; must be full-bar-range-aware, higher-domain, reversible)

| Series | Status (EXP-009 native) |
|---|---|
| S3 DETREND (rolling-OLS-trendline residual) | **SCREENED-ADMIT** — 14 leak-clean per-stratum passes (moderate robustness). |
| S5 SPREAD (rolling-β asset-class basket, cross-instrument) | **SCREENED-ADMIT** — 20 passes, FX-major-concentrated, **robust** (18–20 across sweep). Headline. |
| S4 OU (Ornstein-Uhlenbeck equilibrium on HLC3) | **SCREENED-WEAK** — 2 passes (sparse fits; OU-as-source, not screen). |
| S1 CENTER (rolling median) / S2 RANGE (Donchian midline) | **SCREENED-HINT** — 0 resolved but +5–8pp positive hints, precision-limited (fewer extremes from trend-inflated median-MAD z). Re-open with a less-trend-contaminated z / higher-n (OPEN). |
| New anchor constructions | **OPEN** — any full-bar-range-aware, higher-domain, reversible series (dump constraint). |

### C. `/EXTREME` — extreme-detection method (`≤ t-1`)

Options (dump): **quantiles/percentiles**, **z-score (mean/std)**, **robust z-score (median/MAD)**.
Used: robust-z (median/MAD) for S1/S2/S4, std-z for S3/S5, probe `|z|≥2.0`. **DEFERRED** systematic sweep
(quantile vs z vs robust-z; `z*` band) — a registered branch.

### D. `/DIRECTION` — entry direction

Dump: **primarily the extreme reached**, secondarily anchor-timeframe **trend strength + regime**. Used:
fade-toward-anchor (extreme-primary). **DEFERRED** — the trend/regime secondary conditioner is an OPEN branch.

### E. Execution machinery — DEFERRED to price-primary concretization (in-engine, L-01)

| Axis | Options (dump) | Status |
|---|---|---|
| Entry mechanics | **strictly limit orders**, precalc on `≤ t-1` anchor data, refreshed per anchor bar, **live intra-bar fill** | **DEFERRED** — EXP-009 modelled only target reachability, not the live-limit entry fill. |
| `/REENTRY` | none / allow / **extend** (multiple prices at deeper extremes) | **DEFERRED** |
| `/TARGET` | reversion-to-**mean** / reversion-to-**opposite-extreme** | **mean SCREENED** (EXP-009 anchor-hit); opposite-extreme **DEFERRED**. |
| `/EXIT` | form-1 natural (event-driven on anchor reversion) · form-2 precalc favourable limit · `/EXIT` plane (other) | **DEFERRED** — form-2-limit-at-mean is the natural first concretization. |

## Concretization roadmap (post-ADMIT; each step = own dated D0 + slot; price-primary where an edge/P&L is generated)

1. **CONC-1 T1 DONE (EXP-010, 2026-07-01) — NOT-TRADABLE (UNPOWERED):** form-2 **limit-at-anchor, `/TARGET`=mean**,
   `/DIRECTION`=fade, `/REENTRY`=none, live-limit entries on `≤ t-1` anchor — run **in cTrader** on the **5 distinct
   S5_SPREAD exec-1h** admits (exec-grid-β anchor in-engine), binding-leg cost, frozen 1h referee. **0/5 powered,
   0/5 admit** (episode sparsity < min_state 20); availability does not survive to net. 1 slot consumed; 0 counted
   reads; holdout sealed.
1b. **CONC-1 T2 DONE (EXP-012, 2026-07-01) — NOT-TRADABLE (POWERED); TRADABILITY CLOSED:** the same form-2
   limit-at-anchor fade on the **24 exec-15m admits** (T2a 14 S3_DETREND single-symbol + T2b 10 S5_SPREAD basket),
   frozen **15m** referee (EXP-011), one Holm family. **24/24 powered** (episodes 70–390 ≥ 15m floor 25 — extra
   bars clear the higher floor), **0/24 admit**, every CI_low ≤ 0 (net −0.77…+0.04 bps/active) — the **powered**
   close the LOW prior predicted. **EXP-010 gate-debt discharged:** F-1 vehicle fidelity PASS all 24 (1.00 /
   0.97–0.99); F-2 tested — plant 24/24 + valid live phase-shift future-destroy clean. (Raw `REJECT_LEAK` = false
   trip from mean-invariant permutation-destroy; superseded, no re-run.) **⇒ availability does not survive to net
   at 1h or 15m.** 0 new slots, 0 counted reads, holdout sealed, referee untouched (L-12).
2. **CONC-2+:** ~~on a tradable CONC-1, sweep the deferred axes~~ — **MOOT (2026-07-01):** no tradable CONC-1
   base at either horizon → the axis sweep is not opened (no P-02 dead-entry rescue). Retained for the record.
3. **Robustness debt (carry):** constant-n TRAIN-thirds test (resolve the recent-third power gap); S1/S2
   less-trend-contaminated-z re-screen.

## Referee note (binding)

If/when CF-MR-003 reaches a tradability read, it is adjudicated under the **frozen** renewed referee
(§10.3a q\*=0.75 + E6 `referee_pstar.gate_stack_pstar`, Phase-001 E5/E6). CF-MR-003 must **never** be used
to tune the referee (L-12).

## Exclusions / deferred

No strategy machinery, no cost/net-tradability claim, no in-engine run, no counted TEST read, no holdout
release in HYP-001. Each subsequent step needs its own dated D0 + slot decision.

## Discipline

Real-price excursion outcomes only; final-30% global holdout never read; matched-random control per
methodology-canon (matched count + regime, within-instrument); per-stratum verdicts (no pool-as-verdict,
L-03); availability measured **first** (methodology-canon). All outcomes retained, never deleted.
