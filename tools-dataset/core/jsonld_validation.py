import logging
import os
from collections.abc import Iterable
from urllib.parse import quote

import requests
from jsonschema import validators

from .jsonld_properties import (
    DATE_REGEX,
    EMAIL_REGEX,
    EUROVOC_REGEX,
    FORMAT_REGEX,
    FREQUENCY_REGEX,
    HTTPS_REGEX,
    ISVS_REGEX,
    MEDIA_TYPE_REGEX,
    PROVIDER_REGEX,
    THEME_REGEX,
)
from .jsonld_required_fields import find_missing_required_entries


DEFAULT_SCHEMA_URL = (
    "https://ofn.gov.cz/dcat-ap-cz-datov%c3%a1-rozhran%c3%ad/"
    "2026-09-23/datov%C3%A1-sada/sch%C3%A9ma.json"
)
SCHEMA_URL = os.environ.get("JSON_SCHEMA_URL", DEFAULT_SCHEMA_URL).strip()
logger = logging.getLogger(__name__)

SCHEMA_URI_KEYWORDS = {"$id", "$ref", "$schema"}
URI_REFERENCE_SAFE_CHARACTERS = ":/?#[]@!$&'()*+,;=%"

EXPECTED_VALUES = {
    HTTPS_REGEX: "an HTTPS URL",
    DATE_REGEX: "a date in YYYY-MM-DD format",
    EMAIL_REGEX: "an email address",
    FORMAT_REGEX: "a file format code",
    MEDIA_TYPE_REGEX: "an IANA media type",
    PROVIDER_REGEX: "an OVM identifier such as ovm:12345678",
    THEME_REGEX: "a data theme code",
    FREQUENCY_REGEX: "an update frequency code",
    EUROVOC_REGEX: "a EuroVoc code",
    ISVS_REGEX: "an ISVS identifier",
}


