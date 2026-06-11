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


def create_jsonld_files(parsed_xml: ParsedXml) -> list[JsonLdFile]:

    ret: list[JsonLdFile] = []

    model = parsed_xml.model
    if not model:
        # TODO
        pass
    else:
        for element in model.elements:
            nameCs = [
                x for x in element.names if x.language and x.language == CS]
            if len(nameCs) == 0:
                warnings.warn(
                    "Skipping element ID {} because it doesn't have a name in Czech".format(element.identifier))
                continue
            elif len(nameCs) > 1:
                warnings.warn(
                    "Warning: element ID {} has multiple Czech names, there should be only one Czech name. The first one found will be used.".format(element.identifier))
            if containsCompare(element.resolved_properties[TYP], "datová sada"):
                jsonLdContent = {
                    CONTEXT: "https://ofn.gov.cz/dcat-ap-cz-otevřená-data/draft/datová-sada/kontext.jsonld",
                    IRI: createDatasetIRI(nameCs[0].value),
                    TYP: ["Datová sada", "Datová sada SSP"],
                    NAZEV: {x.language: x.value for x in element.names},
                    **addProperty(POPIS, {CS: addPropertyHelper(element.resolved_properties.get(POPIS))}, element),
                    **addProperty(POSKYTOVATEL, addPropertyHelper(element.resolved_properties.get(POSKYTOVATEL)), element),
                    **addProperty(TEMA, splitProperty(element.resolved_properties.get(TEMA)), element),
                    **addProperty(PERIODICITA_AKTUALIZACE, addPropertyHelper(element.resolved_properties.get(PERIODICITA_AKTUALIZACE)), element),
                    **addProperty(KLICOVE_SLOVO, {CS: splitProperty(element.resolved_properties.get(KLICOVE_SLOVO))}, element),
                    **addProperty(CASOVE_POKRYTI, {
                        TYP: ["Časový interval"],
                        ZACATEK: addPropertyHelper(element.resolved_properties.get(CASOVE_POKRYTI_ZACATEK)),
                        KONEC: addPropertyHelper(element.resolved_properties.get(CASOVE_POKRYTI_KONEC)),
                    }, element),
                    **addProperty(KONTAKTNI_BOD, {
                        TYP: ["Organizace"],
                        JMENO: addPropertyHelper(element.resolved_properties.get(KONTAKTNI_BOD_JMENO)),
                        E_MAIL: addPropertyHelper(element.resolved_properties.get(KONTAKTNI_BOD_EMAIL)),
                    }, element),
                    **addProperty(DOKUMENTACE, addPropertyHelper(element.resolved_properties.get(DOKUMENTACE)), element),
                    **addProperty(SPECIFIKACE, {CS: addPropertyHelper(element.resolved_properties.get(SPECIFIKACE))}, element),
                    **addProperty(KONCEPT_EUROVOC, {CS: addPropertyHelper(element.resolved_properties.get(KONCEPT_EUROVOC))}, element),
                    **addProperty(TYKA_SE_POJMU, {CS: addPropertyHelper(element.resolved_properties.get(TYKA_SE_POJMU))}, element),
                    **addProperty(JE_ZAHRNUTA_V_ISVS, {CS: addPropertyHelper(element.resolved_properties.get(JE_ZAHRNUTA_V_ISVS))}, element),
                    **addProperty(JE_SOUCASTI, {CS: addPropertyHelper(element.resolved_properties.get(JE_SOUCASTI))}, element),
                    **addProperty(PRAVNI_PREDPIS, {CS: addPropertyHelper(element.resolved_properties.get(PRAVNI_PREDPIS))}, element),
                    **addProperty(DISTRIBUCE, {CS: addPropertyHelper(element.resolved_properties.get(DISTRIBUCE))}, element),
                    **addProperty(PRISTUPOVE_URL, {CS: addPropertyHelper(element.resolved_properties.get(PRISTUPOVE_URL))}, element),
                    **addProperty(PODMINKY_UZITI, {CS: addPropertyHelper(element.resolved_properties.get(PODMINKY_UZITI))}, element),
                    **addProperty(AUTORSKE_DILO, {CS: addPropertyHelper(element.resolved_properties.get(AUTORSKE_DILO))}, element),
                    **addProperty(AUTOR, {CS: addPropertyHelper(element.resolved_properties.get(AUTOR))}, element),
                    **addProperty(DATABAZE_JAKO_AUTORSKE_DILO, {CS: addPropertyHelper(element.resolved_properties.get(DATABAZE_JAKO_AUTORSKE_DILO))}, element),
                    **addProperty(AUTOR_DATABAZE, {CS: addPropertyHelper(element.resolved_properties.get(AUTOR_DATABAZE))}, element),
                    **addProperty(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY, {CS: addPropertyHelper(element.resolved_properties.get(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY))}, element),
                    **addProperty(OSOBNI_UDAJE, {CS: addPropertyHelper(element.resolved_properties.get(OSOBNI_UDAJE))}, element),
                    **addProperty(SDILI_UDAJ, {CS: addPropertyHelper(element.resolved_properties.get(SDILI_UDAJ))}, element),
                    **addProperty(ODPOVIDAJICI_POJEM, {CS: addPropertyHelper(element.resolved_properties.get(ODPOVIDAJICI_POJEM))}, element),
                    **addProperty(ZPUSOB_ZISKANI_SDILENYCH_UDAJU, {CS: addPropertyHelper(element.resolved_properties.get(ZPUSOB_ZISKANI_SDILENYCH_UDAJU))}, element),
                    **addProperty(ZPUSOB_SDILENI_UDAJU, {CS: addPropertyHelper(element.resolved_properties.get(ZPUSOB_SDILENI_UDAJU))}, element),
                    **addProperty(TYP_OBSAHU_SDILENYCH_UDAJU, {CS: addPropertyHelper(element.resolved_properties.get(TYP_OBSAHU_SDILENYCH_UDAJU))}, element),
                    **addProperty(SOUBOR_KE_STAZENI, {CS: addPropertyHelper(element.resolved_properties.get(SOUBOR_KE_STAZENI))}, element),
                    **addProperty(FORMAT, {CS: addPropertyHelper(element.resolved_properties.get(FORMAT))}, element),
                    **addProperty(TYP_MEDIA, {CS: addPropertyHelper(element.resolved_properties.get(TYP_MEDIA))}, element),
                    **addProperty(SCHEMA, {CS: addPropertyHelper(element.resolved_properties.get(SCHEMA))}, element),
                    **addProperty(TYP_MEDIA_KOMPRESE, {CS: addPropertyHelper(element.resolved_properties.get(TYP_MEDIA_KOMPRESE))}, element),
                    **addProperty(TYP_MEDIA_BALICKU, {CS: addPropertyHelper(element.resolved_properties.get(TYP_MEDIA_BALICKU))}, element),
                    **addProperty(PRISTUPOVA_SLUZBA, {CS: addPropertyHelper(element.resolved_properties.get(PRISTUPOVA_SLUZBA))}, element),
                    **addProperty(PRISTUPOVY_BOD, {CS: addPropertyHelper(element.resolved_properties.get(PRISTUPOVY_BOD))}, element),
                    **addProperty(POPIS_PRISTUPOVEHO_BODU, {CS: addPropertyHelper(element.resolved_properties.get(POPIS_PRISTUPOVEHO_BODU))}, element),
                }
                jsonLdFile = JsonLdFile(
                    filename=nameCs[0].value,
                    document=jsonLdContent
                )
                ret.append(jsonLdFile)

    return ret
