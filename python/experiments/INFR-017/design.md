# INFR-017 — Signed-Bar Tier: Provenance Audit, Column Pins, Catalog Lane, Seasonal Baselines

**Item:** INFR-017 · **Opened:** 2026-07-20 · **Status:** DESIGN — awaiting QA then operator execution approval
**Family:** CF-SIGAUC-001 (REGISTERED 2026-07-20) · **Checkpoint:** 014 §3 (D5 APPROVED)
**Source methodology:** `.ignore/what-next/orderflow/ohlc/SIGNAL-SIGNED.md` — **Phase 0** of Appendix B, plus A5 / A8 of the Assumption Register and §6.4(i). Normative; this design implements it, it does not re-decide it.
**Stage:** I (instrument building). **Tuning is free here** — outputs are *frozen inputs*, never claims. The one kill-gate (HYP-I1) is a hypothesis and carries full rigor.

---

## 1. What this item is, in one line

Make the signed data tier **real, audited, and engine-readable** — and refuse to let any later phase measure anything with an unaudited ruler.

Source Phase 0: *"Holdout carved and locked. Seasonal baselines fitted per instrument for volume, range, |Δ|, Δ/V, and spread (A5). Parameter grid pre-registered. A8 provenance audit… No results — conditions."*

**This item produces no evidence that anything works.** Every output is a parameter, a pin, or a validated instrument.

## 2. Object identity

| Item | Value |
|---|---|
| Object built | The **signed 1-minute bar**: `O,H,L,C,V` + `BuyVolume` + `SellVolume` + `NTrades` + a spread feature + derived `Δ = BuyVolume − SellVolume` |
| Source of truth | Bybit public trade archives (`https://public.bybit.com/trading/<SYMBOL>/`) — aggressor `side` per trade |
| Current materialisation | `python/experiments/INFR-011/data/staging/bars/*.parquet` (904 symbols), built by `INFR-011/scripts/stream_pipeline.py::day_to_bars` |
| Consumers | INFR-018 (instrument build), SPDR-007/008, checkpoint-015 XENA |
| Band | **TRAIN only** (`analysis_start_utc → train_end_utc`). TEST and holdout are not read by this item at all |

## 3. Pre-audit ground truth (established on disk 2026-07-20, before any design decision)

Read directly from `stream_pipeline.py:314-356` — the code that produced the staging bars:

```python
is_buy  = pl.col("side").str.to_lowercase() == "buy"
is_sell = pl.col("side").str.to_lowercase() == "sell"
...
pl.col("size").filter(is_buy).sum().alias("BuyVolume"),
pl.col("size").filter(is_sell).sum().alias("SellVolume"),
pl.col("price").filter(is_buy).mean().alias("MeanBuy"),
pl.col("price").filter(is_sell).mean().alias("MeanSell"),
...
(pl.col("MeanBuy") - pl.col("MeanSell")).alias("SpreadAbs"),
SpreadBps = 1e4 * SpreadAbs / ((MeanBuy + MeanSell) / 2)
```

Two facts follow, and they set this item's agenda:

**(a) The signed split is structurally sound.** `BuyVolume`/`SellVolume` partition `Volume` by Bybit's per-trade aggressor `side`. Measured: `|Buy+Sell − Volume| / Volume` max **3.8e-16** across BTC/ETH/SOL (float epsilon), 0 nulls. This is the exact-Δ premise the whole family rests on. It still requires the A8 audit against raw trades — internal consistency is not provenance.

**(b) The spread column is not a spread — measured, pre-registered here as the expected finding.**
`SpreadAbs = MeanBuy − MeanSell` is a **difference of mean print prices**, which is dominated by intra-minute price drift, not by the bid–ask gap. Measured **on the TRAIN band only** (`OpenTime < train_end_utc`):

| Symbol | n (TRAIN) | `SpreadBps` < 0 | null | median (bps) |
|---|---|---|---|---|
| BTCUSDT | 750,081 | **32.4%** | 158 | 0.147 |
| ETHUSDT | 745,563 | **39.9%** | 4,543 | 0.077 |
| SOLUSDT | 744,336 | **24.9%** | 6,951 | 0.910 |
| DOGEUSDT | 662,099 | 11.5% | 69,125 | 1.513 |
| XRPUSDT | 733,587 | 7.3% | 15,465 | 1.983 |

