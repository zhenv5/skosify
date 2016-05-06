# Introduction #

Skosify supports checking many of the validity criteria for SKOS vocabularies expressed in the SKOS reference. It can also fix many of the issues automatically.

Links to the relevant section in the SKOS reference have been provided below. S`<number>` refers to the formal definitions in the SKOS reference.

# Hierachy cycle detection #

Skosify will check that the skos:broader hierarchy does not contain cycles. If cycles are found, Skosify will break the cycle by removing the skos:broader relationship that causes the cycle, and print a warning message.

Note that cycles in the hierarchy are not forbidden in SKOS, but can be considered bad practice and will likely cause problems.

# Disjoint semantic relations #

SKOS defines the skos:related relation to be disjoint with skos:broaderTransitive; that is, two concepts cannot be connected by both ([S27](http://www.w3.org/TR/skos-reference/#L2422)). Skosify will check this condition and if found it will remove the skos:related relationship and print a warning message.

# Removal of extra whitespace #

Skosify will find label property values (skos:prefLabel, skos:altLabel and skos:hiddenLabel) with surrounding whitespace, remove the whitespace and print out a warning message.

Note that extra whitespace is not forbidden by SKOS.

# Only one skos:prefLabel per language #

Skosify will check that concepts have only one skos:prefLabel per language ([S14](http://www.w3.org/TR/skos-reference/#L1567)). If a concept has more than one skos:prefLabel with the same language tag, one will be arbitrarily selected as the real one (by default, the shortest one, but that can be changed using the `--preflabel-policy` option) and the rest will be converted to skos:altLabels. Skosify will also print a warning message.

# Overlap in disjoint label properties #

SKOS specifies that the label properties skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint, so a concept may not have the same label in more than one of these properties ([S13](http://www.w3.org/TR/skos-reference/#L1567)). Skosify checks that this is the case, and if necessary, removes the value for the less important property (hiddenLabel < altLabel < prefLabel) and prints a warning message.

# Unimplemented validation checks #

Some SKOS integrity constraints are not checked in Skosify, e.g. [S37](http://www.w3.org/TR/skos-reference/#L3424) and [S46](http://www.w3.org/TR/skos-reference/#L5429).

You can use the [PoolParty SKOS validator](http://demo.semantic-web.at:8080/SkosServices/check) to perform a more comprehensive validation of your SKOS vocabulary.