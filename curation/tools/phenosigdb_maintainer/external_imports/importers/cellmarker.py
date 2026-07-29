from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from ..base import ExternalImporter, ImportPackage
from ..download import download_file
from ..utils import (
    infer_cell_family,
    json_dumps,
    make_signature_id,
    normalize_cell_type_label,
    normalize_gene_symbol,
    normalize_species,
    normalize_whitespace,
    split_genes,
)

INDEX_URL = "https://bio-bigdata.hrbmu.edu.cn/CellMarker/index.html"
HUMAN_URL = "https://bio-bigdata.hrbmu.edu.cn/CellMarker/file/human_cell_marker.zip"
MOUSE_URL = "https://bio-bigdata.hrbmu.edu.cn/CellMarker/file/mouse_cell_marker.zip"


def _read_txt_from_zip(path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != 1:
            raise ValueError(f"Expected a single file in {path}, found {len(names)}")
        with archive.open(names[0]) as handle:
            return pd.read_csv(io.BytesIO(handle.read()), sep="\t", dtype=str).fillna("")


def _detect_version(index_html: str) -> str | None:
    match = re.search(r"CellMarker\s+(\d+(?:\.\d+)*)", index_html, flags=re.IGNORECASE)
    return match.group(1) if match else None


class CellMarkerImporter(ExternalImporter):
    resource_name = "cellmarker"
    resource_label = "CellMarker"
    homepage_url = "https://bio-bigdata.hrbmu.edu.cn/CellMarker/index.html#/download"

    def build(self, cache_dir: Path, force: bool = False) -> ImportPackage:
        index_path = cache_dir / "index.html"
        human_path = cache_dir / "human_cell_marker.zip"
        mouse_path = cache_dir / "mouse_cell_marker.zip"

        downloads = [
            download_file(INDEX_URL, index_path, force=force),
            download_file(HUMAN_URL, human_path, force=force),
            download_file(MOUSE_URL, mouse_path, force=force),
        ]

        version = _detect_version(index_path.read_text(encoding="utf-8", errors="replace"))
        human = _read_txt_from_zip(human_path).reset_index().rename(columns={"index": "_row_id"})
        mouse = _read_txt_from_zip(mouse_path).reset_index().rename(columns={"index": "_row_id"})

        signatures: list[dict] = []
        members: list[dict] = []

        for source_key, table in (("Human", human), ("Mouse", mouse)):
            for row in table.to_dict(orient="records"):
                species_original = normalize_whitespace(row.get("species")) or source_key
                species = normalize_species(species_original)
                cell_type = normalize_cell_type_label(row.get("cell_name")) or normalize_cell_type_label(row.get("cell_name_class"))
                if cell_type is None:
                    continue

                row_id = int(row["_row_id"]) + 1
                signature_id = make_signature_id("CELLMARKER", source_key, f"row{row_id:07d}.{cell_type}")
                genes = split_genes(row.get("symbol"))
                if not genes:
                    genes = split_genes(row.get("gene_name"))
                gene_pairs = [
                    (gene_original, normalize_gene_symbol(gene_original, species))
                    for gene_original in genes
                ]
                gene_pairs = [(gene_original, gene) for gene_original, gene in gene_pairs if gene]

                signatures.append(
                    {
                        "signature_id": signature_id,
                        "signature_name": cell_type,
                        "signature_kind": "literature_marker_set",
                        "source_record_id": row_id,
                        "source_identifier": normalize_whitespace(row.get("marker")) or normalize_whitespace(row.get("series_id")) or str(row_id),
                        "source_label": normalize_whitespace(row.get("title")) or "CellMarker record",
                        "source_url": self.homepage_url,
                        "source_pmid": normalize_whitespace(row.get("pmid")),
                        "source_doi": None,
                        "dataset_id": normalize_whitespace(row.get("series_id")),
                        "dataset_name": normalize_whitespace(row.get("series_id")),
                        "cancer_type": normalize_whitespace(row.get("disease")),
                        "species": species,
                        "species_original": species_original,
                        "tissue": normalize_whitespace(row.get("tissue_type")),
                        "tissue_original": normalize_whitespace(row.get("tissue_type")),
                        "organ": normalize_whitespace(row.get("tissue_class")),
                        "disease": normalize_whitespace(row.get("disease")),
                        "context": None,
                        "cell_family": infer_cell_family(row.get("cell_name"), row.get("cell_name_class")),
                        "cell_type": cell_type,
                        "cell_type_original": normalize_whitespace(row.get("cell_name")),
                        "cell_ontology_id": normalize_whitespace(row.get("cellontology_id")),
                        "annotation_level": normalize_whitespace(row.get("cell_name_class")),
                        "cluster_id": None,
                        "marker_type": normalize_whitespace(row.get("marker_source")) or normalize_whitespace(row.get("marker")),
                        "evidence_level": normalize_whitespace(row.get("technology_seq")),
                        "original_member_count": len(genes),
                        "imported_member_count": len(gene_pairs),
                        "signature_metadata_json": json_dumps(
                            {
                                "marker": normalize_whitespace(row.get("marker")),
                                "marker_source": normalize_whitespace(row.get("marker_source")),
                                "technology_seq": normalize_whitespace(row.get("technology_seq")),
                                "journal": normalize_whitespace(row.get("journal")),
                                "year": normalize_whitespace(row.get("year")),
                                "method_details": normalize_whitespace(row.get("method_details")),
                                "uberon_id": normalize_whitespace(row.get("uberon_id")),
                            }
                        ),
                    }
                )

                seen: set[str] = set()
                for member_index, (gene_original, gene) in enumerate(gene_pairs, start=1):
                    if gene in seen:
                        continue
                    seen.add(gene)
                    members.append(
                        {
                            "signature_id": signature_id,
                            "member_id": member_index,
                            "gene": gene,
                            "gene_original": gene_original,
                            "species": species,
                            "species_original": species_original,
                            "weight": None,
                            "rank": member_index,
                            "logfc": None,
                            "avg_log2fc": None,
                            "p_value": None,
                            "adjusted_p_value": None,
                            "percentage": None,
                            "pct_1": None,
                            "pct_2": None,
                            "sensitivity": None,
                            "specificity": None,
                            "sensitivity_human": None,
                            "sensitivity_mouse": None,
                            "specificity_human": None,
                            "specificity_mouse": None,
                            "canonical_marker": None,
                            "ubiquitous": None,
                            "marker_type": normalize_whitespace(row.get("marker_source")) or normalize_whitespace(row.get("marker")),
                            "evidence": normalize_whitespace(row.get("method_details")),
                            "evidence_level": normalize_whitespace(row.get("technology_seq")),
                            "source_member_id": member_index,
                            "source_gene_id": normalize_whitespace(row.get("gene_id")),
                            "source_uniprot_id": normalize_whitespace(row.get("uniprot_id")),
                            "source_series_id": normalize_whitespace(row.get("series_id")),
                            "member_metadata_json": None,
                        }
                    )

        return ImportPackage(
            resource_name=self.resource_name,
            resource_label=self.resource_label,
            resource_version=version,
            signatures=pd.DataFrame(signatures),
            members=pd.DataFrame(members),
            metadata={
                "human_rows": int(len(human)),
                "mouse_rows": int(len(mouse)),
                "source_urls": [HUMAN_URL, MOUSE_URL],
            },
            downloads=downloads,
        )
