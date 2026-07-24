# PhenoSigDB

PhenoSigDB is a signature database and access library for Python and R, providing gene sets (signatures) for cancer, immune, stromal, and other biological contexts.

## Installation

### Python
```bash
pip install git+https://github.com/GeNeHetX/phenosigdb.git#subdirectory=packages/python
```

### R
```r
remotes::install_url(
  "https://github.com/GeNeHetX/phenosigdb/releases/latest/download/phenosigdb-r.tar.gz"
)

# Reproducible release:
# remotes::install_url("https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.19/phenosigdb_0.1.19.tar.gz")
```

## Quick Start

### Python
```python
from phenosigdb import list_signatures, get_signatures, phenosigdb_resources

# List all available signatures
meta = list_signatures()

# Search signatures (case-insensitive regex across default metadata columns)
caf_signatures = list_signatures("FIBROBLAST")

# Get signatures selected from the metadata table
sig = get_signatures(caf_signatures)

# Install optional resources
phenosigdb_resources("install", "pid")
```

### R
```r
library(phenosigdb)

# List all available signatures  
meta <- list_signatures()

# Search signatures (regex by default, case-insensitive)
caf_signatures <- list_signatures("FIBROBLAST")

# Get signatures selected from the metadata table
sig <- get_signatures(caf_signatures)

# Install optional resources
phenosigdb_resources("install", "pid")
```

## Public API

### Find signatures

```r
list_signatures("FIBROBLAST")
list_signatures("metabolism", columns = c("signature_name", "context"))
```

`query` is one case-insensitive regex searched across `signature_id`, `signature_name`, `source`, `domain`, `cell_family`, `context`, and `disease`. `columns` is optional. `min_genes` and `signature_format` provide simple size/type filters.

### Get signatures

Pass either IDs from the `signature_id` column of `list_signatures()` or the complete table returned by `list_signatures()`:

```r
get_signatures(caf_signatures)
```

Python uses the same calls with a DataFrame and returns a dictionary. R returns a named list. Binary signatures are gene vectors; weighted signatures are gene-to-weight mappings.

### Manage resources

```r
phenosigdb_resources("list")
phenosigdb_resources("install")
phenosigdb_resources("update")
```

`list` shows the bundled `core` database and optional resources, including versions and installed status. `install` adds missing optional resources. `update` refreshes installed optional resources.

## Metadata Columns

| Column | Description |
|--------|-------------|
| `signature_id` | Unique identifier (e.g., `FIBROBLAST.Elyada19.iCAF`) |
| `signature_name` | Human-readable name (e.g., `iCAF`) |
| `source` | Signature origin, e.g. `curated.Elyada19`, `MSigDB.C8`, `BioCarta` |
| `domain` | Broad biology group, e.g. `CELL`, `CANCER`, `PATHWAY` |
| `collection` | Resource family, e.g. `CellMarker`, `msigdb.C7`, `Reactome` |
| `species` | Species (human/mouse) |
| `cell_family` | Cell type family (e.g., `fibroblast`, `tumor`) |
| `context` | Biological context (e.g., `cancer`, `pathway`) |
| `disease` | Disease association (e.g., `PDAC`, `HCC`) |
| `signature_format` | `binary` or `continuous` |
| `n_genes` | Number of genes in signature |

`list_signatures()` lists original signatures once. `get_signatures()` serves them as human by default, or translates to mouse/original identifiers when requested with `reference_species`.

## Curated Signatures

Organized by domain. Bundled signatures are the core curated database.

- **FIBROBLAST**: Multiple PDAC CAF subtypes (iCAF, myoCAF, etc.) from Elyada19, Dominguez20, Kieffer20, etc.
- **PDAC**: Tumor, stromal, immune signatures from Bailey16, Moffitt15, Collisson11, etc.
- **IMMUNE**: Immune cell type signatures from Becht16, Chu23, Mulder21, Rodrigues18, Wu24
- **Other**: GASTRIC, HCC, ORGANOID, CCA, etc.

For bundled signatures: `list_signatures()` returns the core curated database.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

<!-- PHENOSIGDB_SIGNATURES_START -->

## Available Signatures

Core curated signatures: **785** across **48** curated source keys.

