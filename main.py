#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp.util import run_wsgi_app


class MainHandler(webapp.RequestHandler):

    def get(self):
        self.response.headers['Content-type'] = 'text/html'
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            label = "Logout"
        else:
            url = users.create_login_url(self.request.uri)
            label = "Login"
        
        self.response.out.write("<a href='%s'>%s</a>" % (url, label))


application = webapp.WSGIApplication([('/', MainHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)
    # wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
