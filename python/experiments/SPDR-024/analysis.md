# SPDR-024 — analysis

- **Experiment:** `SPDR-024` — breakout baseline characterisation on estimands that can see the effect
- **Family / registration:** `CF-VOLDIR-001`, checkpoint-018 item 7b / Step 3b
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN only. No TEST or holdout artifact was opened at any point in producing this record.
- **Cells:** 4 — 2 signal domains (H1, H4) × 2 universes (cTrader, crypto), never pooled
- **Governing contract:** `adaptive-management-design.md`, binding except where `next-experiment-shape.md` supersedes it
- **Date:** 2026-08-07

## 0. Boundary of this record

**This record issues no verdict.** It does not say the hypothesis is supported or refuted, does not
name a winner or a best arm, does not rank arms, does not claim anything is tradable or deployable,
and does not gate the family or XENA. Where the word "pass" appears it is the literal name of an
integrity field in an artifact (`blocking_pass`, `row_accounting.pass`), never a judgement about a
measured value.

Every observation below is labelled either **observed** — a number read directly out of an emitted
artifact — or **inference** — a mechanism reading that explains observed numbers but is not itself
measured.

**No row carries a result label, and neither does this document.** Every estimate appears with its
own interval, its own population count, its own effective count and its own MDE, and the reader
compares them. Power is context: no row anywhere below is dropped, trimmed, top-N pruned or
described by its count or its MDE. This replaces two earlier versions of this document that did
label rows; both are withdrawn, and the reason is recorded in `implementation-notes.md` §6.

---

## 1. Cost scope — read this before any number

Reproduced verbatim from each run's own disclosure (`config.json`, `run_summary.json`, all four
cells, identical):

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

**Observed.** No cost of any kind is charged in this run (OD-4 / D9). Spread is not charged at all;
the declared scope is fees and funding only, and this run charges neither. Every figure in this
document is gross.

**Consequence (inference).** Two riders. Because the scale channel is a *paired* adaptive-minus-fixed
difference, a per-trade cost paid by both sides at the same rate would largely cancel — but not
exactly, because the arms differ in fill count. The selection channel is not paired in that sense:
its two populations are disjoint and differ substantially in size, so cost would not cancel there at
all. In place of charging cost, every effect emits `breakeven_spread_rt_bps` at that arm's own
round-trip count, labelled `NON_EMITTED_SCENARIO` (M7).

---

## 2. Integrity, provenance and reproduction

**Observed.** All four cells report `blocking_pass: true` on estimand validation and on the
self-check: 17 of 17 declared HARD checks run, none failed, the count reconciled against the
design's list by name (L-52 / P-23). Determinism compares a three-worker run against an independent
one-worker replay — 41 of 41 artifacts equal in each cTrader cell, 217 of 217 in each crypto cell,
none differing, with only a wall-clock stamp and the declared worker count normalised out by name.
These were regenerated on 2026-08-07 after the admission-at-fill correction; `screen.md` §3 records
why and carries the table.

**Observed.** The future-shift tripwire covers 34 arms per cell on both channels, and in no cell
does any shifted arm outperform its causal twin beyond that cell's own floor — 0 survivors
everywhere. The shift is not vacuous: it changes admission on 871–12,664 rows and committed capital
on 14,668–246,756 rows, depending on the cell.

**Observed, and this is the informative part.** Seven arm-cells carry a causal effect above their
own floor, so the tripwire had something to destroy on them. On six of the seven the shifted twin is
the same size or larger:

| Cell | Arm | causal (σ̂) | shifted (σ̂) | MDE | collapse fraction |
|---|---|---:|---:|---:|---:|
| crypto H1 | `LEVEL_FORECAST_K12` halve-high | −0.0458 | −0.0523 | 0.0305 | −0.141 |
| crypto H1 | `LEVEL_FORECAST_K4` halve-high | −0.0490 | −0.0527 | 0.0304 | −0.074 |
| crypto H1 | `LEVEL_NOW` halve-high | −0.0337 | −0.0366 | 0.0304 | −0.084 |
| crypto H1 | `SWING_GT_CUR` halve-high | −0.0438 | −0.0431 | 0.0304 | +0.016 |
| crypto H1 | `SWING_SCALE` scale-normalised | +0.0341 | +0.0281 | 0.0307 | +0.174 |
| crypto H4 | `SWING_SCALE` halve-high | +0.0648 | +0.0656 | 0.0626 | −0.012 |
| cTrader H1 | `SHOCK` halve-high | −0.0692 | −0.0576 | 0.0680 | +0.168 |

