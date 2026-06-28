from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

GREEK_REPLACEMENTS = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "κ": "kappa",
    "λ": "lambda",
    "μ": "mu",
    "ω": "omega",
}

CELL_FAMILY_RULES = [
    ("fibroblast", "fibroblast"),
    ("myofibroblast", "fibroblast"),
    ("pericyte", "pericyte"),
    ("smooth muscle", "smooth_muscle"),
    ("endothelial", "endothelial"),
    ("epithelial", "epithelial"),
    ("malignant", "tumor"),
    ("tumor", "tumor"),
    ("cancer cell", "tumor"),
    ("ductal", "ductal"),
    ("acinar", "acinar"),
    ("b cell", "B_cell"),
    ("plasma", "plasma_cell"),
    ("cd8", "T_cell"),
    ("cd4", "T_cell"),
    ("t cell", "T_cell"),
    ("t-cell", "T_cell"),
    ("treg", "T_cell"),
    ("nk", "NK_cell"),
    ("natural killer", "NK_cell"),
    ("neutrophil", "neutrophil"),
    ("macrophage", "macrophage"),
    ("monocyte", "monocyte"),
    ("dendritic", "immune"),
    ("immune", "immune"),
    ("stromal", "stromal"),
]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_blank(value: Any) -> str | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def normalize_whitespace(value: Any) -> str | None:
    text = normalize_blank(value)
    if text is None:
        return None
    return re.sub(r"\s+", " ", text)


def normalize_species(value: Any) -> str | None:
    text = normalize_whitespace(value)
    if text is None:
        return None
    key = text.casefold().replace("_", " ")
    compact = re.sub(r"\s+", " ", key)
    mapping = {
        "human": "human",
        "homo sapiens": "human",
        "hs": "human",
        "mouse": "mouse",
        "mus musculus": "mouse",
        "mm": "mouse",
        "mm hs": "mixed",
        "hs mm": "mixed",
        "human mouse": "mixed",
        "mouse human": "mixed",
        "mixed": "mixed",
    }
    if compact in mapping:
        return mapping[compact]
    if "human" in compact and "mouse" in compact:
        return "mixed"
    if compact.startswith("taxon:9606") or compact == "9606":
        return "human"
    if compact.startswith("taxon:10090") or compact == "10090":
        return "mouse"
    return compact.replace(" ", "_")


def normalize_gene_symbol(gene: Any, species: str | None) -> str | None:
    text = normalize_blank(gene)
    if text is None:
        return None
    normalized_species = normalize_species(species)
    if normalized_species == "human":
        return text.upper()
    if normalized_species == "mouse":
        head = text[:1].upper()
        tail = text[1:].lower()
        return head + tail if head else text
    return text


def normalize_cell_type_label(value: Any) -> str | None:
    text = normalize_whitespace(value)
    if text is None:
        return None
    return re.sub(r"\s*/\s*", "/", text)


def infer_cell_family(*values: Any) -> str | None:
    joined = " ".join(filter(None, (normalize_whitespace(value) for value in values))).casefold()
    if not joined:
        return None
    for needle, family in CELL_FAMILY_RULES:
        if needle in joined:
            return family
    return None


def _replace_greek(text: str) -> str:
    out = text
    for greek, ascii_name in GREEK_REPLACEMENTS.items():
        out = out.replace(greek, ascii_name)
        out = out.replace(greek.upper(), ascii_name.capitalize())
    return out


def normalize_id_token(value: Any, uppercase: bool = False) -> str:
    text = normalize_whitespace(value) or ""
    text = _replace_greek(text)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.replace("+", ".pos")
    text = re.sub(r"[^A-Za-z0-9]+", ".", text)
    text = re.sub(r"\.+", ".", text).strip(".")
    if not text:
        text = "unknown"
    return text.upper() if uppercase else text


def make_signature_id(domain: str, source_key: str, signature_name: str) -> str:
    return ".".join(
        [
            normalize_id_token(domain, uppercase=True),
            normalize_id_token(source_key, uppercase=False),
            normalize_id_token(signature_name, uppercase=False),
        ]
    )


def safe_float(value: Any) -> float | None:
    text = normalize_blank(value)
    if text is None:
        return None
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return None
    if math.isnan(number):
        return None
    return number


def safe_int(value: Any) -> int | None:
    number = safe_float(value)
    if number is None:
        return None
    return int(number)


def safe_bool(value: Any) -> bool | None:
    text = normalize_whitespace(value)
    if text is None:
        return None
    mapping = {
        "1": True,
        "0": False,
        "true": True,
        "false": False,
        "yes": True,
        "no": False,
        "y": True,
        "n": False,
    }
    key = text.casefold()
    return mapping.get(key)


def split_genes(value: Any) -> list[str]:
    text = normalize_blank(value)
    if text is None:
        return []
    tokens = [
        token.strip()
        for token in re.split(r"[,\n;\t ]+", text)
        if token.strip()
    ]
    seen: set[str] = set()
    genes: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            genes.append(token)
    return genes


def json_dumps(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def signature_counts(members: pd.DataFrame) -> pd.DataFrame:
    if members.empty:
        return pd.DataFrame(columns=["signature_id", "imported_member_count"])
    counts = (
        members.groupby("signature_id", as_index=False, sort=False)["gene"]
        .nunique()
        .rename(columns={"gene": "imported_member_count"})
    )
    return counts
