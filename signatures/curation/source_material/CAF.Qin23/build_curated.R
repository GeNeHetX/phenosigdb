library(readxl)

args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.Qin23")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Qin.etal",
    "species: human",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: PDAC",
    "tags: CAF;fibroblast",
    "source_author: Qin.etal",
    "source_pmid: ''",
    "source_doi: ''"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "Qin23_mmc3.xls")
dat <- read_excel(raw_path, skip = 1)
dat <- dat[!is.na(dat$cluster), c("cluster", "gene", "avg_log2FC")]

if (nrow(dat) == 0) {
  stop("No subtype rows found in Qin23 table")
}
if (any(dat$avg_log2FC <= 0, na.rm = TRUE)) {
  stop("Non-positive avg_log2FC found in Qin23 markers")
}

dat$signature_name <- normalize_sig(dat$cluster)
members <- unique(data.frame(
  signature_id = paste0("CAF.Qin23.", dat$signature_name),
  signature_name = dat$signature_name,
  gene = dat$gene,
  stringsAsFactors = FALSE
))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Qin23 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
