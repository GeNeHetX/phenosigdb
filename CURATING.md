# Curation Workflow

**For maintainers adding new signatures from published studies.**

Users: see [README.md](README.md) for library usage.

---

## Workflow

```bash
# 1. Create scaffold (folder + template parser)
python curation/tools/phenosigdb-scaffold Smith24 --domain FIBROBLAST

# 2. Add raw supplementary data to: curation/input/Smith24/

# 3. Edit parser: curation/input/Smith24/build_curated.R
   - Set file path
   - Read data
   - Define metadata (DOI from paper, species, cell_family, context, disease)
   - Parse signatures into all_members data.frame

# 4. Test (runs parser + validates)
python curation/tools/tests/test_parser_cli.py Smith24

# 5. Inspect output: curation/curated/FIBROBLAST.Smith24/
   - Check signature names, gene counts, gene lists

# 6. Release (after committing changes)
python curation/tools/phenosigdb-release <version>
```

---

## What to Edit in Parser

The generated `build_curated.R` template:

```r
# === EDIT BELOW THIS LINE ===

# Set your raw file path
raw_path <- file.path(source_dir, "your_data.xlsx")

# Read your data
dat <- read_excel(raw_path)  # or read.delim() for TSV

# Define metadata (ALL REQUIRED)
# Get DOI and PubMed ID from the paper's abstract page or PDF
source_author <- "Author.etal"
source_doi <- ""      # DOI from paper
source_pmid <- ""     # PubMed ID if available
species <- "human"    # human, mouse, mixed, unknown
cell_family <- ""    # See allowed values below
context <- ""        # See allowed values below
disease <- "unknown"
tags <- NULL         # optional

# Parse signatures
# For each signature in your data:
signature_name <- normalize_sig("RawName")
genes <- split_genes("gene1, gene2, gene3")
signature_id <- paste0("FIBROBLAST.Smith24.", signature_name)
members <- data.frame(
  signature_id = rep(signature_id, length(genes)),
  signature_name = rep(signature_name, length(genes)),
  gene = genes,
  stringsAsFactors = FALSE
)
# Combine all signatures
all_members <- do.call(rbind, list_of_members_dataframes)

# === DO NOT EDIT BELOW THIS LINE ===
```

---

## Allowed Metadata Values

**Species:** `human`, `mouse`, `mixed`, `unknown`

**Cell Family:** `fibroblast`, `endothelial`, `epithelial`, `tumor`, `macrophage`, `monocyte`, `neutrophil`, `T_cell`, `B_cell`, `plasma_cell`, `NK_cell`, `immune`, `stromal`, `ductal`, `acinar`, `endocrine`, `pericyte`, `smooth_muscle`, `neuron`, `glial`, `unknown`

**Context:** `physiology`, `development`, `inflammation`, `fibrosis`, `cancer`, `treatment`, `organoid`, `unknown`

---

## Instructing an LLM

Provide to the LLM:
1. The raw data file(s)
2. SourceKey (e.g., `Smith24`), DOMAIN (e.g., `FIBROBLAST`)
3. Author, DOI, species (from paper)
4. File format and which columns contain signature names and genes
5. Any filtering rules

LLM should use the scaffold-generated template and functions from `parser_utils.R`.

---

## Multiple Cell Types from One Paper

If a paper has multiple cell type signatures (e.g., different fibroblast subtypes):
- Use single SourceKey: `Smith24` with domain `FIBROBLAST`
- In parser: set different `cell_family` per signature
- All signatures go in `curation/curated/FIBROBLAST.Smith24/`

If a paper truly spans different biological domains (e.g., both CAF and PATHWAY signatures):
- Create separate scaffolds with different domains
- Example: `Smith24.CAF` with `--domain FIBROBLAST` and `Smith24.Pathway` with `--domain PATHWAY`
- Two parser folders, two curated outputs

---

## Release

```bash
python curation/tools/phenosigdb-release <version>
git diff --stat
git commit -m "Add Smith24 signatures"
git tag v<version>
git push && git push --tags
```
