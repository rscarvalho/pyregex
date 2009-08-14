# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.encoding import force_unicode
from django.utils.functional import Promise

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_unicode(obj)
        return super(LazyEncoder, self).default(obj)

class JSONResponse(HttpResponse):
    def __init__(self, pyobj, **kwargs):
        super(JSONResponse, self).__init__(
            simplejson.dumps(pyobj, cls=LazyEncoder),
            content_type='application/json; charset=%s' %
                            settings.DEFAULT_CHARSET,
            **kwargs)
