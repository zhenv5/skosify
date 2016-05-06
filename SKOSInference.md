# Introduction #

SKOS defines some rules that can be automatically applied to enhance a vocabulary expressed in SKOS. Skosify supports many of these inferences and can perform them automatically.

The inferences are implemented manually in the Skosify code. In a perfect world most of them could easily be performed with an OWL reasoner, but in practice the reasoning could generate its own problems such as redundant data in the vocabulary.

Links to the relevant section in the SKOS reference have been provided below. S`<number>` refers to the formal definitions in the SKOS reference.

# Related relationship inference #

SKOS defines the skos:related property as symmetric ([S23](http://www.w3.org/TR/skos-reference/#L2055)). Skosify makes sure that skos:related is always defined in both directions even though the original vocabulary only defines it in one direction.

(This may be considered redundant information. A future version may allow pruning the skos:related relationships instead, so that only one direction is retained.)

# Hierarchical broader/narrower inference #

The hierarchical skos:broader and skos:narrower properties are defined as the inverse of each other ([S25](http://www.w3.org/TR/skos-reference/#L2055)). Skosify will automatically convert skos:broader relationships to skos:narrower relationships in the oppposite direction, and vice versa.

The skos:narrower relationships can be considered redundant information.
When given the option `--no-narrower`, Skosify will remove the skos:narrower relationships.


# Transitive closure inference #

SKOS defines the transitive properties skos:broaderTransitive and skos:narrowerTransitive which can be used to find all the parents/siblings of a concept ([S22,S24](http://www.w3.org/TR/skos-reference/#L2055)). When given the `--transitive` option, Skosify will generate all the possible skos:broaderTransitive relations (i.e. transitive closure).

If skos:narrower relationships are enabled (see above), skos:narrowerTransitive relations are also generated.

Note that adding the transitive relations can substantially increase the number of triples in a vocabulary.