import os

from flask import Flask

from core.logging_config import configure_logging
from frontend.routes import main_routes


def create_app():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    configure_logging(app)
    app.register_blueprint(main_routes)
    app.logger.info("Flask application initialized")
    return app


app = create_app()


if __name__ == "__main__":
    app.logger.info("Starting Flask development server")
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )
