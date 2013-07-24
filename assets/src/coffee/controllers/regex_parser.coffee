ctrl = ($log, _, RegexResource, $scope, $rootScope) ->
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

  $scope.resultTemplateUrl = '/assets/templates/regex/start.html'
  $scope.currentResult = {result_type: null}
  $scope.processing = false

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
    $scope.processing = true

    data =
      flags: $scope.re.flag
      regex: $scope.re.source
      test_string: $scope.re.testString
      match_type: $scope.re.matchType

    RegexResource.test(data).then (result) ->
      $scope.processing = false
      $scope.currentResult = result.data
      $scope.resultTemplateUrl = '/assets/templates/regex/result.html'

    , (result) ->
      $scope.processing = false
      $scope.currentResult = result.data
      $scope.resultTemplateUrl = '/assets/templates/regex/error.html'

  $scope.hasResult = ->
    $scope.isResult() and
    $scope.currentResult.result != undefined and
    $scope.currentResult.result != null

  checkResultType = (type) ->
    $scope.isResult() and $scope.currentResult.result_type == type

  $scope.isError = ->
    $scope.currentResult != null and
    $scope.currentResult.result_type == 'error'

  $scope.isResult = -> not $scope.isError()
  $scope.isFindall = -> checkResultType('findall')
  $scope.isSearch = -> checkResultType('search')
  $scope.isMatch = -> checkResultType('match')

@PyRegex().controller('RegexParser', ctrl)