from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import pandas as pd

from ._version import __version__
from ._download import download_to_path

try:  # pragma: no cover - dependency fallback
    from platformdirs import user_cache_dir as _user_cache_dir
except ImportError:  # pragma: no cover - dependency fallback
    def _user_cache_dir(appname: str) -> str:
        return str(Path.home() / ".cache" / appname)


RESOURCE_METADATA_COLUMNS = [
    "signature_id",
    "signature_name",
    "domain",
    "source",
    "collection",
    "source_resource",
    "resource_key",
    "signature_format",
    "species",
    "species_original",
    "cell_family",
    "context",
    "disease",
    "n_genes",
    "source_version",
    "source_label",
    "source_pmid",
    "source_doi",
    "source_url",
    "original_source",
    "original_signature_name",
    "cell_ontology_id",
    "annotation_level",
    "resource_metadata_json",
]

PUBLIC_METADATA_COLUMNS = [
    "signature_id",
    "signature_name",
    "domain",
    "source",
    "collection",
    "source_resource",
    "signature_format",
    "species",
    "cell_family",
    "context",
    "disease",
    "n_genes",
]

BINARY_TABLE_COLUMNS = ["signature_id", "gene"]
CONTINUOUS_TABLE_COLUMNS = ["signature_id", "gene", "weight"]

ALLOWED_REFERENCE_SPECIES = {"original", "human", "mouse"}
DEFAULT_GITHUB_RELEASE_REPOSITORY = "GeNeHetX/phenosigdb"


@dataclass(frozen=True)
class RuntimeResourceSpec:
    resource: str
    signature_id_prefixes: tuple[str, ...]
    signature_format: str
    expected_files: tuple[str, ...]
    install_kind: str = "archive"
    archive_name: str | None = None
    download_url: str | None = None
    version: str | None = None
    public_domain: str | None = None
    public_source: str | None = None
    public_collection: str | None = None
    public_source_resource: str | None = None
    public_context: str | None = None
    public_tags: str | None = None
    public_species: str | None = None
    public_cell_family: str | None = None
    license_notice: str | None = None


MSIGDB_LICENSE_NOTICE = (
    "This downloads MSigDB C7/C8/PID/BioCarta gene sets from the Broad MSigDB release server.\n"
    "By continuing, you are responsible for complying with MSigDB license terms.\n"
    "phenosigdb stores the files locally for your own use and does not redistribute them."
)


