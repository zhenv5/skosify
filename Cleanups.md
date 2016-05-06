# Introduction #

Skosify identifies some types of garbage data often found in SKOS vocabularies (especially after transformation from OWL). It tries to identify these and remove the unnecessary triples from the vocabulary.

Cleanups are performed after transformations but before validation.

# Unnecessary class definitions #

Skosify removes definitions of SKOS classes (skos:Concept, skos:Collection etc.) as their proper place is the SKOS RDF definition, not an individual SKOS vocabulary.

Skosify will also remove any OWL or RDFS classes of which there are no instances in the vocabulary.

# Unnecessary property definitions #

Skosify removes definitions of SKOS and Dublin Core properties, as their proper place is the respective RDF definition.

Skosify will also remove any property definition that is not used in the vocabulary itself (i.e. does not appear as a property part of any triple).

# Unreachable triples #

Skosify will remove any triples that are not connected to the main vocabulary in any way. Typically this will find and remove parts of rdf:List structures which have been left behind when an ontology has been modified, or other structures which consist mainly of blank nodes.