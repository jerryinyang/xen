# SPDR-013 — Direction expectancy (SMA + ZigZag)

- **Family:** `CF-VOLDIR-001` · **Checkpoint:** 017 · **Lane:** SPDR (TRAIN-only)
- **Status:** `DESIGN COMPLETE — DEFAULT EXECUTION AFTER SPDR-012 GATE; OPERATOR MAY OVERRIDE SEQUENCE`
- **Hypothesis:** `CF-VOLDIR-001/HYP-B`
- **Governing:** RAW §3B/§5.2; checkpoint-017 §5B/§8.2; chapter-06 governance; `spdr-lane.md`
- **Produces:** per-arm expectancy in **bps** under frozen TF capture geometry; availability-when-right;
  damage-when-wrong; comparison to SMA benchmark; **not** win-rate as primary
- **Must not produce:** tradability/deployability claim; vol×direction combination (that is SPDR-014);
  range-break as primary direction; TEST/holdout contact

**0 counted reads, 0 slots.** Win-rate may be disclosed only as a secondary diagnostic.

---

## §0 Scope fence

| | |
|---|---|
| **Vehicle** | Vectorised Python, fenced 1m → **1h and 15m decision clocks** — both **mandatory first-pass** (full arm suite on each) |
| **Band** | DESIGN `[2021-06-29T06:53Z, 2023-03-01T00:00Z)` primary. CONFIRM `[2023-03-01, 2023-12-18)` one TRAIN-internal verify. TEST/holdout never |
| **Symbols** | Same **top-25 volume universe** as SPDR-012 (AMENDMENT-U1; `universe_top25.json`) |
| **Start gate** | Default: SPDR-012 analysis complete (PASS or STOP on combo path). Operator may authorise SPDR-013 after SPDR-012 data exists even if combo STOP |
| **Forbidden direction device** | SPDR-011 confirmed prior-UTC-day range break as primary |

### §0.1 Universe pin (family-wide AMENDMENT-U1)

Identical to SPDR-012: top 25 by 30d `sum(close×volume)` on TRAIN 1m bars ending at
`train_end_utc` (2023-12-18). Pinned list in `results/universe_top25.json` and
`docs/signal-registry/candidate-families/cf-voldir-001-universe.json`. Code must recompute and
assert equality. Sparse DESIGN coverage → UNPOWERED, not silent drop.

**AMENDMENT-U1:** five-name core → top-25 — DIRECTION: **NEUTRAL** (pre-execution).

```
SPREAD-COST-DISCLOSURE:
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: partial_net understates true cost; reported expectancy overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## §1 Mechanism + question

**One question:** Do **fast, simple** direction policies (mid-term SMA benchmark; ATR ZigZag
structure) deliver positive **expectancy in bps** when scored by how much is available when right
and how adverse when wrong — under frozen cut-loser / let-winner capture geometry?

```
MECHANISM: Directional pressure on liquid perps is partially captured by mid-horizon trend
filters that act *before* multi-hour confirmation devices. A mid-term SMA (buy above / sell
below) is the intentionally dumb benchmark. ATR ZigZag supplies alternating swing structure:
after a swing completes, the next structural leg is opposite by construction; path-local
features (magnitude, angle, noise about the line) describe the completed swing and may forecast
the *size* (magnitude and/or volatility) of the next whole move. P&L-bearing object of this
screen is a single-leg episode under TF capture geometry (enter on signal, cut losers quickly,
let winners run), measured open-to-open in bps after partial costs.

DERIVED:
  estimand = per-episode partial_net_bps and the expectancy decomposition
             (p_right, avail_when_right, damage_when_wrong); optional next-swing magnitude/vol
             forecast skill (secondary)
  null     = (i) direction-label derangement within (symbol × calendar-third); (ii) matched
             random-entry same side/slot occupancy battery ≥200 seeds; (iii) flat (no-trade) = 0
  horizon  = path-dependent under TF rules (stop / opposite signal / time cap §4) — native to
             the capture geometry, not a fixed 4h late-break object
  test     = mean expectancy bps with date-block CI; decomposition table; collapse under
             derangement; SMA as benchmark baseline for ZigZag arms
```

**Anti-L-13:** capture geometry and expectancy decomposition are native to TF/ZigZag direction
products; not SPDR-011’s fixed 4h post-break residue.

---

## §2 Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: YES.
    Both are the single-leg episode defined by entry at decision-bar open after signal and exit
    under §4 TF rules. Expectancy is the mean partial_net of those episodes.
  measured conditioning event == traded entry event: YES.
    Signal is decided on completed bar i (features ≤ i). Entry = RealOpen of bar i+1 (first
    actionable open). No resting limit; no fill at the decision bar’s close.
  effect-splitting windows non-overlapping: YES.
    Per symbol at most one open episode; new signals ignored until exit (no pyramid).
    Outcome path measured from entry open to exit open only.
```

