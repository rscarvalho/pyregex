from webob import Request

class CORSMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        req = Request(environ)
        resp = req.get_response(self.app)

        resp.headers['Access-Control-Allow-Origin'] = "*"
        resp.headers['Access-Control-Allow-Method'] = "GET"

        return resp(environ, start_response)

