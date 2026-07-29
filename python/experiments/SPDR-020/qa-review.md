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

---

## QA run 3 — 2026-07-28T19:26:49Z — mode: subagent — HEAD 42934ef91adb15a4aac2625b323021abf9ad94e5 (clean tree)

**Target:** `python/experiments/SPDR-020/design.md` (774 lines)
**Stage:** DESIGN-STAGE. `screen_code/` does not exist; that is expected and is **not** a finding.
**Independence:** this reviewer authored neither the design nor runs 1–2. Every number below was
re-derived with my own code from `SPDR-014/results/{zones,post_event,expectancy_by_cell}.parquet`,
`SPDR-014/results/zvol_scale.json` and `SPDR-018/results/analyst_per_cell_magnitudes.parquet`.
Where run 2's arithmetic and mine disagree, I show both.

**Verdict: REVISE.** Not fit to authorise implementation.

Findings: **4 HIGH · 4 MEDIUM · 6 LOW.**

**Plain reading.** The additions this revision made are real and mostly good: the mechanism for
`R > 1` is named and falsifiable, the three thin control blocks are properly filled, the three L-24
clauses are present, the parity tolerance is numeric, and the parent's deadband and UNDECIDED rule
are back. Every population figure I could check reproduces exactly from the parent's emission.
**But §8 — the section the revision was chiefly meant to fix — is now internally inconsistent three
ways, its required-`n` table does not follow from the formula printed directly above it, and the one
sentence run 2 identified as the design's central viability claim survives verbatim while the text
two paragraphs above it refutes that claim.** And **nine** run-2 findings are unchanged word for word.

---

### PART A — closure of the run-2 findings, verified against the artifacts

**Population and coverage figures — all reproduce exactly.** From `SPDR-014/results/`:

| §8 / §10 claim | Design | Re-derived | Verdict |
|---|---|---|---|
| zones by `z` (1.0 / 1.5 / 2.0) | 234,785 / 261,305 / 253,366 | **234,785 / 261,305 / 253,366** | REPRODUCES |
| post-event rows by `z` | 190,467 / 211,872 / 158,313 | **190,467 / 211,872 / 158,313** | REPRODUCES |
| whole-grid total spans all three `z` | 749,456 | **749,456** (`zones.parquet` row count) | REPRODUCES |
| Z-VOL, `z`=1.5, `h`=12 post-event rows | ~86.8k | **86,831** | REPRODUCES |
| **Z-VOL resolves on 17 of 25 symbols** | 17 of 25 | **17**; the 8 absent are exactly ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH, 1000RATS | REPRODUCES, and the symbol list is exact |
| G2's parent `p_event` at the primary cell | 0.995–1.000 | ETHUSDT Z-VOL z=1.5 E-TOUCH H=12: DESIGN **0.994872**, CONFIRM **1.000000** | REPRODUCES |
| the removed gate would have discarded most of the population | "most" | `p_event ≤ 0.60` retains **41,739 of 511,350** Z-VOL events — it would have discarded **91.8%** | REPRODUCES |
| Z-MAG / Z-MAG-SENS rows at the parent's primary cell | 223 / 876 | **223** / **876** — but only on the **DESIGN band** (`z`=1.5, H=12, h=12, E-TOUCH). On full TRAIN, the design's new primary band, they are **1,911** / **2,253** | REPRODUCES ON THE WRONG BAND — F3-13 |

**SPDR-018 scaling constants — all reproduce exactly.** 23,700 cells with finite MDE and `n > 0`;
powered subset (`at_parent_target_precision == True`) = **1,413** with median `k = MDE·√n` = **370.33**;
full-population median `k` = **947.9**; by horizon **568.98 / 955.18 / 1,383.68**; arm C = **18,632**.
Every value in §8's `k` block is correct.

| Run 2 | Status in run 3 | Evidence |
|---|---|---|
| **H4** §8 resolution arithmetic | **NOT CLOSED — half-fixed and now self-contradictory** | `k` moved to the full population and split by horizon exactly as required. But the required-`n` table does not use the stated denominator, and run 2's recomputed values were not adopted. **F3-01**, **F3-02** |
| **H5** no named mechanism | **CLOSED** | §1.1 names a falsifiable mechanism (fixed-quantile truncation of a *forecastable* conditional dispersion), states the prior against it from SPDR-018's own 5.3× `W/L` range, cites P-02 by name, and carries pre-registered expectations from reflection §5.6. Three of §5.6's five predictions are carried rather than all five — a residue, not a defect |
| **H6** three control blocks unfilled | **CLOSED** | SIDE-DERANGEMENT, AMBIENT-BASE and MAGNITUDE-MATCHED now each carry question / population + disjointness / bite-MDE / non-vacuity / expected outcome both ways / disclosure / destroy form. The known priors are retained and correctly labelled as priors |
| **H7** L-24 clauses 1–3 | **CLOSED on substance** | §6.1 adds thirds-stability (correctly justified as replacing the stability signal AMENDMENT-2 removed), exit-matched nulls with a demotion rule where matching is impossible, and a derived-not-asserted TRIPWIRE-1 threshold with a CI. See **F3-12** on how the block renders |
| **H8** 17-of-25 coverage undisclosed | **CLOSED** | §10 declares it with the eight symbols named; verified exact |
| **H9** HYP-D7's registered wording contradicted | **CLOSED in §2.2, NOT in the ledger** | §2.2's "Reconciliation with the registered `HYP-D7` wording" paragraph is exactly what run 2 asked for and is well argued. But it says the departure "is disclosed here **and in the amendment ledger**", and §14's AMENDMENT-1 does not mention HYP-D7 at all. **F3-14** |
| **M9** `r == 0` vs the 5 bps deadband; UNDECIDED | **MOSTLY CLOSED** | §3 now reads `\|r\| < 5 bps`; UNDECIDED is in the §2.1 grammar table. Still absent from §3's exclusion rule and from §12. **F3-11** |
| **M10** parity tolerance undeclared | **MOSTLY CLOSED** | §2.2 declares `\|Δ\| ≤ 1e-9` on `mean_r_h`, `p_momo`, `p_mr`, `n_decided` — all four exist in `expectancy_by_cell.parquet`, verified. G1 still asserts against "SPDR-014's **published** values" without naming that artifact. **F3-11** |
| **M11** cell cap contradicts the sweeps | **NOT CLOSED — verbatim unchanged** | **F3-05** |
| **M12** L1 changes the entry population | **NOT CLOSED — verbatim unchanged** | **F3-06** |
| **M13** CONVERSION-PIN omits `s_symbol` | **NOT CLOSED — verbatim unchanged** | **F3-03** |
| **M14** L-51 anchored to a retired population | **NOT CLOSED — verbatim unchanged** | **F3-07**. SPDR-019 fixed this in its §15; this design did not |
| **M15** pooled-primary inverts lane default | **NOT CLOSED — verbatim unchanged** | **F3-08** |
| **L6** golden traces carry no values | **NOT CLOSED — verbatim unchanged** | **F3-10** |
| **L7** plant curves absolute-bps only | **NOT CLOSED — verbatim unchanged** | **F3-10** |
| **L8** stale §14 opener; C7 absent from in-force list | **NOT CLOSED — verbatim unchanged** | **F3-09** |
| **L9** collapse fraction / M-5 | **NOT CLOSED — verbatim unchanged** | **F3-10** |

**Nine findings unchanged word for word.** Run 2 wrote: *"If they survive a second revision, escalate
to the operator rather than issuing a third identical REVISE."* It wrote that about H5/H6/H7, which
**were** closed. A different set of nine took their place. I am recording the pattern rather than the
individual instruction: this design's revisions have twice closed the findings that required new
writing and twice skipped the findings that required editing existing text.

---

### PART B — defects in the run-2 changes

#### F3-01 — HIGH — §8's required-`n` table does not follow from the formula printed one line above it; the numbers imply a divisor of ~47.8, not the stated 66.4

**Fails:** §8 (`Delta log R ~= Delta mean / ((1-p)*L); arm C: p 0.467, L 124.5 -> (1-p)*L ~= 66.4 bps`);
§8's footnote (`n ≈ (k / (Δ·66.4))²`); §8's required-`n` table; run-2 H4's required fix, which
supplied the correct values and was not adopted.

`(1−p)·L = 66.4` is right for arm C's stated terms — I verified `0.533 × 124.5 = 66.36`. The table
does not use it. Solving each printed cell backwards for the divisor gives **47.7–47.9** in all
twelve, and the printed values sit ~1.03× above SPDR-019's table, which is computed at **48.5** — the
median `(1−p)·L` on SPDR-018's *powered* subset. The table appears to have been carried over from
SPDR-019's basis and lightly perturbed rather than recomputed at 66.4.

| Δ`log R` | design, h=4 | correct at 66.4 | design, h=12 | correct at 66.4 | design, h=24 | correct at 66.4 |
|---|---:|---:|---:|---:|---:|---:|
| 0.15 | ~6,300 | **3,264** | ~17,700 | **9,193** | ~37,100 | **19,309** |
| 0.10 | ~14,200 | **7,343** | ~39,900 | **20,684** | ~83,400 | **43,436** |
| 0.075 | ~25,300 | **13,053** | ~70,800 | **36,772** | ~148,000 | **77,222** |
| 0.05 | ~57,000 | **29,371** | ~159,000 | **82,736** | ~333,000 | **173,745** |

The right-hand columns are run 2's own recomputation (H4 gave 29,405 / 82,874 / 173,908 at the 0.05
rung — agreeing with mine to 0.1%). The design cites run 2 as the source of the correction and then
prints numbers **1.93× above** what run 2 computed.

**A second, deeper basis problem sits underneath it, and it is the one worth fixing properly.** 66.4
is itself drawn from arm C's `at_parent_target_precision` subset — a *precision-selected* population,
which is the same P-25 / L-53 objection §8 raises against `k = 370` two lines earlier. Arm C's
`(1−p)·L` on the full emitted population is **90.81 (h=4) / 146.44 (h=12) / 212.57 (h=24)** — it
varies 2.3× with horizon, exactly as `k` does.

**The clean fix, and it removes the horizon split entirely.** The quantity that actually governs
resolution is dimensionless: `c = mde_log · √n`, where `mde_log = block_mde_bps / ((1−p)·L)` on the
cell's own terms. Measured on arm C, `c` is **flat across horizons** — the `k` and `(1−p)·L`
horizon-dependences cancel — but it **rises with `n`**, which is the block-dependence signature:

| `n` band | cells | `c` at h=4 | h=12 | h=24 |
|---|---:|---:|---:|---:|
| < 100 | 8,264 | 5.4 | 5.7 | 5.7 |
| 100–1k | 7,150 | 6.7 | 6.7 | 6.6 |
| 1k–5k | 2,791 | 7.4 | 7.3 | 7.3 |
| 5k–15k | 401 | 7.7 | 7.4 | 7.3 |
| **> 15k** — this design's target scale | 26 | 11.9 | 8.4 | 11.7 |

So one dimensionless constant replaces two horizon-split tables, it is portable across arms and
universes (L-50 clean), and it **measures** the dependence penalty instead of arguing about it. At
this design's target scale, `c ≈ 7.5–9`, giving `n = (c/Δ)²`: **0.10 → 5,600–8,100 · 0.075 →
10,000–14,400 · 0.05 → 22,500–32,400 · 0.03 → 62,500–90,000**.

*(Recorded so it is not re-derived a fourth time: run 2's H4 table reported these cells at
"0.079–0.101 at h=4 and 0.137–0.157 at h=12". That applies the h≈4 constant 66.4 across all three
horizons. Per cell, the three `n ≈ 21k` arm-C pooled cells realise **0.073–0.094** at every horizon —
flat, as the `c` table predicts.)*

**Required fix (quant-designer).** Replace the two horizon tables with the dimensionless `c` above,
stratified by `n` band; report the range across bases and state which conclusions are invariant
(**P-25**, already binding). Then reconcile §8's three resolution statements against it — they
currently disagree with each other and all three disagree with the artifact.

#### F3-02 — HIGH — the design's central viability claim survives verbatim and is refuted by its own text, twice, in the same section

