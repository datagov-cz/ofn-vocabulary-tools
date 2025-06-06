from ofnBindings import DEFAULT_LANGUAGE
from ofnClasses import Relationship, TermClass, Trope, Vocabulary
import re
from urllib.parse import unquote
import rfc3987

reportWarning = False


def getAgendaODIRI(input: str) -> str:
    if re.search("^(https:\/\/rpp-opendata.egon.gov.cz\/odrpp\/zdroj\/agenda\/A)([0-9]+)$", input) is not None:
        return input
    elif re.search("^A([0-9]+)$", input):
        return "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/agenda/{}".format(input)
    elif re.search("^([0-9]+)$", input):
        return "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/agenda/A{}".format(input)
    else:
        print(
            "{} je neplatná hodnota pro charakteristiku Agenda.".format(input))
        global reportWarning
        reportWarning = True
        return ""


def getAISODIRI(input: str) -> str:
    if re.search("^(https:\/\/rpp-opendata.egon.gov.cz\/odrpp\/zdroj\/isvs\/)([0-9]+)$", input) is not None:
        return input
    elif re.search("^([0-9]+)$", input):
        return "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/isvs/{}".format(input)
    else:
        print("{} je neplatná hodnota pro charakteristiku Agendový informační systém.".format(input))
        global reportWarning
        reportWarning = True
        return ""


def getSourceODIRI(input: str) -> str:
    if input == "":
        return input
    eliPart = re.search("eli\/cz\/sb\/.*$", input)
    control = re.search("^https\:\/\/.*\/eli\/cz\/sb\/.*$", input)
    if control and eliPart:
        return "https://opendata.eselpoint.cz/esel-esb/{}".format(eliPart.group())
    else:
        print("Zdroj {} je nevalidní. Vymazávám.".format(input))
        global reportWarning
        reportWarning = True
        return ""


def processLink(input: str, vocabulary: Vocabulary) -> str:
    if not rfc3987.match(input, rule="IRI"):
        termIRI = next(x.getIRI(vocabulary, DEFAULT_LANGUAGE)
                       for x in vocabulary.terms if input.lower() == x.name[DEFAULT_LANGUAGE].lower())
        return termIRI
    else:
        return input


def preprocessVocabulary(vocabulary: Vocabulary) -> Vocabulary:
    global reportWarning
    reportWarning = False
    vocabulary.terms = sorted(vocabulary.terms,
                              key=lambda x: x._iri)
    for term in vocabulary.terms:
        for sco in term.subClassOf.copy():
            replace = processLink(sco, vocabulary)
            term.subClassOf.remove(sco)
            term.subClassOf.append(replace)
        term.related = [getSourceODIRI(unquote(x)) for x in term.related]
        term.source = getSourceODIRI(unquote(term.source))
        if term.rppPrivateTypeSource:
            term.rppPrivateTypeSource = getSourceODIRI(
                unquote(term.rppPrivateTypeSource))
        term.equivalent = [unquote(x) for x in term.equivalent]
        term.subClassOf = [unquote(x) for x in term.subClassOf]
        if isinstance(term, TermClass):
            if term.agenda:
                term.agenda = getAgendaODIRI(unquote(term.agenda))
            if term.ais:
                term.ais = getAISODIRI(unquote(term.ais))
        if isinstance(term, Relationship):
            if term.domain:
                term.domain = processLink(unquote(term.domain), vocabulary)
            if term.range:
                term.range = processLink(unquote(term.range), vocabulary)
        if isinstance(term, Trope):
            if term.datatype:
                term.datatype = unquote(term.datatype)
            if term.target:
                term.target = processLink(unquote(term.target), vocabulary)
            term.datatype = ""

        if reportWarning:
            print(
                "------\tProblémy výše byly nalezeny u pojmu {}.".format(term.name[DEFAULT_LANGUAGE]))
            reportWarning = False
    return vocabulary
