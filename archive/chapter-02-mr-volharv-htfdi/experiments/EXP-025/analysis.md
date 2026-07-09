# Data Analysis: EXP-025 — CF-HTFDI-001/HYP-A (HTF-DI-confirmed breakout, 22 symbols, 1h/5min)

Analyst: data-analyst skill, 2026-07-09. Scope: **Stage T1 TRAIN only** (20 X×H confs × 22
symbols = 440 cells) + controls (CTRL-REF-RANDOM, CTRL-NULLSENT). TEST rows quarantined
(never loaded past the per-symbol TRAIN cut); battery/tripwire/T2 stages not run — see §6.
All numbers from `analysis_code/` scripts over raw emissions; no experiment-local
accounting; canonical `xen.evaluation` estimators throughout.

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all cells blocking_pass) | **PASS** | `results/estimand_validation_EXP-025-*.json` — 22/22 emissions `blocking_pass: true` (20 T1 confs + ref + sent), reconciliation + schema + fence OK |
| Provenance trace (verdict-bearing columns ≤ t−1) | **PASS** | Signal: `HtfDiBreakoutModel.cs` decision on closed bar t, fill at Open(t+1); HTF gate hard assert `snapshot.CloseTime > bar.OpenTime → throw` (`HtfDiBreakoutModel.cs:148`); QA golden trace byte-consistent over 5,486 TRAIN trades; `HtfBarCloseTime < EntryTime` verified per emitted trade at QA |
| Leak tripwire | **NOT RUN at T1** — phase-shift stage is design §6 post-selection (survivor cells). Zero cells qualified, so no verdict-bearing positive exists that would require the collapse check. If the operator elevates any disclosure cell, the +60-bar shift run is mandatory first |
| Holdout untouched | **PASS** | Engine `AnalysisEndUtc` fence (70% cut, per `run_metadata.json`); analyst TRAIN cut at 70%×70% of canonical m1 rows (`results/train_cuts.json`); TEST rows dropped unread in `build_cells.py`; final-30% never loaded |
| Price-primary (engine emission under fence) | **PASS** | All trades from `data/strategy_runs/EXP-025-*/htfdi_*/cis_trades.parquet` (cTrader StrategyHost); no Python backtest anywhere in the loop |
| No experiment-local accounting defs | **PASS** | `code/` is C# refs + confs notes only (QA verified); analyst estimators = `xen.evaluation` |

Dataset: 2,432,812 non-censored TRAIN trades across 440 cells (`results/cell_counts.csv`);
per-symbol TRAIN n ≈ 48k (STOXX50) – 141k (BTCUSD). Censored open-at-end legs excluded.

## 2. Question list

1. Reconcile per-leg totals? → ANSWERED §1 (gate).
2. P&L object = design estimand? → ANSWERED: per-trade open-to-open leg, 1 leg = 1 episode, one position at a time; matches §2 OBJECT-IDENTITY.
3. Per-leg net distribution per cell? → ANSWERED §3/§4 + focus-cell tails (probes.py): q01 ≈ −180 to −210 bps, q99 ≈ +170 to +230 bps at h48; median ≈ 0. Money comes from tiny mean asymmetry on a ±100 bps-scale distribution.
4. Episode anatomy? → N/A (single-leg episodes by construction).
5. Concentration? → ANSWERED §4: focus cells survive top-5 removal (e.g. HK50 x2h48: 3.18 → 2.32 bps) but not top-20 (→ 0.61); no single-outlier artifact, but thin.
6. Per-year stability? → ANSWERED §4: unstable (HK50 x2h48: −2.4 / +8.0 / +3.8 bps by year; US2000 x8h48 flips sign in 2023).
7. Per-stratum structure? → ANSWERED §3/§4: positives are equity-index-only; all 10 FX symbols ≤ 0 in every one of their 20 cells.
8. Occupancy/physicality? → ANSWERED (partial): one-position-at-a-time with dense signals ⇒ near-continuous occupancy at small H (trades/cell up to 13k on ~120k TRAIN bars at h12 ⇒ in-market most of the time). This is a drift-exposed always-in rotation, not a sparse event strategy. Detailed exposure metrics not computed (no qualifying cell to carry them).
9. Sharpe/maxDD vs B&H? → UNANSWERED (deliberate): no cell qualified; computing deployment stats for non-qualifying cells invites narrative. Available on request from emissions.
10. Cost sensitivity? → ANSWERED §4: FX cells die at < 1 bps RT commission — all FX net ≤ 0 even at 0 cost on gross for most cells; indices are 0-commission (design tier) so their numbers are gross=net; spread unpinned (scenario curve moot with no qualifying cell).
11. Control collapse fractions? → ANSWERED §3/§4: sentinel within expectation; ref-arm below.
12. "What would make the headline wrong?" probes → ANSWERED §4: direction split (drift), DI-margin split (dose-response), fold persistence, year splits, block sweep, seed ranges.
13. Power of the negative? → ANSWERED §4: MDE ≤ 5.2 bps on ALL 440 cells (median 0.4–1.3 by hold) vs screen-implied 30–60 bps effect. 0 cells UNPOWERED (min n = 1,332 ≥ 50).

