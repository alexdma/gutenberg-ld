Gutenberg-LD
============
This is a suite of scripts and models that refactor the metadata set of the [Project Gutenberg](https://www.gutenberg.org) digital library, with the aim of turning it into a proper Linked Data set.

## Features

* Reconciliation of blank nodes, resulting in a much smaller dataset (~29% smaller as of March 2020)
* Linking with Library of Congress subject headings and classification systems
* Structuring of Table Of Contents data
* Ontology alignment of undocumented Gutenberg terms

## Requirements

You need:
* Python 3
* an RDF store with SPARQL querying/updating over HTTP (e.g. Jena Fuseki, Virtuoso, BlazeGraph)
* The Project Gutenberg catalog as RDF - Download at https://www.gutenberg.org/wiki/Gutenberg:Feeds

## Usage

1. Download the metadata set from Gutenberg and load it onto your RDF store.
2. `cd gutenberg-fixes`
3. In `settings.py` set the SPARQL service and RDF graph name
4. `python refactor.py bookshelves formats toc` (or a subset of the three arguments)
5. in [gutenberg-fixes/queries](gutenberg-fixes/queries) you can find other SPARQL queries to run by yourselves.

## Licensing

Gutenberg-LD is licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full license text.
