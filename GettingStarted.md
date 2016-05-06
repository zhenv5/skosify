# Introduction #

Skosify was created in order to transform a collection of thesaurus-like OWL ontologies into a standard SKOS format. It works by stepwise adjusting the input ontology so that it becomes more SKOS-like.

You can give it any RDF/RDFS, OWL or SKOS vocabulary as input. However, to get meaningful results the input should be a thesaurus-like vocabulary or ontology, i.e. someting that can be usefully represented using SKOS.

# Operation #

Skosify will adjust the structure of the vocabulary using the following processing steps:

  1. Read the input file. Supported formats include RDF/XML, Turtle, N3 and N-Triples (i.e. anything that rdflib supports).
  1. Make sure the vocabulary has a defined skos:ConceptScheme.
    1. If not, see if it has an owl:Ontology instance and convert that to a skos:ConceptScheme.
    1. Otherwise create a skos:ConceptScheme. This will require that the `--namespace` parameter is given.
  1. If enabled, perform RDFS subclass and subproperty inference. See [RDFSInference](RDFSInference.md) for details.
  1. Transform classes/concepts, literals and relations according to the `[types]`, `[literals]` and `[relations]` mappings defined in a configuration file. See [OWLconversionToSKOS](OWLconversionToSKOS.md) for details.
  1. Make sure that skos:Collections have the right structure, i.e. they are defined outside the concept hierarchy. See [Collections](Collections.md) for details.
  1. Transform _aggregate concepts_ into a more SKOS-like representation. This is a peculiarity of some FinnONTO ontologies which you can safely ignore. See [AggregateConcepts](AggregateConcepts.md) for details.
  1. Enrich the vocabulary by performing inferences specified in SKOS. Optionally add skos:narrower, skos:broaderTransitive and skos:narrowerTransitive relationships. See [SKOSInference](SKOSInference.md) for details.
  1. Clean up unused and/or unnecessary class and property definitions and unreachable triples. See [Cleanups](Cleanups.md) for details.
  1. Make sure all concepts have a skos:inScheme relation to a skos:ConceptScheme.
  1. Make sure the topmost concepts have been identified using skos:hasTopConcept and skos:topConceptOf relationships.
  1. Perform some validations. See [Validation](Validation.md) for details.
    1. Check for loops in the skos:broader hierarchy and break them.
    1. Check for overlap in disjoint semantic relations (skos:related and skos:broaderTransitive) and correct any inconsistencies.
    1. Remove extra whitespace from labels.
    1. Check that concepts have only one skos:prefLabel per language and correct any inconsistencies.
    1. Check for overlap in disjoint label properties and correct any inconsistencies.
  1. Write out the resulting SKOS vocabulary (as RDF/XML, N3/Turtle...)

# Installation #

Get a copy Skosify from the Google Code SVN repository:

`svn checkout http://skosify.googlecode.com/svn/trunk/ skosify-read-only`

There is no special installation needed, but you will need Python (version 2.6 or newer, but not 3.x) and the rdflib Python library (version 2.4.x, 3.x or 4.x). Using rdflib 4.x is recommended particularly for large vocabularies. In versions up to 0.6, Skosify contained a custom rdflib Store implementation: a set-based in-memory RDF store (SetStore) that is often slightly faster and consumes much less memory than the original rdflib implementation. SetStore was incorporated into rdflib 4.0 and thereafter removed from Skosify, starting with version 0.7.

Skosify has been developed on Ubuntu Linux 10.04 and 12.04, but should work on other platforms as well if you install the above dependencies.

# Running #

Simple usage of Skosify:

`./skosify.py myvoc.rdf -o myvoc-skos.rdf`

This will read the file `myvoc.rdf` (assumed to be in RDF/XML format due to the extension) and write output into the file `myvoc-skos.rdf` as RDF/XML.

For detailed help, see

`./skosify.py --help`