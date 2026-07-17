# INFR-014 — Fresh Bybit/Nautilus XENA Calibration + Universe Selection

**Type:** INFR-class infrastructure (not a candidate-family experiment)  
**Status:** DESIGN — 2026-07-16 · runs **∥ SPDR-004/005** (checkpoint-013 D4)  
**Goal:** Produce a **new hash-pinned frozen XENA registry** for the Bybit/Nautilus stack;
chapter-03 pin `db87dc1a…` (`pc_frozen_registry.json` v2) is **VOID on Bybit** (INFR-010 R4).  
**Checkpoint scope:** `docs/experiments-docs/checkpoints/2026-07-16-013-chapter04-open-htfcap-epsosc-cal/` §3.  
**Spec:** `docs/references/xena-lane.md` v2 · prior binder form
`archive/chapter-03-xena-mtfctx/experiments/INFR-009/` (CONFIRM DUAL_CERTIFY / exit (c)).  
**Stop this session:** design + fresh-context QA · **execution is operator-gated**.

---

## 1. One falsifiable question + mechanism

**Question.** Can the INFR-009 **two-stage sample-split CONFIRM DUAL_CERTIFY** binder form be
**re-measured** (not reinvented) on the Bybit/Nautilus substrate — with **net-cost-binding**
selection (L-26), class-shaped nulls for **conditioning/filter** and **episode-harvest**,
and a codified **point-in-time universe selector** — such that a new registry pin certifies
end-to-end α̂ ≤ 5% (point estimate, predeclared n_null) on both class configs, and S1
multi-instrument engine smoke records a pass/fail?

```
MECHANISM: XENA portfolio selection under shared-capital oracle needs a substrate-local false
positive rate under pure-null universes. Chapter-03 pin is VOID on Bybit (different costs,
universe, emission path). Binder *form* is fixed (stage-1 select top-1 → embargo → stage-2
leg-studentized LCB once); α̂ is *measured* by scaling n_null (SE≈0.218/√n). Filter theses
cannot be adjudicated under costless cadence-max (L-26) → net cost binds selection on this
stack. Universe membership is online/causal (≤t−1) — without xen.nautilus.universe_selection,
no reproducible XENA manifest exists.
DERIVED: estimand = e2e α̂ under null battery + no-search coverage (per class config);
         null = synthetic/path nulls + derangement destroys (L-28); optional next-open (L-27);
         horizon = TRAIN fence only; test = design bank → confirm bank (no optional stopping).
```

---

## 2. Object identity

```
OBJECT-IDENTITY:
  measurement object == trading object: N/A (infrastructure) — measured object = binder
    false-positive rate under null universes + registry pin integrity; not a live family P&L.
  measured conditioning event == traded entry event: N/A for CAL synthetic banks; for S1
    smoke and any real-catalog cells: market-on-confirmed / strategy design of the cell.
  effect-splitting windows non-overlapping: design bank and confirm bank use DISJOINT seed
    ranges; no design→confirm leakage; one clean cycle before any binder-form change.
```

---

## 3. VOID prior + what is re-used vs re-measured

| Item | Status |
|---|---|
| Chapter-03 `pc_frozen_registry.json` sha256 `db87dc1a…` | **VOID on Bybit/crypto** — archive-only |
| INFR-006 v3 extensive-F (`537d691a…`) | Still superseded — never re-enable |
| Binder **form** (exit (c) two-stage) | **Re-use form**; re-measure α̂/cov on new substrate |
| Thresholds/scalars from chapter-03 | **Do not copy as binding** — only procedure constants that are form-defining (α target 5%, embargo_frac 0.20, search/ranking fracs, estimator family) |
| New pin | `python/experiments/INFR-014/results/bybit_pc_frozen_registry.json` (+ sha256) |

**No threshold invention:** freezable numbers are those **measured** on the confirm bank under
the predeclared procedure (α̂, cov, selection_inflation, Wilson intervals). Changing form
after design-bank contact = new predeclared CAL (L-23 LOOSER/TIGHTER + new ID).

---

## 4. Class-shaped calibration targets (ckpt-013 §3)

