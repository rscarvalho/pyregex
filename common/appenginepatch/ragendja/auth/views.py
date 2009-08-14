# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login, logout
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from google.appengine.api import users
from ragendja.template import render_to_response

def get_redirect_to(request, redirect_field_name):
    redirect_to = request.REQUEST.get(redirect_field_name)
    # Light security check -- make sure redirect_to isn't garbage.
    if not redirect_to or '//' in redirect_to or ' ' in redirect_to:
        redirect_to = settings.LOGIN_REDIRECT_URL
    return redirect_to

def google_login(request, template_name=None,
        redirect_field_name=REDIRECT_FIELD_NAME):
    redirect_to = get_redirect_to(request, redirect_field_name)
    return HttpResponseRedirect(users.create_login_url(redirect_to))

def hybrid_login(request, template_name='registration/login.html',
        redirect_field_name=REDIRECT_FIELD_NAME):
    # Don't login using both authentication systems at the same time
    if request.user.is_authenticated():
        redirect_to = get_redirect_to(request, redirect_field_name)
        return HttpResponseRedirect(redirect_to)
    return login(request, template_name, redirect_field_name)

def google_logout(request, next_page=None,
        template_name='registration/logged_out.html'):
    if users.get_current_user():
        # Redirect to this page until the session has been cleared.
        logout_url = users.create_logout_url(next_page or request.path)
        return HttpResponseRedirect(logout_url)
    if not next_page:
        return render_to_response(request, template_name,
            {'title': _('Logged out')})
    return HttpResponseRedirect(next_page)

def hybrid_logout(request, next_page=None,
        template_name='registration/logged_out.html'):
    if users.get_current_user():
        return google_logout(request, next_page)
    return logout(request, next_page, template_name)

def google_logout_then_login(request, login_url=None):
    if not login_url:
        login_url = settings.LOGIN_URL
    return google_logout(request, login_url)

def hybrid_logout_then_login(request, login_url=None):
    if not login_url:
        login_url = settings.LOGIN_URL
    return hybrid_logout(request, login_url)

def google_redirect_to_login(next, login_url=None, redirect_field_name=None):
    return HttpResponseRedirect(users.create_login_url(next))