> **CORRECTION + DISCLOSURE (2026-07-20, QA run 1 Issue 2) — ADJUDICATED: CLEARED by the operator 2026-07-20.**
> The figures originally in this table (BTC n = 2,103,839, 39.6% negative, median 0.09; SOL
> n = 2,103,447) were computed by an exploratory scan over the **entire staging file**. Those files
> span 2022-07-15 → 2026-07-14 and therefore include 796,320 BTC bars at or after
> `holdout_start_utc` (2025-01-08). **That read crossed the sealed holdout.**
> - *What was read:* the univariate distribution of one data-quality column (`SpreadBps`) — count,
>   sign fraction, quantiles. No price path, no forward return, no P&L, no signal.
> - *Why it happened:* an ad-hoc characterisation scan run before the item's read paths were
>   written; the code was subsequently fenced, this table was not.
> - *Effect on conclusions:* none directional — the column is negative on TRAIN too (32.4% BTC),
>   so W2 exists for the same reason. But the specific numbers did not reproduce and are replaced
>   above.
> - *Read budget:* spends no sanctioned shot (not an edge or TEST read).
> - **OPERATOR RULING (2026-07-20): CLEARED.** The touch is recorded permanently here; the holdout
>   remains SEALED for all evidential purposes and no read was consumed. The corrected TRAIN-only
>   figures stand as the item's evidence.

A spread is non-negative by construction. A quantity negative in a third of BTC minutes and 40% of ETH minutes — the two most liquid instruments on the venue — is measuring drift, not liquidity. Two further gaps:
- `docs/references/dataset-reference.md` describes this column as having a *"tick-size floor, conservative bias"*. **No tick-size floor exists in the producing code.** The doc and the artifact disagree.
- `xen.evaluation.t1_round_trip_spread_bps` returns `stress * spread_bps` **unfloored**, so a negative value propagates into `bybit_round_trip_cost_bps` as a *negative cost* — a subsidy.

This is precisely the failure A8 exists to prevent (source: *"A framework built on an unaudited column inherits its silent errors"*). **W2 below resolves it; nothing downstream may use the column until it does.**

> **Blast radius flag (out of scope, raised not resolved).** This column and `t1_round_trip_spread_bps` are shared programme cost machinery, not family-local. Whether any prior chapter-04 cost read was affected is **not** an INFR-017 question and is not investigated here. Recorded for the operator in `results/` and the checkpoint retrospective.

## 4. Work items and exit conditions

| ID | Work item | Exit condition |
|---|---|---|
| **W1** | **A8 provenance audit** — reconcile the taker split against raw trades | For a pre-declared sample (§5), re-download raw Bybit trade CSVs and recompute `BuyVolume`/`SellVolume`/`NTrades` independently of `stream_pipeline`. Must match stored values **to rounding**. Emits `results/a8_provenance_audit.json` with per-day per-symbol max relative deviation. **This is the kill-gate.** |
| **W2** | **Spread pin** — pin the definition, characterise the defect, decide usability | Written pin of the *exact* current definition + the measured defect (§3b) + a decision among: (i) **recompute** a proper effective-spread estimator from the W1 raw trades and ship it as a new column; (ii) **floor-and-flag** the existing column; (iii) **mark UNUSABLE** as a cost input. Whichever is chosen is **frozen and hash-pinned**; the losing options are recorded with reasons. Until pinned, the column is a *relative liquidity-stress feature only* (source P4). |
| **W3** | **Shared-source dependence** | Measure and record `corr(Δ/V, SpreadBps)` per symbol on the sample. The source treats P2 (bar-flow / session-flow) and P4 (§2.5 spread regime) as separate streams; they are computed from **the same aggressor split**. If dependence is material, §2.5 spread reads may not be presented as independent corroboration of a Δ read — the constraint is written into the pin artifact and inherited by INFR-018. |
| **W4** | **`NTrades` usability** | Confirm `NTrades` supports average-trade-size (`V/NTrades`) as a z-scored participation multiplier (source Part 5 cheap upgrade). Record the secular drift caveat (order-splitting) → seasonal normalisation mandatory (A5). **Never a standalone signal.** |
| **W5** | **Signed-bar catalog lane** | A `SignedBar` custom Nautilus `Data` type + a fenced ingest writing **`data/catalog_sigbar/`** (a separate root — the pinned OHLCV catalog and its fence sha stay untouched; the lane is additive) so the **engine** reads Δ causally. Round-trip equality asserted in code; fence attestation via `xen.nautilus.catalog_fence.fence_attestation_payload`; `pipeline_version` + `config_hash` stamped on every record (INFR-013 pattern). |
| **W6** | **Seasonal baselines (A5)** | Fitted **minute-of-day × day-of-week** residual baselines **per instrument that has DESIGN-bank data** for: `Volume`, `range = High−Low`, `\|Δ\|`, **`Δ/V` separately from `\|Δ\|`** (source A5 is explicit: Δ scales with volume, normalise both), and the W2-pinned spread feature. Frozen artifact + sha256. Fitted on the **DESIGN bank only**. |
| **W7** | **Admission reconciliation** | Explain the 904 staging files vs 894 catalog ADMITTED delta symbol-by-symbol against `INFR-011/artifacts/admission-ledger.jsonl`. The signed lane inherits ADMITTED status; any signed-lane-specific exclusion is listed with a reason. No symbol enters the lane unexplained. |

