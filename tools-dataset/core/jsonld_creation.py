"""Public entry point for converting parsed ArchiMate models to JSON-LD."""

from dataclasses import dataclass
import logging
import warnings

from .jsonld_builders import (
    DistributionDocument,
    build_dataset_document,
    build_distributions,
)
from .jsonld_properties import (
    DATE_REGEX,
    EMAIL_REGEX,
    EUROVOC_REGEX,
    FORMAT_REGEX,
    FREQUENCY_REGEX,
    HTTPS_REGEX,
    ISVS_REGEX,
    MEDIA_TYPE_REGEX,
    PN_CHARS,
    PN_CHARS_U,
    PN_LOCAL,
    PN_LOCAL_1,
    PN_LOCAL_2,
    PN_LOCAL_3,
    PN_LOCAL_ESC,
    PERCENT,
    PLX,
    PROVIDER_REGEX,
    THEME_REGEX,
    addEmailProperty,
    addNonEmptyProperty,
    addPrefixedProperty,
    addProperty,
    addPropertyHelper,
    addRegexProperty,
    containsCompare,
    createDatasetIRI,
    getProperty,
    getSubproperty,
    readProperty,
    regexFilterValue,
    regexWarning,
    sanitizeString,
    splitProperty,
)
from .jsonld_relationships import (
    getIRIofTerm,
    getRelatedDistributionElements,
    getRelatedTerms,
)
from .jsonld_required_fields import (
    ACCESS_SERVICE_REQUIRED_FIELDS,
    CONTACT_POINT_REQUIRED_FIELDS,
    DATASET_REQUIRED_FIELDS,
    DOWNLOAD_DISTRIBUTION_REQUIRED_FIELDS,
    SERVICE_DISTRIBUTION_REQUIRED_FIELDS,
    find_missing_required_fields,
    missingRequiredFields,
)
# These bindings were historically available from this module through a
# wildcard import. Keep re-exporting them for compatibility with callers.
from .ofn_distribution_bindings import *  # noqa: F403
from .xml_processing import ArchimateElement, ArchimateRelationship, ParsedXml


logger = logging.getLogger(__name__)

# Preserve the private names introduced by the original single-file refactor.
_DistributionDocument = DistributionDocument
_build_dataset_document = build_dataset_document
_build_distributions = build_distributions
_find_missing_required_fields = find_missing_required_fields


@dataclass(frozen=True)
class JsonLdFile:
    filename: str | None
    document: dict


def _czech_names(element: ArchimateElement):
    return [
        name
        for name in element.names
        if name.language and name.language == CS  # noqa: F405
    ]


def _log_element_properties(element_kind, element):
    for property_name, value in sorted(element.resolved_properties.items()):
        logger.debug(
            "Property found for %s element ID %r: %r=%r",
            element_kind,
            element.identifier,
            property_name,
            value,
        )


def create_jsonld_files(parsed_xml: ParsedXml) -> list[JsonLdFile]:
    model = parsed_xml.model
    if not model:
        logger.error(
            "Cannot create JSON-LD: no supported model found under XML root %s",
            parsed_xml.root_element_name,
        )
        raise Exception("Cannot find model in Archimate File")

    logger.info(
        "Creating JSON-LD from %s model with %d element(s)",
        parsed_xml.source_format,
        len(model.elements),
    )
    jsonld_files = []
    for dataset in model.elements:
        czech_names = _czech_names(dataset)
        if not czech_names:
            warnings.warn(
                "Skipping element ID {} because it doesn't have a name in "
                "Czech".format(dataset.identifier)
            )
            continue
        if len(czech_names) > 1:
            warnings.warn(
                "Warning: element ID {} has multiple Czech names, there "
                "should be only one Czech name. The first one found will be "
                "used.".format(dataset.identifier)
            )

        if not containsCompare(readProperty(dataset, TYP), "datová sada"):  # noqa: F405
            logger.debug("Skipping non-dataset element ID %s", dataset.identifier)
            continue

        dataset_name = czech_names[0].value
        logger.info(
            "Found dataset element ID %r named %r with type %r",
            dataset.identifier,
            dataset_name,
            readProperty(dataset, TYP),
        )
        _log_element_properties("dataset", dataset)
        dataset_iri = createDatasetIRI(dataset_name)
        logger.info(
            "Generated dataset IRI %r for dataset element ID %r",
            dataset_iri,
            dataset.identifier,
        )
        related_terms = getRelatedTerms(parsed_xml, dataset)
        related_term_iris = [
            iri
            for iri in (getIRIofTerm(term, model) for term in related_terms)
            if iri
        ]
        distribution_elements = getRelatedDistributionElements(
            parsed_xml,
            dataset,
        )
        distributions = build_distributions(
            distribution_elements,
            dataset_iri,
        )
        logger.debug(
            "Dataset element ID %s has %d related term(s) and %d valid "
            "distribution(s)",
            dataset.identifier,
            len(related_term_iris),
            len(distributions),
        )
        document = build_dataset_document(
            dataset,
            dataset_iri,
            related_term_iris,
            distributions,
        )

        missing_fields = find_missing_required_fields(
            document,
            distributions,
        )
        if missing_fields:
            logger.error(
                "Generated JSON-LD for dataset element ID %s is missing "
                "required fields: %s",
                dataset.identifier,
                ", ".join(missing_fields),
            )

        jsonld_files.append(JsonLdFile(
            filename=dataset_name,
            document=document,
        ))

    if not jsonld_files:
        logger.warning("No dataset JSON-LD documents were generated")
    else:
        logger.info("Created %d JSON-LD document(s)", len(jsonld_files))

    return jsonld_files
