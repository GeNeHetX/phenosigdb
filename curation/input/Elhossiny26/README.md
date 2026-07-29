# Parser for {DOMAIN}.{SOURCE_KEY}

## Quick Start

1. **Place raw supplementary files** in this folder
2. **Edit `build_curated.R`** - see TODOs in the file
3. **Run parser:**
   ```bash
   Rscript build_curated.R
   ```
4. **Validate output:**
   ```bash
   python curation/tools/phenosigdb-validate-source {DOMAIN}.{SOURCE_KEY}
   ```
5. **Test full build:**
   ```bash
   python curation/tools/phenosigdb-release --dry-run
   ```

## File Structure

```
curation/input/{SOURCE_KEY}/
    build_curated.R      # Parser script (edit this)
    your_data.xlsx       # Raw supplementary files (place here)
    README.md            # This file

curation/curated/{DOMAIN}.{SOURCE_KEY}/
    source.yaml          # Metadata (generated)
    members.tsv          # Signature genes (generated)
```

## Metadata Fields (required in source.yaml)

- `source`: Short source identifier (e.g., "Smith24")
- `source_author`: Author name (e.g., "Smith.etal")
- `source_doi`: DOI of paper (e.g., "10.1038/xyz123")
- `source_pmid`: PubMed ID if available (optional)
- `species`: "human", "mouse", "mixed", or "unknown"
- `cell_family`: See `ALLOWED_CELL_FAMILY` in `tools/phenosigdb_maintainer/io.py`
- `context`: See `ALLOWED_CONTEXT` in `tools/phenosigdb_maintainer/io.py`
- `disease`: Disease name or "unknown"
- `tags`: Semicolon-separated tags (optional)

## members.tsv Format

Minimum columns: `signature_id`, `signature_name`, `gene`
Optional: `weight` (any non-empty weight makes signature continuous)

**Rules:**
- Never mix weighted and unweighted rows in one signature
- `signature_id` = `<DOMAIN>.<SOURCE_KEY>.<SignatureName>`
- SignatureName: ASCII only, normalize spaces/separators to dots
- Gene symbols: normalized (case-insensitive matching)

## Common Patterns

See existing parsers in `curation/input/` for examples:
- Excel: `CAF.Xing21/build_curated.R`
- Multi-sheet Excel: `CAF.Wang21/build_curated.R`
- Text/TSV: `CAF.ReviewLiu26/build_curated.R`

## Validation

Pre-commit hook runs automatically. To validate manually:
```bash
python curation/tools/phenosigdb-validate-source {DOMAIN}.{SOURCE_KEY}
```
