# OFN Workbench frontend

One responsive interface for dataset generation, vocabulary conversion, and the future vocabulary validation tool. The Flask application and its conversion API are shared by the web and Electron deployments.

## Run as a web app with Docker

From this directory:

```sh
docker compose up --build
```

Open <http://localhost:5000>. The build context intentionally includes the sibling `tools-dataset` and `tools-vocabulary` directories.

## Run as a Windows Electron app

Install Python 3.12+ and Node.js 20+, then double-click `install_and_run.bat`. It creates a local Python environment, installs the backend and Electron dependencies, starts the private Flask service on `127.0.0.1:5127`, and opens the desktop window.

For subsequent launches:

```powershell
cd tools-frontend
npm run desktop
```

`OFN_PYTHON` may be set to an alternative Python executable and `OFN_PORT` to an alternative local port.

## Architecture

- `app.py`: shared Flask API and tool adapters
- `templates/` and `static/`: dependency-free browser frontend
- `electron/main.js`: secure desktop shell and Python service lifecycle
- `/api/dataset/convert`: existing dataset conversion pipeline
- `/api/vocabulary/convert`: allow-listed vocabulary converter scripts
- `/api/validation/validate`: explicit `501` placeholder until `tools-validation` is implemented

Uploads are limited to 50 MB. Temporary vocabulary inputs and outputs are deleted after every request.
