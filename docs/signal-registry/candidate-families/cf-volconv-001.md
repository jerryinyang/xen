# CF-VOLCONV-001 — Volatility-to-Direction Conversion

- **Status:** `REGISTERED` — 2026-07-22, checkpoint-016, operator-authorised
- **Chapter:** 05
- **Route:** `SPDR-011 → EXP-099` if separately authorised; no XENA
- **Reads:** TRAIN only; 0 counted TEST reads; global holdout sealed
- **Checkpoint:** `docs/experiments-docs/checkpoints/2026-07-22-016-volatility-direction-conversion/design.md`

## 1. Falsifiable thesis

A causally known high-volatility state predicts the magnitude, but not the sign, of near-future
movement. A completed four-hour break of the prior confirmed UTC-day range supplies the sign. The
family exists only if enough signed movement remains during one fixed four-hour market-entry episode
to be useful after the available fee, funding and execution-allowance accounting.

```text
MECHANISM:
  Lagged daily volatility clusters into the next day. A completed four-hour range break converts
  that directionless magnitude forecast into a causal direction. P&L is borne by one non-overlapping
  four-hour episode entered at the next four-hour boundary and exited four wall-clock hours later.
DERIVED:
  estimand=one signed four-hour episode
  null=matched non-event timing plus identical unconditional breakouts
  horizon=four wall-clock hours
  test=partial-cost episode residue and incremental volatility-state contrasts
```

This is a conversion test, not a search for a directional price pattern. The breakout itself earns no
information claim; its unconditional twin is the primary mechanism control.

## 2. Lineage and distinctness

| Prior work | Recorded result | Distinctness boundary |
|---|---|---|
| `CF-HTFCAP-001` | Real but sub-cost BTC directional/volatility interaction at 8–16h; historical TRAIN+TEST already touched | New fixed daily-volatility → completed-range-break → four-hour residue estimand; TRAIN only; no DI/ADX, XENA or hold search |
| P-01 price geometry | Price-pattern direction alone repeatedly failed | Breakout is a conversion device and is controlled by the identical unconditional breakout population |
| `CF-SIGAUC-001` | Tested signed-flow transforms added no tradable marginal value | Signed volume is one fixed last-layer modifier on the same event set, never a new pattern family |

Failure of the core volatility increment or conversion residue under adequate power closes this
direction on the existing catalog. It does not license a replacement volatility indicator, breakout,
horizon, exit, grid or signed-flow pattern.

## 3. Object identity

```text
OBJECT-IDENTITY:
  measurement object == trading object: YES — next-boundary RealOpen to RealOpen exactly 4h later
  measured conditioning event == traded entry event: YES — completed 4h close beyond prior UTC-day range
  effect-splitting windows non-overlapping: YES — later triggers ignored while an episode is open
```

The pre-trigger move is never credited. Open episodes cannot pyramid, refresh, reverse, or extend.

## 4. Frozen scope

### 4.1 Instruments and time

- Core: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `DOGEUSDT`, `XRPUSDT`.
- DESIGN: `2021-06-29T06:53Z ≤ t < 2023-03-01T00:00Z`.
- CONFIRM: `2023-03-01T00:00Z ≤ t < 2023-12-18T00:00Z`, one frozen-rule read only.
- Historical TEST: `2023-12-18T00:00Z ≤ t < 2025-01-08T00:00Z`, never loaded.
- Global holdout: `t ≥ 2025-01-08T00:00Z`, never loaded.
- A broader catalog may appear only as a gross event-supply appendix that cannot select or advance
  the rule.

### 4.2 Fixed construction

- `rv20`: square-root mean of the preceding 20 confirmed daily squared log returns.
- `vol_pct`: causal percentile against up to 252 preceding confirmed `rv20` values, excluding the
  current value; minimum 60 daily returns.
- HIGH/MID/LOW terciles fixed at `2/3` and `1/3`; continuous `vol_pct` remains primary.
- Long: completed four-hour close strictly above the prior confirmed UTC-day high.
- Short: completed four-hour close strictly below the prior confirmed UTC-day low.
- Entry: next four-hour boundary's first available one-minute `RealOpen`.
- Exit: `RealOpen` exactly four wall-clock hours later.
- Incomplete entry/path rows are excluded before outcome access and counted as availability failures.

### 4.3 Fixed conditioning arms

- Drift control: preceding 20 confirmed daily log returns summed.
- Beta control: trailing 60-day covariance with BTC divided by BTC variance; BTC beta fixed at 1.
- Cross-section: daily causal `vol_pct` rank on the five eligible symbols; lexical tie-break.
  Executable candidate is `TOP2`; TOP1/TOP3 are sensitivity arms only.
- Signed flow: trigger-bar exact aggressor imbalance, direction-aligned and ranked against the prior
  60 completed same-slot four-hour bars. Executable candidate is the upper tercile only.
