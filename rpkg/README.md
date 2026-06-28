# PhenoSigDB R

Install:

```r
remotes::install_github("GeNeHetX/phenosigdb", subdir = "rpkg")
```

Public API:

- `list_signatures(query = NULL, reference_species = "human", fixed = FALSE)`
- `get_signatures(signature_ids = NULL, reference_species = "human")`
- `phenosigdb_resources(action = "list", resource = NULL, force = FALSE, verbose = TRUE)`
- `phenosigdb_version()`

Examples:

```r
library(phenosigdb)

# List all signatures
meta <- list_signatures()

# Query behavior (regex by default, case-insensitive):
# Searches: signature_id, signature_name, domain, source, collection,
# source_resource, signature_format, species, cell_family, context, disease
# Does NOT search: n_genes

# Regex search (default - fixed = FALSE)
immune <- list_signatures("immune")
caf_sigs <- list_signatures("^CAF\\.")
pdac_pathways <- list_signatures("PDAC.*pathway")

# Literal text search (fixed = TRUE)
exact_match <- list_signatures("iCAF", fixed = TRUE)

# normal filtering is just data.frame filtering
pdac <- meta[meta$disease == "PDAC", ]
pathways <- meta[meta$context == "pathway", ]
continuous <- meta[meta$signature_format == "continuous", ]

# Get signatures
sig <- get_signatures("CAF.Elyada19.iCAF")
weighted <- get_signatures("PDAC.PAMG20.PDX")

mouse_sig <- get_signatures("CAF.Elyada19.iCAF", reference_species = "mouse")

# Version info
phenosigdb_version()

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
- `get_signatures()` auto-installs missing optional resources
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
