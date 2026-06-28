from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

from .io import CANONICAL_COLUMNS, DATA_DIR

HOMOLOGY_URL = "https://www.informatics.jax.org/downloads/reports/HOM_MouseHumanSequence.rpt"
HOMOLOGY_DIR = DATA_DIR / "reference" / "homology"
MOUSE_TAXON = "10090"
HUMAN_TAXON = "9606"


def _timestamp_tag(last_modified: str | None) -> str:
    if last_modified:
        stamp = parsedate_to_datetime(last_modified)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp.astimezone(timezone.utc).strftime("%Y%m%d")
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def homology_path(tag: str) -> Path:
    return HOMOLOGY_DIR / f"mgi_alliance_mouse_human_homology_{tag}.tsv"


def homology_metadata_path(tag: str | None = None, path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path).with_suffix(".json")
    if tag is None:
        raise ValueError("tag or path is required")
    return homology_path(tag).with_suffix(".json")


def list_homology_tags() -> list[str]:
    if not HOMOLOGY_DIR.exists():
        return []
    tags = []
    prefix = "mgi_alliance_mouse_human_homology_"
    suffix = ".tsv"
    for path in sorted(HOMOLOGY_DIR.glob(f"{prefix}*{suffix}")):
        name = path.name
        tags.append(name[len(prefix) : -len(suffix)])
    return tags


def latest_homology_tag() -> str:
    tags = list_homology_tags()
    if not tags:
        raise FileNotFoundError("No downloaded homology reference found")
    return tags[-1]


def read_homology_metadata(tag: str | None = None, path: str | Path | None = None) -> dict[str, str] | None:
    meta_path = homology_metadata_path(tag=tag, path=path)
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def download_mouse_human_homology(tag: str | None = None, force: bool = False, url: str = HOMOLOGY_URL) -> Path:
    request = Request(url, method="HEAD")
    with urlopen(request) as response:
        last_modified = response.headers.get("Last-Modified")
    resolved_tag = tag or _timestamp_tag(last_modified)
    out_path = homology_path(resolved_tag)
    meta_path = out_path.with_suffix(".json")
    if out_path.exists() and not force:
        return out_path

    HOMOLOGY_DIR.mkdir(parents=True, exist_ok=True)
    request = Request(url, method="GET")
    with urlopen(request) as response, out_path.open("wb") as handle:
        handle.write(response.read())

    metadata = {
        "tag": resolved_tag,
        "url": url,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_last_modified": last_modified,
    }
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return out_path


def read_mouse_human_homology(tag: str | None = None, path: str | Path | None = None) -> pd.DataFrame:
    if path is not None:
        source = Path(path)
    else:
        source = homology_path(tag or latest_homology_tag())
    return pd.read_csv(source, sep="\t", dtype=str, quoting=csv.QUOTE_NONE).fillna("")


def ortholog_table(tag: str | None = None, path: str | Path | None = None) -> pd.DataFrame:
    raw = read_mouse_human_homology(tag=tag, path=path)
    needed = {"DB Class Key", "NCBI Taxon ID", "Symbol"}
    missing = sorted(needed.difference(raw.columns))
    if missing:
        raise ValueError(f"Homology file missing columns: {', '.join(missing)}")

    raw = raw.loc[raw["NCBI Taxon ID"].isin([MOUSE_TAXON, HUMAN_TAXON]), ["DB Class Key", "NCBI Taxon ID", "Symbol"]].copy()
    raw = raw.loc[raw["Symbol"] != ""].drop_duplicates()

    rows: list[dict[str, object]] = []
    for db_class_key, group in raw.groupby("DB Class Key", sort=True):
        mouse = sorted(set(group.loc[group["NCBI Taxon ID"] == MOUSE_TAXON, "Symbol"]))
        human = sorted(set(group.loc[group["NCBI Taxon ID"] == HUMAN_TAXON, "Symbol"]))
        if not mouse or not human:
            continue

        def relation_for_direction(source_genes: list[str], target_genes: list[str]) -> str:
            if len(source_genes) == 1 and len(target_genes) == 1:
                return "one_to_one"
            if len(source_genes) == 1 and len(target_genes) > 1:
                return "one_to_many"
            if len(source_genes) > 1 and len(target_genes) == 1:
                return "many_to_one"
            return "many_to_many"

        relation_mouse = relation_for_direction(mouse, human)
        relation_human = relation_for_direction(human, mouse)

        for source_gene in mouse:
            for target_gene in human:
                rows.append(
                    {
                        "db_class_key": str(db_class_key),
                        "source_species": "mouse",
                        "source_gene": source_gene,
                        "target_species": "human",
                        "target_gene": target_gene,
                        "relation": relation_mouse,
                        "source_gene_count": len(mouse),
                        "target_gene_count": len(human),
                    }
                )
        for source_gene in human:
            for target_gene in mouse:
                rows.append(
                    {
                        "db_class_key": str(db_class_key),
                        "source_species": "human",
                        "source_gene": source_gene,
                        "target_species": "mouse",
                        "target_gene": target_gene,
                        "relation": relation_human,
                        "source_gene_count": len(human),
                        "target_gene_count": len(mouse),
                    }
                )
    return pd.DataFrame(rows)


