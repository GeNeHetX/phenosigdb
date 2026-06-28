args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.Cords23")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Cords.etal;DOI:10.1038/s41467-023-39762-1",
    "species: human",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: PDAC",
    "tags: CAF;fibroblast",
    "source_author: Cords.etal",
    "source_pmid: ''",
    "source_doi: 10.1038/s41467-023-39762-1"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "Cords23_41467_2023_39762_MOESM6_ESM.csv")
dat <- read.csv(raw_path, stringsAsFactors = FALSE, check.names = FALSE)
dat <- dat[!is.na(dat$cluster) & grepl("CAF", dat$cluster, fixed = TRUE), c("cluster", "gene", "avg_log2FC")]

if (nrow(dat) == 0) {
  stop("No CAF rows found in Cords23 table")
}
if (any(dat$avg_log2FC <= 0, na.rm = TRUE)) {
  stop("Non-positive avg_log2FC found in Cords23 CAF markers")
}

dat$signature_name <- normalize_sig(dat$cluster)
members <- unique(data.frame(
  signature_id = paste0("CAF.Cords23.", dat$signature_name),
  signature_name = dat$signature_name,
  gene = dat$gene,
  stringsAsFactors = FALSE
))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Cords23 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
