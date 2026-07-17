# INFR-015 — CLS-EPISODE Binder-Form Amendment (Overlap-Aware Stage-2 Blocks)

**Type:** INFR-class infrastructure (not a candidate-family experiment)  
**Status:** DESIGN — 2026-07-17  
**Lineage:** amends the **CLS-EPISODE class block** of the INFR-014 pin
(`bybit_pc_frozen_registry.json` sha256 `ac8a1eb6…`, operator-accepted 2026-07-17).
CLS-FILTER block **untouched** (byte-identical carry-over). ch03 pin `db87dc1a…` stays VOID.  
**Discipline:** iterated-calibration — INFR-014 was the one clean cycle; this is the
predeclared **binder-form switch**, new ID, new seed banks (design §5.3 step 5 of INFR-014).  
**Stop this session:** design + fresh-context QA · execution operator-gated.

---

## 1. One falsifiable question + mechanism

**Question.** Does replacing the CLS-EPISODE stage-2 estimator's independent-leg bootstrap
(`block_legs=1`) with an **episode-overlap-derived block bootstrap** restore per-cadence
e2e α̂ ≤ 5% AND no-search coverage ≤ 5% on fresh confirm banks — with every other form
constant unchanged?

```
MECHANISM: CLS-EPISODE null streams are episode objects (duration ~ truncated lognormal,
median 4h LOW / 1h HIGH, cap 48h) drawn on ONE shared path per candidate with sorted entries
(calibration_bybit.py:248-303). Long holds ⇒ episodes OVERLAP in time ⇒ leg P&Ls share path
segments ⇒ positive cross-leg correlation under the null. leg_studentized_bootstrap_t with
block_legs=1 assumes exchangeable legs ⇒ variance underestimated ⇒ LCB anti-conservative ⇒
false-certify rate inflated EVEN WITHOUT SEARCH. Fix must therefore change the RESAMPLING
UNIT to respect overlap (block ≥ effective episode horizon — overlapping-estimand rule),
not tighten α or n_boot (knob-twiddle prohibited).
DERIVED: estimand = e2e α̂ + no-search coverage per cadence (same events as INFR-014 §5.1);
         null = SAME make_episode_null_universe generator (unchanged, so the failure the fix
                targets is held fixed) on fresh seeds;
         horizon = synthetic TRAIN-fence banks only;
         test = design bank (bite + coverage disclosure) → confirm bank once, no optional
                stopping; single form change per cycle.
```

### 1.1 Diagnosis (grounded in INFR-014 confirm artifact — exact values)

`INFR-014/results/confirm_CLS-EPISODE.json`, seeds 93000/94000, n=200/cell:

| Cadence | no_search_cov | e2e α̂ | selection_inflation | failure_label |
|---|---:|---:|---:|---|
| low | **0.100** | 0.075 | **−0.025** | coverage_limited |
| high | **0.050** | 0.080 | **+0.030** | selection_unsafe |

- **Primary failure = base LCB coverage:** the no-search arm (no selection at all) already
  misses at 2× target on low. Search adds little (inflation −0.025/+0.030, within ±2·SE of 0).
- Contrast CLS-FILTER (short/fixed holds, less overlap): cov 0.035/0.065, α̂ 0.045/0.060.
- ⇒ the defect sits in the stage-2 estimator's independence assumption on episode-shaped
  streams, exactly where the class objects differ. A selection-side fix would be aimed at the
  secondary failure and is NOT taken.
- Disclosure: on HIGH cadence coverage_ok was true (0.050 at boundary) and the miss is carried
  by the selection channel (+0.030); the blocked LCB is still the mechanism-matched fix (wider
  stage-2 LCB shrinks false-certifies through both channels), but HIGH may remain NEAR-MISS —
  predeclared as a possible outcome, read per §7 bands.

---

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: N/A (infrastructure) — measured object = binder
    false-positive rate + LCB coverage on episode-class null universes; no live family P&L.
  measured conditioning event == traded entry event: N/A (synthetic CAL banks only).
  effect-splitting windows non-overlapping: DESIGN and CONFIRM banks on DISJOINT fresh seed
    ranges (§5); disjoint from ALL INFR-014 and chapter-03 banks; no design→confirm leakage.
