---
name: per-notional-blind-to-size
description: A per-notional estimand divides the size term out by construction; its exact zero is a units alarm, not a null.
metadata: { type: lesson, chapter: 5 }
---
In SPDR-021/022/023 the paired SIZE delta was exactly `0.000000` on **1,400 of 1,400 rows in all
six cells**. Per-trade bps is per-unit-notional: halving size halves numerator and denominator,
so the result is an algebraic identity that reports as a clean, confident, tightly-CI'd zero —
the most convincing-looking null in the study, and entirely an artifact of the unit. The one
device that survived every other refutation was being measured by an instrument that cannot see
it.

Rules: any **sizing, exposure or capital-efficiency** claim requires a **capital-normalised**
estimand (`E6`). Before accepting any null, verify the estimand can express the effect — an exact
zero across 100% of rows is a **units alarm**. Related: [[unit-pin-money-floor]] (L-21 unit pin
at seams; this pins the estimand's *capability*).
