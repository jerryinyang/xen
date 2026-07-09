# Amendment 001 — Faithful Full-Strategy Redo (EXP-014, CF-MR-004 / HYP-002)

**Date:** 2026-07-02 · **Phase:** 004 (Cross-Domain MR Renewal) · **Family:** CF-MR-004
**Trigger:** operator-directed investigative review of EXP-013 (`.ignore/idea/newer.md`) + orchestrator
review of the EXP-013 code against the proposal (`.ignore/idea/`).
**Type:** dated amendment (L-10) — downgrades the EXP-013 disposition and plans a from-scratch faithful
redo (EXP-014). EXP-013's record is retained (never deleted); its `NOT_TRADABLE` is reclassified
**CONFOUNDED / vehicle-incomplete** (below). **Operator decision (do not override):** all items here are
implemented and tested **immediately**, not procedurally gated behind an initial edge confirmation — the
missing exits and the trend/vol conditioners may themselves be the core of the family.

---

## 1. Why EXP-013 does not answer the question

The review found the strategy that ran is **not the strategy proposed** (`original-phase002-thoughts.md`).
Entry math is correct; the exit is incomplete and partly stale, and that confound is the most plausible
source of the `NOT_TRADABLE` read.

| # | Finding | Evidence | Severity |
|---|---------|----------|----------|
| A | **Form-1 (event-driven back-to-anchor) exit absent.** Proposal mandates two native exits: form-1 = exit when the anchor **series** reverts (spread → mean, recomputed each bar); form-2 = favorable limit at anchor mean. Only form-2 + a **time-horizon** stop shipped. | No spread-reversion exit anywhere; only `Xen.cs:657-658` horizon close + `:742` form-2 TP. | **Verdict-material** |
| B | **Form-2 TP frozen at entry, never refreshed.** `_exitTargetPrice = exp(anchorLog_entry)` set once (`Xen.cs:702,741-742`); `RearmBracket` early-returns while in position (`:696`). The anchor is a **moving target** (peer basket moves each bar); a fixed price TP can only capture price-side reversion. | Peer-side reversion never triggers an exit → position rides to horizon, books adverse. | **Verdict-material** |
| C | **Mechanism story is confounded.** Report's "~30% favorable-hit → spread not reverting" is the **static-TP hit rate**, not the spread-reversion rate. Audit named the right cause ("reversion shared with the peer") then dismissed it (report.md:42) as a bug artifact — it is the uncaptured form-1 exit. | The `~70% ride to horizon adverse` is manufactured by A+B, not a property of the family. | **Verdict-material** |
| D | **MR characterisation not independent, and only 2/6 of the framework.** VR + AR(1)-HL computed inside the same emission run and reported alongside tradability. Framework (`original-mean-reversion-screening-framework.md`) mandates 6 stages: lag-1 autocorr, VR, ADF, KPSS, half-life, robust detrend + OU params. Only VR + HL reported. "How mean-reverting is the series" was never answered on its own terms. | design §9 / report MR-screen table = VR, HL only. | Material to interpretation |
| E | **No re-entry (any version).** `/REENTRY=none` hard-coded (sibling cancelled on fill `Xen.cs:743`; no re-arm while holding). "allow" / "extend" not built. Otherwise-profitable intrabar/peer-side reversions structurally unbookable. | — | Scope gap |
| F | **Minor: S8 deviates from the doc's headline construction** (`new-anchor-series-suggestions.md` "practical variation" = **basket** − median-**90**; S8 shipped **pair** − median-**60**). Favorable-placement guard not asserted before placement (guaranteed by band>0, but not checked). Breach policy uses **live** `Symbol.Bid/Ask`, not the ≤t-1 close. | `CrossInstrumentSpreadPlanner.cs`; `Xen.cs:705,707`. | Informative |

**Disposition change.** EXP-013 verdict → **CONFOUNDED (vehicle-incomplete); do NOT reinforce the
terminal-branch prior on this run.** CF-MR-004 stays REGISTERED. The audit's `CONFIRMED / no-rerun` is
superseded: A/B/C are verdict-material per the materiality gate → fix + re-execute (this amendment).
**Lesson to log:** form-1 was dropped silently past the pre-exec gate — the exact "unauthorised silent
deviation masked in a complex document" the renewal warned of (`README.md`). Enter as a lessons/pitfalls
note; the pre-exec gate must diff the implemented exit set against the proposal's named exits.

---

## 2. EXP-014 — scope (CF-MR-004 / HYP-002)

