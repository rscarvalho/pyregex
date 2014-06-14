from flask import Flask, request, make_response
from flask.json import jsonify
from pyregex.middleware import CORSMiddleware
from pyregex.service import RegexService, InvalidRegexError, UnprocessibleRegexError

app = Flask('pyregex')
app.secret_key = '\x0f0%T\xd3\xd5\x11\xca\xaa\xf5,\x02Zp,"\x83\x94\x1b\x9e|6\xd7<'

def setup_logging(app):
    import logging
    from os.path import join, dirname, abspath

    log_path = join(dirname(__file__), '..', 'tmp')
    log_path = abspath(log_path)
    log_file = join(log_path, 'pyregex.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(file_handler)


def api_error(message, *args, **kwargs):
    response = jsonify(result_type='error', message=message % args)
    response.status_code = int(kwargs.get('status', 400))
    response.headers['Content-type'] = 'application/json'
    return response


@app.route('/api/regex/test/', methods=['GET'])
def test_regex():
    match_type  = request.values.get('match_type', 'findall')
    regex       = request.values.get('regex', '')
    test_string = request.values.get('test_string', '')

    try:
        flags = int(request.values.get('flags', '0'))
    except TypeError:
        flags = 0

    try:
        service = RegexService(regex, match_type, flags)
    except ValueError, e:
        fmt = 'Invalid value for {}: "{}"'
        if len(e.args) > 2:
            fmt += ". Acceptable values are {}"

        args = [", ".join(a) if type(a) is tuple else a for a in e.args]
        return api_error(fmt.format(*args))
    except InvalidRegexError:
        return api_error('Invalid regular expression: %s' % regex)

    try:
        result = service.test(test_string)
    except UnprocessibleRegexError:
        return api_error('This regular expression is unprocessible', status=422)

    return jsonify(result_type=match_type, result=result)

setup_logging(app)
app = CORSMiddleware(app)

if __name__ == '__main__':
    from werkzeug.serving import run_simple
    app.app.debug = True
    run_simple('localhost', 5000, app, use_reloader=True)
