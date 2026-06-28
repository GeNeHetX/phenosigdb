import re
from pathlib import Path

import pandas as pd

from phenosigdb_maintainer.build import build_database
from phenosigdb_maintainer.homology import ortholog_table, translate_reference
from phenosigdb_maintainer.io import CANONICAL_COLUMNS


def test_all_signature_ids_use_domain_sourcekey_prefix():
    frame = build_database()
    pattern = re.compile(r"^[A-Z][A-Z0-9_]*\.[A-Za-z][A-Za-z0-9]*\d{2}\..+$")
    bad = [signature_id for signature_id in sorted(set(frame["signature_id"])) if not pattern.match(signature_id)]
    assert bad == []


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
            ["S1", "S1", "x", "x", "", "", "human", "human", "COL1A1", "COL1A1", 0.5, "fibroblast", "cancer", "PDAC", "CAF", "same_species", ""],
            ["S1", "S1", "x", "x", "", "", "human", "human", "HSD3B1", "HSD3B1", 1.0, "fibroblast", "cancer", "PDAC", "CAF", "same_species", ""],
            ["S1", "S1", "x", "x", "", "", "human", "human", "HSD3B2", "HSD3B2", 2.0, "fibroblast", "cancer", "PDAC", "CAF", "same_species", ""],
        ],
        columns=CANONICAL_COLUMNS,
    )

    translated, summary, stats = translate_reference(frame, target_species="mouse", homology_path_value=homology)
    assert set(translated["gene"]) == {"Col1a1", "Hsd3b8"}
    collapsed = translated.loc[translated["gene"] == "Hsd3b8"].iloc[0]
    assert collapsed["gene_original"] == "HSD3B1;HSD3B2"
    assert collapsed["weight"] == 3.0
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
