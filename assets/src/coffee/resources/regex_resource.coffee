@PyRegex().factory('RegexResource', (apiUrl, $resource, $log) ->
  $log.info "API URL: #{apiUrl}"
  $resource "#{apiUrl}/regex/:id", {},
    test:
      method: 'GET',
      params: {flags: 0, regex: '', test_string: '', match_type: 'match'}
)