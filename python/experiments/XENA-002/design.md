# XENA-002 — MTFCTX-C2: HTF context filters on a NAIVE MOMENTUM control (CTRL-02)

**Status:** QA-APPROVED ×2 (design run 1 + post-implementation run 2 APPROVE, 2026-07-11;
Amendments 1–2 NEUTRAL) — model + conf + manifest built, smoke verified (76/76 candidate
gate, golden trace 10/10); execution HARD-BLOCKED until XENA-001 retrospective read
(operator sequencing decision 2026-07-11) + operator execution approval.
**Checkpoint:** 011 (`docs/experiments-docs/checkpoints/2026-07-10-011-mtf-context-xena/`)
**Family group:** CF-MTFCTX-001 (`docs/signal-registry/candidate-families/cf-mtfctx-001.md`)
**Frozen registry:** sha256 `537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6`
(v3, 2026-07-10) — verified via `xen.xena.calibration.verify_frozen_registry` at ingest and
pasted into qa-review.md. Thresholds NEVER re-derived (X=0.70, F_floor=0.4302, gate=0.0558
GROSS null-P95; cited, not restated as claims).

## 1. Idea + mechanism

```
MECHANISM: short-horizon price continuation — a close breaking the prior 3-bar high/low range
marks initiative flow whose direction is hypothesised to persist over 0.5–4× the HTF span.
HTF context (trend strength ADX, trend direction ±DI, volatility regime) is hypothesised to
condition the quality of these LTF breakout entries: continuation should be richer when HTF
trend is established/aligned and vol regime admits follow-through. Event cadence: breakout
events when flat (~0.2–0.3/bar both sides, empirical; clustered in trends). P&L-bearing
object: the round-trip leg (entry fill → hold-period exit fill), composed chronologically by
the shared-capital oracle.
DERIVED: estimand = oracle log-wealth F over composed legs (xen.xena.oracle, gross at
selection, net informational at gate); null = frozen WS-6 calibration battery + entry-time
block-rotation permutation battery on these emissions (alignment destroy, never P&L permute —
L-14); horizon = hold-period grid {0.5,1,2,4}× HTF span (matches the continuation-horizon
hypothesis); test = frozen XENA certification + counted gross gate.
```

**Run purpose (declared).** XENA-002 is the family's first **informed** control universe:
unlike XENA-001 (random entries, null-expected), CTRL-02 entries carry naive momentum
information. The thesis read stays portfolio-level (cf-mtfctx-001, no A/B claim): whether
the machinery certifies anything, and whether filtered variants (V01–V18) are systematically
selected over baseline (V00), are the informative outputs. Sequencing per checkpoint 011:
this design + QA land now; **execution requires the XENA-001 retro read first** (operator
2026-07-11).

**KB/pitfalls check.** P-14 (HTF-DI sub-cost at 1h/5m) — not a re-run: new family, holds
0.5–4× HTF span (≥10× capture-vehicle escape clause), L-21 unit pins §4. P-01 (directional
price-geometry entries availability ≈ random) — acknowledged: CTRL-02 is deliberately naive
(a control entry engine, not a claimed edge); the registered thesis is the HTF filter effect,
adjudicated by portfolio selection. P-02 not triggered: no downstream tuning — exits are
fixed hold-periods, no optimisation of exits. L-19: no RNG in this model — determinism is
structural (no seed battery needed for the model itself; permutation battery supplies the
null draws). Native-order carve-out (EXP-013) not needed: CTRL-02 uses market orders at bar
open (CTRL-03/XENA-003 is the limit-order case).

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — oracle-composed round-trip legs of the emitted
    candidates; selection and gate read the same composed portfolio object (L-16/L-18).
  measured conditioning event == traded entry event: YES — the breakout is evaluated on the
    latest confirmed bar at the same bar-open the market order fires; filters mask that same
    decision; no post-hoc stratification (B-4).
  effect-splitting windows non-overlapping: YES — search/ranking/gate bands disjoint (§5);
    folds purged ≥ max hold horizon.
