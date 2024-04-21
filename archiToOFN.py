import sys

from lxml import etree
from ofnClasses import ClassType, Relationship, Trope, Vocabulary, Term, VocabularyType, getClass, getTrope
from outputToRDF import convertToRDF

# TODO: Vocabularies
# TODO: Cardinalities
# TODO: Security!!!

# TODO
inputLocation = sys.argv[1]
outputLocation = sys.argv[2]


# ARCHIMATE_NAMESPACE = 'http://www.w3.org/2001/XMLSchema-instance'


propertyDefinitions = {}

# XML parsing

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
            if "typ" in termProperties:
                valueTextNormalized = termProperties["typ"][0].strip().lower()
                match valueTextNormalized:
                    case "typ subjektu":
                        term = getClass(term)
                        term.type = ClassType.SUBJECT
                    case "typ objektu":
                        term = getClass(term)
                        term.type = ClassType.OBJECT
                    case "typ vlastnosti":
                        term = getTrope(term)
                        # TODO: domain, datatype
            # Source
            if "zdroj" in termProperties:
                term.source = termProperties["zdroj"][0]
            # Definition
            if "definice" in termProperties:
                term.definition[termProperties["definice"]
                                [1]] = termProperties["definice"][0]
            # Description
            if "popis" in termProperties:
                term.description[termProperties["popis"]
                                 [1]] = termProperties["popis"][0]
            if "datový typ" in termProperties and isinstance(term, Trope):
                term.datatype = termProperties["datový typ"][0]
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
        elif relationshipType == "Composition" and isinstance(domainTerm, Trope):
            domainTerm.target = rangeTerm.iri
        elif relationshipType == "Association":
            isDirected = relationship.attrib.get("isDirected", False)
            if not isDirected or isDirected != "true":
                continue
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
                    case "zdroj":
                        term.source = valueText
                    # Definition
                    case "definice":
                        term.definition[valueLang] = valueText
                    # Description
                    case "popis":
                        term.description[valueLang] = valueText
            for name in names:
                lang = name.attrib['{http://www.w3.org/XML/1998/namespace}lang']
                term.name[lang] = name.text
            vocabulary.terms.append(term)
    if (next(x for x in vocabulary.terms if isinstance(x, Trope) or isinstance(x, Relationship))):
        vocabulary.type = VocabularyType.CONCEPTUAL_MODEL
    convertToRDF(vocabulary, "cs", outputLocation)

# File output

# with open("{}_OFN_Slovník.ttl".format(vocabulary.name), "w") as outputFile:
# pass