**Falsifiable question (one).** On the 4h anchor domain, does the **faithful, full-exit** precalc
limit-order cross-instrument MR-fade strategy (4 series S5/S6/S7/S8; form-1 **and** refreshing form-2
exits; re-entry variants; trend + volatility conditioners) produce (a) reversion-to-anchor beyond a
dislocation-matched matched-random control (availability) AND (b) a net-positive per-stratum edge under
the frozen 4h referee (tradability) — or not, and **exactly which leg fails where**?

**Classification.** PRICE-PRIMARY, cTrader in-engine, native pending orders (Mode=NativeOrders), m1
fills own resolution. Python analysis-only on emissions (L-01/P-09).

**Governance (unchanged, binding).** TRAIN-only, first-49% fence; final-30% holdout **never loaded**;
**0 counted TEST reads**, 0 slots; per-stratum binding (L-03); frozen referee **never tuned** (L-12);
MR screen **informative-not-gating**; cost realism binding early (L-02); from-scratch family code (L-13).
Credentialed cTrader-CLI runs remain **operator-gated**.

---

## 3. Faithfulness fixes (core — in-engine, not derivable post-hoc)

1. **Form-1 exit (event-driven reversion).** On each completed 4h bar, recompute the anchor/spread from
   ≤ t-1 data; if the position's spread has reverted through the mean (short: spread ≤ mean; long:
   spread ≥ mean), **close at the next bar open** (executable, open-to-open — never `OnClose`). This is
   the moving-anchor exit the static TP cannot represent.
2. **Refreshing form-2 TP.** Each bar while holding, recompute `exp(anchorLog_t)` (the moving anchor
   mean price) and **modify the resting TP** to it. Form-2 stays a favorable limit (no adverse cost);
   form-1 is the market fallback when the favorable price is not reached but the spread has already
   reverted. Assert **favorable placement before every (re)placement** (long: TP > current price /
   entry; short: TP < ...) — skip/log if violated (guards F).
3. **Horizon fallback retained** as the last-resort time stop `H_i = min(48, 3·HL_i)` (market close at
   bar open), but it is now the exception, not the default exit. Emit exit reason so the three paths are
   separable (§6).
4. **No other exit methods** (proposal constraint). No stop-loss, no trailing, no /EXIT-plane techniques
   in HYP-002.
5. **Breach / entry-vs-price:** predeclare the entry breach test against the **≤ t-1 confirmed close**
   (proposal wording), and additionally record the live-bid/ask skip as a disclosure — quantify both.

---

## 4. New axes — tested immediately (operator NEW section)

**Design principle for efficiency + integrity:** emit **rich per-bar state** and derive every *filter*
variant as a **python slice of one unfiltered emission** wherever the filter only *suppresses* an
otherwise-independent order; use **separate labeled runs** only where a variant changes the position
lifecycle (and therefore fills) and cannot be derived. This gives full-scope coverage with minimum runs.

1. **Recalculation → fill-likelihood (A/B, needs 2 runs).** Does per-bar refresh (cancel + re-arm at the
   moved band) change fill probability vs a **place-once, leave-until-filled-or-horizon** order?
   - Arm R (refresh): current behaviour (re-arm each 4h bar).
   - Arm S (static): place the bracket once when flat, do not move it until filled/cancelled by horizon.
   - Emit armed levels + fill outcomes + realized OHLC per bar → quantify fill rate, near-misses, and how
     often the refresh moved a level *away from* an excursion that arm S would have caught.
2. **Trend-strength conditioner (post-hoc slice).** Only fade **adverse to the 4h trend**: in a strong
   up-trend take **only the long** (buy lower band — bearish excursions are valid dips); in a strong
   down-trend take **only the short**; in weak/consolidation take both (and a "neither" sub-variant).
   Predeclare a mild trend measure on the traded instrument's 4h (e.g. sign+magnitude of an EMA slope or
   a normalized directional index) with a small predeclared strength-band set (informative bands, L-08).
   **Emit trend dir+strength per bar**; run the bracket unfiltered; derive each trend variant by dropping
   the with-trend side in python.
3. **Volatility-regime conditioner (post-hoc slice).** Predeclare a vol-regime state (e.g. spread-σ or
   ATR percentile bucket on 4h). **Emit per bar**; derive low/mid/high-vol variants as slices. Report
   whether extremes are more monetisable in some regimes.
4. **Re-entry variants (`/REENTRY`).** none / allow / extend (multi-level ladder, one fill per deeper
   level). These change lifecycle → **superset run**: engine emits the most-permissive ladder (extend +
   allow) with per-fill provenance; derive none/allow/extend-subset by truncation in python where sound,
   else a separate labeled run. Predeclare the ladder levels (e.g. z\* ∈ {2.0, 2.5, 3.0}).

