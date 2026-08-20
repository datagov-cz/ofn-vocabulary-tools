from dataclasses import dataclass


class UploadError(ValueError):
    def __init__(self, text_key):
        super().__init__(text_key)
        self.text_key = text_key


@dataclass(frozen=True)
class UploadedXml:
    filename: str
    content: bytes


def read_xml_upload(uploaded_file):
    if uploaded_file is None or uploaded_file.filename == "":
        raise UploadError("missing_file")

    if not uploaded_file.filename.lower().endswith((".xml", ".xmi")):
        raise UploadError("invalid_file_type")

    return UploadedXml(
        filename=uploaded_file.filename,
        content=uploaded_file.read(),
    )
