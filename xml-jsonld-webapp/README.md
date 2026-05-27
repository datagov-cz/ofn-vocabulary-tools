# XML to JSON-LD Web App

This is a small standalone Flask app. It serves one page with an XML upload form and returns a generated JSON-LD file for download.

The XML conversion is currently only a skeleton. It parses the XML, reads the root element name, and emits a minimal JSON-LD document. The real XML parsing can be added later in `parse_xml()` in `xml_processing.py`, and the real JSON-LD mapping can be added in `create_jsonld()` in `jsonld_creation.py`.

## Project Structure

- `app.py` creates and runs the Flask application.
- `routes.py` connects the upload form to the conversion flow.
- `file_upload.py` loads and checks the uploaded XML file.
- `xml_processing.py` parses XML and contains the marked setup area for custom XML parsing.
- `jsonld_creation.py` creates JSON-LD and contains the marked setup area for custom JSON-LD mapping.
- `jsonld_validation.py` validates generated JSON-LD against `JSON_SCHEMA_URL` when configured.
- `jsonld_download.py` returns the generated JSON-LD as a file download.
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

## Run

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## JSON Schema Validation

The app is ready to validate the generated JSON-LD against an online JSON schema.

Set the schema URL before running the app:

```bash
export JSON_SCHEMA_URL="https://example.com/schema.json"
python app.py
```

On Windows PowerShell:

```powershell
$env:JSON_SCHEMA_URL = "https://example.com/schema.json"
python app.py
```

If `JSON_SCHEMA_URL` is not set, schema validation is skipped for now.

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

To include schema validation:

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

To include schema validation:

```bash
JSON_SCHEMA_URL="https://example.com/schema.json" docker compose -f docker-compose.prod.yml up --build -d
```

Stop the production container:

```bash
docker compose -f docker-compose.prod.yml down
```
