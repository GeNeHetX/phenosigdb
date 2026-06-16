from phenosigdb.query import phenosig


def test_parquet_readable():
    table = phenosig(cell_family="fibroblast", format="table")
    assert not table.empty
    assert set(table.columns) == {
        "signature_id",
        "signature_name",
        "source",
        "species",
        "gene",
        "cell_family",
        "context",
        "disease",
        "tags",
    }


def test_query_api_works():
    as_dict = phenosig(query="Elyada", format="dict")
    assert "CAF.Elyada19.iCAF" in as_dict
    assert "CAF.Elyada19.myo" in as_dict
    assert all(isinstance(genes, list) and genes for genes in as_dict.values())

    metadata = phenosig(source="Elyada.etal;PMID:31197017", format="metadata")
    assert list(metadata["signature_id"]) == ["CAF.Elyada19.iCAF", "CAF.Elyada19.myo"]

    table = phenosig(query="CAF", format="table")
    assert not table.empty
