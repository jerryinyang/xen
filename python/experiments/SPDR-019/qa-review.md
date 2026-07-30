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

---

## QA run 8 — 2026-07-29T11:07:16Z — mode: subagent — HEAD a41cb7c (dirty: SPDR-019/screen_code/ untracked, SPDR-020/screen_code/ untracked)

**Reviewed git state:** `HEAD a41cb7ce1c71f77faebf011234b3e1aa9bf9589d`; working tree carries two
untracked directories, `python/experiments/SPDR-019/screen_code/` (15 modules, 4,193 lines) and
`python/experiments/SPDR-020/screen_code/`. Only the former is in scope.
**Stage:** IMPLEMENTATION QA — first run against code. Runs 1–7 were design-stage.
**Independence:** fresh subagent context. I authored none of the implementation and none of the
design. `design.md` (1,358 lines) read in full; `qa-review.md` runs 5–7 read in full; runs 1–4
read by heading and finding ID. `spdr-lane.md`, the knowledge-base index, lessons and pitfalls
ledgers, and `_pipeline-config.md` read.

**Verdict: REJECT.**

**Execution authorisation: NO.**

This is not a "revise a few clauses" outcome. The code implements the entry, the fill resolution,
the (p, W, L, log R) identity and the bootstrap machinery correctly and, in several places,
provably so — I executed those paths. But the **integrity layer that the design exists to
guarantee is not implemented**. Two of the design's HARD tripwires are constructed so that they
cannot fail; nine further HARD checks are hardcoded `True` literals in a dictionary; the exit-matched
derangement that AMENDMENT-18(c) added is dead code that is never called while its HARD check
attests that it ran; and the ≥2,000-seed side-derangement battery collapses to a single value.
Under `spdr-lane.md`'s HARD integrity boundary and P-23/L-52 (a check that cannot fail is
indistinguishable from one that was skipped), that is REJECT-class and cannot be overridden
in-session.

Findings: **6 CRITICAL · 9 HIGH · 10 MEDIUM · 4 LOW.**

Every claim below is marked **CONFIRMED** (I executed it or hand-derived it) or **READ** (read-only
inference). No number appears here that I did not produce myself.

---

### PART A — run-7 residue: status

| Run-7 finding | Status | Evidence |
|---|---|---|
| **R7-01** — parity NaN convention + L2 coverage disclosure | **CLOSED in design; NOT IMPLEMENTED in code** | `design.md:256–266` now names the 8 PARITY-EXEMPT symbols and discloses the 17-of-25 L2 coverage. `config.py:177–180` carries the list verbatim and `parent_gates.py:176–182` short-circuits those symbols to `PARITY_EXEMPT`. But the coverage fact is never emitted to `metrics_by_cell` as §4.1a requires, and the parity gate itself passes vacuously — see **R8-15** |
| **R7-02** — generator-hash mismatch | **CLOSED — CONFIRMED by execution** | `shasum -a 256`: `resolution_basis.json` = `23d5f5bf1eb1…`, `expected_resolution.json` = `e3247798edc9…`, `resolution_basis.py` = `72c6b1f953ca…`. The artifact's `generator_sha256` and `source_sha256.generator_code` both read `72c6b1f953ca…` — they now match the file on disk. `input_sha256.basis` = `23d5f5bf1eb1…` = the measured basis sha. `input_sha256.prior` = `961cec28e28f…` = measured. `config.py:240–248` pins all three correctly. SPDR-020's `resolution_basis.json` is byte-identical (`23d5f5bf…`), so the sibling defect is closed too. Payload unchanged: `row_count` 5,148, `strata` 5,148 rows, all `UNKNOWN_NO_PARENT_MEASURED_POPULATION` |
| **R7-03** — missing ledger row for run-6 | **CLOSED** | `design.md:1264–1292` = `AMENDMENT-18`, items (a)–(j), `DIRECTION: TIGHTER`; counts updated to `4 looser / 9 tighter / 5 neutral`, active `3 / 8 / 5` (`:1294–1296`) |
| **R7-04** — "same average notional by construction" | **CLOSED** | `design.md:319` now reads "anchored at the same scale … Its realised mean weight is **not** identical (Jensen, plus the clip): the mean and sd of the realised weight are emitted per symbol". Note the emission it promises does not exist in code — see **R8-23** |
| **R7-05** — three unlabelled reflection departures | **CLOSED** | `design.md:1278–1292` books all three under AMENDMENT-18 as narrowings, and `design.md:1064` now cites "**Authority: reflection §5.9's single-fixed-entry rule**, which binds over §5.5's suggestion" |
| **R7-06** — "ALL THREE" over four conjuncts | **CLOSED** | `design.md:579` reads "HARD PASS, fixed before the run - ALL FOUR" |
| Standing blocker 1 (AMENDMENT-7 / C6) | **DISCHARGED — re-confirmed, not re-flagged** | Signed at `9d8832e`; `design.md:376–400` carries the pre-declared trigger |
| Standing blocker 2 (`reflection-inputs.md` §9 unsigned) | **DISCHARGED** | Commit `9d8832e` "sign the mid-checkpoint reflection (option B)". Confirmed, not re-flagged |
| Standing blocker 3 (lane-wide spread pin) | **STANDS — and is respected by the code** | `config.py:185–203` carries `SPREAD_COST_DISCLOSURE` verbatim; `SPREAD_BPS_PROHIBITED = True`; the only cost objects in the emission are `p_be_net` and `cost_bps_DISCLOSURE_ONLY`, both flagged, neither entering an estimand, threshold, band or comparison (`metrics.py:333, 354–357`). **The code makes no money read.** AMENDMENT-C5 satisfied |

---

### PART B — what the code gets right (verified, not assumed)

Recorded so the REJECT is not read as a blanket condemnation. Each row below I executed.

| Design clause (§ref) | Code (file:line) | Verdict | Evidence |
|---|---|---|---|
| §2 entry: `low[1] < min(low[0],low[2])`, `(c[0]−c[1])/ATR20 > δ`, stop `= high[0]` | `entry.py:57–67` | **MATCHES — CONFIRMED** | Ran G1 on BTCUSDT H1 DESIGN δ=0.5. First LONG at `decision_idx 37`: bar0 OHLC `20683.5 / 20866.0 / 20674.5 / 20831.5`; pivot `low[1] < min(low[0],low[2])` → `True`; `ATR20 = 173.5281`; momentum `0.8529 > 0.5`; `stop_price == high[0]` → `True` |
| §2 entry fill on M1, fill after decision close | `fills.py:41–83`, `entry.py:99–110` | **MATCHES — CONFIRMED** | Same trace: `fill_kind = STOP`, `fill_price = 20866.0` = the stop, `fill_ts > decision_end_ns` → `True`. `_first_m1_after` uses `side="right"` so the fill bar is strictly after the decision close |
| §10 TRAIN fence asserted in code; zero queries ≥ 2025-01-08 | `catalog_io.py:60–65, 95–98` | **MATCHES — READ** | `assert_within_fence` plus two explicit raises (`end_ns > TRAIN_END_NS`, `end_ns > HOLDOUT_START_NS`) before any read, and four post-load asserts on the loaded frame. `HOLDOUT_START = 2025-01-08T00:00Z` (`config.py:49`). The date bound is enforced, not merely documented |
| §5 identity `\|p·W − (1−p)·L − mean\| < 0.01` | `metrics.py:53–72, 360–366` | **MATCHES — hand-derived** | With `p = n_pos/(n_pos+n_neg)`, `W = Σ⁺/n_pos`, `L = −Σ⁻/n_neg`: `p·W − (1−p)·L = (Σ⁺+Σ⁻)/(n_pos+n_neg)` = the mean over signed episodes exactly. The residual is zero by construction, so G4 passes analytically |
| §5 `log R = log(W/L) − log((1−p)/p)`, slope 1 | `metrics.py:75–79` | **MATCHES — READ** | Slope 1, no fitted coefficient. No `0.9408` anywhere in `screen_code/` |
| §3 flat legs excluded from `p`, counted as `p_flat` | `metrics.py:61, 71` | **MATCHES — READ** | `signed = n_pos + n_neg`; zeros enter only `p_flat` |
| §8.1 block bootstrap == `xen.evaluation.block_bootstrap_ci` | `metrics.py:82–89, 162–186` | **MATCHES — CONFIRMED** | Ran `assert_canonical_equivalence` on 2,000 synthetic episodes over 300 days: canonical CI `[−0.04400456485167759, 0.16925966248798424]` vs vectorised `[−0.04400456485167753, 0.16925966248798474]`, `abs_diff = [6.2e-17, 5.0e-16]`, `equivalent: True`. The fast path is bit-equivalent to the library |
| §8.1 clause 5 — effective block capped `< n` (INFR-004/L-20) | `metrics.py:84` | **MATCHES — READ** | `eff = max(1, min(block, n_days − 1))`. The Phase-010 `block=5` default is **not** used; blocks are `{1,3,7}` calendar days from `config.BOOT_BLOCKS_DAYS` |
| §8.1 clause 1 — per-calendar-day sufficient statistics | `metrics.py:27–50` | **MATCHES — READ** | `day_index` floors ts to `DAY_NS`; resampling is over day rows, never episodes |
| §4.2 modulated-hold equation | `engine.py:196–199` | **MATCHES — hand-derived** | `e_run = clip(p_stay/(1−p_stay), 1, 48)`; `h_mod = clip(h·e_run/20, 1, 20)`. Character-for-character the design's equation, including both clips and the divisor 20. (The *input* is broken — R8-06 — but the equation is right) |
| §12 L1 fixed-entry subset | `engine.py:338–368`, `run_screen.py:754–764` | **MATCHES — READ** | L1–L3 are built by tagging L0 episode objects (`Episode(**{**ep0.__dict__, "variant_id": vid})`), so stop price, fill ts/price and signal bar are identical by construction; `run_screen.py` then re-asserts key membership on the 5-tuple. This is the one HARD check in `integrity_extra` that is genuinely computed |
| §4.1b decile population/window/warm-up | `indicators.py:105–127`, `panel.py:115`, `config.py:102` | **MATCHES — READ** | `expanding_decile_edges` ranks `x[i]` against `hist` = finite values at indices `< i` only, appending `x[i]` *after* the rank is taken — strictly before `[0]`. `min_hist = DECILE_WARMUP_SHAT = 250`. Computed per symbol inside `build_shat_h1`; no pooled or full-TRAIN edge exists anywhere |
| §7 unit pin — two divisor objects, ATR barred from L4 | `indicators.py:62–84`, `engine.py:212–233` | **MATCHES — CONFIRMED** | `wilder_atr` is referenced only by `panel.build_*` and consumed only at `entry.py:57` as the `deltaThreshold` normaliser. `_exit_params` reads `sig.s_hat_bps` / `panel.s_hat_uncond` exclusively; `grep` finds no `atr` token in any exit-width path. Ran the pin on BTCUSDT: `s_hat_uncond = 22.859` bps, `atr20_median_h1` finite, both computed at run and written to `unit_pin.json` (`run_screen.py:568–578`) |
| §4.2 UNMOD/MOD share estimator, unit, clock, √h, multiplier | `engine.py:214–233` | **MATCHES — READ** | Both arms call `_horizon_scale_bps(·, h_hours)` = `ŝ·√h` with `h` in hours; the only difference is `s_hat` vs `s_uncond`. No level shift, no unit seam. (The *assertion* of this is fake — R8-03 — but the implementation is correct) |
| §7 `√h` with `h` in HOURS on both clocks | `engine.py:75–79`, `config.py:109` | **MATCHES — READ** | `L4_HOLD_HOURS = (1,4,12,20)` in hours; `active_ns = h_hours·3600·NS` on both clocks. The EXP-025 bar-vs-hour trap is avoided |
| §2 exit precedence: adverse wins in-bar; time exit open-to-open | `fills.py:182–191, 86–107` | **MATCHES — READ** | Trail returned on both-hit; target only when trail did not hit. Time exit fills at `clock_open[i]` where `slot_start[i] ≥ fill_ts + hold`. Trail ratchets on `c[i]` *after* the trigger test on bar `i` (`fills.py:193–202`) — M1 closes only, never intra-bar, as §2 requires |
| §12 33 named variants | `config.py:119–154` | **MATCHES — CONFIRMED** | Literal list, `assert len(VARIANT_IDS) == 33` at import. Names match `design.md:192–198` one for one |
| §12 HARD check count 28, by name | `config.py:251–282` | **MATCHES — CONFIRMED** | `HARD_CHECK_NAMES` holds exactly the 28 names of the §12 HARD block; `assert len(...) == 28` at import. `selfcheck.run_selfcheck` calls `mark()` with 27 of them plus `check-count reconciliation` = 28, and rebuilds the list in canonical order, appending `held: False, missing: True` for any name never executed (`selfcheck.py:315–330`) — the *structure* is right even though the *content* is not |
| §12 predeclaration consumed, never regenerated | `run_screen.py:92–105`, `selfcheck.py:85–99` | **MATCHES — CONFIRMED** | Both paths hash the committed files and compare to the `config.py` pins; `main()` calls `verify_predeclaration()` before any data is touched. `_join_predeclaration` reads `exp["strata"]` — I confirmed `strata` is the real key and holds 5,148 rows keyed `(clock, delta, variant_id, scope)`, matching §8.1's join key exactly |
| §12 cost isolation / AMENDMENT-C5 | `metrics.py:333, 354–357`, `config.py:191–203` | **MATCHES — READ** | `p_be_net` present and flagged `DISCLOSURE_ONLY`; no net figure enters any band, CI or comparison |
| §12 no adequacy flag / no canonical threshold | whole tree | **MATCHES — CONFIRMED** | `grep -ri "powered\|unpowered\|at_target\|not_resolvable"` over `screen_code/` returns nothing. AMENDMENT-C7 honoured |
| §10 no XENA, no TEST, no holdout, no family action | whole tree | **MATCHES — CONFIRMED** | No `xena` import, no TEST band, `TEST_START` and `HOLDOUT_START` are defined and never read |

---

### PART C — findings

#### R8-01 — CRITICAL — TRIPWIRE-1 rebuilds its own input until it passes

**Fails:** `design.md:549–568` (§6.1 TRIPWIRE-1, HARD PASS, all three conditions), `design.md:1088`
(§12 HARD list), P-23/L-52.
**Code:** `run_screen.py:685–696`.

```python
tw1 = controls_mod.tripwire_1_shift(sl, sk, ...)
# ensure structural conditions: construct exact shift if needed
if not tw1["hard_pass"] and sl.size > 2:
    leaky = np.full_like(sl, np.nan)
    leaky[:-1] = sl[1:]
    ...
    tw1 = controls_mod.tripwire_1_shift(sl, leaky, sel_l, sel_k)
```

**Design requires:** two state streams **materialised before the comparison** — the legal stream
built from `[0]` and a leaky stream built from `[+1]` — then the identical pipeline re-run on each,
and the three structural conditions read off the result.

**Code does:** if the real comparison fails, it **synthesises** `leaky` as `legal` shifted by one row
and re-runs the check against that. `shift_is_exact_one_row` is then true *by definition of the
construction*, because `controls.tripwire_1_shift` tests precisely `leaky[:-1] == legal[1:]`
(`controls.py:274–277`). The tripwire cannot fail. A causal-misalignment detector that reconstructs
its own evidence detects nothing.

Compounding this: neither stream is ever run through the pipeline. `sel_legal` / `sel_leaky`
(`run_screen.py:189–190`) are `s_hmm_rv == 1` masks over raw H1 bars, not the episode selections the
design names (`changed_selection_episodes`). No episode is re-selected and no exit is re-placed under
the leaky state, so §6.1's vacuity argument ("it moves p, W and L") does not apply to what is
actually computed.

**Required fix (experiment-developer).** Delete the reconstruction branch outright. Build the leaky
conditioning state by indexing the parent-gate arrays at `[+1]`, re-run `build_episodes_for_variant`
for every layer variant on that state, and compute `changed_selection_episodes` as the symmetric
difference of the two episode key sets. If the resulting check fails, that is the finding — not a
prompt to rebuild the input.

#### R8-02 — CRITICAL — TRIPWIRE-2 runs on synthetic prices and falls back to literal dummy values

**Fails:** `design.md:569–593` (§6.1 TRIPWIRE-2, all four HARD clauses), `design.md:1088`, P-23/L-52.
**Code:** `run_screen.py:191–231` and `run_screen.py:697–703`.

Three separate defects, any one of which is disqualifying.

1. **The levels are invented.** `_tripwire_material` walks every 17th M1 bar of one symbol and
   fabricates `tgt = mid*1.001`, `trail = mid*0.999` (`run_screen.py:202–204`). These are not the
   experiment's L4 target and trail levels, and they sit on bars that belong to no episode.
   TRIPWIRE-2 exists to prove that `resolve_target_trail_time` — the real exit path — takes the
   adverse branch. Scanning invented levels on unrelated bars proves nothing about that function,
   which is never called by the tripwire at all.
2. **Clause 4 is unfalsifiable.** `fav_prices.append((fav, adv, 1))` (`run_screen.py:216`) always
   appends `fav = mid*1.001`, `adv = mid*0.999`, `side = +1`. `controls.tripwire_2_fills:308–311`
   then tests `side > 0 and fav_px < em_px` — i.e. `1.001·mid < 0.999·mid`, always false. The
   "favourable twin is never worse" assertion passes on synthetic arithmetic, per id, for every id.
3. **The fallbacks manufacture a pass.**
   ```python
   tw2 = controls_mod.tripwire_2_fills(
       tm.get("clock_diff_ids", [1]),
       tm.get("both_ids", [1]),
       tm.get("fav_ids", tm.get("both_ids", [1])),
       tm.get("fav_prices", [(1.001, 0.999, 1)]),
       tm.get("price_identical", 0))
   ```
   With no material at all, the counts become `1 / 1 / 1` and `price_ok` is `True`, so
   `hard_pass = (1>0) and (1>0) and (1==1) and True` → **`True`**. §6.1 states in terms:
   *"A missing, empty or zero-count field is a FAILURE, never a vacuous pass (P-23/L-52)."* The code
   inverts that rule exactly.

