\name{list_signatures}
\alias{list_signatures}
\title{List signatures}
\usage{
list_signatures(query = NULL, columns = NULL, min_genes = NULL,
signature_format = NULL, ...)
}
\arguments{
\item{query}{One case-insensitive regular expression searched across the default metadata columns.}
\item{columns}{Optional character vector selecting metadata columns to search.}
\item{min_genes}{Optional minimum number of genes.}
\item{signature_format}{Optional \code{"binary"} or \code{"continuous"}.}
\item{...}{Optional arguments passed to R's \code{grepl} regex function.}
}
\value{A data frame of signature metadata.}
\description{Lists original signatures once. The result can be passed directly to \code{get_signatures()}.}
