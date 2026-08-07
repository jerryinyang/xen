# SPDR-018B — Screen summary (neutral quantification)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5` — the 017 residue on a second universe
- **Universe:** cTrader — `EURUSD`, `XAUUSD`, `USTEC` (INFR-021 fence)
- **Lane:** SPDR · TRAIN-only · 0 counted TEST reads · no family action · no XENA
- **Design:** `design.md`, operator-approved 2026-07-25. **No amendments.**
- **Relationship to SPDR-018:** SPDR-018 is COMPLETE and FROZEN and was **not modified**.
- **Status:** SCREEN COMPLETE — **no disposition taken here**
- **CORRECTED 2026-07-25** after the fresh-context analyst pass. See §9.

> Subordinate to `analysis.md`. Quantifies; does not adjudicate.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  cost_scope: PARTIAL_FEES_FUNDING_ONLY — BORROWED and VOL-SCALED (design §3, §3.1)
  implication: every net figure understates true cost and is NOT a cTrader cost measurement
  prohibited_claims: fully-net, cost-complete, tradable, deployable, "this is the cTrader cost"
```

---

## 1. What ran

All four arms, rebuilt from the parents' own modules against cTrader bars (no parent panel exists
for this universe). **7,578 cells.**

| Arm | Cells | Parent entry point driven |
|---|---|---|
| A | 675 | `SPDR-012 pipeline.prepare_cell` |
| B | 630 | `SPDR-013 run_screen.prepare_clock` + `capture.simulate_signal`, **all 5 exit modes** |
| C | 5,526 | `SPDR-014 prepare.prepare_symbol` + `engine.run_cell` |
| D | 747 | `SPDR-015 features/hmm/transitions` |

Residue items with cells: `A1` 36 · `A2` 72 · `A3` 432 · `A4` 108 · `A5` 27 · `B1` 252 · `B2` 126 ·
`B4` 18 · `B5` 315 · `C1` 1,497 · `C2` 345 · `C3` 2,237 · `C4` 174 · `C5` 1,215 · `C6` 58 ·
`D1` 216 · `D2` 36 · `D5` 81 · `D6` 108 · `D7` 9 · `D8` 249.

**Not run, and reported as such rather than as absent:**

| Item | Why |
|---|---|
| `D3`, `D4` (T-GT-MED10 / MED5) | arm D's 2b leg reads SPDR-015's emitted crypto ZigZag panel; a cTrader equivalent was not built |
| `C7` (DESIGN→CONFIRM sign flip), `C8` (rate lean), `C9` (`DA-STRADDLE`) | not implemented in the 018B arm-C runner |
| `B3` (positive-mean cells) | defined by reference to SPDR-013's published crypto table; no cTrader analogue exists |

**Unit pin, measured on cTrader (never carried over from crypto):** pooled σ̂ **13.03 bps**,
3/3 symbols. Crypto's measured σ̂ is **73.00 bps** — a **5.6×** difference, which is why the cost
is scaled (§2).

---

## 2. Cost — borrowed and vol-scaled (design §3.1)

```
ratio = sigma_ctrader / sigma_crypto = 13.034 / 73.001 = 0.17855   (COMPUTED AT RUN)
cost floor: 13.5 bps (crypto)  ->  2.410 bps (cTrader, vol-scaled)
```

Both legs are emitted on every cell — `c_net_bps` (vol-scaled, headline) and
`c_net_unscaled_bps` (unscaled borrowed, companion). **Gross remains primary.**

```
COST-STATUS: DOUBLY SYNTHETIC — BORROWED and RESCALED. Not any instrument's real cost.
  Supports exactly one claim: cross-universe comparability in volatility units.
