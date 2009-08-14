# -*- coding: utf-8 -*-
"""
Provides basic set of auth urls.
"""
from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('')

LOGIN = '^%s$' % settings.LOGIN_URL.lstrip('/')
LOGOUT = '^%s$' % settings.LOGOUT_URL.lstrip('/')

# If user set a LOGOUT_REDIRECT_URL we do a redirect.
# Otherwise we display the default template.
LOGOUT_DATA = {'next_page': getattr(settings, 'LOGOUT_REDIRECT_URL', None)}

# register auth urls depending on whether we use google or hybrid auth
if 'ragendja.auth.middleware.GoogleAuthenticationMiddleware' in \
        settings.MIDDLEWARE_CLASSES:
    urlpatterns += patterns('',
        url(LOGIN, 'ragendja.auth.views.google_login',
            name='django.contrib.auth.views.login'),
        url(LOGOUT, 'ragendja.auth.views.google_logout', LOGOUT_DATA,
            name='django.contrib.auth.views.logout'),
    )
elif 'ragendja.auth.middleware.HybridAuthenticationMiddleware' in \
        settings.MIDDLEWARE_CLASSES:
    urlpatterns += patterns('',
        url(LOGIN, 'ragendja.auth.views.hybrid_login',
            name='django.contrib.auth.views.login'),
        url(LOGOUT, 'ragendja.auth.views.hybrid_logout', LOGOUT_DATA,
            name='django.contrib.auth.views.logout'),
    )

# When faking a real function we always have to add the real function, too.
urlpatterns += patterns('',
    url(LOGIN, 'django.contrib.auth.views.login'),
    url(LOGOUT, 'django.contrib.auth.views.logout', LOGOUT_DATA,),
)
