from rdflib import XSD, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL, RDFS, SKOS, DCTERMS, TIME
from ofnClasses import ClassType, RPPType, Relationship, Term, TermClass, Trope, VocabularyType, Vocabulary
from datetime import datetime
import traceback

# TODO: Better IRI generation (PN_LOCAL)
# TODO: Code lists
# TODO: Error handling
# TODO: Input validation
# TODO: check for duplicate values
# TODO: search for terms within file is IRI is not provided
# TODO: Write to file


def getRDFoutput(graph: Graph, outputLocation: str):
    with open(outputLocation, "w", encoding="utf-8") as outputFile:
        format: str = outputLocation[len(outputLocation) - 3:]
        outputFile.write(graph.serialize(format=format))


def testInputString(string: str) -> bool:
    return string is not None and string.strip() != ""


def getURIRefOrLiteral(string: str):
    result = URIRef(string)
    try:
        result.n3()
        return result
    except Exception:
        print(traceback.format_exc())
        return Literal(string)


def convertToRDF(vocabulary: Vocabulary, defaultLanguage: str, outputFile: str):
    graph = Graph()

    # Vocabulary
    vocabularyIRI = URIRef(vocabulary.getIRI(defaultLanguage))

    # types
    graph.add((vocabularyIRI, RDF.type, SKOS.ConceptScheme))
    if (vocabulary.type == VocabularyType.CONCEPTUAL_MODEL):
        graph.add((vocabularyIRI, RDF.type, OWL.Ontology))
    # prefLabel
    for lang, name in vocabulary.name.items():
        graph.add((vocabularyIRI, SKOS.prefLabel, Literal(name, lang)))
    # description
    for lang, name in vocabulary.description.items():
        graph.add((vocabularyIRI, DCTERMS.description, Literal(name, lang)))
    # TODO: creation date
    modifiedBNode = BNode()
    graph.add((vocabularyIRI, DCTERMS.modified, modifiedBNode))
    graph.add((modifiedBNode, RDF.type, TIME.Instant))
    graph.add((modifiedBNode, TIME.inXSDDateTimeStamp,
              Literal(datetime.now().isoformat(), datatype=XSD.dateTimeStamp)))

    # Terms
    for term in vocabulary.terms:
        term.getIRI(vocabulary, defaultLanguage)

        termIRI = URIRef(term.iri)
        # Basic term info
        graph.add((termIRI, RDF.type, SKOS.Concept))
        graph.add((termIRI, SKOS.inScheme, vocabularyIRI))
        # prefLabel
        for lang, name in term.name.items():
            if testInputString(name):
                graph.add((termIRI, SKOS.prefLabel, Literal(name, lang)))
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
        # shared in PPDF
        if term.sharedInPPDF is not None:
            graph.add((termIRI, URIRef("https://slovník.gov.cz/agendový/104/pojem/je-sdílen-v-propojeném-datovém-fondu"), Literal(
                term.sharedInPPDF, datatype=XSD.boolean)))

        # term types (& broader)
        if isinstance(term, Term):
            for broader in term.subClassOf:
                if testInputString(broader):
                    graph.add((termIRI, SKOS.broader,
                              getURIRefOrLiteral(broader)))
        if isinstance(term, TermClass):
            graph.add((termIRI, RDF.type, OWL.Class))
            if testInputString(term.ais):
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais"), getURIRefOrLiteral(term.ais)))
            if testInputString(term.agenda):
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy"), getURIRefOrLiteral(term.agenda)))
            for broader in term.subClassOf:
                if testInputString(broader):
                    graph.add((termIRI, RDFS.subClassOf,
                              getURIRefOrLiteral(broader)))
        if isinstance(term, TermClass) and term.type is ClassType.OBJECT:
            graph.add((termIRI, RDF.type, URIRef(
                "https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva")))
        if isinstance(term, TermClass) and term.type is ClassType.SUBJECT:
            graph.add((termIRI, RDF.type, URIRef(
                "https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva")))
        if isinstance(term, Trope) or isinstance(term, Relationship):
            for broader in term.subClassOf:
                if testInputString(broader):
                    graph.add((termIRI, RDFS.subPropertyOf,
                              getURIRefOrLiteral(broader)))
        if isinstance(term, Trope):
            graph.add((termIRI, RDF.type, OWL.DatatypeProperty))
            if term.target is not None:
                graph.add(
                    (termIRI, RDFS.domain, getURIRefOrLiteral(term.target)))
            if term.datatype is not None:
                graph.add(
                    (termIRI, RDFS.range, getURIRefOrLiteral(term.datatype)))
        if isinstance(term, Relationship):
            graph.add((termIRI, RDF.type, OWL.ObjectProperty))
            if term.domain is not None:
                graph.add(
                    (termIRI, RDFS.domain, getURIRefOrLiteral(term.domain)))
            if term.range is not None:
                graph.add((termIRI, RDFS.range, getURIRefOrLiteral(term.range)))

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

    getRDFoutput(graph, outputFile)
