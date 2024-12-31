import sys
from lxml import etree  # type: ignore
from ofnClasses import ClassType, Relationship, Trope, Vocabulary, Term, VocabularyType, getClass, getTrope
from outputToRDF import convertToRDF
from ofnBindings import *
from outputUtil import testInputString
import warnings

# TODO: Security!!!
# TODO: Support multiple vocabularies?
# ARCHIMATE_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'

inputLocation = "C:\\Users\\alice\\Documents\\GitHub\\ofn-vocabulary-tools\\Slovník zákona o silničním provozu.xml"
outputLocation = "output.ttl"
propertyDefinitions = {}

with open(inputLocation, "r", encoding="utf-8") as inputFile:
    tree = etree.parse(inputLocation, parser=etree.XMLParser())
    root = tree.getroot()
    vocabularyNameElement = root.find(
        "{http://www.opengroup.org/xsd/archimate/3.0/}name")
    vocabularyName: str = "slovník"
    if vocabularyNameElement is not None:
        vocabularyName = vocabularyNameElement.text
    else:
        raise LookupError(
            "Cannot find model name. Are you sure you are passing an Archi export?")
    vocabulary = Vocabulary()
    DEFAULT_LANGUAGE = vocabularyNameElement.attrib['{http://www.w3.org/XML/1998/namespace}lang']
    vocabulary.name[DEFAULT_LANGUAGE] = vocabularyName
    properties = root.findall(
        ".//{http://www.opengroup.org/xsd/archimate/3.0/}propertyDefinition[@identifier]")
    elements = root.findall(
        ".//{http://www.opengroup.org/xsd/archimate/3.0/}element[@{http://www.w3.org/2001/XMLSchema-instance}type]")
    relationships = root.findall(
        ".//{http://www.opengroup.org/xsd/archimate/3.0/}relationship[@{http://www.w3.org/2001/XMLSchema-instance}type]")

    # Vocabulary info
    for vocabularyPropertyElement in properties:
        name = vocabularyPropertyElement.find(
            ".//{http://www.opengroup.org/xsd/archimate/3.0/}name")
        propertyDefinitions[vocabularyPropertyElement.attrib['identifier']
                            ] = getattr(name, "text", "name")
    vocabularyPropertyElements = root.findall(
        "./{http://www.opengroup.org/xsd/archimate/3.0/}properties/{http://www.opengroup.org/xsd/archimate/3.0/}property")
    vocabularyProperties: dict[str, tuple[str, str]] = {}

    for vocabularyPropertyElement in vocabularyPropertyElements:
        identifier = vocabularyPropertyElement.attrib['propertyDefinitionRef']
        value = vocabularyPropertyElement.find(
            "{http://www.opengroup.org/xsd/archimate/3.0/}value")
        valueLang = value.attrib['{http://www.w3.org/XML/1998/namespace}lang']
        valueText = value.text
        propertyType = propertyDefinitions[identifier]
        vocabularyProperties[propertyType] = (valueText.lower(), valueLang)

    if OFN_LKOD.lower() in vocabularyProperties:
        vocabulary.lkod = vocabularyProperties[OFN_LKOD.lower()][0]

    if OFN_DESCRIPTION.lower() in vocabularyProperties:
        vocabulary.description[DEFAULT_LANGUAGE] = vocabularyProperties[OFN_DESCRIPTION.lower(
        )][0]

    for element in elements:
        if element.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == "BusinessObject":
            term = Term()
            term.id = element.attrib['identifier']
            # Name
            names = element.findall(
                "{http://www.opengroup.org/xsd/archimate/3.0/}name")
            for name in names:
                lang = name.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                term.name[lang] = name.text
            # Properties
            termProperties: dict[str, tuple[str, str]] = {}
            termPropertyElements = element.findall(
                ".//{http://www.opengroup.org/xsd/archimate/3.0/}property")
            for termPropertyElement in termPropertyElements:
                identifier = termPropertyElement.attrib['propertyDefinitionRef']
                value = termPropertyElement.find(
                    "{http://www.opengroup.org/xsd/archimate/3.0/}value")
                valueLang = value.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                valueText = value.text
                propertyType = propertyDefinitions[identifier]
                termProperties[propertyType] = (valueText, valueLang)
            if OFN_TYPE.lower() in termProperties and termProperties[OFN_TYPE.lower()][0] is not None:
                valueTextNormalized = termProperties[OFN_TYPE.lower()][0].strip(
                ).lower()
                if valueTextNormalized == OFN_SUBJECT_TYPE.lower():
                    term = getClass(term)
                    term.type = ClassType.SUBJECT
                elif valueTextNormalized == OFN_OBJECT_TYPE.lower():
                    term = getClass(term)
                    term.type = ClassType.OBJECT
                elif valueTextNormalized == OFN_TROPE_TYPE.lower():
                    term = getTrope(term)
            # Source
            if OFN_SOURCE.lower() in termProperties:
                term.source = termProperties[OFN_SOURCE.lower()][0]
            # Related source
            if OFN_RELATED.lower() in termProperties and testInputString(termProperties[OFN_RELATED.lower()][0]):
                term.related += [x.strip() for x in termProperties[OFN_SOURCE.lower()]
                                 [0].split(MULTIPLE_VALUE_SEPARATOR)]
            # Alternative name
            if OFN_ALTERNATIVE.lower() in termProperties and testInputString(termProperties[OFN_ALTERNATIVE.lower()][0]):
                term.alternateName += [(DEFAULT_LANGUAGE, x.strip()) for x in termProperties[OFN_ALTERNATIVE.lower()]
                                       [0].split(MULTIPLE_VALUE_SEPARATOR)]
            # Definition
            if OFN_DEFINITION.lower() in termProperties:
                term.definition[termProperties[OFN_DEFINITION.lower()]
                                [1]] = termProperties[OFN_DEFINITION.lower()][0]
            # Description
            if OFN_DESCRIPTION.lower() in termProperties:
                term.description[termProperties[OFN_DESCRIPTION.lower()]
                                 [1]] = termProperties[OFN_DESCRIPTION.lower()][0]
            if OFN_DATATYPE.lower() in termProperties and isinstance(term, Trope):
                term.datatype = termProperties[OFN_DATATYPE.lower()][0]
            vocabulary.terms.append(term)

    for relationship in relationships:
        identifier = relationship.attrib['identifier']
        domain = relationship.attrib['source']
        range = relationship.attrib['target']
        domainTerm = None
        rangeTerm = None
        for term in vocabulary.terms:
            if term.id == domain:
                domainTerm = term
            if term.id == range:
                rangeTerm = term
            if domainTerm is not None and rangeTerm is not None:
                break
        relationshipType = relationship.attrib['{http://www.w3.org/2001/XMLSchema-instance}type']
        if domainTerm is None or rangeTerm is None:
            continue
        if relationshipType == "Specialization":
            # FIXME
            domainTerm.subClassOf.append(rangeTerm.iri)
        elif relationshipType == "Composition" and isinstance(rangeTerm, Trope):
            rangeTerm.target = domainTerm.iri
        elif relationshipType == "Association":
            isDirected = relationship.attrib.get("isDirected", False)
            if not isDirected or isDirected != "true":
                warnings.warn("")
                continue
            # FIXME
            term = Relationship(domainTerm.getIRI(
                vocabulary, DEFAULT_LANGUAGE), rangeTerm.getIRI(vocabulary, DEFAULT_LANGUAGE))
            term.id = identifier
            # Name
            names = relationship.findall(
                "{http://www.opengroup.org/xsd/archimate/3.0/}name")
            for name in names:
                lang = name.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                term.name[lang] = name.text
            # Properties
            termPropertyElements = relationship.findall(
                ".//{http://www.opengroup.org/xsd/archimate/3.0/}property")
            for termPropertyElement in termPropertyElements:
                identifier = termPropertyElement.attrib['propertyDefinitionRef']
                value = termPropertyElement.find(
                    ".//{http://www.opengroup.org/xsd/archimate/3.0/}value")
                valueLang = value.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                valueText = value.text
                propertyType = propertyDefinitions[identifier]
                if propertyType == OFN_SOURCE.lower():
                    term.source = valueText
                elif propertyType == OFN_DEFINITION.lower():
                    term.definition[valueLang] = valueText
                elif propertyType == OFN_DESCRIPTION.lower():
                    term.description[valueLang] = valueText
            for name in names:
                lang = name.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                term.name[lang] = name.text
            vocabulary.terms.append(term)
    if (next(x for x in vocabulary.terms if isinstance(x, Trope) or isinstance(x, Relationship))):
        vocabulary.type = VocabularyType.CONCEPTUAL_MODEL
    convertToRDF(vocabulary, DEFAULT_LANGUAGE, outputLocation)