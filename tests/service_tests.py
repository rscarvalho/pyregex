import unittest
import re
from pyregex.service import RegexService, InvalidRegexError, UnprocessibleRegex

class ServiceTests(unittest.TestCase):
    def test_initialize(self):
        svc = RegexService(r'\d+', 'match', re.I)


    def test_invalidArgs(self):
        self.assertRaises(ValueError, lambda: RegexService(None, 'match', 2))
        self.assertRaises(ValueError, lambda: RegexService(r'\d+', None, 2))
        self.assertRaises(ValueError, lambda: RegexService(r'\d+', 'findall', -1))
        self.assertRaises(ValueError, lambda: RegexService(r'\d+', 'invalid', 2))
        self.assertRaises(InvalidRegexError, lambda: RegexService('\\d+[', 'match', 2))

    def test_immutability(self):
        svc = RegexService(r'\d+', 'match', 0)
        with self.assertRaises(TypeError):
            svc.match_type = 'findall'

    def test_match(self):
        svc = RegexService(r'\d+', 'match', 0)
        result = svc.test("1984")
        self.assertIsNotNone(result)
        self.assertEqual(result['group'], "1984")

        result = svc.test("x1984")
        self.assertIsNone(result)

    def test_findall(self):
        svc = RegexService(r'\d+', 'findall', 0)
        result = svc.test("1984 2013 2020")
        self.assertIsNotNone(result)
        self.assertEqual(result, ['1984', '2013', '2020'])

        result = svc.test("testing")
        self.assertIsNone(result)

    def test_search(self):
        svc = RegexService(r'\d+', 'search', 0)
        result = svc.test("1984")
        self.assertIsNotNone(result)
        self.assertEqual(result['group'], "1984")

        result = svc.test("x1984")
        self.assertIsNotNone(result)
        self.assertEqual(result['group'], "1984")

    @unittest.skip("Not supported by GoogleAppEngine edition")
    def test_catastrophicBacktrace(self):
        input = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" + \
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        svc = RegexService(r'(a?a)+b', 'match', 0)
        with self.assertRaises(UnprocessibleRegex):
            svc.test(input)