Design §9 expects a collapse fraction near 1.0 where an edge exists. The largest observed is 0.174.
**Every arm in this run that reaches its own floor produces very nearly the same effect when its
component is made available one bar earlier than it could have been.**

**Two readings, and this run does not separate them (inference).** Either the effect does not depend
on the component's information at all — consistent with §5.1, where the exposure term is 46–76% of
the movement on these arms, and a one-bar shift barely changes the gate *rate* so the exposure term
survives it almost intact. Or the tripwire has little bite on a persistent state variable: volatility
state one bar apart is nearly the same state, so the shifted gate is nearly the same gate, and
non-collapse would then say more about the apparatus than about the components. Both are consistent
with every number above.

**What the pass does and does not attest.** The HARD criterion is design §9's REJECT clause — the
shift must be non-vacuous and no shifted arm may outperform its causal twin beyond the cell's floor.
That holds in all four cells. It is **not** an attestation that the measured effects are
causally driven, and the collapse fractions above are the reason to say so explicitly.

**Two limits on what a tripwire pass can mean, recorded in the artifact rather than left implicit.**
The statistic is scale-invariant in the delta series, so a strictly proportional leak would not trip
it. And an arm whose causal effect already sits inside its cell's own floor has no edge to destroy,
so its non-survival carries no causal information — that describes **all 34 arms in cTrader H4**,
where no arm carries an edge at all and the artifact says so in its own `bite_note`. The corrected
artifact records how many arms carried an edge, which collapsed, and by how much, so a pass cannot
be read as more than it is.

**Physicality — how to read it (inference).** `estimand_validation.json` reports occupancy 0.804
against the baseline strategy's own 1.6–3.0%. That figure is computed over the union of every arm's
positions in a 38-arm lattice, so it describes the lattice's coverage, not a tradable object. The
baseline's own numbers are in §3 and are the ones to quote. `analysis_summary.json` carries this
scope warning explicitly.

---

## 3. The baseline, alone and first (OD-3)

Fixed candlestick breakout, unit size, no adaptive component. Design §6A makes this first-class, and
it is the level every later comparison is read against. Full table:
`results/analysis/<cell>/baseline_characterisation.parquet`, per symbol and pooled.

**Observed — pooled, all four cells:**

| Cell | origins | orders | fills | fill rate | gross mean (bps) | gross median | σ (bps) | win share | its own break-even | difference |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cTrader H1 | 20,061 | 5,738 | 1,695 | 0.0845 | +1.099 | +0.368 | 27.04 | 0.5145 | 0.4795 | +0.0349 |
| cTrader H4 | 5,455 | 1,647 | 491 | 0.0900 | −2.480 | −2.654 | 42.21 | 0.4379 | 0.4845 | −0.0466 |
| crypto H1 | 102,160 | 26,849 | 8,470 | 0.0829 | +5.206 | **−3.984** | 152.33 | 0.4605 | 0.4402 | +0.0203 |
| crypto H4 | 27,194 | 6,348 | 2,003 | 0.0737 | −8.802 | **−20.524** | 272.19 | 0.4314 | 0.4629 | −0.0316 |

**Observed — cTrader H1, all three symbols:**

| Symbol | origins | orders | fills | fill rate | gross mean (bps) | win share | break-even |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD | 6,882 | 2,057 | 624 | 0.0907 | +0.778 | 0.5032 | 0.4585 |
| USTEC | 6,589 | 1,810 | 501 | 0.0760 | −0.274 | 0.5110 | 0.5185 |
| XAUUSD | 6,590 | 1,871 | 570 | 0.0865 | +2.656 | 0.5298 | 0.4323 |

**Observed.** The fixed breakout converts 7.4–9.0% of eligible origins into a fill in every cell.
Gross mean is positive in both H1 cells and negative in both H4 cells. Win share clears its own
break-even in both H1 cells and misses it in both H4 cells. The break-even is gross, so charging any
spread moves it against the strategy by an amount this run cannot state.