| Config ID | Class | Family prior | CAL shaping |
|---|---|---|---|
| **CLS-FILTER** | Conditioning / filters + hold-scale capture | CF-HTFCAP-001 | Net-cost-binding selection (L-26); pre-search gross-bps floor vs Bybit breakeven (XENA-003 lesson); funding in cost; filter thinning must be able to win under **net** objective |
| **CLS-EPISODE** | Episode-harvest / path structure | CF-EPSOSC-001 | Episode/leg-level streams in null/plant generators; funding × episode length in cost; avoid cadence-only artifacts; L-16 episode object when real candidates exist |

Both configs share the same binder **form** and α gate rule. **Single registry file only**
(§4.2) with `class_configs[]` — no sibling-pin dual option.

### 4.1 Class-shaped null / plant generator contracts (WP1 — binding)

Shared shell: `path_universe`-style shared regime path + LOW/HIGH cadence specs from
`xen.xena.calibration_p3b` (bar density, n_trades class). Differences **must** be code-asserted
(class id on every stream; refuse if CLS-FILTER factory == CLS-EPISODE factory byte-identical).

**CLS-FILTER — `make_filter_null_universe(seed, cadence, n_cand, …)`**

| Field | Spec |
|---|---|
| Candidate roles | Each universe = mix of **BASE** (unfiltered high-cadence random-sign) + **FILT** (same entry times thinned by a synthetic “HTF gate” independent of future PnL under null) |
| Null property | Under pure null, FILT and BASE both have E[g]≈0; FILT has **lower cadence** (thinning rate τ∈{0.3,0.5,0.7} drawn per candidate) so a **costless** objective prefers BASE; a **net-binding** objective can prefer FILT only if plant injects quality |
| Plant (bite / power) | `plant_filter`: stage-1 band only — FILT candidates get +edge_bps on exit (same P-C deplant on stage-2); BASE unplanted. Bite: stage-1 must select a FILT plant with rate ≥0.5; stage-2 survival ≤0.125 after deplant |
| Cost / hold | Every leg carries `hold_hours` from entry→exit bar span; funding via COST-STACK; synthetic default hold = cadence mean hold (LOW 8h, HIGH 2h) if span missing |
| n_cand | 64 (same ScaleSpec); ≥25% FILT, ≥25% BASE; remainder random mix |

**CLS-EPISODE — `make_episode_null_universe(seed, cadence, n_cand, …)`**

| Field | Spec |
|---|---|
| Candidate roles | Streams are **episode objects**: entry → path of marks → clear time (not fixed-H per-bar only). Legs group into episodes with duration D~ truncated lognormal (median 4h LOW / 1h HIGH; cap 48h) |
| Null property | E[g_episode]≈0; random clear; **no** hard inventory cap / banded rebalance structure (P-12 out) |
| Plant | `plant_episode`: stage-1-only positive episode completion bps; deplant stage-2 band exactly as P-C |
| Cost / hold | `hold_hours = episode_duration_hours` per episode (funding scales with D); bps/episode functional for disclosure, binding ratio still g_* on admitted legs |
| n_cand | 64; all episode-shaped (no BASE/FILT split) |

### 4.2 Frozen registry schema (single file — no dual option)

**Path:** `python/experiments/INFR-014/results/bybit_pc_frozen_registry.json`  
**Schema id:** `xena.infr014.bybit_pc_registry.v1`

```json
{
  "registry": {
    "schema": "xena.infr014.bybit_pc_registry.v1",
    "substrate": "bybit_nautilus",
    "void_priors": ["db87dc1a…", "537d691a…"],
    "limit_entry_cells": false,
    "l27_next_open_tool": "xen.xena.fill_basis.next_open_discriminating_control",
    "pin_usage": {
      "forbid_chapter03_on_bybit": true,
      "limit_print_sole_certify_forbidden": true,
      "note_spdr005_2_3b": "CF-EPSOSC must not be certified solely on limit-print passive edge"
    },
    "selection_rule_default_hash": "<sha256 of SelectionRule used for real-membership pilots>",
    "class_configs": [
      {
        "class_id": "CLS-FILTER",
        "family_prior": "CF-HTFCAP-001",
        "procedure": { "...form constants §5.4 + stage1_score..." },
        "design_seeds": {"low": 91000, "high": 92000},
        "confirm_seeds": {"low": 93000, "high": 94000},
        "cost_stack": "bybit_round_trip_cost_bps_v1",
        "stage1_score_kind": "g_net",
        "stage1_charge_costs": true,
        "e2e_pass_event": "stage2_gross_lcb_positive",
        "deployability_binding": "stage2_net_lcb_positive",
        "confirm_summary": { "verdict": "DUAL_CERTIFY|…", "per_cadence": {} },
        "limit_entry_cells": false
      },
      { "class_id": "CLS-EPISODE", "...same keys..." }
    ]
  }
}
```

