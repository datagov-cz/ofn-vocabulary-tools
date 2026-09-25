# Dataset generation functions

Python modules for converting ArchiMate Model Exchange XML and Enterprise
Architect XMI 2.1 exports to dataset JSON-LD.

The user interface and deployment configuration live in `../tools-frontend`.
This directory contains the format parsers, shared conversion pipeline,
documentation, examples, and functional tests.

## Structure

- `archi/`: ArchiMate Model Exchange parser
- `ea/`: Enterprise Architect XMI parser and package filtering
- `core/`: format dispatch, JSON-LD creation, validation, bindings, and models
- `docs/`: input-format and term-selection documentation
- `tests/`: conversion-pipeline tests

## Use from Python

```python
from core.jsonld_creation import create_jsonld_files
from core.xml_processing import parse_xml

with open("model.xml", "rb") as source:
    outputs = create_jsonld_files(parse_xml(source.read()))
```

Generated documents can be checked with
`core.jsonld_validation.validate_jsonld_files(outputs)`. By default validation
uses the schema configured by `JSON_SCHEMA_URL`; set it to an empty string to
disable remote schema validation.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r ../tools-frontend/requirements.txt
python -m unittest discover -s tests -v
```

For the web and Windows Electron applications, see
[`../tools-frontend/README.md`](../tools-frontend/README.md).
