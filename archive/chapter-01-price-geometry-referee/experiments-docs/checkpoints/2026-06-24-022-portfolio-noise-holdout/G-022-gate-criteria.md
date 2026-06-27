# G-022 Gate Criteria — Terminal Global-Holdout Rubric (CF-MR-001 deployment portfolio)

**Date:** 2026-06-25 (frozen at G-022a; **adjudicated only after EXP-097**).
**Gate:** G-022 (Phase 022 terminal gate — **DEPLOYABLE_CONFIRMED / DECAYED / INCONCLUSIVE** on the bare RSI-2
fade deployed as the frozen ERC portfolio, against the single sanctioned final-30% global-holdout read).
**Status:** **FROZEN — PENDING EXP-097.** This fixes the mechanical rubric the future G-022 adjudication applies,
frozen **before** the holdout is loaded (freeze the rule, not the story). The adjudication
(`G-022-gate-review.md`) is written **after** EXP-097, reading the realized holdout numbers against this rubric.
**Adjudication basis:** the G-022a-frozen confirmation statistic + bands ([`G-022a-gate-criteria.md`](G-022a-gate-criteria.md)
§3.4), primary = Portfolio B (§3.3). No threshold/band/rule is re-edited after seeing the holdout outcome.

---

## 1. What G-022 decides

G-022 emits the programme's **deployment-grade OOS-final** verdict on the bare RSI-2 fade: *deployed as the
frozen, noise-aware ERC portfolio under a realistic 1-minute entry fill, does it confirm a positive risk-adjusted
edge on the fully-fresh final-30% global holdout, within the G-022a-predeclared band?* The **binding estimand is
the portfolio** (primary = B); per-cell holdout outcomes are disclosed alongside (LESSON-001).

## 2. The mechanical rule (frozen at G-022a — reproduced for adjudication)

```
Per portfolio P in {A, B}, on the global-holdout slice, with the G-022a-frozen construction:
  Sharpe_LB(P)  = holdout annualized-Sharpe moving-block one-sided lower bound
                  (block = weekly cadence in 1h-grid steps; N_BOOT=10_000; alpha=0.10; seed 20260624)
  Calmar_LB(P)  = holdout Calmar moving-block one-sided lower bound (same block/N_BOOT)
  CONFIRM(P)    iff  Sharpe_LB(P) > band_P  AND  Calmar_LB(P) > 0
                with  band_A = 1.75 ,  band_B = 2.00   (= inherited A4 MDE m*)

PRIMARY = Portfolio B.  Portfolio A is co-adjudicated and reported on the SAME single read (one holdout
contact), but does NOT rescue the family verdict via an OR.

G-022:
  DEPLOYABLE_CONFIRMED  iff  CONFIRM(B)                            (deploy B; A's status disclosed)
  DECAYED / NOT_CONFIRMED iff  Sharpe_pt(B) <= band_B  OR  Sharpe_LB(B) <= 0
                               (the central estimate itself fails the bar, or the LB is non-positive)
  INCONCLUSIVE          iff  not CONFIRM(B) and not DECAYED        (Sharpe_pt(B) > band_B but Sharpe_LB(B) <=
                             band_B, or the Calmar leg fails while Sharpe holds — power-limited / spans the
                             band, a la EXP-032)
```

The verdict is mechanical and predeclared; the mechanism explanation is not.

## 3. Adjudication checklist (what the G-022 review must affirmatively confirm)

Read **per stratum / per cell** alongside the binding portfolio (LESSON-001); no collapsed cross-cell boolean is
binding beyond the predeclared primary-B rule.

1. **Holdout virginity until EXP-097.** The final-30% global holdout was loaded for the **first time** at EXP-097,
   after the G-022a freeze; no earlier stage touched it (incl. its 1-minute bars). `holdout_untouched` flips to
   `false` **only** in EXP-097's `run_metadata.json`, recorded as the single sanctioned shot.
