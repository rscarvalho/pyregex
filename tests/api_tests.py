import unittest
import webapp2
import urllib
from pyregex.webapp import application as app
import re
import json


class RegexHandlerTest(unittest.TestCase):
    def test_index(self):
        request = webapp2.Request.blank('/api/regex/')
        response = request.get_response(app)
        self.assertEqual(404, response.status_int)


    def test_regexTestFindall(self):
        params = dict(
            flags=re.I | re.M,
            regex=r'\w+',
            test_string=u'Hello, World!',
            match_type='findall'
        )
        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)

        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertEqual(['Hello', 'World'], json_body['result'])


    def test_regexTestFindallNotAMatch(self):
        params = dict(
            flags=re.I | re.M,
            regex=r'\d+',
            test_string=u'Hello, World!',
            match_type='findall'
        )
        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)

        json_body = self.get_json_response(response)
        self.assertEqual('findall', json_body['result_type'])
        self.assertEqual(None, json_body['result'])    


    def test_regexTestMatch(self):
        params = dict(
            flags=0,
            regex=r'\[(\d{4,}-\d{2,}-\d{2})\] Testing beginning on server (.+)$',
            test_string=u'[2013-07-23] Testing beginning on server example.com',
            match_type='match'
        )

        expected = dict(
            group='[2013-07-23] Testing beginning on server example.com',
            groups=['2013-07-23', 'example.com'],
            group_dict={},
            end=52, start=0, pos=0,
            span=[0, 52],
            regs=[[0, 52], [1, 11], [41, 52]],
            last_group=None,
            last_index=2
        )

        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('match', json_body['result_type'])
        self.assertEqual(expected, json_body['result'])

    def test_regexTestMatchNotAMatch(self):
        params = dict(
            flags=0,
            regex=r'\[(\d{4,}-\d{2,}-\d{2})\] Testing beginning on server (.+)$',
            test_string=u'Not Matching [2013-07-23] Testing beginning on server example.com',
            match_type='match'
        )

        expected = None

        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('match', json_body['result_type'])
        self.assertEqual(expected, json_body['result'])


    def test_regexTestSearch(self):
        params = dict(
            flags=0,
            regex=r'^\[(\d{4,}-\d{2,}-\d{2})\] Testing beginning on server (.+)$',
            test_string=u'[2013-07-23] Testing beginning on server example.com',
            match_type='search'
        )

        expected = dict(
            group='[2013-07-23] Testing beginning on server example.com',
            groups=['2013-07-23', 'example.com'],
            group_dict={},
            end=52, start=0, pos=0,
            span=[0, 52],
            regs=[[0, 52], [1, 11], [41, 52]],
            last_group=None,
            last_index=2
        )

        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)
        json_body = self.get_json_response(response)
        self.assertEqual('search', json_body['result_type'])
        self.assertEqual(expected, json_body['result'])


    def test_regexTestInvalidRegex(self):
        params = dict(
            match_type='match',
            regex='[Not balanced',
            test_string='[Not balanced',
            flags=0
        )

        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)
        json_body = self.get_json_response(response, 400)
        self.assertEqual('error', json_body['result_type'])
        self.assertEqual('Invalid regular expression: %s' % params['regex'], json_body['message'])


    def test_regexTestUnknown(self):
        params = dict(
            flags=re.I | re.M,
            regex=r'\w+',
            test_string='Hello, World!',
            match_type='not_really_sure_about_it'
        )
        request = webapp2.Request.blank(
            '/api/regex/test/?%s' % urllib.urlencode(params))
        response = request.get_response(app)

        json_body = self.get_json_response(response, 400)
        self.assertEqual('error', json_body['result_type'])
        self.assertTrue(json_body['message'].startswith('Match Type must be one of the following:'))


    def get_json_response(self, response, *acceptable_statuses):
        if not acceptable_statuses:
            acceptable_statuses = [200]

        self.assertIn(response.status_int, acceptable_statuses)
        self.assertEqual('application/json', response.content_type)
        return json.loads(response.body)

