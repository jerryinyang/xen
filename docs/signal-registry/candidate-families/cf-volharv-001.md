# CF-VOLHARV-001 — Two-Sided Oscillation/Volatility Harvest

**Status:** `RETIRED (2026-07-05, checkpoint-008 retrospective, operator-signed).` Both core
hypotheses closed negative — HYP-001 ARTIFACT_CONFIRMED (founding anomaly is a draw),
HYP-002 NOT SUPPORTED (EXP-020: neither rebalance nor grid harvests the real FX-block
oscillation at scale — a capture-geometry / cadence-collapse failure, not clean substrate
absence). 0 slots, 0 counted reads, holdout sealed lifetime. A *different* within-episode-
clearing structure (rolling anchor / no hard cap) on an unseen band would be a NEW family with
its own D0, not a re-open of this one. Prior: `REGISTERED (2026-07-04, operator-directed;
falsification-first structure — HYP-001 a kill test of the founding anomaly).`
**Family ID:** CF-VOLHARV-001. **Chapter:** 02 (cTrader-primary era).
**Origin:** convergence of two independent residues — (a) EXP-018's random-timing destroy arm
(NZDUSD rt per-leg +31.5 bps, CI_low +13.7, both directions positive, produced by the
programme's own falsification machinery, `python/experiments/EXP-018/report.md`); (b)
CF-VOLEXP-001's Chapter-01 tail-only long-vol hint (provisionally admitted, never
concretized, `docs/knowledge-base/families-explored.md`). Synthesis:
`.ignore/temp/new-family/analysis-1.md`, `analysis-2.md`. Checkpoint-006 retrospective
explicitly sanctioned the vol-harvest reframing as a new-family route.

## Thesis (two-stage, honestly split)

**Stage 1 (HYP-001 — falsification, prior LOW that it survives):** the EXP-018 anomaly is a
draw, not a property. A fixed-unit, random-direction, random-timing, fixed-hold leg has
**E[gross P&L] = 0 by construction** (the coin flip annihilates drift; no conditioning,
price-dependent exit, or rebalancing channels path structure into the per-leg mean). "Both
directions positive" is impossible in expectation for that object. Reproduction across 25
independent seeds would therefore indicate an artifact (fills/spread/accounting) or an
extraordinary process asymmetry — either way a forensic finding, never a booked edge.

**Stage 2 (HYP-002 — the actual family bet, gated on checkpoint):** structures that CAN
carry nonzero expectation from oscillation — rebalanced-exposure (volatility-pumping) and/or
symmetric always-on grid objects — earn positive expectation on range-persistent instruments
net of double-sided spread + swap, at a capped inventory, versus their own unconditioned twin
and exposure-matched two-sided B&H. Design contingent on HYP-001's measured swap-inclusive
cost floors and VR/oscillation substrate profile.

## Binding first-branch constraints (operator-agreed 2026-07-04)

1. Causal construction only: ex-ante cadence, exogenous hold grid {6,12,24,48}, fixed unit,
   no ladder adds, no borrowed live-arm distributions (the EXP-018 rt schedule's post-hoc
   template/hold borrowing is exactly what a candidate run may NOT do).
2. Multi-seed (25/instrument), engine-run, m1 fills; schedules provably price-independent
   (regenerable from seed + bar calendar, byte-diff at QA).
3. Episode/seed-level inference; leg-level CIs under clustering known-optimistic
   (checkpoint-006 lesson-candidate).
4. Swap/financing charged from a declared, version-pinned analysis-layer table (1× binding,
   2× stress always shown) — new `xen.evaluation` component, built before any read.
5. Primary comparator for any HYP-002 claim: its own unconditioned twin + exposure-matched
   two-sided B&H; predeclared inventory cap; exposure-honest normalization (avg + peak).
6. Collapse fractions disclosed for every control (L-15); pooled figures disclosure-only
   (L-03); UNPOWERED never read as negative (B-5).
7. TRAIN-only throughout the first checkpoint: 0 slots consumed at screen stage, 0 counted
   TEST reads, holdout sealed.

## Distinctness from retired families (P-01/P-02 compliance)

Not a dislocation-fade: no entry conditioning on price state at all (HYP-001), or
structure-borne expectation with no directional forecast (HYP-002). Not a re-parameterisation
of CF-MR-002..005 (all entry-conditioned directional reversion claims). The pitfalls-ledger
re-open standard — "a genuinely new mechanism, not another price-pattern on a directional
target" — is met: the target class is path-structure harvest, two-sided, magnitude-shaped.

## Hypotheses

