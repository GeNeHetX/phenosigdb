.phenosigdb_package_version <- "0.1.3"
.phenosigdb_public_metadata_columns <- c(
  "signature_id",
  "signature_name",
  "domain",
  "source",
  "collection",
  "source_resource",
  "signature_format",
  "species",
  "cell_family",
  "context",
  "disease",
  "n_genes"
)

.phenosigdb_resource_metadata_columns <- c(
  .phenosigdb_public_metadata_columns,
  "resource_key",
  "species_original",
  "source_version",
  "source_label",
  "source_pmid",
  "source_doi",
  "source_url",
  "original_source",
  "original_signature_name",
  "cell_ontology_id",
  "annotation_level",
  "resource_metadata_json"
)

.phenosigdb_msigdb_notice <- paste(
  "This downloads MSigDB C7/C8/PID/BioCarta gene sets from the Broad MSigDB release server.",
  "By continuing, you are responsible for complying with MSigDB license terms.",
  "phenosigdb stores the files locally for your own use and does not redistribute them.",
  sep = "\n"
)

.phenosigdb_known_resources <- function() {
  data.frame(
    resource = c(
      "celltypist",
      "cellmarker",
      "msigdb_c7immune",
      "msigdb_c8celltype",
      "pid",
      "biocarta",
      "reactome",
      "wikipathways"
    ),
    prefix = c(
      "CELLTYPIST.",
      "CELLMARKER.",
      "MSIGDB.C7.",
      "MSIGDB.C8.",
      "PID.",
      "BIOCARTA.",
      "REACTOME.PATHWAYS.",
      "WIKIPATHWAYS."
    ),
    signature_format = c("continuous", "binary", "binary", "binary", "binary", "binary", "binary", "binary"),
    install_kind = c("archive", "archive", "gmt", "gmt", "gmt", "gmt", "zip_gmt", "wikipathways_current_gmt"),
    archive_name = c(
      "phenosigdb-resource-celltypist.tar.gz",
      "phenosigdb-resource-cellmarker.tar.gz",
      NA, NA, NA, NA, NA, NA
    ),
    download_url = c(
      NA,
      NA,
      "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c7.all.v2025.1.Hs.symbols.gmt",
      "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c8.all.v2025.1.Hs.symbols.gmt",
      "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c2.cp.pid.v2025.1.Hs.symbols.gmt",
      "https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/c2.cp.biocarta.v2025.1.Hs.symbols.gmt",
      "https://reactome.org/download/current/ReactomePathways.gmt.zip",
      "https://data.wikipathways.org/current/gmt/"
    ),
    version = c(NA, NA, "2025.1.Hs", "2025.1.Hs", "2025.1.Hs", "2025.1.Hs", "current", "current"),
    public_domain = c(NA, NA, "MSIGDB", "MSIGDB", "PID", "BIOCARTA", "REACTOME", "WIKIPATHWAYS"),
    public_source = c(NA, NA, "C7", "C8", "PID", "BIOCARTA", "Pathways", "WikiPathways"),
    public_collection = c(NA, NA, "C7", "C8", "PID", "BIOCARTA", "ReactomePathways", "WikiPathways"),
    public_source_resource = c(NA, NA, "msigdb", "msigdb", "pid", "biocarta", "reactome", "wikipathways"),
    public_context = c(NA, NA, "immunology", "cell_type", "pathway", "pathway", "pathway", "pathway"),
    public_tags = c(NA, NA, "C7", "C8", "PID", "BIOCARTA", "Reactome", "WikiPathways"),
    public_species = c(NA, NA, "human", "human", "human", "human", "human", "human"),
    public_cell_family = c(NA, NA, "immune", "unknown", "unknown", "unknown", "unknown", "unknown"),
    license_notice = c(NA, NA, .phenosigdb_msigdb_notice, .phenosigdb_msigdb_notice, .phenosigdb_msigdb_notice, .phenosigdb_msigdb_notice, NA, NA),
    stringsAsFactors = FALSE
  )
}

.phenosigdb_parquet_name <- function(reference_species = "human") {
  reference_species <- match.arg(reference_species, c("human", "mouse", "original"))
  switch(
    reference_species,
    original = "phenosigdb.parquet",
    human = "phenosigdb_human.parquet",
    mouse = "phenosigdb_mouse.parquet"
  )
}

.phenosigdb_repo_core_path <- function(reference_species = "human") {
  parquet_name <- .phenosigdb_parquet_name(reference_species)
  candidates <- c(
    file.path("signatures", "data", parquet_name),
    file.path("..", "signatures", "data", parquet_name)
  )
  for (candidate in candidates) {
    if (file.exists(candidate)) {
      return(normalizePath(candidate, winslash = "/", mustWork = TRUE))
    }
  }
  NULL
}

.phenosigdb_core_dir <- function() {
  file.path(.phenosigdb_cache_dir_create(), "curated")
}

