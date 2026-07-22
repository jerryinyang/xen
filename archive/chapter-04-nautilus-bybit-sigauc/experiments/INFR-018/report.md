# INFR-018 — Report: Instrument Build & Freeze (CF-SIGAUC-001, Stage I)

**Item:** INFR-018 · **Executed:** 2026-07-20 → 2026-07-21 · **Family:** CF-SIGAUC-001 · **Checkpoint:** 014 §4  
**Stage:** I (instrument building) — outputs are **parameters and validated instruments**, never evidence that anything works.  
**Band:** DESIGN (selection) + CONFIRM (train-internal once). **TEST never read. Holdout SEALED. 0 counted reads.**

---

## 1. One-line outcome

**The measuring instruments are frozen and integrity-clean** — session anchor, acceptance rule, profile kernel, and class thresholds are hash-pinned for Stage II. **Nothing here says a signal pays.**

## 2. Operator verdict

**COMPLETE — instrument registry accepted (operator, 2026-07-21).**  
Substance: Stage I deliverable on disk; close-out authorised after integrity gates passed and freezes wrote cleanly.  
Analyst recommendation: N/A (no expectancy analysis; parameter freeze only).

## 3. Deliverable

| Artifact | Path | Pin / note |
|---|---|---|
| **Instrument registry** | `results/instrument_registry.json` | `pin_sha256` **`5c3869845bd514bf…`** |
| Anchor freeze | `results/anchor_freeze.json` | `60ae790a1a839ef4…` |
| A6 freeze | `results/a6_freeze.json` | `3bdd89ba2afb66a6…` |
| Frozen inputs (from INFR-017) | baselines / column pins | `1b7244c8…` / `e3b9fd9b…` (re-hashed at every entry) |

### Frozen parameters

| Piece | Value |
|---|---|
| Session anchor | **A-USOPEN · IB L = 15 min** |
| Acceptance rule (A6) | **D4-t50-w30 · poke δ = 0.0** (price-only) |
| Profile kernel | **K-UNIFORM** · `calibration: PERFORMED` · selected on DESIGN days only |
| Class residual thresholds | Per-symbol p90/p10 values under `class_thresholds` in the registry |
| Spread regime bands (§2.5) | **UNAVAILABLE — NO USABLE INPUT** (INFR-017 W2; binding on Stage II) |

Universe realised for races: **140 symbols · 609 DESIGN days** (online top-20 panel; not smoke).

## 4. What was raced (method)

| Gate | Question | Bank | Control / tripwire |
|---|---|---|---|
| **HYP-I2** | Which clock + IB length yields the most post-break excursion asymmetry vs matched pseudo-anchors? | DESIGN select → CONFIRM once | Soft: pseudo-anchor derangement/exclusion; **HARD:** future IB levels (`ib_shift`) + leak plant |
| **HYP-I3** | Which A6 discriminator best separates ACCEPTANCE vs TRAP after a boundary poke? | DESIGN select → CONFIRM once | Soft: label derangement within days; **HARD:** outcome **path swap** + leak plant |
| **HYP-I4** | Kernel calibration + class clustering + band finalisation | DESIGN | Kernel vs trade-truth sample; residual-matched non-event control |

Scope fence (§0): no P&L, no expectancy headline, no TEST, no holdout. Absolute rates quarantined under `CALIBRATION_ONLY`.

## 5. Integrity gates (HARD) — all clean on DESIGN freezes

| Gate | Result | Meaning |
|---|---|---|
| I2 future-shift | `survives: false` · cf ≈ **−41.7** · day_corr ≈ **0.060** | Destroyed arm not same-sign material; construction not leaking |
| I2 leak plant | `survives: true` · cf ≈ **0.70** | Gate has bite |
| I3 path-swap | `survives: false` · cf ≈ **0.037** · S_raw ≈ 0.754 → S_swapped ≈ 0.028 | Honest rule collapses under path destroy |
| I3 leak plant | `survives: true` · cf ≈ **1.32** | Destroy reaches bars the rule reads (AMENDMENT-6) |
| Path-swap coverage | 7911/8076 spliced · 165 singletons skipped · 0 missing donors · fraction **1.0** of eligible | I-56/I-57/I-61 fixes held at full scale |

