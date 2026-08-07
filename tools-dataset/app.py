import os

from flask import Flask

from routes import main_routes


def create_app():
    app = Flask(__name__)
    app.register_blueprint(main_routes)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )
