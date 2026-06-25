from dataclasses import dataclass
import warnings
import re
from xml_processing import ArchimateElement, ArchimateRelationship, ParsedXml
from ofnDistributionBindings import *

# https://www.w3.org/TR/sparql11-query/#rPN_LOCAL
PN_CHARS_U = re.compile(
    "[A-Za-z]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]|[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF]|_", re.U)
PERCENT = re.compile("%([0-9A-Fa-f])([0-9A-Fa-f])", re.U)
PN_LOCAL_ESC = re.compile("\\\\[_~\\.\\-!$&\"'()*+,;=/?#@%]")
PLX = re.compile("({})|({})".format(
    PERCENT.pattern, PN_LOCAL_ESC.pattern), re.I)
PN_CHARS = re.compile(
    "({})|[-0-9]|\u00B7|[\u0300-\u036F]|[\u203F-\u2040]".format(PN_CHARS_U.pattern), re.U)
PN_LOCAL_1 = re.compile(
    "({})|[:0-9]|({})".format(PN_CHARS_U.pattern, PLX.pattern))
PN_LOCAL_2 = re.compile("({})|[.:]|({})".format(
    PN_CHARS.pattern, PLX.pattern))
PN_LOCAL_3 = re.compile("({})|:|({})".format(
    PN_CHARS.pattern, PLX.pattern))
PN_LOCAL = re.compile("({})(({})*({}))?".format(PN_LOCAL_1.pattern,
                                                PN_LOCAL_2.pattern, PN_LOCAL_3.pattern), re.U)


def sanitizeString(string: str) -> str:
    result: str = ""
    for match in PN_LOCAL.finditer(string):
        m = match.group(0)
        result = result.ljust(match.end(0), "-")
        result = result[0:(match.end(0) - len(m))]
        result += m
    result = re.sub("-+$", "", result)
    return result


@dataclass(frozen=True)
class JsonLdFile:
    filename: str | None
    document: dict


def containsCompare(input: str | list[str], target: str) -> bool:
    if type(input) is str:
        return target.lower() in input.lower()
    if type(input) is list:
        boolList: list[bool] = [target.lower() in x.lower() for x in input]
        return any(boolList)
    return False


def createDatasetIRI(name: str) -> str:
    namespace = "https://slovník.gov.cz"
    namespace = re.sub("/$", "", namespace)
    while namespace.endswith("/"):
        namespace = namespace[:-1]
    return "{}/{}".format(namespace,
                          sanitizeString(name.strip().lower()))


def addProperty(key: str, value, element: ArchimateElement | ArchimateRelationship, property=None) -> dict:
    if not property:
        property = key
    if property in element.resolved_properties:
        return {key: value}
    else:
        return {}


def addPropertyHelper(input: str | list[str] | None):
    if type(input) is str:
        return input
    if type(input) is list:
        return input[0]
    return None


def splitProperty(input: str | list[str] | None):
    if type(input) is str:
        return input.split(";")
    if type(input) is list:
        return input
    return None


def getProperty(property: str) -> str:
    return property.replace("_", " ")


def getRelatedDistributionElements(parsed_xml: ParsedXml, dataset_element: ArchimateElement) -> list[ArchimateElement]:
    model = parsed_xml.model
    if not model or not dataset_element.identifier:
        return []

    if not containsCompare(dataset_element.resolved_properties.get(TYP), "datová sada"):
        return []

    distribution_by_id = {
        element.identifier: element
        for element in model.elements
        if element.identifier
        and containsCompare(element.resolved_properties.get(TYP), "distribuce")
    }
    related_distribution_ids = set()

    for relationship in model.relationships:
        if relationship.source == dataset_element.identifier and relationship.target in distribution_by_id:
            related_distribution_ids.add(relationship.target)
        if relationship.target == dataset_element.identifier and relationship.source in distribution_by_id:
            related_distribution_ids.add(relationship.source)

    return [
        element
        for element_id, element in distribution_by_id.items()
        if element_id in related_distribution_ids
    ]


def getRelatedElementsByAssociation(parsed_xml: ParsedXml, dataset_element: ArchimateElement) -> list[ArchimateElement]:
    model = parsed_xml.model
    if not model or not dataset_element.identifier:
        return []

    if not containsCompare(dataset_element.resolved_properties.get(TYP), "datová sada"):
        return []

    requested_types = ["subjekt práva", "objekt práva"]
    related_element_by_id = {
        element.identifier: element
        for element in model.elements
        if element.identifier
        and any(containsCompare(element.resolved_properties.get(TYP), requested_type) for requested_type in requested_types)
    }
    related_element_ids = set()

    for relationship in model.relationships:
        if relationship.type != "Association":
            continue
        if relationship.source == dataset_element.identifier and relationship.target in related_element_by_id:
            related_element_ids.add(relationship.target)
        if relationship.target == dataset_element.identifier and relationship.source in related_element_by_id:
            related_element_ids.add(relationship.source)

    return [
        element
        for element_id, element in related_element_by_id.items()
        if element_id in related_element_ids
    ]


