# SPDR-005 — Design (CF-EPSOSC-001 TRAIN-only availability screen)

**Lane:** SPDR (speed-run) — `docs/references/spdr-lane.md` · pack
`docs/references/spdr-pack-epsosc-001.md` · family D0
`docs/signal-registry/candidate-families/cf-epsosc-001.md`.
**NOT** a Nautilus price-primary experiment: TRAIN-only, **vectorised Python**, disposition-only.
**No** QA subagent (SPDR stage-2 = code-asserted self-check). **No** estimand gate, **no**
counted TEST read, **no** tradability/deployability claim.
**Route if promote:** full **XENA** (XENA-EPSOSC-001) — EXP lane not used (D0 / Q freeze).
**Checkpoint:** `docs/experiments-docs/checkpoints/2026-07-16-013-chapter04-open-htfcap-epsosc-cal/`.
**Designed:** 2026-07-16 · **Status:** DESIGN COMPLETE — screen execution is a separate go.

---

## 0. Registration precondition (HARD — before any screen code)

| Item | State |
|---|---|
| Family | **CF-EPSOSC-001 REGISTERED** 2026-07-16 (checkpoint-013 D2, operator-signed) |
| Multiplicity row | `docs/signal-registry/multiplicity-registry.md` § Chapter 04 · CF-EPSOSC-001 |
| Candidate card | `docs/signal-registry/candidate-families/cf-epsosc-001.md` status `REGISTERED` |
| Slots / reads | **0 slots; 0 counted TEST reads**; SPDR screen is **uncounted** |
| XENA gate | blocked until INFR-014 fresh CAL pin |
| This design | freezes episode objects + grid + selection; does not re-register or change family status |

Registration-before-screening satisfied. Screen code must refuse to run if the family card
status is not `REGISTERED` or the multiplicity row is missing (self-check §11).

---

## 1. Question + mechanism

**Falsifiable question (pack §3).** On TRAIN Bybit (rule-selected 10), do one or more
**coherent clusters** of **non-grid** episode-harvest variants (rolling-anchor stretch / vol-arm
fade × clear × side × k) show **lift over matched random-timing or shuffled-episode controls**
in **bps per episode**, under causal `t−1` rules?

```
MECHANISM: Prices may oscillate enough that a harvest structure earns gross bps by fading a
confirmed stretch (or vol-armed stretch) back toward a rolling anchor and clearing *within the
episode* — return-to-anchor / time-stop / hybrid — without a hard inventory freeze. The
P&L-bearing object is the **episode** (entry → within-episode clear), not a fixed-horizon
per-event return and not a banded rebalance grid (P-12 dead object banned). FX VR<1 is a soft
hope only; must reappear as a parallel diagnostic or the process story is weak (not sole gate).
DERIVED: estimand = mean gross bps/episode + lift vs matched random-timing / episode-shuffle;
         null = cadence-matched random entry battery (≥25 seeds) + derangement episode-time
         shuffle (L-28) + optional grid-like twin (expected NOT to promote);
         horizon = episode duration until clear (endogenous) or time-stop cap;
         test = episode-level block bootstrap + cluster K≥3 promote rule.
```

---

## 2. P-12 distinctness + P-10 / L-27 entry-object check (binding)

### 2.1 P-12 — not a CF-VOLHARV / banded-grid re-run

| | Closed vehicle (P-12 / CF-VOLHARV-001 / EXP-020) | This vehicle (CF-EPSOSC-001 / SPDR-005) |
|---|---|---|
| Dead object | **Banded rebalance + hard inventory cap** symmetric grid | **Banned out of family** (hard exclusion) |
| Failure mode | Cadence collapse 5–28% of implied; cap-lock; censored inventory erases harvest; premium ~100× below design | Structure search for **within-episode clear**, rolling anchor, **no hard inventory cap** |
| Re-open clause (P-12) | Only a **within-episode-clearing** structure on an **unseen band**, **own D0** | **NEW family** CF-EPSOSC-001, new stack (Bybit/Nautilus), own D0 — not re-parameterisation |
| Promote identity | Grid “worked” as cadence theater | Promote cluster must be **structure-identified non-grid** (pack §6.3) |

