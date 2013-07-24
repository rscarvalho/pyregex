import webapp2
from webob.exc import HTTPNotFound
import json
from .decorators import handle_json
import sys
import logging
import re


class ApiBaseResource(webapp2.RequestHandler):

    def api_error(self, message, *args):
        return dict(result_type='error', message=message % args)


class RegexResource(ApiBaseResource):
    __urls__ = ('regex/', 'regex/<key>', 'regex/test/')

    VALID_MATCH_TYPES = ('findall',)

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

        if match_type not in self.VALID_MATCH_TYPES:
            self.response.set_status(400)
            return self.api_error('Match Type must be one of the following: %s', str(self.VALID_MATCH_TYPES))

        r = dict(result_type=match_type)

        if match_type == 'findall':
            r['result'] = re.compile(regex, flags).findall(test_string)

        return r