2. **Construction identity.** The holdout portfolio used the **G-022a-frozen pipeline verbatim** (carry-8 set,
   ERC/LW-90d/weekly/10%-vol/1.5×-cap/intra-1h-MTM, binding **v2** entry fill, EXIT-RCT/adverse/cost) — **no
   re-fit, no re-tune, no re-selection**. Causal weights/MTM/fills; real touched prices; determinism
   byte-identical.
3. **Statistic fidelity.** `Sharpe_LB` / `Calmar_LB` computed with the **frozen** MBB machinery (block = cadence,
   N_BOOT=10_000, α=0.10, seed 20260624); bands applied as frozen (A 1.75 / B 2.00); **primary = B**; A
   co-reported. No band/rule retro-edited.
4. **A-vs-B / multiplicity honesty.** Both A and B read from **one** holdout materialization (one read); the
   family verdict keys off **B only**; an A-confirm with a B-fail is **disclosed, not promoted** to
   DEPLOYABLE_CONFIRMED.
5. **Per-cell disclosure.** Per-cell holdout net outcomes (incl. the flagged EURJPY-4h) reported alongside the
   portfolio; masking checked (no broken cell hidden in the aggregate; no single cell carrying the verdict).
6. **Read & ledger.** EXP-097 recorded as **one global-holdout-governance event** in `test-read-ledger.md` +
   `multiplicity-registry.md` in the **same change**; **outside** the analysis-TEST 48-stratum ledger (11 carried
   strata stay 1/2); **0 counted analysis-TEST reads, 0 candidate slots**; non-repeatable / non-upgradable.
7. **No goalpost-moving.** The frozen set / construction / band / primary / rule are **not** re-edited after the
   holdout outcome is seen, whatever it is.

## 4. Programme routing (mechanical consequence)

| Adjudicated state | Consequence |
| --- | --- |
| **DEPLOYABLE_CONFIRMED** | The bare RSI-2 fade is the programme's **first deployment-grade price strategy**. The frozen spec (carry-8 set, ERC + circuit-breaker **B**, v2 fill, cost) is the production deployment; the holdout shot is spent. The deferred levers (vol-regime, contrarian, 25/75, 15m, cross-cuts, tuning, expansion) become expansion candidates, each under its own slot/D0. A's co-confirmation status is disclosed. |
| **DECAYED / NOT_CONFIRMED** | The analysis-TEST edge did not survive to the fully-fresh final slice as a deployable portfolio. Recorded permanently; the deployment claim is unsupported OOS-final; the holdout shot is spent and non-repeatable. The per-cell file drawer and the G-021 analysis-TEST TRADABLE verdict stand unchanged. |
| **INCONCLUSIVE** | Disclosed; neither confirmed nor refuted as a deployment; the holdout shot is spent (one-shot, non-upgradable, EXP-032 precedent). Any further deployment claim needs a separate, later sanctioned read under whatever reserve remains. |

## 5. Integrity expectations at adjudication (carried)

- **One holdout read, ever** (this gate): spent at EXP-097, recorded as the single sanctioned shot; non-repeatable.
- **Frozen-rule discipline:** the §2 rule, §3.2 construction, and the bands/primary are exactly as frozen at
  G-022a; no retro-edit.
- **Determinism / real-price:** byte-identical second pass; real touched fill prices; ATR/real-price metrics.
- **Per-stratum doctrine (LESSON-001):** per-cell holdout outcomes disclosed; the binding estimand is the
  primary-B portfolio; any collapsed convenience flag is NON-BINDING.
- **File drawer:** A and B holdout outcomes and every per-cell outcome are **retained** whatever the verdict;
  nothing is reopened by re-parameterization.

---

*Companion documents: [`design.md`](design.md) §6 · [`D0-predeclarations.md`](D0-predeclarations.md) §D4/§D9 ·
pre-holdout freeze [`G-022a-gate-criteria.md`](G-022a-gate-criteria.md) · adjudication (after EXP-097)
`G-022-gate-review.md` · family spec
[`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).*