- Deterministic progression: base → optionally TOP2 → optionally upper-tercile flow. No best-P&L
  threshold, symbol, side or horizon selection.

## 5. Cost and claim boundary

- Entry and exit are taker market orders: 11.0 bps round-trip fee.
- Funding counts crossed 00:00/08:00/16:00 UTC stamps in `(entry, exit]`; missing history charges
  adverse-side 1.0 bps per crossed stamp.
- Execution allowance: governing 2.0 bps round trip; 0/2/5 bps reported.
- **Spread cost unavailable and not charged.** `spread_rt_bps=null`,
  `cost_scope=PARTIAL_FEES_FUNDING_ONLY`.
- Reported cost understates total cost and reported net performance is overstated. No historical
  result may be labelled fully net, cost-complete, tradable or deployable.
- Raw `SpreadBps`, `MeanPriceSkewBps`, flip-pair values and former proxy pins are prohibited inputs.

## 6. Registered hypotheses and items

| ID | Item | Question | Planned vehicle |
|---|---|---|---|
| `HYP-001` | Partial economics | Does the HIGH-vol breakout episode retain positive residue after available fees, funding and allowance, with missing spread disclosed? | SPDR-011 L1 |
| `HYP-002` | Volatility bite | Does HIGH state predict more post-entry absolute movement than disjoint MID/LOW breakout events? | SPDR-011 L2 |
| `HYP-003` | Conversion residue | Does HIGH state improve signed residue beyond the identical unconditional breakout? | SPDR-011 L3 |
| `HYP-004` | Cross-sectional increment | Does fixed TOP2 add value beyond the all-core base under beta/occupancy-matched random top-k controls? | SPDR-011 L4 |
| `HYP-005` | Signed-flow increment | Does fixed upper-tercile aligned flow add value on the identical selected event set? | SPDR-011 L5 |
| `HYP-006` | Strategy physicality | Does the one frozen rule reproduce event membership and canonical episode/portfolio accounting in Nautilus? | EXP-099, conditional |

The five SPDR layers share one frozen event artifact. They are not five searches or five independent
runs. Each later layer requires an operator decision; TOP1/TOP3 and continuous flow are distributions,
not selectable candidates.

## 7. Controls

- Matched random timing: disjoint non-breakout opens matched on symbol, direction, UTC slot,
  volatility tercile, calendar third and hold; at least 2,000 seeds.
- Unconditional breakout: disjoint MID/LOW episodes with identical trigger/execution/hold.
- Direction derangement: same event times and occupancy, at least 2,000 seeds, zero fixed points.
- Drift-only direction and exposure-matched BTC: benchmarks, not vetoes.
- Hard future destroy: derange each outcome path to another eligible within-symbol/calendar-third
  date, zero fixed points; survival invalidates the emission/analysis.

## 8. Power, uncertainty and interpretation

- A count-only, outcome-isolated census precedes the final SPDR-011 design.
- Primary resampling is UTC-date blocks retaining cross-symbol clusters; 1/3/7-day sensitivity.
- Per-symbol results precede pooled disclosure; leave-one-symbol/calendar-third-out required.
- Mean, median and 20% trimmed mean co-report; concentration by day/week/symbol/top decile disclosed.
- Each layer reports realised MDE. `MDE > plausible increment` means `UNPOWERED`, never negative.
- CONFIRM is read only when prospective MDE is no larger than the chronologically shrunk DESIGN
  effect; it cannot select a replacement rule.
- Value bands are informative reports; only holdout, causality, provenance, future-destroy and
  canonical reconciliation are machine blocks.

## 9. Locked exclusions

No multi-day drift or carry product; no secondary/L2 branch; no XENA; no indicator/model/exit/target
search; no passive or maker assumption; no overlap/pyramiding; no historical TEST/holdout; no
spread proxy; no cheaper-execution rescue; no automatic family verdict.

## 10. Sequence and authority

1. Count-only census and final `SPDR-011/design.md`.
2. Fresh-context QA.
3. Separate operator execution approval.
4. One TRAIN-only event artifact; DESIGN L1–L5 opened sequentially.
5. Freeze one rule; one power-qualified CONFIRM read.
6. If separately authorised, design/QA/execute `EXP-099` in Nautilus.
7. Operator-signed checkpoint retrospective or frozen forward shadow.

Registration authorises design only. It does not authorise the census if it cannot be proven
outcome-isolated, SPDR execution, EXP execution, TEST, holdout, shadow or deployment.

## 11. Registration ledger

| Date | Action |
|---|---|
| 2026-07-22 | Operator authorised family registration and checkpoint-016 opening after the no-spread cost/data preflight passed QA run 10. Assigned SPDR-011; reserved EXP-099. 0 counted reads; no outcome contact. |
