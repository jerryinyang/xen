# Data Analysis: VAL-006 — corrective re-derivation of multi-leg verdicts (EXP-014b/c/016/017)

**Question.** Which multi-leg (allow/extend/both-leg) claims from EXP-014b, EXP-014c, EXP-016
and EXP-017 survive re-derivation from per-leg truth (`cis_trades.RealizedBps`) via the
canonical `xen.adjudication` estimands, after critical-017 invalidated the per-bar series?

**Scope.** TRAIN band only (EXP-014b/c emissions end at the TRAIN fence by construction —
US2000 `analysis_end_utc` 2024-09-10T09:33 == EXP-016 `TRAIN_FENCE`). TEST band untouched:
EXP-016's 3 counted reads are spent-on-defect; any corrected TEST read needs operator
authorization. 23 family roots, 207 raw cells + 46 shift-twin cells, 11 instruments, frozen
per-instrument 4h costs. All code in `analysis_code/` (gate: `run_gate.py`; census:
`census.py`; probes: `probes.py`); zero imports from any experiment's `code/`.

---

## 1. Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand validation, all cells | **PASS** (25 roots, 271 cells) | `results/estimand_validation.json`; every cell reconciles per-bar↔per-leg within 1 bps (typ. ~1e-12) |
| Provenance (fills physical) | **PASS** (spot) | own fill-in-bar check: US2000 e0/e3 extend z15 entry+exit breach 0.0000 (n=1317 each); blmkt US500 0.0000 (n=58); full-sweep fill checks previously run per-cell in 014b/c |
| Leak tripwire | **DISCLOSED-ONLY** | original phase-shift/permute controls documented invalid/vacuous (B-3/B-6); corrected-estimand shift disclosure in §4 (P3) — informative, not a gate |
| Holdout | **PASS** | every root fence-checked in the gate (last bar ≤ `analysis_end_utc`); no TEST-band bar read anywhere in this analysis |
| Price-primary | **PASS** | all numbers from engine emissions (`data/strategy_runs/`); no signal regenerated |
| Shared-code boundary | **PASS** | `check_no_local_accounting(analysis_code)` → ok; all estimands via `xen.adjudication` |

Gate incidents (both are findings, not blockers, after handling):
- **`partial_abort` legs**: 2 legs (bllim-z15 AUDUSD/US2000 ledgers) with no exit fill and
  NaN `RealizedBps`, not censored — NaN-poisoned totals until `xen.adjudication` learned to
  exclude+disclose them (`n_aborted`). The legacy path silently absorbed these.
- **Mixed-symbol censored marking**: both-leg ledgers carry mate-symbol legs; marking a
  censored EURUSD leg to USDJPY opens fabricated ±10⁶-bps artifacts in an early probe run.
  Fixed with the `own_symbol` guard; note `LegSymbol == ""` means own-instrument in
  single-instrument arms.

## 2. Question list

| # | Question | Answered |
|---|---|---|
| Q1 | Do per-bar and per-leg totals reconcile per cell? | §1 — yes, everywhere, after canonical rebuild |
| Q2 | Which of the invalidated multi-leg cells remain CI-positive per leg? | §3/§4 census |
| Q3 | Are e1 (frozen-TP-only) positives real or survivorship? | §4 P1 — survivorship |
| Q4 | Does the US2000 e3/extend/z15 candidate (+9.5 bps/leg gross) survive? | §4 P4 — no |
| Q5 | What do the survivors look like exposure-adjusted? | §4 P2 |
| Q6 | Is the surviving cluster year-stable? | §4 P5 — no (2022-concentrated) |
| Q7 | Corrected shift-collapse fractions? | §4 P3 — incoherent noise |
| Q8 | AUDUSD/NZDUSD extend "sign-flip" cells — confirmed losers? | §4 — yes |
| Q9 | Both-leg arms under corrected accounting? | §4 — US500 minor positive cluster |
| Q10 | EXP-016 TRAIN reproduction on its own emission | UNANSWERED — same conf as 014c e3 root; TRAIN equivalence adds nothing beyond Q4, and the root spans TEST (left unread) |
| Q11 | Occupancy/physicality of survivors | §4 P2/§5 |

## 3. Census headline (corrected estimand, TRAIN)

207 raw cells. Per-leg net (frozen cost), moving-block bootstrap CI over time-ordered
legs/episodes (block 5, 10k draws, seed 20260704):

