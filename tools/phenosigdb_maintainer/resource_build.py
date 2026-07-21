from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd

from phenosigdb._version import __version__
from phenosigdb.resources import (
    BINARY_TABLE_COLUMNS,
    CONTINUOUS_TABLE_COLUMNS,
    RESOURCE_METADATA_COLUMNS,
    RESOURCE_SPECS,
    normalize_resource_signature_id,
)
from .external_imports.utils import infer_cell_family, normalize_blank, normalize_gene_symbol, normalize_whitespace


def _resource_staging_dir(resource: str, staging_root: str | Path | None = None) -> Path:
    if staging_root is not None:
        return Path(staging_root)
    base = Path(__file__).resolve().parents[2] / "data" / "external_imports" / resource
    latest_path = base / "latest.json"
    if not latest_path.exists():
        raise FileNotFoundError(f"No staged import found for {resource}: {latest_path}")
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    version_key = latest.get("version_key")
    if not version_key:
        raise ValueError(f"Invalid latest.json for {resource}: missing version_key")
    return base / str(version_key)


def _safe_text(value: Any, default: str = "unknown") -> str:
    text = normalize_whitespace(value)
    return text if text else default


def _public_domain_source(signature_id: str, fallback_source: str) -> tuple[str, str]:
    parts = str(signature_id).split(".", 2)
    domain = parts[0] if parts else "unknown"
    return domain, fallback_source