Spot-check (I2 pooled vs BTC/ETH/SOL): **COSMETIC** — freeze allowed under design §3.7.

## 6. Value-layer reads (labels only — L-32 / INFR-016)

These **do not gate** the freeze. Recorded for SPDR-007 context.

| Read | DESIGN | Note |
|---|---|---|
| I2 winner contrast E | **+0.100** (A-USOPEN×15) | Report layer; several cells sit near/below own MDE — pin carries full table |
| I3 winner S | **+0.753** · band **SUGGESTIVE** | Soft-control collapse ≈ 0.39 (above SEPARATES collapse label); 1 cell SEPARATES, 55 SUGGESTIVE |
| I3 CONFIRM top (full grid re-rank) | D3-w30 S≈0.753 SUGGESTIVE | Implementation races full grid on CONFIRM; **pin uses DESIGN freeze (D4)**, not CONFIRM re-selection |
| I2 CONFIRM top (full grid re-rank) | A-EUOPEN×15 E≈+0.231 | Same: freeze stays A-USOPEN×15 from DESIGN |

CONFIRM = **TRAIN_INTERNAL_CONFIRMATION** — not programme out-of-sample.

## 7. HYP-I4 exits

| Exit | Outcome |
|---|---|
| 1 Kernel vs trade-truth | **K-UNIFORM** wins on DESIGN calibration days; `PERFORMED` |
| 2 Class clustering | Per-class contrasts + MDEs published; sparse tails as designed |
| 3 Bands | A5 baselines **consumed not refitted**; spread regime **UNAVAILABLE** with binding Stage II consequence |

## 8. QA history

Eight pre-exec QA runs (append-only `qa-review.md`). Runs 1–7 **REVISE**; run 8 **APPROVE**. Material late fixes: AMENDMENT-6 path-swap must move bars (I-45); I-56 session_end shadow; I-57 singleton self-donors; I-59 sign clause; I-60 matched S_raw population; I-61 truncated splice + uniqueness. 39 unit tests green at freeze.

## 9. Scope limits (carry into Stage II)

1. **Survivorship-shaped panel** — top-20 online membership from DESIGN-bank-covered instruments (~197), not full 894 ADMITTED.  
2. **No spread regime layer** — Stage II cannot use §2.5 stress/precision demotion until a usable spread input exists.  
3. **Stage I parameters only** — cite the pin identity, never E or S as “edge.”  
4. **CONFIRM tops ≠ freezes** — full-grid CONFIRM re-ranks; freezes are DESIGN-only.  
5. Path-swap destroy partly randomises price level (median donor offset ~23 IB widths disclosed); labels still non-degenerate.

## 10. Registry disposition

- **Family status:** unchanged (**REGISTERED**). No open/retire/promote from this item.  
- **Evidence row:** append to `docs/signal-registry/candidate-families/cf-sigauc-001.md` (instrument freeze complete).  
- **TEST ledger:** no contact · 0 counted reads.  
- **multiplicity-registry:** apparatus / instrument pin only — no strategy screen.

## 11. Next (not this item)

| Next | Role |
|---|---|
| **SPDR-007** | Statistical spine — master go/no-go (uses this pin) |
| **SPDR-008** | Breadth (296 TRAIN-readable per post-INFR-017 ruling) |
| Checkpoint-015 | Signal tests / model assembly (deferred) |

## 12. Artifacts

| Kind | Path |
|---|---|
| Design | `design.md` |
| QA | `qa-review.md` (runs 1–8) |
| Code | `code/` · shared `python/src/xen/sigbar/` |
| Tests | `python/tests/test_sigbar_infr018.py` |
| Results | `results/*` (races, freezes, registry) |
| Perf note | `code/PERF-NOTE.md` (I2/I3 runner optimisations; methodology-neutral) |
