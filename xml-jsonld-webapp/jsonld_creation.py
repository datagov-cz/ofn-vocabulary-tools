def create_jsonld(parsed_xml):
    # CUSTOM JSON-LD CREATION SETUP:
    # Replace this skeleton with the real JSON-LD mapping once the target
    # structure and XML parsing rules are defined.
    return {
        "@context": {},
        "@type": "ConvertedXmlDocument",
        "sourceRootElement": parsed_xml.root_element_name,
        "conversionStatus": "skeleton",
    }