```

## 3. Universe manifest (every cell enters; no per-candidate quality gates)

| Axis | Values |
|---|---|
| Model | `MtfCtxMomentum` (C# ISignalModel, **written from scratch** — no code reuse from MtfCtxRandom or any prior model; HTF feature logic (ADX/DI, median-TR ATR, hysteresis regime) reimplemented fresh against the family spec, verified for spec equivalence at QA, never copied) |
| Filter variants | V00 baseline · V01 ADX<25 · V02 ADX≥25 · V03 DI-direction · V04/05/06 vol LOW/MED/HIGH · V07–V12 vol×ADX (6) · V13–V18 vol×ADX+DI (6) — 19 total |
| Hold multipliers | 0.5× 1× 2× 4× HTF span → LTF bars: 1d/1h {12,24,48,96}; 4h/15m {8,16,32,64}; 1h/5m {6,12,24,48} |
| Domain pairs (HTF/LTF) | 1d/1h · 4h/15m · 1h/5m |
| Instruments | USTEC US500 US2000 JP225 AUS200 US30 EU50 GER40 HK50 UK100 XAUUSD BTCUSD |
| **Total candidates** | 19 × 4 × 3 × 12 = **2,736** |

Candidate ID: `C2-<SYM>-<DOM>-H<mult>-V<nn>` (e.g. `C2-USTEC-4H15M-H2X-V07`).
Manifest file: `data/strategy_runs/XENA-002/universe_manifest.json`.

### Model pins (CTRL-02)

- **Entry signal (causal derivation, pinned):** at each LTF bar t open, on confirmed bars
  only: LONG if `Close[t−1] > max(High[t−4], High[t−3], High[t−2])`; SHORT if
  `Close[t−1] < min(Low[t−4], Low[t−3], Low[t−2])` — the signal close is compared against
  the 3 bars **strictly before it** (a close can never exceed its own bar's high, so the
  family text "close > highest high of last 3 bars" has exactly one causal reading). Strict
  inequalities; ties = no signal. Both true simultaneously is impossible.
- **Entry execution:** if flat and the signal fires and the variant's filters (confirmed
  HTF bars ≤ t−1) pass: **market order fills at that SAME bar's open** (decision-bar open,
  standard evaluate-at-open convention — XENA-001 Amendment 2 pattern; no extra delay).
  Signal ignored while holding or filter-masked. No RNG anywhere; model fully deterministic.
- **Exit:** market at bar open after hold-period bars elapsed. No other exits (fixed
  hold-period only per family spec).
- **Filters (HTF, confirmed bars only, ≤ t−1, `CloseTime` alignment, never bar indices):**
  ADX(14) Wilder, threshold 25; ±DI comparison for direction (long allowed iff +DI > −DI;
  short iff +DI < −DI); volatility regime per family pin: **median-TR ATR(14)** (rolling
  median of true ranges, window 14 — not Wilder ATR), percentile-ranked against trailing
  **250 HTF bars** (pinned from the registered 200–300 range; matches XENA-001 for
  cross-universe comparability), hysteresis HIGH entered >P80 / exited <P65, LOW entered
  <P20 / exited >P35, MID otherwise. Pinned before search, never tuned on outcomes.
- **Warmup:** signals suppressed until every feature the variant uses is defined (LTF
  breakout window: 4 confirmed LTF bars; ADX/DI: ~28 HTF bars; vol regime: 264 HTF bars).
  Disclosed: 1d-domain vol variants lose ~10 months of the search band to warmup.
- **Sizing stop (SlPrice):** `SlPrice = EntryFill ∓ 2 × HTF median-TR ATR(14)` (k=2, value
  at latest confirmed HTF bar). Sizing-only field — **no live stop orders** (family lane
  reconciliation 2026-07-10). Finite on every leg or candidate-gate REJECT.

## 4. Per-candidate cost + unit pins (L-21/L-22)

Costs excluded from selection (gross amendment A-1); charged at the NET informational gate
leg (forced in code). Pins are gate-verdict-bearing. Identical instrument set, data files,
and TRAIN-window FX pins as XENA-001 (same pre-gate window, file start → 2024-03-28, no
gate-band contact):

| Symbol | commission (FTMO table) | cost_bps RT (commission-only; +spread once pinned) | spread | money_per_unit (pin source) |
|---|---|---|---|---|
| USTEC US500 US2000 US30 | 0 (cash-CFD) | 0 + spread | **OPERATOR PIN REQUIRED pre-gate** | 1.0 (USD-quoted) |
| XAUUSD | 0.0014%/side | 0.28 bps + spread | operator pin pre-gate | 1.0 |
| BTCUSD | 0.065%/side | 13.0 bps + spread | operator pin pre-gate | 1.0 |
| JP225 | 0 | 0 + spread | operator pin pre-gate | 0.006968 (JPY→USD = 1/143.516; USDJPY median 2023-01-03→2024-03-28) |
| AUS200 | 0 | 0 + spread | operator pin pre-gate | 0.66197 (AUDUSD median, same window) |
| EU50, GER40 | 0 | 0 + spread | operator pin pre-gate | 1.08418 (EURUSD median 2023-01-02→2024-03-28) |
| UK100 | 0 | 0 + spread | operator pin pre-gate | 1.25292 (GBPUSD median, same window) |
| HK50 | 0 | 0 + spread | operator pin pre-gate | 0.128205 (HKD peg mid 7.80; USD-pegged band 7.75–7.85) |

**Spread pins are a BLOCKING precondition for the final-gate NET leg and any deployability
read** — not for emission, candidate gate, search, or certification (all gross). L-22: any
deployability claim cites the `net_informational` block. JP225 `contract_size=10` disclosed;
oracle sizes raw units.

## 5. Band boundaries (pre-registered, Q1 partition — identical to XENA-001)

Same 12 instruments, same data files, same common analysis span: start **2021-06-02T00:01Z**,
end **2024-12-11T08:19Z** (min per-file 70% analysis cutoff; binding instrument GER40).
Per-instrument 70% fences (holdout starts) as registered in XENA-001 design §5:
USTEC 2024-12-11T17:33 · US500 2024-12-19T14:58 · US2000 2024-12-12T14:32 ·
JP225 2024-12-30T00:01 · AUS200 2025-01-07T04:24 · US30 2024-12-11T23:37 ·
EU50 2025-01-29T10:38 · GER40 2024-12-11T08:19 · HK50 2024-12-30T16:50 ·
UK100 2024-12-11T19:27 · XAUUSD 2024-12-12T04:09 · BTCUSD 2025-03-12T19:22.
Final 30% of every file never touched. `AnalysisEndUtc = 2024-12-11T08:19:00Z` for ALL
emissions (uniform fence at the common end).

| Band | Start (UTC) | End (UTC) |
|---|---|---|
| TRAIN search (50%) | 2021-06-02T00:01 | 2023-03-08T00:00 |
| TRAIN ranking (30%) | 2023-03-08T00:00 | 2024-03-28T00:00 |
| TEST gate (20%) | 2024-03-28T00:00 | 2024-12-11T08:19 |

**This table IS the binding band definition**: code constructs `SegmentLayout` directly from
these pre-registered ns timestamps — `from_span` is not re-run at execution time. Folds:
**n=4 contiguous purged folds** in the ranking band, boundaries 2023-06-12 · 2023-09-16 ·
2023-12-22 (00:00 UTC), **purge = 14 calendar days** (covers the measured worst
96-trading-hour span, 11.375 d, XENA-001 QA run 2). Gate band ≫ block 64 on every LTF grid.

## 6. Run parameters

Restarts **12**, seeds = restart ids 0–11; search budget from the pre-registered smoke
procedure (3 smoke restarts, budget = iteration where best-F improvement < 1% over trailing
20% of iterations, then fixed for all 12) — XENA-001's realised budget (16000) is NOT
inherited blind; the procedure re-runs on this universe's smoke restarts. Everything else:
frozen registry values byte-checked by QA (`SearchParams()` defaults; gate mechanics fixed
in code). `certify_and_rank` / `run_final_gate` receive `registry_path` (mandatory).

## 7. Controls, tripwires, integrity

```
CONTROL frozen-machinery null calibration (structural, pre-existing):
  question answered: what certification/gate rate does this machinery produce on no-edge
    universes? WS-6 v3 battery: null certification 2/300, end-to-end false passes 0/300
    (FPR ≤1% @95%); power 70% @30 bps gross/trade, 94% @40 bps at 60-trade density —
    restated per live trade density at analysis.
  population: 550 realistic-null synthetic universes — DISJOINT from this emission.
  bite/MDE: the battery's power curve IS the MDE statement; live trade counts (§9) ≫ 60 ⇒
    battery power conservative here.
  non-vacuity: battery exercised the real code paths incl. the A-4 dual gate.
  expected outcome if filters worthless AND momentum worthless: no certification/no pass.
  disclosure: full certification evidence package regardless of outcome.
