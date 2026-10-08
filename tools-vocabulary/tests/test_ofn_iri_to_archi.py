import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from lxml import etree


MODULE_PATH = Path(__file__).resolve().parents[1] / "ofnIRItoArchi.py"
SPEC = importlib.util.spec_from_file_location("ofnIRItoArchi", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

NS = "http://www.opengroup.org/xsd/archimate/3.0/"


MODEL = f"""<?xml version="1.0" encoding="UTF-8"?>
<model xmlns="{NS}" identifier="model-1">
  <name>Test</name>
  <elements>
    <element identifier="element-1"><name xml:lang="cs"> Turistický   cíl </name>
      <properties><property propertyDefinitionRef="identifier"><value>https://old.example/id</value></property></properties>
    </element>
  </elements>
  <relationships>
    <relationship identifier="relationship-1" source="element-1" target="element-1"><name>MÁ TYP</name></relationship>
  </relationships>
  <propertyDefinitions>
    <propertyDefinition identifier="identifier" type="string"><name>Identifikátor</name></propertyDefinition>
  </propertyDefinitions>
</model>"""


class OfnIriToArchiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.model = self.root / "model.xml"
        self.output = self.root / "output.xml"
        self.model.write_text(MODEL, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def values(self, identifier):
        tree = etree.parse(str(self.output))
        node = tree.xpath(f"//*[local-name()='element' or local-name()='relationship'][@identifier='{identifier}']")[0]
        return node.xpath("./*[local-name()='properties']/*[local-name()='property']/*[local-name()='value']/text()")

    def test_compact_json_discards_new_iri_when_valid_identifier_exists(self):
        vocabulary = self.root / "vocabulary.json"
        vocabulary.write_text(json.dumps({
            "pojmy": [
                {"iri": "https://example.com/tourist", "typ": ["Pojem"],
                 "název": {"cs": "Turistický cíl"}},
                {"iri": "https://example.com/has-type", "typ": "Pojem",
                 "název": {"cs": "má typ"}},
            ]
        }, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(MODULE.enrich_model(self.model, vocabulary, self.output), (2, 1))
        self.assertEqual(self.values("element-1"), ["https://old.example/id"])
        self.assertEqual(self.values("relationship-1"), ["https://example.com/has-type"])

    def test_turtle_discards_matches_when_valid_identifier_exists(self):
        vocabulary = self.root / "vocabulary.ttl"
        vocabulary.write_text("""
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
<https://example.com/a> a slovníky:pojem; skos:prefLabel "Turistický cíl"@cs .
<https://example.com/b> a slovníky:pojem; skos:prefLabel "Turistický cíl"@cs .
""", encoding="utf-8")

        self.assertEqual(MODULE.enrich_model(self.model, vocabulary, self.output), (1, 0))
        self.assertEqual(self.values("element-1"), ["https://old.example/id"])

    def test_malformed_identifier_is_replaced_instead_of_appended(self):
        self.model.write_text(MODEL.replace(
            "https://old.example/id", "not-an-https-iri"), encoding="utf-8")
        vocabulary = self.root / "vocabulary.json"
        vocabulary.write_text(json.dumps({"pojmy": [{
            "iri": "https://example.com/tourist", "typ": "Pojem",
            "název": {"cs": "Turistický cíl"},
        }]}, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(MODULE.enrich_model(self.model, vocabulary, self.output), (1, 1))
        self.assertEqual(self.values("element-1"), ["https://example.com/tourist"])

    def test_empty_identifier_is_replaced_instead_of_appended(self):
        self.model.write_text(MODEL.replace(
            "<value>https://old.example/id</value>", "<value />"), encoding="utf-8")
        vocabulary = self.root / "vocabulary.json"
        vocabulary.write_text(json.dumps({"pojmy": [{
            "iri": "https://example.com/tourist", "typ": "Pojem",
            "název": {"cs": "Turistický cíl"},
        }]}, ensure_ascii=False), encoding="utf-8")

        self.assertEqual(MODULE.enrich_model(self.model, vocabulary, self.output), (1, 1))
        self.assertEqual(self.values("element-1"), ["https://example.com/tourist"])


if __name__ == "__main__":
    unittest.main()
