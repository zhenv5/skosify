# Introduction #

In SKOS vocabularies, [Collections can be used to group Concepts](http://www.w3.org/TR/skos-primer/#seccollections). The canonical example of such a grouping is "milk by source animal", which includes e.g. "cow milk" and "goat milk".

SKOS specifies Collections as disjoint from Concepts. Thus they cannot be used with SKOS semantic relations (broader, narrower, related etc.). Instead, Concepts that are part of a Collection are (usually) defined using the skos:member property.


# Transformation of Collections #

In some vocabularies, groups/collections of concepts are modelled similarly to concepts and are included in the same hierarchy. For example, the Finnish General Upper Ontology YSO uses the GroupConcept class to represent concept groups, and these are included as nodes in the rdfs:subClassOf hierarchy just like regular Concepts. Thus they cannot be directly represented using skos:Collection and skos:broader.

Skosify checks for this structural problem and corrects it by removing the Collections from the skos:broader hierarchy, replacing the hierarchical relationships with skos:member properties.

![http://skosify.googlecode.com/svn/images/collection-example.png](http://skosify.googlecode.com/svn/images/collection-example.png)

Figure: Example of transforming Collections.

When doing a transformation from an OWL vocabulary to SKOS (see OWLconversionToSKOS), it is sufficient to map the Concept and GroupConcept types into skos:Concept and skos:Collection, and the hierarchical relationship (e.g. rdfs:subClassOf) into skos:broader. Skosify will then take care of first transforming the types and then correcting the representation of Collections.


# Limitations in Collection support #

Skosify does not currently support the skos:OrderedCollection type or the skos:memberList property.