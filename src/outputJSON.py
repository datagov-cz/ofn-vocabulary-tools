import json
from ofnClasses import *
import urllib.request
import urllib.parse
from rdflib import RDFS


def getReference(uri: str) -> object:
    with urllib.request.urlopen(urllib.parse.quote(uri)) as schema:
        return schema


def getJSONLDfromVocabulary(vocabulary: Vocabulary) -> json:
    output = {}
    output["@context"] = "https://ofn.gov.cz/slovníky/draft/kontexty/slovníky.jsonld"
    output["iri"] = vocabulary.getIRI()
    vocTypes = ["Slovník", "Tezaurus"]
    if vocabulary.type == VocabularyType.CONCEPTUAL_MODEL:
        vocTypes.append("Konceptuální model")
    output["typ"] = vocTypes
    output["název"] = vocabulary.name
    if DEFAULT_LANGUAGE in vocabulary.description and vocabulary.description[DEFAULT_LANGUAGE]:
        output["popis"] = vocabulary.description
    terms = []
    for term in vocabulary.terms:
        outputTerm = {}
        # iri
        outputTerm["iri"] = term.getIRI(vocabulary, DEFAULT_LANGUAGE)
        # typ
        termTypes = ["Pojem"]
        termSubClassOf = [
            x for x in term.subClassOf if x and len(x) != 0 and x is not None]
        if isinstance(term, TermClass):
            termTypes.append("Třída")
            if len(termSubClassOf) > 0:
                outputTerm["nadřazená-třída"] = termSubClassOf
            if term.type == ClassType.OBJECT:
                termTypes.append("Typ objektu práva")
            elif term.type == ClassType.SUBJECT:
                termTypes.append("Typ subjektu práva")
            if term.ais:
                outputTerm["agendový-informační-systém"] = term.ais
            if term.agenda:
                outputTerm["agenda"] = term.agenda
        elif isinstance(term, Relationship):
            termTypes.append("Vztah")
            outputTerm["definiční-obor"] = term.domain
            outputTerm["obor-hodnot"] = term.range
            if len(termSubClassOf) > 0:
                outputTerm["nadřazený-vztah"] = termSubClassOf
        elif isinstance(term, Trope):
            termTypes.append("Vlastnost")
            outputTerm["definiční-obor"] = term.target
            outputTerm["obor-hodnot"] = term.datatype if term.datatype else RDFS.Literal
            if len(termSubClassOf) > 0:
                outputTerm["nadřazená-vlastnost"] = termSubClassOf
        if term.rppType == RPPType.PRIVATE:
            termTypes.append("Neveřejný údaj")
        elif term.rppType == RPPType.PUBLIC:
            termTypes.append("Veřejný údaj")
        outputTerm["typ"] = termTypes
        outputTerm["název"] = term.name
        if DEFAULT_LANGUAGE in term.definition and term.definition[DEFAULT_LANGUAGE]:
            outputTerm["definice"] = {x: term.definition[x]
                                      for x in term.definition if term.definition[x] is not None}
        if DEFAULT_LANGUAGE in term.description and term.description[DEFAULT_LANGUAGE]:
            outputTerm["popis"] = {x: term.description[x]
                                   for x in term.description if term.description[x] is not None}
        if term.equivalent:
            outputTerm["ekvivalentní-pojem"] = [
                x for x in term.equivalent if x and len(x) != 0 and x is not None]
        if term.related:
            outputTerm["související-ustanovení-právního-předpisu"] = [
                x for x in term.related if x and len(x) != 0 and x is not None]
        if term.source:
            outputTerm["definující-ustanovení-právního-předpisu"] = [term.source]
        if term.sharedInPPDF:
            outputTerm["je-sdílen-v-ppdf"] = term.sharedInPPDF
        if term.rppPrivateTypeSource:
            outputTerm["ustanovení-dokládající-neveřejnost-údaje"] = [term.rppPrivateTypeSource]
        terms.append(outputTerm)
    output["pojmy"] = terms
    return output