| Domain | SourceKey | Signatures | Format | Species | Context | Disease |
| --- | --- | ---: | --- | --- | --- | --- |
| `CANCER_ATLAS` | `Gavish23` | 41 | binary | human | cancer | cancer |
| `CANCER_ATLAS` | `Yuan18` | 14 | binary | human | cancer | cancer |
| `CCA` | `Serrano23` | 5 | binary | human | cancer | cholangiocarcinoma |
| `CCA` | `Sia13` | 2 | binary | human | cancer | cholangiocarcinoma |
| `CELL_ATLAS` | `PanglaoDB2020` | 163 | binary | human, mouse | physiology | unknown |
| `ECM` | `Helms22` | 1 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Affo21` | 3 | binary | human | cancer | unknown |
| `FIBROBLAST` | `Cords23` | 9 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Dominguez20` | 3 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Elyada19` | 2 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Gao24` | 20 | binary | human | unknown | unknown |
| `FIBROBLAST` | `Grout22` | 3 | binary | human | cancer | unknown |
| `FIBROBLAST` | `Kieffer20` | 8 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Neuzillet22` | 4 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Patrick24` | 11 | binary | mouse | unknown | unknown |
| `FIBROBLAST` | `Peng26` | 2 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Qin23` | 4 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `ReviewLiu26` | 24 | binary | human, mouse | cancer | unknown |
| `FIBROBLAST` | `Wang21` | 6 | binary | human | cancer | unknown |
| `FIBROBLAST` | `Xing21` | 4 | binary | human | cancer | unknown |
| `FIBROBLAST` | `Zhang23` | 8 | binary | human | cancer | PDAC |
| `GASTRIC` | `Bockerstett20` | 15 | binary | human | physiology | normal |
| `GASTRIC` | `Ma21` | 11 | binary | mouse | physiology | normal |
| `GASTRIC_CANCER` | `Kim22` | 7 | binary | human | cancer | gastric_cancer |
| `GASTRIC_CANCER` | `Sathe20` | 3 | binary | human | cancer | gastric_cancer |
| `GI` | `Busslinger21` | 35 | binary | human | physiology | normal |
| `HCC` | `Petitprez19` | 73 | binary | human | cancer | HCC |
| `IBD` | `Nie23` | 96 | binary | human | inflammation | IBD |
| `IMMUNE` | `Becht16` | 10 | binary | human | unknown | unknown |
| `IMMUNE` | `Chu23` | 8 | binary | human | unknown | unknown |
| `IMMUNE` | `Mulder21` | 17 | binary | human | unknown | unknown |
| `IMMUNE` | `Rodrigues18` | 2 | binary | human | unknown | unknown |
| `IMMUNE` | `Wu24` | 10 | binary | human | unknown | unknown |
| `ORGANOID` | `Xu25` | 48 | binary | human | organoid | unknown |
| `PANCREAS` | `Fernandez24` | 23 | binary | mouse | physiology | normal |
| `PANCREAS` | `Schlesinger20` | 14 | binary | mouse | physiology | normal |
| `PDAC` | `Bailey16` | 4 | binary | human | cancer | PDAC |
| `PDAC` | `ChanSengYue20` | 12 | binary | human | cancer | PDAC |
| `PDAC` | `Collisson11` | 3 | binary | human | cancer | PDAC |
| `PDAC` | `GemPred20` | 1 | continuous | human | cancer | PDAC |
| `PDAC` | `Grunwald21` | 2 | binary | human | cancer | PDAC |
| `PDAC` | `Hwang22` | 18 | binary | human | cancer | PDAC |
| `PDAC` | `Maurer18` | 2 | binary | human | cancer | PDAC |
| `PDAC` | `Moffitt15` | 14 | binary | human | cancer | PDAC |
| `PDAC` | `Nicolle17` | 2 | binary | human | cancer | PDAC |
| `PDAC` | `PAMG20` | 4 | continuous | human | cancer | PDAC |
| `PDAC` | `Puleo18` | 10 | binary | human | cancer | PDAC |
| `SINET` | `Patte25` | 4 | binary | human | cancer | siNETs |

<!-- PHENOSIGDB_SIGNATURES_END -->
