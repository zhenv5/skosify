#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Osma Suominen <osma.suominen@tkk.fi>
# Copyright (c) 2010-2011 Aalto University and University of Helsinki
# MIT License
# see README.txt for more information

import sys
import time

try:
  from RDF import Model, NS, Uri, Node, Statement, HashStorage, Parser, Serializer
except ImportError:
  print >>sys.stderr, "You need to install the librdf Python library (http://librdf.org)."
  print >>sys.stderr, "On Debian/Ubuntu, try: sudo apt-get install python-librdf"
  sys.exit(1)

# namespace defs
RDF = NS("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = NS("http://www.w3.org/2000/01/rdf-schema#")
SKOS = NS("http://www.w3.org/2004/02/skos/core#")
SKOSEXT = NS("http://purl.org/finnonto/schema/skosext#")
OWL = NS("http://www.w3.org/2002/07/owl#")
DC = NS("http://purl.org/dc/elements/1.1/")
DCT = NS("http://purl.org/dc/terms/")

# default namespaces to register in the graph
DEFAULT_NAMESPACES = {
  'rdf': Uri(RDF._prefix),
  'rdfs': Uri(RDFS._prefix),
  'owl': Uri(OWL._prefix),
  'skos': Uri(SKOS._prefix),
  'dc': Uri(DC._prefix),
  'dct': Uri(DCT._prefix),
}

# default values for config file / command line options
DEFAULT_OPTIONS = {
  'output': '-',
  'from_format': None,
  'to_format': None,
  'narrower': True,
  'transitive': False,
  'aggregates': False,
  'namespace': None,
  'debug': False,
  'infer': False,
}




# global flag for debugging
debugging = False



def debug(str):
  if debugging:
    print >>sys.stderr, "[debug]", str.encode('UTF-8')

def warn(str):
  print >>sys.stderr, "Warning:", str.encode('UTF-8')

def error(str):
  print >>sys.stderr, "ERROR:", str.encode('UTF-8')
  sys.exit(1)

def localname(uri):
  """Determine the local name (after namespace) of the given URI"""
  return str(uri).split('/')[-1].split('#')[-1]

def mapping_get(uri, mapping):
  """Look up the URI in the given mapping and return the result. Throws KeyError if no matching mapping was found."""
  ln = localname(uri)
  # 1. try to match URI keys
  for k, v in mapping.iteritems():
    if k == uri:
      return v
  # 2. try to match local names
  for k, v in mapping.iteritems():
    if k == ln:
      return v
  # 3. try to match local names with * prefix
  # try to match longest first, so sort the mapping by key length
  l = mapping.items()
  l.sort(key=lambda i: len(str(i[0])), reverse=True)
  for k,v in l:
    k = str(k)
    if k[0] == '*' and ln.endswith(k[1:]):
      return v
  raise KeyError, uri

def mapping_match(uri, mapping):
  """Determine whether the given URI matches one of the given mappings. Returns True if a match was found, False otherwise."""
  try:
    val = mapping_get(uri, mapping)
    return True
  except KeyError:
    return False

def in_general_ns(uri):
  """Return True iff the URI is in a well-known general RDF namespace (RDF, RDFS, OWL, SKOS, DC)"""
  for ns in (RDF, RDFS, OWL, SKOS, DC):
    if str(uri).startswith(str(ns._prefix)): return True
  return False

def replace_subject(rdf, fromuri, touri):
  """Replace all occurrences of fromuri as subject with touri in the given
     model. If touri=None, will delete all occurrences of fromuri instead."""
  if fromuri == touri: return
  for stmt in rdf.find_statements(Statement(fromuri, None, None)):
    p = stmt.predicate
    o = stmt.object
    del rdf[Statement(fromuri, stmt.predicate, stmt.object)]
    if touri is not None:
      rdf.append(Statement(touri, stmt.predicate, stmt.object))

def replace_predicate(rdf, fromuri, touri, subjecttypes=None):
  """Replace all occurrences of fromuri as predicate with touri in the given
     model. If touri=None, will delete all occurrences of fromuri instead.
     If a subjecttypes sequence is given, modify only those triples where
     the subject is one of the provided types."""

  if fromuri == touri: return
  for stmt in rdf.find_statements(Statement(None, fromuri, None)):
    if subjecttypes is not None:
      typeok = False
      for t in subjecttypes:
        if Statement(stmt.subject, RDF.type, t) in rdf: typeok = True
      if not typeok: continue
    del rdf[Statement(stmt.subject, fromuri, stmt.object)]
    if touri is not None:
      rdf.append(Statement(stmt.subject, touri, stmt.object))

def replace_object(rdf, fromuri, touri, predicate=None):
  """Replace all occurrences of fromuri as object with touri in the given
     model. If touri=None, will delete all occurrences of fromuri instead. If
     predicate is given, modify only triples with the given predicate."""
  if fromuri == touri: return
  for stmt in rdf.find_statements(Statement(None, predicate, fromuri)):
    del rdf[Statement(stmt.subject, stmt.predicate, fromuri)]
    if touri is not None:
      rdf.append(Statement(stmt.subject, stmt.predicate, touri))

def replace_uri(rdf, fromuri, touri):
  """Replace all occurrences of fromuri with touri in the given model. If touri=None, will delete all occurrences of fromuri instead."""
  replace_subject(rdf, fromuri, touri)
  replace_predicate(rdf, fromuri, touri)
  replace_object(rdf, fromuri, touri)

def delete_uri(rdf, uri):
  """Delete all occurrences of uri in the given model."""
  replace_uri(rdf, uri, None)

def find_prop_overlap(rdf, prop1, prop2):
  """Generate pairs of (subject,object) tuples which are connected by both prop1 and prop2."""
  for s,o in rdf.subject_objects(prop1):
    if (s,prop2,o) in rdf:
      yield (s,o)

def read_input(filename, fmt):
  """Read the given RDF file and return an librdf Model object."""
  
  if not fmt:
    # determine format based on file extension
    fmt = 'rdfxml' # default
    if filename.endswith('nt'): fmt = 'ntriples'
    if filename.endswith('n3'): fmt = 'turtle'
    if filename.endswith('ttl'): fmt = 'turtle'

  store = HashStorage("skosify", options="hash-type='memory'")
  rdf = Model(store)
  parser = Parser(name=fmt)
  
  if filename == '-':
    data = sys.stdin.read()
    parser.parse_string_into_model(rdf, data, "http://example.org/")
  else:
    parser.parse_into_model(rdf, "file:" + filename)
  
  return (rdf, parser.namespaces_seen())

def get_concept_scheme(rdf):
  """Return a skos:ConceptScheme contained in the model, or None if not present."""
  for cs in rdf.sources(RDF.type, SKOS.ConceptScheme):
    return cs # the first match
  return None

def create_concept_scheme(rdf, ns, lname='conceptscheme'):
  """Create a skos:ConceptScheme in the model and return it."""

  ont = None
  if not ns:
    # see if there's an owl:Ontology and use that to determine namespace
    # FIXME what if there are several owl:Ontology instances? (TERO)
    for ont in rdf.sources(RDF.type, OWL.Ontology):
      pass
    if not ont:
      error("No skos:ConceptScheme or owl:Ontology found, please set the vocabulary namespace using --namespace option")
    if str(ont.uri).endswith('/') or str(ont.uri).endswith('#'):
      ns = unicode(ont)
    else:
      ns = unicode(ont.uri) + '/'
  
  cs = Uri((ns + lname).encode('UTF-8')) # unicode objs don't always work here
  
  rdf.append(Statement(cs, RDF.type, SKOS.ConceptScheme))
  
  if ont is not None:
    del rdf[Statement(ont, RDF.type, OWL.Ontology)]
    # remove owl:imports declarations
    for o in rdf.targets(ont, OWL.imports):
      del rdf[Statement(ont, OWL.imports, o)]
    # remove protege specific properties
    for stmt in rdf.find_statements(Statement(ont, None, None)):
      p = stmt.predicate
      o = stmt.object
      if str(p.uri).startswith('http://protege.stanford.edu/plugins/owl/protege#'):
        del rdf[Statement(ont,p,o)]
    # move remaining properties (dc:title etc.) of the owl:Ontology into the skos:ConceptScheme
    replace_uri(rdf, ont, cs)
    
  return cs


def infer_classes(rdf):
  """Do RDFS subclass inference: mark all resources with a subclass type with the upper class."""

  debug("doing RDFS subclass inference")
  # find out the subclass mappings
  upperclasses = {}	# key: class val: set([superclass1, superclass2..])
  for s,o in rdf.subject_objects(RDFS.subClassOf):
    upperclasses.setdefault(s, set())
    for uc in rdf.transitive_objects(s, RDFS.subClassOf):
      if uc != s:
        upperclasses[s].add(uc)

  # set the superclass type information for subclass instances
  for s,ucs in upperclasses.iteritems():
    debug("setting superclass types: %s -> %s" % (s, str(ucs)))
    for res in rdf.subjects(RDF.type, s):
      for uc in ucs:
        rdf.add((res, RDF.type, uc))
  

def infer_properties(rdf):
  """Do RDFS subproperty inference: add superproperties where subproperties have been used."""

  debug("doing RDFS subproperty inference")
  # find out the subproperty mappings
  superprops = {}	# key: property val: set([superprop1, superprop2..])
  for s,o in rdf.subject_objects(RDFS.subPropertyOf):
    superprops.setdefault(s, set())
    for sp in rdf.transitive_objects(s, RDFS.subPropertyOf):
      if sp != s:
        superprops[s].add(sp)
  
  # add the superproperty relationships
  for p,sps in superprops.iteritems():
    debug("setting superproperties: %s -> %s" % (p, str(sps)))
    for s,o in rdf.subject_objects(p):
      for sp in sps:
        rdf.add((s,sp,o))
  

def transform_concepts(rdf, cs, typemap):
  """Transform YSO-style Concepts into skos:Concepts, GroupConcepts into skos:Collections and AggregateConcepts into ...what?"""

  # find out all the types used in the model
  types = set()
  for stmt in rdf.find_statements(Statement(None, RDF.type, None)):
    o = stmt.object
    if o.uri not in typemap and in_general_ns(o.uri): continue
    types.add(o.uri)

  for t in types:
    if mapping_match(t, typemap):
      newval = mapping_get(t, typemap)
      debug("transform class %s -> %s" % (t, newval))
      if newval is None: # delete all instances
        for inst in rdf.sources(RDF.type, t):
          delete_uri(rdf, inst)
        delete_uri(rdf, t)
      else:
        replace_object(rdf, t, newval, predicate=RDF.type)
    else:
      warn("Don't know what to do with type %s" % t)
      

def transform_literals(rdf, literalmap):
  """Transform YSO-style labels and other literal properties of Concepts into SKOS equivalents."""
  
  affected_types = (SKOS.Concept, SKOS.Collection)
  
  props = set()
  for t in affected_types:
    for conc in rdf.sources(RDF.type, t):
      for stmt in rdf.find_statements(Statement(conc, None, None)):
        p = stmt.predicate.uri
        o = stmt.object
        if o.is_literal() and (p in literalmap or not in_general_ns(p)):
          props.add(p)

  for p in props:
    if mapping_match(p, literalmap):
      newval = mapping_get(p, literalmap)
      debug("transform literal %s -> %s" % (p, newval))
      replace_predicate(rdf, p, newval, subjecttypes=affected_types)
    else:
      warn("Don't know what to do with literal %s" % p)
      

def transform_relations(rdf, relationmap):
  """Transform YSO-style concept relations into SKOS equivalents."""

  affected_types = (SKOS.Concept, SKOS.Collection)

  props = set()
  for t in affected_types:
    for conc in rdf.subjects(RDF.type, t):
      for p,o in rdf.predicate_objects(conc):
        if isinstance(o, (URIRef, BNode)) and (p in relationmap or not in_general_ns(p)):
          props.add(p)
  
  for p in props:
    if mapping_match(p, relationmap):
      newval = mapping_get(p, relationmap)
      debug("transform relation %s -> %s" % (p, newval))
      replace_predicate(rdf, p, newval, subjecttypes=affected_types)
    else:
      warn("Don't know what to do with relation %s" % p)

def transform_labels(rdf):
  # fix labels with extra whitespace
  for labelProp in (SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel, SKOSEXT.candidateLabel):
    for conc, label in rdf.subject_objects(labelProp):
      if len(label.strip()) < len(label):
        warn("Stripping whitespace from label of %s: '%s'" % (conc, label))
        newlabel = Literal(label.strip(), label.language)
        rdf.remove((conc, labelProp, label))
        rdf.add((conc, labelProp, newlabel))

  # make skosext:candidateLabel either prefLabel or altLabel
  
  # make a set of (concept, language) tuples for concepts which have candidateLabels in some language
  conc_lang = set([(c,l.language) for c,l in rdf.subject_objects(SKOSEXT.candidateLabel)])
  for conc, lang in conc_lang:
    # check whether there are already prefLabels for this concept in this language
    if lang not in [pl.language for pl in rdf.objects(conc, SKOS.prefLabel)]:
      # no -> let's transform the candidate labels into prefLabels
      to_prop = SKOS.prefLabel
    else:
      # yes -> let's make them altLabels instead
      to_prop = SKOS.altLabel
    
    # do the actual transform from candidateLabel to prefLabel or altLabel
    for label in rdf.objects(conc, SKOSEXT.candidateLabel):
      if label.language != lang: continue
      rdf.remove((conc, SKOSEXT.candidateLabel, label))
      rdf.add((conc, to_prop, label))
  
  
  for conc, label in rdf.subject_objects(SKOSEXT.candidateLabel):
    rdf.remove((conc, SKOSEXT.candidateLabel, label))
    if label.language not in [pl.language for pl in rdf.objects(conc, SKOS.prefLabel)]:
      # no prefLabel found, make this candidateLabel a prefLabel
      rdf.add((conc, SKOS.prefLabel, label))
    else:
      # prefLabel found, make it an altLabel instead
      rdf.add((conc, SKOS.altLabel, label))

def transform_collections(rdf):
  for coll in rdf.subjects(RDF.type, SKOS.Collection):
    broaders = set(rdf.objects(coll, SKOSEXT.broaderGeneric))
    narrowers = set(rdf.subjects(SKOSEXT.broaderGeneric, coll))
    # remove the Collection from the hierarchy
    for b in broaders:
      rdf.remove((coll, SKOSEXT.broaderGeneric, b))
    # replace the broaderGeneric relationship with inverse skos:member
    for n in narrowers:
      rdf.remove((n, SKOSEXT.broaderGeneric, coll))
      rdf.add((coll, SKOS.member, n))
      # add a direct broaderGeneric relation to the broaders of the collection
      for b in broaders:
        rdf.add((n, SKOSEXT.broaderGeneric, b))

    # avoid using SKOS semantic relations as they're only meant for concepts
    # FIXME should maybe use some substitute for exactMatch for collections?
    for relProp in (SKOS.semanticRelation, 
                    SKOS.broader, SKOS.narrower, SKOS.related,
                    SKOS.broaderTransitive, SKOS.narrowerTransitive,
                    SKOS.mappingRelation,
                    SKOS.closeMatch, SKOS.exactMatch,
                    SKOS.broadMatch, SKOS.narrowMatch, SKOS.relatedMatch):
      for o in rdf.objects(coll, relProp):
        warn("Removing concept relation %s -> %s from collection %s" %
             (localname(relProp), o, coll))
        rdf.remove((coll, relProp, o))
      for s in rdf.subjects(relProp, coll):
        warn("Removing concept relation %s <- %s from collection %s" %
             (localname(relProp), s, coll))
        rdf.remove((s, relProp, coll))

def transform_aggregate_concepts(rdf, cs, relationmap, aggregates):
  """Transform YSO-style AggregateConcepts into skos:Concepts within their
     own skos:ConceptScheme, linked to the regular concepts with
     SKOS.narrowMatch relationships. If aggregates is False, remove
     all aggregate concepts instead."""

  if not aggregates:
    debug("removing aggregate concepts")

  aggregate_concepts = []

  relation = relationmap.get(OWL.equivalentClass, OWL.equivalentClass)
  for conc, eq in rdf.subject_objects(relation):
    eql = rdf.value(eq, OWL.unionOf, None)
    if eql is None:
      continue
    if aggregates:
      aggregate_concepts.append(conc)
      for item in rdf.items(eql):
        rdf.add((conc, SKOS.narrowMatch, item))
    # remove the old equivalentClass-unionOf-rdf:List structure
    rdf.remove((conc, relation, eq))
    rdf.remove((eq, RDF.type, OWL.Class))
    rdf.remove((eq, OWL.unionOf, eql))
    # remove the rdf:List structure
    delete_uri(rdf, eql)
    if not aggregates:
      delete_uri(rdf, conc)
  
  if len(aggregate_concepts) > 0:
    ns = cs.replace(localname(cs), '')
    acs = create_concept_scheme(rdf, ns, 'aggregateconceptscheme')
    debug("creating aggregate concept scheme %s" % acs)
    for conc in aggregate_concepts:
      rdf.add((conc, SKOS.inScheme, acs))


def enrich_relations(rdf, use_narrower, use_transitive):
  """Enrich the SKOS relations according to SKOS semantics, including
     subproperties of broader and symmetric related properties. If
     use_narrower is True, include inverse narrower relations for all
     broader relations. If use_narrower is False, instead remove all
     narrower relations, replacing them with inverse broader relations. If
     use_transitive is True, calculate transitive hierarchical relationships
     (broaderTransitive, and also narrowerTransitive if use_narrower is
     True) and include them in the model."""

  # related goes both ways
  for s,o in rdf.subject_objects(SKOS.related):
    rdf.add((o, SKOS.related, s))

  # broaderGeneric -> broader + inverse narrowerGeneric
  for s,o in rdf.subject_objects(SKOSEXT.broaderGeneric):
    rdf.add((s, SKOS.broader, o))

  # broaderPartitive -> broader + inverse narrowerPartitive
  for s,o in rdf.subject_objects(SKOSEXT.broaderPartitive):
    rdf.add((s, SKOS.broader, o))

  # broader -> narrower
  if use_narrower: 
    for s,o in rdf.subject_objects(SKOS.broader):
      rdf.add((o, SKOS.narrower, s))
  # narrower -> broader
  for s,o in rdf.subject_objects(SKOS.narrower):
    rdf.add((o, SKOS.broader, s))
    if not use_narrower: 
      rdf.remove((s, SKOS.narrower, o))

  # transitive closure: broaderTransitive and narrowerTransitive  
  if use_transitive:
    for conc in rdf.subjects(RDF.type, SKOS.Concept):
      for bt in rdf.transitive_objects(conc, SKOS.broader):
        if bt == conc: continue
        rdf.add((conc, SKOS.broaderTransitive, bt))
        if use_narrower:
          rdf.add((bt, SKOS.narrowerTransitive, conc))

def setup_top_concepts(rdf):
  """Determine the top concepts of each concept scheme and mark them using hasTopConcept/topConceptOf."""

  for cs in rdf.subjects(RDF.type, SKOS.ConceptScheme):
    for conc in rdf.subjects(SKOS.inScheme, cs):
      # check whether it's a top concept
      broader = rdf.value(conc, SKOS.broader, None, any=True)
      if broader is None: # yes it is a top concept!
        rdf.add((cs, SKOS.hasTopConcept, conc))
        rdf.add((conc, SKOS.topConceptOf, cs))

def setup_concept_scheme(rdf, defaultcs):
  """Make sure all concepts have an inScheme property, using the given default concept scheme if necessary."""
  for conc in rdf.subjects(RDF.type, SKOS.Concept):
    # check concept scheme
    cs = rdf.value(conc, SKOS.inScheme, None, any=True)
    if cs is None: # need to set inScheme
      rdf.add((conc, SKOS.inScheme, defaultcs))

def cleanup_classes(rdf):
  """Remove unnecessary class definitions: definitions of SKOS classes or
     unused classes. If a class is also a skos:Concept or skos:Collection,
     remove the 'classness' of it but leave the Concept/Collection."""
  for t in (OWL.Class, RDFS.Class):
    for cl in rdf.subjects(RDF.type, t):
      # SKOS classes may be safely removed
      if cl.startswith(SKOS):
        debug("removing SKOS class definition: %s" % cl)
        replace_subject(rdf, cl, None)
        continue
      # if there are instances of the class, keep the class def
      if rdf.value(None, RDF.type, cl, any=True) != None: continue
      # if the class is used in a domain/range/equivalentClass definition, keep the class def
      if rdf.value(None, RDFS.domain, cl, any=True) != None: continue
      if rdf.value(None, RDFS.range, cl, any=True) != None: continue
      if rdf.value(None, OWL.equivalentClass, cl, any=True) != None: continue

      # if the class is also a skos:Concept or skos:Collection, only remove its rdf:type
      if (cl, RDF.type, SKOS.Concept) in rdf or (cl, RDF.type, SKOS.Collection) in rdf:
        debug("removing classiness of %s" % cl)
        rdf.remove((cl, RDF.type, t))
      else: # remove it completely
        debug("removing unused class definition: %s" % cl)
        replace_subject(rdf, cl, None)

def cleanup_properties(rdf):
  """Remove unnecessary property definitions: SKOS and DC property definitions and definitions of unused properties."""
  for t in (RDF.Property, OWL.DatatypeProperty, OWL.ObjectProperty):
    for prop in rdf.subjects(RDF.type, t):
      if prop.startswith(SKOS):
        debug("removing SKOS property definition: %s" % prop)
        replace_subject(rdf, prop, None)
        continue
      if prop.startswith(DC):
        debug("removing DC property definition: %s" % prop)
        replace_subject(rdf, prop, None)
        continue
      
      # if there are triples using the property, keep the property def
      if len(list(rdf.subject_objects(prop))) > 0: continue
      
      debug("removing unused property definition: %s" % prop)
      replace_subject(rdf, prop, None)

def find_reachable(rdf, res):
  """Return the set of reachable resources starting from the given resource,
     excluding the seen set of resources. Note that the seen set is modified
     in-place to reflect the ongoing traversal."""

  starttime = time.time()

  # This is almost a non-recursive breadth-first search algorithm, but a set
  # is used as the "open" set instead of a FIFO, and an arbitrary element of
  # the set is searched. This is slightly faster than DFS (using a stack)
  # and much faster than BFS (using a FIFO).
  seen = set()			# used as the "closed" set
  to_search = set([res])	# used as the "open" set
  
  while len(to_search) > 0:
    res = to_search.pop()
    if res in seen: continue
    seen.add(res)
    # res as subject
    for p,o in rdf.predicate_objects(res):
      if isinstance(p, URIRef) and p not in seen:
        to_search.add(p)
      if isinstance(o, URIRef) and o not in seen:
        to_search.add(o)
    # res as predicate
    for s,o in rdf.subject_objects(res):
      if isinstance(s, URIRef) and s not in seen:
        to_search.add(s)
      if isinstance(o, URIRef) and o not in seen:
        to_search.add(o)
    # res as object
    for s,p in rdf.subject_predicates(res):
      if isinstance(s, URIRef) and s not in seen:
        to_search.add(s)
      if isinstance(p, URIRef) and p not in seen:
        to_search.add(p)

  endtime = time.time()
  debug("find_reachable took %f seconds" % (endtime-starttime))
  
  return seen

def cleanup_unreachable(rdf, cs):
  """Remove triples which cannot be reached from the concept scheme by graph traversal."""  
  
  all_subjects = set(rdf.subjects())
  
  debug("total subject resources: %d" % len(all_subjects))
  
  reachable = find_reachable(rdf, cs)
  nonreachable = all_subjects - reachable

  debug("deleting %s non-reachable resources" % len(nonreachable))
  
  for subj in nonreachable:
    delete_uri(rdf, subj)
    

def check_labels(rdf):
  # check that concepts have only one prefLabel per language
  for conc in rdf.subjects(RDF.type, SKOS.Concept):
    prefLabels = {}
    for label in rdf.objects(conc, SKOS.prefLabel):
      lang = label.language
      if lang not in prefLabels:
        prefLabels[lang] = []
      prefLabels[lang].append(label)
    for lang, labels in prefLabels.items():
      if len(labels) > 1:
        shortest = sorted(labels, key=len)[0]
        warn("Concept %s has more than one prefLabel@%s: choosing %s" % \
             (conc, lang, shortest))
        for label in labels:
          if label != shortest:
            rdf.remove((conc, SKOS.prefLabel, label))
            rdf.add((conc, SKOS.altLabel, label))

  # check overlap between disjoint label properties
  for conc,label in find_prop_overlap(rdf, SKOS.prefLabel, SKOS.altLabel):
    warn("Concept %s has '%s'@%s as both prefLabel and altLabel; removing altLabel" % \
         (conc, label, label.language))
    rdf.remove((conc, SKOS.altLabel, label))
  for conc,label in find_prop_overlap(rdf, SKOS.prefLabel, SKOS.hiddenLabel):
    warn("Concept %s has '%s'@%s as both prefLabel and hiddenLabel; removing hiddenLabel" % \
         (conc, label, label.language))
    rdf.remove((conc, SKOS.hiddenLabel, label))
  for conc,label in find_prop_overlap(rdf, SKOS.altLabel, SKOS.hiddenLabel):
    warn("Concept %s has '%s'@%s as both altLabel and hiddenLabel; removing hiddenLabel" % \
         (conc, label, label.language))
    rdf.remove((conc, SKOS.hiddenLabel, label))
  

def check_hierarchy_visit(rdf, node, parent, status):
  if status.get(node) is None:
    status[node] = 1 # entered
    for child in rdf.subjects(SKOS.broader, node):
      check_hierarchy_visit(rdf, child, node, status)
  elif status.get(node) == 1: # has been entered but not yet done
    warn("Hierarchy loop removed at %s -> %s" % (localname(parent), localname(node)))
    rdf.remove((node, SKOS.broader, parent))
    rdf.remove((node, SKOS.broaderTransitive, parent))
    rdf.remove((node, SKOSEXT.broaderGeneric, parent))
    rdf.remove((node, SKOSEXT.broaderPartitive, parent))
    rdf.remove((parent, SKOS.narrower, node))
    rdf.remove((parent, SKOS.narrowerTransitive, node))
  elif status.get(node) == 2: # is completed already
    pass
  status[node] = 2 # set this node as completed

def check_hierarchy(rdf):
  # check for cycles in the skos:broader hierarchy
  # using a recursive depth first search algorithm
  starttime = time.time()

  top_concepts = rdf.subject_objects(SKOS.hasTopConcept)
  for cs,root in top_concepts:
    check_hierarchy_visit(rdf, root, None, status={})

  endtime = time.time()
  
  
  # check overlap between disjoint semantic relations
  # related and broaderTransitive
  for conc1,conc2 in rdf.subject_objects(SKOS.related):
    if conc2 in rdf.transitive_objects(conc1, SKOS.broader):
      warn("Concepts %s and %s connected by both skos:broaderTransitive and skos:related, removing skos:related" % \
           (conc1, conc2))
      rdf.remove((conc1, SKOS.related, conc2))
      rdf.remove((conc2, SKOS.related, conc1))

  debug("check_hierarchy took %f seconds" % (endtime-starttime))
      

def write_output(rdf, filename, fmt, namespaces):
  """Serialize the RDF output to the given file (or - for stdout)."""
  if not fmt:
    # determine output format
    fmt = 'rdfxml' # default
    if filename.endswith('nt'): fmt = 'ntriples'
    if filename.endswith('n3'): fmt = 'turtle'
    if filename.endswith('ttl'): fmt = 'turtle'

  serializer = Serializer(name=fmt)
  for prefix, ns in namespaces.items():
    serializer.set_namespace(prefix, ns)
  
  if filename == '-':
    sys.stdout.write(serializer.serialize_model_to_string(rdf))
  else:
    serializer.serialize_model_to_file(filename, model=rdf)

def skosify(inputfile, namespaces, typemap, literalmap, relationmap, options):
  global debugging
  debugging = options.debug

  starttime = time.time()

  # Stage 1: Read input
  (voc, ns_seen) = read_input(inputfile, options.from_format)
  namespaces.update(ns_seen)
  
  inputtime = time.time()

  # Stage 2: Process
  if options.infer:
    infer_classes(voc)
    infer_properties(voc)

  # find/create concept scheme
  cs = get_concept_scheme(voc)
  if not cs:
    cs = create_concept_scheme(voc, options.namespace)

  # transform concepts, literals and concept relations
  transform_concepts(voc, cs, typemap)
  transform_literals(voc, literalmap)
#  transform_relations(voc, relationmap) 

  # special transforms for labels: whitespace, prefLabel vs altLabel
#  transform_labels(voc)

  # special transforms for collections and aggregate concepts
#  transform_collections(voc)
#  transform_aggregate_concepts(voc, cs, relationmap, options.aggregates)

  # enrichments: broader <-> narrower, related <-> related
#  enrich_relations(voc, options.narrower, options.transitive)

  # clean up unused/unnecessary class/property definitions and unreachable triples
#  cleanup_properties(voc)
#  cleanup_classes(voc)
#  cleanup_unreachable(voc, cs)
  
  # setup inScheme and hasTopConcept
#  setup_concept_scheme(voc, cs)
#  setup_top_concepts(voc)

  # check hierarchy for cycles
#  check_hierarchy(voc)
  
  # check for duplicate labels
#  check_labels(voc)
  

  processtime = time.time()

  # Stage 3: Write output
  
  write_output(voc, options.output, options.to_format, namespaces)
  endtime = time.time()

  debug("reading input file %s took  %d seconds" % (inputfile, inputtime - starttime))
  debug("processing took             %d seconds" % (processtime - inputtime))
  debug("writing output file %s took %d seconds" % (options.output, endtime-processtime))
  debug("total time taken:           %d seconds" % (endtime - starttime))


def get_option_parser(defaults):
  """Create and return an OptionParser with the given defaults"""
  # based on recipe from: http://stackoverflow.com/questions/1880404/using-a-file-to-store-optparse-arguments

  import optparse
  
  # process command line parameters
  # e.g. skosify yso.owl -o yso-skos.rdf
  parser = optparse.OptionParser()
  parser.set_defaults(**defaults)
  parser.add_option('-c', '--config', type='string', help='Read default options and transformation definitions from the given configuration file.')
  parser.add_option('-o', '--output', type='string', help='Output file name. Default is "-" (stdout).')
  parser.add_option('-s', '--namespace', type='string', help='Namespace of vocabulary (usually optional; used to create a ConceptScheme)')
  parser.add_option('-f', '--from-format', type='string', help='Input format. Default is to detect format based on file extension. Possible values: rdfxml, turtle, ntriples...')
  parser.add_option('-F', '--to-format', type='string', help='Output format. Default is to detect format based on file extension. Possible values: rdfxml, turtle, ntriples...')
  parser.add_option('-i', '--infer', action="store_true", help='Perform RDFS subclass/subproperty inference before transforming input.')
  parser.add_option('-I', '--no-infer', dest="infer", action="store_false", help="Don't perform RDFS subclass/subproperty inference before transforming input.")
  parser.add_option('-N', '--narrower', action="store_true", help='Include narrower/narrowerGeneric/narrowerPartitive relationships in the output vocabulary.')
  parser.add_option('-n', '--no-narrower', dest="narrower", action="store_false", help="Don't include narrower/narrowerGeneric/narrowerPartitive relationships in the output vocabulary.")
  parser.add_option('-T', '--transitive', action="store_true", help='Include transitive hierarchy relationships in the output vocabulary.')
  parser.add_option('-t', '--no-transitive', dest="transitive", action="store_false", help="Don't include transitive hierarchy relationships in the output vocabulary.")
  parser.add_option('-A', '--aggregates', action="store_true", help='Keep AggregateConcepts completely in the output vocabulary.')
  parser.add_option('-a', '--no-aggregates', dest="aggregates", action="store_false", help='Remove AggregateConcepts completely from the output vocabulary.')
  parser.add_option('-D', '--debug', action="store_true", help='Show debug output.')
  parser.add_option('-d', '--no-debug', dest="debug", action="store_false", help='Hide debug output.')
  
  return parser

def expand_curielike(namespaces, curie):
  """Expand a CURIE (or a CURIE-like string with a period instead of colon
  as separator) into a Uri. If the provided curie is not a CURIE, return it
  unchanged."""

  if curie == '': return None
  curie = curie.decode('UTF-8')

  if curie.startswith('[') and curie.endswith(']'):
    # decode SafeCURIE
    curie = curie[1:-1]

  if ':' in curie:
    ns, localpart = curie.split(':', 1)
  elif '.' in curie:
    ns, localpart = curie.split('.', 1)
  else:
    return curie

  if ns in namespaces:
    uri = unicode(namespaces[ns]) + localpart
    # for some reason Uri doesn't like calculated unicode objects
    # so encoding to UTF-8 instead (which redland would do anyway)
    return Uri(uri.encode('UTF-8'))
  else:
    warn("Unknown namespace prefix %s" % ns)
    return Uri(curie)

def main():
  """Read command line parameters and make a transform based on them"""

  namespaces = DEFAULT_NAMESPACES
  typemap = {}
  literalmap = {}
  relationmap = {}
  defaults = DEFAULT_OPTIONS
  options, remainingArgs = get_option_parser(defaults).parse_args()

  if options.config is not None:
    # read the supplied configuration file
    import ConfigParser
    cfgparser = ConfigParser.SafeConfigParser()
    cfgparser.optionxform = str # force case-sensitive handling of option names
    cfgparser.read(options.config)

    # parse namespaces from configuration file
    for prefix, uri in cfgparser.items('namespaces'):
      namespaces[prefix] = Uri(uri)
    
    # parse types from configuration file
    for key, val in cfgparser.items('types'):
      typemap[expand_curielike(namespaces, key)] = expand_curielike(namespaces, val)

    # parse literals from configuration file
    for key, val in cfgparser.items('literals'):
      literalmap[expand_curielike(namespaces, key)] = expand_curielike(namespaces, val)

    # parse relations from configuration file
    for key, val in cfgparser.items('relations'):
      relationmap[expand_curielike(namespaces, key)] = expand_curielike(namespaces, val)

    # parse options from configuration file
    for opt, val in cfgparser.items('options'):
      if opt not in defaults:
        warn('Unknown option in configuration file: %s (ignored)' % opt)
        continue
      if defaults[opt] in (True, False): # is a Boolean option
        defaults[opt] = cfgparser.getboolean('options', opt)
      else:
        defaults[opt] = val
    
    # re-initialize and re-run OptionParser using defaults read from configuration file
    options, remainingArgs = get_option_parser(defaults).parse_args()
    

  if remainingArgs:
    inputfile = remainingArgs[0]
  else:
    inputfile = '-'

  skosify(inputfile, namespaces, typemap, literalmap, relationmap, options)
  
  
if __name__ == '__main__':
  main()

