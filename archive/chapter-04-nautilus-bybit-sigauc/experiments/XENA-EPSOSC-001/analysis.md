# Data Analysis: XENA-EPSOSC-001 (CF-EPSOSC-001, VOLARM episode-fade)

Analyst pass on emitted raw artifacts (2026-07-18). Interrogates the certification
evidence package, stage-2 gate, seed battery, economics, estimand gate. **Search/certify +
stage-2 done; no TEST gate.** All numbers below trace to `results/*.json` / `.csv` and
`data/nautilus_runs/XENA-EPSOSC-001/`.

## 1. Integrity gate

| Check | Result | Evidence |
|---|---|---|
| Estimand validation (all 464 binding cells blocking_pass) | **PASS** | `estimand_validation_summary.json` n_cells_blocking_pass=464/464; fail_breakdown all 0; reconciliation abs_diff ~3.6e-12 bps |
| Provenance ≤ t-1 (features + membership) | PASS (code-asserted) | design §2/§4.1; not independently re-derived here — see open Q |
| **Leak tripwire (episode-label DERANGEMENT §8)** | **RUN — formal top-1 FAILS** | `analysis_code/derangement_tripwire.py` → `results/derangement_tripwire.json`; L-29 anchor `anchor_ok=true` (recon reproduces emitted bps, median err <5 bps). See §1a. |
| Holdout untouched | PASS | gate band ends 2023-12-18; TEST/holdout 2023-12-18→ not read; `final_gate.run=false` |
| Price-primary (Nautilus binding, non-STUB) | PASS | 464 binding emissions; gate v2 fence_fail=0, catalog_fail=0 |
| No experiment-local accounting | PASS | `no_local_accounting.ok=true` |

### 1a. Leak tripwire results (design §8 — HARD: collapse < 0.5 ⇒ REJECT, no override)

Alignment-destroy: preserve each leg's duration + side, derange entry slots (zero fixed
points, L-28), re-price entry from exact emitted fill of the deranged slot + marks exit,
200 seeds, gate-band legs. `collapse = 1 − deranged_median / real_recon_mean`.

| Finalist | n_legs | real (bps/ep) | deranged med | **collapse** | survival ≥½ | verdict |
|---|---|---|---|---|---|---|
| **#1 AKRO W192 k3 HYBRID S** (formal top-1) | 25 | 161.1 | 97.5 | **0.395** | 0.57 | **FAIL — REJECT-class** |
| **#3 AKRO dual RET_ANCHOR S** | 52 | 172.1 | 66.8 | **0.612** | 0.38 | **PASS** |
| #5 AKRO RET S + RSR HYB L | 25 | 172.0 | 92.9 | 0.46 | 0.52 | INVALID (RSR <2 gate legs → cell can't self-derange) |

**The formal one_subset top-1 fails the leak tripwire** (collapse 0.395 < 0.5): ~60% of its
gross "edge" survives destroying the signal→price alignment. Per design §8/§14 this is
**REJECT-class, no operator override** — the HYBRID singleton's edge is majority
directional-drift artifact, not the VOLARM signal.

**Non-obvious pedestal caveat (why collapse is low even for the survivor):** all three
subsets are single-symbol shorts (AKRO) in a 2023 downtrend. The *unconditional* short
return over that window is positive, so derangement cannot destroy the drift component — a
**directional-drift pedestal (~half the edge)** floors the collapse. This is itself evidence
that the single-symbol AKRO edge is **inseparable from AKRO's 2023 decline**. Only **#3
(RET_ANCHOR)** clears 0.5, and only modestly — the endogenous-clear variant is the one whose
edge actually depends on signal alignment; the HYBRID time-cap edge is mostly drift.

**Integrity verdict:** tripwire executed. **Formal top-1 = REJECT-class.** The only finalist
that both net-passes AND survives the tripwire is **#3 (AKRO dual RET_ANCHOR short)** — and
even it sits on a drift pedestal. Any claim must move off the formal winner onto #3, as
disclosure, with the single-symbol/drift caveat attached.

## 2. Headline (formal top-1, one_subset pin)

`AKROUSDT__VOLARM__15m__W192__k3__HYBRID__S` — **singleton short, one symbol.**
Stage-2 gate band (2023-06-20→2023-12-18), seed=42, n_legs=25:

