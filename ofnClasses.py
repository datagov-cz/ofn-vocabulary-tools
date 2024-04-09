from enum import Enum

TermType = Enum("TermType", ['TERM', 'CLASS',
                'RELATIONSHIP', 'TROPE', 'SUBJECT', 'OBJECT'])

VocabularyType = Enum("VocabularyType", ["THESAURUS", "CONCEPTUAL_MODEL"])


class Term:
    def __init__(self) -> None:
        self.id: str = ""
        self.type: TermType = TermType.TERM
        self.name: dict = {}
        self.description: dict = {}
        self.definition: dict = {}
        self.source = ""
        self.domain = ""
        self.range = ""
        self.datatype = ""
        self.subClassOf = []
        self.tropes = []


class Vocabulary:
    def __init__(self) -> None:
        self.name = {}
        self.description = {}
        self.terms = []
        self.type = VocabularyType.THESAURUS