| Bucket | Cells |
|---|---|
| per-leg mean CI_low > 0 | 52 |
| …of which e1 (frozen-TP-only exit — survivorship, see P1) | 44 |
| …of which legitimate candidates | 8 |
| per-leg mean CI_high < 0 | 27 |
| total net < 0 | 108/207 |

The 8 legitimate CI-positive cells:

| exit | arm | z | inst | n_legs | net/leg [CI] | episodes | epi CI_low | peak legs | occupancy |
|---|---|---|---|---|---|---|---|---|---|
| e0 | extend | z15 | US2000 | 1317 | +56.8 [+31.5, +82.6] | 130 | **+42.5** | 47 | 0.54 |
| e0 | extend | z20 | US2000 | 771 | +74.5 [+39.0, +110] | 85 | −20.6 | 34 | 0.41 |
| e0 | allow | z20 | US2000 | 442 | +78.8 [+42.6, +115] | 88 | **+128.7** | 18 | 0.41 |
| e0 | allow | z15 | US2000 | 642 | +32.1 [+0.5, +64] | 133 | −80.0 | 20 | 0.53 |
| e2 | extend | z20 | US2000 | 771 | +56.3 [+12.5, +100] | 45 | +45.3 | 28 | 0.75 |
| e0 | extend | z20 | JP225 | 542 | +48.4 [+9.1, +88] | 59 | −85.6 | 40 | 0.34 |
| e0 | blmkt | z15 | US500 | 232 | +41.4 [+2.3, +80] | 58 | +14.5 | 4 | n/a |
| e0 | blmkt | z20 | US500 | 156 | +56.1 [+5.1, +107] | 39 | +33.8 | 4 | n/a |

## 4. Probes

**P1 — e1 positives are survivorship artifacts.** e1 has no SL and no time-stop: a leg exits
only if its frozen TP fills. Completed legs are therefore winners by construction; losers ride
to the fence as "censored" (up to 194 of 388 legs, USDJPY z15). Realized-only accounting shows
+99…+335 bps/leg with occupancy 94-97% and peak exposure up to 212 legs. Including censored
legs' marked-to-open P&L: **16 of 44 e1 cells flip sign outright** (e.g. US500 e1/extend/z20:
realized +185.8k, censored MTM −336.3k → honest **−150.9k bps**), and the remainder shrink to
economically arbitrary residues of an unbounded-inventory grid. No e1 cell is evidence of edge.

**P2 — exposure normalisation deflates the legitimate 8.** Totals are single-unit bps summed
across dozens of concurrent legs. Per exposure-bar and on peak concurrent exposure:

- best cell (e0/allow/z20 US2000): 2.8 bps/exposure-bar, ~5.1%/yr on peak exposure;
- e0/extend/z15 US2000: 2.2 bps/exposure-bar, ~4.2%/yr on peak, maxDD −29.9k bps single-unit
  (≈ −64% of a 47-leg capital base);
- JP225 e0/z20: 1.5 bps/exposure-bar, ~1.7%/yr, episode CI not positive;
- blmkt US500: 0.8-1.0 bps/exposure-bar but only 4 legs peak → ~5.7-6.2%/yr on peak exposure —
  the cleanest exposure profile in the census.

