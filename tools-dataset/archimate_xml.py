"""Parser for Open Group ArchiMate Model Exchange XML."""

from xml_model import (
    ArchimateElement, ArchimateModel, ArchimateProperty,
    ArchimateRelationship, LangText, ParsedXml, PropertyDefinition,
)

XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def namespaced_attribute(namespace, name):
    return f"{{{namespace}}}{name}"


def child(parent, name):
    return next((item for item in parent if local_name(item.tag) == name), None)


def children(parent, name):
    return [item for item in parent if local_name(item.tag) == name]


def parse_lang_texts(parent, tag_name):
    return [LangText(
        node.text or "",
        node.attrib.get(namespaced_attribute(XML_NAMESPACE, "lang")),
    ) for node in children(parent, tag_name)]


def parse_properties(parent):
    container = child(parent, "properties")
    if container is None:
        return []
    return [ArchimateProperty(
        node.attrib.get("propertyDefinitionRef", ""),
        parse_lang_texts(node, "value"),
    ) for node in children(container, "property")]


def parse_property_definitions(model_node):
    container = child(model_node, "propertyDefinitions")
    if container is None:
        return []
    return [PropertyDefinition(
        node.attrib.get("identifier"), node.attrib.get("type"),
        parse_lang_texts(node, "name"), parse_lang_texts(node, "documentation"),
    ) for node in children(container, "propertyDefinition")]


def add_resolved_property_value(properties, name, value):
    if name not in properties:
        properties[name] = value
    elif isinstance(properties[name], list):
        properties[name].append(value)
    else:
        properties[name] = [properties[name], value]


def resolve_properties(properties, definitions):
    by_id = {item.identifier: item for item in definitions if item.identifier}
    result = {}
    for item in properties:
        definition = by_id.get(item.property_definition_ref)
        name = definition.names[0].value if definition and definition.names else item.property_definition_ref
        for value in item.values:
            add_resolved_property_value(result, name, value.value)
    return result


def archimate_type(node):
    value = node.attrib.get(namespaced_attribute(XSI_NAMESPACE, "type"))
    return value.rsplit(":", 1)[-1] if value else None


def parse_model(model_node):
    definitions = parse_property_definitions(model_node)
    properties = parse_properties(model_node)
    elements_container = child(model_node, "elements")
    relationships_container = child(model_node, "relationships")
    elements, relationships = [], []
    if elements_container is not None:
        for node in children(elements_container, "element"):
            node_properties = parse_properties(node)
            elements.append(ArchimateElement(
                node.attrib.get("identifier"), archimate_type(node),
                parse_lang_texts(node, "name"), parse_lang_texts(node, "documentation"),
                node_properties, resolve_properties(node_properties, definitions),
            ))
    if relationships_container is not None:
        for node in children(relationships_container, "relationship"):
            node_properties = parse_properties(node)
            relationships.append(ArchimateRelationship(
                node.attrib.get("identifier"), archimate_type(node),
                node.attrib.get("source"), node.attrib.get("target"),
                parse_lang_texts(node, "name"), parse_lang_texts(node, "documentation"),
                node_properties, resolve_properties(node_properties, definitions),
                node.attrib.get("accessType"), node.attrib.get("modifier"),
                node.attrib.get("isDirected"),
            ))
    return ArchimateModel(
        model_node.attrib.get("identifier"), model_node.attrib.get("version"),
        parse_lang_texts(model_node, "name"), parse_lang_texts(model_node, "documentation"),
        properties, resolve_properties(properties, definitions), definitions,
        elements, relationships,
    )


def parse_archimate_xml(root):
    return ParsedXml(local_name(root.tag), parse_model(root), "archimate")
