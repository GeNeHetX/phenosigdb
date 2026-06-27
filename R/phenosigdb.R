.phenosigdb_release_ref <- "v0.1.0"

.phenosigdb_parquet_name <- function(reference_species = c("original", "human", "mouse")) {
  reference_species <- match.arg(reference_species)
  switch(
    reference_species,
    original = "phenosigdb.parquet",
    human = "phenosigdb_human.parquet",
    mouse = "phenosigdb_mouse.parquet"
  )
}

.phenosigdb_default_path <- function(reference_species = c("original", "human", "mouse")) {
  parquet_name <- .phenosigdb_parquet_name(reference_species)
  local_path <- file.path("data", parquet_name)
  if (file.exists(local_path)) {
    return(local_path)
  }
  paste0("https://raw.githubusercontent.com/GeNeHetX/phenosigdb/", .phenosigdb_release_ref, "/data/", parquet_name)
}

.phenosigdb_read <- function(path = NULL, reference_species = c("original", "human", "mouse")) {
  if (!requireNamespace("arrow", quietly = TRUE)) {
    stop("Package 'arrow' is required. Install it with install.packages('arrow').", call. = FALSE)
  }

  target <- if (is.null(path)) .phenosigdb_default_path(reference_species) else path
  if (grepl("^https?://", target)) {
    tmp <- tempfile(fileext = ".parquet")
    on.exit(unlink(tmp), add = TRUE)
    utils::download.file(target, tmp, mode = "wb", quiet = TRUE)
    target <- tmp
  }
  arrow::read_parquet(target, as_data_frame = TRUE)
}

.phenosigdb_search_mask <- function(table, query, columns) {
  mask <- rep(FALSE, nrow(table))
  if (is.null(query) || !nrow(table)) {
    return(mask)
  }
  query <- as.character(query)[1]
  for (column in columns) {
    if (!column %in% names(table)) {
      next
    }
    values <- table[[column]]
    values[is.na(values)] <- ""
    mask <- mask | grepl(query, values, ignore.case = TRUE, fixed = TRUE)
  }
  mask
}

list_signatures <- function(path = NULL, reference_species = c("original", "human", "mouse"), query = NULL) {
  reference_species <- match.arg(reference_species)
  db <- .phenosigdb_read(path = path, reference_species = reference_species)
  db <- db[order(db$signature_id, db$gene), , drop = FALSE]

  meta_columns <- c(
    "signature_id",
    "signature_name",
    "source",
    "source_author",
    "source_pmid",
    "source_doi",
    "species",
    "species_original",
    "cell_family",
    "context",
    "disease",
    "tags"
  )
  meta_columns <- meta_columns[meta_columns %in% names(db)]
  meta <- db[!duplicated(db$signature_id), meta_columns, drop = FALSE]
  meta$domain <- sub("\\..*$", "", meta$signature_id)
  meta$n_genes <- as.integer(table(db$signature_id)[meta$signature_id])

  ordered_columns <- c(
    "signature_id",
    "signature_name",
    "domain",
    "source",
    "source_author",
    "source_pmid",
    "source_doi",
    "species",
    "species_original",
    "cell_family",
    "context",
    "disease",
    "tags",
    "n_genes"
  )
  ordered_columns <- ordered_columns[ordered_columns %in% names(meta)]
  meta <- meta[, ordered_columns, drop = FALSE]

  if (!is.null(query)) {
    search_columns <- setdiff(names(meta), "n_genes")
    meta <- meta[.phenosigdb_search_mask(meta, query = query, columns = search_columns), , drop = FALSE]
  }

  rownames(meta) <- NULL
  meta
}

get_signatures <- function(
  signature_ids = NULL,
  path = NULL,
  reference_species = c("original", "human", "mouse"),
  format = c("dict", "table")
) {
  reference_species <- match.arg(reference_species)
  format <- match.arg(format)
  db <- .phenosigdb_read(path = path, reference_species = reference_species)

  if (is.null(signature_ids)) {
    db <- db[order(db$signature_id, db$gene), , drop = FALSE]
    ordered_ids <- unique(db$signature_id)
  } else {
    ordered_ids <- unique(as.character(signature_ids))
    ordered_ids <- ordered_ids[!is.na(ordered_ids) & nzchar(trimws(ordered_ids))]
    db <- db[db$signature_id %in% ordered_ids, , drop = FALSE]
    if (nrow(db)) {
      db$signature_id <- factor(db$signature_id, levels = ordered_ids)
      db <- db[order(db$signature_id, db$gene), , drop = FALSE]
      db$signature_id <- as.character(db$signature_id)
    }
  }

  rownames(db) <- NULL
  if (format == "table") {
    return(db)
  }

  signatures <- split(db$gene, db$signature_id)
  signatures <- lapply(signatures, unique)
  if (is.null(signature_ids)) {
    return(signatures)
  }
  signatures[ordered_ids[ordered_ids %in% names(signatures)]]
}
