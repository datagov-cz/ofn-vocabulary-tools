from dataclasses import dataclass, field
from xml.etree import ElementTree


XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


@dataclass(frozen=True)
class LangText:
    value: str
    language: str | None = None


@dataclass(frozen=True)
class ArchimateProperty:
    property_definition_ref: str
    values: list[LangText] = field(default_factory=list)


@dataclass(frozen=True)
class PropertyDefinition:
    identifier: str | None
    type: str | None
    names: list[LangText] = field(default_factory=list)
    documentation: list[LangText] = field(default_factory=list)


@dataclass(frozen=True)
class ArchimateElement:
    identifier: str | None
    type: str | None
    names: list[LangText] = field(default_factory=list)
    documentation: list[LangText] = field(default_factory=list)
    properties: list[ArchimateProperty] = field(default_factory=list)
    resolved_properties: dict[str, str |
                              list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ArchimateRelationship:
    identifier: str | None
    type: str | None
    source: str | None
    target: str | None
    names: list[LangText] = field(default_factory=list)
    documentation: list[LangText] = field(default_factory=list)
    properties: list[ArchimateProperty] = field(default_factory=list)
    resolved_properties: dict[str, str |
                              list[str]] = field(default_factory=dict)
    access_type: str | None = None
    modifier: str | None = None
    is_directed: str | None = None


@dataclass(frozen=True)
class ArchimateModel:
    identifier: str | None
    version: str | None
    names: list[LangText] = field(default_factory=list)
    documentation: list[LangText] = field(default_factory=list)
    properties: list[ArchimateProperty] = field(default_factory=list)
    resolved_properties: dict[str, str |
                              list[str]] = field(default_factory=dict)
    property_definitions: list[PropertyDefinition] = field(
        default_factory=list)
    elements: list[ArchimateElement] = field(default_factory=list)
    relationships: list[ArchimateRelationship] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedXml:
    root_element_name: str
    model: ArchimateModel | None = None


def local_name(tag):
    """Return a readable element name when the XML uses namespaces."""
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def namespaced_attribute(namespace, name):
    return f"{{{namespace}}}{name}"


def child(parent, name):
    for candidate in parent:
        if local_name(candidate.tag) == name:
            return candidate
    return None


def children(parent, name):
    return [candidate for candidate in parent if local_name(candidate.tag) == name]


def parse_lang_texts(parent, tag_name):
    return [
        LangText(
            value=text_node.text or "",
            language=text_node.attrib.get(
                namespaced_attribute(XML_NAMESPACE, "lang")),
        )
        for text_node in children(parent, tag_name)
    ]


def parse_properties(parent):
    properties_container = child(parent, "properties")
    if properties_container is None:
        return []

    parsed_properties = []
    for property_node in children(properties_container, "property"):
        parsed_properties.append(
            ArchimateProperty(
                property_definition_ref=property_node.attrib.get(
                    "propertyDefinitionRef", ""),
                values=parse_lang_texts(property_node, "value"),
            )
        )

    return parsed_properties


def parse_property_definitions(model_node):
    property_definitions_container = child(model_node, "propertyDefinitions")
    if property_definitions_container is None:
        return []

    parsed_definitions = []
    for definition_node in children(property_definitions_container, "propertyDefinition"):
        parsed_definitions.append(
            PropertyDefinition(
                identifier=definition_node.attrib.get("identifier"),
                type=definition_node.attrib.get("type"),
                names=parse_lang_texts(definition_node, "name"),
                documentation=parse_lang_texts(
                    definition_node, "documentation"),
            )
        )

    return parsed_definitions


def property_definition_lookup(property_definitions):
    return {
        definition.identifier: definition
        for definition in property_definitions
        if definition.identifier
    }


def property_definition_name(property_definition):
    if property_definition is None:
        return None

    if property_definition.names:
        return property_definition.names[0].value

    return property_definition.identifier


def add_resolved_property_value(resolved_properties, property_name, value):
    if property_name not in resolved_properties:
        resolved_properties[property_name] = value
        return

    current_value = resolved_properties[property_name]
    if isinstance(current_value, list):
        current_value.append(value)
        return

    resolved_properties[property_name] = [current_value, value]


def resolve_properties(properties, definitions_by_id):
    resolved_properties = {}

    for property_item in properties:
        property_definition = definitions_by_id.get(
            property_item.property_definition_ref)
        property_name = property_definition_name(property_definition)
        if property_name is None:
            property_name = property_item.property_definition_ref

        for value in property_item.values:
            add_resolved_property_value(
                resolved_properties,
                property_name,
                value.value,
            )

    return resolved_properties


def archimate_type(node):
    xsi_type = node.attrib.get(namespaced_attribute(XSI_NAMESPACE, "type"))
    if xsi_type is None:
        return None
    return xsi_type.rsplit(":", 1)[-1]


def parse_elements(model_node, definitions_by_id):
    elements_container = child(model_node, "elements")
    if elements_container is None:
        return []

    parsed_elements = []
    for element_node in children(elements_container, "element"):
        properties = parse_properties(element_node)
        parsed_elements.append(
            ArchimateElement(
                identifier=element_node.attrib.get("identifier"),
                type=archimate_type(element_node),
                names=parse_lang_texts(element_node, "name"),
                documentation=parse_lang_texts(element_node, "documentation"),
                properties=properties,
                resolved_properties=resolve_properties(
                    properties, definitions_by_id),
            )
        )

    return parsed_elements


def parse_relationships(model_node, definitions_by_id):
    relationships_container = child(model_node, "relationships")
    if relationships_container is None:
        return []

    parsed_relationships = []
    for relationship_node in children(relationships_container, "relationship"):
        properties = parse_properties(relationship_node)
        parsed_relationships.append(
            ArchimateRelationship(
                identifier=relationship_node.attrib.get("identifier"),
                type=archimate_type(relationship_node),
                source=relationship_node.attrib.get("source"),
                target=relationship_node.attrib.get("target"),
                names=parse_lang_texts(relationship_node, "name"),
                documentation=parse_lang_texts(
                    relationship_node, "documentation"),
                properties=properties,
                resolved_properties=resolve_properties(
                    properties, definitions_by_id),
                access_type=relationship_node.attrib.get("accessType"),
                modifier=relationship_node.attrib.get("modifier"),
                is_directed=relationship_node.attrib.get("isDirected"),
            )
        )

    return parsed_relationships


def parse_model(model_node):
    property_definitions = parse_property_definitions(model_node)
    definitions_by_id = property_definition_lookup(property_definitions)
    properties = parse_properties(model_node)

    return ArchimateModel(
        identifier=model_node.attrib.get("identifier"),
        version=model_node.attrib.get("version"),
        names=parse_lang_texts(model_node, "name"),
        documentation=parse_lang_texts(model_node, "documentation"),
        properties=properties,
        resolved_properties=resolve_properties(properties, definitions_by_id),
        property_definitions=property_definitions,
        elements=parse_elements(model_node, definitions_by_id),
        relationships=parse_relationships(model_node, definitions_by_id),
    )


def parse_xml(xml_bytes):
    root = ElementTree.fromstring(xml_bytes)

    # CUSTOM XML PARSING SETUP:
    # This skeleton follows the Open Group ArchiMate 3.x Model Exchange
    # structure from archimate3_Model.xsd:
    # - model: identifier, version, name, documentation, properties
    # - elements/element: identifier, xsi:type, name, documentation, properties
    # - relationships/relationship: identifier, xsi:type, source, target,
    #   relationship-specific attributes, name, documentation, properties
    # - propertyDefinitions/propertyDefinition: identifier, type, name,
    #   documentation
    #
    # Add project-specific interpretation, validation, normalization, and
    # transformation rules here as the target JSON-LD mapping is defined.
    model = parse_model(root) if local_name(root.tag) == "model" else None

    return ParsedXml(
        root_element_name=local_name(root.tag),
        model=model,
    )
