# SPDR-006 — Design (CF-HTFCAP-001 vol-regime facet — TRAIN-only availability screen)

**Lane:** SPDR — `docs/references/spdr-lane.md` · pack `docs/references/spdr-pack-htfcap-001.md`
(HTF-state axis "simple vol regime (optional)" — cut from SPDR-004 for budget, screened here).
**Family:** CF-HTFCAP-001 (REGISTERED; same D0 — this is a facet screen, not a new family).
**Relation to SPDR-004:** slimmer sibling. SPDR-004 results are **FROZEN** — DI-only and
DI_ADX-only variants are NOT re-run here; their frozen cells serve as reference disclosure.
SPDR-006 answers: does HTF **volatility regime** (standalone, and as an amplifier on
DI / DI+ADX) condition LTF entry quality × capture scale?
**Designed:** 2026-07-17 · **Status:** DESIGN COMPLETE — screen execution separate go.
**No** QA subagent (code-asserted checklist §9); **no** estimand gate; **no** counted reads;
**no** tradability claim. Multiplicity: own grid, own K — separate screen precisely to avoid
post-results expansion of SPDR-004 (L-23).

---

## 0. Registration precondition (HARD)

Family CF-HTFCAP-001 REGISTERED (checkpoint-013 D2); SPDR-006 row appended to
`multiplicity-registry.md` Chapter 04 (0 slots, screen uncounted). Screen code refuses to run
if card status ≠ REGISTERED or row missing.

---

## 1. Question + mechanism

On TRAIN Bybit (same rule-selected 10), do coherent clusters of (HTF **vol regime** [×
direction/strength] × LTF base × hold × domain) show signal-conditional lift in gross
open-to-open bps/trade under causal t−1 rules?

```
MECHANISM: HTF volatility regime (ATR expansion/compression on the higher TF) conditions the
economic scale of LTF entries — directly (vol alone selects harvestable bars) or as an
AMPLIFIER on directional HTF state (high-vol amplifies a DI/DI_ADX edge; vol never sets the
sign — CF-HTFDI lesson, `quantify_not_qualify_base_conditional`). Capture scale (hold ×
HTF span) remains the first-class axis (P-14 escape).
DERIVED: estimand/null/horizon/test identical in FORM to SPDR-004 §4/§7 (same family, same
object: single-leg open-to-open over H); filter axis replaced by vol-regime levels.
```

## 2. Inheritance from SPDR-004 (verbatim unless stated)

| Block | Status |
|---|---|
| §2 P-14 distinctness, §3 object identity, §4 estimand + formula, §5 unit pin form, §6.1 selection rule, §6.2 data/fence, §9 power discipline, §10 checklist form, L-28..L-31 cites | **Inherited verbatim** (SPDR-004 design.md AMENDMENTS 1–5 included: notional-volume selection, fixed top-10 strata declaration, two-sample lift CIs incl. `two_sample_block_vs_battery` for UNF, L-20 emissions) |
| Money floor | **Improved:** per-symbol TRAIN-measured pseudo-quote RT spread from INFR-011 staging `SpreadBps` (median over TRAIN) replaces GAP=2 (measured 2026-07-17: BTC 0.15, SOL 0.91, OP 1.15, PEPE 1.22, DOGE 1.51 bps class); fees stay pinned `BYBIT_USDT_PERP_FEES` taker 5.5 bps/side (operator challenge 2026-07-17 resolved: linear-perp fees charge on notional → hit o2o returns 1:1; taker-both-sides faithful to market-entry design) |
| DI / DI_ADX pure-direction variants | **NOT re-run** — frozen SPDR-004 cells are the reference; joint reads are disclosure |

## 3. Grid (frozen)

HTF vol state: `vol_ratio[t] = ATR(14)[t−1] / median(ATR(14))[t−1, W=100 HTF bars]`
(all inputs last-closed HTF bar, CloseTime < Open(t) — same MTF boundary hazard rule).

