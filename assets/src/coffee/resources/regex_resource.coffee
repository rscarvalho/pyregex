@PyRegex().factory('RegexResource', (apiUrl, $http, jQuery) ->
  class RegexResource
    constructor: (http, apiUrl) ->
      @apiUrl = apiUrl
      @http = http

    test: (data) ->
      @http.get(@apiUrl + '/regex/test/?' + jQuery.param(data))


  new RegexResource($http, apiUrl)
)
