# Curation Layout

Each curated source lives in its own folder:

- `curation/<source_name>/source.yaml`
- `curation/<source_name>/members.tsv`

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
