from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CURATION_DIR = ROOT / "curation"
SOURCE_MATERIAL_DIR = CURATION_DIR / "source_material"
DATA_DIR = ROOT / "data"
PARQUET_PATH = DATA_DIR / "phenosigdb.parquet"
HUMAN_PARQUET_PATH = DATA_DIR / "phenosigdb_human.parquet"
MOUSE_PARQUET_PATH = DATA_DIR / "phenosigdb_mouse.parquet"
CSV_PATH = DATA_DIR / "phenosigdb.csv.gz"
REFERENCE_METADATA_PATH = DATA_DIR / "phenosigdb_reference_metadata.json"

CANONICAL_COLUMNS = [
    "signature_id",
    "signature_name",
    "source",
    "source_author",
    "source_pmid",
    "source_doi",
    "species",
    "species_original",
    "gene",
    "gene_original",
    "weight",
    "cell_family",
    "context",
    "disease",
    "tags",
    "homology_relation",
    "homology_db_class_key",
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


def parquet_path(reference_species: str = "original", data_dir: str | Path | None = None) -> Path:
    target_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    if reference_species == "original":
        return target_dir / PARQUET_PATH.name
    if reference_species == "human":
        return target_dir / HUMAN_PARQUET_PATH.name
    if reference_species == "mouse":
        return target_dir / MOUSE_PARQUET_PATH.name
    raise ValueError("reference_species must be one of: original, human, mouse")


def translation_signature_stats_path(reference_species: str, data_dir: str | Path | None = None) -> Path:
    if reference_species not in {"human", "mouse"}:
        raise ValueError("translation signature stats only exist for human or mouse")
    target_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    return target_dir / f"phenosigdb_{reference_species}_translation_signature_stats.tsv"


def read_database(path: str | Path | None = None, reference_species: str = "original") -> pd.DataFrame:
    target = Path(path) if path is not None else parquet_path(reference_species)
    return pd.read_parquet(target)


def write_database(
    df: pd.DataFrame,
    data_dir: str | Path | None = None,
    reference_species: str = "original",
    write_csv: bool = False,
) -> tuple[Path, Path | None]:
    target_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    target_parquet = parquet_path(reference_species=reference_species, data_dir=target_dir)
    csv_path: Path | None = target_dir / CSV_PATH.name if write_csv else None

    ordered = df.loc[:, CANONICAL_COLUMNS]
    ordered.to_parquet(target_parquet, index=False)
    if csv_path is not None:
        ordered.to_csv(csv_path, index=False, compression="gzip")
    return target_parquet, csv_path


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
