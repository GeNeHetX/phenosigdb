\name{phenosigdb_resources}
\alias{phenosigdb_resources}
\title{Manage optional resources}
\usage{
phenosigdb_resources(action = "list", resource = NULL, force = FALSE, verbose = TRUE)
}
\arguments{
  \item{action}{One of \code{"list"}, \code{"install"}, \code{"remove"}, \code{"update"}, or \code{"path"}.}
  \item{resource}{Optional resource name: \code{celltypist}, \code{cellmarker}, \code{msigdb_c7immune}, \code{msigdb_c8celltype}, \code{pid}, \code{biocarta}, \code{reactome}, or \code{wikipathways}.}
  \item{force}{Logical. Reinstall if already present.}
  \item{verbose}{Logical. Print progress messages.}
}
\value{
Either a cache path or a data frame describing optional resources.
}
\description{
Lists, installs, updates, removes, or locates optional PhenoSigDB resources. With \code{action = "install"} and \code{resource = NULL}, installs all missing optional resources.
}