**Observed.** In both crypto cells the mean and the median disagree in sign — mean +5.21 against
median −3.98 at H1, mean −8.80 against median −20.52 at H4, with σ of 152 and 272 bps. The average
is carried by a right tail; the typical trade loses.

**Observed.** Exit composition is a single value in all four cells: 100% `HOLD`. Realised hold is
exactly 1 domain bar on every closed position. With the four capture devices excluded (OD-11 /
OD-15), the one-bar hold *is* the strategy's exit rule, so E4 and E5 are populated but constant and
the H3 decay curve is a single point.

---

## 4. Populations and the two channels — definitions used throughout

| Field | Meaning as emitted |
|---|---|
| `eligible_origin_n` | eligible scheduled origins for that arm |
| `entry_fill_n` | actual filled entries — **admission is the stop fill**, not order creation (design §2) |
| `close_n` | actual confirmed closes |
| `common_fill_n` | origins filled on **both** comparison sides |
| `common_close_n` | origins closed on both sides — the paired population of a scale-channel row |
| `effective_origin_blocks` | resampled origin blocks behind an origin-lens interval |
| `effective_trade_blocks` | resampled paired-trade blocks behind a trade-lens interval |

A count is null where its population does not apply to that channel, and is **never** filled in from
another population. The two channels answer different questions and are never merged:

- **SCALE** — paired adaptive-minus-fixed on common-closed episodes, on the PRIMARY
  capital-normalised estimand. Uncertainty uses `effective_trade_blocks`; `effective_origin_blocks`
  is null.
- **SELECTION** — admitted-minus-declined on the origin lens, against the declined origins' emitted
  counterfactuals (E2). Uncertainty uses `effective_origin_blocks`; the trade-block count is null.

Every estimate is computed under all three declared variance treatments (V-A unchunked, V-B
fixed-time-block, V-C regime-episode) and all three are emitted. The treatment crediting the fewest
independent blocks is marked `governs`; that marks a treatment, not a result.

**Reference context, used nowhere in the artifacts.** Step-3 observed sizing effects spanning
**0.022–0.150 σ̂**. Comparing a cell's MDE against that range is how a reader judges what the cell
can see. No emitted column is derived from it.

---

## 5. Scale channel — every SIZE arm against `FIXED_SIZE_UNIT`

Full tables: `results/analysis/<cell>/scale_channel_estimates.parquet` — 360 rows per cell covering
10 arms × 2 lenses × 3 regime strata × (3 treatments pooled + per-symbol). Nothing below replaces
them.

### 5.1 The paired difference is not a measurement of the component

**Observed.** The paired difference for a SIZE arm is exactly `(risk_size − 1) × baseline_outcome`,
to a maximum absolute difference of 0.0. Its mean therefore decomposes into an **EXPOSURE** term
`(E[size] − 1) × E[outcome]` and a **SELECTIVITY** term `Cov(size, outcome)`.

**Observed.** The exposure term is 25–94% of the movement across arm-cells, median ≈ 0.65. And the
sign of the raw difference tracks the sign of the cell's baseline:

| Cell | baseline gross mean (bps) | SIZE arms with a negative estimate |
|---|---:|---:|
| cTrader H1 | +1.099 | 10 of 10 |
| crypto H1 | +5.206 | 7 of 10 |
| cTrader H4 | −2.480 | 1 of 10 |
| crypto H4 | −8.802 | 0 of 10 |

**Mechanism (inference).** Exposure arithmetic. Cutting exposure must lower the measure wherever the
baseline earns and raise it wherever the baseline loses, whatever the component is doing. A
component-level reading therefore rests on the SELECTIVITY term and on the gate-permutation control,
which preserves the gate rate and the exact multiplier distribution — so the exposure term is
identical under the null — and destroys only the gate-to-outcome association.

### 5.2 Whole-channel shape, PRIMARY lens, governing treatment

Tally convention, as in SPDR-021: `ci+` / `ci−` count intervals excluding zero on each side out of
the 10 arms in that stratum; `|est| ≥ MDE` counts estimates reaching their own floor.

