# XENA-001 — MTFCTX-C1: HTF context filters on a RANDOM entry control (CTRL-01)

**Status:** QA-APPROVED (design QA run 3, 2026-07-10; post-implementation QA run 4 APPROVE, 2026-07-11) — awaiting OPERATOR execution approval
**Checkpoint:** 011 (`docs/experiments-docs/checkpoints/2026-07-10-011-mtf-context-xena/`)
**Family group:** CF-MTFCTX-001 (`docs/signal-registry/candidate-families/cf-mtfctx-001.md`)
**Frozen registry:** sha256 `537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6`
(v3, 2026-07-10) — to be verified via `xen.xena.calibration.verify_frozen_registry` at
ingest and pasted into qa-review.md. Thresholds NEVER re-derived (X=0.70, F_floor=0.4302,
gate=0.0558 GROSS null-P95; cited, not restated as claims).

## 1. Idea + mechanism

```
MECHANISM: HTF context (trend strength ADX, trend direction ±DI, volatility regime) is
hypothesised to change the conditional quality of LTF entries. CTRL-01 strips the entry of
all information: entries are seeded pseudo-random (lambda=2), holds are fixed multiples of
the HTF span. Any portfolio-level structure XENA finds must therefore come from the HTF
filter masks (or be a machinery artifact). P&L-bearing object: the round-trip leg
(entry fill → hold-period exit fill), composed chronologically by the shared-capital oracle.
DERIVED: estimand = oracle log-wealth F over composed legs (xen.xena.oracle, gross at
selection, net informational at gate); null = the run itself is null-expected (random
entries) + WS-6 calibration battery + permutation-null battery on these emissions;
horizon = hold-period grid {0.5,1,2,4}× HTF span; test = frozen XENA certification +
counted gross gate.
```

**Dual purpose (declared):** XENA-001 is simultaneously (a) the family's random-entry
control universe and (b) the first live exercise of the XENA machinery on real emissions.
Because entries carry no information, the **null-expected outcome is: no certification, no
gate pass** (WS-6: false-pass ≤1% @95%). A certification or gate pass here is treated as a
**machinery/selection alarm, never as an edge** — routed to the permutation-null battery
and operator review. This framing is pre-registered and cannot be reinterpreted post hoc.

**KB/pitfalls check:** P-14 (HTF-DI sub-cost at 1h/5m) — not a re-run: new family, holds
0.5–4× HTF span (≥10× capture vehicle clause), unit pins below (L-21). L-19: single random
control fragility — here randomness IS the candidate set; 36 independent streams (per
symbol × domain) + 2,736 candidates form the battery; no single-seed read exists.
Native-order carve-out (EXP-013) not needed: CTRL-01 uses market orders at bar open.

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — oracle-composed round-trip legs of the
    emitted candidates; selection and gate read the same composed portfolio object (L-16/L-18).
  measured conditioning event == traded entry event: YES — filters mask the entry decision
    at the same bar-open the order fires; no post-hoc stratification of results (B-4).
  effect-splitting windows non-overlapping: YES — search/ranking/gate bands disjoint
    (§5); folds purged ≥ max hold horizon.