CONTROL cross-universe null anchor (XENA-001, informative):
  question answered: what does this same manifest grid produce on information-free entries
    on the SAME instruments/bands/machinery? XENA-001's certification evidence package is
    the live-data null anchor for reading XENA-002's (checkpoint-011 sequencing rationale).
  population: 2,736 random-entry candidates — disjoint by construction (no shared entries).
  disclosure: side-by-side best-F/certification comparison, informative only.
TRIPWIRE permutation-null battery (runs BEFORE any gate spend):
  causal alignment-breaking permutations of the real emitted trade streams — entry-time
  block rotation across candidates within symbol×domain (NEVER P&L permutation — L-14
  mean-invariance). Unlike XENA-001 (no structure to destroy), CTRL-02 entries are
  price-aligned: IF search/certification finds real structure, rotation MUST collapse
  best-F/P25 toward the XENA-001-like null level (expected collapse fraction → ~1 of the
  above-null excess). A certified subset whose F̂ SURVIVES entry-alignment rotation =
  leak/artifact alarm → HARD STOP, operator.
  vacuity check: rotation changes which legs coincide in time and decouples entries from
  the price paths that follow them → moves portfolio F̂/P25, the statistics certification
  reads (composition + alignment are exactly what it destroys).
TRIPWIRE oracle determinism: (bitmask, segment, seed) re-run → bit-identical F (raises on
  reconciliation drift; L-18 invariant).
