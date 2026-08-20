import unittest

from jsonld_creation import create_jsonld_files
from file_upload import read_xml_upload
from xml_processing import parse_xml


EA_XMI = b'''<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:uml="http://schema.omg.org/spec/UML/2.1"
         xmlns:Slovniky="http://example.com/Slovniky">
  <uml:Model xmi:id="model" name="Root model">
    <packagedElement xmi:type="uml:Package" xmi:id="vocabulary" name="Testovaci slovnik">
      <packagedElement xmi:type="uml:Package" xmi:id="nested" name="Nested">
        <packagedElement xmi:type="uml:Class" xmi:id="dataset" name="Datova sada" />
        <packagedElement xmi:type="uml:Class" xmi:id="distribution" name="CSV" />
        <packagedElement xmi:type="uml:Association" xmi:id="relation">
          <ownedEnd xmi:id="end-1" type="dataset" />
          <ownedEnd xmi:id="end-2" type="distribution" />
        </packagedElement>
      </packagedElement>
    </packagedElement>
    <packagedElement xmi:type="uml:Package" xmi:id="outside" name="Outside">
      <packagedElement xmi:type="uml:Class" xmi:id="excluded" name="Excluded" />
    </packagedElement>
  </uml:Model>
  <Slovniky:slovnikyPackage xmi:id="sp" base_Package="vocabulary" />
  <Slovniky:datovaSada xmi:id="sd" base_Class="dataset"
      popis="Popis" klicoveSlovo="test" jeZahrnutaVIsvs="42"
      pravniPredpis="https://example.com/law">
    <tag name="vstupn&#237; str&#225;nka" value="https://example.com/dataset" />
  </Slovniky:datovaSada>
  <Slovniky:distribuceSouborKeStazeni xmi:id="ss" base_Class="distribution"
      pristupoveUrl="https://example.com/file.csv"
      souborKeStazeni="https://example.com/file.csv" format="CSV"
      typMedia="text/csv" pravniPredpis="https://example.com/law" />
  <Slovniky:datovaSada xmi:id="ignored" base_Class="excluded" />
</xmi:XMI>'''


class EaXmiTest(unittest.TestCase):
    def test_front_end_upload_accepts_xmi_extension(self):
        class Upload:
            filename = "model.xmi"

            @staticmethod
            def read():
                return EA_XMI

        self.assertEqual(read_xml_upload(Upload()).content, EA_XMI)

    def test_detects_ea_and_filters_to_stereotyped_package_tree(self):
        parsed = parse_xml(EA_XMI)

        self.assertEqual(parsed.source_format, "ea-xmi-2.1")
        self.assertEqual(
            [element.identifier for element in parsed.model.elements],
            ["dataset", "distribution"],
        )
        self.assertEqual(
            [relationship.identifier for relationship in parsed.model.relationships],
            ["relation"],
        )

    def test_uses_stereotype_as_type_and_attributes_as_tagged_values(self):
        parsed = parse_xml(EA_XMI)
        dataset, distribution = parsed.model.elements

        self.assertEqual(dataset.resolved_properties["typ"], "datovaSada")
        self.assertEqual(dataset.resolved_properties["klíčové slovo"], "test")
        self.assertEqual(
            distribution.resolved_properties["typ"],
            "distribuceSouborKeStazeni",
        )
        document = create_jsonld_files(parsed)[0].document
        self.assertEqual(document["popis"], {"cs": "Popis"})
        self.assertEqual(
            document["vstupní_stránka"],
            "https://example.com/dataset",
        )
        self.assertEqual(document["distribuce"][0]["formát"], "formáty:CSV")
        self.assertEqual(document["distribuce"][0]["typ_média"], "mediaTypes:text/csv")


if __name__ == "__main__":
    unittest.main()