```

## 3. Universe manifest (every cell enters; no per-candidate quality gates)

| Axis | Values |
|---|---|
| Model | `MtfCtxRandom` (C# ISignalModel, **written from scratch**) |
| Filter variants | V00 baseline · V01 ADX<25 · V02 ADX≥25 · V03 DI-direction · V04/05/06 vol LOW/MED/HIGH · V07–V12 vol×ADX (6) · V13–V18 vol×ADX+DI (6) — 19 total |
| Hold multipliers | 0.5× 1× 2× 4× HTF span → LTF bars: 1d/1h {12,24,48,96}; 4h/15m {8,16,32,64}; 1h/5m {6,12,24,48} |
| Domain pairs (HTF/LTF) | 1d/1h · 4h/15m · 1h/5m |
| Instruments | USTEC US500 US2000 JP225 AUS200 US30 EU50 GER40 HK50 UK100 XAUUSD BTCUSD |
| **Total candidates** | 19 × 4 × 3 × 12 = **2,736** |

Candidate ID: `C1-<SYM>-<DOM>-H<mult>-V<nn>` (e.g. `C1-USTEC-4H15M-H2X-V07`).
Manifest file: `data/strategy_runs/XENA-001/universe_manifest.json`.

### Model pins (CTRL-01)

- **Entry:** at each LTF bar open: **one draw per LTF bar always consumed** (stream
  advances uniformly so all variants/holds of a (symbol, domain) share an identical
  stream). If flat and the draw signals (SELL if u ≤ −0.5, BUY if u ≥ +0.5; lambda=2
  fixed) and the variant's filters (evaluated on confirmed bars ≤ t−1) pass: **market
  order fills at that SAME bar's open** (the decision bar's open — the standard
  evaluate-at-open convention; no extra one-bar delay). Signal ignored if holding or
  filter-masked.
- **RNG pin (regenerable, L-19 D1):** splitmix64, stream seed =
  FNV-1a-64 of the string `XENA-001/C1/<SYM>/<DOM>` (36 streams; shared across all 19
  variants × 4 holds of that cell). u = ((x >> 11) * 2^−53) * 2 − 1. Constants verbatim in
  code; Python regeneration must reproduce the C# stream bit-identically.
- **Exit:** market at bar open after hold-period bars elapsed. No other exits.
- **Filters (HTF, confirmed bars only, ≤ t−1, `CloseTime` alignment):** ADX(14) Wilder,
  threshold 25; ±DI comparison for direction; volatility regime per family pin:
  **median-TR ATR(14)**, percentile-ranked against trailing **250 HTF bars** (pinned from
  the registered 200–300 range), hysteresis HIGH >P80/exit <P65, LOW <P20/exit >P35, MID
  otherwise. DI filter: long allowed iff +DI > −DI; short iff +DI < −DI.
- **Warmup:** signals suppressed until every feature the variant uses is defined (ADX/DI:
  ~28 HTF bars; vol regime: 264 HTF bars). Disclosed: 1d-domain vol variants lose ~10
  months of the search band to warmup.
- **Sizing stop (SlPrice):** `SlPrice = EntryFill ∓ 2 × HTF median-TR ATR(14)` (k=2,
  value at latest confirmed HTF bar). Sizing-only field — **no live stop orders**
  (lane reconciliation 2026-07-10). Finite on every leg or candidate-gate REJECT.

## 4. Per-candidate cost + unit pins (L-21/L-22)

Costs excluded from selection (gross amendment A-1); charged at the NET informational gate
leg (forced in code). Pins are gate-verdict-bearing.

FX rate pins = median Close over the pre-gate TRAIN window only (file start → 2024-03-28,
end of ranking band; **no gate-band contact**), from our own m1 data (files listed):

| Symbol | commission (FTMO table) | cost_bps RT (commission-only; +spread once pinned) | spread | money_per_unit (pin source) |
|---|---|---|---|---|
| USTEC US500 US2000 US30 | 0 (cash-CFD) | 0 + spread | **OPERATOR PIN REQUIRED pre-gate** | 1.0 (USD-quoted) |
| XAUUSD | 0.0014%/side | 0.28 bps + spread | operator pin pre-gate | 1.0 |
| BTCUSD | 0.065%/side | 13.0 bps + spread | operator pin pre-gate | 1.0 |
| JP225 | 0 | 0 + spread | operator pin pre-gate | 0.006968 (JPY→USD = 1/143.516; USDJPY median 2023-01-03→2024-03-28, `timebars_usdjpy_20230103_*`) |
| AUS200 | 0 | 0 + spread | operator pin pre-gate | 0.66197 (AUDUSD median, same window) |
| EU50, GER40 | 0 | 0 + spread | operator pin pre-gate | 1.08418 (EURUSD median 2023-01-02→2024-03-28) |
| UK100 | 0 | 0 + spread | operator pin pre-gate | 1.25292 (GBPUSD median, same window) |
| HK50 | 0 | 0 + spread | operator pin pre-gate | 0.128205 (HKD peg mid 7.80; band 7.75–7.85, USD-pegged; no in-house HKD data) |

**Spread pins are a BLOCKING precondition for the final-gate NET leg and any deployability
read** — not for emission, candidate gate, search, or certification (all gross). Operator
supplies FTMO-published spreads (source+date) before gate spend; unpinned spread blocks the
NET block per L-22. JP225 `contract_size=10` disclosed; oracle sizes raw units.

## 5. Band boundaries (pre-registered, Q1 partition)

Common analysis span across the 12 instruments: start **2021-06-02T00:01Z** (common data
start), end **2024-12-11T08:19Z** = min over instruments of the per-file 70% analysis-set
cutoff (binding instrument: GER40/DE40). Per-instrument 70% fences (holdout starts):
USTEC 2024-12-11T17:33 · US500 2024-12-19T14:58 · US2000 2024-12-12T14:32 ·
JP225 2024-12-30T00:01 · AUS200 2025-01-07T04:24 · US30 2024-12-11T23:37 ·
EU50 2025-01-29T10:38 · GER40 2024-12-11T08:19 · HK50 2024-12-30T16:50 ·
UK100 2024-12-11T19:27 · XAUUSD 2024-12-12T04:09 · BTCUSD 2025-03-12T19:22.
Final 30% of every file never touched. `AnalysisEndUtc = 2024-12-11T08:19:00Z` for ALL
emissions (uniform fence at the common end).

| Band | Start (UTC) | End (UTC) | 1h bars ≈ | 5m bars ≈ |
|---|---|---|---|---|
| TRAIN search (50%) | 2021-06-02T00:01 | 2023-03-08T00:00 | 11.6k | 139k |
| TRAIN ranking (30%) | 2023-03-08T00:00 | 2024-03-28T00:00 | 7.0k | 84k |
| TEST gate (20%) | 2024-03-28T00:00 | 2024-12-11T08:19 | 4.6k | 56k |

**The table above IS the binding band definition**: code constructs `SegmentLayout`
directly from these pre-registered ns timestamps (interior boundaries rounded to 00:00
UTC, NEUTRAL) — `from_span` is not re-run at execution time. Folds: **n=4 contiguous
purged folds** in the ranking band, boundaries pinned at equal calendar quarters:
2023-06-12 · 2023-09-16 · 2023-12-22 (all 00:00 UTC); **purge = 14 calendar days**
after each boundary (QA run 2 measured the worst 96-trading-hour span at 11.375 calendar
days across the 2023 Christmas/New-Year closure — 14 covers it with margin;
Amendment-5). Gate band ≫ block 64 on every LTF grid — non-degenerate.

## 6. Run parameters

Restarts **12**, seeds = restart ids 0–11; search budget from smoke-run flattening
(pre-registered procedure: 3 smoke restarts, budget = iteration where best-F improvement
< 1% over trailing 20% of iterations, then fixed for all 12). Everything else: frozen
registry values byte-checked by QA (`SearchParams()` defaults; gate mechanics fixed in
code). `certify_and_rank` / `run_final_gate` receive `registry_path` (mandatory).

## 7. Controls, tripwires, integrity

```
CONTROL universe-is-null (structural):
  question answered: does the machinery manufacture certified portfolios from noise on
    real prices/real code paths?
  population: all 2,736 candidates (random entries) — DISJOINT from any informed signal
    population by construction; it can show what no informed set can: pure selection bias.
  bite/MDE: WS-6 v3 battery — power 70% at 30 bps gross/trade, 94% at 40 bps (restated
    per live trade density at analysis); FPR ≤1% @95%.
  non-vacuity: certification + gate read the composed portfolio P25/F̂ — exactly the
    statistics selection could inflate.
  expected outcome if machinery sound: no certification / no gate pass.
  disclosure: full certification evidence package regardless of outcome.
