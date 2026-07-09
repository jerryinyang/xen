# EXP-014c — Audit (Stage 4)

**Auditor:** experiment-auditor · **Date:** 2026-07-03 · **Scope:** full forensic + causal-provenance
audit of `python/experiments/EXP-014c/` (design.md, code/, results/verdict.json, 21
`data/strategy_runs/EXP-014c-*` emission dirs + 6 reused `EXP-014b-4h-s8-*` E0 dirs, C# exit block
in `Xen.cs` / `StrategyHost/SignalRecords.cs` / `StrategyRunParquetWriter.cs`, 22 conf files).
Every number below was **re-derived from raw emissions**, not copied from any report.

**Audit verdict: PASS — no Critical findings. Per-stratum statuses stand. 3 Warnings, 5 Info.**
The headline `outcome` string needs interpretive correction at Stage 5 (W1).

---

## 1. Scope compliance

| Check | Result |
|---|---|
| 4h only, S8 only, single-leg, 11 cells | ✓ — 24 (exit×arm×z\*) families × 11 cells = 264 expected; 262 present (2 missing US500 cells, see I4) |
| E0 = reused 014b emissions, read-only | ✓ — `lib.run_root` maps e0 → `EXP-014b-4h-s8-*`; dirs untouched (mtimes pre-date 014c) |
| Entry machinery unchanged from 014b | ✓ — same arm block (`Xen.cs:960-995`): band limits at exp(anchorLog±z\*σ) from ≤t-1 close, breach-skip vs `closeI` and live Bid/Ask |
| Exit axes E1/E2/E3 as specified | ✓ — `_frozenExit/_frozenSl/_frozenTimeStop` from `CisExitSet` (`Xen.cs:758-760`); confs carry `frozen_tp` / `frozen_tp_sl` / `bracket` |
| No undocumented analyses | ✓ — verdict.json contains exactly M1-M6 + statuses |
| Budget | ✓ — 4 tests (all existing machinery), 5 plots, lib.py+run_experiment.py only |

## 2. Data handling & holdout

- **Fence:** `ANALYSIS_END` in every 014c conf is byte-identical to `EXP-013.conf` (diff-verified —
  `FENCE_IDENTICAL`). Loader calls `assert_run_within_holdout` per cell. Spot check JP225
  e3/none/z20: max `SourceCloseTime` = 2024-09-23 01:00 ≤ fence 2024-09-23 04:40. Final-30% never
  touched; no TEST read spent.
- **Alignment:** all joins/sorts on `SourceCloseTime`/`EntryTime`/`ExitTime`; no bar-index joins.
- **Real prices:** all outcomes from engine fills + `RealOpen/High/Low`; per-bar NET via the audited
  `assemble_realized_bps` (intra-position MTM L-09; RT cost once per entry L-02, frozen map —
  EURUSD 1.0 / US500 3.0 / JP225 4.0 bps).
- **NaN:** censored legs (`RealizedBps` NaN) excluded from realized stats and disclosed as counts.

## 3. Code correctness (C# + Python)

**C# frozen bracket (`Xen.cs:1063-1090`)** — at the entry fill tick: `aEntry = exp(b.AnchorLog)`
with `b = _lastBracket` (the ≤t-1 arm bracket; limit orders are cancelled/re-placed every completed
bar, so a fill during bar t can only see the bracket built from bars ≤ t-1 — causal). TP modified
onto the native position, `D = |fill − aEntry|`, SL at `fill ∓ D`, `HorizonBars =
min(48, ⌈3·b.Hl⌉)`. Never modified afterwards: `RefreshForm2Targets` (`Xen.cs:860`) and
`ApplyEventExits`/form-1 (`Xen.cs:847`) are gated on `!_frozenExit`. Time-stop
(`ApplyFrozenTimeStop`, `Xen.cs:1197-1206`) runs on completed bars, closes at next open.