## 3. Evidence FOR the hypothesis

- **3 of 440 cells clear full-TRAIN CI_low > 0** (block-8, 5-seed battery; sign stable across the 4/8/16 block sweep): HK50 x2h48 net +3.18 bps [0.13, 6.20]; US500 x4h24 +0.93 [0.07, 1.80]; US500 x5h24 +0.93 [0.07, 1.81]. (Multiplicity note: ≈ 11 spurious one-sided CI-clear cells expected among 440 at 2.5% — 3 observed is *below* chance expectation.)
- **Sign structure is not random across instruments**: positive-mean cells concentrate entirely in equity indices (USTEC 16/20 cells, HK50 16, JP225 14, US500 13), while all 10 FX pairs are ≤ 0 in all 200 FX cells. Some systematic mechanism separates the classes (but see §4.5 — the obvious candidate is index drift, not DI information).
- **Ref-arm USTEC h48 dir_gap is nominally positive**: +3.40 bps, CI [0.09, 6.68] — the only hold on the established stratum with a CI-clear point, sign-consistent with the screen's continuation thread.
- **Apparatus is healthy**: CTRL-NULLSENT family-wise read = 1/22 CI-clear strata vs binomial 95th pct threshold 3 → machinery reports null where null is expected; the negative below is not an apparatus artifact.

## 4. Evidence AGAINST the hypothesis

1. **SEL-NEIGHBOR: 0 of 440 cells qualify.** Rule 1 (own F0 CI_low > 0) fails in **every single cell** — best F0 CI_low in the whole grid is −0.09 (US500 x4h24). Rules 2/3 pass in 79/205 cells respectively, but no cell clears its own selection-fold CI. No battery run, no TEST read is reachable under the pre-registered eligibility (§8 design): criterion (i) fails universally.
2. **Effect sizes are ~1 order of magnitude below the mechanism's claim — and the claim itself was overstated in the design.** Design §8/§9 converted the screen's +0.26–0.50 ATR to "30–60 bps at TRAIN-median ATR"; the measured USTEC TRAIN-median 1h ATR is **33.9 bps of price**, so the correct conversion is ≈ **9–17 bps** (0.09 ATR ≈ 3 bps). Measured: best USTEC cell net +1.20 bps (x5h48); best grid cell +3.18 bps (HK50). The negative is **powered against the corrected target**: per-cell MDE 0.18–5.23 bps (median 0.4–1.3 by hold), all 440 cells n ≥ 1,332.
3. **Ref-arm dir_gap does not replicate the screen on its established stratum.** USTEC h12/24/36 all CI-straddle 0; the h48 point (+3.40) is **MC-fragile** (ci_low seed range [−0.02, +0.15] straddles 0) and **block-fragile** (2× block CI [−0.13, 6.93]). Family-wise, CI-clear strata ≈ 5/88 ≈ the 4.4 expected at 5% — and two of those are STOXX50 *negative* (h12 [−5.22, −0.03], h24 [−8.48, −0.64]). The conditioning channel, measured directly and confound-free, is indistinguishable from noise at TRAIN scale.
4. **No DI dose-response.** If DI direction carries information, wider |+DI−−DI| margins should carry more. Measured on all focus cells the *low*-margin half earns as much or more (HK50 x8h36: low 4.60 [0.51, 8.58] vs high 0.48 [−3.47, 4.48]; US2000 x8h48: low +2.38 vs high −0.60; USTEC x4h48: low 1.87 vs high 0.50). The gate's payoff is flat-to-inverted in its own conditioning variable.
5. **The index positives have the fingerprint of drift, not conditioning — quantified over the full index grid (probe b, `analysis_code/probe_direction.py`, `results/direction_split.csv`).** Across all 200 index cells, **99% have their stronger direction side equal to the instrument's own realized drift side** (long for 2021–23 rising US/JP/EU indices, short for falling HK50). Only 25/200 cells show both sides positive (16 of them HK50, whose short side still dominates). Examples: US500 x4h24 long +1.26 [0.12, 2.41] vs short +0.62 [−0.63, 1.89]; USTEC x4h48 long +2.97 [0.33, 5.60] vs short −0.51; HK50 x3h48 short +4.06 vs long +2.00. Beta explains the sign structure of §3 without any DI information. The cadence-matched battery (drift-symmetric benchmark) is running as a diagnostic on the 3 disclosure cells (probe a).
6. **Fold and year instability.** The 3 full-TRAIN CI-clear cells all FAIL F0 (their significance comes from pooling selection+validation folds — exactly what SEL-NEIGHBOR exists to prevent reading). Per-year nets flip sign (HK50 x2h48: −2.4/+8.0/+3.8; US2000 x8h48: +1.8/+1.7/−1.1).
7. **FX is uniformly dead**: 200/200 FX cells net ≤ 0 gross ≥ net before commission; adding the 0.5–1.0 bps FX RT commission makes every FX cell negative. The mechanism claims no instrument-class restriction; its universal absence on the class with the least drift is consistent with §4.5.

