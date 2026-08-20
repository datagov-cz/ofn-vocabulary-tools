"""Detect the uploaded XML dialect and dispatch it to its isolated parser."""

from xml.etree import ElementTree

from archimate_xml import local_name, parse_archimate_xml
from ea_xmi import is_ea_xmi, parse_ea_xmi
from xml_model import (  # re-exported for backwards compatibility
    ArchimateElement,
    ArchimateModel,
    ArchimateProperty,
    ArchimateRelationship,
    LangText,
    ParsedXml,
    PropertyDefinition,
)


def parse_xml(xml_bytes):
    root = ElementTree.fromstring(xml_bytes)
    if local_name(root.tag) == "model":
        return parse_archimate_xml(root)
    if is_ea_xmi(root):
        return parse_ea_xmi(root)
    return ParsedXml(root_element_name=local_name(root.tag))


__all__ = [
    "ArchimateElement", "ArchimateModel", "ArchimateProperty",
    "ArchimateRelationship", "LangText", "ParsedXml", "PropertyDefinition",
    "parse_xml",
]
