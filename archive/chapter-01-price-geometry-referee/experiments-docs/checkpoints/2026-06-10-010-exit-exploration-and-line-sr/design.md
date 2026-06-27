# Phase 010 — Exit Exploration, Line-S/R Science, and New-Universe Groundwork

**Checkpoint type:** Research phase design.
**Date finalized:** 2026-06-10.
**Status:** ACTIVE — operator approved 2026-06-10. Registry amendment (D0)
recorded 2026-06-10; EXP-039/EXP-040 scoped Stage 1 the same day. Gate
parameters (§8), the candidate exit family (§5/A1), and the Last-X grid are
operator-amendable **until the corresponding Stage-1 scope freeze**; frozen
thereafter.
**Candidate family:** `CF-AVWAP-001` (continued from Phases 004–009).
**Follows:** `2026-06-10-009-avwap-holdout-release` (COMPLETED —
HOLDOUT_INCONCLUSIVE, shot SPENT; Tier-C routing per Phase 008 design §9).

## 1. Provenance

Phase 009 spent the programme's single sanctioned holdout read on Package B
(EURUSD-4h, FH H\*=12 all_legs): HOLDOUT_INCONCLUSIVE — positive (+20.60 bps net)
but margin-insufficient at n=27. Consequences that bind this phase:

- **No second holdout read exists for any package, ever.** All Phase 008 TEST
  evidence is final and permanently non-upgradable.
- **EURUSD holdout is contaminated-by-disclosure** for EURUSD-4h event-level
  claims. BTCUSD/USTEC/XAUUSD holdouts remain sealed and verifiably unread.
- Routing follows Phase 008 design §9 Tier C: Stage-C branches and HYP-001.

Programme findings that shape this phase (all data-dependent design inputs,
recorded per the Phase 008 §7.4 convention):

- **Capture efficiency was the only lever that delivered** (Phase 008): the FH
  exit beat the band-target/trend-change (BTC) exit by +16.29 bps net on
  EURUSD-4h TEST; selectivity qualified nothing (EXP-035); instrument selection
  alone was demoted to necessary-but-not-sufficient (F02).
- **The BTC exit is two mechanisms in one rule** (EXP-031/033): a loss-cutter at
  short horizons, a trend-truncator at long horizons (4h X_exit ≈ −27 bps).
  Stable attribution crossovers: 5m H=3, 1h H=4. Any new exit must be read
  against this profile.
- **Tradability lives at 4h** (EXP-030/034): 1h is net-negative equal-weight
  under CONSERVATIVE costs (BTCUSD drag dominant); per-instrument, only
  EURUSD-4h passed strictly; USTEC-4h power-limited; 5m closed for this
  substrate. 1h FH grid max ≤ 0 on TRAIN (EXP-033) — FH alone cannot rescue 1h;
  a structurally different exit might.
- **Small-n bootstrap reads are anti-conservative without calibration** (R1.2,
  EXP-032): every binding one-shot read in this phase carries the matched-
  structure null calibration and margin.

**Operator decisions recorded 2026-06-10 (pre-design, with the pipeline):**
(1) HYP-001 runs as a parallel science track in this phase. (2) The new-asset
universe is the programme's confirmation path — existing-asset results are
accepted as TEST-capped; cTrader collection for the new universe starts now.
(3) Exit-screen domains: **4h primary, 1h secondary**; 5m retired as a primary
signal source (reserved for the later multi-timeframe phase). (4) The
multi-timeframe model (signal 4h / execution 5m–30m) is **deferred to Phase 011**,
conditional on this phase's exit verdict and gated on its own EXP-027-analog
method calibration for any new execution domain.

## 2. Objective

Three independent tracks:

1. **Track A — Exit exploration (`/EXIT-X`):** screen a registered family of
   structurally distinct exit rules on the unchanged AVWAP bounce-entry
   substrate, TRAIN-only, against the best validated exits (FH H\* and BTC),
   under the frozen cost model + financing. Qualifying exits get at most one
   one-shot TEST confirmation. The prize is a frozen, TEST-confirmed exit
   package to carry to the new-asset universe — not a holdout claim.
2. **Track B — HYP-001 mechanism science:** the direct S/R test of the AVWAP
   line itself, in the confound-free framing preserved since Phase 007 design
   §8: `P(bounce | approach to AVWAP)` vs matched non-AVWAP price levels.
   Mechanism knowledge that survives all strategy-form outcomes.