All conditioners are **informative slices**, not gates on signal quality (L-12): they define *which
extremes are valid deviations*, they do not disqualify a series.

---

## 5. Independent MR characterisation (separate artifact, before tradability read)

Answer "how mean-reverting is each series" on its own terms — a dedicated, faithful **limit-order
simulation** of the pure reversion mechanism, independent of the tradability run.

- **Full 6-stage screen per series/stratum** (≤ t-1, TRAIN): robust detrend, lag-1 autocorr, VR(q),
  ADF, KPSS, AR(1) **and OU** half-life. Reported, never gating.
- **Faithful reversion simulation:** for each armed extreme, measure reach-anchor rate, fraction-of-
  dislocation recovered, and time-to-anchor **scaled by fitted half-life** (the L-13 native estimands
  from EXP-009), under a **dislocation-matched matched-random** null (not random-timing — L-13/L-07:
  block-permute per-event outcomes, never rotate the path). This isolates *reversion completion* from
  *static-TP price-hit*, disambiguating finding C.
- Emitted from the same cTrader run's per-bar state (analysis-only python); **no vectorized python edge
  module** (L-01). This is characterisation, separate from the net-tradability adjudication.

---

## 6. Rich emission spec (quantify every leg)

Emissions must let the python audit quantify **each leg** and localize exactly what works / fails.
Extend `SignalRecords` / `StrategyRunParquetWriter` (reusable base, see §7) with, per bar:

- **Flat bar:** armed sell/buy band levels (both), σ, moving anchor price, spread, z, β, **basket mate
  count used + any mate gaps**, trend dir/strength, vol-regime, breach-skip flags (≤t-1-close and
  live-bid/ask), would-fill / near-miss vs realized OHLC.
- **Entry:** side, filled band, entry fill price + time, level index (ladder), z/spread/anchor/σ at
  entry, trend + vol state at entry.
- **Hold bar (per bar):** mark (RealClose), **moving anchor price + spread/z**, form-1 trigger flag,
  refreshed form-2 TP level, **unrealized MTM bps** (intra-position MTM — L-09, required for the
  per-bar referee and comparability).
- **Exit:** **exit reason ∈ {form1_reversion, form2_favorable_limit, horizon_time_stop}**, exit fill
  price + time, moving anchor + spread at exit, bars held, realized per-trade bps.
- **Per series:** the full 6-stage MR-screen vector (§5).

Provenance: all decision inputs ≤ t-1; `CloseTime`/`SourceCloseTime` alignment only; forming-bar OHLC
never read. The leak tripwires (peer-feed phase-shift future-destroy; label-permute) must be **re-run on
any admitting cell** — the EXP-013 gate-debt carries.

---

## 7. Adversarial contamination review of reusable components

Per operator: every existing component to be reused is reviewed **adversarially against this review**
before reuse; approve or propose fixes.

| Component | Verdict | Reason / required fix |
|---|---|---|
| `StrategyHost/CrossInstrumentSpreadPlanner.cs` | **APPROVE + EXTEND** | Entry/exit math correct, from-scratch, causal contract clean. **Add:** moving form-1 exit condition output + refreshed form-2 anchor-mean price per bar; full 6-stage screen outputs; trend/vol state. Fix F (S8 basket−median-90 variant; assert favorable placement). |
| `Xen.cs` native-orders block (`RunNativeOrdersOnBar`/`OnNativePositionOpened`/`Closed`/`RearmBracket`) | **APPROVE core + REWRITE exit/entry gating** | Order plumbing, causal `Observe`, fence, emission convention sound. **Rewrite:** exit set (form-1 + refreshing form-2 + horizon) — the defect (A/B) lives here; add conditioner state capture and reentry ladder; add the A/B refresh-vs-static arm. |
| `CrossInstrumentBasketFeed` (in `Xen.cs`) | **APPROVE + INSTRUMENT** | Fresh 4h exact-CloseTime, no carry-forward (fixed CF-MR-003 F-1). **Risk:** the "skip a mate with no bar at slot" gap policy silently shifts basket composition → moves β/anchor. **Fix:** emit per-bar mate-count + gap flags so the audit can bound the effect; predeclare a min-mate-count for a valid basket bar. |
| Frozen referee `referee_pstar.gate_stack_pstar` (4h) | **APPROVE as binding; ADD disclosure lens** | FROZEN — never tune (L-12); stays the binding adjudicator. **But** audit §4 flagged a vehicle-fit risk: a per-bar/episode referee may misfit a discrete round-trip bracket. **Add a per-trade evaluation as a non-binding disclosure** alongside the frozen verdict (a vehicle question, allowed as new-experiment disclosure; does not replace the frozen read, does not retune). |
| `SignalRecords.cs` (`SignalPositionRecord`) | **APPROVE base + EXTEND** | Schema is reusable but carries CONC-1/CF-MR-003 legacy fields and **lacks** exit-reason, per-trade legs, moving-anchor-at-exit, conditioner state, basket membership, per-bar MTM. Extend per §6 (default sentinels keep other models unchanged). |
| `StrategyRunParquetWriter.cs` | **APPROVE + EXTEND** | Writer infra; add the new columns (§6). |
| Python `xen.signals.ingestion` | **APPROVE** | Analysis-only ingest infra; reusable. |
| EXP-013 `run_experiment.py` availability/leak/referee analysis | **REWRITE** | Availability re-derivation conflated static-TP hit with reversion (finding C). Rewrite to separate form-1/form-2/horizon legs and use the native reversion estimands (§5). Logic reuse OK, code from scratch (L-13). |
| `tools/ctrader-cli/run-experiment.sh` + `.conf` harness | **APPROVE + NEW confs** | Harness reusable; write EXP-014 confs (series × conditioner/reentry/A-B arms), same first-49% fences. |

