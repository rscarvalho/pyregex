import webapp2
from pyregex import api, urls
import os.path
import json
from webob.exc import HTTPBadRequest

routes = urls.discover_resources(api, endpoint='/api')

def route_dispatcher(router, request, response):
    rv = router.default_dispatcher(request, response)
    if isinstance(rv, dict):
        if 'application/json' in request.accept:
            response.write(json.dumps(rv))
            rv = response
            rv.headers['Content-type'] = 'application/json; charset=utf-8'
        else:
            raise HTTPBadRequest()

    elif isinstance(rv, basestring):
        response.write(rv)
        rv = response
    elif isinstance(rv, tuple):
        rv = webapp2.Response(*rv)

    rv.headers['Access-Control-Allow-Origin'] = "*"
    return rv

application = webapp2.WSGIApplication(routes, debug=True)
application.router.set_dispatcher(route_dispatcher)
