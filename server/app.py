from flask import Flask, jsonify, request
from flask_cors import CORS  # type: ignore
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
cors = CORS(app, resources={r"/api/test": {"origins": "*"}})

if __name__ == "__main__":
    app.run()


@app.route("/api/test", methods=["POST"])
def testAPI():
    if request.method == 'POST':
        if request.data:
            return jsonify({"size": len(request.data), "line": request.get_data(as_text=True)[:10]})
        else:
            return '''Invalid request'''