---

## §3 Decision clock and features

### 3.1 Bars

- Aggregate fenced 1m → **1h** and **15m** complete bars (mandatory both clocks).
  - H1 complete if ≥48 minutes; **M15** complete if ≥12 minutes in the slot.
- `O,H,L,C` = first open / max high / min low / last close of the slot.
- ATR(14)[t] = Wilder ATR on completed bars **of that clock** ≤ t; used only lagged: ATR(14)[t−1]
  at decision t (never mix H1 ATR into M15 stops or vice versa).

### 3.2 Arm D-SMA (benchmark)

| Parameter | Freeze |
|---|---|
| Periods | **14**, **25**, and **50** — all three **mandatory** on every decision clock |
| SMA | Simple mean of completed closes `C_{t-n+1}…C_t` |
| Signal at t | `+1` if `C_t > SMA_t`; `−1` if `C_t < SMA_t`; `0` if equal (no flip) |
| Angle filter | **OFF** and **ON** both **mandatory** on every period × clock: ON requires \|SMA_t − SMA_{t-3}\| / ATR(14)[t−1] ≥ 0.15 else flat (0) |
| 200-SMA | **Forbidden** |
| Grid size | 3 periods × 2 angle × 2 clocks = **12 D-SMA cells** per symbol (all run) |

Position: follow signal; on change from +1 to −1 (or reverse), close and reverse at next open
subject to §4 stops (stop may exit earlier without reverse until next signal).

### 3.3 Arm D-ZZ (ATR ZigZag)

| Parameter | Freeze |
|---|---|
| ATR | period 14, Wilder |
| Reversal threshold | **2.0 × ATR(14)** from extreme (standard ATR ZigZag) |
| Confirmation | swing end confirmed when close reverses from last extreme by ≥ threshold |
| Line features (at confirmation of swing k) | **magnitude** = \|end − start\| / start × 1e4 bps; **direction** ∈ {+1,−1}; **angle** = magnitude / max(1, bars_in_swing); **path_noise** = mean absolute deviation of bar closes from linear interpolation of start→end, in ATR units |

**Signed policy (primary expectancy) — run on both H1 and M15:**

- On confirmation of swing k at bar t, expected next structural direction = `−direction_k`.
- Enter that side at open of t+1 (if flat or reverse).
- Same §4 capture geometry as SMA (ATR and bars native to that clock).

**Next-move magnitude and/or volatility forecast — mandatory characterisation (both clocks):**

- AR(1) **and** ridge on feature vector of swing k → predict next swing’s **magnitude bps** and
  **path_noise** (volatility proxy) — both targets, both models.
- Report IC/MAE per clock; does **not** replace expectancy as the direction headline, but **must
  be computed and tabled** (not optional).

**Known weaknesses (disclosed):** fake confirmations; missed early move portion — expectancy
must absorb that lag cost.

**AMENDMENT-A2 (2026-07-23):** M15 clock mandatory; SMA50 mandatory (not sensitivity-only);
ZZ mag/vol forecast mandatory on both clocks — DIRECTION: **NEUTRAL** (pre-execution completeness).

---

## §4 Capture geometry (TF — frozen, both arms)

Classic: **cut losers quickly; let winners run.**

| Rule | Freeze |
|---|---|
| Entry | Next 1h **RealOpen** after signal/confirmation bar |
| Initial stop | Adverse excursion from entry open ≥ **1.5 × ATR(14)[entry−1]** → exit next bar open after stop touch on high/low (conservative: if bar trades through stop, exit that bar’s open if open already beyond stop, else next open) |
| Winner trail | Once favorable open-to-open excursion ≥ **1.0 × ATR**, trail stop to **entry + 0.5×ATR × side** then ratchet by high-water mark − **2.0×ATR** (long) / + 2.0×ATR (short) |
| Opposite signal | SMA: reverse on signal flip (exit+enter). ZZ: reverse on next opposite confirmation |
| Time cap | **H1:** max **48** bars (~48h). **M15:** max **192** bars (same ~48h wall-clock). Exit at open of bar after cap |
| One position | Max 1 per symbol; ignore signals while open except stop/time/opposite rules above |

**Partial cost on each episode:**

- Fee RT = 11.0 bps taker (Bybit).  
- Funding = 1.0 bps × discrete stamps crossed in `(entry, exit]` (`count_bybit_funding_stamps`).  
- Allowance = **2.0 bps** governing (report 0/2/5 sensitivity).  
- `partial_net_bps = gross_signed_oo_bps − fee − funding − allowance`.  
- Spread not charged.

