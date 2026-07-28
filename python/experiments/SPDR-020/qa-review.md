# SPDR-020 — QA review (append-only)

## QA run 1 — 2026-07-28T14:49:15Z — mode: subagent — HEAD c52993e679a18b28015b1a0dbed80ddaf51f26f7 (clean)

**Verdict: REVISE** (design-stage compliance review; `screen_code/` not yet written, which is the
expected state and is not a finding).

**Scope of this run.** Clause-by-clause check of `design.md` against
`.claude/skills/quant-designer/references/design-requirements.md`, `docs/references/spdr-lane.md`,
`docs/references/chapter-06-governance.md`, the knowledge base (L-21/28/50–53, P-21–25), the binding
upstream documents (reflection §2.0/§5.4/§5.4a/§5.9, `cf-voldir-001.md` C1/C2/C5/C6 + HYP-D7,
checkpoint-018 design, SoT §6.2/§6.3), and the parent object `SPDR-014`. All numeric claims were
re-derived from the emitted artifacts by this reviewer; none was taken on trust.

**Blocking summary.** Two CRITICAL findings, both provable from the design's own text and confirmed
against data: the primary (selective) grid and the powered grid are **disjoint** as specified, so the
experiment as written cannot produce a primary read; and the §8 power statement rests on a
mis-attributed population and a precision bar that no real cell in the parent's most-pooled emission
attains.

---

### Design-fidelity trace (design clause → binding source → verdict)

No code exists, so the trace is design-clause → binding upstream requirement.

| Design clause (§ref) | Binding source | Verdict | Notes |
|---|---|---|---|
| §1 `MECHANISM` / `DERIVED` | design-req §1 | **PRESENT, WEAK** | Blocks filled; but the mechanism that would put `R > 1` is asserted, not named — see H1 |
| §3 `OBJECT-IDENTITY` (3 clauses) | design-req §2 (B-8/B-4/B-9) | **MATCHES** | Breach-bar conditioning, three event types kept distinct, one open episode + suppression count — B-4 and B-9 correctly discharged |
| §6 `CONTROL MIRROR-NULL` | design-req §3 | MATCHES | Point-null; B-1 non-applicability argued explicitly and correctly |
| §6 `CONTROL ENTRY-TIMING DERANGEMENT` | design-req §3, L-28 | MATCHES | Derangement declared, ≥2000 seeds, plant curve, P-24 disclosure |
| §6 `CONTROL SIDE-DERANGEMENT` | design-req §3 | **DEVIATES** | 4 of 7 required clauses absent — H2 |
| §6 `CONTROL AMBIENT-BASE` | design-req §3 | **DEVIATES** | non-vacuity + expected-outcome clauses absent — H2 |
| §6 `CONTROL MAGNITUDE-MATCHED (M-3)` | design-req §3, gov §1b | **DEVIATES** | Carries a prior and a reporting rule; population / DISJOINT proof / non-vacuity / expected outcomes absent — H2 |
| §6.1 `TRIPWIRE-1` / `TRIPWIRE-2` | design-req §4, L-24 F06 | **DEVIATES** | No expected collapse fraction; thresholds asserted, not derived; TRIPWIRE-2 has no vacuity check — H3 |
| §7 `CONVERSION-PIN` | design-req §9, L-21/P-15 | PARTIAL | Divisor object verbatim ✓, measured value computed at run ✓, "resulting effect" line carries no number — L4 |
| §8 `POWER` | design-req §6, SoT §7, M-1 | **FAILS** | Population base misquoted; precision bar unattainable; selectivity loss not accounted — C2 |
| §9 `BANDS` | design-req §5, reflection §5.4 | PARTIAL | Thresholds match §5.4's +0.03…+0.07; internally unreachable in [0.03, 0.07) — M8 |
| §11 `GOLDEN-TRACE` G1–G7 | design-req §7 | PARTIAL | Procedures, no hand-derived values or timestamps — L3 |
| §12 HARD / INFORMATIVE split | design-req §8, P-23/L-52 | MATCHES | Check-count reconciliation by name, artifact-dependency rule, unconditional determinism — correct |
| §0 `SPREAD-COST-DISCLOSURE` | design-req §10 | MATCHES | Verbatim; prohibited claims listed |
| §14 amendment ledger | design-req §12, L-23 | **DEVIATES** | Direction of the z-extension declared one-sided; "NARROWING" is not a permitted label — M3 |
| §13 battery/eligibility rules | design-req §13 (L-24) | **DEVIATES** | Clauses 1–3 unmet — H3 |
| §2.1 inherited grammar table | SPDR-014 §2–§4 | **DEVIATES** | UNDECIDED-side rule dropped; FLAT deadband silently changed — M6 |
| §2.2 selectivity fix | ckpt-018 design, HYP-D7 registered wording | **DEVIATES** | Registered in substance; parent p_event misquoted and the parent's z cap undisclosed — M1/M2 |
| §2.3 sign-flip discharge | SPDR-018 report §C7 | **MATCHES** | Verified — see "verified claims" below |
| §4 layer protocol L0–L5 | AMENDMENT-C6 / reflection §5.9 | PARTIAL | Structure and phase-(b) trigger/scope split are correct; L1 breaks "same fixed signed entry" — M7 |
| §5 residual target | reflection §5.4, audit A1 | **MATCHES** | Exact mirror, slope 1, intercept 0; fitted slope refused in §5, §12 and §13. No defect |
| §13 refusals | AMENDMENT-C2/C5, gov §3 | MATCHES | Cost enters no estimand, threshold or comparison anywhere in the design |

---

### Golden-trace diff

G1–G7 cannot be diffed pre-execution as written: they specify *procedures* for QA to run at
emission time and contain no timestamps, input states or expected values. Per design-requirements §7
the design should carry 2–3 hand-derived events. Two further notes:

- **G1** asserts per-event quantities (band width, touch bar, entry open, exit open, `r_h`) against
  "SPDR-014's published values for the same cell". SPDR-014's *report* publishes cell aggregates
  (§4.2: ETHUSDT n=194, mean +26.2 bps, MDE 49); the per-event values live in
  `python/experiments/SPDR-014/results/post_event.parquet`. Name the artifact, not the report.
- **G2** is the one trace that can be pre-evaluated, and it fails as written: it asserts that "the
  z=3.0 cell's `p_event` is emitted and used to set its NON-SELECTIVE / selective label", implying a
  selective cell exists at z=3.0. Measured, it does not (C1).

---

### Governance & boundary

