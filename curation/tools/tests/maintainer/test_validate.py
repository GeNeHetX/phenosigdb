import pandas as pd
import pytest

from phenosigdb_maintainer.build import build_database
from phenosigdb_maintainer.io import CANONICAL_COLUMNS, PARQUET_PATH
from phenosigdb_maintainer.validate import validate_database


def test_validate_succeeds():
    build_database()
    frame = validate_database()
    assert not frame.empty
    assert frame.columns.tolist() == CANONICAL_COLUMNS
    assert PARQUET_PATH.exists()


def test_duplicate_genes_detected():
    frame = pd.DataFrame(
        [
            {
                "signature_id": "TEST.A",
                "signature_name": "A",
                "source": "Test source",
                "source_author": "Test",
                "source_pmid": "",
                "source_doi": "",
                "species": "human",
                "species_original": "human",
                "gene": "TP53",
                "gene_original": "TP53",
                "cell_family": "tumor",
                "context": "cancer",
                "disease": "test",
                "tags": "test",
                "homology_relation": "same_species",
                "homology_db_class_key": "",
            },
            {
                "signature_id": "TEST.A",
                "signature_name": "A",
                "source": "Test source",
                "source_author": "Test",
                "source_pmid": "",
                "source_doi": "",
                "species": "human",
                "species_original": "human",
                "gene": "TP53",
                "gene_original": "TP53",
                "cell_family": "tumor",
                "context": "cancer",
                "disease": "test",
                "tags": "test",
                "homology_relation": "same_species",
                "homology_db_class_key": "",
            },
        ],
        columns=CANONICAL_COLUMNS,
    )

    with pytest.raises(ValueError, match="Duplicate signature_id \\+ gene pairs"):
        validate_database(frame)