**Why this is the P-12 escape, not a retune.**
1. **New D0 / new family / new universe** — Bybit USDT-perp, not FX MR block re-grid.
2. **Object class:** stretch-from-**rolling-anchor** fade and vol-expansion-arm fade with
   **return-to-anchor / time-stop / hybrid clears** — harvest ends when the episode clears,
   not when a monthly/hard inventory cap freezes the book.
3. **Hard ban** on identical dead grid (banded rebalance + hard cap symmetric two-sided grid).
4. Optional **grid-like twin** (disclosure only) expected **not** to promote — if only the
   twin “works,” disposition NOT_WORTH / structure-identity fail.
5. Path diagnostics (duration, cadence, funding×length) mandatory at screen summary.

### 2.2 P-10 check — entry objects declared (no resting limits at SPDR)

| Entry object in this design | Type | P-10 status |
|---|---|---|
| Stretch confirmed-event entry | **Market at LTF bar open** on confirmed stretch event (signal ≤ t−1) | **Allowed** (confirmed-event, not limit-at-measured-level) |
| Vol-arm fade entry | **Market at LTF bar open** on confirmed arm+stretch | **Allowed** |
| Resting limit / passive MR entry | **NONE in SPDR-005 grid** | **Banned** (P-10) — not a cell |

**Declaration:** **zero** SPDR-005 cells use a resting limit, passive bid/ask, or
limit-at-anchor entry. Fill = next/open market semantics on the decision bar open after a
confirmed event (vectorised open-to-open). Passive-limit MR capture is **out of scope**; any
future limit cell requires fill-vs-prediction decomposition and is a **new design amendment**.

### 2.3 L-27 → INFR-014 battery design (forward constraint — binding handoff)

L-27: permutation-null battery is **confounded on limit-entry / non-grid-priced universes**
without a **next-open discriminating control** (re-price entries to adjacent grid open; hold
times/exits/sizing). If the battery cannot be de-confounded, it is **inadmissible**.

| Scope | Constraint |
|---|---|
| **SPDR-005** | Market-entry only → standard derangement / random-timing battery **admissible** (no limit-print confound). Still use **derangements** for any index permutation (L-28). |
| **INFR-014 (fresh XENA CAL)** | Battery design **must** predeclare: (a) if **any** candidate cell in the CAL or later XENA-EPSOSC universe uses **limit / passive entry**, then either ship a **next-open discriminating control** (L-27) **or** mark the permutation battery **inadmissible** for that universe and use an alternative null; (b) CF-EPSOSC mechanism class must not be certified solely on a limit-print passive edge (P-10 + L-27). |
| **XENA-EPSOSC-001** | Inherits (a)(b); default preferred entry remains market-on-confirmed-event unless a dedicated limit cell + decomp is operator-approved. |

This paragraph is the formal forward-note for INFR-014 design.md — copy/cite, do not re-decide.

---

## 3. Object identity + L-16 episode-native estimand (binding)

```
OBJECT-IDENTITY:
  measurement object == trading object: YES — both are the **episode**:
    open at confirmed-event market entry → path until within-episode clear
    (return-to-anchor | time-stop | hybrid). Single-name, typically single-leg one-sided fade.
  measured conditioning event == traded entry event: YES — stretch/vol-arm event is the same
    confirmed state that triggers market entry at next bar open (B-4: no limit-touch ≠ breach).
  effect-splitting windows non-overlapping: non-overlapping episodes within an arm
    (no new entry while an episode is open on that arm).
```

```
L-16 (episode-native — mandatory):
  P&L-bearing object: EPISODE (entry → clear), measured as gross open-to-open bps summed over
    the episode path (entry open → exit open), sign = fade direction.
  Primary estimand: mean bps/episode (and lift vs control) — THIS object only for promote.
  Disclosure only: bps/trade, fixed-horizon per-event MFE/MAE, per-bar carry.
  Ban: a null on a narrower per-event fixed-H estimand MUST NOT be read as family-terminal
    absence (label NO_PER_EVENT_MECHANISM at most — never family retirement from per-event alone).
```

Primary formula (screen metric — not `xen.adjudication` P&L for a verdict):

```
R_ep_bps = Direction · (RealOpen[t_exit] − RealOpen[t_entry]) / RealOpen[t_entry] · 1e4
```

- `Direction` = fade side (+1 short stretch-up / −1 long stretch-down for classic fade).
- Exit = first clear: price returns through rolling anchor (confirmed ≤ t−1) **or** time-stop
  bar, per clear policy.
