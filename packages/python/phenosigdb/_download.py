from __future__ import annotations

import ssl
from pathlib import Path
from urllib.request import Request, urlopen


def download_to_path(url: str, destination: str | Path, *, headers: dict[str, str] | None = None, verify_ssl: bool = True) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    request_headers = {"User-Agent": "Mozilla/5.0"}
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers, method="GET")
    context = None if verify_ssl else ssl._create_unverified_context()
    with urlopen(request, context=context) as response, path.open("wb") as handle:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            handle.write(chunk)
    return path