.phenosigdb_core_cache_path <- function(reference_species = "human") {
  file.path(.phenosigdb_core_dir(), .phenosigdb_parquet_name(reference_species))
}

.phenosigdb_core_url <- function(reference_species = "human") {
  parquet_name <- .phenosigdb_parquet_name(reference_species)
  explicit <- Sys.getenv(paste0("PHENOSIGDB_DATA_URL_", toupper(reference_species)), unset = "")
  if (nzchar(explicit)) {
    return(explicit)
  }
  base <- Sys.getenv("PHENOSIGDB_DATA_BASE_URL", unset = "")
  if (nzchar(base)) {
    return(paste0(sub("/+$", "", base), "/", parquet_name))
  }
  ref <- Sys.getenv("PHENOSIGDB_DATA_REF", unset = "main")
  paste0("https://raw.githubusercontent.com/GeNeHetX/phenosigdb/", ref, "/signatures/data/", parquet_name)
}

.phenosigdb_ensure_core_path <- function(reference_species = "human") {
  repo_path <- .phenosigdb_repo_core_path(reference_species)
  if (!is.null(repo_path)) {
    return(repo_path)
  }
  cache_path <- .phenosigdb_core_cache_path(reference_species)
  if (file.exists(cache_path)) {
    return(cache_path)
  }
  dir.create(dirname(cache_path), recursive = TRUE, showWarnings = FALSE)
  utils::download.file(.phenosigdb_core_url(reference_species), cache_path, mode = "wb", quiet = TRUE)
  normalizePath(cache_path, winslash = "/", mustWork = TRUE)
}

.phenosigdb_default_path <- function(reference_species = "human") {
  .phenosigdb_ensure_core_path(reference_species)
}

.phenosigdb_require_arrow <- function() {
  if (!requireNamespace("arrow", quietly = TRUE)) {
    stop("Package 'arrow' is required. Install it with install.packages('arrow').", call. = FALSE)
  }
}

.phenosigdb_require_jsonlite <- function() {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("Package 'jsonlite' is required for phenosigdb_resources(). Install it with install.packages('jsonlite').", call. = FALSE)
  }
}

.phenosigdb_read <- function(path = NULL, reference_species = "human") {
  .phenosigdb_require_arrow()
  target <- if (is.null(path)) .phenosigdb_default_path(reference_species) else path
  arrow::read_parquet(target, as_data_frame = TRUE)
}

.phenosigdb_cache_dir <- function() {
  override <- Sys.getenv("PHENOSIGDB_CACHE_DIR", unset = "")
  if (nzchar(override)) {
    return(normalizePath(path.expand(override), winslash = "/", mustWork = FALSE))
  }
  if ("R_user_dir" %in% getNamespaceExports("tools")) {
    return(normalizePath(tools::R_user_dir("phenosigdb", which = "cache"), winslash = "/", mustWork = FALSE))
  }
  if (requireNamespace("rappdirs", quietly = TRUE)) {
    return(normalizePath(rappdirs::user_cache_dir("phenosigdb"), winslash = "/", mustWork = FALSE))
  }
  normalizePath(path.expand(file.path("~", ".cache", "phenosigdb")), winslash = "/", mustWork = FALSE)
}

.phenosigdb_cache_dir_create <- function() {
  dir.create(.phenosigdb_cache_dir(), recursive = TRUE, showWarnings = FALSE)
  .phenosigdb_cache_dir()
}

.phenosigdb_resources_manifest_path <- function() {
  file.path(.phenosigdb_cache_dir(), "resources.json")
}

.phenosigdb_resource_dir <- function(resource) {
  file.path(.phenosigdb_cache_dir(), tolower(resource))
}

.phenosigdb_resource_manifest_path <- function(resource) {
  file.path(.phenosigdb_resource_dir(resource), "resource.json")
}

.phenosigdb_resource_files <- function(resource) {
  switch(
    tolower(resource),
    celltypist = c("metadata.parquet", "continuous.parquet", "resource.json"),
    cellmarker = c("metadata.parquet", "binary.parquet", "resource.json"),
    msigdb_c7immune = c("metadata.parquet", "binary.parquet", "resource.json"),
    msigdb_c8celltype = c("metadata.parquet", "binary.parquet", "resource.json"),
    pid = c("metadata.parquet", "binary.parquet", "resource.json"),
    biocarta = c("metadata.parquet", "binary.parquet", "resource.json"),
    reactome = c("metadata.parquet", "binary.parquet", "resource.json"),
    wikipathways = c("metadata.parquet", "binary.parquet", "resource.json"),
    {
      available <- paste(.phenosigdb_known_resources()$resource, collapse = ", ")
      stop("Unknown resource: ", resource, ". Available resources: ", available, call. = FALSE)
    }
  )
}

.phenosigdb_json_read <- function(path) {
  if (!file.exists(path)) {
    return(NULL)
  }
  .phenosigdb_require_jsonlite()
  jsonlite::fromJSON(path, simplifyVector = FALSE)
}

.phenosigdb_json_write <- function(path, value) {
  .phenosigdb_require_jsonlite()
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  writeLines(jsonlite::toJSON(value, auto_unbox = TRUE, pretty = TRUE, null = "null"), con = path, useBytes = TRUE)
}

.phenosigdb_resource_url <- function(resource) {
  key <- toupper(resource)
  explicit <- Sys.getenv(paste0("PHENOSIGDB_RESOURCE_URL_", key), unset = "")
  if (nzchar(explicit)) {
    return(explicit)
  }
  info <- .phenosigdb_known_resources()[match(tolower(resource), .phenosigdb_known_resources()$resource), , drop = FALSE]
  if (!nrow(info)) {
    available <- paste(.phenosigdb_known_resources()$resource, collapse = ", ")
    stop("Unknown resource: ", resource, ". Available resources: ", available, call. = FALSE)
  }
  if (identical(info$install_kind[[1]], "archive")) {
    base <- Sys.getenv("PHENOSIGDB_RESOURCES_BASE_URL", unset = "")
    if (nzchar(base)) {
      return(paste0(sub("/+$", "", base), "/", info$archive_name[[1]]))
    }
    release_ref <- Sys.getenv("PHENOSIGDB_RESOURCES_RELEASE", unset = paste0("v", .phenosigdb_package_version))
    return(paste0("https://github.com/GeNeHetX/phenosigdb/releases/download/", release_ref, "/", info$archive_name[[1]]))
  }
  info$download_url[[1]]
}

.phenosigdb_download_file <- function(source, destination) {
  if (grepl("^file://", source)) {
    local_path <- sub("^file://", "", source)
    ok <- file.copy(local_path, destination, overwrite = TRUE)
    if (!ok) {
      stop("Failed to copy local resource archive: ", local_path, call. = FALSE)
    }
    return(destination)
  }
  if (!grepl("^https?://", source)) {
    ok <- file.copy(path.expand(source), destination, overwrite = TRUE)
    if (!ok) {
      stop("Failed to copy local resource archive: ", source, call. = FALSE)
    }
    return(destination)
  }
  utils::download.file(source, destination, mode = "wb", quiet = TRUE)
  destination
}

.phenosigdb_resource_status_row <- function(resource) {
  dir_path <- .phenosigdb_resource_dir(resource)
  manifest_path <- .phenosigdb_resource_manifest_path(resource)
  manifest <- NULL
  if (file.exists(manifest_path) && requireNamespace("jsonlite", quietly = TRUE)) {
    manifest <- jsonlite::fromJSON(manifest_path)
  }
  manifest_value <- function(name, default = NA) {
    if (is.null(manifest)) {
      return(default)
    }
    value <- manifest[[name]]
    if (is.null(value) || !length(value)) {
      return(default)
    }
    value[[1]]
  }
  expected_files <- .phenosigdb_resource_files(resource)
  installed <- all(file.exists(file.path(dir_path, expected_files)))
  data.frame(
    resource = tolower(resource),
    installed = installed,
    version = manifest_value("version", .phenosigdb_known_resources()$version[match(tolower(resource), .phenosigdb_known_resources()$resource)]),
    installed_at = manifest_value("installed_at", NA_character_),
    signature_format = manifest_value("signature_format", .phenosigdb_known_resources()$signature_format[match(tolower(resource), .phenosigdb_known_resources()$resource)]),
    n_signatures = manifest_value("n_signatures", NA_real_),
    n_rows = manifest_value("n_rows", NA_real_),
    checksum = manifest_value("checksum", NA_character_),
    package_version = manifest_value("package_version", NA_character_),
    cache_path = normalizePath(dir_path, winslash = "/", mustWork = FALSE),
    stringsAsFactors = FALSE
  )
}

.phenosigdb_write_resources_manifest <- function() {
  rows <- do.call(rbind, lapply(.phenosigdb_known_resources()$resource, .phenosigdb_resource_status_row))
  if (requireNamespace("jsonlite", quietly = TRUE)) {
    .phenosigdb_json_write(
      .phenosigdb_resources_manifest_path(),
      list(
        generated_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE),
        resources = unname(split(rows, seq_len(nrow(rows))))
      )
    )
  }
  rows
}

.phenosigdb_extract_resource_root <- function(tmp_dir, resource) {
  candidate <- file.path(tmp_dir, tolower(resource))
  if (dir.exists(candidate)) {
    return(candidate)
  }
  tmp_dir
}

.phenosigdb_resource_info <- function(resource) {
  info <- .phenosigdb_known_resources()[match(tolower(resource), .phenosigdb_known_resources()$resource), , drop = FALSE]
  if (!nrow(info)) {
    available <- paste(.phenosigdb_known_resources()$resource, collapse = ", ")
    stop("Unknown resource: ", resource, ". Available resources: ", available, call. = FALSE)
  }
  info
}

