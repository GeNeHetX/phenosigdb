from __future__ import annotations

import argparse
import re
from pathlib import Path

from .build import build_database

ROOT = Path(__file__).resolve().parents[1]

VERSION_TARGETS = [
    (
        ROOT / "pyproject.toml",
        re.compile(r'(^version\s*=\s*")([^"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
    (
        ROOT / "phenosigdb" / "__init__.py",
        re.compile(r'(^__version__\s*=\s*")([^"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
    (
        ROOT / "python" / "pyproject.toml",
        re.compile(r'(^version\s*=\s*")([^"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
    (
        ROOT / "python" / "phenosigdb" / "_version.py",
        re.compile(r'(^__version__\s*=\s*")([^"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
    (
        ROOT / "rpkg" / "DESCRIPTION",
        re.compile(r"(^Version:\s*)([^\n]+)$", flags=re.MULTILINE),
        r"\g<1>{version}",
    ),
    (
        ROOT / "rpkg" / "R" / "phenosigdb.R",
        re.compile(r'(^\.phenosigdb_package_version\s*<-\s*")([^"]+)(")', flags=re.MULTILINE),
        r"\g<1>{version}\g<3>",
    ),
]


def _validate_version(version: str) -> str:
    text = version.strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", text):
        raise ValueError("version must look like MAJOR.MINOR.PATCH, for example 0.1.3")
    return text


def _replace_version(path: Path, pattern: re.Pattern[str], template: str, version: str) -> None:
    content = path.read_text(encoding="utf-8")
    replaced, count = pattern.subn(template.format(version=version), content, count=1)
    if count != 1:
        raise ValueError(f"Could not update version in {path}")
    path.write_text(replaced, encoding="utf-8")


def bump_versions(version: str, root: str | Path | None = None) -> None:
    version = _validate_version(version)
    base = Path(root) if root is not None else ROOT
    for path, pattern, template in VERSION_TARGETS:
        target = base / path.relative_to(ROOT)
        _replace_version(target, pattern, template, version)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a PhenoSigDB release")
    parser.add_argument("version", help="New version number, for example 0.1.3")
    parser.add_argument("--download-homology", action="store_true", help="Refresh homology before rebuilding")
    args = parser.parse_args()

    version = _validate_version(args.version)
    bump_versions(version)
    build_database(download_homology=args.download_homology)

    print(f"Prepared release {version}")
    print("Next steps:")
    print("1. Run tests")
    print("2. Review README and built artifacts")
    print(f"3. Commit and tag v{version}")
    print("4. Push branch and tag")
    print("5. Publish the GitHub release")


if __name__ == "__main__":
    main()