```
UNIT-PIN:
  gross_signed_oo_bps = direction * (exit_open/entry_open − 1) * 1e4
  ATR object: 1h Wilder ATR(14)[t−1] in price; stops in price space from that ATR
  expectancy unit: mean partial_net_bps per episode (bps of notional)
```

---

## §5 Expectancy decomposition (primary scoring — not win-rate)

For each episode compute `partial_net_bps`. Define:

- **Right** iff `sign(gross_signed_oo_bps) == +1` (position made money before costs)  
  — use **gross** sign for right/wrong so costs do not redefine correctness of direction.
- **Wrong** otherwise (including flat zero gross).

| Statistic | Definition |
|---|---|
| `p_right` | fraction right |
| `avail_when_right` | mean `gross_signed_oo_bps` on right episodes |
| `damage_when_wrong` | mean `gross_signed_oo_bps` on wrong episodes (typically ≤ 0) |
| `expectancy_gross` | `p_right * avail_when_right + (1−p_right) * damage_when_wrong` ≡ mean gross |
| `expectancy_partial` | mean `partial_net_bps` (**headline**) |
| `win_rate` | **disclosure only** — never primary band driver |

Report all per symbol × arm × period × angle × **clock**; pooled disclosure-only.

---

## §6 Controls

```
CONTROL DIRECTION-DERANGEMENT:
  question answered: is expectancy an artifact of path marginals without signal timing?
  population: derange entry sides within (symbol × DESIGN calendar-third); paths fixed
  DISJOINT: zero fixed points
  bite/MDE: plant +20 bps expectancy must be detected as extreme vs null
  non-vacuity: moves signed sufficient statistic
  expected if H true: live expectancy > null p95; if false: inside null
  disclosure: collapse = null_median / live; seeds 31000..31199 (≥200; prefer 2000 if feasible)
  destroy form: DERANGEMENT
```

```
CONTROL MATCHED-RANDOM-ENTRY:
  question answered: does signal timing beat equal-side random entries with same occupancy?
  population: non-overlapping random 1h entries, same side distribution per symbol-third,
              same mean hold cap; ≥200 seeds 41000+
  DISJOINT: exclude live entry timestamps ±1h
  bite/MDE: +20 bps plant
  non-vacuity: changes entry times
  disclosure: live percentile vs seed expectancy distribution; collapse fraction
```

```
CONTROL SMA-BENCHMARK:
  question answered: does D-ZZ improve on D-SMA14/25?
  population: D-SMA14 and D-SMA25 expectancy on identical cost/geometry
  disclosure: Δ expectancy (ZZ − SMA) with CI; not a hard gate
```

```
TRIPWIRE: PATH-FUTURE-DESTROY
  metric: expectancy_partial on D-SMA14
  must collapse: derange exit marks / future path within symbol-third (pair episodes to foreign
    future paths); synthetic +30 bps plant must fall into null envelope
  vacuity check: destroys path pairing for signed P&L
  derangement=YES
  class: future_destroy (HARD validity)
```

---

## §7 Inference, bands, power

### 7.1 Inference

- Date-block bootstrap on entry dates (block 1/3/7); seeds 101/211/307/401/503; 10k resamples.
- Per-symbol primary; leave-one-symbol-out disclosure.
- DESIGN thirds stability: expectancy sign in ≥2/3 thirds for SUPPORTED label eligibility.

### 7.2 Bands (per symbol × arm; labels only)

```
BANDS (expectancy_partial bps):
  SUPPORTED:      mean ≥ +5 bps and date-block CI low > 0
  WASH:           |mean| < 5 bps
  CONTRADICTED:   mean ≤ −5 bps and CI high < 0
  UNPOWERED:      n_episodes < 80 or MDE > 10 bps or dates < 30
COST FLOOR (informative): fee+funding+allowance ≈ 11 + ~0.5 + 2 ≈ 13.5 bps RT;
  if avail_when_right < 13.5 while p_right≤0.55, note “damage/availability cannot clear partial
  costs even when right” — characterisation, not tradability.
```

### 7.3 Operator recommendation inputs (informative)

Recommend direction product **adequate for combination consideration** if:

1. At least one arm is SUPPORTED on **≥8 of 25** symbols (or ≥30% of powered symbols), **or**
   pooled (disclosure) CI low > 0 with ≥50% of powered symbols positive mean; **and**
2. Derangement collapse shows live above null; **and**
3. Decomposition shows `avail_when_right` materially > `|damage_when_wrong|` weighted by
   frequencies (i.e. positive expectancy not a single tail day — drop top date sensitivity).

Else recommend **weak/negative direction** for signed combination; reflection C may still
authorise direction-agnostic path if SPDR-012 vol PASS and ZZ magnitude/vol forecast useful.