.phenosigdb_print_license_notices <- function(resources, verbose = TRUE) {
  if (!verbose || !length(resources)) {
    return(invisible(NULL))
  }
  notices <- unique(stats::na.omit(.phenosigdb_known_resources()$license_notice[match(resources, .phenosigdb_known_resources()$resource)]))
  for (notice in notices) {
    message(notice)
  }
  invisible(NULL)
}

.phenosigdb_normalize_human_gene <- function(value) {
  if (is.null(value) || length(value) == 0L || is.na(value)) {
    return(NA_character_)
  }
  text <- trimws(enc2utf8(as.character(value)))
  if (!nzchar(text)) {
    return(NA_character_)
  }
  text <- iconv(text, to = "ASCII//TRANSLIT", sub = "")
  text <- gsub("\\s+", "", text)
  text <- toupper(text)
  if (!nzchar(text)) {
    return(NA_character_)
  }
  text
}

.phenosigdb_deduplicate <- function(values) {
  values[!duplicated(values)]
}

.phenosigdb_signature_id <- function(domain, source_key, signature_name) {
  normalize_token <- function(x, upper = FALSE) {
    text <- trimws(enc2utf8(as.character(x)))
    text <- iconv(text, to = "ASCII//TRANSLIT", sub = "")
    text <- gsub("[^A-Za-z0-9]+", "_", text)
    text <- gsub("^_+|_+$", "", text)
    if (!nzchar(text)) {
      text <- "unknown"
    }
    if (upper) {
      text <- toupper(text)
    }
    text
  }
  paste(normalize_token(domain, upper = TRUE), normalize_token(source_key), normalize_token(signature_name), sep = ".")
}

.phenosigdb_resolve_wikipathways_source <- function(source) {
  if (!grepl("^https?://", source) || grepl("\\.gmt$", source, ignore.case = TRUE)) {
    return(list(url = source, version = NA_character_))
  }
  html <- paste(readLines(source, warn = FALSE), collapse = "\n")
  matches <- gregexpr("wikipathways-([0-9]+)-gmt-Homo_sapiens\\.gmt", html, perl = TRUE)
  found <- regmatches(html, matches)[[1]]
  if (!length(found)) {
    stop("Could not resolve a Homo sapiens WikiPathways GMT file from the current directory listing", call. = FALSE)
  }
  versions <- sub("^wikipathways-([0-9]+)-gmt-Homo_sapiens\\.gmt$", "\\1", found, perl = TRUE)
  idx <- order(versions)[length(versions)]
  list(url = paste0(sub("/+$", "", source), "/", found[[idx]]), version = versions[[idx]])
}

.phenosigdb_read_gmt_entries <- function(path, kind = "gmt") {
  if (identical(kind, "zip_gmt")) {
    tmp_dir <- tempfile(pattern = "phenosigdb-gmt-")
    dir.create(tmp_dir, recursive = TRUE, showWarnings = FALSE)
    on.exit(unlink(tmp_dir, recursive = TRUE, force = TRUE), add = TRUE)
    utils::unzip(path, exdir = tmp_dir)
    files <- sort(list.files(tmp_dir, pattern = "\\.gmt$", recursive = TRUE, full.names = TRUE))
    if (!length(files)) {
      stop("No .gmt file found inside ", path, call. = FALSE)
    }
    lines <- readLines(files[[1]], warn = FALSE, encoding = "UTF-8")
  } else {
    lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  }
  entries <- vector("list", 0L)
  for (line in lines) {
    if (!nzchar(trimws(line))) {
      next
    }
    fields <- strsplit(line, "\t", fixed = TRUE)[[1]]
    if (length(fields) < 3L) {
      next
    }
    genes <- vapply(fields[-c(1, 2)], .phenosigdb_normalize_human_gene, character(1))
    genes <- genes[!is.na(genes) & nzchar(genes)]
    genes <- .phenosigdb_deduplicate(genes)
    if (!length(genes)) {
      next
    }
    entries[[length(entries) + 1L]] <- list(
      signature_name = fields[[1]],
      description = if (nzchar(trimws(fields[[2]]))) fields[[2]] else NA_character_,
      genes = genes
    )
  }
  entries
}

.phenosigdb_write_runtime_resource <- function(resource, metadata, values, resource_json, verbose = TRUE) {
  .phenosigdb_require_arrow()
  dest_dir <- .phenosigdb_resource_dir(resource)
  unlink(dest_dir, recursive = TRUE, force = TRUE)
  dir.create(dest_dir, recursive = TRUE, showWarnings = FALSE)
  arrow::write_parquet(metadata, file.path(dest_dir, "metadata.parquet"), compression = "zstd")
  if (identical(.phenosigdb_resource_info(resource)$signature_format[[1]], "continuous")) {
    arrow::write_parquet(values, file.path(dest_dir, "continuous.parquet"), compression = "zstd")
  } else {
    arrow::write_parquet(values, file.path(dest_dir, "binary.parquet"), compression = "zstd")
  }
  resource_json$resource <- resource
  if (is.null(resource_json$installed_at)) {
    resource_json$installed_at <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  }
  if (is.null(resource_json$signature_format)) {
    resource_json$signature_format <- .phenosigdb_resource_info(resource)$signature_format[[1]]
  }
  if (is.null(resource_json$package_version)) {
    resource_json$package_version <- .phenosigdb_package_version
  }
  .phenosigdb_json_write(file.path(dest_dir, "resource.json"), resource_json)
  rows <- .phenosigdb_write_resources_manifest()
  row <- rows[rows$resource == tolower(resource), , drop = FALSE]
  if (verbose) {
    message("Installed ", resource, " into ", row$cache_path[[1]])
  }
  row
}

