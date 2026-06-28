import json

import pandas as pd

from phenosigdb_maintainer.resource_build import build_runtime_cellmarker, build_runtime_celltypist


def test_runtime_builders_normalize_celltypist_and_group_cellmarker(tmp_path):
    ct_stage = tmp_path / "celltypist_stage"
    ct_stage.mkdir(parents=True)
    ct_signatures = pd.DataFrame(
        [
            {
                "signature_id": "old.id.1",
                "resource_version": "2026.06",
                "signature_name": "CD8 T cell",
                "dataset_id": "Immune_All_Low",
                "dataset_name": "Immune_All_Low",
                "species": "human",
                "species_original": "human",
                "cell_family": "T_cell",
                "context": "reference_model",
                "disease": None,
                "cell_type_original": "CD8 T cell",
                "cell_ontology_id": None,
                "annotation_level": "classifier_label",
                "source_label": "Immune model",
                "source_pmid": None,
                "source_doi": None,
                "source_url": "https://example.org/celltypist",
                "source_identifier": "Immune_All_Low.pkl",
                "signature_metadata_json": "{}",
            }
        ]
    )
    ct_members = pd.DataFrame(
        [
            {"signature_id": "old.id.1", "gene": "CD3D", "weight": 1.0},
            {"signature_id": "old.id.1", "gene": "TRBC1", "weight": 0.0},
            {"signature_id": "old.id.1", "gene": "TRBC2", "weight": -0.5},
        ]
    )
    ct_signatures.to_parquet(ct_stage / "signatures.parquet", index=False)
    ct_members.to_parquet(ct_stage / "members.parquet", index=False)
    (ct_stage / "manifest.json").write_text(json.dumps({"resource_version": "2026.06"}), encoding="utf-8")

    ct_meta, ct_values, _ = build_runtime_celltypist(staging_root=ct_stage)
    assert ct_meta.loc[0, "signature_id"] == "CELLTYPIST.Immune_All_Low.CD8_T_cell"
    assert list(ct_values["gene"]) == ["CD3D", "TRBC2"]
    assert str(ct_values["weight"].dtype) == "float32"

    cm_stage = tmp_path / "cellmarker_stage"
    cm_stage.mkdir(parents=True)
    cm_signatures = pd.DataFrame(
        [
            {
                "signature_id": "raw1",
                "resource_version": "3.0",
                "species": "human",
                "species_original": "human",
                "tissue": "Liver",
                "organ": "Digestive system",
                "disease": "Normal",
                "context": None,
                "cell_family": "epithelial",
                "cell_type": "Hepatocyte",
                "cell_type_original": "Hepatocyte",
                "cell_ontology_id": "CL:0000182",
                "annotation_level": "Hepatocyte",
                "source_pmid": "12345",
                "source_doi": None,
                "source_url": "https://example.org/cellmarker",
                "source_record_id": 1,
                "source_identifier": "row1",
                "source_label": "CellMarker row 1",
                "signature_metadata_json": "{}",
            },
            {
                "signature_id": "raw2",
                "resource_version": "3.0",
                "species": "human",
                "species_original": "human",
                "tissue": "Liver",
                "organ": "Digestive system",
                "disease": "Normal",
                "context": None,
                "cell_family": "epithelial",
                "cell_type": "Hepatocyte",
                "cell_type_original": "Hepatocyte",
                "cell_ontology_id": "CL:0000182",
                "annotation_level": "Hepatocyte",
                "source_pmid": "67890",
                "source_doi": None,
                "source_url": "https://example.org/cellmarker",
                "source_record_id": 2,
                "source_identifier": "row2",
                "source_label": "CellMarker row 2",
                "signature_metadata_json": "{}",
            },
        ]
    )
    cm_members = pd.DataFrame(
        [
            {"signature_id": "raw1", "gene": "ALB"},
            {"signature_id": "raw1", "gene": "APOA1"},
            {"signature_id": "raw2", "gene": "ALB"},
            {"signature_id": "raw2", "gene": "TTR"},
        ]
    )
    cm_signatures.to_parquet(cm_stage / "signatures.parquet", index=False)
    cm_members.to_parquet(cm_stage / "members.parquet", index=False)
    (cm_stage / "manifest.json").write_text(json.dumps({"resource_version": "3.0"}), encoding="utf-8")

    cm_meta, cm_values, _ = build_runtime_cellmarker(staging_root=cm_stage)
    assert len(cm_meta) == 1
    assert cm_meta.loc[0, "signature_id"] == "CELLMARKER.human_Liver_Normal.Hepatocyte"
    assert sorted(cm_values["gene"].tolist()) == ["ALB", "APOA1", "TTR"]
    assert json.loads(cm_meta.loc[0, "resource_metadata_json"])["publication_count"] == 2
