"""Run OFN Workbench locally and open it in the default web browser."""

from __future__ import annotations

import os
import threading
import webbrowser

from waitress import create_server

from app import app


def main() -> None:
    host = os.getenv("OFN_HOST", "127.0.0.1")
    port = int(os.getenv("OFN_PORT", "5127"))
    url = f"http://{host}:{port}"
    server = create_server(app, host=host, port=port, threads=4)

    print(f"OFN Workbench is running at {url}")
    print("Press Ctrl+C to stop it.")
    if os.getenv("OFN_NO_BROWSER") != "1":
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()

    try:
        server.run()
    except KeyboardInterrupt:
        print("\nStopping OFN Workbench.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
