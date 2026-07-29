# Curation Workflow

**For maintainers adding new signatures from published studies.**

Users: see [README.md](README.md) for library usage.

---

## Quick Start (Recommended)

```bash
# 1. Generate scaffold (creates folder + template parser)
python curation/tools/phenosigdb-scaffold Smith24 --domain FIBROBLAST

# 2. Put your raw supplementary data in the generated folder
#    curation/input/Smith24/your_data.xlsx

# 3. Edit the parser
#    curation/input/Smith24/build_curated.R

# 4. Test (runs parser + validates output)
python curation/tools/tests/test_parser_cli.py Smith24
```

---

## What is SourceKey?

**SourceKey = Paper identifier**

- Format: `AuthorYear` (e.g., `Smith24`, `Wang21`)
- Uppercase, alphanumeric only, no spaces or special characters
- Examples from existing curation: `Xing21`, `Wang21`, `ReviewLiu26`, `Elyada19`

**DOMAIN = Biology category**

- `CELL` - Cell type signatures
- `FIBROBLAST` - Fibroblast/CAF signatures  
- `CANCER` - Cancer-related signatures
- `PATHWAY` - Pathway signatures
- Always uppercase, simple

**Full signature ID format:**
```
<DOMAIN>.<SourceKey>.<SignatureName>
Example: FIBROBLAST.Wang21.Myofibroblast
```

---

## What Parser Does

Simple transformation:
```
Your raw supplementary data (Excel/TSV/CSV/Text)
    → build_curated.R (parser script)
        → members.tsv (gene list)
        → source.yaml (metadata)
```

The generated `build_curated.R` has **TODOs** showing exactly what to edit.

---

## Directory Structure

```
curation/
├── input/                          # Raw supplementary data
│   └── Smith24/                    # SourceKey = folder name
│       ├── your_data.xlsx          # Your raw file(s)
│       ├── build_curated.R         # Parser (edit this)
│       └── README.md               # This guide
│
└── curated/                       # Generated clean data
    └── FIBROBLAST.Smith24/         # DOMAIN.SourceKey
        ├── source.yaml             # Metadata
        └── members.tsv             # Signature genes
```

---

## Parser Template (build_curated.R)

After running scaffold, your parser has this structure:

```r
# === EDIT BELOW THIS LINE ===

# TODO: Set raw file path
raw_path <- file.path(source_dir, "your_file.xlsx")

# TODO: Read data
dat <- read_excel(raw_path)  # or read.delim() for TSV

# TODO: Define metadata (ALL REQUIRED)
# Get DOI and PubMed ID from the paper's abstract page or PDF
source_author <- "Smith.etal"
source_doi <- ""        # Required: DOI from paper
source_pmid <- ""       # Optional: PubMed ID
species <- "human"      # human, mouse, mixed, unknown
cell_family <- "fibroblast" # see allowed values below
context <- "cancer"     # see allowed values below
disease <- "PDAC"      # or "unknown"
tags <- c("CAF", "pancreatic")  # optional

# TODO: Parse signatures
# For each signature in your data:
signature_name <- normalize_sig("Raw Name Here")
genes <- split_genes("ACTA2, COL1A1, COL3A1")
signature_id <- paste0("FIBROBLAST.Smith24.", signature_name)
members <- data.frame(
  signature_id = signature_id,
  signature_name = signature_name,
  gene = genes,
  stringsAsFactors = FALSE
)
# Combine all: all_members <- do.call(rbind, list_of_members)

# === DO NOT EDIT BELOW THIS LINE ===
# (auto-writes source.yaml and members.tsv)
```

---

## Allowed Metadata Values

### Species
`human`, `mouse`, `mixed`, `unknown`

### Cell Family
`fibroblast`, `endothelial`, `epithelial`, `tumor`, `macrophage`, `monocyte`, 
`neutrophil`, `T_cell`, `B_cell`, `plasma_cell`, `NK_cell`, `immune`, `stromal`, 
`ductal`, `acinar`, `endocrine`, `pericyte`, `smooth_muscle`, `neuron`, `glial`, `unknown`

### Context
`physiology`, `development`, `inflammation`, `fibrosis`, `cancer`, `treatment`, `organoid`, `unknown`

See full list in: `curation/tools/phenosigdb_maintainer/io.py`

---

## members.tsv Format

**Required columns:** `signature_id`, `signature_name`, `gene`

**Optional:** `weight` (any non-empty weight makes signature continuous)