- Report **bps/trade** as disclosure when multi-leg appears (should be rare on one-sided SPDR).
- **No local adjudication accounting** for disposition (L-18); evaluation toolbox / declared
  screen metrics only.

---

## 4. L-21 unit pin AT THE SCREEN (binding)

```
UNIT-PIN (SPDR-005):
  primary unit:     gross open-to-open bps/episode  (formula §3) — NO ATR divisor on promote facet
  disclosure ATR:   domain LTF ATR(14)[t−1] on the bar series of the episode domain
                    (name indicator + file:line at implement)
  measured value:   TRAIN-median ATR in bps of price per (instrument × domain)
                    = median(ATR(14)[t−1] / RealOpen[t] · 1e4)
                    → results/unit_pin.json at screen start (never pre-assert numbers)
  resulting effect: ATR-normalised disclosure × measured_ATR_bps → bps (promote uses raw bps only)
  money-unit floor: per instrument / median episode length:
                    xen.evaluation.bybit_round_trip_cost_bps(
                      symbol, entry_px,
                      liquidity="taker",   # 2×5.5 = 11 bps fee RT
                      spread_bps=<TRAIN-median T1 RT spread or GAP+disclosed assumption>,
                      funding_bps_per_8h=<disclosed; scale by median episode hours>,
                      hold_hours=<median episode duration hours>
                    ).total_bps
                    + capture-dilution note if path clear is one-sided incomplete
  floor rule:       if best cluster median gross bps/episode ≤ floor → disposition MUST state
                    sub-floor; graduate only as characterisation/apparatus if operator still wants
  funding:          disclose episode-length × funding sensitivity at SPDR (Q5 / pack §5);
                    bind at XENA only
```

```
SPREAD-SCALE-ROUTING (disclosure at SPDR):
  estimated_rt_spread_bps: <measured TRAIN>
  gross_edge_bps: <cluster median bps/episode>
  t1_undecidable: YES if |gross| < 3× rt_spread
  SPDR disposition is never a T1 tradability band
```

---

## 5. Scope + frozen thin grid

### 5.1 Instrument selection (shared with SPDR-004 / checkpoint-013 §5)

```
INSTRUMENT-SELECTION (online, D5 — same rule as CF-HTFCAP-001):
  n: 10
  rule: highest trailing 24h volume (sum 1m catalog volume, window ends ≤ t−1)
  rebalance frequency: every 1 UTC calendar day at 00:00 UTC
  causality: volume data ≤ t−1 only — code-asserted
  tie-break: lexicographic InstrumentId
  SPDR pool (D3): ADMITTED + not delisted at rebalance (currently-most-liquid justification)
  artifacts: results/membership.parquet
```

### 5.2 Data + fence

| Item | Value |
|---|---|
| Catalog | `data/catalog/` |
| Fence | `xen.nautilus.catalog_fence` · PINNED INFR-011 A6 manifest |
| TRAIN | `[2021-06-29, 2023-12-18)` — `band="TRAIN"` only |
| TEST / HOLDOUT | **never** (holdout_start 2025-01-08 sealed) |
| Bars | 1m → domain LTF via `xen.bar_aggregator` |
| Engine | vectorised Python screen |

### 5.3 Episode objects (two — Q-B1 frozen)

**Object A — Stretch-from-rolling-anchor fade (`STRETCH`)**  
- Anchor: rolling **median** of `RealClose` over window `W` bars, lagged (`anchor[t]` uses data ≤ t−1).  
- Stretch event (confirmed): `|RealClose[t−1] − anchor[t−1]| / ATR(14)[t−1] ≥ k`.  
- Side (one-sided): fade **against** stretch (stretch up → short; stretch down → long).  
- Entry: **market** at open of bar `t` after confirmed event.  
- Clear policies (axis):  
  - `RET_ANCHOR` — exit when `|RealClose[t−1] − anchor[t−1]|` re-crosses below 0.25·k·ATR or price crosses anchor  
  - `TIME` — exit at `t_entry + H` (H frozen per domain below)  
  - `HYBRID` — RET_ANCHOR else TIME  