.phenosigdb_install_direct_resource <- function(resource, verbose = TRUE) {
  .phenosigdb_require_jsonlite()
  info <- .phenosigdb_resource_info(resource)
  source <- .phenosigdb_resource_url(resource)
  resolved_source <- source
  resolved_version <- info$version[[1]]
  if (identical(info$install_kind[[1]], "wikipathways_current_gmt")) {
    resolved <- .phenosigdb_resolve_wikipathways_source(source)
    resolved_source <- resolved$url
    if (!is.na(resolved$version)) {
      resolved_version <- resolved$version
    }
  }
  suffix <- if (identical(info$install_kind[[1]], "zip_gmt")) ".zip" else ".gmt"
  raw_path <- tempfile(pattern = paste0("phenosigdb-", resource, "-"), fileext = suffix)
  on.exit(unlink(raw_path, recursive = TRUE, force = TRUE), add = TRUE)
  .phenosigdb_download_file(resolved_source, raw_path)
  entries <- .phenosigdb_read_gmt_entries(raw_path, kind = info$install_kind[[1]])
  metadata_rows <- list()
  binary_rows <- list()
  for (entry in entries) {
    signature_id <- .phenosigdb_signature_id(info$public_domain[[1]], info$public_source[[1]], entry$signature_name)
    metadata_rows[[length(metadata_rows) + 1L]] <- data.frame(
      signature_id = signature_id,
      signature_name = entry$signature_name,
      domain = info$public_domain[[1]],
      source = info$public_source[[1]],
      collection = info$public_collection[[1]],
      source_resource = info$public_source_resource[[1]],
      resource_key = resource,
      signature_format = "binary",
      species = info$public_species[[1]],
      species_original = info$public_species[[1]],
      cell_family = info$public_cell_family[[1]],
      context = info$public_context[[1]],
      disease = "unknown",
      n_genes = length(entry$genes),
      source_version = resolved_version,
      source_label = entry$description,
      source_pmid = NA_character_,
      source_doi = NA_character_,
      source_url = resolved_source,
      original_source = info$public_source[[1]],
      original_signature_name = entry$signature_name,
      cell_ontology_id = NA_character_,
      annotation_level = NA_character_,
      resource_metadata_json = jsonlite::toJSON(
        list(
          description = entry$description,
          tags = info$public_tags[[1]],
          resolved_source_url = resolved_source
        ),
        auto_unbox = TRUE,
        null = "null"
      ),
      stringsAsFactors = FALSE
    )
    binary_rows[[length(binary_rows) + 1L]] <- data.frame(
      signature_id = rep(signature_id, length(entry$genes)),
      gene = entry$genes,
      stringsAsFactors = FALSE
    )
  }
  metadata <- if (length(metadata_rows)) do.call(rbind, metadata_rows) else data.frame(setNames(replicate(length(.phenosigdb_resource_metadata_columns), logical(0), simplify = FALSE), .phenosigdb_resource_metadata_columns))
  binary <- if (length(binary_rows)) do.call(rbind, binary_rows) else data.frame(signature_id = character(), gene = character(), stringsAsFactors = FALSE)
  metadata <- metadata[, .phenosigdb_resource_metadata_columns, drop = FALSE]
  metadata <- metadata[order(metadata$signature_id), , drop = FALSE]
  binary <- binary[order(binary$signature_id, binary$gene), , drop = FALSE]
  rownames(metadata) <- NULL
  rownames(binary) <- NULL
  .phenosigdb_write_runtime_resource(
    resource,
    metadata = metadata,
    values = binary,
    resource_json = list(
      resource = resource,
      version = resolved_version,
      signature_format = "binary",
      n_signatures = nrow(metadata),
      n_rows = nrow(binary),
      package_version = .phenosigdb_package_version,
      source_resource = info$public_source_resource[[1]],
      source_url = resolved_source
    ),
    verbose = verbose
  )
}

