import inspect
import logging
import webapp2

def discover_resources(module, endpoint='/'):
    resources = [getattr(module, cls) for cls in dir(module)]
    resources = [cls for cls in resources if inspect.isclass(cls) and issubclass(cls, webapp2.RequestHandler)]
    resources = map(lambda r: [(url, r) for url in r.__urls__] if hasattr(r, '__urls__') else [], resources)
    resources = reduce(lambda x, y: x + y, resources)

    logging.info('Registering URLs for endpoint "%s": %s' % (endpoint, resources))

    return [("%s/%s" % (endpoint, url), handler) for url, handler in resources]