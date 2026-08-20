import unittest

from jsonld_creation import create_jsonld_files
from xml_processing import (
    ArchimateElement,
    ArchimateModel,
    ArchimateRelationship,
    LangText,
    ParsedXml,
)


def element(identifier, name, term_type, **properties):
    return ArchimateElement(
        identifier=identifier,
        type="BusinessObject",
        names=[LangText(name, "cs")],
        resolved_properties={"typ": term_type, **properties},
    )


class LoggingDetailsTest(unittest.TestCase):
    def test_conversion_logs_summary_and_detailed_element_information(self):
        dataset = element(
            "dataset",
            "Dataset",
            "datová sada",
            **{"metoda sbírání pojmů": "podrobně"},
        )
        distribution = element(
            "distribution",
            "Distribution",
            "distribuce - soubor ke stažení",
            formát="CSV",
        )
        class_element = element(
            "class-a",
            "Class A",
            "typ objektu",
            identifikátor="https://example.com/class-a",
        )
        attribute_element = element(
            "attribute-a",
            "Attribute A",
            "typ vlastnosti",
            identifikátor="https://example.com/attribute-a",
        )
        term_relationship = ArchimateRelationship(
            identifier="term-relationship",
            type="Association",
            source="class-a",
            target="class-b",
            names=[LangText("Term relationship", "cs")],
            resolved_properties={
                "identifikátor": "https://example.com/term-relationship",
            },
            is_directed="true",
        )
        class_b = element("class-b", "Class B", "typ subjektu")
        relationships = [
            term_relationship,
            ArchimateRelationship(
                "dataset-distribution", "Association", "dataset", "distribution"
            ),
            ArchimateRelationship(
                "dataset-class", "Association", "dataset", "class-a"
            ),
            ArchimateRelationship(
                "dataset-attribute", "Association", "dataset", "attribute-a"
            ),
            ArchimateRelationship(
                "dataset-relationship",
                "Association",
                "dataset",
                "term-relationship",
            ),
        ]
        parsed_xml = ParsedXml(
            root_element_name="model",
            source_format="archimate",
            model=ArchimateModel(
                identifier="model",
                version=None,
                names=[LangText("Vocabulary", "cs")],
                elements=[
                    dataset,
                    distribution,
                    class_element,
                    attribute_element,
                    class_b,
                ],
                relationships=relationships,
            ),
        )

        with self.assertLogs(level="DEBUG") as captured:
            create_jsonld_files(parsed_xml)

        messages = "\n".join(captured.output)
        self.assertIn("Found dataset element ID 'dataset'", messages)
        self.assertIn("Found distribution element ID 'distribution'", messages)
        self.assertIn("retrieval method 'podrobně'", messages)
        self.assertIn(
            "found 1 class(es), 1 relationship(s), and 1 attribute(s)",
            messages,
        )
        self.assertIn("Class found: element ID 'class-a'", messages)
        self.assertIn("Relationship found: element ID 'term-relationship'", messages)
        self.assertIn("Attribute found: element ID 'attribute-a'", messages)
        self.assertIn("Property found for dataset element ID 'dataset'", messages)
        self.assertIn(
            "Property found for distribution element ID 'distribution'",
            messages,
        )
        self.assertIn("Generated dataset IRI", messages)
        self.assertIn("Retrieved term IRI 'https://example.com/class-a'", messages)
        self.assertIn("Generated distribution IRI", messages)


if __name__ == "__main__":
    unittest.main()
