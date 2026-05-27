from rdflib import DCTERMS, OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef
from ofnClasses import Relationship, Term, TermClass, Trope, GetValueType, ShareValueType, ContentValueType
from urllib.parse import unquote
from outputUtil import getURIRefOrLiteral, testInputString

# Remember to call AFTER the term's IRI has been initialized!


def outputToRDF360(term: Term, iri: str, graph: Graph):
    termIRI = URIRef(unquote(iri))
    if isinstance(term, Trope):
        if term.getValueType is not None:
            if term.getValueType is GetValueType.BASE_REGISTRY:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-získání-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-získání-údajů/položky/základních-registrů")))
            if term.getValueType is GetValueType.OTHER_AGENDA:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-získání-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-získání-údajů/položky/jiných-agend")))
            if term.getValueType is GetValueType.OWN_AGENDA:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-získání-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-získání-údajů/položky/vlastní")))
            if term.getValueType is GetValueType.OPERATING:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-získání-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-získání-údajů/položky/provozní")))
        if len(term.shareValueType) > 0:
            for svt in term.shareValueType:
                if svt is ShareValueType.PUBLIC:
                    graph.add((termIRI, URIRef(
                        "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-sdílení-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-sdílení-údajů/položky/veřejně-přístupné")))
                if svt is ShareValueType.ON_REQUEST:
                    graph.add((termIRI, URIRef(
                        "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-sdílení-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-sdílení-údajů/položky/poskytované-na-žádost")))
                if svt is ShareValueType.FOR_AGENDAS:
                    graph.add((termIRI, URIRef(
                        "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-sdílení-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-sdílení-údajů/položky/zpřístupňované-pro-výkon-agendy")))
                if svt is ShareValueType.PRIVATE:
                    graph.add((termIRI, URIRef(
                        "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-sdílení-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/způsoby-sdílení-údajů/položky/nesdílené")))
        if term.contentValueType is not None:
            if term.getValueType is ContentValueType.IDENTIFICATION:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-typ-obsahu-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/typy-obsahu-údajů/položky/identifikační")))
            if term.getValueType is ContentValueType.RECORD:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-typ-obsahu-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/typy-obsahu-údajů/položky/evidenční")))
            if term.getValueType is ContentValueType.STATISTICAL:
                graph.add((termIRI, URIRef(
                    "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-typ-obsahu-údaje"), URIRef("https://data.dia.gov.cz/zdroj/číselníky/typy-obsahu-údajů/položky/statistické")))
