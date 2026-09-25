import json
from functools import lru_cache
from pathlib import Path


TEXTS_PATH = Path(__file__).with_name("texts.json")


@lru_cache(maxsize=1)
def get_texts():
    with TEXTS_PATH.open(encoding="utf-8") as texts_file:
        return json.load(texts_file)


def get_error_text(error_key, **values):
    template = get_texts()["errors"][error_key]
    return template.format(**values)