**Fails:** §8 (*"a pooled cell … lands in the **20k–45k** range …, **which reaches `Δlog R = 0.05` and
approaches 0.03**"*) against (a) §8's own required-`n` table two paragraphs above, (b) §8's own
EXPECTED RESOLUTION table three paragraphs below, and (c) §8's own preceding paragraph; run-2 H4,
which named this exact sentence.

Three statements about the same population, in one section:

| Source | What it says about a 20k–45k cell |
|---|---|
| §8 required-`n` table | 0.05 needs **57,000** at h=4 and **159,000** at h=12 → 20k–45k reaches **neither** |
| §8 prose (line 460) | "**reaches 0.05 and approaches 0.03**" |
| §8 EXPECTED RESOLUTION | Z-VOL low `z`: **0.09–0.13** (h=4), **0.14–0.21** (h=12) → reaches neither |

And in the paragraph immediately above the prose claim, §8 states: *"**0 of 18,632 arm-C cells reach
0.03**. Any prediction that this design will 'approach 0.03' is refuted by the parent's own data
before it runs."* The design refutes its own claim on the page, and then makes it.

**On the substance, and in the design's favour:** measured against the `c` constant in F3-01, a
20k–45k cell resolves roughly **0.040–0.065**, so *"reaches 0.05"* is approximately right at the top
of that range — while the required-`n` table (too pessimistic ~1.8×) and the EXPECTED RESOLUTION
table (too pessimistic ~2×) are both wrong in the *other* direction. *"Approaches 0.03"* is wrong on
every basis; 0.03 needs ~62k–90k.

This matters because §8 immediately draws a conclusion from it: *"**Removing the selectivity gate is
what makes this experiment powered.**"* That is the design's viability argument, and it currently
rests on a sentence contradicted by both tables surrounding it.

**Required fix.** After F3-01's recomputation, state one resolution expectation and make all three
places agree with it — including deleting "approaches 0.03", which no basis supports.

#### F3-03 — HIGH — the CONVERSION-PIN still omits the frozen `s_symbol` that is the entire bps conversion; this is the EXP-025 seam P-15 exists for, unchanged from run 2

**Fails:** §7 CONVERSION-PIN (*"`s_hat` = LTF H1 Parkinson EWMA(λ=0.94) … **in bps** … IDENTICAL
object to SPDR-014's Z-VOL width — reused verbatim, never redefined"*); L-21 / P-15; run-2 M13.

I verified against the parent's own artifact. SPDR-014's Z-VOL width is `σ_bps,t = s_symbol ×
EWMA_park,t`. `EWMA_park` alone is **dimensionless**; `s_symbol` is the whole bps conversion, and it
is a per-symbol frozen constant in `SPDR-014/results/zvol_scale.json` — BTCUSDT **6,384.3**, ETHUSDT
**6,547.2**, SOLUSDT **6,215.6**, and NaN for the eight symbols of §10's coverage row. §7 names the
EWMA and calls it "in bps"; without `s_symbol` it is not.

P-15 exists because EXP-025 inflated a target 4.1× by asserting a divisor from memory at exactly this
seam, and this design's own §7 header cites L-21/P-15. A pin that omits the scale factor is not a
pin.

**Required fix.** State the divisor as `σ_bps,t = s_symbol × EWMA_park,t`; name
`SPDR-014/results/zvol_scale.json` as the source of the frozen `s_symbol`; state the eight-symbol NaN
gap in the same block (§7 says "All 25 symbols **or the gap is stated**" — §10 states it, §7 does
not); and add the `s_symbol` provenance to §12's unit assertions.

#### F3-04 — HIGH — the predeclared 20k–45k population holds for one of the three event types, on a design that forbids pooling them

**Fails:** §8 EXPECTED RESOLUTION (*"Z-VOL, low `z`, h=4/12/24 → **20k–45k**"*, no event-type split);
§4 L0 row (6 cells = 3 event types × 2 sides); §10 Events row (*"E-TOUCH, E-CLOSE, E-HORIZON —
separate, **never pooled**"*); §13 (*"**Pooling event types with each other**"* is refused).

Measured at the design's own primary cell (Z-VOL, `z` = 1.5, H = 12, h = 12):

| Event type | post-event rows | vs the predeclared 20k–45k |
|---|---:|---|
| **E-TOUCH** | **40,178** | in band |
| **E-CLOSE** | **6,484** | **~6× below** |
| **E-HORIZON** | **4,485** | **~7× below** |

Since event types are never pooled, two of the three primary strata carry roughly one seventh the
predeclared `n`, which at `c ≈ 7.4` puts them near **0.09–0.11** log units rather than the band's
implied range. The stratum table therefore mis-calibrates the reader on two thirds of the primary
grid — and under C7 that predeclaration is the B-5 protection (Part C).

The same omission runs through §8's viability sentence: *"a pooled cell at one `(z, event, h, source,
side)` combination lands in the 20k–45k range"* is true for E-TOUCH and false for the other two.

**Required fix.** Split the EXPECTED RESOLUTION table by event type, using the parent's measured
counts (they exist today — no estimate is needed), and restate the viability sentence per event type.

#### F3-05 — MEDIUM — §10's ≤ 120-cell cap contradicts §4 and §10's own sweeps; unchanged from run 2

**Fails:** §10 Cell count row; §4's stage table; §10's `z`(4) × sources(3) × `h`(3) × clocks(2) ×
events(3) × sides(2) sweep; `spdr-lane.md:35` (multiplicity disclosure is a lane requirement) and the
design's own "disclosed, not rationed".

"≤ 120 cells" holds only at one `(z, source, H, h, clock)` point (L0 6 + L1 3 + L2 5 + L3 2 + L4 ~44 +
L5 4 = 64). L0 alone across the declared sweeps is 3 sources × 2 clocks × 4 `z` × 3 `h` × 3 events ×
2 sides = **432**, before H alternatives and before the two verification bands; L4's ~44 devices
multiply through the same axes. **Fix the cap or fix the scope table** — a design on record as
disclosing rather than rationing must have the number right.

#### F3-06 — MEDIUM — L1 changes which zones breach, so Δ`log R`(L1) confounds an entry-population change with a capture effect; unchanged from run 2

**Fails:** §4 L1 row (*"ŝ used only to set the band width `z` as a ŝ-conditioned quantity rather than
a constant multiple"*); reflection §5.9's "same fixed signed entry" premise; §1 (*"the entry is fixed
and is not the research subject"*).

Making `z` a ŝ-conditioned quantity changes **which** zones breach and **when**. L1's Δ`log R` vs L0
is therefore measured across two different event populations, which is the one comparison the layer
protocol exists to avoid. L2 and L3 subset the population without changing the entry and are fine.

**Required fix.** Either re-specify L1 as a capture-parameter scaling on a fixed entry, or declare it
a distinct-entry arm with **its own L0 baseline**, so its delta is measured against its own
population.

#### F3-07 — MEDIUM — the L-51 selection check is still anchored to a population this design abolished, and still has no §12 row; unchanged from run 2

**Fails:** `chapter-06-governance.md:98` (binding: *"no powered subset's magnitudes may be read
without the three-number selection check (**L-51**)"*); §15 (*"the L-51 three-number check on every
**powered** subset (P-22)"*); §9 (retires the powered/unpowered classification); §12 (asserts **no**
adequacy flag anywhere, HARD; carries no L-51 row); run-2 M14.

As written the artifact has no population. **SPDR-019 solved this in its own §15** — re-anchoring to
"every subset the design or analysis reports separately (each selection layer's kept-vs-excluded
episodes, and cells above vs below median `mde50`)". Adopt that wording verbatim, add an L-51 row to
§12, and place it in the HARD list — or state in §12 why a missing selection check is INFORMATIVE on
a design whose L1/L2/L3 layers are all selections on a fat-tailed payoff distribution.

#### F3-08 — MEDIUM — pooled-primary still inverts a binding lane default with no predeclared consequence; unchanged from run 2

**Fails:** `spdr-lane.md:35` and `:93` (*"**A pooled figure is disclosure-only**"* (L-03)); §8
(*"like `SPDR-019`, this is a **pooled** experiment"*); §9 POOLED (*"the PRIMARY read **by
construction**"*).

I² is emitted, and nothing follows from any value of it. **Fix, requiring no threshold:** state that
the pooled line reverts to disclosure-only, per the lane default, if the emitted homogeneity
statistic does not support pooling, with the operator judging on the emitted value. Note also that
the pool is **17 symbols**, not 25 (§10), which bears directly on the homogeneity argument.

#### F3-09 — LOW — §14 opens by contradicting itself, and AMENDMENT-C7 is still missing from the in-force list; unchanged from run 2

§14 opens *"No amendments to this design. Registered 2026-07-28. running count: 0 looser / 0 tighter /
0 neutral"* and then lists six amendments closing at 2/2/2. The closing count is **correct** (LOOSER
1, 2; NEUTRAL 3, 4; TIGHTER 5, 6) and the L-23 streak note on the 2-looser run is adequate and
individually reasoned — both loosenings act only on population size, neither touches a fence,
causality rule, control or claim boundary, and I verified that independently. **Delete the stale
opener.** Separately, §14's closing in-force list reads U1, S1, C1, C2, C5, C6 — **C7 is absent**,
though it is registered (`cf-voldir-001.md:448`) and is the authority for §8, §9 and AMENDMENT-4.

#### F3-10 — LOW — three run-2 items unchanged verbatim

| Item | Where | Fix |
|---|---|---|
| Golden traces carry no hand-derived values (**L6**) | §11 | G1–G7 are procedures; nothing in them is falsifiable before the run. The parent's `post_event.parquet` makes G1 and G5 derivable **today** — add two concrete events with timestamp, input state, expected entry price/side, expected exit price/reason |
| Control plant curves are absolute-bps only (**L7**) | §6 | `+5/+10/+20/+40 bps` on a σ̂ = 73 bps universe. §7 already promises every effect in both bps and σ̂ units; L-50/P-21 requires the same of every precision threshold. This is the exact 5.6× silent loosening P-21 records, and it bites the moment a C1 cTrader leg (σ̂ = 13.03 bps) is authorised |
| Collapse-fraction disclosure (B-2) absent from all five control blocks; M-5 uncarried (**L9**) | §6, §12 | "collapse fraction" appears only in §12's INFORMATIVE list. Governance's standing rule that collapse fraction is **disclosure-only near a zero mean** (M-5) is squarely applicable to an object measured at gross break-even and is stated nowhere |

#### F3-11 — LOW — two partial closures with a residue each

- **UNDECIDED (run-2 M9).** Restored in §2.1's grammar table, which was the main gap. Still absent
  from §3's exclusion rule and from §12. *Fix:* add a §12 check asserting the UNDECIDED count is
  emitted and excluded from the signed residual — its incidence rises with `z`, i.e. across exactly
  the extended grid this design adds.
- **Parity artifact (run-2 M10).** The tolerance is now numeric and well justified (`|Δ| ≤ 1e-9`
  against SPDR-018's achieved 9.1e-13 on this same object) — good. G1 still asserts against
  "SPDR-014's **published** values". *Fix:* name `SPDR-014/results/expectancy_by_cell.parquet`, which
  I verified carries all four declared parity fields.

#### F3-12 — LOW — §6's code fences are off by one, so the L-24 clauses and both TRIPWIRE blocks are not declaration blocks as rendered

The fence opened before SIDE-DERANGEMENT is never closed before the `### 6.1` heading, so §6.1 and
§6.2's headings render **inside** code blocks while the L-24 clauses and the TRIPWIRE-1 / TRIPWIRE-2
bodies render as **prose**. Cosmetic in substance — every clause is present and correct — but this
design's contract is carried in its declaration blocks, and a HARD tripwire that is not inside one is
harder to trace mechanically. *Fix:* close the fence after MAGNITUDE-MATCHED's last line.

#### F3-13 — LOW — §8's Z-MAG / Z-MAG-SENS counts are DESIGN-band figures quoted inside a full-TRAIN forecast

`223` and `876` reproduce exactly — as the **DESIGN band** counts at `z`=1.5, H=12, h=12, E-TOUCH.
AMENDMENT-2 made **full TRAIN** the primary read, where the same cells carry **1,911** and **2,253**.
Quoting a DESIGN-band count in the section that predicts full-TRAIN resolution understates those
strata ~2.5×. Direction is conservative; fix the figures or name the band.

#### F3-14 — LOW — §2.2 claims the HYP-D7 departure is disclosed in the amendment ledger; it is not

§2.2's reconciliation paragraph is exactly what run 2 asked for and closes H9 on substance. It then
says the departure "is disclosed here **and in the amendment ledger**". §14's AMENDMENT-1 records the
gate removal and its direction but never mentions HYP-D7's registered wording. *Fix:* one clause in
AMENDMENT-1, or drop the cross-reference.

---

### PART C — does the current text deliver B-5's protection?

**Independent judgement: the run-2 remedies are architecturally sound and do not merely relocate the
problem — but on this design the calibration they depend on is materially wrong, so the protection
does not yet operate.**

The structural assessment is identical to the one I recorded on SPDR-019 and I will not repeat it at
length. In summary: the HARD schema check binding every `log R` to `ci_low` / `ci_high` / `ci_width` /
`block_mde` on the same row landed; the §13 refusal on aggregates lacking the resolution distribution
landed; per-stratum predeclaration landed. Run 2's proposed `finest_rung_detected` was **correctly
refused** — it requires privileging a detection rate, which is the retired cutoff renamed — and
`mde50`/`mde80`/`mde95` is the better answer, restoring countability and separability with no
privileged value. On the emission axis, C7's construction now has machinery behind it and the
"strengthened" claim is defensible. On the inference axis it remains overstated: what is enforced is
an *input* to the reader's judgement, not the judgement.

**Where this design differs from SPDR-019, and it differs badly.** C7 deliberately removed the
insulation that a boolean label provided: with no adequacy flag, the reader calibrates entirely
against §8's predeclared numbers. That makes correct predeclaration a **precondition** of C7 rather
than a nicety. On this design §8 currently issues **three mutually contradictory calibrations**
(F3-02), computes its table from a divisor it does not state (F3-01), and predeclares a population
that holds for one of three primary event types (F3-04). A reader told to expect 0.05 and a reader
told to expect 0.14 draw opposite inferences from an identical covering CI, and this design tells
them both, four paragraphs apart.

So the honest answer to *"do the run-2 remedies work, or do they relocate the problem"* is: **they
work, and this design has not yet supplied the input they need.** The failure is arithmetic, not
architecture — which is good news, because arithmetic is cheap to fix and does not require
reintroducing a threshold.

**What would deliver B-5's protection here — no threshold in any of them:**

1. **Fix §8 per F3-01, F3-02 and F3-04** — one basis, dimensionless, `n`-stratified, split by event
   type, with all three statements in §8 agreeing. Adequacy cannot be "the reader's judgement"
   against a prediction the design itself refutes on the page.
2. **Predeclare at the granularity the design actually reports.** §8 predeclares by source and `z`;
   §4/§10 report by event type × side × `h` × `z` × source × clock. A predeclaration coarser than the
   reporting unit cannot calibrate a reader for the rows they will read.
3. **Make the predeclaration auditable after the run** — one HARD schema check that each stratum's
   **predeclared** expected `mde50` and its **realised** `mde50` ship on the same row of the emitted
   stratum table. It admits, excludes, labels and ranks nothing, so it is C7-clean; it converts an
   unfalsifiable forecast into a checkable record. It is the cheapest thing that would have caught
   F3-01, F3-02 and F3-04 at run time rather than at a third review.
4. **Carry all five of reflection §5.6's predictions**, not three. §1.1's pre-registered expectation
   block is the strongest B-5 instrument this design has — a prediction made before the run cannot be
   reinterpreted after it — and it costs nothing to complete.

---

### Independent verification of the operator's named checks

| Check | Result |
|---|---|
| **Exact mirror, slope 1, everywhere a target is stated** | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` in §1, §5, §12, G5, G6, §13. `0.9408` appears **zero** times; §5 refuses the fitted-slope form as a target by description, §12 makes a fitted-slope residual anywhere a **hard failure**, §13 refuses it, and G6 exists to make audit A1 non-repeatable. The refusal is present and correct without the number — not a finding |
| **Cost enters no estimand, threshold, band or comparison (C5)** | **CLEAN.** Traced every cost mention: header NOTE, §5 `DISCLOSED REFERENCE ONLY`, §7 ("no read in this design is compared against it"; sigma-unit effects never compared to the floor), §12 HARD cost-isolation row with `p_be_net` flagged `DISCLOSURE_ONLY`, §13 first bullet, §15 column flag. `p_be_net` is disclosure-only throughout |
| **No `powered`/`unpowered`/`at_target`/`NOT_RESOLVABLE` flag survives** | **CLEAN as an emitted flag**; §12 asserts the absence HARD and §9/§13 refuse it. Every other use of "powered" is a historical reference to SPDR-018's own subset (§1, §8, §14) **except §15's L-51 anchor** — F3-07, which matters because it leaves a governance-mandatory check with no population, not because a flag is emitted |
| **No single canonical adequacy threshold under another name** | **CLEAN.** The ladder `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` matches C7's registered set exactly; `mde50`/`mde80`/`mde95` are three points of one curve, explicitly non-canonical; nothing is admitted, excluded, labelled or ranked by them; §12 asserts no single canonical MDE threshold appears in code |
| **Nothing filters, weights, labels or ranks on `p_event`** | **CLEAN — swept every occurrence** (§2.2, §5, §8, §9, §10, §11 G2, §12, §13, §15). It is emitted per cell per event type as a covariate and dose-response axis; §12 asserts it does not filter, gate or label; G2 exists specifically to prove no code path applies it; §13 refuses any selectivity gate, breach-rate cutoff or cell exclusion on it. Band labels are CI-relative only. **This is the cleanest part of the document** |
| **Amendment ledger direction** | **Closing count 2/2/2 is correct** and the L-23 note on the 2-looser streak is adequate and individually reasoned. Both loosenings act only on population size; neither touches a fence, causality rule, control or claim boundary — verified against §10, §12, §13. Defects are the stale opener and the missing C7 (F3-09) and the missing HYP-D7 clause (F3-14), not the count |
| **L-28 derangements** | **CLEAN.** SIDE-DERANGEMENT and ENTRY-TIMING DERANGEMENT both declare `DERANGEMENT (zero fixed points, asserted and counted)`; §12 asserts a measured fixed-point count of 0; AMBIENT-BASE and MAGNITUDE-MATCHED correctly declare `N/A (a matched comparator, not a permutation)` |
| **L-52 / P-23 check integrity** | **CLEAN.** Expected HARD-check **count** asserted and reconciled **by name**; every check depends on an emitted artifact; determinism unconditional at `--jobs > 1` independent of `--resume`; no required check in a manual post-step |
| **P-24 comparator disclosure** | **CLEAN, and now complete.** All three comparator blocks carry the comparator's own mean, null quantiles **and** plant curve with every percentile; a bare percentile is explicitly refused. The known priors (side-derangement −12.221 bps at pct 0.0065; `mag_high` at pct 0.46; ambient's offsetting-terms result) are correctly labelled priors from SPDR-018's population rather than results on this one |
| **L-24 (all three clauses)** | **PRESENT and correct in substance** — thirds-stability, exit-matched nulls with a demotion rule, derived tripwire threshold with a CI. See F3-12 on rendering |
| **L-21 / P-15 unit pin** | **FAILS — F3-03.** The divisor omits `s_symbol`, which is the entire bps conversion |
| **L-50 / P-21 threshold portability** | **PARTIAL.** All bands and rungs are dimensionless log units — clean. The control plant curves remain absolute bps (F3-10) |
| **Bands partition** | **CLEAN.** `ci_low > 0` / spans 0 / `ci_high < 0` is exhaustive and mutually exclusive |
| **B-4 / B-9 object identity** | **CLEAN, and better than the parent.** Conditioning at the breach bar; E-TOUCH / E-CLOSE / E-HORIZON kept as separate commitment states and never pooled; one open episode per symbol with suppression counted; block ≥ `h` |
| **Parent fidelity** | **CLEAN.** §2.1's grammar table is faithful row by row; the 5 bps deadband and UNDECIDED rule are restored; the parity tolerance is numeric and the four parity fields all exist in the parent's emission. §2.3's discharge of the DESIGN→CONFIRM sign flip is correct and needs no re-litigation |
| **Holdout / XENA / family action / TEST** | **CLEAN.** §10 holdout never queried; §12 asserts zero queries ≥ 2025-01-08; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| **SPREAD-COST-DISCLOSURE** | **CLEAN.** All five fields verbatim |
| `check_no_local_accounting` | **DEFERRED** to post-implementation QA; §12 declares the check |
| **Start gate** | **STILL FLAGGED.** `reflection-inputs.md` §9's operator decision remains unsigned. Design registration does not require it; **execution does** |

---

### Verdict and routing

**REVISE.** All findings route to **`quant-designer`**; no implementation exists.

**Nothing rises to REJECT.** No holdout contact, no causality violation, no missing tripwire, no cost
smuggling, no fitted-slope target, no unapproved silent deviation. The `p_event` quarantine, the
exact mirror and the cost isolation are intact and are the strongest parts of the document.

**Fit to authorise implementation (`screen_code/`): NO.** Four findings specify behaviour the code
must implement and are unresolved: **F3-03** (the unit pin is incomplete, and the omitted term is the
whole bps conversion — this is the seam that cost EXP-025 a 4.1× target error), **F3-06** (L1's
estimand confounds an entry-population change with a capture effect), **F3-05** (the cell grid is
undefined — the cap and the sweeps differ by a factor of several), and **F3-07** (a
governance-mandatory check has no population). §8 must also be made self-consistent before it can
serve as the predeclaration C7 makes load-bearing.

**A process note for the operator, offered once and not repeated.** Run 2 asked that findings
surviving a second revision be escalated rather than re-issued. Its three HIGH findings that required
*new writing* — the named mechanism, the control blocks, the L-24 clauses — were all closed, and
closed well. Nine findings that required *editing existing text* are unchanged word for word across
both revisions, and three of them (F3-05, F3-06, F3-07) are implementation-blocking. That is a
pattern worth naming at the gate rather than a third list of the same items.

**Execution remains a separate operator gate regardless of this verdict**, and carries the standing
unsigned-start-gate flag.

---

## QA run 4 — 2026-07-29T00:00Z — mode: subagent — HEAD 42934ef91adb15a4aac2625b323021abf9ad94e5 (dirty: `SPDR-019/design.md`, `SPDR-019/qa-review.md`, `SPDR-020/design.md`, `SPDR-020/qa-review.md`)

**Target:** `python/experiments/SPDR-020/design.md` (1,027 lines)
**Stage:** DESIGN-STAGE. `screen_code/` does not exist; expected, not a finding.
**Independence:** this reviewer authored neither the design nor runs 1–3, and made no edit to any
file other than this append. Run 3 was written by the session that then applied the fixes, so every
run-3 number and every run-3 remedy below was re-derived from the artifacts with my own code before
being accepted. Where run 3 and I disagree I show both.

**Verdict: REVISE.** Not fit to authorise implementation.

Findings: **4 HIGH · 4 MEDIUM · 8 LOW.**

**Plain reading.** The run-3 fixes are, on the whole, real fixes and not restatements. Twelve of the
fourteen run-3 findings are genuinely closed and I verified each against the artifact rather than
against run 3's description of it: the required-`n` table now reproduces exactly from its own
formula, the withdrawn "approaches 0.03" claim is gone, the unit pin is complete and its three named
`s_symbol` values are exact, the code fences are balanced, the ledger count is right, and all five
reflection predictions are carried. **But §8's population arithmetic — the one input AMENDMENT-C7
made load-bearing — is wrong again, in a new way, and in the optimistic direction.** The E-TOUCH
count of 40,178 is a row count spanning three of the parent's policy arms and two clocks; SPDR-018's
own arm-C emission at exactly this stratum carries `n` = **15,041** and **15,331**. The header count
86,831 and the split beneath it (which sums to 51,147) come from different filters. And the new
20-hour block is an invented number whose stated derivation is contradicted by SPDR-018's own design,
which used a **24-hour** minimum block — so AMENDMENT-8, declared TIGHTER, is looser than the basis
`c` was measured on.

---

### PART A — closure of the run-3 findings, re-derived independently

All re-derivations from `SPDR-018/results/analyst_per_cell_magnitudes.parquet` and
`SPDR-014/results/{zones,post_event,expectancy_by_cell}.parquet`, `zvol_scale.json`.

| Run-3 finding | Status | Independent evidence |
|---|---|---|
| **F3-01** required-`n` table implied divisor ~47.8 | **CLOSED** | The old table is gone. Every cell of the new `n = (c/Δ)²` table reproduces exactly: c=7.5 → 2,500 / 5,625 / 10,000 / 22,500 / 62,500; c=9 → 3,600 / 8,100 / 14,400 / 32,400 / 90,000; c=11.9 → 6,294 / 14,161 / 25,172 / 56,644 / 157,378. Printed values match to rounding |
| **F3-02** "reaches 0.05 and approaches 0.03" | **CLOSED** | The sentence is explicitly withdrawn in §8 and the withdrawal is recorded in AMENDMENT-7. `grep` finds no surviving claim. `0 of 18,632` verified: the only arm-C cells with `mde_log ≤ 0.03` are three degenerate `n`=2, `p`=0 cells, minimum **0.010148** (design says 0.0101) |
| **F3-03** CONVERSION-PIN omits `s_symbol` | **CLOSED, and exact** | §7 now states `sigma_bps = s_symbol × EWMA_park`, names `zvol_scale.json`, adds a §12 provenance row. Verified from the artifact: BTCUSDT **6384.32135**, ETHUSDT **6547.22311**, SOLUSDT **6215.59765**; range **4,606.42 (INJUSDT) – 7,338.34 (LINKUSDT)**; exactly 17 finite and 8 NaN, and the eight are exactly ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH, 1000RATS |
| **F3-04** predeclaration not split by event type | **PARTIAL — split added, E-TOUCH number wrong** | See **F4-01** |
| **F3-05** ≤120-cell cap | **MOSTLY CLOSED** | Primary arithmetic verifies exactly: base points `z`(4)×`h`(3)×event(3)×side(2) = **72**; layer variants 1+4+5+2+4 = **16** → 1,152; L4 (6+4+2)=12 × 72 = 864 plus hold 6 × 24 = 144 → **1,008**; total **2,160**. §4's L4 count 3+3+2+2+3+3+1+1 = **18** reconciles with §10's 12+6. The **co-report** figure does not — **F4-07** |
| **F3-06** L1 confounds entry change with capture | **PARTIAL — remedied by a route that departs from §5.9** | See **F4-06** |
| **F3-07** L-51 anchored to a retired population | **CLOSED, and correctly** | Re-anchored to "every selected subset", §12 row added, HARD list. **Not** contrary to INFR-016: §12 states it is HARD on presence and form only, adjudicates no value, and admits/excludes/labels/ranks nothing. `chapter-06-governance.md:99-100` makes the check mandatory, and a silently-skipped check is indistinguishable from a passed one. Defensible |
| **F3-08** pooled-primary inverts the lane default | **CLOSED** | §9 POOLED now reverts to `spdr-lane.md:35` disclosure-only if the emitted homogeneity statistic does not support pooling, operator judging, no cutoff written |
| **F3-09** stale §14 opener; C7 absent | **CLOSED** | Opener deleted; C7 present in the in-force list with its NEUTRAL label and named as the authority for §8/§9/AMENDMENT-4 |
| **F3-10** golden values / σ̂ plant curves / collapse fraction + M-5 | **CLOSED** | G1/G2 carry hand-derived values (verified below); plant curves carry σ̂ units and the conversions are right (5/73.00 = 0.0685, 10 → 0.1370, 20 → 0.2740, 40 → 0.5479 vs the stated 0.068/0.137/0.274/0.548); COLLAPSE FRACTION (B-2) + M-5 block added and correctly kept out of the HARD list |
| **F3-11** UNDECIDED in §3/§12; parity artifact named | **CLOSED** | §3's exclusion rule and a §12 row both carry UNDECIDED; §11 names `expectancy_by_cell.parquet`. All four declared parity fields — `mean_r_h`, `p_momo`, `p_mr`, `n_decided` — exist in that file. `1e-9` is comfortably achievable against SPDR-018's 9.1e-13 |
| **F3-12** §6 code fences off by one | **CLOSED** | 32 fences in the file, all balanced. §6's four blocks close at 304–338, 342–396, 400–415, 419–441. Nothing swallowed, nothing duplicated; the L-24 clauses and both TRIPWIREs render as declaration blocks |
| **F3-13** Z-MAG counts on the wrong band | **CLOSED on the band** | §8 now quotes ~1.9k / ~2.3k. Verified full-TRAIN: **1,911** and **2,253**. See **F4-14** on what 1,911 actually counts |
| **F3-14** HYP-D7 departure absent from the ledger | **CLOSED** | AMENDMENT-1 now carries a REGISTERED-WORDING DEPARTURE clause naming HYP-D7's "with a band that actually selects", the intent-vs-literal distinction, and the invitation to amend the registry |
| Run-3 Part C item 4 — carry all five §5.6 predictions | **CLOSED** | All five are in §1.1 and each is faithful to the reflection's wording. But prediction 1's attachment to L1 is now wrong — **F4-06** |

**Run-3's own numbers, re-derived.** The `k` block reproduces: full-population median `k = MDE·√n` =
**949.6** (run 3: 947.9); by horizon **570.7 / 956.2 / 1,384.9** (run 3: 568.98 / 955.18 / 1,383.68;
the small gap is a `(1−p)·L > 0` filter, immaterial at the printed precision of 569 / 955 / 1,384).
Powered subset **1,413** cells, median `k` **370.33**, median `(1−p)·L` **48.54** — all exact. Arm C's
full-population `(1−p)·L` by horizon **90.81 / 146.44 / 212.57** — exact.

**The n-band `c` table reproduces to the printed digit**, which is the strongest single fact in the
revision:

| `n` band | design | re-derived (median per-cell `c`, arm C, h=4/12/24) |
|---|---|---|
| < 100 | 5.4 / 5.7 / 5.7 | **5.391 / 5.732 / 5.675** |
| 100–1k | 6.7 / 6.7 / 6.6 | **6.676 / 6.675 / 6.584** |
| 1k–5k | 7.4 / 7.3 / 7.3 | **7.424 / 7.320 / 7.316** |
| 5k–15k | 7.7 / 7.4 / 7.3 | **7.672 / 7.359 / 7.327** |
| > 15k | 11.9 / 8.4 / 11.7 | **11.855 / 8.363 / 11.744** |

**Population and coverage** all reproduce: zones by `z` **234,785 / 261,305 / 253,366**; post-event
by `z` **190,467 / 211,872 / 158,313**; 17-of-25 Z-VOL coverage with the eight named symbols exact;
`n ≥ 10,000` arm-C cells realise **0.05343–0.10680** (design: 0.053–0.107); the three largest cells
(`n` = 20,977 / 20,572 / 20,279) realise **0.0727–0.0945** (design: 0.073–0.094).

---

### PART B — defects, including four introduced or left open by the run-3 changes

#### F4-01 — HIGH — the E-TOUCH population is a row count over three policy arms and two clocks; the claim that both side arms use it is refuted by SPDR-018's own emission at this exact stratum

**Fails:** §8 (*"E-TOUCH **40,178**"*, *"expected `mde50` 0.042–0.060"*); §8 (*"The MOMO and MR arms
each use the full event count for their event type (a side arm re-signs `r_h`; it does not partition
the population), so the counts above apply to both arms"*); §8 EXPECTED RESOLUTION (*"Z-VOL z=1.5,
E-TOUCH (either side arm) ~40k"*); §9's B-5 argument, which makes this table the protection.

The parent's `post_event.parquet` carries a `policy` column with three values that **partition the
rows**. At `Z-VOL, z=1.5, H=12, h=12`:

| | rows | P-NONE | P-MOMO | P-MR | H1 | H4 |
|---|---:|---:|---:|---:|---:|---:|
| E-TOUCH | **40,178** | 9,806 | **15,041** | **15,331** | 37,233 | 2,945 |
| E-CLOSE | 6,484 | 6,484 | 0 | 0 | 6,484 | 0 |
| E-HORIZON | 4,485 | 4,485 | 0 | 0 | 4,485 | 0 |

E-CLOSE and E-HORIZON are single-policy, H1-only, and their counts are clean — **those two rows of
the table are correct.** E-TOUCH is not. The 40,178 figure sums three policy arms and both clocks.

The decisive check is that the parent's per-policy counts appear **verbatim** as `gross_n` in
SPDR-018's arm-C pooled cells at this stratum:

```
arm C, __POOLED__, TRAIN, H1, Z-VOL, z=1.5, H=12, h=12, E-TOUCH
    gross_n 15,041   (1-p)L 186.76   mde_log 0.06819   c 8.363
    gross_n 15,331   (1-p)L 189.93   mde_log 0.05343   c 6.615
```

So on the design's own parent arm, at the design's own primary cell, this stratum's `n` is **~15k,
not ~40k** — an overstatement of **2.7×** — and the realised `mde_log` is **0.053–0.068**, not the
predeclared 0.042–0.060. Whatever reading is intended, 40,178 is not it: the unique breach-event
count on H1 at this cell is **33,968**, also not 40,178.

The prose claim is separately unsupported. "A side arm re-signs `r_h`; it does not partition the
population" is true of a screen that generates both sides on every event — but this design asserts it
**inherits SPDR-014's grammar unchanged** and asserts parent parity, and the parent's P-MOMO and
P-MR sets are largely **disjoint** (15,041 and 15,331 with only 2,241 in common). Either the design
departs from the parent here — in which case that is an undeclared re-specification against §2.1's
"inherited, not re-specified" and the §12 parity check — or the arms are partitioned and the counts
must be per-arm. The design cannot have both.

**Required fix (quant-designer).** Recompute the per-event-type table on the design's own primary
clock (H1) and its own object, per side arm; state which policy/side construction the figure counts;
and re-derive the expected `mde50` column from the corrected `n`. State explicitly whether both
arms are generated on every event (a departure from the parent's emission, needing a ledger row) or
inherited as partitioned arms.

#### F4-02 — HIGH — §8's header count and the split beneath it come from different filters and differ by 35,684

**Fails:** §8 (*"At `z = 1.5`, `Z-VOL`, `H = 12`, `h = 12` the parent emitted **86,831** post-event
rows across event types; split, and read against the `c` table above"*).

- `Z-VOL, z=1.5, H=12, h=12` → **51,147** rows. The printed split (40,178 + 6,484 + 4,485) sums to
  exactly **51,147**, confirming the split is on this filter.
- **86,831** is `Z-VOL, z=1.5, h=12` across **all three `H`** (4, 12, 24).

So the sentence's stated filter produces one number and its own split produces another. This is the
same numerator/denominator-from-different-populations failure that §8's "WHY THE EARLIER FORMS ARE
WITHDRAWN" block was written to eliminate, re-committed one paragraph later. Run 3 recorded
"Z-VOL, `z`=1.5, `h`=12 post-event rows ~86.8k → 86,831 REPRODUCES" — that reproduction is correct
for run 3's own filter (`h`=12, all `H`) and does **not** validate the design's sentence, which adds
`H = 12`.

**Required fix.** State one filter and make the header and the split agree on it.

#### F4-03 — HIGH — the 20-hour block is an invented number, and its stated derivation is contradicted by SPDR-018's own design; AMENDMENT-8 is declared TIGHTER but is looser

**Fails:** §1 MECHANISM, §3, §6 MIRROR-NULL, §8 RESOLUTION, §12 Block rule, AMENDMENT-8 (all seven
occurrences of *"`block >= max(h in hours, 20 hours)`"*); §8's transport claim (*"20 hours … is also
the basis on which `c` was measured (SPDR-018 H1 cells, where bars and hours coincide), so `c`
transports only under this rule"*); AMENDMENT-C7's prohibition on canonical numbers picked rather
than derived; L-23 direction labelling.

`c` is measured entirely from SPDR-018's emitted `gross_block_mde_mean_bps`. **SPDR-018/design.md:248
sets the block: *"minimum block = 1 day = 24 H1 bars ≥ every horizon in scope"*.** The basis `c` was
measured on is therefore **24 hours**, not 20. A 20-hour minimum is **looser** than that basis: on H1
it binds at `h`=4 and `h`=12, giving a block 20/24 = 0.83× the parent's, which narrows CIs and
understates dependence — the anti-conservative direction, and precisely the direction the transport
claim asserts it protects against.

This makes "20 hours" an invented number with a false stated derivation, and makes AMENDMENT-8's
**TIGHTER** label wrong at two of the three horizons. The design's own defence — that 20 hours is a
dependence-matching parameter and not an effect threshold — is correct in kind and does not rescue
it: a dependence-matching parameter must still match the dependence of the basis it transports.

**Required fix.** State the block as `≥ max(h in hours, 24 hours)` — one calendar day, the parent's
own rule, derived rather than picked — and relabel AMENDMENT-8 accordingly. A derived alternative
(the realised autocorrelation length on TRAIN, with a CI, as §6.1's L-24.3 already requires of
TRIPWIRE-1) is also acceptable and would be stronger.

#### F4-04 — HIGH — the `> 15k` band is 26 rows but only 8 distinct cells, 12 of them at a `z` this design drops; the `8.4` the whole basis-range conclusion turns on is a single cell

**Fails:** §8 (*"`> 15k` … 26 … 11.9 / 8.4 / 11.7 ← this design's E-TOUCH strata"*); §8 BASIS RANGE
(*"the conclusion NOT invariant is the 0.05 rung — reachable at `c` = 8.4 on a 40k cell, NOT
reachable at `c` = 11.9"*); §8 EXPECTED RESOLUTION; §8's own *"`c` is FLAT ACROSS HORIZONS"*.

Enumerating the 26 rows: they cover **8 distinct `n` values** (20,977 / 20,572 / 20,279 / 19,942 /
19,383 / 18,339 / 15,331 / 15,041), each appearing 3–4 times across horizons and duplicated
`residue_item` entries. Of the 26, **18 are at `z` = 1.0** — the level this design explicitly drops —
or are `H`-pooled (`H` = NaN) rather than the design's `H` = 12.

Three consequences:

1. **`c` is not flat across horizons in the band the design actually uses.** 11.9 / 8.4 / 11.7 is a
   **1.42× spread**, in the same section that asserts flatness as the reason the horizon axis was
   deleted. The flatness holds on the pooled population (6.53 / 6.64 / 6.52) and fails here.
2. **The `8.4` is one cell.** It is the `n` = 15,041 cell (`c` = 8.3628) replicated three times; it
   is the `h` = 12 median only because the band has 9 rows at that horizon. The 11.9 / 8.4 gap is a
   **composition** artifact, not a horizon effect — so "basis-dependent: yes at 8.4, no at 11.9" is
   not a basis range, it is sampling noise in a 26-row stratum.
3. The design's own primary stratum is *in* that band, and its two cells give `c` = **6.62 and
   8.36** — materially finer than the 11.9 the band's other horizons report.

**Required fix.** Anchor the E-TOUCH basis on the cells that *are* this design's stratum (Z-VOL,
`z` = 1.5, `H` = 12, `h` = 12, E-TOUCH, pooled: `c` = 6.62–8.36) or on the 5k–15k band (401 cells,
`c` = 7.3–7.7), and state the thinness of the `>15k` band wherever it is quoted. P-25 requires the
basis range; it does not license a range drawn from 8 distinct cells at the wrong `z`.

#### F4-05 — MEDIUM — §4.1's phase-(b) trigger contradicts binding AMENDMENT-C6, with no ledger row

**Fails:** `cf-voldir-001.md:430ff` AMENDMENT-C6 (*"the (b) trigger is **pre-declared before (a)
runs** (deciding afterwards what counted as promising is optional stopping)"*); reflection §5.9
(*"Two phases, both pre-declared"*); §4.1 (*"**Trigger: the operator decides, on the full phase-(a)
report.** No numeric cutoff is written here"*); §14's in-force list, which carries C6 as TIGHTER.

C6 is listed as in force and its scope clause is honoured in full (§4.1's scope is fixed,
individually-flat layers retained, interaction estimand correct — verified against C6 verbatim). Its
**trigger** clause is not: deciding on the full report afterwards is the exact construction C6 names
as optional stopping. The design's reasoning — that a numeric cutoff is the wrong shape under
INFR-016 — is a real tension and may well be the right call, but it is a **departure from an in-force
binding amendment** and §14 records no row for it, while §14 does record a departure row for HYP-D7's
wording. Either declare the departure with its direction, or state a non-numeric pre-declared trigger
(e.g. "phase (b) runs unless every L1–L4 layer's CI covers the mirror on every event type").

#### F4-06 — MEDIUM — AMENDMENT-10 fixes F3-06 by a route that departs from binding reflection §5.9, and it breaks §1.1's prediction 1

**Fails:** reflection §5.9 (BINDING; *"Each layer is characterised alone, against **the same fixed
signed entry**"*; L1 row: *"ŝ used **only** to set parameter magnitudes; no state gate, no swing
gate"*); §4's L1 row and the "Why L1 is scored against its own baseline" paragraph; §1.1 prediction 1
(*"**ŝ-scaling every capture parameter** leaves `log R` unchanged … This is the direct predeclared
expectation for the **L1** layer"*); AMENDMENT-10's TIGHTER label.

Run 3 diagnosed the confound correctly. §5.9's own remedy, however, is the *first* of the two options
run 3 offered — re-specify L1 as capture-parameter scaling on the fixed entry — because that is what
§5.9's L1 row literally specifies. The design took the second: keep the band-width form and add a
second baseline. That is a **scope expansion** (an extra baseline cell, counted in §10's L1 = 4) and
a **change of estimand** for L1 (Δ against a different population), against a directive whose first
sentence is "against the same fixed signed entry". The isolation argument in §4 is sound on its own
terms; the problem is that it is an argument for a construction §5.9 does not permit, recorded as
TIGHTER with no departure disclosure.

It also creates a live inconsistency: §1.1 predeclares "ŝ-scaling every capture **parameter** leaves
`log R` unchanged" as *the direct predeclared expectation for L1* — but the design's L1 scales the
**band width**, not capture parameters. Under this L1, prediction 1 is not tested by any layer.
Re-specifying L1 per §5.9 closes both halves at once.

#### F4-07 — MEDIUM — §10's "≈ 13,000 cells with co-reports" does not follow from the axes it names

**Fails:** §10 Cell count (*"Including the declared co-reports (H4 clock, `Z-MAG`, `Z-MAG-SENS`, the
parent's `H` alternatives) the emission reaches **≈ 13,000 cells***"); `spdr-lane.md:35` (multiplicity
disclosed); the design's own *"Counted out, not capped"*.

The primary total 2,160 is computed at `Z-VOL × H1 × H=12`. The four named co-report axes multiply it
by clock (2) × source (3) × `H` alternatives (3) = **18** → **38,880**. 13,000 is 2,160 × 6, i.e. the
`H` alternatives are listed and then not multiplied. Direction is anti-conservative (it understates
multiplicity ~3×) on a design that explicitly repudiated its previous under-count. Fix the number or
drop `H` alternatives from the declared co-reports.

*(For the record, neither figure conflicts with the "≤ 8 plots" complexity freeze — that row bounds
modules and plots, not cells, and a large disclosure-classed emission is what `spdr-lane.md:35`
contemplates provided the count is right.)*

#### F4-08 — MEDIUM — the predeclared-vs-realised same-row check is inert where it matters most

**Fails:** §8 B-5 ENFORCEMENT clause 4 and §12's Predeclared-vs-realised row (*"Nothing is admitted,
excluded, labelled or ranked by the comparison"*); §9 (*"§8's predeclared resolution table **IS** the
protection"*).

Putting the pair on one row is right and C7-clean, and I would not ask for anything to *act* on it.
But nothing directs a reader to it either: §13's aggregate-disclosure refusal requires an aggregate to
carry median `mde50` and the count below each rung, and does **not** require it to carry the
predeclared/realised gap; `analysis.md` is not required to report the gap; no golden trace touches it.
Concretely: under F4-01 the emission would ship "predeclared `n` 40,000 / realised `n` ~15,000" on a
row, and nothing in the design causes anyone to read those two numbers together.

**Fix, no threshold required.** Extend §13's aggregate refusal so that any aggregate statement over
cells must also carry the predeclared-vs-realised `mde50` gap for the strata it spans, and name the
gap as a required line in `analysis.md`.

#### F4-09 — LOW — G1 and G2 do not name the parent's `policy`, and the parent emits three rows for G1 whose `exit_reason` differs between them

Every stated G1 value verifies exactly against `post_event.parquet` (ETHUSDT, H1, DESIGN, Z-VOL,
`z`=1.5, `H`=12, E-TOUCH, `h`=12, first decided event): `anchor_idx` **61**, `event_idx` **61**,
`entry_idx` **62**, `exit_idx` **74**, `entry_ts` **2022-07-17T14:00:00Z**, `exit_ts`
**2022-07-18T02:00:00Z**, `side` **−1**, `label` **MR**, `r_h` **−157.371411** bps. That is a good,
falsifiable trace and closes F3-10 on substance.

But the parent emits **three** rows for that event, one per policy, and `exit_reason` differs across
them — **P-NONE: NaN · P-MOMO: `stop` · P-MR: `time`**. The design's stated `exit_reason = time` is
reachable **only** on the P-MR row. Since §12 will assert code output against these values to
`|d| ≤ 1e-9`, the trace must name the policy/side arm it refers to, or the assertion is ambiguous by
construction. Same for G2: **0.994872 / 1.000000** are the **P-NONE** rows (`n_events` 194 / 249,
verified exactly); the P-MOMO rows are 0.995272 / 0.996324 and the P-MR rows 0.995413 / 1.000000.

#### F4-10 — LOW — the gate denominator 511,350 does not reproduce; the numerator and the percentage do

`p_event ≤ 0.60` retains **41,739** Z-VOL post-event rows — exact. The population carrying a
`p_event` is **510,720** (Z-VOL post-event rows on H1; the 2,945 H4 rows carry none), against the
design's 511,350. 91.8% discarded is right either way (91.83% vs 91.84%). Run 3 recorded 511,350 as
reproducing; I cannot reproduce it on any filter I tried.

#### F4-11 — LOW — §8 uses two different estimators of `c` in one block without saying so

The definition is per-cell (`c = mde_log · √n`). The horizon line `c = k / (1−p)·L → 6.27 / 6.52 /
6.51` is a **ratio of medians**; the median of per-cell `c` is **6.53 / 6.64 / 6.52**. The n-band
table is the per-cell form (it reproduces exactly). Both are defensible, the gap is ~4%, and no
conclusion turns on it — but the definitional line and the line beneath it compute different things.

#### F4-12 — LOW — the n-band table's cell counts include cells that contribute no `c`

The printed counts (8,264 / 7,150 / 2,791 / 401 / 26) sum to 18,632 = arm-C cells with finite MDE and
`n` > 0. **153 of those have `(1−p)·L ≤ 0`** (`p` = 1 or `L` = 0) and cannot produce a `c`. On the
`(1−p)·L > 0` population the counts are 8,078 / 7,180 / 2,794 / 401 / 26. The medians are unaffected;
the count column overstates the basis.

#### F4-13 — LOW — the per-symbol row does not use the `c` band table it declares, and its `n` range is not the parent's

§8 EXPECTED RESOLUTION: *"per-symbol (any stratum) — parent `n` 10–517 → 0.24 to ~1.8"*. 0.24 at
`n` = 517 implies `c` = 5.4, but `n` = 517 sits in the **100–1k** band where the design's own table
gives `c` = 6.6–6.7 → **0.29**. Separately, at the design's primary stratum the parent's per-symbol
`n_decided` runs **0 to 1,158** (median 231, 150 cells, several at 0), not 10–517.

#### F4-14 — LOW — the Z-MAG full-TRAIN count carries the same three-policy conflation as F4-01

**1,911** reproduces exactly, and is P-MOMO 669 + P-MR 667 + P-NONE 575. **2,253** (Z-MAG-SENS)
reproduces and is single-policy, so it is clean. Same defect as F4-01, one seventh the stakes.

#### F4-15 — LOW — "identical on H1 and H4" is false of the block value; it is true only of the rule

`block ≥ max(h in hours, 20 hours)` with `h` inherited in **bars**: on H1, `h` = 4/12/24 → 20/20/24
hours; on H4, `h` = 16/48/96 hours → 20/48/96 hours. The **rule** is identical; the **block** is not,
and at `h` = 12 the two clocks differ 2.4×. §12 asserts *"every block-bootstrap block ≥ `max(h in
hours, 20 hours)`, **identical on H1 and H4**"* as a HARD check — as worded, unsatisfiable. The bars→
hours conversion itself is coherent and does not change the parent's object or the parity anchor
(parity is on `mean_r_h`, `p_momo`, `p_mr`, `n_decided`, none of which depend on the bootstrap block).
Reword to "the same rule on both clocks".

#### F4-16 — LOW — an undisclosed conflict between AMENDMENT-C6 and AMENDMENT-C7

C6 requires that *"a grid that cannot resolve the interaction is booked `NOT_RESOLVABLE`"*; C7
forbids any `NOT_RESOLVABLE` flag anywhere. The design follows C7 (later, and correct), but §14 lists
both as in force without noting that C7 supersedes C6 on this clause.

---

### PART C — does the design now deliver B-5's protection?

**Independent judgement: the architecture is sound and the run-3 remedies are real, but the
protection still does not operate — and this time the failure is in the direction that costs.**

I agree with run 3's structural read and reached it independently: the HARD schema check binding
every `log R` to `ci_low`/`ci_high`/`ci_width`/`block_mde` on the same row is genuinely stronger than
a boolean on the *emission* axis, because a label can be dropped from a summary and a missing column
cannot; the §13 refusal on aggregates closes negative-by-aggregation; `mde50`/`mde80`/`mde95` restores
countability without privileging a rate, and run 2's `finest_rung_detected` was correctly refused.
None of that is self-grading — I can verify each of those clauses exists and does what it says.

**On the symmetry argument — is "a pessimistic predeclaration is also a B-5 failure" real or a
rationalisation? Both, and the rationalisation is the load-bearing half.** The symmetry is real in
kind: predeclaring 0.14 on a stratum that resolves 0.05 does cause a genuinely resolved null to be
read as unresolvable, and that discards evidence. But the two errors are **not symmetric in
consequence**. An optimistic table converts a thin cell into a *claim* ("we looked and there was
nothing"); a pessimistic table converts a resolved cell into an *abstention* ("we could not tell").
In a falsification programme whose entire recorded failure history is negatives that were not
actually powered — SPDR-014's 0/927, ckpt-017's "unresolved-at-power" — the abstention is the cheap
error and the claim is the expensive one. B-5 exists to prevent the expensive one specifically.

That asymmetry matters here because the argument is deployed in defence of a table that is
**optimistic on the stratum that carries the experiment**: F4-01 predeclares ~40k where the parent's
own arm reads ~15k, and F4-04's `8.4` — the value that makes the 0.05 rung "reachable at one basis" —
comes from a single cell. The design's §9 says plainly that with the adequacy label retired, the
predeclared table *is* the protection. It is, and it is currently mis-calibrated 2.7× toward
optimism on E-TOUCH. So the answer to "did the run-3 fix work" is: **the fix was the right fix and
was applied honestly; the arithmetic underneath it is wrong again.** That is the second consecutive
review at which §8's population arithmetic has been the blocking defect, which is worth naming to the
operator as a pattern rather than as a third list.

**Does the same-row predeclared-vs-realised check do anything?** Structurally yes — it converts an
unfalsifiable forecast into a record that survives the run, and that is exactly the property run 3
was right to want. Operationally, not yet: nothing directs a reader to compare the two numbers
(F4-08). It is a good instrument with no wiring.

**What would deliver the protection, with no threshold reintroduced:**

1. **Recompute §8's populations on the design's own object and clock, per side arm** (F4-01, F4-02),
   and re-derive the expected `mde50` column from the corrected `n`. The parent's emission already
   contains the answer — no estimate is needed.
2. **Anchor `c` for the E-TOUCH strata on cells that are actually this design's stratum** (F4-04),
   and state the `>15k` band's thinness wherever it is quoted. P-25 asks for a defensible basis range,
   not for the widest available spread.
3. **Derive the block, don't pick it** (F4-03) — 24 hours is the parent's own rule and is the basis
   `c` was measured on; or derive it from TRAIN autocorrelation with a CI, as §6.1 already requires of
   TRIPWIRE-1.
4. **Wire the predeclaration into what gets read** (F4-08) — one clause in §13 requiring any aggregate
   to carry the predeclared-vs-realised `mde50` gap for the strata it spans. Admits, excludes, labels
   and ranks nothing; costs nothing; would have caught F4-01 at run time.

---

### Independent verification of the operator's named checks

| Check | Result |
|---|---|
| **Exact mirror, slope 1, everywhere a target is stated** | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` in §1 DERIVED, §5, §12, G5, G6, §13. `0.9408` appears **zero** times — the refusal of the fitted-slope form is present, complete, and correctly stated by description rather than by naming the number: §5 refuses it as a target, §12 makes a fitted-slope residual anywhere a HARD failure, §13 refuses it, G6 asserts the emitted null is 0 at slope 1 |
| **Cost enters no estimand, threshold, band or comparison (C5)** | **CLEAN.** Swept every cost mention: header NOTE, §5 `DISCLOSED REFERENCE ONLY`, §7 cost-floor line ("no read in this design is compared against it"; σ-unit effects never compared to the floor, P-15), §12 HARD cost-isolation row, §13 first bullet, §15 column flag. `p_be_net` is disclosure-only at every occurrence |
| **No `powered`/`unpowered`/`at_target`/`NOT_RESOLVABLE` flag emitted** | **CLEAN.** §12 asserts the absence HARD; §9 and §13 refuse it; §15's `resolution_ladder.parquet` says "No adequacy flag". Every surviving use of "powered" is a historical reference to SPDR-018's own subset (§1, §8, §14) or the §15 note explaining why the L-51 anchor changed. F3-07's residue is closed |
| **No canonical adequacy threshold under another name** | **CLEAN on the ladder; ONE candidate elsewhere.** The ladder `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` matches C7's registered set exactly; `mde50`/`mde80`/`mde95` are three points of one curve and nothing is admitted, excluded, labelled or ranked by them — I traced every occurrence. The **20-hour block** is the one number picked rather than derived (**F4-03**); it is not an *adequacy* threshold, and nothing is admitted or excluded by it, so it does not breach C7's letter — but its stated derivation is false and it is looser than the basis it claims to match |
| **Nothing filters, weights, labels or ranks on `p_event`** | **CLEAN — swept all 20 occurrences** (§2.2, §5, §8, §9, §10, §11 G2, §12, §13, §15). Emitted per cell per event type as a covariate and dose-response axis; §12 asserts it does not filter, gate or label; G2(c) exists specifically to prove no code path applies it; §13 refuses any selectivity gate, breach-rate cutoff or exclusion on it. Band labels are CI-relative only. Still the cleanest part of the document |
| **Parent fidelity** | **CLEAN on all four items.** §2.1's grammar table is faithful row by row; the **5 bps deadband** is in §3's governing clause (not `r == 0`); the **UNDECIDED rule** is in §2.1, §3's exclusion rule and a §12 HARD row; the **parity tolerance** `\|Δ\| ≤ 1e-9` is declared on `mean_r_h`, `p_momo`, `p_mr`, `n_decided` — **all four columns exist in `expectancy_by_cell.parquet`**, verified — and 1e-9 is achievable with ~4 orders of margin against SPDR-018's 9.1e-13. The one open question about parent fidelity is F4-01's side-arm construction |
| **Amendment ledger direction count** | **2 looser / 6 tighter / 3 neutral is ARITHMETICALLY CORRECT** — I read all eleven rows (LOOSER 1, 2; NEUTRAL 3, 4, 7; TIGHTER 5, 6, 8, 9, 10, 11). Two labels are wrong on substance: **AMENDMENT-8 is not TIGHTER** (F4-03) and **AMENDMENT-10's TIGHTER omits a departure from a binding directive** (F4-06). The L-23 note on the 2-looser streak is adequate and individually reasoned; both loosenings act only on population size and I verified neither touches a fence, causality rule, control or claim boundary. The 6-tighter streak is a ≥3 one-directional run in the safe direction and is not flagged in the design — worth a line at the gate |
| **L-28 derangements** | **CLEAN.** Both permutation controls declare `DERANGEMENT (zero fixed points, asserted and counted)`; §12 asserts a measured fixed-point count of 0; the two matched comparators correctly declare `N/A` |
| **L-52 / P-23 check integrity** | **CLEAN.** Expected HARD-check count asserted and reconciled by name; every check depends on an emitted artifact; determinism unconditional at `--jobs > 1` independent of `--resume`; no required check in a manual post-step; TRIPWIRE-2 present with a vacuity check and a derived-threshold clause (L-24.3), which closes the SPDR-018 P-23 failure mode |
| **P-24 comparator disclosure** | **CLEAN.** All three comparator blocks carry the comparator's own mean, null quantiles and plant curve with every percentile; a bare percentile is explicitly refused; the known priors are correctly labelled as priors from SPDR-018's population |
| **L-50 / P-21 portability** | **CLEAN.** All bands and rungs are dimensionless log units; plant curves now carry σ̂ units and re-derivation per universe. Conversions verified against σ̂ = 73.00 |
| **L-21 / P-15 unit pin** | **CLEAN — F3-03 closed and exact** (see Part A) |
| **L-24 (three clauses)** | **PRESENT, correct, and now rendering as a declaration block** |
| **Internal consistency §4 ↔ §10 ↔ §15** | **CLEAN except F4-07.** §4's L4 = 18 reconciles with §10's 12 + 6; §4's L1 = 4 matches §10's "L1 4"; §15's artifact list covers every file §8 and §12 name (`resolution_ladder.parquet`, `selection_check.json`, `unit_pin.json`, `parent_parity.json`, `controls.json`, `integrity_selfcheck.json`) with no orphans in either direction |
| **B-4 / B-9 object identity** | **CLEAN.** Conditioning at the breach bar; three event types kept as separate commitment states and never pooled; one open episode per symbol with suppression counted |
| **Bands partition** | **CLEAN.** `ci_low > 0` / spans 0 / `ci_high < 0` is exhaustive and mutually exclusive; no magnitude appears in any band |
| **Holdout / XENA / family action / TEST** | **CLEAN.** §10 holdout never queried; §12 asserts zero queries ≥ 2025-01-08; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| **SPREAD-COST-DISCLOSURE** | **CLEAN.** All five fields verbatim plus the C5 note |
| **Governance — spdr-lane** | **CLEAN** on causal lag, per-stratum reporting, pooled-as-disclosure fallback (F3-08 closed), TRAIN-only, 0 counted TEST reads. Multiplicity is disclosed but mis-multiplied (**F4-07**) |
| **Governance — chapter-06 §1b (L-51)** | **CLEAN.** The check is mandatory, is present, has a population again, and is HARD on presence/form only |
| **Reflection §5.6 / §5.9 consistency** | **§5.6: CLEAN** — all five predictions carried, wording faithful (but see F4-06 on prediction 1's attachment). **§5.9: FAILS on L1** (F4-06) and on the phase-(b) trigger (F4-05) |
| **Registry — HYP-D7 wording** | **CLEAN.** The departure is now disclosed in both §2.2 and AMENDMENT-1, with the intent-vs-literal distinction argued and the registry amendment offered to the operator |
| `check_no_local_accounting` | **DEFERRED** to post-implementation QA; §12 declares the check |
| **Start gate** | **STILL FLAGGED.** The reflection's operator decision remains unsigned. Design registration does not require it; execution does |

---

### Verdict and routing

**REVISE.** All findings route to **`quant-designer`**; no implementation exists.

**Nothing rises to REJECT.** No holdout contact, no causality violation, no missing tripwire, no cost
smuggling, no fitted-slope target, no `p_event` application, no unapproved silent deviation. The
`p_event` quarantine, the exact mirror, the cost isolation, the unit pin and the parent-fidelity
restorations are intact and are the strongest parts of the document.

**Fit to authorise implementation (`screen_code/`): NO.** Four findings specify numbers or behaviour
the code would be built and checked against:

- **F4-01** — the predeclared population for the stratum that carries the experiment is wrong by
  2.7×, and the design's stated reason ("both side arms use the full event count") is contradicted by
  the parent's emission. Under C7 this table *is* the B-5 protection.
- **F4-03** — the block rule is a picked number with a false derivation, and it is looser than the
  basis `c` was measured on. It is a HARD check in §12, so the code would enforce the wrong value.
- **F4-02** and **F4-04** — §8's remaining arithmetic and basis defects; §8 must be self-consistent
  before it can serve as the predeclaration.

**F4-05** and **F4-06** are governance departures from in-force binding amendments (C6 and reflection
§5.9) that need either compliance or a declared ledger row before execution; **F4-06** additionally
changes what L1 is, which is implementation-relevant.

**A note for the operator, offered once.** Run 3 recorded that this design's revisions had twice
skipped the findings needing edits to existing text. That pattern is **broken** — twelve of fourteen
run-3 findings are closed and closed properly, including all the ones that needed rewriting. The
pattern that has now replaced it is narrower and more specific: **§8's population arithmetic has been
the blocking defect at two consecutive reviews**, each time in a new form, each time optimistic. It
may be worth having the corrected populations computed directly from the parent's parquet and pasted
in, rather than re-derived in prose a fourth time.

**Execution remains a separate operator gate regardless of this verdict**, and carries the standing
unsigned-start-gate flag.

## QA run 5 — 2026-07-29T00:46:49Z — mode: operator-session — HEAD 42934ef91adb15a4aac2625b323021abf9ad94e5

**Reviewed git state:** dirty:
`python/experiments/SPDR-019/design.md`,
`python/experiments/SPDR-019/qa-review.md`,
`python/experiments/SPDR-020/design.md`,
`python/experiments/SPDR-020/qa-review.md`;
untracked:
`python/experiments/SPDR-019/results/`,
`python/experiments/SPDR-020/results/`,
`python/src/xen/resolution_basis.py`.

**Target:** `python/experiments/SPDR-020/design.md` (1,061 lines).
**Stage:** DESIGN-STAGE. `screen_code/` is absent — expected, not a finding.
**Independence:** fresh operator session; this reviewer authored neither the design nor the two
rounds of fixes. Runs 3 and 4 were read in full. Current text, the new module and both JSON artifacts
were treated as untrusted claims.

**Verdict: REVISE. Not fit to authorise implementation (`screen_code/`).**

Findings: **4 HIGH · 4 MEDIUM · 1 LOW.**

### Run-4 blocker closure

| Run-4 blocker | Run-5 result | Independent evidence |
|---|---|---|
| **F4-01 population grain** | **CLOSED on the parent counts; new predeclaration defect remains** | At `Z-VOL/H1/H=12/h=12`, the parent signed arms exist at exactly one cell: `z=1.5/E-TOUCH`, MOMO **15,041**, MR **15,331**. Every other `(z,event_type)` is P-NONE only. The design table states this correctly. `expected_resolution_prior.json` reproduces the nine listed parent cells exactly. See **R5-01** for the missing future artifact and omitted new cells |
| **F4-02 86,831 vs 51,147** | **CLOSED** | Re-derived: 86,831 = `Z-VOL,z=1.5,h=12`, all `H`; 51,147 = the same plus `H=12`, all clocks. The live design no longer presents them as one population |
| **F4-03 block rule** | **PARTIAL** | The live `max(h in hours, 20 hours)` rule is withdrawn; only its amendment history remains. The replacement is still not verbatim and is not coherent on H4 — **R5-02** |
| **F4-04 thin 15k+ band** | **CLOSED** | Re-derived from arm C: **26 rows, 8 distinct `n`, 3 bases**, median `c=11.3036`, IQR **8.3628–12.0899**. The JSON matches exactly and the design makes no range-across-bases claim |

The other withdrawn figures are also cleanly historical: `91.8% / 511,350`, “reaches 0.05 and
approaches 0.03”, and the required-`n` table based on the unstated ~47.8 divisor do not survive as
live rules. The new uncomputed “no stratum reaches 0.03” forecast is separate — **R5-01**.

### Independent population and resolution audit

At `(source=Z-VOL, clock=H1, H=12, h=12)`:

| `z` | Event | P-NONE | P-MOMO | P-MR |
|---:|---|---:|---:|---:|
| 1.0 | E-TOUCH / E-CLOSE / E-HORIZON | 6,994 / 6,763 / 4,684 | — | — |
| 1.5 | E-TOUCH | 6,861 | **15,041** | **15,331** |
| 1.5 | E-CLOSE / E-HORIZON | 6,484 / 4,485 | — | — |
| 2.0 | E-TOUCH / E-CLOSE / E-HORIZON | 6,662 / 6,163 / 4,284 | — | — |

`results/resolution_basis.json` reproduces `xen.resolution_basis` exactly on its declared arm-C
population. The unit-pin artifact also reproduces: 17 finite `s_symbol` values, with the eight NaNs
exactly ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH and 1000RATS.

### Design-fidelity trace

No implementation exists, so code locations are intentionally `N/A`. This table gates whether the
design is sufficiently determinate to implement.

| Design clause | Code | Verdict | Notes |
|---|---|---|---|
| §2 SPDR-014 grammar/parity | N/A | **MATCHES** | 5 bps deadband and UNDECIDED rule restored; parity fields all exist |
| §4 L0/L2/L3/L4/L5 protocol | N/A | **MATCHES** | L-51 is HARD on presence/form only, not on value |
| §4 L1 distinct entry | N/A | **DEVIATES** | registered C6 requires one fixed entry; no operator authority for the departure — R5-03 |
| §6 tripwire pass rules | N/A | **MISSING** | “materially change” / “distinguishable” have no executable statistic or inequality — R5-04 |
| §7 unit pin / L4 comparator | N/A | **MATCHES** | both L4 arms use Parkinson; Wilder ATR sets no exit boundary |
| §8 expected resolution | N/A | **MISSING** | promised artifact absent; current prior is incomplete — R5-01 |
| §8.1 inherited uncertainty | N/A | **DEVIATES** | shortened parent rule; H4 minimum/horizon contradiction — R5-02 |
| §11 G1/G2 | N/A | **DEVIATES** | numbers reproduce only after supplying omitted policies — R5-05 |
| §12 hard/informative split | N/A | **MATCHES** | L-51 presence/form is an integrity check; no value is gated |

### Findings

#### R5-01 — HIGH — `expected_resolution.json` is absent, so “predeclared by generation” is still a promissory note

**Fails:** §8 lines 488–491, 637–673; §12 Predeclared-vs-realised row; design-requirements §6;
B-5; §15 artifact map.

`results/expected_resolution.json` does not exist. `xen.resolution_basis` has no function that can
generate it. There is no schema, generation command, source hash, outcome-access fence, timestamp or
commit pin. The module and the two existing JSON files are themselves untracked. A deterministic
generated artifact **can** be a real predeclaration, but only when the method, frozen inputs and
generated output are fixed before implementation/outcome access. Naming a future path is not that.

`expected_resolution_prior.json` is numerically exact for its nine listed parent cells, but it omits
the design's new `z=2.5/3.0` cells and every other clock/source/horizon stratum rather than marking
them explicitly unknown. The prose then adds two unsupported claims:

- both known signed counts are **above 15,000**, so they do not “straddle” the 5k–15k and 15k+ bands;
  the lower endpoint `0.061` comes from applying the neighbouring band anyway;
- “NO stratum is expected to resolve 0.03” cannot follow when every non-anchor signed count is
  declared unknown.

“Unknown until measured” is acceptable where the parent genuinely supplies no signed-arm prior;
fabricating a number would be worse. It must be encoded as an explicit
`UNKNOWN_NO_PARENT_SIGNED_ARM` state for **every** declared stratum, with `expected_n` and
`expected_mde50` null. It is not a quantitative power forecast and cannot support a live resolution
claim.

**Required fix before implementation (quant-designer):** implement and test the deterministic
generator; define the complete per-stratum schema; generate and commit `expected_resolution.json`
from hash-pinned frozen inputs; include explicit unknown rows, source hashes and timestamp; list the
module and all three JSON artifacts in §15; remove the false “straddles” and uncomputed 0.03 claims;
then run fresh QA.

#### R5-02 — HIGH — the claimed verbatim block rule omits binding clauses and breaks its own horizon guarantee on H4

**Fails:** §1 lines 60–64; §8 lines 507–513; §8.1 lines 681–697; §12 Block-rule row;
SPDR-018 §6.2 lines 247–250; L-20/INFR-004.

SPDR-018's rule is:

1. aggregate to **per-calendar-day sufficient statistics**;
2. resample day-blocks of **`{1,3,7}` days**;
3. minimum block one day / 24 H1 bars;
4. take the min/max envelope over blocks × five seeds;
5. call `xen.evaluation.block_bootstrap_ci` and cap effective block `< n`.

SPDR-020 quotes only items 3–4 plus an unnamed sweep. “Inherited verbatim” is false, and an
implementer can choose a different sweep, omit daily aggregation and omit the small-`n` cap while
passing §12 as written.

The transport to H4 is also internally false. The design inherits `h={4,12,24}` in **bars**.
On H4 those horizons are 16/48/96 hours; a one-day minimum is not `>= every horizon`. Saying a day
is a calendar unit does not repair that. The parent parity fields are means/rates and therefore are
not changed by the bootstrap, but the H4 CI/MDE construction is under-specified and cannot inherit
the H1 guarantee silently.

**Required fix before implementation:** quote SPDR-018 §6.2 word for word, including `{1,3,7}`,
daily sufficient statistics, function and effective-block cap; pin the complete rule in the JSON.
For H4, predeclare the clock-specific day-block sweep/minimum that is at least the inherited
bar-horizon, or explicitly demote H4 resolution transport and compute its realised basis without
claiming parent parity for `c`.

#### R5-03 — HIGH — L1 still violates the single-entry protocol; disclosure is not operator authority

**Fails:** §1.1 prediction 1; §4 lines 229–255; AMENDMENT-14; registered AMENDMENT-C6
(`cf-voldir-001.md` lines 430–443); reflection §5.9.

C6 and reflection §5.9 require every phase-(a) layer to be characterised against **the same fixed
signed entry**, and define L1 as ŝ setting capture **parameter magnitudes**. Current L1 instead
changes the entry band and which zones breach, then gives that distinct entry its own baseline.
That removes the run-3 comparison confound, but it creates a different experiment. AMENDMENT-14
discloses the departure; unlike AMENDMENT-15, it carries no execution blocker or operator sign-off.

The claimed pre-registered prediction is also not tested: “ŝ-scaling every capture parameter” is
assigned to L1, while L1 scales the entry band, not a capture parameter. Comparing the changed entry
to its own L0 does not make those objects identical.

**Required fix before implementation:** restore L1 to capture-parameter scaling on the fixed entry,
or obtain operator-signed authority amending C6 and rewrite prediction 1 to the estimand actually
tested. Disclosure alone is insufficient because this choice changes the code and estimand.

#### R5-04 — HIGH — both HARD tripwires lack an implementable pass rule

**Fails:** §6.1–§6.2 lines 412–441; §11 G7; §12 HARD list; design-requirements §4; L-24/F06.

TRIPWIRE-1 says “must materially change” and “indistinguishable” without naming the comparison
statistic, mapping the conditioning-stream autocorrelation to an expected effect, or giving an exact
CI inequality. TRIPWIRE-2 says “must differ” but its form — “the breach bar's own full OHLC range
including bars after `j`” — mixes a single bar with later bars and does not define the leaky detector.
Neither HARD result is executable without developer judgement.

**Required fix before implementation:** for each tripwire define the altered inputs exactly, name
the emitted statistic, give the prospective TRAIN-derived threshold and exact pass/fail inequality
(including CI endpoint and direction), and bind it to a named artifact field. Prefer deterministic
affected-event/entry-price counts where possible.

#### R5-05 — MEDIUM — the golden values are correct only for policies the design does not name

**Fails:** §11 G1/G2; §12 Golden traces.

Every G1 number reproduces exactly for the first decided P-MR row:
`anchor_idx=61`, `event_idx=61`, `entry_idx=62`, `exit_idx=74`,
`entry_ts=2022-07-17T14:00:00Z`, `exit_ts=2022-07-18T02:00:00Z`, side `-1`, label `MR`,
`exit_reason=time`, `r_h=-157.371411` bps. But the same event has P-MOMO `exit_reason=stop` and
P-NONE `exit_reason=null`. G1 omits `policy=P-MR`.

G2's `0.994872 / 1.000000` and `194/249` reproduce exactly only for P-NONE; P-MOMO and P-MR carry
different values. G2 omits `policy=P-NONE`.

**Required fix:** add the policies to G1/G2 and their asserted artifact keys. The numbers themselves
are correct.

#### R5-06 — MEDIUM — the ~13,000-cell count still omits a declared axis

**Fails:** §10 Cell count; `spdr-lane.md` multiplicity disclosure; AMENDMENT-11.

The primary arithmetic is correct: 1,152 non-L4 + 1,008 L4 = **2,160**. Applying every named
co-report axis gives clock `2` × source `3` × `H` alternatives `3` = `18`, hence **38,880**, not
~13,000, before DESIGN/CONFIRM verification rows. The stated ~13,000 is `2,160×6` and omits the
named `H` axis.

**Required fix:** either state the narrower co-report restrictions that prevent a full cross and
count that grid exactly, or disclose ~38,880. This does not conflict with the `<=8 plots` freeze:
plot count and emitted-cell count are different limits, and a large disclosure table can feed a
small fixed plot set.

#### R5-07 — MEDIUM — the predeclared/realised comparison is a useful audit, not the B-5 protection the prose claims

**Fails:** §8 B-5 clauses 3–4; §9 lines 739–753.

The emission-side protection is strong: every effect carries its realised CI/MDE, and aggregates
must carry the realised resolution distribution. The same-row expected/realised pair makes
calibration error visible.

The forecast-error symmetry is real in kind but not in consequence. An optimistic forecast can
turn an unresolved covering CI into a false negative — B-5's core harm. A pessimistic forecast can
waste resolved evidence; that is bad evidence handling, but it is an abstention, not the same false
negative. Because nothing acts on or requires analysis to discuss the comparison, it detects
miscalibration after the fact but does not stop a reader using the forecast.

**Required fix without a threshold:** state that every inference and aggregate uses the **realised**
CI/MDE/resolution curve only; require `analysis.md` to report the full signed
predeclared-minus-realised discrepancy distribution. Treat the pair as a calibration audit, never
as an adequacy input, rank or gate.

#### R5-08 — MEDIUM — live indexes and the registered wording are not reconciled with the current design

**Fails:** §2.2; governance/checkpoint/registry consistency.

The §2.2 reconciliation is transparent and adequate as a **disclosure**: it quotes HYP-D7's “with a
band that actually selects”, distinguishes intent from literal filtering, and records the operator
directive that removed the gate. The design-stage `p_event` sweep is clean: it is emitted and read
only as a covariate; no occurrence filters, weights, labels or ranks a cell.

The external records are still stale:

- `python/experiments/INDEX.md` says low-`z` cells expect **20–45k** episodes, contradicting the
  corrected ~15k anchor and unknown non-anchor arms;
- `docs/experiments-docs/INDEX.md` says both designs are pending, while the checkpoint and experiment
  index say complete;
- the family registry and checkpoint still carry the literal “actually selects” wording.

Because the no-filter form is recorded as an operator directive, this inconsistency does not add an
implementation blocker. It must be reconciled before execution so the registry cannot later be read
as requiring the prohibited `p_event` filter.

**Required fix:** update the two indexes; append an operator-authorised registry clarification that
selectivity is measured/reported, not an eligibility filter.

#### R5-09 — LOW — the amendment arithmetic is historical, but the live tally and prose are stale

**Fails:** §14; L-23.

Counting all 15 rows exactly as labelled gives **3 looser / 8 tighter / 4 neutral**, matching the
printed total. AMENDMENT-13 withdraws AMENDMENT-8's live rule, but AMENDMENT-8 is not marked
`SUPERSEDED BY AMENDMENT-13`; excluding it from the active set gives **3 / 7 / 4**. The closing note
then says “six tightenings”, matching neither count. The final-set false-qualifier expectation is
also absent; with C7 removing machine qualifiers this should be stated explicitly as
`N/A — zero machine qualification rule`, not left implicit.

**Required fix:** mark AMENDMENT-8 superseded, distinguish historical from active counts, repair
“six tightenings”, and state the final-set L-23 qualifier expectation as N/A/zero with the reason.

### Checks independently verified clean

| Check | Result |
|---|---|
| **Exact mirror** | **CLEAN.** Every live target uses slope 1/intercept 0. `0.9408` is absent; refusing the fitted form without naming its old estimate is complete |
| **Cost isolation** | **CLEAN.** Cost enters no estimand, threshold, band or comparison; `p_be_net` is disclosure-only |
| **No adequacy flag** | **CLEAN.** No emitted `powered`, `unpowered`, `at_target` or `NOT_RESOLVABLE` field; no replacement canonical threshold |
| **`p_event`** | **CLEAN at design stage.** Every occurrence is covariate/reporting or an explicit refusal; no filtering, weighting, labelling or ranking |
| **Unit pin** | **CLEAN.** `sigma_bps=s_symbol×EWMA_park`; EWMA alone is explicitly dimensionless; 8 NaNs exact; Wilder ATR sets no exit boundary |
| **Parent fidelity** | **CLEAN.** Grammar, 5 bps deadband and UNDECIDED rule present. `mean_r_h`, `p_momo`, `p_mr`, `n_decided` all exist; `|Δ|<=1e-9` is coherent |
| **L-51 vs INFR-016** | **CLEAN.** HARD on presence/form only; no value is adjudicated and no cell is dropped |
| **Declaration rendering** | **CLEAN.** 34 fences, balanced; no heading is swallowed; §6.1/§6.2 and all declarations render as blocks |
| **Holdout/TEST/family action** | **CLEAN.** TRAIN-only, zero counted reads, no holdout or family transition authorised |

### Standing execution blockers

Confirmed without re-litigation:

1. AMENDMENT-15's phase-(b) trigger conflicts with registered C6 and has an explicit execution
   blocker;
2. `reflection-inputs.md` §9 remains unsigned.

Both block **execution**, not implementation. They are separate from R5-01 through R5-04, which
block implementation now.

### Golden-trace and gate verdict

Design-stage only: no code or smoke emission exists to diff. The numeric G1/G2 values are correct on
P-MR/P-NONE respectively, but their keys are ambiguous until R5-05 is fixed. G7 is non-executable
until R5-04 defines the tripwire comparison.

**FAILING_ARTIFACT:** `python/experiments/SPDR-020/design.md` and its pre-execution resolution
artifacts.
**REQUIRED_SKILL:** `quant-designer`.
**Implementation authorisation:** **NO.** The missing resolution predeclaration, incomplete H4/block
rule, unauthorised L1 estimand departure and undefined HARD tripwire rules would otherwise force the
developer to invent design decisions.

## QA run 6 — 2026-07-29T04:58:06Z — mode: subagent — HEAD ac6d91c (clean tree)

**Reviewed git state:** `HEAD ac6d91c` ("fix(spdr-019,020): close QA run-5 findings; commit the
resolution predeclarations"), working tree **clean** — no modified, no untracked files. The three
`SPDR-020/results/*.json` artifacts, `python/src/xen/resolution_basis.py` and
`python/tests/test_resolution_basis.py` are now **git-tracked** (`git ls-files` confirms all five).

**Target:** `python/experiments/SPDR-020/design.md` (1,101 lines).
**Stage:** DESIGN-STAGE. `screen_code/` is absent — expected, not a finding.
**Independence:** fresh subagent context. This reviewer authored neither the design, nor
AMENDMENT-16/17, nor any earlier QA run. Runs 4 and 5 were read in full. Every number below was
re-derived from the parquet/JSON artifacts with my own code before being accepted; where I could not
reproduce a figure I say so.

**Verdict: REVISE.** One HIGH finding is a genuine implementation blocker.

Findings: **1 HIGH · 1 MEDIUM · 5 LOW.**

**Plain reading.** The AMENDMENT-16/17 remediation is the strongest round this design has had.
All nine run-5 findings are closed or substantially closed, and I verified each against the
artifacts rather than against the design's description of them: the expected-resolution
predeclaration now genuinely exists, is committed, is dated, pins eight SHA-256 values that all
verify, expands to the complete 1,296-row grain with 1,294 explicit unknowns and no imputation, and
**regenerates byte-for-byte to the SHA the design pins**. The block rule is now literally verbatim
SPDR-018 §6.2, the H4 sweep is coherent against the inherited bar horizons, L1 is back inside the
single-entry protocol, both tripwires carry deterministic count inequalities, the golden traces name
their policy arms, and the multiplicity count reproduces at every step.

**What still blocks implementation is new and was not raised before.** L4 — the payoff-bearing
layer, 1,008 of the 1,872 primary cells — introduces **path-dependent exits (dynamic profit target,
trailing stop) with no fill-resolution rule anywhere in the document.** The parent SPDR-014 resolves
its stop at the next H1 bar open after touch; sibling SPDR-019 resolves target and trail on M1 bars
with an explicit adverse-precedence rule and its own AMENDMENT-4. SPDR-020 says only "the SPDR-019
grid unchanged", which imports the parameter grid, not the mechanics. A developer must invent the
fill price, the target-vs-trail precedence, the time-exit precedence, gap handling, and the clock
that resolves them — and no golden trace would catch a wrong choice.

---

### Run-5 closure, re-derived independently

| Run-5 finding | Status | Independent evidence |
|---|---|---|
| **R5-01** `expected_resolution.json` absent; predeclaration promissory | **CLOSED** | File exists, is **git-tracked**, `generated_at_utc` `2026-07-29T00:00:00Z`. `row_count` **1,296**, `len(strata)` 1,296, **1,296 unique grain tuples**; grain 3×2×3×3×4×3×2 = 1,296 exactly. **2** rows `KNOWN_PARENT_SIGNED_ARM`, **1,294** `UNKNOWN_NO_PARENT_SIGNED_ARM` with `expected_n` / `n_band` / `c_median` / `expected_mde50` all `null` — no imputation, nothing omitted. `source_sha256` carries six pins; I recomputed **all six** and all six match (`resolution_basis.py` 2489bd5b…, SPDR-014 `expectancy_by_cell` 7427e20e…, `post_event` 8abd40c8…, `zones` c66402f2…, `zvol_scale.json` 3c1046d5…, SPDR-018 `analyst_per_cell_magnitudes` c06c58f5…). `input_sha256` for prior (04f7755b…) and basis (74c4b2b7…) both match the on-disk files. **Regeneration check:** re-running `write_expected_resolution` from the pinned inputs reproduces SHA-256 **`39db9012791d37bd210e1272e0635d5690cf54a121a3a8a7cdfb7acb1b8ac077`** — **identical to the design's §8 pin**. `PYTHONPATH=src pytest -q tests/test_resolution_basis.py` → **9 passed**. The withdrawn "straddles" and "no stratum reaches 0.03" claims do not survive |
| **R5-02** block rule not verbatim; H4 incoherent | **CLOSED** | SPDR-018 `design.md:247-250` reads: per-calendar-day sufficient statistics · day-blocks `{1,3,7}` · minimum block 1 day = 24 H1 bars ≥ every horizon · min/max envelope over blocks × seeds, 5-seed battery, `xen.evaluation.block_bootstrap_ci`, effective block capped `< n` · block MDE reported, iid `2.8σ/√n` companion-only. §8.1's H1 block reproduces **all five clauses**, and §12's Block-rule row names all five again. H4: `h`={4,12,24} bars on H4 = {16,48,96} hours = max **4 days**; the declared `{4,12,28}`-day sweep has minimum 4 days ≥ 4 days, and is exactly `{1×,3×,7×}` of it. Coherent. §8/§8.1/§12 all forbid H4 consuming the H1 `c` prior. `xen.evaluation.block_bootstrap_ci` imports |
| **R5-03** L1 violates single-entry protocol | **CLOSED** | §4's L1 row is now "Scale alone, **on the fixed L0 entry** … event keys, breach bar, side and entry fill bit-identical to L0", at the central settings of the L4 devices (`a=2`, `b=1`, `h=12`), **3 paired reads = 6 physical rows already inside L4's 18, adding zero rows**. The §4 "L1 fixed-entry assertion" paragraph forbids changing `z`, band width, event eligibility, event index, side, entry index or entry price, and withdraws the ŝ-conditioned entry arm. This satisfies registered C6 (`cf-voldir-001.md:430ff`, "one fixed entry") and reflection §5.9 ("ŝ used **only** to set parameter magnitudes"). §1.1 prediction 1 ("ŝ-scaling every capture **parameter**") is now tested by the layer it is assigned to. AMENDMENT-16 supersedes -10 and -14 |
| **R5-04** tripwires lack an implementable pass rule | **CLOSED** | §6.2 TRIPWIRE-1 HARD PASS is now `changed_conditioning_rows > 0` **AND** `event_key_symmetric_difference_count > 0` — two deterministic counts, no magnitude, no CI. TRIPWIRE-2 defines the illegal detector by its window (`[anchor_idx, anchor_idx+H]` inspected at the anchor) and passes on `future_touch_zones > 0` AND `early_entry_count > 0` AND `leaky_event_idx = anchor_idx < legal_event_idx` for **every** counted early entry. The ambiguous "bars after `j`" phrasing is explicitly excluded. Both are executable without developer judgement and neither uses a payoff magnitude (L-24.3 / F06 satisfied) |
| **R5-05** golden values correct only for unnamed policies | **CLOSED, verified to the digit** | G1 now names **`policy P-MR`**. Re-derived from `post_event.parquet` (ETHUSDT, H1, DESIGN, Z-VOL, z=1.5, H=12, E-TOUCH, h=12, P-MR, first decided event): `anchor_idx` **61**, `event_idx` **61**, `entry_idx` **62**, `exit_idx` **74**, `entry_ts` **2022-07-17T14:00:00Z**, `exit_ts` **2022-07-18T02:00:00Z**, `side` **−1**, `label` **MR**, `exit_reason` **time**, `r_h` **−157.37141148**. The same event under P-MOMO carries `exit_reason` `stop` and under P-NONE `NaN`, so naming P-MR is what makes the assertion unambiguous. G2 now names **`policy P-NONE`**: `p_event` **0.994872** (`n_events` 194) DESIGN and **1.000000** (249) CONFIRM reproduce exactly and **only** on the P-NONE rows |
| **R5-06** ~13,000 omits a declared axis | **CLOSED, arithmetic reproduces** | Base points `z`(4)×`h`(3)×event(3)×side(2) = **72**. Non-L4 = L0 1 + L2 5 + L3 2 + L5 ≤4 = **12** → **864**. L1 adds **0** physical rows (R5-03). L4 = (target 6 + trail 4 + sizing 2) × 72 = 864, plus hold 6 × 24 `h`-free points = 144 → **1,008**. Primary = **1,872**. Declared expansion clock(2)×source(3)×H(3) = **18** → **1,872 × 18 = 33,696**, as printed. The count fell from 2,160 because AMENDMENT-16 removed L1's four rows per base point (4 × 72 = 288) |
| **R5-07** predeclared/realised is an audit, not the protection | **PARTIALLY CLOSED** | First half done: §8:685-690 and §9:769-774 now state that inference and every aggregate use the **realised** CI/MDE only, that the comparison referees nothing, and that the operative protections are the same-row realised CI/MDE, the aggregate-resolution requirement and the ban on negative-by-omission. Second half **not** done — see finding 4 |
| **R5-08** stale indexes / registry wording | **CLOSED** | `python/experiments/INDEX.md:41` no longer carries "20–45k"; it states the parity anchor's known counts (P-MOMO 15,041; P-MR 15,331) and that every other declared base stratum is explicitly unknown until measured. `docs/experiments-docs/INDEX.md:8,91` now says the designs are complete. `docs/signal-registry/candidate-families/cf-voldir-001.md:135` and its dated **2026-07-29 HYP-D7 WORDING CLARIFICATION** replace "with a band that actually selects" with the executable requirement that selectivity is measured and reported, `p_event` a covariate that "may never admit, exclude, weight, label or rank a cell". No prohibited-filter reading of the registry survives |
| **R5-09** stale ledger tally | **CLOSED** | Counted all **17** rows by their own labels: LOOSER {1, 2, 15}=3, TIGHTER {5, 6, 8, 9, 10, 11, 12, 13, 16, 17}=10, NEUTRAL {3, 4, 7, 14}=4 → **3/10/4**, exactly as printed. Removing the four superseded rows (8 by 13, 10 and 14 by 16, 15 by 17) leaves 13 rows: **2 looser / 8 tighter / 3 neutral**, exactly as printed. AMENDMENT-8 now carries "**SUPERSEDED by AMENDMENT-13**". "six tightenings" is gone. The L-23 final-set false-qualifier expectation is stated as **N/A / zero machine qualifiers** with its reason (C7 removed every machine qualification field). Residual: see finding 5 |

**Standing execution blockers.** AMENDMENT-15's blocker is **genuinely discharged**, not merely
declared discharged: §4.1 now pre-declares the phase-(b) trigger *before* phase (a) runs, as a stated
condition on the (a) reads — exactly the form registered AMENDMENT-C6 and reflection §5.9.1's
"Trigger" row require ("Pre-declared **before phase (a) runs**, in the design, as a stated condition
on the (a) reads"). It uses only the §9 CI-relative vocabulary (`ci_low > 0`), introduces **no
magnitude**, drops no cell, and admits/excludes/labels/ranks nothing — so it does not reintroduce an
INFR-016 / L-32 value gate: it is a stopping rule on a **phase**, not a machine verdict on a cell,
and INFR-016's "machines gate integrity only" is intact. §4.1 keeps the scope protection (phase (a)
may not shrink phase (b)) and states the condition is necessary-not-sufficient, preserving operator
authority. **One standing execution blocker remains: `reflection-inputs.md` §9 is unsigned.** It
blocks execution, not implementation.

---

### Independent numeric audit

Every figure below was recomputed; none was taken from the design or from an earlier run.

| Quantity | Design says | Re-derived |
|---|---|---|
| Parent signed arms, `Z-VOL/H1/H=12/h=12/z=1.5/E-TOUCH` | 15,041 / 15,331 | **15,041 / 15,331** — and every other `(z, event_type)` at that filter is P-NONE only, exactly as §8's table states |
| Parent unsigned counts at the same filter | 6,861 / 6,484 / 4,485; others 4,284–6,994 | **6,861 / 6,484 / 4,485**; `z`∈{1.0, 2.0} span **4,284–6,994**. All nine reproduce, and match `expected_resolution_prior.json`'s `parent_population_evidence` row for row |
| Band assignment of the two known arms | both in the **15,000+** band | **Correct.** `_band_for_n` uses `lo < n ≤ hi`; 15,041 and 15,331 both fall in `15,000-inf`, not the 5k–15k band. No "straddle" |
| `c_median` of the 15,000+ band | (not typed; artifact) | **11.303596531036092** — reproduced from the parquet independently of the module |
| `expected_mde50` for the two arms | (artifact) | 11.3036/√15,041 = **0.0921676**; 11.3036/√15,331 = **0.0912917** — both match the artifact exactly |
| 15,000+ band thinness | 26 rows, 8 distinct `n`, 3 bases, IQR `c` 8.36–12.09 | **26 rows, 8 distinct `n` (15,041 / 15,331 / 18,339 / 19,383 / 19,942 / 20,279 / 20,572 / 20,977), `distinct_groups` 3, p25 8.3628, p75 12.0899** |
| Arm-C basis population | **18,632** cells | **18,479.** The pinned artifact's own `row_counts` says source 24,098 → arm-C filter 18,988 → excluded 509 (all `missing_required_value`) → **retained 18,479**, and my recomputation gives 18,988 / 509 / 18,479 and band counts 8,111 / 7,150 / 2,791 / 401 / 26 summing to 18,479. **See finding 3** |
| Cells reaching 0.03 | 0, other than three degenerate `n`=2, `p`=0 cells | **Exactly 3**, all `n`=2, `p`=0, `mde_log` 0.010148 / 0.011893 / 0.015225. Substance correct; only the denominator is stale |
| `n ≥ 10,000` arm-C realised resolution | 0.053–0.107 | **41 cells, 0.05343–0.10680** |
| Three largest cells | 0.073–0.094 | `n` 20,977 / 20,572 / 20,279 → **0.07271–0.09447** at every horizon |
| Zones by `z` | 234,785 / 261,305 / 253,366 | **exact** |
| Post-event rows by `z` | 190,467 / 211,872 / 158,313 | **exact** |
| `s_symbol` | BTC 6384.3 · ETH 6547.2 · SOL 6215.6; range ~4,606–7,338; 17 finite / 8 NaN | **6384.32135 / 6547.22311 / 6215.59765**; min INJUSDT **4606.417**, max LINKUSDT **7338.341**; **17 finite, 8 NaN** and the eight are exactly ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH, 1000RATS |
| SPDR-018 priors (§1, §2.3, §6, §9) | 121 cells @ 7.87 bps vs 0/927 · p 0.467, W 142.1, L 124.5, W/L 1.136 · 0.0007 from gross BE · side-derangement −12.221 @ pct 0.0065, ~2.4 null sd · C7 2,714 pairs, 44.14%, 6.63%, 0.33 bps · median log R −0.0301 | **All verified** against `SPDR-018/report.md:61,87,91,108,109,154,157,189` and `analysis.md:290,311,419-430,553,559` |
| §1.1 / §4 reflection citations | 5.3× powered `W/L`; W/L moves <~0.3 under selection (V21); 51–62% agreement (V9/V10); ~1/5.6 σ̂ ratio (V28); E-TOUCH > E-HORIZON > E-CLOSE ≈3–4 bps, ~1/5 on cTrader (V27) | **All faithful.** V25 [P] span is 5.3× (0.998→5.25) — the reflection explicitly says "the powered statement is the one to carry", so 5.3× is the correct figure and the governance file's 36–67× is the [U] descriptive span. V21 W/L 1.10→1.40 = 0.30. V9 51–62%. V28 73.00/13.03 = 5.60. V27 exact |
| σ̂-unit plant conversions | 0.068 / 0.137 / 0.274 / 0.548 at σ̂ = 73.00 | 5/73 = 0.06849, 10/73 = 0.13699, 20/73 = 0.27397, 40/73 = 0.54795 — **all four correct to the printed digit** |
| L4 device grid (via SPDR-019 §4.2) | target 3+3, trail 2+2, hold 3+3, sizing 1+1 = 18 | SPDR-019 `design.md:237-240`: `a ∈ {1,2,3}`, `b ∈ {1,2}`, sizing 1 — so 6 + 4 + 2 = 12, plus hold 6 = **18**. L1's named central settings `a=2` (middle of {1,2,3}), `b=1`, `h=12` are all inside the grid |
| Fences / pins | TRAIN `2021-06-29T06:53Z → 2023-12-18T00:00Z`; DESIGN/CONFIRM split at 2023-03-01; holdout 2025-01-08 | Match SPDR-018 `design.md:421-422` and `dataset-reference.md:158`. `cf-voldir-001-universe.json` exists, `top_n` 25, band TRAIN, asof 2023-12-18 |

---

### Findings

#### QA6-01 — HIGH — L4's path-dependent exits have no fill-resolution rule anywhere in the design

**Fails:** §3:198 (*"exit at the variant's exit rule"* — undefined for L4); §4 L4 row (lines 237,
240–242, *"**L4 device grid** is the SPDR-019 grid unchanged (dynamic target, trailing stop, holding
period, sizing)"*); §11 G1–G7 (no trace covers a target or trail fill); §12 Causality row (asserts
only `exit open[entry+h]`, the time exit); §6.1 L-24.2, which makes every derangement seed re-run
"UNDER THE SAME EXIT RULE" — a rule that does not exist cannot be matched; design-requirements §1
(the P&L-bearing object) and §7 (golden trace).

L4 is 1,008 of the 1,872 primary cells and is the layer the entire mechanism claim in §1.1 rests on
("the exit boundaries are placed as multiples of that *conditional* forecast"). Introducing a
dynamic profit target and a trailing stop onto an object whose parent exits only at
`open[entry + h]` requires, at minimum:

1. **the fill price** when a bar trades through the boundary, and the gap case (bar *opens* beyond
   it);
2. **precedence when target and trail are both reachable inside the same bar** — SPDR-019 mandates
   the **adverse** branch precisely because assuming the favourable ordering manufactures edge;
3. **precedence against the time exit**;
4. **the clock the boundary is monitored on.** §10 Scope declares **H1 primary / H4 co-report** and
   no M1 catalog, so an M1-resolved fill is not even in scope as written;
5. **the trail's ratchet cadence** (per bar on close, or intra-bar).

The document answers none of these, and the two candidate parents disagree: **SPDR-014**
(`design.md:243`) resolves its stop as *"adverse excursion ≥ 1.5 × ATR(14) Wilder H1 at entry−1 →
exit **next bar open** after touch"*, while **SPDR-019** (`design.md:130-134`, and its own
AMENDMENT-4 written specifically for this) fills **at the boundary price on M1 bars** with adverse
precedence. "The SPDR-019 grid unchanged" imports the *parameter grid*; it does not import mechanics
that SPDR-019 states in a different section. §7 additionally forbids Wilder ATR for exit boundaries,
so the SPDR-014 convention cannot be inherited wholesale either.

This is the exact class the QA skill flags as a shipped failure shape ("an exit that never updates";
"a reference that moves when the design says fixed"), and it is the one seam in this design that
still forces the developer to invent a design decision. It is also un-checkable: no golden trace
would expose a wrong choice, and no §12 assertion constrains it.

**Required fix (quant-designer).** Add an exit-fill resolution block to §2 or §4 stating, verbatim
and per device: fill price on trade-through, fill price on gap-through, target-vs-trail precedence
(declare the adverse branch), precedence against the time exit, the ratchet cadence, and the clock
and bar granularity on which boundaries are monitored — with §10 Scope updated if a sub-H1 series is
required. Add one golden trace (a G8) on an episode where target and trail are both reachable in the
same bar, with the hand-derived fill price and `r` in bps, and a §12 causality row asserting that no
post-fill bar information is used. Record it as an amendment with its L-23 direction.

#### QA6-02 — MEDIUM — 10 of §12's 29 checks are in neither the HARD nor the INFORMATIVE list, and the expected HARD-check count is never stated

**Fails:** §12 table (lines 859–889) vs the HARD/INFORMATIVE block (lines 891–905); §12's own
first row (*"the self-check asserts the **expected NUMBER** of HARD checks and reconciles them **by
name** against this table"*, P-23 / L-52); design-requirements §8 (integrity-vs-informative split).

The table carries **29** check rows. The HARD block names **21** items. The INFORMATIVE block names
only *quantities* the operator judges (effect sizes, control percentiles, collapse fraction, band
label, `p_event`, dose-response, κ, cost overlay, heterogeneity statistic, event-type ordering) — not
checks. That leaves **10 table rows with no declared class**:

`p_event` emitted · MDE column (M-1 block form) · M-4 effective coverage · Ladder plant operator ·
**No adequacy flag** · Ladder emitted · Span disclosure (M-2) · Episode exclusivity · No local
accounting · Code hash.

Two of these are the design's own headline protections: the **"No adequacy flag"** assertion is the
operative AMENDMENT-C7 guarantee, and the **`p_event` emitted / never-filters** assertion is the
operative INFR-016 guarantee. `No local accounting` is a hard lane rule
(`spdr-lane.md` integrity boundary; `check_no_local_accounting` exists at
`python/src/xen/estimand_validation.py:387`). Leaving their blocking class undeclared means the
developer decides whether a failure invalidates the emission — and, because the check-count
reconciliation is itself HARD and must reconcile "by name against this table", the developer cannot
even compute the expected number unambiguously (21? 29? something between?).

**Required fix (quant-designer).** Assign every §12 table row to HARD or INFORMATIVE explicitly, and
state the expected HARD-check count as a literal number in §12 so the reconciliation has a
predeclared target. `No adequacy flag`, `p_event` non-application and `No local accounting` should be
HARD on presence and form, on the same basis §12 already gives for L-51 ("a check that is silently
skipped is indistinguishable from one that passed").

#### QA6-03 — LOW — §8's "18,632 arm-C cells" contradicts the artifact the same section pins

**Fails:** §8:539 (*"**0 of 18,632 arm-C cells** reach 0.03"*); §8:503-504 (*"**No resolution figure
is typed into this document.** Every one is computed by `xen.resolution_basis` … and pinned to
`results/resolution_basis.json`"*).

`resolution_basis.json`'s own `row_counts` — added in this very commit to make the population
checkable — reads source 24,098 → arm-C filter matched **18,988** → excluded **509** → retained
**18,479**, and its band cells (8,111 + 7,150 + 2,791 + 401 + 26) sum to **18,479**. I reproduce all
of it independently. **18,632** is a stale figure from the pre-filter era and reproduces on no filter
I can construct. The substantive claim is unaffected (exactly 3 cells reach 0.03, all `n`=2, `p`=0),
but §8's population arithmetic has been the blocking defect at three prior reviews, so a live number
that its own pinned artifact contradicts should not stand.

**Required fix.** Replace `18,632` with `18,479`, or state the count by reference to
`resolution_basis.json` `row_counts.retained` rather than typing it.

#### QA6-04 — LOW — R5-07 residue: nothing requires the predeclared-vs-realised gap to be read

**Fails:** §13:927 (the aggregate-disclosure refusal requires median `mde50` and the count below each
rung, but **not** the predeclared-vs-realised gap); §15:1101 (`analysis.md` carries no such
requirement); §8:688-692.

Run 4 (F4-08) and run 5 (R5-07) both asked for the same one-clause wiring. The design implemented the
half that costs nothing to state (inference and aggregates use realised CI/MDE only) and argued in
§9:769-774 why the comparison is a calibration audit rather than a referee — which I accept as
sound and correctly reasoned. But the instrument still has no reader: `analysis.md` is the binding
read, and nothing obliges it to report the signed `(realised − expected)` distribution the emission
now carries on every row.

**Required fix, no threshold.** Add to §13 (or §15's `analysis.md` row) that the fresh-context
analyst must report the signed predeclared-minus-realised `mde50` distribution for the strata any
aggregate spans. It admits, excludes, labels and ranks nothing.

#### QA6-05 — LOW — the ≥3 one-directional TIGHTER streak is not flagged, as L-23 requires

**Fails:** §14:1063-1069; L-23 clause 3 (`lessons-and-amendments.md:575`, *"A one-directional streak
≥3 is an explicit flag to the operator at the execution gate"*); design-requirements §12.

The L-23 note flags only the two LOOSER rows. AMENDMENTS 8–13 are **six consecutive TIGHTER** rows
(and the active tally is 8 tighter), which is a one-directional streak ≥3 and is flagged nowhere.
L-23 does not exempt the conservative direction. Run 4 raised this as "worth a line at the gate"; it
is still absent.

**Required fix.** Add one line to §14's L-23 note recording the tighter streak and its length, for
the operator at the execution gate.

#### QA6-06 — LOW — AMENDMENT-11 is an active row carrying two counts the design has withdrawn

**Fails:** §14:1000-1009 (*"count the cell grid out rather than capping it (**~2,160 primary,
~13,000** including declared co-reports …)"*) vs §10:797 (*"Primary maximum = **1,872** cells …
**33,696**"*) and §10's own parenthetical (*"the withdrawn '≈13,000'"*).

AMENDMENT-16 supersedes only -10 and -14. AMENDMENT-11 therefore remains an **active** ledger row
whose text states a primary count (2,160) that AMENDMENT-16 changed and a co-report count (~13,000)
that §10 explicitly withdraws. Every other superseded row in this ledger carries an explicit
supersession note; this one does not.

**Required fix.** Add to AMENDMENT-11 a line noting that its cell counts are superseded by
AMENDMENT-16 (1,872 primary / 33,696 with co-reports), leaving its other content active.

#### QA6-07 — LOW — the in-force amendment list still carries C6 and C7 without noting the `NOT_RESOLVABLE` conflict

**Fails:** §14:1072-1076; registered C6 (`cf-voldir-001.md:441-443`, *"a grid that cannot resolve the
interaction is booked `NOT_RESOLVABLE` rather than run and explained"*) vs C7 (*"**no `powered` /
`unpowered` / `at_target` / `NOT_RESOLVABLE` flag is emitted anywhere**"*).

The design follows C7, which is later and correct, and §12 asserts the absence of the flag as a
check. But the in-force list presents both amendments as jointly binding with no note that C7
supersedes C6 on this one clause. Carried unclosed from run 4 (F4-16); run 5 did not re-raise it.

**Required fix.** One clause in §14's in-force list: C7 supersedes C6's `NOT_RESOLVABLE` booking
requirement; an unresolvable phase-(b) grid is reported through the resolution ladder instead.

---

### Checks independently verified clean

| Check | Result |
|---|---|
| **Predeclaration integrity (the run-5 centrepiece)** | **CLEAN and strong.** Complete 1,296-row grain, dated, 8 SHA-256 pins all verified, byte-reproducible to the design's stated hash, 1,294 explicit `UNKNOWN_NO_PARENT_SIGNED_ARM` nulls, zero imputation, generator unit-tested (9 passing). The chain design → `expected_resolution.json` → `input_sha256` → prior + basis → `generator_sha256` + `source_sha256` closes end to end |
| **Phase-(b) trigger vs C6 / §5.9.1 / INFR-016** | **CLEAN.** Pre-declared before (a), stated on the (a) reads, CI-relative only, no magnitude, no cell dropped, necessary-not-sufficient with operator authority retained. Scope remains fixed and complete with individually-flat layers retained; estimand is the interaction. AMENDMENT-15's execution blocker is genuinely discharged |
| **Exact mirror, slope 1** | **CLEAN.** `log R = log(W/L) − log((1−p)/p)` in §1 DERIVED, §5, §12, G5, G6, §13. `0.9408` appears zero times; the fitted-slope form is refused as a target in §5, is a HARD failure in §12, is refused in §13, and G6 asserts slope 1 |
| **Cost isolation (AMENDMENT-C5)** | **CLEAN.** Header NOTE, §5 `DISCLOSED REFERENCE ONLY`, §7 cost-floor line, §12 HARD row, §13 first bullet, §15 column flag. `p_be_net` is disclosure-only everywhere; no threshold, band or comparison uses cost |
| **No adequacy flag / no canonical threshold** | **CLEAN.** Ladder `{0.02, 0.03, 0.05, 0.075, 0.10, 0.15}` matches C7's registered set exactly; `mde50/mde80/mde95` are three points of one curve; the invented 20-hour block is gone and no replacement picked number survives. Every remaining use of "powered" is a historical reference to SPDR-018 |
| **`p_event` quarantine** | **CLEAN.** Swept every occurrence (§2.2, §5, §8, §9, §10, §11 G2, §12, §13, §15): covariate and dose-response axis only; §12 asserts non-application; G2(c) exists to prove no code path applies it; §13 refuses any selectivity gate. Registry now matches |
| **Parent fidelity** | **CLEAN.** §2.1's grammar table faithful row by row; **5 bps deadband** governs `p` in §3 (not `r == 0`); **UNDECIDED** rule in §2.1, §3's exclusion clause and a §12 HARD row; parity tolerance `|Δ| ≤ 1e-9` declared on `mean_r_h`, `p_momo`, `p_mr`, `n_decided` — **all four columns exist** in `expectancy_by_cell.parquet`, and SPDR-018 achieved 9.1e-13 on the same arm-C object |
| **L-28 derangements** | **CLEAN.** Both permutation controls declare `DERANGEMENT (zero fixed points, asserted and counted)`; §12 asserts a measured fixed-point count of 0; the two matched comparators correctly declare `N/A` |
| **L-21 / P-15 unit pin** | **CLEAN and exact.** `sigma_bps = s_symbol × EWMA_park`; EWMA alone declared dimensionless; `zvol_scale.json` named as the read source; 17/25 coverage with the 8 NaN symbols named exactly; Wilder ATR explicitly excluded from every exit boundary with the EXP-025 rationale |
| **L-50 / P-21 portability** | **CLEAN.** All bands and rungs dimensionless; plant curves in σ̂ as well as bps, re-derived per universe at run; no absolute-bps bar crosses a universe |
| **P-24 comparator disclosure** | **CLEAN.** All three comparator blocks carry own mean, null quantiles and plant curve with every percentile; a bare percentile is refused; the SPDR-018 priors are labelled as priors |
| **L-24 (three clauses)** | **CLEAN.** Thirds stability reported-not-gated; exit-matched nulls declared (though see QA6-01 — the exit rule they must match is undefined); tripwire thresholds structural, not effect-size |
| **L-51 vs INFR-016** | **CLEAN.** HARD on presence/form only, re-anchored to every reported selected subset, no statistic carries a pass value, nothing is gated. `chapter-06-governance.md:99-100` makes it mandatory |
| **M-1 / M-2 / M-4 / M-5** | **CLEAN.** Block MDE is the reported form with iid as a labelled companion; span disclosure present; effective coverage over 17 not 25; collapse fraction disclosure-only near a zero mean and absent from the HARD list |
| **B-1 / B-4 / B-6 / B-8 / B-9** | **CLEAN.** Point-null disjointness argued explicitly rather than omitted; conditioning at the breach bar; three event types kept as separate commitment states and never pooled; episode-level `p`, `W`, `L`; one open episode per symbol with suppression counted |
| **Bands partition** | **CLEAN.** `ci_low > 0` / spans 0 / `ci_high < 0` is exhaustive, mutually exclusive, magnitude-free; POOLED reverts to the `spdr-lane.md` disclosure-only default if homogeneity does not support it |
| **Declaration blocks (design-requirements §1–§13)** | **PRESENT.** Mechanism + DERIVED, OBJECT-IDENTITY, five control blocks with validity proofs, two tripwires, bands, resolution (C7-substituted power), golden traces, hard/informative split (but see QA6-02), CONVERSION-PIN, SPREAD-COST-DISCLOSURE (all five fields verbatim + the C5 note), amendment ledger, L-24 battery clauses |
| **Artifact map internal consistency** | **CLEAN.** §15 covers every file §8, §11 and §12 name; no orphan in either direction; `resolution_basis.py`, `resolution_basis.json`, `expected_resolution_prior.json` and `expected_resolution.json` are all listed |
| **Holdout / XENA / TEST / family action** | **CLEAN.** Holdout `2025-01-08` matches `dataset-reference.md:158` and is never queried; §12 asserts zero queries at or after it; TRAIN fence matches SPDR-018 exactly; §13 refuses family status change, XENA, TEST and holdout contact; header declares execution unauthorised |
| `check_no_local_accounting` | **DEFERRED** to post-implementation QA; the function exists at `estimand_validation.py:387`; §12 declares the check (unclassified — QA6-02) |
| **Golden-trace diff** | **Design-stage only.** No code or smoke emission exists to diff. G1 and G2 are now falsifiable before the run and both reproduce exactly against the named artifacts with their policy keys. G3, G4, G5, G6, G7 are executable as written. **No trace covers an L4 target/trail fill (QA6-01)** |

---

### Verdict and routing

**REVISE.** All findings route to **`quant-designer`**; no implementation exists.

**Nothing rises to REJECT.** No holdout contact, no causality violation, no missing tripwire, no cost
smuggling, no fitted-slope target, no `p_event` application, no unapproved silent deviation, and — for
the first time in this design's history — no false or unreproducible resolution arithmetic in the
artifacts. The predeclaration chain, the `p_event` quarantine, the unit pin, the parent-fidelity
restorations and the restored C6 trigger are all sound.

**Standing execution blockers:** one — `reflection-inputs.md` §9 remains unsigned. It blocks
execution, not implementation. AMENDMENT-15's blocker is discharged.

**FAILING_ARTIFACT:** `python/experiments/SPDR-020/design.md` (§3, §4, §11, §12, §13, §14).
**REQUIRED_SKILL:** `quant-designer`.
**Implementation authorisation:** **NO.** QA6-01 alone blocks it: the L4 capture devices — the layer
the whole experiment is about — have no exit-fill resolution rule, so the developer would have to
invent the fill price, the target-vs-trail precedence, the time-exit precedence, the ratchet cadence
and the monitoring clock, with no golden trace or integrity check able to catch a wrong choice.
QA6-02 compounds it by leaving the blocking class of ten integrity checks undeclared. The remaining
five findings are corrections to prose and to the ledger and do not, on their own, block
implementation.
