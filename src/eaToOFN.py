import sys
from typing import List
from lxml import etree  # type: ignore
from ofnClasses import *
from outputToRDF import convertToRDF
from ofnBindings import *
from outputUtil import testInputString
from dataclasses import dataclass
import warnings

inputLocation = "C:\\Users\\AliceBinderová\\data.gov.cz\\přílohy\\popis-dat\\šablony\\Příkladový-slovník.xml"
outputLocation = "eaTest.ttl"


@dataclass
class Package:
    id: str
    parent: str
    isSP: bool


ns = {
    "xmi": "http://schema.omg.org/spec/XMI/2.1",
    "uml": "http://schema.omg.org/spec/UML/2.1",
    "Slovniky": "http://www.sparxsystems.com/profiles/Slovniky/1.0"
}

with open(inputLocation, "r") as inputFile:
    tree = etree.parse(
        inputLocation, parser=etree.XMLParser())
    root = tree.getroot()
    umlModel = root.find("uml:Model", ns)
    packageElements = umlModel.findall(
        ".//packagedElement[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Package']")
    packages = {}
    for packageElement in packageElements:
        packages[packageElement.get("{http://schema.omg.org/spec/XMI/2.1}id")] = {
            "parent": model.get("package"), "isSP": properties.get("stereotype") == "slovnikyPackage"}

    # packageElements = root.findall(
    #     ".//element[@{http://schema.omg.org/spec/XMI/2.1}type='uml:Package']")
    # packages = {}
    # terms = []
    # for packageElement in packageElements:
    #     model = packageElement.find("model")
    #     properties = packageElement.find("properties")
    #     if model is None or properties is None:
    #         continue
    #     packages[packageElement.get("{http://schema.omg.org/spec/XMI/2.1}idref")] = {
    #         "parent": model.get("package"), "isSP": properties.get("stereotype") == "slovnikyPackage"}
    # # if not True in [x["isSP"] for x in packages.values()]:
    # #     raise Exception(
    # #         "Provided file has no package of stereotype 'slovnikyPackage'.")
    # termElements = root.findall(.//element)
