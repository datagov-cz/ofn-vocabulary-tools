# ArchiMate / Enterprise Architect XMI to JSON-LD Web App

This is a small standalone Flask app. It accepts either an ArchiMate Model Exchange XML file or an Enterprise Architect XMI 2.1 export through the same upload and returns the generated JSON-LD file(s). The input format is detected from the XML root and namespaces.

For EA exports, only elements and relationships nested anywhere below a package with stereotype `slovnikyPackage` are processed. Regular properties come from stereotype tagged values. `typ` is derived from the element's stereotype name in ASCII camelCase, for example `datovaSada` or `distribuceSouborKeStazeni`.

## Project Structure

- `app.py` creates and runs the Flask application.
- `routes.py` connects the upload form to the conversion flow.
- `file_upload.py` loads and checks the uploaded XML file.
- `xml_processing.py` detects the XML format and dispatches it.
- `archimate_xml.py` contains only ArchiMate Model Exchange parsing.
- `ea_xmi.py` contains only Enterprise Architect XMI 2.1 parsing and package filtering.
- `xml_model.py` defines the neutral model used by JSON-LD generation.
- `jsonld_creation.py` orchestrates creation of one or more JSON-LD files and preserves the public creation API.
- `jsonld_builders.py` maps datasets and distributions to JSON-LD documents.
- `jsonld_properties.py` reads, normalizes, and validates ArchiMate properties.
- `jsonld_relationships.py` finds distributions and terms related to a dataset.
- `jsonld_required_fields.py` reports required fields missing from generated documents.
- `jsonld_validation.py` validates generated JSON-LD against the default OFN schema or a schema configured with `JSON_SCHEMA_URL`.
- `jsonld_download.py` returns one generated JSON-LD file directly, or multiple JSON-LD files as a ZIP download.
- `texts.json` contains the user-facing front-end text and displayed error messages.
- `texts.py` loads text from `texts.json`.
- `templates/index.html` and `static/styles.css` contain the front end.
- `docs/archimate-jsonld-guide.html` and `docs/archimate-jsonld-guide-en.html` document Archi input.
- `docs/ea-xmi-jsonld-guide.html` and `docs/ea-xmi-jsonld-guide-en.html` document EA XMI input.

## Setup

```bash
cd tools-dataset
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd tools-dataset
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

On Windows, you can also run the installation script:

```bat
install_and_run.bat
```

The script pulls the latest `main` branch, creates `.venv` when needed, installs or updates dependencies, starts the app, and opens the default browser.

## Run

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Logging

Application, conversion, validation, download, and Python warning messages are
written to the Flask instance log:

```text
instance/tools-dataset.log
```

The log rotates at 10 MB and keeps five backup files. The default logging
level is `INFO`. Set `LOG_LEVEL` to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or
`CRITICAL` before starting the application. `DEBUG` includes detailed parsing,
element-selection, and per-document validation messages.

At `INFO`, the conversion records the dataset and distribution elements it
finds, the selected class/term retrieval method, class/relationship/attribute
counts, and every generated or retrieved output IRI. At `DEBUG`, it additionally
records every selected class, relationship, and attribute, plus every resolved
property on each selected dataset and distribution element.

On Linux or macOS:

```bash
LOG_LEVEL=DEBUG python app.py
```

On Windows PowerShell:

```powershell
$env:LOG_LEVEL = "DEBUG"
python app.py
```

With Docker Compose:

```bash
LOG_LEVEL=DEBUG docker compose up --build
```

An invalid `LOG_LEVEL` stops application startup with an explanatory error.

## JSON Schema Validation

By default, the app validates generated JSON-LD against:

```text
https://ofn.gov.cz/dcat-ap-cz-datov%c3%a1-rozhran%c3%ad/draft/datov%C3%A1-sada/sch%C3%A9ma.json
```

Set `JSON_SCHEMA_URL` to override the schema URL before running the app:

```bash
export JSON_SCHEMA_URL="https://example.com/schema.json"
python app.py
```

On Windows PowerShell:

```powershell
$env:JSON_SCHEMA_URL = "https://example.com/schema.json"
python app.py
```

Set `JSON_SCHEMA_URL` to an empty string to disable schema validation.

## Docker Development

The development container bind-mounts the project folder and runs Flask with debug mode enabled.

```bash
cd tools-dataset
docker compose up --build
```

Then open:

```text
http://127.0.0.1:5000
```

To override the default validation schema:

```bash
JSON_SCHEMA_URL="https://example.com/schema.json" docker compose up --build
```

The same development setup is also available explicitly as `docker-compose.dev.yml`.

## Docker Production

The production container copies the app into the image and runs it with Gunicorn.

```bash
cd tools-dataset
docker compose -f docker-compose.prod.yml up --build -d
```

Then open:

```text
http://127.0.0.1:5000
```

To override the default validation schema:

```bash
JSON_SCHEMA_URL="https://example.com/schema.json" docker compose -f docker-compose.prod.yml up --build -d
```

Stop the production container:

```bash
docker compose -f docker-compose.prod.yml down
```
