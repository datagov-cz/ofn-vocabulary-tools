"""Parser for Enterprise Architect UML XMI 2.1 exports.

Only UML objects contained in a package carrying the ``slovnikyPackage``
stereotype (including any nested package) enter the neutral conversion model.
Profile applications supply tagged values and the application name supplies
the special ``typ`` value.
"""

import re
import unicodedata

import ofnDistributionBindings as bindings
from archimate_xml import local_name
from xml_model import (
    ArchimateElement, ArchimateModel, ArchimateRelationship, LangText, ParsedXml,
)


XMI_NAMESPACES = (
    "http://schema.omg.org/spec/XMI/2.1",
    "http://www.omg.org/spec/XMI/20110701",
    "http://www.omg.org/spec/XMI/20131001",
)
UML_RELATIONSHIP_TYPES = {
    "Abstraction", "Aggregation", "Association", "Composition", "Dependency",
    "Generalization", "Realization", "Specialization", "Usage",
}


def attribute(node, name, default=None):
    for key, value in node.attrib.items():
        if local_name(key) == name:
            return value
    return default


def _signature(value):
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", ascii_value.lower())


def _canonical_property_names():
    result = {}
    for constant_name in dir(bindings):
        value = getattr(bindings, constant_name)
        if constant_name.isupper() and isinstance(value, str) and not value.startswith(("@", "http")):
            source_name = value.replace("_", " ")
            result[_signature(source_name)] = source_name
    return result


CANONICAL_PROPERTIES = _canonical_property_names()


def _canonical_property_name(name):
    return CANONICAL_PROPERTIES.get(_signature(name), name.replace("_", " "))


def _uml_type(node):
    tag = local_name(node.tag)
    if tag in ("packagedElement", "ownedMember"):
        value = attribute(node, "type")
        return value.rsplit(":", 1)[-1] if value else None
    return tag


def _is_xmi_root(root):
    namespace = root.tag[1:].split("}", 1)[0] if root.tag.startswith("{") else ""
    return local_name(root.tag).lower() == "xmi" or namespace in XMI_NAMESPACES


def is_ea_xmi(root):
    return _is_xmi_root(root) and any(local_name(node.tag) == "Model" for node in root.iter())


def _stereotype_applications(root):
    by_base_id = {}
    for node in root.iter():
        base_ids = [
            value for key, value in node.attrib.items()
            if local_name(key).startswith("base_") and value
        ]
        for base_id in base_ids:
            by_base_id.setdefault(base_id, []).append(node)
    return by_base_id


def _package_roots(root, nodes_by_id, applications):
    roots = []
    for base_id, items in applications.items():
        if any(_signature(local_name(item.tag)) == "slovnikypackage" for item in items):
            package = nodes_by_id.get(base_id)
            if package is not None and _uml_type(package) == "Package":
                roots.append(package)
    return roots


def _included_nodes(package_roots):
    return {id(node): node for package in package_roots for node in package.iter()}


def _stereotype_name(applications):
    for application in applications:
        name = local_name(application.tag)
        if _signature(name) != "slovnikypackage":
            return name
    return None


def _tagged_values(applications):
    result = {}
    for application in applications:
        for key, value in application.attrib.items():
            key = local_name(key)
            if key in ("id", "type") or key.startswith("base_") or value == "":
                continue
            result[_canonical_property_name(key)] = value
        for tag in application.iter():
            if tag is application or local_name(tag.tag).lower() not in ("tag", "taggedvalue", "taggedvalueproperty"):
                continue
            name = attribute(tag, "name") or attribute(tag, "tag")
            value = attribute(tag, "value") or (tag.text or "")
            if name and value:
                result[_canonical_property_name(name)] = value
    stereotype = _stereotype_name(applications)
    if stereotype:
        result["typ"] = stereotype
    return result


def _names(node, tagged_values):
    """EA's UML name has no language marker; treat it as Czech."""
    name = attribute(node, "name")
    return [LangText(name, "cs")] if name else []


def _documentation(node):
    result = []
    for item in node:
        if local_name(item.tag) != "ownedComment":
            continue
        value = attribute(item, "body") or (item.text or "")
        if value:
            result.append(LangText(value, "cs"))
    return result


def _reference(node, name):
    value = attribute(node, name)
    if value:
        return value.split()[0]
    for item in node:
        if local_name(item.tag) == name:
            return attribute(item, "idref") or attribute(item, "href")
    return None


