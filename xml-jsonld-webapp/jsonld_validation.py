import os

import requests
from jsonschema import validate


SCHEMA_URL = os.environ.get("JSON_SCHEMA_URL", "").strip()


def load_schema():
    if not SCHEMA_URL:
        return None

    response = requests.get(SCHEMA_URL, timeout=15)
    response.raise_for_status()
    return response.json()


def validate_jsonld(document):
    schema = load_schema()
    if schema is None:
        return

    validate(instance=document, schema=schema)


def validate_jsonld_files(jsonld_files):
    for jsonld_file in jsonld_files:
        validate_jsonld(jsonld_file.document)