| ID | Question | EXP | Status |
|---|---|---|---|
| HYP-001 | Is the EXP-018 rt per-leg positive reproducible across 25 ex-ante seeds (16 instruments × hold grid), or an artifact as the symmetry null predicts? Plus: swap-inclusive carrying-cost floor + VR substrate profile (disclosures). | EXP-019 | COMPLETED 2026-07-05 — SUPPORTED / ARTIFACT_CONFIRMED (operator verdict); `python/experiments/EXP-019/report.md` |
| HYP-002 | Do rebalanced-exposure / grid structures earn net-positive oscillation harvest vs unconditioned twin + exposure-matched B&H at capped inventory? | EXP-020 | COMPLETED 2026-07-05 — NOT SUPPORTED (operator verdict), USDCAD flagged; `python/experiments/EXP-020/report.md`. Family disposition deferred to checkpoint-008 retrospective (operator-signed) |
| HYP-003 | CF-VOLEXP-001 tail-only long-vol concretization under the two-sided harvest model. | — | DEFERRED — not scoped this checkpoint |

## Kill criteria (predeclared, checkpoint-level)

- HYP-001 ARTIFACT_CONFIRMED **and** HYP-002's design inputs show no instrument where
  plausible harvest (from measured VR/oscillation amplitude) clears 1× swap + double-sided
  spread → family retires at the checkpoint retrospective having spent 0 reads, 0 slots.
- Any tripwire failure (schedule data-dependence, fill-causality) → REJECT the run, fix,
  rerun; never book around it.
- 2022-concentration or top-k-episode funding of any HYP-002 positive → carry attribution
  per EXP-018 precedent, not a harvest claim.

## Evidence ledger

| Date | Item | EXP | Result |
|---|---|---|---|
| 2026-07-04 | Registration; HYP-001 design | EXP-019 | design.md written; QA + operator execution gate pending |
| 2026-07-05 | HYP-002 structure-harvest screen complete (operator verdict NOT SUPPORTED, USDCAD flagged) | EXP-020 | Neither structure earns net-positive harvest across the MR block. **ARM R** (banded rebalance vs never-rebalanced twin): all 4 MR cells tiny-positive but **UNPOWERED** (MDE > effect; design §8 over-stated the classical w(1−w)σ² premium ~100×, true ~0.04–0.07%/yr); only US2000 (mid, disclosure) CI-positive. **ARM G** (MR grid vs momentum twin, drift-robust spread): MR-block scoreboard 1/4 — USDCAD +132 bps/mo CI[+43,+257] survives commission/weekend-×4/top-3/both-halves **but** fails the inverted-twin sign-flip (momentum twin +3,491) and the 60% cleanliness bar (2022 = 67% of funding); NZDUSD −56, GBPUSD wash, AUDUSD −104 (momentum twin beats MR grid). Realized RT mean = +g every cell (mechanism real) but **rare**. **Structure failure, not substrate absence:** fills at 5–28% of A1-implied cadence, 3/4 MR cap-locked, NZDUSD dead after 2022-04; censored ≤8-leg inventory erases 100–155% of realized harvest (VAL-006). Tripwire 1 graceful (ratios 1.01–1.06); +2 bps plant detected pre-read; RW-block alarm scan clean (USDCHF spread CI-negative, BTCUSD drift-contaminated level read). Verdict robust to the hardened `block_bootstrap_ci` re-run (INFR-004/L-20; 2 immaterial temporal-half flips). **Net-at-live-spread BLOCKED** (spread pin carried blocker; EURJPY unpinned even at ceiling). Under UNPOWERED discipline this does NOT license "no oscillation harvest exists." 0 slots, 0 counted reads, holdout sealed. `python/experiments/EXP-020/{report,analysis}.md` |
| 2026-07-05 | HYP-001 falsification complete (operator verdict SUPPORTED / ARTIFACT_CONFIRMED) | EXP-019 | EXP-018 rt positive = sampling draw: NZDUSD battery ≈ 0 in all hold strata (\|mean\| < MDE 1.4–5.3 bps); +31.5 above the entire 25-seed distribution ([−11.5,+8.6] pooled seed means); 2/64 strata beyond MDE (≈ chance); direction splits drift-shaped; BTCUSD-48/EURUSD-12 WASH; BTCUSD H∈{12,24,48} UNPOWERED. Tripwires clean (byte-exact regeneration; fills never early; delay twin max pair-diff +0.74 bps). 441 runs, 286,476 legs, 0 censored, estimand gates blocking_pass. **HYP-002 design inputs booked:** cost floor = FTMO commissions (FX 0.47–1.04 bps RT, BTC 13.0, indices 0; **spread unpinned — pin from live FTMO page before any binding cost read**; A5 superseded the swap table per operator directive) + VR substrate (FX block genuinely MR: NZDUSD 0.92/0.88/0.80/0.80 at H=6/12/24/48, AUDUSD →0.76, GBPUSD/USDCAD similar; BTC/JPY/gold/CHF ≈ RW). Kill-criterion input: oscillation exists in FX but is not harvestable unconditioned — HYP-002 viability turns on whether structure (rebalance/grid) clears the measured floor on the MR block. 0 slots, 0 counted reads, holdout sealed. `python/experiments/EXP-019/{report,analysis}.md` |