RESOURCE_SPECS: dict[str, RuntimeResourceSpec] = {
    "celltypist": RuntimeResourceSpec(
        resource="celltypist",
        signature_id_prefixes=("CELLTYPIST.",),
        signature_format="continuous",
        expected_files=("metadata.parquet", "continuous.parquet", "resource.json"),
        archive_name="phenosigdb-resource-celltypist.tar.gz",
    ),
    "cellmarker": RuntimeResourceSpec(
        resource="cellmarker",
        signature_id_prefixes=("CELLMARKER.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        archive_name="phenosigdb-resource-cellmarker.tar.gz",
    ),
    "msigdb_c7immune": RuntimeResourceSpec(
        resource="msigdb_c7immune",
        signature_id_prefixes=("MSIGDB.C7.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        install_kind="gmt",
        download_url="https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c7.all.v2025.1.Hs.symbols.gmt",
        version="2025.1.Hs",
        public_domain="MSIGDB",
        public_source="C7",
        public_collection="C7",
        public_source_resource="msigdb",
        public_context="immunology",
        public_tags="C7",
        public_species="human",
        public_cell_family="immune",
        license_notice=MSIGDB_LICENSE_NOTICE,
    ),
    "msigdb_c8celltype": RuntimeResourceSpec(
        resource="msigdb_c8celltype",
        signature_id_prefixes=("MSIGDB.C8.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        install_kind="gmt",
        download_url="https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c8.all.v2025.1.Hs.symbols.gmt",
        version="2025.1.Hs",
        public_domain="MSIGDB",
        public_source="C8",
        public_collection="C8",
        public_source_resource="msigdb",
        public_context="cell_type",
        public_tags="C8",
        public_species="human",
        public_cell_family="unknown",
        license_notice=MSIGDB_LICENSE_NOTICE,
    ),
    "pid": RuntimeResourceSpec(
        resource="pid",
        signature_id_prefixes=("MSIGDB.PID.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        install_kind="gmt",
        download_url="https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c2.cp.pid.v2025.1.Hs.symbols.gmt",
        version="2025.1.Hs",
        public_domain="MSIGDB",
        public_source="PID",
        public_collection="PID",
        public_source_resource="msigdb",
        public_context="pathway",
        public_tags="PID",
        public_species="human",
        public_cell_family="unknown",
        license_notice=MSIGDB_LICENSE_NOTICE,
    ),
    "biocarta": RuntimeResourceSpec(
        resource="biocarta",
        signature_id_prefixes=("MSIGDB.BIOCARTA.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        install_kind="gmt",
        download_url="https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c2.cp.biocarta.v2025.1.Hs.symbols.gmt",
        version="2025.1.Hs",
        public_domain="MSIGDB",
        public_source="BIOCARTA",
        public_collection="BIOCARTA",
        public_source_resource="msigdb",
        public_context="pathway",
        public_tags="BIOCARTA",
        public_species="human",
        public_cell_family="unknown",
        license_notice=MSIGDB_LICENSE_NOTICE,
    ),
    "reactome": RuntimeResourceSpec(
        resource="reactome",
        signature_id_prefixes=("REACTOME.PATHWAYS.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        install_kind="zip_gmt",
        download_url="https://reactome.org/download/current/ReactomePathways.gmt.zip",
        version="current",
        public_domain="REACTOME",
        public_source="Pathways",
        public_collection="ReactomePathways",
        public_source_resource="reactome",
        public_context="pathway",
        public_tags="Reactome",
        public_species="human",
        public_cell_family="unknown",
    ),
    "wikipathways": RuntimeResourceSpec(
        resource="wikipathways",
        signature_id_prefixes=("WIKIPATHWAYS.HOMOSAPIENS.",),
        signature_format="binary",
        expected_files=("metadata.parquet", "binary.parquet", "resource.json"),
        install_kind="wikipathways_current_gmt",
        download_url="https://data.wikipathways.org/current/gmt/",
        version="current",
        public_domain="WIKIPATHWAYS",
        public_source="HomoSapiens",
        public_collection="WikiPathways",
        public_source_resource="wikipathways",
        public_context="pathway",
        public_tags="WikiPathways",
        public_species="human",
        public_cell_family="unknown",
    ),
}


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_token(value: Any) -> str:
    text = "" if value is None else str(value).strip()
    if not text:
        return "unknown"
    text = text.encode("ascii", "ignore").decode("ascii")
    out: list[str] = []
    last_sep = False
    for char in text:
        if char.isalnum():
            out.append(char)
            last_sep = False
        elif char == "_":
            if not last_sep:
                out.append("_")
            last_sep = True
        else:
            if not last_sep:
                out.append("_")
            last_sep = True
    normalized = "".join(out).strip("_")
    return normalized or "unknown"


def normalize_resource_signature_id(domain: str, source_key: Any, signature_name: Any) -> str:
    return ".".join(
        [
            _normalize_token(domain).upper(),
            _normalize_token(source_key),
            _normalize_token(signature_name),
        ]
    )


def cache_root() -> Path:
    override = os.getenv("PHENOSIGDB_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(_user_cache_dir("phenosigdb")).expanduser().resolve()


def resources_manifest_path(root: str | Path | None = None) -> Path:
    base = Path(root) if root is not None else cache_root()
    return base / "resources.json"


def resource_dir(resource: str, root: str | Path | None = None) -> Path:
    base = Path(root) if root is not None else cache_root()
    return base / resource.strip().casefold()


def resource_manifest_path(resource: str, root: str | Path | None = None) -> Path:
    return resource_dir(resource, root=root) / "resource.json"


def known_resources() -> list[str]:
    return list(RESOURCE_SPECS)


def resource_name_for_signature_id(signature_id: str | None) -> str | None:
    if not signature_id:
        return None
    text = str(signature_id).strip().upper()
    for resource, spec in RESOURCE_SPECS.items():
        if any(text.startswith(prefix.upper()) for prefix in spec.signature_id_prefixes):
            return resource
    return None


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _default_resource_source(spec: RuntimeResourceSpec) -> str:
    explicit = os.getenv(f"PHENOSIGDB_RESOURCE_URL_{spec.resource.upper()}")
    if explicit:
        return explicit
    if spec.install_kind == "archive":
        base = os.getenv("PHENOSIGDB_RESOURCES_BASE_URL")
        if base:
            return base.rstrip("/") + "/" + str(spec.archive_name)
        release_ref = os.getenv("PHENOSIGDB_RESOURCES_RELEASE", f"v{__version__}")
        return f"https://github.com/{DEFAULT_GITHUB_RELEASE_REPOSITORY}/releases/download/{release_ref}/{spec.archive_name}"
    if spec.download_url is None:
        raise ValueError(f"Resource {spec.resource} is missing a download_url")
    return spec.download_url


def _download_file(source: str, destination: Path) -> dict[str, Any]:
    parsed = urlparse(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if parsed.scheme in {"", "file"}:
        local_path = Path(parsed.path if parsed.scheme == "file" else source).expanduser()
        if not local_path.exists():
            raise FileNotFoundError(f"Resource archive not found: {local_path}")
        shutil.copy2(local_path, destination)
        return {
            "url": source,
            "resolved_url": str(local_path.resolve()),
            "path": str(destination),
            "bytes": destination.stat().st_size,
            "sha256": _sha256_file(destination),
            "downloaded_at_utc": _now_utc(),
            "from_cache": False,
        }

    path = download_to_path(source, destination)
    return {
        "url": source,
        "resolved_url": source,
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
        "downloaded_at_utc": _now_utc(),
        "from_cache": False,
    }


def _download_resource_file(spec: RuntimeResourceSpec, destination: Path) -> dict[str, Any]:
    return _download_file(_default_resource_source(spec), destination)


def _read_status(resource: str, root: str | Path | None = None) -> dict[str, Any]:
    spec = RESOURCE_SPECS[resource]
    base = resource_dir(resource, root=root)
    manifest = _read_json(base / "resource.json") or {}
    expected = [base / name for name in spec.expected_files]
    installed = all(path.exists() for path in expected)
    return {
        "resource": resource,
        "installed": bool(installed),
        "version": manifest.get("version", spec.version),
        "installed_at": manifest.get("installed_at"),
        "signature_format": manifest.get("signature_format", spec.signature_format),
        "n_signatures": manifest.get("n_signatures"),
        "n_rows": manifest.get("n_rows"),
        "checksum": manifest.get("checksum"),
        "package_version": manifest.get("package_version"),
        "files": manifest.get("files", [path.name for path in expected if path.exists()]),
        "cache_path": str(base),
    }


def _write_resources_manifest(root: str | Path | None = None) -> pd.DataFrame:
    records = [_read_status(resource, root=root) for resource in known_resources()]
    frame = pd.DataFrame(records)
    _write_json(
        resources_manifest_path(root=root),
        {"generated_at_utc": _now_utc(), "resources": frame.to_dict(orient="records")},
    )
    return frame


def _resource_listing(root: str | Path | None = None) -> pd.DataFrame:
    manifest = _read_json(resources_manifest_path(root=root))
    current = pd.DataFrame([_read_status(resource, root=root) for resource in known_resources()])
    if manifest and isinstance(manifest.get("resources"), list):
        frame = pd.DataFrame(manifest["resources"])
        if set(frame.get("resource", [])) == set(current.get("resource", [])):
            return current.loc[:, list(current.columns)]
    return current


def _extract_resource_dir(archive_path: Path, resource: str) -> Path:
    with tempfile.TemporaryDirectory(prefix=f"phenosigdb-{resource}-") as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with tarfile.open(archive_path, "r:gz") as archive:
            archive.extractall(tmp_dir)
        direct = tmp_dir / resource
        if direct.exists():
            final_root = direct
        else:
            final_root = tmp_dir
        staged = Path(tempfile.mkdtemp(prefix=f"phenosigdb-{resource}-staged-"))
        shutil.copytree(final_root, staged / resource)
    return staged / resource


def _write_runtime_resource_dir(
    resource: str,
    *,
    metadata: pd.DataFrame,
    values: pd.DataFrame,
    resource_json: dict[str, Any],
    root: str | Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    base = resource_dir(resource, root=root)
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    metadata.to_parquet(base / "metadata.parquet", index=False, compression="zstd")
    if RESOURCE_SPECS[resource].signature_format == "continuous":
        values.to_parquet(base / "continuous.parquet", index=False, compression="zstd")
    else:
        values.to_parquet(base / "binary.parquet", index=False, compression="zstd")
    resource_json.setdefault("resource", resource)
    resource_json.setdefault("installed_at", _now_utc())
    resource_json.setdefault("signature_format", RESOURCE_SPECS[resource].signature_format)
    resource_json.setdefault("package_version", __version__)
    resource_json["files"] = sorted(path.name for path in base.iterdir() if path.is_file())
    _write_json(base / "resource.json", resource_json)
    frame = _write_resources_manifest(root=root)
    row = frame.loc[frame["resource"] == resource].iloc[0].to_dict()
    if verbose:
        print(f"Installed {resource} into {row['cache_path']}")
    return row


def _validate_installed_files(resource: str, extracted_dir: Path) -> None:
    spec = RESOURCE_SPECS[resource]
    missing = [name for name in spec.expected_files if not (extracted_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Resource archive for {resource} is missing required files: {', '.join(missing)}")


def _resource_state_from_manifest(resource: str, resource_json: dict[str, Any], destination: Path) -> dict[str, Any]:
    files = sorted(path.name for path in destination.iterdir() if path.is_file())
    return {
        "resource": resource,
        "installed": True,
        "version": resource_json.get("version"),
        "installed_at": resource_json.get("installed_at"),
        "signature_format": resource_json.get("signature_format", RESOURCE_SPECS[resource].signature_format),
        "n_signatures": resource_json.get("n_signatures"),
        "n_rows": resource_json.get("n_rows"),
        "checksum": resource_json.get("checksum"),
        "package_version": resource_json.get("package_version"),
        "files": files,
        "cache_path": str(destination),
    }


def _normalize_human_gene(value: Any) -> str | None:
    text = "" if value is None else str(value).strip()
    if not text:
        return None
    normalized = text.encode("ascii", "ignore").decode("ascii").strip()
    normalized = normalized.replace(" ", "")
    return normalized.upper() or None


def _deduplicate_genes(genes: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for gene in genes:
        if gene in seen:
            continue
        seen.add(gene)
        out.append(gene)
    return out


def _read_text_url(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="ignore")


def _resolve_wikipathways_source(source: str) -> tuple[str, str | None]:
    parsed = urlparse(source)
    if parsed.scheme in {"", "file"} or source.lower().endswith(".gmt"):
        return source, None
    html = _read_text_url(source)
    matches = re.findall(r"(wikipathways-(\d+)-gmt-Homo_sapiens\.gmt)", html, flags=re.IGNORECASE)
    if not matches:
        raise FileNotFoundError("Could not resolve a Homo sapiens WikiPathways GMT file from the current directory listing")
    filename, version = sorted(matches, key=lambda item: item[1])[-1]
    base = source.rstrip("/") + "/"
    return base + filename, version


def _read_gmt_entries(path: Path, *, kind: str) -> list[tuple[str, str | None, list[str]]]:
    if kind == "zip_gmt":
        with zipfile.ZipFile(path) as handle:
            names = [name for name in handle.namelist() if name.lower().endswith(".gmt")]
            if not names:
                raise FileNotFoundError(f"No .gmt file found inside {path}")
            with handle.open(sorted(names)[0]) as raw:
                text = raw.read().decode("utf-8", errors="ignore")
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")

    entries: list[tuple[str, str | None, list[str]]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        fields = [field.strip() for field in line.rstrip("\n").split("\t")]
        if len(fields) < 3:
            continue
        name = fields[0]
        description = fields[1] or None
        genes = _deduplicate_genes(
            [
                gene
                for gene in (_normalize_human_gene(value) for value in fields[2:])
                if gene is not None
            ]
        )
        if genes:
            entries.append((name, description, genes))
    return entries


def _build_direct_binary_resource(
    spec: RuntimeResourceSpec,
    *,
    resolved_source_url: str,
    source_version: str | None,
    entries: list[tuple[str, str | None, list[str]]],
    download_meta: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    metadata_rows: list[dict[str, Any]] = []
    binary_rows: list[dict[str, str]] = []
    domain = spec.public_domain or spec.resource.upper()
    source_key = spec.public_source or spec.resource
    collection = spec.public_collection or source_key
    source_resource = spec.public_source_resource or spec.resource
    species = spec.public_species or "unknown"
    cell_family = spec.public_cell_family or "unknown"

    for set_name, description, genes in entries:
        signature_id = normalize_resource_signature_id(domain, source_key, set_name)
        metadata_rows.append(
            {
                "signature_id": signature_id,
                "signature_name": set_name,
                "domain": domain,
                "source": source_key,
                "collection": collection,
                "source_resource": source_resource,
                "resource_key": spec.resource,
                "signature_format": "binary",
                "species": species,
                "species_original": species,
                "cell_family": cell_family,
                "context": spec.public_context or "unknown",
                "disease": "unknown",
                "n_genes": len(genes),
                "source_version": source_version or spec.version,
                "source_label": description,
                "source_pmid": None,
                "source_doi": None,
                "source_url": resolved_source_url,
                "original_source": source_key,
                "original_signature_name": set_name,
                "cell_ontology_id": None,
                "annotation_level": None,
                "resource_metadata_json": json.dumps(
                    {
                        "description": description,
                        "tags": spec.public_tags,
                        "resolved_source_url": resolved_source_url,
                    }
                ),
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
        "resource": spec.resource,
        "version": source_version or spec.version,
        "signature_format": "binary",
        "n_signatures": int(metadata["signature_id"].nunique()),
        "n_rows": int(len(binary)),
        "package_version": __version__,
        "source_resource": source_resource,
        "source_url": resolved_source_url,
        "download_url": download_meta.get("url"),
        "resolved_download_url": download_meta.get("resolved_url"),
        "checksum": download_meta.get("sha256"),
    }
    return metadata, binary, resource_json


def _install_from_archive(resource: str, archive_path: Path, download_meta: dict[str, Any], root: str | Path | None = None, verbose: bool = True) -> dict[str, Any]:
    extracted_dir = _extract_resource_dir(archive_path, resource)
    _validate_installed_files(resource, extracted_dir)
    resource_json = _read_json(extracted_dir / "resource.json") or {}
    resource_json.setdefault("resource", resource)
    resource_json.setdefault("installed_at", _now_utc())
    resource_json.setdefault("signature_format", RESOURCE_SPECS[resource].signature_format)
    resource_json.setdefault("package_version", __version__)
    resource_json.setdefault("files", sorted(path.name for path in extracted_dir.iterdir() if path.is_file()))
    resource_json["checksum"] = download_meta.get("sha256")

    base = resource_dir(resource, root=root)
    if base.exists():
        shutil.rmtree(base)
    base.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(extracted_dir), str(base))
    _write_json(base / "resource.json", resource_json)
    shutil.rmtree(extracted_dir.parent, ignore_errors=True)

    frame = _write_resources_manifest(root=root)
    row = frame.loc[frame["resource"] == resource].iloc[0].to_dict()
    if verbose:
        print(f"Installed {resource} into {row['cache_path']}")
    return row


def _install_direct_resource(resource: str, root: str | Path | None = None, verbose: bool = True) -> dict[str, Any]:
    spec = RESOURCE_SPECS[resource]
    source = _default_resource_source(spec)
    resolved_source = source
    resolved_version = spec.version
    if spec.install_kind == "wikipathways_current_gmt":
        resolved_source, listing_version = _resolve_wikipathways_source(source)
        resolved_version = listing_version or resolved_version

    suffix = ".zip" if spec.install_kind == "zip_gmt" else ".gmt"
    staged_file = Path(tempfile.mkdtemp(prefix=f"phenosigdb-{resource}-raw-")) / f"{resource}{suffix}"
    try:
        download_meta = _download_file(resolved_source, staged_file)
        entries = _read_gmt_entries(staged_file, kind=spec.install_kind)
        metadata, binary, resource_json = _build_direct_binary_resource(
            spec,
            resolved_source_url=resolved_source,
            source_version=resolved_version,
            entries=entries,
            download_meta=download_meta,
        )
        return _write_runtime_resource_dir(
            resource,
            metadata=metadata,
            values=binary,
            resource_json=resource_json,
            root=root,
            verbose=verbose,
        )
    finally:
        shutil.rmtree(staged_file.parent, ignore_errors=True)


def _remove_resource(resource: str, root: str | Path | None = None, verbose: bool = True) -> dict[str, Any]:
    base = resource_dir(resource, root=root)
    if base.exists():
        shutil.rmtree(base)
    frame = _write_resources_manifest(root=root)
    row = frame.loc[frame["resource"] == resource].iloc[0].to_dict()
    if verbose:
        print(f"Removed {resource} from cache")
    return row


def _resolve_resource(resource: str | None, *, allow_none: bool = False) -> str | None:
    if resource is None:
        if allow_none:
            return None
        raise ValueError("resource is required for this action")
    key = resource.strip().casefold()
    if key not in RESOURCE_SPECS:
        available = ", ".join(sorted(RESOURCE_SPECS.keys()))
        raise KeyError(f"Unknown resource: {resource}. Available resources: {available}")
    return key


def _resolve_resource_list(resource: str | None, *, allow_none: bool = False) -> list[str]:
    if resource is None or not str(resource).strip():
        if allow_none:
            return known_resources()
        raise ValueError("resource is required for this action")
    key = _resolve_resource(resource)
    assert key is not None
    return [key]


def _print_license_notices(resource_keys: list[str], *, verbose: bool) -> None:
    if not verbose:
        return
    notices: list[str] = []
    seen: set[str] = set()
    for resource_key in resource_keys:
        notice = RESOURCE_SPECS[resource_key].license_notice
        if notice and notice not in seen:
            notices.append(notice)
            seen.add(notice)
    for notice in notices:
        print(notice)


def _fetch_resource(
    resource_key: str,
    *,
    action_key: str,
    force: bool = False,
    verbose: bool = True,
    root: str | Path | None = None,
) -> dict[str, Any]:
    spec = RESOURCE_SPECS[resource_key]
    current = _read_status(resource_key, root=root)
    if action_key == "install" and current["installed"] and not force:
        if verbose:
            print(f"{resource_key} is already installed")
        return current
    if spec.install_kind != "archive":
        if action_key == "update" and current["installed"] and not force and spec.version is not None and current.get("version") == spec.version:
            if verbose:
                print(f"{resource_key} is already up to date")
            return current
        return _install_direct_resource(resource_key, root=root, verbose=verbose)
    archive_path = Path(tempfile.mkdtemp(prefix=f"phenosigdb-{resource_key}-archive-")) / spec.archive_name
    try:
        download_meta = _download_resource_file(spec, archive_path)
        extracted_dir = _extract_resource_dir(archive_path, resource_key)
        _validate_installed_files(resource_key, extracted_dir)
        resource_json = _read_json(extracted_dir / "resource.json") or {}
        remote_version = resource_json.get("version")
        shutil.rmtree(extracted_dir.parent, ignore_errors=True)

        if action_key == "update" and current["installed"] and not force and current.get("version") == remote_version:
            if verbose:
                print(f"{resource_key} is already up to date")
            return current

        return _install_from_archive(resource_key, archive_path, download_meta, root=root, verbose=verbose)
    finally:
        shutil.rmtree(archive_path.parent, ignore_errors=True)


def phenosigdb_resources(action: str = "list", resource: str | None = None, force: bool = False, verbose: bool = True):
    action_key = str(action).strip().casefold()
    if action_key not in {"list", "install", "remove", "update", "path"}:
        raise ValueError(
            "action must be one of: list, install, remove, update, path"
        )

    if action_key == "path":
        root = cache_root()
        root.mkdir(parents=True, exist_ok=True)
        return str(root)

    if action_key == "list":
        return _resource_listing()

    if action_key == "remove":
        resource_key = _resolve_resource(resource)
        assert resource_key is not None
        return _remove_resource(resource_key, verbose=verbose)

    resource_keys = _resolve_resource_list(resource, allow_none=True)
    _print_license_notices(resource_keys, verbose=verbose)
    if len(resource_keys) == 1 and resource is not None and str(resource).strip():
        return _fetch_resource(resource_keys[0], action_key=action_key, force=force, verbose=verbose)

    for resource_key in resource_keys:
        _fetch_resource(resource_key, action_key=action_key, force=force, verbose=verbose)
    return _resource_listing()


def installed_resource_metadata(reference_species: str = "human", root: str | Path | None = None) -> pd.DataFrame:
    if reference_species not in ALLOWED_REFERENCE_SPECIES:
        raise ValueError(
            f"reference_species must be one of: {', '.join(sorted(ALLOWED_REFERENCE_SPECIES))}"
        )
    frames: list[pd.DataFrame] = []
    for resource in known_resources():
        path = resource_dir(resource, root=root) / "metadata.parquet"
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        for column in RESOURCE_METADATA_COLUMNS:
            if column not in frame.columns:
                frame[column] = pd.NA
        if reference_species != "original":
            frame = frame.loc[frame["species_original"].fillna(frame["species"]).astype(str).str.casefold() == reference_species].copy()
        frames.append(frame.loc[:, RESOURCE_METADATA_COLUMNS])
    if not frames:
        return pd.DataFrame(columns=RESOURCE_METADATA_COLUMNS)
    combined = pd.concat(frames, ignore_index=True)
    combined.sort_values("signature_id", inplace=True, kind="stable")
    combined.reset_index(drop=True, inplace=True)
    return combined


def _read_resource_table(resource: str, table_name: str, root: str | Path | None = None) -> pd.DataFrame:
    path = resource_dir(resource, root=root) / f"{table_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Installed resource file is missing: {path}")
    return pd.read_parquet(path)


def installed_resource_values(signature_ids: list[str] | None = None, reference_species: str = "human", root: str | Path | None = None) -> dict[str, list[str] | dict[str, float]]:
    meta = installed_resource_metadata(reference_species=reference_species, root=root)
    if signature_ids is not None:
        requested = set(signature_ids)
        meta = meta.loc[meta["signature_id"].isin(requested)].copy()
    if meta.empty:
        return {}

    results: dict[str, list[str] | dict[str, float]] = {}
    for resource_key, group in meta.groupby("resource_key", sort=False):
        resource_key = str(resource_key)
        format_name = str(group["signature_format"].iloc[0])
        if format_name == "binary":
            table = _read_resource_table(resource_key, "binary", root=root)
            subset = table.loc[table["signature_id"].isin(group["signature_id"])].copy()
            subset.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
            for signature_id, genes in subset.groupby("signature_id", sort=False)["gene"]:
                results[str(signature_id)] = pd.unique(genes).tolist()
        elif format_name == "continuous":
            table = _read_resource_table(resource_key, "continuous", root=root)
            subset = table.loc[table["signature_id"].isin(group["signature_id"])].copy()
            subset.sort_values(["signature_id", "gene"], inplace=True, kind="stable")
            subset = subset.drop_duplicates(subset=["signature_id", "gene"], keep="first")
            for signature_id, frame in subset.groupby("signature_id", sort=False):
                results[str(signature_id)] = {str(gene): float(weight) for gene, weight in zip(frame["gene"], frame["weight"])}
        else:
            raise ValueError(f"Unsupported signature_format for resource {resource_key}: {format_name}")
    return results


def ensure_optional_resource_available(
    signature_ids: list[str] | None = None,
    root: str | Path | None = None,
    *,
    auto_install: bool = True,
    verbose: bool = True,
) -> None:
    if not signature_ids:
        return
    listing = _resource_listing(root=root).set_index("resource", drop=False)
    missing_resources: list[str] = []
    for signature_id in signature_ids:
        resource = resource_name_for_signature_id(signature_id)
        if resource is None:
            continue
        installed = bool(listing.loc[resource, "installed"]) if resource in listing.index else False
        if not installed:
            missing_resources.append(resource)
    if not missing_resources:
        return
    for resource in sorted(set(missing_resources)):
        if auto_install:
            phenosigdb_resources("install", resource, verbose=verbose)
        else:
            raise FileNotFoundError(f"Resource '{resource}' is not installed. Run phenosigdb_resources('install', '{resource}').")
