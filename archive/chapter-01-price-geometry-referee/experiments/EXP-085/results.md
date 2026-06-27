# Results: Experiment EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate on the EXP-083 Valid-Candidate Set

## Summary

Under the predeclared conservative round-trip + bar-count financing cost model (operator-ratified at Stage 4),
the experiment returns the predeclared verdict **`NET_SURVIVES`** — ≥1 of the 26 EXP-083 hash-pinned survivors
retains a net per-event edge on TRAIN (21/26 `NET_POS`, 5 `NET_INCONCLUSIVE_SPANS_ZERO`, 0 `NET_NEG`). **But
the pooled "21/26" is a disclosure, not a clean tradability signal, and per stratum it points the other way:**
every one of the 21 net survivors is a **shape-unadjudicated, low-n (n=44–78) 4h `SUB-AVWAP` cell** whose
separability gate (S2) was never evaluated, while the **only well-powered, S2-shape-guarded stratum —
AUDUSD-1h (`SUB-HARAMI-V2A`, n=988) — is net-inconclusive in all 4 of its cells**, passing the expectancy leg
but failing the median leg by a hair. Realistic cost did **not** kill the gross edge here (contrast EXP-030/045),
because the 4h gross magnitudes (1–2 ATR mean) dwarf the ~0.15–0.35 ATR cost — but that edge lives entirely in
the cells the programme has least reason to trust. EXP-085 **authorizes nothing**; it is a read-gate input to
the operator's G-018 decision. The audit is PASS (0C/2W/3I); numerics reproduce to full float precision;
holdout untouched, 0 counted TEST reads.

## Detailed Findings

### Finding 1 — Per-stratum verdict (the binding read): the only shape-guarded, well-powered stratum does not survive net

The binding rule is **per stratum** (LESSON-001): a survivor is `NET_POS` iff net expectancy `CI_low_1s > 0`
**and** net median `CI_low_1s > 0`. Re-derived per stratum (independently confirmed in the audit):

| Stratum (cell) | substrate / n / S2 | per-survivor verdicts | net read |
|---|---|---|---|
| **AUDUSD-1h** | `SUB-HARAMI-V2A` / **988** / **S2-PASS** | **4/4 `NET_INCONCLUSIVE_SPANS_ZERO`** | exp_lo **+0.057…+0.081 > 0**, med_lo **−0.020…−0.047 < 0** (median leg fails) |
| NZDUSD-4h | `SUB-AVWAP` / 77 / **S2-DEFERRED** | 9 `NET_POS`, 1 inconclusive (D3, exp_lo −0.017) | net_exp +0.56…+1.00, net_med +0.92…+1.77 |
| USDCAD-4h | `SUB-AVWAP` / 77 (VP-POC 44) / **S2-DEFERRED** | **11/11 `NET_POS`** | net_exp +0.81…+1.74, net_med +1.51…+3.98 |
| USTEC-4h | `SUB-AVWAP` / 46 / **S2-DEFERRED** | 1/1 `NET_POS` (RR-1) | net_exp +1.50, net_med +2.13 |

- **Observation:** the **single S2-PASS stratum** (AUDUSD-1h, n=988) — the only cell where the binding pre-TEST
  separability shape-guard was actually run and passed, and the only well-powered cell — is **net-inconclusive
  in every candidate**. Its net expectancy is solidly positive (point +0.59…+0.65 ATR, lower bound > 0) but the
  **net median lower bound sits just below zero** (−0.020 to −0.047), so it fails the conjunction. This is the
  CF-HA-HARAMI "median-positive-but-not-quite" signature appearing in the one cell with the power to resolve it.
- **Observation:** **all 21 `NET_POS` are S2-DEFERRED** (n<120, separability never adjudicated).
- **Evidence:** `results/cost_readgate.csv`; `plots/01_gross_to_net_waterfall.png` (net expectancy with
  one-sided 95% CI_low whisker vs the zero line, S2-PASS green vs S2-DEFERRED orange).
- **Interpretation:** the pooled `NET_SURVIVES` is rule-correct (≥1 `NET_POS`) but **masks heterogeneity in the
  direction that matters**: read-eligibility is entirely shape-unadjudicated low-n cells; the shape-guarded,
  well-powered stratum is not a net survivor.

### Finding 2 — Cost did not kill the gross edge, but only because gross magnitude dwarfs cost on 4h

- **Observation:** on the 4h `SUB-AVWAP` cells, gross expectancy is 0.74–2.07 ATR (median 1.2–4.4 ATR) against
  a mean per-event cost of only **0.15–0.35 ATR (~15–30% of gross)** — so net ≈ gross and stays strongly
  positive. On AUDUSD-1h the cost bites harder (cost_atr 0.29 ATR, `txn_share` **0.72**) because a 1h ATR is
  smaller, so the same fixed price-bps round-trip is a larger ATR-unit fraction; even there it does not flip
  the sign, but it is enough to leave the median leg short.
- **Evidence:** `results/cost_readgate.csv` (`cost_atr_mean`, `txn_share`/`fin_share`);
  `plots/02_cost_decomposition.png` (transaction vs financing share); `plots/03_net_vs_gross.png` (net vs gross
  with the gross=net diagonal and net=0 line).
