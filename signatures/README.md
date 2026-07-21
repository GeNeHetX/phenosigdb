# Signatures

Maintainer area only.

Repository layout:

- `signatures/curated/`: build-ready YAML/TSV signature inputs
- `signatures/source_material/`: raw files and one-off parsers
- `data/`: generated core artifacts and homology references
- `tools/`: maintainer code and commands
- `packages/python/`: Python user package
- `packages/r/`: R user package

## Main Commands

```bash
pip install -e packages/python
./tools/phenosigdb-build
./tools/phenosigdb-build --download-homology
./tools/phenosigdb-validate
pytest -q tests/maintainer
```

## Outputs

- `data/phenosigdb.parquet`
- `data/phenosigdb_human.parquet`
- `data/phenosigdb_mouse.parquet`
- `data/phenosigdb_reference_metadata.json`
- `data/phenosigdb_human_translation_signature_stats.tsv`
- `data/phenosigdb_mouse_translation_signature_stats.tsv`

## Optional Resource Staging

Use `external_imports` only for optional cached runtime resources.
Core curated signatures belong in `signatures/curated/` and are built by `phenosigdb-build`.

```bash
./tools/phenosigdb-external-imports list
./tools/phenosigdb-external-imports run celltypist cellmarker
./tools/phenosigdb-external-imports runtime-package celltypist <archive.tar.gz>
./tools/phenosigdb-external-imports runtime-package cellmarker <archive.tar.gz>
```

Generated staging outputs under `data/external_imports/` are maintainer-only and should stay out of git.

## Versioning

- curated core data changes when the repo curation changes
- optional resources are pinned by PhenoSigDB release code and manifests
- MSigDB resources use explicit upstream release URLs
- WikiPathways resolves the current Homo sapiens GMT file and records the resolved version in the installed manifest
- Reactome is fetched from the official current GMT zip and recorded with install metadata and checksum

More curation rules live in [signatures/curated/README.md](/Users/remy.nicolle/Workspace/DEV/phenosigdb/signatures/curated/README.md).
