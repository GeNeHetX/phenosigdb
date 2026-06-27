from pathlib import Path

import pandas as pd

from phenosigdb.build import build_database
from phenosigdb.homology import ortholog_table, translate_reference
from phenosigdb.io import CANONICAL_COLUMNS
from phenosigdb.query import phenosig


def test_parquet_readable():
    build_database()
    table = phenosig(cell_family="fibroblast", format="table")
    assert not table.empty
    assert set(table.columns) == {
        "signature_id",
        "signature_name",
        "source",
        "source_author",
        "source_pmid",
        "source_doi",
        "species",
        "species_original",
        "gene",
        "gene_original",
        "cell_family",
        "context",
        "disease",
        "tags",
        "homology_relation",
        "homology_db_class_key",
    }


def test_query_api_works():
    build_database()
    as_dict = phenosig(query="Elyada", format="dict")
    assert "CAF.Elyada19.iCAF" in as_dict
    assert "CAF.Elyada19.myo" in as_dict
    assert all(isinstance(genes, list) and genes for genes in as_dict.values())

    metadata = phenosig(source="Elyada.etal;PMID:31197017", format="metadata")
    assert list(metadata["signature_id"]) == ["CAF.Elyada19.iCAF", "CAF.Elyada19.myo"]
    assert "species_original" in metadata.columns

    table = phenosig(query="CAF", format="table", reference_species="original")
    assert not table.empty


def test_translate_reference_split_and_collapse(tmp_path: Path):
    homology = tmp_path / "homology.tsv"
    homology.write_text(
        "\t".join(["DB Class Key", "Common Organism Name", "NCBI Taxon ID", "Symbol"]) + "\n"
        + "\t".join(["1", "mouse, laboratory", "10090", "Col1a1"]) + "\n"
        + "\t".join(["1", "human", "9606", "COL1A1"]) + "\n"
        + "\t".join(["2", "mouse, laboratory", "10090", "Hsd3b8"]) + "\n"
        + "\t".join(["2", "human", "9606", "HSD3B1"]) + "\n"
        + "\t".join(["2", "human", "9606", "HSD3B2"]) + "\n",
        encoding="utf-8",
    )
    frame = pd.DataFrame(
        [
            ["S1", "S1", "x", "x", "", "", "human", "human", "COL1A1", "COL1A1", "fibroblast", "cancer", "PDAC", "CAF", "same_species", ""],
            ["S1", "S1", "x", "x", "", "", "human", "human", "HSD3B1", "HSD3B1", "fibroblast", "cancer", "PDAC", "CAF", "same_species", ""],
            ["S1", "S1", "x", "x", "", "", "human", "human", "HSD3B2", "HSD3B2", "fibroblast", "cancer", "PDAC", "CAF", "same_species", ""],
        ],
        columns=CANONICAL_COLUMNS,
    )

    translated, summary, stats = translate_reference(frame, target_species="mouse", homology_path_value=homology)
    assert set(translated["gene"]) == {"Col1a1", "Hsd3b8"}
    collapsed = translated.loc[translated["gene"] == "Hsd3b8"].iloc[0]
    assert collapsed["gene_original"] == "HSD3B1;HSD3B2"
    assert summary["collapse_removed_rows"] == 1
    assert summary["collapse_output_rows"] == 1
    assert int(stats.loc[stats["signature_id"] == "S1", "max_collapse_size"].iloc[0]) == 2


def test_ortholog_table_builds_directional_relations(tmp_path: Path):
    homology = tmp_path / "homology.tsv"
    homology.write_text(
        "\t".join(["DB Class Key", "Common Organism Name", "NCBI Taxon ID", "Symbol"]) + "\n"
        + "\t".join(["1", "mouse, laboratory", "10090", "Col1a1"]) + "\n"
        + "\t".join(["1", "human", "9606", "COL1A1"]) + "\n"
        + "\t".join(["2", "mouse, laboratory", "10090", "Hsd3b8"]) + "\n"
        + "\t".join(["2", "human", "9606", "HSD3B1"]) + "\n"
        + "\t".join(["2", "human", "9606", "HSD3B2"]) + "\n",
        encoding="utf-8",
    )
    table = ortholog_table(path=homology)
    mouse_rel = set(table.loc[table["source_species"] == "mouse", "relation"])
    human_rel = set(table.loc[table["source_species"] == "human", "relation"])
    assert "one_to_many" in mouse_rel
    assert "many_to_one" in human_rel
