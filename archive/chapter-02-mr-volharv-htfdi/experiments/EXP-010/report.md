# EXP-010 — CF-MR-003 CONC-1 Track 1 · REPORT

**Family:** CF-MR-003 (SCREENED-ADMIT, EXP-009) · **Phase:** 003 · **Type:** tradability screen (net, TRAIN,
price-primary in-engine) · **Date:** 2026-07-01 · **Audit:** PASS, 0 Critical.
**Outcome:** **NOT-TRADABLE (UNPOWERED)** — the S5_SPREAD availability edge does **not** survive to net under the
frozen referee. Family retained; terminal-branch prior reinforced.

## Question (one)
On the EXP-009-admitted S5_SPREAD exec-1h strata, does the concretized **form-2 limit-at-anchor fade**
(exec-grid-β anchor; live-limit entry at the `|z|=2` band; favourable limit exit at the anchor mean; horizon
market fallback; `/REENTRY`=none) produce a **net-positive** per-bar realized edge (binding-leg cost charged)
clearing the frozen renewed referee (§10.3a q\*=0.75 + E6 P\*-gate, `domain="1h"`) on a majority of powered
strata — or not (honest prior: not)?

## Scope
- **Member set = 5 distinct S5 exec-1h cells** (EXP-009 admits, exec-grid-β; the 1D/4h-anchor label split is
  degenerate for S5 → collapsed): **AUDUSD, GBPUSD, NZDUSD** (FX_MAJORS basket) · **US2000, US500** (INDICES).
