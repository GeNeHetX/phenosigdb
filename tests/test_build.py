import pandas as pd
from pathlib import Path

from phenosigdb.build import build_database
from phenosigdb.io import CANONICAL_COLUMNS, HUMAN_PARQUET_PATH, MOUSE_PARQUET_PATH, PARQUET_PATH, REFERENCE_METADATA_PATH


def test_build_succeeds():
    frame = build_database()

    assert not frame.empty
    assert frame.columns.tolist() == CANONICAL_COLUMNS
    assert PARQUET_PATH.exists()
    assert not pd.read_parquet(PARQUET_PATH).empty
    assert frame["signature_id"].nunique() >= 500


def test_build_writes_translated_references_with_homology(tmp_path: Path):
    curation_dir = tmp_path / "curation"
    source_dir = curation_dir / "TEST.Source01"
    source_dir.mkdir(parents=True)
    (source_dir / "source.yaml").write_text(
        "\n".join(
            [
                "source: Test.etal",
                "species: human",
                "cell_family: fibroblast",
                "context: cancer",
                "disease: PDAC",
                "tags: CAF",
                "source_author: Test.etal",
                "source_pmid: ''",
                "source_doi: ''",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (source_dir / "members.tsv").write_text(
        "signature_id\tsignature_name\tgene\n"
        "TEST.Source01.A\tA\tCOL1A1\n"
        "TEST.Source01.A\tA\tHSD3B1\n"
        "TEST.Source01.A\tA\tHSD3B2\n",
        encoding="utf-8",
    )
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
    data_dir = tmp_path / "data"

    build_database(curation_dir=curation_dir, data_dir=data_dir, homology_path_value=homology)

    assert (data_dir / PARQUET_PATH.name).exists()
    assert (data_dir / HUMAN_PARQUET_PATH.name).exists()
    assert (data_dir / MOUSE_PARQUET_PATH.name).exists()
    assert (data_dir / REFERENCE_METADATA_PATH.name).exists()

    mouse = pd.read_parquet(data_dir / MOUSE_PARQUET_PATH.name)
    assert set(mouse["gene"]) == {"Col1a1", "Hsd3b8"}
