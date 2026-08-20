import logging
import os

import requests
from jsonschema import validate


DEFAULT_SCHEMA_URL = (
    "https://ofn.gov.cz/dcat-ap-cz-datov%c3%a1-rozhran%c3%ad/"
    "draft/datov%C3%A1-sada/sch%C3%A9ma.json"
)
SCHEMA_URL = os.environ.get("JSON_SCHEMA_URL", DEFAULT_SCHEMA_URL).strip()
logger = logging.getLogger(__name__)


def load_schema():
    if not SCHEMA_URL:
        logger.info("JSON-LD schema validation is disabled")
        return None

    logger.debug("Loading JSON schema from %s", SCHEMA_URL)
    response = requests.get(SCHEMA_URL, timeout=15)
    response.raise_for_status()
    schema = response.json()
    logger.debug("JSON schema loaded successfully")
    return schema


def validate_jsonld(document):
    schema = load_schema()
    if schema is None:
        return

    validate(instance=document, schema=schema)
    logger.debug("JSON-LD document passed schema validation")


def validate_jsonld_files(jsonld_files):
    if not SCHEMA_URL:
        logger.info("Skipping validation for %d JSON-LD document(s)", len(jsonld_files))
        return

    logger.info("Validating %d JSON-LD document(s)", len(jsonld_files))
    for index, jsonld_file in enumerate(jsonld_files, start=1):
        logger.debug(
            "Validating JSON-LD document %d (%r)",
            index,
            jsonld_file.filename or "unnamed",
        )
        validate_jsonld(jsonld_file.document)
    logger.info("All JSON-LD documents passed schema validation")
