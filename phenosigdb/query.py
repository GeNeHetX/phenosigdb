from __future__ import annotations

import pandas as pd

from .io import read_database

SIGNATURE_METADATA_COLUMNS = [
    "signature_id",
    "signature_name",
    "domain",
    "source",
    "source_author",
    "source_pmid",
    "source_doi",
    "species",
    "species_original",
    "cell_family",
    "context",
    "disease",
    "tags",
    "n_genes",
]

SIGNATURE_SEARCH_COLUMNS = [
    "signature_id",
    "signature_name",
    "domain",
    "source",
    "source_author",
    "source_pmid",
    "source_doi",
    "species",
    "species_original",
    "cell_family",
    "context",
    "disease",
    "tags",
]


def _contains(series: pd.Series, query: str) -> pd.Series:
    return series.fillna("").astype(str).str.contains(query, case=False, regex=False)


def _exact(series: pd.Series, value: str) -> pd.Series:
    return series.fillna("").astype(str).str.casefold() == value.casefold()


def _read_frame(path=None, reference_species="original") -> pd.DataFrame:
    return read_database(path=path, reference_species=reference_species)


def _normalize_signature_ids(signature_ids) -> list[str] | None:
    if signature_ids is None:
        return None
    if isinstance(signature_ids, str):
        values = [signature_ids]
    else:
        values = list(signature_ids)
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if pd.isna(value):
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized


def _signature_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = [
        "signature_name",
        "source",
        "source_author",
        "source_pmid",
        "source_doi",
        "species",
        "species_original",
        "cell_family",
        "context",
        "disease",
        "tags",
    ]
    aggregations = {column: (column, "first") for column in metadata_columns if column in frame.columns}
    meta = frame.groupby("signature_id", as_index=False, sort=True).agg(**aggregations)
    counts = frame.groupby("signature_id", as_index=False, sort=True)["gene"].nunique()
    counts.rename(columns={"gene": "n_genes"}, inplace=True)
    meta = meta.merge(counts, on="signature_id", how="left", sort=False)
    meta.insert(2, "domain", meta["signature_id"].str.split(".", n=1).str[0])
    columns = [column for column in SIGNATURE_METADATA_COLUMNS if column in meta.columns]
    meta = meta.loc[:, columns]
    meta.sort_values("signature_id", inplace=True, kind="stable")
    meta.reset_index(drop=True, inplace=True)
    return meta


def _apply_signature_query(frame: pd.DataFrame, query) -> pd.DataFrame:
    if query is None:
        return frame.reset_index(drop=True)
    query_text = str(query)
    mask = pd.Series(False, index=frame.index)
    for column in SIGNATURE_SEARCH_COLUMNS:
        if column in frame.columns:
            mask |= _contains(frame[column], query_text)
    return frame.loc[mask].reset_index(drop=True)


def _order_signature_rows(frame: pd.DataFrame, signature_ids: list[str] | None) -> pd.DataFrame:
    if signature_ids is None:
        ordered = frame.sort_values(["signature_id", "gene"], kind="stable")
    else:
        signature_order = {signature_id: position for position, signature_id in enumerate(signature_ids)}
        ordered = frame.loc[frame["signature_id"].isin(signature_order)].copy()
        ordered["__signature_order"] = ordered["signature_id"].map(signature_order)
        ordered.sort_values(["__signature_order", "signature_id", "gene"], inplace=True, kind="stable")
        ordered.drop(columns="__signature_order", inplace=True)
    ordered.reset_index(drop=True, inplace=True)
    return ordered


def list_signatures(query=None, reference_species="original", path=None) -> pd.DataFrame:
    frame = _read_frame(path=path, reference_species=reference_species)
    meta = _signature_metadata(frame)
    return _apply_signature_query(meta, query)


def get_signatures(signature_ids=None, format="dict", reference_species="original", path=None):
    ordered_ids = _normalize_signature_ids(signature_ids)
    frame = _read_frame(path=path, reference_species=reference_species)
    subset = _order_signature_rows(frame, signature_ids=ordered_ids)

    if format == "table":
        return subset
    if format == "dict":
        grouped = subset.groupby("signature_id", sort=False)["gene"]
        signatures = {signature_id: pd.unique(genes).tolist() for signature_id, genes in grouped}
        if ordered_ids is None:
            return signatures
        return {signature_id: signatures[signature_id] for signature_id in ordered_ids if signature_id in signatures}
    raise ValueError("format must be one of: dict, table")


def phenosig(
    query=None,
    cell_family=None,
    context=None,
    disease=None,
    tags=None,
    source=None,
    format="dict",
    reference_species="original",
    path=None,
):
    frame = _read_frame(path=path, reference_species=reference_species)

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
        return _signature_metadata(subset)
    if format == "dict":
        return {signature_id: pd.unique(group["gene"]).tolist() for signature_id, group in subset.groupby("signature_id", sort=True)}
    raise ValueError("format must be one of: dict, table, metadata")