```

---

## 3. The form change (the ONLY change)

| Item | INFR-014 (TERMINAL) | INFR-015 |
|---|---|---|
| Stage-2 estimator | `leg_studentized_bootstrap_t`, `block_legs=1` | same estimator family, **circular block bootstrap over time-ordered legs**, `block_legs = B(stream)` |
| Block rule `B(stream)` | — | `B = min( max(1, ceil( q90(episode_duration_h) / median(inter_entry_gap_h) )), max(1, floor(n_legs/4)) )` — computed deterministically per stream from its OWN trades table (entry/exit timestamps). **Estimators pinned:** q90 = `numpy.quantile(…, 0.9, method="linear")`; median = `numpy.median`; gaps from consecutive sorted EntryTime; single-leg or zero-gap stream ⇒ B=1 |
| Applied to | — | CLS-EPISODE only (both stage-2 gross α̂ event and net deployability field); CLS-FILTER keeps `block_legs=1` (its pin is frozen; not re-measured) |
| Everything else | — | **unchanged**: binder `two_stage_sample_split`; stage-1 `g_net`+`charge_costs=True`; embargo 0.20; fracs 0.50/0.25; n_boot 200; confidence 0.95; α 0.05; one_subset; Fork B (`held_out_escalation=False`); gate = point α̂ ≤ 0.05 ∧ cov ≤ 0.05 per cadence; α̂ event = stage-2 GROSS LCB > 0 on top-1; net separate deployability field |

**Why this is form, not a knob:** `B(stream)` is a deterministic function of the stream's own
timestamps derived from the overlap mechanism (block ≥ effective horizon), not a free scalar
fitted to any bank (F06 pattern: computed, never asserted). No α, n_boot, confidence, or
fraction moves. Rule frozen at QA; never adjusted after seed contact.

**No threshold invention:** freezable numbers remain only measured quantities (α̂, cov,
inflation, Wilson) plus the `B` rule TEXT above.

---

## 4. Null / plant generators — UNCHANGED

`make_episode_null_universe` reused byte-identical (fingerprint asserted equal to INFR-014's,
inverse of the §4.1 inequality assert — the target failure must be held fixed for the fix to
be attributable). `plant_episode` bite plant reused unchanged. n_cand 64; COST-STACK
`bybit_round_trip_cost_bps_v1`; `hold_hours = episode_duration_hours`.

---

## 5. Banks, seeds, discipline (n_null per CAL-FPR rule: SE ≈ 0.218/√n)

| Bank | Seeds (fresh — disjoint from 91k–94k, 951k/952k, all ch03) | n_null | SE(α̂)@0.05 | Role |
|---|---|---:|---:|---|
| DESIGN | low **95000**, high **96000** | 80 | ≈0.024 | coverage disclosure + bite; freeze `B` rule; **no knob fitting** |
| BITE (design-only) | low **953000**, high **954000** | — | — | plant select ≥0.5 / deplant survival ≤0.125 (same criteria as INFR-014) |
| CONFIRM | low **97000**, high **98000** | **200** | ≈0.0154 | binding α̂ + coverage; point-α̂ gate |

- Coverage arm MUST use confirm seed bases (INFR-014 Issue-9 regression test reused;
  hard assert `seed_bases == CONFIRM_SEEDS`).
- No optional stopping; incomplete bank ⇒ no pin amendment.
- One clean cycle: if this form also fails confirm ⇒ STOP, TERMINAL stands; next change =
  new design (candidate: episode-level resampling unit or generator realism), never a retune
  on this confirm data.

---

## 6. Controls (validity proofs)

```
CONTROL no-search-coverage:
  question answered: is the overlap-aware LCB itself calibrated (≤5% miss) absent selection?
  population: same null universes, stage-2 applied to a RANDOM candidate (no stage-1 search);
    DISJOINT decision path from the α̂ arm (no selection step) — B-1 satisfied: it can pass
    while α̂ fails (isolates selection inflation) or fail while search is fine (isolates LCB).
  bite/MDE: at n=200, SE≈0.0154 ⇒ detects cov 0.10 vs 0.05 at >3 SE (the INFR-014 low-cadence
    defect size is exactly the calibration target).
  non-vacuity: moves the LCB miss-rate numerator directly (sufficient statistic of the gate).
  expected outcome if H true: cov ≤ 0.05 both cadences; if H false: cov stays ≈0.10 on low.
  disclosure: selection_inflation = α̂ − cov reported per cadence.
  destroy form: N/A (no permutation in this arm).