def getIRIofTerm(element: ArchimateElement) -> str:
    ret = ""
    if ret:
        ret = element.resolved_properties.get(IDENTIFIKATOR)
        if isinstance(ret, list):
            ret = ret[0]
        if isinstance(ret, str):
            return ret
        else:
            nameCs = [
                x for x in element.names if x.language and x.language == CS]
            if len(nameCs) == 0:
                warnings.warn(
                    "Skipping element ID {} because it doesn't have a name in Czech".format(element.identifier))
            namespace = "https://slovník.gov.cz"
            namespace = re.sub("/$", "", namespace)
            while namespace.endswith("/"):
                namespace = namespace[:-1]
            ret = "{}/{}".format(namespace,
                                 sanitizeString(nameCs[0].value.strip().lower()))
    return ret


def create_jsonld_files(parsed_xml: ParsedXml) -> list[JsonLdFile]:

    ret: list[JsonLdFile] = []

    model = parsed_xml.model
    if not model:
        raise Exception("Cannot find model in Archimate File")
    else:
        for dataset in model.elements:
            nameCs = [
                x for x in dataset.names if x.language and x.language == CS]
            if len(nameCs) == 0:
                warnings.warn(
                    "Skipping element ID {} because it doesn't have a name in Czech".format(dataset.identifier))
                continue
            elif len(nameCs) > 1:
                warnings.warn(
                    "Warning: element ID {} has multiple Czech names, there should be only one Czech name. The first one found will be used.".format(dataset.identifier))
            if containsCompare(dataset.resolved_properties[TYP], "datová sada"):
                distributions = getRelatedDistributionElements(
                    parsed_xml, dataset)
                distributionJsonLDcontents = []
                relatedTerms = getRelatedElementsByAssociation(
                    parsed_xml, dataset)
                for i, distribution in enumerate(distributions):
                    distributionJsonLDcontents.append({
                        IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}".format(i),
                        TYP: ["Datové rozhraní", "Distribuce"],
                        NAZEV: {x.language: x.value for x in distribution.names},
                        **addProperty(PRISTUPOVE_URL, addPropertyHelper(distribution.resolved_properties.get(PRISTUPOVE_URL)), distribution),
                        **addProperty(PRAVNI_PREDPIS, splitProperty(distribution.resolved_properties.get(PRAVNI_PREDPIS)), distribution),
                        **addProperty(PODMINKY_UZITI, {
                            IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}/specifikace-podmínek-užití".format(i),
                            TYP: ["Specifikace podmínek užití"],
                            **addProperty(AUTORSKE_DILO, addPropertyHelper(distribution.resolved_properties.get(AUTORSKE_DILO)), distribution),
                            **addProperty(AUTOR, {CS: addPropertyHelper(distribution.resolved_properties.get(AUTOR))}, distribution),
                            **addProperty(DATABAZE_JAKO_AUTORSKE_DILO, addPropertyHelper(distribution.resolved_properties.get(DATABAZE_JAKO_AUTORSKE_DILO)), distribution),
                            **addProperty(AUTOR_DATABAZE, {CS: addPropertyHelper(distribution.resolved_properties.get(AUTOR_DATABAZE))}, distribution),
                            **addProperty(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY, addPropertyHelper(distribution.resolved_properties.get(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY)), distribution),
                            **addProperty(OSOBNI_UDAJE, addPropertyHelper(distribution.resolved_properties.get(OSOBNI_UDAJE)), distribution),
                        }, distribution),
                        # **addProperty(SDILI_UDAJ, {CS: addPropertyHelper(distribution.resolved_properties.get(SDILI_UDAJ))}, distribution),
                        **addProperty(PRISTUPOVA_SLUZBA, {
                            IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}/přístupová-služba".format(i),
                            TYP: ["Datová služba"],
                            NAZEV: {x.language: x.value for x in distribution.names},
                        }, distribution),
                        # **addProperty(ODPOVIDAJICI_POJEM, {CS: addPropertyHelper(distribution.resolved_properties.get(ODPOVIDAJICI_POJEM))}, distribution),
                        # **addProperty(ZPUSOB_ZISKANI_SDILENYCH_UDAJU, splitProperty(distribution.resolved_properties.get(ZPUSOB_ZISKANI_SDILENYCH_UDAJU)), distribution),
                        # **addProperty(ZPUSOB_SDILENI_UDAJU, addPropertyHelper(distribution.resolved_properties.get(ZPUSOB_SDILENI_UDAJU)), distribution),
                        # **addProperty(TYP_OBSAHU_SDILENYCH_UDAJU, splitProperty(distribution.resolved_properties.get(TYP_OBSAHU_SDILENYCH_UDAJU)), distribution),
                        **addProperty(SOUBOR_KE_STAZENI, {CS: addPropertyHelper(distribution.resolved_properties.get(SOUBOR_KE_STAZENI))}, distribution),
                        **addProperty(FORMAT, {CS: addPropertyHelper(distribution.resolved_properties.get(FORMAT))}, distribution),
                        **addProperty(TYP_MEDIA, {CS: addPropertyHelper(distribution.resolved_properties.get(TYP_MEDIA))}, distribution),
                        **addProperty(SCHEMA, {CS: addPropertyHelper(distribution.resolved_properties.get(SCHEMA))}, distribution),
                        **addProperty(TYP_MEDIA_KOMPRESE, {CS: addPropertyHelper(distribution.resolved_properties.get(TYP_MEDIA_KOMPRESE))}, distribution),
                        **addProperty(TYP_MEDIA_BALICKU, {CS: addPropertyHelper(distribution.resolved_properties.get(TYP_MEDIA_BALICKU))}, distribution),
                        **addProperty(PRISTUPOVY_BOD, {CS: addPropertyHelper(distribution.resolved_properties.get(PRISTUPOVY_BOD))}, distribution),
                        **addProperty(POPIS_PRISTUPOVEHO_BODU, {CS: addPropertyHelper(distribution.resolved_properties.get(POPIS_PRISTUPOVEHO_BODU))}, distribution),
                    })

                jsonLdContent = {
                    CONTEXT: "https://ofn.gov.cz/dcat-ap-cz-otevřená-data/draft/datová-sada/kontext.jsonld",
                    IRI: createDatasetIRI(nameCs[0].value),
                    TYP: ["Datová sada", "Datová sada SSP"],
                    NAZEV: {x.language: x.value for x in dataset.names},
                    **addProperty(POPIS, {CS: addPropertyHelper(dataset.resolved_properties.get(POPIS))}, dataset),
                    **addProperty(POSKYTOVATEL, addPropertyHelper(dataset.resolved_properties.get(POSKYTOVATEL)), dataset),
                    **addProperty(TEMA, splitProperty(dataset.resolved_properties.get(TEMA)), dataset),
                    **addProperty(PERIODICITA_AKTUALIZACE, addPropertyHelper(dataset.resolved_properties.get(PERIODICITA_AKTUALIZACE)), dataset),
                    **addProperty(KLICOVE_SLOVO, {CS: splitProperty(dataset.resolved_properties.get(KLICOVE_SLOVO))}, dataset),
                    **addProperty(CASOVE_POKRYTI, {
                        TYP: ["Časový interval"],
                        ZACATEK: addPropertyHelper(dataset.resolved_properties.get(CASOVE_POKRYTI_ZACATEK)),
                        KONEC: addPropertyHelper(dataset.resolved_properties.get(CASOVE_POKRYTI_KONEC)),
                    }, dataset),
                    **addProperty(KONTAKTNI_BOD, {
                        TYP: ["Organizace"],
                        JMENO: addPropertyHelper(dataset.resolved_properties.get(KONTAKTNI_BOD_JMENO)),
                        E_MAIL: addPropertyHelper(dataset.resolved_properties.get(KONTAKTNI_BOD_EMAIL)),
                    }, dataset),
                    **addProperty(DOKUMENTACE, addPropertyHelper(dataset.resolved_properties.get(DOKUMENTACE)), dataset),
                    **addProperty(SPECIFIKACE, addPropertyHelper(dataset.resolved_properties.get(SPECIFIKACE)), dataset),
                    **addProperty(KONCEPT_EUROVOC, splitProperty(dataset.resolved_properties.get(KONCEPT_EUROVOC)), dataset),
                    # jak agresivní by mělo hledání pojmů být?
                    **addProperty(TYKA_SE_POJMU, [getIRIofTerm(x) for x in relatedTerms], dataset),
                    **addProperty(JE_ZAHRNUTA_V_ISVS, addPropertyHelper(dataset.resolved_properties.get(JE_ZAHRNUTA_V_ISVS)), dataset),
                    **addProperty(JE_SOUCASTI, addPropertyHelper(dataset.resolved_properties.get(JE_SOUCASTI)), dataset),
                    **addProperty(PRAVNI_PREDPIS, splitProperty(dataset.resolved_properties.get(PRAVNI_PREDPIS)), dataset),
                    **addProperty(DISTRIBUCE, distributionJsonLDcontents, dataset),
                }
                jsonLdFile = JsonLdFile(
                    filename=nameCs[0].value,
                    document=jsonLdContent
                )
                ret.append(jsonLdFile)

        return ret