HARD (block): estimand gate (xen.estimand_validation, --expect 12 instruments) before any
  analysis/search read; SlPrice finite per leg (gate_universe); holdout fence; registry
  hash match; permutation-battery alarm; XENA-001 retro read before execution (operator
  sequencing gate, this run only).
INFORMATIVE (operator judges): all F/P25 readings, certification evidence, net block,
  collapse fractions, filter-structure reads. No auto-verdicts.
```

## 8. Interpretation bands (run-level, pre-registered)

```
NO-CERT:            0 certified subsets — machinery-consistent negative for naive momentum
                    + HTF filters at portfolio level on these bands (informative, not a
                    family verdict; family status moves only at checkpoint retro).
CERT-EVIDENCE:      ≥1 certified subset — operator reviews evidence package (plateau,
                    restart dispersion, fold ranking, resim divergence) + permutation
                    battery BEFORE any gate consideration. Certification is evidence,
                    never a verdict.
GATE (if spent):    GROSS binding / NET informational (A-4); fail = negative result, no
                    threshold revision (L-23), no re-search on gate segments.
FILTER-STRUCTURE (informative): over-representation of V01–V18 vs V00 among top search
                    subsets and certified finalists — the family-thesis read; reported
                    with composition stats, never as a standalone SUPPORTED claim.
POOLED: all cross-domain/cross-instrument figures disclosure-only.
UNPOWERED strata: none binding — the run object is the portfolio; per-candidate reads are
                    not verdicts in the XENA lane.
