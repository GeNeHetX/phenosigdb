"""
PhenoSigDB Parser Tests

Test that parsers produce valid curated output.

Usage:
    # Test all parsers
    pytest curation/tools/tests/test_parsers.py -v
    
    # Test single parser
    pytest curation/tools/tests/test_parsers.py -v -k "CAF_Xing21"
    
    # Test your new parser (add to PARSER_SOURCES list below)
    pytest curation/tools/tests/test_parsers.py::test_parser_produces_valid_output -v -k "YourSourceKey"

Add new parsers to PARSER_SOURCES list at the bottom of this file.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# Path to curation tools
CURATION_TOOLS = Path(__file__).resolve().parents[1]  # tests/ parent is tools/
sys.path.insert(0, str(CURATION_TOOLS))

from phenosigdb_maintainer.validate_source import validate_source, load_source


# List of all curated sources to test
# Format: (source_key, domain)
# Add new sources here when you create them
PARSER_SOURCES = [
    # CAF signatures
    ("CAF.Affo21", "FIBROBLAST"),
    ("CAF.Cords23", "FIBROBLAST"),
    ("CAF.Dominguez20", "FIBROBLAST"),
    ("CAF.Elyada19", "FIBROBLAST"),
    ("CAF.Grout22", "FIBROBLAST"),
    ("CAF.Kieffer20", "FIBROBLAST"),
    ("CAF.Neuzillet22", "FIBROBLAST"),
    ("CAF.Peng26", "FIBROBLAST"),
    ("CAF.Qin23", "FIBROBLAST"),
    ("CAF.ReviewLiu26", "FIBROBLAST"),
    ("CAF.Wang21", "FIBROBLAST"),
    ("CAF.Xing21", "FIBROBLAST"),
    ("CAF.Zhang23", "FIBROBLAST"),
    # Other signatures
    ("CELL.PanglaoDB2020", "CELL"),
    ("Fibroblast.Patrick24", "FIBROBLAST"),
    ("CancerRNASigModels", "CANCER"),
    # Elhossiny26
    ("Elhossiny26", "FIBROBLAST"),
]


def find_parser_info(source_key: str, repo_root: Path) -> tuple[Path, Path, Path]:
    """
    Find parser path and curated dir, handling SourceKey normalization.
    Returns: (parser_path, input_dir, curated_dir)
    """
    import re
    
    # Try exact match first
    input_dir = repo_root / "curation" / "input" / source_key
    parser_path = input_dir / "build_curated.R"
    curated_dir = repo_root / "curation" / "curated" / source_key
    
    if parser_path.exists() and curated_dir.exists():
        return parser_path, input_dir, curated_dir
    
    # Try normalizing dots (CAF.Xing.21 -> CAF.Xing21)
    normalized = re.sub(r'\.(\d{2,})', r'\1', source_key)
    input_dir = repo_root / "curation" / "input" / normalized
    parser_path = input_dir / "build_curated.R"
    curated_dir = repo_root / "curation" / "curated" / normalized
    
    if parser_path.exists() and curated_dir.exists():
        return parser_path, input_dir, curated_dir
    
    # Try listing all input dirs
    input_root = repo_root / "curation" / "input"
    if input_root.exists():
        for item in input_root.iterdir():
            if item.is_dir():
                parser_path = item / "build_curated.R"
                if parser_path.exists():
                    # Check if this matches our source_key
                    item_normalized = re.sub(r'\.(\d{2,})', r'\1', item.name)
                    if source_key in [item.name, item_normalized]:
                        curated_dir = repo_root / "curation" / "curated" / item_normalized
                        return parser_path, item, curated_dir
    
    return None, None, None


def run_parser(source_key: str) -> tuple[bool, str, Path]:
    """
    Run a parser by its SourceKey.
    
    Returns: (success, stdout/stderr, curated_dir)
    """
    repo_root = Path(__file__).resolve().parents[3]
    
    parser_path, input_dir, curated_dir = find_parser_info(source_key, repo_root)
    
    if parser_path is None:
        return False, f"Parser not found: {source_key}", curated_dir
    
    # Run parser using Rscript
    result = subprocess.run(
        ["Rscript", str(parser_path)],
        capture_output=True,
        text=True,
        cwd=str(input_dir)
    )
    
    success = result.returncode == 0
    output = result.stdout + result.stderr
    
    return success, output, curated_dir


@pytest.mark.parametrize("source_key,expected_domain", PARSER_SOURCES)
def test_parser_produces_valid_output(source_key: str, expected_domain: str):
    """
    Test that a parser runs successfully and produces valid output.
    
    This test:
    1. Runs the parser
    2. Checks that it succeeded (exit code 0)
    3. Checks that curated output exists
    4. Validates the output
    """
    success, output, curated_dir = run_parser(source_key)
    
    # Check parser ran successfully
    assert success, f"Parser failed for {source_key}:\n{output}"
    
    # Check curated directory exists
    assert curated_dir.exists(), f"Curated dir not created: {curated_dir}"
    
    # Check source.yaml exists
    yaml_path = curated_dir / "source.yaml"
    assert yaml_path.exists(), f"source.yaml not found: {yaml_path}"
    
    # Check members.tsv exists
    tsv_path = curated_dir / "members.tsv"
    assert tsv_path.exists(), f"members.tsv not found: {tsv_path}"
    
    # Validate the source
    errors = validate_source(source_key)
    assert len(errors) == 0, f"Validation errors for {source_key}:\n" + "\n".join(f"  - {e}" for e in errors)
    
    # Check source.yaml has required fields
    with open(yaml_path, 'r') as f:
        meta = yaml.safe_load(f)
    
    required_fields = ['source', 'species', 'cell_family', 'context', 'disease']
    for field in required_fields:
        assert field in meta, f"Missing required field '{field}' in {source_key}/source.yaml"


@pytest.mark.parametrize("source_key,expected_domain", PARSER_SOURCES)
def test_parser_source_yaml_format(source_key: str, expected_domain: str):
    """Test that source.yaml has correct format and fields."""
    repo_root = Path(__file__).resolve().parents[3]
    
    # Find the actual curated dir (handles SourceKey normalization and DOMAIN prefix)
    _, _, curated_dir = find_parser_info(source_key, repo_root)
    if curated_dir is None or not curated_dir.exists():
        # Try to find curated dir by searching
        curated_root = repo_root / "curation" / "curated"
        for entry in curated_root.iterdir():
            if entry.is_dir() and source_key in entry.name:
                curated_dir = entry
                break
        else:
            pytest.skip(f"Curated dir not found for: {source_key}")
    
    yaml_path = curated_dir / "source.yaml"
    
    if not yaml_path.exists():
        pytest.skip(f"source.yaml not found: {yaml_path}")
    
    with open(yaml_path, 'r') as f:
        meta = yaml.safe_load(f)
    
    # Check required fields exist
    assert 'source' in meta
    assert 'species' in meta
    assert 'cell_family' in meta
    assert 'context' in meta
    assert 'disease' in meta
    assert 'source_author' in meta
    assert 'source_doi' in meta
    
    # Check species is valid
    valid_species = {"human", "mouse", "mixed", "unknown"}
    assert meta['species'] in valid_species, f"Invalid species: {meta['species']}"


@pytest.mark.parametrize("source_key,expected_domain", PARSER_SOURCES)
def test_parser_members_tsv_format(source_key: str, expected_domain: str):
    """Test that members.tsv has correct format."""
    repo_root = Path(__file__).resolve().parents[3]
    
    # Find the actual curated dir (handles SourceKey normalization and DOMAIN prefix)
    _, _, curated_dir = find_parser_info(source_key, repo_root)
    if curated_dir is None or not curated_dir.exists():
        # Try to find curated dir by searching
        curated_root = repo_root / "curation" / "curated"
        for entry in curated_root.iterdir():
            if entry.is_dir() and source_key in entry.name:
                curated_dir = entry
                break
        else:
            pytest.skip(f"Curated dir not found for: {source_key}")
    
    tsv_path = curated_dir / "members.tsv"
    
    if not tsv_path.exists():
        pytest.skip(f"members.tsv not found: {tsv_path}")
    
    import pandas as pd
    df = pd.read_csv(tsv_path, sep='\t')
    
    # Check required columns exist
    assert 'signature_id' in df.columns, "Missing signature_id column"
    assert 'signature_name' in df.columns, "Missing signature_name column"
    assert 'gene' in df.columns, "Missing gene column"
    
    # Check no empty values in required columns
    assert df['signature_id'].notna().all(), "Empty signature_id values"
    assert df['signature_name'].notna().all(), "Empty signature_name values"
    assert df['gene'].notna().all(), "Empty gene values"
    
    # Check at least one signature
    assert len(df) > 0, f"No rows in {source_key}/members.tsv"


# === Test for new parsers (not in PARSER_SOURCES yet) ===


def test_new_parser_template():
    """
    Template for testing a new parser before adding to PARSER_SOURCES.
    
    To test your new parser:
    1. Create the parser in curation/input/YourSourceKey/build_curated.R
    2. Run it manually first: Rscript curation/input/YourSourceKey/build_curated.R
    3. Copy this test and replace 'YourSourceKey' with your actual SourceKey
    4. Run: pytest curation/tools/tests/test_parsers.py::test_new_parser_template -v
    
    Or use the command-line test:
        python curation/tools/tests/test_parser_cli.py YourSourceKey
    """
    # Example: test_parser("YourSourceKey")
    # Uncomment and replace with your SourceKey:
    # source_key = "YourSourceKey"
    # success, output, curated_dir = run_parser(source_key)
    # assert success, f"Parser failed: {output}"
    # errors = validate_source(source_key)
    # assert len(errors) == 0, f"Validation errors: {errors}"
    pass
