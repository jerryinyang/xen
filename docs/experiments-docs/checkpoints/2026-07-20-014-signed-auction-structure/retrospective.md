# Checkpoint-014 Retrospective — Signed Auction Structure: Instrument Build → Spine → Breadth

> **STATUS: CLOSED — operator-directed 2026-07-21.** Checkpoint-014 (source Phases 0–5) is
> complete. **Family CF-SIGAUC-001 stays `REGISTERED` — no status transition** (§4): the
> designer's Addendum v1.1 closure logic (§3.3) requires a *third* independent powered null
> (S9 absorption) before the family closes, and that screen is not yet run. The signal-level
> grade transitions from the addendum (S1 demoted, S3 Δ+ deleted, S2/S3-base/A6/A8 confirmed)
> are recorded here and carried onto the family card. Next work opens as **checkpoint-015**
> (§6). No TEST contact anywhere in this checkpoint; holdout SEALED throughout.

**Checkpoint:** 014 · **Opened:** 2026-07-20 (design SIGNED, D1–D6) · **CLOSED:** 2026-07-21
**Family in scope:** CF-SIGAUC-001 (Signed Auction Structure) — stays REGISTERED
**Lane:** INFR → SPDR → XENA (XENA deferred to ckpt-015)
**Source addendum received:** `signed_bar_framework_addendum_v1_1.md` (2026-07-21) — the designer
converted the framework's grades from hypothesis to empirical state on this checkpoint's evidence;
where it conflicts with the base document, the addendum governs.
**One-line outcome:** the measuring stack is real and audited (the founding premise — exact per-bar
taker delta is a **measurement** — is verified end-to-end), but **both tested edges failed**: the
price-only session spine reproduces without conditional skill and dies after cost (P-01), and the
first signed refinement (S3 trap-load) is a **powered null** on three independent boundaries. The
family's flagship claim — signed value *where price is blind* (S9 absorption / S14 divergence) —
remains untested and is the sole reason the family is not closed here. **Four TRAIN-only items,
zero counted TEST reads.**

---

## 1. Objectives vs outcomes (checkpoint design §Objectives)

| Checkpoint objective | Outcome |
|---|---|
| 1. Register CF-SIGAUC-001 as a formal REGISTERED family | **DONE** — D1 rows appended 2026-07-20, consistent with the D0 card (0 unexplained deltas) |
| 2. Build + validate measuring instruments before any hypothesis | **DONE** — INFR-017 (A8 provenance PASS, A5 baselines frozen, signed-bar lane) + INFR-018 (hash-pinned instrument registry `5c386984…`) |
| 3. Reach the master go/no-go (Phase 4 spine) with the money floor first | **DONE** — SPDR-007; floor computed first (TP1 above floor on size), master gate disposition NOT_WORTH |
| 4. Map where the logic pays across the cross-section (Phase 5) | **DONE** — SPDR-008 breadth (296 denom / 194 A5-fitted); no signed cluster; only unsigned P-01 geometry reproduces |
| 5. Resolve holdout mapping + universe rules as reproducible declarations | **DONE** — CONFIRM-bank adaptation (§5 D3) + universe rules (§6, AMENDMENT-1 sized to 296) declared and code-asserted |

All five objectives met. The checkpoint delivered its designed purpose: **discover an absent edge
cheaply, in TRAIN-only items, at zero holdout cost** — the addendum grades the experimental path
itself (Appendix B) CONFIRMED on this basis.

## 2. The experiment arc

