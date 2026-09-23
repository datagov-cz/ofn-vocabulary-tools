import io
import json
import unittest
from urllib.parse import quote
from unittest.mock import Mock, patch
from zipfile import ZipFile
from xml.sax.saxutils import escape
import requests
from app import app
from core import jsonld_validation as validation
EA_XMI = b'''<?xml version="1.0" encoding="UTF-8"?>
<xmi:XMI xmlns:xmi="http://schema.omg.org/spec/XMI/2.1"
         xmlns:uml="http://schema.omg.org/spec/UML/2.1"
         xmlns:Slovniky="http://example.com/Slovniky">
  <uml:Model xmi:id="model" name="Root model">
    <packagedElement xmi:type="uml:Package" xmi:id="vocabulary" name="Testovaci slovnik">
      <packagedElement xmi:type="uml:Package" xmi:id="nested" name="Nested">
        <packagedElement xmi:type="uml:Class" xmi:id="dataset" name="Datova sada" />
        <packagedElement xmi:type="uml:Class" xmi:id="distribution" name="CSV" />
        <packagedElement xmi:type="uml:Association" xmi:id="relation">
          <ownedEnd xmi:id="end-1" type="dataset" />
          <ownedEnd xmi:id="end-2" type="distribution" />
        </packagedElement>
      </packagedElement>
    </packagedElement>
    <packagedElement xmi:type="uml:Package" xmi:id="outside" name="Outside">
      <packagedElement xmi:type="uml:Class" xmi:id="excluded" name="Excluded" />
    </packagedElement>
  </uml:Model>
  <Slovniky:slovnikyPackage xmi:id="sp" base_Package="vocabulary" />
  <Slovniky:datovaSada xmi:id="sd" base_Class="dataset"
      popis="Popis" klicoveSlovo="test" jeZahrnutaVIsvs="42"
      pravniPredpis="https://example.com/law">
    <tag name="vstupn&#237; str&#225;nka" value="https://example.com/dataset" />
  </Slovniky:datovaSada>
  <Slovniky:distribuceSouborKeStazeni xmi:id="ss" base_Class="distribution"
      pristupoveUrl="https://example.com/file.csv"
      souborKeStazeni="https://example.com/file.csv" format="CSV"
      typMedia="text/csv" pravniPredpis="https://example.com/law" />
  <Slovniky:datovaSada xmi:id="ignored" base_Class="excluded" />
</xmi:XMI>'''


def xml(names):
    elements = ''.join(f'<element identifier="d{i}"><name xml:lang="cs">{escape(name)}</name><properties><property propertyDefinitionRef="typ"><value>datová sada</value></property></properties></element>' for i, name in enumerate(names))
    return f'<model identifier="m"><name xml:lang="cs">Slovník</name><elements>{elements}</elements></model>'.encode()