**Object B — Vol-expansion arm → fade (`VOLARM`)**  
- Arm when `ATR(14)[t−1] / ATR(14×4 slow)[t−1] ≥ vol_ratio` **and** stretch event as in A.  
- Same fade direction, market entry, clear policies as A.  
- Isolates “only fade when vol expanding” vs pure stretch.

### 5.4 Grid (frozen)

| Axis | Levels | n |
|---|---|---|
| Symbols | online top-10 (§5.1) | 10 |
| Domain (LTF) | **5m**, **15m**, **1h** | 3 |
| Episode object | **STRETCH**, **VOLARM** | 2 |
| Anchor window W (LTF bars) | **48, 96, 192** | 3 |
| Threshold k | **2.0, 2.5, 3.0** (3 of 2–4 coarse pack span) | 3 |
| Clear | **RET_ANCHOR**, **TIME**, **HYBRID** | 3 |
| Side | **LONG_ONLY**, **SHORT_ONLY** (required); **TWO_SIDED** optional disclosure ≤25% cells | 2 binding (+ optional) |
| VOLARM vol_ratio (VOLARM only) | **1.25** fixed at SPDR (single level — keep thin) | 1 |

**TIME-stop H (LTF bars):** `H = W` (one anchor window). Episode must end ≤ TRAIN end.

**Censoring at train_end (AMENDMENT-1):** pure `RET_ANCHOR` episodes have no time cap and may
be open at `train_end_utc`. Policy: mark such episodes **CENSORED**, exclude them from mean
bps/episode (primary estimand), and **disclose the censored fraction per cell**; a cell with
censored fraction > 20% is flagged in diagnostics (clear policy failing to clear is itself
evidence about the structure). Silent drop is banned — it biases toward fast-clearing wins.

**Binding treatment cells (one-sided):**  
10 × 3 × 2 × 3 × 3 × 3 × 2 = **3240** — large but thin vs XENA; disclose multiplicity.
**Promote facets run on a predeclared primary slice to keep K-read tractable:**

```
PRIMARY PROMOTE SLICE (binding for K-rule; full grid still emitted):
  domains: {15m, 1h}          # 5m = power/disclosure dense; not required for K
  W: {96, 192}
  k: {2.5, 3.0}
  clear: {RET_ANCHOR, HYBRID} # TIME alone = disclosure (path-endogenous clear is the thesis)
  side: {LONG_ONLY, SHORT_ONLY}
  objects: {STRETCH, VOLARM}
→ 10 × 2 × 2 × 2 × 2 × 2 × 2 = 640 primary cells
```

Full grid remains in `results/` for analyst facets; **WORTH_EXPLORING uses primary slice only**
for cluster K (freeze prevents 3240-cell lottery).

**Hard exclusions:** banded rebalance + hard inventory cap grid; passive-limit entry; forming-bar
features; TEST/holdout; two-sided cells >25% of emitted promote-facing cells.

**Optional negative control (disclosure):** one **GRID_TWIN** arm — symmetric two-sided banded
rebalance-style book with hard max-inventory cap (P-12 shape), same instruments — expected
**not** to form a promote cluster. If GRID_TWIN is the only positive, structure-identity fails.

### 5.5 VR / oscillation parallel facet (Q-B3 — not sole hard-gate)

```
VR-FACET (parallel, always report):
  per (instrument × domain): variance-ratio / simple oscillation diagnostic on TRAIN
    log-returns at lag ∈ {2, 4, 8, 16} LTF bars (implementation: xen or declared screen helper).
  coupling to promote (pack §6.4, frozen here):
    if VR facet is flat (no lag with VR systematically < 1 on ≥ half of symbols in primary domains)
    THEN require stronger cluster evidence: K≥3 AND median lift ci_low > MDE with collapse under
    episode-shuffle Control C; else prefer INCONCLUSIVE over thin WORTH_EXPLORING.
  VR flat alone does NOT force NOT_WORTH (diagnostic, not sole gate).
```

---

## 6. Controls (validity proofs)

