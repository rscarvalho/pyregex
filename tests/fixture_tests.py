"""Portable engine expectations, separately exercised through legacy adapters."""
import json
import os
import re
import unittest
from urllib.parse import urlencode

from webob import Request

from pyregex.api import app
from pyregex.service import InvalidRegexError, RegexService


with open(os.path.join(os.path.dirname(__file__), 'fixtures',
                       'regex_baseline.json'), encoding='utf-8') as fixture_file:
    CORPUS = json.load(fixture_file)
ENGINE_CASES = {case['id']: case for case in CORPUS['engine_cases']}


def flags_for(case):
    flags = 0
    for name in case['flags']:
        flags |= getattr(re, name)
    return int(flags)


def json_value(value):
    """Normalize tuples without importing the application's serialization code."""
    return json.loads(json.dumps(value))


def engine_result(case):
    pattern = re.compile(case['pattern'], flags_for(case))
    result = getattr(pattern, case['operation'])(case['input'])
    if case['operation'] == 'findall' or result is None:
        return json_value(result)
    return json_value(dict(
        group=result.group(), groups=result.groups(),
        group_dict=result.groupdict(), start=result.start(), end=result.end(),
        pos=result.pos, span=result.span(), regs=result.regs,
        last_group=result.lastgroup, last_index=result.lastindex))


class FixtureTests(unittest.TestCase):
    def test_engine_corpus(self):
        for case in CORPUS['engine_cases']:
            with self.subTest(case=case['id']):
                if 'error' in case:
                    error_type = {'invalid_pattern': re.error,
                                  'invalid_flags': ValueError}[case['error']]
                    with self.assertRaises(error_type):
                        engine_result(case)
                else:
                    self.assertEqual(case['expected'], engine_result(case))

    def test_legacy_service_corpus(self):
        for adapter in CORPUS['adapter_cases']:
            case = ENGINE_CASES[adapter['engine_case']] if 'engine_case' in adapter else adapter
            with self.subTest(case=case['id']):
                if 'error' in case:
                    error_type = (InvalidRegexError if case['error'] == 'invalid_pattern'
                                  else ValueError)
                    with self.assertRaises(error_type):
                        RegexService(case['pattern'], case['operation'], flags_for(case))
                else:
                    service = RegexService(case['pattern'], case['operation'], flags_for(case))
                    expected = (adapter['expected'] if adapter['expectation'] == 'override'
                                else case['expected'])
                    self.assertEqual(expected, json_value(service.test(case['input'])))

    def test_legacy_api_corpus(self):
        for adapter in CORPUS['adapter_cases']:
            case = ENGINE_CASES[adapter['engine_case']] if 'engine_case' in adapter else adapter
            with self.subTest(case=case['id']):
                query = urlencode(dict(regex=case['pattern'], test_string=case['input'],
                                       match_type=case['operation'], flags=flags_for(case)))
                response = Request.blank('/api/regex/test/?' + query).get_response(app)
                if adapter.get('api_status') == 500:
                    self.assertEqual(500, response.status_int)
                    continue
                body = json.loads(response.body.decode('utf-8'))
                self.assertEqual('application/json', response.content_type)
                if 'error' in case:
                    self.assertEqual(400, response.status_int)
                    self.assertEqual('error', body['result_type'])
                    self.assertIsInstance(body['message'], str)
                    self.assertTrue(body['message'])
                else:
                    expected = (adapter['expected'] if adapter['expectation'] == 'override'
                                else case['expected'])
                    self.assertEqual(200, response.status_int)
                    self.assertEqual(dict(result_type=case['operation'], result=expected), body)
