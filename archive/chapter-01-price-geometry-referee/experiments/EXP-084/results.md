# Results: EXP-084 — AVWAP-4h Portfolio Confirmation Read (CF-CAPGEO-001 Phase 018 / HYP-004b)

**Verdict: `NOT_CONFIRM`** (portfolio unit; well-powered; exit-invariant). The single sanctioned out-of-sample
contact for HYP-004 is spent. **HYP-004 closes at G-018.** Ledger: **0 counted reads** — the read was a
portfolio-aggregate **disclosure** against the three member strata (caps preserved, all 48 strata stay 0/2).
The audit returned **PASS** (0 Critical / 0 Warning / 3 Info); the verdict reproduces exactly from the raw
outputs.

This maps directly to the predeclared interpretation guide (analysis-plan.md → "`NOT_CONFIRM` (a binding leg
fails with power): the net edge does not survive OOS as a portfolio → HYP-004 closes at G-018, basket
disclosed, 0 counted reads. Record the failing leg"). No goalpost was moved.

---

## 1. What was tested

One frozen `WF-EXPANDING` read of a single portfolio basket: `SUB-AVWAP` 4h events pooled across
**NZDUSD + USDCAD + USTEC**, exited by the pinned parameter-free **`AVWAP-FH`**, **NET** of the EXP-085
operator-ratified cost model, adjudicated by the D4 G-018 conjunction (frozen referee suite via `xen.wf` +
FPR-calibrated margin, beats-matched-random, and TRAIN separability S1 ∧ S2). Pooled `n=303`; separability
TRAIN region `n=152`; OOS WF test `n=151` (5 folds, all ≥ MIN_FOLD=30).

The portfolio framing existed precisely to make **S2 adjudicable** (its n≥120 floor blocked every per-cell
read in EXP-083/085). That goal was achieved: pooled TRAIN `n_train_sep=152 ≥ 120`, so S2 was genuinely
evaluated for the first time in this family.

## 2. The binding result — separation on TRAIN, no edge OOS

| Binding leg (G-018 conjunction) | Value | Threshold | Pass? |
|---|---|---|---|
| Suite expectancy (FPR margin) | `exp_lo = −1.045` | `> m = −0.0396` | **FAIL** |
| Co-primary median | `med_lo = −0.821` | `> 0` | **FAIL** |
| Beats matched-random | `beats_lo = −0.656` | `> 0` | **FAIL** |
| S1 attribution | `s1_excess_lo = 1.109` | `> m` | PASS |
| S2 tail non-residual | `tailmass 0.0263 ≤ 0.06` ∧ `q05 −5.049 ≥ −8.430` | both | PASS (n=152) |

**Failing legs: all three economic legs** (expectancy, median, beats-random). The basket *separates* on TRAIN
(S1 ∧ S2 pass) but carries **no positive net edge out-of-sample** — every economic CI_low is materially below
its bar. The pooled net expectancy is **−0.221 ATR** (CI_low −1.045); the net median point estimate is a
marginal +0.058 ATR but its CI_low is −0.821. There is no robust location effect of either kind.

## 3. Mechanism — the apparent edge lives in the selection-overlap region and reverses out-of-sample

This is the headline finding, and it is unambiguous in the per-fold trajectory (plot 1):

| Fold | Test window | Fresh? | Net expectancy | Net median |
|---|---|---|---|---|
| fold0 | [50.2%, 60.1%] | No (selection-overlap) | **+1.866** | +1.626 |
| fold1 | [60.1%, 70.0%] | No (23% fresh) | **+0.068** | +0.910 |
| fold2 | [70.0%, 79.9%] | **Yes** | **−1.002** | −0.465 |
| fold3 | [79.9%, 90.1%] | **Yes** | **−1.250** | −1.665 |
| fold4 | [90.1%, 100%] | **Yes** | **−0.754** | −0.790 |

The frozen §D5 schedule starts WF testing at 50% of the analysis set, but EXP-083/085 **selected** this
candidate on [0, 70%]. The two non-fresh folds (fold0–1, overlapping the selection window) are **positive**;
all three genuinely held-back folds (fold2–4, entries beyond the 70% boundary) are **negative**. The positive
signal that motivated the whole HYP-004 line is an artifact of evaluating on the same region the candidate was
mined from; in the region that was actually held back, the net return is consistently negative. This is
**Risk-1 (flagged in the plan and scope) materializing in full** — and it is the disciplined reason the
protocol disclosed per-fold freshness rather than reporting a bare aggregate.

## 4. Verdict forensics (from the audit — PASS)

- **Not masking a positive stratum.** All three member strata are net-negative on expectancy
  (NZDUSD −0.579, USDCAD −0.484, USTEC −0.159) with deeply negative CI_lows (−2.100, −2.468, −2.949). The
  pooled `NOT_CONFIRM` is conservative, not concealing. USTEC shows a positive *median* point estimate
  (+0.925) on n=77, but its mean and expectancy CI_low remain negative — a single-instrument median quirk,
  **disclosure-only**, not a basket-level signal.
- **Exit-invariant.** None of the 11 exit arms (the pinned `AVWAP-FH` plus 10 disclosure exits) has a positive
  CI_low. The best point estimates — VP-POC +0.747, D1/D2 +0.505 — still have exp_lo < 0 (−0.259, −0.269,
  −0.251). The non-confirmation is not an artifact of the pinned arm; **no exit rescues the basket OOS.**
