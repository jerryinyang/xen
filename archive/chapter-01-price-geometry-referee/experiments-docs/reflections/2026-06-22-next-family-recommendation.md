# Next-Family Recommendation — verbatim (2026-06-22)

> Captured verbatim from the post-Phase-018 discussion (CF-CAPGEO-001 retired at G-018). This is the
> assistant's full, exact recommendation for the next candidate family, preserved unedited for a fresh-context
> deep-dive. Companion: [Phase 018 retrospective](../checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md);
> [two-family retrospective reflections](2026-06-19-two-family-retrospective-reflections.md).

---

Out of ideas is the right place to be — you've genuinely exhausted a vein, and the honest move is to read what the three dead families are *telling* you rather than dig a fourth hole next to them.

## What the three closures actually rule out

CF-AVWAP-001, CF-HA-HARAMI-001, CF-CAPGEO-001 are not three different failures. They're one failure, three times: **single-instrument, event-driven, price-geometry signals carry no signal-conditional *directional* edge.** EXP-081 said it most cleanly — favourable *availability* ≈ random. You've now also ruled out that the exit, the sizing, or a strength filter rescues it. So the next family must change the **category of signal**, not tune within it. Two categories are genuinely untouched, and I have a clear ranking.

## My genuine recommendation: stop predicting direction; predict *magnitude*

Here's the thing I think the data has been screaming and the programme kept reading past: the recurring **median-positive / mean-killed, heavy-tailed** shape is *not* a weak directional edge. It's the **fingerprint of a volatility signal being measured through a directional lens.** A compression pattern that usually resolves slightly your way (median +) but occasionally gaps hard against you (mean killed by the tail) is exactly what a *magnitude* signal looks like when you score it as signed return. And the harami literally *is* a compression pattern (an inside bar on HA). You've been measuring `E[signed return]` ≈ 0 and concluding "no edge," when the structure may live entirely in `E[|return|]` / realized range.

So the next family:

> **Non-directional volatility-expansion signals: does a compression/quiet-state signal predict forward *realized range* (magnitude), independent of direction — harvestable as a breakout/straddle rather than a directional bet?**

Why I'd lead with this over anything else:
- **It follows your own evidence.** This isn't a new guess; it's the direct reading of EXP-081's "shape has structure, direction doesn't." Falsification-first means following the data, and the data points here.
- **It's the cheapest possible falsification.** Run the *exact* EXP-081 availability screen, but on forward realized range / |return| (ATR-normalized) vs a random-entry baseline, TRAIN-only, 0 reads. If compression signals show forward-range > random, you've found the **first non-random availability the programme has ever seen.** If it's ≈ random too, you kill it for one experiment's cost and you've learned the structure isn't even in magnitude.
- **The cost budget exists.** EXP-085 showed 4h gross magnitudes (1–2 ATR) dwarf cost (~15–30%). A straddle pays both sides, but that's a *different, larger* magnitude budget to clear — not the near-impossible directional one.
- **It reuses most of your machinery** (single-instrument, event-driven, per-event expectancy, separability gate) — you mainly swap the endpoint from signed return to range/|return| and the exit from directional to a breakout bracket.

## The strong runner-up (and the bigger bet): go cross-sectional

The other fully untested axis: **every family so far was time-series — "does *this* instrument move after the signal."** You have 16 instruments across FX/metals/crypto/indices, 5 years, synchronized, and you've **never once asked a relative question.** Cross-sectional momentum / relative-strength is among the most robust empirical anomalies across asset classes precisely because its edge source is the *relationship* between instruments, not one instrument's price pattern — a fundamentally different, demonstrably non-random signal from what you've been testing.

Why it's the runner-up and not the lead: **higher ceiling, higher cost.** It's a real pivot in the programme's character (event-driven → ranking/rebalance/market-neutral portfolio returns), needs new infrastructure (the referee suite, separability gate, and per-event expectancy are all built for single-instrument events), and is a bigger commitment before the first cheap "is there availability" read. If you'd rather make the strategic bet now, this is the one — but I'd want the magnitude screen first because it's a tenth of the work to falsify.

## How I'd actually sequence it

1. **One cheap diagnostic, no slots, no reads** — the magnitude-availability screen: forward realized range (ATR units) conditional on your existing compression signals (harami, and a clean NR/inside-bar primitive) vs random entry, TRAIN-only. This is an EXP-081 clone with one column changed. It's the lowest-cost, highest-information next action you can take.
2. **If magnitude-availability beats random** → open the volatility-expansion family at a proper G0/D0 (breakout/straddle harvest, range endpoint, the median/tail co-primary you already trust).
3. **If it's ≈ random too** → that's a *huge* result: it says there's no harvestable structure of either kind in single-instrument price geometry, and it fully justifies the cross-sectional pivot as the next family. You'd reach that decision having spent one experiment, not a phase.

If you want, I can draft the scope for that magnitude-availability diagnostic right now — it's small, it reuses the EXP-081 substrate/readiness scaffolding, and it would tell you which of these two families to actually open before you spend a single slot.
