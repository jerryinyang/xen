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
