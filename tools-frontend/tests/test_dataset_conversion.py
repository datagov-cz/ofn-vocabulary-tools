"""Checks vocabulary preparation and both dataset download formats."""

import base64
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as frontend  # noqa: E402


MODEL = (b'<model xmlns="http://www.opengroup.org/xsd/archimate/3.0/">'
         b'<elements><element identifier="e1"><name>Foo</name></element></elements></model>')
VOCABULARY = json.dumps({"typ": "Pojem", "iri": "https://example.org/foo", "název": "Foo"},
                        indent=2, ensure_ascii=False)


class DatasetConversionTest(unittest.TestCase):
    def setUp(self):
        self.client = frontend.create_app({"TESTING": True, "SECRET_KEY": "test"}).test_client()

    def prepare(self, result):
        response = SimpleNamespace(ok=True, status_code=200, json=lambda: result)
        with patch.object(frontend.requests, "post", return_value=response) as post:
            prepared = self.client.post(
                "/api/dataset/vocabulary",
                data={"file": (io.BytesIO(MODEL), "model.xml")},
                content_type="multipart/form-data",
            )
            self.assertEqual(post.call_args.kwargs["params"], {"output": "json"})
            self.assertEqual(post.call_args.kwargs["headers"],
                             {"Accept": "application/ld+json"})
        return prepared

    def test_generated_zip_contains_vocabulary_enriched_model_and_dataset(self):
        prepared = self.prepare({"output": VOCABULARY,
                                 "validationResults": {"severityGroups": []}})
        self.assertEqual(prepared.status_code, 200)
        with patch.object(frontend, "parse_xml", return_value=SimpleNamespace(model=object())), \
             patch.object(frontend, "create_jsonld_files", return_value=[
                 SimpleNamespace(filename="dataset.jsonld", document={"ok": True})]), \
             patch.object(frontend, "validate_jsonld_files"):
            converted = self.client.post(
                "/api/dataset/convert",
                data={"file": (io.BytesIO(MODEL), "model.xml"),
                      "vocabulary_file": (io.BytesIO(prepared.json["vocabulary"].encode("utf-8")),
                                          "vocabulary.jsonld"),
                      "conversion_token": prepared.json["conversionToken"]},
                content_type="multipart/form-data",
            )
        self.assertEqual(converted.status_code, 200)
        with ZipFile(io.BytesIO(converted.data)) as archive:
            self.assertEqual(set(archive.namelist()), {
                "model-ofn-vocabulary.jsonld", "model-with-iri.xml", "dataset.jsonld"})
            self.assertIn(b"https://example.org/foo", archive.read("model-with-iri.xml"))
            self.assertEqual(archive.read("model-ofn-vocabulary.jsonld"),
                             VOCABULARY.encode("utf-8"))

    def test_individual_files_include_all_generated_outputs(self):
        prepared = self.prepare({"output": VOCABULARY})
        self.assertEqual(prepared.status_code, 200)
        with patch.object(frontend, "parse_xml", return_value=SimpleNamespace(model=object())), \
             patch.object(frontend, "create_jsonld_files", return_value=[
                 SimpleNamespace(filename="dataset.jsonld", document={"ok": True})]), \
             patch.object(frontend, "validate_jsonld_files"):
            converted = self.client.post(
                "/api/dataset/convert",
                data={"file": (io.BytesIO(MODEL), "model.xml"),
                      "vocabulary_file": (io.BytesIO(VOCABULARY.encode("utf-8")),
                                          "vocabulary.jsonld"),
                      "conversion_token": prepared.json["conversionToken"],
                      "download_mode": "files"},
                content_type="multipart/form-data",
            )
        self.assertEqual(converted.status_code, 200)
        files = {file["name"]: base64.b64decode(file["content"])
                 for file in converted.json["files"]}
        self.assertEqual(set(files), {
            "model-ofn-vocabulary.jsonld", "model-with-iri.xml", "dataset.jsonld"})
        self.assertEqual(files["model-ofn-vocabulary.jsonld"], VOCABULARY.encode("utf-8"))
        self.assertIn(b"https://example.org/foo", files["model-with-iri.xml"])
        self.assertEqual(json.loads(files["dataset.jsonld"]), {"ok": True})

    def test_dataset_step_requires_matching_prepared_model(self):
        prepared = self.prepare({"output": VOCABULARY})
        response = self.client.post(
            "/api/dataset/convert",
            data={"file": (io.BytesIO(MODEL + b" "), "model.xml"),
                  "vocabulary_file": (io.BytesIO(prepared.json["vocabulary"].encode("utf-8")),
                                      "vocabulary.jsonld"),
                  "conversion_token": prepared.json["conversionToken"]},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("model se mezi kroky změnil", response.json["error"])


if __name__ == "__main__":
    unittest.main()
