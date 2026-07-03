# EXP-014 — CF-MR-004 / HYP-002: faithful full-exit cross-instrument MR (report)

**Family:** CF-MR-004 · **Phase:** 004 · **Type:** price-primary full-strategy screen (availability + net, TRAIN)
**Verdict:** **NOT_TRADABLE** (faithful, powered on the bite-passing subset) · **Audit:** PASS (0 Critical)
**Reads/slots:** 0 counted TEST reads, 0 slots · **Holdout:** sealed · **Referee:** frozen 4h, untuned (L-12)
Artifacts: [design.md](design.md) · [code/](code/) · [audit.md](audit.md) · results/{verdict,mr_characterisation}.json · plots/

## 1. Question

On the 4h anchor domain, does the **faithful full-exit** precalc limit-order cross-instrument MR-fade
strategy (4 series S5/S6/S7/S8; form-1 event-reversion **and** refreshing form-2 anchor-mean limit;
horizon last-resort; reentry + trend/vol conditioners) produce (a) reversion-to-anchor beyond a
dislocation-matched control (availability) AND (b) a net-positive per-stratum edge under the frozen 4h
referee (tradability) — and if not, **which leg fails where**? This is the faithful redo of EXP-013,
whose NOT_TRADABLE was downgraded CONFOUNDED (form-1 absent + form-2 frozen at entry — L-14).

## 2. Scope

- **Price-primary, in-engine** (cTrader `Mode=NativeOrders`, m1 fills own resolution; Python analysis-only, L-01/P-09).
- 4 series × 4 arms = 16 confs, **152 cells**, all TRAIN (first-49% `AnalysisEndUtc` fence = EXP-013 cutoffs); final-30% never loaded.
- Binding = **PRIMARY none/R** (reentry=none, refresh); disclosure = none/S (A/B), allow/R, extend/R.
- Strata: `(series, instrument, 4h)` — S5/S7/S8 11 cells (FX+idx baskets), S6 5 pairs = **38 binding cells**.
- 0 counted TEST reads; frozen referee never tuned.

## 3. Method

Native resting bracket at `exp(anchor±2σ)` (band is the trigger, no z-gate — z provenance-only). **Faithful
exit set:** (1) **form-2** favorable limit at the moving anchor mean, **refreshed every 4h bar** (favorable-
placement asserted before each modify); (2) **form-1** event-reversion — close at next bar open when the
spread reverts through the mean (`logClose − anchorLog` crosses 0); (3) **horizon** `min(48,3·HL)` last-resort.
Multi-leg netting engine (none≤1 leg; allow refills base band; extend arms z\*∈{2.0,2.5,3.0} ladder). Min-mate
rule (basket bar valid only with full predeclared membership). Per-4h-bar realized NET series (engine fills,
intra-position MTM, RT cost once/entry from the frozen per-instrument 4h cost map) → frozen referee
`referee_pstar.gate_stack_pstar` per stratum; cross-axis Holm. Availability = native reversion-completion
(reach-anchor / fraction-recovered / time-to-anchor ÷ HL) vs a **dislocation-matched** matched-random control.
6-stage MR screen (robust-detrend, lag-1 autocorr, VR, ADF, KPSS, AR(1)/OU HL) **booked before verdict contact** (§7).

## 4. Results

### 4.1 Tradability (binding, PRIMARY none/R) — NOT_TRADABLE

**0/38 net-admit AND 0/38 gross-admit.** Every stratum: referee `passed=False`, `ci_lower_bps < 0`, gross and net.
**Homogeneous — no masking:** an independent sweep finds **zero** cells with net `ci_low > 0` (L-03 satisfied).

| Series | cells | powered (L1∧epi≥8) | net-Holm-admit | net bps/active range |
|---|---|---|---|---|
| S5 (rolling-β basket) | 11 | 8 | 0 | −1.31 … +0.57 |
| S6 (fixed pair) | 5 | 3 | 0 | −1.61 … +0.56 |
| S7 (fixed basket) | 11 | 7 | 0 | −2.31 … +0.86 |
| S8 (basket−median-90) | 11 | 6 | 0 | −1.41 … +0.39 |

Point estimates straddle 0 (net −2.3…+0.9 bps/active); all CIs cover/exclude-below 0. See `plots/net_vs_gross_per_cell.png`.

### 4.2 Faithfulness — the two proposal-named exits fired (L-14 discharged)