**Rules:**
- Never mix weighted and unweighted rows in one signature
- `signature_id` = `<DOMAIN>.<SourceKey>.<SignatureName>`
- SignatureName: ASCII only, normalize spaces/separators to dots
- Gene symbols: normalized (case-insensitive matching)

---

## Common Patterns

See existing parsers in `curation/input/` for examples:

| Format | Example Parser | Notes |
|--------|----------------|-------|
| Excel (single sheet) | `CAF.Xing21/build_curated.R` | Simple gene lists |
| Excel (multi-sheet) | `CAF.Wang21/build_curated.R` | One sheet per signature |
| Text (block format) | `CAF.Grout22/build_curated.R` | Blank-line separated |
| Text (free-form) | `CAF.ReviewLiu26/build_curated.R` | One line per signature |

---

## Validation

Pre-commit hook runs automatically.

To test a single parser (runs parser + validates output):
```bash
python curation/tools/tests/test_parser_cli.py Smith24
```

To validate existing curated output without re-running parsers:
```bash
# Single source
python curation/tools/phenosigdb-validate-source FIBROBLAST.Smith24

# All changed sources
python curation/tools/phenosigdb-validate-source --changed

# All sources
python curation/tools/phenosigdb-validate-source --all
```

---

## Testing Parsers

### Quick Test (CLI)

Test a single parser you're developing:

```bash
# Run parser + validate output
python curation/tools/tests/test_parser_cli.py Smith24
```

This runs:
1. Parser execution
2. Checks output files exist
3. Validates output format
4. Reports success/failure with details

### Full Test Suite (pytest)

Run all parser tests:

```bash
# Install pytest if needed
pip install pytest

# Run all tests
pytest curation/tools/tests/test_parsers.py -v

# Run single test
pytest curation/tools/tests/test_parsers.py -v -k "CAF_Xing21"

# Run with verbose output
pytest curation/tools/tests/test_parsers.py -v --tb=short
```

### Add Your Parser to Test Suite

1. Run your parser manually first:
   ```bash
   Rscript curation/input/Smith24/build_curated.R
   ```

2. Add to test list in `curation/tools/tests/test_parsers.py`:
   ```python
   PARSER_SOURCES = [
       # ... existing entries ...
       ("Smith24", "FIBROBLAST"),  # Add this line
   ]
   ```

3. Run the test:
   ```bash
   pytest curation/tools/tests/test_parsers.py::test_parser_produces_valid_output -v -k "Smith24"
   ```

---

## Development Workflow

---

## Shared Utilities

Your parser can use these functions from `curation/tools/phenosigdb_maintainer/parser_utils.R`:

```r
# Normalize signature names
normalize_sig("My CAF Signature")  # -> "My.CAF.Signature"

# Split gene strings (comma, semicolon, newline, tab separated)
split_genes("ACTA2, COL1A1, ACTA2")  # -> c("ACTA2", "COL1A1")

# Infer species from gene symbols (human vs mouse)
infer_species(c("ACTA2", "COL1A1", "Tcra"))  # -> "human"

# Infer cell family from signature name
infer_cell_family("Fibro-C1")  # -> "fibroblast"

# Write metadata file
write_source_yaml(path, source, source_author, source_doi, species, cell_family, context, disease, tags)
```

---

## Release Workflow

After adding/updating signatures:

```bash
# Full build and validation
python curation/tools/phenosigdb-release <version>

# Review changes
git diff --stat
git diff -- README.md

# Commit, tag, push (follows standard GitHub release flow)
```

---

## Troubleshooting

**Problem:** Parser fails with path errors

**Solution:** Make sure your parser uses relative paths from `source_dir`, not absolute paths.

**Problem:** Validation fails with "missing columns"

**Solution:** Ensure `members.tsv` has at least: `signature_id`, `signature_name`, `gene`

**Problem:** Validation fails with "empty values"

**Solution:** Check for empty strings or NA values in required columns

---

## Agent/LLM Instructions

When instructing an LLM to write a parser:

1. Provide the raw data file(s)
2. Specify: SourceKey, DOMAIN, author, DOI, species
3. Describe the file format (Excel/TSV/Text, delimiters, sheets, etc.)
4. Describe which columns contain signature names and genes
5. Mention any filtering rules (e.g., exclude certain rows)

The LLM should:
- Use the scaffold-generated template as a starting point
- Use functions from `parser_utils.R` (normalize_sig, split_genes, etc.)
- Output to `curation/curated/<DOMAIN>.<SourceKey>/`