| Check | Evidence |
|---|---|
| TRAIN-only, holdout sealed | §10 fence `2023-12-18`, holdout `2025-01-08` never queried; §12 asserts both — PASS |
| Causal `t-1` | §2.1 anchor `open[t+1]`, entry `open[j+1]`, exit `open[entry+h]`, layer state at breach-bar close; §12 causality row + TRIPWIRE-1/2 — PASS |
| No tradability / deployability claim | §0 prohibited claims; §13 refusals — PASS |
| Matched control + seed battery | ≥2000 seeds on both derangement controls; ≥25-seed floor exceeded (L-19) — PASS |
| Per-stratum reporting, multiplicity disclosed | §9 per-cell bands, pooled with homogeneity statistic — PASS on form; cell count wrong — M4 |
| No local accounting | §12 row present; screen metrics are residual bps — PASS |
| Dependence-matched uncertainty | Block bootstrap, block ≥ h; iid companion-only (M-1) — PASS |
| L-28 derangement | Both permutation controls declare `DERANGEMENT`, fixed-point count == 0 emitted — PASS |
| L-50 / P-21 threshold units | Primary bar (`0.07 log units`) is scale-free — PASS. Control plant curves in absolute bps — L5 |
| L-51 / P-22 selection check | `results/selection_check.json` "on every powered subset" — PASS |
| L-52 / P-23 check counting | §12 check-count reconciliation by name; artifact-dependency; unconditional determinism — PASS |
| L-53 / P-25 deflator | No deflator (gross-only) — N/A |
| L-21 / P-15 unit pin | §7 present, computed at run — PASS with L4 |
| AMENDMENT-C5 cost exclusion | Traced through §0, §5, §7, §12, §13 — **no reintroduction found anywhere** — PASS |
| AMENDMENT-C6 layer protocol | Phase (a) sequential, L5 ≠ phase (b), phase-(b) trigger pre-declared and scope fixed independent of (a), individually-flat layers retained — PASS |
| AMENDMENT-C1 / C2 | cTrader excluded from phase (a) and never pooled; no expectancy claim — PASS |
| Registry precondition | HYP-D7 registered (`cf-voldir-001.md` L135); C5/C6 amendment rows exist (L421–435) — PASS |
| XENA | None — N/A |
| Recorded dead end re-walked | **P-02** (tuning capture geometry on a dead entry) is not acknowledged — H1 |
| Named-mechanism requirement | gov §1b "demand the mechanism, not a search" — **not met** — H1 |

---

### Verified numeric claims (re-derived by this reviewer)

Recomputed from `python/experiments/SPDR-018/results/analyst_per_cell_magnitudes.parquet`,
`python/experiments/SPDR-014/results/zones.parquet`, and the fenced H1 catalog via
`SPDR-014/screen_code/`:

| Design claim | Re-derived | Status |
|---|---|---|
| §1 "121 cells at median block MDE 7.87 bps" | C1 residue item, arm C: **121** cells, median block MDE **7.8706** bps | ✓ |
| §1 / §8 arm C `p` 0.467, `W` 142.1, `L` 124.5, `W/L` 1.136 | **0.4674 / 142.128 / 124.482 / 1.1363** (medians, 534 powered arm-C cells) | ✓ |
| §8 `(1−p)·L ≈ 66.4 bps` | 66.36 (and `p·W` = 66.36 — the object is at break-even) | ✓ |
| §8 required mean-MDE 4.6 / 3.3 / 2.0 bps | 4.65 / 3.32 / 1.99 | ✓ |
| §8 n multiples 3.1× / 6.0× / 16.8× | **2.87× / 5.62× / 15.61×** (from MDE 7.8706) | ✗ — L1 |
| §6 side-derangement −12.221 bps @ pct 0.0065 | SPDR-018 report §5 | ✓ |
| §6 `mag_high` percentile 0.46 | SPDR-018 report §5 (live −11.607 vs −10.704, gap 0.90 bps) | ✓ |
| §6 ambient-base rate +0.0255, `W` −33.7, `W/L` −0.124 | SPDR-018 report §5 | ✓ |
| §2.3 C7: 44.14% flip, 6.63% > MDE, 0.33 bps; cTrader 40.99% / 0.65 bps | SPDR-018 report §C7; SPDR-018B report R10 / §188 | ✓ |
| §7 cost floor 13.1–16.1 bps | SPDR-018 report §24 | ✓ |
| §1 "parent's 0 of 927" | SPDR-014 report §8 | ✓ |
| §2.2 / §8 "parent p_event 0.938–0.998 **at z = 1.5**" | 0.998 / 0.985 / 0.938 at z = **1.0 / 1.5 / 2.0**; at the primary cell median 1.000, per-symbol 0.995–1.0 | ✗ — M1 |
| §8 "749,456 zones / 560,652 rows … at z=1.5" | Those are **grid totals** over z∈{1.0,1.5,2.0}×H×sources×events. At z=1.5: **261,305** zones / **211,872** rows; at the primary Z-VOL/H1/H12/z1.5 cell: **19,637** zones | ✗ — C2(a) |

---

### Issues

#### CRITICAL

**C1 — The selective grid and the powered grid are disjoint; the primary read is empty as specified.**
(§2.2 BAND-SELECTIVITY RULE + §10 `z ∈ {1.5…3.5}` + §10 `H = 12 primary` + §8 predeclared-UNPOWERED
list.)

Two independent proofs.

*From the design's own text.* §2.2 gives a primary conclusion only to cells with `p_event ≤ 0.60`,
which requires high `z`. §8 then predeclares "**the high-z tail (z ≥ 3.0) on any symbol subset;
likely on the pool too**" as UNPOWERED for the `log R` read, and §9 permanently excludes UNPOWERED
cells from any conclusion. Every cell is therefore either non-selective (no primary conclusion, §2.2)
or high-z (predeclared unpowered, §8). No cell can carry a powered primary conclusion.

*From data.* I reconstructed `p_event` exactly, using SPDR-014's own zone anchors and `sigma_bps`
from `zones.parquet` against the fenced H1 bars (excursion in σ̂ units over the H-bar window), for
Z-VOL:

| symbol | H | event | z=1.5 | z=2.0 | z=2.5 | z=3.0 | z=3.5 | z=5.0 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 12 | E-TOUCH | 1.000 | 0.984 | 0.950 | 0.896 | 0.844 | 0.673 |
| ETHUSDT | 12 | E-TOUCH | 0.998 | 0.986 | 0.966 | 0.930 | 0.867 | 0.674 |
| MATICUSDT | 12 | E-TOUCH | 1.000 | 0.989 | 0.959 | 0.905 | 0.833 | 0.605 |
| BTCUSDT | 12 | E-CLOSE | 0.955 | 0.883 | 0.792 | 0.706 | 0.645 | 0.451 |
| ETHUSDT | 12 | E-CLOSE | 0.950 | 0.898 | 0.835 | 0.737 | 0.656 | 0.471 |
| BTCUSDT | 4 | E-TOUCH | 0.929 | 0.805 | 0.681 | 0.576 | 0.491 | 0.272 |
| BTCUSDT | 4 | E-CLOSE | 0.672 | 0.524 | 0.445 | 0.355 | 0.279 | 0.164 |
| BTCUSDT | 24 | E-TOUCH | 1.000 | 0.998 | 0.990 | 0.969 | 0.961 | 0.890 |

(SOLUSDT and XRPUSDT reproduce the same shape on both DESIGN and CONFIRM; z=3.5/H=12/E-TOUCH runs
0.785–0.906 across five symbols and two bands.)

At the design's **primary** configuration (H = 12), the top of the declared sweep, z = 3.5, still
gives `p_event` ≈ **0.83–0.87** on E-TOUCH and ≈ **0.65** on E-CLOSE. Reaching `p_event ≤ 0.60` at
H = 12 needs z ≈ 5.5–6. Selectivity is only reachable inside the **co-report** stratum H = 4
(E-TOUCH from z ≈ 3.0, E-CLOSE from z ≈ 2.0), and at H = 24 it is unreachable at any declared z.

*Required fix (design-level, `quant-designer`).* One of: (a) make **H part of the selectivity
sweep** and re-declare the primary as the first (H, z, event) triple that satisfies the rule, with
§8 power re-derived at that triple; (b) extend `z` to the level that actually selects at H = 12
(≈ 6) and re-derive n there; or (c) restate the 0.60 threshold as a measured, relative selectivity
criterion. Whichever is chosen, §8's predeclared-UNPOWERED list must stop excluding the region the
primary read now lives in, and §11 G2 must be rewritten against a z that actually crosses the
threshold.