Neither twin the design names is built. There is no **DECISION-CLOCK twin** (re-resolving fills on
the decision bar's OHLC) anywhere in the tree — `clock_diff_ids` is a heuristic on M1 gaps
(`run_screen.py:219`), not a re-resolution. There is no **FAVOURABLE-PRECEDENCE twin** either.

**Required fix (experiment-developer).** Implement both twins as second passes over the real
episode set: (a) a variant of `resolve_target_trail_time` fed the decision-clock OHLC arrays,
(b) a variant with the `tgt_hit and trail_hit` branch at `fills.py:182` inverted to return the
target. Emit the real differing-id lists and the two fill prices per id, as §6.1 requires so QA can
re-derive them from the catalog. Remove all default arguments.

#### R8-03 — CRITICAL — nine HARD checks are hardcoded `True` literals

**Fails:** `design.md:1086–1099` (§12 HARD block), `design.md:1105–1106` ("Every check depends on an
**emitted artifact** — missing or empty is a **failure**"), P-23/L-52.
**Code:** `run_screen.py:715–751`.

The `integrity_extra` dictionary that `selfcheck.run_selfcheck` consumes is a literal. Nine HARD
checks read their verdict straight out of it:

| §12 HARD check | Line | Value | What is actually verified |
|---|---|---|---|
| Causality | `run_screen.py:716` | `"causality_ok": True` | nothing; a prose `"rule"` string accompanies it |
| Fill causality | `:718` | `"fill_causality_ok": True` | nothing. `fill_ts > decision_end_ns` is trivially checkable on `episodes_df` and is not checked |
| L4 COMPARATOR IDENTITY | `:730` | `"l4_comparator_ok": True` | nothing |
| PARENT-GATE PROVENANCE | `:734` | `"parent_prov_ok": True` | nothing |
| DECILE CAUSALITY | `:740` | `"decile_ok": True` | nothing |
| EXIT-MATCHED NULLS | `:742` | `"exit_matched_ok": True` | nothing — and the thing it attests to does not exist (R8-04) |
| L1 FIXED-ENTRY SUBSET | `:747` | `"l1_subset_ok": True` | **genuinely re-computed** at `:754–764`. The one honest member of the set |
| MOD-HOLD ELIGIBILITY | `:749` | `"mod_hold_ok": True` | nothing. §12 requires "A MOD row whose holds are identical to its UNMOD twin on every episode is a hard failure" — never evaluated |
| BLOCK RULE | `:723` | `boot_eq["equivalent"]` | partially real; see R8-13 |

`selfcheck.py:147–256` then faithfully records each literal as a HARD check that `held`. The
self-check is a transcription layer over a dictionary of assertions, not an independent verification.
This is the precise failure shape L-52 was written after: *"No required check lives in a manual
post-step"* — here they live in a literal, which is weaker still.

**Required fix (experiment-developer).** Each must be computed from an emitted artifact:
causality from `episodes.decision_end_ns` vs the state index used; fill causality from
`episodes.fill_ts > episodes.decision_end_ns` over all rows; L4 comparator identity by asserting
that every `L4_*` exit width traces to `s_hat_bps`/`s_hat_uncond` and that `atr20` appears in no
width; decile causality by re-deriving a sample of edges from history strictly before `[0]` and
diffing; MOD-hold by comparing the `active_hold_hours` vectors of each MOD/UNMOD twin.

#### R8-04 — CRITICAL — the exit-matched derangement is dead code, and its HARD check attests that it ran

**Fails:** `design.md:483–491` (§6 EXIT-MATCHING, BINDING ON BOTH DERANGEMENTS), `design.md:1061`
(§12 HARD **Exit-matched nulls**), AMENDMENT-18(c), L-24.2/F04.
**Code:** `controls.py:81–118` (defined), `run_screen.py:618–624` (never called).

`grep -n "side_derangement_exit_matched" screen_code/*.py` returns exactly one hit — the `def` line.
**CONFIRMED.** The function is never invoked from anywhere.

`run_screen.py:608–629` runs controls on a single cell (`L0_BASELINE`, H1, δ=0.5) and calls only
`side_derangement_time_exit` and `entry_timing_derangement`. `L0_BASELINE` is a time-exit arm, so the
sign-negation shortcut is legitimate there — but **no target or trail arm ever gets a control at
all**. The 10 path-dependent L4 variants (`L4_TARGET_A{1,2,3}_*`, `L4_TRAIL_B{1,2}_*`) run with no
derangement of any kind.

Meanwhile `run_screen.py:742–746` sets `"exit_matched_ok": True` with the detail
`{"target_trail_reresolve": "required"}` — the artifact will record that the exit-matched-null HARD
check passed, on arms where no null was computed. The design's own reasoning
(`design.md:485–488`: *"on a target or trailing-stop arm the SIDE decides WHICH BARRIER IS HIT AND
WHEN, so a sign flip would referee a path the deranged position never took"*) is unimplemented.

**Required fix (experiment-developer).** Wire `side_derangement_exit_matched` to a `resolve_fn` that
applies the deranged side, then re-resolves the entry fill, the barrier levels and the exit from M1
per §2, and computes `r` from the re-resolved fills. Run it on every target and trail arm. Assert per
arm that the negation shortcut appears only on `TIME_EXIT_VARIANTS`, and derive `exit_matched_ok`
from that assertion rather than declaring it.

#### R8-05 — CRITICAL — the ≥2,000-seed side-derangement battery produces one distinct value

**Fails:** `design.md:498–510` (§6 CONTROL SIDE-DERANGEMENT: ">= 2000 seeds", "null's own mean, sd
and quantiles (P-24)"), `spdr-lane.md` integrity boundary ("Random controls use a ≥25-seed battery
with a percentile/rank read, never a single twin (L-19)"), L-19.
**Code:** `controls.py:32–39, 50–56`.

```python
def derange_sides_zero_fixed(n, seed):
    rng = np.random.default_rng(seed)      # created, never used
    return np.full(n, -1, dtype=np.int64)
...
for sd in seeds:
    r_d = -r                                # identical on every iteration
    nulls.append(_logR(r_d))
```

The seed is accepted and discarded. Every one of the 2,000 iterations computes `-r`, so the null
"distribution" is a point mass.

**CONFIRMED by execution** on 3,000 synthetic episodes, `n_seeds=2000`:
`null_sd = 1.39e-17`, `null_q05 = null_q95 = −0.10081439007827171`, `percentile = 1.0`.

A percentile against a degenerate null is `0.0` or `1.0` and carries no information. The design cites
SPDR-013's side-derangement percentiles (0.20–0.28 on M15, 0.48–0.57 on H1) as the comparable object;
this control cannot produce a value in that range. It also cannot support the `>= 2000 seeds` claim
the design makes, nor the plant curve that is supposed to establish its own resolution.

`side_derangement_exit_matched:94–97` has the same structure (`side_mult=-1` on every seed), so it
would be degenerate too if it were ever called.

**Required fix (experiment-developer).** Derange the side *labels across episodes* — a permutation of
the side vector with zero fixed points, redrawn per seed and rejected if any episode retains its own
side — so that 2,000 seeds yield 2,000 draws. Count and emit the fixed points measured per seed
rather than hardcoding `fixed_total += 0` (`controls.py:55, 96, 114`), which is an unmeasured
constant standing in for the L-28 count §12 makes HARD.

#### R8-06 — CRITICAL — `p_stay` is identically 1.0, so all four MOD-hold variants emit zero episodes

**Fails:** `design.md:351–355` (§4.2 `p_stay` = the R-MARKOV same-state transition rate),
`design.md:1069` (§12 HARD **MOD-hold eligibility**).
**Code:** `parent_gates.py:216–219`.

```python
same = [1 for (av, os, stayed) in avail if av < t and os == st]
n_src[i] = len(same)
if len(same) >= 30:
    p_src[i] = float(np.mean(same))
```

The comprehension emits the literal `1` for every matching transition instead of the `stayed` flag it
unpacks. `np.mean` of a list of ones is `1.0`, unconditionally.

**CONFIRMED by execution.** On a synthetic two-state chain with a true stay rate of `0.642`:
`p_stay` distinct values = `[1.0]` across 349 finite entries.

The consequence propagates. `engine.py:196–197`:

```python
if not np.isfinite(p_stay) or p_stay <= 0 or p_stay >= 1:
    return float("nan")
```

`p_stay = 1.0` trips `p_stay >= 1` on **every** episode, so `_active_hold_hours` returns `NaN`,
`build_l4_episodes:408–412` marks the row `INELIGIBLE / HOLD_NA`, and `L4_HOLD_1H_MOD`,
`L4_HOLD_4H_MOD`, `L4_HOLD_12H_MOD`, `L4_HOLD_20H_MOD` produce **zero episodes**. Four of the 33
predeclared variants — the entire modulated-hold device, and the one L4 device whose modulation is
driven by regime persistence rather than by ŝ — measure nothing.

The §12 MOD-hold HARD check would not catch it either: it is hardcoded `True` (R8-03), and even a
correct implementation of "MOD holds identical to UNMOD on every episode" would pass on an empty set.

**Required fix (experiment-developer).** `same = [stayed for (av, os, stayed) in avail if av < t and
os == st]`. Then re-verify: `p_stay` must vary, `E_run = p_stay/(1−p_stay)` must land inside `[1,48]`
for a meaningful share of events, and the MOD hold vector must differ from its UNMOD twin.

#### R8-07 — HIGH — the entry-timing derangement re-labels realised returns instead of re-timing entries

**Fails:** `design.md:512–522` (§6 CONTROL ENTRY-TIMING DERANGEMENT: *"episodes whose entry
timestamps are deranged within symbol"*, *"re-timing changes which returns are realised"*),
§6 EXIT-MATCHING (binding on **both** derangements).
**Code:** `controls.py:121–158`, specifically `:153–156`.

```python
r_d[idx] = r[idx[perm]] * np.sign(side[idx]) * np.sign(side[idx[perm]])
# simpler: use permuted r with side preserved via re-sign
r_d[idx] = np.abs(r[idx[perm]]) * np.sign(side[idx]) * np.sign(r[idx[perm]])
```

Line 154's assignment is dead — line 156 overwrites it. What survives permutes **realised `r`
values** among episodes and re-signs them. No timestamp moves, no price path is touched, no fill is
re-resolved. The `ambient_r_by_key` argument — the ambient return lookup this control needs — is
accepted and never referenced (**CONFIRMED**: `grep` finds it only in the signature), and
`run_screen.py:623` passes `{}` for it.

This is the EXP-012 trap in the knowledge base: permuting realised P&L cannot destroy the alignment
the control is meant to break, because the returns being permuted were generated by the very signal
under test. The returned payload nonetheless carries `"exit_matched": True` (`controls.py:179`) — a
false attestation feeding a HARD check.

**Required fix (experiment-developer).** Draw a deranged entry timestamp per episode within symbol,
then resolve a fresh episode from the M1 stream at that timestamp with the original holding length
and side, exactly as §2 specifies, and compute `r` from those fills. Emit the measured fixed-point
count per seed.

#### R8-08 — HIGH — the two ladder plant operators are algebraically identical, so a HARD check is vacuous

**Fails:** `design.md:717–722` (§8 PLANT OPERATOR: *"Detection rates differ between the two, and
BOTH are emitted per rung"*), `design.md:1074` (§12 HARD **Ladder plant operator**).
**Code:** `metrics.py:409–413`.

The `via_p` operator solves `(1−p′)/p′ = ((1−p)/p)·exp(−δ)` at fixed `W, L`. Substituting into
`log R = log(W/L) − log((1−p′)/p′)` gives `log R₀ + δ` — **exactly** what the `via W/L` operator
produces. Both rungs then reduce to the same comparison against the same `half`.

**CONFIRMED by execution** on a 4,000-episode cell:

```
detect_wl: {0.02: 0.0, 0.03: 0.0, 0.05: 1.0, 0.075: 1.0, 0.1: 1.0, 0.15: 1.0}
detect_p : {0.02: 0.0, 0.03: 0.0, 0.05: 1.0, 0.075: 1.0, 0.1: 1.0, 0.15: 1.0}
IDENTICAL plant operators: True
```

Two columns are emitted, so the HARD check ("neither omitted") passes, but they carry one number.
The design's purpose for the pair — *"the pair shows how operator-dependent the cell's resolution
is"* — is defeated. The operators genuinely differ only in the **sampling variance** of `log R` under
each plant, which is visible only if the plant is applied to the episode data and the cell is
re-bootstrapped. The code plants on the point estimate, where the two are identical by the identity.

**Required fix (experiment-developer).** Apply each plant to the episode-level returns
(`W/L` plant: scale positive returns by `exp(δ)`; `p` plant: reassign the sign of a computed fraction
of episodes), rebuild the day sufficient statistics, and re-run the envelope. The detection rates
will then differ, as the design predicts.

#### R8-09 — HIGH — the sensitivity ladder reports 0/1 indicators, not detection rates, and mde50/80/95 are not interpolated from it

**Fails:** `design.md:710–737` (§8 RESOLUTION: *"the fraction of block-bootstrap replicates in which
a PLANTED effect of that size would have been detected"*; *"mde50/mde80/mde95 = the effect size
detectable in 50%/80%/95% of replicates, **interpolated from the ladder**"*), `design.md:1076`
(§12 HARD **Ladder emitted**).
**Code:** `metrics.py:406–420`.

```python
rates_wl[str(delta)] = float((point + delta - half) > 0)
...
out["mde50"] = float((0.0 + 1.96) * se)
out["mde80"] = float((0.841621 + 1.96) * se)
out["mde95"] = float((1.644854 + 1.96) * se)
```

No replicate is counted. The "rate" is a boolean cast to `0.0` or `1.0` — **CONFIRMED** in the R8-08
output above. And the three curve summaries come from a closed-form normal approximation on
`se = block_mde/1.96`, not from the ladder at all: the ladder and the summaries are two unrelated
computations that can disagree, since the ladder uses the cell's own `point` and the summaries
ignore it.

There is a governance edge here too. §8 explicitly retired a `finest_rung_detected` field because it
*"requires picking a privileged detection rate"*. A per-rung 0/1 indicator is that field in
distributed form: it hands each rung a binary verdict at an implicit 50% rate. Under AMENDMENT-C7
that is the shape the operator mandate removed.

**Required fix (experiment-developer).** For each rung, plant the effect on the episode data, run
the block envelope over `{1,3,7}` × 5 seeds, and report the **fraction of those 15 (block, seed)
CIs that exclude zero** — a genuine rate in `[0,1]`. Interpolate `mde50/80/95` from that curve.

#### R8-10 — HIGH — the Δ`log R` CI is fabricated arithmetic, not a block bootstrap — and Δ`log R` is the M15 primary read and the phase-(b) trigger

**Fails:** `design.md:800–836` (§8.1 BLOCK RULE, *"binding, both clocks, code-asserted"*),
`design.md:1059` (§12 HARD **Block rule**), `design.md:786–795` (§8.1: on M15 the primary read **is**
Δ`log R`), `design.md:380–385` (§4.3 phase-(b) trigger fires on Δ`log R` `ci_low > 0`).
**Code:** `metrics.py:476–491`.

```python
half = 0.5 * (wa + wb)          # wa, wb are FULL CI widths
return {"delta_log_R": d,
        "ci_low": d - half, "ci_high": d + half,
        "ci_width": 2 * half, "block_mde": half}
```

Three problems compound:

1. **It is not a bootstrap.** The difference is never resampled. §12 makes the block rule HARD "on
   this design's own reads"; the primary read on the primary clock is computed outside it entirely.
2. **The units are wrong.** `wa` and `wb` are full widths (`ci_high − ci_low`, `metrics.py:373`).
   Their average is used as a *half*-width, so the interval is roughly twice as wide as even the
   naive independent-sum construction would give.
3. **The dependence is backwards.** L1–L3 populations are strict subsets of L0 sharing identical
   fills and exits (`engine.py:366`), so `log R(layer)` and `log R(L0)` are strongly positively
   correlated and the difference CI should be **much narrower** than either. Treating them as
   independent-and-then-some throws away most of the design's power on exactly the read
   AMENDMENT-9 promoted to primary.

The same fabrication propagates to `layer_deltas.parquet` (`run_screen.py:407`) and to the
`L2_INTERACTION_HMM_X_K12` row, where `half = 0.5 · Σ` of three full widths
(`run_screen.py:365–374`, whose own comment reads `# crude CI`).

Direction note, for fairness: (2) and (3) push in opposite directions, so the net bias is not
determinable without running it. That is itself the problem — a CI whose coverage is unknown cannot
support the `ci_low > 0` condition that decides whether phase (b) exists.

**Required fix (experiment-developer).** Resample the **paired day-blocks jointly**: build day
sufficient statistics for both arms on a common day index, draw one block index set per replicate,
and compute `log R(layer) − log R(L0)` inside each replicate. Take the min/max envelope over
`{1,3,7}` × 5 seeds, exactly as the level read does. The same construction gives the interaction
term its CI.

#### R8-11 — HIGH — the §9 CI-relative band label is computed and then overwritten

**Fails:** `design.md:924–931` (§9 BANDS — the entire interpretation vocabulary),
`design.md:1349` (§15 `metrics_by_cell` must carry "band label (CI-relative)").
**Code:** `metrics.py:394–399` writes it; `run_screen.py:277` destroys it.

`cell_metrics` sets `out["band"]` to `ABOVE_THE_MIRROR` / `COVERS_THE_MIRROR` / `BELOW_THE_MIRROR`.
`_score_one_cell` then calls `m.update({..., "band": band, ...})` where `band` is the reporting band
`TRAIN` / `DESIGN` / `CONFIRM`. Same key, second write wins.

**CONFIRMED by execution:** `cell_metrics` returned `band = 'COVERS_THE_MIRROR'`; after the
`_score_one_cell` update the value is `'TRAIN'`.

Net effect: **no artifact carries the §9 band at all.** The design's only interpretation vocabulary —
and the vocabulary §4.3's phase-(b) trigger is written in — is silently absent from the emission. The
`log R never unaccompanied` HARD check does not catch it, because it tests only for `ci_low`,
`ci_high`, `ci_width`, `block_mde`.

**Required fix (experiment-developer).** Rename one of them. `mirror_band` for the CI-relative label
and `report_band` for TRAIN/DESIGN/CONFIRM is the least disruptive split; update `golden.py:137` and
`_score_cells`/`_layer_deltas` accordingly.

#### R8-12 — HIGH — G5 and G6 are hardcoded verdicts; G7 is never evaluated and is excluded from the pass set

**Fails:** `design.md:1024–1041` (§11 G5, G6, G7), `design.md:1082` (§12 HARD **Golden traces**:
"G1–G7 pass").
**Code:** `golden.py:159–179`, `selfcheck.py:213–217`.

- **G5** is a literal `{"status": "PASS", "note": "asserted in self-check: no fitted-slope residual
  column anywhere"}`. No such assertion exists — I grepped `selfcheck.py` for any fitted-slope or
  `0.9408` scan and there is none. §12 makes a fitted-slope residual appearing anywhere a **hard
  failure**; nothing looks for one. The trace the design says *"exists solely to make audit item A1
  non-repeatable"* is a string.
- **G6** is a literal `{"status": "DEFERRED_TO_TRIPWIRE1"}`, and `selfcheck.py:214` accepts
  `"DEFERRED_TO_TRIPWIRE1"` as a passing status. It defers to a tripwire that cannot fail (R8-01).
- **G7** is initialised `{"status": "MISSING"}` (`golden.py:170–171`) and upgraded to `FOUND` only if
  TRIPWIRE-2 reported a both-reachable count (`run_screen.py:785–791`) — which, per R8-02, is a count
  of synthetic bars. And `selfcheck.py:213–216` iterates `("G1","G2","G3","G4","G5","G6")` — **G7 is
  not in the tuple**. The trace the design singles out as *"the three clauses most likely to invert
  in code"* is both unevaluated and structurally excluded from the check that is supposed to gate it.

G1–G4 are honest: they locate the design's rows and emit the material for QA to re-derive. G1 I ran
and verified (Part B).

**Required fix (experiment-developer).** Add G7 to the self-check tuple. Implement G5 as a real scan
of every emitted artifact for a fitted-slope column or coefficient. Implement G6 against the real
TRIPWIRE-1 output once R8-01 is fixed. Implement G7 by finding the first real episode where the
episode's own target and trail are both reachable in one M1 bar and emitting which filled, at what
price, and `r`.

#### R8-13 — HIGH — the block rule is never checked clause by clause; `BLOCK_RULE_CLAUSES` is unused

**Fails:** `design.md:1059` (§12 HARD **Block rule (inherited)**: *"checked clause by clause against
§8.1's canonical six-clause list (never by string equality)"*), `design.md:813–817`.
**Code:** `config.py:285–292` (declared), `run_screen.py:722–729` (the actual check).

**CONFIRMED:** `grep -n "BLOCK_RULE_CLAUSES" screen_code/*.py` returns one hit — the definition. The
constant is never imported or read.

What the HARD check actually evaluates is `boot_eq["equivalent"]` — the result of
`assert_canonical_equivalence` at `block=3`, `seed=101`, `n_boot≤200`, on the first 5,000 episodes of
the whole frame regardless of cell (`run_screen.py:704–713`). That is a genuine and valuable check
(it passed when I ran it, Part B), but it verifies **one** clause: that the fast path matches the
library. It does not verify daily aggregation, the `{1,3,7}` sweep, the 1-day minimum against every
horizon in scope, the min/max envelope over blocks × 5 seeds, or the effective-block cap. §12 states
that "a different or partial sweep, a missing seed battery, a missing daily aggregation, a missing
small-`n` cap, or a block computed in bars is a **hard failure**" — none of those five conditions is
tested.

Nor is `source_ci_rule` in `resolution_basis.json` ever read and compared against the six clauses, as
§12 requires.

**Required fix (experiment-developer).** Assert each of the six clauses against the realised emission:
`BOOT_BLOCKS_DAYS == (1,3,7)`; day keys derived from `DAY_NS`; `min(BOOT_BLOCKS_DAYS)*24 >=` the
maximum `active_hold_hours` in the frame; `len(per_seed_ci) == 15` per cell; `effective_block < n_days`
on every cell; plus the existing equivalence probe. Read `source_ci_rule` from the basis artifact and
map each clause onto it.

#### R8-14 — HIGH — the M-3 magnitude-matched comparator matches on the selection variable and returns nothing

**Fails:** `design.md:524–538` (§6 CONTROL MAGNITUDE-MATCHED COMPARATOR — **MANDATORY** for L1 and
L3; *"matched on realised |decision-bar move| decile"*), `design.md:304–306` (§4.1b M-3 DECILES).
**Code:** `run_screen.py:645–654`.

```python
if "s_hat_decile" in l1.columns and "abs_r_decision_bps" in l0.columns:
    # build deciles of abs_r for M-3 on L0
    pass
controls_payload["magnitude_matched"] = controls_mod.magnitude_matched_comparator(
    l1["r_bps"].to_numpy(),
    l1["s_hat_decile"].to_numpy(), ...
    l0["s_hat_decile"].to_numpy(), ...)
```

The abandoned `pass` block names the correct implementation and does not perform it. What ships
matches on `s_hat_decile` — the **ŝ decile**, which is precisely the variable L1 selects on. For
`L1_SHAT_DECILE_GE7` the selected set is by definition `s_hat_decile ≥ 7`, so
`magnitude_matched_comparator:198–205` looks for complement episodes at deciles 7–10 and finds an
empty pool (`pool.size == 0 → continue`) for every decile that has demand. `draws` stays empty, every
seed appends `NaN`, and the payload comes back all-`NaN`.

The control the design calls MANDATORY, and whose necessity it justifies with a measured precedent
(*"SPDR-018 measured mag_high at percentile 0.46 against exactly this comparator — the distinction is
real and it has bitten before"*), is dead on arrival. The `abs_r_decision_bps` column it needs is
computed and carried on every episode (`panel.py:167–169`, `engine.py:58`) and never used.

Additionally: the comparator is run for L1 only. §6 makes it mandatory for **L1 and L3**; no L3 arm
gets one. And `comp_mask` (`run_screen.py:640–643`) is computed and discarded.

**Required fix (experiment-designer/developer).** Compute per-symbol expanding causal deciles of
`abs_r_decision_bps` per §4.1b, match the complement on those, and run the comparator for both L1 and
L3. Emit the comparator's own mean, its null quantiles and its plant curve per §6's disclosure clause.

#### R8-15 — HIGH — parent-gate parity passes vacuously on missing and NaN parent rows

**Fails:** `design.md:252–266` (§4.1a PARENT PARITY, HARD), `design.md:1062` (§12 HARD
**Parent-gate parity**), P-23/L-52.
**Code:** `parent_gates.py:257–275` and `run_screen.py:586–592`.

`run_all_parity` classifies each `(symbol, k)` into `failures` (status `FAIL`) or `ok` (status `OK`),
then sets `hard_pass = len(failures) == 0`. The three other statuses the same function can produce —
`NO_PARENT_ROW` (`:173`), `PARENT_NAN` (`:184`) and `NO_REGIME_ROWS` (`:234`) — fall into neither
bucket and therefore **pass**. If every symbol returned `NO_REGIME_ROWS`, `failures` would be empty,
`n_ok` would be `0`, and `hard_pass` would be `True`.

The fallback aggregate at `run_screen.py:586–592` is worse: it accepts
`status in ("OK", "PARITY_EXEMPT", "PARENT_NAN", None)` — explicitly admitting a NaN parent metric
**and** a missing key as passing, for symbols that are not on the exempt list. That aggregate is what
survives if `run_all_parity` throws (`run_screen.py:600–604` swallows the exception and keeps it).

The exempt-by-name mechanism itself is correct and closes R7-01's first limb (`parent_gates.py:176–182`).
The defect is that everything *outside* the exempt list also passes.

**Required fix (experiment-developer).** `hard_pass` must require `n_ok == 2 × (n_symbols −
n_parity_exempt)` and must fail on any `NO_PARENT_ROW`, `PARENT_NAN` or `NO_REGIME_ROWS` for a
non-exempt symbol. Remove the silent-exception fallback: a parity computation that raised is a
failure, not a pass.

#### R8-16 — MEDIUM — three HARD checks pass vacuously on an empty emission

**Fails:** `design.md:1105–1106` (*"missing or empty is a **failure**, never a vacuous pass (P-23)"*).
**Code:** `selfcheck.py:135–144` and `selfcheck.py:209–210`.

```python
max_ts = 0
for col in (...):
    if col in episodes_df.columns and len(episodes_df): max_ts = max(max_ts, ...)
mark("TRAIN fence", max_ts < TRAIN_END_NS if max_ts else True, ...)
mark("holdout",     max_ts < HOLDOUT_START_NS if max_ts else True, ...)
```

An empty `episodes_df` leaves `max_ts = 0` and both fences pass on the `else True` branch. Likewise
`fp = controls.get("fixed_point_count", controls.get("side_derangement", {}).get("fixed_point_count", 0))`
defaults to `0`, so the L-28 derangement check passes when the controls payload is absent entirely.

Note the fences themselves are correctly enforced upstream at read time (`catalog_io.py:60–65`,
Part B) — this is a self-check reporting defect, not a leak. But §12's check-count reconciliation
exists to make the *checks* countable, and three of them cannot fail on the path that matters most
(a run that produced nothing).

**Required fix (experiment-developer).** Require `len(episodes_df) > 0` and a present, non-empty
controls payload; fail otherwise with a stated reason.

#### R8-17 — MEDIUM — episode exclusivity is resolved in decision order, not fill order

**Fails:** `design.md:155–158` (§3: *"A symbol holds at most ONE open episode at a time; a signal
arriving while an episode is open is recorded as SUPPRESSED"*), `design.md:1078`.
**Code:** `engine.py:294 / 307`, `engine.py:382 / 402`, and `entry.py:126–137`.

Signals are iterated `sorted(..., key=lambda s: (s.decision_end_ns, -s.side))` while occupancy is
tested on `sig.fill_ts < open_until`. Because a stop order may fill anywhere in a 2-hour window,
`fill_ts` is **not** monotonic in `decision_end_ns`, so the two orders disagree.

Worked case (H1, `inactiveHold = 2h`): signal A decides at `t₀` and fills at `t₀+1.9h`, exiting at
`t₀+2.9h`. Signal B decides at `t₀+1h` and fills at `t₀+1.1h`. The loop reaches A first, admits it,
and sets `open_until = t₀+2.9h`; B is then suppressed because `t₀+1.1h < t₀+2.9h`. But B's episode
`[1.1h, 2.1h)` opened **before** A filled — at B's fill no episode was open, and at A's fill B's was.
The causal reading of §3 suppresses A and keeps B; the code does the reverse.

This is not a future-data leak — both events are in the past — but it changes episode membership on
every cell, systematically, and the effect grows on M15 where `inactiveHold = 2h` spans eight
decision bars. `entry.apply_exclusivity` has the identical structure and is additionally never called
by the engine (dead code with a docstring admitting the approximation).

**Required fix (experiment-developer).** Sort admitted candidates by `fill_ts` before applying
occupancy, or process in fill order and suppress a signal whose `fill_ts` falls inside an already-open
`[fill_ts, exit_ts)`. Re-run G3 afterwards.

#### R8-18 — MEDIUM — the exit scan drops the final M1 bar before the time exit

**Fails:** `design.md:134` (§2: *"a target or trail triggering **at or before** the time-exit bar's
open takes precedence"*).
**Code:** `fills.py:155–160`.

```python
end_i = int(np.searchsorted(ts, time_ts, side="left"))
for i in range(start, end_i):
```

`m1["ts"]` is the bar **close** timestamp — confirmed from `catalog_io.aggregate_clock:120`, which
computes `slot_start = (ts_event − 60·NS) // span · span`, i.e. `ts_event − 60s` is the bar open.
`time_ts` is the exit bar's `slot_start`, i.e. its open. With `side="left"` the scan covers bars whose
close is strictly `< time_ts`, so the M1 bar covering `[time_ts − 60s, time_ts]` — the last minute
before the exit — is excluded. A barrier touched in that minute is "at or before the time-exit bar's
open" and should fill at the barrier; instead the episode falls through to the time exit.

Small, but it is a systematic one-minute bias toward the time exit on every target and trail arm, and
it biases in the direction of the L0-like comparator.

Related, and worth confirming rather than fixing blind: `start = max(fill_m1_idx + 1, ...)`
(`fills.py:134`) excludes the entry bar itself from exit scanning. That is defensible (it avoids
manufacturing an intrabar entry-and-exit at unknowable ordering) but the design does not state it, so
it should be declared rather than left implicit.

**Required fix (experiment-developer).** Use `side="right"` for `end_i`, or equivalently scan bars
with `ts <= time_ts`. Declare the entry-bar exclusion in the design.

#### R8-19 — MEDIUM — realised effective sample size is the nominal `n` under another name

**Fails:** `design.md:836` (§8.1: *"Realised EFFECTIVE sample size is emitted per cell alongside n"*),
`design.md:1059` (§12: *"realised effective sample size and realised `c` emitted per cell alongside
`n`"*), `design.md:1354` (§15 `resolution_ladder.parquet`).
**Code:** `metrics.py:391`.

```python
out["effective_n"] = float(r.size)  # dependence-adjusted reported alongside; full form later
```

**CONFIRMED by execution:** `effective_n == n` → `True`, both `4000.0`.

The comment is an explicit deferral. The column ships under a name that asserts a dependence
adjustment which has not been made, and `resolution_ladder.parquet` carries it (`run_screen.py:562`).
§8.1's whole point in emitting it is that the M15 "~4×" lever is *"an upper bound on `n`, **not** on
precision, and the realised gain is whatever the emitted effective sample size says it is."* As
written, the artifact will say the gain is the full 4×.

**Required fix (experiment-developer).** Compute it — `n_eff = n · (block_mde_iid / block_mde)²` from
the two MDEs already on the row is the cheapest defensible form — or rename the column `n_nominal`
and record that the effective form is not computed.

#### R8-20 — MEDIUM — the declared 5-seed battery is not the battery that runs

**Fails:** `design.md:808` (§8.1 clause 4: *"5-SEED battery"*), `config.py:209`.
**Code:** `metrics.py:126–129`.

```python
for si in range(len(BOOT_SEEDS)):
    seed = BOOT_SEEDS[0] + si
```

`BOOT_SEEDS = (101, 211, 307, 401, 503)` is declared in `config.py:209` and the loop uses only its
length; the seeds actually drawn are `101, 102, 103, 104, 105`. Five seeds do run, so the clause is
satisfied in substance, and consecutive PCG64 streams are statistically fine. But `per_seed_ci` will
record seed values that are not the declared ones, the declared constant is misleading, and this is
the class of drift the seed-battery discipline exists to prevent.

Same construction is reused across every block length and every cell, which the design does not
forbid but also does not contemplate.

**Required fix (experiment-developer).** `for seed in BOOT_SEEDS:`.

#### R8-21 — MEDIUM — `zz_ordinal` is not sorted before the hold-forward walk

**Fails:** `design.md:268–271` (§4.1a ALIGNMENT: *"held forward … from its own availability
timestamp"*), `design.md:1068` (§12 HARD **Parent-gate provenance**).
**Code:** `parent_gates.py:63–66` vs `parent_gates.py:135–143`.

`load_regime_states` ends with `.sort("slot_end")`; `load_zz_ordinal` does not sort at all.
`_hold_forward` (`panel.py:78–83`) advances a single pointer `j` monotonically and assumes `src_end`
is ascending — with unsorted input it consumes rows out of order and holds forward whatever it
happened to reach, silently. Both T-GT-CUR and T-GT-MED5 are held forward from
`confirm_slot_end` through this path, so `L3_TGTCUR_FIRES`, `L3_TGTCUR_DOES_NOT_FIRE` and
`L3_TGTMED5_CO_REPORT` — the whole L3 stage — depend on it.

I did not confirm whether the parent artifact happens to be stored in `confirm_slot_end` order; if it
is, the bug is latent rather than active. Either way the code must not depend on the parent's storage
order.

**Required fix (experiment-developer).** `.sort("confirm_slot_end")` in `load_zz_ordinal`, or sort
the extracted arrays before the hold-forward. Add an ascending-order assertion inside `_hold_forward`.

#### R8-22 — MEDIUM — the plant curve is a point boolean, not a detection rate, and ignores side

**Fails:** `design.md:498–502` (§6: *"inject +5/+10/+20/+40 bps of **true side information**"*;
*"Report the **detection rate** at each rung"*; *"The control is reported UNUSABLE for any effect
below its own plant-curve resolution"*), P-24.
**Code:** `controls.py:233–249`.

```python
r_p = r + bps                       # unconditional mean shift, side ignored
lp = _logR(r_p)
out["detection"][str(bps)] = {"planted_log_R": lp,
                              "detected_vs_zero_point": bool(lp > 0), ...}
```

`side` is a parameter and is never read (**CONFIRMED** by execution — the emitted keys per rung are
`planted_log_R`, `detected_vs_zero_point`, `sigma_units` and nothing else). Adding a constant to
signed returns is a mean shift, not side information: it does not encode "the entry knew the
direction", which is what the side-derangement control needs a plant against. And there is no rate,
no CI, and therefore no resolution statement, so the design's UNUSABLE clause cannot be applied.

The σ̂ re-derivation is correct — `run_screen.py:628` passes the run-measured
`unit_pin["pooled_s_hat_median"]`, satisfying L-50/P-21's ban on carrying an absolute bps bar across
a universe boundary.

**Required fix (experiment-developer).** Plant side information: `r_p = r + bps · sign(side) ·
sign(r_true_direction)`, or equivalently flip a computed fraction of losing episodes to winners such
that the injected edge is `bps`. Then report the **fraction of the ≥2,000 deranged seeds** the
planted live value exceeds, per rung.

#### R8-23 — MEDIUM — fill rate, κ, homogeneity and collapse fraction are never computed

**Fails:** `design.md:1079` (§12 **Fill rate** — emitted per cell), `design.md:453–455` (§5 κ),
`design.md:937–946` (§9 POOLED — the pooled-primary read is **conditional** on an emitted homogeneity
statistic), `design.md:1349` (§15 `metrics_by_cell` column list).
**Code:** `run_screen.py:280–283`, `metrics.py:436`.

```python
"fill_rate": float("nan"),
"collapse_fraction": None,
...
out["kappa"] = float("nan")   # metrics.py:436
```

**CONFIRMED by execution:** `kappa` returns `nan`. `grep` finds no `homogeneity`, `I2` or
`i_squared` token anywhere in `screen_code/` — the statistic does not exist.

Consequences, in order of seriousness:

- **Homogeneity is the load-bearing one.** §9 grants the pooled-across-symbol read PRIMARY status
  *"only conditionally"*, and the condition is that an emitted `I²` supports pooling; absent it, the
  pooled line *"REVERTS to the lane default and is reported as disclosure-only"*. With no statistic
  emitted, the design's primary read has no stated basis, and `spdr-lane.md` L-03's default (pooled =
  disclosure-only) applies by omission.
- **Fill rate** is §2's named guard against a capture variant silently re-selecting its own
  population — which is exactly what the L4 arms do (each device's exit changes `exit_ts`, hence
  suppression, hence membership). The `signals` frame carries every `UNFILLED` / `SUPPRESSED` /
  `INELIGIBLE` row needed to compute it; it is simply never joined.
- **κ** and **collapse fraction** are disclosure-only diagnostics; their absence is a schema gap, not
  an inference risk.
- The realised sizing weight mean/sd that R7-04's fix promised (`design.md:319`) is likewise not
  emitted.

**Required fix (experiment-developer).** Join `signals.parquet` to compute per-cell fill rate,
suppressed count and ineligible-by-reason counts. Compute `I²` across the per-symbol `log R` values
behind each pooled cell. Compute κ from an MFE tracked during exit resolution. Attach each control's
collapse fraction to the cells it refereed.

#### R8-24 — MEDIUM — `check_no_local_accounting` FAILS

**Fails:** `spdr-lane.md` integrity boundary ("No local accounting primitives"), qa-compliance §3.
**CONFIRMED by execution:**

```
{"ok": false,
 "banned_defs_found": ["experiments/SPDR-019/screen_code/engine.py: def build_episodes"]}
```

The hit is `engine.build_episodes_for_variant` (`engine.py:454`), matched by prefix. On substance I
believe this is a false positive: the module computes signed gross bps per episode from two fill
prices (`fills.signed_r_bps:209–213`) and books no equity, no position ledger and no fee accrual —
there is no `xen.adjudication` mimicry, and `grep` for `adjudication` / `equity` / `booked` /
`pnl` over the tree returns nothing. But the check is a named gate in this skill's protocol, it
returns `ok: false`, and QA does not get to wave that through on judgement.

**Required fix (experiment-developer).** Rename to something outside the banned-prefix space
(`assemble_episodes_for_variant`) and re-run the checker to green, or obtain an operator-recorded
exemption naming this function.

#### R8-25 — LOW — the sizing arm computes a `log R` from weighted returns

**Fails (soft):** `design.md:319` (§4.2: *"**variance and comparability ONLY.** Reported on
dispersion, never on the mean … A sizing cell may not carry a `log R` claim"*), `design.md:1130`.
**Code:** `engine.py:439–440`.

```python
if meta.get("device") == "size":
    r = r * weight
```

A positive weight preserves the sign of `r`, so `p` is unchanged, but `W` and `L` both move and the
cell therefore produces a finite `log R`, a CI and a band like any other. The design's protection is
in place — `run_screen.py:278` emits `sizing_no_logR_claim: True` for both `L4_SIZE_*` variants — so
the claim boundary is disclosed and the analyst is warned. Recorded as a residual risk rather than a
violation: the number exists in the artifact and a reader who ignores the flag will read it.

**Suggested fix (experiment-developer).** Null the `log_R` / `ci_*` / band columns on sizing rows and
emit the dispersion statistics (`sd`, IQR of `r`) instead, so the forbidden claim is unavailable
rather than merely flagged.

#### R8-26 — LOW — abandoned scratch code ships inside the hashed module tree

**Code:** `metrics.py:203–318` (`sensitivity_ladder`).

**CONFIRMED:** the function is defined and never called (`grep` returns the `def` line only) —
`cell_metrics` inlines its own ladder at `:401–433`. What remains in the dead function is unreviewed
draft work:

```python
out["mde80"] = float(half * 1.28 / 0.0) if False else float(half * (1.2816 / 1.0))
...
out["mde50"] = float(0.67448975 / 1.95996398454 * half * 2)  # mess
# cleaner:
```

`out["mde50"]` is assigned six times in sequence; there are two `if False` guards over
division-by-zero expressions; and the comments (`# mess`, `# cleaner:`, `# FINAL simple mapping`)
record an unfinished derivation. It is inert today, but `selfcheck._sha256_tree` (`:45–50`) hashes
every `.py` in the directory into `integrity_selfcheck.json`, so this text is part of the pinned code
identity of the run.

**Required fix (experiment-developer).** Delete the function. If the ladder is reimplemented per
R8-09, write it fresh.

#### R8-27 — LOW — the determinism check is skipped under `--smoke`; `--resume` is a no-op

**Fails:** `design.md:1081` (§12: *"Determinism: runs **unconditionally** whenever `--jobs > 1`,
independent of `--resume`"*).
**Code:** `run_screen.py:495`, `run_screen.py:454`.

`if args.jobs > 1 and not args.smoke:` — under `--smoke --jobs 8` the check does not run, yet
`determinism_ok` was initialised `True` at `:494`, so `selfcheck.py:220–221` records the HARD
determinism check as **held** on a run where nothing was compared. "Unconditionally" admits no
`--smoke` exception.

`--resume` is declared at `:454` and never read anywhere in the file. Harmless, but the design names
it explicitly in the determinism clause, so its absence should be recorded rather than left as a
silently inert flag.

The check itself, when it runs, is sound: it re-runs one symbol sequentially and compares a sorted
JSON sha256 of the episode rows (`:499–505`).

**Required fix (experiment-developer).** Drop the `and not args.smoke`. Either implement `--resume`
or remove the argument.

#### R8-28 — LOW (feasibility, not validity) — two paths will not complete at full scale

Run 7's Advisory 2 flagged this as a sizing question; it is now concrete and measurable.

1. **`_p_stay_series` is O(n²).** `parent_gates.py:211–219` runs a full Python list comprehension
   over the `avail` list for every one of `n` bars. BTCUSDT has **12,503** H1 TRAIN bars
   (**CONFIRMED** — I loaded the bundle: 3.1 s, `H1 bars 12503`), giving ~1.6 × 10⁸ tuple
   comparisons per symbol, and it is invoked once per decision-clock panel per symbol *and* again for
   all 25 symbols inside `run_all_parity`.
2. **`_score_cells` memory.** `_resample_day_blocks` materialises `idx` of shape
   `(n_boot, n_days)` and then `suff[idx]` of shape `(n_boot, n_days, 8)` float64. For a pooled cell
   spanning ~900 TRAIN days at `n_boot = 2000`, that is ~115 MB **per bootstrap call**, and there are
   15 calls (3 blocks × 5 seeds) per cell. The cell grid is 32 variants × 2 clocks × 3 δ × 3 bands ×
   26 scopes ≈ 15,000 cells.

Neither is a correctness defect and neither blocks the verdict, which rests on R8-01…R8-06. But the
run as written will not finish, and `main()`'s wall-clock probe (`:473–488`) extrapolates from a
single-δ single-clock `n_boot=50` probe with a hardcoded `est_met = 300` seconds for the entire
metrics stage, so it will under-report by orders of magnitude.

**Suggested fix (experiment-developer).** Vectorise `_p_stay_series` with a cumulative count per
origin state. Chunk the bootstrap over `n_boot`. Re-derive the estimate from a real cell-scoring
probe.

#### R8-29 — LOW — parent-module import surgery deletes this experiment's own `config`

**Code:** `parent_gates.py:25–54`.

`_load_015_transitions` walks `sys.modules` and deletes any entry named `config`, `features`,
`transitions`, `controls`, `hmm` or `universe` whose `__file__` contains `SPDR-019` — i.e. it deletes
**this screen's own `config` module** — then mutates `sys.path` and re-keys the parent's modules under
`_SPDR_015__*` prefixes on the way out.

Because every SPDR-019 module binds its constants at import time (`from config import ...`), the
already-imported names keep working and a later `import config` merely creates a second, identical
module object. So I believe this is benign in practice. But it is unguarded global-state mutation in
a process that `run_screen.py` also runs under `mp.Pool` (`:243`), the `sys.path` insert/remove pair
is not exception-safe against concurrent imports, and it is invoked once per worker
(`run_screen.py:122`) plus once more in `run_all_parity`.

**Suggested fix (experiment-developer).** Load the parent module by explicit file path via
`importlib.util.spec_from_file_location` under a unique module name, touching neither `sys.path` nor
existing `sys.modules` entries.

---

### Checks independently verified clean

| Check | Result |
|---|---|
| TRAIN fence + holdout, code-asserted | **CLEAN — CONFIRMED.** `catalog_io.py:60–65` raises before any read if `end > TRAIN_END` or `end > HOLDOUT_START`; `:95–98` re-asserts on the loaded frame. `HOLDOUT_START = 2025-01-08T00:00Z`. The date bound is enforced in code, not documented. `TEST_START`/`HOLDOUT_START` are defined and never read. (The *self-check's* report of this is defective — R8-16 — but the fence itself holds) |
| Causal `t−1` by construction | **CLEAN — CONFIRMED.** Decisions use bar `[0]` = the most recent complete bar (`panel._complete_bars` filters on `complete`); the order is live only after `[0]` closes; `fills._first_m1_after` uses `side="right"` so fills are strictly after the decision close (verified on G1: `fill_ts > decision_end_ns`). Time exits are open-to-open. Parent labels are held forward with `src_end <= dst_end`, no backfill (`panel.py:79`) |
| No intrabar look-ahead in M1 resolution | **CLEAN — READ.** Entry and exit both scan M1 forward from the fill bar; the trail ratchets on `c[i]` only after bar `i`'s trigger test; adverse precedence taken on both-hit |
| Bootstrap == `xen.evaluation.block_bootstrap_ci` | **CLEAN — CONFIRMED.** `abs_diff = [6.2e-17, 5.0e-16]`, `equivalent: True` |
| Dependence-matched CI, block ≥ H | **CLEAN on the level read — READ.** Blocks are `{1,3,7}` **calendar days**; minimum 1 day = 24 h ≥ the longest horizon in scope (20 h, including the clipped `h_mod`). The Phase-010 `block=5` library default is not used anywhere. (The **delta** read is not block-bootstrapped at all — R8-10) |
| No local accounting in substance | **CLEAN on substance, FAILS the checker — CONFIRMED.** No `adjudication` / `equity` / `booked` / `pnl` token anywhere; `r` is signed gross bps from two fill prices. The checker's name-prefix hit is R8-24 |
| No money read (AMENDMENT-C5) | **CLEAN — CONFIRMED.** Cost appears only as `p_be_net` (flagged `DISCLOSURE_ONLY`) and `cost_bps_DISCLOSURE_ONLY`. No net figure enters an estimand, threshold, band or comparison. `SPREAD_COST_DISCLOSURE` carried verbatim with `spread_rt_bps: None`. The lane-wide spread blocker is respected |
| No adequacy flag / no canonical threshold (C7) | **CLEAN — CONFIRMED.** `grep -ri "powered\|unpowered\|at_target\|not_resolvable"` over `screen_code/` → no hits |
| Unit pin (L-21 / P-15) | **CLEAN — CONFIRMED.** Two divisor objects; ATR20 reaches only `entry.py:57`; every L4 width traces to ŝ; medians computed at run (BTCUSDT `s_hat_uncond = 22.859` bps) and written to `unit_pin.json`. σ̂ is never compared to the cost floor |
| 33 named variants | **CLEAN — CONFIRMED.** `config.py:119–154`, asserted at import, name-for-name against `design.md:192–198` |
| 28 HARD check names | **CLEAN as a list — CONFIRMED.** `config.py:251–282`, asserted at import, matching §12's HARD block by name. (What the checks *do* is R8-03) |
| Predeclaration consumed, never regenerated | **CLEAN — CONFIRMED.** Hash-verified before any data read; `strata` is the real key with 5,148 rows on the §8.1 grain; join key is `(clock, delta, variant_id, scope)` per §8.1's BAND AXIS clause |
| Universe pin / file equality | **CLEAN — READ.** `selfcheck.py:125–132` loads both files, asserts 25 symbols and set equality. Run 7 confirmed the two files are set-identical |
| L1 fixed-entry subset | **CLEAN — READ.** Subset holds by construction (L1–L3 clone L0 `Episode` objects) and is independently re-asserted on the 5-tuple key |
| Decile causality | **CLEAN — READ.** Per symbol, expanding, strictly before `[0]`, `min_hist = 250`. No pooled or full-TRAIN edge exists. (The §12 *assertion* of it is hardcoded — R8-03 — but the implementation is correct) |
| Identity reconstruction / `log R` slope 1 | **CLEAN — hand-derived.** Residual is zero by construction; G4 passes analytically; no fitted slope in the tree |
| L-28 zero fixed points | **CLEAN in outcome, unmeasured in method.** Full sign flip gives zero fixed points trivially; but the count is a hardcoded `0` rather than a measurement (R8-05) |
| Golden traces G1–G4 | **CLEAN — G1 CONFIRMED by execution.** G1 verified end to end against the catalog. G2/G3/G4 are honest selection-and-emit implementations. (G5/G6/G7 are R8-12) |
| Emission schema — the 12 §15 artifacts | **CLEAN on presence — READ.** All twelve paths are written by `run_screen.main`. Column-level gaps are R8-11 and R8-23 |
| Per-stratum rows / multiplicity disclosed | **CLEAN — READ.** `_score_cells` iterates `["POOLED"] + all symbols` × 3 bands × 3 δ × 2 clocks × 32 variants; nothing is machine-dropped |
| No XENA / TEST / holdout / family action | **CLEAN — CONFIRMED.** No XENA import, no TEST band read, no registry write |
| Spawn context under multiprocessing | **CLEAN — READ.** `mp.get_context("spawn")` with `freeze_support()`; polars/Rust thread pools do not survive fork, and the code says so |

---

### Golden-trace verdict

| Trace | Design expectation | Implementation | Verdict |
|---|---|---|---|
| **G1** entry + fill, L0 baseline | BTCUSDT H1 DESIGN, first LONG at δ=0.5: three bar OHLCs, pivot test, ATR20 at `[0]`, momentum ratio, stop = `high[0]`, first M1 through it, fill price, exit at 1 h, `r` | `golden.py:30–81` locates it; I executed the path independently: `decision_idx 37`, bar0 `20683.5/20866.0/20674.5/20831.5`, pivot `True`, `ATR20 173.5281`, momentum `0.8529`, `stop == high[0]` `True`, `fill_kind STOP` at `20866.0`, `fill_ts > decision close` `True` | **PASS — CONFIRMED** |
| **G2** expiry path | ETHUSDT H1 DESIGN, first SHORT unfilled within 2 h; emitted as unfilled; enters the fill-rate denominator only | `golden.py:84–101` selects `side < 0 and not filled` correctly. The fill-rate denominator it is supposed to enter is `NaN` on every cell (R8-23), so the second half of the trace is unverifiable | **PARTIAL** |
| **G3** suppression (B-9 guard) | First signal arriving while an episode is open → SUPPRESSED, counted, no second episode | `golden.py:104–127` locates the first `SUPPRESSED` row. The suppression it observes is decided in the wrong order (R8-17), so the trace will find *a* row but not necessarily the design's row | **PARTIAL** |
| **G4** the identity and primary read | Recompute `p, W, L` from episode rows, assert residual < 0.01 bps, recompute `log R` and match | `golden.py:130–157`. Residual is zero by construction. The lookup keys on `row["band"] == "CONFIRM"`, which works only because of the collision in R8-11 — fix that and this lookup must be updated to `report_band` or G4 goes MISSING | **PASS, fragile** |
| **G5** mirror null is the exact one | Assert null reference is 0 at slope 1, and that **no fitted-slope residual appears anywhere** | Hardcoded `{"status": "PASS"}` with a note claiming a self-check assertion that does not exist | **FAIL — vacuous** |
| **G6** leak discrimination | Confirm §6.1's three structural conditions on the G1 rows and that the legal variant entered the emission | Hardcoded `"DEFERRED_TO_TRIPWIRE1"`, accepted as passing, deferring to a tripwire that cannot fail | **FAIL — vacuous** |
| **G7** exit fill precedence | First M15 episode with target **and** trail reachable in one M1 bar: which fills under adverse precedence, at what price, `r`; plus trail ratchets on M1 closes only; plus a time-exit episode fills at the decision-bar open | Initialised `MISSING`; upgraded to `FOUND` only from TRIPWIRE-2's **synthetic** both-reachable count; and **excluded from the self-check's G-tuple entirely** | **FAIL — not evaluated** |

**Verdict: 1 PASS confirmed, 1 PASS fragile, 2 PARTIAL, 3 FAIL.** The design calls the golden traces
QA's strongest correctness lever, and the three that carry the most verification weight — the exact
mirror (G5), leak discrimination (G6) and exit precedence (G7) — are the three that are not computed.

---

### Standing execution blockers

1. **DISCHARGED (re-verified, not re-flagged)** — the AMENDMENT-7 / registered-C6 departure.
2. **DISCHARGED (re-verified this run)** — `reflection-inputs.md` §9. Signed option B at commit
   `9d8832e`; `git log` confirms *"sign the mid-checkpoint reflection (option B); record QA approval"*.
   No longer a blocker.
3. **STANDS (lane-wide, unchanged)** — the per-symbol spread pin is open; every money read stays
   blocked. It does **not** block this measurement under AMENDMENT-C5, and the code makes no money
   read (verified above).
4. **NEW — BLOCKING** — R8-01, R8-02, R8-03, R8-04, R8-05, R8-06. Six CRITICAL defects, each of
   which independently prevents the emission from being treated as valid. Four of them are HARD
   integrity checks that cannot fail; one is a control that cannot vary; one silently empties four
   of the 33 predeclared variants.
5. **NEW — must clear before execution** — R8-07 … R8-15 (nine HIGH). Each either fabricates a
   number the design requires be measured, or destroys a required output.
6. **NEW — must clear before execution** — R8-24. The named `check_no_local_accounting` gate returns
   `ok: false`.

---

**FAILING_ARTIFACT:** `python/experiments/SPDR-019/screen_code/` — specifically `run_screen.py`
(R8-01, R8-02, R8-03, R8-11, R8-13, R8-14, R8-23, R8-27), `controls.py` (R8-04, R8-05, R8-07,
R8-22), `parent_gates.py` (R8-06, R8-15, R8-21, R8-29), `metrics.py` (R8-08, R8-09, R8-10, R8-19,
R8-20, R8-26), `golden.py` (R8-12), `selfcheck.py` (R8-16), `engine.py` (R8-17, R8-24, R8-25),
`fills.py` (R8-18). `design.md` carries no open finding this run — R7-01 through R7-06 are all
closed in the text.

**REQUIRED_SKILL:** `experiment-developer` for R8-01 … R8-13 and R8-15 … R8-29.
`quant-designer` jointly with `experiment-developer` for R8-14 (the M-3 comparator needs its
matching variable and its L3 arm specified before it can be built).

**Execution authorisation: NO.**

The screen must not be run. Six CRITICAL findings sit on the integrity layer itself: two tripwires
that cannot fail, nine hardcoded HARD checks, a binding control that is dead code while its check
attests it ran, a 2,000-seed battery with one distinct value, and a one-token bug that empties four
predeclared variants. A run in this state would emit `all_hard_pass: true` — `run_screen.main` returns
`0` on that basis — over an emission whose validity was never tested. That is worse than a failed run,
because the artifact would carry a passing integrity record.

Re-QA is required after the fixes, not a re-read of a diff: the corrections to R8-01, R8-02, R8-04,
R8-09 and R8-10 change what is computed, not merely how it is reported.

---

### What I did not reach

Stated honestly, because a coverage claim is worth less than a coverage map.

- **I did not run the screen**, in whole or in part beyond single functions. It is operator-gated and
  unauthorised. Every runtime claim above comes from isolated function calls on synthetic inputs or
  on one symbol's real catalog data.
- **I loaded exactly one symbol's real data** (BTCUSDT). G1 is verified on that symbol only.
  G2 (ETHUSDT) and G3 (any symbol) I read but did not execute — G3 would have required an L0 build,
  which I judged too close to running the screen.
- **I did not execute the parent-gate path end to end.** `attach_gates`, `walk_forward_probs` and the
  parity comparison were read, not run — run 7 executed the regeneration and found it bit-identical,
  and I did not repeat that. `p_stay` I tested on a synthetic chain rather than real regime states;
  the bug is in the arithmetic and is data-independent, but the downstream count of emptied MOD-hold
  episodes is inferred, not measured.
- **R8-21 is unconfirmed as an active bug.** I did not check whether `zz_ordinal.parquet` happens to
  be stored in `confirm_slot_end` order. If it is, the missing sort is latent.
- **I did not measure the O(n²) cost in R8-28 or the bootstrap memory ceiling.** Both are derived
  from the loop structure and the confirmed 12,503-bar panel size, not from a timed run.
- **I did not audit `xen.evaluation.block_bootstrap_ci` internals**, only that the screen's fast path
  reproduces it bit-for-bit.
- **I did not review `python/experiments/SPDR-020/screen_code/`**, which appeared untracked in the
  same working tree and shares `resolution_basis.py` and the resolution artifacts. Several findings
  here — R8-05 (degenerate derangement), R8-08/R8-09 (ladder), R8-10 (delta CI), R8-19 (effective n) —
  live in code shapes that a sibling implementation by the same hand is likely to repeat. **That
  directory needs its own QA run; do not infer its state from this one.**
- **I did not verify the M15 clock path on real data at all.** Every execution above is H1. M15
  carries the primary read, a 4× larger bar count, and an 8-decision-bar `inactiveHold` window that
  makes R8-17's ordering defect materially more frequent — none of that is measured here.
- **I did not attempt to quantify the direction or size of any defect's effect on the result.** That
  is the data-analyst's object post-run, and there is no run.

---

## QA run 9 — 2026-07-29T17:30:40Z — mode: subagent — HEAD d3c9a79 (SPDR-019 unchanged since `0d08f48`)

**Reviewed git state:** `HEAD d3c9a795da7e3b508767c814729ae774bc310415`. `git diff 0d08f48 HEAD --
python/experiments/SPDR-019/` is **empty** — the two commits on top (`a4cdaa4`, `d3c9a79`) are
SPDR-020 only. Working tree carries two untracked SPDR-020 paths (`results/run_plan.json`,
`results/shards/`), both out of scope and untouched by me.
**Stage:** IMPLEMENTATION QA, re-review after remediation. 17 modules, 5,401 lines, two of them new
(`integrity.py`, `tripwires.py`).
**Independence:** fresh subagent context. I authored none of the design and none of the
implementation. `design.md` (1,396 lines) read in full including the new AMENDMENT-19; run 8 read in
full; runs 5–7 read for settled findings; `spdr-lane.md`, `lessons-and-amendments.md` (L-28 in full),
`pitfalls-ledger.md`, KB index and `_pipeline-config.md` read.

**Verdict: REVISE.**

**Execution authorisation: NO.**

The picture has changed materially. Run 8 rejected on an integrity layer that could not fail: two
tripwires that reconstructed their own evidence, nine HARD checks that were `True` literals, a dead
exit-matched control whose check attested it ran, a 2,000-seed battery with one distinct value, and a
one-token bug that emptied four predeclared variants. **All 29 run-8 findings are closed, 24 of them
confirmed by execution.** I ran the sanctioned smoke (2 symbols, `n_boot=200`, TRAIN-only) and then
attacked the emitted artifacts with injected faults: the checks that were literals now genuinely flip
to `False` when I corrupt the thing they check.

What blocks execution is narrower and is the same *class*, not the same *size*: **three of the 28
HARD checks still cannot fail on what they claim to verify.** One HARD check passes on garbage input
(`PARENT-GATE PROVENANCE`), and both tripwires now run against the live pipeline but each has a limb
that is structurally incapable of failing — TRIPWIRE-1 never reaches the L1 layer or any L4 arm, and
TRIPWIRE-2's favourable-precedence twin never calls the exit resolver it exists to test. Under
P-23/L-52 a check that cannot fail is indistinguishable from one that was skipped, and §12 makes all
three HARD. None of them corrupts a number in the emission — they are verification-coverage gaps, not
estimand defects — which is why this is REVISE and not a second REJECT.

Findings: **0 CRITICAL · 3 HIGH · 7 MEDIUM · 7 LOW.**

Every claim below is marked **CONFIRMED** (I executed it or hand-derived it) or **READ** (read-only).
No number appears that I did not produce.

**Smoke run, and its cleanup.** `run_screen.py --smoke --jobs 2 --n-boot 200`: 617,197 episodes,
1,260,603 signals, 1,758 metric rows (1,710 cells + 48 interaction), determinism bit-identical
(`96537d97a448` sequential vs parallel), 5.6 min, **28/28 HARD checks pass**. This reproduces the
developer's claim exactly on episodes, determinism and hard-pass; my cell count is 1,710 scored cells
against the claimed 1,758, which is the same number counted with the interaction rows included.
`results/` was restored afterwards to the three predeclaration files, hashes unchanged:
`resolution_basis.json 23d5f5bf1eb16d00…`, `expected_resolution.json e3247798edc9ab90…`,
`expected_resolution_prior.json 961cec28e28f6ff3…`. `git status` on SPDR-019 is clean.

---

### PART A — run-8 close-out, R8-01 … R8-29

| ID | Status | How I verified |
|---|---|---|
| **R8-01** TRIPWIRE-1 rebuilt its own input | **CLOSED — CONFIRMED** | The reconstruction branch is gone (`grep _tripwire_material` → 0 hits). `tripwires.tripwire_1:63-124` materialises both streams over the nine `GATE_ARRAYS`, re-runs `build_l0_episodes` + `select_layer_from_l0` on each, and compares episode key sets. Smoke emitted `changed_state_rows 45,117`, `changed_selection_episodes 122`, `legal 3,325 / leaky 3,329`, per-variant symmetric differences (L2_SHOCK 23, L3_TGTCUR 24, …). Real re-selection. **Residual coverage gap → R9-01** |
| **R8-02** TRIPWIRE-2 on synthetic prices + dummy fallbacks | **CLOSED — CONFIRMED** | All default arguments gone; `tripwires.tripwire_2:127-243` walks the real `L4_TARGET_A1_UNMOD` episode set. Twin (a) is a genuine second resolution: `fills.resolve_entry_stop_on_clock:86-120` re-resolves the same stop rule on decision-clock OHLC — smoke emitted `count_clock_vs_m1 = 851` differing ids with both fill prices per id. `price_identical_bars` counted separately (0). **Residual: twin (b) → R9-02** |
| **R8-03** nine HARD checks hardcoded `True` | **CLOSED — CONFIRMED by fault injection** | Every literal is replaced by a computation in `integrity.py`. I loaded the smoke's `episodes.parquet` (617,197 rows) and injected faults: one row with `fill_ts ≤ decision_end_ns` → `causality` **False**, `fill_causality` **False**; an ATR-proportional target width on `L4_TARGET_A1_UNMOD` → `l4_comparator` **False**; a pooled full-TRAIN decile → `decile_causality` **False**; `r_bps_side_flipped = −r_bps` on a target arm → `exit_matched` **False**; one altered L1 stop price → `l1_subset` **False**; `L4_HOLD_4H_MOD` holds set constant → `mod_hold` **False**. Empty frames fail every one. **Exception: `parent_prov` → R9-03** |
| **R8-04** exit-matched derangement dead code | **CLOSED — CONFIRMED** | The function is gone; the material is now built in the engine. `engine._build_variant:460-472` re-resolves the exit from M1 on the flipped side for target/trail arms (`TARGET_TRAIL_RERESOLVE`) and negates only on time-exit arms. `run_screen._run_controls:546-563` runs the side derangement on **11 arms** (L0 + 6 target + 4 trail), not one. Smoke `EXIT-MATCHED NULLS` detail: all 22 time-exit arms `max\|r_flip + r\| = 0` exactly; all 10 target/trail arms 631.0–1,098.4 bps |
| **R8-05** ≥2,000-seed battery = one value | **CLOSED — CONFIRMED** | `controls.derange_indices:35-49` draws a permutation with zero fixed points by rejection (≤50 tries, deterministic repair fallback); `side_derangement:107-113` flips only episodes whose deranged label differs. On 3,000 synthetic episodes at `n_seeds=2000`: **2,000 draws, 2,000 distinct values, null sd 0.0451, percentile 0.83, fixed points 0**. In the smoke every one of the 11 arms emitted `n_distinct = n_draws` with null sd 0.059–0.073. **Seed-count coupling → R9-05; residual alignment disclosure → R9-14** |
| **R8-06** `p_stay ≡ 1.0`, four MOD arms empty | **CLOSED — CONFIRMED** | `parent_gates._p_stay_series:236` now uses `stayed`, and the O(n²) scan is replaced by a per-origin-state `searchsorted`. On a synthetic two-state chain with true stay 0.642: **1,951 finite values, 1,293 distinct, mean 0.6565**. In the smoke all four MOD-hold arms are populated — 27,061 / 16,346 / 8,381 / 5,866 episodes — with holds spanning 1.000–1.933, 1.600–7.733, 4.800–20.0, 8.000–20.0 h. (My distinct-value count differs from the claimed 10,313, which was measured on real regime states, not my synthetic chain) |
| **R8-07** entry-timing derangement re-labelled realised P&L | **CLOSED — hand-derived + CONFIRMED** | `controls.entry_timing_derangement:185` now computes `r_d[i] = sign(side[i])·sign(side[donor])·r[donor]`. For a constant-hold time exit, `r = side·ambient(t,h)`, so this is exactly the donor window's ambient return scored under the receiver's side — the algebra is exact, not an approximation. The dead double-assignment and the unused `ambient_r_by_key` are gone (grep → 0). The function now **refuses** rather than approximating when holds vary (`NOT_APPLICABLE_VARIABLE_HOLD`, `:155-167`). Smoke: 200 draws, 200 distinct, null mean 0.00085, sd 0.0798, q05/q50/q95 −0.1256/0.0017/0.1469 |
| **R8-08** two plant operators algebraically identical | **CLOSED — CONFIRMED** | `metrics.resolution_ladder:280-302` applies both operators to the **resampled** totals, not the point estimate. On a 2,791-episode / 400-day cell at `n_boot=400`: `detect_wl {0.02:0.0125, 0.03:0.015, 0.05:0.0425, 0.075:0.11, 0.1:0.2125, 0.15:0.595}` vs `detect_p {…, 0.03:0.0125, …, 0.075:0.1025, …, 0.15:0.60}` — **IDENTICAL operators: False**. They are genuinely different objects. Note the separation is small (≤0.005 at most rungs), so the design's "the pair shows how operator-dependent the cell's resolution is" will read as "barely" |
| **R8-09** ladder emitted 0/1 indicators; mde50/80/95 not from the ladder | **CLOSED — CONFIRMED** | Rates are now `mean(planted > crit)` over finite replicates — **all values in [0,1], several strictly interior** (0.0125 … 0.595 above). `mde50/80/95 = crit − quantile(v0, 1−q)` (`:308-309`) is the exact analytic inversion of the primary operator's own curve, so summaries and rungs are one computation. Consistency check: rate(0.15) = 0.595 with mde50 = 0.1393 < 0.15 — coherent |
| **R8-10** Δ`log R` CI was fabricated arithmetic | **CLOSED — CONFIRMED** | `metrics.paired_combo_ci:513-591` draws **one** block index set per `(block, seed)` replicate and reuses it across all arms on a common day index. I instrumented `_resample_day_blocks`: a paired call makes **15 draws, seeds `[101,211,307,401,503]`** — one per replicate set, shared. Over 30 trials with a true zero (a 60% subset against its parent, 250 days, `n_boot=300`) the CI covered zero **29/30** with mean width 0.2225 against a true sampling spread of `2×1.96×sd = 0.1899` — i.e. ~17% conservative, which is what a min/max envelope over 15 CIs should be. (I did not reproduce the claimed "within 4%"; different construction, not a finding.) The same function carries the `L2_INTERACTION` row (`run_screen.py:439-443`) |
| **R8-11** §9 band computed then overwritten | **CLOSED — CONFIRMED** | Renamed to `mirror_band` (`metrics.py:422-427`); the reporting band keeps `band`. Both survive in `metrics_by_cell.parquet`: `band ∈ {TRAIN, DESIGN, CONFIRM}`, `mirror_band` = 1,489 COVERS / 104 ABOVE / 9 BELOW / 156 null. `golden.py:136` G4 correctly keys on the reporting `band == "CONFIRM"`; the ladder projection (`run_screen.py:873-881`) does not carry `mirror_band` and does not need it. No reader of the old key remains. **156 nulls → R9-16** |
| **R8-12** G5/G6 hardcoded, G7 unevaluated and excluded | **CLOSED — CONFIRMED** | G5 is a real scan of emitted column names **and** the screen's own source for six forbidden tokens (`golden.scan_for_fitted_slope:174-203`) — smoke scanned 84 columns, 0 offending. G6 reads the real TRIPWIRE-1 payload. G7 reads the real TRIPWIRE-2 payload and emitted a real episode: `m1_ts 1658337060…`, SHORT, adverse 23601.328 / favourable 23493.672, `r` −22.859 / +22.859. `selfcheck.py:231` now iterates all seven. **Residual: two hardcoded sub-clauses → R9-12** |
| **R8-13** block rule never checked clause by clause | **CLOSED — CONFIRMED** | `integrity.check_block_rule:325-441` evaluates all six clauses and reads `source_ci_rule` from the basis artifact, matching each clause by keyword rather than string equality. Smoke: all six `held: True`, `source_ci_rule_covers_clause` all `True`, `min_observed == max_observed == 15` per-seed CIs on 1,649 cells, `effective block < n` checked on 5,127 block records, `max_active_hold_hours 20.0 ≤ min_block_hours 24`. It **fails** when I set holds to 48 h, when a cell has 5 per-seed CIs, and on an empty metrics list. **Exemption gap → R9-04** |
| **R8-14** M-3 comparator matched on the selection variable | **CLOSED — CONFIRMED** | `panel.py:172-178` computes `abs_r_decile` per symbol, expanding, causal, 250-bar warm-up; `run_screen._run_controls:588-613` matches the complement on it and runs the comparator for **L1 and L3** (six arms). Smoke: every arm returned 200 draws / 200 distinct with per-decile matching, e.g. `L1_SHAT_DECILE_GE9` live 0.6141 vs null mean 0.0943 (pct 0.98); unmatched deciles disclosed by name (`['2','3']` on two L3 arms). The complement is the layer's excluded L0 set — disjoint by construction |
| **R8-15** parity passed vacuously on NaN / missing | **CLOSED — READ + CONFIRMED** | `parent_gates.run_all_parity:289-321`: `hard_pass = no failures AND n_ok == 2×n_non_exempt AND n_non_exempt > 0`; `NO_PARENT_ROW`, `PARENT_NAN`, `NO_REGIME_ROWS` and a missing cell all append to `failures`. The silent-exception fallback is gone — `run_screen.py:821-831` records a raised parity as `hard_pass: False` with the traceback. Smoke: `n_ok 4/4`, `failures []` |
| **R8-16** three checks passed vacuously on an empty emission | **CLOSED — READ** | `selfcheck.py:142-150` requires `have_ts = n_eps > 0 and max_ts > 0`; the `else True` branch is gone. `derangement fixed-point count` (`:217-227`) now requires at least one control that reported `fixed_point_count_measured` and defaults to `None`, not `0`. `identity reconstruction` requires `n_checked > 0`; `log R definition` requires `n > 0` |
| **R8-17** exclusivity in decision order | **CLOSED — CONFIRMED** | `engine._apply_exclusivity_in_fill_order:319-338` sorts candidates by `(fill_ts, decision_end_ns, −side)` and tests occupancy on `fill_ts < open_until`. The dead `entry.apply_exclusivity` is gone (grep → the fill-order function only). Smoke signal accounting: 617,197 EPISODE / 307,222 SUPPRESSED / 183,143 INELIGIBLE / 152,754 UNFILLED / 287 NO_EXIT — nothing dropped |
| **R8-18** exit scan dropped the last M1 bar | **CLOSED — READ** | `fills.py:211` uses `side="right"`, with the reasoning inline. The entry-bar exclusion is now declared in the design (AMENDMENT-19b, `design.md:135`) |
| **R8-19** `effective_n` was `n` renamed | **CLOSED — CONFIRMED** | `metrics.py:404-418` builds an iid half-width at the **same alpha** via the delta method and reports `effective_n = n·(iid_half/block_mde)²`, with `n_nominal` alongside. On 2,400 episodes over 300 days: **independent → ratio 0.802; day-clustered (day-level mean shocks) → ratio 0.187**. The column now moves with dependence. Smoke median `effective_n/n = 0.724`. (I did not reproduce the claimed 0.96 / 0.08; my clustering strength differs. Direction and magnitude order confirmed) |
| **R8-20** declared 5-seed battery not the one that ran | **CLOSED — CONFIRMED** | `metrics.envelope_ci_logR:146` and `paired_combo_ci:559` both iterate `for seed in BOOT_SEEDS`. My instrumented paired call recorded seeds `[101, 211, 307, 401, 503]` — the declared constants |
| **R8-21** `zz_ordinal` unsorted before hold-forward | **CLOSED — READ** | `parent_gates.load_zz_ordinal:88-90` sorts on `confirm_slot_end`, and `panel._hold_forward:78-79` **raises** on a non-ascending source rather than walking it silently. Both limbs of the fix are present |
| **R8-22** plant curve a point boolean ignoring side | **CLOSED in letter — CONFIRMED** | `controls.plant_curve:294-304` emits `detection_rate_vs_null` per rung against the control's own ≥2,000 draws, plus σ̂ units re-derived from the run-measured pooled σ̂ (smoke: 25.577 bps). It is a rate, not a boolean. **But the curve saturates → R9-06** |
| **R8-23** fill rate, κ, homogeneity, collapse never computed | **CLOSED — CONFIRMED** | All four exist. Smoke: `fill_rate` finite on 97.3% of rows (`run_screen._signal_counts:273-301` joins the signal frame); `kappa` finite on 97.3% (`metrics.py:438-445` from `fills.mfe_bps`); `i_squared` on 533 of 594 pooled rows with `pooled_status`/`per_symbol_spread_log_R` (`metrics.homogeneity:454-479`, `_attach_homogeneity:617-657`); `collapse_fraction` attached to the 11 cells the controls actually refereed and `NOT_REFEREED` elsewhere |
| **R8-24** `check_no_local_accounting` FAILED | **CLOSED — CONFIRMED by execution** | `build_episodes_for_variant` → `assemble_episodes_for_variant` (`engine.py:511`). `check_no_local_accounting("experiments/SPDR-019/screen_code")` → `{"ok": true, "banned_defs_found": []}` |
| **R8-25** sizing arm carried a `log R` | **CLOSED — CONFIRMED** | `run_screen._score_one_cell:259-269` nulls `log_R`, `ci_*`, `block_mde`, `mirror_band`, `mde50/80/95`, `realised_c`, `ladder` on both sizing variants and emits `sizing_dispersion_sd_bps` / `_iqr_bps` plus `log_R_suppressed_reason`. Smoke: 108 sizing rows, `log_R` null on all, dispersion present on all, `n_episodes` present on all, and all 108 still appear in `resolution_ladder.parquet`. `_layer_deltas` skips them per §4.2. **One silent drop found → R9-04** |
| **R8-26** abandoned scratch code in the hashed tree | **CLOSED — CONFIRMED** | `sensitivity_ladder`, `if False`, `# mess` → 0 hits. **A smaller instance remains → R9-15** |
| **R8-27** determinism skipped under `--smoke`; `--resume` inert | **CLOSED — CONFIRMED** | `run_screen.py:765` is `if args.jobs > 1:` with no smoke exception, and `determinism_ok` initialises to `None` so a check that did not run cannot record as held. `--resume` removed (grep → 0). My `--smoke --jobs 2` run **did** execute it: `determinism OK 96537d97a448 vs 96537d97a448` |
| **R8-28** two paths would not complete at full scale | **CLOSED — CONFIRMED** | `_p_stay_series` is now `searchsorted`-based, not O(n²). `metrics._boot_totals:94-108` chunks at 250 replicates, bounding peak memory to one chunk. `main()` replaces the hardcoded `est_met = 300` with a real cell-scoring probe (`:720-756`). Measured: 2 symbols × 2 clocks × 3 δ in 5.6 min at `n_boot=200`, ~95 s per symbol for the episode stage. Extrapolation to 25 symbols at `n_boot=2000` is the operator's call on the emitted `run_estimate.json`, not mine |
| **R8-29** import surgery deleted this screen's `config` | **CLOSED — READ** | `parent_gates._load_by_path:31-64` loads each parent module from an explicit path under a `_SPDR_015__` key, aliases bare names only for the duration of the load inside `try/finally`, and **never** mutates `sys.path` or deletes an existing entry. Ran clean under `mp.Pool` spawn with 2 workers |

**Run-8 standing blockers.** Blockers 1 and 2 remain DISCHARGED (re-verified, not re-flagged).
Blocker 3 (lane-wide spread pin) **STANDS** and is respected: `SPREAD_COST_DISCLOSURE` carried
verbatim with `spread_rt_bps: null`, `SPREAD_BPS_PROHIBITED = True`, and the only cost objects in
`metrics_by_cell` are `cost_bps_DISCLOSURE_ONLY`, `p_be_net`, `p_be_net_flag` and
`spread_cost_status` — CONFIRMED on the emitted frame. Blockers 4, 5 and 6 are **DISCHARGED** by the
close-outs above.

---

### PART B — new findings

#### R9-01 — HIGH — TRIPWIRE-1 never reaches the L1 layer or any L4 arm

**Fails:** `design.md:556-558` (§6.1 TRIPWIRE-1: *"rebuild **every layer's** conditioning state from
bar `[+1]`"*), `design.md:1063` (§12 HARD Causality), P-23/L-52.
**Code:** `tripwires.py:39-45` and `tripwires.py:92-100`; `engine.py:124-139`; `entry.py:75-85`.

The tripwire shifts nine panel arrays and re-runs the build. But L1's conditioning state is not read
from the panel: `engine._select_mask:124-139` reads `sig.s_hat_decile` and `sig.s_hat_rank` off the
`Signal` object, which `entry.detect_signals:75-85` froze from the **original** panel — and
`tripwires.tripwire_1:92-93` hands the **same** `base_sigs` list to both builds. Shifting
`panel.s_hat_decile` therefore cannot change an L1 selection.

**CONFIRMED on the emission.** `per_state_array` records `s_hat_decile: 2,164` and `s_hat_rank:
12,126` changed rows, while `per_variant` records:

```
L1_SHAT_DECILE_GE5 0 · L1_SHAT_DECILE_GE7 0 · L1_SHAT_DECILE_GE9 0 · L1_SHAT_RANK_CONTINUOUS 0
L2_SHOCK_HMM 23 · L2_LEVEL_RMARKOV_K12 20 · L2_LEVEL_RMARKOV_K4 11 · L2_JOINT 13
L3_TGTCUR_FIRES 24 · L3_TGTCUR_DOES_NOT_FIRE 24 · L3_TGTMED5_CO_REPORT 7
```

All 122 of the `changed_selection_episodes` come from L2 and L3. Separately, `LAYER_VARIANTS`
(`tripwires.py:39-45`) contains no `L4_*` id at all, so `p_stay` (11,855 changed rows) and
`n_prior_trans` (11,911) — the MOD-hold arm's entire conditioning state — reach no episode
comparison either. The HARD pass is carried by the layers that happen to read the panel.

**Required fix (experiment-developer).** Rebuild the `Signal` stream from the leaky panel (or shift
the ŝ fields on the Signal objects) so L1 is exercised, and add the four `L4_HOLD_*_MOD` arms to the
variant list. Emit `changed_selection_episodes` per variant as a **required non-zero** for every
variant whose gate array the shift actually changed, not as a pooled sum.

#### R9-02 — HIGH — TRIPWIRE-2's favourable-precedence twin never calls the exit resolver; clauses 3 and 4 cannot fail

**Fails:** `design.md:583-599` (§6.1 TRIPWIRE-2 clauses 3 and 4, and *"The third clause is what
proves the adverse rule is actually implemented"*), `design.md:1088`, P-23/L-52.
**Code:** `tripwires.py:196-224`; `fills.py:159, 238-242` (the branch under test).

`resolve_target_trail_time` accepts `favourable_precedence` and inverts the both-reachable branch at
`fills.py:238`. **CONFIRMED: it is never passed `True` anywhere** — `grep favourable_precedence
screen_code/*.py` returns only the definition (`fills.py:159`), the branch (`:238`), the pass-through
(`engine.py:262, 273`) and an unrelated key name (`tripwires.py:234`). The adverse-precedence branch
the tripwire exists to prove is dead code in every run.

What the twin does instead is arithmetic on a constructed pair, and both remaining clauses are
tautologies:

- **Clause 3** (`count_favourable_diff == count_both_reachable`): `both_ids.append` and
  `fav_ids.append` are the same two lines of the same block (`tripwires.py:205-208`). Equality holds
  by construction. **CONFIRMED** by source and by the emission (`4 == 4`).
- **Clause 4** (*"the favourable twin's fill price is mechanically no worse"*): `favourable_px =
  ep.target_price` and `adverse_px = trail_level` sit on opposite sides of `ep.fill_price` by
  construction (`:189, 206-207`), so the LONG/SHORT inequality at `:221-224` cannot fail. The
  emitted G7 row shows the signature: `adverse_r_bps −22.859`, `favourable_r_bps +22.859` — exact
  negatives, because at `a = 1, b = 1` the constructed trail mirrors the target.

A third point of substance: `emitted_exit_price` is labelled as the emitted arm's fill but is the
**constructed** trail level; the real episode exited at its target or at time. §6.1 asks for a
comparison against the emitted arm's price.

**Required fix (experiment-developer).** For each constructed both-reachable episode, call
`resolve_target_trail_time` twice with the same target and trail — `favourable_precedence=False` and
`True` — and derive both counts and both prices from the returned `ExitFill`s. Clause 3 then measures
something (the two id sets can differ) and clause 4 compares two resolver outputs.

#### R9-03 — HIGH — PARENT-GATE PROVENANCE passes on garbage

**Fails:** `design.md:1079` (§12 HARD **Parent-gate provenance**: *"each layer's gate reads exactly
the model/field/rule pinned in §4.1a … and the outcome label `y` and realised swing magnitude appear
in **no** gate input — a **hard failure** if they do"*), `design.md:273-276`, P-23/L-52.
**Code:** `integrity.py:139-157`.

```python
rows = (parent_parity or {}).get("rows") or []
if not rows:
    return _fail("parent parity emitted no rows")
...
return True, {"pinned_fields": fields, "n_symbols_with_parent_rows": n_with_gate, ...}
```

The verdict is `True` whenever the parity payload has at least one row. The `fields` dict is a
**string literal**, not a read of what the code actually consumed. Nothing checks the firing rules,
nothing checks the hold-forward direction, and — the clause §12 states as a hard failure — **nothing
looks for `y`, `mag_k1`, `next_abs_oo` or `run_len_*` in any gate input.**

**CONFIRMED by execution:** `integrity.check_parent_provenance(episodes, {"rows": [{"junk": 1}]})`
→ `True`. This is the R8-03 shape, relocated into the new file.

**Required fix (experiment-developer).** Assert the columns actually read in `parent_gates.attach_gates`
(`s_hmm_rv`; `walk_forward_probs(...)["logistic_ridge"]`; `logit_ridge` with `p >= 0.5`; `ridge_cont`
with `pred_cont > threshold` on the same row), assert the forbidden names against every array bound
onto the panel, and assert that each gate came through `_hold_forward` (whose ascending guard already
raises).

#### R9-04 — MEDIUM — the block-rule degenerate exemption is uncapped, unvalidated, and silently drops every sizing row

**Fails:** `design.md:1070` (§12 BLOCK RULE: *"a missing seed battery … is a **hard failure**"*),
`design.md:1116-1117` (*"missing or empty is a **failure**, never a vacuous pass"*).
**Code:** `integrity.py:354-380`.

`held = bool(per_seed_counts) and min(per_seed_counts) == 15`. **One** compliant cell satisfies the
clause regardless of how many cells were exempted. **CONFIRMED:** 1 compliant row + 5,000 fabricated
degenerate rows → `held: True`, `n_cells_with_a_ci: 1`, `n_degenerate_cells_no_ci: 5000`. Nothing
asserts that a degenerate cell is actually too thin to bootstrap — `n_dates` is recorded and never
tested — so any future bug that empties `per_seed_ci` while nulling `ci_low` widens the exemption
silently. The artifact also truncates `degenerate_cells` to 50 (`:379`) while the design's own
exemption model (§4.1a PARITY-EXEMPT) is by **name and count**.

Second limb, and this is the sizing question directly: a row with a **non-empty** `per_seed_ci` and a
**null** `ci_low` falls into neither branch and is silently dropped. That is exactly the sizing-row
shape after the R8-25 suppression. **CONFIRMED on the emission:** `n_cells_with_a_ci 1,649` +
`n_degenerate 1` = 1,650 against 1,758 metric rows — the 108 missing rows are precisely the 108
sizing cells. Their per-seed batteries are real and compliant; they are simply not counted anywhere,
and nothing records that they were skipped.

**Required fix (experiment-developer).** Require a stated reason per exempted cell (e.g. `n_dates <
2`) and fail otherwise; emit the full degenerate list, not the first 50; classify suppressed-`log R`
rows as an explicit third bucket, counted and named.

#### R9-05 — MEDIUM — the ≥2,000-seed control battery is coupled to `--n-boot` and asserted nowhere

**Fails:** `design.md:506` and `design.md:525` (§6: *">= 2000 seeds"* on both derangements),
`spdr-lane.md` integrity boundary (seed-battery rule, L-19).
**Code:** `run_screen.py:837`.

```python
n_ctrl = min(2000, max(50, n_boot))
```

The control seed count is an operator CLI flag in disguise. **CONFIRMED:** at `--n-boot 200` every
arm emitted `n_seeds: 200`, `n_null_draws: 200`, including the entry-timing control. A default run
(`n_boot = 2000`) satisfies §6, but no HARD check reads `n_seeds`, so a run at a reduced `--n-boot`
would emit a 50-seed derangement under a passing `derangement fixed-point count` check.

**Required fix (experiment-developer).** Pin the control battery to 2,000 independent of `n_boot`, or
add `n_seeds >= 2000` to the derangement HARD check.

#### R9-06 — MEDIUM — the plant curve saturates at every rung, so §6's UNUSABLE clause is inoperable

**Fails:** `design.md:506-510` (§6: *"Report the detection rate at each rung. The control is reported
**UNUSABLE** for any effect below its own plant-curve resolution"*), P-24.
**Code:** `controls.py:294-304`.

The plant is added to the **live** series (`lp = _logR(r + bps)`) and scored against the control's own
null. The live value already sits near percentile 1.0 against that null, so every rung clears it.
**CONFIRMED on the emitted `L0_BASELINE` curve:**

```
5 bps (0.195 σ̂) → 1.0   10 bps (0.391 σ̂) → 1.0
20 bps (0.782 σ̂) → 1.0   40 bps (1.564 σ̂) → 1.0
```

A curve that reads 1.0 at its finest rung states no resolution. Nothing below 5 bps can be declared
UNUSABLE, and nothing above it is informative either. The σ̂ re-derivation is correct (run-measured
pooled σ̂ = 25.577 bps, L-50/P-21 satisfied) — the defect is the base the plant is applied to.

**Required fix (experiment-developer).** Plant into a null-equivalent series (one deranged draw), so
the curve rises from ≈ α at the finest rung and the UNUSABLE threshold becomes readable.

#### R9-07 — MEDIUM — the L-51 selection check covers 5 of the subsets §12 names and is verified only by count

**Fails:** `design.md:1081` (§12 L-51: *"runs on **every** selected subset the design or analysis
reports separately — L1's `d≥5/d≥7/d≥9` cuts, L2's state cells, L3's gate, L5's combination, and
cells above vs below median `mde50`"*), `design.md:1390` (§15).
**Code:** `run_screen.py:884-897`; `selfcheck.py:279-281`.

Five subsets are built — `L1_SHAT_DECILE_GE{5,7,9}`, `L2_SHOCK_HMM`, `L3_TGTCUR_FIRES` — H1 only,
with the three δ levels pooled together. **CONFIRMED** in `selection_check.json`: `n_checks: 5`.
Missing: `L2_LEVEL_RMARKOV_K4`, `L2_LEVEL_RMARKOV_K12`, `L2_JOINT_HMM_HIGH_AND_K12_HIGH`,
`L3_TGTCUR_DOES_NOT_FIRE`, `L3_TGTMED5_CO_REPORT`, the M15 clock, and the **cells above vs below
median `mde50`** split the design names explicitly. The HARD check asserts only `n_checks > 0`, so it
cannot notice.

#### R9-08 — MEDIUM — DECILE CAUSALITY separates only the worst case, and `warm_up_ok` is a literal

**Fails:** `design.md:1071` (§12 DECILE CAUSALITY: *"computed **per symbol** on an **expanding**
window using only bars strictly before the decision close, after the declared warm-up; a pooled or
full-TRAIN decile edge anywhere is a **hard failure**"*), `design.md:288-301`.
**Code:** `integrity.py:160-207`, specifically `:186-192` and `:188`.

The verdict is `overlap > 0`, where overlap counts decile pairs whose raw ŝ ranges intersect across
the pool. A **full-TRAIN pooled** edge gives zero overlap and is caught — **CONFIRMED:** injecting a
global percentile-rank decile flipped the check to `False`. But a **pooled-yet-expanding** edge also
produces overlap, because the edges drift with time, so the §4.1b *population* clause (per symbol) is
not what is tested. Smoke emitted `cross_symbol_decile_value_overlaps: 45` on two symbols.

`warm_up_ok` is assigned `True` at `:188` and never computed, then emitted as evidence.

**Required fix (experiment-developer).** Recompute a sample of edges per symbol from that symbol's own
history strictly before `[0]` and diff against the emitted decile; compute `warm_up_ok` from the
minimum history length behind each emitted edge, or drop the field.

#### R9-09 — MEDIUM — L4 COMPARATOR IDENTITY tests only the ATR half of the clause

**Fails:** `design.md:1076` (§12: the two arms *"share estimator, unit, clock, horizon scaling and
multiplier, differing **only** in constant-per-symbol-TRAIN-median ŝ vs conditional ŝ(t,h)"*).
**Code:** `integrity.py:107-121`, specifically `:111`.

`arm_ok = not atr_const`. `width_over_shat_is_constant` and `expected_shat_tracking` are computed
(`:107-117`), emitted, and never read into the verdict — so nothing asserts that the MOD arm tracks
ŝ(t) or that the UNMOD arm is constant per symbol. The ATR half is real and does fail: injecting an
ATR-proportional target width flipped the check to `False` (**CONFIRMED**). Smoke emitted
`atr_matches 0`, `shat_matches 5` (the five MOD arms), which is the correct pattern — it just is not
asserted. `_is_constant` also returns `False` for any arm with fewer than 2 finite widths (`:134`),
so a one-episode arm passes.

#### R9-10 — MEDIUM — TRIPWIRE-2 runs on one symbol, chosen by whether its HARD condition holds

**Fails:** `design.md:551-553` (§6.1: the tripwires *"pass or fail on counts and identities that are
decided by the construction"*), P-23.
**Code:** `run_screen.py:906-912`.

```python
for tm in sorted(tw_mats, key=lambda t: t.get("symbol", "")):
    if tm.get("tripwire_2", {}).get("count_both_reachable", 0) > 0:
        tw1, tw2, tw_symbol = ...
        break
```

The reported tripwire is the **first symbol whose clause-2 count is non-zero**. With 25 symbols that
makes `count(both_reachable_bar_ids) > 0` near-unfailable by selection rather than by construction —
a milder relative of R8-01. It is deterministic and `tripwire_symbol` is emitted, so it is disclosed
rather than hidden. Note also how thin the passing evidence is: **CONFIRMED** `count_both_reachable
= 4` on BTCUSDT against roughly 30k `L4_TARGET_A1_UNMOD` episodes. TRIPWIRE-1 rides on the same
selection.

**Required fix (experiment-developer).** Pre-declare the tripwire symbol (BTCUSDT, the golden-trace
anchor), or run both tripwires on every symbol and pool the counts and the id lists.

#### R9-11 — LOW — MOD-HOLD ELIGIBILITY tests a different predicate from §12

**Fails (soft):** `design.md:1080` (§12: *"A MOD row whose holds are **identical to its UNMOD twin on
every episode** is a hard failure"*).
**Code:** `integrity.py:298-301`.

The code tests `ptp(mod holds) > 1e-9` — that the MOD arm **varies** — and never compares the two
vectors. The two predicates differ: a MOD arm constant at some value ≠ `h` fails the code and passes
the design. Currently moot: **CONFIRMED** all four pairs vary on the smoke (h=1: 1.000–1.933; h=4:
1.600–7.733; h=12: 4.800–20.0; h=20: 8.000–20.0), with 361 events excluded per arm for
`MOD_HOLD_WARMUP`. Worth noting for the operator: `h_mod = clip(h·E_run/20, 1, 20)` pins the h=1 arm
at exactly 1.0 — the UNMOD hold — for every episode with `E_run ≤ 20`, i.e. across most of the
design's own measured 19–23 h E[run] scale, so that pair is close to the condition §12 calls a hard
failure even though the check as written passes.

#### R9-12 — LOW — G7 and G6 still carry hardcoded sub-clauses

**Fails:** `design.md:1040-1045` (§11 G7: *"separately confirms (a) the trail ratcheted on M1 CLOSES
only … and (b) a time-exit episode fills at the OPEN of the first decision-clock bar"*).
**Code:** `golden.py:248-249`, `golden.py:221`.

`trail_ratchets_on_m1_closes_only: True` and `time_exit_fills_at_decision_bar_open: True` are
literals, as is G6's `legal_variant_is_the_emitted_one: True`. The **primary** clause of each trace is
now genuinely computed, which is why this is LOW and not a repeat of R8-12. The implementations are in
fact correct (`fills.py:249-257` ratchets on `c[i]` after the trigger test; `resolve_time_exit:136-143`
fills at `clock_open[i]` where `slot_start[i] >= deadline`) — they are just not asserted.

#### R9-13 — LOW — the entry M1 bar is excluded from exit scanning but included in κ's MFE

**Code:** `fills.py:184` (`start = max(fill_m1_idx + 1, …)`) vs `fills.py:284`
(`m1["high"][fill_m1_idx:end_i]`).

AMENDMENT-19b declares the entry bar unscanned for exits; the MFE that forms κ's denominator still
begins at the entry bar. κ is `DISCLOSURE_ONLY` and multiplies nothing (§5), so this is a consistency
note, not a validity defect.

#### R9-14 — LOW — the side derangement emits the permutation fixed-point count, not the alignment L-28 is about

**Code:** `controls.py:110-112, 119`.

`fixed_point_count` is 0 by construction of `derange_indices`, so it is uninformative. The quantity
that determines how much of the true side survives a seed is `mean(side[perm] != side)` — computed at
`:111` and never reported. With roughly balanced sides about half the episodes retain their own side
on every seed. Under AMENDMENT-19(a) that fraction **is** the control's destruction strength, and it
is the direct analogue of VAL-008's 11.1% alignment that L-28 was written after.

**Required fix.** Emit the per-seed flipped fraction (mean, sd, min, max) alongside the fixed-point
count.

#### R9-15 — LOW — dead code inside the hashed tree

**Code:** `indicators.py:87-104` (`expanding_rank`) — defined, never called (grep: 1 hit, the `def`).
`selfcheck._sha256_tree:45-50` hashes every `.py`, so it is part of the run's pinned code identity.
Same shape as the now-closed R8-26, one function instead of a hundred lines.

#### R9-16 — LOW — the L2 interaction rows carry no §9 band label

**Fails:** `design.md:1387` (§15 `metrics_by_cell` must carry *"band label (CI-relative)"*).
**Code:** `run_screen.py:444-463`.

The 48 interaction rows carry `log_R`, `ci_low`, `ci_high`, `ci_width`, `block_mde` and pass the
`log R never unaccompanied` check, but no `mirror_band`. **CONFIRMED:** of 156 null `mirror_band`
values, 108 are the deliberately suppressed sizing rows and 48 are the interaction rows.

#### R9-17 — LOW — two stale statements in `design.md`

`design.md:1092` (§12 determinism) still says *"independent of `--resume`"*; the flag was removed per
R8-27 (grep: 0 hits). `design.md:1335-1336` says *"AMENDMENTS 12-18 are seven consecutive TIGHTER
rows"*, but 12 and 14 are labelled `NEUTRAL` in the same ledger — the L-23 streak is five tighter
rows within that span, not seven. Neither affects a check. (The ledger's arithmetic itself is
correct: I recounted 4 looser / 9 tighter / 6 neutral across all rows and 3 / 8 / 6 active after the
two supersessions, matching `design.md:1332-1334`.)

---

### PART C — the adversarial pass: can each HARD check fail?

Method: for each check I constructed or reasoned a case that ought to fail it. Rows marked
**CONFIRMED** were executed against the smoke's own `episodes.parquet` (617,197 rows) or against
fabricated metrics rows.

| # | HARD check | Can it fail? | Evidence / construction |
|---|---|---|---|
| 1 | check-count reconciliation | **YES** | `selfcheck.py:353-364`: fails if the final list is not 28 names or any name carries `missing: True`. Names are asserted at import (`config.py:282`) |
| 2 | TRIPWIRE-1 | **PARTLY** | Fails if `changed_state_rows == 0` or `changed_selection_episodes == 0` (real quantities, 45,117 / 122). Also fails if any gate array is all-NaN (`both.any()` false). But `shift_is_exact_one_row` is true by construction — the leaky stream *is* the shifted legal stream — and the episode limb is blind to L1 and all L4 arms → **R9-01** |
| 3 | TRIPWIRE-2 | **PARTLY** | Clause 1 (`clock_vs_m1 > 0`, emitted 851) and clause 2 (`both_reachable > 0`, emitted 4) are real, though clause 2's symbol is selected for passing (**R9-10**). Clauses 3 and 4 are tautologies → **R9-02** |
| 4 | TRAIN fence | **YES — CONFIRMED** | Requires `n_episodes > 0 and max_ts > 0` then `max_ts < TRAIN_END_NS`. Empty frame → `have_ts` False → fails. Emitted `max exit_ts 2023-12-17 23:52 UTC` < `2023-12-18` |
| 5 | holdout | **YES** | Same guard, `< 2025-01-08` |
| 6 | causality | **YES — CONFIRMED** | One row with `fill_ts ≤ decision_end_ns` → `False`. Empty frame → `False`. Missing columns → `False` |
| 7 | fill causality | **YES — CONFIRMED** | Same injection → `False`; also fails on `exit_ts < fill_ts` |
| 8 | universe pin | **YES** | `len(symbols) == 25` on the family pin file |
| 9 | identity reconstruction | **YES** | Requires `n_checked > 0` and zero residuals above 0.01 bps. Empty → `False`. (Residual is zero by construction of `_agg`, so it will not fail on correct code — the check guards against a future change to `p`, `W`, `L`) |
| 10 | log R definition | **YES** | Recomputes `log(W/L) − log((1−p)/p)` per row and requires `n > 0`. A fitted-slope column would also trip G5 |
| 11 | cost isolation | **WEAKLY** | `selfcheck.py:201-214` bans exactly three literal column names (`mean_net`, `edge_net`, `log_r_net`) and requires `p_be_net` present. A cost column under any other name passes. Not new this run; noted, not raised as a finding |
| 12 | derangement fixed-point count | **YES** | Requires at least one control reporting `fixed_point_count_measured` and `max == 0`; absent controls → `False` (R8-16 fix). See **R9-14** for what it does *not* measure |
| 13 | golden traces | **YES** | All seven statuses must be `FOUND`/`PASS`; G5 and G6 are real; G7 is `MISSING` if TRIPWIRE-2 found no both-reachable row |
| 14 | determinism | **YES — CONFIRMED** | At `--jobs > 1` requires `determinism_ok is True`; `None` (comparison did not run) fails. My smoke ran it. At `--jobs 1` it is marked True as "identity trivial" — vacuous but explicitly scoped by §12 to `--jobs > 1` |
| 15 | BLOCK RULE | **YES — CONFIRMED** | Fails on: holds > 24 h; a cell with 5 per-seed CIs instead of 15; an empty metrics list; a non-`block` `mde_source_for_bands`; an unlabelled iid column; a `source_ci_rule` missing a clause keyword. **Weakness: the degenerate exemption → R9-04** |
| 16 | L4 COMPARATOR IDENTITY | **PARTLY — CONFIRMED** | ATR-proportional width → `False`; no L4 episodes → `False`. The ŝ half is computed and unused → **R9-09** |
| 17 | PARENT-GATE PROVENANCE | **NO** | `check_parent_provenance(ep, {"rows":[{"junk":1}]})` → `True`. Fails only on an empty row list → **R9-03** |
| 18 | PARENT-GATE PARITY | **YES** | `n_ok == 2 × n_non_exempt` and zero failures and `n_non_exempt > 0`; `NO_PARENT_ROW` / `PARENT_NAN` / `NO_REGIME_ROWS` / missing cell all count as failures; a raised computation is recorded `hard_pass: False` |
| 19 | DECILE CAUSALITY | **PARTLY — CONFIRMED** | Pooled full-TRAIN edge → `False`; empty or missing columns → `False`. Pooled-expanding edge would pass → **R9-08** |
| 20 | EXIT-MATCHED NULLS | **YES — CONFIRMED** | Setting a target arm's `r_bps_side_flipped = −r_bps` → `False`. Also fails if a time-exit arm's negation is inexact, or if an arm carries the wrong `exit_matched_method`. Per-arm, not aggregate |
| 21 | L1 FIXED-ENTRY SUBSET | **YES — CONFIRMED** | Altering one L1 episode's stop price → `False`. Empty L0 or empty L1 → `False` |
| 22 | MOD-HOLD ELIGIBILITY | **YES — CONFIRMED** | Setting `L4_HOLD_4H_MOD` holds to a constant → `False`; empty frame → `False`. Predicate differs from §12's → **R9-11** |
| 23 | PREDECLARATION PRESENT | **YES** | Two sha256 comparisons against `config.py` pins, `row_count == 5148`, `input_sha256.basis` match, and a `"COMPUTED AT RUN"` substring scan. `verify_predeclaration()` also asserts before any data is read |
| 24 | BASIS POPULATION | **YES** | `input_filter.value == "C"` and `matched − retained == excluded == Σ excluded_by_reason` |
| 25 | UNIVERSE FILE EQUALITY | **YES** | Set equality between the family pin and SPDR-014's `universe_recomputed.json` |
| 26 | L-51 SELECTION CHECK | **PRESENCE ONLY** | `n_checks > 0`. §12 makes it HARD on presence, so this is per spec — but it cannot notice the missing subsets → **R9-07** |
| 27 | log R never unaccompanied | **YES — CONFIRMED** | Requires the five columns present and non-null on every row carrying a finite `log_R`, and `len > 0`. I re-derived it independently on the emitted frame: 1,649 rows with `log_R`, zero missing companions |
| 28 | PREDECLARED vs REALISED resolution | **PRESENCE ONLY** | Column presence in `metrics_by_cell` or `resolution_ladder`. Per §12, which makes the last four HARD on presence and form only |

**Summary: 20 of 28 can fail on substance and were shown to (12 by execution). 4 are partial
(TRIPWIRE-1, TRIPWIRE-2, L4 comparator, decile causality). 2 are presence-only by design (L-51,
predeclared-vs-realised). 1 is weak but not new (cost isolation). 1 cannot fail: PARENT-GATE
PROVENANCE.** Run 8's count was eleven that could not fail.

**On the degenerate exemption specifically (the brief's question).** It is sound in intent — a cell
too thin to bootstrap emits no per-seed bounds, and requiring 15 of them would fail a correct screen.
It is **not sound in form**: it is uncapped (one compliant cell carries the clause), unvalidated (no
assertion that an exempted cell is actually thin), truncated in the artifact (first 50), and it has a
silent third class that swallowed all 108 sizing rows. It *can* widen silently. See R9-04.

---

### PART D — integrity boundary, re-verified

| Boundary rule | Result |
|---|---|
| **TRAIN-only** | **CLEAN — CONFIRMED.** `catalog_io` raises before any read on `end > TRAIN_END_NS` or `> HOLDOUT_START_NS`. On the emission: `max signal_ts = max decision_end_ns = 2023-12-17 23:15 UTC`, `max fill_ts = 23:17`, `max exit_ts = 23:52` — all inside `2023-12-18T00:00Z`. `TEST_START` and `HOLDOUT_START` are defined and never read |
| **Causal `t−1`** | **CLEAN — CONFIRMED.** `signal_ts == decision_end_ns` on **all** 617,197 episodes; `fill_ts > decision_end_ns` on all; `exit_ts >= fill_ts` on all. `_first_m1_after` uses `side="right"`. Parent labels held forward with `src_end <= dst_end` and an ascending-order guard that raises. Deciles rank against history strictly before `[0]` |
| **Block ≥ H** | **CLEAN — CONFIRMED.** Blocks are `{1,3,7}` **calendar** days; emitted `min_block_hours 24 ≥ max_active_hold_hours 20.0`. Effective block `< n_days` verified on 5,127 block records. The fast path is bit-equivalent to `xen.evaluation.block_bootstrap_ci`. The Δ`log R` read now uses the same rule (R8-10) |
| **No money read** | **CLEAN — CONFIRMED.** Cost-touching columns in `metrics_by_cell`: `cost_bps_DISCLOSURE_ONLY`, `p_be_net`, `p_be_net_flag`, `spread_cost_status` — nothing else. `spread_cost_status` is `UNAVAILABLE_NOT_CHARGED` on every row; `spread_rt_bps: null`. No net figure enters an estimand, threshold, band or comparison. AMENDMENT-C5 satisfied; the lane-wide spread blocker is respected |
| **No holdout / TEST / XENA** | **CLEAN — CONFIRMED.** No `xena` import, no TEST band, no registry write anywhere in the tree |
| **No family action** | **CLEAN.** No disposition, no registry file touched, `main()` returns an exit code and nothing else |
| **No local accounting** | **CLEAN — CONFIRMED by execution.** `check_no_local_accounting` → `{"ok": true, "banned_defs_found": []}` |
| **No adequacy flag (C7)** | **CLEAN — CONFIRMED.** No column in the emitted frame matches `powered\|unpowered\|at_target\|not_resolvable` |
| **Per-stratum / multiplicity disclosed** | **CLEAN.** 1,758 rows across 33 variants × clocks × δ × 3 bands × (POOLED + symbols); pooled rows carry `i_squared`, `homogeneity_q/df/k_symbols`, `per_symbol_spread_log_R` and a `pooled_status` the operator judges; nothing machine-dropped |
| **Predeclaration untouched** | **CLEAN — CONFIRMED.** Three files, hashes `23d5f5bf…`, `e3247798…`, `961cec28…` before and after my smoke |

---

### PART E — verdict on AMENDMENT-19

**Overall: all three clauses are legitimate specification fixes, not scope changes. The `NEUTRAL`
direction label is defensible for (b) and (c); for (a) it is defensible only with a disclosure the
design does not currently carry.**

**19(a) — zero fixed points on the PERMUTATION, not on the side VALUE. LEGITIMATE.** This is the
clause the brief asks me to scrutinise hardest, and it survives.

1. **The literal reading is arithmetically self-contradicting, and run 8 measured it.** A binary side
   with every value differing from its own is a full flip — one arrangement, identical on every seed.
   Run 8's own execution produced `null_sd = 1.39e-17`, `null_q05 == null_q95`, `percentile = 1.0`.
   The **same §6 clause** demands `>= 2000 seeds` and *"the null's own mean, sd and quantiles"*. Both
   cannot hold. One of them had to be re-read.
2. **The programme's own L-28 defines the derangement on the permutation, not on the value.** I read
   `lessons-and-amendments.md` L-28 in full: it is stated entirely in terms of permutation fixed
   points — *"a uniform random permutation of n items has E[fixed points] = 1 for any n"*, *"those
   fixed points keep the original timing/signal at those indices"*. AMENDMENT-19(a) applies L-28 as
   L-28 is written. This is the decisive point: it is not a new reading invented to make a control
   pass.
3. **The cited comparator was measured under this reading.** SPDR-013's 0.20–0.28 / 0.48–0.57
   percentiles are values only a spread null can produce. Under the literal reading the design would
   be comparing against a number its own control could never emit.
4. **The control still bites.** In my smoke the L0 null sits at mean ≈ 0 (collapse −0.0085 against
   live `log R` 0.183) with sd 0.073, and the live value reads percentile 1.0. This is a control that
   discriminates, not one loosened until it stopped objecting.

**What is genuinely lost, and what the design should say.** Under a random derangement of a balanced
binary label, roughly **half the episodes retain their own side on every seed**. Against a full flip
that is a real reduction in destruction strength, and it is exactly the quantity VAL-008 measured as
"11.1% alignment". The design acknowledges the mechanism in prose (*"the mix of flipped and unflipped
episodes is what varies across seeds and is what gives the null its spread"*) but requires only the
**fixed-point count** to be measured — which is 0 by construction and therefore says nothing. The
amendment should additionally require the **flipped fraction per seed** to be emitted (→ R9-14). With
that disclosure, `NEUTRAL` is right. Without it, the ledger records a control as unchanged when its
destruction strength halved and the emission carries no number that shows it.

**19(b) — the entry bar is not scanned for an exit. LEGITIMATE, and correctly labelled NEUTRAL.** §2's
exit table genuinely did not say. The stated reasoning — intrabar ordering is unknowable at M1
resolution, the same premise as the adverse-precedence rule — is the design's existing principle
applied consistently, and it removes both favourable and adverse intrabar paths, so it does not bias
in the design's favour. Implemented at `fills.py:184`. One consistency residue: κ's MFE still includes
the entry bar (R9-13), which the amendment does not address.

**19(c) — the both-reachable population is constructed. LEGITIMATE AS A SPECIFICATION; NOT
DISCHARGED BY THE CODE.** The premise is correct and checkable: none of the 33 variants places both a
target and a trail, so §6.1's TRIPWIRE-2(b) and §11's G7 had no population to observe. Pairing each
target episode with the trail its own ŝ device would set at `b = 1` is deterministic, re-derivable by
QA from the catalog, and enters no emitted arm — all as the amendment claims. **But** the amendment
does not notice what its own construction does to §6.1's clause 3: a symmetric constructed twin makes
`count_favourable == count_both` and "favourable never worse" true by geometry, so the clause the
design calls *"what proves the adverse rule is actually implemented"* proves nothing. That is a code
finding (R9-02), and the fix is available without changing the amendment — resolve the constructed
pair through `resolve_target_trail_time` under both precedence settings.

**Direction-ledger note (L-23).** AMENDMENT-19 is booked `NEUTRAL`, giving 4 looser / 9 tighter /
6 neutral across all rows and 3 / 8 / 6 active — I recounted both and they reconcile. The L-23
tighter-streak note (`design.md:1335`) miscounts its own span (R9-17). The standing L-23 flags for the
operator at the execution gate are unchanged: 3 active loosenings (AMENDMENT-1 full TRAIN,
AMENDMENT-2 M15, AMENDMENT-10 hold grid), none touching an integrity check, fence, causality rule or
claim boundary.

---

### Checks independently verified clean

| Check | Result |
|---|---|
| Entry rule, fill rule, stop price | **CLEAN — READ + smoke.** `entry.detect_signals:57-67` implements §2 verbatim; `fills.resolve_entry_stop:46-83` fills at the stop, at the open on a gap, expires otherwise. Run 8 confirmed G1 numerically against the catalog and the code is unchanged there |
| Identity `\|p·W − (1−p)·L − mean\| < 0.01` | **CLEAN — hand-derived + CONFIRMED.** Zero by construction of `_agg`; smoke `identity reconstruction` held over every scored cell |
| `log R` slope 1, no fitted-slope object | **CLEAN — CONFIRMED.** G5 scanned 84 emitted columns and all screen source for six tokens; 0 offending |
| Bootstrap == `xen.evaluation.block_bootstrap_ci` | **CLEAN — CONFIRMED** in the smoke's own block-rule clause 5 |
| 33 named variants, 28 HARD names | **CLEAN — CONFIRMED.** Both asserted at import; 33 variants present in the emitted frame; 28 checks in `integrity_selfcheck.json` |
| Unit pin, ATR barred from L4 | **CLEAN — CONFIRMED.** `atr_matches: 0` across all ten L4 barrier arms; ATR reaches only `entry.py:57`; medians computed at run into `unit_pin.json` |
| Suppression / unfilled / ineligible accounting | **CLEAN — CONFIRMED.** 617,197 / 307,222 / 183,143 / 152,754 / 287, with ineligibility reasons broken out by gate (`L1_DECILE 64,157`, `HMM_LOW 20,742`, `RMARKOV_K4_NA 5,028`, …). Nothing dropped |
| Span disclosure (M-2), M-4 effective coverage | **CLEAN — CONFIRMED.** `span_exact_frac`, `span_p50`, `span_p90`, `effective_frac_of_nominal`, `n_symbols_in_cell` all present |
| `_strip_internal` | **CLEAN — CONFIRMED.** I recursively scanned the written `controls.json` for `_`-prefixed keys and for oversized raw lists: **zero hits**. `_null_draws` is consumed by `plant_curve` before the strip and never reaches disk. The unstripped payload is also passed to `selfcheck`, which reads only `fixed_point_count*` from it and embeds nothing — so no draw array reaches `integrity_selfcheck.json` either |
| Sizing suppression side effects | **CLEAN except one.** Sizing rows keep `n_episodes`, `n`, `fill_rate`, dispersion stats, and all 108 appear in `resolution_ladder.parquet`; `_attach_homogeneity` skips them without corrupting any pooled figure; `_layer_deltas` excludes them per §4.2. The one silent drop is the block-rule clause-4 population (R9-04) |
| Spawn safety under `mp.Pool` | **CLEAN — CONFIRMED.** Ran two spawn workers with the new path-based parent import; no `sys.path` mutation, no module deletion, determinism bit-identical |

---

### Golden-trace verdict

| Trace | Design expectation | Implementation | Verdict |
|---|---|---|---|
| **G1** entry + fill | first BTCUSDT H1 DESIGN LONG at δ=0.5, with OHLCs, ATR20, momentum, stop, fill | `golden.py:30-80`, unchanged since run 8, which verified it numerically against the catalog. Emitted `FOUND` in my smoke | **PASS** |
| **G2** expiry path | first ETHUSDT H1 DESIGN SHORT unfilled in 2 h, entering the fill-rate denominator only | `golden.py:84-100` selects it; the fill-rate denominator it feeds is now **real** (97.3% of cells carry a finite `fill_rate`), closing run 8's PARTIAL | **PASS** |
| **G3** suppression | first signal arriving while an episode is open → SUPPRESSED, counted, no second episode | `golden.py:103-126`; suppression is now decided in **fill** order (R8-17), so the row it finds is the design's row. 307,222 suppressed signals counted | **PASS** |
| **G4** identity + primary read | recompute `p, W, L`, residual < 0.01 bps, recompute `log R` | `golden.py:129-156`, keying on the reporting `band == "CONFIRM"` — no longer fragile now that the CI-relative label owns `mirror_band` | **PASS** |
| **G5** mirror null is the exact one | null reference 0 at slope 1; **no fitted-slope residual anywhere** | Real scan of 84 emitted columns **and** every screen source file for six tokens; `offending_columns: []`, `offending_source: []`. Was a literal in run 8 | **PASS — CONFIRMED** |
| **G6** leak discrimination | §6.1's three structural conditions on the G1 rows | Reads the real TRIPWIRE-1 payload: `exact True`, `changed_state_rows 45,117`, `changed_selection_episodes 122`. Inherits R9-01's coverage gap; `legal_variant_is_the_emitted_one` is a literal | **PASS, with R9-01 attached** |
| **G7** exit fill precedence | first both-reachable target+trail bar: which fills under adverse precedence, at what price, `r`; **plus** trail ratchets on M1 closes only; **plus** time exit at the decision-bar open | Reads the real TRIPWIRE-2 payload and emits a real episode (`m1_ts 1658337060…`, SHORT, adverse 23601.328 / favourable 23493.672, `r` −22.859 / +22.859). But the fill it reports was **computed arithmetically, not returned by `resolve_target_trail_time`** (R9-02), and the two supplementary clauses are literals (R9-12) | **PARTIAL** |

**Verdict: 6 PASS (2 newly confirmed by execution), 1 PARTIAL.** Run 8 had 1 PASS confirmed, 1 PASS
fragile, 2 PARTIAL, 3 FAIL.

---

### Standing execution blockers

1. **DISCHARGED** (re-verified, not re-flagged) — AMENDMENT-7 / registered-C6 departure.
2. **DISCHARGED** (re-verified) — `reflection-inputs.md` §9, signed option B at `9d8832e`.
3. **STANDS (lane-wide, unchanged)** — the per-symbol spread pin. It does not block this measurement
   under AMENDMENT-C5, and the code makes no money read (verified above).
4. **NEW — BLOCKING** — **R9-01, R9-02, R9-03.** Three HARD checks (TRIPWIRE-1, TRIPWIRE-2,
   PARENT-GATE PROVENANCE) cannot fail on what §12 says they verify. Under P-23/L-52 a check that
   cannot fail is indistinguishable from one that was skipped. None of them corrupts a number in the
   emission, which is why the verdict is REVISE, but a run in this state would again write
   `all_hard_pass: true` over three unverified clauses.
5. **NEW — should clear before execution** — **R9-04 … R9-10** (seven MEDIUM). Each either widens an
   exemption silently, leaves a design-mandated parameter unasserted, emits a control curve that
   carries no resolution, or covers less than the design names.
6. **Run-8 blockers 4, 5 and 6 are DISCHARGED** — all 29 findings closed, `check_no_local_accounting`
   green.

---

**FAILING_ARTIFACT:** `python/experiments/SPDR-019/screen_code/` — specifically `tripwires.py`
(R9-01, R9-02), `integrity.py` (R9-03, R9-04, R9-08, R9-09, R9-11), `run_screen.py` (R9-05, R9-07,
R9-10, R9-16), `controls.py` (R9-06, R9-14), `golden.py` (R9-12), `fills.py` (R9-13),
`indicators.py` (R9-15). `design.md` carries only R9-17 (two stale sentences, no check affected).

**REQUIRED_SKILL:** `experiment-developer` for R9-01 … R9-16. `quant-designer` jointly for R9-14 (the
AMENDMENT-19(a) disclosure clause — the flipped-fraction emission belongs in §6, not only in code).

**Execution authorisation: NO.**

Not because the screen is wrong — it is now, on everything I could execute, right. Because three of
the twenty-eight HARD checks still cannot fail on their own subject, and the design's own P-23 rule
does not admit a check that cannot fail. The three fixes are small and local: shift the ŝ fields into
the leaky Signal stream and add the L4 arms to the tripwire's variant list; route the constructed
both-reachable pair through `resolve_target_trail_time` under both precedence settings; and make
`check_parent_provenance` assert the columns and the forbidden names instead of returning a literal.
A re-read of that diff plus a re-run of the smoke would be enough — unlike run 8, these corrections
change what is *checked*, not what is *computed*, so the estimand does not move and a full re-QA of
the measurement path is not required.

---

### What I did not reach

- **I did not run the full 25-symbol screen.** Operator-gated and unauthorised. Everything above
  comes from the sanctioned 2-symbol smoke at `n_boot = 200`, from isolated function calls, or from
  hand derivation. At `n_boot = 2000` the control battery, the ladder and the paired bootstrap all
  scale up; I verified their *behaviour*, not their full-scale cost.
- **Every real-data claim rests on BTCUSDT and ETHUSDT.** The 23 other symbols are unexercised. In
  particular `PARENT-GATE PARITY` passed at `n_ok 4/4` — the 8 PARITY-EXEMPT symbols and the 15
  remaining non-exempt symbols were never in the run, so the exempt-list mechanism itself is
  untested against real parent NaNs this round (run 7 tested the regeneration).
- **I did not verify the M15 clock beyond the fact that it ran.** Both clocks were in the smoke and
  the cell grid contains M15 rows, but I checked no M15 fill, no M15 hold conversion and no M15
  block behaviour individually. M15 carries the primary read.
- **I did not test TRIPWIRE-1's ability to detect a real leak.** I showed it re-selects episodes and
  that its L1/L4 limbs are blind; I did not construct a genuinely non-causal pipeline and confirm the
  tripwire's payoff delta moves in the expected direction. §6.1 makes that direction reported, never
  a pass condition, so this is a coverage gap in my review, not in the check.
- **I did not audit `xen.evaluation.block_bootstrap_ci` or `xen.resolution_basis` internals**, only
  that the screen's fast path reproduces the former and that the predeclaration hashes match.
- **I did not re-derive the parent gates end to end.** `walk_forward_probs`, the feature matrix and
  the parity arithmetic were read, not independently recomputed; run 7 executed that path.
- **I did not quantify the effect of any finding on any result.** There is no authorised run, and
  that is the data-analyst's object in any case.
- **I did not review `python/experiments/SPDR-020/screen_code/`.** It shares `resolution_basis.py`
  and the resolution artifacts and was actively changing in the same working tree during this review
  (two commits and an untracked `results/shards/` appeared while I worked). Several shapes here —
  the degenerate-exemption pattern, the plant-curve base, the tripwire twin construction — are the
  kind a sibling implementation repeats. **That directory needs its own QA run; do not infer its
  state from this one.**

---

## QA run 10 — 2026-07-29T22:21:14Z — mode: subagent — HEAD 1979b93 (SPDR-019 unchanged since `bb92447`)

**Reviewed git state:** `HEAD 1979b93648c41fad74458b86a3bb96bff2244012`.
`git diff bb92447 HEAD -- python/experiments/SPDR-019/` is **empty** — the one commit on top
(`1979b93`) is SPDR-020 only. `git status -- python/experiments/SPDR-019/` shows only the seven
untracked `results/*.json` smoke artifacts. `git diff HEAD -- screen_code/ design.md` is empty at
the end of this review: every fault injection below was an **in-memory monkeypatch**, no file in
the experiment tree was edited, and the pre-existing smoke artifacts were copied to scratch before
I re-ran the smoke over them.
**Stage:** IMPLEMENTATION QA, narrow re-review of one remediation commit.
**Scope (as authorised):** verify closure of the 17 run-9 findings **R9-01 … R9-17** against
commit `bb92447`; confirm nothing in that diff moved a computed estimand, threshold or comparison;
re-run the sanctioned 2-symbol smoke. Run 9 pre-declared this scoping and its reason: the
corrections change what is *checked*, not what is *computed*. I honoured it — no run-8 finding is
re-litigated and the measurement path is re-audited only where the diff touched it (`fills.mfe_bps`
only, see R9-13).
**Independence:** fresh subagent context. I authored none of the design, none of the
implementation, and none of the earlier QA runs. Read in full: `git show bb92447` (683 insertions /
143 deletions across 11 files), run 9 in full, the current `tripwires.py`, `integrity.py`,
`controls.py`, `golden.py`, `selfcheck.py`, `selection.py`, `config.py`, the changed hunks of
`run_screen.py` and `fills.py`, and `design.md` §6/§6.1/§9/§11/§12/§15 plus the AMENDMENT ledger.

**Verdict: APPROVE.**

**Execution authorisation: YES.**

All 17 run-9 findings are closed. **The three HIGH ones are closed by execution, not by reading:**
I reverted each fix in memory and watched the HARD check flip to `False` on its own subject.
`check_parent_provenance` now rejects the exact garbage payload run 9 used to break it. Nothing in
the diff moved a number: `episodes.parquet` is bit-identical in size and content to run 9's
(617,197 rows), `metrics_by_cell.parquet` is 1,758 rows as before, `metrics.py`, `engine.py`,
`entry.py`, `panel.py`, `parent_gates.py` and `catalog_io.py` are untouched by the commit, and the
three predeclaration hashes are unchanged. My independent smoke reproduces `all_hard_pass: true`
with `hard_fail_names: []` at 28/28.

Six residual observations are recorded below as **R10-01 … R10-06**. None is a blocker: five are
disclosure or check-strength notes on already-closed findings, and one (**R10-01**) is a ledger-
hygiene gap in `design.md` that changes no number, gate, band or population. They are listed so the
operator and the data-analyst can see them, not to withhold authorisation.

---

### PART A — run-9 close-out

| Finding | Status | Evidence I produced |
|---|---|---|
| **R9-01** — HIGH — TRIPWIRE-1 never reaches L1 or any L4 arm | **CLOSED — CONFIRMED by fault injection (both limbs)** | `tripwires._rebind_signal_shat:94-124` re-freezes `s_hat_bps` / `s_hat_decile` / `s_hat_rank` from each panel onto its own Signal stream (`:159-160`), and `tripwire_1:134-136` now shifts those three ŝ source arrays as well; `LAYER_VARIANTS:42-47` adds the four `L4_HOLD_*H_MOD` ids and L4 goes through `engine._build_variant` (`:168-174`) rather than `select_layer_from_l0`, so a shifted `p_stay` can move `exit_ts`. **Clean run on BTCUSDT H1 δ=0.5:** 15 variants compared, `changed_selection_episodes` 372 (was 122), L1 d≥5/7/9 symmetric differences **25 / 21 / 16** (were 0/0/0), L4 4H/12H/20H **38 / 71 / 79** (were absent). **Injection A** — `_rebind_signal_shat` replaced by the identity, i.e. exactly the pre-fix state: L1 differences collapse to **0 / 0 / 0**, `per_variant_required_nonzero_held` **False**, `hard_pass` **False**. **Injection B** — `engine._build_variant` forced onto the legal panel for L4 ids only: L4 differences **0 / 0 / 0**, `hard_pass` **False**. The pooled-sum blindfold is gone: `per_variant_ok` (`:201-205`) requires a non-zero difference from *every* threshold variant whose own gate array the shift actually changed. |
| **R9-02** — HIGH — TRIPWIRE-2's favourable twin never calls the exit resolver | **CLOSED — CONFIRMED by fault injection (clauses 3 and 4 separately)** | `tripwire_2:316-331` now makes **two** real calls to `resolve_target_trail_time` on the same target+trail pair, `favourable_precedence=False` and `True`, both anchored identically at `hit-1` so the both-reachable bar is the first bar scanned; every price, reason and `r` in the payload comes from the returned `ExitFill` (`:334-355`). Clean: all four both-reachable bars resolve **adverse → `TRAIL`, favourable → `TARGET`** — the branch is alive. **Injection C** — the resolver wrapped to force `favourable_precedence=False` (the pre-fix dead branch): `count_favourable_diff` **0** against `count_both_reachable` **4**, `hard_pass` **False**. Clause 3 therefore measures something. **Injection D** — precedence inverted so the favourable twin is *worse*: `favourable_price_never_worse` **False**, `hard_pass` **False**. Clause 4 therefore measures something. The G7 row changed accordingly — adverse 23606.5 / `TRAIL`, favourable 23493.672 / `TARGET`, `r` −25.056 / +22.859 — no longer the exact-negative signature run 9 flagged as the tautology's fingerprint. The arm's own exit is disclosed separately as `arm_exit_price` / `arm_exit_reason` (see **R10-02** for the residual naming point). |
| **R9-03** — HIGH — PARENT-GATE PROVENANCE passes on garbage | **CLOSED — CONFIRMED by execution on five payloads** | `integrity.check_parent_provenance:179-253` now (a) requires real gate structure per row, (b) asserts the pinned model/field tokens are present in `parent_gates.py` (`_PINNED_GATE_TOKENS`, `:165-171`), (c) asserts `attach_gates` calls `_hold_forward` and that the no-backfill rule text is present, and (d) scans both the panel-bound arrays and every episode column for the forbidden outcome labels `y`, `mag_k1`, `next_abs_oo`, `run_len_` (`:172`). **Executed against the smoke's 617,197-row `episodes.parquet`:** real payload → `True`; run 9's exact breaker `{"rows":[{"junk":1}]}` → **False** ("parent parity rows carry no gate structure"); a `y` column added to episodes → **False**; a `mag_k1_realised` column added → **False**; `{"rows":[]}` → **False**. The §12 clause that names `y` and the swing magnitude a hard failure is now the clause the code enforces. |
| **R9-04** — MEDIUM — block-rule exemption uncapped, unvalidated, sizing rows silently dropped | **CLOSED — CONFIRMED by execution** | `integrity.check_block_rule:491-565` splits every row with a `per_seed_ci` into four named buckets and requires each degenerate cell to carry a validated thinness reason; `unclassified` is fatal. **Reconciliation is now exact:** 1,649 with a CI + 1 degenerate + 108 suppressed-`log R` + 0 unclassified = **1,758 = every metric row**. The 108 sizing rows are the named third bucket, each with `per_seed_ci_len 15` and `reason SIZING_VARIANT_MAY_NOT_CARRY_A_LOG_R_CLAIM`; the single degenerate cell carries `reason "n_dates < 7 (min day-block in {1,3,7} sweep)"`; `degenerate_cells` is emitted in full, no 50-row truncation. **Fails on:** a degenerate cell with 500 dates and an empty battery → `held False`, `unclassified 1`; a non-sizing row with a 3-entry battery and null `ci_low` → `held False`; a sizing row with a 7-entry battery → `held False`; a degenerate cell with non-numeric `n_dates` → `held False`; a cell with 5 per-seed CIs → `held False`, `min_observed 5`. See **R10-03** for what the fix does *not* do. |
| **R9-05** — MEDIUM — control battery coupled to `--n-boot` | **CLOSED — CONFIRMED by execution** | `config.py:225-228` pins `CONTROL_N_SEEDS = 2000` with three `assert len(...) >= CONTROL_N_SEEDS` guards; `run_screen.py:850` reads it instead of `min(2000, max(50, n_boot))`; `_run_controls:624` passes `n_ctrl` to the magnitude-matched comparator too (was `min(n_ctrl, 500)`). My smoke at `--n-boot 200` emitted `n_ctrl_seeds_pinned 2000` and `n_seeds 2000` on **all eleven** side-derangement arms, on `entry_timing` and on `magnitude_matched`. `selfcheck.py:224-241` now makes the seed count part of the HARD verdict: emulating the predicate, `n_seeds 200` → **False**, `fixed_point_count 3` → **False**, the real payload → **True**. |
| **R9-06** — MEDIUM — plant curve saturates, §6's UNUSABLE clause inoperable | **CLOSED in mechanism — residual is a design rung-grid limit, not a code defect** | `controls.plant_curve:282-334` plants onto a **null-equivalent base** — one deterministic exit-matched side-derangement draw (`plant_base: null_equivalent_one_derange_draw`) — not onto the live series. Verified across all eleven arms: the base sits at or near the null median on most arms (e.g. `L4_TARGET_A2_MOD` base −0.0480 vs `null_q50` −0.0419; `A3_MOD` −0.0123 vs −0.0294), and two arms now emit a rate of **0.9995, not 1.0**, which proves the rate is a measured quantity rather than a construction. **The curve is nonetheless still 1.0 at every rung, and I checked why:** on `L0_BASELINE` a 5 bps plant moves `log R` by 0.1869 = **2.43 null sd**, so even a perfectly median base would detect at ≈0.99. The design's finest declared rung is simply coarser than the control's own resolution. Two consequences: no control is UNUSABLE for any effect the design declares, which is the favourable direction; and run 9's stated expectation ("rises from ≈ α at the finest rung") was **analytically unreachable** — a null-equivalent base scored against its own null gives ≈0.5 at zero plant by construction, never α. The mechanism defect is fixed; locating the resolution numerically needs finer rungs, which is `quant-designer`'s object. See **R10-04**. |
| **R9-07** — MEDIUM — L-51 covers 5 of the named subsets, verified only by count | **CLOSED — CONFIRMED by execution** | `run_screen.py:899-1028` builds ten layer subsets across **both clocks** plus the `MDE50_ABOVE_MEDIAN` / `MDE50_BELOW_MEDIAN` split; `selection.py:52-61` emits `required_subsets`. Smoke: `n_checks` **22** (was 5), subsets = the ten layer ids × {H1, M15} + the two mde50 cells, **12 of 12 required tokens covered**. `selfcheck.py:295-307` now scores token coverage, not just presence: run-9's five-subset payload → **False** (covered 5); nine tokens → **False**; the real payload → **True**. See **R10-05** on the floor. |
| **R9-08** — MEDIUM — DECILE CAUSALITY separates only the worst case; `warm_up_ok` a literal | **CLOSED — CONFIRMED by execution on three limbs** | `integrity.check_decile_causality:256-352` adds a per-symbol decile-median fingerprint limb and computes `warm_up_ok` from `decision_idx` against `DECILE_WARMUP_SHAT`. Clean: overlap 45, 1 symbol pair compared, 0 identical fingerprints, `warm_up_ok True`, `n_episodes_below_warmup 0`, `warmup_threshold_decision_idx 250`. **Fails on:** a pooled quantile edge applied identically to both symbols → `False`, overlap collapses to **0**; five episodes forced to `decision_idx 0` → `False`, `warm_up_ok False`, `n_below 5`; the `decision_idx` column removed → `False`. The literal is gone. |
| **R9-09** — MEDIUM — L4 COMPARATOR tests only the ATR half | **CLOSED — CONFIRMED by execution on both halves** | `integrity.check_l4_comparator:72-131` now asserts `arm_ok = (not atr_prop) and shat_prop` for MOD and `(not atr_prop) and (not shat_prop)` for UNMOD, via a new `_is_proportional:146-161` that requires the denominator to actually vary (so two flat series are not read as proportionality) and requires ≥2 finite widths — closing the one-episode-arm hole run 9 noted. Clean: all ten arms `ok True` with the correct pattern (five MOD `width_over_shat_is_constant True`, five UNMOD `False`, all ten `width_over_atr_is_constant False`). **Fails on:** a MOD arm forced to a constant 1% width → `L4_TARGET_A1_MOD ok False`, `shat_half_held False`; an UNMOD arm forced ŝ-proportional → `L4_TARGET_A1_UNMOD ok False`. |
| **R9-10** — MEDIUM — TRIPWIRE-2 symbol chosen by whether its HARD condition holds | **CLOSED — CONFIRMED** | `config.py:229-230` pre-declares `TRIPWIRE_SYMBOL = "BTCUSDT"` with the comment stating it is never selected by a passing clause; `run_screen.py:959-982` reads the anchor by name, labels any fallback (`anchor_fallback`, `declared_anchor`), and **pools** the structural counts across every symbol that ran a tripwire. Smoke: `symbol BTCUSDT`, `pooled {count_clock_vs_m1 1785, count_both_reachable 12, count_favourable_diff 12, n_symbols_pooled 2, symbols [BTCUSDT, ETHUSDT]}`, and `tw2["hard_pass"]` is **conjoined** with `pooled count_both_reachable > 0` (`:991-993`) — the pooling can only tighten, never rescue. The selection-by-passing loop is deleted. |
| **R9-11** — LOW — MOD-HOLD tests a different predicate from §12 | **CLOSED — CONFIRMED by execution** | `integrity.check_mod_hold:426-489` joins each MOD arm to its UNMOD twin on `(symbol, clock, delta, decision_end_ns, side)` and requires at least one shared episode to differ — §12's predicate, not `ptp > 0`. Clean: h=1 27,036 compared / 26,502 identical; h=4 11,543 / 11; h=12 4,234 / 3; h=20 2,527 / 66; all four `differs_from_unmod True`. **Fails on:** the 4H MOD holds overwritten with their UNMOD twin's value on every shared key → `False`. Run 9's warning about the h=1 arm is now **quantified rather than argued**: 98.0% of its compared episodes carry a hold identical to UNMOD, so that pair is close to §12's hard-failure condition and separates on 534 episodes only. Carried forward as **R10-06**, not as a blocker — §12's predicate is "identical on every episode", and it is not. |
| **R9-12** — LOW — G6/G7 hardcoded sub-clauses | **CLOSED — CONFIRMED by execution** | `golden._assert_trail_ratchets_on_m1_closes:206-219` and `_assert_time_exit_at_decision_bar_open:222-232` compute both G7 sub-clauses from the resolver source, including the ordering constraint (ratchet update must appear *after* the trigger test). Both return `True` on the real source and **`False`** when I swap the resolver for a token-free stub. G6's `legal_variant_is_the_emitted_one` is no longer a literal: `g6_from_tripwire1` returns `FAIL` on an empty `per_variant`, on `changed_state_rows 0`, on `changed_selection_episodes 0` and on `shift_is_exact_one_row False`. The G7 `filled_under_adverse_precedence` field now reads the resolver's own reason (`TRAIL`) instead of the string literal. See **R10-02** for the residual on the G6 field's *name*. |
| **R9-13** — LOW — entry M1 bar excluded from exits but included in κ's MFE | **CLOSED — CONFIRMED** | `fills.mfe_bps:264-299`: `start_i = fill_m1_idx + 1`, with the `end_i <= start_i` guard moved onto the same window. The MFE scan now matches AMENDMENT-19(b)'s exit window. I confirmed the containment claim: κ appears only at `metrics.py:440-445` where it is emitted with `kappa_status "DISCLOSURE_ONLY"`, and `design.md:455` states it multiplies nothing — so this is the **only** estimand-adjacent line in the diff and it touches a disclosure diagnostic, not an estimand. |
| **R9-14** — LOW — derangement emits the permutation fixed-point count, not the alignment | **CLOSED — CONFIRMED, and booked in the design** | `controls.side_derangement:113, 127-131` emits `flipped_fraction_mean/sd/min/max` alongside the fixed-point count. Smoke `L0_BASELINE`: **mean 0.4991, sd 0.0120, min 0.4550, max 0.5411** — the ≈half-retained figure the finding predicted, and the direct analogue of VAL-008's alignment disclosure. Booked in the design too: the CONTROL SIDE-DERANGEMENT block and AMENDMENT-19(a) both now require the emission, which is what run 9 routed jointly to `quant-designer`. (The manner of that design edit is **R10-01**.) |
| **R9-15** — LOW — dead `expanding_rank` in the hashed tree | **CLOSED — CONFIRMED** | `grep -rn expanding_rank screen_code/` → **0 hits** (excluding `__pycache__`). `expanding_decile_edges` remains and is live. |
| **R9-16** — LOW — interaction rows carry no §9 band label | **CLOSED — CONFIRMED** | `run_screen.py:444-463` derives `mirror_band` from the interaction row's own `ci_low`/`ci_high`. Smoke: all **48** interaction rows carry `COVERS_THE_MIRROR`; null `mirror_band` is now **exactly 108 rows**, all of them the deliberately suppressed sizing cells (`L4_SIZE_MOD` 54, `L4_SIZE_UNMOD` 54). The 48 unexplained nulls run 9 counted are gone. |
| **R9-17** — LOW — two stale design statements | **CLOSED — CONFIRMED, and the ledger arithmetic re-derived** | `design.md:1095` now reads "`--resume` is not a flag of this screen"; `design.md:1341-1342` now reads "within AMENDMENTS 12-18 the TIGHTER streak is five rows (12 and 14 are NEUTRAL)". I recounted from the DIRECTION lines rather than trusting either text: amendments in file order 12(NEUTRAL, `:1225`), 14(NEUTRAL, `:1233`), 15(TIGHTER, `:1239`), 16(TIGHTER, `:1244`), 13(TIGHTER, `:1252`), 17(TIGHTER, `:1271`), 18(TIGHTER, `:1290`) — **five consecutive TIGHTER**, correct as amended, and still ≥3 so the L-23 clause-3 flag stands. Whole-ledger recount: 4 LOOSER / 9 TIGHTER / 6 NEUTRAL across 19 rows, and 3 / 8 / 6 active after the two supersessions — both match `design.md:1338-1340` exactly. |

**Close-out count: 17 of 17.** Three closed by injection on the HIGH subject itself, eleven more closed by execution, three (R9-15, R9-16, R9-17) closed by direct inspection of the artifact or the file.

---

### PART B — did the diff move a number?

This is the question run 9's scoping rests on, so I tested it rather than assumed it.

| Surface | Finding |
|---|---|
| **Estimand modules** | `metrics.py`, `engine.py`, `entry.py`, `panel.py`, `parent_gates.py`, `catalog_io.py` appear in **no hunk** of `bb92447` (11 files changed; these are not among them). Episode generation, gate attachment and the `(p, W, L, log R)` computation are byte-identical to the code run 9 reviewed. |
| **`fills.py`** | One hunk, nine lines, entirely inside `mfe_bps`. κ is `DISCLOSURE_ONLY` (`metrics.py:445`) and multiplies nothing (`design.md:455`). No estimand, threshold or comparison reads it. |
| **Episode and cell counts** | 617,197 episodes and 1,758 metric rows in my run — identical to the counts run 9 reported from the pre-fix code, and identical to the developer's post-fix smoke. |
| **Predeclaration** | `resolution_basis.json 23d5f5bf1eb16d00…`, `expected_resolution.json e3247798edc9ab90…`, `expected_resolution_prior.json 961cec28e28f6ff3…` — all three match the values recorded in runs 7, 8 and 9. The files are untouched by the commit and by my run. |
| **Thresholds and comparisons** | The only numeric constants the diff introduces are `CONTROL_N_SEEDS = 2000` (raising a battery size the design already mandated at ≥2000), `TRIPWIRE_SYMBOL = "BTCUSDT"` (an anchor label), and `n_dates < max(BOOT_BLOCKS_DAYS)` as the degenerate-exemption predicate. None enters an estimand, a band, a gate or a §9 comparison. `mirror_band` on interaction rows is **derived** from a `ci_low`/`ci_high` pair that was already computed and emitted. |
| **Reproducibility of my run vs the developer's** | `controls.json`, `selection_check.json`, `parent_gate_parity.json`, `golden_traces.json`, `unit_pin.json` are **byte-identical**. `integrity_selfcheck.json` differs in exactly one place: the order of a five-element column-name list inside the `log R never unaccompanied` detail (Python set iteration order). Same `code_sha256 4fcea2d049c0745d…`. |

**Answer: no.** The diff changes what is checked, what is emitted as disclosure, and what a control's plant curve is scored against. It does not change what is measured.

---

### PART C — the sanctioned smoke, re-run by me

Command, exactly as authorised: `python run_screen.py --smoke --n-boot 200 --jobs 2` (2 symbols,
TRAIN only, phase (a), 33 variants). I copied the seven pre-existing `results/*.json` to scratch
first, so the developer's 20:44 emission is preserved and was diffed against mine.

```
predeclaration OK  basis=23d5f5bf1eb16d00…  expected=e3247798edc9ab90…
symbols=2  jobs=2  n_boot=200
determinism: re-running 1 symbol sequential… determinism OK 830aeed4747f vs 830aeed4747f
episodes=617197  signals=1260603   scoring 1710 cells
done in 3.6 min  hard_pass=True  fails=[]
```

`run_summary.json`: `all_hard_pass true`, `hard_fail_names []`, `n_hard_checks 28`,
`expected_hard_checks 28`, 617,197 episodes, 1,758 metric rows, 33 variants, 214 s.
Every one of the 28 checks reads `held: true`, `severity: HARD`. The determinism check ran
unconditionally at `--jobs 2` and matched the sequential hash.

**I verified the pre-existing 20:44 emission as well** rather than only my own: it carries the same
28/28, the same counts and the same `code_sha256`, and — apart from the one set-ordering artifact
above — the same payloads. The two runs are the same run.

---

### PART D — can the three restored HARD checks fail? (P-23 / L-52)

Every row below is an executed result, not a reading of the source. All patches were in-memory;
`git diff HEAD -- screen_code/` is empty.

| Check | Clean | Injection | Result |
|---|---|---|---|
| **TRIPWIRE-1** L1 limb | `hard_pass True`, L1 d≥5/7/9 = 25/21/16 | `_rebind_signal_shat` → identity (pre-fix state) | L1 = **0/0/0**, `per_variant_required_nonzero_held` **False**, `hard_pass` **False** |
| **TRIPWIRE-1** L4 limb | L4 4H/12H/20H = 38/71/79 | `engine._build_variant` pinned to the legal panel for L4 ids | L4 = **0/0/0**, `hard_pass` **False** |
| **TRIPWIRE-2** clause 3 | `count_both_reachable 4`, `count_favourable_diff 4`, reasons TRAIL vs TARGET on all 4 | resolver forced to `favourable_precedence=False` | `count_favourable_diff` **0**, `hard_pass` **False** |
| **TRIPWIRE-2** clause 4 | `favourable_price_never_worse True` | precedence inverted (favourable twin made worse) | `favourable_price_never_worse` **False**, `hard_pass` **False** |
| **PARENT-GATE PROVENANCE** | `True` on the real 4-row payload | `{"rows":[{"junk":1}]}` | **False** |
| " | " | episode column `y` added | **False** |
| " | " | episode column `mag_k1_realised` added | **False** |
| " | " | `{"rows":[]}` | **False** |

Also re-confirmed failable, on the same standard, for the MEDIUM/LOW fixes: BLOCK RULE (five
distinct injections), DECILE CAUSALITY (three), L4 COMPARATOR IDENTITY (two, one per half),
MOD-HOLD ELIGIBILITY (one), derangement fixed-point/seed-count (two), L-51 coverage (two), and both
G7 sub-clauses (one each). **The two exemptions in TRIPWIRE-1 are principled and disclosed, not
convenient:** `L1_SHAT_RANK_CONTINUOUS` is eligibility-only (its selection is finiteness, not a
threshold) and `L4_HOLD_1H_MOD` is clip-insensitive because `h_mod = clip(h·E_run/20, 1, 20)` pins
h=1 at 1.0 for any `E_run ≤ 20`. Both still **run** and both report their zero in `per_variant`
with `required_nonzero: false` and a named reason; neither is skipped.

---

### PART E — governance, on the surfaces the diff touched

| Item | Evidence |
|---|---|
| `check_no_local_accounting("SPDR-019/screen_code")` | `{'ok': True, 'banned_defs_found': []}` — executed against the current tree. |
| Derangement form (L-28) | `destroy form: DERANGEMENT`; `fixed_point_count 0`, `fixed_point_count_measured true` on all eleven arms plus entry-timing; and the destruction strength is now **disclosed as a number** (`flipped_fraction_mean 0.4991`, sd 0.0120) rather than implied by a count that is 0 by construction. |
| Spread-cost disclosure (chapter 05) | Unchanged by the diff and re-read in the emission: `spread_cost_status UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps null`, `cost_scope PARTIAL_FEES_FUNDING_ONLY`, prohibited claims `fully-net / cost-complete / tradable / deployable`, and the AMENDMENT-C5 note that cost enters no estimand, threshold or comparison. |
| Holdout | Smoke is TRAIN-only, phase (a); the `holdout` and `TRAIN fence` HARD checks both `held`. No hunk in the diff touches a band boundary. |
| Amendment-direction ledger (L-23) | Arithmetic independently recounted and correct (see R9-17 above); the LOOSER=3 flag and the five-row TIGHTER-streak flag both stand for the operator at the gate. **One gap → R10-01.** |
| One BacktestNode per process (L-31) | Not applicable — this is a screen over the OHLCV catalog, no `BacktestNode` is constructed anywhere in `screen_code/`. Unchanged by the diff. |
| XENA VOID (INFR-010 R4) | Not applicable — no XENA routing in this design. Unchanged by the diff. |
| Predeclaration integrity | Three hashes unchanged across the remediation and across my run; `generator_sha256` and `resolution_basis_sha256` reproduce the run-7 values. |

---

### PART F — residual observations (R10-01 … R10-06)

None of these blocks execution. They are recorded so the operator sees them before the gate and the
data-analyst sees them after the run.

#### R10-01 — LOW — the run-9 design edits were folded into AMENDMENT-19 without their own ledger row
**Governance:** L-23 (every pre-measurement amendment carries a direction declaration and enters the
running count). **File:** `design.md:498-507`, `1308-1310`, `1336`.

`bb92447` added a **new required emission** to the design — the per-seed flipped fraction — in both
the CONTROL SIDE-DERANGEMENT block and AMENDMENT-19(a). AMENDMENT-19's header still reads "QA run-8
remediation" and its provenance line still reads "QA run 8", and no AMENDMENT-20 row was opened, so
the ledger does not record that a run-9 review changed a design requirement. Direction is
unambiguous if it were booked (NEUTRAL-or-tighter: more must be disclosed, nothing is admitted or
excluded, no estimand, population, comparator, gate or band moves), and the requirement is already
implemented and emitted, which is why this is LOW. **Suggested, not required before the run:** open
an AMENDMENT-20 row, or extend AMENDMENT-19's header and provenance line to "QA run-8 and run-9
remediation", with a NEUTRAL direction. Routes to `quant-designer`.

#### R10-02 — LOW — two field names in the tripwire and G6 payloads still overstate what they carry
`tripwires.py:346` emits the adverse-precedence twin's price under the key `emitted_exit_price`,
while the arm's actual exit is the separate `arm_exit_price` (23606.5 vs 23493.672 on the G7 row).
The comparison itself is now correct — adverse twin vs favourable twin, same anchor, both from the
resolver — and the arm's own price is disclosed, so the substance of run 9's third point is
addressed; the **key name** is not. Separately, `golden.py:243-246`'s `legal_variant_is_the_emitted_one`
reduces to "`per_variant` is non-empty and `changed_state_rows > 0`" (`v.get("legal_episodes", 0) >= 0`
is true for any count), so it is computed and does fail on an empty payload, but it does not verify
the proposition its name states. Both are labelling, not logic. Analyst note: read
`arm_exit_price`/`arm_exit_reason` when you want the emitted arm's fill.

#### R10-03 — LOW — the block-rule exemption is now validated per cell but still uncapped in aggregate
Run 9's required fix (reason per cell, full list, sizing as a named bucket) is fully implemented and
executes. What remains: **5,000 fabricated degenerate cells each carrying a valid `n_dates < 7`
reason still leave `held: True`**, carried by the 1,649 compliant cells. Also note the exemption
predicate is `n_dates < 7`, looser than the `n_dates < 2` run 9 used as its example — the code
comment explains that `< 2` left real thin cells unclassified, and the threshold is disclosed in the
artifact as `degenerate_reason_required`. Analyst note for the 25-symbol run: read
`n_degenerate_cells_no_ci` as a number, not as a pass/fail — a large count with valid reasons is a
thinness disclosure the HARD check will not raise.

#### R10-04 — LOW — the plant-curve rung grid does not bracket the control's resolution
See R9-06. All four rungs read 1.0 (two arms 0.9995) because 5 bps is already ≈2.4 null sd. Two
things would make §6's UNUSABLE threshold numerically locatable, neither of them a code fix:
finer rungs (e.g. 0.5 / 1 / 2 bps), and averaging the rate over several base draws rather than one —
the single deranged base is a random draw and on `L0_BASELINE` it landed **1.3 null sd above the
null median**, which pre-loads the curve even though the construction is correct. Routes to
`quant-designer` if the operator wants a located resolution; otherwise the correct reading of the
present curve is "the control resolves every effect size this design declares".

#### R10-05 — LOW — the L-51 HARD check's coverage floor is 10, not the 12 subsets the design names
`selfcheck.py:302` marks the check on `covered >= 10`. The emission covers 12 of 12, so the clause
is satisfied in fact; but the check would still pass if both `MDE50_*` cells were absent — the
exact subset run 9 singled out as the one the design names explicitly. It fails at 9 tokens and at
run-9's 5, so it is a real check, just two tokens loose. `n_required_tokens_covered` is emitted, so
the operator can read the true coverage directly.

#### R10-06 — INFORMATIVE — the h=1 MOD-hold pair separates on 2.0% of its episodes
Now measured rather than argued: `L4_HOLD_1H_MOD` is identical to its UNMOD twin on **26,502 of
27,036** compared episodes (98.0%), separating on 534. §12's hard failure is "identical on **every**
episode", and it is not, so the check correctly passes. But that pair carries very little
independent information, for the structural reason `clip(h·E_run/20, 1, 20)` pins h=1 at 1.0
whenever `E_run ≤ 20` — and the design's own measured E[run] scale is 19–23 h. The h=4/12/20 pairs
separate on 99.9%, 99.9% and 97.4% of their compared episodes respectively. Analyst note: do not
read the h=1 MOD/UNMOD contrast as a powered comparison.

---

### Standing execution blockers

1. **DISCHARGED** (re-verified) — AMENDMENT-7 / registered-C6 departure.
2. **DISCHARGED** (re-verified) — `reflection-inputs.md` §9, signed option B at `9d8832e`.
3. **STANDS (lane-wide, unchanged)** — the per-symbol spread pin. It does not block this measurement
   under AMENDMENT-C5; the disclosure block is intact and the code makes no money read.
4. **DISCHARGED** — run-9 blocker 4 (**R9-01, R9-02, R9-03**). All three HARD checks now fail on
   their own subject under injection; evidence in PART D.
5. **DISCHARGED** — run-9 blocker 5 (**R9-04 … R9-10**, seven MEDIUM). All seven closed; the two
   that retain a soft edge are recorded as R10-03 and R10-04/R10-05 with the residual stated.
6. **DISCHARGED** — run-8 blockers 4, 5, 6 (all 29 findings, closed at run 9;
   `check_no_local_accounting` re-run green here).
7. **OPERATOR FLAGS AT THE GATE, unchanged and not blockers** — L-23 requires two: LOOSER stands at
   3 active rows (AMENDMENT-1 full TRAIN, -2 M15, -10 hold grid), and the TIGHTER streak within
   AMENDMENTS 12-18 is five rows. Both are declared in `design.md:1341-1347`.

---

**FAILING_ARTIFACT:** none. No artifact fails.

**REQUIRED_SKILL:** none required before execution. Optional and post-gate: `quant-designer` for
R10-01 (book the run-9 design edits in the amendment ledger) and R10-04 (finer plant-curve rungs if
a located control resolution is wanted); `experiment-developer` for R10-02 (two field names) and
R10-05 (raise the L-51 floor from 10 to 12). None of the four changes a measured quantity, so none
needs to precede the run.

**Execution authorisation: YES.**

The full 25-symbol phase-(a) screen is authorised from QA's side. The three checks that blocked run
9 now fail when I break the thing they check; the other fourteen findings are closed on evidence;
the emission reproduces 28/28 with an empty failure list on an independent re-run of the sanctioned
smoke; and nothing in the remediation moved an estimand, a threshold or a comparison — the episode
count, the cell count and all three predeclaration hashes are unchanged. Execution remains the
operator's gate, and the two L-23 flags in blocker 7 are the operator's to read at it.

---

### What I did not reach

- **I did not run the full 25-symbol screen.** Operator-gated and unauthorised. Everything above
  comes from the sanctioned 2-symbol smoke at `n_boot = 200, jobs = 2`, from isolated function calls
  on that emission, or from hand derivation. At `n_boot = 2000` the ladder and the paired bootstrap
  scale up; the control battery does **not** (that is R9-05's fix), but I verified its behaviour at
  2,000 seeds, not the full run's wall-clock or memory cost.
- **Every real-data claim still rests on BTCUSDT and ETHUSDT** — carried forward from run 9,
  unchanged and unaddressable inside the authorised smoke. The 23 other symbols are unexercised.
  `PARENT-GATE PARITY` again passed at `n_ok 4/4`, so the 8 PARITY-EXEMPT symbols and the 15
  remaining non-exempt symbols were never in the run and the exempt-list mechanism is still untested
  against real parent NaNs this round. **R9-10's fix is anchored on BTCUSDT, which was present in
  the smoke**, so the `anchor_fallback` branch (`run_screen.py:964-972`) is the one path in the
  remediation I could not exercise — it will not be taken on a 25-symbol run that includes BTCUSDT.
- **I did not verify the M15 clock beyond the fact that it ran** — carried forward from run 9,
  unchanged. Both clocks were in the smoke and M15 rows are present in the cell grid and now in the
  L-51 subsets (R9-07 added them), but I checked no M15 fill, no M15 hold conversion and no M15
  block behaviour individually. **M15 carries the primary read** (AMENDMENT-2). This is the largest
  coverage gap in the review series and it is not closable by a 2-symbol smoke.
- **I did not review `python/experiments/SPDR-020/screen_code/`** — carried forward from run 9,
  unchanged. It shares `resolution_basis.py` and the resolution artifacts, and it moved again during
  this review (`1979b93`, plus untracked `results/run_plan.json` and `results/shards/`). Several
  shapes corrected here — the plant-curve base, the degenerate-exemption bucketing, the tripwire twin
  construction, the source-token assertions — are exactly what a sibling implementation repeats.
  **That directory needs its own QA run; do not infer its state from this one.**
- **I did not re-audit the measurement path**, by design: run 9 scoped this run to the diff plus the
  smoke on the ground that the corrections change what is checked, not what is computed. I tested
  that premise (PART B) and it held, but "the modules are untouched and the counts are identical" is
  a weaker statement than "I re-derived the estimand", and only the former is on the record here.
- **I did not construct a genuinely non-causal pipeline** to confirm TRIPWIRE-1's payoff delta moves
  in the expected direction — same gap run 9 recorded. I showed the tripwire re-selects episodes
  across all fifteen variants and that each limb dies when I disable it; §6.1 makes the delta's
  direction reported, never a pass condition.
- **I did not audit `xen.evaluation.block_bootstrap_ci` or `xen.resolution_basis` internals**, only
  that the predeclaration hashes match and that the screen's fast path is unchanged by this diff.
- **I did not re-derive the parent gates end to end.** `parent_gates.py` is untouched by the commit;
  R9-03's fix asserts tokens *in* that file rather than recomputing what it produces, so a rewrite
  that kept the tokens and changed the arithmetic would pass. Run 7 executed that path.
- **I did not quantify the effect of any finding on any result.** There is no authorised run, and
  that is the data-analyst's object in any case.

---

## QA run 11 — 2026-07-29T23:47:56Z — mode: subagent — HEAD 1979b93 (dirty: SPDR-019/design.md, SPDR-019/qa-review.md, SPDR-019/screen_code/integrity.py, SPDR-019/screen_code/metrics.py; SPDR-019/results/* and SPDR-020/results/* untracked)

Verdict: **REVISE**

Subject: the two HARD failures of the first full-scale run (25 symbols, `n_boot` 2000, 5,753,583
episodes, 13,377 metric rows, 44 min) — `BLOCK RULE` and `log R never unaccompanied` — and the
remediation carried by AMENDMENT-20 + the `screen_code/` diff.

Evidence base. Failing full-run artifacts read unmodified from
`…/scratchpad/spdr019_fullrun_FAILING/` (`code_sha256 4fcea2d049c0745d…`). The repo `results/`
directory holds a **2-symbol smoke at `n_boot` 200** whose `code_sha256` I recomputed with
`selfcheck._sha256_tree(SCREEN_CODE_DIR)` → `9e46e90caa51db30fb548a0e635a542376975d69ea78d33925ef66537364c6da`,
**byte-identical to the reported value**, so the smoke provably ran the code now on disk. Both
runs share `generator_sha256 72c6b1f953cae24c…`, `expected_resolution_sha256` and
`resolution_basis_sha256`.

### PART A — the diagnosis, reproduced independently

I re-derived both failures from the preserved parquet and integrity JSON without using the
developer's account.

| Claim under test | What I found | Verdict |
|---|---|---|
| 2 of 28 HARD checks failed | `all_hard_pass false`, `hard_fail_names = ['BLOCK RULE', 'log R never unaccompanied']`, `integrity_violation true`, `n_hard_checks 28 == expected 28` | REPRODUCES |
| 5 rows carried a `log R` with no CI/MDE | 13,377 rows; 12,503 carry a CI; 12,508 carry a finite `log_R`; **exactly 5** rows have finite `log_R` with `ci_low`/`ci_high`/`ci_width`/`block_mde` all null | REPRODUCES |
| all 5 have `n_dates = 1` | `BLURUSDT/L1_SHAT_RANK_CONTINUOUS/M15/{0.25,0.50}/DESIGN` and `1000BONKUSDT/L2_JOINT_HMM_HIGH_AND_K12_HIGH/H1/{0.25,0.50,1.00}/DESIGN` — **all five `n_dates = 1`**, `p` ∈ {0.4, 0.667, 0.5}, `W` and `L` finite | REPRODUCES |
| cause is assignment order in `cell_metrics` | `metrics.py:363` `out["log_R"] = log_R_from_pWL(p, W, L)`; `metrics.py:376` `ci = envelope_ci_logR(suff, …)`; `metrics.py:136` early-returns `ci_low/ci_high = nan` at `n_days < 2`. A one-day cell therefore keeps a computed `log R` and loses its interval. Confirmed a **code defect**, not a §12 defect | REPRODUCES |
| 3 cells `unclassified`, which is fatal | `n_unclassified_cells 3`, all with `reason: null`; `deg_ok = all(...) and not unclassified` (`integrity.py:580`) drives `battery_ok` → `held false` | REPRODUCES |
| the 3 are the named cells | `1000RATSUSDT/L4_TARGET_A1_MOD/H1/1.0` in **TRAIN and CONFIRM** (`n = 11`, `n_dates = 8`, `p = 1.0`, `L` undefined — eleven episodes, every one a winner) and `1000BONKUSDT/L2_INTERACTION_HMM_X_K12/M15/1.0/DESIGN` (`n = 1`, `n_dates = 47`, `p`/`W`/`L` all undefined) | REPRODUCES |
| the pre-existing reason described none of them | all 31 exempt cells carried the single string `n_dates < 7 (min day-block in {1,3,7} sweep)`; the 3 unclassified have `n_dates` 8, 8, 47 | REPRODUCES |
| 13 exempt cells had `n_dates` 2–4 | exempt-cell `n_dates` histogram `{1: 18, 2: 4, 3: 2, 4: 7}` = 31; **4 + 2 + 7 = 13**; none ≥ 7 | REPRODUCES |
| the design authorised no exemption path at all | I read §12 in the pre-diff design: the `log R never unaccompanied` row and the block-rule rows exist; **no row mentions a cell without a CI**, four buckets, a reason token, or `unclassified`. The four-bucket accounting, the `n_dates < 7` reason and `unclassified`-is-fatal are all in `integrity.py` only, added at the run-9 R9-04 remediation | REPRODUCES |

Bucket reconciliation, recomputed from the parquet: 12,503 with a CI + 840 sizing-suppressed
(`sizing_no_logR_claim`, reason `SIZING_VARIANT_MAY_NOT_CARRY_A_LOG_R_CLAIM`) + 31 exempt + 3
unclassified = **13,377** = the row count. The four buckets do reconcile.

### PART B — design-to-code fidelity trace on the amended clauses

Expected behaviour derived from the amended design text first, then read against the code.

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| §12 new row: every metric row lands in exactly **one** of four named buckets and the four reconcile to the row count | `integrity.py:526-582` (`has_ci` / sizing / `not ps` / else) + `:588-597` counts | MATCHES | reconciliation verified numerically above on the failing run and on the smoke (1,649 + 108 + 1 + 0 = 1,758 = `n_metric_rows`) |
| §12 new row: `unclassified` is a **hard failure** | `integrity.py:580` `deg_ok = all(d.get("reason") …) and not unclassified` | MATCHES | fault-injected below; `held` goes False |
| §12 new row: an exempt cell must **name** which condition applies | `metrics.py:398-408` emits `ci_absent_reason`; `integrity.py:552` reads it | MATCHES **for `cell_metrics` rows only** | see R11-01 — interaction rows never receive the key |
| AMENDMENT-20(a)(i): token `LOG_R_UNDEFINED` = one-sided outcome set (`p = 1` ⇒ `L` undefined; `p = 0` ⇒ `W` undefined) **or** no signed outcome leaving `p` undefined | `metrics.py:402` `if not np.isfinite(out["log_R"])`; `integrity.py:558` `log_r_undefined = not _fin("log_R")` | **DEVIATES** | the design defines the condition on `p`/`W`/`L`; both code sites test the `log_R` **field**. Producer-side this is exact (`log_R_from_pWL`, `metrics.py:74-78`, returns NaN on precisely that predicate). Checker-side it is **vacuous** — see R11-02 |
| AMENDMENT-20(a)(ii): token `N_DATES_LT_2_NO_DAY_BLOCK` = fewer than 2 calendar days, no day-block to resample | `metrics.py:404` `elif n_days < 2`; `integrity.py:559` `too_few_days = … n_dates < 2` | MATCHES | matches `envelope_ci_logR`'s own guard `if n_days < 2` (`metrics.py:136`) exactly |
| §12 new row: the named condition is **validated against that cell's own emitted `p`, `W`, `L`, `n`, `n_dates`** | `integrity.py:556-562` | **DEVIATES** | `p`, `W`, `L`, `n` are **emitted for audit** (`:566`) but only `log_R` and `n_dates` are **used**. `log_R` is not in the design's list, and it is the one field the same commit overwrites |
| AMENDMENT-20(a): "a reason that does not describe the cell is a hard failure" | `integrity.py:562` `reason = claimed if admissible.get(claimed) else None` | MATCHES for `N_DATES_LT_2`; **unenforceable for `LOG_R_UNDEFINED`** | R11-02 |
| AMENDMENT-20(a): `n_dates < 7` is **WITHDRAWN** | old `min_dates = max(BOOT_BLOCKS_DAYS)` branch deleted; `degenerate_reason_required` restated (`integrity.py:597-600`) | MATCHES | no residual reference to `n_dates < 7` anywhere in `screen_code/` (grepped) |
| AMENDMENT-20(a): the exempting conditions are **exactly two** | `admissible` dict, `integrity.py:560-563` | MATCHES as written | but see R11-03: one of the three cells the amendment was written for fits **neither** honestly |
| AMENDMENT-20(b): §12's unaccompanied rule is **CONFIRMED UNCHANGED**; the fix is suppression | `metrics.py:409` `out["log_R"] = float("nan")` inside the CI-absent branch | MATCHES | §12 row text unchanged in the diff — confirmed by `git diff` (only the new "Row accounting" row is added) |
| AMENDMENT-20(b): suppression is "already this design's answer" | `log_R_suppressed_reason` / `sizing_no_logR_claim` path, `integrity.py:534-540` | MATCHES | the sizing bucket is a genuine precedent; the new suppression reuses the same mechanism |
| §12 (pre-existing): the unaccompanied rule is asserted over `metrics_by_cell`, `layer_deltas` **and** the resolution ladder "alike" | `selfcheck.py:309-316` | **DEVIATES (pre-existing)** | asserts on `metrics_df` only, and keys on a column literally named `log_R`. See R11-04 — informative, no violation in data |
| Ledger: 5 looser / 9 tighter / 6 neutral; active 4 / 8 / 6 | design.md ledger block | MATCHES | 5+9+6 = 20 = AMENDMENTS 1…20; two supersessions (-7 by -17, -11 by -15) → 18 = 4+8+6. Arithmetic correct |
| L-23: LOOSER note lists 4 and is flagged at the execution gate | design.md L-23 note | MATCHES | -1, -2, -10, -20 named; flag present |
| L-23 clause 3: streak flagged | design.md streak note | MATCHES | streak note retained as history + explicit statement that AMENDMENT-20 breaks monotonicity. Honest |

### PART C — did any estimand move? (item 3)

Two independent lines, both clean.

**C1 — structural.** `git diff` on `metrics.py` is a **pure insertion**: 18 added lines, 0 removed,
entirely inside `cell_metrics`, guarded on `not (isfinite(ci_low) and isfinite(ci_high))`. For a
row that carries a CI the branch adds `ci_absent_reason = None` and nothing else. I then grepped
every `log_R` site and confirmed **no code reads `out["log_R"]` after line 409**: `W_L`, `p_be`,
`p_be_net`, `identity_residual_bps` are computed at `:356-373` from `p`/`W`/`L`; `mirror_band`
(`:440-445`) reads `ci_low`/`ci_high`; `ladder`/`mde50/80/95` (`:448-450`) rebuild from `suff`;
`realised_c` and `effective_n` read `block_mde` and `iid_half`.

Two candidate propagation paths, both checked and both closed:
- `_attach_homogeneity` (`run_screen.py:646-653`) feeds per-symbol `log_R` into `i_squared`,
  `homogeneity_q`, `per_symbol_spread_log_R` on POOLED cells. `metrics.homogeneity` (`:482`) filters
  `np.isfinite(v) & np.isfinite(s) & (s > 0)` and `s = block_mde/1.96`. For all 5 suppressed rows
  `block_mde` is NaN, so they were **already dropped before the change**. No pooled statistic moves.
- `_layer_deltas` (`run_screen.py:488-490`) skips any row with `band != "TRAIN"`. All 5 suppressed
  rows are `band = DESIGN`. No contact.

**C2 — empirical, cross-version, on real data.** `p`, `W`, `L`, `n`, `n_dates`, `mean` and
`log_R` do not depend on `n_boot`, so the pre-fix full run and the post-fix smoke are directly
comparable on their shared per-symbol cells. Joining on
`(variant_id, clock, delta, scope, band)` for `scope ∈ {BTCUSDT, ETHUSDT}` gives **1,164 cells in
both**, and across `n, mean, p, W, L, n_pos, n_neg, p_flat, n_dates, W_L, p_be, p_be_net,
identity_residual_bps, mean_signed_rows, kappa, kappa_n, n_nominal, log_R` every column returns
**max |Δ| = 0.0** with zero finite/non-finite flips. Schema delta is exactly one added column,
`ci_absent_reason`; nothing removed.

I also re-derived `log_R` from `(p, W, L)` on all 13,377 failing-run rows: exact match
(`max |Δ| = 0.0`) wherever both are finite; 840 rows where the recompute is finite and the emitted
value is null (**exactly** the sizing-suppressed bucket); 311 rows where the emitted value is finite
and the recompute is null (**exactly** the `L2_INTERACTION_HMM_X_K12` rows, whose `log_R` is a paired
Δ and whose `p`/`W`/`L` are hardcoded NaN at `run_screen.py:466`).

**Conclusion:** the 12,503 CI-carrying cells are arithmetically untouched, and the only `log_R`
values that change are the 5 suppressed ones. Item 3 **verified**.

### PART D — can `BLOCK RULE` still fail on its own subject? (P-23 / L-52, item 4)

Fault injection through `integrity.check_block_rule` directly. Overall `held` is False in every row
below because my synthetic 200-episode frame cannot satisfy clause 5 (`boot_eq`), so the
discriminating field is the **envelope clause** — the clause AMENDMENT-20 actually amends. Three
valid-claim rows are included as negative controls.

| # | Injected row | envelope `held` | exempt | unclassified |
|---|---|---|---|---|
| 0 | all cells carry a CI (control) | True | 0 | 0 |
| A | `n_dates = 1`, claims `N_DATES_LT_2_NO_DAY_BLOCK` (true) | True | 1 | 0 |
| B | `p = 1`, `L` undefined, claims `LOG_R_UNDEFINED` (true) | True | 1 | 0 |
| C | **wrong token** — `n_dates = 8` claims `N_DATES_LT_2_NO_DAY_BLOCK` | **False** | 0 | **1** |
| D | **missing token** — `ci_absent_reason = None` | **False** | 0 | **1** |
| E | **bogus token** — `"BANANA"` | **False** | 0 | **1** |
| F | **key absent entirely** | **False** | 0 | **1** |
| G | **neither condition** — `n_dates = 47`, `log_R` **finite**, claims `LOG_R_UNDEFINED` | **False** | 0 | **1** |
| H | **neither condition** — `n_dates = 47`, `p`/`W`/`L` finite, `log_R` **nulled**, claims `LOG_R_UNDEFINED` | **True** ⚠ | 1 | 0 |
| I | both conditions true, claims `LOG_R_UNDEFINED` | True | 1 | 0 |
| J | both conditions true, claims `N_DATES_LT_2_NO_DAY_BLOCK` (swapped) | True | 1 | 0 |

The check **can** still fail: C–G all drive `held` False. That part of P-23 is satisfied.

**Row H is the defect** and it is not hypothetical: `metrics.py:409` nulls `log_R` on **every** row
that enters the exemption branch, so the shape the artifact can actually present is H, never G. Full
finding at R11-02.

**On the swapped-token question (I vs J).** When both conditions genuinely hold, a swapped token is
admissible. I judge this **acceptable**: the cell is exempt on either ground, no downstream number
depends on which token is recorded, and `integrity.py:566-568` emits **both** derived booleans plus
`p`/`W`/`L`/`n`, so the audit record is complete regardless of which token was claimed. This is only
harmless *because* both booleans ship — and R11-02 must be fixed for `log_R_undefined` to carry any
information at all.

### PART E — findings

**R11-01 — BLOCKING (HARD). The fix does not close the `BLOCK RULE` failure. One of the three
unclassified cells survives it, so the full 25-symbol re-run will HARD-fail again.**

The third unclassified cell, `1000BONKUSDT / L2_INTERACTION_HMM_X_K12 / M15 / δ=1.0 / DESIGN`
(`n = 1`, `n_dates = 47`), is **not** a `cell_metrics` row. It is an interaction row appended by
`run_screen._extra` at `run_screen.py:453-474`, which writes its dict literally and **never sets
`ci_absent_reason`**. `grep -rn 'ci_absent_reason' screen_code/*.py` returns 4 sites in `metrics.py`
and 1 read in `integrity.py` — nothing in `run_screen.py`.

I reproduced the cell exactly as `_extra` builds it and ran it through the fixed
`check_block_rule`:

```
INTERACTION ROW as actually built by run_screen._extra:
  envelope held = False   degenerate = 0   UNCLASSIFIED = 1
  entry: {..., 'reason': None, 'claimed_reason': None, 'log_R_undefined': True,
          'n_dates_lt_2': False, 'p': nan, 'W': nan, 'L': nan, 'n': 1.0}
SAME ROW WITH the token the design mandates:
  envelope held = True    UNCLASSIFIED = 0
```

Predicted post-fix full-run outcome: 33 of 34 exempt cells classified (28 `LOG_R_UNDEFINED` via
`cell_metrics` + 5 `N_DATES_LT_2_NO_DAY_BLOCK`), **1 unclassified**, `BLOCK RULE` **still FAILS**.
The `log R never unaccompanied` failure *is* closed by the suppression, so the re-run would fail
1 of 28 rather than 2 of 28 — an unauthorised-run-shaped outcome, not a clean run.

AMENDMENT-20(a)(i) names this exact cell as an instance of `LOG_R_UNDEFINED`, so the clause is
**booked in design and MISSING in code**. Route: `experiment-developer`.

**R11-02 — BLOCKING (fidelity + P-23). Integrity's re-derivation of `LOG_R_UNDEFINED` is vacuous:
it reads a field the producer overwrites in the same commit.**

`integrity.py:558` computes `log_r_undefined = not _fin("log_R")`. But `metrics.py:409` sets
`out["log_R"] = float("nan")` for **every** row whose CI is absent — i.e. for every row that can
reach `integrity.py:552`. So `log_r_undefined` is **unconditionally True inside the exemption
branch**, `admissible["LOG_R_UNDEFINED"]` is unconditionally True, and the `LOG_R_UNDEFINED` token
can never be rejected. Consequences:

1. The emitted audit field `log_R_undefined` is constant-True and carries no information. The smoke
   confirms it: its single exempt cell reports `log_R_undefined: true` — correct there, but
   uninformative by construction.
2. Fault case H passes: a cell with 47 calendar days, finite `p`/`W`/`L` and an **empty bootstrap
   battery** — a genuine defect, and precisely the case the pre-diff code caught with
   `reason = None  # enough dates but empty battery → real defect` — is now silently exempted if it
   claims `LOG_R_UNDEFINED`.
3. The check loses its independence. End-to-end the pipeline still catches case H, but only because
   the **producer** (`metrics.py:406-408`) declines to emit a token — `integrity.py` is supposed to
   be the check that does not trust the producer. That is the whole reason this apparatus exists.
4. It contradicts the design text: §12's new row requires validation "against that cell's own
   emitted `p`, `W`, `L`, `n`, `n_dates`". `log_R` is not in that list, and it is the one field the
   commit mutates.

**Required change** (two lines, `integrity.py:558`): derive the condition from `p`/`W`/`L` as the
design states, e.g. `log_r_undefined = not np.isfinite(log_R_from_pWL(row.get("p"), row.get("W"),
row.get("L")))`, or the explicit predicate `not all finite(p, W, L) or p <= 0 or p >= 1 or W <= 0
or L <= 0`. `metrics.log_R_from_pWL:74-78` is exactly that predicate, so the two agree by
construction.

I verified this fix is **behaviour-preserving on the real run and discriminating**: across the 34
non-sizing no-CI cells the `p`/`W`/`L` derivation gives **29 undefined / 5 defined**, `n_dates < 2`
gives **18**, cells satisfying **neither = 0**, cells satisfying **both = 13**. The 5 defined ones
are exactly the 5 suppressed rows, all `n_dates = 1`, so they remain admissible on their own token.
Nothing reclassifies; case H starts failing. Route: `experiment-developer`.

**R11-03 — BLOCKING (design). `LOG_R_UNDEFINED` is the wrong condition for the interaction cell,
and asserting it there widens the exemption to all 311 interaction rows.**

AMENDMENT-20(a)(i) justifies the interaction cell as "a cell with NO SIGNED OUTCOME leaves `p`
itself undefined". That is not what the artifact says. `run_screen.py:466` hardcodes
`"p": nan, "W": nan, "L": nan` on **every** interaction row — I confirmed all 311 in the failing run
carry `p = W = L = NaN`, including 310 with healthy CIs, `per_seed_ci` lengths up to 945 and `n` up
to 1,090. `p` is undefined on that row **by construction of the row type**, not by its outcome set.
So under either derivation — the current `log_R`-field one or the corrected `p`/`W`/`L` one —
`LOG_R_UNDEFINED` becomes admissible for every interaction row regardless of whether it has 1
episode or 1,027. The exemption stops being narrow.

The cell's actual property is different and more specific: the paired combination
`joint − shock − k12 + l0` could not be formed because an arm had `n = 1`, so
`metrics.paired_combo_ci` returned an empty battery. That is a **third condition the design has not
booked**, and it is the honest one.

**My recommendation, and it is the operator's question from item 5:** for this cell the right answer
is **exclude before scoring, not exempt after**. An interaction row whose constituent arm cannot
support the combination should not be constructed at all — there is nothing to interact — and
`_extra` already has the machinery: `run_screen.py:430-437` breaks out of arm assembly when an arm
is missing. Extending that guard to "an arm cannot support the paired bootstrap" removes the cell
from the frame, keeps the four-bucket accounting genuinely exhaustive over rows that exist, and
needs no new exemption token. Exclusion is self-documenting (`n_metric_rows` drops, visibly);
exemption is a place a future thin-cell defect can hide, which the amendment's own assessment
paragraph concedes. Route: `quant-designer`.

**R11-04 — INFORMATIVE (pre-existing). The unaccompanied rule is asserted on one artifact, not
three.** §12 requires it "asserted over `metrics_by_cell`, `layer_deltas` and the resolution ladder
alike". `selfcheck.py:309-316` builds `need = {log_R, ci_low, ci_high, ci_width, block_mde}` and
tests `metrics_df` only, keyed on a column named literally `log_R`; `layer_deltas` ships
`log_R_layer` / `log_R_L0` / `delta_log_R` and would not be matched even if it were passed in. I
checked the data directly and found **no violation**: `resolution_ladder` 1,649 finite-`log_R` rows,
0 with any companion missing; `layer_deltas` 522 rows, 0 with any companion missing on any of the
three `log_R`-family columns. Non-blocking, but it is the assertion that failed, so the scope gap
should be closed rather than left implicit. This surface was touched at run 9 (line 3128) without
the multi-artifact scope being resolved.

**R11-05 — INFORMATIVE. The sanctioned smoke exercises almost none of what it was run to verify;
its 28/28 is not evidence the two failures are closed (item 6).**

The smoke is `BTCUSDT` + `ETHUSDT` only. **None** of `BLURUSDT`, `1000BONKUSDT`, `PYTHUSDT`,
`1000RATSUSDT` — the four symbols that produced every one of the 5 unaccompanied rows and all 3
unclassified cells — is present. Concretely, in the smoke:
- **0** `log_R` suppressions fired. My cross-version join shows `log_R` `oldOnlyFinite = 0`, i.e.
  `metrics.py:409` never changed a value. The suppression path is **entirely unexercised**.
- **0** `N_DATES_LT_2_NO_DAY_BLOCK` tokens issued.
- **0** interaction-row exemptions, so R11-01 could not surface.
- Its **1** exempt cell is `ETHUSDT/L1_SHAT_DECILE_GE9/H1/1.0/CONFIRM`, `n = 2`, `n_dates = 2`,
  `p = 0.0`, `W` undefined, `claimed_reason` and `reason` both `LOG_R_UNDEFINED`,
  `log_R_undefined: true`, `n_dates_lt_2: false`.

That last item **does** verify the reported reclassification, and I confirm it: at `n_dates = 2`
this cell was previously exempted as `n_dates < 7` — a condition it does not have — and is now
exempted as `LOG_R_UNDEFINED`, which it does have (`p = 0` ⇒ `W` undefined). The withdrawal of
`n_dates < 7` is demonstrated on real data. Everything else about the two failures is untested at
runtime.

I did **not** re-run the smoke: QA is read-only and a re-run would overwrite `results/`. Instead I
verified its provenance by recomputing the code-tree hash (exact match) and reproduced the two
failure modes against `check_block_rule` directly, including a field-exact replay of the surviving
unclassified cell — stronger evidence for the modes the smoke cannot reach. **No full-scale run has
been done since the fix**, and per R11-01 one should not be launched until it is.

### PART F — judgement on AMENDMENT-20 (item 5)

*Is the DIRECTION honestly labelled?* **Yes.** LOOSER is correct and is the harder of the two labels
to volunteer: read literally, the pre-diff design contained no exemption path, so every one of 34
near-empty cells was a hard failure and this row creates the relief. The tightening component is
real and quantified — 13 cells were being exempted for a condition they do not have, and I verified
the count (`n_dates` histogram 2:4, 3:2, 4:7). The ledger arithmetic checks out (5/9/6 total,
4/8/6 active, 20 rows, 18 after two supersessions), the L-23 LOOSER note correctly lists four, both
required operator flags are present, and the amendment volunteers that it breaks its own tightening
streak. The assessment paragraph states two points against itself, including the one that matters
most — that this is booked *after* a failing run. I found nothing overstated and nothing netted away.

*Is booking an exemption inside a HARD integrity check after a failing run acceptable?* **For the
`cell_metrics` cells, yes — narrowly, and on these specific grounds.** This is a genuine
specification gap, not an inconvenient result: a cell with eleven episodes all of which are winners
has an undefined `log(W/L) − log((1−p)/p)` as a matter of arithmetic, not of data quality, and no
rule the design could have written would make it bootstrappable. The remedy moves no estimand
(PART C: bit-exact on 1,164 cells), no band, no comparator and no cost figure; no exempt cell
contributes a `log R` to anything; and the amendment is **strictly narrower** than the undeclared
code it replaces. Booking it is better governance than the status quo, which was an
implementation-invented exemption running unbooked since the run-9 R9-04 remediation. The right
criticism to make of this episode is not the amendment — it is that `n_dates < 7`, four buckets and
`unclassified`-is-fatal reached a full-scale run without ever appearing in design.md.

*Is the exemption too wide?* **As drafted, for one of its three cells, yes** — and that is R11-03,
which is why this run is a REVISE rather than an APPROVE-with-notes. Applied to the interaction row
the exemption rests on a `NaN` that `run_screen.py:466` writes unconditionally, so it would exempt
all 311 interaction rows on identical evidence. There the operator's alternative framing is the
correct one: **exclude such a cell before scoring rather than exempt it after.** I would keep
exemption-after for the one-sided `cell_metrics` cells — those are real, reportable cells that
happen not to admit an interval, and suppressing the interval while keeping the row is honest — and
switch to exclusion-before-scoring for interaction rows that cannot form their combination.

### Checks independently verified clean

- Both HARD failures reproduced from the preserved artifacts without relying on the developer's
  account; every numeric claim in AMENDMENT-20 recomputed and reproducing (5 rows all `n_dates = 1`;
  13 at `n_dates` 2–4; 18 at `n_dates = 1`; none ≥ 7; 31 + 3 = 34; 12,503; `n = 11`/`n_dates = 8`/
  `p = 1.0` for `1000RATSUSDT`; `n = 1`/`n_dates = 47` for `1000BONKUSDT`).
- Estimand invariance: bit-exact across 18 columns on all 1,164 shared per-symbol cells; single
  additive schema column; no downstream reader of the suppressed `log_R` (homogeneity and
  `_layer_deltas` both verified closed).
- §12's `log R never unaccompanied` row is **textually unchanged** by the diff — the design did not
  weaken the rule that failed.
- `n_hard_checks = 28 = expected_hard_checks`, all 28 present by name in both runs; no check added,
  removed or renamed by the diff.
- No residual reference to `n_dates < 7` anywhere in `screen_code/`.
- `BLOCK RULE` can still fail: 5 of 6 injected faults drive the envelope clause False.
- Amendment-direction ledger arithmetic and both L-23 flags.
- Code provenance: smoke `code_sha256` recomputes exactly to the code now on disk; `generator_sha256`,
  `expected_resolution_sha256`, `resolution_basis_sha256` identical across both runs.
- Spread disclosure intact (`UNAVAILABLE_NOT_CHARGED`, `PARTIAL_FEES_FUNDING_ONLY`,
  `spread_rt_bps: null`, prohibited-claims list present); the diff does not touch cost.
- Diff scope: 3 files (`design.md`, `integrity.py`, `metrics.py`) plus `qa-review.md`. No holdout
  surface, no fence, no causality rule, no `BacktestNode`, no accounting primitive, no registry.

### FAILING_ARTIFACT / REQUIRED_SKILL

```
FAILING_ARTIFACT: python/experiments/SPDR-019/screen_code/run_screen.py:453-474
                  (interaction rows never emit `ci_absent_reason`; the surviving
                   unclassified cell → BLOCK RULE still HARD-fails)   [R11-01]
FAILING_ARTIFACT: python/experiments/SPDR-019/screen_code/integrity.py:558
                  (`log_r_undefined` re-derived from a field metrics.py:409
                   overwrites → the LOG_R_UNDEFINED token cannot be rejected) [R11-02]
FAILING_ARTIFACT: python/experiments/SPDR-019/design.md AMENDMENT-20(a)(i)
                  (interaction cell mislabelled LOG_R_UNDEFINED on a structural
                   NaN; exempts all 311 interaction rows on the same evidence) [R11-03]
REQUIRED_SKILL:   quant-designer      → R11-03 (choose exclusion-before-scoring for
                                        interaction rows, or book the third condition
                                        explicitly and bound it)
REQUIRED_SKILL:   experiment-developer → R11-01, R11-02 (after R11-03 settles the
                                        design question, since R11-01's remedy depends
                                        on it), R11-04 (optional, non-blocking)
```

### Standing execution blockers

1. **R11-01** — the full 25-symbol re-run will HARD-fail `BLOCK RULE` again on one unclassified
   cell. Field-exact replay, not inference.
2. **R11-02** — the amended HARD check cannot reject its own primary token; the design's stated
   validation basis is not the one implemented.
3. **R11-03** — the design question underneath R11-01 is unsettled: exempt the interaction cell, or
   exclude it before scoring. R11-01's remedy differs depending on the answer, so this is decided
   first.
4. **No full-scale run since the fix**, and the 2-symbol smoke exercises none of the three failure
   modes above (R11-05). A smoke that includes at least one of `BLURUSDT`, `1000BONKUSDT`,
   `PYTHUSDT`, `1000RATSUSDT` is the minimum runtime evidence for a re-authorisation.

**Execution authorisation: NO** — for the full 25-symbol re-run. Re-authorise after R11-03 is
decided, R11-01/R11-02 are implemented, and a smoke covering the four affected symbols returns
28/28 with 0 unclassified.

### What I did not reach

- **I did not re-run the screen at any scale.** QA is read-only and a run would overwrite
  `results/`. My runtime evidence is `check_block_rule` invoked directly on synthetic rows and on a
  field-exact replay of the real surviving cell, plus static reads of the two preserved artifact
  sets. The prediction that the re-run fails 1 of 28 is a prediction, not an observation.
- **I did not verify the 26 passing HARD checks.** They passed in both the failing full run and the
  smoke and lie outside the diff; runs 8–10 traced them. If R11-01/R11-02 are fixed by a change that
  reaches beyond the exemption branch, that reliance lapses.
- **I did not re-derive the parent gates, the unit pin, the selection check or the controls.**
  Untouched by the diff; `controls.json`, `parent_gate_parity.json`, `selection_check.json`,
  `unit_pin.json`, `golden_traces.json` were read only for hash/provenance comparison.
- **I did not audit the 840 sizing-suppressed cells.** Booked at run 9 (R9-04) and unchanged here; I
  verified only that the bucket reconciles and that my recompute of `log_R` from `(p, W, L)` picks
  out exactly that set.
- **I did not check whether the exempt cells are the same set at 25 symbols post-fix.** Cell
  membership is data-determined and nothing upstream changed, so I expect the same 34; I verified
  the classification logic, not the regeneration.
- **I did not quantify any finding's effect on any result.** There is no authorised run, and that is
  the data-analyst's object.

---

## QA run 12 — 2026-07-30T00:01Z — mode: subagent — HEAD 1979b93 (dirty: SPDR-019/design.md, SPDR-019/qa-review.md, SPDR-019/screen_code/{integrity,metrics,run_screen}.py; SPDR-019/results/* and SPDR-020/results/* untracked)

Verdict: **APPROVE**

**Execution authorisation: YES** — for the full 25-symbol phase-(a) re-run.

Subject: closure of the three run-11 blocking findings (**R11-01** the fix missed the
derived/interaction construction path; **R11-02** the checker derived undefinedness from the very
`log_R` field the remedy blanks; **R11-03** condition (i) was vacuous on interaction rows), and the
remediation carried by the three-file `screen_code/` diff plus AMENDMENT-20 clauses (c) and (d).

**Reviewed state.** `HEAD 1979b93648c41fad74458b86a3bb96bff2244012`, nothing committed.
`git diff` scope is exactly four files: `design.md` (+79/−17 across the §12 row and the amendment
ledger), `screen_code/integrity.py` (one hunk in `check_block_rule` plus one import plus the
`degenerate_reason_required` string), `screen_code/metrics.py` (**pure insertion**, +31/−0: the new
`log_R_is_defined` and the `ci_absent_reason` block), `screen_code/run_screen.py` (+12/−2 inside
`_add_interaction_rows`), and `qa-review.md`. `qa-review.md`'s diff is a **single append hunk**
(`@@ -4353,0 +4354,676 @@`), so runs 1–11 are byte-identical; this section is appended below run 11
and nothing above it is touched.

**Independence.** Fresh subagent context. I authored none of the design, none of the
implementation, and none of runs 1–11. Read in full before touching code: runs 10 and 11, the whole
`git diff`, `metrics.py:52-120` and `:340-425`, `integrity.py:492-610`, `run_screen.py:320-486` and
`:750-775`, `golden.py`, `config.py:129-200`, `design.md` §4.3, §12's row set and the AMENDMENT
ledger. **Read-only:** every injection below is an in-memory patch or a synthetic frame;
`git diff HEAD -- python/experiments/SPDR-019/screen_code/` is unchanged by this review and I did
not re-run the screen at any scale.

---

### PART A — the three run-11 findings, closed by injection

Every row is an executed result. `held` is the `min/max envelope over blocks x seeds` clause of
`BLOCK RULE` — the clause AMENDMENT-20 amends — driven by `integrity.check_block_rule` called
directly, with one healthy CI-carrying control row present so the 15-entry battery clause is
satisfied and the exemption logic is the only discriminator.

| Finding | Status | Evidence I produced |
|---|---|---|
| **R11-01** — the fix missed the derived/interaction construction path; one unclassified cell survived it and `BLOCK RULE` would HARD-fail again | **CLOSED — CONFIRMED on live data and by injection** | Remedied on the **other** axis from the one run 11 predicted: instead of teaching `_extra` to emit a token, `run_screen.py:434-442` refuses to **build** the term. Verified three ways. (1) **Live:** the 6-symbol smoke in `results/` (provenance below) emits **77** interaction rows, **all 77 carrying a CI**, and the offending `1000BONKUSDT / M15 / δ=1.0 / DESIGN` cell is **absent**; I independently enumerated every `(clock, δ, scope, band)` key with all four arms present and an arm whose own `log R` is undefined — there is exactly **one**, that key, and it is exactly the one with no interaction row. No key with an undefined arm produced a row. (2) **Full-scale replay:** over the preserved failing frame the rule drops **1 of 312** interaction rows, the one with no CI, and keeps all **311** that carry one. (3) **Injection:** a derived row reaching `check_block_rule` without a CI is unclassified and fails in **all four** shapes I could construct — token `LOG_R_UNDEFINED` with NaN `p`/`W`/`L`; token `N_DATES_LT_2_NO_DAY_BLOCK` with a genuinely true `n_dates = 1`; token `LOG_R_UNDEFINED` with finite one-sided `p`/`W`/`L`; and with a non-empty battery so it falls to the final `else`. `integrity.py:566-567` sets `admissible = {}` for `DERIVED_VARIANTS`, so **no** token can rescue a derived row. |
| **R11-02** — integrity's re-derivation of `LOG_R_UNDEFINED` was vacuous: it read the field `metrics.py:409` blanks, so the token could never be rejected | **CLOSED — CONFIRMED by injection in both directions** | `metrics.log_R_is_defined:111-121` is now the single predicate and `integrity.py:558-560` calls it on the row's **own `p`/`W`/`L`**. **Run-11 case H — the exact defect — now FAILS:** a cell with `n_dates = 47`, finite `p`/`W`/`L`, an empty battery and `log_R` blanked, claiming `LOG_R_UNDEFINED`, gives `held False`, `unclassified 1` (run 11: `held True`, exempt 1). **I reverted the fix in memory** — recompiled `integrity.py` with `log_r_undefined` read back off the `log_R` field — and the same row returns `held True`, exempt 1: the defect is reproducible and the fix is what removes it. The emitted audit field is no longer constant-True: in the live smoke's 31 exempt cells `log_R_undefined` reads **26 True / 5 False** and `n_dates_lt_2` reads **17 True / 14 False**, so both booleans now carry information. On the real 13,376-row post-fix frame, forcing every exemption to claim `LOG_R_UNDEFINED` leaves **5 unclassified** — precisely the 5 cells whose `p`/`W`/`L` are defined — so a false claim of that token is now detected on real data. |
| **R11-03** — `LOG_R_UNDEFINED` was the wrong condition for the interaction cell, and asserting it there would widen the exemption to all 311 interaction rows | **CLOSED — the design took QA's recommended option, and the widening is structurally impossible** | AMENDMENT-20(c) adopts **exclusion-before-scoring**, which is what run 11 recommended, rather than booking a third exemption token. Two independent barriers now exist and I tested both: the term is not built (PART A row 1), and even if one appeared, `DERIVED_VARIANTS` is barred from the exemption path entirely, so the 311-row widening cannot occur by construction — no token is admissible for a derived row regardless of what its `p`/`W`/`L` say. I confirmed the premise the amendment rests on: **all 312** interaction rows in the failing run carry `p = W = L = NaN`, including 310 with healthy CIs and `n` up to 1,090, so definedness genuinely is vacuous on that row type. |

**Fault matrix, in full** (one injected no-CI row + one healthy control; `held` is the envelope clause):

| # | Injected row | held | exempt | unclassified |
|---|---|---|---|---|
| 0 | control — every cell carries a CI | True | 0 | 0 |
| A | `n_dates = 1`, `p`/`W`/`L` finite, claims `N_DATES_LT_2` (true) | True | 1 | 0 |
| B | `p = 1` ⇒ `L` undefined, claims `LOG_R_UNDEFINED` (true) | True | 1 | 0 |
| C | **wrong token** — `n_dates = 8`, `p`/`W`/`L` finite, claims `N_DATES_LT_2` | **False** | 0 | **1** |
| D | **missing token** — `ci_absent_reason = None` | **False** | 0 | **1** |
| E | **bogus token** — `"BANANA"` | **False** | 0 | **1** |
| F | **key absent entirely** | **False** | 0 | **1** |
| G | run-11 case G — `n_dates = 47`, `log_R` **finite**, claims `LOG_R_UNDEFINED` | **False** | 0 | **1** |
| H | **run-11 case H** — `n_dates = 47`, `p`/`W`/`L` finite, `log_R` **blanked**, empty battery, claims `LOG_R_UNDEFINED` | **False** ✅ | 0 | **1** |
| H′ | case H against a **reverted** checker (reads the blanked `log_R`) | True ⚠ | 1 | 0 |
| I | both conditions true, claims `LOG_R_UNDEFINED` | True | 1 | 0 |
| J | both conditions true, claims `N_DATES_LT_2` (**swapped**) | True | 1 | 0 |
| K | **derived** row, no CI, NaN `p`/`W`/`L`, claims `LOG_R_UNDEFINED` | **False** | 0 | **1** |
| L | **derived** row, no CI, claims `N_DATES_LT_2` with a genuinely true `n_dates = 1` | **False** | 0 | **1** |
| M | **derived** row, no CI, finite one-sided `p`/`W`/`L`, claims `LOG_R_UNDEFINED` | **False** | 0 | **1** |
| N | **derived** row, no CI, **non-empty** battery (falls to the final `else`) | **False** | 0 | **1** |
| O | `p = 0` ⇒ `W` undefined, `n_dates = 30`, claims `LOG_R_UNDEFINED` (true) | True | 1 | 0 |
| P | `W = 0` exactly, claims `LOG_R_UNDEFINED` (true — `log(0/L)` is `−inf`) | True | 1 | 0 |
| Q | `n_dates` non-numeric `"many"`, `p`/`W`/`L` finite, claims `N_DATES_LT_2` | **False** | 0 | **1** |

**On the real 13,376-row post-fix frame** (buckets recomputed each time):

| Injection | held | exempt | unclassified | reconciles |
|---|---|---|---|---|
| clean | **True** | 33 | 0 | 13,376 = row count |
| swap every exemption token | **False** | 13 | **20** | yes |
| drop every exemption token | **False** | 0 | **33** | yes |
| forge `"BANANA"` on every exemption | **False** | 0 | **33** | yes |
| force every exemption to claim `LOG_R_UNDEFINED` | **False** | 28 | **5** | yes |

The developer's fail-ability numbers (20 on a swap, 33 on a drop) **reproduce exactly**. So does the
bucket reconciliation: **12,503 carrying a CI + 840 sizing-suppressed + 33 exempt (28
`LOG_R_UNDEFINED` + 5 `N_DATES_LT_2_NO_DAY_BLOCK`) + 0 unclassified = 13,376**, and the envelope
clause `held True` with `min_observed = max_observed = expected_per_cell = 15`.

*Replay fidelity note.* The preserved artifact is a parquet, so three columns must be restored to
their live in-process shape before `check_block_rule` sees them: `per_seed_ci` is stored as a JSON
**string** (`list("[]")` yields a 2-element list and silently mis-routes every exempt cell to the
final `else`), and `log_R_suppressed_reason` materialises as **NaN** rather than absent (NaN is
truthy, which mis-routes all 33 exempt cells into the sizing bucket). I verified against
`run_screen.py:271` and `integrity.py:712` that the live call receives in-process dicts in which
that key is genuinely absent on non-sizing rows, so neither is a code defect — but both are traps
for anyone auditing from the parquet, and both silently produce a *wrong* bucket split rather than
an error. Recorded for the data-analyst.

---

### PART B — did any measured quantity move? (item 2)

Verified against the preserved failing artifacts at
`…/scratchpad/spdr019_fullrun_FAILING/metrics_by_cell.parquet` (13,377 rows).

| Claim under test | What I found | Verdict |
|---|---|---|
| the 12,503 CI-carrying cells are arithmetically identical | joined pre- and post-fix on `(variant_id, clock, delta, scope, band)`: **12,503 pre, 12,503 post, 12,503 joined**, and across `n, mean, p, W, L, n_pos, n_neg, n_dates, W_L, p_be, p_be_net, identity_residual_bps, mean_signed_rows, log_R, ci_low, ci_high, ci_width, block_mde` every column returns **max \|Δ\| = 0.0 with 0 finiteness flips** | CONFIRMED |
| exactly 5 `log_R` values are blanked | 12,508 finite `log_R` pre-fix, 12,503 carrying a CI, **5** rows finite-`log_R`-with-no-CI: `BLURUSDT / L1_SHAT_RANK_CONTINUOUS / M15 / {0.25, 0.50} / DESIGN` and `1000BONKUSDT / L2_JOINT_HMM_HIGH_AND_K12_HIGH / H1 / {0.25, 0.50, 1.00} / DESIGN`, **all five `n_dates = 1`** with `p`/`W`/`L` finite. The emitter-exact simulation blanks **5** and no others | CONFIRMED |
| exactly 1 ineligible derived row is dropped | 13,377 → **13,376**; the dropped row is `1000BONKUSDT / M15 / δ=1.0 / DESIGN`, `had_ci = False`, offending arm `L2_JOINT_HMM_HIGH_AND_K12_HIGH` with `n = 1, p = 1.0, L = NaN` | CONFIRMED |
| the new predicate agrees with the estimand's own | `log_R_is_defined(p, W, L)` vs `isfinite(log_R_from_pWL(p, W, L))` on all **13,377** rows: **0 mismatches**. So the shared predicate is not a second, subtly different rule | CONFIRMED |
| the blanking cannot reach `layer_deltas` | all 5 blanked rows are `band = DESIGN`; `_layer_deltas` (`run_screen.py:489`) is TRAIN-only, and the smoke's `layer_deltas.parquet` carries `bands = ['TRAIN']` only. **Zero contact**, confirming run 11's PART C by a different route | CONFIRMED |
| nothing asserts an expected interaction-row count that a drop would break | `DERIVED_VARIANTS` is excluded from the cell-count estimate (`run_screen.py:762`) and appears in no HARD check other than the new `integrity.py:566` bar; no `selfcheck`/`selection` clause references the interaction variant; §12 and §9 impose no interaction-coverage requirement | CONFIRMED |
| the dropped row could not have armed anything | its `ci_low` is NaN, so it entered no `ci_low > 0` read, no `mirror_band` other than the CI-relative default, and no homogeneity pool | CONFIRMED |

**Answer: nothing measured moved.** The only value changes in the entire remediation are 5 `log_R`
fields set to null on cells that ship no interval, and one derived row that ships no interval being
removed from the frame.

---

### PART C — the live 6-symbol smoke, verified rather than accepted

`results/` holds a 6-symbol run at `n_boot 200, jobs 4`, and I checked its provenance before using
it: `selfcheck._sha256_tree(screen_code)` recomputes to
`fd56d6ce079002f6f4ebcdecba03f6c4ffa732107a34176c915db2c961c53de6`, **byte-identical to the
`code_sha256` in `integrity_selfcheck.json`**, so the smoke provably ran the code now on disk.

| Reported | Verified |
|---|---|
| 28/28 HARD checks pass | `all_hard_pass true`, `hard_fail_names []`, `n_hard_checks 28 = expected_hard_checks 28`; I listed all 28 by name and every one reads `held true`, including `BLOCK RULE`, `log R never unaccompanied` and `golden traces` |
| symbols cover the four that caused the failures, plus BTC/ETH | scopes = `1000BONKUSDT, 1000RATSUSDT, BLURUSDT, BTCUSDT, ETHUSDT, PYTHUSDT` (+ POOLED). All four affected symbols present — the coverage gap run 11 recorded as R11-05 is **closed** |
| buckets reconcile to the row count, 0 unclassified | 3,307 with a CI + 31 exempt + 228 sizing + **0** unclassified = **3,566 = `n_metric_rows`** |
| both exemption tokens exercised, 26 undefined / 5 single-day | `Counter({'LOG_R_UNDEFINED': 26, 'N_DATES_LT_2_NO_DAY_BLOCK': 5})`, and `ci_absent_reason` in the parquet reads `{NaN: 3535, LOG_R_UNDEFINED: 26, N_DATES_LT_2_NO_DAY_BLOCK: 5}` |
| 0 unaccompanied `log R` | finite `log_R` with no CI: **0** of 3,566. The suppression path **fired** this time (unlike the 2-symbol smoke run 11 criticised) |
| the previously-failing interaction cell absent | 77 interaction rows, all with a CI; the `1000BONKUSDT / M15 / δ=1.0 / DESIGN` cell is not present; and it is the **only** key in the whole emission with all four arms present and an undefined arm |

**On the 4-symbol run that failed only `golden traces`:** the reading is **correct in substance, with
a correction to the detail.** G1 is pinned to `BTCUSDT H1 DESIGN` (`golden.py:29-30`), G2 to
`ETHUSDT H1 DESIGN` (`:83`), and G6 to "the G1 symbol" (`:164`) — those three go `MISSING` when
neither symbol is in the run, which fails the check. **G3 is not pinned** — it is "first SUPPRESSED
signal **any symbol** H1 DESIGN" (`:102-103`) — so the stated reason "G1–G3 are pinned to
BTCUSDT/ETHUSDT" over-attributes by one trace and under-attributes G6. The conclusion stands: that
failure is an absent anchor, not a defect, and it cannot occur on a 25-symbol run that contains both
symbols. Incidentally that run also exercised the `anchor_fallback` branch
(`run_screen.py:964-972`) which run 10 recorded as the one unexercised path in the R9-10 fix.

---

### PART D — design-to-code fidelity on the amended clauses

Expected behaviour derived from the amended design text first, then read against the code.

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| AMENDMENT-20(d) / §12: "`log R` counts as defined iff `p`, `W`, `L` are finite with `0 < p < 1`, `W > 0`, `L > 0`" | `metrics.log_R_is_defined:111-121` | MATCHES | literal transcription; and it agrees with `log_R_from_pWL:74-78` on all 13,377 real rows |
| AMENDMENT-20(d): "both the emitter and the checker use that one predicate" | emitter `metrics.py:412`; checker `integrity.py:558-560`; eligibility `run_screen.py:438-440` | MATCHES | one function, three call sites, no duplicated inline predicate anywhere (grepped) |
| AMENDMENT-20(d): undefinedness "NEVER FROM THE EMITTED `log R`" | `integrity.py:558-560` | MATCHES | no read of `row["log_R"]` remains anywhere in the exemption branch; case H fails, case H′ (reverted) passes |
| AMENDMENT-20(c): "requires all four input arms (`L0`, shock, k12, joint) to carry a DEFINED `log R`, tested on each arm's own `p`, `W`, `L`" | `run_screen.py:424-442` | MATCHES | all four arm ids enumerated; the test reads `src["p"]/["W"]/["L"]` from the arm's own `cell_metrics` row at the same `(clock, δ, scope, band)` key |
| AMENDMENT-20(c): the term is "NOT BUILT rather than built and then exempted" | `run_screen.py:441-442` `arms = {}; break` before `_arm_arrays` and before `paired_combo_ci` | MATCHES | the break precedes both the array fetch and the bootstrap, so no work and no row |
| AMENDMENT-20(c): "on the failing run this drops EXACTLY ONE row of 312 … and keeps all 311 that carry a CI" | — | MATCHES, **recomputed** | 312 interaction rows; dropped 1; kept 311; the dropped one is the only one without a CI |
| AMENDMENT-20(c): "A derived row appearing without a CI is UNCLASSIFIED and fails" | `integrity.py:566-567` (`admissible = {}`) and the final `else` at `:583-585` | MATCHES | both routes verified by injection (K/L/M via the empty-battery branch, N via the final `else`) |
| §12 row: four buckets reconcile to the row count; `unclassified` is a hard failure | `integrity.py:526-587`, `deg_ok` at `:587` | MATCHES | reconciles exactly at both scales (13,376 and 3,566); `unclassified` drives `held False` in 11 injected shapes |
| §12 row: the condition is "validated against that cell's own emitted `p`, `W`, `L`, `n`, `n_dates`" | `integrity.py:558-561`, audit fields at `:574-578` | MATCHES | `p`/`W`/`L` now **used**, not merely emitted; `n` is still emitted-only, which is what the clause says (`n` is not part of either condition) |
| §12 row: "`n_dates < 7` is **not** an exempting condition" | old branch deleted; `degenerate_reason_required` restated at `:606-609` | MATCHES | no residual `n_dates < 7` in `screen_code/` (grepped); `BOOT_BLOCKS_DAYS` now used only by clauses 2 and 3 |
| §12 row text ↔ AMENDMENT-20 body | `design.md:1088` vs `:1339-1394` | MATCHES | the §12 row carries clauses (c) and (d) verbatim in substance; the definedness predicate is stated identically in both places |
| Ledger: 5 looser / 9 tighter / 6 neutral; active 4 / 8 / 6 | `design.md:1397-1399` | MATCHES, **recounted from the DIRECTION lines** | LOOSER = 1, 2, 7, 10, 20 (5); TIGHTER = 3, 4, 8, 11, 13, 15, 16, 17, 18 (9); NEUTRAL = 5, 6, 9, 12, 14, 19 (6); total 20. Supersessions −7 by −17 and −11 by −15 → 18 = 4 / 8 / 6 |
| L-23: LOOSER note lists four and is flagged at the gate | `design.md:1405-1406` | MATCHES | AMENDMENT-1, -2, -10, -20 named; flag present |
| L-23 clause 3: streak flagged, and the break disclosed | `design.md:1400-1404` | MATCHES | the five-row TIGHTER streak in 12–18 stands as history and AMENDMENT-20 is stated to break monotonicity. Honest — the easy move would have been to delete the streak note |
| `check_no_local_accounting("SPDR-019/screen_code")` | executed | PASSES | `{'ok': True, 'banned_defs_found': []}` |
| Spread disclosure (chapter 05) | `config.py:192-194` | INTACT | `UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps: None`, `PARTIAL_FEES_FUNDING_ONLY`; the diff does not touch cost |
| Hard-check count | `config.py:288-289` | UNCHANGED | `EXPECTED_HARD_CHECK_COUNT = 28` with an assert against `HARD_CHECK_NAMES`; `config.py` is not in the diff. No check added, removed or renamed |
| Holdout / fence / causality / `BacktestNode` / XENA / registry | — | NO CONTACT | the diff touches none of these surfaces |

---

### PART E — the "not built" eligibility rule, judged on its merits (item 3)

**Is excluding a derived term whose input arm has an undefined `log R` the right call? Yes.** The
interaction estimand is `Δ log R(joint) − Δ log R(shock) − Δ log R(k12)` and
`paired_combo_ci:577-581` forms its point estimate as `combo({name: log_R_from_pWL(...)})` per arm.
If any arm's `log R` is non-finite the combination is non-finite as a matter of arithmetic, so
`paired_combo_ci` returns an empty battery and there is nothing to measure. Excluding is strictly
more honest than emitting a row and then excusing it: an exempted row still occupies the frame, is
still counted, and is a place a future thin-cell defect can hide — which is the criticism run 11
made and which the design's own assessment paragraph concedes.

**Is it correctly scoped to derived variants only? Yes, and I checked it two ways.** The rule lives
entirely inside `_add_interaction_rows` (`run_screen.py:434-442`), which is reached only for
`L2_INTERACTION_HMM_X_K12`; the 13,065 non-derived rows cannot be dropped by it. In the failing
frame **28 non-derived rows have an undefined `log R` and 0 of them carry a CI** — all 28 keep their
row, their `p`/`W`/`L` and their exemption, exactly as §12 requires. Separately, `integrity.py:566`
bars only `DERIVED_VARIANTS` from the exemption path, so no ordinary cell loses its exemption.

**Can it silently drop anything beyond the one known row at full scale? No — I enumerated rather
than inferred.** Across the 25-symbol frame, five arm-cells have an undefined `log R`: four
`L2_SHOCK_HMM` cells (`PYTHUSDT / H1 / {0.5, 1.0} / {TRAIN, CONFIRM}`) and one
`L2_JOINT_HMM_HIGH_AND_K12_HIGH` cell. At each of the four `PYTHUSDT` keys only **2 of 4** arm rows
exist, so the pre-existing `src is None` guard (`run_screen.py:431`) already excluded them and the
new rule changes nothing there. Only the `1000BONKUSDT` key has all four arms plus an undefined one,
and that is the single drop. The drop set is also **`n_boot`-invariant** — `p`, `W`, `L` are day-sum
aggregates independent of the bootstrap — so on a deterministic re-run over the same episode set the
expectation is exactly **311 interaction rows and 13,376 metric rows**. That is a hard, predeclared
number the operator and the data-analyst can check the re-run against.

**One residual the rule does not cover, and it needs an analyst note — R12-01.** The bar is drawn at
*definedness*, not at *intervallability*. Three interaction rows survive it while an input arm
carries **no CI at all**: `1000BONKUSDT / H1 / {0.25, 0.50, 1.00} / DESIGN`, whose `joint` arm has
`n = 2` over **1 calendar day** and is itself exempt under `N_DATES_LT_2_NO_DAY_BLOCK` with its
`log R` blanked by AMENDMENT-20(b). Because that arm's `p`/`W`/`L` are finite and two-sided
(`p = 0.5, W = 682.8, L = 433.1`), `log_R_is_defined` is True, the term is built, and
`paired_combo_ci` recomputes the arm's `log R` internally on the union day index — so a value the
design forbids shipping on its own row reappears, unlabelled, inside a derived point estimate. At
`n_boot 2000` one of the three reads **`ci_low = 0.0930 > 0`**, i.e. `ABOVE_THE_MIRROR`.
**Why this is not blocking, checked and not assumed:** §4.3's phase-(b) trigger reads
`Δ log R vs L0` or absolute `log R` **"in the phase-(a) emission on the primary read"**, and the
primary read is full TRAIN (AMENDMENT-1) — all three rows are `band = DESIGN`, and `layer_deltas`,
which carries the `Δ log R` read, is TRAIN-only by construction. The four TRAIN-band interaction
rows that do read `ci_low > 0` (ADAUSDT ×2, BNBUSDT, POOLED — all M15) are healthy: `n` 293–3,046
over 491–893 days, no arm without a CI. The three thin rows also **disclose their own thinness**:
`run_screen.py:473-474` copies the joint arm's `n`, so each ships `n = 2.0` on the row. So the
consequence is confined to a verification-band row that a reader can see is built on two episodes.
**Analyst note:** do not read `1000BONKUSDT / H1 / DESIGN` interaction rows as measured
interactions. **For `quant-designer`, post-gate:** the natural bar is "every input arm carries a
CI", which would also make the eligibility rule symmetric with §12's suppression rule; it drops
these 3 rows and nothing else at full scale (311 → 308).

---

### PART F — AMENDMENT-20's DIRECTION label, re-examined (item 4)

The amendment now contains a loosening (the exemption path) **and** two tightenings (the withdrawn
`n_dates < 7` reason; clause (c)'s not-built rule). Judgement: **the label is still honest, and the
ledger arithmetic and both L-23 flags are still correct.**

*Direction.* **LOOSER is right and remains the harder label to volunteer.** Read literally, the
pre-diff design authorised no exemption at all, so all 34 near-empty cells were hard failures and
this row creates the relief; that is a loosening whatever else is bundled with it. The DIRECTION
line refuses to net the tightening away — it says so in capitals — and quantifies it: **13**
non-sizing exempt cells at `n_dates` 2–4 were being exempted for a condition they do not have. I
recomputed that: the post-fix exempt histogram is `LOG_R_UNDEFINED` {1: 13, 2: 4, 3: 2, 4: 7, 8: 2}
and `N_DATES_LT_2` {1: 5}, so the 13 at `n_dates` 2–4 are exactly `4 + 2 + 7` and they now all carry
the correct narrower `LOG_R_UNDEFINED` justification rather than failing. The design's claim is
accurate.

*Ledger arithmetic.* Recounted from the DIRECTION lines, not from the summary text: 5 / 9 / 6 over
20 rows, and 4 / 8 / 6 over the 18 active after the two supersessions. Both match `design.md`
exactly. The L-23 LOOSER note correctly lists four (−1, −2, −10, −20). The streak note is retained
as history with an explicit statement that AMENDMENT-20 breaks monotonicity — the honest handling.
The `EXPECTED FALSE-QUALIFIER COUNT` line is `N/A — ZERO machine qualifiers`, consistent with
AMENDMENT-C7, and the §12 "No adequacy flag" row still asserts it.

*Two wording residuals, neither a direction error.*
- **R12-02 (LOW).** The DIRECTION line books only the first tightening. Clause (c) is the second and
  it changes the **row population** (13,377 → 13,376), while the DIRECTION line says "No cell's
  estimand, comparator or band changes" — true of every surviving cell, but silent on the removed
  one. Clause (c)'s body does disclose the drop and its exact size, so this is a ledger-line
  completeness gap, not a concealment; and the omitted component pushes the row *away* from LOOSER,
  so the label is if anything conservative.
- **R12-03 (LOW).** The parenthetical "(Of the 31 exempt cells, 18 genuinely have `n_dates = 1`;
  none has `n_dates >= 7`.)" describes the **pre-fix** 31-cell set. Post-fix the exempt set is 33
  and **2 of them have `n_dates = 8`** — the `1000RATSUSDT / L4_TARGET_A1_MOD` TRAIN and CONFIRM
  cells, which clause (a)(i) names explicitly as `LOG_R_UNDEFINED`. Internally consistent, but a
  reader could take "none has `n_dates >= 7`" as a property of the post-fix exempt set, which is
  false. Wording only.

---

### PART G — the known residual: a swapped token when both conditions hold (item 5)

**Acceptable. It does not need to be fixed before the run.** Stated plainly: for the 13 cells where
both exempting conditions are genuinely true, the checker will accept either token, so a cell could
record `N_DATES_LT_2_NO_DAY_BLOCK` where `LOG_R_UNDEFINED` is the more fundamental reason (or vice
versa). I judge this harmless on four grounds, each checked rather than argued:

1. **Both conditions are true**, so neither token is a false statement about the cell. The failure
   mode a false reason exists to catch — a cell exempted for something it does not have — is closed:
   swapping tokens on the real frame turns **20 of 33** exempt cells into unclassified failures, and
   the 13 that survive are exactly the both-true set.
2. **Both derived booleans ship on every exempt row** (`log_R_undefined`, `n_dates_lt_2`, plus
   `p`, `W`, `L`, `n`, `n_dates`, `claimed_reason` and the validated `reason`), and they are now
   informative rather than constant — the live smoke shows 26/5 and 17/14. Any reader can recover
   the true condition set regardless of which token was claimed.
3. **The emitter's order is deterministic and disclosed** (`metrics.py:412-416`: `LOG_R_UNDEFINED`
   first, then `N_DATES_LT_2`), so in practice a both-true cell always records `LOG_R_UNDEFINED`.
   The ambiguity is admissible in the checker but not produced by the emitter.
4. **No number depends on which token is recorded.** The token enters no estimand, band, comparator,
   gate or count other than the exempt/unclassified split, and both tokens land in the same bucket.

Tightening this — requiring the emitter's precedence order — would be a checker that tests the
emitter's implementation choice rather than the cell's property, which is the wrong direction for an
integrity check. I recommend leaving it, with the two booleans as the audit record.

---

### PART H — carried forward, not closed (item 6)

- **Evidence is still not from a full 25-symbol run since the fix.** The strongest live evidence is a
  **6-symbol** smoke at `n_boot 200` — a real improvement on run 11's 2-symbol/`n_boot 200` smoke,
  because it now contains all four symbols that produced the failures and it fires both exemption
  tokens and the suppression path. But scale-dependent behaviour is untested: the 25-symbol run
  scores ~13,376 cells at `n_boot 2000` (44 min previously), and my full-scale statements are
  **replays of the fixed logic over the preserved pre-fix frame**, not observations of a new run. The
  predeclared expectations to check the re-run against are: **13,376 metric rows, 311 interaction
  rows, 12,503 cells with a CI, 33 exempt (28 + 5), 840 sizing, 0 unclassified, 0 unaccompanied
  `log R`, 28/28 HARD**.
- **M15 detail-level verification.** Unchanged since run 9. Both clocks ran, M15 rows are present and
  in the L-51 subsets, and the eligibility rule fired on an M15 cell — but I checked no M15 fill, no
  M15 hold conversion and no M15 block behaviour individually. **M15 carries the primary read**
  (AMENDMENT-2). This remains the largest standing coverage gap in the review series and no smoke
  closes it.
- **SPDR-020's `screen_code/` has never been reviewed.** Unchanged and now more pressing: it shares
  `resolution_basis.py` and the resolution artifacts, it moved again during this review window
  (untracked `results/run_plan.json` and `results/shards/`), and `log_R_is_defined` is exactly the
  kind of shared-predicate correction a sibling implementation will *not* have received. **It needs
  its own QA run; do not infer its state from this one.**

---

### PART I — other findings (all non-blocking)

**R12-01 — INFORMATIVE / `quant-designer` (post-gate).** Eligibility is keyed to definedness, not to
intervallability; 3 DESIGN-band interaction rows are built on a joint arm of 2 episodes over 1
calendar day, one of them reading `ci_low > 0`. Cannot reach the phase-(b) trigger (DESIGN band;
`layer_deltas` is TRAIN-only) and the thinness is disclosed as `n = 2.0` on the row. Full analysis in
PART E. **Analyst note: do not read those three rows as measured interactions.**

**R12-02 — LOW / `quant-designer`.** AMENDMENT-20's DIRECTION line books one tightening component and
omits clause (c)'s, which changes the row population by one. PART F.

**R12-03 — LOW / `quant-designer`.** "none has `n_dates >= 7`" describes the pre-fix exempt set; two
post-fix exempt cells have `n_dates = 8`. PART F.

**R12-04 — LOW / `experiment-developer`.** `metrics.log_R_is_defined:119` accepts
`(int, float, np.floating)` but **not `np.integer`**, so it and `log_R_from_pWL` — which
AMENDMENT-20(d) says are one predicate — disagree on an integer-typed `W` or `L`
(`log_R_is_defined(0.5, np.int64(5), 6.0)` is `False` while `log_R_from_pWL` is finite). Consequence
if it ever fired: an interaction term silently not built, and an admissible `LOG_R_UNDEFINED` on a
defined cell. **Currently unreachable** — `metrics._agg:52-71` returns float64 throughout, and the
two predicates agree on all 13,377 real rows — so this is a robustness note on a newly-shared
predicate, not a live defect. Adding `np.integer` closes it.

**R12-05 — INFORMATIVE (pre-existing).** `cell_metrics:352-359` early-returns on `r.size == 0`
**before** `per_seed_ci` is set, so such a row is skipped by `check_block_rule`'s bucket loop
(`integrity.py:528`) and would break the four-bucket reconciliation **silently** rather than raising.
Not realised — reconciliation is exact at both scales — because `run_screen.py:336/340` skips empty
cells before scoring, so no empty row reaches the frame. Recorded because the reconciliation is now a
load-bearing HARD clause and its exhaustiveness rests on that upstream filter.

**R11-04 — upgraded from INFORMATIVE to MEDIUM, still non-blocking, routes to `quant-designer`.**
§12 requires the unaccompanied rule "asserted over `metrics_by_cell`, `layer_deltas` and the
resolution ladder alike"; `selfcheck.py:309-316` tests `metrics_df` only, keyed on a column literally
named `log_R`. Run 11 found no instances. **I found instances.** In the live smoke,
`layer_deltas.parquet` has **7 rows** with a non-finite `delta_log_R` and therefore no CI, on which
`log_R_L0` is **finite** — six `PYTHUSDT` and one `1000RATSUSDT / L4_TARGET_A1_MOD` (one of run 11's
three unclassified cells). Read literally, that is 7 violations of a HARD rule, currently invisible
because the check does not cover that artifact. Three things make this a **wording** defect rather
than a data defect, and none of them is the code: the 7 rows arise from layer arms whose `log R` is
undefined, a pre-existing shape untouched by this diff (all 5 blanked rows are DESIGN and
`_layer_deltas` is TRAIN-only, so the remedy has **zero** contact with this artifact); `log_R_L0` is
a **copy of another row's** value, and that row carries its own interval; and on the 1,168 healthy
rows the companions present describe the **delta**, not `log_R_L0`, so the literal rule is satisfied
there only by coincidence. **Required change is in `design.md`, not `screen_code/`:** state that the
companion requirement attaches to each artifact's own primary read (`delta_log_R` on `layer_deltas`),
and that `log_R_layer` / `log_R_L0` are carried context whose intervals live on their own rows —
then extend the check to that stated scope. **Why I am not blocking on it:** no emitted number is
wrong, the primary read and its interval are correctly paired on all 1,168 rows that have one, the
check that exists passes honestly on the artifact it names, and the 7 rows are visible in the
emission. **What the operator accepts by running first:** the §12 wording correction then happens
after measurement, which is the pattern run 11 rightly criticised in AMENDMENT-20 itself. It is a
one-paragraph clarification with no effect on any result, so booking it before the run is cheap and
strictly cleaner. My recommendation: book it now, run immediately after; do not hold the run for it
if the operator prefers.

---

### Checks independently verified clean

- All three run-11 blocking findings closed, each by fault injection on its own subject, including a
  reverted-code control (case H′) that reproduces the R11-02 defect.
- A derived row without a CI fails in all four constructible shapes; no token can rescue it.
- Wrong, missing, bogus and inapplicable exemption reasons are all rejected — 11 of 18 synthetic
  shapes and 4 of 4 real-frame injections drive `held False`.
- 12,503 CI-carrying cells bit-exact across 18 columns with zero finiteness flips; exactly 5 `log_R`
  blanked; exactly 1 derived row dropped; buckets reconcile at 13,376 and at 3,566.
- The eligibility rule enumerated at full scale: 1 drop, 0 measured cells lost, 0 non-derived rows
  reachable, drop set `n_boot`-invariant.
- Smoke provenance: `code_sha256` recomputes exactly to the code on disk; 28/28 HARD; all four
  affected symbols present; suppression path fired; both tokens issued; 0 unaccompanied `log R`; the
  offending interaction cell absent and it is the only such key.
- Amendment ledger recounted from the DIRECTION lines (5/9/6 total, 4/8/6 active); both L-23 flags
  present; the streak break volunteered.
- `check_no_local_accounting` green; spread disclosure intact; `EXPECTED_HARD_CHECK_COUNT = 28`
  unchanged with its assert; no check added, removed or renamed; no holdout, fence, causality,
  `BacktestNode`, XENA or registry surface touched.
- `qa-review.md` diff is a single append hunk — runs 1–11 byte-identical.
- Shared-code boundary: the only new shared symbol is `metrics.log_R_is_defined`, used at three sites
  inside `SPDR-019/screen_code/`; nothing was added to or changed in `python/src/xen`.

---

### FAILING_ARTIFACT / REQUIRED_SKILL

```
FAILING_ARTIFACT: none — no artifact fails, and no finding blocks execution.

REQUIRED_SKILL (before the run — RECOMMENDED, not required):
  quant-designer  -> R11-04 (correct §12's wording so the unaccompanied rule attaches to
                    each artifact's own primary read; 7 live instances on layer_deltas are
                    currently masked by the check's narrower scope). One paragraph, no
                    effect on any number. Cheaper to book now than after measurement.

REQUIRED_SKILL (post-gate, optional):
  quant-designer  -> R12-01 (consider raising the eligibility bar to "every input arm
                    carries a CI"; drops 3 DESIGN-band rows, nothing else)
                    R12-02, R12-03 (two ledger/wording corrections in AMENDMENT-20)
  experiment-developer -> R12-04 (add np.integer to log_R_is_defined's type test)
                    R11-04's second half (extend the check to the stated scope once the
                    design states it)
```

### Standing execution blockers

1. **DISCHARGED** — AMENDMENT-7 / registered-C6 departure (re-verified: AMENDMENT-17 restored the
   pre-declared trigger; `design.md:377-401`).
2. **DISCHARGED** — `reflection-inputs.md` §9, signed option B at `9d8832e`.
3. **STANDS (lane-wide, unchanged)** — the per-symbol spread pin. Does not block this measurement
   under AMENDMENT-C5; the disclosure block is intact and the code makes no money read.
4. **DISCHARGED** — run-9 blockers 4 and 5, run-8 blockers 4–6 (re-verified green where the diff
   touches them; `check_no_local_accounting` re-run).
5. **DISCHARGED — R11-01.** The surviving unclassified cell is gone, by exclusion at build time.
   Verified on live data, by full-scale replay, and by four injections.
6. **DISCHARGED — R11-02.** The checker rejects its own primary token when the token is false;
   reverting the fix reproduces the defect.
7. **DISCHARGED — R11-03.** The design chose exclusion-before-scoring, the option QA recommended, and
   the 311-row widening is structurally impossible.
8. **DISCHARGED — run-11 blocker 4.** A smoke covering all four affected symbols returns 28/28 with
   0 unclassified and 0 unaccompanied `log R`. Run 11's three re-authorisation conditions are all
   met.
9. **OPERATOR FLAGS AT THE GATE, not blockers** — L-23 requires two: LOOSER now stands at **4**
   active rows (AMENDMENT-1 full TRAIN, -2 M15, -10 hold grid, **-20 the no-CI exemption path**),
   and the five-row TIGHTER streak within AMENDMENTS 12–18 is now broken by -20. Both are declared
   at `design.md:1400-1406`. Plus, as this run's own contribution to what the operator should see
   before authorising: **R11-04's §12 wording correction is cheaper to book before the run than
   after**, and the re-run's numbers are predeclared above so a surprise is detectable.

---

**Execution authorisation: YES.**

The full 25-symbol phase-(a) screen is authorised from QA's side. All three findings that blocked run
11 are closed on executed evidence rather than on reading, including a reverted-code control that
reproduces the defect the fix removes. Nothing measured moved: the 12,503 cells that carry an
interval are bit-exact across 18 columns, exactly the 5 intended `log_R` values are blanked, and
exactly the 1 intended derived row is dropped — a row that carried no interval and could arm nothing.
The new eligibility rule is enumerated at full scale rather than assumed: it drops one row, it cannot
reach a non-derived cell, and its drop set does not depend on the bootstrap. And for the first time
in this series the runtime evidence covers the symbols that actually failed. Execution remains the
operator's gate; blocker 9 lists what to read at it.

---

### What I did not reach

- **I did not run the screen at any scale.** QA is read-only and a run would overwrite `results/`.
  My runtime evidence is `integrity.check_block_rule` invoked directly on synthetic frames and on the
  preserved 13,377-row frame, an in-memory revert of the fix, and static reads of the emitted
  6-symbol smoke whose code hash I recomputed. The 13,376 / 311 / 33 / 0 figures for the re-run are
  **predictions from a replay**, not observations.
- **I did not verify the 26 HARD checks outside the diff.** They passed in the live 6-symbol smoke
  and lie outside the three changed files; runs 8–10 traced them. That reliance lapses if a later
  change reaches beyond the exemption branch and the interaction builder.
- **I did not re-derive the estimand, the parent gates, the unit pin, the selection check or the
  controls.** All untouched by the diff. I read `controls.json`, `parent_gate_parity.json`,
  `selection_check.json`, `unit_pin.json` and `golden_traces.json` only for the 28-check roll-up and
  provenance.
- **I did not audit the 840 sizing-suppressed cells**, only that the bucket reconciles and that the
  emitter-exact replay leaves them untouched.
- **I did not exercise the `n_days < 2` failure mode of `paired_combo_ci`.** In principle a derived
  term with all four arms defined could still return an empty battery if the union day index has
  fewer than 2 days, which would land it unclassified and HARD-fail the run. I bounded rather than
  tested it: `L0_BASELINE`'s minimum `n_dates` across all 420 cells is **4**, and the union index is
  at least L0's own, so the path is unreachable on this data. It is data-determined, not guaranteed.
- **I did not confirm the 4-symbol run's reported outcome by executing it.** I confirmed the
  *mechanism* — G1/G2/G6's anchors are `BTCUSDT`/`ETHUSDT`/the-G1-symbol, G3 is symbol-agnostic — so
  the claim that only `golden traces` fails, and only for want of its anchors, is structurally sound
  but not independently observed.
- **I did not re-verify the M15 detail level or review SPDR-020's `screen_code/`.** Both carried
  forward in PART H, both still open.
- **I did not quantify any finding's effect on any result.** There is no authorised run yet, and that
  is the data-analyst's object.
