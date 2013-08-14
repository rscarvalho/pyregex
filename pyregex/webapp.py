import webapp2
from pyregex import api, urls
import os.path
import os
import sys
import json
from webob.exc import HTTPBadRequest
import logging

class WSGIApplication(webapp2.WSGIApplication):
    def __init__(self, *args, **kwargs):
        super(WSGIApplication, self).__init__(*args, **kwargs)
        self.setup_logging()


    def setup_logging(self):
        log_path = os.path.join(os.path.dirname(__file__), '..', 'tmp')
        log_path = os.path.abspath(log_path)
        log_file = os.path.join(log_path, 'pyregex.log')
    
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)

        logging.info("Starting app...")


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
    rv.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin')
    return rv

application = WSGIApplication(routes, debug=True)
application.router.set_dispatcher(route_dispatcher)
