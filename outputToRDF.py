from rdflib import XSD, Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF, OWL, RDFS, SKOS, DCTERMS, TIME
from ofnClasses import ClassType, RPPType, Relationship, Term, TermClass, Trope, VocabularyType, Vocabulary
from datetime import datetime

# TODO: Better IRI generation (priority,PN_LOCAL)
# TODO: Code lists
# TODO: Error handling
# TODO: Input validation

# TODO: Write to file


def getRDFoutput(graph: Graph):
    with open("output.ttl", "w", encoding="utf-8") as outputFile:
        outputFile.write(graph.serialize(format="ttl"))


def convertToRDF(vocabulary: Vocabulary, defaultLanguage: str):
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
            graph.add((termIRI, SKOS.prefLabel, Literal(name, lang)))
        # description
        for lang, name in term.description.items():
            graph.add((termIRI, DCTERMS.description, Literal(name, lang)))
        # definition
        for lang, name in term.definition.items():
            graph.add((termIRI, DCTERMS.definition, Literal(name, lang)))
        # relation
        for relation in term.related:
            graph.add((termIRI, DCTERMS.relation, URIRef(relation)))
        # conformsTo
        if term.source is not None:
            graph.add((termIRI, DCTERMS.conformsTo, URIRef(term.source)))
        # exactMatch
        for equivalent in term.equivalent:
            graph.add((termIRI, SKOS.exactMatch, URIRef(equivalent)))
        # shared in PPDF
        if term.sharedInPPDF is not None:
            graph.add((termIRI, URIRef("https://slovník.gov.cz/agendový/104/pojem/je-sdílen-v-propojeném-datovém-fondu"), Literal(
                term.sharedInPPDF, datatype=XSD.boolean)))

        # term types (& broader)
        if isinstance(term, Term):
            for broader in term.subClassOf:
                graph.add((termIRI, SKOS.broader, URIRef(broader)))
        if isinstance(term, TermClass):
            graph.add((termIRI, RDF.type, OWL.Class))
            if term.ais is not None:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais"), URIRef(term.ais)))
            if term.agenda is not None:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy"), URIRef(term.agenda)))
            for broader in term.subClassOf:
                graph.add((termIRI, RDFS.subClassOf, URIRef(broader)))
        if isinstance(term, TermClass) and term.type is ClassType.OBJECT:
            graph.add((termIRI, RDF.type, URIRef(
                "https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva")))
        if isinstance(term, TermClass) and term.type is ClassType.SUBJECT:
            graph.add((termIRI, RDF.type, URIRef(
                "https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva")))
        if isinstance(term, Trope) or isinstance(term, Relationship):
            for broader in term.subClassOf:
                graph.add((termIRI, RDFS.subPropertyOf, URIRef(broader)))
        if isinstance(term, Trope):
            graph.add((termIRI, RDF.type, OWL.DatatypeProperty))
            if term.target is not None:
                graph.add((termIRI, RDFS.domain, URIRef(term.target)))
            if term.datatype is not None:
                graph.add((termIRI, RDFS.range, URIRef(term.datatype)))
        if isinstance(term, Relationship):
            graph.add((termIRI, RDF.type, OWL.ObjectProperty))
            if term.domain is not None:
                graph.add((termIRI, RDFS.domain, URIRef(term.domain)))
            if term.range is not None:
                graph.add((termIRI, RDFS.range, URIRef(term.range)))

        # RPP public/private types
        if term.rppType is not None:
            if term.rppType is RPPType.PUBLIC:
                graph.add((termIRI, RDF.type, URIRef(
                    "https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/veřejný-údaj")))
            if term.rppType is RPPType.PRIVATE and term.rppPrivateTypeSource is not None:
                graph.add((termIRI, RDF.type, URIRef(
                    "https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/neveřejný-údaj")))
                graph.add((termIRI, RDF.type, URIRef(
                    term.rppPrivateTypeSource)))

        getRDFoutput(graph)
