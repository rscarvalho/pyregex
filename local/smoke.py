"""Representative local HTTP requests; each request has an external deadline."""
import json
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


def check(params, status, result_type, expected):
    url = 'http://127.0.0.1:5000/api/regex/test/?' + urlencode(params)
    try:
        response = urlopen(url, timeout=6)
    except HTTPError as error:
        response = error
    with response:
        body = json.load(response)
        assert response.code == status, (response.code, body)
    assert body['result_type'] == result_type, body
    if status == 200:
        assert body['result'] == expected, body
    else:
        assert body['message'] == expected, body
    print('PASS', status, params.get('match_type', 'findall'))


check(dict(regex=r'\w+', test_string='Hello, World!'),
      200, 'findall', ['Hello', 'World'])
check(dict(regex=r'\d+', test_string='none'), 200, 'findall', None)
check(dict(regex='[', test_string=''), 400, 'error',
      'Invalid regular expression: [')
check(dict(regex='(a?a)+b', test_string='a' * 112, match_type='match'),
      422, 'error', 'This regular expression is unprocessible')