- **Gate-shape: correct instrument.** S2 was genuinely adjudicated (n=152) and **passed** — the `AVWAP-FH`
  catastrophe tail is non-residual (tailmass 0.026; q05 −5.05 vs control −8.03). This validates the pin's
  a-priori rationale (genuine continuous-tail pass, not stop-truncation-to-point-mass). So the failure is
  **"no OOS edge," not "an effect of a shape the gate cannot see."** Both location measures are non-positive at
  their CI_lows; there is no hidden tail- or median-only edge.
- **Power adequate → `NOT_CONFIRM`, not `INCONCLUSIVE`.** `n_oos = 151 ≥ 2·MIN_FOLD`, 0 subfloor folds. The
  expectancy CI spans zero, but with adequate power and decisively failing legs the correct pre-registered
  outcome is `NOT_CONFIRM`. `INCONCLUSIVE_SPANS_ZERO` (the acceptable power-limited outcome) does **not**
  apply — this is a substantive negative, not a power deficit.

## 5. Uncertainty and caveats

- **Negative FPR margin (Info 1).** The null-calibrated margin came out mildly negative (`m = −0.0396`),
  making the expectancy leg marginally *easier* than `> 0`. For a `NOT_CONFIRM` this is **conservative-safe**:
  a looser margin can only ease CONFIRM, yet the expectancy CI_low (−1.045) misses even the negative bar, and
  the median and beats-random legs fail independently of `m`. It does not affect this verdict; it is flagged
  for any future read where a CONFIRM could hinge on `m`.
- **Pooled FX+index basket.** The basket mixes FX (NZDUSD/USDCAD) and an index (USTEC) in ATR units, by
  operator ratification. The per-stratum disclosure (§4) shows the OOS negativity is broad, not driven by the
  heterogeneity — so the pooling choice did not manufacture the result.
- **Disclosure-only scope.** Per the portfolio-aggregate rule, **no per-stratum or per-arm binding claim** is
  made. The three strata are now *disclosed* (basket-claim-only); a future *clean* per-instrument counted read
  on NZDUSD/USDCAD/USTEC-4h is permanently mildly weakened (EXP-032 precedent). This was the accepted trade-off
  in D0-amendment-003 §3.

## 6. Programme reading

EXP-083 established that the data-derived exits (D1/D2/D3) earned **no distinctive TRAIN support**, and that
the only net-surviving cells (EXP-085) were the shape-unadjudicated low-n 4h `SUB-AVWAP` cells. EXP-084 now
closes the loop: pooled into a portfolio so S2 could finally be evaluated, those cells **separate on TRAIN but
do not confirm out-of-sample under any exit**. The single positive-looking signal was selection-region
overlap, and it reverses in the held-back folds.

- **HYP-004 closes at G-018.** The AVWAP-4h reversal capture geometry is **not net-tradable out-of-sample as a
  portfolio**. The family's "data-derived exits beat conventional" thesis was already *unsupported on TRAIN*
  (EXP-083) and is now also *unconfirmed OOS* (the derived arms fare no better than conventional ones — all
  CI_lows negative). The holdout was never touched and is **not** released.

## 7. Suggested next steps (new scopes — not extensions of EXP-084)

These are candidate directions for a future phase/checkpoint, each requiring its own G0 registration and D0:

1. **New-substrate entry geometry, not exit geometry.** The cross-exit invariance of the failure (no exit
   helps) points away from exit design entirely. A new candidate family targeting a *different entry/availability
   condition* (the EXP-083 finding located any edge in AVWAP-4h availability, which EXP-084 now shows does not
   persist OOS) — e.g. a regime/liquidity-conditioned entry — would be a fresh hypothesis, not a re-run.
2. **Higher-frequency, better-powered stratum.** The only well-powered S2-PASS stratum in this family
   (AUDUSD-1h harami, n=988) was net-*inconclusive* on TRAIN in EXP-085 (median leg failed by a hair). A
   separate scope could open a counted read there with its own D0-fixed binding stratum and Holm family — a
   distinct, clean per-stratum read (not the disclosed 4h basket).
3. **Cost-sensitivity as a standalone characterization.** A TRAIN-only scope quantifying how much of the 4h
   gross edge is structurally cost-fragile vs selection-fragile could inform whether any 4h reversal line is
   worth a future counted read at all.

## 8. Registry disposition (for Stage 7 documenter)

- **Registry-relevant: YES.**
- `multiplicity-registry.md` EXP-084 row → **`COMPLETE — NOT_CONFIRM`** (portfolio read; 0 candidate slots; no
  new countable item). Item outcome recorded and **retained** (not deleted).
- `candidate-families/cf-capgeo-001.md` → **HYP-004 closed at G-018**; family status `SCREENED`/closed-thesis
  for the AVWAP-4h portfolio line (the "data-derived beats conventional" thesis remains unsupported on TRAIN
  and is now additionally unconfirmed OOS as a portfolio). Family-level: no net-tradable OOS capture geometry
  found.
- `test-read-ledger.md` → enter the EXP-084 **disclosure** against NZDUSD-4h, USDCAD-4h, USTEC-4h
  (portfolio-aggregate rule); **0 counted reads**, the three strata become *disclosed*, all 48 strata stay
  **0/2 open**. Holdout never read.
