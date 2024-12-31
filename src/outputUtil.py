import traceback
from rdflib import Graph, Literal, URIRef

from ofnClasses import Vocabulary


def getRDFoutput(graph: Graph, outputLocation: str):
    with open(outputLocation, "w", encoding="utf-8") as outputFile:
        format: str = outputLocation[len(outputLocation) - 3:]
        outputFile.write(graph.serialize(format=format))


def testInputString(string: str | None) -> bool:
    return string is not None and string.strip() != ""


def getURIRefOrLiteral(string: str | None):
    if not testInputString(string):
        raise Exception("")
    result = URIRef(str(string))
    try:
        result.n3()
        return result
    except Exception:
        print(traceback.format_exc())
        return Literal(string)


def checkForTerm(vocabulary: Vocabulary, string: str):
    result = URIRef(string)
    try:
        result.n3()
        return result
    except Exception:

        pass
