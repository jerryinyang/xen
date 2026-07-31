# SPDR-018B — Report (the checkpoint-017 residue on the cTrader universe)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5` — same hypothesis, second universe
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Lane:** SPDR · TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Universe:** cTrader — `EURUSD`, `XAUUSD`, `USTEC` (INFR-021 fence `4cdc7b01…6de0`) — **3 instruments against crypto's 25**
- **Status:** **COMPLETE AND CLOSED 2026-07-26** — 7,578 cells, **11 HARD checks, 0 failed**
- **Analyst recommendation:** `HYP-D5` **PARTIALLY SUPPORTED** — the structural result replicates convincingly; the specific replication target does not resolve in either direction
- **Operator verdict:** **PARTIALLY SUPPORTED, as recommended** (§8). No gating verdict.
- **Binding analysis of record:** `analysis.md` (fresh-context analyst, re-derived from `results/` only; `screen_code/` never read). **It supersedes `screen.md`, which is stale in §2, §3 and §4.**
- **Parent:** `python/experiments/SPDR-018/` — COMPLETE, FROZEN, **not modified by this experiment**
- **Corrections:** `docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/corrections-log.md`
  — independent adversarial audit 2026-07-26. **One CRITICAL fix in §4.1:** the C2 ruling's third reason
  was false and now supports *not replicated*; the "not refuted" half rests on **three legs, not four**.
  See also the ADDENDUM appended to `analysis.md`. Verdict unaffected.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY — BORROWED from Bybit AND RESCALED
  COST-STATUS: DOUBLY SYNTHETIC. Not EURUSD's, XAUUSD's or USTEC's cost. It supports exactly one
               claim — cross-universe comparability in volatility units — and even that is weakened
               by the deflator circularity in §6.
  implication: every net figure understates true cost and OVERSTATES performance
  prohibited_claims: fully-net, cost-complete, tradable, deployable, "this is the cTrader cost"