| Cell | regime | `common_close_n` | `effective_trade_blocks` | median \|est\| (σ̂) | median MDE (σ̂) | ci+ | ci− | \|est\| ≥ MDE |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| crypto H1 | ALL | 8,469 | 5,058 | 0.0297 | 0.0394 | 0 | 4 | 3 |
| | HIGH | 4,639 | 2,820 | 0.0405 | 0.0527 | 1 | 4 | 3 |
| | LOW | 3,751 | 2,318 | 0.0168 | 0.0582 | 0 | 0 | 0 |
| cTrader H1 | ALL | 1,695 | 1,107 | 0.0561 | 0.0842 | 0 | 1 | 0 |
| | HIGH | 819 | 574 | 0.0706 | 0.1169 | 0 | 2 | 0 |
| | LOW | 870 | 557 | 0.0275 | 0.1186 | 0 | 0 | 0 |
| crypto H4 | ALL | 2,003 | 1,203 | 0.0350 | 0.0807 | 2 | 0 | 0 |
| | HIGH | 1,069 | 649 | 0.0456 | 0.1099 | 3 | 0 | 0 |
| | LOW | 865 | 556 | 0.0319 | 0.1194 | 0 | 0 | 0 |
| cTrader H4 | ALL | 491 | 292 | 0.0487 | 0.1639 | 0 | 0 | 0 |
| | HIGH | 289 | 173 | 0.0653 | 0.2129 | 0 | 0 | 0 |
| | LOW | 188 | 123 | 0.0399 | 0.2525 | 0 | 0 | 0 |

**Observed.** In 9 of the 12 strata no estimate reaches its own MDE. The three that do are all in
crypto H1, the largest cell — its floor of 0.0394 σ̂ is the only one below the middle of the
0.022–0.150 σ̂ reference range. cTrader H4's floor of 0.1639 σ̂ exceeds the largest effect in that
range; its median estimate is 0.0487 σ̂, about 30% of its floor.

**Observed.** The LOW stratum produces no interval excluding zero and no estimate reaching its floor
in any cell, and it carries the highest floor in every cell (0.058–0.253 σ̂ against 0.039–0.164 on
ALL). The HIGH stratum produces more intervals excluding zero than LOW in all four cells.

### 5.3 crypto H1, ALL stratum — all 10 arms in full

Governing treatment, PRIMARY lens, pooled. `exp` is the exposure share of movement; `comp` is the
component-specific part surviving the gate permutation, with its two-sided percentile in its own
null.

| Arm | est (σ̂) | 95% CI | MDE | exp | comp (σ̂) | p |
|---|---:|---|---:|---:|---:|---:|
| `LEVEL_FORECAST_K4` halve-high | −0.0490 | [−0.0781, −0.0198] | 0.0394 | 0.46 | −0.0342 | 0.000 |
| `LEVEL_FORECAST_K12` halve-high | −0.0458 | [−0.0761, −0.0157] | 0.0394 | 0.47 | −0.0316 | 0.000 |
| `SWING_GT_CUR` halve-high | −0.0438 | [−0.0721, −0.0150] | 0.0394 | 0.62 | −0.0246 | 0.001 |
| `LEVEL_NOW` halve-high | −0.0337 | [−0.0657, −0.0020] | 0.0394 | 0.63 | −0.0134 | 0.062 |
| `SWING_SCALE` scale-normalised | +0.0341 | [−0.0005, +0.0662] | 0.0397 | 0.72 | +0.0196 | 0.035 |
| `TAIL_RISK` halve-high | −0.0258 | [−0.0584, +0.0058] | 0.0394 | 0.68 | −0.0077 | 0.331 |
| `RANGE_SCALE` scale-normalised | +0.0179 | [−0.0173, +0.0527] | 0.0394 | 0.50 | +0.0079 | 0.409 |
| `SHOCK` halve-high | −0.0132 | [−0.0470, +0.0189] | 0.0394 | 0.59 | −0.0006 | 0.963 |
| `SWING_SCALE` halve-high | +0.0083 | [−0.0251, +0.0404] | 0.0394 | 0.70 | +0.0225 | 0.006 |
| `RANGE_SCALE` halve-high | −0.0015 | [−0.0363, +0.0329] | 0.0394 | 0.76 | +0.0145 | 0.073 |

