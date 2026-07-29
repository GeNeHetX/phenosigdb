from __future__ import annotations

import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from .utils import now_utc_iso, sha256_file


def _download_metadata_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".download.json")


def _read_metadata(path: Path) -> dict[str, Any] | None:
    meta_path = _download_metadata_path(path)
    if not meta_path.exists():
        return None
    return json.loads(meta_path.read_text(encoding="utf-8"))


def download_file(
    url: str,
    destination: str | Path,
    *,
    force: bool = False,
    headers: dict[str, str] | None = None,
    verify_ssl: bool = True,
) -> dict[str, Any]:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not force:
        metadata = _read_metadata(path) or {}
        metadata.setdefault("path", str(path))
        metadata.setdefault("sha256", sha256_file(path))
        metadata.setdefault("bytes", path.stat().st_size)
        metadata["from_cache"] = True
        return metadata

    request_headers = {"User-Agent": "Mozilla/5.0"}
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers, method="GET")
    context = None if verify_ssl else ssl._create_unverified_context()

    sha256 = None
    with urlopen(request, context=context) as response, path.open("wb") as handle:
        import hashlib

        digest = hashlib.sha256()
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            digest.update(chunk)
            handle.write(chunk)
        sha256 = digest.hexdigest()
        metadata = {
            "url": url,
            "resolved_url": response.geturl(),
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha256,
            "content_type": response.headers.get("Content-Type"),
            "source_last_modified": response.headers.get("Last-Modified"),
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "from_cache": False,
        }

    _download_metadata_path(path).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata
