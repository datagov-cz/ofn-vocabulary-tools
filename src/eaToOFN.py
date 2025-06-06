import sys
import os
from typing import List
from lxml import etree  # type: ignore
from ofnClasses import *
from outputToRDF import convertToRDF
from ofnBindings import *
from rdflib import XSD, RDFS

inputLocation = sys.argv[1]
outputLocation = sys.argv[2]


def getBaseInfo(term: Term, element):
    term.id = element.get("base_Class")
    term._iri = element.get(OFN_IRI.lower(), "")
    term.source = element.get(OFN_SOURCE.lower(), "")
    term.related = [x.strip() for x in str(element.get(
        OFN_RELATED.lower(), "")).split(MULTIPLE_VALUE_SEPARATOR)]
    term.alternateName = [(DEFAULT_LANGUAGE, x.strip()) for x in str(element.get(
        OFN_ALTERNATIVE.lower(), "")).split(MULTIPLE_VALUE_SEPARATOR)]
    term.definition = element.get(OFN_DEFINITION.lower(), "")
    term.description = element.get(OFN_DESCRIPTION.lower(), "")
    term.equivalent = [x.strip() for x in str(element.get(
        OFN_EQUIVALENT.lower(), "")).split(MULTIPLE_VALUE_SEPARATOR)]


def get3602023Info(term: Term, element):
    getValueType = element.get(OFN_360_2023_GET.lower(), "")
    if getValueType:
        if getValueType == OFN_360_2023_GET_BASE_REGISTRY.lower():
            term.getValueType = GetValueType.BASE_REGISTRY
        elif getValueType == OFN_360_2023_GET_OTHER_AGENDA.lower():
            term.getValueType = GetValueType.OTHER_AGENDA
        elif getValueType == OFN_360_2023_GET_OWN_AGENDA.lower():
            term.getValueType = GetValueType.OWN_AGENDA
        elif getValueType == OFN_360_2023_GET_OPERATING.lower():
            term.getValueType = GetValueType.OPERATING
    shareValueType = element.get(
        OFN_360_2023_SHARE.lower(), "")
    if shareValueType:
        if shareValueType == OFN_360_2023_SHARE_PUBLIC.lower():
            term.shareValueType = ShareValueType.PUBLIC
        elif shareValueType == OFN_360_2023_SHARE_ON_REQUEST.lower():
            term.shareValueType = ShareValueType.ON_REQUEST
        elif shareValueType == OFN_360_2023_SHARE_FOR_AGENDAS.lower():
            term.shareValueType = ShareValueType.FOR_AGENDAS
        elif shareValueType == OFN_360_2023_SHARE_PRIVATE.lower():
            term.shareValueType = ShareValueType.PRIVATE
    contentValueType = element.get(
        OFN_360_2023_CONTENT.lower(), "")
    if contentValueType:
        if contentValueType == OFN_360_2023_CONTENT_IDENTIFICATION.lower():
            term.contentValueType = ContentValueType.IDENTIFICATION
        elif contentValueType == OFN_360_2023_CONTENT_RECORD.lower():
            term.contentValueType = ContentValueType.RECORD
        elif contentValueType == OFN_360_2023_CONTENT_STATISTICAL.lower():
            term.contentValueType = ContentValueType.STATISTICAL


def getRPPInfo(term: Term, element):
    rppType = element.get(OFN_RPP_TYPE.lower(), "")
    if rppType:
        if rppType == YES.lower():
            term.rppType = RPPType.PUBLIC
        elif rppType == NO.lower():
            term.rppType = RPPType.PRIVATE
    rppShared = element.get(OFN_RPP_SHARED.lower(), "")
    if rppShared:
        if rppShared == YES.lower():
            term.sharedInPPDF = True
        elif rppShared == NO.lower():
            term.sharedInPPDF = False
    term.rppPrivateTypeSource = element.get(OFN_RPP_PRIVATE_SOURCE.lower(), "")


ns = {
    "xmi": "http://schema.omg.org/spec/XMI/2.1",
    "uml": "http://schema.omg.org/spec/UML/2.1",
    "Slovníky": "http://www.sparxsystems.com/profiles/Slovníky/1.0.1"
}

tree = etree.parse(inputLocation, parser=etree.XMLParser(recover=True))
root = tree.getroot()
umlModel = root.find("uml:Model", ns)
slovnikyPackageElements = umlModel.findall(
    ".//Slovníky:slovnikyPackage", ns)
vocabularies: dict[str, Vocabulary] = {}
for slovnikyPackageElement in slovnikyPackageElements:
    vocabularies[slovnikyPackageElement.get("base_Package")] = Vocabulary()
subjectElements = umlModel.findall(
    ".//Slovníky:typSubjektu", ns)
objectElements = umlModel.findall(
    ".//Slovníky:typObjektu", ns)
slovnikyPackageElements = umlModel.findall(
    ".//Slovníky:slovnikyPackage", ns)
tropeElements = umlModel.findall(
    ".//Slovníky:typVlastnosti", ns)
relationshipElements = umlModel.findall(
    ".//Slovníky:typVztahu", ns)
packagedElements = umlModel.findall(".//packagedElement", ns)

for element in subjectElements + objectElements:
    term = TermClass()
    getBaseInfo(term, element)
    # RPP
    term.agenda = element.get(OFN_RPP_AGENDA.lower(), "")
    term.ais = element.get(OFN_RPP_AIS.lower(), "")


for element in tropeElements:
    term = Trope()
    getBaseInfo(term, element)
    get3602023Info(term, element)
    getRPPInfo(term, element)
    datatype: str = element.get(OFN_DATATYPE.lower(), "")
    if datatype:
        if datatype.startswith("http://www.w3.org/2001/XMLSchema#"):
            term.datatype = datatype
        elif datatype == OFN_DATATYPE_BOOLEAN.lower():
            datatype = XSD.boolean
        elif datatype == OFN_DATATYPE_DATE.lower():
            datatype = XSD.date
        elif datatype == OFN_DATATYPE_TIME.lower():
            datatype = XSD.time
        elif datatype == OFN_DATATYPE_DATETIME.lower():
            datatype = XSD.dateTimeStamp
        elif datatype == OFN_DATATYPE_INTEGER.lower():
            datatype = XSD.integer
        elif datatype == OFN_DATATYPE_DECIMAL.lower():
            datatype = XSD.double
        elif datatype == OFN_DATATYPE_IRI.lower():
            datatype = XSD.anyURI
        elif datatype == OFN_DATATYPE_STRING.lower():
            datatype = XSD.string
        else:
            datatype = RDFS.Literal

for element in relationshipElements:
    term = Relationship()
    getBaseInfo(term, element)
    get3602023Info(term, element)
    getRPPInfo(term, element)


for vocabulary in vocabularies.values():
    location = os.path.dirname(outputLocation) + \
        "\\{}.ttl".format(vocabulary.name[DEFAULT_LANGUAGE])
    convertToRDF(vocabulary, DEFAULT_LANGUAGE, outputLocation)
