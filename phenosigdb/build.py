from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .homology import (
    HOMOLOGY_URL,
    download_mouse_human_homology,
    homology_path,
    latest_homology_tag,
    read_homology_metadata,
    translate_reference,
)
from .io import (
    ALLOWED_CELL_FAMILY,
    ALLOWED_CONTEXT,
    ALLOWED_SPECIES,
    CANONICAL_COLUMNS,
    CURATION_DIR,
    DATA_DIR,
    REFERENCE_METADATA_PATH,
    normalize_blank,
    normalize_tags,
    translation_signature_stats_path,
    write_database,
)
from .validate import validate_database

README_START = "<!-- PHENOSIGDB_SIGNATURES_START -->"
README_END = "<!-- PHENOSIGDB_SIGNATURES_END -->"


def _display_path(path: Path) -> str:
    root = Path(__file__).resolve().parents[1]
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _load_source_defaults(source_dir: Path) -> dict[str, Any]:
    config_path = source_dir / "source.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing source.yaml in {source_dir}")
    with config_path.open("r", encoding="utf-8") as handle:
        defaults = yaml.safe_load(handle) or {}
    if not isinstance(defaults, dict):
        raise ValueError(f"source.yaml must contain a mapping: {config_path}")
    return defaults


def _load_members(source_dir: Path) -> pd.DataFrame:
    members_path = source_dir / "members.tsv"
    if not members_path.exists():
        raise FileNotFoundError(f"Missing members.tsv in {source_dir}")
    members = pd.read_csv(members_path, sep="\t", dtype=str).fillna("")
    required = {"signature_id", "signature_name", "gene"}
    missing = sorted(required.difference(members.columns))
    if missing:
        raise ValueError(f"{members_path} is missing required columns: {', '.join(missing)}")
    return members


