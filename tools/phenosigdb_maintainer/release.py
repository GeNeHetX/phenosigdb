from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

from .build import build_database
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and verify a PhenoSigDB release")
    parser.add_argument("version", help="New version number, for example 0.1.6")
    parser.add_argument("--download-homology", action="store_true", help="Refresh homology before building")
    args = parser.parse_args()

    version = validate_version(args.version)
    _write_version(version)
    bump_versions(version)
    build_database(download_homology=args.download_homology)
    validate_database(reference_species="original")
    for species in ("human", "mouse"):
        validate_database(reference_species=species)

    _run(["pytest", "-q", "packages/python/tests"])
    _run(["pytest", "-q", "tests/maintainer"])
    archive = build_r_release(version)
    _run(["R", "CMD", "check", "--no-manual", str(archive)])

    print(f"Prepared release {version}")
    print(f"R package: {archive}")
    print("Next steps: commit, push main, tag v<version>, push the tag, and upload both dist archives to the GitHub release.")


if __name__ == "__main__":
    main()
