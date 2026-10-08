import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


class FrontendTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app({"TESTING": True}).test_client()

    def test_health_describes_validation_status(self):
        self.assertEqual(self.client.get("/api/health").json,
                         {"status": "ok", "validation_available": False})

    def test_rejects_unknown_converter(self):
        response = self.client.post("/api/vocabulary/convert", data={
            "converter": "anything", "file": (io.BytesIO(b"x"), "model.xml")})
        self.assertEqual(response.status_code, 400)

    def test_ofn_iri_converter_requires_vocabulary_and_returns_archimate(self):
        model = b'''<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/" identifier="m">
          <name>Model</name><elements><element identifier="e"><name>Pojem A</name></element></elements>
        </model>'''
        vocabulary = json.dumps({"pojmy": [{"iri": "https://example.com/a", "typ": "Pojem",
                                              "název": {"cs": "Pojem A"}}]}).encode()
        missing = self.client.post("/api/vocabulary/convert", data={
            "converter": "ofn-iri-to-archi", "file": (io.BytesIO(model), "model.xml")})
        self.assertEqual(missing.status_code, 400)

        response = self.client.post("/api/vocabulary/convert", data={
            "converter": "ofn-iri-to-archi",
            "file": (io.BytesIO(model), "model.xml"),
            "vocabulary_file": (io.BytesIO(vocabulary), "vocabulary.json"),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        self.assertIn(b"https://example.com/a", response.data)

    def test_json_ld_format_sets_output_extension_and_content_type(self):
        def write_output(command, **_kwargs):
            Path(command[3]).write_text('{}', encoding="utf-8")
            return type("Result", (), {"returncode": 0, "stderr": "", "stdout": ""})()

        with patch("app.subprocess.run", side_effect=write_output):
            response = self.client.post("/api/vocabulary/convert", data={
                "converter": "table-to-ofn",
                "output_format": "json-ld",
                "file": (io.BytesIO(b"xlsx"), "vocabulary.xlsx"),
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/ld+json")
        self.assertIn("vocabulary.json-ld", response.headers["Content-Disposition"])

    def test_rejects_unknown_output_format(self):
        response = self.client.post("/api/vocabulary/convert", data={
            "converter": "table-to-ofn",
            "output_format": "xml",
            "file": (io.BytesIO(b"xlsx"), "vocabulary.xlsx"),
        })
        self.assertEqual(response.status_code, 400)

    def test_validation_is_explicitly_unimplemented(self):
        response = self.client.post("/api/validation/validate")
        self.assertEqual(response.status_code, 501)
        self.assertIn("zatím nebyla implementována", response.json["error"])


if __name__ == "__main__":
    unittest.main()
