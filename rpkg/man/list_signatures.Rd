\name{list_signatures}
\alias{list_signatures}
\title{List available signatures}
\usage{
list_signatures(query = NULL, reference_species = "human", fixed = FALSE)
}
\arguments{
  \item{query}{Optional search string. Regex by default (set \code{fixed = TRUE} for literal text).}
  \item{reference_species}{One of \code{"human"}, \code{"mouse"}, or \code{"original"}.}
  \item{fixed}{Logical. If \code{TRUE}, treat \code{query} as literal text. If \code{FALSE} (default), treat as regular expression.}
}
\value{
A data frame with one row per signature and these columns:
\code{signature_id}, \code{signature_name}, \code{domain}, \code{source},
\code{collection}, \code{source_resource}, \code{signature_format},
\code{species}, \code{cell_family}, \code{context}, \code{disease},
\code{n_genes}.
}
\description{
Lists available PhenoSigDB signatures. The default reference is human.
The \code{query} argument does case-insensitive regex search across these metadata columns:
\code{signature_id}, \code{signature_name}, \code{domain}, \code{source},
\code{collection}, \code{source_resource}, \code{signature_format},
\code{species}, \code{cell_family}, \code{context}, \code{disease}.
The \code{n_genes} column is NOT searched.
}