**Emission-level verification of the invariants (JP225 e3/none/z20, all 85 legs):**
- SL symmetry `|fill−SL| = |fill−TP|`: max relative asymmetry 9.9e-15 (exact to rounding).
- TP = entry-time anchor: max rel dev vs `EntryAnchorPrice` 1.9e-07 (price rounding).
- Horizon: min 20 / max 48; all 24 `time_stop` legs have `BarsHeld ≥ HorizonBars`; all 61 decided
  legs have `BarsHeld ≤ HorizonBars`.
- Exit fills: TP fills within 0.19% of frozen TP; SL fills median dev 0.015%, max 0.11% —
  **stop-order gap slippage is real and charged** (adverse fills, correct direction).
- Forbidden-reason assertion (design §12): **zero** `form1_reversion`/`form2_favorable_limit` in
  any e1/e2/e3 cell (checked all 198 cells); zero `sl_outward`/`time_stop` in e1; zero `time_stop`
  in e2. The exit decomposition is clean.
- E1 legs: 0/272 NaN `FixedExitPrice` (spot cell) — no unbracketed frozen legs.

**Python:** `lib.py`/`run_experiment.py` reuse the audited 014b machinery verbatim (same
`assemble_realized_bps`, `gate_stack_pstar` wrapper, frozen SEED=20260703, N_BOOT=10k, Holm
step-down verified correct). `validate_provenance` (fills within [Low,High]+tolerance) wired per
cell: max breach fraction across all 262 cells = 3.1% < 5% threshold, primaries ≤ 0.5%.

## 4. Numerical re-derivation (independent, from raw parquet)

Fresh loads + fresh referee calls reproduced verdict.json exactly:

| Cell | verdict.json net/ci_low | re-derived | match |
|---|---|---|---|
| e3/none/z20 JP225 | 0.263 / −1.844, epi 19 | 0.263 / −1.844, epi 19 | ✓ |
| e3/none/z20 EURUSD | 0.278 / −0.465, epi 18 | identical | ✓ |
| e3/extend/z15 AUDUSD | 3.981 / 1.060, admit | identical | ✓ |
| e3/extend/z15 NZDUSD | 3.995 / 1.526, admit | identical | ✓ |
| e2/extend/z15 US2000 | 9.153 / 3.163, admit | identical | ✓ |

Shift twins independently re-adjudicated (not read from verdict.json):
AUDUSD-shift net 3.37, ci_low **+1.10, still admits**; NZDUSD-shift net 3.03, ci_low **+1.14,
still admits** → REJECT_LEAK confirmed at the raw-data level. Primary twins: JP225-shift ci_low
−1.53, EURUSD-shift ci_low −0.46 — no admit either way (consistent; primaries never admitted, so
the tripwire was not binding on them).

## 5. Verdict forensics

### 5.1 Per-stratum re-derivation & masking check

Binding family (e3/none/z20), all 11 cells re-checked: 7 powered, **0 referee admits, 0 Holm
admits**. No pooled figure is doing any work — the headline is built from per-cell statuses; no
stratum is masked. Statuses: JP225 + EURUSD = NOT_TRADABLE (powered, bite-passing,
availability-confirmed); 9 × AVAILABILITY_NULL/UNPOWERED. The two prespecified primaries are
exactly the two cells with credible negative reads — no post-hoc cell selection occurred (both
named in design §3 before data existed; verified present in `lib.PRIMARY_CELLS`).

### 5.2 Mechanism — why the primaries failed (investigated, not summarised)

**The measurement-matched bracket produced a fair race that pays the spread.** Per-exit-reason
economics (JP225 primary): tp_anchor n=32 @ +266 bps/leg, sl_outward n=29 @ −280, time_stop n=24 @
+25. TP-share of decided legs **0.52** (CI 0.39-0.66) vs the 014b measured p_inward **0.696** —
**inconsistent** (M3; EURUSD 0.51 vs 0.589, CI-consistent but ~coin-flip). Symmetric ±D barriers at
~52% inward = gross edge ≈ 0.04·|leg| ≈ +9 bps/trade gross on JP225, which the referee correctly
reads as ci_low < 0 at 19 episodes. The verdict is *availability did not convert*, not a referee
artifact.

