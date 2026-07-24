# PhenoSigDB Python

Install:

```bash
pip install git+https://github.com/GeNeHetX/phenosigdb.git#subdirectory=packages/python
```

Public API:

- `list_signatures(query=None, columns=None, min_genes=None, signature_format=None)`
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

# Case-insensitive regex search across the default metadata columns
immune = list_signatures("immune")
source_slice = list_signatures("MSigDB.C8")
metabolism = list_signatures("metabolism", columns=["signature_name", "context"])

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
- Query is a case-insensitive regex across `signature_id`, `signature_name`, `source`, `domain`, `cell_family`, `context`, and `disease`
- `columns` selects a smaller search set; `min_genes` and `signature_format` are optional filters

Optional resources:

- `celltypist`
- `cellmarker`
- `msigdb_c7immune`
- `msigdb_c8celltype`
- `pid`
- `biocarta`
- `reactome`
- `wikipathways`
