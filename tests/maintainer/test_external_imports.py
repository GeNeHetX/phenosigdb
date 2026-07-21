import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from phenosigdb_maintainer.external_imports.base import ExternalImporter, ImportPackage
from phenosigdb_maintainer.external_imports.importers import cellmarker as cellmarker_mod
from phenosigdb_maintainer.external_imports.importers import celltypist as celltypist_mod


def _fake_download(expected: dict[str, Path]):
    def _download(url, destination, **kwargs):
        path = Path(destination)
        source = expected[path.name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source.read_bytes())
        return {
            "url": url,
            "resolved_url": url,
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": path.name,
            "content_type": None,
            "source_last_modified": None,
            "downloaded_at_utc": None,
            "from_cache": True,
        }

    return _download


def test_external_importer_run_writes_versioned_outputs(tmp_path: Path):
    class DummyImporter(ExternalImporter):
        resource_name = "dummy"
        resource_label = "Dummy"
        homepage_url = "https://example.org"

        def build(self, cache_dir: Path, force: bool = False) -> ImportPackage:
            return ImportPackage(
                resource_name=self.resource_name,
                resource_label=self.resource_label,
                resource_version="2026-06-27",
                signatures=pd.DataFrame([{"signature_id": "DUMMY.Source.Test", "signature_name": "Test"}]),
                members=pd.DataFrame([{"signature_id": "DUMMY.Source.Test", "gene": "COL1A1"}]),
                downloads=[{"sha256": "abc123"}],
            )

    manifest = DummyImporter().run(output_root=tmp_path)
    version_dir = tmp_path / "dummy" / "2026.06.27"
    assert (version_dir / "manifest.json").exists()
    assert (version_dir / "signatures.parquet").exists()
    assert manifest["summary"]["signature_count"] == 1
    assert (tmp_path / "dummy" / "latest.json").exists()


def test_cellmarker_importer_splits_multigene_rows(tmp_path: Path, monkeypatch):
    cache_dir = tmp_path / "cache"
    index_html = cache_dir / "index.html"
    index_html.parent.mkdir(parents=True)
    index_html.write_text("<html><body>CellMarker 3.0</body></html>", encoding="utf-8")

    header = "\t".join(
        [
            "species",
            "tissue_class",
            "tissue_type",
            "uberon_id",
            "disease",
            "cell_name_class",
            "cell_name",
            "cellontology_id",
            "marker",
            "symbol",
            "gene_id",
            "gene_type",
            "gene_name",
            "uniprot_id",
            "technology_seq",
            "marker_source",
            "pmid",
            "title",
            "journal",
            "year",
            "series_id",
            "method_details",
        ]
    )
    human_txt = cache_dir / "human_cell_marker.txt"
    human_txt.write_text(
        header
        + "\n"
        + "\t".join(
            [
                "Human",
                "Digestive system",
                "Liver",
                "UBERON:0002107",
                "normal",
                "Parenchymal",
                "Hepatocyte",
                "CL:0000182",
                "MarkerSet1",
                "ALB, APOA1",
                "1;2",
                "protein-coding",
                "albumin, apolipoprotein A1",
                "P02768;P02647",
                "scRNA-seq",
                "Cell marker",
                "12345678",
                "A title",
                "Journal",
                "2024",
                "GSE1",
                "literature",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    mouse_txt = cache_dir / "mouse_cell_marker.txt"
    mouse_txt.write_text(header + "\n", encoding="utf-8")

    for txt_path, zip_name in ((human_txt, "human_cell_marker.zip"), (mouse_txt, "mouse_cell_marker.zip")):
        with zipfile.ZipFile(cache_dir / zip_name, "w") as archive:
            archive.write(txt_path, arcname=txt_path.name)

    monkeypatch.setattr(
        cellmarker_mod,
        "download_file",
        _fake_download(
            {
                "index.html": index_html,
                "human_cell_marker.zip": cache_dir / "human_cell_marker.zip",
                "mouse_cell_marker.zip": cache_dir / "mouse_cell_marker.zip",
            }
        ),
    )
    package = cellmarker_mod.CellMarkerImporter().build(cache_dir=cache_dir)

    assert package.resource_version == "3.0"
    assert package.signatures["signature_id"].nunique() == 1
    assert sorted(package.members["gene"].tolist()) == ["ALB", "APOA1"]

def test_celltypist_importer_extracts_coefficients(tmp_path: Path, monkeypatch):
    class FakeClassifier:
        coef_ = np.array([[1.0, -0.5], [-1.0, 0.5]])
        intercept_ = np.array([0.1, -0.1])

    class FakeModel:
        description = {"details": "Human immune reference", "source": "CellTypist", "version": "1"}
        features = ["CD3D", "NKG7"]
        cell_types = ["T cell", "NK"]
        classifier = FakeClassifier()

    class FakeModelLoader:
        @staticmethod
        def load(name):
            return FakeModel()

    class FakeModels:
        Model = FakeModelLoader

        @staticmethod
        def download_model_index(only_model=True):
            return None

        @staticmethod
        def get_models_index(force_update=False):
            return {"version": "2026-06-27"}

        @staticmethod
        def download_models(force_update=False):
            model_dir = Path(os.environ["CELLTYPIST_FOLDER"]) / "models"
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "Immune_All_Low.pkl").write_bytes(b"model")
            (model_dir / "models.json").write_text(json.dumps({"version": "2026-06-27"}), encoding="utf-8")

        @staticmethod
        def models_description():
            return pd.DataFrame(
                [
                    {
                        "model": "Immune_All_Low.pkl",
                        "description": "Immune model",
                        "url": "https://celltypist.example/model",
                    }
                ]
            )

        @staticmethod
        def get_all_models():
            return ["Immune_All_Low.pkl"]

        @staticmethod
        def get_model_path(name):
            return str(Path(os.environ["CELLTYPIST_FOLDER"]) / "models" / name)

    class FakeCellTypist:
        __version__ = "1.7.0"

    import os

    monkeypatch.setattr(celltypist_mod, "_require_celltypist", lambda: (FakeCellTypist, FakeModels))
    package = celltypist_mod.CellTypistImporter().build(cache_dir=tmp_path / "cache")

    assert package.resource_version == "2026-06-27"
    assert package.signatures["signature_id"].nunique() == 2
    assert package.members["weight"].notna().all()
    assert sorted(package.members["gene"].unique().tolist()) == ["CD3D", "NKG7"]
