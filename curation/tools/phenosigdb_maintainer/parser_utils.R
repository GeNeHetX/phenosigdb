#' PhenoSigDB Parser Utilities
#'
#' Shared helper functions for signature parsers.
#' Source this file in your build_curated.R:
#'   source(file.path(repo_dir, "tools", "phenosigdb_maintainer", "parser_utils.R"))

#' Normalize signature ID or name to canonical format
#'
#' Converts spaces, underscores, hyphens, slashes to dots.
#' Collapses multiple dots to single dot.
#' Trims leading/trailing dots.
#'
#' @param x character vector to normalize
#' @return normalized character vector
#' @examples
#' normalize_sig("My CAF Signature")  # -> "My.CAF.Signature"
#' normalize_sig("Fibro-C1 / Pericyte")  # -> "Fibro.C1.Pericyte"
normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

#' Split gene string into individual gene symbols
#'
#' Splits on commas, newlines, semicolons, tabs, or spaces.
#' Trims whitespace, removes empty strings, returns unique values.
#'
#' @param text character string containing gene symbols
#' @return character vector of unique gene symbols
#' @examples
#' split_genes("ACTA2, COL1A1, ACTA2")  # -> c("ACTA2", "COL1A1")
#' split_genes("gene1; gene2\ngene3")  # -> c("gene1", "gene2", "gene3")
split_genes <- function(text) {
  if (is.null(text) || length(text) == 0 || is.na(text)) {
    return(character(0))
  }
  # Split on common delimiters
  tokens <- trimws(unlist(strsplit(as.character(text), "[,\\n;\\t ]+")))
  # Remove empty strings
  tokens <- tokens[nzchar(tokens)]
  # Return unique
  unique(tokens)
}

#' Write source.yaml metadata file
#'
#' Creates a properly formatted YAML file with signature metadata.
#'
#' @param path file path for source.yaml
#' @param source short source identifier
#' @param source_author author name (e.g., "Smith.etal")
#' @param source_pmid PubMed ID (optional)
#' @param source_doi DOI
#' @param species species: "human", "mouse", "mixed", "unknown"
#' @param cell_family cell family (see ALLOWED_CELL_FAMILY)
#' @param context context (see ALLOWED_CONTEXT)
#' @param disease disease name or "unknown"
#' @param tags character vector of tags (optional)
#' @examples
#' write_source_yaml(
#'   path = " curation/curated/CELL.Smith24/source.yaml",
#'   source = "Smith24",
#'   source_author = "Smith.etal",
#'   source_doi = "10.1038/xyz",
#'   species = "human",
#'   cell_family = "fibroblast",
#'   context = "cancer",
#'   disease = "unknown"
#' )
write_source_yaml <- function(
    path,
    source,
    source_author,
    source_pmid = "",
    source_doi = "",
    species,
    cell_family,
    context,
    disease,
    tags = NULL
) {
  lines <- c(
    sprintf("source: %s", source),
    sprintf("species: %s", species),
    sprintf("cell_family: %s", cell_family),
    sprintf("context: %s", context),
    sprintf("disease: %s", disease),
    if (!is.null(tags) && length(tags) > 0) sprintf("tags: %s", paste(tags, collapse = ";")) else "tags: ''",
    sprintf("source_author: %s", source_author),
    sprintf("source_pmid: '%s'", source_pmid),
    sprintf("source_doi: %s", source_doi)
  )
  writeLines(lines, path)
}

#' Infer species from gene symbols
#'
#' Human genes typically have mixed case (e.g., "Tcra", "CD4").
#' Mouse genes are typically all uppercase (e.g., "Tcra", "Cd4") or Title Case.
#'
#' @param genes character vector of gene symbols
#' @return "human", "mouse", or "unknown"
#' @examples
#' infer_species(c("ACTA2", "COL1A1", "Tcra"))  # -> "human"
#' infer_species(c("Acta2", "Col1a1"))         # -> "mouse"
infer_species <- function(genes) {
  if (length(genes) == 0) {
    return("unknown")
  }
  
  # Count genes with lowercase letters (human) vs all uppercase/title case (mouse)
  has_lower <- grepl("[a-z]", genes)
  human_count <- sum(has_lower)
  mouse_count <- length(genes) - human_count
  
  if (human_count > mouse_count) {
    return("human")
  } else if (mouse_count > human_count) {
    return("mouse")
  }
  
  return("unknown")
}

#' Infer cell family from signature name or label
#'
#' Uses keyword matching against known cell family patterns.
#'
#' @param label signature name or label
#' @param override_rules named list of additional patterns (optional)
#' @return cell family string or "unknown"
#' @examples
#' infer_cell_family("Fibro-C1")  # -> "fibroblast"
#' infer_cell_family("T_cell_marker")  # -> "T_cell"
infer_cell_family <- function(label, override_rules = NULL) {
  # Default keyword mappings (from ALLOWED_CELL_FAMILY in io.py)
  rules <- list(
    fibroblast = c("fibro", "caf", "fibroblast", "myofibroblast"),
    endothelial = c("endo", "endothelial", "vascular"),
    epithelial = c("epi", "epithelial", "epithel"),
    tumor = c("tumor", "cancer", "carcinoma", "neoplasm", "malignant"),
    macrophage = c("macro", "macrophage", "monocyte", "mono"),
    T_cell = c("t.cell", "t cell", "t-cell", "cd4", "cd8", "th1", "th2", "tcells"),
    B_cell = c("b.cell", "b cell", "b-cell", "bcells"),
    plasma_cell = c("plasma", "plasma.cell", "plasma cell"),
    NK_cell = c("nk", "nk.cell", "natural killer", "nk cell"),
    immune = c("immune", "leukocyte", "lymphocyte", "white blood"),
    stromal = c("stromal", "stroma"),
    ductal = c("ductal", "duct"),
    acinar = c("acinar", "acinus"),
    endocrine = c("endocrine", "hormone"),
    pericyte = c("pericyte", "perivascular"),
    smooth_muscle = c("smooth.muscle", "smooth muscle", "vsms", "sma"),
    neuron = c("neuron", "neural", "nerve"),
    glial = c("glial", "astrocyte", "oligodendrocyte", "microglia")
  )
  
  # Merge with override rules
  if (!is.null(override_rules)) {
    rules <- c(rules, override_rules)
  }
  
  label_lower <- tolower(label)
  
  for (family in names(rules)) {
    for (pattern in rules[[family]]) {
      if (grepl(pattern, label_lower, ignore.case = TRUE)) {
        return(family)
      }
    }
  }
  
  return("unknown")
}
