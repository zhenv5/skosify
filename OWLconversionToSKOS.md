# Introduction #

You can use Skosify to transform any vocabulary-like RDF/RDFS/OWL ontology into SKOS format. You need to specify the way yor ontology structure maps to SKOS constructs using a configuration file. See the provided configuration file examples [owl2skos.cfg](http://code.google.com/p/skosify/source/browse/trunk/owl2skos.cfg) and [finnonto.cfg](http://code.google.com/p/skosify/source/browse/trunk/finnonto.cfg) in the Skosify distribution package.

The specification is performed by editing the configuration file sections `[types]`, `[literals]` and `[relations]`.

Based on the three mappings, Skosify will change your ontology structure. This is a destructive operation: the old structure is replaced by the new (presumably more SKOS-like) structure.

As an alternative, you can consider extending SKOS using RDFS subclass and subproperty definitions and use the [RDFSInference](RDFSInference.md) capabilities of Skosify. In that approach, the original structure is kept intact. It may be more appropriate to do so if your ontology already follows SKOS conventions, but extends SKOS using RDFS.

# `[types]` #

This section specifies how your classes correspond to SKOS classes. You most probably want to map one or more classes to skos:Concept, and possibly to skos:Collection as well. Instances of the matching class will be converted to the new (SKOS) class.

The key in the dictionary can either be a full URI (using [CURIE](http://www.w3.org/TR/curie/) syntax, but with a period as separator) or a string which matches the last part (local name) of a URI. The string may start with an asterisk, which matches any prefix.

The value part is the SKOS class (again defined using CURIE syntax, with either period or colon separator) which will be used to replace the matching classes. It can be empty, which causes matching instances to be deleted instead.

# `[literals]` #

Similarly to `[types]`, this defines what to do with properties of your classes which have a literal value. Usually these will be mapped to SKOS label or notation properties, or to Dublin Core properties.

An asterisk can be used to map any prefix. An empty value causes the property to be deleted.

# `[relations]` #

This is otherwise similar to `[literals]`, but performed on properties with a resource value. This can be used to map a hierarchical relation such as rdfs:subClassOf into a SKOS equivalent such as skos:broader.

An asterisk can be used to map any prefix. An empty value causes the property to be deleted.