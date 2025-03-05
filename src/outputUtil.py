import json
import traceback
from rdflib import Graph, Literal, URIRef
from os.path import splitext

from ofnClasses import Vocabulary
from outputJSON import getJSONLDfromVocabulary


def getRDFoutput(graph: Graph, vocabulary: Vocabulary, outputLocation: str):
    output = None
    format: str = splitext(outputLocation)[1][1:]
    if format != "json-ld":
        output = graph.serialize(format=format)
    else:
        output = getJSONLDfromVocabulary(vocabulary)
    with open(outputLocation, "w", encoding="utf-8") as outputFile:
        if format != "json-ld":
            outputFile.write(output)
        else:
            json.dump(output, outputFile, ensure_ascii=False, indent=2)


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
