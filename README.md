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

---

## Quick Start

### Python

```python
from phenosigdb import list_signatures, get_signatures, phenosigdb_resources, phenosigdb_version

# List all available signatures
meta = list_signatures()
print(f"Found {len(meta)} signatures")

# Search signatures (regex by default, case-insensitive)
caf_signatures = list_signatures("CAF")
pathway_signatures = list_signatures("pathway")

# Get a specific signature by ID
sig = get_signatures("CAF.Elyada19.iCAF")

# Get multiple signatures
signatures = get_signatures(["CAF.Elyada19.iCAF", "CAF.Elyada19.myCAF"])

# List installed optional resources
resources = phenosigdb_resources("list")
print(resources)

# Install a specific optional resource
phenosigdb_resources("install", "pid")

# Get cache directory path
cache_path = phenosigdb_resources("path")
print(f"Cache directory: {cache_path}")

# Check version
print(f"PhenoSigDB version: {phenosigdb_version()}")
```

### R

```r
library(phenosigdb)

# List all available signatures
meta <- list_signatures()
print(paste("Found", nrow(meta), "signatures"))

# Search signatures (regex by default, case-insensitive)
caf_signatures <- list_signatures("CAF")
pathway_signatures <- list_signatures("pathway")

# Get a specific signature by ID
sig <- get_signatures("CAF.Elyada19.iCAF")

# Get multiple signatures
signatures <- get_signatures(c("CAF.Elyada19.iCAF", "CAF.Elyada19.myCAF"))

# List installed optional resources
resources <- phenosigdb_resources("list")
print(resources)

# Install a specific optional resource
phenosigdb_resources("install", "pid")

# Get cache directory path
cache_path <- phenosigdb_resources("path")
print(paste("Cache directory:", cache_path))

# Check version
print(paste("PhenoSigDB version:", phenosigdb_version()))
```

---

## Public API

Both Python and R provide the same three main functions with identical behavior:

### `list_signatures(query=None, reference_species="human", fixed=False)`

List available signatures with metadata. Search is case-insensitive by default.

**Parameters:**
- `query`: Optional search string. **Default behavior: regex search, case-insensitive.** Use `fixed=True` for literal text matching.
- `reference_species`: One of `"human"`, `"mouse"`, `"original"`. Filters signatures by species:
  - `"human"`: Returns signatures with human gene identifiers (default)
  - `"mouse"`: Returns signatures with mouse gene identifiers  
  - `"original"`: Returns signatures in their original species without translation
- `fixed`: If `True`, treats query as literal text. If `False` (default), treats as regex.

**Search behavior:**
- Searches all metadata columns **except** `n_genes`
- Columns searched: `signature_id`, `signature_name`, `domain`, `source`, `collection`, `source_resource`, `signature_format`, `species`, `cell_family`, `context`, `disease`
- Case-insensitive matching is always applied
- Regex syntax supported when `fixed=False`

**Returns:** DataFrame (Python) or data.frame (R) with columns:
- `signature_id`, `signature_name`, `domain`, `source`, `collection`, `source_resource`, `signature_format`, `species`, `cell_family`, `context`, `disease`, `n_genes`

**Examples:**
```python
# Find all CAF signatures
caf_sigs = list_signatures("^CAF\.")

# Find signatures containing "pathway" (case-insensitive)
pathway_sigs = list_signatures("pathway")

# Exact text match (not regex)
exact_sigs = list_signatures("immune", fixed=True)
```

### `get_signatures(signature_ids=None, reference_species="human")`

Retrieve signature gene sets by ID. Automatically installs required optional resources.

**Parameters:**
- `signature_ids`: Signature ID, list of IDs, or `None`. If `None`, returns all signatures.
- `reference_species`: One of `"human"`, `"mouse"`, `"original"`. Species filtering for the returned signatures.

**Returns:**
- Binary signatures: `list[str]` (Python) or `character` vector (R) of gene symbols
- Continuous signatures: `dict[str, float]` (Python) or named `numeric` vector (R) of gene->weight

**Auto-install behavior:** If requested signature IDs belong to optional resources that aren't installed, they will be automatically downloaded and installed.

### `phenosigdb_resources(action="list", resource=None, force=False, verbose=True)`

Manage optional resources.

**Parameters:**
- `action`: One of `"list"`, `"install"`, `"remove"`, `"update"`, `"path"`
- `resource`: Resource name. If `None` with `action="install"`, installs all missing resources.
- `force`: If `True`, reinstall existing resources even if already installed.
- `verbose`: If `True`, print progress messages.

**Returns:** 
- `"path"`: Path string to the cache directory
- Other actions: DataFrame/data.frame with resource status information

### `phenosigdb_version()`

Return the PhenoSigDB package version string.