| | LCB | point | SE | boot_median | pass |
|---|---|---|---|---|---|
| Gross | +31.2 | 179.2 | 103.3 | 175.3 | ✅ |
| Net | −2.3 | 160.5 | 107.3 | 168.4 | ❌ |

Costs shave only ~19 bps off the point (179→160). The net FAIL is driven by **SE≈107 on
n=25**, not by cost magnitude — the LCB machinery, not the edge, fails.

## 3. Evidence FOR the hypothesis

- **Point edges are large and cost-robust.** Gross point 179 bps/ep, net point 160
  bps/ep. Cost drag ~19 bps ≪ edge. Pre-search floor: 411/464 cells ≥ breakeven, binding
  median gross 121 bps/ep.
- **Endogenous-clear (RET_ANCHOR) variants are the strongest net performers**, which is
  exactly the design mechanism (within-episode reversion). Both stage-2 **net-passes** are
  RET_ANCHOR-led: #3 (AKRO W192 dual RET S, net LCB +7.05) and #5 (AKRO RET S + RSR HYB L,
  net LCB +12.1). The pure-endogenous-clear thesis is the part that survives net.
- **AKRO edge is deep, not a 25-leg fluke.** Full-TRAIN physicality: 120 legs / 1.56 yr,
  occupancy 0.156 (genuinely episodic, NOT a grid — P-12 clear), Sharpe 1.36, total net
  +23,006 bps, reconciliation exact.
- **Reproduces SPDR-005 direction.** SHORT-side VOLARM fade on high-turnover alts; median
  lift is real where mass exists.

## 4. Evidence AGAINST the hypothesis

- **Gross pass is MC-fragile — it is a coin-toss on the bootstrap seed.** Rank-1 seed
  battery (10 seeds, same 25 legs):

  | | pass rate | LCB range |
  |---|---|---|
  | Gross | **0.80** (8/10) | **−3.7 … +31.2** (straddles 0) |
  | Net | **0.10** (1/10) | −24.2 … +7.3 |

  Per CI hygiene (INFR-004/L-20): `ci_low_seed_range` straddles zero ⇒ the gross gate read
  is **MC-fragile, not significant**. The +31.2 at seed=42 is the lucky draw, not the
  central tendency. n=25 is simply too thin for a leg-studentized LCB.
- **Net is effectively dead** on the formal winner (1/10 seeds). L-22 → no deployability.
- **Certification crowned the fragile, non-deployable subset.** Ranking is by **median
  fold-F on g_net**, which hides worst-fold. Top-1 (HYBRID S) fold_F = [**17.5**, 262, 276]
  — worst fold barely positive — yet won on median 262. Rank-3 (RET dual) fold_F = [154,
  232, 279], worst-fold **9× more robust**, AND net-passes. **The median-fold rule selected
  the weakest passing candidate on the deployability axis.** The formal one_subset winner is
  arguably the worst of the survivors.
- **HYBRID vs RET_ANCHOR is thesis-adverse for the winner.** The time-cap (HYBRID, H=W)
  forces exits the endogenous thesis would let revert → fatter tail → higher SE → net fail.
  The winner is HYBRID; the net-passers are RET_ANCHOR. The ranking picked the variant that
  least matches the mechanism.
- **The whole search is essentially an AKRO detector.** 10/12 finalists contain AKRO.
  Per-symbol median gross (search band): AKRO **349** bps vs #2 REEF 143, HOT 94, STMX 86,
  XEM 78 — AKRO is a **2.4× outlier**. Pooled universe median gross = **18 bps** (a wash;
  mean 2.5 bps, frac>0 = 0.55). SPDR-005's "concentrated cluster, not broad availability"
  collapsed here to **near-single-symbol** availability (SPDR had 4).
- **Search band predates the mechanism's mass.** Search segment = 2021-06-29 → 2022-06-24;
  design states effective VOLARM mass starts **~2022-07** (caveat 4). The search band ends
  *before* the mass begins. **176/464 cells (38%) had zero legs on the search band**; only
  **18 of 29 symbols** contributed (all newer memecoins — BONK/PEPE/SHIB1000/DOGE/GALA/RSR/
  SLP/LADYS/BTT/JASMY/LEVER — were empty). The winner was picked on the sparsest, oldest
  slice; whatever had 2021 episodes (AKRO) got found.