def build_runtime_celltypist(staging_root: str | Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    staged_dir = _resource_staging_dir("celltypist", staging_root=staging_root)
    signatures = pd.read_parquet(staged_dir / "signatures.parquet")
    members = pd.read_parquet(staged_dir / "members.parquet")
    manifest = json.loads((staged_dir / "manifest.json").read_text(encoding="utf-8"))

    signatures = signatures.copy()
    signatures["runtime_signature_id"] = signatures.apply(
        lambda row: normalize_resource_signature_id(
            "CELLTYPIST",
            row.get("dataset_id") or row.get("dataset_name") or row.get("source_identifier") or "unknown",
            row.get("cell_type_original") or row.get("signature_name") or "unknown",
        ),
        axis=1,
    )
    signature_map = dict(zip(signatures["signature_id"], signatures["runtime_signature_id"]))

    continuous = members.loc[members["weight"].notna()].copy()
    continuous = continuous.loc[continuous["weight"].astype(float) != 0.0].copy()
    continuous["signature_id"] = continuous["signature_id"].map(signature_map)
    continuous = continuous.loc[:, ["signature_id", "gene", "weight"]]
    continuous["weight"] = continuous["weight"].astype("float32")
    continuous.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    continuous = continuous.drop_duplicates(subset=["signature_id", "gene"], keep="first")
    continuous.reset_index(drop=True, inplace=True)

    counts = continuous.groupby("signature_id", as_index=False)["gene"].nunique().rename(columns={"gene": "n_genes"})
    metadata = signatures.copy()
    metadata["signature_id"] = metadata["runtime_signature_id"]
    metadata = metadata.merge(counts, on="signature_id", how="left", sort=False)
    metadata["n_genes"] = metadata["n_genes"].fillna(0).astype(int)
    metadata["domain"] = "CELLTYPIST"
    metadata["source"] = metadata["dataset_id"].fillna(metadata["dataset_name"]).fillna("unknown")
    metadata["collection"] = metadata["dataset_id"].fillna(metadata["dataset_name"]).fillna("unknown")
    metadata["source_resource"] = "celltypist"
    metadata["resource_key"] = "celltypist"
    metadata["signature_format"] = "continuous"
    metadata["source_version"] = metadata["resource_version"]
    metadata["source_label"] = metadata["source_label"]
    metadata["source_pmid"] = metadata["source_pmid"]
    metadata["source_doi"] = metadata["source_doi"]
    metadata["source_url"] = metadata["source_url"]
    metadata["original_source"] = metadata["dataset_name"].fillna(metadata["dataset_id"]).fillna("unknown")
    metadata["original_signature_name"] = metadata["cell_type_original"].fillna(metadata["signature_name"])
    metadata["resource_metadata_json"] = metadata["signature_metadata_json"]
    for column in ("signature_name", "species", "species_original", "cell_family", "context", "disease", "cell_ontology_id", "annotation_level"):
        metadata[column] = metadata[column].where(metadata[column].notna(), None)
    metadata = metadata.loc[:, RESOURCE_METADATA_COLUMNS].copy()
    metadata.sort_values("signature_id", inplace=True, kind="stable")
    metadata.reset_index(drop=True, inplace=True)

    resource_json = {
        "resource": "celltypist",
        "version": manifest.get("resource_version"),
        "signature_format": "continuous",
        "n_signatures": int(metadata["signature_id"].nunique()),
        "n_rows": int(len(continuous)),
        "package_version": __version__,
        "source_manifest_path": str(staged_dir / "manifest.json"),
        "source_resource": "celltypist",
    }
    return metadata, continuous, resource_json


def build_runtime_cellmarker(staging_root: str | Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    staged_dir = _resource_staging_dir("cellmarker", staging_root=staging_root)
    signatures = pd.read_parquet(staged_dir / "signatures.parquet")
    members = pd.read_parquet(staged_dir / "members.parquet")
    manifest = json.loads((staged_dir / "manifest.json").read_text(encoding="utf-8"))

    signature_cols = [
        "signature_id",
        "resource_version",
        "species",
        "species_original",
        "tissue",
        "organ",
        "disease",
        "context",
        "cell_family",
        "cell_type",
        "cell_type_original",
        "cell_ontology_id",
        "annotation_level",
        "source_pmid",
        "source_doi",
        "source_url",
        "source_record_id",
        "source_identifier",
        "source_label",
        "signature_metadata_json",
    ]
    merged = members.merge(signatures.loc[:, signature_cols], on="signature_id", how="left", sort=False)
    merged["species"] = merged["species"].map(lambda x: _safe_text(x))
    merged["species_original"] = merged["species_original"].map(lambda x: _safe_text(x))
    merged["tissue_or_organ"] = merged["tissue"].map(normalize_whitespace)
    missing_tissue = merged["tissue_or_organ"].isna() | merged["tissue_or_organ"].eq("")
    merged.loc[missing_tissue, "tissue_or_organ"] = merged.loc[missing_tissue, "organ"].map(normalize_whitespace)
    merged["tissue_or_organ"] = merged["tissue_or_organ"].map(lambda x: _safe_text(x))
    merged["disease"] = merged["disease"].map(lambda x: _safe_text(x))
    merged["cell_type"] = merged["cell_type"].map(lambda x: _safe_text(x))

    group_cols = ["species", "species_original", "tissue_or_organ", "disease", "cell_type"]
    metadata_rows: list[dict[str, Any]] = []
    binary_rows: list[dict[str, Any]] = []
    for _, group in merged.groupby(group_cols, dropna=False, sort=True):
        first = group.iloc[0]
        source_key = "__".join(
            [
                _safe_text(first["species"]),
                _safe_text(first["tissue_or_organ"]),
                _safe_text(first["disease"]),
            ]
        )
        signature_id = normalize_resource_signature_id("CELLMARKER", source_key, first["cell_type"])
        genes = sorted(
            {
                gene
                for gene in group["gene"].astype(str).tolist()
                if normalize_blank(gene) is not None
            }
        )
        if not genes:
            continue

        resource_meta = {
            "publication_count": int(group["source_pmid"].fillna("").astype(str).replace("", pd.NA).dropna().nunique()),
            "pmids": sorted({pmid for pmid in group["source_pmid"].astype(str).tolist() if normalize_blank(pmid) is not None}),
            "source_record_ids": sorted({str(value) for value in group["source_record_id"].astype(str).tolist() if normalize_blank(value) is not None}),
            "source_identifiers": sorted({str(value) for value in group["source_identifier"].astype(str).tolist() if normalize_blank(value) is not None}),
            "cell_ontology_ids": sorted({str(value) for value in group["cell_ontology_id"].astype(str).tolist() if normalize_blank(value) is not None}),
        }

        metadata_rows.append(
            {
                "signature_id": signature_id,
                "signature_name": first["cell_type"],
                "domain": "CELLMARKER",
                "source": source_key,
                "collection": "grouped",
                "source_resource": "cellmarker",
                "resource_key": "cellmarker",
                "signature_format": "binary",
                "species": first["species"],
                "species_original": first["species_original"],
                "cell_family": first["cell_family"] or infer_cell_family(first["cell_type"], first["tissue_or_organ"]),
                "context": first["context"] or "unknown",
                "disease": first["disease"],
                "n_genes": len(genes),
                "source_version": first["resource_version"],
                "source_label": first["source_label"],
                "source_pmid": ";".join(resource_meta["pmids"]) or None,
                "source_doi": first["source_doi"],
                "source_url": first["source_url"],
                "original_source": first["tissue_or_organ"],
                "original_signature_name": first["cell_type_original"] or first["cell_type"],
                "cell_ontology_id": ";".join(resource_meta["cell_ontology_ids"]) or first["cell_ontology_id"],
                "annotation_level": first["annotation_level"],
                "resource_metadata_json": json.dumps(resource_meta),
            }
        )
        for gene in genes:
            binary_rows.append({"signature_id": signature_id, "gene": gene})

    metadata = pd.DataFrame(metadata_rows, columns=RESOURCE_METADATA_COLUMNS)
    metadata.sort_values("signature_id", inplace=True, kind="stable")
    metadata.reset_index(drop=True, inplace=True)

    binary = pd.DataFrame(binary_rows, columns=BINARY_TABLE_COLUMNS)
    binary.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    binary.reset_index(drop=True, inplace=True)

    resource_json = {
        "resource": "cellmarker",
        "version": manifest.get("resource_version"),
        "signature_format": "binary",
        "n_signatures": int(metadata["signature_id"].nunique()),
        "n_rows": int(len(binary)),
        "package_version": __version__,
        "source_manifest_path": str(staged_dir / "manifest.json"),
        "source_resource": "cellmarker",
    }
    return metadata, binary, resource_json


RUNTIME_BUILDERS = {
    "celltypist": build_runtime_celltypist,
    "cellmarker": build_runtime_cellmarker,
}


def build_runtime_resource_dir(resource: str, output_dir: str | Path, staging_root: str | Path | None = None) -> Path:
    resource_key = resource.strip().casefold()
    if resource_key not in RESOURCE_SPECS:
        raise KeyError(f"Unknown runtime resource: {resource}")
    builder = RUNTIME_BUILDERS[resource_key]
    metadata, values, resource_json = builder(staging_root=staging_root)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    metadata.to_parquet(out / "metadata.parquet", index=False, compression="zstd")
    if resource_key == "celltypist":
        values.to_parquet(out / "continuous.parquet", index=False, compression="zstd")
    else:
        values.to_parquet(out / "binary.parquet", index=False, compression="zstd")
    resource_json["files"] = sorted(path.name for path in out.iterdir() if path.is_file())
    (out / "resource.json").write_text(json.dumps(resource_json, indent=2) + "\n", encoding="utf-8")
    return out


def package_runtime_resource(resource: str, archive_path: str | Path, staging_root: str | Path | None = None) -> Path:
    resource_key = resource.strip().casefold()
    with tempfile.TemporaryDirectory(prefix=f"phenosigdb-package-{resource_key}-") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        resource_dir = build_runtime_resource_dir(resource_key, tmp_dir / resource_key, staging_root=staging_root)
        archive = Path(archive_path)
        archive.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "w:gz") as handle:
            handle.add(resource_dir, arcname=resource_key)
    return Path(archive_path)