## 5. Anomalies & open questions

- **Screen→engine attenuation FULLY RECONCILED (2026-07-09, operator-ordered forensics): it
  was a units artifact in the design, not a replication failure.** The SPDR screens normalise
  forward returns by the **LTF 5-minute ATR(14)[t−1]** (`spdr001_screen.py:204,299` —
  `ltf_atr_prev`, the causal normaliser), NOT the 1h HTF ATR. USTEC TRAIN-median 5min ATR =
  **8.19 bps** (vs 1h ATR 33.9 bps). Re-expressed in the screen's own units, the engine
  ref-arm dir_gap is **0.026 / 0.136 / 0.217 / 0.415 ATR_5m** at h12/24/36/48 vs the screen's
  +0.09→+0.50 — the screen effect **replicates in the engine ref-arm** (h48 0.42 vs 0.50,
  within CI). Chain of error: design §4 declared a "1h ATR(14)" divisor for ATR units and §8/§9
  projected "30–60 bps"; the correct real-money size of the screen effect was always
  0.50 × 8.19 ≈ **4 bps/trade at h48** (≈ 0.2–1 bps at short holds). Consequences: (i) the
  conditioning channel is REAL and replicated, but an order of magnitude too small to trade
  net of noise, spread, and one-sided capture (candidate arm ≈ gap/2 further diluted by the
  near-continuous throttle — USTEC x3h12 mean 11.4 bars between entries); (ii) the experiment's
  power design was built against a fictitious 30–60 bps target; the apparatus was nonetheless
  powered for the true ~4 bps effect at TRAIN n (MDE ≈ 0.2–1.3 bps on USTEC cells), so the T1
  negative stands; (iii) the SPDR lane's ATR-unit convention must be pinned in
  `docs/references/spdr-lane.md` to prevent recurrence (graduation designs must state the
  divisor object and its bps value).
- **DE40/STOXX50 missing from the FTMO cost table** under those names (`xen.evaluation.FTMO_COSTS` has `EU50` but no DE40/STOXX50 key). Treated as index-class 0-commission per design §10; flag for the cost-table maintainer.
- STOXX50 ref-arm dir_gap is *negative* CI-clear at h12/h24 — a fade-signed conditioning effect on the smallest-n symbol (4,619 entries). Family-wise it is within the 5% breach budget; noted because CF-HTFDI-001's corrected registration explicitly withdrew fade threads.
- The h48 column is systematically the friendliest hold across indices (USTEC ref-arm h48; grid f0 means rising in H). Longer-horizon drift capture grows with H mechanically; consistent with §4.5, not with a 1h-DI horizon story.
- QA Issue 4 resolution (E6 → DI-gated, code split 2026-07-08) is implemented but the E6 branch is unexercised — T2 never ran (no survivors). No re-QA needed unless a future experiment reuses the model.

## 5b. Operator-ordered forensic probes (2026-07-09, all executed)

**(a) Diagnostic battery — 25-seed matched-cadence random-direction, 3 disclosure cells**
(75 engine runs, all `blocking_pass: true`; `analysis_code/battery_read.py`,
`results/battery_read.csv`; cadence exact — battery n identical to candidate n per cell, E0
direction-independent per D5):

| cell | cand mean | battery mean ± seed-SD | z | pct rank | ≥2 SD |
|---|---|---|---|---|---|
| HK50 x2 h48 | +3.18 | −0.61 ± 1.92 | 1.97 | 0.96 | no (marginal) |
| US500 x4 h24 | +0.93 | +0.04 ± 0.34 | 2.62 | 1.00 | yes |
| US500 x5 h24 | +0.93 | −0.11 ± 0.45 | 2.31 | 1.00 | yes |

