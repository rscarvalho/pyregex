import webapp2
from pyregex import api, urls
import os.path

routes = urls.discover_resources(api, endpoint='/api')

application = webapp2.WSGIApplication(routes, debug=True)