---

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

---

## Curated Signatures

The curated signatures are organized by domain. All curated signatures have `source_resource = "curated"` and include:

### CAF (Cancer-Associated Fibroblast) Signatures
- Multiple PDAC CAF subtypes (iCAF, myoCAF, etc.) from Elyada19, Dominguez20, Kieffer20, and others

### PDAC (Pancreatic Ductal Adenocarcinoma) Signatures
- Tumor, stromal, immune signatures from Bailey16, Moffitt15, Collisson11, Puleo18, and others
- Molecular subtypes and gene expression models

### Immune Signatures
- Immune cell type signatures from Becht16, Chu23, Mulder21, Rodrigues18, Wu24

### Other Cancer Types
- GASTRIC, GASTRIC_CANCER, HCC, PANCREAS, PAN_CANCER, ORGANOID, CCA, GI, SINET, ECM

### Additional
- CANCERSEA signatures
- Fibroblast signatures from Patrick24, Gao24

For a complete list, run `list_signatures()` and filter by `source_resource == "curated"`.

---

## Optional Resources

Optional resources provide additional signature collections. Each can be installed on-demand:

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

**Installation:**
```python
# Python
phenosigdb_resources("install", "pid")  # Install single resource
phenosigdb_resources("install")        # Install all missing
```

```r
# R
phenosigdb_resources("install", "pid")  # Install single resource
phenosigdb_resources("install")        # Install all missing
```

**Auto-install:** `get_signatures()` automatically installs any optional resource needed to fulfill the requested signature IDs.

---

## Query Behavior

### Search Features
- **Default behavior**: Regex search with case-insensitive matching
- **Literal text matching**: Set `fixed=True` (Python) or `fixed=TRUE` (R)
- **Searched columns**: All metadata columns **except** `n_genes`
- **Case sensitivity**: Always case-insensitive, regardless of regex or fixed mode

### Examples

```python
# Regex search (default) - find all CAF signatures
caf_sigs = list_signatures("^CAF\.")

# Regex search - find signatures with pathway in any metadata field
pathway_sigs = list_signatures("pathway")

# Literal text search - exact match on "immune"
immune_sigs = list_signatures("immune", fixed=True)

# Find signatures from specific domains
pdac_sigs = list_signatures("^PDAC\.")
immune_sigs = list_signatures("^IMMUNE\.")
```

```r
# Same behavior in R
caf_sigs <- list_signatures("^CAF\.")
pathway_sigs <- list_signatures("pathway")
immune_sigs <- list_signatures("immune", fixed = TRUE)
```

### Regular Expression Support
- Full regex syntax supported when `fixed=False` (default)
- Common patterns: `^pattern` (starts with), `pattern$` (ends with), `.*` (any characters)
- Remember to escape dots: `\.` to match literal dots in signature IDs

---

## Versioning

- Core curated signatures: Versioned with repository releases
- Optional resources: Pinned to specific versions (MSigDB 2025.1.Hs, Reactome current, WikiPathways current)
- Installed resources: Local manifests record version, install time, and checksum

```python
# Python
from phenosigdb import phenosigdb_version
print(phenosigdb_version())  # e.g., "0.1.0"
```

```r
# R
phenosigdb_version()  # e.g., "0.1.0"
```

---

## Repository Layout

- `python/`: Python library
- `rpkg/`: R package
- `signatures/`: Maintainer tools, curation, build system, and reference data

Maintainer documentation: [signatures/README.md](signatures/README.md)

---

## Complete Function Reference

### User-Facing Functions (Python and R)

#### 1. `list_signatures(query=None, reference_species="human", fixed=False)`

**Purpose:** List available signatures with metadata

**Parameters:**
- `query` (str, optional): Search string. Default: None (returns all signatures)
  - When `fixed=False` (default): Regex pattern, case-insensitive
  - When `fixed=True`: Literal text, case-insensitive
- `reference_species` (str): Species filter. One of: `"human"`, `"mouse"`, `"original"`
  - `"human"`: Returns signatures with human gene identifiers (default)
  - `"mouse"`: Returns signatures with mouse gene identifiers
  - `"original"`: Returns signatures in their original species without translation
- `fixed` (bool): Search mode. Default: False (regex search)

**Returns:** DataFrame/data.frame with columns:
- `signature_id`: Unique identifier (e.g., "CAF.Elyada19.iCAF")
- `signature_name`: Human-readable name (e.g., "iCAF")
- `domain`: Broad category (e.g., "CAF", "PDAC", "IMMUNE")
- `source`: Source paper/key (e.g., "Elyada19")
- `collection`: Subgroup (e.g., "curated")
- `source_resource`: Data origin (e.g., "curated", "pid", "biocarta", "reactome")
- `signature_format`: Format type ("binary" or "continuous")
- `species`: Species identifier
- `cell_family`: Cell type family (e.g., "fibroblast", "tumor")
- `context`: Biological context (e.g., "cancer", "pathway")
- `disease`: Disease association (e.g., "PDAC", "HCC")
- `n_genes`: Number of genes in signature