.phenosigdb_install_resource <- function(resource, force = FALSE, verbose = TRUE, action = "install") {
  .phenosigdb_require_jsonlite()
  action <- match.arg(action, c("install", "update"))
  resource <- tolower(resource)
  info <- .phenosigdb_resource_info(resource)
  current <- .phenosigdb_resource_status_row(resource)
  if (identical(action, "install") && isTRUE(current$installed) && !force) {
    if (verbose) {
      message(resource, " is already installed")
    }
    return(current)
  }
  if (!identical(info$install_kind[[1]], "archive")) {
    if (identical(action, "update") && isTRUE(current$installed) && !force && !is.na(current$version) && identical(as.character(current$version), as.character(info$version[[1]]))) {
      if (verbose) {
        message(resource, " is already up to date")
      }
      return(current)
    }
    return(.phenosigdb_install_direct_resource(resource, verbose = verbose))
  }
  archive_path <- tempfile(fileext = ".tar.gz")
  tmp_dir <- tempfile(pattern = paste0("phenosigdb-", resource, "-"))
  dir.create(tmp_dir, recursive = TRUE, showWarnings = FALSE)
  on.exit(unlink(c(archive_path, tmp_dir), recursive = TRUE, force = TRUE), add = TRUE)

  .phenosigdb_download_file(.phenosigdb_resource_url(resource), archive_path)
  utils::untar(archive_path, exdir = tmp_dir)
  extracted <- .phenosigdb_extract_resource_root(tmp_dir, resource)
  missing <- .phenosigdb_resource_files(resource)[!file.exists(file.path(extracted, .phenosigdb_resource_files(resource)))]
  if (length(missing)) {
    stop("Resource archive for ", resource, " is missing required files: ", paste(missing, collapse = ", "), call. = FALSE)
  }

  resource_json <- .phenosigdb_json_read(file.path(extracted, "resource.json"))
  remote_version <- if (!is.null(resource_json)) resource_json$version else NA_character_
  if (identical(action, "update") && isTRUE(current$installed) && !force) {
    if (!is.na(current$version) && identical(as.character(current$version), as.character(remote_version))) {
      if (verbose) {
        message(resource, " is already up to date")
      }
      return(current)
    }
  }

  dest_dir <- .phenosigdb_resource_dir(resource)
  unlink(dest_dir, recursive = TRUE, force = TRUE)
  dir.create(dirname(dest_dir), recursive = TRUE, showWarnings = FALSE)
  ok <- file.copy(extracted, dirname(dest_dir), recursive = TRUE)
  if (!ok) {
    stop("Failed to install resource: ", resource, call. = FALSE)
  }

  if (is.null(resource_json)) {
    resource_json <- list()
  }
  if (is.null(resource_json$resource)) {
    resource_json$resource <- resource
  }
  if (is.null(resource_json$installed_at)) {
    resource_json$installed_at <- format(Sys.time(), tz = "UTC", usetz = TRUE)
  }
  if (is.null(resource_json$signature_format)) {
    resource_json$signature_format <- .phenosigdb_known_resources()$signature_format[match(resource, .phenosigdb_known_resources()$resource)]
  }
  if (is.null(resource_json$package_version)) {
    resource_json$package_version <- .phenosigdb_package_version
  }
  .phenosigdb_json_write(file.path(dest_dir, "resource.json"), resource_json)
  rows <- .phenosigdb_write_resources_manifest()
  row <- rows[rows$resource == resource, , drop = FALSE]
  if (verbose) {
    message("Installed ", resource, " into ", row$cache_path[[1]])
  }
  row
}

.phenosigdb_install_resources <- function(resources = NULL, force = FALSE, verbose = TRUE, action = "install") {
  action <- match.arg(action, c("install", "update"))
  known <- .phenosigdb_known_resources()$resource
  if (is.null(resources)) {
    resources <- known
  }
  resources <- unique(tolower(trimws(as.character(resources))))
  resources <- resources[nzchar(resources)]
  if (!length(resources)) {
    return(do.call(rbind, lapply(known, .phenosigdb_resource_status_row)))
  }
  unknown <- setdiff(resources, known)
  if (length(unknown)) {
    available <- paste(known, collapse = ", ")
    stop("Unknown resource: ", unknown[[1]], ". Available resources: ", available, call. = FALSE)
  }
  .phenosigdb_print_license_notices(resources, verbose = verbose)
  if (length(resources) == 1L) {
    return(.phenosigdb_install_resource(resources[[1]], force = force, verbose = verbose, action = action))
  }
  for (resource in resources) {
    .phenosigdb_install_resource(resource, force = force, verbose = verbose, action = action)
  }
  do.call(rbind, lapply(known, .phenosigdb_resource_status_row))
}

.phenosigdb_remove_resource <- function(resource, verbose = TRUE) {
  .phenosigdb_require_jsonlite()
  unlink(.phenosigdb_resource_dir(resource), recursive = TRUE, force = TRUE)
  rows <- .phenosigdb_write_resources_manifest()
  row <- rows[rows$resource == tolower(resource), , drop = FALSE]
  if (verbose) {
    message("Removed ", tolower(resource), " from cache")
  }
  row
}

