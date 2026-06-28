# PhenoSigDB

PhenoSigDB is a signature database and access library for Python and R, providing gene sets (signatures) for cancer, immune, stromal, and other biological contexts.

## Installation

### Python
```bash
pip install git+https://github.com/GeNeHetX/phenosigdb.git#subdirectory=python
```

### R
```r
remotes::install_github("GeNeHetX/phenosigdb", subdir = "rpkg")
```

## Quick Start

### Python
```python
from phenosigdb import list_signatures, get_signatures, phenosigdb_resources

# List all available signatures
meta = list_signatures()

# Search signatures (regex by default, case-insensitive)
caf_signatures = list_signatures("CAF")

# Get a specific signature
sig = get_signatures("CAF.Elyada19.iCAF")

# Install optional resources
phenosigdb_resources("install", "pid")
```

### R
```r
library(phenosigdb)

# List all available signatures  
meta <- list_signatures()

# Search signatures (regex by default, case-insensitive)
caf_signatures <- list_signatures("CAF")

# Get a specific signature
sig <- get_signatures("CAF.Elyada19.iCAF")

# Install optional resources
phenosigdb_resources("install", "pid")
```

## Public API

### `list_signatures(query=None, reference_species="human", fixed=False)`
List signatures with metadata. **Default: regex search, case-insensitive.** Use `fixed=True` for literal text.

**Parameters:**
- `query`: Optional search string (all metadata columns except `n_genes`)
- `reference_species`: `"human"` (default), `"mouse"`, or `"original"`
- `fixed`: If `True`, literal text matching

**Returns:** DataFrame with signature metadata.

### `get_signatures(signature_ids=None, reference_species="human")`
Retrieve signature gene sets. **Auto-installs missing optional resources.**

**Parameters:**
- `signature_ids`: Signature ID, list of IDs, or `None` (all signatures)
- `reference_species`: Species filter

**Returns:** Dict mapping signature_id → gene list (binary) or gene→weight dict (continuous).

### `phenosigdb_resources(action, resource=None, force=False, verbose=True)`
Manage optional resources.

**Parameters:**
- `action`: `"list"`, `"install"`, `"remove"`, `"update"`, `"path"`
- `resource`: Resource name (optional for list/install all)
- `force`: Reinstall existing resources
- `verbose`: Print progress messages

**Returns:** Path string ("path") or DataFrame with resource status.

### `phenosigdb_version()`
Return package version string.

## Metadata Columns

| Column | Description |
|--------|-------------|
| `signature_id` | Unique identifier (e.g., `CAF.Elyada19.iCAF`) |
| `signature_name` | Human-readable name (e.g., `iCAF`) |
| `domain` | Broad category (e.g., `CAF`, `PDAC`, `IMMUNE`) |
| `source` | Source paper/key (e.g., `Elyada19`) |
| `collection` | Subgroup (e.g., `curated`) |
| `source_resource` | Data origin: `curated`, `celltypist`, `cellmarker`, `msigdb`, `pid`, `biocarta`, `reactome`, `wikipathways` |
| `signature_format` | `binary` (gene set) or `continuous` (weighted) |
| `species` | Species (human/mouse) |
| `cell_family` | Cell type family (e.g., `fibroblast`, `tumor`) |
| `context` | Biological context (e.g., `cancer`, `pathway`) |
| `disease` | Disease association (e.g., `PDAC`, `HCC`) |
| `n_genes` | Number of genes in signature |

## Query Behavior

- **Default**: Regex search, case-insensitive
- **Literal text**: Set `fixed=True` (Python) or `fixed=TRUE` (R)
- **Searched columns**: All metadata columns except `n_genes`
- **Examples**: `"^CAF\."` (starts with CAF.), `"pathway"` (contains pathway)
- **Remember**: Escape dots in regex: `\.` for literal dots

## Curated Signatures

Organized by domain. All have `source_resource = "curated"`.

- **CAF**: Multiple PDAC CAF subtypes (iCAF, myoCAF, etc.) from Elyada19, Dominguez20, Kieffer20, etc.
- **PDAC**: Tumor, stromal, immune signatures from Bailey16, Moffitt15, Collisson11, etc.
- **IMMUNE**: Immune cell type signatures from Becht16, Chu23, Mulder21, Rodrigues18, Wu24
- **Other**: GASTRIC, HCC, ORGANOID, CCA, etc.

For complete list: `list_signatures()` then filter by `source_resource == "curated"`.

## Optional Resources

Install on-demand. `get_signatures()` auto-installs as needed.

