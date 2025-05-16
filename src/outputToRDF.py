from rdflib import XSD, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL, SKOS, DCTERMS, TIME
from checkVocabulary import checkVocabulary
from ofnClasses import VocabularyType, Vocabulary
from datetime import datetime, timezone

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
    checkVocabulary(vocabulary)
    # Vocabulary
    vocabularyIRI = vocabulary.getIRI(DEFAULT_LANGUAGE)

    # types
    graph.add((URIRef(vocabularyIRI), RDF.type, SKOS.ConceptScheme))
    if (vocabulary.type == VocabularyType.CONCEPTUAL_MODEL):
        graph.add((URIRef(vocabularyIRI), RDF.type, OWL.Ontology))
    # prefLabel
    for lang, name in vocabulary.name.items():
        graph.add((URIRef(vocabularyIRI), SKOS.prefLabel, Literal(name, lang)))
    # description
    for lang, name in vocabulary.description.items():
        graph.add((URIRef(vocabularyIRI),
                  DCTERMS.description, Literal(name, lang)))
    # TODO: creation date (requires NDC module)
    modifiedBNode = BNode()
    graph.add((URIRef(vocabularyIRI), DCTERMS.modified, modifiedBNode))
    graph.add((modifiedBNode, RDF.type, TIME.Instant))
    graph.add((modifiedBNode, TIME.inXSDDateTimeStamp,
              Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTimeStamp)))

    # Terms
    for term in vocabulary.terms:
        termIRI = term.getIRI(vocabulary, DEFAULT_LANGUAGE)
        if not termIRI.startswith(vocabularyIRI):
            continue
        # associate with vocabulary
        graph.add((URIRef(termIRI),
                  SKOS.inScheme, URIRef(vocabularyIRI)))
        # Base
        outputToRDFBase(term, termIRI, graph)
        # RPP
        outputToRDFRegistry(term, term.getIRI(
            vocabulary, DEFAULT_LANGUAGE), graph)
    getRDFoutput(graph, vocabulary, outputFile)
