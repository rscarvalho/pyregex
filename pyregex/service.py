import re, sre_constants
import exceptions
from .util import Value, dict_from_object
import signal
import logging
from multiprocessing import Process, Queue

class InvalidRegexError(exceptions.Exception):
    def __init__(self, error=None, *args, **kwargs):
        super(InvalidRegexError, self).__init__(*args, **kwargs)
        self.error = error


class UnprocessibleRegexError(exceptions.Exception):
    def __init__(self, error=None, *args, **kwargs):
        super(UnprocessibleRegexError, self).__init__(*args, **kwargs)
        self.error = error


class RegexService(Value):
    VALID_MATCH_TYPES = ('findall', 'match', 'search',)
    REGEX_TIMEOUT = 2 # seconds

    def __init__(self, regex, match_type, flags):
        if regex is None:
            raise ValueError('regex', regex)

        if match_type not in self.VALID_MATCH_TYPES:
            raise ValueError('match_type', match_type, self.VALID_MATCH_TYPES)

        if type(flags) != int or flags < 0:
            raise ValueError('flags', flags)

        try:
            re.compile(regex, flags)
        except sre_constants.error, error:
            raise InvalidRegexError(error)

        super(RegexService, self).__init__(pattern=regex, match_type=match_type, flags=flags)


    def test(self, test_string):
        def x(pattern, match_type, flags, test_string, q):
            regex = re.compile(self.pattern, self.flags)
            cb = getattr(regex, match_type)
            q.put(dict_from_object(cb(test_string)))

        queue = Queue()
        args = (self.pattern, self.match_type, self.flags, test_string, queue)
        p = Process(target=x, args=args)
        p.start()
        p.join(self.REGEX_TIMEOUT)
        if p.is_alive():
            p.terminate()
            raise UnprocessibleRegexError()
        return queue.get()