class JsonLdValidationError(Exception):
    """All human-readable errors found while validating generated JSON-LD."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def _normalize_schema_uri_references(value):
    """Encode non-ASCII characters in JSON Schema URI-reference keywords.

    Some published OFN schemas use IRIs (for example ``schéma.json``) in
    ``$id``.  JSON Schema declares these values as URI references, and strict
    format-checking backends reject the otherwise harmless Unicode characters.
    """
    if isinstance(value, dict):
        for key, item in value.items():
            if key in SCHEMA_URI_KEYWORDS and isinstance(item, str):
                value[key] = quote(
                    item, safe=URI_REFERENCE_SAFE_CHARACTERS)
            else:
                _normalize_schema_uri_references(item)
    elif isinstance(value, list):
        for item in value:
            _normalize_schema_uri_references(item)
    return value


def load_schema():
    if not SCHEMA_URL:
        logger.info("JSON-LD schema validation is disabled")
        return None

    logger.debug("Loading JSON schema from %s", SCHEMA_URL)
    response = requests.get(SCHEMA_URL, timeout=15)
    response.raise_for_status()
    schema = _normalize_schema_uri_references(response.json())
    logger.debug("JSON schema loaded successfully")
    return schema


def _entry_at_path(document: dict, path: Iterable) -> dict:
    """Return the deepest enclosing entry which has an IRI."""
    current = document
    entry = document if isinstance(
        document, dict) and "iri" in document else None
    for part in path:
        try:
            current = current[part]
        except (KeyError, IndexError, TypeError):
            break
        if isinstance(current, dict) and "iri" in current:
            entry = current
    return entry or document


def _entry_name(entry: dict) -> str | None:
    names = entry.get("název")
    if isinstance(names, str) and names.strip():
        return names.strip()
    if isinstance(names, dict):
        preferred = names.get("cs")
        if isinstance(preferred, str) and preferred.strip():
            return preferred.strip()
        return next(
            (value.strip() for value in names.values()
             if isinstance(value, str) and value.strip()),
            None,
        )
    return None


def _entry_description(entry: dict) -> str:
    iri = entry.get("iri") if isinstance(entry, dict) else None
    iri_text = str(iri) if iri else "<missing>"
    name = _entry_name(entry) if isinstance(entry, dict) else None
    if name:
        return "entry with name {!r} and IRI {!r}".format(name, iri_text)
    return "entry with IRI {!r}".format(iri_text)


def _field_path(error) -> str:
    return ".".join(str(part) for part in error.absolute_path) or "the entry"


def _human_readable_errors(error, document: dict) -> list[str]:
    entry = _entry_at_path(document, error.absolute_path)
    description = _entry_description(entry)

    if error.validator == "required":
        missing = [
            field for field in error.validator_value if field not in error.instance]
        return [
            "Mandatory attribute {!r} is missing from {}.".format(
                field, description)
            for field in missing
        ]
    if error.validator == "type":
        return [
            "Attribute {!r} has an invalid value in {}; expected type {}."
            .format(_field_path(error), description, error.validator_value)
        ]
    if error.validator == "format":
        return [
            "Attribute {!r} has an invalid {} format in {}."
            .format(_field_path(error), error.validator_value, description)
        ]
    if error.validator == "enum":
        return [
            "Attribute {!r} has a value outside the allowed set in {}."
            .format(_field_path(error), description)
        ]
    return [
        "Attribute {!r} is invalid in {}: {}."
        .format(_field_path(error), description, error.message.rstrip("."))
    ]


def _validate_document(document: dict, schema: dict) -> list[str]:
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(
        schema, format_checker=validator_class.FORMAT_CHECKER)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    return [
        message
        for error in errors
        for message in _human_readable_errors(error, document)
    ]


def _validate_required_fields(
    document: dict,
    malformed_fields: set[tuple[int, str]] | None = None,
) -> list[str]:
    return [
        "Mandatory attribute {!r} is missing from {}."
        .format(field, _entry_description(entry))
        for field, entry in find_missing_required_entries(document)
        if (id(entry), field) not in (malformed_fields or set())
    ]


def _validate_malformed_properties(jsonld_file) -> tuple[list[str], set[tuple[int, str]]]:
    errors = []
    malformed_fields = set()
    entries = getattr(jsonld_file, "source_entries", None) or {}
    for problem in getattr(jsonld_file, "malformed_properties", ()):
        entry = entries.get(problem.element_id, jsonld_file.document)
        if problem.attribute.startswith("přístupová služba - "):
            entry = entry.get("přístupová_služba", entry)
        elif problem.attribute.startswith("podmínky užití - "):
            entry = entry.get("podmínky_užití", entry)

        field = problem.attribute.rsplit(" - ", 1)[-1].replace(" ", "_")
        if field == "email":
            field = "e-mail"
        malformed_fields.add((id(entry), field))
        expected = EXPECTED_VALUES.get(
            problem.expected_pattern, "a valid value")
        errors.append(
            "Attribute {!r} has malformed value {!r} in {}; expected {}."
            .format(problem.attribute, problem.value, _entry_description(entry), expected)
        )
    return list(dict.fromkeys(errors)), malformed_fields


def _raise_validation_errors(errors: list[str]):
    if not errors:
        return
    for error in errors:
        logger.error("JSON-LD validation error: %s", error)
    raise JsonLdValidationError(errors)


def validate_jsonld(document):
    _raise_validation_errors(_validate_required_fields(document))
    schema = load_schema()
    if schema is None:
        return

    errors = _validate_document(document, schema)
    _raise_validation_errors(errors)
    logger.debug("JSON-LD document passed schema validation")


def validate_jsonld_files(jsonld_files):
    local_errors = []
    for jsonld_file in jsonld_files:
        malformed_errors, malformed_fields = _validate_malformed_properties(
            jsonld_file)
        local_errors.extend(malformed_errors)
        local_errors.extend(_validate_required_fields(
            jsonld_file.document, malformed_fields,
        ))
    _raise_validation_errors(local_errors)

    if not SCHEMA_URL:
        logger.info("Skipping validation for %d JSON-LD document(s)",
                    len(jsonld_files))
        return

    logger.info("Validating %d JSON-LD document(s)", len(jsonld_files))
    schema = load_schema()
    errors = []
    for index, jsonld_file in enumerate(jsonld_files, start=1):
        logger.debug(
            "Validating JSON-LD document %d (%r)",
            index,
            jsonld_file.filename or "unnamed",
        )
        errors.extend(_validate_document(jsonld_file.document, schema))

    _raise_validation_errors(errors)
    logger.info("All JSON-LD documents passed schema validation")
