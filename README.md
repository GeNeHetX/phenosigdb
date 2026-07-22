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
# remotes::install_url("https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.10/phenosigdb_0.1.10.tar.gz")
```

## Quick Start

### Python
```python
from phenosigdb import list_signatures, get_signatures, get_signature, phenosigdb_resources

# List all available signatures
meta = list_signatures()

# Search signatures (regex by default, case-insensitive)
caf_signatures = list_signatures("CAF")

# Get a specific signature
sig = get_signatures("CAF.Elyada19.iCAF")
sig = get_signatures(list_signatures("CAF"))
one_sig = get_signature("CAF.Elyada19.iCAF")

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
- `domain`, `species`, `cell_family`, `context`, `disease`, `source_resource`, `collection`: Exact column filters
- `logic`: `"and"` (default) or `"or"` for combining query and filters
- `ignore_case`: `True` (default) or `False`

**Returns:** DataFrame with signature metadata.

### `get_signatures(signature_ids=None, reference_species="human")`
Retrieve signature gene sets. If an ID belongs to an optional resource that is not installed, that resource is downloaded automatically.

**Parameters:**
- `signature_ids`: Signature ID, list of IDs, or `None` (all signatures)
- `reference_species`: Species filter

**Returns:** Dict mapping signature_id → gene list (binary) or gene→weight dict (continuous).

`signature_ids` also accepts the table returned by `list_signatures()`.

### `get_signature(signature_id, reference_species="human")`
Return one signature directly.

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
| `collection` | Subgroup (e.g., `curated`) |
| `source_resource` | Runtime origin: `core`, `celltypist`, `cellmarker`, `msigdb`, `pid`, `biocarta`, `reactome`, `wikipathways` |
| `species` | Species (human/mouse) |
| `cell_family` | Cell type family (e.g., `fibroblast`, `tumor`) |
| `context` | Biological context (e.g., `cancer`, `pathway`) |
| `disease` | Disease association (e.g., `PDAC`, `HCC`) |
| `n_genes` | Number of genes in signature |

`source_resource` answers “where did this data come from?” (`core`, `celltypist`, `msigdb`, etc.). `collection` answers “which subgroup within that source?” (`curated`, `C7`, `C8`, `PID`, etc.).

## Query Behavior

- **Default**: Regex search, case-insensitive
- **Literal text**: Set `fixed=True` (Python) or `fixed=TRUE` (R)
- **Searched columns**: All metadata columns except `n_genes`
- **Examples**: `"^CAF\."` (starts with CAF.), `"pathway"` (contains pathway)
- **Remember**: Escape dots in regex: `\.` for literal dots

## Curated Signatures

Organized by domain. Bundled signatures have `source_resource = "core"` and `collection = "curated"`.

- **CAF**: Multiple PDAC CAF subtypes (iCAF, myoCAF, etc.) from Elyada19, Dominguez20, Kieffer20, etc.
- **PDAC**: Tumor, stromal, immune signatures from Bailey16, Moffitt15, Collisson11, etc.
- **IMMUNE**: Immune cell type signatures from Becht16, Chu23, Mulder21, Rodrigues18, Wu24
- **Other**: GASTRIC, HCC, ORGANOID, CCA, etc.

For bundled signatures: `list_signatures()` then filter by `source_resource == "core"` or `collection == "curated"`.

## Optional Resources

Install optional resources once when needed:

```r
phenosigdb_resources("install")
```

They remain available after package upgrades. `get_signatures()` installs a missing resource automatically. Use `phenosigdb_resources("update")` to refresh them.

```python
from phenosigdb import phenosigdb_version
print(phenosigdb_version())
```

```r
phenosigdb_version()
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.

<!-- PHENOSIGDB_SIGNATURES_START -->

## Available Signatures

Core curated signatures: **785** across **48** curated source keys.

| Domain | SourceKey | Signatures | Format | Species | Context | Disease |
| --- | --- | ---: | --- | --- | --- | --- |
| `CAF` | `Affo21` | 3 | binary | human | cancer | unknown |
| `CAF` | `Cords23` | 9 | binary | human | cancer | PDAC |
| `CAF` | `Dominguez20` | 3 | binary | human | cancer | PDAC |
| `CAF` | `Elyada19` | 2 | binary | human | cancer | PDAC |
| `CAF` | `Grout22` | 3 | binary | human | cancer | unknown |
| `CAF` | `Kieffer20` | 8 | binary | human | cancer | PDAC |
| `CAF` | `Neuzillet22` | 4 | binary | human | cancer | PDAC |
| `CAF` | `Peng26` | 2 | binary | human | cancer | PDAC |
| `CAF` | `Qin23` | 4 | binary | human | cancer | PDAC |
| `CAF` | `ReviewLiu26` | 24 | binary | human, mouse | cancer | unknown |
| `CAF` | `Wang21` | 6 | binary | human | cancer | unknown |
| `CAF` | `Xing21` | 4 | binary | human | cancer | unknown |
| `CAF` | `Zhang23` | 8 | binary | human | cancer | PDAC |
| `CANCERSEA` | `Yuan18` | 14 | binary | human | cancer | cancer |
| `CCA` | `Serrano23` | 5 | binary | human | cancer | cholangiocarcinoma |
| `CCA` | `Sia13` | 2 | binary | human | cancer | cholangiocarcinoma |
| `CELL` | `PanglaoDB2020` | 163 | binary | human, mouse | physiology | unknown |
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

<!-- PHENOSIGDB_SIGNATURES_END -->