3. **Track C — New-universe groundwork (INFR-002):** cTrader 1-minute time-bar
   collection for the new instrument set, with the holdout policy declared at
   first touch. Collection and integrity validation only; **no analysis** this
   phase.

## 3. Track and gate structure

```
Tier 0 (desk, no runs, no EXP-ID)
  D0  Registry amendment (multiplicity-registry.md): Phase 010 batch, exit
      family E1–E5 registered with parameters, time-stop disposition recorded,
      all data-dependent design inputs (§1) listed.
        │
        ▼
Track A (exit exploration)                Track B (science)      Track C (infra)
  A1 = EXP-039  /EXIT-X TRAIN-only          B1 = EXP-040           INFR-002
       exit screen [DIAG-006, 0 slots]          HYP-001 direct       cTrader
        │                                       S/R test             collection
        ▼  GATE G1 (lenient, §8.1):             [0 slots,            (no EXP-ID;
        │  per domain, any exit beating         analysis set]        VAL-class
        │  both references on TRAIN with                             admission
        │  stability → Tier-B activation                             later)
        ▼
  A2 = EXP-041 (provisional)  /EXIT-X one-shot TEST confirmation
       [1 slot; ≤2 exits × declared instruments, Holm + R1.2 margins]
        │
        ▼  GATE G2 (strict, §8.2): margin-adjusted net CI_low > 0 on TEST
        │  (Holm across the declared family)
        ▼
  Consequence of a G2 pass: the exit package is FROZEN (hash-pinned) as the
  carry-forward candidate for (a) Phase 011 MTF work and (b) new-universe
  confirmation. NO holdout read exists or is implied.
```

- Tracks A, B, C are mutually independent and may run in parallel. Track B
  never gates Track A; Track C produces no analysis this phase.
- **TRAIN/TEST discipline:** EXP-039 reads TRAIN only (boundary = the R1.3
  1-minute-row timestamp convention, `train_end_ts`). EXP-041 evaluates frozen
  selections **once** on TEST. TEST at 4h is honestly degraded: EURUSD-4h and
  XAUUSD/USTEC-4h TEST strata were read by EXP-037/038 under FH and BTC exits.
  Stratum-level reads under *new* exit rules are fresh, but every TEST result
  in this phase carries the disclosure "TEST stratum previously read under
  FH/BTC exits in Phase 008" and is interpreted as variant-level confirmation,
  not independent out-of-sample evidence (the R1.7 lesson, applied in advance).

## 4. Scope discipline

**In scope:** D0 registry amendment; EXP-039 (TRAIN exit screen); EXP-040
(HYP-001 direct S/R test); EXP-041 (provisional one-shot TEST confirmation,
activated only by G1); INFR-002 (new-universe collection + integrity checks).

**Out of scope (carried, not worked):** holdout (none exists for this family);
multi-timeframe model (Phase 011, conditional); stop-style/intrabar exit fills
(deferred pending a fill-rule method validation — §7.6); Stage-C detector/anchor
branches (`/LB` `/MB` `/ATR` `/ANCHOR` — next family review if Track A is FLAT);
`/ALPHA` `/BAND` `/XTF` `/MA-DOMAIN`; any analysis of new-universe data; any
change to the frozen EXP-027 method, EXP-030 cost constants, or Phase 008
financing layer; any entry-signal modification.

## 5. Experiment specifications

### D0 — Registry amendment (Tier 0)

First Phase 010 artifact. Amends `docs/signal-registry/multiplicity-registry.md`:
opens the Phase 010 batch recording the Phase 009 close; registers EXP-039
(DIAG-006, 0 slots), EXP-040 (HYP-001 measurement, 0 slots), and reserves
EXP-041 (`/EXIT-X`, 1 slot, activation behind G1); registers the exit family
E1–E5 with exact parameters; records the time-stop disposition (§5/A1) and
every data-dependent input from §1; records INFR-002 and the new-universe
holdout declaration (§5/C1).

### A1 / EXP-039 — `/EXIT-X` TRAIN-only exit screen (DIAG-006, 0 slots)

- **Question (exploratory):** on the unchanged AVWAP bounce-entry substrate,
  does any registered candidate exit rule deliver TRAIN per-event **net**
  expectancy (frozen CONSERVATIVE costs + Phase 008 financing) that is positive
  and exceeds both reference exits, stably, on 4h (primary) or 1h (secondary)?