## 5. Pre-registered parameters (frozen before any result is computed — source §6.1)

Declared now so nothing is chosen after seeing an outcome.

| Parameter | Frozen value |
|---|---|
| **W1 audit sample** | Symbols: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `DOGEUSDT`, `XRPUSDT` (3 majors + 2 high-cadence alts). Days: `2022-09-14`, `2023-01-11`, `2023-06-07`, `2023-11-01` (4 dates spread across the TRAIN span, all < `train_end_utc`, chosen by fixed rule — the 14th/11th/7th/1st of four evenly-spaced months — not by inspection). **20 symbol-days.** |
| **W1 tolerance** | `max |recomputed − stored| / stored ≤ 1e-9` on `BuyVolume`, `SellVolume`, `Volume`; `NTrades` exact integer match |
| **W1 failure rule** | ANY symbol-day breaching tolerance ⇒ **HYP-I1 FAIL** ⇒ family PARKED. No partial pass, no re-sampling, no tolerance revision after the fact |
| **W3 dependence threshold** | Report `|corr|` with a 95% CI; `|corr| ≥ 0.20` ⇒ independence constraint written binding into the pin. (A *reporting* threshold under INFR-016 — it constrains a downstream framing rule, it does not gate this item) |
| **W6 baseline grid** | 1,440 minutes-of-day × 7 days-of-week = 10,080 cells per instrument per metric; robust location = **median**, robust scale = **1.4826 × MAD** (consistency-corrected); cells with < 8 observations flagged `SPARSE` and fall back to the day-of-week marginal; fallback usage rate disclosed per instrument |
| **W6 fit band** | **DESIGN bank only**: `2021-06-29T06:53:00Z → 2023-03-01T00:00:00Z` (checkpoint-014 §5). CONFIRM bank untouched by this item |
| **W5 pipeline version** | `sigbar-0.1.0` |

## 6. Integrity (hard — these are the only blocking checks)

| Check | How |
|---|---|
| **TRAIN-only fence** | Every read routes through `xen.nautilus.catalog_fence`; `assert_within_fence(..., band="TRAIN")` code-asserted. TEST and HOLDOUT are never queried by this item |
| **DESIGN/CONFIRM split** | W6 fit asserts `max(ts) < 2023-03-01T00:00:00Z` in code |
| **Causality** | The signed bar carries no forward-looking field. `ts_event` = bar close (data known at close); consumers apply `≤ t−1`. Asserted by a unit test that a bar's fields depend only on trades within `[bar_open, bar_close)` |
| **Determinism** | Ingest is byte-reproducible from the same inputs: `maintain_order=True` on sort and group_by (inherited from `stream_pipeline`), fixed column order, fixed dtypes. Re-run produces identical sha256 |
| **No local accounting** | This item computes no P&L. `check_no_local_accounting` applies; no `xen.adjudication` primitives are redefined |
| **Provenance** | W1 is the audit itself; its verdict blocks everything else |

