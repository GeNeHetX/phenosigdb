# PhenoSigDB Python

Install:

```bash
pip install git+https://github.com/GeNeHetX/phenosigdb.git#subdirectory=python
```

Public API:

- `list_signatures(query=None, reference_species="human", fixed=False)`
- `get_signatures(signature_ids=None, reference_species="human")`
- `phenosigdb_resources(action="list", resource=None, force=False, verbose=True)`
- `phenosigdb_version()`
- Constants: `DEFAULT_REFERENCE_SPECIES`, `ALLOWED_REFERENCE_SPECIES`

Examples:

```python
from phenosigdb import (
    get_signatures,
    list_signatures,
    phenosigdb_resources,
    phenosigdb_version,
    ALLOWED_REFERENCE_SPECIES,
)

# List all signatures
meta = list_signatures()

# Query behavior (regex by default, case-insensitive):
# Searches: signature_id, signature_name, domain, source, collection,
# source_resource, signature_format, species, cell_family, context, disease
# Does NOT search: n_genes

# Regex search (default - fixed=False)
immune = list_signatures("immune")
caf_sigs = list_signatures(r"^CAF\.")
pdac_pathways = list_signatures(r"PDAC.*pathway")

# Literal text search (fixed=True)
exact_match = list_signatures("iCAF", fixed=True)

# normal filtering is just pandas filtering
pdac = meta[meta["disease"] == "PDAC"]
pathways = meta[meta["context"] == "pathway"]
continuous = meta[meta["signature_format"] == "continuous"]

# Get signatures
sig = get_signatures(["CAF.Elyada19.iCAF"])
weighted = get_signatures(["PDAC.PAMG20.PDX"])

mouse_sig = get_signatures(["CAF.Elyada19.iCAF"], reference_species="mouse")

# Version info
print(phenosigdb_version())
print(ALLOWED_REFERENCE_SPECIES)  # {'human', 'mouse', 'original'}

# Resource management
phenosigdb_resources("list")
phenosigdb_resources("install", "celltypist")
phenosigdb_resources("install", "msigdb_c8celltype")
cache_path = phenosigdb_resources("path")
```

Return shapes:

- binary signature -> `list[str]`
- continuous signature -> `dict[str, float]`
- outer container -> `dict[signature_id, signature]`

Notes:

- default reference is human (`DEFAULT_REFERENCE_SPECIES`)
- no path argument is needed
- curated reference parquet downloads automatically on first use
- `get_signatures()` auto-installs missing optional resources
- Query uses regex by default; set `fixed=True` for literal text matching
- All query matching is case-insensitive

Optional resources:

- `celltypist`
- `cellmarker`
- `msigdb_c7immune`
- `msigdb_c8celltype`
- `pid`
- `biocarta`
- `reactome`
- `wikipathways`
