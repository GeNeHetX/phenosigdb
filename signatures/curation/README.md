# Curation

Internal maintainer notes for curated signatures.

## Layout

Build-ready curated sources:

- `signatures/curation/<DOMAIN>.<SourceKey>/source.yaml`
- `signatures/curation/<DOMAIN>.<SourceKey>/members.tsv`

Raw supplementary material and one-off parsers:

- `signatures/curation/source_material/<SourceKey>/`

## Build

```bash
pip install -e python
./signatures/phenosigdb-build
./signatures/phenosigdb-build --download-homology
./signatures/phenosigdb-validate
pytest -q signatures/tests
```

## Curated Row Schema

Canonical built columns:

- `signature_id`
- `signature_name`
- `source`
- `source_author`
- `source_pmid`
- `source_doi`
- `species`
- `species_original`
- `gene`
- `gene_original`
- `weight`
- `cell_family`
- `context`
- `disease`
- `tags`
- `homology_relation`
- `homology_db_class_key`

`members.tsv` minimum columns:

- `signature_id`
- `signature_name`
- `gene`

Optional per-row columns:

- `weight`
- `species`
- `cell_family`
- `context`
- `disease`
- `tags`

Rule:

- if a signature has any non-empty `weight`, it is treated as `continuous`
- otherwise it is `binary`
- do not mix weighted and unweighted rows within one signature

## IDs

```text
<DOMAIN>.<SourceKey>.<SignatureName>
```

Rules:

- `DOMAIN`
  - broad, simple, uppercase
- `SourceKey`
  - stable paper/resource key
- `SignatureName`
  - ASCII, machine-friendly, dot-normalized

Normalization:

- no Greek letters in IDs or signature names
- use `alpha`, `beta`, `gamma`, etc.
- spaces and separators normalize to dots or safe ASCII tokens

## Translation

Pinned build rules:

- `1:1` keep
- `1:many` split
- `many:1` collapse within signature
- `many:many` split and collapse
- symbol matching is case-insensitive

Reference outputs:

- `signatures/data/phenosigdb.parquet`
- `signatures/data/phenosigdb_human.parquet`
- `signatures/data/phenosigdb_mouse.parquet`
- `signatures/data/phenosigdb_reference_metadata.json`
- `signatures/data/phenosigdb_human_translation_signature_stats.tsv`
- `signatures/data/phenosigdb_mouse_translation_signature_stats.tsv`

Some translated signatures can drop to zero output rows. Check the translation stats TSVs instead of assuming every signature survives every reference species.

## Workflow

- intake raw data under `source_material/<SourceKey>/`
- write one local parser for that source
- emit curated `source.yaml` + `members.tsv`
- run build
- run validate

No repo-wide intake/promote CLI is needed for paper-specific curation.

## External Imports Boundary

- `CancerRNASig` is reference-only for migrated content
- do not edit `CancerRNASig` from this repo
- optional runtime resources are staged under `signatures/data/external_imports/`
- if a resource is promoted to core curated data, remove its old optional staging logic

## Parser Notes

- prefer `R/readxl` for `.xls` and `.xlsx` in this repo
- Python Excel readers were unreliable in this environment

### CAF.Xing.21

- `summarytableMArker.xlsx`
- broad marker table, not fibroblast-only
- keep `Fibro-C1` to `Fibro-C4`
- exclude `Fibro-C5 / Pericyte`
- use `Annotated Name` as signature label
- split `Selected Marker Genes` on commas

### CAF.Wang.21

- `41421_2021_271_MOESM19_ESM.xlsx`
- one sheet per CAF cluster
- row 1 = cluster id
- row 2 = real header
- header mixes `Gene_name` and `Gene_Name`
- keep only positive `avg_logFC` rows

### CAF.ReviewLiu.26

- `manuallist.txt`
- parse `first token = proposed id`, remainder = gene list
- split genes on comma or whitespace
- infer species from symbol case
- override `cell_family` for pericyte / smooth muscle labels

### CAF.Grout.22

- `caflvl1.txt`
- use `readLines`, not `read.table`

### CAF.Affo.21

- `humanCafGeneset.txt`
- block format: label line, gene lines, blank line
- split genes on comma or whitespace
- normalize `icaf` -> `iCAF`
