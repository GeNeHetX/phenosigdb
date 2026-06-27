# PhenoSigDB

PhenoSigDB is a curated reference database of transcriptomic gene-set signatures.

One row in the parquet = one gene in one signature.

## Main files

- `data/phenosigdb.parquet`
  - original curated species
- `data/phenosigdb_human.parquet`
  - all signatures represented in human symbols
- `data/phenosigdb_mouse.parquet`
  - all signatures represented in mouse symbols
- `data/phenosigdb_reference_metadata.json`
  - build metadata, pinned homology metadata, translation summary
- `data/phenosigdb_human_translation_signature_stats.tsv`
- `data/phenosigdb_mouse_translation_signature_stats.tsv`

## Naming

```text
signature_id = <DOMAIN>.<SourceKey>.<SignatureName>
```

Examples:

- `CAF.Elyada19.iCAF`
- `PDAC.Moffitt15.Classical`
- `IMMUNE.Becht16.Tcells`

## Build

```bash
pip install -e .
phenosigdb-build --download-homology
phenosigdb-validate
```

Translation rules are fixed:

- `1:1` keep
- `1:many` split
- `many:1` collapse within signature
- `many:many` split and collapse

## Python

Use two functions:

- `list_signatures()`
  - returns one row per signature
- `get_signatures()`
  - returns gene sets for selected `signature_id` values

### Python example

```python
from phenosigdb import get_signatures, list_signatures

meta = list_signatures()
print(meta[["signature_id", "domain", "cell_family", "n_genes"]].head())

caf = meta[meta["domain"] == "CAF"]
caf_ids = caf["signature_id"]

caf_sets = get_signatures(caf_ids)
print(caf_sets["CAF.Elyada19.iCAF"][:10])
```

Minimal text search is available on the metadata table:

```python
from phenosigdb import list_signatures

list_signatures(query="Elyada")
```

Return a row table instead of a dict:

```python
from phenosigdb import get_signatures, list_signatures

meta = list_signatures(query="Elyada")
table = get_signatures(meta["signature_id"], format="table")
```

Switch reference species:

```python
from phenosigdb import get_signatures

original = get_signatures(["CAF.Elyada19.iCAF"], reference_species="original")
human = get_signatures(["CAF.Elyada19.iCAF"], reference_species="human")
mouse = get_signatures(["CAF.Elyada19.iCAF"], reference_species="mouse")
```

Arguments are intentionally small:

- `list_signatures(query=None, reference_species="original", path=None)`
- `get_signatures(signature_ids=None, format="dict", reference_species="original", path=None)`

`path` can point to a parquet file if you want to read another copy explicitly.

`phenosig()` is still available for backward compatibility, but the intended user API is now `list_signatures()` + `get_signatures()`.

## R

Source one file directly from GitHub:

```r
source(url("https://raw.githubusercontent.com/GeNeHetX/phenosigdb/v0.1.0/R/phenosigdb.R"))
```

Requirements:

```r
install.packages("arrow")
```

The R helper uses local `data/phenosigdb*.parquet` if present. If not, it downloads the matching parquet from GitHub.

### R example

```r
source(url("https://raw.githubusercontent.com/GeNeHetX/phenosigdb/v0.1.0/R/phenosigdb.R"))

meta <- list_signatures()
meta[, c("signature_id", "domain", "cell_family", "n_genes")]

caf_ids <- meta$signature_id[meta$domain == "CAF"]

caf_sets <- get_signatures(caf_ids)
caf_sets[["CAF.Elyada19.iCAF"]][1:10]
```

Get a row table:

```r
meta <- list_signatures(query = "Elyada")
table <- get_signatures(meta$signature_id, format = "table")
```

Switch reference species:

```r
human_sets <- get_signatures(caf_ids[1:2], reference_species = "human")
mouse_sets <- get_signatures(caf_ids[1:2], reference_species = "mouse")
```

R function signatures:

- `list_signatures(path = NULL, reference_species = c("original", "human", "mouse"), query = NULL)`
- `get_signatures(signature_ids = NULL, path = NULL, reference_species = c("original", "human", "mouse"), format = c("dict", "table"))`

For a newer release later, replace `v0.1.0` in the source URL with another git tag.

## Canonical columns

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
- `cell_family`
- `context`
- `disease`
- `tags`
- `homology_relation`
- `homology_db_class_key`

## Curation

- curated source folders: `curation/<DOMAIN>.<SourceKey>/`
- source metadata: `source.yaml`
- signature members: `members.tsv`
- raw supplementary material and one-off intake scripts: `curation/source_material/<SourceKey>/`

## Licensing

- code: MIT
- curated data: CC BY 4.0

See [LICENSE](LICENSE) and [LICENSE-DATA.md](LICENSE-DATA.md).

<!-- PHENOSIGDB_SIGNATURES_START -->

## Available Signatures

| Domain | Signature count | Species | Cell family | Context | Disease |
| --- | ---: | --- | --- | --- | --- |
| `CAF` | 78 | human, mouse | fibroblast, pericyte, smooth_muscle | cancer | PDAC, unknown |
| `CCA` | 7 | human | epithelial | cancer | cholangiocarcinoma |
| `ECM` | 1 | human | stromal | cancer | PDAC |
| `FIBROBLAST` | 31 | human, mouse | fibroblast | unknown | unknown |
| `GASTRIC` | 26 | human, mouse | epithelial | physiology | normal |
| `GASTRIC_CANCER` | 10 | human | tumor | cancer | gastric_cancer |
| `GI` | 35 | human | epithelial | physiology | normal |
| `HCC` | 73 | human | tumor | cancer | HCC |
| `IBD` | 96 | human | immune | inflammation | IBD |
| `IMMUNE` | 47 | human | T_cell, immune, macrophage, neutrophil | unknown | unknown |
| `ORGANOID` | 48 | human | epithelial | organoid | unknown |
| `PANCREAS` | 37 | mouse | epithelial | physiology | normal |
| `PAN_CANCER` | 41 | human | tumor | cancer | cancer |
| `PDAC` | 67 | human | stromal, tumor | cancer | PDAC |
| `SINET` | 4 | human | tumor | cancer | siNETs |

<!-- PHENOSIGDB_SIGNATURES_END -->