def _collapse_join(series: pd.Series) -> str | None:
    values = sorted({str(value) for value in series if pd.notna(value) and str(value).strip()})
    return ";".join(values) if values else None


def _first(series: pd.Series):
    for value in series:
        return value
    return None


def _sum_or_none(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return None
    return float(values.sum())


def _gene_key(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.upper()


def translate_reference(
    frame: pd.DataFrame,
    target_species: str,
    homology_tag: str | None = None,
    homology_path_value: str | Path | None = None,
) -> tuple[pd.DataFrame, dict[str, object], pd.DataFrame]:
    if target_species not in {"human", "mouse"}:
        raise ValueError("target_species must be human or mouse")
    if frame.empty:
        return frame.copy(), {}, pd.DataFrame()

    invalid_species = sorted(set(frame["species"].astype(str)).difference({"human", "mouse"}))
    if invalid_species:
        raise ValueError(
            "Translated reference build requires all curated signatures to have species human or mouse. "
            f"Invalid values: {', '.join(invalid_species)}"
        )

    translated = frame.copy()
    translated["source_row_id"] = range(len(translated))
    same_rows = translated.loc[translated["species"] == target_species].copy()

    convert_rows = translated.loc[translated["species"] != target_species].copy()
    mapping = ortholog_table(tag=homology_tag, path=homology_path_value)
    mapping = mapping.loc[mapping["target_species"] == target_species].copy()
    convert_rows["gene_key"] = _gene_key(convert_rows["gene_original"])
    mapping["gene_key"] = _gene_key(mapping["source_gene"])

    merged = convert_rows.merge(
        mapping,
        how="left",
        left_on=["species_original", "gene_key"],
        right_on=["source_species", "gene_key"],
    )

    unmapped_source_rows = int(merged.loc[merged["target_gene"].isna(), "source_row_id"].nunique())
    mapped = merged.loc[merged["target_gene"].notna()].copy()

    if mapped.empty:
        out = same_rows.drop(columns=["source_row_id"]).copy()
        out.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
        out.reset_index(drop=True, inplace=True)
        stats = pd.DataFrame(
            [
                {
                    "signature_id": sig,
                    "source_gene_rows_in": int(len(group)),
                    "same_species_rows": int(len(group)),
                    "needs_translation_rows": 0,
                    "unmapped_rows": 0,
                    "translated_rows_pre_collapse": 0,
                    "output_gene_rows": int(len(group)),
                    "split_source_rows": 0,
                    "split_added_rows": 0,
                    "max_split_size": 1,
                    "collapse_output_rows": 0,
                    "collapse_removed_rows": 0,
                    "max_collapse_size": 1,
                }
                for sig, group in same_rows.groupby("signature_id", sort=True)
            ]
        )
        summary = {
            "target_species": target_species,
            "source_gene_rows": int(len(frame)),
            "output_gene_rows": int(len(out)),
            "same_species_rows": int(len(same_rows)),
            "needs_translation_rows": int(len(convert_rows)),
            "unmapped_rows": unmapped_source_rows,
            "split_source_rows": 0,
            "split_added_rows": 0,
            "max_split_size": 1,
            "collapse_output_rows": 0,
            "collapse_removed_rows": 0,
            "max_collapse_size": 1,
            "relation_source_rows": {},
        }
        return out.loc[:, CANONICAL_COLUMNS], summary, stats

    split_groups = mapped.groupby("source_row_id", sort=False).size().rename("mapped_count").reset_index()
    split_source_rows = int((split_groups["mapped_count"] > 1).sum())
    split_added_rows = int((split_groups["mapped_count"] - 1).clip(lower=0).sum())
    max_split_size = int(split_groups["mapped_count"].max())

    relation_rows = mapped.groupby("source_row_id", as_index=False).agg(
        relation=("relation", _first),
        signature_id=("signature_id", _first),
    )
    relation_counts = {
        key: int(value)
        for key, value in relation_rows["relation"].value_counts(sort=False).to_dict().items()
    }

    mapped["gene"] = mapped["target_gene"]
    mapped["species"] = target_species
    mapped["homology_relation"] = mapped["relation"]
    mapped["homology_db_class_key"] = mapped["db_class_key"]

    collapse_sizes = mapped.groupby(["signature_id", "gene"], sort=False).size().rename("collapse_size").reset_index()
    collapse_output_rows = int((collapse_sizes["collapse_size"] > 1).sum())
    collapse_removed_rows = int((collapse_sizes["collapse_size"] - 1).clip(lower=0).sum())
    max_collapse_size = int(collapse_sizes["collapse_size"].max())

    aggregated = (
        mapped.groupby(["signature_id", "gene"], as_index=False, sort=False)
        .agg(
            signature_name=("signature_name", _first),
            source=("source", _first),
            source_author=("source_author", _first),
            source_pmid=("source_pmid", _first),
            source_doi=("source_doi", _first),
            species=("species", _first),
            species_original=("species_original", _collapse_join),
            gene_original=("gene_original", _collapse_join),
            weight=("weight", _sum_or_none),
            cell_family=("cell_family", _first),
            context=("context", _first),
            disease=("disease", _first),
            tags=("tags", _first),
            homology_relation=("homology_relation", _collapse_join),
            homology_db_class_key=("homology_db_class_key", _collapse_join),
        )
    )

    out = pd.concat([same_rows.drop(columns=["source_row_id"]), aggregated], ignore_index=True)
    out = out.loc[:, CANONICAL_COLUMNS].copy()
    out.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    out.reset_index(drop=True, inplace=True)

    same_stats = same_rows.groupby("signature_id", sort=True).size().rename("same_species_rows")
    need_stats = convert_rows.groupby("signature_id", sort=True).size().rename("needs_translation_rows")
    unmapped_stats = (
        merged.loc[merged["target_gene"].isna(), ["signature_id", "source_row_id"]]
        .drop_duplicates()
        .groupby("signature_id", sort=True)
        .size()
        .rename("unmapped_rows")
    )
    pre_collapse_stats = mapped.groupby("signature_id", sort=True).size().rename("translated_rows_pre_collapse")
    output_stats = out.groupby("signature_id", sort=True).size().rename("output_gene_rows")
    split_stats = relation_rows.merge(split_groups, on="source_row_id", how="left")
    split_stats["split_extra"] = (split_stats["mapped_count"] - 1).clip(lower=0)
    per_sig_split = split_stats.groupby("signature_id", sort=True).agg(
        split_source_rows=("mapped_count", lambda s: int((s > 1).sum())),
        split_added_rows=("split_extra", "sum"),
        max_split_size=("mapped_count", "max"),
    )
    collapse_sig = mapped.groupby(["signature_id", "gene"], sort=True).size().rename("collapse_size").reset_index()
    per_sig_collapse = collapse_sig.groupby("signature_id", sort=True).agg(
        collapse_output_rows=("collapse_size", lambda s: int((s > 1).sum())),
        collapse_removed_rows=("collapse_size", lambda s: int((s - 1).clip(lower=0).sum())),
        max_collapse_size=("collapse_size", "max"),
    )

    signature_stats = pd.DataFrame(index=sorted(set(frame["signature_id"].astype(str)))).rename_axis("signature_id")
    for series in (same_stats, need_stats, unmapped_stats, pre_collapse_stats, output_stats):
        signature_stats = signature_stats.join(series, how="left")
    signature_stats = signature_stats.join(per_sig_split, how="left")
    signature_stats = signature_stats.join(per_sig_collapse, how="left")
    source_rows = frame.groupby("signature_id", sort=True).size().rename("source_gene_rows_in")
    signature_stats = signature_stats.join(source_rows, how="left")
    signature_stats.fillna(
        {
            "same_species_rows": 0,
            "needs_translation_rows": 0,
            "unmapped_rows": 0,
            "translated_rows_pre_collapse": 0,
            "output_gene_rows": 0,
            "split_source_rows": 0,
            "split_added_rows": 0,
            "max_split_size": 1,
            "collapse_output_rows": 0,
            "collapse_removed_rows": 0,
            "max_collapse_size": 1,
            "source_gene_rows_in": 0,
        },
        inplace=True,
    )
    for col in signature_stats.columns:
        signature_stats[col] = signature_stats[col].astype(int)
    signature_stats.reset_index(inplace=True)

    summary = {
        "target_species": target_species,
        "source_gene_rows": int(len(frame)),
        "output_gene_rows": int(len(out)),
        "same_species_rows": int(len(same_rows)),
        "needs_translation_rows": int(len(convert_rows)),
        "unmapped_rows": unmapped_source_rows,
        "split_source_rows": split_source_rows,
        "split_added_rows": split_added_rows,
        "max_split_size": max_split_size,
        "collapse_output_rows": collapse_output_rows,
        "collapse_removed_rows": collapse_removed_rows,
        "max_collapse_size": max_collapse_size,
        "relation_source_rows": relation_counts,
    }
    return out, summary, signature_stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Download or inspect the pinned MGI mouse-human homology reference")
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser("download")
    download_parser.add_argument("--tag", default=None)
    download_parser.add_argument("--force", action="store_true")
    download_parser.add_argument("--url", default=HOMOLOGY_URL)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--latest", action="store_true")

    args = parser.parse_args()
    if args.command == "download":
        print(download_mouse_human_homology(tag=args.tag, force=args.force, url=args.url))
        return
    if args.command == "list":
        tags = list_homology_tags()
        if args.latest:
            if not tags:
                raise SystemExit("No homology tag downloaded")
            print(tags[-1])
            return
        for tag in tags:
            print(tag)
        return
    raise SystemExit("Unknown command")


if __name__ == "__main__":
    main()
