"""Windows desktop entry point for the local production deployment."""

import socket
import sys


def _get_free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("The desktop deployment is supported on Windows only.")

    # Keep desktop-only dependencies out of the regular Flask/Docker startup path.
    from flaskwebgui import FlaskUI

    from app import app

    port = _get_free_loopback_port()
    app.logger.info("Starting Windows desktop application")
    FlaskUI(
        app=app,
        server="flask",
        port=port,
        server_kwargs={
            "app": app,
            "host": "127.0.0.1",
            "port": port,
        },
        width=1280,
        height=900,
        fullscreen=False,
        app_mode=True,
        auto_close=True,
    ).run()


if __name__ == "__main__":
    main()
