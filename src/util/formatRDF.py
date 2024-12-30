import rdflib
import sys

inputLocation = sys.argv[1]
outputLocation = sys.argv[2]

g = rdflib.Graph()
g.parse(inputLocation)

with open(outputLocation, "w", encoding="utf-8") as outputFile:
    format: str = outputLocation[len(outputLocation) - 3:]
    outputFile.write(g.serialize(format=format))
