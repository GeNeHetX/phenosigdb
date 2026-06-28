import pandas as pd

from phenosigdb import query as query_mod
from phenosigdb.query import get_signatures, list_signatures


def _fake_core_read(reference_species="human"):
    gene_a = "COL1A1" if reference_species != "mouse" else "Col1a1"
    gene_b = "CXCL12" if reference_species != "mouse" else "Cxcl12"
    gene_c = "ACTA2" if reference_species != "mouse" else "Acta2"
    gene_d = "KRT19" if reference_species != "mouse" else "Krt19"
    gene_e = "EPCAM" if reference_species != "mouse" else "Epcam"
    species = "human" if reference_species != "mouse" else "mouse"
    return pd.DataFrame(
        [
            {
                "signature_id": "CAF.Elyada19.iCAF",
                "signature_name": "iCAF",
                "source": "Elyada19",
                "source_author": "Elyada",
                "source_pmid": "31197017",
                "source_doi": None,
                "species": species,
                "species_original": species,
                "gene": gene_a,
                "gene_original": gene_a,
                "weight": None,
                "cell_family": "fibroblast",
                "context": "cancer",
                "disease": "PDAC",
                "tags": "CAF",
                "homology_relation": "same_species",
                "homology_db_class_key": None,
            },
            {
                "signature_id": "CAF.Elyada19.iCAF",
                "signature_name": "iCAF",
                "source": "Elyada19",
                "source_author": "Elyada",
                "source_pmid": "31197017",
                "source_doi": None,
                "species": species,
                "species_original": species,
                "gene": gene_b,
                "gene_original": gene_b,
                "weight": None,
                "cell_family": "fibroblast",
                "context": "cancer",
                "disease": "PDAC",
                "tags": "CAF",
                "homology_relation": "same_species",
                "homology_db_class_key": None,
            },
            {
                "signature_id": "CAF.Elyada19.myo",
                "signature_name": "myo",
                "source": "Elyada19",
                "source_author": "Elyada",
                "source_pmid": "31197017",
                "source_doi": None,
                "species": species,
                "species_original": species,
                "gene": gene_c,
                "gene_original": gene_c,
                "weight": None,
                "cell_family": "fibroblast",
                "context": "cancer",
                "disease": "PDAC",
                "tags": "CAF",
                "homology_relation": "same_species",
                "homology_db_class_key": None,
            },
            {
                "signature_id": "PDAC.PAMG20.PDX",
                "signature_name": "PDX",
                "source": "PAMG20",
                "source_author": "PDACMolGrad",
                "source_pmid": None,
                "source_doi": "10.1016/j.ebiom.2020.102858",
                "species": species,
                "species_original": species,
                "gene": gene_d,
                "gene_original": gene_d,
                "weight": 1.5,
                "cell_family": "tumor",
                "context": "cancer",
                "disease": "PDAC",
                "tags": "PDAC;model;continuous",
                "homology_relation": "same_species",
                "homology_db_class_key": None,
            },
            {
                "signature_id": "PDAC.PAMG20.PDX",
                "signature_name": "PDX",
                "source": "PAMG20",
                "source_author": "PDACMolGrad",
                "source_pmid": None,
                "source_doi": "10.1016/j.ebiom.2020.102858",
                "species": species,
                "species_original": species,
                "gene": gene_e,
                "gene_original": gene_e,
                "weight": -0.25,
                "cell_family": "tumor",
                "context": "cancer",
                "disease": "PDAC",
                "tags": "PDAC;model;continuous",
                "homology_relation": "same_species",
                "homology_db_class_key": None,
            },
        ]
    )


def test_get_signatures_returns_dict(monkeypatch):
    monkeypatch.setattr(query_mod, "read_database", lambda reference_species="human": _fake_core_read(reference_species=reference_species))
    signatures = get_signatures()
    assert set(signatures) == {"CAF.Elyada19.iCAF", "CAF.Elyada19.myo", "PDAC.PAMG20.PDX"}
    assert signatures["CAF.Elyada19.iCAF"] == ["COL1A1", "CXCL12"]
    assert signatures["PDAC.PAMG20.PDX"] == {"EPCAM": -0.25, "KRT19": 1.5}


def test_list_signatures_returns_simple_metadata_table(monkeypatch):
    monkeypatch.setattr(query_mod, "read_database", lambda reference_species="human": _fake_core_read(reference_species=reference_species))
    metadata = list_signatures()

    assert list(metadata["signature_id"]) == ["CAF.Elyada19.iCAF", "CAF.Elyada19.myo", "PDAC.PAMG20.PDX"]
    assert list(metadata.columns) == [
        "signature_id",
        "signature_name",
        "domain",
        "source",
        "collection",
        "source_resource",
        "signature_format",
        "species",
        "cell_family",
        "context",
        "disease",
        "n_genes",
    ]
    assert set(metadata["domain"]) == {"CAF", "PDAC"}
    assert set(metadata["source"]) == {"Elyada19", "PAMG20"}
    assert set(metadata["collection"]) == {"curated"}
    assert set(metadata["source_resource"]) == {"curated"}
    assert set(metadata["signature_format"]) == {"binary", "continuous"}
    assert metadata["n_genes"].tolist() == [2, 1, 2]


def test_get_signatures_accepts_signature_id_vector(monkeypatch):
    monkeypatch.setattr(query_mod, "read_database", lambda reference_species="human": _fake_core_read(reference_species=reference_species))
    selected_ids = ["PDAC.PAMG20.PDX", "CAF.Elyada19.myo", "CAF.Elyada19.iCAF"]

    as_dict = get_signatures(selected_ids)
    assert list(as_dict) == selected_ids
    assert as_dict["CAF.Elyada19.myo"] == ["ACTA2"]
    assert as_dict["CAF.Elyada19.iCAF"] == ["COL1A1", "CXCL12"]
    assert as_dict["PDAC.PAMG20.PDX"] == {"EPCAM": -0.25, "KRT19": 1.5}