- **Instruments:** BTCUSD, EURUSD, USTEC, XAUUSD (descriptive per-instrument
  tables for all; the binding screen statistic is per-instrument net per
  domain — equal-weight pooling is reported but non-binding, per the EXP-030
  lesson that one high-cost instrument can veto a domain).
- **Reference exits (fixed):** R-BTC = the registered band-target/trend-change
  exit (HYP-004-R baseline); R-FH = FH(H\*) where eligible — 4h: H\*=12
  all_legs (EXP-037 freeze, hash-pinned); 1h: ineligible (EXP-033 grid max ≤ 0),
  so the 1h bar is R-BTC plus the positivity requirement.
- **Candidate exit family (registered; bar-close trigger and bar-close fill
  only — §7.6):**
  - **E1 — HA Harami size exhaustion:** exit on the global-techniques Pattern 1
    condition (`max(close_1,open_1) > max(close_0,open_0)` and
    `min(close_1,open_1) < min(close_0,open_0)`) on domain-bar HA values,
    direction-independent variant. No parameters.
  - **E2 — HA trailing reference:** exit when domain-bar real close crosses the
    HA trailing reference (long: `min(HAOpen, HAClose)` of the prior bar;
    short: `max(HAOpen, HAClose)`), bar-close market-style trigger (the
    stop-style variant stays deferred). No parameters.
  - **E3 — Last-X high/low trailing:** exit when real close crosses the prior-X
    domain bars' lowest low (long) / highest high (short).
    **X ∈ {3, 5, 8}** — the full grid is declared here; selection across X is
    mechanical (§5/A1 selection rule) and X counts against the family size in
    G1 stability checks.
  - **E4 — Adverse-band stop:** exit when real close crosses the opposite MAD
    band of the live anchored VWAP (the registered band definition,
    multiplier 1.0). No new parameters.
  - **E5 — Target-conditional time-stop:** the BTC exit's band-target rule kept,
    trend-change leg replaced by a hard time-stop at H_ts domain bars if no
    target hit; **H_ts ∈ {8, 12, 24}** declared. This is the only admissible
    time-stop form: the unconditional time-stop **is dropped** — it duplicates
    the FH exit already swept in EXP-033/037 (disposition recorded in D0).
  - Every exit composes with the unchanged entry/pyramid substrate under the
    **all_legs** pyramid policy (the Phase 008 frozen winner; policy variation
    is out of scope this phase).
- **Selection rule (mechanical, predeclared — adapted from R1.4):** per domain,
  a candidate exit (at one parameter point for E3/E5, chosen by the same rule
  within its declared grid) **qualifies on TRAIN** iff: (i) per-instrument net
  point estimate > 0 on the domain's surviving instruments (4h: EURUSD, USTEC,
  XAUUSD — BTCUSD excluded by the break-even map; 1h: EURUSD, USTEC, XAUUSD);
  (ii) net point estimate > the better reference exit's TRAIN net on the same
  events; (iii) split-half stability — both chronological TRAIN halves keep
  net > 0 and the sign of the reference gap. Ranking among qualifiers:
  max-min across split halves (worst-half net), smaller-complexity tie-break
  (fewer parameters, then shorter average holding time). **At most 2 exits
  per domain proceed to G1 consideration; at most 2 total enter EXP-041.**
- **Boundary containment (R1.5 analog):** the selection statistic is computed
  on the boundary-contained TRAIN subset (events whose exit under the
  longest-horizon candidate resolves at or before `train_end_ts`); spill counts
  disclosed.
- **Power statement (mandatory in scope.md):** 4h TRAIN holds ~90 events per
  instrument-set read (EXP-033 disclosure); selection on this base is fragile —
  hence the stability filter and the max-min rule. State per-cell minimal
  detectable nets from EXP-030/033 bootstrap dispersions before any read.
- **Hard no-promotion rule:** EXP-039 outputs characterisation and the frozen
  qualifying set only. No TEST or analysis-set verdict is read inside A1.

### A2 / EXP-041 (provisional) — `/EXIT-X` one-shot TEST confirmation (1 slot)

- Activates only on G1 qualification. Inputs frozen from EXP-039
  (`frozen_selection.json`, hash-pinned: exit rule(s), parameter point(s),
  per-domain instrument family) **before any TEST row is read**.
