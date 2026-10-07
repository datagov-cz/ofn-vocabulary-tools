"""Add OFN concept IRIs to an ArchiMate Open Exchange model.

Usage: python ofnIRItoArchi.py MODEL VOCABULARY OUTPUT

VOCABULARY may be an OFN Slovníky JSON/JSON-LD document or Turtle file.
Element and relationship names are matched to concept preferred labels after
Unicode, whitespace, and case normalization. Existing properties are kept.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from lxml import etree


OFN_CONCEPT = "https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem"
SKOS_PREF_LABEL = "http://www.w3.org/2004/02/skos/core#prefLabel"
IDENTIFIER_NAME = "identifikátor"
HTTPS_IRI_REGEX = r"^https://.*$"


def normalized(value: str) -> str:
    """Return the comparison form used for both model names and labels."""
    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


def _values(value):
    """Yield strings from compact or expanded JSON-LD literal structures."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _values(item)
    elif isinstance(value, dict):
        if isinstance(value.get("@value"), str):
            yield value["@value"]
        else:
            for item in value.values():
                yield from _values(item)


def _type_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _type_values(item)
    elif isinstance(value, dict):
        candidate = value.get("@id") or value.get("iri")
        if isinstance(candidate, str):
            yield candidate


def _is_concept(node: dict) -> bool:
    types = node.get("typ", node.get("@type", []))
    return any(value == "Pojem" or value == "slovníky:pojem" or value == str(OFN_CONCEPT)
               for value in _type_values(types))


def _json_concepts(document) -> dict[str, set[str]]:
    concepts: dict[str, set[str]] = defaultdict(set)

    def visit(value):
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if not isinstance(value, dict):
            return
        if _is_concept(value):
            iri = value.get("iri") or value.get("@id")
            labels = (value.get("název") or value.get("skos:prefLabel")
                      or value.get(SKOS_PREF_LABEL))
            if isinstance(iri, str) and _valid_iri(iri):
                for label in _values(labels):
                    if normalized(label):
                        concepts[normalized(label)].add(iri)
        for child_value in value.values():
            visit(child_value)

    visit(document)
    return concepts


def _valid_iri(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and (parsed.netloc or parsed.scheme == "urn"))


def load_concepts(path: Path) -> dict[str, set[str]]:
    """Load normalized preferred label -> IRI mappings from JSON or Turtle."""
    suffix = path.suffix.lower()
    if suffix in {".json", ".jsonld", ".json-ld"}:
        with path.open(encoding="utf-8-sig") as source:
            concepts = _json_concepts(json.load(source))
    elif suffix in {".ttl", ".turtle"}:
        from rdflib import Graph, RDF, SKOS, URIRef

        graph = Graph()
        graph.parse(path, format="turtle")
        concepts = defaultdict(set)
        for subject in graph.subjects(RDF.type, URIRef(OFN_CONCEPT)):
            if not isinstance(subject, URIRef):
                continue
            for label in graph.objects(subject, SKOS.prefLabel):
                if normalized(str(label)):
                    concepts[normalized(str(label))].add(str(subject))
    else:
        raise ValueError("Vocabulary must be JSON, JSON-LD, or Turtle (.ttl)")
    if not concepts:
        raise ValueError(
            "The vocabulary contains no Pojem entries with a preferred label and IRI")
    return concepts


def _local_name(element) -> str:
    return etree.QName(element).localname


def _direct_child(element, name):
    return next((child for child in element if _local_name(child) == name), None)


def _children(element, name):
    return (child for child in element if _local_name(child) == name)


def enrich_model(model_path: Path, vocabulary_path: Path, output_path: Path) -> tuple[int, int]:
    """Write the enriched model and return (matched model objects, added IRIs)."""
    if model_path.resolve() == output_path.resolve():
        raise ValueError("Input and output model paths must differ")
    concepts = load_concepts(vocabulary_path)
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(str(model_path), parser)
    root = tree.getroot()
    if _local_name(root) != "model":
        raise ValueError(
            "The first input is not an ArchiMate Open Exchange model")
    namespace = etree.QName(root).namespace
    def qname(name): return f"{{{namespace}}}{name}" if namespace else name

    identifier_definitions = set()
    definition_ids = set()
    for node in root.iter():
        if _local_name(node) != "propertyDefinition":
            continue
        identifier = node.get("identifier")
        if identifier:
            definition_ids.add(identifier)
            name = _direct_child(node, "name")
            if name is not None and normalized(name.text or "") == normalized(IDENTIFIER_NAME):
                identifier_definitions.add(identifier)

    identifier_definition = sorted(identifier_definitions)[
        0] if identifier_definitions else None
    if identifier_definition is None:
        number = 1
        identifier_definition = "id-property-identifier"
        while identifier_definition in definition_ids:
            number += 1
            identifier_definition = f"id-property-identifier-{number}"
        container = _direct_child(root, "propertyDefinitions")
        if container is None:
            container = etree.Element(qname("propertyDefinitions"))
            # In the Open Exchange schema, property definitions precede views.
            views = _direct_child(root, "views")
            if views is None:
                root.append(container)
            else:
                root.insert(root.index(views), container)
        definition = etree.SubElement(container, qname("propertyDefinition"),
                                      identifier=identifier_definition, type="string")
        etree.SubElement(definition, qname("name")).text = IDENTIFIER_NAME
        identifier_definitions.add(identifier_definition)

    matched = added = 0
    for node in root.iter():
        if _local_name(node) not in {"element", "relationship"}:
            continue
        iris = set()
        for name in _children(node, "name"):
            iris.update(concepts.get(normalized(name.text or ""), ()))
        if not iris:
            continue
        matched += 1
        properties = _direct_child(node, "properties")
        existing = set()
        malformed = []
        has_identifier_property = False
        if properties is not None:
            for prop in _children(properties, "property"):
                if prop.get("propertyDefinitionRef") in identifier_definitions:
                    has_identifier_property = True
                    value = _direct_child(prop, "value")
                    text = (value.text or "").strip() if value is not None else ""
                    if text and re.fullmatch(HTTPS_IRI_REGEX, text):
                        existing.add(text)
                    else:
                        malformed.append((prop, value))

        # A valid identifier means that this object is already assigned: keep
        # it and discard newly matched IRIs. Empty or malformed identifier
        # properties are replaced, while a missing property is created below.
        if existing:
            continue
        ordered_iris = sorted(iris)
        for index, (prop, value) in enumerate(malformed):
            iri = ordered_iris[index % len(ordered_iris)]
            if value is None:
                value = etree.SubElement(prop, qname("value"))
            value.text = iri
            added += 1
        if has_identifier_property:
            continue
        for iri in ordered_iris:
            if properties is None:
                properties = etree.SubElement(node, qname("properties"))
            prop = etree.SubElement(properties, qname("property"),
                                    propertyDefinitionRef=identifier_definition)
            etree.SubElement(prop, qname("value")).text = iri
            added += 1

    tree.write(str(output_path), encoding="utf-8",
               xml_declaration=True, pretty_print=True)
    return matched, added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path,
                        help="ArchiMate Open Exchange XML model")
    parser.add_argument("vocabulary", type=Path,
                        help="OFN vocabulary (.json, .jsonld, or .ttl)")
    parser.add_argument("output", type=Path, help="output ArchiMate XML model")
    args = parser.parse_args()
    try:
        matched, added = enrich_model(args.model, args.vocabulary, args.output)
        print(
            f"Matched {matched} model object(s); added {added} identifier value(s).")
    except (OSError, ValueError, json.JSONDecodeError, etree.XMLSyntaxError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
