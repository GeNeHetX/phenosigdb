from __future__ import annotations

import pandas as pd

from .io import read_database


def _contains(series: pd.Series, query: str) -> pd.Series:
    return series.fillna("").astype(str).str.contains(query, case=False, regex=False)


def _exact(series: pd.Series, value: str) -> pd.Series:
    return series.fillna("").astype(str).str.casefold() == value.casefold()


def phenosig(
    query=None,
    cell_family=None,
    context=None,
    disease=None,
    tags=None,
    source=None,
    format="dict",
    reference_species="original",
):
    frame = read_database(reference_species=reference_species)

    mask = pd.Series(True, index=frame.index)
    for column, value in (
        ("cell_family", cell_family),
        ("context", context),
        ("disease", disease),
        ("source", source),
    ):
        if value is not None:
            mask &= _exact(frame[column], str(value))

    if tags is not None:
        tag_value = str(tags).casefold()
        mask &= frame["tags"].fillna("").astype(str).map(
            lambda cell: tag_value in {part.strip().casefold() for part in cell.split(";") if part.strip()}
        )

    if query is not None:
        query_text = str(query)
        query_mask = pd.Series(False, index=frame.index)
        for column in ("signature_id", "signature_name", "source", "cell_family", "context", "disease", "tags"):
            query_mask |= _contains(frame[column], query_text)
        mask &= query_mask

    subset = frame.loc[mask].copy()
    subset.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    subset.reset_index(drop=True, inplace=True)

    if format == "table":
        return subset
    if format == "metadata":
        aggregations = {
            "signature_name": ("signature_name", "first"),
            "source": ("source", "first"),
            "species": ("species", "first"),
            "cell_family": ("cell_family", "first"),
            "context": ("context", "first"),
            "disease": ("disease", "first"),
            "tags": ("tags", "first"),
        }
        if "species_original" in subset.columns:
            aggregations["species_original"] = ("species_original", "first")
        meta = subset.groupby("signature_id", as_index=False, sort=True).agg(**aggregations)
        columns = ["signature_id", "signature_name", "source", "species"]
        if "species_original" in meta.columns:
            columns.append("species_original")
        columns.extend(["cell_family", "context", "disease", "tags"])
        meta = meta.loc[:, columns]
        return meta.reset_index(drop=True)
    if format == "dict":
        return {signature_id: group["gene"].tolist() for signature_id, group in subset.groupby("signature_id", sort=True)}
    raise ValueError("format must be one of: dict, table, metadata")
