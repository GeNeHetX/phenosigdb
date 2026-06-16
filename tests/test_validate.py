import pandas as pd
import pytest

from phenosigdb.io import CANONICAL_COLUMNS, PARQUET_PATH
from phenosigdb.validate import validate_database


def test_validate_succeeds():
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
                "species": "human",
                "gene": "TP53",
                "cell_family": "tumor",
                "context": "cancer",
                "disease": "test",
                "tags": "test",
            },
            {
                "signature_id": "TEST.A",
                "signature_name": "A",
                "source": "Test source",
                "species": "human",
                "gene": "TP53",
                "cell_family": "tumor",
                "context": "cancer",
                "disease": "test",
                "tags": "test",
            },
        ],
        columns=CANONICAL_COLUMNS,
    )

    with pytest.raises(ValueError, match="Duplicate signature_id \\+ gene pairs"):
        validate_database(frame)