- Price-primary, in-engine (L-01): `StrategyHost/CrossDomainMrLimitModel.cs` (anchor/selector/fills all C#);
  Python ingests/adjudicates only. Frozen referee, `domain="1h"`, untouched (L-12).
- **TRAIN-only:** first-49% fence per file (`int(int(N·0.7)·0.7)`); analysis-TEST band + final-30% holdout never
  emitted/loaded. **0 counted TEST reads; 1 candidate slot** (tradability exploration opened).

## Method
Per 1h exec bar (all decisions `≤ t-1`): basket = class-mate mean log-Close (class−self), 1h grid; anchor
`a = β·basket+α` (rolling OLS W_Z=200); `dev = logp−a`; `z = std-z(dev,200)`; selector `VR(4)<0.9 ∧ HL∈(0,48]`;
extreme `|z|≥2`; fade. Entry = live limit at the band edge `exp(a±2σ)`; exit = favourable limit at `exp(a)`;
fallback = horizon `min(48,3·HL)` bars → market close. Cost = frozen per-instrument 1h RT `cost_bps` charged
once per round-trip (binding-leg, L-02). Realized net → `referee_pstar.gate_stack_pstar` → `adaptive_row`;
phase **Holm(5)**. Leak tripwire = phase-shifted basket (`EXP-010-shuffle`, decorrelate basket from price).

## Results (per stratum — L-03; frozen referee domain=1h)

| Cell | entries | episodes | net bps/active | referee ci_low (bps) | L1 (min_state≥20) | L3 | Holm-admit |
|---|---|---|---|---|---|---|---|
| AUDUSD | 77 | 10 | −0.26 | −0.19 | ✗ (3) | FAIL | no |
| GBPUSD | 116 | 23 | **+0.10** | −0.04 | ✗ (11) | FAIL | no |
| NZDUSD | 89 | 22 | −0.26 | −0.11 | ✗ (7) | FAIL | no |
| US2000 | 119 | 18 | −0.70 | −0.56 | ✗ (7) | FAIL | no |
| US500 | 157 | 32 | −0.61 | −0.16 | ✗ (15) | FAIL | no |

- **0/5 powered, 0/5 admit.** The 1h L1 floor requires `min_state_count ≥ 20` per direction/split; all cells
  have 3–17 (too few reversion episodes). `min_effective_n=60` is met (eff_n≈5000) — power fails on **episode
  count**, not series length.
- Net point estimates ~null-to-negative; only GBPUSD is fractionally positive (+0.10 bps) and its CI covers 0.
- **Leak tripwire:** `surviving-under-shuffle = []` → PASS **but non-informative** (see caveats): the live edge is
  already null, so there is nothing for the control to collapse.

## Interpretation (predeclared §8; L-11 discipline)
**NOT-TRADABLE / UNPOWERED.** Read as *"could not test at the required power,"* **not** a positive refutation.
Absolute effect sizes: net −0.70…+0.10 bps/active bar, all CIs overlapping zero, all cells below the referee's
power floor. Mechanism: the form-2 strategy fires only where `VR<0.9 ∧ HL∈(0,48] ∧ |z|≥2` co-occur — a rare
conjunction → 10–32 reversion episodes/cell → below floor. **The EXP-009 availability edge (anchor-hit /
fraction-recovered) does not translate into a net-tradable per-bar edge**: consistent with the honest LOW prior
and the CF-MR-002 exoneration (same broad reversion mechanism, net-negative once causal + cost-charged). No
goalpost move; the availability admit (EXP-009) stands, the tradability question resolves negative-at-this-power.

## Audit caveats (carried as **tradability-gate debt** — non-material here, binding before any future powered positive)
- **F-1 (Medium).** The concretized in-engine vehicle is a **loose replica** of the screened availability vehicle:
  anchor *level* matches `cross_domain_mr` (corr **0.99** → β correct), but the residual `dev` (corr 0.73) and the
  `z`-selector (corr 0.67; |z|≥2 sets Jaccard 0.30) diverge. Drivers: cTrader-native 1h bars (real execution
  prices — correct for tradability) vs m1-aggregation, **plus** basket carry-forward (≤t most-recent) vs the
  design/substrate exact-`CloseTime` join. Non-material to UNPOWERED (episode sparsity is invariant to which
  extremes fire; both vehicles are equally sparse), but **must be reconciled** before any powered-positive booking.
- **F-2 (Low).** Leak tripwire **vacuous** on a null edge → leak-resistance of this vehicle is **UNTESTED**
  (the phase-shifted control was in fact more positive, unpowered noise). Must be exercised on a future powered
  positive.
- Causal-provenance PASS (decide-before-fold, `≤ t-1`; fills executable, all within `[Low,High]` after the
  smoke-caught gap-through fix; fence sealed 0/… rows at/after `AnalysisEndUtc`); price-primary in-engine
  confirmed; frozen referee untouched; shared-module additions NaN-default (other models unaffected).

## Conclusion
**CF-MR-003 CONC-1 (S5 exec-1h) = NOT-TRADABLE (UNPOWERED, TRAIN, net).** Availability → net erosion; terminal-
branch prior reinforced. Family **retained** (not refuted): the read is unpowered, not a positive against.

## Follow-ups (new scopes; not extensions)
- **EXP-011 (E7)** — referee 15m-domain extension → unblocks **T2a** (14 S3 exec-15m, single-symbol) + **T2b**
  (10 S5 exec-15m). Higher-turnover 15m cells may clear the episode floor the 1h cells missed.
- **CONC-1 fidelity reconciliation** (if any arm powers positive) — align basket construction (exact-join vs
  carry-forward) + document cTrader-bar vs m1 source; re-exercise the leak tripwire on the powered cell.
- No `/TARGET`=opposite-extreme / `/REENTRY` sweeps on a dead entry (P-02).

## Artifacts
[design.md](design.md) · [code/](code/) (+ [code/README.md](code/README.md) code map) ·
[audit.md](audit.md) · results/verdict.json · emissions `data/strategy_runs/EXP-010/` (+ `-shuffle/`).

## Registry disposition
CF-MR-003 `SCREENED-ADMIT → CONC-1 NOT-TRADABLE (UNPOWERED, S5 exec-1h, net, TRAIN)`. **1 candidate slot
consumed**; **0 counted TEST reads**; holdout sealed; referee untouched (L-12). Roadmap CONC-1 **done**;
CONC-1b/T2b (S5 exec-15m) + T2a (S3 exec-15m) remain **DEFERRED** behind E7/EXP-011. Registry-honesty fix
recorded: cf-mr-003.md "S5 20 admits" → **15 distinct** (exec-1h anchor-label duplicate collapsed). F-1/F-2
carried as tradability-gate debt.

---

## GATE: APPROVE (post-exec, orchestrator 2026-07-01)
Audit PASS (0 Critical); verdict forensics + causal-provenance/leak passes present; per-stratum masking check
done (5/5 reported, no pooled headline); every finding non-verdict-material for UNPOWERED (F-1/F-2 carried as
gate debt, no fix+rerun required); registry disposition recorded (NOT-TRADABLE; 1 slot; 0 counted reads; holdout
sealed; referee untouched). Tripwire reported honestly as vacuous. → Document complete; Phase 003 CONC-1 closed
(Track 1); Track 2 (E7 → T2a/T2b) is the next critical path.