**Decomposition (static drift-capture vs timing):** candidate long-share is 0.45–0.49 (slightly
short-biased), so the static side-imbalance term contributes ≈ 0 (−0.01 to +0.09 bps). The
candidate mean is a genuine **direction-timing gap** on traded slots: E[m|long slots] −
E[m|short slots] = +6.2 (HK50), +1.9 (US500 both) bps — the same channel the ref-arm measures.
The battery result therefore confirms a REAL conditioning effect of ~1–3 bps/trade on these
cells — and simultaneously bounds it: it is the reconciled screen effect (§5 units finding),
an order of magnitude below tradeable size at these holds.

**(b) Direction decomposition** — see §4.5 (99% drift-side alignment; the drift determines
*where* the tiny timing gap is visible, not its existence).

**(c) Screen↔engine reconciliation** — see §5 first bullet (units artifact; screen replicates
in engine ref-arm at 0.42 vs 0.50 ATR_5m at h48; true effect ≈ 4 bps/trade).

**Net forensic conclusion:** the SPDR observation was real and replicates end-to-end; it never
was 30–60 bps. The design's unit conversion (1h-ATR divisor instead of the screen's 5min-ATR)
inflated the target ~4×, and one-sided capture + throttle dilution take the tradable residue
to ~1–3 bps — below commission on FX and below noise-robust selection everywhere. EXP-025's
negative is a magnitude falsification, not an existence falsification.

## 6. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: NOT SUPPORTED** (TRAIN-stage terminal: no cell reaches the pre-registered
  TEST eligibility, so the confirmatory machinery never engages; the design's own protocol
  ends the experiment at T1).
- **Driven by:** (1) 0/440 SEL-NEIGHBOR qualification with the negative fully powered
  (MDE ≤ 5.2 bps vs 30–60 bps claimed effect); (2) direct ref-arm measurement of the
  conditioning channel is noise-level and fragile on the established stratum, with
  family-wise breaches at chance; (3) the only positive structure in the grid (equity-index
  cells) is long/short-asymmetric in each index's own drift direction and shows no DI
  dose-response — a beta artifact shape, not a conditioning edge.
- **Symmetry note (L-11):** this is not a wash — the measured effects are 1–3 bps against a
  powered 30–60 bps claim; but neither is it a *contradiction* (no CONTRADICTED band cell on
  the established stratum; USTEC stays weakly positive-signed throughout). The screen's
  SPDR-scale effect simply does not survive contact with trade-level engine economics.
- **Probes (a)–(c) executed 2026-07-09 (§5b): both "would change if" conditions fired — and
  the verdict recommendation stands, refined.** The battery cleared 2 seed-SD on the US500
  cells and the reconciliation showed the gap was a units mismatch: the conditioning effect
  EXISTS (replicated screen→ref-arm→battery) at ~1–3 bps/trade, but the hypothesis under test
  — "carries a NET-of-commission per-trade directional edge [at] TEST" — fails on magnitude:
  no cell passes the pre-registered selection (rule 1 universal fail), FX dies to commission,
  index cells sit at ~1/10 of the noise-robust selection bar. Recommendation remains **NOT
  SUPPORTED (magnitude, not existence)**: the mechanism is real and now precisely sized;
  it is not tradeable in this vehicle class.
- **Final verdict is the operator's.** Remaining pushes if wanted: same-events dual-pipeline
  diff on USTEC x3 (would pin the residual 0.42-vs-0.50 gap — event-population difference is
  the likely cause); exit-method (T2) rescue is NOT recommended — no exit can multiply a
  ~2 bps conditional gap past costs without leverage on the same noise.

## Artifact map

| Artifact | Producer |
|---|---|
| `results/train_trades.parquet`, `cell_counts.csv`, `train_cuts.json` | `analysis_code/build_cells.py` |
| `results/cell_stats.csv` (440 cells + SEL-NEIGHBOR), `commission_bps.json` | `analysis_code/cell_stats.py` |
| `results/ref_arm_dir_gap.csv` | `analysis_code/ref_arm.py` (seed 2001, D4 regenerable) |
| `results/sentinel.csv` | `analysis_code/sentinel.py` |
| `results/mde.csv` + focus-cell probes (stdout) | `analysis_code/probes.py` |
| `results/estimand_validation_EXP-025-*.json` (22) | `xen.estimand_validation` CLI |
