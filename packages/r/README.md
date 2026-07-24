# PhenoSigDB R

Install:

```r
remotes::install_url(
  "https://github.com/GeNeHetX/phenosigdb/releases/latest/download/phenosigdb-r.tar.gz"
)

# Reproducible release:
# remotes::install_url("https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.20/phenosigdb_0.1.20.tar.gz")
```

Public API:

- `list_signatures(query = NULL, columns = NULL, min_genes = NULL, signature_format = NULL)`
- `get_signatures(signature_ids = NULL, reference_species = "human")`
- `phenosigdb_resources(action = "list", resource = NULL, force = FALSE, verbose = TRUE)`

Examples:

```r
library(phenosigdb)

# List all signatures
meta <- list_signatures()
caf <- list_signatures("FIBROBLAST")
sig <- get_signatures(caf)

# Case-insensitive regex search across the default metadata columns
immune <- list_signatures("immune")
source_slice <- list_signatures("MSigDB.C8")
metabolism <- list_signatures("metabolism", columns = c("signature_name", "context"))

# normal filtering is just data.frame filtering
pdac <- meta[meta$disease == "PDAC", ]
pathways <- meta[meta$context == "pathway", ]
continuous <- meta[meta$signature_format == "continuous", ]
msigdb_c7 <- meta[meta$collection == "msigdb.C7", ]

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
