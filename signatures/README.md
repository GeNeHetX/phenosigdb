# Signatures

Maintainer area only.

Repository layout:

- `signatures/curated/`: build-ready YAML/TSV signature inputs
- `signatures/source_material/`: raw files and one-off parsers
- `data/`: generated core artifacts and homology references
- `tools/`: maintainer code and commands
- `packages/python/`: Python user package
- `packages/r/`: R user package

## Add A Paper

Do this once per paper/source. For two papers, repeat with two different `SourceKey` values.

1. Make a folder:

```text
signatures/source_material/<SourceKey>/
```

2. Put the downloaded supplementary files there.
3. Put one parser there: `build_curated.R` or `build_curated.py`.
4. Run the parser. It reads `source_material` and writes one curated folder. It does not write new files beside the raw input.

```text
signatures/curated/<DOMAIN>.<SourceKey>/
```

5. That folder must contain:

```text
source.yaml
members.tsv
```

6. `members.tsv` needs at least:

```text
signature_id	signature_name	gene
```

Add `weight` for weighted signatures. Do not mix weighted and unweighted rows in one signature.

Minimum information for a new signature:

```yaml
source: JournalAuthor24
source_author: Author
source_pmid: ""
source_doi: ""
species: human
cell_family: fibroblast
context: cancer
disease: PDAC
tags: CAF
```

And for each gene set:

```text
signature_id	signature_name	gene
CAF.JournalAuthor24.proCAF	proCAF	COL1A1
```

Required to build: `signature_id`, `signature_name`, and at least one non-empty `gene` in `members.tsv`.
Required metadata: `source`, `species`, `cell_family`, `context`, and `disease`; use `unknown` only when genuinely unavailable. PMID and DOI may be empty, but author/source provenance must remain.

Use IDs like:

```text
CAF.JournalA24.proCAF
CAF.JournalB25.restCAF
```

Use simple uppercase domains, stable source keys, ASCII signature names, and no Greek letters.

## Outputs

- `data/phenosigdb.parquet`
- `data/phenosigdb_human.parquet`
- `data/phenosigdb_mouse.parquet`
- `data/phenosigdb_reference_metadata.json`
- `data/phenosigdb_human_translation_signature_stats.tsv`
- `data/phenosigdb_mouse_translation_signature_stats.tsv`

## Versioning

- curated core data changes when the repo curation changes
- optional resources are pinned by PhenoSigDB release code and manifests
- MSigDB resources use explicit upstream release URLs
- WikiPathways resolves the current Homo sapiens GMT file and records the resolved version in the installed manifest
- Reactome is fetched from the official current GMT zip and recorded with install metadata and checksum

## Release

R must have `arrow`, `jsonlite`, `rappdirs`, and `testthat` installed. Run this from the repository root:

For a new source, run exactly this from the repository root. Replace the parser path and version for future releases.

```bash
Rscript signatures/source_material/CAF.Peng.26/build_curated.R
./tools/phenosigdb-release 0.1.8
git diff --stat
git diff -- README.md
git add -A
git commit -m "Release v0.1.8"
git push origin main
git tag -a v0.1.8 -m "Release v0.1.8"
git push origin v0.1.8
gh release create v0.1.8 \
  dist/phenosigdb_0.1.8.tar.gz \
  dist/phenosigdb-r.tar.gz \
  --verify-tag --generate-notes
```

The final `gh` command publishes the local tarballs. The tag workflow only verifies the release; it does not build or upload files.

Install the exact release in R:

```r
remotes::install_url(
  "https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.8/phenosigdb_0.1.8.tar.gz"
)
```

Later, install the latest published release:

```r
remotes::install_url(
  "https://github.com/GeNeHetX/phenosigdb/releases/latest/download/phenosigdb-r.tar.gz"
)
```

More curation rules live in [signatures/curated/README.md](/Users/remy.nicolle/Workspace/DEV/phenosigdb/signatures/curated/README.md).
