from enum import Enum

ClassType = Enum("ClassType", ['CLASS', 'SUBJECT', 'OBJECT'])

VocabularyType = Enum("VocabularyType", ["THESAURUS", "CONCEPTUAL_MODEL"])

RPPType = Enum("RPPType", ["PUBLIC", "PRIVATE"])


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
        self.terms: list[Term] = []
        self.type: VocabularyType = VocabularyType.THESAURUS

    def getIRI(self, defaultLanguage: str) -> str:
        self.iri = "https://slovník.gov.cz/{}".format(
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

    def getIRI(self, vocabulary: Vocabulary, defaultLanguage: str) -> str:
        self.iri = "https://slovník.gov.cz/{}/pojem/{}".format(
            vocabulary.name[defaultLanguage].strip().lower().replace(" ", "-"),
            self.name[defaultLanguage].strip().lower().replace(" ", "-"))
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
