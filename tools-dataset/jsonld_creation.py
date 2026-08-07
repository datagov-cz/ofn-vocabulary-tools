"""Public entry point for converting parsed ArchiMate models to JSON-LD."""

from dataclasses import dataclass
import logging
import warnings

from jsonld_builders import (
    DistributionDocument,
    build_dataset_document,
    build_distributions,
)
from jsonld_properties import (
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
from jsonld_relationships import (
    getIRIofTerm,
    getRelatedDistributionElements,
    getRelatedTerms,
)
from jsonld_required_fields import (
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
from ofnDistributionBindings import *  # noqa: F403
from xml_processing import ArchimateElement, ArchimateRelationship, ParsedXml


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


def create_jsonld_files(parsed_xml: ParsedXml) -> list[JsonLdFile]:
    model = parsed_xml.model
    if not model:
        raise Exception("Cannot find model in Archimate File")

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
            continue

        dataset_name = czech_names[0].value
        dataset_iri = createDatasetIRI(dataset_name)
        related_terms = getRelatedTerms(parsed_xml, dataset)
        related_term_iris = [
            iri
            for iri in (getIRIofTerm(term) for term in related_terms)
            if iri
        ]
        distributions = build_distributions(
            getRelatedDistributionElements(parsed_xml, dataset),
            dataset_iri,
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

    return jsonld_files
