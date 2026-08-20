"""Format-neutral model consumed by the JSON-LD conversion layer."""

from dataclasses import dataclass, field


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
    resolved_properties: dict[str, str | list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class ArchimateRelationship:
    identifier: str | None
    type: str | None
    source: str | None
    target: str | None
    names: list[LangText] = field(default_factory=list)
    documentation: list[LangText] = field(default_factory=list)
    properties: list[ArchimateProperty] = field(default_factory=list)
    resolved_properties: dict[str, str | list[str]] = field(default_factory=dict)
    access_type: str | None = None
    modifier: str | None = None
    is_directed: str | bool | None = None


@dataclass(frozen=True)
class ArchimateModel:
    identifier: str | None
    version: str | None
    names: list[LangText] = field(default_factory=list)
    documentation: list[LangText] = field(default_factory=list)
    properties: list[ArchimateProperty] = field(default_factory=list)
    resolved_properties: dict[str, str | list[str]] = field(default_factory=dict)
    property_definitions: list[PropertyDefinition] = field(default_factory=list)
    elements: list[ArchimateElement] = field(default_factory=list)
    relationships: list[ArchimateRelationship] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedXml:
    root_element_name: str
    model: ArchimateModel | None = None
    source_format: str | None = None
