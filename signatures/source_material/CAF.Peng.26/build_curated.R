args <- commandArgs(trailingOnly = FALSE)
file_arg <- args[grep("^--file=", args)]
if (!length(file_arg)) {
  stop("Run this script with Rscript so its source directory can be found.")
}

script_path <- normalizePath(sub("^--file=", "", file_arg[[1]]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "signatures", "curated", "CAF.Peng26")
raw_path <- file.path(source_dir, "rawsigprorestcaf_peng.txt")

normalize_gene <- function(x) {
  x <- trimws(as.character(x))
  x <- gsub("[^A-Za-z0-9._-]", "", x)
  toupper(x)
}

normalize_signature <- function(x) {
  x <- trimws(x)
  if (!grepl("^[A-Za-z][A-Za-z0-9_-]*$", x)) {
    stop("Invalid signature name: ", x)
  }
  x
}

lines <- trimws(readLines(raw_path, warn = FALSE, encoding = "UTF-8"))
lines <- lines[nzchar(lines)]
signature_lines <- lines[grepl("^(proCAF|restCAF)\\s*:", lines, ignore.case = FALSE)]
if (length(signature_lines) != 2L) {
  stop("Expected exactly two signature definitions in ", raw_path)
}

parsed <- lapply(signature_lines, function(line) {
  match <- regexec("^([^:]+):\\s*(.+)$", line)
  parts <- regmatches(line, match)[[1]]
  if (length(parts) != 3L) {
    stop("Could not parse signature line: ", line)
  }

  signature_name <- normalize_signature(parts[[2]])
  genes <- normalize_gene(unlist(strsplit(parts[[3]], "[[:space:],;]+")))
  genes <- unique(genes[nzchar(genes)])
  if (!length(genes)) {
    stop("Empty gene list for ", signature_name)
  }

  data.frame(
    signature_id = paste0("CAF.Peng26.", signature_name),
    signature_name = signature_name,
    gene = genes,
    stringsAsFactors = FALSE
  )
})

members <- do.call(rbind, parsed)
if (!identical(sort(unique(members$signature_name)), sort(c("proCAF", "restCAF")))) {
  stop("Expected signatures proCAF and restCAF")
}
if (anyDuplicated(members[c("signature_id", "gene")])) {
  stop("Duplicate signature/gene rows found")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
writeLines(c(
  "source: Peng.etal;PMID:41707654;DOI:10.1016/j.xcrm.2026.102611",
  "species: human",
  "cell_family: fibroblast",
  "context: cancer",
  "disease: PDAC",
  "tags: CAF",
  "source_author: Peng.etal",
  "source_pmid: '41707654'",
  "source_doi: 10.1016/j.xcrm.2026.102611"
), file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir, " (", length(unique(members$signature_id)), " signatures, ", nrow(members), " genes)")
