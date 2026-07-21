from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .paths import EXTERNAL_CACHE_DIR, EXTERNAL_IMPORTS_DIR, display_path
from .schema import TABLE_SCHEMAS, conform_table, table_path
from .utils import normalize_id_token, now_utc_iso, signature_counts


@dataclass
class ImportPackage:
    resource_name: str
    resource_label: str
    resource_version: str | None = None
    resource_snapshot_id: str | None = None
    signatures: pd.DataFrame | None = None
    members: pd.DataFrame | None = None
    datasets: pd.DataFrame | None = None
    scores: pd.DataFrame | None = None
    downloads: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def tables(self) -> dict[str, pd.DataFrame | None]:
        return {
            "signatures": self.signatures,
            "members": self.members,
            "datasets": self.datasets,
            "scores": self.scores,
        }


class ExternalImporter(ABC):
    resource_name: str
    resource_label: str
    homepage_url: str
    importer_version = "1"

    @abstractmethod
    def build(self, cache_dir: Path, force: bool = False) -> ImportPackage:
        raise NotImplementedError

    def run(self, output_root: str | Path | None = None, force: bool = False) -> dict[str, Any]:
        cache_dir = EXTERNAL_CACHE_DIR / self.resource_name
        cache_dir.mkdir(parents=True, exist_ok=True)

        package = self.build(cache_dir=cache_dir, force=force)
        snapshot_id = package.resource_snapshot_id or self._snapshot_id(package.downloads)
        version_key = normalize_id_token(package.resource_version or snapshot_id or "current")

        root = Path(output_root) if output_root is not None else EXTERNAL_IMPORTS_DIR
        resource_root = root / self.resource_name
        version_dir = resource_root / version_key
        version_dir.mkdir(parents=True, exist_ok=True)

        tables = {
            name: self._prepare_table(name, frame, package.resource_name, package.resource_version, snapshot_id)
            for name, frame in package.tables().items()
        }
        self._update_signature_counts(tables)

        written_tables: dict[str, dict[str, Any]] = {}
        for name, frame in tables.items():
            path = table_path(version_dir, name)
            frame.to_parquet(path, index=False)
            written_tables[name] = {
                "path": display_path(path),
                "rows": int(len(frame)),
                "columns": list(TABLE_SCHEMAS[name]),
            }

        manifest = {
            "resource_name": package.resource_name,
            "resource_label": package.resource_label,
            "resource_version": package.resource_version,
            "resource_snapshot_id": snapshot_id,
            "importer_version": self.importer_version,
            "homepage_url": self.homepage_url,
            "imported_at_utc": now_utc_iso(),
            "downloads": package.downloads,
            "tables": written_tables,
            "summary": {
                "signature_count": int(tables["signatures"]["signature_id"].nunique()) if not tables["signatures"].empty else 0,
                "member_rows": int(len(tables["members"])),
                "dataset_rows": int(len(tables["datasets"])),
                "score_rows": int(len(tables["scores"])),
            },
            "warnings": package.warnings,
            "metadata": package.metadata,
        }

        manifest_path = version_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        latest_path = resource_root / "latest.json"
        latest_path.write_text(
            json.dumps(
                {
                    "resource_name": package.resource_name,
                    "resource_version": package.resource_version,
                    "resource_snapshot_id": snapshot_id,
                    "version_key": version_key,
                    "manifest_path": display_path(manifest_path),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest["manifest_path"] = display_path(manifest_path)
        return manifest

    def _prepare_table(
        self,
        name: str,
        frame: pd.DataFrame | None,
        resource_name: str,
        resource_version: str | None,
        snapshot_id: str,
    ) -> pd.DataFrame:
        out = conform_table(name, frame)
        if out.empty:
            return out
        out["resource_name"] = resource_name
        out["resource_version"] = resource_version
        out["resource_snapshot_id"] = snapshot_id
        return out

    def _snapshot_id(self, downloads: list[dict[str, Any]]) -> str | None:
        hashes = [record.get("sha256") for record in downloads if record.get("sha256")]
        if not hashes:
            return None
        import hashlib

        digest = hashlib.sha256()
        for value in hashes:
            digest.update(str(value).encode("utf-8"))
        return digest.hexdigest()[:16]

    def _update_signature_counts(self, tables: dict[str, pd.DataFrame]) -> None:
        signatures = tables["signatures"]
        members = tables["members"]
        if signatures.empty:
            return
        if members.empty:
            if "imported_member_count" in signatures.columns:
                signatures["imported_member_count"] = signatures["imported_member_count"].fillna(0)
            return
        counts = signature_counts(members)
        mapped = counts.set_index("signature_id")["imported_member_count"].to_dict()
        import_mask = signatures["imported_member_count"].isna() | signatures["imported_member_count"].eq(0)
        signatures.loc[import_mask, "imported_member_count"] = signatures.loc[import_mask, "signature_id"].map(mapped)
        signatures["imported_member_count"] = signatures["imported_member_count"].fillna(0)
        original_mask = signatures["original_member_count"].isna() | signatures["original_member_count"].eq(0)
        signatures.loc[original_mask, "original_member_count"] = signatures.loc[original_mask, "imported_member_count"]
