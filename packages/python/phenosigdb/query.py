from __future__ import annotations

import re
import warnings

import pandas as pd

from .io import read_database
from .resources import ALLOWED_REFERENCE_SPECIES, PUBLIC_METADATA_COLUMNS, ensure_optional_resource_available, installed_resource_metadata, installed_resource_values

DEFAULT_REFERENCE_SPECIES = "human"

BROWSE_METADATA_COLUMNS = [
    "signature_id",
    "signature_name",
    "source",
    "domain",
    "species",
    "cell_family",
    "context",
    "disease",
    "signature_format",
    "n_genes",
]

SIGNATURE_METADATA_COLUMNS = list(BROWSE_METADATA_COLUMNS)

DEFAULT_SEARCH_COLUMNS = [
    "signature_id",
    "signature_name",
    "source",
    "domain",
    "cell_family",
    "context",
    "disease",
]

def _read_core_frame(reference_species=DEFAULT_REFERENCE_SPECIES) -> pd.DataFrame:
    return read_database(reference_species=reference_species)


def _normalize_signature_ids(signature_ids) -> list[str] | None:
    if signature_ids is None:
        return None
    if isinstance(signature_ids, pd.DataFrame):
        if "signature_id" not in signature_ids.columns:
            raise ValueError("signature table must contain a 'signature_id' column")
        values = signature_ids["signature_id"].tolist()
    elif isinstance(signature_ids, str):
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


