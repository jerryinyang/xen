# G-022 Gate Review — Global-Holdout Deployment Release (Terminal)

> ## ⚠ RETRACTED — REFUTED (2026-06-26): EXIT-RCT exit look-ahead
> **The G-022 `DEPLOYABLE_CONFIRMED` adjudication below is RETRACTED.** The deployment portfolio (EXP-095/096)
> and the EXP-097 global-holdout confirmation inherit the EXP-093 EXIT-RCT one-bar exit look-ahead: `arm_levels`
> (`EXP-090/code/run_experiment.py:305-310`) rests `rct_target[di]` — bar `di`'s **own** close
> (`mean_reversion.py:174`) — as the intrabar limit during bar `di`; live-actable is `rct_target[di-1]`.
> Causalized, the bare RSI-2 fade is net-negative even gross, so the high portfolio Sharpe is not a deployable
> edge. Exposed by the cTrader port + forward test (`XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md`; a
> secondary cBot-port defect = the REAL stream also omitted the v2 0.05·ATR entry slippage the research charges).
> **The single sanctioned global-holdout shot (EXP-097) stays SPENT — spent-on-defect, non-refundable.** EXP-098
> robustness replicated a look-ahead-biased portfolio. **CF-MR-001 CLOSED — REFUTED**; EXP-089/G-020 availability
> stands. Full scope + governance: `docs/experiments-docs/families/cf-mr-001/INDEX.md` §CLOSURE. *Text below
> retained verbatim.*

**Date:** 2026-06-25
**Gate:** G-022 (Phase 022 terminal gate — **DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE** on the **bare RSI-2
fade (CORE) + EXIT-RCT** deployed as the G-022a-frozen, noise-aware causal ERC portfolio, against the single
sanctioned final-30% global-holdout read).
**Adjudication basis:** the mechanical rule frozen **before** the holdout was loaded
([`G-022-gate-criteria.md`](G-022-gate-criteria.md) §2), over the G-022a-frozen confirmation statistic + bands
([`G-022a-gate-criteria.md`](G-022a-gate-criteria.md) §3.4); primary = Portfolio **B**; A co-reported on the same
read. No threshold/band/rule re-edited after seeing the holdout outcome.
**Input:** EXP-097 (`COMPLETED`, audit PASS 0C/0W/4I, pre-exec + post-exec APPROVE) — the single global-holdout
contact. Robustness companion EXP-098 (PPS cross-broker + aggregation, both arms ROBUST) is **non-binding
disclosure**, does not enter this adjudication, and does not upgrade the verdict.
**Outcome:** **DEPLOYABLE_CONFIRMED.** Primary Portfolio B clears its predeclared band — Sharpe LB **4.762 >
band 2.00** (+2.76, ≈2.4×) with co-binding Calmar LB **10.731 > 0** — on n=80 fresh holdout weeks. The bare
RSI-2 fade is the programme's **first deployment-grade price strategy**.
**Reads / holdout:** EXP-097 spent the **single sanctioned global-holdout-governance event** (`holdout_first_touch
=EXP-097`, `global_holdout_shot_spent=true`); **outside** the analysis-TEST 48-stratum ledger (the 11 carried
strata stay 1/2, the other 37 stay 0/2); **0 counted analysis-TEST reads, 0 candidate slots**. Non-repeatable,
non-upgradable.

> **Scope note.** G-022 adjudicates the **portfolio deployment** estimand (primary = B) on the final-30% global
> holdout. It does **not** re-open the per-cell file drawer, the 3 non-confirming 1h cells, or any
> registered-but-deferred lever; each needs its own dated `D0-amendment-*` + slot decision. The EURJPY-4h drop is
> a *new* post-G-022 deployment-engineering item, not part of this frozen read.

---

## 1. Decision

The verdict is adjudicated by the predeclared §2 mechanical rule over the primary Portfolio B, on the holdout
region (`grid_epoch ≥ H`, H = 2024-12-13; weekly-aggregated MBB one-sided LBs, N_BOOT=10,000, α=0.10, seed
20260624):

```
CONFIRM(B)            iff  Sharpe_LB(B) > band_B (2.00)  AND  Calmar_LB(B) > 0
DEPLOYABLE_CONFIRMED  iff  CONFIRM(B)
```

