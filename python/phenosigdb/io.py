from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

try:  # pragma: no cover - dependency fallback
    from platformdirs import user_cache_dir as _user_cache_dir
except ImportError:  # pragma: no cover - dependency fallback
    def _user_cache_dir(appname: str) -> str:
        return str(Path.home() / ".cache" / appname)

from ._download import download_to_path

REPOSITORY = "GeNeHetX/phenosigdb"
REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_SIGNATURE_DATA_DIR = REPO_ROOT / "signatures" / "data"

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


def _cache_root() -> Path:
    override = os.getenv("PHENOSIGDB_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(_user_cache_dir("phenosigdb")).expanduser().resolve()


def parquet_filename(reference_species: str = "human") -> str:
    if reference_species == "original":
        return "phenosigdb.parquet"
    if reference_species == "human":
        return "phenosigdb_human.parquet"
    if reference_species == "mouse":
        return "phenosigdb_mouse.parquet"
    raise ValueError("reference_species must be one of: original, human, mouse")


def _repo_data_path(reference_species: str = "human") -> Path:
    return REPO_SIGNATURE_DATA_DIR / parquet_filename(reference_species)


def _cached_data_path(reference_species: str = "human") -> Path:
    return _cache_root() / "curated" / parquet_filename(reference_species)


def _data_url(reference_species: str = "human") -> str:
    filename = parquet_filename(reference_species)
    explicit = os.getenv(f"PHENOSIGDB_DATA_URL_{reference_species.upper()}")
    if explicit:
        return explicit
    base = os.getenv("PHENOSIGDB_DATA_BASE_URL")
    if base:
        return base.rstrip("/") + "/" + filename
    ref = os.getenv("PHENOSIGDB_DATA_REF", "main")
    return f"https://raw.githubusercontent.com/{REPOSITORY}/{ref}/signatures/data/{filename}"


def ensure_database_path(reference_species: str = "human") -> Path:
    repo_path = _repo_data_path(reference_species)
    if repo_path.exists():
        return repo_path

    cache_path = _cached_data_path(reference_species)
    if cache_path.exists():
        return cache_path

    return download_to_path(_data_url(reference_species), cache_path)


def read_database(reference_species: str = "human") -> pd.DataFrame:
    return pd.read_parquet(ensure_database_path(reference_species=reference_species))
