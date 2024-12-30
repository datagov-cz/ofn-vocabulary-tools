from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef
from src.util.ofnClasses import Relationship, Term, TermClass, Trope
from src.output.outputToRDF import getURIRefOrLiteral, testInputString

# Remember to call AFTER the term's IRI has been initialized!


def outputToRDFBase(term: Term, graph: Graph):
    termIRI = URIRef(term.iri)
    # Basic term info
    graph.add((termIRI, RDF.type, SKOS.Concept))
    # prefLabel
    for lang, name in term.name.items():
        if testInputString(name):
            graph.add((termIRI, SKOS.prefLabel, Literal(name, lang)))
    # altLabel
    for (lang, name) in term.alternateName:
        graph.add((termIRI, SKOS.altLabel, Literal(name, lang)))
    # description
    for lang, name in term.description.items():
        if testInputString(name):
            graph.add((termIRI, DCTERMS.description, Literal(name, lang)))
    # definition
    for lang, name in term.definition.items():
        if testInputString(name):
            graph.add((termIRI, SKOS.definition, Literal(name, lang)))
    # relation
    for relation in term.related:
        if testInputString(relation):
            graph.add((termIRI, DCTERMS.relation,
                       getURIRefOrLiteral(relation)))
    # conformsTo
    if testInputString(term.source):
        graph.add((termIRI, DCTERMS.conformsTo,
                   getURIRefOrLiteral(term.source)))
    # exactMatch
    for equivalent in term.equivalent:
        if testInputString(equivalent):
            graph.add((termIRI, SKOS.exactMatch,
                       getURIRefOrLiteral(equivalent)))
    # broader
    if isinstance(term, Term):
        for broader in term.subClassOf:
            if testInputString(broader):
                graph.add((termIRI, SKOS.broader,
                           getURIRefOrLiteral(broader)))
    # owl:Class (class) and subClassOf
    if isinstance(term, TermClass):
        graph.add((termIRI, RDF.type, OWL.Class))
        for broader in term.subClassOf:
            if testInputString(broader):
                graph.add((termIRI, RDFS.subClassOf,
                           getURIRefOrLiteral(broader)))
    # subPropertyOf (tropes or relationships)
    if isinstance(term, Trope) or isinstance(term, Relationship):
        for broader in term.subClassOf:
            if testInputString(broader):
                graph.add((termIRI, RDFS.subPropertyOf,
                           getURIRefOrLiteral(broader)))
    # datatypeProperty (trope), domain, range (datatype)
    if isinstance(term, Trope):
        graph.add((termIRI, RDF.type, OWL.DatatypeProperty))
        if term.target is not None:
            graph.add(
                (termIRI, RDFS.domain, getURIRefOrLiteral(term.target)))
        if term.datatype is not None:
            graph.add(
                (termIRI, RDFS.range, getURIRefOrLiteral(term.datatype)))
    # Object property (relationship), domain, range
    if isinstance(term, Relationship):
        graph.add((termIRI, RDF.type, OWL.ObjectProperty))
        if term.domain is not None:
            graph.add(
                (termIRI, RDFS.domain, getURIRefOrLiteral(term.domain)))
        if term.range is not None:
            graph.add((termIRI, RDFS.range, getURIRefOrLiteral(term.range)))