```

**Consequence that must travel with any net figure below:** 12.9% of powered cTrader cells sit
above their net break-even against 0.0% on crypto. That difference is produced by the cost floor
moving from 13.5 to 2.41 bps. It is a property of the cost model, **not** a measured edge.
**Analyst confirmation:** recomputed at the UNSCALED 13.5 bps floor, **1 of 2,388** powered cells
clears net — reproducing crypto's 0.0%.

**CORRECTION (analyst): the scaling itself is wrong by roughly 2×.** It uses the ratio of H1 *bar*
volatility (0.1786); the ratio of realised *trade* payoffs is **0.32–0.48**. A trade-scale-matched
deflator puts the net-clearing figure at **1.6–3.5%**, not 12.9%. The vol-scaled floor should be
read as a lower bound on the true like-for-like floor.

---

## 3. The `(p, W, L)` picture — 2,388 powered signed cells of 6,156

| Term | cTrader | crypto (SPDR-018) |
|---|---|---|
| `p` | **0.4922** | 0.3887 |
| `p_be` (gross) | **0.4917** | 0.4025 |
| `p_be_net` | 0.5265 | 0.4992 |
| `W/L` | **1.034** | 1.484 |
| gross mean | **−0.08 bps** | −1.18 bps |
| net mean | −2.62 bps | −15.16 bps |
| clears gross break-even | 47.5% | 32.5% |
| clears net break-even | 12.9% | 0.0% |

**The zero-line result replicates, and more tightly.** `p` sits **0.0005** from its own gross
break-even and the gross mean is **−0.08 bps** — indistinguishable from zero on an independent
asset class, its own fence and its own band split.

**The term structure differs.** Both `p` and `W/L` sit much closer to the symmetric point here
(0.492 / 1.03) than on crypto (0.389 / 1.48).

**On the `W/L` mirror — stated carefully.** Regressing log `W/L` on the driftless mirror
`(1−p)/p` gives **R² 0.311** here against 0.967 on crypto, with a mean log residual of
**−0.0024** (crypto: −0.036). The cells sit *on* the zero line, but `W/L` barely varies
(clustered at ~1.03), so there is little dynamic range for the regression to fit. **The low R² is
a mechanical consequence of that narrow spread, not evidence that the mirror fails.**

**Analyst adjudication:** conclusion upheld, reason incomplete. The dominant term is a **3.3×
larger noise floor in `log R`**, not only the narrow range. Within `signalflip` alone the mirror is
recovered at **R² 0.932, slope 0.980**, and the arm-B movability test — possible here because all
five exit modes ran — shows `W/L` moving **36×** while `p` moves inversely by the offsetting
amount and the gross mean does not improve. ("mean log residual −0.0024" is the mean of `log R`,
not a regression residual, which is 0 by construction.)

Band labels (mean): 2,424 WASH · 2,407 NOT_RESOLVABLE · 939 UNPOWERED · 301 CONTRADICTED ·
85 SUPPORTED.

---

## 4. `C2` shock-conditioned MOMO — the replication target

This item is why SPDR-018B exists: it was SPDR-018's only live thread and had **zero external
replication**.

**Raw split** (arm C, cTrader): `shock_flag = True` gross **−3.43 bps** (171 cells, 30,319 rows,
38 powered) against `False` gross **+0.33 bps** (174 cells, 203,250 rows, 101 powered).

**M-3 magnitude-matched comparator** — the control that separates "the volatility state" from
"this was a big bar", 2,000 seeds, decile-stratified, comparator supply present in every decile:

| Read | cTrader | crypto (SPDR-018) |
|---|---|---|
| `shock_flag`, primary cell | live **−9.38 bps**, percentile **0.043** (n_live 290) | live +22.6 bps, percentile 0.95 (n 505) |
| `shock_flag`, full arm-C panel | live **−4.21 bps**, percentile **0.000** (n_live 30,319) | — |
| `mag_high`, primary cell | live −3.40 bps, percentile 0.274 | percentile 0.46 |

On the full panel the plant curve reads 1.000 at every plant level {5, 10, 20, 40} bps, so the
control has ample bite at this `n` — the read is not a power artifact.

**CORRECTION (analyst).** The `−4.21 bps / 30,319 rows` figure above is a **net** number, not
gross, and is computed over ALL shock bars — including the ~87% that carry no momentum policy. It
is therefore **not the shock-MOMO object**. The analyst rebuilt the correct `P-MOMO` object:
**−3.99 bps below its comparator, one-sided p = 0.0045, n_live = 1,594**, with `P-MR` at +1.30
(pct 0.81). The conclusion survives; the quoted number does not mean what it says. The raw
`−3.43 / +0.33` split likewise collapses to **−0.32 / +0.07 with straddling CIs** on powered
cells only.

**Quantified, not adjudicated:** on crypto the shock state sat *above* its magnitude-matched
comparator (percentile 0.95); on cTrader it sits *below* it (percentile 0.0045 on the correct
1,594-trade object).
The direction is opposite and the cTrader read is well powered. Whether that is a genuine
cross-asset-class reversal, a mechanism absent outside crypto, or a difference in what "shock"
selects on a 24/5 instrument is the analyst's question.

**Side-derangement, arm C primary cell:** live −2.63 bps at percentile 0.023, 0 fixed points,
n 2,602 — the signed live arm sits below its own side-deranged null.

---

## 5. Integrity — all HARD checks held

`cTrader TRAIN fence` · `cTrader holdout (2024-12-13 never queried)` ·
`cTrader fence sha256 == 4cdc7b01…` · `identity reconstruction < 0.01 bps` ·
`M-1 block MDE drives every band label` · `no pass field / no at_or_above_pXX` ·
`derangement fixed points == 0` · **`CROSS-UNIVERSE OBJECT IDENTITY`**.

**The identity guard did real work and is worth recording.** Design §5 substitutes it for parent
parity, which cannot exist on this universe. It runs the retargeted code path over a **Bybit**
symbol and requires SPDR-018's emitted cells to be reproduced exactly.

It **failed twice before passing**, both times on genuine defects in this experiment's own code:

1. An arm-B reimplementation set the ZigZag start to `ATR_PERIOD+1`; SPDR-013 uses the first
   index with a finite ATR.
2. More seriously, SPDR-013 constructs **each band separately** — every bar up to that band's end,
   with the signal zeroed before the band start, preserving warm-up history while confining
   trading to the band. The first implementation ran once over the full span and assigned bands by
   exit timestamp. Different episode set: max cell-count difference **61**, max gross difference
   **14,217 bps**.

Arm B now drives SPDR-013's own `prepare_clock` and replicates its band loop.
**Final guard result: 0 cells differ in count, max gross difference 1.1e-13.**

Without this check, 018B would have reported an arm-B "non-replication" that was an artifact of
this experiment's code — on a 3-symbol universe where a null is the expected outcome, and
therefore easy to accept as real.

---

## 6. Power — predeclared, and it bound

3 instruments against 25. **2,407 cells are `NOT_RESOLVABLE`.** Per design §7 and B-5, an
unpowered non-replication says nothing; only powered cTrader cells are informative about the
crypto result. The `C2` reversal in §4 is reported precisely because it **is** powered.

---

## 7. Deviations

**CORRECTED — the original claim of "none" was inaccurate.**

The design inherits SPDR-018 §7's **three** uniform controls and **three** tripwires. The original
emission ran only side-derangement and the M-3 comparator: **the ambient-base control and all
three tripwires were absent**, and the self-check carried 8 entries where SPDR-018 carried 18 —
while §7 claimed a clean sheet. **This is the same class of failure SPDR-018 made with
TRIPWIRE-2**: a declared check silently not running underneath a "deviations: none" statement.

All four were subsequently built and run (`screen_code/add_missing_controls.py`); the self-check
now carries **11 HARD checks, 0 failed**, and TRIPWIRE-2 separates the legal variant (0.49 bps)
from the leaky twin (203.65 bps).

Other process items:

- The identity guard failures in §5 — caught, fixed, re-run, and the guard now holds.
- **A selection artifact the screen did not catch (analyst §12).** "At parent target precision" is
  a **dispersion** filter, and on skewed P&L it is not sign-neutral: it retains cells whose loss
  tail has not yet fired. It produces ten arm-B trailing-stop cells with gross means +7 to +23 bps
  clearing every floor, drawn from a population of 116 excluded cells averaging **−27.6 bps**.
  **Those ten must not be read as an edge.**
- **The precision target is not portable across universes.** Carrying SPDR-013/014's absolute
  10 bps rule from a σ = 73 bps universe into a σ = 13 bps universe silently loosened it ~5.6×,
  inflating every powered count here and depressing the `W/L` mirror R². Power counts in §3 and §6
  are therefore **not** comparable to SPDR-018's.
- Arm C's controls were skipped by a resumed run (the resume path left the panel empty). They were
  rebuilt and the arm-C panel is now persisted to `results/panel_C.parquet` so it cannot be
  skipped again.

Interpretation notes `IN-B1` (objects rebuilt from parent code, guard-checked) and `IN-B2`
(borrowed cost) are in `screen_code/config18b.py`.

---

## 9. Corrections carried after the analyst pass

Seven, all from the fresh-context analyst and all applied above: the missing controls and
tripwires (§7); the `−4.21 bps` M-3 figure being net and off-object (§4); the raw shock split
collapsing on powered cells (§4); the cost scaling being ~2× off and the 12.9% figure (§2); the
`W/L` reason and the "residual" mislabel (§3); the `trail` selection artifact (§7); and the
non-portability of the precision target (§7).

The analyst's `analysis.md` is BINDING and supersedes this document wherever they differ.

---

## 8. Artifacts

`results/arm_A.parquet` · `arm_B.parquet` · `arm_C.parquet` · `arm_D.parquet` ·
`metrics_by_cell.parquet` (7,578 cells) · `panel_C.parquet` · `controls.json` ·
`unit_pin.json` · `integrity_selfcheck.json` · `run_summary.json`.

**Next:** fresh-context `data-analyst` → `analysis.md` (binding), then the operator disposition.
No tradability, deployability, family-status or graduation claim is made or implied.