def _merge_record(defaults: dict[str, Any], member: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for field in CANONICAL_COLUMNS:
        record[field] = None
    for field in ("signature_id", "signature_name", "source", "source_author", "source_pmid", "source_doi", "species", "gene", "cell_family", "context", "disease", "tags"):
        record[field] = normalize_blank(defaults.get(field))

    for key in ("signature_id", "signature_name", "gene", "species", "cell_family", "context", "disease", "tags"):
        value = normalize_blank(member.get(key))
        if value is not None:
            record[key] = value

    record["source"] = normalize_blank(defaults.get("source")) or record["source"]
    record["tags"] = normalize_tags(record["tags"])
    return record


def _parse_source(source: str | None) -> dict[str, str | None]:
    text = normalize_blank(source)
    if text is None:
        return {"source_author": None, "source_pmid": None, "source_doi": None}
    author = text.split(";", 1)[0].strip() or None
    pmid = None
    doi = None
    for part in text.split(";"):
        part = part.strip()
        if part.upper().startswith("PMID"):
            pmid = part.split(":", 1)[-1].replace(".", "").strip() or None
        if part.upper().startswith("DOI"):
            doi = part.split(":", 1)[-1].strip() or None
    return {"source_author": author, "source_pmid": pmid, "source_doi": doi}


def _clean_record(record: dict[str, Any]) -> dict[str, Any]:
    species = (record.get("species") or "unknown").strip()
    record["species"] = species if species in ALLOWED_SPECIES else species

    cell_family = (record.get("cell_family") or "unknown").strip()
    record["cell_family"] = cell_family if cell_family in ALLOWED_CELL_FAMILY else cell_family

    context = (record.get("context") or "unknown").strip()
    record["context"] = context if context in ALLOWED_CONTEXT else context

    gene = normalize_blank(record.get("gene"))
    if gene is None:
        record["gene"] = None
    elif record["species"] == "human":
        record["gene"] = gene.upper()
    else:
        record["gene"] = gene

    record["tags"] = normalize_tags(record.get("tags"))
    for key in ("signature_id", "signature_name", "source", "disease"):
        record[key] = normalize_blank(record.get(key))
    parsed_source = _parse_source(record.get("source"))
    for key, value in parsed_source.items():
        if normalize_blank(record.get(key)) is None and value is not None:
            record[key] = value

    record["species_original"] = record["species"]
    record["gene_original"] = record["gene"]
    record["homology_relation"] = "same_species"
    record["homology_db_class_key"] = None
    return record


def _family_from_signature(signature_id: str) -> str:
    return signature_id.split(".", 1)[0]


def _family_summary(df: pd.DataFrame) -> pd.DataFrame:
    meta = (
        df.groupby("signature_id", as_index=False, sort=True)
        .agg(
            signature_name=("signature_name", "first"),
            source=("source", "first"),
            species=("species", "first"),
            cell_family=("cell_family", "first"),
            context=("context", "first"),
            disease=("disease", "first"),
            tags=("tags", "first"),
        )
    )
    meta["signature_family"] = meta["signature_id"].map(_family_from_signature)
    return meta


def _write_summary_files(meta: pd.DataFrame, output_dir: Path) -> None:
    summary_path = output_dir / "signatures.md"
    lines = [
        "# Available Signatures",
        "",
        "| Domain | Signatures | Species | Cell family | Context | Disease |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family, group in meta.groupby("signature_family", sort=True):
        signatures = ", ".join(group["signature_id"].tolist())
        species = ", ".join(sorted(set(group["species"].tolist())))
        cell_family = ", ".join(sorted(set(group["cell_family"].tolist())))
        context = ", ".join(sorted(set(group["context"].tolist())))
        disease = ", ".join(sorted(set(group["disease"].fillna("unknown").tolist())))
        lines.append(f"| `{family}` | {signatures} | {species} | {cell_family} | {context} | {disease} |")
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _update_readme_signature_section(meta: pd.DataFrame) -> None:
    readme = Path(__file__).resolve().parents[1] / "README.md"
    if not readme.exists():
        return
    content = readme.read_text(encoding="utf-8").splitlines()
    start = next((i for i, line in enumerate(content) if line.strip() == README_START), None)
    end = next((i for i, line in enumerate(content) if line.strip() == README_END), None)
    if start is None or end is None or end <= start:
        return

    section = [
        README_START,
        "",
        "## Available Signatures",
        "",
        "| Domain | Signature count | Species | Cell family | Context | Disease |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]
    for family, group in meta.groupby("signature_family", sort=True):
        species = ", ".join(sorted(set(group["species"].tolist())))
        cell_family = ", ".join(sorted(set(group["cell_family"].tolist())))
        context = ", ".join(sorted(set(group["context"].tolist())))
        disease = ", ".join(sorted(set(group["disease"].fillna("unknown").tolist())))
        section.append(f"| `{family}` | {len(group)} | {species} | {cell_family} | {context} | {disease} |")
    section.extend(["", README_END])
    new_content = content[:start] + section + content[end + 1 :]
    readme.write_text("\n".join(new_content) + "\n", encoding="utf-8")


def _artifact_summary(df: pd.DataFrame, parquet_path: Path, csv_path: Path | None = None) -> dict[str, Any]:
    return {
        "parquet": _display_path(parquet_path),
        "csv_gz": _display_path(csv_path) if csv_path is not None else None,
        "gene_rows": int(len(df)),
        "signature_count": int(df["signature_id"].nunique()),
        "species": sorted(set(df["species"].astype(str).tolist())),
    }


def _write_reference_metadata(metadata: dict[str, Any], output_dir: Path) -> None:
    path = output_dir / REFERENCE_METADATA_PATH.name
    path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def _resolve_homology_reference(download_homology: bool, homology_tag: str | None, homology_url: str) -> tuple[Path | None, dict[str, Any] | None]:
    if download_homology:
        path = download_mouse_human_homology(tag=homology_tag, url=homology_url)
        return path, read_homology_metadata(path=path)

    if homology_tag is not None:
        path = homology_path(homology_tag)
        if not path.exists():
            raise FileNotFoundError(f"Requested homology tag not found locally: {path}")
        return path, read_homology_metadata(path=path)

    try:
        tag = latest_homology_tag()
    except FileNotFoundError:
        return None, None
    path = homology_path(tag)
    return path, read_homology_metadata(path=path)


def build_database(
    curation_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
    homology_tag: str | None = None,
    download_homology: bool = False,
    homology_url: str = HOMOLOGY_URL,
    homology_path_value: str | Path | None = None,
) -> pd.DataFrame:
    source_root = Path(curation_dir) if curation_dir is not None else CURATION_DIR
    output_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    if not source_root.exists():
        raise FileNotFoundError(f"Curation directory does not exist: {source_root}")

    rows: list[dict[str, Any]] = []
    for source_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
        if source_dir.name in {"example_source", "source_material"} or source_dir.name.startswith("."):
            continue
        if not (source_dir / "source.yaml").exists() or not (source_dir / "members.tsv").exists():
            continue
        defaults = _load_source_defaults(source_dir)
        members = _load_members(source_dir)
        for member in members.to_dict(orient="records"):
            record = _clean_record(_merge_record(defaults, member))
            rows.append(record)

    if not rows:
        raise ValueError(f"No curation sources found under {source_root}")

    df = pd.DataFrame(rows, columns=CANONICAL_COLUMNS).loc[:, CANONICAL_COLUMNS].copy()
    df.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    df.reset_index(drop=True, inplace=True)

    original_parquet, original_csv = write_database(df, data_dir=output_dir, reference_species="original", write_csv=True)
    meta = _family_summary(df)
    _write_summary_files(meta, output_dir)
    if source_root.resolve() == CURATION_DIR.resolve() and output_dir.resolve() == DATA_DIR.resolve():
        _update_readme_signature_section(meta)
    validate_database(df, reference_species="original")

    build_meta: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {
            "original": _artifact_summary(df, parquet_path=original_parquet, csv_path=original_csv),
        },
    }

    if homology_path_value is not None:
        homology_ref_path = Path(homology_path_value)
        homology_meta = read_homology_metadata(path=homology_ref_path)
    else:
        homology_ref_path, homology_meta = _resolve_homology_reference(
            download_homology=download_homology,
            homology_tag=homology_tag,
            homology_url=homology_url,
        )

    if homology_ref_path is None:
        build_meta["homology"] = {"status": "missing", "reason": "No local homology reference found. Run phenosigdb-build --download-homology"}
        for target in ("human", "mouse"):
            build_meta["artifacts"][target] = {"status": "skipped", "reason": "homology_missing"}
        _write_reference_metadata(build_meta, output_dir)
        return df

    build_meta["homology"] = {"status": "used", "path": _display_path(homology_ref_path)}
    if homology_meta is not None:
        build_meta["homology"].update(homology_meta)

    for target in ("human", "mouse"):
        translated, translation_summary, signature_stats = translate_reference(
            df,
            target_species=target,
            homology_path_value=homology_ref_path,
        )
        translated_parquet, _ = write_database(translated, data_dir=output_dir, reference_species=target, write_csv=False)
        validate_database(translated, reference_species=target)
        signature_stats_path = translation_signature_stats_path(target, data_dir=output_dir)
        signature_stats.to_csv(signature_stats_path, sep="\t", index=False)
        artifact_summary = _artifact_summary(translated, parquet_path=translated_parquet, csv_path=None)
        artifact_summary["translation_signature_stats_tsv"] = _display_path(signature_stats_path)
        artifact_summary["translation_summary"] = translation_summary
        build_meta["artifacts"][target] = artifact_summary

    _write_reference_metadata(build_meta, output_dir)
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PhenoSigDB reference artifacts")
    parser.add_argument("--download-homology", action="store_true", help="Download the official MGI mouse-human homology report before building")
    parser.add_argument("--homology-tag", default=None, help="Use or assign a specific local homology tag such as 20260615")
    parser.add_argument("--homology-url", default=HOMOLOGY_URL, help=argparse.SUPPRESS)
    args = parser.parse_args()
    build_database(
        download_homology=args.download_homology,
        homology_tag=args.homology_tag,
        homology_url=args.homology_url,
    )
