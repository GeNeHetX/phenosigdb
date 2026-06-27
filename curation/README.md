# Curation Layout

`curation/` contains build-ready curated sources only.

Raw PDFs, XLSX, CSVs, ZIPs, notes, and extraction scripts belong in `curation/source_material/<SourceKey>/`.

Each curated source lives in its own folder:

- `curation/<source_name>/source.yaml`
- `curation/<source_name>/members.tsv`

Use the same source name as the `signature_id` prefix:

```text
curation/<DOMAIN>.<SourceKey>/
```

Signature IDs must use:

```text
<DOMAIN>.<SourceKey>.<SignatureName>
```

Examples:

- `PDAC.Moffitt15.Classical`
- `CAF.Elyada19.iCAF`
- `IMMUNE.Becht16.Tcells`
- `GI.Busslinger21.Stem.cells`

`source.yaml` stores source-level defaults.

`members.tsv` stores one row per gene with:

- `signature_id`
- `signature_name`
- `gene`

Optional overrides may be added for:

- `species`
- `cell_family`
- `context`
- `disease`
- `tags`

`curation/example_source/` is a template example and is ignored by the build.

Keep workflow simple: `curation/source_material/` is manual staging space, and sibling curated folders are the canonical output. No repo-wide intake/promote CLI is required for paper-specific processing.