| Portfolio | ann Sharpe (pt) | **Sharpe LB (binding)** | band | Calmar LB | MaxDD | ann vol | CONFIRM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :--: |
| **B** (ERC + circuit-breaker, **primary**) | 6.639 | **4.762** | **2.00** | 10.731 | 0.046 | 0.114 | **YES** |
| A (static ERC, disclosed) | 6.055 | 4.250 | 1.75 | 8.296 | 0.047 | 0.115 | YES |
| naive inverse-vol (contrast) | 6.030 | 4.261 | — | 8.351 | 0.045 | 0.110 | — |

**CONFIRM(B) holds** (Sharpe LB 4.762 > 2.00 ∧ Calmar LB 10.731 > 0) → **DEPLOYABLE_CONFIRMED** with no
discretion. A co-confirms (disclosed, not used to rescue); the naive inverse-vol contrast also clears, showing the
edge is not an artifact of the ERC weighting choice. B clears its band by **+2.76** and is **not** in the DECAYED
region (`Sharpe_pt(B)=6.639 > 2.00`, `Sharpe_LB(B)=4.762 > 0`) nor INCONCLUSIVE (LB strictly above the band).

## 2. Relationship to the predeclared rule (mechanical)

`G-022-gate-criteria.md` §2 and `G-022a-gate-criteria.md` §3.4 fixed the rule, statistic, primary, and bands
**before** the holdout was loaded. The realized numbers resolve the rule to **DEPLOYABLE_CONFIRMED** without
discretion: the primary-B Sharpe LB sits ~2.76 above its band and the Calmar leg is strongly positive. No band,
block definition, N_BOOT, α, seed, primary designation, or construction parameter was retro-edited after the
holdout outcome was seen (§3.7 no goalpost-moving). The mechanism explanation (§4) is *not* part of the mechanical
verdict.

## 3. Adjudication checklist (G-022-gate-criteria.md §3 — affirmatively confirmed)

1. **Holdout virginity until EXP-097.** ✓ `holdout_untouched` flips to `false` **only** in EXP-097's
   `run_metadata.json`; no earlier stage loaded any final-30% bar (incl. 1-minute). Analysis set entered EXP-097
   solely as past-only causal warmup; the binding metric is restricted to `grid_epoch ≥ H` (excludes the ~2-day
   transition zone). The G-022a freeze certified holdout virginity before the read.
2. **Construction identity.** ✓ The G-022a-frozen pipeline verbatim — carry-8 set, binding-v2 ERC (LW-90d
   covariance, weekly rebalance, 10% vol anchor, 1.5× concurrent-risk cap, intra-1h MTM, trailing-50 circuit
   breaker), EXIT-RCT/adverse/cost frozen, seed 20260624. No re-fit, re-tune, or re-selection. Causal
   weights/MTM/fills exercised **in the holdout region** and PASS; real touched prices; determinism byte-identical
   (A/B).
3. **Statistic fidelity.** ✓ Sharpe/Calmar LBs computed with the frozen MBB machinery (block = weekly cadence,
   N_BOOT=10,000, α=0.10, seed 20260624); bands applied as frozen (A 1.75 / B 2.00); primary = B; A co-reported;
   binding-statistic re-seed identity confirmed. No band/rule retro-edited.
4. **A-vs-B / multiplicity honesty.** ✓ Both A and B read from **one** holdout materialization (one read); family
   verdict keys off **B only**; A's co-confirmation is disclosed, not promoted. No OR-rescue path was available or
   used.
5. **Per-cell disclosure (LESSON-001).** ✓ Per-cell holdout nets reported alongside the portfolio; **7 of 8 cells
   carry a positive one-sided LB** (verdict broad-based, not one-cell-driven). The single net-negative cell,
   **EURJPY-4h** (net mean −0.006, ci_low −0.031), is exactly the cell pre-flagged `NOISE_DEGRADED` at G-022a and
   is the smallest positive contributor — dropping it would *improve* the book. No broken cell hidden in the
   aggregate; no single cell carries the verdict.
6. **Read & ledger.** ✓ EXP-097 recorded as **one** global-holdout-governance event in `test-read-ledger.md` +
   `multiplicity-registry.md` in the same change; **outside** the analysis-TEST 48-stratum ledger (11 carried
   strata stay 1/2); **0 counted analysis-TEST reads, 0 candidate slots**; non-repeatable / non-upgradable.
7. **No goalpost-moving.** ✓ Frozen set / construction / band / primary / rule not re-edited after the holdout
   outcome. The EURJPY-4h drop and all deferred levers are explicitly deferred to new scopes.

