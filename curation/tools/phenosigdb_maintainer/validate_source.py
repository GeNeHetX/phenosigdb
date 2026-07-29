"""
Validate a single curated source without building the full database.

Usage as module:
    from phenosigdb_maintainer.validate_source import validate_source, main

Usage as script:
    python curation/tools/phenosigdb-validate-source [SOURCE_KEY | --changed | --all]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from .io import (
    ALLOWED_CELL_FAMILY,
    ALLOWED_CONTEXT,
    ALLOWED_SPECIES,
    CANONICAL_COLUMNS,
    normalize_blank,
)


def load_source(source_key: str, curated_dir: Path | None = None) -> pd.DataFrame:
    """Load a single curated source from its members.tsv."""
    if curated_dir is None:
        repo_root = Path(__file__).resolve().parents[3]
        curated_dir = repo_root / "curation" / "curated" / source_key
    else:
        curated_dir = Path(curated_dir)

    members_path = curated_dir / "members.tsv"
    if not members_path.exists():
        raise FileNotFoundError(f"members.tsv not found at {members_path}")

    return pd.read_csv(members_path, sep="\t")


def validate_source(source_key: str, curated_dir: Path | None = None) -> list[str]:
    """
    Validate a single curated source.
    
    Returns list of error messages. Empty list means valid.
    """
    errors = []

    try:
        df = load_source(source_key, curated_dir)
    except Exception as e:
        errors.append(f"Failed to load source: {e}")
        return errors

    # Only check columns that are in members.tsv (source.yaml has the rest)
    required_in_members = ["signature_id", "signature_name", "gene"]
    missing_cols = [col for col in required_in_members if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns in members.tsv: {', '.join(missing_cols)}")

    # Check for extra columns (warn but don't error)
    canonical_members_cols = ["signature_id", "signature_name", "gene", "weight"]
    extras = [col for col in df.columns if col not in canonical_members_cols]
    if extras:
        errors.append(f"Unexpected columns in members.tsv: {', '.join(extras)}")

    # Check non-empty for required columns
    for col in ["signature_id", "signature_name", "gene"]:
        if col not in df.columns:
            continue
        empty = df[col].map(normalize_blank).isna()
        if empty.any():
            count = int(empty.sum())
            errors.append(f"Column '{col}' contains {count} missing or empty values")

    # Check for duplicates
    if "signature_id" in df.columns and "gene" in df.columns:
        duplicates = df.duplicated(subset=["signature_id", "gene"])
        if duplicates.any():
            dup_count = duplicates.sum()
            errors.append(f"Duplicate signature_id + gene pairs: {dup_count}")

    # Check weight consistency
    if "weight" in df.columns:
        numeric_weight = pd.to_numeric(df["weight"], errors="coerce")
        invalid_weight = df["weight"].notna() & numeric_weight.isna()
        if invalid_weight.any():
            count = int(invalid_weight.sum())
            errors.append(f"Column 'weight' contains {count} non-numeric values")
        
        if "signature_id" in df.columns:
            format_flags = (
                df.assign(__has_weight=numeric_weight.notna())
                .groupby("signature_id", sort=True)["__has_weight"]
                .agg(["any", "all"])
            )
            mixed = format_flags.loc[format_flags["any"] & ~format_flags["all"]]
            if not mixed.empty:
                bad = ", ".join(mixed.index[:5].tolist())
                errors.append(f"Weighted and unweighted rows are mixed within signatures: {bad}")

    return errors


def get_changed_sources() -> list[str]:
    """Get list of changed curated sources since last commit."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = result.stdout.strip().split("\n")
    except Exception:
        return []

    curated_dirs = set()
    for f in changed_files:
        if f.startswith("curation/curated/"):
            parts = f.split("/")
            if len(parts) >= 3:
                curated_dirs.add(".".join(parts[2:3]))  # DOMAIN.SourceKey
    
    return sorted(curated_dirs)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate PhenoSigDB curated sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python curation/tools/phenosigdb-validate-source CAF.Xing21
  python curation/tools/phenosigdb-validate-source --changed
  python curation/tools/phenosigdb-validate-source --all
        """
    )
    parser.add_argument(
        "source_key",
        nargs="?",
        default=None,
        help="Source key to validate (e.g., CAF.Xing21). Use --changed or --all instead."
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="Validate only sources changed since last commit"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all curated sources"
    )

    args = parser.parse_args()

    if args.changed:
        sources = get_changed_sources()
        if not sources:
            print("No changed curated sources found.")
            sys.exit(0)
        print(f"Validating {len(sources)} changed source(s): {', '.join(sources)}")
    elif args.all:
        repo_root = Path(__file__).resolve().parents[3]
        curated_dir = repo_root / "curation" / "curated"
        sources = []
        for entry in curated_dir.iterdir():
            if entry.is_dir():
                sources.append(entry.name)
        print(f"Validating {len(sources)} curated source(s)")
    elif args.source_key:
        sources = [args.source_key]
    else:
        parser.error("Please specify a source_key, --changed, or --all")

    all_errors = {}
    for source in sources:
        errors = validate_source(source)
        if errors:
            all_errors[source] = errors

    if all_errors:
        print("\nValidation ERRORS:")
        for source, errors in all_errors.items():
            print(f"\n  {source}:")
            for error in errors:
                print(f"    - {error}")
        sys.exit(1)
    else:
        print("\nAll sources validated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
