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