**Partial-write policy:** write registry only if **≥1** class has `confirm_summary.verdict` in
`{DUAL_CERTIFY, HIGH_ONLY_CERTIFY, LOW_ONLY_CERTIFY}`. Classes that TERMINAL are present with
`certified: false` and **must not** be selected by a live universe. XENA universe manifest field
**`xena_class_id`**: `CLS-FILTER` | `CLS-EPISODE` — gate refuses missing/unknown id or a class
block with `certified: false` on the required cadence set.

**Universe → pin binding:** `verify_frozen_registry(path)` checks schema + re-hash; live
`certify_and_rank` / gate load `class_configs[i]` matching manifest `xena_class_id`.
---

## 5. CAL discipline (binding — item 1)

### 5.1 α resolution and n_null

Binomial SE under α≈0.05: **SE(α̂) ≈ √(p(1−p)/n) ≈ 0.218/√n_null**.

| Bank | n_null (predeclared) | SE(α̂) @ p=0.05 | Role |
|---|---:|---:|---|
| **DESIGN** | **80** | ≈ 0.024 | Bite-check + no-search coverage **disclosure**; freeze procedure constants only if bite OK; **no knob fitting** |
| **CONFIRM** | **200** | ≈ **0.0154** | Binding e2e α̂ + coverage; gate on **point α̂** |
| Optional power disclosure | 40 (non-binding) | — | Planted-edge power curves only |

**e2e pass event (α̂ numerator) — frozen:**

```
A null universe "false-certifies" for α̂ counting IFF
  stage-2 lcb_g_leg_studentized(g_gross) > 0
  on the single top-1 subset selected in stage-1
  (archived P-C / P5 form: n_gross_lcb_positive).

α̂ = (# false-certifies) / n_null

stage-2 net (Bybit RT) is a SEPARATE deployability field:
  deployability_pass ⇔ lcb_g_leg_studentized(g_net) > 0 after bybit_round_trip_cost_bps
  recorded per row; NOT inside α̂.
  Class pin may be written with DUAL_CERTIFY on gross α̂ even if net deployability is weak;
  then deployability_binding status is disclosed and live XENA still charges net (operator
  judges). If operator requires net-binding for pin acceptance, that is a confirm-time
  operator fork — default = gross α̂ for FPR control (comparable to ch03), net disclosed.
```

**Gate rule (point α̂, not UCB):**

```
per cadence / class config:
  alpha_certified ⇔ (point α̂ ≤ 0.05) ∧ (no_search_cov ≤ 0.05)
DUAL_CERTIFY ⇔ both low+high cadences alpha_certified (Fork A form retained)
```

- **Gate on point α̂**, never on Wilson upper bound (UCB) — Wilson disclosed only.
- **No optional stopping:** n_null fixed before first confirm seed runs; no peek-and-extend.
- **No under-n freeze:** if compute fails mid-confirm, bank is incomplete → no pin.
### 5.2 Design / confirm null-bank split

| Bank | Seeds (new Bybit banks — disjoint from all chapter-03) | Cadences |
|---|---|---|
| DESIGN | low **91000**, high **92000** | low + high |
| CONFIRM | low **93000**, high **94000** | low + high |
| BITE (design-only) | low **951000**, high **952000** | stage-1 plant / stage-2 deplant |

Disjoint from INFR-009 banks (71k/72k, 81k/82k, 791k/792k, …). Written into registry.

### 5.3 One clean cycle before binder-form change

```
1. Predeclare procedure (this design) → QA → operator execution approval
2. DESIGN bank: bite → coverage disclosure → design_ok?
3. If design_ok: freeze procedure dict (form constants only) → CONFIRM bank once
4. If confirm DUAL_CERTIFY (or predeclared partial): write registry + hash-pin + verify wrapper
5. If design or confirm FAIL: STOP — binder-form change requires NEW design.md amendment
   (L-23 direction tag) + new seed banks — never silent retune on the same confirm data
```

### 5.4 Procedure constants (form — inherited, not invented)

From INFR-009 P-C / `calibration_pc.py` (re-implemented for Bybit harness, same numbers):

