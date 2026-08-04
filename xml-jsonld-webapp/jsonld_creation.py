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
HTTPS_REGEX = r"^https://.*$"
FORMAT_REGEX = r"^formáty:.*$"
MEDIA_TYPE_REGEX = r"^mediaTypes:.*$"
PROVIDER_REGEX = r"^ovm:[^/]+$"
THEME_REGEX = r"^témata:.*$"
FREQUENCY_REGEX = r"^frekvence:.*$"
EUROVOC_REGEX = r"^euroVoc:.*$"
ISVS_REGEX = r"^isvs:[^/]+$"
DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


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
    if getProperty(property) in element.resolved_properties:
        return {key: value}
    else:
        return {}


def regexWarning(element: ArchimateElement | ArchimateRelationship, property: str, value, regex: str):
    warnings.warn(
        "Skipping property {} of element ID {} because value {!r} doesn't satisfy regex {}".format(
            property,
            element.identifier,
            value,
            regex,
        )
    )


def regexFilterValue(value, regex: str, element: ArchimateElement | ArchimateRelationship, property: str):
    if isinstance(value, str):
        if re.fullmatch(regex, value):
            return value
        regexWarning(element, property, value, regex)
        return None

    if isinstance(value, list):
        filtered = [
            item
            for item in (
                regexFilterValue(item, regex, element, property)
                for item in value
            )
            if item is not None
        ]
        return filtered if filtered else None

    if isinstance(value, dict):
        filtered = {
            key: filtered_value
            for key, filtered_value in (
                (key, regexFilterValue(item, regex, element, property))
                for key, item in value.items()
            )
            if filtered_value is not None
        }
        return filtered if filtered else None

    regexWarning(element, property, value, regex)
    return None


def addRegexProperty(key: str, value, regex: str, element: ArchimateElement | ArchimateRelationship, property=None) -> dict:
    if not property:
        property = key
    if getProperty(property) not in element.resolved_properties:
        return {}

    filtered_value = regexFilterValue(value, regex, element, property)
    if filtered_value is None:
        return {}

    return {key: filtered_value}


def addPropertyHelper(input: str | list[str] | None):
    if type(input) is str:
        return input
    if type(input) is list:
        return input[0]
    return None


def splitProperty(input: str | list[str] | None):
    if type(input) is str:
        return [item.strip() for item in input.split(";") if item.strip()]
    if type(input) is list:
        return [item.strip() for item in input if item.strip()]
    return None


def getProperty(property: str) -> str:
    return property.replace("_", " ")


def readProperty(element: ArchimateElement | ArchimateRelationship, property: str):
    return element.resolved_properties.get(getProperty(property))


