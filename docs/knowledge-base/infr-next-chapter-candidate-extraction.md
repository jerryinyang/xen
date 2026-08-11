# INFR Next Chapter - Candidate Extraction

**Status:** planning extraction only. This document does not register a family, authorise an
implementation, open a read, or change a historical disposition.

## Purpose

The next INFR chapter will rerun a small representative set of strategies from the previous
catalogues in order to build a technique-impact matrix. The reruns will not treat old emissions or
old results as current evidence. Historical records below are selection rationale only.

Each candidate will be re-emitted through the renewed Nautilus execution path and evaluated under
the live INFR-022 frame:

- `NO_COST_CHARGED` by default, with the required zero-cost caveat.
- No MDE, detection floor, power gate, arbitrary threshold, or machine value label.
- Direct comparison against a fixed, pre-specified baseline.
- Complete per-stratum rows with counts and matching populations.
- PSR beside every mean-trade or mean-leg bps read.
- Causal decision-time features, native fills, and open-to-open outcomes.
- No TEST or holdout contact during the technique-impact chapter.

The renewed reruns are evidence recovery. They do not by themselves reopen the registered family,
promote a candidate, or overturn a prior verdict.

## Candidate Set

| Category | Candidate anchor | Prior lineage | Selection rationale | Rerun boundary |
|---|---|---|---|---|
| Momentum | **C2 shock-conditioned MOMO** | `CF-VOLDIR-001`, SPDR-014 -> SPDR-018/018B | The crypto run recorded a +22.6 bps shock-conditioned momentum observation at percentile 0.95 with n=505. SPDR-018B did not replicate or refute it because its comparator was non-neutral and the session composition changed. It is the strongest unresolved momentum lead, not an established edge. | Reconstruct the original `P-MOMO` object, shock definition, session strata, and magnitude-matched comparator before implementation. Report the comparator's own mean and null distribution. |
| Breakout | **SPDR-024 fixed candlestick-breakout baseline** | `CF-VOLDIR-001`, SPDR-021/024 | The fixed baseline was positive on H1 in the retained analysis (`+5.21 bps` crypto and `+1.10 bps` cTrader), while H4 differed in sign. This is the clearest recent baseline for separating entry quality from downstream management effects. | Rerun the fixed breakout baseline first. Do not carry forward the old SIZE lattice, MDE apparatus, or volatility-adaptive conclusion as evidence. |
| Mean-reversion | **CF-MR-002 causal RSI-2 fade** | Successor to the retracted CF-MR-001 result | The causal `rct[di-1]` construction was leak-clean and retained a relative fade-versus-momentum effect. It is the correct RSI-2 lineage; the contaminated CF-MR-001 `rct[di]` result is excluded. | Reimplement the causal entry and exit in Nautilus. Never rerun or cite the same-bar `rct[di]` favourable-limit result. |
| Multi-timeframe | **CF-HTFCAP-001** HTF direction and volatility context with LTF hold scale | Chapter 04 HTFCAP / HTFDI lineage | The prior run found a real gross BTC `DI_ADX x VOL_HI` effect of approximately `+8` to `+18 bps` at longer holds, while its closure was dominated by the historical cost treatment. It is the strongest explicit HTF/LTF candidate and supplies a distinct multi-timeframe mechanism. | Rebuild the confirmed-HTF / LTF relationship in the renewed Nautilus path. Treat hold scale as a predeclared technique axis, not as an assumed rescue. |

These categories are organisational, not mutually exclusive market mechanisms. The C2 candidate
contains a momentum and volatility interaction; it occupies the momentum slot because it is the
unresolved directional lead. HTFCAP occupies the multi-timeframe slot so the chapter does not
duplicate a second HTF continuation candidate.

### C2 Source Trace And Minimal Rule

C2 originated as **C2 shock-conditioned MOMO** in the Arm-C residue of `SPDR-014`, the
zone-to-event-to-post-event MOMO/MR characterisation. `SPDR-018` carried that residue forward as
Arm C; `SPDR-018B` was the attempted independent cTrader replication. It was never a complete
standalone strategy family.

