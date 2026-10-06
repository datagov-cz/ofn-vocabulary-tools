"""Unified web API and UI for the OFN conversion tools."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

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
    app.config.from_mapping(MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES)
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
        upload = _required_upload("file", {".xml", ".xmi"})
        if not hasattr(upload, "filename"):
            return upload
        try:
            parsed = parse_xml(upload.read())
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
        if len(outputs) == 1:
            name = Path(outputs[0].filename or f"{stem}.jsonld").name
            if not name.endswith(".jsonld"):
                name += ".jsonld"
            payload = json.dumps(outputs[0].document, indent=2, ensure_ascii=False).encode()
            return _download(payload, name, "application/ld+json")

        buffer = io.BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            used = set()
            for number, output in enumerate(outputs, 1):
                name = Path(output.filename or f"{stem}-{number}.jsonld").name
                if not name.endswith(".jsonld"):
                    name += ".jsonld"
                while name in used:
                    name = f"{Path(name).stem}-{number}.jsonld"
                used.add(name)
                archive.writestr(name, json.dumps(output.document, indent=2, ensure_ascii=False))
        return _download(buffer.getvalue(), f"{stem}.zip", "application/zip")

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
            vocabulary_upload = _required_upload("vocabulary_file", converter["vocabulary_inputs"])
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
            input_name = secure_filename(upload.filename) or f"input{next(iter(converter['inputs']))}"
            input_path = temp / input_name
            output_path = temp / (
                f"{Path(input_name).stem}{converter.get('output_name_suffix', '')}{output_suffix}"
            )
            upload.save(input_path)
            command = [sys.executable, str(VOCABULARY_ROOT / converter["script"]),
                       str(input_path)]
            if vocabulary_upload is not None:
                vocabulary_name = secure_filename(vocabulary_upload.filename) or "vocabulary.json"
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
                detail = (result.stderr or result.stdout or "Nebyl vytvořen žádný výstup.").strip()
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
            logger.warning("Ignoring invalid news entry %s: %s", path.name, exc)
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
        raise ValueError(f"missing fields: {', '.join(sorted(required - item.keys()))}")
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
