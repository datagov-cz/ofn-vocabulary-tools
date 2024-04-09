from rdflib import Graph, URIRef, Literal
from rdflib.namespace import RDF, OWL, RDFS, SKOS, DCTERMS
from ofnClasses import TermType, VocabularyType, Vocabulary, Term

# RDF conversion
graph = Graph()

# Vocabulary
vocabularyIRI = URIRef(
    "https://slovník.gov.cz/{}".format(vocabulary.name[defaultLanguage].strip().lower().replace(" ", "-")))

graph.add((vocabularyIRI, RDF.type, SKOS.ConceptScheme))
if (vocabulary.type == VocabularyType.CONCEPTUAL_MODEL):
    graph.add((vocabularyIRI, RDF.type, OWL.Ontology))
for lang, name in vocabulary.name.items():
    graph.add((vocabularyIRI, SKOS.prefLabel, Literal(name, lang)))
for lang, name in vocabulary.description.items():
    graph.add((vocabularyIRI, DCTERMS.description, Literal(name, lang)))

# Terms
for term in vocabulary.terms:
    termIRI = URIRef("https://slovník.gov.cz/{}/pojem/{}".format(
        vocabulary.name[defaultLanguage].strip().lower().replace(" ", "-"),
        term.name[defaultLanguage].strip().lower().replace(" ", "-")))
    graph.add((termIRI, RDF.type, SKOS.Concept))
    graph.add((termIRI, SKOS.inScheme, vocabularyIRI))
    graph.add((termIRI, DCTERMS.conformsTo, URIRef(term.source)))
    for lang, name in term.name.items():
        graph.add((vocabularyIRI, SKOS.prefLabel, Literal(name, lang)))
    for lang, name in term.description.items():
        graph.add((vocabularyIRI, DCTERMS.description, Literal(name, lang)))

    if term.type is TermType.CLASS or term.type is TermType.OBJECT or term.type is TermType.SUBJECT:
        graph.add((termIRI, RDF.type, OWL.Class))
    if term.type is TermType.OBJECT:
        graph.add((termIRI, RDF.type, URIRef(
            "https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva")))
    if term.type is TermType.SUBJECT:
        graph.add((termIRI, RDF.type, URIRef(
            "https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva")))
    if term.type is TermType.TROPE:
        graph.add((termIRI, RDF.type, OWL.DatatypeProperty))
        graph.add((termIRI, RDFS.domain, URIRef(term.domain)))
        graph.add((termIRI, RDFS.range, URIRef(term.datatype)))
    if term.type is TermType.RELATIONSHIP:
        graph.add((termIRI, RDF.type, OWL.ObjectProperty))
        graph.add((termIRI, RDFS.domain, URIRef(term.domain)))
        graph.add((termIRI, RDFS.range, URIRef(term.range)))

    for broader in term.subClassOf:
        # TODO: term IRIs
        graph.add((termIRI, SKOS.broader, URIRef(broader)))
