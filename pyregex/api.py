import os
from os.path import join, dirname, abspath, exists, realpath
from flask import Flask, request, make_response
from flask.json import jsonify
from flask import got_request_exception
from pyregex.middleware import CORSMiddleware
from pyregex.service import RegexService, InvalidRegexError, UnprocessibleRegexError
import rollbar
import rollbar.contrib.flask

app = Flask('pyregex')
app.secret_key = '\x0f0%T\xd3\xd5\x11\xca\xaa\xf5,\x02Zp,"\x83\x94\x1b\x9e|6\xd7<'


@app.before_first_request
def init_rollbar():
    """Initializes the rollbar module
    """
    token = os.environ.get("ROLLBAR_TOKEN")
    environment = os.environ.get("ROLLBAR_ENV", "development")
    if token:
        rollbar.init(token, environment, root=dirname(
            realpath(__file__)), allow_logging_basic_config=False)
        got_request_exception.connect(
            rollbar.contrib.flask.report_exception, app)
    else:
        app.logger.info("Rollbar token not present. Skipping rollbar setup")


def api_error(message, *args, **kwargs):
    response = jsonify(result_type='error', message=message % args)
    response.status_code = int(kwargs.get('status', 400))
    response.headers['Content-type'] = 'application/json'
    return response


@app.route('/api/regex/test/', methods=['GET'])
def test_regex():
    match_type = request.values.get('match_type', 'findall')
    regex = request.values.get('regex', '')
    test_string = request.values.get('test_string', '')

    try:
        flags = int(request.values.get('flags', '0'))
    except TypeError:
        flags = 0

    try:
        service = RegexService(regex, match_type, flags)
    except ValueError as e:
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
