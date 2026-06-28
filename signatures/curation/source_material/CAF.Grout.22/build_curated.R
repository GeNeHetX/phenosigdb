args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.Grout22")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

split_genes <- function(text) {
  tokens <- trimws(unlist(strsplit(as.character(text), "[,[:space:]]+")))
  tokens <- tokens[nzchar(tokens)]
  unique(tokens)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Grout.etal",
    "species: human",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: unknown",
    "tags: CAF;fibroblast",
    "source_author: Grout.etal",
    "source_pmid: ''",
    "source_doi: ''"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "caflvl1.txt")
lines <- readLines(raw_path, warn = FALSE)
lines <- trimws(lines)
lines <- lines[nzchar(lines)]

members_list <- lapply(seq_along(lines), function(i) {
  parts <- strsplit(lines[[i]], "\t", fixed = TRUE)[[1]]
  if (length(parts) != 2) {
    stop("Expected two tab-separated fields in caflvl1.txt line ", i)
  }
  signature_name <- normalize_sig(parts[[1]])
  genes <- split_genes(parts[[2]])
  if (!length(genes)) {
    stop("Empty gene list in caflvl1.txt row ", i)
  }
  data.frame(
    signature_id = paste0("CAF.Grout22.", signature_name),
    signature_name = signature_name,
    gene = genes,
    stringsAsFactors = FALSE
  )
})
members <- unique(do.call(rbind, members_list))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Grout22 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
