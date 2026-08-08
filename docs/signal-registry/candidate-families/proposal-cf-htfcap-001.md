# PROPOSAL — CF-HTFCAP-001 — Higher-Timeframe Context × Capture Scale

**Status:** `SUPERSEDED` (2026-07-16) — authoritative D0: [`cf-htfcap-001.md`](cf-htfcap-001.md).  
**Working name:** REF-A  
**Chapter context:** post–INFR-010 (NautilusTrader + Bybit USDT-perp primary)  
**Supersedes / re-opens:** spirit of CF-HTFDI-001 (P-14) and the capture-scale intent of CF-MTFCTX-001 — **new family, new D0, new stack**. Does **not** revive retired cards or import their verdicts as true on Bybit.

**Companion:** SPDR pack → *(removed from live refs — family closed)*  
**Shared open questions:** `docs/signal-registry/candidate-families/proposal-ref-ab-open-questions.md`

---

## 1. Thesis (restated)

Higher-timeframe (HTF) market state can change the **conditional quality and/or scale** of lower-timeframe (LTF) trades. Prior work found a **real but thin** directional-conditioning channel and **failed to monetize** it at short grain and on weak bases. This family re-opens the question on the **Bybit crypto universe** with:

- **many** HTF-state definitions, LTF entry modalities, and hold/capture scales  
- **no locked** entry/exit rules  
- qualification via **SPDR (family justification) → full XENA (portfolio + cost)** if promising  
- room for **crypto-native** paths that were never on the FX/indices tape  

**Not claimed:** that USTEC 1h/5min HTF-DI numbers transfer to Bybit, or that multi-day holds are automatically better.

---

## 2. Binding process decisions (operator-aligned, 2026-07-16)

| Decision | Choice |
|---|---|
| Route | **SPDR → (minimal promote) → full XENA** |
| EXP lane | **Skipped** — XENA cost layer + portfolio contribution is the qualification mechanic |
| Rules | **Not locked** — explore hyperparameter and sub-modality variants in SPDR and XENA |
| Universe | New stack primary (**Bybit USDT linear perps**); old FX/indices residue is **prior**, not truth |
| Priors from past kills | **Soft** (shape grids and diagnostics); **hard** only for process mistakes and identical dead structures |
| Qualification philosophy | Avoid fragile per-variant “metric perfection”; let **portfolio contribution under cost** select variants |

---

## 3. Prior evidence (legacy — do not transplant as Bybit fact)

| Source | What it established | What it did **not** establish |
|---|---|---|
| SPDR-001..003 / CF-HTFDI-001 | HTF ±DI can condition LTF forward path; USTEC 1h/5min continuation; dir_gap scaled with hold **in ATR units** (H12→H48 ≈ 1h–4h) | Deployable money; multi-day holds; 4h/1h domain as supported |
| EXP-025 | Channel real at ~**1–4 bps**/trade after unit correction; tradability failed (0/440 qualifiers) | That longer holds were fully stress-tested in money units |
| CF-MTFCTX / XENA-001..003 | Longer hold **grid existed** (0.5–4× HTF span; 1d/1h, 4h/15m, 1h/5m); bases exhausted / print / binder issues | Fair proof that HTF conditioning is more edgeful at long hold; filter thesis under costless objective was confounded (L-26) |

**Soft design hints (not auto-rejects):** prefer including longer holds / coarser grains in the grid; report **bps** early; control or disclose drift; don’t treat passive fill as free edge.

---

## 4. Hard bans (process — any universe)

1. Look-ahead / non-causal HTF (forming bar); decisions only on confirmed HTF/LTF.  
2. Unit lies across seams (ATR-normalised screen → bps graduation without pin).  
3. Costless “success” when the claim is net edge; cadence-only objectives when testing selectivity.  
4. Passive-limit “edge” without fill-vs-prediction decomposition (or explicit MM product framing).  
5. Counting SPDR as tradability/deployability.  
6. Importing chapter-03 XENA registry pins onto Bybit without fresh CAL.

---

## 5. Soft priors (shape, don’t forbid)

- Short-hold thin conditioning may be real and still sub-cost → grid should **include** large-capture cells, not only short holds.  
- Old clean cell was index-led → start SPDR with **liquid majors**, allow broader universe in XENA.  
- XENA search historically over-weighted high cadence → binder must **penalize cost**, not reward trade count alone.

---

## 6. Exploration plane (no locked rules)

Variant axes are **illustrative defaults** for the first SPDR pack and the first XENA universe; operator may widen/narrow before run.

| Axis | Example levels (not final) | Role |
|---|---|---|
| HTF/LTF pair | e.g. 1h/5m, 4h/15m, 1d/1h (and crypto-native alternatives) | Domain |
| HTF state modality | ±DI continuation; ADX gate; vol regime; combinations; other simple HTF direction stats | Sub-model |
| LTF entry modality | random-sign baseline (control); naive momentum; breakout; other thin LTF rules | Base vehicle |
| Hold / capture | Multiples of HTF span (include short and long) | Capture scale |
| Filter polarity | with-HTF / against-HTF / unfiltered baseline | Mechanism check |
| Symbols | **10-asset** SPDR universe via instrument selection rules (Q1); XENA may expand later | Universe |

**Controls (measurement instruments, not candidates to “save”):** unfiltered baseline; optional random-sign null base; phase-shift / misaligned-HTF sentinels where cheap.

---

## 7. Route detail

```text
SPDR pack (TRAIN-only, multi-variant, disposition-only)
    → operator: WORTH_EXPLORING / NOT_WORTH / INCONCLUSIVE
    → if WORTH_EXPLORING: register family (if not yet) + build XENA universe
Full XENA (Nautilus emissions, Bybit cost model, portfolio selection, cost-aware binder after fresh CAL)
    → operator gate / TEST only under current ledger rules
```

**SPDR promote bar:** minimal — see SPDR pack (cluster lift vs null, not deploy CI).  
**XENA:** pre-search gross-bps sanity vs breakeven band (XENA-003 lesson); finite `SlPrice` / sizing contract; net cost binds selection.

---

## 8. Success / kill (family level)

| Stage | Success (route forward) | Kill / park |
|---|---|---|
| SPDR | Predeclared promote rule met on ≥1 coherent variant **cluster** | No cluster lift; pure noise / underpowered only → INCONCLUSIVE |
| XENA | Cost-aware portfolio certification finds structure beyond battery null | Universe noise-like under honest binder; or only print/cadence artifacts |

No global-holdout deploy claim on legacy rules without a new sanctioned shot policy on the new fence.

---

## 9. Infrastructure dependencies

- Nautilus emission path + catalog fence (INFR-010 lineage).  
- Bybit T1 cost stack: spread model + fees + **funding** (critical for multi-session holds).  
- XENA: **fresh CAL + hash-pinned registry** before counted gate (old registry VOID).  
- Real volume available — optional for HTF state; useful for vol-regime features.

---

## 10. Open questions

See shared sheet: `proposal-ref-ab-open-questions.md` (Q1–Q3 family-shared; Q-A* for this family).

---

## 11. Operator sign-off block

| Item | Decision | Date |
|---|---|---|
| Approve thesis + route (SPDR→XENA, no EXP) | ☐ | |
| Approve hard bans / soft priors | ☐ | |
| Resolve open questions (shared sheet) | ☐ | |
| Assign SPDR-ID / register CF-ID | ☐ | |
