import re
import warnings

from jsonld_properties import (
    HTTPS_REGEX,
    containsCompare,
    readProperty,
    regexWarning,
    sanitizeString,
)
from ofnDistributionBindings import CS, IDENTIFIKATOR, METODA_SBIRANI_POJMU, TYP
from xml_processing import ArchimateElement, ArchimateRelationship, ParsedXml


DETAILED = "podrobně"
STANDARD = "standard"
AGGRESSIVE = "agresivně"

CLASS_TYPES = ("typ subjektu", "typ objektu")
PROPERTY_TYPE = "typ vlastnosti"
GENERALIZATION_RELATIONSHIP_TYPES = ("Specialization", "Generalization")


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


def _has_any_type(element: ArchimateElement, requested_types) -> bool:
    return any(
        containsCompare(readProperty(element, TYP), requested_type)
        for requested_type in requested_types
    )


def _collection_method(dataset_element: ArchimateElement) -> str:
    value = readProperty(dataset_element, METODA_SBIRANI_POJMU)
    if isinstance(value, list):
        value = next((item for item in value if item.strip()), None)
    if not isinstance(value, str) or not value.strip():
        return DETAILED

    normalized = value.strip().lower()
    if normalized in (DETAILED, STANDARD, AGGRESSIVE):
        return normalized

    warnings.warn(
        "Unknown value {!r} of property {!r} on dataset element ID {}; "
        "using {!r}.".format(
            value,
            METODA_SBIRANI_POJMU,
            dataset_element.identifier,
            DETAILED,
        )
    )
    return DETAILED


def _directly_associated_ids(model, dataset_id: str) -> set[str]:
    related_ids = set()
    for relationship in model.relationships:
        if relationship.type != "Association":
            continue
        if relationship.source == dataset_id and relationship.target:
            related_ids.add(relationship.target)
        elif relationship.target == dataset_id and relationship.source:
            related_ids.add(relationship.source)
    return related_ids


def _has_name(relationship: ArchimateRelationship) -> bool:
    return any(name.value.strip() for name in relationship.names)


def _is_directed_association(
    relationship: ArchimateRelationship,
) -> bool:
    is_directed = relationship.is_directed
    return (
        relationship.type == "Association"
        and (
            is_directed is True
            or (
                isinstance(is_directed, str)
                and is_directed.strip().lower() == "true"
            )
        )
    )


def _is_term_association(
    relationship: ArchimateRelationship,
    class_ids: set[str],
) -> bool:
    return (
        bool(relationship.identifier)
        and _is_directed_association(relationship)
        and relationship.source in class_ids
        and relationship.target in class_ids
        and _has_name(relationship)
    )


def _other_endpoint(
    relationship: ArchimateRelationship,
    current_id: str,
) -> str | None:
    if relationship.source == current_id:
        return relationship.target
    if relationship.target == current_id:
        return relationship.source
    return None


def _aggressive_neighbor(
    relationship: ArchimateRelationship,
    current_id: str,
    class_ids: set[str],
    property_ids: set[str],
) -> str | None:
    """Return the next term when this relationship is traversable."""
    if _is_directed_association(relationship):
        if (
            relationship.source in class_ids
            and relationship.target in class_ids
            and _has_name(relationship)
        ):
            return _other_endpoint(relationship, current_id)
        return None

    other_id = _other_endpoint(relationship, current_id)
    if not other_id:
        return None

    endpoints = {relationship.source, relationship.target}
    if relationship.type in GENERALIZATION_RELATIONSHIP_TYPES:
        if endpoints <= class_ids or endpoints <= property_ids:
            return other_id
    elif relationship.type == "Composition":
        if (
            endpoints <= class_ids | property_ids
            and endpoints & class_ids
            and endpoints & property_ids
        ):
            return other_id
    return None


def getRelatedTerms(
    parsed_xml: ParsedXml,
    dataset_element: ArchimateElement,
) -> list[ArchimateElement | ArchimateRelationship]:
    """Collect vocabulary terms according to the dataset's chosen strategy."""
    model = parsed_xml.model
    if not model or not dataset_element.identifier:
        return []
    if not containsCompare(readProperty(dataset_element, TYP), "datová sada"):
        return []

    elements_by_id = {
        element.identifier: element
        for element in model.elements
        if element.identifier
    }
    class_ids = {
        element_id
        for element_id, element in elements_by_id.items()
        if _has_any_type(element, CLASS_TYPES)
    }
    property_ids = {
        element_id
        for element_id, element in elements_by_id.items()
        if _has_any_type(element, (PROPERTY_TYPE,))
    }
    term_element_ids = class_ids | property_ids
    term_association_ids = {
        relationship.identifier: relationship
        for relationship in model.relationships
        if _is_term_association(relationship, class_ids)
    }
    direct_ids = _directly_associated_ids(
        model,
        dataset_element.identifier,
    )
    method = _collection_method(dataset_element)

    if method == DETAILED:
        selected_element_ids = direct_ids & term_element_ids
        selected_association_ids = direct_ids & set(term_association_ids)
    elif method == STANDARD:
        selected_class_ids = direct_ids & class_ids
        selected_element_ids = set(selected_class_ids)
        for relationship in model.relationships:
            endpoints = {relationship.source, relationship.target}
            if (
                relationship.type == "Composition"
                and endpoints & selected_class_ids
                and endpoints & property_ids
            ):
                selected_element_ids.update(endpoints & property_ids)
        selected_association_ids = {
            relationship_id
            for relationship_id, relationship in term_association_ids.items()
            if relationship.source in selected_element_ids
            and relationship.target in selected_element_ids
        }
    else:
        selected_element_ids = direct_ids & class_ids
        frontier = list(selected_element_ids)
        traversed = set(selected_element_ids)

        while frontier:
            current_id = frontier.pop()
            for relationship in model.relationships:
                other_id = _aggressive_neighbor(
                    relationship,
                    current_id,
                    class_ids,
                    property_ids,
                )
                if not other_id:
                    continue

                selected_element_ids.add(other_id)
                if other_id not in traversed:
                    traversed.add(other_id)
                    frontier.append(other_id)

        selected_association_ids = {
            relationship_id
            for relationship_id, relationship in term_association_ids.items()
            if relationship.source in selected_element_ids
            and relationship.target in selected_element_ids
        }

    return [
        element
        for element in model.elements
        if element.identifier in selected_element_ids
    ] + [
        relationship
        for relationship in model.relationships
        if relationship.identifier in selected_association_ids
    ]


def getIRIofTerm(
    element: ArchimateElement | ArchimateRelationship,
) -> str:
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
