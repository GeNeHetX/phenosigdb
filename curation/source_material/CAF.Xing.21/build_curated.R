library(readxl)

args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("^--file=", "", args[grep("^--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "CAF.Xing21")

normalize_sig <- function(x) {
  x <- trimws(x)
  x <- gsub("[[:space:]_/-]+", ".", x)
  x <- gsub("\\.+", ".", x)
  gsub("^\\.|\\.$", "", x)
}

split_genes <- function(text) {
  tokens <- trimws(unlist(strsplit(as.character(text), ",")))
  tokens <- tokens[nzchar(tokens)]
  unique(tokens)
}

write_source_yaml <- function(path) {
  lines <- c(
    "source: Xing.etal;DOI:10.1126/sciadv.abd9738",
    "species: human",
    "cell_family: fibroblast",
    "context: cancer",
    "disease: unknown",
    "tags: CAF;fibroblast",
    "source_author: Xing.etal",
    "source_pmid: ''",
    "source_doi: 10.1126/sciadv.abd9738"
  )
  writeLines(lines, path)
}

raw_path <- file.path(source_dir, "summarytableMArker.xlsx")
dat <- read_excel(raw_path)
keep <- grepl("^Fibro-", dat[["Cluster Name"]]) & !grepl("Pericyte", dat[["Annotated Name"]], ignore.case = TRUE)
dat <- dat[keep, c("Cluster Name", "Annotated Name", "Selected Marker Genes")]

if (nrow(dat) == 0) {
  stop("No fibroblast rows found in Xing21 summary table")
}

members_list <- lapply(seq_len(nrow(dat)), function(i) {
  genes <- split_genes(dat[["Selected Marker Genes"]][[i]])
  if (!length(genes)) {
    stop("Empty gene list in Xing21 row ", i)
  }
  signature_name <- normalize_sig(dat[["Annotated Name"]][[i]])
  data.frame(
    signature_id = paste0("CAF.Xing21.", signature_name),
    signature_name = signature_name,
    gene = genes,
    stringsAsFactors = FALSE
  )
})
members <- unique(do.call(rbind, members_list))

if (any(duplicated(members[c("signature_name", "gene")]))) {
  stop("Duplicate gene rows found in Xing21 members.tsv")
}

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(file.path(out_dir, "source.yaml"))
write.table(members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