**Observed.** Three arms have an estimate reaching the floor with an interval excluding zero, and
all three are **negative**: halving size in the identified high-volatility state lowered the
capital-normalised return in this cell. A fourth (`LEVEL_NOW`) has an interval excluding zero with
an estimate just below the floor.

**Observed, and it cuts across the raw ordering.** The component-specific part separates from its
own gate-permutation null on five arms, and the two `SWING_SCALE` forms are on the **positive** side
while `K4`, `K12` and `SWING_GT_CUR` are on the negative side. `SWING_SCALE` halve-high has a raw
estimate of +0.0083 σ̂ — well inside its interval — and a component-specific part of +0.0225 σ̂ at
p = 0.006, because 70% of its raw movement is exposure arithmetic pulling the other way.

**Observed, bounding the two strongest.** `LEVEL_FORECAST_K4` and `K12` are the two components
design §7 pre-declared as horizon-mismatched in the H1 domain: they forecast the volatility state 4
and 12 bars ahead of a position held one bar. That pre-declaration was made before results existed.

**Observed.** The same three arms are the only ones reaching their floor in the HIGH stratum too,
and none reaches it in LOW.

### 5.4 The per-notional lens, for the record

**Observed.** On `outcome_bps` the paired SIZE delta is exactly zero on 100% of rows in all four
cells (`exact_zero_delta_share = 1.0`).

**Mechanism (inference).** Basis points are per unit of notional, so scaling the position cannot
move them. The SIZE device is invisible to that estimand by construction, which is why the PRIMARY
estimand was changed (E6 / AMENDMENT-4). The zeros are the expected reading, not a missing
measurement, and they are cited neither for nor against any sizing statement (design §3 binding
report rule).

**Observed, and distinct.** One arm-cell per cell also shows `exact_zero_delta_share = 1.0` on the
**PRIMARY** lens: a HIGH-gated arm inside the LOW stratum never fires, so its delta is zero on every
row. The lens, the gate rate and the counts on those rows separate that case from the one above.

---

## 6. Selection channel — admitted against the declined origins' counterfactuals

Declined origins carry the fixed arm's realised outcome on that same origin (E2), instead of the
`0.0` fill that made every prior selection read void. Full tables:
`results/analysis/<cell>/selection_channel_estimates.parquet`, 96 pooled rows across the four cells
plus per-symbol.

**Observed, and it changed what is measurable.** Admission is read at the **stop fill**, which
design §2 OBJECT-IDENTITY binds it to. Read at order creation instead, the eight `PENDING_EXPIRY`
arms produce exactly the comparator's order set and no declines at all; read at the fill, they
produce 25–4,431 declined origins per arm carrying real counterfactuals, because that is the event
their rule acts on. `NAT_BREAKOUT_TAIL_RISK_PENDING_EXPIRY_DIRECT` fills 1,808 against the
comparator's 1,695 in cTrader H1.

**Observed — whole-channel shape, governing treatment, pooled:**

| Cell | arms | declined per arm | median \|contrast\| (bps) | median MDE (bps) | ci+ | ci− | \|contrast\| ≥ MDE | contrasts negative |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| cTrader H1 | 24 | 74–782 | 1.041 | 5.300 | 0 | 0 | 0 of 24 | 17 of 24 |
| cTrader H4 | 24 | 25–207 | 2.971 | 18.970 | 0 | 0 | 0 of 24 | 10 of 24 |
| crypto H1 | 24 | 657–4,431 | 4.292 | 12.553 | 0 | 0 | 0 of 24 | 2 of 24 |
| crypto H4 | 24 | 167–982 | 11.421 | 49.838 | 0 | 0 | 0 of 24 | 18 of 24 |

**Observed.** In all four cells, no contrast reaches its own MDE and no interval excludes zero on
either side, out of 96 contrasts. Median contrast is between 20% and 34% of the median floor in
every cell.

**Observed, and it does not replicate.** Reading the directions anyway, as description: cTrader H1
is 17 of 24 negative (admitted below declined) and crypto H4 is 18 of 24 negative, but crypto H1 is
**22 of 24 positive** and cTrader H4 is 14 of 24 positive. The direction flips between the two
universes at H1 and between the two domains within crypto — i.e. across both declared replication
axes.

