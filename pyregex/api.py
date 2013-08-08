import webapp2
from webob.exc import HTTPNotFound
import json
from .decorators import handle_json
from .service import RegexService, InvalidRegexError
import logging


class ApiBaseResource(webapp2.RequestHandler):
    def api_error(self, message, *args):
        return dict(result_type='error', message=message % args)


class RegexResource(ApiBaseResource):
    __urls__ = ('regex/', 'regex/<key>', 'regex/test/')


    @handle_json
    def get(self):
        if self.request.path_info.endswith('/test/'):
            return self.test_regex()
        raise HTTPNotFound('Not Implemented Yet')


    def test_regex(self):
        match_type = self.request.get('match_type')
        regex = self.request.get('regex')
        test_string = self.request.get('test_string')
        flags = int(self.request.get('flags'))

        try:
            service = RegexService(regex, match_type, flags)
        except ValueError, e:
            self.response.set_status(400)
            fmt = "Invalid value for {}: \"{}\""
            if len(e.args) > 2:
                fmt += ". Acceptable values are {}"

            args = [", ".join(a) if type(a) is tuple else a for a in e.args]
            return self.api_error(fmt.format(*args))
        except InvalidRegexError:
            self.response.set_status(400)
            return self.api_error('Invalid regular expression: %s', regex)

        return {
            'result_type': match_type,
            'result': service.test(test_string)
        }

