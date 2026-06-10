# Phase 007 Retrospective — NOT_TRADABLE (Edge Real but Cost-Dominated; Attribution Horizon-Dependent)

**Checkpoint:** `2026-06-09-007-avwap-tradability-and-isolation`
**Status:** **COMPLETED 2026-06-10** — both experiments executed and
post-governance APPROVED; phase objective fully satisfied.
**Outcome class:** `NOT_TRADABLE` (design §9) — EXP-030 returned net
EVIDENCE_AGAINST/INCONCLUSIVE on every domain, so the holdout-release gate
(EXP-032) is **NOT passed**. The companion isolation read (EXP-031) delivered
`ISOLATION_READ_UNRESOLVED` — a horizon-dependent attribution that is itself the
phase's most actionable mechanism finding.
**Follows:** `2026-06-08-006-avwap-evaluation-correction` (COMPLETED —
EVAL_SUPPORTED, cTrader-confirmed).
**Candidate family:** `CF-AVWAP-001` (Anchored VWAP on regime pivots).

---

## 1. Why this phase existed

Phase 006 closed `EVAL_SUPPORTED`/cTrader-confirmed: the faithful selective AVWAP
strategy shows positive per-event matched-control excess on all three domains
(+5.78 / +23.38 / +69.02 bps on 5m/1h/4h, Holm p=0.003), reproduced bar-by-bar on
the cTrader production path. Two facts bounded that result:

1. **The edge was gross of costs.** Whether it survives a realistic cost/slippage
   model was unresolved, and the two available yardsticks pointed opposite
   directions (event-level EVIDENCE_FOR vs per-bar REFUTED).
2. **The edge was undecomposed.** The measured excess was the whole strategy —
   bounce entry timing plus the EXP-022 band-target/trend-change (BTC) exit — with
   no attribution between them.

Phase 007 answered exactly those two questions, predeclared once and measured once,
**before** any holdout release. EXP-030 (tradability) was the hard gate for a future
holdout-release experiment (EXP-032); EXP-031 (isolation) ran independently and was
explicitly not cancelled by a tradability failure (operator decision 2026-06-09:
mechanism information is retained regardless of the tradability verdict).

## 2. Experiments executed and their verdicts

| EXP | Role | Verdict | Headline |
| --- | --- | --- | --- |
| **EXP-030** | Cost-bearing tradability of the faithful strategy (cost layer on the registered HYP-004-R baseline; no new candidate slot) | **INCONCLUSIVE** (per scope phase-outcome definition) | No domain passes the gate. Equal-weight cross-instrument net per-event expectancy under CONSERVATIVE costs: 5m −6.74 bps [−7.04, −6.38] and 1h −6.04 bps [−11.02, −1.53] are clean EVIDENCE_AGAINST; 4h +2.60 bps [−14.87, +19.28] is INCONCLUSIVE_SPANS_ZERO (n=187, CI half-width ~17 bps). All integrity guards pass (gross reconciliation to EXP-028 exact to 0.00 bps; commute check at machine epsilon; frozen EXP-027 hash pinned). |
| **EXP-031** | Edge isolation: entry-timing vs exit-rule decomposition (diagnostic; no candidate slot) | **ISOLATION_READ_UNRESOLVED** | All 3 domains ENTRY_DOMINANT at H=6 (PRIMARY; s_entry 1.53/1.13/1.41 — the entry carries >100% of the excess, the BTC exit is a differential drag) but EXIT_DOMINANT at H=1 (the BTC exit carries ~80–100% of the excess). The horizon contradiction triggers the predeclared unresolved class. Additivity X_full = X_entry + X_exit verified to machine precision; X_full reconciles with EXP-028 exactly. |
| *(EXP-032)* | Holdout release | **DEFERRED / NOT REGISTERED** | Admissible only on EXP-030 EVIDENCE_FOR (≥1 domain) — **gate not passed**. Holdout remains sealed. |

Against design §9: the TRADABLE row is not met; the NOT_TRADABLE row is met exactly
(EVIDENCE_AGAINST/INCONCLUSIVE on every domain); the ISOLATION_READ row is delivered
in its predeclared unresolved form.

## 3. What the phase established

- **The edge is relative, not absolute — now quantified.** The strategy's gross
  *absolute* per-event return is +0.76 / +1.46 / +10.10 bps (5m/1h/4h), an order of
  magnitude below the matched-control *excess* (+5.78 / +23.38 / +69.02 bps). Most
  of what Phase 006 measured is control discount — bounce-entry timing avoids the
  negative drift that matched controls suffer, rather than capturing large positive
  drift itself. This confirms and sharpens the retained EXP-024 finding, and it is
  the economic reason tradability fails: absolute P&L must carry costs that
  matched-control subtraction nets out.
- **Costs dominate on the fast domains.** 5m (+0.76 bps gross absolute) and 1h
  (+1.46) sit far below every instrument's round-trip cost (CONSERVATIVE 3.0–16.0
  bps) — net-negative under any realistic cost model, not just the predeclared one.
  The anti-trap expectation in the design (a net-negative 5m is informative, not a
  failure) was borne out.
