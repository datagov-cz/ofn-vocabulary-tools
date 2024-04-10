from enum import Enum

TermType = Enum("TermType", ['TERM', 'CLASS',
                'RELATIONSHIP', 'TROPE', 'SUBJECT', 'OBJECT'])

VocabularyType = Enum("VocabularyType", ["THESAURUS", "CONCEPTUAL_MODEL"])

RPPType = Enum("RPPType", ["PUBLIC", "PRIVATE"])


class Vocabulary:
    def __init__(self) -> None:
        self.iri = ""
        self.name = {}
        self.description = {}
        self.terms = []
        self.type = VocabularyType.THESAURUS

    def getIRI(self, defaultLanguage: str) -> str:
        self.iri = "https://slovník.gov.cz/{}".format(
            self.name[defaultLanguage].strip().lower().replace(" ", "-"))
        return self.iri


class Term:
    def __init__(self) -> None:
        self.id: str = ""
        self.iri: str = ""
        self.type: TermType = TermType.TERM
        self.name: dict = {}
        self.description: dict = {}
        self.definition: dict = {}
        self.source = None
        self.related = []
        self.domain = None
        self.range = None
        self.datatype = None
        self.subClassOf = []
        self.tropes = []
        self.equivalent = []
        self.sharedInPPDF = None
        self.rppType = None
        self.rppPrivateTypeSource = None
        self.ais = None
        self.agenda = None

    def getIRI(self, vocabulary: Vocabulary, defaultLanguage: str) -> str:
        self.iri = "https://slovník.gov.cz/{}/pojem/{}".format(
            vocabulary.name[defaultLanguage].strip().lower().replace(" ", "-"),
            self.name[defaultLanguage].strip().lower().replace(" ", "-"))
        return self.iri
