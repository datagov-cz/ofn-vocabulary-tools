from enum import Enum
import re
from typing import Tuple

ClassType = Enum("ClassType", ['CLASS', 'SUBJECT', 'OBJECT'])

VocabularyType = Enum("VocabularyType", ["THESAURUS", "CONCEPTUAL_MODEL"])

RPPType = Enum("RPPType", ["PUBLIC", "PRIVATE"])

# https://www.w3.org/TR/sparql11-query/#rPN_LOCAL
PN_CHARS_U = re.compile(
    "[A-Za-z]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]|[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF]|_", re.U)
PERCENT = re.compile("%([0-9A-Fa-f])([0-9A-Fa-f])", re.U)
PN_LOCAL_ESC = re.compile("\\\\[_~\\.\\-!$&\"'()*+,;=/?#@%]")
PLX = re.compile("({})|({})".format(
    PERCENT.pattern, PN_LOCAL_ESC.pattern), re.I)
PN_CHARS = re.compile(
    "({})|[-0-9]|\u00B7|[\u0300-\u036F]|[\u203F-\u2040]".format(PN_CHARS_U.pattern), re.U)
PN_LOCAL_1 = re.compile(
    "({})|[:0-9]|({})".format(PN_CHARS_U.pattern, PLX.pattern))
PN_LOCAL_2 = re.compile("({})|[.:]|({})".format(
    PN_CHARS.pattern, PLX.pattern))
PN_LOCAL_3 = re.compile("({})|:|({})".format(
    PN_CHARS.pattern, PLX.pattern))
PN_LOCAL = re.compile("({})(({})*({}))?".format(PN_LOCAL_1.pattern,
                                                PN_LOCAL_2.pattern, PN_LOCAL_3.pattern), re.U)


class Resource:
    def __init__(self) -> None:
        self.id = None
        self.iri = None
        self.name: dict[str, str] = {}
        self.description: dict[str, str] = {}

    def getIRI(self):
        raise NotImplementedError()


class Vocabulary(Resource):
    def __init__(self) -> None:
        super().__init__()
        self.lkod: str = ""
        self.terms: list[Term] = []
        self.type: VocabularyType = VocabularyType.THESAURUS

    def getIRI(self, defaultLanguage: str) -> str:
        self.iri = "{}/{}".format(self.lkod,
                                  self.name[defaultLanguage].strip().lower().replace(" ", "-"))
        return self.iri


class Term(Resource):
    def __init__(self) -> None:
        super().__init__()
        self.name: dict = {}
        self.description: dict = {}
        self.definition: dict = {}
        self.source: str | None = None
        self.related: list[str] = []
        self.subClassOf: list[str] = []
        self.equivalent: list[str] = []
        self.sharedInPPDF: bool | None = None
        self.rppType: RPPType | None = None
        self.rppPrivateTypeSource: str | None = None
        self.alternateName: list[Tuple[str, str]] = []

    def getIRI(self, vocabulary: Vocabulary, defaultLanguage: str) -> str:
        name: str = self.name[defaultLanguage].strip().lower()
        result: str = ""
        for match in PN_LOCAL.finditer(name):
            m = match.group(0)
            result = result.ljust(match.end(0), "-")
            result = result[0:(match.end(0) - len(m))]
            result += m
        result = re.sub("-+$", "", result)
        self.iri = "{}/pojem/{}".format(
            vocabulary.getIRI(),
            result)
        return self.iri


class TermClass(Term):
    def __init__(self) -> None:
        super().__init__()
        self.ais: str | None = None
        self.agenda: str | None = None
        self.type: ClassType = ClassType.CLASS


class Relationship(TermClass):
    def __init__(self, domain: str, range: str) -> None:
        super().__init__()
        self.domain: str = domain
        self.range: str = range


class Trope(TermClass):
    def __init__(self) -> None:
        super().__init__()
        self.target: str | None = None
        self.datatype: str | None = None


def getClass(term: Term) -> TermClass:
    termClass = TermClass()
    termClass.id = term.id
    termClass.name = term.name
    termClass.description = term.description
    termClass.definition = term.definition
    termClass.source = term.source
    termClass.related = term.related
    termClass.subClassOf = term.subClassOf
    termClass.equivalent = term.equivalent
    termClass.sharedInPPDF = term.sharedInPPDF
    termClass.rppType = term.rppType
    termClass.rppPrivateTypeSource = term.rppPrivateTypeSource
    return termClass


def getTrope(term: Term) -> Trope:
    termClass = Trope()
    termClass.id = term.id
    termClass.name = term.name
    termClass.description = term.description
    termClass.definition = term.definition
    termClass.source = term.source
    termClass.related = term.related
    termClass.subClassOf = term.subClassOf
    termClass.equivalent = term.equivalent
    termClass.sharedInPPDF = term.sharedInPPDF
    termClass.rppType = term.rppType
    termClass.rppPrivateTypeSource = term.rppPrivateTypeSource
    return termClass


def getRelationship(term: Term, domain: str, range: str) -> Relationship:
    termClass = Relationship(domain, range)
    termClass.id = term.id
    termClass.name = term.name
    termClass.description = term.description
    termClass.definition = term.definition
    termClass.source = term.source
    termClass.related = term.related
    termClass.subClassOf = term.subClassOf
    termClass.equivalent = term.equivalent
    termClass.sharedInPPDF = term.sharedInPPDF
    termClass.rppType = term.rppType
    termClass.rppPrivateTypeSource = term.rppPrivateTypeSource
    return termClass
