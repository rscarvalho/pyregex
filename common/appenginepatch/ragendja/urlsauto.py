# -*- coding: utf-8 -*-
"""
Imports urlpatterns from apps, so we can have nice plug-n-play installation. :)
"""
from django.conf.urls.defaults import *
from django.conf import settings

IGNORE_APP_URLSAUTO = getattr(settings, 'IGNORE_APP_URLSAUTO', ())
check_app_imports = getattr(settings, 'check_app_imports', None)

urlpatterns = patterns('')

for app in settings.INSTALLED_APPS:
    if app == 'ragendja' or app.startswith('django.') or \
            app in IGNORE_APP_URLSAUTO:
        continue
    appname = app.rsplit('.', 1)[-1]
    try:
        if check_app_imports:
            check_app_imports(app)
        module = __import__(app + '.urlsauto', {}, {}, [''])
    except ImportError:
        pass
    else:
        if hasattr(module, 'urlpatterns'):
            urlpatterns += patterns('', (r'^%s/' % appname,
                                         include(app + '.urlsauto')),)
        if hasattr(module, 'rootpatterns'):
            urlpatterns += module.rootpatterns
