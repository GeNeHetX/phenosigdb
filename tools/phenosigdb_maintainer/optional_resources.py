from __future__ import annotations

OPTIONAL_RESOURCES = [
    {
        "resource": "celltypist",
        "prefix": "CELL.CellTypist.*",
        "collection": "CellTypist",
        "signature_format": "continuous",
        "context": "cell_type",
    },
    {
        "resource": "cellmarker",
        "prefix": "CELL.CellMarker.*",
        "collection": "CellMarker",
        "signature_format": "binary",
        "context": "cell_type",
    },
    {
        "resource": "msigdb_c7immune",
        "prefix": "PATHWAY.MSigDB.C7_*",
        "collection": "msigdb.C7",
        "signature_format": "binary",
        "context": "immunology",
    },
    {
        "resource": "msigdb_c8celltype",
        "prefix": "PATHWAY.MSigDB.C8_*",
        "collection": "msigdb.C8",
        "signature_format": "binary",
        "context": "cell_type",
    },
    {
        "resource": "pid",
        "prefix": "PATHWAY.PID_*",
        "collection": "PID",
        "signature_format": "binary",
        "context": "pathway",
    },
    {
        "resource": "biocarta",
        "prefix": "PATHWAY.BioCarta_*",
        "collection": "BioCarta",
        "signature_format": "binary",
        "context": "pathway",
    },
    {
        "resource": "reactome",
        "prefix": "PATHWAY.Reactome_*",
        "collection": "Reactome",
        "signature_format": "binary",
        "context": "pathway",
    },
    {
        "resource": "wikipathways",
        "prefix": "PATHWAY.WikiPathways_*",
        "collection": "WikiPathways",
        "signature_format": "binary",
        "context": "pathway",
    },
]
