# XML to JSON-LD Web App

This is a small standalone Flask app. It serves one page with an XML upload form and returns a generated JSON-LD file for download.

The XML conversion is currently only a skeleton. It parses the XML, reads the root element name, and emits a minimal JSON-LD document. The real XML parsing can be added later in `parse_xml()` in `xml_processing.py`, and the real JSON-LD mapping can be added in `create_jsonld_files()` in `jsonld_creation.py`.

## Project Structure

- `app.py` creates and runs the Flask application.
- `routes.py` connects the upload form to the conversion flow.
- `file_upload.py` loads and checks the uploaded XML file.
- `xml_processing.py` parses XML and contains the marked setup area for custom XML parsing.
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

## Setup

```bash
cd xml-jsonld-webapp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd xml-jsonld-webapp
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
cd xml-jsonld-webapp
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
cd xml-jsonld-webapp
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
