# PhenoSigDB Python

Install:

```bash
pip install git+https://github.com/GeNeHetX/phenosigdb.git#subdirectory=packages/python
```

Public API:

- `list_signatures(query=None, reference_species="human", fixed=False)`
- `get_signatures(signature_ids=None, reference_species="human")`
- `phenosigdb_resources(action="list", resource=None, force=False, verbose=True)`
- Constants: `DEFAULT_REFERENCE_SPECIES`, `ALLOWED_REFERENCE_SPECIES`

Examples:

```python
from phenosigdb import (
    get_signatures,
    list_signatures,
    phenosigdb_resources,
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
caf_sigs = list_signatures(r"^FIBROBLAST\.")
pdac_caf = list_signatures("FIBROBLAST", domain="FIBROBLAST", species="human")
pdac_pathways = list_signatures(r"PDAC.*pathway")

# Literal text search (fixed=True)
exact_match = list_signatures("iCAF", fixed=True)

# normal filtering is just pandas filtering
pdac = meta[meta["disease"] == "PDAC"]
pathways = meta[meta["context"] == "pathway"]
continuous = meta[meta["signature_format"] == "continuous"]

# Get signatures
sig = get_signatures(["FIBROBLAST.Elyada19.iCAF"])
sig = get_signatures(list_signatures("FIBROBLAST"))
weighted = get_signatures(["PDAC.PAMG20.PDX"])

mouse_sig = get_signatures(["FIBROBLAST.Elyada19.iCAF"], reference_species="mouse")

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
- Query uses case-insensitive regex by default; set `fixed=True` for literal text matching
- `domain`, `species`, `cell_family`, `context`, `disease`, `source_resource`, and `collection` are exact filters
- Query and filters intersect by default; set `logic="or"` to union them; set `ignore_case=False` for case-sensitive matching

Optional resources:

- `celltypist`
- `cellmarker`
- `msigdb_c7immune`
- `msigdb_c8celltype`
- `pid`
- `biocarta`
- `reactome`
- `wikipathways`
