# Open questions — REF-A / REF-B — DECISION LOG (frozen)

**Date frozen:** 2026-07-16  
**Applies to D0 cards:**  
- `cf-htfcap-001.md` (REF-A)  
- `cf-epsosc-001.md` (REF-B)  
- SPDR packs: `docs/references/spdr-pack-htfcap-001.md`, `spdr-pack-epsosc-001.md`  

## Locked before this sheet (discussion)

| Item | Decision |
|---|---|
| Route | SPDR → XENA (skip EXP) |
| Rules | Unlocked multi-variant exploration |
| Priors | Soft market; hard process bans |
| Universe substrate | Bybit / Nautilus primary; legacy residue = prior only |

## Operator freeze (2026-07-16)

| ID | Choice | Note |
|---|---|---|
| **Q1** | **10-asset universe** | Membership via **instrument selection rules** (not ad-hoc list only). Selector implementation may follow (`xen.nautilus.universe_selection` currently uncodified — rules still stated in SPDR/XENA design.md at run time). |
| **Q2** | **A — K = 3** | Per recommendation |
| **Q3** | **A — parallel, separate packs/universes** | Per recommendation |
| **Q4** | **A — SPDR may proceed on available Bybit data; XENA after emission+cost+CAL** | **Clarification:** CAL is **waiting on these family D0s**, not the reverse. Design is complete so ckpt-013 / CAL can be shaped to family class. Do not block D0 on CAL. |
| **Q5** | **A — funding disclose @ SPDR, bind @ XENA** | Per recommendation |
| **Q-A1** | **A — unfiltered + momentum + random control** | Per recommendation |
| **Q-A2** | **A — must include 2× and 4× holds; short allowed** | Per recommendation |
| **Q-B1** | **A — two episode objects at SPDR** | Per recommendation |
| **Q-B2** | **A — one-sided required; two-sided optional ≤25%** | Per recommendation |
| **Q-B3** | **A — VR diagnostic parallel, not sole hard-gate** | Per recommendation |

## Option catalogue (reference only — decisions above bind)

<details>
<summary>Original options text (collapsed reference)</summary>

### Q1 — SPDR universe size
- A: 6–10 liquid majors  
- B: Top 20  
- C: Full archive universe  
**Taken:** 10 + selection rules.

### Q2 — Cluster K
- A: K=3 · B: K=5 · C: K=1 + analyst only → **A**

### Q3 — Parallelism
- A: parallel separate · B: serial · C: combined mega-grid → **A**

### Q4 — SPDR before full INFR
- A: vectorised Bybit SPDR OK; XENA waits CAL · B: block all until Phase D · C: legacy FX only → **A** (+ CAL waits on D0)

### Q5 — Funding
- A: disclose SPDR / bind XENA · B: full at SPDR · C: ignore → **A**

### Q-A1 — LTF bases
- A: unfiltered+momentum+random · B: unfiltered+random only · C: wide menu → **A**

### Q-A2 — Long holds
- A: mandatory 2×/4× · B: free · C: long only → **A**

### Q-B1 — Episode objects
- A: two · B: one · C: four+ → **A**

### Q-B2 — Two-sided
- A: one-sided required, two-sided ≤25% · B: one-sided only · C: two-sided default → **A**

### Q-B3 — VR diagnostic
- A: parallel facet · B: hard gate · C: none → **A**

</details>