```
CONTROL A — matched random-timing battery (L-19):
  question: is episode bps above cadence-matched random entries with the same clear policy?
  population: ≥25 seeds {2000..2024}; random entry times on same domain calendar; same
    Direction policy / clear rules / non-overlap; seeds do not use stretch labels for timing.
  bite/MDE: battery percentile of treatment mean bps/episode + CI on lift.
  non-vacuity: random timing destroys stretch alignment → moves episode mean (B-6).
  expected if H true: treatment rank high vs battery; if false: ~median.
  destroy form: N/A for pure random times; if schedule permutation used → DERANGEMENT (L-28).

CONTROL B — episode-time / label shuffle (attribution):
  question: does edge need the actual stretch→clear path alignment?
  destroy: derangement-permute episode start indices or stretch event labels within symbol×domain
    (zero fixed points — L-28); re-run clear on shuffled events.
  non-vacuity: breaks event→path coupling → moves mean.
  MUST collapse promote-candidate cells; expected collapse fraction ≈ 1.
  destroy form: DERANGEMENT (L-28) required.

CONTROL C — optional GRID_TWIN (structure identity / P-12 sentinel):
  question: is any “edge” just the banned grid shape reappearing?
  population: banded symmetric two-sided rebalance + hard inventory cap (disclosure arm).
  expected: does NOT promote; if it is the sole positive cluster → NOT_WORTH (structure fail).
```

Leak / causality tripwire: confirmed-event lag (all features ≤ t−1); TRAIN fence; active
episode non-overlap. Phase-shift of stretch series by large lag (K≫ max H) as alternate destroy
if shuffle is infeasible — still derangement if permutation-based.

---

## 7. Promote rule + bands

Pack §6 · **K = 3**:

**WORTH_EXPLORING** iff **all** of:
1. **Cluster:** ≥3 cells in primary promote slice, same episode-object family (STRETCH or
   VOLARM), varying k and/or W and/or symbol/domain, positive lift vs Control A (ci_low>0 or
   high battery rank), dependence-honest.
2. **Neighbourhood:** best cell not lone positive in neighbourhood (adjacent k or W).
3. **Structure identity:** cluster is **not** GRID_TWIN / banned grid; path clears within
   episode (median duration finite; not cap-lock dominated).
4. **Substrate honesty:** VR-facet coupling (§5.5) satisfied.
5. **Money-relevant:** cluster median bps/episode reported + §4 floor disclosure.

**NOT_WORTH:** no cluster; only GRID_TWIN; pure noise.  
**INCONCLUSIVE:** underpowered / VR+structure thin / data gap — never a silent negative (B-5).

```
BANDS (per stratum — magnitudes for analyst):
  SUPPORTED_LIFT: lift vs battery ci_low>0 AND collapses under Control B
  WASH:           |lift| < MDE / CI spans 0
  CONTRADICTED:   lift ci_high < 0
  UNPOWERED:      n_episodes < max(30, dependence floor) — not a negative
POOLED: disclosure-only (L-03).
HARD: registration; TRAIN fence; t−1; market entry only; L-16 episode primary; L-28 derangement;
      per-stratum emission; unit_pin.json.
INFORMATIVE: sizes, VR facet, funding×duration, floor, GRID_TWIN.
```

---

## 8. Power + diagnostics

```
POWER:
  expected episodes: denser on 5m/k=2.0; thinner on 1h/k=3.0/W=192.
  MDE: per cell from episode-level bootstrap (block by episode or calendar block ≥ median duration).
  predeclared UNPOWERED: cells with n_episodes < 30; 1h × k=3.0 × W=192 tails on short membership.
```

**Diagnostics (pack §7, always):** one-sided vs two-sided (if any); episode duration vs funding;
cadence (episodes/year) vs capacity; clear reason mix (anchor vs time); GRID_TWIN comparison;
no fill-artifact claim (market entries only).

**Stage 5:** fresh-context `data-analyst` after `screen.md` — quantify-not-qualify (spdr-lane).
Operator disposition only after `analysis.md`.

---

## 9. Integrity checklist (code-asserted — no QA subagent)

1. **Registration** — CF-EPSOSC-001 `REGISTERED` + multiplicity row; 0 slots.  
2. **TRAIN fence** — `fenced_bar_query(..., band="TRAIN")` / `assert_within_fence`; entry+clear
   < `train_end_utc`; 0 TEST/HOLDOUT.  
