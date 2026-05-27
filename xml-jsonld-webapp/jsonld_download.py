import json
from pathlib import Path

from flask import Response


def download_name(upload_name):
    stem = Path(upload_name).stem or "converted"
    return f"{stem}.jsonld"


def create_jsonld_download(document, upload_name):
    json_bytes = json.dumps(document, indent=2, ensure_ascii=False).encode("utf-8")
    return Response(
        json_bytes,
        mimetype="application/ld+json",
        headers={
            "Content-Disposition": f'attachment; filename="{download_name(upload_name)}"'
        },
    )