| Constant | Value |
|---|---|
| binder | `two_stage_sample_split` |
| stage1 | search+certify → **exactly one** top-1 subset |
| stage1_score (CLS-FILTER) | **`score_kind="g_net"`**, `OracleConfig.charge_costs=True`, per-leg/stream `cost_bps` from COST-STACK (§6) — **hard refuse** if costless |
| stage1_score (CLS-EPISODE) | same as CLS-FILTER (`g_net` + charge_costs=True) — L-26 funding-sensitive harvest |
| stage1_score_gross_disclosure | companion `g_gross` robust hat logged; never the search objective |
| embargo_frac | **0.20** of span between ranking end and gate start |
| search_frac / ranking_frac | **0.50 / 0.25** of usable post-embargo span |
| stage2 gross (α̂ event) | `lcb_g_leg_studentized(g_gross) > 0` — **defines e2e α̂** (§5.1) |
| stage2 net (deployability field) | `lcb_g_leg_studentized(g_net) > 0` after **Bybit RT** (§6) — **not** inside α̂ |
| estimator | leg_studentized_bootstrap_t |
| n_boot / block_legs / confidence | **200 / 1 / 0.95** |
| α target | **0.05** |
| one_subset / shortlist | true / false |
| held_out_escalation | false (Fork B: bite fail → TERMINAL) |
Cadence specs (low/high trade density) re-use the synthetic generator shapes from
`xen.xena.calibration_p3b` LOW/HIGH, re-homed onto Bybit cost + fence calendar where streams
touch real catalog.

---

## 6. Net-cost-binding selection (L-26 — item 3)

**L-26:** costless cadence-max cannot adjudicate a conditioning/filter thesis.

| Stage | Chapter-03 (VOID) | INFR-014 (Bybit) |
|---|---|---|
| Stage-1 search objective | costless g_gross (A-1) | **Both classes:** `score_kind="g_net"` + `charge_costs=True` (§5.4) |
| Stage-2 gross (α̂) | LCB(g_gross)>0 | **same** — defines α̂ only |
| Stage-2 net deployability | flat **1.0 bps** RT inject | Bybit COST-STACK below — **field**, not α̂ |
| Engine | costless-honest | unchanged — costs **oracle-injected** |

### 6.1 Stage-1 scoring path (single contract — no implementer choice)

```
FOR class in {CLS-FILTER, CLS-EPISODE}:
  OracleConfig.charge_costs = True
  search score_kind = "g_net"          # intensive net turnover-edge on admitted legs
  per CandidateStream / leg:
      cost_bps = bybit_round_trip_cost_bps(
          symbol, entry_price,
          liquidity="taker",
          spread_bps=<pin or GAP default>,
          funding_bps_per_8h=<pin or conservative 1.0>,
          hold_hours=<leg or episode duration hours>,
      ).total_bps
  ASSERT at harness entry:
      if charge_costs is False OR score_kind != "g_net":
          raise IntegrityError("CLS-* forbids costless stage-1 — L-26")
  g_gross companion: compute robust_g_hat gross for disclosure only; never rank/search key
```

**Synthetic hold/funding defaults (null banks):**  
- CLS-FILTER: `hold_hours = max(1/60, (exit_ts−entry_ts) in hours)`; if missing → cadence default
  LOW **8.0 h**, HIGH **2.0 h**.  
- CLS-EPISODE: `hold_hours = episode_duration_hours` (generator §4.1).  
- GAP spread: use `spread_bps=5.0` labeled GAP in `cost_pins.json` (disclosed; not silent zero).

**Hard refuse:** CLS-FILTER (and CLS-EPISODE) design/confirm runners **abort** if stage-1 is
costless — porting P-C with only stage-2 inject is a process FAIL, not a variant.

```
COST-STACK (binding):
  fee_rt_bps     = 2 × bybit_fee_bps_per_side(liquidity="taker")   # 11.0 default
  spread_rt_bps  = t1_round_trip_spread_bps(symbol, spread_bps=TRAIN_median_or_GAP)
  funding_rt_bps = funding_bps_per_8h × (hold_hours / 8)
  total          = bybit_round_trip_cost_bps(...).total_bps
  pin status: per-symbol spread coverage OK|GAP disclosed in results/cost_pins.json
```

Amendment tag vs archived P5 pin: **TIGHTER** on deployability realism (Bybit not flat 1.0);
**TIGHTER** on stage-1 selection (net binds). L-23 ledger in report if any post-design procedure edit.

