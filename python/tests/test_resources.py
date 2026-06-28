import json
import tarfile
import zipfile
from pathlib import Path

import pandas as pd

from phenosigdb import get_signatures, list_signatures, phenosigdb_resources
from phenosigdb import query as query_mod


def _resource_archive(tmp_path: Path, resource: str, metadata: pd.DataFrame, values: pd.DataFrame, version: str = "1.0") -> Path:
    resource_dir = tmp_path / resource
    resource_dir.mkdir(parents=True, exist_ok=True)
    metadata.to_parquet(resource_dir / "metadata.parquet", index=False)
    if resource == "celltypist":
        values.to_parquet(resource_dir / "continuous.parquet", index=False)
        signature_format = "continuous"
    else:
        values.to_parquet(resource_dir / "binary.parquet", index=False)
        signature_format = "binary"
    (resource_dir / "resource.json").write_text(
        json.dumps(
            {
                "resource": resource,
                "version": version,
                "installed_at": "2026-06-27T00:00:00Z",
                "signature_format": signature_format,
                "n_signatures": int(metadata["signature_id"].nunique()),
                "n_rows": int(len(values)),
                "package_version": "0.1.0",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    archive = tmp_path / f"{resource}.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(resource_dir, arcname=resource)
    return archive


def _gmt_file(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _zip_with_gmt(path: Path, name: str, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as handle:
        handle.writestr(name, "\n".join(lines) + "\n")
    return path


def _fake_core_read(reference_species="human"):
    if reference_species == "mouse":
        species = "mouse"
        gene = "Col1a1"
    else:
        species = "human"
        gene = "COL1A1"
    return pd.DataFrame(
        [
            {
                "signature_id": "CAF.Elyada19.iCAF",
                "signature_name": "iCAF",
                "source": "Elyada.etal",
                "source_author": "Elyada.etal",
                "source_pmid": "31197017",
                "source_doi": None,
                "species": species,
                "species_original": species,
                "gene": gene,
                "gene_original": gene,
                "cell_family": "fibroblast",
                "context": "cancer",
                "disease": "PDAC",
                "tags": "CAF",
                "homology_relation": "same_species",
                "homology_db_class_key": None,
            }
        ]
    )


def test_phenosigdb_resources_install_remove_update(monkeypatch, tmp_path: Path):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("PHENOSIGDB_CACHE_DIR", str(cache_dir))

    ct_meta = pd.DataFrame(
        [
            {
                "signature_id": "CELLTYPIST.Immune_All_Low.CD8_T_cell",
                "signature_name": "CD8 T cell",
                "domain": "CELLTYPIST",
                "source": "Immune_All_Low",
                "collection": "Immune_All_Low",
                "source_resource": "celltypist",
                "resource_key": "celltypist",
                "signature_format": "continuous",
                "species": "human",
                "species_original": "human",
                "cell_family": "T_cell",
                "context": "reference_model",
                "disease": None,
                "n_genes": 2,
                "source_version": "v1",
                "source_label": "Immune model",
                "source_pmid": None,
                "source_doi": None,
                "source_url": "https://example.org/celltypist",
                "original_source": "Immune_All_Low.pkl",
                "original_signature_name": "CD8 T cell",
                "cell_ontology_id": None,
                "annotation_level": "classifier_label",
                "resource_metadata_json": "{}",
            }
        ]
    )
    ct_values = pd.DataFrame(
        [
            {"signature_id": "CELLTYPIST.Immune_All_Low.CD8_T_cell", "gene": "CD3D", "weight": 1.0},
            {"signature_id": "CELLTYPIST.Immune_All_Low.CD8_T_cell", "gene": "TRBC1", "weight": 0.5},
        ]
    )
    cm_meta = pd.DataFrame(
        [
            {
                "signature_id": "CELLMARKER.human_Liver_Normal.Hepatocyte",
                "signature_name": "Hepatocyte",
                "domain": "CELLMARKER",
                "source": "human__Liver__Normal",
                "collection": "grouped",
                "source_resource": "cellmarker",
                "resource_key": "cellmarker",
                "signature_format": "binary",
                "species": "human",
                "species_original": "human",
                "cell_family": "epithelial",
                "context": "unknown",
                "disease": "Normal",
                "n_genes": 2,
                "source_version": "3.0",
                "source_label": "CellMarker grouped",
                "source_pmid": "12345",
                "source_doi": None,
                "source_url": "https://example.org/cellmarker",
                "original_source": "Liver",
                "original_signature_name": "Hepatocyte",
                "cell_ontology_id": "CL:0000182",
                "annotation_level": "Hepatocyte",
                "resource_metadata_json": "{}",
            }
        ]
    )
    cm_values = pd.DataFrame(
        [
            {"signature_id": "CELLMARKER.human_Liver_Normal.Hepatocyte", "gene": "ALB"},
            {"signature_id": "CELLMARKER.human_Liver_Normal.Hepatocyte", "gene": "APOA1"},
        ]
    )

    ct_archive = _resource_archive(tmp_path / "ct", "celltypist", ct_meta, ct_values, version="2026.06")
    cm_archive = _resource_archive(tmp_path / "cm", "cellmarker", cm_meta, cm_values, version="3.0")
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_CELLTYPIST", str(ct_archive))
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_CELLMARKER", str(cm_archive))

    listing = phenosigdb_resources("list")
    assert {"celltypist", "cellmarker"}.issubset(set(listing["resource"]))
    assert not listing["installed"].any()

    installed_ct = phenosigdb_resources("install", "celltypist", verbose=False)
    installed_cm = phenosigdb_resources("install", "cellmarker", verbose=False)
    assert installed_ct["resource"] == "celltypist"
    assert installed_cm["resource"] == "cellmarker"
    assert installed_ct["installed"] is True
    assert installed_cm["installed"] is True
    assert (cache_dir / "celltypist" / "continuous.parquet").exists()
    assert (cache_dir / "cellmarker" / "binary.parquet").exists()

    updated_ct = phenosigdb_resources("update", "celltypist", verbose=False)
    assert updated_ct["version"] == "2026.06"

    removed_cm = phenosigdb_resources("remove", "cellmarker", verbose=False)
    assert removed_cm["installed"] is False
    assert not (cache_dir / "cellmarker").exists()

    reinstalled_missing = phenosigdb_resources("install", "cellmarker", verbose=False)
    assert reinstalled_missing["installed"] is True
    assert (cache_dir / "cellmarker" / "binary.parquet").exists()
    assert phenosigdb_resources("path") == str(cache_dir.resolve())


def test_list_signatures_and_get_signatures_include_optional_resources(monkeypatch, tmp_path: Path):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("PHENOSIGDB_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(query_mod, "read_database", lambda reference_species="human": _fake_core_read(reference_species=reference_species))

    ct_meta = pd.DataFrame(
        [
            {
                "signature_id": "CELLTYPIST.Immune_All_Low.CD8_T_cell",
                "signature_name": "CD8 T cell",
                "domain": "CELLTYPIST",
                "source": "Immune_All_Low",
                "collection": "Immune_All_Low",
                "source_resource": "celltypist",
                "resource_key": "celltypist",
                "signature_format": "continuous",
                "species": "human",
                "species_original": "human",
                "cell_family": "T_cell",
                "context": "reference_model",
                "disease": None,
                "n_genes": 2,
                "source_version": "v1",
                "source_label": "Immune model",
                "source_pmid": None,
                "source_doi": None,
                "source_url": "https://example.org/celltypist",
                "original_source": "Immune_All_Low.pkl",
                "original_signature_name": "CD8 T cell",
                "cell_ontology_id": None,
                "annotation_level": "classifier_label",
                "resource_metadata_json": "{}",
            }
        ]
    )
    ct_values = pd.DataFrame(
        [
            {"signature_id": "CELLTYPIST.Immune_All_Low.CD8_T_cell", "gene": "CD3D", "weight": 1.25},
            {"signature_id": "CELLTYPIST.Immune_All_Low.CD8_T_cell", "gene": "TRBC1", "weight": 0.5},
        ]
    )
    cm_meta = pd.DataFrame(
        [
            {
                "signature_id": "CELLMARKER.mouse_Brain_Normal.Neuron",
                "signature_name": "Neuron",
                "domain": "CELLMARKER",
                "source": "mouse__Brain__Normal",
                "collection": "grouped",
                "source_resource": "cellmarker",
                "resource_key": "cellmarker",
                "signature_format": "binary",
                "species": "mouse",
                "species_original": "mouse",
                "cell_family": "neuron",
                "context": "unknown",
                "disease": "Normal",
                "n_genes": 2,
                "source_version": "3.0",
                "source_label": "CellMarker grouped",
                "source_pmid": "12345",
                "source_doi": None,
                "source_url": "https://example.org/cellmarker",
                "original_source": "Brain",
                "original_signature_name": "Neuron",
                "cell_ontology_id": "CL:0000540",
                "annotation_level": "Neuron",
                "resource_metadata_json": "{}",
            }
        ]
    )
    cm_values = pd.DataFrame(
        [
            {"signature_id": "CELLMARKER.mouse_Brain_Normal.Neuron", "gene": "Snap25"},
            {"signature_id": "CELLMARKER.mouse_Brain_Normal.Neuron", "gene": "Rbfox3"},
        ]
    )
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_CELLTYPIST", str(_resource_archive(tmp_path / "ct", "celltypist", ct_meta, ct_values)))
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_CELLMARKER", str(_resource_archive(tmp_path / "cm", "cellmarker", cm_meta, cm_values)))

    human_meta = list_signatures(reference_species="human")
    assert set(human_meta["source_resource"]) == {"curated"}

    mixed = get_signatures(
        [
            "CAF.Elyada19.iCAF",
            "CELLTYPIST.Immune_All_Low.CD8_T_cell",
            "CELLMARKER.mouse_Brain_Normal.Neuron",
        ],
        reference_species="original",
    )
    assert mixed["CAF.Elyada19.iCAF"] == ["COL1A1"]
    assert mixed["CELLTYPIST.Immune_All_Low.CD8_T_cell"] == {"CD3D": 1.25, "TRBC1": 0.5}
    assert mixed["CELLMARKER.mouse_Brain_Normal.Neuron"] == ["Rbfox3", "Snap25"]
    assert (cache_dir / "celltypist" / "continuous.parquet").exists()
    assert (cache_dir / "cellmarker" / "binary.parquet").exists()

    human_meta = list_signatures(reference_species="human")
    assert set(human_meta["source_resource"]) == {"curated", "celltypist"}
    assert "signature_format" in human_meta.columns

    mouse_meta = list_signatures(reference_species="mouse")
    assert "CELLMARKER.mouse_Brain_Normal.Neuron" in set(mouse_meta["signature_id"])
    assert "CELLTYPIST.Immune_All_Low.CD8_T_cell" not in set(mouse_meta["signature_id"])


def test_direct_gmt_resources_install_and_auto_install(monkeypatch, tmp_path: Path, capsys):
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("PHENOSIGDB_CACHE_DIR", str(cache_dir))
    monkeypatch.setattr(query_mod, "read_database", lambda reference_species="human": _fake_core_read(reference_species=reference_species))

    msigdb_gmt = _gmt_file(
        tmp_path / "msigdb" / "c7.gmt",
        ["CD8_EFFECTOR_UP\tpmid:1\tGZMB\tPRF1\tGZMB"],
    )
    reactome_zip = _zip_with_gmt(
        tmp_path / "reactome" / "reactome.zip",
        "ReactomePathways.gmt",
        ["REACTOME_INTERFERON_SIGNALING\thttps://reactome.org\tSTAT1\tIRF9"],
    )
    wp_gmt = _gmt_file(
        tmp_path / "wikipathways" / "wikipathways-20260610-gmt-Homo_sapiens.gmt",
        ["WP_FIBROBLAST_SIGNALING\tWikiPathways\tCOL1A1\tCOL3A1"],
    )
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_MSIGDB_C7IMMUNE", str(msigdb_gmt))
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_REACTOME", str(reactome_zip))
    monkeypatch.setenv("PHENOSIGDB_RESOURCE_URL_WIKIPATHWAYS", str(wp_gmt))

    installed = phenosigdb_resources("install", "msigdb_c7immune")
    out = capsys.readouterr().out
    assert "MSigDB" in out
    assert installed["resource"] == "msigdb_c7immune"
    assert (cache_dir / "msigdb_c7immune" / "binary.parquet").exists()

    meta = list_signatures(reference_species="human")
    row = meta.loc[meta["signature_id"] == "MSIGDB.C7.CD8_EFFECTOR_UP"].iloc[0]
    assert row["source_resource"] == "msigdb"
    assert row["collection"] == "C7"
    assert row["context"] == "immunology"
    assert row["signature_format"] == "binary"

    sigs = get_signatures(["REACTOME.Pathways.REACTOME_INTERFERON_SIGNALING", "WIKIPATHWAYS.HomoSapiens.WP_FIBROBLAST_SIGNALING"])
    assert sigs["REACTOME.Pathways.REACTOME_INTERFERON_SIGNALING"] == ["IRF9", "STAT1"]
    assert sigs["WIKIPATHWAYS.HomoSapiens.WP_FIBROBLAST_SIGNALING"] == ["COL1A1", "COL3A1"]
    assert (cache_dir / "reactome" / "binary.parquet").exists()
    assert (cache_dir / "wikipathways" / "binary.parquet").exists()