.phenosigdb_search_mask <- function(table, query, columns, fixed = FALSE) {
  mask <- rep(FALSE, nrow(table))
  if (is.null(query) || !nrow(table)) {
    return(mask)
  }
  query <- as.character(query)[1]
  for (column in columns) {
    if (!column %in% names(table)) {
      next
    }
    values <- as.character(table[[column]])
    values[is.na(values)] <- ""
    mask <- mask | grepl(query, values, ignore.case = TRUE, fixed = fixed)
  }
  mask
}

.phenosigdb_core_metadata <- function(reference_species = "human") {
  db <- .phenosigdb_read(reference_species = reference_species)
  db <- db[order(db$signature_id, db$gene), , drop = FALSE]
  meta_columns <- c(
    "signature_id",
    "signature_name",
    "species",
    "species_original",
    "cell_family",
    "context",
    "disease",
    "tags",
    "weight"
  )
  meta_columns <- meta_columns[meta_columns %in% names(db)]
  meta <- db[!duplicated(db$signature_id), meta_columns, drop = FALSE]
  meta$domain <- sub("\\..*$", "", meta$signature_id)
  meta$source <- sub("^[^.]+\\.([^.]+)\\..*$", "\\1", meta$signature_id)
  meta$collection <- "curated"
  meta$source_resource <- "curated"
  if ("weight" %in% names(db)) {
    weight_present <- tapply(!is.na(db$weight), db$signature_id, any)
    meta$signature_format <- ifelse(weight_present[meta$signature_id], "continuous", "binary")
  } else {
    meta$signature_format <- "binary"
  }
  if ("species_original" %in% names(meta)) {
    meta$species <- ifelse(is.na(meta$species_original), meta$species, meta$species_original)
  }
  meta$n_genes <- as.integer(table(db$signature_id)[meta$signature_id])
  meta <- meta[, .phenosigdb_public_metadata_columns, drop = FALSE]
  rownames(meta) <- NULL
  meta
}

.phenosigdb_optional_metadata <- function(reference_species = "human") {
  .phenosigdb_require_arrow()
  frames <- list()
  for (resource in .phenosigdb_known_resources()$resource) {
    path <- file.path(.phenosigdb_resource_dir(resource), "metadata.parquet")
    if (!file.exists(path)) {
      next
    }
    frame <- arrow::read_parquet(path, as_data_frame = TRUE)
    for (column in .phenosigdb_resource_metadata_columns) {
      if (!column %in% names(frame)) {
        frame[[column]] <- NA
      }
    }
    if (reference_species != "original") {
      species <- as.character(frame$species_original)
      species[is.na(species)] <- ""
      frame <- frame[tolower(species) == tolower(reference_species), , drop = FALSE]
    }
    frames[[length(frames) + 1L]] <- frame[, .phenosigdb_resource_metadata_columns, drop = FALSE]
  }
  if (!length(frames)) {
    return(data.frame(setNames(replicate(length(.phenosigdb_resource_metadata_columns), logical(0), simplify = FALSE), .phenosigdb_resource_metadata_columns)))
  }
  out <- do.call(rbind, frames)
  out <- out[order(out$signature_id), , drop = FALSE]
  rownames(out) <- NULL
  out
}

.phenosigdb_resource_for_signature_id <- function(signature_id) {
  text <- toupper(trimws(as.character(signature_id)))
  resources <- .phenosigdb_known_resources()
  for (i in seq_len(nrow(resources))) {
    if (startsWith(text, toupper(resources$prefix[[i]]))) {
      return(resources$resource[[i]])
    }
  }
  NULL
}

.phenosigdb_ensure_optional_resources_available <- function(signature_ids, verbose = TRUE) {
  if (is.null(signature_ids) || !length(signature_ids)) {
    return(invisible(NULL))
  }
  statuses <- phenosigdb_resources("list", verbose = FALSE)
  missing <- character()
  for (signature_id in signature_ids) {
    resource <- .phenosigdb_resource_for_signature_id(signature_id)
    if (is.null(resource)) {
      next
    }
    installed <- statuses$installed[match(resource, statuses$resource)]
    if (!length(installed) || is.na(installed) || !installed) {
      missing <- c(missing, resource)
    }
  }
  missing <- unique(missing)
  if (length(missing)) {
    .phenosigdb_install_resources(missing, force = FALSE, verbose = verbose)
  }
}

