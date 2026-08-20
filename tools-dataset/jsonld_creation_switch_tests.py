import unittest

from jsonld_creation import create_jsonld_files
from jsonld_relationships import getIRIofTerm
from xml_processing import (
    ArchimateElement,
    ArchimateModel,
    ArchimateRelationship,
    LangText,
    ParsedXml,
)


def element(identifier, name, properties):
    return ArchimateElement(
        identifier=identifier,
        type="BusinessObject",
        names=[LangText(name, "cs")],
        resolved_properties=properties,
    )


def parsed_model(elements, relationships):
    return ParsedXml(
        root_element_name="model",
        model=ArchimateModel(
            identifier="model",
            version=None,
            names=[LangText("Testovací slovník", "cs")],
            elements=elements,
            relationships=relationships,
        ),
    )


class CreateJsonLdFilesSwitchTest(unittest.TestCase):
    def test_generated_term_iri_requires_a_czech_model_name(self):
        term = element("term", "Term", {"typ": "typ subjektu"})
        model = ArchimateModel(
            identifier="model",
            version=None,
            names=[
                LangText("", "cs"),
                LangText("Test vocabulary", "en"),
            ],
        )

        with self.assertRaisesRegex(
            ValueError,
            "model doesn't have a name in Czech",
        ):
            getIRIofTerm(term, model)

    def test_codes_are_expanded_to_jsonld_compact_iris(self):
        dataset = element("dataset", "Test", {
            "typ": "datová sada",
            "téma": "GOVE;ECON",
            "periodicita aktualizace": "CONT",
            "koncept euroVoc": "1234; 5678",
            "je zahrnuta v isvs": "42",
        })
        distribution = element("distribution", "Archive", {
            "typ": "distribuce - soubor ke stažení",
            "formát": "7Z",
            "typ média": "application/json",
            "typ média komprese": "application/gzip",
            "typ média balíčku": "application/zip",
        })
        relationship = ArchimateRelationship(
            identifier="distribution-relation",
            type="Association",
            source="dataset",
            target="distribution",
        )

        document = create_jsonld_files(
            parsed_model([dataset, distribution], [relationship])
        )[0].document

        self.assertEqual(document["téma"], ["témata:GOVE", "témata:ECON"])
        self.assertEqual(
            document["periodicita_aktualizace"],
            "frekvence:CONT",
        )
        self.assertEqual(
            document["koncept_euroVoc"],
            ["euroVoc:1234", "euroVoc:5678"],
        )
        self.assertEqual(document["je_zahrnuta_v_isvs"], "isvs:42")

        output_distribution = document["distribuce"][0]
        self.assertEqual(output_distribution["formát"], "formáty:7Z")
        self.assertEqual(
            output_distribution["typ_média"],
            "mediaTypes:application/json",
        )
        self.assertEqual(
            output_distribution["typ_média_komprese"],
            "mediaTypes:application/gzip",
        )
        self.assertEqual(
            output_distribution["typ_média_balíčku"],
            "mediaTypes:application/zip",
        )

    def test_prefixed_subproperties_replace_switches(self):
        dataset = element("dataset", "Test", {
            "typ": "datová sada",
            "specifikace": "https://example.com/specification; https://example.com/second-specification",
            "je součástí": "https://example.com/dataset-series",
            "časové pokrytí - začátek": "2026-08-04",
            "časové pokrytí - konec": "2026-08-05",
            "kontaktní bod - jméno": "Alice",
            "kontaktní bod - email": "alice@example.com",
        })
        distribution = element("distribution", "API", {
            "typ": "distribuce - datová služba",
            "podmínky užití - autorské dílo": "https://example.com/licence",
            "podmínky užití - autor": "Alice",
            "podmínky užití - databáze jako autorské dílo": "https://example.com/database-copyright",
            "podmínky užití - autor databáze": "Bob",
            "podmínky užití - databáze chráněná zvláštními právy": "https://example.com/database-rights",
            "podmínky užití - osobní údaje": "https://example.com/personal-data",
            "autorské dílo": "https://example.com/ignored",
            "přístupová služba - přístupový bod": "https://example.com/api",
            "přístupová služba - popis přístupového bodu": "https://example.com/api-description",
            "přístupová služba - právní předpis": "https://example.com/law",
            "přístupová služba - specifikace": "https://example.com/specification",
            "přístupová služba - dokumentace": "https://example.com/documentation",
            "přístupový bod": "https://example.com/ignored-api",
        })
        term = element("term", "Term", {"typ": "typ subjektu"})
        relationships = [
            ArchimateRelationship(
                identifier="distribution-relation",
                type="Association",
                source="dataset",
                target="distribution",
            ),
            ArchimateRelationship(
                identifier="term-relation",
                type="Association",
                source="dataset",
                target="term",
            ),
        ]

        document = create_jsonld_files(
            parsed_model([dataset, distribution, term], relationships)
        )[0].document

        self.assertEqual(
            document["časové_pokrytí"]["začátek"],
            "2026-08-04",
        )
        self.assertEqual(document["časové_pokrytí"]["konec"], "2026-08-05")
        self.assertEqual(
            document["kontaktní_bod"]["e-mail"],
            "mailto:alice@example.com",
        )
        self.assertEqual(document["kontaktní_bod"]["jméno"], {"cs": "Alice"})
        self.assertEqual(
            document["specifikace"],
            [
                "https://example.com/specification",
                "https://example.com/second-specification",
            ],
        )
        self.assertEqual(
            document["je_součástí"],
            "https://example.com/dataset-series",
        )
        self.assertIn("týká_se_pojmu", document)
        self.assertEqual(
            document["týká_se_pojmu"],
            ["https://slovník.gov.cz/testovací-slovník/pojem/term"],
        )
        self.assertEqual(len(document["distribuce"]), 1)

        output_distribution = document["distribuce"][0]
        self.assertEqual(
            output_distribution["podmínky_užití"]["autorské_dílo"],
            "https://example.com/licence",
        )
        self.assertEqual(
            set(output_distribution["podmínky_užití"]),
            {
                "iri",
                "typ",
                "autorské_dílo",
                "autor",
                "databáze_jako_autorské_dílo",
                "autor_databáze",
                "databáze_chráněná_zvláštními_právy",
                "osobní_údaje",
            },
        )
        self.assertEqual(
            output_distribution["přístupová_služba"]["přístupový_bod"],
            "https://example.com/api",
        )
        self.assertEqual(
            output_distribution["přístupová_služba"]["specifikace"],
            ["https://example.com/specification"],
        )
        self.assertEqual(
            set(output_distribution["přístupová_služba"]),
            {
                "iri",
                "typ",
                "název",
                "přístupový_bod",
                "popis_přístupového_bodu",
                "právní_předpis",
                "specifikace",
                "dokumentace",
            },
        )

    def test_old_switches_and_unprefixed_children_do_not_create_nested_objects(self):
        dataset = element("dataset", "Test", {
            "typ": "datová sada",
            "časové pokrytí": "ano",
            "kontaktní bod": "ano",
        })
        distribution = element("distribution", "CSV", {
            "typ": "distribuce - soubor ke stažení",
            "podmínky užití": "ano",
            "autorské dílo": "https://example.com/licence",
        })
        relationship = ArchimateRelationship(
            identifier="distribution-relation",
            type="Association",
            source="dataset",
            target="distribution",
        )

        document = create_jsonld_files(
            parsed_model([dataset, distribution], [relationship])
        )[0].document

        self.assertNotIn("časové_pokrytí", document)
        self.assertNotIn("kontaktní_bod", document)
        self.assertNotIn("podmínky_užití", document["distribuce"][0])

    def test_missing_required_fields_are_logged_with_paths(self):
        dataset = element("dataset", "Test", {
            "typ": "datová sada",
            "kontaktní bod - email": "alice@example.com",
        })
        distribution = element("distribution", "CSV", {
            "typ": "distribuce - soubor ke stažení",
        })
        service_distribution = element("service-distribution", "API", {
            "typ": "distribuce - datová služba",
            "přístupová služba - dokumentace": "https://example.com/docs",
        })
        relationships = [
            ArchimateRelationship(
                identifier="distribution-relation",
                type="Association",
                source="dataset",
                target="distribution",
            ),
            ArchimateRelationship(
                identifier="service-distribution-relation",
                type="Association",
                source="dataset",
                target="service-distribution",
            ),
        ]

        with self.assertLogs("jsonld_creation", level="ERROR") as captured:
            create_jsonld_files(
                parsed_model(
                    [dataset, distribution, service_distribution],
                    relationships,
                )
            )

        message = "\n".join(captured.output)
        for field in (
            "popis",
            "klíčové_slovo",
            "týká_se_pojmu",
            "je_zahrnuta_v_isvs",
            "právní_předpis",
            "kontaktní_bod.jméno",
            "distribuce[0].přístupové_url",
            "distribuce[0].právní_předpis",
            "distribuce[0].podmínky_užití",
            "distribuce[0].formát",
            "distribuce[0].typ_média",
            "distribuce[1].přístupové_url",
            "distribuce[1].právní_předpis",
            "distribuce[1].podmínky_užití",
            "distribuce[1].přístupová_služba.přístupový_bod",
            "distribuce[1].přístupová_služba.právní_předpis",
        ):
            self.assertIn(field, message)


if __name__ == "__main__":
    unittest.main()
