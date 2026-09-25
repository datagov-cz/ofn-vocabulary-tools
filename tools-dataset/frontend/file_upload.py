import logging
from dataclasses import dataclass


logger = logging.getLogger(__name__)


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
        logger.warning("Upload rejected: no file was provided")
        raise UploadError("missing_file")

    if not uploaded_file.filename.lower().endswith((".xml", ".xmi")):
        logger.warning(
            "Upload rejected because file type is not XML or XMI: %r",
            uploaded_file.filename,
        )
        raise UploadError("invalid_file_type")

    uploaded_xml = UploadedXml(
        filename=uploaded_file.filename,
        content=uploaded_file.read(),
    )
    logger.info(
        "Accepted upload %r (%d bytes)",
        uploaded_xml.filename,
        len(uploaded_xml.content),
    )
    return uploaded_xml
