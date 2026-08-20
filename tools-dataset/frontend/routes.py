import logging
from xml.etree import ElementTree

import requests
from flask import Blueprint, render_template, request
from jsonschema.exceptions import ValidationError

from core.jsonld_creation import create_jsonld_files
from core.jsonld_validation import validate_jsonld_files
from core.xml_processing import parse_xml
from .file_upload import UploadError, read_xml_upload
from .jsonld_download import create_jsonld_download
from .texts import get_error_text, get_texts


main_routes = Blueprint("main_routes", __name__)
logger = logging.getLogger(__name__)


@main_routes.get("/")
def index():
    logger.debug("Rendering upload page")
    return render_template("index.html", texts=get_texts(), error=None)


@main_routes.post("/")
def convert():
    logger.info("Conversion request started")
    try:
        uploaded_xml = read_xml_upload(request.files.get("xml_file"))
        parsed_xml = parse_xml(uploaded_xml.content)
        jsonld_files = create_jsonld_files(parsed_xml)
        validate_jsonld_files(jsonld_files)
    except UploadError as exc:
        logger.warning("Conversion request rejected: %s", exc.text_key)
        return render_template("index.html", texts=get_texts(), error=get_error_text(exc.text_key)), 400
    except ElementTree.ParseError as exc:
        logger.warning("Conversion failed because the XML is invalid: %s", exc)
        error = get_error_text("invalid_xml", details=exc)
        return render_template("index.html", texts=get_texts(), error=error), 400
    except requests.RequestException as exc:
        logger.error("Conversion failed while loading the JSON schema: %s", exc)
        error = get_error_text("schema_load_failed", details=exc)
        return render_template("index.html", texts=get_texts(), error=error), 502
    except ValidationError as exc:
        logger.warning("Generated JSON-LD failed schema validation: %s", exc.message)
        error = get_error_text("schema_validation_failed", details=exc.message)
        return render_template("index.html", texts=get_texts(), error=error), 422

    response = create_jsonld_download(jsonld_files, uploaded_xml.filename)
    logger.info(
        "Conversion request completed for %r with %d generated file(s)",
        uploaded_xml.filename,
        len(jsonld_files),
    )
    return response