**Pre-search economics (both classes):** Q1-style disclosure of median gross bps vs Bybit
breakeven **before** search on any real-catalog pilot cells; incomplete cost map → refuse
search (E3 / `economics` integrity).
---

## 7. L-27 / L-28 battery guards (item 4)

### 7.1 Entry-mode declaration (CAL + downstream universes)

| Universe / config | SPDR default | CAL null streams | L-27 action |
|---|---|---|---|
| CLS-FILTER (→ XENA-HTFCAP) | market / open-to-open | market-priced synthetic | permutation/derangement battery **admissible** |
| CLS-EPISODE (→ XENA-EPSOSC) | **market-on-confirmed-event** (SPDR-005 §2.2: 0 limit cells) | market-priced synthetic | battery **admissible** under market fill basis |
| Any future limit-entry cell | — | — | **must** add **next-open discriminating control** (re-price entries to adjacent bar open; hold times/exits/sizing fixed) **or** declare permutation battery **inadmissible** for that universe |

**Hard predeclaration:** INFR-014 CAL **does not** include limit-entry candidate cells. Registry
`limit_entry_cells: false`. If a later XENA design adds limits, it must amend the pin usage
rules (new CAL or explicit L-27 control artifact) — cannot silently reuse this pin on
limit-print universes.

**SPDR-005 §2.3(b) pin-usage (explicit):** a live CF-EPSOSC / CLS-EPISODE universe **must not**
be certified or route-restored **solely** on a limit-print passive edge (P-10 + L-27). Registry
`pin_usage.limit_print_sole_certify_forbidden: true` (§4.2).

### 7.2 Destroy form (L-28)

Any index/label permutation used as a null or destroy is a **derangement** (0 fixed points);
regenerate draws with fixed points. Alignment-break, not P&L multiset shuffle (L-14).

### 7.3 Next-open control (shipped even if unused by CAL)

Implement `xen.xena.fill_basis.next_open_discriminating_control` on the **existing**
`fill_basis` module only (never a parallel `fills_basis` package): re-price entry fills to
next open; compare live vs next-open edge. **Required artifact** in results even when all
cells are market — proves tooling for XENA-EPSOSC if limits appear later (SPDR-005 §2.3
forward note absorbed).

---

## 8. S1 multi-instrument single-engine smoke (item 5)

**Goal.** Close VAL-008 §5.5 open item.

| Field | Spec |
|---|---|
| Instruments | N≥3 ADMITTED Bybit perps (e.g. BTC/ETH/SOL USDT linear) |
| Path A | **One** `BacktestNode` process, multi-instrument engine, single run |
| Path B | Subprocess-per-instrument (L-31 baseline), N separate nodes |
| Config | `BacktestRunConfig(dispose_on_completion=False)` (L-30); capture reports then `dispose()` |
| Criterion | **Bitwise / byte-identical** emission artifacts for the overlapping columns after
 canonicalisation (strip process UUIDs per emission contract v1) **or** documented
 non-identity with root cause (then S1 FAIL → XENA batch = subprocess-per-cell) |
| Fence | TRAIN-only, PINNED attestation |
| Estimand gate | v2 `blocking_pass` on each cell emission |
| Outcome | `results/s1_smoke.json` PASS|FAIL; decides XENA batch topology |

L-29 fill-ts anchor: `EntryFillPrice == next-bar RealOpen ± 1 tick` sample check on S1 legs.

---

## 9. NEW DELIVERABLE — `xen.nautilus.universe_selection` (item 6)

**Currently uncodified** (`universe_selection.py` missing). XENA universes cannot be built
without it. **Ship + test as part of INFR-014** (blocking for pin usage on real membership).

### 9.1 API (minimum)

