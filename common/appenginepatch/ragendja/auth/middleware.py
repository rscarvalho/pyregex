# Parts of this code are taken from Google's django-helper (license: Apache 2)

class LazyGoogleUser(object):
    def __init__(self, middleware_class):
        self._middleware_class = middleware_class

    def __get__(self, request, obj_type=None):
        if not hasattr(request, '_cached_user'):
            from django.contrib.auth import get_user
            from django.contrib.auth.models import AnonymousUser, User
            from google.appengine.api import users
            if self._middleware_class is HybridAuthenticationMiddleware:
                request._cached_user = get_user(request)
            else:
                request._cached_user = AnonymousUser()
            if request._cached_user.is_anonymous():
                user = users.get_current_user()
                if user:
                    request._cached_user = User.get_djangouser_for_user(user)
        return request._cached_user

class GoogleAuthenticationMiddleware(object):
    def process_request(self, request):
        request.__class__.user = LazyGoogleUser(self.__class__)

class HybridAuthenticationMiddleware(GoogleAuthenticationMiddleware):
    pass
