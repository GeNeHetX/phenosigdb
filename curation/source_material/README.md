# Source Material

Single intake point for new papers and supplementary material.

Most legacy curated sources in this repo were migrated from CancerRNASig. `curation/source_material/` is for raw downloads and one-off build scripts for additions or recuration done directly in PhenoSigDB.

Workflow:

1. Create `curation/source_material/<SourceKey>/`.
2. Put PDFs, XLSX, CSV, TSV, ZIPs in `raw/`.
3. Write one local build script in the source folder, for example `build_curated.R`.
4. Manually create `curation/<DOMAIN>.<SourceKey>/source.yaml`.
5. Manually create `curation/<DOMAIN>.<SourceKey>/members.tsv`.
6. Run `phenosigdb-build --download-homology` and `phenosigdb-validate`.

Rules:

- `curation/source_material/` is raw material, notes, and one-off extraction scripts.
- sibling `curation/<DOMAIN>.<SourceKey>/` folders are the build-ready curated sources.
- IDs use `<DOMAIN>.<SourceKey>.<SignatureName>`.
- Keep domains simple and uppercase.
- No Greek letters in IDs or signature names; use `beta`, `gamma`, etc.
- Keep repo workflow simple: no global intake/promotion CLI for paper-specific scripts.
