# Reference Documents Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan.

**Goal:** Make `docs/references/` a self-contained, chapter-agnostic source of truth and align its dataset, architecture, lane, neutrality, governance, and template documents with the current repository state.

**Architecture:** Keep seven governing documents plus the README in `docs/references/`. Move the obsolete orderflow proposal into the Chapter 04 INFR-013 archive. Encode current rules directly in the live documents; use only stable current code entry points and explicitly marked run-created paths.

**Tech Stack:** Markdown, Git history, shell-based repository and link checks.

## Global Constraints

- Preserve the pre-existing modifications to `docs/knowledge-base/families-explored.md` and `docs/knowledge-base/infr-next-chapter-candidate-extraction.md`.
- Do not rewrite historical archive documents except where a link is directly broken by moving the obsolete orderflow file.
- Do not cite `INFR-*` directives, chapter-specific authority, `.ignore` notes, archived paths, or superpowers plans from live references.
- Do not invent current data materializations. Distinguish existing data from run-created outputs.
- Use `apply_patch` for Markdown edits and a recoverable `git mv` for the requested archive move.

## Tasks

### 1. Establish the live reference boundary

**Files:** `docs/references/README.md`, `docs/references/chapter-06-governance.md` → `docs/references/governance.md`

- Rename the governance document.
- Rewrite the README as the authority/index for the retained set.
- Rewrite governance as standing programme rules, including the universal zero-cost boundary, validity/value separation, no research powering, operator decisions, and lane roles.

**Verify:** README lists only retained live documents; governance has no chapter status or historical authority citation; active links to the old filename are identified for repair.

### 2. Consolidate neutrality and statistical rules

**Files:** `docs/references/neutrality-standard.md`

- Remove directive and archive provenance.
- Preserve and hardcode N1–N11.
- Include the exact zero-cost disclosure, PSR formula and `psr_n` pairing rule, sample-size treatment, validity conditions, and powering-strip denylist.

**Verify:** The document stands alone and contains no unresolved reference to a plan, directive, chapter, or archive.

### 3. Replace the stale dataset and architecture descriptions

**Files:** `docs/references/dataset-reference.md`, `docs/references/architecture.md`

- Describe the current Bybit catalog, admission counts, materialized layout, signed-bar TRAIN catalog, cTrader compatibility catalog, fence dates, and sanctioned access wrapper.
- Remove stale census interpretations, archived artifact paths, old cTrader-primary framing, and nonexistent current directory claims.
- State the exact signed-volume and mean-price-skew semantics.
- Explain run-created emission output without claiming that an empty clean slate already contains run outputs.

**Verify:** Every claimed current path exists or is explicitly marked as created by an authorized run; layout and counts agree with `data/` and the checked-in fence facts.

### 4. Update the SPDR and XENA lane documents

**Files:** `docs/references/spdr-lane.md`, `docs/references/xena-lane.md`

- Remove historical cTrader-primary, power-analysis, and archived-registry narratives.
- Encode current screening, portfolio-construction, causality, holdout, ledger, cost, PSR, and operator-decision rules.
- Reconcile XENA `passed` as an operator-facing machinery field rather than an economic verdict.
- Keep the gross, zero-cost, non-deployable boundary explicit.

**Verify:** Both lanes agree on engine, costs, validity, and final-disposition semantics; no stale contradiction remains.

### 5. Refresh the XENA design template

**File:** `docs/references/xena-run-design-template.md`

- Make the template current and pre-registration oriented.
- Require universe, bands, candidate accounting, gate budget, amendments, and cost semantics.
- Remove frozen historical registry/hash requirements and old cost tables.

**Verify:** A copied template can define a run without consulting historical plans or an archived registry.

### 6. Archive the obsolete orderflow proposal and repair active links

**Files:** move `docs/references/orderflow-feature-store.md` to `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-013/orderflow-feature-store.md`; update active links caused by the governance rename and move.

- Keep the proposal in its originating experiment archive.
- Update only historical links that become directly broken by the move, if required for local archive coherence.
- Update non-archive live references to `governance.md` where the old filename is used.

**Verify:** The old live orderflow path is absent, the archive destination exists, and no non-archive link points at the old governance filename.

### 7. Run final audits

- Run `git diff --check`.
- Search retained references for archive paths, `.ignore`, `INFR-*`, chapter-specific authority, directive IDs, and superpowers-plan paths.
- Validate all Markdown links that can be checked locally.
- Review the diff for contradictions and confirm unrelated worktree changes remain untouched.

**Verify:** All success criteria in the design record pass; report any repository-level historical links intentionally left unchanged.
