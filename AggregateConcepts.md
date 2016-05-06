# Introduction #

Aggregate Concepts are used in some FinnONTO ontologies to represent the situation when a concept has been determined to be ambiguous and has been split into several concepts representing the different meanings. The aggregate concept is a marker for the old, unsplit, ambiguous concept and contains an explicit representation of its relationship to the new component concepts.

# Transforming aggregate concepts to SKOS #

There is no "official" SKOS representation for aggregate concepts. When Skosify encounters an aggregate concept, it will create a special concept scheme for these and place the aggregate concepts within this aggregate concept scheme. Otherwise they are represented as regular skos:Concepts. The mapping between the unsplit aggregate concepts and the constituent parts is represented using the skos:broadMatch property.

![http://skosify.googlecode.com/svn/images/aggregate-example.png](http://skosify.googlecode.com/svn/images/aggregate-example.png)

Figure: Example of transforming aggregate concepts into a SKOS representation. Note that the owl:unionOf representation actually uses a rdf:List, as specified by OWL.