**Why the traded race is worse than the measured race — the fill seam.** The 014b two-barrier
measurement (`mr_characterisation.py:128-151,216-227`) is price-space with the same frozen anchor
and the same H=min(48,⌈3·HL⌉) horizon — the *object* matches. What differs is the **conditioning
event and entry price**: measurement enters at the action-bar **open after a confirmed close
breach** (|z_{t-1}| ≥ z\*, o = next open, D = |o − anchor| ≥ band); trading fills a **resting limit
at the band touch** (D = z\*·σ exactly, the marginal dislocation, plus limit-fill adverse
selection — touches that never confirm also fill). Traded entries are systematically *shallower*
and *earlier* than measured entries, and the measured p_inward = 0.696 lives at deeper
dislocations. Direct evidence of decoupling from the spread signal (per-bar Z traces, JP225
primary): 20/32 tp_anchor legs hit the frozen price TP **without** the spread ever reverting
(mates fell with it), while 15/24 time_stop legs saw the spread revert but the frozen price TP
never filled. On EURUSD, 0/20 sl_outward legs had a spread reversion — stops fire exactly when
the basket signal is also wrong, i.e. the SL adds no information, it just charges −112 bps/leg.

**Attribution (M2, none/z20, descriptive):** freezing the TP rescues most of the E0 loss engine
(JP225 E0 −0.58 → E3 +0.26 net/bar; US500 −1.53 → −1.10) but strands the residual edge below
costs everywhere. E1 (TP-only) ≈ 0 net in every powered cell (allow/extend arms, 11/11 powered);
adding the SL (E1→E2) *hurts* (EURUSD −0.26, US2000 +0.50→+0.11) — consistent with the SL firing
on noise; adding the time-stop (E2→E3) is roughly neutral-to-positive (recycles dead capital:
time_stop legs mean ≈ +2 to +25 bps). **Read: no exit rule unlocks the entry; the entry fill
itself (band-touch limit) is where the measured availability is lost.**

**Session structure (M4, JP225):** decided P&L is concentrated in server slots 0-1 (00-08h ≈
Asia/Tokyo): +2844/+1315 bps vs negative all US-hours slots (−208/−1719/−246/−987). 27/85 entries
in slot 0. JP225's residual availability is session-structural, as design §10 suspected — but
JP225 never admitted, so no downgrade action triggers.

### 5.3 Why the leak cells leaked (all 4 in extend/z15)

e0/extend/z15 {NZDUSD, US2000} and e3/extend/z15 {AUDUSD, NZDUSD} admit strongly (net 4.0-14.3,
ci_low 1.1-3.7, 23-42 episodes, 839-1317 trades) **and survive the 60h peer-feed phase-shift with
nearly the full edge intact** (AUDUSD 3.98→3.37, NZDUSD 4.00→3.03, still ci_low>+1.1). The basket
feed contributes almost nothing: the extend ladder is a **scale-in grid harvesting own-price mean
reversion around a slow anchor** — exactly the 014b 1h finding, now demonstrated at 4h, and it
persists even under frozen brackets (E3). The z15 ladder trades ~10× the primary's count, which is
what powers the admit. These are correctly labeled REJECT_LEAK per-cell (C1b discipline). The
shift barely dents the FX edges (AUDUSD 3.98→3.37, NZDUSD 4.00→3.03 — ~85% survives): pure
own-price. The US2000/GBPUSD `NET_ADMIT_AVAIL_NULL` cells looked like the opposite pattern
(basket-specific edge, availability NULL) — but the §5.4 dissection shows the US2000 "collapse"
is binarization noise on a half-surviving edge, so they are **not** clean construction-specific
evidence either.