| ID | Role | Outcome |
|---|---|---|
| **INFR-017** | Phase 0 — signed-bar lane, A8 provenance, A5 baselines | **HYP-I1 PASS** — taker split reconciles bit-exactly to raw trades (20/20 symbol-days, worst rel dev 0.0); archive `side` = aggressor (Buy-PlusTick 26:1). Baselines frozen `1b7244c8…`. **`SpreadBps` pinned UNUSABLE** (mean-print differential, negative in 32–40% of BTC/ETH TRAIN minutes) → §2.5 spread layer UNAVAILABLE |
| **INFR-018** | Phases 1–3 — anchor race, A6 discriminator, kernel/class validation | Instruments frozen: anchor **A-USOPEN·L=15**, A6 **D4-t50-w30·δ=0** (price-only won; flow-augmented lost the race), kernel **K-UNIFORM** (calibrated). Registry `5c386984…`. Integrity clean (future-shift + path-swap collapse; plants fire). **Anchor selection contrast weak** (E≈+0.10, CI through 0) — a frozen *parameter*, not a proven edge |
| **SPDR-007** | Phase 4 — statistical spine (S1+S2), master go/no-go | **NOT_WORTH** (price-only spine, P-01). Protection quantile reproduces (pooled calib_err +0.028), **but accepted breaks add ≈0 over matched unconditional** (race 0.333 vs 0.343) and sit **below cost-adjusted breakeven on all 5 majors** (w−p0ᶜ −0.05 to −0.14). Control hits the signal's own level 67.5%. Per-symbol census 51 reproduce / 25 drift / 21 broken (SOL p70 broken +0.105) — pooling masked it |
| **SPDR-008** | Phase 5 — breadth + S3 trap-load (Δ+) | **NOT_WORTH** (signed warrant). Trap-load monotonicity a **powered null** on IB (ρ −0.015) / prior-VA (+0.023, flips negative on CONFIRM) / prior-extreme (−0.033), all inside MDE≈0.02 at n in the tens of thousands. K=3 ruled noise: 7 positive cells vs 6.0 expected, **10 anti-monotone mirror cells**. Only reproducing edge = **unsigned** failed-break geometry (~30–55 bps MFE, not load-dependent) |

## 3. Reads + holdout state

- **Global 30% holdout (≥ 2025-01-08): SEALED throughout.** Never queried on any item; holdout-safety
  self-tests PASS. The one disclosed INFR-017 holdout *touch* (a data-quality column's distribution,
  corrected to TRAIN, no shot consumed) was operator-CLEARED 2026-07-20; holdout remains SEALED for
  all evidential purposes.
- **Counted TEST reads: 0.** SPDR spends no reads; the reserved TEST band (`2023-12-18 → 2025-01-08`)
  was untouched. `test-read-ledger.md` unchanged.
- **CONFIRM band is TRAIN-INTERNAL** (D3), not programme out-of-sample — labelled as such in every artifact.
- **Registry:** evidence rows appended to the family card §10 and `multiplicity-registry.md`; no status
  transitions during the checkpoint (append-only). All items RETAINED.
- **Apparatus produced (durable):** signed-bar catalog lane (`SignedBar` + `data/catalog_sigbar/`),
  A5 seasonal baselines `1b7244c8…`, acceptance/trap modules (`xen.sigbar.trap`), frozen instrument
  registry `5c386984…`.

## 4. Family-status decision — KEEP REGISTERED (operator-directed)

The pipeline separation is binding: family status changes happen only at a retrospective. **Decision:
CF-SIGAUC-001 stays `REGISTERED` — no transition.** This is a KEEP, the low-risk direction, and it is
*dictated*, not discretionary: the designer's Addendum v1.1 §3.3 states closure requires a **third
independent powered null** (S9 absorption marginal value ≈ 0), and §1.4 states that closing before
framework-falsifiers #3/#4 are exercised "would violate the framework's own closure logic." Two nulls
lower the prior; they do not close the family.

**Why the two nulls do not settle the flagship claim.** S3 trap-load was the most **price-adjacent**
signed claim in the catalog — a Δ tag on geometry price already sees. Its null is *adjacent* evidence
against the flagship (it lowers priors), not a test of it. S9 (effort without result at a shelf) and
S14 (CVD decoupling from price) are the mechanisms **definitionally invisible to price alone** — the
tier's actual thesis. They are untested.

### Signal-level grade transitions recorded (from Addendum v1.1 Part 1) — carried onto the card

| Grade | Item | State |
|---|---|---|
| **CONFIRMED** | A8 (provenance), S2 (excursion *object*, + mandatory per-symbol census clause), S3-base (unsigned failed-break geometry — as characterisation, not strategy), A6 (discriminator constructible), Appendix B (the experimental path) | measurement / characterisation confirmed; none is a strategy edge |
| **DEMOTED** | S1 (session breakout → `==`; retained only as an **operational anchor**, not an edge-bearing gate), A7 (anchor "stable" ≠ "edge-bearing"), §2.5 spread layer (UNAVAILABLE until tick-floored spread rebuilt) | scoped to the daily US-open session object; prior on untested horizons lowered, not neutral |
| **DELETED** | **S3 Δ+ (trap-load monotonicity)** — powered null, binary-mechanism rule; any future signed-trap proposal needs a *new written mechanism*, not a re-parameterisation | M4 claim-2 deleted with it; M1 SUSPENDED (its S1 direction layer is dead here); Phase-6 gating premise redesigned gate-free |
| **UNTOUCHED** | S4–S6, S8, **S9, S14**, S10/S11/S13/S15/S16, M3/M5, and the micro/structural/funding-cadence horizon menu | neither confirmed nor refuted; framework-falsifiers #3/#4 remain open |