def _core_signature_metadata(frame: pd.DataFrame) -> pd.DataFrame:
    metadata_columns = [
        "signature_name",
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
    if "weight" in frame.columns:
        formats = (
            frame.assign(__has_weight=frame["weight"].notna())
            .groupby("signature_id", as_index=False, sort=True)["__has_weight"]
            .any()
            .rename(columns={"__has_weight": "signature_format"})
        )
        formats["signature_format"] = formats["signature_format"].map(lambda value: "continuous" if value else "binary")
        meta = meta.merge(formats, on="signature_id", how="left", sort=False)
    else:
        meta["signature_format"] = "binary"
    id_parts = meta["signature_id"].str.split(".", n=2, expand=True)
    meta.insert(2, "domain", id_parts[0])
    meta.insert(3, "source", "curated." + id_parts[1])
    if "species_original" in meta.columns:
        meta["species"] = meta["species_original"].fillna(meta["species"])
    columns = [column for column in SIGNATURE_METADATA_COLUMNS if column in meta.columns]
    meta = meta.loc[:, columns]
    meta.sort_values("signature_id", inplace=True, kind="stable")
    meta.reset_index(drop=True, inplace=True)
    return meta


def _normalize_query(query: str) -> str:
    return str(query).strip()


def _apply_signature_query(
    frame: pd.DataFrame,
    query: str | None = None,
    columns: list[str] | None = None,
    min_genes: int | None = None,
    signature_format: str | None = None,
    regex_options: dict | None = None,
) -> pd.DataFrame:
    masks: list[pd.Series] = []
    if query is not None:
        query_text = _normalize_query(query)
        if not query_text:
            raise ValueError("query must not be empty")
        search_columns = DEFAULT_SEARCH_COLUMNS if columns is None else list(columns)
        invalid = [column for column in search_columns if column not in frame.columns]
        if invalid:
            raise ValueError(f"Unknown search column(s): {', '.join(invalid)}")
        query_masks = []
        regex_options = dict(regex_options or {})
        regex_options.setdefault("flags", re.IGNORECASE)
        pattern = re.compile(query_text, **regex_options)
        for column in search_columns:
            query_masks.append(frame[column].fillna("").astype(str).map(lambda value: bool(pattern.search(value))))
        query_mask = (pd.concat(query_masks, axis=1).any(axis=1) if query_masks else pd.Series(False, index=frame.index))
        masks.append(query_mask)
    if min_genes is not None:
        if int(min_genes) < 0:
            raise ValueError("min_genes must be non-negative")
        masks.append(frame["n_genes"].fillna(0).astype(int) >= int(min_genes))
    if signature_format is not None:
        if signature_format not in {"binary", "continuous"}:
            raise ValueError("signature_format must be 'binary' or 'continuous'")
        masks.append(frame["signature_format"].fillna("").eq(signature_format))
    if not masks:
        return frame.reset_index(drop=True)
    combined = pd.concat(masks, axis=1)
    mask = combined.all(axis=1)
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


def _validate_reference_species(reference_species: str) -> str:
    if reference_species not in ALLOWED_REFERENCE_SPECIES:
        raise ValueError(
            f"reference_species must be one of: {', '.join(sorted(ALLOWED_REFERENCE_SPECIES))}"
        )
    return reference_species


def _combined_metadata() -> pd.DataFrame:
    core = _core_signature_metadata(_read_core_frame(reference_species="original"))
    optional = installed_resource_metadata(reference_species="original")
    if optional.empty:
        return core
    columns = [column for column in SIGNATURE_METADATA_COLUMNS if column in optional.columns]
    optional = optional.loc[:, columns].copy()
    combined = pd.concat([core, optional], ignore_index=True)
    combined.sort_values("signature_id", inplace=True, kind="stable")
    combined.reset_index(drop=True, inplace=True)
    return combined


def list_signatures(
    query: str | None = None,
    columns: list[str] | None = None,
    min_genes: int | None = None,
    signature_format: str | None = None,
    **regex_options,
) -> pd.DataFrame:
    """List available signatures.

    Args:
        query: One case-insensitive regular expression. It is searched across the default columns.
        columns: Optional columns to search instead of the default search columns.
        min_genes: Optional minimum signature size.
        signature_format: Optional "binary" or "continuous" filter.
        **regex_options: Optional keyword arguments passed to Python's ``re.compile``.

    Returns:
        DataFrame with signature metadata columns.

    Raises:
        ValueError: If reference_species is not valid.
    """
    meta = _combined_metadata()
    return _apply_signature_query(meta, query, columns=columns, min_genes=min_genes,
                                  signature_format=signature_format,
                                  regex_options=regex_options)


def get_signatures(
    signature_ids: list[str] | str | None = None,
    reference_species: str = DEFAULT_REFERENCE_SPECIES,
) -> dict[str, list[str] | dict[str, float]]:
    """Get signatures by ID.

    Args:
        signature_ids: Optional signature ID or list of IDs. If None, returns all signatures.
        reference_species: One of "human", "mouse", "original".

    Returns:
        Dict mapping signature_id to gene list (binary) or dict of gene->weight (continuous).
        Binary signatures return list[str]. Continuous signatures return dict[str, float].

    Raises:
        ValueError: If reference_species is not valid.
    """
    _validate_reference_species(reference_species)
    ordered_ids = _normalize_signature_ids(signature_ids)
    if ordered_ids is not None:
        ensure_optional_resource_available(ordered_ids)
        available = _combined_metadata()
        available_ids = set(available["signature_id"])
        missing = [sid for sid in ordered_ids if sid not in available_ids]
        unknown_optional = [sid for sid in missing if any(sid.upper().startswith(prefix) for prefix in ("CELLTYPIST.", "CELL.CELLMARKER.", "MSIGDB.C7.", "MSIGDB.C8.", "PID.", "BIOCARTA.", "PATHWAY.REACTOME.", "PATHWAY.WIKIPATHWAYS."))]
        if unknown_optional:
            available = _combined_metadata()
            missing = [sid for sid in ordered_ids if sid not in set(available["signature_id"])]
        if missing:
            if len(missing) == len(ordered_ids):
                raise KeyError(f"No requested signatures found: {', '.join(missing)}")
            warnings.warn(
                f"Some requested signatures were not found: {', '.join(missing)}",
                UserWarning,
                stacklevel=2,
            )
            ordered_ids = [sid for sid in ordered_ids if sid not in missing]
        if reference_species == "original":
            selected_species = set(
                available.loc[available["signature_id"].isin(ordered_ids), "species"].dropna().astype(str).str.casefold()
            )
            if len(selected_species) > 1:
                raise ValueError(
                    "Mixed species request. Select one species or use reference_species='human' or 'mouse'."
                )
    frame = _read_core_frame(reference_species=reference_species)
    subset = _order_signature_rows(frame, signature_ids=ordered_ids)
    signatures: dict[str, list[str] | dict[str, float]] = {}
    if not subset.empty:
        if "weight" not in subset.columns:
            subset["weight"] = pd.NA
        for signature_id, group in subset.groupby("signature_id", sort=False):
            if group["weight"].notna().any():
                dedup = group.drop_duplicates(subset=["gene"], keep="first")
                signatures[str(signature_id)] = {
                    str(gene): float(weight)
                    for gene, weight in zip(dedup["gene"], dedup["weight"])
                    if pd.notna(weight)
                }
            else:
                signatures[str(signature_id)] = pd.unique(group["gene"]).tolist()

    optional = installed_resource_values(signature_ids=ordered_ids, reference_species=reference_species)
    signatures.update(optional)

    if ordered_ids is None:
        return signatures
    return {signature_id: signatures[signature_id] for signature_id in ordered_ids if signature_id in signatures}