### 5.4 Disclosure-admit dissection (US2000 and the extend/z15 complex) — collapse vs shrink

The four Holm-admitting disclosure cells were dissected at the raw level: raw vs shift-twin
re-adjudication across every exit family (fresh referee calls, not verdict.json reads):

| Cell (extend) | RAW net / ci_low / admit | SHIFT net / ci_low / admit | Read |
|---|---|---|---|
| US2000 e0/z15 | 14.33 / +3.74 / ✓ | **7.12 / +0.19 / ✓ still admits** | leak (also 014b's read) |
| US2000 e0/z20 | 12.42 / +1.54 / ✓ | 6.62 / −0.24 / ✗ | shrink, dips under bar |
| US2000 e2/z15 | 9.15 / +3.16 / ✓ | 3.49 / **+0.49** / ✗ | shrink, dips under bar |
| US2000 e3/z15 | 10.90 / +3.17 / ✓ | 5.58 / **+0.48** / ✗ | shrink, dips under bar |
| AUDUSD e3/z15 | 3.98 / +1.06 / ✓ | 3.37 / +1.10 / ✓ | pure own-price |
| NZDUSD e3/z15 | 4.00 / +1.53 / ✓ | 3.03 / +1.14 / ✓ | pure own-price |

**US2000's "shift collapse" at e2/e3 is not a zeroing — it is a ~50% shrink that fails a
materiality leg, not the zero test.** Referee leg forensics on the shift twins: net ci_low stays
**positive** at every exit (+0.19 e0, +0.485 e2, +0.482 e3; raw subpop ci_lower +4.3 to +5.7
bps); what flips at e2/e3 is `L5_materiality` — shifted effect 2.26–2.58 bps vs the 3.0 bps
materiality bar, studentized subpop stat 0.12–0.16 < Q_STUD_MIN 0.674 — while the *same cell* at
e0/z15 passes the full stack under the shift (`verdict: PASS`). The admit/no-admit binarization
flips across exit bolt-ons on a continuous ~half-surviving, still-CI-positive edge. A
construction-specific edge should go toward zero under a 60h-stale basket at *every* exit; it
does not. The `NET_ADMIT_AVAIL_NULL` statuses are literally correct per the frozen label rules,
but the attribution reading "genuinely needs the S8 construction" is **not supported** — roughly
half the US2000 edge survives a garbage basket and remains statistically positive.

Anatomy (US2000 e3/extend/z15, decided legs): raw P&L concentrates in the deeper ladder levels
(L0 +2.8, L1 +10.5, L2 +26.3 bps/leg) — a scale-in-on-depth harvest. Under the shift the strategy
*still* nets +13k bps with a completely different exit mix (time_stop 293/477 legs at +48.5
bps/leg vs 150/1317 raw — the stale anchor is rarely touched, so legs ride the index's own
rebound/drift and exit on time). That is own-price index mean-reversion/drift capture, not spread
convergence. No session concentration (P&L spread across slots). The residual raw-minus-shift
increment (~5 bps/bar) is the most that could be construction-specific, and it carries the full
unpaid multiplicity of 1 cell × 24 disclosure families. Also note: US2000's own two-barrier
availability was NULL (ci_low exactly 0.500) — a net admit with unconfirmed availability inverts
the family's own causal logic.

**Field analysis — US2000 is the top of a continuum, and the continuum is the finding.**
Deweighting the leak test and ranking all 262 cells by net ci_low: **61 cells have ci_low_net >
0, of which 53 never Holm-admitted**. US2000's immediate neighbours match its profile while
failing other referee legs (not the zero test): USTEC extend/z15 e0/e2/e3 = 13.0/+2.85,
8.5/+2.14, 9.9/+2.11 (powered, bite-passing, cross-exit persistent — a one-notch-weaker clone);
US500 e0/extend/z15 9.9/+2.00; then a smooth tail (JP225 8.1/+1.14, GBPUSD 3.8/+1.26, …).
**Every positive row is an extend (or allow) arm; not one `none` arm has ci_low > 0.** The
positive field is one mechanism expressed across all 11 instruments (10 powered; USDJPY's positives all unpowered), both z\*, all four exit
sets: ladder scale-in on 4h dislocations harvesting short-horizon own-price mean reversion,
per-leg P&L fattening with add depth (US2000 L2 +26.3 bps/leg).

Supplementary stress reads on the three admitting survivors (e3/extend/z15):
- **Year-by-year (2021-2024): positive every year, all three cells** (US2000 +10.7/+17.5/+5.3/
  +9.2 bps/active-bar; AUDUSD +2.9/+5.7/+4.3/+2.5; NZDUSD +3.2/+4.2/+5.6/+2.6). No regime spike.
- **Cost stress:** NZDUSD survives 3× cost; AUDUSD survives 2×; US2000 fails at 2× (ladder P&L
  concentrated in deep, fast levels — most slippage-exposed component).
- z20 non-admits are **power losses, not sign flips** (AUDUSD z20 3.96/+0.33 @13 epi; NZDUSD
  3.34/+0.59 @14) — the effect persists at the deeper trigger with fewer events. Axis
  "fragility" is not evidence against the phenomenon (operator-reviewed, 2026-07-03).
- Provenance clean everywhere (fills in-range, gap slippage charged, causality traced).

**Agreed reading (operator + auditor, 2026-07-03):** these observations are inadmissible as
CF-MR-004 evidence (availability NULL; attribution not basket-specific; single-cell claims carry
unpaid cross-family multiplicity) — per-cell statuses stand unchanged. But the field itself — a
cross-instrument, year-stable, execution-clean 4h ladder scale-in own-price MR harvest — is a
robust unclaimed phenomenon that warrants its **own registered candidate family** with a native
design (basket-free trigger, cost-stressed, ladder-depth-aware, mindful that CF-MR-001/002/003
died on cost-vs-capture and P-02 bars exit-stack rescues). No in-run promotion; registration is
an operator-gated Stage-5/registry action. **Order of investigation:** characterise the
mechanism first; only then revisit why the phase-shift control "fails" on it — for a mixed
own-price/construction P&L the shift destroys trigger timing, not the harvest mechanism, so it
tests *attribution*, never signal quality, and its reads are uninterpretable before the
mechanism is known.

### 5.5 Gate-shape check

The frozen referee (mean-location bootstrap ci_low) is the right instrument for this question —
the claim is "net-positive per-bar mean". No tail/bimodal effect is being vetoed: the decided-leg
P&L is by construction near-symmetric two-sided (±D barriers), and the failure is a location
failure (TP-share ~0.52). Bite passed on both primaries (+8 bps plant admits), so the negative is
non-vacuous. USTEC/US500/US2000 are bite-blind (plant fails — high per-bar vol swamps +8 bps);
their negatives are correctly *not* escalated to NOT_TRADABLE (label logic verified in
`cell_status`, matches audited post-C1 semantics: powered AND bite required).

## 6. Causal-provenance & leak pass

- **Provenance trace (verdict-bearing columns):** entry limits armed from `_lastBracket` built on
  completed bars (`Count-2` path; breach reference = ≤t-1 close; live Bid/Ask guard); TP/SL/horizon
  frozen at fill from that same ≤t-1 bracket (`Xen.cs:1063-1090`); fills are engine m1;
  `assemble_realized_bps` uses entry fill → next open / exit fill only (no forming-bar reads);
  time-stop decision on completed bar i, executed at open of i+1. `EntryH4Index` = arm-bar index →
  race window [entry..entry+H−1] matches the availability window definition. **No acausal input
  found on any traced path.**
- **Leak tripwire:** shipped and binding — PRIMARY twin (e3/none/z20, 11 cells,
  `BasketPhaseShiftHours=60` verified in conf) + on-demand twins for both admitting disclosure
  families (e2/extend/z15, e3/extend/z15; dirs present, 11 cells each). Every Holm-admitting cell
  got its own-cell shift verdict; 4 survived ⇒ REJECT_LEAK (correct, REJECT-class applied
  per-stratum); e0 admits used the pre-existing 014b shift twins. Absent-control ⇒ UNVERIFIED
  logic present (`cell_status`), not exercised (no admit lacked a control).
- **Shared modules:** `referee_pstar`, `referee_adaptive`, `signals.ingestion` — unchanged since
  their EXP-013/014b audits (no diffs in working tree beyond documented SignalRecords/Writer
  column additions: `SlPrice`, `HorizonBars`, schema fields 28-29 correctly wired).
- **Price-primary check:** all E1-E3 arms ran native cTrader MODE=3 (NativeOrders, m1 fills),
  emitted under the fence; Python is strictly analysis-only on emissions. No vectorized backtest
  anywhere in `code/`.
- **Booked-vs-real:** stop-leg slippage is charged (SL fills show real adverse gap devs, §3); cost
  charged once per entry from the frozen map; no favorable-index view used.

## 7. Findings

### Critical
None.

### Warnings

- **W1 — Headline `outcome` label buries the binding result.** `run_experiment.py:414-425` orders
  the outcome ladder so any REJECT_LEAK (all 4 are non-binding disclosure arms) pre-empts the
  primary-family read. Both prespecified primaries are powered, bite-non-vacuous, and net-fail —
  design §10's **"Credible negative → RETIRE thesis"** condition is met on the primaries, yet
  verdict.json says `REJECT_LEAK_DISCLOSURE`. Materiality: none of the 262 per-cell statuses, any
  number, or any denominator changes; the binding per-stratum verdicts (the programme's actual
  instrument, L-03) are correct. **No rerun required; Stage 5 must state the primary outcome as
  CREDIBLE_NEGATIVE_RETIRE with the extend/z15 leaks as a separate disclosure line.**
- **W2 — M4 session metric is mis-normalised.** `session_read` divides the best-4-slot P&L by the
  *net* total, which is near zero for most cells → shares of 2.9-23× and `session_flag=True` on
  15/22 flagged keys; the flag as computed is uninformative. Materiality: the flag feeds only the
  design §10 JP225-admit downgrade, and JP225 never admitted — no verdict-bearing number moves.
  The underlying slot data is sound (the JP225 Asia-concentration read in §5.2 was re-derived from
  slot P&L directly). Fix the normalisation (e.g. share of gross |P&L|) if the read is reused.
- **W3 — Shift-tripwire binary read is noisy at the admit bar; report collapse fraction.**
  §5.4: US2000 extend/z15's shift verdict flips between exit objects (e0 passes the full stack;
  e2/e3 fail only the L5 materiality leg at 2.3-2.6 bps vs the 3.0 bar, net ci_low still
  positive). E0 vs E2/E3 are different trading objects, so divergent attribution reads are
  informative, not disqualifying (operator-reviewed) — the narrow defect is that a *binary*
  admit near threshold binarizes noise. Per-cell statuses follow the frozen rules and stand (not
  verdict-material: no admit becomes TRADABLE, availability NULL in all four, binding primary
  untouched). Stage 5 must not describe US2000 as "construction-specific"; future designs
  hanging attribution claims on a shift twin must report the shift **net magnitude / collapse
  fraction** alongside the binary admit, or use a paired raw-vs-shift statistic. Lesson-candidate
  for the KB.

### Info

- **I1 —** E1/none arms are structurally vacuous: reentry=none + no SL/time-stop ⇒ 1 open leg
  blocks all re-arming (EURUSD: 1 trade in 5y, epi=1); all 22 e1/none cells unpowered. Anticipated
  by design §12 ("expect higher censoring"), but the blocking interaction means e1/none carries no
  information — exclude from any attribution narrative. e1 censored legs across all arms: 3,314.
- **I2 —** Missing emissions: US500 absent from `EXP-014c-4h-s8-e2-extend-z15` and
  `…-e3-allow-z20` (10 run dirs, not empty-run: directory absent — run-level failure, no CLI log
  retained). Effect: Holm m=10 instead of 11 in those two disclosure families (marginally *less*
  strict). The only admit affected (e2/extend/z15 US2000, ci_low 3.16) admits by a wide margin and
  is disclosure-only. Not verdict-material; re-emit the two US500 cells before any follow-up that
  promotes either family.
- **I3 —** M4b: same-bar TP+SL races are essentially a US500 phenomenon (14/309 primary, 63/1939
  extend-z15; 0 in JP225/FX), resolved SL-first 13:1 on the m1 path — the availability read's
  "ambiguous ≈ 0" claim holds everywhere except US500, where the m1 resolution is adverse.
  Consistent with US500's fast races (median 2-3 bars held) and its M3 inconsistency in the
  *other* direction (traded 0.47 > measured 0.41).
- **I4 —** Availability merge verified against `EXP-014b/results/mr_characterisation.json`
  raw values: JP225 z2.0 (0.696/0.638, shift 0.450 → confirmed), EURUSD z2.0 (0.589/0.520, shift
  0.486 → confirmed), JP225 z1.5 confirmed, EURUSD z1.5 not (ci_low 0.485) — matches every
  `avail_confirmed` flag in verdict.json.
- **I5 —** Provenance fill-breach max 3.1% (single non-primary cell), all others ≤ ~0.5%, under
  the 5% systematic threshold; breaches consistent with weekend/session gaps, not look-ahead.

## 8. What the data says (for Stage 5 interpretation — auditor's mechanism summary, not conclusions)

1. **Binding:** both prespecified primaries fail credibly → design §10 retire condition met for
   the CF-MR-004 fixed-parameter thesis.
2. **The exit decomposition worked as an instrument:** it localises the loss precisely — E0's
   moving-target loss engine is real (freezing recovers +0.8-1.9 net/bar on JP225/US2000), the SL
   adds negative value (fires when the basket signal is jointly wrong; 0/20 EURUSD stops had
   spread reversion), the time-stop is benign. Nothing in the exit set can rescue the entry.
3. **The availability→tradability gap is an entry-seam effect:** measured races condition on
   confirmed close-breaches at depth ≥ band; traded limit fills condition on marginal band touches
   (D = z\*σ exactly, adverse selection included). JP225 realized inward share 0.52 vs measured
   0.696. Any follow-up must move the *entry* object toward the measured conditioning event
   (e.g. enter on confirmed breach at next open, market order), not touch exits again.
4. **The extend-arm positive field is one unclaimed phenomenon, not per-cell edges:** 53
   never-admitted cells with net ci_low > 0, exclusively extend/allow arms, across 10
   instruments, positive every year 2021-2024, surviving 50-85% of a garbage-basket shift —
   a 4h ladder scale-in own-price MR harvest. Inadmissible for CF-MR-004 (per-cell statuses
   stand); **operator-directed disposition: open a dedicated candidate family** with a
   basket-free trigger and cost-stressed, ladder-depth-aware design. Characterise the mechanism
   before revisiting the phase-shift control's semantics on mixed P&L (§5.4).
5. JP225's residual P&L is Asia-session-structural.

**GATE handoff:** audit PASS; proceed to Stage 5. Stage 5 must: implement W1's re-labeling in
`report.md`; carry W3's constraint (no "construction-specific" claim for US2000; collapse
fractions disclosed); record the registry disposition — retire the CF-MR-004 fixed-parameter
thesis, log the 4 leak cells, record the extend-field phenomenon as disclosure, and register the
new own-price ladder-harvest candidate family (operator-approved 2026-07-03, pending its own
design.md); no TEST read spent; W3 filed as a KB lesson-candidate.
