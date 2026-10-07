"""Unified web API and UI for the OFN conversion tools."""

from __future__ import annotations

import io
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from urllib.parse import urlparse

import requests
from itsdangerous import BadSignature, URLSafeTimedSerializer

from flask import Flask, jsonify, render_template, request, send_file, send_from_directory
from werkzeug.utils import secure_filename


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parent
DATASET_ROOT = REPOSITORY / "tools-dataset"
VOCABULARY_ROOT = REPOSITORY / "tools-vocabulary"
NEWS_ROOT = HERE / "news"

# The legacy tools are intentionally left in their existing directories. Their
# public Python API is loaded here, while vocabulary CLIs run in an isolated
# child process because they read sys.argv at import time.
sys.path.insert(0, str(DATASET_ROOT))

from core.jsonld_creation import create_jsonld_files  # noqa: E402
from core.jsonld_validation import (  # noqa: E402
    JsonLdValidationError,
    validate_jsonld_files,
)
from core.xml_processing import parse_xml  # noqa: E402


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
DEFAULT_CONVERTER_ENDPOINT = "https://oha03.dia.gov.cz/validujeme/api/backend/api/converter/convert"
VOCABULARY_CONVERTERS = {
    "ofn-iri-to-archi": {
        "script": "ofnIRItoArchi.py",
        "inputs": {".xml", ".archimate"},
        "vocabulary_inputs": {".json", ".jsonld", ".json-ld", ".ttl"},
        "output": ".xml",
        "output_name_suffix": "-with-iri",
    },
    "archi-to-ofn": {
        "script": "archiToOFN.py",
        "inputs": {".xml", ".archimate"},
        "output": ".ttl",
    },
    "ea-to-ofn": {
        "script": "eaToOFN.py",
        "inputs": {".xml", ".xmi"},
        "output": ".ttl",
    },
    "table-to-ofn": {
        "script": "tableToOFN.py",
        "inputs": {".xlsx"},
        "output": ".ttl",
    },
    "table-to-archi": {
        "script": "tableToArchi.py",
        "inputs": {".xlsx"},
        "output": ".xml",
        "options": {"with_view": "--with-view"},
    },
}
VOCABULARY_OUTPUT_FORMATS = {
    "ttl": {"suffix": ".ttl", "mimetype": "text/turtle"},
    "json-ld": {"suffix": ".json-ld", "mimetype": "application/ld+json"},
}


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
                            SECRET_KEY=os.getenv(
                                "OFN_SECRET_KEY", "ofn-dataset-conversion-v1"),
                            DATASET_CONVERTER_ENDPOINT=os.getenv(
                                "DATASET_CONVERTER_ENDPOINT", DEFAULT_CONVERTER_ENDPOINT))
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/news")
    def news_page():
        return render_template("news.html")

    @app.get("/docs/dataset/<path:filename>")
    def dataset_documentation(filename):
        return send_from_directory(DATASET_ROOT / "docs", filename)

    @app.get("/api/news")
    def news_feed():
        return jsonify(items=_load_news(app.logger))

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", validation_available=False)

    @app.post("/api/dataset/convert")
    def convert_dataset():
        upload = _required_upload("file", {".xml"})
        if not hasattr(upload, "filename"):
            return upload
        source = upload.read()
        vocabulary_upload = request.files.get("vocabulary_file")
        token = request.form.get("conversion_token", "")
        if vocabulary_upload is None or not token:
            return _error("Nejprve vytvořte slovník OFN pomocí validátoru.", 400)
        vocabulary_bytes = vocabulary_upload.read()
        try:
            vocabulary_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return _error("Vygenerovaný slovník není platný UTF-8.", 400)
        signer = URLSafeTimedSerializer(
            app.secret_key, salt="dataset-vocabulary")
        try:
            expected = signer.loads(token, max_age=1800)
        except BadSignature:
            return _error("Platnost připraveného slovníku vypršela. Spusťte převod znovu.", 400)
        if expected[0] != _digest(source):
            return _error("Nahraný model se mezi kroky změnil. Spusťte převod znovu.", 400)
        if expected[1] != _digest(vocabulary_bytes):
            return _error("Vygenerovaný slovník se mezi kroky změnil. Spusťte převod znovu.", 400)
        try:
            with tempfile.TemporaryDirectory(prefix="ofn-dataset-") as temp_dir:
                temp = Path(temp_dir)
                original = temp / "original.xml"
                vocabulary_path = temp / "vocabulary.jsonld"
                enriched = temp / "enriched.xml"
                original.write_bytes(source)
                vocabulary_path.write_bytes(vocabulary_bytes)
                result = subprocess.run(
                    [sys.executable, str(VOCABULARY_ROOT / "ofnIRItoArchi.py"),
                     str(original), str(vocabulary_path), str(enriched)],
                    cwd=VOCABULARY_ROOT, capture_output=True, text=True,
                    timeout=120, check=False,
                )
                if result.returncode or not enriched.is_file():
                    detail = (
                        result.stderr or result.stdout or "Nevznikl obohacený model.").strip()
                    return _error(f"Doplnění IRI se nezdařilo: {detail[-2000:]}", 422)
                enriched_bytes = enriched.read_bytes()
            parsed = parse_xml(enriched_bytes)
            if parsed.model is None:
                return _error("Tento formát XML není podporován.", 400)
            outputs = create_jsonld_files(parsed)
            if not outputs:
                return _error("V nahraném modelu nebyly nalezeny žádné datové sady.", 422)
            validate_jsonld_files(outputs)
        except JsonLdValidationError as exc:
            app.logger.warning(
                "Dataset conversion found %d validation error(s)",
                len(exc.errors),
            )
            return jsonify(
                error="Vygenerovaná metadata obsahují chyby.",
                errors=exc.errors,
            ), 422
        except Exception as exc:  # converters expose several domain exceptions
            app.logger.exception("Dataset conversion failed")
            return _error(f"Převod datové sady se nezdařil: {exc}", 422)

        stem = Path(secure_filename(upload.filename)).stem or "dataset"
        buffer = io.BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr(f"{stem}-ofn-vocabulary.jsonld", vocabulary_bytes)
            archive.writestr(f"{stem}-with-iri.xml", enriched_bytes)
            used = {f"{stem}-ofn-vocabulary.jsonld", f"{stem}-with-iri.xml"}
            for number, output in enumerate(outputs, 1):
                name = Path(output.filename or f"{stem}-{number}.jsonld").name
                if not name.endswith(".jsonld"):
                    name += ".jsonld"
                while name in used:
                    name = f"{Path(name).stem}-{number}.jsonld"
                used.add(name)
                archive.writestr(name, json.dumps(
                    output.document, indent=2, ensure_ascii=False))
        return _download(buffer.getvalue(), f"{stem}.zip", "application/zip")

    @app.post("/api/dataset/vocabulary")
    def prepare_dataset_vocabulary():
        upload = _required_upload("file", {".xml", ".archimate"})
        if not hasattr(upload, "filename"):
            return upload
        source = upload.read()
        endpoint = request.form.get("endpoint", "").strip(
        ) or app.config["DATASET_CONVERTER_ENDPOINT"]
        parsed_url = urlparse(endpoint)
        if parsed_url.scheme not in {"https", "http"} or not parsed_url.netloc or parsed_url.username or parsed_url.password:
            return _error("Zadejte platnou adresu HTTP nebo HTTPS konvertoru.", 400)
        try:
            response = requests.post(endpoint, params={"output": "json"},
                                     headers={"Accept": "application/ld+json"},
                                     files={"file": (secure_filename(
                                         upload.filename), source, "application/xml")},
                                     timeout=(10, 120))
            data = response.json()
        except requests.RequestException as exc:
            app.logger.warning(
                "Vocabulary converter connection failed: %s", exc)
            return _error("Spojení s konvertorem slovníku se nezdařilo.", 502)
        except ValueError:
            detail = response.text.strip()[:1000] if not response.ok else ""
            return _error(detail or "Konvertor nevrátil platnou odpověď JSON.", 502)
        if not isinstance(data, dict):
            return _error("Konvertor nevrátil očekávaný objekt JSON.", 502)
        report = data.get("validationReport")
        results = data.get("validationResults")
        message = data.get("errorMessage")
        if not response.ok or message:
            return jsonify(error=message or f"Konvertor vrátil HTTP {response.status_code}.",
                           validationReport=report, validationResults=results), 422
        # if _converter_has_errors(results, report):
        #     return jsonify(error="Validátor našel chyby ve slovníku.",
        #                    validationReport=report, validationResults=results), 422
        vocabulary = data.get("output")
        if not isinstance(vocabulary, str) or not vocabulary.strip():
            return jsonify(error="Konvertor nevrátil slovník OFN.",
                           validationReport=report, validationResults=results), 422
        try:
            json.loads(vocabulary)
        except ValueError:
            return _error("Výstup konvertoru není platný JSON-LD.", 422)
        signer = URLSafeTimedSerializer(
            app.secret_key, salt="dataset-vocabulary")
        token = signer.dumps(
            [_digest(source), _digest(vocabulary.encode("utf-8"))])
        return jsonify(vocabulary=vocabulary, conversionToken=token,
                       validationReport=report, validationResults=results)

    @app.post("/api/vocabulary/convert")
    def convert_vocabulary():
        converter_name = request.form.get("converter", "")
        converter = VOCABULARY_CONVERTERS.get(converter_name)
        if converter is None:
            return _error("Vyberte podporovaný typ převodu.", 400)
        upload = _required_upload("file", converter["inputs"])
        if not hasattr(upload, "filename"):
            return upload
        vocabulary_upload = None
        if "vocabulary_inputs" in converter:
            vocabulary_upload = _required_upload(
                "vocabulary_file", converter["vocabulary_inputs"])
            if not hasattr(vocabulary_upload, "filename"):
                return vocabulary_upload

        output_suffix = converter["output"]
        output_mimetype = "application/xml"
        if output_suffix == ".ttl":
            output_format = request.form.get("output_format", "ttl")
            format_config = VOCABULARY_OUTPUT_FORMATS.get(output_format)
            if format_config is None:
                return _error("Vyberte podporovaný výstupní formát.", 400)
            output_suffix = format_config["suffix"]
            output_mimetype = format_config["mimetype"]

        with tempfile.TemporaryDirectory(prefix="ofn-tools-") as temp_dir:
            temp = Path(temp_dir)
            input_name = secure_filename(
                upload.filename) or f"input{next(iter(converter['inputs']))}"
            input_path = temp / input_name
            output_path = temp / (
                f"{Path(input_name).stem}{converter.get('output_name_suffix', '')}{output_suffix}"
            )
            upload.save(input_path)
            command = [sys.executable, str(VOCABULARY_ROOT / converter["script"]),
                       str(input_path)]
            if vocabulary_upload is not None:
                vocabulary_name = secure_filename(
                    vocabulary_upload.filename) or "vocabulary.json"
                vocabulary_path = temp / vocabulary_name
                vocabulary_upload.save(vocabulary_path)
                command.append(str(vocabulary_path))
            command.append(str(output_path))
            for field, argument in converter.get("options", {}).items():
                if request.form.get(field) in {"1", "true", "on"}:
                    command.append(argument)
            try:
                result = subprocess.run(
                    command, cwd=VOCABULARY_ROOT, capture_output=True, text=True,
                    timeout=120, check=False,
                )
            except subprocess.TimeoutExpired:
                return _error("Převod nebyl dokončen v časovém limitu 120 sekund.", 504)
            if result.returncode != 0 or not output_path.is_file():
                detail = (
                    result.stderr or result.stdout or "Nebyl vytvořen žádný výstup.").strip()
                return _error(f"Převod slovníku se nezdařil: {detail[-2000:]}", 422)
            return _download(output_path.read_bytes(), output_path.name, output_mimetype)

    @app.post("/api/validation/validate")
    def validate_vocabulary():
        return _error(
            "Validace slovníku je v rozhraní připravena, ale zatím nebyla implementována.",
            501,
        )

    @app.errorhandler(413)
    def too_large(_error_value):
        return _error("Nahraný soubor překračuje limit 50 MB.", 413)

    return app