- **The equal-weight binding metric is BTCUSD-cost-dominated; one cell survives
  descriptively.** BTCUSD (16 bps RT) contributes 4.0 of the 7.5 bps mean cost drag.
  EURUSD-4h individually shows net_cons +12.38 bps [+2.67, +21.46] — descriptive and
  multiplicity-uncontrolled per governance; no cell is promoted. A per-instrument
  tradability question requires a new pre-registered experiment.
- **The Phase 006 gross edge is not overturned.** The non-binding attribution
  companion (net matched-control excess, controls uncosted) remains EVIDENCE_FOR on
  1h/4h under CONSERVATIVE costs (Holm p=0.003). The binding-vs-companion verdict
  gap is an estimand difference, not a contradiction.
- **The BTC exit is two mechanisms in one rule.** EXP-031's exit-substitution
  diagnostic shows the exit *cuts early losers* (outperforms a 1-bar neutral exit,
  especially on controls — e.g. 1h control dH −20.48 bps at H=1) but *truncates
  trends* (underperforms a 6-bar neutral exit on bounce-entries — e.g. 4h X_exit
  −27.14 bps at H=6). Attribution therefore flips with the evaluation horizon on
  every domain. Any future exit redesign must preserve the short-horizon
  loss-cutting while reducing the long-horizon trend-truncation.
- **4h is unresolved by power, not by evidence of absence.** n=187 events yields
  ~17 bps CI half-widths against a +2.60 bps net point estimate; the domain cannot
  be resolved on this analysis set under the absolute estimand.

## 4. What changed vs the original design

- **EXP-030 inference substitution (predeclared, Stage 2).** The frozen EXP-027
  stratified sign-permutation test is invalid for the *absolute* net-expectancy
  estimand (it assumes a symmetric-under-null paired difference); the analysis plan
  replaced it with a one-sided bootstrap p from the same regime-cluster bootstrap,
  keeping the CI machinery and Holm adjustment unchanged. The frozen-tail hash
  (`e50873d12a9f68d9`) was pinned and verified.
- **EXP-030 governance Revision 1 (2026-06-09).** After the manual run, an
  adversarial review (F01–F07) found uncommitted post-run, result-aware code
  modifications. Stage 4 re-reviewed the diff change-by-change as a formal revision
  cycle: all changes were disclosure diagnostics (pyramid net split, seed
  robustness, per-instrument headroom columns) with **no binding-metric change**; a
  mandatory clean re-run was required before Stage 5; the non-binding companion was
  explicitly labeled; post-run diffs are now routed through Stage 4 by rule. The
  re-run reproduced the binding results.
- **EXP-031 audit fix (Warning 1, CLOSED).** A Polars NaN-vs-null handling defect
  made some 4h H=6 entry effects non-finite; the fix was applied and the determinism
  replay re-passed. The attribution classification was unchanged pre- vs post-fix.

No EXP-IDs were renamed or reused; no new candidate-family slots were consumed
(EXP-030 = cost layer on the registered baseline; EXP-031 = DIAG-003 diagnostic).

## 5. Lessons learned

1. **Predeclare the estimand split before costs enter.** The binding
   absolute-net metric and the non-binding matched-control companion gave opposite
   verdicts on 1h/4h. Because their roles were fixed in scope *before* measurement,
   the divergence is information (the edge is relative, not absolute) rather than a
   metric-shopping opportunity. Any cost-bearing experiment should declare which
   estimand binds — and why — before reading a single net number.
2. **Equal-weight cross-instrument aggregation makes the costliest instrument the
   binding constraint.** BTCUSD's 16 bps RT contributed over half the aggregate cost
   drag and mechanically capped the domain verdicts. The aggregation rule was
   correctly predeclared, but its economic consequence (one high-cost instrument can
   veto a domain) should be surfaced at scope time, with the per-instrument breakout
   predeclared as descriptive disclosure — as EXP-030 did.
3. **A decomposition needs at least two predeclared operating points to be
   falsifiable as a *read*.** Had EXP-031 predeclared only H=6, it would have
   confidently reported ENTRY_DOMINANT; only H=1 alone, EXIT_DOMINANT. The
   two-horizon design plus a predeclared UNRESOLVED class converted a would-be
   overconfident answer into the true finding: attribution is horizon-dependent.
   Predeclaring a contradiction outcome is cheap and pays for itself.
4. **Check power against the estimand at scope time.** 4h n=187 with ~17 bps CI
   half-widths could never resolve a single-digit-bps net effect; the
   INCONCLUSIVE_SPANS_ZERO was close to foreordained. Future scopes should state the
   minimal detectable net effect per domain up front and either accept the
   non-resolution explicitly or not bind on that domain.
5. **Post-run code changes are result-aware by definition — route them through
   governance.** The EXP-030 Revision 1 pattern (adversarial diff review +
   mandatory clean re-run + frozen-tail hash pin) is the correct handling and is now
   the standing rule: any post-execution modification, however cosmetic, goes
   through Stage 4 before Stage 5 reads results.

## 6. Open items