```

## 9. Power

Search band ≈ 21.3 months. Entry cadence estimate (3-bar breakout, both sides, when flat):
~0.2–0.3 signals/bar unfiltered (order-of-magnitude estimate; empirical cadence disclosed at
analysis — breakouts cluster in trends, so effective cycle ≈ hold + 3–5 bars):
1h LTF (≈11.6k bars): H12 ≈ 700, H96 ≈ 115 · 15m (≈46k): H8 ≈ 3.8k, H64 ≈ 660 ·
5m (≈139k): H6 ≈ 14k, H48 ≈ 2.7k. All ≫ the 60-trade density of the WS-6 power curve;
battery power statements conservative here. Filtered variants (esp. vol-HIGH/LOW and
ADX≥25 combos) thin the cadence — per-variant trade counts disclosed at analysis; the
portfolio object, not per-candidate cells, carries the verdict. Vol-variant candidates on
1d domain: warmup-reduced band (~11.4 months) disclosed.

## 10. Golden trace (QA derives; developer must NOT generate)

Recipe (fully determined by §3 pins — no RNG, simpler than XENA-001): for candidates
`C2-USTEC-1D1H-H1X-V00` and `C2-XAUUSD-1H5M-H2X-V03`: (1) aggregate raw m1 to the LTF grid;
(2) walk confirmed LTF bars from warmup end; (3) first bar t where flat AND
`Close[t−1] > max(High[t−4..t−2])` (long) or `Close[t−1] < min(Low[t−4..t−2])` (short) —
and, for V03, the ±DI direction check passes on the latest confirmed HTF bar — ⇒ entry at
bar t's open, side by breakout direction; (4) exit at open of bar t+hold; (5)
`SlPrice = entry ∓ 2×HTF median-TR ATR(14)`. QA hand-computes 2–3 events per candidate
(timestamps, side, entry/exit prices from raw m1-aggregated bars, SlPrice) and diffs against
the emission before execution sign-off.

## 11. Amendments (L-23)

| # | Date | Change | Direction | Running count |
|---|---|---|---|---|
| 1 | 2026-07-11 | QA run 1 MINOR: from-scratch carve-out pinned — no code reuse from MtfCtxRandom; HTF features reimplemented fresh, spec-equivalence checked at QA | NEUTRAL | 0L/0T/1N |
| 2 | 2026-07-11 | QA run 2 REVISE resolution (operator): spec-identical HTF feature code shared across family universes ACCEPTED (cross-universe comparability); from-scratch clause scoped to entry/model logic. Developer disclosed non-clean-room feature code; QA independently confirmed spec equivalence (golden trace 10/10). | NEUTRAL | 0L/0T/2N |

(XENA-001's QA-derived pins — same-bar-open fill, binding band table, 14-day purge, TRAIN-only
FX pins — are inherited here as design content, not amendments.)

## 12. Gate plan

Ledger state at design: 0/2 slots. Intended spend: **no default gate spend** — a slot is
spent only on operator approval after the certification evidence package + permutation-null
battery. `new_data_attestation` operator-only, as always.

## 13. Execution + artifacts (deferred)

Execution blocked until the XENA-001 retrospective read (operator sequencing, 2026-07-11).
When approved: C# batch manifest runner sweeps the manifest through `tools/ctrader-cli/`;
emissions → `data/strategy_runs/XENA-002/<candidate_id>/` (fills-based contract,
`positions.parquet` + `cis_trades.parquet`, finite SlPrice). Then: `gate_universe` →
estimand gate → 12-restart LAHC (search band only) → `certify_and_rank(registry_path=…)` →
operator review. Ledger row at `docs/signal-registry/xena-runs.md` registered 2026-07-11
(this design); eval_count / distinct_subsets mandatory at close.

---

## Operational addendum (2026-07-11): EC2 search execution — status + completion runbook

Not a design change. Emission complete (2,736/2,736), candidate gate PASS, estimand gate
PASS (2,773 cells). Search runs on AWS EC2 (shared box with XENA-003; XENA-001 ran on its
own instance, terminated after 12/12 pull).

**Instance**: `i-0a64575c6bfcea2d9` (c7a.8xlarge, 32 vCPU, us-east-1, ~$1.64/h, account
801242831140), tag `xena-002-003-search`. IP at launch: 107.20.27.67 (re-check:
`aws ec2 describe-instances --instance-ids i-0a64575c6bfcea2d9
--query 'Reservations[0].Instances[0].PublicIpAddress' --output text`).
SSH: `ssh -i ~/.ssh/xena-run.pem ubuntu@<IP>`.

**Data on box**: minimal loader payload only (all `cis_trades.parquet`, one
`positions.parquet` per feed — 36 feeds × 76 candidates share the mark grid — plus the
two universe JSONs; sha256-verified after chunked upload). Full 3.1 GB emission stays local.

**Status at write (2026-07-11 ~23:30Z)**: 3-restart smoke-budget ladder (rids 100–102,
250→8000) in flight — 8000-leg. F̂@4000: 3.52/3.96/4.12; r101 F̂@8000 = 4.16 (+1% over
4000 → flattening, XENA-001-like curve). Production 12-restart LAHC (rids 0–11, budget
16000 default pending operator confirmation on smoke read) launches next, in parallel with
XENA-003's 12 (24 workers, `POLARS_MAX_THREADS=2`).

**Monitor**: workers `ps aux | grep -c "[f]ull-one"`; done
`ls ~/xen/python/experiments/XENA-002/results/search_restart_*.json | wc -l` (target 12);
smoke logs `~/smoke_XENA-002_r10*.log`.

**When 12/12 done**:
1. Pull: `scp -i ~/.ssh/xena-run.pem 'ubuntu@<IP>:~/xen/python/experiments/XENA-002/results/search_restart_*.json' python/experiments/XENA-002/results/`
2. Verify: 12 files, each `n_evaluations`/`distinct_subsets` (§10.4) + `charge_costs: false`.
3. **Terminate** `i-0a64575c6bfcea2d9` ONLY when XENA-003's 12/12 are also pulled (shared box).
4. `certify_and_rank` locally with
   `registry_path=python/experiments/INFR-006/results/xena_frozen_registry.json`
   (sha256 537d691a… mandatory), folds per the binding band table (boundaries
   2023-06-12/09-16/12-22, purge 14d, ranking band 2023-03-08→2024-03-28) → evidence
   package to operator. Permutation-null battery before any gate consideration; default
   NO gate spend (ledger 0/2); `new_data_attestation` operator-only.
