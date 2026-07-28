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
