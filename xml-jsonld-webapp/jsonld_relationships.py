import re
import warnings

from jsonld_properties import (
    HTTPS_REGEX,
    containsCompare,
    readProperty,
    regexWarning,
    sanitizeString,
)
from ofnDistributionBindings import CS, IDENTIFIKATOR, TYP
from xml_processing import ArchimateElement, ParsedXml


def getRelatedDistributionElements(
    parsed_xml: ParsedXml,
    dataset_element: ArchimateElement,
) -> list[ArchimateElement]:
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
        if (
            relationship.source == dataset_element.identifier
            and relationship.target in distribution_by_id
        ):
            related_distribution_ids.add(relationship.target)
        if (
            relationship.target == dataset_element.identifier
            and relationship.source in distribution_by_id
        ):
            related_distribution_ids.add(relationship.source)

    return [
        element
        for element_id, element in distribution_by_id.items()
        if element_id in related_distribution_ids
    ]


def getRelatedElementsByAssociation(
    parsed_xml: ParsedXml,
    dataset_element: ArchimateElement,
) -> list[ArchimateElement]:
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
        and any(
            containsCompare(readProperty(element, TYP), requested_type)
            for requested_type in requested_types
        )
    }
    related_element_ids = set()

    for relationship in model.relationships:
        if relationship.type != "Association":
            continue
        if (
            relationship.source == dataset_element.identifier
            and relationship.target in related_element_by_id
        ):
            related_element_ids.add(relationship.target)
        if (
            relationship.target == dataset_element.identifier
            and relationship.source in related_element_by_id
        ):
            related_element_ids.add(relationship.source)

    return [
        element
        for element_id, element in related_element_by_id.items()
        if element_id in related_element_ids
    ]


def getIRIofTerm(element: ArchimateElement) -> str:
    iri = readProperty(element, IDENTIFIKATOR)
    if isinstance(iri, list):
        iri = iri[0]
    if isinstance(iri, str) and iri:
        if re.fullmatch(HTTPS_REGEX, iri):
            return iri
        regexWarning(element, IDENTIFIKATOR, iri, HTTPS_REGEX)

    czech_names = [name for name in element.names if name.language == CS]
    if not czech_names:
        warnings.warn(
            "Skipping element ID {} because it doesn't have a name in Czech".
            format(element.identifier)
        )
        return ""

    namespace = "https://slovník.gov.cz"
    return "{}/{}".format(
        namespace.rstrip("/"),
        sanitizeString(czech_names[0].value.strip().lower()),
    )
