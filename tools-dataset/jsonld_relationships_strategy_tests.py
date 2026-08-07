import unittest

from jsonld_creation import create_jsonld_files
from xml_processing import (
    ArchimateElement,
    ArchimateModel,
    ArchimateRelationship,
    LangText,
    ParsedXml,
)


def element(identifier, term_type, **properties):
    return ArchimateElement(
        identifier=identifier,
        type="BusinessObject",
        names=[LangText(identifier, "cs")],
        resolved_properties={
            "typ": term_type,
            "identifikátor": "https://example.com/{}".format(identifier),
            **properties,
        },
    )


def relationship(
    identifier,
    relationship_type,
    source,
    target,
    *,
    directed=False,
    named=True,
):
    return ArchimateRelationship(
        identifier=identifier,
        type=relationship_type,
        source=source,
        target=target,
        names=[LangText(identifier, "cs")] if named else [],
        resolved_properties={
            "identifikátor": "https://example.com/{}".format(identifier),
        },
        is_directed="true" if directed else "false",
    )


def document(elements, relationships):
    parsed_xml = ParsedXml(
        root_element_name="model",
        model=ArchimateModel(
            identifier="model",
            version=None,
            elements=elements,
            relationships=relationships,
        ),
    )
    return create_jsonld_files(parsed_xml)[0].document


class RelatedTermStrategyTest(unittest.TestCase):
    def test_detailed_includes_only_terms_directly_associated_with_dataset(self):
        dataset = element(
            "dataset",
            "datová sada",
            **{"metoda sbírání pojmů": "podrobně"},
        )
        class_a = element("class-a", "typ objektu")
        class_b = element("class-b", "typ subjektu")
        property_a = element("property-a", "typ vlastnosti")
        class_association = relationship(
            "class-association",
            "Association",
            "class-a",
            "class-b",
            directed=True,
        )
        relationships = [
            class_association,
            relationship("dataset-class", "Association", "dataset", "class-a"),
            relationship(
                "dataset-property", "Association", "dataset", "property-a"
            ),
            relationship(
                "dataset-association",
                "Association",
                "dataset",
                "class-association",
            ),
        ]

        result = document(
            [dataset, class_a, class_b, property_a], relationships
        )

        self.assertEqual(
            result["týká_se_pojmu"],
            [
                "https://example.com/class-a",
                "https://example.com/property-a",
                "https://example.com/class-association",
            ],
        )
        self.assertNotIn("metoda_sbírání_pojmů", result)

    def test_standard_expands_properties_and_associations_of_selected_classes(self):
        dataset = element(
            "dataset",
            "datová sada",
            **{"metoda sbírání pojmů": "standard"},
        )
        class_a = element("class-a", "typ objektu")
        class_b = element("class-b", "typ subjektu")
        class_c = element("class-c", "typ objektu")
        property_a = element("property-a", "typ vlastnosti")
        property_c = element("property-c", "typ vlastnosti")
        relationships = [
            relationship("dataset-a", "Association", "dataset", "class-a"),
            relationship("dataset-b", "Association", "class-b", "dataset"),
            relationship(
                "a-specializes-c", "Specialization", "class-a", "class-c"
            ),
            relationship(
                "property-of-a", "Composition", "class-a", "property-a"
            ),
            relationship(
                "aggregated-property", "Aggregation", "class-a", "property-c"
            ),
            relationship(
                "a-to-b",
                "Association",
                "class-a",
                "class-b",
                directed=True,
            ),
            relationship(
                "b-to-c",
                "Association",
                "class-b",
                "class-c",
                directed=True,
            ),
            relationship(
                "a-to-b-undirected", "Association", "class-a", "class-b"
            ),
            relationship(
                "a-to-b-unnamed",
                "Association",
                "class-a",
                "class-b",
                directed=True,
                named=False,
            ),
        ]

        result = document(
            [
                dataset,
                class_a,
                class_b,
                class_c,
                property_a,
                property_c,
            ],
            relationships,
        )

        self.assertEqual(
            result["týká_se_pojmu"],
            [
                "https://example.com/class-a",
                "https://example.com/class-b",
                "https://example.com/property-a",
                "https://example.com/a-to-b",
            ],
        )

    def test_aggressive_recursively_expands_the_reachable_term_graph(self):
        dataset = element(
            "dataset",
            "datová sada",
            **{"metoda sbírání pojmů": "agresivně"},
        )
        class_a = element("class-a", "typ objektu")
        class_b = element("class-b", "typ subjektu")
        class_c = element("class-c", "typ objektu")
        class_d = element("class-d", "typ subjektu")
        class_e = element("class-e", "typ objektu")
        reverse_only = element("reverse-only", "typ objektu")
        property_d = element("property-d", "typ vlastnosti")
        property_e = element("property-e", "typ vlastnosti")
        property_ignored = element("property-ignored", "typ vlastnosti")
        property_wrong_hierarchy = element(
            "property-wrong-hierarchy", "typ vlastnosti"
        )
        relationships = [
            relationship("dataset-a", "Association", "dataset", "class-a"),
            relationship(
                "a-to-b", "Association", "class-a", "class-b", directed=True
            ),
            relationship(
                "b-to-c-undirected", "Association", "class-b", "class-c"
            ),
            relationship(
                "b-specializes-d", "Specialization", "class-b", "class-d"
            ),
            relationship(
                "property-of-d", "Composition", "class-d", "property-d"
            ),
            relationship(
                "property-generalization",
                "Generalization",
                "property-d",
                "property-e",
            ),
            relationship(
                "property-aggregation",
                "Aggregation",
                "property-e",
                "property-ignored",
            ),
            relationship(
                "class-property-generalization",
                "Generalization",
                "class-d",
                "property-wrong-hierarchy",
            ),
            relationship(
                "d-to-e-unnamed",
                "Association",
                "class-d",
                "class-e",
                directed=True,
                named=False,
            ),
            relationship(
                "reverse-to-a",
                "Association",
                "reverse-only",
                "class-a",
                directed=True,
            ),
        ]

        result = document(
            [
                dataset,
                class_a,
                class_b,
                class_c,
                class_d,
                class_e,
                reverse_only,
                property_d,
                property_e,
                property_ignored,
                property_wrong_hierarchy,
            ],
            relationships,
        )

        self.assertEqual(
            result["týká_se_pojmu"],
            [
                "https://example.com/class-a",
                "https://example.com/class-b",
                "https://example.com/class-d",
                "https://example.com/reverse-only",
                "https://example.com/property-d",
                "https://example.com/property-e",
                "https://example.com/a-to-b",
                "https://example.com/reverse-to-a",
            ],
        )


if __name__ == "__main__":
    unittest.main()
