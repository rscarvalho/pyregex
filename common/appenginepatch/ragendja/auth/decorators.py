# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from functools import wraps
from ragendja.auth.views import google_redirect_to_login
from ragendja.template import render_to_response

def staff_only(view):
    """
    Decorator that requires user.is_staff. Otherwise renders no_access.html.
    """
    @login_required
    def wrapped(request, *args, **kwargs):
        if request.user.is_active and request.user.is_staff:
            return view(request, *args, **kwargs)
        return render_to_response(request, 'no_access.html')
    return wraps(view)(wrapped)

def google_login_required(function):
    def login_required_wrapper(request, *args, **kw):
        if request.user.is_authenticated():
            return function(request, *args, **kw)
        return google_redirect_to_login(request.get_full_path())
    return wraps(function)(login_required_wrapper)
