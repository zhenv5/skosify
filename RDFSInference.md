Skosify supports basic RDFS subclass and  subproperty inference when given the `--infer` option. The inference is performed early, just after reading the input file.

This inference allows specializing the SKOS model by adding custom versions of SKOS concepts and properties, which will then be automatically translated to the SKOS constructs by Skosify (without losing the original types and properties). See [SKOS Primer, section 4.7](http://www.w3.org/TR/skos-primer/#secskosspecialization) for examples.

The inference implementation is quite naïve and the inference is only performed once. See [issue #5](https://code.google.com/p/skosify/issues/detail?id=#5) for plans for performing inference later in the processing.