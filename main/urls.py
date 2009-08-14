from django.conf.urls.defaults import *

urlpatterns = patterns('main.views',
    (r'^$', 'index'),
    (r'^check_regex/$', 'check_regex')
)
