# SPDR-019 — QA / Compliance review (append-only)

## QA run 1 — 2026-07-28T14:48:16Z — mode: subagent — HEAD c52993e679a18b28015b1a0dbed80ddaf51f26f7 (clean tree)

**Target:** `python/experiments/SPDR-019/design.md` (525 lines)
**Stage:** DESIGN-STAGE review. `screen_code/` does not exist; that is the expected state and is
**not** reported as a finding. No design-to-code fidelity trace is possible or attempted.
**Question answered:** is this design complete, internally consistent and compliant enough to
authorise implementation?

**Verdict: REVISE**

Findings: **1 CRITICAL · 2 HIGH · 4 MEDIUM · 4 LOW · 2 INFO**

The design is unusually strong on the things that have previously shipped defects in this
programme — the exact-mirror target, cost isolation, the C6 phase-(b) protocol, L-52 check
counting, L-28 derangements, P-24 comparator disclosure. It fails on **power arithmetic** and on
**exit-fill specification**, and one entry parameter that the power arithmetic depends on is not
frozen. Those are implementation-blocking.

---

### 1. Mandatory declaration blocks (`quant-designer/references/design-requirements.md`)

| # | Block | Design § | Present | Substantively filled | Notes |
|---|---|---|---|---|---|
| 1 | MECHANISM / DERIVED | §1 | YES | YES | Falsifiable; cadence, horizon and P&L object named; §1's "why this is not a reused stack" paragraph directly answers the L-13 anti-pattern. Estimand/null/horizon are all mechanism-derived. **PASS** |
| 2 | OBJECT-IDENTITY (B-8/B-4/B-9) | §3 | YES | YES | All three clauses answered YES with the object named. B-4 clause correctly pins conditioning to decision-bar close `[0]`, the bar whose extreme becomes the stop. B-9 handled by one-open-episode-per-symbol + block ≥ horizon. **PASS** |
| 3 | CONTROL validity proofs | §6 | YES (4 blocks) | YES | Each carries question / population / bite-MDE / non-vacuity / expected-if-true / expected-if-false / disclosure. MIRROR-NULL declares itself **non-disjoint** and argues why B-1 does not apply to a point null — a reasoned declaration, not an omission. Derangement form declared on both permutation controls. See finding **F6** on the missing collapse-fraction line (mitigated by M-5) |
| 4 | TRIPWIRE | §6.1 | YES (2) | YES | Both HARD. Vacuity check present on TRIPWIRE-1 and correctly names `p`, `W`, `L` as the moved sufficient statistics. `if permutation-based: N/A` correctly declared (index shift, not a permutation). **PASS**. See **F2** — TRIPWIRE-2 covers entry fills only |
| 5 | BANDS | §9 | YES | PARTIAL | See finding **F5** — the four labels do not partition |
| 6 | POWER | §8 | YES | **NO** | See finding **F1** |
| 7 | GOLDEN-TRACE | §11 | YES (G1–G6) | YES | Deterministic selection rules; explicitly assigns derivation to QA, not the developer. G5 (no fitted-slope residual anywhere) is a well-designed audit-A1 tripwire. See **F3** re G1's hard-coded `deltaThreshold = 0.5` |
| 8 | HARD / INFORMATIVE split | §12 | YES | YES | 14 HARD, all blocking; INFORMATIVE list contains every effect size, percentile, band label and collapse fraction — no auto-verdict threshold anywhere. **PASS** |
| 9 | CONVERSION-PIN (L-21) | §7 | YES | YES | Divisor object 1 (Wilder ATR(20), decision clock, `[0]`, causal) and object 2 (σ̂) both named to indicator/period/timeframe/lag. **Verified:** object 2's wording matches `SPDR-018/results/unit_pin.json.divisor_object` byte-for-byte ("LTF H1 Parkinson EWMA(lambda=0.94), 60 H1-bar warm-up, causal <= t-1, in bps; horizon-scaled sigma_t*sqrt(h). Identical object to SPDR-014's Z-VOL width."). Measured value correctly deferred to a run-time emission (`results/unit_pin.json`) rather than recalled. Cost floor stated and explicitly quarantined from every comparison. **PASS** |
| 10 | SPREAD-COST-DISCLOSURE | header | YES | YES | All five required fields verbatim; `spread_rt_bps: null`; `PARTIAL_FEES_FUNDING_ONLY`; prohibited-claims list complete. **PASS** |
| 11 | Cost interpretation (ch-05) | §5 / §7 / §13 | YES | YES | Cost appears only as `DISCLOSURE_ONLY`. No proxy, no zero-fill, no `SpreadBps` route (P-20 clean). **PASS** |
| 12 | Amendment-direction ledger (L-23) | §14 | YES | PARTIAL | 0/0/0 running count is correct (no design amendment landed). See **F10** |
| 13 | Battery/eligibility/null rules (L-24) | §6, §8 | YES | YES | Not a battery-gated or capped-read design; seed batteries are ≥2000 with co-designed plant curves; read floors are MDE-consistent by construction (§8/§9 tie the UNPOWERED label to the block MDE, not to a bare `n`). **PASS** |

---

### 2. Numeric verification (independently re-derived — §8)

I recomputed every figure in §8 from `python/experiments/SPDR-018/results/analyst_per_cell_magnitudes.parquet`.

| §8 claim | Design value | Re-derived | Verdict |
|---|---|---|---|
| powered cells | 1,413 | 1,413 (`at_parent_target_precision == True`, all with non-null `gross_p`) | **REPRODUCES** |
| median `(1−p)·L` on powered cells | 48.54 bps | 48.53907609 | **REPRODUCES** |
| median block MDE on the mean | 6.51 bps | 6.51313470 | **REPRODUCES** |
| typical cell resolves `Δlog R` | ≈ 0.123 | per-cell median 0.12280 | **REPRODUCES** |
| IQR | 0.099 – 0.151 | 0.09849 – 0.15092 | **REPRODUCES** |
| median powered cell `n` | 3,427 episodes | 3,427.0 | **REPRODUCES** |
| n-multiple 3.1× / 6.0× / 16.8× | — | 3.09 / 6.05 / 16.81 | **REPRODUCES** |
| implied episodes 10,800 / 21,200 / 58,800 | — | from n=3,427: **10,581 / 20,739 / 57,608** | **DOES NOT REPRODUCE** (see F8) |

The derivation `Δlog R ≈ Δmean / ((1−p)·L)` from `mean = (1−p)·L·(R−1)` is algebraically correct.

Independent measurements taken from the catalog for the power findings below (my own code, H1
resample of `data/catalog/`, Wilder ATR(20), SoT §6.1 signal, `inactiveHold = 2`, `δ = 0.5`):

| Quantity | Measured |
|---|---|
| Actual H1 TRAIN bars, all 25 pinned symbols | **229,646** (confirmed independently by `unit_pin.json.pooled_n = 229646`) |
| Design's implied nominal (25 × 21,648) | 541,200 → effective coverage **42.4 %** |
| Symbol start dates | only `MATICUSDT` starts 2021-06-29; 13 start 2022-07-14/15; **11 start in 2023** |
| DESIGN-band actual bars / CONFIRM-band actual bars | ≈ 91,100 / ≈ 140,200 |
| Signal rate at `δ = 0.5` (6 symbols) | **9.84 – 12.67 %** of H1 bars (pooled 11.41 %) |
| Signal rate at `δ = 1.0` / `δ = 0.25` (BTCUSDT) | 2.80 % / 20.12 % |
| Fill rate within `inactiveHold = 2` (6 symbols) | 0.687 – 0.796 (pooled **0.761**) |
| Episodes per 100 H1 bars at `δ = 0.5` | **8.68** |

---

### 3. Findings

#### F1 — CRITICAL — §8 power statement is built on nominal coverage that the artifact it cites contradicts, and its predeclared-UNPOWERED list omits every hypothesis-bearing stratum

**Fails:** design §8 `POWER` block, line "pooled across 25 symbols on H1 over TRAIN (~21,600 H1
bars/symbol) … yields an ESTIMATED 10k-25k pooled episodes per cell"; SoT §9 **M-4** ("use
effective, not nominal, coverage — power plans must use the effective figure"), which
chapter-06-governance.md §1b declares binding on every 018 design; `design-requirements.md` §6
("strata predeclared UNPOWERED: these can never be read as negatives"); spdr-lane
per-stratum-reporting rule.

Three compounding problems.

**(a) Nominal vs effective coverage.** §8 multiplies 25 symbols × ~21,600 H1 bars. The real
figure is **229,646 bars, 42.4 % of that** — and it is emitted, at run time, by the very
SPDR-018 run §8 cites three lines earlier (`unit_pin.json.pooled_n = 229646`). Only one of the
25 pinned symbols spans the TRAIN fence; eleven do not start until 2023. This is exactly the
defect M-4 exists to prevent, and §12's integrity checklist has no effective-coverage assertion
(it has M-2 span disclosure but not M-4).

**(b) The two errors in §8 partially cancel, which hides the problem at the pooled level and not
below it.** §8 also states a pivot cadence of "1-5 % of H1 bars per symbol"; measured at the
design's own golden-trace threshold `δ = 0.5` it is **9.8–12.7 %**. Net of both errors the pooled
full-TRAIN L0 cell lands at roughly **19,900 episodes** — inside §8's stated 10k–25k range by
coincidence, not by derivation.

**(c) Below the pooled full-TRAIN cell the arithmetic fails, and §8 does not say so.** §10
mandates that **both** bands are "scored explicitly", and §4.3's phase-(b) trigger is defined
**on the CONFIRM band**. Using §8's own `MDE ∝ 1/√n` scaling from (0.123 @ n=3,427):

| Cell | Est. episodes | Implied block MDE (log units) | §9 label it would receive |
|---|---:|---:|---|
| L0 pooled, full TRAIN | ~19,900 | 0.051 | powered |
| **L0 pooled, CONFIRM** | ~12,200 | 0.065 | marginal (bar is 0.07) |
| **L0 pooled, DESIGN** | ~7,900 | 0.081 | **UNPOWERED** |
| **L1 `d ≥ 9`** (top ŝ decile), CONFIRM | ~1,200 | 0.205 | **UNPOWERED** |
| **L2(i) shock axis** (5–13 % of bars), CONFIRM | ~600–1,600 | 0.18–0.29 | **UNPOWERED** |
| **L3 `T-GT-CUR` gate**, CONFIRM | swing-event cadence, sparser still | > 0.2 | **UNPOWERED** |

Every **selection** layer — L1's decile cuts, L2's shock/level cells, L3's swing gate — is the
part of the design that carries HYP-D6's "opportunity-modulated" content, and every one of them
is unpowered **before the run**, by the design's own numbers. §8's estimate is the L0 population
figure applied uniformly to all cells; it contains no term for the selection layers' `n`
reduction. Consequently:

- §8's `strata PREDECLARED UNPOWERED` list (per-symbol cells; `Δlog R ≤ 0.03` targets; sizing
  cells; fill-rate shortfalls) is **inconsistent with §10's own cell inventory** — it omits the
  selection-defined strata, which are the majority of the hypothesis-bearing grid.
