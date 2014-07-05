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


application = WSGIApplication(routes, debug=True)
application.router.set_dispatcher(route_dispatcher)
