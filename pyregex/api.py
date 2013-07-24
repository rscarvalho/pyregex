import webapp2
from webob.exc import HTTPNotFound
import json
from .decorators import handle_json
import sys
import logging
import re, sre_constants


class ApiBaseResource(webapp2.RequestHandler):
    def api_error(self, message, *args):
        return dict(result_type='error', message=message % args)


class RegexResource(ApiBaseResource):
    __urls__ = ('regex/', 'regex/<key>', 'regex/test/')

    VALID_MATCH_TYPES = ('findall', 'match', 'search',)

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

        if not regex:
            self.response.set_status(400)
            return self.api_error('Regex string must not be empty')

        r = dict(result_type=match_type)

        try:
            regex = re.compile(regex, flags)
        except sre_constants.error, error:
            self.response.set_status(400)
            return self.api_error('Invalid regular expression: %s', regex)

        cb = getattr(regex, match_type)
        r['result'] = self.dict_from_object(cb(test_string))

        return r

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