**No estimand gate.** This item emits no strategy run and makes no P&L claim, so `xen.estimand_validation` does not apply (it adjudicates emissions). The integrity substitute is the fence assertion + W1 + the determinism check — mirroring the SPDR-lane substitution rule.

## 7. Deliverables

```
python/experiments/INFR-017/
├── design.md                     # this file
├── qa-review.md                  # fresh-context QA, append-only
├── code/
│   ├── a8_provenance_audit.py    # W1 — raw-trade re-download + reconciliation
│   ├── spread_pin.py             # W2/W3 — defect characterisation + dependence + pin
│   ├── signed_bar_lane.py        # W5 — SignedBar type + fenced ingest + round-trip
│   └── seasonal_baselines.py     # W6 — A5 fit + freeze; W7 admission reconciliation
├── results/
│   ├── a8_provenance_audit.json  # KILL-GATE artifact
│   ├── column_pins.json          # W2/W3/W4 frozen pins + sha256
│   ├── seasonal_baselines.parquet + seasonal_baselines_manifest.json (sha256)
│   ├── signed_lane_manifest.json # W5 ingest attestation + fence payload
│   └── admission_reconciliation.json
├── plots/                        # seasonal curves, spread defect, dependence
└── report.md                     # verdict + what is frozen for INFR-018
```

New shared code: `xen.sigbar` (a `SignedBar` custom data type + fenced ingest + baseline fit). Placed in its own module rather than `xen.orderflow` — that package is the **MBP/L2** feature store (INFR-013 spec); this is the **bar tier** and must not be conflated.

## 8. Success criteria (verifiable)

1. `a8_provenance_audit.json` exists, covers all 20 pre-declared symbol-days, and records PASS/FAIL against the frozen tolerance.
2. `column_pins.json` states the spread definition verbatim, the measured defect, the chosen resolution with reasons for the rejected options, the W3 dependence figure with CI, and the W4 `NTrades` verdict — all hash-pinned.
3. Seasonal baselines exist for all five metrics **for every admitted instrument that has DESIGN-bank data**, fitted on the DESIGN bank only, on the full 1440x7 grid with uncovered cells materialised and `SPARSE`/fallback rates denominated on the declared grid; manifest sha256 recorded. Instruments with no DESIGN-bank bars are listed with that status — the shortfall is a reported finding, not a silent omission.
4. The signed lane round-trips: a symbol-day written to catalog and read back through the fence wrapper equals the staging source bit-for-bit on all signed fields.
5. Re-running reproduces the **parquet** sha256 and the **`pin_sha256`** (which excludes `generated_utc`). Whole-JSON shas are not stable by construction — every JSON embeds its generation timestamp — so determinism is asserted on the hashed payloads, not the files.
6. `report.md` states plainly what INFR-018 may now treat as frozen, and what it may not.

## 9. Guardrails (binding)

- **This item may not evaluate any signal, grade, or edge.** Producing a "signal fires here" figure is out of scope and would make Stage II results unattributable.
- **No threshold in `column_pins.json` may be revised after INFR-018 or later sees an outcome.** A change is a new predeclared calibration with a LOOSER/TIGHTER tag (L-23).
- **Tuning inside W2/W5/W6 is free** (Stage I). The W1 gate is not — its tolerance and sample are frozen in §5 above.
- **A8 failure is not "no edge."** It is *emission invalid → fix the data* (INFR-016 validity/value split). It parks the family; it refutes nothing.
- Nautilus conventions apply if any node is constructed: `dispose_on_completion=False` (L-30), one node per process (L-31). W5 ingest is a catalog write, not a backtest node — neither is expected to bind.

## 10. Kill-gate

**HYP-I1 — does the stored taker split reproduce from raw trades?**

| Outcome | Meaning | Action |
|---|---|---|
| PASS | The Δ premise is sound; the tier is real | Freeze pins, proceed to INFR-018 |
| FAIL | The column does not reproduce | **PARK CF-SIGAUC-001.** The family's entire warrant is the split's exactness; no downstream phase is worth running |

A spread-column resolution of "UNUSABLE" (W2 option iii) does **not** fail this gate — it constrains the cost model and the §2.5 regime layer, and is reported as a scope limit into SPDR-007's money floor.