---

## 8. Discipline: full-scope, performant, no simplification

- Full faithful build from the start (operator mandate) — no staged simplification that licenses
  downstream shortcuts. Any deviation deemed necessary is **explicitly operator-approved** and logged.
- Max, safe performance: streaming O(1)/O(n) per-bar state (rolling windows, incremental OLS/median);
  no quadratic ops; bounded memory (fixed-size trailing buffers). Rich emission is append-only parquet.
  Performance must never compromise causality, denominators, metric definitions, or streaming validity.
- One emission drives many variants (§4 slice principle) — coverage without a run explosion.

---

## 9. Interpretation criteria (predeclared, to be frozen in EXP-014 design.md before outcome contact)

| Outcome | Condition |
|---|---|
| **Tradable-on-TRAIN** | ≥1 series axis clears cross-axis Holm **AND** ≥50% of that axis's powered cells referee-ADMIT (net ci_low>0) **AND** availability Δ>0 (ci_low>0) on ≥50% powered cells **AND** both leak tripwires collapse on admitting cells. → operator-gated counted TEST read (new D0). |
| **Not-tradable (now credible)** | With the **faithful full exit set** + conditioners, availability real but net fails the majority. Only *this* reinforces the terminal-branch prior — EXP-013 could not, being vehicle-incomplete. |
| **Inconclusive / UNPOWERED** | <3 powered cells/axis, or n_episodes<N_min, or direction mixed → UNPOWERED (never FAIL, L-12). |
| **REJECT** | Edge survives either future-destroy tripwire → leak → hard stop. |

Per-leg reporting is mandatory: entry fill rate, exit-reason split (form-1 / form-2 / horizon), P&L by
exit type, by trend bucket, by vol regime, by reentry variant, refresh-vs-static — so a null names
**exactly which leg failed where**, not a pooled wash.

---

## 10. Sequencing

1. **This amendment** — ratify scope (operator). *(EXP-013 disposition downgraded; lesson logged.)*
2. **EXP-014 design.md (Stage 1, quant-analyst)** — freeze exact params: trend/vol measures + bands,
   ladder levels, cost model, endpoints, member set, multiplicity (series × conditioner × reentry × A/B —
   with the slice-derivation map), leak tripwires, MDE. Inline pre-exec GATE — **must diff implemented
   exits vs the proposal's named exits** (form-1 present).
3. **Implement (Stage 2)** — planner/robot/feed/records/writer per §3/§6/§7; from-scratch family code.
4. **Execute (Stage 3, operator-gated)** — credentialed cTrader-CLI; TRAIN fence; holdout sealed.
5. **Audit (Stage 4) → Document (Stage 5)** — verdict forensics + causal-provenance/leak; per-leg
   quantification; independent MR characterisation; registry + index updates; inline post-exec GATE.

**Registry actions:** update `cf-mr-004.md` (EXP-013 → CONFOUNDED/vehicle-incomplete, retained;
HYP-002 added); add EXP-014 row to `python/experiments/INDEX.md` + `docs/experiments-docs/INDEX.md`;
log the silent-deviation lesson. **0 counted reads; holdout sealed; ledger unchanged.**
