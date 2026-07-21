from __future__ import annotations

from pathlib import Path

import pandas as pd

SIGNATURE_COLUMNS = [
    "resource_name",
    "resource_version",
    "resource_snapshot_id",
    "signature_id",
    "signature_name",
    "signature_kind",
    "source_record_id",
    "source_identifier",
    "source_label",
    "source_url",
    "source_pmid",
    "source_doi",
    "dataset_id",
    "dataset_name",
    "cancer_type",
    "species",
    "species_original",
    "tissue",
    "tissue_original",
    "organ",
    "disease",
    "context",
    "cell_family",
    "cell_type",
    "cell_type_original",
    "cell_ontology_id",
    "annotation_level",
    "cluster_id",
    "marker_type",
    "evidence_level",
    "original_member_count",
    "imported_member_count",
    "signature_metadata_json",
]

MEMBER_COLUMNS = [
    "resource_name",
    "resource_version",
    "resource_snapshot_id",
    "signature_id",
    "member_id",
    "gene",
    "gene_original",
    "species",
    "species_original",
    "weight",
    "rank",
    "logfc",
    "avg_log2fc",
    "p_value",
    "adjusted_p_value",
    "percentage",
    "pct_1",
    "pct_2",
    "sensitivity",
    "specificity",
    "sensitivity_human",
    "sensitivity_mouse",
    "specificity_human",
    "specificity_mouse",
    "canonical_marker",
    "ubiquitous",
    "marker_type",
    "evidence",
    "evidence_level",
    "source_member_id",
    "source_gene_id",
    "source_uniprot_id",
    "source_series_id",
    "member_metadata_json",
]

DATASET_COLUMNS = [
    "resource_name",
    "resource_version",
    "resource_snapshot_id",
    "dataset_id",
    "dataset_name",
    "dataset_url",
    "species",
    "cancer_type",
    "tissue",
    "disease",
    "context",
    "accession",
    "pmid",
    "doi",
    "sample_count",
    "cell_count",
    "dataset_metadata_json",
]

SCORE_COLUMNS = [
    "resource_name",
    "resource_version",
    "resource_snapshot_id",
    "signature_id",
    "dataset_id",
    "dataset_name",
    "cancer_type",
    "cell_id",
    "sample_id",
    "state_name",
    "score",
    "score_metadata_json",
]

TABLE_SCHEMAS = {
    "signatures": SIGNATURE_COLUMNS,
    "members": MEMBER_COLUMNS,
    "datasets": DATASET_COLUMNS,
    "scores": SCORE_COLUMNS,
}


def empty_table(name: str) -> pd.DataFrame:
    columns = TABLE_SCHEMAS[name]
    return pd.DataFrame({column: pd.Series(dtype="object") for column in columns})


def conform_table(name: str, frame: pd.DataFrame | None) -> pd.DataFrame:
    if name not in TABLE_SCHEMAS:
        raise ValueError(f"Unknown external import table: {name}")
    if frame is None:
        return empty_table(name)

    columns = TABLE_SCHEMAS[name]
    extra = sorted(set(frame.columns).difference(columns))
    if extra:
        raise ValueError(f"{name} table has unexpected columns: {', '.join(extra)}")

    out = frame.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = pd.NA
    return out.loc[:, columns].reset_index(drop=True)


def table_path(output_dir: str | Path, name: str) -> Path:
    return Path(output_dir) / f"{name}.parquet"
