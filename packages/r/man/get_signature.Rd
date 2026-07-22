\name{get_signature}
\alias{get_signature}
\title{Get one signature}
\usage{
get_signature(signature_id, reference_species = "human")
}
\arguments{
  \item{signature_id}{One signature ID.}
  \item{reference_species}{One of \code{"human"}, \code{"mouse"}, or \code{"original"}.}
}
\value{A character vector for binary signatures or named numeric vector for continuous signatures.}
\description{Returns one PhenoSigDB signature by ID.}
