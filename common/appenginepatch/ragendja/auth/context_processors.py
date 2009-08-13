# -*- coding: utf-8 -*-
from google.appengine.api import users

def google_user(request):
    return {'google_user': users.get_current_user()}
