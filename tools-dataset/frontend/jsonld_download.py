import json
import logging
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Response


logger = logging.getLogger(__name__)


def upload_stem(upload_name):
    stem = Path(upload_name).stem or "converted"
    return stem


def single_download_name(upload_name, jsonld_file):
    if jsonld_file.filename:
        return ensure_jsonld_extension(Path(jsonld_file.filename).name)
    return f"{upload_stem(upload_name)}.jsonld"


def zip_download_name(upload_name):
    return f"{upload_stem(upload_name)}.zip"


def json_bytes(document):
    json_bytes = json.dumps(document, indent=2, ensure_ascii=False).encode("utf-8")
    return json_bytes


def create_single_jsonld_download(jsonld_file, upload_name):
    download_name = single_download_name(upload_name, jsonld_file)
    logger.info("Preparing single JSON-LD download %r", download_name)
    return Response(
        json_bytes(jsonld_file.document),
        mimetype="application/ld+json",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"'
        },
    )


def create_zip_download(jsonld_files, upload_name):
    zip_buffer = BytesIO()
    used_names = set()

    with ZipFile(zip_buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        for index, jsonld_file in enumerate(jsonld_files, start=1):
            file_name = unique_file_name(jsonld_file.filename, used_names, index, upload_stem(upload_name))
            zip_file.writestr(file_name, json_bytes(jsonld_file.document))

    logger.info(
        "Preparing ZIP download %r containing %d JSON-LD file(s)",
        zip_download_name(upload_name),
        len(jsonld_files),
    )

    return Response(
        zip_buffer.getvalue(),
        mimetype="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_download_name(upload_name)}"'
        },
    )


def ensure_jsonld_extension(file_name):
    if file_name.endswith(".jsonld"):
        return file_name
    return f"{file_name}.jsonld"


def unique_file_name(file_name, used_names, index, default_stem):
    safe_name = Path(file_name or f"{default_stem}-{index}.jsonld").name
    safe_name = ensure_jsonld_extension(safe_name)

    if safe_name not in used_names:
        used_names.add(safe_name)
        return safe_name

    stem = Path(safe_name).stem
    suffix = Path(safe_name).suffix
    deduplicated_name = f"{stem}-{index}{suffix}"
    used_names.add(deduplicated_name)
    return deduplicated_name


def create_jsonld_download(jsonld_files, upload_name):
    if len(jsonld_files) == 1:
        return create_single_jsonld_download(jsonld_files[0], upload_name)

    return create_zip_download(jsonld_files, upload_name)