CONTROL bite-plant (power):
  question answered: does the blocked estimator retain power to certify a REAL planted edge
    (fix must not buy coverage by killing all power)?
  population: BITE banks (953k/954k) with plant_episode stage-1-only edge; DISJOINT from null
    banks by seed and by construction (plants injected).
  bite/MDE: predeclared plant edge_bps grid as INFR-014 WP2; pass = stage-1 selects a plant
    with rate ≥0.5 AND stage-2 deplant survival ≤0.125.
  non-vacuity: plant moves stage-1 ranking AND stage-2 LCB numerator; blocking changes LCB
    width, so this directly prices the power cost of wider blocks.
  expected if H true: bite passes with wider (but finite) LCBs; if blocking is too destructive:
    select rate <0.5 ⇒ design_ok=False ⇒ Fork B TERMINAL, no confirm spend.
  disclosure: LCB width ratio (blocked/unblocked) on design bank, disclosure-only.
  destroy form: deplant on stage-2 band (P-C form, unchanged).

TRIPWIRE (integrity, HARD): seed-disjointness assert across {ch03, INFR-014, INFR-015} bank
  registries + coverage-arm seed assert (Issue-9 class). Not a P&L leak tripwire — no real
  price data or edge claim exists in this CAL; causal-leak tripwires N/A synthetic banks.
  Vacuity: the assert fails loudly on any seed reuse (it caught the Issue-9 class in QA run 3).
```

L-28 derangement: no permutation-based destroy arm in this CAL (deplant is band removal, not
permutation) — declared N/A with reason.

---

## 7. Interpretation bands (per cadence — no binaries)

```
BANDS (per cadence, CLS-EPISODE):
  CERTIFIED:      point α̂ ≤ 0.05 ∧ no_search_cov ≤ 0.05
  NEAR-MISS:      α̂ or cov in (0.05, 0.05+1·SE] — reported as boundary, still NOT certified
  FAIL_ALPHA:     α̂ > 0.05 (Wilson disclosed, never gated)
  FAIL_COVERAGE:  cov > 0.05 with α̂ ≤ 0.05
  UNPOWERED:      n < 200 (incomplete bank) — no reading, no pin
Verdict ∈ {DUAL_CERTIFY, LOW_ONLY_CERTIFY, HIGH_ONLY_CERTIFY, TERMINAL} — same lattice as pin.
POOLED (across cadences): disclosure-only.
```

## 8. Power statement

```
POWER: n=200/cell confirm ⇒ SE(α̂)≈0.0154 at p=0.05.
  Detectable vs 0.05 at ~2 SE: α̂ ≥ 0.081 (the INFR-014 failure sizes 0.075/0.080 sit at
    1.6–1.9 SE — a REPEAT failure of the same size may read NEAR-MISS, disclosed as such).
  UNPOWERED distinctions (predeclared): 0.05 vs 0.06 true rates; low-vs-high cadence α̂
    difference < 0.03. Neither may be read as a negative.
  Bite power: per INFR-014 WP2 plant grid (design bank, disclosure).
```

## 9. Golden trace (QA diffs before execution sign-off)

```
GOLDEN-TRACE (developer must not generate):
 G1 B-rule fixture: stream with episode durations [2,4,8,16] h (q90=13.6h) and entries every
    1h (median gap 1.0h) ⇒ B = ceil(13.6/1.0) = 14; with n_legs=40 cap floor(40/4)=10 ⇒ B=10.
    Hand-check both the uncapped and capped branch.
 G2 Degenerate stream: single leg ⇒ B = 1; implementation MUST route B==1 to the existing
    block_legs=1 code path (same RNG stream), so equality is bit-for-bit by construction —
    a reimplementation with tolerance does not satisfy G2.
 G1b Cap-degenerate fixture: n_legs=3 ⇒ cap term max(1, floor(3/4)) = 1 ⇒ B=1 (never 0).
 G3 Seed assert: attempt confirm-coverage run with seed_bases=(95000,96000) must raise
    IntegrityError (Issue-9 regression, now on 015 constants).
