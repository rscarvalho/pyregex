from ragendja.settings_post import settings
from appenginepatcher import have_appserver, on_production_server
if have_appserver and not on_production_server and \
        settings.MEDIA_URL.startswith('/'):
    if settings.ADMIN_MEDIA_PREFIX.startswith(settings.MEDIA_URL):
        settings.ADMIN_MEDIA_PREFIX = '/generated_media' + \
                                      settings.ADMIN_MEDIA_PREFIX
    settings.MEDIA_URL = '/generated_media' + settings.MEDIA_URL
    settings.MIDDLEWARE_CLASSES = (
        'mediautils.middleware.MediaMiddleware',
    ) + settings.MIDDLEWARE_CLASSES
