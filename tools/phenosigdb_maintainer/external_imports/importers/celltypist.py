from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from ..base import ExternalImporter, ImportPackage
from ..utils import infer_cell_family, json_dumps, make_signature_id, normalize_gene_symbol, normalize_species, normalize_whitespace, sha256_file


def _require_celltypist():
    try:
        from celltypist import models  # type: ignore
        import celltypist  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised via unit tests with monkeypatch
        raise ImportError("CellTypist importer requires `pip install -e .[external-import]`") from exc
    return celltypist, models


def _infer_model_species(model_name: str, description: dict) -> str | None:
    text = " ".join(
        filter(
            None,
            [
                model_name,
                str(description.get("details", "")),
                str(description.get("source", "")),
                str(description.get("version", "")),
            ],
        )
    )
    return normalize_species(text)


class CellTypistImporter(ExternalImporter):
    resource_name = "celltypist"
    resource_label = "CellTypist"
    homepage_url = "https://github.com/Teichlab/celltypist"

    def build(self, cache_dir: Path, force: bool = False) -> ImportPackage:
        cache_home = cache_dir / "celltypist_home"
        os.environ["CELLTYPIST_FOLDER"] = str(cache_home)
        celltypist, models = _require_celltypist()

        models.download_model_index(only_model=True)
        index = models.get_models_index(force_update=force)
        models.download_models(force_update=force)
        catalog = models.models_description()
        if not isinstance(catalog, pd.DataFrame):
            catalog = pd.DataFrame(catalog)
        catalog_map = {
            record["model"]: record
            for record in catalog.to_dict(orient="records")
            if "model" in record
        }

        signatures: list[dict] = []
        members: list[dict] = []
        downloads: list[dict] = []

        model_files = [Path(models.get_model_path(name)) for name in models.get_all_models()]
        for model_file in model_files:
            if model_file.exists():
                downloads.append(
                    {
                        "url": None,
                        "resolved_url": None,
                        "path": str(model_file),
                        "bytes": model_file.stat().st_size,
                        "sha256": sha256_file(model_file),
                        "content_type": None,
                        "source_last_modified": None,
                        "downloaded_at_utc": None,
                        "from_cache": not force,
                    }
                )
        index_candidates = list(cache_home.rglob("models.json"))
        index_path = index_candidates[0] if index_candidates else None
        if index_path is not None and index_path.exists():
            downloads.append(
                {
                    "url": "https://celltypist.cog.sanger.ac.uk/models/models.json",
                    "resolved_url": "https://celltypist.cog.sanger.ac.uk/models/models.json",
                    "path": str(index_path),
                    "bytes": index_path.stat().st_size,
                    "sha256": sha256_file(index_path),
                    "content_type": "application/json",
                    "source_last_modified": None,
                    "downloaded_at_utc": None,
                    "from_cache": not force,
                }
            )

        for model_name in models.get_all_models():
            model = models.Model.load(model_name)
            description = getattr(model, "description", {}) or {}
            species = _infer_model_species(model_name, description)
            details = catalog_map.get(model_name, {})
            features = list(model.features)
            cell_types = list(model.cell_types)
            coef = model.classifier.coef_
            intercept = getattr(model.classifier, "intercept_", None)

            if getattr(coef, "shape", None) is None:
                raise ValueError(f"CellTypist model {model_name} does not expose classifier coefficients")

            label_vectors: dict[str, tuple] = {}
            if coef.shape[0] == len(cell_types):
                for label_index, cell_type in enumerate(cell_types):
                    label_vectors[str(cell_type)] = (coef[label_index], intercept[label_index] if intercept is not None else None)
            elif coef.shape[0] == 1 and len(cell_types) == 2:
                label_vectors[str(cell_types[1])] = (coef[0], intercept[0] if intercept is not None else None)
                label_vectors[str(cell_types[0])] = (-coef[0], -intercept[0] if intercept is not None else None)
            else:
                raise ValueError(f"Unexpected coefficient matrix shape for {model_name}: {coef.shape}")

            source_key = Path(model_name).stem
            for cell_type, (weights, cell_intercept) in label_vectors.items():
                signature_id = make_signature_id("CELLTYPIST", source_key, cell_type)
                signatures.append(
                    {
                        "signature_id": signature_id,
                        "signature_name": cell_type,
                        "signature_kind": "classifier_coefficients",
                        "source_record_id": model_name,
                        "source_identifier": model_name,
                        "source_label": details.get("description") or description.get("details") or model_name,
                        "source_url": details.get("url") or self.homepage_url,
                        "source_pmid": None,
                        "source_doi": None,
                        "dataset_id": source_key,
                        "dataset_name": source_key,
                        "cancer_type": None,
                        "species": species,
                        "species_original": species,
                        "tissue": None,
                        "tissue_original": None,
                        "organ": None,
                        "disease": None,
                        "context": "reference_model",
                        "cell_family": infer_cell_family(cell_type),
                        "cell_type": normalize_whitespace(cell_type),
                        "cell_type_original": normalize_whitespace(cell_type),
                        "cell_ontology_id": None,
                        "annotation_level": "classifier_label",
                        "cluster_id": None,
                        "marker_type": "coefficient",
                        "evidence_level": "celltypist_model",
                        "original_member_count": len(features),
                        "imported_member_count": len(features),
                        "signature_metadata_json": json_dumps(
                            {
                                "celltypist_version": getattr(celltypist, "__version__", None),
                                "model_date": description.get("date"),
                                "model_version": description.get("version"),
                                "model_source": description.get("source"),
                                "model_details": description.get("details"),
                                "intercept": float(cell_intercept) if cell_intercept is not None else None,
                            }
                        ),
                    }
                )
                for member_id, (gene, weight) in enumerate(zip(features, weights), start=1):
                    members.append(
                        {
                            "signature_id": signature_id,
                            "member_id": member_id,
                            "gene": normalize_gene_symbol(gene, species),
                            "gene_original": gene,
                            "species": species,
                            "species_original": species,
                            "weight": float(weight),
                            "rank": member_id,
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
                            "marker_type": "coefficient",
                            "evidence": None,
                            "evidence_level": "celltypist_model",
                            "source_member_id": member_id,
                            "source_gene_id": None,
                            "source_uniprot_id": None,
                            "source_series_id": None,
                            "member_metadata_json": None,
                        }
                    )

        return ImportPackage(
            resource_name=self.resource_name,
            resource_label=self.resource_label,
            resource_version=index.get("version") if isinstance(index, dict) else None,
            resource_snapshot_id=None,
            signatures=pd.DataFrame(signatures),
            members=pd.DataFrame(members),
            downloads=downloads,
            metadata={"model_count": len(model_files)},
        )
