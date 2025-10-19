import sys
from lxml import etree  # type: ignore
from ofnClasses import *
from outputToRDF import convertToRDF
from ofnBindings import *
from outputUtil import testInputString
import warnings

inputLocation = sys.argv[1]
outputLocation = sys.argv[2]
propertyDefinitions = {}


def getSimilar(termProperties, input):
    for x in list(termProperties.keys()):
        if input.lower().strip() in x.lower():
            if termProperties[x] is not None and testInputString(termProperties[x][0]):
                return x
    return False


def getTermFromElement(element, term) -> Term:
    term.id = element.attrib['identifier']
    # Name
    names = element.findall(
        "{http://www.opengroup.org/xsd/archimate/3.0/}name")
    for name in names:
        lang = name.attrib['{http://www.w3.org/XML/1998/namespace}lang']
        term.name[lang] = name.text
        while term.name[lang].endswith("/"):
            term.name[lang] = term.name[lang][:-1]
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
    ofnIRI = getSimilar(termProperties, OFN_IRI)
    if ofnIRI:
        term._iri = termProperties[ofnIRI][0].strip()
    ofnType = getSimilar(termProperties, OFN_TYPE)
    if ofnType:
        valueTextNormalized = termProperties[ofnType][0].strip(
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
    ofnSource = getSimilar(termProperties, OFN_SOURCE)
    if ofnSource:
        term.source = [termProperties[ofnSource][0]]
    # Related source
    ofnRelated = getSimilar(termProperties, OFN_RELATED)
    if ofnRelated:
        term.related += [x.strip() for x in termProperties[ofnRelated]
                         [0].split(MULTIPLE_VALUE_SEPARATOR)]
    # Alternative name
    ofnAlternate = getSimilar(termProperties, OFN_ALTERNATIVE)
    if ofnAlternate:
        term.alternateName += [(DEFAULT_LANGUAGE, x.strip()) for x in termProperties[ofnAlternate]
                               [0].split(MULTIPLE_VALUE_SEPARATOR)]
    # Definition
    ofnDefinition = getSimilar(termProperties, OFN_DEFINITION)
    if ofnDefinition:
        term.definition[termProperties[ofnDefinition]
                        [1]] = termProperties[ofnDefinition][0]
    # Description
    ofnDescription = getSimilar(termProperties, OFN_DESCRIPTION)
    if ofnDescription:
        term.description[termProperties[ofnDescription]
                         [1]] = termProperties[ofnDescription][0]
    ofnDatatype = getSimilar(termProperties, OFN_DATATYPE)
    if ofnDatatype and isinstance(term, Trope):
        term.datatype = termProperties[ofnDatatype][0]
    # Equivalent
    ofnEquivalent = getSimilar(termProperties, OFN_EQUIVALENT)
    if ofnEquivalent:
        term.equivalent = [x.strip() for x in termProperties[ofnEquivalent][0].split(
            MULTIPLE_VALUE_SEPARATOR)]

    # RPP
    ofnAIS = getSimilar(termProperties, OFN_RPP_AIS)
    if ofnAIS and isinstance(term, TermClass):
        term.ais = termProperties[ofnAIS][0]
    ofnAgenda = getSimilar(termProperties, OFN_RPP_AGENDA)
    if ofnAgenda and isinstance(term, TermClass):
        term.agenda = termProperties[ofnAgenda][0]
    ofnRPPtype = getSimilar(termProperties, OFN_RPP_TYPE)
    if ofnRPPtype and (
            isinstance(term, Trope) or isinstance(term, Relationship)):
        if termProperties[ofnRPPtype][0].strip().lower() == YES.lower():
            term.rppType = RPPType.PUBLIC
        elif termProperties[ofnRPPtype][0].strip().lower() == NO.lower():
            term.rppType = RPPType.PRIVATE
        else:
            warnings.warn("warn")
    ofnShared = getSimilar(termProperties, OFN_RPP_SHARED)
    if ofnShared and (
            isinstance(term, Trope) or isinstance(term, Relationship)):
        if termProperties[ofnShared][0].strip().lower() == YES.lower():
            term.sharedInPPDF = True
        elif termProperties[ofnShared][0].strip().lower() == NO.lower():
            term.sharedInPPDF = False
        else:
            warnings.warn("warn")
    ofnPrivate = getSimilar(termProperties, OFN_RPP_PRIVATE_SOURCE)
    if ofnPrivate and (
            isinstance(term, Trope) or isinstance(term, Relationship)):
        term.rppPrivateTypeSource = termProperties[ofnPrivate][0]

    # 360
    ofn360get = getSimilar(termProperties, OFN_360_2023_GET)
    if ofn360get and isinstance(term, Trope):
        get360 = termProperties[ofn360get][0].strip().lower()
        if OFN_360_2023_GET_BASE_REGISTRY.lower() in get360:
            term.getValueType = GetValueType.BASE_REGISTRY
        elif OFN_360_2023_GET_OTHER_AGENDA.lower() in get360:
            term.getValueType = GetValueType.OTHER_AGENDA
        elif OFN_360_2023_GET_OWN_AGENDA.lower() in get360:
            term.getValueType = GetValueType.OWN_AGENDA
        elif OFN_360_2023_GET_OPERATING.lower() in get360:
            term.getValueType = GetValueType.OPERATING
    ofn360share = getSimilar(termProperties, OFN_360_2023_SHARE)
    if ofn360share and isinstance(term, Trope):
        share360 = termProperties[ofn360share][0].strip().lower()
        if OFN_360_2023_SHARE_PUBLIC.lower() in share360:
            term.shareValueType.append(ShareValueType.PUBLIC)
        elif OFN_360_2023_SHARE_ON_REQUEST.lower() in share360:
            term.shareValueType.append(ShareValueType.ON_REQUEST)
        elif OFN_360_2023_SHARE_FOR_AGENDAS.lower() in share360:
            term.shareValueType.append(ShareValueType.FOR_AGENDAS)
        elif OFN_360_2023_SHARE_PRIVATE.lower() in share360:
            term.shareValueType.append(ShareValueType.PRIVATE)
    ofn360content = getSimilar(termProperties, OFN_360_2023_CONTENT)
    if ofn360content and isinstance(term, Trope):
        content360 = termProperties[ofn360content][0].strip().lower()
        if OFN_360_2023_CONTENT_IDENTIFICATION.lower() in content360:
            term.contentValueType = ContentValueType.IDENTIFICATION
        elif OFN_360_2023_CONTENT_RECORD.lower() in content360:
            term.contentValueType = ContentValueType.RECORD
        elif OFN_360_2023_CONTENT_STATISTICAL.lower() in content360:
            term.contentValueType = ContentValueType.STATISTICAL
    return term


with open(inputLocation, "r", encoding="utf-8") as inputFile:
    tree = etree.parse(inputLocation, parser=etree.XMLParser())
    root = tree.getroot()
    vocabularyNameElement = root.find(
        "{http://www.opengroup.org/xsd/archimate/3.0/}name")
    vocabularyName: str = "Nepojmenovaný slovník"
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
        if name is not None and name.text is not None:
            propertyDefinitions[vocabularyPropertyElement.attrib['identifier']
                                ] = getattr(name, "text", "name").lower()
    vocabularyPropertyElements = root.findall(
        "./{http://www.opengroup.org/xsd/archimate/3.0/}properties/{http://www.opengroup.org/xsd/archimate/3.0/}property")
    vocabularyProperties: dict[str, tuple[str, str]] = {}

    for vocabularyPropertyElement in vocabularyPropertyElements:
        identifier = vocabularyPropertyElement.attrib['propertyDefinitionRef']
        value = vocabularyPropertyElement.find(
            "{http://www.opengroup.org/xsd/archimate/3.0/}value")
        valueLang = value.attrib['{http://www.w3.org/XML/1998/namespace}lang']
        valueText = value.text
        if valueText is None:
            continue
        propertyType = propertyDefinitions[identifier]
        vocabularyProperties[propertyType] = (valueText.lower(), valueLang)

    ofnLKOD = getSimilar(vocabularyProperties, OFN_LKOD)
    if ofnLKOD:
        vocabulary.lkod = vocabularyProperties[ofnLKOD][0]

    ofnDescription = getSimilar(vocabularyProperties, OFN_DESCRIPTION)
    if ofnDescription:
        vocabulary.description[DEFAULT_LANGUAGE] = vocabularyProperties[ofnDescription][0]

    for element in elements:
        if element.attrib['{http://www.w3.org/2001/XMLSchema-instance}type'] == "BusinessObject":
            vocabulary.terms.append(getTermFromElement(element, Term()))

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
        if domainTerm is None or rangeTerm is None:
            continue
        relationshipType = relationship.attrib['{http://www.w3.org/2001/XMLSchema-instance}type']
        if relationshipType == "Specialization":
            domainTerm.subClassOf.append(
                rangeTerm.getIRI(vocabulary, DEFAULT_LANGUAGE))
        elif relationshipType == "Composition" and isinstance(rangeTerm, Trope):
            rangeTerm.target = domainTerm.getIRI(vocabulary, DEFAULT_LANGUAGE)
        elif relationshipType == "Association":
            isDirected = relationship.attrib.get("isDirected", False)
            if not isDirected or isDirected != "true":
                warnings.warn("")
                continue
            term = getTermFromElement(relationship, Relationship(domainTerm.getIRI(
                vocabulary, DEFAULT_LANGUAGE), rangeTerm.getIRI(vocabulary, DEFAULT_LANGUAGE)))
            vocabulary.terms.append(term)
    try:
        if next(x for x in vocabulary.terms if isinstance(x, Trope) or isinstance(x, Relationship)):
            vocabulary.type = VocabularyType.CONCEPTUAL_MODEL
    except:
        pass

    convertToRDF(vocabulary, DEFAULT_LANGUAGE, outputLocation)
