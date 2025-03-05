from rdflib import XSD, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL, SKOS, DCTERMS, TIME
from ofnClasses import VocabularyType, Vocabulary
from datetime import datetime

from outputToRDFBase import outputToRDFBase
from outputToRDFRegistry import outputToRDFRegistry
from outputUtil import getRDFoutput
from preprocessOutput import preprocessVocabulary

# TODO: Code lists
# TODO: Error handling
# TODO: Input validation
# TODO: check for duplicate values
# TODO: search for terms within file is IRI is not provided


def convertToRDF(vocabulary: Vocabulary, DEFAULT_LANGUAGE: str, outputFile: str):
    graph = Graph()
    vocabulary = preprocessVocabulary(vocabulary)
    # Vocabulary
    vocabularyIRI = URIRef(vocabulary.getIRI(DEFAULT_LANGUAGE))

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
        # associate with vocabulary
        graph.add((URIRef(term.getIRI(vocabulary, DEFAULT_LANGUAGE)),
                  SKOS.inScheme, vocabularyIRI))
        # Base
        outputToRDFBase(term, term.getIRI(vocabulary, DEFAULT_LANGUAGE), graph)
        # RPP
        outputToRDFRegistry(term, term.getIRI(
            vocabulary, DEFAULT_LANGUAGE), graph)
    getRDFoutput(graph, vocabulary, outputFile)
