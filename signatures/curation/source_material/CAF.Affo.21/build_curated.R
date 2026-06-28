args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.Affo21")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

normalize_label <- function(x) {
  key <- tolower(trimws(x))
  if (key == "icaf") {
    return("iCAF")
  }
  if (key == "mycaf") {
    return("myCAF")
  }
  if (key == "mescaf") {
    return("mesCAF")
  }
  x
}

split_genes <- function(text) {
  tokens <- trimws(unlist(strsplit(as.character(text), "[,[:space:]]+")))
  tokens <- tokens[nzchar(tokens)]
  unique(tokens)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Affo.etal",
    "species: human",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: unknown",
    "tags: CAF;fibroblast",
    "source_author: Affo.etal",
    "source_pmid: ''",
    "source_doi: ''"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "humanCafGeneset.txt")
lines <- readLines(raw_path, warn = FALSE)
lines <- trimws(lines)

signature_blocks <- list()
current_name <- NULL
current_genes <- character()
for (line in lines) {
  if (!nzchar(line)) {
    if (!is.null(current_name)) {
      signature_blocks[[length(signature_blocks) + 1]] <- list(name = current_name, genes = current_genes)
      current_name <- NULL
      current_genes <- character()
    }
    next
  }
  if (is.null(current_name)) {
    current_name <- normalize_label(line)
  } else {
    current_genes <- c(current_genes, split_genes(line))
  }
}
if (!is.null(current_name)) {
  signature_blocks[[length(signature_blocks) + 1]] <- list(name = current_name, genes = current_genes)
}

members_list <- lapply(signature_blocks, function(block) {
  genes <- unique(block$genes)
  if (!length(genes)) {
    stop("Empty gene list in humanCafGeneset.txt block: ", block$name)
  }
  signature_name <- normalize_sig(block$name)
  data.frame(
    signature_id = paste0("CAF.Affo21.", signature_name),
    signature_name = signature_name,
    gene = genes,
    stringsAsFactors = FALSE
  )
})
members <- unique(do.call(rbind, members_list))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Affo21 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