```python
# python/src/xen/nautilus/universe_selection.py

@dataclass(frozen=True)
class SelectionRule:
    n: int = 10
    metric: str = "trailing_volume"      # trailing 24h sum of 1m volume
    window_bars: int = 1440              # 24h at 1m
    rebalance: str = "1d"                # daily
    rebalance_tz: str = "UTC"
    rebalance_time: str = "00:00"
    hysteresis_rank: int = 0             # 0 = pure top-n; optional keep-if-rank≤n+h
    pool: str = "admitted_listed"        # SPDR/default; "admitted_pit_incl_delisted" for XENA
    causal: bool = True                  # data ≤ t−1 only
    tie_break: str = "lexicographic_id"

def select_membership(
    catalog, rule: SelectionRule, *, asof_ts, fence, band="TRAIN"
) -> pl.DataFrame:
    """Return n rows: rank, instrument_id, metric_value.

    Causality: only bars with ts_event ≤ asof_ts − 1ns (ε = 1 nanosecond strictly before
    asof; equivalently last closed 1m bar before asof). Future volume must not enter rank.
    """
def rebalance_schedule(start, end, rule: SelectionRule) -> list[datetime]: ...

def build_membership_series(catalog, rule, *, start, end, fence) -> pl.DataFrame:
    """Long membership.parquet: rebalance_ts, instrument_id, rank, metric_value, rule_hash."""

def rule_hash(rule: SelectionRule) -> str:
    """Canonical JSON sha256 of rule fields — pin into universe manifests."""
```

### 9.2 Integrity

- All catalog reads through `xen.nautilus.catalog_fence` (`band="TRAIN"` for CAL).
- Selection at t uses metric window ending **≤ t−1** (code assert).
- **Hysteresis:** default 0 for SPDR parity; XENA may set `hysteresis_rank≥1` to reduce churn
  (declare in universe manifest).
- **Anti-survivorship:** `pool=admitted_pit_incl_delisted` for XENA characterisation;
  `admitted_listed` acceptable for SPDR justification (D3) — rule field records which.
- Artifacts: `results/membership_<rule_hash>.parquet` + `rule.json`.
- Universe manifests **must** embed `selection_rule_hash` + path to membership parquet;
  `verify_frozen_registry` / gate refuses manifests without pin when live XENA runs.

### 9.3 Tests

Unit tests: causality (future volume cannot enter rank), determinism (same catalog+rule →
byte-identical membership), tie-break stability, fence refusal on HOLDOUT.

---

## 10. Implementation map + work packages

| WP | Deliverable | Notes |
|---|---|---|
| **WP0** | `xen.nautilus.universe_selection` + tests | Blocking apparatus |
| **WP1** | Bybit CAL harness (port `calibration_pc` form) | New seeds; Bybit cost injection; CLS-FILTER/EPISODE stream factories |
| **WP2** | DESIGN bank both classes | Bite + coverage; stop if bite fail |
| **WP3** | CONFIRM bank both classes | n_null=200; point α̂ gate; no optional stopping |
| **WP4** | Registry write + `verify_frozen_registry` path | `results/bybit_pc_frozen_registry.json` |
| **WP5** | S1 multi-instrument smoke | PASS/FAIL topology decision |
| **WP6** | L-27 next-open control apparatus | Even if unused by market-only CAL |
| **WP7** | Report + INDEX | Operator pin sign-off |

Code homes: `python/src/xen/nautilus/universe_selection.py`,
`python/src/xen/xena/calibration_bybit.py` (or `calibration_pc_bybit.py`),
`python/experiments/INFR-014/code/`, tests under `python/tests/`.

**No** `run_final_gate` on live family universes. **No** TEST/holdout. TRAIN fence only.

---

## 11. Estimand / integrity split

```
HARD (block):
  TRAIN-only fence; design/confirm seed disjointness; predeclared n_null; no optional stopping;
  bite fail → TERMINAL (no confirm); gate on point α̂ not UCB; L-28 derangements;
  L-27 if any limit cell; L-30 dispose_on_completion=False on node runners; L-31 one node/process
  unless S1 PASS multi-instrument; no local accounting for verdicts; chapter-03 pin not used on Bybit;
  universe manifests carry selection_rule_hash.

INFORMATIVE (operator judges):
  power curves; Wilson intervals; class-wise α̂ differences; S1 FAIL→subprocess topology;
  cost pin GAP rates; any HIGH_ONLY / LOW_ONLY partial certify recommendation.
```

```
BANDS (confirm, per class × cadence):
  CERTIFIED:     point α̂ ≤ 0.05 ∧ no_search_cov ≤ 0.05
                 (α̂ event = stage2 gross LCB>0 only — §5.1; net is deployability field)
  FAIL_ALPHA:    α̂ > 0.05
  FAIL_COV:      no_search_cov > 0.05
  DEPLOY_WEAK:   alpha CERTIFIED but stage2 net LCB≤0 often (disclosure; not α fail)
DUAL_CERTIFY: both cadences alpha-CERTIFIED for a class.
```

---

## 12. Exit criteria (checkpoint-013 §3)