```

## 10. Integrity vs informative split

```
HARD (block): seed disjointness (banks registry-pinned); coverage-arm seed assert; fixed
  n_null / no optional stopping; generator fingerprint EQUALITY assert vs INFR-014;
  CLS-FILTER pin block byte-identical carry-over (verify green before + after);
  incomplete bank ⇒ no write.
INFORMATIVE (operator judges): α̂, cov, inflation, Wilson, LCB-width ratio, bite power
  curves, deployability rates. No auto-verdict thresholds beyond the predeclared CERTIFIED
  definition, which gates the PIN FIELD only — pin acceptance stays an operator gate.
```

## 11. Registry amendment (deliverable)

- Identity checks use `verify_bybit_registry` canonicalization (canonical sha `ac8a1eb6…`;
  raw-file sha differs) — "byte-identical CLS-FILTER" = identical canonical JSON block.
- Rewrite `bybit_pc_frozen_registry.json` (same path/schema v1): CLS-EPISODE block gets the
  amended `procedure` (block rule text + `block_legs: "episode_overlap_rule_v1"`), fresh seed
  fields, new `confirm_summary`; CLS-FILTER block **byte-identical**; `void_priors` +
  `pin_usage` unchanged; `superseded_pins`: append `ac8a1eb6…`.
- New sha256 recorded; `verify_bybit_registry` green; INFR-014 report/indexes NOT rewritten —
  supersession recorded here and in indexes only.
- Write policy: amend only if CLS-EPISODE reaches ≥1 certified cadence; on TERMINAL, pin
  `ac8a1eb6…` stands unchanged and this experiment reports TERMINAL-2.

## 12. Scope caps, N/A declarations

- N/A with reason: CONVERSION-PIN (no screen-effect→money conversion); SPREAD-SCALE-ROUTING
  (no verdict-bearing T1 read — synthetic banks; cost stack enters only via g_net, unchanged);
  L-22 spread leg (no SUPPORTED/tradability band exists in a CAL); holdout untouched;
  no family status transitions; no TEST reads; 0 slots.
- Complexity budget: 1 module change (`calibration_bybit.py` stage-2 estimator plumbing +
  `episode_overlap_rule_v1`), 1 test file extension, no new packages.
- L-24 battery/eligibility rules: N/A with reason — no battery-gated eligibility, no
  path-dependent exit selection, no derived tripwire thresholds, no TEST reads in this CAL;
  the only derived quantity is the B rule (§3), pinned above.
- AMENDMENT ledger (post-QA run 1):
  AMENDMENT-1: B-rule cap made degenerate-safe (min/max order pinned; B≥1 always) — DIRECTION: NEUTRAL
  AMENDMENT-2: q90/median estimators pinned (numpy linear-interpolation quantile) — DIRECTION: NEUTRAL
  AMENDMENT-3: G2 routes B==1 to legacy code path (bit-for-bit by construction); G1b added;
    HIGH-cadence selection-channel disclosure added; canonical-sha language pinned — DIRECTION: NEUTRAL
  running count: 0 looser / 0 tighter / 3 neutral.

## 13. Exit criteria

| Outcome | Action |
|---|---|
| design bank: bite FAIL or cov still ≈0.10 | Fork B TERMINAL — no confirm spend, no pin write |
| confirm: ≥1 cadence CERTIFIED | amend pin (§11) → operator sign-off gate |
| confirm: TERMINAL-2 | pin stands; next form change = new design (episode-level resampling unit or generator realism), operator chooses at checkpoint |

---

## 14. AMENDMENT-4 — derived n_legs_floor stage-2 domain guard (operator-directed, 2026-07-18)

```
AMENDMENT-4: add DERIVED n_legs_floor to CLS-EPISODE stage-2 (blocked estimator kept);
  floor derived on a FRESH design bank, frozen, confirmed on a FRESH confirm bank.
  DIRECTION: TIGHTER
  running count: 0 looser / 1 tighter / 3 neutral