**C2 — §8's power statement rests on a mis-attributed population and a precision bar that no real
cell in the parent's emission attains; the selectivity loss is asserted, not computed.** (§8 POWER.)

(a) *Wrong base.* "SPDR-014 emitted 749,456 zones / 560,652 post-event rows across 25 symbols **at
z=1.5**" — those are totals over the whole parent grid (z ∈ {1.0, 1.5, 2.0} × H × sources × events).
Measured: **261,305** zones and **211,872** post-event rows at z=1.5; **19,637** zones at the
primary Z-VOL/H1/H12/z1.5 cell. The 15–40 % retention estimate and the "8k–25k episodes per pooled
cell" figure inherit a base inflated ≈2.6–2.9×.

(b) *The bar is not attainable.* §6 and §9 predeclare UNPOWERED at block MDE > 0.07 log units
(= 4.65 bps at `(1−p)L` = 66.4). Of the **18,988** arm-C cells SPDR-018 emitted on this very object
— already σ̂-normalised and pooled — only **8** have block MDE ≤ 4.65 bps, and all 8 are degenerate
`n = 2` cells. **0 of the 534** powered arm-C cells reach it. The largest genuine cell in arm C
(`n = 20,977`, whole-TRAIN pooled, no band split, no selectivity restriction) reaches **5.19–5.27
bps = 0.078–0.079 log units** — still above the design's own UNPOWERED line, *before* SPDR-020
splits DESIGN/CONFIRM (§10, "both scored") and *before* the `p_event ≤ 0.60` restriction removes
episodes.

(c) *The two estimates point at different cells.* §8's "8k–25k episodes per pooled cell **at the
lower z-levels**" describes exactly the cells §2.2 labels NON-SELECTIVE. The design's own power
argument is therefore made on the population its primary read excludes.

(d) The prose "Forcing `p_event ≤ 0.60` … removes roughly 40% or more of the event population per
zone" is not derivable from anything in the design and conflates a per-cell rate constraint with a
population count. Replace with a computed retention curve per (H, z, event) — the data to compute it
already exists in `SPDR-014/results/`.

*Required fix.* Re-derive §8 from the correct base, state the achievable block MDE in log units at
the design's actual maximum pooling (including the DESIGN/CONFIRM split), and either raise the
UNPOWERED threshold to something attainable and say so, or predeclare the whole primary read
`NOT_RESOLVABLE` and reframe the run as characterisation. Both are honest; the current text is
neither.

#### HIGH

**H1 — No named mechanism, and a recorded dead end is re-walked without reconciliation.**
(§1 MECHANISM; chapter-06 governance §1b; pitfalls P-02; reflection §5.3/§5.6.)

Governance §1b is explicit and binding on this design: *"any proposal must **name the mechanism**
that puts `R = p·W/((1−p)·L)` above 1 — five distinct exit devices spanning a 36–67× range of `W/L`
did not, on either universe. **Demand the mechanism, not a search.**"* §1 offers "the SAME forecast
that sets the band can also place the exit boundaries so the realised payoff sits OFF the driftless
mirror" — a restatement of the hoped-for outcome, with no account of *why* coupling the exit to the
band-setting forecast should break an identity that `E[gross] = 0` forces. What follows is a ~44-cell
device grid: structurally, a search.

Compounding, the design nowhere reconciles itself with:
- **P-02** — "Tuning the downstream stack (exits, capture geometry, conditioning, anchors, sizing) to
  rescue a dead entry … Re-open only if: **Never, on a dead entry**." The inherited entry is measured
  at gross break-even (arm C gross median +0.08 bps, 0 of 1,413 clearing `p_be_net`) with a
  side-derangement pointing against the registered direction.
- **Reflection §5.3** — "Exit geometry can manufacture expectancy: **No — measured false on two
  universes** (V24, V25)". That is a binding input to this design and its expected outcome.
- **Reflection §5.6** — five pre-registered falsifiable predictions written specifically so
  SPDR-019/020 carry expectations. None appears in the design.

*Required fix.* Add (i) a `MECHANISM-NAMED` statement answering governance §1b, (ii) a dead-end
reconciliation stating why this is powered characterisation of a registered UNPOWERED item rather
than a P-02 re-walk (the honest answer is available — HYP-D7 is registered, the estimand is `log R`
not P&L, and no tradability claim is made — but it must be written down), and (iii) reflection
§5.6's predictions as pre-registered expectations.

**H2 — Three of five control blocks are not filled out.** (§6; design-requirements §3.)

The requirement is one block per control with seven clauses each; a block that is merely named is
non-compliant.

| Control | Missing clauses |
|---|---|
| SIDE-DERANGEMENT | `question answered`, `population` + B-1 disjointness, `non-vacuity` (B-6), `expected outcome if H true/false` |
| AMBIENT-BASE | `non-vacuity`, `expected outcome if H true/false`, destroy-form statement |
| MAGNITUDE-MATCHED (M-3) | `question answered`, `population` + B-1 disjointness, `non-vacuity`, `expected outcome if H true/false`, own bite/MDE curve (it borrows SPDR-018's prior instead) |

All three carry a *prior* from SPDR-018 and a *reporting rule*; neither substitutes for a validity
proof on **this** population, which differs from SPDR-018's (high-z, selective). Additionally, none
of the five blocks states the **collapse fraction** disclosure required by B-2 / design-requirements
§3 — and governance §1b's standing rule that collapse fraction is disclosure-only near a zero mean
(M-5) is not carried either.

**H3 — L-24 battery/eligibility/null clauses 1–3 unmet.** (§6, §6.1; design-requirements §13.)

1. *Time-stability eligibility (F02).* No time-stability read and no concentration ceiling. The
   parent required sign agreement in ≥2/3 chronological thirds (SPDR-014 §8.1); SPDR-020 drops it
   without disclosure. On a fat-tailed object where §6 itself warns about term offsetting, this is
   the eligibility clause that matters.
2. *Exit-matched nulls (F04).* L4 introduces trailing stops and dynamic targets — path-dependent
   exits. The ENTRY-TIMING DERANGEMENT preserves "hold length `h` and side", i.e. the **fixed-horizon**
   exit. Each battery seed must be re-run under `exit*`, or `exit*` cells are demoted to disclosure.
   As written, every L4 device cell will be scored against a null built on a different exit rule.
3. *Derived tripwire thresholds (F06).* TRIPWIRE-1 "must materially change the edge" and TRIPWIRE-2
   "must differ" are assertions. design-requirements §4 requires an expected collapse fraction;
   L-24 requires it derived from the data, with CI. TRIPWIRE-2 also carries no vacuity check. Both
   are declared HARD, so an underived threshold makes a HARD gate unauditable.

#### MEDIUM

**M1 — §2.2 and §8 misquote the parent's `p_event`.** "SPDR-014's `p_event` ran 0.938–0.998 **at
z = 1.5**" — that range is the parent's **z-sweep** (0.998 / 0.985 / 0.938 at z = 1.0 / 1.5 / 2.0,
`SPDR-014/screen.md` §22). At z=1.5 the primary cell's median `p_event` is **1.000**
(`SPDR-014/analysis.md` §3) and the per-symbol range is 0.995–1.0 (`report.md` §4.2). The
misquote understates the problem the fix exists to solve and makes the z-sweep look far more
promising than it is. (Note: the checkpoint design and governance file carry the same 0.938–0.998
figure, correctly, as a sweep range — the error is the "at z=1.5" attribution.)

