import unittest
import re
import signal

from pyregex.service import RegexService, InvalidRegexError, UnprocessibleRegexError


class TimeoutException(Exception):
    pass


class ServiceTests(unittest.TestCase):
    def test_initialize(self):
        svc = RegexService(r'\d+', 'match', int(re.I))
        self.assertIsNotNone(svc)

    def test_invalidArgs(self):
        self.assertRaises(ValueError, lambda: RegexService(None, 'match', 2))
        self.assertRaises(ValueError, lambda: RegexService(r'\d+', None, 2))
        self.assertRaises(
            ValueError, lambda: RegexService(r'\d+', 'findall', -1))
        self.assertRaises(
            ValueError, lambda: RegexService(r'\d+', 'invalid', 2))
        self.assertRaises(InvalidRegexError,
                          lambda: RegexService('\\d+[', 'match', 2))

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

    def test_findall2(self):
        svc = RegexService(r'[\w\']+', 'findall', 0)
        result = svc.test('Hey, you - what are you doing here!?')
        self.assertIsNotNone(result)
        self.assertEqual(
            result, ['Hey', 'you', 'what', 'are', 'you', 'doing', 'here'])

    def test_search(self):
        svc = RegexService(r'\d+', 'search', 0)
        result = svc.test("1984")
        self.assertIsNotNone(result)
        self.assertEqual(result['group'], "1984")

        result = svc.test("x1984")
        self.assertIsNotNone(result)
        self.assertEqual(result['group'], "1984")

    def test_catastrophicBacktrace(self):
        input = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" + \
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

        def timeout_cb(signum, frame):
            raise TimeoutException("Timeout!")

        old_handler = signal.signal(signal.SIGALRM, timeout_cb)
        signal.alarm(5)

        try:
            svc = RegexService(r'(a?a)+b', 'match', 0)
            with self.assertRaises(UnprocessibleRegexError):
                svc.test(input)
        except TimeoutException as e:
            self.fail("Response took more than 5 seconds to execute")
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
