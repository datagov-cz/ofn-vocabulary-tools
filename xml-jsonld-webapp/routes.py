from xml.etree import ElementTree

import requests
from flask import Blueprint, render_template, request
from jsonschema.exceptions import ValidationError

from file_upload import read_xml_upload
from jsonld_creation import create_jsonld
from jsonld_download import create_jsonld_download
from jsonld_validation import validate_jsonld
from xml_processing import parse_xml


main_routes = Blueprint("main_routes", __name__)


@main_routes.get("/")
def index():
    return render_template("index.html", error=None)


@main_routes.post("/")
def convert():
    try:
        uploaded_xml = read_xml_upload(request.files.get("xml_file"))
        parsed_xml = parse_xml(uploaded_xml.content)
        jsonld_document = create_jsonld(parsed_xml)
        validate_jsonld(jsonld_document)
    except ValueError as exc:
        return render_template("index.html", error=str(exc)), 400
    except ElementTree.ParseError as exc:
        return render_template("index.html", error=f"Invalid XML: {exc}"), 400
    except requests.RequestException as exc:
        return render_template("index.html", error=f"Could not load JSON schema: {exc}"), 502
    except ValidationError as exc:
        return render_template("index.html", error=f"Generated JSON-LD failed schema validation: {exc.message}"), 422

    return create_jsonld_download(jsonld_document, uploaded_xml.filename)