**Observed — regime confounding, and the control on it.** Every admission rule in this run *is* a
volatility gate, so the admitted and declined populations differ by realised regime by construction.
The contrast is recomputed inside each realised state (`CONTROL MAGNITUDE-MATCH`), with the
unmatched comparator recomputed on the same covered rows so a coverage difference cannot enter the
collapse fraction. The collapse fraction is emitted only where the unmatched contrast clears its own
floor. **It is null on every row in every cell**, with `collapse_fraction_suppressed_reason`
recorded, because no unmatched contrast clears its floor anywhere in this run. Any figure quoting a
collapse percentage for SPDR-024 is a ratio of two noise draws.

---

## 7. Concentration ladder (OD-9 / OD-10)

**Observed.** The ladder is emitted for both channels at all three declared steps — every symbol
individually, pooled, and pooled with `drop-worst` / `drop-best` / both — 336 rows per cell. Nothing
is tuned at entry and no trade is selected on its own outcome.

**Observed, and it must not be confused with the estimate tables.** The ladder's pooled figure is
the unweighted mean of per-symbol means in raw units, named `unweighted_mean_of_symbol_means_raw`.
It is a different quantity from the σ̂-normalised pooled estimate the estimate tables carry under the
word POOLED, and is named so that the two are not read as one.

**Observed.** Per-symbol trade counts fall to the low tens on the thinnest crypto symbols. Those
rows are retained in full with their counts beside them; none is pruned.

---

## 8. Controls

| Control | Question | Population | Status |
|---|---|---|---|
| `FIXED-COMPARATOR` | does the arm differ from its own unconditioned form? | same origins/episodes under the fixed arm | every scale row is already this difference |
| `COUNTERFACTUAL-REJECT` | are admitted origins better than the ones the rule declined? | declined origins with emitted counterfactuals, disjoint from the admitted set | executed; §6 |
| `MAGNITUDE-MATCH` | is the contrast attributable to regime alone? | contrast recomputed inside each realised state | executed; collapse fraction null everywhere, §6 |
| `GATE-PERMUTATION` | is the gate applied to worse trades, or merely applied? | the arm's own paired episodes, `risk_size` permuted against its own outcomes within symbol | executed; §5.3 |
| `TIME-DERANGEMENT` | — | — | removed by OD-17; the future-destroy tripwire is retained and is separate |

**Observed.** The gate-permutation control reports `applicable: false` with a stated reason wherever
the gate takes one value on every row of a stratum — permuting a constant is the identity, so the
control cannot move the statistic it exists to destroy. Those rows carry the reason rather than a
null result that would read as having run.

---

## 9. Dependence (P-5)

**Observed.** Design §10 argued that no serial dependence is detectable in the trade series and that
the inherited 24-bar block therefore costs resolution for nothing. **This run's own measurement does
not support that premise.** `dependence_premise_check` returns `NOT_SUPPORTED_BY_THIS_RUN_SEE_SYMBOLS`
in every cell, naming the symbols whose autocorrelation sits outside its own noise band — 16 of 25
crypto symbols on the baseline series, and 23 symbols on at least one paired-difference series.

**Consequence (inference), and it is bounded.** V-A would overstate resolution. V-B and V-C remain,
and the treatment crediting the fewest independent blocks governs every figure quoted in this
document. All three are emitted on every row.

**Observed.** Cross-symbol contemporaneous correlation averages +0.38 in crypto (max 0.84) and +0.31
in cTrader. That is not a time-series dependence and no time-blocking treatment addresses it, which
is why the interval stays symbol-clustered (M1) under all three treatments.

---

## 10. Observations, stated symmetrically

### Consistent across cells

1. **The baseline earns gross on H1 and loses gross on H4**, in both universes, and clears its own
   gross break-even win share only on H1 (§3).
2. **The sign of every raw sizing estimate follows the sign of its cell's baseline** — 10 of 10
   negative where the baseline earns most per trade, 0 of 10 negative where it loses most. The
   exposure term is 25–94% of the movement (§5.1).
3. **Exit composition and realised hold are constants** in all four cells: 100% `HOLD`, exactly one
   domain bar (§3).
4. **The LOW regime stratum produces no interval excluding zero and no estimate reaching its floor
   in any cell**, and carries the highest floor in every cell (§5.2).
