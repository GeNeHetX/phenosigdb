# PhenoSigDB Maintenance

## Add a signature

1. Create a source folder:

```bash
mkdir -p signatures/source_material/<SourceKey>
```

2. Put the downloaded supplementary files in that folder.

3. Add one parser:

```text
signatures/source_material/<SourceKey>/build_curated.R
```

4. Run the parser:

```bash
Rscript signatures/source_material/<SourceKey>/build_curated.R
```

5. Check that it created:

```text
signatures/curated/<DOMAIN>.<SourceKey>/source.yaml
signatures/curated/<DOMAIN>.<SourceKey>/members.tsv
```

`source.yaml` must contain `source`, `species`, `cell_family`, `context`, and `disease`. Keep author, PMID, and DOI when available.

`members.tsv` must contain `signature_id`, `signature_name`, and `gene`. Add `weight` for weighted signatures.

IDs:

```text
<DOMAIN>.<SourceKey>.<SignatureName>
```

Use uppercase simple domains and ASCII names.

## Release

Run from the repository root.

1. Install dependencies once:

```bash
python -m venv /tmp/phenosigdb-release-venv
source /tmp/phenosigdb-release-venv/bin/activate
pip install -e 'packages/python[maintainer]' pytest PyYAML
Rscript -e 'install.packages(c("arrow","jsonlite","rappdirs","testthat"), repos="https://cloud.r-project.org")'
```

2. Build and test the complete release. Replace `0.1.11` with the new version:

```bash
./tools/phenosigdb-release 0.1.11
```

3. Review:

```bash
git diff --stat
git diff -- README.md
ls -lh dist/
```

4. Commit and push the source:

```bash
git add -A
git commit -m "Release v0.1.11"
git push origin main
git tag -a v0.1.11 -m "Release v0.1.11"
git push origin v0.1.11
```

5. Create the GitHub release and upload every file in `dist/`:

```bash
gh release create v0.1.11 dist/* --verify-tag --generate-notes
```

6. Install the released R package:

```r
remotes::install_url(
  "https://github.com/GeNeHetX/phenosigdb/releases/download/v0.1.17/phenosigdb_0.1.17.tar.gz"
)
```

Release output:

```text
dist/phenosigdb_<VERSION>.tar.gz
dist/phenosigdb-r.tar.gz
dist/phenosigdb-resource-*.tar.gz
```