- **Diversification mitigation did not fire.** Design §10 says "portfolio pooling is the
  powered path." The certified top-1 is a **singleton in one symbol** at n=25 — the exact
  underpowered single-cell case the design predicted would be fragile. The pooled/diverse
  subsets rank *below* it.

## 5. Anomalies & open questions

- **Derangement tripwire not executed** (blocking; §1). Must run before any claim.
- **36/464 cells carry non-physical sanity flags** (|ann.return|>100%/yr, 4 cells Sharpe
  3.3–3.8) — memecoin thin-tail artifacts; disclosure, but the winner's cohort lives here
  (AKRO ann.return 147%, maxDD −66%).
- **Identical fold_F values across subsets** (e.g. 262.21, 275.84 recur) confirm the
  portfolio functional is **driven by the single AKRO cell** wherever present — the
  "portfolio" is AKRO plus noise.
- **block_legs_used=1 for the singleton winner** vs 5 for rank-3: the winner has no
  overlapping-episode structure, so the overlap-block guard is inert on it.
- Provenance (t-1 features, causal membership) is code-asserted but not independently
  re-derived by this analyst — suggested probe if the operator wants it hardened.

## 6. Tier-B reframe (bounds the claim; no new emission)

Applied per operator instruction (mitigate #2/#3/#4 by correct reporting):

- **#2 median-fold ranking is a pin-level defect, not a result.** The formal one_subset
  top-1 is now known **REJECT-class** (tripwire). The ranking rule (median fold-F) selected
  it over the tripwire-passing #3. **Recommendation: the object of record is #3 (AKRO dual
  RET_ANCHOR short)**, carried as disclosure. Median-fold-vs-robustness gap logged for the
  next CLS-EPISODE CAL cycle (do not re-derive the pin here).
- **#3 HYBRID vs RET_ANCHOR — mechanism-confirming.** RET_ANCHOR (pure endogenous clear =
  the thesis) is the ONLY variant that clears the leak tripwire; HYBRID's time-capped edge
  is drift. The data supports the endogenous-reversion mechanism and rejects the time-cap
  variant.
- **#4 concentration — hard bound.** Claim scope = **one symbol (AKRO), short side, 2023
  window**. Pooled universe median gross = 18 bps (wash). No universe-level VOLARM
  availability claim is supportable. BONK/BTT/PEPE/late-listed strata excluded from any
  centre (design caveat 2).

## 7. Recommended verdict (experiment hypothesis only — NOT final, NOT family)

- **Recommendation: NOT SUPPORTED as a deployable/universe result; INCONCLUSIVE-CHARACTER
  for a single-symbol RET_ANCHOR object.**
  - Formal top-1 is **REJECT-class** (leak tripwire collapse 0.395 < 0.5, §1a).
  - The only survivor (#3, AKRO RET_ANCHOR dual short) net-passes at seed=42 and clears the
    tripwire at 0.612 — but on a **directional-drift pedestal**, in **one symbol**, with a
    **seed-fragile** LCB and a **search band that predates the mechanism's mass**.
- **Driven by:** (1) tripwire — formal winner fails, only RET_ANCHOR #3 survives, and only
  modestly on a drift floor; (2) seed battery — gross LCB range −3.7…+31 (straddles 0), net
  1/10; (3) AKRO-only concentration + pre-mass search band → an AKRO-2023-downtrend detector,
  not a VOLARM-universe edge.
- **Would change if:** a mass-aligned, multi-symbol re-run (XENA-EPSOSC-002) reproduced #3's
  edge on legs whose derangement collapses cleanly (no single-symbol drift pedestal) with a
  seed-stable LCB. That is Tier-C (new design), not fixable here.
- **Do NOT spend a TEST slot.** The formal top-1 is REJECT-class; #3 is single-symbol,
  drift-pedestalled, seed-fragile. A counted read here buys no information (L-22).

Final verdict is the operator's. Tier-A (leak tripwire) + Tier-B (reframe) are DONE. The
structural fixes (#1/#5/#6 power + band-mass) require XENA-EPSOSC-002.
