args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.ReviewLiu26")

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

infer_species <- function(genes) {
  upper <- sum(grepl("^[A-Z0-9.-]+$", genes))
  mixed <- sum(grepl("^[A-Z][a-z0-9.-]+$", genes))
  if (mixed > upper) "mouse" else "human"
}

infer_cell_family <- function(signature_raw) {
  text <- tolower(signature_raw)
  if (grepl("smoothmuscle", text)) {
    return("smooth_muscle")
  }
  if (grepl("pericyte|pvl", text)) {
    return("pericyte")
  }
  "fibroblast"
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Liu.etal",
    "species: mixed",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: unknown",
    "tags: CAF;review",
    "source_author: Liu.etal",
    "source_pmid: ''",
    "source_doi: ''"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "manuallist.txt")
lines <- readLines(raw_path, warn = FALSE)
lines <- trimws(lines)
lines <- lines[nzchar(lines)]

members_list <- lapply(lines, function(line) {
  parts <- regmatches(line, regexec("^(\\S+)\\s+(.+)$", line))[[1]]
  if (length(parts) != 3) {
    stop("Could not parse line in manuallist.txt: ", line)
  }
  signature_raw <- parts[2]
  genes <- split_genes(parts[3])
  if (!length(genes)) {
    stop("Empty gene list in manuallist.txt line: ", line)
  }
  signature_name <- normalize_sig(signature_raw)
  species <- infer_species(genes)
  cell_family <- infer_cell_family(signature_raw)
  data.frame(
    signature_id = paste0("CAF.ReviewLiu26.", signature_name),
    signature_name = signature_name,
    gene = genes,
    species = species,
    cell_family = cell_family,
    stringsAsFactors = FALSE
  )
})

members <- unique(do.call(rbind, members_list))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in ReviewLiu26 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
