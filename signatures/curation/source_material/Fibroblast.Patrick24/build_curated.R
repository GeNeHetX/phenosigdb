library(readxl)

args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "FIBROBLAST.Patrick24")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Patrick.etal;DOI:10.1126/sciadv.adk8501",
    "species: mouse",
    "cell_family: fibroblast",
    "context: unknown",
    "disease: unknown",
    "tags: fibroblast",
    "source_author: Patrick.etal",
    "source_pmid: ''",
    "source_doi: 10.1126/sciadv.adk8501"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "Patrick24_Table S1.xlsx")
sheets <- excel_sheets(raw_path)
members_list <- vector("list", length(sheets))

for (i in seq_along(sheets)) {
  sheet <- sheets[[i]]
  dat <- read_excel(raw_path, sheet = sheet)
  dat <- dat[!is.na(dat$Gene), c("Gene", "avg_log2FC")]
  if (nrow(dat) == 0) {
    stop("No marker rows found in Patrick24 sheet: ", sheet)
  }
  if (any(as.numeric(dat$avg_log2FC) <= 0, na.rm = TRUE)) {
    stop("Non-positive avg_log2FC found in Patrick24 sheet: ", sheet)
  }

  signature_name <- normalize_sig(sheet)
  members_list[[i]] <- unique(data.frame(
    signature_id = paste0("FIBROBLAST.Patrick24.", signature_name),
    signature_name = signature_name,
    gene = dat$Gene,
    stringsAsFactors = FALSE
  ))
}

members <- do.call(rbind, members_list)

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Patrick24 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
