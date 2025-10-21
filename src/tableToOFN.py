from typing import List
import openpyxl  # type: ignore
import sys

from rdflib import RDFS, XSD
from ofnClasses import *
from outputToRDF import convertToRDF
from ofnBindings import *
import warnings


def getSimilar(arr: List[str], target: str) -> int:
    for i, x in enumerate(arr):
        if x is not None and target.lower() in x.lower():
            return i
    return -1


def xlsxToSheets(file: str):
    soSheet = None
    itSheet = None
    rlSheet = None
    vcSheet = None
    if file.endswith("xlsx"):
        wb = openpyxl.load_workbook(file, data_only=True)
        if SHEET_VOCABULARY in wb:
            vcSheet = wb[SHEET_VOCABULARY]
        soSheet = wb[SHEET_CLASS]
        itSheet = wb[SHEET_TROPE]
        rlSheet = wb[SHEET_RELATIONSHIP]

    if soSheet is not None and itSheet is not None and rlSheet is not None:
        return (soSheet, itSheet, rlSheet, vcSheet)
    else:
        raise Exception()


def soSheetToOFN(sheet) -> List[TermClass]:
    nameIndex = -1
    descriptionIndex = -1
    definitionIndex = -1
    sourceIndex = -1
    subClassOfIndex = -1
    equivalentIndex = -1
    aisIndex = -1
    agendaIndex = -1
    iriIndex = -1
    typeIndex = -1
    relatedSourceIndex = -1
    alternativeNameIndex = -1
    sos = []
    for lst in sheet:
        row = [cell.value for cell in lst]
        if nameIndex == -1:
            nameIndex = getSimilar(row, OFN_NAME)
            descriptionIndex = getSimilar(row, OFN_DESCRIPTION)
            definitionIndex = getSimilar(row, OFN_DEFINITION)
            sourceIndex = getSimilar(row, OFN_SOURCE)
            subClassOfIndex = getSimilar(row, OFN_SUBCLASS)
            equivalentIndex = getSimilar(row, OFN_EQUIVALENT)
            iriIndex = getSimilar(row, OFN_IRI)
            aisIndex = getSimilar(row, OFN_RPP_AIS)
            agendaIndex = getSimilar(row, OFN_RPP_AGENDA)
            typeIndex = getSimilar(row, OFN_TYPE)
            relatedSourceIndex = getSimilar(row, OFN_RELATED)
            alternativeNameIndex = getSimilar(row, OFN_ALTERNATIVE)
            continue
        else:
            term = TermClass()
            if row[nameIndex] is None:
                warnings.warn("warn")
                continue
            term.name = {DEFAULT_LANGUAGE: row[nameIndex]}
            if (row[typeIndex]):
                if row[typeIndex].strip().lower() == OFN_SUBJECT.lower():
                    term.type = ClassType.SUBJECT
                elif row[typeIndex].strip().lower() == OFN_OBJECT.lower():
                    term.type = ClassType.OBJECT
                else:
                    warnings.warn("warn")
            if row[definitionIndex]:
                term.definition = {
                    DEFAULT_LANGUAGE: row[definitionIndex].strip()}
            if row[descriptionIndex]:
                term.description = {
                    DEFAULT_LANGUAGE: row[descriptionIndex].strip()}
            if row[sourceIndex]:
                term.source = [x.strip()
                               for x in row[sourceIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[subClassOfIndex]:
                term.subClassOf += [x.strip()
                                    for x in row[subClassOfIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[equivalentIndex]:
                term.equivalent += [x.strip()
                                    for x in row[equivalentIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[iriIndex]:
                term._iri = row[iriIndex].strip()
            if row[aisIndex]:
                term.ais = str(row[aisIndex]).strip()
            if row[agendaIndex]:
                term.agenda = row[agendaIndex].strip()
            if row[relatedSourceIndex]:
                term.related += [x.strip()
                                 for x in row[relatedSourceIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[alternativeNameIndex]:
                term.alternateName += [(DEFAULT_LANGUAGE, x.strip())
                                       for x in row[alternativeNameIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            sos.append(term)
    return sos


def itSheetToOFN(sheet) -> List[Trope]:
    termClassIndex = -1
    datatypeIndex = -1
    nameIndex = -1
    descriptionIndex = -1
    definitionIndex = -1
    sourceIndex = -1
    subClassOfIndex = -1
    equivalentIndex = -1
    sharedInPPDFIndex = -1
    rppTypeIndex = -1
    rppPrivateTypeSourceIndex = -1
    iriIndex = -1
    relatedSourceIndex = -1
    alternativeNameIndex = -1
    get360Index = -1
    share360Index = -1
    content360Index = -1
    tropes = []
    for lst in sheet:
        row = [cell.value for cell in lst]
        if nameIndex == -1:
            nameIndex = getSimilar(row, OFN_NAME)
            descriptionIndex = getSimilar(row, OFN_DESCRIPTION)
            definitionIndex = getSimilar(row, OFN_DEFINITION)
            sourceIndex = getSimilar(row, OFN_SOURCE)
            subClassOfIndex = getSimilar(row, OFN_SUBCLASS)
            equivalentIndex = getSimilar(row, OFN_EQUIVALENT)
            iriIndex = getSimilar(row, OFN_IRI)
            relatedSourceIndex = getSimilar(row, OFN_RELATED)
            alternativeNameIndex = getSimilar(row, OFN_ALTERNATIVE)
            get360Index = getSimilar(row, OFN_360_2023_GET)
            share360Index = getSimilar(row, OFN_360_2023_SHARE)
            content360Index = getSimilar(row, OFN_360_2023_CONTENT)
            termClassIndex = getSimilar(row, OFN_SUBJECT_OR_OBJECT)
            datatypeIndex = getSimilar(row, OFN_DATATYPE)
            sharedInPPDFIndex = getSimilar(row, OFN_RPP_SHARED)
            rppTypeIndex = getSimilar(row, OFN_RPP_TYPE)
            rppPrivateTypeSourceIndex = getSimilar(row, OFN_RPP_PRIVATE_SOURCE)
            continue
        else:
            if row[nameIndex] is None or row[termClassIndex] is None:
                continue
            term = Trope()
            term.name = {DEFAULT_LANGUAGE: row[nameIndex].strip()}
            term.target = row[termClassIndex].strip()
            if row[definitionIndex]:
                term.definition = {
                    DEFAULT_LANGUAGE: row[definitionIndex].strip()}
            if row[descriptionIndex]:
                term.description = {
                    DEFAULT_LANGUAGE: row[descriptionIndex].strip()}
            if row[sourceIndex]:
                term.source = [x.strip()
                               for x in row[sourceIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[subClassOfIndex]:
                term.subClassOf += [x.strip()
                                    for x in row[subClassOfIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[equivalentIndex]:
                term.equivalent += [x.strip()
                                    for x in row[equivalentIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[iriIndex]:
                term._iri = row[iriIndex].strip()
            if row[sharedInPPDFIndex]:
                if row[sharedInPPDFIndex].strip().lower() == YES.lower():
                    term.sharedInPPDF = True
                elif row[sharedInPPDFIndex].strip().lower() == NO.lower():
                    term.sharedInPPDF = False
            if row[datatypeIndex]:
                datatype = row[datatypeIndex].strip().lower()
                if datatype.startswith("http://www.w3.org/2001/XMLSchema#"):
                    term.datatype = datatype
                elif datatype.startswith("xsd:"):
                    term.datatype = "http://www.w3.org/2001/XMLSchema#{}".format(
                        datatype[4:])
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
                term.datatype = datatype
            if row[rppTypeIndex]:
                if row[rppTypeIndex].strip().lower() == YES.lower():
                    term.rppType = RPPType.PUBLIC
                elif row[rppTypeIndex].strip().lower() == NO.lower():
                    term.rppType = RPPType.PRIVATE
            if row[rppPrivateTypeSourceIndex]:
                term.rppPrivateTypeSource = row[rppPrivateTypeSourceIndex].strip(
                )
            if row[relatedSourceIndex]:
                term.related += [x.strip()
                                 for x in row[relatedSourceIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[alternativeNameIndex]:
                term.alternateName += [(DEFAULT_LANGUAGE, x.strip())
                                       for x in row[alternativeNameIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[get360Index]:
                get360 = row[get360Index].strip().lower()
                if OFN_360_2023_GET_BASE_REGISTRY.lower() in get360:
                    term.getValueType = GetValueType.BASE_REGISTRY
                elif OFN_360_2023_GET_OTHER_AGENDA.lower() in get360:
                    term.getValueType = GetValueType.OTHER_AGENDA
                elif OFN_360_2023_GET_OWN_AGENDA.lower() in get360:
                    term.getValueType = GetValueType.OWN_AGENDA
                elif OFN_360_2023_GET_OPERATING.lower() in get360:
                    term.getValueType = GetValueType.OPERATING
            if row[share360Index]:
                share360 = row[get360Index].strip().lower()
                if OFN_360_2023_SHARE_PUBLIC.lower() in share360:
                    term.shareValueType.append(ShareValueType.PUBLIC)
                elif OFN_360_2023_SHARE_ON_REQUEST.lower() in share360:
                    term.shareValueType.append(ShareValueType.ON_REQUEST)
                elif OFN_360_2023_SHARE_FOR_AGENDAS.lower() in share360:
                    term.shareValueType.append(ShareValueType.FOR_AGENDAS)
                elif OFN_360_2023_SHARE_PRIVATE.lower() in share360:
                    term.shareValueType.append(ShareValueType.PRIVATE)
            if row[content360Index]:
                content360 = row[get360Index].strip().lower()
                if OFN_360_2023_CONTENT_IDENTIFICATION.lower() in content360:
                    term.contentValueType = ContentValueType.IDENTIFICATION
                elif OFN_360_2023_CONTENT_RECORD.lower() in content360:
                    term.contentValueType = ContentValueType.RECORD
                elif OFN_360_2023_CONTENT_STATISTICAL.lower() in content360:
                    term.contentValueType = ContentValueType.STATISTICAL
            tropes.append(term)
    return tropes


def rlSheetToOFN(sheet) -> List[Relationship]:
    termClassSourceIndex = -1
    termClassTargetIndex = -1
    nameIndex = -1
    descriptionIndex = -1
    definitionIndex = -1
    sourceIndex = -1
    subClassOfIndex = -1
    equivalentIndex = -1
    iriIndex = -1
    relatedSourceIndex = -1
    alternativeNameIndex = -1
    sharedInPPDFIndex = -1
    rppTypeIndex = -1
    rppPrivateTypeSourceIndex = -1
    relationships = []
    for lst in sheet:
        row = [cell.value for cell in lst]
        if nameIndex == -1:
            nameIndex = getSimilar(row, OFN_NAME)
            descriptionIndex = getSimilar(row, OFN_DESCRIPTION)
            definitionIndex = getSimilar(row, OFN_DEFINITION)
            sourceIndex = getSimilar(row, OFN_SOURCE)
            subClassOfIndex = getSimilar(row, OFN_SUBCLASS)
            equivalentIndex = getSimilar(row, OFN_EQUIVALENT)
            iriIndex = getSimilar(row, OFN_IRI)
            termClassIndices = [x for x, y in enumerate(
                row) if y == OFN_SUBJECT_OR_OBJECT]
            if len(termClassIndices) == 2:
                termClassSourceIndex = termClassIndices[0]
                termClassTargetIndex = termClassIndices[1]
            relatedSourceIndex = getSimilar(row, OFN_RELATED)
            alternativeNameIndex = getSimilar(row, OFN_ALTERNATIVE)
            sharedInPPDFIndex = getSimilar(row, OFN_RPP_SHARED)
            rppTypeIndex = getSimilar(row, OFN_RPP_TYPE)
            rppPrivateTypeSourceIndex = getSimilar(row, OFN_RPP_PRIVATE_SOURCE)
            continue
        else:
            if row[nameIndex] is None or row[termClassSourceIndex] is None or row[termClassTargetIndex] is None:
                continue
            term = Relationship(row[termClassSourceIndex].strip(),
                                row[termClassTargetIndex].strip())
            term.name = {DEFAULT_LANGUAGE: row[nameIndex].strip()}
            if row[definitionIndex]:
                term.definition = {
                    DEFAULT_LANGUAGE: row[definitionIndex].strip()}
            if row[descriptionIndex]:
                term.description = {
                    DEFAULT_LANGUAGE: row[descriptionIndex].strip()}
            if row[sourceIndex]:
                term.source = [x.strip()
                               for x in row[sourceIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[subClassOfIndex]:
                term.subClassOf += [x.strip()
                                    for x in row[subClassOfIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[equivalentIndex]:
                term.equivalent += [x.strip()
                                    for x in row[equivalentIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[iriIndex]:
                term._iri = row[iriIndex].strip()
            if row[sharedInPPDFIndex]:
                if row[sharedInPPDFIndex].strip().lower() == YES.lower():
                    term.sharedInPPDF = True
                elif row[sharedInPPDFIndex].strip().lower() == NO.lower():
                    term.sharedInPPDF = False
                else:
                    warnings.warn("warn")
            if row[rppTypeIndex]:
                if row[rppTypeIndex].strip().lower() == YES.lower():
                    term.rppType = RPPType.PUBLIC
                elif row[rppTypeIndex].strip().lower() == NO.lower():
                    term.rppType = RPPType.PRIVATE
                else:
                    warnings.warn("warn")
            if row[rppPrivateTypeSourceIndex]:
                term.rppPrivateTypeSource = row[rppPrivateTypeSourceIndex].strip(
                )
            if row[relatedSourceIndex]:
                term.related += [x.strip()
                                 for x in row[relatedSourceIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            if row[alternativeNameIndex]:
                term.alternateName += [(DEFAULT_LANGUAGE, x.strip())
                                       for x in row[alternativeNameIndex].split(MULTIPLE_VALUE_SEPARATOR)]
            relationships.append(term)
    return relationships


def vcSheetToOFN(sheet):
    name = None
    desc = ""
    lkod = "https://slovník.gov.cz/"
    for lst in sheet:
        row = [cell.value for cell in lst]
        if name is None:
            name = row[1]
            continue
        elif desc is None:
            desc = row[1]
            continue
        elif lkod is None:
            lkod = row[1]
            continue
        else:
            break
    if name is None:
        raise Exception()
    return (name, desc, lkod)


inputLocation = sys.argv[1]
outputLocation = sys.argv[2]


def tableToOFN():
    (soSheet, itSheet, rlSheet, vcSheet) = xlsxToSheets(inputLocation)
    soList = soSheetToOFN(soSheet)
    itList = itSheetToOFN(itSheet)
    rlList = rlSheetToOFN(rlSheet)
    vocabulary = Vocabulary()
    if vcSheet:
        (name, desc, lkod) = vcSheetToOFN(vcSheet)
        vocabulary.name[DEFAULT_LANGUAGE] = str(name)
        vocabulary.description[DEFAULT_LANGUAGE] = str(desc)
        vocabulary.lkod = str(lkod)
    else:
        raise Exception()
    vocabulary.terms.extend(soList)
    vocabulary.terms.extend(itList)
    vocabulary.terms.extend(rlList)
    if len(itList) > 0 or len(rlList) > 0:
        vocabulary.type = VocabularyType.CONCEPTUAL_MODEL
    convertToRDF(vocabulary, DEFAULT_LANGUAGE, outputLocation)


tableToOFN()
