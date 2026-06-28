`%||%` <- function(x, y) if (is.null(x) || !length(x)) y else x

args_full <- commandArgs(trailingOnly = FALSE)
file_arg <- args_full[grep("^--file=", args_full)]
script_path <- if (length(file_arg)) sub("^--file=", "", file_arg[[1]]) else sys.frames()[[1]]$ofile
script_dir <- normalizePath(dirname(script_path), winslash = "/", mustWork = TRUE)
repo_root <- normalizePath(file.path(script_dir, "..", "..", "..", ".."), winslash = "/", mustWork = TRUE)
cancerrnasig_dir <- Sys.getenv("CANCERRNASIG_DIR", unset = file.path(dirname(repo_root), "CancerRNASig"))

load(file.path(cancerrnasig_dir, "data", "molGradsys.rda"))
load(file.path(cancerrnasig_dir, "data", "GP2model_simple.rda"))

curation_root <- file.path(repo_root, "signatures", "curation")

normalize_gene <- function(x) {
  x <- trimws(iconv(as.character(x), to = "ASCII//TRANSLIT", sub = ""))
  x <- toupper(x)
  x[nchar(x) == 0L] <- NA_character_
  x
}

split_aliases <- function(x) {
  trimws(unlist(strsplit(x, "///", fixed = TRUE), use.names = FALSE))
}

keep_strongest_weight <- function(tab) {
  tab <- tab[order(abs(tab$weight), decreasing = TRUE), , drop = FALSE]
  tab[!duplicated(tab$gene), , drop = FALSE]
}

build_pamg_members <- function() {
  out <- list()
  for (model_name in names(molGradsys)) {
    mg <- molGradsys[[model_name]]
    weights <- as.numeric(mg$gw[, mg$k]) * as.numeric(mg$dir)
    genes <- rownames(mg$gw)
    expanded <- data.frame(
      gene = unlist(lapply(genes, split_aliases), use.names = FALSE),
      weight = rep(weights, lengths(lapply(genes, split_aliases))),
      stringsAsFactors = FALSE
    )
    expanded$gene <- normalize_gene(expanded$gene)
    expanded <- expanded[!is.na(expanded$gene), , drop = FALSE]
    expanded <- keep_strongest_weight(expanded)
    expanded$signature_id <- paste("PDAC", "PAMG20", model_name, sep = ".")
    expanded$signature_name <- model_name
    out[[model_name]] <- expanded[, c("signature_id", "signature_name", "gene", "weight")]
  }
  members <- do.call(rbind, out)
  members <- members[order(members$signature_id, members$gene), , drop = FALSE]
  rownames(members) <- NULL
  members
}

build_gempred_members <- function() {
  tab <- GP2model_simple[, c(1, 3)]
  names(tab) <- c("gene", "weight")
  tab$gene <- normalize_gene(tab$gene)
  tab <- tab[!is.na(tab$gene), , drop = FALSE]
  tab$weight <- as.numeric(tab$weight)
  tab <- keep_strongest_weight(tab)
  tab$signature_id <- "PDAC.GemPred20.Simple"
  tab$signature_name <- "Simple"
  tab <- tab[, c("signature_id", "signature_name", "gene", "weight")]
  tab <- tab[order(tab$gene), , drop = FALSE]
  rownames(tab) <- NULL
  tab
}

write_source_yaml <- function(path, source, doi, tags) {
  lines <- c(
    paste0("source: ", source, ";DOI:", doi),
    "species: human",
    "cell_family: tumor",
    "context: cancer",
    "disease: PDAC",
    paste0("tags: ", tags),
    paste0("source_author: ", source),
    "source_pmid: null",
    paste0("source_doi: ", doi),
    ""
  )
  writeLines(lines, con = path, useBytes = TRUE)
}

write_curated_source <- function(dir_name, members, source, doi, tags) {
  out_dir <- file.path(curation_root, dir_name)
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  utils::write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
  write_source_yaml(file.path(out_dir, "source.yaml"), source = source, doi = doi, tags = tags)
}

write_curated_source(
  "PDAC.PAMG20",
  build_pamg_members(),
  source = "PDACMolGrad",
  doi = "10.1016/j.ebiom.2020.102858",
  tags = "PDAC;model;continuous;molecular_gradient"
)

write_curated_source(
  "PDAC.GemPred20",
  build_gempred_members(),
  source = "GemPred",
  doi = "10.1016/j.annonc.2020.10.601",
  tags = "PDAC;model;continuous;gemcitabine"
)

cat("Wrote PDAC.PAMG20 and PDAC.GemPred20 curated weighted signatures\n")
