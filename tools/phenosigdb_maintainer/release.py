from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .build import build_database
from .external_imports.registry import run_importers
from .resource_build import package_runtime_resource
from .validate import validate_database

ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = ROOT / "VERSION"

VERSION_TARGETS = [
    (
        Path("packages/python/pyproject.toml"),
        re.compile(r'(^version\s*=\s*")([^\"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
    (
        Path("packages/python/phenosigdb/_version.py"),
        re.compile(r'(^__version__\s*=\s*")([^\"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
    (
        Path("packages/r/DESCRIPTION"),
        re.compile(r"(^Version:\s*)([^\n]+)$", flags=re.MULTILINE),
        r"\g<1>{version}",
    ),
    (
        Path("packages/r/R/phenosigdb.R"),
        re.compile(r'(^\.phenosigdb_package_version\s*<-\s*")([^\"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
]


def validate_version(version: str) -> str:
    text = version.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", text):
        raise ValueError("version must look like MAJOR.MINOR.PATCH, for example 0.1.6")
    return text


def require_new_version(version: str) -> str:
    version = validate_version(version)
    current = validate_version(VERSION_FILE.read_text(encoding="utf-8"))
    if tuple(map(int, version.split("."))) <= tuple(map(int, current.split("."))):
        raise ValueError(f"new version must be greater than current version {current}")
    return version


def bump_versions(version: str, root: str | Path | None = None) -> None:
    version = validate_version(version)
    base = Path(root) if root is not None else ROOT
    for relative_path, pattern, template in VERSION_TARGETS:
        target = base / relative_path
        content = target.read_text(encoding="utf-8")
        replaced, count = pattern.subn(template.format(version=version), content, count=1)
        if count != 1:
            raise ValueError(f"Could not update version in {target}")
        target.write_text(replaced, encoding="utf-8")


def _run(command: list[str], *, cwd: Path = ROOT) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _write_version(version: str) -> None:
    VERSION_FILE.write_text(version + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_report(version: str, log_path: Path) -> Path:
    dist = ROOT / "dist"
    assets = []
    for path in sorted(dist.glob("*.tar.gz")):
        assets.append({"file": path.name, "bytes": path.stat().st_size, "sha256": _sha256(path)})
    report = {
        "version": version,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "log": log_path.name,
        "assets": assets,
    }
    path = dist / "release_manifest.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def _check_generated_files() -> None:
    required = [
        ROOT / "data" / "phenosigdb.parquet",
        ROOT / "data" / "phenosigdb_human.parquet",
        ROOT / "data" / "phenosigdb_mouse.parquet",
        ROOT / "README.md",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing generated release files: {', '.join(missing)}")
    for path in required:
        relative = str(path.relative_to(ROOT))
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", relative], cwd=ROOT, capture_output=True)
        ignored = subprocess.run(["git", "check-ignore", "--quiet", relative], cwd=ROOT)
        if tracked.returncode != 0 and ignored.returncode != 0:
            raise RuntimeError(f"Generated file is neither tracked nor ignored: {relative}")


def check_release_dependencies() -> None:
    try:
        from .external_imports.importers.celltypist import _require_celltypist

        _require_celltypist()
    except ImportError as exc:
        raise RuntimeError(
            "Release requires the CellTypist importer dependency. "
            "Install maintainer dependencies before releasing, for example: "
            "pip install celltypist"
        ) from exc


def build_r_release(version: str) -> Path:
    dist = ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    for old in dist.glob("phenosigdb*.tar.gz"):
        old.unlink()

    _run(["R", "CMD", "build", str(ROOT / "packages" / "r")], cwd=dist)
    versioned = dist / f"phenosigdb_{version}.tar.gz"
    if not versioned.exists():
        candidates = sorted(dist.glob("phenosigdb_*.tar.gz"))
        if len(candidates) != 1:
            raise FileNotFoundError("R CMD build did not create the expected PhenoSigDB source archive")
        candidates[0].rename(versioned)
    shutil.copy2(versioned, dist / "phenosigdb-r.tar.gz")
    return versioned


def refresh_external_resources(version: str) -> list[Path]:
    """Refresh staged resources and validate direct upstream resources.

    Redistributable runtime archives are built here. Licensed/direct resources
    are downloaded into a temporary cache and parsed, but are not redistributed.
    """
    dist = ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    for old in dist.glob("phenosigdb-resource-*.tar.gz"):
        old.unlink()

    # Importers reuse their ignored raw-download cache. They still rebuild the
    # generated tables and write a fresh manifest on every release.
    run_importers(("celltypist", "cellmarker"), force=False)
    archives: list[Path] = []
    for resource in ("celltypist", "cellmarker"):
        archive = dist / f"phenosigdb-resource-{resource}.tar.gz"
        package_runtime_resource(resource, archive, package_version=version)
        archives.append(archive)

    # Exercise every direct source in an isolated cache. This checks URLs,
    # parsing, schemas, and metadata without retaining licensed source files.
    from phenosigdb.resources import RESOURCE_SPECS, _fetch_resource

    cache_root = ROOT / ".cache" / "phenosigdb-release-resources"
    cache_root.mkdir(parents=True, exist_ok=True)
    for resource, spec in RESOURCE_SPECS.items():
        if spec.install_kind == "archive":
            continue
        _fetch_resource(resource, action_key="update", force=False, verbose=False, root=cache_root)
    return archives


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and verify a PhenoSigDB release")
    parser.add_argument("version", help="New version number, for example 0.1.6")
    args = parser.parse_args()

    try:
        version = require_new_version(args.version)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        check_release_dependencies()
    except RuntimeError as exc:
        parser.error(str(exc))
    dist = ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    log_path = dist / f"release-{version}.log"
    log_path.write_text(f"PhenoSigDB release {version}\nStarted: {datetime.now(timezone.utc).isoformat()}\n\n", encoding="utf-8")
    resource_archives: list[Path] = []

    def refresh_stage() -> None:
        nonlocal resource_archives
        resource_archives = refresh_external_resources(version)

    stages = [
        ("Build curated and translated core data", lambda: build_database(download_homology=True)),
        ("Validate core data", lambda: ([validate_database(reference_species=species) for species in ("original", "human", "mouse")], _check_generated_files())),
        ("Refresh external resources", refresh_stage),
        ("Run Python tests", lambda: _run(["pytest", "-q", "packages/python/tests"])),
        ("Run maintainer tests", lambda: _run(["pytest", "-q", "tests/maintainer"])),
        ("Synchronize package versions", lambda: (_write_version(version), bump_versions(version))),
        ("Build R package", lambda: build_r_release(version)),
    ]
    results = {}
    for index, (name, action) in enumerate(stages, start=1):
        started = time.monotonic()
        line = f"[{index}/{len(stages)}] {name}"
        print(line)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(line + "\n")
        try:
            result = action()
        except Exception as exc:
            elapsed = time.monotonic() - started
            failure = f"FAILED after {elapsed:.1f}s: {exc}"
            print(failure)
            with log_path.open("a", encoding="utf-8") as log:
                log.write(failure + "\n")
            raise
        elapsed = time.monotonic() - started
        results[name] = round(elapsed, 2)
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"OK ({elapsed:.1f}s)\n\n")

    archive = dist / f"phenosigdb_{version}.tar.gz"
    _run(["R", "CMD", "check", "--no-manual", str(archive)])
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"R CMD check: OK\nTimings: {json.dumps(results)}\n")
    report_path = _release_report(version, log_path)

    print(f"Prepared release {version}")
    print(f"R package: {archive}")
    for resource_archive in resource_archives:
        print(f"Resource archive: {resource_archive}")
    print(f"Release log: {log_path}")
    print(f"Release manifest: {report_path}")
    print("Next steps: commit, push main, tag v<version>, push the tag, and upload all dist archives to the GitHub release.")


if __name__ == "__main__":
    main()
