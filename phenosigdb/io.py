from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CURATION_DIR = ROOT / "curation"
DATA_DIR = ROOT / "data"
PARQUET_PATH = DATA_DIR / "phenosigdb.parquet"
CSV_PATH = DATA_DIR / "phenosigdb.csv.gz"

CANONICAL_COLUMNS = [
    "signature_id",
    "signature_name",
    "source",
    "species",
    "gene",
    "cell_family",
    "context",
    "disease",
    "tags",
]

ALLOWED_SPECIES = {"human", "mouse", "mixed", "unknown"}
ALLOWED_CELL_FAMILY = {
    "fibroblast",
    "endothelial",
    "epithelial",
    "tumor",
    "macrophage",
    "monocyte",
    "neutrophil",
    "T_cell",
    "B_cell",
    "plasma_cell",
    "NK_cell",
    "immune",
    "stromal",
    "ductal",
    "acinar",
    "endocrine",
    "pericyte",
    "smooth_muscle",
    "neuron",
    "glial",
    "unknown",
}
ALLOWED_CONTEXT = {
    "physiology",
    "development",
    "inflammation",
    "fibrosis",
    "cancer",
    "treatment",
    "organoid",
    "unknown",
}


def repo_root() -> Path:
    return ROOT


def canonical_columns() -> list[str]:
    return list(CANONICAL_COLUMNS)


def read_database(path: str | Path | None = None) -> pd.DataFrame:
    target = Path(path) if path is not None else PARQUET_PATH
    return pd.read_parquet(target)


def write_database(df: pd.DataFrame, data_dir: str | Path | None = None) -> tuple[Path, Path]:
    target_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = target_dir / PARQUET_PATH.name
    csv_path = target_dir / CSV_PATH.name

    ordered = df.loc[:, CANONICAL_COLUMNS]
    ordered.to_parquet(parquet_path, index=False)
    ordered.to_csv(csv_path, index=False, compression="gzip")
    return parquet_path, csv_path


def normalize_blank(value):
    if value is None:
        return None
    if pd.isna(value):
        return None
    text = str(value).strip()
    return None if text == "" else text


def normalize_tags(value: str | None) -> str | None:
    text = normalize_blank(value)
    if text is None:
        return None
    tokens: list[str] = []
    seen: set[str] = set()
    for token in (part.strip() for part in text.split(";")):
        if not token:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        tokens.append(token)
    return ";".join(tokens) if tokens else None