Exit-reason split (engine `cis_trades`), PRIMARY none/R, 3445 trades: **form-1 281 · form-2 (refreshing) 1898 · horizon 1266.**
Refreshing form-2 is the **dominant** exit (55%) — peer-side reversion now exits (EXP-013's frozen-TP defect gone);
form-1 adds 8%. Disclosure arms confirm the exits scale with reentry (none/S 321/968/364; allow/R 799/6591/5676;
extend/R 1469/12282/11145). **This is a verdict on the faithful strategy, not a vehicle-incomplete one.** `plots/exit_leg_split.png`.

### 4.3 Availability — does not separate at 4h

Native reversion-completion Δ (cond − dislocation-matched control) has **`ci_low < 0` on ~all 38 cells**;
the largest positive point estimates are ≤ +0.036 (S7:USDCHF hitΔ +0.036, S8:USDCHF +0.019) with CIs covering 0.
Among equally-dislocated bars the screen does **not** pick better reversion. `plots/mr_characterisation.png`.

### 4.4 MR screen (informative, not gating)

VR<1 broadly — S7/S8 FX baskets strongly reverting (VR 0.27–0.37), S5 near 1 (0.95–1.00), **S6 pairs near
random-walk** (VR≈0.94–1.03, HL 139–3173 4h-bars). S8 basket−median short HL (2–10). ADF/KPSS mixed
(structural — not a clean stationary/non-stationary split). Reversion *structure* exists in the baskets, but
does not convert to capturable, cost-surviving edge.

## 5. Interpretation

**The faithful full-exit cross-instrument MR fade is a net wash at 4h, and its availability does not separate
from a dislocation-matched control.** With form-1 + refreshing form-2 both live (fixing EXP-013), positions exit
on price-side *and* peer-side reversion — yet per-trade P&L is a **dispersed wash** (`cis_trades.RealizedBps`
−57…+29 bps/trade; several cells positive per-trade but net `ci_low<0` because dispersion swamps the mean). The
capturable reversion is not reliably larger than the round-trip cost — the **same cost/capture veto** that closed
CF-MR-002 (EXONERATED) and CF-MR-003 (RETIRED). Mechanism = capture-vs-dispersion, not a single failing leg.

**Strength / caveats (do not overclaim):**
- **Powered on the bite-passing subset.** A planted +8 bps edge is detected in **19/38** cells; the 19 bite-*failing*
  cells (high-cost indices US500/USTEC/JP225/US2000 cost 3–5 bps + low-episode FX) have no finite power at that size,
  so their rejection is *unpowered*, not *effect-absent* (L-12 mode-2; the per-bar mean-referee is a partial
  gate-shape mismatch for a discrete, high-variance round-trip bracket — amendment §7 vehicle-fit risk). The credible
  null rests on the bite-passing powered cells, which **also all reject**.
- **Availability itself does not separate** — so this is *not* "availability real but uncaptured"; it is "faithful
  full-exit is a net wash **and** the 4h reversion signal does not beat matched-random."
- **Terminal-branch:** a stronger null than EXP-013 could give (that run was vehicle-incomplete), tempered by the two
  caveats above. Cross-instrument price-derived MR at 4h adds no tradable edge here.

**Result category: NOT_TRADABLE (TRAIN, faithful).**

## 6. Audit caveats (from [audit.md](audit.md) — PASS, 0 Critical)

- Numeric reproduction ✓ (indep re-derivation ≤0.05 bps). Causal-provenance ✓ — all decisions ≤ t-1, open-to-open,
  engine-realized fills, no `rct[di]` pattern, no vectorized price backtest. Fence sealed; exit-fill breach 0–0.7%
  (isolated, benign). Min-mate MateGap 0.04–0.19%.
- Leak tripwires **moot** (0 admits): T1 peer-feed phase-shift not generated (only needed on an admit); T2 label-perm
  correctly flagged **mean-invariant/vacuous**, not gating. Binding future-destroy (T1) to be exercised only if a
  future cell admits.
- 2 Warnings (availability-not-separating; per-cell power heterogeneity) — interpretation-framing, **non-verdict-moving**.

## 7. Conclusion & follow-ups

CF-MR-004 tradability is **NOT_TRADABLE on TRAIN** with the faithful full-exit set + conditioners. The exit-set
confound that downgraded EXP-013 is fixed; the null is now a real (if power-caveated) family reading.

**Disposition (registry):** CF-MR-004 → recommend **RETIRED** (availability does not separate + net wash at 4h,
faithful vehicle). **Retiring a candidate family is operator-gated** — awaiting operator sign-off; until then
CF-MR-004 stays REGISTERED with the HYP-002 faithful-null booked.

**Follow-ups (separate experiments, if the operator does not retire):**
1. Lower-cost universe / cheaper capture (the only re-open condition from cf-mr-003) — 4h indices are cost-3-5 heavy.
2. A per-trade / episode-native referee variant co-designed for a discrete round-trip bracket (would need its own
   predeclared FPR calibration + freeze before judging CF-MR-004 — L-12; not a rescue of this run).
3. Lower anchor domain (1D deferred; needs referee-domain extension) — but the cost/capture veto is the binding wall.

## GATE (post-exec)

**GATE: APPROVE** (orchestrator, 2026-07-02).

Confirmed:
- **Verdict forensics present** — per-stratum re-derivation (PRIMARY none/R, 38 strata), mechanism stated
  (capture-vs-dispersion wash), gate-shape check (per-bar mean referee vs discrete round-trip bracket).
- **Causal-provenance & leak pass present** — every verdict-bearing column traced ≤ t-1 (open-to-open,
  engine-realized EntryFillPrice/ExitFillPrice, no Python edge recompute); leak tripwires moot (0 admits),
  label-perm correctly flagged mean-invariant/vacuous.
- **Per-stratum masking check done** — 0/38 net ci_low>0, homogeneous; no pooled figure hides a separating
  stratum (L-03).
- **No verdict-material finding outstanding** — audit PASS, 0 Critical (2 Warning, 3 Info, all shown
  non-verdict-bearing). Faithfulness discharged (L-14): both proposal-named exits fired.
- **Registry disposition recorded** — see below; candidate status advanced (HYP-002 NOT_TRADABLE booked),
  multiplicity outcome entered, 0 counted TEST reads / holdout sealed / referee untuned.

Operator-gated item held open: **RETIRE CF-MR-004** (retiring a candidate family is a critical decision —
recommended, not executed; family stays REGISTERED until operator sign-off).

## Signal-registry disposition

registry-relevant: **CF-MR-004 HYP-002 → NOT_TRADABLE (faithful, TRAIN)**; RETIRE recommended, operator-gated.
`multiplicity-registry.md`: EXP-014 outcome entered (0 counted reads, TRAIN disclosure). `test-read-ledger.md`:
unchanged (0 reads). `candidate-families/cf-mr-004.md`: HYP-002 result booked; EXP-013 CONFOUNDED record retained.