**M2 — the z-extension is defensible but is mis-characterised; disclose that it leaves the parent's
frozen grid.** (§2.2, §14.) Assessment of the QA question "grid extension or estimand substitution":
**grid extension, legitimately registered — but out-of-parent-grid.** Reasoning: HYP-D7's registered
wording in `cf-voldir-001.md` L135 is *"Same question on the SPDR-014 E-TOUCH / E-CLOSE event object
under direction-aware capture, **with a band that actually selects**"*, so forcing selectivity is the
registered hypothesis, not a substitution; the object's anchor, event types, entry, exit and residual
are untouched; and z=1.5 is retained as a parity anchor. Separate registration is not required.
However, SPDR-014 §2.3 froze `z ∈ {1.0, 1.5, 2.0}` ("all mandatory"), so {2.5, 3.0, 3.5} is an
**expansion** of the parent's frozen grid into a region with no parent evidence and no parity anchor
— and (per C1) the region that actually selects is further out still. The design's sentence "`z` is a
registered parameter of the 014 object" is true but omits the cap. State the parent's grid, state
that every selective cell is out-of-parent-grid, and state that parent parity is assertable at
z = 1.5 only.

**M3 — amendment-direction ledger under-declares (L-23).** (§14.) The z-extension is recorded as
"TIGHTER in effect". It is tighter on the primary-conclusion filter and **looser** on the parameter
grid and its multiplicity (5 z-levels against the parent's 3). Declare both. Also "C5 (NARROWING)" is
not one of the three permitted labels (design-requirements §12: LOOSER | TIGHTER | NEUTRAL).

**M4 — §10's cell count contradicts §4 and §10's own sweeps.** "phase (a): ≤ 120 cells × 2 bands"
cannot hold: §4 counts L0 as "6 (3 event types × 2 sides) **at the primary z**", while §10 sweeps
z(5) × sources(3) × H-alternatives × h(3) × clocks(2) × bands(2). L0 alone is 3 × 2 × 5 × 3 × 3 × 2 ×
2 = 1,080 cells; L4's ~44 devices multiply through the same axes. Either the count or the scope table
is wrong. Multiplicity disclosure is a HARD lane requirement (spdr-lane, L-03) and this design is on
record as "disclosed, not rationed" — so the number must be right.

**M5 — parent parity is a HARD check with no tolerance.** (§2.2, §11 G1, §12.) "to a declared
tolerance" appears three times; the tolerance is never declared. SPDR-018 declared and achieved
9.1e-13 on this same arm. State the number, and name the artifact parity is asserted against
(`SPDR-014/results/post_event.parquet`, not the report's aggregates).

**M6 — the inherited grammar is silently re-specified in two places** despite §2.1's "inherited, not
re-specified".
- *UNDECIDED side.* SPDR-014 §3 defines it (both extremes pierced within one bar → the farther
  extreme wins; tie → UNDECIDED, counted in the event rate, **excluded** from the signed residual).
  SPDR-020 never mentions it. Its incidence rises with `z` — i.e. exactly in the selective region the
  design depends on — so this is not a cosmetic omission.
- *FLAT deadband.* SPDR-014 §4.2 uses `c = 5 bps`. SPDR-020 §3 uses `r == 0`. The change is arguably
  correct for a `(p, W, L)` decomposition, but it is undisclosed and it moves `p`.

**M7 — L1 changes the entry population, breaking §5.9's "same fixed signed entry".** (§4, L1.)
Reflection §5.9 is binding: "Each layer is characterised **alone**, against the **same fixed signed
entry**". For this object the band width already *is* σ̂-scaled; L1 as written makes `z` itself a
ŝ-conditioned quantity, which changes **which zones breach and when**. Consequently (i) Δ`log R`(L1)
confounds a change of entry population with a capture effect, and (ii) every L1 cell has its own
`p_event`, hence its own selective/non-selective label — so L1 cells are not comparable to L0 under
§2.2. L2/L3 (breach-bar state and swing gates) subset the population without changing the entry and
are fine. Either re-specify L1 as a capture-parameter scaling on a fixed entry, or declare it a
distinct-entry arm with its own L0.

**M8 — the SUPPORTED band's lower half is unreachable by construction.** (§8 vs §9.) §9 sets
SUPPORTED at `log R ≥ +0.03` with `ci_low > 0`; §8 predeclares "every cell at target Δ`log R` ≤ 0.03"
UNPOWERED and §9 sets UNPOWERED at MDE > 0.07. An effect in [0.03, 0.07) can never show `ci_low > 0`
at an admissible MDE, so no cell can be SUPPORTED below ≈0.07. State the reachable region explicitly
so a reader cannot mistake "+0.03" for the operative bar.

#### LOW

**L1 — §8's n-multiples do not reproduce.** With arm-C C1 median block MDE **7.8706** bps and
`(1−p)L` = 66.36, the multiples are **2.87× / 5.62× / 15.61×**, not 3.1× / 6.0× / 16.8× (the stated
values imply an MDE of ≈8.15 bps). The direction is conservative. Separately, §8's "the requirement
is ~10,800" uses a different n base (arm-C median n = 3,708) than the table's stated base ("a median
SPDR-018 powered cell"; C1 median n = 4,284, which gives ~12,300). Pick one base and show it.

**L2 — golden traces carry no values.** (§11; design-requirements §7.) G1–G7 are instructions, not
hand-derived events; nothing in them is falsifiable before the run. Add at least two concrete events
(timestamp, input state, expected entry price/side, expected exit price/reason).

**L3 — CONVERSION-PIN's "resulting effect" line is empty.** (§7; design-requirements §9.) Defensible
here, because every band, threshold and MDE is in log units and no screen effect is being converted
into a money target — but say that explicitly, so the L-21 clause is satisfied on the record rather
than deferred to run time.

**L4 — control plant curves are in absolute bps.** (§6.) `+5/+10/+20/+40 bps` on a σ̂ = 73 bps
universe. §7 already promises every effect in both bps and σ units; do the same for the plant curves
(L-50/P-21). Matters if the AMENDMENT-C1 cTrader leg is ever authorised (σ̂ = 13.03 bps).

**L5 — two standing governance rules not carried.** (gov §1b "Standing design rules".) Power plans
must use **effective, not nominal**, multi-symbol coverage — §8 uses pooled episode counts with no
coverage statement (SPDR-018 emits `coverage_effective_frac_of_nominal`; inherit it). And collapse
fraction is disclosure-only near a zero mean (M-5) — not stated anywhere in §6.

---

### What is right, and should not be changed

Recorded so a revision does not disturb it: the residual target is the **exact** mirror at slope 1 /
intercept 0, with the fitted-slope form refused in three separate places (§5, §12, §13) — audit A1 is
correctly discharged. AMENDMENT-C5 is clean throughout: no cost term enters any estimand, threshold,
band or comparison, and `p_be_net` / the cost floor are marked `DISCLOSURE_ONLY` in §5, §7, §12 and
§15. AMENDMENT-C6 is implemented faithfully, including the hard part — phase (b)'s trigger is
pre-declared before phase (a) runs and its scope is fixed independent of (a)'s outcome, with
individually-flat layers retained. B-4 is handled better than the parent: conditioning is at the
breach bar, the three breach types are kept as separate commitment states and are never pooled. B-9
suppression is explicit and counted. The §12 integrity checklist correctly implements L-52/P-23
(check-count reconciliation **by name**, every check dependent on an emitted artifact, determinism
unconditional under `--jobs > 1`), L-28 (fixed-point counts), P-22 (selection check artifact) and
P-24 (null means, quantiles and plant curves alongside every percentile). §2.3's discharge of the
DESIGN→CONFIRM sign flip is correct and fully supported by SPDR-018 C7 and SPDR-018B R10 — it does
not need re-litigating.

### Routing

- **C1, C2, H1, H2, H3, M1–M8, L1–L5** → `quant-designer` (all design defects; no implementation
  exists).
- Re-run QA after revision. Execution remains unauthorised and is the operator's gate regardless of
  this verdict.

---

## QA run 2 — 2026-07-28T18:56:58Z — mode: subagent — HEAD 51d6a281ef2f0833cbc15c3fa062f70409a1b983 (clean)

**Verdict: REVISE** (design-stage compliance review; `screen_code/` not yet written — expected state,
not a finding).

**Scope.** Fresh context; run 1's conclusions were not assumed. Three parts: (A) closure of each
run-1 finding against the current text, numbers re-derived; (B) defects introduced by the changes
(gate removal, full-TRAIN primary, AMENDMENT-C7 adequacy retirement, corrected populations);
(C) independent judgement on the design-requirements §5/§6 vs AMENDMENT-C7 tension. Sources read:
`SPDR-014/{design,report,analysis,screen}.md` and its emitted `zones.parquet` / `post_event.parquet`
/ `zvol_scale.json`; `SPDR-018/results/analyst_per_cell_magnitudes.parquet`;
`quant-designer/references/design-requirements.md`; `docs/references/spdr-lane.md`;
`docs/references/chapter-06-governance.md`; `docs/knowledge-base/pitfalls-ledger.md`;
`reflection-mid-volatility-model.md`; `docs/signal-registry/candidate-families/cf-voldir-001.md`.

**Headline.** Real progress: both run-1 CRITICALs are closed, and the design can now produce a
primary read. **No CRITICAL findings this run.** But three of the six blockers the revision was
meant to close are *verbatim unchanged* (named mechanism, control blocks, L-24), one is closed only
in prose while the body still contradicts it, and the corrected §8 has replaced a wrong population
with a resolution arithmetic that is 3–8× optimistic and derived from a precision-selected subset.

---

### Part A — closure of run-1 findings

| Run-1 | Status | Evidence |
|---|---|---|
| **C1** selectivity gate unreachable | **CLOSED** | Gate removed entirely (§2.2). `p_event` swept across §2.2/§5/§8/§9/§11 G2/§12/§13/§15 — it is emitted as a covariate and dose-response axis and **nothing filters, weights, labels or ranks on it**. Band labels are CI-relative only. Verified clean. |
| **C2(a)** population mis-attributed | **CLOSED** | Re-derived from the parent artifacts: zones 234,785 / **261,305** / 253,366 and post-event rows 190,467 / **211,872** / 158,313 at z = 1.0 / 1.5 / 2.0. Design §8 matches **exactly**. Grid totals 749,456 / 560,652 confirmed as whole-grid. §8's "~86.8k post-event rows at z=1.5, Z-VOL, h=12" = **86,831** measured. Correct. |
| **C2(b)** unattainable 0.07 bar | **CLOSED BY REMOVAL** — but see **H4**: the optimism migrated into the required-episode table and EXPECTED RESOLUTION and is now measurably wrong. |
| **H1** no named mechanism | **NOT CLOSED** — see H5. §1 MECHANISM is unchanged verbatim; no `MECHANISM-NAMED` block; no P-02 reconciliation; reflection §5.6's five predictions still absent. |
| **H2** three control blocks unfilled | **NOT CLOSED** — see H6. SIDE-DERANGEMENT, AMBIENT-BASE and MAGNITUDE-MATCHED are unchanged; the missing clauses are the same ones. |
| **H3** L-24 clauses 1–3 | **NOT CLOSED** — see H7. All three still unmet. |
| **M5** parity tolerance undeclared | **NOT CLOSED** — see M10. Still "a declared numeric tolerance (stated in `results/parent_parity.json`)" on a HARD check; G1 still targets the report's "published values". |
| **M6** UNDECIDED + 5 bps deadband | **PARTIALLY CLOSED** — see M9. §2.2 asserts both restored and explicitly withdraws the `r == 0` test; **§3 still says `r == 0`**. Internal contradiction. |
| **M1** parent `p_event` misquote | **CLOSED** — the "0.938–0.998 at z=1.5" attribution is gone; G2's 0.995–1.000 is the correct per-symbol range at the primary cell. |
| **M2** z-grid disclosure | **CLOSED** — §2.2 now states the parent's frozen `{1.0, 1.5, 2.0}`, names the drop and the two additions, and anchors parity at z = 1.5; repeated in §10 and §14. Adequate disclosure of the departure. |
| **M3** ledger direction | **CLOSED** — amendments 1–4 carry LOOSER/NEUTRAL with a running count and an L-23 streak note. "C5 (NARROWING)" is the **family ledger's own label** (`cf-voldir-001.md` L420), transcribed, not invented — defensible. |
| **M4** cell count | **NOT CLOSED** — see M11. |
| **M7** L1 changes the entry population | **NOT CLOSED** — see M12. L1's text is unchanged. |
| **M8** unreachable SUPPORTED band | **CLOSED BY REMOVAL** (magnitude thresholds retired). |
| **L1** n-multiples | **CLOSED** — the table now states required episodes; ~10,800 / 21,200 / 58,800 reproduce from the C1 at-precision base to within rounding. (Superseded by H4, which is about the base itself.) |
| **L2** golden traces carry no values | **NOT CLOSED** — see L6. |
| **L3** CONVERSION-PIN "resulting effect" | **CLOSED** — §7 now states effects in both bps and σ units and AMENDMENT-C5 removes the money-target seam. (But see M13 on the divisor.) |
| **L4** plant curves bps-only | **NOT CLOSED** — see L7. |
| **L5** effective vs nominal coverage | **NOT CLOSED**, and now shown to be material — see H8. |

**Verified numeric claims (re-derived this run).** §1's "121 cells at median block MDE 7.87 bps" =
121 arm-C C1 cells at `at_parent_target_precision`, median **7.8706** ✓. Arm-C at-precision medians
`p` **0.4674**, `W` **142.128**, `L` **124.482**, `W/L` **1.1363** ✓. `(1−p)·L` = **66.30** ✓.
SPDR-014 parent grammar confirmed against its design §2.3/§3/§4: z ∈ {1.0,1.5,2.0}, H ∈ {4,12,24},
E-TOUCH/E-CLOSE/E-HORIZON as SPDR-020 §2.1 states them, entry `RealOpen[j+1]`, exit
`RealOpen[entry+h]`, `h ∈ {4,12,24}`, side ±1, UNDECIDED counted in the event rate and excluded from
the signed residual, FLAT deadband `c = 5 bps`, Z-VOL = Parkinson EWMA(λ=0.94) × frozen `s_symbol`,
Z-MAG = ZigZag next-swing magnitude, Z-MAG-SENS = half width. **§2.1's inherited-grammar table is
faithful to the parent on every row.**

---

### Part B — findings on the changes

#### HIGH

**H4 — §8's resolution arithmetic is derived from a precision-selected subset, is blind to the
horizon its own M-1 rule mandates, and is contradicted by direct measurement on the same object.**
(§8 required-episode table + EXPECTED RESOLUTION; design-requirements §6; P-22, P-25; M-1.)

The table's scaling constant `k = MDE·√n` comes from arm C's **`at_parent_target_precision == True`**
subset — the 534 cells (121 in C1) that SPDR-018's precision filter *retained*, which §1 cites by
name. That subset is selected on the very quantity being extrapolated. Measured:

| Base | `k = MDE·√n` (median) |
|---|---:|
| arm-C C1 at-precision (the design's base) | **523.9** |
| full arm-C emitted population | **982.7** |
| full arm-C, `h = 4` | 569.0 |
| full arm-C, **`h = 12`** (design's primary hold) | **955.2** |
| full arm-C, **`h = 24`** | **1383.7** |

Required episodes, recomputed on the unselected population:

| Rung | Design says | `h = 4` | `h = 12` | `h = 24` |
|---|---:|---:|---:|---:|
| Δlog R = 0.05 | ~21,200 | 29,405 | **82,874** | **173,908** |
| Δlog R = 0.03 | ~58,800 | 81,666 | **230,160** | **482,981** |

This is not extrapolation — SPDR-018 emitted the confirming cells. Its largest genuine pooled cells
(`n` = 20,977 / 20,572 / 20,279, `__POOLED__`, dose-response basis) realise block MDE of
**0.079–0.101 log units at `h = 4`** and **0.137–0.157 at `h = 12`**. Of **18,632** arm-C cells,
**zero** reach 0.03 log units and only **four** reach 0.05 — all degenerate `n = 2`.

Against this, §8's `EXPECTED RESOLUTION` predicts the 20k–45k Z-VOL cell lands "around the **0.05**
rung, approaching **0.03**". Measured at that exact `n` on that exact object, it lands at **0.08
(h=4) to 0.16 (h=12)** — the coarsest one or two rungs of the ladder. The prediction is off by ~3×
at the design's primary hold, and the design's central viability claim ("Removing the selectivity
gate is what makes this experiment powered") rests on it.

Why this is HIGH and not CRITICAL: nothing gates on the prediction, and the ladder will emit realised
values regardless, so the run cannot produce a *wrong result* — only a wrong *expectation*. But under
AMENDMENT-C7 the reader's calibration **is** the B-5 protection (see Part C), which makes a 3×-wrong
predeclared expectation load-bearing in a way it would not have been before.

*Required fix.* Re-derive the table **per `h`** from the **full emitted arm-C population**, not the
at-precision subset; report the range across defensible bases and state which conclusions are
invariant to it (**P-25**); if the at-precision base is retained for any purpose, carry the L-51
three-number selection check on it (**P-22**). Restate `EXPECTED RESOLUTION` to the measured values
— i.e. that the primary read is expected to resolve near the **0.10–0.15** rungs at `h = 12` and
near **0.075–0.10** at `h = 4`, and that a CI covering the mirror is therefore the *expected* outcome
under both "H true but small" and "H false".

**H5 — no named mechanism; a recorded dead end is re-walked without reconciliation; the binding
pre-registered predictions are absent.** (§1; chapter-06 governance §1b; P-02; reflection §5.6.)
Unchanged from run 1 — the §1 MECHANISM sentence is verbatim identical. Governance §1b is binding
and explicit: *"any proposal must name the mechanism that puts `R = p·W/((1−p)·L)` above 1 — five
distinct exit devices spanning a 36–67× range of `W/L` did not, on either universe. **Demand the
mechanism, not a search.**"* §1 still offers only "the SAME forecast that sets the band can also
place the exit boundaries so the realised payoff sits OFF the driftless mirror" — a restatement of
the hoped-for outcome. What follows is a ~44-cell device grid.

**P-02** (verified verbatim in the ledger: *"Tuning the downstream stack (exits, capture geometry,
conditioning, anchors, sizing) to rescue a dead entry … Re-open only if: **Never, on a dead
entry**"*) is still unmentioned. Reflection **§5.6**'s five falsifiable predictions — written, in the
document's own words, "so the strategies have pre-registered expectations" — appear nowhere; §5.6 #1
(*"Scaling every capture parameter by ŝ leaves `log R` unchanged"*) is the direct predeclared
expectation for the L1 layer and its absence is why this run is not falsifiable in advance.

*Required fix.* Unchanged from run 1: (i) a `MECHANISM-NAMED` block answering governance §1b;
(ii) a written P-02 reconciliation (the honest answer is available — HYP-D7 is registered, the
estimand is `log R` not P&L, no tradability claim is made — but it must be on the page); (iii) §5.6's
five predictions carried as pre-registered expectations. **Third occurrence would warrant operator
escalation.**

**H6 — three of five control blocks are still not filled out.** (§6; design-requirements §3.)
Verbatim unchanged from run 1. Design-requirements §3 mandates seven clauses per control; a block
that carries only a *prior* and a *reporting rule* is non-compliant, and the priors are borrowed from
SPDR-018's population, not proven on this one.

| Control | Missing clauses |
|---|---|
| SIDE-DERANGEMENT | `question answered`, `population` + B-1, `non-vacuity` (B-6), `expected outcome if H true/false` |
| AMBIENT-BASE | `non-vacuity`, `expected outcome if H true/false`, destroy-form statement |
| MAGNITUDE-MATCHED (M-3) | `question answered`, `population` + B-1, `non-vacuity`, `expected outcome if H true/false`, its own bite/MDE curve |

**H7 — L-24 clauses 1–3 still unmet.** (§6, §6.1; design-requirements §13.)
1. *Time-stability eligibility (F02).* No time-stability read, no concentration ceiling. The parent
   required sign agreement in ≥2/3 chronological thirds (SPDR-014 §8.1). **AMENDMENT-2 makes this
   worse, not better**: promoting full TRAIN to primary and demoting DESIGN/CONFIRM to verification
   removes the only remaining temporal check from the primary read.
2. *Exit-matched nulls (F04).* L4 introduces trailing stops and dynamic targets — path-dependent
   exits — while ENTRY-TIMING DERANGEMENT still preserves "hold length `h` and side", i.e. the
   fixed-horizon exit. As written, every one of ~44 L4 device cells is scored against a null built on
   a different exit rule. Re-run each seed under `exit*`, or demote `exit*` cells to disclosure.
3. *Derived tripwire thresholds (F06).* TRIPWIRE-1's "must materially change the edge" and
   TRIPWIRE-2's "must differ" are assertions. design-requirements §4 requires an **expected collapse
   fraction**; L-24 requires it derived from TRAIN with a CI. TRIPWIRE-2 additionally carries no
   vacuity check. Both are declared HARD, so an underived threshold makes a HARD gate unauditable.

**H8 — the primary width source covers 17 of 25 symbols; the design states 25 and the
effective-coverage rule is uncarried.** (§7, §8, §10; governance "Standing design rules (SoT §9)":
*"power plans use effective, not nominal, multi-symbol coverage"*.)

`SPDR-014/results/zvol_scale.json` carries **NaN `s_symbol` for 8 of 25 symbols** — ORDIUSDT,
TIAUSDT, BIGTIMEUSDT, 1000PEPEUSDT, SEIUSDT, WLDUSDT, PYTHUSDT, 1000RATSUSDT (insufficient DESIGN
warm-up). Confirmed downstream: Z-VOL produces zones and post-event rows for **17 symbols only**, at
every `z` and `h`. §7 says "All 25 symbols **or the gap is stated**" — the gap is not stated. §8 says
"Pooled across **25 symbols** on full TRAIN". SPDR-018 already emits
`coverage_effective_frac_of_nominal`; inherit it.

*To be precise, and in the design's favour:* the §8 row counts I verified are computed from the
parent's emission and therefore **already** reflect 17 symbols, so this does not compound H4. It is a
disclosure defect plus an uncarried binding governance rule — but it also means the pooled primary
rests on 17 symbols, which bears directly on the §9 homogeneity argument (M15).

**H9 — HYP-D7's registered wording is now contradicted, and the departure is not reconciled.**
(§2.2, §14; `cf-voldir-001.md` L135.) HYP-D7 is registered as: *"Same question on the SPDR-014
E-TOUCH / E-CLOSE event object under direction-aware capture, **with a band that actually selects**."*
§2.2 now argues at length that selectivity is the wrong criterion and removes it entirely. Run 1
cited that same registered clause as the justification for the gate; run 2 removes the gate and
drops the reconciliation with it. AMENDMENT-1 records the change and its direction but never notes
that it departs from the hypothesis as registered.

The departure is defensible — the z-grid shift ({1.0} dropped, {2.5, 3.0} added) does make the band
strictly more selective than the parent's, and `p_event` is measured across it as a dose-response
axis rather than assumed. But that argument must be **written down**, and the registry entry either
amended or explicitly noted as read in this narrower sense. A design that contradicts its
hypothesis's registered wording without saying so is a registry-precondition failure.

#### MEDIUM

**M9 — §3 still specifies `r == 0`, contradicting §2.2's restoration of the parent's 5 bps deadband;
UNDECIDED is restored in prose only.** (§2.2 vs §3; SPDR-014 §3 and §4.2.) §2.2 states both parent
rules are "inherited verbatim" and that "the `r == 0` flat test in an earlier draft … is withdrawn".
§3 then reads: *"**Flat legs** (`r == 0`) are excluded from `p`, counted as `p_flat`."* The parent's
rule is `FLAT ⇔ |r_h| ≤ c`, `c = **5 bps**` (SPDR-014 §4.2, confirmed; parent emission carries 14,075
FLAT labels). The two clauses give materially different `p` — and `p` is the primary read's first
term. Separately, **UNDECIDED appears only in §2.2's assertion**: not in the §2.1 grammar table, not
in §3's flat/exclusion rule, not in §12's integrity checks, not in any golden trace. Its incidence
rises with `z`, i.e. across exactly the extended grid. *Fix:* correct §3 to `|r| ≤ 5 bps`; put
UNDECIDED in the §2.1 table and in §3's exclusion rule; add a §12 check asserting the UNDECIDED count
is emitted and excluded from the signed residual.

**M10 — parent parity is a HARD check with no declared tolerance, and G1 targets the wrong artifact.**
(§2.2, §11 G1, §12.) "to a declared tolerance" now appears three times and is still never declared;
deferring it to `results/parent_parity.json` means the HARD check's pass condition is authored at run
time by the code it is meant to police. SPDR-018 declared and achieved **9.1e-13** on this same arm.
State the number in the design. G1 still asserts against "SPDR-014's **published** values" — the
report publishes cell aggregates; the per-event values live in
`SPDR-014/results/post_event.parquet`. Name the artifact.

**M11 — §10's cell cap contradicts §4 and §10's own sweeps.** (§4, §10.) "phase (a): ≤ 120 cells"
holds only if each stage runs at one `(z, source, H, h, clock)` point (L0 6 + L1 3 + L2 5 + L3 2 + L4
~44 + L5 4 = 64). But §10 sweeps z(4) × sources(3) × h(3) × clocks(2) × events(3, never pooled) ×
sides(2), plus H alternatives. L0 alone is 3 × 2 × 4 × 3 × 3 × 2 = **432** before H alternatives and
before the verification bands; L4's ~44 devices multiply through the same axes. Multiplicity
disclosure is a HARD lane requirement (spdr-lane L-03) and this design is on record as "disclosed,
not rationed" — so the number must be right. Fix the cap or fix the scope table.

**M12 — L1 still changes the entry population, breaking reflection §5.9's "same fixed signed entry".**
(§4 L1.) Unchanged from run 1. Making `z` a ŝ-conditioned quantity changes **which zones breach and
when**, so Δ`log R`(L1) confounds a change of entry population with a capture effect. (The
selective/non-selective-label half of run 1's M7 is moot now that labels are gone; the confound is
not.) L2/L3 subset the population without changing the entry and are fine. Either re-specify L1 as a
capture-parameter scaling on a fixed entry, or declare it a distinct-entry arm with its own L0.

**M13 — the CONVERSION-PIN divisor omits the frozen `s_symbol` that makes it bps.** (§7; L-21/P-15.)
§7 pins `s_hat = LTF H1 Parkinson EWMA(λ=0.94) … **in bps**` and calls it "IDENTICAL object to
SPDR-014's Z-VOL width — reused verbatim". The parent's Z-VOL width is
`σ_bps_t = s_symbol × EWMA_park_t`; `EWMA_park` alone is **dimensionless**, and `s_symbol` (measured
range **4,606–7,338** across the 17 covered symbols) is the entire bps conversion. P-15 exists
because EXP-025 inflated a target 4.1× by asserting a divisor from memory at exactly this seam. *Fix:*
state the divisor as `σ_bps_t = s_symbol × EWMA_park_t`, name `SPDR-014/results/zvol_scale.json` as
the source of the frozen `s_symbol`, and state the 8-symbol NaN gap (H8) in the same block.

**M14 — the L-51 selection check is defined over a subset the design has retired.** (§4 L3, §15.)
`results/selection_check.json` is specified as "the L-51 three-number check on every **powered**
subset (P-22)", while §9 retires the powered/unpowered classification and §12 asserts that **no**
adequacy flag is emitted anywhere. As written the artifact has no population. Re-anchor L-51 to
whatever selection actually occurs (any subset formed on precision, magnitude or CI, including the
at-precision base if H4's fix retains it) and say so.

**M15 — pooled-primary inverts the lane default with no predeclared consequence.** (§9 POOLED;
spdr-lane L-03; design-requirements §5.) spdr-lane L-03 is explicit — *"A pooled figure is
disclosure-only"* — and design-requirements §5 permits pooled-primary only *"unless homogeneity
shown"*. §9 declares pooled "the PRIMARY read **by construction**" and emits I² alongside. Homogeneity
cannot be *shown* in advance, so this is an a-priori override of a lane default. No predeclared
consequence exists for the case where I² does not support pooling. *Fix compatible with INFR-016
(no thresholds):* state that the pooled line reverts to disclosure-only if the emitted homogeneity
statistic does not support it, with the operator judging — this keeps the lane default intact without
inventing a cutoff. Note H8: the pool is 17 symbols, not 25.

#### LOW

**L6 — golden traces still carry no hand-derived values.** (§11; design-requirements §7.) G1–G7 are
procedures. §7 requires 2–3 events with timestamp, input state, expected entry price/side and
expected exit reason/price, hand-derived *from the design*, so QA can diff before execution. Nothing
in G1–G7 is falsifiable pre-run. The parent's `post_event.parquet` makes at least G1 and G5 derivable
today.

**L7 — control plant curves remain absolute-bps only.** (§6.) `+5/+10/+20/+40 bps` on a σ̂ = 73 bps
universe. §7 already promises every effect in both bps and σ units; **L-50/P-21** requires the same of
every precision and materiality threshold. Matters the moment the AMENDMENT-C1 cTrader leg is
authorised (σ̂ = 13.03 bps) — the exact 5.6× silent loosening P-21 records.

**L8 — §14's opening line contradicts its own ledger, and AMENDMENT-C7 is missing from the in-force
list.** §14 opens *"No amendments to this design. Registered 2026-07-28. running count: 0 looser /
0 tighter / 0 neutral"* and then lists four amendments closing at 2/0/2. Delete the stale opener.
§14's closing "amendments in force" line reads U1, S1, C1, C2, C5, C6 — **C7 is absent**, though it is
registered (`cf-voldir-001.md` L448) and is the authority for §8, §9 and AMENDMENT-4. Add it.

**L9 — B-2 collapse-fraction disclosure absent from all five control blocks; M-5 uncarried.**
(§6; design-requirements §3.) "collapse fraction" appears only in §12's INFORMATIVE list. Each control
block must state the disclosure (B-2), and governance's standing rule that **collapse fraction is
disclosure-only near a zero mean (M-5)** — squarely applicable to an object measured at gross
break-even — is stated nowhere.

---

### Part C — is AMENDMENT-C7's B-5 argument sound? (independent judgement)

**Short answer: the argument is sound in principle and the replacement is better than what it
replaced, but the current text does not yet deliver B-5's protection.**

**What C7 gets right.** The diagnosis is correct and I verified it. The retired bars (+0.03 / 0.07)
were anchored on `sd(log R) = 0.0729` and `median log R = −0.0301` — the **dispersion** and
**location** of the observed residual. Neither is a statement about what effect size matters, and
using a dispersion statistic as an adequacy bar is circular: "adequate" comes to mean "as large as
whatever noise this sample happens to have", which drifts with `n` and with the population. Run 1
proved the practical consequence — **0 of 534** genuinely powered parent cells met the bar. Removing
a bar no cell could reach cannot weaken B-5.

**Where the "stronger" claim genuinely holds.** B-5's real-world failure mode is a thin cell's point
estimate travelling downstream without its precision. A boolean lives in a separate column and is
trivially dropped in a summary table; an effect whose MDE and CI width sit on the same row is
structurally harder to strip, and §12 makes the ladder's presence a HARD, artifact-dependent check.
That is a real improvement in *emission* discipline, and the design's stated reason for it is the
right one.

**Where the argument is incomplete — two gaps, both fixable.**

1. **B-5 is a rule about inference, not about emission.** "Cannot be read as a negative by omission"
   describes what a *careful* reader does with a complete row. B-5 exists because readers are not
   careful — that is precisely why the protection was machine-enforced. Co-location makes the
   *inputs* to the judgement unavoidable; it does not make the *judgement* unavoidable. Nothing in
   the current design prevents the summary sentence *"no cell's CI excluded the mirror"* — which is
   a negative-by-omission, is literally true, requires dropping nothing, and (given H4's measured
   resolution) is the single most likely sentence this experiment will produce. §9 does instruct that
   a covering CI "is NEVER a refutation and NEVER a negative" — good — but that instruction lives in
   the design, and there is no corresponding constraint on the prose that will carry the result.

2. **Co-location only protects a *calibrated* reader, and §8 mis-calibrates the reader in advance.**
   This is where H4 stops being a separate finding. A reader told to expect resolution at the 0.05
   rung, who then sees a CI covering the mirror, reads a well-measured null. A reader told to expect
   0.14 reads the same row as "we could not have seen anything this experiment was ever going to
   see". Identical numbers, opposite inference — and the design currently issues the first
   calibration while the object delivers the second. Under the old regime a wrong power prediction
   was insulated by the `UNPOWERED` label; C7 removed the insulation, which makes getting the
   prediction right a **precondition** of C7 rather than an independent nicety.

**What would deliver B-5's protection** — all three compatible with INFR-016 (no arbitrary
value-gates) and with C7 (no adequacy labels), none requiring a magnitude threshold:

- **(i)** Fix §8 per H4, so the predeclared expectation matches the object's measured behaviour.
  Adequacy cannot be "the reader's judgement" against a prediction that is 3× wrong.
- **(ii)** Add a **predeclared reporting rule** (not a threshold): every statement about a cell — in
  `screen.md`, `analysis.md` and any operator summary — must carry that cell's CI width and block MDE
  in the same sentence; and any aggregate statement of the form "no cell resolved above the mirror"
  must be accompanied by the count of cells whose ladder shows <50% detection at the effect size
  being discussed. This admits, excludes, labels and ranks nothing, and it closes the
  negative-by-omission route that co-location alone leaves open. It moves C7's protection from a
  property of the row to a property of the prose, which is where B-5 actually gets violated.
- **(iii)** State the experiment-level **expected outcome** in advance — reflection §5.6's five
  predictions (H5) plus an explicit statement that, at the resolution measured in H4, a CI covering
  the mirror is the expected result under *both* "H true but small" and "H false". A prediction made
  before the run is the strongest available B-5 protection, it costs nothing, and it is already
  required by design-requirements §3 and by the reflection.

With (i)–(iii) the C7 construction is, in my judgement, genuinely stronger than the label it
replaced. Without them it is weaker, because it has removed an enforced protection and replaced it
with an unenforced one.

---

### Governance & boundary (run 2 delta)

| Check | Evidence |
|---|---|
| AMENDMENT-C7 conformance | Registry L448 read in full; §8 ladder `{0.02,0.03,0.05,0.075,0.10,0.15}`, no adequacy flag, CI-relative bands, ledger AMENDMENT-4 — **conforms** (except the in-force list, L8) |
| `p_event` never applied | Swept all 8 occurrences — covariate/dose-response only; §12 asserts it, §11 G2 proves it, §13 refuses it — **PASS** |
| AMENDMENT-C5 cost exclusion | Re-traced §0, §5, §7, §12, §13, §15 — no cost term in any estimand, threshold, band or comparison; `p_be_net` and floor `DISCLOSURE_ONLY` — **PASS** |
| Exact mirror, slope 1 | §5, §12 and §13 all refuse the fitted-slope form; G6 asserts it — **PASS, no defect** |
| B-4 conditioning at the breach bar | §3 OBJECT-IDENTITY; three breach types kept distinct and never pooled (§4, §10, §13); G3 guards it — **PASS**, and better than the parent |
| B-9 non-overlap / suppression | One open episode per symbol, SUPPRESSED counted; block ≥ h — **PASS** |
| Parent fidelity (grammar) | §2.1 verified row-by-row against SPDR-014 §2.2/§2.3/§3/§4 — **PASS** |
| Parent fidelity (rules) | UNDECIDED + 5 bps deadband — **FAIL**, M9 |
| z-grid departure disclosed | §2.2 + §10 + §14 name the parent's frozen grid and both changes — **PASS** (M2 closed) |
| Registry precondition | HYP-D7 registered; C5/C6/C7 present — **PASS on existence**, **FAIL on wording** (H9) |
| L-21 / P-15 unit pin | Divisor incomplete — **FAIL**, M13 |
| L-28 derangement | Both permutation controls declare DERANGEMENT + fixed-point counts — **PASS** |
| L-52 / P-23 check counting | Check-count reconciliation by name, artifact-dependency, unconditional determinism — **PASS** |
| L-03 multiplicity | Cell count wrong (M11); pooled-primary override (M15) — **FAIL** |
| Effective coverage (SoT §9) | 17/25 on the primary source, undisclosed — **FAIL**, H8 |
| TRAIN fence / holdout | §10 + §12; no code path to holdout — **PASS** |
| Spread disclosure | §0 verbatim, prohibited claims listed — **PASS** |
| No local accounting / no XENA / 0 TEST reads | §10, §13 — **PASS** |

### Routing

- **H4–H9, M9–M15, L6–L9** → `quant-designer`. No implementation exists; every finding is a design
  defect.
- **H5, H6, H7** are *unchanged* from run 1 (H1, H2, H3). If they survive a second revision,
  escalate to the operator rather than issuing a third identical REVISE.
- Re-run QA after revision. Execution remains unauthorised and is the operator's gate regardless of
  this verdict.