## 4. Mechanism (why DEPLOYABLE_CONFIRMED, and what carries it)

The confirm is **structural, not a bug**. Three facts carry it:

1. **High Sharpe is diversification, not a single lucky cell.** A causal ERC book of 8 weakly-correlated cells
   vol-anchored to 10% produces Sharpe ≈ 6 (LB ≈ 4.8); the same construction produced Sharpe ≈ 6 / LB ≈ 4.9 on
   the analysis set, and the bands were the A4-calibrated m\* against that distribution. The holdout number is
   **in-family with the pre-frozen band** — over-confirmation context (EXP-032 lesson), not a regime surprise.
2. **No portfolio decay, because per-cell decay was heterogeneous and offsetting.** The 3 strongest 4h cells
   (EURUSD/XAUUSD/USDCHF) **improved** OOS (+0.015…+0.033 ATR); the JPY-cluster and 1h-index cells decayed; the
   gainers offset the decayers. Portfolio Sharpe LB shrank only **−0.135** for B (4.897 → 4.762) vs **−0.897** for
   A (5.147 → 4.250). The circuit breaker — de-allocating the fragile 1h cells during their weak stretches — is
   precisely why **B both lands higher and shrank far less than A**, vindicating the pre-holdout choice of B as
   primary (the adaptability hypothesis the phase was built to test).
3. **Gate matches the effect shape.** Sharpe LB (risk-adjusted location) + co-binding Calmar LB (downside) fit a
   positive-mean diversified stream; there is no tail/bimodal structure the binding gate would miss
   (gate-shape check PASS).

The honest design prior — *the holdout may show additional decay beyond the uniform TRAIN→TEST shrinkage* — was
tested and did **not** materialize at the portfolio level; diversification + the online breaker absorbed the
heterogeneous per-cell decay, which is the deployment claim the phase set out to falsify.

## 5. Programme routing (mechanical consequence)

**DEPLOYABLE_CONFIRMED** → the bare RSI-2 fade (CORE) + EXIT-RCT, deployed as the **carry-8 causal ERC portfolio
with circuit-breaker (Portfolio B), binding-v2 entry fill, under conservative round-trip cost**, is the
programme's **first deployment-grade price strategy**. The frozen spec is the production deployment; the global
holdout shot is spent and non-repeatable. Next moves, each a **separate** scope (not part of G-022):

- **EURJPY-4h drop / book-trim re-cost** — deployment engineering (the cell is a confirmed OOS-final loser within
  the book, surviving only by diversification); a new dated item, not a holdout re-read.
- **Deferred levers** — vol-regime, contrarian, 25/75 sizing, 15m domain, regime×variant cross-cuts, faster-cost
  sensitivity, instrument/domain expansion — each under its own `D0-amendment-*` + slot decision.

## 6. Integrity expectations at adjudication (carried — all met)

- **One holdout read, ever** (this gate): spent at EXP-097, recorded as the single sanctioned shot;
  non-repeatable / non-upgradable. ✓
- **Frozen-rule discipline:** the §2 rule, §3.2 construction, bands, and primary are exactly as frozen at G-022a;
  no retro-edit. ✓
- **Determinism / real-price / causality:** byte-identical second pass; real touched fills; causal weights/MTM;
  MTM conservation ≤ 2.8e-14 ATR (8/8); headline re-derived bit-for-bit from the saved return series. ✓
- **Per-stratum doctrine (LESSON-001):** per-cell holdout outcomes disclosed (incl. the EURJPY-4h loser); the
  binding estimand is the primary-B portfolio; any collapsed convenience flag is NON-BINDING. ✓
- **File drawer:** A and B holdout outcomes and every per-cell outcome are **retained** whatever the verdict;
  nothing reopened by re-parameterization. ✓

---

*Companion documents: [`design.md`](design.md) §6 · [`G-022-gate-criteria.md`](G-022-gate-criteria.md) (frozen
rubric) · [`G-022a-gate-criteria.md`](G-022a-gate-criteria.md) · [`G-022a-gate-review.md`](G-022a-gate-review.md) ·
[`D0-predeclarations.md`](D0-predeclarations.md) §D4/§D9 · EXP-097
[`report.md`](../../../../python/experiments/EXP-097/report.md) · EXP-098
[`report.md`](../../../../python/experiments/EXP-098/report.md) (non-binding robustness) · family spec
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).
Phase 022 retrospective: [`retrospective.md`](retrospective.md).*