### 7.4 Power

```
POWER:
  expected DESIGN 1h bars/symbol ~ 2.5*365*24 ≈ 20k; episodes depend on signal rate
  SMA14: rough episode count ~ 200–600/symbol (flip rate); if n<80 → UNPOWERED
  MDE ~ 2.8 * σ / sqrt(n_dates); predeclare UNPOWERED when dates < 30
```

---

## §8 Integrity checklist

1. TRAIN-only fence; max exit < train_end; no holdout.  
2. Entry uses open of bar after signal bar; features ≤ signal bar.  
3. ATR stops use ATR[t−1] only.  
4. Derangement fixed points = 0.  
5. Win-rate never used as PASS criterion in code paths that emit recommendations.  
6. `results/integrity_selfcheck.json` PASS.

---

## §9 Golden traces

```
GOLDEN-TRACE:
  G1 BTCUSDT D-SMA14: first signal flip after 2022-09-14 — hand SMA14 from 1h closes;
     entry = next hour open; confirm side.
  G2 ETHUSDT stop: synthetic path — if low breaches entry − 1.5*ATR, exit rule matches §4.
  G3 SOLUSDT D-ZZ: one confirmed swing — magnitude/angle/path_noise recomputed from OHLC path
     vs linear bridge; match to 1e-6 rel.
```

---

## §10 Deliverables

| Artifact | Content |
|---|---|
| `screen_code/` | SMA, ZigZag, TF geometry, costs, controls |
| `results/episodes.parquet` | one row per episode with gross/partial, right flag, arm ids |
| `results/expectancy_by_cell.parquet` | decomposition + CIs |
| `results/zz_features.parquet` | swing features + next magnitude/vol targets |
| `screen.md` / `analysis.md` | neutral + full expectancy interrogation |

---

## §11 Hard vs informative

```
HARD: fence, causality, integrity self-check, engine parity, universe pin.
      (tripwire collapse demoted to INFORMATIVE — AMENDMENT-T1 below.)
INFORMATIVE: expectancy, decomposition, bands, SMA benchmark Δ, future-destroy tripwire,
  combination readiness recommendation (operator + reflection C decide).
```

**No SPDR-014 combination object is frozen here.**

---

## §12 Amendments (operator-signed 2026-07-23)

**AMENDMENT-T1 (DEV-1) — future-destroy tripwire → informative.** §6 `PATH-FUTURE-DESTROY` and
§11 `tripwire collapse` are demoted from HARD gate to an **informative report layer** (no PASS/FAIL
effect on integrity). Reason: an outcome-side path-destroy on a **mean episode-P&L direction
object** cannot separate a look-ahead leak from a genuine **causal** timing association — a causal
trend rule that avoids the worst random paths reads as "surviving" the destroy even when its
expectancy is negative (observed: SOL D-SMA14 H1 CONFIRM live −2.23 bps vs destroyed-null p95
−3.20; all 12 D-SMA14 live values negative → no positive surviving edge). Same class SPDR-012
resolved (its AMENDMENT-T1/DEV-1). **Applicability residual kept HARD:** no cell that CLAIMS a
positive edge (`live>0`) may survive above the destroyed-null p95. Causality for SPDR-013 rests on
construction asserts (entry strictly after the signal bar; ATR[t−1]; TRAIN fence), engine parity
(sequential==batch, `max_rel 0.0`), and the predictor-side controls. Operator sign-off RECORDED
2026-07-23. Direction: LOOSER.

**AMENDMENT-A3 — exit-mode decomposition.** §3/§4's single combined capture geometry is the
`combined` arm; each termination rule is additionally isolated as its own arm so the exit
contribution is diagnosable (exploratory screen): every direction signal (6 D-SMA cells + D-ZZ) is
run under `{combined, stop, trail, time, signalflip}` on both clocks and both bands. **D-ZZ
`signalflip` is the full structural-leg arm** (hold open-after-confirm → open-after-next-confirm,
no stop/trail/time). The frozen §4 `combined` stack is unchanged. Operator-directed; sign-off
RECORDED 2026-07-23. Direction: NEUTRAL (pre-outcome completeness).

**AMENDMENT-E1 — median disclosure.** §5 reports **median alongside mean** for
`avail_when_right`, `damage_when_wrong`, `expectancy_gross`, `expectancy_partial` (fat-tail
visibility). Headline band driver stays mean `expectancy_partial` (§7.2). Right/wrong remains the
trade **gross-P&L** split (§5); ZZ magnitude/path_noise features remain forecasting-only and are
never the avail/damage object. Operator-directed; sign-off RECORDED 2026-07-23. Direction: NEUTRAL.