**Search Behavior:**
- Searches all columns **except** `n_genes`
- Case-insensitive matching is always applied
- Regex syntax supported when `fixed=False`
- Examples: `"^CAF\."` (starts with CAF.), `"pathway"` (contains pathway anywhere)

---

#### 2. `get_signatures(signature_ids=None, reference_species="human")`

**Purpose:** Retrieve signature gene sets by ID

**Parameters:**
- `signature_ids` (str, list, or None): Signature ID(s) to retrieve
  - If string: Single signature ID
  - If list/array: Multiple signature IDs
  - If None: Returns all signatures
- `reference_species` (str): Species filter. One of: `"human"`, `"mouse"`, `"original"`

**Returns:** Dictionary/named list mapping signature_id to gene data:
- Binary signatures: `list[str]` (Python) or `character` vector (R) of gene symbols
- Continuous signatures: `dict[str, float]` (Python) or named `numeric` vector (R) of gene->weight

**Auto-install:** If requested signature IDs belong to optional resources that aren't installed, they will be automatically downloaded and installed.

**Examples:**
```python
# Get single signature
sig = get_signatures("CAF.Elyada19.iCAF")

# Get multiple signatures
sigs = get_signatures(["CAF.Elyada19.iCAF", "CAF.Elyada19.myCAF"])

# Get all signatures
all_sigs = get_signatures()
```

---

#### 3. `phenosigdb_resources(action="list", resource=None, force=False, verbose=True)`

**Purpose:** Manage optional resources

**Parameters:**
- `action` (str): Action to perform. One of: `"list"`, `"install"`, `"remove"`, `"update"`, `"path"`
- `resource` (str, optional): Resource name. If None with `action="install"`, installs all missing
- `force` (bool): If True, reinstall existing resources. Default: False
- `verbose` (bool): If True, print progress messages. Default: True

**Available Resources:**
- `celltypist`: Cell type signatures (continuous format)
- `cellmarker`: Cell marker gene sets (binary format)
- `msigdb_c7immune`: MSigDB C7 immunology gene sets (binary)
- `msigdb_c8celltype`: MSigDB C8 cell type gene sets (binary)
- `pid`: PID pathway gene sets (binary)
- `biocarta`: BioCarta pathway gene sets (binary)
- `reactome`: Reactome pathway gene sets (binary)
- `wikipathways`: WikiPathways pathway gene sets (binary)

**Returns:**
- `action="path"`: Path string to the cache directory
- Other actions: DataFrame/data.frame with resource status information

**Examples:**
```python
# List all available resources and their status
resources = phenosigdb_resources("list")

# Install a specific resource
phenosigdb_resources("install", "pid")

# Install all missing resources
phenosigdb_resources("install")

# Update existing resources
phenosigdb_resources("update")

# Remove a resource
phenosigdb_resources("remove", "pid")

# Get cache directory path
cache_path = phenosigdb_resources("path")
```

---

#### 4. `phenosigdb_version()`

**Purpose:** Return the PhenoSigDB package version string

**Parameters:** None

**Returns:** String with version number (e.g., "0.1.2")

**Examples:**
```python
version = phenosigdb_version()
print(f"PhenoSigDB version: {version}")
```

---

## Signature ID Prefixes and Resource Mapping

| Resource | Signature ID Prefix | Resource Name | Auto-install Trigger |
|----------|---------------------|---------------|---------------------|
| Curated | Various (e.g., `CAF.*`, `PDAC.*`, `IMMUNE.*`) | `curated` | Built-in |
| CellTypist | `CELLTYPIST.*` | `celltypist` | `CELLTYPIST.*` |
| CellMarker | `CELLMARKER.*` | `cellmarker` | `CELLMARKER.*` |
| MSigDB C7 | `MSIGDB.C7.*` | `msigdb_c7immune` | `MSIGDB.C7.*` |
| MSigDB C8 | `MSIGDB.C8.*` | `msigdb_c8celltype` | `MSIGDB.C8.*` |
| PID | `PID.*` | `pid` | `PID.*` |
| BioCarta | `BIOCARTA.*` | `biocarta` | `BIOCARTA.*` |
| Reactome | `REACTOME.PATHWAYS.*` | `reactome` | `REACTOME.PATHWAYS.*` |
| WikiPathways | `WIKIPATHWAYS.*` | `wikipathways` | `WIKIPATHWAYS.*` |

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
