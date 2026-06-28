# Source Material

Single maintainer intake point for raw supplementary material and one-off parsers.

Most older curated signatures were migrated from CancerRNASig. New direct curation work should start here.

## Workflow

1. Create `signatures/curation/source_material/<SourceKey>/`.
2. Put raw files there.
3. Add one local parser such as `build_curated.R` or `build_curated.py`.
4. Emit `signatures/curation/<DOMAIN>.<SourceKey>/source.yaml`.
5. Emit `signatures/curation/<DOMAIN>.<SourceKey>/members.tsv`.
6. Run `./signatures/phenosigdb-build`.
7. Run `./signatures/phenosigdb-validate`.

## Rules

- this folder is raw downloads, notes, and one-off scripts
- sibling curated folders are the build-ready source of truth
- IDs use `<DOMAIN>.<SourceKey>.<SignatureName>`
- keep domains simple and uppercase
- no Greek letters in IDs or signature names
- use `beta`, `gamma`, etc.
- keep the workflow explicit and local to each source

## CancerRNASig Imports

CancerRNASig remains reference-only.

- use it to recover metadata or model objects when needed
- do not edit it from here
- if a CancerRNASig-derived model is promoted into PhenoSigDB core, create a local source folder and parser in this directory

Current example:

- `CancerRNASigModels/build_curated.R`
  - builds weighted curated sources for `PDAC.PAMG20` and `PDAC.GemPred20`
