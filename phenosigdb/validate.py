from __future__ import annotations

from pathlib import Path

import pandas as pd

from .io import (
    ALLOWED_CELL_FAMILY,
    ALLOWED_CONTEXT,
    ALLOWED_SPECIES,
    CANONICAL_COLUMNS,
    normalize_blank,
    parquet_path,
    read_database,
)

def _missing_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in CANONICAL_COLUMNS if column not in frame.columns]


def validate_database(data: str | Path | pd.DataFrame | None = None, reference_species: str = "original") -> pd.DataFrame:
    if data is None:
        frame = read_database(reference_species=reference_species)
    elif isinstance(data, pd.DataFrame):
        frame = data.copy()
    else:
        frame = read_database(path=data)

    missing = _missing_columns(frame)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    extras = [column for column in frame.columns if column not in CANONICAL_COLUMNS]
    if extras:
        raise ValueError(f"Unexpected columns present: {', '.join(extras)}")

    for column in ("signature_id", "signature_name", "gene", "source"):
        empty = frame[column].map(normalize_blank).isna()
        if empty.any():
            count = int(empty.sum())
            raise ValueError(f"Column '{column}' contains {count} missing or empty values")

    duplicates = frame.duplicated(subset=["signature_id", "gene"])
    if duplicates.any():
        dup_rows = frame.loc[duplicates, ["signature_id", "gene"]].head(5).to_dict(orient="records")
        raise ValueError(f"Duplicate signature_id + gene pairs detected: {dup_rows}")

    for column, allowed in (
        ("species", ALLOWED_SPECIES),
        ("species_original", ALLOWED_SPECIES),
        ("cell_family", ALLOWED_CELL_FAMILY),
        ("context", ALLOWED_CONTEXT),
    ):
        values = {
            value
            for value in frame[column].map(normalize_blank)
            if value is not None
        }
        invalid = sorted(values.difference(allowed))
        if invalid:
            raise ValueError(f"Invalid values in {column}: {', '.join(invalid)}")

    for column in ("gene_original", "homology_relation"):
        empty = frame[column].map(normalize_blank).isna()
        if empty.any():
            count = int(empty.sum())
            raise ValueError(f"Column '{column}' contains {count} missing or empty values")

    if reference_species in {"human", "mouse"}:
        species_values = {value for value in frame["species"].map(normalize_blank) if value is not None}
        invalid = sorted(species_values.difference({reference_species}))
        if invalid:
            raise ValueError(f"Translated reference contains non-{reference_species} species values: {', '.join(invalid)}")

    return frame


def main() -> None:
    validate_database(reference_species="original")
    for ref in ("human", "mouse"):
        path = parquet_path(reference_species=ref)
        if path.exists():
            validate_database(path, reference_species=ref)