- **The global holdout remains sealed.** EXP-032 is not admissible; the gate
  failed. The holdout is never released to confirm a gross edge.
- **Per-instrument tradability is unanswered as a verdict.** EURUSD-4h's
  descriptive net-positive is the strongest surviving cell but is
  multiplicity-uncontrolled. A pre-registered per-instrument experiment (explicit
  multiplicity control, financing/swap included) is the admissible follow-up.
- **Financing/swap costs were excluded** — most material on 1h/4h holding periods.
  Any future positive tradability finding needs a financing check before holdout
  discussion.
- **The attribution crossover horizon is unknown.** Only H ∈ {1, 6} were
  predeclared; where s_entry ≈ s_exit sits, and whether attribution stabilizes
  beyond H=6, is unmeasured.
- **HYP-001 (AVWAP line as direct S/R) remains OPEN and untested.** The
  confound-free framing is recorded in design §8 (event = approach, outcome =
  directional-inverse exit of the ε-neighborhood, control = matched non-AVWAP
  levels). The edge not being localized to entry or exit individually keeps a
  line-level mechanism viable.
- **Stage-C branches** (`/LB` `/MB` `/ATR` `/ANCHOR`) and `/ALPHA` `/BAND` `/XTF`
  `/MA-DOMAIN` remain deferred/registered; the family-review path in design §9 is
  now triggered.

## 7. Disposition of artifacts

| Item | Status | Disposition |
| --- | --- | --- |
| EXP-030 | INCONCLUSIVE (phase read: NOT_TRADABLE) | Tradability gate failed; holdout-release (EXP-032) blocked. Binding equal-weight estimand net-negative on 5m/1h, unresolved on 4h. Per-instrument table retained as descriptive disclosure only. |
| EXP-031 | ISOLATION_READ_UNRESOLVED | Horizon-dependent attribution (entry-dominant H=6, exit-dominant H=1, all domains) recorded as the mechanism read; constrains any future `/EXIT` redesign. Registered as DIAG-003, 0 slots. |
| EXP-032 | DEFERRED / NOT REGISTERED | Remains inadmissible until some future experiment passes a predeclared cost-bearing gate under its own checkpoint + governance. |
| EXP-030 Revision 1 | CLOSED | Process record: post-run result-aware diffs must route through Stage 4; clean re-run reproduced binding results. |
| HYP-001 (line S/R) | OPEN | Testable framing preserved (design §8); candidate next-phase experiment. |
| Global holdout | SEALED | Never loaded in Phase 007. |

## 8. Redirect — logical next steps (operator-gated)

The NOT_TRADABLE consequence row in design §9 routes to family review. The phase's
own findings rank the candidate directions; the choice is the operator's:

1. **Per-instrument cost-bearing tradability screen (new EXP; pre-registered
   multiplicity control; financing/swap included).** The cheapest direct follow-up
   to the one surviving cell: test net expectancy on the low-cost instruments
   (EURUSD, possibly USTEC) as *predeclared* per-instrument hypotheses with Holm/FDR
   control, instead of letting BTCUSD's cost veto the domain aggregate. The 4h
   power floor (lesson 4) must be addressed in scope — n≈47/instrument at 4h makes
   a 4h-only binding test likely unresolvable; 1h EURUSD (RT 3.0 bps vs gross
   absolute +1.46 bps domain-wide) is probably also below water, so the scope must
   state the minimal detectable effect honestly before binding on any cell.
2. **Attribution horizon sweep (provisionally EXP-033, DIAG-004, 0 slots).** Map
   s_entry over a fine predeclared grid (e.g. H ∈ {1,2,3,4,5,6,12,24} on 5m) to
   locate the crossover and test whether the H=6 entry-dominance stabilizes. Pure
   diagnostic, cheap, and it directly de-risks any exit redesign.
3. **Exit-overlay redesign (`/EXIT`, un-shelving EXP-026 with a new scope).** The
   mechanism read says exactly what a better exit must do: keep the short-horizon
   loss-cutting (the H=1 benefit, strongest on controls), shed the long-horizon
   trend-truncation (the H=6 drag, −27 bps on 4h). A structural, predeclared,
   measured-once redesign — no sweep against analysis-set performance — ideally
   sequenced after (2) so the horizon profile informs the design rather than the
   result.
4. **HYP-001 direct S/R test.** The design §8 framing is confound-free and ready to
   scope: `P(bounce | approach to AVWAP)` vs matched non-AVWAP reference levels,
   with the bounce-trigger definition appearing nowhere in the metric. This is the
   mechanism-level question that survives regardless of strategy-form decisions.
5. **Stage-C detector/anchor branches** (`/LB` `/MB` `/ATR` `/ANCHOR`) — the wider
   family review if the operator judges the bounce-entry + BTC-exit form exhausted.

A coherent minimal next phase is **(1) + (2)**: one pre-registered tradability
question aimed at the only surviving cell, plus one zero-slot diagnostic that
de-risks the exit-redesign decision — with (3) or (4) scoped afterward depending on
what those two return. No tuning was performed in Phase 007; no metric was
reselected after results; predeclared once, measured once. Holdout remains sealed.