def _association_endpoints(node, nodes_by_id):
    endpoint_ids = []
    for end in node:
        if local_name(end.tag) in ("ownedEnd", "end"):
            endpoint = attribute(end, "type")
            if endpoint:
                endpoint_ids.append(endpoint)
        elif local_name(end.tag) == "memberEnd":
            referenced_end = nodes_by_id.get(attribute(end, "idref"))
            endpoint = attribute(referenced_end, "type") if referenced_end is not None else None
            if endpoint:
                endpoint_ids.append(endpoint)
    if len(endpoint_ids) < 2:
        for end_id in (attribute(node, "memberEnd") or "").split():
            end = nodes_by_id.get(end_id)
            endpoint = attribute(end, "type") if end is not None else None
            if endpoint and endpoint not in endpoint_ids:
                endpoint_ids.append(endpoint)
    return endpoint_ids[:2]


def _relationship_endpoints(node, relationship_type, nodes_by_id, parent_by_node):
    if relationship_type == "Association":
        endpoints = _association_endpoints(node, nodes_by_id)
        if len(endpoints) == 2:
            return endpoints
    source = _reference(node, "source") or _reference(node, "client") or _reference(node, "specific")
    target = _reference(node, "target") or _reference(node, "supplier") or _reference(node, "general")
    if relationship_type == "Generalization" and not source:
        parent = parent_by_node.get(id(node))
        source = attribute(parent, "id") if parent is not None else None
    return source, target


def _relationship_type(node):
    uml_type = _uml_type(node)
    if uml_type == "Association":
        aggregations = {attribute(item, "aggregation") for item in node if attribute(item, "aggregation")}
        if "composite" in aggregations:
            return "Composition"
        if "shared" in aggregations:
            return "Aggregation"
    return uml_type


def parse_ea_xmi(root):
    all_nodes = list(root.iter())
    nodes_by_id = {attribute(node, "id"): node for node in all_nodes if attribute(node, "id")}
    parent_by_node = {id(child): parent for parent in all_nodes for child in parent}
    applications = _stereotype_applications(root)
    package_roots = _package_roots(root, nodes_by_id, applications)
    included = _included_nodes(package_roots)
    elements, relationships = [], []

    for node in all_nodes:
        if id(node) not in included:
            continue
        # UML properties and association ends also carry a plain ``type``
        # reference. They are structural details, not standalone model
        # elements for the JSON-LD converter.
        if local_name(node.tag) not in (
            "packagedElement", "ownedMember", "Abstraction", "Artifact",
            "Association", "Class", "Component", "DataType", "Dependency",
            "Enumeration", "Generalization", "Object", "Realization", "Usage",
        ):
            continue
        identifier = attribute(node, "id")
        uml_type = _uml_type(node)
        if not identifier or uml_type in (None, "Model", "Package"):
            continue
        node_applications = applications.get(identifier, [])
        tagged_values = _tagged_values(node_applications)
        if uml_type in UML_RELATIONSHIP_TYPES:
            relationship_type = _relationship_type(node)
            source, target = _relationship_endpoints(node, uml_type, nodes_by_id, parent_by_node)
            relationships.append(ArchimateRelationship(
                identifier=identifier,
                type=relationship_type,
                source=source,
                target=target,
                names=_names(node, tagged_values),
                documentation=_documentation(node),
                resolved_properties=tagged_values,
                is_directed=attribute(node, "isDirected") or (
                    "true" if _signature(_stereotype_name(node_applications) or "") == "typvztahu" else None
                ),
            ))
        else:
            elements.append(ArchimateElement(
                identifier=identifier,
                type=uml_type,
                names=_names(node, tagged_values),
                documentation=_documentation(node),
                resolved_properties=tagged_values,
            ))

    model_node = next((node for node in all_nodes if local_name(node.tag) == "Model"), root)
    package_names = [attribute(package, "name") for package in package_roots if attribute(package, "name")]
    model_name = package_names[0] if package_names else attribute(model_node, "name")
    model = ArchimateModel(
        identifier=attribute(model_node, "id"),
        version=attribute(root, "version"),
        names=[LangText(model_name, "cs")] if model_name else [],
        elements=elements,
        relationships=relationships,
    )
    return ParsedXml(local_name(root.tag), model, "ea-xmi-2.1")
