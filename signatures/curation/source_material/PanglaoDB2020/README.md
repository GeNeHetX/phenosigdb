## PanglaoDB2020

- Raw file: `PanglaoDB_markers_27_Mar_2020.tsv.gz`
- URL: <https://panglaodb.se/markers/PanglaoDB_markers_27_Mar_2020.tsv.gz>
- Parser: `build_curated.py`
- Curated output: `curation/CELL.PanglaoDB2020/`

Cleanup rules:

- keep only explicit `human` and `mouse`
- exclude `mixed`, blank, and malformed species rows
- drop malformed species rows such as blank or `4`
- one signature per `(species, organ, cell type)`
- normalize genes to species-aware symbols
- output binary marker gene sets only