| Axis | Levels | n |
|---|---|---|
| Symbols | online top-10 (§6.1 inherited; same membership rule) | 10 |
| Domain | 1h/5m, 4h/15m, 1d/1h | 3 |
| Hold | 0.5×, 1×, 2×, 4× HTF span | 4 |
| LTF base | UNF, MOM, RAND (params inherited; RAND seeds 1000–1024) | 3 |
| **HTF filter (new axis)** | **VOL_HI** (ratio ≥ 1.25); **VOL_LO** (ratio ≤ 0.8); **DI×VOL_HI**; **DI_ADX×VOL_HI** | 4 |

Interactions: `DI×VOL_HI` = +DI>−DI direction AND VOL_HI (sign from DI; vol gates only).
`DI_ADX×VOL_HI` adds ADX≥25. **No DI-only / DI_ADX-only cells** (frozen in SPDR-004).
VOL_HI/VOL_LO standalone cells are direction-less gates: MOM/RAND keep base sign; UNF
standalone-vol cells have no sign → baseline = RAND battery at that cadence and **UNF ×
{VOL_HI, VOL_LO} treatment sign = long-only, disclosed as drift-exposed** (declared here,
pre-run; the against-drift read is the RAND interaction cell).

**Cells:** 10 × 3 × 4 × 3 × 4 = **1440** treatment + matched baselines (NONE twin for
MOM/RAND; RAND battery for UNF per SPDR-004 AMENDMENT-1). Multiplicity disclosed; promote =
cluster K≥3 on THIS grid only (no pooling with SPDR-004 cells for K).

**Amplifier read (binding disclosure, per family card design constraint):** for each
DI×VOL_HI / DI_ADX×VOL_HI cluster candidate, report lift vs the FROZEN SPDR-004 DI / DI_ADX
cell at the same (symbol × domain × hold × base) — the amplifier claim requires interaction >
direction-only, not just interaction > baseline.

## 4. Controls (forms inherited from SPDR-004 §7)

- **Control A:** matched baselines as above (paired two-sample block CIs; AMENDMENT-4/5 methods).
- **Control B:** RAND ≥25-seed battery (rank + battery-aggregated lift).
- **Control C:** HTF phase-shift destroy K=50 HTF bars on the **vol stream and DI stream
  jointly** (both features shifted together — destroying only one would leave a live gate);
  derangement if permutation-based (L-28); must collapse any promote-candidate cell.

## 5. Promote rule + bands

SPDR-004 §8 verbatim with: cluster K=3 within THIS grid; neighbourhood on hold axis and/or
symbol; money floor per §2 improved spreads; VOL_LO clusters interpreted as compression-regime
finding (no sign flip storytelling). Bands (SUPPORTED_LIFT / WASH / CONTRADICTED / UNPOWERED)
inherited. Predeclared UNPOWERED: 1d/1h × 4× tails; any cell n < max(30, 2·block);
DI_ADX×VOL_HI thin tails.

## 6. Integrity checklist (code-asserted, §10 form inherited)

SPDR-004 items 1–11 verbatim (registration row = SPDR-006; unit_pin.json fresh; membership
re-derived or reused byte-identical from SPDR-004 with sha recorded) PLUS:
12. Joint phase-shift covers every HTF input feeding the cell's gate (vol + DI + ADX).
13. No DI-only/DI_ADX-only treatment cell present (frozen-facet guard).
14. Amplifier disclosure table emitted for every interaction cluster candidate.

## 7. Golden trace

G1 (4h/15m, DI×VOL_HI): confirmed entry — verify ATR ratio, DI sign, ADX (if gated) all from
last closed 4h bar; hand r_bps H=16. G2 (1h/5m, VOL_LO standalone, UNF long-only): verify
ratio ≤ 0.8 and long sign convention. G3 membership rebalance re-check (or byte-identity vs
SPDR-004 membership.parquet).

## 8. Artifacts + stop

```
python/experiments/SPDR-006/
  design.md  screen_code/  results/  plots/  screen.md  analysis.md (fresh-context analyst)
```
Stop: design complete. Screen execution = separate operator go. Disposition = operator, on
analysis.md. Joint SPDR-004+006 family read happens at disposition/checkpoint, never inside
either screen.
