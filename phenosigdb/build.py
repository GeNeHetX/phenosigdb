from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from .io import (
    ALLOWED_CELL_FAMILY,
    ALLOWED_CONTEXT,
    ALLOWED_SPECIES,
    CANONICAL_COLUMNS,
    CURATION_DIR,
    DATA_DIR,
    normalize_blank,
    normalize_tags,
    write_database,
)
from .validate import validate_database

README_START = "<!-- PHENOSIGDB_SIGNATURES_START -->"
README_END = "<!-- PHENOSIGDB_SIGNATURES_END -->"


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
        record[field] = normalize_blank(defaults.get(field))

    for key in ("signature_id", "signature_name", "gene", "species", "cell_family", "context", "disease", "tags"):
        value = normalize_blank(member.get(key))
        if value is not None:
            record[key] = value

    record["source"] = normalize_blank(defaults.get("source")) or record["source"]
    record["tags"] = normalize_tags(record["tags"])
    return record


def _clean_record(record: dict[str, Any]) -> dict[str, Any]:
    species = (record.get("species") or "unknown").strip()
    if species not in ALLOWED_SPECIES:
        record["species"] = species
    else:
        record["species"] = species

    cell_family = (record.get("cell_family") or "unknown").strip()
    if cell_family not in ALLOWED_CELL_FAMILY:
        record["cell_family"] = cell_family
    else:
        record["cell_family"] = cell_family

    context = (record.get("context") or "unknown").strip()
    if context not in ALLOWED_CONTEXT:
        record["context"] = context
    else:
        record["context"] = context

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
        "| Signature family | Signatures | Species | Cell family | Context | Disease |",
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
        "| Signature family | Signatures | Species | Cell family | Context | Disease |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family, group in meta.groupby("signature_family", sort=True):
        signatures = ", ".join(group["signature_id"].tolist())
        species = ", ".join(sorted(set(group["species"].tolist())))
        cell_family = ", ".join(sorted(set(group["cell_family"].tolist())))
        context = ", ".join(sorted(set(group["context"].tolist())))
        disease = ", ".join(sorted(set(group["disease"].fillna("unknown").tolist())))
        section.append(f"| `{family}` | {signatures} | {species} | {cell_family} | {context} | {disease} |")
    section.extend(["", README_END])
    new_content = content[:start] + section + content[end + 1 :]
    readme.write_text("\n".join(new_content) + "\n", encoding="utf-8")


def build_database(
    curation_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
) -> pd.DataFrame:
    source_root = Path(curation_dir) if curation_dir is not None else CURATION_DIR
    output_dir = Path(data_dir) if data_dir is not None else DATA_DIR
    if not source_root.exists():
        raise FileNotFoundError(f"Curation directory does not exist: {source_root}")

    rows: list[dict[str, Any]] = []
    for source_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
        if source_dir.name == "example_source" or source_dir.name.startswith("."):
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

    df = pd.DataFrame(rows, columns=CANONICAL_COLUMNS)
    df = df.loc[:, CANONICAL_COLUMNS].copy()
    df.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    df.reset_index(drop=True, inplace=True)

    write_database(df, data_dir=output_dir)
    meta = _family_summary(df)
    _write_summary_files(meta, output_dir)
    _update_readme_signature_section(meta)
    validate_database(df)
    return df


def main() -> None:
    build_database()
