# -*- coding: utf-8 -*-
from django.conf import settings
from mediautils.views import get_file

class MediaMiddleware(object):
    """Returns media files.
    
    This is a middleware, so it can handle the request as early as possible
    and thus with minimum overhead."""
    def process_request(self, request):
        if request.path.startswith(settings.MEDIA_URL):
            path = request.path[len(settings.MEDIA_URL):]
            return get_file(request, path)
        return None