.phenosigdb_optional_values <- function(signature_ids = NULL, reference_species = "human") {
  .phenosigdb_require_arrow()
  values <- list()
  metadata <- .phenosigdb_optional_metadata(reference_species = reference_species)
  if (!is.null(signature_ids)) {
    metadata <- metadata[metadata$signature_id %in% signature_ids, , drop = FALSE]
  }
  if (!nrow(metadata)) {
    return(values)
  }

  for (resource in unique(metadata$resource_key)) {
    format_name <- unique(metadata$signature_format[metadata$resource_key == resource])[1]
    ids <- metadata$signature_id[metadata$resource_key == resource]
    if (identical(format_name, "binary")) {
      path <- file.path(.phenosigdb_resource_dir(resource), "binary.parquet")
      frame <- arrow::read_parquet(path, as_data_frame = TRUE)
      frame <- frame[frame$signature_id %in% ids, c("signature_id", "gene"), drop = FALSE]
      frame <- frame[order(frame$signature_id, frame$gene), , drop = FALSE]
      split_values <- split(frame$gene, frame$signature_id)
      split_values <- lapply(split_values, unique)
      values[names(split_values)] <- split_values
    } else if (identical(format_name, "continuous")) {
      path <- file.path(.phenosigdb_resource_dir(resource), "continuous.parquet")
      frame <- arrow::read_parquet(path, as_data_frame = TRUE)
      frame <- frame[frame$signature_id %in% ids, c("signature_id", "gene", "weight"), drop = FALSE]
      frame <- frame[order(frame$signature_id, frame$gene), , drop = FALSE]
      frame <- frame[!duplicated(paste(frame$signature_id, frame$gene, sep = "\r")), , drop = FALSE]
      split_frames <- split(frame, frame$signature_id)
      split_values <- lapply(
        split_frames,
        function(subframe) stats::setNames(as.numeric(subframe$weight), as.character(subframe$gene))
      )
      values[names(split_values)] <- split_values
    }
  }
  values
}

phenosigdb_resources <- function(action = "list", resource = NULL, force = FALSE, verbose = TRUE) {
  action <- match.arg(action, c("list", "install", "remove", "update", "path"))
  if (identical(action, "path")) {
    return(.phenosigdb_cache_dir_create())
  }
  if (identical(action, "list")) {
    return(do.call(rbind, lapply(.phenosigdb_known_resources()$resource, .phenosigdb_resource_status_row)))
  }
  if (identical(action, "install") && (is.null(resource) || !nzchar(trimws(resource)))) {
    return(.phenosigdb_install_resources(force = force, verbose = verbose, action = "install"))
  }
  if (identical(action, "update") && (is.null(resource) || !nzchar(trimws(resource)))) {
    return(.phenosigdb_install_resources(force = force, verbose = verbose, action = "update"))
  }
  if (is.null(resource) || !nzchar(trimws(resource))) {
    stop("resource is required for this action", call. = FALSE)
  }
  resource <- tolower(trimws(resource))
  if (!resource %in% .phenosigdb_known_resources()$resource) {
    available <- paste(.phenosigdb_known_resources()$resource, collapse = ", ")
    stop("Unknown resource: ", resource, ". Available resources: ", available, call. = FALSE)
  }
  if (identical(action, "remove")) {
    return(.phenosigdb_remove_resource(resource, verbose = verbose))
  }
  if (identical(action, "install")) {
    return(.phenosigdb_install_resource(resource, force = force, verbose = verbose, action = "install"))
  }
  .phenosigdb_install_resource(resource, force = force, verbose = verbose, action = "update")
}

list_signatures <- function(query = NULL, reference_species = "human", fixed = FALSE) {
  reference_species <- match.arg(reference_species, c("human", "mouse", "original"))
  core <- .phenosigdb_core_metadata(reference_species = reference_species)
  optional <- .phenosigdb_optional_metadata(reference_species = reference_species)
  meta <- if (nrow(optional)) rbind(core, optional) else core
  meta <- meta[order(meta$signature_id), .phenosigdb_public_metadata_columns, drop = FALSE]
  if (!is.null(query)) {
    search_columns <- setdiff(names(meta), "n_genes")
    meta <- meta[.phenosigdb_search_mask(meta, query = query, columns = search_columns, fixed = fixed), , drop = FALSE]
  }
  rownames(meta) <- NULL
  meta
}

phenosigdb_version <- function() {
  .phenosigdb_package_version
}

get_signatures <- function(signature_ids = NULL, reference_species = "human") {
  reference_species <- match.arg(reference_species, c("human", "mouse", "original"))
  db <- .phenosigdb_read(reference_species = reference_species)
  if (!"weight" %in% names(db)) {
    db$weight <- NA_real_
  }
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
  split_frames <- split(db, db$signature_id)
  signatures <- lapply(
    split_frames,
    function(subframe) {
      if (any(!is.na(subframe$weight))) {
        subframe <- subframe[!duplicated(subframe$gene), c("gene", "weight"), drop = FALSE]
        return(stats::setNames(as.numeric(subframe$weight), as.character(subframe$gene)))
      }
      unique(as.character(subframe$gene))
    }
  )

  .phenosigdb_ensure_optional_resources_available(ordered_ids)
  optional <- .phenosigdb_optional_values(signature_ids = ordered_ids, reference_species = reference_species)
  signatures[names(optional)] <- optional

  if (is.null(signature_ids)) {
    return(signatures)
  }
  signatures[ordered_ids[ordered_ids %in% names(signatures)]]
}
