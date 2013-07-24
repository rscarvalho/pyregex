@PyRegex().controller('RegexParser', ($log, _, RegexResource, $scope) ->
  $scope.reFlags = [false, false, false, false, false, false]
  $scope.allFlags =
    I: 'Ignore Case'
    L: 'Make \\w, \\W, \\b, \\B, \\s and \\S dependent on the current locale.'
    M: 'Multi-line Regular Expression'
    S: 'Make the "." special character match any character at all, ' +
       'including a newline'
    U: 'Make \\w, \\W, \\b, \\B, \\d, \\D, \\s and \\S dependent on the ' +
       'Unicode character properties database.'
    X: 'Verbose'

  $scope.re =
    flag: 0
    source: ""
    testString: ""
    matchType: "match"

  $scope.calculateFlags = ->
    mapList = _.map($scope.reFlags, (x, i) ->
      if x
        Math.pow(2, i + 1)
      else
        false
    )
    $scope.re.flag = _.reduce(_.filter(mapList, (x) -> x),
      (memo, value) -> memo | value
    , 0)

  $scope.getResults = ->
    data =
      flags: $scope.re.flag
      regex: $scope.re.source
      test_string: $scope.re.testString
      match_type: $scope.re.matchType
    $log.info(data)
    result = RegexResource.$test(data)
    $log.info(result)
)