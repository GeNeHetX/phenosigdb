# PhenoSigDB R

Install:

```r
remotes::install_url(
  "https://github.com/GeNeHetX/phenosigdb/releases/latest/download/phenosigdb-r.tar.gz"
)

# Reproducible release:
# remotes::install_url("https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.16/phenosigdb_0.1.16.tar.gz")
```

Public API:

- `list_signatures(query = NULL, reference_species = "human", fixed = FALSE)`
- `get_signatures(signature_ids = NULL, reference_species = "human")`
- `phenosigdb_resources(action = "list", resource = NULL, force = FALSE, verbose = TRUE)`

Examples:

```r
library(phenosigdb)

# List all signatures
meta <- list_signatures()
caf <- list_signatures("FIBROBLAST", domain = "FIBROBLAST", species = "human")
sig <- get_signatures(caf)

# Query behavior (regex by default, case-insensitive):
# Searches: signature_id, signature_name, domain, source, collection,
# source_resource, signature_format, species, cell_family, context, disease
# Does NOT search: n_genes

# Regex search (default - fixed = FALSE)
immune <- list_signatures("immune")
caf_sigs <- list_signatures("^FIBROBLAST\\.")
pdac_pathways <- list_signatures("PDAC.*pathway")

# Literal text search (fixed = TRUE)
exact_match <- list_signatures("iCAF", fixed = TRUE)

# normal filtering is just data.frame filtering
pdac <- meta[meta$disease == "PDAC", ]
pathways <- meta[meta$context == "pathway", ]
continuous <- meta[meta$signature_format == "continuous", ]

# Get signatures
sig <- get_signatures("FIBROBLAST.Elyada19.iCAF")
weighted <- get_signatures("PDAC.PAMG20.PDX")

mouse_sig <- get_signatures("FIBROBLAST.Elyada19.iCAF", reference_species = "mouse")

# Resource management
phenosigdb_resources("list")
phenosigdb_resources("install", "celltypist")
phenosigdb_resources("install", "msigdb_c8celltype")
cache_path <- phenosigdb_resources("path")
```

Return shapes:

- binary signature -> character vector
- continuous signature -> named numeric vector
- outer container -> named list

Notes:

- default reference is human
- no path argument is needed
- curated reference parquet downloads automatically on first use
- `get_signatures()` downloads only the missing optional resource required by a requested ID
- Optional resources persist in the user cache across package upgrades
- `phenosigdb_resources("update")` explicitly refreshes installed resources
- `domain`, `species`, `cell_family`, `context`, `disease`, `source_resource`, and `collection` are exact filters
- Query and filters intersect by default; use `logic = "or"` to union them
- Query uses regex by default; set `fixed = TRUE` for literal text matching
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
