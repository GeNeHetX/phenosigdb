# Signatures

Maintainer area only.

Repo split:

- `python/`
  - Python user library
- `r-package/`
  - R user package
- `signatures/`
  - curation, build tooling, built reference artifacts, optional-resource staging

## Main Commands

```bash
pip install -e python
./signatures/phenosigdb-build
./signatures/phenosigdb-build --download-homology
./signatures/phenosigdb-validate
pytest -q signatures/tests
```

## Outputs

- `signatures/data/phenosigdb.parquet`
- `signatures/data/phenosigdb_human.parquet`
- `signatures/data/phenosigdb_mouse.parquet`
- `signatures/data/phenosigdb_reference_metadata.json`
- `signatures/data/phenosigdb_human_translation_signature_stats.tsv`
- `signatures/data/phenosigdb_mouse_translation_signature_stats.tsv`

## Optional Resource Staging

Use `external_imports` only for optional cached runtime resources.
Core curated signatures belong in `curation/` and are built by `phenosigdb-build`.

```bash
./signatures/phenosigdb-external-imports list
./signatures/phenosigdb-external-imports run celltypist cellmarker
./signatures/phenosigdb-external-imports runtime-package celltypist <archive.tar.gz>
./signatures/phenosigdb-external-imports runtime-package cellmarker <archive.tar.gz>
```

Generated staging outputs under `signatures/data/external_imports/` are maintainer-only and should stay out of git.

## Versioning

- curated core data changes when the repo curation changes
- optional resources are pinned by PhenoSigDB release code and manifests
- MSigDB resources use explicit upstream release URLs
- WikiPathways resolves the current Homo sapiens GMT file and records the resolved version in the installed manifest
- Reactome is fetched from the official current GMT zip and recorded with install metadata and checksum

More curation rules live in [signatures/curation/README.md](/Users/remy.nicolle/Workspace/DEV/phenosigdb/signatures/curation/README.md).
