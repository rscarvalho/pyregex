# -*- coding: utf-8 -*-
from django.conf import settings
from django.template import Library
from django.utils.html import escape
from google.appengine.api import users

register = Library()

@register.simple_tag
def google_login_url(redirect=settings.LOGIN_REDIRECT_URL):
    return escape(users.create_login_url(redirect))

@register.simple_tag
def google_logout_url(redirect='/'):
    prefixes = getattr(settings, 'LOGIN_REQUIRED_PREFIXES', ())
    if any(redirect.startswith(prefix) for prefix in prefixes):
        redirect = '/'
    return escape(users.create_logout_url(redirect))
