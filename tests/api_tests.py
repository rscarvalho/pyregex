import unittest
import webapp2
import urllib
from pyregex.webapp import application as app
import re
import json


class RegexHandlerTest(unittest.TestCase):

    def test_regex_test_findall(self):
        params = dict(
            flags=re.I | re.M,
            regex=r'\w+',
            test_string='Hello, World!',
            match_type='findall'
        )
        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)

        self.assertEqual(200, response.status_int)
        self.assertEqual('application/json', response.content_type)
        json_body = json.loads(response.body)
        self.assertEqual('findall', json_body['result_type'])
        self.assertEqual(['Hello', 'World'], json_body['result'])

    def test_regex_test_unknown(self):
        params = dict(
            flags=re.I | re.M,
            regex=r'\w+',
            test_string='Hello, World!',
            match_type='not_really_sure_about_it'
        )
        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)

        self.assertEqual(400, response.status_int)
        json_body = json.loads(response.body)
        self.assertEqual('error', json_body['result_type'])
        self.assertTrue(json_body['message'].startswith('Match Type must be one of the following:'))
        self.assertEqual('application/json', response.content_type)