## 5. Lessons (ratify into KB at the next boundary)

1. **Reproduction is not skill.** The Protection quantile reproduced cleanly and meant nothing tradable —
   price paths have quantiles. The master gate must be a **conjunction** (calibrates AND beats a matched
   unconditional control AND clears the cost floor); a gate that can pass on calibration alone is
   defective. [Addendum §2.1] [[quantify_not_qualify_base_conditional]]
2. **Count both tails.** K=3 was ruled noise not on "7 vs 6 expected" but on **10 anti-monotone mirror
   cells** — the positive tail was not even enriched over its own negative. Single-tail "≥k winners"
   promote rules mis-promote. [Addendum §2.2]
3. **Pooling masks per-symbol breakage.** Pooled calib passed while 21/97 symbols were broken (SOL +0.105).
   Every pooled effect must co-report its per-symbol census. [Addendum §2.3] [[quantify_not_qualify_base_conditional]]
4. **Sparse events break day-block derangement nulls.** Only 60 of 7,070 events were derangeable within a
   calendar day; sign/side nulls on session-scale events need blocks wider than the day. [Addendum §2.4]
5. **Cost, again, is the wall — and here it is partly unmeasurable.** `SpreadBps` is unusable, so every
   net breadth claim currently carries an unmeasured spread term that concentrates exactly where a breadth
   map places its soil (illiquid alts). No net claim is admissible until a tick-floored reconstruction
   exists. [Addendum §2.9] [[cost_model_and_injection]]
6. **The cheap-death path worked as designed.** An absent edge resolved in two days / four TRAIN-only items /
   zero reads at 296-name scale — the SPDR breadth-before-depth discipline paid off exactly as intended.

## 6. Next — checkpoint-015 (the absorption screen)

Per Addendum v1.1 Part 3, the revised path supersedes Appendix B's Phase 6 onward. Opened as a **draft
checkpoint-015 design** (`docs/experiments-docs/checkpoints/2026-07-21-015-signed-value-absorption-screen/design.md`),
operator decisions pending:

1. **Phase 6′ — S9 absorption screen (next spend; cheap, TRAIN-only).** Does signed absorption add
   marginal value over the unsigned Climax-hold class on the same events? **Gate-free**, location-qualified
   (balance edges / prior-value edges / defended bands), marginal framing (signed − unsigned on identical
   events). The single screen that carries the family's fate: soil ⇒ the depth spend is warranted; a third
   powered null ⇒ close the family on the session horizon.
2. **Phase 6′b — S14 divergence (rides along).** Gated by a one-paragraph mechanism-differentiation memo
   written *before* the run (why integration/location/multi-bar structure creates information bar-level
   trap load did not) — so an S14 null cleanly kills the *mechanism family* rather than laundering the S3
   null through a new name.
3. **Parallel / non-blocking:** tick-floored per-symbol spread reconstruction (prerequisite for any net
   breadth claim, blocks nothing at the screen stage); trimmed/median re-read of the unsigned bounce (cheap;
   converts the 30–55 bps characterisation from upper bound to estimate or kills it); horizon-menu screens
   (required only before a *whole-family* close, per §2.10).

**Also on the table (operator's call, out of the addendum's scope):** chapter-04 rollover has been
available and deferred since ckpt-013. With this family one screen from possible closure and the
apparatus mature, it is a natural boundary — but the addendum's path (ckpt-015 S9 screen) does not
require it.

---

*CLOSED — operator-directed 2026-07-21. Evidence: `SPDR-007/{report,analysis}.md`,
`SPDR-008/{report,analysis}.md`, `INFR-017/report.md`, `INFR-018/report.md`, the family card
`cf-sigauc-001.md`, the designer handoff `source-designer-handoff.md`, and the designer's
`signed_bar_framework_addendum_v1_1.md`. Checkpoint design: [`design.md`](design.md).*
