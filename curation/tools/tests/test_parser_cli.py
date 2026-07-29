#!/usr/bin/env python3
"""
Command-line tool to test a single parser.

Usage:
    python curation/tools/tests/test_parser_cli.py <SourceKey>

Examples:
    # Test existing parser
    python curation/tools/tests/test_parser_cli.py CAF.Xing21
    
    # Test new parser you're developing
    python curation/tools/tests/test_parser_cli.py MyNewSource26

This runs:
1. Parser execution
2. Output validation
3. Reports success/failure with details
"""

import subprocess
import sys
from pathlib import Path

# Add curation/tools to path
CURATION_TOOLS = Path(__file__).resolve().parents[1]  # tests/ parent is tools/
sys.path.insert(0, str(CURATION_TOOLS))

from phenosigdb_maintainer.validate_source import validate_source


def find_parser_path(source_key: str, repo_root: Path) -> tuple[Path, Path]:
    """
    Find parser path, trying both original and normalized SourceKey.
    Returns: (parser_path, input_dir)
    """
    import re
    
    # Try exact match first
    input_dir = repo_root / "curation" / "input" / source_key
    parser_path = input_dir / "build_curated.R"
    if parser_path.exists():
        return parser_path, input_dir
    
    # Try normalizing dots (CAF.Xing.21 -> CAF.Xing21)
    normalized = re.sub(r'\.(\d{2,})', r'\1', source_key)  # Remove dot before year
    input_dir = repo_root / "curation" / "input" / normalized
    parser_path = input_dir / "build_curated.R"
    if parser_path.exists():
        return parser_path, input_dir
    
    # Try listing all input dirs and find match
    input_root = repo_root / "curation" / "input"
    if input_root.exists():
        for item in input_root.iterdir():
            if item.is_dir():
                # Check if source_key matches (with or without dots)
                item_normalized = re.sub(r'\.(\d{2,})', r'\1', item.name)
                if source_key in [item.name, item_normalized]:
                    parser_path = item / "build_curated.R"
                    if parser_path.exists():
                        return parser_path, item
    
    return None, None


def run_parser(source_key: str) -> tuple[bool, str, Path]:
    """Run parser and return (success, output, curated_dir)."""
    repo_root = Path(__file__).resolve().parents[3]
    
    parser_path, input_dir = find_parser_path(source_key, repo_root)
    
    if parser_path is None:
        input_root = repo_root / "curation" / "input"
        available = "\n".join(f"  - {d.name}" for d in input_root.iterdir() if d.is_dir())
        return False, f"Parser not found for SourceKey: {source_key}\n\nAvailable parsers:\n{available}", input_root
    
    result = subprocess.run(
        ["Rscript", str(parser_path)],
        capture_output=True,
        text=True,
        cwd=str(input_dir)
    )
    
    success = result.returncode == 0
    output = result.stdout + result.stderr
    
    # Infer curated_dir from parser output or convention
    # The curated dir uses DOMAIN.SourceKey format, so we need to find it
    # Try common domains as prefix
    curated_dir = repo_root / "curation" / "curated" / source_key
    if not curated_dir.exists():
        # Try normalized version
        import re
        normalized = re.sub(r'\.(\d{2,})', r'\1', source_key)
        curated_dir = repo_root / "curation" / "curated" / normalized
    
    # If still not found, search for directories containing source_key
    if not curated_dir.exists():
        curated_root = repo_root / "curation" / "curated"
        for entry in curated_root.iterdir():
            if entry.is_dir() and source_key in entry.name:
                curated_dir = entry
                break
        else:
            curated_dir = None
    
    return success, output, curated_dir


def main():
    if len(sys.argv) < 2:
        print("Usage: python curation/tools/tests/test_parser_cli.py <SourceKey>")
        print()
        print("Examples:")
        print("  python curation/tools/tests/test_parser_cli.py CAF.Xing21")
        print("  python curation/tools/tests/test_parser_cli.py MyNewSource26")
        sys.exit(1)
    
    source_key = sys.argv[1]
    print(f"Testing parser: {source_key}")
    print("=" * 60)
    
    # Run parser
    print(f"[1/3] Running parser...")
    success, output, curated_dir = run_parser(source_key)
    
    if not success:
        print(f"❌ Parser FAILED")
        print()
        print("Output:")
        print(output)
        sys.exit(1)
    
    print(f"✅ Parser succeeded")
    print(f"   Output dir: {curated_dir}")
    
    # Check files exist
    print(f"[2/3] Checking output files...")
    yaml_path = curated_dir / "source.yaml"
    tsv_path = curated_dir / "members.tsv"
    
    if not yaml_path.exists():
        print(f"❌ source.yaml not found: {yaml_path}")
        sys.exit(1)
    print(f"   ✅ source.yaml exists")
    
    if not tsv_path.exists():
        print(f"❌ members.tsv not found: {tsv_path}")
        sys.exit(1)
    print(f"   ✅ members.tsv exists")
    
    # Validate
    print(f"[3/3] Validating output...")
    # Use the actual curated_dir name (which includes DOMAIN prefix)
    curated_source_key = curated_dir.name
    errors = validate_source(curated_source_key)
    
    if errors:
        print(f"❌ Validation FAILED")
        print()
        print("Errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    print(f"✅ Validation passed")
    print()
    print("=" * 60)
    print(f"✅ ALL CHECKS PASSED for {source_key}")
    print()
    print("Next steps:")
    print(f"  - Review output: {curated_dir}")
    print(f"  - Add to test suite: edit curation/tools/tests/test_parsers.py")
    print(f"  - Commit changes")


if __name__ == "__main__":
    main()