- The §4.3 phase-(b) trigger ("any phase-(a) cell has a `log R` CI excluding zero from above, at
  that cell's stated MDE, **on the CONFIRM band**") is close to unreachable on selection cells,
  and on the L0/L4 full-population cells it is at best marginal. As written the design can run
  in full and produce a grid in which nothing can fire the trigger — a `NOT_RESOLVABLE` outcome
  that is knowable now, at zero cost, rather than after execution.

**Required fix (quant-designer).** (i) Re-derive §8 from **effective** coverage (229,646 bars, or
recompute at design time and pin it), stated **per band**, not pooled-over-TRAIN. (ii) State the
expected `n` for each layer stratum, applying that layer's own selection rate, and move every
stratum that cannot reach its target into the predeclared-UNPOWERED list — an honest
`NOT_RESOLVABLE` predeclaration is a first-class result under this design's own §8. (iii) Correct
the cadence figure (measured 8.68 episodes per 100 H1 bars at `δ = 0.5`, fill rate 0.761).
(iv) Add an **M-4 effective-coverage assertion** to §12. (v) Re-examine whether the phase-(b)
trigger should be evaluated on CONFIRM alone given (iii) — and if the answer is that phase (a)
cannot resolve at the CONFIRM band, say so in §8 before the run rather than discover it after.

---

#### F2 — HIGH — exit fill resolution is undeclared; the causal fill rule covers entry stops only

**Fails:** §2 fill-rule table (entry only); §4.2 (introduces profit target and trailing stop with
no resolution rule); §5 (`r` definition); §6.1 TRIPWIRE-2 (entry fills only); spdr-lane "any
limit-fill simulation resolved causally on the 1-minute bars, no intrabar look-ahead".

§2's three-row fill table is coherent and, as far as it goes, causally clean: the fill decision
uses only the M1 bar's own range, the fill price is the pre-known stop, and the gap case is
resolved adversely and never improved. No look-ahead is possible in the stated entry procedure.
**But it is the entry procedure only.** §4.2 then adds two path-dependent exit devices, and the
design never states:

1. **Intrabar precedence.** When a profit target and a trailing stop both lie inside one M1 bar's
   range, which fills? This is the classic OHLC path-ambiguity bias, it is not resolvable from
   M1 OHLC, and it moves `W`, `L` **and** `p` — the three sufficient statistics of the primary
   read. An optimistic convention (target first) manufactures exactly the `p`-high / `W/L`-high
   signature that L-51/P-22 documents as an artifact.
2. **Trailing-stop update cadence.** Does the trail ratchet on M1 extremes or on decision-clock
   bar closes? Unstated. A trail that ratchets on M1 while the state is `t−1` on H1 is a
   different device from one that ratchets hourly. This is the QA skill's named "frozen
   computation / exit that never updates" failure shape, and its mirror.
3. **Exit price for the time exit.** §2 says "close after `activeHold` periods"; §5 defines `r`
   as "signed gross **open-to-open** return, bps, **entry fill -> exit fill**". Those two
   clauses contradict each other — the entry is a mid-bar stop fill, not an open. The spdr-lane
   integrity boundary requires open-to-open returns; the design needs one convention, stated
   once, and it must be the same one §12's identity assertion reconciles against.
4. **TRIPWIRE-2 scope.** It re-resolves *stop fills* on decision-clock OHLC. It does not test
   exit resolution, so the M1-vs-H1 discrimination is unproven for exactly the devices (L4) whose
   whole purpose is to move `W/L`.

**Required fix (quant-designer).** Add an exit-resolution block to §2 with: a declared,
pessimistic intrabar precedence rule (adverse-first is the convention consistent with §2's gap
handling); the trailing-stop ratchet clock; the time-exit price convention reconciled with §5;
and extend TRIPWIRE-2 (or add TRIPWIRE-3) to cover exit resolution.

---

#### F3 — HIGH — `deltaThreshold` is not frozen, and §8's power depends on it by a factor of ~7

**Fails:** §2 heading ("The entry — **fixed, frozen**, not the research subject"); §13 bullet
("`deltaThreshold` is calibrated for **sample size**, not for `p` — and its calibration is
emitted so QA can verify which was optimised"); §11 G1/G2 (hard-code `deltaThreshold = 0.5`);
§4.1 L0 row (fixes `activeHold`, `inactiveHold`, no target, no stop — but not `deltaThreshold`).

§13's refusal is the right refusal (no tuning for `p`), but "calibrated for adequate signal
sample size" is not an algorithm, and no value is frozen anywhere in the design except inside two
golden traces. Measured on BTCUSDT H1 TRAIN, the signal rate is **20.1 % at δ=0.25, 9.8 % at
δ=0.5, 2.8 % at δ=1.0** — a ~7× swing in the population, hence a ~2.7× swing in every block MDE,
hence direct control over which §9 band label each cell receives. An unpinned parameter that
determines the experiment's power is a researcher degree of freedom regardless of what it is
nominally optimised for; and if the calibration lands anywhere other than 0.5, G1/G2 no longer
trace the L0 population.

**Required fix (quant-designer).** Either freeze `deltaThreshold` in §2/§4.1 (0.5 is defensible —
it is the golden traces' own value and yields ~8.7 episodes per 100 bars), or state the
calibration as a **deterministic, pre-registered rule** evaluated on a declared quantity that is
not an outcome (e.g. "the smallest δ in a declared grid whose pooled CONFIRM episode count ≥ the
§8 requirement"), emit it, and make G1/G2 reference the rule rather than a literal.

---

#### F4 — MEDIUM — §4.1/§4.2 narrow reflection §5.9's L4 modulation without declaring the narrowing; §10's cell count is not derivable from §4.2 and exceeds its own cap

**Fails:** reflection `§5.9` (BINDING): *"Inside L4, every device is tested twice: once
unmodulated (a fixed multiple of ATR) and once modulated **by each volatility layer**"*;
design §4.1 L4 row and §4.2; design §10 "Cell count".

- §4.1 L4 reads "modulated (the same multiple **× ŝ**)" and §4.2's Modulated column is `a × ŝ(h)`,
  `b × ŝ(h)`, `activeHold` scaled to `E[run]`, `c / ŝ`. That is modulation by **L1 (scale) only**.
  L2-state and L3-gate modulation of the devices is absent from phase (a). §5.9 is an operator
  directive marked BINDING; a narrowing of it needs to be declared and carried in §14, not made
  silently. (It may be a defensible narrowing — the full set is what phase (b) is for — but it is
  undeclared, and §14 asserts zero amendments.)
- §10 gives `L0 1 + L1 4 + L2 5 + L3 3 + L4 ~44 + L5 ≤4` = **61**, against a stated cap of
  **≤ 60**. The decomposition contradicts its own bound.
- §4.2 as written yields ~17–20 L4 cells (target 3+3, trail 2+2, hold 4+n, sizing 1+1), not ~44.
  ~44 is only reachable under the broader §5.9 reading that §4.1 dropped. So §10 and §4.2 are
  counting different experiments.

**Required fix (quant-designer).** Reconcile §4.2's grid, §10's count and §5.9's requirement; if
the ŝ-only narrowing is intended, record it as an amendment row in §14 with a direction label.

---

#### F5 — MEDIUM — §9's interpretation bands do not partition; cells can land unlabelled

**Fails:** §9 `BANDS`; `design-requirements.md` §5 (bands are per-stratum labels covering the
outcome space); INFR-016 report-layer discipline.

As written:
- `SUPPORTED`: `log R ≥ +0.03` **and** `ci_low > 0`
- `WASH`: `|log R| < the cell's own block MDE`
- `CONTRADICTED`: `log R ≤ −0.03` **and** `ci_high < 0`
- `UNPOWERED`: block MDE > 0.07 **or** `n` below the §8 requirement

Two uncovered regions:
- `log R = +0.08`, MDE `0.06`, `ci_low ≤ 0` — not SUPPORTED (CI fails), not WASH (0.08 > 0.06),
  not CONTRADICTED, not UNPOWERED (0.06 ≤ 0.07). **Unlabelled.**
- `log R = +0.02`, MDE `0.01`, `ci_low > 0` — not SUPPORTED (< 0.03), not WASH (0.02 > 0.01).
  **Unlabelled.**

Given that §8 predicts most cells will sit near the 0.07 boundary, the first region is not
hypothetical. An unlabelled cell in an emission is where a reader supplies their own label.

**Required fix (quant-designer).** Add an explicit residual label (`SUGGESTIVE` /
`INDETERMINATE`, excluded from negatives per B-5 and from positives per B-5's symmetry), or
redefine the bands so the four cases are exhaustive and mutually exclusive.

---

#### F6 — MEDIUM — the L-51 three-number selection check is not a HARD check and is scoped inconsistently

**Fails:** chapter-06-governance.md §1b ("no powered subset's magnitudes may be read without the
three-number selection check (**L-51**)"); pitfalls-ledger **P-22**; design §4.1 (L3 row only),
§15 (`selection_check.json` — "on every powered subset"), §12 (absent), §12 HARD list (absent).

Every magnitude read in this design is a read on a **selected** subset: §9's UNPOWERED rule filters
on the cell's own realised block MDE, which is a dispersion gate, which L-51 establishes is
non-neutral on skewed P&L. So the check applies to every stage, not only L3. §4.1 attaches it to
L3; §15 says "every powered subset"; §12 does not mention it at all and it is not HARD. Under
L-52's own logic (a check not reconciled by name against the design's declared list is a check
that can silently not run), this is precisely the shape that failed four times in the SPDR-018
build.

**Required fix (quant-designer).** Move the L-51 check to §12, scope it to every powered subset at
every stage, and place it in the HARD list (or state explicitly why a missing selection check is
INFORMATIVE here).

---

#### F7 — MEDIUM — `activeHold ∈ {1, 4, 12, 20}` expands the checkpoint's frozen horizon set with no amendment row

**Fails:** checkpoint-018 `design.md` §8 ("Horizons: `h ∈ {4, 12, 24}` bars; H1 primary; frozen
per SPDR design") and §1 ("Per-SPDR designs may **narrow** arms and horizons"); design §4.2, §14
("No amendments to this design").

`activeHold = 1` is defensible on SoT precedence (SoT §6.1 default is 1 period, and SoT substance
outranks the checkpoint's procedural freeze). `activeHold = 20` is in neither set; it is derived
from the measured `E[run]` 18.9–23.1, which is sound science but is an **expansion**, not a
narrowing, of a frozen default. §14 declares zero amendments, so the expansion is unrecorded.

**Required fix (quant-designer).** Add an amendment row to §14 with a direction label, or move 20
to the nearest frozen value.

---

#### F8 — LOW — §8's implied-episode column uses a base `n` of ~3,499, not the stated 3,427

**Fails:** design §8, "scaling MDE ∝ 1/√n from a median powered cell of n = 3,427 episodes".

From n = 3,427 the table should read **10,581 / 20,739 / 57,608**; it reads 10,800 / 21,200 /
58,800 — a uniform +2.1 %, consistent with a base of 3,499. The stated median (3,427) reproduces
exactly from the parquet; the table does not follow from it. The direction is **conservative**
(the design demands more episodes than its own arithmetic requires), so this is presentational
rather than a rigour risk — but §9's UNPOWERED band cites "n below the §8 requirement", so the
number is load-bearing and should reconcile.

Related, minor: SPDR-018's `gross_n` is a per-cell leg/observation count whose unit varies by arm;
§8 reads it as "episodes". Worth one clause of disclosure.

---

#### F9 — LOW — §8's stated pivot cadence (1–5 %) is contradicted by measurement (8.7–12.7 %)

**Fails:** design §1 `MECHANISM` ("Event cadence: pivot events, ~1-5% of H1 bars per symbol") and
§8's POWER block.

Measured across BTC/ETH/SOL/DOGE/LINK/PEPE/ADA/OP at `δ = 0.5`: signal rate 9.84–12.67 %, fill
rate 0.687–0.796, net **8.68 episodes per 100 H1 bars**. The 1–5 % figure is only reached near
`δ ≈ 1.0` (2.8 % on BTCUSDT). Folded into F1; listed separately because §1's MECHANISM block also
carries it and both need the same correction.

---

#### F10 — LOW — amendment-ledger labelling

**Fails:** `design-requirements.md` §12 (`DIRECTION: LOOSER | TIGHTER | NEUTRAL`); design §14.

- C5 is labelled **NARROWING**, which is not one of the three permitted directions. (The family
  contract uses the same word, so the design is consistent with the registry — but the ledger
  format requires one of three, and a narrowing is a TIGHTER.)
- §10 relies on "AMENDMENT-C3 precedent" for disclosed-not-rationed multiplicity, but §14's
  "amendments in force" list omits C3. C3 is a **multiplicity-registry** amendment
  (`docs/signal-registry/multiplicity-registry.md:1660`), not a family-contract one — correct in
  substance, but §14 should say so rather than leave the citation dangling.

---

#### F11 — INFO — only 1 of the reflection's 5 pre-registered predictions is carried

Reflection §5.6 states five falsifiable predictions "so the strategies have pre-registered
expectations". The design carries **prediction 4** (L2 shock/level near-independence, §4.1 L2
row). Predictions 1 (ŝ-scaling leaves `log R` unchanged), 2 (`T-GT-CUR` moves `W/L` < ~0.3),
3 (hold ≈ `E[run]` → `W/L` ≈ 1, `p` ≈ 0.5) and 5 (cTrader σ̂-ratio scaling; out of phase-(a) scope
under C1) map directly onto L1, L3 and L4-hold respectively and cost nothing to pre-register.
§5.6 is not marked BINDING, so this is a strengthening suggestion, not a violation.

---

#### F12 — INFO — P-02 / P-04 are not acknowledged in §13

The pitfalls ledger records **P-02** ("tuning the downstream stack — exits, capture geometry,
conditioning, anchors, sizing — to rescue a dead entry … Re-open only if: **Never, on a dead
entry**") and **P-04** (CF-CAPGEO-001 capture-geometry basket). SPDR-019 is, on its face, capture
geometry wrapped around an entry whose direction is measured dead.

**I do not report this as a violation**, because the design is framed the way P-02's escape
requires: it is a **measurement** experiment with a pre-registered zero expectation (§1: "A zero
baseline residual is a predeclared, acceptable, and expected outcome"), a named mechanism
(forecastable move scale rescaling the magnitude distribution — governance §1b's "name the
mechanism, not a search" requirement), an exact-null falsifier, and an explicit refusal of
expectancy claims (§13). It is authorised at three levels above the design (SoT §6, checkpoint §5
Step 3, governance §1b step 3). But §13's refusal list should **name P-02 and P-04 and state the
distinction**, so that a later reader cannot mistake a phase-(b) grid for a rescue search. One
line.

---

### 4. Checks that PASS and are worth recording explicitly

These are the risks the review was asked to probe hardest. All clean.

| Check | Result |
|---|---|
| **Exact-mirror target (slope 1)** | **CLEAN.** §1, §5 and §9 all define `log R = log(W/L) − log((1−p)/p)`. The fitted slope **0.9408 appears exactly once (§5)** and is there to be **refused** as a target, with the correct reason (its residual is centred at zero by construction). §13 refuses it again; §12 makes a fitted-slope residual appearing anywhere a **hard failure**; **G5 exists solely to make audit item A1 non-repeatable**. This is the strongest part of the design |
| **AMENDMENT-C5 cost isolation** | **CLEAN.** I traced every cost mention: header NOTE, §5 `DISCLOSED REFERENCE ONLY`, §7 cost floor "no read in this design is compared against it", §9 (bands are purely on `log R`), §12 HARD cost-isolation check with `p_be_net` flagged `DISCLOSURE_ONLY`, §13 refusal, §15 `metrics_by_cell` column flagged. **No estimand, threshold, band or comparison in the document takes a cost term.** §8's MDE conversion is bps→log units via `(1−p)·L`, which is a gross quantity |
| **AMENDMENT-C6 phase (b)** | **CLEAN.** The trigger is stated in §4.3 **before** phase (a) runs, is a single stated condition ("any phase-(a) cell has a `log R` CI excluding zero from above … on the CONFIRM band. That is the whole condition"), and explicitly refuses post-hoc definition of "promising". The scope is fixed and complete, **individually-flat layers are retained on equal footing**, the estimand is the **interaction** `Δlog R(combined) − Σ Δlog R(individual)`, and §4.1's L5 row explicitly states that L5 "does not and cannot substitute for phase (b)". The trigger cannot act as a filter. **The one live concern is F1** — that the trigger may be unreachable for power reasons, which is a power defect, not a C6 defect |
| **Entry fill causality** | **CLEAN as far as it goes** (see F2 for exits). The M1 rule uses only the bar's own range; the fill price is pre-known; gaps resolve adversely and are "never improved"; unfilled orders are emitted, not dropped; fill rate is reported per cell precisely because a variant that changes it re-selects the population. §12 asserts every fill's M1 timestamp > its decision-bar close. No look-ahead is possible in the stated entry procedure |
| **L-28 derangements** | **CLEAN.** Both permutation controls declare `destroy form: DERANGEMENT (zero fixed points)`; §12 asserts `fixed-point count == 0, measured and reported`; TRIPWIRE-1 correctly declares `N/A` (it is an index shift, not a permutation) |
| **L-52 / P-23 check integrity** | **CLEAN and unusually thorough.** §12 asserts the **expected number** of HARD checks and reconciles them **by name**; every check depends on an emitted artifact ("missing or empty is a failure, never a vacuous pass"); determinism runs **unconditionally whenever `--jobs > 1`, independent of `--resume`"; "No required check lives in a manual post-step". This closes all four SPDR-018/018B failure modes |
| **P-24 comparator disclosure** | **CLEAN.** The M-3 block mandates the comparator's own mean, its null quantiles **and** its plant curve with every percentile, and states a bare percentile "is uninterpretable and is refused". Both derangement controls disclose null mean/sd/quantiles |
| **L-50 / P-21 threshold portability** | **CLEAN.** Every band threshold (±0.03, 0.07) is in **log units** — dimensionless and universe-free by construction. §7 states a σ-unit effect is never compared to the cost floor. cTrader is excluded from phase (a) under C1 |
| **L-21 / P-15 unit pin** | **CLEAN.** Both divisor objects named to indicator/period/clock/lag; σ̂ wording matches `SPDR-018/results/unit_pin.json` verbatim; measured values computed at run, never recalled |
| **SPDR-lane integrity boundary** | TRAIN-only ✓ (§10 fence + §12 assertion); causal `t−1` ✓ (§2, §12, TRIPWIRE-1); no tradability claim ✓ (§2, §13, header); matched control + seed battery ✓ (M-3 comparator; ≥2000 seeds, far above the ≥25 floor); per-stratum reporting + multiplicity disclosed ✓ (§9, §10); no local accounting ✓ (§12); dependence-matched uncertainty ✓ (block ≥ holding horizon, §1/§6/§8; iid form explicitly companion-only) |
| **B-5 symmetry** | **CLEAN.** §9 excludes UNPOWERED from negatives "permanently"; §13 refuses reading UNPOWERED or NOT_RESOLVABLE as a negative **and** reading SUGGESTIVE as SUPPORTED; §8 makes `NOT_RESOLVABLE` a first-class reported result with the shortfall quantified |
| **Registry / hypothesis wording** | **CLEAN.** §1's falsifiable question matches `cf-voldir-001.md` HYP-D6's registered wording (as narrowed by C5) clause for clause |
| **Holdout / XENA / family action** | **CLEAN.** §10 holdout never queried + §12 assertion; §13 refuses any family status change, XENA, TEST or holdout contact; header declares execution unauthorised |

---

### 5. Golden-trace review (design-stage: adequacy, not diff)

No emission exists, so no diff is possible. Assessed for whether G1–G6 are **independently
computable by QA from the design text plus the catalog**, which is their stated purpose.

| Trace | Independently computable? | Notes |
|---|---|---|
| G1 (entry + fill, L0) | **Partly** | Selection rule is deterministic *given* `δ`. It hard-codes `δ = 0.5`, which §4.1/§13 do not freeze — **see F3**. Also: BTCUSDT data starts 2022-07-15, inside the DESIGN band, so "the FIRST bar" is well-defined but is not the band's first bar; harmless, worth a note |
| G2 (expiry path) | YES | Deterministic; correctly asserts the unfilled signal enters the fill-rate denominator and no `(p, W, L)` term |
| G3 (suppression) | YES | Directly tests the B-9 exclusivity guard |
| G4 (identity + primary read) | YES | The strongest trace: reconstructs `p`, `W`, `L` from episode rows, asserts the identity to < 0.01 bps, then recomputes `log R` from those same three numbers |
| G5 (mirror null is the exact one) | YES | Purpose-built to make audit A1 non-repeatable. Keep exactly as written |
| G6 (leak discrimination) | YES | Ties TRIPWIRE-1 to a specific row set |
| **Missing** | — | No trace covers **exit** resolution — the target/trail precedence and ratchet cadence of **F2**. A G7 on an L4 device is needed once F2 is specified |

---

### 6. Governance & boundary checklist

| Item | Evidence | Result |
|---|---|---|
| Fresh context | This review was produced in a dedicated subagent that did not author the design | PASS |
| `check_no_local_accounting` | N/A — no `screen_code/` yet. §12 declares the check | DEFERRED to QA run 2 |
| No Python strategy backtest | This is a vectorised SPDR screen, the sanctioned lane vehicle | PASS |
| Registry precondition | `CF-VOLDIR-001` REGISTERED; `HYP-D6` registered; SPDR-019 registered 2026-07-25 | PASS |
| Counted TEST reads | 0 declared; §13 refuses TEST/holdout contact | PASS |
| CONVERSION-PIN (L-21) | §7; σ̂ object verified against `SPDR-018/results/unit_pin.json` | PASS |
| SPREAD-COST-DISCLOSURE | header block; all fields | PASS |
| Amendment-direction ledger (L-23) | §14; 0/0/0 correct; see F10 (labelling) and F4/F7 (undeclared narrowing/expansion) | PARTIAL |
| XENA VOID on new stack (INFR-010 R4) | Design routes to no XENA; §13 refuses it | N/A — PASS |
| L-24 battery rules | Not battery-gated; MDE-consistent read floors present | PASS |
| L-28 derangement | §6, §12 | PASS |
| L-31 one BacktestNode per process | N/A — no Nautilus engine in this lane | N/A |
| Holdout untouchable | §10, §12 | PASS |
| DEVIATIONS block | None claimed; none needed at design stage | PASS |
| **Start gate** | Governance §4 start-gates SPDR-019 on the mid-checkpoint reflection. The reflection **companion** (`reflection-mid-volatility-model.md`) is delivered and carries the binding C5/C6 directives, but `reflection-inputs.md` §9 — the **operator decision** — remains **unsigned** (governance line 84; checkpoint design §6 row 4). Design registration does not require it; **execution does**. Flagged for the operator, not counted as a design defect | FLAG |

---

### 7. Routing

- **F1, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12 → `quant-designer`** (design defects; no code
  exists to fix).
- **F2 → `quant-designer`** (specification gap; becomes an `experiment-developer` clause once
  specified).
- Re-run QA after revision. F1 and F2 are implementation-blocking: F1 because the grid's power
  is knowable now and most of it does not resolve, F2 because the exit convention determines
  `W`, `L` and `p` and therefore the primary read.

**Nothing found rises to REJECT.** There is no holdout contact, no causality violation, no
missing tripwire, no cost smuggling, no fitted-slope target, and no unapproved silent deviation.

---

## QA run 2 — 2026-07-28T18:56:49Z — mode: subagent — HEAD 51d6a281ef2f0833cbc15c3fa062f70409a1b983 (clean tree)

**Target:** `python/experiments/SPDR-019/design.md` (644 lines; 525 at run 1)
**Stage:** DESIGN-STAGE review. `screen_code/` still does not exist; that is the expected state and
is **not** a finding. No design-to-code fidelity trace is possible or attempted.
**Independence:** this reviewer did not author the design or the run-1 review, and re-derived every
number below from the cited artifacts rather than from the design's own account of its fixes.

**Verdict: REVISE**

Findings: **3 HIGH · 6 MEDIUM · 5 LOW · 1 INFO**

Plain reading: the three run-1 blockers are **substantively fixed** — the population figure now
reproduces exactly from the artifact, the exit fills are fully specified with an adverse-precedence
rule, and `deltaThreshold` is genuinely frozen as a three-value swept axis. Nothing about the exact
mirror or the cost quarantine has regressed; both are still the strongest parts of the document.
What blocks it now is different: **the two power levers were adopted without their scientific
costs**, one of which is contradicted by the family's own M15 evidence; **the phase-(b) trigger
change contradicts a registered in-force amendment** the design lists as binding on itself; and the
**sensitivity ladder that replaced the power statement has no stated computation**. Six run-1
findings were also never touched.

---

### PART A — closure of the run-1 blockers

#### Blocker 1 (run-1 F1: bar count 2.35× too large) — **CLOSED**, verified independently

Re-derived from `SPDR-018/results/unit_pin.json` and `analyst_per_cell_magnitudes.parquet`:

| §8 claim | Design | Re-derived | Verdict |
|---|---|---|---|
| pooled H1 TRAIN bars, 25 symbols | 229,646 | `sum(per_symbol.n)` = **229,646**, `pooled_n` = **229,646** | REPRODUCES |
| MATICUSDT the only symbol spanning the window | 21,582 | 21,582; next largest 12,468 | REPRODUCES |
| median symbol | 12,444 | 12,444 | REPRODUCES |
| smallest symbol | 555 | 555 (`1000RATSUSDT`) | REPRODUCES |
| the 2.35× overstatement | 541,200 / 229,646 | **2.357** | REPRODUCES |
| powered cells | 1,413 | 1,413 | REPRODUCES |
| median `(1−p)·L` | 48.54 bps | 48.53908 | REPRODUCES |
| median block MDE on the mean | 6.51 bps | 6.51313 | REPRODUCES |
| typical cell resolves `Δlog R` | ≈0.123 (IQR 0.099–0.151) | 0.12280 (0.09849–0.15092) | REPRODUCES |
| median powered-cell `n` | 3,427 | 3,427 | REPRODUCES |
| n-multiples | 3.1 / 6.0 / 16.8 | 3.08 / 6.03 / 16.76 | REPRODUCES |
| implied episodes | 10,800 / 21,200 / 58,800 | **10,547 / 20,671 / 57,420** | **DOES NOT REPRODUCE** — see R2-11 |

The correction is real, it is sourced to the artifact, and the design says plainly that the earlier
figure was wrong and by how much. Governance's binding M-4 rule ("power plans use effective, not
nominal, multi-symbol coverage", `chapter-06-governance.md:105`) is now satisfied in §8. **Closed.**
Two residues carry forward: no M-4 assertion reached §12 (run-1 F1(iv), see R2-13), and the
per-stratum expected-`n` statement run-1 F1(ii) demanded was **deleted rather than answered** (see
R2-04).

#### Blocker 2 (run-1 F2: exit fills unspecified; open-to-open contradiction) — **CLOSED on specification, OPEN on verification**

§2's new exit table answers all four sub-items: profit-target price, trailing-stop ratchet clock
(once per M1 bar, on that bar's close, never intra-bar), time-exit price (open of the first
decision-clock bar at or after `activeHold`), intrabar precedence (**adverse fills**), and
target-vs-time precedence. §5 now states explicitly that open-to-open describes the **time exit
only** and names the earlier draft's wording as the error. This is a clean, pessimistic, causally
resolvable specification. **Specification closed.**

But run-1's required fix had a second half — *"extend TRIPWIRE-2 (or add TRIPWIRE-3) to cover exit
resolution"* — and its golden-trace section required *"a G7 on an L4 device … once F2 is
specified"*. Neither landed. §6.1 TRIPWIRE-2 still reads "re-resolve **stop fills**"; §11 still ends
at G6. See R2-06.

#### Blocker 3 (run-1 F3: `deltaThreshold` unpinned) — **CLOSED in §2/§10/§14, CONTRADICTED in §13**

§2 now freezes `δ ∈ {0.25, 0.5, 1.0}`, all three reported side by side, none selected, with the
realised signal rate emitted per level; §10's freeze table repeats it; §14 records it as
AMENDMENT-3 TIGHTER. That is exactly the fix. **But §13 line 571–572 still carries the original
text run-1 quoted as the failing clause:** "`deltaThreshold` is **calibrated for sample size**, not
for `p` — and **its calibration is emitted** so QA can verify which was optimised." §2 says "There
is no calibration step". One of the two is wrong, and the surviving sentence is the one that
describes the defect. See R2-08.

---

### PART B — defects in the changes

#### R2-01 — HIGH — §4.3 replaces the phase-(b) trigger with operator judgement, which is the exact thing registered AMENDMENT-C6 forbids, and no amendment row records the change

**Fails:** `docs/signal-registry/candidate-families/cf-voldir-001.md` AMENDMENT-C6 (TIGHTER,
operator directive 2026-07-28, listed by this design's own §14 as **in force**): *"the (b) trigger is
**pre-declared before (a) runs** (deciding afterwards what counted as promising is optional
stopping)"*; reflection §5.9.1 Consequences table, row **Trigger**: *"Pre-declared **before phase (a)
runs**, in the design, as a stated condition on the (a) reads. **Deciding afterwards what counted as
'promising' is optional stopping**"*; design §4.3; design §14.

§4.3 states: *"Trigger: the operator decides, on the full phase-(a) report. No numeric cutoff is
written here."* That is the clause C6 was written to prohibit, verbatim in substance.

**On the substance, the design's own defence is half right and I record that plainly.** The
protection C6 lists under **Scope** — that (a) may not shrink (b) — **does survive intact**. §4.3
holds the {L1,L2,L3} × {target, trail, hold, sizing} cross fixed, keeps individually-flat layers on
equal footing, and keeps the interaction estimand. I checked this against C6's two recorded grounds
and both are still answered. The design is correct that the shrink protection never depended on the
trigger being numeric.

**But the trigger clause protects a different thing, and that protection is now gone.** Phase (b) is
a further read on the **same episode population**; conditioning whether it happens on a post-hoc
reading of (a) is optional stopping on a shared sample, which is precisely what C6 names. INFR-016
("machines gate integrity, the operator judges value") is real but does not reach here: INFR-016
retired *arbitrary value gates that machine-dropped cells*, and §4.3's trigger drops nothing — it
only decides whether more data is read.

There are two separate defects and they need separating:

1. **Governance.** A design may not silently override a registered TIGHTER amendment it lists as in
   force. Either amend C6 on the family contract, or restore a pre-declared condition.
2. **Ledger.** §14 has **no row** for this change, and its "running count: 2 looser / 2 tighter /
   2 neutral" is therefore wrong. Retiring a pre-declared trigger is **LOOSER**; adding it makes the
   count 3 looser / 2 tighter / 2 neutral, and L-23's one-directional-streak flag then needs
   re-checking at the execution gate.

**Required fix (quant-designer + operator).** Either (a) restore a condition stated before (a) runs
that is *not* a value bar — e.g. "phase (b) is authorised unless every phase-(a) cell's CI on
`Δlog R` covers zero at a resolution finer than the 0.05 rung", which is a resolution statement, not
a magnitude gate and not a machine drop — or (b) carry an operator-signed amendment to C6 on the
family contract, and add the §14 row with `DIRECTION: LOOSER`.

#### R2-02 — HIGH — M15 is made the primary read on power grounds alone; SPDR-013 measured this entry class's *direction* on M15 as **worse than shuffled**, which would bias every M15 cell below the mirror

**Fails:** design §10 Clocks row; §8 "Consequence, stated plainly: the primary reads live on **M15**
…"; §14 AMENDMENT-2 ("Cost: multiplicity"); §1 MECHANISM ("this design **assumes p sits at its own
break-even**"); §9 BANDS (`BELOW THE MIRROR` is "itself a finding").

I read `SPDR-013/analysis.md` for the family's own M15 evidence. Two results, pointing opposite ways,
and the design cites neither:

**Supporting the amendment** (§7, §0 item 3): the ZZ next-swing **magnitude** forecast is
*better* on M15 than H1 — "OOS IC 0.34–0.46, ridge ≥ AR1, **M15 > H1**, all 25 symbols". Scale
forecastability at M15 is measured, in-family, on the whole universe. This is a materially stronger
warrant for AMENDMENT-2 than the argument §10 actually gives, and it should be cited.

**Against the primary-read choice** (§6 controls, §5 table, §4): on M15 the signed direction reads
**worse than random** — DIRECTION-DERANGEMENT live percentile **0.20–0.28 on M15** against 0.48–0.57
on H1, with a +20 bps bite plant detected (so the control is not blind); M15 combined gross **−2 to
−3 bps** against H1 "breakeven-to-slightly-positive"; `p_right` 0.28–0.43.

The consequence is structural, not stylistic. §1 assumes `p` sits at its own break-even, so a zero
baseline `log R` is the predeclared expectation. If M15 direction sits below shuffled, the **L0
baseline `log R` on M15 sits measurably below zero**, and under §9's CI-relative bands *every* M15
cell reads `BELOW THE MIRROR` — a finding about the entry on that clock, which §9 explicitly calls
"itself a finding", with no clause anywhere separating it from a finding about capture geometry.
The design would then have put its **primary** read on the clock where its own null is displaced.

The entry differs (three-bar pivot breakout vs SPDR-013's trend/ZZ arms), so this is a prior, not a
refutation. But it is a powered, same-universe, same-fence prior on the exact object being moved to
the primary slot, and §14's cost column for AMENDMENT-2 says only "Multiplicity".

**Required fix (quant-designer).** (i) Cite both SPDR-013 M15 results in §8/§14 and correct
AMENDMENT-2's cost column. (ii) Pre-register the M15 baseline expectation (`L0 log R` may sit below
zero) as a falsifiable prediction. (iii) State that on M15 the primary comparison is **Δ`log R` vs
that clock's own L0**, with level `log R` co-reported, so a displaced baseline cannot be read as a
capture-geometry result — or move the primary read to H1 and keep M15 as the power co-report.

#### R2-03 — HIGH — the L4 modulated and unmodulated arms are in different units with no scale-match declared; the comparator that is supposed to isolate "information" also carries a level shift

**Fails:** §4.2 ("Each device runs twice: unmodulated (`a × ATR20`) and modulated (`a × ŝ(h)`) …
**the unmodulated run is the comparator that separates the device from the information**"); §7
CONVERSION-PIN (divisor object 1 in price/ATR units on the decision clock; divisor object 2 "in bps,
horizon-scaled `ŝ*√h`", computed on **H1**); L-21 / P-15; the QA-skill failure shape "a comparator
that differs from the design's control in size/population".

Three unbridged seams, none declared:

1. **Units.** `a × ATR20` is a decision-clock ATR (price/ATR units); `a × ŝ(h)` is a bps quantity.
   No conversion is stated anywhere. Even after converting ATR to bps the two estimators do not have
   the same expectation: Wilder ATR ≈ mean true range, while Parkinson σ ≈ range / (2√ln 2) ≈ 0.6 ×
   range. At the same `a` the two arms get **systematically different exit widths** (order 1.5–1.7×).
2. **Clock.** On the M15 primary clock, ATR20 is a 20-**M15**-bar object while ŝ is an **H1**
   object horizon-scaled by `√h` — and §7 never says what `h` is counted in on the M15 clock.
   Reading `h` as M15 periods against an H1-per-bar ŝ inflates every modulated width by **2×**. This
   is the EXP-025 units-seam shape (4× ATR-unit inflation at a screen seam) that L-21…L-24 exist for.
3. **Holds.** §4.2 bounds `activeHold ∈ {1,4,12,20}` by "`E[run]` 18.9–23.1 **H1 bars**". On M15,
   20 bars = 5 H1 bars — the sweep does not reach the stated scale at all — and the modulated arm
   ("`activeHold` scaled to the state's `E[run]`") needs an H1→M15 conversion that is not written.

The consequence is that the unmodulated arm is **not** a matched comparator. It differs from the
modulated arm in mean width as well as in whether width varies with ŝ, so every `Δlog R` per device
confounds a level effect with the information effect the pair exists to isolate. Exit width moves
`W`, `L` and `p` — all three sufficient statistics of the primary read.

**Required fix (quant-designer).** Add a scale-match clause to §4.2/§7: express the modulated arm as
`a × ATR20 × (ŝ / median_TRAIN(ŝ))` (or equivalently normalise both arms to the same TRAIN-median
width per symbol and clock), so the two arms are matched on mean width by construction and differ
only in cross-sectional variation. State the H1→M15 conversion for `√h` and for `E[run]` explicitly,
and add it to §12's causality/unit assertions.

#### R2-04 — MEDIUM — the sensitivity ladder has no stated computation, and it is now the design's entire resolution object

**Fails:** §8 RESOLUTION block ("the fraction of block-bootstrap replicates in which a **PLANTED
effect of that size** would have been detected at its own realised `n`"); §12 "Ladder emitted";
§15 `resolution_ladder.parquet`; AMENDMENT-C7 (which makes the ladder the replacement for the power
statement); L-24 §12 clause "MDE-consistent read floors".

Planting an effect of `Δlog R = 0.05` on an episode series is **not a unique operation.** `log R` is
a function of `p`, `W` and `L` jointly, and a 0.05 log-unit shift can be planted by moving `p`, by
moving `W`, by moving `L`, or by any combination — and the three routes give *different* detection
rates, because they perturb the block-bootstrap variance differently. The design nowhere states
which. A ladder whose plant route is a developer choice is an unpinned researcher degree of freedom
sitting directly under the only resolution number the design now reports.

This is structurally the same gap as run-1's F2: a new primary device introduced without its
resolution rule. It matters more here because C7 removed the fallback.

**Required fix (quant-designer).** State the plant operator explicitly — e.g. "planted by scaling
every winning episode's `r` by `exp(Δ)` with losses unchanged, which moves `W` alone; the `p`-route
and `L`-route are co-reported on the L0 cell as a sensitivity" — and add the plant route to §12's
asserted list.

#### R2-05 — MEDIUM — the M15 power gain is stated in bars, but block dependence is calendar-based, so the ~4× is an overstatement of independent information

**Fails:** §8 AMENDMENT-2 lever table ("**~4×**"); §1 DERIVED `test` and §6 MIRROR-NULL
("block >= holding horizon"); `docs/references/spdr-lane.md:37` dependence-matched-uncertainty rule
and its Phase-010 precedent (block=5 on H=48 overlapping windows understated uncertainty 2–3× and
manufactured a thread that did not exist).

The design's block rule is stated in **bars** ("block ≥ the holding horizon"). On M15 a 20-bar block
spans 5 hours; on H1 it spans 20 hours. Volatility clustering and regime persistence — the very
things ŝ and the L2 state axes condition on — are **calendar** phenomena, so four M15 episodes inside
one hour are far from four independent H1 episodes. The lever table's "~4× n" therefore does not
translate into a 2× MDE improvement; the realised gain will be smaller and is not bounded anywhere in
the design.

I verified the *unit* half of the conversion is sound: the noise constant `c = MDE_mean·√n /
((1−p)·L)` is clock-invariant to first order (both numerator and denominator scale with σ), and it
reproduces stably across bases — median **7.28** on the powered subset, **6.60** on all 23,527 cells
with IQRs that overlap heavily. So the *arithmetic* transports; it is the *independence* assumption
that does not.

**Required fix (quant-designer).** State the block length in **calendar time**, matched across
clocks (e.g. block ≥ max(holding horizon, 20 H1-equivalents)), and emit the realised effective
sample size per cell alongside `n`. Restate AMENDMENT-2's lever as "~4× raw episodes; effective gain
smaller and measured at run".

#### R2-06 — MEDIUM — the new exit rules have no tripwire and no golden trace

**Fails:** §6.1 TRIPWIRE-2 ("re-resolve **stop fills**"); §11 (G1–G6, none on an L4 device); run-1
F2's required fix, both halves; §12 HARD list.

§2's exit specification is good, but nothing verifies it. The three clauses most likely to invert in
code are exactly the three with no check attached: the **adverse-precedence** rule inside one M1 bar
(an optimistic implementation manufactures the high-`p` / high-`W/L` signature P-22 documents as an
artifact), the **once-per-M1-bar-on-close** trail ratchet (an intra-bar ratchet is a materially
better device and reads as an effect), and the **time-exit open** convention. TRIPWIRE-2 as written
does not reach them.

**Required fix (quant-designer).** Extend TRIPWIRE-2 to re-resolve **exits** on decision-clock OHLC
as well (or add TRIPWIRE-3), and add **G7** on one L4 target+trail cell where both levels lie inside
a single M1 bar, with QA computing the adverse fill independently. Both HARD.

#### R2-07 — MEDIUM — after C7, "powered subset" is an undefined term, and the L-51 selection check that governance makes mandatory now has no anchor

**Fails:** `chapter-06-governance.md:98` (binding on any 019/020 design: *"no powered subset's
magnitudes may be read without the three-number selection check (**L-51**)"*); P-22; reflection §5.9
L3 row ("the selection check is **mandatory**, not optional"); design §4.1 L3 row and §15, both of
which say "every **powered** subset"; design §9 ("The `[P]`/`[U]` adequacy classes are **RETIRED**");
design §12 (no L-51 row, not in HARD).

Run-1's F6 flagged the scope and HARD-ness. AMENDMENT-6 made it worse rather than better: the two
places the check is still attached (§4.1, §15) both key it to "powered subset", and §9 has abolished
the concept. As written the check can be argued to apply to nothing.

C7 does remove one genuine L-51 trigger — there is no longer a precision filter selecting cells, so
the SPDR-018B dispersion-gate mechanism does not arise. That is a real benefit and worth recording.
But **L1's ŝ-decile cuts, L2's state cells and L3's swing gate are still selections on a fat-tailed
P&L distribution**, which is L-51's actual subject.

**Required fix (quant-designer).** Re-anchor: "the L-51 three-number check runs on **every selected
subset at every layer (L1, L2, L3, L5)** against its own complement", move it into §12, and place it
in the **HARD** list — or state explicitly why a missing selection check is INFORMATIVE here.

#### R2-08 — MEDIUM — §13 still describes `deltaThreshold` as calibrated, contradicting §2's freeze

**Fails:** §13 bullet 6 vs §2 ("There is no calibration step, no selection of a 'best' δ") and §10's
freeze row. Run-1 F3's required fix landed everywhere except the clause run-1 quoted.

**Required fix.** Replace §13's bullet with: "no tuning of any entry parameter to improve `p`;
`deltaThreshold` is frozen at `{0.25, 0.5, 1.0}` with all three reported and none selected (§2)".

#### R2-09 — MEDIUM — C6's `NOT_RESOLVABLE` booking and C7's prohibition on it are in direct conflict, and the design silently drops C6's obligation

**Fails:** AMENDMENT-C6 as registered (*"a grid that cannot resolve the interaction is booked
`NOT_RESOLVABLE` rather than run and explained"*) and reflection §5.9.1 Power row; AMENDMENT-C7
(*"no `powered` / `unpowered` / `at_target` / `NOT_RESOLVABLE` flag is emitted anywhere"*); design
§12 "No adequacy flag" (asserts the C7 side, HARD) and §4.3 (silent on the C6 side).

Both are operator-mandated and both are dated 2026-07-28. C7 is the later and more specific, so it
plausibly supersedes — but the design must say so rather than assert one and drop the other, and
§4.3 must state what replaces C6's protection against running an unresolvable phase-(b) grid.

**Required fix.** Add a §14 row reconciling C6 and C7 explicitly, and give §4.3 a resolution
statement for the (b) grid that carries C6's intent without the retired flag (e.g. "the (b)
amendment states each cell's expected ladder rung before the run; a grid whose cells all sit above
the 0.10 rung is reported as such and the operator decides").

---

### PART C — is the B-5 argument sound?

**Short answer: the critique is sound, the "strengthened" claim is not, and the current text does
not deliver B-5's protection. It delivers more information and less enforcement.**

**What the design gets right, and I want it on the record.** Retiring the 0.07 adequacy cutoff and
the ±0.03 bands is correct. Both were anchored on `sd(log R) = 0.0729` and `median log R = −0.0301`
— dispersion and location of the *observed* residual, which are not statements about what effect
size matters. The ladder is strictly more information than a boolean. And the specific mechanism the
design names is real: an effect quoted without its precision is a documented failure mode, and
binding them to one row addresses it. Run-1's F5 (bands did not partition) is **fully closed** as a
by-product — `ci_low > 0` / spans 0 / `ci_high < 0` is exhaustive and mutually exclusive.

**Where the argument fails.** B-5 is a rule about **reading**, not about **emission**. `UNPOWERED`
was not protective because it was hard to drop; it was protective because it was **categorical, and
therefore countable and separable**. It let a reader say "these 40 cells are not evidence of
anything" as a set. The replacement collapses two categorically different states — *resolved and
null* and *unresolved* — into the single band `COVERS THE MIRROR`. §9's answer is that a wide-CI cell
and a genuinely-null cell will be "visibly different" because the width and MDE sit alongside. That
is a presentation hope, not a constraint. Three specific gaps follow:

1. **Nothing forbids aggregation.** A summary reading "38 of 60 cells covered the mirror" is a
   negative by aggregation, is fully compliant with §9 as written, and is *easier* to produce now
   than under a boolean, because there is no longer a category to exclude first.
2. **The "cannot be quoted without its precision" claim is asserted, not enforced.** §12 has a HARD
   check for the **absence** of the old flag and **no** check for the **presence** of the new
   binding. Nothing requires `ci_width` and `block_mde` to travel with `log R` into
   `results/layer_deltas.parquet`, `screen.md`, or `analysis.md`. The one protective property the
   design claims over the boolean is the one property it does not machine-enforce.
3. **The forecast was deleted along with the label.** `design-requirements.md` §6's real content is
   *predeclaration* — saying **before the run** which strata will not resolve, so a thin stratum
   cannot be reinterpreted afterwards. That is orthogonal to labelling: you can predeclare expected
   per-stratum resolution without any adequacy verdict. §8's EXPECTED RESOLUTION block gives
   baseline pooled figures only; it says nothing about L1's `d≥9` decile cut, L2's shock/level cells
   or L3's swing gate — the strata that carry HYP-D6's entire content and that run-1's F1(ii)
   specifically required. Those strata cut `n` by roughly 10× (§8 says so itself, in one clause,
   with no table), landing them several rungs coarser. **Run-1's F1(ii) was removed, not answered.**

**What would fix it** — none of these reintroduces a threshold, and all are consistent with C7:

- **(a)** A **HARD** §12 check: no artifact may emit a `log R` or `Δlog R` value without
  `ci_low`, `ci_high`, `ci_width` and `block_mde` on the same row. Extend the schema rule to
  `layer_deltas.parquet`, `screen.md` and `analysis.md` tables. This converts the design's central
  claim from an assertion into an invariant.
- **(b)** Emit a **descriptive** resolution field per cell — `finest_rung_detected` = the smallest
  ladder rung whose detection rate ≥ 0.8, or `none`. It admits, excludes, labels and ranks nothing
  (C7 satisfied), but it restores the **categorical separability** B-5's reader-protection actually
  needs, straight off the ladder the design already computes.
- **(c)** Restore §6's predeclaration as a **per-stratum expected-resolution table** — expected `n`
  and expected finest rung for L1 (`d≥5 / d≥7 / d≥9` / continuous), L2's three cells, L3's gate,
  L4's devices and per-symbol — with **no adequacy verdict attached**. This is F1(ii), and it costs
  one table.
- **(d)** A §13 refusal: **no summary may count or aggregate cells by band label without carrying
  the resolution distribution of the cells counted.**

With (a)–(d) the design's claim would be true. Without them, "strengthened" overstates it: what
exists today is a richer emission with weaker guardrails.

---

### Run-1 findings not touched (carry-forward)

| Run-1 | Status in run 2 | Note |
|---|---|---|
| **F4** — L4 modulation narrowed to ŝ only vs reflection §5.9 ("modulated **by each volatility layer**"); §10's count `1+4+5+3+44+4` = **61** against a stated cap of **≤ 60**; §4.2 yields **~20** L4 cells, not ~44 | **OPEN, and now worse** | Arithmetic re-checked: §4.2 gives target 3+3, trail 2+2, hold 4+4, sizing 1+1 = **20**. §10 now also multiplies "≤ 60 cells" by "× 2 clocks × 3 δ" = **366**, so the cap sentence contradicts itself twice. §4.1 says L3 = "2 (+ co-report)"; §10 counts 3. No §14 row for the §5.9 narrowing. **R2-10, MEDIUM** |
| **F5** — bands did not partition | **CLOSED** | The CI-relative bands are exhaustive and mutually exclusive |
| **F6** — L-51 not HARD, scoped to L3 | **OPEN, and worse after C7** | Promoted to **R2-07** |
| **F7** — `activeHold = 20` expands the checkpoint's frozen `h ∈ {4,12,24}` with no amendment row | **OPEN** | Reflection §5.5 authorises the `E[run]` bound, so the substance is fine; §14 still has no row. **R2-12, LOW.** Compounded by R2-03(3) on M15 |
| **F8** — implied-episode column uses base ~3,499, not 3,427 | **OPEN, unchanged** | Recomputed: **10,547 / 20,671 / 57,420** vs the design's 10,800 / 21,200 / 58,800 (+2.3%). Direction conservative. **R2-11, LOW** |
| **F9** — cadence 1–5% contradicted by measurement | **CLOSED** | §1 now says "MEASURED and EMITTED per delta level, never assumed"; §8 says "near 10%" and names the earlier figure as wrong |
| **F10** — C5 labelled `NARROWING`; C3 citation dangling | **OPEN, unchanged** | §624 still `NARROWING` (not one of LOOSER/TIGHTER/NEUTRAL); §10 still cites "AMENDMENT-C3 precedent" while §14's in-force list omits C3. **R2-14, LOW** |
| **F11** — 4 of 5 reflection §5.6 predictions uncarried | **OPEN** | Non-binding. **INFO** |
| **F12** — P-02 / P-04 unnamed in §13 | **OPEN** | Non-binding; still worth one line. **INFO** |

---

### Additional run-2 findings

#### R2-10 — MEDIUM — §10's cell-count row is internally contradictory in three ways
See the F4 row above. **Required fix:** reconcile §4.1, §4.2 and §10 on one number; state whether
the cap is per-clock-per-δ or total; add the §5.9 L4-narrowing amendment row with a direction label.

#### R2-11 — LOW — §8's implied-episode column does not follow from its own stated base `n`
Conservative direction, but §8 is the design's only resolution forecast. **Fix:** 10,547 / 20,671 /
57,420, or state the base actually used.

#### R2-12 — LOW — `activeHold = 20` still carries no amendment row
**Fix:** one §14 row, `DIRECTION: LOOSER`, citing reflection §5.5's `E[run]` bound.

#### R2-13 — LOW — no M-4 effective-coverage assertion reached §12
§8 now uses effective coverage correctly, but §12 has only M-2 span disclosure. Governance:105 makes
M-4 binding. **Fix:** add an assertion that the pooled bar count used in any resolution statement is
the measured `unit_pin.json` value, not a date-range product.

#### R2-14 — LOW — amendment-ledger labelling, unchanged from F10
**Fix:** C5 → `TIGHTER`; note C3's registry location (`multiplicity-registry.md`) in §14.

#### R2-15 — LOW — §8's resolution constant is derived from SPDR-018's *powered* subset, which is the L-53/P-25 shape; I checked it and the conclusion is invariant
**Fails (in form):** P-25 / L-53 (*"Derive on the full emitted population, or on a subset defined
without reference to the outcome; **report the range across every defensible basis** and state which
conclusions are invariant to it"*); §8 ("1,413 powered cells", median `(1−p)·L` and median block MDE
both taken on that subset).

There is a mild irony here: the design retires powering for the L-50 reason while still importing
SPDR-018's powered-subset-derived numbers as its resolution anchor. I recomputed across bases:

| Basis | cells | median `(1−p)·L` | median block MDE | median `Δlog R` | median `c = Δlog R·√n` |
|---|---:|---:|---:|---:|---:|
| powered (design's) | 1,413 | 48.54 | 6.51 | 0.1228 | **7.28** |
| all emitted cells | 23,527 | 147.97 | 87.02 | 0.5517 | **6.60** |
| not-powered | 22,114 | 154.90 | 96.26 | 0.5869 | **6.60** |

The *level* figures differ 4.5×, but the **scaling constant the design actually uses** is stable
(7.28 vs 6.60, IQRs overlapping). Every §8 conclusion is invariant to the basis, and the design's
choice is the conservative one. **Fix is one sentence** stating the range and the invariance, per
P-25's own remedy.

---

### Checks re-verified clean in run 2

| Check | Result |
|---|---|
| **Exact-mirror target, slope 1** | **CLEAN, unchanged.** `log R = log(W/L) − log((1−p)/p)` in §1, §5, §9, §12, G4, G5. **0.9408 appears exactly once (§5:229) and only to be refused**, with the correct reason (residual centred at zero by construction). §12 makes a fitted-slope residual anywhere a **hard failure**; §13 refuses it again; G5 exists solely to make audit A1 non-repeatable. Matches reflection §5.4 verbatim in substance |
| **AMENDMENT-C5 cost isolation** | **CLEAN, and now stronger.** Traced every cost mention: header NOTE, §5 `DISCLOSED REFERENCE ONLY`, §7 ("no read in this design is compared against it"), §12 HARD cost-isolation check with `p_be_net` flagged `DISCLOSURE_ONLY`, §13, §15 column flag. C7 *improves* this — the bands now carry **no magnitude at all**, so there is even less surface for a cost term to enter |
| §8 population and precision figures | **All reproduce** from `unit_pin.json` and `analyst_per_cell_magnitudes.parquet` except the implied-episode column (R2-11). See the Part A table |
| L-28 derangements | **CLEAN.** Both permutation controls declare `DERANGEMENT (zero fixed points)`; §12 asserts a measured fixed-point count of 0; TRIPWIRE-1 correctly declares `N/A` (index shift) |
| L-52 / P-23 check integrity | **CLEAN.** Expected HARD-check **count** asserted and reconciled **by name**; every check depends on an emitted artifact; determinism unconditional at `--jobs > 1` independent of `--resume`; no required check in a manual post-step |
| P-24 comparator disclosure | **CLEAN.** M-3 block mandates the comparator's own mean, null quantiles **and** plant curve with every percentile; a bare percentile is refused |
| L-50 / P-21 threshold portability | **CLEAN, improved by C7.** All remaining numbers are dimensionless log units; after C7 no magnitude threshold exists at all. cTrader excluded from phase (a) under C1 |
| L-21 / P-15 unit pin (numerator) | **CLEAN** for the pin itself — object 2's wording matches `SPDR-018/results/unit_pin.json.divisor_object`; measured values computed at run. **But see R2-03** for the ATR↔ŝ and H1↔M15 seams the pin does not bridge |
| Interpretation bands partition | **CLEAN** (closes run-1 F5) |
| B-9 / object identity | **CLEAN.** One open episode per symbol, suppression counted, block ≥ holding horizon (subject to R2-05 on the M15 block unit) |
| Holdout / XENA / family action / TEST | **CLEAN.** §10 holdout never queried; §12 assertion; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| SPREAD-COST-DISCLOSURE | **CLEAN.** All five fields verbatim, unchanged |
| `check_no_local_accounting` | **DEFERRED** to post-implementation QA; §12 declares the check |
| Start gate | **STILL FLAGGED.** `reflection-inputs.md` §9 operator decision remains **unsigned**. Design registration does not require it; **execution does** |

---

### Verdict and routing

**REVISE.** Everything found routes to **`quant-designer`**; no code exists.

Implementation-blocking: **R2-01** (contradicts a registered in-force amendment; also invalidates
the §14 direction count), **R2-02** (the primary clock is chosen against the family's own M15
direction evidence), **R2-03** (the L4 comparator confounds level with information, and the M15
`√h` seam is the EXP-025 shape). **R2-04** and **R2-06** are blocking in the weaker sense that the
ladder and the exit rules are unverifiable as written.

**Nothing rises to REJECT.** No holdout contact, no causality violation, no missing tripwire, no
cost smuggling, no fitted-slope target, no unapproved silent deviation. The exact mirror and the
cost quarantine are intact and remain the strongest parts of the document.

---

## QA run 3 — 2026-07-28T19:26:49Z — mode: subagent — HEAD 42934ef91adb15a4aac2625b323021abf9ad94e5 (clean tree)

**Target:** `python/experiments/SPDR-019/design.md` (793 lines; 644 at run 2, 525 at run 1)
**Stage:** DESIGN-STAGE. `screen_code/` does not exist; that is expected and is **not** a finding.
**Independence:** this reviewer authored neither the design nor runs 1–2. Every number below was
re-derived from the cited artifacts with my own code. Where run 2's arithmetic and mine disagree,
I say so and show both.

**Verdict: REVISE.** Not yet fit to authorise implementation — but the gap is short and mostly
textual. Two clauses must be written before code (F3-02 block length, F3-06 M15 hold grid); the
rest is prose arithmetic and ledger hygiene.

Findings: **2 HIGH · 5 MEDIUM · 5 LOW.**

---

### PART A — closure of the run-2 findings, verified against the artifacts

Re-derived from `SPDR-018/results/analyst_per_cell_magnitudes.parquet` (24,098 rows; 23,700 with a
finite `gross_block_mde_mean_bps` and `gross_n > 0`) and `SPDR-018/results/unit_pin.json`:

| §8 claim | Design | Re-derived | Verdict |
|---|---|---|---|
| powered subset size | 1,413 | `at_parent_target_precision == True` → **1,413** | REPRODUCES |
| `k` on the powered subset | 370 | median `MDE·√n` = **370.33** | REPRODUCES |
| full population size | 23,700 | **23,700** | REPRODUCES |
| `k` on the full population | 948 | median **947.9** | REPRODUCES |
| `k` by horizon | 569 / 955 / 1,384 | h=4 **568.98** · h=12 **955.18** · h=24 **1,383.68** | REPRODUCES |
| arm-C cell count | 18,632 | **18,632** | REPRODUCES |
| pooled H1 TRAIN bars | 229,646 | `pooled_n` = `sum(per_symbol.n)` = **229,646** | REPRODUCES |
| only MATICUSDT spans the window | 21,582 | **21,582**, the max | REPRODUCES |
| median symbol / smallest | 12,444 / 555 | **12,444** / **555** (`1000RATSUSDT`) | REPRODUCES |
| required-`n` table (16 cells) | see §8 | reproduces **exactly** from `(k/(Δ·48.5))²` | ARITHMETIC OK, **BASIS WRONG — F3-01** |
| largest pooled cells realise 0.08–0.16 | 0.08–0.16 | **0.073–0.094** at n≈21k; **0.053–0.107** for all cells n≥10k | **DOES NOT REPRODUCE — F3-10** |
| 0 of 18,632 arm-C cells reach 0.03 | 0 | **3** reach it (min 0.0101) — all degenerate `n = 2`, `p = 0` | SUBSTANTIALLY TRUE, MISSTATED — F3-10 |

`k` is now on the right basis and split by horizon exactly as claimed. **AMENDMENT-8's headline
correction is real and verified.** Run-2 closure status, item by item:

| Run 2 | Status in run 3 | Evidence |
|---|---|---|
| **R2-01** phase-(b) trigger vs registered C6 | **DISCLOSED, NOT RESOLVED** | §14 AMENDMENT-7 added with `DIRECTION: LOOSER` and an explicit `DISCLOSED CONFLICT` paragraph — the ledger half of run 2's fix (b) is done. The family half is not: `cf-voldir-001.md` still carries C6 verbatim ("the (b) trigger is **pre-declared before (a) runs**") and there is no C8. **F3-09** |
| **R2-02** M15 chosen against the family's own direction evidence | **CLOSED** | §8.1 cites both SPDR-013 results and I verified both verbatim: `SPDR-013/analysis.md:177` "IC 0.34–0.46; ridge ≥ AR1; M15 > H1; all 25 symbols"; `:164` "H1 DESIGN 0.57 / CONFIRM 0.48; **M15 0.20–0.28** (worse than shuffled). +20 bps bite plant detected". AMENDMENT-9 switches the M15 primary read to Δ`log R` vs L0 and labels absolute `log R` an ENTRY statement — this is run-2 fix (iii) implemented |
| **R2-03** L4 comparator unit seam | **CLOSED on units and clock, OPEN on holds** | §4.2's UNMODULATED arm is now `a × s_hat_uncond` = the TRAIN-median of the **same** Parkinson estimator per symbol. Same unit, same estimator, same clock; the ATR↔Parkinson 1.5–1.7× level shift is gone and ATR20 is confined to the `deltaThreshold` normaliser. The `√h`-in-hours clause closes the 2× bar-vs-hour ambiguity explicitly. Seam 3 (holds) survives — **F3-06** |
| **R2-04** ladder plant operator unstated | **CLOSED** | §8 names PRIMARY (`W/L` × `exp(δ)`, `p` fixed) and CO-REPORT (`p` at fixed `W/L`), both emitted per rung, neither privileged; §12 asserts both |
| **R2-05** M15 block dependence is calendar-based | **DISCLOSED, NOT FIXED** | §8.1 adds the paragraph; the estimator is unchanged. **F3-02** |
| **R2-06** exit tripwire + golden trace | **CLOSED** | TRIPWIRE-2 now names "entry stops AND the L4 exits (target, trail, time)" and adds a favourable-precedence twin that must read better; G7 covers same-M1-bar target/trail precedence, the M1-close-only ratchet and the time-exit open. Both HARD |
| **R2-07** L-51 anchor after C7 | **HALF CLOSED** | §15 redefines the anchor well ("every subset the design or analysis reports separately"). But §4.1's L3 row still reads "on every **powered** subset", and L-51 still has **no §12 row and is not in the HARD list** — the second half of run 2's fix. **F3-04** |
| **R2-08** §13 still calls `deltaThreshold` calibrated | **NOT CLOSED — verbatim unchanged** | design.md:690–691 |
| **R2-09** C6's `NOT_RESOLVABLE` booking vs C7's prohibition | **NOT CLOSED** | No §14 row reconciles them; §4.3 still has no resolution statement for the (b) grid. **F3-08** |
| **R2-10** §10 cell count contradictory three ways | **NOT CLOSED** | **F3-05** |
| **R2-11** implied-episode column | **CLOSED BY WITHDRAWAL** | §8 names the old figures and withdraws them |
| **R2-12** `activeHold = 20` has no ledger row | **NOT CLOSED** | **F3-11** |
| **R2-13** no M-4 assertion in §12 | **NOT CLOSED** | **F3-11** |
| **R2-14** `C5 (NARROWING)`; dangling C3 citation | **NOT CLOSED** | §14:773 and §10:592. Note in the design's defence: `NARROWING` is transcribed from the family ledger's own label (`cf-voldir-001.md:420`), so this is a transcription, not an invention. **F3-11** |
| **R2-15** resolution constant from a precision-selected subset | **HALF CLOSED, AND THE HALF LEFT OPEN IS THE LOAD-BEARING ONE** | **F3-01** |

---

### PART B — defects in the run-2 changes

#### F3-01 — HIGH — §8 pairs a full-population `k` with a powered-subset `(1−p)·L`, so the entire required-`n` table and every predeclared resolution figure is ~6.9× too pessimistic; this is the same P-25 / L-53 defect AMENDMENT-8 says it closed

**Fails:** §8 ("using the **FULL population**, not the powered subset"); §8's `(1−p)·L = 48.5 bps`;
§8's EXPECTED RESOLUTION table; P-25 / L-53 (*"Derive on the full emitted population, or on a subset
defined without reference to the outcome; **report the range across every defensible basis** and
state which conclusions are invariant to it"*); AMENDMENT-8's own stated purpose.

The numerator was fixed. The denominator was not, and nothing in §8 says so. Measured:

| `(1−p)·L` basis | value | source |
|---|---:|---|
| powered subset (1,413 cells) — **what §8 uses** | **48.54 bps** | median on `at_parent_target_precision == True` |
| full emitted population (23,700) | **147.97 bps** | median |
| arm C by horizon | **90.81** (h=4) · **146.44** (h=12) · **212.57** (h=24) | median |

Cells enter the powered subset because their MDE is small — the design says this itself, in the same
block, as the reason to reject `k = 370`. `(1−p)·L` is drawn from that identical selection, and it is
also **horizon-dependent by a factor of 2.3**, the same objection §8 raises to a single `k`.

**The design's own direct check refutes its table, and I verified this per cell rather than by
argument.** For every arm-C cell with `n ≥ 5,000` (427 cells) I computed the MDE in log units the
design's formula predicts, `k_h / (√n · 48.5)`, against the MDE the artifact actually realises,
`block_mde_bps / ((1−p)·L)` on that cell's own terms:

| | median ratio predicted ÷ realised |
|---|---:|
| using `(1−p)·L = 48.5` (the design) | **2.62×** |
| using each cell's own `(1−p)·L` | **1.07×** |

At the three largest arm-C pooled cells (`n` = 20,977 / 20,572 / 20,279) the design's arithmetic
predicts 0.136 log units at h=12; the artifact realises **0.077**. The formula is right; the
denominator is not. Squared, this inflates every required-`n` figure in §8 by roughly **6.9×**.

*(Recorded so it is not re-derived a fourth time: run 2's SPDR-020 review computed the same cells at
0.137–0.157 for h=12. That figure applies arm C's h≈4 constant 66.4 across all three horizons.
`(1−p)·L` rises 90.8 → 146.4 → 212.6 with `h`, so a constant denominator across horizons is the same
class of error as a constant `k` across horizons. Per-cell, those cells realise 0.073–0.094.)*

Direction is conservative, so this creates no over-claim. It matters anyway, and more than it would
have before C7: with the adequacy label retired, the **predeclared resolution table is the B-5
protection** (see Part C). A table 2.6× pessimistic tells the reader to expect coarse resolution from
strata that will in fact resolve two rungs finer — which converts a genuinely well-measured null into
"we could not have seen it". That is the mirror image of the error B-5 exists to prevent, and the
retired label used to make it impossible.

**Required fix (quant-designer).** Recompute the table with numerator and denominator on the **same**
basis, per horizon. Then apply P-25's own remedy, which is already binding: print the required-`n`
range across every defensible basis (48.5 / per-horizon arm-C / 147.97) and state explicitly which
conclusions are invariant. They are not invariant here — at `(1−p)·L = 148` the 0.05 rung at h=12
needs ~16,700 episodes, which the design's own strata reach; at 48.5 it needs ~155,100, which they do
not. That is precisely the disclosure P-25 requires and precisely the conclusion §8 currently hides.

#### F3-02 — HIGH — the block-bootstrap block is still stated in **bars** while the primary clock is now M15, so the primary read's CI is anti-conservative — and the CI is the entire band definition after C7

**Fails:** §1 DERIVED `test` ("block >= holding horizon"); §6 MIRROR-NULL ("block >= holding
horizon"); §9 BANDS (`ci_low > 0` / spans 0 / `ci_high < 0` — the CI *is* the band); §10 Clocks row
(M15 primary); `docs/references/spdr-lane.md:32,35` dependence-matched uncertainty and its Phase-010
precedent (block=5 on H=48 overlapping windows understated uncertainty 2–3× and manufactured a thread
that did not exist); run-2 R2-05's required fix.

§8.1's new paragraph states the problem correctly — "four M15 bars inside one hour are close to one
observation for block purposes" — and then leaves the rule that causes it unchanged. A block of `h`
M15 bars at `h = 12` spans **3 hours**; the same block on H1 spans 12 hours; the clustering the L2
state axes and ŝ condition on is calendar-persistent at the 19–23 hour scale the design cites for
`E[run]`. Under-blocked bootstrap resampling **understates** variance, which narrows CIs, which
produces `ci_low > 0` — `ABOVE THE MIRROR`, the design's one positive finding — more often than the
data warrant, on the clock carrying the primary read.

§8.1's answer, that "the realised block MDE is emitted per cell and is the only figure that counts",
does not reach this: the realised block MDE is computed *by* the under-blocked estimator, so it
inherits the same bias. The disclosure describes a defect it does not remove.

This is the one finding that must be written before code, because it is a specification of the
estimator, not of the prose.

**Required fix (quant-designer).** State the block length in **calendar time**, matched across
clocks — run 2's formulation, `block ≥ max(holding horizon, 20 H1-equivalents)`, is adequate — and
emit the realised **effective sample size** per cell alongside `n`, so the M15 gain is measured
rather than assumed. Add the calendar-block rule to §12's asserted list. Restate AMENDMENT-2's lever
as "~4× raw episodes; effective gain smaller and measured at run", which is what §8.1 already
concedes in prose.

#### F3-03 — MEDIUM — §13 still describes `deltaThreshold` as calibrated, contradicting §2's freeze; unchanged from run 2, which was unchanged from run 1

**Fails:** §13 bullet 6 (design.md:690–691) vs §2 ("There is no calibration step, no selection of a
'best' δ, and no tuning against any outcome") and §10's freeze row.

This is the third run in which the *same two lines* are quoted. The surviving sentence is the one
that describes the defect: "`deltaThreshold` is **calibrated for sample size** … and **its
calibration is emitted** so QA can verify which was optimised." There is no calibration to emit.

**Required fix.** Replace with: "no tuning of any entry parameter to improve `p`; `deltaThreshold` is
frozen at `{0.25, 0.5, 1.0}` with all three reported and none selected (§2), and the realised signal
rate at each level is emitted."

#### F3-04 — MEDIUM — L-51 is governance-binding, is still keyed in §4.1 to a population C7 abolished, and still has no §12 row and no HARD status

**Fails:** `docs/references/chapter-06-governance.md:98` (binding on any 019/020 design: *"no powered
subset's magnitudes may be read without the three-number selection check (**L-51**)"*); design §4.1
L3 row ("on every **powered** subset"); §12 (no L-51 row); §12 HARD list (L-51 absent); P-22; run-2
R2-07's required fix, second half.

§15's re-anchoring is good and I want it recorded as such — running the check on every separately
reported subset, including cells above vs below median `mde50`, is a better answer than the retired
one. But §4.1 still points the check at "every powered subset", and §9 has abolished that concept, so
the two clauses that invoke L-51 disagree about its population. And the check that governance calls
mandatory sits in neither §12 nor the HARD list, which means nothing asserts it ran.

**Required fix.** Align §4.1's L3 row with §15's anchor; add an L-51 row to §12; place it in the
**HARD** list — or state explicitly, in §12, why a missing selection check is INFORMATIVE on a design
whose L1/L2/L3 layers are all selections on a fat-tailed payoff distribution.

#### F3-05 — MEDIUM — §10's cell-count row contradicts §4.2, contradicts itself, and breaches its own cap

**Fails:** §10 Cell count row; §4.1 L3 and L4 rows; §4.2's device grid; `spdr-lane.md:35` (multiplicity
disclosure is a lane requirement, and this design is on record as "disclosed, not rationed");
run-2 R2-10, unchanged.

Three arithmetic problems, all still present:
1. `1 + 4 + 5 + 3 + 44 + 4 = 61`, stated as "**≤ 60 cells**".
2. §4.2's grid yields target 3+3, trail 2+2, hold 4+4, sizing 1+1 = **20** L4 cells, not ~44.
3. The row then multiplies "≤ 60 cells" by "× 2 clocks × 3 δ" = **366**, so the cap contradicts
   itself in the same sentence.
Separately §4.1 gives L3 as "2 (+ co-report)" while §10 counts 3.

**Required fix.** Reconcile §4.1, §4.2 and §10 on one number; state whether the cap is per-clock-per-δ
or total; add the §14 row for the reflection §5.9 L4 narrowing (modulation by ŝ only, rather than by
each volatility layer) with a direction label.

#### F3-06 — MEDIUM — on the M15 primary clock the unmodulated hold sweep does not reach the regime scale the design says bounds it

**Fails:** §4.2 ("Hold values are bounded by the **measured** regime run-length scale (`E[run]`
18.9–23.1 H1 bars … so it sets a *scale*) … **Nothing outside that scale is swept**"); §4.2's
`activeHold ∈ {1, 4, 12, 20}` periods; §4.2's own conversion clause ("`E[run]` is measured in H1 bars;
on M15 it is converted to hours first, never applied as a bar count"); run-2 R2-03(3).

The conversion clause is right and is a genuine fix — but it is applied to the *modulated* arm only.
The unmodulated arm's grid is still stated in **periods**. On M15, `{1, 4, 12, 20}` periods is
**0.25 to 5 hours**; `E[run]` is **19–23 hours**. The entire M15 hold sweep therefore sits below the
stated scale rather than spanning it, and the longest M15 hold is roughly a quarter of the shortest
H1 hold the same grid produces. Since the primary read is on M15, the hold device is being measured
outside the range the design says makes it meaningful.

**Required fix.** State `activeHold` in **hours** (or as an explicit per-clock bar count derived from
hours) so the sweep spans the same calendar scale on both clocks, and say what the M15 grid is.

#### F3-07 — MEDIUM — pooled-across-symbol is declared the PRIMARY read by construction, which inverts a binding lane default, with no predeclared consequence if homogeneity does not support it

**Fails:** `docs/references/spdr-lane.md:35` (*"Per-stratum reporting; multiplicity disclosed (L-03).
**A pooled figure is disclosure-only**"*) and `:93` (*"a pooled line is disclosure-only (L-03)"*);
design §8 ("the primary reads live on M15, full TRAIN, **pooled across symbols**"); §9 POOLED block
("pooled-across-symbol figures are the PRIMARY read **by construction**").

Not raised in runs 1 or 2 on this design; raised as M15 on SPDR-020, where it is equally unclosed.
The lane rule is binding and the design overrides it a priori. The mitigation offered — emitting I²
so "pooling is justified rather than assumed" — is the right instrument but is not connected to any
consequence: I² is emitted, and nothing follows from any value of it.

**Required fix, and it needs no threshold.** State that the pooled line **reverts to
disclosure-only, per the lane default, if the emitted homogeneity statistic does not support
pooling**, with the operator judging on the emitted value. That preserves INFR-016 (no machine drop,
no cutoff) and restores the lane default as the fallback rather than discarding it.

#### F3-08 — LOW — C6's `NOT_RESOLVABLE` booking and C7's prohibition are still unreconciled, and §4.3 still carries no replacement for C6's protection

**Fails:** AMENDMENT-C6 as registered (*"a grid that cannot resolve the interaction is booked
`NOT_RESOLVABLE` rather than run and explained"*, `cf-voldir-001.md`); AMENDMENT-C7 (*"no `powered` /
`unpowered` / `at_target` / `NOT_RESOLVABLE` flag is emitted anywhere"*); design §12 (asserts the C7
side, HARD) and §4.3 (silent on the C6 side); run-2 R2-09, unchanged.

C7 is later and more specific, so it plausibly supersedes; the design must **say** so rather than
assert one obligation and drop the other silently. **Fix:** one §14 row reconciling them, plus a
resolution statement in §4.3 that carries C6's intent without the retired flag — e.g. the (b)
amendment states each cell's expected ladder rung before the run, and a grid whose cells all sit
above the 0.10 rung is reported as such for the operator to judge.

#### F3-09 — LOW as a design defect, HIGH at the execution gate — AMENDMENT-7 discloses its conflict with registered C6 but does not resolve it, and a design cannot amend the family contract by disclosing that it disagrees with it

**Fails:** `cf-voldir-001.md` AMENDMENT-C6, still in force verbatim and listed by §14 as binding on
this design; `_pipeline-config.md` / the pipeline's binding separation (*"Registry updates during an
experiment: append evidence/disposition rows only — never a status transition"*; family changes are
operator-signed at a checkpoint).

I checked the registry directly: C6 is unchanged and there is no C8. The disclosure is a real
improvement over run 2's silence, the ledger row is correctly labelled LOOSER, and the design's
substantive argument is right on the part it claims — the protection C6 lists under *Scope* (phase
(a) may not shrink phase (b)) survives intact in §4.3, with the cross fixed, flat layers retained and
the interaction estimand unchanged. What C6's *trigger* clause protects — optional stopping on a
shared sample — is genuinely given up, and the design says so.

This does not block writing `screen_code/`: phase (b) is not authorised by this document and the
trigger governs nothing the implementation does. It **does** block execution until resolved.

**Required fix (operator).** Either an operator-signed AMENDMENT-C8 on the family contract amending
C6's trigger clause, or restore a condition stated before (a) runs that is not a value bar. Route to
the operator at the execution gate, not to `quant-designer`.

#### F3-10 — LOW — §8's two "direct check" figures do not reproduce from the artifact they cite, and §8 is the section that insists on computed-not-asserted

**Fails:** §8 ("Derived from SPDR-018's emitted cells, **computed not asserted**"); §8's "largest
pooled cells (n ≈ 21k) realise **0.08–0.16 log units**" and "**0 of 18,632** arm-C cells reach 0.03".

Measured, converting each cell's block MDE to log units on that cell's own `(1−p)·L`:

| Claim | Design | Measured |
|---|---|---|
| largest pooled cells, n≈21k | 0.08–0.16 | **0.073–0.094** (the three `n` = 20,977 / 20,572 / 20,279 cells, all three horizons) |
| all arm-C pooled cells, n ≥ 10k | — | **0.053–0.107** |
| arm-C cells reaching 0.03 | 0 of 18,632 | **3** of 18,632 (min 0.0101) |

The three exceptions are `n = 2`, `p = 0` degenerate cells, so the claim's *substance* holds and the
sentence it supports — that "approaching 0.03" is refuted by the parent's own emission — stands. But
0.08–0.16 is an inherited number, not a computed one (it traces to the constant-denominator
computation noted under F3-01), and it is 1.5× coarser than the artifact at the low end.

**Fix.** Restate as "0.053–0.107 log units across arm-C pooled cells with `n ≥ 10k`; 0.073–0.094 at
`n ≈ 21k`", and "0 of 18,632 arm-C cells reach 0.03 other than three degenerate `n = 2` cells".

#### F3-11 — LOW — four run-2 ledger and checklist items, all unchanged

| Item | Where | Fix |
|---|---|---|
| `activeHold = 20` expands the checkpoint's frozen `h ∈ {4,12,24}` with no ledger row (R2-12) | §4.2, §14 | one §14 row, `DIRECTION: LOOSER`, citing reflection §5.5's `E[run]` bound |
| No M-4 effective-coverage assertion in §12 (R2-13); governance:105 makes it binding | §12 | assert that any pooled bar count used in a resolution statement is the measured `unit_pin.json` value, never a date-range product |
| `C5 (NARROWING)` is not one of LOOSER / TIGHTER / NEUTRAL (R2-14) | §14:773 | transcribed from `cf-voldir-001.md:420`, so annotate rather than relabel: "NARROWING (family ledger's own label; TIGHTER in L-23 terms)" |
| §10 cites "AMENDMENT-C3 precedent" while §14's in-force list omits C3 (R2-14) | §10:592 | name C3's registry location or drop the citation |

Also noted, and not counted as a separate finding: **AMENDMENT-C7 is absent from §14's closing
in-force list** (U1, S1, C1, C2, C5, C6), although C7 is registered at `cf-voldir-001.md:448` and is
the authority for §8, §9 and AMENDMENT-6. Add it.

---

### PART C — does the current text deliver B-5's protection?

**Independent judgement: the run-2 remedies are architecturally sound and do not merely relocate the
problem. What survives is an arithmetic failure, not a structural one — and after C7 that arithmetic
is load-bearing in a way it was not before.**

**Run 2 asked for four things; three landed, and the fourth was correctly refused.**

- Run-2 (a) — a HARD schema check binding `log R` to its precision — **landed**, and it is the right
  instrument. §8 B-5 ENFORCEMENT clause 1 and the §12 "`log R` never unaccompanied" row require
  `ci_low`, `ci_high`, `ci_width` and `block_mde` on the **same row**, asserted over
  `metrics_by_cell`, `layer_deltas` and the ladder alike. This converts the design's central claim
  from an assertion into an invariant, which is exactly what run 2 said was missing.
- Run-2 (d) — a refusal on aggregates — **landed**. §8 clause 2 and §13 forbid any "N of M covered
  the mirror" statement without the resolution distribution of the cells counted (median `mde50`,
  count below each rung). This closes the negative-by-aggregation route, which was run 2's strongest
  objection.
- Run-2 (c) — restore predeclaration per stratum — **landed** as §8's EXPECTED RESOLUTION table,
  with the design correctly observing that predeclaration was the real content of the retired POWER
  block and is orthogonal to the label.
- Run-2 (b) — `finest_rung_detected` — **correctly refused, and the replacement is better.** The
  design's objection is right: "the smallest rung whose detection rate ≥ 0.8" requires picking 0.8,
  which is a privileged detection rate and therefore the cutoff C7 removed, wearing a different name.
  `mde50` / `mde80` / `mde95` restore the property run 2 actually needed — cells become countable,
  sortable and comparable — with no rung and no rate privileged, because three points of a curve
  cannot be a single bar. I record this as the design being right and run 2 being wrong.

**So the answer to "do the remedies work, or do they relocate the problem" is: they work.** B-5's
three requirements are all present, and two are HARD artifact-dependent checks rather than
conventions: precision travels with every effect; aggregates carry the resolution distribution;
resolution is predeclared before the run.

**Where the current text still fails B-5 is calibration, not architecture.** Under the old regime a
wrong power forecast was insulated — the `UNPOWERED` label caught a thin cell regardless of what the
design had predicted. C7 removed that insulation deliberately, and in doing so it made the
predeclared table **the** protection: adequacy is "the reader's judgement", and the reader judges
against §8's numbers. F3-01 shows those numbers are ~2.6× pessimistic in MDE terms and ~6.9× in
required `n`, because they mix a full-population numerator with a precision-selected denominator.

The failure mode this produces is worth naming precisely, because it is *not* the one B-5 was written
for. B-5 prevents a thin cell being read as a negative. A pessimistic predeclaration produces the
opposite: a stratum that genuinely resolves 0.05 is predeclared at 0.10–0.12, so a covering CI on a
well-measured cell reads as "we could not have seen it". Real evidence gets discarded as noise. The
retired boolean made that error impossible; the ladder makes it possible, and only correct arithmetic
closes it. That is the honest statement of C7's cost, and neither C7 as registered nor §9's
"strengthened, not weakened" paragraph acknowledges it.

**§9's "strengthened, not weakened" claim, as it now stands.** With the two HARD schema checks in
place the claim is *no longer* the bare assertion run 2 rejected — there is now machinery behind it,
and on the emission axis the claim is true. On the inference axis it remains overstated: what the
design has is an enforced *input* to the judgement, not an enforced judgement. One sentence would fix
the overstatement: "strengthened on emission; the inference protection now rests on §8's predeclared
resolution being correct, which is why §8 is computed from the artifact and reported across bases."

**What would fix the remainder — none of these is a threshold, and all are consistent with C7:**

1. **Fix §8's arithmetic per F3-01**, and print the range across defensible bases with an explicit
   invariance statement. P-25 already requires this; it is not a new obligation.
2. **Predeclare at the granularity the design actually reports.** §8's table is per clock and per
   coarse/narrow selection; the design reports per horizon, per δ, per layer cell and per clock. A
   predeclaration coarser than the reporting unit cannot calibrate a reader for the rows they will
   read. Extend it to L1's `d ≥ 9` cut, L2's three state cells and L3's gate — the strata that carry
   HYP-D6's content and that run-1 F1(ii) already asked for.
3. **Make the predeclaration auditable after the run** — one HARD schema check that each stratum's
   **predeclared** expected `mde50` and its **realised** `mde50` ship on the same row of the emitted
   stratum table. This admits, excludes, labels and ranks nothing, so it is C7-clean; what it does is
   convert the calibration from an unfalsifiable forecast into a checkable record, so a mis-calibrated
   predeclaration is visible in the emission rather than only in a later review. It is the single
   cheapest thing that would have caught F3-01 at run time.

---

### Independent verification of the operator's named checks

| Check | Result |
|---|---|
| **Exact mirror, slope 1, everywhere a target is stated** | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` in §1, §4.1, §5, §8, §9, §12, G4, G5, §13. `0.9408` appears **exactly once** (§5:251) and only to be refused, with the correct reason. §12 makes a fitted-slope residual anywhere a **hard failure**; G5 exists solely to make audit A1 non-repeatable. No defect |
| **Cost enters no estimand, threshold, band or comparison (C5)** | **CLEAN, and stronger after C7.** Traced every cost mention: header NOTE, §5 `DISCLOSED REFERENCE ONLY`, §7 ("no read in this design is compared against it"; "a sigma-unit effect is NEVER compared to the floor"), §12 HARD cost-isolation row with `p_be_net` flagged `DISCLOSURE_ONLY`, §13 first bullet, §15 column flag. With magnitudes gone from the bands there is no longer any surface for a cost term to enter |
| **No `powered`/`unpowered`/`at_target`/`NOT_RESOLVABLE` flag survives** | **CLEAN as an emitted flag.** §12 asserts the absence HARD; §9 and §13 refuse it; every remaining use of the word "powered" is either a historical reference to SPDR-018's own subset (§1, §8, §14 — correct and necessary) or the §4.1 scoping residue at F3-04. No flag is emitted anywhere |
| **No single canonical adequacy threshold under another name** | **CLEAN.** The ladder `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` matches C7's registered set exactly. `mde50`/`mde80`/`mde95` are three points of one curve, explicitly non-canonical, and nothing is admitted, excluded, labelled or ranked by them. §12 asserts no single canonical MDE threshold appears in code. The `0.10 rung` I suggest in F3-08 would be a *reporting* trigger for an operator decision, not an admission bar — but if it is adopted it must be written that way |
| **Amendment ledger reads 3 looser; L-23 flag adequacy** | **Count correct** (LOOSER 1, 2, 7; TIGHTER 3, 4, 8; NEUTRAL 5, 6, 9 = 3/3/3). **Flag adequately stated:** §14 names the streak, flags it for the operator at the execution gate as L-23 requires, and assesses each loosening individually rather than asserting the streak is benign. **But the ledger is incomplete** — F3-05 (§5.9 L4 narrowing) and F3-11 (`activeHold = 20`) are undeclared changes, so 3/3/3 is not yet provable. See the defensibility assessment below |
| **L-28 derangements** | **CLEAN.** Both permutation controls declare `DERANGEMENT (zero fixed points, asserted and counted)`; §12 asserts a measured fixed-point count of 0; TRIPWIRE-1 correctly declares `N/A` (a deliberate index shift, not a permutation) |
| **L-52 / P-23 check integrity** | **CLEAN.** Expected HARD-check **count** asserted and reconciled **by name**; every check depends on an emitted artifact (missing/empty ⇒ failure); determinism unconditional at `--jobs > 1` independent of `--resume`; no required check in a manual post-step |
| **P-24 comparator disclosure** | **CLEAN.** The M-3 block mandates the comparator's own mean, its null quantiles **and** its plant curve with every percentile; a bare percentile is explicitly refused |
| **L-50 / P-21 threshold portability** | **CLEAN.** All remaining numbers are dimensionless log units; §7 requires every effect in both bps and σ̂ units. One residue: §6's plant curves are still absolute bps (`+5/+10/+20/+40`) on a σ̂ = 73 bps universe — harmless in phase (a), which is crypto-only, but it must be restated in σ̂ units before any C1 cTrader leg (σ̂ = 13.03 bps) is authorised. Noted for the execution gate, not counted as a finding here |
| **L-21 / P-15 unit pin** | **CLEAN, and materially improved.** The ATR↔Parkinson estimator seam is gone (F3-03 closure above); the `√h`-in-hours clause closes the 2× bar-vs-hour ambiguity by name; divisor object 2's wording matches `unit_pin.json.divisor_object`; measured values computed at run |
| **Bands partition** | **CLEAN.** `ci_low > 0` / spans 0 / `ci_high < 0` is exhaustive and mutually exclusive |
| **B-9 / object identity** | **CLEAN** on structure (one open episode per symbol, suppression counted, block ≥ holding horizon) — **subject to F3-02** on the block's unit |
| **Holdout / XENA / family action / TEST** | **CLEAN.** §10 holdout never queried; §12 asserts zero queries ≥ 2025-01-08; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| **SPREAD-COST-DISCLOSURE** | **CLEAN.** All five fields verbatim, unchanged across three runs |
| `check_no_local_accounting` | **DEFERRED** to post-implementation QA; §12 declares the check |
| **Start gate** | **STILL FLAGGED.** `reflection-inputs.md` §9's operator decision remains unsigned. Design registration does not require it; **execution does** |

**Are the three loosenings individually defensible?**

- **AMENDMENT-1 (full TRAIN primary).** **Yes.** SPDR-018's own power lever 2; acts purely on
  population size; both bands still emitted and scored as verification; touches no fence, causality
  rule, control or claim boundary.
- **AMENDMENT-2 (M15 primary clock).** **Defensible only after F3-02.** The population half is
  sound and the direction risk is now correctly handled by AMENDMENT-9's Δ`log R` read. But §14's
  assessment that the two population loosenings "act only on population size and buy precision"
  is **not established for M15**: under a bar-stated block rule, M15 buys *apparent* precision that
  the calendar dependence does not support. Fix the block rule and this becomes true as written.
- **AMENDMENT-7 (phase-(b) trigger).** **Not defensible on this document's own authority** — see
  F3-09. The design is right that it is the one carrying real risk, and right that the scope
  protection survives; it needs an operator-signed family amendment, not a disclosure.

§14's closing assessment — "no loosening touches an integrity check, fence, causality rule or claim
boundary" — is **correct as stated** and I verified it independently against §10, §12 and §13.

---

### Verdict and routing

**REVISE.** F3-01 through F3-08, F3-10 and F3-11 route to **`quant-designer`**. **F3-09 routes to the
operator** (family-contract amendment), not to the designer.

**Nothing rises to REJECT.** No holdout contact, no causality violation, no missing tripwire, no cost
smuggling, no fitted-slope target, no unapproved *silent* deviation — AMENDMENT-7's departure is
disclosed, which is the difference between a REVISE and a REJECT.

**Fit to authorise implementation (`screen_code/`): NO — narrowly.** Two findings specify behaviour
the code must implement and are not yet written: **F3-02** (the block length is the estimator that
produces every band, and it is stated in the wrong unit for the primary clock) and **F3-06** (the M15
hold grid is undefined at the scale the design says bounds it). Everything else is prose arithmetic,
ledger rows and cross-reference repair — real, but it does not change a line of code.

This design is close. The run-2 fixes that were made are substantive and verified: the `k` correction
is exact on all five values, the comparator seam is genuinely closed, the M15 evidence is cited
correctly in both directions, the exit tripwire and G7 landed, and the B-5 schema checks are the
right instrument. What is left is one estimator clause, one grid clause, and a section-8 denominator
that was left behind when its numerator was fixed.

**Execution remains a separate operator gate regardless of this verdict**, and carries two standing
flags: the unsigned start gate, and F3-09.

---

### Addendum to F3-01 — the constructive fix, derived here so it is not re-derived a fifth time

Four QA runs have now produced four different resolution constants (370, 948, 569/955/1384, 7.28/6.60)
because each pairs a numerator and a denominator on different bases. The quantity that actually
governs resolution is **dimensionless** and removes the horizon split entirely:

```
c = mde_log * sqrt(n),   where  mde_log = block_mde_bps / ((1-p)*L)   on the CELL's own terms
required n at a target effect D:   n = (c / D)^2
```

Measured on SPDR-018's arm C (`analyst_per_cell_magnitudes.parquet`), `c` is **flat across horizons**
— `k` and `(1−p)·L` both rise ~2.3× with `h` and cancel — but it **rises with `n`**, which is the
block-dependence penalty, measured rather than argued:

| `n` band | cells | `c` at h=4 | h=12 | h=24 |
|---|---:|---:|---:|---:|
| < 100 | 8,264 | 5.4 | 5.7 | 5.7 |
| 100–1k | 7,150 | 6.7 | 6.7 | 6.6 |
| 1k–5k | 2,791 | 7.4 | 7.3 | 7.3 |
| 5k–15k | 401 | 7.7 | 7.4 | 7.3 |
| **> 15k** — this design's target scale | 26 | 11.9 | 8.4 | 11.7 |

At `c ≈ 7.5–9` (the target scale), `n = (c/Δ)²`:

| Δ`log R` | required `n` |
|---|---|
| 0.15 | ~2,500–3,600 |
| 0.10 | ~5,600–8,100 |
| 0.075 | ~10,000–14,400 |
| 0.05 | ~22,500–32,400 |
| 0.03 | ~62,500–90,000 |

Three properties worth having: it is one table instead of two, it is dimensionless so it ports across
arms and universes without re-derivation (**L-50 clean**), and the rise of `c` with `n` **is** the
block-dependence effect **F3-02** raises — measured on the parent's own emission rather than asserted.
Predeclaring `c` per stratum and emitting the realised `c` alongside would make the M15 dependence
question answerable from the run rather than arguable about it.

Applied to this design's strata, the conclusion changes: the M15 pooled baseline (~50–60k predeclared)
resolves near **0.031–0.040**, not the 0.05–0.07 §8 predeclares, and the H1 baseline (~13–16k) near
**0.060–0.078**, not 0.10–0.12. Both are roughly **1.6× finer** than the current predeclaration —
which is the direction that matters, because it means §8 currently tells the reader to discard
resolvable evidence as unresolvable. That is the B-5 inversion described in Part C.

---

## QA run 4 — 2026-07-29T00:00Z — mode: subagent — HEAD 42934ef91adb15a4aac2625b323021abf9ad94e5 (dirty: SPDR-019/design.md, SPDR-019/qa-review.md, SPDR-020/design.md, SPDR-020/qa-review.md)

**Target:** `python/experiments/SPDR-019/design.md` (987 lines; 793 at run 3).
**Stage:** DESIGN-STAGE. `screen_code/` absent — expected, not a finding.
**Independence:** I authored neither the design nor runs 1–3. Run 3's session went on to write the
fixes, so run 3's findings and the design's §8 are the *same* reasoning; I treated both as claims to
be broken, and re-derived every number from
`SPDR-018/results/analyst_per_cell_magnitudes.parquet` (24,098 rows) and
`SPDR-018/results/unit_pin.json` with my own code.

**Verdict: REVISE.** **Not fit to authorise implementation.** Three findings specify behaviour
`screen_code/` must implement and are not yet written (N-01, N-02, N-03). The remainder is
arithmetic and ledger repair — but two of those (N-04, N-06) sit on the one number that, post-C7,
*is* the B-5 protection.

Findings: **3 HIGH · 5 MEDIUM · 6 LOW.**

---

### PART A — run-3 findings: closure, and whether run 3's own numbers were right

Every figure run 3 asserted reproduces. I could not find an arithmetic error in run 3.

| Quantity | Run 3 / design | My re-derivation | Verdict |
|---|---|---|---|
| powered subset / `k` on it | 1,413 / 370 | 1,413 / **370.33** | REPRODUCES |
| full population / `k` | 23,700 / 948 | 23,700 / **947.89** | REPRODUCES |
| `(1−p)·L` powered vs full | 48.5 / 147.97 | **48.54 / 147.97** | REPRODUCES |
| `(1−p)·L` arm C by horizon | 90.81 / 146.44 / 212.57 | **90.81 / 146.44 / 212.57** | REPRODUCES |
| arm-C cell count | 18,632 | **18,632** | REPRODUCES |
| n-band table, cells | 8,264 / 7,150 / 2,791 / 401 / 26 | **exact**, on a left-open (`lo < n ≤ hi`) convention | REPRODUCES |
| n-band table, `c` | 5.4/5.7/5.7 · 6.7/6.7/6.6 · 7.4/7.3/7.3 · 7.7/7.4/7.3 · 11.9/8.4/11.7 | **5.39/5.73/5.67 · 6.68/6.68/6.58 · 7.42/7.32/7.32 · 7.67/7.36/7.33 · 11.85/8.36/11.74** | REPRODUCES |
| required-n at c=7.5 / c=9 | 2,500/3,600 … 62,500/90,000 | **exact** at both anchors | ARITHMETIC OK (anchors challenged — N-05) |
| arm-C pooled `n ≥ 10k` realised | 0.053–0.107 | **0.0534–0.1068** (41 cells) | REPRODUCES |
| three largest (20,977/20,572/20,279) | 0.073–0.094 at every horizon | **0.0727–0.0945**, h=4/12/24 all inside | REPRODUCES |
| arm-C cells reaching 0.03 | 0, other than three degenerate `n=2, p=0` | **exactly 3**, all `n=2, p=0`, min **0.01015** | REPRODUCES |
| pooled H1 TRAIN bars | 229,646 | **229,646** = Σ per-symbol `n`, 25 symbols | REPRODUCES |
| MATICUSDT / median / min | 21,582 / 12,444 / 555 | **21,582 / 12,444 / 555** (`1000RATSUSDT`) | REPRODUCES |
| σ̂ pooled = 73.00 bps; plant rungs 0.068/0.137/0.274/0.548 σ̂ | — | **73.0006**; 5/10/20/40 ÷ 73.0006 = 0.0685/0.1370/0.2740/0.5479 | REPRODUCES |

**Withdrawn claims are genuinely gone.** `k = 370`, `k = 948`, `569/955/1384`, `(1−p)·L = 48.5`, the
~10,800/21,200/58,800 table, the ~541k bar count and the "0.08–0.16" direct check all now appear
only inside explicit withdrawal paragraphs, with the correct replacement stated. §8's WHY THE EARLIER
FORMS ARE WITHDRAWN block is accurate on all three counts. The replacement arithmetic — `c` per band,
`n = (c/Δ)²` — is internally sound.

**Closure of F3-01…F3-11:**

| # | Status | Evidence |
|---|---|---|
| F3-01 (`k`/denominator basis mismatch) | **CLOSED as arithmetic** | §8 now forms numerator and denominator on the same cell; table reproduces exactly. But the *basis-range and invariance* half of P-25 that F3-01 invoked is now itself wrong — **N-06** |
| F3-02 (block in bars) | **CLOSED in unit, OPENED in estimator** | Block is now calendar-time, ≥ max(hold h, 20 h), identical on both clocks, code-asserted, effective `n` emitted. But the estimator that produces it is now under-specified and inconsistent with the basis `c` was measured on — **N-03** |
| F3-03 (§13 "calibrated") | **CLOSED** | The calibration sentence is gone; `design.md:836–838` states the freeze and the emitted signal rate |
| F3-04 (L-51 anchor / §12 / HARD) | **CLOSED** | §4.1 L3 now reads "every selected subset"; §12 row added; in the HARD list. HARD status defensible — see Part B |
| F3-05 (cell count) | **CLOSED and correct** | 1+4+5+3+**20**+4 = **37** ✓; L4 = 3+3+2+2+4+4+1+1 = **20** ✓; 37 × 2 × 3 = **222 ≤ 240** ✓. Internally consistent for the first time. One omission — **N-10** |
| F3-06 (M15 hold grid) | **CLOSED** | Hours on both clocks throughout; the only surviving "period" occurrences are the two withdrawal notes. §2 entry rule, §2 exit table, §4.1 L0 (1 h / 2 h) and §4.2 all agree. G1/G2 quote bare `1` / `2` but are H1-only, where hours = bars |
| F3-07 (pooled primary) | **CLOSED, properly** | The revert clause matches `design-requirements.md` §5 verbatim ("POOLED: disclosure-only **unless homogeneity shown**"), so this is compliance, not an override |
| F3-08 (C6 `NOT_RESOLVABLE`) | **CLOSED with a new blemish** | §4.3 discharges C6's obligation without the flag. The "0.10 rung" is a privileged value — **N-12** |
| F3-09 (AMENDMENT-7 vs C6) | **CORRECTLY BOOKED** | I re-checked `cf-voldir-001.md`: C6's trigger clause is verbatim unchanged, there is no C8. The EXECUTION BLOCKER note is the right instrument and correctly scoped to execution, not implementation |
| F3-10 (direct-check figures) | **CLOSED** | Restated figures reproduce exactly (table above) |
| F3-11 (ledger/checklist items) | **CLOSED**, one with a wrong reason | M-4 row present in §12; C5 NARROWING annotated with its provenance; C7 added to the in-force list; the dangling C3 citation is gone from §10. AMENDMENT-10 exists but its stated justification is factually wrong — **N-11** |

---

### PART B — defects in the run-3 changes

#### N-01 — HIGH — both HARD tripwires have no stated criterion, so the design's two blocking checks cannot be implemented as written

**Fails:** `design-requirements.md` §4 (`must collapse the edge; expected collapse fraction ≈ <...>`);
§6.1 TRIPWIRE-1 ("must **materially** change the edge"); TRIPWIRE-2 ("must differ on both legs");
§11 G6 ("QA confirms a **material** difference"); §12 HARD list, which blocks execution on both.

"Materially" is not a number and not a rule. A HARD check that invalidates the emission needs a
criterion the code can evaluate; here the developer must invent one, and whatever they invent is an
undeclared threshold that no review has seen. The mandatory block format asks for an expected
collapse fraction precisely to stop this. TRIPWIRE-2 is worse: it carries *two* legs plus a
directional claim ("the favourable twin must read BETTER") with no magnitude on any of them, so a
1e-9 difference passes.

This is not in tension with C7. C7 retires adequacy thresholds on the *effect*; a future-destroy
tripwire is the one place INFR-016 keeps HARD, and it is required to state its own bite.

**Fix (quant-designer).** State each tripwire's expected collapse fraction (or its expected Δ`log R`
in log units, with the plant curve that shows the twin is detectable at that size) and the rule the
code applies. Same for G6.

#### N-02 — HIGH — §4.1 still defines the L4 unmodulated arm as "a fixed ATR multiple", contradicting §4.2 and reopening the exact EXP-025 seam AMENDMENT-8 says it closed

**Fails:** §4.1 L4 row, `design.md:179` — *"unmodulated (a fixed ATR multiple)"* — against §4.2's
UNMODULATED block (`a * s_hat_uncond`, "the SAME Parkinson-EWMA estimator … Same unit, same
estimator, same clock") and §4.2's flat prohibition *"ATR20 … never sets an exit boundary"*; L-21 /
P-15; AMENDMENT-8's stated purpose.

Run 3 recorded R2-03 as "CLOSED on units and clock". It is closed in §4.2 and **open in §4.1**, which
is the stage table an implementer reads first. The two clauses specify different estimators for the
same arm, differing by the ~1.5–1.7× Wilder-vs-Parkinson level shift the design itself names as the
corrupting factor. §12 has **no** assertion binding the unmodulated arm to `ŝ_uncond`, so nothing in
the integrity checklist would catch the wrong one being coded.

(Provenance, in the design's defence: reflection §5.9 says "a fixed multiple of ATR", so §4.1 is
inherited text. Registered C6 does not specify ATR, so §4.2's change is legitimate against the family
contract — but then §4.1 must follow it.)

**Fix.** Restate §4.1's L4 row as `a × ŝ_uncond` per §4.2, and add a §12 assertion that the
unmodulated and modulated arms share estimator, unit and clock.

#### N-03 — HIGH — the block-bootstrap estimator is now specified by a single block length with no seed battery and no block sweep (L-20 / INFR-004), and §8.1's claim that `c` was measured on this basis is false

**Fails:** **L-20** clauses 2 and 3 (*"aggregate every CI across a **seed battery** (`DEFAULT_N_SEEDS=5`)
and disclose the per-seed bound spread"*; *"**block length has no correct value**: disclose a
`block_sensitivity` sweep (½×/1×/2×) and flag if `sign(ci_low)` changes — block-fragile inference is
not evidence"*), enforced in `xen.evaluation`; §8.1 BLOCK RULE; §8.1's transport claim; §12's calendar
block row.

Three distinct problems in one clause.

1. **No seed battery, no sweep.** §8.1 mandates one block length. `ci_low > 0` — ABOVE THE MIRROR —
   is this design's only positive finding and is decided entirely by the 2.5% quantile of one
   bootstrap. L-20 exists because that quantile is itself a random draw and because block choice
   flips signs. The 2,000-seed batteries in §6 are on the *derangement controls*, not on the CI. The
   parent, SPDR-018, ran a **5-seed battery and an envelope over {1,3,7}-day blocks**; SPDR-019 drops
   both. That is a regression against a lesson already enforced in shared code.
2. **`c` was not measured under this rule.** §8.1 asserts *"this is also the basis on which §8's `c`
   constant was measured (SPDR-018 H1 cells, where bars and hours coincide), so `c` transports to M15
   only under this rule."* SPDR-018 §6.2 actually specifies: aggregate to **per-calendar-day
   sufficient statistics**, resample **day-blocks of {1, 3, 7} days**, minimum block **24 H1 bars**,
   and take the **min/max envelope over blocks × seeds (conservative)**. That is a different
   estimator, a coarser minimum (24 h, not 20 h), and a deliberately conservative envelope. `c` is
   therefore an artefact of an estimator SPDR-019 does not use, and its transport is asserted, not
   established. Direction: the parent's envelope is conservative, so SPDR-019's single 20-hour block
   will likely realise **smaller** `c` — i.e. the predeclared table is pessimistic, which §9 itself
   now names as a B-5 failure.
3. **20 hours is the wrong end of the range.** `E[run]` is 18.9–23.1 H1 bars with MAE ≈ 12, evidence
   class **[D]** — "sets a scale, never a timer" (reflection V14, verified). Taking the **bottom** of
   a [D] range as a floor is the least conservative choice available, on the one parameter whose
   failure mode (under-blocking → narrow CI → manufactured `ci_low > 0`) the clause exists to
   prevent. It is also *below the parent's own 24-hour minimum block*.

   To be clear on the question the operator asked: **20 hours is not a threshold in disguise.** Nothing
   is admitted, excluded, labelled or ranked by it; it is an estimator parameter of the same class as
   "block ≥ H", and it survives AMENDMENT-C7, which retires *effect-size adequacy* thresholds. The
   objection is that it is calibrated to the wrong end of its own evidence and unsupported by a sweep.

**Fix.** Adopt the parent's estimator or state why not: minimum block **24 hours**, a `{1×, 2×, 4×}`
(or {1,3,7}-day) block sensitivity sweep with a `sign(ci_low)`-flip flag, and a ≥5-seed battery with
the per-seed bound spread emitted. Then either re-measure `c` under that estimator or restate §8.1's
transport sentence as the assumption it is.

#### N-04 — MEDIUM — the design's target strata sit *beyond* every `n` band `c` was measured on, in the direction `c` is known to rise; the `>15k` band is 26 cells and is not flat across horizons

**Fails:** §8's *"`c` is FLAT ACROSS HORIZONS"* against its own `>15k` row; §8.1's per-stratum table;
P-25 / L-53 (basis range must be reported *and* its conclusions' invariance stated).

Answering the operator's question directly: **the `>15k` band is too thin to carry the weight placed
on it.** 26 cells over 8 distinct `n` values, split **6 / 14 / 6** across h=4/12/24, and 20 of the 26
are `dose_response` basis. Within h=12 the 14 cells run `c` = 6.62 to 12.34 (IQR 7.38–11.58). The
band's own numbers refute the flatness claim the sentence above it makes: 11.9 / 8.4 / 11.7 is a 1.4×
spread across horizons, where every other band is flat to ±0.1. The design prints the row and labels
it "this design's target scale" without noting that the flatness statement fails exactly there.

Worse, the design's headline strata are **not in that band either**. Maximum `n` anywhere in the
parent is **20,977**. §8.1 predeclares M15 L0 at **50k–60k** and M15 L1 `d≥5` / L2 shock at 25k–30k.
`c` **rises monotonically with `n`** (5.4 → 6.7 → 7.4 → 7.7 → 8.4–11.9) — the design says so and
attributes it to block dependence. Applying a `c` measured at `n ≤ 21k` to `n = 60k` therefore
extrapolates a rising quantity, which **understates** `mde50`. That is the optimistic direction: the
classic B-5 failure (a cell reads as a measured null when it is not), not the mirror-image one §9
spends a paragraph on.

**Fix.** State plainly that the `>15k` band is 26 cells and is *not* horizon-flat; mark every stratum
predeclared above `n = 21k` as an **extrapolation beyond the measured support**, with the direction of
the likely error named; and emit realised `c` per cell so the extrapolation is checked at run.

#### N-05 — MEDIUM — the `c = 7.5` and `c = 9` anchors are picked, not measured; 7.5 lies below the entire target-scale band

**Fails:** §8's required-episodes table and its BASIS RANGE paragraph ("`c` across defensible bases
runs **5.4** … to **11.9**").

Neither anchor is an endpoint of the stated range, and neither is a measured band value. The measured
values are 5.4 / 5.7 / 6.6 / 6.7 / 7.3 / 7.4 / 7.7 / 8.4 / 11.7 / 11.9. **7.5 appears nowhere**, and it
sits *below* the whole `>15k` band (8.4–11.9) that the same section calls the design's target scale.
The arithmetic at both anchors is exact — I reproduce all ten cells — but the anchors themselves are
chosen, and the choice is in the optimistic direction for the strata that matter.

**Fix.** Quote the table at the endpoints the section actually declares (5.4 and 11.9), or at the
target band's own endpoints (8.4 and 11.9), and say which is which.

#### N-06 — MEDIUM — the invariance statement is arithmetically false on the design's own basis range: 0.03 is *not* out of reach at every basis

**Fails:** §8 BASIS RANGE — *"0.03 is out of reach at EVERY basis (≥ **62,500** episodes even at the
most favourable `c`)"*; P-25 (*"state which conclusions are invariant to it"*), which this paragraph
exists to discharge.

62,500 = `(7.5/0.03)²`. The most favourable `c` in the design's own declared range is **5.4**, giving
`(5.4/0.03)² = ` **32,400** episodes — and §8.1 predeclares the M15 L0 baseline at **50k–60k**. So on
the design's own stated basis range, the M15 baseline *does* reach 0.03, and the invariance claim
inverts. The same substitution error weakens the 0.05 row (at c=5.4, 0.05 needs 11,664 — reachable by
almost every M15 stratum and by H1 L0 — so "BASIS-DEPENDENT" understates how basis-dependent it is).

This matters more than a normal arithmetic slip, because §8's whole purpose post-C7 is to be the
predeclaration the reader calibrates against, and P-25 compliance is the reason the paragraph exists.

**Fix.** Recompute the invariance statement at 5.4 and 11.9 and restate honestly: 0.15 and 0.10
invariant; **0.05 and 0.03 both basis-dependent**, with the crossing `n` for each.

#### N-07 — MEDIUM — one row of the §8.1 expected-resolution table cannot be derived from any single `c` band, and one is optimistic

I recomputed every row as `mde50 = c/√n` using the `c` bands the section itself prints
(`>15k → 8.4–11.9`; `5k–15k → 7.3–7.7`; `1k–5k → 7.3–7.4`; `100–1k → 6.6–6.7`):

| Stratum | Design | My recompute | Verdict |
|---|---|---|---|
| M15 L0, ~50–60k | 0.034–0.053 | 8.4/√60k = 0.0343 · 11.9/√50k = 0.0532 | MATCHES (band extrapolated — N-04) |
| M15 L1 d≥5, ~25–30k | 0.049–0.075 | 0.0485 – 0.0753 | MATCHES |
| M15 L1 d≥7, ~15–18k | 0.063–0.097 | 0.0626 – 0.0972 | MATCHES |
| M15 L1 d≥9, ~5–6k | 0.094–0.109 | 0.0942 – 0.1089 | MATCHES |
| M15 L2 shock, ~25–30k | 0.049–0.075 | 0.0485 – 0.0753 | MATCHES |
| M15 L2 k=4, ~12–15k | 0.060–0.070 | 0.0596 – 0.0703 | MATCHES |
| M15 L2 k=12, ~4–5k | 0.103–0.117 | 0.1032 – 0.1170 | MATCHES |
| M15 L2 joint, ~6–8k | 0.082–0.099 | 0.0816 – 0.0994 | MATCHES |
| M15 L3 gate, ~8–15k | 0.060–0.086 | 0.0596 – 0.0861 | MATCHES |
| **H1 L0, ~13–16k** | **0.059–0.074** | on `5k–15k` c: 0.0577–0.0675; on `>15k` c: **0.0664–0.1044** | **DOES NOT MATCH EITHER BAND** |
| H1 coarse, ~7–8k | 0.082–0.092 | 0.0816 – 0.0920 | MATCHES |
| H1 narrow, ~1.3–1.6k | 0.183–0.205 | 0.1825 – 0.2052 | MATCHES |
| per-symbol, ~0.5–2.5k | 0.13–0.30 | 0.146 – 0.300 | HIGH END MATCHES; **low end 0.13 vs 0.146** |

The H1 L0 row straddles the 15k boundary and has been computed by taking the *lower* `c` at the
*higher* `n` and the *higher* `c` at the *lower* `n` — the inverse of the c-rises-with-n rule the same
section states. Read on the correct band its interval is **0.066–0.104**, i.e. up to 1.4× coarser than
predeclared. The per-symbol low end uses an unstated `c ≈ 6.5`.

**Fix.** Recompute both rows on the band their `n` falls in; where a stratum straddles a boundary,
show both and say so.

#### N-08 — MEDIUM — the predeclaration is still coarser than the reporting unit, on the axis with the largest known effect on `n`

**Fails:** §8.1's own stated principle (*"Predeclared at the granularity the design REPORTS … A
predeclaration coarser than the reporting unit cannot calibrate the reader for the rows they will
actually read"*); §10's cell count, which is defined **per `(clock, δ)`**; AMENDMENT-12, which claims
this was fixed.

The table is predeclared per (clock × layer cell). The reporting unit is (clock × layer cell × **δ**),
and the design states in AMENDMENT-3 that `deltaThreshold` "swung power ~7×". A 7× swing in `n` is a
**2.6× swing in `mde50`** — larger than the entire correction F3-01 was raised for. So the row a
reader will actually read (say, M15 L1 `d≥7` at δ=1.0) has no predeclared value, and the value it will
be compared against is the one predeclared for a population up to seven times larger.

This is the un-fixed half of run 3's own Part C recommendation 2. Run 3 asked for L1/L2/L3 granularity
and got it; the δ axis, which run 3 did not name, is the bigger term.

**Fix.** Either predeclare per δ (three columns, same arithmetic), or predeclare at δ=0.5 and state
explicitly that the δ=0.25 and δ=1.0 rows scale by `√(n_δ/n_0.5)` with the realised ratio emitted.

#### N-09 — MEDIUM — no re-derived false-qualification expectation for the final band set (L-23 clause 2), on a ≤240-cell grid whose only positive band is a 95% CI

**Fails:** **L-23** (*"After the final amendment, re-state the expected number of false qualifiers
under the global null with the FINAL gate set"*), which the `qa-compliance` §3 amendment-ledger clause
makes binding; §9 BANDS; §10 Cell count ("Disclosed, not rationed").

The ledger does the direction half of L-23 properly (see below) and skips the arithmetic half.
ABOVE THE MIRROR is `ci_low > 0` at nominal 95% — a one-sided ~2.5% false rate. Across 222 declared
cells that is **~5–6 cells expected above the mirror under a true global null**, before the per-symbol
expansion. The design's headline finding is precisely "some cell read above the mirror", and nothing
in §8, §9 or §13 tells the reader how many to expect for free. "Disclosed, not rationed" discloses the
*count of cells*; L-23 asks for the expected count of *false positives* under the final band set. They
are not the same disclosure and only the second protects the read.

This requires no threshold and no rationing — it is one predeclared number.

**Fix.** State the expected number of ABOVE-THE-MIRROR cells under the global null for the declared
grid (and separately for the per-symbol expansion), in §9 or §10.

#### N-10 — LOW — the multiplicity count omits the per-symbol expansion the design commits to reporting

§10 declares ≤240 cells. §8.1 predeclares a "per-symbol (any stratum)" resolution row and §9 reports
per-symbol figures as disclosure, so the emitted table is ~222 × 25 ≈ 5,550 rows. `spdr-lane.md`
requires the cell count and the multiplicity treatment to be disclosed. **Fix:** add the per-symbol
row count to §10 and mark it disclosure-only, so the declared count matches the emitted table.

#### N-11 — LOW — AMENDMENT-10's justification describes a deviation that did not occur

The row says the grid "reaches 20 hours — **beyond** the checkpoint's frozen `h ∈ {4, 12, 24}` bars".
20 < 24, so it does not reach beyond the frozen grid at all. The actual deviations are the *addition*
of `h = 1` (below the frozen grid, and it is also the L0 baseline) and the *removal* of `h = 24`. The
`E[run]` authority cited is therefore invoked for something the amendment does not do, while the two
things it does do are undeclared. `h = 1` also sits outside the support on which `c` was measured
(parent horizons are {4, 12, 24}), which compounds N-04.

**Fix.** Restate the row: adds `h = 1`, drops `h = 24`, both inside the `E[run]` scale; label the
direction on what actually changed.

#### N-12 — LOW — §4.3's "0.10 rung" privileges one value out of six for no stated reason

The clause is correctly built — the fraction is **reported, not adjudicated**, no cell is labelled and
no grid is auto-refused — so this is **not** a reintroduced threshold in force, and it does discharge
C6's obligation without the retired flag. My objection is narrower: C7 removed *the* canonical rung,
and singling out 0.10 for the summary statistic re-creates a canonical rung by habit, with no argument
for 0.10 over 0.075 or 0.05. The fix is free: report the fraction at **every** rung of C7's registered
ladder — a six-number distribution, which privileges nothing and tells the operator strictly more.

#### N-13 — LOW — control blocks omit the B-2 collapse fraction; the M-2 span artifact has no home

`design-requirements.md` §3 requires `disclosure: collapse fraction reported (control effect / raw
effect)` in every control block. None of the four blocks carries one; §12 lists "collapse fraction"
only in the INFORMATIVE catch-all. Separately, §12 asserts M-2 span disclosure per horizon cell, but
neither `metrics_by_cell.parquet` nor any other §15 row lists a span column, so the assertion has no
artifact to read. **Fix:** add the collapse-fraction line to the two derangement blocks and the
magnitude-matched comparator; name the span columns in §15.

#### N-14 — LOW — G1/G2 quote holds without units

`activeHold = 1` and `inactiveHold = 2` in G1/G2 against §2's "HOURS on BOTH clocks". Both traces are
H1, where the two readings coincide, so nothing is ambiguous in practice — but these are the traces QA
computes by hand, and the unit should be written. **Fix:** "`activeHold` = 1 hour".

---

### Verified clean — recorded so they are not re-litigated

| Check | Result |
|---|---|
| **Exact mirror, slope 1, everywhere a target is stated** | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` in §1, §4.1, §5, §8, §9, §12, G4, G5, §13. `0.9408` appears exactly once (§5:282) and only to refuse it, with the correct reason (its residual is centred at zero by construction). §12 makes any fitted-slope residual a hard failure; G5 exists to make audit A1 non-repeatable. **This is correct and is not a finding** |
| **Cost isolation (AMENDMENT-C5)** | **CLEAN.** Header NOTE, §5 DISCLOSED REFERENCE ONLY, §7 ("no read in this design is compared against it"; σ̂ effects never compared to the floor), §12 HARD cost-isolation row with `p_be_net` flagged `DISCLOSURE_ONLY`, §13 first bullet, §15 column flag. With magnitudes gone from the bands there is no surface for a cost term to enter |
| **No adequacy flag survives as an emitted field** | **CLEAN.** Every occurrence of "powered" is either a historical reference to SPDR-018's own subset (§1, §8, §14) or the explicit retirement note in §4.1's L3 row. §12 asserts the absence HARD; §9 and §13 refuse it |
| **No canonical threshold under another name** | **CLEAN in force.** Ladder `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` matches C7's registered set exactly. `mde50/mde80/mde95` are three points of one curve and nothing is admitted, excluded, labelled or ranked by them. The 20-hour block is an estimator parameter, not an effect bar (N-03 challenges its calibration, not its class). The 0.10 rung is a reporting cut, not an admission bar (N-12 is hygiene) |
| **L-51 HARD status vs INFR-016** | **DEFENSIBLE — I tested the argument and it holds.** INFR-016 retired *value* gates (`at_or_above_p95`, `n_legs_floor`, `hard_fail_leak`) and split controls by class. L-51's check adjudicates no value; §12 makes it HARD on **presence and form** only, which is the same class as P-23/L-52's "a check that depends on an emitted artifact — missing or empty is a failure". Governance `chapter-06-governance.md:98` makes it mandatory on any 019/020 design, and a mandatory check that can be silently skipped is indistinguishable from one that passed. The re-anchor to "every selected subset … each against its own complement", explicitly including cells above vs below median `mde50`, preserves L-51's original precision-selection target after C7 removed the population it named. **Better than the retired form** |
| **Amendment-direction count** | **VERIFIED ROW BY ROW.** LOOSER = 1, 2, 7, 10 (**4**); TIGHTER = 3, 4, 8, 11, 13 (**5**); NEUTRAL = 5, 6, 9, 12 (**4**). 13 rows, no row unlabelled. The stated "4 looser / 5 tighter / 4 neutral" is **correct** |
| **L-23 streak flag** | **ADEQUATE on the direction half.** The four loosenings are named, flagged for the operator at the execution gate, and assessed individually rather than asserted benign; AMENDMENT-7 is correctly conceded as not defensible on this document's authority. The arithmetic half is missing — **N-09** |
| **L-28 derangements** | **CLEAN.** Both permutation controls declare zero fixed points, asserted and counted; §12 asserts a measured count of 0; TRIPWIRE-1 correctly declares N/A (deliberate index shift, not a permutation) |
| **L-50 / P-21** | **CLEAN.** Plant curve now in σ̂ units, re-derived per universe at run; I verified 5/10/20/40 bps ÷ 73.0006 = 0.0685 / 0.1370 / 0.2740 / 0.5479 against the design's 0.068 / 0.137 / 0.274 / 0.548. Run 3's standing residue is closed |
| **L-21 / P-15 unit pin** | **CLEAN in §7.** Divisor object 2's wording matches `unit_pin.json.divisor_object` verbatim; values computed at run. Subject to **N-02** in §4.1 |
| **SPDR-013 M15 evidence, both ways** | **VERIFIED VERBATIM.** `analysis.md:177` "IC 0.34–0.46; ridge ≥ AR1; M15 > H1; all 25 symbols"; `:164` "H1 DESIGN 0.57 / CONFIRM 0.48; M15 0.20–0.28 (worse than shuffled). +20 bps bite plant detected". §8.1 cites both correctly and AMENDMENT-9's Δ`log R` response is the right one |
| **`E[run]` 18.9–23.1, MAE ~12, class [D]** | **VERIFIED** at reflection V14 (`:150`), including "use `E[run]` as a **scale**, never as a timer" |
| **C5 / C6 / C7 registry text** | **VERIFIED** at `cf-voldir-001.md:420 / 430 / 448`. C6's trigger clause and `NOT_RESOLVABLE` booking are verbatim as the design quotes them; C7's ladder set matches; **there is no C8** |
| **Internal consistency §4.1 / §4.2 / §10** | **CLEAN** on counts (37 = 1+4+5+3+20+4; L4 = 20; 222 ≤ 240). Contradictory on the L4 unmodulated arm — **N-02** |
| **§15 vs §8 / §12** | **CLEAN** except the M-2 span columns (**N-13**). `selection_check.json`, `resolution_ladder.parquet` (with the predeclared-vs-realised columns), `layer_deltas.parquet`, `unit_pin.json` and `integrity_selfcheck.json` are all present and match their citing clauses |
| **Holdout / XENA / TEST / family action** | **CLEAN.** §10 holdout never queried; §12 asserts zero queries ≥ 2025-01-08; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| **SPREAD-COST-DISCLOSURE** | **CLEAN.** All five fields verbatim, unchanged across four runs |
| **L-52 / P-23** | **CLEAN.** HARD-check count asserted and reconciled by name; every check bound to an emitted artifact; determinism unconditional at `--jobs > 1` |
| **Start gate** | **STILL FLAGGED.** `reflection-inputs.md` §9's operator decision remains unsigned. Execution requires it |

---

### PART C — does the design deliver B-5's protection under C7?

**Judgement: the architecture is sound and I confirm run 3's structural conclusion — but run 3's
diagnosis that "only the arithmetic is wrong" was too generous, and the remedy it chose does not do
the work it is asked to do.**

**The three emission-side protections are real and I have no objection to them.** Every `log R` bound
to `ci_low`/`ci_high`/`ci_width`/`block_mde` on the same row, asserted across three artifacts; every
aggregate required to carry the resolution distribution of the cells it counts; the full ladder on
every cell. These are HARD, artifact-dependent, and they close the two routes a boolean label left
open. On emission the design is genuinely stronger than the label it replaced.

**The symmetry argument is real, not a rationalisation.** The design now argues that a *pessimistic*
predeclaration is also a B-5 failure — resolvable evidence discarded as unresolvable. I tested this
for self-serving convenience and it survives: B-5's purpose is that the reader's judgement about
adequacy be correctly informed, and a forecast that is wrong in either direction mis-informs it
identically. It is also not costless to the design, since it is the reason §8 had to be recomputed
rather than left conservative. Two caveats keep it from being a free pass. First, the two errors are
**not equally dangerous**: an optimistic table converts a thin cell into a measured null, which is the
error that ends a research line, while a pessimistic one converts a measured null into "we could not
see it", which merely wastes it. §9 presents them as equivalent. Second — and this is the sting —
after the run-3 fixes the design's residual error is now most likely **optimistic**, not pessimistic:
`c` is extrapolated past its support in the direction it rises (N-04), the anchors chosen are below
the target band (N-05), and the parent's conservative envelope is dropped (N-03). The symmetry
argument was used to justify making the table finer; the mechanisms that made it finer are the ones
that push it toward the dangerous side.

**The predeclared-vs-realised same-row check does less than it is credited with.** The operator's
question is the right one. On the evidence: nothing acts on the comparison — the design says so four
times ("Nothing is admitted, excluded, labelled or ranked by the comparison"). What it buys is real
but narrow: it makes a mis-calibration **visible in the emission** rather than only reconstructible by
a reviewer who re-derives `c` from the parent. That is a genuine improvement over an unfalsifiable
forecast, and it is C7-clean. What it does **not** do is what §9 claims for it — it is not the
protection, because a reader who trusts the predeclaration has already formed their judgement by the
time they could notice the discrepancy, and no artifact tells them the discrepancy matters. Under
N-08 it is also partly inoperative: the predeclaration has no δ axis, so for two of three δ levels
there is no matching predeclared value to put on the row.

**What would actually work, without a threshold.** Three things, none of which admits, excludes,
labels or ranks anything:

1. **Emit realised `c` per cell** (`block_mde_log × √n`) next to the predeclared `c` band. This is the
   single most useful column the design is missing. It converts every open question above —
   does `c` transport to M15? does it keep rising past n = 21k? does the calendar block rule reproduce
   the parent's envelope? — from an argument into a measurement, and it is one multiplication.
2. **Predeclare an interval, not a point, and derive the interval from the measured band spread**
   (including the `>15k` band's 6.6–12.3 dispersion), rather than from the band medians. A
   predeclaration whose stated width matches the parent's actual dispersion cannot be "wrong by 1.6×"
   in either direction; it is simply wide, which is the honest state of the evidence.
3. **Restore the parent's estimator** — block sweep plus seed battery (N-03). This is what makes the
   realised `mde50` a property of the data rather than of one block choice, and it is the only one of
   the three that changes a number rather than a disclosure.

None of these is a rung, a rate or a bar. All three are consistent with C7 as registered.

---

### Verdict and routing

**REVISE.**

- **N-01, N-02, N-03** → `quant-designer`, **before implementation**. Each specifies behaviour
  `screen_code/` must contain: the criterion two HARD tripwires apply, which estimator sets the L4
  unmodulated boundary, and how the CI that defines every band is computed.
- **N-04 … N-08, N-11, N-12** → `quant-designer` (arithmetic, predeclaration granularity, ledger).
- **N-09, N-10, N-13, N-14** → `quant-designer` (disclosure completeness).
- **AMENDMENT-7's EXECUTION BLOCKER stands** and routes to the **operator**, not the designer. I
  re-verified independently: `cf-voldir-001.md` carries C6's trigger clause verbatim and there is no
  C8. Run 3's booking of this is correct and correctly scoped to execution.

**Nothing rises to REJECT.** No holdout contact, no causality violation, no missing tripwire, no cost
smuggling, no fitted-slope target, no silent deviation.

**Fit to authorise implementation (`screen_code/`): NO.** Three clauses the code must implement are
either undefined (N-01), self-contradictory (N-02), or under-specified against a lesson already
enforced in shared code (N-03). That is the whole of the implementation objection — N-04 through N-14
are prose, arithmetic and disclosure, and none of them changes a line of code.

**Execution remains a separate operator gate regardless**, carrying two standing flags: the unsigned
start gate (`reflection-inputs.md` §9) and AMENDMENT-7 vs registered C6.

**What I did not reach.** I did not re-derive the M15 bar count or the predeclared M15/H1 episode
counts from the catalog — I verified only that they are internally consistent with 229,646 H1 bars ×4
and with each other; the design makes them measured-at-run predictions, so this is deferred to the
run. I did not independently audit `xen.evaluation.block_bootstrap_ci`'s current defaults beyond L-20's
recorded contract. I did not review SPDR-020, which shares §8's `c` derivation and where N-03 through
N-06 are likely to apply verbatim.

## QA run 5 — 2026-07-29T00:42:39Z — mode: operator-session — HEAD 42934ef91adb15a4aac2625b323021abf9ad94e5

**Reviewed git state:** dirty:
`python/experiments/SPDR-019/design.md`,
`python/experiments/SPDR-019/qa-review.md`,
`python/experiments/SPDR-020/design.md`,
`python/experiments/SPDR-020/qa-review.md`;
untracked:
`python/experiments/SPDR-019/results/`,
`python/experiments/SPDR-020/results/`,
`python/src/xen/resolution_basis.py`.

**Target:** `python/experiments/SPDR-019/design.md` (978 lines).
**Stage:** DESIGN-STAGE. `screen_code/` is absent — expected, not a finding.
**Independence:** fresh operator session; this reviewer authored neither the design nor its fixes.
Runs 3 and 4 were read in full. Current text, the new module, and both resolution artifacts were
treated as untrusted claims.

**Verdict: REVISE. Not fit to authorise implementation (`screen_code/`).**

Findings: **5 HIGH · 2 MEDIUM · 2 LOW.**

### Run-4 blocker closure

| Run-4 blocker | Run-5 result | Evidence |
|---|---|---|
| N-01 tripwire pass rules | **OPEN** | §6.1 adds TRAIN-derived inputs and CIs, but still never defines the statistic, mapping, or executable inequality that makes either HARD check distinguishable — **R5-01** |
| N-02 L4 comparator seam | **OPEN** | §4.1 and §4.2 now agree on Parkinson `ŝ`; §7 still calls ATR20 the “unmodulated-device normaliser”, and §12 still has no comparator-identity assertion — **R5-02** |
| N-03 inherited block rule | **OPEN** | sweep and battery are now mandatory, but the alleged verbatim quote omits the `{1,3,7}`-day sweep, per-calendar-day aggregation, and effective-block cap — **R5-03** |
| N-06 false 0.03 invariance | **CLOSED** | the claim is explicitly withdrawn and not replaced by another uncomputed invariance claim |

The withdrawn `max(hold hours, 20 hours)` single-block rule appears only in the superseded
AMENDMENT-11 record and explicit withdrawal history. It is not a live rule and is not a finding.

### Independent numeric audit of the new resolution basis

I recomputed
`c = gross_block_mde_mean_bps / ((1-gross_p) * gross_L) * sqrt(gross_n)`
directly from
`SPDR-018/results/analyst_per_cell_magnitudes.parquet`.

| Scope / `n` band | Cells | Distinct `n` | Median `c` | Horizon medians (`h=4 / 12 / 24`) |
|---|---:|---:|---:|---|
| all arms, `15,000+` | **138** | **36** | 13.140 | 11.855 / 8.363 / 11.744 |
| arm C, `15,000+` | **26** | **8** | 11.304 | 11.855 / 8.363 / 11.744 |

`results/resolution_basis.json` reproduces the module's arithmetic exactly **for its chosen
all-arm, `n > 1` population**. It does not reproduce the design's declared 26-cell / 8-distinct-`n`
thinness disclosure: its JSON says 138 / 36. The target band is also not horizon-flat (1.42× between
8.363 and 11.855). See **R5-04**.

### Findings

#### R5-01 — HIGH — the two HARD tripwires still have no implementable pass rule

**Fails:** design §6.1 lines 357–386; §11 G6; §12 HARD list;
`design-requirements.md` §4; L-24/F06.

TRIPWIRE-1 says “must materially change” and “HARD on DISCRIMINATION”. Its new expected separation is
derived from autocorrelation of the shifted conditioning stream, but no formula maps that
autocorrelation to an expected `Δlog R`, no tested statistic is named, and no inequality defines
“distinguishable”. TRIPWIRE-2 has the same defect: ambiguous-bar frequencies predict how often fills
may differ, not the size or sampling distribution of the resulting `log R` difference. “With a CI”
does not itself define a pass rule. A developer must still invent both HARD criteria.

**Fix before implementation:** for each leg, name the measured statistic, derive the prospective
TRAIN threshold from the stated pre-outcome stream, give the exact pass/fail inequality (including
CI endpoint and direction), and bind it to a named emitted field. For the deterministic fill twin,
an exact affected-fill count/price-difference rule is preferable to an unexplained effect threshold.

#### R5-02 — HIGH — the L4 comparator still changes estimator at the §4/§7 seam

**Fails:** §4.1 line 180; §4.2 lines 187–207; §7 lines 394–400; §12; L-21/P-15;
AMENDMENT-16.

§4.1 and §4.2 correctly define the unmodulated boundary as a constant per-symbol TRAIN median of the
same Parkinson-EWMA `ŝ` used by the modulated arm. §7 then says Wilder ATR20 is the
“deltaThreshold **and unmodulated-device normaliser**”. Those are different estimators with the
known 1.5–1.7× level seam. §12 contains no assertion that would catch an ATR implementation.

**Fix before implementation:** make §7 say ATR20 normalises `deltaThreshold` only; bind the
unmodulated devices to `ŝ_uncond` there; add a §12 HARD assertion that both L4 arms share estimator,
unit, clock, horizon scaling, and multiplier, differing only in conditional-vs-constant `ŝ`.

#### R5-03 — HIGH — the block rule is not inherited verbatim and remains under-specified

**Fails:** §1 lines 66–69; §8 lines 437–442; §8.1 lines 565–585; §12 line 764;
SPDR-018 §6.2 lines 247–250; L-20/INFR-004.

SPDR-018's live rule is:

1. aggregate to per-calendar-day sufficient statistics;
2. resample day-blocks of **`{1,3,7}` days**;
3. minimum block one day / 24 H1 bars;
4. take the min/max envelope over blocks × five seeds;
5. cap effective block `< n`.

SPDR-019 quotes only items 3–4 plus “a sweep”. The JSON repeats that shortened source rule. A missing
sweep/battery is declared HARD, which is good, but the implementer is still free to choose any sweep
and omit the daily aggregation and small-`n` cap while claiming compliance.

**Fix before implementation:** quote SPDR-018 §6.2 word for word in §8.1 and §12, including
`{1,3,7}`, daily sufficient statistics, `xen.evaluation.block_bootstrap_ci`, and effective block
`< n`; pin the same complete string in `resolution_basis.json`. Require emitted per-seed bound
spreads and per-block sensitivity, not just the final envelope.

#### R5-04 — HIGH — the pinned resolution JSON uses the wrong population and refutes the
horizon-flat claim

**Fails:** §8 lines 418–456; §8.1 predeclaration basis; P-25/L-53;
`results/resolution_basis.json`.

The JSON is labelled “all arms” and reports 138 cells / 36 distinct `n` in the 15k+ band. The design
states 26 / 8, which is the arm-C population. Both cannot be the pinned basis. On the arm-C basis the
26 / 8 disclosure is correct, but the horizon medians are 11.855 / 8.363 / 11.744, so the categorical
“`c` is FLAT across horizons” statement is false exactly at the target scale. The JSON does not emit
horizon breakdowns, so it cannot support or falsify the claim it is meant to pin.

The module also says the count of arithmetically excluded rows is returned, but it is not:
`_terms()` silently drops `n <= 1` and invalid denominators. This changes 23,700 eligible
`gross_n > 0` rows to 23,527 JSON-source rows without an exclusion count.

**Fix before implementation:** declare and enforce one population (arm C if 26 / 8 is intended);
emit filters, input-row count, retained-row count, exclusions by reason, horizon counts and
horizon-specific `c` summaries; regenerate the JSON; replace “flat” with the measured qualification.

#### R5-05 — HIGH — `expected_resolution.json` is a promissory note, not a predeclaration

**Fails:** §8 B-5 clauses 3–4; §8.1 lines 593–621; §12 line 767;
`design-requirements.md` §6; B-5; §15 artifact map.

`results/expected_resolution.json` does not exist. The new `xen.resolution_basis` module has no
function that can generate it. The design gives no schema, input hash, generation command, or
outcome-access fence, and §15 omits both resolution JSONs and the shared module. “COMPUTED AT RUN”
is not an expected `n` or MDE and directly contradicts “fixed, dated and committed before any read”.

Predeclaration by generation **can** be genuine: generated numbers are as predeclared as typed ones
when the deterministic method, frozen inputs, artifact hash, and timestamp are committed before
outcome access. None of that exists here yet. Naming a future path is not the declaration required
by design-requirements §6.

**Fix before implementation:** implement and test the deterministic generator; define the complete
per `(clock, delta, layer cell, symbol/pooled)` schema; use only frozen pre-outcome inputs; generate
and commit `expected_resolution.json` with source hashes, timestamp and no `COMPUTED AT RUN`
placeholders; list it and `resolution_basis.json` in §15. Then run fresh QA on the artifact.

#### R5-06 — MEDIUM — realised `c` exposes miscalibration but does not itself repair B-5

**Fails:** §8.1 lines 610–621 and §9's claim that the predeclared table “IS the protection”.

The emission-side rule is strong: every effect carries its realised CI/MDE and every aggregate
carries the resolution distribution. That directly prevents an unresolved covering CI from being
reported as a negative. Emitting realised `c` adds a useful calibration audit.

The claimed symmetry is overstated. An optimistic forecast can turn an unresolved null into a false
negative — the B-5 harm. A pessimistic forecast wastes resolved evidence; that is bad evidence
handling, but not the same false-negative mechanism. Because nothing acts on predeclared-vs-realised,
the comparison makes error visible after the fact; it does not prevent the reader from using the
wrong forecast. The defect class is relocated into report interpretation, not closed.

**Fix without a threshold:** state that all inference and every aggregate use the **realised**
CI/MDE/resolution curve only; treat predeclared-vs-realised solely as a calibration audit whose full
signed discrepancy distribution must be reported. If transport fails, say so and use the realised
curve—do not admit, drop, rank, or relabel any cell.

#### R5-07 — MEDIUM — the amendment tally is right, but L-23 is only half discharged

**Fails:** §14; `design-requirements.md` §12 lines 151–163; L-23.

Independent tally: **4 LOOSER / 7 TIGHTER / 5 NEUTRAL**, exactly as stated; AMENDMENT-11 is explicitly
superseded by AMENDMENT-15. The four-loosening streak is named and assessed, so that half of L-23 is
adequate.

The mandatory expected false-qualifier count under the **final** band set is still absent. The
ledger also says “five tightenings” after correctly counting seven and says AMENDMENT-2 is defensible
only with superseded AMENDMENT-11 rather than AMENDMENT-15. AMENDMENT-10 still falsely says 20 hours
is “beyond” `{4,12,24}`; the actual changes were adding 1 and dropping 24.

**Fix:** derive and state the final global-null false-qualifier expectation (including the declared
per-symbol/reporting expansion), then repair the three stale ledger sentences. This is disclosure,
not an auto-gate.

#### R5-08 — LOW — the phase-(b) “0.10 rung” remains a privileged adequacy cut

**Fails:** §4.3 lines 245–260; AMENDMENT-C7.

No `powered`, `unpowered`, `at_target`, or `NOT_RESOLVABLE` emitted field survives. `mde50`,
`mde80`, and `mde95` are descriptive points on one curve and are not gates as written. However,
phase (b) still summarises only the fraction above **0.10**, giving one ladder rung a canonical role
with no basis. It is reported rather than machine-gated, so this is not a hidden execution threshold,
but it is the exact blemish Run 4 identified.

**Fix:** report the fraction at every registered ladder rung (the six-number distribution), with no
single rung privileged.

#### R5-09 — LOW — required disclosure fields and artifacts remain unmapped

**Fails:** mandatory control block format (`design-requirements.md` §3); §12 span disclosure; §15;
Run-4 N-10/N-13/N-14.

The control blocks still omit the required collapse-fraction disclosure. §12 requires exact-span
statistics but §15 names no span columns. §15 also omits both resolution JSONs. The ≤240 count omits
the per-symbol disclosure expansion, and G1/G2 still state holds without the now-binding “hours”
unit (harmless on H1, but avoidable).

**Fix:** add collapse fraction to each applicable control block; name span and resolution fields and
artifacts in §15; disclose the per-symbol row expansion; write “1 hour” / “2 hours” in G1/G2.

### Checks independently verified clean

| Check | Result |
|---|---|
| Exact residual | **CLEAN.** Every target is `log R = log(W/L) − log((1−p)/p)`, slope 1. `0.9408` appears once and only to refuse it |
| Cost isolation | **CLEAN.** Cost enters no estimand, threshold, band or comparison; `p_be_net` is disclosure-only |
| Hold units/grid | **CLEAN in live rules.** §2 entry/exit, §4.1 L0 and §4.2 use hours on both clocks; `{1,4,12,20}` reaches the measured 19–23-hour scale |
| Counts | **CLEAN.** 37 = 1+4+5+3+20+4 per `(clock, δ)`; L4 = 20; 37×2×3 = 222 ≤ 240 |
| Pooled read | **CONDITIONALLY COMPLIANT.** Pooled primary reverts to disclosure-only if homogeneity does not support it; operator judges, no cell is dropped |
| Derangements | **CLEAN.** Both permutation controls require zero fixed points |
| Holdout / TEST / family action | **CLEAN.** TRAIN-only; no TEST/holdout query or family transition authorised |

### Standing execution blockers

Confirmed without re-litigation:

1. registered AMENDMENT-C6 still requires a predeclared phase-(b) trigger; this design substitutes
   post-(a) operator judgement. Operator must sign an amendment or restore a predeclared condition;
2. `reflection-inputs.md` §9 remains unsigned.

Both block **execution**, not implementation. They are separate from the Run-5 implementation
blockers above.

### Golden-trace and boundary verdict

Design-stage only: no code or smoke emission exists to diff. G1–G7 cover entry, expiry, suppression,
identity, exact mirror, exit precedence and leak discrimination. G6 remains non-executable until
R5-01 is fixed; G1/G2 need the unit cleanup in R5-09.

**FAILING_ARTIFACT:** `python/experiments/SPDR-019/design.md` plus its pinned resolution artifacts.  
**REQUIRED_SKILL:** `quant-designer`.  
**Implementation authorisation:** **NO.** R5-01 through R5-05 specify unresolved behaviour or a
missing pre-execution artifact that `screen_code/` would otherwise have to invent.

**What I did not reach:** I did not recompute the predicted M15/H1 event counts from the catalog,
because the promised per-stratum artifact does not exist and no generator specifies those inputs.
I did not audit SPDR-020.

## QA run 6 — 2026-07-29T04:56:38Z — mode: subagent — HEAD ac6d91c (clean tree)

**Reviewed git state:** `HEAD ac6d91c584d069a914e29050f33f2ecd6be6a706`, working tree clean
(`git status --porcelain` empty). Target: `python/experiments/SPDR-019/design.md` (1,202 lines).
**Stage:** DESIGN-STAGE. `screen_code/` absent — expected, not a finding.
**Independence:** fresh subagent context. I authored neither the design nor any of its fixes. Runs 4
and 5 were read in full. Every number below was recomputed by me from
`SPDR-018/results/analyst_per_cell_magnitudes.parquet` (sha256 `c06c58f5…`),
`SPDR-018/results/unit_pin.json`, the three committed resolution JSONs and the registry/reflection
sources. The design's prose was treated as an untrusted claim throughout.

**Verdict: REVISE.** **Implementation of `screen_code/` is NOT authorised.**

R5-01 … R5-09 are **all genuinely closed** — I could not break any of them. The block is a new,
narrower set: two clauses still force the developer to invent a design decision that changes
episode membership (R6-01, R6-02), and one control is not exit-matched for the path-dependent exits
the L4 stage exists to measure (R6-03).

Findings: **2 HIGH · 2 MEDIUM · 7 LOW.**

---

### PART A — run-5 closure, verified independently

| # | Run-5 finding | Status | Independent evidence |
|---|---|---|---|
| R5-01 | tripwires had no implementable pass rule | **CLOSED** | §6.1 now states, for each tripwire, named emitted fields and a boolean conjunction over counts and identities: TRIPWIRE-1 = `shift_is_exact_one_row == true AND changed_state_rows > 0 AND changed_selection_episodes > 0` (`design.md:465–472`); TRIPWIRE-2 = `count(clock_vs_m1_differing_fill_ids) > 0 AND count(favourable_precedence_differing_fill_ids) == count(both_reachable_bar_ids) > 0 AND` a per-id price-direction assertion (`:490–497`). No magnitude, no invented constant, every term computable from the emission. Direction is explicitly reported-not-required. This is a *structural discrimination* check rather than design-requirements §4's "expected collapse fraction", which is the correct substitution for a design whose null is an analytic zero line — there is no edge to collapse. Residue: G6 (R6-07), and a degenerate-equality trap (R6-06) |
| R5-02 | L4 comparator changed estimator at the §4/§7 seam | **CLOSED** | §4.1 L4 row reads "a fixed multiple of the **TRAIN-median ŝ per symbol** — the SAME estimator as the modulated arm" (`:182`); §7 divisor object 1 reads "This is the `deltaThreshold` normaliser **AND NOTHING ELSE** … never appears in any L4 arm" (`:509–516`); §12 carries a new HARD **L4 comparator identity** row asserting shared estimator/unit/clock/horizon-scaling/multiplier and making an ATR-derived exit boundary a hard failure (`:945`). All three now agree |
| R5-03 | block rule not inherited verbatim | **CLOSED** | I read SPDR-018 `design.md:245–252` myself. Its §6.2 is: (1) per-calendar-day sufficient statistics; (2) day-blocks `{1,3,7}`; (3) min block = 1 day = 24 H1 bars ≥ every horizon; (4) min/max envelope over blocks × seeds, 5-seed battery, `xen.evaluation.block_bootstrap_ci`, effective block capped `< n`. SPDR-019 §8.1 (`:706–715`) reproduces all four as five numbered clauses; §12 (`:943`) asserts all five separately and names each omission a hard failure; `resolution_basis.json.source_ci_rule` carries the same complete text. Residue is the string-equality mechanics only (R6-05) |
| R5-04 | basis on the wrong population; horizon-flat claim false | **CLOSED** | The JSON now declares `input_filter: {column: arm, operator: ==, value: C}` with full row accounting, and I reproduced every number (Part B). The categorical flatness claim is gone: §8 now says "**THE ARTIFACT REFUTES THAT AS A CATEGORICAL CLAIM AT THE TARGET SCALE**" and prints the measured 11.855 / 8.363 / 11.744 (`:549–555`); the JSON emits `horizon_summaries` per band and the string "flat" appears nowhere in it (asserted by `tests/test_resolution_basis.py:278`). The silent-drop defect is fixed: `_terms()` now tallies four exclusion reasons and `write_basis` raises if they do not sum to the drop count (`resolution_basis.py:103–108, 408–409`). Residue: the module docstring still asserts flatness (R6-09) |
| R5-05 | `expected_resolution.json` was a promissory note | **CLOSED** | The file exists, is dated `2026-07-29T00:00:00Z`, carries 5,148 rows, and its hashes reconcile against the files on disk *now*: `input_sha256.basis = 74c4b2b7…` = sha256 of the committed `resolution_basis.json`; `input_sha256.prior = 961cec28…` = sha256 of `expected_resolution_prior.json`; `source_sha256.generator_code = 2489bd5b…` = sha256 of `python/src/xen/resolution_basis.py`; `source_sha256.spdr018_analyst_per_cell_magnitudes = c06c58f5…` = sha256 of the parent emission. All four recomputed by me. No placeholder, no `COMPUTED AT RUN` string anywhere in the payload. `PYTHONPATH=src python -m pytest -q tests/test_resolution_basis.py` → **9 passed**, and two of those tests pin the committed artifacts rather than synthetic fixtures |
| R5-06 | realised `c` exposes but does not repair B-5 | **CLOSED as asked** | §8 (`:788–794`) and §9 (`:849–861`) now say explicitly that **all inference and every aggregate use the realised CI/MDE/resolution curve only**, that the predeclared-vs-realised pair is a calibration audit reported as a full signed discrepancy distribution, and that the two forecast errors are *not* equivalent in consequence. The overstated symmetry claim is withdrawn in the design's own words |
| R5-07 | L-23 half-discharged; three stale ledger sentences | **CLOSED** | Independent row-by-row tally (Part B) matches the stated `4 looser / 8 tighter / 5 neutral` and the active `3 / 7 / 5`. The false-qualifier expectation is now stated and its arithmetic is right. The three stale sentences are repaired: "the **seven** active tightenings" (`:1170`), AMENDMENT-2 defensible "ONLY WITH AMENDMENT-15 (which superseded AMENDMENT-11)" (`:1159`), and AMENDMENT-10 restated as "ADDS 1 hour and DROPS 24 hours; 20 is INSIDE the frozen range" (`:1069–1074`) |
| R5-08 | phase-(b) "0.10 rung" privileged | **CLOSED** | §4.3 now requires "the fraction of the (b) grid whose expected mde50 sits above **EACH** of the six registered ladder rungs … the whole six-number distribution" and states that no rung is privileged (`:341–347`) |
| R5-09 | disclosure fields/artifacts unmapped | **CLOSED** | Collapse fraction now in all four control blocks, including the mirror null's explicit `collapse_fraction: null, reason: POINT_NULL` (`:399–402, 417–418, 431–432, 448`); §15 names `span_exact_frac` / `span_p50` / `span_p90` and `collapse_fraction` on `metrics_by_cell`, and lists `resolution_basis.json`, `expected_resolution_prior.json`, `expected_resolution.json` and `python/src/xen/resolution_basis.py` (`:1186–1198`); §10 discloses the 5,148-row per-symbol expansion (`:879`); G1/G2 now say "1 HOUR" / "2 HOURS" (`:892, 897`) |

**Standing execution blocker 1 (AMENDMENT-7 vs registered C6) is DISCHARGED, and I verified this
against the registry, not the design.** `docs/signal-registry/candidate-families/cf-voldir-001.md`
C6 requires "the (b) trigger is **pre-declared before (a) runs** (deciding afterwards what counted
as promising is optional stopping)"; reflection §5.9.1's Trigger row says the same. §4.3 (`:297–316`)
now states the condition on the phase-(a) reads themselves, in the §9 CI-relative vocabulary, before
(a) runs. **No INFR-016 conflict:** the condition names no magnitude, admits/excludes/labels/ranks no
cell, drops nothing, and every phase-(a) cell is reported in full either way; phase (b) additionally
needs its own operator authority and its own design amendment, and the operator may decline a fired
trigger. That is a stopping rule on a phase, not a machine value gate. AMENDMENT-17's supersession
of AMENDMENT-7 is correctly booked and the ledger's active-row arithmetic reflects it.

---

### PART B — independent numeric audit

Recomputed with my own code from the parent emission (no reuse of the module under review for the
band table).

| Quantity | Design / artifact | My recomputation | Verdict |
|---|---|---|---|
| Source rows / arm-C matched / retained / excluded | 24,098 / 18,988 / 18,479 / 509 | **24,098 / 18,988 / 18,479 / 509** | REPRODUCES |
| Exclusions by reason | 509 missing_required_value, 0 / 0 / 0 | **509 / 0 / 0 / 0** | REPRODUCES |
| Row-accounting identity (§12) | `filter_matched − retained == excluded == Σ by_reason` | 18,988 − 18,479 = 509 = 509 | RECONCILES |
| 15,000+ band: cells / distinct `n` / bases | 26 / 8 / 3 | **26 / 8 / 3** (`pooled_raw`, `pooled_sigma_normalised`, `dose_response`) | REPRODUCES |
| 15,000+ horizon medians (h=4/12/24) | 11.855 / 8.363 / 11.744 on 6 / 14 / 6 cells | **11.8547 / 8.3628 / 11.7438** on **6 / 14 / 6** | REPRODUCES |
| Horizon spread at the target band | "1.42×" | 11.8547 / 8.3628 = **1.4176** | REPRODUCES |
| Band medians `c` (arm C) | JSON: 5.634 / 6.648 / 7.353 / 7.418 / 11.304 | **identical to 4 d.p.** | REPRODUCES |
| Arm-C pooled `n ≥ 10,000` | 0.053–0.107 over 41 cells | **0.05343–0.10680**, **41** cells | REPRODUCES |
| Three largest `n` | 20,977 / 20,572 / 20,279; 0.0727–0.0945 over 9 cells | **exact**; 9 cells, **0.07271–0.09447** | REPRODUCES |
| Per-horizon spans of those nine | h=4 0.078–0.094 · h=12 0.076–0.082 · h=24 0.073–0.090 | **0.0781–0.0945 · 0.0756–0.0823 · 0.0727–0.0904** | REPRODUCES |
| Cells reaching 0.03 | 0, other than three degenerate `n=2, p=0` | **exactly 3**, all `n=2, p=0` (min 0.01015) | REPRODUCES |
| Pooled H1 TRAIN bars | 229,646; MATIC 21,582; median 12,444; min 555 | **229,646** = Σ per-symbol `n` over 25 symbols; **21,582 / 12,444 / 555 (1000RATSUSDT)** | REPRODUCES |
| `25 × 21,648` | 541,200 | **541,200** | REPRODUCES |
| σ̂ pooled / plant rungs | 73.00 bps; 0.068 / 0.137 / 0.274 / 0.548 σ̂ | **73.0006**; 5/10/20/40 ÷ 73.0006 = **0.0685 / 0.1370 / 0.2740 / 0.5479** | REPRODUCES |
| Cell arithmetic | L4 = 3+3+2+2+4+4+1+1 = 20; 1+4+5+3+20 = **33**; 33 × 2 × 3 = **198**; +L5≤4 → **≤222**; 198 × 26 = **5,148** | all exact; `expected_resolution_prior.declared_axes.variant_id` holds **33** ids matching §4.1a name for name; `expected_resolution.json.row_count` = **5,148** with **5,148 distinct** grain tuples | REPRODUCES |
| L-23 false-qualifier disclosure | 2.5% → 4.95 of 198; 128.7 of 5,148 | 0.025 × 198 = **4.95**; 0.025 × 5,148 = **128.7** | REPRODUCES |
| Amendment tally | 4 looser / 8 tighter / 5 neutral (17 rows); active 3 / 7 / 5 | LOOSER {1,2,7,10}=4; TIGHTER {3,4,8,11,13,15,16,17}=8; NEUTRAL {5,6,9,12,14}=5; total 17; less superseded 7 and 11 → **3 / 7 / 5** | REPRODUCES |
| Reflection citations | E[run] 18.9–23.1, MAE ~12, class [D]; V9/V10 51–62%; V15 ΔBrier −0.1085 (k=12) vs −0.0199 (k=4); σ̂ 73.00 vs 13.03; cost floor 13.1–16.1 | verified verbatim at reflection `:150`, `:145–146`, `:151`, `:174`, `:180` | REPRODUCES |
| Registry text | C5 NARROWING; C6 pre-declared trigger + `NOT_RESOLVABLE` booking; C7 ladder `{0.02,0.03,0.05,0.075,0.10,0.15}`; no C8 | verified at `cf-voldir-001.md` C5/C6/C7 rows; the 2026-07-29 clarification row is scoped to HYP-D7 and to **SPDR-020's** trigger blocker only | CORRECT |
| Universe | prior scope axis = POOLED + 25 symbols | set- and order-identical to `docs/signal-registry/candidate-families/cf-voldir-001-universe.json`; the pinned hash is SPDR-014's `universe_recomputed.json` (`89b9ba96…`, verified) — see R6-11 | EQUAL, differently pinned |

**On question 4 — is the all-UNKNOWN predeclaration honest, or is it hiding an available forecast?**
It is honest, with one wording caveat. The generator's inputs are the declared axes, the universe pin
and the arm-C basis; it reads no episode, return or outcome of this experiment, and none exists. I
checked the parent claim directly: no emission in the programme carries a signal, fill or episode
count for the SoT §6.1 breakout at any `(clock, δ)` — SPDR-018's cells are the parents' own exit
geometries on different entry objects. The mechanism is not a blanket abstention either: SPDR-020's
sibling artifact carries two `KNOWN_PARENT_SIGNED_ARM` rows (`expected_n` 15,041 / 15,331), so a
prior is attached exactly where one exists. The caveat: a bar-level *signal-rate* forecast is in
principle computable from the catalog before any outcome is touched, so "an invented number" (`:771`)
overstates it — the accurate statement is that any such count requires running this entry, which
cannot precede the predeclaration. Since nothing consumes the forecast (all inference uses the
realised curve), the all-null table costs the reader nothing. **Not a finding on its own; but §8 then
contradicts itself in prose — R6-04.**

---

### PART C — findings

#### R6-01 — HIGH — the R-MARKOV k=4 / k=12 gate reads a forecast no parent ever emitted, so the HARD parent-gate provenance check cannot be satisfied as written

**Fails:** `design.md:216–219` (§4.1a parent rows — *"These layers consume forecasts already emitted
by registered parents"*); `design.md:948` (§12 HARD **Parent-gate provenance**); §4.1 L2 row (`:180`);
`design-requirements.md` §1/§2.

I searched every emitted parquet under `SPDR-015/017/018/results/`. Three of the four pinned gates
resolve to real emitted series:

- `s_hmm_rv` — `SPDR-015/results/regime_states.parquet` (H1, 25 symbols, 212,224 rows spanning
  2021-06-29 → 2023-12-17, i.e. the whole TRAIN fence). **Available.**
- `T-GT-CUR` / `logit_ridge` and `T-GT-MED5` / `ridge_cont` — `SPDR-015/results/zz_ordinal.parquet`
  (82,377 rows, `p` and `pred_cont` per swing, H1, 25 symbols, targets `T-GT-CUR` / `T-GT-MED5` /
  `T-GT-MED10`). **Available.**
- **R-MARKOV k=4 / k=12 `logistic_ridge` — NOT emitted anywhere.** The forecast is computed inside
  `SPDR-015/screen_code/transitions.py` (`_logistic_ridge_fit`, `:85`; `FORECAST_METHODS` at
  `config.py:82`) and only *skill metrics* were persisted (`transition_metrics.parquet` — accuracy,
  Brier, log-loss per symbol × model × k). `regime_states.parquet` carries `s_markov`,
  `n_high_4_markov`, `n_high_12_markov`, `dur_markov` — states and counts, **not** the
  `P(HIGH_{t+k}) ≥ 0.5` forecast the design fires on.

So a developer implementing §4.1a must re-fit the parent model and choose its feature set, ridge
alpha, training window and OOS fold protocol — none of which SPDR-019 states — while §12 asserts as
a **hard failure** that the gate "reads exactly the model/field/rule pinned in §4.1a". This decides
membership of `L2_LEVEL_RMARKOV_K4`, `L2_LEVEL_RMARKOV_K12`, `L2_JOINT_HMM_HIGH_AND_K12_HIGH` and
`L2_INTERACTION_HMM_X_K12` — 4 of the 5 L2 variants and the whole of prediction 4.

**Required fix (quant-designer).** For each of the four gates, name the **source artifact path and
column**. For R-MARKOV, either (a) point at `SPDR-015/screen_code/transitions.py` with its frozen
config and state that the forecast is regenerated under it, unchanged, on the H1 decision grid — with
the fit window and causality stated — or (b) substitute an emitted field (`s_markov` /
`n_high_{4,12}_markov`) and restate the firing rule against it. Then make §12's provenance row check
the named path+column.

#### R6-02 — HIGH — L1's ŝ-decile cuts have no declared reference population and no declared causality

**Fails:** `design.md:179` (§4.1 L1 — *"4 (ŝ-decile cuts d≥5, d≥7, d≥9, and the ŝ-continuous rank
reported as a dose-response)"*); §3 OBJECT-IDENTITY (`:152–155`); §12 Causality row (`:936`) and
**L1 fixed-entry subset** row (`:944`).

Deciles of *what*? Per symbol or pooled across the 25? Over the full TRAIN band, or an expanding
causal window ending at `t−1`? The design says only that ŝ itself is causal `≤ t−1`. Both open
choices are verdict-material:

- **Population:** pooled deciles on a 25-symbol panel with σ̂ running 13 → 129 bps per symbol are
  largely a *symbol* selector, not a scale selector; per-symbol deciles are not. The two produce
  different `L1` populations and therefore different `p`, `W`, `L` and `n` on every L1 row.
- **Causality:** full-TRAIN decile boundaries use the whole sample's ŝ distribution to decide which
  episodes are kept — a cross-sectional look-ahead into the selection rule. §12's causality assertion
  covers state *indices*, not threshold estimation, so nothing in the checklist would catch it. The
  §12 subset check catches only "did ŝ move the entry", which is a different failure.

The same gap applies to the `ŝ-continuous rank` variant (rank within what?) and to the
magnitude-matched comparator's `|decision-bar move| decile` (`:439`).

**Required fix (quant-designer).** State, for the L1 axis, the ŝ-decile reference population
(per-symbol recommended, stated either way) and the estimation window (causal expanding, ≤ t−1, with
a declared minimum history), and the identical convention for the continuous rank and for the M-3
comparator's magnitude deciles; add a §12 assertion that decile boundaries use no data dated at or
after each episode's decision bar.

#### R6-03 — MEDIUM — the side and entry-timing derangements are not exit-matched, so on every path-dependent L4 arm the control's null is mechanically wrong

**Fails:** `design.md:404–421` (CONTROL SIDE-DERANGEMENT — *"deranging the side flips the sign of
r"*), `:423–433` (CONTROL ENTRY-TIMING DERANGEMENT); **L-24 clause 2 / F04** (exit-matched nulls),
which `qa-compliance` §3 makes binding on any multi-cell design; §2 exit fill rules (`:128–134`).

On the L0 / time-exit arms a side flip does negate `r` exactly, and the block as written is correct
there. On the L4 **target** and **trail** arms it is not: which barrier is reached, and when, depends
on the side. A LONG episode stopped out by its trail becomes, under a flipped side, a SHORT episode
whose target may fire at a different M1 bar and a different price. Negating `r` therefore fabricates
a null distribution no strategy could realise, on precisely the arms whose payoff asymmetry the L4
stage exists to measure. The entry-timing block has the mirror problem: "holding length and side
preserved" does not say whether the deranged episode's exit path is re-resolved on M1 or its old `r`
is transplanted.

**Required fix (quant-designer).** State in both control blocks that on any arm carrying a target or
trail the deranged twin **re-resolves the exit path on the M1 stream** under the deranged side /
timestamp, using §2's adverse-precedence rule unchanged; permit sign negation only on time-exit-only
arms and say so; add a §12 assertion that the deranged arm's exit-reason mix is recomputed, not
inherited.

#### R6-04 — MEDIUM — §8 still asserts, in the present tense, the population forecast the predeclaration declares UNKNOWN and §8.1 says was withdrawn

**Fails:** `design.md:579` (*"the 15,000+ band — **where the M15 pooled strata land**"*) and
`:583–584` (*"at c = 5.4 the 0.03 rung needs 32,400 episodes and **this design predicts 50k-60k for
its primary stratum**"*) against `:770–772` (*"the withdrawn '~13-16k on H1 / ~50-60k on M15' figures
were exactly that: a date-range-shaped guess (M-4)"*) and against
`expected_resolution.json`, where all 5,148 rows carry `expected_n: null`.

The arithmetic in the paragraph is right — `(5.4/0.03)² = 32,400` — but the design cannot both
withdraw the 50–60k forecast as an M-4 violation and use it as a live premise 190 lines earlier. This
is the exact shape M-4 exists to stop, and it is the number a downstream analyst would quote. The
`c = 5.4` anchor is also stale: on the arm-C basis the smallest band median is **5.634**, so 5.4 is
now a value from the superseded all-arms computation.

**Required fix.** Rewrite the withdrawal paragraph so it contains no live `n` prediction — state the
crossing `n` at the measured band endpoints (`(5.634/0.03)² = 35,268`, already in the artifact's
`required_n_by_band`) and say that whether any stratum reaches it is unknown until measured. Same for
"where the M15 pooled strata land".

#### R6-05 — LOW — §12's block-rule string-equality check has no canonical string to compare against, and the JSON's "verbatim" string is not verbatim

`design.md:943` requires "The rule string asserted here must equal `source_ci_rule` in
`results/resolution_basis.json`", but §8.1 states the rule as a five-clause list, not as a literal.
The only literal in the repository is the JSON's own field, so the check as written is either
self-comparing or requires the developer to compose the canonical string. Separately, that field is
labelled *"SPDR-018 §6.2, verbatim:"* and then appends "emit per-seed bound spreads and per-block
sensitivity", which is SPDR-019's own requirement and appears nowhere in SPDR-018 `design.md:245–252`.
**Fix:** make §12 a clause-by-clause check of the five clauses (each independently asserted, as §12
already promises), and relabel the JSON string as "SPDR-018 §6.2 (clauses 1–5 verbatim) plus this
design's emission requirement".

#### R6-06 — LOW — TRIPWIRE-2's equality clause false-fails on a degenerate but legal case

`design.md:492` requires `count(favourable_precedence_differing_fill_ids) == count(both_reachable_bar_ids) > 0`.
If a target price and a trail level coincide inside an M1 bar, the two twins fill at the same price,
the id does not enter the differing set, the counts diverge, and a **HARD** check fails on a correctly
implemented screen. **Fix:** define the differing set by price inequality and require
`count(both_reachable) − count(differing) == count(price_identical)`, with `price_identical` emitted.

#### R6-07 — LOW — G6 still asks QA to confirm a "material difference"

`design.md:923`. §6.1's TRIPWIRE-1 is now structural, so the golden trace should be too, otherwise
the trace QA computes at execution has no criterion. **Fix:** restate G6 as the structural comparison
— the G1 episode's conditioning row differs by exactly one decision-clock shift, its selection or exit
placement changes, and the emitted variant is the legal one.

#### R6-08 — LOW — the predeclaration grain omits the band axis the design scores

`expected_resolution.json` grain is `(clock, delta, variant_id, scope)`; §10 (`:874`) scores DESIGN and
CONFIRM as verification bands alongside full TRAIN, and §12 (`:952`) requires the predeclared values
to ship on the **same row** as the realised ones in `resolution_ladder.parquet`. If that ladder carries
a band column the join key is under-specified. Harmless today because every predeclared value is null,
but it is a schema the developer must otherwise invent. **Fix:** state the join key explicitly (or add
`band` to the grain and regenerate — which would require fresh QA, per §12).

#### R6-09 — LOW — the shared module still asserts the withdrawn flatness claim

`python/src/xen/resolution_basis.py:22`: *"`c` is flat across holding horizons — `block_mde_bps` and
`(1-p)*L` both rise with `h` and cancel"*. AMENDMENT-17(d) withdrew exactly this, the artifact refutes
it at the target band (1.42×), and the test suite bans the word from the JSON but not from the module.
The design pins this module as its authority in §15. **Fix:** correct the docstring to match
`horizon_interpretation` in the emitted artifact.

#### R6-10 — LOW — the modulated sizing arm's constant is undefined

`design.md:240`: modulated sizing is `c / ŝ` with `c` unstated. Sizing changes `W` and `L` (not `p`),
so it does move `log R`, which is why the design forbids a sizing cell carrying a `log R` claim — but
the developer still has to pick `c`. **Fix:** pin the normalisation (e.g. `c` = per-symbol TRAIN-median
ŝ, so mean weight is 1 and the arm is comparable to the fixed-notional twin).

#### R6-11 — LOW (informational) — the predeclaration pins a different file from the one §10 names as the universe pin

`expected_resolution.json.source_sha256.spdr014_universe_recomputed = 89b9ba96…` is the sha256 of
`python/experiments/SPDR-014/results/universe_recomputed.json`, whereas §10 (`:871`) names
`cf-voldir-001-universe.json` as the pin. I verified the 25 symbols are identical **and identically
ordered** in both files and in the prior's `scope` axis, so nothing is wrong substantively. **Fix:**
pin the family universe file itself, or record the equivalence in the prior.

**Advisory (not a finding):** §12's fixed-entry-subset assertion (`:944`) covers L1 only. L2 and L3
are also selection layers on the same frozen entry; extending the same subset assertion to them is
free and closes the symmetric failure.

---

### Checks independently verified clean

| Check | Result |
|---|---|
| Exact mirror, slope 1 | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` in §1, §4.1, §5, §8, §9, §12, G4, G5, §13. `0.9408` appears once (`:371`) and only to refuse it, with the correct reason. §12 makes a fitted-slope residual a hard failure |
| Cost isolation (C5) | **CLEAN.** Header NOTE, §5 DISCLOSED REFERENCE ONLY, §7 (`:525–527`), §12 HARD row, §13 first bullet, §15 column flag. No band, threshold or comparison carries a cost term |
| SPREAD-COST-DISCLOSURE | **CLEAN.** All five fields verbatim per `design-requirements.md` §10, unchanged across six runs |
| No adequacy flag / no canonical threshold | **CLEAN.** §12 asserts the absence HARD; ladder `{0.02,0.03,0.05,0.075,0.10,0.15}` matches registered C7 exactly; `mde50/mde80/mde95` are three points of one curve; the committed predeclaration contains none of `powered`/`unpowered`/`at_target`/`not_resolvable` (asserted by test) |
| Phase-(b) trigger vs C6 / reflection §5.9.1 / INFR-016 | **CLEAN.** Pre-declared before (a), stated on the (a) reads, no magnitude, nothing machine-dropped, operator authority still required. Execution blocker 1 discharged |
| Block rule vs SPDR-018 §6.2 | **CLEAN on substance.** All five clauses present in §8.1 and §12 and in `source_ci_rule`; the mechanics of the equality check are R6-05 |
| Basis population | **CLEAN.** One declared population (`arm == 'C'`), accounting reconciles, exclusions tallied by reason, generator raises if they do not sum |
| Predeclaration integrity | **CLEAN.** Dated, hash-pinned on four inputs (all four recomputed and matching), 5,148 distinct strata, no placeholder, no outcome input, generator deterministic and tested (9/9 pass) |
| Cell arithmetic | **CLEAN.** 33 named variants = the 33 in the prior; 198 fixed cells; 5,148 disclosure rows = the artifact's row count |
| L-23 ledger | **CLEAN.** Direction on every row, tally correct, active tally correct after two supersessions, streak flagged for the operator, false-qualifier expectation stated with correct arithmetic |
| L-28 derangements | **CLEAN.** Both permutation controls declare and count zero fixed points; TRIPWIRE-1 correctly declares N/A (index shift, not a permutation) |
| L-50 / P-21 | **CLEAN.** Plant rungs in σ̂ units, re-derived per universe at run; recomputed against σ̂ = 73.0006 |
| L-21 / P-15 unit pin | **CLEAN.** Divisor object 2 matches `SPDR-018/results/unit_pin.json.divisor_object` verbatim; ATR20 bound to `deltaThreshold` only; medians computed at run |
| M-4 effective coverage | **CLEAN in §8** (229,646 measured, not date-arithmetic) and asserted in §12. Residue is the prose contradiction R6-04 |
| Governance "name the mechanism" (chapter-06 §1) | **SATISFIED.** §1 names forecastable move *scale* placing the exit boundaries as the mechanism putting `R > 1`; whether it persuades is the operator's call, not QA's |
| L-51 HARD status | **DEFENSIBLE.** HARD on presence and form only; re-anchored to every separately reported subset; `chapter-06-governance.md:101` makes it mandatory |
| Holdout / TEST / XENA / family action | **CLEAN.** TRAIN-only; §12 asserts zero queries ≥ 2025-01-08; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| L-52 / P-23 | **CLEAN.** Check-count reconciliation by name; every check bound to an emitted artifact; determinism unconditional at `--jobs > 1` |
| Lane compliance (`spdr-lane.md`) | **CLEAN.** TRAIN-only, causal `t−1`, M1 fill resolution, ≥2000-seed control batteries (lane floor is 25), per-stratum reporting with multiplicity disclosed, pooled reverts to disclosure-only without homogeneity, no local accounting, dependence-matched CI |
| Shared-code boundary | **CLEAN.** `python/src/xen/resolution_basis.py` contains no threshold and no admit/exclude/label/rank path; `required_n` and `mde50` are pure conversions; 9/9 tests pass, two of them pinning the committed artifacts |

---

### Standing execution blockers

1. **DISCHARGED** — the AMENDMENT-7 / registered-C6 departure. Verified against
   `cf-voldir-001.md` and reflection §5.9.1, not against the design's assertion.
2. **STANDS** — `reflection-inputs.md` §9 remains explicitly unsigned ("OPERATOR DECISION NOT TAKEN
   … deliberately blank"). This blocks **execution**, not implementation.
3. **STANDS (lane-wide, unchanged)** — the per-symbol spread pin is open; every money read stays
   blocked. It does not block this measurement (C5).

### Golden-trace and boundary verdict

Design-stage: no code and no smoke emission to diff. G1–G7 cover entry, expiry, suppression, the
identity, the exact mirror, exit precedence and leak discrimination, and G1/G2 now carry hour units.
G7 is deterministic and computable by QA from the catalog. G6 remains non-executable until R6-07.

**FAILING_ARTIFACT:** `python/experiments/SPDR-019/design.md`
(the pinned resolution artifacts and `python/src/xen/resolution_basis.py` are clean apart from the
R6-09 docstring).
**REQUIRED_SKILL:** `quant-designer`.
**Implementation authorisation: NO.** R6-01 and R6-02 each force the developer to invent a decision
that changes which episodes exist in a cell; R6-03 leaves a control's null undefined on the arms the
experiment is built to measure. R6-04 … R6-11 are prose, schema and hygiene and change no line of
code.

**What I did not reach.** I did not recompute M15 or H1 episode counts from the catalog — no parent
emission carries them and the design correctly declares them unknown. I did not audit
`xen.evaluation.block_bootstrap_ci`'s internals beyond the L-20 contract. I did not review SPDR-020,
which shares `resolution_basis.py`, the block rule and the control blocks — R6-03, R6-05 and R6-09
are likely to apply there verbatim.

---

## QA run 7 — 2026-07-29T05:15:22Z — mode: subagent — HEAD 112242c (clean tree)

**Reviewed git state:** `HEAD 112242c8b6fc81e86116699e567e9bfea941b3ba`, working tree clean.
Target: `python/experiments/SPDR-019/design.md` (1,314 lines).
**Stage:** DESIGN-STAGE. `screen_code/` absent — expected, not a finding.
**Independence:** fresh subagent context. I authored neither the design nor any of its fixes. Run 6
was read in full, run 5 skimmed. Every number below was recomputed by me from
`SPDR-018/results/analyst_per_cell_magnitudes.parquet`, `SPDR-015/results/{regime_states,
zz_ordinal,transition_metrics}.parquet`, `SPDR-015/screen_code/{transitions,features}.py`,
`SPDR-018/design.md` §6.2, the three committed resolution JSONs, and the registry/reflection
sources. The design's prose was treated as an untrusted claim throughout. For R6-01 I did not stop
at reading the parent code — I **executed** the proposed regeneration route.

**Verdict: APPROVE.** **Implementation of `screen_code/` IS authorised.**

R6-01 … R6-11 are **all genuinely closed**. R6-01, the largest of them, is closed by construction
rather than by assertion: I ran the parent's own frozen function over the parent's own emitted
columns and reproduced its published skill metric **exactly** (see Part A). Six new findings remain
— one check-convention gap, one stale provenance hash, one ledger row, one prose overclaim, one
citation-accuracy issue and one wrong number-word. **None of them forces the developer to invent an
estimand, a population, a comparator or an integrity check**; all six are fixable during or after
implementation without touching a line of screen logic. Under the pipeline's own standard that is
an APPROVE.

Findings: **1 MEDIUM · 5 LOW.** No HIGH. No REJECT-class issue.

---

### PART A — run-6 closure, verified independently

| # | Run-6 finding | Status | Independent evidence |
|---|---|---|---|
| R6-01 | R-MARKOV gate reads a forecast no parent emitted | **CLOSED — verified by execution** | §4.1a now names, per gate, the source artifact **and column**. I checked each against the emission: (i) `s_hmm_rv` exists in `SPDR-015/results/regime_states.parquet` (H1: 212,224 rows, 25 symbols) with values `{0: 149,121, 1: 52,954, −1: 10,149}` — the design's `< 0 means NO STATE, INELIGIBLE, never coerced to LOW` matches the real value domain; (ii) `zz_ordinal.parquet` carries `target`, `model`, `p`, `pred_cont`, `threshold`, `confirm_slot_end` — every field the T-GT-CUR / T-GT-MED5 rules name; (iii) the R-MARKOV route: `walk_forward_probs(state, X, slot_end, is_origin, k)` exists at `transitions.py:170` with **exactly** that signature; the feature matrix is `_feature_matrix_for_model(cols,'R-MARKOV')` at `:134`, whose eight inputs are `s_markov, dur_markov, rv20, park_ewma, lvl_pct, n_high_4_markov, n_high_12_markov, s_shock` — **name for name the list §4.1a pins**, and all eight are emitted in `regime_states.parquet`. Causality: `_n_high_last_k` (`features.py:96–105`) windows `[i−k+1, i]` — backward-looking, as claimed; the forward-looking `run_len_markov` / `run_len_hmm` are in the artifact but **excluded from the feature matrix** and named in the FORBIDDEN list. `run_screen.py:289–311` emits the same frame, in the same row order, that `transitions.py:478` builds `cols` from, so the regeneration is exactly reproducible. **I ran it.** For 1000BONKUSDT and 1000LUNCUSDT at k=4 and k=12 the regenerated `delta_brier_vs_pers` matched the parent's published value with **diff = 0.0** (bit-identical, not merely within 1e-9). The parity check is therefore both meaningful (Brier over the whole OOS probability vector is a checksum of that vector — any differing probability moves it far above 1e-9) and achievable. Residue: the NaN case, R7-01 |
| R6-02 | L1 deciles had no reference population and no causality | **CLOSED** | New §4.1b (`design.md:271–299`) pins all four: POPULATION per symbol (with the 13→129 bps σ̂ rationale); WINDOW expanding and causal, quantiles over bars **strictly before** `[0]`, full-TRAIN edges explicitly refused as "a look-ahead that survives a fence check"; WARM-UP 250 prior H1 ŝ values, sub-warm-up events INELIGIBLE for L1 rows only, counted with reason, retained everywhere else; CONTINUOUS rank on the same per-symbol expanding empirical rank; and the M-3 magnitude deciles bound to the identical rule. §12 adds a HARD **Decile causality** row (`:1049`) making a pooled or full-TRAIN edge a hard failure. Both open choices run 6 named are now closed, and closed the way run 6 recommended |
| R6-03 | derangements not exit-matched on path-dependent arms | **CLOSED** | §6 carries a new binding block, **EXIT-MATCHING, BINDING ON BOTH DERANGEMENTS** (`:472–480`): the deranged side/timing is applied first, then entry fill, barrier levels and exit are **re-resolved from M1 exactly as §2 specifies**, and `r` is computed from the re-resolved fills; sign negation is PERMITTED ONLY on time-exit arms and asserted per arm; a device whose null cannot be exit-matched is demoted to DISCLOSURE and labelled. §12 adds a HARD **Exit-matched nulls** row (`:1050`). The mechanism run 6 described (side decides which barrier is hit and when) is now the design's own stated reason |
| R6-04 | live 50–60k prediction contradicted the all-null predeclaration | **CLOSED** | Both live premises are gone. `:662–669` now reads "WHICH band this design's strata land in is **NOT predicted** — no `n` is forecast anywhere (§8.1), so the band is assigned from the realised `n` when it exists", and the `c = 5.4` anchor and the 50–60k figure appear **only** inside the withdrawal sentence, with the artifact-checked reason ("`c = 5.4` appears nowhere in the arm-C artifact (its smallest band median is 5.634)"). I confirmed 5.634 from the JSON: band `0-100`, `c_median = 5.6339`. The crossing point is now read off `required_n_by_band`, not typed. `grep` over the whole design finds no surviving live `n` forecast |
| R6-05 | block-rule check had no canonical string; JSON string not verbatim | **CLOSED** | §8.1 now declares a **six-clause canonical literal** (`:790–806`) and §12 (`:1048`) checks it "**clause by clause against §8.1's canonical six-clause list** (never by string equality), because a string comparison fails on whitespace and passes on a paraphrase". I diffed the JSON's `source_ci_rule` against `SPDR-018/design.md:245–252` myself: the quoted text is now SPDR-018 §6.2's three bullets **and nothing else** — the appended "emit per-seed bound spreads" sentence run 6 flagged is gone, and §8.1/§12 both state that this design's extra emission requirement is deliberately outside the pinned string. All six clauses map onto SPDR-018 §6.2's content with no addition and no loss |
| R6-06 | TRIPWIRE-2 equality clause false-fails on coincident prices | **CLOSED** | `:570–574` now defines `both_reachable_bar_ids` as counting **only** M1 bars where target and trail/stop are DISTINCT prices, and adds `price_identical_bars`, "counted separately … never as a failure" — exactly run 6's fix |
| R6-07 | G6 asked QA to confirm a "material difference" | **CLOSED** | G6 (`:1025–1029`) is now the structural comparison: `shift_is_exact_one_row`, `changed_state_rows > 0`, `changed_selection_episodes > 0`, and that the legal variant entered the emission — with "No magnitude is asserted: the payoff delta is reported and carries no pass rule" |
| R6-08 | predeclaration grain omitted the band axis | **CLOSED** | §8.1 **BAND AXIS AND THE JOIN KEY** (`:871–876`) states the predeclaration is at the full-TRAIN grain, that DESIGN/CONFIRM carry `band` as a fourth **reporting** column and join on `(clock, delta, variant_id, scope)` alone — and honestly notes the join is exact *only because* every predeclared value is null. The developer no longer invents the schema |
| R6-09 | module docstring asserted the withdrawn flatness claim | **CLOSED** | `git show 112242c -- python/src/xen/resolution_basis.py`: the docstring now reads "The derivation EXPECTS `c` to be flat … but that is a hypothesis, not a result: on SPDR-018's arm-C cells the 15,000+ band's horizon medians are 11.855 / 8.363 / 11.744, a 1.42× spread … no caller may assume flatness". Matches `horizon_interpretation` in the artifact. This fix is what created R7-02 |
| R6-10 | modulated sizing constant undefined | **CLOSED** | §4.2 (`:308`) now pins it: `N0 × (ŝ_uncond / ŝ(t,h))`, clipped `[0.25, 4]`, with the constant pinned to `N0 × ŝ_uncond` per symbol — run 6's recommended normalisation. Residue is the prose claim attached to it, R7-04 |
| R6-11 | predeclaration pinned a different universe file from §10's | **CLOSED** | §8.1 **UNIVERSE PIN** (`:878–882`) states both files, and §12 adds a HARD **Universe file equality** row (`:1052`) asserting set equality before the run, with regeneration-and-re-review rather than hand reconciliation if they differ. I verified independently: the prior's `scope` axis minus `POOLED` is set-identical to both `cf-voldir-001-universe.json` and `SPDR-014/results/universe_recomputed.json` (25 symbols, both `True`) |
| *(advisory)* | subset assertion covers L1 only | **NOT TAKEN UP** | §12's **L1 fixed-entry subset** row (`:1053`) is still L1-only. Restated as Advisory 1 below; it was advisory in run 6 and stays advisory |

---

### PART B — independent numeric audit

Recomputed from the parent emission with my own code, not the module under review.

| Quantity | Design / artifact | My recomputation | Verdict |
|---|---|---|---|
| Basis row accounting | 24,098 → 18,988 (`arm == 'C'`) → 18,479 retained, 509 excluded | **24,098 / 18,988 / 18,479 / 509** | REPRODUCES |
| Exclusions by reason | 509 `missing_required_value`, 0 / 0 / 0 | **509 / 0 / 0 / 0** | REPRODUCES |
| §12 accounting identity | `filter_matched − retained == excluded == Σ by_reason` | 18,988 − 18,479 = 509 = 509 | RECONCILES |
| 15,000+ band | 26 cells, 8 distinct `n`, 3 bases | **26 / 8 / 3** (`pooled_raw`, `pooled_sigma_normalised`, `dose_response`) | REPRODUCES |
| 15,000+ horizon medians | 11.855 / 8.363 / 11.744 on 6 / 14 / 6 cells | **11.8547 / 8.3628 / 11.7438** on **6 / 14 / 6** | REPRODUCES |
| Horizon spread "1.42×" | 1.42 | 11.8547 / 8.3628 = **1.4176** | REPRODUCES |
| Smallest band median (the 5.4 refutation) | 5.634 | JSON band `0-100` `c_median` = **5.6339** | REPRODUCES |
| Full band table | 5.634 / 6.648 / 7.353 / 7.418 / 11.304 | **5.6339 / 6.6475 / 7.3528 / 7.4177 / 11.3036** over bands `0-100 / 100-1,000 / 1,000-5,000 / 5,000-15,000 / 15,000-inf` | REPRODUCES |
| Arm-C `n ≥ 10,000` | 0.053–0.107 over 41 cells | **0.05343–0.10680**, **41** cells | REPRODUCES |
| Three largest `n` | 20,977 / 20,572 / 20,279; 0.0727–0.0945 over 9 cells | **exact**; 9 cells, **0.07271–0.09447** | REPRODUCES |
| Per-horizon spans of those nine | h=4 0.078–0.094 · h=12 0.076–0.082 · h=24 0.073–0.090 | **0.0781–0.0945 · 0.0756–0.0823 · 0.0727–0.0904** | REPRODUCES |
| Cells reaching 0.03 | 0, other than three degenerate `n=2, p=0` | **exactly 3**, all `n = 2, p = 0` (0.01015 / 0.01189 / 0.01523) | REPRODUCES |
| `source_ci_rule` vs parent | "SPDR-018 §6.2's own text and nothing else" | diffed against `SPDR-018/design.md:245–252`: three bullets, verbatim, **no addition** | REPRODUCES |
| Cell arithmetic | L4 = 3+3+2+2+4+4+1+1 = 20; 1+4+5+3+20 = **33**; 33 × 2 × 3 = **198**; 198 × 26 = **5,148** | all exact; `declared_axes.variant_id` holds **33** ids matching §4.1a **name for name**; axes 2 × 3 × 33 × 26 | REPRODUCES |
| Predeclaration integrity | 5,148 strata, all UNKNOWN, no placeholder | `row_count` **5,148**, **5,148 distinct** grain tuples, **5,148/5,148** `UNKNOWN_NO_PARENT_MEASURED_POPULATION`, **0** non-null `expected_n`, **0** non-null `expected_mde50`; payload contains none of `computed at run`, `placeholder`, `l5_slot`, `powered`, `unpowered`, `at_target`, `not_resolvable` | REPRODUCES |
| §12 `input_sha256.basis` assertion | equals sha256 of committed `resolution_basis.json` | pinned `c1c560bb7934…` = actual `c1c560bb7934…` | HOLDS |
| Generator provenance pin | `source_sha256.generator_code` | pinned `2489bd5b…`, **actual `72c6b1f9…`** | **MISMATCH → R7-02** |
| Prior pin | `input_sha256.prior` | pinned `961cec28…` = actual `961cec28…` | HOLDS |
| Parent emission pin | `spdr018_analyst_per_cell_magnitudes` | pinned `c06c58f5…` = actual `c06c58f5…` | HOLDS |
| Universe set equality | prior scope ≡ family pin ≡ SPDR-014 recompute | 25 symbols, both comparisons `True` | HOLDS |
| §12 HARD-check count | "EXPECTED HARD-CHECK COUNT: **28**" | I counted the named list: check-count, TRIPWIRE-1, TRIPWIRE-2, TRAIN fence, holdout, causality, fill causality, universe pin, identity reconstruction, log R definition, cost isolation, derangement fixed-point count, golden traces, determinism, block rule, L4 comparator identity, parent-gate provenance, parent-gate parity, decile causality, exit-matched nulls, L1 fixed-entry subset, MOD-hold eligibility, predeclaration present, basis population, universe file equality, L-51 selection check, log R never unaccompanied, predeclared-vs-realised = **28**. Every one has its own row in the §12 table | REPRODUCES |
| L-23 tally | 4 looser / 8 tighter / 5 neutral (17 rows); active 3 / 7 / 5 | LOOSER {1,2,7,10}=4; TIGHTER {3,4,8,11,13,15,16,17}=8; NEUTRAL {5,6,9,12,14}=5; total **17**; less superseded 7 and 11 → **3 / 7 / 5** | REPRODUCES (but see R7-03) |
| False-qualifier disclosure | 2.5% → 4.95 of 198; 128.7 of 5,148 | 0.025 × 198 = **4.95**; 0.025 × 5,148 = **128.7** | REPRODUCES |
| Registry C6 / C7 | pre-declared (b) trigger; ladder `{0.02,0.03,0.05,0.075,0.10,0.15}`; no `NOT_RESOLVABLE` flag anywhere | verified verbatim at `cf-voldir-001.md` rows dated 2026-07-28. §4.3's reconciliation (C7 supersedes the *flag*, not the *obligation*; the six-rung distribution is reported instead) is a disclosed, defensible reading of a genuine conflict between two registered amendments | CORRECT |
| M1 lane exists | `data/catalog/`, T1 lane | `data/catalog/data/bar` holds **903** `…-1-MINUTE-LAST-EXTERNAL` catalogs | HOLDS |
| `xen.evaluation.block_bootstrap_ci` | named in the block rule | exists, `src/xen/evaluation.py:59` | HOLDS |
| `tests/test_resolution_basis.py` | tested and re-runnable | `PYTHONPATH=src python -m pytest -q tests/test_resolution_basis.py` → **9 passed** in 0.39s | PASSES |

**On the R-MARKOV regeneration, executed rather than argued.** Running
`walk_forward_probs` + `metrics_row` on `regime_states.parquet` for four symbols at k=4 and k=12:

```
1000BONKUSDT  k=4   emitted -0.02304579816015967   regen -0.02304579816015967   diff 0.0
1000BONKUSDT  k=12  emitted -0.09525884058640921   regen -0.09525884058640921   diff 0.0
1000LUNCUSDT  k=4   emitted -0.00739049895070917   regen -0.00739049895070917   diff 0.0
1000LUNCUSDT  k=12  emitted -0.09855503079154710   regen -0.09855503079154710   diff 0.0
1000PEPEUSDT  k=4   emitted NaN                    regen NaN     (n_finite_p = 0)
1000RATSUSDT  k=4   emitted NaN                    regen NaN     (n_finite_p = 0)
```

The route is sound, deterministic and bit-identical — R6-01's fix is real, not a promise. The last
two rows are R7-01.

---

### PART C — findings

#### R7-01 — MEDIUM — the HARD parent-gate parity check has no defined outcome for the 8 of 25 symbols where the parent emitted no probability at all

**Fails:** `design.md:252–255` (§4.1a PARENT PARITY, HARD: *"must reproduce SPDR-015's own emitted
`delta_brier_vs_pers` at k=4 and k=12, per symbol, to `|d| <= 1e-9`"*); `design.md:1051` (§12 HARD
**Parent-gate parity**).

`transition_metrics.parquet`, filtered to `clock == 'H1'`, `model == 'R-MARKOV'`,
`method == 'logistic_ridge'`, `horizon_k ∈ {4, 12}`, holds 50 rows — and **only 34 carry a finite
`delta_brier_vs_pers`**. Eight symbols are NaN at **both** horizons:

`1000PEPEUSDT · 1000RATSUSDT · BIGTIMEUSDT · ORDIUSDT · PYTHUSDT · SEIUSDT · TIAUSDT · WLDUSDT`

I traced the cause: `walk_forward_probs` returns an all-NaN `logistic_ridge` vector when
`origin_idx.size < 40` (`transitions.py:189–190`), so the parent never produced a probability for
those symbols and its Brier is undefined. My regeneration reproduces the NaN faithfully. Two
consequences the design does not state:

1. **The check.** `|NaN − NaN| ≤ 1e-9` evaluates false. A literal implementation of the HARD
   assertion fails on a **correct** screen, on a third of the universe — the same shape as R6-06,
   which the design has already fixed once for TRIPWIRE-2.
2. **The population.** Those eight symbols have no R-MARKOV k=4/k=12 gate at all, so every one of
   their episodes is ineligible for `L2_LEVEL_RMARKOV_K4`, `L2_LEVEL_RMARKOV_K12`,
   `L2_JOINT_HMM_HIGH_AND_K12_HIGH` and `L2_INTERACTION_HMM_X_K12` — 4 of the 33 variants run on
   **17 of 25 symbols**. §4.1a's ALIGNMENT clause already forces the right behaviour ("An event with
   no available label yet is excluded from that layer's rows with a count and reason"), so the
   population rule is not missing — but the coverage fact is undisclosed, and a per-symbol L2 read
   on 17 rather than 25 symbols is exactly the kind of silent narrowing the design elsewhere refuses.

**Why this is not blocking.** The developer is not being asked to invent a rule: §4.1a already says
what happens to an event with no label, and the parity convention follows from the design's own
P-23/L-52 principle that a check which cannot be evaluated is recorded, not vacuously passed.

**Required fix (quant-designer), before EXECUTION not before implementation.** In §4.1a and §12,
state that a symbol whose parent `delta_brier_vs_pers` is null at a horizon is **PARITY-EXEMPT** at
that horizon, that its count and its symbol list are emitted to `results/parent_gate_parity.json`,
and that its episodes are INELIGIBLE for the four R-MARKOV variants with the same count-and-reason
treatment as any other missing label. Add the realised per-variant symbol coverage to
`metrics_by_cell` so the 17-of-25 fact is disclosed rather than inferred.

#### R7-02 — LOW — the committed predeclaration pins a generator hash that no longer matches the generator

`expected_resolution.json.source_sha256.generator_code = 2489bd5b9600…` and
`resolution_basis.json.generator_sha256 = 2489bd5b9600…`, but the actual sha256 of
`python/src/xen/resolution_basis.py` at HEAD 112242c is **`72c6b1f953ca…`**. The R6-09 docstring fix
landed in the same commit as the artifact regeneration but **after** it, so the provenance pin is
stale. The same defect is present in `SPDR-020/results/expected_resolution.json` and in the shared
`resolution_basis.json` (byte-identical file, same sha `c1c560bb…`, pinned by both experiments).

§12's **Predeclaration present** row asserts only that `input_sha256.basis` equals the sha of the
committed basis — which **does** hold — so no stated check fails. What fails is §15's and §8.1's
claim that the artifact is "SHA-256-pinned on its inputs": the pinned generator is not the generator
on disk. I verified the change is numerically inert — I recomputed every band, cell count,
`distinct_n`, horizon summary and `c_median` independently and they reproduce the committed values
exactly — so this is a provenance-record defect, not a data defect.

**Required fix (experiment-developer).** Re-run the §8.1 generator command at the pinned
`generated_at_utc` with the current source hashes and re-commit both experiments' JSONs; confirm the
payload is unchanged apart from `generator_sha256` / `source_sha256.generator_code`. Do this before
execution so the audit trail is intact.

#### R7-03 — LOW — the L-23 ledger has no row for the run-6 remediation

`design.md:1127–1257`. Every earlier QA round is booked — AMENDMENT-3/4/5 (run 1), 9/10 (run 2),
12/13 (run 3), 14/15/16 (run 4), 17 (run 5, "in one row because the items are one repair of the same
document"). The run-6 repair is not: commit 112242c added §4.1b whole, replaced the R-MARKOV gate
route, added the binding exit-matching clause, added or edited six §12 rows and stated the HARD count
as a literal 28 — and the ledger still totals 17 rows reading `4 looser / 8 tighter / 5 neutral`. My
recount of the 17 booked rows matches those numbers exactly, so the tally is right *for what is
booked*; the omission is that the run-6 changes are not booked at all. L-23 requires **every**
pre-measurement amendment to carry a direction and enter the running count.

**Required fix (quant-designer).** Add `AMENDMENT-18: QA run-6 remediation` in the AMENDMENT-17 style
(one row, items (a)–(k)), `DIRECTION: TIGHTER`, and update the counts to `4 looser / 9 tighter /
5 neutral`, active `3 / 8 / 5`. The LOOSER streak flag for the operator is unaffected.

#### R7-04 — LOW — the sizing arm's "same average notional by construction" is not true by construction

`design.md:308`: *"the constant `c` is pinned to `N0 × ŝ_uncond` per symbol, so the modulated arm has
the SAME average notional as its comparator **by construction** and only its dispersion differs."*
The weight is `ŝ_uncond / ŝ(t,h)`; by Jensen `E[ŝ_uncond/ŝ] ≥ ŝ_uncond/E[ŝ] = 1` whenever `ŝ` varies,
and the `[0.25, 4]` clip perturbs it further. What is equal by construction is the **scale anchor**,
not the realised mean notional. Harmless to every estimand — §4.2 and §13 forbid a sizing cell
carrying a `log R` claim and bind it to dispersion (SoT §4.4) — but a reader will take the sentence
at face value and it is checkable, so it should be right.

**Required fix (quant-designer).** Replace "the SAME average notional … by construction" with
"anchored at the same scale; the realised mean weight is emitted", and add the realised mean and sd
of the weight per symbol to the two `L4_SIZE_*` rows' emission.

#### R7-05 — LOW — three departures from the BINDING reflection are unlabelled, and one §12 row mis-cites it

The reflection at
`docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/reflection-mid-volatility-model.md`
is the binding source. Three departures exist. All three are, in my judgement, **improvements** — but
L-23 and the design's own practice require them to be booked as departures, and one of them is
currently justified by a misquotation.

1. **§12's L1 row (`design.md:1053`) asserts "§5.5's ŝ-decile axis is a selection axis, not an entry
   re-parameterisation".** Reflection §5.5 (`:359`) says the opposite: the ŝ-decile axis is offered
   as the **calibration axis for `deltaThreshold`** — *"a decile-based threshold is the natural
   calibration axis, not an absolute number"* — which is precisely an entry re-parameterisation. The
   design's choice (freeze `δ` at `{0.25, 0.5, 1.0}`, use ŝ deciles to **select** among the signals
   the frozen δ already produced) is the better one and is compelled by §5.9's single-fixed-entry
   requirement plus AMENDMENT-3. But the authority for it is §5.9, not §5.5, and the sentence as
   written tells a reader the reflection says something it does not.
2. **Reflection §5.9's L1 row (`:429`)** is *"ŝ used **only** to set parameter magnitudes; no state
   gate, no swing gate"*. The design's L1 sets no magnitudes — it selects — and magnitude-setting has
   moved into L4. A real reallocation of content between layers, unbooked.
3. **Reflection §5.9 (`:435`)** specifies the L4 unmodulated arm as *"a fixed multiple of **ATR**"*.
   The design uses the per-symbol TRAIN-median **ŝ** instead (§4.2, §7, and the HARD §12 L4 comparator
   identity row). This is right — the ATR-vs-Parkinson pairing is the EXP-025 seam (L-21) and would
   have put a ~1.5–1.7× level shift inside the one comparison L4 exists to make — but it is a
   departure from the binding text, currently framed only as "QA run 2".

The design already books the one §5.9 narrowing it noticed (AMENDMENT-13: *"record the reflection
§5.9 L4 narrowing (modulation by ŝ only, not by each volatility layer)"*), which is why the other
three read as an oversight rather than concealment.

**Required fix (quant-designer).** Correct the §12 citation to name §5.9's fixed-entry requirement as
the authority, and book (1)–(3) inside the AMENDMENT-18 row of R7-03 as disclosed, reasoned
departures from reflection §5.5 / §5.9, each with its own direction label.

#### R7-06 — LOW — §6.1 TRIPWIRE-2 says "ALL THREE" over four conjuncts

`design.md:568–579`. The R6-06 fix added the `price_identical_bars` clause, so the HARD pass rule now
has four conjuncts under a heading that still reads *"HARD PASS, fixed before the run - ALL THREE"*.
TRIPWIRE-1's "ALL THREE" (`:545`) is correct. Cosmetic, but §12's check-count reconciliation is a
by-name discipline and a miscounted conjunction inside a HARD rule is the wrong habit.
**Fix:** "ALL FOUR".

**Advisory 1 (unchanged from run 6, still advisory).** §12's **L1 fixed-entry subset** row covers L1
only. L2 and L3 are selection layers on the same frozen entry; extending the identical subset
assertion to them costs nothing and closes the symmetric failure.

**Advisory 2 (feasibility, not validity).** §6 now requires **≥ 2,000 deranged seeds** whose exit
paths are **re-resolved on the M1 stream** for every target and trail arm, across 198 fixed cells.
That is a materially larger compute object than a sign flip, and §10's complexity freeze says nothing
about it. Worth the developer sizing before starting, and worth the operator knowing; it is not a
design defect and does not change what must be measured.

---

### Checks independently verified clean

| Check | Result |
|---|---|
| Exact mirror, slope 1 | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` consistent across §1, §4.1, §5, §8, §9, §12, G4, G5, §13. `0.9408` appears once and only to refuse it; §12 makes a fitted-slope residual a hard failure |
| Cost isolation (AMENDMENT-C5) | **CLEAN.** Header NOTE, §5 DISCLOSED REFERENCE ONLY, §7 cost-floor line, §12 HARD row, §13 first bullet, §15 column flag. No band, threshold, estimand or comparison carries a cost term |
| SPREAD-COST-DISCLOSURE | **CLEAN.** All five fields present verbatim per `design-requirements.md` §10; `UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps: null`, `PARTIAL_FEES_FUNDING_ONLY`, prohibited claims listed. Unchanged across seven runs |
| Mandatory declaration blocks | **CLEAN.** Mechanism + DERIVED (§1), OBJECT-IDENTITY (§3), four control blocks with all seven required fields each (§6), two tripwires (§6.1), bands (§9), golden traces G1–G7 (§11), HARD/INFORMATIVE split (§12), CONVERSION-PIN (§7), amendment ledger (§14). The `UNPOWERED` band and the POWER block are replaced by the ladder under registered AMENDMENT-C7 — an authorised, registry-backed substitution, not an omission |
| No adequacy flag / no canonical threshold | **CLEAN.** §12 asserts the absence HARD; the ladder matches registered C7 rung for rung; `mde50/mde80/mde95` are three points of one curve, none privileged; the committed predeclaration contains none of `powered`/`unpowered`/`at_target`/`not_resolvable` (I grepped the payload) |
| Phase-(b) trigger vs C6 / reflection §5.9.1 / INFR-016 | **CLEAN.** Pre-declared before (a), stated on the (a) reads in the §9 CI-relative vocabulary, no magnitude, nothing machine-dropped, operator authority still required and declinable. Execution blocker 1 stays discharged |
| C6 `NOT_RESOLVABLE` vs C7 | **CLEAN.** §4.3 discharges C6's obligation without C7's forbidden flag by requiring the whole six-rung distribution, reported and not adjudicated. Both registry rows verified |
| Block rule vs SPDR-018 §6.2 | **CLEAN.** Six-clause canonical literal, clause-by-clause §12 check, JSON string verbatim with nothing appended. Min block 1 day = 24 h ≥ the longest horizon in scope (20 h, including the clipped `h_mod`) |
| Basis population | **CLEAN.** One declared population, accounting reconciles, exclusions tallied by reason, generator raises if they do not sum (`resolution_basis.py:412–413`) |
| Predeclaration integrity | **CLEAN on content** (5,148 distinct strata, dated, no placeholder, no outcome input, generator deterministic, 9/9 tests pass). Provenance-hash residue is R7-02 |
| Decile causality (new) | **CLEAN.** Per symbol, expanding, strictly-before-`[0]`, 250-bar warm-up, continuous rank and M-3 deciles bound to the same rule, HARD in §12 |
| Exit-matched nulls (new) | **CLEAN.** Binding on both derangements, negation restricted to time-exit arms and asserted per arm, un-matchable devices demoted to DISCLOSURE |
| L-28 derangements | **CLEAN.** Both permutation controls declare and count zero fixed points; TRIPWIRE-1 correctly declares N/A (index shift, not a permutation) |
| L-50 / P-21 | **CLEAN.** Plant rungs stated in σ̂ units and re-derived per universe at run; no absolute bps bar crosses a universe boundary |
| L-21 / P-15 unit pin | **CLEAN.** Two divisor objects, ATR20 bound to `deltaThreshold` and explicitly barred from every L4 arm, medians computed at run to `unit_pin.json`, effects reported in bps and σ̂ side by side, σ̂ never compared to the cost floor |
| M-4 effective coverage | **CLEAN.** 229,646 measured pooled H1 bars, not date arithmetic; asserted in §12; the R6-04 prose contradiction is gone |
| M-2 / M-3 / M-5 | **CLEAN.** Span disclosure in §12 and `metrics_by_cell`; magnitude-matched comparator mandatory for L1 and L3 with its own plant curve; collapse fraction disclosure-only in every control, with the mirror null's explicit `null / POINT_NULL` |
| L-51 selection check | **CLEAN and defensible.** HARD on presence and form only, re-anchored to every separately reported subset now that the powered/unpowered split is retired |
| L-52 / P-23 | **CLEAN.** Check-count reconciliation by name with a stated literal (28, which I recounted); every check bound to an emitted artifact; missing/empty is a failure not a vacuous pass; determinism unconditional at `--jobs > 1` |
| Lane compliance (`spdr-lane.md`) | **CLEAN.** TRAIN-only, causal `t−1`, M1 fill resolution with no intrabar look-ahead, ≥2,000-seed batteries against a lane floor of 25, per-stratum reporting with multiplicity disclosed (5,148 rows named explicitly), pooled reverts to disclosure-only without homogeneity, no local accounting, dependence-matched CI with block ≥ H |
| Shared-code boundary | **CLEAN.** `python/src/xen/resolution_basis.py` contains no threshold and no admit/exclude/label/rank path; `required_n`, `mde50`, `c_bands` are pure conversions and summaries; tests pass |
| Holdout / TEST / XENA / family action | **CLEAN.** TRAIN-only; §12 asserts zero queries `≥ 2025-01-08`; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised. No XENA route, so INFR-010 R4 does not apply |
| Golden traces | **CLEAN.** G1–G7 cover entry+fill, expiry, suppression, the identity, the exact mirror, exit precedence, and leak discrimination; all are deterministic selection rules QA can compute from the catalog without running the implementation; G6 is now structural |

---

### Standing execution blockers

1. **DISCHARGED (re-verified this run)** — the AMENDMENT-7 / registered-C6 departure. Checked against
   `cf-voldir-001.md` and reflection §5.9.1 directly, not against the design's assertion.
2. **STANDS** — `reflection-inputs.md` §9 is still explicitly unsigned. This blocks **execution**,
   not implementation.
3. **STANDS (lane-wide, unchanged)** — the per-symbol spread pin is open; every money read stays
   blocked. It does not block this measurement under AMENDMENT-C5.

New this run, and to be cleared before execution rather than before implementation: **R7-01** (parity
NaN convention + L2 coverage disclosure) and **R7-02** (regenerate the artifacts so the generator hash
matches).

### Golden-trace and boundary verdict

Design-stage: no code and no smoke emission to diff. G1–G7 are hand-derivable from the catalog and
the design alone, as the lane requires, and G6 is now executable. No golden trace depends on a value
the implementation would produce.

---

**FAILING_ARTIFACT:** none blocking. Residual defects sit in
`python/experiments/SPDR-019/design.md` (R7-01, R7-03, R7-04, R7-05, R7-06) and in the committed
provenance pins of `python/experiments/SPDR-019/results/expected_resolution.json` +
`python/experiments/SPDR-019/results/resolution_basis.json` (R7-02, which also affects SPDR-020).

**REQUIRED_SKILL:** `quant-designer` for R7-01/03/04/05/06; `experiment-developer` for R7-02.

**Implementation authorisation: YES.** Every clause a developer must build from is now specified:
the entry and both fill rules, the 33 named variants, each gate's source artifact and column, the
decile population and window, the L4 comparator identity and the exact modulated-hold equation, both
tripwires' structural pass rules, the exit-matched null construction, the block rule clause by
clause, and the full emission schema. The six open findings are a check convention, a stale hash, a
ledger row, a sentence, three citations and one number-word — none changes the estimand, the
population, a comparator or an integrity check, and none can silently corrupt a result if fixed
before the operator's execution gate.

**What I did not reach.** I did not recompute M15 or H1 episode counts from the catalog — no parent
emission carries them and the design correctly declares them unknown. I did not audit
`xen.evaluation.block_bootstrap_ci`'s internals beyond confirming it exists and honours the L-20
contract. I regenerated the R-MARKOV parity on 4 of 25 symbols, not all 25; the two matching symbols
matched bit-identically and the two NaN symbols reproduced the NaN, which is what R7-01 rests on. I
did not review SPDR-020, which shares `resolution_basis.py` and the resolution artifacts — **R7-02
applies there verbatim**, and R7-04/R7-05 may.
