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

from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename


HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parent
DATASET_ROOT = REPOSITORY / "tools-dataset"
VOCABULARY_ROOT = REPOSITORY / "tools-vocabulary"

# The legacy tools are intentionally left in their existing directories. Their
# public Python API is loaded here, while vocabulary CLIs run in an isolated
# child process because they read sys.argv at import time.
sys.path.insert(0, str(DATASET_ROOT))

from core.jsonld_creation import create_jsonld_files  # noqa: E402
from core.jsonld_validation import validate_jsonld_files  # noqa: E402
from core.xml_processing import parse_xml  # noqa: E402


MAX_UPLOAD_BYTES = 50 * 1024 * 1024
VOCABULARY_CONVERTERS = {
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


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES)
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html")

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
                return _error("The XML format is not supported.", 400)
            outputs = create_jsonld_files(parsed)
            if not outputs:
                return _error("No datasets were found in the uploaded model.", 422)
            validate_jsonld_files(outputs)
        except Exception as exc:  # converters expose several domain exceptions
            app.logger.exception("Dataset conversion failed")
            return _error(f"Dataset conversion failed: {exc}", 422)

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
            return _error("Select a supported conversion.", 400)
        upload = _required_upload("file", converter["inputs"])
        if not hasattr(upload, "filename"):
            return upload

        with tempfile.TemporaryDirectory(prefix="ofn-tools-") as temp_dir:
            temp = Path(temp_dir)
            input_name = secure_filename(upload.filename) or f"input{next(iter(converter['inputs']))}"
            input_path = temp / input_name
            output_path = temp / f"{Path(input_name).stem}{converter['output']}"
            upload.save(input_path)
            command = [sys.executable, str(VOCABULARY_ROOT / converter["script"]),
                       str(input_path), str(output_path)]
            for field, argument in converter.get("options", {}).items():
                if request.form.get(field) in {"1", "true", "on"}:
                    command.append(argument)
            try:
                result = subprocess.run(
                    command, cwd=VOCABULARY_ROOT, capture_output=True, text=True,
                    timeout=120, check=False,
                )
            except subprocess.TimeoutExpired:
                return _error("Conversion timed out after 120 seconds.", 504)
            if result.returncode != 0 or not output_path.is_file():
                detail = (result.stderr or result.stdout or "No output was produced.").strip()
                return _error(f"Vocabulary conversion failed: {detail[-2000:]}", 422)
            mimetype = "application/xml" if converter["output"] == ".xml" else "text/turtle"
            return _download(output_path.read_bytes(), output_path.name, mimetype)

    @app.post("/api/validation/validate")
    def validate_vocabulary():
        return _error(
            "Vocabulary validation is prepared in the interface but has not been implemented yet.",
            501,
        )

    @app.errorhandler(413)
    def too_large(_error_value):
        return _error("The uploaded file exceeds the 50 MB limit.", 413)

    return app


def _required_upload(field, suffixes):
    upload = request.files.get(field)
    if upload is None or not upload.filename:
        return _error("Choose a file to continue.", 400)
    if Path(upload.filename).suffix.lower() not in suffixes:
        expected = ", ".join(sorted(suffixes))
        return _error(f"Unsupported file type. Expected: {expected}.", 400)
    return upload


def _error(message, status):
    return jsonify(error=message), status


def _download(content, filename, mimetype):
    return send_file(io.BytesIO(content), mimetype=mimetype, as_attachment=True,
                     download_name=filename)


app = create_app()

if __name__ == "__main__":
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=False)
