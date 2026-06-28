from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from phenosigdb_maintainer.external_imports.utils import (
    infer_cell_family,
    make_signature_id,
    normalize_gene_symbol,
    normalize_id_token,
    normalize_species,
    normalize_whitespace,
)

RAW_NAME = "PanglaoDB_markers_27_Mar_2020.tsv.gz"
RAW_URL = "https://panglaodb.se/markers/PanglaoDB_markers_27_Mar_2020.tsv.gz"
DOMAIN = "CELL"
SOURCE_KEY = "PanglaoDB2020"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def source_material_dir() -> Path:
    return Path(__file__).resolve().parent


def curated_dir() -> Path:
    return repo_root() / "curation" / f"{DOMAIN}.{SOURCE_KEY}"


def local_raw_path() -> Path:
    return source_material_dir() / RAW_NAME


def cache_raw_path() -> Path:
    return repo_root() / "data" / "external_imports" / "_cache" / "panglaodb" / RAW_NAME


def resolve_raw_path() -> Path:
    for path in (local_raw_path(), cache_raw_path()):
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Missing {RAW_NAME}. Put it in {source_material_dir()} or download it from {RAW_URL}."
    )


def normalize_label(value: str | None) -> str:
    return normalize_id_token(normalize_whitespace(value) or "", uppercase=False)


def build_members(raw_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(raw_path, sep="\t", compression="gzip", dtype=str).fillna("")
    raw["species_norm"] = raw["species"].map(normalize_species)
    raw = raw.loc[raw["species_norm"].isin(["human", "mouse"])].copy()

    rows: list[dict[str, str]] = []
    group_cols = ["species_norm", "organ", "cell type"]
    for (species, organ, cell_type), group in raw.groupby(group_cols, dropna=False, sort=True):
        organ_label = normalize_whitespace(organ) or "unknown"
        cell_type_label = normalize_whitespace(cell_type) or "unknown"
        signature_id = make_signature_id(DOMAIN, SOURCE_KEY, f"{species}.{organ_label}.{cell_type_label}")
        signature_name = ".".join([normalize_label(organ_label), normalize_label(cell_type_label)])
        cell_family = infer_cell_family(cell_type_label, organ_label) or "unknown"
        tags = ";".join(["PanglaoDB", "marker_gene_set", normalize_label(organ_label)])

        genes = []
        seen_genes: set[str] = set()
        for gene in group["official gene symbol"].tolist():
            normalized_gene = normalize_gene_symbol(gene, species)
            if not normalized_gene or normalized_gene in seen_genes:
                continue
            seen_genes.add(normalized_gene)
            genes.append(normalized_gene)

        for gene in sorted(genes):
            rows.append(
                {
                    "signature_id": signature_id,
                    "signature_name": signature_name,
                    "gene": gene,
                    "species": species,
                    "cell_family": cell_family,
                    "context": "physiology",
                    "disease": "unknown",
                    "tags": tags,
                }
            )

    members = pd.DataFrame(rows)
    members.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
    members.reset_index(drop=True, inplace=True)
    return members


def write_source_yaml(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "source: PanglaoDB",
                "species: unknown",
                "cell_family: unknown",
                "context: physiology",
                "disease: unknown",
                "tags: PanglaoDB;marker_gene_set",
                "source_author: PanglaoDB",
                "source_pmid: null",
                "source_doi: null",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    out_dir = curated_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    members = build_members(resolve_raw_path())
    members.to_csv(out_dir / "members.tsv", sep="\t", index=False)
    write_source_yaml(out_dir / "source.yaml")
    print(f"Wrote {len(members)} rows across {members['signature_id'].nunique()} signatures to {out_dir}")


if __name__ == "__main__":
    main()
