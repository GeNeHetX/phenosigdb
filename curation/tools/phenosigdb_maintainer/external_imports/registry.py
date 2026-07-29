from __future__ import annotations

from typing import Iterable

from .base import ExternalImporter
from .importers.cellmarker import CellMarkerImporter
from .importers.celltypist import CellTypistImporter

IMPORTERS: dict[str, ExternalImporter] = {
    "cellmarker": CellMarkerImporter(),
    "celltypist": CellTypistImporter(),
}


def list_resources() -> list[str]:
    return sorted(IMPORTERS)


def get_importer(name: str) -> ExternalImporter:
    key = name.strip().casefold()
    if key not in IMPORTERS:
        raise KeyError(f"Unknown external resource importer: {name}")
    return IMPORTERS[key]


def run_importers(resource_names: Iterable[str], *, output_root=None, force: bool = False) -> list[dict]:
    manifests = []
    for resource_name in resource_names:
        manifests.append(get_importer(resource_name).run(output_root=output_root, force=force))
    return manifests