5. **No selection contrast reaches its own floor in any cell** — 0 of 96, with median contrast
   20–34% of median MDE (§6).

### Contrary, concentrated, or inconsistent

6. **Everything that reaches a floor is in one cell.** crypto H1 is the only cell with any estimate
   reaching its own MDE, and it is four times the size of the next cell (§5.2).
7. **The three arms that do reach it are negative** — halving size in the high-volatility state
   lowered the capital-normalised return there — and two of the three are the components design §7
   pre-declared as horizon-mismatched in H1 (§5.3).
8. **The gate-permutation control reorders the arms.** `SWING_SCALE` halve-high has a raw estimate
   of +0.0083 σ̂ inside its interval and a component-specific part of +0.0225 σ̂ at p = 0.006, while
   `SHOCK` has a larger raw estimate and a component-specific part of −0.0006 at p = 0.963 (§5.3).
9. **The selection sign pattern flips across both declared replication axes** — between universes at
   H1 and between domains within crypto (§6).
10. **crypto's mean and median disagree in sign in both domains**, with σ of 152 and 272 bps (§3).
11. **Every arm that reaches its own floor produces nearly the same effect when its component is
    made available a bar early.** Seven arm-cells carry an edge; six have a shifted twin the same
    size or larger, and the largest collapse fraction anywhere is 0.174 against a design expectation
    near 1.0 (§2).

### Unresolved

11. **The magnitude question for sizing, in every cell.** Every arm reaching its floor does so with
    an interval excluding zero on one side; none separates a size.
12. **The selection-quality question entirely.** 96 of 96 contrasts sit below their own floor. This
    run did not measure whether volatility admission rules pick better trades.
13. **Whether the non-collapse under the future shift means the effects are not
    information-driven, or that a one-bar shift has little bite on a persistent state variable**
    (§2). The two readings are observationally identical in this emission.
14. **Whether the HIGH-versus-LOW asymmetry is a mechanism or a sample-size artifact.** LOW is the
    thinner read and carries the higher floor in every cell, so the two cannot be separated here.
15. **Whether the crypto H1 result transports.** cTrader H1 agrees in direction on all ten arms and
    reaches no floor; the two H4 cells run the other way, which §5.1 shows is what the arithmetic
    requires given their negative baselines.
16. **What any of this looks like under real cost.** No spread is charged anywhere (§1), and the
    selection channel's two populations are disjoint and unequal, so cost would not cancel there.

---

## 11. Caveats a reader must carry

1. Cost is absent, not partial. All figures are gross and the break-even win shares in §3 are gross.
2. The PRIMARY estimand is `outcome_bps × risk_size` against a fixed unit-capital base
   (AMENDMENT-4, **unsigned**). Under it, reducing exposure can only improve the measure where gross
   expectancy is negative and only worsen it where it is positive. §5.1 exists for that reason.
3. The regime label is `level_now`, which is also the `LEVEL_NOW` arm's own gate. For that one arm,
   "stratify by regime" and "stratify by its own gate" are the same cut.
4. The tripwire and determinism attestations are being regenerated (§2). Until they land, this run
   has a valid estimand gate but no current leak or determinism attestation.
5. This run's own dependence measurement contradicts design §10's premise (§9). The most
   conservative treatment governs every figure here, which bounds the effect.
6. `estimand_validation.json` physicality describes the 38-arm lattice, not the strategy (§2).
7. OD-14's continuous-versus-discrete head-to-head exists for 2 of 8 components — the two that carry
   a numeric scale. The design declares no continuous schedule for a categorical state component.
8. Prose tables here are summaries. The complete row-level record is the parquet files under
   `results/analysis/<cell>/`, and no row is hidden.

---

## 12. Hand-off

This record issues no verdict, no ranking and no disposition. Probes that could be run against the
existing emission without a new run: per-bar mark-to-market on arm B, which is what the H3 decay
curve needs and this emission does not carry; a cost-sensitivity sweep charging each arm at its own
round-trip count, since `breakeven_spread_rt_bps` is already emitted per arm on both channels; and
regeneration of the shift and replay passes to re-run the corrected tripwire criterion. The
interpretation belongs to the operator.
