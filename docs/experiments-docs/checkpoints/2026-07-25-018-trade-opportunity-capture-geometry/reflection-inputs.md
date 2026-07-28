# Checkpoint 018 — Mid-checkpoint Reflection: INPUT PACKAGE

- **Date assembled:** 2026-07-26
- **Family:** `CF-VOLDIR-001` — status remains `REGISTERED`. **No family action is taken or proposed here.**
- **Authority:** checkpoint-018 `design.md` §5 Step 2; SoT `.ignore/what-next/alts/opportunity.md`; chapter-06 governance
- **Status:** **INPUTS ASSEMBLED — OPERATOR DECISION NOT TAKEN.** The decision record is §9, deliberately unsigned. When signed it becomes `reflection-mid.md` in this directory.
- **Corrections applied:** `corrections-log.md` — independent adversarial audit 2026-07-26,
  **RELIABLE WITH CORRECTIONS**; both verdicts survive. Two critical fixes are already reflected below.
- **Binding inputs (final, not re-run here):**
  - `python/experiments/SPDR-018/analysis.md` + `report.md` — crypto, 25 Bybit perps
  - `python/experiments/SPDR-018B/analysis.md` + `report.md` — cTrader, replication only
- **What this reflection owns** (design §5 Step 2): booking each 017 open question as resolved or
  `NOT_RESOLVABLE`, and deciding **how SPDR-019/020 are parameterised**.
- **What it does NOT own:** whether SPDR-019/020 run at all. They are registered, and **SPDR-018
  carries no gating verdict** (design §2). It also does not close the checkpoint — the end-state is
  taken at the retrospective, never here, and never on a null rate.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY  (cTrader: BORROWED from Bybit AND RESCALED = DOUBLY SYNTHETIC)
  implication: every money figure understates true cost; reported net is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
  PER-SYMBOL SPREAD PIN: still OPEN and BLOCKING for any Step 3 money read (design §6 item 5)
