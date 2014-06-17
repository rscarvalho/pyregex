@PyRegex().service 'RegexResource', (apiUrl, $http, jQuery) ->
  test: (data) ->
    $http.get(apiUrl + '/regex/test/?' + jQuery.param(data))