def _load_news(logger):
    """Load valid, repository-owned news entries, newest first."""
    items = []
    if not NEWS_ROOT.is_dir():
        return items

    for path in NEWS_ROOT.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            _validate_news_item(item)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "Ignoring invalid news entry %s: %s", path.name, exc)
            continue
        items.append({
            "id": item["id"],
            "publishedAt": item["publishedAt"],
            "title": item["title"],
            "summary": item["summary"],
            "details": item.get("details", []),
        })
    return sorted(items, key=lambda item: (item["publishedAt"], item["id"]), reverse=True)


def _validate_news_item(item):
    if not isinstance(item, dict):
        raise ValueError("entry must be a JSON object")
    required = {"id", "publishedAt", "title", "summary"}
    if not required.issubset(item):
        raise ValueError(
            f"missing fields: {', '.join(sorted(required - item.keys()))}")
    if not all(isinstance(item[field], str) and item[field].strip() for field in required):
        raise ValueError("required fields must be non-empty strings")
    if not item["id"].replace("-", "").isalnum() or item["id"].lower() != item["id"]:
        raise ValueError("id must be a lowercase slug")
    try:
        from datetime import date
        date.fromisoformat(item["publishedAt"])
    except ValueError as exc:
        raise ValueError("publishedAt must be an ISO date") from exc
    details = item.get("details", [])
    if not isinstance(details, list) or not all(isinstance(detail, str) for detail in details):
        raise ValueError("details must be an array of strings")


