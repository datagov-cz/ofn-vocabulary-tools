from rdflib import XSD, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL, RDFS, SKOS, DCTERMS, TIME
from ofnClasses import ClassType, RPPType, Relationship, Term, TermClass, Trope, VocabularyType, Vocabulary
from datetime import datetime
import traceback

from outputToRDFBase import outputToRDFBase
from outputToRDFRegistry import outputToRDFRegistry

# TODO: Code lists
# TODO: Error handling
# TODO: Input validation
# TODO: check for duplicate values
# TODO: search for terms within file is IRI is not provided


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
        # create IRI if not available
        if len(term.iri) == 0:
            term.getIRI(vocabulary, defaultLanguage)
        # associate with vocabulary
        graph.add((URIRef(term.iri), SKOS.inScheme, vocabularyIRI))
        # Base
        outputToRDFBase(term, graph)
        # RPP
        outputToRDFRegistry(term, graph)
    getRDFoutput(graph, outputFile)
