# PhenoSigDB

PhenoSigDB is a signature database and access library for Python and R, providing gene sets (signatures) for cancer, immune, stromal, and other biological contexts.

## Quick Start

### Python

```bash
# Install
pip install git+https://github.com/GeNeHetX/phenosigdb.git#subdirectory=python
```

```python
from phenosigdb import list_signatures, get_signatures, phenosigdb_resources

# List all available signatures
meta = list_signatures()

# Search signatures (regex by default, case-insensitive)
caf_signatures = list_signatures("CAF")
pathway_signatures = list_signatures("pathway", fixed=False)

# Get a specific signature
sig = get_signatures("CAF.Elyada19.iCAF")

# Install optional resources
phenosigdb_resources("list")
phenosigdb_resources("install", "pid")
```

### R

```r
# Install
remotes::install_github("GeNeHetX/phenosigdb", subdir = "rpkg")
```

```r
library(phenosigdb)

# List all available signatures
meta <- list_signatures()

# Search signatures (regex by default, case-insensitive)
caf_signatures <- list_signatures("CAF")
pathway_signatures <- list_signatures("pathway", fixed = FALSE)

# Get a specific signature
sig <- get_signatures("CAF.Elyada19.iCAF")

# Install optional resources
phenosigdb_resources("list")
phenosigdb_resources("install", "pid")
```

---

## Public API

Both Python and R provide the same three core functions:

### `list_signatures(query=None, reference_species="human", fixed=False)`

List available signatures with metadata.

**Parameters:**
- `query`: Optional search string (regex by default, case-insensitive). Use `fixed=True` for literal text matching.
- `reference_species`: One of `"human"`, `"mouse"`, `"original"`. Selects gene identifier space.
- `fixed`: If `True`, treat query as literal text. If `False` (default), treat as regex.

**Returns:** DataFrame (Python) or data.frame (R) with columns:
- `signature_id`, `signature_name`, `domain`, `source`, `collection`, `source_resource`, `signature_format`, `species`, `cell_family`, `context`, `disease`, `n_genes`

### `get_signatures(signature_ids=None, reference_species="human")`

Retrieve signature gene sets by ID.

**Parameters:**
- `signature_ids`: Signature ID or list of IDs. If `None`, returns all signatures.
- `reference_species`: One of `"human"`, `"mouse"`, `"original"`.

**Returns:**
- Binary signatures: `list[str]` (Python) or `character` vector (R) of gene symbols
- Continuous signatures: `dict[str, float]` (Python) or named `numeric` vector (R) of gene->weight

### `phenosigdb_resources(action="list", resource=None, force=False, verbose=True)`

Manage optional resources.

**Parameters:**
- `action`: One of `"list"`, `"install"`, `"remove"`, `"update"`, `"path"`
- `resource`: Resource name (see below). If `None` with `action="install"`, installs all missing.
- `force`: If `True`, reinstall existing resources.
- `verbose`: If `True`, print progress messages.

**Returns:** Path string for `"path"`, DataFrame/data.frame for other actions.

---

## Metadata Columns

| Column | Description |
|--------|-------------|
| `signature_id` | Unique identifier (e.g., `CAF.Elyada19.iCAF`) |
| `signature_name` | Human-readable name (e.g., `iCAF`) |
| `domain` | Broad category (e.g., `CAF`, `PDAC`, `IMMUNE`) |
| `source` | Source paper/key (e.g., `Elyada19`) |
| `collection` | Subgroup (e.g., `curated`) |
| `source_resource` | Data origin: `curated`, `celltypist`, `cellmarker`, `msigdb`, `reactome`, `wikipathways` |
| `signature_format` | `binary` (gene set) or `continuous` (weighted) |
| `species` | Species (human/mouse) |
| `cell_family` | Cell type family (e.g., `fibroblast`, `tumor`) |
| `context` | Biological context (e.g., `cancer`, `pathway`) |
| `disease` | Disease association (e.g., `PDAC`, `HCC`) |
| `n_genes` | Number of genes in signature |

---

## Curated Signatures (Core)

The core curated signatures are organized by domain. The curated collection (`source_resource = "curated"`) includes:

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
| `pid` | `MSIGDB.PID.*` | binary | MSigDB PID: Pathway gene sets |
| `biocarta` | `MSIGDB.BIOCARTA.*` | binary | MSigDB BioCarta: Pathway gene sets |
| `reactome` | `REACTOME.PATHWAYS.*` | binary | Reactome pathway gene sets |
| `wikipathways` | `WIKIPATHWAYS.HOMOSAPIENS.*` | binary | WikiPathways human pathway gene sets |

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

- **Default**: Regex search (case-insensitive)
- **Literal text**: Set `fixed=True` (Python) or `fixed=TRUE` (R)
- **Searched columns**: All metadata columns except `n_genes`
- **Examples**:
  - `list_signatures("^CAF\.")` - All CAF signatures
  - `list_signatures("PDAC.*pathway")` - PDAC pathway signatures
  - `list_signatures("immune", fixed=True)` - Exact match on "immune"

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

## License

MIT License. See [LICENSE](LICENSE) for details.