def getRelatedDistributionElements(parsed_xml: ParsedXml, dataset_element: ArchimateElement) -> list[ArchimateElement]:
    model = parsed_xml.model
    if not model or not dataset_element.identifier:
        return []

    if not containsCompare(readProperty(dataset_element, TYP), "datová sada"):
        return []

    distribution_by_id = {
        element.identifier: element
        for element in model.elements
        if element.identifier
        and containsCompare(readProperty(element, TYP), "distribuce")
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

    if not containsCompare(readProperty(dataset_element, TYP), "datová sada"):
        return []

    requested_types = ["typ subjektu", "typ objektu"]
    related_element_by_id = {
        element.identifier: element
        for element in model.elements
        if element.identifier
        and any(containsCompare(readProperty(element, TYP), requested_type) for requested_type in requested_types)
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
        ret = readProperty(element, IDENTIFIKATOR)
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
            if containsCompare(readProperty(dataset, TYP), "datová sada"):
                distributions = getRelatedDistributionElements(
                    parsed_xml, dataset)
                distributionJsonLDcontents = []
                relatedTerms = getRelatedElementsByAssociation(
                    parsed_xml, dataset)
                for i, distribution in enumerate(distributions):
                    usageTerms = {
                        IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}/specifikace-podmínek-užití".format(i),
                        TYP: ["Specifikace podmínek užití"],
                        # IRI. Satisfies regex ^https://.*$
                        **addRegexProperty(AUTORSKE_DILO, addPropertyHelper(readProperty(distribution, AUTORSKE_DILO)), HTTPS_REGEX, distribution),
                        # Czech string.
                        **addProperty(AUTOR, {CS: addPropertyHelper(readProperty(distribution, AUTOR))}, distribution),
                        # IRI. Satisfies regex ^https://.*$
                        **addRegexProperty(DATABAZE_JAKO_AUTORSKE_DILO, addPropertyHelper(readProperty(distribution, DATABAZE_JAKO_AUTORSKE_DILO)), HTTPS_REGEX, distribution),
                        # Czech string.
                        **addProperty(AUTOR_DATABAZE, {CS: addPropertyHelper(readProperty(distribution, AUTOR_DATABAZE))}, distribution),
                        # IRI. Satisfies regex ^https://.*$
                        **addRegexProperty(DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY, addPropertyHelper(readProperty(distribution, DATABAZE_CHRANENA_ZVLASTNIMI_PRAVY)), HTTPS_REGEX, distribution),
                        # IRI. Satisfies regex ^https://.*$
                        **addRegexProperty(OSOBNI_UDAJE, addPropertyHelper(readProperty(distribution, OSOBNI_UDAJE)), HTTPS_REGEX, distribution),
                    }
                    if containsCompare(readProperty(distribution, TYP), "distribuce - soubor ke stažení"):
                        distributionJsonLDcontents.append({
                            IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}".format(i),
                            TYP: ["Datové rozhraní", "Distribuce"],
                            NAZEV: {x.language: x.value for x in distribution.names},
                            # URL. Satisfies regex ^https://.*$
                            **addRegexProperty(PRISTUPOVE_URL, addPropertyHelper(readProperty(distribution, PRISTUPOVE_URL)), HTTPS_REGEX, distribution),
                            # Strings separated by ; that satisfy regex ^https://.*$
                            **addRegexProperty(PRAVNI_PREDPIS, splitProperty(readProperty(distribution, PRAVNI_PREDPIS)), HTTPS_REGEX, distribution),
                            **addProperty(PODMINKY_UZITI, usageTerms, distribution),
                            # URL. Satisfies regex ^https://.*$
                            **addRegexProperty(SOUBOR_KE_STAZENI, {CS: addPropertyHelper(readProperty(distribution, SOUBOR_KE_STAZENI))}, HTTPS_REGEX, distribution),
                            # String. Satisfies regex ^formáty:.*$
                            **addRegexProperty(FORMAT, {CS: addPropertyHelper(readProperty(distribution, FORMAT))}, FORMAT_REGEX, distribution),
                            # String. Satisfies regex ^mediaTypes:.*$
                            **addRegexProperty(TYP_MEDIA, {CS: addPropertyHelper(readProperty(distribution, TYP_MEDIA))}, MEDIA_TYPE_REGEX, distribution),
                            # URL. Satisfies regex ^https://.*$
                            **addRegexProperty(SCHEMA, {CS: addPropertyHelper(readProperty(distribution, SCHEMA))}, HTTPS_REGEX, distribution),
                            # String. Satisfies regex ^mediaTypes:.*$
                            **addRegexProperty(TYP_MEDIA_KOMPRESE, {CS: addPropertyHelper(readProperty(distribution, TYP_MEDIA_KOMPRESE))}, MEDIA_TYPE_REGEX, distribution),
                            # String. Satisfies regex ^mediaTypes:.*$
                            **addRegexProperty(TYP_MEDIA_BALICKU, {CS: addPropertyHelper(readProperty(distribution, TYP_MEDIA_BALICKU))}, MEDIA_TYPE_REGEX, distribution),
                        })
                    elif containsCompare(readProperty(distribution, TYP), "distribuce - datová služba"):
                        distributionJsonLDcontents.append({
                            IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}".format(i),
                            TYP: ["Datové rozhraní", "Distribuce"],
                            NAZEV: {x.language: x.value for x in distribution.names},
                            # URL. Satisfies regex ^https://.*$
                            **addRegexProperty(PRISTUPOVE_URL, addPropertyHelper(readProperty(distribution, PRISTUPOVE_URL)), HTTPS_REGEX, distribution),
                            # Strings separated by ; that satisfy regex ^https://.*$
                            **addRegexProperty(PRAVNI_PREDPIS, splitProperty(readProperty(distribution, PRAVNI_PREDPIS)), HTTPS_REGEX, distribution),
                            **addProperty(PODMINKY_UZITI, usageTerms, distribution),
                            **addProperty(PRISTUPOVA_SLUZBA, {
                                IRI: createDatasetIRI(nameCs[0].value) + "/distribuce/{}/přístupová-služba".format(i),
                                TYP: ["Datová služba"],
                                NAZEV: {x.language: x.value for x in distribution.names},
                                **addProperty(PRISTUPOVY_BOD, {CS: addPropertyHelper(readProperty(distribution, PRISTUPOVY_BOD))}, distribution),
                                **addProperty(POPIS_PRISTUPOVEHO_BODU, {CS: addPropertyHelper(readProperty(distribution, POPIS_PRISTUPOVEHO_BODU))}, distribution),
                                # Strings separated by ; that satisfy regex ^https://.*$
                                **addRegexProperty(PRAVNI_PREDPIS, splitProperty(readProperty(distribution, PRAVNI_PREDPIS)), HTTPS_REGEX, distribution),
                                # URL. Satisfies regex ^https://.*$
                                **addRegexProperty(SPECIFIKACE, addPropertyHelper(readProperty(distribution, SPECIFIKACE)), HTTPS_REGEX, distribution),
                                # URL. Satisfies regex ^https://.*$
                                **addRegexProperty(DOKUMENTACE, addPropertyHelper(readProperty(distribution, DOKUMENTACE)), HTTPS_REGEX, distribution),
                            }, distribution),
                        })
                    else:
                        warnings.warn(
                            "Skipping distribution of element ID {} because it doesn't specify the exact distribution type".format(distribution.identifier))

                jsonLdContent = {
                    CONTEXT: "https://ofn.gov.cz/dcat-ap-cz-otevřená-data/draft/datová-sada/kontext.jsonld",
                    # IRI identifier of the dataset created from the element name.
                    IRI: createDatasetIRI(nameCs[0].value),
                    TYP: ["Datová sada", "Datová sada SSP"],
                    # String in Czech. Required.
                    NAZEV: {x.language: x.value for x in dataset.names},
                    # Text in Czech. Required
                    **addProperty(POPIS, {CS: addPropertyHelper(readProperty(dataset, POPIS))}, dataset),
                    # String that satisfies regex ^ovm:[^/]+$
                    **addRegexProperty(POSKYTOVATEL, addPropertyHelper(readProperty(dataset, POSKYTOVATEL)), PROVIDER_REGEX, dataset),
                    # Strings separated by ; that satisfy regex ^témata:.*$
                    **addRegexProperty(TEMA, splitProperty(readProperty(dataset, TEMA)), THEME_REGEX, dataset),
                    # String that satisfies regex ^frekvence:.*$
                    **addRegexProperty(PERIODICITA_AKTUALIZACE, addPropertyHelper(readProperty(dataset, PERIODICITA_AKTUALIZACE)), FREQUENCY_REGEX, dataset),
                    # Strings in Czech separated by ;
                    **addProperty(KLICOVE_SLOVO, {CS: splitProperty(readProperty(dataset, KLICOVE_SLOVO))}, dataset),
                    **addProperty(CASOVE_POKRYTI, {
                        TYP: ["Časový interval"],
                        # Date in format yyyy-MM-dd.
                        **addRegexProperty(ZACATEK, addPropertyHelper(readProperty(dataset, CASOVE_POKRYTI_ZACATEK)), DATE_REGEX, dataset, CASOVE_POKRYTI_ZACATEK),
                        # Date in format yyyy-MM-dd.
                        **addRegexProperty(KONEC, addPropertyHelper(readProperty(dataset, CASOVE_POKRYTI_KONEC)), DATE_REGEX, dataset, CASOVE_POKRYTI_KONEC),
                    }, dataset),
                    **addProperty(KONTAKTNI_BOD, {
                        TYP: ["Organizace"],
                        # Name.
                        JMENO: addPropertyHelper(readProperty(dataset, KONTAKTNI_BOD_JMENO)),
                        # Email address
                        **addRegexProperty(E_MAIL, addPropertyHelper(readProperty(dataset, KONTAKTNI_BOD_EMAIL)), EMAIL_REGEX, dataset, KONTAKTNI_BOD_EMAIL),
                    }, dataset),
                    # URL. Satisfies regex ^https://.*$
                    **addRegexProperty(DOKUMENTACE, addPropertyHelper(readProperty(dataset, DOKUMENTACE)), HTTPS_REGEX, dataset),
                    # URL. Satisfies regex ^https://.*$
                    **addRegexProperty(SPECIFIKACE, addPropertyHelper(readProperty(dataset, SPECIFIKACE)), HTTPS_REGEX, dataset),
                    # Strings separated by ; that satisfy regex ^euroVoc:.*$
                    **addRegexProperty(KONCEPT_EUROVOC, splitProperty(readProperty(dataset, KONCEPT_EUROVOC)), EUROVOC_REGEX, dataset),
                    # jak agresivní by mělo hledání pojmů být?
                    **addProperty(TYKA_SE_POJMU, [getIRIofTerm(x) for x in relatedTerms], dataset),
                    # String that satisfies regex ^isvs:[^/]+$
                    **addRegexProperty(JE_ZAHRNUTA_V_ISVS, addPropertyHelper(readProperty(dataset, JE_ZAHRNUTA_V_ISVS)), ISVS_REGEX, dataset),
                    # Strings separated by ; that satisfy regex ^https://.*$
                    **addRegexProperty(JE_SOUCASTI, splitProperty(readProperty(dataset, JE_SOUCASTI)), HTTPS_REGEX, dataset),
                    # Strings separated by ; that satisfy regex ^https://.*$
                    **addRegexProperty(PRAVNI_PREDPIS, splitProperty(readProperty(dataset, PRAVNI_PREDPIS)), HTTPS_REGEX, dataset),
                    **addProperty(DISTRIBUCE, distributionJsonLDcontents, dataset),
                }
                jsonLdFile = JsonLdFile(
                    filename=nameCs[0].value,
                    document=jsonLdContent
                )
                ret.append(jsonLdFile)

        return ret
