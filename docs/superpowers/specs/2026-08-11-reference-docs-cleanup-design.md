# Live Reference Documents Cleanup Design

## Goal

Make `docs/references/` the one-step, chapter-agnostic source of truth for the Xen programme. A reader of a live reference must not need a chapter pack, archived directive, temporary source note, or historical experiment plan to determine the current rule.

The cleanup also makes the dataset reference describe the data that is actually materialized under `data/`, and removes the obsolete orderflow feature-store proposal from the live reference set.

## Scope

### Live documents to retain and rewrite

- `governance.md` — standing programme rules and validity boundaries.
- `neutrality-standard.md` — the complete neutrality, evidence, PSR, and powering-strip rules.
- `architecture.md` — the current event-driven research architecture and data flow.
- `dataset-reference.md` — the current Bybit, signed-bar, and compatibility-catalog state.
- `spdr-lane.md` — the current lightweight screening lane.
- `xena-lane.md` — the current portfolio-construction lane.
- `xena-run-design-template.md` — a current pre-registration template.
- `README.md` — the live reference-set index and authority statement.

### Archive action

Move `orderflow-feature-store.md` to the Chapter 04 INFR-013 experiment archive. It describes a historical feature-store proposal and implementation skeleton, not a current programme contract. The live reference index must no longer advertise it.

### Compatibility action

Rename `chapter-06-governance.md` to `governance.md` and update active links caused by that rename. Historical archive material remains historical and is not rewritten as part of this cleanup.

## Content decisions

### Authority boundary

Live references will contain rules and facts directly. They may name current code entry points and stable repository paths, but they will not cite `INFR-*` identifiers, chapter-specific directives, archived paths, `.ignore` source notes, or superpowers plans as authority.

Historical context belongs in the archive. If a historical change still governs current work, its operative rule will be restated in the live document itself.

### Dataset truth

The live dataset description will be pinned to the current materialization:

- 903 structurally readable Bybit symbols in the catalog.
- 894 admitted symbols and 9 specification-incomplete symbols.
- 672,138,742 total bars in the admitted materialization.
- Five-symbol signed-bar TRAIN catalog with 3,731,908 rows across 90 parquet files.
- Three-instrument cTrader compatibility catalog, explicitly non-primary.
- Current fence dates, Nautilus version pin, manifest hash, and sanctioned fenced-read wrapper.

The document will describe the actual `data/catalog/data/...` and `data/catalog_sigbar/train/data/...` layout. It will distinguish materialized data from per-run output directories that are created only when an authorized run executes.

### Statistical and cost rules

The live neutrality rules will include the complete zero-cost disclosure, PSR definition and pairing rule, sample-size treatment, validity/value separation, and powering-strip restrictions. Lane documents and the run template will encode the operational consequences directly, including:

- no cost-complete, tradable, or deployable claims by default;
- no research powering, MDE, detection floors, or machine success labels;
- direct predeclared baseline comparisons and descriptive sample-size context;
- PSR computed on the same predeclared per-trade series as the reported Sharpe ratio;
- operator-only final disposition.

### Lane consistency

SPDR and XENA will use the same current cost, validity, causality, holdout, and operator-decision semantics. SPDR remains a screening lane; XENA remains a portfolio-construction lane. Both will describe the sanctioned event-driven engine without retaining the superseded cTrader-primary narrative.

The XENA template will require predeclared universe, bands, candidate accounting, gate budget, and cost semantics, without requiring a historical frozen registry or importing old calibration values.

## Success criteria

1. No file under `docs/references/` contains an archive path, `.ignore` path, `INFR-*` authority citation, chapter-specific authority citation, or superpowers-plan citation.
2. No retained live document relies on a historical artifact to define a current rule.
3. Every path presented as current either exists now or is explicitly identified as a run-created/future output path.
4. `orderflow-feature-store.md` is absent from the live set and present in the Chapter 04 archive.
5. The governance filename and all active links agree.
6. The contradictions around cTrader primacy, research powering, cost accounting, XENA `passed`, and signed-bar meaning are removed.
7. `git diff --check` passes, and unrelated pre-existing worktree changes remain untouched.
