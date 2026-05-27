from dataclasses import dataclass


@dataclass(frozen=True)
class UploadedXml:
    filename: str
    content: bytes


def read_xml_upload(uploaded_file):
    if uploaded_file is None or uploaded_file.filename == "":
        raise ValueError("Choose an XML file to upload.")

    if not uploaded_file.filename.lower().endswith(".xml"):
        raise ValueError("Only .xml files are accepted.")

    return UploadedXml(
        filename=uploaded_file.filename,
        content=uploaded_file.read(),
    )
