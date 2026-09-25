from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef, BNode
from ofnClasses import Relationship, Term, TermClass, Trope
from urllib.parse import unquote
from outputUtil import getURIRefOrLiteral, testInputString
import rfc3987
import re

# Remember to call AFTER the term's IRI has been initialized!


def processSource(input: str, termIRI: URIRef, graph: Graph, main: bool):
    eliPart = re.search("eli\/cz\/sb\/.*$", input)
    control = re.search("^https\:\/\/.*\/eli\/cz\/sb\/.*$", input)
    if control and eliPart:
        eliSource = "https://opendata.eselpoint.cz/esel-esb/{}".format(
            eliPart.group())
        if main:
            graph.add((termIRI, DCTERMS.conformsTo, URIRef(eliSource)))
            graph.add((termIRI, URIRef(
                "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/definující-ustanovení"), URIRef(eliSource)))
        else:
            graph.add((termIRI, DCTERMS.relation, URIRef(eliSource)))
            graph.add((termIRI, URIRef(
                "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/související-ustanovení"), URIRef(eliSource)))
    else:
        bn = BNode()
        graph.add((bn, RDF.type, URIRef(
            "https://slovník.gov.cz/generický/digitální-objekty/pojem/digitální-objekt")))
        if rfc3987.match(input, rule="IRI"):
            graph.add((bn, URIRef("http://schema.org/url"),
                      URIRef(unquote(input))))
        else:
            graph.add((bn, DCTERMS.title, Literal(input)))
        if main:
            graph.add((termIRI, URIRef(
                "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/definující-nelegislativní-zdroj"), bn))
        else:
            graph.add((termIRI, URIRef(
                "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/související-nelegislativní-zdroj"), bn))


def outputToRDFBase(term: Term, iri: str, graph: Graph):
    termIRI = URIRef(unquote(iri))
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
            processSource(relation, termIRI, graph, False)
    # conformsTo
    for source in term.source:
        if testInputString(source):
            processSource(source, termIRI, graph, True)
    # exactMatch
    for equivalent in term.equivalent:
        if testInputString(equivalent):
            graph.add((termIRI, SKOS.exactMatch,
                       getURIRefOrLiteral(equivalent)))

    # owl:Class (class) and subClassOf
    if isinstance(term, TermClass):
        graph.add((termIRI, RDF.type, OWL.Class))
        for broader in term.subClassOf:
            if testInputString(broader):
                graph.add((termIRI, RDFS.subClassOf,
                           getURIRefOrLiteral(broader)))
    # subPropertyOf (tropes or relationships)
    elif isinstance(term, Trope) or isinstance(term, Relationship):
        for broader in term.subClassOf:
            if testInputString(broader):
                graph.add((termIRI, RDFS.subPropertyOf,
                           getURIRefOrLiteral(broader)))
    # broader
    elif isinstance(term, Term):
        for broader in term.subClassOf:
            if testInputString(broader):
                graph.add((termIRI, SKOS.broader,
                           getURIRefOrLiteral(broader)))
    # datatypeProperty (trope), domain, range (datatype)
    if isinstance(term, Trope):
        graph.add((termIRI, RDF.type, OWL.DatatypeProperty))
        if len(term.target) > 0:
            graph.add(
                (termIRI, RDFS.domain, getURIRefOrLiteral(term.target)))
        if term.datatype is not None and len(term.datatype) > 0:
            graph.add(
                (termIRI, RDFS.range, getURIRefOrLiteral(term.datatype)))
        else:
            graph.add(
                (termIRI, RDFS.range, getURIRefOrLiteral(RDFS.Literal)))
    # Object property (relationship), domain, range
    if isinstance(term, Relationship):
        graph.add((termIRI, RDF.type, OWL.ObjectProperty))
        if term.domain is not None:
            graph.add(
                (termIRI, RDFS.domain, getURIRefOrLiteral(term.domain)))
        if term.range is not None:
            graph.add((termIRI, RDFS.range, getURIRefOrLiteral(term.range)))
