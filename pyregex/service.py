import re, sre_constants
import exceptions
from .util import Value
import signal

class InvalidRegexError(exceptions.Exception):
    def __init__(self, error=None, *args, **kwargs):
        super(InvalidRegexError, self).__init__(*args, **kwargs)
        self.error = error


class UnprocessibleRegex(exceptions.Exception):
    @classmethod
    def cb(cls, signum, frame):
        raise cls()


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
        regex = re.compile(self.pattern, self.flags)
        cb = getattr(regex, self.match_type)

        old_handler = signal.signal(signal.SIGALRM, UnprocessibleRegex.cb)
        signal.alarm(self.REGEX_TIMEOUT)
        try:
            return self.dict_from_object(cb(test_string))
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


    def dict_from_object(self, obj):
        if obj and hasattr(obj, 'groupdict') and callable(getattr(obj, 'groupdict')):
            return dict(
                group=obj.group(),
                groups=obj.groups(),
                group_dict=obj.groupdict(),
                end=obj.end(), start=obj.start(), pos=obj.pos,
                span=obj.span(),
                regs=obj.regs,
                last_group=obj.lastgroup,
                last_index=obj.lastindex
            )
        elif not obj:
            return None
        return obj

