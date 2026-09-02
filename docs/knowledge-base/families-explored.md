# Strategy Families Compendium — Every Hypothesis, Every Candidate, Every Verdict

> **Canonical disposition index (2026-08-08).** This file is the programme's single disposition
> index. It replaced the former families-explored.md disposition tables with the full
> strategy-families compendium content; prior tables are in git history. Live per-family cards
> remain authoritative for registration detail: `docs/signal-registry/candidate-families/`.

**Purpose.** A single extraction of everything the Xen research programme has tested: every
candidate strategy family, every screen and hypothesis, all arms and variants, the verdict on
tradability/deployability, the reason for each disqualification, and what looked promising from
each arc. Written 2026-08-08 as a consolidation of the knowledge base, the signal registry, the
reviews, and the chapter archives (see [Source map](#source-map)).

**Currency.** Programme status at 2026-08-08: Chapter 05 closed and archived; **no family is
open**; nothing in five chapters of experiments was ever deployed as a live, tradable strategy.
The standing programme frame is **INFR-022** (zero-cost model, sample-size context + direct
baseline comparison, PSR pairing, neutrality N1–N11). Historical "net of cost" numbers are
retained below as recorded; the live programme charges no cost and every money-bearing claim
carries the ZERO-COST-DISCLOSURE caveat.

**One-line headline.** Across ~20 registered families, five chapters and thousands of cells, the
recurring outcome is *real but sub-cost or non-causal gross effects, zero deployable net edges*.
The dominant disqualifiers, in order of frequency: **cost geometry** (the capturable move is
smaller than the round-trip cost), **availability ≈ random** (the entry carries no
signal-conditional move beyond matched random timing), **capture cannot convert availability**
(exit/stop/trail/hold/size levers move the payoff shape, not the mean — the `W/L` mirror),
**entry-seam mismatch** (the traded fill event differs from the measured event), **print
artifacts** (passive-limit fills look like edge), and **one look-ahead defect** that produced the
programme's only false `DEPLOYABLE_CONFIRMED` (L-01).

---

## 1. Programme context: how the map is organised

- **The availability 2×2.** The programme's frame for what has been tested. Unconditioned
  single-instrument × directional price-geometry entries have repeatedly failed to establish a
  robust transferable edge against matched controls, but that is not a blanket closure of every
  conditional directional baseline. A new claim that a decision-time conditioner changes the
  baseline must be tested directly, with the conditioner treated as entry information rather than
  as a downstream rescue. The open frontier remains cross-sectional / magnitude / flow, alongside
  this explicitly bounded conditional-baseline question.

  ```
                 DIRECTIONAL target            MAGNITUDE / range target
  single-series │  TESTED → weak/unresolved     │  screened (CF-VOLEXP-001): typical range
                │  unconditioned; conditional  │  flat, only a tail-only hint
                │  baseline remains open       │
  cross-section │  screened (CF-XSECT-001):    │  UNTESTED
                │  NOT_ADMITTED (below band)   │
  ```

- **Chapters.** Ch.01 (price-geometry + referee, ~98 experiments, ~25 phases) → Ch.02 (EXP-001..025,
  SPDR-001..003, seven family arcs, all closed negative with recorded mechanisms) → Ch.03
  (XENA-001..003, CF-MTFCTX-001 retired, referee redesigned) → Ch.04 (Nautilus/Bybit migration,
  exact taker volume, CF-HTFCAP/EPSOSC/SIGAUC closed) → Ch.05 (structural volatility-and-direction
  programme, CF-VOLDIR-001 retired; the joint `(p,W,L)` sits at break-even; `W/L` is not a free
  lever).
- **Read budget.** Two global-holdout shots ever existed; both are SPENT (EXP-032 old dataset;
  EXP-097 new dataset — the latter spent-on-defect, non-refundable). TEST strata cap at 2 counted
  reads lifetime. Chapter 05 consumed 0 TEST reads and 0 multiplicity slots.
- **The referee.** The evaluation gate is itself a frozen, hash-pinned apparatus (Chapter-02
  renewed §10.3a at q*=0.75 + E6 P*-gate + 15m domain); live evaluation frame is INFR-022.

---

## 2. Master disposition table

| Family | Thesis class | Status / verdict | Disqualification (mechanism) |
|---|---|---|---|
| **framework-referee** | The evaluation suite itself (EXP-001..019) | **CONCLUDED / FROZEN** | Superseded by INFR-022 live frame; frozen gate remains calibration history |
| **CF-AVWAP-001** | Anchored-VWAP bounce on regime pivots (continuation pullback) | **CLOSED** (gross-positive, net-negative) | Cost-dominated; exits/entry/anchor flat; EURUSD holdout shot spent INCONCLUSIVE (P-03) |
| **CF-HA-HARAMI-001** | HA-harami exhaustion reversal on strong moves | **CLOSED / marginal** | Real median edge, mean killed by same unfilterable tail; OOS ≈ random (P-01 lineage) |
| **CF-CAPGEO-001** | Data-derived exit/capture geometry on frozen entries | **RETIRED — NOT_CONFIRM** | Exit-invariant failure: availability ≈ random on the frozen entries (P-04) |
| **CF-MR-001** | RSI-2 fade + EXIT-RCT favourable-limit exit | **CLOSED — REFUTED (retracted)** | One-bar look-ahead in the exit limit; causalized the strategy is net-negative even gross (P-05, L-01) |
| **CF-VOLEXP-001** | Single-series magnitude/vol-expansion availability | **CLOSED — NOT ADMITTED** | Typical range flat/below random; only a tail-only long-vol hint; fails cross-axis Holm (p=0.0652) |
| **CF-XSECT-001** | Cross-sectional relative-strength directional availability | **CLOSED — NOT ADMITTED** | Dead-by-absence: S=1 ≤ S*=1, below coin-flip band (P-06) |
| **CF-FLOW-001** | Order-flow / liquidity-imbalance screen | **RESERVED — NEVER OPENED** | Not run at G-019 (terminal branch reached without it); tick-volume proxy historically inert (P-07) |
| **CF-MR-002** | Causal RSI-2 fade, cTrader-primary, `rct[di-1]` | **EXONERATED / NOT-TRADABLE 34/34** | Fade beats naive momentum but net-negative absolute; leak-clean on faithful engine fill |
| **CF-MR-003** | Deviation-from-HTF-anchor mean reversion, limit-at-anchor | **RETIRED** | Availability real (36 passes) but capturable move < round-trip cost; 0/24 powered at 15m (P-10) |
| **CF-MR-004** | Cross-instrument fixed-param spreads, limit entries | **RETIRED (CREDIBLE_NEGATIVE)** | Entry-seam mismatch: limit-touch fill ≠ measured confirmed-breach; adverse selection; no exit unlocks |
| **CF-MR-005** | 4h ladder scale-in own-price harvest | **RETIRED** | Episode-net WASH; random-timing ladders reproduce per-leg CI_low>0 with no signal; survivor = 2022 drift carry (P-11) |
| **CF-VOLHARV-001** | Two-sided oscillation harvest (rebalance + grid) | **RETIRED** | Structure failure: cadence collapse, cap-lock, censored inventory erases harvest; rebalance premium ~100× below design (P-12) |
| **CF-CSRR-001** | Cross-sectional consensus-residual reversion (baskets) | **RETIRED (availability)** | Residual reverts (VR<1 everywhere) but hedged idiosyncratic component ≈ 0; leads effect-at-MDE (P-13) |
| **CF-HTFDI-001** | HTF ±DI continuation conditioning (1h→5min) | **RETIRED (magnitude, not existence)** | Channel real and replicates blind but ≈1–4 bps/trade after capture dilution — below cost (P-14, L-21) |
| **CF-MTFCTX-001** | HTF context filters on naive controls (XENA portfolio) | **RETIRED (substrate exhaustion)** | All three substrates spent: random=noise, momentum=no structure, reversion=cost-fatal passive-limit print (P-10 fifth vehicle) |
| **CF-HTFCAP-001** | HTF direction × volatility × capture scale (Bybit) | **CLOSED — CHARACTERISED (not refuted)** | Real BTC gross directional edge, but 0/72 cells net-positive vs ~18 bps cost wall |
| **CF-EPSOSC-001** | Vol-expansion arm → episode reversion (VOLARM) | **RETIRED — REFUTED** | Apparent edge = volatility-window clustering / AKRO drift pedestal, not armed reversion (P-16) |
| **CF-SIGAUC-001** | Signed auction structure (exact taker volume) | **CLOSED** | Three independent powered nulls: price spine, signed trap-load, D1 signed absorption (P-17..P-19); SPDR-010 (S14) and INFR-019 never run |
| **CF-VOLCONV-001** | Assumed volatility + late range-break direction | **CLOSED** (KB disposition; live card still header-`REGISTERED` — stale) | SPDR-011 L1 NOT SUPPORTED; residue not trustworthy (concentration/regime artifact; UNPOWERED) |
| **CF-VOLDIR-001** | Structural volatility + direction programme (25 perps + 3 cTrader) | **RETIRED — CHARACTERISED, NOT TRADABLE** | Joint `(p,W,L)` at net break-even on two universes (0/1,413 + 0/315 powered cells); `W/L` is the mirror of `p`; every volatility-adaptive device inert or worse |
| **XENA referee (INFR-006→009)** | Portfolio-adjudication layer | **REDESIGNED** | Extensive-F absolute floor inoperative at live scale; exit-(c) two-stage binder restored the route |
| **Referee-renew (E-series + E7)** | Chapter-02 rebuild of the referee gate | **COMPLETE / FROZEN** | §10.3a at q*=0.75 + E6 P*-gate + 15m domain hash-pinned; historical referee pin — live frame is INFR-022 |
| **infrastructure-validation** | VAL-/INFR substrate work (universe, 5-year re-collect, ports) | **Ongoing infra (not a strategy)** | VAL-003 universe admit; INFR-003 / VAL-005 5-year dataset; VAL-002 cTrader port suite — apparatus only |
| **Nautilus/Bybit (INFR-010..020, VAL-008)** | Engine migration, fenced catalog, signed bars, emission recon | **COMPLETE as apparatus** | VAL-008 39/39; taker volume 20/20; `SpreadBps` UNUSABLE; no deployable strategy edge from the stack alone |

Every family is **retained** (file-drawer), never deleted; none is reopenable by
re-parameterisation — only by a genuinely new information source or mechanism under its own D0.
The three infra rows above are not strategy candidates; they are listed so this table stands as
the programme's **single disposition index** (superseding the former families-explored.md tables).

---

## 3. Chapter 01 families (price geometry + the referee)

### 3.1 CF-AVWAP-001 — Anchored VWAP bounce on regime pivots

**Thesis.** An AVWAP reset at deterministic trend-regime pivots acts as support/resistance; bounces
from it carry real-price reaction and lifetime moves.

**What was tested.**
- Substrate/readiness (EXP-020), fixed-horizon signed reaction H∈{1,3,6} (EXP-021), original
  lifetime band-target/trend-change completion (EXP-022), first full candidate screen (EXP-023).
- Exits (Phases 010–011): MAD band+trend-change (BTC), fixed-horizon (FH) grid, structurally
  distinct families E1–E5 (HA-harami-size exit, HA trailing reference, Last-X trailing, adverse-band
  stop, target-conditional time-stop), per-instrument exit training grids (EXP-045).
- Entry params (Phase 012): `/ALPHA` volume-weight exponent, `/MA-DOMAIN` periods — flat.
- Anchor (Phase 013): significant-pivot anchor k=1.0 — **collapses to the running extreme**
  (coincidence 94.6–98.5%).
- Conditioning (EXP-035): session / %completion / trailing-vol terciles — 0 qualified dimensions.
- Registered but unopened: `/LB`, `/MB`, `/ATR` regime detectors, `/XTF`, `/BAND`, `/EXIT` overlays.

**Verdict.** **CLOSED.** Bounce reaction gross-positive (+3.8 / +9.1 / +37.6 bps across domains;
lifetime favourable-rate advantage 22–26pp; 31/37 cells gross-positive after per-instrument
training) — but net EVIDENCE_AGAINST under conservative round-trip cost (EXP-030), net medians
−5…−7 bps at every grid point (EXP-045). The one sanctioned global-holdout shot (EXP-032,
EURUSD-4h, n=27, +20.6 bps) was margin-insufficient → INCONCLUSIVE; EURUSD-4h permanently
contaminated. EXP-047 showed the lifetime move is 5–9× the cost floor in all 51 cells — **but so is
the matched random control's**: the bounce trigger accesses no privileged move sizes.

**What looked promising.** (a) The gross bounce reaction is real and survives across domains.
(b) Fixed-horizon exit recovered ~+16 bps vs BTC on the same TEST events on EURUSD-4h — capture
efficiency is a real lever *on that cell* (non-upgradable after the holdout was spent). (c) The
lesson that became the programme's pivot: *move availability was never the constraint; capture
geometry is* — later refined into the availability-first rule.

**Reason disqualified.** Cost-dominated (Mode B: availability without capturable residue) on the
old narrative; later matched-control work established the deeper cause — event MFE ≈ control MFE
(Mode A). P-03: re-open only with a new universe powering 4h *and* a new exit mechanism.

### 3.2 CF-HA-HARAMI-001 — Heiken-Ashi harami at trend exhaustion

**Thesis.** An HA harami (latest HA body inside the prior body) at the exhaustion of a strong
impulsive move marks a trend reversal with lead time over the ZigZag/MA confirmation.

**What was tested** (the full barrier + position-management surface, two substrates).
- 014-A: readiness (EXP-048), benchmark 3-barrier capture rate (EXP-049: 0/99 viable at the
  r≈0.50 null), position-in-move context (EXP-050: haramis front-loaded, not at exhaustion),
  strong-move filters `/STRONG-STAT` `/STRONG-HA` (EXP-051), direct-vs-confirm (EXP-052:
  confirmation arm universally worse).
- 014-B on the **ZigZag substrate**: favourable-target alts (EXP-056: no improvement), adverse
  `/ADV-NONE` (EXP-057: improves median), third-barrier alts (EXP-058: no improvement), partials
  `/EXIT-PARTIAL` V2A (EXP-059: improves), structure trail + uncapped trail (EXP-059B/066: no
  improvement), combined champion (EXP-060: 0/99 beats MA baseline).
- Phase 015 on the **MA(20,50) substrate** (dual parallel objects, native vs hybrid): benchmark
  geometry (EXP-061/014), favourable-target VP/MAG variants (EXP-064: VP gain is a substrate
  property), third-barrier variants (EXP-065: refuted on both substrates), position management
  (EXP-066: only native PARTIAL-V2A composes), combined champions (EXP-068: N-PARTIAL-V2A and
  N-V2A×ADV-NONE both compose on TRAIN).
- Screening → TEST: EXP-071 portfolio TEST **NOT_CONFIRMED** (0/6 cells; 4/6 median CI_low ≤ 0);
  loss-tail diagnostic (EXP-074: exhaustion magnitude separates the q05 catastrophe tail,
  rank-biserial 0.68–0.80, AUC 0.84–0.90 — but the pre-registered sign-consistency gate is blind
  to tail-shape effects); exhaustion-**cap** design (EXP-075: **not a lever** — the cap strips
  winners with losers; intrinsic entry bimodality).

**Verdict.** **CLOSED / marginal** (G-016, operator-directed). 6 counted TEST reads spent (1/2 per
stratum); holdout never touched.

**What looked promising.** (a) A real **median** edge on the MA substrate: M3 beats its own
matched-random in 85/99 cells (vs 3/99 on ZigZag) — the conditioned harami expresses genuine
signal-conditional availability on old data. (b) PARTIAL-V2A (even-thirds favourable scaling) and
uncapped adverse (`/ADV-NONE`) are the only surface levers that ever moved expectancy coherently.
(c) The robust non-4h FX core (GBPUSD/NZDUSD/GBPJPY ± EURUSD) was mean-positive even at the single
benchmark leg.

**Reason disqualified.** The mean is killed by a catastrophic left tail that is **unfilterable**:
high-exhaustion entries are bimodal — median-positive or catastrophic — and the feature that
separates the tail (EXP-074) is exactly the feature the consistency gate rejects; capping the tail
strips the winners too (EXP-075). On fresh 5-year data (EXP-081) favourable availability is below
random (17/46). Edge on old data under one geometry; marginal-to-absent OOS; reversal in held-back
folds. P-01 lineage.

### 3.3 CF-CAPGEO-001 — Data-derived exit / capture geometry on frozen entries

**Thesis (reverse-direction).** Rather than "how does this entry do under an arbitrary exit",
derive the exit from the entry's own realised return structure (freeze the rule, not the story) and
ask whether a data-derived exit beats conventional exits.

**What was tested.**
- Four frozen entry substrates: SUB-AVWAP, SUB-HARAMI-PARTIAL-V2A, SUB-HARAMI-V2A-ADVNONE,
  SUB-RANDOM (matched-control baseline).
- Readiness (EXP-080): 184/192 substrate-cells, 46 instrument×domain members.
- Characterisation (EXP-081): gross capture availability ≈ random — harami median MFE below random
  in 17/46, AVWAP coin-flip 28/46; only structure is the outcome shape (harami median +0.135 /
  mean ≈ 0, tailmass 0.0526 vs random 0.0437).
- Derivation (EXP-082): 552/552 valid triple-barrier exits — D1≡D2 on 184/184 (the catastrophe is a
  continuous tail, so `m_anti` is dormant 549/552 and the adverse leg reverts to a generic ~9-ATR
  MAE_q90 stop sitting **at** the catastrophe edge — the harami trap geometry re-derived).
- Screen (EXP-083): 98.2% (2033/2070) die at the gross screen; the data-derived D1/D2/D3 earned
  **no distinctive TRAIN support**; 4 S2-PASS cells are conventional exits (AVWAP-FH + RR-1.5/2/3)
  on one well-powered cell (AUDUSD-1h harami, n=988).
- Cost read-gate (EXP-085): 21/26 NET_POS but **all** in low-n S2-DEFERRED 4h cells; the only
  powered S2-PASS stratum is NET_INCONCLUSIVE.
- Confirmation (EXP-084): AVWAP-4h portfolio basket on the one sanctioned OOS read —
  **NOT_CONFIRM** — separates on TRAIN but all three economic OOS legs fail; the edge was
  **selection-region overlap** that reverses in the fresh folds; **exit-invariant** (0/11 exit arms
  positive OOS CI_low).
- Qualifier infra (Phase 017): ASS adaptive scoring + WF-EXPANDING walk-forward — ASS demoted to
  DISCOVERY_ONLY (shape-blind to the median+/minority-catastrophe shape; FPR k-fragile).

**Verdict.** **RETIRED** (G-018). 0 candidate slots, 0 counted TEST reads (portfolio-aggregate
disclosure only); holdout never touched.

**What looked promising.** Nothing tradable — but this is the programme's **cleanest negative**
and its methodological cornerstone: the exit/capture-geometry lever was **exonerated** for these
signals ("if sweeping exits does not move the verdict, stop sweeping exits"), the separability
gate was born here, and fail-cheaply (98.2% killed at gross for 0 reads) became canon.

**Reason disqualified.** Mode A: for single-instrument directional price geometry, the binding
constraint is upstream — no signal-conditional favourable excursion beyond random. P-04.

### 3.4 CF-MR-001 — RSI-2 mean-reversion fade + EXIT-RCT (the false positive)

**Thesis.** A short-period RSI(2) fade (10/90) — the programme's first *contrarian* entry — alone
or partitioned by a strategy-agnostic ATR volatility regime, produces signal-conditional favourable
excursion beyond matched random control.

**What was tested.**
- Availability screen (EXP-089): S_fam=28 > S*=7, axis perm-p ≈ 0.0002 → **ADMITTED**. The lever is
  the **bare RSI-2 fade** (CORE 28 cells; 15m 16/16, 1h 11/16, 4h 1/14; ~0.75 ATR favourable MFE,
  ~3-bar horizon). Vol-regime partition **inert** (LOW/MED/HIGH all ≈ CORE); TREND/FILTER variants
  counter-productive (S=0/1).
- Readiness (EXP-090): 20/32 powered cells; the exit-fill engine (1m intrabar) built and
  validated; 12 cells excluded for no finite MDE (later recognised as L-12 mode-2).
- Exit screen (EXP-091): **EXIT-RCT** (native reversion-completion target, 1m fills) is the only
  arm to net-clear — 5 cells/5 instruments all 1h. EXIT-ERT, ATR triple-barrier, RSI-revert-on-close,
  fixed-bar, partial/trail all die at screen. Mechanism: pure cost geometry (15m cost ≈ 2× gross;
  4h smallest ATR-fraction cost).
- 4h falsification re-screen (EXP-094): 6 powered cells admit, beating a matched-distance
  oscillation null 6/6 — the edge is the fade signal, not generic oscillation.
- Sequence (EXP-092): 11 carried cells SEQUENCE_PASS; robust core = six 4h + USTEC-1h + US2000-1h.
- One-shot TEST (EXP-093): **8/11 CONFIRM** at Holm-adj p=0.0011 — the programme's first
  net-positive OOS price entry (later retracted).
- Portfolio economics (EXP-095/096): causal ERC portfolio Sharpe 11.7 (later ~6.5 under v2 fill
  noise); diversification benefit SUPPORTED; circuit-breaker NEUTRAL at v2, tail-insurance at v3.
- Global-holdout release (EXP-097): **DEPLOYABLE_CONFIRMED** — B holdout Sharpe 6.639 (LB 4.762);
  7/8 cells positive; holdout shot SPENT.
- Cross-broker robustness (EXP-098): reproduced on a second broker's data (PPS) — Sharpe LB 5.97/6.10.

**Verdict.** **CLOSED — REFUTED (2026-06-26), all deployment claims RETRACTED.** The EXIT-RCT
favourable limit rested `rct_target[di]` (computed from bar `di`'s **own close**) as the intrabar
limit during bar `di`; the live-actable limit is `rct[di-1]`. This one-bar look-ahead inflated the
captured edge by **~+0.25 ATR/trade**. Causalized, the bare fade + EXIT-RCT is **net-negative even
gross**. It slipped past audit because numeric re-derivation re-ran the same contaminated module.
Exposed only by the cTrader port (XRSI-V1) + forward test. The 11 counted TEST reads and the
global-holdout shot are **spent-on-defect, non-refundable**.

**What looked promising.** (a) The gross fade availability is real and broad (G-020 stands —
gross MFE, no RCT limit). (b) Proactive reversion-completion limits beat reactive close rules
20/20 cells as a vehicle class. (c) The diversified 8-cell portfolio genuinely de-risked
(intra-position MTM lesson L-09). All of it was riding the look-ahead.

**Reason disqualified.** Mode C (spurious capture) — the programme's canonical look-ahead (L-01,
P-05, P-09). The causal re-run (CF-MR-002) confirmed: net-negative absolute even leak-clean.

### 3.5 Phase 019 screens — CF-VOLEXP-001, CF-XSECT-001, CF-FLOW-001

**What was tested** (family-agnostic availability screens at 0 slots / 0 reads).
- **Screen M (CF-VOLEXP-001, single-series × magnitude):** typical-range read is **dead** (NR7
  conditioned median range *below* random, Δ̂ med ≈ −0.28 ATR); the only non-null thread is the
  rare catastrophe tail (NR7 compression→expansion; ~0.5–1.1 extra catastrophe events/100; tailmass
  Δ>0 in 15/16·15m cells). Single-axis provisional ADMIT (S=3 > S*=2, perm-p 0.0326) that **failed
  the cross-axis Holm** (adjusted p=0.0652 > 0.05).
- **Screen X (CF-XSECT-001, cross-sectional × directional):** cross-sectional rank/divergence
  conditioning **degrades** favourable availability at fast domains (per-domain mean Δ̂: 15m −0.26,
  1h −0.15, 4h ≈ 0); S=1 ≤ S*=1, below the coin-flip band → **dead-by-absence** (perm-p 0.323).
  Mechanism: the decile fires after the trailing-20-bar relative move — no favourable continuation
  beyond a direction-matched random clock.
- **Screen F (CF-FLOW-001, order-flow):** never opened — the terminal branch was reached without
  it; tick-volume-weighted construction is historically inert (EXP-046; broker-dependent proxy).

**Verdicts.** Both screened cells CLOSED and retained; G-019 reached the **terminal branch**:
price-derived information — single-series magnitude *and* cross-sectional relational — exhausted on
this dataset; the frontier is **non-price data acquisition** (a data decision, not a modelling
one). The operator override that re-opened the price surface for CF-MR-001 is what followed.

**What looked promising.** The NR7 tail hint (long-vol, not directional) — parked as a "pass on the
tail read is a long-vol finding, not a tradable directional edge". Cross-sectional remains the
a-priori mechanism favourite **on other endpoints** (P-06: re-screen with a different target).

---

## 4. Chapter 02 families (MR renewal, harvest, cross-section, HTF)

### 4.1 CF-MR-002 — Causal RSI-2 fade (cTrader-primary benchmark)

**What was tested.** The CF-MR-001 entry with the causal `rct[di-1]` exit, engine-realized intrabar
fills, run in the cTrader StrategyHost over 17×{1h,4h}=34 strata, adjudicated under three referees;
future-destroy tripwire mandatory.

**Verdict.** **EXONERATED / NOT-TRADABLE 34/34** (EXP-006). Net P&L negative on all 34
(−0.03…−9.66 bps/active bar); binding leg = the L3 absolute neutral floor — the fade **beats a
naive momentum baseline but is net-negative in absolute terms**. Leak-clean (future-destroy
collapsed 0.000/34) — the L-01 falsification confirmed on the faithful engine fill.

**What looked promising.** The fade-vs-momentum relative edge — i.e., the RSI-2 fade does contain a
*relative* signal; the veto is absolute economics, not signal absence. (Same wall as every MR
vehicle: cost vs capturable move.)

### 4.2 CF-MR-003 — Deviation-from-HTF-anchor mean reversion

**Thesis.** Entries conditioned on a cross-domain deviation series (price − higher-domain anchor)
that is itself characterised mean-reverting (VR + half-life screen) show reversion beyond a
dislocation-matched control.

**What was tested.** 5 anchor series (S1 CENTER rolling-median, S2 RANGE Donchian midline, S3
DETREND rolling-OLS residual, S4 OU equilibrium, S5 SPREAD rolling-β basket) × 3 domain pairs
(4h/1h, 4h/15m, 1d/1h); native target-based availability re-screen (EXP-009: **36 leak-clean
per-stratum reversion passes** — S5_SPREAD 20, S3_DETREND 14, S4_OU 2); then the form-2
limit-at-anchor fade in-engine at 1h (EXP-010, 0/5 powered) and 15m (EXP-012, **24/24 powered,
0/24 admit**, every CI_low ≤ 0, net −0.77…+0.04 bps/active).

**Verdict.** **RETIRED.** Availability is real; the capturable move never survives the
capture/cost seam — shorter horizons multiply episodes but shrink the per-episode move against the
same round-trip cost.

**What looked promising.** The native re-screen methodology (L-13): target-based estimands
(anchor-hit +2.9pp, fraction-recovered +2.7pp over a dislocation-matched null) rescued a family the
inherited MFE/random-timing vehicle had falsely exonerated — the anchor-reversion substrate exists.
S5_SPREAD FX majors and S3_DETREND were the robust anchors.

**Reason disqualified.** Cost/capture veto (P-10); also the L-13 vehicle-fit lesson (the first
screen's verdicts were vehicle artifacts, not family readings).

### 4.3 CF-MR-004 — Cross-instrument fixed-parameter spreads, precalc limits

**Thesis.** Fixed-weight/ratio cross-instrument spreads (S6 pair, S7 fixed-weight basket, S8
relative-value index, S5 rolling-β redo) revert to anchor; precalculated limit orders at the
extreme, set-and-forget, exit at the anchor mean (form-1 event-reversion + form-2 refreshing limit).

**What was tested.** EXP-013 (confounded — form-1 exit silently dropped, form-2 TP frozen at entry:
**L-14**, the strategy that ran was not the strategy proposed); EXP-014 faithful redo (both exits
fire; still 0/38 strata net- and gross-admit — capture-vs-dispersion wash); EXP-014b (S8 streamlined
symmetry re-screen — 1h raw-passes are own-price auto-reversion leaks; collapse-verified
availability only on 4h JP225 p=0.696 and weak 4h EURUSD); EXP-014c lean bracket (both powered
primaries net-fail; 262-cell census: NULL 218 / UNPOWERED 22 / NOT_TRADABLE 14 / NET_ADMIT 4 /
REJECT_LEAK 4). Exit decomposition E0–E3: freezing the TP removes the moving-target loss engine,
the SL subtracts value, the time-stop is benign — **no exit rule unlocks the entry**.

**Verdict.** **RETIRED (CREDIBLE_NEGATIVE)**. Mechanism = **entry-seam mismatch**: the limit-touch
fill is a shallower, adversely-selected version of the measured confirmed-close-breach event
(JP225 TP-share 0.52 vs measured p_inward 0.696). P-10: a confirmed-breach entry object traded
natively is required; passive-limit entry on an MR fade is banned as a capture vehicle.

**What looked promising.** The extend-arm field (53 non-admitted cells net ci_low>0, year-stable
2021–2024, 50–85% phase-shift survival) — spun out into CF-MR-005. The form-1/form-2 exit-set
fidelity discipline became a standing pre-exec gate (L-14).

### 4.4 CF-MR-005 — 4h ladder scale-in own-price harvest

**Thesis.** Scaling into 4h dislocations with a ladder of deepening adds harvests short-horizon
own-price mean reversion; per-leg P&L fattens with add depth.

**What was tested.** Mechanism characterisation (EXP-015: per-event estimand → NO_MECHANISM_EVIDENCE
— an object-mismatch null, L-16); TEST persistence (EXP-016 — VOIDED: 3 counted reads spent-on-defect
on a corrupted multi-leg per-bar estimand, 3.8× inflation); VAL-006 canonical re-derivation (the
"61-cell field" collapses — 44/52 corrected CI-positive cells are e1 frozen-TP survivorship
artifacts; US2000 e3/extend/z15 = +9.5 bps/leg gross CI [−15.9,+32.0] ≈ 0 even at zero cost); the
deliberate ladder-harvest disposition probe (EXP-018: episode-net primary **WASH** in all residue
cells; random-timing kill test unfalsified — NZDUSD random ladder per-leg +31.5 CI_low +13.7 > 0
**with no signal** while the live arm loses).

**Verdict.** **RETIRED.** The per-leg positive is reproducible by matched-cadence random ladders —
the form is producible unconditioned (P-11). Surviving US2000 cell = 2022 long-drift carry on
deep-add inventory (peak 43 legs; return on peak exposure ≈ buy-and-hold).

**What looked promising.** None, as a strategy. The episode-native estimand lesson (L-16) and the
seed-battery control requirement (L-19: one random draw is a noisy yardstick; NZDUSD's +31.5 sat
above an entire 25-seed distribution of [−11.5, +8.6]) are durable methodology.

### 4.5 CF-VOLHARV-001 — Two-sided oscillation harvest

**Thesis.** Structures that can carry nonzero expectation from oscillation — rebalanced-exposure
(volatility pumping) and symmetric always-on grids — earn positive net harvest on range-persistent
instruments.

**What was tested.** HYP-001 falsification (EXP-019, 441 runs / 286,476 legs): the founding anomaly
(NZDUSD random-timing leg +31.5 bps) is a **sampling draw of a zero-mean construction** — analytic
E[gross]=0, 25-seed battery centres on 0 in every stratum. HYP-002 structure screen (EXP-020):
banded-rebalance arm (the classical w(1−w)σ² premium overstates the real rebalance premium by
**~100×**; true ~0.04–0.07%/yr, UNPOWERED) and symmetric-grid arm (1/4 MR cells positive: USDCAD
+132 bps/mo CI [+43,+257] survives commission/weekend/top-3/both-halves but fails the inverted-twin
sign-flip and the 60% cleanliness bar — 2022 = 67% of funding).

**Verdict.** **RETIRED.** The FX mean-reversion substrate genuinely exists (VR<1: NZDUSD 0.80–0.92
across holds) — but the tested structures **fail mechanically**: grid fills at 5–28% of implied
cadence, 3/4 cap-locked, censored ≤8-leg inventory erases 100–155% of realized harvest. **Structure
failure, not substrate absence** (P-12). A within-episode-clearing structure (rolling anchor, no
hard cap) = a NEW family.

### 4.6 CF-CSRR-001 — Cross-sectional consensus-residual reversion

**Thesis.** On a basket of co-moving instruments, a member's move away from the cross-sectional
consensus (median / equal-weight / weighted-implied) is dominated by transient idiosyncratic flow
and reverts within a bounded horizon; fade it hedged.

**What was tested.** 5 variants decomposed onto 7 component axes (consensus estimator × residual
normalisation × selection × hedge × execution × exit/stop × threshold); USD-strength-aligned
Currencies basket (EXP-021) and single-factor Indices basket (EXP-022), both 4h TRAIN,
execution-agnostic; US-bloc session-anchor follow-up on the USTEC lead (EXP-024). V5 execution
model (active confirmed-breach entry + passive rolling-consensus exit + time-only stop) was the
planned tradability vehicle — never reached.

**Verdict.** **RETIRED (availability)**. The residual **does** mean-revert (VR(2)<1 on 28/28 FX and
40/40 index cells; half-life ~1.4 4h-bars) — but **no mechanism-faithful (hedged) construction
clears multiplicity**: the tradable idiosyncratic component is ≈ 0; every survivor is drift/beta
(AUDUSD unhedged +9.4 bps fw_p .008 vs hedged twin fw_p .68). Disclosed leads (AUDUSD, USDCAD,
USTEC +4.7–4.8 bps p_perm .002) all retired as **effect-at-MDE** — reproduced, real, but at the
detection floor, USTEC-specific, no sibling reproduces (P-13).

**What looked promising.** The consensus-residual reversion is a genuine, reproducible
cross-sectional anomaly (VR<1 everywhere) — the idiosyncratic (hedgeable) part is what is missing,
not the substrate. Re-open route: a different cross-sectional endpoint or a construction that does
not route through argmax|s| event concentration.

### 4.7 CF-HTFDI-001 — HTF ±DI continuation conditioning

**Thesis.** The last closed higher-timeframe bar's directional state (Wilder ±DI) conditions the
sign of the LTF forward return — a magnitude-weighted continuation effect, amplified by high
volatility.

**What was tested.** SPDR-001/002/003 screens (with a same-day correction after audit: under-blocked
CIs and a mislabelled side-signed interaction; Thread B XAUUSD fade **withdrawn**); the graduation
experiment EXP-025: CTRL-02 momentum-breakout vehicle gated by HTF-DI on the full 22-symbol
universe, 1h/5min only, variants {di, atrL/M/H×di}, breakout lookback grid {2,3,4,5,8}, holds
{12,24,36,48}, SEL-NEIGHBOR plateau selection, WF-EXPANDING, 440 cells / 2.43M TRAIN trades, six
registered exit methods (triple-barrier, Last-X trail, HA trail, AE-stop-only, HTF-DI-flip,
opposite-breakout).

**Verdict.** **RETIRED — NOT SUPPORTED (magnitude, not existence)**. The conditioning channel is
**real and replicates blind** (USTEC 1h/5min dir_gap +0.09→+0.50 ATR, CI-clear under hold-matched
blocks; engine ref-arm + battery replication) — but the true effect is **≈1–4 bps/trade** at h48
after capture dilution: below FX commission and ~1/10 of the indices selection bar. 0/440
qualifiers; T1-terminal powered negative (MDE ≤ 5.2 bps). The "30–60 bps" graduation target was a
**4.1× unit inflation** (screen normalised by 5-min ATR; design asserted 1h ATR — **L-21**). Index
grid positives 99% drift-side aligned; no DI dose-response (P-14).

**What looked promising.** The replication itself: HTF conditioning of LTF sign is a real market
structure (not noise), just sub-cost at this granularity. Re-open requires a vehicle with ≥10×
per-trade capture (longer holds / different granularity) — the exact intent behind CF-MTFCTX and
CF-HTFCAP.

---

## 5. Chapter 03 — CF-MTFCTX-001 (XENA portfolio lane) and the referee redesign

### 5.1 CF-MTFCTX-001 — HTF context filters on naive controls

**Thesis.** HTF context (ADX strength, ±DI direction, ATR vol regime — 19 variants V00–V18) improves
signal quality of LTF entries; tested as portfolio selection over 2,736 candidates per universe
(19 variants × 3 domain pairs × 4 hold multipliers × 12 instruments).

**What was tested.** Three XENA universes: XENA-001 (CTRL-01 RANDOM control), XENA-002 (CTRL-02
naive momentum breakout), XENA-003 (CTRL-03 naive reversion via native limit orders, hold-or-float
profit exit). ~1M total search evals.

**Verdict.** **RETIRED (substrate-exhaustion, 2026-07-14)**.
- **RANDOM** (XENA-001): **MACHINERY-ALARM** — a pure-noise control certified 4/12 finalists (33%)
  vs a 0.75% null rate. Root cause: the `F_floor` absolute threshold on an **extensive** statistic,
  calibrated at 24 candidates/400 budget, inoperative at 2,736-candidate scale (L-25). Emission
  layer clean; adjudication layer defective.
- **MOMENTUM** (XENA-002): no detectable structure even unfiltered — live−permuted −1.41 vs the
  control's −1.67 no-structure bias ⇒ +0.26 above random, inside dispersion 2.90. Statistically it
  *is* the random control.
- **REVERSION** (XENA-003): real gross +1.958 bps/leg (CI [1.85, 2.07], 195k legs, all 12
  instruments positive) but **cost-fatal** (breakeven spread 0.705 bps median; 0/12 finalists at 1.5
  bps) and **91.2% of the edge is the passive-limit print** to the next grid open — the
  discriminating next-open control collapsed F̂ 23 → 0.09–1.93 (L-27: the permutation battery is
  confounded on limit-entry universes; P-10, fifth vehicle). V00 (unfiltered) 4.0× over-represented
  — but this read is **confounded** by the costless cadence-maximising objective (L-26) and is
  explicitly NOT the retirement grounds.

**What looked promising.** The naive-reversion gross leg being real +1.958 bps/leg across the whole
universe (pre-cost) — i.e. short-horizon reversion is a genuine property; the print artifact is the
enemy, not the mechanism. And the referee redesign (below) that this arc forced.

### 5.2 XENA referee redesign (INFR-006 → INFR-009)

**What was tested / built.** INFR-006 v3 extensive-F/plateau adjudicator (superseded — L-25);
INFR-009 exit-(c) two-stage binder (stage-1 screen fixes one subset → embargo → stage-2
leg-studentized LCB on an independent band; DUAL_CERTIFY e2e α̂ 5.0%; net 1.0 bps bound into the
objective). INFR-016 split the value chain: VALIDITY attestations stay HARD; VALUE reads become
operator-facing **report layers** (no machine `pass` fields; ≥2000-seed sign batteries; collapse
fractions reported, not auto-blocked — L-32).

**Verdict.** Route **restored** for portfolio adjudication; registry pins VOID on the INFR-010
Nautilus/Bybit stack until a fresh calibration cycle.

---

## 6. Chapter 04 families (NautilusTrader + Bybit USDT-perps + exact signed volume)

### 6.1 CF-HTFCAP-001 — HTF direction × volatility × capture scale

**Thesis.** HTF market state (DI direction × ADX × ATR vol regime) changes the conditional quality
*and economic scale* of LTF trades; hold scale (0.5×–4× HTF span) is a first-class axis.

**What was tested.** SPDR-004 (DI/ADX continuation × hold ladders on rule-selected top-10; promote
cluster K≥3 — SOL 4h/15m UNF cluster 5.9→50.1 bps/trade monotone), SPDR-006 (vol-regime facet:
DI×VOL_HI and DI_ADX×VOL_HI amplifiers, interaction-only scope; K=3 met on BTC+SOL with +26.6/+28.5
bps median lifts; standalone vol NOT a promote), then XENA-HTFCAP-001 (72 binding + 36 disclosure
cells; BTC+SOL; TRAIN+TEST exploratory window, no reserved OOS — 1/2 gate slots spent).

**Verdict.** **CLOSED — CHARACTERISED (not refuted)**. A **real, gate-attributable, sign-null-
clearing GROSS edge** on BTC `DI_ADX×VOL_HI adx25` H32/H64 (embargoed gross LCB +8..+18 bps, sign p
0.02–0.05, derangement collapse ~0.9) — but **0/72 cells and 0 subsets net-positive** (best net LCB
−4.6) against the ~18 bps taker+GAP+funding wall at 8–16h holds. Volatility is an **amplifier of
directional drift/continuation, not a standalone signal**. No untouched OOS remains; a fixed
lower-cost intraday product would be a new D0.

**What looked promising.** The BTC high-volatility directional gross effect — the first genuinely
positive gross finding on the new stack, robust to the derangement control. The question it leaves:
whether an intentionally directional, risk-managed volatility/trend exposure can clear exact
intraday costs (later answered by Chapter 05: the joint sits at break-even).

### 6.2 CF-EPSOSC-001 — Episode-clearing oscillation harvest (VOLARM)

**Thesis.** After a volatility-expansion arm (VOLARM), prices revert to a rolling anchor (RET_ANCHOR
/ HYBRID clears) — a within-episode harvest, explicitly not the dead P-12 grid.

**What was tested.** SPDR-005 (STRETCH + VOLARM market-entry episodes; K≥3 cluster on VOLARM×15m —
23–25 cells, 4 symbols, med lift +54–60 bps/episode, derangement collapse ≈0.95 — with binding
caveats: pooled median negative, concentrated cluster); XENA-EPSOSC-001 (top-1 REJECT-class on the
leak tripwire, collapse 0.395; only survivor = AKRO RET_ANCHOR dual short on a directional-drift
pedestal, single-symbol, seed-fragile); XENA-EPSOSC-002 (mass-aligned cross-symbol redesign:
certified 4-symbol subset fails stage-2 gross LCB −68.2 / net −102.1 and the derangement tripwire;
AKRO +450 bps/10 legs carries the pool — **the drift pedestal reproduced**).

**Verdict.** **RETIRED — REFUTED**. The apparent edge is **volatility-window clustering /
unconditional drift**, not the armed return-to-anchor mechanism (P-16, L-35: cross-symbol
membership ≠ diversification — one name can carry the point estimate).

**What looked promising.** The SPDR cluster was the strongest promote signal Chapter 04 produced —
before XENA showed it was drift. The mass-aligned redesign (XENA-002) and overlap-aware/contribution-
concentration analysis are the durable methodology.

### 6.3 CF-SIGAUC-001 — Signed auction structure

**Thesis.** Auction structure — where participation concentrated, which boundaries were accepted or
rejected, and **which side's aggression was rewarded or absorbed** (exact per-bar taker aggressor
delta, Δ = BuyVolume − SellVolume, from Bybit trade archives) — conditions forward price resolution.

**What was tested.**
- Infra: INFR-017 (raw-trade provenance — Δ verified bit-exact 20/20 symbol-days, aggressor-side
  semantics unanimous; `SpreadBps` pinned UNUSABLE as spread), INFR-018 (frozen instrument
  registry), INFR-020 (count-only candidate census).
- SPDR-007 (price-only session spine — the Protection quantile reproduces but adds ≈0 over matched
  unconditional timing; signal race 0.333 vs control 0.343; P-01 confirmed): **NOT_WORTH**.
- SPDR-008 (S3 signed trap-load monotonicity on IB/PVA/PRIOR boundaries — powered null on all
  three; 7 positive qualifiers vs 6.0 null-expected and 10 anti-monotone; K=3 ruled noise):
  **NOT_WORTH**.
- SPDR-009 (S9 signed-absorption marginal value at D1 1d/1m — powered null: +1.81 bps, CI
  [−3.62,+7.09], MDE 5.5; ρ +0.008; S9 median 0.0 bps vs an 11.3–13.0 bps floor; MIRROR arm larger;
  D2/D3/D4 event-rate-inconclusive 16/2/0): **NOT_WORTH**.
- **Never run (not covered by the close):** SPDR-010 (S14 CVD–price divergence, memo-gated rider);
  INFR-019 (tick-floored spread reconstruction — never built, so no net claim was ever admissible);
  structural and funding-cadence horizons.

**Verdict.** **CLOSED** (third powered null, D8). S3 Δ+ and S9 **DELETED** (binary-mechanism rule —
no threshold re-mining). **Explicitly not covered by the close**: S14 / SPDR-010 never run;
structural and funding-cadence horizons never screened; D2–D4 unpowered, not negative.
Durable assets: the signed-bar catalog lane, A5 seasonal baselines, `xen.sigbar.trap`/`absorb` —
exact taker-side volume survives as **data infrastructure, not edge**.

**What looked promising.** Two things. (1) The **unsigned failed-break bounce** at prior
value-area / prior-session extremes — the only object in the arc above its cost floor: +5–11%
relative MFE lift over matched random on PVA/PRIOR (reproduces both TRAIN bands, 194 symbols),
MFE:MAE ≈ 1.35:1. **Characterisation, not a candidate**: it is price-only P-01 geometry stripped of
the signed claim, no realized return was ever computed, and under the only exit tested (full
rotation to the opposite edge) 81% stop out (see [unsigned-failed-break-bounce-review.md](reviews/unsigned-failed-break-bounce-review.md)).
Re-opening needs a P-01-distinctness argument that survives without the signed input. (2) The data
itself: exchange-native taker volume is the first genuinely non-price information source the
programme has held — the named frontier.

---

## 7. Chapter 05 — the structural volatility-and-direction programme

### 7.1 CF-VOLCONV-001 — Volatility-to-direction conversion

**Thesis.** A causally known high-volatility state (daily rv20 percentile) predicts magnitude but
not sign; a completed 4h break of the prior UTC-day range supplies the sign; one fixed 4h episode,
entered at the next boundary, exited exactly 4 wall-clock hours later.

**What was tested.** SPDR-011 L1 (partial economics on 5 symbols: HIGH-vol breakout episode residue
after fees+funding+allowance): **NOT SUPPORTED** — the HIGH residue is not trustworthy
(concentration/regime artifact; UNPOWERED for ~10 bps). L2–L5 (volatility bite, conversion residue
vs identical unconditional breakout, TOP2 cross-sectional increment, signed-flow increment) and
EXP-099 (Nautilus physicality) never opened.

**Verdict.** **CLOSED** at L1 (programme/KB disposition); superseded by the structural
decomposition programme (separating the volatility claim from the direction claim rather than
assuming the first). **Registry lag:** the live card
`docs/signal-registry/candidate-families/cf-volconv-001.md` still headers as `REGISTERED` with only
SPDR-011 closed — treat the KB/compendium **CLOSED** as authoritative; do not re-open from the
card alone.

### 7.2 CF-VOLDIR-001 — Structural volatility + direction programme

**Thesis (programme-level, decomposed).** (A) Is volatility reliably modelable? (B) Does fast
direction have positive expectancy in bps under damage-when-wrong scoring? (C) What does the joint
`(p, W, L)` look like, and can capture geometry move it? (D) Cost. Failure must be *diagnosable*.
Two independent universes: 25 Bybit USDT-perps (top-25 by 30d volume, anti-survivorship) + 3
cTrader instruments (EURUSD/XAUUSD/USTEC, INFR-021 fence).

**What was tested** (vehicles **SPDR-012…018B, 021…024** — no SPDR-019/020 ever assigned; SPDR-011
is CF-VOLCONV, not this family; SPDR-016 superseded never-run; checkpoints 016/017/018; 0 TEST
reads, 0 slots).
- **SPDR-012 (A, vol characterisation):** persistence/level/regime/realised-measure/calendar/
  cross-sectional tools — H1/H4 range level adequate for conditioning; A-IC verified 0.3262 (100%
  CI-excluding-zero across 11 models).
- **SPDR-013 (B, direction expectancy):** SMA 14/25/50 benchmarks + deterministic ATR ZigZag
  direction, scored availability-when-right/damage-when-wrong/expectancy-bps — **signed (SMA)
  not adequate; ZigZag magnitude positive**; signed vol×direction product closed.
- **SPDR-015 (conditioners):** ordinal swing-size gate T-GT-CUR (21/21 coins × 3 models, hit ~+20pt
  over base, IC≈0.37), vol level-state labels (next-|oo| gap +35 bps HMM / +16 bps R-MARKOV),
  R-MARKOV multi-bar gate k=4/12 (16/16 coins, ΔBrier −0.025/−0.114) — **WORTH_EXPLORING**;
  k=1 next-bar NOT_WORTH.
- **SPDR-014 (zone/event MOMO vs MR):** INCONCLUSIVE/UNPOWERED (0/927 powered cells; band
  non-selective; DESIGN→CONFIRM sign flip 12/17); coherent SUGGESTIVE leads: shock-MOMO (pooled CI
  excl 0), E-TOUCH/E-CLOSE asymmetry, L→H vol-flip MOMO.
- **SPDR-017 (independent predicted-price mispricing):** model IC ≈ 0; DERIVED feature layer inert
  (A1−A0 median −5.8 bps, 5/16 improve) → NOT_WORTH; SPDR-016 superseded, never run.
- **SPDR-018 / 018B (D5, power the complete residue):** 37,791 cells (24,098 signed; 1,413 powered)
  on crypto and 7,578 cells (315 powered) on cTrader, with the identity
  `E[net] = p·W − (1−p)·L − cost`, `p_be_net = (L+cost)/(W+L)`, `edge = p − p_be_net`
  reconstructing to 1.46e-11 bps. 3,559 cells booked `NOT_RESOLVABLE` (median 7.87× short of target
  precision).
- **SPDR-021/022/023 (D8–D10, capture geometry on breakout / MOMO / MR vehicles):** every native
  volatility-adaptive device vs its fixed form, direct and reverse, with admission vs valuation
  device classification, origin-lens reads, capital-normalised estimands, labelled realised states,
  non-degenerate controls (the L-57..L-61 emission-contract rebuild); six TRAIN cells, 13/13
  reproduction hashes.
- **SPDR-024 (dedicated SIZE measurement):** vol-aware sizing with a capital-normalised,
  regime-labelled, counterfactual-bearing estimand, after the first emission was purged as defective
  (AMENDMENT-7 R1–R5 — the detection-floor scale lesson L-56).

**Verdict.** **RETIRED — CHARACTERISED, NOT TRADABLE** (2026-08-07, operator-signed). Five
structural findings:
1. **The joint sits at net break-even; nothing clears it.** 0 of 1,413 powered crypto cells, 0 of
   315 powered cTrader cells; crypto p 0.3887 vs p_be_net 0.4992 (edge −0.0728, gross −1.18 bps);
   cTrader p 0.4868 vs p_be 0.4855 (gross −0.080 bps = 0.006σ). **91% (crypto) to 96% (cTrader) of
   the distance is cost, not rate.** The structure replicates *more tightly* on the second
   universe (no shared instrument, venue, cost model or vendor).
2. **`W/L` is not a free lever** — it is ~97% the arithmetic mirror of `p` (R² 0.9667 / 0.9746,
   slope 0.9656): exit geometry moves the payoff ratio 36–67× while the hit rate moves inversely
   and the mean does not improve; 82.8%/93% of cells indistinguishable from the driftless mirror.
   The capture programme's whole premise was that this handle was independent. It is not.
3. **Adaptive capture geometry adds nothing.** MOMO and MR breach screens are the same trades
   sign-flipped (r = −0.98; "native geometry effect" was a direction artifact); admission rules move
   shared-trade value by exactly zero on ~2.3M paired rows; vol-gated hold is inert (0.03–0.60× its
   floor); vol-gated stop distance is *worse* than fixed; vol-scaled trails give back more when
   wider; nothing recovers after a vol-adapted stop.
4. **The one surviving lever — vol-aware SIZE** — reduces drawdown depth with a consistent sign
   (236/236 resolving rows, 6/6 cells) but a **magnitude below its own detection floor**
   (est/MDE 0.20–0.97); SPDR-024's rebuilt estimand intervals still cross zero at the governing
   treatment, with gate-permutation p-values frequently failing to reject exchangeability with a
   **random** gate.
5. **Vol state is not a selectivity filter** — HIGH−LOW never clears zero on mean or Sharpe at any
   cell's pooled level.

**What looked promising (parked, terminal `NOT_RESOLVABLE` — never refuted, never re-booked as
refutations).**
- **C2 shock-MOMO**: Asia-session shock continuation — M-3 live +22.6 bps at percentile 0.95 (n
  505) in the powered run; but 018B's comparator is not a neutral yardstick (its own mean runs
  +0.97 EU → +12.05 Asia; the Asia null lies entirely above zero and is blind upward), and an
  independent rebuild flipped P-MR 0.067 → 0.826. P1 skipped by operator; no 018C.
- **C3**: unpowerable in its registered form (1,946 unresolved cells fully levered, median 81×
  short; median cell needs ~201 years of 25-symbol history).
- **C9 / D3 / D4**: OPEN, never run. **P6**: Asia magnitude × shock ≈ +10 bps vs ≈ 0 in EU (162–184
  rows) — an **unregistered lead** (must be registered before it is screened).
- The **conditioner science** (SPDR-015): ordinal swing-size gating and multi-bar regime gates with
  real out-of-sample Brier improvements — useful as gates/labels for any future direction work.

**Reason disqualified (the structural statement).** Not an empirical null of "volatility
conditioning is weak" — a statement about the **geometry of the exit problem**: on this substrate,
win/loss ratio and hit rate are very nearly the same number, so the two-dimensional capture search
space is approximately one-dimensional, and moving along it does not move the mean. Because
91–96% of the gap is cost, **no successor on this substrate is evaluable at all while spread
remains uncharged** — the cost precondition binds before any modelling question. Re-opening
requires a **new information source** — not a new exit rule, volatility transform, or
re-parameterisation of the same lattice.

---

## 8. Cross-cutting: the recurring disqualifiers (with mechanisms)

| # | Disqualifier | Mechanism | Canonical evidence |
|---|---|---|---|
| 1 | **Cost geometry (historical Mode B)** | In the historical costed reads, the capturable move at the tested horizon was smaller than the applied round-trip cost; faster domains multiplied trades but shrank the move against that cost | AVWAP net-negative; MR-003 0/24 powered; XENA-003 breakeven 0.705 bps; HTFCAP 0/72 vs ~18 bps; VOLDIR 91–96% of the gap was cost |
| 2 | **Availability ≈ random (Mode A)** | Event MFE/path equals a matched random control's — no signal-conditional move | EXP-047, EXP-081, SPDR-007 (race 0.333 vs 0.343), SPDR-008 T4 (random timing gets 90–95% of the excursion) |
| 3 | **`W/L` mirror — capture can't move the mean** | `E[net] = p·W − (1−p)·L − cost`; near break-even, exits trade p against W/L along the zero line | VOLDIR: R² 0.9667/0.9746; 36–67× W/L movability with no mean improvement |
| 4 | **Entry-seam mismatch** | The traded fill event (limit touch) is a different, adversely-selected conditioning event than the measured one (confirmed breach) | MR-004 (TP-share 0.52 vs 0.696); P-10 |
| 5 | **Print / passive-limit artifacts (Mode C)** | Passive fills mark at a favourable price with no prediction behind it | XENA-003 (91.2% of edge is the limit print); L-27 confounded permutation battery |
| 6 | **Look-ahead in shared outcome modules** | A vectorized favourable-index pattern (`rct[di]`) inflates the edge; numeric re-derivation is blind to provenance | MR-001 (+0.25 ATR/trade; the only false DEPLOYABLE_CONFIRMED); L-01, P-09 |
| 7 | **One-name / one-window concentration** | Pooled or K-symbol results carried by a single volatile name or episode | EPSOSC-002 (AKRO +450 bps); CSRR (leads effect-at-MDE); L-35, L-61 |
| 8 | **Selection-region overlap / winner's curse** | TRAIN-selected cells reverse in fresh folds or the null tail | CAPGEO EXP-084; SPDR-008 (7 qualifiers vs 6.0 expected); L-23, L-51 |
| 9 | **Structure failure of the vehicle** | Harvest vehicles die on cadence collapse, cap-lock, censored inventory — not substrate absence | VOLHARV (fills 5–28% of cadence; inventory erases 100–155% of harvest) |
| 10 | **Effect at / below its own detection floor** | Real, reproducible, too small to resolve — universality of failure is the alarm | CSRR USTEC, SIGAUC leads, VOLDIR SIZE (est/MDE 0.20–0.97); L-56, P-28 |

**The unifying error the programme identified:** building or retuning **capture** (exits, stops,
trails, holds, size) before proving (a) the entry has signal-conditional availability, (b) the
traded fill event matches the measured object, (c) the residual is measurable at the chosen
horizon, and (d) causality holds. Capture is a **second-order operator** — a converter of a
conditional, causally-fillable residual; it cannot manufacture one. Under INFR-022, cost is a
separate, explicitly authorised economic scenario rather than a hidden live discovery gate.

---

## 9. What looked promising overall — the surviving threads

Nothing has graduated to tradable or deployable. The threads that repeatedly *looked* real and
remain live science:

1. **Short-horizon mean reversion / oscillation is a genuine property** (VR<1 on FX and baskets;
   naive-reversion gross +1.958 bps/leg; anchor-reversion availability; the RSI-2 fade relative
   edge) — historical vetoes were vehicle, capture, or cost findings, not a universal proof of
   substrate absence (MR-002..005, VOLHARV, CSRR, MTFCTX).
2. **HTF conditioning and volatility-amplified drift are real but sub-cost at tested granularity**
   (HTFDI ≈1–4 bps; HTFCAP gross +8..+18 bps; SPDR-015 conditioner gates with OOS Brier gains) —
   they amplify a direction term, never substitute for one (VOLDIR).
3. **Exact exchange-native taker volume is validated data** (20/20 raw-trade reconciliation) and
   the first truly non-price input — its first transforms (spine, trap-load, absorption) were null,
   but S14 (CVD–price divergence) and structural/funding-cadence horizons were **never run**.
4. **The unsigned failed-break bounce at PVA/PRIOR** — +5–11% relative MFE availability, reproduced
   on 194 symbols, 2 bands; the strongest single object ever measured above its cost floor. Parked
   as characterisation (P-01-shaped; no realized return ever computed; 81% stop under the only exit
   tested).
5. **C2 shock-MOMO** (Asia shock continuation, +22.6 bps at pct 0.95, n 505) and **P6** (Asia
   magnitude × shock ≈ +10 bps) — the only direction-leads parked as `NOT_RESOLVABLE`, not refuted;
   both need a clean comparator/registration before they can be re-examined.
6. **Cross-sectional × magnitude is the one untested cell** of the availability 2×2; cross-sectional
   reversion reverts but the hedgeable part is ≈0.
7. **The portfolio/diversification result (MR-001)**: 8 low-correlation cells genuinely de-risk
   (mean |corr| 0.10; MaxDD below every constituent; benefit survives realistic fill noise) — a
   structural property worth keeping for any future book, independent of the retracted edge.
8. **Methodology that earned its keep** (reusable on any future family): availability-screen-first,
   matched-random + seed batteries + derangement controls, multiplicity-adjusted admission gates,
   per-stratum adjudication, fail-cheaply screens at 0 reads, report-layer value chains, the
   `(p,W,L)` identity with numeric reconstruction, admission-vs-valuation device classification,
   capital-normalised estimands, gate-implies-label emission contracts.

---

## 10. The bottom line for "tradable / deployable"

- **No candidate strategy family from Chapters 01–05 is tradable or deployable.** Dispositions
  range over CLOSED, RETIRED, REFUTED, CHARACTERISED-NOT-TRADABLE; the single historical
  `DEPLOYABLE_CONFIRMED` (CF-MR-001) was retracted on a look-ahead defect.
- The **historical reasons** are mechanism-specific, not a programme-wide proof of no gross effect:
  (a) on the VOLDIR capture substrate the `(p, W, L)` joint sat at break-even and `W/L` was not an
  independent lever; (b) 91–96% of that measured VOLDIR gap was cost; (c) many unconditioned
  single-instrument entries failed matched-control availability; and (d) the tested signed-volume
  transforms did not separate from matched timing. The VOLDIR cost share must not be reported as a
  count of all programme failures.
- Under **INFR-022**, a successor or evidence-recovery rerun is evaluable on the default
  `NO_COST_CHARGED` gross path. This is a model, not a measured zero-cost claim. A costed result
  requires an operator cost directive and must remain a scenario disclosure, not an arbitrary
  discovery threshold.
- A renewed-engine rerun for the next chapter's technique-impact ledger is **evidence recovery**,
  not an automatic family reopening and not a change to any historical disposition. It must use
  the Nautilus execution path, the live INFR-022 evaluation frame, direct fixed-baseline
  comparisons, complete rows, PSR pairing, and no MDE, power, or machine value labels.
- **Preconditions for a future viable candidate** remain: an explicitly stated information source
  or conditional mechanism; availability-first screening; object-matched causal execution; a
  direct baseline comparator; and no downstream exit/size/trail re-parameterisation presented as
  new entry information. Cost may be added only through the recorded INFR-022 directive.

The provisional candidate extraction for the next INFR chapter is maintained separately in
[`infr-next-chapter-candidate-extraction.md`](infr-next-chapter-candidate-extraction.md). It is a
planning record, not a family registration or disposition change.

---

## 8. Chapter 06 — CF-LIQSWP-001 (closed 2026-09-02)

**Thesis.** Liquidity levels as causal objects; leftover after a raid may differ by level
type, repeat count, TPO tightness, or volatility state. Not a live prediction and not a
costed trade.

**What was tested.** EXP-100 apparatus (264-cell cTrader TRAIN). EXP-101–104 leftover
contrasts on **completed primaries only**. VAL-009–011 selection/anatomy/frequency on the
same emission. AMENDMENT-17 (score every raid eligible at confirmation) specified, not
computed.

**Verdict.** **RETIRED — CHARACTERISED, NOT TRADABLE** (operator-signed, checkpoint-019).
Completed primaries are ~8% of raid rows; ~44% confirm but are not primary. Winner-only
leftover differences are not a live-raid object and are not an edge. 0 TEST reads.

---

## Source map

- **This file consolidates:** `docs/knowledge-base/INDEX.md`,
  `pitfalls-ledger.md`, `lessons-and-amendments.md` (L-01..L-65), `methodology-canon.md`,
  `evaluation-framework.md`, `data-architecture.md`, `memory/`, and the reviews
  (`reviews/capture-geometry-review.md`, `reviews/capture-geometry-recommendations.md`,
  `reviews/unsigned-failed-break-bounce-review.md`).
- **Per-family live cards:** `docs/signal-registry/candidate-families/` (`avwap.md`,
  `harami.md`, `cf-capgeo-001.md`, `cf-mr-001..005.md`, `cf-volharv-001.md`, `cf-csrr-001.md`,
  `cf-htfdi-001.md`, `cf-mtfctx-001.md`, `cf-htfcap-001.md`, `cf-epsosc-001.md`, `cf-sigauc-001.md`,
  `cf-volconv-001.md`, `cf-voldir-001.md`, `family-selection-phase-019.md`).
- **Operational ledgers:** `docs/signal-registry/multiplicity-registry.md`,
  `test-read-ledger.md`, `xena-runs.md`.
- **Chapter archives** (experiment reports, checkpoints, retrospectives, source code):
  `archive/chapter-01-price-geometry-referee/`,
  `archive/chapter-02-mr-volharv-htfdi/`,
  `archive/chapter-03-xena-mtfctx/`,
  `archive/chapter-04-nautilus-bybit-sigauc/`,
  `archive/chapter-05-voldir-capture-geometry/` (incl. `python-src/adaptive_management/` — the
  Nautilus strategy/engine/policy source for SPDR-021..024).
- **Live frame:** `docs/references/neutrality-standard.md`, `docs/references/governance.md`,
  `docs/superpowers/plans/2026-08-08-infr-022-zero-cost-neutrality-psr-pipeline-update.md`.

*This document is a consolidation, not a new claim. It adds no experiments, changes no
dispositions, and does not alter any registry status. Append-merge at future rollovers.*