- **Interpretation / mechanism:** this is **why EXP-085 did not reproduce the EXP-030/045 cost-kill.** Those
  families had bps-scale gross edges where conservative cost was comparable in magnitude → net went negative.
  Here the returns are ATR-unit and the 4h gross magnitudes are large, so a fixed bps round-trip ÷ a large 4h
  ATR is a small ATR-unit cost. Part of this is a genuine economic effect (a fixed spread is a smaller fraction
  of a larger expected move); part is a property of the ATR normalization; and the favourable magnitudes sit
  **entirely** in n=44–78 cells that the EXP-083 ASS overlay already flagged as small-n-inflated. The financing
  leg (`fin_share` ≈ 0.40–0.60 on 4h via the multi-day bar-count holds vs ≈0.28 on the short 1h holds) is
  material but not decisive.

### Finding 3 — The gate sees the tail; the limitation is power/adjudication, not gate shape

- **Observation:** in the 4h cells net **median ≫ net mean** (e.g. USDCAD/D1: net_med 3.98 vs net_exp 1.17),
  i.e. the catastrophic left tail persists after cost.
- **Interpretation:** the binding **expectancy ∧ median** gate is appropriately **tail-aware** — the mean leg
  incorporates the catastrophic losers, so `net_exp_lo > 0` means the mean survives the tail and the cost. This
  is unlike the EXP-074 all-framing consistency gate that was structurally blind to tails. The real limitation
  is **statistical power and separability adjudication**: at n=77 the bootstrap lower bound on the mean clears
  zero despite the tail because the gross magnitude is large, and **S2 (the dedicated catastrophe-separability
  guard) was deferred on every survivor (n<120)** — so whether the persisting tail is survivable is precisely
  what these cells have never tested.

## Hypothesis Verdict

**`NET_SURVIVES`** (predeclared rule, rule-correct) — **qualified per stratum.**

≥1 survivor clears the net conjunction on TRAIN, so by the scope's predeclared definition the verdict is
`NET_SURVIVES` and the 21 `NET_POS` form the **read-eligible set** (`results/valid_net_set.json`). The honest
per-stratum reading is the binding one: **the read-eligible set is entirely shape-unadjudicated, low-n (n=44–78)
4h `SUB-AVWAP` cells; the only S2-PASS, well-powered stratum (AUDUSD-1h, n=988) is net-inconclusive (median leg
fails).** Cost was not the eliminator the prior families saw — but the net-positive signal does not coincide
with the cells the programme has adjudicated or powered.

**This experiment authorizes nothing.** It is a read-gate input to the operator's G-018 decision. Per the scope
and D0-amendment-002, an EXP-084 counted TEST read opens **only** on (a) `NET_SURVIVES` (met) **and** (b)
additional operator ratification at EXP-084's own D0. The net matched-random excess companion (positive in all
26 cells) is **non-binding disclosure** and carries no weight in this verdict.

## Limitations

- **Read-eligibility ≠ tradability.** All 21 read-eligible survivors are S2-DEFERRED: their separability /
  catastrophe-tail question was never adjudicated (n<120). Net-positive on TRAIN at low n is weak evidence.
- **Small-n CIs.** n=44–78 for the 22 4h survivors → wide intervals; VP-POC (n=44) and USTEC-RR-1 (n=46) are
  below the EXP-077 Guard-(i) n≤60 threshold where the percentile-bootstrap **expectancy** CI is known to
  under-cover (EXP-076). Per the audit this is **non-material here** because the binding rule requires the
  robust **median** leg too, and those cells clear it (med_lo 1.48 and 0.78 respectively) — so requiring both
  legs is conservative and no verdict moves. But it caps confidence in the expectancy leg at small n.
- **ATR-unit framing.** The favourable cost/ATR ratio on 4h is partly a real economic effect and partly a
  normalization artifact; a price-/notional-unit cost frame would shift the relative cost burden.
- **TRAIN-only.** No referee suite, no WF-EXPANDING, no TEST/holdout contact. This is robustness eligibility,
  not confirmation.
- **VP-POC (USDCAD-4h)** carries EXP-083's disclosed selection-on-geometry caveat (POC subsample, n=44).

## Alternative Explanations

- The 4h net-positivity could be **small-sample inflation** of the gross magnitude (ASS-overlay-flagged) rather
  than a durable edge — consistent with the well-powered AUDUSD-1h cell failing the median leg.
- The AUDUSD-1h median-leg miss (med_lo just below 0) could be marginal noise rather than a true null; only a
  counted read (or more TRAIN power, unavailable) could separate these — which is exactly the G-018 question.

## Recommended Next Steps (new scopes only — not extensions of EXP-085)

These are **inputs to the operator's G-018 read decision**, framed as candidate new scopes, not a recommendation
to spend a lifetime TEST read:

1. **G-018 decision input — where would an EXP-084 read even point?** The net survivors (shape-unadjudicated
   low-n 4h) and the shape-guarded well-powered stratum (AUDUSD-1h, net-inconclusive) are disjoint. A counted
   read on the 4h survivors would test cells whose separability is unknown and whose magnitudes are small-n
   inflated; a read on AUDUSD-1h would test a stratum that already fails the median leg on TRAIN. Neither is a
   clean confirm target — material for the operator's decline-vs-ratify call at G-018.
2. **(new scope, if a read is ratified)** A narrowly-scoped EXP-084 confirmation under the frozen cost-calibrated
   referee suite, with the binding stratum and Holm family fixed in its own D0 — explicitly choosing between the
   shape-guarded AUDUSD-1h cell and the shape-unadjudicated 4h survivors, not pooling them.
3. **(new scope, TRAIN-only, no read)** If the operator declines the read, a TRAIN-only S2 power-extension or
   notional-unit cost reframing could test whether the 4h net-positivity is separability-survivable and
   robust to the cost-frame choice before any read is ever contemplated.
