# ArchiMate / Enterprise Architect XMI to JSON-LD Web App

This is a small standalone Flask app. It accepts either an ArchiMate Model Exchange XML file or an Enterprise Architect XMI 2.1 export through the same upload and returns the generated JSON-LD file(s). The input format is detected from the XML root and namespaces.

For EA exports, only elements and relationships nested anywhere below a package with stereotype `slovnikyPackage` are processed. Regular properties come from stereotype tagged values. `typ` is derived from the element's stereotype name in ASCII camelCase, for example `datovaSada` or `distribuceSouborKeStazeni`.

## Project Structure

- `app.py` is the thin Flask composition and launch entry point.
- `frontend/` contains the HTTP routes, upload/download handling, localized text,
  templates, and static assets.
- `archi/` contains only ArchiMate Model Exchange parsing.
- `ea/` contains only Enterprise Architect XMI 2.1 parsing and package filtering.
- `core/` contains the neutral XML model, format dispatcher, shared JSON-LD
  conversion pipeline, validation, bindings, and logging configuration.
- `tests/` mirrors the runtime behavior with conversion and logging tests.
- `docs/archimate-jsonld-guide.html` and `docs/archimate-jsonld-guide-en.html` document Archi input.
- `docs/ea-xmi-jsonld-guide.html` and `docs/ea-xmi-jsonld-guide-en.html` document EA XMI input.

The format-specific parsers depend on `core.models`. The shared dispatcher in
`core.xml_processing` detects the uploaded format and invokes the appropriate
parser; the front end only calls the public core conversion flow.

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

### Windows local production deployment

Windows users can run the app in a separate desktop window by double-clicking:

```bat
install_and_run.bat
```

This variant requires only Python 3.12 or newer. It does not require Docker,
Git, administrator privileges, or changes to the PowerShell execution policy.
The script creates `.venv` inside `tools-dataset`, installs or updates the
dependencies from `requirements-windows.txt`, and launches `desktop.py` with
`pythonw.exe`. FlaskWebGUI displays the application in its own window and
stops the local Waitress server when that window is closed. Microsoft Edge,
included with supported Windows versions, is used as the window engine.

The desktop entry point can also be started from an activated environment:

```powershell
pip install -r requirements-windows.txt
python desktop.py
```

This deployment is bound to the local computer and runs with Flask debugging
and automatic reloading disabled. The ordinary development and Docker entry
points remain available separately below.

## Run

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

Run the automated tests from this directory with:

```bash
python -m unittest discover -s tests -v
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
