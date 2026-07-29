# PhenoSigDB Parser for FIBROBLAST.Elhossiny26
# Parses: cd-25-2001_supp_table_11_suppst11 (1).xlsx
# From: Elhossiny et al. (supplementary data)

library(readxl)

# Get script directory (works from any location)
args <- commandArgs(trailingOnly = FALSE)
script_path <- normalizePath(sub("--file=", "", args[grep("--file=", args)]))
source_dir <- dirname(script_path)
repo_dir <- normalizePath(file.path(source_dir, "..", "..", ".."))
out_dir <- file.path(repo_dir, "curation", "curated", "FIBROBLAST.Elhossiny26")

# Load shared utilities
source(file.path(repo_dir, "curation", "tools", "phenosigdb_maintainer", "parser_utils.R"))

# === EDIT BELOW THIS LINE ===

# Read Excel file (skip row 1 which has the title)
raw_path <- file.path(source_dir, "cd-25-2001_supp_table_11_suppst11 (1).xlsx")
dat <- read_excel(raw_path, sheet = 1, skip = 1)

# Define metadata
source_author <- "Elhossiny.etal"
source_doi <- "10.1016/j.celrep.2025.114110"  # Example DOI, update if known
source_pmid <- ""  # Add if available
species <- "human"
cell_family <- "fibroblast"
context <- "cancer"
disease <- "unknown"  # Update if specific disease
tags <- c("CAF", "fibroblast", "single-cell")

# Clean cluster names: change from "Gene+_Fibro" to "Gene_fibro"
clean_cluster <- function(cluster_name) {
  # Replace + with _
  clean <- gsub("+", "_", cluster_name, fixed = TRUE)
  # Remove any double underscores that result from +_ -> __
  clean <- gsub("__+", "_", clean)
  # Keep gene symbol uppercase, convert _fibro to _fibro (lowercase)
  # Split on underscore, uppercase first part, lowercase rest
  parts <- strsplit(clean, "_")[[1]]
  parts <- sapply(parts, function(x) {
    if (x == "Fibro" || x == "fibro") {
      "fibro"
    } else {
      toupper(x)
    }
  })
  clean <- paste(parts, collapse = "_")
  # Trim whitespace
  trimws(clean)
}

# Apply cleaning to all cluster values
clusters <- unique(na.omit(dat$cluster))

# Filter to positive logFC genes only
positive_dat <- as.data.frame(dat[dat$avg_log2FC > 0, ])

# Group by cluster and extract top 100 genes by p_val_adj
all_members <- list()
for (cluster in clusters) {
  clean_name <- clean_cluster(cluster)
  
  # Get rows for this cluster with positive logFC
  cluster_dat <- positive_dat[positive_dat$cluster == cluster, ]
  
  if (nrow(cluster_dat) == 0) {
    warning(paste("No positive logFC genes for cluster:", cluster))
    next
  }
  
  # Sort by p_val_adj (ascending = most significant first)
  cluster_dat <- cluster_dat[order(cluster_dat$p_val_adj), ]
  
  # Take top 100 genes (or all if less than 100)
  top_genes <- head(cluster_dat$gene, 100)
  
  # Get unique gene symbols
  genes <- unique(na.omit(top_genes))
  
  if (length(genes) == 0) {
    warning(paste("No valid genes for cluster:", cluster))
    next
  }
  
  # Create signature with underscore naming (user requested gene_fibro pattern)
  signature_name <- clean_name
  signature_id <- paste0("FIBROBLAST.Elhossiny26.", signature_name)
  
  # Create data.frame for this signature
  members <- data.frame(
    signature_id = rep(signature_id, length(genes)),
    signature_name = rep(signature_name, length(genes)),
    gene = genes,
    stringsAsFactors = FALSE
  )
  
  all_members[[length(all_members) + 1]] <- members
}

# Combine all signatures
if (length(all_members) == 0) {
  stop("No signatures were created. Check your filters and data.")
}
all_members <- do.call(rbind, all_members)

# === DO NOT EDIT BELOW THIS LINE ===
if (!exists("all_members")) stop("Error: 'all_members' data.frame not defined. Edit parser logic above.")
if (!exists("source_author")) stop("Error: 'source_author' not defined.")
if (!exists("source_doi")) stop("Error: 'source_doi' not defined.")
if (!exists("species")) stop("Error: 'species' not defined.")
if (!exists("cell_family")) stop("Error: 'cell_family' not defined.")
if (!exists("context")) stop("Error: 'context' not defined.")
if (!exists("disease")) stop("Error: 'disease' not defined.")

dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
write_source_yaml(
  path = file.path(out_dir, "source.yaml"),
  source = "Elhossiny26",
  source_author = source_author,
  source_pmid = if (exists("source_pmid")) source_pmid else "",
  source_doi = source_doi,
  species = species,
  cell_family = cell_family,
  context = context,
  disease = disease,
  tags = if (exists("tags")) tags else NULL
)
write.table(all_members, file.path(out_dir, "members.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
message("Wrote ", out_dir)