TRIPWIRE permutation-null battery (checkpoint-011 deliverable, runs BEFORE any gate spend):
  causal alignment-breaking permutations of the real emitted trade streams (entry-time
  block rotation across candidates within symbol×domain; NEVER P&L permutation — L-14
  mean-invariance). Must reproduce the search's best-F distribution ≈ live search on
  originals (random entries ⇒ no alignment structure to destroy; a LARGE live-vs-permuted
  gap = leak/artifact alarm → HARD STOP, operator).
  vacuity check: rotation changes which legs coincide in time → moves portfolio F̂/P25
  (composition statistics), which is what certification reads.
TRIPWIRE oracle determinism: (bitmask, segment, seed) re-run → bit-identical F (raises on
  reconciliation drift; L-18 invariant).
HARD (block): estimand gate (xen.estimand_validation, --expect 12 instruments) before any
  analysis/search read; SlPrice finite per leg (gate_universe); holdout fence; registry
  hash match; permutation-battery alarm.
INFORMATIVE (operator judges): all F/P25 readings, certification evidence, net block,
  collapse fractions. No auto-verdicts.
```

## 8. Interpretation bands (run-level, pre-registered)

```
MACHINERY-CLEAN:   0 certified subsets OR certified-but-gate-fail with evidence package
                   consistent with noise (expected; supports proceeding to XENA-002/003).
