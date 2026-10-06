# OFN Workbench frontend

One responsive interface for dataset generation, vocabulary conversion, and the future vocabulary validation tool. The application uses a Python backend and a dependency-free browser frontend; Node.js and npm are not required.

## Run locally

Install Python 3.12+, then create an environment and install the dependencies:

```sh
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -r requirements.txt
# Linux/macOS: .venv/bin/python -m pip install -r requirements.txt
```

Start the application with the environment's Python:

```sh
# Windows: .venv\Scripts\python launcher.py
# Linux/macOS: .venv/bin/python launcher.py
```

The launcher serves the application at <http://127.0.0.1:5127> and opens it in the default browser. Press Ctrl+C in its terminal to stop it. `OFN_HOST` and `OFN_PORT` may be used to change the listening address.

### Develop with automatic reload

Run `app.py` instead of the Waitress-based launcher while developing:

```sh
# Windows: .venv\Scripts\python app.py
# Linux/macOS: .venv/bin/python app.py
```

The development server also runs at <http://127.0.0.1:5127>. It automatically
restarts after Python source changes. Refresh the browser after changing HTML,
CSS, or JavaScript files. This debug server is intended only for local
development; use `launcher.py` or the Docker image for normal deployments.

On Windows, [`../install_and_run.bat`](../install_and_run.bat) creates a dedicated `.venv-windows` environment, installs the dependencies, and starts the application. Double-click it in the project root for the first and subsequent launches. To run the Flask development server with debug mode and automatic reload, invoke it from a terminal in the project root:

```bat
install_and_run.bat --debug
```

Run `install_and_run.bat --help` to display the available option. Set `OFN_PYTHON` if the Python executable cannot be found automatically. If setup fails, the window stays open and displays the error.

The Windows installer accepts prebuilt Python packages only. It does not require Visual Studio or the Microsoft C++ Build Tools.

## Run as a web app with Docker

From this directory:

```sh
docker compose up --build
```

Open <http://localhost:5000>. The build context intentionally includes the sibling `tools-dataset` and `tools-vocabulary` directories.

## Architecture

- `app.py`: shared Flask API and tool adapters
- `launcher.py`: local production server and browser launcher
- `templates/` and `static/`: dependency-free browser frontend
- `/api/dataset/convert`: existing dataset conversion pipeline
- `/api/vocabulary/convert`: allow-listed vocabulary converter scripts
- `/api/validation/validate`: explicit `501` placeholder until `tools-validation` is implemented
- `/api/news`: repository-owned changelog entries, newest first
- `/news`: complete news archive with browser-local read state

Uploads are limited to 50 MB. Temporary vocabulary inputs and outputs are deleted after every request.

## Writing news entries

Add one JSON file to `news/` in the same commit as each user-visible change. Open
`news-editor.html` directly in a browser to fill in a small form and download a
correctly named entry. Move the downloaded file into `news/` before committing.

The title and summary are required. Details are optional and entered one per line.
The editor creates the entry ID and publication date from the title and the
developer's local date. IDs must be unique; adjust the generated slug before
committing if two updates have the same title on the same day.

Maintenance-only commits such as refactors, tests, or documentation changes do
not need a news entry.
