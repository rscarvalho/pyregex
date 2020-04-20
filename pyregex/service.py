import re
import sre_constants
from multiprocessing import Process, Queue

from .util import Value, dict_from_object

SINGLE_PROCESS = False


class InvalidRegexError(Exception):
    def __init__(self, error, *args, **kwargs):
        super(InvalidRegexError, self).__init__(*args, **kwargs)
        self.error = error


class UnprocessibleRegexError(Exception):
    def __init__(self, *args, **kwargs):
        super(UnprocessibleRegexError, self).__init__(*args, **kwargs)


class RegexService(Value):
    VALID_MATCH_TYPES = ('findall', 'match', 'search',)
    REGEX_TIMEOUT = 2  # seconds

    def __init__(self, regex, match_type, flags):
        if regex is None:
            raise ValueError('regex', regex)

        if match_type not in self.VALID_MATCH_TYPES:
            raise ValueError('match_type', match_type, self.VALID_MATCH_TYPES)

        if not isinstance(flags, int) or flags < 0:
            raise ValueError('flags', flags)

        try:
            re.compile(regex, flags)
        except sre_constants.error as error:
            raise InvalidRegexError(error)

        super(RegexService, self).__init__(
            pattern=regex, match_type=match_type, flags=flags)

    def test(self, test_string):
        def run_regex_test(pattern, match_type, flags, test_string, queue):
            regex = re.compile(pattern, flags)
            callback = getattr(regex, match_type)
            queue.put(dict_from_object(callback(test_string)))

        queue = Queue()
        # TODO; Let us just remove those immutable types because they're not very useful
        # pylint: disable=no-member
        args = (self.pattern, self.match_type, self.flags, test_string, queue)

        if SINGLE_PROCESS:
            run_regex_test(*args)
        else:
            process = Process(target=run_regex_test, args=args)
            process.start()
            process.join(self.REGEX_TIMEOUT)
            if process.is_alive():
                process.terminate()
                raise UnprocessibleRegexError()
        return queue.get()
