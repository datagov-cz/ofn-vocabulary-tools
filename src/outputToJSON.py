import json
from ofnClasses import *
import urllib.request
import urllib.parse
import re
import rfc3987
from jsonschema import validate


def validateJSON(voc: object):
    with open("schéma.json", "r", encoding="utf-8") as schemaFile:
        schema = json.load(schemaFile)
        validate(voc, schema=schema)


def getReference(uri: str) -> object:
    with urllib.request.urlopen(urllib.parse.quote(uri)) as schema:
        return schema


def processSource(input: str, outputTerm: dict, main: bool):
    eliPart = re.search("eli\/cz\/sb\/.*$", input)
    control = re.search("^https\:\/\/.*\/eli\/cz\/sb\/.*$", input)
    if control and eliPart:
        eliSource = "https://opendata.eselpoint.cz/esel-esb/{}".format(
            eliPart.group())
        if main:
            if "definující-ustanovení-právního-předpisu" not in outputTerm:
                outputTerm["definující-ustanovení-právního-předpisu"] = []
            outputTerm["definující-ustanovení-právního-předpisu"].append(
                eliSource)
        else:
            if "související-ustanovení-právního-předpisu" not in outputTerm:
                outputTerm["související-ustanovení-právního-předpisu"] = []
            outputTerm["související-ustanovení-právního-předpisu"].append(
                eliSource)
    else:
        do = {"typ": "Digitální objekt"}
        if rfc3987.match(input, rule="IRI"):
            do["url"] = urllib.parse.unquote(input)
        else:
            do["název"] = {"cs": input}
        if main:
            if "definující-nelegislativní-zdroj" not in outputTerm:
                outputTerm["definující-nelegislativní-zdroj"] = []
            outputTerm["definující-nelegislativní-zdroj"].append(do)
        else:
            if "související-nelegislativní-zdroj" not in outputTerm:
                outputTerm["související-nelegislativní-zdroj"] = []
            outputTerm["související-nelegislativní-zdroj"].append(do)


def getJSONLDfromVocabulary(vocabulary: Vocabulary) -> object:
    output = {}
    output["@context"] = "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
    # output["@context"] = "https://ofn.gov.cz/slovníky/draft/kontexty/slovníky.jsonld"
    output["iri"] = vocabulary.getIRI()
    vocTypes = ["Slovník", "Tezaurus"]
    if vocabulary.type == VocabularyType.CONCEPTUAL_MODEL:
        vocTypes.append("Konceptuální model")
    output["typ"] = vocTypes
    output["název"] = vocabulary.name
    if DEFAULT_LANGUAGE in vocabulary.description and vocabulary.description[DEFAULT_LANGUAGE]:
        output["popis"] = vocabulary.description
    terms = []
    prevTerm = ""
    for term in sorted(vocabulary.terms,
                       key=lambda x: x._iri):
        outputTerm = {}
        # iri
        outputTerm["iri"] = term.getIRI(vocabulary, DEFAULT_LANGUAGE)
        if prevTerm == outputTerm["iri"]:
            print("Pojem {} je duplicitní!".format(
                term.name[DEFAULT_LANGUAGE]))
        if not outputTerm["iri"].startswith(output["iri"]):
            continue
        if term.name[DEFAULT_LANGUAGE] in ["Objekt", "Subjekt", "Vlastnost"]:
            continue
        prevTerm = outputTerm["iri"]
        # typ
        termTypes = ["Pojem", "Koncept"]
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
            outputTerm["obor-hodnot"] = term.datatype
            if len(termSubClassOf) > 0:
                outputTerm["nadřazená-vlastnost"] = termSubClassOf
        if term.rppType == RPPType.PRIVATE:
            termTypes.append("Neveřejný údaj")
            if isinstance(term, Trope) and not term.rppPrivateTypeSource:
                print(
                    "Neveřejný údaj {} nemá ustanovení dokládající neveřejnost.".format(prevTerm))
        elif term.rppType == RPPType.PUBLIC:
            termTypes.append("Veřejný údaj")
        outputTerm["typ"] = termTypes
        outputTerm["název"] = term.name
        altNames: dict[str, list[str]] = {}
        for l, v in term.alternateName:
            if l not in altNames:
                altNames[l] = []
            altNames[l].append(v)
        if len(altNames) > 0:
            outputTerm["alternativní-název"] = altNames
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
            for x in [x for x in term.related if x and len(x) != 0 and x is not None]:
                processSource(x, outputTerm, False)
        if term.source:
            for x in [x for x in term.source if x and len(x) != 0 and x is not None]:
                processSource(x, outputTerm, True)
        if term.sharedInPPDF is not None:
            outputTerm["je-sdílen-v-ppdf"] = term.sharedInPPDF
        if term.rppPrivateTypeSource:
            outputTerm["ustanovení-dokládající-neveřejnost-údaje"] = [term.rppPrivateTypeSource]
        if term.getValueType is not None:
            if term.getValueType is GetValueType.BASE_REGISTRY:
                outputTerm["způsob-získání-údaje"] = "způsoby-získání:základních-registrů"
            if term.getValueType is GetValueType.OTHER_AGENDA:
                outputTerm["způsob-získání-údaje"] = "způsoby-získání:jiných-agend"
            if term.getValueType is GetValueType.OWN_AGENDA:
                outputTerm["způsob-získání-údaje"] = "způsoby-získání:vlastní"
            if term.getValueType is GetValueType.OPERATING:
                outputTerm["způsob-získání-údaje"] = "způsoby-získání:provozní"
        if len(term.shareValueType) > 0:
            outputTermSVT = []
            for svt in term.shareValueType:
                if svt is ShareValueType.PUBLIC:
                    outputTermSVT.append(
                        "způsoby-sdílení:veřejně-přístupné")
                if svt is ShareValueType.ON_REQUEST:
                    outputTermSVT.append(
                        "způsoby-sdílení:poskytované-na-žádost")
                if svt is ShareValueType.FOR_AGENDAS:
                    outputTermSVT.append(
                        "způsoby-sdílení:zpřístupňované-pro-výkon-agendy")
                if svt is ShareValueType.PRIVATE:
                    outputTermSVT.append(
                        "způsoby-sdílení:nesdílené")
            outputTerm["způsoby-sdílení-údaje"] = outputTermSVT
        if term.contentValueType is not None:
            if term.contentValueType is ContentValueType.IDENTIFICATION:
                outputTerm["typ-obsahu-údaje"] = "typy-obsahu:identifikační"
            if term.contentValueType is ContentValueType.RECORD:
                outputTerm["typ-obsahu-údaje"] = "typy-obsahu:evidenční"
            if term.contentValueType is ContentValueType.STATISTICAL:
                outputTerm["typ-obsahu-údaje"] = "typy-obsahu:statistické"
        terms.append(outputTerm)
    termIRIs = []
    for x in terms:
        if x["iri"] in termIRIs:
            raise Exception
        else:
            termIRIs.append(x["iri"])
    output["pojmy"] = terms
    validateJSON(output)
    return output
