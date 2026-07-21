\name{get_signatures}
\alias{get_signatures}
\title{Get signatures}
\usage{
get_signatures(signature_ids = NULL, reference_species = "human")
}
\arguments{
  \item{signature_ids}{Optional character vector of signature IDs.}
  \item{reference_species}{One of \code{"human"}, \code{"mouse"}, or \code{"original"}.}
}
\value{
A named list. Binary signatures return character vectors. Continuous signatures return named numeric vectors.
}
\description{
Returns PhenoSigDB signatures by \code{signature_id}. Binary signatures return gene vectors. Continuous signatures return named weight vectors. Optional resources are installed automatically if needed.
}