def _required_upload(field, suffixes):
    upload = request.files.get(field)
    if upload is None or not upload.filename:
        return _error("Nejprve vyberte soubor.", 400)
    if Path(upload.filename).suffix.lower() not in suffixes:
        expected = ", ".join(sorted(suffixes))
        return _error(f"Nepodporovaný typ souboru. Očekávané typy: {expected}.", 400)
    return upload


def _error(message, status):
    return jsonify(error=message), status


def _digest(value):
    return hashlib.sha256(value).hexdigest()


def _converter_has_errors(results, report):
    groups = results.get("severityGroups", []) if isinstance(
        results, dict) else []
    for group in groups if isinstance(groups, list) else []:
        if not isinstance(group, dict):
            continue
        severity = str(group.get("severity", "")).lower()
        if any(word in severity for word in ("violation", "error", "fatal")):
            try:
                if int(group.get("count", 0)) > 0:
                    return True
            except (TypeError, ValueError):
                return True
    validation = report.get("validation", {}) if isinstance(
        report, dict) else {}
    for concept in validation.values() if isinstance(validation, dict) else []:
        violations = concept.get("violations", {}) if isinstance(
            concept, dict) else {}
        for finding in violations.values() if isinstance(violations, dict) else []:
            if isinstance(finding, dict):
                severity = str(finding.get("severity")
                               or finding.get("level") or "").lower()
                if any(word in severity for word in ("violation", "error", "fatal")):
                    return True
    return False


def _download(content, filename, mimetype):
    return send_file(io.BytesIO(content), mimetype=mimetype, as_attachment=True,
                     download_name=filename)


app = create_app()

if __name__ == "__main__":
    # This entry point is for local development. The production container uses
    # Gunicorn and the desktop-style launcher uses Waitress, so enabling Flask's
    # debugger and reloader here does not affect either deployment.
    app.run(
        host=os.getenv("OFN_HOST", "127.0.0.1"),
        port=int(os.getenv("OFN_PORT", "5127")),
        debug=True,
    )