The minimal registered rule was:

1. At a causal decision bar, build the parent absolute-move likelihood zone from the registered
   volatility or magnitude forecast.
2. Wait up to the registered event horizon for the first band breach. For `E-TOUCH`, an upper
   high breach is `side=+1` and a lower low breach is `side=-1`; a simultaneous touch is resolved
   by the larger excursion.
3. Keep only the parent event-grammar row where the decision-bar `shock_flag` is true. Historically
   this flag meant the expanding top decile of absolute decision-bar return after at least 20
   observations; it was named `shock`, not a volatility regime.
4. For `P-MOMO`, enter at the open after the breach and trade with the breach side. The historical
   optional policy exited at the declared post-event horizon or at the first adverse `1.5 x ATR`
   stop.
5. Measure side-signed open-to-open post-event return. The C2 attribution read additionally
   compared shock `P-MOMO` rows with non-shock `P-MOMO` rows matched on the decision-bar magnitude
   distribution, not with an unconditioned pool.

The renewed design must pin the return basis explicitly. The archived `SPDR-014` preparation code
constructs `shock_flag` from an expanding top decile of close-to-close log return, while the
M-3 documentation describes matching on decision-bar magnitude. The new Nautilus implementation
must resolve and test that object identity before any C2 result is interpreted.

## Historical Evidence Rules

The following records may justify candidate selection, but their estimates are not pooled with the
new emissions:

- `docs/knowledge-base/families-explored.md`
- `docs/signal-registry/candidate-families/cf-mr-002.md`
- `docs/signal-registry/candidate-families/cf-htfcap-001.md`
- `archive/chapter-05-voldir-capture-geometry/experiments/SPDR-014/`
- `archive/chapter-05-voldir-capture-geometry/experiments/SPDR-018/`
- `archive/chapter-05-voldir-capture-geometry/experiments/SPDR-021/`
- `archive/chapter-05-voldir-capture-geometry/experiments/SPDR-024/`

The following are not eligible as positive evidence for the rerun set:

- The retracted CF-MR-001 `EXIT-RCT` result.
- Any result whose entry seam was a passive-limit print unless the new design explicitly tests a
  different, causal fill object.
- Historical MDE, power, detection-floor, or cost-floor labels.
- Any pooled headline that fails per-symbol, per-domain, or leave-one-out inspection.

## Technique-Impact Ledger Contract

The later technique catalogue will be developed and frozen before the chapter starts. It must be
applied to each candidate against its own fixed baseline, with one direct comparison per technique
and no unplanned combinations.

Each ledger row should identify:

- Candidate and technique ID.
- Fixed baseline and changed component.
- Entry, fill, close, and common-population counts.
- Mean, median, PSR, uncertainty, and tail summaries.
- Drawdown, risk dispersion, occupancy, turnover, and concentration where applicable.
- Per-stratum effect direction, including negative effects.
- Whether the technique changes admission, valuation, execution, or capital allocation.
- Whether the observed change is causal, ambiguous, or invalidated by an integrity defect.

No technique is selected because it clears a gate. The purpose is to quantify what each technique
actually changes, including techniques that damage a KPI.

## Explicit Exclusions

This chapter must not become a second sweep of every historical family. In particular, it should
not rerun the look-ahead result, passive-limit mean-reversion vehicle unchanged, random-ladder
harvest, EPSOSC drift pedestal, or powered signed-volume nulls. A new candidate can be proposed
later only with a distinct mechanism, fill object, information source, or explicitly approved
evidence-recovery rationale.

## Next Artefacts

1. Freeze the technique catalogue before chapter registration.
2. Write one INFR design covering the four candidate anchors and the common ledger contract.
3. Run fresh-context QA against the design and the renewed Nautilus implementation.
4. Produce the technique-impact ledger from new emissions only.
5. Interpret the ledger at the operator boundary; do not let experiment code alter family status.
