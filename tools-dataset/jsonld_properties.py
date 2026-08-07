import re
import warnings

from xml_processing import ArchimateElement, ArchimateRelationship


# https://www.w3.org/TR/sparql11-query/#rPN_LOCAL
PN_CHARS_U = re.compile(
    "[A-Za-z]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]|"
    "[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]|[\u2070-\u218F]|"
    "[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|"
    "[\U00010000-\U000EFFFF]|_",
    re.U,
)
PERCENT = re.compile("%([0-9A-Fa-f])([0-9A-Fa-f])", re.U)
PN_LOCAL_ESC = re.compile("\\\\[_~\\.\\-!$&\"'()*+,;=/?#@%]")
PLX = re.compile(
    "({})|({})".format(PERCENT.pattern, PN_LOCAL_ESC.pattern),
    re.I,
)
PN_CHARS = re.compile(
    "({})|[-0-9]|\u00B7|[\u0300-\u036F]|[\u203F-\u2040]".format(
        PN_CHARS_U.pattern,
    ),
    re.U,
)
PN_LOCAL_1 = re.compile(
    "({})|[:0-9]|({})".format(PN_CHARS_U.pattern, PLX.pattern),
)
PN_LOCAL_2 = re.compile(
    "({})|[.:]|({})".format(PN_CHARS.pattern, PLX.pattern),
)
PN_LOCAL_3 = re.compile(
    "({})|:|({})".format(PN_CHARS.pattern, PLX.pattern),
)
PN_LOCAL = re.compile(
    "({})(({})*({}))?".format(
        PN_LOCAL_1.pattern,
        PN_LOCAL_2.pattern,
        PN_LOCAL_3.pattern,
    ),
    re.U,
)

HTTPS_REGEX = r"^https://.*$"
FORMAT_REGEX = r"^formáty:.*$"
MEDIA_TYPE_REGEX = r"^mediaTypes:.*$"
PROVIDER_REGEX = r"^ovm:[^/]+$"
THEME_REGEX = r"^témata:.*$"
FREQUENCY_REGEX = r"^frekvence:.*$"
EUROVOC_REGEX = r"^euroVoc:.*$"
ISVS_REGEX = r"^isvs:[^/]+$"
DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"
EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def sanitizeString(string: str) -> str:
    result: str = ""
    for match in PN_LOCAL.finditer(string):
        matched_text = match.group(0)
        result = result.ljust(match.end(0), "-")
        result = result[0:(match.end(0) - len(matched_text))]
        result += matched_text
    return re.sub("-+$", "", result)


def containsCompare(input: str | list[str], target: str) -> bool:
    if type(input) is str:
        return target.lower() in input.lower()
    if type(input) is list:
        boolList: list[bool] = [target.lower() in x.lower() for x in input]
        return any(boolList)
    return False


def createDatasetIRI(name: str) -> str:
    namespace = "https://slovník.gov.cz"
    namespace = re.sub("/$", "", namespace)
    while namespace.endswith("/"):
        namespace = namespace[:-1]
    return "{}/{}".format(
        namespace,
        sanitizeString(name.strip().lower()),
    )


def addProperty(
    key: str,
    value,
    element: ArchimateElement | ArchimateRelationship,
    property=None,
) -> dict:
    if not property:
        property = key
    if getProperty(property) in element.resolved_properties:
        return {key: value}
    return {}


def regexWarning(
    element: ArchimateElement | ArchimateRelationship,
    property: str,
    value,
    regex: str,
):
    warnings.warn(
        "Skipping property {} of element ID {} because value {!r} doesn't "
        "satisfy regex {}".format(
            property,
            element.identifier,
            value,
            regex,
        )
    )


def regexFilterValue(
    value,
    regex: str,
    element: ArchimateElement | ArchimateRelationship,
    property: str,
):
    if isinstance(value, str):
        if re.fullmatch(regex, value):
            return value
        regexWarning(element, property, value, regex)
        return None

    if isinstance(value, list):
        filtered = [
            item
            for item in (
                regexFilterValue(item, regex, element, property)
                for item in value
            )
            if item is not None
        ]
        return filtered if filtered else None

    if isinstance(value, dict):
        filtered = {
            key: filtered_value
            for key, filtered_value in (
                (key, regexFilterValue(item, regex, element, property))
                for key, item in value.items()
            )
            if filtered_value is not None
        }
        return filtered if filtered else None

    regexWarning(element, property, value, regex)
    return None


def addRegexProperty(
    key: str,
    value,
    regex: str,
    element: ArchimateElement | ArchimateRelationship,
    property=None,
) -> dict:
    if not property:
        property = key
    if getProperty(property) not in element.resolved_properties:
        return {}

    filtered_value = regexFilterValue(value, regex, element, property)
    if filtered_value is None:
        return {}

    return {key: filtered_value}


def prefixValue(value, prefix: str):
    """Add a JSON-LD compact-IRI prefix to scalar or list input values.

    Values that already carry the requested prefix are left unchanged.  This
    keeps older ArchiMate models working while allowing users to enter just
    the code (or media type) in newly created models.
    """
    if isinstance(value, str):
        stripped_value = value.strip()
        if not stripped_value or stripped_value.startswith(prefix):
            return stripped_value
        return "{}{}".format(prefix, stripped_value)

    if isinstance(value, list):
        return [prefixValue(item, prefix) for item in value]

    return value


def addCodeProperty(
    key: str,
    value,
    prefix: str,
    regex: str,
    element: ArchimateElement | ArchimateRelationship,
    property=None,
) -> dict:
    """Prefix an input code and validate the resulting compact IRI."""
    return addRegexProperty(
        key,
        prefixValue(value, prefix),
        regex,
        element,
        property,
    )


def addEmailProperty(
    key: str,
    value,
    element: ArchimateElement,
    property: str,
) -> dict:
    if getProperty(property) not in element.resolved_properties:
        return {}

    if not isinstance(value, str):
        regexWarning(element, property, value, EMAIL_REGEX)
        return {}

    address = value.removeprefix("mailto:")
    if not re.fullmatch(EMAIL_REGEX, address):
        regexWarning(element, property, value, EMAIL_REGEX)
        return {}

    return {key: "mailto:{}".format(address)}


def addPropertyHelper(input: str | list[str] | None):
    if type(input) is str:
        return input
    if type(input) is list:
        return input[0]
    return None


def splitProperty(input: str | list[str] | None):
    if type(input) is str:
        return [item.strip() for item in input.split(";") if item.strip()]
    if type(input) is list:
        return [item.strip() for item in input if item.strip()]
    return None


def getProperty(property: str) -> str:
    return property.replace("_", " ")


def getSubproperty(parent: str, child: str) -> str:
    return "{} - {}".format(getProperty(parent), getProperty(child))


def addPrefixedProperty(
    key: str,
    value,
    element: ArchimateElement | ArchimateRelationship,
) -> dict:
    prefix = "{} - ".format(getProperty(key))
    if any(
        property_name.startswith(prefix)
        for property_name in element.resolved_properties
    ):
        return {key: value}
    return {}


def addNonEmptyProperty(key: str, value) -> dict:
    return {key: value} if value else {}


def readProperty(
    element: ArchimateElement | ArchimateRelationship,
    property: str,
):
    return element.resolved_properties.get(getProperty(property))