class HttpChecks(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
        self.client = app.test_client()
        schema_setting = patch.object(validation, 'SCHEMA_URL', validation.DEFAULT_SCHEMA_URL)
        schema_setting.start()
        self.addCleanup(schema_setting.stop)
    def upload(self, content, filename='model.xml'):
        return self.client.post('/', data={'xml_file': (io.BytesIO(content), filename)})
    def test_homepage(self):
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'multipart/form-data', r.data)
    def test_stylesheet(self):
        r = self.client.get('/static/styles.css')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'text/css')
    def test_missing_file(self):
        self.assertEqual(self.client.post('/').status_code, 400)
    def test_wrong_extension(self):
        self.assertEqual(self.upload(b'<model/>', 'model.txt').status_code, 400)
    def test_empty_filename(self):
        self.assertEqual(self.upload(b'', '').status_code, 400)
    def test_empty_file(self):
        self.assertEqual(self.upload(b'').status_code, 400)
    def test_malformed_xml(self):
        self.assertEqual(self.upload(b'<model>').status_code, 400)
    def test_unsupported_xml_returns_client_error(self):
        self.assertEqual(self.upload(b'<foo/>').status_code, 400)
    def test_no_datasets_returns_client_error(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            self.assertEqual(self.upload(xml([])).status_code, 400)
    def test_archimate_single_download_validation_disabled(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            r = self.upload(xml(['Dataset']))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/ld+json')
        self.assertEqual(r.json['název']['cs'], 'Dataset')
        self.assertIn('Dataset.jsonld', r.headers['Content-Disposition'])
    def test_ea_download_validation_disabled(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            r = self.upload(EA_XMI, 'model.xmi')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['popis']['cs'], 'Popis')
    def test_multiple_downloads(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            r = self.upload(xml(['One', 'Two']))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/zip')
        with ZipFile(io.BytesIO(r.data)) as z:
            self.assertEqual(z.namelist(), ['One.jsonld', 'Two.jsonld'])
            for name in z.namelist():
                self.assertIsInstance(json.loads(z.read(name)), dict)
    def test_zip_names_unique(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            r = self.upload(xml(['a', 'a-3', 'a']))
        with ZipFile(io.BytesIO(r.data)) as z:
            self.assertEqual(len(set(z.namelist())), 3)
    def test_schema_success(self):
        response = Mock()
        response.json.return_value = {'type': 'object', 'required': ['název']}
        with patch.object(validation.requests, 'get', return_value=response):
            self.assertEqual(self.upload(xml(['Dataset'])).status_code, 200)
    def test_schema_rejection(self):
        response = Mock()
        response.json.return_value = {'type': 'object', 'required': ['missing_test_field']}
        with patch.object(validation.requests, 'get', return_value=response):
            self.assertEqual(self.upload(xml(['Dataset'])).status_code, 422)
    def test_schema_timeout(self):
        with patch.object(validation.requests, 'get', side_effect=requests.Timeout('test timeout')):
            self.assertEqual(self.upload(xml(['Dataset'])).status_code, 502)
    def test_invalid_schema_returns_gateway_error(self):
        response = Mock()
        response.json.return_value = {'type': 'invalid_type'}
        with patch.object(validation.requests, 'get', return_value=response):
            self.assertEqual(self.upload(xml(['Dataset'])).status_code, 502)


    def test_unicode_single_download_header(self):
        name = 'Žluťoučký kůň'
        with patch.object(validation, 'SCHEMA_URL', ''):
            response = self.upload(xml([name]))
        self.assertEqual(response.status_code, 200)
        header = response.headers['Content-Disposition']
        header.encode('ascii')
        self.assertIn("filename*=UTF-8''" + quote(name + '.jsonld'), header)
        self.assertEqual(response.json['název']['cs'], name)

    def test_unicode_zip_download_header(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            response = self.upload(xml(['One', 'Two']), 'žluťoučký.xml')
        self.assertEqual(response.status_code, 200)
        header = response.headers['Content-Disposition']
        header.encode('ascii')
        self.assertIn("filename*=UTF-8''" + quote('žluťoučký.zip'), header)

    def test_quoted_download_name(self):
        from werkzeug.http import parse_options_header
        with patch.object(validation, 'SCHEMA_URL', ''):
            response = self.upload(xml(['Dataset "quoted"']))
        _, options = parse_options_header(response.headers['Content-Disposition'])
        self.assertEqual(options['filename'], 'Dataset "quoted".jsonld')

    def test_published_context_matches_schema_version(self):
        with patch.object(validation, 'SCHEMA_URL', ''):
            response = self.upload(xml(['Dataset']))
        from urllib.parse import unquote
        expected = unquote(validation.DEFAULT_SCHEMA_URL).replace('schéma.json', 'kontext.jsonld')
        self.assertEqual(response.json['@context'], expected)
        self.assertNotIn('/draft/', expected)


class LegislationDefaultsTests(unittest.TestCase):
    def test_defaults_and_custom_legislation_at_all_levels(self):
        from core.jsonld_builders import build_dataset_document, build_distributions
        from core.models import ArchimateElement, LangText
        import warnings

        default = 'https://www.e-sbirka.cz/eli/cz/sb/2026/60/2026-05-27'
        custom = 'https://example.com/additional-law'
        cases = [
            (None, [default]),
            ('', [default]),
            (custom, [default, custom]),
            (f'{default};{custom};{default};{custom}', [default, custom]),
            ([custom, default, custom], [default, custom]),
            ('invalid;' + custom, [default, custom]),
        ]
        for supplied, expected in cases:
            with self.subTest(supplied=supplied):
                def make_element(identifier, properties):
                    return ArchimateElement(
                        identifier=identifier,
                        type='BusinessObject',
                        names=[LangText(identifier, 'cs')],
                        resolved_properties=properties,
                    )

                properties = {} if supplied is None else {'právní předpis': supplied}
                dataset = make_element('dataset', {
                    **properties,
                    'je součástí': 'https://example.com/series',
                })
                download = make_element('download', {
                    **properties,
                    'typ': 'distribuce - soubor ke stažení',
                })
                service = make_element('service', {
                    **properties,
                    'typ': 'distribuce - datová služba',
                    'přístupová služba - přístupový bod': 'https://example.com/api',
                    **({} if supplied is None else {
                        'přístupová služba - právní předpis': supplied,
                    }),
                })
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    document = build_dataset_document(
                        dataset, 'https://example.com/dataset', [],
                        build_distributions([download, service], 'https://example.com/dataset'),
                    )
                self.assertNotIn('je_součástí', document)
                objects = [document, *document['distribuce'],
                           document['distribuce'][1]['přístupová_služba']]
                for obj in objects:
                    self.assertEqual(obj['právní_předpis'], expected)


if __name__ == '__main__':
    unittest.main()
