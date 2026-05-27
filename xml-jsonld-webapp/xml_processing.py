from dataclasses import dataclass
from xml.etree import ElementTree


@dataclass(frozen=True)
class ParsedXml:
    root_element_name: str


def local_name(tag):
    """Return a readable element name when the XML uses namespaces."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def parse_xml(xml_bytes):
    root = ElementTree.fromstring(xml_bytes)

    # CUSTOM XML PARSING SETUP:
    # Add project-specific XML reading and transformation logic here.
    # For now, this only extracts the XML root element name.
    return ParsedXml(root_element_name=local_name(root.tag))