3. **Causal t−1** — anchor, ATR, stretch, vol-arm all ≤ t−1; entry at bar open after confirm.  
4. **Market entry only** — assert no limit/passive fill path in screen_code.  
5. **P-12 ban** — no hard inventory cap / banded rebalance in treatment objects.  
6. **L-16** — primary table is bps/**episode**; per-event fixed-H not used for promote.  
7. **Seed battery** — ≥25 regenerable seeds for Control A.  
8. **L-28** — any permutation destroy is a derangement (0 fixed points).  
9. **Per-stratum** — full cell table to `results/`; no pooled-only headline.  
10. **L-21** — `results/unit_pin.json` from TRAIN before disposition text.  
11. **Membership** — daily selection ≤ t−1; `membership.parquet` written.  
12. **Golden trace** G1–G3 PASS.

Any FAIL blocks disposition path.

---

## 10. Golden trace

```
GOLDEN-TRACE:
  G1 (15m, STRETCH, W=96, k=2.5, RET_ANCHOR, SHORT_ONLY): pick a confirmed stretch-up event;
      verify anchor/ATR from ≤ t−1; entry open[t]; hand r_bps to clear; no forming-bar inputs.
  G2 (1h, VOLARM): arm+stretch both true at t−1; entry market; TIME clear at H=W; exit < train_end.
  G3 (membership): one 00:00 UTC rebalance top-10 matches recomputed trailing 24h volume ≤ t−1.
```

---

## 11. Ratified stack lessons + pitfall cites

| ID | Relevance to SPDR-005 |
|---|---|
| **L-16** | Episode is the P&L object; per-event cannot retire family |
| **L-18** | No local P&L accounting for verdict |
| **L-19** | Random-timing ≥25-seed battery |
| **L-20** | Block bootstrap hygiene on episode series |
| **L-21** | Unit pin + money floor at this screen |
| **L-27** | Forward to INFR-014 if any limit-entry universe (§2.3) |
| **L-28** | Derangement destroys |
| **L-29..L-31** | Cite-only (Nautilus/XENA path) |
| **P-10** | No passive-limit MR at SPDR |
| **P-12** | Dead grid banned; within-episode clear is the escape |
| **P-15** | No unit lies at screen→graduation seam |

---

## 11b. Amendment ledger (L-23)

```
AMENDMENT-1 (2026-07-16, pre-execution): RET_ANCHOR episodes open at train_end are marked
  CENSORED, excluded from mean bps/episode, censored fraction disclosed per cell (>20% flagged).
  Gap-fill — pack silent on censoring; consistent with "prefer within-episode clear".
  DIRECTION: NEUTRAL (measurement completeness; no gate/threshold change).
  running count: 0 looser / 0 tighter / 1 neutral.

AMENDMENT-2 (2026-07-17, post-exec QA run 1 Issue 1, operator-ratified): primary cell strata =
  fixed top-10 symbols by total membership-days over TRAIN (screen_code selection
  spdr005_screen.py:1080-1082), not the online daily top-10 of design §5.1. Episodes remain
  member-gated per-bar (within-cell numbers causal); the deviation is WHICH 10 symbols form the
  promote evidence base (full-TRAIN information; survivorship/liquidity-persistence lean).
  Mirrors SPDR-004 AMENDMENT-3 form.
  DIRECTION: LOOSER (hindsight universe reduction; disposition must carry the caveat).
  running count: 1 looser / 0 tighter / 1 neutral.

AMENDMENT-3 (2026-07-17, post-exec QA run 1 Issue 2, operator-ratified): Control A seed battery
  tiered — 25 seeds {2000..2024} on the 640 primary cells (K-rule binding path), 5 seeds on the
  2600 non-primary disclosure cells (spdr005_screen.py:68). Integrity item 7 detail "seeds=25"
  is unqualified and applies to primary only; non-primary battery_rank has 0.2 resolution +
  L-19 fragility exposure — disclosure facets only, never promote-bearing.
  DIRECTION: NEUTRAL for the promote path / LOOSER for disclosure facets.
  running count: 1 looser (+1 disclosure-scoped) / 0 tighter / 2 neutral.
```

## 12. Artifacts + stop

```
python/experiments/SPDR-005/
  design.md       # this file — DESIGN COMPLETE
  screen_code/    # (next go)
  results/ plots/
  screen.md
  analysis.md     # fresh-context analyst (mandatory)
```

**Stop:** design + registration complete. **Do not run screen** until operator execution go.
On WORTH_EXPLORING → XENA-EPSOSC-001 design only after INFR-014 pin (battery must honor §2.3).
