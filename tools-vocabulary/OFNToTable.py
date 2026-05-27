import csv
from ofnClasses import *


def OFNToTable(vocabulary: Vocabulary):
    with open("output.csv", "w", newline="", encoding="utf-8") as csvfile:
        csvwriter = csv.writer(csvfile)
        for term in [x for x in vocabulary.terms if isinstance(x, TermClass)]:
            name = term.name["cs"]
            type = ""
            if (term.type == ClassType.SUBJECT):
                type = "Subjekt práva"
            elif (term.type == ClassType.OBJECT):
                type = "Objekt práva"
            desc = term.description["cs"] if "cs" in term.description else ""
            defi = term.definition["cs"] if "cs" in term.definition else ""
            src = term.source
            sco = ";".join(term.subClassOf)
            csvwriter.writerow([name, type, desc, defi, src, sco])
        for term in [x for x in vocabulary.terms if isinstance(x, Trope)]:
            name = term.name["cs"]
            dom = term.target if term.target is not None else ""
            desc = term.description["cs"] if "cs" in term.description else ""
            defi = term.definition["cs"] if "cs" in term.definition else ""
            src = term.source
            sco = ";".join(term.subClassOf)
            csvwriter.writerow([name, dom, desc, defi, src, sco])
        for term in [x for x in vocabulary.terms if isinstance(x, Relationship)]:
            name = term.name["cs"]
            dom = term.domain
            ran = term.range
            desc = term.description["cs"] if "cs" in term.description else ""
            defi = term.definition["cs"] if "cs" in term.definition else ""
            src = term.source
            sco = ";".join(term.subClassOf)
            csvwriter.writerow([dom, name, ran, desc, defi, src, sco])