- **Declared TEST family (fixed before any TEST read):** the qualifying
  (exit × domain × instrument) cells, ≤2 exits total; all realized binding
  one-sided p-values form **one Holm family at α = 0.05** for the phase
  (R1.1 analog — EXP-041 is expected to be the only binding TEST reader this
  phase; if any other binding TEST read is added by amendment, it joins this
  family). Adjudication is mechanical, in a desk artifact
  `G2-gate-review.md` in this checkpoint directory; no experiment code
  declares a gate satisfied.
- **Small-n calibration (R1.2, mandatory per cell):** before the TEST read,
  synthetic-null calibration of the frozen EXP-027 bootstrap at the matched
  TEST cell structure (cluster sizes/direction labels from entry attributes;
  zero-mean Gaussian cluster model with TRAIN-estimated variance components;
  R = 2000 null replicates); binding bound rule `ci_low_1s > m_cell`,
  `m_cell = max(0, Q95 of null ci_low_1s)`, persisted before the freeze.
- **Recovery semantics (R1.6):** a halt after freeze but before any verdict
  artifact permits a rerun that must hash-reproduce the freeze or hard-stop;
  a run finding an existing verdict artifact refuses to recompute.
- **Disclosure:** every TEST cell carries the Phase 008 prior-read disclosure
  (§3) and the EURUSD cap note (§7.3).

### B1 / EXP-040 — HYP-001 direct S/R test (0 slots; mechanism science)

- **Hypothesis (HYP-001, open since Phase 004):** price reacts at the AVWAP
  line as support/resistance beyond what matched non-AVWAP price levels show.
- **Framing (inherited; confound-free per Phase 007 design §8 and the EXP-025
  post-mortem):** condition on **approaches** to the line, not on bounce
  triggers — `P(bounce-like reaction | approach to AVWAP within ε)` vs the same
  statistic at matched control levels (look-ahead-safe levels carrying no AVWAP
  information, e.g. price levels at matched distance/volatility offsets),
  with the approach definition computable strictly at or before the approach
  timestamp. The EXP-025 event-bar penetration metric is explicitly
  inadmissible (it conflates the trigger definition with the outcome).
- **Data:** full analysis set (first 70%), 1h and 4h domains, all four
  instruments. Gross, real-price reaction statistics — this is mechanism
  science, not tradability; no cost layer.
- **Inference:** matched-control contrast with the regime-cluster bootstrap +
  permutation machinery (EXP-021/027 family), Holm across the declared
  domain×instrument family. Stage 2 defines exact reaction metrics, ε, and the
  control-level construction; Stage 1 must predeclare the approach definition,
  denominators (approaches, not bars — duplicate-source rules stated), and a
  power statement.
- **Role:** never gates Track A. Its answer reweights priors for Phase 011 and
  the Stage-C family review (a NO closes the mechanistic story for line-S/R
  and reframes the edge as relative momentum around pivots).

### C1 / INFR-002 — New-universe data collection (infrastructure; no EXP-ID)

