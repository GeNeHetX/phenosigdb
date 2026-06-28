library(readxl)

args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.Wang21")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Wang.etal;DOI:10.1038/s41421-021-00271-4",
    "species: human",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: unknown",
    "tags: CAF;fibroblast",
    "source_author: Wang.etal",
    "source_pmid: ''",
    "source_doi: 10.1038/s41421-021-00271-4"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "41421_2021_271_MOESM19_ESM.xlsx")
sheets <- excel_sheets(raw_path)

members_list <- lapply(sheets, function(sheet_name) {
  cluster_name <- as.character(read_excel(raw_path, sheet = sheet_name, col_names = FALSE, n_max = 1)[[1, 1]])
  dat <- read_excel(raw_path, sheet = sheet_name, skip = 1)
  gene_col <- if ("Gene_name" %in% names(dat)) "Gene_name" else if ("Gene_Name" %in% names(dat)) "Gene_Name" else NA_character_
  if (is.na(gene_col)) {
    stop("Missing gene column in Wang21 sheet: ", sheet_name)
  }
  dat <- dat[!is.na(dat[[gene_col]]) & !is.na(dat$avg_logFC), c(gene_col, "avg_logFC")]
  names(dat)[1] <- "Gene_name"
  dat$avg_logFC <- as.numeric(dat$avg_logFC)
  dat <- dat[dat$avg_logFC > 0, , drop = FALSE]

  if (!nrow(dat)) {
    stop("No positive marker rows found in Wang21 sheet: ", sheet_name)
  }

  signature_name <- normalize_sig(cluster_name)
  data.frame(
    signature_id = paste0("CAF.Wang21.", signature_name),
    signature_name = signature_name,
    gene = as.character(dat$Gene_name),
    stringsAsFactors = FALSE
  )
})

members <- unique(do.call(rbind, members_list))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Wang21 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