```

---

## 0. The 20-second version

Two experiments spent 0 test reads and 0 multiplicity slots to answer the question checkpoint-017
could not: **is the trade there, and is it big enough to pay for itself?**

**The trade is there and it is exactly break-even.** Across 25 crypto perps and, independently, three
cTrader instruments, the win rate sits within a rounding error of the rate each cell would need just
to cover its *gross* zero line, and **not one powered cell out of 1,728 clears its cost floor.** The
distance to profitability is **91–96% cost, not skill.**

**The lever we hoped to pull is not a lever.** Payoff asymmetry (`W/L`) was the checkpoint's named
"unclaimed degree of freedom". It is real and it is enormously movable — exit geometry swings it 36–67×
— but it is ~97% the *arithmetic mirror* of the win rate: push one, the other moves back by almost
exactly the offsetting amount, and the average trade does not improve. This replicated on the second
asset class more tightly than on the first.

**Two questions are still genuinely open, and neither is a "no".** Shock-conditioned momentum (C2) and
the ordered volatility-flip conditioner (C3) are both **unpowered, not refuted**. The replication
attempt on C2 came back genuinely inconclusive rather than negative.

**So the honest position:** the signed branch as registered has no positive term at this cost floor,
the magnitude work still stands and still parameterises capture design, and closing the checkpoint
would require treating "we could not measure it" as "it is not there" — the exact error 017 was closed
to avoid.

---

## 1. The consolidated `(p, W, L, W/L, edge)` picture

**Crypto is the powered estimate. cTrader is credibility only — never pooled into `n`, never cited as
power** (AMENDMENT-C1 / S1). **Power counts are not comparable between the two** (different precision
bases — see L-50).

**Medians are the headline** (fat-tailed family), **with the cross-cell mean given alongside every term**
because the two differ and one conclusion turns on it (see the reading note below).

| Term | **Crypto** (25 perps, 1,413 powered) median \| mean | **cTrader** (3 instruments, 315 powered) median \| mean |
|---|---|---|
| `p` | 0.3887 \| 0.3781 | 0.4868 \| **0.4300** |
| `p_be` (gross) | 0.4025 \| 0.3859 | 0.4855 \| 0.4330 |
| **gap `p − p_be`** | **−0.0138 \| −0.0078** | **+0.0013 \| −0.0030** ← *changes sign* |
| `W` / `L` | 128.65 / 75.55 \| 128.81 / **84.69** bps | 24.66 / 20.99 \| 23.90 / 19.02 bps |
| `W/L` | 1.4844 \| **1.7548** | 1.0597 \| **1.4372** |
| `p_be_net` | 0.4992 \| 0.4641 | 0.5334 \| 0.4987 |
| **`edge = p − p_be_net`** | **−0.0728 \| −0.0860** | **−0.0544 \| −0.0687** |
| gross mean | −1.178 bps (**0.016σ**) | −0.080 bps (**0.006σ**) |
| net mean | −15.157 bps | −2.500 bps (doubly synthetic) |
| clears gross break-even | 459 / 1,413 = **32.5%** | 129 / 315 = **41.0%** |
| **clears net break-even** | **0 / 1,413** | **0 / 315** |
| gap decomposition | rate +0.0067 / cost +0.0650 → **cost 90.7%** | rate +0.0023 / cost +0.0529 → **cost 95.8%** |
| σ̂ (pooled TRAIN) | 73.00 bps | 13.03 bps |
| mirror fit `log(W/L)` on `log((1−p)/p)` | R² **0.9667**, slope 0.9408 | R² **0.9746**, slope 0.9656 |
| cells indistinguishable from the mirror | 82.8% | 93.0% |
| `W/L` movability via exit geometry | **67×** (0.150 → 10.05) | **36.4×** (0.274 → 9.975) |
| best powered cell | **+8.50** bps gross (the best with a CI excluding zero is +8.24, cost 13.62 → **net −5.38**) | **+1.389 bps** gross vs a 2.43 bps charge |
| edge negative in **every** symbol | yes — all 21 named (−0.020 to −0.160) | yes — all 3 (−0.054 to −0.106) |

> **Reading note — two traps in this table.**
>
> **1. Do not subtract the rows.** `edge = p − p_be_net` holds **exactly per cell** (max deviation
> 0.0), but **neither the median nor the mean operator is additive across cells.** Crypto: median `p` −
> median `p_be_net` gives −0.1105, while the true median `edge` is **−0.0728**. cTrader: −0.0466 versus
> a true −0.0544. Always read `edge` from its own column. *(This package initially carried the derived
> −0.1105 for crypto; corrected 2026-07-26 against `analyst_per_cell_magnitudes.parquet`. The binding
> `analysis.md` never stated a pooled `edge` — its arm-level figures are B −0.096 / C −0.057 and its
> per-symbol range is −0.020 to −0.160, all consistent with −0.0728.)*
>
> **2. One conclusion is median-dependent and must be stated carefully.** cTrader's gap to gross
> break-even is **+0.0013 on medians and −0.0030 on means** — it changes sign. Both are inside noise
> (the gross mean is 0.006σ either way), so **"`p` sits *at* its own gross break-even" is robust on both
> bases and is the claim to make.** **"`p` sits *above* its gross break-even" is NOT robust and must not
> be claimed.** Crypto's gap is negative on both bases (−0.0138 / −0.0078), and the cTrader-is-tighter
> comparison also holds on both (|0.0013| < |0.0138| on medians; |0.0030| < |0.0078| on means).
>
> **Where mean and median diverge most:** crypto `L` (75.55 vs 84.69) and both universes' `W/L`
> (1.4844 vs 1.7548; 1.0597 vs 1.4372) — the right-skew in loss size and payoff asymmetry. This is the
> same fat tail that L-51 and threads P2/P3 are about, and it is why **median/trimmed-mean CIs (P2) are
> the cheapest thing that would sharpen this table.**

**Arm split (crypto), because the two arms are different objects and must not be pooled into one story:**

| Arm | `p` | `W` | `L` | `W/L` | `p_be_net` | edge | gross | cost share of the gap |
|---|---|---|---|---|---|---|---|---|
| **B** (SPDR-013 residue) | 0.336 | 107.6 | 53.9 | **1.880** | 0.434 | −0.096 | −1.75 | 88.4% |
| **C** (SPDR-014 residue) | 0.467 | 142.1 | 124.5 | **1.136** | 0.526 | −0.057 | **+0.08** | **98.8%** |

**Arm C's rate sits 0.0007 from its own gross break-even.** There is no rate deficit to fix on arm C;
there is only a cost floor.

### 1.1 The identity is verified, not assumed

`p·W − (1−p)·L = mean` reconstructs to **1.46e-11 bps** on crypto's 24,098 signed cells and **8.53e-14
bps** on cTrader's, against a 0.01 bps tolerance. `p_be`, `p_be_net` and `edge` re-derive from `W`, `L`
and `cost` to **max difference 0.0**. Axis-B of design §3 — listed as **NEVER MEASURED** at checkpoint
open — is discharged.

**One caveat to carry into any 019/020 budget:** `p` excludes flat legs, so the identity describes the
mean over *non-flat* legs. Immaterial at the powered scale (≤0.6 bps crypto, ≤0.042 bps cTrader) but
**flat legs must still be charged their cost.**

### 1.2 The three point statistics disagree on crypto, and only one of them has CIs

| Statistic | crypto powered (gross) | cTrader powered (gross) |
|---|---|---|
| mean | **−1.18** | −0.080 |
| median | **−14.43** | −0.560 |
| 10% trimmed mean | **−11.67** | −0.573 |

The mean is the correct object for the identity (it is a mean identity and cannot be restated on
medians). But **"the cells sit essentially at gross break-even" is the most favourable of the three by
13 bps on crypto**; on the median the typical powered cell is 14 bps below zero *before* any cost. And
**median/trimmed CIs exist on 1.0% of crypto cells and 0% of cTrader cells** — so the disagreement is
under-quantified. This is thread **P2** and it is cheap.

---

## 2. Every checkpoint-017 open question, booked

Full per-item ledger with magnitudes and CIs: **`python/experiments/SPDR-018/report.md` §3**. Summary:

| Class | Count | Items |
|---|---|---|
| **Now powered and answered** | 20 | A1, A2, A3, A4, A5, A-IC, B4, B5, C1, C4, C5, C6, C7, C8, C9, D1, D2, D3, D4, D5, D6, D7, D8 (A2/A3/D2 answered as quantified WASH / two-part / disclosure) |
| **Powered, and the answer runs against registration** | 3 findings | the counter-outcome (129 negative CI-excl-0 cells vs 1 positive, **does not route**); A4 (calendar features measured zero-to-negative); `W/L` **refuted as a free degree of freedom** |
| **Still `NOT_RESOLVABLE` — a power statement, never a negative** | 7 | **B1**, **B2**, **B3** (830 cells, not the design's 125 — a premise defect), **C2**, **C3**, A3-per-symbol-DESIGN, D3/D4 residual cells |
| **NOT RUN on cTrader, never to be read as null** | 3 | C9 (`DA-STRADDLE`), D3, D4 |

**The five results most load-bearing for Step 3:**

1. **C1 — the 017 blocker is broken.** 121 powered cells at median block MDE **7.87 bps** on the object
   that gave SPDR-014 **0 of 927** at 20–796 bps. Parent parity at 9.1e-13 proves it is the same object.
2. **C5 — selection scales both sides of the identity.** Rate pinned in 0.4147–0.4795 while `W` ranges
   109.5 → 235.4 bps and `L` 94.7 → 171.1; `W/L` moves only 1.10 → 1.40. **SoT §3.1 measured, not
   argued: scaling the move scales a zero.** Corroborated independently by both ambient-base reads
   (arm B `W` +130 / `L` +88 / **`W/L` −0.174**).
3. **`W/L` is 96.7% mirror-determined**, 67× movable, free residual `log R` negative **at the centre** (median −0.0301, mean −0.0356) though positive in 32.5% of cells — the same 32.5% that clears gross break-even, by identity and
   worst for the most aggressive device (`stop`: `W/L` 10.05, gross **−37.9 bps**). 82.8% of powered
   cells cannot be distinguished from the driftless mirror at all.
4. **D8 / T-GT-CUR is the most robust positive object in either run** — 1,800 never-before-scored
   CONFIRM cells; hit rates 0.6465 / 0.6999 / 0.6781 against a base rate of 0.4674, all CIs 16–23
   points clear of base. **A magnitude object with no signed term attached.**
5. **Arm C's side-derangement**: live −12.221 bps at percentile **0.0065** (cTrader: −2.632 at 0.023,
   ~1/5 the magnitude on a 1/5.6-σ universe). **The sides carry real directional information and it
   points against the registered direction.**

---

## 3. The two threads that remain open — and why neither is a "no"

### 3.1 C2 — shock-conditioned MOMO

| | Value |
|---|---|
| Crypto (the survivor) | M-3 live **+22.6 bps** vs a magnitude-matched comparator at percentile **0.95**, one-sided p = 0.05, **n = 505**; **+37.1 bps above** magnitude-matched bars; above the 15.3 bps partial floor on that cell class |
| Crypto grid | **UNPOWERED** — 65 of 1,020 at target, 263 `NOT_RESOLVABLE`; powered C2 cells sit at gross −0.32 bps |
| cTrader replication | **NOT REPLICATED AND NOT REFUTED** |

**Why the cTrader read cannot close it** (four reasons, descending force):

1. **The comparator is not a neutral yardstick** — its own mean runs +0.97 (EU) → +3.46 (US) →
   **+12.05 bps (Asia)**, and the Asia null lies **entirely above zero** (q5 +2.09). A zero-effect arm
   reads percentile 0.000 against that.
2. **The effect vanishes where liquidity is deepest** — ASIA −13.57 (n 184) / US −1.99 (n 853) /
   **EU +0.62, pct 0.443 (n 557)**.
3. **CORRECTED — this leg was stated wrongly and now points the other way.** The like-for-like cell
   (n=290) **was** powered for an effect of crypto's magnitude: its plant curve is {+5: 0.285, +10:
   0.755, **+20: 1.000, +40: 1.000**}. It measured **−9.383 bps at pct 0.043** — the opposite sign.
   **That strengthens "not replicated" and removes one of the four supports for "not refuted".** The
   Asia *session* control is separately blind upward (a +20 bps plant reaches only 0.115), which is a
   different and still-valid point about the session decomposition.
4. **The comparator level is construction-dependent** — an independent rebuild reproduces every *live*
   value exactly but shifts the comparator 2.3–3.4 bps and **flips the `P-MR` read** (0.067 → 0.826).

> **Binding on all downstream writing:** 018B's C2 evidence may be cited only as a *"does not transport
> cleanly"* flag. It may **not** close the thread and may **not** be reported as a cross-asset-class
> reversal. And the crypto survivor remains **one 505-row control cell against a 37,791-cell grid**,
> at exactly the 0.95 boundary, against a null with sd 22.35 bps, with spread uncharged.

**Standing methodological consequence (now P-24):** *a magnitude-matched percentile is uninterpretable
without the comparator's own mean, null quantiles and plant curve reported alongside it.*

### 3.2 C3 — ordered `last_k` volatility flip

**NOT_RESOLVABLE, decisively: 127 of 6,987 at target; 1,946 cells = 55% of the entire unresolved
population.** Median n 102 events. Powered C3 cells sit at gross **+0.34 bps** — the only positive
item-level gross median in arm C.

This is **precisely the "conditional direction is unpowered, not refuted" object the checkpoint premise
names** (design §2), and it is still that. Pooling plus σ̂-normalisation did not close it in the
registered event-nested form.

### **ANSWERED 2026-07-26 (thread P4) — C3 is terminally unpowerable, and this is the answer**

`python/experiments/SPDR-018/addendum-p04-c3-reachability.md`. Pure arithmetic over the emitted
`not_resolvable.json`; no re-run, no catalog read.

**All 1,946 unresolved C3 cells are already pooled + σ̂-normalised on the full TRAIN span — every design
§5 lever is spent.** Median realised `n` = **140 events** at a block MDE of **90.2 bps** against a
10 bps target; median required `n` = **10,450**, an **81× shortfall**.

The event rate is what closes it: **3 events per 10,000 bars**. At that rate the shortfall converts to
calendar span as:

| Required 25-symbol history | Share of C3 unresolved cells |
|---|---|
| more than **20 years** | **88.3%** |
| more than **100 years** | **64.5%** |
| median requirement | **200.6 years** |
| most favourable single cell | 3.1 years |

**The distinction that makes this defensible:** it is *not* arithmetically impossible — the required
`n` is only **0.02×** the absolute ceiling of one event per bar per symbol. It is impossible **at the
registered conditioner's own event rate**. So the only route to powering C3 is changing its event
definition, which is a **different object and a new registration** — precisely what SPDR-018 was
forbidden from doing (*original statement, no estimand substitution*).

> **Consequence for the retrospective.** C3 may now be closed over **without violating B-5**, provided
> it is booked as **terminally unpowerable in its registered form**, never as *refuted*, and provided
> the recorded reason is this arithmetic rather than the absence of a positive finding. "We measured it
> and it isn't there" is false. "The registered object cannot be measured on any obtainable crypto
> history" is true.

**This does not say the C3 mechanism is absent.** The powered C3 cells sit at gross **+0.34 bps** — the
only positive item-level gross median in arm C, and far below any cost floor. A measured magnitude, not
an edge.

---

## 4. Open threads, consolidated and costed

| # | Thread | Cost | Why it matters to this reflection |
|---|---|---|---|
| **P1** | ~~Re-run M-3 on `shock_flag` at `n` in the thousands~~ | — | **SKIPPED BY OPERATOR 2026-07-26** (no 018C). Consequence: **C2 can never be settled on this data.** At the retrospective it must be booked as **unresolved-and-parked — a terminal `NOT_RESOLVABLE`, explicitly NOT a refutation** (B-5). Note the audit correction: the like-for-like cTrader cell WAS powered for an effect of crypto's size and saw the opposite sign, so "not replicated" is better supported than first written |
| **P2** | Median / trimmed-mean CIs | **partly DONE** | **DONE for the 451 powered arm-B `per_symbol` cells** → `SPDR-018/addendum-p02-p03-ci-recovery.md`. **Changes the wording, not the verdict:** median CI excludes zero on **449/451**, trimmed on **451/451, all negative**; the **mean** CI on only **46/451**. "Sits at gross break-even" is the *only* one of the three statistics that fails to reject zero — the negative read gets **stronger**. Identity conclusions unaffected (it is a mean identity). **Still open: arm C (534) and the `trail`/`stop` populations** |
| **P3** | CI fragility sweep | **DONE** | **CLOSED 2026-07-26**, same 451 cells. Seed spans **~4.8% of CI width** (p95 0.067); block spans **0.43–0.65 bps** against 2–18 bps effects. **No read in either run rests on a Monte-Carlo or block artifact** — retroactively supports every CI-based conclusion in both reports and closes the INFR-004 / L-20 gap for this stratum. P3 was never a missing method: computed on all 37,791 cells, discarded at `cells.py:127` |
| **P4** | ~~Is C3's required `n` reachable?~~ | — | **ANSWERED 2026-07-26** → `SPDR-018/addendum-p04-c3-reachability.md`. **C3 is terminally unpowerable in its registered form:** all 1,946 unresolved cells are already pooled+σ-normalised on full TRAIN (no lever remains), median **81× short**, and at the conditioner's own event rate (3 per 10,000 bars) the median cell needs **201 years** of 25-symbol history — 88.3% need >20y. **Unpowerable, NOT refuted.** §3.2 is answered |
| **P5** | **Per-symbol spread pin** (SoT §3 axis E) | Infra | **Already declared BLOCKING.** The difference between "misses by 0.65 bps" and "nowhere close". No capture design should be parameterised before it exists, and the cTrader deflator cannot be pinned without it |
| **P6** | Determinism (one sequential pass) + a Bybit-holdout assertion on 018B's §5 guard reads | **Cheap** | Closes the only residual Phase-0 exposure in the evidence base |
| **P7** | **The Asia magnitude × shock interaction** — magnitude-matched **no-shock** momentum ≈ **+9.98 bps in Asia vs −1.17 in EU**, on 162–184 rows | Medium | **The only genuinely new substantive object either run produced.** Unregistered — **must be registered before it is screened** (SoT §7 exploration guardrail; L-controlled thesis-shopping is allowed, un-registered screening is not) |
| **P8** | C9 / D3 / D4 on cTrader; arm-C parent parity on the remaining 2,323 crypto cells; why the 018B power flag is not regenerable (317 vs 315) | Low–Medium | Completeness, not decision-relevant |

**P2, P3, P4 and P6 are all cheap, in-scope, and change how the evidence reads. P5 is already
blocking.** None of them requires a new experiment.

---

## 5. The three checkpoint end-states, with the evidence for and against each

Design §9: exactly one is taken **at the retrospective**, never here.

| End-state | Evidence FOR | Evidence AGAINST / what forbids it |
|---|---|---|
| **1. Terminal capture-geometry package** — the residue is powered and no cell clears `p_be_net`; the `W/L` handle does not move it | 0 of 1,413 and 0 of 315 clear `p_be_net`; 0 cells with a `gross_edge` or `net_edge` CI-low above zero; the gap is 91–96% **cost**; `W/L` 96.7% mirror-determined and 67× movable **without lifting the mean**; free residual negative at the centre (median log R −0.0301) though positive in 32.5% of cells; selection scales both sides (C5 + both ambient-base reads); **edge negative in all 24 named symbols across both universes**; the whole picture **replicated on an independent asset class, more tightly** | **Two things forbid taking it now:** (a) **C2** is a surviving M-3 thread that 018B could neither replicate nor refute; (b) **3,559 `NOT_RESOLVABLE` crypto cells, 55% of them C3** — the exact object the premise names as *unpowered, not refuted*. **Closing over these reads UNPOWERED as a negative, which B-5 forbids and which is precisely the error checkpoint-017 was closed to avoid** |
| **2. Graduated base for XENA** — some cell clears `p_be_net` | — | **Nothing clears it, on either universe, at any horizon, on either band.** Best crypto cell: +8.24 bps gross → **net −5.38**. Best cTrader cell: +1.389 bps against a 2.43 bps charge. Not available on this evidence |
| **3. A powered counter-outcome that routes** | **129 powered crypto cells with a gross-mean CI excluding zero, all negative** (median −4.12, max −12.93 bps) — a genuine powered directional statement that the registered side loses; corroborated by C8's mean-reversion lean (`p_momo` ≈ 0.468) and arm C's side-derangement (pct 0.0065). **This is a positive quantification and must not be filed as a null** | **It does not route.** 0 of 129 clear even the *partial* cost floor when flipped; best flipped gross +12.93 vs 13.1–16.0 bps; best flipped **net −0.65 bps**. On cTrader there is **no enriched tail at all** (12 negative / 2 positive of 315 ≈ nominal expectation). **Checked and not satisfied at this cost floor** |

**Where the evidence points:** end-state 1 — **but it is not takeable while C2 and C3 stand.** That is a
statement about sequencing, not about the strength of the negative.

---

## 6. What this evidence permits and forbids for SPDR-019 / SPDR-020

**Both are registered. Neither is gated on a SPDR-018 outcome** (design §2). This reflection sets their
**parameterisation**.

### 6.1 Three hard constraints the evidence places on any design

1. **The joint sits at break-even on two independent universes.** SoT §1.1's gate — *a capture design
   cannot manufacture expectancy out of a joint `(p, W, L)` that sits at break-even* — now binds on two
   asset classes. **Any 019/020 proposal must NAME the mechanism that puts `R = p·W/((1−p)·L)` above 1,
   because five distinct exit devices spanning a 36–67× range of `W/L` did not, on either universe.**
   Demand the mechanism, not a search.
2. **Do not parameterise off a powered subset's magnitudes without the L-51 three-number check**
   (payoff-scale ratio powered÷excluded; sign-share differential; mean-vs-median gap in the excluded
   set). The worked example is ten `trail` cells at +7 to +23 bps drawn from 116 excluded cells
   averaging **−27.6 bps**, every one with a CI-low above zero.
3. **Do not state any threshold in absolute bps across a universe boundary** (L-50). σ̂ is 73.00 on
   crypto and 13.03 on cTrader. State targets in σ units or re-derive per universe.

**Plus the standing refusals**, unchanged and still binding: no expectancy claim from exits/holds/sizing
on a joint that does not clear `p_be_net` at power; nothing phrased against `p > 0.5`; no blended
opportunity score without its term-level decomposition; sizing changes variance, not mean; no researching
direction prediction (entries stay simple and fixed; direction is **measured, not targeted**).

### 6.2 What the evidence says each strategy can still legitimately be

- **`SPDR-019`** (fixed signed breakout + opportunity-modulated capture): its three hyperparameters map
  onto the identity terms, and **its own `p_dir` and `κ` must be measured first** or later changes are
  misattributed. **A zero baseline edge is a predeclared, acceptable outcome** — and on this evidence it
  is the *expected* one. Its honest value is as **apparatus**: the first vehicle that measures `W/L`
  under a *designed* capture policy rather than under the parents' incidental exit geometries.
- **`SPDR-020`** (E-TOUCH/E-CLOSE grammar, direction-aware capture): two carry-forward fixes are now
  informed by data — the band must actually **select** (SPDR-014's `p_event` was 0.938–0.998), and the
  DESIGN→CONFIRM sign flip **has been shown to be a power/weighting artifact** (C7: flip rate *below*
  chance on both universes; `n`-weighted bands agree to 0.33 bps crypto / 0.65 bps cTrader). That second
  fix is **discharged by SPDR-018 and need not be re-litigated in the 020 design.**
- **The measured E-TOUCH > E-HORIZON > E-CLOSE ordering** (~3–4 bps crypto, ~1/5 that on cTrader,
  replicated in sign) is real structure below the cost floor — usable as a design input, not as an edge.

### 6.3 The honest caveat that keeps §1's conclusion falsifiable

SPDR-018/018B measured `W/L` under the **parents' own exit geometries**, not under a designed capture
policy. They show that the five geometries present in the data all sit on the zero line. They **cannot
rule out** that some geometry outside this grid sits off it. What they do is **raise the bar** — and
that is exactly the gap SPDR-019/020 exist to probe, provided they are framed as measurement rather
than as an edge search.

---

## 7. Decision options for the operator

Each is a *sequencing* choice. None closes the checkpoint; none takes a family action.

| Option | What it means | Consequence |
|---|---|---|
| **A — Resolve the cheap threads first, then design 019/020 as apparatus** ⭐ **RECOMMENDED** | Run **P2, P3, P4, P6** (all cheap, all in-scope, no new experiment) and press on **P5** (the spread pin, already blocking). Then design SPDR-019/020 as **apparatus / characterisation**, carrying the §6.1 constraints, with the "name the mechanism for `R > 1`" requirement written into the design | The evidence base becomes fragility-checked and Phase-0 clean before anything is parameterised off it; P4 may convert C3 from an open lead into a recorded answer; 019/020 proceed with an honest frame and a predeclared acceptable-zero outcome |
| **B — Design 019/020 immediately, resolve the threads in parallel** | Same designs, but do not wait | Faster, but 019/020 get parameterised off means whose medians disagree by 13 bps and whose CIs have never been fragility-tested (P2/P3), and against a cost floor that is still unpinned (P5) |
| **C — Press C2 first (P1) before anything else** | Treat the one surviving live thread as the priority: re-run M-3 at `n` in the thousands on the powered grid strata, multiplicity treated, comparator mean disclosed | Settles the single question that most affects whether end-state 1 is takeable at the retrospective. Costs more than A's threads and delays 019/020 |
| **D — Take end-state 1 now and close** | Declare the terminal capture-geometry package | **Not available on this evidence.** It requires reading C2 and 3,559 `NOT_RESOLVABLE` cells as negatives, which B-5 forbids. Recorded here only so the refusal is explicit |

**Recommendation: A**, with **P1 (option C's substance) scheduled straight after** — the cheap threads
change how every number in §1 reads, and P1 is the only probe that can settle C2, but neither needs to
block the 019/020 *designs* if those designs are framed as apparatus and carry the §6.1 constraints.

**One question, plainly:** do you want the cheap integrity and uncertainty threads (P2/P3/P4/P6) run
before SPDR-019/020 are designed, or in parallel with them?

---

## 8. Governance state entering the reflection

| Item | Value |
|---|---|
| Counted TEST reads consumed by SPDR-018 + SPDR-018B | **0** (lifetime cap untouched) |
| Multiplicity slots consumed | **0** (AMENDMENT-C3 disclosed-not-rationed; AMENDMENT-C4 records the tail counts) |
| Holdout contact | **none** — Bybit 2025-01-08 and cTrader 2024-12-13 never queried. One recorded gap: no HARD assertion that 018B's §5 cross-universe guard reads stayed inside the Bybit TRAIN fence (P6); no violation is evidenced |
| Family status | `CF-VOLDIR-001` **REGISTERED**, unchanged. Transitions are retrospective-only |
| XENA | `XENA-VOLDIR-001` **RESERVED**; not discussable until Step 3 graduates a cost-surviving base under separate authority |
| Spread pin | **OPEN / BLOCKING** (design §6 item 5) |
| New knowledge-base entries | **L-50, L-51, L-52, L-53**; dead ends **P-21…P-25** |
| Unregistered lead | **P7** — Asia magnitude×shock. **Register before screening** |
| Outstanding engineering | `SPDR-018B/screen_code/add_missing_controls.py` is still a manual post-step any re-run silently undoes (L-52) |

---

## 9. OPERATOR DECISION — *unsigned*

```
DECISION RECORD (to be completed by the operator; this section is deliberately blank)

  Date:
  Option taken (A / B / C / D / other):
  Booking of the 017 residue:            [ ] accepted as recorded in SPDR-018/report.md §3
  C2 ruling accepted (not replicated,
    not refuted; may not close the thread): [ ]
  Ruling on SPDR-018B's seven un-run
    inherited HARD checks:               [ ] accept with them recorded  [ ] require P6 first
  Thread priority ordering:
  SPDR-019 / SPDR-020 framing:           [ ] apparatus / characterisation  [ ] other (state)
  Notes:

  Operator signature:
```

**On signature this document is renamed / superseded by `reflection-mid.md` in this directory, per
design §5 Step 2.**

---

**No family action, end-state decision, tradability, deployability, cost-complete, graduation or XENA
claim is made or implied by this document. The mid-checkpoint reflection does not close the checkpoint
on a null rate (design §5 Step 2).**