```

**Authorization + deviation.** Operator approved TERMINAL-2 and directed this follow-up run
as an INFR-015 amendment (report §8), overriding §13's "new design" exit. Discipline
preserved: the spent 95k–98k banks are NEVER reused; this is a predeclared new cycle on
fresh seeds with one added form element.

### 14.1 Mechanism (targets the PROVEN defect)

TERMINAL-2 diagnosis: LOW false-certifies concentrate at top-1 n_legs<8 (pass 0.179 on 67
rows) where studentized bootstrap-t is fragile and blocking is inert (B=1). Fix: stage-2
refuses to certify below a leg-count domain floor (`lcb_g_leg_studentized(n_legs_floor=F*)`
— existing param; out-of-domain ⇒ pass_positive=False ⇒ counted as non-certify in α̂ AND
unavailable to live XENA). Block rule `episode_overlap_rule_v1` kept (SUPPORTED on HIGH).

### 14.2 Floor derivation rule (F06 pattern — computed, never asserted)

- Grid (predeclared): F ∈ {0, 4, 6, 8, 10, 12, 16, 20, 24, 32}.
- Run the A4 DESIGN bank ONCE (no per-floor reruns): no-search coverage + e2e α̂ with
  floor OFF, recording per-row `n_legs`; bite then runs with F* ON (power must survive
  the guard — QA run 4 Issue 14 clarification). Floor evaluation is deterministic post-hoc
  monotone filtering: under floor F a row false-certifies iff `gross_pass ∧ n_legs ≥ F`.
- **F\* = smallest F in grid** s.t. design cov(F) ≤ 0.05 AND design α̂(F) ≤ 0.05 on BOTH
  cadences. No such F ⇒ **TERMINAL-3, no confirm spend, no write**.
- Disclosure (informative): out-of-domain fraction per cadence at F*; if >0.5 on a cadence,
  flagged as domain-starved for the operator (certification would rarely be reachable live).
- F* frozen into the procedure dict before any confirm seed runs; never adjusted after.

### 14.3 Banks (fresh; disjoint from 91k–98k, 951k–954k, all ch03)

| Bank | Seeds | n_null | Role |
|---|---|---:|---|
| DESIGN-A4 | low **99000**, high **100000** | 80 | bite + cov/α̂ rows for floor curve; freeze F* |
| BITE-A4 | low **955000**, high **956000** | — | same criteria (select ≥0.5, survival ≤0.125) |
| CONFIRM-A4 | low **101000**, high **102000** | 200 | binding α̂ + cov with floor ON; point-α̂ gate |

No optional stopping; incomplete ⇒ no write; coverage arm hard-asserts CONFIRM-A4 bases.

### 14.4 Everything else unchanged

Binder/stage-1/embargo/fracs/n_boot/confidence/α/gate rule/α̂ event/write policy §11 all
verbatim from §3–§5. Generator byte-identical (fingerprint assert). Golden traces: G4a —
fixture rows (gross_pass, n_legs) ∈ {(T,4),(T,8),(F,50),(T,20)} under F=8 ⇒ α̂ numerator
counts rows 2 and 4 only; G4b — confirm procedure missing `n_legs_floor` ⇒ IntegrityError;
G4c — stage-2 result with n_legs < F* must carry pass_positive=False + out_of_calibration_domain=True.

### 14.5 Exit criteria (amended)

| Outcome | Action |
|---|---|
| No F in grid works on design bank | TERMINAL-3 — no confirm, no write; pin stands |
| Bite-A4 FAIL | TERMINAL-3 — Fork B, no confirm |
| Confirm-A4 ≥1 cadence CERTIFIED | amend pin per §11 → operator sign-off |
| Confirm-A4 fails | TERMINAL-3 — pin stands; NEXT paths (operator/checkpoint, each a NEW design): (a) episode-level resampling unit (resample episodes not leg-blocks); (b) LOW generator leg-starvation realism review (top-1 subsets too thin — n_cand/episode-density rework) |