```

---

## 1. Why this experiment existed

SPDR-018 ran all four arms on crypto but replicated **only arm B, at one exit geometry, gross only**
on cTrader. The operator's intent was that everything be tested on both universes. That narrowing was
an implementation defect in SPDR-018, not a design decision, and it left that run's **single surviving
live thread — `C2` shock-conditioned MOMO — with zero external replication.**

> **The falsifiable question.** Do SPDR-018's results — the break-even geometry, the `W/L` mirror, the
> powered / `NOT_RESOLVABLE` split, and specifically the `C2` shock-MOMO survivor — reproduce on an
> independent asset class with its own fence?

A true speed run by operator directive: objects, estimands, controls and protocol inherited verbatim
from 017/018; only the universe changes. **cTrader is REPLICATION and CREDIBILITY only** — never
pooled into crypto `n`, never cited as power for the crypto estimate (AMENDMENT-C1 / S1).

**Three replicate. The fourth — the one the experiment was built for — does not resolve.**

---

## 2. Corrected headline numbers

`screen.md`'s §2/§3/§4 tables were written against superseded cost, power and C2 numbers. The reasoning
in them stands; the numbers do not. Every figure below is re-derived by the fresh-context analyst from
`results/*.parquet` and `results/controls.json`, and independently spot-checked by the orchestrator.

| Quantity | **Corrected (binding)** | `screen.md` (stale) |
|---|---|---|
| powered signed cells | **315** of 6,156 (5.1%) | 2,388 — **reproduces under no constructible definition** |
| `p` / `p_be` (gross) | **0.4868 / 0.4855** — gap **+0.0013** | 0.4922 / 0.4917 |
| `W` / `L` / `W/L` | **24.66 / 20.99 bps / 1.0597** | — / — / 1.034 |
| `p_be_net` / `edge` | **0.5334 / −0.0544** | 0.5265 / — |
| gross mean | **−0.080 bps = 0.006σ** | −0.08 ✓ |
| clears gross break-even | **129 / 315 = 41.0%** | 47.5% |
| **clears net break-even** | **0 / 315 = 0.0%** | 12.9% |
| `W/L` mirror fit | **R² 0.9746, slope 0.9656** — *it replicates* | R² 0.311, explained away as a narrow-range artifact |
| best single powered cell | **+1.389 bps gross** vs its own 2.43 bps charge | — |
| identity residual | **8.53e-14 bps**; `p_be`/`p_be_net`/`edge` reconstructed to **exactly 0.0** | ~1e-12 claimed |

**Three corrections produced this, and they compounded:**

1. **The precision target was not portable.** SPDR-013/014's absolute **10 bps** rule was imported from
   a σ̂ = 73.00 bps universe into a σ̂ = 13.03 bps one — silently loosening it **5.6×**. Re-stated in σ
   units it is **1.785 bps**. Powered signed cells **2,401 → 315**.
2. **The cost deflator was wrong by ~2×.** It used the ratio of H1 *bar* volatility (0.17855) where
   cost scales with what a trade *pays*. Now derived per arm from realised payoff scale, median
   `(W+L)`: **arm B 0.2611, arm C 0.3118**. Cost and precision deliberately use **different**
   deflators — cost scales with payoff, the MDE with bar noise. Collapsing them was the original error.
3. **The net-clearing rate was entirely an artifact of (1) and (2).** 12.9% → **0.0%**.

> **`0 of 315` is robust, not a cost-model choice.** It holds at the vol-scaled charge, at the
> unscaled borrowed charge, and at **any charge above 1.39 bps** — because the best powered cell in
> the entire run earns +1.389 bps gross. **Crypto's 0% is reproduced.**

**Power counts are NOT comparable between SPDR-018 and SPDR-018B.** Different precision bases. 315 vs
1,413 says nothing about relative evidence strength. Operator ruling: the portability correction
applies to **018B only** — the finding is recorded against SPDR-018 but **SPDR-018 is not reopened**.

---

## 3. What replicates (powered, and load-bearing)

Only powered cTrader cells are informative about crypto (B-5 / design §7). Rows R1–R11 and R13 are
powered. **R12 is a mixed row and must not be read as uniformly powered: within it, A5 (27 cells),
D2 (24) and D7 (6) have ZERO powered cells** — for A5/D2/D7 no bps target attaches, so this is a
definitional gap, not a power failure, but the replication claim for those three items rests on
point magnitudes without a power statement behind them.

| # | Object | cTrader | crypto |
|---|---|---|---|
| R1 | **The zero line** — `p` at its own gross break-even | gap **+0.0013**; gross mean **0.006σ** | gap −0.0138; 0.016σ. **In σ units cTrader sits 2.6× closer to zero** |
| R2 | **Nothing clears net break-even** | **0 / 315** | 0 / 1,413 |
| R3 | **The `W/L` mirror** | **R² 0.9746, slope 0.9656**, sd(log R) 0.0607, free share 0.163 | R² 0.9667, slope 0.9408, sd 0.0729, free share 0.193 |
| R4 | **`W/L` is movable and moving it does not help** | exit geometry moves `W/L` **0.274 → 9.975 = 36.4×** while `p` moves inversely 0.840 → 0.0625; the mean does not improve | 67×, same inverse structure |
| R5 | **Per-cell `W/L` inseparable from the driftless mirror** | CI excludes the mirror in **22 of 315 (7.0%)** — 93% indistinguishable | 17.2% / 82.8%. **Even less separable here** |
| R6 | **Cost, not rate, is the whole gap** | cost share **95.8%**; arm C **100.8%** (rate −0.0004), arm B 94.5% | 90.7%; C 98.8%, B 88.4% |
| R7 | **Selection scales both sides of the identity** | ambient-base arm C: `W` +6.67, `L` +7.74, **`W/L` −0.028**, Δmean −0.053 bps | `W` +130, `L` +88, `W/L` −0.174. **SoT §3.1 now measured on two universes** |
| R8 | **Arm C's sides carry real information against the registered direction** | side-derangement live **−2.632** vs null +0.382 (sd 1.551), **pct 0.023**, 0 fixed points | −12.221, pct 0.0065. **~1/5 the magnitude on a 1/5.6-σ universe — it scales with σ̂** |
| R9 | **`mag_high` is "the bar was large", not the volatility state** | live −3.402 vs comparator −2.068, pct 0.2735 | live −11.607 vs −10.704, pct 0.46 |
| R10 | **C7 — the DESIGN→CONFIRM sign flip is not distinguishable from noise** | **40.99%** flip (below chance), 1.44% exceed the two-band MDE, `n`-weighted bands agree to **0.65 bps** | 44.14% / 6.63% / 0.33 bps |
| R11 | **C8 — the two weightings agree; the lean is to mean-reversion** | 0.4939 / 0.4946, per-cell median \|diff\| **0.0009** | 0.4676 / 0.4699; crypto's per-cell median \|diff\| is **0.0082** (its `analysis.md` quotes 0.0023, which is the difference of the two medians, not a per-cell figure — 018B computed its own correctly) |
| R12 | **The `E[\|move\|]` / regime layer** (A1, A3-IC, A5, D1, D2, D5, D6, D7, D8) | A1 +6.88 bps, IC **+0.228**, A5 **27/27**, D7 `p_stay` **0.9517**, D8 ΔBrier −0.0256 | +18…+48 bps, IC 0.326, 135/135, 0.9365–0.9486. **10 of 12 items replicate; magnitudes scale with σ̂** |
| R13 | **E-TOUCH > E-HORIZON > E-CLOSE** | **+0.124 / +0.158 / −0.491 bps** | +0.6…+1.5 / −0.03…+0.69 / −1.2…−3.0. **~1/5 the spread** |

**The most valuable single replication is R3.** The `W/L` mirror was SPDR-018's decisive finding, and
it is confirmed here at a *tighter* fit, on data sharing nothing with it — and with **all five exit
geometries running**, which SPDR-018's cTrader leg could not do. The design's stated reason for
existing is discharged on this point.

---

## 4. What does not replicate — and the C2 ruling

### 4.1 The ruling

> ## `C2` shock-conditioned MOMO: **NOT REPLICATED AND NOT REFUTED.**
>
> **018B's C2 evidence may be cited only as a "does not transport cleanly" flag. It may not close the
> thread, and it may not be reported as a cross-asset-class reversal.**

On crypto, shock-MOMO sat **above** its magnitude-matched comparator (+22.6 bps, percentile 0.95,
n=505) — above the partial cost floor, in the registered direction. On cTrader the corrected `P-MOMO`
object sits **below** its comparator (−2.414 bps, percentile 0.000, n=1,594; `P-MR` −0.15, pct 0.067).
Opposite sign. **Four reasons that is not a reversal**, in descending force:

| # | Reason |
|---|---|
| 1 | **The comparator is not a neutral yardstick.** Its own mean runs **+0.97 bps (EU) → +3.46 (US) → +12.05 (Asia)**, and the Asia null lies **entirely above zero** (5th percentile +2.09). Against a yardstick like that, a genuinely zero-effect arm also reads percentile 0.000. The "significance" is partly the control's own drift |
| 2 | **The session split destroys the clean story in both directions.** ASIA **−13.57 bps** (pct 0.000, n 184) · US **−1.99** (pct 0.000, n 853) · **EU +0.62 (pct 0.443, n 557)**. The effect concentrates in Asia and **vanishes in Europe — the deepest-liquidity session.** Neither an asset-class fact nor a clean artifact |
| 3 | **The like-for-like cell is a POWERED non-replication — this leg of the ruling was stated wrongly and is corrected here.** The report originally claimed the n=290 control "could not reliably have detected crypto's +22.6 bps". **That is false.** Its own plant curve reads {+5 bps: 0.285, +10: 0.755, **+20: 1.000**, **+40: 1.000**} — resolution is 10–20 bps, so an effect of crypto's magnitude WOULD have been detected. The honest reading is the opposite of what was written: the cTrader control was powered for an effect that size and measured **−9.383 bps at percentile 0.043**, i.e. the opposite sign. **This strengthens "not replicated" and removes one of the four supports for "not refuted".** What still limits it: n=290 on one cell, a one-sided ~4%, and a magnitude far smaller than crypto's +22.6 |
| 4 | **The comparator level does not survive independent reconstruction.** The analyst's own rebuild reproduces every **live** value exactly but shifts the **comparator** by 2.3–3.4 bps and **flips the `P-MR` read** (pct 0.0665 → 0.826). The session *pattern* is robust under an independent session cut; the *magnitudes* are not |

The 20 powered C2 grid cells themselves sit flat: gross **−0.065 bps**, `p` 0.4962 against
`p_be` 0.4971.

**Correction of record:** the earlier "−4.21 bps / 30,319 rows" figure was **net and off-object** — it
covered all shock bars, including the ~87% carrying no momentum policy. It is not the shock-MOMO
object and must not be quoted.

**Standing methodological consequence:** *a magnitude-matched percentile is uninterpretable without
the comparator's own mean reported alongside it.* Every future M-3 read must emit both.

### 4.2 The other non-replications, each with its power statement

| # | Object | crypto | cTrader | Binding qualification |
|---|---|---|---|---|
| N3 | **A2 V-TAIL exceedance lift** | +0.056 (p90) / +0.031 (p95), 90.9% CI-excl-0 | **+0.0095**, only 8.3% CI-excl-0, all 72 WASH | Magnitude ~6× smaller and mostly inside its CI on 3 instruments. **Reported as a magnitude; NOT a refutation** |
| N4 | **A4 V-CLOCK incremental R²** | −0.032 to −0.0004 | **+0.0291** — sign reversal | **A positive in-sample incremental R² on 3 instruments is what over-fitting looks like.** Not read as a market statement. No held-back fold exists in a TRAIN-only lane |
| N5 | **The counter-outcome barely exists here** | 129 negative CI-excl-0 cells, 1 positive; positive tail depleted, negative enriched ~3.7× | **12 negative, 2 positive of 315**; best flipped gross **+1.754** vs its own 2.544 bps charge; **0 of 12** clear when flipped | **Powered.** 12/2 on 315 correlated cells is near the nominal-95% expectation — **there is no enriched tail here at all**, so nothing routes. SoT §10 end-state 3 not satisfied |

---

## 5. Not resolvable — a first-class quantified answer, never a negative

**2,407 cells `NOT_RESOLVABLE`; 939 `UNPOWERED`; 4,330 `levers_exhausted`.** Only **315 of 6,156
signed cells (5.1%)** reach the corrected bar. Predeclared in design §7 — 3 instruments against 25 —
and it bound exactly as predicted.

| Item | State | What would resolve it |
|---|---|---|
| **B3 (native, 159 cells)** | **0 of 159** at target; median block MDE **29.22 bps** against 1.785 — **16.4× short**; median n 84 episodes / 61 dates. All 159 are gross-**and**-net positive, and **99 of them are `trail`/`stop`** — i.e. the §7 truncated-tail population | ~270× the realised `n` at the same variance. **Do not let this one through on its sign** |
| **arm B `stop` / `time` / `trail`** | **0 of 378** at target on all three | One-tail estimators by construction (`p` 0.06 / 0.51 / 0.84); pooling across 3 symbols does not fix them |
| **arm C at large** | **179 of 5,526 (3.2%)** at target | The event-nested conditioner science remains substantially unanswered **on this universe** |
| **D2, D7, A5** | 0 at target | **Definitional** — no bps target attaches to these items. **Not a power failure** |
| **C9 (`DA-STRADDLE`), D3, D4** | **NOT RUN — 0 cells** | A straddle runner (C9) and a cTrader ZigZag panel (D3/D4). Operator accepted these stay open. **NEVER to be read as nulls.** D4's `ridge_cont` K=5 was the strongest D3/D4 object on crypto and its cTrader status is entirely unknown |

**Every one of these is a statement about a 3-instrument universe's size, and none of it is evidence
against the crypto result.**

---

## 6. Coverage gaps closed, and one nobody had flagged

**Closed in this run** — all three under a **native** definition, because 018's versions were defined
by pointing at crypto tables with no cTrader analogue:

| Gap | Native result |
|---|---|
| **C7** (`coverage_gap_C7_C8.parquet`, 627 pairs) | Flip rate **40.99% — below chance**; 90.3% of flips have overlapping band CIs; only **1.44%** exceed the two-band MDE; `n`-weighted bands agree to **0.65 bps**. **Agrees with crypto's resolution** |
| **C8** (339 cells) | Row-weighted `p_momo` **0.4939**, symbol-weighted **0.4946**, median \|diff\| **0.0009**. **Agrees with crypto's resolution** |
| **B3** (`coverage_gap_B3.parquet`, 159 cells) | Defined natively rather than by reference to SPDR-013's crypto table. Substantive answer supplied: **0 of 159 powered, 16.4× short** (§5) |

**The circularity nobody had flagged — the cost deflator is not identified.** Its payoff scales are
computed on the **superseded absolute-powered subset**, i.e. the very selection the precision
correction invalidated. The analyst reproduced arm B's 43.166 as median `W` + median `L` on those 270
cells and arm C's 83.015 exactly on those 2,131. Recomputed on the corrected 315 the same statistic
gives **0.185 / 0.196**; over all signed cells **0.703 / 0.386**.

```
COST DEFLATOR: defensible range 0.185 - 0.703  ->  a factor of 3.8, i.e. +/-2x on EVERY net figure.
  Harmless for the headline: 0 of 315 clear net at ANY charge above 1.39 bps.
  FATAL for any cross-universe comparison of net MAGNITUDES.
```

Treat every cTrader net figure as **ordinal at best**. The per-symbol spread pin remains a declared
blocking prerequisite.

---

## 7. The selection-artifact check — and it runs the other way

`screen.md` §7 flagged ten arm-B trailing-stop cells at +7 to +23 bps as a probable artifact of the
precision filter. **Verified exactly**, and then some:

- The ten cells are real and verify at **+7.13 to +22.97 bps**, all with CI-low above zero, at
  `p` **0.80–0.89** *with* `W/L` up to **6.67** — the unmistakable truncated-tail signature.
- They were drawn from a population of **116 excluded cells averaging −27.610 bps**.
- **All ten have since vanished: 0 of those 126 cells survive the corrected precision bar.** Fixing
  the portability defect deleted this artifact's own example.

**The refinement, which matters more than the original claim:** the bias direction follows the
**population's skew, not the gate**. On arm B overall the same gate *discards* the positives —
excluded cells average **+6.63 bps with 51.8% positive**, against powered cells at **−0.14 bps with
28.7% positive**. A dispersion gate is not sign-neutral, but it is not reliably *optimistic* either.

**Recommended standard check** before any powered subset's magnitudes are read — three numbers:

1. **payoff-scale ratio** powered vs excluded (here **0.43** — the gate halves the payoff scale);
2. **sign-share differential** (positive share powered vs excluded);
3. **mean-vs-median gap in the excluded set** (here **32 bps** — the unfired tail).

---

## 8. Verdict

### On `HYP-D5` as posed by `design.md` §1

> ## **PARTIALLY SUPPORTED** — the structural result replicates convincingly; the specific replication target does not resolve in either direction.
>
> **Operator-confirmed 2026-07-26**, as recommended by the binding analysis.

| Design §1 question | Answer |
|---|---|
| Does the **break-even geometry** reproduce? | **YES, and more tightly.** gap +0.0013; gross mean 0.006σ against crypto's 0.016σ; **0 of 315 clear net** at any charge above 1.39 bps |
| Does the **`W/L` mirror** reproduce? | **YES.** R² **0.9746** / slope **0.9656** against crypto's 0.9667 / 0.9408; 93% of powered cells indistinguishable from the driftless mirror; `W/L` moves **36.4×** with `p` inverse and no improvement in the mean |
| Does the **powered / `NOT_RESOLVABLE` split** reproduce? | **YES in structure, and it bound harder** — 5.1% powered, 2,407 unresolved, three of five exit geometries at zero powered cells. Exactly as design §7 predeclared. **Counts not comparable to SPDR-018's** |
| Does the **`C2` shock-MOMO survivor** reproduce? | **UNRESOLVED — not replicated, not refuted** (§4) |

**What this experiment explicitly does not decide:** no gating verdict; no family action
(`CF-VOLDIR-001` remains `REGISTERED`); no tradability, deployability, cost-complete, graduation or
XENA claim; no end-state decision; and **nothing about SPDR-018**, which stays frozen.

**What would change this verdict:** a determinism run showing the parallel and sequential paths differ
(which would invalidate the emission); or a C2 re-run with a properly matched object and a disclosed
comparator mean that put the cTrader shock-MOMO effect *above* its comparator after all.

---

## 9. Integrity — 11 HARD checks held, and seven inherited ones that do not exist

**`results/integrity_selfcheck.json` carries 12 entries: 11 HARD, all held, 0 failed, plus 1
INFORMATIVE.** Counted element by element rather than accepted as prose. `controls.json` carries both
`tripwires` and `arm_C_ambient_base`.

**What did real work:**

- **The cross-universe identity guard [HARD]**, which design §5 substitutes for parent parity (there
  are no published cTrader cells to reproduce). It runs the retargeted code path over a **Bybit**
  symbol and requires SPDR-018's emitted cells to be reproduced exactly. **It failed twice before
  passing, both times on genuine defects in this experiment's own code:** an arm-B ZigZag start index
  off by one, and — more seriously — a band-construction difference (SPDR-013 builds *each band
  separately*, preserving warm-up history while confining trading to the band; the first
  implementation ran once over the full span and assigned bands by exit timestamp, giving a different
  episode set: max cell-count difference **61**, max gross difference **14,217 bps**). Final result:
  **0 cells differ, max gross difference 1.14e-13.**
  **Without this check, 018B would have reported an arm-B "non-replication" that was an artifact of
  its own code — on a 3-symbol universe where a null is the expected outcome, and therefore easy to
  accept as real.**
- **TRIPWIRE-2** separates the legal variant (**0.494 bps**) from the leaky twin (**203.65 bps**) — a
  **412× separation** on 106 matched rows, against SPDR-018's 7.55×.
- **TRIPWIRE-1** holds on 100% of 233,569 rows by the analyst's own recomputation: entry strictly
  after the decision bar (min offset 1), exits at the declared `h`.

### 9.1 Seven inherited HARD checks that do not exist in this run — operator ruling requested

SPDR-018 carries 18 HARD checks; 018B carries 11, one of which is a presence assertion. Missing:

| Missing check | Assessment |
|---|---|
| **Determinism** | **The sharp one — absent on a run that WAS resumed**, i.e. the single check built to catch a resume defect, on the run where a resume defect actually occurred (arm-C controls left empty) |
| **Bybit-holdout assertion on the §5 guard's own reads** | **The only genuine residual Phase-0 exposure.** The guard reads Bybit bars; nothing asserts it stayed inside the Bybit TRAIN fence |
| Golden traces | Procedural gap |
| Universe-pin set-equality | Procedural gap |
| Bootstrap-path parity | Procedural gap |
| No-local-accounting | Procedural gap |
| Spread-never-charged | Procedural gap (the disclosure block is present and consistent) |

`run_summary.json` still reports `deviations: []`.

**Mitigation:** TRIPWIRE-1 and TRIPWIRE-2 both hold (412× separation), the identity guard passes at
1e-13, and the direction of the headline result is negative-to-null — a look-ahead leak inflates
edges, and there is no inflated edge to explain away. **Recommended: accept the emission with the
seven recorded as un-run, and run determinism plus the Bybit-holdout assertion as a cheap follow-up
(P4).**

### 9.2 Other recorded gaps, none verdict-bearing

| # | Gap | Assessment |
|---|---|---|
| 1 | **Median and trimmed-mean CIs do not exist at all** (crypto had 1%), and **no `ci_low_seed_range` or `block_sensitivity` sweep is emitted anywhere** | **No CI in this run can be checked for MC- or block-fragility** — an INFR-004 / L-20 requirement. Matters most for the two positive CI-excluding-zero cells (CI-low 0.146 / 0.118 bps) and for the `trail` population's 32 bps mean-vs-median gap |
| 2 | **The power flag is not regenerable from the emission** — recomputing `MDE ≤ target` gives **317 vs 315** (2,485 vs 2,401 on the old basis) | ~1–3% of cells carry an undisclosed additional condition. The binding subset cannot be independently reconstructed |
| 3 | **`entry_ts == event_ts` on 96.3% of panel rows** (224,830 of 233,569 — not 100% as first
reported) while `entry_idx = event_idx + 1` | The **fill-ts off-by-one shape**. Harmless here — nothing joins on it, and the *index* is causal — but it is a known-dangerous shape in this programme (INFR-010) and must be fixed |
| 4 | **`unit_pin.json` carries Bybit's TRAIN band string** on a cTrader measurement | A carried-over constant of exactly the kind the retarget was built to eliminate. Affects no number |
| 5 | **`screen.md` §3/§4 headline tables were never recomputed** after the corrections | `analysis.md` is binding and supersedes them. §2 of this report is the corrected record |
| 6 | **Ambient-base and TRIPWIRE-1/2/3 were absent from the original emission** while `screen.md` §7 claimed "deviations: none" — the same failure class as SPDR-018's TRIPWIRE-2 | Built and run; `screen.md` §7/§9 corrected. See §11 |
| 7 | **Multiplicity disclosed, not treated** (AMENDMENT-C3) | 7,578 cells and five separately-cut M-3 reads on one object. Per L-34, tail counts must be read against the realised testing process |
| 8 | **207 of 315 powered cells are `__CTRADER_POOLED__`** | `edge` is negative in **all three** named symbols *and* in the pooled cells, so the pooled sign is not a Simpson artifact. But with 3 symbols homogeneity is weakly established; design §8's "POOLED: disclosure-only unless homogeneity is shown" was applied |

---

## 10. The `(p, W, L, W/L, edge)` picture for the mid-checkpoint reflection

**cTrader is credibility, never power, and never pooled into crypto `n`.**

```
CTRADER (EURUSD, XAUUSD, USTEC) - 315 powered signed cells, TRAIN only, GROSS PRIMARY
  Each term as MEDIAN | MEAN | 10%-TRIMMED MEAN across the powered cells. Medians are the headline.

  term        median      mean    trim10
  p           0.4868    0.4300    0.4371   <-- p diverges more here than on crypto
  W (bps)    24.6599   23.9017   23.5885
  L (bps)    20.9894   19.0185   19.1412
  W/L         1.0597    1.4372    1.3460   <-- so does W/L
  p_be        0.4855    0.4330    0.4402
  p_be_net    0.5334    0.4987    0.5054
  edge       -0.0544   -0.0687   -0.0648
  gross mean -0.0804   -0.0929   -0.0931

  gap to own gross break-even (median p - median p_be) = +0.0013   (on means: -0.0030)
  gross mean = -0.080 bps  (= 0.006 sigma, sigma-hat = 13.03 bps)
  net mean   = -2.500 bps  (DOUBLY SYNTHETIC charge, median 2.43 bps, spread NOT charged)
  gross median = -0.560    gross trimmed-10 = -0.573   (all three AGREE here, unlike crypto)
  clears gross break-even = 129/315 (41.0%)   clears net break-even = 0/315 (0.0%)
  best single powered cell = +1.389 bps gross vs its own 2.43 bps charge  (short by 1.04 bps)
  gap decomposition: rate term +0.0023 | cost term +0.0529  -> cost is 95.8% of the gap
  arm B: p 0.3604  W/L 1.7457  p_be 0.3642  p_be_net 0.4462  edge -0.0820  gross -0.148
  arm C: p 0.4950  W/L 1.0167  p_be 0.4959  p_be_net 0.5430  edge -0.0489  gross +0.018
  W/L movability (all 630 arm-B signed cells, exit geometry as the lever):
      trail p 0.840 W/L 0.274 | time p 0.509 W/L 0.994 | combined p 0.393 W/L 1.498
      signalflip p 0.343 W/L 1.840 | stop p 0.0625 W/L 9.975   -> 36.4x, p moves inversely
      gross medians: +7.6 / +0.8 / -0.005 / -0.22 / -10.4 bps
      (trail's +7.6 median sits against a -24.3 MEAN and a -1,002 bps min: an unfired tail)
  mirror fit: log(W/L) = -0.0030 + 0.9656 * log((1-p)/p),  R2 0.9746,  sd(log R) 0.0607
              93.0% of powered cells cannot be distinguished from the driftless mirror
  edge is NEGATIVE in every named symbol: USTEC -0.054, XAUUSD -0.091, EURUSD -0.106
```

> **Reading note — do not subtract these rows.** `edge = p − p_be_net` holds **exactly per cell** (max
> deviation 0.0), but **neither the median nor the mean operator is additive across cells**: median
> `edge` is −0.0544 while median `p` − median `p_be_net` is −0.0466. Always read `edge` from its own
> column.
>
> **The mean/median divergence is larger here than on crypto, and it matters for one headline.** The
> `+0.0013` gap to gross break-even is a median statement; on **means** the same gap is **−0.0030**,
> i.e. it changes sign. Both are within noise of zero (the gross mean is 0.006σ either way), so the
> claim *"`p` sits at its own gross break-even"* is robust — but the claim *"`p` sits **above** it"* is
> **not**, and must not be made. Crypto's gap is −0.0138 on medians and −0.0078 on means: negative on
> both.

**Three constraints this places on any capture-geometry design:**

1. **The joint sits at break-even on two independent universes.** SoT §1.1's gate — *a capture design
   cannot manufacture expectancy out of a joint `(p, W, L)` that sits at break-even* — now binds on
   two asset classes. **Any proposal must name the mechanism that puts `R` above 1, because five
   distinct exit devices spanning 36–67× of `W/L` did not, on either universe.**
2. **Do not parameterise off a powered subset's magnitudes without the §7 three-number check.**
3. **Do not state any threshold in absolute bps across a universe boundary.** State it in σ units or
   re-derive it per universe.

---

## 11. Process defect class — four failures, one cause

Recorded because it is the most transferable thing this build produced.

**Checks that lived in transient in-memory state, or were appended to an artifact a later stage
regenerates, silently did not run while the run reported success:**

| # | Failure | Fix |
|---|---|---|
| 1 | **SPDR-018 TRIPWIRE-2 and determinism** — declared HARD, never invoked | **Structural.** Determinism now executes unconditionally whenever `--jobs > 1`, independent of `--resume`; TRIPWIRE-2 computed on the independent self-check side |
| 2 | **018B arm-C controls** — a resumed run left the panel empty | **Structural.** `run18b.py` now persists `panel_C.parquet` as an artifact; the guard is parameterised |
| 3 | **018B post-run fixes** — `panel_C.parquet` had been deleted and was never persisted | **Structural**, same fix |
| 4 | **018B ambient-base + TRIPWIRE-1/2/3** — appended by `add_missing_controls.py`, then **wiped** when a later re-run regenerated `controls.json` and `integrity_selfcheck.json` from scratch. Caught **only by manually counting HARD checks** (8 against the expected 11) | **NOT FIXED.** `add_missing_controls.py` remains a manual post-step that any re-run silently undoes. **Folding it into `run18b.py` is outstanding work** |

> **The rule this build earned, and it is now KB L-52:** never trust "HARD checks held" as a
> count-free statement. **Assert the expected NUMBER of checks, and make every check depend on an
> emitted artifact rather than on in-memory state.** Verified for this report:
> `integrity_selfcheck.json` shows 11 HARD, and `controls.json` carries both `tripwires` and
> `arm_C_ambient_base`.

---

## 12. Threads this experiment could not resolve

| # | Thread | Why it needs new work |
|---|---|---|
| **P1** | **Is `shock_flag` real?** | **SKIPPED BY OPERATOR 2026-07-26** — no SPDR-018C. **C2 cannot be settled on this data**; book it at the retrospective as **unresolved-and-parked, a terminal `NOT_RESOLVABLE`, never a refutation** (B-5). Note the §4.1 correction: the like-for-like cell **was** powered for an effect of crypto's size and saw the opposite sign, so *not replicated* is better supported than first written |
| **P2** | **Median and trimmed-mean CIs** | **DONE on the crypto side** (451 arm-B cells) → `SPDR-018/addendum-p02-p03-ci-recovery.md`: median CI excludes zero on 449/451 and trimmed on 451/451, all negative, against 46/451 for the mean. **Not yet done on cTrader's 315** — and cTrader is the one universe where all three statistics currently agree (−0.560 / −0.573 / −0.080), so the check matters less here but is not redundant |
| **P3** | **CI fragility sweep** | **CLOSED 2026-07-26** on the crypto side → `SPDR-018/addendum-p02-p03-ci-recovery.md` §4: seed spans ~4.8% of CI width, block spans 0.43–0.65 bps. **No read rests on a Monte-Carlo artifact.** The same recovery applies here — the data is computed and discarded at `cells.py:127`, which 018B inherits unchanged |
| **P4** | **Determinism** (one sequential pass) + a **Bybit-holdout assertion on the §5 guard's own reads** | Both cheap; the second closes the only genuine residual Phase-0 exposure |
| **P5** | **The per-symbol spread pin** (SoT §3 axis E, blocking) | Until it exists no net figure on this universe means anything, and the cost deflator cannot be pinned |
| **P6** | **The Asia magnitude × shock interaction** — magnitude-matched **no-shock** momentum runs **+9.98 bps in Asia against −1.17 in EU** on 162–184 rows | **The only genuinely new lead in this run.** Needs its own powering attempt and a session-composition control before it is anything at all. **Register before screening** |
| **P7** | **C9 / D3 / D4 on cTrader** — a straddle runner and a cTrader ZigZag panel | D4's `ridge_cont` K=5 was the strongest D3/D4 object on crypto; its cTrader status is entirely unknown |
| **P8** | **Why is the power flag not reproducible from `gross_block_mde_mean_bps`?** | 2 cells on the σ basis, 84 on the absolute — the emission cannot be independently regenerated |

---

## 13. Artifacts

```
python/experiments/SPDR-018B/
├── design.md                       # frozen, operator-approved 2026-07-25, no amendments
├── screen.md                       # subordinate AND STALE in §2/§3/§4 — superseded by analysis.md
├── analysis.md                     # BINDING (785 lines); screen_code/ never read
├── report.md                       # this file
├── screen_code/                    # incl. add_missing_controls.py (manual post-step, §11 item 4)
├── analysis_code/b01…b08            # analyst's own re-derivation
└── results/                        # 7,578 cells; integrity_selfcheck.json (11 HARD + 1 INFORMATIVE,
                                    # 0 failed); controls.json (tripwires + arm_C_ambient_base);
                                    # deflators.json; unit_pin.json (sigma-hat 13.03);
                                    # panel_C.parquet (now persisted);
                                    # coverage_gap_C7_C8.parquet (966 rows);
                                    # coverage_gap_B3.parquet (159 cells);
                                    # analyst_per_cell_magnitudes.parquet (6,156 signed cells);
                                    # analyst_stratum_tables.csv (11 stratum views)
```

`plots/` is empty.

---

## 14. Governance record

| Item | Value |
|---|---|
| Counted TEST reads consumed | **0** |
| Multiplicity slots consumed | **0** (AMENDMENT-C3) |
| Holdout contact | **none** — cTrader 2024-12-13 and Bybit 2025-01-08 never queried |
| Family status change | **none** — `CF-VOLDIR-001` remains `REGISTERED` |
| XENA authorisation | **none** — `XENA-VOLDIR-001` remains `RESERVED` |
| Role of this universe | **REPLICATION / CREDIBILITY ONLY** — never pooled into crypto `n`, never cited as power for the crypto estimate (AMENDMENT-C1 / S1) |
| Effect on SPDR-018 | **none** — frozen and unmodified; the portability finding is recorded against it but does **not** reopen it (operator ruling) |

**No tradability, deployability, cost-complete, family-status, graduation or XENA claim is made or
implied by this document.**
