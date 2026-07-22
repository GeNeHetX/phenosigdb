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

## Finish

Follow [MAINTAINING.md](../MAINTAINING.md) for the release command.
