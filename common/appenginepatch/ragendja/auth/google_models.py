from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from google.appengine.api import users
from google.appengine.ext import db
from ragendja.auth.models import EmailUserTraits

class GoogleUserTraits(EmailUserTraits):
    @classmethod
    def get_djangouser_for_user(cls, user):
        django_user = cls.all().filter('user_id = ', user.user_id()).get()
        
        if not django_user:
            django_user = cls.all().filter('user = ', user).get()
            
        if not django_user:
            django_user = cls.create_djangouser_for_user(user)
            django_user.is_active = True
            
        user_put = False
        if django_user.user != user:
            django_user.user = user
            user_put = True
            
        user_id = user.user_id()
        if django_user.user_id != user_id:
            django_user.user_id = user_id
            user_put = True
            
        if getattr(settings, 'AUTH_ADMIN_USER_AS_SUPERUSER', True):
            is_admin = users.is_current_user_admin()
            if django_user.is_staff != is_admin or django_user.is_superuser != is_admin:
                django_user.is_superuser = django_user.is_staff = is_admin
                user_put = True
                
        if not django_user.is_saved() or user_put:
            django_user.put()
            
        return django_user

    class Meta:
        abstract = True

class User(GoogleUserTraits):
    """Extended User class that provides support for Google Accounts."""
    user = db.UserProperty(required=True)
    user_id = db.StringProperty()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    @property
    def username(self):
        return self.user.nickname()

    @property
    def email(self):
        return self.user.email()

    @classmethod
    def create_djangouser_for_user(cls, user):
        return cls(user=user, user_id=user.user_id())