MACHINERY-ALARM:   gross gate pass, or certification rate far above battery null rate,
                   or live-vs-permuted search gap — operator stop; no edge claim possible
                   from random entries by construction.
FILTER-STRUCTURE (informative only): systematic over-representation of filtered variants
                   (V01–V18) vs baseline (V00) among top search subsets — disclosure to
                   seed XENA-002/003 reading; never a SUPPORTED claim in this run.
POOLED: all cross-domain/cross-instrument figures disclosure-only.
UNPOWERED strata: none binding — the run object is the portfolio; per-candidate reads are
                   not verdicts in the XENA lane.
```

## 9. Power

Search band ≈ 21.3 months. Expected trades/candidate (draw accept ≈ 0.5/bar when flat ⇒
cycle ≈ hold + 2 bars): 1h LTF: H12 ≈ 830, H96 ≈ 120 · 15m: H8 ≈ 4.6k, H64 ≈ 700 ·
5m: H6 ≈ 17k, H48 ≈ 2.8k. All ≫ the 60-trade density of the WS-6 power curve; battery
power statements conservative here. Vol-variant candidates on 1d domain: warmup-reduced
band (~11.4 months) disclosed.

## 10. Golden trace (QA derives; developer must NOT generate)

Recipe (fully determined by §3 pins): for candidates `C1-USTEC-1D1H-H1X-V00` and
`C1-XAUUSD-1H5M-H2X-V03`: (1) compute the splitmix64 stream from the pinned FNV-1a-64
seed string; (2) walk LTF confirmed bars from warmup end, one draw per bar; (3) first
draw with |u| ≥ 0.5 while flat (and, for V03, passing the DI direction check on the
latest confirmed HTF bar) ⇒ entry at THAT bar's open (same-bar-open fill, §3), side by
sign; (4) exit at open of bar entry+hold; (5) `SlPrice = entry ∓ 2×HTF median-TR
ATR(14)`. QA hand-computes 2–3
events per candidate (timestamps, side, entry/exit prices from raw m1-aggregated bars,
SlPrice) and diffs against the emission before execution sign-off.

## 11. Amendments (L-23)

| # | Date | Change | Direction | Running count |
|---|---|---|---|---|
| 1 | 2026-07-10 | QA run 1 REVISE: fold purge 5 → 10 calendar days (weekend-safe vs 96h max hold) | TIGHTER | 0L/1T/0N |
| 2 | 2026-07-10 | QA run 1 REVISE: entry fill pinned to same-bar-open (removed §3/§10 contradiction) | NEUTRAL | 0L/1T/1N |
| 3 | 2026-07-10 | QA run 1 REVISE: band table declared binding (code consumes pre-registered ns, not from_span rerun) | NEUTRAL | 0L/1T/2N |
| 4 | 2026-07-10 | QA run 1 REVISE: FX money_per_unit pins recomputed on TRAIN-only window (search+ranking, no gate contact): JPY 0.006968, AUD 0.66197, EUR 1.08418, GBP 1.25292; cost_bps RT column added | NEUTRAL | 0L/1T/3N |
| 5 | 2026-07-10 | QA run 2 REVISE: purge 10 → 14 calendar days (measured worst 96-trading-hour span 11.375 d over 2023 year-end closure); fold boundaries pinned (2023-06-12 / 2023-09-16 / 2023-12-22) | TIGHTER | 0L/2T/3N |

## 12. Gate plan

Ledger state at design: 0/2 slots. Intended spend: **default NO gate spend** — XENA-001 is
null-expected; a slot is spent only if the operator, on the certification evidence package
+ permutation-battery result, explicitly chooses to fire the gate as a machinery
validation shot. `new_data_attestation` operator-only, as always.

## 13. Execution + artifacts

C# batch manifest runner (checkpoint deliverable) sweeps the manifest through
`tools/ctrader-cli/`; emissions → `data/strategy_runs/XENA-001/<candidate_id>/`
(fills-based contract, `positions.parquet` + `cis_trades.parquet`, finite SlPrice).
Then: `gate_universe` → estimand gate → 12-restart LAHC (search band only) →
`certify_and_rank(registry_path=…)` → operator review. Ledger row at
`docs/signal-registry/xena-runs.md` registered 2026-07-10 (this design); eval_count /
distinct_subsets mandatory at close.

---

## Operational addendum (2026-07-11): EC2 search execution — monitoring + completion runbook

Not a design change. The 12 LAHC production restarts (budget 16000, operator-directed)
run on AWS EC2 because the local machine could not be kept on.

**Instance**: `i-0321fcc9a35b511a8` (c7i.4xlarge, us-east-1, ~$0.71/h, account 801242831140).
IP at launch: 23.23.45.69 (re-check: `aws ec2 describe-instances --instance-ids
i-0321fcc9a35b511a8 --query 'Reservations[0].Instances[0].PublicIpAddress' --output text`).
SSH: `ssh -i ~/.ssh/xena-run.pem ubuntu@<IP>`.

**Monitor**:
- workers: `ps aux | grep -c "[r]un_search.py full-one"` (expect 12 while running)
- done: `ls ~/xen/python/experiments/XENA-001/results/search_restart_*.json | wc -l` (target 12)
- memory: `free -g` (OOM history: first launch needed `POLARS_MAX_THREADS=2`; if a worker
  dies check `sudo dmesg | grep -i oom`, relaunch that rid staggered:
  `cd ~/xen/python/experiments/XENA-001/code && POLARS_MAX_THREADS=2 nohup ~/venv/bin/python
  run_search.py full-one <rid> 16000 > ~/rid<rid>.log 2>&1 &`)

**When 12/12 done**:
1. Pull: `scp -i ~/.ssh/xena-run.pem 'ubuntu@<IP>:~/xen/python/experiments/XENA-001/results/search_restart_*.json' python/experiments/XENA-001/results/`
2. Verify: 12 files, each with `n_evaluations`/`distinct_subsets` (§10.4) and `charge_costs: false` (A-1).
3. **Terminate** (billing): `aws ec2 terminate-instances --instance-ids i-0321fcc9a35b511a8`
4. Proceed per pipeline state: `certify_and_rank` with
   `registry_path=python/experiments/INFR-006/results/xena_frozen_registry.json`
   (sha256 537d691a…e672a6 mandatory), folds per §5 (boundaries 2023-06-12/09-16/12-22,
   purge 14d, ranking band 2023-03-08→2024-03-28) → present evidence package to operator.
   Pre-registered reading (§1/§8): RANDOM universe ⇒ certification pass = MACHINERY-ALARM,
   never an edge. Default NO gate spend (ledger 0/2). Permutation-null battery pending
   before any gate consideration.