- **Instruments (new):** GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD,
  EURJPY, GBPJPY, AUDJPY; US500, US2000, DE30, JP225. (USTEC from the
  proposal's index list is already local and is not re-collected.)
- **Deliverables this phase:** 1-minute time-bar Parquet per instrument under
  `data/timebars/` via the existing cAlgo collector (`Mode=TimeBars`), plus a
  VAL-001-style temporal-integrity validation run before any experiment may
  admit the data (scoped as a VAL item when collection completes; not this
  phase's analysis).
- **Holdout declaration at first touch (binding from the moment each file
  lands):** the final 30% of each new instrument's chronologically ordered
  dataset is global holdout, sealed under the standard rules; the first 70%
  splits 70/30 TRAIN/TEST on the 1-minute-row timestamp convention. **No
  Phase 010 experiment reads any new-universe row.**
- **Strategic role (recorded):** the new universe is the programme's
  confirmation ground for TEST-capped existing-asset candidates. Confirmation
  design (which candidates, what gates, whether a new-universe holdout read is
  ever sanctioned) is a future phase's checkpoint, not this one.

## 6. Multiplicity & registry gate

No Phase 010 measurement is admissible until D0 lands. Slot accounting:
EXP-039 diagnostic (0), EXP-040 mechanism science (0), EXP-041 reserved (1,
consumed only on G1 activation). The exit family E1–E5, the E3/E5 parameter
grids, and the dropped unconditional time-stop are registered before any TRAIN
read. Negative, blocked, and inconclusive outcomes go to the file-drawer
ledger.

## 7. Methodological guardrails

1. The final 30% global holdout (all instruments, old and new) is excluded
   from all Phase 010 analysis. The new-universe data is excluded entirely.
2. **Cost model frozen** (EXP-030 CONSERVATIVE + Phase 008 financing:
   EURUSD 0.6 / USTEC 1.2 / XAUUSD 1.2 / BTCUSD 10.0 bps/day). A net-negative
   exit is never permission to revisit costs.
3. **EURUSD cap disclosure:** any EURUSD-4h result in this phase is permanently
   TEST-capped (holdout contaminated-by-disclosure; no read exists). Carried on
   every EURUSD artifact. The instruments worth a winner are XAUUSD-4h and
   USTEC-4h (sealed holdouts; usable in any future new-confirmation design)
   and the new universe.
4. **TRAIN-only selection via mechanical predeclared rules; TEST touched once**
   by the ≤2 frozen exits. No post-result recombination, no parameter-point
   reselection after any TEST read.
5. **HA values may trigger exits; fills are always real prices**
   (`RealClose`/time-matched at the domain bar close). Renko/HA construction
   prices never enter P&L. Synthetic-price discipline per the data layer.
6. **Bar-close fills only.** Stop-style/intrabar triggers (E2's deferred
   variant, any true stop-loss semantics) are out of scope until a dedicated
   method-validation experiment defines a conservative fill rule the EXP-027
   machinery can carry. Crossing detection uses domain-bar closes.
7. **Exit causality:** every exit condition is computable at the domain-bar
   close that triggers it, from data at or before that timestamp; exits
   evaluated per event with the same reportability conventions as EXP-030/037
   (ex-post reportability conditioning disclosed per F04).
8. **Two-speed gating:** G1 lenient (continue exploring), G2 strict (freeze a
   carry-forward package). Nothing closes on a wide CI; nothing is promoted on
   one.
9. **Honest expectation set:** 4h is the realistic carrier; the 1h secondary
   screen exists because a structurally different exit is the one untested
   lever there — a 1h wipe-out is an expected outcome, not failure. The FH
   bar on 4h is high (TRAIN grid max +45.79 bps); most candidates failing to
   beat it is the base case.

## 8. Gate specifications (predeclared; amendable only until the EXP-039 scope freeze)

### 8.1 G1 — exit qualification (lenient)

Per domain d, candidate exit E (at its mechanically selected parameter point)
qualifies iff ALL of:

- **(i) Positive:** per-instrument TRAIN net point estimate > 0 on every
  surviving instrument of d (4h and 1h: EURUSD, USTEC, XAUUSD).
- **(ii) Better:** pooled TRAIN net on d's surviving instruments exceeds the
  better reference (4h: max(R-FH, R-BTC); 1h: R-BTC) on the same events.
- **(iii) Stable:** chronological split-half of TRAIN — net > 0 and the
  reference gap keeps its sign in both halves.
- **(iv) Bounded family:** at most 2 exits total (across both domains) proceed;
  ranking by max-min worst-half net, then fewer parameters, then shorter
  average hold.

Nothing qualifies → Track A is FLAT; EXP-041 does not activate; its slot is
unused (ID reserved-inactive).

### 8.2 G2 — carry-forward freeze (strict)

A qualifying exit cell passes G2 iff, on its one-shot TEST read: phase-family
Holm-adjusted one-sided p ≤ 0.05 **and** `ci_low_1s > m_cell` (R1.2 margin).
Adjudicated once, mechanically, in `G2-gate-review.md`. Consequence: the exit
package (rule, parameters, instruments, domain) is frozen hash-pinned as the
carry-forward candidate for Phase 011 and new-universe confirmation. **No
holdout consequence exists.** A G2 fail leaves the Phase 008 Package-B/A
evidence as the family's standing record.

### 8.3 HYP-001 verdict classes (Track B)

EVIDENCE_FOR / EVIDENCE_AGAINST / INCONCLUSIVE per the Stage-2 plan's
predeclared contrast and Holm family. No gate consequence either way; the
verdict is a permanent mechanism record and a Phase 011 / family-review input.

## 9. Phase outcome criteria

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| EXIT_CONFIRMED | ≥1 exit passes G2 on TEST. | Frozen carry-forward exit package; Phase 011 (MTF) builds on it; new-universe confirmation design becomes the follow-up checkpoint. |
| EXIT_CHARACTERISED | G1 qualified ≥1 exit but nothing passed G2. | Exit landscape documented; Phase 011 proceeds on the Phase 008 frozen package (FH H\*=12 all_legs); family review with better priors. |
| EXIT_FLAT | Nothing qualifies at G1. | Capture-efficiency lever exhausted beyond FH on this substrate; Phase 011 decision (proceed on FH package vs Stage-C family review) is an operator call informed by HYP-001. |
| (orthogonal) HYP-001 verdict | §8.3 | Mechanism record; reweights Phase 011 / Stage-C priors. |
| (orthogonal) INFR-002 | Collection + integrity validation complete per instrument. | New-universe data admitted for future phases only after its VAL item passes. |

## 10. Non-goals

- Any holdout read (none exists for this family; new-universe holdouts are
  sealed at first touch).
- Entry-signal, anchor, detector, or band changes (Stage-C territory).
- Stop-style/intrabar fills or slippage-model changes.
- Pyramid-policy variation (all_legs frozen this phase).
- Cost or financing iteration after freeze.
- Any analysis of new-universe data, including "quick looks".
- Multi-timeframe execution work (Phase 011, conditional, behind its own
  method calibration).
- Re-running EXP-025's confounded HYP-001 metric.

## 11. Amendment log

### 2026-06-10 — pre-execution adversarial review (no TRAIN/analysis-set outcome read before any item)

1. **EXP-039 containment populations (deviation from §5/A1 as written):** the
   scope replaces the shared longest-horizon-candidate containment population
   with per-candidate containment plus reference-intersection populations for
   all gap statistics. Qualification criteria populations are pinned per
   criterion ((i) and the net>0 leg of (iii): own-contained; (ii) and the
   gap-sign leg of (iii): intersection).
2. **EXP-039 ranking population:** the §8.1(iv) ranking (and the ≤2 cap) is
   computed on the within-domain qualifier-intersection population so
   cross-candidate ranking is a same-events comparison; per-candidate numbers
   disclosed; any rank reversal between the two computations escalates to
   operator adjudication before the EXP-041 freeze.
3. **EXP-039 EURUSD-share disclosure:** the qualification table carries the
   EURUSD share of each pooled net and the ex-EURUSD pooled net (descriptive;
   G1 desk-review input — EURUSD evidence is permanently TEST-capped per §7.3).
4. **EXP-040 binding family (narrows §5/B1 as written):** Holm at α = 0.05
   over the **2 pooled domain contrasts only**; all per-instrument×domain
   cells are descriptive and never promoted. §8.3 defers to the Stage-2 plan,
   which now controls.
5. **EXP-040 immaterial-null symmetrized:** AGAINST-as-immaterial ⇔
   CI_high < +2 pp ∧ CI_low ≤ 0, regardless of the sign of Δ.
6. **EXP-040 power statement added (closes the §5/B1 Stage-1 requirement):**
   structural statement in scope.md plus an ordering-enforced realized
   `power_statement.csv` (counts-only, written before any contrast read).
7. **EXP-040 disclosures added:** censoring-sensitivity bracket (extreme
   imputation of unresolved episodes, non-binding) for the arms' asymmetric
   censoring mechanisms; moving-vs-static kinematic confound and the control
   arm's unmatched price-stretch regime carried as verbatim caveats; matching
   covariates pinned (entry direction, vol tercile, speed tercile;
   band-width tercile balance-reported, not a stratum key).

### 2026-06-11 — operator-directed addition (before any outcome read)

8. **EXP-040 secondary moving-copy control arm (descriptive):** a third arm
   of shifted **moving** copies `AVWAP(t) + δ·BW(t)` (identical δ
   construction, spawn grid, and lifetime as the frozen-horizontal arm; own
   fixed seed; |δ| ≥ 1.5 BW keeps copies clear of the line's neighborhoods by
   construction) is run through the identical detector and matching
   machinery. The AVWAP-vs-moving-copy contrast Δ_m is **descriptive only**
   (cluster-bootstrap CI; no permutation p, no Holm membership) — the binding
   family remains the 2 pooled static-control domain contrasts. Predeclared
   joint reading: Δ > 0 with Δ_m ≈ 0 → moving-level kinematics, not the
   line; Δ > 0 with Δ_m > 0 → line-specific S/R beyond both geometry and
   kinematics; Δ_m never produces or upgrades a verdict. The static arm
   carries the kinematic confound, the moving arm the band-family-geometry
   confound; the pair brackets the estimand (closes the residual of
   amendment 7's caveat).
