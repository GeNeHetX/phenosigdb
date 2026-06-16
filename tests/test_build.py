import pandas as pd

from phenosigdb.build import build_database
from phenosigdb.io import CANONICAL_COLUMNS, PARQUET_PATH


def test_build_succeeds():
    frame = build_database()

    assert not frame.empty
    assert frame.columns.tolist() == CANONICAL_COLUMNS
    assert PARQUET_PATH.exists()
    assert not pd.read_parquet(PARQUET_PATH).empty
    assert frame["signature_id"].nunique() >= 500
