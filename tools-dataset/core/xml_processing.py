"""Detect the uploaded XML dialect and dispatch it to its isolated parser."""

import logging
from xml.etree import ElementTree

from archi.parser import local_name, parse_archimate_xml
from ea.parser import is_ea_xmi, parse_ea_xmi
from .models import (  # re-exported for backwards compatibility
    ArchimateElement,
    ArchimateModel,
    ArchimateProperty,
    ArchimateRelationship,
    LangText,
    ParsedXml,
    PropertyDefinition,
)


logger = logging.getLogger(__name__)


def parse_xml(xml_bytes):
    logger.debug("Parsing uploaded XML (%d bytes)", len(xml_bytes))
    root = ElementTree.fromstring(xml_bytes)
    root_name = local_name(root.tag)
    if root_name == "model":
        logger.info("Detected ArchiMate Model Exchange XML input")
        return parse_archimate_xml(root)
    if is_ea_xmi(root):
        logger.info("Detected Enterprise Architect XMI 2.1 input")
        return parse_ea_xmi(root)
    logger.warning("Unsupported XML input with root element %s", root_name)
    return ParsedXml(root_element_name=root_name)


__all__ = [
    "ArchimateElement", "ArchimateModel", "ArchimateProperty",
    "ArchimateRelationship", "LangText", "ParsedXml", "PropertyDefinition",
    "parse_xml",
]