1. `xen.nautilus.universe_selection` imported, tested, rule_hash documented.  
2. DESIGN ok both classes (bite PASS).  
3. CONFIRM: DUAL_CERTIFY **or** operator-accepted partial with terminal note on failed cadence.  
4. `bybit_pc_frozen_registry.json` written; sha256 recorded; `verify_frozen_registry` green.  
5. `s1_smoke.json` PASS or FAIL with topology decision.  
6. L-27 tooling present; registry declares `limit_entry_cells: false`.  
7. Report.md + INDEX update.  

Until (3)+(4): **XENA counted path blocked** on Bybit. SPDR-004/005 may continue (Q4).

---

## 13. Golden trace / acceptance checks (QA-facing)

```
GOLDEN-TRACE (infra):
  G1: rule_hash stable under key reorder; membership at fixed asof matches hand rank of
      top-10 volume ≤ t−1 on a fixture day.
  G2: design bank refuses if confirm seeds accidentally reused (assert disjoint).
  G3: S1 — three instruments; dispose_on_completion=False; reports non-empty; fill-ts anchor
      sample; second BacktestNode in same process must not be used (L-31).
  G4: confirm gate function signature takes frozen procedure dict only — no free thresholds.
```

---

## 14. Complexity budget

| Item | Budget |
|---|---|
| New modules | universe_selection; calibration_bybit harness; next_open control helper |
| Modified | verify_frozen_registry accept v3 Bybit schema; xena-lane doc pin pointer post-report |
| Frozen invented thresholds | **0** — only measured α̂/cov and form constants above |
| Holdout / TEST contact | **0** |
| Live family XENA runs | **0** in this INFR |

---

## 15. Controls validity (CAL nulls)

```
CONTROL NULL-BATTERY:
  question: e2e false certify rate under pure null
  population: n_null predeclared synthetic/path universes per cadence×class
  bite: stage-1-only plant must not survive stage-2 (embargo independence)
  non-vacuity: plant collapses; null mean≈0 on g
  destroy form: DERANGEMENT for permutations (L-28)
  disclosure: α̂, SE, Wilson, selection_inflation, collapse fractions

CONTROL NEXT-OPEN (L-27 apparatus):
  question: is edge passive-print vs predictive timing?
  population: re-priced entries; required if limit cells ever appear
  expected: market-only CAL → near-zero discrimination gap (sanity)
```

---

## 16. Power statement

```
POWER:
  confirm n_null=200 → SE(α̂)≈0.0154 at p=0.05; resolves α̂ to ~1.5pp.
  design n_null=80 → SE≈0.024 — validation only.
  UNPOWERED: not applicable (fixed n); incomplete bank = FAIL not underpowered pass.
```

---

## 17. Integrity checklist (pre-exec + code-asserted)

1. Chapter-03 pin never loaded as binding on Bybit.  
2. Seeds disjoint from archive banks.  
3. n_null fixed; no optional stopping in code.  
4. Gate compares point α̂ to 0.05, not UCB.  
5. Bybit costs via `bybit_round_trip_cost_bps` only (no silent flat 1.0 without disclosure).  
6. CLS-FILTER stage-1 uses net-binding objective (L-26).  
7. limit_entry_cells false; L-27 tool present.  
8. L-28 derangements.  
9. universe_selection causal + fence.  
10. L-30/L-31 on all BacktestNode runners.  
11. TRAIN fence only.  
12. One clean cycle rule enforced in runner CLI (confirm blocked unless design_ok artifact exists).

---

## 18. Artifacts

```
python/experiments/INFR-014/
  design.md          # this file
  qa-review.md       # fresh-context QA (append-only)
  code/              # runners, S1 smoke, harness entrypoints
  results/
    design_<cls>.json
    confirm_<cls>.json
    bybit_pc_frozen_registry.json
    s1_smoke.json
    membership_*.parquet
    cost_pins.json
    unit / rule hashes
  report.md          # after execution
python/src/xen/nautilus/universe_selection.py
python/src/xen/xena/calibration_bybit.py   # or equivalent
```

---

## 19. Operator gates

1. **QA APPROVE** (this stage).  
2. **Execution approval** — WP0–WP7 may be long-running; operator may stage WP0+S1 first.  
3. **Registry pin sign-off** — after confirm; operator accepts DUAL_CERTIFY / partial / TERMINAL.  

**Stop now:** design complete → QA subagent → present QA verdict. No execution without operator go.
