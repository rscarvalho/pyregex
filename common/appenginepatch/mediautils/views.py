# -*- coding: utf-8 -*-
from django.http import HttpResponse, Http404
from django.views.decorators.cache import cache_control
from mediautils.generatemedia import get_targets, get_copy_targets, \
    get_target_content, get_media_dirs
from mimetypes import guess_type
from ragendja.template import render_to_response

@cache_control(public=True, max_age=3600*24*60*60)
def get_file(request, path):
    media_dirs = get_media_dirs()
    data = {'media_dirs': media_dirs}
    targets = get_targets(**data)
    copy_targets = get_copy_targets(**data)
    target_names = [target[0] for target in targets]

    name = path.rsplit('/', 1)[-1]
    cache = {}
    if path in target_names:
        target, kwargs, group = targets[target_names.index(path)]
        content = get_target_content(group, cache, **kwargs)
    elif path in copy_targets:
        fp = open(copy_targets[path], 'rb')
        content = fp.read() 
        fp.close()
    else:
        raise Http404('Media file not found: %s' % path)
    return HttpResponse(content,
        content_type=guess_type(name)[0] or 'application/octet-stream')
