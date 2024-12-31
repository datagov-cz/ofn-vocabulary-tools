from rdflib import RDF, XSD, Graph, Literal, URIRef
from ofnClasses import ClassType, Term, TermClass, RPPType
from outputUtil import getURIRefOrLiteral, testInputString

# Remember to call AFTER the term's IRI has been initialized!


def outputToRDFRegistry(term: Term, graph: Graph):
    termIRI = URIRef(term.iri)
    # shared in PPDF
    if term.sharedInPPDF is not None:
        graph.add((termIRI, URIRef("https://slovník.gov.cz/agendový/104/pojem/je-sdílen-v-propojeném-datovém-fondu"), Literal(
            term.sharedInPPDF, datatype=XSD.boolean)))
    if isinstance(term, TermClass) and term.type is ClassType.OBJECT:
        graph.add((termIRI, RDF.type, URIRef(
            "https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva")))
    if isinstance(term, TermClass) and term.type is ClassType.SUBJECT:
        graph.add((termIRI, RDF.type, URIRef(
            "https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva")))
    if isinstance(term, TermClass):
        if testInputString(term.ais):
            graph.add((termIRI, URIRef(
                "https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais"), getURIRefOrLiteral(term.ais)))
        if testInputString(term.agenda):
            graph.add((termIRI, URIRef(
                "https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy"), getURIRefOrLiteral(term.agenda)))
    # RPP public/private types
    if term.rppType is not None:
        if term.rppType is RPPType.PUBLIC:
            graph.add((termIRI, RDF.type, URIRef(
                "https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/veřejný-údaj")))
        if term.rppType is RPPType.PRIVATE and term.rppPrivateTypeSource is not None:
            graph.add((termIRI, RDF.type, URIRef(
                "https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/neveřejný-údaj")))
            graph.add((termIRI, RDF.type, getURIRefOrLiteral(
                term.rppPrivateTypeSource)))
