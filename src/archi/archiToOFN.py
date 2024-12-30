import sys
import archiBindings

from lxml import etree
from src.util.ofnClasses import ClassType, Relationship, Trope, Vocabulary, Term, VocabularyType, getClass, getTrope
from src.output.outputToRDF import convertToRDF
from util.ofnBindings import MULTIPLE_VALUE_SEPARATOR

# TODO: Security!!!
# TODO: Support multiple vocabularies?
# ARCHIMATE_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'

inputLocation = sys.argv[1]
outputLocation = sys.argv[2]
propertyDefinitions = {}

with open(inputLocation, "r", encoding="utf-8") as inputFile:
    tree = etree.parse(inputLocation, parser=etree.XMLParser())
    root = tree.getroot()
    vocabularyNameElement = root.find(
        "{http://www.opengroup.org/xsd/archimate/3.0/}name")
    vocabularyName: str = "slovník"
    defaultLanguage: str = "cs"
    if vocabularyNameElement is not None:
        vocabularyName = vocabularyNameElement.text
    else:
        raise LookupError(
            "Cannot find model name. Are you sure you are passing an Archi export?")
    vocabulary = Vocabulary()
    defaultLanguage = vocabularyNameElement.attrib['{http://www.w3.org/XML/1998/namespace}lang']
    vocabulary.name[defaultLanguage] = vocabularyName
    properties = root.findall(
        ".//{http://www.opengroup.org/xsd/archimate/3.0/}propertyDefinition[@identifier]")
    elements = root.findall(
        ".//{http://www.opengroup.org/xsd/archimate/3.0/}element[@{http://www.w3.org/2001/XMLSchema-instance}type]")
    relationships = root.findall(
        ".//{http://www.opengroup.org/xsd/archimate/3.0/}relationship[@{http://www.w3.org/2001/XMLSchema-instance}type]")
    for property in properties:
        name = property.find(
            ".//{http://www.opengroup.org/xsd/archimate/3.0/}name")
        propertyDefinitions[property.attrib['identifier']
                            ] = getattr(name, "text", "name")
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
            if archiBindings.OFN_TYPE in termProperties and termProperties[archiBindings.OFN_TYPE][0] is not None:
                valueTextNormalized = termProperties[archiBindings.OFN_TYPE][0].strip(
                ).lower()
                match valueTextNormalized:
                    case archiBindings.OFN_SUBJECT_TYPE:
                        term = getClass(term)
                        term.type = ClassType.SUBJECT
                    case archiBindings.OFN_OBJECT_TYPE:
                        term = getClass(term)
                        term.type = ClassType.OBJECT
                    case archiBindings.OFN_TROPE_TYPE:
                        term = getTrope(term)
            # Source
            if archiBindings.OFN_RELATION in termProperties:
                term.source = termProperties[archiBindings.OFN_RELATION][0]
            # Related source
            if archiBindings.OFN_RELATED in termProperties:
                term.related += [x.strip() for x in termProperties[archiBindings.OFN_RELATION]
                                 [0].split(MULTIPLE_VALUE_SEPARATOR)]
            # Alternative name
            if archiBindings.OFN_ALTERNATIVE in termProperties:
                term.alternateName += [(defaultLanguage, x.strip()) for x in termProperties[archiBindings.OFN_RELATION]
                                       [0].split(MULTIPLE_VALUE_SEPARATOR)]
            # Definition
            if archiBindings.OFN_DEFINITION in termProperties:
                term.definition[termProperties[archiBindings.OFN_DEFINITION]
                                [1]] = termProperties[archiBindings.OFN_DEFINITION][0]
            # Description
            if archiBindings.OFN_DESCRIPTION in termProperties:
                term.description[termProperties[archiBindings.OFN_DESCRIPTION]
                                 [1]] = termProperties[archiBindings.OFN_DESCRIPTION][0]
            if archiBindings.OFN_DATATYPE in termProperties and isinstance(term, Trope):
                term.datatype = termProperties[archiBindings.OFN_DATATYPE][0]
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
            domainTerm.subClassOf.append(rangeTerm.iri)
        elif relationshipType == "Composition" and isinstance(rangeTerm, Trope):
            rangeTerm.target = domainTerm.iri
        elif relationshipType == "Association":
            isDirected = relationship.attrib.get("isDirected", False)
            if not isDirected or isDirected != "true":
                continue
            # FIXME
            term = Relationship(domainTerm.getIRI(
                vocabulary, defaultLanguage), rangeTerm.getIRI(vocabulary, defaultLanguage))
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
                match propertyType:
                    # Not interested in type
                    # Source
                    case archiBindings.OFN_RELATION:
                        term.source = valueText
                    # Definition
                    case archiBindings.OFN_DEFINITION:
                        term.definition[valueLang] = valueText
                    # Description
                    case archiBindings.OFN_DESCRIPTION:
                        term.description[valueLang] = valueText
            for name in names:
                lang = name.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                term.name[lang] = name.text
            vocabulary.terms.append(term)
    if (next(x for x in vocabulary.terms if isinstance(x, Trope) or isinstance(x, Relationship))):
        vocabulary.type = VocabularyType.CONCEPTUAL_MODEL
    convertToRDF(vocabulary, "cs", outputLocation)