**P3 — corrected shift-collapse is incoherent.** Per-leg shift/raw fractions range −3.0 to
+13.8; the shifted twin frequently *beats* raw (US2000 e3/z15: raw +4.5 vs shift +22.9/leg).
The prior "50-85% survives the shift" narrative was an artifact of the corrupted series; under
per-leg truth the shift control carries no coherent signal in either direction (consistent with
B-3: mixed own-price/construction P&L makes the control's semantics uninterpretable).

**P4 — the critical-017 candidate dies.** US2000 e3/extend/z15: gross +9.53 bps/leg,
CI **[−15.9, +32.0]** (n=1317) — indistinguishable from zero **even at zero cost**; there is no
cost at which CI_low > 0. EXP-016's PERFORMANCE_RETAINED, already void for spending reads on
the corrupted series, also has no valid TRAIN-side edge behind it.

**P5 — no year stability.** The surviving cluster is 2021-22-concentrated; 2023 is negative in
5 of 6 probed cells (US2000 e0/extend/z15: 2021 +23.5k, 2022 +51.9k, 2023 **−11.1k**, 2024
+10.5k). 2022's dislocation regime supplies most of the P&L. The 014c "year-stable 2021-24"
claim does not survive corrected accounting.

## 5. Evidence FOR (anything surviving)

1. **A US2000 e0/e2 cluster is statistically positive per leg on TRAIN**: 5 cells, net/leg
   CI_low > 0 at frozen cost, two also episode-CI-positive (e0/allow/z20 epi_lo +128.7;
   e0/extend/z15 epi_lo +42.5, 130 episodes). Consistent across z15/z20 and allow/extend —
   not a single-cell fluke within US2000.
2. **US500 both-leg is positive in all four both-leg variants** (blmkt/bllim × z15/z20:
   +9.6k/+8.8k/+6.8k/+5.0k total net; blmkt cells CI-positive per leg), with bounded exposure
   (peak 4 legs) — small but structurally the cleanest positive in the census.
3. Fills are physical (0.0000 breach on all spot-checked cells), accounting now reconciles
   exactly, and these positives are net of frozen costs.

## 6. Evidence AGAINST

1. **Estimand collapse of the prior record**: of the "61-cell extend field", the corrected
   census leaves 8 legitimate CI-positive cells, 44 e1 survivorship artifacts, and confirms
   AUDUSD (−7…−14/leg) and NZDUSD (−25…−33/leg) extend ladders as outright losers.
2. **The named candidate is dead** (P4): US2000 e3/extend/z15 CI straddles 0 at zero cost.
3. **Magnitudes are small once exposure-honest** (P2): 1-3 bps/exposure-bar, 2-5%/yr on peak
   exposure, against single-unit maxDD of −10k…−30k bps and multi-month underwater episodes.
4. **Regime concentration** (P5): 2022 supplies the bulk; 2023 negative almost everywhere.
5. **No attribution story**: the corrected shift disclosure (P3) is noise; nothing established
   about mechanism (CF-MR-005's mechanism question remains open, now on a much thinner base).
6. Multiple-comparison context: 8 CI-positive cells out of 207 at α=0.05 with heavy
   cross-cell correlation is only modestly above the ~10 false positives chance would give —
   the US2000/US500 clustering is the only reason this isn't dismissible outright.

## 7. Anomalies & open questions

- e1's engine design (no loss exit) makes any realized-only statistic meaningless; if e1 is
  ever revisited, the estimand must be inventory-marked, not fill-realized.
- 2 `partial_abort` legs and 2 missing US500 emissions (e2/extend/z15, e3/allow/z20 roots have
  10 cells) — now surfaced by the manifest; harmless here, should not recur silently.
- JP225 e0/z20: leg-CI-positive but episode-CI-negative — episode aggregation absorbs the
  positive legs into long mixed episodes; object-identity question for any follow-up.

## 8. Recommended verdict (experiment-level only — NOT final, NOT family)

**On the corrective question "do the invalidated multi-leg verdicts survive re-derivation?":
NOT SUPPORTED — the prior multi-leg record does not survive.** Specifically:
- EXP-014b/c multi-leg NET_ADMIT/REJECT_LEAK adjudications: superseded; corrected statuses per
  §3 (most cells null or negative; 8 CI-positive remainders listed).
- EXP-016 PERFORMANCE_RETAINED: no valid basis (reads spent-on-defect AND no TRAIN edge in the
  read arm).
- EXP-017 A1 Δ: corrupted net side confirmed; episode objects must be rebuilt from
  `xen.adjudication.build_episodes` if the probe is rerun.

**Residual worth operator attention (WASH-to-weak-positive, unadjudicated):** the US2000
e0/e2 cluster and the US500 both-leg cluster — statistically positive per leg on TRAIN, small
after exposure adjustment, 2022-concentrated, mechanism unknown.

Driven by: (1) P1 survivorship collapse of the e1 block, (2) P4 death of the named candidate,
(3) exposure/regime deflation of the remainder (P2/P5).
Would change if: a predeclared, exposure-honest read of the US2000/US500 clusters on fresh
data (or the unread TEST band, operator-authorized) showed the 2023 drawdown to be
non-structural.

**Final verdict is the operator's.** Suggested probes if you want to push: (a) episode-level
deep-dive on US2000 e0/allow/z20 (the strongest cell: epi CI [+128.7, …], 88 episodes);
(b) US500 both-leg mechanism look (4-leg bounded exposure makes it cheap to reason about);
(c) authorize a corrected TEST-band read policy before anything touches TEST.