| Resource | ID Prefix | Format | Description |
|----------|-----------|--------|-------------|
| `celltypist` | `CELLTYPIST.*` | continuous | Cell type signatures from CellTypist |
| `cellmarker` | `CELLMARKER.*` | binary | Cell marker gene sets |
| `msigdb_c7immune` | `MSIGDB.C7.*` | binary | MSigDB C7: Immunology gene sets |
| `msigdb_c8celltype` | `MSIGDB.C8.*` | binary | MSigDB C8: Cell type gene sets |
| `pid` | `PID.*` | binary | PID pathway gene sets |
| `biocarta` | `BIOCARTA.*` | binary | BioCarta pathway gene sets |
| `reactome` | `REACTOME.PATHWAYS.*` | binary | Reactome pathway gene sets |
| `wikipathways` | `WIKIPATHWAYS.*` | binary | WikiPathways pathway gene sets |

## Versioning

- Curated signatures: Versioned with repository releases
- Optional resources: Pinned to specific versions
- Installed resources: Local manifests record version, install time, checksum

```python
from phenosigdb import phenosigdb_version
print(phenosigdb_version())
```

```r
phenosigdb_version()
```

## Repository Layout

- `python/`: Python library
- `rpkg/`: R package  
- `signatures/`: Maintainer tools and reference data

Maintainer documentation: [signatures/README.md](signatures/README.md)

---

## License

MIT License. See [LICENSE](LICENSE) for details.

<!-- PHENOSIGDB_SIGNATURES_START -->

## Available Signatures

Core curated signatures: **606** across **45** curated source keys.

| Domain | SourceKey | Signatures | Format | Species | Context | Disease |
| --- | --- | ---: | --- | --- | --- | --- |
| `CAF` | `Affo21` | 3 | binary | human | cancer | unknown |
| `CAF` | `Cords23` | 9 | binary | human | cancer | PDAC |
| `CAF` | `Dominguez20` | 3 | binary | human | cancer | PDAC |
| `CAF` | `Elyada19` | 2 | binary | human | cancer | PDAC |
| `CAF` | `Grout22` | 3 | binary | human | cancer | unknown |
| `CAF` | `Kieffer20` | 8 | binary | human | cancer | PDAC |
| `CAF` | `Neuzillet22` | 4 | binary | human | cancer | PDAC |
| `CAF` | `Qin23` | 4 | binary | human | cancer | PDAC |
| `CAF` | `ReviewLiu26` | 24 | binary | human, mouse | cancer | unknown |
| `CAF` | `Wang21` | 6 | binary | human | cancer | unknown |
| `CAF` | `Xing21` | 4 | binary | human | cancer | unknown |
| `CAF` | `Zhang23` | 8 | binary | human | cancer | PDAC |
| `CCA` | `Serrano23` | 5 | binary | human | cancer | cholangiocarcinoma |
| `CCA` | `Sia13` | 2 | binary | human | cancer | cholangiocarcinoma |
| `ECM` | `Helms22` | 1 | binary | human | cancer | PDAC |
| `FIBROBLAST` | `Gao24` | 20 | binary | human | unknown | unknown |
| `FIBROBLAST` | `Patrick24` | 11 | binary | mouse | unknown | unknown |
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
| `PAN_CANCER` | `Gavish23` | 41 | binary | human | cancer | cancer |
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

Optional downloadable references available through `phenosigdb_resources()`: **8**.

| Resource | Source Resource | Collection | Prefix | Format | Context |
| --- | --- | --- | --- | --- | --- |
| `celltypist` | `celltypist` | `reference_models` | `CELLTYPIST.*` | continuous | cell_type |
| `cellmarker` | `cellmarker` | `cell_markers` | `CELLMARKER.*` | binary | cell_type |
| `msigdb_c7immune` | `msigdb` | `C7` | `MSIGDB.C7.*` | binary | immunology |
| `msigdb_c8celltype` | `msigdb` | `C8` | `MSIGDB.C8.*` | binary | cell_type |
| `pid` | `pid` | `PID` | `PID.*` | binary | pathway |
| `biocarta` | `biocarta` | `BIOCARTA` | `BIOCARTA.*` | binary | pathway |
| `reactome` | `reactome` | `ReactomePathways` | `REACTOME.PATHWAYS.*` | binary | pathway |
| `wikipathways` | `wikipathways` | `WikiPathways` | `WIKIPATHWAYS.*` | binary | pathway |

<!-- PHENOSIGDB_SIGNATURES_END -->